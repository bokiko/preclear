"""Zero-token tests for the driver's preflight states and gates (plan 03-01; HARN-01, HARN-02, D-10, D-13).

No test starts a real claude. The only claude executed is a fake or tripwire script written into a
temporary directory by pc_testutil. A dry run is proved process-free with an in-process trap on
subprocess.Popen as well as a tripwire claude first on PATH. Every call that could reach a harness
home, a runs root or a repository passes its own temporary one, so nothing here reads or writes the
user's real folders. Scratch folders come from tempfile.mkdtemp and are never deleted.

pc_rows and pc_matrix are imported inside each test, so a missing module is reported as one error
per test instead of a single load failure of the whole file.
"""
from __future__ import annotations

import datetime
import io
import os
import re
import shutil
import tempfile
import unittest
from decimal import Decimal
from typing import List
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_leakgate
import pc_runroot
import pc_sanitize
import pc_seeds
import pc_spend
import pc_stream
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
README = os.path.join(HARNESS_DIR, "README.md")
GOOD_BANNER = "2.1.310 (Claude Code)"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
DESTINATION = "rerun-2026-10-28-claude-sonnet-5-5"
ROW1 = "row1-wrong-binding"


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def spike():
    import pc_spike

    return pc_spike


def scratch() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-mxpf-"))


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def make_repo(skip_source=None, with_evidence=True) -> str:
    """Build a repository layout holding only what row 1 lists as sources (placeholders) and the stub."""
    repo = scratch()
    pc_rows = rows()
    for path, kind in pc_rows.find_entry(pc_rows.build_registry(), "row", ROW1).sources:
        if path == skip_source:
            continue
        target = os.path.join(repo, *path.split("/"))
        if kind == "dir":
            os.makedirs(target, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(b"placeholder\n")
    stub = os.path.join(repo, "tests", "harness", "checkpoint_stub.py")
    if skip_source != "tests/harness/checkpoint_stub.py":
        shutil.copyfile(os.path.join(HARNESS_DIR, "checkpoint_stub.py"), stub)
    if with_evidence:
        os.makedirs(os.path.join(repo, "tests", "evidence"), exist_ok=True)
    return repo


def make_env(path_dirs, home=None, runs=None, harness_home=None) -> dict:
    base = scratch()
    env = {
        "PATH": os.pathsep.join(list(path_dirs) + list(pc_testutil.SYSTEM_DIRS)),
        "HOME": home if home is not None else os.path.join(base, "home"),
        "LANG": "en_US.UTF-8",
        "PRECLEAR_RUNS_ROOT": runs if runs is not None else scratch(),
        "PRECLEAR_HARNESS_HOME": harness_home if harness_home is not None else os.path.join(scratch(), "hh"),
    }
    return env


def run_main(args, env, repo, **kwargs):
    out = io.StringIO()
    err = io.StringIO()
    kwargs.setdefault("clock", lambda: FIXED_DATE)
    code = matrix().main(list(args), env=env, repo_root=repo, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def injected_row(row_id, caps=("0.10",), precondition=None, runner=None, sources=()):
    pc_rows = rows()
    stages = tuple(
        pc_rows.StageSpec("s%d" % (index + 1), "work turn", "work", 5, Decimal(cap), 60, "new:%s" % "ABCDEFGH"[index])
        for index, cap in enumerate(caps)
    )
    return pc_rows.RowSpec(row_id, "row", "injected test row", stages, True, precondition, runner, tuple(sources))


def registry_with(*extra):
    return rows().build_registry(extra=list(extra))


class NoProcess(object):
    """Context manager: any subprocess.Popen in this process is a test failure."""

    def __enter__(self):
        self.patch = mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started"))
        self.patch.start()
        return self

    def __exit__(self, *exc):
        self.patch.stop()
        return False


class ThreeStateTests(unittest.TestCase):
    """The claude-free gate runs inside the dry run and answers 12, 11, 17 and 10 with no process."""

    def setUp(self) -> None:
        self.repo = make_repo()
        self.bin = os.path.join(scratch(), "bin")
        os.makedirs(self.bin)
        pc_testutil.make_tripwire(self.bin)
        self.env = make_env([self.bin])

    def dry(self, extra_args=(), repo=None, env=None, **kwargs):
        with NoProcess():
            result = run_main(
                ["--dry-run"] + list(extra_args), self.env if env is None else env, repo or self.repo, **kwargs
            )
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        return result

    def test_a_clean_setup_is_ok_and_the_dry_run_exits_zero(self) -> None:
        code, out, err = self.dry(["--row", ROW1])
        self.assertEqual(code, 0, out + err)
        self.assertIn("worst case 2.00", out)
        self.assertNotIn("SKIPPED", out)

    def test_a_runs_root_inside_a_home_folder_is_blocked_with_exit_12_and_the_fix_line(self) -> None:
        home = scratch()
        env = make_env([self.bin], home=home, runs=os.path.join(home, "runs"))
        code, out, err = self.dry(["--row", ROW1], env=env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn("BLOCKED", out)
        self.assertIn("fix: " + matrix().BLOCKED_FIXES["runs-root"], out)
        self.assertNotIn(home, out + err)

    def test_a_runs_root_under_a_home_shaped_path_is_blocked_too(self) -> None:
        home = pc_seeds.home_path("zz-tester")
        env = make_env([self.bin], home=home, runs=home + "/runs")
        code, out, err = self.dry(["--row", ROW1], env=env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertNotIn("zz-tester", out + err)

    def test_a_runs_root_inside_the_repository_is_blocked(self) -> None:
        env = make_env([self.bin], runs=os.path.join(self.repo, "runs"))
        code, out, err = self.dry(["--row", ROW1], env=env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)

    def test_a_missing_row_source_is_a_fail_with_exit_11_naming_only_the_relative_source(self) -> None:
        missing = "tests/harness/pc_hooklog.py"
        repo = make_repo(skip_source=missing)
        code, out, err = self.dry(["--row", ROW1], repo=repo)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, out + err)
        self.assertIn("FAIL", out)
        self.assertIn(missing, out)
        self.assertNotIn(repo, out + err)

    def test_a_missing_evidence_folder_is_a_fail(self) -> None:
        registry = registry_with(injected_row("row0-no-evidence"))
        code, out, err = self.dry(["--row", "row0-no-evidence"], repo=scratch(), registry=registry)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, out + err)
        self.assertIn("evidence folder is missing", out)

    def test_an_existing_destination_folder_is_refused_with_exit_17(self) -> None:
        os.makedirs(os.path.join(self.repo, "tests", "evidence", DESTINATION))
        code, out, err = self.dry(["--row", ROW1])
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertIn(DESTINATION, out)
        self.assertNotIn(self.repo, out + err)

    def test_a_dangling_symlink_destination_is_refused_with_exit_17(self) -> None:
        os.symlink(
            os.path.join(self.repo, "no-such-target"), os.path.join(self.repo, "tests", "evidence", DESTINATION)
        )
        code, out, err = self.dry(["--row", ROW1])
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)

    def test_a_precondition_with_a_reason_is_skip_10_and_printed_as_skipped(self) -> None:
        reason = "the row needs a fixture that is absent"
        registry = registry_with(injected_row("row0-skip-case", precondition=lambda: reason))
        code, out, err = self.dry(["--row", "row0-skip-case"], registry=registry)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_SKIP, out + err)
        self.assertIn("SKIPPED: " + reason, out)
        self.assertNotIn("gate ok", out)

    def test_a_precondition_without_a_reason_passes(self) -> None:
        registry = registry_with(injected_row("row0-fine-case", precondition=lambda: None))
        code, out, err = self.dry(["--row", "row0-fine-case"], registry=registry)
        self.assertEqual(code, 0, out + err)

    def test_the_three_states_use_three_distinct_codes(self) -> None:
        skip = self.dry(
            ["--row", "row0-skip-case"],
            registry=registry_with(injected_row("row0-skip-case", precondition=lambda: "no")),
        )[0]
        fail = self.dry(["--row", ROW1], repo=make_repo(skip_source="SKILL.md"))[0]
        home = scratch()
        blocked = self.dry(["--row", ROW1], env=make_env([self.bin], home=home, runs=os.path.join(home, "r")))[0]
        self.assertEqual((skip, fail, blocked), (10, 11, 12))
        self.assertEqual(len({skip, fail, blocked}), 3)

    def test_dry_run_all_stops_at_the_first_gate_that_is_not_ok(self) -> None:
        registry = registry_with(
            injected_row("row0-skip-first", precondition=lambda: "reason one"),
            injected_row("row0-skip-second", precondition=lambda: "reason two"),
        )
        code, out, err = self.dry(["--all"], registry=registry)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_SKIP, out + err)
        self.assertIn("reason one", out)
        self.assertNotIn("reason two", out)

    def test_the_dry_run_creates_no_harness_home_and_no_ledger(self) -> None:
        self.dry(["--row", ROW1])
        self.assertFalse(os.path.exists(self.env["PRECLEAR_HARNESS_HOME"]))
        self.assertFalse(os.path.exists(os.path.join(self.env["PRECLEAR_HARNESS_HOME"], "matrix-spend.jsonl")))
        self.assertEqual(os.listdir(self.env["PRECLEAR_RUNS_ROOT"]), [])


class BudgetBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = make_repo()
        self.bin = os.path.join(scratch(), "bin")
        os.makedirs(self.bin)
        pc_testutil.make_tripwire(self.bin)
        self.env = make_env([self.bin])

    def budget(self, value, extra=(), registry=None, row=ROW1):
        with NoProcess():
            result = run_main(
                ["--dry-run", "--row", row, "--budget", value] + list(extra), self.env, self.repo, registry=registry
            )
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        return result

    def test_the_worst_case_and_above_are_accepted_up_to_five(self) -> None:
        for value in ("2.00", "2.01", "5.00", "2.0", "3", "4.99"):
            code, out, err = self.budget(value)
            self.assertEqual(code, 0, "a budget at or above the worst case was refused")

    def test_one_cent_less_and_malformed_amounts_are_refused_with_exit_18(self) -> None:
        bad = (
            "1.99",
            "0",
            "0.00",
            "5.01",
            "2.000",
            "1e1",
            "2e0",
            "-2",
            "",
            "2.",
            ".5",
            "2,00",
            "2.00 ",
            "NaN",
            "Infinity",
            chr(0x0662) + ".00",
            "9" * 40,
        )
        for value in bad:
            code, out, err = self.budget(value)
            self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, "a bad budget was not refused with 18")
            self.assertIn("worst case 2.00", out, "the plan was not printed before the refusal")
            self.assertEqual(out.count("Traceback"), 0)

    def test_a_refused_budget_never_echoes_the_value(self) -> None:
        for value in ("1.99", "7.77", "bogus-marker-zz"):
            code, out, err = self.budget(value)
            self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED)
            self.assertNotIn(value, out + err)

    def test_the_worst_case_is_exact_decimal_arithmetic_with_no_float_residue(self) -> None:
        registry = registry_with(injected_row("row0-tenths", caps=("0.10", "0.10", "0.10")))
        self.assertEqual(self.budget("0.30", registry=registry, row="row0-tenths")[0], 0)
        self.assertEqual(
            self.budget("0.29", registry=registry, row="row0-tenths")[0], pc_exitcodes.BUDGET_REFUSED
        )
        self.assertEqual(
            self.budget("0.30", registry=registry, row="row0-tenths")[1].count("worst case 0.30"), 1
        )

    def test_a_real_run_without_a_budget_prints_the_plan_and_exits_18_with_no_process(self) -> None:
        with NoProcess():
            code, out, err = run_main(["--row", ROW1], self.env, self.repo)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertIn("worst case 2.00", out)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        self.assertFalse(os.path.exists(self.env["PRECLEAR_HARNESS_HOME"]))

    def test_a_real_run_with_a_short_budget_is_refused_before_any_process(self) -> None:
        with NoProcess():
            code, out, err = run_main(["--row", ROW1, "--budget", "1.99"], self.env, self.repo)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertFalse(os.path.exists(self.env["PRECLEAR_HARNESS_HOME"]))

    def test_the_budget_is_checked_before_the_gate_in_a_dry_run(self) -> None:
        repo = make_repo(skip_source="SKILL.md")
        with NoProcess():
            code, out, err = run_main(["--dry-run", "--row", ROW1, "--budget", "1.00"], self.env, repo)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)


class ClaudePathTests(unittest.TestCase):
    """The real path: gate, budget, stub check, then the strict preflight, then the row runner."""

    def setUp(self) -> None:
        self.repo = make_repo()
        self.root = scratch()
        self.bin = os.path.join(self.root, "bin")
        os.makedirs(self.bin)
        self.calls: List[object] = []

        def runner(ctx):
            self.calls.append(ctx)
            return rows().RowOutcome(0, ("runner reached",))

        self.row = injected_row("row0-runner-case", caps=("0.10", "0.20"), runner=runner)
        self.registry = registry_with(self.row)
        self.args = ["--row", "row0-runner-case", "--budget", "0.30"]

    def real(self, env, extra=(), args=None):
        return run_main((self.args if args is None else args) + list(extra), env, self.repo, registry=self.registry)

    def ledger_absent(self, env) -> bool:
        return not os.path.exists(os.path.join(env["PRECLEAR_HARNESS_HOME"], "matrix-spend.jsonl"))

    def test_the_default_path_build_outside_the_tested_set_answers_13_with_the_fix_line(self) -> None:
        pc_testutil.make_fake_claude(self.bin, "2.1.311 (Claude Code)", True)
        env = make_env([self.bin])
        code, out, err = self.real(env)
        self.assertEqual(code, pc_exitcodes.VERSION_UNTESTED, out + err)
        self.assertIn("fix: " + matrix().BLOCKED_FIXES["untested-version"], out)
        self.assertEqual(self.calls, [])
        self.assertTrue(self.ledger_absent(env))

    def test_no_claude_anywhere_answers_12_with_the_no_claude_fix(self) -> None:
        env = make_env([])
        for directory in pc_testutil.SYSTEM_DIRS:
            if os.path.exists(os.path.join(directory, "claude")):
                self.skipTest("a claude exists in a system directory of this machine")
        code, out, err = self.real(env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn("fix: " + matrix().BLOCKED_FIXES["no-claude"], out)
        self.assertEqual(self.calls, [])
        self.assertTrue(self.ledger_absent(env))

    def test_a_logged_out_fake_answers_12_and_the_config_placeholder_is_replaced_for_printing(self) -> None:
        pc_testutil.make_fake_claude(self.bin, GOOD_BANNER, False)
        env = make_env([self.bin])
        code, out, err = self.real(env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        config = os.path.join(os.path.realpath(env["PRECLEAR_HARNESS_HOME"]), "claude-config")
        fix_lines = [line for line in out.splitlines() if line.startswith("fix: ")]
        self.assertEqual(len(fix_lines), 1)
        self.assertEqual(fix_lines[0], "fix: " + matrix().BLOCKED_FIXES["logged-out"].replace("<config>", config))
        self.assertNotIn("<config>", out)
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, out + err)
        self.assertEqual(self.calls, [])
        self.assertTrue(self.ledger_absent(env))

    def test_a_tested_explicit_build_reaches_the_row_runner_and_the_fake_is_asked_only_two_things(self) -> None:
        other = os.path.join(self.root, "other-bin")
        os.makedirs(other)
        pc_testutil.make_fake_claude(other, "2.1.999 (Claude Code)", True)
        explicit = pc_testutil.make_fake_claude(self.bin, GOOD_BANNER, True)
        env = make_env([other])
        code, out, err = self.real(env, ["--claude", explicit])
        self.assertEqual(code, 0, out + err)
        self.assertIn("runner reached", out)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        self.assertEqual(len(pc_testutil.read_env_log(self.bin)), 1)
        self.assertEqual(len(self.calls), 1)
        ctx = self.calls[0]
        self.assertEqual(ctx.claude, explicit)
        self.assertEqual(ctx.version, "2.1.310")
        self.assertEqual(ctx.banner, GOOD_BANNER)
        self.assertEqual(ctx.budget, Decimal("0.30"))
        self.assertEqual(ctx.model, pc_flags.PINNED_MODEL)
        self.assertEqual(ctx.evidence_date, "2026-10-28")
        self.assertEqual(ctx.config_dir, os.path.join(ctx.harness_home, "claude-config"))
        self.assertEqual(ctx.destination, os.path.join(self.repo, "tests", "evidence", DESTINATION))
        self.assertEqual(ctx.runs_root, os.path.realpath(env["PRECLEAR_RUNS_ROOT"]))
        self.assertIsNone(ctx.run_root)
        self.assertIsNone(ctx.sanitizer)
        self.assertTrue(self.ledger_absent(env))

    def test_a_relative_missing_or_non_executable_claude_option_is_blocked_12(self) -> None:
        plain = os.path.join(self.root, "plain")
        with open(plain, "w", encoding="utf-8") as handle:
            handle.write("x\n")
        os.chmod(plain, 0o644)
        env = make_env([self.bin])
        for candidate in ("claude", "", os.path.join(self.root, "absent"), self.bin, plain):
            code, out, err = self.real(env, ["--claude", candidate])
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
            self.assertIn("fix: " + matrix().BLOCKED_FIXES["no-claude"], out)
            self.assertNotIn(self.root, out + err)
        self.assertEqual(self.calls, [])

    def test_the_claude_option_is_accepted_and_unused_in_a_dry_run(self) -> None:
        env = make_env([self.bin])
        with NoProcess():
            code, out, err = run_main(
                ["--dry-run", "--row", ROW1, "--claude", os.path.join(self.root, "absent")], env, self.repo
            )
        self.assertEqual(code, 0, out + err)

    def test_the_stub_check_runs_before_the_preflight_on_the_real_path(self) -> None:
        pc_testutil.make_fake_claude(self.bin, GOOD_BANNER, True)
        repo = make_repo()
        with open(os.path.join(repo, "tests", "harness", "checkpoint_stub.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        env = make_env([self.bin])
        code, out, err = run_main(self.args, env, repo, registry=self.registry)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn("fix: " + matrix().BLOCKED_FIXES["stub-unreachable"], out)
        self.assertEqual(pc_testutil.read_env_log(self.bin), [])
        self.assertEqual(self.calls, [])


class StubGateTests(unittest.TestCase):
    def test_a_missing_or_empty_stub_is_blocked_with_the_stub_cause(self) -> None:
        pc_matrix = matrix()
        missing = make_repo(skip_source="tests/harness/checkpoint_stub.py")
        result = pc_matrix.check_stub(missing)
        self.assertEqual((result.code, result.cause), (pc_exitcodes.PREFLIGHT_BLOCKED, "stub-unreachable"))
        empty = make_repo()
        with open(os.path.join(empty, "tests", "harness", "checkpoint_stub.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        result = pc_matrix.check_stub(empty)
        self.assertEqual((result.code, result.cause), (pc_exitcodes.PREFLIGHT_BLOCKED, "stub-unreachable"))

    def test_a_working_stub_is_ok_and_runs_without_a_ckpt_home(self) -> None:
        pc_matrix = matrix()
        repo = make_repo()
        result = pc_matrix.check_stub(repo, env={"PATH": os.environ.get("PATH", ""), "CKPT_HOME": "/nonexistent-zz"})
        self.assertEqual(result.code, 0)

    def test_a_stub_that_exits_non_zero_is_blocked(self) -> None:
        repo = make_repo()
        with open(os.path.join(repo, "tests", "harness", "checkpoint_stub.py"), "w", encoding="utf-8") as handle:
            handle.write("import sys\nsys.exit(3)\n")
        self.assertEqual(matrix().check_stub(repo).code, pc_exitcodes.PREFLIGHT_BLOCKED)

    def test_the_dry_run_never_runs_the_stub_check(self) -> None:
        repo = make_repo()
        with open(os.path.join(repo, "tests", "harness", "checkpoint_stub.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        bin_dir = os.path.join(scratch(), "bin")
        os.makedirs(bin_dir)
        env = make_env([bin_dir])
        with NoProcess():
            code, out, err = run_main(["--dry-run", "--row", ROW1], env, repo)
        self.assertEqual(code, 0, out + err)


class ExecuteMappingTests(unittest.TestCase):
    def context(self):
        pc_rows = rows()
        return pc_rows.RunContext(
            repo_root=ROOT,
            env={},
            claude=None,
            harness_home=scratch(),
            config_dir=scratch(),
            runs_root=scratch(),
            run_root=None,
            destination=os.path.join(scratch(), "dest"),
            evidence_date="2026-10-28",
            model=pc_flags.PINNED_MODEL,
            sanitizer=None,
            deny_entries=None,
            budget=Decimal("2.00"),
            banner=GOOD_BANNER,
            version="2.1.310",
        )

    def run_row(self, runner):
        row = injected_row("row0-exec-case", runner=runner)
        out = io.StringIO()
        err = io.StringIO()
        code = matrix().execute_row(row, self.context(), out, err)
        return code, out.getvalue(), err.getvalue()

    def test_a_runner_outcome_is_printed_and_its_code_returned(self) -> None:
        code, out, err = self.run_row(lambda ctx: rows().RowOutcome(0, ("first line", "second line")))
        self.assertEqual((code, out), (0, "first line\nsecond line\n"))
        code, out, err = self.run_row(lambda ctx: rows().RowOutcome(11, ("fixed failure line",)))
        self.assertEqual((code, out), (11, "fixed failure line\n"))

    def test_each_named_exception_maps_to_its_code_with_fixed_text_and_no_traceback(self) -> None:
        probe = "distinctive-probe-text-zz"
        cases = [
            (spike().BudgetRefused, 18),
            (pc_runroot.RunRootCollision, 16),
            (pc_sanitize.SanitizerError, 15),
            (pc_leakgate.ScannerError, 15),
            (spike().HomeRefused, 12),
            (spike().SpikeError, 11),
            (pc_stream.StreamError, 19),
            (pc_spend.SpendRefused, 18),
            (pc_spend.SpendError, 11),
            (ImportError, 11),
        ]
        for exception, expected in cases:

            def runner(ctx, exception=exception):
                raise exception(probe)

            code, out, err = self.run_row(runner)
            self.assertEqual(code, expected, "an exception was mapped to the wrong exit code")
            text = out + err
            self.assertTrue(text.strip(), "an exception printed nothing")
            self.assertNotIn(probe, text)
            self.assertNotIn("Traceback", text)

    def test_a_runner_that_returns_something_else_is_a_fail(self) -> None:
        code, out, err = self.run_row(lambda ctx: "not an outcome")
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)

    def test_an_unresolvable_runner_name_is_a_fail_not_a_traceback(self) -> None:
        for runner in ("pc_no_such_module_zz:run_row", "pc_rows:no_such_function_zz", "no-colon", None):
            code, out, err = self.run_row(runner)
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
            self.assertNotIn("Traceback", out + err)
            self.assertIn("not available", out + err)

    def test_the_exception_mapping_also_holds_on_the_real_path(self) -> None:
        bin_dir = os.path.join(scratch(), "bin")
        os.makedirs(bin_dir)
        pc_testutil.make_fake_claude(bin_dir, GOOD_BANNER, True)
        env = make_env([bin_dir])

        def runner(ctx):
            raise spike().BudgetRefused("distinctive-probe-text-zz")

        registry = registry_with(injected_row("row0-raises", caps=("0.10",), runner=runner))
        code, out, err = run_main(
            ["--row", "row0-raises", "--budget", "0.10"], env, make_repo(), registry=registry
        )
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertNotIn("distinctive-probe-text-zz", out + err)


class FixLineTests(unittest.TestCase):
    def test_the_five_causes_in_order(self) -> None:
        self.assertEqual(
            list(matrix().BLOCKED_FIXES),
            ["no-claude", "logged-out", "untested-version", "runs-root", "stub-unreachable"],
        )

    def test_each_fix_line_is_a_readme_bullet_byte_for_byte(self) -> None:
        text = read_text(README)
        for cause, line in matrix().BLOCKED_FIXES.items():
            bullet = "- `%s`: %s" % (cause, line)
            self.assertTrue(("\n" + bullet + "\n") in text, "a fix line is not a README bullet byte for byte")
            self.assertEqual(text.count(bullet), 1)

    def test_no_fix_line_holds_an_absolute_path_or_a_newline(self) -> None:
        absolute = re.compile(r"(?<![\w.<>~-])/(?:usr|bin|sbin|etc|opt|var|tmp|private|Users|home|Volumes|Library|root)\b")
        for cause, line in matrix().BLOCKED_FIXES.items():
            self.assertNotIn("\n", line)
            line.encode("ascii")
            self.assertIsNone(absolute.search(line), "a fix line holds an absolute path")

    def test_the_login_fix_keeps_the_config_token_as_written(self) -> None:
        self.assertIn("CLAUDE_CONFIG_DIR=<config> claude auth login", matrix().BLOCKED_FIXES["logged-out"])


if __name__ == "__main__":
    unittest.main()
