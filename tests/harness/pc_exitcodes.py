"""Named exit codes for the preclear acceptance harness.

Harness codes (every command-line entry point of the pc_ modules uses these):

    0   OK                 success
    2   USAGE              bad command-line usage
    10  PREFLIGHT_SKIP     a row precondition is not met; the row is skipped, never counted as OK
    11  PREFLIGHT_FAIL     claude answered, but the answer is unusable (malformed banner, bad auth output)
    12  PREFLIGHT_BLOCKED  claude is absent or not logged in; nothing can run (also the shim's refusal code)
    13  VERSION_UNTESTED   a well-formed Claude Code version outside the tested set
    14  LEAK_REFUSED       the leak gate found a leak-shaped value and refused
    15  SCANNER_ERROR      the leak scanner itself failed; the result is a refusal, never a pass
    16  RUNROOT_COLLISION  the run root or a file in it already exists
    17  PROMOTE_REFUSED    promote refused to copy into the evidence folder
    18  BUDGET_REFUSED     a budget value is outside the allowed range or shape
    19  DENIAL_FOUND       the stream shows a permission denial, or the stream is incomplete

Stub mirrors (the checkpoint stub's own codes, repeated here so tests assert them by name;
they are not harness codes and may share a number with one, as 0 and 2 do):

    0   STUB_OK            success
    1   STUB_INTERNAL      internal error
    2   STUB_USAGE         bad usage
    3   STUB_CONFLICT      section hash conflict
    4   STUB_INVALID       the ledger is invalid
    5   STUB_KILL_SWITCH   labelled stub-internal switch (UNCONFIRMED against the real build)
    6   STUB_LOCK_TIMEOUT  labelled stub-internal switch (UNCONFIRMED against the real build)
    64  STUB_NO_CKPT_HOME  the stub refuses to run without CKPT_HOME

Harness codes 10 to 19 avoid 0 to 6, 64 and the shell's 124 to 143 range.
"""
from __future__ import annotations

OK = 0
USAGE = 2
PREFLIGHT_SKIP = 10
PREFLIGHT_FAIL = 11
PREFLIGHT_BLOCKED = 12
VERSION_UNTESTED = 13
LEAK_REFUSED = 14
SCANNER_ERROR = 15
RUNROOT_COLLISION = 16
PROMOTE_REFUSED = 17
BUDGET_REFUSED = 18
DENIAL_FOUND = 19

STUB_OK = 0
STUB_INTERNAL = 1
STUB_USAGE = 2
STUB_CONFLICT = 3
STUB_INVALID = 4
STUB_KILL_SWITCH = 5
STUB_LOCK_TIMEOUT = 6
STUB_NO_CKPT_HOME = 64

_HARNESS_MEANINGS = {
    OK: "OK: success",
    USAGE: "USAGE: bad command-line usage",
    PREFLIGHT_SKIP: "PREFLIGHT_SKIP: a row precondition is not met",
    PREFLIGHT_FAIL: "PREFLIGHT_FAIL: claude answered with an unusable result",
    PREFLIGHT_BLOCKED: "PREFLIGHT_BLOCKED: claude is absent or not logged in",
    VERSION_UNTESTED: "VERSION_UNTESTED: a well-formed Claude Code version outside the tested set",
    LEAK_REFUSED: "LEAK_REFUSED: the leak gate refused",
    SCANNER_ERROR: "SCANNER_ERROR: the leak scanner failed",
    RUNROOT_COLLISION: "RUNROOT_COLLISION: the run root or a file in it already exists",
    PROMOTE_REFUSED: "PROMOTE_REFUSED: promote refused to copy into the evidence folder",
    BUDGET_REFUSED: "BUDGET_REFUSED: a budget value was refused",
    DENIAL_FOUND: "DENIAL_FOUND: a permission denial or an incomplete stream",
}

_STUB_ONLY_MEANINGS = {
    STUB_INTERNAL: "stub: internal error",
    STUB_CONFLICT: "stub: section hash conflict",
    STUB_INVALID: "stub: the ledger is invalid",
    STUB_KILL_SWITCH: "stub: labelled kill switch (UNCONFIRMED)",
    STUB_LOCK_TIMEOUT: "stub: lock timeout (UNCONFIRMED)",
    STUB_NO_CKPT_HOME: "stub: refused to run without CKPT_HOME",
}


def describe(code: int) -> str:
    """Return the one-line meaning of an exit code; harness meanings win on shared numbers."""
    if code in _HARNESS_MEANINGS:
        return _HARNESS_MEANINGS[code]
    if code in _STUB_ONLY_MEANINGS:
        return _STUB_ONLY_MEANINGS[code]
    return "unknown exit code %d" % code
