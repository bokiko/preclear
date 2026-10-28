"""Row 1 (wrong binding): seed the run root, run the stages, record the facts (plan 03-02; HARN-05, HARN-07).

What a row 1 run is, in order:

  * seed_row1         the committed wrong-binding setup in a fresh run root: the scratch project (CLAUDE.md
                      filled from the committed row's fixture, the three-step plan, a git repository on main,
                      the frozen skill as untracked files), the logging wrapper, two ledgers of which only the
                      second is bound to the work session, the audit hook and the settings file
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
  * extract_resume_line, caller_map, finish   the resume-line rule, the sanitizer's caller map and the closing
                      lines of a completed chain
  * breach_outcome    the mechanical checks of pc_checks over the run root after every stage and in finish: a
                      write outside the approved roots or a git mutation is exit 11, counts only, nothing filed
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
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
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
LEDGER_A_NAME = "CONTINUITY_CLAUDE-widget-export.md"
LEDGER_B_NAME = "CONTINUITY_CLAUDE-other-task.md"
PLAN_NAME = "2026-10-15-widget-export.md"
TOKEN_PROJECT = "<repo>/<run>/project"
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
_ISOLATION_PREFIX = "Isolation claim: "


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _read(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _within(path: str, parent: str) -> bool:
    return path == parent or path.startswith(parent.rstrip(os.sep) + os.sep)


def isolation_mode() -> str:
    """The isolation mode word, taken from the pinned isolation claim and never typed here."""
    claim = pc_flags.ISOLATION_CLAIM
    if not claim.startswith(_ISOLATION_PREFIX):
        raise ValueError("the pinned isolation claim has an unexpected shape")
    found = re.match(r"[A-Za-z]+", claim[len(_ISOLATION_PREFIX):])
    if found is None:
        raise ValueError("the pinned isolation claim has an unexpected shape")
    return found.group(0)


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

_SOURCE_FILES = (
    ("skill", "SKILL.md"),
    ("wrapper", "tests/harness/checkpoint-wrapper"),
    ("stub", "tests/harness/checkpoint_stub.py"),
    ("hooklog", "tests/harness/pc_hooklog.py"),
    ("claude_md", FIXTURE_CLAUDE_MD),
    ("ledger_a", PUBLICATION + "/snap-0-setup/" + LEDGER_A_NAME),
    ("ledger_b", PUBLICATION + "/snap-0-setup/" + LEDGER_B_NAME),
    ("plan", PLAN_DATA),
)
_SOURCE_DIRS = (
    ("references", "references"),
    ("fixture", "tests/fixtures/bound-ledger/project"),
)


def _sources(repo: str) -> Dict[str, str]:
    """Return the absolute path of every seed source; a missing one is a SpikeError naming it repo-relative."""
    found: Dict[str, str] = {}
    for key, relative in _SOURCE_FILES:
        path = os.path.join(repo, *relative.split("/"))
        if not os.path.isfile(path):
            raise pc_spike.SpikeError("a source the run root needs is missing: %s" % relative)
        found[key] = path
    for key, relative in _SOURCE_DIRS:
        path = os.path.join(repo, *relative.split("/"))
        if not os.path.isdir(path):
            raise pc_spike.SpikeError("a source the run root needs is missing: %s" % relative)
        found[key] = path
    return found


def _copy_fixture_project(source: str, dest: str) -> None:
    """Create dest and copy the fixture project into it without its CLAUDE.md and without thoughts/ledgers."""
    entries = pc_manifest.tree_manifest(source)
    for entry in entries:
        if entry["kind"] not in ("d", "f"):
            raise ValueError("a source tree holds a symlink or special file")
    pc_runroot.exclusive_dir(dest, 0o700)
    for entry in entries:
        relative = os.fsdecode(entry["path"])
        if relative == "CLAUDE.md" or relative == "thoughts/ledgers" or relative.startswith("thoughts/ledgers/"):
            continue
        target = os.path.join(dest, relative)
        if entry["kind"] == "d":
            pc_runroot.exclusive_dir(target, 0o700)
        else:
            pc_runroot.write_exclusive(target, _read(os.path.join(source, relative)), 0o644)


def _real_ledger(data: bytes, project: str) -> bytes:
    """Return a committed ledger copy with the token project path replaced by the real project path."""
    text = data.decode("utf-8").replace(TOKEN_PROJECT, project)
    if "<repo>" in text or "<run>" in text:
        raise pc_spike.SpikeError("a committed ledger copy holds a token this seed does not know")
    return text.encode("utf-8")


def _run_stub(interpreter: str, stub: str, project: str, ckpt: str, args: Sequence[str]) -> bytes:
    """Call the checkpoint stub directly (never the wrapper) and return its standard output."""
    try:
        done = subprocess.run(
            [interpreter, "-I", "-B", stub] + list(args),
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "CKPT_HOME": ckpt},
            cwd=project,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_STUB_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise pc_spike.SpikeError("the checkpoint stub could not run for the state setup") from None
    if done.returncode != 0:
        raise pc_spike.SpikeError("the checkpoint stub refused the state setup")
    return done.stdout


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

    Everything is created exclusively, so a second call on the same run root raises FileExistsError. Created,
    in order: project, wrapper, ckpt (two ledgers, the second bound to the session through the stub's own bind),
    raw (the stub's status and lint output from before the first stage), auto-memory, snaps, settings.json and
    raw/run.json (row, model, evidence date, session id, isolation mode).
    """
    try:
        canonical = str(uuid.UUID(session_id))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("the session id must be a UUID") from None
    if canonical != session_id:
        raise ValueError("the session id must be the canonical lowercase form")
    repo = os.path.realpath(repo_root)
    root = os.path.realpath(run_root)
    runs = os.path.realpath(runs_dir)
    if not os.path.isdir(root):
        raise ValueError("the run root does not exist")
    if not _within(root, runs) or root == runs:
        raise ValueError("the run root must lie under the runs folder")
    if _within(root, repo):
        raise ValueError("the run root must be outside the repository")
    source = _sources(repo)
    interpreter = os.path.realpath(sys.executable)
    if not interpreter:
        raise ValueError("no interpreter path is known")

    project = os.path.join(root, "project")
    wrapper_dir = os.path.join(root, "wrapper")
    wrapper = os.path.join(wrapper_dir, "checkpoint")
    ckpt = os.path.join(root, "ckpt")
    ledgers = os.path.join(ckpt, "ledgers")
    ledger_a = os.path.join(ledgers, LEDGER_A_NAME)
    ledger_b = os.path.join(ledgers, LEDGER_B_NAME)
    auto_memory = os.path.join(root, "auto-memory")
    raw = os.path.join(root, "raw")
    snaps = os.path.join(root, "snaps")
    settings = os.path.join(root, "settings.json")
    hooklog = os.path.join(raw, "hooklog.jsonl")

    _copy_fixture_project(source["fixture"], project)
    thoughts = os.path.join(project, "thoughts")
    if not os.path.isdir(thoughts):
        pc_runroot.exclusive_dir(thoughts, 0o700)
    plans = os.path.join(thoughts, "plans")
    pc_runroot.exclusive_dir(plans, 0o700)
    pc_runroot.write_exclusive(os.path.join(plans, PLAN_NAME), _read(source["plan"]), 0o644)
    values = {
        "executable": wrapper,
        "project": project,
        "ledger": ledger_a,
        "fallback_directory": os.path.join(project, ".preclear"),
    }
    configuration = pc_spike._fill_configuration(_read(source["claude_md"]).decode("utf-8"), values)
    pc_runroot.write_exclusive(os.path.join(project, "CLAUDE.md"), configuration.encode("utf-8"), 0o644)
    pc_spike._run_git(project, ["init", "-q"])
    pc_spike._run_git(project, ["symbolic-ref", "HEAD", "refs/heads/main"])
    pc_spike._run_git(project, ["add", "-A"])
    pc_spike._run_git(project, ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "Initial fixture commit"])

    skill_dir = os.path.join(project, ".claude", "skills", "preclear")
    pc_runroot.exclusive_dir(os.path.join(project, ".claude"), 0o700)
    pc_runroot.exclusive_dir(os.path.join(project, ".claude", "skills"), 0o700)
    pc_runroot.exclusive_dir(skill_dir, 0o700)
    pc_runroot.write_exclusive(os.path.join(skill_dir, "SKILL.md"), _read(source["skill"]), 0o644)
    pc_spike._copy_tree_with(source["references"], os.path.join(skill_dir, "references"))

    pc_runroot.exclusive_dir(wrapper_dir, 0o700)
    pc_runroot.write_exclusive(wrapper, _read(source["wrapper"]), 0o755)
    pc_runroot.write_exclusive(os.path.join(wrapper_dir, "py"), interpreter.encode("utf-8"), 0o644)
    pc_runroot.write_exclusive(os.path.join(wrapper_dir, "stub"), source["stub"].encode("utf-8"), 0o644)
    pc_runroot.write_exclusive(os.path.join(wrapper_dir, "calls.log"), b"", 0o644)

    pc_runroot.exclusive_dir(ckpt, 0o700)
    pc_runroot.exclusive_dir(ledgers, 0o700)
    pc_runroot.write_exclusive(ledger_a, _real_ledger(_read(source["ledger_a"]), project), 0o644)
    pc_runroot.write_exclusive(ledger_b, _real_ledger(_read(source["ledger_b"]), project), 0o644)
    _run_stub(interpreter, source["stub"], project, ckpt, ["bind", "--ledger", ledger_b, "--session", session_id])

    pc_runroot.exclusive_dir(raw, 0o700)
    status = _run_stub(interpreter, source["stub"], project, ckpt, ["status", "--session", session_id])
    lint = _run_stub(interpreter, source["stub"], project, ckpt, ["lint"])
    pc_runroot.write_exclusive(os.path.join(raw, "status-before.txt"), status, 0o600)
    pc_runroot.write_exclusive(os.path.join(raw, "lint-before.txt"), lint, 0o600)

    pc_runroot.exclusive_dir(auto_memory, 0o700)
    pc_runroot.exclusive_dir(snaps, 0o700)
    command = " ".join(shlex.quote(part) for part in (interpreter, "-I", "-B", source["hooklog"], hooklog))
    rendered = pc_flags.render_settings(auto_memory, command)
    pc_runroot.write_exclusive(settings, (json.dumps(rendered, indent=2, sort_keys=True) + "\n").encode("utf-8"), 0o600)
    run_facts = {
        "row": ROW_ID,
        "model": model,
        "evidence_date": evidence_date,
        "session_id": session_id,
        "isolation": isolation_mode(),
    }
    pc_runroot.write_exclusive(
        os.path.join(raw, "run.json"), (json.dumps(run_facts, indent=2, sort_keys=True) + "\n").encode("utf-8"), 0o600
    )

    return {
        "run_root": root,
        "project": project,
        "skill_dir": skill_dir,
        "wrapper_dir": wrapper_dir,
        "wrapper": wrapper,
        "ckpt": ckpt,
        "ledgers": ledgers,
        "ledger_a": ledger_a,
        "ledger_b": ledger_b,
        "auto_memory": auto_memory,
        "raw": raw,
        "snaps": snaps,
        "settings": settings,
        "hooklog": hooklog,
    }


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
    """True for entries a boundary snapshot leaves out: raw, snaps, stage-prefixed folders, the project's .git."""
    top = path.split(b"/", 1)[0]
    if top in (b"raw", b"snaps") or top.startswith(b"stage"):
        return True
    return path == b"project/.git" or path.startswith(b"project/.git/")


def _sorted_names(names: Sequence[str]) -> List[str]:
    return sorted(names, key=os.fsencode)


def _listing(names: Sequence[str]) -> bytes:
    return "".join(name + "\n" for name in names).encode("utf-8", "surrogateescape")


def take_snapshot(
    paths: Mapping[str, Optional[str]],
    name: str,
    git: str,
    refuse_under: Sequence[str] = (),
) -> List[str]:
    """Write snaps/<name> and return the names of model-written trees whose copy was skipped.

    The folder holds sha.txt and manifest.jsonl of the run root (without raw, snaps, any stage-prefixed
    top-level folder and the project's .git), status.txt and status.raw from git status, ledgers-ls.txt and
    bindings-ls.txt, a copy of each ledger markdown file and, when present, copies of project/.preclear
    (as preclear) and the auto-memory folder (as auto-memory). A symlink or special file inside one of those
    two trees skips that one copy only; the manifest still lists the entry. A taken name is FileExistsError.
    """
    run_root = str(paths["run_root"])
    entries = [e for e in pc_manifest.tree_manifest(run_root, tuple(refuse_under)) if not _excluded(e["path"])]
    dest = os.path.join(str(paths["snaps"]), name)
    pc_manifest.write_snapshot(dest, entries)
    raw_status, text_status = pc_manifest.capture_git_status(str(paths["project"]), git)
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


def _row_stage_keys() -> Tuple[str, ...]:
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, ROW_ID)
    if entry is None:
        raise pc_spike.SpikeError("the row is not in the registry")
    return tuple(pc_rows.stage_key(ROW_ID, stage.name) for stage in entry.stages)


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


def _consistent(previous_total: Optional[Decimal], delta: Optional[Decimal], cumulative: Optional[Decimal]) -> str:
    """yes when the cumulative total equals the previous total plus this call's delta (to a millionth)."""
    if delta is None or cumulative is None:
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
) -> StageResult:
    """Run one stage: reserve its cap, run the process, settle the cost, keep the raw bytes, snapshot.

    The command is built only by pc_flags (build_argv, build_env, build_allowed_tools). The reservation is a
    pessimistic launch line written before the process; the settlement replaces it with the call's own cost
    (a timeout settles with no delta, so the cap stays counted). A stage is never started a second time: the
    ledger refuses a second launch. The stage record and the snapshot are written whatever the outcome.

    When the stream parses, the init manifest and the instruction audit are asserted for this stage on the hook
    log lines added since the previous stage boundary (hook_start is the line count that boundary recorded);
    the triples and the entry counts go into the stage record. scan is the cached binary lookup of the run.
    """
    tools = pc_flags.build_allowed_tools(str(paths["wrapper"]), pc_flags.MODEL_FACING_WRAPPER_VERBS)
    argv = pc_flags.build_argv(
        str(ctx.claude), session_id, str(paths["settings"]), tools, spec.max_turns, spec.cap, resume=resume, model=ctx.model
    )
    env = pc_flags.build_env(ctx.env, ctx.config_dir, str(paths["ckpt"]))
    key = pc_rows.stage_key(ROW_ID, spec.name)
    attempt = pc_spend.append_launch(ctx.harness_home, ROW_ID, key, spec.cap, ctx.version, _row_stage_keys())
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
    pc_spend.settle(ctx.harness_home, ROW_ID, key, attempt, subtype, delta, cumulative, ctx.version)

    problem = _classify(call, events, summary)
    snapshot = SNAPSHOT_NAMES[spec.name]
    vcs = _git_executable(ctx.env)
    skipped = take_snapshot(paths, snapshot, vcs)
    pc_checks.capture_boundary_state(paths, spec.name, vcs)
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
        "cumulative_consistent": _consistent(previous_total, delta, cumulative),
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

MESSAGE_DESTINATION = "REFUSED: the evidence folder already exists; a folder is never reused"
MESSAGE_SANITIZER = "FAIL: the sanitizer or the deny entries could not be built; nothing was spent"
_STOP_TEXT = {
    PROBLEM_TIMEOUT: "timed out",
    PROBLEM_EXIT: "exited with a non-zero status",
    PROBLEM_STREAM: "ended without a single result event",
    PROBLEM_SUBTYPE: "ended with a result that is not a success",
    PROBLEM_IS_ERROR: "reported an error in its result",
    PROBLEM_TERMINAL: "did not end as completed",
}


def _stopped(stage_name: str, problem: str) -> pc_rows.RowOutcome:
    code = pc_exitcodes.DENIAL_FOUND if problem == PROBLEM_STREAM else pc_exitcodes.PREFLIGHT_FAIL
    line = "FAIL: stage %s %s; the chain stopped and nothing was filed" % (stage_name, _STOP_TEXT[problem])
    return pc_rows.RowOutcome(code, (line,))


def _isolation_stop(stage_name: str, evaluation: Evaluation) -> pc_rows.RowOutcome:
    head = "FAIL: stage %s did not meet the isolation baseline; the chain stopped and nothing was filed" % stage_name
    return pc_rows.RowOutcome(
        pc_exitcodes.PREFLIGHT_FAIL, tuple([head] + describe_evaluation(stage_name, evaluation))
    )


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
    "FAIL: the mechanical checks could not read the run root; nothing is filed and the raw files stay in the run root"
)
MESSAGE_NOTHING_FILED = "nothing is filed; the raw files and snapshots stay in the run root"
_BREACH_TEXT = {
    pc_checks.BREACH_WRITES: "writes outside approved roots",
    pc_checks.BREACH_GIT: "git mutations",
}


def breach_outcome(ctx: pc_rows.RunContext, paths: Mapping[str, Optional[str]]) -> Optional[pc_rows.RowOutcome]:
    """Run the mechanical checks over the run root as it is on disk; a breach is exit 11 and files nothing.

    Only a concrete write outside the approved roots or a git mutation is a breach (HARN-09). Every other
    fact (denials, ledger changes, helper-call disagreement, Bash path mentions) is left for the reviewer.
    The lines hold counts and ids only, never a path. A run root the checks cannot read is a broken harness
    and is also exit 11, because a run whose isolation cannot be shown must not be filed.
    """
    try:
        facts = pc_checks.compute_facts(str(paths["run_root"]), ctx.config_dir)
    except pc_checks.CheckError:
        return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_CHECKS_UNREADABLE,))
    found = pc_checks.breaches(facts)
    if not found:
        return None
    lines = ["isolation or git breach: %s: %d" % (_BREACH_TEXT[name], count) for name, count in found]
    lines.append(MESSAGE_NOTHING_FILED)
    return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, tuple(lines))


def finish(
    ctx: pc_rows.RunContext, paths: Mapping[str, Optional[str]], results: Sequence[StageResult]
) -> pc_rows.RowOutcome:
    """Close a completed chain: the mechanical checks, one fixed line per stage, the filing and the row total.

    A breach found by the checks ends the row with 11 and prints counts only. When the checks find none, the row
    is filed through pc_evidence.file_row, the last step; a refusal of the filing is its exit code and its fixed
    lines (nothing more is printed), and the raw files stay in the run root for a zero-token refile.
    """
    blocked = breach_outcome(ctx, paths)
    if blocked is not None:
        return blocked
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
    if len(results) == 2:
        lines.append("stage s3: not run (%s)" % MARKER_NONE)
    filed = pc_evidence.file_row(ctx, str(paths["run_root"]))
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
    """Run row 1: refusals first, then seed, snapshot 0 and the stage chain (D-01, D-02, D-12, D-14).

    Order before any ledger line: an existing destination (17, nothing created), the run root (a taken name
    raises RunRootCollision, the driver's 16), the sanitizer and the deny entries (15, review WR-12), the
    readable ledger, the seed and the version control tool. Then s1 with a fresh session, s2 resumed on that
    session and s3 in a second fresh session whose prompt is the resume line, only when s2 printed one. The
    chain stops at the first stage that is not a clean success.
    """
    if os.path.lexists(ctx.destination):
        return pc_rows.RowOutcome(pc_exitcodes.PROMOTE_REFUSED, (MESSAGE_DESTINATION,))
    run_name = "%s-%s" % (ROW_ID, _utc_now().strftime("%Y%m%dT%H%M%SZ"))
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
    paths = seed_row1(ctx.repo_root, run_root, session, ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model)
    take_snapshot(paths, SNAPSHOT_SETUP, vcs)
    pc_checks.capture_boundary_state(paths, pc_checks.SETUP_STATE, vcs)
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, ROW_ID)
    if entry is None:
        raise pc_spike.SpikeError("the row is not in the registry")
    s1_prompt, s2_prompt = read_stage_prompts(ctx.repo_root, str(paths["ledger_a"]))

    results: List[StageResult] = []
    resume_line = ""
    scan = BinaryScan(str(ctx.claude))
    for stage in entry.stages:
        timeout = timeout_override if timeout_override is not None else stage.timeout
        boundary = results[-1].hooklog_lines if results else 0
        if stage.kind == "work":
            result = run_stage(ctx, paths, stage, session, s1_prompt, False, None, timeout, boundary, scan)
        elif stage.kind == "preclear":
            result = run_stage(
                ctx, paths, stage, session, s2_prompt, True, results[-1].cumulative, timeout, boundary, scan
            )
        else:
            if not resume_line:
                break
            second = str(uuid.uuid4())
            while second == session:
                second = str(uuid.uuid4())
            result = run_stage(ctx, paths, stage, second, resume_line, False, None, timeout, boundary, scan)
        results.append(result)
        blocked = breach_outcome(ctx, paths)
        if blocked is not None:
            extra = () if result.ok else _stopped(stage.name, result.problem).lines
            return pc_rows.RowOutcome(blocked.code, tuple(blocked.lines) + tuple(extra))
        if not result.ok:
            return _stopped(stage.name, result.problem)
        if result.evaluation is not None and result.evaluation.status != STATUS_PASS:
            return _isolation_stop(stage.name, result.evaluation)
        if stage.kind == "preclear":
            resume_line = extract_resume_line(_result_text(result))
            _write_chain(paths, resume_line)
    return finish(ctx, paths, results)
