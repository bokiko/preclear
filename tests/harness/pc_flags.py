"""The pinned claude -p contract: one table, one call builder, one environment scrub (HARN-04).

Everything the harness decides about how claude is driven lives here and nowhere else:

  * FLAG_TABLE         every flag and environment variable, pinned or deliberately not pinned
  * build_argv         the argument list in one fixed order (the prompt goes to stdin, never argv)
  * build_env          a minimal allow-listed environment for the child (D-02, D-03)
  * build_allowed_tools  the allowlist: the committed row 10 rerun baseline plus per-verb
                       wrapper rules, never a bare wrapper prefix (HARN-06, STUB-06 first half)
  * render_settings    the settings dict for --settings
  * parse_banner, check_version  the exact-match version gate
  * format_budget      exact two-decimal budgets (D-04)

Standard library only, Python 3.9 floor. No function here starts a process.
"""
from __future__ import annotations

import os
import re
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

PINNED_MODEL = "claude-sonnet-5-5"  # D-05: the full id; aliases move.
PERMISSION_MODE = "default"
SETTING_SOURCES = "project,local"

# Documented floor: every capability the harness relies on exists from this version on.
VERSION_FLOOR = (2, 1, 302)

# The build the committed publication evidence was produced with. Documentation only: it is
# never a tested version, because the new harness has not driven it.
COMMITTED_EVIDENCE_VERSION = "2.1.304"

# The exact-match set of versions the new harness has actually run against. It was seeded from the
# S2 capture of plan 02-08 (FA-5): claude --version and init.claude_code_version of the S1, S2a and
# S2b captures all reported this one build. Tests inject their own set.
TESTED_VERSIONS: Tuple[str, ...] = ("2.1.310",)

ISOLATION_CLAIM = (
    "Isolation claim: strict. Each matrix run uses a harness-owned CLAUDE_CONFIG_DIR outside "
    "the repository and outside the user's own Claude config, plus --setting-sources "
    "project,local, so user-level instructions, memory and skills are absent from the run."
)

PINNED = "PINNED"
ADDED = "ADDED"
NOT_PINNED = "NOT_PINNED"

# Row 10 rerun allowlist, verbatim and in file order (FA-4). The rules for env, python3 -c,
# mkdir and cd stay so reruns remain row-for-row comparable; narrowing any of them is a
# per-row decision for a later phase and would start a new baseline.
BASELINE_ALLOWED_TOOLS: Tuple[str, ...] = (
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash(git status:*)",
    "Bash(git rev-parse:*)",
    "Bash(git branch:*)",
    "Bash(git log:*)",
    "Bash(git diff:*)",
    "Bash(git symbolic-ref:*)",
    "Bash(wc:*)",
    "Bash(shasum:*)",
    "Bash(ls:*)",
    "Bash(find:*)",
    "Bash(cat:*)",
    "Bash(realpath:*)",
    "Bash(pwd)",
    "Bash(mkdir:*)",
    "Bash(printf:*)",
    "Bash(head:*)",
    "Bash(sed -n:*)",
    "Bash(awk:*)",
    "Bash(cd:*)",
    "Bash(date:*)",
    "Bash(python3 -c:*)",
    "Bash(env:*)",
    "Bash(git worktree list:*)",
    "Bash(git show:*)",
    "Bash(git ls-files:*)",
    "Bash(git --no-optional-locks status:*)",
    "Bash(git --no-optional-locks rev-parse:*)",
    "Bash(pwd -P)",
)

# Wrapper verbs the model may call, one rule each. Driver-only verbs are never allowed.
MODEL_FACING_WRAPPER_VERBS: Tuple[str, ...] = (
    "status",
    "show",
    "validate",
    "update",
    "note",
    "lint",
    "handoff",
)
DRIVER_ONLY_VERBS: Tuple[str, ...] = ("bind", "create", "init")

_ENV_ALLOW_LIST = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TERM",
)

_MAX_BUDGET = Decimal("5.00")
_BUDGET_TEXT = re.compile(r"[0-9]+(?:\.[0-9]{1,2})?\Z")
_BANNER = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+) \(Claude Code\)\n?\Z")

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class FlagRow(NamedTuple):
    name: str
    value: str
    status: str
    rationale: str
    source: str
    confirmed_by: str


def _row(name: str, value: str, status: str, rationale: str, source: str) -> FlagRow:
    # confirmed_by stays "research" until plan 02-08 confirms or removes the row from a live run.
    return FlagRow(name, value, status, rationale, source, "research")


FLAG_TABLE: Tuple[FlagRow, ...] = (
    _row("prompt", "stdin", PINNED,
         "the prompt is piped; --allowedTools is variadic, so a positional prompt could be read as a tool name",
         "prior harness; cli-reference"),
    _row("-p", "always", PINNED,
         "print mode; judge success from the result event, not the exit status", "headless"),
    _row("--output-format", "stream-json", PINNED, "one JSON event per line", "headless"),
    _row("--verbose", "always", PINNED, "required with -p and stream-json", "prior live probe"),
    _row("--setting-sources", SETTING_SOURCES, PINNED,
         "leaving out user also stops claude.ai skill sync", "cli-reference; skills"),
    _row("--settings", "absolute realpath of a regular file", PINNED,
         "overrides same keys in settings files for the session", "cli-reference"),
    _row("--session-id", "lowercase UUID, one per stage", PINNED,
         "must be a valid UUID", "cli-reference"),
    _row("--resume", "the stage's session id", PINNED, "continues a stage's session", "cli-reference"),
    _row("--permission-mode", PERMISSION_MODE, PINNED,
         "asserted later against init.permissionMode", "cli-reference; permission-modes"),
    _row("--allowedTools", "one comma-joined argument", PINNED,
         "naming Glob or Grep restores both tools; one argument avoids variadic parsing", "permissions"),
    _row("--model", PINNED_MODEL, PINNED, "D-05: the full model id; aliases move", "model-config"),
    _row("--max-turns", "small integer per call", PINNED,
         "print mode only; accepted although 2.1.310 hides it from --help; the limit itself was not reached",
         "cli-reference"),
    _row("--max-budget-usd", "exact two-decimal value, at most 5.00", PINNED,
         "client-side estimate that may overshoot slightly; per-call caps leave headroom", "cli-reference"),
    _row("--strict-mcp-config", "no --mcp-config given", ADDED,
         "only servers from --mcp-config are used; zero servers is asserted from init.mcp_servers",
         "cli-reference"),
    _row("--effort", "high", ADDED,
         "pinning blocks drift of the default; accepted, but 2.1.310 reports no effort in the init event",
         "model-config"),
    _row("--include-hook-events", "spike audit only", ADDED,
         "accepted, but 2.1.310 put no hook events in the stream; the audit reads the logger file instead",
         "agent-sdk"),
    _row("DISABLE_AUTOUPDATER", "1", PINNED, "the build under test must not change mid-run", "env-vars"),
    _row("CLAUDE_CONFIG_DIR", "harness-owned directory", PINNED,
         "credentials, settings, history and plugins live under it (D-02)", "env-vars; authentication"),
    _row("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "1", ADDED,
         "strips credential-shaped variables from the model's Bash subprocesses", "env-vars"),
    _row("CKPT_HOME", "run-owned directory", PINNED,
         "the stub keeps all state under it; the model's Bash inherits it", "prior harness"),
    _row("--bare", "not passed", NOT_PINNED, "changes what the skill sees; not what the matrix measures",
         "cli-reference"),
    _row("--safe-mode", "not passed", NOT_PINNED, "restricts the run beyond the baseline", "cli-reference"),
    _row("--restricted", "not passed", NOT_PINNED, "restricts the run beyond the baseline", "cli-reference"),
    _row("--dangerously-skip-permissions", "not passed", NOT_PINNED,
         "the matrix measures permission behaviour; it never bypasses it", "cli-reference"),
    _row("--permission-mode auto, dontAsk, acceptEdits", "not passed", NOT_PINNED,
         "only the default mode is evidence-comparable", "permission-modes"),
    _row("--include-partial-messages", "not passed", NOT_PINNED,
         "adds events the parser does not need", "cli-reference"),
    _row("--no-session-persistence", "not passed on real rows", NOT_PINNED,
         "stages resume by session id", "cli-reference"),
    _row("--fallback-model", "not passed", NOT_PINNED, "a silent model switch would corrupt a row", "cli-reference"),
    _row("--tools", "not passed", NOT_PINNED, "init.tools is recorded instead", "cli-reference"),
    _row("--add-dir", "not passed", NOT_PINNED,
         "out-of-project reads of the wrapper folder were refused in committed evidence; decided per row later",
         "cli-reference"),
    _row("--system-prompt", "not passed", NOT_PINNED, "the skill is the only instruction source under test",
         "cli-reference"),
    _row("--exclude-dynamic-system-prompt-sections", "not passed", NOT_PINNED,
         "changes the prompt the skill runs under", "cli-reference"),
    _row("--input-format", "not passed", NOT_PINNED, "the prompt is plain text on stdin", "cli-reference"),
    _row("--permission-prompts", "not passed", NOT_PINNED,
         "with no host, prompts are denied either way; the flag only adds a message to the model",
         "headless"),
)


# Rows that a live spike confirmed (plan 02-08), with the spike that did: S1 (isolation capture) or
# S2 (stream capture, probe, resume, verbose probe). Every other row stays "research" because no run
# exercised it: the NOT_PINNED rows are flags that are never passed.
_CONFIRMED_BY = {
    "prompt": "S1",
    "-p": "S1",
    "--output-format": "S1",
    "--verbose": "S2",
    "--setting-sources": "S1",
    "--settings": "S1",
    "--session-id": "S2",
    "--resume": "S2",
    "--permission-mode": "S1",
    "--allowedTools": "S2",
    "--model": "S1",
    "--max-turns": "S1",
    "--max-budget-usd": "S1",
    "--strict-mcp-config": "S1",
    "--effort": "S1",
    "--include-hook-events": "S1",
    "CLAUDE_CONFIG_DIR": "S1",
    "CKPT_HOME": "S2",
}
FLAG_TABLE = tuple(
    row._replace(confirmed_by=_CONFIRMED_BY.get(row.name, row.confirmed_by)) for row in FLAG_TABLE
)


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_flag_table_markdown() -> str:
    """Return the flag table as deterministic Markdown (header, rule, one line per row)."""
    lines = [
        "| Flag or env | Pinned value | Status | Why | Source | Confirmed by |",
        "|---|---|---|---|---|---|",
    ]
    for row in FLAG_TABLE:
        lines.append(
            "| `%s` | %s | %s | %s | %s | %s |"
            % (
                _escape_cell(row.name),
                _escape_cell(row.value),
                row.status,
                _escape_cell(row.rationale),
                _escape_cell(row.source),
                row.confirmed_by,
            )
        )
    return "\n".join(lines) + "\n"


def format_budget(value: Any) -> str:
    """Return value as text with exactly two decimals, or raise ValueError (D-04).

    Only str and Decimal are accepted: floats, ints and bools are refused. The value must be
    above zero, at most 5.00 and have at most two decimal places (nothing is ever rounded).
    """
    if isinstance(value, bool) or not isinstance(value, (str, Decimal)):
        raise ValueError("budget must be a str or Decimal")
    if isinstance(value, str):
        if _BUDGET_TEXT.match(value) is None:
            raise ValueError("budget text must be digits with at most two decimals")
        number = Decimal(value)
    else:
        number = value
        if not number.is_finite():
            raise ValueError("budget must be a finite number")
        exponent = number.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -2:
            raise ValueError("budget has more than two decimals")
    if number <= 0:
        raise ValueError("budget must be above zero")
    if number > _MAX_BUDGET:
        raise ValueError("budget must be at most 5.00")
    return format(number.quantize(Decimal("0.01")), "f")


def _require_absolute(path: Any, what: str) -> str:
    if not isinstance(path, str) or not path or not os.path.isabs(path):
        raise ValueError("%s must be an absolute path" % what)
    return path


def _check_session_id(session_id: Any) -> str:
    if not isinstance(session_id, str):
        raise ValueError("session id must be a string")
    try:
        canonical = str(uuid.UUID(session_id))
    except ValueError:
        raise ValueError("session id must be a UUID") from None
    if canonical != session_id:
        raise ValueError("session id must be the canonical lowercase form of a UUID")
    return session_id


def build_argv(
    claude_path: str,
    session_id: str,
    settings_path: str,
    allowed_tools: Sequence[str],
    max_turns: int,
    max_budget_usd: Any,
    resume: bool = False,
    include_hook_events: bool = False,
    model: str = PINNED_MODEL,
) -> List[str]:
    """Return the pinned claude -p argument list in one fixed order.

    The prompt is never part of argv (it goes to stdin) and --allowedTools is one
    comma-joined argument. Equal inputs give equal lists; each call returns a new list.
    """
    _require_absolute(claude_path, "claude path")
    _require_absolute(settings_path, "settings path")
    _check_session_id(session_id)
    if isinstance(allowed_tools, str) or not isinstance(allowed_tools, (list, tuple)):
        raise ValueError("allowed tools must be a list or tuple of strings")
    tools = list(allowed_tools)
    if not tools:
        raise ValueError("allowed tools must not be empty")
    for tool in tools:
        if not isinstance(tool, str) or not tool or "," in tool:
            raise ValueError("each allowed tool must be a non-empty string without commas")
    if len(set(tools)) != len(tools):
        raise ValueError("allowed tools must not repeat")
    if isinstance(max_turns, bool) or not isinstance(max_turns, int) or not 1 <= max_turns <= 100:
        raise ValueError("max turns must be an integer from 1 to 100")
    if not isinstance(model, str) or not model or model != model.strip() or " " in model:
        raise ValueError("model must be a non-empty string without spaces")
    budget = format_budget(max_budget_usd)

    argv = [
        claude_path,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--setting-sources",
        SETTING_SOURCES,
        "--settings",
        settings_path,
        "--resume" if resume else "--session-id",
        session_id,
        "--permission-mode",
        PERMISSION_MODE,
        "--allowedTools",
        ",".join(tools),
        "--model",
        model,
        "--max-turns",
        str(max_turns),
        "--max-budget-usd",
        budget,
        "--strict-mcp-config",
        "--effort",
        "high",
    ]
    if include_hook_events:
        argv.append("--include-hook-events")
    return argv


def _is_within(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip(os.sep) + os.sep)


def build_env(
    base_env: Mapping[str, str],
    config_dir: Optional[str],
    ckpt_home: Optional[str] = None,
) -> Dict[str, str]:
    """Return a new minimal environment for the child (D-02, D-03).

    Only the allow-listed names are copied from base_env, so ANTHROPIC_*, CLAUDE_CODE_*,
    CLAUDECODE, cloud and token variables never reach the child or the model's Bash tool.
    CLAUDE_CONFIG_DIR (when given), DISABLE_AUTOUPDATER=1, CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1
    and CKPT_HOME (when given) are set. A config directory that is relative, inside this
    repository or under the user's own Claude config directory is refused with ValueError;
    the message never contains the path.
    """
    env: Dict[str, str] = {}
    for name in _ENV_ALLOW_LIST:
        if name in base_env:
            env[name] = base_env[name]
    if config_dir is not None:
        if not isinstance(config_dir, str) or not os.path.isabs(config_dir):
            raise ValueError("the config directory must be an absolute path")
        resolved = os.path.realpath(config_dir)
        if _is_within(resolved, os.path.realpath(_REPO_ROOT)):
            raise ValueError("the config directory must be outside the repository")
        own = os.path.realpath(os.path.expanduser(os.path.join("~", ".claude")))
        if _is_within(resolved, own):
            raise ValueError("the config directory must be outside the user's own Claude config")
        env["CLAUDE_CONFIG_DIR"] = config_dir
    env["DISABLE_AUTOUPDATER"] = "1"
    env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] = "1"
    if ckpt_home is not None:
        if not isinstance(ckpt_home, str) or not os.path.isabs(ckpt_home):
            raise ValueError("CKPT_HOME must be an absolute path")
        env["CKPT_HOME"] = ckpt_home
    return env


def build_allowed_tools(wrapper_path: str, verbs: Sequence[str]) -> Tuple[str, ...]:
    """Return the committed baseline followed by one Bash rule per allowed wrapper verb.

    Only the model-facing verbs are accepted; bind, create, init, unknown verbs and repeats
    raise ValueError. The wrapper path must be absolute and free of commas, parentheses,
    asterisks, colons and whitespace. A bare wrapper prefix is never emitted (STUB-06).
    """
    _require_absolute(wrapper_path, "wrapper path")
    if re.search(r"[,()*:?\s]", wrapper_path):
        raise ValueError("the wrapper path holds a character that is unsafe in an allow rule")
    if isinstance(verbs, str):
        raise ValueError("verbs must be a sequence of strings")
    chosen = list(verbs)
    for verb in chosen:
        if verb not in MODEL_FACING_WRAPPER_VERBS:
            raise ValueError("verb is not model-facing")
    if len(set(chosen)) != len(chosen):
        raise ValueError("verbs must not repeat")
    rules = ["Bash(%s %s:*)" % (wrapper_path, verb) for verb in chosen]
    return tuple(BASELINE_ALLOWED_TOOLS) + tuple(rules)


def render_settings(auto_memory_dir: str, audit_hook_command: Optional[str] = None) -> Dict[str, Any]:
    """Return the dict for --settings: the auto-memory directory (realpath) and an optional hook."""
    _require_absolute(auto_memory_dir, "auto memory directory")
    settings: Dict[str, Any] = {
        "autoMemoryDirectory": os.path.realpath(auto_memory_dir),
        "autoMemoryEnabled": True,
    }
    if audit_hook_command is not None:
        if not isinstance(audit_hook_command, str) or not audit_hook_command:
            raise ValueError("the audit hook command must be a non-empty string")
        settings["hooks"] = {
            "InstructionsLoaded": [
                {"hooks": [{"type": "command", "command": audit_hook_command}]}
            ]
        }
    return settings


def parse_banner(text: str) -> str:
    """Return X.Y.Z from exactly "X.Y.Z (Claude Code)" plus at most one newline, else ValueError."""
    if not isinstance(text, str):
        raise ValueError("banner must be text")
    match = _BANNER.match(text)
    if match is None:
        raise ValueError("banner is not in the expected shape")
    return "%s.%s.%s" % match.groups()


class Verdict(NamedTuple):
    version: Optional[str]
    status: str  # TESTED, UNTESTED, BELOW_FLOOR or MALFORMED


def check_version(text: str, tested: Sequence[str]) -> Verdict:
    """Gate a claude --version banner against the exact-match tested set.

    TESTED: the version is listed. UNTESTED and BELOW_FLOOR: a well-formed banner that is not
    listed (the caller maps both to exit 13). MALFORMED: empty or unparseable (exit 11).
    The gate is an exact match, never a range.
    """
    try:
        version = parse_banner(text)
    except ValueError:
        return Verdict(None, "MALFORMED")
    if version in tuple(tested):
        return Verdict(version, "TESTED")
    parts = tuple(int(piece) for piece in version.split("."))
    if parts < VERSION_FLOOR:
        return Verdict(version, "BELOW_FLOOR")
    return Verdict(version, "UNTESTED")
