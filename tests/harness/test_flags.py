"""Tests for pc_flags: the pinned claude -p contract (HARN-04, HARN-06, D-02, D-03, D-04, D-05).

No test runs a real claude. Leak-shaped strings are never written as literals; paths that
the code must refuse are built at run time from the repository location and a patched HOME.
"""
from __future__ import annotations

import os
import re
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import pc_flags

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
TOOLS_TXT = os.path.join(
    REPO_ROOT,
    "tests",
    "evidence",
    "publication-2026-10-20",
    "row10-large-status-rerun",
    "tools.txt",
)
SESSION_ID = "0b1f2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
CLAUDE = os.path.join(os.sep, "opt", "fake", "claude")
SETTINGS = os.path.join(os.sep, "opt", "fake", "settings.json")
WRAPPER = os.path.join(os.sep, "opt", "fake", "wrapper")


def _argv(**overrides):
    params = dict(
        claude_path=CLAUDE,
        session_id=SESSION_ID,
        settings_path=SETTINGS,
        allowed_tools=("Read", "Bash(pwd)"),
        max_turns=12,
        max_budget_usd="1.00",
    )
    params.update(overrides)
    return pc_flags.build_argv(**params)


class BuildArgvTests(unittest.TestCase):
    def test_exact_documented_order(self) -> None:
        self.assertEqual(
            _argv(),
            [
                CLAUDE,
                "-p",
                "--output-format",
                "stream-json",
                "--verbose",
                "--setting-sources",
                "project,local",
                "--settings",
                SETTINGS,
                "--session-id",
                SESSION_ID,
                "--permission-mode",
                "default",
                "--allowedTools",
                "Read,Bash(pwd)",
                "--model",
                "claude-sonnet-5-5",
                "--max-turns",
                "12",
                "--max-budget-usd",
                "1.00",
                "--strict-mcp-config",
                "--effort",
                "high",
            ],
        )

    def test_equal_inputs_give_equal_lists_that_are_independent(self) -> None:
        first = _argv()
        second = _argv()
        self.assertEqual(first, second)
        first.append("mutated")
        self.assertNotEqual(first, second)
        self.assertEqual(_argv(), second)

    def test_allowed_tools_is_one_comma_joined_argument(self) -> None:
        tools = ("Read", "Write", "Bash(ls:*)")
        argv = _argv(allowed_tools=tools)
        position = argv.index("--allowedTools")
        self.assertEqual(argv[position + 1], ",".join(tools))
        for tool in tools:
            self.assertNotIn(tool, argv)

    def test_prompt_and_unsafe_flags_never_appear(self) -> None:
        argv = _argv(include_hook_events=True)
        for banned in ("--bare", "--dangerously-skip-permissions", "--safe-mode", "--restricted"):
            self.assertNotIn(banned, argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "default")
        self.assertEqual(argv[-1], "--include-hook-events")

    def test_resume_replaces_session_id(self) -> None:
        argv = _argv(resume=True)
        self.assertIn("--resume", argv)
        self.assertNotIn("--session-id", argv)
        self.assertEqual(argv[argv.index("--resume") + 1], SESSION_ID)

    def test_invalid_inputs_raise_value_error(self) -> None:
        bad_cases = [
            dict(session_id=SESSION_ID.upper()),
            dict(session_id="{" + SESSION_ID + "}"),
            dict(session_id="not-a-uuid"),
            dict(settings_path="settings.json"),
            dict(claude_path="claude"),
            dict(allowed_tools=()),
            dict(allowed_tools=("Read,Write",)),
            dict(allowed_tools=("Read", "Read")),
            dict(allowed_tools="Read"),
            dict(max_turns=0),
            dict(max_turns=101),
            dict(max_turns=True),
            dict(max_turns="5"),
            dict(max_budget_usd="0"),
        ]
        for overrides in bad_cases:
            with self.assertRaises(ValueError, msg=str(sorted(overrides))):
                _argv(**overrides)


class FormatBudgetTests(unittest.TestCase):
    def test_accepted_values_have_exactly_two_decimals(self) -> None:
        self.assertEqual(pc_flags.format_budget("1.00"), "1.00")
        self.assertEqual(pc_flags.format_budget("0.50"), "0.50")
        self.assertEqual(pc_flags.format_budget("2.5"), "2.50")
        self.assertEqual(pc_flags.format_budget(Decimal("5.00")), "5.00")
        self.assertEqual(pc_flags.format_budget(Decimal("0.01")), "0.01")

    def test_refused_values(self) -> None:
        refused = [
            "0",
            "0.00",
            "-1.00",
            "5.01",
            "0.123",
            "1.000",
            " 1.00",
            "1.00 ",
            "1e0",
            "",
            "abc",
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("0.123"),
            Decimal("-1.00"),
            1.0,
            1,
            True,
            None,
        ]
        for value in refused:
            with self.assertRaises(ValueError, msg=repr(value)):
                pc_flags.format_budget(value)


class VersionGateTests(unittest.TestCase):
    TESTED = ("2.1.310",)

    def test_listed_version_passes(self) -> None:
        verdict = pc_flags.check_version("2.1.310 (Claude Code)", self.TESTED)
        self.assertEqual(verdict.status, "TESTED")
        self.assertEqual(verdict.version, "2.1.310")
        self.assertEqual(pc_flags.check_version("2.1.310 (Claude Code)\n", self.TESTED).status, "TESTED")

    def test_neighbours_and_variants_are_refused(self) -> None:
        untested = [
            "2.1.309 (Claude Code)",
            "2.1.311 (Claude Code)",
            "2.2.310 (Claude Code)",
            "3.1.310 (Claude Code)",
        ]
        for banner in untested:
            self.assertEqual(pc_flags.check_version(banner, self.TESTED).status, "UNTESTED", banner)
        malformed = [
            "2.1.310-beta (Claude Code)",
            " 2.1.310 (Claude Code)",
            "2.1.310 (Claude Code) ",
            "v2.1.310 (Claude Code)",
            "2.1.310 (Claude Code)\n\n",
            "2.1.310",
            "",
            "garbage",
        ]
        for banner in malformed:
            verdict = pc_flags.check_version(banner, self.TESTED)
            self.assertEqual(verdict.status, "MALFORMED", repr(banner))
            self.assertIsNone(verdict.version)

    def test_below_floor_is_its_own_class(self) -> None:
        verdict = pc_flags.check_version("2.1.301 (Claude Code)", self.TESTED)
        self.assertEqual(verdict.status, "BELOW_FLOOR")
        self.assertEqual(verdict.version, "2.1.301")

    def test_empty_tested_set_passes_nothing(self) -> None:
        self.assertEqual(pc_flags.check_version("2.1.310 (Claude Code)", ()).status, "UNTESTED")

    def test_tested_versions_is_a_tuple_of_dotted_triples(self) -> None:
        self.assertIsInstance(pc_flags.TESTED_VERSIONS, tuple)
        for item in pc_flags.TESTED_VERSIONS:
            self.assertRegex(item, r"^[0-9]+\.[0-9]+\.[0-9]+$")

    def test_parse_banner_accepts_only_the_exact_shape(self) -> None:
        self.assertEqual(pc_flags.parse_banner("2.1.310 (Claude Code)"), "2.1.310")
        with self.assertRaises(ValueError):
            pc_flags.parse_banner("2.1.310 (Claude Code) extra")


class BuildEnvTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = tempfile.mkdtemp(prefix="pc-flags-")
        self.config_dir = os.path.join(self.parent, "config")
        os.makedirs(self.config_dir)

    def test_secrets_never_reach_the_child(self) -> None:
        base = {
            "PATH": "/usr/bin",
            "HOME": self.parent,
            "ANTHROPIC_API_KEY": "sentinel-a",
            "ANTHROPIC_AUTH_TOKEN": "sentinel-b",
            "CLAUDE_CODE_OAUTH_TOKEN": "sentinel-c",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_SESSION_ID": "sentinel-d",
            "AWS_SECRET_ACCESS_KEY": "sentinel-e",
            "AWS_ACCESS_KEY_ID": "sentinel-f",
            "GITHUB_TOKEN": "sentinel-g",
            "GH_TOKEN": "sentinel-h",
        }
        env = pc_flags.build_env(base, self.config_dir, None)
        for name in base:
            if name not in ("PATH", "HOME"):
                self.assertNotIn(name, env)
        self.assertNotIn("sentinel", " ".join(env.values()))

    def test_fixed_variables_are_set(self) -> None:
        env = pc_flags.build_env({"PATH": "/usr/bin"}, self.config_dir, os.path.join(self.parent, "ckpt"))
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], self.config_dir)
        self.assertEqual(env["DISABLE_AUTOUPDATER"], "1")
        self.assertEqual(env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"], "1")
        self.assertEqual(env["CKPT_HOME"], os.path.join(self.parent, "ckpt"))

    def test_keys_stay_inside_the_allow_list(self) -> None:
        allowed = {
            "PATH",
            "HOME",
            "USER",
            "LOGNAME",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "TMPDIR",
            "TERM",
            "CLAUDE_CONFIG_DIR",
            "DISABLE_AUTOUPDATER",
            "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB",
            "CKPT_HOME",
        }
        base = {name: "x" for name in allowed}
        base["EXTRA_VARIABLE"] = "y"
        env = pc_flags.build_env(base, self.config_dir, os.path.join(self.parent, "ckpt"))
        self.assertTrue(set(env) <= allowed)
        self.assertNotIn("EXTRA_VARIABLE", env)

    def test_ckpt_home_is_omitted_when_not_given(self) -> None:
        env = pc_flags.build_env({"PATH": "/usr/bin"}, self.config_dir, None)
        self.assertNotIn("CKPT_HOME", env)

    def test_config_dir_inside_the_repository_is_refused(self) -> None:
        inside = os.path.join(REPO_ROOT, "scratch-config-dir")
        with self.assertRaises(ValueError):
            pc_flags.build_env({"PATH": "/usr/bin"}, inside, None)

    def test_config_dir_under_the_users_own_claude_directory_is_refused(self) -> None:
        fake_home = os.path.join(self.parent, "fake-home")
        own = os.path.join(fake_home, ".claude", "harness")
        with mock.patch.dict(os.environ, {"HOME": fake_home}):
            with self.assertRaises(ValueError):
                pc_flags.build_env({"PATH": "/usr/bin"}, own, None)
            with self.assertRaises(ValueError):
                pc_flags.build_env({"PATH": "/usr/bin"}, os.path.join(fake_home, ".claude"), None)
            # A sibling outside that directory is fine.
            pc_flags.build_env({"PATH": "/usr/bin"}, os.path.join(fake_home, ".claude-harness"), None)

    def test_relative_config_dir_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            pc_flags.build_env({"PATH": "/usr/bin"}, "relative/config", None)

    def test_refusal_messages_do_not_echo_the_path(self) -> None:
        inside = os.path.join(REPO_ROOT, "scratch-config-dir")
        try:
            pc_flags.build_env({"PATH": "/usr/bin"}, inside, None)
        except ValueError as problem:
            self.assertNotIn(REPO_ROOT, str(problem))
        else:
            self.fail("expected a refusal")


class AllowedToolsTests(unittest.TestCase):
    def test_baseline_equals_the_committed_row10_rerun_list(self) -> None:
        with open(TOOLS_TXT, "r", encoding="utf-8") as handle:
            committed = handle.read().strip().split(",")
        self.assertEqual(len(pc_flags.BASELINE_ALLOWED_TOOLS), 33)
        self.assertEqual(list(pc_flags.BASELINE_ALLOWED_TOOLS), committed)

    def test_one_rule_per_model_facing_verb_appended_to_the_baseline(self) -> None:
        tools = pc_flags.build_allowed_tools(WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        baseline = pc_flags.BASELINE_ALLOWED_TOOLS
        self.assertEqual(tools[: len(baseline)], baseline)
        added = tools[len(baseline):]
        self.assertEqual(len(added), 7)
        self.assertEqual(
            list(added),
            ["Bash(%s %s:*)" % (WRAPPER, verb) for verb in pc_flags.MODEL_FACING_WRAPPER_VERBS],
        )
        self.assertEqual(
            sorted(pc_flags.MODEL_FACING_WRAPPER_VERBS),
            ["handoff", "lint", "note", "show", "status", "update", "validate"],
        )

    def test_no_rule_is_only_the_wrapper_path_and_none_covers_driver_verbs(self) -> None:
        tools = pc_flags.build_allowed_tools(WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        for rule in tools:
            if WRAPPER in rule:
                self.assertNotIn(rule, ("Bash(%s)" % WRAPPER, "Bash(%s:*)" % WRAPPER, "Bash(%s *)" % WRAPPER))
                for driver_verb in pc_flags.DRIVER_ONLY_VERBS:
                    self.assertNotIn(" %s" % driver_verb, rule)
        self.assertEqual(sorted(pc_flags.DRIVER_ONLY_VERBS), ["bind", "create", "init"])

    def test_driver_only_and_unknown_verbs_are_refused(self) -> None:
        for verb in ("bind", "create", "init", "unknown", "", "status:*", "Status"):
            with self.assertRaises(ValueError, msg=verb):
                pc_flags.build_allowed_tools(WRAPPER, [verb])

    def test_duplicate_verbs_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            pc_flags.build_allowed_tools(WRAPPER, ["status", "status"])

    def test_unsafe_wrapper_paths_are_refused(self) -> None:
        bad = [
            "wrapper",
            "relative/wrapper",
            WRAPPER + ",extra",
            WRAPPER + "(x)",
            WRAPPER + ")",
            WRAPPER + " with space",
            WRAPPER + "\ttab",
            WRAPPER + "\nnewline",
            WRAPPER + "*",
            "",
        ]
        for wrapper in bad:
            with self.assertRaises(ValueError, msg=repr(len(wrapper))):
                pc_flags.build_allowed_tools(wrapper, ["status"])

    def test_returns_an_immutable_tuple_and_independent_calls(self) -> None:
        first = pc_flags.build_allowed_tools(WRAPPER, ["status"])
        self.assertIsInstance(first, tuple)
        copy = list(first)
        copy.append("Bash(rm:*)")
        second = pc_flags.build_allowed_tools(WRAPPER, ["status"])
        self.assertEqual(first, second)
        self.assertNotIn("Bash(rm:*)", second)

    def test_no_verbs_gives_just_the_baseline(self) -> None:
        self.assertEqual(pc_flags.build_allowed_tools(WRAPPER, []), pc_flags.BASELINE_ALLOWED_TOOLS)


class RenderSettingsTests(unittest.TestCase):
    def test_auto_memory_directory_is_the_realpath(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            real = os.path.join(parent, "real")
            link = os.path.join(parent, "link")
            os.makedirs(real)
            os.symlink(real, link)
            settings = pc_flags.render_settings(link, None)
            self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(real))
            self.assertIs(settings["autoMemoryEnabled"], True)
            self.assertNotIn("hooks", settings)

    def test_audit_hook_is_added_only_when_a_command_is_given(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            settings = pc_flags.render_settings(parent, "audit-command")
            hooks = settings["hooks"]["InstructionsLoaded"]
            self.assertEqual(hooks[0]["hooks"][0]["command"], "audit-command")
            self.assertEqual(hooks[0]["hooks"][0]["type"], "command")

    def test_relative_input_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            pc_flags.render_settings("relative/memory", None)


class FlagTableTests(unittest.TestCase):
    def test_rows_have_valid_status_and_unconfirmed_source(self) -> None:
        names = [row.name for row in pc_flags.FLAG_TABLE]
        self.assertEqual(len(names), len(set(names)))
        for row in pc_flags.FLAG_TABLE:
            self.assertIn(row.status, ("PINNED", "ADDED", "NOT_PINNED"))
            self.assertEqual(row.confirmed_by, "research")
            self.assertTrue(row.rationale)

    def test_pinned_values_match_the_constants(self) -> None:
        by_name = {row.name: row for row in pc_flags.FLAG_TABLE}
        self.assertEqual(by_name["--model"].value, pc_flags.PINNED_MODEL)
        self.assertEqual(by_name["--setting-sources"].value, pc_flags.SETTING_SOURCES)
        self.assertEqual(by_name["--permission-mode"].value, pc_flags.PERMISSION_MODE)
        for name in ("--bare", "--dangerously-skip-permissions", "--safe-mode", "--restricted"):
            self.assertEqual(by_name[name].status, "NOT_PINNED")

    def test_markdown_mentions_every_flag_and_is_deterministic(self) -> None:
        first = pc_flags.render_flag_table_markdown()
        second = pc_flags.render_flag_table_markdown()
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        for row in pc_flags.FLAG_TABLE:
            self.assertIn(row.name, first)
        lines = first.splitlines()
        self.assertEqual(len(lines), len(pc_flags.FLAG_TABLE) + 2)


class IsolationClaimTests(unittest.TestCase):
    def test_single_line_with_the_required_phrases(self) -> None:
        claim = pc_flags.ISOLATION_CLAIM
        self.assertNotIn("\n", claim)
        self.assertTrue(claim.startswith("Isolation claim: strict."))
        for phrase in ("CLAUDE_CONFIG_DIR", "repository", "user's own Claude config", "project,local"):
            self.assertIn(phrase, claim)
        self.assertIn("instructions, memory and skills", claim)


class ConstantsTests(unittest.TestCase):
    def test_pins(self) -> None:
        self.assertEqual(pc_flags.PINNED_MODEL, "claude-sonnet-5-5")
        self.assertEqual(pc_flags.PERMISSION_MODE, "default")
        self.assertEqual(pc_flags.SETTING_SOURCES, "project,local")
        self.assertEqual(pc_flags.VERSION_FLOOR, (2, 1, 302))
        self.assertRegex(pc_flags.COMMITTED_EVIDENCE_VERSION, re.compile(r"^2\.1\.304$"))


if __name__ == "__main__":
    unittest.main()
