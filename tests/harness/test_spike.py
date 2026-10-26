"""Zero-token tests for the spike driver and the hook logger (plan 02-08, task 1; HARN-04).

No test starts a real claude. The only claude executed is a fake or tripwire script written
into a temporary directory by pc_testutil. Every call that could reach a harness home passes
its own environment (a temporary PRECLEAR_HARNESS_HOME and HOME), so nothing here ever reads
or writes the user's real harness folder or Claude folders. Scratch directories are never
deleted by a test and their paths are never printed.

pc_spike is imported inside each test (through spike()), so a missing module is reported as
one error per test instead of a single load failure of the whole file.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_manifest
import pc_runroot
import pc_seeds
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
SPIKE_SCRIPT = os.path.join(HARNESS_DIR, "pc_spike.py")
HOOKLOG_SCRIPT = os.path.join(HARNESS_DIR, "pc_hooklog.py")
HOME_ENV = "PRECLEAR_HARNESS_HOME"
BANNER = "2.1.310 (Claude Code)"
LEDGER_NAME = "CONTINUITY_CLAUDE-widget-export.md"
ROW2_SETUP = os.path.join("tests", "evidence", "publication-2026-10-20", "row2-double-conflict", "snap-0-setup")


def spike():
    import pc_spike

    return pc_spike


def scratch() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-spike-"))


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def cli_env(base: str, path_dirs, harness_home=None, extra=None) -> dict:
    env = {
        "PATH": os.pathsep.join(list(path_dirs) + list(pc_testutil.SYSTEM_DIRS)),
        "HOME": base,
        "LANG": "en_US.UTF-8",
    }
    if harness_home is not None:
        env[HOME_ENV] = harness_home
    if extra:
        env.update(extra)
    return env


def run_cli(args, env, stdin=b""):
    proc = subprocess.run(
        [sys.executable, "-E", "-s", "-B", SPIKE_SCRIPT] + list(args),
        env=env,
        input=stdin,
        capture_output=True,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def run_main(args, env):
    """Run pc_spike.main in this process with an explicit environment; return (code, out, err)."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = spike().main(list(args), env=env)
    return code, out.getvalue(), err.getvalue()


def make_repo(base: str) -> str:
    """A temporary repository root holding only what the materialiser reads."""
    repo = os.path.join(base, "repo")
    shutil.copytree(
        os.path.join(ROOT, "tests", "fixtures", "bound-ledger"),
        os.path.join(repo, "tests", "fixtures", "bound-ledger"),
    )
    shutil.copyfile(os.path.join(ROOT, "SKILL.md"), os.path.join(repo, "SKILL.md"))
    shutil.copytree(os.path.join(ROOT, "references"), os.path.join(repo, "references"))
    harness = os.path.join(repo, "tests", "harness")
    os.makedirs(harness)
    shutil.copy2(os.path.join(HARNESS_DIR, "checkpoint-wrapper"), os.path.join(harness, "checkpoint-wrapper"))
    shutil.copy2(os.path.join(HARNESS_DIR, "checkpoint_stub.py"), os.path.join(harness, "checkpoint_stub.py"))
    shutil.copy2(os.path.join(HARNESS_DIR, "pc_hooklog.py"), os.path.join(harness, "pc_hooklog.py"))
    setup = os.path.join(repo, ROW2_SETUP)
    os.makedirs(setup)
    shutil.copyfile(os.path.join(ROOT, ROW2_SETUP, LEDGER_NAME), os.path.join(setup, LEDGER_NAME))
    return repo


def git_out(project: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", project] + list(args),
        env=pc_testutil.git_env({"PATH": os.environ.get("PATH", "")}),
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.decode("utf-8")


class ModuleConstantsTests(unittest.TestCase):
    def test_the_caps_and_attempt_limits_are_the_decided_ones(self) -> None:
        m = spike()
        self.assertEqual(m.TOTAL_CAP, Decimal("5.00"))
        self.assertEqual(m.MAX_ATTEMPTS, 2)
        self.assertEqual(m.PINNED_MODEL, pc_flags.PINNED_MODEL)
        self.assertEqual(
            {name: (spec.turns, spec.cap) for name, spec in m.CALLS.items()},
            {
                "s1": (3, Decimal("0.50")),
                "s2a": (12, Decimal("1.00")),
                "s2b": (2, Decimal("0.50")),
                "verbose": (1, Decimal("0.05")),
            },
        )

    def test_the_worst_case_with_every_retry_stays_under_the_total_cap(self) -> None:
        m = spike()
        worst = sum((spec.cap * m.MAX_ATTEMPTS for spec in m.CALLS.values()), Decimal("0"))
        self.assertEqual(worst, Decimal("4.10"))
        self.assertLessEqual(worst, m.TOTAL_CAP)


class HarnessHomeTests(unittest.TestCase):
    def test_a_relative_path_is_refused(self) -> None:
        m = spike()
        base = scratch()
        with self.assertRaises(m.HomeRefused):
            m.harness_home({HOME_ENV: "relative/folder"}, home_dir=base, repo_root=os.path.join(base, "repo"))

    def test_a_path_inside_the_repository_is_refused_also_through_a_link(self) -> None:
        m = spike()
        base = scratch()
        repo = os.path.join(base, "repo")
        os.makedirs(os.path.join(repo, "sub"))
        with self.assertRaises(m.HomeRefused):
            m.harness_home({HOME_ENV: os.path.join(repo, "sub", "h")}, home_dir=base, repo_root=repo)
        link = os.path.join(base, "alias")
        os.symlink(os.path.join(repo, "sub"), link)
        with self.assertRaises(m.HomeRefused):
            m.harness_home({HOME_ENV: os.path.join(link, "h")}, home_dir=base, repo_root=repo)

    def test_a_path_at_or_under_the_users_own_claude_folder_is_refused(self) -> None:
        m = spike()
        base = scratch()
        own = os.path.join(base, ".claude")
        os.makedirs(own)
        for candidate in (own, os.path.join(own, "harness")):
            with self.assertRaises(m.HomeRefused):
                m.harness_home({HOME_ENV: candidate}, home_dir=base, repo_root=os.path.join(base, "repo"))

    def test_the_default_is_the_dot_folder_under_the_home_resolved_at_call_time(self) -> None:
        m = spike()
        first = scratch()
        second = scratch()
        with mock.patch.dict(os.environ, {"HOME": first}):
            os.environ.pop(HOME_ENV, None)
            self.assertEqual(m.harness_home(), os.path.join(first, ".preclear-harness"))
        with mock.patch.dict(os.environ, {"HOME": second}):
            os.environ.pop(HOME_ENV, None)
            self.assertEqual(m.harness_home(), os.path.join(second, ".preclear-harness"))

    def test_the_config_directory_is_created_with_mode_0700_and_reported_once(self) -> None:
        m = spike()
        base = scratch()
        env = {HOME_ENV: os.path.join(base, "h")}
        path, created = m.ensure_config_dir(env, home_dir=base)
        self.assertTrue(created)
        self.assertEqual(os.path.basename(path), "claude-config")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o700)
        again, created_again = m.ensure_config_dir(env, home_dir=base)
        self.assertEqual(again, path)
        self.assertFalse(created_again)
        self.assertEqual(m.config_dir(env, home_dir=base), path)


class LocalNamesTests(unittest.TestCase):
    def test_entry_names_of_the_four_folders_are_listed_without_opening_any_file(self) -> None:
        m = spike()
        home = scratch()
        claude = os.path.join(home, ".claude")
        for folder in ("skills", "commands", "agents", "plugins"):
            os.makedirs(os.path.join(claude, folder))
        os.makedirs(os.path.join(claude, "skills", "alpha-skill"))
        os.makedirs(os.path.join(claude, "skills", "beta-skill"))
        os.makedirs(os.path.join(claude, "plugins", "zeta-plugin"))
        unreadable = []
        for folder, name in (("commands", "gamma.md"), ("commands", "delta.md"), ("agents", "eps.md")):
            path = os.path.join(claude, folder, name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("not read\n")
            os.chmod(path, 0o000)
            unreadable.append(path)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            names = m.local_user_names(home)
        self.assertIsInstance(names, frozenset)
        self.assertEqual(
            names,
            frozenset(["alpha-skill", "beta-skill", "gamma", "delta", "eps", "zeta-plugin"]),
        )
        self.assertEqual(out.getvalue(), "")
        for path in unreadable:
            os.chmod(path, 0o600)

    def test_missing_folders_give_an_empty_set(self) -> None:
        m = spike()
        self.assertEqual(m.local_user_names(scratch()), frozenset())


class MaterializeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        m = spike()
        cls.base = scratch()
        cls.repo = make_repo(cls.base)
        cls.home = os.path.join(cls.base, "harness")
        runs = os.path.join(cls.home, "runs")
        os.makedirs(runs)
        cls.run_root = pc_runroot.allocate_run_root(runs, "spike-s1-a1-20260101T000000Z")
        cls.before = pc_manifest.tree_manifest(cls.base)
        cls.session = str(uuid.uuid4())
        cls.paths = m.materialize(cls.repo, cls.run_root, cls.session, cls.home, audit_hook=True)
        cls.after = pc_manifest.tree_manifest(cls.base)

    def test_the_project_is_the_fixture_with_its_configuration_block_filled_in(self) -> None:
        text = read_text(os.path.join(self.paths["project"], "CLAUDE.md"))
        self.assertNotIn("/path/to/", text)
        self.assertIn("executable: %s\n" % self.paths["wrapper"], text)
        self.assertIn("project: %s\n" % self.paths["project"], text)
        self.assertIn("ledger: %s\n" % self.paths["ledger"], text)
        self.assertIn("fallback_directory: %s\n" % os.path.join(self.paths["project"], ".preclear"), text)
        self.assertTrue(self.paths["ledger"].startswith(self.paths["ckpt"] + os.sep))

    def test_the_project_is_a_git_repository_on_main_with_one_commit(self) -> None:
        project = self.paths["project"]
        self.assertEqual(git_out(project, "symbolic-ref", "--short", "HEAD").strip(), "main")
        self.assertEqual(git_out(project, "rev-list", "--count", "HEAD").strip(), "1")
        self.assertIn("CLAUDE.md", git_out(project, "ls-files").split())

    def test_the_skill_files_are_exact_copies_and_untracked(self) -> None:
        project = self.paths["project"]
        skill = os.path.join(project, ".claude", "skills", "preclear")
        self.assertEqual(read_bytes(os.path.join(skill, "SKILL.md")), read_bytes(os.path.join(self.repo, "SKILL.md")))
        names = sorted(os.listdir(os.path.join(self.repo, "references")))
        self.assertTrue(names)
        for name in names:
            self.assertEqual(
                read_bytes(os.path.join(skill, "references", name)),
                read_bytes(os.path.join(self.repo, "references", name)),
            )
        status = git_out(project, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        self.assertIn("?? .claude/skills/preclear/SKILL.md", status)
        self.assertEqual(git_out(project, "ls-files", ".claude").strip(), "")

    def test_the_wrapper_folder_holds_a_0755_copy_the_interpreter_and_the_stub(self) -> None:
        wrapper = self.paths["wrapper"]
        self.assertEqual(os.path.basename(wrapper), "checkpoint")
        self.assertEqual(stat.S_IMODE(os.stat(wrapper).st_mode), 0o755)
        self.assertEqual(read_bytes(wrapper), read_bytes(os.path.join(self.repo, "tests", "harness", "checkpoint-wrapper")))
        folder = os.path.dirname(wrapper)
        self.assertEqual(read_text(os.path.join(folder, "py")).strip(), os.path.realpath(sys.executable))
        self.assertEqual(
            read_text(os.path.join(folder, "stub")).strip(),
            os.path.join(self.repo, "tests", "harness", "checkpoint_stub.py"),
        )

    def test_the_state_folder_holds_the_committed_row_2_ledger_registered_and_bound(self) -> None:
        ledger = self.paths["ledger"]
        self.assertEqual(os.path.basename(ledger), LEDGER_NAME)
        self.assertEqual(read_bytes(ledger), read_bytes(os.path.join(ROOT, ROW2_SETUP, LEDGER_NAME)))
        roots = json.loads(read_text(os.path.join(self.paths["ckpt"], "ledger-roots.json")))
        self.assertEqual(roots, {"roots": [os.path.dirname(ledger)]})
        binding = json.loads(read_text(os.path.join(self.paths["ckpt"], "bindings", self.session + ".json")))
        self.assertEqual(binding["session_id"], self.session)
        self.assertEqual(binding["ledger"], ledger)

    def test_the_wrapper_answers_status_for_the_bound_session(self) -> None:
        env = {"PATH": "/usr/bin:/bin", "CKPT_HOME": self.paths["ckpt"], "CLAUDE_CODE_SESSION_ID": self.session}
        proc = subprocess.run([self.paths["wrapper"], "status"], env=env, cwd=self.paths["project"], capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        self.assertTrue(proc.stdout)

    def test_the_auto_memory_folder_is_empty_and_the_settings_name_its_realpath(self) -> None:
        self.assertEqual(os.listdir(self.paths["auto_memory"]), [])
        settings = json.loads(read_text(self.paths["settings"]))
        self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(self.paths["auto_memory"]))

    def test_the_audit_hook_is_in_the_settings_only_when_asked(self) -> None:
        settings = json.loads(read_text(self.paths["settings"]))
        command = settings["hooks"]["InstructionsLoaded"][0]["hooks"][0]["command"]
        self.assertIn(os.path.join(self.repo, "tests", "harness", "pc_hooklog.py"), command)
        self.assertIn(self.paths["hooklog"], command)
        self.assertIn(" -I -B ", command)
        self.assertTrue(self.paths["hooklog"].startswith(self.paths["raw"] + os.sep))

    def test_a_second_call_on_the_same_run_root_raises(self) -> None:
        with self.assertRaises(FileExistsError):
            spike().materialize(self.repo, self.run_root, str(uuid.uuid4()), self.home)

    def test_nothing_outside_the_run_root_changes(self) -> None:
        prefix = os.path.relpath(self.run_root, self.base).encode("utf-8") + b"/"
        before = {entry["path"]: entry for entry in self.before}
        after = {entry["path"]: entry for entry in self.after}
        for path, entry in before.items():
            if path.startswith(prefix):
                continue
            self.assertEqual(after.get(path), entry)
        for path in after:
            if path not in before:
                self.assertTrue(path.startswith(prefix), "a new entry outside the run root")

    def test_the_hook_free_variant_has_no_hooks_key(self) -> None:
        m = spike()
        runs = os.path.join(self.home, "runs")
        run_root = pc_runroot.allocate_run_root(runs, "spike-s2a-a1-20260101T000001Z")
        paths = m.materialize(self.repo, run_root, str(uuid.uuid4()), self.home)
        self.assertNotIn("hooks", json.loads(read_text(paths["settings"])))

    def test_a_run_root_outside_the_harness_runs_folder_is_refused(self) -> None:
        m = spike()
        elsewhere = pc_runroot.allocate_run_root(self.base, "elsewhere")
        with self.assertRaises(ValueError):
            m.materialize(self.repo, elsewhere, str(uuid.uuid4()), self.home)
        self.assertEqual(os.listdir(elsewhere), [])


class RunRootNameTests(unittest.TestCase):
    def test_new_run_root_is_created_exclusively_under_the_runs_folder(self) -> None:
        m = spike()
        home = os.path.join(scratch(), "h")
        os.makedirs(home)
        first = m.new_run_root(home, "s1", 1, stamp="20260101T000000Z")
        self.assertEqual(os.path.basename(first), "spike-s1-a1-20260101T000000Z")
        self.assertEqual(os.path.dirname(first), os.path.join(home, "runs"))
        with self.assertRaises(pc_runroot.RunRootCollision):
            m.new_run_root(home, "s1", 1, stamp="20260101T000000Z")


class SpendGuardTests(unittest.TestCase):
    def home(self) -> str:
        path = os.path.join(scratch(), "h")
        os.makedirs(path)
        return path

    def test_a_fresh_home_allows_every_call_and_has_the_whole_budget(self) -> None:
        m = spike()
        home = self.home()
        for name in m.CALLS:
            m.guard(home, name)
        self.assertEqual(m.remaining(home), Decimal("5.00"))
        self.assertIsInstance(m.remaining(home), Decimal)

    def test_a_third_attempt_of_a_call_name_is_refused_with_exit_18(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s1", 1, Decimal("0.01"), "success", "2.1.310")
        m.guard(home, "s1")
        m.append_spend(home, "s1", 2, None, "no-result", "2.1.310")
        with self.assertRaises(m.BudgetRefused) as caught:
            m.guard(home, "s1")
        self.assertEqual(caught.exception.exit_code, pc_exitcodes.BUDGET_REFUSED)
        m.guard(home, "s2a")

    def test_a_call_that_would_push_recorded_spend_plus_its_cap_over_the_total_is_refused(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s2a", 1, Decimal("4.50"), "success", "2.1.310")
        m.guard(home, "s1")  # 4.50 + 0.50 = 5.00, exactly the cap, allowed
        m.guard(home, "verbose")
        with self.assertRaises(m.BudgetRefused) as caught:
            m.guard(home, "s2a")  # 4.50 + 1.00 = 5.50, and this is only its second attempt
        self.assertEqual(caught.exception.exit_code, pc_exitcodes.BUDGET_REFUSED)

    def test_an_unknown_cost_counts_as_the_calls_cap(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s2a", 1, None, "no-result", "2.1.310")
        self.assertEqual(m.recorded_total(home), Decimal("1.00"))
        self.assertEqual(m.remaining(home), Decimal("4.00"))

    def test_arithmetic_is_decimal_not_binary_floating_point(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s1", 1, Decimal("0.1"), "success", "2.1.310")
        m.append_spend(home, "s2b", 1, Decimal("0.2"), "success", "2.1.310")
        self.assertEqual(m.recorded_total(home), Decimal("0.3"))
        with self.assertRaises(ValueError):
            m.append_spend(home, "s1", 2, 0.1, "success", "2.1.310")

    def test_the_ledger_is_append_only_and_keeps_existing_lines(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s1", 1, Decimal("0.01"), "success", "2.1.310")
        path = os.path.join(home, "spike-spend.jsonl")
        first = read_bytes(path)
        m.append_spend(home, "s2b", 1, Decimal("0.02"), "success", "2.1.310")
        second = read_bytes(path)
        self.assertTrue(second.startswith(first))
        self.assertEqual(len(second.splitlines()), 2)
        record = json.loads(first.decode("utf-8"))
        self.assertEqual(
            sorted(record),
            ["attempt", "call", "subtype", "total_cost_usd", "version"],
        )
        self.assertEqual(record["total_cost_usd"], "0.01")

    def test_an_unreadable_ledger_line_refuses_instead_of_guessing(self) -> None:
        m = spike()
        home = self.home()
        with open(os.path.join(home, "spike-spend.jsonl"), "w", encoding="utf-8") as handle:
            handle.write("not json\n")
        with self.assertRaises(m.BudgetRefused):
            m.guard(home, "s1")

    def test_an_unknown_call_name_is_refused(self) -> None:
        m = spike()
        with self.assertRaises(ValueError):
            m.guard(self.home(), "s9")


class DryRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = scratch()
        cls.bin = os.path.join(cls.base, "bin")
        os.makedirs(cls.bin)
        pc_testutil.make_tripwire(cls.bin)
        cls.home = os.path.join(cls.base, "h")
        cls.env = cli_env(cls.base, [cls.bin], harness_home=cls.home)

    def run_ok(self, *args: str) -> str:
        code, out, err = run_cli(list(args), self.env)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        return out

    def argv_tokens(self, out: str):
        lines = [line for line in out.splitlines() if line.startswith("argv: ")]
        self.assertEqual(len(lines), 1, out)
        return lines[0][len("argv: "):].split(" ")

    def test_s1_prints_the_pinned_call_with_role_tokens_and_starts_no_process(self) -> None:
        out = self.run_ok("s1")
        self.assertIn("--max-budget-usd 0.50", out)
        self.assertIn("--max-turns 3", out)
        self.assertIn("--model claude-sonnet-5-5", out)
        self.assertIn("--include-hook-events", self.argv_tokens(out))
        for token in ("<claude>", "<settings>", "<session>"):
            self.assertIn(token, out)

    def test_s2a_and_s2b_print_their_caps(self) -> None:
        out = self.run_ok("s2a")
        self.assertIn("--max-budget-usd 1.00", out)
        self.assertIn("--max-turns 12", out)
        self.assertNotIn("--include-hook-events", self.argv_tokens(out))
        self.assertNotIn("--resume", self.argv_tokens(out))
        out = self.run_ok("s2b")
        self.assertIn("--max-budget-usd 0.50", out)
        self.assertIn("--max-turns 2", out)
        self.assertIn("--resume", self.argv_tokens(out))

    def test_the_verbose_probe_leaves_out_the_verbose_flag(self) -> None:
        out = self.run_ok("verbose-probe")
        self.assertIn("--max-budget-usd 0.05", out)
        self.assertIn("--max-turns 1", out)
        self.assertNotIn("--verbose", self.argv_tokens(out))
        self.assertIn("--output-format stream-json", out)

    def test_the_plan_shows_names_attempts_and_the_remaining_budget_and_no_real_path(self) -> None:
        out = self.run_ok("s2a")
        self.assertIn("CLAUDE_CONFIG_DIR", out)
        self.assertIn("CKPT_HOME", out)
        self.assertIn("attempts: 0 of 2", out)
        self.assertIn("remaining 5.00 USD", out)
        self.assertNotIn(self.base, out)
        self.assertNotIn(os.path.realpath(ROOT), out)

    def test_a_dry_run_needs_no_claude_and_creates_nothing(self) -> None:
        env = cli_env(self.base, [], harness_home=os.path.join(self.base, "other-home"))
        code, out, err = run_cli(["s2a"], env)
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.exists(os.path.join(self.base, "other-home")))
        self.assertFalse(os.path.exists(self.home))

    def test_a_dash_dash_dry_run_flag_is_not_defined(self) -> None:
        code, out, err = run_cli(["s1", "--dry-run"], self.env)
        self.assertEqual(code, 2)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])

    def test_the_calls_not_yet_enabled_stop_at_the_paid_boundary_without_a_process(self) -> None:
        for name in ("s2a", "s2b", "verbose-probe"):
            code, out, err = run_cli([name, "--run"], self.env)
            self.assertEqual(code, 2, name)
            self.assertIn("paid path is enabled in task 4", err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])

    def test_run_is_refused_with_exit_18_when_the_guard_says_so(self) -> None:
        m = spike()
        home = os.path.join(scratch(), "h")
        os.makedirs(home)
        m.append_spend(home, "s1", 1, Decimal("0.01"), "success", "2.1.310")
        m.append_spend(home, "s1", 2, Decimal("0.01"), "success", "2.1.310")
        env = cli_env(self.base, [self.bin], harness_home=home)
        code, out, err = run_cli(["s1", "--run"], env)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])

    def test_a_harness_home_inside_the_repository_is_refused_with_exit_2(self) -> None:
        env = cli_env(self.base, [self.bin], harness_home=os.path.join(ROOT, "tests", "harness", "nope"))
        code, out, err = run_cli(["s1"], env)
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(os.path.join(ROOT, "tests", "harness", "nope")))

    def test_spend_and_probes_read_only_and_report_an_empty_state(self) -> None:
        code, out, err = run_cli(["spend"], self.env)
        self.assertEqual(code, 0, err)
        self.assertIn("recorded spend: 0.00 USD", out)
        self.assertIn("remaining: 5.00 USD", out)
        code, out, err = run_cli(["probes"], self.env)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "no login probes recorded")
        self.assertFalse(os.path.exists(self.home))


class HookLogTests(unittest.TestCase):
    def run_hook(self, log: str, payload: bytes, args=None):
        argv = [sys.executable, "-I", "-B", HOOKLOG_SCRIPT] + ([log] if args is None else list(args))
        proc = subprocess.run(argv, input=payload, capture_output=True)
        return proc.returncode

    def test_a_payload_appends_one_json_line_with_the_three_fields_only(self) -> None:
        log = os.path.join(scratch(), "hooklog.jsonl")
        payload = json.dumps(
            {
                "hook_event_name": "InstructionsLoaded",
                "file_path": "/synthetic/CLAUDE.md",
                "memory_type": "Project",
                "load_reason": "session_start",
                "session_id": "must-not-be-copied",
            }
        ).encode("utf-8")
        self.assertEqual(self.run_hook(log, payload), 0)
        self.assertEqual(self.run_hook(log, payload), 0)
        lines = read_text(log).splitlines()
        self.assertEqual(len(lines), 2)
        record = json.loads(lines[0])
        self.assertEqual(
            record,
            {"file_path": "/synthetic/CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"},
        )
        self.assertEqual(stat.S_IMODE(os.stat(log).st_mode), 0o600)

    def test_missing_fields_are_null_and_non_text_values_are_dropped(self) -> None:
        log = os.path.join(scratch(), "hooklog.jsonl")
        self.assertEqual(self.run_hook(log, b'{"file_path": 7, "memory_type": "User"}'), 0)
        self.assertEqual(
            json.loads(read_text(log)),
            {"file_path": None, "memory_type": "User", "load_reason": None},
        )

    def test_invalid_input_is_recorded_as_unparseable_and_still_exits_0(self) -> None:
        log = os.path.join(scratch(), "hooklog.jsonl")
        for payload in (b"not json", b"[1, 2]", b"", b"\xff\xfe", b'"text"'):
            self.assertEqual(self.run_hook(log, payload), 0, payload)
        lines = read_text(log).splitlines()
        self.assertEqual(len(lines), 5)
        for line in lines:
            self.assertEqual(json.loads(line), {"error": "unparseable"})

    def test_an_unwritable_target_or_no_argument_never_blocks_a_run(self) -> None:
        missing = os.path.join(scratch(), "no-such-folder", "hooklog.jsonl")
        self.assertEqual(self.run_hook(missing, b'{"file_path": "x"}'), 0)
        self.assertFalse(os.path.exists(missing))
        self.assertEqual(self.run_hook("", b'{"file_path": "x"}', args=[]), 0)

    def test_the_module_names_the_event_it_serves(self) -> None:
        self.assertIn("InstructionsLoaded", read_text(HOOKLOG_SCRIPT))


class AuthCheckTests(unittest.TestCase):
    def rig(self, logged_in: bool, auth_raw=None, with_claude: bool = True):
        base = scratch()
        bin_dir = os.path.join(base, "bin")
        os.makedirs(bin_dir)
        if with_claude:
            pc_testutil.make_fake_claude(bin_dir, BANNER, logged_in, auth_raw)
        home = os.path.join(base, "h")
        env = cli_env(base, [bin_dir], harness_home=home, extra={"ANTHROPIC_API_KEY": "planted-key-value"})
        return base, bin_dir, home, env

    def probe_lines(self, home: str):
        path = os.path.join(home, "auth-probes.jsonl")
        return read_text(path).splitlines() if os.path.exists(path) else []

    def test_logged_out_exits_12_with_the_login_instruction_and_records_one_probe(self) -> None:
        base, bin_dir, home, env = self.rig(False)
        code, out, err = run_cli(["auth-check"], env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        combined = out + err
        self.assertIn("claude auth login", combined)
        self.assertIn("CLAUDE_CONFIG_DIR=%s" % os.path.join(home, "claude-config"), combined)
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, combined)
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(home, "claude-config")).st_mode), 0o700)
        lines = self.probe_lines(home)
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(sorted(record), ["created", "exit", "loggedIn", "time", "version"])
        self.assertIs(record["loggedIn"], False)
        self.assertEqual(record["exit"], 12)
        self.assertEqual(record["version"], "2.1.310")
        self.assertIs(record["created"], True)
        self.assertRegex(record["time"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(pc_testutil.read_tripwire(bin_dir), [])

    def test_a_second_call_appends_and_never_rewrites_the_first_probe(self) -> None:
        base, bin_dir, home, env = self.rig(False)
        run_cli(["auth-check"], env)
        first = read_bytes(os.path.join(home, "auth-probes.jsonl"))
        code, out, err = run_cli(["auth-check"], env)
        self.assertEqual(code, 12)
        both = read_bytes(os.path.join(home, "auth-probes.jsonl"))
        self.assertTrue(both.startswith(first))
        records = [json.loads(line) for line in both.decode("utf-8").splitlines()]
        self.assertEqual([r["created"] for r in records], [True, False])

    def test_logged_in_exits_0_and_prints_only_the_boolean(self) -> None:
        base, bin_dir, home, env = self.rig(True)
        code, out, err = run_cli(["auth-check"], env)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "loggedIn true\n")
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, out + err)
        record = json.loads(self.probe_lines(home)[0])
        self.assertIs(record["loggedIn"], True)
        self.assertEqual(record["exit"], 0)
        self.assertEqual(pc_testutil.read_tripwire(bin_dir), [])

    def test_the_child_sees_the_harness_config_directory_and_no_api_key(self) -> None:
        base, bin_dir, home, env = self.rig(True)
        run_cli(["auth-check"], env)
        rows = pc_testutil.read_env_log(bin_dir)
        self.assertTrue(rows)
        for row in rows:
            config, key, token = row.split("|")
            self.assertEqual(config, os.path.join(home, "claude-config"))
            self.assertEqual(key, "unset")
            self.assertEqual(token, "unset")

    def test_an_answer_without_a_boolean_exits_11_and_records_an_unknown_login(self) -> None:
        base, bin_dir, home, env = self.rig(True, auth_raw='{"loggedIn": "yes"}')
        code, out, err = run_cli(["auth-check"], env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, out + err)
        record = json.loads(self.probe_lines(home)[0])
        self.assertIsNone(record["loggedIn"])
        self.assertEqual(record["exit"], 11)

    def test_no_claude_at_all_exits_12_and_records_an_unknown_login(self) -> None:
        base, bin_dir, home, env = self.rig(True, with_claude=False)
        code, out, err = run_cli(["auth-check"], env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        record = json.loads(self.probe_lines(home)[0])
        self.assertIsNone(record["loggedIn"])
        self.assertIsNone(record["version"])

    def test_a_version_below_the_floor_exits_13_and_is_never_a_pass(self) -> None:
        base = scratch()
        bin_dir = os.path.join(base, "bin")
        os.makedirs(bin_dir)
        pc_testutil.make_fake_claude(bin_dir, "2.1.100 (Claude Code)", True)
        home = os.path.join(base, "h")
        code, out, err = run_main(["auth-check"], cli_env(base, [bin_dir], harness_home=home))
        self.assertEqual(code, pc_exitcodes.VERSION_UNTESTED, out + err)

    def test_probes_prints_only_time_login_exit_and_created(self) -> None:
        base, bin_dir, home, env = self.rig(False)
        run_cli(["auth-check"], env)
        run_cli(["auth-check"], env)
        code, out, err = run_cli(["probes"], env)
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z loggedIn=false exit=12 created=true$")
        self.assertRegex(lines[1], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z loggedIn=false exit=12 created=false$")
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, out)
        self.assertNotIn(home, out)


# ---------------------------------------------------------------------------------------------
# Task 3: spike S1 (assertions, STOP outcome, sanitised data, the paid path through a fake claude)
# ---------------------------------------------------------------------------------------------

SESSION = "11111111-2222-4333-8444-555555555555"
USER_NAME = "pcsynthskill"


def init_event(project: str, auto_memory: str, **over) -> dict:
    base = {
        "type": "system",
        "subtype": "init",
        "session_id": SESSION,
        "claude_code_version": "2.1.310",
        "cwd": project,
        "tools": ["Bash", "Read"],
        "mcp_servers": [],
        "model": "claude-sonnet-5-5",
        "permissionMode": "default",
        "slash_commands": ["compact", "preclear"],
        "skills": ["update-config", "preclear"],
        "plugins": [],
        "agents": ["general-purpose"],
        "apiKeySource": "none",
        "memory_paths": {"auto": auto_memory},
        "effort": "high",
    }
    base.update(over)
    return base


class S1Rig(object):
    """Synthetic paths for the assertion tests; nothing here touches a real folder."""

    def __init__(self) -> None:
        self.base = scratch()
        self.run_root = os.path.join(self.base, "runs", "spike-s1-a1-20260101T000000Z")
        self.project = os.path.join(self.run_root, "project")
        self.auto_memory = os.path.join(self.run_root, "auto-memory")
        self.config = os.path.join(self.base, "claude-config")
        os.makedirs(self.project)
        os.makedirs(self.config)
        os.makedirs(self.auto_memory)
        self.claude_md = os.path.join(self.project, "CLAUDE.md")
        with open(self.claude_md, "w", encoding="utf-8") as handle:
            handle.write("x\n")

    def init(self, **over) -> dict:
        return init_event(self.project, self.auto_memory, **over)

    def good_hooks(self):
        return [
            {"file_path": self.claude_md, "memory_type": "Project", "load_reason": "session_start"},
            {"file_path": os.path.join(self.config, "CLAUDE.md"), "memory_type": "User", "load_reason": "session_start"},
        ]

    def run(self, event=None, hooks="good", names=frozenset()):
        m = spike()
        lines = self.good_hooks() if hooks == "good" else hooks
        return m.s1_assertions(
            [event if event is not None else self.init()],
            lines,
            names,
            self.project,
            self.run_root,
            self.config,
        )


def by_id(assertions):
    return dict((item[0], item) for item in assertions)


class S1AssertionTests(unittest.TestCase):
    def test_the_declared_assertion_ids_are_the_nine_of_the_plan_in_order(self) -> None:
        m = spike()
        self.assertEqual(
            m.S1_ASSERTION_IDS,
            (
                "permission-mode-default",
                "model-pinned",
                "skill-preclear-present",
                "mcp-servers-empty",
                "no-non-builtin-plugins",
                "user-names-absent",
                "no-user-instruction-outside-config",
                "project-claude-md-loaded",
                "project-local-inside-run-root",
            ),
        )

    def test_a_clean_run_passes_every_assertion_and_tags_how_each_was_asserted(self) -> None:
        rig = S1Rig()
        result = rig.run(names=frozenset(["othername"]))
        self.assertEqual([item[0] for item in result], list(spike().S1_ASSERTION_IDS))
        self.assertTrue(all(item[2] for item in result), result)
        hows = [item[1] for item in result]
        self.assertEqual(hows, ["init"] * 6 + ["hook"] * 3)

    def test_each_rule_fails_in_its_own_variant(self) -> None:
        rig = S1Rig()
        other = os.path.join(rig.base, "elsewhere")
        os.makedirs(other)
        user_leak = {"file_path": os.path.join(other, "CLAUDE.md"), "memory_type": "User", "load_reason": "session_start"}
        project_leak = {"file_path": os.path.join(other, "CLAUDE.md"), "memory_type": "Project", "load_reason": "nested_traversal"}
        local_leak = {"file_path": os.path.join(other, "CLAUDE.local.md"), "memory_type": "Local", "load_reason": "session_start"}
        user_only = [{"file_path": os.path.join(rig.config, "CLAUDE.md"), "memory_type": "User", "load_reason": "session_start"}]
        variants = [
            ("permission-mode-default", dict(event=rig.init(permissionMode="acceptEdits"))),
            ("model-pinned", dict(event=rig.init(model="some-other-model"))),
            ("skill-preclear-present", dict(event=rig.init(skills=["update-config"]))),
            ("mcp-servers-empty", dict(event=rig.init(mcp_servers=[{"name": "x", "status": "connected"}]))),
            ("no-non-builtin-plugins", dict(event=rig.init(plugins=[{"name": "p", "path": "q", "source": "p@market"}]))),
            ("user-names-absent", dict(event=rig.init(skills=["preclear", USER_NAME]), names=frozenset([USER_NAME]))),
            ("no-user-instruction-outside-config", dict(hooks=rig.good_hooks() + [user_leak])),
            ("project-claude-md-loaded", dict(hooks=user_only)),
            ("project-local-inside-run-root", dict(hooks=rig.good_hooks() + [project_leak])),
            ("project-local-inside-run-root", dict(hooks=rig.good_hooks() + [local_leak])),
        ]
        for failing, kwargs in variants:
            result = by_id(rig.run(**kwargs))
            self.assertFalse(result[failing][2], failing)
            for name in result:
                if name != failing:
                    self.assertTrue(result[name][2], "%s should still pass when %s fails" % (name, failing))

    def test_a_user_instruction_file_inside_the_config_directory_is_fine(self) -> None:
        rig = S1Rig()
        result = by_id(rig.run())
        self.assertTrue(result["no-user-instruction-outside-config"][2])

    def test_an_unreadable_hook_record_fails_closed(self) -> None:
        rig = S1Rig()
        hooks = rig.good_hooks() + [{"error": "unparseable"}]
        result = by_id(rig.run(hooks=hooks))
        self.assertFalse(result["no-user-instruction-outside-config"][2])


class AbsenceAndCountsTests(unittest.TestCase):
    def test_the_absence_check_reports_counts_only_and_never_a_name(self) -> None:
        m = spike()
        rig = S1Rig()
        names = frozenset([USER_NAME, "secondhidden", "preclear"])
        outcome = m.evaluate_s1(
            [rig.init(skills=["preclear", USER_NAME])],
            rig.good_hooks(),
            names,
            rig.project,
            rig.run_root,
            rig.config,
        )
        self.assertEqual(outcome.status, "stop")
        self.assertEqual(outcome.counts["user_names"], 2)  # preclear is excluded and the exclusion is counted
        self.assertEqual(outcome.counts["user_names_excluded"], 1)
        self.assertEqual(outcome.counts["user_name_hits"], 1)
        text = repr(outcome) + "\n".join(m.describe_s1(outcome))
        self.assertNotIn(USER_NAME, text)
        self.assertNotIn("secondhidden", text)

    def test_managed_entries_are_counted_and_never_hidden_or_failed(self) -> None:
        m = spike()
        rig = S1Rig()
        hooks = rig.good_hooks() + [
            {"file_path": "/etc/example-managed/CLAUDE.md", "memory_type": "Managed", "load_reason": "session_start"}
        ]
        outcome = m.evaluate_s1([rig.init()], hooks, frozenset(), rig.project, rig.run_root, rig.config)
        self.assertEqual(outcome.status, "pass")
        self.assertEqual(outcome.counts["entries_managed"], 1)
        self.assertEqual(outcome.counts["entries_project"], 1)
        self.assertEqual(outcome.counts["entries_user"], 1)

    def test_a_dict_plugin_or_a_prefixed_name_still_counts_as_a_hit(self) -> None:
        m = spike()
        rig = S1Rig()
        event = rig.init(plugins=[{"name": USER_NAME}], skills=["preclear", "vendor:" + USER_NAME])
        result = by_id(
            m.s1_assertions([event], rig.good_hooks(), frozenset([USER_NAME]), rig.project, rig.run_root, rig.config)
        )
        self.assertFalse(result["user-names-absent"][2])


class StopOutcomeTests(unittest.TestCase):
    def test_no_hook_events_and_no_logger_file_makes_the_audit_not_assertable_and_stops(self) -> None:
        m = spike()
        rig = S1Rig()
        for hooks in (None, []):
            result = by_id(m.s1_assertions([rig.init()], hooks, frozenset(), rig.project, rig.run_root, rig.config))
            for name in (
                "no-user-instruction-outside-config",
                "project-claude-md-loaded",
                "project-local-inside-run-root",
            ):
                self.assertEqual(result[name][1], "not-assertable", name)
                self.assertFalse(result[name][2], name)
            outcome = m.evaluate_s1([rig.init()], hooks, frozenset(), rig.project, rig.run_root, rig.config)
            self.assertEqual(outcome.status, "stop")
            self.assertIn("not assertable", outcome.reason)
            text = "\n".join(m.describe_s1(outcome))
            self.assertIn("STOP", text)
            self.assertIn("by-construction", text)
            self.assertIn("canary", text)
            self.assertIn("changed", text)

    def test_stream_hook_events_alone_are_enough_for_the_audit_to_run(self) -> None:
        m = spike()
        rig = S1Rig()
        events = [
            rig.init(),
            {
                "type": "system",
                "subtype": "hook_response",
                "hook_event": "InstructionsLoaded",
                "file_path": rig.claude_md,
                "memory_type": "Project",
            },
        ]
        result = by_id(m.s1_assertions(events, None, frozenset(), rig.project, rig.run_root, rig.config))
        self.assertEqual(result["project-claude-md-loaded"][1], "hook")
        self.assertTrue(result["project-claude-md-loaded"][2])

    def test_a_stream_hook_event_without_a_payload_does_not_make_the_audit_assertable(self) -> None:
        m = spike()
        rig = S1Rig()
        events = [rig.init(), {"type": "system", "subtype": "hook_started", "hook_event": "InstructionsLoaded"}]
        outcome = m.evaluate_s1(events, None, frozenset(), rig.project, rig.run_root, rig.config)
        self.assertEqual(outcome.status, "stop")

    def test_a_failed_isolation_assertion_is_also_a_stop_with_counts_only(self) -> None:
        m = spike()
        rig = S1Rig()
        outcome = m.evaluate_s1(
            [rig.init(model="x")], rig.good_hooks(), frozenset(), rig.project, rig.run_root, rig.config
        )
        self.assertEqual(outcome.status, "stop")
        text = "\n".join(m.describe_s1(outcome))
        self.assertIn("STOP", text)
        self.assertIn("model-pinned: FAIL", text)


class SanitizeToDataTests(unittest.TestCase):
    def sanitizer(self, base: str, run_root: str):
        import pc_sanitize

        src = pc_sanitize.Sources([pc_seeds.home_path("pcsynthhome")], "pcsynthlogin", [], [], "")
        return pc_sanitize.Sanitizer.from_machine(base, {run_root: "<run>"}, None, src)

    def test_a_sanitised_manifest_is_written_exclusively_with_the_run_token(self) -> None:
        m = spike()
        base = scratch()
        run_root = os.path.join(base, "runs", "spike-s1-a1-x")
        os.makedirs(run_root)
        data = json.dumps({"cwd": run_root + "/project", "model": "m"}, sort_keys=True).encode("utf-8")
        dest = os.path.join(base, "out.json")
        m.sanitize_to_data(data, dest, self.sanitizer(base, run_root))
        text = read_text(dest)
        self.assertIn("<run>/project", text)
        self.assertNotIn(run_root, text)
        self.assertEqual(stat.S_IMODE(os.stat(dest).st_mode), 0o644)

    def test_an_existing_target_is_never_overwritten(self) -> None:
        m = spike()
        base = scratch()
        dest = os.path.join(base, "out.json")
        with open(dest, "w", encoding="utf-8") as handle:
            handle.write("keep")
        with self.assertRaises(FileExistsError):
            m.sanitize_to_data(b"{}\n", dest, self.sanitizer(base, os.path.join(base, "r")))
        self.assertEqual(read_text(dest), "keep")

    def test_a_manifest_that_still_holds_an_unknown_home_path_is_refused_and_not_written(self) -> None:
        m = spike()
        base = scratch()
        dest = os.path.join(base, "out.json")
        data = json.dumps({"cwd": pc_seeds.home_path("someone-else") + "/x"}).encode("utf-8")
        with self.assertRaises(m.LeakRefused) as caught:
            m.sanitize_to_data(data, dest, self.sanitizer(base, os.path.join(base, "r")))
        self.assertEqual(caught.exception.exit_code, pc_exitcodes.LEAK_REFUSED)
        self.assertNotIn("someone-else", str(caught.exception))
        self.assertFalse(os.path.exists(dest))

    def test_the_known_home_is_replaced_before_the_gate_looks(self) -> None:
        m = spike()
        base = scratch()
        dest = os.path.join(base, "out.json")
        data = json.dumps({"cwd": pc_seeds.home_path("pcsynthhome") + "/x"}).encode("utf-8")
        m.sanitize_to_data(data, dest, self.sanitizer(base, os.path.join(base, "r")))
        self.assertIn("<home>", read_text(dest))


class SupersedeLedgerTests(unittest.TestCase):
    def home(self) -> str:
        path = os.path.join(scratch(), "h")
        os.makedirs(path)
        return path

    def test_a_later_line_for_the_same_attempt_supersedes_the_earlier_cost_and_is_one_attempt(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s1", 1, None, "launched", "2.1.310")
        self.assertEqual(m.recorded_total(home), Decimal("0.50"))
        m.append_spend(home, "s1", 1, Decimal("0.0123"), "success", "2.1.310")
        self.assertEqual(m.recorded_total(home), Decimal("0.0123"))
        self.assertEqual(m.attempts_made(home, "s1"), 1)
        self.assertEqual(len(read_bytes(os.path.join(home, "spike-spend.jsonl")).splitlines()), 2)
        m.guard(home, "s1")

    def test_a_launched_line_with_no_reconciliation_keeps_counting_as_the_cap(self) -> None:
        m = spike()
        home = self.home()
        m.append_spend(home, "s2a", 1, None, "launched", "2.1.310")
        m.append_spend(home, "s2a", 2, None, "launched", "2.1.310")
        self.assertEqual(m.recorded_total(home), Decimal("2.00"))
        with self.assertRaises(m.BudgetRefused):
            m.guard(home, "s2a")


FAKE_CLAUDE = """#!%(python)s
import json, os, shlex, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
cfg = json.load(open(os.path.join(here, "fake.json")))
if args == ["--version"]:
    print(cfg["banner"])
    sys.exit(0)
if args == ["auth", "status", "--json"]:
    print(json.dumps({"loggedIn": cfg.get("logged_in", True), "account": "planted-identity-sentinel-7f3a91"}))
    sys.exit(0 if cfg.get("logged_in", True) else 1)
prompt = sys.stdin.read()
keep = ("CLAUDE_CONFIG_DIR", "CKPT_HOME", "DISABLE_AUTOUPDATER")
record = {"args": args, "prompt": prompt, "cwd": os.getcwd(),
          "env": dict((k, os.environ[k]) for k in os.environ if k in keep), "names": sorted(os.environ)}
with open(os.path.join(here, "calls.log"), "a") as handle:
    handle.write(json.dumps(record) + "\\n")
settings = json.load(open(args[args.index("--settings") + 1]))
sid = args[args.index("--resume") + 1] if "--resume" in args else args[args.index("--session-id") + 1]
cwd = os.getcwd()
config = os.environ.get("CLAUDE_CONFIG_DIR", "")
hooks = settings.get("hooks", {}).get("InstructionsLoaded")
if hooks and cfg.get("hook_payloads"):
    command = hooks[0]["hooks"][0]["command"]
    for payload in cfg["hook_payloads"]:
        text = json.dumps(payload).replace("$CWD", cwd).replace("$CONFIG", config)
        subprocess.run(shlex.split(command), input=text.encode("utf-8"))
if cfg.get("exit_without_result"):
    sys.exit(1)
init = {"type": "system", "subtype": "init", "session_id": sid, "claude_code_version": cfg["version"], "cwd": cwd,
        "tools": ["Bash", "Read"], "mcp_servers": [], "model": "claude-sonnet-5-5", "permissionMode": "default",
        "slash_commands": ["compact", "preclear"], "skills": ["update-config", "preclear"], "plugins": [],
        "agents": ["general-purpose"], "apiKeySource": "none",
        "memory_paths": {"auto": settings["autoMemoryDirectory"]}, "effort": "high"}
init.update(cfg.get("init_override", {}))
print(json.dumps(init))
print(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "ready."}]}}))
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "session_id": sid,
                  "total_cost_usd": cfg.get("cost", 0.0123), "permission_denials": [],
                  "terminal_reason": "completed"}))
"""


class PaidRig(object):
    """A fake claude that behaves like the paid path needs; no real model, no real login."""

    def __init__(self, hooks="project", init_override=None, exit_without_result=False, cost=0.0123) -> None:
        self.base = scratch()
        self.bin = os.path.join(self.base, "bin")
        os.makedirs(self.bin)
        script = os.path.join(self.bin, "claude")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(FAKE_CLAUDE % {"python": os.path.realpath(sys.executable)})
        os.chmod(script, 0o755)
        payloads = {
            "project": [
                {"file_path": "$CWD/CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"},
                {"file_path": "$CONFIG/CLAUDE.md", "memory_type": "User", "load_reason": "session_start"},
            ],
            "leak": [
                {"file_path": "$CWD/CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"},
                {"file_path": "/elsewhere/CLAUDE.md", "memory_type": "User", "load_reason": "session_start"},
            ],
            "none": [],
        }[hooks]
        self.config = {
            "banner": BANNER,
            "version": "2.1.310",
            "hook_payloads": payloads,
            "init_override": init_override or {},
            "exit_without_result": exit_without_result,
            "cost": cost,
        }
        self.write_config()
        self.repo = make_repo(self.base)
        self.home = os.path.join(self.base, "harness")
        self.user_home = os.path.join(self.base, "user-home")
        os.makedirs(self.user_home)
        self.runs = os.path.join(self.base, "runs-root", "runs")
        self.data = os.path.join(self.base, "data")
        os.makedirs(self.data)
        self.env = cli_env(
            self.base,
            [self.bin],
            harness_home=self.home,
            extra={"HOME": self.user_home, "PRECLEAR_RUNS_ROOT": self.runs},
        )

    def write_config(self) -> None:
        with open(os.path.join(self.bin, "fake.json"), "w", encoding="utf-8") as handle:
            json.dump(self.config, handle)

    def calls(self):
        path = os.path.join(self.bin, "calls.log")
        if not os.path.exists(path):
            return []
        return [json.loads(line) for line in read_text(path).splitlines()]

    def run_s1(self):
        m = spike()
        return m.run_s1(
            self.home,
            self.env,
            self.repo,
            self.data,
            self.env["PATH"].split(os.pathsep),
            self.user_home,
        )


class PaidS1Tests(unittest.TestCase):
    def runs_of(self, rig) -> str:
        return rig.runs

    def test_a_clean_run_writes_raw_files_the_ledger_and_the_sanitised_manifest(self) -> None:
        rig = PaidRig()
        code, lines = rig.run_s1()
        self.assertEqual(code, 0, "\n".join(lines))
        calls = rig.calls()
        self.assertEqual(len(calls), 1)
        argv = calls[0]["args"]
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.50")
        self.assertEqual(argv[argv.index("--max-turns") + 1], "3")
        self.assertEqual(argv[argv.index("--model") + 1], "claude-sonnet-5-5")
        self.assertIn("--include-hook-events", argv)
        for forbidden in ("--bare", "--dangerously-skip-permissions"):
            self.assertNotIn(forbidden, argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "default")
        self.assertEqual(calls[0]["prompt"], "Reply with exactly the one word: ready.")
        self.assertNotIn("ready", " ".join(argv))
        home = os.path.realpath(rig.home)
        self.assertEqual(calls[0]["env"]["CLAUDE_CONFIG_DIR"], os.path.join(home, "claude-config"))
        self.assertEqual(calls[0]["env"]["DISABLE_AUTOUPDATER"], "1")
        inherited = [n for n in calls[0]["names"] if n.startswith(("ANTHROPIC", "CLAUDE_CODE", "CLAUDECODE"))]
        self.assertEqual(inherited, ["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"])
        runs_dir = os.path.realpath(self.runs_of(rig))
        runs = os.listdir(runs_dir)
        self.assertEqual(len(runs), 1)
        self.assertFalse(os.path.exists(os.path.join(home, "runs")))
        self.assertEqual(stat.S_IMODE(os.stat(runs_dir).st_mode), 0o700)
        self.assertRegex(runs[0], r"^spike-s1-a1-\d{8}T\d{6}Z$")
        raw = os.path.join(runs_dir, runs[0], "raw")
        for name in ("s1.stdout", "s1.stderr", "hooklog.jsonl"):
            self.assertTrue(os.path.isfile(os.path.join(raw, name)), name)
        self.assertEqual(calls[0]["cwd"], os.path.join(runs_dir, runs[0], "project"))
        ledger = [json.loads(line) for line in read_text(os.path.join(home, "spike-spend.jsonl")).splitlines()]
        self.assertEqual(
            [(r["call"], r["attempt"], r["total_cost_usd"], r["subtype"]) for r in ledger],
            [("s1", 1, None, "launched"), ("s1", 1, "0.0123", "success")],
        )
        manifest_path = os.path.join(rig.data, "s1-init-manifest.json")
        manifest = json.loads(read_text(manifest_path))
        for key in ("permissionMode", "model", "skills", "plugins", "mcp_servers", "apiKeySource", "claude_code_version", "baseline"):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["permissionMode"], "default")
        self.assertIn("preclear", manifest["skills"])
        self.assertEqual(manifest["cwd"], "<run>/project")
        self.assertEqual(manifest["baseline"]["assertions"]["model-pinned"], "init")
        self.assertEqual(manifest["baseline"]["assertions"]["project-claude-md-loaded"], "hook")
        self.assertEqual(manifest["baseline"]["builtin_plugins"], [])
        self.assertEqual(manifest["baseline"]["counts"]["user_names_excluded"], 0)
        self.assertNotIn(rig.base, read_text(manifest_path))
        printed = "\n".join(lines)
        self.assertIn("permission-mode-default: pass", printed)
        self.assertNotIn(rig.base, printed)
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, printed)

    def test_an_unassertable_audit_stops_with_exit_11_and_writes_nothing_under_data(self) -> None:
        rig = PaidRig(hooks="none")
        code, lines = rig.run_s1()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("STOP", "\n".join(lines))
        self.assertEqual(os.listdir(rig.data), [])
        self.assertEqual(len(rig.calls()), 1)
        ledger = [json.loads(line) for line in read_text(os.path.join(os.path.realpath(rig.home), "spike-spend.jsonl")).splitlines()]
        self.assertEqual(ledger[-1]["total_cost_usd"], "0.0123")

    def test_a_failed_isolation_assertion_stops_with_exit_11_and_is_not_retried(self) -> None:
        rig = PaidRig(hooks="leak")
        code, lines = rig.run_s1()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
        printed = "\n".join(lines)
        self.assertIn("STOP", printed)
        self.assertIn("no-user-instruction-outside-config: FAIL", printed)
        self.assertEqual(os.listdir(rig.data), [])
        self.assertEqual(len(rig.calls()), 1)

    def test_an_infrastructure_failure_records_the_cap_and_allows_exactly_one_retry(self) -> None:
        m = spike()
        rig = PaidRig(exit_without_result=True)
        code, lines = rig.run_s1()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("retry", "\n".join(lines))
        self.assertEqual(m.recorded_total(os.path.realpath(rig.home)), Decimal("0.50"))
        code, lines = rig.run_s1()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
        with self.assertRaises(m.BudgetRefused):
            rig.run_s1()
        self.assertEqual(len(rig.calls()), 2)
        self.assertEqual(len(os.listdir(os.path.realpath(rig.runs))), 2)

    def test_a_refused_guard_starts_no_claude_at_all(self) -> None:
        m = spike()
        rig = PaidRig()
        home = os.path.realpath(rig.home)
        os.makedirs(home)
        m.append_spend(home, "s1", 1, Decimal("0.01"), "success", "2.1.310")
        m.append_spend(home, "s1", 2, Decimal("0.01"), "success", "2.1.310")
        with self.assertRaises(m.BudgetRefused):
            rig.run_s1()
        self.assertEqual(rig.calls(), [])

    def test_a_logged_out_config_directory_is_blocked_before_any_spend(self) -> None:
        rig = PaidRig()
        rig.config["logged_in"] = False
        rig.write_config()
        code, lines = rig.run_s1()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED)
        self.assertEqual(rig.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(os.path.realpath(rig.home), "spike-spend.jsonl")))
        self.assertNotIn(pc_testutil.IDENTITY_SENTINEL, "\n".join(lines))

    def test_the_cli_run_for_s1_is_blocked_with_exit_12_when_logged_out_and_spends_nothing(self) -> None:
        rig = PaidRig()
        rig.config["logged_in"] = False
        rig.write_config()
        code, out, err = run_cli(["s1", "--run"], rig.env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertEqual(rig.calls(), [])



class RefinedAssertionTests(unittest.TestCase):
    """bokiko's decision of 2026-10-26: built-in plugins and binary-defined names are not leaks."""

    def test_builtin_plugins_pass(self) -> None:
        rig = S1Rig()
        plugins = [
            {"name": "a", "path": "builtin", "source": "a@builtin"},
            {"name": "b", "path": "builtin", "source": "b@builtin"},
        ]
        result = by_id(rig.run(event=rig.init(plugins=plugins)))
        self.assertTrue(result["no-non-builtin-plugins"][2])

    def test_a_plugin_without_a_builtin_source_or_a_bare_string_fails(self) -> None:
        rig = S1Rig()
        good = {"name": "a", "path": "builtin", "source": "a@builtin"}
        for plugins in (
            [good, {"name": "b", "path": "p", "source": "b@elsewhere"}],
            [{"name": "a", "path": "builtin"}],
            ["a@builtin"],
        ):
            result = by_id(rig.run(event=rig.init(plugins=plugins)))
            self.assertFalse(result["no-non-builtin-plugins"][2], plugins)

    def test_a_name_that_the_binary_itself_defines_is_a_collision_not_a_leak(self) -> None:
        m = spike()
        rig = S1Rig()
        event = rig.init(skills=["preclear", USER_NAME], slash_commands=["compact", USER_NAME])
        outcome = m.evaluate_s1(
            [event],
            rig.good_hooks(),
            frozenset([USER_NAME, "other", "preclear"]),
            rig.project,
            rig.run_root,
            rig.config,
            binary_defined=frozenset([USER_NAME]),
        )
        self.assertEqual(outcome.status, "pass")
        self.assertEqual(outcome.counts["user_name_hits"], 0)
        self.assertEqual(outcome.counts["user_name_collisions"], 2)
        self.assertEqual(outcome.counts["user_names_excluded"], 1)
        self.assertNotIn(USER_NAME, repr(outcome) + "\n".join(m.describe_s1(outcome)))

    def test_a_name_the_binary_does_not_define_is_still_a_leak(self) -> None:
        m = spike()
        rig = S1Rig()
        event = rig.init(skills=["preclear", USER_NAME, "secondhidden"])
        outcome = m.evaluate_s1(
            [event],
            rig.good_hooks(),
            frozenset([USER_NAME, "secondhidden"]),
            rig.project,
            rig.run_root,
            rig.config,
            binary_defined=frozenset([USER_NAME]),
        )
        self.assertEqual(outcome.status, "stop")
        self.assertEqual(outcome.counts["user_name_hits"], 1)
        self.assertEqual(outcome.counts["user_name_collisions"], 1)

    def test_binary_defines_finds_a_name_definition_in_a_file_and_returns_only_matches(self) -> None:
        m = spike()
        base = scratch()
        blob = os.path.join(base, "fake-binary")
        with open(blob, "wb") as handle:
            handle.write(b"xx" * 10 + b'{name:"' + USER_NAME.encode() + b'",description:"d"}' + b"yy" * 10)
        self.assertEqual(m.binary_defines(blob, frozenset([USER_NAME, "notthere"])), frozenset([USER_NAME]))

    def test_binary_defines_sees_a_name_that_straddles_a_chunk_boundary(self) -> None:
        m = spike()
        base = scratch()
        blob = os.path.join(base, "fake-binary")
        needle = b'name:"' + USER_NAME.encode() + b'"'
        with open(blob, "wb") as handle:
            handle.write(b"z" * (m.BINARY_CHUNK - 5) + needle + b"z" * 100)
        self.assertEqual(m.binary_defines(blob, frozenset([USER_NAME])), frozenset([USER_NAME]))


class RunsRootTests(unittest.TestCase):
    """Leak 1 of 2026-10-26: the runs root must lie outside every home folder."""

    def test_the_default_is_a_shared_folder_outside_any_home(self) -> None:
        m = spike()
        self.assertEqual(m.DEFAULT_RUNS_ROOT, os.sep.join(["", "Users", "Shared", "preclear-harness", "runs"]))
        self.assertEqual(m.RUNS_ROOT_ENV, "PRECLEAR_RUNS_ROOT")

    def test_a_runs_root_inside_a_local_user_home_is_refused(self) -> None:
        m = spike()
        base = scratch()
        home = os.path.join(base, "home-a")
        os.makedirs(home)
        for inside in (home, os.path.join(home, ".preclear-harness", "runs")):
            with self.assertRaises(m.HomeRefused) as caught:
                m.runs_root({"PRECLEAR_RUNS_ROOT": inside}, home, os.path.join(base, "repo"), homes=[home])
            self.assertEqual(caught.exception.exit_code, pc_exitcodes.USAGE)

    def test_a_runs_root_outside_every_home_is_accepted_and_resolved(self) -> None:
        m = spike()
        base = scratch()
        home = os.path.join(base, "home-a")
        os.makedirs(home)
        target = os.path.join(base, "shared", "runs")
        got = m.runs_root({"PRECLEAR_RUNS_ROOT": target}, home, os.path.join(base, "repo"), homes=[home])
        self.assertEqual(got, os.path.realpath(target))
        self.assertFalse(os.path.exists(target))

    def test_a_relative_path_the_repository_and_the_users_claude_folder_are_refused(self) -> None:
        m = spike()
        base = scratch()
        home = os.path.join(base, "home-a")
        os.makedirs(home)
        repo = os.path.join(base, "repo")
        os.makedirs(repo)
        for bad in ("relative/runs", os.path.join(repo, "runs"), os.path.join(home, ".claude", "runs")):
            with self.assertRaises(m.HomeRefused):
                m.runs_root({"PRECLEAR_RUNS_ROOT": bad}, home, repo, homes=[])

    def test_an_ancestor_folder_with_an_instruction_file_or_folder_is_refused(self) -> None:
        m = spike()
        base = scratch()
        repo = os.path.join(base, "repo")
        plants = ("CLAUDE.md", "CLAUDE.local.md", os.path.join(".claude", "CLAUDE.md"), os.path.join(".claude", "rules", "x.md"))
        for index, plant in enumerate(plants):
            top = os.path.join(base, "anc%d" % index)
            path = os.path.join(top, plant)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("x\n")
            with self.assertRaises(m.HomeRefused):
                m.runs_root({"PRECLEAR_RUNS_ROOT": os.path.join(top, "deeper", "runs")}, None, repo, homes=[])

    def test_local_user_homes_lists_the_given_home_and_never_the_shared_folder(self) -> None:
        m = spike()
        base = scratch()
        homes = m.local_user_homes(base)
        self.assertIn(os.path.realpath(base), homes)
        self.assertNotIn(os.sep.join(["", "Users", "Shared"]), homes)
        self.assertTrue(all(os.path.isabs(item) for item in homes))

    def test_ensure_runs_root_creates_every_missing_level_with_mode_0700_and_tolerates_existing(self) -> None:
        m = spike()
        base = scratch()
        target = os.path.join(base, "a", "b", "runs")
        m.ensure_runs_root(target)
        for level in (os.path.join(base, "a"), os.path.join(base, "a", "b"), target):
            self.assertEqual(stat.S_IMODE(os.stat(level).st_mode), 0o700)
        m.ensure_runs_root(target)

    def test_new_run_root_and_materialize_accept_a_runs_dir_outside_the_harness_home(self) -> None:
        m = spike()
        base = scratch()
        repo = make_repo(base)
        home = os.path.join(base, "harness")
        runs = os.path.join(base, "elsewhere", "runs")
        root = m.new_run_root(home, "s1", 1, runs_dir=runs)
        self.assertEqual(os.path.dirname(root), os.path.realpath(runs))
        paths = m.materialize(repo, root, str(uuid.uuid4()), home, runs_dir=runs)
        self.assertTrue(os.path.isdir(paths["project"]))
        other = m.new_run_root(home, "s2a", 1, runs_dir=runs)
        with self.assertRaises(ValueError):
            m.materialize(repo, other, str(uuid.uuid4()), home)  # the default runs folder is not this one


if __name__ == "__main__":
    unittest.main()
