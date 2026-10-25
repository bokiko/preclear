"""Exclusive run-root allocation and exclusive file creation (HARN-03).

Every run lives in one harness-created directory (the run root). This module only ever
creates: a directory with one os.mkdir call that has no exist_ok handling, a file with
O_CREAT and O_EXCL. A second creation of the same path is an error, never a reuse. The
module lists no run roots, sorts none, renames nothing and deletes nothing, so run-root
ordering belongs to the caller. (copy_tree_exclusive walks a source tree in sorted order
only to copy it into a brand-new destination.)

CLI: python3 -E -s -B pc_runroot.py PARENT NAME
  prints the created path on stdout and exits 0;
  prints "run root collision" on stderr and exits 16 when the name is taken;
  exits 2 for a bad name, a missing parent or bad usage;
  exits 1 when the operating system refuses the creation for another reason.
"""
from __future__ import annotations

import os
import stat
import sys

# Same value as the RUNROOT_COLLISION constant in pc_exitcodes (plan 02-01). It is a
# literal here so this module imports nothing from its siblings; test_exitcode_agreement
# (plan 02-07) compares the two by running this CLI.
EXIT_COLLISION = 16
EXIT_USAGE = 2
EXIT_OS_ERROR = 1

MAX_NAME_BYTES = 255


class RunRootError(Exception):
    """The request was refused before anything was created (bad name or parent)."""


class RunRootCollision(RunRootError):
    """The path already exists as a directory, file or symlink (also a dangling one)."""


def _validate_name(name):
    if not isinstance(name, str):
        raise RunRootError("run root name must be text")
    if name == "":
        raise RunRootError("run root name is empty")
    if name in (".", ".."):
        raise RunRootError("run root name is a dot name")
    if os.sep in name or (os.altsep is not None and os.altsep in name):
        raise RunRootError("run root name holds a path separator")
    if "\x00" in name:
        raise RunRootError("run root name holds a NUL")
    try:
        encoded = name.encode("utf-8")
    except UnicodeEncodeError:
        raise RunRootError("run root name cannot be encoded as UTF-8")
    if len(encoded) > MAX_NAME_BYTES:
        raise RunRootError("run root name is longer than 255 UTF-8 bytes")


def allocate_run_root(parent, name):
    """Create PARENT/NAME exclusively and return its realpath.

    The name is validated and the parent checked before any directory exists. The
    parent is resolved once; the single os.mkdir call has no exist_ok handling, so an
    existing directory, regular file, symlink (dangling or not) is a RunRootCollision.
    """
    _validate_name(name)
    parent = os.fspath(parent)
    if isinstance(parent, bytes) or parent == "" or "\x00" in parent:
        raise RunRootError("run root parent is not usable")
    if not os.path.isdir(parent):
        raise RunRootError("run root parent is not an existing directory")
    real_parent = os.path.realpath(parent)
    path = os.path.join(real_parent, name)
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        raise RunRootCollision("run root collision")
    return os.path.realpath(path)


def exclusive_dir(path, mode):
    """Create one directory; FileExistsError surfaces when it already exists."""
    os.mkdir(path, mode)


def write_exclusive(path, data, mode):
    """Create PATH with O_EXCL (never following a final symlink) and write all of DATA.

    FileExistsError surfaces when anything, a dangling symlink included, is already
    there. The file is fsynced before it is closed.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags, mode)
    try:
        os.fchmod(fd, mode)
        view = memoryview(data)
        while len(view) > 0:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _raise(error):
    raise error


def _read_regular(path):
    """Read one regular file in full without following a final symlink or blocking on a pipe."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        raise RunRootError("a source file could not be opened safely")
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise RunRootError("a source entry is not a regular file")
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(fd)
    return b"".join(chunks)


def copy_tree_exclusive(src, dst):
    """Copy the tree SRC to the new path DST and return the number of files copied.

    SRC must be an existing real directory (not a symlink); DST must not exist, so an
    existing destination, a dangling symlink included, raises FileExistsError. The whole
    source is walked on raw bytes, in sorted order and without following symlinks, and
    refused (RunRootError) if it holds any symlink or special file, before anything is
    created. Directories are created with exclusive_dir and files with write_exclusive,
    each from bytes read once. A file is 0o755 when the source has any executable bit and
    0o644 otherwise. Nothing is ever removed, renamed or overwritten.
    """
    src_bytes = os.fsencode(os.fspath(src))
    dst_bytes = os.fsencode(os.fspath(dst))
    if src_bytes == b"" or os.path.islink(src_bytes) or not os.path.isdir(src_bytes):
        raise RunRootError("copy source is not an existing real directory")
    directories = []
    files = []
    for dirpath, dirnames, filenames in os.walk(src_bytes, onerror=_raise):
        if dirpath == src_bytes:
            rel_dir = b""
        else:
            rel_dir = dirpath[len(src_bytes):].lstrip(b"/")
        for name in list(dirnames) + list(filenames):
            rel = rel_dir + b"/" + name if rel_dir else name
            mode = os.lstat(os.path.join(dirpath, name)).st_mode
            if stat.S_ISDIR(mode):
                directories.append(rel)
            elif stat.S_ISREG(mode):
                files.append((rel, 0o755 if mode & 0o111 else 0o644))
            else:
                raise RunRootError("copy source holds a symlink or special file")
    directories.sort()
    files.sort()
    exclusive_dir(dst_bytes, 0o700)
    for rel in directories:
        exclusive_dir(os.path.join(dst_bytes, rel), 0o700)
    for rel, mode in files:
        write_exclusive(os.path.join(dst_bytes, rel), _read_regular(os.path.join(src_bytes, rel)), mode)
    return len(files)


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: pc_runroot.py PARENT NAME\n")
        return EXIT_USAGE
    try:
        created = allocate_run_root(argv[0], argv[1])
    except RunRootCollision:
        sys.stderr.write("run root collision\n")
        return EXIT_COLLISION
    except RunRootError as exc:
        sys.stderr.write("run root refused: %s\n" % exc)
        return EXIT_USAGE
    except OSError:
        sys.stderr.write("run root could not be created\n")
        return EXIT_OS_ERROR
    sys.stdout.buffer.write(os.fsencode(created) + b"\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
