"""Zero-token tests for the matrix spend ledger (plan 03-01, task 3; D-12, D-14; HARN-05).

No test starts a process. Every ledger lives in a temporary harness home made by tempfile.mkdtemp
and is never deleted. Costs are exact Decimal values throughout; the committed spike streams give
the real per-call and cumulative figures the delta accounting must reproduce.

pc_spend is imported inside each test, so a missing module is reported as one error per test
instead of a single load failure of the whole file.
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
import unittest
from decimal import Decimal
from typing import Any, List

import pc_stream

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HARNESS_DIR, "data")
ROW = "row1-wrong-binding"
S1, S2, S3 = "row1-s1", "row1-s2", "row1-s3"
ALLOWED = (S1, S2, S3)
VERSION = "2.1.310"


def spend():
    import pc_spend

    return pc_spend


def scratch_home() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-spend-"))


def ledger_path(home: str) -> str:
    return os.path.join(home, "matrix-spend.jsonl")


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def write_raw(home: str, data: bytes) -> None:
    """Plant ledger bytes for a malformed-ledger test (append mode, never truncating)."""
    with open(ledger_path(home), "ab") as handle:
        handle.write(data)


def lines_of(home: str) -> List[dict]:
    return [json.loads(line) for line in read_bytes(ledger_path(home)).decode("ascii").splitlines()]


def launch(home: str, stage: str, cap: str, allowed=ALLOWED) -> int:
    return spend().append_launch(home, ROW, stage, Decimal(cap), VERSION, allowed)


def result_event(path: str) -> dict:
    with open(os.path.join(DATA_DIR, path), "rb") as handle:
        events = pc_stream.parse_stream(handle.read())
    return pc_stream.require_single_result(events)


class ReservationTests(unittest.TestCase):
    def test_the_first_launch_is_attempt_one_and_writes_one_private_line(self) -> None:
        home = scratch_home()
        self.assertEqual(launch(home, S1, "0.30"), 1)
        records = lines_of(home)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(
            sorted(record), ["attempt", "cap", "kind", "row", "stage", "version"], "a launch line has the wrong keys"
        )
        self.assertEqual(
            (record["kind"], record["row"], record["stage"], record["attempt"], record["cap"], record["version"]),
            ("launch", ROW, S1, 1, "0.30", VERSION),
        )
        self.assertEqual(stat.S_IMODE(os.stat(ledger_path(home)).st_mode), 0o600)

    def test_a_missing_home_is_created_private(self) -> None:
        home = os.path.join(scratch_home(), "new-home")
        self.assertEqual(launch(home, S1, "0.30"), 1)
        self.assertEqual(stat.S_IMODE(os.stat(home).st_mode), 0o700)

    def test_a_second_launch_of_one_stage_is_refused_and_writes_nothing(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        before = read_bytes(ledger_path(home))
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, S1, "0.30")
        self.assertEqual(read_bytes(ledger_path(home)), before)

    def test_another_stage_is_unaffected(self) -> None:
        home = scratch_home()
        launch(home, S1, "0.30")
        self.assertEqual(launch(home, S2, "1.30"), 1)

    def test_an_unknown_stage_is_refused_and_nothing_is_written(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, "row1-s9", "0.10")
        self.assertFalse(os.path.exists(ledger_path(home)))

    def test_a_cap_that_is_not_an_exact_decimal_is_refused(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        for bad in (0.3, 1, "0.30", None):
            with self.assertRaises((TypeError, ValueError)):
                pc_spend.append_launch(home, ROW, S1, bad, VERSION, ALLOWED)
        for bad in (Decimal("-0.10"), Decimal("NaN"), Decimal("Infinity"), Decimal("0")):
            with self.assertRaises(ValueError):
                pc_spend.append_launch(home, ROW, S1, bad, VERSION, ALLOWED)
        self.assertFalse(os.path.exists(ledger_path(home)))

    def test_a_missing_or_empty_ledger_is_an_empty_history(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        self.assertEqual(pc_spend.read_records(home), [])
        write_raw(home, b"")
        self.assertEqual(pc_spend.read_records(home), [])
        self.assertEqual(pc_spend.attempts_used(home, S1), 0)
        self.assertEqual(launch(home, S1, "0.30"), 1)

    def test_a_malformed_ledger_is_refused_by_every_read_and_append_and_nothing_is_written(self) -> None:
        pc_spend = spend()
        good = json.dumps(
            {"attempt": 1, "cap": "0.30", "kind": "launch", "row": ROW, "stage": S1, "version": None},
            sort_keys=True,
        )
        bad_lines = [
            "not json at all",
            "[]",
            "{}",
            good.replace('"kind": "launch"', '"kind": "mystery"'),
            good.replace('"cap": "0.30"', '"cap": 0.3'),
            good.replace('"cap": "0.30"', '"cap": "-0.30"'),
            good.replace('"cap": "0.30"', '"cap": "abc"'),
            good.replace('"cap": "0.30"', '"cap": "1e1"'),
            good.replace('"cap": "0.30"', '"cap": "NaN"'),
            good.replace('"attempt": 1', '"attempt": 0'),
            good.replace('"attempt": 1', '"attempt": true'),
            good.replace('"attempt": 1', '"attempt": "1"'),
            good.replace('"stage": "row1-s1"', '"stage": "Row1 S1"'),
            good[:-1] + ', "extra": 1}',
            good.replace('"version": null', '"version": 5'),
            "",
        ]
        for line in bad_lines:
            home = scratch_home()
            write_raw(home, (line + "\n").encode("utf-8"))
            before = read_bytes(ledger_path(home))
            with self.assertRaises(pc_spend.SpendError, msg="a malformed ledger line was accepted"):
                pc_spend.read_records(home)
            with self.assertRaises(pc_spend.SpendError):
                launch(home, S2, "1.30")
            with self.assertRaises(pc_spend.SpendError):
                pc_spend.authorize_retry(home, ROW, S1, Decimal("0.30"), ALLOWED)
            self.assertEqual(read_bytes(ledger_path(home)), before)

    def test_a_ledger_without_a_final_newline_or_with_non_ascii_bytes_is_refused(self) -> None:
        pc_spend = spend()
        good = json.dumps(
            {"attempt": 1, "cap": "0.30", "kind": "launch", "row": ROW, "stage": S1, "version": None}, sort_keys=True
        )
        for data in (good.encode("ascii"), (good + "\n").encode("ascii") + b"\xff\xfe\n"):
            home = scratch_home()
            write_raw(home, data)
            with self.assertRaises(pc_spend.SpendError):
                pc_spend.read_records(home)

    def test_a_home_that_is_a_file_is_a_spend_error(self) -> None:
        pc_spend = spend()
        base = scratch_home()
        as_file = os.path.join(base, "not-a-folder")
        with open(as_file, "wb") as handle:
            handle.write(b"x")
        with self.assertRaises(pc_spend.SpendError):
            launch(as_file, S1, "0.30")


class AuthorizationTests(unittest.TestCase):
    def test_an_authorization_permits_exactly_one_more_attempt_of_that_stage(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        records = lines_of(home)
        self.assertEqual([r["kind"] for r in records], ["launch", "authorize"])
        self.assertEqual(sorted(records[1]), ["cap", "kind", "row", "stage"])
        self.assertEqual((records[1]["stage"], records[1]["cap"]), (S2, "1.30"))
        self.assertEqual(launch(home, S2, "1.30"), 2)
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, S2, "1.30")

    def test_the_authorization_is_per_stage(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        launch(home, S2, "1.30")
        pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, S1, "0.30")
        self.assertEqual(launch(home, S2, "1.30"), 2)

    def test_a_never_attempted_or_unknown_stage_cannot_be_authorized(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        with self.assertRaises(pc_spend.StageNotAttempted):
            pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        self.assertFalse(os.path.exists(ledger_path(home)), "a refused authorization created a ledger")
        launch(home, S1, "0.30")
        with self.assertRaises(pc_spend.StageNotAttempted):
            pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        with self.assertRaises(pc_spend.SpendRefused):
            pc_spend.authorize_retry(home, ROW, "row1-s9", Decimal("1.30"), ALLOWED)
        self.assertEqual([r["kind"] for r in lines_of(home)], ["launch"])
        self.assertTrue(issubclass(pc_spend.StageNotAttempted, pc_spend.SpendRefused))

    def test_a_second_authorization_before_the_retry_is_refused(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        with self.assertRaises(pc_spend.SpendRefused):
            pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), ALLOWED)
        self.assertEqual([r["kind"] for r in lines_of(home)], ["launch", "authorize"])

    def test_the_authorization_cap_must_be_an_exact_decimal(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        for bad in (1.3, 1, "1.30"):
            with self.assertRaises((TypeError, ValueError)):
                pc_spend.authorize_retry(home, ROW, S2, bad, ALLOWED)


class RowLimitTests(unittest.TestCase):
    def test_the_three_row_one_launches_total_exactly_two_and_are_all_accepted(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        launch(home, S2, "1.30")
        launch(home, S3, "0.40")
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("2.00"))
        self.assertEqual(pc_spend.ROW_CAP, Decimal("2.00"))

    def test_a_launch_above_the_row_limit_is_refused(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        allowed = ALLOWED + ("row1-s4",)
        launch(home, S1, "0.30", allowed)
        launch(home, S2, "1.30", allowed)
        launch(home, S3, "0.40", allowed)
        before = read_bytes(ledger_path(home))
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, "row1-s4", "0.01", allowed)
        self.assertEqual(read_bytes(ledger_path(home)), before)

    def test_a_settled_attempt_counts_its_delta_and_an_unsettled_one_its_cap(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        allowed = ALLOWED + ("row1-s4",)
        launch(home, S1, "0.30", allowed)
        launch(home, S2, "1.30", allowed)
        launch(home, S3, "0.40", allowed)
        pc_spend.settle(home, ROW, S1, 1, "success", Decimal("0.05"), Decimal("0.05"), VERSION)
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("1.75"))
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, "row1-s4", "0.26", allowed)
        self.assertEqual(launch(home, "row1-s4", "0.25", allowed), 1)
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("2.00"))

    def test_an_unsettled_attempt_without_a_result_keeps_its_cap(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        pc_spend.settle(home, ROW, S1, 1, "no-result", None, None, VERSION)
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("0.30"))

    def test_an_authorization_raises_the_limit_by_that_stage_cap_and_no_more(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        allowed = ALLOWED + ("row1-s4",)
        launch(home, S1, "0.30", allowed)
        launch(home, S2, "1.30", allowed)
        launch(home, S3, "0.40", allowed)
        pc_spend.authorize_retry(home, ROW, S2, Decimal("1.30"), allowed)
        self.assertEqual(launch(home, S2, "1.30", allowed), 2)
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("3.30"))
        with self.assertRaises(pc_spend.SpendRefused):
            launch(home, "row1-s4", "0.01", allowed)

    def test_another_row_has_its_own_total(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        pc_spend.append_launch(home, "row2-double-conflict", "row2-s1", Decimal("1.90"), VERSION, ("row2-s1",))
        self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("1.30"))
        self.assertEqual(pc_spend.row_pessimistic_total(home, "row2-double-conflict"), Decimal("1.90"))


class RaceTests(unittest.TestCase):
    def run_threads(self, jobs):
        gate = threading.Barrier(len(jobs))
        results: List[Any] = [None] * len(jobs)

        def work(index: int, job) -> None:
            gate.wait()
            try:
                results[index] = ("ok", job())
            except Exception as problem:  # noqa: BLE001 - the test classifies the outcome
                results[index] = ("error", problem)

        threads = [threading.Thread(target=work, args=(i, job)) for i, job in enumerate(jobs)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        return results

    def test_two_concurrent_launches_of_one_stage_give_exactly_one_winner(self) -> None:
        pc_spend = spend()
        for _round in range(5):
            home = scratch_home()
            results = self.run_threads([lambda: launch(home, S1, "0.30") for _ in range(6)])
            winners = [r for r in results if r[0] == "ok"]
            losers = [r for r in results if r[0] == "error"]
            self.assertEqual(len(winners), 1, "more or fewer than one launch won the race")
            for _kind, problem in losers:
                self.assertIsInstance(problem, pc_spend.SpendRefused)
            self.assertEqual(len([r for r in lines_of(home) if r["kind"] == "launch"]), 1)

    def test_concurrent_launches_of_different_stages_cannot_pass_the_row_limit_together(self) -> None:
        pc_spend = spend()
        allowed = ("row1-sa", "row1-sb", "row1-sc")
        for _round in range(5):
            home = scratch_home()
            jobs = [lambda stage=stage: launch(home, stage, "1.50", allowed) for stage in allowed]
            results = self.run_threads(jobs)
            self.assertEqual(len([r for r in results if r[0] == "ok"]), 1)
            self.assertEqual(pc_spend.row_pessimistic_total(home, ROW), Decimal("1.50"))


class CostTests(unittest.TestCase):
    def test_the_first_call_of_a_session_costs_its_own_total(self) -> None:
        pc_spend = spend()
        cost = pc_spend.call_cost(result_event("s2-stream.jsonl"))
        self.assertEqual(cost, Decimal("0.057689300000000006"))
        self.assertIsInstance(cost, Decimal)

    def test_a_resume_costs_its_delta_not_its_cumulative_total(self) -> None:
        pc_spend = spend()
        resumed = result_event("s2b-stream.jsonl")
        cost = pc_spend.call_cost(resumed)
        self.assertEqual(cost, Decimal("0.002608"))
        self.assertEqual(resumed["total_cost_usd"], Decimal("0.060297300000000005"))
        self.assertNotEqual(cost, resumed["total_cost_usd"])

    def test_the_delta_agrees_with_the_difference_of_the_two_cumulative_totals(self) -> None:
        pc_spend = spend()
        first = result_event("s2-stream.jsonl")
        resumed = result_event("s2b-stream.jsonl")
        difference = resumed["total_cost_usd"] - first["total_cost_usd"]
        self.assertLess(abs(pc_spend.call_cost(resumed) - difference), Decimal("0.000000001"))

    def test_without_a_per_call_breakdown_the_total_is_a_first_call_or_a_difference(self) -> None:
        pc_spend = spend()
        resumed = dict(result_event("s2b-stream.jsonl"))
        del resumed["model_usage_since_last_result"]
        self.assertEqual(pc_spend.call_cost(resumed), Decimal("0.060297300000000005"))
        first_total = result_event("s2-stream.jsonl")["total_cost_usd"]
        delta = pc_spend.call_cost(resumed, previous_total=first_total)
        self.assertEqual(delta, Decimal("0.060297300000000005") - Decimal("0.057689300000000006"))

    def test_a_result_with_no_usable_cost_is_refused(self) -> None:
        pc_spend = spend()
        for event in ({}, {"total_cost_usd": None}, {"total_cost_usd": True}, {"total_cost_usd": "abc"}):
            with self.assertRaises(pc_spend.SpendError):
                pc_spend.call_cost(event)

    def test_the_row_total_adds_each_session_chain_once(self) -> None:
        pc_spend = spend()
        total = pc_spend.row_total([Decimal("0.0900"), Decimal("0.0400")])
        self.assertEqual(total, Decimal("0.1300"))
        self.assertIsInstance(total, Decimal)
        self.assertEqual(pc_spend.row_total([]), Decimal("0"))
        # s1 is inside the cumulative total of the s2 chain: only the chain totals are summed.
        s1_total, s2_chain_total, s3_total = Decimal("0.0300"), Decimal("0.0900"), Decimal("0.0400")
        self.assertEqual(pc_spend.row_total([s2_chain_total, s3_total]), Decimal("0.1300"))
        self.assertNotEqual(pc_spend.row_total([s1_total, s2_chain_total, s3_total]), Decimal("0.1300"))

    def test_pc_spend_does_no_float_arithmetic(self) -> None:
        import ast

        with open(os.path.join(HARNESS_DIR, "pc_spend.py"), "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        floats = [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, float)]
        self.assertEqual(floats, [], "pc_spend.py holds a float literal")
        names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "float"]
        self.assertEqual(names, [], "pc_spend.py uses float")


class RecordTests(unittest.TestCase):
    def test_the_stage_key_is_the_row_prefix_and_the_stage_name(self) -> None:
        import pc_rows

        self.assertEqual(pc_rows.stage_key(ROW, "s2"), S2)

    def test_settle_appends_a_line_and_keeps_the_launch_line(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        pc_spend.settle(home, ROW, S2, 1, "success", Decimal("0.4000"), Decimal("0.5000"), VERSION)
        records = lines_of(home)
        self.assertEqual([r["kind"] for r in records], ["launch", "settle"])
        settle_line = records[1]
        self.assertEqual(
            sorted(settle_line), ["attempt", "cumulative", "delta", "kind", "row", "stage", "subtype", "version"]
        )
        self.assertEqual(
            (settle_line["subtype"], settle_line["delta"], settle_line["cumulative"], settle_line["attempt"]),
            ("success", "0.4000", "0.5000", 1),
        )
        self.assertEqual(pc_spend.attempts_used(home, S2), 1)

    def test_the_effective_record_of_an_attempt_is_the_latest_line_for_it(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S2, "1.30")
        pc_spend.settle(home, ROW, S2, 1, "error", None, None, VERSION)
        pc_spend.settle(home, ROW, S2, 1, "success", Decimal("0.40"), Decimal("0.50"), VERSION)
        effective = pc_spend.effective_records(pc_spend.read_records(home))
        self.assertEqual(list(effective), [(S2, 1)])
        self.assertEqual(effective[(S2, 1)]["kind"], "settle")
        self.assertEqual(effective[(S2, 1)]["delta"], Decimal("0.40"))

    def test_a_settle_for_an_attempt_that_was_never_launched_is_refused(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        before = read_bytes(ledger_path(home))
        with self.assertRaises(pc_spend.SpendError):
            pc_spend.settle(home, ROW, S1, 2, "success", Decimal("0.01"), Decimal("0.01"), VERSION)
        with self.assertRaises(pc_spend.SpendError):
            pc_spend.settle(home, ROW, S2, 1, "success", Decimal("0.01"), Decimal("0.01"), VERSION)
        self.assertEqual(read_bytes(ledger_path(home)), before)

    def test_settle_refuses_a_float_cost(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        with self.assertRaises((TypeError, ValueError)):
            pc_spend.settle(home, ROW, S1, 1, "success", 0.05, Decimal("0.05"), VERSION)
        with self.assertRaises((TypeError, ValueError)):
            pc_spend.settle(home, ROW, S1, 1, "success", Decimal("-0.05"), Decimal("0.05"), VERSION)

    def test_read_records_gives_decimal_costs(self) -> None:
        pc_spend = spend()
        home = scratch_home()
        launch(home, S1, "0.30")
        pc_spend.settle(home, ROW, S1, 1, "success", Decimal("0.0264"), Decimal("0.0264"), VERSION)
        records = pc_spend.read_records(home)
        self.assertEqual(records[0]["cap"], Decimal("0.30"))
        self.assertEqual(records[1]["delta"], Decimal("0.0264"))
        self.assertIsInstance(records[1]["cumulative"], Decimal)


if __name__ == "__main__":
    unittest.main()
