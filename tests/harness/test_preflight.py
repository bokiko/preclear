"""Tests for the exit-code table and the zero-token preflight (HARN-04, D-13).

No test runs a real claude. The only claude executed is a fake script from pc_testutil in a
temporary directory.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

import pc_exitcodes
import pc_preflight

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
PREFLIGHT_SCRIPT = os.path.join(HARNESS_DIR, "pc_preflight.py")


def _constants(prefix_stub: bool) -> dict:
    found = {}
    for name in dir(pc_exitcodes):
        value = getattr(pc_exitcodes, name)
        if name.isupper() and isinstance(value, int) and not isinstance(value, bool):
            if name.startswith("STUB_") == prefix_stub:
                found[name] = value
    return found


class ExitCodeTests(unittest.TestCase):
    def test_harness_constants_are_the_twelve_named_codes(self) -> None:
        expected = {
            "OK": 0,
            "USAGE": 2,
            "PREFLIGHT_SKIP": 10,
            "PREFLIGHT_FAIL": 11,
            "PREFLIGHT_BLOCKED": 12,
            "VERSION_UNTESTED": 13,
            "LEAK_REFUSED": 14,
            "SCANNER_ERROR": 15,
            "RUNROOT_COLLISION": 16,
            "PROMOTE_REFUSED": 17,
            "BUDGET_REFUSED": 18,
            "DENIAL_FOUND": 19,
        }
        self.assertEqual(_constants(False), expected)

    def test_stub_mirrors_are_the_eight_named_codes(self) -> None:
        expected = {
            "STUB_OK": 0,
            "STUB_INTERNAL": 1,
            "STUB_USAGE": 2,
            "STUB_CONFLICT": 3,
            "STUB_INVALID": 4,
            "STUB_KILL_SWITCH": 5,
            "STUB_LOCK_TIMEOUT": 6,
            "STUB_NO_CKPT_HOME": 64,
        }
        self.assertEqual(_constants(True), expected)

    def test_harness_codes_are_pairwise_distinct(self) -> None:
        values = list(_constants(False).values())
        self.assertEqual(len(values), len(set(values)))

    def test_harness_codes_collide_with_no_reserved_range(self) -> None:
        for name, value in _constants(False).items():
            if name in ("OK", "USAGE"):
                continue
            self.assertTrue(10 <= value <= 19, name)
            self.assertNotIn(value, range(0, 7), name)
            self.assertNotEqual(value, 64, name)
            self.assertNotIn(value, range(124, 144), name)

    def test_describe_gives_a_one_line_meaning_for_every_code(self) -> None:
        for value in list(_constants(False).values()) + list(_constants(True).values()):
            text = pc_exitcodes.describe(value)
            self.assertTrue(text)
            self.assertNotIn("\n", text)
        self.assertIn("unknown", pc_exitcodes.describe(99))


class PreflightBlockedTests(unittest.TestCase):
    def test_absent_claude_is_blocked_with_exit_12(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            result = pc_preflight.run_preflight(search_path=[empty])
            self.assertEqual(result.state, "BLOCKED")
            self.assertEqual(result.exit_code, 12)
            self.assertEqual(result.exit_code, pc_exitcodes.PREFLIGHT_BLOCKED)
            self.assertEqual(result.message, "claude not found on PATH")

    def test_cli_prints_exactly_one_line_and_exits_12(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            done = subprocess.run(
                [sys.executable, "-E", "-s", "-B", PREFLIGHT_SCRIPT, "--search-path", empty],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=60,
            )
            self.assertEqual(done.returncode, 12, done.stderr)
            self.assertEqual(done.stdout, "BLOCKED: claude not found on PATH\n")


if __name__ == "__main__":
    unittest.main()
