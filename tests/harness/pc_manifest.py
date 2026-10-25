"""Byte-walk tree manifests, sha.txt and JSON-lines writers (HARN-08).

A manifest lists every entry of a tree by walking raw byte paths in-process. Names are
never split on newlines and no external listing command is used, so a name holding a
newline, a carriage return, a backslash, CJK, an emoji or right-to-left text stays one
entry. Entries are sorted by their raw relative path bytes, never by locale.

Two text forms are produced from the entries:
  sha.txt         the committed shape: 64 lowercase hex, two spaces, relative path, one
                  line per regular file. A name holding a backslash, newline or carriage
                  return is written with a leading backslash on the line and backslash
                  escapes (the sha256sum convention), which is injective.
  manifest.jsonl  a lossless companion, one JSON object per entry, ensure_ascii, with the
                  path decoded by os.fsdecode so a lone surrogate round-trips to the
                  original bytes through os.fsencode.

Entry shape (a dict): path (raw relative bytes, forward slashes), kind (f regular file,
d directory, l symlink, o any other type), size (int for f, else None), sha256 (hex for
f, else None), target (raw link target bytes for l, else None).

CLI: python3 -E -s -B pc_manifest.py ROOT [--jsonl]
  writes the chosen form to stdout and exits 0; exits 2 on a bad root or bad usage.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys

import pc_runroot

CHUNK = 1024 * 1024


class ManifestError(Exception):
    """The manifest was refused (missing or non-directory root)."""


def _raise(error):
    raise error


def tree_manifest(root):
    """Return the entries of ROOT sorted by raw relative path bytes.

    Never follows symlinks. A missing or non-directory root raises ManifestError; an
    empty tree returns an empty list. Walk errors are raised, never skipped.
    """
    root_bytes = os.fsencode(root)
    if root_bytes == b"" or not os.path.isdir(root_bytes):
        raise ManifestError("manifest root is missing or is not a directory")
    entries = []
    for dirpath, dirnames, filenames in os.walk(root_bytes, onerror=_raise):
        if dirpath == root_bytes:
            rel_dir = b""
        else:
            rel_dir = dirpath[len(root_bytes):].lstrip(b"/")
        for name in list(dirnames) + list(filenames):
            full = os.path.join(dirpath, name)
            rel = rel_dir + b"/" + name if rel_dir else name
            mode = os.lstat(full).st_mode
            entry = {"path": rel, "kind": "o", "size": None, "sha256": None, "target": None}
            if stat.S_ISLNK(mode):
                entry["kind"] = "l"
                entry["target"] = os.readlink(full)
            elif stat.S_ISDIR(mode):
                entry["kind"] = "d"
            elif stat.S_ISREG(mode):
                digest = hashlib.sha256()
                size = 0
                with open(full, "rb") as handle:
                    while True:
                        chunk = handle.read(CHUNK)
                        if not chunk:
                            break
                        digest.update(chunk)
                        size += len(chunk)
                entry["kind"] = "f"
                entry["size"] = size
                entry["sha256"] = digest.hexdigest()
            entries.append(entry)
    entries.sort(key=lambda item: item["path"])
    return entries


def escape_name(name_bytes):
    """Return (text, escaped): the text form of a name and whether an escape was applied.

    A backslash becomes two backslashes, a newline becomes backslash n and a carriage
    return becomes backslash r. Bytes that are not valid UTF-8 are carried through with
    surrogateescape, so encoding the text again with surrogateescape gives the same bytes.
    """
    escaped_bytes = name_bytes.replace(b"\\", b"\\\\").replace(b"\n", b"\\n").replace(b"\r", b"\\r")
    return escaped_bytes.decode("utf-8", "surrogateescape"), escaped_bytes != name_bytes


def sha_txt_bytes(entries):
    """Return the sha.txt bytes: one line per regular file, in entry order."""
    lines = []
    for entry in entries:
        if entry["kind"] != "f":
            continue
        text, escaped = escape_name(entry["path"])
        line = ("\\" if escaped else "") + entry["sha256"] + "  " + text + "\n"
        lines.append(line.encode("utf-8", "surrogateescape"))
    return b"".join(lines)


def jsonl_bytes(entries):
    """Return the lossless JSON-lines companion: one ASCII JSON object per entry."""
    lines = []
    for entry in entries:
        target = entry.get("target")
        record = {
            "path": os.fsdecode(entry["path"]),
            "kind": entry["kind"],
            "size": entry.get("size"),
            "sha256": entry.get("sha256"),
            "target": os.fsdecode(target) if target is not None else None,
        }
        lines.append(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
    return "".join(lines).encode("ascii")


def write_snapshot(dest_dir, entries):
    """Create DEST_DIR exclusively and write sha.txt and manifest.jsonl inside it.

    The stage folder name (snap-0-setup, snap-1-after-work, snap-2-after-preclear) is the
    caller's choice. An existing folder raises FileExistsError and nothing is written.
    """
    pc_runroot.exclusive_dir(dest_dir, 0o700)
    pc_runroot.write_exclusive(os.path.join(dest_dir, "sha.txt"), sha_txt_bytes(entries), 0o600)
    pc_runroot.write_exclusive(os.path.join(dest_dir, "manifest.jsonl"), jsonl_bytes(entries), 0o600)


def main(argv):
    args = list(argv)
    want_jsonl = False
    if "--jsonl" in args:
        want_jsonl = True
        args.remove("--jsonl")
    if len(args) != 1:
        sys.stderr.write("usage: pc_manifest.py ROOT [--jsonl]\n")
        return 2
    try:
        entries = tree_manifest(args[0])
    except ManifestError as exc:
        sys.stderr.write("manifest refused: %s\n" % exc)
        return 2
    except OSError:
        sys.stderr.write("manifest could not be read\n")
        return 1
    data = jsonl_bytes(entries) if want_jsonl else sha_txt_bytes(entries)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
