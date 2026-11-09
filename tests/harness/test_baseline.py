"""Zero-token tests for stopped rows and the top-level files of a dated folder (plan 04-03; RERUN-03; D-02, D-03).

A row that stops after its run root exists is filed as a STOPPED label folder with its reason, its usage and the
traces of the stages that ran; promote_into adds a flat file to an existing evidence folder without ever
overwriting; close and report summarise a dated folder. No test starts a real claude: the only claude executed is
the scripted fake written by pc_testutil. Every folder comes from RowRig or tempfile and is never deleted. Modules
are imported inside small accessors, so a missing module is one error per test and not one load failure of the
file. Leak-shaped strings come only from pc_seeds, and the verdict words are assembled from fragments.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import unittest
from decimal import Decimal
from unittest import mock

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
        self.assertIn("\ncounts: stage records %d of 3" % ran, stop)
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



# ---------------------------------------------------------------------------------------------
# The dated folder: a filed row, a STOPPED label and a SKIPPED label built through the real filing path
# ---------------------------------------------------------------------------------------------

_WORLD = {}
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def fixed_clock():
    return FIXED_DATE


def baseline():
    import pc_baseline

    return pc_baseline


def drive_matrix(rig, args, registry=None):
    out = io.StringIO()
    err = io.StringIO()
    kwargs = {} if registry is None else {"registry": registry}
    code = matrix().main(
        list(args) + ["--claude", rig.claude, "--budget", "5.00"],
        env=dict(rig.env), repo_root=rig.repo, clock=fixed_clock, out=out, err=err, **kwargs,
    )
    return code, out.getvalue() + err.getvalue()


class World(object):
    """A scratch repository whose dated folder holds, from three driver invocations of scripted rows: row 1 filed,
    row 4a STOPPED (attempt 1), row 4a filed (attempt 2) and row 4a SKIPPED through a precondition (attempt 3)."""

    def __init__(self) -> None:
        spec4a = spec_of(ROW4A)
        stages = pc_testutil.default_row1_stages()
        stages += pc_testutil.stages_with(pc_testutil.default_row_stages(spec4a), 0, exit=1)[:1]
        stages += pc_testutil.default_row_stages(spec4a)
        self.rig = pc_testutil.RowRig(stages=stages)
        self.codes = []
        code, text = drive_matrix(self.rig, ["--row", ROW1, "--row", ROW4A])
        self.codes.append(code)
        code, text2 = drive_matrix(self.rig, ["--row", ROW4A, "--attempt", "2"])
        self.codes.append(code)
        entries = tuple(
            entry._replace(precondition=lambda: "the fixture of this test row is absent") if entry.row_id == ROW4A else entry
            for entry in rows().build_registry()
        )
        code, text3 = drive_matrix(self.rig, ["--row", ROW4A, "--attempt", "3"], registry=entries)
        self.codes.append(code)
        self.text = "\n".join([text, text2, text3])

    @property
    def dated(self) -> str:
        return os.path.join(self.rig.repo, "tests", "evidence", DATED)

    def relative(self) -> str:
        return os.path.join("tests", "evidence", DATED)

    def read(self, *parts: str) -> str:
        return read_text(os.path.join(self.dated, *parts))


def world() -> "World":
    if "world" not in _WORLD:
        _WORLD["world"] = World()
    return _WORLD["world"]


def fresh_copy_of_world() -> "World":
    """A new scratch repository with a copy of the shared world's dated folder, for tests that write into it."""
    import shutil

    source = world()
    copy = World.__new__(World)
    copy.rig = pc_testutil.RowRig(stages=[])
    copy.codes = list(source.codes)
    copy.text = source.text
    shutil.copytree(source.dated, copy.dated)
    return copy


def run_baseline(rig, args, env_extra=None):
    out = io.StringIO()
    err = io.StringIO()
    env = dict(rig.env)
    env.update(env_extra or {})
    code = baseline().main(list(args), env=env, repo_root=rig.repo, clock=fixed_clock, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def tree_snapshot(folder: str) -> dict:
    found = {}
    for dirpath, _dirnames, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, folder)] = handle.read()
    return found


def make_item_folder(rig, name, files, dated="rerun-2026-10-30-model-x"):
    """A hand-made dated folder holding one folder of the given files, for the strict-pattern tests."""
    folder = os.path.join(rig.repo, "tests", "evidence", dated)
    os.makedirs(os.path.join(folder, name), exist_ok=True)
    for file_name, text in files.items():
        with open(os.path.join(folder, name, file_name), "xb") as handle:
            handle.write(text.encode("utf-8"))
    return folder


def digest_lines(skill="a", adapter="b", stub="c", wrapper="d"):
    names = (
        (skill, "<run>/project/.claude/skills/preclear/SKILL.md"),
        (adapter, "<run>/project/.claude/skills/preclear/references/checkpoint-v1.md"),
        (stub, "tests/harness/checkpoint_stub.py"),
        (wrapper, "<run>/wrapper/checkpoint"),
    )
    return "".join("%s  %s\n" % ((sha * 64) if len(sha) == 1 else sha, name) for sha, name in names)


class WorldTests(unittest.TestCase):
    def test_the_world_was_built_through_the_driver_with_the_expected_exit_codes(self) -> None:
        w = world()
        self.assertEqual(w.codes, [pc_exitcodes.PREFLIGHT_FAIL, 0, pc_exitcodes.PREFLIGHT_SKIP], w.text)
        self.assertEqual(
            sorted(os.listdir(w.dated)),
            ["SKIPPED-row4a-unknown-backend-attempt-3", "STOPPED-row4a-unknown-backend", ROW1,
             "row4a-unknown-backend-attempt-2"],
        )


class DigestTableTests(unittest.TestCase):
    def items(self):
        return baseline().read_items(world().dated)

    def test_the_order_is_the_registry_order_then_the_attempt_with_a_label_after_its_own_folder(self) -> None:
        names = [item.folder for item in self.items()]
        self.assertEqual(
            names,
            [ROW1, "STOPPED-row4a-unknown-backend", "row4a-unknown-backend-attempt-2",
             "SKIPPED-row4a-unknown-backend-attempt-3"],
        )
        self.assertEqual([item.state for item in self.items()], ["filed", "STOPPED", "filed", "SKIPPED"])
        self.assertEqual([item.attempt for item in self.items()], [1, 1, 2, 3])

    def test_layouts_come_first_and_a_label_sits_directly_after_the_folder_it_labels(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        folder = make_item_folder(rig, "row4a-unknown-backend", {})
        for name in ("row1-wrong-binding", "hub-memory", "plain-memory", "STOPPED-row1-wrong-binding",
                     "SKIPPED-hub-memory", "row1-wrong-binding-attempt-2", "zzz-not-a-row"):
            os.makedirs(os.path.join(folder, name))
        names = [item.folder for item in baseline().read_items(folder)]
        self.assertEqual(
            names,
            ["plain-memory", "hub-memory", "SKIPPED-hub-memory", "row1-wrong-binding", "STOPPED-row1-wrong-binding",
             "row1-wrong-binding-attempt-2", "row4a-unknown-backend", "zzz-not-a-row"],
        )
        states = dict((item.folder, item.state) for item in baseline().read_items(folder))
        self.assertEqual(states["zzz-not-a-row"], "unrecognised")

    def test_each_row_line_quotes_the_files_it_was_read_from(self) -> None:
        w = world()
        filed = self.items()[0]
        usage = w.read(ROW1, "usage.txt")
        total = [line for line in usage.splitlines() if line.startswith("row total: ")][0][len("row total: "):]
        self.assertEqual(filed.cost, total, "the cost text is exactly the usage file's row total")
        digests = dict((line.split("  ", 1)[1], line.split("  ", 1)[0]) for line in w.read(ROW1, "digests.txt").splitlines())
        skill = [sha for name, sha in digests.items() if name.endswith("/preclear/SKILL.md")][0]
        adapter = [sha for name, sha in digests.items() if name.endswith("/references/checkpoint-v1.md")][0]
        stub = digests["tests/harness/checkpoint_stub.py"]
        wrapper = [sha for name, sha in digests.items() if name.endswith("/wrapper/checkpoint")][0]
        self.assertEqual((filed.skill, filed.adapter, filed.stub, filed.wrapper), (skill, adapter, stub, wrapper))
        for value in (filed.skill, filed.adapter, filed.stub, filed.wrapper):
            self.assertRegex(value, HEX64)
        table = baseline().render_digest_table(self.items(), 1)
        self.assertIn("| %s | filed | 1 | - | %s | %s | %s | %s | %s |" % (ROW1, skill, adapter, stub, wrapper, total), table)

    def test_a_stopped_label_shows_its_reason_and_its_partial_cost_and_a_skipped_label_its_reason_and_zero(self) -> None:
        w = world()
        table = baseline().render_digest_table(self.items(), 1)
        stopped = [line for line in table.splitlines() if line.startswith("| STOPPED-row4a")][0]
        self.assertIn("| STOPPED | 1 | exit at s1 |", stopped)
        partial = [line for line in w.read("STOPPED-row4a-unknown-backend", "usage.txt").splitlines()
                   if line.startswith("partial total: ")][0][len("partial total: "):]
        self.assertTrue(stopped.endswith("| %s |" % partial), stopped)
        skipped = [line for line in table.splitlines() if line.startswith("| SKIPPED-row4a")][0]
        self.assertIn("| SKIPPED | 3 | the fixture of this test row is absent |", skipped)
        self.assertTrue(skipped.endswith("| 0 |"), skipped)

    def test_the_total_is_the_exact_decimal_sum_and_counts_the_stopped_rows_partial_cost(self) -> None:
        w = world()
        parts = []
        for name, label in ((ROW1, "row total"), ("STOPPED-row4a-unknown-backend", "partial total"),
                            ("row4a-unknown-backend-attempt-2", "row total")):
            line = [x for x in w.read(name, "usage.txt").splitlines() if x.startswith(label + ": ")][0]
            parts.append(Decimal(line[len(label) + 2:]))
        expected = sum(parts, Decimal("0"))
        self.assertGreater(parts[1], 0, "the stopped row has a partial cost")
        table = baseline().render_digest_table(self.items(), 1)
        self.assertIn("total: %s USD from 4 cost value(s); 0 UNCONFIRMED" % format(expected, "f"), table)

    def test_costs_are_summed_with_exact_decimals_not_floats(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        folder = make_item_folder(rig, "row1-wrong-binding", {"digests.txt": digest_lines(), "usage.txt": "row total: 0.1\n"})
        make_item_folder(rig, "row2-double-conflict", {"digests.txt": digest_lines(), "usage.txt": "row total: 0.2\n"})
        make_item_folder(rig, "row3a-missing-executable",
                         {"digests.txt": digest_lines(), "usage.txt": "row total: 0.27231170000000002\n"})
        table = baseline().render_digest_table(baseline().read_items(folder), 1)
        self.assertIn("total: 0.57231170000000002 USD from 3 cost value(s); 0 UNCONFIRMED", table)
        self.assertIn("| 0.27231170000000002 |", table, "the long decimal is quoted as written")

    def test_an_empty_dated_folder_gives_a_header_and_rows_0(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        folder = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-30-model-x")
        os.makedirs(folder)
        table = baseline().render_digest_table(baseline().read_items(folder), 1)
        self.assertIn("rows: 0", table.splitlines())
        self.assertIn("| Folder | State | Attempt | Reason |", table)
        usage = baseline().render_usage_by_row([], 1)
        self.assertIn("rows: 0", usage.splitlines())
        code, out, err = run_baseline(rig, ["report", "--folder", folder])
        self.assertEqual(code, 0, err)
        self.assertIn("rows: 0", out)

    def test_a_value_that_is_not_a_64_hex_digest_or_a_plain_decimal_is_unconfirmed(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        bad_digests = digest_lines(skill="A" * 64, adapter="b" * 63, stub="UNCONFIRMED", wrapper="d")
        folder = make_item_folder(rig, "row1-wrong-binding", {"digests.txt": bad_digests, "usage.txt": "row total: 1e-3\n"})
        make_item_folder(rig, "row2-double-conflict", {"usage.txt": "row total: 0.5\nrow total: 0.6\n"})
        make_item_folder(rig, "row3a-missing-executable", {"digests.txt": digest_lines(), "usage.txt": "stage s1: nothing\n"})
        items = baseline().read_items(folder)
        first = items[0]
        self.assertEqual((first.skill, first.adapter, first.stub), ("UNCONFIRMED",) * 3, "upper case, short, and not a digest")
        self.assertEqual(first.wrapper, "d" * 64)
        self.assertEqual(first.cost, "UNCONFIRMED")
        self.assertEqual(items[1].cost, "UNCONFIRMED", "two row total lines are ambiguous")
        self.assertEqual(items[1].skill, "UNCONFIRMED", "no digests file")
        self.assertEqual(items[2].cost, "UNCONFIRMED", "no row total line")
        table = baseline().render_digest_table(items, 1)
        self.assertIn("total: 0 USD from 0 cost value(s); 3 UNCONFIRMED", table)

    def test_model_written_text_cannot_steer_the_table(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        folder = make_item_folder(
            rig, "STOPPED-row1-wrong-binding", {"stop.txt": "reason: turns | injected cell\nstage: s2\n", "usage.txt": "partial total: 0.01\n"}
        )
        make_item_folder(rig, "SKIPPED-row2-double-conflict",
                         {"README.md": "This row was skipped on this machine: a | b\nnewline. No session was run\n"})
        make_item_folder(rig, "STOPPED-row3a-missing-executable", {"stop.txt": "reason: turns\nstage: s2\n"})
        os.makedirs(os.path.join(folder, "evil|folder"))
        items = baseline().read_items(folder)
        by_folder = dict((item.folder, item) for item in items)
        self.assertEqual(by_folder["STOPPED-row1-wrong-binding"].reason, "UNCONFIRMED", "the reason is a known word or nothing")
        self.assertEqual(by_folder["SKIPPED-row2-double-conflict"].reason, "UNCONFIRMED")
        self.assertEqual(by_folder["STOPPED-row3a-missing-executable"].reason, "turns at s2")
        self.assertIn("evil?folder", by_folder, "a cell never holds a pipe")
        table = baseline().render_digest_table(items, 1)
        for line in table.splitlines():
            if line.startswith("| ") and not line.startswith("| ---") and not line.startswith("| Folder"):
                self.assertEqual(line.count("|"), 10, "one cell per column: " + line)

    def test_the_usage_table_lists_the_stage_lines_and_the_totals_as_the_files_hold_them(self) -> None:
        w = world()
        text = baseline().render_usage_by_row(self.items(), 1)
        self.assertIn("usage by row, part 1", text)
        self.assertIn("rows: 4", text.splitlines())
        for stage in ("s1", "s2", "s3"):
            self.assertIn("  stage %s: subtype success" % stage, text)
        self.assertIn("  no session was run; cost 0", text)
        self.assertIn("  partial total: ", text)
        total = [x for x in w.read(ROW1, "usage.txt").splitlines() if x.startswith("row total: ")][0]
        self.assertIn("  " + total, text)

    def test_every_line_is_free_of_the_vocabulary_and_of_paths(self) -> None:
        w = world()
        for text in (baseline().render_digest_table(self.items(), 1), baseline().render_usage_by_row(self.items(), 1),
                     baseline().render_folder_readme(w.dated, self.items(), False)):
            self.assertIsNone(verdict_pattern().search(text))
            self.assertNotIn(w.rig.base, text)

    def test_the_report_over_the_frozen_baseline_quotes_its_cost_and_writes_nothing(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        folder = os.path.join(root, "tests", "evidence", "rerun-2026-10-29-claude-sonnet-5-5")
        before = tree_snapshot(folder)
        out = io.StringIO()
        err = io.StringIO()
        code = baseline().main(["report", "--folder", folder], repo_root=root, out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        text = out.getvalue()
        self.assertIn("| row1-wrong-binding | filed | 1 | - |", text)
        self.assertIn("| 0.27231170000000002 |", text)
        self.assertIn("total: 0.27231170000000002 USD from 1 cost value(s); 0 UNCONFIRMED", text)
        self.assertEqual(tree_snapshot(folder), before, "nothing was written")
        for value in re.findall(r"\| ([0-9a-fA-FU][0-9a-fA-FN]*) \|", text):
            if len(value) == 64:
                self.assertRegex(value, HEX64)


class CloseTests(unittest.TestCase):
    def test_close_writes_the_readme_the_digest_table_and_the_usage_table(self) -> None:
        w = fresh_copy_of_world()
        before = tree_snapshot(w.dated)
        code, out, err = run_baseline(w.rig, ["close", "--folder", w.relative()])
        self.assertEqual(code, 0, out + err)
        self.assertIn("closed: %s, part 1, 3 file(s)" % DATED, out)
        after = tree_snapshot(w.dated)
        self.assertEqual(sorted(set(after) - set(before)), ["README.md", "digest-table.md", "usage-by-row.txt"])
        for name, data in before.items():
            self.assertEqual(after[name], data, name + " is untouched")
        self.assertNotIn(w.rig.base, out + err)
        self.assertIn("lists every row folder present", w.read("digest-table.md"))
        self.assertIn("every row folder present", w.read("usage-by-row.txt"))

    def test_a_second_close_writes_part_two_and_leaves_the_first_three_files_untouched(self) -> None:
        w = fresh_copy_of_world()
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        first = tree_snapshot(w.dated)
        code, out, err = run_baseline(w.rig, ["close", "--folder", w.relative()])
        self.assertEqual(code, 0, out + err)
        self.assertIn("part 2, 2 file(s)", out)
        self.assertIn("README.md: already present", out)
        second = tree_snapshot(w.dated)
        self.assertEqual(sorted(set(second) - set(first)), ["digest-table-part-2.md", "usage-by-row-part-2.txt"])
        for name, data in first.items():
            self.assertEqual(second[name], data, name + " is untouched")
        self.assertIn("digest table, part 2", w.read("digest-table-part-2.md").lower())
        code, out, err = run_baseline(w.rig, ["close", "--folder", w.relative()])
        self.assertEqual(code, 0, out + err)
        self.assertIn("part 3, 2 file(s)", out)
        third = tree_snapshot(w.dated)
        self.assertEqual(sorted(set(third) - set(second)), ["digest-table-part-3.md", "usage-by-row-part-3.txt"])

    def test_a_row_added_after_a_close_appears_in_the_next_part_only(self) -> None:
        w = fresh_copy_of_world()
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        os.makedirs(os.path.join(w.dated, "SKIPPED-row2-double-conflict"))
        with open(os.path.join(w.dated, "SKIPPED-row2-double-conflict", "README.md"), "xb") as handle:
            handle.write(b"# SKIPPED: row2-double-conflict\n\nThis row was skipped on this machine: a late skip. No session was run.\n")
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        self.assertNotIn("SKIPPED-row2-double-conflict", w.read("digest-table.md"))
        self.assertIn("SKIPPED-row2-double-conflict", w.read("digest-table-part-2.md"))
        self.assertIn("rows: 5", w.read("digest-table-part-2.md"))

    def test_the_readme_labels_an_attribution_run_by_default_and_a_new_baseline_with_the_flag(self) -> None:
        plain = fresh_copy_of_world()
        self.assertEqual(run_baseline(plain.rig, ["close", "--folder", plain.relative()])[0], 0)
        text = plain.read("README.md")
        self.assertIn("campaign attribution run", text)
        self.assertIn("not a baseline", text)
        self.assertIn("model claude-sonnet-5-5", text)
        self.assertIn("Claude Code 2.1.310", text)
        self.assertIn("4 (2 filed, 1 STOPPED, 1 SKIPPED, 0 unrecognised)", text)
        self.assertNotIn("replication of", text)
        flagged = fresh_copy_of_world()
        self.assertEqual(run_baseline(flagged.rig, ["close", "--folder", flagged.relative(), "--baseline"])[0], 0)
        text = flagged.read("README.md")
        self.assertIn("new baseline on the pinned model and Claude Code build", text)
        self.assertIn("model claude-sonnet-5-5, Claude Code 2.1.310", text)
        self.assertIn("not a replication", text)
        self.assertNotIn("campaign attribution run", text)
        for body in (text, plain.read("README.md")):
            self.assertIsNone(verdict_pattern().search(body), "no vocabulary word")

    def test_everything_close_files_is_clean_for_the_leak_gate(self) -> None:
        import pc_leakgate

        w = fresh_copy_of_world()
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        entries = pc_leakgate.collect_tree(w.dated)
        report = pc_leakgate.scan_entries(entries, [])
        self.assertEqual(list(report.findings), [], "no finding in the whole dated folder")

    def test_a_leak_shaped_reason_is_refused_with_14_and_nothing_is_written(self) -> None:
        w = fresh_copy_of_world()
        seeded = pc_seeds.home_path("pcsynthhome") + "/data"
        folder = os.path.join(w.dated, "SKIPPED-row2-double-conflict")
        os.makedirs(folder)
        with open(os.path.join(folder, "README.md"), "xb") as handle:
            handle.write(("# SKIPPED: row2-double-conflict\n\nThis row was skipped on this machine: the folder %s is missing. "
                          "No session was run.\n" % seeded).encode("utf-8"))
        before = tree_snapshot(w.dated)
        code, out, err = run_baseline(w.rig, ["close", "--folder", w.relative()])
        self.assertEqual(code, pc_exitcodes.LEAK_REFUSED, out + err)
        self.assertEqual(tree_snapshot(w.dated), before, "no file was created")
        self.assertNotIn(seeded, out + err)

    def test_close_refuses_a_target_that_is_not_a_dated_folder_of_the_evidence_tree(self) -> None:
        w = fresh_copy_of_world()
        link = os.path.join(w.rig.repo, "tests", "evidence", "rerun-linked")
        os.symlink(w.dated, link)
        os.makedirs(os.path.join(w.rig.repo, "tests", "evidence", "publication-2026-10-20"), exist_ok=True)
        os.makedirs(os.path.join(w.rig.repo, "tests", "other"))
        cases = [
            os.path.join("tests", "evidence"), os.path.join("tests", "other"), "..", w.rig.repo, os.path.join("tests", "evidence", "rerun-linked"),
            os.path.join("tests", "evidence", "rerun-missing"), os.path.join("tests", "evidence", "publication-2026-10-20"),
            os.path.join(w.relative(), ROW1), os.path.join("tests", "evidence", "..", "evidence", DATED), "", "a\x00b",
        ]
        before = tree_snapshot(w.dated)
        for case in cases:
            code, out, err = run_baseline(w.rig, ["close", "--folder", case])
            self.assertEqual(code, pc_exitcodes.USAGE, repr(case) + out + err)
            if case and "\x00" not in case:
                self.assertNotIn(case, out + err, "the value is not echoed")
        self.assertEqual(tree_snapshot(w.dated), before, "nothing was written")

    def test_close_is_never_pointed_at_the_frozen_folders(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for name in ("rerun-2026-10-29-claude-sonnet-5-5", "publication-2026-10-20"):
            folder = os.path.join(root, "tests", "evidence", name)
            before = tree_snapshot(folder)
            out = io.StringIO()
            err = io.StringIO()
            code = baseline().main(["close", "--folder", folder], repo_root=root, out=out, err=err)
            self.assertEqual(code, pc_exitcodes.USAGE, name)
            self.assertEqual(tree_snapshot(folder), before, name + " is unchanged")

    def test_the_command_line_refuses_unknown_words_and_a_missing_folder_with_2(self) -> None:
        rig = pc_testutil.RowRig(stages=[])
        for args in ([], ["other"], ["close"], ["report"], ["close", "--folder", "x", "--extra"], ["report", "--baseline", "--folder", "x"],
                     ["check-words", "--folder"]):
            code, out, err = run_baseline(rig, args)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(args))
        code, out, err = run_baseline(rig, ["--help"])
        self.assertEqual(code, 0)
        self.assertIn("usage: pc_baseline.py", out)

    def test_report_prints_what_close_writes_and_creates_no_file(self) -> None:
        w = fresh_copy_of_world()
        before = tree_snapshot(w.dated)
        code, out, err = run_baseline(w.rig, ["report", "--folder", w.relative()])
        self.assertEqual(code, 0, err)
        self.assertEqual(tree_snapshot(w.dated), before, "report wrote nothing")
        self.assertEqual(os.listdir(w.rig.runs) if os.path.isdir(w.rig.runs) else [], [], "no run root was made")
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        self.assertIn(w.read("digest-table.md").rstrip("\n"), out)
        self.assertIn(w.read("usage-by-row.txt").rstrip("\n"), out)

    def test_the_tables_and_the_report_read_only_filed_folders_never_a_run_root(self) -> None:
        import pc_evidence

        w = fresh_copy_of_world()
        with mock.patch.object(pc_evidence, "load_stage_data", side_effect=AssertionError("a run root was read")):
            with mock.patch("pc_checks.compute_facts", side_effect=AssertionError("a run root was read")):
                self.assertEqual(run_baseline(w.rig, ["report", "--folder", w.relative()])[0], 0)
                self.assertEqual(run_baseline(w.rig, ["check-words", "--folder", w.relative()])[0], 0)
                self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        source = read_text(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_baseline.py"))
        for forbidden in ("run.json", "raw/", "credentials", ".credentials", "urllib", "socket", "subprocess", "os.environ.get(\"HOME\""):
            self.assertNotIn(forbidden, source, forbidden)

    def test_the_module_holds_none_of_the_vocabulary_whole(self) -> None:
        source = read_text(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_baseline.py"))
        lines = [line for line in source.splitlines() if "VERDICT_LINE" not in line]
        self.assertIsNone(verdict_pattern().search("\n".join(lines)))


class CheckWordsTests(unittest.TestCase):
    def words(self) -> list:
        return [a + b for a, b in (("fa", "iled"), ("pa", "ssed"), ("ver", "dict"), ("acc", "epted"))]

    def test_a_folder_built_from_scripted_rows_has_none_and_exits_0(self) -> None:
        w = fresh_copy_of_world()
        code, out, err = run_baseline(w.rig, ["check-words", "--folder", w.relative()])
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, r"^check-words: [1-9][0-9]* file\(s\) scanned, 0 hit\(s\)\n$")
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        code, out, err = run_baseline(w.rig, ["check-words", "--folder", w.relative()])
        self.assertEqual(code, 0, "the closing files are clean too: " + out + err)

    def plant(self, w, relative, text):
        with open(os.path.join(w.dated, *relative.split("/")), "ab") as handle:
            handle.write(text.encode("utf-8"))

    def test_an_unquoted_word_in_a_harness_authored_file_exits_1_with_counts_only(self) -> None:
        for relative in ("%s/usage.txt" % ROW1, "STOPPED-row4a-unknown-backend/stop.txt", "%s/mechanical-checks.md" % ROW1,
                         "SKIPPED-row4a-unknown-backend-attempt-3/README.md", "row4a-unknown-backend-attempt-2/s1.exit"):
            w = fresh_copy_of_world()
            word = self.words()[0]
            self.plant(w, relative, "\nthe run %s here\n" % word)
            code, out, err = run_baseline(w.rig, ["check-words", "--folder", w.relative()])
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, relative + out + err)
            self.assertRegex(out, r"^check-words: [1-9][0-9]* file\(s\) scanned, [1-9][0-9]* hit\(s\)\n$")
            self.assertNotIn(word, out + err, "the word is never printed")

    def test_the_top_level_files_and_the_part_files_are_scanned_too(self) -> None:
        w = fresh_copy_of_world()
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        self.assertEqual(run_baseline(w.rig, ["close", "--folder", w.relative()])[0], 0)
        for relative in ("README.md", "digest-table.md", "usage-by-row.txt", "digest-table-part-2.md", "usage-by-row-part-2.txt"):
            copy = fresh_copy_of_world()
            self.assertEqual(run_baseline(copy.rig, ["close", "--folder", copy.relative()])[0], 0)
            self.assertEqual(run_baseline(copy.rig, ["close", "--folder", copy.relative()])[0], 0)
            self.plant(copy, relative, "\nmentions %s\n" % self.words()[1])
            code, out, err = run_baseline(copy.rig, ["check-words", "--folder", copy.relative()])
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, relative + out + err)

    def test_a_word_on_a_quoted_line_or_in_a_model_text_file_is_not_a_hit(self) -> None:
        w = fresh_copy_of_world()
        self.plant(w, "%s/usage.txt" % ROW1, "\n> the model said %s\n" % self.words()[2])
        self.plant(w, "%s/s1.err" % ROW1, "\nthe process said %s\n" % self.words()[0])
        self.plant(w, "%s/s2-preclear-trace.md" % ROW1, "\nthe reply said %s\n" % self.words()[3])
        code, out, err = run_baseline(w.rig, ["check-words", "--folder", w.relative()])
        self.assertEqual(code, 0, out + err)

    def test_only_the_closing_line_of_a_readme_is_allowed_its_own_word(self) -> None:
        w = fresh_copy_of_world()
        readme = os.path.join(w.dated, "STOPPED-row4a-unknown-backend", "README.md")
        text = read_text(readme)
        self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"), "the closing line is there")
        self.assertEqual(run_baseline(w.rig, ["check-words", "--folder", w.relative()])[0], 0, "and it is not counted")
        with open(readme, "ab") as handle:
            handle.write((VERDICT_LINE + "\n").encode("utf-8"))
        code, out, err = run_baseline(w.rig, ["check-words", "--folder", w.relative()])
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, "a second copy of the line is a hit: " + out + err)

    def test_the_frozen_phase_3_baseline_has_none(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        folder = os.path.join(root, "tests", "evidence", "rerun-2026-10-29-claude-sonnet-5-5")
        before = tree_snapshot(folder)
        out = io.StringIO()
        err = io.StringIO()
        code = baseline().main(["check-words", "--folder", folder], repo_root=root, out=out, err=err)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        self.assertRegex(out.getvalue(), r"^check-words: [1-9][0-9]* file\(s\) scanned, 0 hit\(s\)\n$")
        self.assertEqual(tree_snapshot(folder), before)


FACTS_NAME = "clone-facts.json"
FINAL_NAMES = ["README.md", "comparison-vs-publication-2026-10-20.txt", "digest-table.md", "review-brief.md", "usage-by-row.txt"]
FACTS_LINE = "REFUSED: the clone-facts file does not match its schema; nothing was filed"
HEAD40 = "0123456789abcdef0123456789abcdef01234567"


def good_facts(**changes):
    facts = {
        "env_names": ["HOME", "PATH", "TERM"],
        "path_checkpoint_binaries": 0,
        "helper_files_in_clone": 1,
        "helper_calls": 7,
        "helper_calls_stub": 6,
        "helper_calls_other": 1,
        "clone_head": HEAD40,
        "source_kind": "url",
        "home_kind": "throwaway",
    }
    facts.update(changes)
    return facts


def write_facts(rig, facts=None, raw=None, name=FACTS_NAME):
    """The clone-facts file in the scratch base, outside the repository; raw text wins over the dict."""
    path = os.path.join(rig.base, name)
    text = raw if raw is not None else json.dumps(good_facts() if facts is None else facts)
    with open(path, "xb") as handle:
        handle.write(text.encode("utf-8"))
    return path


def unquoted(text):
    return [line for line in text.splitlines() if not line.startswith("> ")]


class FinalizeTests(unittest.TestCase):
    """finalize files the baseline form of a dated folder through promote_into (plan 04-18, Task 1)."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()

    def finalize(self, *extra):
        return run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative()] + list(extra))

    def test_finalize_files_the_five_top_level_files_with_the_baseline_label_and_the_row_counts(self) -> None:
        before = tree_snapshot(self.w.dated)
        code, out, err = self.finalize()
        self.assertEqual(code, 0, out + err)
        after = tree_snapshot(self.w.dated)
        self.assertEqual(sorted(set(after) - set(before)), FINAL_NAMES)
        for name, data in before.items():
            self.assertEqual(after[name], data, name + " is untouched")
        self.assertIn("finalized: %s, 5 file(s)" % DATED, out)
        self.assertNotIn(self.w.rig.base, out + err)
        readme = self.w.read("README.md")
        self.assertTrue(readme.startswith("# %s\n" % DATED))
        self.assertIn("new baseline on the pinned model and the Claude Code build its rows record (model claude-sonnet-5-5, Claude Code 2.1.310)", readme)
        self.assertIn("not a replication of the committed publication folder", readme)
        self.assertIn("Row folders present when this file was written: 4 (2 filed, 1 STOPPED, 1 SKIPPED, 0 unrecognised).", readme)
        self.assertIn("Entries by outcome, the latest attempt of each: 1 filed, 0 STOPPED, 1 SKIPPED.", readme)
        self.assertNotIn("Reviewer verdict", readme, "the folder README holds no reviewer line")
        self.assertNotIn("Clean-clone run facts", readme, "no facts without a clone-facts file")
        self.assertNotIn("environment-names.txt", sorted(after))
        self.assertEqual(self.w.read("digest-table.md").splitlines()[0], "# Digest table, part 1")

    def test_the_closing_line_of_each_row_readme_is_left_alone_and_the_folder_has_no_verdict_line(self) -> None:
        self.assertEqual(self.finalize()[0], 0)
        for name in sorted(os.listdir(self.w.dated)):
            path = os.path.join(self.w.dated, name)
            if os.path.isdir(path):
                self.assertTrue(read_text(os.path.join(path, "README.md")).endswith("\n" + VERDICT_LINE + "\n"), name)

    def test_with_clone_facts_the_readme_states_them_and_the_names_file_lists_the_names_one_per_line(self) -> None:
        path = write_facts(self.w.rig)
        code, out, err = self.finalize("--clone-facts", path)
        self.assertEqual(code, 0, out + err)
        self.assertIn("finalized: %s, 6 file(s)" % DATED, out)
        self.assertEqual(self.w.read("environment-names.txt"), "HOME\nPATH\nTERM\n")
        readme = self.w.read("README.md")
        self.assertIn("environment variable names the run was started with (3, also in `environment-names.txt`): HOME, PATH, TERM", readme)
        self.assertIn("before the run: 0 checkpoint binaries on the search path of the child, 1 helper files in the clone", readme)
        self.assertIn("after the run: 7 helper calls, 6 to the stub, 1 to anything else", readme)
        self.assertIn("clone head: " + HEAD40, readme)
        self.assertIn("source of the clone: the public address", readme)
        self.assertIn("home folder of the child: a throwaway folder", readme)
        self.assertNotIn(self.w.rig.base, readme)

    def test_the_other_source_and_home_kinds_read_as_a_local_path_and_the_real_home_folder(self) -> None:
        path = write_facts(self.w.rig, good_facts(source_kind="local", home_kind="real", env_names=[]))
        self.assertEqual(self.finalize("--clone-facts", path)[0], 0)
        readme = self.w.read("README.md")
        self.assertIn("source of the clone: a local path", readme)
        self.assertIn("home folder of the child: the real home folder", readme)
        self.assertIn("(0, also in `environment-names.txt`): none", readme)

    def test_every_entry_present_reads_complete_and_a_missing_entry_reads_partial_with_a_not_run_line(self) -> None:
        import pc_rows as rows_module

        folder = self.w.dated
        done = baseline().finalize_folder(folder, self.w.rig.repo, dict(self.w.rig.env), fixed_clock, io.StringIO(), io.StringIO(),
                                          entries=[ROW1, ROW4A])
        self.assertEqual(done, 0)
        readme = self.w.read("README.md")
        self.assertIn("\nRun state: complete\n", readme)
        self.assertIn("Entries with an outcome folder: 2 of 2", readme)
        self.assertNotIn("Not run:", readme)
        self.assertNotIn("partial baseline", readme)
        other = fresh_copy_of_world()
        out = io.StringIO()
        code = baseline().finalize_folder(other.dated, other.rig.repo, dict(other.rig.env), fixed_clock, out, io.StringIO(),
                                          entries=[ROW1, ROW4A, "row2-double-conflict"])
        self.assertEqual(code, 0)
        readme = other.read("README.md")
        self.assertIn("\nRun state: partial\n", readme)
        self.assertIn("Entries with an outcome folder: 2 of 3", readme)
        self.assertIn("\nEntries not run: 1\n", readme)
        self.assertEqual([line for line in readme.splitlines() if line.startswith("Not run:")], ["Not run: row2-double-conflict"])
        self.assertIn("This is a partial baseline", readme)
        self.assertIn("Not run: row2-double-conflict", other.read("review-brief.md"))
        self.assertIn("Run state: partial", out.getvalue())
        self.assertIn("Not run: row2-double-conflict", out.getvalue())
        self.assertEqual(rows_module.ROW_IDS.count("row2-double-conflict"), 1)

    def test_the_command_line_default_expects_every_layout_and_row_so_this_small_folder_is_partial(self) -> None:
        code, out, err = self.finalize()
        self.assertEqual(code, 0, out + err)
        self.assertIn("Run state: partial", out)
        self.assertIn("Entries not run: 19", out)
        self.assertEqual(sum(1 for line in out.splitlines() if line.startswith("Not run: ")), 19)
        self.assertNotIn("Not run: " + ROW1, out)
        self.assertNotIn("Not run: " + ROW4A, out)
        self.assertIn("Not run: plain-memory", out)

    def test_the_entry_counts_follow_the_latest_attempt_of_each_id_and_the_folder_counts_follow_the_folders(self) -> None:
        os.makedirs(os.path.join(self.w.dated, "STOPPED-row2-double-conflict"))
        with open(os.path.join(self.w.dated, "STOPPED-row2-double-conflict", "README.md"), "xb") as handle:
            handle.write(b"# STOPPED: row2-double-conflict\n\nRow: row2-double-conflict\nReason: turns\nStage: s2\n\n" + VERDICT_LINE.encode() + b"\n")
        self.assertEqual(self.finalize()[0], 0)
        readme = self.w.read("README.md")
        self.assertIn("Row folders present when this file was written: 5 (2 filed, 2 STOPPED, 1 SKIPPED, 0 unrecognised).", readme)
        self.assertIn("Entries by outcome, the latest attempt of each: 1 filed, 1 STOPPED, 1 SKIPPED.", readme)

    def test_a_second_finalize_is_refused_with_17_and_changes_nothing(self) -> None:
        self.assertEqual(self.finalize()[0], 0)
        first = tree_snapshot(self.w.dated)
        code, out, err = self.finalize()
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(tree_snapshot(self.w.dated), first)
        self.assertNotIn(self.w.rig.base, out + err)

    def test_a_folder_that_already_holds_one_closing_file_is_refused_with_17_and_nothing_is_added(self) -> None:
        self.assertEqual(run_baseline(self.w.rig, ["close", "--folder", self.w.relative()])[0], 0)
        before = tree_snapshot(self.w.dated)
        code, out, err = self.finalize()
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(tree_snapshot(self.w.dated), before)

    def test_a_frozen_folder_is_refused_with_2_and_nothing_is_written(self) -> None:
        names = sorted(baseline().FROZEN_FOLDERS)
        self.assertIn("publication-2026-10-20", names)
        self.assertIn("rerun-2026-10-29-claude-sonnet-5-5", names)
        self.assertIn("rerun-2026-11-09-claude-sonnet-5-5-triple", names)
        self.assertIn("bound-ledger-2026-10-19-rerun", names)
        for name in names:
            folder = os.path.join(self.w.rig.repo, "tests", "evidence", name)
            os.makedirs(os.path.join(folder, ROW1), exist_ok=True)
            before = tree_snapshot(folder)
            code, out, err = run_baseline(self.w.rig, ["finalize", "--folder", os.path.join("tests", "evidence", name)])
            self.assertEqual(code, pc_exitcodes.USAGE, name + out + err)
            self.assertEqual(tree_snapshot(folder), before, name + " was not written")
            self.assertEqual(sorted(set(os.listdir(folder)) & set(FINAL_NAMES)), [], name + " holds no filed name")

    def test_the_real_first_baseline_is_refused_with_2_and_stays_as_it_is(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        folder = os.path.join(root, "tests", "evidence", "rerun-2026-10-29-claude-sonnet-5-5")
        before = tree_snapshot(folder)
        out = io.StringIO()
        err = io.StringIO()
        code = baseline().main(["finalize", "--folder", folder], repo_root=root, out=out, err=err)
        self.assertEqual(code, pc_exitcodes.USAGE)
        self.assertEqual(tree_snapshot(folder), before)

    def test_a_leak_shaped_reason_is_refused_with_14_and_nothing_is_filed(self) -> None:
        seeded = pc_seeds.home_path("pcsynthhome") + "/data"
        folder = os.path.join(self.w.dated, "SKIPPED-row2-double-conflict")
        os.makedirs(folder)
        with open(os.path.join(folder, "README.md"), "xb") as handle:
            handle.write(("# SKIPPED: row2-double-conflict\n\nThis row was skipped on this machine: the folder %s is missing. "
                          "No session was run.\n" % seeded).encode("utf-8"))
        before = tree_snapshot(self.w.dated)
        code, out, err = self.finalize()
        self.assertEqual(code, pc_exitcodes.LEAK_REFUSED, out + err)
        self.assertEqual(tree_snapshot(self.w.dated), before)
        self.assertNotIn(seeded, out + err)

    def test_everything_finalize_files_is_clean_for_the_leak_gate_and_the_vocabulary_scan(self) -> None:
        import pc_leakgate

        path = write_facts(self.w.rig)
        self.assertEqual(self.finalize("--clone-facts", path)[0], 0)
        report = pc_leakgate.scan_entries(pc_leakgate.collect_tree(self.w.dated), [])
        self.assertEqual(list(report.findings), [])
        code, out, err = run_baseline(self.w.rig, ["check-words", "--folder", self.w.relative()])
        self.assertEqual(code, 0, out + err)
        for name in ("README.md", "review-brief.md", "comparison-vs-publication-2026-10-20.txt", "digest-table.md", "usage-by-row.txt"):
            plain = [line for line in unquoted(self.w.read(name)) if not line.startswith("  content: ")]
            self.assertEqual(verdict_pattern().findall("\n".join(plain)), [], name)

    def test_the_vocabulary_scan_covers_the_brief_and_the_readme_in_full_and_reads_a_review_line_as_closing(self) -> None:
        self.assertEqual(self.finalize()[0], 0)
        word = "fa" + "iled"
        for name in ("review-brief.md", "README.md", "comparison-vs-publication-2026-10-20.txt"):
            copy = fresh_copy_of_world()
            self.assertEqual(run_baseline(copy.rig, ["finalize", "--folder", copy.relative()])[0], 0)
            with open(os.path.join(copy.dated, name), "ab") as handle:
                handle.write(("\nthe run %s here\n" % word).encode("utf-8"))
            code, out, err = run_baseline(copy.rig, ["check-words", "--folder", copy.relative()])
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, name + out + err)
        quoted = fresh_copy_of_world()
        self.assertEqual(run_baseline(quoted.rig, ["finalize", "--folder", quoted.relative()])[0], 0)
        with open(os.path.join(quoted.dated, "comparison-vs-publication-2026-10-20.txt"), "ab") as handle:
            handle.write(("  content: the committed text said %s\n" % word).encode("utf-8"))
        with open(os.path.join(quoted.dated, "review-brief.md"), "ab") as handle:
            handle.write(("> the quoted line said %s\n" % word).encode("utf-8"))
        self.assertEqual(run_baseline(quoted.rig, ["check-words", "--folder", quoted.relative()])[0], 0)


class FinalizeComparisonTests(unittest.TestCase):
    """finalize files the all-rows comparison against the default reference in place of the interim text (plan 04-18, Task 2)."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()

    def test_the_comparison_file_is_the_all_rows_report_against_the_publication_folder(self) -> None:
        import pc_compare

        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        reference = os.path.join(root, "tests", "evidence", "publication-2026-10-20")
        before = pc_compare.tree_digest(reference)
        code, out, err = run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative()])
        self.assertEqual(code, 0, out + err)
        text = self.w.read("comparison-vs-publication-2026-10-20.txt")
        self.assertEqual(pc_compare.tree_digest(reference), before, "the reference was only read")
        self.assertIn("compare all rows: old publication-2026-10-20, new %s\n" % DATED, text)
        self.assertIn("old unchanged: yes\n", text)
        self.assertIn("new unchanged: yes\n", text)
        self.assertNotIn("not part of this file", text, "the interim line is gone")
        self.assertIn("compare row %s: old folder %s, new folder %s, attempt 1\n" % (ROW1, ROW1, ROW1), text)
        self.assertIn("compare row %s: old folder %s, new folder %s, attempt 2\n" % (ROW4A, ROW4A, ROW4A + "-attempt-2"), text)
        self.assertIn("stopped, not compared: 1\n  STOPPED-%s\n" % ROW4A, text)
        self.assertIn("skipped, not compared: 1\n  SKIPPED-%s-attempt-3\n" % ROW4A, text)
        self.assertIn("  row2-double-conflict\n", text, "an id with no outcome folder is listed as not run")
        self.assertIn("  layout plain-memory: no structural reference (new tree: not run)\n", text)
        self.assertNotIn(self.w.rig.base, text)

    def test_the_comparison_is_part_of_the_vocabulary_scan_apart_from_the_content_lines(self) -> None:
        self.assertEqual(run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative()])[0], 0)
        code, out, err = run_baseline(self.w.rig, ["check-words", "--folder", self.w.relative()])
        self.assertEqual(code, 0, out + err)
        text = self.w.read("comparison-vs-publication-2026-10-20.txt")
        pattern = verdict_pattern()
        self.assertTrue(any(pattern.search(line) for line in text.splitlines() if line.startswith("  content: ")),
                        "the committed text quoted on content lines does hold such words")
        self.assertEqual([line for line in text.splitlines() if not line.startswith("  content: ") and pattern.search(line)], [])

    def test_a_reference_that_cannot_be_read_is_refused_with_2_and_nothing_is_filed(self) -> None:
        before = tree_snapshot(self.w.dated)
        err = io.StringIO()
        code = baseline().finalize_folder(self.w.dated, self.w.rig.repo, dict(self.w.rig.env), fixed_clock, io.StringIO(), err,
                                          reference=os.path.join(self.w.rig.base, "no-such-reference"))
        self.assertEqual(code, pc_exitcodes.USAGE)
        self.assertEqual(err.getvalue().strip(), "REFUSED: the reference tree could not be read; nothing was filed")
        self.assertEqual(tree_snapshot(self.w.dated), before)


class CloneFactsTests(unittest.TestCase):
    """The clone-facts file has one fixed schema, read strictly: any other shape is refused with exit 2 and a fixed line."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()

    def refused(self, facts=None, raw=None, name=FACTS_NAME):
        path = write_facts(self.w.rig, facts, raw, name)
        before = tree_snapshot(self.w.dated)
        code, out, err = run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative(), "--clone-facts", path])
        self.assertEqual(code, pc_exitcodes.USAGE, out + err)
        self.assertEqual(err.strip(), FACTS_LINE)
        self.assertEqual(out, "")
        self.assertEqual(tree_snapshot(self.w.dated), before, "nothing was filed")
        self.assertNotIn(self.w.rig.base, out + err)
        self.assertEqual(baseline().read_clone_facts(path), None)

    def test_a_good_file_is_read_back_as_the_same_dict(self) -> None:
        path = write_facts(self.w.rig)
        self.assertEqual(baseline().read_clone_facts(path), good_facts())
        self.assertEqual(sorted(good_facts()), sorted(baseline().CLONE_FACTS_KEYS))

    def test_an_unknown_or_a_missing_key_is_refused(self) -> None:
        facts = good_facts()
        facts["extra"] = 1
        self.refused(facts)

    def test_a_missing_key_is_refused(self) -> None:
        facts = good_facts()
        del facts["home_kind"]
        self.refused(facts)

    def test_a_negative_count_a_float_a_boolean_and_a_text_count_are_refused(self) -> None:
        for index, value in enumerate((-1, 1.5, True, "3", None, 10 ** 12)):
            self.setUp()
            self.refused(good_facts(helper_calls=value), name="f%d.json" % index)

    def test_a_name_with_a_lower_case_letter_a_dash_a_space_or_a_non_text_is_refused(self) -> None:
        for index, name in enumerate(("Path", "A-B", "A B", "", "A" * 65, 5, None, "$HOME")):
            self.setUp()
            self.refused(good_facts(env_names=["HOME", name]), name="n%d.json" % index)

    def test_a_forty_first_name_is_refused_and_forty_are_read(self) -> None:
        forty = ["NAME_%d" % number for number in range(40)]
        self.assertEqual(baseline().read_clone_facts(write_facts(self.w.rig, good_facts(env_names=forty), name="forty.json"))["env_names"], forty)
        self.refused(good_facts(env_names=forty + ["NAME_40"]), name="forty-one.json")

    def test_a_repeated_name_and_a_non_list_are_refused(self) -> None:
        self.refused(good_facts(env_names=["A", "A"]))
        self.setUp()
        self.refused(good_facts(env_names="HOME"), name="b.json")

    def test_a_head_of_the_wrong_length_case_or_alphabet_is_refused(self) -> None:
        for index, head in enumerate((HEAD40[:39], HEAD40 + "0", HEAD40.upper(), "g" * 40, 12, "")):
            self.setUp()
            self.refused(good_facts(clone_head=head), name="h%d.json" % index)

    def test_a_source_kind_other_than_url_or_local_and_a_home_kind_other_than_throwaway_or_real_are_refused(self) -> None:
        self.refused(good_facts(source_kind="path"))
        self.setUp()
        self.refused(good_facts(home_kind="home"), name="b.json")

    def test_a_file_that_is_not_one_json_object_is_refused(self) -> None:
        for index, raw in enumerate(("", "[]", "null", "{", '{"a": 1} {"b": 2}', "\xff", json.dumps(good_facts()).replace("}", ", \"home_kind\": \"real\"}"),
                                     json.dumps(good_facts()).replace("7", "NaN", 1))):
            self.setUp()
            self.refused(raw=raw, name="r%d.json" % index)

    def test_a_missing_file_a_folder_and_a_symlink_are_refused_with_the_same_fixed_line(self) -> None:
        missing = os.path.join(self.w.rig.base, "missing.json")
        for path in (missing, self.w.rig.base, ""):
            before = tree_snapshot(self.w.dated)
            code, out, err = run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative(), "--clone-facts", path])
            self.assertEqual(code, pc_exitcodes.USAGE)
            self.assertEqual(err.strip(), FACTS_LINE)
            self.assertEqual(tree_snapshot(self.w.dated), before)
        real = write_facts(self.w.rig)
        link = os.path.join(self.w.rig.base, "link.json")
        os.symlink(real, link)
        code, out, err = run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative(), "--clone-facts", link])
        self.assertEqual(code, pc_exitcodes.USAGE)
        self.assertEqual(err.strip(), FACTS_LINE)

    def test_an_oversized_file_is_refused(self) -> None:
        self.refused(raw=json.dumps(good_facts()) + " " * 70000)

    def test_the_schema_holds_no_key_that_could_carry_a_path_or_a_login(self) -> None:
        for key in baseline().CLONE_FACTS_KEYS:
            self.assertNotRegex(key, r"path$|dir$|login|user|host|home$", key)


class BriefTests(unittest.TestCase):
    """review-brief.md is built from filed files and asks for conclusions without a vocabulary word."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()
        self.assertEqual(run_baseline(self.w.rig, ["finalize", "--folder", self.w.relative()])[0], 0)
        self.brief = self.w.read("review-brief.md")

    def test_it_names_the_folder_the_model_and_build_and_the_digest_table(self) -> None:
        self.assertTrue(self.brief.startswith("# Review brief: %s\n" % DATED))
        self.assertIn("- model: claude-sonnet-5-5", self.brief)
        self.assertIn("- Claude Code build: 2.1.310", self.brief)
        self.assertIn("- Run state: partial", self.brief)
        self.assertIn("> # Digest table, part 1", self.brief)
        self.assertIn("> | %s | filed | 1 |" % ROW1, self.brief)

    def test_it_quotes_the_checklist_lines_of_each_row_and_the_stop_and_skip_lines_with_the_prefix(self) -> None:
        readme = self.w.read(ROW1, "README.md")
        checklist = [line for line in readme.splitlines() if line.startswith("- [ ]")]
        self.assertGreaterEqual(len(checklist), 6)
        for line in checklist:
            self.assertIn("> " + line + "\n", self.brief)
        self.assertIn("### %s (filed)" % ROW1, self.brief)
        self.assertIn("### STOPPED-row4a-unknown-backend (STOPPED)", self.brief)
        self.assertIn("> Row: row4a-unknown-backend\n", self.brief)
        self.assertIn("> Stage: ", self.brief)
        self.assertIn("### SKIPPED-row4a-unknown-backend-attempt-3 (SKIPPED)", self.brief)
        self.assertIn("> This row was skipped on this machine: the fixture of this test row is absent", self.brief)
        self.assertNotIn("Reviewer verdict", self.brief, "the closing lines are not quoted")

    def test_it_asks_for_one_line_per_row_and_layout_and_a_plain_statement_where_a_row_cannot_be_judged(self) -> None:
        self.assertIn("## What to return", self.brief)
        self.assertIn("Give one line for each row and layout", self.brief)
        self.assertIn("names a conclusion in a few words and gives the reason", self.brief)
        self.assertIn("write a plain statement saying so", self.brief)

    def test_it_holds_no_vocabulary_word_on_an_unquoted_line(self) -> None:
        self.assertEqual(verdict_pattern().findall("\n".join(unquoted(self.brief))), [])
        for line in unquoted(self.brief):
            self.assertNotIn(self.w.rig.base, line)

    def test_the_row_7_pointer_says_none_is_present_in_a_clone_without_a_triple_folder(self) -> None:
        self.assertIn("- no row 7 triple folder is present in this clone", self.brief)
        self.assertIn("- row 7 review table of this folder: none is filed in this folder", self.brief)

    def test_the_row_7_pointer_names_a_triple_folder_when_the_clone_holds_one(self) -> None:
        other = fresh_copy_of_world()
        triple = "rerun-2026-11-09-claude-sonnet-5-5-triple"
        os.makedirs(os.path.join(other.rig.repo, "tests", "evidence", triple, "row7-all-destinations-denied"))
        os.makedirs(os.path.join(other.rig.repo, "tests", "evidence", "rerun-2026-11-10-claude-sonnet-5-5-wave-z"))
        self.assertEqual(run_baseline(other.rig, ["finalize", "--folder", other.relative()])[0], 0)
        brief = other.read("review-brief.md")
        self.assertIn("- row 7 review table of the committed triple folder: %s (its row7-review.md)" % triple, brief)
        self.assertNotIn("wave-z", brief)
        self.assertNotIn("no row 7 triple folder", brief)

    def test_a_row_7_table_filed_in_the_folder_itself_is_pointed_to(self) -> None:
        other = fresh_copy_of_world()
        with open(os.path.join(other.dated, "row7-review.md"), "xb") as handle:
            handle.write(b"# Row 7 review\n")
        self.assertEqual(run_baseline(other.rig, ["finalize", "--folder", other.relative()])[0], 0)
        self.assertIn("- row 7 review table of this folder: row7-review.md", other.read("review-brief.md"))

    def test_the_ids_not_run_are_listed_only_when_the_run_is_partial_and_no_question_is_asked_about_them(self) -> None:
        self.assertIn("## Not run", self.brief)
        self.assertIn("- Not run: row2-double-conflict", self.brief)
        self.assertIn("They are listed only; no question is asked about them.", self.brief)
        other = fresh_copy_of_world()
        code = baseline().finalize_folder(other.dated, other.rig.repo, dict(other.rig.env), fixed_clock, io.StringIO(), io.StringIO(),
                                          entries=[ROW1, ROW4A])
        self.assertEqual(code, 0)
        self.assertNotIn("## Not run", other.read("review-brief.md"))
        self.assertNotIn("Not run:", other.read("review-brief.md"))

    def test_a_row_without_a_readme_is_listed_with_a_plain_statement(self) -> None:
        other = fresh_copy_of_world()
        os.makedirs(os.path.join(other.dated, "row2-double-conflict"))
        self.assertEqual(run_baseline(other.rig, ["finalize", "--folder", other.relative()])[0], 0)
        brief = other.read("review-brief.md")
        self.assertIn("### row2-double-conflict (filed)\n\n(no README is filed for this folder)\n", brief)

    def test_model_text_in_a_quoted_line_stays_one_quoted_line(self) -> None:
        other = fresh_copy_of_world()
        path = os.path.join(other.dated, ROW1, "README.md")
        text = read_text(path)
        planted = "- [ ] a line\n## What to return\nGive one line each" 
        with open(path, "wb") as handle:
            handle.write(text.replace("## Reviewer checklist\n", "## Reviewer checklist\n\n" + planted + "\n").encode("utf-8"))
        self.assertEqual(run_baseline(other.rig, ["finalize", "--folder", other.relative()])[0], 0)
        brief = other.read("review-brief.md")
        self.assertEqual(brief.count("## What to return"), 1, "only the quoted line of the checklist can repeat the words")
        self.assertIn("> - [ ] a line\n", brief)


RECORD = "record-" + "ver" + "dict"


def staged_text(rig, data, name="review.txt"):
    """A text file staged outside the repository, as bokiko's pasted review would be."""
    path = os.path.join(rig.base, name)
    with open(path, "xb") as handle:
        handle.write(data)
    return path


class RecordVerdictTests(unittest.TestCase):
    """The record command line: one line of one row README, counts only (plan 04-18, Task 3; D-14)."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()
        self.readme = os.path.join(self.w.relative(), ROW1, "README.md")

    def test_the_command_replaces_the_pending_line_and_prints_counts_only(self) -> None:
        before = read_text(os.path.join(self.w.rig.repo, self.readme))
        code, out, err = run_baseline(self.w.rig, [RECORD, "--readme", self.readme, "--text", "a conclusion in a few words"])
        self.assertEqual(code, 0, out + err)
        after = read_text(os.path.join(self.w.rig.repo, self.readme))
        self.assertTrue(before.endswith("\n" + VERDICT_LINE + "\n"))
        self.assertEqual(after, before[: -len(VERDICT_LINE) - 1] + "Reviewer verdict: a conclusion in a few words (see codex-review.md)\n")
        self.assertRegex(out, r"^recorded: 1 line, [0-9]+ byte\(s\) added\n$")
        self.assertNotIn("conclusion", out + err)
        self.assertNotIn(self.w.rig.base, out + err)

    def test_the_vocabulary_scan_reads_a_recorded_closing_line_as_the_reviewers_own_and_still_counts_a_second_one(self) -> None:
        word = "fa" + "iled"
        self.assertEqual(run_baseline(self.w.rig, [RECORD, "--readme", self.readme, "--text", "the row %s on the helper" % word])[0], 0)
        code, out, err = run_baseline(self.w.rig, ["check-words", "--folder", self.w.relative()])
        self.assertEqual(code, 0, out + err)
        path = os.path.join(self.w.rig.repo, self.readme)
        with open(path, "ab") as handle:
            handle.write(("Reviewer verdict: a second line %s\n" % word).encode("utf-8"))
        self.assertEqual(run_baseline(self.w.rig, ["check-words", "--folder", self.w.relative()])[0], pc_exitcodes.PREFLIGHT_FAIL)

    def test_a_missing_option_and_an_unknown_option_exit_2(self) -> None:
        for args in ([RECORD], [RECORD, "--readme", self.readme], [RECORD, "--text", "x"],
                     [RECORD, "--readme", self.readme, "--text", "x", "--folder", "y"]):
            code, out, err = run_baseline(self.w.rig, args)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(args))

    def test_a_row_readme_of_the_first_baseline_is_refused_with_2_and_stays_as_it_is(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "tests", "evidence", "rerun-2026-10-29-claude-sonnet-5-5", "row1-wrong-binding", "README.md")
        with open(path, "rb") as handle:
            before = handle.read()
        out = io.StringIO()
        err = io.StringIO()
        code = baseline().main([RECORD, "--readme", path, "--text", "x"], repo_root=root, out=out, err=err)
        self.assertEqual(code, pc_exitcodes.USAGE)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)
        self.assertEqual(err.getvalue().strip(), "REFUSED: the target or the text is not allowed; no file was changed")

    def test_the_usage_line_names_the_command_and_a_second_use_on_the_same_readme_is_refused(self) -> None:
        self.assertIn(RECORD, baseline().USAGE_LINE)
        args = [RECORD, "--readme", self.readme, "--text", "one"]
        self.assertEqual(run_baseline(self.w.rig, args)[0], 0)
        self.assertEqual(run_baseline(self.w.rig, args)[0], pc_exitcodes.USAGE)


class FileReviewTests(unittest.TestCase):
    """file-review files a staged text file as codex-review.md, byte for byte, through the leak gate (D-14, D-16)."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()

    def file(self, source, folder=None):
        return run_baseline(self.w.rig, ["file-review", "--folder", folder or self.w.relative(), "--from", source])

    def refused(self, source, code, folder=None):
        before = tree_snapshot(self.w.dated)
        result, out, err = self.file(source, folder)
        self.assertEqual(result, code, out + err)
        self.assertEqual(tree_snapshot(self.w.dated), before, "nothing was created")
        self.assertNotIn(self.w.rig.base, out + err)
        return out + err

    def test_the_file_is_filed_byte_for_byte_and_the_vocabulary_scan_does_not_cover_it(self) -> None:
        word = "fa" + "iled"
        data = ("Codex wrote: row 1 %s, row 2 ok.\r\n\u00e9\u4e2d\n> quoted\n\n" % word).encode("utf-8")
        source = staged_text(self.w.rig, data)
        before = tree_snapshot(self.w.dated)
        code, out, err = self.file(source)
        self.assertEqual(code, 0, out + err)
        after = tree_snapshot(self.w.dated)
        self.assertEqual(sorted(set(after) - set(before)), ["codex-review.md"])
        self.assertEqual(after["codex-review.md"], data)
        self.assertEqual(out, "filed: %s, codex-review.md, %d byte(s)\n" % (DATED, len(data)))
        self.assertEqual(run_baseline(self.w.rig, ["check-words", "--folder", self.w.relative()])[0], 0)

    def test_an_existing_codex_review_md_is_refused_with_17(self) -> None:
        self.assertEqual(self.file(staged_text(self.w.rig, b"one\n"))[0], 0)
        first = tree_snapshot(self.w.dated)
        code, out, err = self.file(staged_text(self.w.rig, b"two\n", "second.txt"))
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(tree_snapshot(self.w.dated), first)

    def test_a_frozen_folder_and_a_folder_that_is_not_a_dated_folder_are_refused_with_2(self) -> None:
        source = staged_text(self.w.rig, b"x\n")
        frozen = os.path.join("tests", "evidence", "rerun-2026-11-03-claude-sonnet-5-5-wave-a")
        os.makedirs(os.path.join(self.w.rig.repo, frozen))
        self.assertEqual(run_baseline(self.w.rig, ["file-review", "--folder", frozen, "--from", source])[0], pc_exitcodes.USAGE)
        self.assertEqual(os.listdir(os.path.join(self.w.rig.repo, frozen)), [])
        for folder in (os.path.join("tests", "evidence"), os.path.join(self.w.relative(), ROW1), "..", "rerun-missing"):
            self.assertEqual(run_baseline(self.w.rig, ["file-review", "--folder", folder, "--from", source])[0], pc_exitcodes.USAGE, folder)

    def test_a_missing_source_a_folder_a_symlink_and_a_source_in_the_evidence_tree_are_refused_with_2(self) -> None:
        self.refused(os.path.join(self.w.rig.base, "missing.txt"), pc_exitcodes.USAGE)
        self.refused(self.w.rig.base, pc_exitcodes.USAGE)
        real = staged_text(self.w.rig, b"x\n")
        link = os.path.join(self.w.rig.base, "link.txt")
        os.symlink(real, link)
        self.refused(link, pc_exitcodes.USAGE)
        inside = os.path.join(self.w.dated, ROW1, "README.md")
        self.refused(inside, pc_exitcodes.USAGE)
        self.refused("", pc_exitcodes.USAGE)

    def test_a_source_of_200000_bytes_is_filed_and_one_byte_more_is_refused_with_2(self) -> None:
        big = ("a" * 79 + "\n") * 2500
        self.assertEqual(len(big), 200000)
        self.refused(staged_text(self.w.rig, (big + "x").encode("utf-8"), "over.txt"), pc_exitcodes.USAGE)
        code, out, err = self.file(staged_text(self.w.rig, big.encode("utf-8"), "exact.txt"))
        self.assertEqual(code, 0, out + err)

    def test_a_leak_shaped_line_is_refused_with_14_and_nothing_is_created(self) -> None:
        seeded = pc_seeds.home_path("pcsynthhome") + "/data"
        text = self.refused(staged_text(self.w.rig, ("a line\n%s\n" % seeded).encode("utf-8")), pc_exitcodes.LEAK_REFUSED)
        self.assertNotIn(seeded, text)

    def test_binary_content_is_refused_by_the_gate_with_14(self) -> None:
        self.refused(staged_text(self.w.rig, b"a\x00b\n"), pc_exitcodes.LEAK_REFUSED)


class EvidenceReadmeTests(unittest.TestCase):
    """evidence-readme files the one top-level file with the evidence-root allowance and nothing else (D-15; T-04-89)."""

    def setUp(self) -> None:
        self.w = fresh_copy_of_world()
        self.evidence = os.path.join(self.w.rig.repo, "tests", "evidence")
        for name in ("rerun-2026-10-29-claude-sonnet-5-5", "rerun-2026-11-03-claude-sonnet-5-5-wave-a", "plain-memory-2026-10-19"):
            os.makedirs(os.path.join(self.evidence, name), exist_ok=True)

    def run_it(self, reference=DATED):
        return run_baseline(self.w.rig, ["evidence-readme", "--reference", reference])

    def test_it_files_the_readme_naming_the_reference_the_superseded_folder_and_the_labelled_folders(self) -> None:
        before = tree_snapshot(self.evidence)
        code, out, err = self.run_it()
        self.assertEqual(code, 0, out + err)
        after = tree_snapshot(self.evidence)
        self.assertEqual(sorted(set(after) - set(before)), ["README.md"])
        for name, data in before.items():
            self.assertEqual(after[name], data, name)
        text = read_text(os.path.join(self.evidence, "README.md"))
        self.assertIn("- Reference baseline: `%s`." % DATED, text)
        self.assertIn("`publication-2026-10-20` is superseded as the reference. It is untouched", text)
        self.assertIn("First single-row baseline: `rerun-2026-10-29-claude-sonnet-5-5`", text)
        self.assertIn("- `rerun-2026-11-03-claude-sonnet-5-5-wave-a`", text)
        self.assertIn("- `plain-memory-2026-10-19`", text)
        self.assertNotIn("`%s`\n- `rerun-2026-10-29" % DATED, text)
        self.assertEqual(out, "filed: tests/evidence, README.md\n")
        self.assertNotIn(self.w.rig.base, text)
        self.assertNotIn("Reviewer verdict", text)

    def test_an_existing_readme_is_refused_with_17_and_left_as_it_is(self) -> None:
        self.assertEqual(self.run_it()[0], 0)
        first = tree_snapshot(self.evidence)
        code, out, err = self.run_it()
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, out + err)
        self.assertEqual(tree_snapshot(self.evidence), first)

    def test_a_reference_that_is_not_a_folder_of_the_tree_is_refused_with_2_and_nothing_is_filed(self) -> None:
        before = tree_snapshot(self.evidence)
        for reference in ("missing-folder", "..", ".", "a/b", "", "a b", "README.md", "plain-memory-2026-10-19", "rerun-missing"):
            self.assertEqual(self.run_it(reference)[0], pc_exitcodes.USAGE, reference)
        link = os.path.join(self.evidence, "rerun-linked")
        os.symlink(os.path.join(self.evidence, DATED), link)
        self.assertEqual(self.run_it("rerun-linked")[0], pc_exitcodes.USAGE)
        self.assertEqual(tree_snapshot(self.evidence), before)

    def test_the_evidence_root_accepts_one_flat_name_only(self) -> None:
        for files in ({"other.md": b"x\n"}, {"README.md": b"x\n", "second.md": b"y\n"}, {"sub/README.md": b"x\n"}):
            before = tree_snapshot(self.evidence)
            out = io.StringIO()
            code, count = baseline()._add_flat_files(
                self.evidence, self.w.rig.repo, dict(self.w.rig.env), fixed_clock, files, "guard-test", out, evidence_root=True
            )
            self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, sorted(files))
            self.assertEqual(count, 0)
            self.assertEqual(tree_snapshot(self.evidence), before)

    def test_the_other_commands_still_refuse_the_evidence_folder_itself(self) -> None:
        for command in ("close", "finalize"):
            code, out, err = run_baseline(self.w.rig, [command, "--folder", os.path.join("tests", "evidence")])
            self.assertEqual(code, pc_exitcodes.USAGE, command)


if __name__ == "__main__":
    unittest.main()
