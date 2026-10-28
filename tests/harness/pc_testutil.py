"""Test support for the harness suite: fake and tripwire claude, shared-directory layout,
minimal environments and git environment hygiene.

Nothing here ever runs a real claude. The only claude a test executes is a small /bin/sh
script written into a temporary directory by this module. A fake claude answers the two
zero-token commands the preflight uses (--version and auth status --json); any other
argument vector is a violation that is appended to tripwire.log beside the script and ends
with exit status 97. A tripwire claude treats every argument vector as a violation.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

# A value planted beside loggedIn in the fake auth output. Tests assert it never reaches any
# message, line or return value (D-03). It is deliberately not shaped like an email address.
IDENTITY_SENTINEL = "planted-identity-sentinel-7f3a91"

TRIPWIRE_EXIT = 97
TRIPWIRE_LOG = "tripwire.log"
ENV_LOG = "env.log"

SYSTEM_DIRS = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")

_SCRIPT_HEAD = """#!/bin/sh
# Test double for claude. Never talks to a model.
here=$(cd "$(dirname "$0")" && pwd)
"""

_FAKE_BODY = """case "$*" in
  "--version")
    __VERSION_LINE__
    exit 0
    ;;
  "auth status --json")
    printf '%s|%s|%s\\n' "${CLAUDE_CONFIG_DIR-unset}" "${ANTHROPIC_API_KEY-unset}" "${CLAUDE_CODE_OAUTH_TOKEN-unset}" >> "$here/__ENV_LOG__"
    printf '%s\\n' __AUTH_OUTPUT__
    exit __AUTH_EXIT__
    ;;
esac
printf '%s\\n' "$*" >> "$here/__TRIPWIRE_LOG__"
exit __TRIPWIRE_EXIT__
"""

_TRIPWIRE_BODY = """printf '%s\\n' "$*" >> "$here/__TRIPWIRE_LOG__"
exit __TRIPWIRE_EXIT__
"""


def _write_executable(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_fake_claude(
    directory: str,
    version_banner: str,
    logged_in: bool,
    auth_raw: Optional[str] = None,
) -> str:
    """Write a fake claude into directory and return its path.

    --version prints version_banner (a trailing newline is added when it is not empty).
    auth status --json prints a JSON object whose loggedIn matches logged_in and which also
    carries a planted identity field; the exit status is 0 when logged in and 1 otherwise.
    auth_raw replaces that output verbatim (for the unparseable-output case).
    Any other argument vector goes to tripwire.log and exits 97.
    """
    if auth_raw is None:
        auth_raw = '{"loggedIn": %s, "account": "%s"}' % (
            "true" if logged_in else "false",
            IDENTITY_SENTINEL,
        )
    if version_banner:
        version_line = "printf '%s\\n' " + shlex.quote(version_banner)
    else:
        version_line = ":"
    body = (
        _FAKE_BODY.replace("__VERSION_LINE__", version_line)
        .replace("__AUTH_OUTPUT__", shlex.quote(auth_raw))
        .replace("__AUTH_EXIT__", "0" if logged_in else "1")
        .replace("__ENV_LOG__", ENV_LOG)
        .replace("__TRIPWIRE_LOG__", TRIPWIRE_LOG)
        .replace("__TRIPWIRE_EXIT__", str(TRIPWIRE_EXIT))
    )
    path = os.path.join(directory, "claude")
    _write_executable(path, _SCRIPT_HEAD + body)
    return path


def make_tripwire(directory: str) -> str:
    """Write a claude whose every argument vector is a violation and return its path."""
    body = _TRIPWIRE_BODY.replace("__TRIPWIRE_LOG__", TRIPWIRE_LOG).replace(
        "__TRIPWIRE_EXIT__", str(TRIPWIRE_EXIT)
    )
    path = os.path.join(directory, "claude")
    _write_executable(path, _SCRIPT_HEAD + body)
    return path


def read_tripwire(directory: str) -> List[str]:
    """Return the logged violation lines (empty list when nothing fired)."""
    path = os.path.join(directory, TRIPWIRE_LOG)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def read_env_log(directory: str) -> List[str]:
    """Return the lines the fake claude logged for auth status calls."""
    path = os.path.join(directory, ENV_LOG)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def make_shared_dir(directory: str, python3_path: str, git_path: str) -> str:
    """Build the layout a stranger may have: claude, python3 and git in one folder.

    python3 and git are linked by absolute path next to a tripwire claude. Removing that
    folder from PATH must not cost the suite its interpreter or git.
    """
    os.makedirs(directory, exist_ok=True)
    os.symlink(os.path.abspath(python3_path), os.path.join(directory, "python3"))
    os.symlink(os.path.abspath(git_path), os.path.join(directory, "git"))
    make_tripwire(directory)
    return directory


def minimal_env(path_dirs: Iterable[str]) -> Dict[str, str]:
    """Return an environment holding only PATH, HOME and LANG.

    PATH is the given directories followed by the system directories. HOME points at a
    fresh temporary directory so a test never reads the caller's real home.
    """
    home = tempfile.mkdtemp(prefix="pc-home-")
    return {
        "PATH": os.pathsep.join(list(path_dirs) + list(SYSTEM_DIRS)),
        "HOME": home,
        "LANG": "en_US.UTF-8",
    }


def git_env(base: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of base with git environment hygiene and a placeholder identity.

    The machine's global git configuration must not influence any result, and the identity
    uses a reserved example domain so nothing personal is ever committed by a test.
    """
    env = dict(base)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    env["GIT_AUTHOR_NAME"] = "Harness Test"
    env["GIT_AUTHOR_EMAIL"] = "harness-test@example.com"
    env["GIT_COMMITTER_NAME"] = "Harness Test"
    env["GIT_COMMITTER_EMAIL"] = "harness-test@example.com"
    return env


# ---------------------------------------------------------------------------------------------
# The scripted multi-stage claude and the row rig (plan 03-02)
# ---------------------------------------------------------------------------------------------
#
# make_scripted_claude writes a python script named claude plus a fake.json beside it. It answers
# --version and auth status --json like the fake above, and for any stage call it appends one record
# to calls.log, takes the next stage from a counter file and plays that stage's ops in order.
#
# Config keys (fake.json): banner, version, logged_in, outside_dir, stages.
# A stage is a mapping: ops (list), result (mapping), init (mapping of init overrides), no_result
# (true: print no result event), exit (process exit status), stderr (text).
# Stage ops (each a mapping with an "op" key):
#   hook   payloads: feed each payload to the InstructionsLoaded command found in the --settings file
#   init   override: emit the system init event (implicit before the first stream op)
#   text   text: an assistant text message
#   tool   name, input, run ("wrapper" really runs the wrapper), args, denied, reject, content
#   write  path, text: really write a file
#   git    args: run git in the cwd with a hygiene environment
#   sleep  seconds
#   raw    line: print one line verbatim
# Result keys: subtype, is_error, terminal_reason, text, total_cost_usd, delta (adds
# model_usage_since_last_result), usage, num_turns, session_id, omit (list of keys to drop).
# Tokens replaced inside strings: $PROJECT and $CWD (the working folder), $RUN, $AUTOMEM,
# $OUTSIDE, $CONFIG, $WRAPPER, $SID. An init override value of "$DELETE" removes that key.

_SCRIPTED_CLAUDE = r'''#!__PYTHON__
import json, os, shlex, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
with open(os.path.join(here, "fake.json")) as handle:
    cfg = json.load(handle)
if args == ["--version"]:
    print(cfg.get("banner", "2.1.310 (Claude Code)"))
    sys.exit(0)
if args == ["auth", "status", "--json"]:
    logged = cfg.get("logged_in", True)
    print(json.dumps({"loggedIn": logged, "account": "__IDENTITY__"}))
    sys.exit(0 if logged else 1)

prompt = sys.stdin.read()
counter = os.path.join(here, "counter.txt")
index = 0
if os.path.exists(counter):
    with open(counter) as handle:
        index = int(handle.read() or "0")
with open(counter, "w") as handle:
    handle.write(str(index + 1))
keep = ("CLAUDE_CONFIG_DIR", "CKPT_HOME", "DISABLE_AUTOUPDATER")
record = {"args": args, "prompt": prompt, "cwd": os.getcwd(), "index": index,
          "env": dict((k, os.environ[k]) for k in os.environ if k in keep), "names": sorted(os.environ)}
with open(os.path.join(here, "calls.log"), "a") as handle:
    handle.write(json.dumps(record) + "\n")
stages = cfg.get("stages", [])
if index >= len(stages):
    with open(os.path.join(here, "tripwire.log"), "a") as handle:
        handle.write("unscripted stage call %d\n" % index)
    sys.exit(97)
stage = stages[index]

settings = {}
if "--settings" in args:
    with open(args[args.index("--settings") + 1]) as handle:
        settings = json.load(handle)
sid = args[args.index("--resume") + 1] if "--resume" in args else args[args.index("--session-id") + 1]
model = args[args.index("--model") + 1] if "--model" in args else "unknown-model"
cwd = os.getcwd()
subs = {"$PROJECT": cwd, "$CWD": cwd, "$RUN": os.path.dirname(cwd),
        "$AUTOMEM": settings.get("autoMemoryDirectory", ""), "$OUTSIDE": cfg.get("outside_dir", ""),
        "$CONFIG": os.environ.get("CLAUDE_CONFIG_DIR", ""),
        "$WRAPPER": os.path.join(os.path.dirname(cwd), "wrapper", "checkpoint"), "$SID": sid}


def subst(value):
    if isinstance(value, str):
        for key in subs:
            value = value.replace(key, subs[key])
        return value
    if isinstance(value, list):
        return [subst(item) for item in value]
    if isinstance(value, dict):
        return dict((key, subst(item)) for key, item in value.items())
    return value


def emit(event):
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


state = {"started": False, "tools": 0, "denials": []}


def init_event(override):
    event = {"type": "system", "subtype": "init", "session_id": sid, "claude_code_version": cfg.get("version", "2.1.310"),
             "cwd": cwd, "tools": ["Bash", "Read", "Write", "Edit"], "mcp_servers": [], "model": model,
             "permissionMode": "default", "slash_commands": ["preclear", "compact"],
             "skills": ["preclear", "update-config"],
             "plugins": [{"name": name, "path": "builtin", "source": name + "@builtin"}
                         for name in ("cc-plugin-agents-md", "cc-plugin-telemetry", "cc-plugin-plugin-authoring")],
             "agents": ["general-purpose"], "apiKeySource": "none",
             "memory_paths": {"auto": settings.get("autoMemoryDirectory", "").rstrip("/") + "/"}}
    for key, value in subst(override).items():
        if value == "$DELETE":
            event.pop(key, None)
        else:
            event[key] = value
    return event


def ensure_init():
    if not state["started"]:
        emit(init_event(stage.get("init", {})))
        state["started"] = True


def do_hook(op):
    hooks = settings.get("hooks", {}).get("InstructionsLoaded")
    if not hooks:
        return
    command = hooks[0]["hooks"][0]["command"]
    for payload in op.get("payloads", []):
        text = json.dumps(subst(payload))
        subprocess.run(shlex.split(command), input=text.encode("utf-8"))


def do_tool(op):
    ensure_init()
    state["tools"] += 1
    tool_id = "toolu_%04d" % state["tools"]
    name = op.get("name", "Bash")
    tool_input = subst(op.get("input", {}))
    emit({"type": "assistant", "session_id": sid,
          "message": {"role": "assistant", "content": [{"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]}})
    denied = bool(op.get("denied"))
    content = subst(op.get("content", "ok"))
    if op.get("run") == "wrapper" and not denied:
        env = dict(os.environ)
        env["CLAUDE_CODE_SESSION_ID"] = sid
        done = subprocess.run([subs["$WRAPPER"]] + subst(op.get("args", [])), env=env, cwd=cwd,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        content = done.stdout.decode("utf-8", "replace")
    rejected = denied or bool(op.get("reject"))
    if denied:
        state["denials"].append({"tool_name": name, "tool_use_id": tool_id, "tool_input": tool_input})
        emit({"type": "system", "subtype": "permission_denied", "tool_name": name, "tool_use_id": tool_id,
              "message": "This command requires approval", "session_id": sid})
    emit({"type": "user", "session_id": sid, "tool_result_meta": "reject" if rejected else "accept",
          "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_id,
                                                    "content": content, "is_error": rejected}]}})


def do_write(op):
    path = subst(op["path"])
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w") as handle:
        handle.write(subst(op.get("text", "")))


def do_git(op):
    env = {"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
           "GIT_AUTHOR_NAME": "Scripted", "GIT_AUTHOR_EMAIL": "scripted@example.com",
           "GIT_COMMITTER_NAME": "Scripted", "GIT_COMMITTER_EMAIL": "scripted@example.com"}
    subprocess.run(["git", "-C", cwd] + subst(op.get("args", [])), env=env, stdin=subprocess.DEVNULL,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


for op in stage.get("ops", []):
    kind = op.get("op")
    if kind == "hook":
        do_hook(op)
    elif kind == "init":
        emit(init_event(dict(stage.get("init", {}), **op.get("override", {}))))
        state["started"] = True
    elif kind == "text":
        ensure_init()
        emit({"type": "assistant", "session_id": sid,
              "message": {"role": "assistant", "content": [{"type": "text", "text": subst(op.get("text", ""))}]}})
    elif kind == "tool":
        do_tool(op)
    elif kind == "write":
        do_write(op)
    elif kind == "git":
        do_git(op)
    elif kind == "sleep":
        time.sleep(float(op.get("seconds", 0)))
    elif kind == "raw":
        sys.stdout.write(op.get("line", "") + "\n")
        sys.stdout.flush()

ensure_init()
if stage.get("stderr"):
    sys.stderr.write(stage["stderr"])
    sys.stderr.flush()
if not stage.get("no_result"):
    res = stage.get("result", {})
    usage = res.get("usage", {"input_tokens": 10, "cache_creation_input_tokens": 20,
                              "cache_read_input_tokens": 30, "output_tokens": 5})
    event = {"type": "result", "subtype": res.get("subtype", "success"), "is_error": res.get("is_error", False),
             "num_turns": res.get("num_turns", 1), "result": subst(res.get("text", "done")),
             "session_id": res.get("session_id", sid), "total_cost_usd": res.get("total_cost_usd", 0.01),
             "usage": usage, "permission_denials": state["denials"],
             "terminal_reason": res.get("terminal_reason", "completed")}
    if "delta" in res:
        event["model_usage_since_last_result"] = {model: {"costUSD": res["delta"], "inputTokens": 1, "outputTokens": 1}}
    for key in res.get("omit", []):
        event.pop(key, None)
    emit(event)
sys.exit(stage.get("exit", 0))
'''


def make_scripted_claude(directory: str, config: Optional[dict] = None) -> str:
    """Write the scripted claude and its fake.json into directory and return the script path."""
    path = os.path.join(directory, "claude")
    script = _SCRIPTED_CLAUDE.replace("__PYTHON__", os.path.realpath(sys.executable)).replace(
        "__IDENTITY__", IDENTITY_SENTINEL
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(script)
    os.chmod(path, 0o755)
    write_scripted_config(directory, config)
    return path


def write_scripted_config(directory: str, config: Optional[dict]) -> None:
    """(Re)write fake.json beside the scripted claude; the call counter file is left alone."""
    settled = {"banner": "2.1.310 (Claude Code)", "version": "2.1.310", "logged_in": True, "stages": []}
    settled.update(config or {})
    with open(os.path.join(directory, "fake.json"), "w", encoding="utf-8") as handle:
        json.dump(settled, handle)


_DASH = "\u2014"
_CHECKPOINT_SECTIONS = (
    "Identity and state",
    "Boundaries and blockers",
    "Next action",
    "Resume reading",
    "Evidence and working changes",
    "Do not redo",
)
_RESUME_LINE = (
    'Resume widget-export from "$PROJECT/.preclear/widget-export/checkpoint.md" '
    + _DASH + " main @ abc1234 " + _DASH + " step 2 done untested; JSON-default diff pending"
)


def default_row1_stages() -> list:
    """The stage scripts of a clean row 1 run: s1 work turn, s2 resumed /preclear turn, s3 fresh resume.

    s1 writes the exporter and loads the project CLAUDE.md. s2 runs the wrapper's status for real, writes the
    checkpoint and a memory file, has one wrapper bind denied and ends with a fenced resume line. s3 is a new
    session that loads the project CLAUDE.md again and reads the checkpoint.
    """
    s1 = {
        "ops": [
            {"op": "hook", "payloads": [
                {"file_path": "$CWD/CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"}]},
            {"op": "init"},
            {"op": "write", "path": "$PROJECT/widget_export.py", "text": "def export(rows):\n    return rows\n"},
            {"op": "text", "text": "step 2 done"},
        ],
        "result": {"text": "step 2 done\nfunctions are small and pure\nno tests were run",
                   "total_cost_usd": 0.03, "num_turns": 2},
    }
    checkpoint = "".join("## %s\nA short body for this section.\n\n" % name for name in _CHECKPOINT_SECTIONS)
    s2 = {
        "ops": [
            {"op": "tool", "name": "Bash", "input": {"command": "$WRAPPER status"}, "run": "wrapper",
             "args": ["status"]},
            {"op": "tool", "name": "Bash", "input": {"command": "ls"}, "content": "CLAUDE.md"},
            {"op": "write", "path": "$PROJECT/.preclear/widget-export/checkpoint.md", "text": checkpoint},
            {"op": "tool", "name": "Write",
             "input": {"file_path": "$PROJECT/.preclear/widget-export/checkpoint.md"}, "content": "written"},
            {"op": "write", "path": "$AUTOMEM/widget-export-json-default.md",
             "text": "JSON is the default export format; CSV only on request.\n"},
            {"op": "tool", "name": "Write",
             "input": {"file_path": "$AUTOMEM/widget-export-json-default.md"}, "content": "written"},
            {"op": "tool", "name": "Bash",
             "input": {"command": "$WRAPPER bind --ledger x --session y"}, "denied": True},
            {"op": "text", "text": "checkpoint written"},
        ],
        "result": {"text": "Checkpoint written.\n\n```\n" + _RESUME_LINE + "\n```\n",
                   "total_cost_usd": 0.09, "delta": 0.06, "num_turns": 5},
    }
    s3 = {
        "ops": [
            {"op": "hook", "payloads": [
                {"file_path": "$CWD/CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"}]},
            {"op": "init"},
            {"op": "tool", "name": "Read",
             "input": {"file_path": "$PROJECT/.preclear/widget-export/checkpoint.md"}, "content": "checkpoint body"},
            {"op": "text", "text": "read the checkpoint"},
        ],
        "result": {"text": "Read the checkpoint; nothing was changed.", "total_cost_usd": 0.04, "num_turns": 2},
    }
    return [s1, s2, s3]


def stages_with(stages: list, index: int, **changes: Any) -> list:
    """Return a deep copy of the stage list with the fields of one stage replaced (ops, result, ...)."""
    copied = json.loads(json.dumps(stages))
    copied[index].update(changes)
    return copied


def _with_ops(stages: list, index: int, ops: list) -> list:
    """Return a deep copy of the stage list with ops appended to the ops of one stage."""
    copied = json.loads(json.dumps(stages))
    copied[index]["ops"] = list(copied[index].get("ops", [])) + json.loads(json.dumps(ops))
    return copied


def seed_outside_write(stages: list, stage_index: int = 1) -> list:
    """A stage list whose stage really writes a small file directly under the run root, outside every
    approved root (a snapshot-path breach; no stream event announces it)."""
    return _with_ops(stages, stage_index, [
        {"op": "write", "path": "$RUN/outside.txt", "text": "outside the approved roots\n"},
    ])


_HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HARNESS_DIR))
_COPIED_FILES = (
    "SKILL.md",
    "tests/harness/checkpoint-wrapper",
    "tests/harness/checkpoint_stub.py",
    "tests/harness/pc_hooklog.py",
    "tests/harness/data/row1-s1-prompt.md",
    "tests/harness/data/row1-plan.md",
)
_COPIED_TREES = (
    "references",
    "tests/fixtures/bound-ledger",
    "tests/evidence/publication-2026-10-20/row1-wrong-binding",
)


class RowRig(object):
    """A temporary world for a row run: a real git repository holding what row 1 reads, a harness
    home, a runs folder, a user home, a bin folder with the scripted claude, and an environment.

    Nothing here touches the caller's real repository, home or harness folder. Scratch folders are
    never deleted.
    """

    def __init__(self, base: Optional[str] = None, stages: Optional[list] = None, **config: Any) -> None:
        self.base = os.path.realpath(base if base else tempfile.mkdtemp(prefix="pc-row-"))
        self.repo = os.path.join(self.base, "repo")
        self.bin = os.path.join(self.base, "bin")
        self.harness_home = os.path.join(self.base, "harness")
        self.user_home = os.path.join(self.base, "user-home")
        self.runs = os.path.join(self.base, "runs-root", "runs")
        self.outside = os.path.join(self.base, "outside")
        for folder in (self.bin, self.user_home, self.outside):
            os.makedirs(folder, exist_ok=True)
        self.stages = default_row1_stages() if stages is None else stages
        self.config = dict(config)
        self.config.setdefault("outside_dir", self.outside)
        self.claude = make_scripted_claude(self.bin, dict(self.config, stages=self.stages))
        self.env = {
            "PATH": os.pathsep.join([self.bin] + list(SYSTEM_DIRS)),
            "HOME": self.user_home,
            "LANG": "en_US.UTF-8",
            "PRECLEAR_HARNESS_HOME": self.harness_home,
            "PRECLEAR_RUNS_ROOT": self.runs,
        }
        self._build_repo()

    def _build_repo(self) -> None:
        os.makedirs(self.repo)
        for relative in _COPIED_FILES:
            source = os.path.join(_REPO_ROOT, *relative.split("/"))
            if os.path.isfile(source):
                target = os.path.join(self.repo, *relative.split("/"))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(source, target)
        for relative in _COPIED_TREES:
            source = os.path.join(_REPO_ROOT, *relative.split("/"))
            if os.path.isdir(source):
                shutil.copytree(source, os.path.join(self.repo, *relative.split("/")))
        os.makedirs(os.path.join(self.repo, "tests", "evidence"), exist_ok=True)
        env = git_env({"PATH": os.pathsep.join(SYSTEM_DIRS)})
        for args in (["init", "-q"], ["symbolic-ref", "HEAD", "refs/heads/main"], ["add", "-A"],
                     ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "rig repository"]):
            subprocess.run(["git", "-C", self.repo] + args, env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def configure(self, stages: Optional[list] = None, **config: Any) -> None:
        """Rewrite the scripted claude's fake.json; the call counter is not reset."""
        if stages is not None:
            self.stages = stages
        self.config.update(config)
        write_scripted_config(self.bin, dict(self.config, stages=self.stages))

    def calls(self) -> list:
        """Return the records of the stage calls the scripted claude has served."""
        path = os.path.join(self.bin, "calls.log")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle.read().splitlines()]

    def tripwire(self) -> list:
        return read_tripwire(self.bin)

    def context(self, **overrides: Any) -> Any:
        """Return a pc_rows.RunContext for this world (run_root, sanitizer and deny_entries unset)."""
        import pc_rows
        import pc_spike

        home_dir = self.env["HOME"]
        harness = pc_spike.harness_home(self.env, home_dir, self.repo)
        config_dir = pc_spike.ensure_config_dir(self.env, home_dir, self.repo)[0]
        runs = pc_spike.runs_root(self.env, home_dir, self.repo)
        pc_spike.ensure_runs_root(runs)
        destination = os.path.join(
            self.repo, "tests", "evidence", pc_rows.evidence_folder_name("2026-10-28", "claude-sonnet-5-5")
        )
        values = dict(
            repo_root=self.repo,
            env=dict(self.env),
            claude=self.claude,
            harness_home=harness,
            config_dir=config_dir,
            runs_root=runs,
            run_root=None,
            destination=destination,
            evidence_date="2026-10-28",
            model="claude-sonnet-5-5",
            sanitizer=None,
            deny_entries=None,
            budget=Decimal("2.00"),
            banner="2.1.310 (Claude Code)",
            version="2.1.310",
        )
        values.update(overrides)
        return pc_rows.RunContext(**values)

    def new_run_root(self, ctx: Any, name: str) -> str:
        import pc_runroot

        return pc_runroot.allocate_run_root(ctx.runs_root, name)
