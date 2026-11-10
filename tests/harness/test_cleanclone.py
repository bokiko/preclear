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


# ---------------------------------------------------------------------------------------------
# Task 2: the scripted full run, the post-assertions and the copy-back
# ---------------------------------------------------------------------------------------------

PATH_SHAPE = re.compile(r"(?<![\w.-])/(?:Users|home|private|var|tmp|opt|Volumes)/")


def registry_specs() -> list:
    import pc_rows

    return [entry for entry in pc_rows.build_registry() if entry.implemented]


def clean_stages(first=None) -> list:
    """The scripted stages of every implemented entry in registry order; first may reshape the first entry's stages."""
    stages = []
    for index, spec in enumerate(registry_specs()):
        part = pc_testutil.default_row_stages(spec)
        if index == 0 and first is not None:
            part = first(part)
        stages += part
    return stages


def stopped_first(part: list) -> list:
    return pc_testutil.stages_with(part, 0, exit=1)[:1]


def incomplete_first(part: list) -> list:
    return pc_testutil.stages_with(part, 0, no_result=True)[:1]


class Run(object):
    """One bootstrap run against a scratch world, kept for the assertions of several tests."""

    def __init__(self, stages, args, source=None, patch=None, **world_options) -> None:
        self.world = World(source=source, stages=stages, **world_options)
        argv = ["--claude", self.world.claude] + list(args)
        if patch is None:
            self.code, self.out, self.err = self.world.run(argv)
        else:
            with patch(self.world):
                self.code, self.out, self.err = self.world.run(argv)

    @property
    def clone_folder(self) -> str:
        (name,) = self.world.folders()
        return os.path.join(self.world.runs, name)

    def main_evidence(self) -> list:
        return sorted(os.listdir(os.path.join(self.world.main, "tests", "evidence")))

    def dated(self) -> str:
        (name,) = [entry for entry in self.main_evidence() if entry.startswith("rerun-") and "wave" not in entry
                   and not entry.endswith("claude-sonnet-5-5-triple")
                   and entry not in COMMITTED_RERUNS]
        return os.path.join(self.world.main, "tests", "evidence", name)


COMMITTED_RERUNS = frozenset(
    name for name in os.listdir(os.path.join(ROOT, "tests", "evidence")) if name.startswith("rerun-")
)
_RUNS = {}


def cached_run(key, stages_of, args, patch=None) -> "Run":
    if key not in _RUNS:
        _RUNS[key] = Run(stages_of(), args, patch=patch)
    return _RUNS[key]


def complete_run() -> "Run":
    return cached_run("complete", clean_stages, ["--budget", "25.00"])


def budget_run() -> "Run":
    return cached_run("budget", clean_stages, ["--budget", "2.30"])


def stopped_run() -> "Run":
    return cached_run("stopped", lambda: clean_stages(stopped_first), ["--budget", "25.00"])


def incomplete_run() -> "Run":
    return cached_run("incomplete", lambda: clean_stages(incomplete_first), ["--budget", "25.00"])


def tamper(world):
    """Patch post_assertions so one wrapper's stub file names another file just before the counts are read."""
    original = pc_cleanclone.post_assertions

    def changed(folder, evidence_folder, out, interpreter=None):
        runs = os.path.join(folder, "runs")
        for name in sorted(os.listdir(runs)):
            stub = os.path.join(runs, name, "wrapper", "stub")
            if os.path.isfile(stub):
                with open(stub, "w", encoding="utf-8") as handle:
                    handle.write(os.path.join(folder, "repo", "tests", "harness", "pc_matrix.py"))
                break
        return original(folder, evidence_folder, out, interpreter)

    return mock.patch.object(pc_cleanclone, "post_assertions", changed)


def tampered_run() -> "Run":
    return cached_run("tampered", lambda: clean_stages(incomplete_first), ["--budget", "25.00"], patch=tamper)


def facts_of(run: "Run") -> dict:
    import pc_baseline

    facts = pc_baseline.read_clone_facts(os.path.join(run.clone_folder, pc_cleanclone.CLONE_FACTS_NAME))
    assert facts is not None
    return facts


class ScriptedFullRunTests(unittest.TestCase):
    def test_a_complete_run_exits_0_and_files_one_folder_per_list_entry_in_the_main_tree(self) -> None:
        run = complete_run()
        self.assertEqual(run.code, 0, run.out + run.err)
        ids = pc_cleanclone.list_entries(run.clone_folder, pc_cleanclone.build_child_env(
            run.clone_folder, run.world.harness, run.world.bin, run.world.env), sys.executable)
        self.assertEqual(len(ids), 21)
        names = [n for n in os.listdir(run.dated()) if os.path.isdir(os.path.join(run.dated(), n))]
        self.assertEqual(sorted(names), sorted(ids))
        self.assertIn("entries: 21, folders: 21\n", run.out)
        self.assertNotIn("not run", run.out.split("entries: 21")[-1])

    def test_the_steps_run_in_the_order_of_the_plan(self) -> None:
        run = complete_run()
        order = [
            "pre: entries in the clone's list: 21",
            "step: dry run of the whole matrix with the same budget",
            "step: stub check and strict preflight",
            "step: the matrix, from the clone",
            "matrix exit code: 0",
            "post: helper calls:",
            "step: finalize in the clone",
            "step: copy-back through the leak gate",
            "entries: 21, folders: 21",
        ]
        positions = [run.out.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("self-test", run.out, "the self-test runs only on request")

    def test_the_baseline_names_the_run_state_and_the_environment_names_one_per_line(self) -> None:
        run = complete_run()
        readme = read_text(os.path.join(run.dated(), "README.md"))
        self.assertIn("Run state: complete", readme)
        self.assertEqual(
            read_text(os.path.join(run.dated(), "environment-names.txt")).split(),
            sorted(pc_cleanclone.ALLOWED_NAMES),
        )

    def test_the_clone_facts_file_is_valid_and_holds_names_and_counts_only(self) -> None:
        run = complete_run()
        facts = facts_of(run)
        self.assertEqual(facts["env_names"], sorted(pc_cleanclone.ALLOWED_NAMES))
        self.assertEqual(facts["helper_calls_other"], 0)
        self.assertEqual(facts["helper_calls"], facts["helper_calls_stub"])
        self.assertGreater(facts["helper_calls"], 0)
        self.assertEqual((facts["path_checkpoint_binaries"], facts["helper_files_in_clone"]), (0, 0))
        self.assertEqual((facts["source_kind"], facts["home_kind"]), ("local", "throwaway"))
        self.assertEqual(facts["clone_head"], git_in(run.world.source, "rev-parse", "HEAD").strip())
        text = read_text(os.path.join(run.clone_folder, pc_cleanclone.CLONE_FACTS_NAME))
        self.assertIsNone(PATH_SHAPE.search(text))
        self.assertLessEqual(os.path.getsize(os.path.join(run.clone_folder, pc_cleanclone.CLONE_FACTS_NAME)), 65536)

    def test_the_facts_file_stays_outside_the_evidence_tree_and_the_copy(self) -> None:
        run = complete_run()
        self.assertNotIn(pc_cleanclone.CLONE_FACTS_NAME, os.listdir(run.dated()))
        self.assertTrue(os.path.isfile(os.path.join(run.clone_folder, pc_cleanclone.CLONE_FACTS_NAME)))

    def test_no_model_call_saw_a_variable_of_the_callers_noisy_environment(self) -> None:
        run = complete_run()
        calls = [json.loads(line) for line in read_text(os.path.join(run.world.bin, "calls.log")).splitlines()]
        self.assertGreater(len(calls), 50)
        for record in calls:
            for noisy in run.world.noise:
                if noisy != "CLAUDE_CONFIG_DIR":
                    self.assertNotIn(noisy, record["names"])
            self.assertTrue(record["env"]["CLAUDE_CONFIG_DIR"].startswith(os.path.realpath(run.world.harness)))
        self.assertEqual(pc_testutil.read_tripwire(run.world.bin), [])

    def test_the_clone_was_never_committed_pushed_or_given_an_identity(self) -> None:
        run = complete_run()
        repo = os.path.join(run.clone_folder, "repo")
        self.assertEqual(git_in(repo, "rev-list", "--count", "HEAD").strip(), git_in(run.world.source, "rev-list", "--count", "HEAD").strip())
        keys = [line.split("=", 1)[0].lower() for line in git_in(repo, "config", "--local", "--list").splitlines()]
        self.assertEqual([key for key in keys if key.startswith("user.") or key == "preclear.pinnedidentity"], [])

    def test_the_run_roots_and_the_clone_stay_in_place_after_the_run(self) -> None:
        run = complete_run()
        self.assertEqual(sorted(os.listdir(run.clone_folder)), ["clone-facts.json", "home", "repo", "runs"])
        self.assertGreater(len(os.listdir(os.path.join(run.clone_folder, "runs"))), 20)

    def test_a_budget_stop_files_the_finished_rows_as_a_partial_baseline_and_exits_18_after_the_copy_back(self) -> None:
        run = budget_run()
        self.assertEqual(run.code, pc_exitcodes.BUDGET_REFUSED, run.out + run.err)
        self.assertIn("matrix exit code: 18", run.out)
        self.assertIn("entries: 21, folders: 3, not run: 18\n", run.out)
        readme = read_text(os.path.join(run.dated(), "README.md"))
        self.assertIn("Run state: partial", readme)
        self.assertEqual(len([l for l in readme.splitlines() if l.startswith("Not run: ")]), 18)
        folders = sorted(n for n in os.listdir(run.dated()) if os.path.isdir(os.path.join(run.dated(), n)))
        self.assertEqual(folders, ["bound-ledger", "hub-memory", "plain-memory"])
        for line in readme.splitlines():
            if line.startswith("Not run: "):
                self.assertNotIn(line[len("Not run: "):], folders)
        self.assertLess(run.out.index("step: finalize"), run.out.index("step: copy-back"))

    def test_a_budget_too_small_for_any_row_is_refused_with_18_by_the_dry_run_and_nothing_is_filed(self) -> None:
        for budget in ("1.00", "abc"):
            world = World(stages=clean_stages())
            before = sorted(os.listdir(os.path.join(world.main, "tests", "evidence")))
            code, out, err = world.run(["--claude", world.claude, "--budget", budget])
            self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
            self.assertNotIn("step: the matrix", out)
            self.assertNotIn("copy-back", out)
            self.assertEqual(sorted(os.listdir(os.path.join(world.main, "tests", "evidence"))), before)
            self.assertFalse(os.path.exists(os.path.join(world.bin, "calls.log")), "no model call was made")
            (name,) = world.folders()
            self.assertFalse(os.path.exists(os.path.join(world.runs, name, pc_cleanclone.CLONE_FACTS_NAME)))

    def test_a_stopped_row_exits_11_and_is_still_finalized_and_copied_back_as_a_stopped_folder(self) -> None:
        run = stopped_run()
        self.assertEqual(run.code, pc_exitcodes.PREFLIGHT_FAIL, run.out + run.err)
        self.assertIn("matrix exit code: 11", run.out)
        self.assertIn("entries: 21, folders: 21\n", run.out)
        self.assertTrue(os.path.isdir(os.path.join(run.dated(), "STOPPED-plain-memory")))
        self.assertTrue(os.path.isfile(os.path.join(run.dated(), "README.md")))

    def test_an_incomplete_stream_exits_19_and_is_still_finalized_and_copied_back(self) -> None:
        run = incomplete_run()
        self.assertEqual(run.code, pc_exitcodes.DENIAL_FOUND, run.out + run.err)
        self.assertIn("entries: 21, folders: 21\n", run.out)
        self.assertTrue(os.path.isdir(os.path.join(run.dated(), "STOPPED-plain-memory")))

    def test_a_call_that_hit_anything_but_the_clone_stub_ends_with_11_after_the_copy_back_and_takes_precedence(self) -> None:
        run = tampered_run()
        self.assertEqual(run.code, pc_exitcodes.PREFLIGHT_FAIL, run.out + run.err)
        self.assertIn("matrix exit code: 19", run.out)
        self.assertIn("post: run roots whose wrapper names anything else: 1", run.out)
        self.assertIn("entries: 21, folders: 21", run.out)
        self.assertLess(run.out.index("copy-back: promoted"), run.out.index("exit 11 after the copy-back"))
        facts = facts_of(run)
        self.assertEqual(facts["helper_calls"], facts["helper_calls_stub"] + facts["helper_calls_other"])
        self.assertTrue(os.path.isdir(run.dated()))

    def test_a_logged_out_claude_stops_at_the_probe_with_12_before_the_matrix(self) -> None:
        world = World(stages=clean_stages(), logged_in=False)
        # the scripted claude reads logged_in from its fake.json
        pc_testutil.write_scripted_config(world.bin, {"stages": clean_stages(), "logged_in": False})
        code, out, err = world.run(["--claude", world.claude, "--budget", "25.00"])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn("step: dry run", out)
        self.assertNotIn("step: the matrix", out)
        self.assertFalse(os.path.exists(os.path.join(world.bin, "calls.log")))

    def test_the_self_test_step_runs_first_and_a_failing_one_stops_the_run(self) -> None:
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-ccsrc-"))
        good = build_source(base, "#!/bin/sh\necho 'preclear harness self-test: 0 model calls'\nexit 0\n")
        world = World(source=good, stages=clean_stages())
        code, out, err = world.run(["--claude", world.claude, "--budget", "1.00", "--selftest"])
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertLess(out.index("0 model calls"), out.index("step: dry run"))
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-ccsrc-"))
        bad = build_source(base, "#!/bin/sh\necho 'one test did not run'\nexit 1\n")
        world = World(source=bad, stages=clean_stages())
        code, out, err = world.run(["--claude", world.claude, "--budget", "25.00", "--selftest"])
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("step: dry run", out)
        self.assertFalse(os.path.exists(os.path.join(world.bin, "calls.log")))

    def test_the_decision_about_filing_follows_the_matrix_code_and_the_folders_filed(self) -> None:
        for code in (0, 10, 11, 18, 19):
            self.assertTrue(pc_cleanclone.reaches_filing(code, 1), code)
            self.assertFalse(pc_cleanclone.reaches_filing(code, 0), code)
        for code in (2, 12, 13, 14, 15, 16, 17):
            self.assertFalse(pc_cleanclone.reaches_filing(code, 5), code)

    def test_a_usage_error_in_the_full_run_starts_nothing(self) -> None:
        world = World(stages=clean_stages())
        code, out, err = world.run(["--claude", world.claude])
        self.assertEqual(code, pc_exitcodes.USAGE, out + err)
        self.assertEqual(world.folders(), [])


class PostAssertionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World()
        self.cloned = Cloned(self.world)
        self.runs = os.path.join(self.cloned.folder, "runs")
        self.stub = os.path.join(self.cloned.repo, "tests", "harness", "checkpoint_stub.py")

    def root(self, name, stub="clone", py="interpreter", calls=None, wrapper=True):
        folder = os.path.join(self.runs, name)
        os.makedirs(folder)
        if not wrapper:
            return folder
        os.makedirs(os.path.join(folder, "wrapper"))
        if stub is not None:
            with open(os.path.join(folder, "wrapper", "stub"), "w", encoding="utf-8") as handle:
                handle.write(self.stub if stub == "clone" else stub)
        if py is not None:
            with open(os.path.join(folder, "wrapper", "py"), "w", encoding="utf-8") as handle:
                handle.write(os.path.realpath(sys.executable) if py == "interpreter" else py)
        if calls is not None:
            with open(os.path.join(folder, "wrapper", "calls.log"), "w", encoding="utf-8") as handle:
                for index in range(calls):
                    handle.write("2026-11-20T08:00:0%dZ CALL status\n2026-11-20T08:00:0%dZ EXIT 0\n" % (index, index))
        return folder

    def post(self, evidence=None):
        out = io.StringIO()
        return pc_cleanclone.post_assertions(self.cloned.folder, evidence, out), out.getvalue()

    def test_calls_to_the_clone_stub_are_counted_as_stub_calls(self) -> None:
        self.root("a", calls=3)
        self.root("b", calls=2)
        result, text = self.post()
        self.assertEqual((result.helper_calls, result.helper_calls_stub, result.helper_calls_other), (5, 5, 0))
        self.assertEqual((result.run_roots, result.stub_roots, result.other_roots), (2, 2, 0))
        self.assertFalse(pc_cleanclone.post_refused(result))
        self.assertIn("post: helper calls to anything else: 0", text)

    def test_a_wrapper_that_names_another_stub_counts_its_calls_as_other(self) -> None:
        self.root("a", calls=1)
        self.root("b", stub=os.path.join(self.cloned.folder, "repo", "tests", "harness", "pc_matrix.py"), calls=4)
        result, text = self.post()
        self.assertEqual((result.helper_calls, result.helper_calls_stub, result.helper_calls_other), (5, 1, 4))
        self.assertEqual(result.other_roots, 1)
        self.assertTrue(pc_cleanclone.post_refused(result))

    def test_a_wrapper_that_names_another_interpreter_counts_as_other(self) -> None:
        self.root("a", py=os.path.join(self.cloned.folder, "repo", "tests", "harness", "pc_matrix.py"), calls=2)
        result, _text = self.post()
        self.assertEqual((result.helper_calls_stub, result.helper_calls_other), (0, 2))

    def test_a_missing_stub_or_py_file_counts_as_other_and_never_raises(self) -> None:
        self.root("a", stub=None, calls=1)
        self.root("b", py=None, calls=1)
        result, _text = self.post()
        self.assertEqual((result.stub_roots, result.other_roots, result.helper_calls_other), (0, 2, 2))

    def test_a_symlinked_stub_file_is_not_followed(self) -> None:
        folder = self.root("a", stub=None, calls=1)
        os.symlink(self.stub, os.path.join(folder, "wrapper", "stub"))
        result, _text = self.post()
        self.assertEqual((result.stub_roots, result.other_roots), (0, 1))

    def test_an_empty_or_absent_log_counts_zero_and_is_not_an_error(self) -> None:
        folder = self.root("a", calls=None)
        self.root("b", calls=0)
        with open(os.path.join(folder, "wrapper", "calls.log"), "x"):
            pass
        result, _text = self.post()
        self.assertEqual((result.helper_calls, result.other_roots), (0, 0))
        self.assertFalse(pc_cleanclone.post_refused(result))

    def test_a_run_root_without_a_wrapper_folder_is_not_a_wrapper_run_root(self) -> None:
        self.root("plain", wrapper=False)
        result, _text = self.post()
        self.assertEqual(result.run_roots, 0)

    def test_only_call_lines_are_counted(self) -> None:
        folder = self.root("a", calls=None)
        with open(os.path.join(folder, "wrapper", "calls.log"), "w", encoding="utf-8") as handle:
            handle.write("t CALL one\nt EXIT 0\nt CALLER notacall\n\nt CALL\nCALL two\n")
        result, _text = self.post()
        self.assertEqual(result.helper_calls, 2)

    def test_the_stub_digest_of_each_filed_row_must_equal_the_clone_stub_digest(self) -> None:
        import hashlib

        with open(self.stub, "rb") as handle:
            right = hashlib.sha256(handle.read()).hexdigest()
        evidence = os.path.join(self.cloned.folder, "evidence-copy")
        os.makedirs(evidence)
        for name, line in (
            ("ok", "%s  tests/harness/checkpoint_stub.py\n" % right),
            ("wrong", "%s  tests/harness/checkpoint_stub.py\n" % ("0" * 64)),
            ("unconfirmed", "UNCONFIRMED  tests/harness/checkpoint_stub.py\n"),
            ("plain", "%s  some/other/file\n" % right),
        ):
            os.makedirs(os.path.join(evidence, name))
            with open(os.path.join(evidence, name, "digests.txt"), "w", encoding="utf-8") as handle:
                handle.write(line)
        os.makedirs(os.path.join(evidence, "nofile"))
        result, text = self.post(evidence)
        self.assertEqual((result.digests_checked, result.digest_mismatches), (3, 2))
        self.assertTrue(pc_cleanclone.post_refused(result))
        self.assertIn("post: stub digest lines that differ from the clone stub: 2", text)

    def test_the_counts_are_printed_as_fixed_lines_without_a_path(self) -> None:
        self.root("a", calls=2)
        _result, text = self.post()
        self.assertEqual(len(text.splitlines()), 8)
        self.assertIsNone(PATH_SHAPE.search(text))


class FactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World()
        self.cloned = Cloned(self.world)
        self.pre = pc_cleanclone.Pre(0, 0, 0, ("a",))
        self.post = pc_cleanclone.Post(2, 2, 0, 2, 0, 5, 5, 0)

    def write(self, head=None, folder=None):
        return pc_cleanclone.write_clone_facts(
            folder or self.cloned.folder, sorted(pc_cleanclone.ALLOWED_NAMES), self.pre, self.post,
            head or self.cloned.head, "local", "throwaway",
        )

    def test_the_file_has_exactly_the_schema_keys_and_the_reader_accepts_it(self) -> None:
        import pc_baseline

        path = self.write()
        facts = pc_baseline.read_clone_facts(path)
        self.assertEqual(sorted(facts), sorted(pc_baseline.CLONE_FACTS_KEYS))
        self.assertEqual((facts["helper_calls"], facts["helper_calls_stub"], facts["helper_calls_other"]), (5, 5, 0))

    def test_an_existing_file_is_never_overwritten(self) -> None:
        path = self.write()
        before = read_text(path)
        self.assertIsNone(self.write())
        self.assertEqual(read_text(path), before)

    def test_a_head_that_is_not_forty_hex_characters_is_not_written_as_valid(self) -> None:
        self.assertIsNone(self.write(head="not-a-head"))


class CopyBackTests(unittest.TestCase):
    NAME = "rerun-2026-11-20-claude-sonnet-5-5"

    def setUp(self) -> None:
        self.world = World()
        self.stage = os.path.join(self.world.base, "stage", self.NAME)
        os.makedirs(os.path.join(self.stage, "row-a"))
        with open(os.path.join(self.stage, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("a plain readme\n")
        with open(os.path.join(self.stage, "row-a", "usage.txt"), "w", encoding="utf-8") as handle:
            handle.write("row total: 0.10\n")
        self.evidence = os.path.join(self.world.main, "tests", "evidence")

    def copy(self):
        out = io.StringIO()
        code = pc_cleanclone.copy_back(self.stage, self.world.main, self.world.harness, out)
        return code, out.getvalue()

    def test_the_folder_is_promoted_under_the_same_name(self) -> None:
        code, text = self.copy()
        self.assertEqual(code, 0, text)
        self.assertEqual(read_text(os.path.join(self.evidence, self.NAME, "README.md")), "a plain readme\n")
        self.assertEqual(read_text(os.path.join(self.evidence, self.NAME, "row-a", "usage.txt")), "row total: 0.10\n")
        self.assertIn("promoted 2 file(s)", text)

    def test_an_existing_destination_is_refused_with_17_and_left_unchanged(self) -> None:
        self.assertEqual(self.copy()[0], 0)
        with open(os.path.join(self.stage, "README.md"), "a", encoding="utf-8") as handle:
            handle.write("a later line\n")
        code, text = self.copy()
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, text)
        self.assertEqual(read_text(os.path.join(self.evidence, self.NAME, "README.md")), "a plain readme\n")

    def test_a_leak_shaped_string_in_a_clone_file_is_refused_and_nothing_is_created(self) -> None:
        with open(os.path.join(self.stage, "row-a", "note.txt"), "w", encoding="utf-8") as handle:
            handle.write("line %s\n" % pc_seeds.anthropic_key())
        before = sorted(os.listdir(self.evidence))
        code, text = self.copy()
        self.assertEqual(code, pc_exitcodes.LEAK_REFUSED, text)
        self.assertEqual(sorted(os.listdir(self.evidence)), before)
        self.assertNotIn(pc_seeds.anthropic_key(), text)

    def test_the_main_trees_local_deny_entries_apply_at_the_copy_back(self) -> None:
        entry = "a-local-only-entry-for-this-test"
        info = os.path.join(self.world.main, ".git", "info")
        os.makedirs(info, exist_ok=True)
        with open(os.path.join(info, "preclear-deny.txt"), "x", encoding="utf-8") as handle:
            handle.write(entry + "\n")
        with open(os.path.join(self.stage, "row-a", "note.txt"), "w", encoding="utf-8") as handle:
            handle.write("text with %s inside\n" % entry)
        before = sorted(os.listdir(self.evidence))
        code, text = self.copy()
        self.assertEqual(code, pc_exitcodes.LEAK_REFUSED, text)
        self.assertEqual(sorted(os.listdir(self.evidence)), before)
        self.assertNotIn(entry, text)


class ListingTests(unittest.TestCase):
    def folder(self, names, readme="a readme\n"):
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-list-"))
        for name in names:
            os.makedirs(os.path.join(base, name))
        with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as handle:
            handle.write(readme)
        return base

    def listing(self, base, ids):
        out = io.StringIO()
        code = pc_cleanclone.final_listing(base, ids, out)
        return code, out.getvalue()

    def test_every_id_as_a_folder_a_stopped_folder_or_a_skipped_folder_gives_the_short_line(self) -> None:
        base = self.folder(["row-a", "STOPPED-row-b", "SKIPPED-row-c", "row-d-attempt-2"])
        code, text = self.listing(base, ["row-a", "row-b", "row-c", "row-d"])
        self.assertEqual((code, text), (0, "entries: 4, folders: 4\n"))

    def test_a_partial_baseline_prints_the_not_run_count_and_the_parts_add_up(self) -> None:
        base = self.folder(["row-a"], "Run state: partial\nNot run: row-b\nNot run: row-c\n")
        code, text = self.listing(base, ["row-a", "row-b", "row-c"])
        self.assertEqual((code, text), (0, "entries: 3, folders: 1, not run: 2\n"))

    def test_an_id_with_neither_a_folder_nor_a_not_run_line_ends_with_11(self) -> None:
        base = self.folder(["row-a"], "Run state: partial\nNot run: row-b\n")
        code, text = self.listing(base, ["row-a", "row-b", "row-c"])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertIn("entries: 3, folders: 1, not run: 1", text)

    def test_a_folder_that_only_resembles_an_id_is_not_counted(self) -> None:
        base = self.folder(["row-a-extra", "xSTOPPED-row-a"])
        code, text = self.listing(base, ["row-a"])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL)

    def test_new_dated_folders_and_outcome_counts_ignore_links_and_files(self) -> None:
        base = self.folder(["a", "b"])
        evidence = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-list-")), "ev")
        os.makedirs(os.path.join(evidence, "rerun-old"))
        before = os.listdir(evidence)
        os.makedirs(os.path.join(evidence, "rerun-new"))
        os.makedirs(os.path.join(evidence, "other-new"))
        os.symlink(base, os.path.join(evidence, "rerun-link"))
        with open(os.path.join(evidence, "rerun-file"), "x", encoding="utf-8") as handle:
            handle.write("x\n")
        self.assertEqual(pc_cleanclone.new_dated_folders(evidence, before), ["rerun-new"])
        self.assertEqual(pc_cleanclone.outcome_folders(base), 2)
        self.assertEqual(pc_cleanclone.outcome_folders(None), 0)


# ---------------------------------------------------------------------------------------------
# Task 3: the real-home flag, usage errors and the no-path scans
# ---------------------------------------------------------------------------------------------


def login_name() -> str:
    try:
        import pwd

        return pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, KeyError, OSError):
        return os.environ.get("USER", "")


def path_text_hits(text: str, world: "World") -> list:
    """Names of the private things a printed text must never hold: every folder of the scratch world, the temp folder,
    the real home, the login and any home-shaped or temp-shaped path."""
    hits = []
    secrets = {
        "world base": world.base,
        "main tree": world.main,
        "source": world.source,
        "caller home": world.home,
        "harness home": world.harness,
        "runs root": world.runs,
        "build folder": world.bin,
        "build path": world.claude,
        "temp folder": tempfile.gettempdir(),
        "real home": os.path.expanduser("~"),
    }
    for label, value in secrets.items():
        if value and len(value) > 3 and value in text:
            hits.append(label)
    login = login_name()
    if len(login) >= 4 and re.search(r"(?<![A-Za-z0-9])" + re.escape(login) + r"(?![A-Za-z0-9])", text):
        hits.append("login")
    if PATH_SHAPE.search(text):
        hits.append("path shape")
    return hits


class RealHomeTests(unittest.TestCase):
    def test_a_full_run_with_the_flag_records_home_kind_real_in_the_clone_facts(self) -> None:
        run = Run(clean_stages(), ["--budget", "2.30", "--real-home"])
        self.assertEqual(run.code, pc_exitcodes.BUDGET_REFUSED, run.out + run.err)
        self.assertIn("home kind: real", run.out)
        self.assertIn(pc_cleanclone.MESSAGE_REAL_HOME, run.out)
        facts = facts_of(run)
        self.assertEqual(facts["home_kind"], "real")
        self.assertEqual(facts["env_names"], sorted(pc_cleanclone.ALLOWED_NAMES))
        self.assertEqual(path_text_hits(run.out + run.err, run.world), [])

    def test_a_full_run_without_the_flag_records_home_kind_throwaway(self) -> None:
        self.assertEqual(facts_of(budget_run())["home_kind"], "throwaway")
        self.assertIn("home kind: throwaway", budget_run().out)
        self.assertNotIn(pc_cleanclone.MESSAGE_REAL_HOME, budget_run().out)

    def test_the_throwaway_home_stays_empty_of_the_callers_files_and_the_flag_is_off_by_default(self) -> None:
        parser = pc_cleanclone.build_parser(io.StringIO(), io.StringIO())
        self.assertFalse(parser.parse_args(["--claude", "x"]).real_home)
        self.assertTrue(parser.parse_args(["--claude", "x", "--real-home"]).real_home)


class UsageTests(unittest.TestCase):
    ODD = "an-odd-value-that-must-not-be-echoed"

    def refused(self, world, args, expect=pc_exitcodes.USAGE):
        code, out, err = world.run(args)
        self.assertEqual(code, expect, out + err)
        self.assertEqual(world.folders(), [], "nothing was created")
        self.assertNotIn(self.ODD, out + err)
        return out + err

    def test_an_unknown_flag_exits_2_with_the_fixed_line(self) -> None:
        world = World()
        text = self.refused(world, ["--claude", world.claude, "--budget", "1.00", "--frobnicate", self.ODD])
        self.assertIn(pc_cleanclone.MESSAGE_USAGE, text)

    def test_a_missing_claude_exits_2(self) -> None:
        world = World()
        self.refused(world, ["--budget", "1.00"])
        self.refused(world, ["--preflight-only"])

    def test_a_relative_or_unusable_claude_exits_2_and_is_never_echoed(self) -> None:
        world = World()
        text = self.refused(world, ["--claude", self.ODD, "--budget", "1.00"])
        self.assertIn(pc_cleanclone.MESSAGE_CLAUDE, text)
        self.refused(world, ["--claude", os.path.join(world.base, "absent"), "--budget", "1.00"])
        plain = os.path.join(world.base, "plain-file")
        with open(plain, "w", encoding="utf-8") as handle:
            handle.write("x\n")
        text = self.refused(world, ["--claude", plain, "--budget", "1.00"])
        self.assertNotIn(plain, text)

    def test_a_full_run_without_a_budget_exits_2(self) -> None:
        world = World()
        self.refused(world, ["--claude", world.claude])
        self.refused(world, ["--claude", world.claude, "--budget", ""])

    def test_preflight_only_takes_neither_a_budget_nor_the_self_test(self) -> None:
        world = World()
        self.refused(world, ["--claude", world.claude, "--preflight-only", "--budget", "1.00"])
        self.refused(world, ["--claude", world.claude, "--preflight-only", "--selftest"])

    def test_a_source_that_is_neither_an_https_address_nor_a_folder_exits_2_and_is_never_echoed(self) -> None:
        world = World()
        for source in (self.ODD, "http://example.invalid/a/b", "ssh://example.invalid/a/b", os.path.join(world.base, "absent")):
            text = self.refused(world, ["--claude", world.claude, "--preflight-only", "--source", source])
            self.assertIn(pc_cleanclone.MESSAGE_SOURCE, text)
            self.assertNotIn(source, text)

    def test_help_prints_the_usage_line_and_exits_0(self) -> None:
        world = World()
        code, out, err = world.run(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("--preflight-only", out)

    def test_an_unusable_runs_root_or_harness_home_exits_12_with_a_fixed_line(self) -> None:
        world = World()
        env = dict(world.env, PRECLEAR_RUNS_ROOT=os.path.join(world.main, "scratch"))
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"], env=env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn(pc_cleanclone.MESSAGE_RUNS_ROOT, err)
        self.assertNotIn(world.main, out + err)
        env = dict(world.env, PRECLEAR_HARNESS_HOME=os.path.join(world.main, "harness"))
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"], env=env)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_BLOCKED, out + err)
        self.assertIn(pc_cleanclone.MESSAGE_HARNESS_HOME, err)

    def test_two_runs_started_in_the_same_second_never_reuse_a_folder(self) -> None:
        world = World()
        fixed = lambda: START
        first = world.run(["--claude", world.claude, "--preflight-only"], clock=fixed)
        second = world.run(["--claude", world.claude, "--preflight-only"], clock=fixed)
        self.assertEqual(first[0], 0, first[1] + first[2])
        self.assertEqual(second[0], pc_exitcodes.RUNROOT_COLLISION)
        self.assertEqual(len(world.folders()), 1)
        third = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(third[0], 0, third[1] + third[2])
        self.assertEqual(len(world.folders()), 2)


class NoLeakTests(unittest.TestCase):
    def test_a_complete_run_prints_and_files_no_path_source_home_temp_folder_or_login(self) -> None:
        run = complete_run()
        self.assertEqual(path_text_hits(run.out + run.err, run.world), [])
        facts = read_text(os.path.join(run.clone_folder, pc_cleanclone.CLONE_FACTS_NAME))
        self.assertEqual(path_text_hits(facts, run.world), [])
        for name in ("README.md", "environment-names.txt", "digest-table.md", "usage-by-row.txt", "review-brief.md"):
            self.assertEqual(path_text_hits(read_text(os.path.join(run.dated(), name)), run.world), [], name)

    def test_a_budget_stop_and_a_stopped_row_print_no_path_either(self) -> None:
        for run in (budget_run(), stopped_run(), incomplete_run(), tampered_run()):
            self.assertEqual(path_text_hits(run.out + run.err, run.world), [])

    def test_preflight_only_prints_no_path_in_any_of_its_states(self) -> None:
        for options in ({}, {"logged_in": False}, {"banner": "9.9.9 (Claude Code)"}):
            world = World(**options)
            code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
            self.assertEqual(path_text_hits(out + err, world), [], options)

    def test_the_origin_address_is_read_at_run_time_and_written_nowhere(self) -> None:
        world = World()
        code, out, err = world.run(["--claude", world.claude, "--preflight-only"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(path_text_hits(out + err, world), [])
        with open(pc_cleanclone.__file__, "r", encoding="utf-8") as handle:
            module = handle.read()
        self.assertNotIn("github", module.lower())
        self.assertIsNone(PATH_SHAPE.search(module.replace("(?:Users|home|private|var|tmp|opt|Volumes|root|etc)", "")))

    def test_the_scrubber_replaces_known_paths_first_and_any_other_home_or_temp_shaped_path_after(self) -> None:
        world = World()
        scrub = pc_cleanclone.Scrubber([(world.base, "<base>"), (world.home, "<home>")])
        text = "saw %s and %s and %s and %s here" % (
            world.home, os.path.join(world.base, "deep"), pc_seeds.home_path("someone") + "/else/file",
            pc_seeds.mac_temp_root() + "/x")
        cleaned = scrub(text)
        self.assertEqual(path_text_hits(cleaned, world), [])
        self.assertIn("<home>", cleaned)
        self.assertIn("<base>/deep", cleaned)
        self.assertEqual(cleaned.count("<path>"), 2)

    def test_child_output_that_holds_a_path_is_scrubbed_before_it_is_printed(self) -> None:
        world = World()
        out = io.StringIO()
        scrub = pc_cleanclone.Scrubber([(world.base, "<base>")])
        code = pc_cleanclone.run_streaming(
            ["/bin/sh", "-c", "echo %s/inside; echo %s >&2" % (world.base, pc_seeds.home_path("x") + "/y")], {"PATH": "/usr/bin:/bin"},
            world.base, out, scrub)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), ["<base>/inside", "<path>"])


if __name__ == "__main__":
    unittest.main()
