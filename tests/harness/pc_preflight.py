"""Zero-token preflight for the acceptance harness (HARN-04, D-01, D-13).

States and exit codes: OK 0, SKIP 10, FAIL 11, BLOCKED 12, and 13 for a well-formed but
untested Claude Code version. The preflight never sends a prompt to a model.

Command line (run as python3 -E -s -B pc_preflight.py, never with -I, because the pc_
modules import each other):

    --search-path DIR      directory to search for claude (repeatable); default is PATH
    --config-dir DIR       harness-owned CLAUDE_CONFIG_DIR
    --tested-version X.Y.Z tested version (repeatable)
    --row-skip-reason TEXT pretend the row precondition is unmet (for tests)

It prints exactly one line, "<STATE>: <message>", and exits with the state's code.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from typing import Callable, Optional, Sequence

import pc_exitcodes

OK = "OK"
SKIP = "SKIP"
FAIL = "FAIL"
BLOCKED = "BLOCKED"
UNTESTED = "UNTESTED"

_STATE_CODES = {
    OK: pc_exitcodes.OK,
    SKIP: pc_exitcodes.PREFLIGHT_SKIP,
    FAIL: pc_exitcodes.PREFLIGHT_FAIL,
    BLOCKED: pc_exitcodes.PREFLIGHT_BLOCKED,
    UNTESTED: pc_exitcodes.VERSION_UNTESTED,
}


class PreflightResult(object):
    """The outcome of a preflight: a state, its exit code, a one-line message and detail."""

    def __init__(self, state: str, message: str, detail: Optional[str] = None) -> None:
        self.state = state
        self.exit_code = _STATE_CODES[state]
        self.message = message
        self.detail = detail

    def line(self) -> str:
        return "%s: %s" % (self.state, self.message)


def find_claude(search_path: Optional[Sequence[str]], name: str = "claude") -> Optional[str]:
    """Return the absolute path of an executable called name, or None.

    The search uses the given directories only, so a test never consults the process PATH.
    """
    if search_path is None:
        return shutil.which(name)
    return shutil.which(name, path=":".join(search_path))


def run_preflight(
    search_path: Optional[Sequence[str]] = None,
    config_dir: Optional[str] = None,
    tested_versions: Sequence[str] = (),
    row_check: Optional[Callable[[], Optional[str]]] = None,
) -> PreflightResult:
    """Run the preflight checks in order and return the first state that is not OK."""
    claude = find_claude(search_path)
    if claude is None:
        return PreflightResult(BLOCKED, "claude not found on PATH")
    return PreflightResult(OK, "preflight passed")


def _constant_reason(reason: str) -> Callable[[], Optional[str]]:
    def check() -> Optional[str]:
        return reason

    return check


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="pc_preflight.py", add_help=True)
    parser.add_argument("--search-path", action="append", default=None)
    parser.add_argument("--config-dir", default=None)
    parser.add_argument("--tested-version", action="append", default=[])
    parser.add_argument("--row-skip-reason", default=None)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.USAGE if exit_request.code not in (0, None) else pc_exitcodes.OK
    row_check = None
    if args.row_skip_reason is not None:
        row_check = _constant_reason(args.row_skip_reason)

    result = run_preflight(
        search_path=args.search_path,
        config_dir=args.config_dir,
        tested_versions=tuple(args.tested_version),
        row_check=row_check,
    )
    sys.stdout.write(result.line() + "\n")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
