"""Zero-token tests for stopped rows and the top-level files of a dated folder (plan 04-03; RERUN-03; D-02, D-03).

A row that stops after its run root exists is filed as a STOPPED label folder with its reason, its usage and the
traces of the stages that ran; promote_into adds a flat file to an existing evidence folder without ever
overwriting; close and report summarise a dated folder. No test starts a real claude: the only claude executed is
the scripted fake written by pc_testutil. Every folder comes from RowRig or tempfile and is never deleted. Modules
are imported inside small accessors, so a missing module is one error per test and not one load failure of the
file. Leak-shaped strings come only from pc_seeds, and the verdict words are assembled from fragments.
"""
from __future__ import annotations

import io
import json
import os
import re
import unittest

import pc_exitcodes
import pc_seeds
import pc_testutil

ROW1 = "row1-wrong-binding"
ROW4A = "row4a-unknown-backend"
VERDICT_LINE = "Reviewer verdict: PENDING"
DATED = "rerun-2026-10-28-claude-sonnet-5-5"
FILED_LINE = re.compile(r"^filed: [a-z0-9.-]+/STOPPED-[a-z0-9-]+, [0-9]+ file\(s\)$")
RAW_NAMES = re.compile(r"(\.stdout$|\.record\.json$|\.guard\.json$|\.git\.json$|^run\.json$|^settings\.json$|^session|^snap-)")


def evidence():
    import pc_evidence

    return pc_evidence


def row1():
    import pc_row1

    return pc_row1


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def spec_of(row_id: str):
    pc_rows = rows()
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id)
    assert entry is not None, row_id
    return entry


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def verdict_pattern():
    return evidence().verdict_pattern()


def with_result(stages: list, index: int, **changes) -> list:
    copied = json.loads(json.dumps(stages))
    copied[index]["result"].update(changes)
    return copied


def default_stages() -> list:
    return pc_testutil.default_row1_stages()


class Stopped(object):
    """A rig, a context and the outcome of one run_row call whose chain was scripted to stop."""

    def __init__(self, stages, timeout_override=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.ctx = self.rig.context()
        self.outcome = row1().run_row(self.ctx, timeout_override=timeout_override)

    @property
    def run_root(self) -> str:
        names = os.listdir(self.ctx.runs_root)
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    @property
    def dated(self) -> str:
        return self.ctx.destination

    @property
    def label(self) -> str:
        return os.path.join(self.dated, "STOPPED-" + ROW1)

    def read(self, name: str) -> str:
        return read_text(os.path.join(self.label, name))

    @property
    def text(self) -> str:
        return "\n".join(self.outcome.lines)


class StoppedFilingTests(unittest.TestCase):
    """Every stop after the run root exists is filed as STOPPED-<row folder> and keeps its own exit code."""

    def check_label(self, run: Stopped, reason: str, stage: str, code: int, ran: int) -> None:
        text = run.text
        self.assertEqual(run.outcome.code, code, text)
        self.assertRegex(run.outcome.lines[-1], FILED_LINE, "the last printed line is the filed line")
        self.assertEqual(sum(1 for line in run.outcome.lines if line.startswith("filed: ")), 1, "one filed line")
        self.assertNotIn(run.rig.base, text, "no path in the printed lines")
        self.assertNotIn("nothing was filed", text, "the old closing text is gone")
        self.assertEqual(os.listdir(run.dated), ["STOPPED-" + ROW1], "no row folder, one label folder")
        names = sorted(os.listdir(run.label))
        self.assertTrue({"README.md", "stop.txt", "usage.txt", "mechanical-checks.md"} <= set(names), names)
        for name in names:
            self.assertTrue(os.path.isfile(os.path.join(run.label, name)), name + ": flat, a file")
            self.assertIsNone(RAW_NAMES.search(name), name + ": no raw capture, settings, session id or snapshot")
        stop = run.read("stop.txt")
        self.assertIn("\nreason: %s\n" % reason, stop)
        self.assertIn("\nstage: %s\n" % stage, stop)
        self.assertIn("\nexit code: %d\n" % code, stop)
        self.assertIn("\ncounts: stages run %d of 3" % ran, stop)
        readme = run.read("README.md")
        self.assertTrue(readme.startswith("# STOPPED: %s\n" % ROW1), "the heading")
        self.assertIn("\nRow: %s\nReason: %s\nStage: %s\n" % (ROW1, reason, stage), readme)
        self.assertIn("is a label for a run that did not finish", readme)
        self.assertIn("It is not a result", readme)
        self.assertTrue(readme.endswith("\n" + VERDICT_LINE + "\n"), "the exact closing line")
        usage = run.read("usage.txt")
        self.assertEqual(len(re.findall(r"^stage s[0-9]: ", usage, re.M)), ran, "one usage line per stage that ran")
        self.assertIn("row total: UNCONFIRMED, the chain did not finish", usage, "the row total is unknown")
        pattern = verdict_pattern()
        for name in ("stop.txt", "usage.txt", "mechanical-checks.md"):
            self.assertIsNone(pattern.search(run.read(name)), name + ": no verdict word")
        self.assertIsNone(pattern.search(readme[: -len(VERDICT_LINE) - 1]), "no verdict word before the closing line")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s%d.stdout" % ran)), "the raw bytes stay in the run root")
        self.assertEqual(len(run.rig.calls()), ran, "no later stage was launched")

    def test_a_turn_limit_in_s2_files_a_label_with_reason_turns_and_keeps_exit_11(self) -> None:
        run = Stopped(with_result(default_stages(), 1, subtype="error_max_turns"))
        self.check_label(run, "turns", "s2", pc_exitcodes.PREFLIGHT_FAIL, 2)
        self.assertIn("\nresult subtype: error_max_turns\n", run.read("stop.txt"))
        names = os.listdir(run.label)
        for expected in ("s1.exit", "s1.err", "s1-work-prompt.md", "s1-work-full-trace.md", "s2-preclear.exit",
                         "s2-preclear-prompt.md", "s2-preclear-trace.md", "s2-preclear-full-trace.md"):
            self.assertIn(expected, names)
        self.assertFalse(any(name.startswith("s3") for name in names), "no file of a stage that did not run")
        self.assertNotIn("s1-work.out", names, "no reply file")
        self.assertIn("partial total: ", run.read("usage.txt"))

    def test_a_budget_limit_files_a_label_with_reason_cap(self) -> None:
        run = Stopped(with_result(default_stages(), 1, subtype="error_max_budget_usd"))
        self.check_label(run, "cap", "s2", pc_exitcodes.PREFLIGHT_FAIL, 2)

    def test_a_subtype_that_is_neither_limit_is_error_and_the_subtype_text_is_recorded(self) -> None:
        run = Stopped(with_result(default_stages(), 1, subtype="error_during_execution"))
        self.check_label(run, "error", "s2", pc_exitcodes.PREFLIGHT_FAIL, 2)
        self.assertIn("\nresult subtype: error_during_execution\n", run.read("stop.txt"))
        again = Stopped(with_result(default_stages(), 1, is_error=True))
        self.check_label(again, "error", "s2", pc_exitcodes.PREFLIGHT_FAIL, 2)

    def test_a_non_zero_exit_with_no_limit_subtype_is_exit(self) -> None:
        run = Stopped(pc_testutil.stages_with(default_stages(), 0, exit=1))
        self.check_label(run, "exit", "s1", pc_exitcodes.PREFLIGHT_FAIL, 1)

    def test_a_timeout_files_a_label_with_reason_timeout(self) -> None:
        stages = pc_testutil.stages_with(
            default_stages(), 0, ops=[{"op": "init"}, {"op": "text", "text": "partial"}, {"op": "sleep", "seconds": 20}]
        )
        run = Stopped(stages, timeout_override=3)
        self.check_label(run, "timeout", "s1", pc_exitcodes.PREFLIGHT_FAIL, 1)

    def test_a_stream_with_no_result_files_a_label_with_reason_stream_and_keeps_exit_19(self) -> None:
        run = Stopped(pc_testutil.stages_with(default_stages(), 0, no_result=True))
        self.check_label(run, "stream", "s1", pc_exitcodes.DENIAL_FOUND, 1)
        names = os.listdir(run.label)
        self.assertFalse(any(name.endswith("trace.md") for name in names), "no trace for an unreadable stream")
        self.assertIn("s1.exit", names)

    def test_a_failing_isolation_assertion_files_a_label_with_reason_isolation(self) -> None:
        run = Stopped(pc_testutil.stages_with(default_stages(), 0, init={"model": "some-other-model"}))
        self.check_label(run, "isolation", "s1", pc_exitcodes.PREFLIGHT_FAIL, 1)

    def test_a_seeded_write_outside_the_run_root_files_a_label_with_reason_breach(self) -> None:
        run = Stopped(pc_testutil.seed_outside_write(default_stages(), 1))
        self.check_label(run, "breach", "s2", pc_exitcodes.PREFLIGHT_FAIL, 2)
        stop = run.read("stop.txt")
        self.assertRegex(stop, r"\nbreach writes-outside-approved-roots: [1-9][0-9]*\n", "the breach counts are in stop.txt")
        self.assertNotIn("outside.txt", stop, "no path in stop.txt")
        self.assertRegex(run.text, r"isolation or git breach: writes outside approved roots: [1-9]")
        self.assertIn("the raw files and snapshots stay in the run root", run.text)

    def test_a_run_record_tamper_files_a_label_with_reason_breach(self) -> None:
        run = Stopped(pc_testutil.seed_run_record_tamper(default_stages(), "extra"))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, run.text)
        self.assertRegex(run.outcome.lines[-1], FILED_LINE)
        self.assertIn("\nreason: breach\n", run.read("stop.txt"))

    def test_a_leak_shaped_string_in_a_stopped_stage_is_refused_with_14_and_nothing_is_filed(self) -> None:
        seeded = pc_seeds.home_path("pcsynthhome") + "/data"
        stages = pc_testutil.stages_with(default_stages(), 0, exit=1, stderr="the folder " + seeded + " is missing\n")
        run = Stopped(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.LEAK_REFUSED, run.text)
        self.assertFalse(os.path.lexists(run.dated), "nothing was created in the evidence tree")
        self.assertNotIn(seeded, run.text, "the seeded text is never printed")
        self.assertRegex(run.text, r"[0-9]+ finding")
        self.assertTrue(os.path.isfile(os.path.join(run.run_root, "raw", "s1.stderr")), "the raw error text stays")

    def test_an_existing_label_folder_is_refused_with_17_and_left_as_it_was(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.stages_with(default_stages(), 0, exit=1))
        ctx = rig.context()
        taken = os.path.join(ctx.destination, "STOPPED-" + ROW1)
        os.makedirs(taken)
        outcome = row1().run_row(ctx)
        self.assertEqual(outcome.code, pc_exitcodes.PROMOTE_REFUSED, "\n".join(outcome.lines))
        self.assertEqual(os.listdir(taken), [], "the existing folder was not written into")

    def test_the_stop_reason_mapping(self) -> None:
        ev = evidence()
        cases = (
            (("subtype", "error_max_turns"), "turns"),
            (("exit", "error_max_turns"), "turns"),
            (("subtype", "error_max_budget_usd"), "cap"),
            (("subtype", "error_during_execution"), "error"),
            (("subtype", "something new"), "error"),
            (("is-error", "success"), "error"),
            (("terminal", "success"), "error"),
            (("exit", ""), "exit"),
            (("exit", None), "exit"),
            (("timeout", ""), "timeout"),
            (("stream", ""), "stream"),
            (("isolation", "success"), "isolation"),
            (("breach", "success"), "breach"),
        )
        for (problem, subtype), expected in cases:
            self.assertEqual(ev.stop_reason(problem, subtype), expected, "%s %r" % (problem, subtype))
        self.assertEqual(ev.stop_exit_code("stream"), pc_exitcodes.DENIAL_FOUND)
        for reason in ev.STOP_REASONS:
            if reason != "stream":
                self.assertEqual(ev.stop_exit_code(reason), pc_exitcodes.PREFLIGHT_FAIL, reason)

    def test_an_unknown_reason_or_a_missing_deny_list_files_nothing(self) -> None:
        run = Stopped(pc_testutil.stages_with(default_stages(), 0, exit=1))
        ev = evidence()
        entry = spec_of(ROW1)
        shelf = os.path.join(run.rig.repo, "tests", "evidence", "other-dated")
        ctx = run.ctx._replace(destination=shelf, run_root=run.run_root)
        for reason in ("bogus", "", "STOPPED"):
            odd = ev.file_stopped(ctx, run.run_root, entry, reason, "s1")
            self.assertEqual(odd.code, pc_exitcodes.PREFLIGHT_FAIL, reason)
        refused = ev.file_stopped(ctx, run.run_root, entry, "turns", "s1")
        self.assertEqual(refused.code, pc_exitcodes.SCANNER_ERROR, "no sanitizer and no deny entries")
        self.assertFalse(os.path.lexists(shelf), "nothing was created")

    def test_a_stop_in_the_first_row_of_two_leaves_the_second_row_running(self) -> None:
        stages = [pc_testutil.stages_with(default_stages(), 0, exit=1)[0]]
        stages += pc_testutil.default_row_stages(spec_of(ROW4A))
        rig = pc_testutil.RowRig(stages=stages)
        out = io.StringIO()
        err = io.StringIO()
        import datetime

        def clock():
            return datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)

        code = matrix().main(
            ["--row", ROW1, "--row", ROW4A, "--claude", rig.claude, "--budget", "5.00"],
            env=dict(rig.env), repo_root=rig.repo, clock=clock, out=out, err=err,
        )
        text = out.getvalue() + err.getvalue()
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, text)
        dated = os.path.join(rig.repo, "tests", "evidence", DATED)
        self.assertEqual(sorted(os.listdir(dated)), ["STOPPED-" + ROW1, ROW4A], "both folders are present")
        self.assertIn("filed: %s/STOPPED-%s" % (DATED, ROW1), text)
        self.assertIn("1 stopped", text)
        self.assertNotIn(rig.base, text)


if __name__ == "__main__":
    unittest.main()
