"""Read-only comparer of two evidence trees for one row (EVID-06; D-07, D-08).

It lines a rerun up against a committed baseline and prints facts. It never prints a verdict for a row:
differences are listed and never judged, and a content digest that differs is expected and is only listed.
Both trees are opened for reading only. This module writes nothing anywhere but standard output.

Proof that nothing was touched: the whole tree named by --old and the whole tree named by --new are digested
before the comparison and again after it, and the report prints both pairs and whether each side is unchanged.
The digest is sha256 over pc_manifest.jsonl_bytes of tree_manifest, so it changes when a byte, a file name, an
empty folder or a symlink target changes. File modes and timestamps are not part of it.

CLI: python3 -E -s -B pc_compare.py --old DIR --new DIR [--row ID]
  DIR is a folder that holds the row folder (a committed publication folder or a rerun folder).
  Exit 0 whenever both trees were readable, whatever they differ in; exit 2 for bad usage or a tree that cannot
  be read. Error text is fixed and never echoes a path or an argument.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys

import pc_exitcodes
import pc_manifest

PROG = "pc_compare.py"
USAGE_LINE = "usage: pc_compare.py --old DIR --new DIR [--row ID]"
DEFAULT_ROW = "row1-wrong-binding"

MESSAGE_USAGE = "invalid command line"
MESSAGE_UNREADABLE = "a tree could not be read"
MESSAGE_NO_ROW = "the row folder is missing on one side"

NEUTRAL_FILES_ONLY_NOTE = "(a file only on the rerun side is a difference, not a fault)"
MODES_SENTENCE = "file modes and timestamps are not part of the digest"
DIFFERENCES_HEADER = "differences, listed and not judged"

_ROW_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")


class CompareError(Exception):
    """A tree could not be read; the message is fixed text."""


def _printable(text):
    """ASCII-only text: anything else is shown as an escape, so no stream can fail on it."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _entry_name(raw):
    """A manifest path (raw bytes) as one printable line: newline and carriage return are escaped."""
    escaped, _changed = pc_manifest.escape_name(raw)
    return _printable(escaped)


def tree_digest(root):
    """Hex sha256 over the lossless manifest bytes of the tree at root. Reads only."""
    return hashlib.sha256(pc_manifest.jsonl_bytes(pc_manifest.tree_manifest(root))).hexdigest()


def _is_real_folder(path):
    if not isinstance(path, str) or path == "":
        return False
    trimmed = path.rstrip(os.sep) or os.sep
    return os.path.isdir(trimmed) and not os.path.islink(trimmed)


def _row_folder(tree, row):
    return os.path.join(tree, row)


def _entry_labels(row_folder):
    """The set of labels of every entry below the row folder: a path, with a trailing slash for a folder."""
    labels = set()
    for entry in pc_manifest.tree_manifest(row_folder):
        label = _entry_name(entry["path"])
        labels.add(label + "/" if entry["kind"] == "d" else label)
    return labels


def _sorted_labels(labels):
    return sorted(labels, key=lambda item: item.encode("ascii", "backslashreplace"))


def compare_rows(old_tree, new_tree, row):
    """Read both row folders and return the structured differences (a dict). Only reads."""
    old_labels = _entry_labels(_row_folder(old_tree, row))
    new_labels = _entry_labels(_row_folder(new_tree, row))
    return {
        "row": row,
        "old_name": _printable(os.path.basename(old_tree.rstrip(os.sep))),
        "new_name": _printable(os.path.basename(new_tree.rstrip(os.sep))),
        "only_old": _sorted_labels(old_labels - new_labels),
        "only_new": _sorted_labels(new_labels - old_labels),
    }


def report_lines(result):
    """The report lines for one comparison, under neutral headings."""
    lines = [DIFFERENCES_HEADER]
    lines.append("files only on the old side: %d" % len(result["only_old"]))
    lines.extend("  " + name for name in result["only_old"])
    lines.append("files only on the rerun side: %d" % len(result["only_new"]))
    lines.extend("  " + name for name in result["only_new"])
    lines.append(NEUTRAL_FILES_ONLY_NOTE)
    return lines


class _Parser(argparse.ArgumentParser):
    """An argument parser whose errors print fixed lines and exit 2, never echoing a value."""

    def __init__(self, err):
        super().__init__(prog=PROG, add_help=False, allow_abbrev=False)
        self._err = err

    def error(self, message):
        self._err.write(USAGE_LINE + "\n")
        self._err.write("%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        raise SystemExit(pc_exitcodes.USAGE)


def _refuse(err, message):
    err.write("%s: %s\n" % (PROG, message))
    return pc_exitcodes.USAGE


def main(argv, out=None, err=None):
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = _Parser(err)
    parser.add_argument("--old", default=None)
    parser.add_argument("--new", default=None)
    parser.add_argument("--row", default=DEFAULT_ROW)
    try:
        args = parser.parse_args(list(argv))
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else pc_exitcodes.USAGE
    if args.old is None or args.new is None or not _ROW_ID.match(args.row):
        err.write(USAGE_LINE + "\n")
        err.write("%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        return pc_exitcodes.USAGE
    old_tree, new_tree, row = args.old, args.new, args.row
    if not (_is_real_folder(old_tree) and _is_real_folder(new_tree)):
        return _refuse(err, MESSAGE_UNREADABLE)
    if not (_is_real_folder(_row_folder(old_tree, row)) and _is_real_folder(_row_folder(new_tree, row))):
        return _refuse(err, MESSAGE_NO_ROW)
    try:
        before = (tree_digest(old_tree), tree_digest(new_tree))
        result = compare_rows(old_tree, new_tree, row)
        after = (tree_digest(old_tree), tree_digest(new_tree))
    except (OSError, pc_manifest.ManifestError, CompareError):
        return _refuse(err, MESSAGE_UNREADABLE)
    lines = ["compare row %s: old %s, new %s" % (_printable(row), result["old_name"], result["new_name"])]
    lines.append("tree digest before: old %s, new %s" % before)
    lines.extend(report_lines(result))
    lines.append("tree digest after: old %s, new %s" % after)
    lines.append("old unchanged: %s" % ("yes" if before[0] == after[0] else "no"))
    lines.append("new unchanged: %s" % ("yes" if before[1] == after[1] else "no"))
    lines.append(MODES_SENTENCE)
    out.write("\n".join(lines) + "\n")
    out.flush()
    return pc_exitcodes.OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
