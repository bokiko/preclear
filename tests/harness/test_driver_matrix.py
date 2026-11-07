"""Zero-token tests for the campaign driver (plan 04-02; RERUN-02, RERUN-03; D-01, D-02, D-03, D-12).

The driver can now run a campaign: a labelled dated folder, an evidence-date override, attempts that never
collide, a loop over several rows that goes on after a skipped or stopped row, one honest exit code and a
per-invocation budget. No test starts a real claude: the only claude executed is the scripted fake written by
pc_testutil, and rows that only need an outcome are injected through the registry argument of main with a callable
runner. Every folder comes from RowRig or tempfile and is never deleted. Modules are imported inside small
accessors, so a missing module is one error per test and not one load failure of the file. A refusal is never
asserted by the value that caused it, and leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_spend
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW1 = "row1-wrong-binding"
ROW4A = "row4a-unknown-backend"
MODEL = "claude-sonnet-5-5"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
CLEAN_DATE = "2026-10-27"


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def fixed_clock():
    return FIXED_DATE


def spec_of(row_id: str):
    pc_rows = rows()
    entry = pc_rows.find_runnable(pc_rows.build_registry(), row_id)  # a row or a layout (plan 04-15)
    assert entry is not None, row_id
    return entry


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def read_json(path: str):
    return json.loads(read_text(path))


def scratch() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-drv-"))


class NoProcess(object):
    """Context manager: any subprocess.Popen in this process is a test failure."""

    def __enter__(self):
        self.patch = mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started"))
        self.patch.start()
        return self

    def __exit__(self, *exc):
        self.patch.stop()
        return False


def drive(rig, args, registry=None, clock=fixed_clock, claude=True):
    """Run pc_matrix.main on a rig's repository with its environment; return (code, stdout, stderr)."""
    out = io.StringIO()
    err = io.StringIO()
    argv = list(args)
    if claude:
        argv += ["--claude", rig.claude]
    kwargs = {} if registry is None else {"registry": registry}
    code = matrix().main(argv, env=dict(rig.env), repo_root=rig.repo, clock=clock, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def rig_for(*row_ids, repeat=1):
    """A rig whose scripted claude plays the clean stages of the given rows in order, repeat times over."""
    stages = []
    for _ in range(repeat):
        for row_id in row_ids:
            stages += pc_testutil.default_row_stages(spec_of(row_id))
    return pc_testutil.RowRig(stages=stages)


def implemented_ids() -> list:
    """The ids of every implemented entry in registry order, the layouts first: what --all runs (plan 04-15)."""
    pc_rows = rows()
    return [e.row_id for e in pc_rows.build_registry() if e.implemented]


def ledger_of(rig):
    import pc_spike

    home = pc_spike.harness_home(rig.env, rig.env["HOME"], rig.repo)
    return pc_spend.read_records(home)


def evidence_names(rig) -> list:
    return sorted(os.listdir(os.path.join(rig.repo, "tests", "evidence")))


class ScopingTests(unittest.TestCase):
    """The naming functions that every folder and every ledger identity of a campaign is built from."""

    def test_the_dated_folder_name_gains_the_label_as_a_suffix_only(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.evidence_folder_name("2026-11-05", MODEL), "rerun-2026-11-05-claude-sonnet-5-5")
        self.assertEqual(
            pc_rows.evidence_folder_name("2026-11-05", MODEL, "wave-a"), "rerun-2026-11-05-claude-sonnet-5-5-wave-a"
        )
        self.assertEqual(pc_rows.evidence_folder_name("2026-11-05", MODEL, None), "rerun-2026-11-05-claude-sonnet-5-5")
        with self.assertRaises(ValueError):
            pc_rows.evidence_folder_name("2026-11-05", MODEL, "Wave")

    def test_scoped_row_ids_follow_the_scope_the_attempt_and_the_matrix_word(self) -> None:
        pc_rows = rows()
        row = "row3a-missing-executable"
        self.assertEqual(pc_rows.scoped_row(row, "wave-a", 1, False), "wave-a-row3a-missing-executable")
        self.assertEqual(pc_rows.scoped_row(row, "wave-a", 2, False), "wave-a-a2-row3a-missing-executable")
        self.assertEqual(pc_rows.scoped_row(row, None, 1, True), "matrix-row3a-missing-executable")
        self.assertEqual(pc_rows.scoped_row(row, None, 3, True), "matrix-a3-row3a-missing-executable")
        self.assertEqual(pc_rows.scoped_row(row), row, "no scope and attempt 1 is the bare Phase 3 id")
        self.assertEqual(pc_rows.scoped_row(row, None, 2, False), "a2-row3a-missing-executable")
        self.assertEqual(
            pc_rows.scoped_row(row, "wave-a", 1, True), "wave-a-row3a-missing-executable", "the label wins over matrix"
        )

    def test_scoped_stage_keys_scope_the_stage_key_of_the_row(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.scoped_stage_key(ROW4A, "s1", "wave-a"), "wave-a-row4a-s1")
        self.assertEqual(pc_rows.scoped_stage_key(ROW4A, "s2", "wave-a", 2), "wave-a-a2-row4a-s2")
        self.assertEqual(pc_rows.scoped_stage_key(ROW1, "s3", None, 1, True), "matrix-row1-s3")
        self.assertEqual(pc_rows.scoped_stage_key(ROW1, "s1"), "row1-s1")

    def test_the_row_folder_is_bare_for_attempt_one_and_suffixed_above(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.row_folder_name(ROW1), ROW1)
        self.assertEqual(pc_rows.row_folder_name(ROW1, 1), ROW1)
        self.assertEqual(pc_rows.row_folder_name(ROW1, 2), "row1-wrong-binding-attempt-2")
        self.assertEqual(pc_rows.row_folder_name(ROW1, 9), "row1-wrong-binding-attempt-9")
        for bad in (0, 10, -1, True, "2", 2.0, None):
            with self.assertRaises(ValueError):
                pc_rows.row_folder_name(ROW1, bad)

    def test_a_label_is_one_lowercase_id_of_at_most_24_characters_without_the_attempt_words(self) -> None:
        pc_rows = rows()
        for good in ("wave-a", "a", "w", "wave-1", "matrix", "x" * 24, "a-b-c", "a10", "wave-a0", "aa1"):
            self.assertTrue(pc_rows.is_valid_campaign(good), good)
        for bad in (
            "",
            "x" * 25,
            "Wave",
            "WAVE-A",
            "wave a",
            "wave_a",
            "wave--a",
            "-wave",
            "wave-",
            "wave\n",
            "wave" + chr(0x0301),
            "a1",
            "a5",
            "a9",
            "wave-a2",
            "a3-wave",
            "x-a9-y",
            None,
            5,
        ):
            self.assertFalse(pc_rows.is_valid_campaign(bad), repr(bad))

    def test_the_longest_id_stays_within_the_64_character_ledger_rule(self) -> None:
        pc_rows = rows()
        longest = max(pc_rows.ROW_IDS, key=len)
        text = pc_rows.scoped_row(longest, "x" * 24, 9, False)
        self.assertLessEqual(len(text), 64)
        self.assertTrue(pc_rows.is_valid_id(text))
        for row_id in pc_rows.ROW_IDS + pc_rows.LAYOUT_IDS:
            for stage in ("s1", "s2", "s3", "s4"):
                key = pc_rows.scoped_stage_key(row_id, stage, "x" * 24, 9, False)
                self.assertLessEqual(len(key), 64)
        with self.assertRaises(ValueError):
            pc_rows.scoped_row("a" * 60, "x" * 24, 9, False)

    def test_no_two_selections_give_the_same_ledger_id(self) -> None:
        pc_rows = rows()
        labels = [None, "matrix", "wave", "wave-a", "a", "x", "wave-b"]
        seen = {}
        for row_id in ("row1-wrong-binding", "row2-double-conflict", "plain-memory"):
            for label in labels:
                for attempt in range(1, 10):
                    for matrix_flag in (False, True):
                        if label is not None and matrix_flag:
                            continue
                        key = pc_rows.scoped_row(row_id, label, attempt, matrix_flag)
                        if label == "matrix" and not matrix_flag:
                            continue  # the label matrix and the matrix flag name the same scope on purpose
                        identity = (row_id, label, attempt, matrix_flag)
                        self.assertNotIn(key, seen, "two selections built the same id")
                        seen[key] = identity
        # the reserved words are why a label may not mimic an attempt of another label
        self.assertFalse(pc_rows.is_valid_campaign("wave-a2"))
        self.assertEqual(pc_rows.scoped_row("row1-wrong-binding", "wave", 2, False), "wave-a2-row1-wrong-binding")

    def test_the_worst_case_is_the_smaller_of_the_cap_sum_and_the_row_cap(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.worst_case(spec_of(ROW4A)), Decimal("1.60"))
        self.assertEqual(pc_rows.worst_case(spec_of(ROW1)), Decimal("2.00"))


class CampaignTests(unittest.TestCase):
    """A scripted row runs through main under --campaign and --evidence-date."""

    LABEL = "wave-a"

    def run_campaign(self, rig, label=None, date=CLEAN_DATE, extra=(), registry=None):
        args = ["--row", ROW4A, "--budget", "1.60", "--campaign", label or self.LABEL, "--evidence-date", date]
        return drive(rig, args + list(extra), registry)

    def test_a_campaign_run_files_into_the_labelled_dated_folder_with_scoped_identities(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = self.run_campaign(rig)
        self.assertEqual(code, 0, out + err)
        dated = "rerun-2026-10-27-claude-sonnet-5-5-wave-a"
        self.assertEqual([name for name in evidence_names(rig) if name.startswith("rerun-")], [dated])
        self.assertTrue(os.path.isdir(os.path.join(rig.repo, "tests", "evidence", dated, ROW4A)))
        self.assertIn("filed: %s %s" % (dated, ROW4A), out)
        ledger = ledger_of(rig)
        self.assertEqual(
            [(line["kind"], line["row"], line["stage"]) for line in ledger],
            [
                ("launch", "wave-a-row4a-unknown-backend", "wave-a-row4a-s1"),
                ("settle", "wave-a-row4a-unknown-backend", "wave-a-row4a-s1"),
                ("launch", "wave-a-row4a-unknown-backend", "wave-a-row4a-s2"),
                ("settle", "wave-a-row4a-unknown-backend", "wave-a-row4a-s2"),
            ],
        )
        self.assertEqual(len(rig.calls()), 2)

    def test_the_run_root_name_and_the_run_record_carry_the_scope(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = self.run_campaign(rig)
        self.assertEqual(code, 0, out + err)
        import pc_spike

        runs = pc_spike.runs_root(rig.env, rig.env["HOME"], rig.repo)
        names = os.listdir(runs)
        self.assertEqual(len(names), 1)
        self.assertTrue(names[0].startswith("wave-a-row4a-unknown-backend-"), names[0])
        raw = os.path.join(runs, names[0], "raw")
        self.assertEqual(read_json(os.path.join(raw, "run.json"))["evidence_date"], CLEAN_DATE)
        self.assertEqual(read_json(os.path.join(raw, "scope.json")), {"attempt": 1, "campaign": "wave-a", "matrix": False})

    def test_a_second_label_has_its_own_attempt_count_in_the_same_harness_home(self) -> None:
        rig = rig_for(ROW4A, repeat=2)
        first = self.run_campaign(rig, label="wave-a")
        second = self.run_campaign(rig, label="wave-b")
        self.assertEqual(first[0], 0, first[1] + first[2])
        self.assertEqual(second[0], 0, second[1] + second[2])
        launches = [line for line in ledger_of(rig) if line["kind"] == "launch"]
        self.assertEqual(len(launches), 4)
        self.assertEqual({line["attempt"] for line in launches}, {1}, "no stage counted a second attempt")
        self.assertEqual(
            sorted(name for name in evidence_names(rig) if name.startswith("rerun-")),
            [
                "rerun-2026-10-27-claude-sonnet-5-5-wave-a",
                "rerun-2026-10-27-claude-sonnet-5-5-wave-b",
            ],
        )

    def test_the_same_label_twice_is_refused_as_a_taken_destination_or_a_used_attempt(self) -> None:
        rig = rig_for(ROW4A, repeat=2)
        self.assertEqual(self.run_campaign(rig)[0], 0)
        code, out, err = self.run_campaign(rig)
        self.assertIn(code, (pc_exitcodes.PROMOTE_REFUSED, pc_exitcodes.BUDGET_REFUSED), out + err)
        self.assertEqual(len(rig.calls()), 2, "no second chain was started")

    def test_a_dry_run_with_the_new_flags_prints_the_suffixed_destination_and_starts_nothing(self) -> None:
        rig = rig_for(ROW4A)
        with NoProcess():
            code, out, err = drive(
                rig,
                ["--dry-run", "--row", ROW4A, "--campaign", self.LABEL, "--evidence-date", "2026-10-30"],
                clock=lambda: datetime.datetime(2026, 11, 1, 9, 0, 0, tzinfo=datetime.timezone.utc),
            )
        self.assertEqual(code, 0, out + err)
        self.assertIn("destination tests/evidence/rerun-2026-10-30-claude-sonnet-5-5-wave-a\n", out)
        self.assertEqual(rig.calls(), [])
        self.assertEqual(rig.tripwire(), [])
        self.assertFalse(os.path.exists(rig.harness_home), "a dry run creates no harness home")
        self.assertEqual([name for name in evidence_names(rig) if name.startswith("rerun-")], [])

    def test_the_label_alone_suffixes_the_clock_date_folder(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--campaign", "wave-a"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("destination tests/evidence/rerun-2026-10-28-claude-sonnet-5-5-wave-a\n", out)

    def test_a_bad_label_is_refused_with_exit_2_and_the_value_is_never_echoed(self) -> None:
        rig = rig_for(ROW4A)
        for value in ("x" * 25, "WaveProbeZz", "", "a1", "a9", "wave-a2", "probe_zz", "probe zz", "probe\nzz"):
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--campaign", value], claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, repr(value))
            self.assertEqual(out, "", "a refusal wrote to standard output")
            self.assertEqual(err, "pc_matrix.py: %s\n" % matrix().MESSAGE_BAD_CAMPAIGN, "only the fixed text")
        self.assertFalse(os.path.exists(rig.harness_home))

    def test_a_bad_date_is_refused_with_exit_2_and_the_value_is_never_echoed(self) -> None:
        rig = rig_for(ROW4A)
        bad = ("2999-01-01", "2026-02-30", "2026-10-29", "2026-1-5", "20261027", "", "2026-10-27 ", "probe-date", "2026-13-01")
        for value in bad:
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--evidence-date", value], claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, repr(value))
            self.assertEqual(out, "")
            self.assertEqual(err, "pc_matrix.py: %s\n" % matrix().MESSAGE_BAD_DATE, "only the fixed text")

    def test_today_and_earlier_dates_are_accepted(self) -> None:
        rig = rig_for(ROW4A)
        for value in ("2026-10-28", "2026-10-27", "2025-01-01"):
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--evidence-date", value], claude=False)
            self.assertEqual(code, 0, out + err)
            self.assertIn("destination tests/evidence/rerun-%s-claude-sonnet-5-5\n" % value, out)

    def test_the_new_flags_cannot_be_combined_with_a_mode_that_does_not_run_rows(self) -> None:
        rig = rig_for(ROW4A)
        for flags in (["--campaign", "wave-a"], ["--evidence-date", CLEAN_DATE]):
            for mode in (["--list"], ["--refile", "relative"], ["--authorize-retry", "row1-s2"]):
                code, out, err = drive(rig, mode + flags, claude=False)
                self.assertEqual(code, pc_exitcodes.USAGE, " ".join(mode + flags))

    def test_no_printed_line_of_a_campaign_run_holds_a_path(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = self.run_campaign(rig)
        self.assertEqual(code, 0, out + err)
        for text in (out, err):
            self.assertNotIn(rig.base, text)
            self.assertNotIn(ROOT, text)



def injected(row_id, caps=("0.10",), precondition=None, runner=None, kind="row"):
    """A registry entry for a test: one stage per cap, every stage in a new session, no sources."""
    pc_rows = rows()
    stages = tuple(
        pc_rows.StageSpec("s%d" % (index + 1), "work turn", "work", 5, Decimal(cap), 60, "new:%s" % "ABCDEFGH"[index])
        for index, cap in enumerate(caps)
    )
    return pc_rows.RowSpec(row_id, kind, "injected test row", stages, True, precondition, runner, ())


class Recorder(object):
    """Scripted row runners that remember who ran, in what order and under which scope."""

    def __init__(self) -> None:
        self.calls = []

    def runner(self, row_id, code=0, spent=None):
        def run(ctx):
            self.calls.append((row_id, ctx.campaign, ctx.attempt, ctx.matrix))
            return rows().RowOutcome(code, ("scripted %s" % row_id,), spent)

        return run

    def ids(self):
        return [call[0] for call in self.calls]


def registry_of(*extra):
    return rows().build_registry(extra=list(extra))


def assert_clean(test, rig, text):
    """No path of the rig, no home path and no verdict word in anything the driver printed."""
    test.assertNotIn(rig.base, text)
    test.assertNotIn(ROOT, text)
    test.assertIsNone(re.search(r"\b(pass|passed|fail|accepted)\b", text, re.I), "a verdict word was printed")


def dated_folder(rig, date="2026-10-28", label=None) -> str:
    name = "rerun-%s-%s" % (date, MODEL) + ("" if label is None else "-" + label)
    return os.path.join(rig.repo, "tests", "evidence", name)


class SelectionTests(unittest.TestCase):
    """--row and --layout may be repeated and combined; the entries run in registry order."""

    def setUp(self) -> None:
        self.rig = pc_testutil.RowRig(stages=[])
        self.rec = Recorder()
        self.layout = injected("layout0-x", runner=self.rec.runner("layout0-x"), kind="layout")
        self.a = injected("row0-a", runner=self.rec.runner("row0-a"))
        self.b = injected("row0-b", runner=self.rec.runner("row0-b"))
        self.registry = (self.layout, self.a, self.b)

    def run_ok(self, args):
        code, out, err = drive(self.rig, args + ["--budget", "1.00"], self.registry)
        return code, out, err

    def test_the_entries_run_in_registry_order_whatever_order_they_were_typed_in(self) -> None:
        code, out, err = self.run_ok(["--row", "row0-b", "--layout", "layout0-x", "--row", "row0-a"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.rec.ids(), ["layout0-x", "row0-a", "row0-b"])

    def test_two_rows_typed_in_reverse_still_run_in_registry_order(self) -> None:
        code, out, err = self.run_ok(["--row", "row0-b", "--row", "row0-a"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a", "row0-b"])

    def test_the_dry_run_plan_lists_the_selected_entries_in_registry_order_with_a_total(self) -> None:
        code, out, err = drive(
            self.rig, ["--dry-run", "--row", "row0-b", "--layout", "layout0-x"], self.registry, claude=False
        )
        self.assertEqual(code, 0, out + err)
        self.assertLess(out.index("layout0-x: 1 stages"), out.index("row0-b: 1 stages"))
        self.assertNotIn("row0-a", out)
        self.assertIn("total: 2 row(s), 2 stage(s), 2 session(s), worst case 0.20 USD", out)
        self.assertEqual(self.rec.calls, [])

    def test_a_repeated_or_unknown_id_is_refused_with_exit_2_and_never_echoed(self) -> None:
        for args in (
            ["--row", "row0-a", "--row", "row0-a"],
            ["--layout", "layout0-x", "--layout", "layout0-x"],
            ["--row", "row0-a", "--row", "row0-zz-probe"],
            ["--row", "row0-zz-probe", "--row", "row0-a"],
            ["--row", "row0-a", "--layout", "layout0-zz-probe"],
        ):
            code, out, err = drive(self.rig, ["--dry-run"] + args, self.registry, claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(args))
            self.assertEqual(out, "", "a refusal wrote to standard output")
            self.assertNotIn("probe", err)
            self.assertNotIn("row0-a", err)
        self.assertEqual(self.rec.calls, [])

    def test_all_cannot_be_combined_with_row_or_layout(self) -> None:
        for extra in (["--row", "row0-a"], ["--layout", "layout0-x"], ["--row", "row0-a", "--layout", "layout0-x"]):
            code, out, err = drive(self.rig, ["--dry-run", "--all"] + extra, self.registry, claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(extra))
        self.assertEqual(self.rec.calls, [])

    def test_all_runs_every_implemented_entry_in_registry_order(self) -> None:
        code, out, err = drive(self.rig, ["--dry-run", "--all"], self.registry, claude=False)
        self.assertEqual(code, 0, out + err)
        positions = [out.index("%s: 1 stages" % name) for name in ("layout0-x", "row0-a", "row0-b")]
        self.assertEqual(positions, sorted(positions))

    def test_the_real_registry_lists_layouts_before_rows_and_all_follows_it(self) -> None:
        pc_rows = rows()
        implemented = [entry for entry in pc_rows.build_registry() if entry.implemented]
        kinds = [entry.kind for entry in implemented]
        self.assertEqual(kinds, sorted(kinds, key=lambda kind: 0 if kind == "layout" else 1))
        ids = [entry.row_id for entry in implemented]
        self.assertEqual(ids, [row_id for row_id in pc_rows.LAYOUT_IDS + pc_rows.ROW_IDS if row_id in ids])
        code, out, err = drive(self.rig, ["--dry-run", "--all"], claude=False)
        self.assertEqual(code, 0, out + err)
        listed = [line.split(":")[0] for line in out.splitlines() if re.match(r"^[a-z0-9-]+: \d+ stages", line)]
        self.assertEqual(listed, ids)


class LoopTests(unittest.TestCase):
    """The loop goes on after a skipped, stopped or incomplete row and reports one honest exit code."""

    def setUp(self) -> None:
        self.rig = pc_testutil.RowRig(stages=[])
        self.rec = Recorder()

    def run_rows(self, specs, extra=(), budget="5.00"):
        """specs is a list of (row id, kind of result): clean, skip, a code number or a spent figure tuple."""
        entries = []
        for row_id, how in specs:
            if how == "skip":
                entries.append(injected(row_id, precondition=lambda: "the fixture of this test row is absent"))
            else:
                entries.append(injected(row_id, runner=self.rec.runner(row_id, code=how)))
        args = []
        for row_id, _how in specs:
            args += ["--row", row_id]
        code, out, err = drive(self.rig, args + ["--budget", budget] + list(extra), registry_of(*entries))
        assert_clean(self, self.rig, out + err)
        return code, out, err

    def test_a_skipped_a_stopped_and_a_clean_row_are_all_attempted_and_the_exit_is_11(self) -> None:
        code, out, err = self.run_rows([("row0-a", "skip"), ("row0-b", 11), ("row0-c", 0)])
        self.assertEqual(code, 11, out + err)
        self.assertEqual(self.rec.ids(), ["row0-b", "row0-c"], "the stopped row did not end the loop")
        lines = out.splitlines()
        self.assertIn("row row0-a: skipped, exit 10, spent 0.00 USD", lines)
        self.assertIn("row row0-b: stopped, exit 11, spent 0.00 USD", lines)
        self.assertIn("row row0-c: filed, exit 0, spent 0.00 USD", lines)
        self.assertIn("summary: 3 row(s) selected, 1 filed, 1 stopped, 1 skipped, 0 refused, 0 not started", lines)
        self.assertLess(lines.index("row row0-a: skipped, exit 10, spent 0.00 USD"), lines.index(
            "row row0-b: stopped, exit 11, spent 0.00 USD"))
        self.assertTrue(os.path.isfile(os.path.join(dated_folder(self.rig), "SKIPPED-row0-a", "README.md")))

    def test_a_skip_only_run_exits_10_and_never_0(self) -> None:
        code, out, err = self.run_rows([("row0-a", "skip"), ("row0-b", "skip")])
        self.assertEqual(code, 10, out + err)
        self.assertIn("summary: 2 row(s) selected, 0 filed, 0 stopped, 2 skipped, 0 refused, 0 not started", out)
        self.assertEqual(self.rec.calls, [])
        self.assertEqual(sorted(os.listdir(dated_folder(self.rig))), ["SKIPPED-row0-a", "SKIPPED-row0-b"])

    def test_a_skip_only_run_needs_no_budget(self) -> None:
        entry = injected("row0-a", precondition=lambda: "the fixture of this test row is absent")
        code, out, err = drive(self.rig, ["--row", "row0-a"], registry_of(entry), claude=False)
        self.assertEqual(code, 10, out + err)

    def test_a_clean_run_exits_0(self) -> None:
        code, out, err = self.run_rows([("row0-a", 0), ("row0-b", 0)])
        self.assertEqual(code, 0, out + err)
        self.assertIn("summary: 2 row(s) selected, 2 filed, 0 stopped, 0 skipped, 0 refused, 0 not started", out)

    def test_the_exit_code_is_the_worst_row_outcome_in_the_order_19_11_10_0(self) -> None:
        cases = (
            ([("row0-a", 11), ("row0-b", 19)], 19),
            ([("row0-a", 19), ("row0-b", 11)], 19),
            ([("row0-a", "skip"), ("row0-b", 11)], 11),
            ([("row0-a", 11), ("row0-b", "skip")], 11),
            ([("row0-a", "skip"), ("row0-b", 0)], 10),
            ([("row0-a", 0), ("row0-b", 19)], 19),
        )
        for specs, expected in cases:
            self.rec.calls.clear()
            self.rig = pc_testutil.RowRig(stages=[])
            code, out, err = self.run_rows(specs)
            self.assertEqual(code, expected, "%s -> %s" % (specs, out + err))
            self.assertEqual(len(self.rec.calls) + sum(1 for _r, how in specs if how == "skip"), 2, "all rows ran")

    def test_a_filing_failure_or_refusal_ends_the_invocation_at_once(self) -> None:
        for ending in (14, 15, 16, 17, 18):
            self.rec.calls.clear()
            self.rig = pc_testutil.RowRig(stages=[])
            code, out, err = self.run_rows([("row0-a", 0), ("row0-b", ending), ("row0-c", 0)])
            self.assertEqual(code, ending, out + err)
            self.assertEqual(self.rec.ids(), ["row0-a", "row0-b"], "no row was started after the ending code")
            self.assertIn("row row0-b: refused, exit %d, spent 0.00 USD" % ending, out)
            self.assertIn("summary: 3 row(s) selected, 1 filed, 0 stopped, 0 skipped, 1 refused, 1 not started", out)

    def test_a_taken_skipped_label_is_refused_by_the_gate_before_any_row_runs(self) -> None:
        entries = [
            injected("row0-a", precondition=lambda: "no fixture"),
            injected("row0-b", runner=self.rec.runner("row0-b")),
        ]
        os.makedirs(os.path.join(dated_folder(self.rig), "SKIPPED-row0-a"))
        code, out, err = drive(
            self.rig, ["--row", "row0-a", "--row", "row0-b", "--budget", "1.00"], registry_of(*entries)
        )
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(self.rec.calls, [], "the gate refused before any row ran")

    def test_the_driver_never_prints_a_verdict_and_every_line_is_fixed_text(self) -> None:
        code, out, err = self.run_rows([("row0-a", "skip"), ("row0-b", 19), ("row0-c", 0)])
        for line in out.splitlines():
            if line.startswith(("row row0", "summary:")):
                self.assertRegex(
                    line,
                    r"^(row row0-[a-c]: (filed|skipped|stopped|refused), exit \d+, spent \d+\.\d\d USD"
                    r"|summary: \d+ row\(s\) selected, \d+ filed, \d+ stopped, \d+ skipped, \d+ refused, \d+ not started)$",
                )

    def test_aggregation_is_a_pure_function_of_the_outcomes(self) -> None:
        pc_matrix = matrix()
        row = injected("row0-a")
        zero = Decimal("0")

        def agg(codes, ending=None):
            return pc_matrix._aggregate_code([(row, code, zero) for code in codes], ending)

        self.assertEqual(agg([]), 0)
        self.assertEqual(agg([0, 0]), 0)
        self.assertEqual(agg([0, 10]), 10)
        self.assertEqual(agg([10, 11]), 11)
        self.assertEqual(agg([11, 19, 10]), 19)
        self.assertEqual(agg([0, 19], ending=17), 17)
        self.assertEqual(agg([], ending=18), 18)

    def test_a_precondition_row_in_a_dry_run_stops_the_gate_loop_as_before(self) -> None:
        entries = [injected("row0-a", precondition=lambda: "no fixture"), injected("row0-b")]
        code, out, err = drive(
            self.rig, ["--dry-run", "--row", "row0-a", "--row", "row0-b"], registry_of(*entries), claude=False
        )
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_SKIP, out + err)


class MatrixScopeTests(unittest.TestCase):
    """--all without a campaign scopes its ledger rows with the word matrix; a single row keeps the bare ids."""

    def test_a_matrix_run_is_not_refused_when_the_ledger_already_holds_the_bare_row_1_lines(self) -> None:
        ids = implemented_ids()
        rig = rig_for(*ids)
        import pc_spike

        home = pc_spike.harness_home(rig.env, rig.env["HOME"], rig.repo)
        bare = ("row1-s1", "row1-s2", "row1-s3")
        for key in bare:
            pc_spend.append_launch(home, ROW1, key, Decimal("0.10"), "2.1.310", bare)
        code, out, err = drive(rig, ["--all", "--budget", "25.00"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(len(rig.calls()), sum(len(spec_of(row_id).stages) for row_id in ids))
        scoped = sorted({line["row"] for line in ledger_of(rig) if line["row"].startswith("matrix-")})
        self.assertEqual(scoped, sorted("matrix-" + row_id for row_id in ids))
        dated = dated_folder(rig)
        self.assertEqual(sorted(os.listdir(dated)), sorted(ids))
        self.assertIn(
            "summary: %d row(s) selected, %d filed, 0 stopped, 0 skipped, 0 refused, 0 not started" % (len(ids), len(ids)),
            out,
        )
        assert_clean(self, rig, out + err)

    def test_a_single_row_without_a_campaign_keeps_the_bare_ids(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = drive(rig, ["--row", ROW4A, "--budget", "1.60"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual({line["row"] for line in ledger_of(rig)}, {ROW4A})
        self.assertEqual({line["stage"] for line in ledger_of(rig)}, {"row4a-s1", "row4a-s2"})

    def test_a_campaign_with_all_uses_the_label_and_not_the_matrix_word(self) -> None:
        ids = implemented_ids()
        rig = rig_for(*ids)
        code, out, err = drive(rig, ["--all", "--campaign", "wave-m", "--budget", "25.00"])
        self.assertEqual(code, 0, out + err)
        rows_in_ledger = {line["row"] for line in ledger_of(rig)}
        self.assertEqual(rows_in_ledger, set("wave-m-" + row_id for row_id in ids))
        self.assertTrue(os.path.isdir(dated_folder(rig, label="wave-m")))


class AttemptTests(unittest.TestCase):
    """--attempt names the row folder and scopes the ledger, and needs an earlier attempt on record."""

    def first_attempt(self, rig, extra=()):
        return drive(rig, ["--row", ROW4A, "--budget", "1.60"] + list(extra))

    def test_an_attempt_without_an_earlier_launch_is_refused_with_18_and_creates_nothing(self) -> None:
        rig = rig_for(ROW4A)
        code, out, err = drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2"])
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertIn(matrix().MESSAGE_NO_EARLIER_ATTEMPT, err)
        self.assertEqual(rig.calls(), [])
        self.assertFalse(os.path.exists(rig.harness_home), "no ledger or harness home was created")
        self.assertEqual([n for n in evidence_names(rig) if n.startswith("rerun-")], [])
        self.assertFalse(os.path.exists(rig.runs), "no run folder was created")
        assert_clean(self, rig, out + err)

    def test_attempt_two_runs_after_attempt_one_and_files_its_own_folder_and_ledger_rows(self) -> None:
        rig = rig_for(ROW4A, repeat=2)
        self.assertEqual(self.first_attempt(rig)[0], 0)
        code, out, err = drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2"])
        self.assertEqual(code, 0, out + err)
        dated = dated_folder(rig)
        self.assertEqual(sorted(os.listdir(dated)), [ROW4A, ROW4A + "-attempt-2"])
        self.assertIn("filed: %s %s-attempt-2" % (os.path.basename(dated), ROW4A), out)
        ledger = ledger_of(rig)
        self.assertEqual(
            sorted({(line["row"], line["stage"]) for line in ledger}),
            sorted(
                [
                    (ROW4A, "row4a-s1"),
                    (ROW4A, "row4a-s2"),
                    ("a2-" + ROW4A, "a2-row4a-s1"),
                    ("a2-" + ROW4A, "a2-row4a-s2"),
                ]
            ),
        )
        self.assertEqual({line["attempt"] for line in ledger}, {1}, "each scoped stage is on its first attempt")
        self.assertTrue(os.path.isfile(os.path.join(dated, ROW4A + "-attempt-2", "README.md")))

    def test_attempt_three_needs_attempt_two_on_record(self) -> None:
        rig = rig_for(ROW4A, repeat=2)
        self.assertEqual(self.first_attempt(rig)[0], 0)
        code, out, err = drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "3"])
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(len(rig.calls()), 2)

    def test_the_same_attempt_twice_is_refused_as_a_taken_row_folder(self) -> None:
        rig = rig_for(ROW4A, repeat=3)
        self.assertEqual(self.first_attempt(rig)[0], 0)
        self.assertEqual(drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2"])[0], 0)
        code, out, err = drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2"])
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(len(rig.calls()), 4, "no third chain started")

    def test_a_campaign_attempt_looks_for_the_earlier_attempt_under_the_same_label(self) -> None:
        rig = rig_for(ROW4A, repeat=2)
        import pc_spike

        home = pc_spike.harness_home(rig.env, rig.env["HOME"], rig.repo)
        keys = ("wave-a-row4a-s1", "wave-a-row4a-s2")
        pc_spend.append_launch(home, "wave-a-" + ROW4A, keys[0], Decimal("0.10"), "2.1.310", keys)
        other = drive(rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2", "--campaign", "wave-b"])
        self.assertEqual(other[0], pc_exitcodes.BUDGET_REFUSED, other[1] + other[2])
        code, out, err = drive(
            rig, ["--row", ROW4A, "--budget", "1.60", "--attempt", "2", "--campaign", "wave-a", "--evidence-date", CLEAN_DATE]
        )
        self.assertEqual(code, 0, out + err)
        rows_in_ledger = {line["row"] for line in ledger_of(rig)}
        self.assertIn("wave-a-a2-" + ROW4A, rows_in_ledger)
        self.assertTrue(os.path.isdir(os.path.join(dated_folder(rig, CLEAN_DATE, "wave-a"), ROW4A + "-attempt-2")))

    def test_a_bad_attempt_is_refused_with_exit_2_and_fixed_text(self) -> None:
        rig = rig_for(ROW4A)
        for value in ("0", "10", "01", "2.0", "", "x", "-1", "+2", "22", "２", " 2", "2 ", "2\n"):
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--attempt", value], claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, repr(value))
            self.assertEqual(out, "")
            self.assertEqual(err, "pc_matrix.py: %s\n" % matrix().MESSAGE_BAD_ATTEMPT)

    def test_attempt_with_all_or_with_more_than_one_entry_is_refused_with_exit_2(self) -> None:
        rig = rig_for(ROW4A)
        for args in (
            ["--all", "--attempt", "2"],
            ["--row", ROW1, "--row", ROW4A, "--attempt", "2"],
            ["--row", ROW1, "--row", ROW4A, "--attempt", "1"],
            ["--all", "--attempt", "1"],
        ):
            code, out, err = drive(rig, ["--dry-run"] + args, claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(args))
            self.assertEqual(err, "pc_matrix.py: %s\n" % matrix().MESSAGE_ATTEMPT_WITH_ALL)

    def test_the_attempt_cannot_be_combined_with_a_mode_that_does_not_run_rows(self) -> None:
        rig = rig_for(ROW4A)
        for mode in (["--list"], ["--refile", "relative"], ["--authorize-retry", "row1-s2"]):
            code, out, err = drive(rig, mode + ["--attempt", "2"], claude=False)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(mode))

    def test_a_dry_run_does_not_read_the_ledger_and_prints_the_row_folder(self) -> None:
        rig = rig_for(ROW4A)
        with NoProcess():
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A, "--attempt", "2"], claude=False)
        self.assertEqual(code, 0, out + err)
        self.assertIn("row folder %s-attempt-2\n" % ROW4A, out)
        self.assertFalse(os.path.exists(rig.harness_home))

    def test_two_attempts_never_share_a_folder_or_a_ledger_row(self) -> None:
        pc_rows = rows()
        folders = {pc_rows.row_folder_name(ROW4A, attempt) for attempt in range(1, 10)}
        ledger_rows = {pc_rows.scoped_row(ROW4A, "wave-a", attempt, False) for attempt in range(1, 10)}
        self.assertEqual(len(folders), 9)
        self.assertEqual(len(ledger_rows), 9)


class RowFolderGateTests(unittest.TestCase):
    """The gate refuses only through the row: its folder, its STOPPED- folder or its SKIPPED- folder."""

    def setUp(self) -> None:
        self.rig = pc_testutil.RowRig(stages=[])
        self.dated = dated_folder(self.rig)

    def dry(self, attempt=None):
        extra = [] if attempt is None else ["--attempt", str(attempt)]
        with NoProcess():
            return drive(self.rig, ["--dry-run", "--row", ROW4A] + extra, claude=False)

    def test_an_existing_dated_folder_alone_is_not_refused(self) -> None:
        os.makedirs(self.dated)
        code, out, err = self.dry()
        self.assertEqual(code, 0, out + err)

    def test_the_row_folder_and_both_label_folders_are_refused_with_17(self) -> None:
        for name in (ROW4A, "STOPPED-" + ROW4A, "SKIPPED-" + ROW4A):
            rig_dated = os.path.join(self.dated, name)
            os.makedirs(rig_dated)
            code, out, err = self.dry()
            self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, name + out + err)
            self.assertIn(name, out)
            self.assertNotIn(self.rig.base, out + err)
            self.rig = pc_testutil.RowRig(stages=[])
            self.dated = dated_folder(self.rig)

    def test_another_rows_folder_does_not_block_this_row(self) -> None:
        os.makedirs(os.path.join(self.dated, ROW1))
        os.makedirs(os.path.join(self.dated, "STOPPED-" + ROW1))
        code, out, err = self.dry()
        self.assertEqual(code, 0, out + err)

    def test_the_attempt_selects_which_row_folder_is_checked(self) -> None:
        os.makedirs(os.path.join(self.dated, ROW4A))
        self.assertEqual(self.dry(2)[0], 0, "attempt 2 is free while attempt 1 exists")
        os.makedirs(os.path.join(self.dated, ROW4A + "-attempt-2"))
        self.assertEqual(self.dry(2)[0], pc_exitcodes.PROMOTE_REFUSED)
        self.assertEqual(self.dry(3)[0], 0)
        os.makedirs(os.path.join(self.dated, "SKIPPED-" + ROW4A + "-attempt-3"))
        self.assertEqual(self.dry(3)[0], pc_exitcodes.PROMOTE_REFUSED)

    def test_a_dated_name_that_is_a_link_or_a_file_is_refused(self) -> None:
        os.symlink(os.path.join(self.rig.base, "nowhere"), self.dated)
        self.assertEqual(self.dry()[0], pc_exitcodes.PROMOTE_REFUSED)
        rig = pc_testutil.RowRig(stages=[])
        with open(dated_folder(rig), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        with NoProcess():
            code, out, err = drive(rig, ["--dry-run", "--row", ROW4A], claude=False)
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)


class RefileAnyRowTests(unittest.TestCase):
    """--refile accepts a run folder of any registered row and files where the run's own scope says."""

    def chain(self, rig, **overrides):
        import pc_row1

        first = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5-first")
        ctx = rig.context(destination=first, **overrides)
        outcome = pc_row1.run_registered_row(ctx, ROW4A)
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        names = sorted(os.listdir(ctx.runs_root))
        self.assertEqual(len(names), 1, names)
        return os.path.join(ctx.runs_root, names[0])

    def refile(self, rig, run_root):
        out, err = io.StringIO(), io.StringIO()
        code = matrix().main(
            ["--refile", run_root], env=dict(rig.env), repo_root=rig.repo, clock=fixed_clock, out=out, err=err
        )
        return code, out.getvalue() + err.getvalue()

    def test_a_row_4a_run_is_refiled_into_its_row_folder_with_zero_tokens(self) -> None:
        rig = rig_for(ROW4A)
        run_root = self.chain(rig)
        calls = len(rig.calls())
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(rig.calls()), calls, "no process was started")
        self.assertTrue(os.path.isfile(os.path.join(dated_folder(rig), ROW4A, "README.md")))
        self.assertIn("filed: %s %s" % (os.path.basename(dated_folder(rig)), ROW4A), text)

    def test_the_campaign_and_the_attempt_of_the_run_name_the_folders(self) -> None:
        rig = rig_for(ROW4A)
        run_root = self.chain(rig, campaign="wave-a", attempt=2)
        scope = read_json(os.path.join(run_root, "raw", "scope.json"))
        self.assertEqual(scope, {"attempt": 2, "campaign": "wave-a", "matrix": False})
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, 0, text)
        target = os.path.join(dated_folder(rig, label="wave-a"), ROW4A + "-attempt-2")
        self.assertTrue(os.path.isfile(os.path.join(target, "README.md")))
        again, text = self.refile(rig, run_root)
        self.assertEqual(again, pc_exitcodes.PROMOTE_REFUSED, text)
        self.assertIn(ROW4A + "-attempt-2", text)

    def test_a_malformed_scope_record_makes_the_run_folder_unusable(self) -> None:
        rig = rig_for(ROW4A)
        run_root = self.chain(rig, campaign="wave-a")
        for body in ("{}", "[]", "not json", '{"attempt": 10, "campaign": null, "matrix": false}',
                     '{"attempt": 1, "campaign": "A1", "matrix": false}',
                     '{"attempt": true, "campaign": null, "matrix": false}'):
            with open(os.path.join(run_root, "raw", "scope.json"), "w", encoding="utf-8") as handle:
                handle.write(body)
            code, text = self.refile(rig, run_root)
            self.assertEqual(code, pc_exitcodes.USAGE, body + text)
            self.assertIn("the run folder is not usable", text)

    def test_a_run_record_that_names_no_registered_row_is_unusable(self) -> None:
        rig = rig_for(ROW4A)
        run_root = self.chain(rig)
        record = read_json(os.path.join(run_root, "raw", "run.json"))
        record["row"] = "row0-not-registered"
        with open(os.path.join(run_root, "raw", "run.json"), "w", encoding="utf-8") as handle:
            json.dump(record, handle)
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, pc_exitcodes.USAGE, text)



class InvocationBudgetParserTests(unittest.TestCase):
    """--budget has its own parser; the per-call flag keeps the lower ceiling."""

    def test_well_formed_amounts_up_to_the_ceiling_are_accepted(self) -> None:
        self.assertEqual(pc_flags.INVOCATION_BUDGET_MAX, Decimal("25.00"))
        self.assertIsInstance(pc_flags.INVOCATION_BUDGET_MAX, Decimal)
        for text, expected in (("25.00", "25.00"), ("25", "25.00"), ("2.5", "2.50"), ("0.01", "0.01"), ("12.34", "12.34")):
            self.assertEqual(pc_flags.format_invocation_budget(text), expected)
        self.assertEqual(pc_flags.format_invocation_budget(Decimal("7.00")), "7.00")

    def test_everything_else_is_refused(self) -> None:
        for bad in (
            "25.01",
            "26",
            "0",
            "0.00",
            "2.005",
            "1e1",
            "2,5",
            "",
            "-1",
            "NaN",
            " 2",
            "2 ",
            ".5",
            "2.",
            "٢.00",
            2.5,
            2,
            True,
            None,
            Decimal("2.005"),
            Decimal("NaN"),
            Decimal("26"),
        ):
            with self.assertRaises(ValueError, msg=repr(bad)):
                pc_flags.format_invocation_budget(bad)

    def test_the_per_call_budget_keeps_its_own_ceiling(self) -> None:
        self.assertEqual(pc_flags.format_budget("5.00"), "5.00")
        for bad in ("5.01", "25.00", "7"):
            with self.assertRaises(ValueError):
                pc_flags.format_budget(bad)


class WorstCaseTests(unittest.TestCase):
    """The worst case of a row is the smaller of the cap sum and the row cap, and the ledger enforces that bound."""

    def four_stage_row(self):
        return injected("row0-four", caps=("0.30", "1.30", "0.40", "0.60"))

    def test_a_four_stage_row_reports_2_00_and_a_two_stage_row_its_cap_sum(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.worst_case(self.four_stage_row()), Decimal("2.00"))
        self.assertEqual(pc_rows.worst_case(injected("row0-two", caps=("0.30", "1.30"))), Decimal("1.60"))
        self.assertEqual(pc_rows.worst_case(injected("row0-one", caps=("0.10",))), Decimal("0.10"))
        self.assertIsInstance(pc_rows.worst_case(self.four_stage_row()), Decimal)

    def test_the_dry_run_prints_2_00_for_it_and_a_total_that_uses_the_bounded_figure(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        registry = registry_of(self.four_stage_row())
        code, out, err = drive(rig, ["--dry-run", "--row", "row0-four"], registry, claude=False)
        self.assertEqual(code, 0, out + err)
        self.assertIn("worst case 2.00 USD", out)

    def test_the_ledger_refuses_the_launch_that_would_take_the_row_past_2_00(self) -> None:
        home = os.path.join(scratch(), "hh")
        keys = tuple("row0-s%d" % number for number in range(1, 5))
        caps = (Decimal("0.30"), Decimal("1.30"), Decimal("0.40"), Decimal("0.60"))
        deltas = (Decimal("0.30"), Decimal("0.80"), Decimal("0.30"))  # settled 1.40 after three stages
        for index in range(3):
            attempt = pc_spend.append_launch(home, "row0-four", keys[index], caps[index], "2.1.310", keys)
            pc_spend.settle(home, "row0-four", keys[index], attempt, "success", deltas[index], None, "2.1.310")
        self.assertEqual(pc_spend.row_pessimistic_total(home, "row0-four"), Decimal("1.40"))
        pc_spend.append_launch(home, "row0-four", keys[3], caps[3], "2.1.310", keys)  # 1.40 + 0.60 is exactly 2.00

        other = os.path.join(scratch(), "hh")
        more = (Decimal("0.30"), Decimal("0.80"), Decimal("0.40"))  # settled 1.50 after three stages
        for index in range(3):
            attempt = pc_spend.append_launch(other, "row0-four", keys[index], caps[index], "2.1.310", keys)
            pc_spend.settle(other, "row0-four", keys[index], attempt, "success", more[index], None, "2.1.310")
        with self.assertRaises(pc_spend.SpendRefused):
            pc_spend.append_launch(other, "row0-four", keys[3], caps[3], "2.1.310", keys)


class BudgetTests(unittest.TestCase):
    """The per-invocation budget: its minimum, its ceiling and the stop before a row that would pass it."""

    def setUp(self) -> None:
        self.rig = pc_testutil.RowRig(stages=[])
        self.rec = Recorder()

    def spending(self, row_id, spent, worst=("1.00", "1.00"), code=0):
        runner = self.rec.runner(row_id, code=code, spent=Decimal(spent) if spent is not None else None)
        return injected(row_id, caps=worst, runner=runner)

    def real(self, entries, budget, extra=()):
        args = []
        for entry in entries:
            args += ["--row", entry.row_id]
        code, out, err = drive(self.rig, args + ["--budget", budget] + list(extra), registry_of(*entries))
        assert_clean(self, self.rig, out + err)
        return code, out, err

    def test_a_one_row_budget_equal_to_the_worst_case_is_accepted_and_one_cent_less_is_refused(self) -> None:
        entry = self.spending("row0-a", "0.30")
        for budget, expected in (("2.00", 0), ("2.01", 0), ("1.99", 18), ("1.00", 18)):
            self.rig = pc_testutil.RowRig(stages=[])
            self.rec.calls.clear()
            dry = drive(self.rig, ["--dry-run", "--row", "row0-a", "--budget", budget], registry_of(entry), claude=False)
            self.assertEqual(dry[0], expected, budget + dry[1] + dry[2])
            code, out, err = self.real([entry], budget)
            self.assertEqual(code, expected, budget + out + err)
            self.assertEqual(len(self.rec.calls), 1 if expected == 0 else 0)

    def test_a_multi_row_selection_needs_only_the_largest_single_worst_case(self) -> None:
        entries = [self.spending("row0-a", "0.30"), self.spending("row0-b", "0.30"), self.spending("row0-c", "0.30")]
        code, out, err = self.real(entries[:1], "2.00")
        self.assertEqual(code, 0, out + err)
        dry = drive(
            self.rig,
            ["--dry-run", "--row", "row0-a", "--row", "row0-b", "--row", "row0-c", "--budget", "2.00"],
            registry_of(*entries),
            claude=False,
        )
        self.assertEqual(dry[0], 0, dry[1] + dry[2])
        self.assertIn("budget 2.00 USD for this invocation", dry[1])
        short = drive(
            self.rig,
            ["--dry-run", "--row", "row0-a", "--row", "row0-b", "--row", "row0-c", "--budget", "1.99"],
            registry_of(*entries),
            claude=False,
        )
        self.assertEqual(short[0], pc_exitcodes.BUDGET_REFUSED)
        self.assertNotIn("budget 1.99", short[1])

    def test_the_minimum_is_the_largest_single_row_not_the_first_or_the_sum(self) -> None:
        small = injected("row0-small", caps=("0.10",), runner=self.rec.runner("row0-small"))
        big = injected("row0-big", caps=("0.90", "0.90"), runner=self.rec.runner("row0-big"))
        args = ["--dry-run", "--row", "row0-small", "--row", "row0-big"]
        self.assertEqual(drive(self.rig, args + ["--budget", "1.80"], registry_of(small, big), claude=False)[0], 0)
        self.assertEqual(
            drive(self.rig, args + ["--budget", "1.79"], registry_of(small, big), claude=False)[0],
            pc_exitcodes.BUDGET_REFUSED,
        )

    def test_the_ceiling_is_25_00_and_every_other_shape_is_refused_without_an_echo(self) -> None:
        entry = self.spending("row0-a", "0.30")
        ok = drive(self.rig, ["--dry-run", "--row", "row0-a", "--budget", "25.00"], registry_of(entry), claude=False)
        self.assertEqual(ok[0], 0, ok[1] + ok[2])
        for bad in ("25.01", "30", "2.005", "1e1", "2,5", "zz-probe-text", "", "0", "-2"):
            code, out, err = drive(
                self.rig, ["--dry-run", "--row", "row0-a", "--budget", bad], registry_of(entry), claude=False
            )
            self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, repr(bad))
            self.assertNotIn("probe", out + err)
            self.assertIn("worst case 2.00", out, "the plan was printed first")

    def test_rows_that_spend_little_all_run_under_a_budget_that_covers_the_running_total(self) -> None:
        entries = [self.spending("row0-a", "0.30"), self.spending("row0-b", "0.30"), self.spending("row0-c", "0.30")]
        code, out, err = self.real(entries, "2.60")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a", "row0-b", "row0-c"])
        self.assertIn("row row0-c: filed, exit 0, spent 0.30 USD", out)
        self.assertIn("summary: 3 row(s) selected, 3 filed, 0 stopped, 0 skipped, 0 refused, 0 not started", out)

    def test_the_third_row_is_not_started_when_the_running_total_plus_its_worst_case_passes_the_budget(self) -> None:
        entries = [self.spending("row0-a", "0.30"), self.spending("row0-b", "0.30"), self.spending("row0-c", "0.30")]
        code, out, err = self.real(entries, "2.59")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a", "row0-b"], "0.60 plus 2.00 is above 2.59")
        self.assertIn(matrix().MESSAGE_BUDGET_STOP, err)
        self.assertIn("summary: 3 row(s) selected, 2 filed, 0 stopped, 0 skipped, 0 refused, 1 not started", out)

    def test_a_tighter_budget_stops_before_the_second_row_and_keeps_the_first_filed(self) -> None:
        entries = [self.spending("row0-a", "0.30"), self.spending("row0-b", "0.30"), self.spending("row0-c", "0.30")]
        code, out, err = self.real(entries, "2.29")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a"], "0.30 plus 2.00 is above 2.29")
        self.assertIn("row row0-a: filed, exit 0, spent 0.30 USD", out)
        self.assertIn("summary: 3 row(s) selected, 1 filed, 0 stopped, 0 skipped, 0 refused, 2 not started", out)

    def test_the_stop_uses_exact_decimal_arithmetic(self) -> None:
        entries = [
            self.spending("row0-a", "0.10", worst=("0.10", "0.10", "0.10")),
            self.spending("row0-b", "0.10", worst=("0.10", "0.10", "0.10")),
            self.spending("row0-c", "0.10", worst=("0.10", "0.10", "0.10")),
        ]
        code, out, err = self.real(entries, "0.50")
        self.assertEqual(code, 0, "0.20 plus 0.30 is exactly 0.50, with no float residue: " + out + err)
        self.rec.calls.clear()
        self.rig = pc_testutil.RowRig(stages=[])
        code, out, err = self.real(entries, "0.49")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a", "row0-b"])

    def test_a_stopped_row_still_counts_what_it_spent(self) -> None:
        entries = [
            self.spending("row0-a", "1.50", code=11),
            self.spending("row0-b", "0.10", worst=("1.00",)),
        ]
        code, out, err = self.real(entries, "2.40")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(self.rec.ids(), ["row0-a"], "1.50 plus 1.00 is above 2.40")
        self.assertIn("row row0-a: stopped, exit 11, spent 1.50 USD", out)
        self.assertIn("1 stopped", out)

    def test_a_skipped_row_costs_nothing_and_is_never_stopped_by_the_budget(self) -> None:
        entries = [
            self.spending("row0-a", "1.90", worst=("1.00", "1.00")),
            injected("row0-b", caps=("1.00", "1.00"), precondition=lambda: "the fixture of this test row is absent"),
        ]
        code, out, err = self.real(entries, "2.00")
        self.assertEqual(code, 10, out + err)
        self.assertIn("row row0-b: skipped, exit 10, spent 0.00 USD", out)
        self.assertNotIn(matrix().MESSAGE_BUDGET_STOP, err)

    def test_a_runner_that_reports_nothing_is_read_from_the_ledger(self) -> None:
        def runner(ctx):
            home = ctx.harness_home
            row = rows().scoped_row("row0-a", ctx.campaign, ctx.attempt, ctx.matrix)
            keys = ("row0-s1",)
            attempt = pc_spend.append_launch(home, row, keys[0], Decimal("1.00"), "2.1.310", keys)
            pc_spend.settle(home, row, keys[0], attempt, "success", Decimal("1.20"), Decimal("1.20"), "2.1.310")
            return rows().RowOutcome(0, ("scripted from the ledger",))

        first = injected("row0-a", caps=("1.00", "1.00"), runner=runner)
        second = self.spending("row0-b", "0.10", worst=("1.30",))
        code, out, err = self.real([first, second], "2.40")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertIn("row row0-a: filed, exit 0, spent 1.20 USD", out)
        self.assertEqual(self.rec.calls, [], "1.20 plus 1.30 is above 2.40")

    def test_a_runner_that_raises_counts_the_ledger_total_and_its_code_is_mapped(self) -> None:
        def runner(ctx):
            raise pc_spend.SpendRefused("probe-zz")

        entry = injected("row0-a", caps=("1.00", "1.00"), runner=runner)
        code, out, err = self.real([entry], "2.00")
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertNotIn("probe", out + err)
        self.assertIn("refused, exit 18", out)

    def test_the_budget_is_the_run_context_budget(self) -> None:
        seen = []

        def runner(ctx):
            seen.append(ctx.budget)
            return rows().RowOutcome(0, ("scripted",))

        entry = injected("row0-a", runner=runner)
        code, out, err = self.real([entry], "7.50")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(seen, [Decimal("7.50")])


class PlanLineTests(unittest.TestCase):
    """The plan prints each row's own allowlist size."""

    def test_every_row_prints_the_size_of_its_own_profile(self) -> None:
        import pc_row1

        pc_rows = rows()
        for row_id in (ROW1, ROW4A):
            entry = spec_of(row_id)
            lines = matrix().plan_lines(entry, "2026-10-28")
            size = len(pc_row1.allowed_tools(entry.tools_profile, matrix().ALLOWLIST_ROLE_WRAPPER))
            self.assertIn("allowlist %d rules" % size, lines)
        self.assertEqual(pc_rows.PROFILE_HELPER, spec_of(ROW1).tools_profile)

    def test_a_row_with_another_profile_prints_that_profile_not_a_shared_figure(self) -> None:
        odd = injected("row0-odd")._replace(tools_profile="no-such-profile")
        lines = matrix().plan_lines(odd, "2026-10-28")
        self.assertIn("allowlist unknown profile", lines)
        self.assertNotIn("allowlist 40 rules", lines)

    def test_the_plan_for_two_rows_prints_one_allowlist_line_each(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        code, out, err = drive(rig, ["--dry-run", "--row", ROW1, "--row", ROW4A], claude=False)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.count("allowlist "), 2)
        self.assertIn("total: 2 row(s), 5 stage(s), 3 session(s), worst case 3.60 USD", out)


if __name__ == "__main__":
    unittest.main()
