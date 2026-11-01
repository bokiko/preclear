"""Row and layout registry for the matrix driver (HARN-01, D-12, D-14).

One place says which layouts and rows exist, in the order the acceptance document runs them,
which of them this phase implements, and what each stage of an implemented row may cost:

  * ROW_IDS, LAYOUT_IDS   the eighteen row ids (the committed evidence folder names with the
                          rerun and first-pass suffixes collapsed) and the three layouts
  * StageSpec, RowSpec    one stage (turns, cap as Decimal, session key) and one registry entry; an entry
                          also carries what makes a row runnable from the registry alone (plan 04-01): the
                          seed it names, the prompt files of its stages, the Setup paragraph of its README and
                          its allowlist profile
  * RunContext, RowOutcome  the records the driver hands to a row runner and gets back
  * build_registry        the full registry, plus any rows a test injects
  * find_entry            exact, whole-id lookup; a prefix, another case or an odd value is None
  * worst_case, session_count, stage_key, evidence_folder_name

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

# Allowlist profiles (RowSpec.tools_profile). PROFILE_HELPER is the committed 33-rule baseline plus one rule per
# model-facing verb of the logging wrapper; the runner and the filing turn the word into rules, never this module.
PROFILE_HELPER = "helper"

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


class RowOutcome(NamedTuple):
    """What a row runner returns: an exit code and the fixed-text lines to print."""

    code: int
    lines: Tuple[str, ...]


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
            "pc_row1:run_row",
            _ROW1_SOURCES,
            setup_text=_ROW1_SETUP_TEXT,
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
    """The sum of the stage caps as an exact Decimal."""
    total = Decimal("0")
    for stage in row.stages:
        total += stage.cap
    return total


def session_count(row: RowSpec) -> int:
    """The number of sessions a row starts: the stages whose session key starts a new one."""
    return sum(1 for stage in row.stages if stage.session.startswith("new"))


def stage_key(row_id: str, stage_name: str) -> str:
    """Return the ledger key of a stage: the part of the row id before its first hyphen, then the stage."""
    if not is_valid_id(row_id) or not is_valid_id(stage_name):
        raise ValueError("a row id and a stage name must match the id pattern")
    return "%s-%s" % (row_id.split("-", 1)[0], stage_name)


def evidence_folder_name(date_text: str, model: str) -> str:
    """Return rerun-<date>-<model> (D-05), refusing a malformed date or a model unsafe in a folder name."""
    if not isinstance(date_text, str) or _DATE_PATTERN.match(date_text) is None:
        raise ValueError("the evidence date must be YYYY-MM-DD")
    try:
        datetime.date(int(date_text[0:4]), int(date_text[5:7]), int(date_text[8:10]))
    except ValueError:
        raise ValueError("the evidence date is not a calendar date") from None
    if (
        not isinstance(model, str)
        or len(model) > MAX_MODEL_LENGTH
        or _MODEL_PATTERN.match(model) is None
        or ".." in model
    ):
        raise ValueError("the model id is not safe in a folder name")
    return "rerun-%s-%s" % (date_text, model)
