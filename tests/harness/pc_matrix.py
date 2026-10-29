"""The matrix driver: the one command that lists, plans and runs acceptance rows (HARN-01, HARN-02).

Run it as python3 -E -s -B pc_matrix.py, never with -I, because the pc_ modules import each other.

    --list                  every layout and row, layouts first, then rows in acceptance order,
                            one fixed-column line each: kind, id, stages, sessions, implemented
    --row ID                one row, by its exact id
    --layout NAME           one layout, by its exact name
    --all                   every implemented row, in registry order
    --dry-run               print the plan (stages, sessions, turns, caps, worst case, allowlist
                            size, model, destination), then run the claude-free gate; start no
                            process of any kind and write nothing
    --claude PATH           the absolute path of the claude executable (D-13); it feeds the
                            preflight, the argument vector and the binary scan from one path
    --budget AMOUNT         the most the caller allows a real run to cost; it must be at least the
                            worst case the plan prints, or the run is refused with exit 18
    --authorize-retry STAGE append one retry authorization line for a stage that was attempted (a
                            stage key such as row1-s2); a second attempt of a stage never starts
                            without it. Starts no process. A person types it; no task runs it.
    --refile RUNROOT        repeat the checks and the filing for a run folder, for zero
                            tokens: no claude, no budget, no ledger line. The destination comes from
                            the evidence date and model recorded in the run folder.

Exactly one of --list, --row, --layout, --all, --authorize-retry and --refile is given. An id is matched whole and exactly
against the registry before it is used for anything; an unknown or unimplemented id exits 2 with
fixed text that never repeats the value.

The claude-free gate (no process): the runs root is outside every home folder (BLOCKED 12), every
row source exists (FAIL 11), the evidence destination does not exist (17, never reused, D-05), and
the row's precondition holds (a reason is SKIP 10, printed as SKIPPED). A real run then checks the
budget, the checkpoint stub and the strict preflight, and only then hands the row to its runner.
BLOCKED and untested-version results print a one-line fix that equals a README bullet.

Messages are fixed text: counts, row ids, stage ids and README-listed fix lines only, never an
argument, a path, a host name or the login. The driver prints no verdict for a row.
"""
from __future__ import annotations

import argparse
import datetime
import importlib
import os
import subprocess
import sys
from decimal import ROUND_UP, Decimal
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, TextIO, Tuple

import pc_evidence
import pc_exitcodes
import pc_flags
import pc_leakgate
import pc_preflight
import pc_rows
import pc_runroot
import pc_sanitize
import pc_spend
import pc_spike
import pc_stream

PROG = "pc_matrix.py"
USAGE_LINE = (
    "usage: pc_matrix.py (--list | --row ID | --layout NAME | --all | --authorize-retry STAGE | --refile RUNROOT) "
    "[--dry-run] [--claude PATH] [--budget AMOUNT]"
)
ALLOWLIST_ROLE_WRAPPER = "/role/wrapper/checkpoint"
STUB_TIMEOUT_SECONDS = 20
CONFIG_TOKEN = "<config>"

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

MESSAGE_USAGE = "invalid command line"
MESSAGE_UNKNOWN_ROW = "unknown row id"
MESSAGE_UNKNOWN_LAYOUT = "unknown layout name"
MESSAGE_NOT_IMPLEMENTED = "that entry is not implemented in this phase"
MESSAGE_NEEDS_BUDGET = "a real run needs --budget at least the worst case printed above"
MESSAGE_BAD_BUDGET = "the budget is not an amount like 2.00 within the allowed range"
MESSAGE_SHORT_BUDGET = "the budget is below the worst case printed above"
MESSAGE_NOTHING_TO_RUN = "no implemented row was selected, so nothing was run"
MESSAGE_UNKNOWN_STAGE = "unknown stage key"
MESSAGE_NOT_ATTEMPTED = "that stage has not been attempted"
MESSAGE_RUN_FOLDER = "the run folder is not usable"
MESSAGE_REFILE_BREACH = "the refile files nothing"

# One line per BLOCKED cause. Each equals a README bullet of the form "- `cause`: line" byte for
# byte (test_matrix_preflight compares them). The angle token is replaced by the harness config
# folder only when the line is printed, never in the README.
BLOCKED_FIXES: Dict[str, str] = {
    "no-claude": "install Claude Code, or pass the absolute path of a tested build with --claude",
    "logged-out": (
        "run this once in your own terminal, then rerun: CLAUDE_CONFIG_DIR=" + CONFIG_TOKEN + " claude auth login"
    ),
    "untested-version": (
        "pass --claude with the absolute path of a tested build, or seed this build by rerunning the spikes "
        "on it as described under Spike spend and adding its version to the tested set in pc_flags.py"
    ),
    "runs-root": (
        "set PRECLEAR_RUNS_ROOT to an absolute folder outside every home folder and the repository whose "
        "parents hold no instruction file"
    ),
    "stub-unreachable": (
        "the checkpoint stub could not be started: check that python3 3.9 or newer runs the stub with --version"
    ),
}

# The short fixed text printed after a state label for each cause.
STATE_LINES: Dict[str, str] = {
    "no-claude": "claude was not found, or the given path is not an absolute path to an executable file",
    "logged-out": "the harness config folder is not logged in",
    "no-config": "the harness config folder has no login yet",
    "untested-version": "this Claude Code build is not in the tested set",
    "runs-root": "the runs root is unusable",
    "stub-unreachable": "the checkpoint stub could not be started",
    "harness-home": "the harness home folder is unusable",
    "malformed": "claude answered with an unusable result",
    "unusable": "claude could not be asked, or the config folder was refused",
}

# Which BLOCKED_FIXES line a cause prints.
_FIX_OF_CAUSE: Dict[str, str] = {
    "no-claude": "no-claude",
    "logged-out": "logged-out",
    "no-config": "logged-out",
    "untested-version": "untested-version",
    "runs-root": "runs-root",
    "stub-unreachable": "stub-unreachable",
}


class GateResult(NamedTuple):
    """The outcome of a claude-free check: an exit code, a state label, the lines to print, a cause."""

    code: int
    state: str
    lines: Tuple[str, ...]
    cause: Optional[str] = None


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


def _write(stream: TextIO, text: str) -> None:
    stream.write(text)
    stream.flush()


def build_parser(out: TextIO, err: TextIO) -> argparse.ArgumentParser:
    parser = _Parser(out, err)
    parser.add_argument("--list", action="store_true", dest="list_all")
    parser.add_argument("--row", default=None)
    parser.add_argument("--layout", default=None)
    parser.add_argument("--all", action="store_true", dest="all_rows")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("--claude", default=None)
    parser.add_argument("--budget", default=None)
    parser.add_argument("--authorize-retry", default=None, dest="authorize_retry")
    parser.add_argument("--refile", default=None)
    return parser


def _money_up(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_UP), "f")


# ---------------------------------------------------------------------------------------------
# The list and the plan (no file access, no process)
# ---------------------------------------------------------------------------------------------


def list_lines(registry: Sequence[pc_rows.RowSpec]) -> List[str]:
    """Return the header and one fixed-column line per entry, layouts first (registry order)."""
    template = "%-6s %-28s %6s %8s %s"
    lines = [template % ("kind", "id", "stages", "sessions", "implemented")]
    for entry in registry:
        if entry.implemented:
            stages = str(len(entry.stages))
            sessions = str(pc_rows.session_count(entry))
        else:
            stages = "-"
            sessions = "-"
        lines.append(template % (entry.kind, entry.row_id, stages, sessions, "yes" if entry.implemented else "no"))
    return lines


def _allowlist_size() -> int:
    tools = pc_flags.build_allowed_tools(ALLOWLIST_ROLE_WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    return len(tools)


def _stage_words(row: pc_rows.RowSpec, stage: pc_rows.StageSpec) -> str:
    if stage.session.startswith("resume:"):
        key = "new:" + stage.session.split(":", 1)[1]
        origin = [other.name for other in row.stages if other.session == key]
        session = "resumes the %s session" % origin[0] if origin else "resumes an earlier session"
    else:
        session = "new session"
    return "%s, %s, %d turns, cap %s" % (stage.work, session, stage.max_turns, format(stage.cap, "f"))


def plan_lines(row: pc_rows.RowSpec, evidence_date: str, model: str = pc_flags.PINNED_MODEL) -> List[str]:
    """Return the dry-run text for one implemented row. It reads nothing and starts nothing."""
    lines = ["%s: %d stages, %d sessions" % (row.row_id, len(row.stages), pc_rows.session_count(row))]
    for stage in row.stages:
        lines.append("  %s: %s" % (stage.name, _stage_words(row, stage)))
    lines.append("worst case %s USD" % _money_up(pc_rows.worst_case(row)))
    lines.append("allowlist %d rules" % _allowlist_size())
    lines.append("model %s" % model)
    lines.append("destination tests/evidence/%s" % pc_rows.evidence_folder_name(evidence_date, model))
    return lines


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _usage(err: TextIO) -> int:
    _write(err, USAGE_LINE + "\n")
    _write(err, "%s: error: %s\n" % (PROG, MESSAGE_USAGE))
    return pc_exitcodes.USAGE


def _refuse(err: TextIO, message: str, code: int = pc_exitcodes.USAGE) -> int:
    _write(err, "%s: %s\n" % (PROG, message))
    return code


def _select_entries(
    args: argparse.Namespace, registry: Sequence[pc_rows.RowSpec], err: TextIO
) -> Tuple[Optional[List[pc_rows.RowSpec]], int]:
    """Resolve the selection to registry entries; the second item is an exit code when it is refused."""
    if args.all_rows:
        return [entry for entry in registry if entry.implemented], pc_exitcodes.OK
    if args.row is not None:
        kind, unknown = pc_rows.KIND_ROW, MESSAGE_UNKNOWN_ROW
        text = args.row
    else:
        kind, unknown = pc_rows.KIND_LAYOUT, MESSAGE_UNKNOWN_LAYOUT
        text = args.layout
    entry = pc_rows.find_entry(registry, kind, text) if pc_rows.is_valid_id(text) else None
    if entry is None:
        return None, _refuse(err, unknown)
    if not entry.implemented:
        return None, _refuse(err, MESSAGE_NOT_IMPLEMENTED)
    return [entry], pc_exitcodes.OK


def _print_plans(
    args: argparse.Namespace,
    registry: Sequence[pc_rows.RowSpec],
    chosen: Sequence[pc_rows.RowSpec],
    evidence_date: str,
    out: TextIO,
) -> None:
    if args.all_rows:
        for entry in registry:
            if entry.implemented:
                for line in plan_lines(entry, evidence_date):
                    _write(out, line + "\n")
            else:
                _write(out, "%s: not implemented\n" % entry.row_id)
    else:
        for entry in chosen:
            for line in plan_lines(entry, evidence_date):
                _write(out, line + "\n")
    if args.all_rows:
        stages = sum(len(entry.stages) for entry in chosen)
        sessions = sum(pc_rows.session_count(entry) for entry in chosen)
        _write(
            out,
            "total: %d row(s), %d stage(s), %d session(s), worst case %s USD\n"
            % (len(chosen), stages, sessions, _money_up(_total_worst_case(chosen))),
        )


def _total_worst_case(chosen: Sequence[pc_rows.RowSpec]) -> Decimal:
    total = Decimal("0")
    for entry in chosen:
        total += pc_rows.worst_case(entry)
    return total


# ---------------------------------------------------------------------------------------------
# The claude-free gate and the stub check (no claude, no model, no spend)
# ---------------------------------------------------------------------------------------------


def _blocked(cause: str, config_dir: Optional[str] = None) -> GateResult:
    """A BLOCKED result: the state line and the README-backed fix line for the cause."""
    lines = ["BLOCKED: %s" % STATE_LINES[cause]]
    fix = BLOCKED_FIXES.get(_FIX_OF_CAUSE.get(cause, ""))
    if fix is not None:
        if config_dir is not None:
            fix = fix.replace(CONFIG_TOKEN, config_dir)
        lines.append("fix: %s" % fix)
    return GateResult(pc_exitcodes.PREFLIGHT_BLOCKED, "BLOCKED", tuple(lines), cause)


def _destination_name(clock: Callable[[], datetime.datetime], model: str = pc_flags.PINNED_MODEL) -> str:
    return pc_rows.evidence_folder_name(clock().strftime("%Y-%m-%d"), model)


def _source_exists(repo_root: str, path: str, kind: str) -> bool:
    full = os.path.join(repo_root, *path.split("/"))
    return os.path.isdir(full) if kind == "dir" else os.path.isfile(full)


def gate(
    row: pc_rows.RowSpec,
    repo_root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    registry: Optional[Sequence[pc_rows.RowSpec]] = None,
) -> GateResult:
    """Run the claude-free checks for one row, in order, with no process and no write.

    1. the runs root is outside every home folder, the repository and the user's own Claude folder
       (BLOCKED 12, cause runs-root; the driver, not pc_spike, owns this mapping)
    2. every source the row declares exists (FAIL 11, naming only the repo-relative source)
    3. tests/evidence is a real folder and the destination name is free (17; a name that exists,
       a dangling symlink included, is refused, never reused, D-05)
    4. the row's precondition (a reason is SKIP 10, printed as SKIPPED)

    The registry argument is accepted for symmetry with the other entry points; the row carries
    everything the gate reads.
    """
    try:
        pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=repo_root)
    except pc_spike.HomeRefused:
        return _blocked("runs-root")
    for path, kind in row.sources:
        if not _source_exists(repo_root, path, kind):
            return GateResult(
                pc_exitcodes.PREFLIGHT_FAIL,
                "FAIL",
                ("FAIL: a row source is missing: %s" % path,),
                "missing-source",
            )
    evidence = os.path.join(repo_root, "tests", "evidence")
    if not os.path.isdir(evidence) or os.path.islink(evidence):
        return GateResult(
            pc_exitcodes.PREFLIGHT_FAIL,
            "FAIL",
            ("FAIL: the evidence folder is missing",),
            "missing-evidence",
        )
    name = _destination_name(clock)
    if os.path.lexists(os.path.join(evidence, name)):
        return GateResult(
            pc_exitcodes.PROMOTE_REFUSED,
            "REFUSED",
            ("REFUSED: the evidence folder %s already exists; a folder is never reused" % name,),
            "destination-taken",
        )
    if row.precondition is not None:
        reason = row.precondition()
        if reason is not None:
            return GateResult(pc_exitcodes.PREFLIGHT_SKIP, "SKIP", ("SKIPPED: %s" % reason,), "precondition")
    return GateResult(
        pc_exitcodes.OK,
        "OK",
        ("gate ok: the runs root, the row sources and the destination name are usable",),
    )


def check_stub(repo_root: str, env: Optional[Mapping[str, str]] = None) -> GateResult:
    """Run the checkpoint stub with --version and no CKPT_HOME; BLOCKED 12 when it cannot start."""
    stub = os.path.join(repo_root, "tests", "harness", "checkpoint_stub.py")
    if not os.path.isfile(stub) or os.path.getsize(stub) == 0:
        return _blocked("stub-unreachable")
    try:
        child_env = pc_flags.build_env(os.environ if env is None else env, None)
        done = subprocess.run(
            [sys.executable, "-I", "-B", stub, "--version"],
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=STUB_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _blocked("stub-unreachable")
    if done.returncode != 0:
        return _blocked("stub-unreachable")
    return GateResult(pc_exitcodes.OK, "OK", ("stub ok",))


# ---------------------------------------------------------------------------------------------
# The budget, the row runner and its exception mapping
# ---------------------------------------------------------------------------------------------


def _check_budget(text: str, needed: Decimal, err: TextIO) -> Tuple[Optional[Decimal], int]:
    """Return (amount, 0) when the budget is well formed and covers the worst case, else (None, 18)."""
    try:
        amount = Decimal(pc_flags.format_budget(text))
    except ValueError:
        return None, _refuse(err, MESSAGE_BAD_BUDGET, pc_exitcodes.BUDGET_REFUSED)
    if amount < needed:
        return None, _refuse(err, MESSAGE_SHORT_BUDGET, pc_exitcodes.BUDGET_REFUSED)
    return amount, pc_exitcodes.OK


_EXCEPTION_LINES: Tuple[Tuple[Any, int, str], ...] = (
    (pc_spike.BudgetRefused, pc_exitcodes.BUDGET_REFUSED, "BUDGET_REFUSED: the spend gate stopped this run"),
    (pc_spend.SpendRefused, pc_exitcodes.BUDGET_REFUSED, "BUDGET_REFUSED: the spend gate stopped this run"),
    (pc_spend.SpendError, pc_exitcodes.PREFLIGHT_FAIL, "FAIL: the spend ledger is unusable"),
    (pc_spike.HomeRefused, pc_exitcodes.PREFLIGHT_BLOCKED, "BLOCKED: the harness home or the runs root is unusable"),
    (pc_spike.LeakRefused, pc_exitcodes.LEAK_REFUSED, "LEAK_REFUSED: the leak gate refused"),
    (pc_spike.SpikeError, pc_exitcodes.PREFLIGHT_FAIL, "FAIL: the harness could not complete the row"),
    (pc_runroot.RunRootCollision, pc_exitcodes.RUNROOT_COLLISION, "RUNROOT_COLLISION: a run folder already exists"),
    (pc_runroot.RunRootError, pc_exitcodes.PREFLIGHT_FAIL, "FAIL: a run folder could not be created"),
    (pc_sanitize.SanitizerError, pc_exitcodes.SCANNER_ERROR, "SCANNER_ERROR: the sanitizer could not be built or applied"),
    (pc_leakgate.ScannerError, pc_exitcodes.SCANNER_ERROR, "SCANNER_ERROR: the leak scanner could not run"),
    (pc_stream.StreamError, pc_exitcodes.DENIAL_FOUND, "DENIAL_FOUND: the stream was incomplete or unreadable"),
    (ImportError, pc_exitcodes.PREFLIGHT_FAIL, "FAIL: the row runner is not available"),
)

_RUNNER_MISSING = "FAIL: the row runner is not available"
_RUNNER_BAD_RESULT = "FAIL: the row runner returned something other than an outcome"


def _resolve_runner(runner: Any) -> Optional[Callable[[pc_rows.RunContext], Any]]:
    """Return the callable named by a registry runner ("module:function" is imported lazily)."""
    if callable(runner):
        return runner  # type: ignore[no-any-return]
    if not isinstance(runner, str):
        return None
    module_name, _, function_name = runner.partition(":")
    try:
        module = importlib.import_module(module_name)
        found = getattr(module, function_name)
    except (ImportError, AttributeError, ValueError):
        return None
    return found if callable(found) else None


def _exception_code(problem: BaseException, err: TextIO) -> int:
    """Print the fixed line for an exception and return its exit code. The message and traceback are never printed."""
    for exception_type, code, line in _EXCEPTION_LINES:
        if isinstance(problem, exception_type):
            _write(err, line + "\n")
            return code
    _write(err, "FAIL: the row runner stopped unexpectedly\n")
    return pc_exitcodes.PREFLIGHT_FAIL


def execute_row(row: pc_rows.RowSpec, ctx: pc_rows.RunContext, out: TextIO, err: TextIO) -> int:
    """Hand one row to its runner and map the outcome or the exception to an exit code.

    The messages are fixed text; an exception's own message and any traceback are never printed.
    """
    runner = _resolve_runner(row.runner)
    if runner is None:
        _write(err, _RUNNER_MISSING + "\n")
        return pc_exitcodes.PREFLIGHT_FAIL
    try:
        outcome = runner(ctx)
    except Exception as problem:  # noqa: BLE001 - every failure must map to a fixed line and code
        return _exception_code(problem, err)
    if not isinstance(outcome, pc_rows.RowOutcome):
        _write(err, _RUNNER_BAD_RESULT + "\n")
        return pc_exitcodes.PREFLIGHT_FAIL
    for line in outcome.lines:
        _write(out, line + "\n")
    return int(outcome.code)


# ---------------------------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------------------------


def _print_result(result: GateResult, out: TextIO) -> None:
    for line in result.lines:
        _write(out, line + "\n")


def _run_gates(
    chosen: Sequence[pc_rows.RowSpec],
    repo_root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    registry: Sequence[pc_rows.RowSpec],
    out: TextIO,
) -> int:
    """Gate each selected row in order; stop at the first one that is not OK and return its code."""
    for entry in chosen:
        result = gate(entry, repo_root, env, clock, registry)
        _print_result(result, out)
        if result.code != pc_exitcodes.OK:
            return result.code
    return pc_exitcodes.OK


def _scratch_map(runs: str) -> Dict[str, str]:
    """The caller map for a filing that has no run root of its own: the runs root and its parents are scratch."""
    import pc_row1  # imported late: pc_row1 imports this module's siblings

    return pc_row1.caller_map({"run_root": os.path.join(runs, "placeholder"), "auto_memory": None}, runs)


def _config_dir_of(env: Mapping[str, str], root: str) -> Tuple[str, str]:
    """Return (harness home, harness config folder) as paths; nothing is created."""
    harness = pc_spike.harness_home(env, env.get("HOME") or None, root)
    return harness, os.path.join(harness, pc_spike.CONFIG_DIR_NAME)


def _file_skipped(
    entry: pc_rows.RowSpec,
    result: GateResult,
    root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    out: TextIO,
    err: TextIO,
) -> int:
    """File a SKIPPED label folder for a row whose precondition is not met and return the exit code.

    The code is 10 when the label is filed (a skip is never a success) and 14, 15, 17 or 11 when a step refuses.
    """
    reason = result.lines[0][len("SKIPPED: "):] if result.lines and result.lines[0].startswith("SKIPPED: ") else ""
    try:
        runs = pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=root)
        _harness, config_dir = _config_dir_of(env, root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    destination = os.path.join(root, "tests", "evidence", _destination_name(clock))
    try:
        sanitizer = pc_sanitize.Sanitizer.from_machine(root, _scratch_map(runs))
        deny_entries = sanitizer.deny_entries()
        outcome = pc_evidence.file_skipped(
            root, destination, entry.row_id, reason, sanitizer, deny_entries, config_dir, runs, clock
        )
    except Exception as problem:  # noqa: BLE001 - every failure must map to a fixed line and code
        return _exception_code(problem, err)
    for line in outcome.lines:
        _write(out, line + "\n")
    return int(outcome.code)


def _usable_run_folder(text: Any, runs: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Return (the run folder's realpath, its run record) when text names a row 1 run folder with a run record, else None.

    The run record, written at setup, is all that makes a folder usable here; whether the chain is complete and
    every stage clean is judged by the filing, which refuses an incomplete chain with exit 11.
    """
    import json

    if not isinstance(text, str) or text == "" or "\x00" in text or not os.path.isabs(text):
        return None
    if not os.path.isdir(text):
        return None
    real = os.path.realpath(text)
    if os.path.dirname(real) != runs:
        return None
    record_path = os.path.join(real, "raw", "run.json")
    try:
        with open(record_path, "rb") as handle:
            record = json.loads(handle.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("row") != pc_rows.ROW1:
        return None
    if not isinstance(record.get("evidence_date"), str) or not isinstance(record.get("model"), str):
        return None
    return real, record


def _refile(text: str, env: Mapping[str, str], root: str, out: TextIO, err: TextIO) -> int:
    """Repeat the checks and the filing for a run folder, for zero tokens (no claude, no ledger line).

    The destination is recomputed from the evidence date and the model recorded in the run folder, so a later day
    does not change it. A destination that exists is exit 17, a breach or an unreadable run folder is 11, and a
    folder that is not usable is 2. The same pc_evidence.file_row as a fresh run does the filing, and it also
    refuses (11, nothing created) a run whose chain stopped early or whose stage did not finish cleanly.
    """
    import pc_row1  # imported late: pc_row1 imports this module's siblings

    try:
        runs = pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=root)
    except pc_spike.HomeRefused:
        return _refuse(err, MESSAGE_RUN_FOLDER)
    found = _usable_run_folder(text, runs)
    if found is None:
        return _refuse(err, MESSAGE_RUN_FOLDER)
    run_root, record = found
    try:
        name = pc_rows.evidence_folder_name(record["evidence_date"], record["model"])
    except ValueError:
        return _refuse(err, MESSAGE_RUN_FOLDER)
    destination = os.path.join(root, "tests", "evidence", name)
    if os.path.lexists(destination):
        _write(out, "REFUSED: the evidence folder %s already exists; a folder is never reused\n" % name)
        return pc_exitcodes.PROMOTE_REFUSED
    try:
        harness, config_dir = _config_dir_of(env, root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    paths = pc_row1.paths_for(run_root)
    try:
        sanitizer = pc_sanitize.Sanitizer.from_machine(root, pc_row1.caller_map(paths, runs))
        deny_entries = sanitizer.deny_entries()
    except (pc_sanitize.SanitizerError, pc_leakgate.ScannerError):
        _write(out, pc_row1.MESSAGE_SANITIZER + "\n")
        return pc_exitcodes.SCANNER_ERROR
    ctx = pc_rows.RunContext(
        repo_root=root,
        env=dict(env),
        claude=None,
        harness_home=harness,
        config_dir=config_dir,
        runs_root=runs,
        run_root=run_root,
        destination=destination,
        evidence_date=record["evidence_date"],
        model=record["model"],
        sanitizer=sanitizer,
        deny_entries=deny_entries,
        budget=Decimal("0"),
        banner=None,
        version=None,
    )
    try:
        blocked = pc_row1.breach_outcome(ctx, paths)
        outcome = blocked if blocked is not None else pc_evidence.file_row(ctx, run_root)
    except Exception as problem:  # noqa: BLE001 - every failure must map to a fixed line and code
        return _exception_code(problem, err)
    for line in outcome.lines:
        _write(out, line + "\n")
    return int(outcome.code)


def _run_real_gates(
    chosen: Sequence[pc_rows.RowSpec],
    repo_root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    registry: Sequence[pc_rows.RowSpec],
    out: TextIO,
    err: TextIO,
) -> int:
    """Gate each selected row as a real run does: a row whose precondition is not met is filed as SKIPPED (D-10).

    Everything else is as _run_gates: stop at the first row that is not OK and return its code. A skip is exit 10
    and never 0, whether its label folder was filed or one of the filing steps refused.
    """
    for entry in chosen:
        result = gate(entry, repo_root, env, clock, registry)
        _print_result(result, out)
        if result.code == pc_exitcodes.PREFLIGHT_SKIP and result.cause == "precondition":
            return _file_skipped(entry, result, repo_root, env, clock, out, err)
        if result.code != pc_exitcodes.OK:
            return result.code
    return pc_exitcodes.OK


def _run_preflight(
    args: argparse.Namespace, env: Mapping[str, str], repo_root: str, out: TextIO
) -> Tuple[Optional[pc_preflight.PreflightResult], Optional[str], Optional[str], int]:
    """Return (result, harness home, config dir, exit code); a non-zero code means stop."""
    home_dir = env.get("HOME") or None
    try:
        harness_home = pc_spike.harness_home(env, home_dir, repo_root)
        config_dir, _created = pc_spike.ensure_config_dir(env, home_dir, repo_root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return None, None, None, pc_exitcodes.PREFLIGHT_BLOCKED
    search = env.get("PATH", "").split(os.pathsep) if env.get("PATH") else []
    result = pc_preflight.run_preflight(
        search_path=search,
        config_dir=config_dir,
        base_env=env,
        claude_path=args.claude,
    )
    if result.exit_code != pc_exitcodes.OK:
        cause = result.cause or "unusable"
        if result.state in (pc_preflight.BLOCKED, pc_preflight.UNTESTED):
            _print_result(_blocked(cause, config_dir), out)
        else:
            _write(out, "%s: %s\n" % (result.state, STATE_LINES.get(cause, STATE_LINES["unusable"])))
        return result, harness_home, config_dir, result.exit_code
    return result, harness_home, config_dir, pc_exitcodes.OK


def _stage_catalog(registry: Sequence[pc_rows.RowSpec]) -> Dict[str, Tuple[pc_rows.RowSpec, pc_rows.StageSpec]]:
    """Map every stage key of every implemented row (row1-s2) to its row and stage."""
    catalog: Dict[str, Tuple[pc_rows.RowSpec, pc_rows.StageSpec]] = {}
    for entry in registry:
        if entry.implemented:
            for stage in entry.stages:
                catalog[pc_rows.stage_key(entry.row_id, stage.name)] = (entry, stage)
    return catalog


def _authorize_retry(
    text: str,
    registry: Sequence[pc_rows.RowSpec],
    env: Mapping[str, str],
    repo_root: str,
    out: TextIO,
    err: TextIO,
) -> int:
    """Append one retry authorization line for an attempted stage. Starts no process."""
    catalog = _stage_catalog(registry)
    found = catalog.get(text) if pc_rows.is_valid_id(text) else None
    if found is None:
        return _refuse(err, MESSAGE_UNKNOWN_STAGE)
    entry, stage = found
    try:
        home = pc_spike.harness_home(env, env.get("HOME") or None, repo_root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    try:
        pc_spend.authorize_retry(home, entry.row_id, text, stage.cap, tuple(catalog))
    except pc_spend.StageNotAttempted:
        return _refuse(err, MESSAGE_NOT_ATTEMPTED)
    except pc_spend.SpendRefused:
        return _refuse(err, "the spend gate refused that authorization", pc_exitcodes.BUDGET_REFUSED)
    except pc_spend.SpendError:
        return _refuse(err, "the spend ledger is unusable", pc_exitcodes.PREFLIGHT_FAIL)
    _write(out, "authorized one more attempt of %s\n" % text)
    return pc_exitcodes.OK


def main(
    argv: Optional[Sequence[str]] = None,
    env: Optional[Mapping[str, str]] = None,
    repo_root: Optional[str] = None,
    registry: Optional[Sequence[pc_rows.RowSpec]] = None,
    clock: Optional[Callable[[], datetime.datetime]] = None,
    out: Optional[TextIO] = None,
    err: Optional[TextIO] = None,
) -> int:
    """Run the driver and return the exit code; this function never calls sys.exit."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = build_parser(out, err)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE

    selections = [
        args.list_all,
        args.row is not None,
        args.layout is not None,
        args.all_rows,
        args.authorize_retry is not None,
        args.refile is not None,
    ]
    if sum(1 for chosen_flag in selections if chosen_flag) != 1:
        return _usage(err)
    if args.dry_run and (args.list_all or args.authorize_retry is not None or args.refile is not None):
        return _usage(err)

    source: Mapping[str, str] = dict(os.environ) if env is None else env
    root = repo_root if repo_root else _REPO_ROOT
    now_of = clock or _utc_now
    entries = pc_rows.build_registry() if registry is None else tuple(registry)
    if args.list_all:
        for line in list_lines(entries):
            _write(out, line + "\n")
        return pc_exitcodes.OK
    if args.authorize_retry is not None:
        return _authorize_retry(args.authorize_retry, entries, source, root, out, err)
    if args.refile is not None:
        return _refile(args.refile, source, root, out, err)

    chosen, refused = _select_entries(args, entries, err)
    if chosen is None:
        return refused
    evidence_date = now_of().strftime("%Y-%m-%d")
    _print_plans(args, entries, chosen, evidence_date, out)
    needed = _total_worst_case(chosen)

    if args.dry_run:
        if args.budget is not None:
            amount, code = _check_budget(args.budget, needed, err)
            if amount is None:
                return code
        return _run_gates(chosen, root, source, now_of, entries, out)

    code = _run_real_gates(chosen, root, source, now_of, entries, out, err)
    if code != pc_exitcodes.OK:
        return code
    if not chosen:
        _write(out, MESSAGE_NOTHING_TO_RUN + "\n")
        return pc_exitcodes.OK
    if args.budget is None:
        return _refuse(err, MESSAGE_NEEDS_BUDGET, pc_exitcodes.BUDGET_REFUSED)
    amount, code = _check_budget(args.budget, needed, err)
    if amount is None:
        return code

    stub = check_stub(root, source)
    if stub.code != pc_exitcodes.OK:
        _print_result(stub, out)
        return stub.code
    result, harness_home, config_dir, code = _run_preflight(args, source, root, out)
    if code != pc_exitcodes.OK or result is None or harness_home is None or config_dir is None:
        return code

    try:
        version: Optional[str] = pc_flags.parse_banner(result.banner or "")
    except ValueError:
        version = None
    destination = os.path.join(root, "tests", "evidence", pc_rows.evidence_folder_name(evidence_date, pc_flags.PINNED_MODEL))
    ctx = pc_rows.RunContext(
        repo_root=root,
        env=dict(source),
        claude=result.claude,
        harness_home=harness_home,
        config_dir=config_dir,
        runs_root=pc_spike.runs_root(source, home_dir=source.get("HOME") or None, repo_root=root),
        run_root=None,
        destination=destination,
        evidence_date=evidence_date,
        model=pc_flags.PINNED_MODEL,
        sanitizer=None,
        deny_entries=None,
        budget=amount,
        banner=result.banner,
        version=version,
    )
    for entry in chosen:
        code = execute_row(entry, ctx, out, err)
        if code != pc_exitcodes.OK:
            return code
    return pc_exitcodes.OK


if __name__ == "__main__":
    sys.exit(main())
