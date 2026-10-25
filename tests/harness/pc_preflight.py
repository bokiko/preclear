"""Zero-token preflight for the acceptance harness (HARN-04, D-01, D-03, D-13).

States and exit codes: OK 0, SKIP 10, FAIL 11, BLOCKED 12, and 13 for a well-formed but
untested Claude Code version (state UNTESTED). The preflight never sends a prompt to a model.

Checks, in order:

  1. claude on the search path                      else BLOCKED
  2. the config directory is acceptable             else FAIL (refused by build_env)
  3. claude --version (20 second timeout)           non-zero, empty or malformed output: FAIL
  4. the exact-match version gate                   untested or below the floor: UNTESTED (13)
  5. a harness config directory that exists         else BLOCKED, never a fallback (D-03)
  6. claude auth status --json under build_env      only the boolean loggedIn is read;
                                                    not boolean or not JSON: FAIL;
                                                    false: BLOCKED with the one-time login step
  7. an optional row precondition                   a reason: SKIP, never OK

No credential file is ever opened, and no field of the auth output other than the boolean
loggedIn is stored, logged, printed or returned (D-03, T-02-01).

Command line (run as python3 -E -s -B pc_preflight.py, never with -I, because the pc_
modules import each other):

    --search-path DIR       directory to search for claude (repeatable); default is PATH
    --config-dir DIR        harness-owned CLAUDE_CONFIG_DIR
    --tested-version X.Y.Z  tested version (repeatable); default is pc_flags.TESTED_VERSIONS
    --row-skip-reason TEXT  pretend the row precondition is unmet (for tests)

It prints exactly one line, "<STATE>: <message>", and exits with the state's code.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Callable, Mapping, Optional, Sequence, Tuple

import pc_exitcodes
import pc_flags

OK = "OK"
SKIP = "SKIP"
FAIL = "FAIL"
BLOCKED = "BLOCKED"
UNTESTED = "UNTESTED"

COMMAND_TIMEOUT_SECONDS = 20

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
        self.message = " ".join(message.split("\n"))
        self.detail = detail

    def line(self) -> str:
        return "%s: %s" % (self.state, self.message)


def find_claude(search_path: Optional[Sequence[str]], name: str = "claude") -> Optional[str]:
    """Return the absolute path of an executable called name, or None.

    With search_path the search uses only those directories, so a test never consults the
    process PATH; with None the process PATH is used.
    """
    if search_path is None:
        return shutil.which(name)
    return shutil.which(name, path=os.pathsep.join(search_path))


def _run(argv: Sequence[str], env: Mapping[str, str]) -> Tuple[int, bytes]:
    """Run an argument list (never a shell) and return (exit status, stdout bytes)."""
    done = subprocess.run(
        list(argv),
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=COMMAND_TIMEOUT_SECONDS,
        shell=False,
    )
    return done.returncode, done.stdout


def _login_instruction(config_dir: str) -> str:
    return (
        "the harness is not logged in; run this once, then rerun: "
        "CLAUDE_CONFIG_DIR=%s claude auth login" % config_dir
    )


def run_preflight(
    search_path: Optional[Sequence[str]] = None,
    config_dir: Optional[str] = None,
    tested_versions: Optional[Sequence[str]] = None,
    row_check: Optional[Callable[[], Optional[str]]] = None,
    base_env: Optional[Mapping[str, str]] = None,
) -> PreflightResult:
    """Run the preflight checks in order and return the first state that is not OK."""
    claude = find_claude(search_path)
    if claude is None:
        return PreflightResult(BLOCKED, "claude not found on PATH")

    tested = pc_flags.TESTED_VERSIONS if tested_versions is None else tuple(tested_versions)
    try:
        env = pc_flags.build_env(os.environ if base_env is None else base_env, config_dir)
    except ValueError as problem:
        return PreflightResult(FAIL, "config directory refused: %s" % problem)

    try:
        status, raw = _run([claude, "--version"], env)
    except subprocess.TimeoutExpired:
        return PreflightResult(FAIL, "claude --version timed out")
    except OSError:
        return PreflightResult(FAIL, "claude --version could not be started")
    if status != 0:
        return PreflightResult(FAIL, "claude --version exited with a non-zero status")
    try:
        banner = raw.decode("utf-8")
    except UnicodeDecodeError:
        return PreflightResult(FAIL, "claude --version printed bytes that are not UTF-8")

    verdict = pc_flags.check_version(banner, tested)
    if verdict.status == "MALFORMED":
        return PreflightResult(FAIL, "claude --version printed an empty or unrecognised banner")
    if verdict.status != "TESTED":
        return PreflightResult(
            UNTESTED,
            "Claude Code %s is %s; the tested set is exact-match"
            % (verdict.version, "below the floor" if verdict.status == "BELOW_FLOOR" else "not tested"),
        )

    if config_dir is None:
        return PreflightResult(
            BLOCKED,
            "no harness config directory was given; the harness never falls back to the user's own config",
        )
    if not os.path.isdir(config_dir):
        return PreflightResult(BLOCKED, _login_instruction(config_dir))

    try:
        status, raw = _run([claude, "auth", "status", "--json"], env)
    except subprocess.TimeoutExpired:
        return PreflightResult(FAIL, "claude auth status timed out")
    except OSError:
        return PreflightResult(FAIL, "claude auth status could not be started")
    # Only the boolean loggedIn is read. Everything else in the output is discarded unseen.
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return PreflightResult(FAIL, "claude auth status did not print a JSON object")
    logged_in = parsed.get("loggedIn") if isinstance(parsed, dict) else None
    del parsed
    if not isinstance(logged_in, bool):
        return PreflightResult(FAIL, "claude auth status carried no boolean loggedIn")
    if not logged_in:
        return PreflightResult(BLOCKED, _login_instruction(config_dir))
    if status != 0:
        return PreflightResult(FAIL, "claude auth status exited non-zero while reporting a login")

    if row_check is not None:
        reason = row_check()
        if reason is not None:
            return PreflightResult(SKIP, "SKIPPED: %s" % reason)
    return PreflightResult(OK, "preflight passed for Claude Code %s" % verdict.version)


def _constant_reason(reason: str) -> Callable[[], Optional[str]]:
    def check() -> Optional[str]:
        return reason

    return check


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="pc_preflight.py", add_help=True)
    parser.add_argument("--search-path", action="append", default=None)
    parser.add_argument("--config-dir", default=None)
    parser.add_argument("--tested-version", action="append", default=None)
    parser.add_argument("--row-skip-reason", default=None)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
    row_check = None
    if args.row_skip_reason is not None:
        row_check = _constant_reason(args.row_skip_reason)

    result = run_preflight(
        search_path=args.search_path,
        config_dir=args.config_dir,
        tested_versions=args.tested_version,
        row_check=row_check,
    )
    sys.stdout.write(result.line() + "\n")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
