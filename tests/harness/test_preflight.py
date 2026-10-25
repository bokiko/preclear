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
import pc_flags
import pc_preflight
import pc_testutil

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


TESTED = ("2.1.310",)
GOOD_BANNER = "2.1.310 (Claude Code)"


class _FakeClaudeCase(unittest.TestCase):
    """Base: a temporary directory holding a fake claude and a harness config directory."""

    def setUp(self) -> None:
        self.parent = tempfile.mkdtemp(prefix="pc-preflight-")
        self.bin_dir = os.path.join(self.parent, "bin")
        self.config_dir = os.path.join(self.parent, "config")
        os.makedirs(self.bin_dir)
        os.makedirs(self.config_dir)
        self.base_env = {"PATH": os.pathsep.join(["/usr/bin", "/bin"]), "HOME": self.parent}

    def run_pre(self, row_check=None, tested=TESTED, config_dir="default", base_env=None):
        return pc_preflight.run_preflight(
            search_path=[self.bin_dir],
            config_dir=self.config_dir if config_dir == "default" else config_dir,
            tested_versions=tested,
            row_check=row_check,
            base_env=self.base_env if base_env is None else base_env,
        )

    def assert_clean(self, result) -> None:
        text = "%s|%s|%s" % (result.message, result.detail, result.line())
        self.assertFalse(pc_testutil.IDENTITY_SENTINEL in text, "identity field leaked")
        self.assertEqual(pc_testutil.read_tripwire(self.bin_dir), [])


class PreflightStateTests(_FakeClaudeCase):
    def test_listed_version_and_logged_in_is_ok(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        result = self.run_pre()
        self.assertEqual((result.state, result.exit_code), ("OK", 0))
        self.assert_clean(result)

    def test_untested_version_is_13(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, "2.1.311 (Claude Code)", True)
        result = self.run_pre()
        self.assertEqual(result.exit_code, 13)
        self.assertEqual(result.exit_code, pc_exitcodes.VERSION_UNTESTED)
        self.assert_clean(result)

    def test_empty_tested_set_refuses_every_real_version(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        self.assertEqual(self.run_pre(tested=()).exit_code, 13)

    def test_below_floor_version_is_13(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, "2.1.301 (Claude Code)", True)
        self.assertEqual(self.run_pre(tested=()).exit_code, 13)

    def test_not_logged_in_is_blocked_with_the_login_instruction(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, False)
        result = self.run_pre()
        self.assertEqual((result.state, result.exit_code), ("BLOCKED", 12))
        self.assertTrue("auth login" in result.message)
        self.assertTrue("CLAUDE_CONFIG_DIR=" in result.message)
        self.assertTrue(self.config_dir in result.message)
        self.assert_clean(result)

    def test_unparseable_auth_output_is_fail(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True, auth_raw="this is not json")
        result = self.run_pre()
        self.assertEqual((result.state, result.exit_code), ("FAIL", 11))
        self.assert_clean(result)

    def test_non_boolean_logged_in_is_fail(self) -> None:
        raw = '{"loggedIn": "yes", "account": "%s"}' % pc_testutil.IDENTITY_SENTINEL
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True, auth_raw=raw)
        result = self.run_pre()
        self.assertEqual(result.exit_code, 11)
        self.assert_clean(result)

    def test_non_object_auth_output_is_fail(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True, auth_raw="[true]")
        self.assertEqual(self.run_pre().exit_code, 11)

    def test_empty_banner_is_fail(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, "", True)
        self.assertEqual(self.run_pre().exit_code, 11)

    def test_garbage_banner_is_fail(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, "garbage", True)
        self.assertEqual(self.run_pre().exit_code, 11)

    def test_row_precondition_not_met_is_skip_and_never_ok(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        result = self.run_pre(row_check=lambda: "the row needs a fixture that is absent")
        self.assertEqual((result.state, result.exit_code), ("SKIP", 10))
        self.assertTrue(result.message.startswith("SKIPPED:"))
        self.assertNotEqual(result.exit_code, 0)

    def test_row_precondition_met_stays_ok(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        self.assertEqual(self.run_pre(row_check=lambda: None).exit_code, 0)

    def test_missing_config_dir_is_blocked_and_never_falls_back(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        self.assertEqual(self.run_pre(config_dir=None).exit_code, 12)
        missing = os.path.join(self.parent, "does-not-exist")
        self.assertEqual(self.run_pre(config_dir=missing).exit_code, 12)
        self.assertEqual(pc_testutil.read_env_log(self.bin_dir), [])

    def test_config_dir_inside_the_repository_is_fail_and_claude_is_not_asked(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        inside = os.path.join(os.path.dirname(HARNESS_DIR), "scratch-config-dir")
        self.assertEqual(self.run_pre(config_dir=inside).exit_code, 11)
        self.assertEqual(pc_testutil.read_env_log(self.bin_dir), [])

    def test_auth_status_runs_under_the_scrubbed_environment(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        noisy = dict(self.base_env)
        noisy["ANTHROPIC_API_KEY"] = "sentinel-key"
        noisy["CLAUDE_CODE_OAUTH_TOKEN"] = "sentinel-token"
        self.assertEqual(self.run_pre(base_env=noisy).exit_code, 0)
        lines = pc_testutil.read_env_log(self.bin_dir)
        self.assertEqual(lines, ["%s|unset|unset" % self.config_dir])

    def test_default_tested_set_is_the_flags_module_set(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        result = pc_preflight.run_preflight(
            search_path=[self.bin_dir],
            config_dir=self.config_dir,
            base_env=self.base_env,
        )
        expected = 0 if "2.1.310" in pc_flags.TESTED_VERSIONS else 13
        self.assertEqual(result.exit_code, expected)


class PreflightCliTests(_FakeClaudeCase):
    def _run_cli(self, *extra: str):
        return subprocess.run(
            [sys.executable, "-E", "-s", "-B", PREFLIGHT_SCRIPT, "--search-path", self.bin_dir]
            + list(extra),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
            env=self.base_env,
        )

    def test_one_line_per_state_and_no_identity_leak(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, True)
        done = self._run_cli("--config-dir", self.config_dir, "--tested-version", "2.1.310")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(len(done.stdout.splitlines()), 1)
        self.assertTrue(done.stdout.startswith("OK: "))
        self.assertFalse(pc_testutil.IDENTITY_SENTINEL in done.stdout + done.stderr)

        done = self._run_cli("--config-dir", self.config_dir)
        self.assertEqual(done.returncode, 13)
        self.assertTrue(done.stdout.startswith("UNTESTED: "))

        done = self._run_cli(
            "--config-dir", self.config_dir, "--tested-version", "2.1.310", "--row-skip-reason", "no fixture"
        )
        self.assertEqual(done.returncode, 10)
        self.assertEqual(done.stdout, "SKIP: SKIPPED: no fixture\n")

    def test_logged_out_cli_exit_12_and_identity_never_printed(self) -> None:
        pc_testutil.make_fake_claude(self.bin_dir, GOOD_BANNER, False)
        done = self._run_cli("--config-dir", self.config_dir, "--tested-version", "2.1.310")
        self.assertEqual(done.returncode, 12)
        self.assertEqual(len(done.stdout.splitlines()), 1)
        self.assertFalse(pc_testutil.IDENTITY_SENTINEL in done.stdout + done.stderr)

    def test_bad_usage_exits_2(self) -> None:
        done = self._run_cli("--no-such-option")
        self.assertEqual(done.returncode, 2)


if __name__ == "__main__":
    unittest.main()
