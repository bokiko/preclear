"""The clean-clone bootstrap (RERUN-02; D-09, D-10, D-11, D-12, D-13b).

Run it as python3 -E -s -B pc_cleanclone.py, never with -I, because the pc_ modules import each other.

    --claude PATH       the absolute path of the pinned claude build (required)
    --preflight-only    the free probe: clone, check, then run the stub check and the strict preflight under the
                        scrubbed environment and stop; it starts no row and no model
    --budget AMOUNT     the full run: the most the caller allows the matrix to cost; handed to the clone's own driver
    --selftest          the full run also runs the clone's own self-test first (zero model calls, several minutes)
    --source SOURCE     an https address or an existing local folder to clone; the default is the origin address read
                        at run time from the main tree's git configuration and never printed or stored
    --real-home         give the child the caller's real home folder instead of the throwaway one (a recorded
                        deviation that needs the owner's word; it is printed and written as home kind real)

What it does, in order (the free steps first, nothing is deleted, reused or overwritten):

  1. creates one never-used folder D under the caller's runs root with three siblings: repo (the clone), runs (the
     clone's own runs root) and home (an empty throwaway home), then clones the source into repo under git hygiene
     variables and prints the clone's head, the main tree's head and whether they are equal;
  2. builds the child environment from an empty dict with exactly the names of ALLOWED_NAMES, and asserts before any
     spend, as counts, that no checkpoint helper is reachable (exit 11 on any non-zero count);
  3. runs the clone's own scripts as child processes under that environment: the self-test (optional), the dry run of
     the whole matrix with the same budget, the stub check and the strict preflight, then the matrix itself;
  4. asserts after the run, as counts, that every helper call hit the clone's stub, writes the clone-facts file (names
     and counts only), runs finalize in the clone, copies the finalized folder back into the main tree through the
     leak gate with the main tree's deny entries, and prints the entries and folders counts.

Exit codes: 0 done; 2 usage; the exit code of the step that refused (10 to 19) as the clone's own scripts return it;
11 also for a pre-assertion count above zero, for a call that reached anything but the clone's stub, and for a listing
that does not add up; 12 for an unusable runs root or harness home; 16 when the folder name is taken; 17 when the
copy-back destination exists. After a matrix exit of 10, 11, 18 or 19 with at least one outcome folder the bootstrap
still files and copies back what was measured, then exits with the matrix's code. The matrix is not resumable, so a
budget stop must not strand measured rows in the clone.

Messages are fixed text: counts, ids, a UTC-stamped folder name and heads only. Child output is scrubbed of every known
path before it is printed. The module imports the main tree's modules for its own checks only; every child process is
the clone's own script.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, TextIO, Tuple

import pc_baseline
import pc_exitcodes
import pc_promote
import pc_runroot
import pc_sanitize
import pc_spike

PROG = "pc_cleanclone.py"
USAGE_LINE = (
    "usage: pc_cleanclone.py --claude PATH (--preflight-only | --budget AMOUNT [--selftest]) "
    "[--source SOURCE] [--real-home]"
)
MESSAGE_USAGE = "invalid command line"
MESSAGE_CLAUDE = "the claude argument is not an absolute path to an executable file"
MESSAGE_SOURCE = "the source is neither an https address nor an existing folder"
MESSAGE_NO_SOURCE = "no source was given and the main tree has no usable origin address"
MESSAGE_FOLDER_TAKEN = "RUNROOT_COLLISION: the clone folder name is taken; nothing was reused"
MESSAGE_RUNS_ROOT = "BLOCKED: the runs root is unusable"
MESSAGE_HARNESS_HOME = "BLOCKED: the harness home folder is unusable"
MESSAGE_CLONE = "ERROR: the clone could not be made"
MESSAGE_FACTS = "ERROR: the clone facts could not be written in the fixed schema"
MESSAGE_NOTHING_FILED = "nothing was filed in the clone, so there is nothing to finalize or copy back"
MESSAGE_KEPT = "the clone folder keeps whatever was filed; nothing was copied back"
MESSAGE_REAL_HOME = (
    "WARNING: --real-home gives the child this account's real home folder; this differs from the minimal "
    "environment and is recorded as home kind real"
)

SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
ALLOWED_NAMES = (
    "HOME",
    "PATH",
    "PRECLEAR_HARNESS_HOME",
    "PRECLEAR_RUNS_ROOT",
    "DISABLE_AUTOUPDATER",
    "TERM",
    "LANG",
)
DEFAULT_TERM = "xterm-256color"
DEFAULT_LANG = "en_US.UTF-8"
LAYOUT_NAMES = ("repo", "runs", "home")
CLONE_FACTS_NAME = "clone-facts.json"
FOLDER_PREFIX = "clean-clone-"
HELPER_NAME = "checkpoint"

# Exit codes the module names itself; the rest are the numbers the clone's own scripts return.
EXIT_PRE_ASSERTION = pc_exitcodes.PREFLIGHT_FAIL

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
_HTTPS_SOURCE = re.compile(r"https://[A-Za-z0-9][A-Za-z0-9.-]*(?::[0-9]{1,5})?/[A-Za-z0-9._~/-]+\Z")
_TERM_TEXT = re.compile(r"[A-Za-z0-9._+-]{1,64}\Z")
_LANG_TEXT = re.compile(r"[A-Za-z0-9._@-]{1,64}\Z")
_ID_TEXT = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\Z")
_CALL_LINE = re.compile(r"[^\s]+ CALL(?: |\Z)")
_STUB_DIGEST_LINE = re.compile(r"(?P<sha>[0-9a-f]{64}|UNCONFIRMED)  tests/harness/checkpoint_stub\.py\Z")
_PATHISH = re.compile(r"(?<![\w.-])/(?:Users|home|private|var|tmp|opt|Volumes|root|etc)(?:/[^\s'\"<>:,;)]*)?")

GIT_TIMEOUT_SECONDS = 600
LIST_TIMEOUT_SECONDS = 120
MAX_SMALL_FILE = 4096

# Run as a child of the clone, never imported by this process: the clone's own preflight under the scrubbed environment.
_PROBE = (
    "import argparse, os, sys\n"
    "sys.path.insert(0, os.path.join(sys.argv[1], 'tests', 'harness'))\n"
    "import pc_matrix\n"
    "env = dict(os.environ)\n"
    "stub = pc_matrix.check_stub(sys.argv[1], env)\n"
    "for line in stub.lines:\n"
    "    print(line)\n"
    "if stub.code != 0:\n"
    "    sys.exit(stub.code)\n"
    "result, home, config, code = pc_matrix._run_preflight(argparse.Namespace(claude=sys.argv[2]), env, sys.argv[1], sys.stdout)\n"
    "if code == 0:\n"
    "    print(result.line())\n"
    "sys.exit(code)\n"
)


class CloneFolderTaken(Exception):
    """The folder name is already there; nothing was created or reused."""


class Pre(NamedTuple):
    """The pre-assertion result: the exit code (0 or the first refusal), the counts and the clone's list ids."""

    code: int
    path_binaries: int
    helper_files: int
    entry_ids: Tuple[str, ...]


class Post(NamedTuple):
    """The post-assertion counts of a run."""

    run_roots: int
    stub_roots: int
    other_roots: int
    digests_checked: int
    digest_mismatches: int
    helper_calls: int
    helper_calls_stub: int
    helper_calls_other: int


class Scrubber(object):
    """Replaces every known path in child output with a fixed token, then any home-shaped or temp-shaped path."""

    def __init__(self, pairs: Sequence[Tuple[str, str]]) -> None:
        cleaned = {}
        for value, token in pairs:
            if isinstance(value, str) and len(value) > 1:
                cleaned[value] = token
                real = os.path.realpath(value)
                if len(real) > 1:
                    cleaned[real] = token
        self._pairs = sorted(cleaned.items(), key=lambda item: -len(item[0]))

    def __call__(self, text: str) -> str:
        for value, token in self._pairs:
            text = text.replace(value, token)
        return _PATHISH.sub("<path>", text)


def _say(stream: TextIO, text: str) -> None:
    stream.write(text + "\n")
    stream.flush()


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------------------------
# The folder, the environment and the clone
# ---------------------------------------------------------------------------------------------


def make_clone_folder(runs_root: str, clock: Callable[[], datetime.datetime]) -> str:
    """Create D under the runs root with a UTC-stamped name and its three siblings runs and home; return its realpath.

    Everything is created with pc_runroot.exclusive_dir, so a name that is taken raises CloneFolderTaken and nothing
    is reused. The clone itself creates the repo folder. D is never deleted.
    """
    now = clock()
    if now.tzinfo is not None:
        now = now.astimezone(datetime.timezone.utc)
    path = os.path.join(runs_root, FOLDER_PREFIX + now.strftime("%Y%m%dT%H%M%SZ"))
    try:
        pc_runroot.exclusive_dir(path, 0o700)
    except FileExistsError:
        raise CloneFolderTaken("the clone folder name is taken") from None
    for name in LAYOUT_NAMES[1:]:
        pc_runroot.exclusive_dir(os.path.join(path, name), 0o700)
    return os.path.realpath(path)


def _text_or(value: Optional[str], pattern: "re.Pattern[str]", default: str) -> str:
    return value if isinstance(value, str) and pattern.match(value) is not None else default


def build_child_env(
    folder: str,
    harness_home: str,
    claude_dir: str,
    caller_env: Mapping[str, str],
    real_home: bool = False,
) -> Dict[str, str]:
    """The child environment, built from an empty dict: exactly the names of ALLOWED_NAMES and nothing of the caller's.

    HOME is the throwaway folder D/home, or the caller's real home only with real_home. PATH is the fixed system
    folders plus the folder of the pinned build. PRECLEAR_HARNESS_HOME is the caller's harness home (so the owner's
    login folder and spend ledger are reused, D-13b). PRECLEAR_RUNS_ROOT is D/runs. TERM and LANG are copied from the
    caller when they are plain words, else fixed. Only the names are ever recorded.
    """
    if os.pathsep in claude_dir or os.pathsep in folder or os.pathsep in harness_home:
        raise ValueError("a folder name holds the path separator")
    home = os.path.join(folder, "home")
    if real_home:
        home = caller_env.get("HOME") or os.path.expanduser("~")
    parts = SYSTEM_PATH.split(os.pathsep)
    if claude_dir and claude_dir not in parts:
        parts.append(claude_dir)
    return {
        "HOME": home,
        "PATH": os.pathsep.join(parts),
        "PRECLEAR_HARNESS_HOME": harness_home,
        "PRECLEAR_RUNS_ROOT": os.path.join(folder, "runs"),
        "DISABLE_AUTOUPDATER": "1",
        "TERM": _text_or(caller_env.get("TERM"), _TERM_TEXT, DEFAULT_TERM),
        "LANG": _text_or(caller_env.get("LANG"), _LANG_TEXT, DEFAULT_LANG),
    }


def child_env_names(env: Mapping[str, str]) -> List[str]:
    """The names of a child environment, sorted; never a value."""
    return sorted(env)


def git_env(folder: str) -> Dict[str, str]:
    """The environment of every git call of the bootstrap: no system or global configuration, no prompt, throwaway home."""
    return {
        "HOME": os.path.join(folder, "home"),
        "PATH": SYSTEM_PATH,
        "LANG": DEFAULT_LANG,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }


def find_git(caller_env: Mapping[str, str]) -> Optional[str]:
    """The absolute path of git: the fixed system folders first, then the caller's own search path."""
    found = shutil.which("git", path=SYSTEM_PATH)
    if found is None and caller_env.get("PATH"):
        found = shutil.which("git", path=caller_env["PATH"])
    return os.path.abspath(found) if found else None


def _git(git: str, env: Mapping[str, str], args: Sequence[str], timeout: int = GIT_TIMEOUT_SECONDS) -> Tuple[int, str]:
    try:
        done = subprocess.run(
            [git] + list(args),
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return done.returncode, done.stdout.decode("utf-8", "replace")


def classify_source(text: Any) -> Optional[Tuple[str, str]]:
    """(kind, value) for an https address without credentials or an existing local folder, else None."""
    if not isinstance(text, str) or text == "" or "\x00" in text or "\n" in text:
        return None
    if text.startswith("https://"):
        return ("url", text) if _HTTPS_SOURCE.match(text) is not None else None
    if text.startswith("-"):
        return None
    if os.path.isdir(text):
        return ("local", os.path.realpath(text))
    return None


def default_source(root: str, git: str, env: Mapping[str, str]) -> Optional[str]:
    """The origin address of the main tree, read at run time (never printed or stored), or None."""
    code, text = _git(git, env, ["-C", root, "config", "--local", "--get", "remote.origin.url"], 60)
    value = text.strip()
    return value if code == 0 and value else None


def clone_repository(source: str, folder: str, git: str) -> Optional[str]:
    """Clone source into D/repo under the git hygiene variables; return the clone's head or None.

    The clone uses --no-hardlinks, runs git with shell=False and an absolute git path, and prints nothing from git.
    The bootstrap never commits, pushes or sets an identity.
    """
    env = git_env(folder)
    repo = os.path.join(folder, "repo")
    code, _text = _git(git, env, ["clone", "--quiet", "--no-hardlinks", "--", source, repo])
    if code != 0 or not os.path.isdir(repo):
        return None
    return head_of(repo, git, env)


_HEAD_TEXT = re.compile(r"[0-9a-f]{40}\Z")


def head_of(root: str, git: str, env: Mapping[str, str]) -> Optional[str]:
    code, text = _git(git, env, ["-C", root, "rev-parse", "HEAD"], 60)
    head = text.strip()
    return head if code == 0 and _HEAD_TEXT.match(head) is not None else None


# ---------------------------------------------------------------------------------------------
# Child processes (the clone's own scripts, scrubbed environment)
# ---------------------------------------------------------------------------------------------


def run_streaming(
    argv: Sequence[str], env: Mapping[str, str], cwd: str, out: TextIO, scrub: Callable[[str], str]
) -> int:
    """Run an argument list (never a shell) and print its output, scrubbed, line by line; return its exit status."""
    try:
        process = subprocess.Popen(
            list(argv),
            env=dict(env),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        )
    except OSError:
        _say(out, "ERROR: a child process could not be started")
        return pc_exitcodes.PREFLIGHT_FAIL
    assert process.stdout is not None
    with process.stdout:
        for raw in process.stdout:
            _say(out, scrub(raw.decode("utf-8", "replace").rstrip("\n")))
    return process.wait()



def capture_child(argv: Sequence[str], env: Mapping[str, str], cwd: str, timeout: int) -> Tuple[int, str]:
    try:
        done = subprocess.run(
            list(argv),
            env=dict(env),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return done.returncode, done.stdout.decode("utf-8", "replace")


def clone_script(folder: str, name: str) -> str:
    return os.path.join(folder, "repo", "tests", "harness", name)


def python_argv(python: str, script: str, *args: str) -> List[str]:
    return [python, "-E", "-s", "-B", script] + list(args)


def list_entries(folder: str, env: Mapping[str, str], python: str) -> Optional[Tuple[str, ...]]:
    """The ids of the clone's own `pc_matrix.py --list`, in order; None when the list cannot be read."""
    code, text = capture_child(
        python_argv(python, clone_script(folder, "pc_matrix.py"), "--list"),
        env,
        os.path.join(folder, "repo"),
        LIST_TIMEOUT_SECONDS,
    )
    if code != 0:
        return None
    lines = [line for line in text.splitlines() if line.strip()]
    ids = []
    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 2 or _ID_TEXT.match(fields[1]) is None:
            return None
        ids.append(fields[1])
    return tuple(ids)


# ---------------------------------------------------------------------------------------------
# Pre-assertions (D-11, first half)
# ---------------------------------------------------------------------------------------------


def count_runs_paths(repo: str, git: str, env: Mapping[str, str]) -> int:
    """A runs folder in the clone plus every tracked path under runs/; an unreadable index counts as one."""
    count = 1 if os.path.lexists(os.path.join(repo, "runs")) else 0
    code, text = _git(git, env, ["-C", repo, "ls-files"], 120)
    if code != 0:
        return count + 1
    for line in text.splitlines():
        if line == "runs" or line.startswith("runs/"):
            count += 1
    return count


def count_path_binaries(path_value: str) -> int:
    """Regular executable files named exactly checkpoint in the folders of a search path."""
    count = 0
    for folder in path_value.split(os.pathsep):
        if not folder:
            continue
        candidate = os.path.join(folder, HELPER_NAME)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            count += 1
    return count


def count_named(root: str, name: str = HELPER_NAME, skip: Sequence[str] = (".git",)) -> int:
    """Entries that are not folders and are named exactly name, anywhere below root (symlinks are not followed)."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(entry for entry in dirnames if entry not in skip)
        count += sum(1 for entry in filenames if entry == name)
        count += sum(1 for entry in dirnames if entry == name and os.path.islink(os.path.join(dirpath, entry)))
    return count


def count_config_keys(repo: str, git: str, env: Mapping[str, str], wanted: Callable[[str], bool]) -> int:
    """Keys of the clone's local configuration for which wanted(lower-case key) is true; unreadable counts as one."""
    code, text = _git(git, env, ["-C", repo, "config", "--local", "--list"], 60)
    if code != 0:
        return 1
    return sum(1 for line in text.splitlines() if wanted(line.split("=", 1)[0].strip().lower()))


def _identity_key(key: str) -> bool:
    return key.startswith("user.") or key == "preclear.pinnedidentity"


def _hook_key(key: str) -> bool:
    return key == "core.hookspath"


def pre_assertions(
    folder: str, env: Mapping[str, str], git: str, out: TextIO, python: Optional[str] = None
) -> Pre:
    """Print the before-run counts (every one must be 0) and return the first refusal code.

    Counted: a runs folder or tracked runs path in the clone; executable files named checkpoint in the folders of the
    scrubbed PATH and shutil.which finding one; files named checkpoint anywhere in the clone and under the throwaway
    home; identity keys and hook path keys in the clone's local configuration. Also required: the runs root is
    accepted for the child environment (12), and the clone's own list prints at least one data line (11).
    """
    python = python or sys.executable
    repo = os.path.join(folder, "repo")
    genv = git_env(folder)
    refusal = pc_exitcodes.OK
    path_value = env.get("PATH", "")
    counts = [
        ("runs folders or tracked runs paths in the clone", count_runs_paths(repo, git, genv)),
        ("checkpoint executables in the folders of the scrubbed PATH", count_path_binaries(path_value)),
        ("checkpoint found by a search of the scrubbed PATH", 1 if shutil.which(HELPER_NAME, path=path_value) else 0),
        ("files named checkpoint in the clone", count_named(repo)),
        ("files named checkpoint under the throwaway home", count_named(os.path.join(folder, "home"), skip=())),
        ("identity keys in the clone's local configuration", count_config_keys(repo, git, genv, _identity_key)),
        ("hook path keys in the clone's local configuration", count_config_keys(repo, git, genv, _hook_key)),
    ]
    path_binaries = counts[1][1]
    helper_files = counts[3][1]
    for label, value in counts:
        _say(out, "pre: %s: %d" % (label, value))
        if value != 0 and refusal == pc_exitcodes.OK:
            refusal = EXIT_PRE_ASSERTION
    try:
        pc_spike.runs_root(env, home_dir=env.get("HOME") or None, repo_root=repo)
        accepted = 1
    except pc_spike.HomeRefused:
        accepted = 0
    _say(out, "pre: runs root usable under the child environment: %s" % ("yes" if accepted else "no"))
    if not accepted and refusal == pc_exitcodes.OK:
        refusal = pc_exitcodes.PREFLIGHT_BLOCKED
    ids = list_entries(folder, env, python)
    _say(out, "pre: entries in the clone's list: %d" % (len(ids) if ids else 0))
    if not ids:
        if refusal == pc_exitcodes.OK:
            refusal = EXIT_PRE_ASSERTION
        ids = ()
    return Pre(refusal, path_binaries, helper_files, tuple(ids))


# ---------------------------------------------------------------------------------------------
# Post-assertions (D-11, second half) and the clone-facts file
# ---------------------------------------------------------------------------------------------


def _small_text(path: str) -> Optional[str]:
    """The text of a small regular file read without following a final symlink, else None."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return None
        with open(path, "rb") as handle:
            data = handle.read(MAX_SMALL_FILE + 1)
    except OSError:
        return None
    if len(data) > MAX_SMALL_FILE:
        return None
    return data.decode("utf-8", "replace").strip()


def _count_calls(path: str) -> int:
    """CALL lines of a wrapper log; an absent or empty log counts 0 and is never an error."""
    try:
        if not stat.S_ISREG(os.lstat(path).st_mode):
            return 0
        count = 0
        with open(path, "rb") as handle:
            for raw in handle:
                if _CALL_LINE.match(raw.decode("utf-8", "replace")) is not None:
                    count += 1
        return count
    except OSError:
        return 0


def _file_sha(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def post_assertions(
    folder: str, evidence_folder: Optional[str], out: TextIO, interpreter: Optional[str] = None
) -> Post:
    """Print the after-run counts and return them.

    Over every run root under D/runs that holds a wrapper folder: the wrapper's stub file must name the clone's
    checkpoint_stub.py (resolved) and its py file the interpreter; CALL lines of its log count as calls to the stub
    when both hold and as calls to something else when not. Each filed folder's digests.txt stub digest must equal the
    digest of the clone's stub. Nothing is opened for writing.
    """
    stub = os.path.realpath(clone_script(folder, "checkpoint_stub.py"))
    interpreter_real = os.path.realpath(interpreter or sys.executable)
    runs = os.path.join(folder, "runs")
    roots = stub_roots = other_roots = calls_stub = calls_other = 0
    try:
        names = sorted(os.listdir(runs))
    except OSError:
        names = []
    for name in names:
        wrapper = os.path.join(runs, name, "wrapper")
        if os.path.islink(os.path.join(runs, name)) or not os.path.isdir(wrapper) or os.path.islink(wrapper):
            continue
        roots += 1
        named_stub = _small_text(os.path.join(wrapper, "stub"))
        named_py = _small_text(os.path.join(wrapper, "py"))
        delegates = (
            named_stub is not None
            and named_stub != ""
            and os.path.realpath(named_stub) == stub
            and named_py is not None
            and named_py != ""
            and os.path.realpath(named_py) == interpreter_real
        )
        calls = _count_calls(os.path.join(wrapper, "calls.log"))
        if delegates:
            stub_roots += 1
            calls_stub += calls
        else:
            other_roots += 1
            calls_other += calls
    checked = mismatches = 0
    if evidence_folder is not None and os.path.isfile(stub):
        wanted = _file_sha(stub)
        for name in sorted(os.listdir(evidence_folder)):
            text = _small_text(os.path.join(evidence_folder, name, "digests.txt")) if not os.path.islink(
                os.path.join(evidence_folder, name)
            ) else None
            if text is None:
                continue
            for line in text.splitlines():
                parsed = _STUB_DIGEST_LINE.match(line)
                if parsed is not None:
                    checked += 1
                    if parsed.group("sha") != wanted:
                        mismatches += 1
    result = Post(roots, stub_roots, other_roots, checked, mismatches, calls_stub + calls_other, calls_stub, calls_other)
    _say(out, "post: run roots with a wrapper folder: %d" % result.run_roots)
    _say(out, "post: run roots whose wrapper names the clone stub and the interpreter: %d" % result.stub_roots)
    _say(out, "post: run roots whose wrapper names anything else: %d" % result.other_roots)
    _say(out, "post: stub digest lines checked: %d" % result.digests_checked)
    _say(out, "post: stub digest lines that differ from the clone stub: %d" % result.digest_mismatches)
    _say(out, "post: helper calls: %d" % result.helper_calls)
    _say(out, "post: helper calls to the clone stub: %d" % result.helper_calls_stub)
    _say(out, "post: helper calls to anything else: %d" % result.helper_calls_other)
    return result


def post_refused(post: Post) -> bool:
    """True when a call reached anything but the clone's stub, or the structure or a digest says it could have."""
    return post.helper_calls_other > 0 or post.other_roots > 0 or post.digest_mismatches > 0


def write_clone_facts(
    folder: str,
    env_names: Sequence[str],
    pre: Pre,
    post: Post,
    clone_head: str,
    source_kind: str,
    home_kind: str,
) -> Optional[str]:
    """Write D/clone-facts.json exclusively in the schema of pc_baseline.read_clone_facts; return its path, else None."""
    facts = {
        "env_names": list(env_names),
        "path_checkpoint_binaries": pre.path_binaries,
        "helper_files_in_clone": pre.helper_files,
        "helper_calls": post.helper_calls,
        "helper_calls_stub": post.helper_calls_stub,
        "helper_calls_other": post.helper_calls_other,
        "clone_head": clone_head,
        "source_kind": source_kind,
        "home_kind": home_kind,
    }
    path = os.path.join(folder, CLONE_FACTS_NAME)
    data = (json.dumps(facts, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        pc_runroot.write_exclusive(path, data, 0o600)
    except OSError:
        return None
    return path if pc_baseline.read_clone_facts(path) is not None else None


# ---------------------------------------------------------------------------------------------
# The matrix step, the copy-back and the listing
# ---------------------------------------------------------------------------------------------

# A matrix exit that still reaches the post-assertions, finalize and the copy-back when something was filed.
FILING_CODES = (0, 10, 11, 18, 19)


def outcome_folders(evidence_folder: Optional[str]) -> int:
    """Folders directly inside a dated folder (row folders, STOPPED and SKIPPED labels); symlinks are not counted."""
    if evidence_folder is None:
        return 0
    count = 0
    for name in os.listdir(evidence_folder):
        path = os.path.join(evidence_folder, name)
        if os.path.isdir(path) and not os.path.islink(path):
            count += 1
    return count


def new_dated_folders(evidence: str, before: Sequence[str]) -> List[str]:
    """Names of the rerun- folders that appeared in the evidence folder since the names in before were listed."""
    found = []
    for name in sorted(set(os.listdir(evidence)) - set(before)):
        path = os.path.join(evidence, name)
        if name.startswith(pc_baseline.DATED_PREFIX) and os.path.isdir(path) and not os.path.islink(path):
            found.append(name)
    return found


def reaches_filing(matrix_code: int, outcomes: int) -> bool:
    """True when the matrix's exit code and the folders it filed mean the finished rows are finalized and copied back."""
    return matrix_code in FILING_CODES and outcomes >= 1


def copy_back(
    clone_folder: str, main_root: str, harness_home: str, out: TextIO
) -> int:
    """Promote the finalized clone folder into the main tree's tests/evidence under the same name.

    The leak gate runs again with the main tree's deny entries (a clone has no local deny file). An existing
    destination is refused with 17 and nothing is overwritten.
    """
    destination = os.path.join(main_root, "tests", "evidence", os.path.basename(clone_folder))
    try:
        deny = pc_sanitize.Sanitizer.from_machine(main_root).deny_entries()
    except pc_sanitize.SanitizerError:
        _say(out, "SCANNER_ERROR: the sanitizer could not be built; nothing was copied back")
        return pc_exitcodes.SCANNER_ERROR
    config = os.path.join(harness_home, pc_spike.CONFIG_DIR_NAME)
    result = pc_promote.promote(clone_folder, destination, main_root, config_dir=config, deny_entries=deny)
    _say(out, "copy-back: %s" % result.message)
    for line in str(result.report_text).splitlines():
        if line.strip():
            _say(out, line)
    return int(result.code)


def _has_outcome(name: str, identifier: str) -> bool:
    return re.match(r"(?:(?:STOPPED|SKIPPED)-)?" + re.escape(identifier) + r"(?:-attempt-[1-9])?\Z", name) is not None


def count_listing(copied: str, entry_ids: Sequence[str]) -> Tuple[int, int, int]:
    """(entries, ids with an outcome folder, Not run: lines of the README) for the copied folder."""
    try:
        names = [name for name in os.listdir(copied) if os.path.isdir(os.path.join(copied, name))]
    except OSError:
        names = []
    folders = sum(1 for identifier in entry_ids if any(_has_outcome(name, identifier) for name in names))
    text = _read_large(os.path.join(copied, "README.md"))
    not_run = sum(1 for line in text.splitlines() if line.startswith("Not run: ")) if text else 0
    return len(entry_ids), folders, not_run


def _read_large(path: str) -> str:

    try:
        with open(path, "rb") as handle:
            return handle.read(4 * 1024 * 1024).decode("utf-8", "replace")
    except OSError:
        return ""


def final_listing(copied: str, entry_ids: Sequence[str], out: TextIO) -> int:
    """Print `entries: N, folders: N`, or the partial form with the not-run count; 11 when the counts do not add up."""
    entries, folders, not_run = count_listing(copied, entry_ids)
    if not_run == 0 and folders == entries:
        _say(out, "entries: %d, folders: %d" % (entries, folders))
        return pc_exitcodes.OK
    _say(out, "entries: %d, folders: %d, not run: %d" % (entries, folders, not_run))
    return pc_exitcodes.OK if folders + not_run == entries else EXIT_PRE_ASSERTION


# ---------------------------------------------------------------------------------------------
# The steps and main
# ---------------------------------------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    def __init__(self, out: TextIO, err: TextIO) -> None:
        super().__init__(prog=PROG, add_help=True, allow_abbrev=False)
        self._out = out
        self._err = err

    def error(self, message: str) -> Any:  # type: ignore[override]
        _say(self._err, USAGE_LINE)
        _say(self._err, "%s: error: %s" % (PROG, MESSAGE_USAGE))
        raise SystemExit(pc_exitcodes.USAGE)

    def print_help(self, file: Optional[TextIO] = None) -> None:
        _say(self._out, USAGE_LINE)

    def print_usage(self, file: Optional[TextIO] = None) -> None:
        _say(self._err, USAGE_LINE)


def build_parser(out: TextIO, err: TextIO) -> argparse.ArgumentParser:
    parser = _Parser(out, err)
    parser.add_argument("--claude", default=None)
    parser.add_argument("--budget", default=None)
    parser.add_argument("--source", default=None)
    parser.add_argument("--preflight-only", action="store_true", dest="preflight_only")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--real-home", action="store_true", dest="real_home")
    return parser


def _usage(err: TextIO, message: str = MESSAGE_USAGE) -> int:
    _say(err, USAGE_LINE)
    _say(err, "%s: error: %s" % (PROG, message))
    return pc_exitcodes.USAGE


def run_free_steps(
    folder: str,
    env: Mapping[str, str],
    python: str,
    claude: str,
    budget: str,
    selftest: bool,
    out: TextIO,
    scrub: Callable[[str], str],
) -> int:
    """The free steps in the clone: the optional self-test, the dry run of the whole matrix, then the probe.

    The first step whose code is not 0 stops the run, except a 10 from the dry run (a row that a precondition skips
    here, which the matrix files as skipped). Nothing starts a model. Returns 0 or the stopping code.
    """
    repo = os.path.join(folder, "repo")
    if selftest:
        _say(out, "step: the clone's own self-test")
        code = run_streaming([clone_script(folder, "selftest")], env, repo, out, scrub)
        if code != pc_exitcodes.OK:
            return code
    _say(out, "step: dry run of the whole matrix with the same budget")
    code = run_streaming(
        python_argv(python, clone_script(folder, "pc_matrix.py"), "--dry-run", "--all", "--claude", claude, "--budget", budget),
        env,
        repo,
        out,
        scrub,
    )
    if code not in (pc_exitcodes.OK, pc_exitcodes.PREFLIGHT_SKIP):
        return code
    return run_probe(folder, env, python, claude, out, scrub)


def run_probe(
    folder: str, env: Mapping[str, str], python: str, claude: str, out: TextIO, scrub: Callable[[str], str]
) -> int:
    """The stub check and the strict preflight, run by the clone's own driver under the scrubbed environment."""
    _say(out, "step: stub check and strict preflight (no row, no model)")
    repo = os.path.join(folder, "repo")
    return run_streaming([python, "-E", "-s", "-B", "-c", _PROBE, repo, claude], env, repo, out, scrub)


def run_matrix(
    folder: str,
    env: Mapping[str, str],
    python: str,
    claude: str,
    budget: str,
    out: TextIO,
    scrub: Callable[[str], str],
) -> int:
    """The clone's own `pc_matrix.py --all` as a child under the scrubbed environment, its exit code passed through."""
    _say(out, "step: the matrix, from the clone")
    repo = os.path.join(folder, "repo")
    return run_streaming(
        python_argv(python, clone_script(folder, "pc_matrix.py"), "--all", "--claude", claude, "--budget", budget),
        env,
        repo,
        out,
        scrub,
    )


def main(
    argv: Optional[Sequence[str]] = None,
    env: Optional[Mapping[str, str]] = None,
    repo_root: Optional[str] = None,
    clock: Optional[Callable[[], datetime.datetime]] = None,
    out: Optional[TextIO] = None,
    err: Optional[TextIO] = None,
    python: Optional[str] = None,
) -> int:
    """Run the bootstrap and return the exit code; this function never calls sys.exit."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = build_parser(out, err)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
    caller: Mapping[str, str] = dict(os.environ) if env is None else env
    main_root = os.path.realpath(repo_root if repo_root else _REPO_ROOT)
    now_of = clock or _utc_now
    python = python or sys.executable

    claude = args.claude
    if not isinstance(claude, str) or not os.path.isabs(claude) or not os.path.isfile(claude) or not os.access(claude, os.X_OK):
        return _usage(err, MESSAGE_CLAUDE)
    if os.pathsep in claude or "\x00" in claude:
        return _usage(err, MESSAGE_CLAUDE)
    if args.preflight_only:
        if args.budget is not None or args.selftest:
            return _usage(err)
    elif args.budget is None or args.budget == "":
        return _usage(err)
    git = find_git(caller)
    if git is None:
        return _usage(err, "git was not found")
    source_text = args.source
    if source_text is None:
        source_text = default_source(main_root, git, _bare_git_env())
        if source_text is None:
            return _usage(err, MESSAGE_NO_SOURCE)
    classified = classify_source(source_text)
    if classified is None:
        return _usage(err, MESSAGE_SOURCE if args.source is not None else MESSAGE_NO_SOURCE)
    source_kind, source_value = classified

    home_dir = caller.get("HOME") or None
    try:
        harness_home = pc_spike.harness_home(caller, home_dir, main_root)
    except pc_spike.HomeRefused:
        _say(err, MESSAGE_HARNESS_HOME)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    try:
        runs_parent = pc_spike.runs_root(caller, home_dir=home_dir, repo_root=main_root)
    except pc_spike.HomeRefused:
        _say(err, MESSAGE_RUNS_ROOT)
        return pc_exitcodes.PREFLIGHT_BLOCKED
    try:
        pc_spike.ensure_runs_root(runs_parent)
        folder = make_clone_folder(runs_parent, now_of)
    except CloneFolderTaken:
        _say(err, MESSAGE_FOLDER_TAKEN)
        return pc_exitcodes.RUNROOT_COLLISION
    except (OSError, pc_spike.SpikeError):
        _say(err, MESSAGE_RUNS_ROOT)
        return pc_exitcodes.PREFLIGHT_BLOCKED

    claude_dir = os.path.dirname(claude)
    try:
        child = build_child_env(folder, harness_home, claude_dir, caller, args.real_home)
    except ValueError:
        return _usage(err, MESSAGE_CLAUDE)
    names = child_env_names(child)
    real_home_path = child["HOME"] if args.real_home else ""
    scrub = Scrubber(
        [
            (folder, "<clone-folder>"),
            (runs_parent, "<runs-root>"),
            (harness_home, "<harness-home>"),
            (claude, "<claude>"),
            (claude_dir, "<claude-folder>"),
            (real_home_path, "<home>"),
            (home_dir or "", "<home>"),
            (main_root, "<main-tree>"),
            (source_value, "<source>"),
        ]
    )

    _say(out, "clean-clone bootstrap")
    _say(out, "clone folder name: %s" % os.path.basename(folder))
    _say(out, "folders existing under that name before: 0")
    _say(out, "child environment names: %s" % ", ".join(names))
    _say(out, "source kind: %s" % source_kind)
    home_kind = "real" if args.real_home else "throwaway"
    _say(out, "home kind: %s" % home_kind)
    if args.real_home:
        _say(out, MESSAGE_REAL_HOME)

    genv = git_env(folder)
    clone_head = clone_repository(source_value, folder, git)
    if clone_head is None:
        _say(err, MESSAGE_CLONE)
        return pc_exitcodes.PREFLIGHT_FAIL
    main_head = head_of(main_root, git, genv)
    _say(out, "clone head: %s" % clone_head)
    _say(out, "main tree head: %s" % (main_head if main_head else "unavailable"))
    _say(out, "heads equal: %s" % ("yes" if main_head == clone_head else "no"))

    pre = pre_assertions(folder, child, git, out, python)
    if pre.code != pc_exitcodes.OK:
        _say(out, "stopped before any step that starts a model")
        return pre.code

    if args.preflight_only:
        _say(out, "preflight-only: no row and no model is started")
        return run_probe(folder, child, python, claude, out, scrub)

    code = run_free_steps(folder, child, python, claude, args.budget, args.selftest, out, scrub)
    if code != pc_exitcodes.OK:
        return code

    repo = os.path.join(folder, "repo")
    evidence = os.path.join(repo, "tests", "evidence")
    try:
        before = os.listdir(evidence)
    except OSError:
        before = []
    matrix_code = run_matrix(folder, child, python, claude, args.budget, out, scrub)
    try:
        fresh = new_dated_folders(evidence, before)
    except OSError:
        fresh = []
    if len(fresh) > 1:
        _say(out, "ERROR: more than one new dated folder appeared in the clone")
        return pc_exitcodes.PREFLIGHT_FAIL
    dated = os.path.join(evidence, fresh[0]) if fresh else None
    outcomes = outcome_folders(dated)
    _say(out, "matrix exit code: %d" % matrix_code)
    _say(out, "outcome folders filed in the clone: %d" % outcomes)
    if matrix_code not in FILING_CODES and outcomes >= 1:
        _say(out, MESSAGE_KEPT)
        return matrix_code
    if not reaches_filing(matrix_code, outcomes) or dated is None:
        _say(out, MESSAGE_NOTHING_FILED)
        return matrix_code if matrix_code != pc_exitcodes.OK else pc_exitcodes.PREFLIGHT_FAIL

    post = post_assertions(folder, dated, out, python)
    facts = write_clone_facts(folder, names, pre, post, clone_head, source_kind, home_kind)
    if facts is None:
        _say(err, MESSAGE_FACTS)
        return pc_exitcodes.PREFLIGHT_FAIL
    _say(out, "step: finalize in the clone")
    code = run_streaming(
        python_argv(
            python,
            clone_script(folder, "pc_baseline.py"),
            "finalize",
            "--folder",
            os.path.join("tests", "evidence", os.path.basename(dated)),
            "--clone-facts",
            facts,
        ),
        child,
        repo,
        out,
        scrub,
    )
    if code != pc_exitcodes.OK:
        return code
    _say(out, "step: copy-back through the leak gate")
    code = copy_back(dated, main_root, harness_home, out)
    if code != pc_exitcodes.OK:
        return code
    copied = os.path.join(main_root, "tests", "evidence", os.path.basename(dated))
    listing = final_listing(copied, pre.entry_ids, out)
    if post_refused(post):
        _say(out, "a helper call or a wrapper named something other than the clone stub: exit 11 after the copy-back")
        return EXIT_PRE_ASSERTION
    if listing != pc_exitcodes.OK:
        return listing
    return matrix_code


def _bare_git_env() -> Dict[str, str]:
    """Environment for reading the main tree's own local configuration: hygiene variables and a fixed search path."""
    return {
        "PATH": SYSTEM_PATH,
        "HOME": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }


if __name__ == "__main__":
    sys.exit(main())
