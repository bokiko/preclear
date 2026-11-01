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

# Allowlist profiles (RowSpec.tools_profile). PROFILE_HELPER is the committed 33-rule baseline plus one rule per
# model-facing verb of the logging wrapper; the runner and the filing turn the word into rules, never this module.
PROFILE_HELPER = "helper"
# PROFILE_PLAIN is the baseline alone (no wrapper rule of any kind); a row adds its own extra rules in RowSpec.extra_tools.
PROFILE_PLAIN = "plain"

# Memory policies (RowSpec.memory): what the run settings say about Claude Code's auto-memory. In both the directory is
# pinned inside the run root. MEMORY_PINNED is the Phase 3 setting (on); MEMORY_DISABLED turns it off (rows 5a and 5b).
MEMORY_PINNED = "pinned"
MEMORY_DISABLED = "disabled"

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
