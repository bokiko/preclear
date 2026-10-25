"""Exclusive run-root allocation and exclusive file creation (HARN-03).

Every run lives in one harness-created directory (the run root). This module only ever
creates: a directory with one os.mkdir call that has no exist_ok handling, a file with
O_CREAT and O_EXCL. A second creation of the same path is an error, never a reuse. The
module lists, sorts, renames and deletes nothing, so run-root ordering belongs to the
caller.

CLI: python3 -E -s -B pc_runroot.py PARENT NAME
  prints the created path on stdout and exits 0;
  prints "run root collision" on stderr and exits 16 when the name is taken;
  exits 2 for a bad name, a missing parent or bad usage;
  exits 1 when the operating system refuses the creation for another reason.
"""
from __future__ import annotations

import os
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


def copy_tree_exclusive(src, dst):
    return None


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
