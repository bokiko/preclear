"""Row and layout registry for the matrix driver (HARN-01, D-12, D-14).

One place says which layouts and rows exist, in the order the acceptance document runs them,
which of them this phase implements, and what each stage of an implemented row may cost:

  * ROW_IDS, LAYOUT_IDS   the eighteen row ids (the committed evidence folder names with the
                          rerun and first-pass suffixes collapsed) and the three layouts
  * StageSpec, RowSpec    one stage (turns, cap as Decimal, session key) and one registry entry; an entry
                          also carries what makes a row runnable from the registry alone (plan 04-01): the
                          seed it names, the prompt files of its stages, the Setup paragraph of its README and
                          its allowlist profile with the extra rules it adds and its memory policy (plan 04-04)
  * RunContext, RowOutcome  the records the driver hands to a row runner and gets back
  * build_registry        the full registry, plus any rows a test injects
  * find_entry            exact, whole-id lookup; a prefix, another case or an odd value is None
  * worst_case, session_count, stage_key, evidence_folder_name
  * campaign and attempt scoping (plan 04-02): is_valid_campaign, scoped_row, scoped_stage_key, row_folder_name

Every cap is a Decimal; no float appears here. An id reaches a path only after it has matched a
registry entry exactly. Standard library only, Python 3.9 floor, no process, no file access.
"""
from __future__ import annotations

import datetime
import re
from decimal import Decimal
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

ROW_CAP = Decimal("2.00")  # D-12: the most one row may cost, in US dollars
ROW1 = "row1-wrong-binding"
ROW4A = "row4a-unknown-backend"
ROW5A = "row5a-no-memory"
ROW5B = "row5b-disabled-memory"
ROW6 = "row6-readonly-plan"
ROW7 = "row7-all-destinations-denied"
ROW8A = "row8a-non-git"
ROW8B = "row8b-detached-head"
ROW8C = "row8c-unborn-branch"
ROW9 = "row9-linked-worktree"
ROW10 = "row10-large-status"

# Allowlist profiles (RowSpec.tools_profile). PROFILE_HELPER is the committed 33-rule baseline plus one rule per
# model-facing verb of the logging wrapper; the runner and the filing turn the word into rules, never this module.
PROFILE_HELPER = "helper"
# PROFILE_PLAIN is the baseline alone (no wrapper rule of any kind); a row adds its own extra rules in RowSpec.extra_tools.
PROFILE_PLAIN = "plain"
# PROFILE_GIT is the baseline alone as well, with no extra rule: the git-shaped rows 8a to 10 need neither chmod nor touch
# (plans 04-09 and 04-10). It is a separate word so a row's registry entry says which family it belongs to.
PROFILE_GIT = "git"

# Memory policies (RowSpec.memory): what the run settings say about Claude Code's auto-memory. In both the directory is
# pinned inside the run root. MEMORY_PINNED is the Phase 3 setting (on); MEMORY_DISABLED turns it off (rows 5a and 5b).
MEMORY_PINNED = "pinned"
MEMORY_DISABLED = "disabled"

# Chain strategies (RowSpec.chain): how the stage of kind resume gets its prompt. CHAIN_RESUME_LINE is the Phase 3 rule
# (the fenced `Resume ...` line the /preclear turn printed, marker found or NO-RESUME-LINE). CHAIN_PRINTED_CHECKPOINT is
# row 7's (a row that could save no file prints no resume line): the last fenced block of the /preclear reply that holds
# both required headings, marker found or NO-PRINTED-CHECKPOINT (plan 04-06).
CHAIN_RESUME_LINE = "resume-line"
CHAIN_PRINTED_CHECKPOINT = "printed-checkpoint"

# Live probes (RowSpec.probe): a named check the row runner makes after the seed and before any spend. The empty word is
# no probe. PROBE_CHMOD proves that a folder at mode 555 refuses a create on the machine that runs the row (plan 04-06).
PROBE_NONE = ""
PROBE_CHMOD = "chmod-denial"

# Analyses (RowSpec.analyses): named, model-free readings of a finished chain that filing adds to the row folder
# (pc_review.ANALYSES holds the functions). Row 7 files its facts and the Do-not-redo candidates (plan 04-07).
ANALYSIS_ROW7_FACTS = "row7-facts"
ANALYSIS_DO_NOT_REDO = "do-not-redo"
ROW7_ANALYSES: Tuple[str, ...] = (ANALYSIS_ROW7_FACTS, ANALYSIS_DO_NOT_REDO)
# Row 10 counts, from the stream and the filed sidecar copy, how the status was read (plan 04-10; HARN-10).
ANALYSIS_STATUS_FORM = "status-form"
ROW10_ANALYSES: Tuple[str, ...] = (ANALYSIS_STATUS_FORM,)

LAYOUT_IDS: Tuple[str, ...] = ("plain-memory", "hub-memory", "bound-ledger")

# The acceptance order of the twelve publication cases (tests/acceptance.md, Publication matrix).
ROW_IDS: Tuple[str, ...] = (
    "row1-wrong-binding",
    "row2-double-conflict",
    "row3a-missing-executable",
    "row3b-denied-helper-write",
    "row3c-unbound-fallback-none",
    "row4a-unknown-backend",
    "row4b-conflicting-blocks",
    "row5a-no-memory",
    "row5b-disabled-memory",
    "row6-readonly-plan",
    "row7-all-destinations-denied",
    "row8a-non-git",
    "row8b-detached-head",
    "row8c-unborn-branch",
    "row9-linked-worktree",
    "row10-large-status",
    "row11-concurrent-change",
    "row12-frozen-handoff",
)

MAX_ID_LENGTH = 64
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

# Campaign labels and attempts (plan 04-02). A label is one lower-case id of at most 24 characters. The words a1 to a9
# are the attempt scope of a ledger id, so no label may hold one as a whole hyphen-separated part: that would let a
# label such as wave-a2 build the same ledger id as the label wave on its second attempt (T-04-08).
CAMPAIGN_PATTERN = ID_PATTERN
MAX_CAMPAIGN_LENGTH = 24
MAX_ATTEMPT = 9
MATRIX_SCOPE = "matrix"
_ATTEMPT_WORD = re.compile(r"a[1-9]\Z")
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_MODEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
MAX_MODEL_LENGTH = 64

KIND_ROW = "row"
KIND_LAYOUT = "layout"

# What a stage does: the word printed in the plan and the kind the stage runner switches on.
WORK_TURN = "work turn"
PRECLEAR_TURN = "/preclear turn"
FRESH_RESUME = "fresh resume"


class StageSpec(NamedTuple):
    """One claude -p call of a row: its turn limit, its cap and the session it uses."""

    name: str  # s1, s2, s3
    work: str  # WORK_TURN, PRECLEAR_TURN or FRESH_RESUME
    kind: str  # work, preclear or resume
    max_turns: int
    cap: Decimal
    timeout: int  # seconds the stage runner waits for the process
    session: str  # new:A starts a session, resume:A continues it, new:B starts another


class RowSpec(NamedTuple):
    """One registry entry: a layout or a row, implemented or only listed."""

    row_id: str
    kind: str  # KIND_ROW or KIND_LAYOUT
    title: str
    stages: Tuple[StageSpec, ...]
    implemented: bool
    precondition: Optional[Callable[[], Optional[str]]]  # a reason when the row must be skipped
    runner: Any  # "module:function" resolved lazily, a callable (tests), or None
    sources: Tuple[Tuple[str, str], ...]  # (repo-relative path, "file" or "dir")
    seed: Any = None  # "module:function" resolved lazily, a callable, or None; builds the run root of the row
    prompts: Tuple[Tuple[str, str], ...] = ()  # (stage name, repo-relative path) of the prompt file of a stage
    setup_text: str = ""  # the harness-authored Setup paragraph of the row README
    tools_profile: str = PROFILE_HELPER  # which allowlist the stages run with
    extra_tools: Tuple[str, ...] = ()  # rules appended to the profile's list, in order (plan 04-04)
    memory: str = MEMORY_PINNED  # MEMORY_PINNED or MEMORY_DISABLED: the memory switch of the run settings
    hooks: Tuple[Tuple[str, str], ...] = ()  # (stage name, hook id) pairs: a hook runs after that stage (plan 04-05)
    chain: str = CHAIN_RESUME_LINE  # CHAIN_RESUME_LINE or CHAIN_PRINTED_CHECKPOINT: what feeds the resume stage (plan 04-06)
    probe: str = PROBE_NONE  # a live probe id the runner makes before any spend, or PROBE_NONE (plan 04-06)
    analyses: Tuple[str, ...] = ()  # ids of pc_review.ANALYSES that filing runs for a completed chain (plan 04-07)


class RunContext(NamedTuple):
    """Everything a row runner needs; run_root, sanitizer, deny_entries and setup_pin are filled by the runner."""

    repo_root: str
    env: Dict[str, str]
    claude: Optional[str]
    harness_home: str
    config_dir: str
    runs_root: str
    run_root: Optional[str]
    destination: str
    evidence_date: str
    model: str
    sanitizer: Any
    deny_entries: Any
    budget: Decimal
    banner: Optional[str]
    version: Optional[str]
    setup_pin: Optional[str] = None  # the gitdir digest at setup, held in memory by the runner (third-pass WR-02)
    campaign: Optional[str] = None  # the validated campaign label of this invocation, or None
    attempt: int = 1  # 1 to MAX_ATTEMPT; above 1 only for one explicitly selected row (a retry)
    matrix: bool = False  # True for --all without a campaign: the ledger scope is the word matrix


class RowOutcome(NamedTuple):
    """What a row runner returns: an exit code and the fixed-text lines to print.

    spent is what the row settled in the spend ledger (a Decimal), or None when the runner does not report it; the
    driver treats None as nothing spent and uses the figure for its per-invocation budget (plan 04-02).
    """

    code: int
    lines: Tuple[str, ...]
    spent: Optional[Decimal] = None


_ROW1_STAGES: Tuple[StageSpec, ...] = (
    StageSpec("s1", WORK_TURN, "work", 15, Decimal("0.30"), 900, "new:A"),
    StageSpec("s2", PRECLEAR_TURN, "preclear", 60, Decimal("1.30"), 1800, "resume:A"),
    StageSpec("s3", FRESH_RESUME, "resume", 15, Decimal("0.40"), 900, "new:B"),
)

_PUBLICATION_ROOT = "tests/evidence/publication-2026-10-20"
_PUBLICATION = _PUBLICATION_ROOT + "/row1-wrong-binding"
_PUBLICATION_4A = _PUBLICATION_ROOT + "/row4a-unknown-backend"
_S1_PROMPT = "tests/harness/data/row1-s1-prompt.md"
_PLAN_DATA = "tests/harness/data/row1-plan.md"
_COMMON_SOURCES: Tuple[Tuple[str, str], ...] = (
    ("SKILL.md", "file"),
    ("references", "dir"),
    ("tests/harness/checkpoint-wrapper", "file"),
    ("tests/harness/checkpoint_stub.py", "file"),
    ("tests/harness/pc_hooklog.py", "file"),
)
_ROW1_SOURCES: Tuple[Tuple[str, str], ...] = _COMMON_SOURCES + (
    (_PUBLICATION + "/fixture-CLAUDE.md", "file"),
    (_PUBLICATION + "/s2-preclear-prompt.md", "file"),
    (_PUBLICATION + "/snap-0-setup/CONTINUITY_CLAUDE-other-task.md", "file"),
    (_PUBLICATION + "/snap-0-setup/CONTINUITY_CLAUDE-widget-export.md", "file"),
    ("tests/fixtures/bound-ledger/project", "dir"),
    (_S1_PROMPT, "file"),
    (_PLAN_DATA, "file"),
)

_ROW1_PROMPTS: Tuple[Tuple[str, str], ...] = (
    ("s1", _S1_PROMPT),
    ("s2", _PUBLICATION + "/s2-preclear-prompt.md"),
)

# Row 4a (unknown backend): the committed two stages, one ledger bound to the session, no between-stage hook.
_ROW4A_STAGES: Tuple[StageSpec, ...] = (
    StageSpec("s1", WORK_TURN, "work", 15, Decimal("0.30"), 900, "new:A"),
    StageSpec("s2", PRECLEAR_TURN, "preclear", 60, Decimal("1.30"), 1800, "resume:A"),
)
_ROW4A_SOURCES: Tuple[Tuple[str, str], ...] = _COMMON_SOURCES + (
    (_PUBLICATION_4A + "/fixture-CLAUDE.md", "file"),
    (_PUBLICATION_4A + "/s2-preclear-prompt.md", "file"),
    (_PUBLICATION_4A + "/snap-0-setup/CONTINUITY_CLAUDE-widget-export.md", "file"),
    ("tests/fixtures/bound-ledger/project", "dir"),
    (_S1_PROMPT, "file"),
    (_PLAN_DATA, "file"),
)
_ROW4A_PROMPTS: Tuple[Tuple[str, str], ...] = (
    ("s1", _S1_PROMPT),
    ("s2", _PUBLICATION_4A + "/s2-preclear-prompt.md"),
)

# Rows 5a and 5b (plain rows: no wrapper, no ledger, no binding): the committed two stages, auto-memory disabled.
_PUBLICATION_5A = _PUBLICATION_ROOT + "/row5a-no-memory"
_PUBLICATION_5B = _PUBLICATION_ROOT + "/row5b-disabled-memory"
_PLAIN_PLAN_DATA = "tests/harness/data/plain-plan.md"
_PLAIN_S1_PROMPT = "tests/harness/data/plain-s1-prompt.md"
_PLAIN_EXTRA_TOOLS: Tuple[str, ...] = ("Bash(chmod:*)", "Bash(touch:*)")
_ROW5_STAGES: Tuple[StageSpec, ...] = (
    StageSpec("s1", WORK_TURN, "work", 15, Decimal("0.30"), 900, "new:A"),
    StageSpec("s2", PRECLEAR_TURN, "preclear", 60, Decimal("1.30"), 1800, "resume:A"),
)
_PLAIN_COMMON_SOURCES: Tuple[Tuple[str, str], ...] = (
    ("SKILL.md", "file"),
    ("references", "dir"),
    ("tests/harness/pc_hooklog.py", "file"),
)


def _plain_sources(folder: str) -> Tuple[Tuple[str, str], ...]:
    return _PLAIN_COMMON_SOURCES + (
        (folder + "/fixture-CLAUDE.md", "file"),
        (folder + "/s2-preclear-prompt.md", "file"),
        (_PLAIN_S1_PROMPT, "file"),
        (_PLAIN_PLAN_DATA, "file"),
    )


def _plain_prompts(folder: str) -> Tuple[Tuple[str, str], ...]:
    return (("s1", _PLAIN_S1_PROMPT), ("s2", folder + "/s2-preclear-prompt.md"))


_ROW5A_SETUP_TEXT = (
    "Setup: a plain project with no configuration block and no memory mentioned anywhere in it, no helper wrapper "
    "and no ledger. Claude Code auto-memory is switched off in the run settings, with its directory still pinned "
    "inside the run root so that a stray write would land there. A work turn comes first, then the /preclear turn "
    "with the JSON-default correction in the same session; no fresh session follows."
)
_ROW5B_SETUP_TEXT = (
    "Setup: as row 5a, plus the project instruction file says that memory is disabled for this project and tells "
    "the session not to create or write memory files anywhere; durable facts go in the plan or the checkpoint. "
    "Auto-memory is also switched off in the run settings, with its directory pinned inside the run root. A work "
    "turn comes first, then the /preclear turn with the JSON-default correction in the same session; no fresh "
    "session follows."
)
# Row 6 (read-only plan): the committed two stages; the plan file is made read-only by the harness after s1.
_PUBLICATION_6 = _PUBLICATION_ROOT + "/row6-readonly-plan"
_ROW6_HOOKS: Tuple[Tuple[str, str], ...] = (("s1", "restrict-plan-444"),)
_ROW6_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. "
    "A work turn comes first. After it the harness sets the plan file to mode 444 and takes an extra snapshot "
    "(`snap-1b-after-restriction`, with a mode-only `perms.txt`); the /preclear turn then asks for a plan update in "
    "the same session. The harness sets the plan file back to mode 644 after the last snapshot and before filing."
)
# Row 7 (all destinations denied): the committed three stages; the project folder is made read-only by the harness after
# s1 and the third stage is a fresh session fed with the checkpoint the /preclear reply printed.
_PUBLICATION_7 = _PUBLICATION_ROOT + "/row7-all-destinations-denied"
_ROW7_HOOKS: Tuple[Tuple[str, str], ...] = (("s1", "restrict-project-555"),)
_ROW7_STAGES: Tuple[StageSpec, ...] = _ROW1_STAGES
_ROW7_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger, and "
    "no established handoff location. Before any session the harness proves on this machine that a folder at mode 555 "
    "refuses a new file; a machine where it does not is filed as skipped and no session runs. A work turn comes "
    "first. After it the harness sets the project folder to mode 555, so that no checkpoint file can be saved, and "
    "takes an extra snapshot (`snap-1b-after-restriction`, with a mode-only `perms.txt`); the /preclear turn then runs "
    "in the same session. A fresh session then receives the checkpoint the /preclear reply printed, taken verbatim, "
    "and the restriction stays in place through it. The harness sets the project folder back to mode 755 after the "
    "last snapshot and before filing."
)


def _chmod_precondition() -> Optional[str]:
    """The row 7 precondition, resolved lazily so this module imports nothing heavy (write-free; plan 04-06)."""
    import pc_rowhooks  # imported late: pc_rowhooks imports this module

    return pc_rowhooks.chmod_precondition()


# Rows 8a, 8b, 8c and 9 (git-shaped rows, plan 04-09): the committed three stages of row 1 with the resume-line chain, the
# baseline allowlist alone (no wrapper, no extra rule) and memory pinned. Only the git shape the seed builds differs.
_PUBLICATION_8A = _PUBLICATION_ROOT + "/row8a-non-git"
_PUBLICATION_8B = _PUBLICATION_ROOT + "/row8b-detached-head"
_PUBLICATION_8C = _PUBLICATION_ROOT + "/row8c-unborn-branch"
_PUBLICATION_9 = _PUBLICATION_ROOT + "/row9-linked-worktree"
# Row 10 (large status, plan 04-10) reads the committed rerun folder: its s2 prompt and fixture are the ones of the corrected
# allowlist; the first pass is not the reference.
_PUBLICATION_10 = _PUBLICATION_ROOT + "/row10-large-status-rerun"
_GIT_ROW_STAGES: Tuple[StageSpec, ...] = _ROW1_STAGES
_ROW8A_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger, and no "
    "git repository at all: the project folder holds no `.git` entry, and the run root lies under no repository either, "
    "which differs from the committed run (that one sat inside an enclosing repository two levels up). A work turn comes "
    "first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the "
    "/preclear turn printed. The harness reads the git state of this project as not applicable and starts no git "
    "process for it."
)
_ROW8B_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The "
    "repository holds two commits on main, the second adding `NOTES.md`; before the work turn the work tree is switched "
    "to the first commit with a detached HEAD, so `NOTES.md` is absent. A work turn comes first, then the /preclear "
    "turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed."
)
_ROW8C_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The "
    "project is a repository on main with no commit yet (an unborn branch), so every file is untracked. A work turn "
    "comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the "
    "/preclear turn printed."
)
_ROW9_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The "
    "repository sits in a sibling folder, `main-checkout`, with the plain files committed on main; the project is a "
    "linked worktree of it on the branch `feature/widget-export`, so the project's `.git` is a file that points into the "
    "main checkout. The session runs in the worktree. The harness leaves the main checkout's git metadata out of its "
    "snapshots and keeps every other file of the main checkout under watch, so the row speaks to content preservation of "
    "the main checkout and not to the absence of every git metadata access. A work turn comes first, then the /preclear "
    "turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed."
)
_ROW10_SETUP_TEXT = (
    "Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The "
    "repository holds one commit on main and then 124 untracked files that make a large status listing hard to read: "
    "90 sample files in a folder whose name holds a space, two folders with Japanese and Arabic names holding 15 files each, "
    "files whose names hold a newline, two double quotes and a tab, or two leading spaces, and a notes file with "
    "Japanese and Arabic text. The allowlist is the 33-rule baseline alone: it holds no rule for the NUL form of the "
    "status command, for a redirection or for a status file. A work turn comes first, then the /preclear turn in the "
    "same session, then a fresh session that pastes the resume line the /preclear turn printed. The harness reads "
    "the status form from the stream afterwards and counts it; it does not say which form was right."
)

_ROW1_SETUP_TEXT = (
    "Setup: the configuration names ledger A (`CONTINUITY_CLAUDE-widget-export.md`); the harness bound the "
    "session to ledger B (`CONTINUITY_CLAUDE-other-task.md`, a different workstream in the same fixture root). "
    "A work turn comes first, then the /preclear turn with the JSON-default correction in the same session, then "
    "a fresh session that pastes the resume line the /preclear turn printed."
)
_ROW4A_SETUP_TEXT = (
    "Setup: the configuration names `backend: checkpoint-v2`, which is not a known backend, and "
    "`executable: wrapper/checkpoint`, a relative path. The session is bound to the one ledger the row seeds "
    "(`CONTINUITY_CLAUDE-widget-export.md`), and a working helper wrapper exists at an absolute path in the run "
    "root. A work turn comes first, then the /preclear turn with the JSON-default correction in the same session; "
    "no fresh session follows."
)


def _title_of(identifier: str) -> str:
    return identifier.replace("-", " ")


def _lazy_runner(row_id: str) -> Callable[..., Any]:
    """Return the runner of a registered row: it imports pc_row1 only when it runs, so this module imports alone."""

    def run(ctx: Any, timeout_override: Optional[int] = None) -> Any:
        import pc_row1  # imported late: the registry must stay importable without the row engine

        return pc_row1.run_registered_row(ctx, row_id, timeout_override)

    return run


def _registered_rows() -> Dict[str, RowSpec]:
    """The implemented rows by id. Everything a row needs to run is in its entry (plan 04-01)."""
    return {
        ROW1: RowSpec(
            ROW1,
            KIND_ROW,
            "Row 1: wrong active binding (1P)",
            _ROW1_STAGES,
            True,
            None,
            _lazy_runner(ROW1),
            _ROW1_SOURCES,
            seed="pc_rowseeds:seed_row1",
            prompts=_ROW1_PROMPTS,
            setup_text=_ROW1_SETUP_TEXT,
            tools_profile=PROFILE_HELPER,
        ),
        ROW4A: RowSpec(
            ROW4A,
            KIND_ROW,
            "Row 4a: unknown backend and relative executable (1P)",
            _ROW4A_STAGES,
            True,
            None,
            _lazy_runner(ROW4A),
            _ROW4A_SOURCES,
            seed="pc_rowseeds:seed_row4a",
            prompts=_ROW4A_PROMPTS,
            setup_text=_ROW4A_SETUP_TEXT,
            tools_profile=PROFILE_HELPER,
        ),
        ROW5A: RowSpec(
            ROW5A,
            KIND_ROW,
            "Row 5a: no memory system (1P)",
            _ROW5_STAGES,
            True,
            None,
            _lazy_runner(ROW5A),
            _plain_sources(_PUBLICATION_5A),
            seed="pc_rowseeds:seed_row5a",
            prompts=_plain_prompts(_PUBLICATION_5A),
            setup_text=_ROW5A_SETUP_TEXT,
            tools_profile=PROFILE_PLAIN,
            extra_tools=_PLAIN_EXTRA_TOOLS,
            memory=MEMORY_DISABLED,
        ),
        ROW5B: RowSpec(
            ROW5B,
            KIND_ROW,
            "Row 5b: memory explicitly disabled (1P)",
            _ROW5_STAGES,
            True,
            None,
            _lazy_runner(ROW5B),
            _plain_sources(_PUBLICATION_5B),
            seed="pc_rowseeds:seed_row5b",
            prompts=_plain_prompts(_PUBLICATION_5B),
            setup_text=_ROW5B_SETUP_TEXT,
            tools_profile=PROFILE_PLAIN,
            extra_tools=_PLAIN_EXTRA_TOOLS,
            memory=MEMORY_DISABLED,
        ),
        ROW6: RowSpec(
            ROW6,
            KIND_ROW,
            "Row 6: read-only canonical plan (1P)",
            _ROW5_STAGES,
            True,
            None,
            _lazy_runner(ROW6),
            _plain_sources(_PUBLICATION_6),
            seed="pc_rowseeds:seed_row6",
            prompts=_plain_prompts(_PUBLICATION_6),
            setup_text=_ROW6_SETUP_TEXT,
            tools_profile=PROFILE_PLAIN,
            extra_tools=_PLAIN_EXTRA_TOOLS,
            memory=MEMORY_PINNED,
            hooks=_ROW6_HOOKS,
        ),
        ROW7: RowSpec(
            ROW7,
            KIND_ROW,
            "Row 7: all checkpoint destinations denied (1P)",
            _ROW7_STAGES,
            True,
            _chmod_precondition,
            _lazy_runner(ROW7),
            _plain_sources(_PUBLICATION_7),
            seed="pc_rowseeds:seed_row7",
            prompts=_plain_prompts(_PUBLICATION_7),
            setup_text=_ROW7_SETUP_TEXT,
            tools_profile=PROFILE_PLAIN,
            extra_tools=_PLAIN_EXTRA_TOOLS,
            memory=MEMORY_PINNED,
            hooks=_ROW7_HOOKS,
            chain=CHAIN_PRINTED_CHECKPOINT,
            probe=PROBE_CHMOD,
            analyses=ROW7_ANALYSES,
        ),
        ROW8A: RowSpec(
            ROW8A,
            KIND_ROW,
            "Row 8a: non-git project (1P + 1R)",
            _GIT_ROW_STAGES,
            True,
            None,
            _lazy_runner(ROW8A),
            _plain_sources(_PUBLICATION_8A),
            seed="pc_rowseeds:seed_row8a",
            prompts=_plain_prompts(_PUBLICATION_8A),
            setup_text=_ROW8A_SETUP_TEXT,
            tools_profile=PROFILE_GIT,
            memory=MEMORY_PINNED,
            chain=CHAIN_RESUME_LINE,
        ),
        ROW8B: RowSpec(
            ROW8B,
            KIND_ROW,
            "Row 8b: detached HEAD (1P + 1R)",
            _GIT_ROW_STAGES,
            True,
            None,
            _lazy_runner(ROW8B),
            _plain_sources(_PUBLICATION_8B),
            seed="pc_rowseeds:seed_row8b",
            prompts=_plain_prompts(_PUBLICATION_8B),
            setup_text=_ROW8B_SETUP_TEXT,
            tools_profile=PROFILE_GIT,
            memory=MEMORY_PINNED,
            chain=CHAIN_RESUME_LINE,
        ),
        ROW8C: RowSpec(
            ROW8C,
            KIND_ROW,
            "Row 8c: unborn branch (1P + 1R)",
            _GIT_ROW_STAGES,
            True,
            None,
            _lazy_runner(ROW8C),
            _plain_sources(_PUBLICATION_8C),
            seed="pc_rowseeds:seed_row8c",
            prompts=_plain_prompts(_PUBLICATION_8C),
            setup_text=_ROW8C_SETUP_TEXT,
            tools_profile=PROFILE_GIT,
            memory=MEMORY_PINNED,
            chain=CHAIN_RESUME_LINE,
        ),
        ROW9: RowSpec(
            ROW9,
            KIND_ROW,
            "Row 9: linked worktree beside the main checkout (1P + 1R)",
            _GIT_ROW_STAGES,
            True,
            None,
            _lazy_runner(ROW9),
            _plain_sources(_PUBLICATION_9),
            seed="pc_rowseeds:seed_row9",
            prompts=_plain_prompts(_PUBLICATION_9),
            setup_text=_ROW9_SETUP_TEXT,
            tools_profile=PROFILE_GIT,
            memory=MEMORY_PINNED,
            chain=CHAIN_RESUME_LINE,
        ),
        ROW10: RowSpec(
            ROW10,
            KIND_ROW,
            "Row 10: large status, hostile file names, non-Latin text (1P + 1R)",
            _GIT_ROW_STAGES,
            True,
            None,
            _lazy_runner(ROW10),
            _plain_sources(_PUBLICATION_10),
            seed="pc_rowseeds:seed_row10",
            prompts=_plain_prompts(_PUBLICATION_10),
            setup_text=_ROW10_SETUP_TEXT,
            tools_profile=PROFILE_GIT,
            memory=MEMORY_PINNED,
            chain=CHAIN_RESUME_LINE,
        ),
    }


def build_registry(extra: Optional[Sequence[RowSpec]] = None) -> Tuple[RowSpec, ...]:
    """Return the layouts, then the rows in acceptance order, then any extra rows a test injects."""
    registered = _registered_rows()
    entries: List[RowSpec] = []
    for identifier in LAYOUT_IDS:
        entries.append(RowSpec(identifier, KIND_LAYOUT, _title_of(identifier), (), False, None, None, ()))
    for identifier in ROW_IDS:
        found = registered.get(identifier)
        if found is None:
            found = RowSpec(identifier, KIND_ROW, _title_of(identifier), (), False, None, None, ())
        entries.append(found)
    if extra:
        entries.extend(extra)
    return tuple(entries)


def is_valid_id(text: Any) -> bool:
    """True for 1 to 64 lower-case letters and digits joined by single hyphens, whole string only."""
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_ID_LENGTH:
        return False
    return ID_PATTERN.match(text) is not None


def find_entry(registry: Sequence[RowSpec], kind: str, text: Any) -> Optional[RowSpec]:
    """Return the entry whose kind and id equal text exactly, else None (never a prefix match)."""
    if not is_valid_id(text):
        return None
    for entry in registry:
        if entry.kind == kind and entry.row_id == text:
            return entry
    return None


def worst_case(row: RowSpec) -> Decimal:
    """The most a row can cost: the smaller of the sum of its stage caps and ROW_CAP, as an exact Decimal.

    The spend ledger refuses the launch that would take a row's settled spend plus that stage's cap above ROW_CAP,
    so a row whose caps add up to more than ROW_CAP still cannot cost more than ROW_CAP (FA-6).
    """
    total = Decimal("0")
    for stage in row.stages:
        total += stage.cap
    return total if total < ROW_CAP else ROW_CAP


def session_count(row: RowSpec) -> int:
    """The number of sessions a row starts: the stages whose session key starts a new one."""
    return sum(1 for stage in row.stages if stage.session.startswith("new"))


def stage_key(row_id: str, stage_name: str) -> str:
    """Return the ledger key of a stage: the part of the row id before its first hyphen, then the stage."""
    if not is_valid_id(row_id) or not is_valid_id(stage_name):
        raise ValueError("a row id and a stage name must match the id pattern")
    return "%s-%s" % (row_id.split("-", 1)[0], stage_name)


def parse_evidence_date(date_text: Any) -> datetime.date:
    """Return the calendar date of a YYYY-MM-DD text, or raise ValueError (never echoing the text)."""
    if not isinstance(date_text, str) or _DATE_PATTERN.match(date_text) is None:
        raise ValueError("the evidence date must be YYYY-MM-DD")
    try:
        return datetime.date(int(date_text[0:4]), int(date_text[5:7]), int(date_text[8:10]))
    except ValueError:
        raise ValueError("the evidence date is not a calendar date") from None


def is_valid_campaign(text: Any) -> bool:
    """True for one lower-case id of 1 to 24 characters that holds no part a1 to a9 (the attempt words)."""
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_CAMPAIGN_LENGTH:
        return False
    if CAMPAIGN_PATTERN.match(text) is None:
        return False
    return not any(_ATTEMPT_WORD.match(part) is not None for part in text.split("-"))


def _check_scope(campaign: Optional[str], attempt: int) -> None:
    if campaign is not None and not is_valid_campaign(campaign):
        raise ValueError("the campaign label is not valid")
    if type(attempt) is not int or not 1 <= attempt <= MAX_ATTEMPT:
        raise ValueError("the attempt must be a whole number from 1 to 9")


def _scoped(campaign: Optional[str], attempt: int, matrix: bool, tail: str) -> str:
    _check_scope(campaign, attempt)
    parts: List[str] = []
    if campaign is not None:
        parts.append(campaign)
    elif matrix:
        parts.append(MATRIX_SCOPE)
    if attempt > 1:
        parts.append("a%d" % attempt)
    parts.append(tail)
    text = "-".join(parts)
    if not is_valid_id(text):
        raise ValueError("the scoped id does not fit the id pattern")
    return text


def scoped_row(row_id: str, campaign: Optional[str] = None, attempt: int = 1, matrix: bool = False) -> str:
    """Return the ledger row id of a row: <scope>-[a<N>-]<row id>.

    The scope is the campaign label when there is one, else the word matrix when matrix is true, else nothing; the
    word a<N> is added only for an attempt above 1. With neither scope nor attempt the id is the bare row id, as
    Phase 3 wrote it. A value that does not fit the 64-character id rule of the spend ledger is a ValueError.
    """
    if not is_valid_id(row_id):
        raise ValueError("a row id must match the id pattern")
    return _scoped(campaign, attempt, matrix, row_id)


def scoped_stage_key(
    row_id: str, stage_name: str, campaign: Optional[str] = None, attempt: int = 1, matrix: bool = False
) -> str:
    """Return the ledger stage key of a stage: <scope>-[a<N>-]<stage_key(row id, stage name)>."""
    return _scoped(campaign, attempt, matrix, stage_key(row_id, stage_name))


def row_folder_name(row_id: str, attempt: int = 1) -> str:
    """Return the row's folder name inside a dated folder: the bare row id, or <row id>-attempt-<N> above attempt 1."""
    if not is_valid_id(row_id):
        raise ValueError("a row id must match the id pattern")
    _check_scope(None, attempt)
    return row_id if attempt == 1 else "%s-attempt-%d" % (row_id, attempt)


def evidence_folder_name(date_text: str, model: str, campaign: Optional[str] = None) -> str:
    """Return rerun-<date>-<model>[-<campaign>] (D-05), refusing a malformed date, a bad label or an unsafe model."""
    parse_evidence_date(date_text)
    if campaign is not None and not is_valid_campaign(campaign):
        raise ValueError("the campaign label is not valid")
    if (
        not isinstance(model, str)
        or len(model) > MAX_MODEL_LENGTH
        or _MODEL_PATTERN.match(model) is None
        or ".." in model
    ):
        raise ValueError("the model id is not safe in a folder name")
    name = "rerun-%s-%s" % (date_text, model)
    return name if campaign is None else "%s-%s" % (name, campaign)
