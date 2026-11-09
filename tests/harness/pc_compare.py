"""Read-only comparer of two evidence trees for one row (EVID-06; D-07, D-08).

It lines a rerun up against a committed baseline and prints facts. It never prints a verdict for a row:
differences are listed and never judged, and a content digest that differs is expected and is only listed.
Both trees are opened for reading only. This module writes nothing anywhere but standard output.

What it lists (D-07), for the one row folder inside each tree:
  * files and folders present on one side only, in both directions
  * the row README headings that differ
  * helper-call counts from wrapper-calls.log: total, per first argument, the multiset of exit codes
  * tool-call counts per tool name from the full traces (s1, s2, s3), with the Calls header value and the
    ERROR and REFUSAL/DENIAL flag counts; a trace that exists on one side only is reported on that side
  * byte measurements read from both shapes of measurements.txt and compared with the cap constants of
    pc_measure (a total of exactly 4096 is within the cap, 4097 is above it; the same for every section)
  * listed, not judged: per snapshot the sha.txt paths whose digests differ and the paths on one side only
    (a leading helper-state or ledgers folder is read as ckpt), the tools.txt rule difference with both counts,
    digests.txt, claude-version.txt and usage.txt
Text that is quoted from a file is printed on a line of the form "  content: <text>", so a reader (and the
vocabulary test) can tell the comparer's own words from content.

Proof that nothing was touched: the whole tree named by --old and the whole tree named by --new are digested
before the comparison and again after it, and the report prints both pairs and whether each side is unchanged.
The digest is sha256 over pc_manifest.jsonl_bytes of tree_manifest, so it changes when a byte, a file name, an
empty folder or a symlink target changes. File modes and timestamps are not part of it.

The committed token <repo>/<run> and the newer token <run> are read as equal before any text-dependent
comparison. A file that is absent or malformed is reported as such for that side and the run goes on.

All rows (plan 04-18; RERUN-03, D-15): `--all-rows --new DIR [--old DIR]` maps every row id of the registry to the committed
folder of the reference tree (the -rerun folder when it exists, else the bare folder) and compares the highest filed
attempt of each row with it. A STOPPED- or SKIPPED- folder is listed and never compared, a registry id with no outcome
folder at all is listed as not run, the committed older attempts (the other folders a reference tree holds for a row id)
are listed as older attempts not compared, and each layout is printed with the words no structural reference. --old
defaults to DEFAULT_REFERENCE, the one value the later swap commit changes.

CLI: python3 -E -s -B pc_compare.py --old DIR --new DIR [--row ID]
     python3 -E -s -B pc_compare.py --all-rows --new DIR [--old DIR]
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

import pc_allowlist
import pc_exitcodes
import pc_manifest
import pc_measure
import pc_mine

PROG = "pc_compare.py"
USAGE_LINE = "usage: pc_compare.py --old DIR --new DIR [--row ID] | --all-rows --new DIR [--old DIR]"
DEFAULT_ROW = "row1-wrong-binding"
# The reference tree of --all-rows when --old is not given: repo-relative, resolved against the repository of this script.
# Plan 04-21 changes this one value in its swap commit.
DEFAULT_REFERENCE = "tests/evidence/publication-2026-10-20"
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MESSAGE_USAGE = "invalid command line"
MESSAGE_UNREADABLE = "a tree could not be read"
MESSAGE_NO_ROW = "the row folder is missing on one side"

NEUTRAL_FILES_ONLY_NOTE = "(a file only on the rerun side is a difference, not a fault)"
MODES_SENTENCE = "file modes and timestamps are not part of the digest"
DIFFERENCES_HEADER = "differences, listed and not judged"
LISTED_HEADER = "listed, not judged"
CONTENT_MARK = "  content: "

COMMITTED_TOKEN = "<repo>/<run>"
RUN_TOKEN = "<run>"

README_NAME = "README.md"
LOG_NAME = "wrapper-calls.log"
MEASUREMENTS_NAME = "measurements.txt"
TOOLS_NAME = "tools.txt"
SHA_NAME = "sha.txt"
SNAPSHOT_PREFIX = "snap-"
TRACES = (
    ("s1-work", "s1-work-full-trace.md"),
    ("s2-preclear", "s2-preclear-full-trace.md"),
    ("s3-resume", "s3-resume-full-trace.md"),
    ("s4-preclear-refresh", "s4-preclear-refresh-full-trace.md"),
)
BLOCK_FILES = ("digests.txt", "claude-version.txt", "usage.txt")

SIDES = (("old", "old side"), ("new", "rerun side"))

_ROW_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")
_TRACE_HEAD = re.compile(r"^### (\d+)\. (\w+) \(([^)]*)\)(.*)$")
_TRACE_FLAGS = re.compile(r"((?:  (?:ERROR|REFUSAL/DENIAL))+)\s*\Z")
_CALLS_HEADER = re.compile(r"^Calls (\d+); results flagged as [^:]*: (\d+)\.")
_TOTAL_LINE = re.compile(r"^total (\d+)(?:/\d+)? bytes(?: \(cap \d+\))?, sha256 [0-9a-f]{64}")
_SECTION_LINE = re.compile(r"^- (.+?): (\d+)(?:/\d+)?(?: over by \d+)?\Z")
_SHA_LINE = re.compile(r"^\\?([0-9a-f]{64})  (.+)\Z")

_SECTION_CAPS = dict(pc_measure.SECTIONS)


class CompareError(Exception):
    """A tree could not be read; the message is fixed text."""


def _printable(text):
    """ASCII-only text: anything else is shown as an escape, so no stream can fail on it."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _sorted_text(items):
    return sorted(items, key=lambda item: item.encode("ascii", "backslashreplace"))


def _entry_name(raw):
    """A manifest path (raw bytes) as one printable line: newline and carriage return are escaped."""
    escaped, _changed = pc_manifest.escape_name(raw)
    return _printable(escaped)


def normalise(text):
    """Read the committed token <repo>/<run> as the newer token <run>."""
    return text.replace(COMMITTED_TOKEN, RUN_TOKEN)


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


# ---------------------------------------------------------------------------------------------
# Reading one file of one side (read-only, tolerant)
# ---------------------------------------------------------------------------------------------


def _read_side(folder, name):
    """Return (state, text). state is ok, absent or unreadable; text is normalised and ASCII-safe."""
    path = os.path.join(folder, *name.split("/"))
    if os.path.islink(path):
        return "unreadable", ""
    if not os.path.exists(path):
        return "absent", ""
    if not os.path.isfile(path):
        return "unreadable", ""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return "unreadable", ""
    return "ok", normalise(data.decode("utf-8", "replace"))


# ---------------------------------------------------------------------------------------------
# README headings
# ---------------------------------------------------------------------------------------------


def _headings(text):
    return [_printable(line.rstrip()) for line in text.splitlines() if line.startswith("#")]


def _compare_headings(old_folder, new_folder):
    sides = {}
    items = {}
    for key, folder in (("old", old_folder), ("new", new_folder)):
        state, text = _read_side(folder, README_NAME)
        found = _headings(text) if state == "ok" else []
        sides[key] = {"state": state, "count": len(found)}
        items[key] = found
    old_set = set(items["old"])
    new_set = set(items["new"])
    result = dict(sides)
    result["only_old"] = [item for item in dict.fromkeys(items["old"]) if item not in new_set]
    result["only_new"] = [item for item in dict.fromkeys(items["new"]) if item not in old_set]
    return result


# ---------------------------------------------------------------------------------------------
# Helper calls
# ---------------------------------------------------------------------------------------------


def _helper_counts(folder):
    state, text = _read_side(folder, LOG_NAME)
    if state != "ok":
        return {"state": state}
    try:
        calls = pc_mine.parse_log(text)
    except pc_mine.MineError:
        return {"state": "unreadable"}
    verbs = {}
    for call in calls:
        verb = _printable(call["argv"][0]) if call["argv"] else "(none)"
        verbs[verb] = verbs.get(verb, 0) + 1
    return {"state": "ok", "total": len(calls), "verbs": verbs, "exits": sorted(call["exit"] for call in calls)}


# ---------------------------------------------------------------------------------------------
# Tool calls
# ---------------------------------------------------------------------------------------------


def count_trace_calls(text):
    """Count the calls of one full trace from its headings and its Calls header (text is already read)."""
    by_tool = {}
    errors = 0
    refusals = 0
    calls = 0
    header_calls = None
    header_flagged = None
    for line in text.splitlines():
        header = _CALLS_HEADER.match(line)
        if header is not None and header_calls is None:
            header_calls = int(header.group(1))
            header_flagged = int(header.group(2))
            continue
        head = _TRACE_HEAD.match(line)
        if head is None:
            continue
        calls += 1
        name = _printable(head.group(2))
        by_tool[name] = by_tool.get(name, 0) + 1
        flags = _TRACE_FLAGS.search(head.group(4))
        if flags is not None:
            if "ERROR" in flags.group(1):
                errors += 1
            if "REFUSAL/DENIAL" in flags.group(1):
                refusals += 1
    if calls == 0 and header_calls is None and text.strip() != "":
        return {"state": "unreadable"}
    return {
        "state": "ok",
        "calls": calls,
        "header_calls": header_calls,
        "header_flagged": header_flagged,
        "error": errors,
        "refusal": refusals,
        "by_tool": by_tool,
    }


def _trace_counts(folder, name):
    state, text = _read_side(folder, name)
    if state != "ok":
        return {"state": state}
    return count_trace_calls(text)


# ---------------------------------------------------------------------------------------------
# Byte measurements
# ---------------------------------------------------------------------------------------------


def parse_measurements(text):
    """Read measurements.txt in either shape. Returns a list of reports (a report per total line).

    Old shape: "total N bytes (cap C), sha256 H" and "- Section: N". New shape: "total N/C bytes, sha256 H" with an
    optional over-by suffix and "- Section: N/cap". The caps compared are the measurer's constants, by section name,
    and strictly greater than the cap means above it.
    """
    reports = []
    current = None
    for line in normalise(text).splitlines():
        total = _TOTAL_LINE.match(line)
        if total is not None:
            current = {"total": int(total.group(1)), "sections": [], "above": []}
            reports.append(current)
            continue
        section = _SECTION_LINE.match(line)
        if section is not None and current is not None:
            name = _printable(section.group(1))
            current["sections"].append((name, int(section.group(2)), _SECTION_CAPS.get(name)))
    for report in reports:
        if report["total"] > pc_measure.FILE_CAP:
            report["above"].append(("total", report["total"], pc_measure.FILE_CAP))
        for name, size, cap in report["sections"]:
            if cap is not None and size > cap:
                report["above"].append((name, size, cap))
    return reports


def _measurements(folder):
    state, text = _read_side(folder, MEASUREMENTS_NAME)
    if state != "ok":
        return {"state": state, "reports": []}
    reports = parse_measurements(text)
    return {"state": "ok" if reports else "none", "reports": reports}


# ---------------------------------------------------------------------------------------------
# Listed, not judged
# ---------------------------------------------------------------------------------------------


def _normalise_sha_path(path):
    """A leading helper-state folder reads as ckpt, and a leading ledgers folder as ckpt/ledgers."""
    if path.startswith("helper-state/"):
        return "ckpt/" + path[len("helper-state/"):]
    if path.startswith("ledgers/"):
        return "ckpt/" + path
    return path


def _sha_map(folder, snapshot):
    """Return (state, {normalised path: digest})."""
    state, text = _read_side(folder, snapshot + "/" + SHA_NAME)
    if state != "ok":
        return state, {}
    found = {}
    for line in text.splitlines():
        match = _SHA_LINE.match(line)
        if match is not None:
            found[_normalise_sha_path(_printable(match.group(2)))] = match.group(1)
    if not found and text.strip() != "":
        return "unreadable", {}
    return "ok", found


def _snapshot_names(folders):
    names = set()
    for folder in folders:
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    if entry.name.startswith(SNAPSHOT_PREFIX) and entry.is_dir(follow_symlinks=False):
                        names.add(_printable(entry.name))
        except OSError:
            continue
    return _sorted_text(names)


def _compare_snapshots(old_folder, new_folder):
    result = {}
    for name in _snapshot_names((old_folder, new_folder)):
        old_state, old_map = _sha_map(old_folder, name)
        new_state, new_map = _sha_map(new_folder, name)
        both = set(old_map) & set(new_map)
        result[name] = {
            "old_state": old_state,
            "new_state": new_state,
            "old_paths": len(old_map),
            "new_paths": len(new_map),
            "differ": _sorted_text(path for path in both if old_map[path] != new_map[path]),
            "same": sum(1 for path in both if old_map[path] == new_map[path]),
            "only_old": _sorted_text(set(old_map) - set(new_map)),
            "only_new": _sorted_text(set(new_map) - set(old_map)),
        }
    return result


def _rules(folder):
    path = os.path.join(folder, TOOLS_NAME)
    if os.path.islink(path):
        return {"state": "unreadable", "rules": []}
    if not os.path.isfile(path):
        return {"state": "absent", "rules": []}
    try:
        found = pc_allowlist.row_rules(folder)
    except (OSError, UnicodeDecodeError):
        return {"state": "unreadable", "rules": []}
    if found is None:
        return {"state": "absent", "rules": []}
    return {"state": "ok", "rules": [_printable(normalise(rule)) for rule in found]}


def _compare_rules(old_folder, new_folder):
    old = _rules(old_folder)
    new = _rules(new_folder)
    return {
        "old": {"state": old["state"], "count": len(old["rules"])},
        "new": {"state": new["state"], "count": len(new["rules"])},
        "only_old": _sorted_text(set(old["rules"]) - set(new["rules"])),
        "only_new": _sorted_text(set(new["rules"]) - set(old["rules"])),
    }


def _block(folder, name):
    state, text = _read_side(folder, name)
    if state != "ok":
        return {"state": state, "lines": []}
    return {"state": "ok", "lines": [_printable(line) for line in text.splitlines()]}


# ---------------------------------------------------------------------------------------------
# The comparison and its report
# ---------------------------------------------------------------------------------------------


def compare_rows(old_tree, new_tree, row, old_row=None):
    """Read both row folders and return the structured differences (a dict). Only reads.

    row names the folder in the new tree; old_row names the folder in the old tree when it differs (the all-rows mapping).
    """
    old_folder = _row_folder(old_tree, row if old_row is None else old_row)
    new_folder = _row_folder(new_tree, row)
    old_labels = _entry_labels(old_folder)
    new_labels = _entry_labels(new_folder)
    return {
        "row": row,
        "old_name": _printable(os.path.basename(old_tree.rstrip(os.sep))),
        "new_name": _printable(os.path.basename(new_tree.rstrip(os.sep))),
        "only_old": _sorted_text(old_labels - new_labels),
        "only_new": _sorted_text(new_labels - old_labels),
        "headings": _compare_headings(old_folder, new_folder),
        "helper": {"old": _helper_counts(old_folder), "new": _helper_counts(new_folder)},
        "tools": {
            label: {"old": _trace_counts(old_folder, name), "new": _trace_counts(new_folder, name)} for label, name in TRACES
        },
        "measurements": {"old": _measurements(old_folder), "new": _measurements(new_folder)},
        "snapshots": _compare_snapshots(old_folder, new_folder),
        "rules": _compare_rules(old_folder, new_folder),
        "blocks": {name: {"old": _block(old_folder, name), "new": _block(new_folder, name)} for name in BLOCK_FILES},
    }


def _plural(count, word):
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def _content(items):
    return [CONTENT_MARK + item for item in items]


def _heading_lines(result):
    headings = result["headings"]
    lines = ["row README headings"]
    for key, label in SIDES:
        side = headings[key]
        lines.append("%s, %s: %s" % (README_NAME, label, _plural(side["count"], "heading") if side["state"] == "ok" else side["state"]))
    lines.append("headings only on the old side: %d" % len(headings["only_old"]))
    lines.extend(_content(headings["only_old"]))
    lines.append("headings only on the rerun side: %d" % len(headings["only_new"]))
    lines.extend(_content(headings["only_new"]))
    return lines


def _helper_lines(result):
    lines = ["helper calls"]
    for key, label in SIDES:
        side = result["helper"][key]
        if side["state"] != "ok":
            lines.append("helper calls, %s: %s" % (label, side["state"]))
            continue
        verbs = ", ".join("%s %d" % (verb, side["verbs"][verb]) for verb in _sorted_text(side["verbs"])) or "none"
        exits = {}
        for code in side["exits"]:
            exits[code] = exits.get(code, 0) + 1
        exit_text = ", ".join("%d x%d" % (code, exits[code]) for code in sorted(exits)) or "none"
        lines.append("helper calls, %s: total %d, verbs: %s, exit codes: %s" % (label, side["total"], verbs, exit_text))
    return lines


def _tool_lines(result):
    lines = ["tool calls"]
    for label, _name in TRACES:
        for key, side_label in SIDES:
            side = result["tools"][label][key]
            prefix = "tool calls, %s, %s: " % (label, side_label)
            if side["state"] != "ok":
                lines.append(prefix + side["state"])
                continue
            header = "no Calls header" if side["header_calls"] is None else "Calls header %d, flagged %d" % (
                side["header_calls"],
                side["header_flagged"],
            )
            lines.append(
                prefix
                + "%s, %s, ERROR flags %d, REFUSAL/DENIAL flags %d"
                % (_plural(side["calls"], "call"), header, side["error"], side["refusal"])
            )
            for tool in _sorted_text(side["by_tool"]):
                lines.append("  %s %d" % (tool, side["by_tool"][tool]))
    return lines


def _measurement_lines(result):
    lines = ["byte measurements against the cap"]
    for key, label in SIDES:
        side = result["measurements"][key]
        if side["state"] != "ok":
            lines.append("measurements, %s: %s" % (label, side["state"]))
            continue
        lines.append("measurements, %s: %s" % (label, _plural(len(side["reports"]), "report")))
        above = []
        for index, report in enumerate(side["reports"], 1):
            lines.append("  report %d: total %d of cap %d" % (index, report["total"], pc_measure.FILE_CAP))
            for name, size, cap in report["sections"]:
                lines.append("    %s: %d" % (name, size) + (" of cap %d" % cap if cap is not None else ", no cap"))
            above.extend("%s %d (by %d)" % (name, size, size - cap) for name, size, cap in report["above"])
        lines.append("%s above the cap: %s" % (label, ", ".join(above) if above else "none"))
    return lines


def _snapshot_lines(result):
    lines = ["sha.txt per snapshot (a leading helper-state or ledgers folder is read as ckpt)"]
    for name, snap in result["snapshots"].items():
        lines.append("%s: old side %s, rerun side %s" % (name, snap["old_state"], snap["new_state"]))
        if snap["old_state"] != "ok" or snap["new_state"] != "ok":
            continue
        lines.append(
            "  paths: old side %d, rerun side %d, digest equal %d, digest differs %d, only on the old side %d, only on the rerun side %d"
            % (snap["old_paths"], snap["new_paths"], snap["same"], len(snap["differ"]), len(snap["only_old"]), len(snap["only_new"]))
        )
        lines.extend("  digest differs: " + path for path in snap["differ"])
        lines.extend("  only on the old side: " + path for path in snap["only_old"])
        lines.extend("  only on the rerun side: " + path for path in snap["only_new"])
    return lines


def _rule_lines(result):
    rules = result["rules"]
    lines = []
    for key, label in SIDES:
        side = rules[key]
        lines.append("%s rules, %s: %s" % (TOOLS_NAME, label, _plural(side["count"], "rule") if side["state"] == "ok" else side["state"]))
    lines.append("rules only on the old side: %d" % len(rules["only_old"]))
    lines.extend(_content(rules["only_old"]))
    lines.append("rules only on the rerun side: %d" % len(rules["only_new"]))
    lines.extend(_content(rules["only_new"]))
    return lines


def _block_lines(result):
    lines = []
    for name in BLOCK_FILES:
        for key, label in SIDES:
            side = result["blocks"][name][key]
            if side["state"] != "ok":
                lines.append("%s, %s: %s" % (name, label, side["state"]))
                continue
            lines.append("%s, %s: %s" % (name, label, _plural(len(side["lines"]), "line")))
            lines.extend(_content(side["lines"]))
    return lines


def report_lines(result):
    """The report lines for one comparison, under neutral headings and in a fixed order."""
    lines = [DIFFERENCES_HEADER]
    lines.append("files only on the old side: %d" % len(result["only_old"]))
    lines.extend("  " + name for name in result["only_old"])
    lines.append("files only on the rerun side: %d" % len(result["only_new"]))
    lines.extend("  " + name for name in result["only_new"])
    lines.append(NEUTRAL_FILES_ONLY_NOTE)
    lines.extend(_heading_lines(result))
    lines.extend(_helper_lines(result))
    lines.extend(_tool_lines(result))
    lines.extend(_measurement_lines(result))
    lines.append(LISTED_HEADER)
    lines.extend(_snapshot_lines(result))
    lines.extend(_rule_lines(result))
    lines.extend(_block_lines(result))
    return lines


# ---------------------------------------------------------------------------------------------
# All rows: the mapping of the new tree onto the reference tree (plan 04-18)
# ---------------------------------------------------------------------------------------------

STOPPED_PREFIX = "STOPPED-"
SKIPPED_PREFIX = "SKIPPED-"
RERUN_SUFFIX = "-rerun"
FIRST_PASS_SUFFIX = "-first-pass"
KIND_LAYOUT = "layout"
NO_STRUCTURAL_REFERENCE = "no structural reference"
_ATTEMPT_SUFFIX = re.compile(r"(.+)-attempt-([2-9])\Z")


class _Outcome(object):
    """One folder of the new tree that belongs to a registry id: its state, its attempt and its name."""

    def __init__(self, name, state, attempt):
        self.name = name
        self.state = state
        self.attempt = attempt


def _real_folder_names(tree):
    names = []
    for name in sorted(os.listdir(tree)):
        path = os.path.join(tree, name)
        if os.path.isdir(path) and not os.path.islink(path):
            names.append(name)
    return names


def _outcomes(new_tree, ids):
    """{registry id: [_Outcome, ...]} for every folder of the new tree whose name is an id, a STOPPED- or SKIPPED- label of one."""
    found = {}
    for name in _real_folder_names(new_tree):
        state = "filed"
        rest = name
        for prefix, label in ((STOPPED_PREFIX, "STOPPED"), (SKIPPED_PREFIX, "SKIPPED")):
            if name.startswith(prefix):
                state, rest = label, name[len(prefix):]
                break
        attempt = 1
        parsed = _ATTEMPT_SUFFIX.match(rest)
        if parsed is not None:
            rest, attempt = parsed.group(1), int(parsed.group(2))
        if rest in ids:
            found.setdefault(rest, []).append(_Outcome(name, state, attempt))
    return found


def map_rows(reference_tree, new_tree, registry):
    """Map the new tree onto the reference tree; reads folder names only.

    registry is a sequence of entries with row_id and kind (the layouts and the rows of pc_rows). Returns a dict:
      rows          one dict per compared row, in registry order: id, old (the reference folder: the -rerun folder when it
                    exists, else the bare folder), new (the highest filed attempt of the row) and attempt
      no_reference  ids of rows with a filed folder and no committed folder to compare it with
      stopped       names of STOPPED- folders, listed and never compared
      skipped       names of SKIPPED- folders, listed and never compared
      not_run       ids with no outcome folder at all, rows and layouts
      older         committed folders of a row id that are not the mapped one (the bare folder beside a -rerun folder, the
                    -first-pass folders), listed and never compared
      layouts       (id, states present in the new tree) for each layout; a layout has no structural reference
    """
    ids = dict((entry.row_id, entry.kind) for entry in registry)
    reference_names = set(_real_folder_names(reference_tree))
    outcomes = _outcomes(new_tree, ids)
    result = {"rows": [], "no_reference": [], "stopped": [], "skipped": [], "not_run": [], "older": [], "layouts": []}
    for entry in registry:
        found = outcomes.get(entry.row_id, [])
        if not found:
            result["not_run"].append(entry.row_id)
        if entry.kind == KIND_LAYOUT:
            states = sorted(set(item.state for item in found)) or ["not run"]
            result["layouts"].append((entry.row_id, states))
            continue
        for item in found:
            if item.state == "STOPPED":
                result["stopped"].append(item.name)
            elif item.state == "SKIPPED":
                result["skipped"].append(item.name)
        mapped = None
        for candidate in (entry.row_id + RERUN_SUFFIX, entry.row_id):
            if candidate in reference_names:
                mapped = candidate
                break
        for candidate in (entry.row_id, entry.row_id + FIRST_PASS_SUFFIX):
            if candidate in reference_names and candidate != mapped:
                result["older"].append(candidate)
        filed = [item for item in found if item.state == "filed"]
        if not filed:
            continue
        best = max(filed, key=lambda item: item.attempt)
        if mapped is None:
            result["no_reference"].append(entry.row_id)
        else:
            result["rows"].append({"id": entry.row_id, "old": mapped, "new": best.name, "attempt": best.attempt})
    return result


def default_reference_path():
    """DEFAULT_REFERENCE resolved against the repository root of this script."""
    return os.path.join(_REPO_ROOT, *DEFAULT_REFERENCE.split("/"))


def _list_lines(title, items):
    lines = ["%s: %d" % (title, len(items))]
    lines.extend("  " + _printable(item) for item in items)
    return lines


def all_rows_lines(old_tree, new_tree, registry):
    """The whole all-rows report as text lines, with both tree digests before and after. Only reads.

    Raises CompareError, OSError or pc_manifest.ManifestError when a tree cannot be read.
    """
    before = (tree_digest(old_tree), tree_digest(new_tree))
    mapping = map_rows(old_tree, new_tree, registry)
    lines = [
        "compare all rows: old %s, new %s"
        % (_printable(os.path.basename(old_tree.rstrip(os.sep))), _printable(os.path.basename(new_tree.rstrip(os.sep)))),
        "tree digest before: old %s, new %s" % before,
        "rows compared: %d" % len(mapping["rows"]),
    ]
    for item in mapping["rows"]:
        result = compare_rows(old_tree, new_tree, item["new"], item["old"])
        lines.append("")
        lines.append(
            "compare row %s: old folder %s, new folder %s, attempt %d"
            % (_printable(item["id"]), _printable(item["old"]), _printable(item["new"]), item["attempt"])
        )
        lines.extend(report_lines(result))
    lines.append("")
    # Committed folder names, listed as content: a name such as the first-pass folders is committed text, not the comparer's word.
    lines.append("older attempts not compared: %d" % len(mapping["older"]))
    lines.extend(_content(_printable(name) for name in mapping["older"]))
    lines.extend(_list_lines("stopped, not compared", mapping["stopped"]))
    lines.extend(_list_lines("skipped, not compared", mapping["skipped"]))
    lines.extend(_list_lines("filed with no committed folder to compare", mapping["no_reference"]))
    lines.extend(_list_lines("not run", mapping["not_run"]))
    lines.append("layouts: %d" % len(mapping["layouts"]))
    for identifier, states in mapping["layouts"]:
        lines.append("  layout %s: %s (new tree: %s)" % (_printable(identifier), NO_STRUCTURAL_REFERENCE, ", ".join(states)))
    after = (tree_digest(old_tree), tree_digest(new_tree))
    lines.append("tree digest after: old %s, new %s" % after)
    lines.append("old unchanged: %s" % ("yes" if before[0] == after[0] else "no"))
    lines.append("new unchanged: %s" % ("yes" if before[1] == after[1] else "no"))
    lines.append(MODES_SENTENCE)
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


def _main_all_rows(args, out, err):
    """--all-rows --new DIR [--old DIR]; --row with it is refused with the usage text."""
    if args.row is not None or args.new is None:
        err.write(USAGE_LINE + "\n")
        err.write("%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        return pc_exitcodes.USAGE
    old_tree = args.old if args.old is not None else default_reference_path()
    new_tree = args.new
    if not (_is_real_folder(old_tree) and _is_real_folder(new_tree)):
        return _refuse(err, MESSAGE_UNREADABLE)
    try:
        import pc_rows

        lines = all_rows_lines(old_tree, new_tree, pc_rows.build_registry())
    except (OSError, pc_manifest.ManifestError, CompareError):
        return _refuse(err, MESSAGE_UNREADABLE)
    out.write("\n".join(lines) + "\n")
    out.flush()
    return pc_exitcodes.OK


def main(argv, out=None, err=None):
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = _Parser(err)
    parser.add_argument("--old", default=None)
    parser.add_argument("--new", default=None)
    parser.add_argument("--row", default=None)
    parser.add_argument("--all-rows", action="store_true", dest="all_rows")
    try:
        args = parser.parse_args(list(argv))
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else pc_exitcodes.USAGE
    if args.all_rows:
        return _main_all_rows(args, out, err)
    row = DEFAULT_ROW if args.row is None else args.row
    if args.old is None or args.new is None or not _ROW_ID.match(row):
        err.write(USAGE_LINE + "\n")
        err.write("%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        return pc_exitcodes.USAGE
    old_tree, new_tree = args.old, args.new
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
