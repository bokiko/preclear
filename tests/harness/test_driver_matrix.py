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
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id)
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


if __name__ == "__main__":
    unittest.main()
