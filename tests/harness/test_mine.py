"""Tests for the wrapper-log miner (STUB-03): inventory, ordering, empty cases, determinism.

Zero tokens: reads only committed files, writes nothing.
"""
from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MINER = os.path.join(HERE, "pc_mine.py")
COMMITTED = os.path.join(HERE, "replay-cases.json")
EVIDENCE = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")

EMPTY_ROWS = [
    "row3a-missing-executable",
    "row3a-missing-executable-rerun",
    "row4a-unknown-backend",
    "row4b-conflicting-blocks",
]


def load_miner():
    """Import pc_mine; the file existing is itself part of the behaviour under test."""
    assert os.path.isfile(MINER), "tests/harness/pc_mine.py does not exist"
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    return importlib.import_module("pc_mine")


class MineInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.miner = load_miner()
        cls.mined = cls.miner.mine(ROOT)

    def test_nine_logs_five_non_empty_fifteen_calls_four_empty(self) -> None:
        self.assertEqual(
            {"logs": 9, "non_empty": 5, "empty": 4, "calls": 15}, self.mined["inventory"]
        )
        self.assertEqual(1, self.mined["schema"])
        empty = [case["row"] for case in self.mined["cases"] if not case["calls"]]
        self.assertEqual(EMPTY_ROWS, empty)
        for row in EMPTY_ROWS:
            log = os.path.join(EVIDENCE, row, "wrapper-calls.log")
            self.assertEqual(0, os.path.getsize(log), row)

    def test_cases_are_in_byte_order_of_row_folder_name(self) -> None:
        rows = [case["row"] for case in self.mined["cases"]]
        self.assertEqual(sorted(rows, key=lambda name: name.encode("utf-8")), rows)
        self.assertEqual(9, len(set(rows)))

    def test_row2_sequence_and_recorded_exits(self) -> None:
        case = next(c for c in self.mined["cases"] if c["row"] == "row2-double-conflict")
        verbs = [call["argv"][0] for call in case["calls"]]
        exits = [call["exit"] for call in case["calls"]]
        self.assertEqual(["status", "show", "validate", "update", "show", "update"], verbs)
        self.assertEqual([0, 0, 0, 3, 0, 3], exits)
        self.assertEqual([1, 2, 3, 4, 5, 6], [call["position"] for call in case["calls"]])
        self.assertEqual(2, len(case["conflict_files"]))
        self.assertIsNotNone(case["writer2_session"])

    def test_row2_update_argv_is_recovered_with_shell_quoting(self) -> None:
        case = next(c for c in self.mined["cases"] if c["row"] == "row2-double-conflict")
        update = case["calls"][3]["argv"]
        self.assertEqual("--section", update[1])
        self.assertEqual("Goal & current state", update[2])
        self.assertEqual("--expect-section", update[3])
        self.assertEqual(".preclear/backend-inputs/goal.md", update[6])

    def test_expect_section_values_are_references_not_literal_hashes(self) -> None:
        case = next(c for c in self.mined["cases"] if c["row"] == "row2-double-conflict")
        for position in (3, 5):
            call = case["calls"][position]
            self.assertEqual("<last-show-hash>", call["argv"][4])
            self.assertEqual(
                [{"index": 4, "kind": "last-show", "section": "Goal & current state"}], call["refs"]
            )
            self.assertEqual(1, len(call["inputs"]))
            self.assertEqual(".preclear/backend-inputs/goal.md", call["inputs"][0]["replay_path"])
            self.assertTrue(
                os.path.isfile(os.path.join(ROOT, *call["inputs"][0]["source"].split("/")))
            )
        text = json.dumps(self.mined)
        self.assertIsNone(re.search(r"--expect-section\W+[0-9a-f]{64}", text))

    def test_rerun_input_path_with_run_token_maps_to_the_snapshot(self) -> None:
        case = next(c for c in self.mined["cases"] if c["row"] == "row3b-denied-helper-write-rerun")
        validate = case["calls"][2]
        self.assertEqual("validate", validate["argv"][0])
        self.assertEqual(".preclear/backend-inputs/block.md", validate["inputs"][0]["replay_path"])
        self.assertIn("snap-2-after-preclear/preclear/backend-inputs/block.md", validate["inputs"][0]["source"])

    def test_thirteen_calls_have_a_decisive_source_and_two_have_none(self) -> None:
        kinds = []
        for case in self.mined["cases"]:
            for call in case["calls"]:
                kinds.append((case["row"], call["position"], call["output"]["kind"]))
        self.assertEqual(15, len(kinds))
        none = [(row, pos) for row, pos, kind in kinds if kind == "none"]
        self.assertEqual([("row2-double-conflict", 3), ("row2-double-conflict", 4)], none)
        for _row, _pos, kind in kinds:
            self.assertIn(kind, ("status-before", "trace", "none"))

    def test_status_before_and_trace_sources_exist_on_disk(self) -> None:
        for case in self.mined["cases"]:
            for call in case["calls"]:
                output = call["output"]
                if output["kind"] != "none":
                    self.assertTrue(
                        os.path.isfile(os.path.join(ROOT, *output["path"].split("/"))), case["row"]
                    )

    def test_bound_ledger_and_unbound_case(self) -> None:
        by_row = {case["row"]: case for case in self.mined["cases"]}
        self.assertEqual("CONTINUITY_CLAUDE-other-task.md", by_row["row1-wrong-binding"]["bound_ledger"])
        self.assertEqual("CONTINUITY_CLAUDE-widget-export.md", by_row["row2-double-conflict"]["bound_ledger"])
        self.assertIsNone(by_row["row3c-unbound-fallback-none"]["bound_ledger"])
        self.assertEqual(
            ["CONTINUITY_CLAUDE-other-task.md", "CONTINUITY_CLAUDE-widget-export.md"],
            by_row["row1-wrong-binding"]["ledgers"],
        )


class ParseLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.miner = load_miner()

    def test_empty_log_is_zero_calls(self) -> None:
        self.assertEqual([], self.miner.parse_log(""))
        self.assertEqual([], self.miner.parse_log("\n"))

    def test_file_line_order_beats_timestamp_order(self) -> None:
        text = (
            "2026-10-19T23:11:03Z CALL show\n"
            "2026-10-19T23:11:03Z EXIT 0\n"
            "2026-10-19T23:11:01Z CALL status\n"
            "2026-10-19T23:11:01Z EXIT 3\n"
        )
        calls = self.miner.parse_log(text)
        self.assertEqual([["show"], ["status"]], [c["argv"] for c in calls])
        self.assertEqual([0, 3], [c["exit"] for c in calls])

    def test_two_calls_in_the_same_second_keep_their_order(self) -> None:
        text = (
            "2026-10-19T23:11:01Z CALL status\n2026-10-19T23:11:01Z EXIT 0\n"
            "2026-10-19T23:11:01Z CALL show\n2026-10-19T23:11:01Z EXIT 0\n"
        )
        self.assertEqual([["status"], ["show"]], [c["argv"] for c in self.miner.parse_log(text)])

    def test_bash_quoted_argv_round_trips(self) -> None:
        line = "2026-10-19T23:12:21Z CALL update --section Goal\\ \\&\\ current\\ state --from a\\ b.md\n"
        calls = self.miner.parse_log(line + "2026-10-19T23:12:21Z EXIT 3\n")
        self.assertEqual(
            ["update", "--section", "Goal & current state", "--from", "a b.md"], calls[0]["argv"]
        )
        self.assertEqual(3, calls[0]["exit"])

    def test_call_without_exit_is_refused(self) -> None:
        with self.assertRaises(self.miner.MineError):
            self.miner.parse_log("2026-10-19T23:11:01Z CALL status\n")
        with self.assertRaises(self.miner.MineError):
            self.miner.parse_log(
                "2026-10-19T23:11:01Z CALL status\n2026-10-19T23:11:02Z CALL show\n"
                "2026-10-19T23:11:02Z EXIT 0\n"
            )

    def test_exit_without_call_and_garbage_are_refused(self) -> None:
        with self.assertRaises(self.miner.MineError):
            self.miner.parse_log("2026-10-19T23:11:01Z EXIT 0\n")
        with self.assertRaises(self.miner.MineError):
            self.miner.parse_log("not a log line\n")
        with self.assertRaises(self.miner.MineError):
            self.miner.parse_log("2026-10-19T23:11:01Z CALL status\n2026-10-19T23:11:01Z EXIT x\n")


class DeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.miner = load_miner()

    def test_mining_twice_is_byte_identical_and_equals_the_committed_copy(self) -> None:
        first = self.miner.canonical_json(self.miner.mine(ROOT))
        second = self.miner.canonical_json(self.miner.mine(ROOT))
        self.assertEqual(first, second)
        with open(COMMITTED, "rb") as handle:
            self.assertEqual(handle.read(), first)

    def test_committed_file_is_canonical_json_and_not_a_log_name(self) -> None:
        self.assertFalse(COMMITTED.endswith(".log"))
        with open(COMMITTED, "rb") as handle:
            raw = handle.read()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertFalse(raw.endswith(b"\n\n"))
        raw.decode("ascii")
        data = json.loads(raw.decode("ascii"))
        again = (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")
        self.assertEqual(raw, again)

    def test_check_flag_exits_zero_and_bad_usage_exits_two(self) -> None:
        env = {"PATH": "/usr/bin:/bin"}
        base = [sys.executable, "-E", "-s", "-B", MINER]
        ok = subprocess.run(base + ["--check"], env=env, capture_output=True, cwd=ROOT)
        self.assertEqual(0, ok.returncode, ok.stderr.decode("utf-8", "replace"))
        bad = subprocess.run(base + ["--nonsense"], env=env, capture_output=True, cwd=ROOT)
        self.assertEqual(2, bad.returncode)
        listing = subprocess.run(base, env=env, capture_output=True, cwd=ROOT)
        self.assertEqual(0, listing.returncode)
        with open(COMMITTED, "rb") as handle:
            self.assertEqual(handle.read(), listing.stdout)


class WritesNothingTests(unittest.TestCase):
    def test_miner_contains_no_write_mode_open_and_no_write_helpers(self) -> None:
        self.assertTrue(os.path.isfile(MINER), "tests/harness/pc_mine.py does not exist")
        with open(MINER, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        found_open = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                if name == "open":
                    found_open += 1
                    modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)]
                    modes += [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
                    for mode in modes:
                        self.assertFalse(set(str(mode)) & set("wax+"), "write-mode open: %r" % mode)
                if name in ("write_text", "write_bytes", "mkdir", "makedirs", "rename", "replace", "remove", "unlink"):
                    self.fail("miner calls %s" % name)
        self.assertGreater(found_open, 0)

    def test_miner_imports_standard_library_only(self) -> None:
        with open(MINER, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        allowed = {"__future__", "json", "os", "re", "shlex", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0], allowed)
            if isinstance(node, ast.ImportFrom):
                self.assertIn((node.module or "").split(".")[0], allowed)


if __name__ == "__main__":
    unittest.main()
