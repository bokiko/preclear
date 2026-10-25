"""Gate-first, exclusive-creation copy of a stage into tests/evidence (EVID-03; D-16).

promote collects the whole stage once (every file is read once into memory), runs the leak gate
over those bytes, and creates nothing unless every entry passes. Only then does it create the
destination: every directory with pc_runroot.exclusive_dir and every file with
pc_runroot.write_exclusive, written from the exact bytes that were scanned. Nothing is ever
deleted, moved or overwritten. Output is counts only.

CLI: python3 -E -s -B pc_promote.py [--repo-root R] STAGE DEST
  exit 0 promoted, 14 the gate found a leak, 15 scanner error, 17 promote refused, 2 usage.
"""
from __future__ import annotations

import collections
import os
import sys

import pc_exitcodes
import pc_leakgate
import pc_runroot

PromoteResult = collections.namedtuple("PromoteResult", "code message report_text")

EVIDENCE_PARTS = ("tests", "evidence")


def _refused(message):
    return PromoteResult(pc_exitcodes.PROMOTE_REFUSED, "promote refused: " + message, "")


def _under(path, root):
    return path != root and path.startswith(root + os.sep)


def promote(stage, dest, repo_root, config_dir=None, deny_entries=None):
    """Promote STAGE into the new path DEST under REPO_ROOT/tests/evidence.

    Returns PromoteResult(code, message, report_text): code 0, 14 (leak), 15 (scanner error) or
    17 (refused). report_text holds the gate's counts-and-labels lines when the gate refused.
    """
    evidence = os.path.realpath(os.path.join(repo_root, *EVIDENCE_PARTS))
    real_dest = os.path.realpath(dest)
    if not _under(real_dest, evidence):
        return _refused("the destination is not under the evidence folder")
    if os.path.lexists(dest):
        return _refused("the destination already exists")
    if os.path.islink(stage) or not os.path.isdir(stage):
        return _refused("the stage is not a directory")
    try:
        entries = pc_leakgate.collect_tree(stage)
    except pc_leakgate.ScannerError:
        return PromoteResult(pc_exitcodes.SCANNER_ERROR, "promote stopped: scanner error", "")
    if not any(entry.kind == "file" for entry in entries):
        return _refused("the stage holds no files")
    try:
        deny = deny_entries if deny_entries is not None else pc_leakgate.build_deny_entries(repo_root, None, None)
        report = pc_leakgate.scan_entries(entries, deny)
    except pc_leakgate.ScannerError:
        return PromoteResult(pc_exitcodes.SCANNER_ERROR, "promote stopped: scanner error", "")
    if report.findings:
        total = sum(finding.count for finding in report.findings)
        return PromoteResult(
            pc_exitcodes.LEAK_REFUSED,
            "promote refused by the leak gate: %d finding(s) in %d file(s)" % (total, len(set(f.label for f in report.findings))),
            pc_leakgate.format_findings(report),
        )
    dest_b = os.fsencode(os.path.abspath(dest))
    try:
        pc_runroot.exclusive_dir(dest_b, 0o755)
    except FileExistsError:
        return _refused("the destination already exists")
    count = 0
    for entry in entries:
        target = os.path.join(dest_b, entry.rel)
        if entry.kind == "dir":
            pc_runroot.exclusive_dir(target, 0o755)
    for entry in entries:
        if entry.kind == "file":
            target = os.path.join(dest_b, entry.rel)
            pc_runroot.write_exclusive(target, entry.data, 0o755 if entry.mode & 0o111 else 0o644)
            count += 1
    return PromoteResult(pc_exitcodes.OK, "promoted %d file(s)" % count, "")


USAGE_TEXT = "usage: pc_promote.py [--repo-root R] STAGE DEST\n"


def main(argv):
    args = list(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    if args and args[0] == "--repo-root":
        if len(args) < 2:
            sys.stderr.write(USAGE_TEXT)
            return pc_exitcodes.USAGE
        repo_root = args[1]
        args = args[2:]
    if len(args) != 2:
        sys.stderr.write(USAGE_TEXT)
        return pc_exitcodes.USAGE
    try:
        result = promote(args[0], args[1], repo_root)
    except Exception:
        sys.stderr.write("promote stopped: scanner error\n")
        return pc_exitcodes.SCANNER_ERROR
    if result.report_text:
        sys.stderr.write(result.report_text)
    stream = sys.stdout if result.code == pc_exitcodes.OK else sys.stderr
    stream.write(result.message + "\n")
    return result.code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
