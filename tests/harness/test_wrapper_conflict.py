"""Tests for tests/harness/checkpoint-wrapper (STUB-04, STUB-06 second layer).

The wrapper sits between the caller and the stub. It logs every call, delegates unchanged,
refuses the driver-only verbs bind, create and init with exit 71, and, while an armed file
holds a positive count, makes the stub itself return a genuine exit 3 by letting a second
bound session update the same section first (the committed row 2 behaviour).

Every test builds its own scratch run under the system temp directory. Scratch directories
are never deleted by a test and their paths are never printed. Session ids and the ledger
come from the committed row 2 evidence at run time; nothing in this file names one.
"""
from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WRAPPER_SRC = os.path.join(HERE, "checkpoint-wrapper")
STUB = os.path.join(HERE, "checkpoint_stub.py")
ROW2 = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20", "row2-double-conflict")

BRAND = "checkpoint-stub: STUB-BACKED test apparatus, not the real checkpoint helper"
LEDGER_NAME = "CONTINUITY_CLAUDE-widget-export.md"
GOAL = "Goal & current state"
NEXT = "Next action"
INPUTS_REL = ".preclear/backend-inputs"

CALL_LINE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z CALL(?: .*)?$")
EXIT_LINE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z EXIT \d+$")
CONFLICT_NAME = re.compile(
    r"^" + re.escape(LEDGER_NAME) + r"\.conflict-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z-[0-9a-f]{8}\.md$"
)
LABELS = ("your base hash: ", "current hash: ", "ledger: ")


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def tree_digest(folder):
    """SHA-256 over every relative path and file content under folder, in sorted order."""
    digest = hashlib.sha256()
    for current, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(current, name)
            digest.update(os.path.relpath(full, folder).encode("utf-8") + b"\0")
            with open(full, "rb") as handle:
                digest.update(handle.read())
            digest.update(b"\0")
        for name in dirs:
            digest.update(os.path.relpath(os.path.join(current, name), folder).encode("utf-8") + b"/\0")
    return digest.hexdigest()


def section_hash(show_text, name):
    match = re.search(r"(?m)^## %s\nsection-hash: ([0-9a-f]{64})$" % re.escape(name), show_text)
    assert match, "no section hash for " + name
    return match.group(1)


def section_body(show_text, name):
    match = re.search(
        r"(?ms)^## %s\nsection-hash: [0-9a-f]{64}\n(.*?)(?=^## |\Z)" % re.escape(name), show_text
    )
    assert match, "no section body for " + name
    return match.group(1).rstrip("\n")


class Rig:
    """One scratch run: CKPT_HOME, project folder, wrapper folder, two bound sessions."""

    def __init__(self, armed=2, py="auto", stub="auto"):
        assert os.path.isfile(WRAPPER_SRC), "tests/harness/checkpoint-wrapper does not exist"
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-wrapper-"))
        self.ckpt = os.path.join(self.base, "ckpt")
        self.ledgers = os.path.join(self.ckpt, "ledgers")
        self.project = os.path.join(self.base, "project")
        self.wdir = os.path.join(self.base, "wrapper")
        for folder in (self.ckpt, self.ledgers, self.project, self.wdir):
            os.makedirs(folder)
        self.ledger = os.path.join(self.ledgers, LEDGER_NAME)
        shutil.copyfile(os.path.join(ROW2, "snap-0-setup", LEDGER_NAME), self.ledger)
        self.inputs = os.path.join(self.project, *INPUTS_REL.split("/"))
        os.makedirs(self.inputs)
        for name in ("block.md", "goal.md"):
            shutil.copyfile(
                os.path.join(ROW2, "snap-2-after-preclear", "preclear", "backend-inputs", name),
                os.path.join(self.inputs, name),
            )
        self.session = read_text(os.path.join(ROW2, "session.id")).strip()
        self.writer2 = read_text(os.path.join(ROW2, "writer2.session")).strip()
        self.wrapper = os.path.join(self.wdir, "checkpoint")
        shutil.copyfile(WRAPPER_SRC, self.wrapper)
        os.chmod(self.wrapper, 0o755)
        if py == "auto":
            py = os.path.realpath(sys.executable)
        if stub == "auto":
            stub = STUB
        if py is not None:
            write_text(os.path.join(self.wdir, "py"), py)
        if stub is not None:
            write_text(os.path.join(self.wdir, "stub"), stub)
        if armed is not None:
            write_text(os.path.join(self.wdir, "armed"), "%d\n" % armed)
        write_text(os.path.join(self.wdir, "writer2.session"), self.writer2 + "\n")
        for session in (self.session, self.writer2):
            code, out, err = self.direct(["bind", "--ledger", self.ledger], session)
            assert code == 0, err

    def env(self, session=None):
        return {
            "PATH": "/usr/bin:/bin",
            "CKPT_HOME": self.ckpt,
            "CLAUDE_CODE_SESSION_ID": session or self.session,
        }

    def _run(self, argv, session):
        proc = subprocess.run(argv, env=self.env(session), cwd=self.project, capture_output=True)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def wrap(self, args, session=None):
        return self._run([self.wrapper] + list(args), session)

    def via_env(self, args, session=None):
        return self._run(["/usr/bin/env", self.wrapper] + list(args), session)

    def direct(self, args, session=None):
        return self._run([sys.executable, "-I", "-B", STUB] + list(args), session)

    def log(self, name):
        path = os.path.join(self.wdir, name)
        return read_text(path) if os.path.exists(path) else None

    def conflict_files(self):
        return sorted(n for n in os.listdir(self.ledgers) if ".conflict-" in n)


def update_args(section, expect, source):
    return ["update", "--section", section, "--expect-section", expect, "--from", source]


class ReplayRow2Tests(unittest.TestCase):
    """The scripted row 2 sequence through the wrapper: exit 3 twice, then success."""

    @classmethod
    def setUpClass(cls):
        rig = Rig(armed=2)
        cls.rig = rig
        goal_rel = INPUTS_REL + "/goal.md"
        block_rel = INPUTS_REL + "/block.md"
        cls.steps = []

        def step(args):
            result = rig.wrap(args)
            cls.steps.append((list(args), result))
            return result

        step(["status"])
        _, show0, _ = step(["show"])
        cls.h0 = section_hash(show0, GOAL)
        step(["validate", "--from", block_rel])
        step(update_args(GOAL, cls.h0, goal_rel))
        cls.conflicts_after_first = rig.conflict_files()
        _, show1, _ = step(["show"])
        cls.h1 = section_hash(show1, GOAL)
        step(update_args(GOAL, cls.h1, goal_rel))
        cls.conflicts_after_second = rig.conflict_files()
        _, show2, _ = step(["show"])
        cls.h2 = section_hash(show2, GOAL)
        goal_text = read_text(os.path.join(rig.inputs, "goal.md")).rstrip("\n")
        cls.merged = section_body(show2, GOAL) + "\n\n" + goal_text + "\n"
        merged_rel = INPUTS_REL + "/goal-merged.md"
        write_text(os.path.join(rig.project, *merged_rel.split("/")), cls.merged)
        step(update_args(GOAL, cls.h2, merged_rel))
        cls.lint = rig.direct(["lint"])

    def test_sequence_exits_are_0_0_0_3_0_3_0_0_and_lint_is_ok(self):
        # status, show, validate, update, show, update, show, update; lint runs straight
        # against the stub, as the committed row 2 driver did (it is not in the wrapper log).
        exits = [result[0] for _, result in self.steps]
        self.assertEqual([0, 0, 0, 3, 0, 3, 0, 0], exits)
        self.assertEqual(0, self.lint[0], self.lint[2])
        self.assertEqual("ledger lint OK\n", self.lint[1])

    def test_hashes_move_between_the_attempts(self):
        self.assertEqual(3, len(set([self.h0, self.h1, self.h2])))

    def test_each_conflict_exit_is_the_stubs_own_and_nothing_else_reaches_the_caller(self):
        for index in (3, 5):
            args, (code, out, err) = self.steps[index]
            self.assertEqual(3, code)
            self.assertEqual("", out)
            self.assertTrue(err.startswith(BRAND + "\n"), err)
            self.assertEqual(1, err.count(BRAND))
            self.assertIn(
                'checkpoint: conflict: "%s" changed since your read. Nothing written. Details: ' % GOAL, err
            )
            self.assertEqual(2, len(err.splitlines()), err)

    def test_two_conflict_files_have_the_committed_name_pattern_and_layout(self):
        self.assertEqual(1, len(self.conflicts_after_first))
        self.assertEqual(2, len(self.conflicts_after_second))
        snap = os.path.join(ROW2, "snap-2-after-preclear")
        committed = sorted(n for n in os.listdir(snap) if ".conflict-" in n)
        self.assertEqual(2, len(committed))
        skeleton = self.skeleton(read_text(os.path.join(snap, committed[0])))
        for name in self.conflicts_after_second:
            self.assertRegex(name, CONFLICT_NAME)
            text = read_text(os.path.join(self.rig.ledgers, name))
            self.assertEqual(skeleton, self.skeleton(text))
        first = read_text(os.path.join(self.rig.ledgers, self.conflicts_after_first[0]))
        second_name = [n for n in self.conflicts_after_second if n != self.conflicts_after_first[0]][0]
        second = read_text(os.path.join(self.rig.ledgers, second_name))
        self.assertIn("your base hash: %s\n" % self.h0, first)
        self.assertIn("current hash: %s\n" % self.h1, first)
        self.assertIn("your base hash: %s\n" % self.h1, second)
        self.assertIn("current hash: %s\n" % self.h2, second)
        self.assertIn("ledger: %s\n" % self.rig.ledger, first)
        kept1 = first.split("\n## Current (kept)\n", 1)[1]
        kept2 = second.split("\n## Current (kept)\n", 1)[1]
        self.assertIn("CI runner for this project was renamed to ci-02; nothing else changed.", kept1)
        self.assertNotIn("db-stg-03", kept1)
        self.assertIn("the staging database moved to db-stg-03; nothing else changed.", kept2)

    @staticmethod
    def skeleton(text):
        labels = []
        for line in text.split("\n"):
            if line.startswith("# Conflict on section "):
                labels.append("title")
            elif line.startswith("## Yours (not applied)") or line.startswith("## Current (kept)"):
                labels.append(line)
            else:
                for label in LABELS:
                    if line.startswith(label):
                        labels.append(label)
        return labels

    def test_the_hand_merged_third_update_lands_in_the_ledger(self):
        args, (code, out, err) = self.steps[7]
        self.assertEqual(0, code, err)
        self.assertEqual('updated "%s" in %s\n' % (GOAL, self.rig.ledger), out)
        ledger = read_text(self.rig.ledger)
        self.assertIn("CI runner for this project was renamed to ci-02", ledger)
        self.assertIn("the staging database moved to db-stg-03", ledger)
        self.assertIn(self.merged.rstrip("\n"), ledger)

    def test_calls_log_has_a_call_and_an_exit_line_per_call_in_order(self):
        lines = self.rig.log("calls.log").splitlines()
        self.assertEqual(2 * len(self.steps), len(lines))
        for index, (args, (code, _, _)) in enumerate(self.steps):
            call, exit_line = lines[2 * index], lines[2 * index + 1]
            self.assertRegex(call, CALL_LINE)
            self.assertRegex(exit_line, EXIT_LINE)
            self.assertEqual(args, shlex.split(call.split(" CALL", 1)[1]))
            self.assertTrue(exit_line.endswith(" EXIT %d" % code), exit_line)

    def test_calls_log_lines_have_the_shape_of_the_committed_wrapper_log(self):
        committed = read_text(os.path.join(ROW2, "wrapper-calls.log")).splitlines()
        self.assertTrue(committed)
        for index, line in enumerate(committed):
            self.assertRegex(line, CALL_LINE if index % 2 == 0 else EXIT_LINE)

    def test_injection_log_holds_two_writer_updates_and_the_armed_file_ends_at_zero(self):
        text = self.rig.log("injection.log")
        self.assertIsNotNone(text)
        all_lines = text.splitlines()
        # The stub brands its stderr once per invocation (a show and an update per injection);
        # the log holds stdout and stderr of the writer, so those lines are expected and counted.
        self.assertEqual(4, all_lines.count(BRAND))
        lines = [line for line in all_lines if line != BRAND]
        self.assertEqual(2, lines.count("writer2 update exit 0"))
        self.assertEqual(6, len(lines))
        headers = [line for line in lines if line.startswith("=== ")]
        self.assertEqual(2, len(headers))
        for number, header in enumerate(headers, 1):
            self.assertRegex(
                header,
                r"^=== \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z injection %d to section \[%s\] as writer2 %s$"
                % (number, re.escape(GOAL), re.escape(self.rig.writer2)),
            )
        for line in lines:
            if not line.startswith("=== ") and line != "writer2 update exit 0":
                self.assertEqual('updated "%s" in %s' % (GOAL, self.rig.ledger), line)
        committed = read_text(os.path.join(ROW2, "wrapper-injection.log")).splitlines()
        self.assertEqual(2, committed.count("writer2 update exit 0"))
        self.assertEqual("0", self.rig.log("armed").strip())
        self.assertEqual(GOAL, self.rig.log("target-section"))


class PassThroughTests(unittest.TestCase):
    def test_wrapper_and_direct_stub_give_identical_output_once_the_scratch_root_is_normalised(self):
        through, direct = Rig(armed=None), Rig(armed=None)
        token = "<scratch>"

        stamp = re.compile(r"\.conflict-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z-")

        def norm(rig, triple):
            # Two normalisations only: the scratch root, and the clock time that the stub
            # itself puts in a conflict file name (two runs never share a millisecond).
            code, out, err = triple
            fix = lambda text: stamp.sub(".conflict-<time>-", text.replace(rig.base, token))
            return code, fix(out), fix(err)

        def both(args):
            via_wrapper = norm(through, through.wrap(args))
            via_stub = norm(direct, direct.direct(args))
            self.assertEqual(via_stub, via_wrapper, "call %r differs between wrapper and direct stub" % (args,))
            return via_wrapper

        read_calls = (
            ["status"],
            ["show"],
            ["show", "--section", NEXT],
            ["validate", "--from", INPUTS_REL + "/block.md"],
            ["lint"],
            ["show", "--section", "No such section"],
        )
        for args in read_calls:
            both(args)
        _, show, _ = through.wrap(["show"])
        expect = section_hash(show, GOAL)
        ok = both(update_args(GOAL, expect, INPUTS_REL + "/goal.md"))
        self.assertEqual(0, ok[0])
        stale = both(update_args(GOAL, expect, INPUTS_REL + "/goal.md"))
        self.assertEqual(3, stale[0])

    def test_with_no_armed_file_the_first_update_succeeds_and_no_injection_log_appears(self):
        rig = Rig(armed=None)
        _, show, _ = rig.wrap(["show"])
        code, out, err = rig.wrap(update_args(GOAL, section_hash(show, GOAL), INPUTS_REL + "/goal.md"))
        self.assertEqual(0, code, err)
        self.assertIsNone(rig.log("injection.log"))
        self.assertIsNone(rig.log("target-section"))
        self.assertEqual([], rig.conflict_files())
        self.assertEqual(4, len(rig.log("calls.log").splitlines()))

    def test_armed_injection_only_fires_for_the_first_touched_section(self):
        rig = Rig(armed=2)
        _, show, _ = rig.wrap(["show"])
        write_text(os.path.join(rig.inputs, "next.md"), "Write the tests.\n")
        code, _, _ = rig.wrap(update_args(NEXT, section_hash(show, NEXT), INPUTS_REL + "/next.md"))
        self.assertEqual(3, code)
        self.assertEqual(NEXT, rig.log("target-section"))
        _, show, _ = rig.wrap(["show"])
        code, out, err = rig.wrap(update_args(GOAL, section_hash(show, GOAL), INPUTS_REL + "/goal.md"))
        self.assertEqual(0, code, err)
        self.assertEqual("1", rig.log("armed").strip())
        self.assertEqual(1, rig.log("injection.log").count("writer2 update exit 0"))


class NotConfiguredTests(unittest.TestCase):
    def check(self, **kwargs):
        rig = Rig(armed=2, **kwargs)
        before = tree_digest(rig.ckpt)
        code, out, err = rig.wrap(["status"])
        self.assertEqual(70, code, err)
        self.assertEqual("", out)
        self.assertIn("not configured", err)
        self.assertNotIn(BRAND, err)
        self.assertIsNone(rig.log("calls.log"))
        self.assertIsNone(rig.log("injection.log"))
        self.assertEqual(before, tree_digest(rig.ckpt))

    def test_missing_py_file_exits_70(self):
        self.check(py=None)

    def test_missing_stub_file_exits_70(self):
        self.check(stub=None)

    def test_empty_py_file_exits_70(self):
        self.check(py="")

    def test_newline_only_stub_file_exits_70(self):
        self.check(stub="\n")

    def test_whitespace_only_stub_file_exits_70(self):
        self.check(stub="  ")


class StubSourceTests(unittest.TestCase):
    def test_the_stub_names_no_log_no_injection_and_no_second_writer(self):
        source = read_text(STUB).lower()
        for forbidden in ("calls.log", "injection", "writer2", "target-section", "armed"):
            self.assertNotIn(forbidden, source, forbidden)
        self.assertIsNone(re.search(r"second[-_ ]writer", source))
        self.assertIsNone(re.search(r"inject", source))

    def test_the_stub_names_at_most_the_two_labelled_switch_variables(self):
        names = set(re.findall(r"CKPT_STUB_[A-Z0-9_]+", read_text(STUB)))
        self.assertLessEqual(len(names), 2, sorted(names))


class WrapperSourceTests(unittest.TestCase):
    def test_mode_shebang_and_bash_3_2_only(self):
        self.assertTrue(os.path.isfile(WRAPPER_SRC), "tests/harness/checkpoint-wrapper does not exist")
        mode = os.stat(WRAPPER_SRC).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "the wrapper must be executable")
        source = read_text(WRAPPER_SRC)
        self.assertEqual("#!/bin/bash", source.split("\n", 1)[0])
        for pattern in (
            r"declare\s+-[aA]",
            r"\bmapfile\b",
            r"\breadarray\b",
            r"\[\[\s+-v",
            r"&>>",
            r"\|&",
            r"wait\s+-n",
            r"\$\{[^}]*(,,|\^\^)[^}]*\}",
            r"\w=\(",
            r"\blocal\s+-n\b",
        ):
            self.assertIsNone(re.search(pattern, source), pattern)


class DriverVerbsTests(unittest.TestCase):
    """bind, create and init are refused by the wrapper whatever launched it (STUB-06, layer 2)."""

    def verb_args(self, rig, verb):
        if verb == "bind":
            return ["bind", "--ledger", rig.ledger, "--project", "x", "--workstream", "y"]
        return [verb, "--ledger", rig.ledger]

    def assert_refused(self, rig, args, result, before):
        code, out, err = result
        self.assertEqual(71, code, err)
        self.assertEqual("", out)
        self.assertIn("driver-only verb", err)
        self.assertNotIn(BRAND, err, "nothing may be delegated to the stub")
        self.assertEqual(before, tree_digest(rig.ckpt))
        lines = rig.log("calls.log").splitlines()
        self.assertEqual(2, len(lines))
        self.assertRegex(lines[0], CALL_LINE)
        self.assertEqual(args, shlex.split(lines[0].split(" CALL", 1)[1]))
        self.assertRegex(lines[1], EXIT_LINE)
        self.assertTrue(lines[1].endswith(" EXIT 71"), lines[1])

    def test_driver_verbs_are_refused_with_exit_71_directly(self):
        for verb in ("bind", "create", "init"):
            rig = Rig(armed=None)
            before = tree_digest(rig.ckpt)
            args = self.verb_args(rig, verb)
            self.assert_refused(rig, args, rig.wrap(args), before)

    def test_driver_verbs_are_refused_with_exit_71_when_launched_through_env(self):
        for verb in ("bind", "create", "init"):
            rig = Rig(armed=None)
            before = tree_digest(rig.ckpt)
            args = self.verb_args(rig, verb)
            self.assert_refused(rig, args, rig.via_env(args), before)

    def test_driver_verbs_are_refused_behind_a_leading_session_option(self):
        other = "feedface-0000-4000-8000-000000000001"
        for verb in ("bind", "create", "init"):
            for lead in (["--session", other], ["--session=" + other]):
                rig = Rig(armed=None)
                before = tree_digest(rig.ckpt)
                args = lead + self.verb_args(rig, verb)
                self.assert_refused(rig, args, rig.wrap(args), before)

    def test_an_option_before_the_verb_reaches_the_stub_which_exits_2_and_changes_nothing(self):
        rig = Rig(armed=None)
        before = tree_digest(rig.ckpt)
        args = ["--no-such-option", "bind", "--ledger", rig.ledger]
        code, out, err = rig.wrap(args)
        self.assertEqual(2, code, err)
        self.assertTrue(err.startswith(BRAND + "\n"), err)
        self.assertEqual(before, tree_digest(rig.ckpt))
        self.assertTrue(rig.log("calls.log").splitlines()[-1].endswith(" EXIT 2"))

    def test_model_facing_verbs_are_not_refused(self):
        rig = Rig(armed=None)
        for verb in ("status", "show", "lint"):
            code, _, err = rig.wrap([verb])
            self.assertEqual(0, code, err)


if __name__ == "__main__":
    unittest.main()
