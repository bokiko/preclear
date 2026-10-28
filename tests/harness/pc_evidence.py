"""Filing a finished row 1 run as sanitized, leak-gated mechanical evidence (plan 03-04; EVID-04, EVID-05, HARN-05).

The only route from a run root to tests/evidence is here, and it has four steps in a fixed order:

  1. stage       one tree is rendered from files that are already on disk in the run root (stage records, raw
                 streams, stored prompts, snapshots, the wrapper log); nothing is taken from memory of the run
  2. sanitize    every staged file passes through the sanitizer that run_row built before any money was spent
  3. gate        the whole staged tree is scanned by the leak gate with the sanitizer's deny entries (review WR-14)
  4. promote     pc_promote.promote creates the new dated folder exclusively, once, from the scanned bytes

Raw captures never leave the run root: no stream, no NUL status capture, no hook log, no stage record, no git state
file and no run.json is ever staged. The stage folder is the first free stage-N inside the run root and is never
reused or removed. Harness-authored files hold facts, counts and ids; the row README ends with the one line
VERDICT_LINE and no harness-authored file holds a verdict word.

Messages are fixed text with counts, ids and rule labels only, never a path, a host name or the login.
Standard library only, Python 3.9 floor. Nothing here deletes, renames, moves or truncates a file.
"""
from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pc_checks
import pc_exitcodes
import pc_promote
import pc_rows
import pc_runroot
import pc_sanitize
import pc_spend
import pc_spike
import pc_stream

VERDICT_LINE = "Reviewer verdict: PENDING"
UNCONFIRMED = "UNCONFIRMED"
MARKER_NO_RESUME = "NO-RESUME-LINE"
STAGE_ORDER: Tuple[str, ...] = ("s1", "s2", "s3")

MESSAGE_UNREADABLE = "FAIL: the run root could not be read for filing; nothing is filed"
MESSAGE_BREACH = "FAIL: the checks found a breach; nothing is filed"
MESSAGE_NO_PROMPT = "FAIL: a stage prompt was not stored in the run root; nothing is filed"
MESSAGE_NO_STREAM = "FAIL: a stage stream cannot be read; nothing is filed"
MESSAGE_SANITIZER = "SCANNER_ERROR: the sanitizer could not process a staged file; nothing is filed"
MESSAGE_STAGING = "FAIL: the stage folder could not be written; nothing is filed"

_STAGE_DIR_MODE = 0o700
_FILE_MODE = 0o644


class EvidenceError(Exception):
    """The run root does not hold what filing needs; messages are fixed text."""


def _row1() -> Any:
    import pc_row1  # imported late: pc_row1 imports this module

    return pc_row1


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


def _decimal(value: Any) -> Optional[Decimal]:
    if not isinstance(value, str):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


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


def render_usage(data: RunData) -> bytes:
    """usage.txt: the stages in execution order with their session, turns and cumulative total, then the totals."""
    lines = ["usage for %s" % pc_rows.ROW1]
    for stage in data.stages:
        record = stage.record
        lines.append(
            "stage %s: session %s, turns %s, cumulative %s"
            % (stage.name, _text(record.get("session_id")), _text(record.get("turns")), _text(record.get("cumulative")))
        )
    row_total, run_total = usage_totals(data.stages)
    lines.append("row total: %s" % row_total)
    lines.append("run total: %s" % run_total)
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_model_id(data: RunData) -> bytes:
    """model-id.txt: the model id the first readable init event reported, or UNCONFIRMED."""
    for stage in data.stages:
        if stage.events is not None:
            return (_text(pc_stream.init_manifest(stage.events).get("model")) + "\n").encode("utf-8")
    return (UNCONFIRMED + "\n").encode("utf-8")


def render_folder_readme(ctx: pc_rows.RunContext, data: RunData) -> bytes:
    row_total, run_total = usage_totals(data.stages)
    lines = [
        "# Rerun %s on %s" % (ctx.evidence_date, ctx.model),
        "",
        "This folder is a new baseline on the pinned model and build.",
        "",
        "Row total: %s. Run total: %s." % (row_total, run_total),
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_row_readme(data: RunData) -> bytes:
    """The row README: the one checklist line of this slice, then the verdict line as the last line."""
    lines = [
        "# Row 1: wrong active binding (1P), rerun",
        "",
        "- [ ] cost and turns per stage: see usage.txt",
        VERDICT_LINE,
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------------------------


def filed_snapshot_files(snapshot_dir: str) -> Dict[str, bytes]:
    """The files of one snapshot folder as relative path to bytes; never the NUL status capture."""
    found: Dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(snapshot_dir):
        dirnames[:] = sorted(dirnames)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            relative = os.path.relpath(full, snapshot_dir).replace(os.sep, "/")
            if relative == "status.raw" or os.path.islink(full) or not os.path.isfile(full):
                continue
            found[relative] = _read_bytes(full)
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


def _unfileable(data: RunData) -> Optional[str]:
    if not data.stages:
        return MESSAGE_UNREADABLE
    for stage in data.stages:
        if stage.prompt is None:
            return MESSAGE_NO_PROMPT
        if stage.events is None:
            return MESSAGE_NO_STREAM
    return None


def collect_files(ctx: pc_rows.RunContext, data: RunData) -> Dict[str, bytes]:
    """Every file to stage, keyed by its path relative to the stage folder (a README.md and the row folder)."""
    row = pc_rows.ROW1
    files: Dict[str, bytes] = {
        "README.md": render_folder_readme(ctx, data),
        row + "/README.md": render_row_readme(data),
        row + "/usage.txt": render_usage(data),
        row + "/model-id.txt": render_model_id(data),
    }
    snaps = str(data.paths["snaps"])
    if os.path.isdir(snaps):
        for name in sorted(os.listdir(snaps)):
            folder = os.path.join(snaps, name)
            if os.path.isdir(folder) and not os.path.islink(folder):
                for relative, content in filed_snapshot_files(folder).items():
                    files["%s/%s/%s" % (row, name, relative)] = content
    return files


def _outcome(result: Any, destination: str, count: int) -> pc_rows.RowOutcome:
    code = int(result.code)
    if code == pc_exitcodes.OK:
        return pc_rows.RowOutcome(
            pc_exitcodes.OK, ("filed: %s, %d file(s)" % (os.path.basename(destination), count),)
        )
    lines = [str(result.message)]
    for line in str(result.report_text).splitlines():
        if line.strip():
            lines.append(line)
    return pc_rows.RowOutcome(code, tuple(lines))


def file_row(ctx: pc_rows.RunContext, run_root: str, facts: Optional[Mapping[str, Any]] = None) -> pc_rows.RowOutcome:
    """Stage, sanitize, gate and promote the finished run in run_root into ctx.destination.

    The sanitizer and the deny entries are the ones the row built before spend (ctx.sanitizer, ctx.deny_entries);
    promote is always called with both the deny entries and the config folder (review WR-14). A breach found by
    the checks files nothing (exit 11); a sanitizer error is 15, a gate refusal 14, a taken destination 17.
    """
    try:
        data = load_stage_data(run_root)
        found = dict(facts) if facts is not None else pc_checks.compute_facts(run_root, ctx.config_dir)
    except (EvidenceError, pc_checks.CheckError):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_UNREADABLE,))
    if pc_checks.breaches(found):
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_BREACH,))
    problem = _unfileable(data)
    if problem is not None:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (problem,))
    try:
        files = collect_files(ctx, data)
    except EvidenceError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_UNREADABLE,))
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
    result = pc_promote.promote(
        stage, ctx.destination, ctx.repo_root, config_dir=ctx.config_dir, deny_entries=ctx.deny_entries
    )
    return _outcome(result, ctx.destination, count)
