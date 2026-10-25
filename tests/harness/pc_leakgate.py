"""Fail-closed leak gate for evidence that is about to become public (EVID-03; D-14, D-16).

The gate scans file names and file contents as text. It refuses (exit 14) any file or file
name that matches one of the six identifier rules mirrored from .gitleaks.toml, or a deny
entry built at run time from this machine (host names with the six-character and generic-name
floors, plus the optional local file .git/info/preclear-deny.txt with a four-character floor).
Output is counts and labels only: a matched value, a home path, a host name, a temporary path
or a deny entry is never printed, logged or put in an error message. A file name that itself
matches is labelled "(file name)", the precedent set by .githooks/checks/denylist.sh.

Every scanner failure fails closed. An exception inside a scan, an empty rule set, an
unreadable deny file or unreadable input is ScannerError (exit 15), never a clean result. A
NUL byte, undecodable bytes, a symlink, a special file and a file above MAX_FILE_BYTES are
refusals, never skips. Each file is read once into memory and scanned as one buffer, so a leak
at byte 0, at the very end or across any chunk boundary is found, and promote writes the same
bytes it scanned.

CLI: python3 -E -s -B pc_leakgate.py [--repo-root R] [--deny-file F] scan PATH...
  exit 0 clean, 14 any finding or refusal (also when there are no files to scan), 15 scanner
  error, 2 usage. Direct runs use -E -s -B, never -I: the pc_ modules import each other.
"""
from __future__ import annotations

import collections
import os
import re
import socket
import stat
import subprocess
import sys

import pc_exitcodes

# FA-4: enough for a sanitised transcript and far above any checkpoint. One byte over is a refusal.
MAX_FILE_BYTES = 5 * 1024 * 1024

FILE_NAME_LABEL = b"(file name)"
SCANNER_ERROR_TEXT = "scanner error"

# Host names shorter than six characters, or on this generic list (copied as data from
# .githooks/checks/denylist.sh), are dropped: a short common word would block ordinary text.
HOST_FLOOR = 6
GENERIC_HOSTS = frozenset(
    "localhost localdomain ubuntu debian fedora centos alpine docker container runner builder "
    "server laptop desktop machine default workstation macbook macbook-pro macbook-air mac-mini "
    "mac-studio mac-pro".split()
)
# Local-file entries keep a four-character floor.
LOCAL_FLOOR = 4


class ScannerError(Exception):
    """The scanner itself failed; the result is a refusal, never a pass. Messages are fixed text."""


Rule = collections.namedtuple("Rule", "id pattern secret_group regex")
Allowlist = collections.namedtuple("Allowlist", "description condition target_rules paths regexes regex_target")
Finding = collections.namedtuple("Finding", "label rule count")
Report = collections.namedtuple("Report", "findings files")
Entry = collections.namedtuple("Entry", "rel kind data mode")


def _make_rule(rule_id, pattern, secret_group=None):
    if not rule_id:
        raise ScannerError(SCANNER_ERROR_TEXT)
    try:
        regex = re.compile(pattern)
    except re.error:
        raise ScannerError(SCANNER_ERROR_TEXT) from None
    return Rule(rule_id, pattern, secret_group, regex)


# The six identifier rules, byte for byte as in .gitleaks.toml (test_leakgate reads the TOML and
# asserts the ids, patterns and secretGroup are identical, so the two cannot drift silently).
RULES = (
    _make_rule("home-path-unix", r'''/(?:Users|home)/[A-Za-z0-9._-]{1,64}(?:[/\s"'`:;,)\]]|$)'''),
    _make_rule("home-path-dash-slug", r'''-(?:Users|home)-[A-Za-z0-9._]{1,64}-'''),
    _make_rule("mac-temp-root", r'''/(?:private/)?var/folders/[A-Za-z0-9_]{2}/'''),
    _make_rule(
        "private-ipv4",
        r'''(?:^|[^0-9.])((?:10\.[0-9]{1,3}|192\.168|172\.(?:1[6-9]|2[0-9]|3[01])|100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7]))\.[0-9]{1,3}\.[0-9]{1,3})(?:[^0-9]|$)''',
        1,
    ),
    _make_rule(
        "internal-hostname",
        r'''\b[A-Za-z0-9][A-Za-z0-9-]*\.(?:local|lan|home\.arpa|internal|localdomain|ts\.net)(?:[^A-Za-z0-9._-]|$)''',
    ),
    _make_rule("email-address", r'''[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b'''),
)

# The two email allowlists, as in .gitleaks.toml. The first holds under an AND condition: the
# public identity address is allowed only in a planning document. The second has no condition
# (the default OR over one list): reserved domains and two exact role addresses.
ALLOWLISTS = (
    Allowlist(
        "The public identity address may appear in planning documents",
        "AND",
        ("email-address",),
        (r'''(?:^|/)\.planning/.+\.md$''',),
        (r'''^bokiko@gmail\.com$''',),
        "match",
    ),
    Allowlist(
        "Reserved domains and two exact role addresses are not personal identifiers",
        "OR",
        ("email-address",),
        (),
        (
            r'''@(?:(?:[A-Za-z0-9-]+\.)*example\.(?:com|org|net|test)|users\.noreply\.github\.com)$''',
            r'''^(?i:noreply|support)@anthropic\.com$''',
        ),
        "match",
    ),
)

# Python-only extra rules and credential shapes (filled in by the next commit of this plan).
PYTHON_ONLY_RULES = ()
CREDENTIAL_RULES = ()


def _active_rules():
    """Return every rule in force, or raise: zero rules loaded must never read as a clean scan."""
    rules = tuple(RULES) + tuple(PYTHON_ONLY_RULES) + tuple(CREDENTIAL_RULES)
    if len(RULES) == 0 or len(rules) == 0:
        raise ScannerError(SCANNER_ERROR_TEXT)
    for rule in rules:
        if not rule.id or not hasattr(rule.regex, "finditer"):
            raise ScannerError(SCANNER_ERROR_TEXT)
    return rules


def _allowed(rule_id, match_text, path_text):
    """Apply the allowlists exactly as gitleaks does: AND needs every criterion, OR needs one."""
    for allowlist in ALLOWLISTS:
        if rule_id not in allowlist.target_rules:
            continue
        criteria = []
        if allowlist.paths:
            criteria.append(any(re.search(pattern, path_text) for pattern in allowlist.paths))
        if allowlist.regexes:
            criteria.append(any(re.search(pattern, match_text) for pattern in allowlist.regexes))
        if not criteria:
            continue
        if (all(criteria) if allowlist.condition == "AND" else any(criteria)):
            return True
    return False


def _deny_regex(deny_entries):
    """One case-insensitive alternation over the deny entries (fixed strings), longest first."""
    entries = set()
    for entry in deny_entries:
        if not isinstance(entry, str):
            raise ScannerError(SCANNER_ERROR_TEXT)
        if entry != "":
            entries.add(entry)
    if not entries:
        return None
    ordered = sorted(entries, key=lambda item: (-len(item), item))
    return re.compile("|".join(re.escape(item) for item in ordered), re.IGNORECASE)


def _label_text(label):
    if isinstance(label, bytes):
        return label.decode("utf-8", "surrogateescape")
    return str(label)


def _count_text(text, path_text, deny_regex):
    """Return {rule id: count} for TEXT, applying the allowlists and the deny entries."""
    counts = {}
    for rule in _active_rules():
        found = 0
        for match in rule.regex.finditer(text):
            if _allowed(rule.id, match.group(0), path_text):
                continue
            found += 1
        if found:
            counts[rule.id] = counts.get(rule.id, 0) + found
    if deny_regex is not None:
        found = sum(1 for _ in deny_regex.finditer(text))
        if found:
            counts["deny-list"] = found
    return counts


def scan_bytes(label, data, deny_entries):
    """Scan one file's bytes and return [(rule id, count), ...] sorted by rule id.

    Refusals come first and are findings with their own ids: refused-oversize (above
    MAX_FILE_BYTES, decided before decoding), refused-binary (a NUL byte) and
    refused-undecodable (not strict UTF-8). An empty file has no findings. LABEL is the file's
    relative path; it only feeds the path condition of the allowlists.
    """
    try:
        _active_rules()
        deny_regex = _deny_regex(deny_entries)
        if len(data) > MAX_FILE_BYTES:
            return [("refused-oversize", 1)]
        if b"\x00" in data:
            return [("refused-binary", 1)]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return [("refused-undecodable", 1)]
        counts = _count_text(text, _label_text(label), deny_regex)
        return sorted(counts.items())
    except ScannerError:
        raise
    except Exception:
        raise ScannerError(SCANNER_ERROR_TEXT) from None


def scan_name(name, deny_entries):
    """Scan one relative path (bytes) as text and return [(rule id, count), ...] sorted by rule id."""
    try:
        _active_rules()
        deny_regex = _deny_regex(deny_entries)
        undecodable = False
        try:
            name.decode("utf-8")
        except UnicodeDecodeError:
            undecodable = True
        text = name.decode("utf-8", "surrogateescape")
        counts = _count_text(text, text, deny_regex)
        if undecodable:
            counts["refused-undecodable"] = counts.get("refused-undecodable", 0) + 1
        return sorted(counts.items())
    except ScannerError:
        raise
    except Exception:
        raise ScannerError(SCANNER_ERROR_TEXT) from None


def _read_limited(path):
    """Read one regular file once, at most MAX_FILE_BYTES + 1 bytes, never following a final symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ScannerError(SCANNER_ERROR_TEXT)
        chunks = []
        total = 0
        limit = MAX_FILE_BYTES + 1
        while total < limit:
            chunk = os.read(fd, min(1024 * 1024, limit - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    finally:
        os.close(fd)
    return b"".join(chunks)


def _entry_for(path_b, rel):
    """Classify one path without following links and read it once when it is a regular file."""
    mode = os.lstat(path_b).st_mode
    if stat.S_ISLNK(mode):
        return Entry(rel, "symlink", None, mode)
    if stat.S_ISDIR(mode):
        return Entry(rel, "dir", None, mode)
    if stat.S_ISREG(mode):
        return Entry(rel, "file", _read_limited(path_b), mode)
    return Entry(rel, "special", None, mode)


def collect_tree(root):
    """Walk ROOT on raw bytes in sorted order and return a list of Entry (rel, kind, data, mode).

    kind is file, dir, symlink or special. Files are read once; symlinks and special files are
    never opened, they are refusal entries. A root that is itself a symlink is one symlink entry.
    Any filesystem error is ScannerError.
    """
    try:
        root_b = os.fsencode(os.fspath(root))
        top = os.lstat(root_b).st_mode
        if stat.S_ISLNK(top) or not stat.S_ISDIR(top):
            return [_entry_for(root_b, os.path.basename(root_b.rstrip(b"/")) or b"root")]

        def fail(error):
            raise error

        entries = []
        for dirpath, dirnames, filenames in os.walk(root_b, onerror=fail):
            rel_dir = b"" if dirpath == root_b else dirpath[len(root_b):].lstrip(b"/")
            for name in list(dirnames) + list(filenames):
                rel = rel_dir + b"/" + name if rel_dir else name
                entries.append(_entry_for(os.path.join(dirpath, name), rel))
        entries.sort(key=lambda entry: entry.rel)
        return entries
    except ScannerError:
        raise
    except Exception:
        raise ScannerError(SCANNER_ERROR_TEXT) from None


def collect_path(path):
    """Collect a directory tree, or one file named by its base name."""
    path_b = os.fsencode(os.fspath(path))
    try:
        mode = os.lstat(path_b).st_mode
    except OSError:
        raise ScannerError(SCANNER_ERROR_TEXT) from None
    if stat.S_ISDIR(mode) and not stat.S_ISLNK(mode):
        return collect_tree(path_b)
    try:
        return [_entry_for(path_b, os.path.basename(path_b.rstrip(b"/")) or b"input")]
    except ScannerError:
        raise
    except Exception:
        raise ScannerError(SCANNER_ERROR_TEXT) from None


def scan_entries(entries, deny_entries):
    """Scan names and contents of every entry and return a Report(findings, files).

    findings is a list of Finding(label bytes, rule id, count) sorted by label bytes and then
    rule id. A name that itself matches relabels the file "(file name)" (names are never
    echoed). files counts the regular files that were scanned.
    """
    try:
        _active_rules()
        totals = {}
        files = 0

        def add(label, rule, count):
            key = (label, rule)
            totals[key] = totals.get(key, 0) + count

        for entry in entries:
            name_findings = scan_name(entry.rel, deny_entries)
            label = FILE_NAME_LABEL if name_findings else entry.rel
            for rule, count in name_findings:
                add(label, rule, count)
            if entry.kind == "file":
                files += 1
                for rule, count in scan_bytes(entry.rel, entry.data, deny_entries):
                    add(label, rule, count)
            elif entry.kind == "symlink":
                add(label, "refused-symlink", 1)
            elif entry.kind == "special":
                add(label, "refused-special", 1)
        findings = [Finding(label, rule, count) for (label, rule), count in sorted(totals.items())]
        return Report(findings, files)
    except ScannerError:
        raise
    except Exception:
        raise ScannerError(SCANNER_ERROR_TEXT) from None


def scan_tree(root, deny_entries):
    """Collect ROOT and scan it; see collect_tree and scan_entries."""
    return scan_entries(collect_tree(root), deny_entries)


def _safe_label(label):
    return ascii(label.decode("utf-8", "backslashreplace"))[1:-1]


def format_findings(report):
    """One line per finding, sorted by label bytes then rule id; counts and labels only."""
    lines = []
    for finding in sorted(report.findings, key=lambda item: (item.label, item.rule)):
        lines.append(
            "leak gate FAILED: %s (%d match(es), rule %s)\n" % (_safe_label(finding.label), finding.count, finding.rule)
        )
    return "".join(lines)


def _git_env():
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    return env


def machine_hostnames():
    """Host names of this machine: gethostname and its short form, plus scutil names on macOS."""
    names = []
    try:
        full = socket.gethostname()
        names.append(full)
        names.append(full.split(".")[0])
    except OSError:
        pass
    if sys.platform == "darwin":
        for key in ("LocalHostName", "ComputerName"):
            try:
                result = subprocess.run(
                    ["scutil", "--get", key],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            if result.returncode == 0:
                names.append(result.stdout.decode("utf-8", "replace").strip())
    return names


def host_entries(hostnames=None):
    """Return the sorted unique host-name deny entries: at least six characters, not generic."""
    names = machine_hostnames() if hostnames is None else hostnames
    kept = set()
    for name in names:
        name = name.strip()
        if len(name) >= HOST_FLOOR and name.lower() not in GENERIC_HOSTS:
            kept.add(name)
    return sorted(kept)


def _git_deny_path(repo_root):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-path", "info/preclear-deny.txt"],
            cwd=os.fspath(repo_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            env=_git_env(),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    path = result.stdout.decode("utf-8", "replace").strip()
    if path == "":
        return None
    if not os.path.isabs(path):
        path = os.path.join(os.fspath(repo_root), path)
    return path


def local_file_entries(repo_root, deny_file=None):
    """Read the local deny file and return its usable entries (sorted, unique).

    DENY_FILE overrides the default location .git/info/preclear-deny.txt (resolved with
    git rev-parse --git-path). No git or no file means no entries. Comment and blank lines are
    skipped, carriage returns are stripped and entries under four characters are dropped. A file
    that exists but cannot be read or decoded raises ScannerError with a fixed message. The
    entries are private: they are never printed, logged or put in a message.
    """
    path = deny_file if deny_file is not None else _git_deny_path(repo_root)
    if path is None or not os.path.lexists(path):
        return []
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise ScannerError("could not read the local deny list") from None
    entries = set()
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        if len(line) >= LOCAL_FLOOR:
            entries.add(line)
    return sorted(entries)


def build_deny_entries(repo_root, hostnames=None, deny_file=None):
    """Return the sorted unique union of the host-name entries and the local file entries."""
    union = set(host_entries(hostnames))
    union.update(local_file_entries(repo_root, deny_file))
    return sorted(union)


def default_repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


USAGE_TEXT = "usage: pc_leakgate.py [--repo-root R] [--deny-file F] scan PATH...\n"


def main(argv):
    args = list(argv)
    repo_root = default_repo_root()
    deny_file = None
    while args and args[0].startswith("--"):
        option = args.pop(0)
        if option == "--repo-root" and args:
            repo_root = args.pop(0)
        elif option == "--deny-file" and args:
            deny_file = args.pop(0)
        else:
            sys.stderr.write(USAGE_TEXT)
            return pc_exitcodes.USAGE
    if len(args) < 2 or args[0] != "scan":
        sys.stderr.write(USAGE_TEXT)
        return pc_exitcodes.USAGE
    paths = args[1:]
    try:
        deny = build_deny_entries(repo_root, None, deny_file)
        entries = []
        for index, path in enumerate(paths):
            collected = collect_path(path)
            if len(paths) > 1:
                prefix = ("%d/" % (index + 1)).encode("ascii")
                collected = [entry._replace(rel=prefix + entry.rel) for entry in collected]
            entries.extend(collected)
        report = scan_entries(entries, deny)
    except Exception:
        sys.stderr.write("leak gate error: %s\n" % SCANNER_ERROR_TEXT)
        return pc_exitcodes.SCANNER_ERROR
    if report.findings:
        sys.stderr.write(format_findings(report))
        return pc_exitcodes.LEAK_REFUSED
    if report.files == 0:
        sys.stderr.write("leak gate FAILED: no files to scan\n")
        return pc_exitcodes.LEAK_REFUSED
    sys.stdout.write("leak gate passed: %d file(s) scanned, 0 findings\n" % report.files)
    return pc_exitcodes.OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
