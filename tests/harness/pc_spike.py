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
                                run is the absence of --run). With --run the guard runs first, then
                                the zero-token preflight, then the paid call; s2b needs --from-run
                                NAME, the run root folder of the s2a call under the runs root
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

import pc_allowlist
import pc_exitcodes
import pc_flags
import pc_leakgate
import pc_manifest
import pc_preflight
import pc_runroot
import pc_sanitize
import pc_stream

HARNESS_HOME_ENV = "PRECLEAR_HARNESS_HOME"
DEFAULT_HOME_NAME = ".preclear-harness"
CONFIG_DIR_NAME = "claude-config"
RUNS_DIR_NAME = "runs"
RUNS_ROOT_ENV = "PRECLEAR_RUNS_ROOT"
# The runs root lies outside every home folder: Claude Code loads the .claude/CLAUDE.md and
# .claude/rules files of every ancestor folder of the working directory as Project instructions, so a
# run root under a home folder would load that user's global rules (spike S1, 2026-10-26). Built
# from pieces so no source line holds a home-shaped path.
DEFAULT_RUNS_ROOT = os.sep.join(["", "Users", "Shared", "preclear-harness", "runs"])
_ANCESTOR_INSTRUCTION_NAMES = (
    "CLAUDE.md",
    "CLAUDE.local.md",
    os.path.join(".claude", "CLAUDE.md"),
    os.path.join(".claude", "rules"),
)
BINARY_CHUNK = 16 * 1024 * 1024
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


class LeakRefused(SpikeError):
    exit_code = pc_exitcodes.LEAK_REFUSED


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


def local_user_homes(home_dir: Optional[str] = None) -> List[str]:
    """Return the realpaths of the local users' home folders (never the shared folder).

    The given home, the account database's home folders under the usual user roots, and every
    folder directly below those roots except the shared one. Used only for the runs-root check.
    """
    roots = (os.sep + "Users", os.sep + "home")
    found = set()
    if home_dir:
        found.add(os.path.realpath(home_dir))
    try:
        import pwd

        for entry in pwd.getpwall():
            directory = entry.pw_dir
            if directory and any(directory.startswith(root + os.sep) for root in roots):
                found.add(os.path.realpath(directory))
    except (ImportError, KeyError, OSError):
        pass
    for root in roots:
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in names:
            if name in ("Shared", ".localized") or name.startswith("."):
                continue
            candidate = os.path.join(root, name)
            if os.path.isdir(candidate):
                found.add(os.path.realpath(candidate))
    found.discard(os.sep)
    return sorted(found)


def runs_root(
    env: Optional[Mapping[str, str]] = None,
    home_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
    homes: Optional[Sequence[str]] = None,
) -> str:
    """Return the realpath of the runs root; refuse an unusable one (HomeRefused, exit 2).

    The folder is PRECLEAR_RUNS_ROOT when set, else DEFAULT_RUNS_ROOT. It must be absolute, outside
    the repository, outside the user's own Claude folder, outside every local user's home folder, and
    none of its ancestor folders may hold an instruction file or folder that Claude Code would load
    as a Project instruction. Nothing is created here (zero tokens, zero side effects).
    """
    source = os.environ if env is None else env
    raw = source.get(RUNS_ROOT_ENV) or DEFAULT_RUNS_ROOT
    if not os.path.isabs(raw):
        raise HomeRefused("the runs root must be an absolute path")
    resolved = os.path.realpath(raw)
    repo = os.path.realpath(repo_root if repo_root else _REPO_ROOT)
    home = home_dir if home_dir else os.path.expanduser("~")
    own = os.path.realpath(os.path.join(home, ".claude"))
    if _within(resolved, repo) or _within(repo, resolved):
        raise HomeRefused("the runs root must be outside the repository")
    if _within(resolved, own):
        raise HomeRefused("the runs root must be outside the user's own Claude config")
    for user_home in (local_user_homes(home_dir) if homes is None else homes):
        if _within(resolved, os.path.realpath(user_home)):
            raise HomeRefused(
                "the runs root must not be inside a local user's home folder: Claude Code loads the "
                "instruction files of every ancestor folder"
            )
    ancestor = os.path.dirname(resolved)
    while True:
        for name in _ANCESTOR_INSTRUCTION_NAMES:
            if os.path.lexists(os.path.join(ancestor, name)):
                raise HomeRefused(
                    "an ancestor folder of the runs root holds an instruction file or folder that would be loaded"
                )
        parent = os.path.dirname(ancestor)
        if parent == ancestor:
            break
        ancestor = parent
    return resolved


def ensure_runs_root(path: str) -> None:
    """Create every missing level of the runs root with mode 0700; existing levels are tolerated."""
    pending = []
    current = path
    while not os.path.isdir(current):
        pending.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for level in reversed(pending):
        try:
            os.mkdir(level, 0o700)
        except FileExistsError:
            if not os.path.isdir(level):
                raise SpikeError("the runs root name is taken by something that is not a folder") from None


# ---------------------------------------------------------------------------------------------
# Time, run roots and the materialiser
# ---------------------------------------------------------------------------------------------


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def new_run_root(
    home: str,
    call: str,
    attempt: int,
    stamp: Optional[str] = None,
    runs_dir: Optional[str] = None,
) -> str:
    """Create <home>/runs/spike-<call>-a<attempt>-<UTC stamp> exclusively and return its realpath.

    The runs folder is created when it is missing and tolerated when it exists; the run root itself
    is never reused (pc_runroot raises RunRootCollision).
    """
    if call not in CALLS:
        raise ValueError("unknown call name")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if runs_dir is None:
        runs = os.path.join(home, RUNS_DIR_NAME)
        os.makedirs(runs, mode=0o700, exist_ok=True)
    else:
        runs = runs_dir
        ensure_runs_root(runs)
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
    runs_dir: Optional[str] = None,
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
    runs = os.path.realpath(runs_dir) if runs_dir else os.path.join(os.path.realpath(harness_home_dir), RUNS_DIR_NAME)
    if not os.path.isdir(root):
        raise ValueError("the run root does not exist")
    if not _within(root, runs) or root == runs:
        raise ValueError("the run root must lie under the runs folder")
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


def _effective(records: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, int], Dict[str, Any]]:
    """Return the effective record per (call name, attempt): a later line supersedes an earlier one.

    The ledger stays append-only. The paid path writes a pessimistic line before it launches a call
    (unknown cost, which counts as the call's cap) and a second line for the same attempt once the
    actual cost is known; the second line supersedes the first, and the pair is still one attempt.
    """
    latest: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for record in records:
        latest[(record["call"], record["attempt"])] = record
    return latest


def _total_of(records: Sequence[Dict[str, Any]]) -> Decimal:
    total = Decimal("0")
    for record in _effective(records).values():
        cost = record["total_cost_usd"]
        total += CALLS[record["call"]].cap if cost is None else Decimal(cost)
    return total


def recorded_total(home: str) -> Decimal:
    """Sum the effective ledger lines; a call with an unknown cost counts as its cap."""
    return _total_of(read_spend(home))


def remaining(home: str) -> Decimal:
    return TOTAL_CAP - recorded_total(home)


def attempts_made(home: str, call: str) -> int:
    if call not in CALLS:
        raise ValueError("unknown call name")
    return sum(1 for key in _effective(read_spend(home)) if key[0] == call)


def guard(home: str, call: str) -> int:
    """Refuse before a paid call; return the number of this attempt when it may go ahead.

    Refused (BudgetRefused, exit 18) when the call name has used up MAX_ATTEMPTS, or when the
    recorded spend plus this call's cap would exceed TOTAL_CAP.
    """
    if call not in CALLS:
        raise ValueError("unknown call name")
    records = read_spend(home)
    used = sum(1 for key in _effective(records) if key[0] == call)
    if used >= MAX_ATTEMPTS:
        raise BudgetRefused("the attempt limit for this call name is used up")
    if _total_of(records) + CALLS[call].cap > TOTAL_CAP:
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
# Spike S1: the isolation assertions, declared before any run (D-02)
# ---------------------------------------------------------------------------------------------

S1_PROMPT = "Reply with exactly the one word: ready."
CALL_TIMEOUT_SECONDS = 600

HOW_INIT = "init"
HOW_HOOK = "hook"
HOW_NONE = "not-assertable"

S1_ASSERTION_IDS = (
    "permission-mode-default",
    "model-pinned",
    "skill-preclear-present",
    "mcp-servers-empty",
    "no-non-builtin-plugins",
    "user-names-absent",
    "no-user-instruction-outside-config",
    "project-claude-md-loaded",
    "project-local-inside-run-root",
)
_AUDIT_IDS = S1_ASSERTION_IDS[6:]

# The user's own skill set includes preclear (the project install carries the same name), so the
# absence check cannot use that name as a contamination signal. The exclusion is counted and stated
# in the findings.
ABSENCE_EXCLUDED = frozenset(["preclear"])

_MEMORY_TYPES = ("User", "Project", "Local", "Managed")
_HOOK_SUBTYPES = ("hook_started", "hook_progress", "hook_response")

S1_ALTERNATIVES = (
    "alternatives for bokiko: (1) accept a by-construction label for the instruction audit, "
    "with the decision dated in the findings; (2) try a canary approach, a planted marker in an "
    "ancestor or user-level file that a leaking run would show; (3) the audit is changed"
)


class S1Outcome(NamedTuple):
    status: str  # "pass" or "stop"
    assertions: List[Tuple[str, str, bool]]
    counts: Dict[str, Any]
    reason: str


def _real(path: str) -> str:
    return os.path.realpath(path)


def _item_name(item: Any) -> Optional[str]:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("name"), str):
        return item["name"]
    return None


def _names_of(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    found = []
    for item in values:
        name = _item_name(item)
        if name is not None:
            found.append(name)
    return found


def _forms(name: str) -> List[str]:
    return [name, name.lstrip("/"), name.split(":")[-1]]


def hook_entries(
    events: Sequence[Dict[str, Any]],
    hooklog_lines: Optional[Sequence[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], str]:
    """Return (the instruction entries seen, the source tag: logger, stream, both or none).

    The logger file carries file_path, memory_type and load_reason per InstructionsLoaded event. A
    stream hook event counts only when it carries a file_path and a memory_type itself: the plain
    stream events of a hook that prints nothing show that the hook fired, not what it loaded.
    """
    seen: List[Dict[str, Any]] = []
    keys = set()
    from_logger = False
    from_stream = False
    for line in hooklog_lines or []:
        if isinstance(line, dict):
            seen.append(line)
            from_logger = True
            keys.add((line.get("file_path"), line.get("memory_type")))
    for event in events:
        if event.get("type") != "system" or event.get("subtype") not in _HOOK_SUBTYPES:
            continue
        if event.get("hook_event") != "InstructionsLoaded":
            continue
        for holder in (event, event.get("input"), event.get("data")):
            if isinstance(holder, dict) and isinstance(holder.get("file_path"), str) and isinstance(
                holder.get("memory_type"), str
            ):
                key = (holder["file_path"], holder["memory_type"])
                if key not in keys:
                    keys.add(key)
                    seen.append(
                        {
                            "file_path": holder["file_path"],
                            "memory_type": holder["memory_type"],
                            "load_reason": holder.get("load_reason")
                            if isinstance(holder.get("load_reason"), str)
                            else None,
                        }
                    )
                from_stream = True
                break
    if from_logger and from_stream:
        tag = "both"
    elif from_logger:
        tag = "logger"
    elif from_stream:
        tag = "stream"
    else:
        tag = "none"
    return seen, tag


def hit_candidates(init: Dict[str, Any], local_names: Any) -> frozenset:
    """Return the user names that appear in the init lists (a run-time set, never printed)."""
    effective = frozenset(local_names) - ABSENCE_EXCLUDED
    found = set()
    for key in ("skills", "slash_commands", "agents", "plugins"):
        for name in _names_of(init.get(key)):
            for form in _forms(name):
                if form in effective:
                    found.add(form)
    return frozenset(found)


def _absence(init: Dict[str, Any], local_names: Any, binary_defined: Any = frozenset()) -> Tuple[int, int, int, int]:
    """Return (name set size, number excluded, leak hits, collisions). Never a name.

    A name that the Claude binary itself defines is a collision with a bundled skill or command, not
    a leak (bokiko's decision of 2026-10-26); every other hit is a leak.
    """
    names = frozenset(local_names)
    effective = names - ABSENCE_EXCLUDED
    defined = frozenset(binary_defined)
    hits = 0
    collisions = 0
    for key in ("skills", "slash_commands", "agents", "plugins"):
        for name in _names_of(init.get(key)):
            matched = [form for form in _forms(name) if form in effective]
            if not matched:
                continue
            if any(form in defined for form in matched):
                collisions += 1
            else:
                hits += 1
    return len(effective), len(names & ABSENCE_EXCLUDED), hits, collisions


def _plugins_builtin_only(plugins: Any) -> bool:
    """True when init.plugins is a list and every entry is a plugin whose source ends in @builtin."""
    if not isinstance(plugins, list):
        return False
    for item in plugins:
        if not isinstance(item, dict):
            return False
        source = item.get("source")
        if not isinstance(source, str) or not source.endswith("@builtin"):
            return False
    return True


def builtin_plugin_sources(plugins: Any) -> List[str]:
    if not isinstance(plugins, list):
        return []
    return sorted(
        item["source"] for item in plugins if isinstance(item, dict) and isinstance(item.get("source"), str)
    )


def binary_defines(path: str, names: Any) -> frozenset:
    """Return the subset of names that the binary at path defines as name:"<name>" (a bytes scan).

    The file is read in chunks with an overlap so a definition across a chunk boundary is found.
    Only the matching subset is returned.
    """
    wanted = dict((('name:"%s"' % name).encode("utf-8"), name) for name in names)
    found = set()
    if not wanted:
        return frozenset()
    overlap = max(len(needle) for needle in wanted) - 1
    tail = b""
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(BINARY_CHUNK)
            if not chunk:
                break
            window = tail + chunk
            for needle, name in wanted.items():
                if name not in found and needle in window:
                    found.add(name)
            tail = window[-overlap:] if overlap > 0 else b""
    return frozenset(found)


def s1_evaluation(
    events: Sequence[Dict[str, Any]],
    hooklog_lines: Optional[Sequence[Dict[str, Any]]],
    local_names: Any,
    project_path: str,
    run_root: str,
    config_dir_path: str,
    binary_defined: Any = frozenset(),
) -> Tuple[List[Tuple[str, str, bool]], Dict[str, Any]]:
    """Return (the nine assertions, the counts) for one S1 capture."""
    init = pc_stream.init_manifest(events)
    result: List[Tuple[str, str, bool]] = []
    skills = _names_of(init.get("skills"))
    result.append(("permission-mode-default", HOW_INIT, init.get("permissionMode") == pc_flags.PERMISSION_MODE))
    result.append(("model-pinned", HOW_INIT, init.get("model") == PINNED_MODEL))
    result.append(
        ("skill-preclear-present", HOW_INIT, any("preclear" in (name, name.split(":")[-1]) for name in skills))
    )
    result.append(("mcp-servers-empty", HOW_INIT, init.get("mcp_servers") == []))
    result.append(("no-non-builtin-plugins", HOW_INIT, _plugins_builtin_only(init.get("plugins"))))
    size, excluded, hits, collisions = _absence(init, local_names, binary_defined)
    result.append(("user-names-absent", HOW_INIT, hits == 0))

    entries, source = hook_entries(events, hooklog_lines)
    counts: Dict[str, Any] = {
        "user_names": size,
        "user_names_excluded": excluded,
        "user_name_hits": hits,
        "user_name_collisions": collisions,
        "audit_source": source,
        "entries_user": 0,
        "entries_project": 0,
        "entries_local": 0,
        "entries_managed": 0,
        "entries_unknown": 0,
    }
    for entry in entries:
        kind = entry.get("memory_type")
        path = entry.get("file_path")
        if kind in _MEMORY_TYPES and isinstance(path, str):
            counts["entries_%s" % kind.lower()] += 1
        else:
            counts["entries_unknown"] += 1
    if not entries:
        for name in _AUDIT_IDS:
            result.append((name, HOW_NONE, False))
        return result, counts

    config_real = _real(config_dir_path)
    run_real = _real(run_root)
    claude_md = _real(os.path.join(project_path, "CLAUDE.md"))
    user_ok = True
    inside_ok = True
    project_loaded = False
    for entry in entries:
        kind = entry.get("memory_type")
        path = entry.get("file_path")
        if kind not in _MEMORY_TYPES or not isinstance(path, str) or not path:
            user_ok = False
            continue
        real = _real(path)
        if kind == "User" and not _within(real, config_real):
            user_ok = False
        if kind in ("Project", "Local") and not _within(real, run_real):
            inside_ok = False
        if kind == "Project" and real == claude_md:
            project_loaded = True
    result.append(("no-user-instruction-outside-config", HOW_HOOK, user_ok))
    result.append(("project-claude-md-loaded", HOW_HOOK, project_loaded))
    result.append(("project-local-inside-run-root", HOW_HOOK, inside_ok))
    return result, counts


def s1_assertions(
    events: Sequence[Dict[str, Any]],
    hooklog_lines: Optional[Sequence[Dict[str, Any]]],
    local_names: Any,
    project_path: str,
    run_root: str,
    config_dir_path: str,
    binary_defined: Any = frozenset(),
) -> List[Tuple[str, str, bool]]:
    """Return a list of (assertion id, how asserted, passed) in the declared order.

    How asserted is init (read from the init event), hook (read from the InstructionsLoaded entries
    in the stream or the logger file) or not-assertable (no instruction entry was seen by either
    source; that assertion is then a failure and the run is a stop, never a degraded pass).
    """
    return s1_evaluation(
        events, hooklog_lines, local_names, project_path, run_root, config_dir_path, binary_defined
    )[0]


def evaluate_s1(
    events: Sequence[Dict[str, Any]],
    hooklog_lines: Optional[Sequence[Dict[str, Any]]],
    local_names: Any,
    project_path: str,
    run_root: str,
    config_dir_path: str,
    binary_defined: Any = frozenset(),
) -> S1Outcome:
    """Evaluate the assertions. Anything but a full pass is a stop for bokiko's decision (D-02)."""
    assertions, counts = s1_evaluation(
        events, hooklog_lines, local_names, project_path, run_root, config_dir_path, binary_defined
    )
    unassertable = [name for name, how, _passed in assertions if how == HOW_NONE]
    failed = [name for name, how, passed in assertions if not passed and how != HOW_NONE]
    if unassertable:
        reason = (
            "the instruction audit is not assertable: no InstructionsLoaded entry with a file path "
            "was seen in the stream or in the logger file"
        )
        return S1Outcome("stop", assertions, counts, reason)
    if failed:
        return S1Outcome("stop", assertions, counts, "isolation assertion(s) failed: %s" % ", ".join(failed))
    return S1Outcome("pass", assertions, counts, "")


def describe_s1(outcome: S1Outcome) -> List[str]:
    """Return the lines to print: assertion ids with pass or fail, counts only, never a name."""
    lines = []
    for name, how, passed in outcome.assertions:
        lines.append("assertion %s: %s (%s)" % (name, "pass" if passed else "FAIL", how))
    c = outcome.counts
    lines.append(
        "user names: %d listed, %d excluded, %d leak hit(s), %d binary-defined collision(s); audit source: %s"
        % (
            c["user_names"],
            c["user_names_excluded"],
            c["user_name_hits"],
            c["user_name_collisions"],
            c["audit_source"],
        )
    )
    lines.append(
        "instruction entries: user=%d project=%d local=%d managed=%d unknown=%d"
        % (c["entries_user"], c["entries_project"], c["entries_local"], c["entries_managed"], c["entries_unknown"])
    )
    if outcome.status != "pass":
        lines.append("STOP: %s" % outcome.reason)
        if any(how == HOW_NONE for _name, how, _passed in outcome.assertions):
            lines.append(S1_ALTERNATIVES)
        lines.append(
            "the isolation claim is not shown as specified; no manifest and no findings were written, "
            "and bokiko decides what happens next"
        )
    return lines


# ---------------------------------------------------------------------------------------------
# Sanitised data files (T-02-32): sanitiser, Python gate, then an exclusive write
# ---------------------------------------------------------------------------------------------


_SOCKET_PATH = re.compile(rb"/tmp/cc-socks/[0-9]+\.sock")


def scrub_volatile(data: bytes) -> bytes:
    """Replace the init event's process-bound socket path (a temp path with a pid) by a token."""
    return _SOCKET_PATH.sub(b"<tmp>/cc-socks/<pid>.sock", data)


def sanitize_to_data(data: bytes, dest: str, sanitizer: Any) -> None:
    """Sanitise DATA, require zero gate findings and create DEST exclusively.

    An existing target is never overwritten (FileExistsError, checked first). A capture that the
    sanitiser cannot process or that still holds a finding is refused (LeakRefused, exit 14) and
    nothing is written; messages name rule ids and counts only, never a value.
    """
    if os.path.lexists(dest):
        raise FileExistsError("the data file already exists")
    try:
        clean = sanitizer.sanitize_bytes(scrub_volatile(data))
    except pc_sanitize.SanitizerError:
        raise LeakRefused("the sanitiser could not process the capture; nothing was written") from None
    try:
        findings = pc_leakgate.scan_bytes(os.path.basename(dest), clean, sanitizer.deny_entries())
    except pc_leakgate.ScannerError:
        raise LeakRefused("the leak gate could not scan the capture; nothing was written") from None
    if findings:
        shown = ", ".join("%s x%d" % (rule, count) for rule, count in findings)
        raise LeakRefused("the leak gate found a leak after sanitising (%s); nothing was written" % shown)
    pc_runroot.write_exclusive(dest, clean, 0o644)


# ---------------------------------------------------------------------------------------------
# The paid path: one launcher for every call
# ---------------------------------------------------------------------------------------------


class CallResult(NamedTuple):
    returncode: Optional[int]
    timed_out: bool
    stdout: bytes
    stderr: bytes


def run_claude(
    argv: Sequence[str],
    env: Mapping[str, str],
    cwd: str,
    prompt: str,
    timeout: int,
    raw_dir: str,
    stem: str,
) -> CallResult:
    """Run one claude -p call and keep the raw bytes under raw_dir by exclusive creation.

    The prompt goes to standard input, never to argv. A timeout kills the child and keeps whatever
    it wrote. The raw files stay under the run root inside the harness home, outside the repository.
    """
    try:
        done = subprocess.run(
            list(argv),
            env=dict(env),
            cwd=cwd,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
        )
        result = CallResult(done.returncode, False, done.stdout, done.stderr)
    except subprocess.TimeoutExpired as expired:
        result = CallResult(None, True, expired.stdout or b"", expired.stderr or b"")
    except OSError:
        result = CallResult(None, False, b"", b"")
    pc_runroot.write_exclusive(os.path.join(raw_dir, stem + ".stdout"), result.stdout, 0o600)
    pc_runroot.write_exclusive(os.path.join(raw_dir, stem + ".stderr"), result.stderr, 0o600)
    return result


def _read_hooklog(path: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """Return the logger file's records, or None when the file does not exist."""
    if path is None or not os.path.exists(path):
        return None
    records: List[Dict[str, Any]] = []
    for line in _read_bytes(path).decode("utf-8", "replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        records.append(record if isinstance(record, dict) else {"error": "unparseable"})
    return records


def _plain_init_event(stdout: bytes) -> Dict[str, Any]:
    """Return the init event with plain json (floats stay floats) for the manifest file."""
    for line in stdout.split(b"\n"):
        if not line:
            continue
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            continue
        if isinstance(event, dict) and event.get("type") == "system" and event.get("subtype") == "init":
            return event
    raise pc_stream.StreamError("no init event")


def build_manifest(
    init_event: Dict[str, Any],
    assertions: Sequence[Tuple[str, str, bool]],
    counts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return the init event's own fields plus the frozen assertion baseline (counts only)."""
    manifest = dict(init_event)
    manifest["baseline"] = {
        "skills": init_event.get("skills"),
        "plugins": init_event.get("plugins"),
        "mcp_servers": init_event.get("mcp_servers"),
        "agents": init_event.get("agents"),
        "slash_commands": init_event.get("slash_commands"),
        "tools": init_event.get("tools"),
        "builtin_plugins": builtin_plugin_sources(init_event.get("plugins")),
        "counts": dict(counts) if counts is not None else {},
        "assertions": dict((name, how) for name, how, _passed in assertions),
    }
    return manifest


def _caller_map(paths: Mapping[str, Optional[str]]) -> Dict[str, str]:
    mapping = {str(paths["run_root"]): "<run>"}
    if paths.get("wrapper"):
        mapping[str(paths["wrapper"])] = "<helper>"
    if paths.get("auto_memory"):
        mapping[str(paths["auto_memory"])] = "<auto-memory-root>"
    return mapping


def _reconcile(home: str, call: str, attempt: int, version: Optional[str], stdout: bytes) -> Tuple[Optional[Any], str]:
    """Append the actual-cost line for an attempt; return (parsed events or None, subtype)."""
    try:
        events = pc_stream.parse_stream(stdout)
        summary = pc_stream.result_summary(events)
        pc_stream.init_manifest(events)
    except pc_stream.StreamError:
        append_spend(home, call, attempt, None, "no-result", version)
        return None, "no-result"
    subtype = summary["subtype"] if isinstance(summary["subtype"], str) else "no-result"
    cost = summary["total_cost_usd"]
    append_spend(home, call, attempt, cost, subtype, version)
    return events, subtype


def run_s1(
    home: str,
    base_env: Mapping[str, str],
    repo_root: str,
    data_dir: str,
    search_path: Optional[Sequence[str]],
    home_dir: Optional[str],
    runs_dir: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Run spike S1 for real and return (exit code, lines to print). Spends tokens.

    Order: the guard (BudgetRefused propagates), the zero-token preflight (nothing is recorded when
    it blocks), a fresh run root with the logger hook, the pessimistic ledger line, the call, the
    reconciling ledger line, the assertions. A pass writes the sanitised init manifest; a failed or
    unassertable assertion, or an infrastructure failure, writes nothing under data_dir.
    """
    attempt = guard(home, "s1")
    cfg, _created = ensure_config_dir(base_env, home_dir, repo_root)
    result, version = spike_preflight(search_path, cfg, base_env)
    if result.state != pc_preflight.OK:
        return result.exit_code, [result.line()]
    claude = pc_preflight.find_claude(search_path)
    if claude is None:
        return pc_exitcodes.PREFLIGHT_BLOCKED, ["claude not found on PATH"]
    spec = CALLS["s1"]
    session_id = str(uuid.uuid4())
    runs = runs_dir if runs_dir else runs_root(base_env, home_dir, repo_root)
    run_root = new_run_root(home, "s1", attempt, runs_dir=runs)
    paths = materialize(repo_root, run_root, session_id, home, audit_hook=True, runs_dir=runs)
    tools = pc_flags.build_allowed_tools(str(paths["wrapper"]), pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = pc_flags.build_argv(
        claude, session_id, str(paths["settings"]), tools, spec.turns, spec.cap, include_hook_events=True
    )
    env = pc_flags.build_env(base_env, cfg, str(paths["ckpt"]))
    append_spend(home, "s1", attempt, None, "launched", version)
    outcome_call = run_claude(argv, env, str(paths["project"]), S1_PROMPT, CALL_TIMEOUT_SECONDS, str(paths["raw"]), "s1")
    events, subtype = _reconcile(home, "s1", attempt, version, outcome_call.stdout)
    lines = ["call s1 attempt %d finished: %s" % (attempt, subtype)]
    if events is None or outcome_call.timed_out or subtype != "success":
        lines.append(
            "infrastructure failure (timeout, no result or malformed stream); one retry is allowed by the guard"
            if attempt < MAX_ATTEMPTS
            else "infrastructure failure and no retry is left"
        )
        return pc_exitcodes.PREFLIGHT_FAIL, lines
    names = local_user_names(home_dir) if home_dir else frozenset()
    candidates = hit_candidates(pc_stream.init_manifest(events), names)
    defined = binary_defines(os.path.realpath(claude), candidates) if candidates else frozenset()
    outcome = evaluate_s1(
        events,
        _read_hooklog(paths["hooklog"]),
        names,
        str(paths["project"]),
        str(paths["run_root"]),
        cfg,
        defined,
    )
    lines.extend(describe_s1(outcome))
    if outcome.status != "pass":
        return pc_exitcodes.PREFLIGHT_FAIL, lines
    manifest = build_manifest(_plain_init_event(outcome_call.stdout), outcome.assertions, outcome.counts)
    sanitizer = pc_sanitize.Sanitizer.from_machine(repo_root, _caller_map(paths))
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    sanitize_to_data(text.encode("utf-8"), os.path.join(data_dir, "s1-init-manifest.json"), sanitizer)
    lines.append("wrote the sanitised init manifest to the data folder")
    return pc_exitcodes.OK, lines


# ---------------------------------------------------------------------------------------------
# Spike S2: the stream shape, the seven-command policy probe, session handling, the verbose probe
# ---------------------------------------------------------------------------------------------


class Probe(NamedTuple):
    key: str
    template: str
    expected: str  # "allowed" or "denied", written here before any run


BIND_SESSION_ID = "aaaaaaaa-0000-4000-8000-000000000001"

# Declared before any S2 run (HARN-06). {wrapper} and {run_root} are filled at run time. The bind
# probe uses a session id nobody holds and a ledger that does not exist, so even an unexpected
# allow would mutate nothing (T-02-34).
PROBE_COMMANDS: Tuple[Probe, ...] = (
    Probe("wrapper-status", "{wrapper} status", "allowed"),
    Probe(
        "git-status",
        "git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none",
        "allowed",
    ),
    Probe("pwd", "pwd -P", "allowed"),
    Probe("pwd-and-status", "pwd -P && {wrapper} status", "allowed"),
    Probe("pwd-and-echo", "pwd -P && echo done", "denied"),
    Probe("variable-expansion", 'wc -c "$PWD/CLAUDE.md"', "denied"),
    Probe(
        "wrapper-bind",
        "{wrapper} bind --ledger {run_root}/ckpt/ledgers/no-such-ledger.md --session " + BIND_SESSION_ID,
        "denied",
    ),
)

_S2A_PROMPT = (
    "You are running a command-policy probe. Run each of the following commands exactly as written, "
    "one per Bash tool call, in order, without combining them, without altering them or quoting them "
    "differently, without retrying a refused command and without substituting another command. If a "
    "command is refused or fails, note that in one short line and continue with the next one. Do "
    "nothing else. When every command has been attempted, finish with the one word: done.\n\n"
)

PROMPTS: Dict[str, str] = {
    "s1": S1_PROMPT,
    "s2b": "Reply with exactly the one word: resumed.",
    "verbose": "x",
}


def probe_commands(wrapper: str, run_root: str) -> List[Tuple[Probe, str]]:
    """Return (probe, command) pairs with the wrapper path and run root filled in."""
    return [
        (probe, probe.template.replace("{wrapper}", wrapper).replace("{run_root}", run_root))
        for probe in PROBE_COMMANDS
    ]


def s2a_prompt(commands: Sequence[Tuple[Probe, str]]) -> str:
    lines = ["%d. %s" % (index, command) for index, (_probe, command) in enumerate(commands, 1)]
    return _S2A_PROMPT + "\n".join(lines) + "\n"


def probe_rows(
    events: Sequence[Dict[str, Any]],
    commands: Sequence[Tuple[Probe, str]],
) -> List[Dict[str, Any]]:
    """Pair every probe command with its Bash tool call, result and the two structured denial signals.

    A command that no Bash call carried is reported with status missing. A reply or tool text that
    holds the word denied is never read (pc_stream looks at structured fields only).
    """
    table = pc_stream.probe_table(events)
    rows: List[Dict[str, Any]] = []
    for probe, command in commands:
        found = None
        for entry in table:
            if entry[1] == "Bash" and entry[2] is not None and entry[2].strip() == command.strip():
                found = entry
                break
        row: Dict[str, Any] = {
            "key": probe.key,
            "command": command,
            "expected": probe.expected,
            "status": "missing",
            "tool_use_id": None,
            "is_error": None,
            "permission_denied_event": None,
            "permission_denials_entry": None,
            "observed": None,
        }
        if found is not None:
            row["status"] = "observed"
            row["tool_use_id"] = found[0]
            row["is_error"] = found[3]
            row["permission_denied_event"] = found[4]
            row["permission_denials_entry"] = found[5]
            row["observed"] = "denied" if (found[4] or found[5]) else "allowed"
        rows.append(row)
    return rows


def session_facts(events: Sequence[Dict[str, Any]], requested: str) -> Dict[str, bool]:
    """Whether init.session_id and result.session_id equal the requested id."""
    init = pc_stream.init_manifest(events)
    summary = pc_stream.result_summary(events)
    return {
        "init_matches": init.get("session_id") == requested,
        "result_matches": summary.get("session_id") == requested,
    }


def matcher_view(command: str, wrapper: str) -> str:
    """What the bounded matcher model (pc_allowlist) says: allowed or denied."""
    rules = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    return "allowed" if pc_allowlist.is_allowed(command, rules).allowed else "denied"


class _Early(Exception):
    def __init__(self, code: int, lines: List[str]) -> None:
        Exception.__init__(self, "early return")
        self.code = code
        self.lines = lines


class _Setup(NamedTuple):
    attempt: int
    cfg: str
    version: Optional[str]
    claude: str
    runs: str


def _setup(
    call: str,
    home: str,
    base_env: Mapping[str, str],
    repo_root: str,
    search_path: Optional[Sequence[str]],
    home_dir: Optional[str],
    runs_dir: Optional[str],
) -> _Setup:
    """The common start of a paid call: guard, config directory, zero-token preflight, claude, runs root."""
    attempt = guard(home, call)
    cfg, _created = ensure_config_dir(base_env, home_dir, repo_root)
    result, version = spike_preflight(search_path, cfg, base_env)
    if result.state != pc_preflight.OK:
        raise _Early(result.exit_code, [result.line()])
    claude = pc_preflight.find_claude(search_path)
    if claude is None:
        raise _Early(pc_exitcodes.PREFLIGHT_BLOCKED, ["claude not found on PATH"])
    runs = runs_dir if runs_dir else runs_root(base_env, home_dir, repo_root)
    return _Setup(attempt, cfg, version, claude, runs)


def _infra_lines(call: str, attempt: int, subtype: str) -> List[str]:
    return [
        "call %s attempt %d finished: %s" % (call, attempt, subtype),
        "infrastructure failure (timeout, no result or malformed stream); one retry is allowed by the guard"
        if attempt < MAX_ATTEMPTS
        else "infrastructure failure and no retry is left",
    ]


def _precheck_free(paths: Sequence[str]) -> None:
    for path in paths:
        if os.path.lexists(path):
            raise FileExistsError("a file this call would write already exists")


def _row_line(row: Dict[str, Any], matcher: Optional[str]) -> str:
    if row["status"] == "missing":
        return "probe %s: missing (expected %s, no Bash call carried it)" % (row["key"], row["expected"])
    text = "probe %s: expected %s, observed %s (is_error %s, permission_denied event %s, permission_denials entry %s)" % (
        row["key"],
        row["expected"],
        row["observed"],
        row["is_error"],
        row["permission_denied_event"],
        row["permission_denials_entry"],
    )
    if matcher is not None and matcher != row["observed"]:
        text += "; matcher model says %s: DISAGREES" % matcher
    return text


def run_s2a(
    home: str,
    base_env: Mapping[str, str],
    repo_root: str,
    data_dir: str,
    search_path: Optional[Sequence[str]],
    home_dir: Optional[str],
    runs_dir: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Run spike S2a for real: the exact matrix flag set (no hook events) and the seven-command probe.

    Writes the sanitised stream fixture and the probe labels only when every probe command was
    observed and the wrapper bind was denied. A missing probe is the one reason for the retry; an
    allowed bind is a STOP for bokiko (it would mean the first layer of STUB-06 does not hold).
    """
    fixture = os.path.join(data_dir, "s2-stream.jsonl")
    labels_path = os.path.join(data_dir, "s2-probe-labels.json")
    _precheck_free([fixture, labels_path])
    try:
        setup = _setup("s2a", home, base_env, repo_root, search_path, home_dir, runs_dir)
    except _Early as early:
        return early.code, early.lines
    spec = CALLS["s2a"]
    session_id = str(uuid.uuid4())
    run_root = new_run_root(home, "s2a", setup.attempt, runs_dir=setup.runs)
    paths = materialize(repo_root, run_root, session_id, home, audit_hook=False, runs_dir=setup.runs)
    wrapper = str(paths["wrapper"])
    tools = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = pc_flags.build_argv(setup.claude, session_id, str(paths["settings"]), tools, spec.turns, spec.cap)
    env = pc_flags.build_env(base_env, setup.cfg, str(paths["ckpt"]))
    commands = probe_commands(wrapper, str(paths["run_root"]))
    raw = str(paths["raw"])
    pc_runroot.write_exclusive(os.path.join(raw, "session-id"), (session_id + "\n").encode("ascii"), 0o600)
    append_spend(home, "s2a", setup.attempt, None, "launched", setup.version)
    done = run_claude(argv, env, str(paths["project"]), s2a_prompt(commands), CALL_TIMEOUT_SECONDS, raw, "s2a")
    events, subtype = _reconcile(home, "s2a", setup.attempt, setup.version, done.stdout)
    if events is None or done.timed_out or subtype != "success":
        return pc_exitcodes.PREFLIGHT_FAIL, _infra_lines("s2a", setup.attempt, subtype)
    lines = ["call s2a attempt %d finished: %s" % (setup.attempt, subtype)]
    rows = probe_rows(events, commands)
    matchers = {}
    for row in rows:
        matcher = matcher_view(row["command"], wrapper) if row["status"] == "observed" else None
        matchers[row["key"]] = matcher
        lines.append(_row_line(row, matcher))
    facts = session_facts(events, session_id)
    init = pc_stream.init_manifest(events)
    lines.append("init.session_id matches the requested id: %s" % facts["init_matches"])
    lines.append("result.session_id matches the requested id: %s" % facts["result_matches"])
    lines.append("claude_code_version in init: %s" % init.get("claude_code_version"))
    missing = [row["key"] for row in rows if row["status"] == "missing"]
    if missing:
        lines.append(
            "a probe command was never run by the model; one retry is allowed by the guard"
            if setup.attempt < MAX_ATTEMPTS
            else "a probe command was never run and no retry is left"
        )
        return pc_exitcodes.PREFLIGHT_FAIL, lines
    bind = [row for row in rows if row["key"] == "wrapper-bind"][0]
    if bind["observed"] != "denied":
        lines.append(
            "STOP: the binary did not deny the wrapper bind; the first layer of STUB-06 is not shown, "
            "nothing was written, and bokiko decides"
        )
        return pc_exitcodes.PREFLIGHT_FAIL, lines
    sanitizer = pc_sanitize.Sanitizer.from_machine(repo_root, _caller_map(paths))
    label_rows = []
    for row in rows:
        entry = dict(row)
        entry["matcher"] = matchers[row["key"]]
        entry["heuristic"] = entry["matcher"] == "allowed" and row["observed"] == "denied"
        label_rows.append(entry)
    labels = {
        "claude_code_version": init.get("claude_code_version"),
        "wrapper_token": "<helper>",
        "run_token": "<run>",
        "probes": label_rows,
    }
    sanitize_to_data(done.stdout, fixture, sanitizer)
    sanitize_to_data((json.dumps(labels, indent=2, sort_keys=True) + "\n").encode("utf-8"), labels_path, sanitizer)
    lines.append("wrote the sanitised S2a stream and the probe labels to the data folder")
    return pc_exitcodes.OK, lines


def _run_paths(root: str) -> Dict[str, Optional[str]]:
    return {
        "run_root": root,
        "project": os.path.join(root, "project"),
        "wrapper": os.path.join(root, "wrapper", "checkpoint"),
        "ckpt": os.path.join(root, "ckpt"),
        "auto_memory": os.path.join(root, "auto-memory"),
        "raw": os.path.join(root, "raw"),
        "settings": os.path.join(root, "settings.json"),
        "hooklog": None,
    }


def run_s2b(
    home: str,
    base_env: Mapping[str, str],
    repo_root: str,
    data_dir: str,
    search_path: Optional[Sequence[str]],
    home_dir: Optional[str],
    from_run: str,
    runs_dir: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Run spike S2b for real: resume the S2a session in the same run root with --resume."""
    if (
        not isinstance(from_run, str)
        or from_run in ("", ".", "..")
        or os.path.basename(from_run) != from_run
        or os.sep in from_run
    ):
        raise HomeRefused("--from-run must be the name of a run root folder")
    runs = runs_dir if runs_dir else runs_root(base_env, home_dir, repo_root)
    root = os.path.join(os.path.realpath(runs), from_run)
    if not os.path.isdir(root) or os.path.islink(root):
        raise HomeRefused("--from-run does not name a run root under the runs folder")
    paths = _run_paths(root)
    fixture = os.path.join(data_dir, "s2b-stream.jsonl")
    _precheck_free([fixture, os.path.join(str(paths["raw"]), "s2b.stdout"), os.path.join(str(paths["raw"]), "s2b.stderr")])
    try:
        session_id = _read_bytes(os.path.join(str(paths["raw"]), "session-id")).decode("ascii").strip()
        if str(uuid.UUID(session_id)) != session_id:
            raise ValueError("not canonical")
    except (OSError, ValueError, UnicodeDecodeError):
        raise HomeRefused("the run root holds no usable session id; run s2a first") from None
    try:
        setup = _setup("s2b", home, base_env, repo_root, search_path, home_dir, runs)
    except _Early as early:
        return early.code, early.lines
    spec = CALLS["s2b"]
    tools = pc_flags.build_allowed_tools(str(paths["wrapper"]), pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = pc_flags.build_argv(
        setup.claude, session_id, str(paths["settings"]), tools, spec.turns, spec.cap, resume=True
    )
    env = pc_flags.build_env(base_env, setup.cfg, str(paths["ckpt"]))
    append_spend(home, "s2b", setup.attempt, None, "launched", setup.version)
    done = run_claude(argv, env, str(paths["project"]), PROMPTS["s2b"], CALL_TIMEOUT_SECONDS, str(paths["raw"]), "s2b")
    events, subtype = _reconcile(home, "s2b", setup.attempt, setup.version, done.stdout)
    if events is None or done.timed_out or subtype != "success":
        return pc_exitcodes.PREFLIGHT_FAIL, _infra_lines("s2b", setup.attempt, subtype)
    facts = session_facts(events, session_id)
    init = pc_stream.init_manifest(events)
    lines = [
        "call s2b attempt %d finished: %s" % (setup.attempt, subtype),
        "init.session_id matches the requested id: %s" % facts["init_matches"],
        "result.session_id matches the requested id: %s" % facts["result_matches"],
        "claude_code_version in init: %s" % init.get("claude_code_version"),
    ]
    sanitizer = pc_sanitize.Sanitizer.from_machine(repo_root, _caller_map(paths))
    sanitize_to_data(done.stdout, fixture, sanitizer)
    lines.append("wrote the sanitised S2b stream to the data folder")
    return pc_exitcodes.OK, lines


def run_verbose(
    home: str,
    base_env: Mapping[str, str],
    repo_root: str,
    data_dir: str,
    search_path: Optional[Sequence[str]],
    home_dir: Optional[str],
    runs_dir: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Run the verbose probe for real: stream-json without --verbose, one turn, the prompt x.

    Either answer is a finding (refused, or accepted), so the exit code is 0 whenever the probe ran.
    The cost counts as the call's cap unless a result event reports one.
    """
    del data_dir
    try:
        setup = _setup("verbose", home, base_env, repo_root, search_path, home_dir, runs_dir)
    except _Early as early:
        return early.code, early.lines
    spec = CALLS["verbose"]
    session_id = str(uuid.uuid4())
    run_root = new_run_root(home, "verbose", setup.attempt, runs_dir=setup.runs)
    paths = materialize(repo_root, run_root, session_id, home, audit_hook=False, runs_dir=setup.runs)
    tools = pc_flags.build_allowed_tools(str(paths["wrapper"]), pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = pc_flags.build_argv(setup.claude, session_id, str(paths["settings"]), tools, spec.turns, spec.cap)
    argv = [item for item in argv if item != "--verbose"]
    env = pc_flags.build_env(base_env, setup.cfg, str(paths["ckpt"]))
    append_spend(home, "verbose", setup.attempt, None, "launched", setup.version)
    done = run_claude(argv, env, str(paths["project"]), PROMPTS["verbose"], CALL_TIMEOUT_SECONDS, str(paths["raw"]), "verbose")
    _events, subtype = _reconcile(home, "verbose", setup.attempt, setup.version, done.stdout)
    sanitizer = pc_sanitize.Sanitizer.from_machine(repo_root, _caller_map(paths))
    stream_name = "stderr" if done.stderr.strip() else "stdout"
    text = (done.stderr if done.stderr.strip() else done.stdout).decode("utf-8", "replace")
    first = ""
    for line in text.splitlines():
        if line.strip():
            first = sanitizer.sanitize_text(line.strip())[:240]
            break
    return pc_exitcodes.OK, [
        "call verbose attempt %d finished: %s" % (setup.attempt, subtype),
        "verbose probe exit code: %s%s" % (done.returncode, " (timed out)" if done.timed_out else ""),
        "verbose probe bytes: stdout %d, stderr %d" % (len(done.stdout), len(done.stderr)),
        "verbose probe message (%s): %s" % (stream_name, first if first else "(none)"),
    ]


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
            data_dir = os.path.join(_REPO_ROOT, "tests", "harness", "data")
            common = (home, source, _REPO_ROOT, data_dir, search_path, home_dir)
            if call == "s1":
                code, lines = run_s1(*common)
            elif call == "s2a":
                code, lines = run_s2a(*common)
            elif call == "s2b":
                if not args.from_run:
                    _write(sys.stderr, "--from-run NAME is required with --run for s2b\n")
                    return pc_exitcodes.USAGE
                code, lines = run_s2b(*(common + (args.from_run,)))
            else:
                code, lines = run_verbose(*common)
            for line in lines:
                _write(sys.stdout, line + "\n")
            return code
        for line in describe_call(call, home, getattr(args, "from_run", None)):
            _write(sys.stdout, line + "\n")
        return pc_exitcodes.OK
    except SpikeError as problem:
        label = "budget refused" if isinstance(problem, BudgetRefused) else "refused"
        _write(sys.stderr, "%s: %s\n" % (label, problem))
        return problem.exit_code


if __name__ == "__main__":
    sys.exit(main())
