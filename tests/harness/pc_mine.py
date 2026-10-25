"""Miner for the committed wrapper-calls.log files (STUB-03).

Reads every committed ``wrapper-calls.log`` under the publication evidence
folder and turns it into replay cases: the helper argv sequence, the recorded
exit codes, the input files each call read, and where each call's decisive
output is recorded in committed evidence.

Output goes to standard output as canonical JSON. This module writes nothing;
the committed copy ``tests/harness/replay-cases.json`` is produced once with a
shell redirect, and ``--check`` compares a fresh mine with that copy.

Run as ``python3 -E -s -B tests/harness/pc_mine.py [--check]``. Not ``-I``:
isolated mode drops the script folder from sys.path and the pc_ modules import
each other.

Exit codes: 0 ok (``--check`` found no difference), 1 ``--check`` found a
difference, 2 bad usage or a mining failure.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

SCHEMA = 1
EVIDENCE = "tests/evidence/publication-2026-10-20"
REPLAY_FILE = "tests/harness/replay-cases.json"
LOG_NAME = "wrapper-calls.log"
TRACE_NAME = "s2-preclear-full-trace.md"
SETUP_SNAPSHOT = "snap-0-setup"
AFTER_SNAPSHOT = "snap-2-after-preclear"
STATUS_BEFORE = "status-before.txt"
WRAPPER_SUFFIX = "wrapper/checkpoint"
HASH_REFERENCE = "<last-show-hash>"
RUN_TOKEN = "<repo>/<run>/project/"

_LINE = re.compile(r"^(\S+) (CALL|EXIT) ?(.*)$")
_TRACE_HEAD = re.compile(r"^### (\d+)\. (\w+) \(([^)]*)\)([^\n]*)\n")
_TRACE_BODY = re.compile(r"```\n(.*?)\n```\nresult:\n```\n(.*?)\n?```\n?\Z", re.S)
_BOUND = re.compile(r"^session \S+ → (.+?)(?: \(carried from [^)]*\))?$")


class MineError(Exception):
    """The committed evidence does not have the shape the miner expects."""


def parse_log(text: str) -> list:
    """Return [{"argv": [...], "exit": n}] in file line order.

    Every CALL line must be followed by exactly one EXIT line before the next
    CALL. Order is line order, never timestamp order, so two calls in the same
    UTC second keep their order.
    """
    calls = []
    pending = None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = _LINE.match(line)
        if match is None:
            raise MineError("log line %d is not a CALL or EXIT line" % number)
        kind, rest = match.group(2), match.group(3)
        if kind == "CALL":
            if pending is not None:
                raise MineError("log line %d: CALL without an EXIT before it" % number)
            try:
                argv = shlex.split(rest)
            except ValueError as exc:
                raise MineError("log line %d: argv does not split: %s" % (number, exc))
            pending = {"argv": argv}
        else:
            if pending is None:
                raise MineError("log line %d: EXIT without a CALL" % number)
            if not re.fullmatch(r"\d+", rest.strip()):
                raise MineError("log line %d: EXIT code is not a number" % number)
            pending["exit"] = int(rest.strip())
            calls.append(pending)
            pending = None
    if pending is not None:
        raise MineError("log ends with a CALL that has no EXIT")
    return calls


def parse_trace(text: str) -> list:
    """Return the Bash calls of a full trace, in file order.

    Each record has number (the heading number), bash_index (1-based among the
    Bash calls), refusal (the REFUSAL/DENIAL marker is present), command and
    result.
    """
    calls = []
    for part in re.split(r"(?m)^(?=### \d+\. )", text):
        head = _TRACE_HEAD.match(part)
        if head is None or head.group(2) != "Bash":
            continue
        body = _TRACE_BODY.match(part[head.end():])
        if body is None:
            continue
        calls.append(
            {
                "number": int(head.group(1)),
                "bash_index": len(calls) + 1,
                "refusal": "REFUSAL/DENIAL" in head.group(4),
                "command": body.group(1),
                "result": body.group(2),
            }
        )
    return calls


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _sorted_names(folder: str) -> list:
    return sorted(os.listdir(folder), key=os.fsencode)


def _rel(repo_root: str, path: str) -> str:
    return os.path.relpath(path, repo_root).replace(os.sep, "/")


def _match_trace(trace_calls: list, argv: list, cursor: int):
    """First unflagged trace call after cursor whose wrapper argv equals argv."""
    for record in trace_calls:
        if record["bash_index"] <= cursor or record["refusal"]:
            continue
        try:
            tokens = shlex.split(record["command"])
        except ValueError:
            continue
        if tokens and tokens[0].endswith(WRAPPER_SUFFIX) and tokens[1:] == argv:
            return record
    return None


def _annotate_argv(argv: list):
    """Return (recorded argv, refs, inputs) for one logged argv.

    The value after --expect-section is a hash that belongs to a sanitised
    section, so it is recorded as a reference to the last show output. The value
    after --from is an input file; the committed source is the snapshot copy.
    """
    recorded = list(argv)
    refs = []
    inputs = []
    section = None
    for index, token in enumerate(argv):
        if token == "--section" and index + 1 < len(argv):
            section = argv[index + 1]
        if token == "--expect-section" and index + 1 < len(argv):
            recorded[index + 1] = HASH_REFERENCE
            refs.append({"index": index + 1, "kind": "last-show", "section": section})
        if token == "--from" and index + 1 < len(argv):
            value = argv[index + 1]
            after = None
            if value.startswith(RUN_TOKEN + ".preclear/"):
                after = value[len(RUN_TOKEN) + len(".preclear/"):]
            elif value.startswith(".preclear/"):
                after = value[len(".preclear/"):]
            if after is not None:
                inputs.append(
                    {
                        "index": index + 1,
                        "replay_path": ".preclear/" + after,
                        "_after": after,
                    }
                )
    return recorded, refs, inputs


def _bound_basename(first_line: str):
    if first_line.endswith(": unbound"):
        return None
    match = _BOUND.match(first_line)
    if match is None:
        return None
    return match.group(1).replace("\\", "/").rsplit("/", 1)[-1]


def mine_row(repo_root: str, row: str) -> dict:
    folder = os.path.join(repo_root, *EVIDENCE.split("/"), row)
    log_path = os.path.join(folder, LOG_NAME)
    calls = parse_log(_read_text(log_path))
    session_file = os.path.join(folder, "session.id")
    if not os.path.isfile(session_file):
        raise MineError("%s has no session.id" % row)
    session_id = _read_text(session_file).strip()
    writer2_file = os.path.join(folder, "writer2.session")
    writer2 = _read_text(writer2_file).strip() if os.path.isfile(writer2_file) else None
    setup = os.path.join(folder, SETUP_SNAPSHOT)
    after = os.path.join(folder, AFTER_SNAPSHOT)
    ledgers = []
    if os.path.isdir(setup):
        for name in _sorted_names(setup):
            if name.startswith("CONTINUITY_CLAUDE-") and name.endswith(".md"):
                ledgers.append(name)
    conflicts = []
    if os.path.isdir(after):
        for name in _sorted_names(after):
            if ".md.conflict-" in name and name.endswith(".md"):
                conflicts.append(_rel(repo_root, os.path.join(after, name)))

    status_before = os.path.join(folder, STATUS_BEFORE)
    has_status_before = os.path.isfile(status_before)
    trace_path = os.path.join(folder, TRACE_NAME)
    trace_calls = parse_trace(_read_text(trace_path)) if os.path.isfile(trace_path) else []

    mined_calls = []
    bound = None
    bound_known = False
    cursor = 0
    if has_status_before:
        first = _read_text(status_before).split("\n", 1)[0]
        bound = _bound_basename(first)
        bound_known = True
    for position, call in enumerate(calls, 1):
        argv = call["argv"]
        recorded, refs, inputs = _annotate_argv(argv)
        for item in inputs:
            after_part = item.pop("_after")
            item["source"] = "%s/%s/preclear/%s" % (
                _rel(repo_root, folder), AFTER_SNAPSHOT, after_part
            )
        matched = _match_trace(trace_calls, argv, cursor)
        if matched is not None:
            cursor = matched["bash_index"]
        if argv == ["status"] and has_status_before:
            output = {"kind": "status-before", "path": _rel(repo_root, status_before)}
        elif matched is not None:
            output = {
                "kind": "trace",
                "path": _rel(repo_root, trace_path),
                "bash_index": matched["bash_index"],
                "trace_number": matched["number"],
            }
        else:
            output = {"kind": "none"}
        if argv == ["status"] and not bound_known and matched is not None:
            bound = _bound_basename(matched["result"].split("\n", 1)[0])
            bound_known = True
        mined_calls.append(
            {
                "position": position,
                "argv": recorded,
                "exit": call["exit"],
                "refs": refs,
                "inputs": inputs,
                "output": output,
            }
        )
    return {
        "row": row,
        "log": _rel(repo_root, log_path),
        "session_id": session_id,
        "writer2_session": writer2,
        "setup_snapshot": _rel(repo_root, setup),
        "ledgers": ledgers,
        "bound_ledger": bound,
        "conflict_files": conflicts,
        "calls": mined_calls,
    }


def mine(repo_root: str) -> dict:
    base = os.path.join(repo_root, *EVIDENCE.split("/"))
    if not os.path.isdir(base):
        raise MineError("evidence folder is missing")
    rows = []
    for name in _sorted_names(base):
        folder = os.path.join(base, name)
        if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, LOG_NAME)):
            rows.append(name)
    cases = [mine_row(repo_root, row) for row in rows]
    non_empty = sum(1 for case in cases if case["calls"])
    return {
        "schema": SCHEMA,
        "source": EVIDENCE,
        "inventory": {
            "logs": len(cases),
            "non_empty": non_empty,
            "empty": len(cases) - non_empty,
            "calls": sum(len(case["calls"]) for case in cases),
        },
        "cases": cases,
    }


def canonical_json(obj) -> bytes:
    """Sorted keys, two-space indent, ASCII only, one trailing newline."""
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True)
    return (text + "\n").encode("ascii")


def repo_root_from_file() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def main(argv: list) -> int:
    args = argv[1:]
    if args not in ([], ["--check"]):
        sys.stderr.write("usage: pc_mine.py [--check]\n")
        return 2
    root = repo_root_from_file()
    try:
        data = canonical_json(mine(root))
    except (MineError, OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("pc_mine: %s: %s\n" % (type(exc).__name__, exc))
        return 2
    if not args:
        sys.stdout.buffer.write(data)
        return 0
    try:
        with open(os.path.join(root, *REPLAY_FILE.split("/")), "rb") as handle:
            committed = handle.read()
    except OSError as exc:
        sys.stderr.write("pc_mine: cannot read the committed copy: %s\n" % type(exc).__name__)
        return 2
    if committed == data:
        return 0
    sys.stderr.write("pc_mine: replay-cases.json differs from a fresh mine\n")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
