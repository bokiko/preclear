"""Zero-token tests for the clean-clone bootstrap (plan 04-19; RERUN-02; D-09, D-10, D-11, D-12, D-13b).

No test starts a real claude and no test clones the real repository: every source is a scratch repository built from
copies of the tracked harness, and the only claude executed is a fake or scripted one written by pc_testutil or by this
file into a scratch folder. The clone's own scripts run as child processes under the scrubbed environment, exactly as
the bootstrap runs them. Every folder comes from tempfile and is never deleted. A refusal is never asserted by the value
that caused it, and leak-shaped strings come only from pc_seeds.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import pc_cleanclone
import pc_exitcodes
import pc_seeds
import pc_spike
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
SYSTEM_DIRS = pc_testutil.SYSTEM_DIRS
BANNER = "2.1.310 (Claude Code)"
START = datetime.datetime(2026, 11, 20, 8, 0, 0, tzinfo=datetime.timezone.utc)
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
ROW1 = "row1-wrong-binding"
AT = chr(64)  # built, not typed, so no line of this file has an address shape
PUBLICATION = "publication-2026-10-20"


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def git_in(folder: str, *args: str) -> str:
    env = pc_testutil.git_env({"PATH": os.pathsep.join(SYSTEM_DIRS)})
    done = subprocess.run(
        ["git", "-C", folder] + list(args), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    )
    return done.stdout.decode("utf-8")


def copy_tree_into(source: str, target: str, ignore=None) -> None:
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copytree(source, target, ignore=ignore)


def build_source(base: str, selftest_text=None) -> str:
    """A scratch repository holding what a clone needs to run the matrix: the skill, the references, the fixtures, the
    harness without its tests, the publication folder (the comparison's reference) and every registry source."""
    import pc_rows

    repo = os.path.join(base, "source")
    os.makedirs(repo)
    for name in ("SKILL.md", ".gitignore"):
        shutil.copy2(os.path.join(ROOT, name), os.path.join(repo, name))
    copy_tree_into(os.path.join(ROOT, "references"), os.path.join(repo, "references"))
    copy_tree_into(os.path.join(ROOT, "tests", "fixtures"), os.path.join(repo, "tests", "fixtures"))
    copy_tree_into(
        HARNESS_DIR, os.path.join(repo, "tests", "harness"),
        ignore=shutil.ignore_patterns("__pycache__", "test_*.py", "*.pyc"),
    )
    copy_tree_into(
        os.path.join(ROOT, "tests", "evidence", PUBLICATION), os.path.join(repo, "tests", "evidence", PUBLICATION)
    )
    for entry in pc_rows.build_registry():
        if not entry.implemented:
            continue
        for relative, kind in entry.sources:
            source = os.path.join(ROOT, *relative.split("/"))
            target = os.path.join(repo, *relative.split("/"))
            if os.path.lexists(target):
                continue
            if kind == "dir" and os.path.isdir(source):
                copy_tree_into(source, target)
            elif kind != "dir" and os.path.isfile(source):
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(source, target)
    if selftest_text is not None:
        selftest = os.path.join(repo, "tests", "harness", "selftest")
        with open(selftest, "w", encoding="utf-8") as handle:
            handle.write(selftest_text)
        os.chmod(selftest, 0o755)
    env = pc_testutil.git_env({"PATH": os.pathsep.join(SYSTEM_DIRS)})
    for args in (["init", "-q"], ["symbolic-ref", "HEAD", "refs/heads/main"], ["add", "-A"],
                 ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "scratch source"]):
        subprocess.run(["git", "-C", repo] + args, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    return repo


_SOURCES = {}


def shared_source() -> str:
    """One scratch source repository per test process; tests only ever clone from it."""
    if "plain" not in _SOURCES:
        _SOURCES["plain"] = build_source(os.path.realpath(tempfile.mkdtemp(prefix="pc-ccsrc-")))
    return _SOURCES["plain"]


ENV_LOGGING_CLAUDE = """#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd)
case "$*" in
  "--version")
    printf '%s\\n' '__BANNER__'
    exit 0
    ;;
  "auth status --json")
    /usr/bin/env | /usr/bin/cut -d= -f1 | /usr/bin/sort > "$here/names.log"
    printf '%s\\n' "$HOME" > "$here/home.log"
    printf '%s\\n' '{"loggedIn": true}'
    exit 0
    ;;
esac
printf '%s\\n' "$*" >> "$here/tripwire.log"
exit 97
"""


def make_env_logging_claude(folder: str) -> str:
    path = os.path.join(folder, "claude")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(ENV_LOGGING_CLAUDE.replace("__BANNER__", BANNER))
    os.chmod(path, 0o755)
    return path


class World(object):
    """A scratch caller: a main tree (a clone of the scratch source), a runs root, a harness home, a fake home, a
    folder holding the claude double and an environment full of variables the child must never see."""

    def __init__(self, source=None, logged_in=True, banner=BANNER, claude="fake", stages=None) -> None:
        self.source = source or shared_source()
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-cc-"))
        self.main = os.path.join(self.base, "main")
        self.home = os.path.join(self.base, "home")
        self.harness = os.path.join(self.base, "harness")
        self.runs = os.path.join(self.base, "callerruns")
        self.bin = os.path.join(self.base, "bin")
        for folder in (self.home, self.bin):
            os.makedirs(folder)
        env = pc_testutil.git_env({"PATH": os.pathsep.join(SYSTEM_DIRS)})
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", self.source, self.main], env=env,
                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if stages is not None:
            self.claude = pc_testutil.make_scripted_claude(self.bin, {"stages": stages})
        elif claude == "logging":
            self.claude = make_env_logging_claude(self.bin)
        else:
            self.claude = pc_testutil.make_fake_claude(self.bin, banner, logged_in)
        self.noise = {
            "ANTHROPIC_API_KEY": pc_seeds.anthropic_key(),
            "GIT_AUTHOR_NAME": "Noise Author",
            "GIT_AUTHOR_EMAIL": pc_seeds.email("noise", "example.com"),
            "CLAUDE_CONFIG_DIR": os.path.join(self.base, "other-config"),
            "SSH_AUTH_SOCK": os.path.join(self.base, "agent.sock"),
            "AWS_SECRET_ACCESS_KEY": "noise-secret-value",
        }
        self.env = {
            "PATH": os.pathsep.join(list(SYSTEM_DIRS) + [self.bin]),
            "HOME": self.home,
            "LANG": "en_US.UTF-8",
            "TERM": "xterm-256color",
            "PRECLEAR_HARNESS_HOME": self.harness,
            "PRECLEAR_RUNS_ROOT": self.runs,
        }
        self.env.update(self.noise)
        self.ticks = 0

    def clock(self) -> datetime.datetime:
        self.ticks += 1
        return START + datetime.timedelta(seconds=self.ticks)

    def run(self, args, clock=None, env=None):
        out = io.StringIO()
        err = io.StringIO()
        code = pc_cleanclone.main(
            list(args), env=dict(self.env if env is None else env), repo_root=self.main, clock=clock or self.clock,
            out=out, err=err,
        )
        return code, out.getvalue(), err.getvalue()

    def folders(self) -> list:
        return sorted(os.listdir(self.runs)) if os.path.isdir(self.runs) else []


class Cloned(object):
    """A clone made through the bootstrap's own functions: the folder D, the child environment and the clone."""

    def __init__(self, world: World, real_home: bool = False, source=None) -> None:
        self.world = world
        os.makedirs(world.runs, exist_ok=True)
        os.makedirs(world.harness, exist_ok=True)
        self.folder = pc_cleanclone.make_clone_folder(world.runs, world.clock)
        self.git = pc_cleanclone.find_git(world.env)
        self.env = pc_cleanclone.build_child_env(
            self.folder, os.path.realpath(world.harness), world.bin, world.env, real_home
        )
        self.head = pc_cleanclone.clone_repository(source or world.source, self.folder, self.git)
        self.repo = os.path.join(self.folder, "repo")

    def pre(self, env=None):
        out = io.StringIO()
        result = pc_cleanclone.pre_assertions(self.folder, self.env if env is None else env, self.git, out)
        return result, out.getvalue()


class CloneLayoutTests(unittest.TestCase):
    def test_the_folder_holds_three_siblings_and_the_clone_creates_the_repo_folder(self) -> None:
        world = World()
        os.makedirs(world.runs)
        folder = pc_cleanclone.make_clone_folder(world.runs, world.clock)
        self.assertEqual(sorted(os.listdir(folder)), ["home", "runs"])
        self.assertEqual(os.listdir(os.path.join(folder, "runs")), [])
        self.assertEqual(os.listdir(os.path.join(folder, "home")), [])
        self.assertEqual(os.path.dirname(folder), os.path.realpath(world.runs))
        self.assertRegex(os.path.basename(folder), r"clean-clone-[0-9]{8}T[0-9]{6}Z\Z")

    def test_a_second_creation_of_the_same_name_is_refused_and_nothing_is_reused_or_changed(self) -> None:
        world = World()
        os.makedirs(world.runs)
        fixed = lambda: START
        folder = pc_cleanclone.make_clone_folder(world.runs, fixed)
        marker = os.path.join(folder, "home", "kept.txt")
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write("kept\n")
        with self.assertRaises(pc_cleanclone.CloneFolderTaken):
            pc_cleanclone.make_clone_folder(world.runs, fixed)
        self.assertEqual(read_text(marker), "kept\n")
        self.assertEqual(sorted(os.listdir(folder)), ["home", "runs"])

    def test_the_runs_folder_neither_holds_nor_lies_inside_the_clone_and_the_runs_root_rule_accepts_it(self) -> None:
        cloned = Cloned(World())
        runs = os.path.join(cloned.folder, "runs")
        self.assertTrue(os.path.isdir(cloned.repo))
        self.assertFalse(runs == cloned.repo or runs.startswith(cloned.repo + os.sep))
        self.assertFalse(cloned.repo.startswith(runs + os.sep))
        accepted = pc_spike.runs_root(cloned.env, home_dir=cloned.env["HOME"], repo_root=cloned.repo)
        self.assertEqual(accepted, os.path.realpath(runs))

    def test_the_clone_holds_no_identity_key_and_no_pin_even_when_the_source_has_them(self) -> None:
        world = World()
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-ccsrc-"))
        source = build_source(base)
        git_in(source, "config", "--local", "user.name", "Planted Name")
        git_in(source, "config", "--local", "preclear.pinnedIdentity", "planted")
        cloned = Cloned(world, source=source)
        keys = [line.split("=", 1)[0].lower() for line in git_in(cloned.repo, "config", "--local", "--list").splitlines()]
        self.assertEqual([key for key in keys if key.startswith("user.") or key == "preclear.pinnedidentity"], [])

    def test_the_heads_are_forty_hex_characters_and_equal_for_a_clone_of_the_source(self) -> None:
        world = World()
        cloned = Cloned(world)
        self.assertRegex(cloned.head, HEX40)
        self.assertEqual(cloned.head, git_in(world.source, "rev-parse", "HEAD").strip())
        self.assertEqual(pc_cleanclone.head_of(world.main, cloned.git, pc_cleanclone.git_env(cloned.folder)), cloned.head)

    def test_an_unreadable_source_makes_no_head_and_nothing_is_printed_by_git(self) -> None:
        world = World()
        os.makedirs(world.runs)
        folder = pc_cleanclone.make_clone_folder(world.runs, world.clock)
        empty = os.path.join(world.base, "not-a-repository")
        os.makedirs(empty)
        self.assertIsNone(pc_cleanclone.clone_repository(empty, folder, pc_cleanclone.find_git(world.env)))

    def test_the_source_rules_take_https_without_credentials_or_an_existing_folder_only(self) -> None:
        world = World()
        good = "https://example.invalid/owner/project.git"
        self.assertEqual(pc_cleanclone.classify_source(good), ("url", good))
        self.assertEqual(pc_cleanclone.classify_source(world.source), ("local", os.path.realpath(world.source)))
        for bad in (
            "https://user:secret" + AT + "example.invalid/owner/project.git",
            "https://example.invalid",
            "http://example.invalid/owner/project.git",
            "ssh://example.invalid/owner/project.git",
            "git" + AT + "example.invalid:owner/project.git",
            "https://example.invalid/owner/project.git\nextra",
            "-" + world.source,
            os.path.join(world.base, "absent"),
            "",
            None,
            5,
        ):
            self.assertIsNone(pc_cleanclone.classify_source(bad), repr(bad))

    def test_the_default_source_is_the_origin_address_of_the_main_tree_read_at_run_time(self) -> None:
        world = World()
        git = pc_cleanclone.find_git(world.env)
        found = pc_cleanclone.default_source(world.main, git, pc_cleanclone._bare_git_env())
        self.assertEqual(os.path.realpath(found), os.path.realpath(world.source))
        bare = os.path.join(world.base, "no-origin")
        os.makedirs(bare)
        git_in(bare, "init", "-q")
        self.assertIsNone(pc_cleanclone.default_source(bare, git, pc_cleanclone._bare_git_env()))


class ChildEnvTests(unittest.TestCase):
    def build(self, world, real_home=False):
        folder = os.path.join(world.base, "D")
        return pc_cleanclone.build_child_env(folder, world.harness, world.bin, world.env, real_home), folder

    def test_the_environment_holds_exactly_the_seven_names_and_nothing_else(self) -> None:
        world = World()
        env, folder = self.build(world)
        self.assertEqual(sorted(env), sorted(pc_cleanclone.ALLOWED_NAMES))
        self.assertEqual(len(pc_cleanclone.ALLOWED_NAMES), 7)
        self.assertEqual(pc_cleanclone.child_env_names(env), sorted(pc_cleanclone.ALLOWED_NAMES))

    def test_the_values_are_the_throwaway_home_the_scrubbed_path_the_harness_home_and_the_clone_runs_root(self) -> None:
        world = World()
        env, folder = self.build(world)
        self.assertEqual(env["HOME"], os.path.join(folder, "home"))
        self.assertEqual(env["PRECLEAR_RUNS_ROOT"], os.path.join(folder, "runs"))
        self.assertEqual(env["PRECLEAR_HARNESS_HOME"], world.harness)
        self.assertEqual(env["PATH"], pc_cleanclone.SYSTEM_PATH + os.pathsep + world.bin)
        self.assertEqual(env["DISABLE_AUTOUPDATER"], "1")
        self.assertEqual(env["TERM"], "xterm-256color")
        self.assertEqual(env["LANG"], "en_US.UTF-8")

    def test_nothing_of_a_noisy_caller_environment_reaches_the_builder_result(self) -> None:
        world = World()
        env, _folder = self.build(world)
        joined = "\n".join(list(env) + list(env.values()))
        for name, value in world.noise.items():
            self.assertNotIn(name, env)
            self.assertNotIn(value, joined)

    def test_a_child_started_through_the_builder_sees_only_the_seven_names(self) -> None:
        world = World()
        env, _folder = self.build(world)
        done = subprocess.run(["/usr/bin/env"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True)
        names = sorted(line.split("=", 1)[0] for line in done.stdout.decode("utf-8").splitlines() if "=" in line)
        self.assertEqual(names, sorted(pc_cleanclone.ALLOWED_NAMES))
        text = done.stdout.decode("utf-8")
        for value in world.noise.values():
            self.assertNotIn(value, text)

    def test_the_real_home_is_given_only_with_the_explicit_flag(self) -> None:
        world = World()
        env, folder = self.build(world, real_home=False)
        self.assertNotEqual(env["HOME"], world.home)
        env, folder = self.build(world, real_home=True)
        self.assertEqual(env["HOME"], world.home)
        self.assertEqual(sorted(env), sorted(pc_cleanclone.ALLOWED_NAMES))

    def test_a_term_or_lang_that_is_not_a_plain_word_is_replaced_by_the_fixed_default(self) -> None:
        world = World()
        folder = os.path.join(world.base, "D")
        odd = dict(world.env, TERM="x y;z", LANG="$(id)")
        env = pc_cleanclone.build_child_env(folder, world.harness, world.bin, odd)
        self.assertEqual((env["TERM"], env["LANG"]), (pc_cleanclone.DEFAULT_TERM, pc_cleanclone.DEFAULT_LANG))
        env = pc_cleanclone.build_child_env(folder, world.harness, world.bin, {})
        self.assertEqual((env["TERM"], env["LANG"]), (pc_cleanclone.DEFAULT_TERM, pc_cleanclone.DEFAULT_LANG))

    def test_a_folder_name_with_the_path_separator_is_refused(self) -> None:
        world = World()
        folder = os.path.join(world.base, "D")
        with self.assertRaises(ValueError):
            pc_cleanclone.build_child_env(folder, world.harness, world.bin + os.pathsep + "/extra", world.env)

    def test_the_build_folder_is_not_added_twice_when_it_is_a_system_folder(self) -> None:
        world = World()
        folder = os.path.join(world.base, "D")
        env = pc_cleanclone.build_child_env(folder, world.harness, "/usr/bin", world.env)
        self.assertEqual(env["PATH"], pc_cleanclone.SYSTEM_PATH)


class PreAssertionTests(unittest.TestCase):
    def test_a_good_clone_prints_zero_counts_and_succeeds(self) -> None:
        cloned = Cloned(World())
        result, text = cloned.pre()
        self.assertEqual(result.code, 0, text)
        counts = [line for line in text.splitlines() if line.startswith("pre: ") and "entries" not in line]
        self.assertEqual(len(counts), 8, text)
        for line in counts[:7]:
            self.assertTrue(line.endswith(": 0"), line)
        self.assertIn("runs root usable under the child environment: yes", text)
        self.assertIn(ROW1, result.entry_ids)
        self.assertEqual(len(result.entry_ids), 21)
        self.assertIn("entries in the clone's list: 21", text)
        self.assertEqual((result.path_binaries, result.helper_files), (0, 0))

    def test_a_runs_folder_in_the_clone_ends_with_exit_11(self) -> None:
        cloned = Cloned(World())
        os.makedirs(os.path.join(cloned.repo, "runs"))
        result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("runs folders or tracked runs paths in the clone: 1", text)

    def test_a_tracked_runs_path_counts(self) -> None:
        world = World()
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-ccsrc-"))
        source = build_source(base)
        os.makedirs(os.path.join(source, "runs"))
        with open(os.path.join(source, "runs", "note.txt"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        git_in(source, "add", "-f", "runs/note.txt")
        git_in(source, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "tracked runs path")
        cloned = Cloned(world, source=source)
        result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("runs folders or tracked runs paths in the clone: 2", text)

    def test_an_executable_checkpoint_on_the_scrubbed_path_ends_with_exit_11(self) -> None:
        world = World()
        planted = os.path.join(world.bin, "checkpoint")
        with open(planted, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        os.chmod(planted, 0o755)
        cloned = Cloned(world)
        result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("checkpoint executables in the folders of the scrubbed PATH: 1", text)
        self.assertIn("checkpoint found by a search of the scrubbed PATH: 1", text)
        self.assertEqual(result.path_binaries, 1)

    def test_a_non_executable_file_named_checkpoint_on_the_path_is_not_an_executable(self) -> None:
        world = World()
        with open(os.path.join(world.bin, "checkpoint"), "w", encoding="utf-8") as handle:
            handle.write("notes\n")
        cloned = Cloned(world)
        result, text = cloned.pre()
        self.assertEqual(result.code, 0, text)
        self.assertEqual(result.path_binaries, 0)

    def test_a_file_named_checkpoint_anywhere_in_the_clone_ends_with_exit_11(self) -> None:
        cloned = Cloned(World())
        folder = os.path.join(cloned.repo, "deep", "er")
        os.makedirs(folder)
        with open(os.path.join(folder, "checkpoint"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("files named checkpoint in the clone: 1", text)
        self.assertEqual(result.helper_files, 1)

    def test_files_that_merely_contain_the_word_are_not_counted(self) -> None:
        cloned = Cloned(World())
        result, text = cloned.pre()
        self.assertEqual(result.code, 0, text)
        self.assertTrue(os.path.isfile(os.path.join(cloned.repo, "tests", "harness", "checkpoint-wrapper")))
        self.assertTrue(os.path.isfile(os.path.join(cloned.repo, "tests", "harness", "checkpoint_stub.py")))
        self.assertEqual(result.helper_files, 0)

    def test_a_file_named_checkpoint_under_the_throwaway_home_ends_with_exit_11(self) -> None:
        cloned = Cloned(World())
        folder = os.path.join(cloned.folder, "home", ".claude", "hooks")
        os.makedirs(folder)
        with open(os.path.join(folder, "checkpoint"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("files named checkpoint under the throwaway home: 1", text)

    def test_an_identity_key_or_the_pin_or_a_hook_path_in_the_clone_configuration_ends_with_exit_11(self) -> None:
        for key, label in (
            ("user.name", "identity keys"),
            ("user.email", "identity keys"),
            ("preclear.pinnedIdentity", "identity keys"),
            ("core.hooksPath", "hook path keys"),
        ):
            cloned = Cloned(World())
            git_in(cloned.repo, "config", "--local", key, "planted")
            result, text = cloned.pre()
            self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL, key)
            self.assertIn("%s in the clone's local configuration: 1" % label, text)

    def test_an_empty_list_ends_with_exit_11(self) -> None:
        cloned = Cloned(World())
        with mock.patch.object(pc_cleanclone, "list_entries", return_value=()):
            result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("entries in the clone's list: 0", text)
        self.assertEqual(result.entry_ids, ())

    def test_a_list_that_cannot_be_read_ends_with_exit_11(self) -> None:
        cloned = Cloned(World())
        with mock.patch.object(pc_cleanclone, "list_entries", return_value=None):
            result, text = cloned.pre()
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_FAIL)

    def test_a_runs_root_the_rule_refuses_ends_with_exit_12(self) -> None:
        cloned = Cloned(World())
        inside = dict(cloned.env, PRECLEAR_RUNS_ROOT=os.path.join(cloned.repo, "scratch"))
        result, text = cloned.pre(env=inside)
        self.assertEqual(result.code, pc_exitcodes.PREFLIGHT_BLOCKED)
        self.assertIn("runs root usable under the child environment: no", text)

    def test_the_lists_ids_are_the_clones_own(self) -> None:
        cloned = Cloned(World())
        ids = pc_cleanclone.list_entries(cloned.folder, cloned.env, sys.executable)
        self.assertEqual(len(ids), 21)
        self.assertEqual(len(set(ids)), 21)


class PreflightOnlyTests(unittest.TestCase):
    def test_a_fake_claude_that_is_logged_in_exits_0_and_prints_the_ok_line(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("OK: preflight passed for Claude Code 2.1.310", out)
        self.assertIn("stub ok", out)
        self.assertIn("preflight-only: no row and no model is started", out)

    def test_it_starts_no_row_no_model_and_writes_no_ledger_line(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(pc_testutil.read_tripwire(world.bin), [])
        (name,) = world.folders()
        self.assertEqual(os.listdir(os.path.join(world.runs, name, "runs")), [])
        self.assertEqual(sorted(os.listdir(world.harness)), ["claude-config"])
        self.assertEqual(os.listdir(os.path.join(world.harness, "claude-config")), [])
        evidence = os.listdir(os.path.join(world.runs, name, "repo", "tests", "evidence"))
        self.assertFalse([entry for entry in evidence if entry.startswith("rerun-")])

    def test_the_auth_probe_sees_the_harness_config_folder_and_none_of_the_noise(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        (line,) = pc_testutil.read_env_log(world.bin)
        config, key, token = line.split("|")
        self.assertEqual(config, os.path.join(world.harness, "claude-config"))
        self.assertEqual((key, token), ("unset", "unset"))

    def test_a_logged_out_claude_exits_12_and_prints_the_fix_line(self) -> None:
        world = World(logged_in=False)
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn("claude auth login", out)
        self.assertIn("BLOCKED", out)
        self.assertNotIn(world.harness, out)

    def test_an_untested_version_exits_13(self) -> None:
        world = World(banner="9.9.9 (Claude Code)")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, pc_exitcodes.VERSION_UNTESTED, out + err)

    def test_the_throwaway_home_is_what_the_claude_double_runs_with_and_the_noise_never_arrives(self) -> None:
        world = World(claude="logging")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        (name,) = world.folders()
        home = read_text(os.path.join(world.bin, "home.log")).strip()
        self.assertEqual(home, os.path.join(world.runs, name, "home"))
        seen = set(read_text(os.path.join(world.bin, "names.log")).split())
        for noisy in world.noise:
            if noisy != "CLAUDE_CONFIG_DIR":  # the harness itself sets this one to its own folder, checked above
                self.assertNotIn(noisy, seen)
        allowed = set(pc_cleanclone.ALLOWED_NAMES) | {"CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "PWD", "SHLVL", "_", "OLDPWD"}
        self.assertEqual(sorted(seen - allowed), [])

    def test_the_real_home_flag_keeps_the_callers_home_prints_the_warning_and_records_the_kind(self) -> None:
        world = World(claude="logging")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only", "--real-home"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(read_text(os.path.join(world.bin, "home.log")).strip(), world.home)
        self.assertIn(pc_cleanclone.MESSAGE_REAL_HOME, out)
        self.assertIn("home kind: real", out)

    def test_the_default_home_kind_is_throwaway_and_no_warning_is_printed(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertIn("home kind: throwaway", out)
        self.assertNotIn("WARNING", out)

    def test_the_heads_and_their_equality_are_printed(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        head = git_in(world.source, "rev-parse", "HEAD").strip()
        self.assertIn("clone head: %s" % head, out)
        self.assertIn("main tree head: %s" % head, out)
        self.assertIn("heads equal: yes", out)

    def test_heads_that_differ_are_printed_as_not_equal(self) -> None:
        world = World()
        git_in(world.main, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "local only")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("heads equal: no", out)

    def test_a_pre_assertion_refusal_stops_before_the_probe(self) -> None:
        world = World()
        planted = os.path.join(world.bin, "checkpoint")
        with open(planted, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        os.chmod(planted, 0o755)
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, out + err)
        self.assertIn("stopped before any step that starts a model", out)
        self.assertNotIn("preflight passed", out)
        self.assertEqual(pc_testutil.read_env_log(world.bin), [])

    def test_the_folder_stays_in_place_and_a_second_run_in_the_same_second_is_refused(self) -> None:
        world = World()
        fixed = lambda: START
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"], clock=fixed)
        self.assertEqual(code, 0, out + err)
        (name,) = world.folders()
        marker = os.path.join(world.runs, name, "home", "kept.txt")
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write("kept\n")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"], clock=fixed)
        self.assertEqual(code, pc_exitcodes.RUNROOT_COLLISION, out + err)
        self.assertEqual(world.folders(), [name])
        self.assertEqual(read_text(marker), "kept\n")

    def test_a_missing_origin_without_a_source_is_a_usage_error(self) -> None:
        world = World()
        git_in(world.main, "remote", "remove", "origin")
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, pc_exitcodes.USAGE, out + err)
        self.assertEqual(world.folders(), [])
        code, out, err = world.run(["--claude", world.claude, "--preflight-only", "--source", world.source])
        self.assertEqual(code, 0, out + err)


if __name__ == "__main__":
    unittest.main()
