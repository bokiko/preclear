"""Row 1 (wrong binding): seed the run root, run the stages, record the facts (plan 03-02; HARN-05, HARN-07).

What a row 1 run is, in order:

  * seed_row1         the committed wrong-binding setup in a fresh run root: the scratch project (CLAUDE.md
                      filled from the committed row's fixture, the three-step plan, a git repository on main,
                      the frozen skill as untracked files), the logging wrapper, two ledgers of which only the
                      second is bound to the work session, the audit hook and the settings file (the body is
                      pc_rowseeds.seed_helper_row; this module keeps the name and the returned keys)
  * take_snapshot     one boundary snapshot (manifest, git status, ledger listings, copies of the ledgers,
                      the helper's fallback folder and the auto-memory folder)
  * run_stage         one claude -p call: the pinned argv from pc_flags, a ledger reservation before the process
                      and a settlement after it, the raw bytes, a stage record and a snapshot
  * read_stage_prompts  the work-turn prompt from the data file and the /preclear prompt read in place from the
                      committed publication folder (never copied, so it is byte-identical by construction)
  * run_row           the chain: every refusal that can come before money (destination, run root, sanitizer,
                      ledger), then s1, s2 resumed on the same session and, when s2 printed a resume line, s3
                      in a fresh session whose prompt is that line; the chain stops at the first stage that
                      did not complete cleanly
  * run_registered_row  the same chain read from a registry entry alone (plan 04-01): the seed, the prompt files,
                      the session keys, the allowlist profile and the filing come from the RowSpec; the row
                      folder is refused when it exists (17), a dated folder that exists is not a refusal
  * extract_resume_line, caller_map, finish   the resume-line rule, the sanitizer's caller map and the closing
                      lines of a completed chain
  * breach_outcome    the mechanical checks of pc_checks over the run root after every stage and in finish: a
                      write outside the approved roots or a git mutation is exit 11, counts only; the raw files
                      stay in the run root
  * file_stop         every stop after the run root exists (a turn limit, a cap, a timeout, a non-zero exit, an
                      unreadable stream, an isolation assertion, a breach) is filed as STOPPED-<row folder>
                      through pc_evidence.file_stopped, with the stop's own exit code kept (plan 04-03)
  * paths_for         the paths mapping of a run root rebuilt from the folder alone (filing and --refile)
  * finish            after clean checks, files the row through pc_evidence.file_row (plan 03-04)

Every file and folder is created exclusively (pc_runroot); nothing here deletes, renames, moves or truncates, and
nothing here starts the real claude by itself: the caller names the executable through the run context.
Messages are fixed text with row and stage ids, counts and states only, never a path or an argument value.

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib
import json
import os
import re
import shutil
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pc_checks
import pc_evidence
import pc_exitcodes
import pc_flags
import pc_leakgate
import pc_manifest
import pc_rows
import pc_rowseeds
import pc_runroot
import pc_sanitize
import pc_spend
import pc_spike
import pc_stream

ROW_ID = pc_rows.ROW1

PUBLICATION = "tests/evidence/publication-2026-10-20/row1-wrong-binding"
DATA_DIR = "tests/harness/data"
PLAN_DATA = DATA_DIR + "/row1-plan.md"
S1_PROMPT_DATA = DATA_DIR + "/row1-s1-prompt.md"
S2_PROMPT_COMMITTED = PUBLICATION + "/s2-preclear-prompt.md"
FIXTURE_CLAUDE_MD = PUBLICATION + "/fixture-CLAUDE.md"
LEDGER_A_NAME = pc_rowseeds.LEDGER_A_NAME
LEDGER_B_NAME = pc_rowseeds.LEDGER_B_NAME
PLAN_NAME = pc_rowseeds.PLAN_NAME
TOKEN_PROJECT = pc_rowseeds.TOKEN_PROJECT
LEDGER_PLACEHOLDER = "$LEDGER"

# The boundary snapshot each stage takes after its process ends.
SNAPSHOT_SETUP = "snap-0-setup"
SNAPSHOT_NAMES: Dict[str, str] = {
    "s1": "snap-1-after-work",
    "s2": "snap-2-after-preclear",
    "s3": "snap-3-after-resume",
}

PROBLEM_TIMEOUT = "timeout"
PROBLEM_EXIT = "exit"
PROBLEM_STREAM = "stream"
PROBLEM_SUBTYPE = "subtype"
PROBLEM_IS_ERROR = "is-error"
PROBLEM_TERMINAL = "terminal"

USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
CONSISTENCY_TOLERANCE = Decimal("0.000001")
_STUB_TIMEOUT_SECONDS = 60


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _read(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def isolation_mode() -> str:
    """The isolation mode word, taken from the pinned isolation claim and never typed here."""
    return pc_rowseeds.isolation_mode()


def read_stage_prompts(repo_root: str, ledger_a_path: str) -> Tuple[str, str]:
    """Return (the s1 prompt, the s2 prompt).

    The s1 prompt is the data file with the ledger placeholder replaced by the ledger A path. The s2 prompt is
    the committed publication file, read in place and never copied, so the bytes are the committed bytes.
    """
    s1 = _read(os.path.join(repo_root, *S1_PROMPT_DATA.split("/"))).decode("utf-8")
    s2 = _read(os.path.join(repo_root, *S2_PROMPT_COMMITTED.split("/"))).decode("utf-8")
    return s1.replace(LEDGER_PLACEHOLDER, ledger_a_path), s2


# ---------------------------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------------------------

def seed_row1(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """Build the row 1 setup inside the already-created run root and return its paths.

    The body is pc_rowseeds.seed_helper_row with the row 1 parameters (ledgers A and B, the session bound to B);
    the returned keys and the layout are the ones this function has always returned.
    """
    return pc_rowseeds.seed_row1(
        repo_root, run_root, session_id, harness_home_dir, runs_dir, evidence_date, model
    )


def paths_for(run_root: str) -> Dict[str, Optional[str]]:
    """Return the paths mapping seed_row1 returned, rebuilt from a run root alone; it touches nothing.

    Filing and --refile use it so they need no memory of the run. The names are the fixed folder names of the
    seed, so the same call on the same folder always gives the same mapping.
    """
    root = os.path.realpath(run_root)
    wrapper_dir = os.path.join(root, "wrapper")
    ckpt = os.path.join(root, "ckpt")
    ledgers = os.path.join(ckpt, "ledgers")
    raw = os.path.join(root, "raw")
    project = os.path.join(root, "project")
    return {
        "run_root": root,
        "project": project,
        "skill_dir": os.path.join(project, ".claude", "skills", "preclear"),
        "wrapper_dir": wrapper_dir,
        "wrapper": os.path.join(wrapper_dir, "checkpoint"),
        "ckpt": ckpt,
        "ledgers": ledgers,
        "ledger_a": os.path.join(ledgers, LEDGER_A_NAME),
        "ledger_b": os.path.join(ledgers, LEDGER_B_NAME),
        "auto_memory": os.path.join(root, "auto-memory"),
        "raw": raw,
        "snaps": os.path.join(root, "snaps"),
        "settings": os.path.join(root, "settings.json"),
        "hooklog": os.path.join(raw, "hooklog.jsonl"),
    }


# ---------------------------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------------------------


def _excluded(path: bytes) -> bool:
    """True for entries a boundary snapshot leaves out: raw, snaps and the project's .git.

    raw and snaps are the run's own record, guarded at every boundary by pc_checks.capture_guard. A
    stage-prefixed top-level folder is no longer left out (the filing makes those only after the last
    snapshot), so one made by the model is listed as a write outside the approved roots.
    """
    top = path.split(b"/", 1)[0]
    if top in (b"raw", b"snaps"):
        return True
    return path == b"project/.git" or path.startswith(b"project/.git/")


def _sorted_names(names: Sequence[str]) -> List[str]:
    return sorted(names, key=os.fsencode)


def _listing(names: Sequence[str]) -> bytes:
    return "".join(name + "\n" for name in names).encode("utf-8", "surrogateescape")


STATUS_NOT_RUN = "git status was not run: the git folder differs from the setup state"
STATUS_NOT_RUN_NESTED = "git status was not run: the project holds a nested repository"


def take_snapshot(
    paths: Mapping[str, Optional[str]],
    name: str,
    git: str,
    refuse_under: Sequence[str] = (),
    setup: bool = False,
    pin: Optional[str] = None,
) -> List[str]:
    """Write snaps/<name> and return the names of model-written trees whose copy was skipped.

    The folder holds sha.txt and manifest.jsonl of the run root (without raw, snaps and the project's .git;
    a stage-prefixed top-level folder is listed like any other), status.txt and status.raw from git status, ledgers-ls.txt and
    bindings-ls.txt, a copy of each ledger markdown file and, when present, copies of project/.preclear
    (as preclear) and the auto-memory folder (as auto-memory). A symlink or special file inside one of those
    two trees skips that one copy only; the manifest still lists the entry. A taken name is FileExistsError.

    git status is gated by the gitdir digest taken at setup and held in memory (pin; pc_checks.pinned_gitdir
    compares the pin file with it before the snapshot folder exists or any git process starts): once the project's
    .git folder differs from it, git is not started (a command planted in the repository's own configuration
    would run), status.raw is empty and status.txt holds the one fixed line STATUS_NOT_RUN. A project that holds
    a nested repository gets the fixed line STATUS_NOT_RUN_NESTED instead, for the same reason. The pin is
    required after setup: only the setup snapshot (setup true) is unpinned; any other snapshot without the
    in-memory pin, without raw/setup.git.json or with a file that differs from the pin is a CheckError (second-pass
    WR-03, third-pass WR-02).
    """
    pin = pc_checks.pinned_gitdir(str(paths["raw"]), setup, pin)
    run_root = str(paths["run_root"])
    entries = [e for e in pc_manifest.tree_manifest(run_root, tuple(refuse_under)) if not _excluded(e["path"])]
    dest = os.path.join(str(paths["snaps"]), name)
    pc_manifest.write_snapshot(dest, entries)
    try:
        raw_status, text_status = pc_manifest.capture_git_status(str(paths["project"]), git, pin)
    except pc_manifest.NestedRepository:
        raw_status, text_status = b"", (STATUS_NOT_RUN_NESTED + "\n").encode("utf-8")
    except pc_manifest.GitDirChanged:
        raw_status, text_status = b"", (STATUS_NOT_RUN + "\n").encode("utf-8")
    pc_runroot.write_exclusive(os.path.join(dest, "status.raw"), raw_status, 0o600)
    pc_runroot.write_exclusive(os.path.join(dest, "status.txt"), text_status, 0o600)
    ledgers = str(paths["ledgers"])
    ledger_names = _sorted_names([n for n in os.listdir(ledgers) if not n.startswith(".")])
    pc_runroot.write_exclusive(os.path.join(dest, "ledgers-ls.txt"), _listing(ledger_names), 0o600)
    bindings = os.path.join(str(paths["ckpt"]), "bindings")
    binding_names = _sorted_names(os.listdir(bindings)) if os.path.isdir(bindings) else []
    pc_runroot.write_exclusive(os.path.join(dest, "bindings-ls.txt"), _listing(binding_names), 0o600)
    for ledger_name in ledger_names:
        full = os.path.join(ledgers, ledger_name)
        if ledger_name.endswith(".md") and os.path.isfile(full) and not os.path.islink(full):
            pc_runroot.write_exclusive(os.path.join(dest, ledger_name), _read(full), 0o600)
    skipped: List[str] = []
    for source, label in (
        (os.path.join(str(paths["project"]), ".preclear"), "preclear"),
        (str(paths["auto_memory"]), "auto-memory"),
    ):
        if os.path.lexists(source) and (os.path.isdir(source) or os.path.islink(source)):
            try:
                pc_runroot.copy_tree_exclusive(source, os.path.join(dest, label))
            except pc_runroot.RunRootError:
                skipped.append(label)
    return skipped


# ---------------------------------------------------------------------------------------------
# The init manifest and the instruction audit, asserted after every stage (HARN-07)
# ---------------------------------------------------------------------------------------------

# The nine spike ids, then three more. The order is part of the contract and is stated only here.
ROW_ASSERTION_IDS: Tuple[str, ...] = tuple(pc_spike.S1_ASSERTION_IDS) + (
    "memory-path-as-set",
    "cwd-is-project",
    "session-id-as-requested",
)
_HOOK_IDS: Tuple[str, ...] = tuple(pc_spike.S1_ASSERTION_IDS[6:])
KIND_FRESH = "fresh"
KIND_RESUME = "resume"
HOW_NOT_ON_RESUME = "not-asserted-on-resume"
STATUS_PASS = "pass"
STATUS_STOP = "stop"


class Evaluation(NamedTuple):
    """The assertions of one stage: status pass or stop, the triples, counts and a fixed-text reason."""

    status: str
    assertions: List[Tuple[str, str, bool]]
    counts: Dict[str, Any]
    reason: str


class BinaryScan(object):
    """Reads the claude executable for defined names at most once per name, and only when asked.

    The scan is asked only when the init lists show a candidate hit. Answers are cached for the life of the
    object, so one run reads the binary once however many stages show the same candidates.
    """

    def __init__(self, claude_path: str, lookup: Any = None) -> None:
        self._path = claude_path
        self._lookup = lookup
        self._known: Dict[str, bool] = {}

    def __call__(self, candidates: Any) -> frozenset:
        wanted = frozenset(candidates)
        unknown = wanted - frozenset(self._known)
        if unknown:
            lookup = self._lookup if self._lookup is not None else pc_spike.binary_defines
            found = frozenset(lookup(os.path.realpath(self._path), unknown))
            for name in unknown:
                self._known[name] = name in found
        return frozenset(name for name in wanted if self._known[name])


def _memory_path_ok(init: Mapping[str, Any], auto_memory: str) -> bool:
    """memory_paths must be a mapping whose auto value is an absolute path naming the auto-memory folder.

    Compared by realpath with a trailing separator tolerated; a sibling folder that shares a name prefix is not
    equal, and an absent, empty or non-text value is a failure, never a pass.
    """
    memory_paths = init.get("memory_paths")
    if not isinstance(memory_paths, dict):
        return False
    auto = memory_paths.get("auto")
    if not isinstance(auto, str) or not auto or not os.path.isabs(auto):
        return False
    trimmed = auto.rstrip(os.sep)
    if trimmed == "":
        return False
    return os.path.realpath(trimmed) == os.path.realpath(auto_memory)


def _cwd_ok(init: Mapping[str, Any], project: str) -> bool:
    cwd = init.get("cwd")
    return isinstance(cwd, str) and cwd != "" and os.path.realpath(cwd) == os.path.realpath(project)


def _session_ok(events: Sequence[Dict[str, Any]], init: Mapping[str, Any], requested: str) -> bool:
    try:
        result = pc_stream.require_single_result(events)
    except pc_stream.StreamError:
        return False
    return init.get("session_id") == requested and result.get("session_id") == requested


def _evaluate_parts(
    events: Sequence[Dict[str, Any]],
    hooklog_slice: Sequence[Dict[str, Any]],
    paths: Mapping[str, Optional[str]],
    requested_session: str,
    kind: str,
    user_names: Any,
    binary_defined: Any,
    config_dir: str,
) -> Tuple[List[Tuple[str, str, bool]], Dict[str, Any]]:
    triples, counts = pc_spike.s1_evaluation(
        events,
        list(hooklog_slice),
        user_names,
        str(paths["project"]),
        str(paths["run_root"]),
        config_dir,
        binary_defined,
    )
    adjusted: List[Tuple[str, str, bool]] = []
    for name, how, ok in triples:
        if kind == KIND_RESUME and name in _HOOK_IDS and how == pc_spike.HOW_NONE:
            adjusted.append((name, HOW_NOT_ON_RESUME, True))
        else:
            adjusted.append((name, how, ok))
    init = pc_stream.init_manifest(events)
    adjusted.append(("memory-path-as-set", pc_spike.HOW_INIT, _memory_path_ok(init, str(paths["auto_memory"]))))
    adjusted.append(("cwd-is-project", pc_spike.HOW_INIT, _cwd_ok(init, str(paths["project"]))))
    adjusted.append(
        ("session-id-as-requested", pc_spike.HOW_INIT, _session_ok(events, init, requested_session))
    )
    return adjusted, counts


def stage_assertions(
    events: Sequence[Dict[str, Any]],
    hooklog_slice: Sequence[Dict[str, Any]],
    paths: Mapping[str, Optional[str]],
    requested_session: str,
    kind: str,
    user_names: Any,
    binary_defined: Any,
    config_dir: str,
) -> List[Tuple[str, str, bool]]:
    """Return the twelve (id, how, ok) triples in the order of ROW_ASSERTION_IDS.

    The nine spike assertions come from pc_spike.s1_evaluation. For a resumed stage whose hook slice holds no
    entry the three hook ids are recorded as not asserted on resume and are ok (silence on resume is a fact,
    not a failure); for any other empty slice they are not assertable and fail. A boundary violation in a
    non-empty slice fails in either kind of stage.
    """
    return _evaluate_parts(
        events, hooklog_slice, paths, requested_session, kind, user_names, binary_defined, config_dir
    )[0]


def evaluate_stage(
    events: Sequence[Dict[str, Any]],
    hooklog_slice: Sequence[Dict[str, Any]],
    paths: Mapping[str, Optional[str]],
    requested_session: str,
    kind: str,
    user_names: Any,
    scan: Any,
    config_dir: str,
) -> Evaluation:
    """Evaluate one stage: pass only when every assertion is ok, otherwise stop (D-02, HARN-07).

    The binary is scanned (through scan, cached) only when the init lists show a candidate user-name hit.
    """
    init = pc_stream.init_manifest(events)
    candidates = pc_spike.hit_candidates(init, user_names)
    defined = scan(candidates) if candidates else frozenset()
    triples, counts = _evaluate_parts(
        events, hooklog_slice, paths, requested_session, kind, user_names, defined, config_dir
    )
    unassertable = [name for name, how, _ok in triples if how == pc_spike.HOW_NONE]
    failed = [name for name, how, ok in triples if not ok and how != pc_spike.HOW_NONE]
    parts = []
    if unassertable:
        parts.append("no instruction entry was seen for this stage so the instruction audit is not assertable")
    if failed:
        parts.append("isolation assertion(s) failed: %s" % ", ".join(failed))
    if parts:
        return Evaluation(STATUS_STOP, triples, counts, ", ".join(parts))
    return Evaluation(STATUS_PASS, triples, counts, "")


def describe_evaluation(stage_name: str, evaluation: Evaluation) -> List[str]:
    """Return the lines to print: ids, yes or no, and counts. Never a name, a path or a host."""
    lines = ["stage %s isolation: %s" % (stage_name, evaluation.status)]
    for name, how, ok in evaluation.assertions:
        lines.append("assertion %s: %s (%s)" % (name, "yes" if ok else "no", how))
    c = evaluation.counts
    lines.append(
        "user names: %d listed, %d excluded, %d hit(s), %d collision(s), audit source %s"
        % (c["user_names"], c["user_names_excluded"], c["user_name_hits"], c["user_name_collisions"], c["audit_source"])
    )
    lines.append(
        "instruction entries: user=%d project=%d local=%d managed=%d unknown=%d"
        % (c["entries_user"], c["entries_project"], c["entries_local"], c["entries_managed"], c["entries_unknown"])
    )
    if evaluation.status != STATUS_PASS:
        lines.append("STOP: %s" % evaluation.reason)
    return lines


def _hook_slice(path: str, start: int) -> List[Dict[str, Any]]:
    """The records the audit hook appended after the first `start` lines of its log."""
    if not os.path.isfile(path):
        return []
    lines = [line for line in _read(path).decode("utf-8", "replace").splitlines() if line.strip()]
    found: List[Dict[str, Any]] = []
    for line in lines[start:]:
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        found.append(record if isinstance(record, dict) else {"error": "unparseable"})
    return found


# ---------------------------------------------------------------------------------------------
# One stage
# ---------------------------------------------------------------------------------------------


class StageResult(NamedTuple):
    """The outcome of one stage. events, summary, delta and cumulative are None where nothing usable arrived."""

    name: str
    session_id: str
    resume: bool
    returncode: Optional[int]
    timed_out: bool
    wall_seconds: float
    events: Optional[List[Dict[str, Any]]]
    summary: Optional[Dict[str, Any]]
    usage: Optional[Dict[str, int]]
    delta: Optional[Decimal]
    cumulative: Optional[Decimal]
    attempt: int
    ok: bool
    problem: str
    stdout_sha256: str
    stdout_size: int
    evaluation: Any = None
    hooklog_lines: int = 0


def _row_stage_keys(
    row_id: str = ROW_ID, campaign: Optional[str] = None, attempt: int = 1, matrix: bool = False
) -> Tuple[str, ...]:
    """The ledger stage keys of a row under a scope: the allowed-stage tuple the spend ledger checks a launch against."""
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id)
    if entry is None:
        raise pc_spike.SpikeError("the row is not in the registry")
    return tuple(pc_rows.scoped_stage_key(row_id, stage.name, campaign, attempt, matrix) for stage in entry.stages)


def _entry_of(row_id: str) -> pc_rows.RowSpec:
    """The implemented registry entry of a row id, matched exactly; anything else is a SpikeError."""
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id) if isinstance(row_id, str) else None
    if entry is None or not entry.implemented:
        raise pc_spike.SpikeError("the row is not in the registry")
    return entry


def allowed_tools(profile: str, wrapper: str) -> Tuple[str, ...]:
    """The --allowedTools rules of an allowlist profile; a profile this harness does not know is a ValueError.

    PROFILE_HELPER is the committed baseline plus one rule per model-facing verb of the logging wrapper. A new
    profile is one more branch here and one more constant in pc_rows, never a second place that builds rules.
    """
    if profile == pc_rows.PROFILE_HELPER:
        return pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    raise ValueError("the allowlist profile is not known")


def snapshot_name(stage: pc_rows.StageSpec) -> str:
    """The boundary snapshot a stage takes after its process ends: snap-<number>-after-<kind word>.

    s1 work, s2 preclear and s3 resume give the three names the Phase 3 baseline holds.
    """
    return "snap-%s-after-%s" % (stage.name[1:], stage.kind)


def _git_executable(env: Mapping[str, str]) -> str:
    found = shutil.which("git", path=env.get("PATH") or os.defpath)
    if found is None:
        found = shutil.which("git", path=os.environ.get("PATH", os.defpath))
    if found is None:
        raise pc_spike.SpikeError("git was not found on the search path")
    return found


def _line_count(path: str, marker: Optional[bytes] = None) -> int:
    """Count the lines of a file (those holding marker when given); a missing file counts zero."""
    if not os.path.isfile(path):
        return 0
    count = 0
    for line in _read(path).split(b"\n"):
        if line and (marker is None or marker in line):
            count += 1
    return count


def _usage_of(result_event: Mapping[str, Any]) -> Optional[Dict[str, int]]:
    usage = result_event.get("usage")
    if not isinstance(usage, dict):
        return None
    found = {}
    for key in USAGE_KEYS:
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            found[key] = value
    return found


def _consistent(
    previous_total: Optional[Decimal], delta: Optional[Decimal], cumulative: Optional[Decimal], has_block: bool
) -> str:
    """yes when the cumulative total equals the previous total plus this call's delta (to a millionth).

    has_block says the call's own cost was read from the per-call block of the result event
    (pc_spend.has_call_block). Without it the delta was derived from the totals, so the comparison would hold by
    construction and compares nothing independent: the value is unknown (second-pass WR-04, D-14).
    """
    if not has_block or delta is None or cumulative is None:
        return "unknown"
    expected = delta if previous_total is None else previous_total + delta
    return "yes" if abs(cumulative - expected) <= CONSISTENCY_TOLERANCE else "no"


def _cost_text(value: Optional[Decimal]) -> Optional[str]:
    return None if value is None else format(value, "f")


def _classify(call: Any, events: Any, summary: Any) -> str:
    if call.timed_out:
        return PROBLEM_TIMEOUT
    if call.returncode != 0:
        return PROBLEM_EXIT
    if events is None or summary is None:
        return PROBLEM_STREAM
    if summary["subtype"] != "success":
        return PROBLEM_SUBTYPE
    if summary["is_error"] is True:
        return PROBLEM_IS_ERROR
    terminal = summary["terminal_reason"]
    if terminal is not None and terminal != "completed":
        return PROBLEM_TERMINAL
    return ""


def run_stage(
    ctx: pc_rows.RunContext,
    paths: Mapping[str, Optional[str]],
    spec: pc_rows.StageSpec,
    session_id: str,
    prompt: str,
    resume: bool,
    previous_total: Optional[Decimal],
    timeout: int,
    hook_start: int = 0,
    scan: Any = None,
    row: Optional[pc_rows.RowSpec] = None,
) -> StageResult:
    """Run one stage: reserve its cap, run the process, settle the cost, keep the raw bytes, snapshot.

    row is the registry entry the stage belongs to (row 1 when omitted): its id keys the ledger and its allowlist
    profile gives the --allowedTools rules.

    The command is built only by pc_flags (build_argv, build_env, build_allowed_tools). The reservation is a
    pessimistic launch line written before the process; the settlement replaces it with the call's own cost
    (a timeout settles with no delta, so the cap stays counted). A stage is never started a second time: the
    ledger refuses a second launch. The stage record and the snapshot are written whatever the outcome.

    When the stream parses, the init manifest and the instruction audit are asserted for this stage on the hook
    log lines added since the previous stage boundary (hook_start is the line count that boundary recorded);
    the triples and the entry counts go into the stage record. scan is the cached binary lookup of the run.
    """
    if row is None:
        row = _entry_of(ROW_ID)
    tools = allowed_tools(row.tools_profile, str(paths["wrapper"]))
    argv = pc_flags.build_argv(
        str(ctx.claude), session_id, str(paths["settings"]), tools, spec.max_turns, spec.cap, resume=resume, model=ctx.model
    )
    env = pc_flags.build_env(ctx.env, ctx.config_dir, str(paths["ckpt"]))
    scope = (ctx.campaign, ctx.attempt, ctx.matrix)
    ledger_row = pc_rows.scoped_row(row.row_id, *scope)
    key = pc_rows.scoped_stage_key(row.row_id, spec.name, *scope)
    attempt = pc_spend.append_launch(
        ctx.harness_home, ledger_row, key, spec.cap, ctx.version, _row_stage_keys(row.row_id, *scope)
    )
    # The prompt is kept verbatim in raw before the process starts, so a later filing or refile needs nothing from
    # memory. It comes after the reservation: a second launch of a stage is refused by the ledger first.
    pc_runroot.write_exclusive(os.path.join(str(paths["raw"]), spec.name + ".prompt"), prompt.encode("utf-8"), 0o600)

    started = datetime.datetime.now(datetime.timezone.utc)
    call = pc_spike.run_claude(argv, env, str(paths["project"]), prompt, timeout, str(paths["raw"]), spec.name)
    wall = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()

    events: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    result_event: Optional[Dict[str, Any]] = None
    try:
        parsed = pc_stream.parse_stream(call.stdout)
        result_event = pc_stream.require_single_result(parsed)
        summary = pc_stream.result_summary(parsed)
        pc_stream.init_manifest(parsed)
        events = parsed
    except pc_stream.StreamError:
        events = summary = result_event = None

    delta: Optional[Decimal] = None
    cumulative: Optional[Decimal] = None
    if events is not None and summary is not None and result_event is not None and not call.timed_out:
        cumulative = summary["total_cost_usd"]
        try:
            delta = pc_spend.call_cost(result_event, previous_total)
        except pc_spend.SpendError:
            delta = None
    if call.timed_out:
        subtype = "timeout"
    elif summary is not None and isinstance(summary["subtype"], str) and summary["subtype"]:
        subtype = summary["subtype"][:64]
    else:
        subtype = "no-result"
    pc_spend.settle(ctx.harness_home, ledger_row, key, attempt, subtype, delta, cumulative, ctx.version)

    problem = _classify(call, events, summary)
    snapshot = snapshot_name(spec)
    vcs = _git_executable(ctx.env)
    skipped = take_snapshot(paths, snapshot, vcs, pin=ctx.setup_pin)
    pc_checks.capture_boundary_state(paths, spec.name, vcs, ctx.setup_pin)
    usage = _usage_of(result_event) if result_event is not None else None
    stdout_sha = _sha256(call.stdout)
    evaluation: Optional[Evaluation] = None
    if events is not None:
        home = ctx.env.get("HOME")
        names = pc_spike.local_user_names(home) if home else frozenset()
        evaluation = evaluate_stage(
            events,
            _hook_slice(str(paths["hooklog"]), hook_start),
            paths,
            session_id,
            KIND_RESUME if resume else KIND_FRESH,
            names,
            scan if scan is not None else BinaryScan(str(ctx.claude)),
            ctx.config_dir,
        )
    hooklog_lines = _line_count(str(paths["hooklog"]))
    record = {
        "stage": spec.name,
        "session_id": session_id,
        "resume": bool(resume),
        "returncode": call.returncode,
        "timed_out": call.timed_out,
        "wall_seconds": "%.1f" % wall,
        "attempt": attempt,
        "cap": _cost_text(spec.cap),
        "max_turns": spec.max_turns,
        "version": ctx.version,
        "wrapper_calls": _line_count(os.path.join(str(paths["wrapper_dir"]), "calls.log"), b" CALL"),
        "hooklog_lines": hooklog_lines,
        "snapshot": snapshot,
        "snapshot_copy_skipped": skipped,
        "subtype": subtype,
        "turns": summary["num_turns"] if summary is not None else None,
        "delta": _cost_text(delta),
        "cumulative": _cost_text(cumulative),
        "cumulative_consistent": _consistent(
            previous_total, delta, cumulative, result_event is not None and pc_spend.has_call_block(result_event)
        ),
        "usage": usage,
        "problem": problem,
        "stdout_sha256": stdout_sha,
        "stdout_size": len(call.stdout),
        "evaluation": evaluation.status if evaluation is not None else None,
        "assertions": [list(triple) for triple in evaluation.assertions] if evaluation is not None else None,
        "hook_entries": _entry_counts(evaluation),
        "audit_source": evaluation.counts["audit_source"] if evaluation is not None else None,
    }
    pc_runroot.write_exclusive(
        os.path.join(str(paths["raw"]), spec.name + ".record.json"),
        (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o600,
    )
    # The guard comes last, after the record, so that the record is part of what the next boundary compares: a
    # record the model rewrites during the next stage differs from the digest taken here (WR-01).
    pc_checks.capture_guard(paths, spec.name)
    return StageResult(
        spec.name,
        session_id,
        bool(resume),
        call.returncode,
        call.timed_out,
        wall,
        events,
        summary,
        usage,
        delta,
        cumulative,
        attempt,
        problem == "",
        problem,
        stdout_sha,
        len(call.stdout),
        evaluation,
        hooklog_lines,
    )


def _entry_counts(evaluation: Optional[Evaluation]) -> Optional[Dict[str, int]]:
    if evaluation is None:
        return None
    return dict(
        (kind, evaluation.counts["entries_" + kind]) for kind in ("user", "project", "local", "managed", "unknown")
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------------------------
# The resume line and the sanitizer's caller map
# ---------------------------------------------------------------------------------------------

MAX_RESUME_LINE_BYTES = 2000
MARKER_FOUND = "found"
MARKER_NONE = "NO-RESUME-LINE"
_RESUME_FENCE = re.compile(r"```[A-Za-z0-9_-]*\n(.*?)\n```", re.S)
_RESUME_START = "Resume "


def extract_resume_line(result_text: Any) -> str:
    """Return the resume line of an s2 reply, or the empty string.

    The line is the last fenced single line that starts with `Resume `. It must be at most 2000 bytes and hold
    no NUL; a last candidate that breaks a bound gives the empty string and is not replaced by an earlier one.
    A fenced block of several lines and a single line that starts with anything else are not candidates.
    """
    if not isinstance(result_text, str):
        return ""
    candidates = []
    for block in _RESUME_FENCE.findall(result_text):
        line = block.strip()
        if "\n" not in line and line.startswith(_RESUME_START):
            candidates.append(line)
    if not candidates:
        return ""
    line = candidates[-1]
    if "\x00" in line or len(line.encode("utf-8")) > MAX_RESUME_LINE_BYTES:
        return ""
    return line


def _users_prefix(path: str) -> Optional[str]:
    """The two-component prefix of a path under a users or home root (a folder the gate reads as a home)."""
    parts = path.split(os.sep)
    if len(parts) >= 3 and parts[0] == "" and parts[1] in ("Users", "home") and parts[2] != "":
        return os.sep.join(parts[:3])
    return None


def caller_map(paths: Mapping[str, Optional[str]], runs_root: str) -> Dict[str, str]:
    """Map absolute paths to the caller tokens the sanitizer accepts (finding C7).

    The run root is the run token and the auto-memory folder its own token. The runs root, its parent and, when
    the runs root sits under a users or home root, the two-component prefix are the scratch token, so the shared
    parent of every run root cannot reach a committed file as a home-shaped path. The sanitizer matches the longest
    text first, so the run root inside the runs root keeps the run token. The wrapper stays under the run token.
    """
    mapping: Dict[str, str] = {str(paths["run_root"]): "<run>"}
    if paths.get("auto_memory"):
        mapping[str(paths["auto_memory"])] = "<auto-memory-root>"
    runs = os.path.realpath(runs_root)
    scratch = [runs, os.path.dirname(runs)]
    prefix = _users_prefix(runs)
    if prefix is not None:
        scratch.append(prefix)
    for path in scratch:
        if len(path.strip(os.sep)) > 0 and path not in mapping:
            mapping[path] = "<scratch>"
    return mapping


# ---------------------------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------------------------

MESSAGE_ROW_FOLDER = "REFUSED: the row folder already exists; a row folder is never reused"
MESSAGE_SANITIZER = "FAIL: the sanitizer or the deny entries could not be built; nothing was spent"
_STOP_TEXT = {
    PROBLEM_TIMEOUT: "timed out",
    PROBLEM_EXIT: "exited with a non-zero status",
    PROBLEM_STREAM: "ended without a single result event",
    PROBLEM_SUBTYPE: "ended with a result that is not a success",
    PROBLEM_IS_ERROR: "reported an error in its result",
    PROBLEM_TERMINAL: "did not end as completed",
}


MESSAGE_RAW_STAYS = "the raw files and snapshots stay in the run root"
MESSAGE_RECORD_UNREADABLE = (
    "FAIL: stage %s could not be checked against the setup record; the chain stopped; "
    "the raw files and snapshots stay in the run root"
)


def _stopped(stage_name: str, problem: str) -> pc_rows.RowOutcome:
    code = pc_exitcodes.DENIAL_FOUND if problem == PROBLEM_STREAM else pc_exitcodes.PREFLIGHT_FAIL
    line = "FAIL: stage %s %s; the chain stopped; %s" % (stage_name, _STOP_TEXT[problem], MESSAGE_RAW_STAYS)
    return pc_rows.RowOutcome(code, (line,))


def _isolation_stop(stage_name: str, evaluation: Evaluation) -> pc_rows.RowOutcome:
    head = "FAIL: stage %s did not meet the isolation baseline; the chain stopped; %s" % (stage_name, MESSAGE_RAW_STAYS)
    return pc_rows.RowOutcome(
        pc_exitcodes.PREFLIGHT_FAIL, tuple([head] + describe_evaluation(stage_name, evaluation))
    )


def file_stop(
    ctx: pc_rows.RunContext,
    entry: pc_rows.RowSpec,
    reason: str,
    stage_name: str,
    outcome: pc_rows.RowOutcome,
) -> pc_rows.RowOutcome:
    """File the STOPPED label of a stop and return the stop's own outcome with the `filed:` line added.

    The exit code stays the stop's (11 or 19), the lines stay as they were and one `filed:` line follows. When the
    filing is refused (14, 15, 17, or 11 for a run root the filing cannot read) the refusal's code and its fixed
    lines follow the stop's lines instead: a stop that could not be labelled is still a stop, and the raw files
    stay in the run root for the reviewer.
    """
    filed = pc_evidence.file_stopped(ctx, str(ctx.run_root), entry, reason, stage_name, outcome.code)
    lines = tuple(outcome.lines) + tuple(filed.lines)
    if filed.code == pc_exitcodes.OK:
        return outcome._replace(lines=lines)
    return pc_rows.RowOutcome(filed.code, lines)


def _result_text(result: StageResult) -> str:
    if result.events is None:
        return ""
    text = pc_stream.require_single_result(result.events).get("result")
    return text if isinstance(text, str) else ""


def _write_chain(paths: Mapping[str, Optional[str]], line: str) -> None:
    """Record whether s2 printed a resume line. The line is model text: it is stored in raw only, never printed."""
    record = {
        "marker": MARKER_FOUND if line else MARKER_NONE,
        "resume_line": line if line else None,
        "resume_line_bytes": len(line.encode("utf-8")) if line else 0,
    }
    pc_runroot.write_exclusive(
        os.path.join(str(paths["raw"]), "chain.json"),
        (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o600,
    )


def _chain_totals(results: Sequence[StageResult]) -> List[Optional[Decimal]]:
    """The final cumulative total of each session chain, once (s1 sits inside the s2 chain)."""
    last: Dict[str, Optional[Decimal]] = {}
    for result in results:
        last[result.session_id] = result.cumulative
    return list(last.values())


MESSAGE_CHECKS_UNREADABLE = (
    "FAIL: the mechanical checks could not read the run root; the raw files stay in the run root"
)
_BREACH_TEXT = {
    pc_checks.BREACH_WRITES: "writes outside approved roots",
    pc_checks.BREACH_GIT: "git mutations",
    pc_checks.BREACH_RECORD: "changes to the run's own record files",
}


def breach_outcome(ctx: pc_rows.RunContext, paths: Mapping[str, Optional[str]]) -> Optional[pc_rows.RowOutcome]:
    """Run the mechanical checks over the run root as it is on disk; a breach is exit 11 (the caller files the label).

    A concrete write outside the approved roots (a Bash write escape included), a git mutation or a change to
    the run's own record files is a breach (HARN-09). Every other fact (denials, ledger changes, helper-call
    disagreement, read-only Bash path mentions) is left for the reviewer.
    The lines hold counts and ids only, never a path. A run root the checks cannot read is a broken harness
    and is also exit 11, because a run whose isolation cannot be shown must not be filed as a row.
    """
    try:
        facts = pc_checks.compute_facts(str(paths["run_root"]), ctx.config_dir)
    except pc_checks.CheckError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_CHECKS_UNREADABLE,))
    found = pc_checks.breaches(facts)
    if not found:
        return None
    lines = ["isolation or git breach: %s: %d" % (_BREACH_TEXT[name], count) for name, count in found]
    lines.append(MESSAGE_RAW_STAYS)
    return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, tuple(lines))


def finish(
    ctx: pc_rows.RunContext,
    paths: Mapping[str, Optional[str]],
    results: Sequence[StageResult],
    entry: pc_rows.RowSpec,
) -> pc_rows.RowOutcome:
    """Close a completed chain: the mechanical checks, one fixed line per stage, the filing and the row total.

    A breach found by the checks ends the row with 11 and prints counts only. When the checks find none, the row
    is filed through pc_evidence.file_row with its registry entry, the last step; a refusal of the filing is its
    exit code and its fixed lines (nothing more is printed), and the raw files stay in the run root for a
    zero-token refile.

    The line `stage <name>: not run (NO-RESUME-LINE)` is printed for each stage of kind resume that did not run,
    so a spec without such a stage prints none.
    """
    blocked = breach_outcome(ctx, paths)
    if blocked is not None:
        return file_stop(ctx, entry, pc_evidence.REASON_BREACH, results[-1].name if results else "s1", blocked)
    lines: List[str] = []
    for result in results:
        turns = result.summary["num_turns"] if result.summary is not None else None
        lines.append(
            "stage %s: %s, %s turn(s), delta %s, cumulative %s"
            % (
                result.name,
                result.summary["subtype"] if result.summary is not None else "no-result",
                turns if isinstance(turns, int) and not isinstance(turns, bool) else "unknown",
                _cost_text(result.delta) or "unknown",
                _cost_text(result.cumulative) or "unknown",
            )
        )
    ran = frozenset(result.name for result in results)
    for stage in entry.stages:
        if stage.kind == "resume" and stage.name not in ran:
            lines.append("stage %s: not run (%s)" % (stage.name, MARKER_NONE))
    filed = pc_evidence.file_row(ctx, str(paths["run_root"]), spec=entry)
    if filed.code != pc_exitcodes.OK:
        return filed
    lines.extend(filed.lines)
    totals = _chain_totals(results)
    if any(total is None for total in totals):
        lines.append("row total: unknown (a result carried no cost)")
    else:
        lines.append("row total: %s USD" % format(pc_spend.row_total([t for t in totals if t is not None]), "f"))
    return pc_rows.RowOutcome(pc_exitcodes.OK, tuple(lines))


def run_row(ctx: pc_rows.RunContext, timeout_override: Optional[int] = None) -> pc_rows.RowOutcome:
    """Run row 1: the registered chain of the row 1 entry (D-01, D-02, D-12, D-14).

    A thin wrapper over run_registered_row; its signature and its return type are the Phase 3 ones. The order
    of refusals, the stage walk and the filing are described there: an existing row folder (17, nothing created),
    the run root, the sanitizer and the deny entries (15), the readable ledger, the seed, then s1, s2 resumed on
    that session and s3 in a second fresh session whose prompt is the resume line, only when s2 printed one.
    """
    return run_registered_row(ctx, ROW_ID, timeout_override)


# ---------------------------------------------------------------------------------------------
# The chain of any registered row (plan 04-01)
# ---------------------------------------------------------------------------------------------


def read_prompts(repo_root: str, entry: pc_rows.RowSpec, ledger_a_path: Optional[str]) -> Dict[str, str]:
    """Return the prompt of each stage the entry names, read in place from its repo-relative file.

    A committed prompt is never copied, so its bytes are the committed bytes. The ledger placeholder of a prompt is
    replaced by the ledger A path when the run has a ledger A; a run without one leaves the text as it is.
    """
    found: Dict[str, str] = {}
    for name, relative in entry.prompts:
        text = _read(os.path.join(repo_root, *relative.split("/"))).decode("utf-8")
        if ledger_a_path:
            text = text.replace(LEDGER_PLACEHOLDER, ledger_a_path)
        found[name] = text
    return found


def _resolve_seed(seed: Any) -> Any:
    """Return the callable a registry entry names as its seed ("module:function" is imported lazily)."""
    if callable(seed):
        return seed
    if isinstance(seed, str):
        module_name, _, function_name = seed.partition(":")
        try:
            found = getattr(importlib.import_module(module_name), function_name)
        except (ImportError, AttributeError, ValueError):
            found = None
        if callable(found):
            return found
    raise pc_spike.SpikeError("the row has no usable seed")


SCOPE_RECORD = "scope.json"


def _write_scope(paths: Mapping[str, Optional[str]], ctx: pc_rows.RunContext) -> None:
    """Record the campaign, the attempt and the matrix flag of a run whose scope is not the Phase 3 default.

    The record is written in raw before the setup snapshot, so the setup guard holds it and a later refile finds the
    dated folder and the row folder this run belongs to. A default-scope run writes nothing.
    """
    if ctx.campaign is None and ctx.attempt == 1 and not ctx.matrix:
        return
    record = {"attempt": ctx.attempt, "campaign": ctx.campaign, "matrix": bool(ctx.matrix)}
    pc_runroot.write_exclusive(
        os.path.join(str(paths["raw"]), SCOPE_RECORD),
        (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o600,
    )


def _settled_spend(ctx: pc_rows.RunContext, entry: pc_rows.RowSpec) -> Optional[Decimal]:
    """What the ledger holds for this row under this scope: a settled attempt counts its delta, an unsettled one its cap."""
    try:
        ledger_row = pc_rows.scoped_row(entry.row_id, ctx.campaign, ctx.attempt, ctx.matrix)
        return pc_spend.row_pessimistic_total(ctx.harness_home, ledger_row)
    except (pc_spend.SpendError, ValueError):
        return None


def run_registered_row(
    ctx: pc_rows.RunContext, row_id: str, timeout_override: Optional[int] = None
) -> pc_rows.RowOutcome:
    """Run one registered row (see _run_registered_row) and report what it spent in RowOutcome.spent.

    The figure is read from the spend ledger under the row's scoped id once the chain has ended, whatever the
    outcome: the pessimistic total of the ledger, so a stage that timed out or returned no cost counts its cap.
    An outcome of a run that never reached the ledger reports zero.
    """
    outcome = _run_registered_row(ctx, row_id, timeout_override)
    entry = _entry_of(row_id)
    spent = _settled_spend(ctx, entry)
    return outcome._replace(spent=spent if spent is not None else Decimal("0"))


def _run_registered_row(
    ctx: pc_rows.RunContext, row_id: str, timeout_override: Optional[int] = None
) -> pc_rows.RowOutcome:
    """Run one registered row from its registry entry alone: refusals first, then seed, snapshot 0 and the chain.

    The entry is found by exact registry match before any path is built: an id that is not an implemented
    registry id, with a seed, raises SpikeError and nothing is created. The row folder name is the entry's id,
    never caller text. Order before any ledger line: an existing row folder under ctx.destination (the entry's id,
    or its id and -attempt-N for an attempt above 1; 17, nothing created; an existing dated folder is fine, two rows
    share it), the run root (a taken name raises
    RunRootCollision, the driver's 16), the sanitizer and the deny entries (15), the readable ledger, the seed and
    the version control tool.

    The stages are walked in the entry's order. A stage whose session is new:K starts a session (the first one is
    the session the seed bound the ledger to, the others get a fresh UUID); a stage whose session is resume:K
    continues the session kept under K with the resume flag and the cumulative total of that session. The prompt
    of a stage is the file the entry names for it; a stage of kind resume without one takes the resume line the
    last /preclear turn printed, and the chain ends there when none was printed. The chain stops at the first
    stage that is not a clean success. The allowlist comes from the entry's profile.
    """
    entry = _entry_of(row_id)
    if entry.seed is None:
        raise pc_spike.SpikeError("the row is not in the registry")
    seed = _resolve_seed(entry.seed)
    if os.path.lexists(os.path.join(ctx.destination, pc_rows.row_folder_name(entry.row_id, ctx.attempt))):
        return pc_rows.RowOutcome(pc_exitcodes.PROMOTE_REFUSED, (MESSAGE_ROW_FOLDER,))
    scoped = pc_rows.scoped_row(entry.row_id, ctx.campaign, ctx.attempt, ctx.matrix)
    run_name = "%s-%s" % (scoped, _utc_now().strftime("%Y%m%dT%H%M%SZ"))
    pc_spike.ensure_runs_root(ctx.runs_root)
    run_root = pc_runroot.allocate_run_root(ctx.runs_root, run_name)
    provisional = {"run_root": run_root, "auto_memory": os.path.join(run_root, "auto-memory")}
    try:
        sanitizer = pc_sanitize.Sanitizer.from_machine(ctx.repo_root, caller_map(provisional, ctx.runs_root))
        deny_entries = sanitizer.deny_entries()
    except (pc_sanitize.SanitizerError, pc_leakgate.ScannerError):
        return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_SANITIZER,))
    ctx = ctx._replace(run_root=run_root, sanitizer=sanitizer, deny_entries=deny_entries)
    pc_spend.read_records(ctx.harness_home)
    vcs = _git_executable(ctx.env)
    session = str(uuid.uuid4())
    paths = seed(ctx.repo_root, run_root, session, ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model)
    _write_scope(paths, ctx)
    take_snapshot(paths, SNAPSHOT_SETUP, vcs, setup=True)
    ctx = ctx._replace(setup_pin=pc_checks.capture_boundary_state(paths, pc_checks.SETUP_STATE, vcs, None))
    pc_checks.capture_guard(paths, pc_checks.SETUP_STATE)
    ledger_a = str(paths["ledger_a"]) if paths.get("ledger_a") and os.path.isfile(str(paths["ledger_a"])) else None
    prompts = read_prompts(ctx.repo_root, entry, ledger_a)

    results: List[StageResult] = []
    sessions: Dict[str, str] = {}
    totals: Dict[str, Optional[Decimal]] = {}
    resume_line = ""
    scan = BinaryScan(str(ctx.claude))
    for stage in entry.stages:
        timeout = timeout_override if timeout_override is not None else stage.timeout
        boundary = results[-1].hooklog_lines if results else 0
        if stage.name in prompts:
            prompt = prompts[stage.name]
        elif stage.kind == "resume":
            if not resume_line:
                break
            prompt = resume_line
        else:
            raise pc_spike.SpikeError("a stage of the row has no prompt")
        mode, _, key = stage.session.partition(":")
        if mode == "new":
            if not sessions:
                session_id = session
            else:
                session_id = str(uuid.uuid4())
                while session_id in sessions.values():
                    session_id = str(uuid.uuid4())
            sessions[key] = session_id
            resume = False
            previous: Optional[Decimal] = None
        elif mode == "resume" and key in sessions:
            session_id = sessions[key]
            resume = True
            previous = totals.get(key)
        else:
            raise pc_spike.SpikeError("a stage of the row names a session that was not started")
        try:
            result = run_stage(ctx, paths, stage, session_id, prompt, resume, previous, timeout, boundary, scan, entry)
        except pc_checks.CheckError:
            # The stage ran and was settled, but the run's own isolation record (the git pin) could not be read
            # for its snapshot: the checks cannot run, which is a breach stop like an unreadable run root.
            return file_stop(
                ctx,
                entry,
                pc_evidence.REASON_BREACH,
                stage.name,
                pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_RECORD_UNREADABLE % stage.name,)),
            )
        totals[key] = result.cumulative
        results.append(result)
        blocked = breach_outcome(ctx, paths)
        if blocked is not None:
            extra = () if result.ok else _stopped(stage.name, result.problem).lines
            return file_stop(
                ctx,
                entry,
                pc_evidence.REASON_BREACH,
                stage.name,
                pc_rows.RowOutcome(blocked.code, tuple(blocked.lines) + tuple(extra)),
            )
        if not result.ok:
            subtype = result.summary.get("subtype") if result.summary is not None else ""
            return file_stop(
                ctx,
                entry,
                pc_evidence.stop_reason(result.problem, subtype),
                stage.name,
                _stopped(stage.name, result.problem),
            )
        if result.evaluation is not None and result.evaluation.status != STATUS_PASS:
            return file_stop(
                ctx,
                entry,
                pc_evidence.REASON_ISOLATION,
                stage.name,
                _isolation_stop(stage.name, result.evaluation),
            )
        if stage.kind == "preclear":
            resume_line = extract_resume_line(_result_text(result))
            _write_chain(paths, resume_line)
    return finish(ctx, paths, results, entry)
