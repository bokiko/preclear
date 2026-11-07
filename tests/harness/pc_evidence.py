"""Filing a finished row 1 run as sanitized, leak-gated mechanical evidence (plan 03-04; EVID-04, EVID-05, HARN-05).

The only route from a run root to tests/evidence is here, and it has four steps in a fixed order:

  1. stage       one tree is rendered from files that are already on disk in the run root (stage records, raw
                 streams, stored prompts, snapshots, the wrapper log); nothing is taken from memory of the run
  2. sanitize    every staged file passes through the sanitizer that run_row built before any money was spent
  3. gate        the whole staged tree is scanned by the leak gate with the sanitizer's deny entries (review WR-14)
  4. promote     pc_promote.promote creates the new dated folder exclusively, once, from the scanned bytes

Raw captures never leave the run root: no stream, no NUL status capture, no hook log, no stage record, no git state
file and no run.json is ever staged. The stage folder is the first free stage-N inside the run root and is never
reused or removed. Harness-authored files hold facts, counts and ids written as `name: value` lines (yes and no for
booleans); the row README ends with the one line VERDICT_LINE and no harness-authored file holds a verdict word.
A value that could not be measured is written UNCONFIRMED and never left blank.

A row is described by its registry entry (pc_rows.RowSpec): the row folder name, the stage file labels, the Setup
paragraph, the allowlist profile and the chain-complete rule are read from the entry, so no renderer names a row.
file_row stages only the row folder and promotes it to <dated folder>/<row id>; an existing row folder is refused
with 17 and an existing dated folder is not, so two rows share one dated folder. The folder-level README is no
longer part of the filing: render_folder_readme stays defined for the step that closes a dated folder.

Renderers are pure functions over data read from the run root; they write nothing. Messages are fixed text with
counts, ids and rule labels only, never a path, a host name or the login. Standard library only, Python 3.9 floor.
Nothing here deletes, renames, moves or truncates a file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pc_checks
import pc_exitcodes
import pc_flags
import pc_manifest
import pc_measure
import pc_promote
import pc_rows
import pc_runroot
import pc_sanitize
import pc_spend
import pc_spike
import pc_stream

VERDICT_LINE = "Reviewer verdict: PENDING"
REVIEW_POINTER_LINE = (
    "- do-not-redo review: the table of candidates for the attempts of this row is row7-review.md at the top of the dated "
    "folder; it lists candidates and counts only"
)
UNCONFIRMED = "UNCONFIRMED"
MARKER_NO_RESUME = "NO-RESUME-LINE"
STAGE_ORDER: Tuple[str, ...] = ("s1", "s2", "s3", "s4")  # the stage names a row may have (row 12 has four, plan 04-13)
USAGE_KEYS: Tuple[Tuple[str, str], ...] = (
    ("input_tokens", "input"),
    ("cache_creation_input_tokens", "cache creation"),
    ("cache_read_input_tokens", "cache read"),
    ("output_tokens", "output"),
)
SECTION_NAMES: Tuple[str, ...] = (
    "Init manifest",
    "Instruction audit",
    "Assertions",
    "Write boundary",
    "Git",
    "Helper calls",
    "Ledgers",
    "Sessions",
    "Denials",
    "Checkpoint bytes",
)
ONE_LINE_TOOLS: Tuple[str, ...] = ("Read", "Glob", "Grep")
SHORT_LIMIT = 200

MESSAGE_UNREADABLE = "FAIL: the run root could not be read for filing; nothing is filed"
MESSAGE_BREACH = "FAIL: the checks found a breach; nothing is filed"
MESSAGE_NO_PROMPT = "FAIL: a stage prompt was not stored in the run root; nothing is filed"
MESSAGE_NO_STREAM = "FAIL: a stage stream cannot be read; nothing is filed"
MESSAGE_SANITIZER = "SCANNER_ERROR: the sanitizer could not process a staged file; nothing is filed"
MESSAGE_STAGING = "FAIL: the stage folder could not be written; nothing is filed"
MESSAGE_STAGE_NOT_CLEAN = "FAIL: a stage did not finish cleanly; nothing is filed"
MESSAGE_STAGE_MISSING = "FAIL: a stage did not run; nothing is filed"
MESSAGE_NO_DENY_ENTRIES = "SCANNER_ERROR: the deny entries were not built; nothing is filed"

_STAGE_DIR_MODE = 0o700
_FILE_MODE = 0o644
_GIT_TIMEOUT_SECONDS = 60


class EvidenceError(Exception):
    """The run root does not hold what filing needs; messages are fixed text."""


def _row1() -> Any:
    import pc_row1  # imported late: pc_row1 imports this module

    return pc_row1


def _spec_of_run(data: Any) -> pc_rows.RowSpec:
    """The registry entry of the row a run record names, matched exactly; a record with no row is a row 1 record.

    Runs filed before the record carried a row id are row 1 runs. An id that matches no registry entry is an
    EvidenceError, so no row id reaches a path or a label before it has matched the registry (T-04-01).
    """
    run = data.run if isinstance(data.run, dict) else {}
    row = run.get("row", pc_rows.ROW1)
    entry = pc_rows.find_runnable(pc_rows.build_registry(), row) if isinstance(row, str) else None
    if entry is None:
        raise EvidenceError("the run record names a row that is not in the registry")
    return entry


def is_refresh_stage(spec: pc_rows.RowSpec, stage_name: str) -> bool:
    """True for a /preclear stage that comes after another /preclear stage of the row (row 12's s4, plan 04-13)."""
    seen_preclear = False
    for stage in spec.stages:
        if stage.name == stage_name:
            return stage.kind == "preclear" and seen_preclear
        if stage.kind == "preclear":
            seen_preclear = True
    raise EvidenceError("a stage is not part of the row")


def stage_label(spec: pc_rows.RowSpec, stage_name: str) -> str:
    """The file label of a stage's traces: its name and its kind (s1-work, s2-preclear, s3-resume).

    A later /preclear stage (the refresh of row 12) is labelled s4-preclear-refresh, the committed name of its traces.
    """
    for stage in spec.stages:
        if stage.name == stage_name:
            word = "%s-%s" % (stage.name, stage.kind)
            return word + "-refresh" if is_refresh_stage(spec, stage_name) else word
    raise EvidenceError("a stage is not part of the row")


def prompt_label(spec: pc_rows.RowSpec, stage_name: str) -> str:
    """The file label of a stage's prompt file: the stage label, except that a refresh keeps the committed s4-preclear."""
    label = stage_label(spec, stage_name)
    return label[: -len("-refresh")] if label.endswith("-refresh") else label


def exit_label(spec: pc_rows.RowSpec, stage_name: str) -> str:
    """The base name of a stage's .exit and .err files: s1 and a refresh stage use the bare stage name (committed names)."""
    if stage_name == "s1" or is_refresh_stage(spec, stage_name):
        return stage_name
    return stage_label(spec, stage_name)


def _stage_kind(spec: pc_rows.RowSpec, stage_name: str) -> str:
    for stage in spec.stages:
        if stage.name == stage_name:
            return stage.kind
    raise EvidenceError("a stage is not part of the row")


class StageData(NamedTuple):
    """One stage as it is on disk: the record, the raw streams, the stored prompt and the parsed events."""

    name: str
    record: Dict[str, Any]
    stdout: bytes
    stderr: bytes
    prompt: Optional[str]
    events: Optional[List[Dict[str, Any]]]


class RunData(NamedTuple):
    run: Dict[str, Any]
    chain: Optional[Dict[str, Any]]
    stages: List[StageData]
    paths: Dict[str, Optional[str]]


def _read_bytes(path: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        raise EvidenceError("a run root file could not be read") from None


def _read_json(path: str) -> Any:
    try:
        return json.loads(_read_bytes(path).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise EvidenceError("a run root file is not valid JSON") from None


def load_stage_data(run_root: str) -> RunData:
    """Read the run record, the chain record and every stage that has a record from the run root.

    A stream that does not parse leaves the stage's events None; the caller decides what that means. A missing
    stored prompt leaves prompt None. A missing run.json or a malformed record is an EvidenceError.
    """
    paths = _row1().paths_for(run_root)
    raw = str(paths["raw"])
    run = _read_json(os.path.join(raw, "run.json"))
    if not isinstance(run, dict):
        raise EvidenceError("the run record has an unexpected shape")
    chain_path = os.path.join(raw, "chain.json")
    chain = _read_json(chain_path) if os.path.isfile(chain_path) else None
    if chain is not None and not isinstance(chain, dict):
        raise EvidenceError("the chain record has an unexpected shape")
    stages: List[StageData] = []
    for name in STAGE_ORDER:
        record_path = os.path.join(raw, name + ".record.json")
        if not os.path.isfile(record_path):
            continue
        record = _read_json(record_path)
        if not isinstance(record, dict):
            raise EvidenceError("a stage record has an unexpected shape")
        stdout_path = os.path.join(raw, name + ".stdout")
        stderr_path = os.path.join(raw, name + ".stderr")
        prompt_path = os.path.join(raw, name + ".prompt")
        stdout = _read_bytes(stdout_path) if os.path.isfile(stdout_path) else b""
        stderr = _read_bytes(stderr_path) if os.path.isfile(stderr_path) else b""
        prompt: Optional[str] = None
        if os.path.isfile(prompt_path):
            try:
                prompt = _read_bytes(prompt_path).decode("utf-8")
            except UnicodeDecodeError:
                prompt = None
        events: Optional[List[Dict[str, Any]]]
        try:
            events = pc_stream.parse_stream(stdout)
            pc_stream.require_single_result(events)
            pc_stream.init_manifest(events)
        except pc_stream.StreamError:
            events = None
        stages.append(StageData(name, record, stdout, stderr, prompt, events))
    return RunData(run, chain, stages, paths)


# ---------------------------------------------------------------------------------------------
# Small value helpers
# ---------------------------------------------------------------------------------------------


def _text(value: Any) -> str:
    """The text of a recorded value, or UNCONFIRMED when it is absent."""
    if value is None or value == "":
        return UNCONFIRMED
    return str(value)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _decimal(value: Any) -> Optional[Decimal]:
    if not isinstance(value, str):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _lines(items: Iterable[str]) -> bytes:
    return ("\n".join(items) + "\n").encode("utf-8")


def _stage(data: RunData, name: str) -> Optional[StageData]:
    for stage in data.stages:
        if stage.name == name:
            return stage
    return None


def _result_event(stage: StageData) -> Dict[str, Any]:
    return pc_stream.require_single_result(stage.events or [])


def _result_text(stage: StageData) -> str:
    if stage.events is None:
        return ""
    text = _result_event(stage).get("result")
    return text if isinstance(text, str) else ""


def _record_int(stage: StageData, key: str) -> Optional[int]:
    value = stage.record.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def usage_totals(stages: Sequence[StageData]) -> Tuple[str, str]:
    """Return (row total, run total) as Decimal text, or UNCONFIRMED when a chain total is missing.

    The row total adds the final cumulative total of each session chain once: s1 sits inside the s2 chain, so it
    is never added to s2. The run total is the sum of the row totals filed in this run, which is the one row.
    """
    last: Dict[str, Optional[Decimal]] = {}
    for stage in stages:
        last[str(stage.record.get("session_id"))] = _decimal(stage.record.get("cumulative"))
    totals = list(last.values())
    if not totals or any(total is None for total in totals):
        return UNCONFIRMED, UNCONFIRMED
    text = format(pc_spend.row_total([t for t in totals if t is not None]), "f")
    return text, text


# ---------------------------------------------------------------------------------------------
# Provenance files (HARN-05)
# ---------------------------------------------------------------------------------------------


def render_usage(data: RunData, spec: Optional[pc_rows.RowSpec] = None, stopped: bool = False) -> bytes:
    """usage.txt: the stages in execution order, each call's own cost and the reported totals as parsed text.

    Costs are the Decimal text exactly as parsed. The row total is the s2 cumulative total plus the s3 total
    (s1 is inside the s2 chain and is never added); the run total is the sum over the rows filed in this run.
    One cumulative-consistent line per stage shows the record's flag (whether the cumulative total equals the
    earlier total plus the call's own cost: yes, no or unknown, UNCONFIRMED when the record lacks it; unknown also
    when the call's own cost was derived from the totals and not read from the per-call block, WR-04), and one
    warning line follows for each stage whose flag is no (IN-01).
    """
    row = spec if spec is not None else _spec_of_run(data)
    lines = ["usage for %s" % row.row_id, "costs are in US dollars as the stream reported them, kept as text"]
    for stage in data.stages:
        record = stage.record
        usage = record.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        tokens = ", ".join("%s %s" % (label, _text(usage.get(key))) for key, label in USAGE_KEYS)
        lines.append(
            "stage %s: session %s, subtype %s, turns %s, %s, cost %s, cumulative %s, wall %s seconds"
            % (
                stage.name,
                _text(record.get("session_id")),
                _text(record.get("subtype")),
                _text(record.get("turns")),
                tokens,
                _text(record.get("delta")),
                _text(record.get("cumulative")),
                _text(record.get("wall_seconds")),
            )
        )
    flags = [(stage.name, _text(stage.record.get("cumulative_consistent"))) for stage in data.stages]
    for name, value in flags:
        lines.append("cumulative-consistent %s: %s" % (name, value))
    for name, value in flags:
        if value == pc_checks.CORRELATED_NO:
            lines.append(
                "warning: the cumulative total at %s differs from the earlier total plus this call's own cost; "
                "check the call cost" % name
            )
    row_total, run_total = usage_totals(data.stages)
    if stopped:
        # A chain that did not finish has no row total: the sum of what the stages that ran reported is a partial
        # total, UNCONFIRMED when any of them reported no cost.
        lines.append("row total: %s, the chain did not finish" % UNCONFIRMED)
        lines.append("partial total: %s" % row_total)
        return _lines(lines)
    lines.append("row total: %s" % row_total)
    lines.append("run total: %s" % run_total)
    return _lines(lines)


def _first_events(data: RunData) -> Optional[List[Dict[str, Any]]]:
    for stage in data.stages:
        if stage.events is not None:
            return stage.events
    return None


def render_model_id(data: RunData) -> bytes:
    """model-id.txt: the model id the first readable init event reported, or UNCONFIRMED."""
    events = _first_events(data)
    if events is None:
        return _lines([UNCONFIRMED])
    return _lines([_text(pc_stream.init_manifest(events).get("model"))])


def render_claude_version(data: RunData) -> bytes:
    """claude-version.txt: the banner line built from the version the stage records hold."""
    for stage in data.stages:
        version = stage.record.get("version")
        if isinstance(version, str) and version:
            return _lines(["%s (Claude Code)" % version])
    return _lines([UNCONFIRMED])


def render_isolation_mode(data: RunData) -> bytes:
    """isolation-mode.txt: the isolation word, the setting sources and the pinned claim sentence."""
    word = data.run.get("isolation")
    return _lines(
        [
            "isolation: %s" % _text(word),
            "setting-sources: %s" % pc_flags.SETTING_SOURCES,
            pc_flags.ISOLATION_CLAIM,
        ]
    )


def _hygiene_environment() -> Dict[str, str]:
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    env.update(pc_manifest.GIT_ENV_OVERRIDES)
    return env


def _git_text(git: Optional[str], repo_root: str, args: Sequence[str]) -> Optional[Tuple[int, str]]:
    if git is None:
        return None
    try:
        done = subprocess.run(
            [git, "-C", repo_root, "--no-optional-locks"] + list(args),
            env=_hygiene_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.returncode, done.stdout.decode("utf-8", "replace")


def render_harness_version(ctx: pc_rows.RunContext) -> bytes:
    """harness-version.txt: the digest of the harness tree, the full HEAD and whether the tree is clean.

    Only read-only git commands run. A value that cannot be measured is unknown (the digest is UNCONFIRMED); a
    describe string is never used.
    """
    folder = os.path.join(ctx.repo_root, "tests", "harness")
    try:
        entries = pc_manifest.tree_manifest(folder)
        entries = [e for e in entries if b"__pycache__" not in e["path"].split(b"/")]
        digest = hashlib.sha256(pc_manifest.sha_txt_bytes(entries)).hexdigest()
    except (pc_manifest.ManifestError, OSError):
        digest = UNCONFIRMED
    git = shutil.which("git", path=ctx.env.get("PATH") or os.defpath) or shutil.which("git")
    head = "unknown"
    found = _git_text(git, ctx.repo_root, ["rev-parse", "HEAD"])
    if found is not None and found[0] == 0 and re.match(r"[0-9a-f]{40}\n?\Z", found[1]):
        head = found[1].strip()
    clean = "unknown"
    status = _git_text(git, ctx.repo_root, ["status", "--porcelain", "--", "tests/harness"])
    if status is not None and status[0] == 0:
        clean = "yes" if status[1].strip() == "" else "no"
    return _lines(["tree-sha256: %s" % digest, "head: %s" % head, "harness-tree-clean: %s" % clean])


def _file_sha(path: str) -> str:
    try:
        return hashlib.sha256(_read_bytes(path)).hexdigest()
    except EvidenceError:
        return UNCONFIRMED


def _has_wrapper(row: pc_rows.RowSpec) -> bool:
    """True for a row whose allowlist profile carries the logging wrapper; a plain row has none (plan 04-04)."""
    return row.tools_profile in (pc_rows.PROFILE_HELPER, pc_rows.PROFILE_HELPER_READ)


def render_digests(ctx: pc_rows.RunContext, data: RunData, spec: Optional[pc_rows.RowSpec] = None) -> bytes:
    """digests.txt: sha256 and name of SKILL.md, the reference files, the stub and the wrapper (run-token paths).

    A row with no wrapper (a plain row) lists the skill and the reference files only: it has no stub and no wrapper,
    so no line for either is written, not even an UNCONFIRMED one.
    """
    row = spec if spec is not None else _spec_of_run(data)
    skill = str(data.paths["skill_dir"])
    items: List[Tuple[str, str]] = [(os.path.join(skill, "SKILL.md"), os.path.join(skill, "SKILL.md"))]
    references = os.path.join(skill, "references")
    if os.path.isdir(references):
        for name in sorted(os.listdir(references)):
            full = os.path.join(references, name)
            if os.path.isfile(full):
                items.append((full, full))
    if _has_wrapper(row):
        stub = os.path.join(ctx.repo_root, "tests", "harness", "checkpoint_stub.py")
        items.append((stub, "tests/harness/checkpoint_stub.py"))
        wrapper = str(data.paths["wrapper"])
        items.append((wrapper, wrapper))
    return _lines(["%s  %s" % (_file_sha(path), name) for path, name in items])


def render_tools(data: RunData, spec: Optional[pc_rows.RowSpec] = None) -> bytes:
    """tools.txt: the allowlist of the row's profile as the comma-joined rules, with the wrapper path in them."""
    row = spec if spec is not None else _spec_of_run(data)
    rules = _row1().allowed_tools(row.tools_profile, str(data.paths["wrapper"]), row.extra_tools)
    return _lines([",".join(rules)])


def memory_policy(data: RunData) -> str:
    """The memory policy the run used, read from its run record; a record with no such key is the pinned policy.

    Rows filed before the record carried the key (Phase 3 and the helper rows) ran with auto-memory on. A value that
    is not one of the two known words is an EvidenceError, never a guess.
    """
    run = data.run if isinstance(data.run, dict) else {}
    policy = run.get("memory", pc_rows.MEMORY_PINNED)
    if policy not in (pc_rows.MEMORY_PINNED, pc_rows.MEMORY_DISABLED):
        raise EvidenceError("the run record names a memory policy that is not known")
    return policy


def render_settings_json(data: RunData) -> bytes:
    """settings.json: the settings the run used, without the audit hook (the memory switch follows the run record)."""
    rendered = pc_flags.render_settings(
        str(data.paths["auto_memory"]), None, memory_policy(data) == pc_rows.MEMORY_PINNED
    )
    return (json.dumps(rendered, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _count_names(root: str, skip_top: Sequence[str] = (), needle: Optional[str] = None) -> Optional[int]:
    """Count the entries under root without following a link: every file (needle None), or every file and folder whose
    path below root holds needle (lower case). The top-level names in skip_top are left out. None when unreadable."""
    if not os.path.isdir(root) or os.path.islink(root):
        return None
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            if dirpath == root:
                dirnames[:] = [name for name in dirnames if name not in skip_top]
                filenames = [name for name in filenames if name not in skip_top]
            for name in list(dirnames) + list(filenames):
                full = os.path.join(dirpath, name)
                if needle is None:
                    if name in filenames or os.path.islink(full):
                        count += 1
                elif needle in os.path.relpath(full, root).lower():
                    count += 1
    except OSError:
        return None
    return count


def program_count_lines(row: pc_rows.RowSpec, facts: Mapping[str, Any]) -> List[str]:
    """The executed chmod and touch counts, for a row whose allowlist holds those rules (rows 6 and 7).

    Each line is a count of the executed Bash command parts whose program word is that program, taken from the
    executed commands only (pc_checks.program_counts): a fact for the reviewer about the model's own use of the
    program, never a verdict, and nothing was prevented or hidden. A row whose allowlist holds neither rule prints
    nothing; a facts mapping with no counts prints UNCONFIRMED.
    """
    rules = list(pc_flags.BASELINE_ALLOWED_TOOLS) + list(row.extra_tools)
    counts = facts.get("program_counts")
    lines: List[str] = []
    for program in pc_checks.COUNTED_PROGRAMS:
        if "Bash(%s:*)" % program not in rules:
            continue
        value = counts.get(program) if isinstance(counts, dict) else None
        lines.append(
            "executed-%s-commands: %s"
            % (program, value if isinstance(value, int) and not isinstance(value, bool) else UNCONFIRMED)
        )
    return lines


def memory_fact_lines(data: RunData, facts: Mapping[str, Any]) -> List[str]:
    """The memory facts of a run as counts and names only: the setting, the files in the pinned auto-memory folder, the
    memory-looking paths under the project (its git folder left out) and the default memory root."""
    files = _count_names(str(data.paths["auto_memory"]))
    paths = _count_names(str(data.paths["project"]), skip_top=(".git",), needle="memory")
    return [
        "memory-setting: %s" % memory_policy(data),
        "auto-memory-files: %s" % (files if files is not None else UNCONFIRMED),
        "project-memory-paths: %s" % (paths if paths is not None else UNCONFIRMED),
        "default-memory-root: %s" % facts["memory_probe"],
    ]


# ---------------------------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------------------------


def find_checkpoint(project: str) -> Optional[str]:
    """The first plain-file checkpoint under project/.preclear/<slug>/, in sorted order, or None."""
    base = os.path.join(project, ".preclear")
    if not os.path.isdir(base):
        return None
    for name in sorted(os.listdir(base)):
        candidate = os.path.join(base, name, "checkpoint.md")
        if os.path.isfile(candidate) and not os.path.islink(candidate):
            return candidate
    return None


def measure_checkpoint(data: RunData) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Return (path, measurement) of the original checkpoint file, or (None, None) when there is none."""
    path = find_checkpoint(str(data.paths["project"]))
    if path is None:
        return None, None
    try:
        return path, pc_measure.measure_file(path)
    except OSError:
        return None, None


_NO_CHECKPOINT = "UNCONFIRMED: no plain-file checkpoint was found under the project fallback folder"


def render_measurements(data: RunData) -> Tuple[bytes, bytes]:
    """Return (measurements.txt, measurements.md).

    Both measure the ORIGINAL checkpoint (before sanitizing), per section as actual/cap. The .md adds the
    ledger folder inventory (every file, dot files included) and the auto-memory file list.
    """
    path, measurement = measure_checkpoint(data)
    if path is None or measurement is None:
        report = _NO_CHECKPOINT + "\n"
    else:
        report = pc_measure.format_report(path, measurement)
    ledgers = str(data.paths["ledgers"])
    inventory: List[str] = []
    if os.path.isdir(ledgers):
        for name in sorted(os.listdir(ledgers)):
            full = os.path.join(ledgers, name)
            if os.path.isfile(full) and not os.path.islink(full):
                content = _read_bytes(full)
                inventory.append(
                    "ledger file %s: %d bytes sha256 %s" % (name, len(content), hashlib.sha256(content).hexdigest())
                )
    memory = str(data.paths["auto_memory"])
    names = sorted(os.listdir(memory)) if os.path.isdir(memory) else []
    inventory.append("auto-memory files: %r" % (names,))
    markdown = "# Measurements (UTF-8 bytes on ORIGINAL unsanitized files)\n\n" + report + "\n" + "\n".join(inventory) + "\n"
    return report.encode("utf-8"), markdown.encode("utf-8")


# ---------------------------------------------------------------------------------------------
# Traces
# ---------------------------------------------------------------------------------------------


def _flatten(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def _results_by_id(events: Sequence[Dict[str, Any]]) -> Dict[str, Tuple[bool, str]]:
    """tool_use id to (is_error, result text). The flag is the structured field, never a search of the text."""
    found: Dict[str, Tuple[bool, str]] = {}
    for event in events:
        if event.get("type") != "user":
            continue
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id")
                if isinstance(tool_id, str) and tool_id:
                    found[tool_id] = (block.get("is_error") is True, _flatten(block.get("content")))
    return found


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _call_argument(name: str, tool_input: Mapping[str, Any]) -> str:
    for key in ("file_path", "path", "pattern", "notebook_path", "command"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            if name == "Glob" and key == "pattern":
                return value
            return value
    return _json_text(dict(tool_input))


def _block_body(name: str, tool_input: Mapping[str, Any]) -> str:
    if name == "Bash":
        command = tool_input.get("command")
        return command if isinstance(command, str) else _json_text(dict(tool_input))
    if name == "Write":
        rest = dict((k, v) for k, v in tool_input.items() if k != "content")
        content = tool_input.get("content")
        return _json_text(rest) + "\n--- content ---\n" + (content if isinstance(content, str) else "")
    return _json_text(dict(tool_input))


def _shorten(text: str, clean: Callable[[str], str]) -> str:
    one = " ".join(clean(text).split())
    return one if len(one) <= SHORT_LIMIT else one[:SHORT_LIMIT]


def render_full_trace(row_id: str, stage: StageData, label: str) -> bytes:
    """The complete trace: every call with its result and the flags the structured fields give.

    A call is flagged ERROR when its tool result is an error and REFUSAL/DENIAL when its tool_use id is in the
    structured denial union. Read, Glob and Grep results are summarised by length. No text of a reply or of a
    result decides a flag. The block shapes are the committed ones, so pc_mine.parse_trace reads them.
    """
    events = stage.events or []
    union = pc_stream.denial_report(events).union if events else frozenset()
    results = _results_by_id(events)
    calls = pc_stream.tool_calls(events)
    lines = [
        "# %s: %s: complete sanitized tool calls and results" % (row_id, label),
        "",
        "raw transcript sha256 %s, %s bytes (retained privately in the run root)"
        % (_text(stage.record.get("stdout_sha256")), _text(stage.record.get("stdout_size"))),
        "",
        "Every Bash, Write and Edit call is listed with its complete result and error flag. Read, Glob and Grep "
        "results are summarised by length. Results are keyed by tool-use id.",
        "Calls %d; results flagged as refusal/denial: %d." % (len(calls), len(union)),
        "",
    ]
    for number, (tool_id, name, tool_input) in enumerate(calls, 1):
        is_error, result = results.get(tool_id, (False, ""))
        flags = ("  ERROR" if is_error else "") + ("  REFUSAL/DENIAL" if tool_id in union else "")
        if name in ONE_LINE_TOOLS:
            lines.append(
                "### %d. %s (%s): `%s` -> result %d chars%s"
                % (number, name, tool_id, _call_argument(name, tool_input), len(result), flags)
            )
        else:
            lines.append("### %d. %s (%s)%s" % (number, name, tool_id, flags))
            lines.append("```")
            lines.append(_block_body(name, tool_input))
            lines.append("```")
            lines.append("result:")
            lines.append("```")
            lines.append(result)
            lines.append("```")
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_short_trace(
    row_id: str, stage: StageData, facts: Mapping[str, Any], clean: Callable[[str], str], label: str
) -> bytes:
    """The short trace: one bullet per call, a footer of counts, the usage line and the final reply.

    clean is the sanitizer's text function; the shortened pieces are cut after cleaning, so a cut never leaves
    half of a sensitive value behind.
    """
    events = stage.events or []
    union = pc_stream.denial_report(events).union if events else frozenset()
    results = _results_by_id(events)
    lines = ["# %s: %s" % (row_id, label), ""]
    edits: List[str] = []
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        argument = _call_argument(name, tool_input)
        lines.append("- %s: `%s`" % (name, _shorten(argument, clean)))
        if name in pc_checks.WRITE_TOOLS:
            edits.append(clean(argument))
        is_error, result = results.get(tool_id, (False, ""))
        if is_error or tool_id in union:
            lines.append("    result: `%s`" % _shorten(result, clean))
    helper = facts.get("helper_calls", {})
    named = helper.get(stage.name, {}).get("attempted") if isinstance(helper, dict) else None
    turns = _record_int(stage, "turns")
    lines.append("")
    lines.append(
        "Turns %s. Write/Edit calls %d: %r. Bash calls naming the configured executable: %s. "
        "Results flagged as refusal/denial (structured signals; the full trace is authoritative): %d."
        % (UNCONFIRMED if turns is None else turns, len(edits), edits, UNCONFIRMED if named is None else named, len(union))
    )
    usage = stage.record.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    lines.append("Usage: " + ", ".join("%s %s" % (label_, _text(usage.get(key))) for key, label_ in USAGE_KEYS) + ".")
    lines.append("")
    lines.append("## Final reply")
    lines.append("")
    lines.append(_result_text(stage))
    return ("\n".join(lines) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------------
# Mechanical checks and the checklist
# ---------------------------------------------------------------------------------------------


def _section(title: str, lines: Sequence[str]) -> List[str]:
    return ["## " + title] + list(lines) + [""]


def _init_lines(stage: StageData) -> List[str]:
    if stage.events is None:
        return ["%s init: %s" % (stage.name, UNCONFIRMED)]
    init = pc_stream.init_manifest(stage.events)

    def names(value: Any, key: Optional[str] = None) -> str:
        if not isinstance(value, list):
            return UNCONFIRMED
        found = []
        for item in value:
            if isinstance(item, dict) and key is not None:
                found.append(str(item.get(key)))
            else:
                found.append(str(item))
        return ", ".join(found) if found else "none"

    tools = init.get("tools")
    mcp = init.get("mcp_servers")
    prefix = stage.name
    return [
        "%s model: %s" % (prefix, _text(init.get("model"))),
        "%s claude-code-version: %s" % (prefix, _text(init.get("claude_code_version"))),
        "%s permission-mode: %s" % (prefix, _text(init.get("permissionMode"))),
        "%s tool-count: %s" % (prefix, len(tools) if isinstance(tools, list) else UNCONFIRMED),
        "%s tools: %s" % (prefix, names(tools)),
        "%s mcp-server-count: %s" % (prefix, len(mcp) if isinstance(mcp, list) else UNCONFIRMED),
        "%s skills: %s" % (prefix, names(init.get("skills"))),
        "%s plugins: %s" % (prefix, names(init.get("plugins"), "name")),
        "%s agents: %s" % (prefix, names(init.get("agents"))),
        "%s slash-commands: %s" % (prefix, names(init.get("slash_commands"))),
        "%s api-key-source: %s" % (prefix, _text(init.get("apiKeySource"))),
    ]


def _assertion_triples(stage: StageData) -> Optional[List[Tuple[str, str, bool]]]:
    raw = stage.record.get("assertions")
    if not isinstance(raw, list):
        return None
    found = []
    for item in raw:
        if isinstance(item, list) and len(item) == 3 and isinstance(item[0], str) and isinstance(item[1], str):
            found.append((item[0], item[1], item[2] is True))
    return found


def _sum_helper(facts: Mapping[str, Any]) -> Dict[str, int]:
    totals = {"attempted": 0, "executed": 0, "denied": 0, "compound_refusals": 0}
    helper = facts.get("helper_calls", {})
    for counts in helper.values() if isinstance(helper, dict) else []:
        for key in totals:
            value = counts.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                totals[key] += value
    return totals


def render_mechanical_checks(
    data: RunData, facts: Mapping[str, Any], spec: Optional[pc_rows.RowSpec] = None
) -> bytes:
    """mechanical-checks.md: ten sections of `name: value` lines, yes and no for booleans, no reply text."""
    row = spec if spec is not None else _spec_of_run(data)
    out: List[str] = ["# Mechanical checks for %s" % row.row_id, ""]
    init_lines: List[str] = []
    for stage in data.stages:
        init_lines.extend(_init_lines(stage))
    out.extend(_section(SECTION_NAMES[0], init_lines or ["init: " + UNCONFIRMED]))

    audit: List[str] = []
    for stage in data.stages:
        record = stage.record
        entries = record.get("hook_entries")
        if isinstance(entries, dict):
            counts = " ".join("%s=%s" % (kind, entries.get(kind)) for kind in ("user", "project", "local", "managed", "unknown"))
        else:
            counts = UNCONFIRMED
        triples = _assertion_triples(stage)
        holds = UNCONFIRMED if triples is None else _yes_no(all(ok for _name, _how, ok in triples))
        audit.append("%s audit-source: %s" % (stage.name, _text(record.get("audit_source"))))
        audit.append("%s instruction-entries: %s" % (stage.name, counts))
        audit.append("%s isolation-assertions-all-hold: %s" % (stage.name, holds))
    out.extend(_section(SECTION_NAMES[1], audit or ["audit: " + UNCONFIRMED]))

    assertions: List[str] = []
    for stage in data.stages:
        triples = _assertion_triples(stage)
        if triples is None:
            assertions.append("%s assertions: %s" % (stage.name, UNCONFIRMED))
            continue
        for name, how, ok in triples:
            assertions.append("%s %s: %s (%s)" % (stage.name, name, _yes_no(ok), how))
    out.extend(_section(SECTION_NAMES[2], assertions or ["assertions: " + UNCONFIRMED]))

    boundary = facts["write_boundary"]
    trace = facts["trace_writes"]
    mentions = facts["bash_mentions"]
    programs = mentions.get("write_programs", {})
    program_text = ", ".join("%s=%s" % (k, programs[k]) for k in sorted(programs)) if programs else "none"
    out.extend(
        _section(
            SECTION_NAMES[3],
            [
                "snapshot-paths-outside-approved-roots: %d" % boundary["count"],
                "snapshot-paths: %s" % (", ".join(boundary["paths"]) if boundary["paths"] else "none"),
                "write-tool-paths-outside-approved-roots: %d" % trace["count"],
                "write-tool-paths: %s" % (", ".join(trace["paths"]) if trace["paths"] else "none"),
                "bash-commands-seen: %d" % mentions["commands"],
                "bash-outside-path-tokens: %d" % mentions["outside_path_tokens"],
                "bash-unparsed-parts: %d" % mentions["unparsed_parts"],
                "bash-write-programs: %s" % program_text,
                "bash-write-escapes: %d" % mentions["write_escapes"]["count"],
                "run-record-changes: %d" % facts["guard"]["count"],
                "default-memory-folder: %s" % facts["memory_probe"],
            ]
            + memory_fact_lines(data, facts)
            + program_count_lines(row, facts),
        )
    )

    states = facts["git"]["states"]
    mutations = facts["git"]["mutations"]
    names = list(facts["boundaries"]) if "boundaries" in facts else [pc_checks.SETUP_STATE] + [name for name in facts["stages"]]
    git_lines = ["states: %d" % len(states)]
    for name, state in zip(names, states):
        git_lines.append(
            "state %s: head %s, branch %s, staged %s"
            % (name, _text(state.get("head")), _text(state.get("branch")), state.get("staged"))
        )
    git_lines.extend(
        [
            "mutations-total: %d" % mutations["total"],
            "mutation-state-changes: %d" % mutations["state_changes"],
            "mutation-changed-fields: %s" % (", ".join(mutations["changed_fields"]) or "none"),
            "mutation-staged-entries: %d" % mutations["staged"],
            "mutation-executed-forms: %d" % mutations["executed"],
        ]
    )
    out.extend(_section(SECTION_NAMES[4], git_lines))

    helper_lines: List[str] = []
    helper = facts["helper_calls"]
    for name in sorted(helper):
        counts = helper[name]
        helper_lines.extend(
            [
                "%s attempted: %d" % (name, counts["attempted"]),
                "%s executed: %d" % (name, counts["executed"]),
                "%s denied: %d" % (name, counts["denied"]),
                "%s compound-refusals: %d" % (name, counts["compound_refusals"]),
                "%s correlated: %s" % (name, counts["correlated"]),
            ]
        )
    out.extend(_section(SECTION_NAMES[5], helper_lines or ["helper-calls: " + UNCONFIRMED]))

    ledgers = facts["ledgers"]
    ledger_lines = ["%s: %s" % (name, status) for name, status in ledgers["names"].items()]
    ledger_lines.append("ledgers-unchanged: %s" % _yes_no(bool(ledgers["unchanged"])))
    out.extend(_section(SECTION_NAMES[6], ledger_lines))

    session = facts["session"]
    session_lines: List[str] = []
    for name in sorted(session["stages"]):
        stage_facts = session["stages"][name]
        session_lines.append("%s init-session-as-requested: %s" % (name, _yes_no(stage_facts["init_session_as_requested"])))
        session_lines.append("%s result-session-as-requested: %s" % (name, _yes_no(stage_facts["result_session_as_requested"])))
    for key in pc_checks.STATUS_FIRST_KEYS + (pc_checks.status_ledger_key(session),):
        session_lines.append("%s: %s" % (key.replace("_", "-"), session[key]))
    ids = ", ".join("%s %s" % (stage.name, _text(stage.record.get("session_id"))) for stage in data.stages)
    session_lines.append("session-ids: %s" % (ids or UNCONFIRMED))
    first = _stage(data, "s1")
    third = _stage(data, "s3")
    if first is not None and third is not None:
        differs = first.record.get("session_id") != third.record.get("session_id")
        session_lines.append("s3-session-differs-from-s1: %s" % _yes_no(differs))
    out.extend(_section(SECTION_NAMES[7], session_lines))

    denial_lines: List[str] = []
    for name in sorted(facts["denials"]):
        ids_ = facts["denials"][name]
        denial_lines.append("%s denial-ids: %d%s" % (name, len(ids_), " (" + ", ".join(ids_) + ")" if ids_ else ""))
    out.extend(_section(SECTION_NAMES[8], denial_lines or ["denial-ids: " + UNCONFIRMED]))

    _path, measurement = measure_checkpoint(data)
    if measurement is None:
        checkpoint_lines = ["checkpoint-total-bytes: " + UNCONFIRMED]
    else:
        total = measurement["total"]
        checkpoint_lines = [
            "checkpoint-total-bytes: %d" % total,
            "checkpoint-file-cap: %d" % pc_measure.FILE_CAP,
            "checkpoint-over-cap-by: %d" % max(0, total - pc_measure.FILE_CAP),
        ]
        for name, size, cap in measurement["rows"]:
            checkpoint_lines.append("section %s: %d/%s" % (name, size, cap if cap is not None else "no cap"))
        if measurement["missing"]:
            checkpoint_lines.append("sections-missing: %s" % ", ".join(measurement["missing"]))
    out.extend(_section(SECTION_NAMES[9], checkpoint_lines))
    return ("\n".join(out).rstrip("\n") + "\n").encode("utf-8")


def checklist_lines(data: RunData, facts: Mapping[str, Any], spec: Optional[pc_rows.RowSpec] = None) -> List[str]:
    """The reviewer checklist: one blank-box line per mechanical fact in the D-09 order, each with its source."""
    row = spec if spec is not None else _spec_of_run(data)
    helper = _sum_helper(facts)
    snapshots = facts["snapshots"]
    last = snapshots[-1] if snapshots else UNCONFIRMED
    boundary = facts["write_boundary"]["count"]
    trace = facts["trace_writes"]["count"]
    memory = facts["memory_probe"]
    escapes = facts["bash_mentions"]["write_escapes"]["count"]
    writes = boundary + trace + escapes + (1 if memory == "present" else 0)
    mutations = facts["git"]["mutations"]
    _path, measurement = measure_checkpoint(data)
    if measurement is None:
        bytes_text = UNCONFIRMED
    else:
        bytes_text = "%d/%d" % (measurement["total"], pc_measure.FILE_CAP)
    ids = ", ".join("%s %s" % (stage.name, _text(stage.record.get("session_id"))) for stage in data.stages)
    costs = ", ".join(
        "%s cost %s and %s turns" % (stage.name, _text(stage.record.get("delta")), _text(stage.record.get("turns")))
        for stage in data.stages
    )
    traces = ", ".join("%s-full-trace.md" % stage_label(row, stage.name) for stage in data.stages)
    lines = [
        "- [ ] helper calls (all stages): attempted %d, executed %d, denied %d, compound refusals %d "
        "(source: %s%s)"
        % (
            helper["attempted"],
            helper["executed"],
            helper["denied"],
            helper["compound_refusals"],
            "wrapper-calls.log, " if _has_wrapper(row) else "",
            traces,
        ),
        "- [ ] ledger digests unchanged, setup to %s: %s (source: snap-0-setup/sha.txt, %s/sha.txt)"
        % (last, _yes_no(bool(facts["ledgers"]["unchanged"])), last),
        "- [ ] writes outside approved roots: %d; snapshot paths %d, tool paths %d, Bash writes %d, "
        "default memory folder %s (source: the sha.txt of each snapshot, mechanical-checks.md, %s)"
        % (writes, boundary, trace, escapes, memory, traces),
        "- [ ] git mutations: %d; state changes %d, staged entries %d, executed forms %d "
        "(source: status.txt of each snapshot, mechanical-checks.md)"
        % (mutations["total"], mutations["state_changes"], mutations["staged"], mutations["executed"]),
        "- [ ] checkpoint bytes versus cap: %s (source: measurements.txt)" % bytes_text,
        "- [ ] session ids per stage: %s (source: session.id, session-resume.id, usage.txt)" % (ids or UNCONFIRMED),
        "- [ ] cost and turns per stage: %s (source: usage.txt)" % (costs or UNCONFIRMED),
    ]
    if pc_rows.ANALYSIS_STATUS_FORM in row.analyses:
        lines.append(_status_form_checklist_line(data, row))
    return lines


def _status_form_checklist_line(data: RunData, row: pc_rows.RowSpec) -> str:
    """The row 10 checklist line: the expected outcome in the plan's words with the status-form counts beside it.

    The counts are read from the /preclear stream and the filed sidecar copy (pc_review.status_form_counts), never
    from the reply; the line states what was expected and prints facts, and the reviewer ticks it.
    """
    import pc_review  # imported late: pc_review imports this module

    head = "- [ ] expected outcome, quoted-porcelain fallback and NUL redirect refused: "
    tail = " (source: mechanical-checks.md Row 10 status form, the /preclear full trace, snap-2-after-preclear/preclear)"
    stage = next((item for item in data.stages if _stage_kind(row, item.name) == "preclear"), None)
    if stage is None or stage.events is None:
        return head + UNCONFIRMED + tail
    snapshot = os.path.join(str(data.paths["snaps"]), _row1().SNAPSHOT_NAMES.get(stage.name, "snap-2-after-preclear"))
    try:
        counts = pc_review.status_form_counts(stage.events, snapshot)
    except pc_review.ReviewError:
        return head + UNCONFIRMED + tail
    sidecar = counts["sidecar"]
    side = (
        "present, %d bytes, %d NUL bytes" % (sidecar["bytes"], sidecar["nul_bytes"]) if sidecar["present"] else "absent"
    )
    return head + (
        "quoted form executed %d, NUL form executed with a redirection %d, NUL form denied with a redirection %d, "
        "NUL form executed without a redirection %d, sidecar status.txt %s"
        % (
            counts["quoted_executed"],
            counts["nul_redirect_executed"],
            len(counts["nul_redirect_denied_ids"]),
            counts["nul_plain_executed"],
            side,
        )
    ) + tail


def _printed_checkpoint_line(chain: Optional[Mapping[str, Any]]) -> str:
    """The README line that says which shape a printed-checkpoint chain had, in the harness's words (plan 04-06)."""
    record = chain if isinstance(chain, Mapping) else {}
    if record.get("marker") == _row1().MARKER_FOUND:
        size = record.get("checkpoint_bytes")
        return (
            "- chain shape: the /preclear reply printed a checkpoint (%s bytes) and a fresh session was started from it"
            % (size if isinstance(size, int) and not isinstance(size, bool) else UNCONFIRMED)
        )
    return (
        "- chain shape: the /preclear reply printed no checkpoint the harness could take (%s: reason %s); "
        "no fresh session was run"
        % (_row1().MARKER_NO_CHECKPOINT, _text(record.get("checkpoint_reason")))
    )


def render_row_readme(data: RunData, facts: Mapping[str, Any], spec: Optional[pc_rows.RowSpec] = None) -> bytes:
    """The row README: setup, stage table, mechanical facts, then the checklist, then the one verdict line.

    The heading is the entry's title and the Setup paragraph is the entry's setup text (left out when it is empty).
    """
    row = spec if spec is not None else _spec_of_run(data)
    lines = ["# %s, rerun on the pinned model and build" % row.title, ""]
    if row.setup_text:
        lines.extend([row.setup_text, ""])
    lines.extend(["## Stages", "", "| Stage | Session | Exit | Turns | Subtype |", "| --- | --- | --- | --- | --- |"])
    for stage in data.stages:
        record = stage.record
        lines.append(
            "| %s | %s | %s | %s | %s |"
            % (
                stage.name,
                _text(record.get("session_id")),
                _text(record.get("returncode")),
                _text(record.get("turns")),
                _text(record.get("subtype")),
            )
        )
    lines.extend(["", "## Mechanical facts", ""])
    helper = facts["helper_calls"]
    for name in sorted(helper):
        counts = helper[name]
        lines.append(
            "- helper calls in %s: attempted %d, executed %d, denied %d, compound refusals %d"
            % (name, counts["attempted"], counts["executed"], counts["denied"], counts["compound_refusals"])
        )
    lines.append("- ledger digests: %s" % ", ".join("%s %s" % (k, v) for k, v in facts["ledgers"]["names"].items()))
    if row.chain == pc_rows.CHAIN_PRINTED_CHECKPOINT:
        lines.append(_printed_checkpoint_line(data.chain))
    if pc_rows.ANALYSIS_DO_NOT_REDO in row.analyses:
        lines.append(REVIEW_POINTER_LINE)
    lines.append("- the full list of facts is in mechanical-checks.md and usage.txt")
    lines.extend(["", "## Reviewer checklist", ""])
    lines.extend(checklist_lines(data, facts, row))
    lines.append(VERDICT_LINE)
    return _lines(lines)


def render_folder_readme(ctx: pc_rows.RunContext, data: RunData) -> bytes:
    """The folder-level README: the run is a new baseline, with its totals and how it differs from 2026-10-20."""
    row_total, run_total = usage_totals(data.stages)
    version = UNCONFIRMED
    for stage in data.stages:
        if isinstance(stage.record.get("version"), str) and stage.record["version"]:
            version = stage.record["version"]
            break
    lines = [
        "# Rerun %s on %s" % (ctx.evidence_date, ctx.model),
        "",
        "This folder is a new baseline on the pinned model and build (model %s, Claude Code %s). It is not a "
        "replication of the 2026-10-20 run: that run recorded no model, so the model cannot be matched." % (ctx.model, version),
        "",
        "Row total: %s. Run total: %s. Both are quoted from `%s/usage.txt`." % (row_total, run_total, pc_rows.ROW1),
        "",
        "Differences from the 2026-10-20 run:",
        "",
        "- Claude Code %s against %s" % (version, pc_flags.COMMITTED_EVIDENCE_VERSION),
        "- the pinned flag set",
        "- the stub in place of the real helper",
        "- per-verb allowlist",
        "- run roots outside the home folder",
        "- strict isolation",
        "",
        "The committed folder stays the reference: `tests/evidence/publication-2026-10-20`. Every file written by "
        "the harness holds facts, counts and ids; each row README ends with a checklist for the reviewer.",
    ]
    return _lines(lines)


# ---------------------------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------------------------

_DROPPED_FROM_LISTING = ("wrapper/py", "wrapper/stub")


def _rebuilt_listings(snapshot_dir: str) -> Dict[str, bytes]:
    """sha.txt and manifest.jsonl rebuilt from the stored manifest without the helper path files."""
    stored = _read_bytes(os.path.join(snapshot_dir, "manifest.jsonl")).decode("utf-8")
    entries: List[Dict[str, Any]] = []
    for line in stored.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except ValueError:
            raise EvidenceError("a snapshot manifest line is not valid JSON") from None
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise EvidenceError("a snapshot manifest line has an unexpected shape")
        if item["path"] in _DROPPED_FROM_LISTING:
            continue
        target = item.get("target")
        entries.append(
            {
                "path": os.fsencode(item["path"]),
                "kind": item.get("kind"),
                "size": item.get("size"),
                "sha256": item.get("sha256"),
                "target": os.fsencode(target) if isinstance(target, str) else None,
            }
        )
    entries.sort(key=lambda entry: entry["path"])
    return {"sha.txt": pc_manifest.sha_txt_bytes(entries), "manifest.jsonl": pc_manifest.jsonl_bytes(entries)}


def filed_snapshot_files(snapshot_dir: str) -> Dict[str, bytes]:
    """The files of one snapshot folder as relative path to bytes.

    sha.txt and manifest.jsonl are rebuilt from the stored manifest without the helper path files (they hold the
    interpreter and stub paths). Never the NUL status capture; ledger copies and the preclear and auto-memory
    trees are carried as they are.
    """
    found: Dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(snapshot_dir):
        dirnames[:] = sorted(dirnames)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            relative = os.path.relpath(full, snapshot_dir).replace(os.sep, "/")
            if relative == "status.raw" or os.path.islink(full) or not os.path.isfile(full):
                continue
            found[relative] = _read_bytes(full)
    if os.path.isfile(os.path.join(snapshot_dir, "manifest.jsonl")):
        found.update(_rebuilt_listings(snapshot_dir))
    return found


# ---------------------------------------------------------------------------------------------
# Staging
# ---------------------------------------------------------------------------------------------


def new_stage_dir(run_root: str) -> str:
    """Create the first free stage-N folder inside the run root exclusively and return its path."""
    number = 1
    while True:
        path = os.path.join(run_root, "stage-%d" % number)
        try:
            pc_runroot.exclusive_dir(path, _STAGE_DIR_MODE)
        except FileExistsError:
            number += 1
            continue
        return path


def stage_tree(stage_dir: str, files: Mapping[str, bytes], sanitizer: Any) -> int:
    """Sanitize every file, then create the staged tree exclusively in sorted path order; return the file count.

    Every file is sanitized before anything is written, so a sanitizer error leaves the stage folder empty.
    SanitizerError propagates. Nothing is overwritten: a path that already exists is FileExistsError.
    """
    cleaned: List[Tuple[str, bytes]] = []
    for relative in sorted(files, key=lambda item: item.encode("utf-8")):
        cleaned.append((relative, sanitizer.sanitize_bytes(pc_spike.scrub_volatile(bytes(files[relative])))))
    made = set()
    for relative, data in cleaned:
        parts = relative.split("/")
        folder = stage_dir
        for part in parts[:-1]:
            folder = os.path.join(folder, part)
            if folder not in made:
                pc_runroot.exclusive_dir(folder, _STAGE_DIR_MODE)
                made.add(folder)
        pc_runroot.write_exclusive(os.path.join(folder, parts[-1]), data, _FILE_MODE)
    return len(cleaned)


def _unfileable(data: RunData, spec: Optional[pc_rows.RowSpec] = None) -> Optional[str]:
    """The fixed line that refuses the filing, or None when the run may be filed.

    Order: no stages, then each stage's prompt, stream and cleanliness, then the chain. Filing needs the chain the
    registry defines (s1 and s2, and s3 exactly when s2 printed a resume line), because the live path files only
    after s2 and runs s3 only then; a refile is held to the same rule.
    """
    if not data.stages:
        return MESSAGE_UNREADABLE
    for stage in data.stages:
        if stage.prompt is None:
            return MESSAGE_NO_PROMPT
        if stage.events is None:
            return MESSAGE_NO_STREAM
        # The live path goes on only when the call is ok (an empty problem) and the isolation evaluation is
        # pass; a record that lacks either key is not clean (fail closed), so a refile cannot file a run the
        # live path refused (CR-01).
        if stage.record.get("problem") != "" or stage.record.get("evaluation") != _row1().STATUS_PASS:
            return MESSAGE_STAGE_NOT_CLEAN
    return _chain_incomplete(data, spec)


def _chain_incomplete(data: RunData, spec: Optional[pc_rows.RowSpec] = None) -> Optional[str]:
    """MESSAGE_STAGE_MISSING unless the stage records are exactly the chain the registry defines for the row.

    The live path files only after the last /preclear turn has run and runs a resume stage only when that turn
    printed a resume line, so a run that stopped early (a crash, an interrupt, a harness error after a paid call)
    has fewer records and must not be filed or refiled (second-pass CR-01). The chain record names which shape is
    complete: every stage of the entry with the marker found, or with the marker none every stage before the
    first stage of kind resume (that stage and every stage after it are dropped). A spec with no stage of kind resume
    therefore has one complete shape, whatever the marker. The stage names come from the registry entry the runner walks,
    not from a second list.
    """
    row1 = _row1()
    marker = data.chain.get("marker") if isinstance(data.chain, dict) else None
    entry = spec if spec is not None else _spec_of_run_or_none(data)
    if entry is None:
        return MESSAGE_STAGE_MISSING
    # The marker word of the none shape belongs to the row's chain strategy: a row that feeds its resume stage with a
    # printed checkpoint (plan 04-06) has NO-PRINTED-CHECKPOINT and refuses NO-RESUME-LINE, and every other row the
    # reverse. Anything else is not a shape the registry defines.
    none_marker = (
        row1.MARKER_NO_CHECKPOINT if entry.chain == pc_rows.CHAIN_PRINTED_CHECKPOINT else row1.MARKER_NONE
    )
    if marker not in (row1.MARKER_FOUND, none_marker):
        return MESSAGE_STAGE_MISSING
    if marker == row1.MARKER_FOUND:
        expected = [stage.name for stage in entry.stages]
    else:
        # No resume line: the chain ends before the first stage of kind resume, and so does every stage after it (row 12's
        # s4 resumes the session of that resume stage, so it never runs either).
        expected = []
        for stage in entry.stages:
            if stage.kind == "resume":
                break
            expected.append(stage.name)
    if [stage.name for stage in data.stages] != expected:
        return MESSAGE_STAGE_MISSING
    return None


def _spec_of_run_or_none(data: RunData) -> Optional[pc_rows.RowSpec]:
    try:
        return _spec_of_run(data)
    except EvidenceError:
        return None


_AUTHORED_ROW_FILES = frozenset(
    [
        "README.md",
        "claude-version.txt",
        "digests.txt",
        "tools.txt",
        "measurements.md",
        "measurements.txt",
        "mechanical-checks.md",
        "usage.txt",
        "model-id.txt",
        "isolation-mode.txt",
        "harness-version.txt",
        "session.id",
        "session-resume.id",
        "do-not-redo-candidates.md",
    ]
)
_AUTHORED_LISTINGS = frozenset(["ledgers-ls.txt", "bindings-ls.txt", "perms.txt"])
_AUTHORED_LABEL_FILES = frozenset(["README.md", "stop.txt", "usage.txt", "mechanical-checks.md"])
_AUTHORED_TOP = re.compile(
    r"(?:README\.md|digest-table(?:-part-[0-9]+)?\.md|usage-by-row(?:-part-[0-9]+)?\.txt|row7-review(?:-part-[0-9]+)?\.md)\Z"
)
# The files that hold quoted model text: a line that starts with the quote marker is model text and is skipped by the
# vocabulary scan; every other line of these files is scanned like any harness-authored line (plan 04-07).
QUOTED_TEXT_FILE = re.compile(r"(?:do-not-redo-candidates\.md|row7-review(?:-part-[0-9]+)?\.md)\Z")
QUOTE_MARKER = "> "
_ATTEMPT_SUFFIX = re.compile(r"(.+)-attempt-[2-9]\Z")


def _folder_kind(part: str, ids: frozenset) -> Optional[str]:
    """`row` for a row folder (its id, or its id and -attempt-N), `label` for STOPPED-/SKIPPED- of one, else None."""
    kind = "row"
    base = part
    for prefix in (STOPPED_PREFIX, SKIPPED_PREFIX):
        if part.startswith(prefix):
            kind, base = "label", part[len(prefix):]
            break
    attempt = _ATTEMPT_SUFFIX.match(base)
    if attempt is not None:
        base = attempt.group(1)
    return kind if base in ids else None


def harness_authored_names(names: Iterable[str]) -> List[str]:
    """Pick the names (relative to the evidence folder, forward slashes) of files the harness wrote in its own words.

    Traces, replies, prompts, ledger and memory copies and stderr come from the model or the process and are not
    in the set. The verdict-word scan covers exactly these files: the top-level files the harness writes (README,
    the digest and usage tables and their part files), the harness-written files of a row folder (any registered
    row id, with or without -attempt-N) and of a STOPPED or SKIPPED label folder.
    """
    ids = frozenset(entry.row_id for entry in pc_rows.build_registry())
    picked: List[str] = []
    for name in names:
        parts = name.split("/")
        base = parts[-1]
        if len(parts) == 1 and _AUTHORED_TOP.match(name):
            picked.append(name)
        elif len(parts) == 2:
            kind = _folder_kind(parts[0], ids)
            if kind == "row" and (base in _AUTHORED_ROW_FILES or base.endswith(".exit")):
                picked.append(name)
            elif kind == "label" and (base in _AUTHORED_LABEL_FILES or base.endswith(".exit")):
                picked.append(name)
        elif len(parts) == 3 and _folder_kind(parts[0], ids) == "row" and parts[1].startswith("snap-") and base in _AUTHORED_LISTINGS:
            picked.append(name)
    return sorted(picked)


def stage_files(
    row: pc_rows.RowSpec, data: RunData, facts: Mapping[str, Any], clean: Callable[[str], str], filed_row: bool
) -> Dict[str, bytes]:
    """The per-stage files of every stage that has a record, keyed by their name inside the folder.

    A filed row (filed_row true) gets all of them: exit, error, the work turn's reply, the prompts, the traces
    and the session ids. A stopped row's folder (filed_row false) holds the prompt, exit, error and trace files
    only: no reply file and no session id. A trace is written only for a stage whose stream is readable.
    """
    files: Dict[str, bytes] = {}
    for stage in data.stages:
        label = stage_label(row, stage.name)
        kind = _stage_kind(row, stage.name)
        record = stage.record
        code = record.get("returncode")
        base = exit_label(row, stage.name)
        prompt_name = prompt_label(row, stage.name)
        files["%s.exit" % base] = _lines(
            ["exit %s" % (code if isinstance(code, int) and not isinstance(code, bool) else UNCONFIRMED)]
        )
        files["%s.err" % base] = stage.stderr
        readable = stage.events is not None
        if kind == "work":
            if filed_row:
                files["%s.out" % label] = _lines([_result_text(stage)])
            if stage.prompt is not None or filed_row:
                files["%s-prompt.md" % label] = (stage.prompt or "").encode("utf-8")
            if readable or filed_row:
                files["%s-full-trace.md" % label] = render_full_trace(row.row_id, stage, label)
            if filed_row:
                files["session.id"] = _lines([_text(record.get("session_id"))])
        elif kind == "preclear":
            if stage.prompt is not None or filed_row:
                files["%s-prompt.md" % prompt_name] = (stage.prompt or "").encode("utf-8")
            if readable or filed_row:
                files["%s-trace.md" % label] = render_short_trace(row.row_id, stage, facts, clean, label)
                files["%s-full-trace.md" % label] = render_full_trace(row.row_id, stage, label)
        else:
            if readable or filed_row:
                files["%s-trace.md" % label] = render_short_trace(row.row_id, stage, facts, clean, label)
                files["%s-full-trace.md" % label] = render_full_trace(row.row_id, stage, label)
            if filed_row:
                files["session-resume.id"] = _lines([_text(record.get("session_id"))])
    return files


def _run_analyses(
    row: pc_rows.RowSpec, data: RunData, facts: Mapping[str, Any], clean: Callable[[str], str], mechanical: bytes
) -> Tuple[bytes, Dict[str, bytes]]:
    """Run each analysis the entry names (pc_review.ANALYSES); return mechanical-checks.md with its sections and the extra files.

    An analysis returns a section title, the section's lines (both empty for no section) and flat files for the row
    folder. An id that pc_review does not know raises EvidenceError, so a misspelt registry entry files nothing.
    """
    import pc_review  # imported late: pc_review imports this module

    text = mechanical.decode("utf-8")
    files: Dict[str, bytes] = {}
    for identifier in row.analyses:
        function = pc_review.ANALYSES.get(identifier)
        if function is None:
            raise EvidenceError("the row names an analysis that does not exist")
        try:
            title, lines, extra = function(row, data, facts, clean)
        except pc_review.ReviewError:
            raise EvidenceError("an analysis could not read the run") from None
        if title:
            text = text.rstrip("\n") + "\n\n" + "\n".join(_section(title, lines)).rstrip("\n") + "\n"
        for name, content in extra.items():
            if name in files:
                raise EvidenceError("two analyses file the same name")
            files[name] = content
    return text.encode("utf-8"), files


def collect_files(
    ctx: pc_rows.RunContext, data: RunData, facts: Mapping[str, Any], spec: Optional[pc_rows.RowSpec] = None
) -> Dict[str, bytes]:
    """Every file to stage, keyed by its path relative to the stage folder.

    The staged tree holds only the row folder, named by the entry's id; the stage file labels, the Setup paragraph
    and the allowlist come from the entry (the one the run record names when none is passed).
    """
    row = spec if spec is not None else _spec_of_run(data)
    folder = row.row_id
    clean: Callable[[str], str] = ctx.sanitizer.sanitize_text
    paths = data.paths
    files: Dict[str, bytes] = {}

    def put(name: str, content: bytes) -> None:
        files[folder + "/" + name] = content

    put("README.md", render_row_readme(data, facts, row))
    put("claude-version.txt", render_claude_version(data))
    put("model-id.txt", render_model_id(data))
    put("isolation-mode.txt", render_isolation_mode(data))
    put("harness-version.txt", render_harness_version(ctx))
    put("digests.txt", render_digests(ctx, data, row))
    put("tools.txt", render_tools(data, row))
    put("settings.json", render_settings_json(data))
    put("usage.txt", render_usage(data, row))
    mechanical = render_mechanical_checks(data, facts, row)
    extra_files: Dict[str, bytes] = {}
    if row.analyses and _chain_incomplete(data, row) is None:
        mechanical, extra_files = _run_analyses(row, data, facts, clean, mechanical)
    put("mechanical-checks.md", mechanical)
    for extra_name, extra_content in extra_files.items():
        put(extra_name, extra_content)
    measurements_txt, measurements_md = render_measurements(data)
    put("measurements.txt", measurements_txt)
    put("measurements.md", measurements_md)

    claude_md = os.path.join(str(paths["project"]), "CLAUDE.md")
    put("fixture-CLAUDE.md", _read_bytes(claude_md) if os.path.isfile(claude_md) else _lines([UNCONFIRMED]))
    helper_files = (
        (os.path.join(str(paths["raw"]), "status-before.txt"), "status-before.txt"),
        (os.path.join(str(paths["raw"]), "lint-before.txt"), "lint-before.txt"),
        (os.path.join(str(paths["wrapper_dir"]), "calls.log"), "wrapper-calls.log"),
        (str(paths["wrapper"]), "wrapper-checkpoint.sh"),
    )
    # A row with no wrapper has no helper state to file: the four files are left out, not filed as UNCONFIRMED.
    for source, target in helper_files if _has_wrapper(row) else ():
        put(target, _read_bytes(source) if os.path.isfile(source) else _lines([UNCONFIRMED]))

    for name, content in stage_files(row, data, facts, clean, filed_row=True).items():
        put(name, content)
    chain = data.chain or {}
    line = chain.get("resume_line")
    if isinstance(line, str) and line:
        resume = line
    elif chain.get("marker") == MARKER_NO_RESUME:
        resume = MARKER_NO_RESUME
    else:
        resume = UNCONFIRMED
    if row.chain != pc_rows.CHAIN_PRINTED_CHECKPOINT:  # a row that saves no file prints no resume line to record
        put("resume-line.txt", _lines([resume]))

    snaps = str(paths["snaps"])
    if os.path.isdir(snaps):
        for name in sorted(os.listdir(snaps)):
            snapshot = os.path.join(snaps, name)
            if os.path.isdir(snapshot) and not os.path.islink(snapshot):
                for relative, content in filed_snapshot_files(snapshot).items():
                    put("%s/%s" % (name, relative), content)
    return files


def _outcome(result: Any, destination: str, count: int, row_folder: Optional[str] = None) -> pc_rows.RowOutcome:
    code = int(result.code)
    if code == pc_exitcodes.OK:
        if row_folder is None:
            line = "filed: %s, %d file(s)" % (os.path.basename(destination), count)
        else:
            line = "filed: %s %s, %d file(s)" % (os.path.basename(destination), row_folder, count)
        return pc_rows.RowOutcome(pc_exitcodes.OK, (line,))
    lines = [str(result.message)]
    for line in str(result.report_text).splitlines():
        if line.strip():
            lines.append(line)
    return pc_rows.RowOutcome(code, tuple(lines))


def file_row(
    ctx: pc_rows.RunContext,
    run_root: str,
    facts: Optional[Mapping[str, Any]] = None,
    spec: Optional[pc_rows.RowSpec] = None,
) -> pc_rows.RowOutcome:
    """Stage, sanitize, gate and promote the finished run in run_root into the evidence folder.

    The staged tree holds only the row folder and it is promoted to ctx.destination joined with the row's folder
    name (its id, or its id and -attempt-N for an attempt above 1, plan 04-02): the dated folder may already exist
    and hold other rows, a row folder that exists is refused with 17. The row is
    the one the run record names, matched exactly against the registry; an entry passed as spec must be that
    same row, or nothing is filed.

    The sanitizer and the deny entries are the ones the row built before spend (ctx.sanitizer, ctx.deny_entries);
    promote is always called with both the deny entries and the config folder (review WR-14), and a context
    without the deny entries is refused with 15 before anything is read or made (WR-03). A breach found by the
    checks, or a stage that did not finish cleanly (a problem or a failed isolation assertion in its record),
    files nothing (exit 11), and so does a chain that stopped early (_unfileable); a sanitizer error is 15, a gate
    refusal 14, a taken row folder 17.
    """
    if ctx.deny_entries is None:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_NO_DENY_ENTRIES,))
    try:
        data = load_stage_data(run_root)
        entry = _spec_of_run(data)
        if spec is not None and spec.row_id != entry.row_id:
            raise EvidenceError("the run record names another row")
        found = dict(facts) if facts is not None else pc_checks.compute_facts(run_root, ctx.config_dir)
    except (EvidenceError, pc_checks.CheckError):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_UNREADABLE,))
    if pc_checks.breaches(found):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_BREACH,))
    problem = _unfileable(data, entry)
    if problem is not None:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (problem,))
    try:
        files = collect_files(ctx, data, found, entry)
    except (EvidenceError, OSError, KeyError, ValueError):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_UNREADABLE,))
    except pc_sanitize.SanitizerError:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_SANITIZER,))
    try:
        stage = new_stage_dir(os.path.realpath(run_root))
    except OSError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STAGING,))
    try:
        count = stage_tree(stage, files, ctx.sanitizer)
    except pc_sanitize.SanitizerError:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_SANITIZER,))
    except OSError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STAGING,))
    folder = pc_rows.row_folder_name(entry.row_id, ctx.attempt)
    result = pc_promote.promote(
        os.path.join(stage, entry.row_id),
        os.path.join(ctx.destination, folder),
        ctx.repo_root,
        config_dir=ctx.config_dir,
        deny_entries=ctx.deny_entries,
    )
    return _outcome(result, ctx.destination, count, folder)


# ---------------------------------------------------------------------------------------------
# A SKIPPED row (D-10)
# ---------------------------------------------------------------------------------------------

MESSAGE_SKIP_ROW = "FAIL: the skipped row could not be filed; nothing is filed"
MESSAGE_SKIP_COLLISION = "RUNROOT_COLLISION: a run folder already exists; nothing is filed"
SKIPPED_PREFIX = "SKIPPED-"
STOPPED_PREFIX = "STOPPED-"  # the label folder of a stopped row (D-02)


def render_skipped_readme(row_id: str, reason: str) -> bytes:
    """The README of a SKIPPED folder: no session was run, the reason, and the one verdict line last."""
    text = " ".join(str(reason).split()).rstrip(".") or "no reason was given"
    return _lines(
        [
            "# SKIPPED: %s" % row_id,
            "",
            "This row was skipped on this machine: %s. No session was run and no usage was recorded. "
            "This folder is a label for the skip, not a result." % text,
            "",
            VERDICT_LINE,
        ]
    )


def file_skipped(
    repo_root: str,
    destination: str,
    row_id: str,
    reason: str,
    sanitizer: Any,
    deny_entries: Any,
    config_dir: str,
    runs_root: str,
    clock: Callable[[], Any],
    folder_name: Optional[str] = None,
) -> pc_rows.RowOutcome:
    """File <destination>/SKIPPED-<folder name>/README.md for a row whose precondition was not met.

    The folder name is the row's folder name (its id, or its id and -attempt-N for a retry; plan 04-02) and
    defaults to the row id. The README heading and the skipped run root keep the row id.

    The run is never counted as a success: the exit code is 10 (PREFLIGHT_SKIP) when the label is filed, and 14,
    15, 17 or 11 when the sanitizer, the gate, promote or the staging refuse. The reason passes through the same
    sanitizer, gate and promote as any other file, so a reason shaped like a home path is refused with 14.
    Deny entries of None are refused with 15 before anything is made (WR-03).
    """
    if deny_entries is None:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_NO_DENY_ENTRIES,))
    if not pc_rows.is_valid_id(row_id):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_SKIP_ROW,))
    stamp = clock().strftime("%Y%m%dT%H%M%SZ")
    try:
        pc_spike.ensure_runs_root(runs_root)
        run_root = pc_runroot.allocate_run_root(runs_root, "%s-skipped-%s" % (row_id, stamp))
        stage = new_stage_dir(run_root)
        stage_tree(stage, {"README.md": render_skipped_readme(row_id, reason)}, sanitizer)
    except pc_sanitize.SanitizerError:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_SANITIZER,))
    except pc_runroot.RunRootCollision:
        return pc_rows.RowOutcome(pc_exitcodes.RUNROOT_COLLISION, (MESSAGE_SKIP_COLLISION,))
    except (pc_runroot.RunRootError, pc_spike.SpikeError, OSError):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_SKIP_ROW,))
    label = folder_name if folder_name is not None else row_id
    if not pc_rows.is_valid_id(label):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_SKIP_ROW,))
    target = os.path.join(destination, SKIPPED_PREFIX + label)
    result = pc_promote.promote(stage, target, repo_root, config_dir=config_dir, deny_entries=deny_entries)
    if int(result.code) != pc_exitcodes.OK:
        return _outcome(result, target, 0)
    return pc_rows.RowOutcome(
        pc_exitcodes.PREFLIGHT_SKIP,
        ("filed: %s/%s%s, 1 file(s); no session was run" % (os.path.basename(destination), SKIPPED_PREFIX, label),),
    )


# ---------------------------------------------------------------------------------------------
# A STOPPED row (D-02, D-03)
# ---------------------------------------------------------------------------------------------

REASON_TURNS = "turns"
REASON_CAP = "cap"
REASON_TIMEOUT = "timeout"
REASON_STREAM = "stream"
REASON_ISOLATION = "isolation"
REASON_BREACH = "breach"
REASON_EXIT = "exit"
REASON_ERROR = "error"
STOP_REASONS: Tuple[str, ...] = (
    REASON_TURNS,
    REASON_CAP,
    REASON_TIMEOUT,
    REASON_STREAM,
    REASON_ISOLATION,
    REASON_BREACH,
    REASON_EXIT,
    REASON_ERROR,
)
STOP_FILE = "stop.txt"
MESSAGE_STOP_UNREADABLE = "FAIL: the stopped run could not be read for filing; nothing is filed"
MESSAGE_STOP_REASON = "FAIL: the stop reason is not one of the known words; nothing is filed"
MESSAGE_CHECKS_NOT_COMPUTED = "The mechanical checks were not computed: the checks could not read the run root.\n"
_SUBTYPE_TEXT = re.compile(r"[A-Za-z0-9_]{1,64}\Z")
_NO_FACTS: Mapping[str, Any] = {}


def verdict_pattern() -> Any:
    """The whole words no harness-authored file may hold, assembled from fragments at run time (EVID-05).

    The module holds none of them whole: the only place the vocabulary exists is the compiled pattern, so a plain
    search of the harness source for the words finds nothing.
    """
    parts = (
        ("pa", "ss"), ("pa", "ssed"), ("fa", "il"), ("fa", "iled"), ("fa", "ilure"),
        ("acc", "ept"), ("acc", "epted"), ("ver", "dict"),
    )
    return re.compile(r"\b(?:%s)\b" % "|".join("".join(pair) for pair in parts), re.IGNORECASE)


def stop_reason(problem: str, subtype: Any) -> str:
    """The reason word of a stop, from the stage's problem word and the result subtype text.

    isolation and breach are named by the caller and pass through; a timeout and an unreadable stream are what
    they are. A subtype text holding max_turns is turns and one holding max_budget is cap, whatever the exit
    status was (the real limit-hit subtype names on the pinned build are unobserved; the first real stop is
    checked against this reading). A non-zero exit with no such subtype is exit. Anything else (a subtype that is
    neither, an error result, a terminal reason that is not completed) is error, and stop.txt records the
    subtype text.
    """
    word = str(problem)
    if word in (REASON_ISOLATION, REASON_BREACH, REASON_TIMEOUT, REASON_STREAM):
        return word
    text = subtype if isinstance(subtype, str) else ""
    if "max_turns" in text:
        return REASON_TURNS
    if "max_budget" in text:
        return REASON_CAP
    if word == REASON_EXIT:
        return REASON_EXIT
    return REASON_ERROR


def stop_exit_code(reason: str) -> int:
    """The exit code a stop keeps: 19 for an unreadable stream, 11 for every other stop."""
    return pc_exitcodes.DENIAL_FOUND if reason == REASON_STREAM else pc_exitcodes.PREFLIGHT_FAIL


def render_stop(row_id: str, reason: str, stage_name: str) -> bytes:
    """The README of a STOPPED folder: the label, the row, the reason and the stage, then the one verdict line last."""
    return _lines(
        [
            "# STOPPED: %s" % row_id,
            "",
            "Row: %s" % row_id,
            "Reason: %s" % reason,
            "Stage: %s" % stage_name,
            "",
            "This folder is a label for a run that did not finish. It is not a result. stop.txt holds the reason "
            "and the counts, usage.txt the cost of the stages that ran. The raw captures stay in the run root and "
            "are not filed.",
            "",
            VERDICT_LINE,
        ]
    )


def _subtype_text(data: RunData, stage_name: str) -> str:
    """The result subtype of a stage as plain text, UNCONFIRMED when absent, odd-shaped or a verdict word."""
    stage = _stage(data, stage_name)
    value = stage.record.get("subtype") if stage is not None else None
    if not isinstance(value, str) or not _SUBTYPE_TEXT.match(value) or verdict_pattern().search(value):
        return UNCONFIRMED
    return value


def render_stop_text(
    row: pc_rows.RowSpec,
    data: RunData,
    reason: str,
    stage_name: str,
    exit_code: int,
    facts: Optional[Mapping[str, Any]],
) -> bytes:
    """stop.txt: the reason, the stage, the exit code, the subtype text and the counts, as `name: value` lines."""
    stage = _stage(data, stage_name)
    turns = _record_int(stage, "turns") if stage is not None else None
    calls = len(pc_stream.tool_calls(stage.events)) if stage is not None and stage.events is not None else None
    lines = [
        "stop for %s" % row.row_id,
        "reason: %s" % reason,
        "stage: %s" % stage_name,
        "exit code: %d" % exit_code,
        "result subtype: %s" % _subtype_text(data, stage_name),
        "counts: stage records %d of %d, turns in the stopped stage %s, tool calls in the stopped stage %s"
        % (
            len(data.stages),
            len(row.stages),
            UNCONFIRMED if turns is None else turns,
            UNCONFIRMED if calls is None else calls,
        ),
    ]
    if facts is None:
        lines.append("checks: not computed")
    else:
        lines.append("checks: computed")
        for name, count in pc_checks.breaches(facts):
            lines.append("breach %s: %d" % (name, count))
    return _lines(lines)


def stopped_files(
    ctx: pc_rows.RunContext,
    data: RunData,
    row: pc_rows.RowSpec,
    reason: str,
    stage_name: str,
    exit_code: int,
    facts: Optional[Mapping[str, Any]],
) -> Dict[str, bytes]:
    """The flat file set of a STOPPED folder: README, stop.txt, usage.txt, the stage files, the checks when readable.

    Nothing from the raw folder is staged as is: no stream, no stage record, no settings file, no session id, no
    snapshot. The stage files are the rendered traces, the stored prompts, the exit lines and the error text.
    """
    clean: Callable[[str], str] = ctx.sanitizer.sanitize_text
    files: Dict[str, bytes] = {
        "README.md": render_stop(row.row_id, reason, stage_name),
        STOP_FILE: render_stop_text(row, data, reason, stage_name, exit_code, facts),
        "usage.txt": render_usage(data, row, stopped=True),
    }
    if facts is not None:
        files["mechanical-checks.md"] = render_mechanical_checks(data, facts, row)
    else:
        files["mechanical-checks.md"] = MESSAGE_CHECKS_NOT_COMPUTED.encode("utf-8")
    files.update(stage_files(row, data, facts if facts is not None else _NO_FACTS, clean, filed_row=False))
    return files


def file_stopped(
    ctx: pc_rows.RunContext,
    run_root: str,
    spec: pc_rows.RowSpec,
    reason: str,
    stage_name: str,
    exit_code: Optional[int] = None,
) -> pc_rows.RowOutcome:
    """File <destination>/STOPPED-<row folder> for a row that stopped after its run root existed.

    The folder is a label, not a result: its README ends with the one verdict line and no harness-authored file
    holds a verdict word. The files are rendered from the run root as it is on disk, for the stages that ran
    (usage.txt marks the row total unknown), sanitized, gated and promoted with the deny entries like a complete
    row; raw captures, settings, session ids and snapshots are never staged. The outcome is exit 0 and the
    `filed:` line when the label was filed (the caller keeps the stop's own exit code), else the refusal's code
    (14 gate, 15 sanitizer or scanner, 17 promote, 11 for a run root that cannot be read) and its fixed lines.
    A short chain, a stream that does not parse and a checks failure are all tolerated: the label is more useful
    filed than not.
    """
    if reason not in STOP_REASONS:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STOP_REASON,))
    if ctx.deny_entries is None or ctx.sanitizer is None:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_NO_DENY_ENTRIES,))
    try:
        data = load_stage_data(run_root)
        entry = _spec_of_run(data)
        if spec is not None and spec.row_id != entry.row_id:
            raise EvidenceError("the run record names another row")
    except EvidenceError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STOP_UNREADABLE,))
    try:
        facts: Optional[Dict[str, Any]] = pc_checks.compute_facts(run_root, ctx.config_dir)
    except pc_checks.CheckError:
        facts = None
    code = exit_code if exit_code is not None else stop_exit_code(reason)
    try:
        files = stopped_files(ctx, data, entry, reason, stage_name, code, facts)
    except (EvidenceError, OSError, KeyError, ValueError):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STOP_UNREADABLE,))
    try:
        stage = new_stage_dir(os.path.realpath(run_root))
    except OSError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STAGING,))
    try:
        count = stage_tree(stage, files, ctx.sanitizer)
    except pc_sanitize.SanitizerError:
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_SANITIZER,))
    except OSError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_STAGING,))
    label = STOPPED_PREFIX + pc_rows.row_folder_name(entry.row_id, ctx.attempt)
    result = pc_promote.promote(
        stage,
        os.path.join(ctx.destination, label),
        ctx.repo_root,
        config_dir=ctx.config_dir,
        deny_entries=ctx.deny_entries,
    )
    if int(result.code) != pc_exitcodes.OK:
        return _outcome(result, ctx.destination, 0)
    return pc_rows.RowOutcome(
        pc_exitcodes.OK, ("filed: %s/%s, %d file(s)" % (os.path.basename(ctx.destination), label, count),)
    )
