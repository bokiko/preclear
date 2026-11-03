"""Seeds of registered rows: the committed setup of a helper-backed row in a fresh run root (plan 04-01; RERUN-02).

A row is defined by its registry entry alone; the seed an entry names builds the run root that row starts from.
This module holds the parameterised seed of the helper-backed rows (the row 1 body, moved out of pc_row1) and the
seeds that call it:

  * seed_helper_row   a scratch project (CLAUDE.md filled from a committed row's fixture, the three-step plan, a git
                      repository on main, the frozen skill as untracked files), the logging wrapper, the ledgers the
                      row asks for with the session bound to one of them or to none, the audit hook, the settings
                      file and raw/run.json (row, bound ledger, model, evidence date, session id, isolation mode)
  * seed_row1         the row 1 parameters: ledgers A and B, the session bound to B, the wrapper path absolute
  * seed_row4a        the row 4a parameters: ledger A only, the session bound to it, backend checkpoint-v2 and the
                      relative executable wrapper/checkpoint kept exactly as the committed fixture holds them
  * seed_plain_row    the setup of a row with no helper (plan 04-04): the committed project instruction file copied in
                      place, the plain plan, a repository on main with one commit, the skill copy, an empty ledgers
                      folder and no wrapper, no stub, no ledger and no binding; the settings follow the memory policy
  * seed_row5a, seed_row5b   the plain rows: the committed fixtures of rows 5a and 5b
  * seed_git_row     the plain setup with a chosen git shape (plan 04-09): commit (one commit on main), detached (two
                     commits, then a detached HEAD at the first), unborn (a repository on main with no commit), none (no
                     git at all) or worktree (the repository in main-checkout, the project a linked worktree on a
                     feature branch); seed_row8a, seed_row8b, seed_row8c, seed_row9 call it with the committed fixtures

Every file and folder is created exclusively through pc_runroot, so a second call on the same run root raises
FileExistsError; nothing here deletes, renames, moves or truncates, and this module is scanned for those primitives
like every other harness module. Messages are fixed text with repo-relative source names only, never a run path.

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from typing import Dict, Mapping, Optional, Sequence

import pc_flags
import pc_manifest
import pc_rows
import pc_runroot
import pc_spike

PUBLICATION_ROOT = "tests/evidence/publication-2026-10-20"
ROW1_FOLDER = PUBLICATION_ROOT + "/row1-wrong-binding"
ROW4A_FOLDER = PUBLICATION_ROOT + "/row4a-unknown-backend"
ROW5A_FOLDER = PUBLICATION_ROOT + "/row5a-no-memory"
ROW5B_FOLDER = PUBLICATION_ROOT + "/row5b-disabled-memory"
ROW6_FOLDER = PUBLICATION_ROOT + "/row6-readonly-plan"
ROW7_FOLDER = PUBLICATION_ROOT + "/row7-all-destinations-denied"
ROW8A_FOLDER = PUBLICATION_ROOT + "/row8a-non-git"
ROW8B_FOLDER = PUBLICATION_ROOT + "/row8b-detached-head"
ROW8C_FOLDER = PUBLICATION_ROOT + "/row8c-unborn-branch"
ROW9_FOLDER = PUBLICATION_ROOT + "/row9-linked-worktree"
DATA_DIR = "tests/harness/data"
PLAN_DATA = DATA_DIR + "/row1-plan.md"
PLAIN_PLAN_DATA = DATA_DIR + "/plain-plan.md"
LEDGER_A_NAME = "CONTINUITY_CLAUDE-widget-export.md"
LEDGER_B_NAME = "CONTINUITY_CLAUDE-other-task.md"
PLAN_NAME = "2026-10-15-widget-export.md"
TOKEN_PROJECT = "<repo>/<run>/project"
LEDGER_NAMES: Dict[str, str] = {"A": LEDGER_A_NAME, "B": LEDGER_B_NAME}
BOUND_NONE = "none"

# The git shapes of a plain project (plan 04-09). The harness identity of every commit is the pc_spike spike identity.
SHAPE_COMMIT = "commit"
SHAPE_DETACHED = "detached"
SHAPE_UNBORN = "unborn"
SHAPE_NONE = "none"
SHAPE_WORKTREE = "worktree"
GIT_SHAPES = (SHAPE_COMMIT, SHAPE_DETACHED, SHAPE_UNBORN, SHAPE_NONE, SHAPE_WORKTREE)
NOTES_NAME = "NOTES.md"
NOTES_TEXT = "Working notes for the widget exporter.\n\nThe consumer reads the export once a day.\n"
FEATURE_BRANCH = "feature/widget-export"
MAIN_CHECKOUT = "main-checkout"

# What a configuration value template may name; each token is replaced by the path the seed made.
TOKEN_WRAPPER = "$WRAPPER"
TOKEN_PROJECT_DIR = "$PROJECT"
TOKEN_LEDGER = "$LEDGER"
TOKEN_FALLBACK = "$FALLBACK"
DEFAULT_VALUES: Dict[str, str] = {
    "executable": TOKEN_WRAPPER,
    "project": TOKEN_PROJECT_DIR,
    "ledger": TOKEN_LEDGER,
    "fallback_directory": TOKEN_FALLBACK,
}

_STUB_TIMEOUT_SECONDS = 60
_ISOLATION_PREFIX = "Isolation claim: "
_LETTER = re.compile(r"[AB]\Z")


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


_SOURCE_FILES = (
    ("skill", "SKILL.md"),
    ("wrapper", "tests/harness/checkpoint-wrapper"),
    ("stub", "tests/harness/checkpoint_stub.py"),
    ("hooklog", "tests/harness/pc_hooklog.py"),
    ("plan", PLAN_DATA),
)
_SOURCE_DIRS = (
    ("references", "references"),
    ("fixture", "tests/fixtures/bound-ledger/project"),
)


def _sources(repo: str, fixture: str, ledger_sources: Mapping[str, str]) -> Dict[str, str]:
    """Return the absolute path of every seed source; a missing one is a SpikeError naming it repo-relative."""
    wanted = list(_SOURCE_FILES) + [("claude_md", fixture)]
    wanted.extend(("ledger_" + letter.lower(), relative) for letter, relative in sorted(ledger_sources.items()))
    found: Dict[str, str] = {}
    for key, relative in wanted:
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


def _filled_values(
    templates: Mapping[str, str], wrapper: str, project: str, ledger_a: Optional[str], fallback: str
) -> Dict[str, str]:
    """Fill the four configuration value templates; a token whose path was not made is a ValueError."""
    if set(templates) != set(DEFAULT_VALUES):
        raise ValueError("the configuration values must be exactly the four keys")
    paths = {
        TOKEN_WRAPPER: wrapper,
        TOKEN_PROJECT_DIR: project,
        TOKEN_LEDGER: ledger_a,
        TOKEN_FALLBACK: fallback,
    }
    filled: Dict[str, str] = {}
    for key, template in templates.items():
        text = template
        for token, path in paths.items():
            if token in text:
                if path is None:
                    raise ValueError("a configuration value names a ledger the seed does not make")
                text = text.replace(token, path)
        filled[key] = text
    return filled


def seed_helper_row(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
    row_id: str,
    fixture: str,
    ledger_sources: Mapping[str, str],
    bound: str,
    values: Optional[Mapping[str, str]] = None,
) -> Dict[str, Optional[str]]:
    """Build the setup of a helper-backed row inside the already-created run root and return its paths.

    row_id is a registry id. fixture is the repo-relative path of the committed fixture-CLAUDE.md. ledger_sources
    maps the ledger letter (A, the configured one, and B) to the repo-relative path of its committed copy; exactly
    those ledgers are created. bound is the letter of the ledger the session is bound to through the stub's own
    bind, or none. values holds a template for each of the four configuration keys (executable, project, ledger,
    fallback_directory) in which the tokens $WRAPPER, $PROJECT, $LEDGER (ledger A) and $FALLBACK stand for the
    paths made here; a template with no token is written as it is, so a relative executable stays relative.

    Everything is created exclusively, so a second call on the same run root raises FileExistsError. Created,
    in order: project, wrapper, ckpt (the ledgers and the binding), raw (the stub's status and lint output from
    before the first stage), auto-memory, snaps, settings.json and raw/run.json (row, bound ledger, model,
    evidence date, session id, isolation mode).
    """
    try:
        canonical = str(uuid.UUID(session_id))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("the session id must be a UUID") from None
    if canonical != session_id:
        raise ValueError("the session id must be the canonical lowercase form")
    if not pc_rows.is_valid_id(row_id):
        raise ValueError("the row id is not a registry id")
    letters = sorted(ledger_sources)
    if not letters or any(_LETTER.match(letter) is None for letter in letters):
        raise ValueError("the ledger letters must be A or B")
    if bound != BOUND_NONE and bound not in letters:
        raise ValueError("the session can be bound only to a ledger the seed makes")
    templates = dict(DEFAULT_VALUES if values is None else values)
    repo = os.path.realpath(repo_root)
    root = os.path.realpath(run_root)
    runs = os.path.realpath(runs_dir)
    if not os.path.isdir(root):
        raise ValueError("the run root does not exist")
    if not _within(root, runs) or root == runs:
        raise ValueError("the run root must lie under the runs folder")
    if _within(root, repo):
        raise ValueError("the run root must be outside the repository")
    source = _sources(repo, fixture, ledger_sources)
    interpreter = os.path.realpath(sys.executable)
    if not interpreter:
        raise ValueError("no interpreter path is known")

    project = os.path.join(root, "project")
    wrapper_dir = os.path.join(root, "wrapper")
    wrapper = os.path.join(wrapper_dir, "checkpoint")
    ckpt = os.path.join(root, "ckpt")
    ledgers = os.path.join(ckpt, "ledgers")
    ledger_paths = dict((letter, os.path.join(ledgers, LEDGER_NAMES[letter])) for letter in LEDGER_NAMES)
    auto_memory = os.path.join(root, "auto-memory")
    raw = os.path.join(root, "raw")
    snaps = os.path.join(root, "snaps")
    settings = os.path.join(root, "settings.json")
    hooklog = os.path.join(raw, "hooklog.jsonl")
    filled = _filled_values(
        templates,
        wrapper,
        project,
        ledger_paths["A"] if "A" in letters else None,
        os.path.join(project, ".preclear"),
    )

    _copy_fixture_project(source["fixture"], project)
    thoughts = os.path.join(project, "thoughts")
    if not os.path.isdir(thoughts):
        pc_runroot.exclusive_dir(thoughts, 0o700)
    plans = os.path.join(thoughts, "plans")
    pc_runroot.exclusive_dir(plans, 0o700)
    pc_runroot.write_exclusive(os.path.join(plans, PLAN_NAME), _read(source["plan"]), 0o644)
    configuration = pc_spike._fill_configuration(_read(source["claude_md"]).decode("utf-8"), filled)
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
    for letter in letters:
        pc_runroot.write_exclusive(
            ledger_paths[letter], _real_ledger(_read(source["ledger_" + letter.lower()]), project), 0o644
        )
    if bound != BOUND_NONE:
        _run_stub(
            interpreter, source["stub"], project, ckpt, ["bind", "--ledger", ledger_paths[bound], "--session", session_id]
        )

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
        "row": row_id,
        "bound_ledger": bound,
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
        "ledger_a": ledger_paths["A"],
        "ledger_b": ledger_paths["B"],
        "auto_memory": auto_memory,
        "raw": raw,
        "snaps": snaps,
        "settings": settings,
        "hooklog": hooklog,
    }


def seed_row1(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 1 setup: the configuration names ledger A, the session is bound to ledger B (the wrong binding)."""
    return seed_helper_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW1,
        ROW1_FOLDER + "/fixture-CLAUDE.md",
        {
            "A": ROW1_FOLDER + "/snap-0-setup/" + LEDGER_A_NAME,
            "B": ROW1_FOLDER + "/snap-0-setup/" + LEDGER_B_NAME,
        },
        "B",
    )


def seed_row4a(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 4a setup: one ledger bound to the session, an unknown backend and a relative executable.

    The committed fixture names backend checkpoint-v2 and the executable wrapper/checkpoint; the executable value
    is a template with no token, so it is written exactly as committed, and only project, ledger and
    fallback_directory take the paths of this run root.
    """
    return seed_helper_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW4A,
        ROW4A_FOLDER + "/fixture-CLAUDE.md",
        {"A": ROW4A_FOLDER + "/snap-0-setup/" + LEDGER_A_NAME},
        "A",
        values={
            "executable": "wrapper/checkpoint",
            "project": TOKEN_PROJECT_DIR,
            "ledger": TOKEN_LEDGER,
            "fallback_directory": TOKEN_FALLBACK,
        },
    )



def _memory_policy(row_id: str) -> str:
    """The memory policy word of a registry entry, taken from the entry and never typed in a seed."""
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id)
    if entry is None or entry.memory not in (pc_rows.MEMORY_PINNED, pc_rows.MEMORY_DISABLED):
        raise ValueError("the row has no known memory policy")
    return entry.memory


def _write_plain_files(base: str, source: Mapping[str, str]) -> None:
    """Create BASE and write the project instruction file (byte for byte) and the plain plan into it."""
    pc_runroot.exclusive_dir(base, 0o700)
    thoughts = os.path.join(base, "thoughts")
    pc_runroot.exclusive_dir(thoughts, 0o700)
    plans = os.path.join(thoughts, "plans")
    pc_runroot.exclusive_dir(plans, 0o700)
    pc_runroot.write_exclusive(os.path.join(plans, PLAN_NAME), _read(source["plan"]), 0o644)
    pc_runroot.write_exclusive(os.path.join(base, "CLAUDE.md"), _read(source["claude_md"]), 0o644)


def _init_on_main(folder: str) -> None:
    pc_spike._run_git(folder, ["init", "-q"])
    pc_spike._run_git(folder, ["symbolic-ref", "HEAD", "refs/heads/main"])


def _commit_all(folder: str, message: str) -> None:
    pc_spike._run_git(folder, ["add", "-A"])
    pc_spike._run_git(folder, ["-c", "commit.gpgsign=false", "commit", "-q", "-m", message])


def _build_plain_project(shape: str, root: str, project: str, source: Mapping[str, str]) -> None:
    """Make the project of a plain row in the git shape named by SHAPE (the skill copy is added by the caller).

    commit: the files and one commit on main. detached: two commits (the second adds NOTES.md), then the work tree is
    switched to the first with a detached HEAD, so NOTES.md is absent. unborn: a repository on main with no commit.
    none: the files and no git at all. worktree: the repository in main-checkout with the files committed on main, and
    the project a linked worktree on the feature branch made by git worktree add -b into the (empty) project folder.
    Every path lies inside the run root; the harness git identity is the spike identity.
    """
    if shape == SHAPE_WORKTREE:
        main_checkout = os.path.join(root, MAIN_CHECKOUT)
        _write_plain_files(main_checkout, source)
        _init_on_main(main_checkout)
        _commit_all(main_checkout, "Initial fixture commit")
        pc_runroot.exclusive_dir(project, 0o700)
        pc_spike._run_git(main_checkout, ["worktree", "add", "-q", "-b", FEATURE_BRANCH, project])
        return
    _write_plain_files(project, source)
    if shape == SHAPE_NONE:
        return
    _init_on_main(project)
    if shape == SHAPE_UNBORN:
        return
    _commit_all(project, "Initial fixture commit")
    if shape == SHAPE_DETACHED:
        pc_runroot.write_exclusive(os.path.join(project, NOTES_NAME), NOTES_TEXT.encode("utf-8"), 0o644)
        _commit_all(project, "Add working notes")
        pc_spike._run_git(project, ["checkout", "-q", "--detach", "HEAD~1"])


def seed_plain_row(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
    row_id: str,
    fixture: str,
    memory: str,
    shape: str = SHAPE_COMMIT,
) -> Dict[str, Optional[str]]:
    """Build the setup of a row with no helper inside the already-created run root and return its paths.

    shape is the git shape of the project (SHAPE_COMMIT, the default and the only one of rows 5a to 7, or one of
    the others of GIT_SHAPES; see _build_plain_project).

    fixture is the repo-relative path of the committed fixture-CLAUDE.md of the row; it is copied byte for byte (a
    plain row has no configuration block to fill). The plan is the plain plan data file. memory is the row's memory
    policy word: the settings carry autoMemoryEnabled false for MEMORY_DISABLED and true for MEMORY_PINNED, and the
    auto-memory directory is pinned inside the run root in both cases.

    Created exclusively, in order: project (CLAUDE.md, the plan, a repository on main with one commit, then the
    skill copy as untracked files), ckpt with an empty ledgers folder (the child's environment still names ckpt;
    nothing writes a ledger or a binding there), raw (run.json: row, bound ledger none, memory, model, evidence date,
    session id, isolation mode), auto-memory, snaps and settings.json. There is no wrapper folder and no stub: the
    returned mapping still names wrapper, wrapper_dir and the two ledger paths, as folders and files that do not
    exist, so paths_for and the checks need no second shape.
    """
    try:
        canonical = str(uuid.UUID(session_id))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("the session id must be a UUID") from None
    if canonical != session_id:
        raise ValueError("the session id must be the canonical lowercase form")
    if not pc_rows.is_valid_id(row_id):
        raise ValueError("the row id is not a registry id")
    if memory not in (pc_rows.MEMORY_PINNED, pc_rows.MEMORY_DISABLED):
        raise ValueError("the memory policy is not known")
    if shape not in GIT_SHAPES:
        raise ValueError("the git shape is not known")
    repo = os.path.realpath(repo_root)
    root = os.path.realpath(run_root)
    runs = os.path.realpath(runs_dir)
    if not os.path.isdir(root):
        raise ValueError("the run root does not exist")
    if not _within(root, runs) or root == runs:
        raise ValueError("the run root must lie under the runs folder")
    if _within(root, repo):
        raise ValueError("the run root must be outside the repository")
    wanted = (
        ("skill", "SKILL.md"),
        ("hooklog", "tests/harness/pc_hooklog.py"),
        ("plan", PLAIN_PLAN_DATA),
        ("claude_md", fixture),
    )
    source: Dict[str, str] = {}
    for key, relative in wanted:
        path = os.path.join(repo, *relative.split("/"))
        if not os.path.isfile(path):
            raise pc_spike.SpikeError("a source the run root needs is missing: %s" % relative)
        source[key] = path
    references = os.path.join(repo, "references")
    if not os.path.isdir(references):
        raise pc_spike.SpikeError("a source the run root needs is missing: references")
    interpreter = os.path.realpath(sys.executable)
    if not interpreter:
        raise ValueError("no interpreter path is known")

    project = os.path.join(root, "project")
    wrapper_dir = os.path.join(root, "wrapper")
    ckpt = os.path.join(root, "ckpt")
    ledgers = os.path.join(ckpt, "ledgers")
    auto_memory = os.path.join(root, "auto-memory")
    raw = os.path.join(root, "raw")
    snaps = os.path.join(root, "snaps")
    settings = os.path.join(root, "settings.json")
    hooklog = os.path.join(raw, "hooklog.jsonl")

    _build_plain_project(shape, root, project, source)

    skill_dir = os.path.join(project, ".claude", "skills", "preclear")
    pc_runroot.exclusive_dir(os.path.join(project, ".claude"), 0o700)
    pc_runroot.exclusive_dir(os.path.join(project, ".claude", "skills"), 0o700)
    pc_runroot.exclusive_dir(skill_dir, 0o700)
    pc_runroot.write_exclusive(os.path.join(skill_dir, "SKILL.md"), _read(source["skill"]), 0o644)
    pc_spike._copy_tree_with(references, os.path.join(skill_dir, "references"))

    pc_runroot.exclusive_dir(ckpt, 0o700)
    pc_runroot.exclusive_dir(ledgers, 0o700)
    pc_runroot.exclusive_dir(raw, 0o700)
    pc_runroot.exclusive_dir(auto_memory, 0o700)
    pc_runroot.exclusive_dir(snaps, 0o700)
    command = " ".join(shlex.quote(part) for part in (interpreter, "-I", "-B", source["hooklog"], hooklog))
    rendered = pc_flags.render_settings(auto_memory, command, memory == pc_rows.MEMORY_PINNED)
    pc_runroot.write_exclusive(settings, (json.dumps(rendered, indent=2, sort_keys=True) + "\n").encode("utf-8"), 0o600)
    run_facts = {
        "row": row_id,
        "bound_ledger": BOUND_NONE,
        "memory": memory,
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
        "wrapper": os.path.join(wrapper_dir, "checkpoint"),
        "ckpt": ckpt,
        "ledgers": ledgers,
        "ledger_a": os.path.join(ledgers, LEDGER_A_NAME),
        "ledger_b": os.path.join(ledgers, LEDGER_B_NAME),
        "auto_memory": auto_memory,
        "raw": raw,
        "snaps": snaps,
        "settings": settings,
        "hooklog": hooklog,
    }


def seed_row5a(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 5a setup: a plain project (no configuration block, no memory text), auto-memory disabled."""
    return seed_plain_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW5A,
        ROW5A_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW5A),
    )


def seed_row5b(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 5b setup: as row 5a, the project instruction file says memory is disabled."""
    return seed_plain_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW5B,
        ROW5B_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW5B),
    )


def seed_row6(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 6 setup: a plain project with memory enabled and pinned and the canonical plan (644 until the hook).

    The project instruction file is the committed row 6 fixture, copied byte for byte; its digest is the one rows 6 to
    12 share. The restriction itself is not part of the seed: the engine applies the between-stage hook of the entry
    after the work turn (pc_rowhooks).
    """
    return seed_plain_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW6,
        ROW6_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW6),
    )


def seed_row7(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 7 setup: a plain project with memory enabled and pinned and the canonical plan.

    The project instruction file is the committed row 7 fixture, copied byte for byte (its digest is the one rows 6 to
    12 share). The restriction itself is not part of the seed: the engine applies the between-stage hook of the entry
    after the work turn (pc_rowhooks), and the live probe runs before the first snapshot (pc_rowhooks.chmod_denial_probe).
    """
    return seed_plain_row(
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW7,
        ROW7_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW7),
    )


# The shapes implemented so far by seed_git_row; the others raise ValueError.
_GIT_ROW_SHAPES = (SHAPE_COMMIT, SHAPE_DETACHED, SHAPE_UNBORN, SHAPE_NONE)


def seed_git_row(
    shape: str,
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
    row_id: str,
    fixture: str,
    memory: str,
) -> Dict[str, Optional[str]]:
    """The plain setup of a git-shaped row (plan 04-09): seed_plain_row with the git shape named by SHAPE.

    The project instruction file is the committed fixture of the row, copied byte for byte; the plan is the plain plan.
    A shape this module does not build yet is a ValueError, and so is any word outside GIT_SHAPES.
    """
    if shape not in GIT_SHAPES or shape not in _GIT_ROW_SHAPES:
        raise ValueError("the git shape is not known")
    return seed_plain_row(
        repo_root, run_root, session_id, harness_home_dir, runs_dir, evidence_date, model, row_id, fixture, memory, shape
    )


def seed_row8b(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 8b setup: two commits on main, then the work tree switched to the first one with a detached HEAD."""
    return seed_git_row(
        SHAPE_DETACHED,
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW8B,
        ROW8B_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW8B),
    )


def seed_row8c(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 8c setup: a repository on main with no commit, so every file of the project is untracked."""
    return seed_git_row(
        SHAPE_UNBORN,
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW8C,
        ROW8C_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW8C),
    )


def seed_row8a(
    repo_root: str,
    run_root: str,
    session_id: str,
    harness_home_dir: str,
    runs_dir: str,
    evidence_date: str,
    model: str,
) -> Dict[str, Optional[str]]:
    """The row 8a setup: a plain project with no .git entry at all (and no repository above the run root).

    The committed run sat under a gitignored folder of this repository, so an enclosing repository existed two levels
    up; this run root lies under the harness runs root, which holds no repository. That is stricter in one way and
    looser in another than the committed run, and the row's Setup paragraph says so.
    """
    return seed_git_row(
        SHAPE_NONE,
        repo_root,
        run_root,
        session_id,
        harness_home_dir,
        runs_dir,
        evidence_date,
        model,
        pc_rows.ROW8A,
        ROW8A_FOLDER + "/fixture-CLAUDE.md",
        _memory_policy(pc_rows.ROW8A),
    )
