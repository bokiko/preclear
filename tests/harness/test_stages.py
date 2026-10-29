"""Zero-token tests for the three-stage chain of row 1 (plan 03-02 Task 2; HARN-05, D-01, D-02, D-12, D-14).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every
folder comes from RowRig and is never deleted. pc_row1 is imported inside each test, so a missing module
is one error per test and not one load failure of the file.
"""
from __future__ import annotations

import io
import json
import os
import unittest
import uuid
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_sanitize
import pc_seeds
import pc_spend
import pc_stream
import pc_testutil

ROW1 = "row1-wrong-binding"
FIXED_STAMP = "20261028T120000Z"
KEYS = ("row1-s1", "row1-s2", "row1-s3")


def row1():
    import pc_row1

    return pc_row1


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def read_json(path: str):
    return json.loads(read_text(path))


def default_stages():
    return pc_testutil.default_row1_stages()


class Run(object):
    """A rig, a context and the outcome of one run_row call."""

    def __init__(self, stages=None, timeout_override=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.ctx = self.rig.context()
        self.outcome = row1().run_row(self.ctx, timeout_override=timeout_override)

    @property
    def run_root(self) -> str:
        names = os.listdir(self.ctx.runs_root)
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    def raw(self, name: str) -> str:
        return os.path.join(self.run_root, "raw", name)

    def ledger(self):
        return pc_spend.read_records(self.ctx.harness_home)

    def session(self) -> str:
        return read_json(self.raw("run.json"))["session_id"]


def with_result(stages, index, **changes):
    updated = pc_testutil.stages_with(stages, index)
    updated[index]["result"] = dict(updated[index].get("result", {}), **changes)
    return updated


class ChainTests(unittest.TestCase):
    def test_three_processes_run_in_order_with_the_pinned_argv_forms_and_a_launch_settle_pair_each(self) -> None:
        run = Run(default_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        calls = run.rig.calls()
        self.assertEqual(len(calls), 3)
        first, second, third = [call["args"] for call in calls]
        u1 = run.session()
        self.assertEqual(first[first.index("--session-id") + 1], u1)
        self.assertEqual(first[first.index("--max-turns") + 1], "15")
        self.assertEqual(first[first.index("--max-budget-usd") + 1], "0.30")
        self.assertEqual(second[second.index("--resume") + 1], u1)
        self.assertNotIn("--session-id", second)
        self.assertEqual(second[second.index("--max-turns") + 1], "60")
        self.assertEqual(second[second.index("--max-budget-usd") + 1], "1.30")
        u2 = third[third.index("--session-id") + 1]
        self.assertNotEqual(u2, u1)
        self.assertEqual(str(uuid.UUID(u2)), u2)
        self.assertNotIn("--resume", third)
        self.assertEqual(third[third.index("--max-turns") + 1], "15")
        self.assertEqual(third[third.index("--max-budget-usd") + 1], "0.40")
        for argv in (first, second, third):
            self.assertEqual(argv[argv.index("--permission-mode") + 1], "default")
            self.assertEqual(len(argv[argv.index("--allowedTools") + 1].split(",")), 40)
            self.assertEqual(argv[argv.index("--model") + 1], pc_flags.PINNED_MODEL)
            for absent in ("--dangerously-skip-permissions", "--include-hook-events"):
                self.assertNotIn(absent, argv)
        for call in calls:
            self.assertEqual(os.path.realpath(call["cwd"]), os.path.realpath(os.path.join(run.run_root, "project")))
            self.assertEqual(call["env"]["DISABLE_AUTOUPDATER"], "1")
        self.assertEqual(
            [(r["kind"], r["stage"]) for r in run.ledger()],
            [("launch", "row1-s1"), ("settle", "row1-s1"), ("launch", "row1-s2"), ("settle", "row1-s2"),
             ("launch", "row1-s3"), ("settle", "row1-s3")],
        )
        self.assertEqual(
            sorted(os.listdir(os.path.join(run.run_root, "snaps"))),
            ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"],
        )
        for line in run.outcome.lines:
            self.assertRegex(
                line, r"^(stage s[123]: [A-Za-z0-9_, .()-]+|filed: [A-Za-z0-9_, .()-]+|row total: [0-9.]+ USD)$"
            )
            self.assertNotIn(run.rig.base, line)
            self.assertNotIn(u1, line)
        self.assertEqual(read_json(run.raw("s2.record.json"))["wrapper_calls"], 1)

    def test_a_run_through_the_driver_reaches_the_row_runner_and_returns_zero(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        import datetime

        out = io.StringIO()
        err = io.StringIO()
        code = matrix().main(
            ["--row", ROW1, "--claude", rig.claude, "--budget", "2.00"],
            env=dict(rig.env),
            repo_root=rig.repo,
            clock=lambda: datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc),
            out=out,
            err=err,
        )
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        self.assertEqual(len(rig.calls()), 3)
        self.assertIn("row total", out.getvalue())

    def test_the_s3_prompt_is_the_resume_line_byte_for_byte_with_no_trailing_newline(self) -> None:
        run = Run(default_stages())
        calls = run.rig.calls()
        project = os.path.join(run.run_root, "project")
        expected = (
            'Resume widget-export from "' + project + '/.preclear/widget-export/checkpoint.md" '
            + "— main @ abc1234 — step 2 done untested; JSON-default diff pending"
        )
        self.assertEqual(calls[2]["prompt"], expected)
        self.assertFalse(calls[2]["prompt"].endswith("\n"))
        with open(run.raw("s2.stdout"), "rb") as handle:
            events = pc_stream.parse_stream(handle.read())
        text = pc_stream.require_single_result(events)["result"]
        self.assertEqual(row1().extract_resume_line(text), expected)
        chain = read_json(run.raw("chain.json"))
        self.assertEqual(chain["marker"], "found")
        self.assertEqual(chain["resume_line"], expected)

    def test_without_a_resume_line_no_third_process_starts_and_the_marker_is_recorded(self) -> None:
        stages = with_result(default_stages(), 1, text="Checkpoint written. There is nothing to resume from.")
        run = Run(stages)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), 2)
        chain = read_json(run.raw("chain.json"))
        self.assertEqual(chain["marker"], "NO-RESUME-LINE")
        self.assertIsNone(chain["resume_line"])
        self.assertEqual([r["stage"] for r in run.ledger()], ["row1-s1", "row1-s1", "row1-s2", "row1-s2"])
        self.assertFalse(os.path.exists(os.path.join(run.run_root, "snaps", "snap-3-after-resume")))
        self.assertFalse(os.path.exists(run.raw("s3.stdout")))
        self.assertTrue(any("NO-RESUME-LINE" in line for line in run.outcome.lines))

    def test_permission_denials_do_not_stop_the_chain(self) -> None:
        run = Run(default_stages())
        with open(run.raw("s2.stdout"), "rb") as handle:
            events = pc_stream.parse_stream(handle.read())
        summary = pc_stream.result_summary(events)
        self.assertEqual(summary["permission_denials"], 1)
        self.assertTrue(any(e.get("subtype") == "permission_denied" for e in events if e["type"] == "system"))
        self.assertEqual(run.outcome.code, 0)
        self.assertEqual(len(run.rig.calls()), 3)

    def test_each_stage_record_keeps_its_own_usage_cost_and_snapshot(self) -> None:
        stages = default_stages()
        for index, tokens in enumerate((111, 222, 333)):
            stages = with_result(
                stages,
                index,
                usage={"input_tokens": tokens, "cache_creation_input_tokens": 1,
                       "cache_read_input_tokens": 2, "output_tokens": 3},
            )
        run = Run(stages)
        self.assertEqual(run.outcome.code, 0)
        records = [read_json(run.raw("s%d.record.json" % n)) for n in (1, 2, 3)]
        self.assertEqual([r["usage"]["input_tokens"] for r in records], [111, 222, 333])
        self.assertEqual([r["delta"] for r in records], ["0.03", "0.06", "0.04"])
        self.assertEqual([r["cumulative"] for r in records], ["0.03", "0.09", "0.04"])
        self.assertEqual(
            [r["snapshot"] for r in records], ["snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"]
        )
        self.assertEqual([r["resume"] for r in records], [False, True, False])
        self.assertEqual(records[0]["session_id"], records[1]["session_id"])
        self.assertNotEqual(records[0]["session_id"], records[2]["session_id"])
        for record in records:
            self.assertEqual(record["cumulative_consistent"], "yes")


class ResumeLineTests(unittest.TestCase):
    def extract(self, text):
        return row1().extract_resume_line(text)

    def test_the_last_fenced_single_line_starting_with_resume_is_returned(self) -> None:
        text = "Done.\n\n```\nResume first thing\n```\n\nMore.\n\n```\nResume second thing\n```\n"
        self.assertEqual(self.extract(text), "Resume second thing")

    def test_a_fence_with_a_language_tag_is_accepted(self) -> None:
        self.assertEqual(self.extract("x\n```text\nResume tagged line\n```\n"), "Resume tagged line")

    def test_a_multi_line_block_and_a_line_not_starting_with_resume_are_ignored(self) -> None:
        self.assertEqual(self.extract("```\nResume a\nmore lines\n```\n"), "")
        self.assertEqual(self.extract("```\nSomething else\n```\n"), "")
        self.assertEqual(self.extract("```\nResume\n```\n"), "")
        text = "```\nResume kept\n```\n\n```\nResume a\nmore lines\n```\n"
        self.assertEqual(self.extract(text), "Resume kept")

    def test_a_long_line_a_nul_or_no_fence_gives_the_empty_string(self) -> None:
        long_line = "Resume " + "x" * 1993
        self.assertEqual(len(long_line.encode("utf-8")), 2000)
        self.assertEqual(self.extract("```\n%s\n```\n" % long_line), long_line)
        self.assertEqual(self.extract("```\n%s\n```\n" % (long_line + "y")), "")
        self.assertEqual(self.extract("```\nResume a\x00b\n```\n"), "")
        self.assertEqual(self.extract("no fence at all"), "")
        self.assertEqual(self.extract(""), "")
        self.assertEqual(self.extract(None), "")

    def test_an_invalid_last_candidate_is_not_replaced_by_an_earlier_one(self) -> None:
        text = "```\nResume good\n```\n\n```\nResume bad\x00\n```\n"
        self.assertEqual(self.extract(text), "")


class CostTests(unittest.TestCase):
    def test_the_s2_delta_is_its_own_call_and_the_row_total_is_the_s2_cumulative_plus_s3(self) -> None:
        run = Run(default_stages())
        settles = [r for r in run.ledger() if r["kind"] == "settle"]
        self.assertEqual([r["delta"] for r in settles], [Decimal("0.03"), Decimal("0.06"), Decimal("0.04")])
        self.assertEqual([r["cumulative"] for r in settles], [Decimal("0.03"), Decimal("0.09"), Decimal("0.04")])
        self.assertIn("row total: 0.13 USD", run.outcome.lines)

    def test_without_the_since_last_result_mapping_the_delta_is_the_difference_of_totals(self) -> None:
        stages = default_stages()
        stages[1]["result"].pop("delta")
        run = Run(stages)
        settles = [r for r in run.ledger() if r["kind"] == "settle"]
        self.assertEqual(settles[1]["delta"], Decimal("0.06"))
        self.assertEqual(
            read_json(run.raw("s2.record.json"))["cumulative_consistent"],
            "unknown",
            "the delta came from the totals, so nothing independent was compared (WR-04)",
        )
        self.assertIn("row total: 0.13 USD", run.outcome.lines)

    def test_a_cumulative_that_disagrees_with_previous_plus_delta_is_recorded_as_inconsistent(self) -> None:
        run = Run(with_result(default_stages(), 1, total_cost_usd=0.20))
        self.assertEqual(run.outcome.code, 0)
        record = read_json(run.raw("s2.record.json"))
        self.assertEqual(record["cumulative_consistent"], "no")
        self.assertEqual(record["delta"], "0.06")
        self.assertEqual(record["cumulative"], "0.2")
        self.assertIn("row total: 0.24 USD", run.outcome.lines)


class ConsistencyUnknownTests(unittest.TestCase):
    """WR-04 of the second pass: yes means two independent numbers agreed, so a cost derived from the totals
    is unknown."""

    def test_has_call_block_is_true_only_for_a_non_empty_mapping(self) -> None:
        key = "model_usage_since_last_result"
        self.assertTrue(pc_spend.has_call_block({key: {"some-model": {"costUSD": 0.01}}}), "a non-empty mapping")
        self.assertFalse(pc_spend.has_call_block({}), "the key is missing")
        self.assertFalse(pc_spend.has_call_block({key: {}}), "an empty mapping")
        self.assertFalse(pc_spend.has_call_block({key: [1]}), "a list")
        self.assertFalse(pc_spend.has_call_block({key: 3}), "a number")

    def test_the_flag_gates_the_comparison(self) -> None:
        consistent = row1()._consistent
        prev, delta, total = Decimal("0.03"), Decimal("0.06"), Decimal("0.09")
        self.assertEqual(consistent(prev, delta, total, False), "unknown", "no block, numbers agree")
        self.assertEqual(consistent(prev, delta, Decimal("0.20"), False), "unknown", "no block, numbers disagree")
        self.assertEqual(consistent(None, Decimal("0.03"), Decimal("0.03"), False), "unknown", "no block, first call")
        self.assertEqual(consistent(prev, delta, total, True), "yes", "block, agree")
        self.assertEqual(consistent(prev, delta, Decimal("0.20"), True), "no", "block, disagree")
        self.assertEqual(consistent(prev, None, total, True), "unknown", "block, no delta")
        self.assertEqual(consistent(prev, delta, None, True), "unknown", "block, no cumulative")

    def test_a_result_without_the_block_reads_unknown_for_that_stage_only(self) -> None:
        stages = default_stages()
        stages[1]["result"].pop("delta")
        run = Run(stages)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        flags = [read_json(run.raw("s%d.record.json" % n))["cumulative_consistent"] for n in (1, 2, 3)]
        self.assertEqual(flags, ["yes", "unknown", "yes"])

    def test_disagreeing_totals_without_the_block_are_still_unknown_and_with_it_are_no(self) -> None:
        stages = with_result(default_stages(), 1, total_cost_usd=0.20)
        stages[1]["result"].pop("delta")
        run = Run(stages)
        self.assertEqual(read_json(run.raw("s2.record.json"))["cumulative_consistent"], "unknown", "nothing compared")
        run = Run(with_result(default_stages(), 1, total_cost_usd=0.20))
        self.assertEqual(read_json(run.raw("s2.record.json"))["cumulative_consistent"], "no", "two numbers compared")

    def test_the_default_run_gives_yes_three_times(self) -> None:
        run = Run(default_stages())
        flags = [read_json(run.raw("s%d.record.json" % n))["cumulative_consistent"] for n in (1, 2, 3)]
        self.assertEqual(flags, ["yes", "yes", "yes"])


class StopRuleTests(unittest.TestCase):
    def assert_stopped(self, run, code, calls, stage="s1"):
        self.assertEqual(run.outcome.code, code, "\n".join(run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), calls)
        self.assertEqual(len(run.outcome.lines), 1)
        self.assertIn("stage " + stage, run.outcome.lines[0])
        self.assertNotIn(run.rig.base, run.outcome.lines[0])
        self.assertEqual(len([r for r in run.ledger() if r["kind"] == "launch"]), calls)
        self.assertEqual(len([r for r in run.ledger() if r["kind"] == "settle"]), calls)
        self.assertTrue(os.path.isfile(run.raw("%s.stdout" % stage)))

    def test_a_non_zero_exit_stops_the_chain_with_11(self) -> None:
        stages = pc_testutil.stages_with(default_stages(), 0, exit=1)
        self.assert_stopped(Run(stages), pc_exitcodes.PREFLIGHT_FAIL, 1)

    def test_a_timeout_stops_the_chain_with_11_keeps_the_raw_bytes_and_the_cap(self) -> None:
        stages = pc_testutil.stages_with(
            default_stages(), 0, ops=[{"op": "init"}, {"op": "text", "text": "partial"}, {"op": "sleep", "seconds": 8}]
        )
        run = Run(stages, timeout_override=1)
        self.assert_stopped(run, pc_exitcodes.PREFLIGHT_FAIL, 1)
        with open(run.raw("s1.stdout"), "rb") as handle:
            self.assertIn("partial", handle.read().decode("utf-8"))
        settle = [r for r in run.ledger() if r["kind"] == "settle"][0]
        self.assertEqual(settle["subtype"], "timeout")
        self.assertIsNone(settle["delta"])
        self.assertEqual(pc_spend.row_pessimistic_total(run.ctx.harness_home, ROW1), Decimal("0.30"))
        self.assertIs(read_json(run.raw("s1.record.json"))["timed_out"], True)

    def test_a_result_that_is_not_a_clean_success_stops_the_chain_with_11(self) -> None:
        for changes in (
            {"subtype": "error_max_turns"},
            {"is_error": True},
            {"terminal_reason": "max_turns"},
        ):
            run = Run(with_result(default_stages(), 0, **changes))
            self.assert_stopped(run, pc_exitcodes.PREFLIGHT_FAIL, 1)

    def test_a_missing_terminal_reason_is_not_a_failure(self) -> None:
        run = Run(with_result(default_stages(), 0, omit=["terminal_reason"]))
        self.assertEqual(run.outcome.code, 0)

    def test_a_stream_without_a_single_result_event_stops_the_chain_with_19(self) -> None:
        stages = pc_testutil.stages_with(default_stages(), 0, no_result=True)
        self.assert_stopped(Run(stages), pc_exitcodes.DENIAL_FOUND, 1)
        broken = pc_testutil.stages_with(default_stages(), 0, ops=[{"op": "raw", "line": "this is not json"}])
        self.assert_stopped(Run(broken), pc_exitcodes.DENIAL_FOUND, 1)

    def test_a_later_stage_that_fails_stops_the_chain_before_the_next_one(self) -> None:
        stages = with_result(default_stages(), 1, subtype="error_during_execution")
        run = Run(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertEqual(len(run.rig.calls()), 2)
        self.assertIn("stage s2", run.outcome.lines[0])
        self.assertFalse(os.path.exists(run.raw("chain.json")))
        self.assertFalse(os.path.exists(run.raw("s3.stdout")))


class PreSpendTests(unittest.TestCase):
    def ledger_file(self, ctx) -> str:
        return os.path.join(ctx.harness_home, "matrix-spend.jsonl")

    def test_an_existing_destination_is_17_before_any_run_root_or_ledger_line(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        ctx = rig.context()
        os.makedirs(ctx.destination)
        outcome = row1().run_row(ctx)
        self.assertEqual(outcome.code, pc_exitcodes.PROMOTE_REFUSED)
        self.assertFalse(os.path.exists(self.ledger_file(ctx)))
        self.assertEqual(os.listdir(ctx.runs_root), [])
        self.assertEqual(rig.calls(), [])
        self.assertNotIn(rig.base, "\n".join(outcome.lines))

    def test_a_dangling_symlink_destination_is_also_17(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        ctx = rig.context()
        os.symlink(os.path.join(rig.base, "no-such-target"), ctx.destination)
        self.assertEqual(row1().run_row(ctx).code, pc_exitcodes.PROMOTE_REFUSED)
        self.assertEqual(rig.calls(), [])

    def test_a_taken_run_root_is_16_before_any_ledger_line(self) -> None:
        import datetime

        rig = pc_testutil.RowRig(stages=default_stages())
        ctx = rig.context()
        moment = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
        rig.new_run_root(ctx, "%s-%s" % (ROW1, FIXED_STAMP))
        row = rows().find_entry(rows().build_registry(), "row", ROW1)
        out = io.StringIO()
        err = io.StringIO()
        with mock.patch.object(row1(), "_utc_now", return_value=moment):
            code = matrix().execute_row(row, ctx, out, err)
        self.assertEqual(code, pc_exitcodes.RUNROOT_COLLISION)
        self.assertFalse(os.path.exists(self.ledger_file(ctx)))
        self.assertEqual(rig.calls(), [])

    def test_a_sanitizer_that_cannot_be_built_is_15_with_no_ledger_line_and_no_process(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        ctx = rig.context()
        with mock.patch("pc_leakgate.subprocess.run", side_effect=OSError("planted failure")):
            outcome = row1().run_row(ctx)
        self.assertEqual(outcome.code, pc_exitcodes.SCANNER_ERROR, "\n".join(outcome.lines))
        self.assertFalse(os.path.exists(self.ledger_file(ctx)))
        self.assertEqual(rig.calls(), [])
        self.assertNotIn("planted", "\n".join(outcome.lines))

    def test_a_malformed_ledger_is_refused_before_the_first_stage(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        ctx = rig.context()
        os.makedirs(ctx.harness_home, exist_ok=True)
        with open(self.ledger_file(ctx), "w", encoding="utf-8") as handle:
            handle.write("not a ledger line\n")
        with self.assertRaises(pc_spend.SpendError):
            row1().run_row(ctx)
        self.assertEqual(rig.calls(), [])


class CallerMapTests(unittest.TestCase):
    def paths(self, base):
        return {"run_root": os.path.join(base, "runs", "row1-x"), "auto_memory": os.path.join(base, "runs", "row1-x", "auto-memory")}

    def test_the_map_sends_the_run_root_the_auto_memory_and_the_runs_folders_to_their_tokens(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        runs = os.path.join(rig.base, "outer", "inner", "runs")
        os.makedirs(runs)
        paths = self.paths(runs)
        mapping = row1().caller_map(paths, runs)
        real = os.path.realpath
        self.assertEqual(mapping[paths["run_root"]], "<run>")
        self.assertEqual(mapping[paths["auto_memory"]], "<auto-memory-root>")
        self.assertEqual(mapping[real(runs)], "<scratch>")
        self.assertEqual(mapping[os.path.dirname(real(runs))], "<scratch>")
        self.assertNotIn(os.path.dirname(os.path.dirname(real(runs))), mapping)
        self.assertNotIn("/", [key for key in mapping])

    def test_a_two_component_prefix_under_a_users_root_is_mapped_to_scratch(self) -> None:
        runs = os.path.join(pc_seeds.home_path("zz-shared"), "preclear-harness", "runs")
        paths = self.paths(runs)
        mapping = row1().caller_map(paths, runs)
        self.assertEqual(mapping[pc_seeds.home_path("zz-shared")], "<scratch>")
        self.assertEqual(mapping[os.path.dirname(runs)], "<scratch>")

    def test_the_prefix_rule_knows_both_users_and_home_roots_and_nothing_else(self) -> None:
        m = row1()
        self.assertEqual(m._users_prefix(pc_seeds.home_path("zz-shared") + "/a/b"), pc_seeds.home_path("zz-shared"))
        self.assertEqual(
            m._users_prefix(pc_seeds.home_path_linux("zz-shared") + "/a/b"), pc_seeds.home_path_linux("zz-shared")
        )
        self.assertIsNone(m._users_prefix(os.sep + "Users"))
        self.assertIsNone(m._users_prefix(os.sep + "srv" + os.sep + "runs" + os.sep + "x"))

    def test_the_sanitizer_with_the_map_removes_the_parent_the_gate_otherwise_flags(self) -> None:
        rig = pc_testutil.RowRig(stages=default_stages())
        runs = os.path.join(rig.base, "outer", "inner", "runs")
        os.makedirs(runs)
        paths = self.paths(os.path.realpath(runs))
        mapping = row1().caller_map(paths, runs)
        sources = pc_sanitize.Sources([], "", [], [], rig.repo)
        full = pc_sanitize.Sanitizer.from_machine(rig.repo, mapping, sources=sources)
        without = pc_sanitize.Sanitizer.from_machine(
            rig.repo, dict((k, v) for k, v in mapping.items() if v != "<scratch>"), sources=sources
        )
        parent = os.path.dirname(os.path.realpath(runs))
        text = "inside %s/project/file and above %s/elsewhere" % (paths["run_root"], parent)
        with_scratch = full.sanitize_text(text)
        self.assertEqual(with_scratch, "inside <run>/project/file and above <scratch>/elsewhere")
        no_scratch = without.sanitize_text(text)
        self.assertEqual(no_scratch, "inside <run>/project/file and above %s/elsewhere" % parent)
        self.assertNotEqual(with_scratch, no_scratch)


if __name__ == "__main__":
    unittest.main()
