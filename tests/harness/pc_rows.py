"""Row and layout registry for the matrix driver (HARN-01, D-12, D-14).

One place says which layouts and rows exist, in the order the acceptance document runs them,
which of them this phase implements, and what each stage of an implemented row may cost:

  * ROW_IDS, LAYOUT_IDS   the eighteen row ids (the committed evidence folder names with the
                          rerun and first-pass suffixes collapsed) and the three layouts
  * StageSpec, RowSpec    one stage (turns, cap as Decimal, session key) and one registry entry
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


class RunContext(NamedTuple):
    """Everything a row runner needs; run_root, sanitizer and deny_entries are filled by the runner."""

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


class RowOutcome(NamedTuple):
    """What a row runner returns: an exit code and the fixed-text lines to print."""

    code: int
    lines: Tuple[str, ...]


_ROW1_STAGES: Tuple[StageSpec, ...] = (
    StageSpec("s1", WORK_TURN, "work", 15, Decimal("0.30"), 900, "new:A"),
    StageSpec("s2", PRECLEAR_TURN, "preclear", 60, Decimal("1.30"), 1800, "resume:A"),
    StageSpec("s3", FRESH_RESUME, "resume", 15, Decimal("0.40"), 900, "new:B"),
)

_PUBLICATION = "tests/evidence/publication-2026-10-20/row1-wrong-binding"
_ROW1_SOURCES: Tuple[Tuple[str, str], ...] = (
    ("SKILL.md", "file"),
    ("references", "dir"),
    ("tests/harness/checkpoint-wrapper", "file"),
    ("tests/harness/checkpoint_stub.py", "file"),
    ("tests/harness/pc_hooklog.py", "file"),
    (_PUBLICATION + "/fixture-CLAUDE.md", "file"),
    (_PUBLICATION + "/s2-preclear-prompt.md", "file"),
    (_PUBLICATION + "/snap-0-setup/CONTINUITY_CLAUDE-other-task.md", "file"),
    (_PUBLICATION + "/snap-0-setup/CONTINUITY_CLAUDE-widget-export.md", "file"),
    ("tests/fixtures/bound-ledger/project", "dir"),
)


def _title_of(identifier: str) -> str:
    return identifier.replace("-", " ")


def build_registry(extra: Optional[Sequence[RowSpec]] = None) -> Tuple[RowSpec, ...]:
    """Return the layouts, then the rows in acceptance order, then any extra rows a test injects."""
    entries: List[RowSpec] = []
    for identifier in LAYOUT_IDS:
        entries.append(RowSpec(identifier, KIND_LAYOUT, _title_of(identifier), (), False, None, None, ()))
    for identifier in ROW_IDS:
        if identifier == ROW1:
            entries.append(
                RowSpec(
                    identifier,
                    KIND_ROW,
                    _title_of(identifier),
                    _ROW1_STAGES,
                    True,
                    None,
                    "pc_row1:run_row",
                    _ROW1_SOURCES,
                )
            )
        else:
            entries.append(RowSpec(identifier, KIND_ROW, _title_of(identifier), (), False, None, None, ()))
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
