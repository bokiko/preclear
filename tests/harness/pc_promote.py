"""Gate-first, exclusive-creation copy of a stage into tests/evidence (EVID-03; D-16).

promote collects the whole stage once (every file is read once into memory), runs the leak gate
over those bytes, and creates nothing unless every entry passes. Only then does it create the
destination: every directory with pc_runroot.exclusive_dir and every file with
pc_runroot.write_exclusive, written from the exact bytes that were scanned, so content that
changes between the scan and the copy cannot reach the destination unscanned. Nothing is ever
deleted, moved or overwritten, and promote never creates the harness config directory. Output is
counts only; a path never appears in a message.

Refused with exit 17: a destination outside <repo>/tests/evidence (or the folder itself), one that
already exists, one reached through a symlink or a dot-dot segment, a stage that is a symlink or
holds a dot-dot segment, any stage or destination at or under the harness Claude config directory
(PRECLEAR_HARNESS_HOME, default ~/.preclear-harness, then claude-config), names with a NUL, and a
missing, unreadable or empty stage. Gate results pass through unchanged: 14 a finding, 15 a
scanner error. The final destination is created exclusively, so of two racing promotes exactly
one wins. A failure while writing reports 17 "partial promote in <destination>" and deletes
nothing.

promote_into (plan 04-03) is the one other way to put bytes into tests/evidence: it adds the flat files of a stage to an
existing real folder (a dated folder, or on request the evidence folder itself) and nothing else. Every staged name is
checked (a plain name, not a dot name, not already there) and every staged byte is scanned by the leak gate before the
first file is created, so a refusal creates nothing; each file is then created exclusively from the scanned bytes.
Nothing is overwritten, renamed or deleted, and a folder that is a symlink or lies outside tests/evidence is refused
with 17.

CLI: python3 -E -s -B pc_promote.py [--repo-root R] STAGE DEST
  exit 0 promoted, 14 the gate found a leak, 15 scanner error, 17 promote refused, 2 usage.
"""
from __future__ import annotations

import collections
import os
import stat
import sys

import pc_exitcodes
import pc_leakgate
import pc_runroot

PromoteResult = collections.namedtuple("PromoteResult", "code message report_text")

EVIDENCE_PARTS = ("tests", "evidence")
HARNESS_HOME_ENV = "PRECLEAR_HARNESS_HOME"
DEFAULT_HARNESS_FOLDER = ".preclear-harness"
CONFIG_FOLDER = "claude-config"

DIR_MODE = 0o755
FILE_MODE = 0o644
EXEC_FILE_MODE = 0o755


class _Refused(Exception):
    """Internal: carries the fixed refusal message."""


def _refused(message):
    return PromoteResult(pc_exitcodes.PROMOTE_REFUSED, "promote refused: " + message, "")


def _scanner_error():
    return PromoteResult(pc_exitcodes.SCANNER_ERROR, "promote stopped: scanner error", "")


def _under(path, root):
    """True when PATH is strictly below ROOT."""
    return path != root and path.startswith(root.rstrip(os.sep) + os.sep)


def _at_or_under(path, root):
    return path == root or _under(path, root)


def default_config_dir():
    """The harness-owned Claude config directory; never created by promote."""
    base = os.environ.get(HARNESS_HOME_ENV)
    if not base:
        base = os.path.join(os.path.expanduser("~"), DEFAULT_HARNESS_FOLDER)
    return os.path.join(base, CONFIG_FOLDER)


def _as_text(value, label):
    try:
        text = os.fspath(value)
    except TypeError:
        raise _Refused("%s is not a path" % label) from None
    if isinstance(text, bytes):
        text = os.fsdecode(text)
    if text == "" or "\x00" in text:
        raise _Refused("%s is empty or holds a NUL" % label)
    if ".." in text.split(os.sep):
        raise _Refused("%s holds a dot-dot segment" % label)
    return text


def _check_destination(dest_text, repo_text):
    """Return (lexical evidence folder, lexical destination, [paths still to create]) or raise _Refused."""
    lex_repo = os.path.abspath(repo_text)
    lex_evidence = os.path.join(lex_repo, *EVIDENCE_PARTS)
    lex_dest = os.path.abspath(dest_text)
    if not _under(lex_dest, lex_evidence):
        raise _Refused("the destination is not under the evidence folder")
    relative = os.path.relpath(lex_dest, lex_evidence).split(os.sep)
    # Walk from the repository root: tests and evidence must be real folders, every folder on the
    # way down must be a real folder, and the destination itself must not exist.
    path = lex_repo
    to_create = []
    missing_from = None
    parts = list(EVIDENCE_PARTS) + relative
    for index, part in enumerate(parts):
        path = os.path.join(path, part)
        final = index == len(parts) - 1
        try:
            mode = os.lstat(path).st_mode
        except FileNotFoundError:
            if index < len(EVIDENCE_PARTS):
                raise _Refused("the evidence folder does not exist") from None
            if missing_from is None:
                missing_from = index
            to_create.append(path)
            continue
        if missing_from is not None:
            raise _Refused("the destination path changed while it was checked")
        if final:
            raise _Refused("the destination already exists")
        if stat.S_ISLNK(mode):
            raise _Refused("the destination is reached through a symlink")
        if not stat.S_ISDIR(mode):
            raise _Refused("a file is in the way of the destination")
    real_evidence = os.path.realpath(lex_evidence)
    if not _under(os.path.realpath(lex_dest), real_evidence):
        raise _Refused("the destination does not resolve under the evidence folder")
    return lex_evidence, lex_dest, to_create


def _check_stage(stage_text):
    if os.path.islink(stage_text):
        raise _Refused("the stage is a symlink")
    if not os.path.isdir(stage_text):
        raise _Refused("the stage is not a directory")
    try:
        os.listdir(stage_text)
    except OSError:
        raise _Refused("the stage cannot be read") from None


def promote(stage, dest, repo_root, config_dir=None, deny_entries=None, allow_default_deny=False):
    """Promote STAGE into the new path DEST under REPO_ROOT/tests/evidence.

    Returns PromoteResult(code, message, report_text): code 0, 14 (leak), 15 (scanner error) or
    17 (refused). report_text holds the gate's counts-and-labels lines when the gate refused.
    DENY_ENTRIES None builds the default entries at run time (a failure to do so is exit 15) only when the
    caller opts in with ALLOW_DEFAULT_DENY=True; without the opt-out a missing list raises ValueError, because
    the default entries carry no login and a caller that forgot to pass the sanitizer's list would file a run
    whose login the gate never checks (WR-03). An explicit empty list is accepted.
    """
    if deny_entries is None and not allow_default_deny:
        raise ValueError("promote needs the deny entries unless allow_default_deny is passed")
    try:
        stage_text = _as_text(stage, "the stage")
        dest_text = _as_text(dest, "the destination")
        repo_text = _as_text(repo_root, "the repository root")
        _check_stage(stage_text)
        lex_evidence, lex_dest, to_create = _check_destination(dest_text, repo_text)
        config = os.path.realpath(config_dir if config_dir is not None else default_config_dir())
        if _at_or_under(os.path.realpath(stage_text), config):
            raise _Refused("the stage is under the harness config directory")
        if _at_or_under(os.path.realpath(lex_dest), config):
            raise _Refused("the destination is under the harness config directory")
    except _Refused as exc:
        return _refused(str(exc))
    except OSError:
        return _refused("a path could not be checked")

    try:
        entries = pc_leakgate.collect_tree(stage_text)
    except pc_leakgate.ScannerError:
        return _scanner_error()
    if not any(entry.kind == "file" for entry in entries):
        return _refused("the stage holds no files")
    relative_dest = os.path.relpath(lex_dest, lex_evidence)
    try:
        deny = deny_entries if deny_entries is not None else pc_leakgate.build_deny_entries(repo_text, None, None)
        report = pc_leakgate.scan_entries(entries, deny)
        name_findings = pc_leakgate.scan_name(os.fsencode(relative_dest), deny)
    except pc_leakgate.ScannerError:
        return _scanner_error()
    except Exception:
        return _scanner_error()
    findings = list(report.findings)
    findings.extend(pc_leakgate.Finding(b"(destination name)", rule, count) for rule, count in name_findings)
    if findings:
        total = sum(finding.count for finding in findings)
        labels = len(set(finding.label for finding in findings))
        return PromoteResult(
            pc_exitcodes.LEAK_REFUSED,
            "promote refused by the leak gate: %d finding(s) in %d label(s)" % (total, labels),
            pc_leakgate.format_findings(pc_leakgate.Report(findings, report.files)),
        )

    # Gate passed for the whole set: only now is anything created. Every file below is written
    # from the bytes that were scanned.
    for path in to_create[:-1]:
        try:
            pc_runroot.exclusive_dir(os.fsencode(path), DIR_MODE)
        except FileExistsError:
            if os.path.islink(path) or not os.path.isdir(path):
                return _refused("a file is in the way of the destination")
        except OSError:
            return _refused("the destination folder could not be created")
    dest_b = os.fsencode(lex_dest)
    try:
        pc_runroot.exclusive_dir(dest_b, DIR_MODE)
    except FileExistsError:
        return _refused("the destination already exists")
    except OSError:
        return _refused("the destination folder could not be created")
    count = 0
    try:
        for entry in entries:
            if entry.kind == "dir":
                pc_runroot.exclusive_dir(os.path.join(dest_b, entry.rel), DIR_MODE)
        for entry in entries:
            if entry.kind == "file":
                mode = EXEC_FILE_MODE if entry.mode & 0o111 else FILE_MODE
                pc_runroot.write_exclusive(os.path.join(dest_b, entry.rel), entry.data, mode)
                count += 1
    except OSError:
        return PromoteResult(
            pc_exitcodes.PROMOTE_REFUSED, "partial promote in %s" % relative_dest.replace(os.sep, "/"), ""
        )
    return PromoteResult(pc_exitcodes.OK, "promoted %d file(s)" % count, "")


def _check_folder(folder_text, repo_text, allow_evidence_root):
    """Return (lexical evidence folder, lexical folder) for an existing real folder under tests/evidence or raise _Refused.

    Every component from the repository root down must be a real folder (no symlink, no file). The folder must
    resolve inside the real evidence folder; the evidence folder itself is accepted only on request.
    """
    lex_repo = os.path.abspath(repo_text)
    lex_evidence = os.path.join(lex_repo, *EVIDENCE_PARTS)
    lex_folder = os.path.abspath(folder_text)
    if lex_folder == lex_evidence:
        if not allow_evidence_root:
            raise _Refused("the folder is the evidence folder itself")
    elif not _under(lex_folder, lex_evidence):
        raise _Refused("the folder is not under the evidence folder")
    relative = [] if lex_folder == lex_evidence else os.path.relpath(lex_folder, lex_evidence).split(os.sep)
    path = lex_repo
    for part in list(EVIDENCE_PARTS) + relative:
        path = os.path.join(path, part)
        try:
            mode = os.lstat(path).st_mode
        except FileNotFoundError:
            raise _Refused("the folder does not exist") from None
        if stat.S_ISLNK(mode):
            raise _Refused("the folder is reached through a symlink")
        if not stat.S_ISDIR(mode):
            raise _Refused("a file is in the way of the folder")
    real_evidence = os.path.realpath(lex_evidence)
    real_folder = os.path.realpath(lex_folder)
    if real_folder != real_evidence and not _under(real_folder, real_evidence):
        raise _Refused("the folder does not resolve under the evidence folder")
    if real_folder == real_evidence and not allow_evidence_root:
        raise _Refused("the folder is the evidence folder itself")
    return lex_evidence, lex_folder


def _flat_names(entries, lex_folder):
    """The flat file entries of a stage, or raise _Refused for a folder, an odd name or a name that exists.

    Every name is checked before the caller creates anything: a name with a slash, a dot-dot, a leading dot, a NUL
    or nothing at all, a stage entry that is not a regular file, and a name that already exists in the folder (a
    symlink or a dangling one included) each refuse the whole request.
    """
    folder_b = os.fsencode(lex_folder)
    files = []
    seen = set()
    for entry in entries:
        if entry.kind != "file":
            raise _Refused("the stage holds an entry that is not a flat file")
        name = entry.rel
        if name == b"" or b"/" in name or b"\x00" in name or name in (b".", b"..") or name.startswith(b"."):
            raise _Refused("a staged name is not a plain file name")
        if name in seen:
            raise _Refused("a staged name is repeated")
        seen.add(name)
        if os.path.lexists(os.path.join(folder_b, name)):
            raise _Refused("a staged name already exists in the folder")
        files.append(entry)
    return files


def promote_into(stage, folder, repo_root, config_dir=None, deny_entries=None, allow_evidence_root=False):
    """Add the flat files of STAGE to the existing folder FOLDER under REPO_ROOT/tests/evidence (D-14, D-15).

    Nothing is overwritten, renamed or deleted. The folder must be a real folder (not a symlink, no symlink on
    the way) whose realpath lies inside the evidence folder, and not the evidence folder itself unless
    ALLOW_EVIDENCE_ROOT is passed (the single top-level evidence README). Every staged name must be a plain file
    name that does not exist in the folder yet. All names are checked, and every staged byte is scanned by the leak
    gate, before the first file is created, so a refusal creates nothing; only then is each file created
    exclusively, from the bytes that were scanned.

    DENY_ENTRIES is required: None is refused with exit 15 before anything else. Returns the same
    PromoteResult as promote, with the same code mapping: 0 promoted, 14 a leak finding, 15 a scanner error,
    17 refused. A failure while writing reports 17 "partial promote" and deletes nothing.
    """
    if deny_entries is None:
        return _scanner_error()
    try:
        stage_text = _as_text(stage, "the stage")
        folder_text = _as_text(folder, "the folder")
        repo_text = _as_text(repo_root, "the repository root")
        _check_stage(stage_text)
        lex_evidence, lex_folder = _check_folder(folder_text, repo_text, bool(allow_evidence_root))
        config = os.path.realpath(config_dir if config_dir is not None else default_config_dir())
        if _at_or_under(os.path.realpath(stage_text), config):
            raise _Refused("the stage is under the harness config directory")
        if _at_or_under(os.path.realpath(lex_folder), config):
            raise _Refused("the folder is under the harness config directory")
    except _Refused as exc:
        return _refused(str(exc))
    except OSError:
        return _refused("a path could not be checked")

    try:
        entries = pc_leakgate.collect_tree(stage_text)
    except pc_leakgate.ScannerError:
        return _scanner_error()
    if not any(entry.kind == "file" for entry in entries):
        return _refused("the stage holds no files")
    try:
        files = _flat_names(entries, lex_folder)
    except _Refused as exc:
        return _refused(str(exc))
    except OSError:
        return _refused("a path could not be checked")
    relative_folder = os.path.relpath(lex_folder, lex_evidence)
    try:
        report = pc_leakgate.scan_entries(entries, deny_entries)
        name_findings = []
        for entry in files:
            label = (b"" if relative_folder == "." else os.fsencode(relative_folder) + b"/") + entry.rel
            name_findings.extend(pc_leakgate.scan_name(label, deny_entries))
    except pc_leakgate.ScannerError:
        return _scanner_error()
    except Exception:
        return _scanner_error()
    findings = list(report.findings)
    findings.extend(pc_leakgate.Finding(b"(file name)", rule, count) for rule, count in name_findings)
    if findings:
        total = sum(finding.count for finding in findings)
        labels = len(set(finding.label for finding in findings))
        return PromoteResult(
            pc_exitcodes.LEAK_REFUSED,
            "promote refused by the leak gate: %d finding(s) in %d label(s)" % (total, labels),
            pc_leakgate.format_findings(pc_leakgate.Report(findings, report.files)),
        )

    # Every check and the gate passed for the whole set: only now is anything created, from the scanned bytes.
    try:
        mode = os.lstat(lex_folder).st_mode
    except OSError:
        return _refused("the folder changed while it was checked")
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        return _refused("the folder changed while it was checked")
    folder_b = os.fsencode(lex_folder)
    count = 0
    try:
        for entry in files:
            pc_runroot.write_exclusive(os.path.join(folder_b, entry.rel), entry.data, FILE_MODE)
            count += 1
    except OSError:
        label = relative_folder.replace(os.sep, "/")
        return PromoteResult(pc_exitcodes.PROMOTE_REFUSED, "partial promote in %s" % label, "")
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
        # The command line has no sanitizer, and its default entries carry no login by design.
        result = promote(args[0], args[1], repo_root, allow_default_deny=True)
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
