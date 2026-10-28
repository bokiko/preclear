"""The matrix spend ledger: reserve a stage's cap before any process, one attempt per stage (D-12, D-14).

The ledger is one append-only file, matrix-spend.jsonl, in the harness home (never in the repository),
next to a lock file. Every line is ASCII JSON with sorted keys and exactly the keys of its kind:

  launch      row, stage, attempt, cap, version      written BEFORE a stage's process starts; the cap
                                                      is the pessimistic cost until a settle line replaces it
  settle      row, stage, attempt, subtype, delta,   written when the stage's result is known; delta is
              cumulative, version                    the cost of that one call, cumulative the reported total
  authorize   row, stage, cap                        written only by --authorize-retry, typed by a person;
                                                      it permits exactly one more attempt of the stage and
                                                      raises the row limit by that stage's cap

All costs are decimal text (never a float); a launch and its settle lines are one attempt, and the latest
line for a (stage, attempt) is its effective record. A stage may be attempted once; a second attempt needs an
authorization line. The pessimistic row total (a settled attempt counts its delta, an unsettled one its cap)
plus a new cap may not exceed ROW_CAP plus the caps of the row's authorization lines.

append_launch reads the history, checks it and appends under one exclusive file lock, so two launches cannot
both pass the same check (review WR-06). A malformed ledger line is refused, never skipped: every read and
every append raises SpendError and writes nothing (fail closed). Nothing here deletes, renames or truncates.

Per-call cost (call_cost) is a delta because total_cost_usd is cumulative across a resumed session; the row
total (row_total) adds the final cumulative total of each session chain once, so an earlier stage inside a
resumed chain is never counted twice.

Standard library only, Python 3.9 floor, exact Decimal arithmetic, no float arithmetic. Messages are fixed
text: stage keys and counts, never a path.
"""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

ROW_CAP = Decimal("2.00")  # D-12: the most one row may cost, in US dollars, before any authorization
LEDGER_NAME = "matrix-spend.jsonl"
LOCK_NAME = "matrix-spend.lock"

KIND_LAUNCH = "launch"
KIND_SETTLE = "settle"
KIND_AUTHORIZE = "authorize"

_KEYS: Dict[str, Tuple[str, ...]] = {
    KIND_LAUNCH: ("attempt", "cap", "kind", "row", "stage", "version"),
    KIND_SETTLE: ("attempt", "cumulative", "delta", "kind", "row", "stage", "subtype", "version"),
    KIND_AUTHORIZE: ("cap", "kind", "row", "stage"),
}
_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_COST = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")
_MAX_ID_LENGTH = 64
_MAX_TEXT_LENGTH = 128

MESSAGE_UNUSABLE_HOME = "the spend ledger folder is unusable"
MESSAGE_BAD_LEDGER = "the spend ledger holds a line that is not a spend record"
MESSAGE_UNKNOWN_STAGE = "that stage is not known"
MESSAGE_NOT_ATTEMPTED = "that stage has not been attempted"
MESSAGE_ATTEMPT_USED = "the attempt for this stage is used up; a retry needs an authorization line"
MESSAGE_ROW_LIMIT = "this launch would take the row above its spend limit"
MESSAGE_PENDING = "an authorization for that stage is already waiting for its retry"
MESSAGE_NO_LAUNCH = "there is no launch line for that attempt"
MESSAGE_NO_COST = "the result event carries no usable cost"


class SpendError(Exception):
    """The ledger or its folder is unusable or malformed. Fail closed: nothing was written."""


class SpendRefused(Exception):
    """The spend gate refused: the attempt or the row limit. Maps to BUDGET_REFUSED (18)."""


class StageNotAttempted(SpendRefused):
    """A retry authorization was asked for a stage that has no launch line."""


# ---------------------------------------------------------------------------------------------
# Validation and the strict reader
# ---------------------------------------------------------------------------------------------


def _is_id(text: Any) -> bool:
    return isinstance(text, str) and 1 <= len(text) <= _MAX_ID_LENGTH and _ID.match(text) is not None


def _check_cap(cap: Any) -> Decimal:
    """A cap, an authorization cap or a settle cost: an exact, finite Decimal above zero is required."""
    if not isinstance(cap, Decimal):
        raise TypeError("a cap must be an exact Decimal")
    if not cap.is_finite() or cap <= 0:
        raise ValueError("a cap must be a finite amount above zero")
    return cap


def _check_cost(value: Any, what: str) -> Optional[Decimal]:
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise TypeError("%s must be an exact Decimal or None" % what)
    if not value.is_finite() or value < 0:
        raise ValueError("%s must be a finite amount of at least zero" % what)
    return value


def _cost_text(value: Optional[Decimal]) -> Optional[str]:
    return None if value is None else format(value, "f")


def _parse_cost(text: Any, positive: bool) -> Decimal:
    if not isinstance(text, str) or len(text) > _MAX_TEXT_LENGTH or _COST.match(text) is None:
        raise SpendError(MESSAGE_BAD_LEDGER)
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise SpendError(MESSAGE_BAD_LEDGER) from None
    if not number.is_finite() or (positive and number <= 0):
        raise SpendError(MESSAGE_BAD_LEDGER)
    return number


def _reject_constant(_name: str) -> Any:
    raise ValueError("non-finite number")


def _validate_line(text: str) -> Dict[str, Any]:
    """Return the record of one ledger line with Decimal costs, or raise SpendError."""
    try:
        raw = json.loads(text, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        raise SpendError(MESSAGE_BAD_LEDGER) from None
    if not isinstance(raw, dict):
        raise SpendError(MESSAGE_BAD_LEDGER)
    kind = raw.get("kind")
    if kind not in _KEYS or tuple(sorted(raw)) != _KEYS[kind]:
        raise SpendError(MESSAGE_BAD_LEDGER)
    if not _is_id(raw["row"]) or not _is_id(raw["stage"]):
        raise SpendError(MESSAGE_BAD_LEDGER)
    record: Dict[str, Any] = {"kind": kind, "row": raw["row"], "stage": raw["stage"]}
    if kind in (KIND_LAUNCH, KIND_SETTLE):
        attempt = raw["attempt"]
        if type(attempt) is not int or attempt < 1:
            raise SpendError(MESSAGE_BAD_LEDGER)
        version = raw["version"]
        if version is not None and (not isinstance(version, str) or len(version) > _MAX_TEXT_LENGTH):
            raise SpendError(MESSAGE_BAD_LEDGER)
        record["attempt"] = attempt
        record["version"] = version
    if kind in (KIND_LAUNCH, KIND_AUTHORIZE):
        record["cap"] = _parse_cost(raw["cap"], positive=True)
    if kind == KIND_SETTLE:
        subtype = raw["subtype"]
        if not isinstance(subtype, str) or not subtype or len(subtype) > _MAX_TEXT_LENGTH:
            raise SpendError(MESSAGE_BAD_LEDGER)
        record["subtype"] = subtype
        for name in ("delta", "cumulative"):
            record[name] = None if raw[name] is None else _parse_cost(raw[name], positive=False)
    return record


def _check_history(records: Sequence[Dict[str, Any]]) -> None:
    """Cross-check the lines: attempts count up from one, settles follow a launch, retries follow a launch."""
    launched: Dict[str, int] = {}
    for record in records:
        stage = record["stage"]
        if record["kind"] == KIND_LAUNCH:
            if record["attempt"] != launched.get(stage, 0) + 1:
                raise SpendError(MESSAGE_BAD_LEDGER)
            launched[stage] = record["attempt"]
        elif record["kind"] == KIND_SETTLE:
            if record["attempt"] > launched.get(stage, 0):
                raise SpendError(MESSAGE_BAD_LEDGER)
        elif stage not in launched:
            raise SpendError(MESSAGE_BAD_LEDGER)


def _read(path: str) -> List[Dict[str, Any]]:
    """Read and strictly validate the ledger at path; a missing or empty file is an empty history."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    except FileNotFoundError:
        return []
    except OSError:
        raise SpendError(MESSAGE_UNUSABLE_HOME) from None
    try:
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError:
        raise SpendError(MESSAGE_UNUSABLE_HOME) from None
    finally:
        os.close(fd)
    data = b"".join(chunks)
    if data == b"":
        return []
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise SpendError(MESSAGE_BAD_LEDGER) from None
    if not text.endswith("\n"):
        raise SpendError(MESSAGE_BAD_LEDGER)
    records = [_validate_line(line) for line in text.split("\n")[:-1]]
    _check_history(records)
    return records


def _append_line(path: str, record: Mapping[str, Any]) -> None:
    line = (json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError:
        raise SpendError(MESSAGE_UNUSABLE_HOME) from None
    try:
        view = memoryview(line)
        while len(view) > 0:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    except OSError:
        raise SpendError(MESSAGE_UNUSABLE_HOME) from None
    finally:
        os.close(fd)


@contextlib.contextmanager
def _locked(home: str) -> Iterator[str]:
    """Hold the exclusive ledger lock; yield the ledger path. The home is created private when missing."""
    if not isinstance(home, str) or not home:
        raise SpendError(MESSAGE_UNUSABLE_HOME)
    try:
        os.makedirs(home, mode=0o700, exist_ok=True)
        fd = os.open(os.path.join(home, LOCK_NAME), os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0), 0o600)
    except OSError:
        raise SpendError(MESSAGE_UNUSABLE_HOME) from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield ledger_path(home)
    finally:
        os.close(fd)  # closing the descriptor releases the lock


def ledger_path(home: str) -> str:
    return os.path.join(home, LEDGER_NAME)


# ---------------------------------------------------------------------------------------------
# Reading the history
# ---------------------------------------------------------------------------------------------


def read_records(home: str) -> List[Dict[str, Any]]:
    """Return the validated ledger lines in order (costs as Decimal); a malformed line is SpendError."""
    return _read(ledger_path(home))


def effective_records(records: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, int], Dict[str, Any]]:
    """Return the latest launch or settle line per (stage, attempt): a later line supersedes an earlier one."""
    latest: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for record in records:
        if record["kind"] in (KIND_LAUNCH, KIND_SETTLE):
            latest[(record["stage"], record["attempt"])] = record
    return latest


def _count(records: Sequence[Dict[str, Any]], kind: str, stage: str) -> int:
    return sum(1 for record in records if record["kind"] == kind and record["stage"] == stage)


def attempts_used(home: str, stage: str) -> int:
    """The number of launch lines recorded for a stage key."""
    return _count(read_records(home), KIND_LAUNCH, stage)


def _pessimistic_total(records: Sequence[Dict[str, Any]], row: str) -> Decimal:
    caps: Dict[Tuple[str, int], Decimal] = {}
    for record in records:
        if record["kind"] == KIND_LAUNCH and record["row"] == row:
            caps[(record["stage"], record["attempt"])] = record["cap"]
    total = Decimal("0")
    effective = effective_records(records)
    for key, cap in caps.items():
        latest = effective[key]
        if latest["kind"] == KIND_SETTLE and latest["delta"] is not None:
            total += latest["delta"]
        else:
            total += cap
    return total


def row_pessimistic_total(home: str, row: str) -> Decimal:
    """The row's pessimistic spend: a settled attempt counts its delta, an unsettled one its cap."""
    return _pessimistic_total(read_records(home), row)


def _row_limit(records: Sequence[Dict[str, Any]], row: str) -> Decimal:
    limit = ROW_CAP
    for record in records:
        if record["kind"] == KIND_AUTHORIZE and record["row"] == row:
            limit += record["cap"]
    return limit


# ---------------------------------------------------------------------------------------------
# Writing: launch, settle, authorize
# ---------------------------------------------------------------------------------------------


def append_launch(
    home: str,
    row: str,
    stage: str,
    cap: Decimal,
    version: Optional[str],
    allowed_stages: Sequence[str],
) -> int:
    """Reserve a stage's cap with a pessimistic launch line and return the attempt number.

    Refused with SpendRefused for an unknown stage, for a stage whose attempts are used up (one attempt, plus
    one per authorization line), and for a launch that would take the row's pessimistic total above ROW_CAP
    plus its authorization caps. The read, the checks and the append happen under one file lock.
    """
    _check_cap(cap)
    if not _is_id(row) or not _is_id(stage) or stage not in tuple(allowed_stages):
        raise SpendRefused(MESSAGE_UNKNOWN_STAGE)
    if version is not None and (not isinstance(version, str) or len(version) > _MAX_TEXT_LENGTH):
        raise ValueError("the version must be text or None")
    with _locked(home) as path:
        records = _read(path)
        used = _count(records, KIND_LAUNCH, stage)
        if used >= 1 + _count(records, KIND_AUTHORIZE, stage):
            raise SpendRefused(MESSAGE_ATTEMPT_USED)
        if _pessimistic_total(records, row) + cap > _row_limit(records, row):
            raise SpendRefused(MESSAGE_ROW_LIMIT)
        attempt = used + 1
        _append_line(
            path,
            {
                "attempt": attempt,
                "cap": _cost_text(cap),
                "kind": KIND_LAUNCH,
                "row": row,
                "stage": stage,
                "version": version,
            },
        )
    return attempt


def settle(
    home: str,
    row: str,
    stage: str,
    attempt: int,
    subtype: str,
    delta: Optional[Decimal],
    cumulative: Optional[Decimal],
    version: Optional[str],
) -> None:
    """Record the outcome of a launched attempt; delta and cumulative are None when no result arrived."""
    _check_cost(delta, "the delta")
    _check_cost(cumulative, "the cumulative total")
    if type(attempt) is not int or attempt < 1:
        raise ValueError("the attempt must be a positive integer")
    if not isinstance(subtype, str) or not subtype or len(subtype) > _MAX_TEXT_LENGTH:
        raise ValueError("the subtype must be non-empty text")
    if not _is_id(row) or not _is_id(stage):
        raise SpendError(MESSAGE_NO_LAUNCH)
    with _locked(home) as path:
        records = _read(path)
        if attempt > _count(records, KIND_LAUNCH, stage):
            raise SpendError(MESSAGE_NO_LAUNCH)
        _append_line(
            path,
            {
                "attempt": attempt,
                "cumulative": _cost_text(cumulative),
                "delta": _cost_text(delta),
                "kind": KIND_SETTLE,
                "row": row,
                "stage": stage,
                "subtype": subtype,
                "version": version if isinstance(version, str) else None,
            },
        )


def authorize_retry(home: str, row: str, stage: str, cap: Decimal, allowed_stages: Sequence[str]) -> None:
    """Append one authorization line: one more attempt of the stage, and the row limit raised by cap.

    Refused for an unknown stage, with StageNotAttempted for a stage that has no launch line, and while an
    earlier authorization for the stage is still waiting for its retry. A refusal creates nothing.
    """
    _check_cap(cap)
    if not _is_id(row) or not _is_id(stage) or stage not in tuple(allowed_stages):
        raise SpendRefused(MESSAGE_UNKNOWN_STAGE)
    if not os.path.exists(ledger_path(home)):
        raise StageNotAttempted(MESSAGE_NOT_ATTEMPTED)
    with _locked(home) as path:
        records = _read(path)
        used = _count(records, KIND_LAUNCH, stage)
        if used == 0:
            raise StageNotAttempted(MESSAGE_NOT_ATTEMPTED)
        if _count(records, KIND_AUTHORIZE, stage) >= used:
            raise SpendRefused(MESSAGE_PENDING)
        _append_line(path, {"cap": _cost_text(cap), "kind": KIND_AUTHORIZE, "row": row, "stage": stage})


# ---------------------------------------------------------------------------------------------
# Cost of one call (a delta) and of one row
# ---------------------------------------------------------------------------------------------


def _as_decimal(value: Any) -> Decimal:
    """Convert a parsed cost to Decimal without float arithmetic (a float goes through its repr text)."""
    if isinstance(value, bool) or value is None:
        raise SpendError(MESSAGE_NO_COST)
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, str):
        try:
            number = Decimal(value)
        except InvalidOperation:
            raise SpendError(MESSAGE_NO_COST) from None
    else:
        try:
            number = Decimal(repr(value))
        except InvalidOperation:
            raise SpendError(MESSAGE_NO_COST) from None
    if not number.is_finite() or number < 0:
        raise SpendError(MESSAGE_NO_COST)
    return number


def call_cost(result_event: Mapping[str, Any], previous_total: Optional[Decimal] = None) -> Decimal:
    """Return the cost of the one call a result event ends, as an exact Decimal.

    total_cost_usd is cumulative across a resumed session, so it is not a call's cost. The cost of the call is
    the sum of costUSD over model_usage_since_last_result when that mapping is present and non-empty; else, for
    a first call of a session, the total itself; else the total minus the previous cumulative total.
    """
    since = result_event.get("model_usage_since_last_result")
    if isinstance(since, dict) and since:
        total = Decimal("0")
        for usage in since.values():
            if not isinstance(usage, dict) or "costUSD" not in usage:
                raise SpendError(MESSAGE_NO_COST)
            total += _as_decimal(usage["costUSD"])
        return total
    cumulative = _as_decimal(result_event.get("total_cost_usd"))
    if previous_total is None:
        return cumulative
    if not isinstance(previous_total, Decimal):
        raise TypeError("the previous total must be an exact Decimal")
    delta = cumulative - previous_total
    if delta < 0:
        raise SpendError(MESSAGE_NO_COST)
    return delta


def row_total(chain_totals: Sequence[Decimal]) -> Decimal:
    """Add the final cumulative total of each session chain once (s1 is inside the s2 chain)."""
    total = Decimal("0")
    for chain in chain_totals:
        if not isinstance(chain, Decimal):
            raise TypeError("a chain total must be an exact Decimal")
        total += chain
    return total
