"""Closing a dated evidence folder: its README, a digest table and a usage table (plan 04-03; RERUN-03; D-03).

Five subcommands, all model-free (plans 04-03, 04-07 and 04-18):

  close        files README.md (only when the folder has none), digest-table.md and usage-by-row.txt for part 1, or
               digest-table-part-N.md and usage-by-row-part-N.txt for the first free N from 2 when the part-1 files
               exist, so it can run again after a retry without editing anything earlier. Each part lists every row
               folder present at the moment it is written; the latest part is the complete one. The files are staged
               in a run root, go through the sanitizer, and are added to the folder through pc_promote.promote_into (the leak gate
               first, flat exclusive creation, never an overwrite).
  report       prints the same two tables to standard output and writes nothing.
  check-words  scans the harness-authored files of the folder for the vocabulary the harness never writes (EVID-05);
               prints counts only; exit 0 when it finds none and 1 otherwise.
  finalize     files the baseline form of a dated folder in one step: README.md (the baseline label, the row counts, the
               Run state lines and, when --clone-facts names a clone-facts file, its facts), digest-table.md,
               usage-by-row.txt, the comparison against the reference tree, review-brief.md and, with clone facts,
               environment-names.txt. Every file goes through the staging, sanitizer, leak gate and promote_into of
               close; an existing name is refused with exit 17 and nothing is filed (plan 04-18; RERUN-03, D-16).
  row7-review  builds the side-by-side Do-not-redo review of the row 7 attempts of the folder from the filed candidate
               files and stop files only (never a run root) and adds it as row7-review.md, or as the first free
               row7-review-part-N.md, through the same staging, sanitizer, leak gate and promote_into as close. It lists
               candidates and counts and decides nothing (plan 04-07; D-06, D-07). A folder with no row 7 attempt is
               refused with exit 2.

The tables read only filed files, never a run root: digests.txt, usage.txt, stop.txt and the reason line of a SKIPPED
README, each through a strict pattern. A value that does not match (not 64 lowercase hex digits for a digest, not a
plain decimal for a cost) is printed UNCONFIRMED and never guessed; model traces are never parsed. Costs are quoted as
text exactly as usage.txt holds them and summed with exact Decimal arithmetic; a stopped row's partial cost is counted.

The folder argument is a repo-relative or absolute path whose real path lies inside tests/evidence and names a dated
folder (rerun-...). close refuses the two frozen folders. Nothing here deletes, renames, moves or truncates a file.
Messages hold counts, ids and fixed words only, never a path.

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import argparse
import datetime
import decimal
import json
import os
import re
import stat
import sys
from decimal import Decimal
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, TextIO, Tuple

import pc_compare
import pc_evidence
import pc_exitcodes
import pc_leakgate
import pc_promote
import pc_review
import pc_rows
import pc_runroot
import pc_sanitize
import pc_spike

PROG = "pc_baseline.py"
USAGE_LINE = (
    "usage: pc_baseline.py {close|report|check-words|row7-review|finalize} --folder FOLDER [--baseline] [--clone-facts FILE]"
)
MESSAGE_USAGE = "see the usage line"
MESSAGE_FOLDER = "REFUSED: the folder is not a dated folder of the evidence tree this step may read"
MESSAGE_FROZEN = "REFUSED: a frozen evidence folder is never closed"
MESSAGE_NO_ROW7 = "REFUSED: the folder holds no row 7 attempt; nothing was filed"
MESSAGE_BLOCKED = "BLOCKED: the harness home or the runs root is not usable; nothing was filed"
MESSAGE_COLLISION = "RUNROOT_COLLISION: a run folder already exists; nothing was filed"
MESSAGE_STAGING = "ERROR: the files could not be staged; nothing was filed"
MESSAGE_SANITIZER = "SCANNER_ERROR: the sanitizer could not process a staged file; nothing was filed"
MESSAGE_FACTS = "REFUSED: the clone-facts file does not match its schema; nothing was filed"
MESSAGE_EXISTS = "REFUSED: a top-level file this step files already exists in the folder; nothing was filed"
MESSAGE_REFERENCE = "REFUSED: the reference tree could not be read; nothing was filed"

DATED_PREFIX = "rerun-"
# Never the target of finalize, close, record_verdict or evidence_readme: the publication folder, the first baseline, the
# older layout folders and every committed rerun folder of the campaign (all read only; plan 04-18).
FROZEN_FOLDERS = frozenset(
    [
        "publication-2026-10-20",
        "rerun-2026-10-29-claude-sonnet-5-5",
        "plain-memory-2026-10-19",
        "hub-memory-2026-10-19",
        "hub-memory-2026-10-19-rerun",
        "bound-ledger-2026-10-19",
        "bound-ledger-2026-10-19-rerun",
        "rerun-2026-11-03-claude-sonnet-5-5-wave-a",
        "rerun-2026-11-05-claude-sonnet-5-5-wave-b",
        "rerun-2026-11-06-claude-sonnet-5-5-wave-c",
        "rerun-2026-11-07-claude-sonnet-5-5-wave-d",
        "rerun-2026-11-09-claude-sonnet-5-5-triple",
    ]
)
EVIDENCE_PARTS = ("tests", "evidence")
UNCONFIRMED = pc_evidence.UNCONFIRMED
STATE_FILED = "filed"
STATE_STOPPED = "STOPPED"
STATE_SKIPPED = "SKIPPED"
STATE_OTHER = "unrecognised"
NO_REASON = "-"
MAX_FILE_BYTES = 1024 * 1024
MAX_REASON = 200
PRECISION = 60

README_FILE = "README.md"
DIGEST_FILE = "digest-table.md"
USAGE_FILE = "usage-by-row.txt"
REVIEW_FILE = pc_review.REVIEW_FILE
COMPARISON_FILE = "comparison-vs-publication-2026-10-20.txt"
BRIEF_FILE = "review-brief.md"
ENV_NAMES_FILE = "environment-names.txt"
FINALIZE_FILES = (README_FILE, DIGEST_FILE, USAGE_FILE, COMPARISON_FILE, BRIEF_FILE, ENV_NAMES_FILE)
# The closing line of a row README is the reviewer line: this prefix, then PENDING, or later the reviewer's own text.
VERDICT_PREFIX = pc_evidence.VERDICT_LINE[: -len("PENDING")]

# The clone-facts file written by the clean-clone bootstrap (plan 04-19) and read strictly here (plan 04-18; D-10, D-11).
CLONE_FACTS_COUNT_KEYS = ("path_checkpoint_binaries", "helper_files_in_clone", "helper_calls", "helper_calls_stub", "helper_calls_other")
CLONE_FACTS_KEYS = ("env_names",) + CLONE_FACTS_COUNT_KEYS + ("clone_head", "source_kind", "home_kind")
MAX_ENV_NAMES = 40
MAX_FACTS_BYTES = 65536
MAX_COUNT = 10 ** 9
SOURCE_KINDS = ("url", "local")
HOME_KINDS = ("throwaway", "real")

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_PLAIN_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")
_ROW_NAME = re.compile(r"(?P<id>.+?)(?:-attempt-(?P<n>[1-9]))?\Z")
_DIGEST_LINE = re.compile(r"(?P<sha>[0-9a-f]{64}|UNCONFIRMED)  (?P<name>[^\n]+)\Z")
_STAGE_LINE = re.compile(
    r"stage (?P<name>s[0-9]): session [^ ,]+, subtype (?P<subtype>[^ ,]+), turns (?P<turns>[^ ,]+), "
    r"input [^ ,]+, cache creation [^ ,]+, cache read [^ ,]+, output [^ ,]+, "
    r"cost (?P<cost>[^ ,]+), cumulative (?P<cumulative>[^ ,]+), wall [^ ,]+ seconds\Z"
)
_SUBTYPE = re.compile(r"[A-Za-z0-9_]{1,64}\Z")
_STOP_STAGE = re.compile(r"s[0-9]\Z")
_REASON_TEXT = re.compile(r"[A-Za-z0-9 ,;:()_./'=-]{1,%d}\Z" % MAX_REASON)
_MODEL_LINE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]{0,63})\Z")
_SAFE_NAME = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")
_BUILD_TEXT = re.compile(r"([0-9]+\.[0-9]+\.[0-9]+) \(Claude Code\)\Z")
_SKIP_HEAD = "This row was skipped on this machine: "
_SKIP_TAIL = ". No session was run"
_PART_DIGEST = re.compile(r"digest-table-part-[0-9]+\.md\Z")
_ENV_NAME = re.compile(r"[A-Z0-9_]{1,64}\Z")
_HEAD = re.compile(r"[0-9a-f]{40}\Z")
_TRIPLE_FOLDER = re.compile(r"rerun-[A-Za-z0-9._-]*-triple\Z")
_QUOTE_CAP = 600


class Item(NamedTuple):
    """One row folder, STOPPED label or SKIPPED label as the filed files describe it."""

    folder: str
    state: str
    row_id: Optional[str]
    attempt: int
    reason: str
    skill: str
    adapter: str
    stub: str
    wrapper: str
    cost: str
    total_label: str
    stages: Tuple[str, ...]


# ---------------------------------------------------------------------------------------------
# Reading filed files
# ---------------------------------------------------------------------------------------------


def _read_text(path: str) -> Optional[str]:
    """The text of one regular, non-symlink file of at most MAX_FILE_BYTES, or None."""
    try:
        mode = os.lstat(path).st_mode
        if not stat.S_ISREG(mode):
            return None
        with open(path, "rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            return None
        return data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _plain_decimal(text: str) -> Optional[Decimal]:
    if len(text) > 64 or _PLAIN_DECIMAL.match(text) is None:
        return None
    return Decimal(text)


def _cost_or_unconfirmed(text: str) -> str:
    return text if _plain_decimal(text) is not None else UNCONFIRMED


def _digest_values(text: Optional[str]) -> Dict[str, str]:
    """The four digests digests.txt holds, each a 64-hex value or UNCONFIRMED (missing, repeated or malformed)."""
    found: Dict[str, List[str]] = {"skill": [], "adapter": [], "stub": [], "wrapper": []}
    for line in (text or "").splitlines():
        parsed = _DIGEST_LINE.match(line)
        if parsed is None:
            continue
        name = parsed.group("name")
        sha = parsed.group("sha")
        if name.endswith("/skills/preclear/SKILL.md"):
            found["skill"].append(sha)
        elif name.endswith("/skills/preclear/references/checkpoint-v1.md"):
            found["adapter"].append(sha)
        elif name == "tests/harness/checkpoint_stub.py":
            found["stub"].append(sha)
        elif name.endswith("/wrapper/checkpoint"):
            found["wrapper"].append(sha)
    values: Dict[str, str] = {}
    for key, shas in found.items():
        values[key] = shas[0] if len(shas) == 1 and _HEX64.match(shas[0]) else UNCONFIRMED
    return values


def _usage_facts(text: Optional[str], label: str) -> Tuple[str, Tuple[str, ...]]:
    """(the cost text after the `label:` line, the stage lines) of a usage.txt; UNCONFIRMED when not one plain decimal."""
    cost_lines = [line[len(label) + 2:] for line in (text or "").splitlines() if line.startswith(label + ": ")]
    cost = _cost_or_unconfirmed(cost_lines[0]) if len(cost_lines) == 1 else UNCONFIRMED
    stages: List[str] = []
    for line in (text or "").splitlines():
        parsed = _STAGE_LINE.match(line)
        if parsed is None:
            continue
        subtype = parsed.group("subtype") if _SUBTYPE.match(parsed.group("subtype")) else UNCONFIRMED
        turns = parsed.group("turns") if parsed.group("turns").isdigit() else UNCONFIRMED
        stages.append(
            "stage %s: subtype %s, turns %s, cost %s, cumulative %s"
            % (
                parsed.group("name"),
                subtype,
                turns,
                _cost_or_unconfirmed(parsed.group("cost")),
                _cost_or_unconfirmed(parsed.group("cumulative")),
            )
        )
    return cost, tuple(stages)


def _stop_reason_line(text: Optional[str]) -> str:
    """`turns at s2` from stop.txt, UNCONFIRMED when the reason or the stage is not a known word."""
    reason = stage = None
    for line in (text or "").splitlines():
        if line.startswith("reason: ") and reason is None:
            reason = line[len("reason: "):]
        elif line.startswith("stage: ") and stage is None:
            stage = line[len("stage: "):]
    if reason not in pc_evidence.STOP_REASONS or stage is None or _STOP_STAGE.match(stage) is None:
        return UNCONFIRMED
    return "%s at %s" % (reason, stage)


def _skip_reason_line(text: Optional[str]) -> str:
    """The reason of a SKIPPED README, UNCONFIRMED unless it is one short plain sentence."""
    for line in (text or "").splitlines():
        if line.startswith(_SKIP_HEAD):
            rest = line[len(_SKIP_HEAD):]
            reason = rest.split(_SKIP_TAIL, 1)[0] if _SKIP_TAIL in rest else UNCONFIRMED
            return reason if _REASON_TEXT.match(reason) else UNCONFIRMED
    return UNCONFIRMED


def _registry_index() -> Dict[str, int]:
    return dict((entry.row_id, number) for number, entry in enumerate(pc_rows.build_registry()))


def _classify(name: str, index: Mapping[str, int]) -> Tuple[str, Optional[str], int]:
    """(state, row id, attempt) of a folder name; the row id is None when the registry does not know it."""
    state = STATE_FILED
    rest = name
    for prefix, label in ((pc_evidence.STOPPED_PREFIX, STATE_STOPPED), (pc_evidence.SKIPPED_PREFIX, STATE_SKIPPED)):
        if name.startswith(prefix):
            state, rest = label, name[len(prefix):]
            break
    parsed = _ROW_NAME.match(rest)
    row_id = parsed.group("id") if parsed is not None else None
    attempt = int(parsed.group("n")) if parsed is not None and parsed.group("n") else 1
    if parsed is not None and parsed.group("n") == "1":
        row_id = None
    if row_id is None or row_id not in index:
        return STATE_OTHER, None, 1
    return state, row_id, attempt


def _display(name: str) -> str:
    """A folder name safe to print in a table cell: plain name characters only, others shown as a question mark."""
    return name if _SAFE_NAME.match(name) else re.sub(r"[^A-Za-z0-9._-]", "?", name)[:128] or "?"


def read_items(folder: str) -> List[Item]:
    """Every row folder, STOPPED label and SKIPPED label of a dated folder, in table order.

    The order is the registry order (layouts first, then rows), then the attempt number, with a STOPPED or SKIPPED
    label directly after the row folder of its attempt; a folder the registry does not name comes last, by name.
    A symlink or a plain file in the dated folder is not a row folder and is not listed.
    """
    index = _registry_index()
    items: List[Tuple[Tuple[int, int, int, str], Item]] = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        try:
            mode = os.lstat(path).st_mode
        except OSError:
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            continue
        state, row_id, attempt = _classify(name, index)
        digests = _digest_values(_read_text(os.path.join(path, "digests.txt")))
        unknown = dict(skill=UNCONFIRMED, adapter=UNCONFIRMED, stub=UNCONFIRMED, wrapper=UNCONFIRMED)
        reason = NO_REASON
        cost = UNCONFIRMED
        label = "row total"
        stages: Tuple[str, ...] = ()
        if state == STATE_FILED:
            cost, stages = _usage_facts(_read_text(os.path.join(path, "usage.txt")), "row total")
            rank = 0
        elif state == STATE_STOPPED:
            reason = _stop_reason_line(_read_text(os.path.join(path, pc_evidence.STOP_FILE)))
            cost, stages = _usage_facts(_read_text(os.path.join(path, "usage.txt")), "partial total")
            label = "partial total"
            rank = 1
        elif state == STATE_SKIPPED:
            reason = _skip_reason_line(_read_text(os.path.join(path, README_FILE)))
            cost = "0"
            label = "no session"
            rank = 2
        else:
            reason = UNCONFIRMED
            rank = 3
        if state != STATE_FILED and state != STATE_STOPPED:
            digests = unknown
        key = (index.get(row_id, len(index)) if row_id else len(index), attempt, rank, name)
        items.append(
            (
                key,
                Item(
                    _display(name), state, row_id, attempt, reason, digests["skill"], digests["adapter"], digests["stub"],
                    digests["wrapper"], cost, label, stages,
                ),
            )
        )
    items.sort(key=lambda pair: pair[0])
    return [item for _key, item in items]


def _sum(costs: Sequence[str]) -> Decimal:
    context = decimal.Context(prec=PRECISION)
    total = Decimal("0")
    for text in costs:
        total = context.add(total, Decimal(text))
    return total


def _totals(items: Sequence[Item]) -> Tuple[Decimal, int, int]:
    """(the Decimal sum of every cost value, the number of values, the number of UNCONFIRMED costs)."""
    values = [item.cost for item in items if _plain_decimal(item.cost) is not None]
    unknown = sum(1 for item in items if _plain_decimal(item.cost) is None)
    return _sum(values), len(values), unknown


def _total_line(items: Sequence[Item]) -> str:
    total, count, unknown = _totals(items)
    return "total: %s USD from %d cost value(s); %d UNCONFIRMED" % (format(total, "f"), count, unknown)


# ---------------------------------------------------------------------------------------------
# Part names and the rendered files
# ---------------------------------------------------------------------------------------------


def part_names(folder: str) -> Tuple[int, str, str]:
    """(part number, digest table name, usage table name) of the next close: part 1 when digest-table.md is absent."""
    if not os.path.lexists(os.path.join(folder, DIGEST_FILE)) and not os.path.lexists(os.path.join(folder, USAGE_FILE)):
        return 1, DIGEST_FILE, USAGE_FILE
    number = 2
    while True:
        digest = "digest-table-part-%d.md" % number
        usage = "usage-by-row-part-%d.txt" % number
        if not os.path.lexists(os.path.join(folder, digest)) and not os.path.lexists(os.path.join(folder, usage)):
            return number, digest, usage
        number += 1


def _lines(items: Sequence[str]) -> str:
    return "\n".join(items) + "\n"


def render_digest_table(items: Sequence[Item], part: int) -> str:
    """The digest table: state, attempt, reason, the four digests and the cost text of every folder, then a total."""
    lines = [
        "# Digest table, part %d" % part,
        "",
        "This part lists every row folder present in this dated folder at the moment it was written. The latest part "
        "is the complete one; earlier parts are never edited. Costs are quoted as the usage files hold them.",
        "",
        "rows: %d" % len(items),
        "",
        "| Folder | State | Attempt | Reason | Skill sha256 | Adapter sha256 | Stub sha256 | Wrapper sha256 | Cost (USD) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| %s | %s | %d | %s | %s | %s | %s | %s | %s |"
            % (item.folder, item.state, item.attempt, item.reason, item.skill, item.adapter, item.stub, item.wrapper, item.cost)
        )
    lines.extend(["", _total_line(items)])
    return _lines(lines)


def render_usage_by_row(items: Sequence[Item], part: int) -> str:
    """The usage table: per folder the per-stage cost lines and the total line, as the usage files hold them."""
    lines = [
        "usage by row, part %d" % part,
        "every row folder present at the moment this part was written is listed; costs are in US dollars, kept as text",
        "rows: %d" % len(items),
    ]
    for item in items:
        lines.append("")
        lines.append("%s (%s, attempt %d)" % (item.folder, item.state, item.attempt))
        if item.state == STATE_SKIPPED:
            lines.append("  no session was run; cost 0")
            continue
        if item.state == STATE_OTHER:
            lines.append("  cost UNCONFIRMED")
            continue
        for stage in item.stages:
            lines.append("  " + stage)
        lines.append("  %s: %s" % (item.total_label, item.cost))
    lines.extend(["", _total_line(items)])
    return _lines(lines)


def _recorded(folder: str, items: Sequence[Item], name: str, pattern: "re.Pattern[str]") -> str:
    """The one value the first line of `name` holds in every filed row, UNCONFIRMED when absent, odd or not agreed."""
    seen = set()
    for item in items:
        if item.state != STATE_FILED:
            continue
        text = _read_text(os.path.join(folder, item.folder, name))
        line = text.splitlines()[0] if text else ""
        parsed = pattern.match(line)
        seen.add(parsed.group(1) if parsed is not None else UNCONFIRMED)
    return seen.pop() if len(seen) == 1 else UNCONFIRMED


def render_folder_readme(folder: str, items: Sequence[Item], baseline: bool) -> str:
    """The folder README: a campaign attribution run, or with baseline a new baseline; never a replication."""
    name = os.path.basename(folder.rstrip(os.sep))
    model = _recorded(folder, items, "model-id.txt", _MODEL_LINE)
    build = _recorded(folder, items, "claude-version.txt", _BUILD_TEXT)
    counts = dict((state, sum(1 for item in items if item.state == state)) for state in
                  (STATE_FILED, STATE_STOPPED, STATE_SKIPPED, STATE_OTHER))
    lines = ["# %s" % name, ""]
    if baseline:
        lines.append(
            "This folder is a new baseline on the pinned model and Claude Code build (model %s, Claude Code %s). It "
            "is not a replication of the 2026-10-20 run: that run recorded no model, so the model cannot be matched."
            % (model, build)
        )
    else:
        lines.append(
            "This folder is a campaign attribution run on the pinned model and Claude Code build (model %s, Claude "
            "Code %s). It is not a baseline and has not been reviewed." % (model, build)
        )
    lines.extend(
        [
            "",
            "Row folders present when this file was written: %d (%d filed, %d STOPPED, %d SKIPPED, %d unrecognised)."
            % (len(items), counts[STATE_FILED], counts[STATE_STOPPED], counts[STATE_SKIPPED], counts[STATE_OTHER]),
            "",
            "`digest-table.md` and `usage-by-row.txt` list them with their digests and costs; a later close adds "
            "part files and never edits an earlier one. A STOPPED or SKIPPED folder is a label for a run that did "
            "not finish or did not start, not a result.",
            "",
            "The committed folder `tests/evidence/publication-2026-10-20` stays the reference. Every file written by "
            "the harness holds facts, counts and ids; each row README ends with a checklist for the reviewer.",
        ]
    )
    return _lines(lines)


# ---------------------------------------------------------------------------------------------
# The folder argument
# ---------------------------------------------------------------------------------------------


def resolve_folder(text: Any, root: str) -> Optional[str]:
    """The real path of a dated folder under tests/evidence, or None when the argument is not one.

    The argument may be repo-relative or absolute. It must be a real folder (not a symlink, none on the way) whose
    real path is strictly inside the real evidence folder, with a plain name that starts with rerun-. The path
    returned is the checked absolute path (no symlink on the way), which promote_into checks again. A closing step
    also refuses the frozen folders (the caller tells them apart with is_frozen).
    """
    if not isinstance(text, str) or text == "" or "\x00" in text or ".." in text.split(os.sep):
        return None
    lexical = os.path.abspath(text if os.path.isabs(text) else os.path.join(root, text))
    evidence = os.path.join(os.path.abspath(root), *EVIDENCE_PARTS)
    if not lexical.startswith(evidence + os.sep):
        return None
    relative = os.path.relpath(lexical, evidence).split(os.sep)
    if len(relative) != 1 or not relative[0].startswith(DATED_PREFIX) or _SAFE_NAME.match(relative[0]) is None:
        return None
    path = os.path.abspath(root)
    for part in list(EVIDENCE_PARTS) + relative:
        path = os.path.join(path, part)
        try:
            mode = os.lstat(path).st_mode
        except OSError:
            return None
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            return None
    real_evidence = os.path.realpath(evidence)
    if not os.path.realpath(lexical).startswith(real_evidence + os.sep):
        return None
    return lexical


def is_frozen(folder: str) -> bool:
    return os.path.basename(folder) in FROZEN_FOLDERS


# ---------------------------------------------------------------------------------------------
# close, report, check-words
# ---------------------------------------------------------------------------------------------


def report_lines(folder: str) -> List[str]:
    """The two tables a close would write next, as text lines; nothing is written and no run root is opened."""
    part = part_names(folder)[0]
    items = read_items(folder)
    return render_digest_table(items, part).splitlines() + [""] + render_usage_by_row(items, part).splitlines()


def _scratch_map(runs: str) -> Dict[str, str]:
    import pc_row1  # imported late: pc_row1 imports this module's siblings

    return pc_row1.caller_map({"run_root": os.path.join(runs, "placeholder"), "auto_memory": None}, runs)


def _add_flat_files(
    folder: str,
    root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    files: Mapping[str, bytes],
    run_name: str,
    out: TextIO,
) -> Tuple[int, int]:
    """Stage flat files in a run root, sanitize them and add them to the folder with promote_into: (exit code, files added).

    Every refusal prints its fixed lines to `out` and returns the code; nothing is overwritten. run_name is the name
    of the run folder in the runs root (the stamp is added by the caller).
    """
    try:
        runs = pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=root)
        harness = pc_spike.harness_home(env, env.get("HOME") or None, root)
    except pc_spike.HomeRefused:
        _write(out, MESSAGE_BLOCKED + "\n")
        return pc_exitcodes.PREFLIGHT_BLOCKED, 0
    config_dir = os.path.join(harness, pc_spike.CONFIG_DIR_NAME)
    try:
        pc_spike.ensure_runs_root(runs)
        run_root = pc_runroot.allocate_run_root(runs, run_name)
        stage = pc_evidence.new_stage_dir(run_root)
        sanitizer = pc_sanitize.Sanitizer.from_machine(root, _scratch_map(runs))
        deny_entries = sanitizer.deny_entries()
        count = pc_evidence.stage_tree(stage, dict(files), sanitizer)
    except (pc_sanitize.SanitizerError, pc_leakgate.ScannerError):
        _write(out, MESSAGE_SANITIZER + "\n")
        return pc_exitcodes.SCANNER_ERROR, 0
    except pc_runroot.RunRootCollision:
        _write(out, MESSAGE_COLLISION + "\n")
        return pc_exitcodes.RUNROOT_COLLISION, 0
    except (pc_runroot.RunRootError, pc_spike.SpikeError, OSError):
        _write(out, MESSAGE_STAGING + "\n")
        return pc_exitcodes.PREFLIGHT_FAIL, 0
    result = pc_promote.promote_into(stage, folder, root, config_dir=config_dir, deny_entries=deny_entries)
    if int(result.code) != pc_exitcodes.OK:
        _write(out, str(result.message) + "\n")
        for line in str(result.report_text).splitlines():
            if line.strip():
                _write(out, line + "\n")
        return int(result.code), 0
    return pc_exitcodes.OK, count


def close_folder(
    folder: str,
    root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    baseline: bool,
    out: TextIO,
) -> int:
    """Stage the part files (and the README when absent), sanitize them and add them with promote_into."""
    part, digest_name, usage_name = part_names(folder)
    items = read_items(folder)
    files: Dict[str, bytes] = {
        digest_name: render_digest_table(items, part).encode("utf-8"),
        usage_name: render_usage_by_row(items, part).encode("utf-8"),
    }
    readme_kept = os.path.lexists(os.path.join(folder, README_FILE))
    if not readme_kept:
        files[README_FILE] = render_folder_readme(folder, items, baseline).encode("utf-8")
    stamp = clock().strftime("%Y%m%dT%H%M%SZ")
    code, count = _add_flat_files(folder, root, env, clock, files, "close-%s-part-%d" % (stamp, part), out)
    if code != pc_exitcodes.OK:
        return code
    _write(out, "closed: %s, part %d, %d file(s)\n" % (os.path.basename(folder), part, count))
    if readme_kept:
        _write(out, "%s: already present, kept as it is\n" % README_FILE)
    return pc_exitcodes.OK


# ---------------------------------------------------------------------------------------------
# row7-review
# ---------------------------------------------------------------------------------------------

_REVIEW_STATES = {STATE_FILED: pc_review.STATE_FILED, STATE_STOPPED: pc_review.STATE_STOPPED, STATE_SKIPPED: pc_review.STATE_SKIPPED}


def row7_attempts(folder: str) -> List[pc_review.Attempt]:
    """The row 7 attempts of a dated folder as filed: the bare folder is attempt 1, then -attempt-N, STOPPED- and SKIPPED- labels.

    Read from the filed files only: a filed attempt's do-not-redo-candidates.md (absent or unreadable is recorded as
    such, not skipped), a stopped or skipped attempt's reason line. Ordering is left to pc_review (by attempt number).
    """
    found: List[pc_review.Attempt] = []
    for item in read_items(folder):
        if item.row_id != pc_rows.ROW7 or item.state not in _REVIEW_STATES:
            continue
        parsed: Optional[Dict[str, Any]] = None
        problem = ""
        reason = ""
        if item.state == STATE_FILED:
            text = _read_text(os.path.join(folder, item.folder, pc_review.CANDIDATE_FILE))
            if text is None:
                problem = pc_review.PROBLEM_ABSENT
            else:
                try:
                    parsed = pc_review.parse_candidates(text)
                except pc_review.ReviewError:
                    problem = pc_review.PROBLEM_UNREADABLE
        else:
            reason = item.reason if item.reason != NO_REASON else ""
        found.append(
            pc_review.Attempt(item.folder, item.attempt, _REVIEW_STATES[item.state], reason, parsed, problem)
        )
    return found


def review_part_name(folder: str) -> str:
    """row7-review.md when it is absent, else the first free row7-review-part-N.md from 2."""
    if not os.path.lexists(os.path.join(folder, REVIEW_FILE)):
        return REVIEW_FILE
    number = 2
    while os.path.lexists(os.path.join(folder, "row7-review-part-%d.md" % number)):
        number += 1
    return "row7-review-part-%d.md" % number


def review_folder(
    folder: str,
    root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    out: TextIO,
    err: TextIO,
) -> int:
    """Build row7-review from the filed attempts and add it as a new flat file; an earlier part is never touched."""
    attempts = row7_attempts(folder)
    if not attempts:
        _write(err, MESSAGE_NO_ROW7 + "\n")
        return pc_exitcodes.USAGE
    name = review_part_name(folder)
    stamp = clock().strftime("%Y%m%dT%H%M%SZ")
    suffix = "" if name == REVIEW_FILE else name[len("row7-review"):-len(".md")]
    code, _count = _add_flat_files(
        folder, root, env, clock, {name: pc_review.render_row7_review(attempts).encode("utf-8")},
        "review-%s%s" % (stamp, suffix or "-part-1"), out,
    )
    if code != pc_exitcodes.OK:
        return code
    _write(out, "review: %s, %s, %d attempt(s)\n" % (os.path.basename(folder), name, len(attempts)))
    return pc_exitcodes.OK


def _vocabulary_hits(text: str, is_readme: bool, is_comparison: bool = False) -> int:
    """The number of vocabulary words on the lines of `text`.

    Skipped: every quoted line (`> `), the closing line of a README (the pending line, or after a review the one line
    that starts with the same prefix and holds the reviewer's own text), and, in the comparison file, the lines the
    comparer marks as quoted from committed files.
    """
    pattern = pc_evidence.verdict_pattern()
    lines = text.splitlines()
    last = len(lines) - 1
    hits = 0
    for number, line in enumerate(lines):
        if line.startswith(pc_evidence.QUOTE_MARKER):
            continue
        if is_comparison and line.startswith(pc_compare.CONTENT_MARK):
            continue
        if is_readme and number == last and (line == pc_evidence.VERDICT_LINE or line.startswith(VERDICT_PREFIX)):
            continue
        hits += len(pattern.findall(line))
    return hits


def check_words(folder: str) -> Tuple[int, int]:
    """(files scanned, hits) over the harness-authored files of a dated folder (EVID-05).

    The files are the ones pc_evidence.harness_authored_names selects: the top-level files the harness writes and the
    harness-written files of every row, STOPPED and SKIPPED folder. A file that cannot be read counts as one hit.
    """
    names: List[str] = []
    for top in sorted(os.listdir(folder)):
        path = os.path.join(folder, top)
        mode = os.lstat(path).st_mode
        if stat.S_ISREG(mode):
            names.append(top)
        elif stat.S_ISDIR(mode) and not stat.S_ISLNK(mode):
            for second in sorted(os.listdir(path)):
                inner = os.path.join(path, second)
                inner_mode = os.lstat(inner).st_mode
                if stat.S_ISREG(inner_mode):
                    names.append("%s/%s" % (top, second))
                elif stat.S_ISDIR(inner_mode) and not stat.S_ISLNK(inner_mode):
                    for third in sorted(os.listdir(inner)):
                        names.append("%s/%s/%s" % (top, second, third))
    scanned = 0
    hits = 0
    for name in pc_evidence.harness_authored_names(names):
        text = _read_text(os.path.join(folder, *name.split("/")))
        scanned += 1
        if text is None:
            hits += 1
            continue
        hits += _vocabulary_hits(text, name.split("/")[-1] == README_FILE, name == COMPARISON_FILE)
    return scanned, hits


# ---------------------------------------------------------------------------------------------
# finalize: the baseline form of a dated folder (plan 04-18; RERUN-03, RERUN-04; D-10, D-11, D-16)
# ---------------------------------------------------------------------------------------------


def _refuse_constant(_name: str) -> Any:
    raise ValueError("not a plain JSON value")


def _no_duplicate_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    keys = [key for key, _value in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("a repeated key")
    return dict(pairs)


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_COUNT


def read_clone_facts(path: Any) -> Optional[Dict[str, Any]]:
    """The clone-facts file as a dict, or None when it is anything but the fixed schema.

    The schema: a JSON object with exactly the keys of CLONE_FACTS_KEYS. env_names is a list of at most 40 distinct
    names of upper-case letters, digits and underscores; the five counts are non-negative integers; clone_head is 40
    lower-case hex characters; source_kind is url or local; home_kind is throwaway or real. No value is ever a path or
    a login, and nothing here echoes the file. Read through lstat, so a symlink is not followed.
    """
    if not isinstance(path, str) or path == "" or "\x00" in path:
        return None
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return None
        with open(path, "rb") as handle:
            data = handle.read(MAX_FACTS_BYTES + 1)
        if len(data) > MAX_FACTS_BYTES:
            return None
        parsed = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys, parse_constant=_refuse_constant)
    except (OSError, ValueError, UnicodeDecodeError, RecursionError):
        return None
    if not isinstance(parsed, dict) or set(parsed) != set(CLONE_FACTS_KEYS):
        return None
    names = parsed["env_names"]
    if not isinstance(names, list) or len(names) > MAX_ENV_NAMES or len(set(map(str, names))) != len(names):
        return None
    for name in names:
        if not isinstance(name, str) or _ENV_NAME.match(name) is None:
            return None
    for key in CLONE_FACTS_COUNT_KEYS:
        if not _is_count(parsed[key]):
            return None
    head = parsed["clone_head"]
    if not isinstance(head, str) or _HEAD.match(head) is None:
        return None
    if parsed["source_kind"] not in SOURCE_KINDS or parsed["home_kind"] not in HOME_KINDS:
        return None
    return dict(parsed)


def default_entry_ids() -> Tuple[str, ...]:
    """The ids a full run holds an outcome folder for: the layouts, then the rows (the `pc_matrix.py --list` order)."""
    return tuple(entry.row_id for entry in pc_rows.build_registry())


def latest_outcomes(items: Sequence[Item]) -> Dict[str, Item]:
    """The last item of each registry id in table order: the highest attempt, a label after the folder it labels."""
    latest: Dict[str, Item] = {}
    for item in items:
        if item.row_id is not None and item.state in (STATE_FILED, STATE_STOPPED, STATE_SKIPPED):
            latest[item.row_id] = item
    return latest


def not_run_ids(items: Sequence[Item], entries: Sequence[str]) -> List[str]:
    """The expected ids that have no outcome folder at all (a row folder, STOPPED- or SKIPPED- of the id)."""
    seen = latest_outcomes(items)
    return [identifier for identifier in entries if identifier not in seen]


def _run_state_lines(items: Sequence[Item], entries: Sequence[str]) -> List[str]:
    missing = not_run_ids(items, entries)
    done = len(entries) - len(missing)
    if not missing:
        return ["Run state: complete", "Entries with an outcome folder: %d of %d" % (done, len(entries))]
    lines = [
        "Run state: partial",
        "Entries with an outcome folder: %d of %d" % (done, len(entries)),
        "Entries not run: %d" % len(missing),
    ]
    lines.extend("Not run: %s" % identifier for identifier in missing)
    return lines


def render_baseline_readme(
    folder: str, items: Sequence[Item], entries: Sequence[str], facts: Optional[Mapping[str, Any]]
) -> str:
    """The folder README of a baseline: the label, the row counts, the Run state lines and the clone facts when given.

    Built from the filed rows and the strict clone-facts dict only. It holds no closing reviewer line and no word of
    the vocabulary the harness never writes.
    """
    name = os.path.basename(folder.rstrip(os.sep))
    model = _recorded(folder, items, "model-id.txt", _MODEL_LINE)
    build = _recorded(folder, items, "claude-version.txt", _BUILD_TEXT)
    latest = latest_outcomes(items)
    counts = dict((state, sum(1 for item in latest.values() if item.state == state)) for state in
                  (STATE_FILED, STATE_STOPPED, STATE_SKIPPED))
    folders = dict((state, sum(1 for item in items if item.state == state)) for state in
                   (STATE_FILED, STATE_STOPPED, STATE_SKIPPED, STATE_OTHER))
    lines = [
        "# %s" % name,
        "",
        "This folder is a new baseline on the pinned model and the Claude Code build its rows record (model %s, Claude "
        "Code %s). It is not a replication of the committed publication folder `tests/evidence/publication-2026-10-20`: "
        "that run recorded no model, so the model cannot be matched." % (model, build),
        "",
        "Row folders present when this file was written: %d (%d filed, %d STOPPED, %d SKIPPED, %d unrecognised)."
        % (len(items), folders[STATE_FILED], folders[STATE_STOPPED], folders[STATE_SKIPPED], folders[STATE_OTHER]),
        "Entries by outcome, the latest attempt of each: %d filed, %d STOPPED, %d SKIPPED."
        % (counts[STATE_FILED], counts[STATE_STOPPED], counts[STATE_SKIPPED]),
    ]
    lines.extend(_run_state_lines(items, entries))
    if entries and not_run_ids(items, entries):
        lines.extend(
            [
                "",
                "This is a partial baseline: only the entries with an outcome folder were measured, and no line of this "
                "folder describes the entries listed as not run.",
            ]
        )
    if facts is not None:
        names = list(facts["env_names"])
        lines.extend(
            [
                "",
                "## Clean-clone run facts",
                "",
                "These facts come from the clone-facts file of the bootstrap: names and counts only, no value.",
                "",
                "- environment variable names the run was started with (%d, also in `%s`): %s"
                % (len(names), ENV_NAMES_FILE, ", ".join(names) if names else "none"),
                "- before the run: %d checkpoint binaries on the search path of the child, %d helper files in the clone"
                % (facts["path_checkpoint_binaries"], facts["helper_files_in_clone"]),
                "- after the run: %d helper calls, %d to the stub, %d to anything else"
                % (facts["helper_calls"], facts["helper_calls_stub"], facts["helper_calls_other"]),
                "- clone head: %s" % facts["clone_head"],
                "- source of the clone: %s"
                % ("the public address" if facts["source_kind"] == "url" else "a local path"),
                "- home folder of the child: %s"
                % ("a throwaway folder" if facts["home_kind"] == "throwaway" else "the real home folder"),
            ]
        )
    lines.extend(
        [
            "",
            "`digest-table.md` and `usage-by-row.txt` list every row folder with its digests and costs. "
            "`comparison-vs-publication-2026-10-20.txt` lines this folder up against the reference; the lines that start "
            "with `  content: ` are quoted from committed files. `review-brief.md` is the text for the reviewer. A STOPPED "
            "or SKIPPED folder is a label for a run that did not finish or did not start, not a result.",
            "",
            "Each row README ends with a closing reviewer line that reads PENDING until a review is filed. Every file "
            "written by the harness holds facts, counts and ids.",
        ]
    )
    return _lines(lines)


def _quoted(line: str) -> str:
    return pc_evidence.QUOTE_MARKER + " ".join(line.split())[:_QUOTE_CAP]


def _readme_quote_lines(folder: str, item: Item) -> List[str]:
    """The lines of a row, STOPPED or SKIPPED README the reviewer reads, each quoted with `> `; plain text when none."""
    text = _read_text(os.path.join(folder, item.folder, README_FILE))
    if text is None:
        return ["(no README is filed for this folder)"]
    lines = text.splitlines()
    picked: List[str] = []
    if item.state == STATE_FILED:
        if "## Reviewer checklist" in lines:
            for line in lines[lines.index("## Reviewer checklist") + 1:]:
                if line.startswith("- ["):
                    picked.append(line)
    elif item.state == STATE_STOPPED:
        picked = [line for line in lines if line.startswith(("Row: ", "Reason: ", "Stage: "))]
    elif item.state == STATE_SKIPPED:
        picked = [line for line in lines if line.startswith(_SKIP_HEAD)]
    if not picked:
        return ["(no checklist line is filed for this folder)"]
    return [_quoted(line) for line in picked]


def triple_folders(root: str) -> List[str]:
    """The names of the committed triple folders of the evidence tree of ROOT, sorted."""
    evidence = os.path.join(root, *EVIDENCE_PARTS)
    found: List[str] = []
    try:
        names = sorted(os.listdir(evidence))
    except OSError:
        return found
    for name in names:
        try:
            mode = os.lstat(os.path.join(evidence, name)).st_mode
        except OSError:
            continue
        if stat.S_ISDIR(mode) and not stat.S_ISLNK(mode) and _TRIPLE_FOLDER.match(name) and _SAFE_NAME.match(name):
            found.append(name)
    return found


def render_review_brief(
    folder: str, root: str, items: Sequence[Item], entries: Sequence[str]
) -> str:
    """The text bokiko pastes to Codex: built from the filed files of the folder and the names of the clone's triple folder.

    It asks for one line per row and layout naming a conclusion in a few words and the reason, and for a plain statement
    for any row the files cannot support. It holds no word of the vocabulary the harness never writes: every line that
    quotes a file starts with `> `.
    """
    name = os.path.basename(folder.rstrip(os.sep))
    model = _recorded(folder, items, "model-id.txt", _MODEL_LINE)
    build = _recorded(folder, items, "claude-version.txt", _BUILD_TEXT)
    missing = not_run_ids(items, entries)
    triples = triple_folders(root)
    own_table = os.path.lexists(os.path.join(folder, REVIEW_FILE))
    lines = [
        "# Review brief: %s" % name,
        "",
        "This brief is built from the filed files of one dated evidence folder. Every number in it is quoted from those "
        "files, and every line that starts with `> ` is quoted text. The harness has judged nothing.",
        "",
        "## What to return",
        "",
        "Give one line for each row and layout listed under Rows and layouts below. Each line names a conclusion in a few "
        "words and gives the reason. When a row cannot be judged from the files named in its quoted lines, write a plain "
        "statement saying so for that row instead of a conclusion. Add no score and no summary of the whole folder.",
        "",
        "## Folder",
        "",
        "- folder: %s" % name,
        "- model: %s" % model,
        "- Claude Code build: %s" % build,
    ]
    lines.extend("- " + line for line in _run_state_lines(items, entries)[:1])
    if triples:
        lines.append("- row 7 review table of the committed triple folder: %s (its row7-review.md)" % ", ".join(triples))
    else:
        lines.append("- no row 7 triple folder is present in this clone")
    lines.append(
        "- row 7 review table of this folder: %s" % ("row7-review.md" if own_table else "none is filed in this folder")
    )
    lines.extend(["", "## Digest table", ""])
    lines.extend(_quoted(line) for line in render_digest_table(items, 1).splitlines() if line.strip())
    if missing:
        lines.extend(["", "## Not run", "", "These ids have no outcome folder. They are listed only; no question is asked about them.", ""])
        lines.extend("- Not run: %s" % identifier for identifier in missing)
    lines.extend(["", "## Rows and layouts", ""])
    for item in items:
        lines.append("### %s (%s)" % (item.folder, item.state))
        lines.append("")
        lines.extend(_readme_quote_lines(folder, item))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


INTERIM_COMPARISON = "The comparer report is not part of this file.\n"


def comparison_text(folder: str) -> Optional[str]:
    """The text filed as the comparison file, or None when the reference tree cannot be read."""
    return INTERIM_COMPARISON


def finalize_folder(
    folder: str,
    root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    out: TextIO,
    err: TextIO,
    facts_path: Optional[str] = None,
    entries: Optional[Sequence[str]] = None,
) -> int:
    """File the baseline form of a dated folder: README, both tables, the comparison, the brief, the environment names.

    entries are the ids a full run holds an outcome folder for (default: every layout and row of the registry). Nothing
    is filed when the clone-facts file, the folder or the reference is refused; an existing top-level name is refused
    with 17 and nothing is created.
    """
    facts: Optional[Dict[str, Any]] = None
    if facts_path is not None:
        facts = read_clone_facts(facts_path)
        if facts is None:
            _write(err, MESSAGE_FACTS + "\n")
            return pc_exitcodes.USAGE
    for existing in FINALIZE_FILES:
        if os.path.lexists(os.path.join(folder, existing)):
            _write(err, MESSAGE_EXISTS + "\n")
            return pc_exitcodes.PROMOTE_REFUSED
    expected = tuple(entries) if entries is not None else default_entry_ids()
    items = read_items(folder)
    comparison = comparison_text(folder)
    if comparison is None:
        _write(err, MESSAGE_REFERENCE + "\n")
        return pc_exitcodes.USAGE
    files: Dict[str, bytes] = {
        README_FILE: render_baseline_readme(folder, items, expected, facts).encode("utf-8"),
        DIGEST_FILE: render_digest_table(items, 1).encode("utf-8"),
        USAGE_FILE: render_usage_by_row(items, 1).encode("utf-8"),
        COMPARISON_FILE: comparison.encode("utf-8"),
        BRIEF_FILE: render_review_brief(folder, root, items, expected).encode("utf-8"),
    }
    if facts is not None:
        files[ENV_NAMES_FILE] = _lines(list(facts["env_names"])).encode("utf-8")
    stamp = clock().strftime("%Y%m%dT%H%M%SZ")
    code, count = _add_flat_files(folder, root, env, clock, files, "finalize-%s" % stamp, out)
    if code != pc_exitcodes.OK:
        return code
    _write(out, "finalized: %s, %d file(s)\n" % (os.path.basename(folder), count))
    for line in _run_state_lines(items, expected):
        _write(out, line + "\n")
    return pc_exitcodes.OK


# ---------------------------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------------------------


def _write(stream: TextIO, text: str) -> None:
    stream.write(text)
    stream.flush()


class _Parser(argparse.ArgumentParser):
    """An argument parser whose errors print one fixed line and exit 2, never echoing a value."""

    def __init__(self, out: TextIO, err: TextIO) -> None:
        super().__init__(prog=PROG, add_help=True, allow_abbrev=False)
        self._out = out
        self._err = err

    def error(self, message: str) -> Any:  # type: ignore[override]
        _write(self._err, USAGE_LINE + "\n")
        _write(self._err, "%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        raise SystemExit(pc_exitcodes.USAGE)

    def print_help(self, file: Optional[TextIO] = None) -> None:
        _write(self._out, USAGE_LINE + "\n")

    def print_usage(self, file: Optional[TextIO] = None) -> None:
        _write(self._err, USAGE_LINE + "\n")


COMMANDS = ("close", "report", "check-words", "row7-review", "finalize")


def build_parser(out: TextIO, err: TextIO, command: str) -> argparse.ArgumentParser:
    """The parser of the words after the subcommand: --folder, and --baseline for close."""
    parser = _Parser(out, err)
    parser.add_argument("--folder", required=True)
    if command == "close":
        parser.add_argument("--baseline", action="store_true")
    if command == "finalize":
        parser.add_argument("--clone-facts", default=None, dest="clone_facts")
    return parser


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(
    argv: Optional[Sequence[str]] = None,
    env: Optional[Mapping[str, str]] = None,
    repo_root: Optional[str] = None,
    clock: Optional[Callable[[], datetime.datetime]] = None,
    out: Optional[TextIO] = None,
    err: Optional[TextIO] = None,
) -> int:
    """Run one subcommand and return the exit code; this function never calls sys.exit."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    words = list(sys.argv[1:] if argv is None else argv)
    if words in (["-h"], ["--help"]):
        _write(out, USAGE_LINE + "\n")
        return pc_exitcodes.OK
    if not words or words[0] not in COMMANDS:
        _write(err, USAGE_LINE + "\n")
        _write(err, "%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        return pc_exitcodes.USAGE
    command = words[0]
    parser = build_parser(out, err, command)
    try:
        args = parser.parse_args(words[1:])
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
    source: Mapping[str, str] = dict(os.environ) if env is None else env
    root = repo_root if repo_root else _REPO_ROOT
    folder = resolve_folder(args.folder, root)
    if folder is None:
        _write(err, MESSAGE_FOLDER + "\n")
        return pc_exitcodes.USAGE
    if command in ("close", "row7-review", "finalize") and is_frozen(folder):
        _write(err, MESSAGE_FROZEN + "\n")
        return pc_exitcodes.USAGE
    try:
        if command == "report":
            for line in report_lines(folder):
                _write(out, line + "\n")
            return pc_exitcodes.OK
        if command == "check-words":
            scanned, hits = check_words(folder)
            _write(out, "check-words: %d file(s) scanned, %d hit(s)\n" % (scanned, hits))
            return pc_exitcodes.OK if hits == 0 else pc_exitcodes.PREFLIGHT_FAIL
        if command == "row7-review":
            return review_folder(folder, root, source, clock or _utc_now, out, err)
        if command == "finalize":
            return finalize_folder(folder, root, source, clock or _utc_now, out, err, args.clone_facts)
        return close_folder(folder, root, source, clock or _utc_now, bool(args.baseline), out)
    except OSError:
        _write(err, MESSAGE_FOLDER + "\n")
        return pc_exitcodes.USAGE


if __name__ == "__main__":
    sys.exit(main())
