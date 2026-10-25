"""Test support for the harness suite: fake and tripwire claude, shared-directory layout,
minimal environments and git environment hygiene.

Nothing here ever runs a real claude. The only claude a test executes is a small /bin/sh
script written into a temporary directory by this module. A fake claude answers the two
zero-token commands the preflight uses (--version and auth status --json); any other
argument vector is a violation that is appended to tripwire.log beside the script and ends
with exit status 97. A tripwire claude treats every argument vector as a violation.
"""
from __future__ import annotations

import os
import shlex
import stat
import tempfile
from typing import Dict, Iterable, List, Optional

# A value planted beside loggedIn in the fake auth output. Tests assert it never reaches any
# message, line or return value (D-03). It is deliberately not shaped like an email address.
IDENTITY_SENTINEL = "planted-identity-sentinel-7f3a91"

TRIPWIRE_EXIT = 97
TRIPWIRE_LOG = "tripwire.log"
ENV_LOG = "env.log"

SYSTEM_DIRS = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")

_SCRIPT_HEAD = """#!/bin/sh
# Test double for claude. Never talks to a model.
here=$(cd "$(dirname "$0")" && pwd)
"""

_FAKE_BODY = """case "$*" in
  "--version")
    __VERSION_LINE__
    exit 0
    ;;
  "auth status --json")
    printf '%s|%s|%s\\n' "${CLAUDE_CONFIG_DIR-unset}" "${ANTHROPIC_API_KEY-unset}" "${CLAUDE_CODE_OAUTH_TOKEN-unset}" >> "$here/__ENV_LOG__"
    printf '%s\\n' __AUTH_OUTPUT__
    exit __AUTH_EXIT__
    ;;
esac
printf '%s\\n' "$*" >> "$here/__TRIPWIRE_LOG__"
exit __TRIPWIRE_EXIT__
"""

_TRIPWIRE_BODY = """printf '%s\\n' "$*" >> "$here/__TRIPWIRE_LOG__"
exit __TRIPWIRE_EXIT__
"""


def _write_executable(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_fake_claude(
    directory: str,
    version_banner: str,
    logged_in: bool,
    auth_raw: Optional[str] = None,
) -> str:
    """Write a fake claude into directory and return its path.

    --version prints version_banner (a trailing newline is added when it is not empty).
    auth status --json prints a JSON object whose loggedIn matches logged_in and which also
    carries a planted identity field; the exit status is 0 when logged in and 1 otherwise.
    auth_raw replaces that output verbatim (for the unparseable-output case).
    Any other argument vector goes to tripwire.log and exits 97.
    """
    if auth_raw is None:
        auth_raw = '{"loggedIn": %s, "account": "%s"}' % (
            "true" if logged_in else "false",
            IDENTITY_SENTINEL,
        )
    if version_banner:
        version_line = "printf '%s\\n' " + shlex.quote(version_banner)
    else:
        version_line = ":"
    body = (
        _FAKE_BODY.replace("__VERSION_LINE__", version_line)
        .replace("__AUTH_OUTPUT__", shlex.quote(auth_raw))
        .replace("__AUTH_EXIT__", "0" if logged_in else "1")
        .replace("__ENV_LOG__", ENV_LOG)
        .replace("__TRIPWIRE_LOG__", TRIPWIRE_LOG)
        .replace("__TRIPWIRE_EXIT__", str(TRIPWIRE_EXIT))
    )
    path = os.path.join(directory, "claude")
    _write_executable(path, _SCRIPT_HEAD + body)
    return path


def make_tripwire(directory: str) -> str:
    """Write a claude whose every argument vector is a violation and return its path."""
    body = _TRIPWIRE_BODY.replace("__TRIPWIRE_LOG__", TRIPWIRE_LOG).replace(
        "__TRIPWIRE_EXIT__", str(TRIPWIRE_EXIT)
    )
    path = os.path.join(directory, "claude")
    _write_executable(path, _SCRIPT_HEAD + body)
    return path


def read_tripwire(directory: str) -> List[str]:
    """Return the logged violation lines (empty list when nothing fired)."""
    path = os.path.join(directory, TRIPWIRE_LOG)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def read_env_log(directory: str) -> List[str]:
    """Return the lines the fake claude logged for auth status calls."""
    path = os.path.join(directory, ENV_LOG)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def make_shared_dir(directory: str, python3_path: str, git_path: str) -> str:
    """Build the layout a stranger may have: claude, python3 and git in one folder.

    python3 and git are linked by absolute path next to a tripwire claude. Removing that
    folder from PATH must not cost the suite its interpreter or git.
    """
    os.makedirs(directory, exist_ok=True)
    os.symlink(os.path.abspath(python3_path), os.path.join(directory, "python3"))
    os.symlink(os.path.abspath(git_path), os.path.join(directory, "git"))
    make_tripwire(directory)
    return directory


def minimal_env(path_dirs: Iterable[str]) -> Dict[str, str]:
    """Return an environment holding only PATH, HOME and LANG.

    PATH is the given directories followed by the system directories. HOME points at a
    fresh temporary directory so a test never reads the caller's real home.
    """
    home = tempfile.mkdtemp(prefix="pc-home-")
    return {
        "PATH": os.pathsep.join(list(path_dirs) + list(SYSTEM_DIRS)),
        "HOME": home,
        "LANG": "en_US.UTF-8",
    }


def git_env(base: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of base with git environment hygiene and a placeholder identity.

    The machine's global git configuration must not influence any result, and the identity
    uses a reserved example domain so nothing personal is ever committed by a test.
    """
    env = dict(base)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    env["GIT_AUTHOR_NAME"] = "Harness Test"
    env["GIT_AUTHOR_EMAIL"] = "harness-test@example.com"
    env["GIT_COMMITTER_NAME"] = "Harness Test"
    env["GIT_COMMITTER_EMAIL"] = "harness-test@example.com"
    return env
