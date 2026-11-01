"""The matrix driver: the one command that lists, plans and runs acceptance rows (HARN-01, HARN-02).

Run it as python3 -E -s -B pc_matrix.py, never with -I, because the pc_ modules import each other.

    --list                  every layout and row, layouts first, then rows in acceptance order,
                            one fixed-column line each: kind, id, stages, sessions, implemented
    --row ID                one row, by its exact id; it may be repeated
    --layout NAME           one layout, by its exact name; it may be repeated and combined with --row
                            (the selected entries run in registry order, layouts first)
    --all                   every implemented row, in registry order
    --dry-run               print the plan (stages, sessions, turns, caps, worst case, allowlist
                            size, model, destination), then run the claude-free gate; start no
                            process of any kind and write nothing
    --claude PATH           the absolute path of the claude executable (D-13); it feeds the
                            preflight, the argument vector and the binary scan from one path
    --budget AMOUNT         the most the caller allows a real run to cost; it must be at least the
                            worst case the plan prints, or the run is refused with exit 18
    --campaign LABEL        name the dated folder rerun-<date>-<model>-<LABEL> and scope every ledger
                            identity and run folder with the label (one lowercase id, at most 24
                            characters, no part a1 to a9)
    --evidence-date DATE    use YYYY-MM-DD instead of today's UTC date in the dated folder name, so a
                            later retry files into the original folder; never a date after today
    --attempt N             retry one explicitly selected entry as attempt N (1 to 9): its row folder is
                            <row id>-attempt-N and its ledger identities are scoped with aN; it needs an
                            earlier attempt of the row on record in the ledger (exit 18 otherwise)
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
row source exists (FAIL 11), the row's folder in the evidence destination does not exist (17, never
reused, D-05; a dated folder that exists is fine, waves and retries share it), and the row's
precondition holds (a reason is SKIP 10, printed as SKIPPED). A real run then checks the budget, the
checkpoint stub and the strict preflight, and only then hands each row to its runner in registry
order. A row that is skipped (10), stopped (11) or has an incomplete stream (19) does not end the
invocation; a filing failure or refusal (14 to 18) does. The exit code is that ending code, else 19,
else 11, else 10, else 0, so a skipped row never reads as success.
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
    "[--dry-run] [--claude PATH] [--budget AMOUNT] [--campaign LABEL] [--evidence-date YYYY-MM-DD] [--attempt N]"
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
MESSAGE_BAD_CAMPAIGN = (
    "the campaign label is not one lowercase id of at most 24 characters without a part from a1 to a9"
)
MESSAGE_BAD_DATE = "the evidence date is not a calendar date like 2026-10-30 on or before today (UTC)"
MESSAGE_BAD_ATTEMPT = "the attempt is not a number from 1 to 9"
MESSAGE_ATTEMPT_WITH_ALL = "--attempt applies to exactly one selected entry"
MESSAGE_REPEATED = "an entry was selected more than once"
MESSAGE_NO_EARLIER_ATTEMPT = "that attempt needs an earlier attempt of the row on record in the spend ledger"
MESSAGE_LEDGER_UNUSABLE = "the spend ledger is unusable"

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
    parser.add_argument("--row", action="append", default=None)
    parser.add_argument("--layout", action="append", default=None)
    parser.add_argument("--all", action="store_true", dest="all_rows")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("--claude", default=None)
    parser.add_argument("--budget", default=None)
    parser.add_argument("--authorize-retry", default=None, dest="authorize_retry")
    parser.add_argument("--refile", default=None)
    parser.add_argument("--campaign", default=None)
    parser.add_argument("--evidence-date", default=None, dest="evidence_date")
    parser.add_argument("--attempt", default=None)
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


def plan_lines(
    row: pc_rows.RowSpec,
    evidence_date: str,
    model: str = pc_flags.PINNED_MODEL,
    campaign: Optional[str] = None,
    attempt: int = 1,
) -> List[str]:
    """Return the dry-run text for one implemented row. It reads nothing and starts nothing."""
    lines = ["%s: %d stages, %d sessions" % (row.row_id, len(row.stages), pc_rows.session_count(row))]
    for stage in row.stages:
        lines.append("  %s: %s" % (stage.name, _stage_words(row, stage)))
    lines.append("worst case %s USD" % _money_up(pc_rows.worst_case(row)))
    lines.append("allowlist %d rules" % _allowlist_size())
    lines.append("model %s" % model)
    lines.append("destination tests/evidence/%s" % pc_rows.evidence_folder_name(evidence_date, model, campaign))
    if attempt > 1:
        lines.append("row folder %s" % pc_rows.row_folder_name(row.row_id, attempt))
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
    """Resolve the selection to registry entries, in registry order; the second item is an exit code when refused.

    --row and --layout may each be repeated and combined: every id is matched whole and exactly against the
    registry, and an unknown, unimplemented or repeated id is refused with exit 2 and fixed text that never echoes
    it. The entries come back in registry order (layouts first, then the rows in acceptance order, D-12) whatever
    order the flags were typed in.
    """
    if args.all_rows:
        return [entry for entry in registry if entry.implemented], pc_exitcodes.OK
    wanted: List[Tuple[str, str]] = []
    for kind, texts, unknown in (
        (pc_rows.KIND_ROW, args.row, MESSAGE_UNKNOWN_ROW),
        (pc_rows.KIND_LAYOUT, args.layout, MESSAGE_UNKNOWN_LAYOUT),
    ):
        for text in texts or ():
            entry = pc_rows.find_entry(registry, kind, text)
            if entry is None:
                return None, _refuse(err, unknown)
            if not entry.implemented:
                return None, _refuse(err, MESSAGE_NOT_IMPLEMENTED)
            if (kind, entry.row_id) in wanted:
                return None, _refuse(err, MESSAGE_REPEATED)
            wanted.append((kind, entry.row_id))
    return [entry for entry in registry if (entry.kind, entry.row_id) in wanted], pc_exitcodes.OK


def _print_plans(
    args: argparse.Namespace,
    registry: Sequence[pc_rows.RowSpec],
    chosen: Sequence[pc_rows.RowSpec],
    evidence_date: str,
    out: TextIO,
    attempt: int = 1,
) -> None:
    if args.all_rows:
        for entry in registry:
            if entry.implemented:
                for line in plan_lines(entry, evidence_date, campaign=args.campaign, attempt=attempt):
                    _write(out, line + "\n")
            else:
                _write(out, "%s: not implemented\n" % entry.row_id)
    else:
        for entry in chosen:
            for line in plan_lines(entry, evidence_date, campaign=args.campaign, attempt=attempt):
                _write(out, line + "\n")
    if args.all_rows or len(chosen) > 1:
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


def _destination_name(
    clock: Callable[[], datetime.datetime],
    model: str = pc_flags.PINNED_MODEL,
    campaign: Optional[str] = None,
    evidence_date: Optional[str] = None,
) -> str:
    """The dated folder name: the evidence date given, else the clock's UTC date, then the model and the label."""
    date_text = evidence_date if evidence_date is not None else clock().strftime("%Y-%m-%d")
    return pc_rows.evidence_folder_name(date_text, model, campaign)


def _taken_label(dated: str, folder: str) -> Optional[str]:
    """The first of the row folder, its STOPPED- folder and its SKIPPED- folder that exists in the dated folder."""
    for label in (folder, pc_evidence.STOPPED_PREFIX + folder, pc_evidence.SKIPPED_PREFIX + folder):
        if os.path.lexists(os.path.join(dated, label)):
            return label
    return None


def _source_exists(repo_root: str, path: str, kind: str) -> bool:
    full = os.path.join(repo_root, *path.split("/"))
    return os.path.isdir(full) if kind == "dir" else os.path.isfile(full)


def gate(
    row: pc_rows.RowSpec,
    repo_root: str,
    env: Mapping[str, str],
    clock: Callable[[], datetime.datetime],
    registry: Optional[Sequence[pc_rows.RowSpec]] = None,
    campaign: Optional[str] = None,
    evidence_date: Optional[str] = None,
    attempt: int = 1,
) -> GateResult:
    """Run the claude-free checks for one row, in order, with no process and no write.

    1. the runs root is outside every home folder, the repository and the user's own Claude folder
       (BLOCKED 12, cause runs-root; the driver, not pc_spike, owns this mapping)
    2. every source the row declares exists (FAIL 11, naming only the repo-relative source)
    3. tests/evidence is a real folder and the row's folder is free inside the dated destination (17): the
       row folder, its STOPPED- folder and its SKIPPED- folder of the selected attempt, a dangling symlink
       included, are refused and never reused (D-05). A dated folder that already exists is fine, so waves
       and retries file into one dated folder; a dated name that is a link or a file is refused
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
    name = _destination_name(clock, campaign=campaign, evidence_date=evidence_date)
    dated = os.path.join(evidence, name)
    if os.path.islink(dated) or (os.path.lexists(dated) and not os.path.isdir(dated)):
        return GateResult(
            pc_exitcodes.PROMOTE_REFUSED,
            "REFUSED",
            ("REFUSED: the evidence folder %s is not a real folder; a folder is never reused" % name,),
            "destination-taken",
        )
    taken = _taken_label(dated, pc_rows.row_folder_name(row.row_id, attempt))
    if taken is not None:
        return GateResult(
            pc_exitcodes.PROMOTE_REFUSED,
            "REFUSED",
            ("REFUSED: the evidence folder %s already holds %s; a folder is never reused" % (name, taken),),
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
    return _execute(row, ctx, out, err)[0]


def _ledger_spent(row: pc_rows.RowSpec, ctx: pc_rows.RunContext) -> Decimal:
    """What the ledger holds for the row under the context's scope (a settled stage its delta, another its cap).

    A ledger that cannot be read counts the row's worst case: the figure only ever feeds a budget stop, so the
    pessimistic reading is the safe one.
    """
    try:
        ledger_row = pc_rows.scoped_row(row.row_id, ctx.campaign, ctx.attempt, ctx.matrix)
        return pc_spend.row_pessimistic_total(ctx.harness_home, ledger_row)
    except (pc_spend.SpendError, ValueError, TypeError, OSError):
        return pc_rows.worst_case(row)


def _execute(row: pc_rows.RowSpec, ctx: pc_rows.RunContext, out: TextIO, err: TextIO) -> Tuple[int, Decimal]:
    """Run one row and return (exit code, what it spent).

    The spent figure is the outcome's own when the runner reports one, else the ledger's reading for the row (zero for
    a row that never reached the ledger); a runner that raised or returned a non-outcome is read from the ledger too.
    """
    runner = _resolve_runner(row.runner)
    if runner is None:
        _write(err, _RUNNER_MISSING + "\n")
        return pc_exitcodes.PREFLIGHT_FAIL, Decimal("0")
    try:
        outcome = runner(ctx)
    except Exception as problem:  # noqa: BLE001 - every failure must map to a fixed line and code
        return _exception_code(problem, err), _ledger_spent(row, ctx)
    if not isinstance(outcome, pc_rows.RowOutcome):
        _write(err, _RUNNER_BAD_RESULT + "\n")
        return pc_exitcodes.PREFLIGHT_FAIL, _ledger_spent(row, ctx)
    for line in outcome.lines:
        _write(out, line + "\n")
    spent = outcome.spent if isinstance(outcome.spent, Decimal) else _ledger_spent(row, ctx)
    return int(outcome.code), spent


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
    campaign: Optional[str] = None,
    evidence_date: Optional[str] = None,
    attempt: int = 1,
) -> int:
    """Gate each selected row in order; stop at the first one that is not OK and return its code."""
    for entry in chosen:
        result = gate(entry, repo_root, env, clock, registry, campaign, evidence_date, attempt)
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
    campaign: Optional[str] = None,
    evidence_date: Optional[str] = None,
    attempt: int = 1,
) -> int:
    """File a SKIPPED label folder for a row whose precondition is not met and return the exit code.

    The label folder is SKIPPED- and the row's folder name of the selected attempt.

    The code is 10 when the label is filed (a skip is never a success) and 14, 15, 17 or 11 when a step refuses.
    """
    reason = result.lines[0][len("SKIPPED: "):] if result.lines and result.lines[0].startswith("SKIPPED: ") else ""
    try:
        runs = pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=root)
        _harness, config_dir = _config_dir_of(env, root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    destination = os.path.join(
        root, "tests", "evidence", _destination_name(clock, campaign=campaign, evidence_date=evidence_date)
    )
    try:
        sanitizer = pc_sanitize.Sanitizer.from_machine(root, _scratch_map(runs))
        deny_entries = sanitizer.deny_entries()
        outcome = pc_evidence.file_skipped(
            root,
            destination,
            entry.row_id,
            reason,
            sanitizer,
            deny_entries,
            config_dir,
            runs,
            clock,
            pc_rows.row_folder_name(entry.row_id, attempt),
        )
    except Exception as problem:  # noqa: BLE001 - every failure must map to a fixed line and code
        return _exception_code(problem, err)
    for line in outcome.lines:
        _write(out, line + "\n")
    return int(outcome.code)


def _scope_of(run_dir: str) -> Optional[Tuple[Optional[str], int, bool]]:
    """Return (campaign, attempt, matrix) of a run folder: the scope record when it holds one, else the defaults.

    A record that is not exactly the three expected keys with valid values makes the folder unusable (None).
    """
    import json

    import pc_row1  # imported late: pc_row1 imports this module's siblings

    path = os.path.join(run_dir, "raw", pc_row1.SCOPE_RECORD)
    if not os.path.lexists(path):
        return None, 1, False
    try:
        with open(path, "rb") as handle:
            record = json.loads(handle.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or sorted(record) != ["attempt", "campaign", "matrix"]:
        return None
    campaign, attempt, flag = record["campaign"], record["attempt"], record["matrix"]
    if campaign is not None and not pc_rows.is_valid_campaign(campaign):
        return None
    if type(attempt) is not int or not 1 <= attempt <= pc_rows.MAX_ATTEMPT or type(flag) is not bool:
        return None
    return campaign, attempt, flag


def _usable_run_folder(
    text: Any, runs: str
) -> Optional[Tuple[str, Dict[str, Any], Tuple[Optional[str], int, bool]]]:
    """Return (the run folder's realpath, its run record, its scope) when text names a run folder of any registered
    row that has a run record, else None.

    The row id of the record is matched exactly against the registry before it is used for anything. The run
    record, written at setup, is all that makes a folder usable here; whether the chain is complete and every stage
    clean is judged by the filing, which refuses an incomplete chain with exit 11.
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
    if not isinstance(record, dict):
        return None
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, record.get("row"))
    if entry is None or not entry.implemented:
        return None
    if not isinstance(record.get("evidence_date"), str) or not isinstance(record.get("model"), str):
        return None
    scope = _scope_of(real)
    if scope is None:
        return None
    return real, record, scope


def _refile(text: str, env: Mapping[str, str], root: str, out: TextIO, err: TextIO) -> int:
    """Repeat the checks and the filing for a run folder, for zero tokens (no claude, no ledger line).

    The destination is recomputed from the evidence date and the model recorded in the run folder and the campaign
    its scope record names, so a later day does not change it. A run folder of any registered row is usable. A row
    folder (or its STOPPED- or SKIPPED- label) that exists in the dated folder is exit 17, a breach or an unreadable
    run folder is 11, and a folder that is not usable is 2. The same pc_evidence.file_row as a fresh run does the filing, and it also
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
    run_root, record, (campaign, attempt, matrix_scope) = found
    try:
        name = pc_rows.evidence_folder_name(record["evidence_date"], record["model"], campaign)
        folder = pc_rows.row_folder_name(record["row"], attempt)
    except ValueError:
        return _refuse(err, MESSAGE_RUN_FOLDER)
    destination = os.path.join(root, "tests", "evidence", name)
    if os.path.islink(destination) or (os.path.lexists(destination) and not os.path.isdir(destination)):
        _write(out, "REFUSED: the evidence folder %s is not a real folder; a folder is never reused\n" % name)
        return pc_exitcodes.PROMOTE_REFUSED
    taken = _taken_label(destination, folder)
    if taken is not None:
        _write(out, "REFUSED: the evidence folder %s already holds %s; a folder is never reused\n" % (name, taken))
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
        campaign=campaign,
        attempt=attempt,
        matrix=matrix_scope,
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
    campaign: Optional[str] = None,
    evidence_date: Optional[str] = None,
    attempt: int = 1,
) -> Tuple[int, Dict[str, GateResult]]:
    """Gate every selected row as a real run does and return (exit code, the rows to skip by id).

    The gate lines print as in a dry run. A row whose precondition is not met is not the end of the invocation: it
    is carried into the loop as a skip (filed there as a SKIPPED label folder, D-10, and recorded as exit 10).
    Any other gate result that is not OK ends the invocation with its code before anything is spent.
    """
    skipped: Dict[str, GateResult] = {}
    for entry in chosen:
        result = gate(entry, repo_root, env, clock, registry, campaign, evidence_date, attempt)
        _print_result(result, out)
        if result.code == pc_exitcodes.PREFLIGHT_SKIP and result.cause == "precondition":
            skipped[entry.row_id] = result
            continue
        if result.code != pc_exitcodes.OK:
            return result.code, {}
    return pc_exitcodes.OK, skipped


class _Invocation(NamedTuple):
    """What the loop needs to file a skipped row: the repository, the environment, the clock and the scope."""

    root: str
    env: Mapping[str, str]
    clock: Callable[[], datetime.datetime]
    campaign: Optional[str]
    evidence_date: str
    attempt: int


# Row-level outcomes that do not end the invocation (D-02): a skip, a stopped row, an incomplete stream.
CONTINUE_CODES = (pc_exitcodes.PREFLIGHT_SKIP, pc_exitcodes.PREFLIGHT_FAIL, pc_exitcodes.DENIAL_FOUND)

_LABEL_FILED = "filed"
_LABEL_SKIPPED = "skipped"
_LABEL_STOPPED = "stopped"
_LABEL_REFUSED = "refused"


def _row_label(code: int) -> str:
    if code == pc_exitcodes.OK:
        return _LABEL_FILED
    if code == pc_exitcodes.PREFLIGHT_SKIP:
        return _LABEL_SKIPPED
    if code in (pc_exitcodes.PREFLIGHT_FAIL, pc_exitcodes.DENIAL_FOUND):
        return _LABEL_STOPPED
    return _LABEL_REFUSED


def summary_lines(
    outcomes: Sequence[Tuple[pc_rows.RowSpec, int, Decimal]], selected: int
) -> List[str]:
    """One fixed line per row that was handled, then the counts. Row ids that matched the registry, labels, exit
    codes and amounts only: no path, no session id, no value from the command line, and no verdict word."""
    lines = [
        "row %s: %s, exit %d, spent %s USD" % (entry.row_id, _row_label(code), code, _money_up(spent))
        for entry, code, spent in outcomes
    ]
    counts = {_LABEL_FILED: 0, _LABEL_SKIPPED: 0, _LABEL_STOPPED: 0, _LABEL_REFUSED: 0}
    for _entry, code, _spent in outcomes:
        counts[_row_label(code)] += 1
    lines.append(
        "summary: %d row(s) selected, %d filed, %d stopped, %d skipped, %d refused, %d not started"
        % (
            selected,
            counts[_LABEL_FILED],
            counts[_LABEL_STOPPED],
            counts[_LABEL_SKIPPED],
            counts[_LABEL_REFUSED],
            selected - len(outcomes),
        )
    )
    return lines


def _aggregate_code(outcomes: Sequence[Tuple[pc_rows.RowSpec, int, Decimal]], ending: Optional[int]) -> int:
    """The invocation's exit code: the ending code, else 19, else 11, else 10, else 0 (a skip never reads as success)."""
    if ending is not None:
        return ending
    codes = [code for _entry, code, _spent in outcomes]
    for wanted in (pc_exitcodes.DENIAL_FOUND, pc_exitcodes.PREFLIGHT_FAIL, pc_exitcodes.PREFLIGHT_SKIP):
        if wanted in codes:
            return wanted
    return pc_exitcodes.OK


def _run_rows(
    chosen: Sequence[pc_rows.RowSpec],
    skipped: Mapping[str, GateResult],
    ctx: Optional[pc_rows.RunContext],
    invocation: _Invocation,
    out: TextIO,
    err: TextIO,
) -> int:
    """Run the selected rows in order and return the invocation's exit code.

    A skipped row is filed as a SKIPPED label and recorded as exit 10; a row whose runner returns 10, 11 or 19 does
    not stop the loop; any other non-zero code (a filing failure or a refusal, 14 to 18) ends the invocation at
    once and later rows are not started. After the loop one line per handled row and the counts are printed.
    """
    outcomes: List[Tuple[pc_rows.RowSpec, int, Decimal]] = []
    ending: Optional[int] = None
    for entry in chosen:
        if entry.row_id in skipped:
            code = _file_skipped(
                entry,
                skipped[entry.row_id],
                invocation.root,
                invocation.env,
                invocation.clock,
                out,
                err,
                invocation.campaign,
                invocation.evidence_date,
                invocation.attempt,
            )
            spent = Decimal("0")
        elif ctx is None:
            code, spent = pc_exitcodes.PREFLIGHT_FAIL, Decimal("0")
        else:
            code, spent = _execute(entry, ctx, out, err)
        outcomes.append((entry, code, spent))
        if code != pc_exitcodes.OK and code not in CONTINUE_CODES:
            ending = code
            break
    for line in summary_lines(outcomes, len(chosen)):
        _write(out, line + "\n")
    return _aggregate_code(outcomes, ending)


def _check_earlier_attempt(
    entry: pc_rows.RowSpec,
    campaign: Optional[str],
    attempt: int,
    matrix_scope: bool,
    env: Mapping[str, str],
    root: str,
    out: TextIO,
    err: TextIO,
) -> int:
    """A retry needs an earlier attempt on record: a launch line of attempt N-1 of this row in the ledger (D-03).

    The ledger is only read. A harness home that cannot be used is BLOCKED 12, a ledger that cannot be read is 11,
    and a missing earlier attempt is 18 with fixed text. Nothing is created.
    """
    try:
        home = pc_spike.harness_home(env, env.get("HOME") or None, root)
    except pc_spike.HomeRefused:
        _print_result(_blocked("harness-home"), out)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    try:
        records = pc_spend.read_records(home)
        wanted = pc_rows.scoped_row(entry.row_id, campaign, attempt - 1, matrix_scope)
    except (pc_spend.SpendError, ValueError):
        return _refuse(err, MESSAGE_LEDGER_UNUSABLE, pc_exitcodes.PREFLIGHT_FAIL)
    for record in records:
        if record["kind"] == pc_spend.KIND_LAUNCH and record["row"] == wanted:
            return pc_exitcodes.OK
    return _refuse(err, MESSAGE_NO_EARLIER_ATTEMPT, pc_exitcodes.BUDGET_REFUSED)


def _parse_attempt(text: Optional[str]) -> Optional[int]:
    """The attempt number of a --attempt text (one digit from 1 to 9, no sign, no zero padding), else None."""
    if text is None or len(text) != 1 or text not in "123456789":
        return None
    return int(text)


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
        args.row is not None or args.layout is not None,
        args.all_rows,
        args.authorize_retry is not None,
        args.refile is not None,
    ]
    if sum(1 for chosen_flag in selections if chosen_flag) != 1:
        return _usage(err)
    if args.dry_run and (args.list_all or args.authorize_retry is not None or args.refile is not None):
        return _usage(err)
    if args.campaign is not None and not pc_rows.is_valid_campaign(args.campaign):
        return _refuse(err, MESSAGE_BAD_CAMPAIGN)
    scope_given = args.campaign is not None or args.evidence_date is not None or args.attempt is not None
    if scope_given and (args.list_all or args.authorize_retry is not None or args.refile is not None):
        return _usage(err)
    attempt = 1
    if args.attempt is not None:
        parsed_attempt = _parse_attempt(args.attempt)
        if parsed_attempt is None:
            return _refuse(err, MESSAGE_BAD_ATTEMPT)
        attempt = parsed_attempt

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

    now = now_of()
    if args.evidence_date is not None:
        try:
            wanted = pc_rows.parse_evidence_date(args.evidence_date)
        except ValueError:
            return _refuse(err, MESSAGE_BAD_DATE)
        today = (now.astimezone(datetime.timezone.utc) if now.tzinfo is not None else now).date()
        if wanted > today:
            return _refuse(err, MESSAGE_BAD_DATE)
    chosen, refused = _select_entries(args, entries, err)
    if chosen is None:
        return refused
    if args.attempt is not None and (args.all_rows or len(chosen) != 1):
        return _refuse(err, MESSAGE_ATTEMPT_WITH_ALL)
    evidence_date = args.evidence_date if args.evidence_date is not None else now.strftime("%Y-%m-%d")
    matrix_scope = bool(args.all_rows and args.campaign is None)
    _print_plans(args, entries, chosen, evidence_date, out, attempt)
    needed = _total_worst_case(chosen)

    if args.dry_run:
        if args.budget is not None:
            amount, code = _check_budget(args.budget, needed, err)
            if amount is None:
                return code
        return _run_gates(chosen, root, source, now_of, entries, out, args.campaign, evidence_date, attempt)

    if attempt > 1:
        code = _check_earlier_attempt(chosen[0], args.campaign, attempt, matrix_scope, source, root, out, err)
        if code != pc_exitcodes.OK:
            return code
    code, skipped = _run_real_gates(chosen, root, source, now_of, entries, out, args.campaign, evidence_date, attempt)
    if code != pc_exitcodes.OK:
        return code
    if not chosen:
        _write(out, MESSAGE_NOTHING_TO_RUN + "\n")
        return pc_exitcodes.OK
    invocation = _Invocation(root, source, now_of, args.campaign, evidence_date, attempt)
    runnable = [entry for entry in chosen if entry.row_id not in skipped]
    if not runnable:
        return _run_rows(chosen, skipped, None, invocation, out, err)

    if args.budget is None:
        return _refuse(err, MESSAGE_NEEDS_BUDGET, pc_exitcodes.BUDGET_REFUSED)
    amount, code = _check_budget(args.budget, _total_worst_case(runnable), err)
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
    destination = os.path.join(
        root, "tests", "evidence", pc_rows.evidence_folder_name(evidence_date, pc_flags.PINNED_MODEL, args.campaign)
    )
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
        campaign=args.campaign,
        attempt=attempt,
        matrix=matrix_scope,
    )
    return _run_rows(chosen, skipped, ctx, invocation, out, err)


if __name__ == "__main__":
    sys.exit(main())
