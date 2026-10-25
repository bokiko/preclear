"""Tests for tests/harness/selftest, the stranger's first command (EVID-07, D-10, D-13).

Every test runs the shim in a subprocess with a private PATH. The only claude that ever
exists is a tripwire script in a temporary directory; the tests prove it is removed from the
child's PATH and never executed. The nested run is narrowed with PC_SELFTEST_PATTERN so it
cannot recurse into this module.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from typing import Dict, List

import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HARNESS_DIR, "selftest")
BANNER = re.compile(r"^preclear harness self-test: 0 model calls; claude directories removed from PATH: (\d+)$", re.M)
NESTED_PATTERN = "test_preflight.py"


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise unittest.SkipTest("%s is not available on this machine" % name)
    return path


def _run_shim(env: Dict[str, str], via_bash: bool = False) -> "subprocess.CompletedProcess[str]":
    if not os.path.isfile(SHIM):
        raise AssertionError("the shim is missing")
    command: List[str] = ["/bin/bash", SHIM] if via_bash else [SHIM]
    merged = dict(env)
    merged["PC_SELFTEST_PATTERN"] = NESTED_PATTERN
    return subprocess.run(
        command,
        env=merged,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        timeout=180,
        cwd=tempfile.gettempdir(),
    )


def _dirs_holding_claude(path_value: str) -> int:
    count = 0
    for entry in path_value.split(os.pathsep):
        if not entry:
            continue
        candidate = os.path.join(entry, "claude")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            count += 1
    return count


class ShimTracerTests(unittest.TestCase):
    def test_shim_is_executable(self) -> None:
        self.assertTrue(os.path.isfile(SHIM), "the shim is missing")
        self.assertTrue(os.access(SHIM, os.X_OK), "the shim is not executable")

    def test_tripwire_first_on_path_never_runs_and_suite_is_green(self) -> None:
        python3 = _tool("python3")
        git = _tool("git")
        with tempfile.TemporaryDirectory() as parent:
            wire = os.path.join(parent, "wire")
            tools = os.path.join(parent, "tools")
            os.makedirs(wire)
            os.makedirs(tools)
            pc_testutil.make_tripwire(wire)
            os.symlink(python3, os.path.join(tools, "python3"))
            os.symlink(git, os.path.join(tools, "git"))
            env = pc_testutil.minimal_env([wire, tools])
            result = _run_shim(env)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertRegex(result.stdout, BANNER)
            self.assertRegex(result.stdout, r"(?m)^OK")
            self.assertNotIn("Ran 0 tests", result.stdout)
            self.assertEqual(pc_testutil.read_tripwire(wire), [])

    def test_empty_path_directory_exits_12_and_names_python3(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            env = {"PATH": empty, "HOME": empty, "LANG": "en_US.UTF-8"}
            result = _run_shim(env, via_bash=True)
            self.assertEqual(result.returncode, 12, result.stdout)
            self.assertIn("python3", result.stdout)

    def test_shared_dir_claude_python3_and_git_together_suite_still_green(self) -> None:
        python3 = _tool("python3")
        git = _tool("git")
        with tempfile.TemporaryDirectory() as parent:
            shared = pc_testutil.make_shared_dir(os.path.join(parent, "shared"), python3, git)
            env = pc_testutil.minimal_env([shared])
            expected_removed = _dirs_holding_claude(env["PATH"])
            result = _run_shim(env, via_bash=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            match = BANNER.search(result.stdout)
            self.assertIsNotNone(match, result.stdout)
            assert match is not None
            self.assertEqual(int(match.group(1)), expected_removed)
            self.assertGreaterEqual(int(match.group(1)), 1)
            self.assertRegex(result.stdout, r"(?m)^OK")
            self.assertNotIn("Ran 0 tests", result.stdout)
            self.assertEqual(pc_testutil.read_tripwire(shared), [])

    def test_shared_dir_missing_git_exits_12_and_names_git(self) -> None:
        python3 = _tool("python3")
        with tempfile.TemporaryDirectory() as only_python:
            os.symlink(python3, os.path.join(only_python, "python3"))
            env = {"PATH": only_python, "HOME": only_python, "LANG": "en_US.UTF-8"}
            result = _run_shim(env, via_bash=True)
            self.assertEqual(result.returncode, 12, result.stdout)
            self.assertIn("git", result.stdout)


if __name__ == "__main__":
    unittest.main()
