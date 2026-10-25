"""Spike driver for the acceptance harness: the only code that may spend tokens (plan 02-08).

This module builds everything the two spikes need and proves it up to the paid boundary:

  * harness_home, ensure_config_dir  the harness-owned folder and its claude-config child, outside
                                     the repository and outside the user's own Claude folder (D-02)
  * local_user_names                 entry names of the user's own skills, commands, agents and
                                     plugins, listed locally for the absence check, never opened
  * materialize                      the scratch project, wrapper folder, bound state folder,
                                     auto-memory folder and settings file inside one run root
  * the spend ledger                 append-only, outside the repository, read by guard() before
                                     any paid call: at most two attempts per call name and recorded
                                     spend plus the next call's cap never above 5.00 USD (D-04)
  * the login probe record           one line per auth-check, holding only the time, the boolean
                                     loggedIn, the exit code, the version and a created flag
  * spike_preflight                  claude --version and claude auth status only, with the detected
                                     version as the only tested version, so an untested build is
                                     allowed here because these runs create the tested set

Command line (run as python3 -E -s -B pc_spike.py, never with -I, because the pc_ modules import each
other):

    auth-check                  zero-token login check; exit 0 (loggedIn true), 12 (not logged in or
                                no claude), 11 (unusable answer), 13 (version below the floor)
    s1 | s2a | s2b | verbose-probe [--run] [--from-run NAME]
                                without --run: print the pinned call, caps and budget and exit 0
                                without starting any process (there is no --dry-run flag; the dry
                                run is the absence of --run). With --run the guard runs first, and
                                the paid path itself is added by the later tasks of the plan
    spend                       print the recorded totals
    probes                      print the recorded login-probe lines

Exit codes: 0, 2 usage, 11 FAIL, 12 BLOCKED, 13 untested version, 18 BUDGET_REFUSED. Messages never
carry a home path, a credential or any auth field other than the boolean loggedIn.

The driver never deletes or overwrites a run root or a capture, never passes --bare,
--dangerously-skip-permissions or a permission mode other than default, and never reads, writes,
copies or prints a credential file (D-03).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from decimal import ROUND_DOWN, ROUND_UP, Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pc_exitcodes
import pc_flags
import pc_manifest
import pc_preflight
import pc_runroot

HARNESS_HOME_ENV = "PRECLEAR_HARNESS_HOME"
DEFAULT_HOME_NAME = ".preclear-harness"
CONFIG_DIR_NAME = "claude-config"
RUNS_DIR_NAME = "runs"
SPEND_FILE = "spike-spend.jsonl"
PROBE_FILE = "auth-probes.jsonl"

TOTAL_CAP = Decimal("5.00")  # D-04: both spikes together, in US dollars
MAX_ATTEMPTS = 2  # D-04: one try and one retry per call name
PINNED_MODEL = pc_flags.PINNED_MODEL  # D-05

LEDGER_NAME = "CONTINUITY_CLAUDE-widget-export.md"
ROW2_SETUP = ("tests", "evidence", "publication-2026-10-20", "row2-double-conflict", "snap-0-setup")
FIXTURE_PROJECT = ("tests", "fixtures", "bound-ledger", "project")

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
_VERSION_TIMEOUT_SECONDS = 20
_STUB_TIMEOUT_SECONDS = 60
_GIT_TIMEOUT_SECONDS = 120


class CallSpec(NamedTuple):
    turns: int
    cap: Decimal


# The four paid calls. Every one passes --max-budget-usd and --max-turns (D-04).
CALLS: Dict[str, CallSpec] = {
    "s1": CallSpec(3, Decimal("0.50")),
    "s2a": CallSpec(12, Decimal("1.00")),
    "s2b": CallSpec(2, Decimal("0.50")),
    "verbose": CallSpec(1, Decimal("0.05")),
}

_COMMAND_CALL = {"s1": "s1", "s2a": "s2a", "s2b": "s2b", "verbose-probe": "verbose"}


class SpikeError(Exception):
    """A refusal or failure that maps to one exit code. Messages never name a path."""

    exit_code = pc_exitcodes.PREFLIGHT_FAIL


class HomeRefused(SpikeError):
    exit_code = pc_exitcodes.USAGE


class BudgetRefused(SpikeError):
    exit_code = pc_exitcodes.BUDGET_REFUSED


# ---------------------------------------------------------------------------------------------
# Harness home and config directory (D-01, D-02, D-03)
# ---------------------------------------------------------------------------------------------


def _within(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip(os.sep) + os.sep)


def harness_home(
    env: Optional[Mapping[str, str]] = None,
    home_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> str:
    """Return the realpath of the harness-owned folder; refuse an unusable one (HomeRefused).

    The folder is PRECLEAR_HARNESS_HOME when set, else .preclear-harness under the home directory,
    resolved at call time. It must be absolute, outside the repository, and neither at, under nor
    above the user's own Claude config directory. Nothing is created here.
    """
    source = os.environ if env is None else env
    home = home_dir if home_dir else os.path.expanduser("~")
    raw = source.get(HARNESS_HOME_ENV)
    if raw:
        if not os.path.isabs(raw):
            raise HomeRefused("the harness home must be an absolute path")
        candidate = raw
    else:
        candidate = os.path.join(home, DEFAULT_HOME_NAME)
    resolved = os.path.realpath(candidate)
    repo = os.path.realpath(repo_root if repo_root else _REPO_ROOT)
    own = os.path.realpath(os.path.join(home, ".claude"))
    if _within(resolved, repo) or _within(repo, resolved):
        raise HomeRefused("the harness home must be outside the repository")
    if _within(resolved, own) or _within(own, resolved):
        raise HomeRefused("the harness home must be outside the user's own Claude config")
    return resolved


def ensure_config_dir(
    env: Optional[Mapping[str, str]] = None,
    home_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> Tuple[str, bool]:
    """Return (config directory, created) and create it with mode 0700 when it is missing.

    This is the one place in the harness where creation tolerates an existing folder: the directory
    is harness-owned and persistent because the login lives in it. It is never deleted.
    """
    home = harness_home(env, home_dir, repo_root)
    path = os.path.join(home, CONFIG_DIR_NAME)
    os.makedirs(home, mode=0o700, exist_ok=True)
    try:
        os.mkdir(path, 0o700)
        created = True
    except FileExistsError:
        if not os.path.isdir(path):
            raise SpikeError("the config directory name is taken by something that is not a folder") from None
        created = False
    return path, created


def config_dir(
    env: Optional[Mapping[str, str]] = None,
    home_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> str:
    """Return the harness config directory, created with mode 0700 when missing."""
    return ensure_config_dir(env, home_dir, repo_root)[0]


def local_user_names(home_dir: str) -> frozenset:
    """Return the entry names in the user's skills, commands, agents and plugins folders.

    Directory names as they are; file names without a .md suffix. No file is opened and nothing is
    printed. Callers report only the size of the set and a hit count, never a name (D-02).
    """
    names = set()
    base = os.path.join(home_dir, ".claude")
    for folder in ("skills", "commands", "agents", "plugins"):
        path = os.path.join(base, folder)
        try:
            entries = list(os.scandir(path))
        except OSError:
            continue
        for entry in entries:
            name = entry.name
            if entry.is_dir():
                names.add(name)
            elif name.endswith(".md"):
                names.add(name[: -len(".md")])
            else:
                names.add(name)
    return frozenset(names)


# ---------------------------------------------------------------------------------------------
# Time, run roots and the materialiser
# ---------------------------------------------------------------------------------------------


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def new_run_root(home: str, call: str, attempt: int, stamp: Optional[str] = None) -> str:
    """Create <home>/runs/spike-<call>-a<attempt>-<UTC stamp> exclusively and return its realpath.

    The runs folder is created when it is missing and tolerated when it exists; the run root itself
    is never reused (pc_runroot raises RunRootCollision).
    """
    if call not in CALLS:
        raise ValueError("unknown call name")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    runs = os.path.join(home, RUNS_DIR_NAME)
    os.makedirs(runs, mode=0o700, exist_ok=True)
    moment = stamp if stamp else _utc_now().strftime("%Y%m%dT%H%M%SZ")
    return pc_runroot.allocate_run_root(runs, "spike-%s-a%d-%s" % (call, attempt, moment))


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _copy_tree_with(src: str, dst: str, transform: Optional[Mapping[str, Any]] = None) -> None:
    """Create dst exclusively and copy every file of src into it, byte for byte.

    The walk is pc_manifest.tree_manifest (never follows a link); a symlink or special file is
    refused. transform maps a relative path to a function of the file bytes.
    """
    entries = pc_manifest.tree_manifest(src)
    for entry in entries:
        if entry["kind"] not in ("d", "f"):
            raise ValueError("a source tree holds a symlink or special file")
    pc_runroot.exclusive_dir(dst, 0o700)
    for entry in entries:
        rel = os.fsdecode(entry["path"])
        target = os.path.join(dst, rel)
        if entry["kind"] == "d":
            pc_runroot.exclusive_dir(target, 0o700)
            continue
        data = _read_bytes(os.path.join(src, rel))
        if transform is not None and rel in transform:
            data = transform[rel](data)
        pc_runroot.write_exclusive(target, data, 0o644)


_CONFIG_LINE = re.compile(r"^(\s+)(executable|project|ledger|fallback_directory): (\S.*)$")


def _fill_configuration(text: str, values: Mapping[str, str]) -> str:
    """Replace the four path values of the fixture's configuration block, line by line."""
    seen = set()
    lines = []
    for line in text.split("\n"):
        match = _CONFIG_LINE.match(line)
        if match is not None:
            key = match.group(2)
            seen.add(key)
            line = "%s%s: %s" % (match.group(1), key, values[key])
        lines.append(line)
    result = "\n".join(lines)
    if seen != set(values) or "/path/to/" in result:
        raise ValueError("the fixture configuration block has an unexpected shape")
    return result


def _git_env() -> Dict[str, str]:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    if "LANG" in os.environ:
        env["LANG"] = os.environ["LANG"]
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_AUTHOR_NAME"] = "Harness Spike"
    env["GIT_AUTHOR_EMAIL"] = "harness-spike@example.com"
    env["GIT_COMMITTER_NAME"] = "Harness Spike"
    env["GIT_COMMITTER_EMAIL"] = "harness-spike@example.com"
    return env


def _run_git(project: str, args: Sequence[str]) -> None:
    git = shutil.which("git", path=_git_env()["PATH"])
    if git is None:
        raise SpikeError("git was not found on the search path")
    try:
        done = subprocess.run(
            [git, "-C", project] + list(args),
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_GIT_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise SpikeError("a git step of the scratch project setup could not run") from None
    if done.returncode != 0:
        raise SpikeError("a git step of the scratch project setup failed")


def _sources(repo_root: str, audit_hook: bool) -> Dict[str, str]:
    harness = os.path.join(repo_root, "tests", "harness")
    found = {
        "fixture": os.path.join(repo_root, *FIXTURE_PROJECT),
        "skill": os.path.join(repo_root, "SKILL.md"),
        "references": os.path.join(repo_root, "references"),
        "wrapper": os.path.join(harness, "checkpoint-wrapper"),
        "stub": os.path.join(harness, "checkpoint_stub.py"),
        "ledger": os.path.join(repo_root, *ROW2_SETUP, LEDGER_NAME),
    }
    if audit_hook:
        found["hooklog"] = os.path.join(harness, "pc_hooklog.py")
    for name, path in found.items():
        exists = os.path.isdir(path) if name in ("fixture", "references") else os.path.isfile(path)
        if not exists:
            raise ValueError("a source the run root needs is missing: %s" % name)
    return found


def materialize(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    audit_hook: bool = False,
) -> Dict[str, Optional[str]]:
    """Build the scratch run inside the already-created run root and return its paths.

    Everything is created exclusively (pc_runroot.exclusive_dir and write_exclusive), so a second
    call on the same run root raises FileExistsError. Created, in order: project (the bound-ledger
    fixture with its configuration block filled in, a git repository on main with one commit, then
    the skill installed as untracked byte-exact copies), wrapper (the wrapper copy named checkpoint
    with mode 0755, py, stub), ckpt (the committed row 2 ledger, registered and bound to the session
    through the stub's own setup verb), auto-memory, raw and settings.json. With audit_hook the
    settings also carry the InstructionsLoaded logger, writing to raw/hooklog.jsonl.
    """
    try:
        canonical = str(uuid.UUID(session_id))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("the session id must be a UUID") from None
    if canonical != session_id:
        raise ValueError("the session id must be the canonical lowercase form")
    repo = os.path.realpath(repo_root)
    root = os.path.realpath(run_root)
    runs = os.path.join(os.path.realpath(harness_home_dir), RUNS_DIR_NAME)
    if not os.path.isdir(root):
        raise ValueError("the run root does not exist")
    if not _within(root, runs) or root == runs:
        raise ValueError("the run root must lie under the harness home's runs folder")
    if _within(root, repo):
        raise ValueError("the run root must be outside the repository")
    source = _sources(repo, audit_hook)
    interpreter = os.path.realpath(sys.executable)
    if not interpreter:
        raise ValueError("no interpreter path is known")

    project = os.path.join(root, "project")
    wrapper_dir = os.path.join(root, "wrapper")
    wrapper = os.path.join(wrapper_dir, "checkpoint")
    ckpt = os.path.join(root, "ckpt")
    ledgers = os.path.join(ckpt, "ledgers")
    ledger = os.path.join(ledgers, LEDGER_NAME)
    auto_memory = os.path.join(root, "auto-memory")
    raw = os.path.join(root, "raw")
    settings = os.path.join(root, "settings.json")
    hooklog = os.path.join(raw, "hooklog.jsonl") if audit_hook else None

    values = {
        "executable": wrapper,
        "project": project,
        "ledger": ledger,
        "fallback_directory": os.path.join(project, ".preclear"),
    }

    def fill(data: bytes) -> bytes:
        return _fill_configuration(data.decode("utf-8"), values).encode("utf-8")

    _copy_tree_with(source["fixture"], project, {"CLAUDE.md": fill})
    _run_git(project, ["init", "-q"])
    _run_git(project, ["symbolic-ref", "HEAD", "refs/heads/main"])
    _run_git(project, ["add", "-A"])
    _run_git(project, ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "Initial fixture commit"])

    skill_dir = os.path.join(project, ".claude", "skills", "preclear")
    pc_runroot.exclusive_dir(os.path.join(project, ".claude"), 0o700)
    pc_runroot.exclusive_dir(os.path.join(project, ".claude", "skills"), 0o700)
    pc_runroot.exclusive_dir(skill_dir, 0o700)
    pc_runroot.write_exclusive(os.path.join(skill_dir, "SKILL.md"), _read_bytes(source["skill"]), 0o644)
    _copy_tree_with(source["references"], os.path.join(skill_dir, "references"))

    pc_runroot.exclusive_dir(wrapper_dir, 0o700)
    pc_runroot.write_exclusive(wrapper, _read_bytes(source["wrapper"]), 0o755)
    pc_runroot.write_exclusive(os.path.join(wrapper_dir, "py"), interpreter.encode("utf-8"), 0o644)
    pc_runroot.write_exclusive(os.path.join(wrapper_dir, "stub"), source["stub"].encode("utf-8"), 0o644)

    pc_runroot.exclusive_dir(ckpt, 0o700)
    pc_runroot.exclusive_dir(ledgers, 0o700)
    pc_runroot.write_exclusive(ledger, _read_bytes(source["ledger"]), 0o644)
    stub_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "CKPT_HOME": ckpt}
    try:
        done = subprocess.run(
            [interpreter, "-I", "-B", source["stub"], "bind", "--ledger", ledger, "--session", session_id],
            env=stub_env,
            cwd=project,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_STUB_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise SpikeError("the checkpoint stub could not run for the state setup") from None
    if done.returncode != 0:
        raise SpikeError("the checkpoint stub refused the state setup")

    pc_runroot.exclusive_dir(auto_memory, 0o700)
    pc_runroot.exclusive_dir(raw, 0o700)
    command = None
    if audit_hook:
        command = " ".join(shlex.quote(part) for part in (interpreter, "-I", "-B", source["hooklog"], hooklog))
    rendered = pc_flags.render_settings(auto_memory, command)
    pc_runroot.write_exclusive(settings, (json.dumps(rendered, indent=2, sort_keys=True) + "\n").encode("utf-8"), 0o600)

    return {
        "run_root": root,
        "project": project,
        "skill_dir": skill_dir,
        "wrapper_dir": wrapper_dir,
        "wrapper": wrapper,
        "ckpt": ckpt,
        "ledger": ledger,
        "auto_memory": auto_memory,
        "raw": raw,
        "settings": settings,
        "hooklog": hooklog,
    }


# ---------------------------------------------------------------------------------------------
# Spend ledger (D-04): append-only, outside the repository, Decimal arithmetic
# ---------------------------------------------------------------------------------------------

_SPEND_KEYS = ("attempt", "call", "subtype", "total_cost_usd", "version")
_PROBE_KEYS = ("created", "exit", "loggedIn", "time", "version")


def _append_json_line(path: str, record: Mapping[str, Any]) -> None:
    line = (json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(line)
        while len(view) > 0:
            written = os.write(fd, view)
            view = view[written:]
    finally:
        os.close(fd)


def _cost_text(cost: Any) -> Optional[str]:
    if cost is None:
        return None
    if isinstance(cost, bool) or isinstance(cost, float) or not isinstance(cost, (Decimal, str)):
        raise ValueError("a cost must be a Decimal, a numeric string or None")
    try:
        number = cost if isinstance(cost, Decimal) else Decimal(cost)
    except InvalidOperation:
        raise ValueError("a cost string must be numeric") from None
    if not number.is_finite() or number < 0:
        raise ValueError("a cost must be a finite number of at least zero")
    return format(number, "f")


def append_spend(
    home: str,
    call: str,
    attempt: int,
    cost: Any,
    subtype: str,
    version: Optional[str],
) -> None:
    """Append one line to the spend ledger; never truncates. cost None means unknown."""
    if call not in CALLS:
        raise ValueError("unknown call name")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    text = _cost_text(cost)
    os.makedirs(home, mode=0o700, exist_ok=True)
    record = {
        "call": call,
        "attempt": attempt,
        "total_cost_usd": text,
        "subtype": subtype if isinstance(subtype, str) else "no-result",
        "version": version if isinstance(version, str) else None,
    }
    _append_json_line(os.path.join(home, SPEND_FILE), record)


def read_spend(home: str) -> List[Dict[str, Any]]:
    """Return the ledger lines; an unreadable ledger refuses (BudgetRefused), it never guesses."""
    path = os.path.join(home, SPEND_FILE)
    if not os.path.exists(path):
        return []
    try:
        data = _read_bytes(path).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise BudgetRefused("the spend ledger could not be read") from None
    records: List[Dict[str, Any]] = []
    if data == "":
        return records
    for line in data.split("\n")[:-1] if data.endswith("\n") else data.split("\n"):
        try:
            record = json.loads(line)
            ok = isinstance(record, dict) and sorted(record) == list(_SPEND_KEYS)
            ok = ok and record["call"] in CALLS and isinstance(record["attempt"], int)
            ok = ok and (record["total_cost_usd"] is None or isinstance(record["total_cost_usd"], str))
            if ok and record["total_cost_usd"] is not None:
                ok = Decimal(record["total_cost_usd"]).is_finite()
        except (ValueError, InvalidOperation):
            ok = False
        if not ok:
            raise BudgetRefused("the spend ledger holds a line that is not a spend record")
        records.append(record)
    return records


def recorded_total(home: str) -> Decimal:
    """Sum the ledger; a call with an unknown cost counts as its cap."""
    total = Decimal("0")
    for record in read_spend(home):
        cost = record["total_cost_usd"]
        total += CALLS[record["call"]].cap if cost is None else Decimal(cost)
    return total


def remaining(home: str) -> Decimal:
    return TOTAL_CAP - recorded_total(home)


def attempts_made(home: str, call: str) -> int:
    if call not in CALLS:
        raise ValueError("unknown call name")
    return sum(1 for record in read_spend(home) if record["call"] == call)


def guard(home: str, call: str) -> int:
    """Refuse before a paid call; return the number of this attempt when it may go ahead.

    Refused (BudgetRefused, exit 18) when the call name has used up MAX_ATTEMPTS, or when the
    recorded spend plus this call's cap would exceed TOTAL_CAP.
    """
    if call not in CALLS:
        raise ValueError("unknown call name")
    records = read_spend(home)
    used = sum(1 for record in records if record["call"] == call)
    if used >= MAX_ATTEMPTS:
        raise BudgetRefused("the attempt limit for this call name is used up")
    total = Decimal("0")
    for record in records:
        cost = record["total_cost_usd"]
        total += CALLS[record["call"]].cap if cost is None else Decimal(cost)
    if total + CALLS[call].cap > TOTAL_CAP:
        raise BudgetRefused("recorded spend plus this call's cap would exceed the total cap")
    return used + 1


# ---------------------------------------------------------------------------------------------
# Login probe record and the zero-token preflight
# ---------------------------------------------------------------------------------------------


def _utc_second_text() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def record_probe(home: str, logged_in: Optional[bool], exit_code: int, version: Optional[str], created: bool) -> None:
    """Append one probe line: only time, loggedIn (true, false or null), exit code, version, created."""
    if logged_in is not None and not isinstance(logged_in, bool):
        raise ValueError("loggedIn must be a boolean or None")
    os.makedirs(home, mode=0o700, exist_ok=True)
    record = {
        "time": _utc_second_text(),
        "loggedIn": logged_in,
        "exit": int(exit_code),
        "version": version if isinstance(version, str) else None,
        "created": bool(created),
    }
    _append_json_line(os.path.join(home, PROBE_FILE), record)


def read_probes(home: str) -> List[Dict[str, Any]]:
    path = os.path.join(home, PROBE_FILE)
    if not os.path.exists(path):
        return []
    try:
        text = _read_bytes(path).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise SpikeError("the login probe record could not be read") from None
    records = []
    for line in text.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        if not isinstance(record, dict) or sorted(record) != list(_PROBE_KEYS):
            raise SpikeError("the login probe record holds a line that is not a probe")
        records.append(record)
    return records


def detect_version(claude: str, env: Mapping[str, str]) -> Optional[str]:
    """Run claude --version (no prompt, no tokens) and return X.Y.Z, or None when unusable."""
    try:
        done = subprocess.run(
            [claude, "--version"],
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=_VERSION_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    try:
        return pc_flags.parse_banner(done.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


def spike_preflight(
    search_path: Optional[Sequence[str]],
    config_dir_path: str,
    base_env: Mapping[str, str],
) -> Tuple[pc_preflight.PreflightResult, Optional[str]]:
    """Run the zero-token preflight in spike mode; return (result, detected version or None).

    The driver runs claude --version itself, requires a parsable banner at or above the floor, and
    passes that detected version as the only tested version to pc_preflight.run_preflight. The
    gate therefore allows an untested build here, because these runs create the tested set, while
    pc_preflight itself stays strict for every other caller. Only the boolean loggedIn is read.
    """
    claude = pc_preflight.find_claude(search_path)
    if claude is None:
        return pc_preflight.run_preflight(search_path, config_dir_path, (), None, base_env), None
    try:
        env = pc_flags.build_env(base_env, config_dir_path)
    except ValueError as problem:
        return pc_preflight.PreflightResult(pc_preflight.FAIL, "config directory refused: %s" % problem), None
    version = detect_version(claude, env)
    if version is None:
        return (
            pc_preflight.PreflightResult(
                pc_preflight.FAIL, "claude --version printed an empty or unrecognised banner, or failed"
            ),
            None,
        )
    if tuple(int(piece) for piece in version.split(".")) < pc_flags.VERSION_FLOOR:
        return (
            pc_preflight.PreflightResult(
                pc_preflight.UNTESTED, "Claude Code %s is below the version floor" % version
            ),
            version,
        )
    result = pc_preflight.run_preflight(search_path, config_dir_path, (version,), None, base_env)
    return result, version


def auth_check(
    env: Mapping[str, str],
    search_path: Optional[Sequence[str]] = None,
    home_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> Tuple[int, str]:
    """Zero-token login check. Return (exit code, the one line to print) after recording the probe.

    Creates the harness config directory when missing (mode 0700), runs the spike-mode preflight
    and maps its answer: loggedIn true is 0 and prints only that; not logged in is 12 with the
    one-time login instruction; no claude is 12; an unusable answer is 11; a version below the
    floor is 13. Only the boolean loggedIn is ever read from the auth status.
    """
    home = harness_home(env, home_dir, repo_root)
    cfg, created = ensure_config_dir(env, home_dir, repo_root)
    result, version = spike_preflight(search_path, cfg, env)
    if result.state == pc_preflight.OK:
        logged_in: Optional[bool] = True
        line = "loggedIn true"
    else:
        logged_in = False if "is not logged in" in result.message else None
        line = result.line()
    record_probe(home, logged_in, result.exit_code, version, created)
    return result.exit_code, line


# ---------------------------------------------------------------------------------------------
# The plan a call would run (the dry run) and the command line
# ---------------------------------------------------------------------------------------------

_ROLE_CLAUDE = "/role/claude"
_ROLE_SETTINGS = "/role/settings.json"
_ROLE_WRAPPER = "/role/wrapper/checkpoint"
_ROLE_SESSION = "00000000-0000-4000-8000-000000000000"


def _money(value: Decimal, rounding: str) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=rounding), "f")


def call_argv(call: str, tools: Sequence[str]) -> List[str]:
    """Return the pinned argv for a call with role placeholders for the path-like values."""
    spec = CALLS[call]
    argv = pc_flags.build_argv(
        _ROLE_CLAUDE,
        _ROLE_SESSION,
        _ROLE_SETTINGS,
        tools,
        spec.turns,
        spec.cap,
        resume=(call == "s2b"),
        include_hook_events=(call == "s1"),
    )
    if call == "verbose":
        argv = [item for item in argv if item != "--verbose"]
    return argv


def describe_call(call: str, home: str, from_run: Optional[str] = None) -> List[str]:
    """Return the lines of the dry-run plan for a call; path values are replaced by role tokens."""
    spec = CALLS[call]
    tools = pc_flags.build_allowed_tools(_ROLE_WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = call_argv(call, tools)
    shown = []
    previous = ""
    for item in argv:
        if item == _ROLE_CLAUDE:
            shown.append("<claude>")
        elif previous == "--settings":
            shown.append("<settings>")
        elif previous in ("--session-id", "--resume"):
            shown.append("<session>")
        elif previous == "--allowedTools":
            shown.append("<allowed-tools:%d>" % len(tools))
        else:
            shown.append(item)
        previous = item
    names = sorted(pc_flags.build_env({}, "/role/config", "/role/ckpt"))
    total = recorded_total(home)
    lines = [
        "call: %s (dry run: no process is started and nothing is sent to a model)" % call,
        "argv: %s" % " ".join(shown),
        "prompt: sent on standard input by the paid path, never in argv",
        "environment names set: %s" % " ".join(names),
        "caps: --max-budget-usd %s --max-turns %d" % (pc_flags.format_budget(spec.cap), spec.turns),
        "attempts: %d of %d" % (attempts_made(home, call), MAX_ATTEMPTS),
        "budget: recorded %s USD, remaining %s USD, this call needs up to %s USD of the %s USD total"
        % (
            _money(total, ROUND_UP),
            _money(TOTAL_CAP - total, ROUND_DOWN),
            _money(spec.cap, ROUND_UP),
            _money(TOTAL_CAP, ROUND_UP),
        ),
    ]
    if call == "s2b":
        lines.append("from run: %s" % (from_run if from_run else "(not given; required with --run)"))
    lines.append("allowed tools (%d):" % len(tools))
    for rule in tools:
        lines.append("  %s" % rule.replace(_ROLE_WRAPPER, "<wrapper>"))
    return lines


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pc_spike.py", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command")
    for name in ("auth-check", "spend", "probes"):
        commands.add_parser(name, allow_abbrev=False)
    for name in _COMMAND_CALL:
        sub = commands.add_parser(name, allow_abbrev=False)
        sub.add_argument("--run", action="store_true")
        if name == "s2b":
            sub.add_argument("--from-run", dest="from_run", default=None)
    return parser


def _write(stream: Any, text: str) -> None:
    stream.write(text)
    stream.flush()


def _cmd_spend(home: str) -> int:
    records = read_spend(home)
    total = recorded_total(home)
    _write(sys.stdout, "recorded spend: %s USD over %d call(s)\n" % (_money(total, ROUND_UP), len(records)))
    _write(sys.stdout, "remaining: %s USD\n" % _money(TOTAL_CAP - total, ROUND_DOWN))
    _write(sys.stdout, "cap: %s USD\n" % _money(TOTAL_CAP, ROUND_UP))
    used = ", ".join("%s %d of %d" % (name, attempts_made(home, name), MAX_ATTEMPTS) for name in CALLS)
    _write(sys.stdout, "attempts: %s\n" % used)
    return pc_exitcodes.OK


def _cmd_probes(home: str) -> int:
    probes = read_probes(home)
    if not probes:
        _write(sys.stdout, "no login probes recorded\n")
        return pc_exitcodes.OK
    for record in probes:
        state = {True: "true", False: "false", None: "unknown"}[record["loggedIn"]]
        _write(
            sys.stdout,
            "%s loggedIn=%s exit=%d created=%s\n"
            % (record["time"], state, record["exit"], "true" if record["created"] else "false"),
        )
    return pc_exitcodes.OK


def main(argv: Optional[Sequence[str]] = None, env: Optional[Mapping[str, str]] = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
    if args.command is None:
        parser.print_usage(sys.stderr)
        return pc_exitcodes.USAGE
    source = os.environ if env is None else env
    home_dir = source.get("HOME") or None
    search_path = source.get("PATH", "").split(os.pathsep)
    try:
        if args.command == "auth-check":
            code, line = auth_check(source, search_path, home_dir)
            _write(sys.stdout, line + "\n")
            return code
        home = harness_home(source, home_dir)
        if args.command == "spend":
            return _cmd_spend(home)
        if args.command == "probes":
            return _cmd_probes(home)
        call = _COMMAND_CALL[args.command]
        if args.run:
            guard(home, call)
            _write(sys.stderr, "paid path is enabled in task 3\n")
            return pc_exitcodes.USAGE
        for line in describe_call(call, home, getattr(args, "from_run", None)):
            _write(sys.stdout, line + "\n")
        return pc_exitcodes.OK
    except SpikeError as problem:
        label = "budget refused" if isinstance(problem, BudgetRefused) else "refused"
        _write(sys.stderr, "%s: %s\n" % (label, problem))
        return problem.exit_code


if __name__ == "__main__":
    sys.exit(main())
