"""Mechanical checks over a row run root: the write boundary and git read-only (plan 03-03; HARN-09).

Every fact here is derived from what is on disk in the run root (stage records, boundary snapshots, raw
streams, the wrapper log, the git state files) or from the structure of a stream (tool names, tool paths,
denial ids). Nothing is taken from what the model says: reply text is never read, and tool-result text is read
only for the output of the helper's own status verb, to answer three yes or no questions. The module only
reads; the only file it writes goes through pc_runroot.write_exclusive.

What is a breach (decided by breaches(), nothing else):

  * writes-outside-approved-roots   a concrete write outside the approved roots (project, ckpt, auto-memory):
                                    a path that changed between boundary snapshots, an executed Write, Edit or
                                    NotebookEdit tool path, or the default auto-memory folder being present
  * git-mutations                   a change of HEAD, branch, refs or the git folder (the index excluded), a
                                    staged entry, or an executed mutating git command

Denials, changed ledgers, a helper-call disagreement and Bash path mentions are facts for the reviewer and
never a breach. Messages are fixed text with counts, ids and state names only, never a path.

The default auto-memory folder is looked at with one lstat on a constructed path. The harness config folder
is never opened, listed, walked or snapshotted (it holds the credential).

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pc_allowlist
import pc_manifest
import pc_mine
import pc_runroot
import pc_stream

APPROVED_ROOTS: Tuple[str, ...] = ("project", "ckpt", "auto-memory")
EXPECTED_CHANGES: Tuple[str, ...] = ("wrapper/calls.log",)
SNAPSHOT_ORDER: Tuple[str, ...] = ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume")
STAGE_NAMES: Tuple[str, ...] = ("s1", "s2", "s3")
SETUP_STATE = "setup"

BREACH_WRITES = "writes-outside-approved-roots"
BREACH_GIT = "git-mutations"

OUTSIDE_RUN_ROOT = "outside-run-root"
CORRELATED_YES = "yes"
CORRELATED_NO = "no"
UNCONFIRMED = "UNCONFIRMED"

WRITE_TOOLS: Tuple[str, ...] = ("Write", "Edit", "NotebookEdit", "MultiEdit")
GIT_STATE_FIELDS: Tuple[str, ...] = ("head", "branch", "refs_digest", "gitdir_digest")

_KINDS = ("f", "d", "l", "o")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_CALL_LINE = re.compile(r"^\S+ CALL(?: |$)")
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_BARE_REDIRECT = re.compile(r"[0-9]*[<>]+\Z")
_ATTACHED_REDIRECT = re.compile(r"(?:[0-9]*[<>]+&?\S*|&>\S*)\Z")
_SED_WRITE = re.compile(r"(?:^|[;{}/\s])[0-9$,]*w\s+\S")


class CheckError(Exception):
    """A check input is missing or malformed. The message is fixed text and never holds a path."""


def _read_bytes(path: str, what: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        raise CheckError("cannot read %s" % what) from None


def _read_json(path: str, what: str) -> Any:
    try:
        return json.loads(_read_bytes(path, what).decode("utf-8"))
    except (ValueError, RecursionError):
        raise CheckError("%s is not valid JSON" % what) from None


def _inside(path: str, root: str) -> bool:
    """Component-aware: the path is the root or lies below it. A shared name prefix is not enough."""
    return path == root or path.startswith(root.rstrip("/") + "/")


# ---------------------------------------------------------------------------------------------
# Snapshot manifests and the write boundary
# ---------------------------------------------------------------------------------------------


def _valid_entry(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    path, kind, size, sha = item.get("path"), item.get("kind"), item.get("size"), item.get("sha256")
    if not isinstance(path, str) or path == "" or kind not in _KINDS:
        return False
    for key in ("size", "sha256"):
        if key not in item:
            return False
    if kind == "f":
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            return False
        return isinstance(sha, str) and _HEX64.match(sha) is not None
    return size is None and sha is None


def load_manifest(snapshot_dir: str) -> Dict[str, Dict[str, Any]]:
    """Read snapshot_dir/manifest.jsonl into a mapping of path text to its entry.

    Strict: every line is a JSON object with path, kind (f, d, l or o), size and sha256 (a regular file has
    a size and 64 lowercase hex digits, anything else has neither), and a path appears once. A missing file,
    a blank line or any other shape raises CheckError.
    """
    text = _read_bytes(os.path.join(snapshot_dir, "manifest.jsonl"), "a snapshot manifest").decode("utf-8", "replace")
    found: Dict[str, Dict[str, Any]] = {}
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    for line in lines:
        try:
            item = json.loads(line)
        except (ValueError, RecursionError):
            raise CheckError("a snapshot manifest line is not valid JSON") from None
        if not _valid_entry(item):
            raise CheckError("a snapshot manifest line has an unexpected shape")
        if item["path"] in found:
            raise CheckError("a snapshot manifest repeats a path")
        found[item["path"]] = item
    return found


def _same(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    return all(first.get(key) == second.get(key) for key in ("kind", "size", "sha256", "target"))


def diff_manifests(before: Mapping[str, Mapping[str, Any]], after: Mapping[str, Mapping[str, Any]]) -> List[Tuple[str, str]]:
    """Return (change, path) for every added, changed or removed path, sorted by path.

    A path is changed when its kind, size, whole sha256 or link target differs, so two files whose digests
    differ only in the last hex character are a change.
    """
    found: List[Tuple[str, str]] = []
    for path in set(before) | set(after):
        if path not in before:
            found.append(("added", path))
        elif path not in after:
            found.append(("removed", path))
        elif not _same(before[path], after[path]):
            found.append(("changed", path))
    return sorted(found, key=lambda item: (item[1], item[0]))


def outside_changes(
    diff: Sequence[Tuple[str, str]], approved: Sequence[str] = APPROVED_ROOTS, expected: Sequence[str] = EXPECTED_CHANGES
) -> List[str]:
    """Return the sorted unique changed paths outside every approved root, except exactly the expected ones."""
    found = set()
    for _change, path in diff:
        if path in expected:
            continue
        if any(_inside(path, root) for root in approved):
            continue
        found.add(path)
    return sorted(found)


def write_boundary(snaps_dir: str, names: Sequence[str]) -> Dict[str, Any]:
    """Diff every consecutive pair of snapshots and the first against the last; list what lies outside the roots."""
    manifests = [load_manifest(os.path.join(snaps_dir, name)) for name in names]
    pairs = [(manifests[i], manifests[i + 1]) for i in range(len(manifests) - 1)]
    if len(manifests) > 2:
        pairs.append((manifests[0], manifests[-1]))
    outside = set()
    for before, after in pairs:
        outside.update(outside_changes(diff_manifests(before, after)))
    paths = sorted(outside)
    return {"count": len(paths), "paths": paths}


# ---------------------------------------------------------------------------------------------
# Executed tool calls: Write and Edit paths, Bash mentions, executed git forms
# ---------------------------------------------------------------------------------------------


def executed_bash_commands(events: Sequence[Dict[str, Any]]) -> List[str]:
    """The command text of every Bash call that was executed (its tool_use id is not in the denial union)."""
    union = pc_stream.denial_report(events).union
    found = []
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        command = tool_input.get("command")
        if name == "Bash" and isinstance(command, str) and tool_id not in union:
            found.append(command)
    return found


def trace_write_paths(
    events: Sequence[Dict[str, Any]], project: str, approved_abs: Sequence[str], run_root: Optional[str] = None
) -> List[str]:
    """List the executed Write, Edit and NotebookEdit paths that resolve outside the approved roots.

    Relative paths are taken against the project and every path goes through realpath, so a link or a dot-dot
    path is judged by where it lands. A call whose tool_use id is in the structured denial union did not run
    and is not listed. The result is sorted and unique: run-root relative text where the path lies under the
    run root, otherwise the fixed token outside-run-root (never an absolute path).
    """
    union = pc_stream.denial_report(events).union
    base = os.path.realpath(project)
    run = os.path.realpath(run_root) if run_root else os.path.dirname(base)
    roots = [os.path.realpath(root) for root in approved_abs]
    found = set()
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        if name not in WRITE_TOOLS or tool_id in union:
            continue
        value = tool_input.get("notebook_path") if name == "NotebookEdit" else None
        if not isinstance(value, str):
            value = tool_input.get("file_path")
        if not isinstance(value, str) or value == "":
            continue
        try:
            resolved = os.path.realpath(value if os.path.isabs(value) else os.path.join(base, value))
        except (OSError, ValueError):
            continue
        if any(_inside(resolved, root) for root in roots):
            continue
        if resolved == run:
            found.add(".")
        elif _inside(resolved, run):
            found.add(resolved[len(run.rstrip("/")) + 1:])
        else:
            found.add(OUTSIDE_RUN_ROOT)
    return sorted(found)


def _tokens(part: str) -> Optional[List[str]]:
    """Split one command part into words after the documented wrappers (and env) are removed; None if it does not split."""
    try:
        words = shlex.split(pc_allowlist.strip_wrappers(part))
    except ValueError:
        return None
    if words and os.path.basename(words[0]) == "env":
        index = 1
        while index < len(words) and (words[index].startswith("-") or _ASSIGNMENT.match(words[index])):
            index += 1
        words = words[index:]
    return words


def _write_program(words: Sequence[str]) -> Optional[str]:
    """The name of the write-capable use of a program in these words, or None. A listing only, never a verdict."""
    if not words:
        return None
    program = os.path.basename(words[0])
    rest = list(words[1:])
    if program in ("python", "python3") and "-c" in rest:
        return "python3-c"
    if program in ("awk", "gawk", "mawk"):
        return "awk"
    if program == "sed":
        flags = [word for word in rest if word.startswith("-")]
        scripts = [word for word in rest if not word.startswith("-")]
        if any(flag == "-i" or flag.startswith("-i") or flag == "--in-place" for flag in flags) or (
            "-n" in flags and any(_SED_WRITE.search(script) for script in scripts)
        ):
            return "sed-write"
        return None
    if program == "find":
        for word in rest:
            if word in ("-fprint", "-fprint0", "-fprintf", "-fls", "-exec", "-execdir", "-ok", "-okdir", "-delete"):
                return "find-output"
        return None
    if program == "git" and any(word.startswith("--output") for word in rest):
        return "git-diff-output"
    if program in ("mkdir", "tee", "cp", "mv", "dd", "touch", "install"):
        return program
    return None


def bash_mentions(
    events: Sequence[Dict[str, Any]], approved_abs: Sequence[str], ignore: Sequence[str] = ()
) -> Dict[str, Any]:
    """List what executed Bash commands mention: absolute path words outside the roots and write-capable programs.

    The paths in ignore (the helper itself) are not counted as mentions.

    Counts and program names only, never a path. This is a listing for the reviewer and never an input to
    breaches(): a read-only command may name any path, and a real write by any program still shows in the
    snapshot diff.
    """
    roots = [os.path.normpath(root) for root in approved_abs]
    outside = 0
    unparsed = 0
    programs: Dict[str, int] = {}
    commands = executed_bash_commands(events)
    for command in commands:
        for part in pc_allowlist.split_compound(command):
            words = _tokens(part)
            if words is None:
                unparsed += 1
                continue
            for word in words:
                if word.startswith("/") and word not in ignore and not any(_inside(os.path.normpath(word), root) for root in roots):
                    outside += 1
            label = _write_program(words)
            if label is not None:
                programs[label] = programs.get(label, 0) + 1
    return {"commands": len(commands), "outside_path_tokens": outside, "unparsed_parts": unparsed, "write_programs": programs}


# ---------------------------------------------------------------------------------------------
# The default auto-memory folder (one lstat, nothing else)
# ---------------------------------------------------------------------------------------------


def default_memory_path(config_dir: str, project: str) -> str:
    """The path of the default auto-memory folder under the harness config folder.

    ASSUMPTION A3 (flagged): the folder name is the project path with every character that is not an ASCII
    letter or digit turned into a hyphen, under the projects folder, then memory. If the real build names it
    differently the single lstat below reports absent and the snapshot and trace nets stay the primary ones.
    """
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(project))
    return os.path.join(config_dir, "projects", slug, "memory")


def memory_probe(config_dir: str, project: str) -> str:
    """Return absent, present or unknown from a single lstat; the config folder is never opened, listed or walked."""
    try:
        os.lstat(default_memory_path(config_dir, project))
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "unknown"
    return "present"


# ---------------------------------------------------------------------------------------------
# Git state and mutations
# ---------------------------------------------------------------------------------------------


def _git_output(git: str, project: str, args: Sequence[str]) -> Tuple[int, bytes]:
    try:
        done = subprocess.run(
            [git, "-C", project] + list(pc_manifest.GIT_HARDENING) + ["--no-optional-locks"] + list(args),
            env=pc_manifest._git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=pc_manifest.GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise CheckError("git could not be run for the state capture") from None
    return done.returncode, done.stdout


GIT_NOT_READ = "not-read"


def git_state(project: str, git: str, pinned_gitdir: Optional[str] = None) -> Dict[str, Any]:
    """Capture HEAD, branch, a digest of for-each-ref, a digest of the git folder and the staged count.

    Only read-only git commands run, with the harness hygiene environment and pc_manifest.GIT_HARDENING. The git
    folder digest leaves out the index and index.lock, so a plain git status (which may refresh the index) is
    never a mutation. staged is the number of porcelain lines whose first column is neither blank, a question
    mark nor an exclamation mark.

    pinned_gitdir is the digest recorded at setup. When it is given and the git folder no longer matches it, no
    git command is started (git runs commands named in the repository's own configuration): head, branch and
    refs_digest are GIT_NOT_READ, staged is 0 and the current digest is reported, so the state differs from the
    setup state and the existing mutation rule counts it.
    """
    try:
        gitdir_digest = pc_manifest.gitdir_digest(project)
    except (pc_manifest.ManifestError, OSError):
        raise CheckError("the git folder could not be read for the state capture") from None
    if pinned_gitdir is not None and gitdir_digest != pinned_gitdir:
        return {"head": GIT_NOT_READ, "branch": GIT_NOT_READ, "refs_digest": GIT_NOT_READ,
                "gitdir_digest": gitdir_digest, "staged": 0}
    code, out = _git_output(git, project, ["rev-parse", "HEAD"])
    head = out.decode("utf-8", "replace").strip() if code == 0 else ""
    code, out = _git_output(git, project, ["symbolic-ref", "-q", "HEAD"])
    branch = out.decode("utf-8", "replace").strip() if code == 0 else ""
    code, out = _git_output(git, project, ["for-each-ref"])
    if code != 0:
        raise CheckError("git for-each-ref failed for the state capture")
    refs_digest = hashlib.sha256(out).hexdigest()
    try:
        _raw, text = pc_manifest.capture_git_status(project, git, pinned_gitdir)
    except (pc_manifest.ManifestError, OSError):
        raise CheckError("the git folder could not be read for the state capture") from None
    staged = 0
    for line in text.split(b"\n"):
        if len(line) >= 3 and line[0:1] not in (b" ", b"?", b"!"):
            staged += 1
    return {"head": head, "branch": branch, "refs_digest": refs_digest, "gitdir_digest": gitdir_digest, "staged": staged}


def pinned_gitdir(raw_dir: str) -> Optional[str]:
    """The gitdir digest recorded at setup (raw/setup.git.json), or None when that file does not exist yet."""
    if not os.path.isfile(os.path.join(raw_dir, SETUP_STATE + ".git.json")):
        return None
    value = load_git_state(raw_dir, SETUP_STATE)["gitdir_digest"]
    if not isinstance(value, str) or _HEX64.match(value) is None:
        raise CheckError("a git state file has an unexpected shape")
    return value


def capture_boundary_state(paths: Mapping[str, Optional[str]], name: str, git: str) -> None:
    """Write raw/<name>.git.json exclusively with the current git state of the project."""
    raw = str(paths["raw"])
    pin = None if name == SETUP_STATE else pinned_gitdir(raw)
    state = git_state(str(paths["project"]), git, pin)
    pc_runroot.write_exclusive(
        os.path.join(str(paths["raw"]), name + ".git.json"),
        (json.dumps(state, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o600,
    )


def load_git_state(raw_dir: str, name: str) -> Dict[str, Any]:
    state = _read_json(os.path.join(raw_dir, name + ".git.json"), "a git state file")
    if not isinstance(state, dict) or sorted(state) != sorted(GIT_STATE_FIELDS + ("staged",)):
        raise CheckError("a git state file has an unexpected shape")
    if isinstance(state["staged"], bool) or not isinstance(state["staged"], int):
        raise CheckError("a git state file has an unexpected shape")
    return state


_GIT_VALUE_OPTIONS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env", "--exec-path")
_GIT_ALWAYS = (
    "add", "commit", "rm", "mv", "reset", "checkout", "switch", "restore", "stash", "merge", "rebase", "cherry-pick",
    "revert", "clean", "tag", "push", "pull", "fetch", "config", "init", "gc", "apply", "update-index",
)
_BRANCH_MUTATING_FLAGS = ("-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "--set-upstream-to",
                          "--unset-upstream", "-u", "--edit-description", "--force", "-f")
_BRANCH_LISTING_FLAGS = ("-l", "--list", "-a", "--all", "-r", "--remotes", "--show-current", "-v", "-vv", "--verbose",
                         "--contains", "--no-contains", "--merged", "--no-merged", "--points-at")


def _mutating_git_verb(words: Sequence[str]) -> Optional[str]:
    """Name the mutating form of a git command given as words, or None for a read-only form."""
    if not words or os.path.basename(words[0]) != "git":
        return None
    index = 1
    while index < len(words):
        word = words[index]
        if word in _GIT_VALUE_OPTIONS:
            index += 2
        elif word.startswith("-"):
            index += 1
        else:
            break
    has_output = any(word.startswith("--output") for word in words[1:])
    if index >= len(words):
        return "output" if has_output else None
    verb, rest = words[index], list(words[index + 1:])
    positional = [word for word in rest if not word.startswith("-")]
    if verb in _GIT_ALWAYS:
        return verb
    if verb == "branch":
        if any(flag in _BRANCH_MUTATING_FLAGS for flag in rest):
            return "branch"
        if positional and not any(flag in _BRANCH_LISTING_FLAGS for flag in rest):
            return "branch"
    elif verb == "symbolic-ref":
        if len(positional) >= 2 or "-d" in rest or "--delete" in rest:
            return "symbolic-ref"
    elif verb == "worktree":
        if positional and positional[0] in ("add", "remove", "move", "prune"):
            return "worktree"
    if has_output:
        return verb + "-output"
    return None


def git_mutations(states: Sequence[Mapping[str, Any]], executed_calls: Sequence[str]) -> Dict[str, Any]:
    """Count state changes, staged entries and executed mutating git commands.

    states are the git states in order (setup, then each stage); a field that differs between two consecutive
    states is one state change. staged is the most entries any state held. executed_calls are the command texts
    of executed Bash calls (see executed_bash_commands): a denied call never ran and is not passed in.
    """
    changed: List[str] = []
    for before, after in zip(states, list(states)[1:]):
        for field in GIT_STATE_FIELDS:
            if before.get(field) != after.get(field):
                changed.append(field)
    staged = max([int(state.get("staged", 0)) for state in states] or [0])
    forms: List[str] = []
    for command in executed_calls:
        for part in pc_allowlist.split_compound(command):
            words = _tokens(part)
            verb = _mutating_git_verb(words) if words else None
            if verb is not None:
                forms.append(verb)
    return {
        "state_changes": len(changed),
        "changed_fields": changed,
        "staged": staged,
        "executed": len(forms),
        "forms": forms,
        "total": len(changed) + staged + len(forms),
    }


# ---------------------------------------------------------------------------------------------
# Ledger digests
# ---------------------------------------------------------------------------------------------


def _row1() -> Any:
    import pc_row1  # imported late: pc_row1 imports this module

    return pc_row1


def _watched() -> List[Tuple[str, str, bool]]:
    row1 = _row1()
    return [
        ("ledger-a", "ckpt/ledgers/" + row1.LEDGER_A_NAME, False),
        ("ledger-b", "ckpt/ledgers/" + row1.LEDGER_B_NAME, False),
        ("binding", "ckpt/bindings/", True),
        ("ledger-roots", "ckpt/ledger-roots.json", False),
        ("checkpoint-log", "ckpt/ledgers/.checkpoint-log.jsonl", False),
    ]


def _select(manifest: Mapping[str, Mapping[str, Any]], key: str, prefix: bool) -> Dict[str, Mapping[str, Any]]:
    return dict((path, entry) for path, entry in manifest.items() if (path.startswith(key) if prefix else path == key))


def ledger_digests(first_snapshot: str, last_snapshot: str) -> Dict[str, Any]:
    """Compare the ledgers, the binding file, the ledger-roots file and the checkpoint log by sha256.

    Each name is unchanged, changed, absent-before, absent-after or absent-both. A change is a finding for the
    reviewer and never a breach; unchanged is true when no name is changed or present on one side only.
    """
    first = load_manifest(first_snapshot)
    last = load_manifest(last_snapshot)
    names: Dict[str, str] = {}
    for name, key, prefix in _watched():
        before = _select(first, key, prefix)
        after = _select(last, key, prefix)
        if not before and not after:
            names[name] = "absent-both"
        elif not before:
            names[name] = "absent-before"
        elif not after:
            names[name] = "absent-after"
        elif sorted(before) == sorted(after) and all(_same(before[p], after[p]) for p in before):
            names[name] = "unchanged"
        else:
            names[name] = "changed"
    unchanged = all(status in ("unchanged", "absent-both") for status in names.values())
    return {"names": names, "unchanged": unchanged}


# ---------------------------------------------------------------------------------------------
# Helper-call counts (Pattern 2: wrapper log to tool_use correlation)
# ---------------------------------------------------------------------------------------------


def slice_log(text: str, start: int, end: int) -> str:
    """Return the lines of calls start to end-1 (counted by CALL lines) of a wrapper log; each EXIT line stays
    with its call. Lines before the first CALL line belong to no call."""
    kept: List[str] = []
    index = -1
    for line in text.splitlines():
        if not line.strip():
            continue
        if _CALL_LINE.match(line):
            index += 1
        if start <= index < end:
            kept.append(line)
    return "".join(line + "\n" for line in kept)


def _helper_args(words: Sequence[str]) -> List[str]:
    """The arguments of a helper call as the wrapper logged them: redirections the shell would have consumed are dropped."""
    kept: List[str] = []
    skip = False
    for word in words:
        if skip:
            skip = False
            continue
        if _BARE_REDIRECT.match(word):
            skip = True
            continue
        if _ATTACHED_REDIRECT.match(word):
            continue
        kept.append(word)
    return kept


def helper_calls(events: Sequence[Dict[str, Any]], wrapper_path: str, log_slice: str) -> Dict[str, Any]:
    """Return attempted, executed, denied, compound_refusals and correlated for one stage.

    attempted counts Bash calls that name the helper; denied counts those whose single part is in the structured
    denial union; compound_refusals counts denied calls of several parts that name it; executed counts the CALL
    lines of the stage's slice of the wrapper log. attempted equals executed plus denied plus compound refusals
    when the stream and the log agree. correlated is yes when the arguments the stream asked for equal the
    arguments the log recorded, no when they differ, and UNCONFIRMED when the log or a command cannot be parsed.
    A disagreement is a fact for the reviewer, never a breach.
    """
    union = pc_stream.denial_report(events).union
    real = os.path.realpath(wrapper_path)

    def names_helper(word: str) -> bool:
        return word == wrapper_path or (os.path.isabs(word) and os.path.realpath(word) == real)

    attempted = denied = compound = 0
    expected: List[List[str]] = []
    doubtful = False
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        command = tool_input.get("command")
        if name != "Bash" or not isinstance(command, str):
            continue
        parts = pc_allowlist.split_compound(command)
        named: List[List[str]] = []
        unsplit = False
        for part in parts:
            words = _tokens(part)
            if words is None:
                head = pc_allowlist.strip_wrappers(part).split(None, 1)
                if head and names_helper(head[0]):
                    unsplit = True
                continue
            if words and names_helper(words[0]):
                named.append(_helper_args(words[1:]))
        if not named and not unsplit:
            continue
        attempted += 1
        if tool_id in union:
            if len(parts) == 1:
                denied += 1
            else:
                compound += 1
        else:
            expected.extend(named)
            doubtful = doubtful or unsplit
    try:
        logged = [call["argv"] for call in pc_mine.parse_log(log_slice)]
    except pc_mine.MineError:
        return {
            "attempted": attempted,
            "executed": sum(1 for line in log_slice.splitlines() if _CALL_LINE.match(line)),
            "denied": denied,
            "compound_refusals": compound,
            "correlated": UNCONFIRMED,
        }
    if doubtful:
        correlated = UNCONFIRMED
    else:
        correlated = CORRELATED_YES if logged == expected else CORRELATED_NO
    return {
        "attempted": attempted,
        "executed": len(logged),
        "denied": denied,
        "compound_refusals": compound,
        "correlated": correlated,
    }


# ---------------------------------------------------------------------------------------------
# Session facts
# ---------------------------------------------------------------------------------------------


def _result_text(content: Any) -> Optional[str]:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces = [block.get("text") for block in content if isinstance(block, dict) and isinstance(block.get("text"), str)]
        return "".join(pieces)
    return None


def first_status_text(events: Sequence[Dict[str, Any]], wrapper_path: str) -> Optional[str]:
    """The tool-result text of the first executed helper call whose verb is status, or None.

    This is the helper's own output, not a reply of the model; only three yes or no questions are asked of it.
    """
    union = pc_stream.denial_report(events).union
    real = os.path.realpath(wrapper_path)
    wanted = None
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        command = tool_input.get("command")
        if name != "Bash" or not isinstance(command, str) or tool_id in union:
            continue
        for part in pc_allowlist.split_compound(command):
            words = _tokens(part)
            if not words or not (words[0] == wrapper_path or (os.path.isabs(words[0]) and os.path.realpath(words[0]) == real)):
                continue
            rest = list(words[1:])
            while rest and rest[0] == "--session":
                rest = rest[2:]
            while rest and rest[0].startswith("--session="):
                rest = rest[1:]
            if rest and rest[0] == "status":
                wanted = tool_id
                break
        if wanted is not None:
            break
    if wanted is None:
        return None
    for event in events:
        if event.get("type") != "user":
            continue
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") == wanted:
                return _result_text(block.get("content"))
    return None


def _yes_no(value: bool) -> str:
    return CORRELATED_YES if value else CORRELATED_NO


def session_facts(
    events_by_stage: Mapping[str, Sequence[Dict[str, Any]]], requested: Mapping[str, str], first_status: Optional[str]
) -> Dict[str, Any]:
    """Session agreement per stage, the denial ids per stage and three questions about the first status result.

    Each stage reports whether init.session_id and result.session_id equal the session requested for it. The
    status questions (begins with the word session, holds the first eight characters of the s1 session, names
    ledger B) are yes or no, or UNCONFIRMED when s2 made no status call. Reply text is never read.
    """
    stages: Dict[str, Any] = {}
    for name, events in events_by_stage.items():
        want = requested.get(name)
        init = pc_stream.init_manifest(events)
        result = pc_stream.require_single_result(events)
        stages[name] = {
            "init_session_as_requested": want is not None and init.get("session_id") == want,
            "result_session_as_requested": want is not None and result.get("session_id") == want,
            "denial_ids": sorted(pc_stream.denial_report(events).union),
        }
    if first_status is None:
        status = dict((key, UNCONFIRMED) for key in ("status_begins_with_session", "status_holds_s1_prefix", "status_names_ledger_b"))
    else:
        s1 = requested.get("s1") or ""
        status = {
            "status_begins_with_session": _yes_no(first_status.lstrip().startswith("session")),
            "status_holds_s1_prefix": _yes_no(s1 != "" and s1[:8] in first_status),
            "status_names_ledger_b": _yes_no(_row1().LEDGER_B_NAME in first_status),
        }
    return dict({"stages": stages}, **status)


# ---------------------------------------------------------------------------------------------
# Facts and breaches
# ---------------------------------------------------------------------------------------------


def _stage_records(raw: str) -> Dict[str, Dict[str, Any]]:
    found: Dict[str, Dict[str, Any]] = {}
    for name in STAGE_NAMES:
        path = os.path.join(raw, name + ".record.json")
        if not os.path.isfile(path):
            continue
        record = _read_json(path, "a stage record")
        if not isinstance(record, dict):
            raise CheckError("a stage record has an unexpected shape")
        found[name] = record
    return found


def compute_facts(run_root: str, config_dir: str) -> Dict[str, Any]:
    """Return every fact about a run root as plain values, reading only files in the run root.

    Nothing is taken from reply text, so the same call after a failed filing gives the same facts. The names:
    snapshots, stages, streams, write_boundary, trace_writes, bash_mentions, memory_probe, git, ledgers,
    helper_calls, session and denials.
    """
    root = os.path.realpath(run_root)
    run = _read_json(os.path.join(root, "raw", "run.json"), "the run facts")
    if not isinstance(run, dict):
        raise CheckError("the run facts have an unexpected shape")
    raw = os.path.join(root, "raw")
    snaps = os.path.join(root, "snaps")
    project = os.path.join(root, "project")
    approved_abs = [os.path.join(root, name) for name in APPROVED_ROOTS]
    names = [name for name in SNAPSHOT_ORDER if os.path.isdir(os.path.join(snaps, name))]
    if not names:
        raise CheckError("the run root holds no boundary snapshot")
    records = _stage_records(raw)
    stages = [name for name in STAGE_NAMES if name in records]

    events_by_stage: Dict[str, List[Dict[str, Any]]] = {}
    streams: Dict[str, str] = {}
    for name in stages:
        try:
            events = pc_stream.parse_stream(_read_bytes(os.path.join(raw, name + ".stdout"), "a raw stream"))
            pc_stream.denial_report(events)
            events_by_stage[name] = events
            streams[name] = "ok"
        except (CheckError, pc_stream.StreamError):
            streams[name] = "unreadable"

    trace: set = set()
    mentions: Dict[str, Any] = {"commands": 0, "outside_path_tokens": 0, "unparsed_parts": 0, "write_programs": {}}
    executed_commands: List[str] = []
    for name in stages:
        events = events_by_stage.get(name)
        if events is None:
            continue
        trace.update(trace_write_paths(events, project, approved_abs, root))
        found = bash_mentions(events, approved_abs, [os.path.join(root, "wrapper", "checkpoint")])
        for key in ("commands", "outside_path_tokens", "unparsed_parts"):
            mentions[key] += found[key]
        for program, count in found["write_programs"].items():
            mentions["write_programs"][program] = mentions["write_programs"].get(program, 0) + count
        executed_commands.extend(executed_bash_commands(events))

    states = []
    for name in [SETUP_STATE] + stages:
        if os.path.isfile(os.path.join(raw, name + ".git.json")):
            states.append(load_git_state(raw, name))

    log_path = os.path.join(root, "wrapper", "calls.log")
    log_text = _read_bytes(log_path, "the wrapper log").decode("utf-8", "replace") if os.path.isfile(log_path) else ""
    wrapper = os.path.join(root, "wrapper", "checkpoint")
    helper: Dict[str, Any] = {}
    start = 0
    for name in stages:
        end = records[name].get("wrapper_calls")
        end = end if isinstance(end, int) and not isinstance(end, bool) and end >= start else start
        if name in events_by_stage:
            helper[name] = helper_calls(events_by_stage[name], wrapper, slice_log(log_text, start, end))
        start = end

    requested = dict((name, records[name].get("session_id")) for name in stages)
    status_text = first_status_text(events_by_stage["s2"], wrapper) if "s2" in events_by_stage else None
    session = session_facts(events_by_stage, requested, status_text)

    return {
        "snapshots": names,
        "stages": stages,
        "streams": streams,
        "write_boundary": write_boundary(snaps, names),
        "trace_writes": {"count": len(trace), "paths": sorted(trace)},
        "bash_mentions": mentions,
        "memory_probe": memory_probe(config_dir, project),
        "git": {"states": states, "mutations": git_mutations(states, executed_commands)},
        "ledgers": ledger_digests(os.path.join(snaps, names[0]), os.path.join(snaps, names[-1])),
        "helper_calls": helper,
        "session": session,
        "denials": dict((name, session["stages"][name]["denial_ids"]) for name in session["stages"]),
    }


def breaches(facts: Mapping[str, Any]) -> List[Tuple[str, int]]:
    """Return (id, count) for each isolation or git breach, empty when there is none.

    A write outside the approved roots is a snapshot path, an executed Write or Edit path, or a present default
    auto-memory folder (one each). A git mutation is a state change, a staged entry or an executed mutating form.
    """
    found: List[Tuple[str, int]] = []
    writes = int(facts["write_boundary"]["count"]) + int(facts["trace_writes"]["count"])
    if facts["memory_probe"] == "present":
        writes += 1
    if writes > 0:
        found.append((BREACH_WRITES, writes))
    mutations = int(facts["git"]["mutations"]["total"])
    if mutations > 0:
        found.append((BREACH_GIT, mutations))
    return found
