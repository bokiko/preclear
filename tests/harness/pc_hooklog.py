"""Hook logger for the isolation spike: one JSON line per InstructionsLoaded event (plan 02-08).

Claude Code runs this script as a command hook for the InstructionsLoaded event. The hook payload
arrives on standard input as one JSON object. The script appends one JSON line to the file named
by its first argument, holding exactly the three fields the isolation audit needs: file_path,
memory_type (User, Project, Local or Managed) and load_reason. A field that is absent or is not
text is recorded as null. Nothing else from the payload is copied.

Input that is not one JSON object is recorded as {"error": "unparseable"}.

The script can never block a run: every failure (an unwritable target, a missing argument, a
payload that cannot be read) is swallowed and it always exits 0. It imports no pc_ module, so it
works under python3 -I -B, which is how the settings file starts it:

    <python> -I -B pc_hooklog.py <jsonl path>

The target is opened with O_APPEND and O_CREAT (mode 0600) and never truncated.
"""
from __future__ import annotations

import json
import os
import sys

MAX_PAYLOAD_BYTES = 1024 * 1024
FIELDS = ("file_path", "memory_type", "load_reason")


def build_record(raw: bytes) -> dict:
    """Return the record for one payload: the three fields, or the unparseable marker."""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return {"error": "unparseable"}
    if not isinstance(payload, dict):
        return {"error": "unparseable"}
    record = {}
    for name in FIELDS:
        value = payload.get(name)
        record[name] = value if isinstance(value, str) else None
    return record


def append_line(path: str, record: dict) -> None:
    line = (json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def main(argv) -> int:
    try:
        if len(argv) < 1 or not argv[0]:
            return 0
        raw = sys.stdin.buffer.read(MAX_PAYLOAD_BYTES)
        append_line(argv[0], build_record(raw))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
