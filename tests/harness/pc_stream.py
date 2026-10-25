"""Strict stream-json parser and structured denial detection (HARN-06, D-13).

A captured claude -p stream is untrusted bytes written by a model-driven process. This module
accepts a stream only when it is complete and well formed, and it decides whether a row hit a
permission denial from structured fields alone:

  * a system event with subtype permission_denied, and
  * an entry in the result event's permission_denials list.

It reads bytes and never inspects reply text or tool-result text for words (Pitfall 9): a
reply that merely contains the word denied is not a signal. The two structured signals are
cross-checked and a mismatch is reported in both directions. A tool result flagged as an
error without either signal is listed for diagnostics only.

Command line (run as python3 -E -s -B pc_stream.py):

    check FILE [--expect-denied ID ...]

prints counts and opaque ids only, and exits 0 when the stream is complete with no unexpected
denial, 19 (DENIAL_FOUND) on an unexpected denial, an incomplete stream or a parse error, and
2 on a missing file or bad usage. The module reads files as bytes only and writes nothing
except to the standard streams.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Sequence, Set, Tuple

import pc_exitcodes

MISSING_ID = "<missing-id>"

_INIT_KEYS = (
    "session_id",
    "claude_code_version",
    "cwd",
    "tools",
    "mcp_servers",
    "model",
    "permissionMode",
    "slash_commands",
    "skills",
    "plugins",
    "agents",
    "apiKeySource",
    "memory_paths",
    "effort",
)

_SAFE_LABEL = re.compile(r"[A-Za-z0-9_.<>-]{1,64}\Z")


class StreamError(ValueError):
    """The stream is malformed, incomplete or of an unknown shape. Never a pass."""


def _reject_constant(_name: str) -> Any:
    raise ValueError("non-finite number")


def parse_stream(data: bytes) -> List[Dict[str, Any]]:
    """Parse a stream into a list of event dicts or raise StreamError.

    Lines are split on the newline byte only, so U+2028 and U+0085 inside a JSON string stay
    inside one event. Errors name the 1-based line number and never the line content.
    Floating-point numbers become Decimal so spend arithmetic never uses binary floats.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise StreamError("the stream must be bytes")
    data = bytes(data)
    if not data:
        raise StreamError("the stream is empty")
    pieces = data.split(b"\n")
    if pieces[-1] == b"":
        pieces.pop()
    events: List[Dict[str, Any]] = []
    for number, piece in enumerate(pieces, 1):
        if piece.endswith(b"\r"):
            piece = piece[:-1]
        if not piece:
            raise StreamError("line %d: blank line" % number)
        try:
            text = piece.decode("utf-8")
        except UnicodeDecodeError:
            raise StreamError("line %d: not valid UTF-8" % number) from None
        try:
            event = json.loads(text, parse_float=Decimal, parse_constant=_reject_constant)
        except (ValueError, RecursionError):
            raise StreamError("line %d: not valid JSON" % number) from None
        if not isinstance(event, dict):
            raise StreamError("line %d: not a JSON object" % number)
        if not isinstance(event.get("type"), str):
            raise StreamError("line %d: missing string type" % number)
        events.append(event)
    return events


def _of_type(events: Sequence[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    return [event for event in events if event.get("type") == event_type]


def require_single_result(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the one result event; zero or several is a StreamError (an incomplete stream)."""
    results = _of_type(events, "result")
    if len(results) != 1:
        raise StreamError("expected exactly one result event, found %d" % len(results))
    return results[0]


def init_manifest(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the system/init fields the matrix records, None where a key is absent."""
    inits = [e for e in _of_type(events, "system") if e.get("subtype") == "init"]
    if len(inits) != 1:
        raise StreamError("expected exactly one init event, found %d" % len(inits))
    return {key: inits[0].get(key) for key in _INIT_KEYS}


def _as_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, bool):
        raise StreamError("total_cost_usd is not a number")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    raise StreamError("total_cost_usd is not a number")


def _result_denial_entries(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "permission_denials" not in result:
        return []
    entries = result["permission_denials"]
    if not isinstance(entries, list):
        raise StreamError("permission_denials is not a list")
    for entry in entries:
        if not isinstance(entry, dict):
            raise StreamError("a permission_denials entry is not an object")
    return entries


def result_summary(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the result event's outcome fields; total_cost_usd is a Decimal or None."""
    result = require_single_result(events)
    return {
        "subtype": result.get("subtype"),
        "is_error": result.get("is_error"),
        "num_turns": result.get("num_turns"),
        "terminal_reason": result.get("terminal_reason"),
        "session_id": result.get("session_id"),
        "permission_denials": len(_result_denial_entries(result)),
        "total_cost_usd": _as_decimal(result.get("total_cost_usd")),
    }


def _id_of(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    return MISSING_ID


def _blocks(event: Dict[str, Any], block_type: str) -> Iterator[Dict[str, Any]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == block_type:
            yield block


class DenialReport(NamedTuple):
    event_ids: frozenset
    result_ids: frozenset
    union: frozenset
    only_in_events: frozenset
    only_in_result: frozenset
    tool_errors: frozenset


def denial_report(events: Sequence[Dict[str, Any]]) -> DenialReport:
    """Cross-check the two structured denial signals; both directions of mismatch are reported."""
    result = require_single_result(events)
    event_ids = frozenset(
        _id_of(e.get("tool_use_id"))
        for e in _of_type(events, "system")
        if e.get("subtype") == "permission_denied"
    )
    result_ids = frozenset(_id_of(entry.get("tool_use_id")) for entry in _result_denial_entries(result))
    union = event_ids | result_ids
    errors = set()
    for event in _of_type(events, "user"):
        for block in _blocks(event, "tool_result"):
            if block.get("is_error") is True:
                tool_id = _id_of(block.get("tool_use_id"))
                if tool_id not in union:
                    errors.add(tool_id)
    return DenialReport(
        event_ids=event_ids,
        result_ids=result_ids,
        union=union,
        only_in_events=event_ids - result_ids,
        only_in_result=result_ids - event_ids,
        tool_errors=frozenset(errors),
    )


def unexpected_denials(events: Sequence[Dict[str, Any]], expected_ids: Set[str]) -> List[str]:
    """Return the sorted denial ids that are outside expected_ids."""
    return sorted(denial_report(events).union - set(expected_ids))


def row_failed(events: Sequence[Dict[str, Any]], expected_ids: Set[str]) -> bool:
    """True when a denial is unexpected or the stream is incomplete (fail closed)."""
    try:
        return bool(unexpected_denials(events, expected_ids))
    except StreamError:
        return True


def tool_calls(events: Sequence[Dict[str, Any]]) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return (tool_use_id, name, input) for each assistant tool_use block, in order."""
    calls = []
    for event in _of_type(events, "assistant"):
        for block in _blocks(event, "tool_use"):
            name = block.get("name")
            tool_input = block.get("input")
            calls.append(
                (
                    _id_of(block.get("id")),
                    name if isinstance(name, str) else "<unknown>",
                    tool_input if isinstance(tool_input, dict) else {},
                )
            )
    return calls


def tool_results(events: Sequence[Dict[str, Any]]) -> Dict[str, Tuple[bool, str, int]]:
    """Return tool_use_id -> (is_error, content type name, content length). Never the content."""
    found: Dict[str, Tuple[bool, str, int]] = {}
    for event in _of_type(events, "user"):
        for block in _blocks(event, "tool_result"):
            content = block.get("content")
            length = len(content) if isinstance(content, (str, list)) else 0
            found[_id_of(block.get("tool_use_id"))] = (
                block.get("is_error") is True,
                type(content).__name__,
                length,
            )
    return found


def probe_table(
    events: Sequence[Dict[str, Any]],
) -> List[Tuple[str, str, Optional[str], Optional[bool], bool, bool]]:
    """Join calls, results and denials into rows for the policy probe.

    Each row is (tool_use_id, name, command for Bash calls else None, is_error or None when no
    result was seen, denied by a permission_denied event, denied in result.permission_denials).
    """
    report = denial_report(events)
    results = tool_results(events)
    rows = []
    for tool_id, name, tool_input in tool_calls(events):
        command = tool_input.get("command") if name == "Bash" else None
        seen = results.get(tool_id)
        rows.append(
            (
                tool_id,
                name,
                command if isinstance(command, str) else None,
                seen[0] if seen is not None else None,
                tool_id in report.event_ids,
                tool_id in report.result_ids,
            )
        )
    return rows


def _safe_label(text: Any) -> str:
    if isinstance(text, str) and _SAFE_LABEL.match(text):
        return text
    return "<odd>"


def _check_command(path: str, expected: Sequence[str]) -> int:
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        sys.stderr.write("cannot read the file\n")
        return pc_exitcodes.USAGE
    try:
        events = parse_stream(data)
    except StreamError as problem:
        sys.stdout.write("stream error: %s\n" % problem)
        return pc_exitcodes.DENIAL_FOUND
    counts: Dict[str, int] = {}
    for event in events:
        label = _safe_label(event.get("type"))
        counts[label] = counts.get(label, 0) + 1
    sys.stdout.write("events: %s\n" % " ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    try:
        summary = result_summary(events)
        report = denial_report(events)
    except StreamError as problem:
        sys.stdout.write("stream error: %s\n" % problem)
        return pc_exitcodes.DENIAL_FOUND
    sys.stdout.write("result subtype: %s\n" % _safe_label(summary["subtype"]))
    ids = sorted(_safe_label(item) for item in report.union)
    if ids:
        sys.stdout.write("denial ids: %d (%s)\n" % (len(ids), ", ".join(ids)))
    else:
        sys.stdout.write("denial ids: 0\n")
    unexpected = sorted(report.union - set(expected))
    if unexpected:
        sys.stdout.write("unexpected denial ids: %d\n" % len(unexpected))
        return pc_exitcodes.DENIAL_FOUND
    return pc_exitcodes.OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="pc_stream.py")
    commands = parser.add_subparsers(dest="command")
    check = commands.add_parser("check")
    check.add_argument("file")
    check.add_argument("--expect-denied", action="append", default=[], metavar="ID")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
    if args.command != "check":
        sys.stderr.write("usage: pc_stream.py check FILE [--expect-denied ID ...]\n")
        return pc_exitcodes.USAGE
    return _check_command(args.file, args.expect_denied)


if __name__ == "__main__":
    sys.exit(main())
