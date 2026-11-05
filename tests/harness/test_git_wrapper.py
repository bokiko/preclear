"""Zero-token tests for the row 11 injector: tests/harness/git-wrapper and row 11 on the scripted claude (plan 04-12; HARN-11).

The wrapper passes every git call to the real git named in its real-git file with the streams and the exit code
unchanged, logs one line per call, counts the calls whose whole argument list equals a listed line of match-argv, and
appends one line to one committed file of another task after the n-th such call has returned. These tests drive the
shim directly under /bin/bash with scratch folders they make themselves (a stub real git where the git itself is not
the point), then run row 11 through the engine on the scripted claude. No test starts a real claude and none names a
model. Every scratch folder lives under the system temporary folder and is never deleted; paths are never printed.
Leak-shaped strings are never typed in this file. Modules are imported inside small accessors so a missing module is
one error per test, not one load failure of the file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import tempfile
import unittest
import uuid

import pc_testutil
from test_row_generic import Registered, tree_names
from test_rows_git import SeededGit, dry_run_row, git_stages, real_git_path
from test_rows_plain import PLAN_DIGEST, SHAPED, VERDICT_LINE, committed, matrix, read_bytes, read_json, read_text, rowseeds, rows, sha_lines, spec_of

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
SHIM = os.path.join(HARNESS_DIR, "git-wrapper")
BASH = "/bin/bash"
ROW11 = "row11-concurrent-change"
ROW11_COMMITTED = "row11-concurrent-change-rerun"
NOTES = "other_task_notes.md"
QUOTED = ("--no-optional-locks", "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
NUL = ("--no-optional-locks", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none")
LOG_LINE = re.compile(r"\AT=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z PID=\d+ EXIT=\d{1,3} ORD=(?:\d+|-) ARGV=.*\Z")
INJECTED_LINE = re.compile(r"\A- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z concurrent edit by another session: renamed the staging host\.\Z")
BASE_NOTES = "Notes of another task.\n"
STATUS_DIGEST_PREFIX = "ed03447e9df43888"


def hygiene_env(home: str) -> dict:
    return pc_testutil.git_env({"PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS), "HOME": home, "LANG": "en_US.UTF-8"})


def lines_of(path: str) -> list:
    if not os.path.exists(path):
        return []
    return read_text(path).splitlines()


def write_file(path: str, text: str, mode: int = 0o644) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.chmod(path, mode)


def stub_git(path: str, code: int = 0) -> str:
    """A real-git stand-in: prints each argument on its own line behind a marker, copies stdin, writes a line to standard
    error and exits with CODE. It lets a test see exactly what the wrapper handed on."""
    write_file(
        path,
        "#!/bin/sh\nfor a in \"$@\"; do printf 'ARG[%s]\\n' \"$a\"; done\ncat\nprintf 'stub-error\\n' >&2\nexit " + str(code) + "\n",
        0o755,
    )
    return path


class WrapperRig(object):
    """A run root in miniature: <run>/ckpt/gitwrap with the shim and its files, and <run>/project holding one commit.

    real_git is the path written to real-git (the real git by default). inject is the inject-file value. match is the
    list of listed argument lines (the two forms of the prescribed status command by default).
    """

    def __init__(self, fire_on: str = "1", inject: str = NOTES, match=None, real_git=None, repo: bool = True) -> None:
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-gw-"))
        self.run = os.path.join(self.base, "run")
        self.w = os.path.join(self.run, "ckpt", "gitwrap")
        self.project = os.path.join(self.run, "project")
        self.home = os.path.join(self.base, "home")
        for folder in (self.home, self.w, self.project):
            os.makedirs(folder)
        self.shim = os.path.join(self.w, "git")
        with open(SHIM, "rb") as source, open(self.shim, "wb") as target:
            target.write(source.read())
        os.chmod(self.shim, 0o755)
        self.real = real_git if real_git is not None else real_git_path()
        write_file(os.path.join(self.w, "real-git"), self.real + "\n")
        lines = list(match) if match is not None else [" ".join(shlex.quote(a) for a in form) for form in (NUL, QUOTED)]
        write_file(os.path.join(self.w, "match-argv"), "\n".join(lines) + "\n")
        write_file(os.path.join(self.w, "fire-on"), fire_on + "\n")
        write_file(os.path.join(self.w, "inject-file"), inject + "\n")
        write_file(os.path.join(self.project, NOTES), BASE_NOTES)
        if repo:
            for args in (["init", "-q"], ["add", "-A"], ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "base"]):
                done = self.direct(*args)
                assert done.returncode == 0, args

    def env(self) -> dict:
        return hygiene_env(self.home)

    def direct(self, *args: str, stdin=None) -> subprocess.CompletedProcess:
        return subprocess.run([self.real] + list(args), cwd=self.project, env=self.env(), input=stdin,
                              stdin=None if stdin is not None else subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def call(self, *args: str, stdin=None, env=None) -> subprocess.CompletedProcess:
        return subprocess.run([self.shim] + list(args), cwd=self.project, env=env if env is not None else self.env(),
                              input=stdin, stdin=None if stdin is not None else subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def file(self, name: str) -> str:
        return os.path.join(self.w, name)

    def notes(self) -> str:
        return read_text(os.path.join(self.project, NOTES))

    def injected_lines(self) -> list:
        return [line for line in self.notes().splitlines() if line.startswith("- ")]

    def match_count(self) -> int:
        return len(lines_of(self.file("matches.log")))

    def log(self) -> list:
        return lines_of(self.file("git-calls.log"))

    def ords(self) -> list:
        return [re.search(r" ORD=(\d+|-) ", line).group(1) for line in self.log()]


class GitWrapperTests(unittest.TestCase):
    def test_the_shim_is_executable_and_names_bash(self) -> None:
        self.assertTrue(os.access(SHIM, os.X_OK))
        self.assertEqual(read_text(SHIM).splitlines()[0], "#!/bin/bash")

    def test_stdout_and_exit_code_are_the_real_gits_for_a_status_call(self) -> None:
        rig = WrapperRig()
        write_file(os.path.join(rig.project, "new file.txt"), "x\n")
        direct = rig.direct("status", "--porcelain=v1", "--untracked-files=all")
        through = rig.call("status", "--porcelain=v1", "--untracked-files=all")
        self.assertEqual((through.returncode, through.stdout, through.stderr), (direct.returncode, direct.stdout, direct.stderr))
        self.assertIn(b"new file.txt", through.stdout)

    def test_a_failing_call_gives_the_same_exit_code_and_standard_error_as_direct(self) -> None:
        rig = WrapperRig()
        direct = rig.direct("no-such-verb")
        through = rig.call("no-such-verb")
        self.assertNotEqual(direct.returncode, 0)
        self.assertEqual((through.returncode, through.stdout, through.stderr), (direct.returncode, direct.stdout, direct.stderr))

    def test_standard_input_reaches_the_real_git_unchanged(self) -> None:
        rig = WrapperRig()
        data = b"first line\nsecond line\n\x00binary tail\n"
        direct = rig.direct("hash-object", "--stdin", stdin=data)
        through = rig.call("hash-object", "--stdin", stdin=data)
        self.assertEqual(through.returncode, 0)
        self.assertEqual(through.stdout, direct.stdout)
        self.assertEqual(len(through.stdout.strip()), 40)

    def test_the_arguments_and_the_exit_code_reach_the_named_real_git_exactly(self) -> None:
        rig = WrapperRig(real_git=None, repo=False)
        stub = stub_git(os.path.join(rig.base, "stub"), 7)
        write_file(rig.file("real-git"), stub + "\n")
        args = ["a b", "--flag=x y", "", "quote'd", "dollar$HOME", "new\nline", "tab\tend"]
        done = rig.call(*args, stdin=b"piped\n")
        self.assertEqual(done.returncode, 7)
        self.assertEqual(done.stderr, b"stub-error\n")
        expected = "".join("ARG[%s]\n" % item for item in args) + "piped\n"
        self.assertEqual(done.stdout.decode("utf-8"), expected)

    def test_a_git_earlier_on_the_path_is_never_started_only_the_named_one(self) -> None:
        rig = WrapperRig(repo=False)
        bin_dir = os.path.join(rig.base, "tripbin")
        os.makedirs(bin_dir)
        trip = os.path.join(bin_dir, "git")
        write_file(trip, "#!/bin/sh\necho started >> \"" + os.path.join(rig.base, "trip.log") + "\"\nexit 97\n", 0o755)
        env = rig.env()
        env["PATH"] = os.pathsep.join([bin_dir, env["PATH"]])
        done = rig.call("--version", env=env)
        self.assertEqual(done.returncode, 0)
        self.assertTrue(done.stdout.startswith(b"git version"))
        self.assertFalse(os.path.exists(os.path.join(rig.base, "trip.log")))

    def test_one_complete_log_line_per_call_in_the_stated_format(self) -> None:
        rig = WrapperRig()
        rig.call("status", "--short")
        rig.call("rev-parse", "HEAD")
        rig.call("no-such-verb")
        log = rig.log()
        self.assertEqual(len(log), 3)
        for line in log:
            self.assertRegex(line, LOG_LINE)
        self.assertEqual([re.search(r" EXIT=(\d+) ", line).group(1) for line in log], ["0", "0", "1"] if rig.call("status").returncode == 0 else None)
        self.assertEqual(len({re.search(r" PID=(\d+) ", line).group(1) for line in log}), 3)

    def test_the_log_line_renders_the_arguments_so_the_harness_parser_reads_them_back(self) -> None:
        import pc_review

        rig = WrapperRig(repo=False)
        stub = stub_git(os.path.join(rig.base, "stub"), 0)
        write_file(rig.file("real-git"), stub + "\n")
        args = ["-c", "core.x=1", "status", "a b", "", "quote'd", "new\nline", "tab\tend", "café", "$HOME", "back\\slash"]
        rig.call(*args)
        text = read_text(rig.file("git-calls.log"))
        self.assertEqual(text.count("\n"), 1, "a newline inside an argument never breaks the line")
        calls = pc_review.parse_git_calls_log(text)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].readable)
        self.assertEqual(tuple(calls[0].argv), tuple(args))
        self.assertEqual(calls[0].ordinal, "-")

    def test_an_unconfigured_wrapper_runs_nothing_and_exits_70(self) -> None:
        rig = WrapperRig(repo=False)
        write_file(rig.file("real-git"), "")
        done = rig.call("--version")
        self.assertEqual(done.returncode, 70)
        self.assertEqual(done.stdout, b"")
        self.assertEqual(rig.log(), [])
        write_file(rig.file("real-git"), os.path.join(rig.base, "missing-git") + "\n")
        self.assertEqual(rig.call("--version").returncode, 70)

    def test_a_non_matching_call_writes_nothing_but_its_log_line(self) -> None:
        rig = WrapperRig(repo=False)
        stub = stub_git(os.path.join(rig.base, "stub"), 0)
        write_file(rig.file("real-git"), stub + "\n")
        before = sorted(os.listdir(rig.w))
        notes = rig.notes()
        rig.call("status", "--short")
        self.assertEqual(sorted(os.listdir(rig.w)), sorted(before + ["git-calls.log"]))
        self.assertEqual(rig.notes(), notes)
        self.assertEqual(sorted(os.listdir(rig.project)), [NOTES])


class Row11RegistryTests(unittest.TestCase):
    def test_the_entry_is_the_three_stage_resume_line_row_with_the_git_profile_and_the_path_prepend(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW11)
        self.assertTrue(spec.implemented)
        self.assertEqual(
            [(s.name, s.kind, s.max_turns, str(s.cap), s.timeout, s.session) for s in spec.stages],
            [("s1", "work", 15, "0.30", 900, "new:A"), ("s2", "preclear", 60, "1.30", 1800, "resume:A"),
             ("s3", "resume", 15, "0.40", 900, "new:B")],
        )
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_GIT)
        self.assertEqual((spec.extra_tools, spec.hooks, spec.probe), ((), (), pc_rows.PROBE_NONE))
        self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
        self.assertEqual(spec.chain, pc_rows.CHAIN_RESUME_LINE)
        self.assertEqual(spec.analyses, ("git-calls",))
        self.assertEqual(spec.analyses, (pc_rows.ANALYSIS_GIT_CALLS,))
        self.assertEqual(spec.path_prepend, (("s2", "ckpt/gitwrap"),))
        self.assertEqual(spec.seed, "pc_rowseeds:seed_row11")
        self.assertEqual(str(pc_rows.worst_case(spec)), "2.00")
        self.assertEqual(pc_rows.session_count(spec), 2)
        self.assertEqual(dict(spec.prompts)["s2"], rowseeds().ROW11_FOLDER + "/s2-preclear-prompt.md")
        self.assertIn((rowseeds().ROW11_FOLDER + "/fixture-CLAUDE.md", "file"), spec.sources)
        self.assertIn(("tests/harness/git-wrapper", "file"), spec.sources)
        for relative, kind in spec.sources:
            full = os.path.join(ROOT, *relative.split("/"))
            self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), relative)
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        self.assertTrue(spec.setup_text.isascii())
        self.assertIsNone(SHAPED.search(spec.setup_text))

    def test_every_other_row_has_an_empty_path_prepend(self) -> None:
        pc_rows = rows()
        for entry in pc_rows.build_registry():
            if entry.row_id != ROW11:
                self.assertEqual(entry.path_prepend, (), entry.row_id)

    def test_the_dry_run_prints_the_plan_and_starts_no_process_and_list_marks_the_row_implemented(self) -> None:
        code, text, tripwire, base = dry_run_row(ROW11)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 3 stages, 2 sessions" % ROW11, text)
        lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
        self.assertEqual(len(lines), 3)
        for line, turns, cap in zip(lines, ("15 turns", "60 turns", "15 turns"), ("cap 0.30", "cap 1.30", "cap 0.40")):
            self.assertIn(turns, line)
            self.assertIn(cap, line)
        self.assertIn("worst case 2.00 USD", text)
        self.assertIn("allowlist 33 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")))
        cells = dict((line.split()[1], line.split()) for line in matrix().list_lines(rows().build_registry())[1:])
        self.assertEqual(cells[ROW11][2:], ["3", "2", "yes"])

    def test_no_allowlist_rule_names_the_wrapper_and_the_baseline_gained_nothing(self) -> None:
        import pc_flags

        rules = list(pc_flags.BASELINE_ALLOWED_TOOLS)
        self.assertEqual(len(rules), 33)
        for rule in rules:
            self.assertNotIn("gitwrap", rule)
            self.assertNotIn("git-wrapper", rule)


class PathPrependTests(unittest.TestCase):
    def setUp(self) -> None:
        import pc_row1
        import pc_rows

        self.row1, self.pc_rows = pc_row1, pc_rows
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-pp-"))
        self.run = os.path.join(self.base, "run")
        os.makedirs(os.path.join(self.run, "ckpt", "gitwrap"))
        os.makedirs(os.path.join(self.run, "ckpt", "second"))
        self.paths = {"run_root": self.run}
        self.env = {"PATH": "/usr/bin:/bin", "HOME": "x"}

    def row(self, entries) -> object:
        return spec_of(ROW11)._replace(path_prepend=tuple(entries))

    def test_the_named_stage_gets_the_folder_first_and_the_others_the_path_as_it_was(self) -> None:
        row = self.row([("s2", "ckpt/gitwrap")])
        changed = self.row1._apply_path_prepend(self.env, row, "s2", self.paths)
        self.assertEqual(changed["PATH"], os.path.join(self.run, "ckpt", "gitwrap") + os.pathsep + "/usr/bin:/bin")
        self.assertEqual(changed["HOME"], "x")
        for other in ("s1", "s3"):
            self.assertEqual(self.row1._apply_path_prepend(self.env, row, other, self.paths), self.env)
        self.assertEqual(self.env["PATH"], "/usr/bin:/bin", "the input is not changed")

    def test_two_entries_keep_their_order_and_an_empty_path_gets_no_trailing_separator(self) -> None:
        row = self.row([("s2", "ckpt/gitwrap"), ("s2", "ckpt/second")])
        changed = self.row1._apply_path_prepend({"PATH": ""}, row, "s2", self.paths)
        self.assertEqual(changed["PATH"], os.pathsep.join([os.path.join(self.run, "ckpt", "gitwrap"), os.path.join(self.run, "ckpt", "second")]))

    def test_an_entry_outside_the_run_root_or_not_a_folder_is_refused_with_fixed_text(self) -> None:
        import pc_spike

        outside = os.path.join(self.base, "elsewhere")
        os.makedirs(outside)
        os.symlink(outside, os.path.join(self.run, "ckpt", "escape"))
        write_file(os.path.join(self.run, "ckpt", "plain-file"), "x")
        for relative in ("/abs/folder", "../elsewhere", "ckpt/../../elsewhere", "ckpt/escape", "ckpt/plain-file", "ckpt/missing", "", "ckpt//gitwrap", "."):
            with self.subTest(relative=relative):
                with self.assertRaises(pc_spike.SpikeError) as caught:
                    self.row1._apply_path_prepend(self.env, self.row([("s2", relative)]), "s2", self.paths)
                self.assertEqual(str(caught.exception), self.row1.MESSAGE_PATH_PREPEND)
                self.assertNotIn(self.base, str(caught.exception))


class Row11SeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = SeededGit(ROW11, "git-seed-row11")

    @property
    def w(self) -> str:
        return os.path.join(str(self.seeded.paths["ckpt"]), "gitwrap")

    def test_the_instruction_file_is_the_committed_fixture_and_the_plan_the_plain_plan(self) -> None:
        data = read_bytes(os.path.join(self.seeded.project, "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW11_COMMITTED, "fixture-CLAUDE.md")))
        self.assertEqual(hashlib.sha256(data).hexdigest(), sha_lines(ROW11_COMMITTED)["project/CLAUDE.md"])
        self.assertTrue(hashlib.sha256(data).hexdigest().startswith(STATUS_DIGEST_PREFIX))
        plan = read_bytes(os.path.join(self.seeded.project, "thoughts", "plans", "2026-10-15-widget-export.md"))
        self.assertEqual(hashlib.sha256(plan).hexdigest(), PLAN_DIGEST)
        self.assertEqual(plan, read_bytes(os.path.join(HARNESS_DIR, "data", "plain-plan.md")))

    def test_the_base_commit_holds_the_other_tasks_notes_and_the_work_tree_is_clean_of_them(self) -> None:
        self.assertEqual(self.seeded.git("rev-list", "--count", "HEAD").strip(), "1")
        self.assertEqual(self.seeded.git("ls-files").split(), ["CLAUDE.md", NOTES, "thoughts/plans/2026-10-15-widget-export.md"])
        self.assertEqual(self.seeded.git("status", "--porcelain=v1", "--", NOTES), "")
        self.assertEqual(self.seeded.git("symbolic-ref", "-q", "HEAD").strip(), "refs/heads/main")
        self.assertEqual(read_text(os.path.join(self.seeded.project, NOTES)), rowseeds().OTHER_NOTES_TEXT)

    def test_the_wrapper_folder_holds_the_five_files_with_the_stated_modes_and_contents(self) -> None:
        self.assertEqual(sorted(os.listdir(self.w)), ["fire-on", "git", "inject-file", "match-argv", "real-git"])
        self.assertEqual(read_bytes(os.path.join(self.w, "git")), read_bytes(SHIM))
        self.assertTrue(stat.S_IMODE(os.stat(os.path.join(self.w, "git")).st_mode) & 0o111 == 0o111)
        self.assertEqual(read_text(os.path.join(self.w, "fire-on")), "1\n")
        self.assertEqual(read_text(os.path.join(self.w, "inject-file")), NOTES + "\n")
        lines = read_text(os.path.join(self.w, "match-argv")).splitlines()
        self.assertEqual(sorted(shlex.split(line) for line in lines), sorted([list(QUOTED), list(NUL)]))
        real = read_text(os.path.join(self.w, "real-git")).rstrip("\n")
        self.assertTrue(os.path.isabs(real))
        self.assertTrue(os.access(real, os.X_OK))
        self.assertNotEqual(os.path.realpath(real), os.path.realpath(os.path.join(self.w, "git")))

    def test_the_digest_record_holds_the_sha256_of_each_of_the_five_files_and_is_in_raw(self) -> None:
        record = read_json(os.path.join(str(self.seeded.paths["raw"]), "gitwrap-digests.json"))
        self.assertEqual(sorted(record), ["fire-on", "git", "inject-file", "match-argv", "real-git"])
        for name, digest in record.items():
            self.assertEqual(digest, hashlib.sha256(read_bytes(os.path.join(self.w, name))).hexdigest(), name)
        import pc_review

        self.assertEqual(pc_review.wrapper_digest_state(str(self.seeded.paths["raw"]), self.w), "yes")

    def test_the_wrapper_works_from_the_seeded_folder_and_injects_into_the_committed_notes_file(self) -> None:
        import subprocess as sp

        env = hygiene_env(self.seeded.rig.base)
        done = sp.run([os.path.join(self.w, "git")] + list(QUOTED), cwd=self.seeded.project, env=env, stdin=sp.DEVNULL,
                      stdout=sp.PIPE, stderr=sp.PIPE)
        self.assertEqual(done.returncode, 0, done.stderr)
        notes = read_text(os.path.join(self.seeded.project, NOTES))
        self.assertTrue(notes.startswith(rowseeds().OTHER_NOTES_TEXT))
        self.assertEqual(len([l for l in notes.splitlines() if l.startswith("- ") and "concurrent edit" in l]), 1)
        self.assertEqual(read_text(os.path.join(self.w, "injection.log")), "INJECTED ORD=1\n")

    def test_the_seed_refuses_a_second_call_on_the_same_run_root(self) -> None:
        with self.assertRaises(FileExistsError):
            rowseeds().install_git_wrapper(self.seeded.rig.repo, self.seeded.run_root, "/bin/echo", str(self.seeded.paths["raw"]))


def s2_ops(extra: list) -> list:
    """Scripted git calls through the PATH. An argument list that starts with -c is an internal call of Claude Code: it
    is made silently, with no tool_use in the stream, as the real binary makes it."""
    return [dict({"op": "run_git", "args": list(args)}, **({"silent": True} if args[:1] == ["-c"] else {})) for args in extra]


def row11_stages(s2_calls: list) -> list:
    stages = git_stages(spec_of(ROW11), "main @ abc1234")
    return pc_testutil.stages_with(stages, 1, ops=list(stages[1]["ops"]) + s2_ops(s2_calls))


INTERNAL = ["-c", "core.fsmonitor=", "-c", "core.askPass=", "status", "--short"]
VERIFY = ["--no-optional-locks", "status", "--short"]


class Row11ChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fired = Registered(ROW11, stages=row11_stages([INTERNAL, list(QUOTED), VERIFY]))
        assert cls.fired.outcome.code == 0, "\n".join(cls.fired.outcome.lines)
        cls.quiet = Registered(ROW11, stages=row11_stages([INTERNAL, VERIFY, ["rev-parse", "HEAD"]]))
        assert cls.quiet.outcome.code == 0, "\n".join(cls.quiet.outcome.lines)

    def wrapper_dir(self, run: Registered) -> str:
        return os.path.join(run.run_root, "ckpt", "gitwrap")

    def read(self, run: Registered, name: str) -> str:
        return read_text(os.path.join(run.row_dir, name))

    def test_only_the_second_stage_has_the_wrapper_folder_first_on_its_path(self) -> None:
        calls = self.fired.rig.calls()
        self.assertEqual(len(calls), 3)
        folder = os.path.join(os.path.realpath(self.fired.run_root), "ckpt", "gitwrap")
        base_path = self.fired.rig.env["PATH"]
        self.assertEqual(calls[0]["path"], base_path)
        self.assertEqual(calls[2]["path"], base_path)
        self.assertEqual(calls[1]["path"], folder + os.pathsep + base_path)
        for index in (0, 2):
            self.assertNotIn("gitwrap", calls[index]["path"])

    def test_the_injector_fires_once_on_the_first_prescribed_status_call_and_appends_to_the_other_tasks_file(self) -> None:
        project = os.path.join(self.fired.run_root, "project")
        notes = read_text(os.path.join(project, NOTES))
        self.assertTrue(notes.startswith(rowseeds().OTHER_NOTES_TEXT))
        added = [line for line in notes.splitlines() if line.startswith("- ")]
        self.assertEqual(len(added) - len([l for l in rowseeds().OTHER_NOTES_TEXT.splitlines() if l.startswith("- ")]), 1)
        self.assertRegex(added[-1], INJECTED_LINE)
        self.assertEqual(lines_of(os.path.join(self.wrapper_dir(self.fired), "injection.log")), ["INJECTED ORD=1"])

    def test_the_wrapper_log_holds_the_three_model_side_calls_and_none_of_the_harnesss_own(self) -> None:
        log = lines_of(os.path.join(self.wrapper_dir(self.fired), "git-calls.log"))
        self.assertEqual(len(log), 3, "the engine's state capture and status snapshots use the absolute git path")
        self.assertEqual([re.search(r" ORD=(\d+|-) ", line).group(1) for line in log], ["-", "1", "-"])
        self.assertIn("ARGV=-c core.fsmonitor= -c core.askPass= status --short", log[0])
        self.assertTrue(log[1].endswith("ARGV=--no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none"))
        self.assertTrue(log[2].endswith("ARGV=--no-optional-locks status --short"))

    def test_the_model_sees_the_status_taken_before_the_change(self) -> None:
        full = self.read(self.fired, "s2-preclear-full-trace.md")
        self.assertIn("status --porcelain=v1", full)
        self.assertEqual(self.fired.outcome.code, 0)

    def test_the_row_is_filed_with_the_analysis_files_of_plan_04_10(self) -> None:
        names = tree_names(self.fired.row_dir)
        for expected in ("git-calls-correlated.txt", "git-calls.log", "injection.log", "wrapper-git.sh", "README.md", "mechanical-checks.md"):
            self.assertIn(expected, names)
        self.assertEqual(os.listdir(self.fired.ctx.destination), [ROW11])
        self.assertEqual(self.read(self.fired, "wrapper-git.sh"), read_text(SHIM))
        section = self.read(self.fired, "mechanical-checks.md").split("## Git wrapper calls\n", 1)[1].split("\n## ", 1)[0].splitlines()
        for expected in (
            "calls-logged: 3",
            "calls-internal: 1",
            "calls-matched-to-one-tool-use: 2",
            "calls-ambiguous: 0",
            "calls-unmatched: 0",
            "lines-unreadable-UNCONFIRMED: 0",
            "wrapper-log: present",
            "injection-log: present",
            "wrapper-files-equal-setup-digests: yes",
        ):
            self.assertIn(expected, section)
        self.assertEqual(self.read(self.fired, "injection.log"), "INJECTED ORD=1\n")

    def test_the_filed_text_holds_no_path_and_the_readme_ends_with_the_pending_line(self) -> None:
        for name in ("README.md", "mechanical-checks.md", "git-calls.log", "git-calls-correlated.txt", "injection.log"):
            text = self.read(self.fired, name).replace(VERDICT_LINE, "")
            self.assertIsNone(SHAPED.search(text), name)
        self.assertTrue(self.read(self.fired, "README.md").endswith(VERDICT_LINE + "\n"))
        self.assertIn(spec_of(ROW11).setup_text, self.read(self.fired, "README.md"))

    def test_the_real_git_path_is_filed_nowhere(self) -> None:
        real = read_text(os.path.join(self.wrapper_dir(self.fired), "real-git")).strip()
        for relative in tree_names(self.fired.row_dir):
            if relative.endswith("/"):
                continue
            self.assertNotIn(real.encode("utf-8"), read_bytes(os.path.join(self.fired.row_dir, *relative.split("/"))), relative)

    def test_a_no_op_session_files_an_absent_injection_log_and_leaves_the_notes_file_alone(self) -> None:
        wrapper = self.wrapper_dir(self.quiet)
        for name in ("matches.log", "fired.lock", "injection.log"):
            self.assertFalse(os.path.exists(os.path.join(wrapper, name)), name)
        self.assertEqual(read_text(os.path.join(self.quiet.run_root, "project", NOTES)), rowseeds().OTHER_NOTES_TEXT)
        names = tree_names(self.quiet.row_dir)
        self.assertNotIn("injection.log", names)
        self.assertIn("git-calls.log", names)
        section = self.read(self.quiet, "mechanical-checks.md").split("## Git wrapper calls\n", 1)[1].split("\n## ", 1)[0].splitlines()
        self.assertIn("injection-log: absent", section)
        self.assertIn("calls-logged: 3", section)
        self.assertIn("wrapper-files-equal-setup-digests: yes", section)

    def test_a_model_write_into_the_wrapper_folder_is_reported_by_the_digest_state(self) -> None:
        import pc_review

        raw = os.path.join(self.fired.run_root, "raw")
        self.assertEqual(pc_review.wrapper_digest_state(raw, self.wrapper_dir(self.fired)), "yes")
        rig = WrapperRig()
        digests = dict((name, hashlib.sha256(read_bytes(rig.file(name))).hexdigest()) for name in ("git", "real-git", "match-argv", "fire-on", "inject-file"))
        record_dir = os.path.join(rig.base, "raw")
        os.makedirs(record_dir)
        write_file(os.path.join(record_dir, "gitwrap-digests.json"), json.dumps(digests))
        self.assertEqual(pc_review.wrapper_digest_state(record_dir, rig.w), "yes")
        write_file(rig.file("fire-on"), "2\n")
        self.assertEqual(pc_review.wrapper_digest_state(record_dir, rig.w), "no")


if __name__ == "__main__":
    unittest.main()
