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

    def test_run_stops_at_the_paid_boundary_in_this_task_without_a_process(self) -> None:
        for name in ("s1", "s2a", "s2b", "verbose-probe"):
            code, out, err = run_cli([name, "--run"], self.env)
            self.assertEqual(code, 2, name)
            self.assertIn("paid path is enabled in task 3", err)
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


if __name__ == "__main__":
    unittest.main()
