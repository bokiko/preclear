"""Zero-token tests for the matrix driver front door (plan 03-01; HARN-01, HARN-02).

No test starts a real claude. The only claude executed is a tripwire script written into a
temporary directory by pc_testutil. Every call that could reach a harness home passes its own
environment (a temporary PRECLEAR_HARNESS_HOME and HOME), so nothing here reads or writes the
user's real harness folder. Scratch folders come from tempfile.mkdtemp and are never deleted.

pc_rows and pc_matrix are imported inside each test, so a missing module is reported as one
error per test instead of a single load failure of the whole file.
"""
from __future__ import annotations

import datetime
import io
import os
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
MATRIX_SCRIPT = os.path.join(HARNESS_DIR, "pc_matrix.py")
HOME_ENV = "PRECLEAR_HARNESS_HOME"

LAYOUTS = ("plain-memory", "hub-memory", "bound-ledger")
ROWS = (
    "row1-wrong-binding",
    "row2-double-conflict",
    "row3a-missing-executable",
    "row3b-denied-helper-write",
    "row3c-unbound-fallback-none",
    "row4a-unknown-backend",
    "row4b-conflicting-blocks",
    "row5a-no-memory",
    "row5b-disabled-memory",
    "row6-readonly-plan",
    "row7-all-destinations-denied",
    "row8a-non-git",
    "row8b-detached-head",
    "row8c-unborn-branch",
    "row9-linked-worktree",
    "row10-large-status",
    "row11-concurrent-change",
    "row12-frozen-handoff",
)
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def scratch() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-matrix-"))


def cli_env(base: str, path_dirs, harness_home=None, extra=None) -> dict:
    env = {
        "PATH": os.pathsep.join(list(path_dirs) + list(pc_testutil.SYSTEM_DIRS)),
        "HOME": base,
        "LANG": "en_US.UTF-8",
        "PRECLEAR_RUNS_ROOT": scratch(),
    }
    if harness_home is not None:
        env[HOME_ENV] = harness_home
    if extra:
        env.update(extra)
    return env


def run_cli(args, env):
    proc = subprocess.run(
        [sys.executable, "-E", "-s", "-B", MATRIX_SCRIPT] + list(args),
        env=env,
        input=b"",
        capture_output=True,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def run_main(args, env, **kwargs):
    """Run pc_matrix.main in this process with an explicit environment; return (code, out, err)."""
    out = io.StringIO()
    err = io.StringIO()
    code = matrix().main(list(args), env=env, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def injected_row(row_id: str, caps, implemented: bool = True):
    """Build a registry entry for a test: one stage per cap, every stage in a new session."""
    pc_rows = rows()
    stages = tuple(
        pc_rows.StageSpec(
            "s%d" % (index + 1), "work turn", "work", 5, Decimal(cap), 60, "new:%s" % "ABCDEFGH"[index]
        )
        for index, cap in enumerate(caps)
    )
    return pc_rows.RowSpec(row_id, "row", "injected test row", stages, implemented, None, None, ())


class RegistryTests(unittest.TestCase):
    def test_three_layouts_and_eighteen_rows_in_acceptance_order(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.LAYOUT_IDS, LAYOUTS)
        self.assertEqual(pc_rows.ROW_IDS, ROWS)
        self.assertEqual(len(set(pc_rows.ROW_IDS)), 18)
        for identifier in LAYOUTS + ROWS:
            self.assertTrue(pc_rows.is_valid_id(identifier), "a registry id does not match the id pattern")
        registry = pc_rows.build_registry()
        self.assertEqual([entry.row_id for entry in registry], list(LAYOUTS + ROWS))
        self.assertEqual([entry.kind for entry in registry], ["layout"] * 3 + ["row"] * 18)

    def test_only_row_one_is_implemented_with_its_three_stages(self) -> None:
        pc_rows = rows()
        registry = pc_rows.build_registry()
        implemented = [entry.row_id for entry in registry if entry.implemented]
        self.assertEqual(implemented, ["row1-wrong-binding"])
        row1 = pc_rows.find_entry(registry, "row", "row1-wrong-binding")
        self.assertEqual([stage.name for stage in row1.stages], ["s1", "s2", "s3"])
        self.assertEqual([stage.max_turns for stage in row1.stages], [15, 60, 15])
        self.assertEqual([str(stage.cap) for stage in row1.stages], ["0.30", "1.30", "0.40"])
        self.assertEqual([stage.session for stage in row1.stages], ["new:A", "resume:A", "new:B"])
        for entry in registry:
            if not entry.implemented:
                self.assertEqual(entry.stages, ())

    def test_caps_are_exact_decimals_and_never_floats(self) -> None:
        pc_rows = rows()
        row1 = pc_rows.find_entry(pc_rows.build_registry(), "row", "row1-wrong-binding")
        for stage in row1.stages:
            self.assertIsInstance(stage.cap, Decimal)
        self.assertEqual(pc_rows.worst_case(row1), Decimal("2.00"))
        self.assertIsInstance(pc_rows.worst_case(row1), Decimal)
        self.assertEqual(pc_rows.session_count(row1), 2)
        self.assertEqual(pc_rows.ROW_CAP, Decimal("2.00"))
        self.assertIsInstance(pc_rows.ROW_CAP, Decimal)
        triple = injected_row("row0-three-caps", ("0.10", "0.10", "0.10"))
        self.assertEqual(pc_rows.worst_case(triple), Decimal("0.30"))
        self.assertEqual(str(pc_rows.worst_case(triple)), "0.30")
        self.assertEqual(pc_rows.session_count(triple), 3)

    def test_find_entry_matches_the_whole_id_only(self) -> None:
        pc_rows = rows()
        registry = pc_rows.build_registry()
        self.assertIsNotNone(pc_rows.find_entry(registry, "row", "row3a-missing-executable"))
        self.assertIsNone(pc_rows.find_entry(registry, "layout", "row3a-missing-executable"))
        self.assertIsNone(pc_rows.find_entry(registry, "row", "plain-memory"))
        for text in ("row3", "ROW1-WRONG-BINDING", "", "row1-wrong-binding ", None, 5):
            self.assertIsNone(pc_rows.find_entry(registry, "row", text))

    def test_stage_key_is_the_row_prefix_and_the_stage_name(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.stage_key("row1-wrong-binding", "s2"), "row1-s2")
        self.assertEqual(pc_rows.stage_key("row3a-missing-executable", "s1"), "row3a-s1")
        with self.assertRaises(ValueError):
            pc_rows.stage_key("Not A Row", "s1")

    def test_the_evidence_folder_name_carries_the_date_and_the_full_model_id(self) -> None:
        pc_rows = rows()
        self.assertEqual(
            pc_rows.evidence_folder_name("2026-10-28", pc_flags.PINNED_MODEL), "rerun-2026-10-28-claude-sonnet-5-5"
        )
        for bad_date in ("2026-1-28", "20261028", "2026-10-28 ", "", "2026-13-40", "26-10-28", "2026-10-28\n"):
            with self.assertRaises(ValueError):
                pc_rows.evidence_folder_name(bad_date, pc_flags.PINNED_MODEL)
        slash = "/"
        for bad_model in (
            "claude" + slash + "x",
            "claude..x",
            "claude x",
            "claude" + chr(233),
            "claude" + chr(7),
            "",
            "a" * 200,
        ):
            with self.assertRaises(ValueError):
                pc_rows.evidence_folder_name("2026-10-28", bad_model)


class ListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = scratch()
        cls.env = cli_env(cls.base, [], harness_home=os.path.join(cls.base, "h"))

    def test_the_list_has_a_header_and_twenty_one_fixed_column_lines(self) -> None:
        code, out, err = run_cli(["--list"], self.env)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(err, "")
        lines = out.splitlines()
        self.assertEqual(len(lines), 22)
        self.assertEqual(lines[0].split(), ["kind", "id", "stages", "sessions", "implemented"])
        body = [line.split() for line in lines[1:]]
        self.assertEqual([cells[1] for cells in body], list(LAYOUTS + ROWS))
        self.assertEqual([cells[0] for cells in body], ["layout"] * 3 + ["row"] * 18)
        for cells in body:
            self.assertEqual(len(cells), 5)
            if cells[1] == "row1-wrong-binding":
                self.assertEqual(cells[2:], ["3", "2", "yes"])
            else:
                self.assertEqual(cells[2:], ["-", "-", "no"])
        id_columns = {line.index(line.split()[1]) for line in lines}
        self.assertEqual(len(id_columns), 1, "the id column is not at a fixed position")

    def test_the_list_is_ascii_and_repeats_byte_for_byte(self) -> None:
        first = run_cli(["--list"], self.env)
        second = run_cli(["--list"], self.env)
        self.assertEqual(first, second)
        first[1].encode("ascii")
        self.assertFalse(os.path.exists(os.path.join(self.base, "h")))


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = scratch()
        cls.env = cli_env(cls.base, [], harness_home=os.path.join(cls.base, "h"))

    def refused(self, args, expect_text=None):
        code, out, err = run_main(args, self.env)
        self.assertEqual(code, pc_exitcodes.USAGE, "a selection was not refused with exit 2")
        self.assertEqual(out, "", "a refusal wrote to standard output")
        self.assertTrue(err.strip(), "a refusal printed nothing")
        if expect_text is not None:
            self.assertIn(expect_text, err)
        return err

    def test_an_unknown_row_is_refused_and_the_value_is_never_echoed(self) -> None:
        marker = "zz-probe-marker-91"
        err = self.refused(["--row", marker], "unknown row id")
        self.assertNotIn(marker, err)
        self.assertNotIn("probe", err)

    def test_near_misses_of_a_real_row_id_are_refused(self) -> None:
        near = (
            "row3",
            "row1-wrong-binding".upper(),
            "Row1-wrong-binding",
            "",
            "row1-wrong-binding ",
            " row1-wrong-binding",
            "row1-wrong-bindin",
            "row1-wrong-binding-",
            "row1_wrong_binding",
        )
        for value in near:
            err = self.refused(["--row", value], "unknown row id")
            self.assertNotIn("row1-wrong", err)

    def test_non_ascii_control_and_overlong_ids_are_refused(self) -> None:
        odd = (
            "row1-wrong-bindin" + chr(0x0121),
            "row1-wrong-binding" + chr(0x0301),
            "row1-wrong" + chr(7) + "-binding",
            "row1-wrong-binding" + chr(10),
            "a" * 64 + "b",
            "a" * 65,
        )
        for value in odd:
            err = self.refused(["--row", value], "unknown row id")
            self.assertNotIn("aaaaaaaa", err)
            self.assertNotIn(chr(7), err)

    def test_an_id_that_is_a_valid_shape_but_unknown_is_refused_for_layouts_too(self) -> None:
        err = self.refused(["--layout", "no-such-layout-zz"], "unknown layout name")
        self.assertNotIn("no-such-layout", err)
        self.refused(["--layout", "row1-wrong-binding"], "unknown layout name")
        self.refused(["--row", "plain-memory"], "unknown row id")
        self.refused(["--layout", ""], "unknown layout name")

    def test_a_known_but_unimplemented_entry_is_refused_with_its_own_text(self) -> None:
        err = self.refused(["--row", "row2-double-conflict"], "not implemented")
        self.assertNotIn("row2", err)
        err = self.refused(["--layout", "plain-memory", "--dry-run"], "not implemented")
        self.assertNotIn("plain-memory", err)
        self.refused(["--row", "row12-frozen-handoff", "--dry-run"], "not implemented")

    def test_selection_flag_combinations_are_refused(self) -> None:
        self.refused([])
        self.refused(["--list", "--all"])
        self.refused(["--row", "row1-wrong-binding", "--all"])
        self.refused(["--row", "row1-wrong-binding", "--layout", "plain-memory"])
        self.refused(["--dry-run", "--list"])
        self.refused(["--dry-run"])
        self.refused(["--bogus-option"])
        self.refused(["--row"])
        err = self.refused(["--row", "-" + "q" * 8])
        self.assertNotIn("qqqqqqqq", err)

    def test_the_command_line_refuses_with_exit_two_and_writes_nothing_to_standard_output(self) -> None:
        code, out, err = run_cli(["--row", "row3"], self.env)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("unknown row id", err)
        self.assertNotIn("row3", err)
        self.assertFalse(os.path.exists(os.path.join(self.base, "h")))


class DryRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = scratch()
        cls.bin = os.path.join(cls.base, "bin")
        os.makedirs(cls.bin)
        pc_testutil.make_tripwire(cls.bin)
        cls.home = os.path.join(cls.base, "h")
        cls.env = cli_env(cls.base, [cls.bin], harness_home=cls.home)

    # The gate refuses a destination that already exists (exit 17) and the repository holds a real
    # rerun folder, so every dry run here pins the clock to a date that has no folder.
    def run_ok(self, *args: str) -> str:
        code, out, err = run_main(list(args), self.env, clock=lambda: FIXED_DATE)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        return out

    def test_the_row_one_plan_prints_sessions_stages_caps_and_the_worst_case(self) -> None:
        out = self.run_ok("--dry-run", "--row", "row1-wrong-binding")
        self.assertIn("row1-wrong-binding: 3 stages, 2 sessions", out)
        stage_lines = [line for line in out.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
        self.assertEqual(len(stage_lines), 3)
        for line, (turns, cap) in zip(stage_lines, (("15", "0.30"), ("60", "1.30"), ("15", "0.40"))):
            self.assertIn("%s turns" % turns, line)
            self.assertIn("cap %s" % cap, line)
        self.assertIn("new session", stage_lines[0])
        self.assertIn("resum", stage_lines[1])
        self.assertIn("/preclear", stage_lines[1])
        self.assertIn("fresh resume", stage_lines[2])
        self.assertIn("worst case 2.00", out)
        self.assertIn("allowlist 40 rules", out)
        self.assertIn(pc_flags.PINNED_MODEL, out)
        self.assertIn("destination tests/evidence/rerun-", out)
        self.assertNotIn(self.base, out)
        self.assertNotIn(ROOT, out)

    def test_the_destination_name_uses_the_injected_clock(self) -> None:
        code, out, err = run_main(
            ["--dry-run", "--row", "row1-wrong-binding"], self.env, clock=lambda: FIXED_DATE
        )
        self.assertEqual(code, 0, err)
        self.assertIn("destination tests/evidence/rerun-2026-10-28-claude-sonnet-5-5", out)

    def test_dry_run_all_counts_only_the_implemented_rows(self) -> None:
        out = self.run_ok("--dry-run", "--all")
        self.assertIn("row1-wrong-binding: 3 stages, 2 sessions", out)
        for identifier in LAYOUTS + ROWS[1:]:
            self.assertIn("%s: not implemented" % identifier, out)
        totals = [line for line in out.splitlines() if line.startswith("total:")]
        self.assertEqual(totals, ["total: 1 row(s), 3 stage(s), 2 session(s), worst case 2.00 USD"])

    def test_an_empty_registry_has_zero_stages_and_zero_sessions(self) -> None:
        code, out, err = run_main(["--dry-run", "--all"], self.env, registry=())
        self.assertEqual(code, 0, err)
        last = out.strip().splitlines()[-1]
        self.assertEqual(last, "total: 0 row(s), 0 stage(s), 0 session(s), worst case 0.00 USD")

    def test_a_dry_run_with_an_injected_row_counts_its_exact_decimal_total(self) -> None:
        registry = rows().build_registry(extra=[injected_row("row0-three-caps", ("0.10", "0.10", "0.10"))])
        code, out, err = run_main(
            ["--dry-run", "--row", "row0-three-caps"], self.env, registry=registry, clock=lambda: FIXED_DATE
        )
        self.assertEqual(code, 0, err)
        self.assertIn("row0-three-caps: 3 stages, 3 sessions", out)
        self.assertIn("worst case 0.30", out)

    def test_a_dry_run_starts_no_process_of_any_kind_and_creates_nothing(self) -> None:
        with mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started")):
            for args in (["--dry-run", "--all"], ["--dry-run", "--row", "row1-wrong-binding"], ["--list"]):
                code, out, err = run_main(args, self.env, clock=lambda: FIXED_DATE)
                self.assertEqual(code, 0, err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])
        self.assertFalse(os.path.exists(self.home))
        self.assertFalse(os.path.exists(os.path.join(self.home, "matrix-spend.jsonl")))

    def test_a_real_run_without_a_budget_is_refused_with_exit_18_before_any_process(self) -> None:
        with mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started")):
            code, out, err = run_main(["--row", "row1-wrong-binding"], self.env, clock=lambda: FIXED_DATE)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED)
        self.assertIn("worst case 2.00", out)
        self.assertFalse(os.path.exists(self.home))


class AuthorizeRetryTests(unittest.TestCase):
    """--authorize-retry appends one ledger line, prints counts only and starts no process."""

    def setUp(self) -> None:
        self.base = scratch()
        self.bin = os.path.join(self.base, "bin")
        os.makedirs(self.bin)
        pc_testutil.make_tripwire(self.bin)
        self.home = os.path.join(self.base, "hh")
        self.env = cli_env(self.base, [self.bin], harness_home=self.home)

    def ledger(self) -> str:
        return os.path.join(self.home, "matrix-spend.jsonl")

    def record_attempt(self, stage: str = "row1-s2", cap: str = "1.30") -> None:
        import pc_spend

        pc_spend.append_launch(
            self.home, "row1-wrong-binding", stage, Decimal(cap), "2.1.310", ("row1-s1", "row1-s2", "row1-s3")
        )

    def kinds(self):
        import json

        with open(self.ledger(), "r", encoding="ascii") as handle:
            return [json.loads(line)["kind"] for line in handle.read().splitlines()]

    def test_a_recorded_stage_gets_exactly_one_authorization_line(self) -> None:
        os.makedirs(self.home)
        self.record_attempt()
        code, out, err = run_cli(["--authorize-retry", "row1-s2"], self.env)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.kinds(), ["launch", "authorize"])
        self.assertEqual(out.strip(), "authorized one more attempt of row1-s2")
        self.assertNotIn(self.base, out + err)
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])

    def test_a_second_authorization_before_the_retry_is_refused_with_exit_18(self) -> None:
        os.makedirs(self.home)
        self.record_attempt()
        self.assertEqual(run_main(["--authorize-retry", "row1-s2"], self.env)[0], 0)
        code, out, err = run_main(["--authorize-retry", "row1-s2"], self.env)
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, out + err)
        self.assertEqual(self.kinds(), ["launch", "authorize"])

    def test_a_never_attempted_stage_exits_2_and_creates_no_ledger(self) -> None:
        code, out, err = run_cli(["--authorize-retry", "row1-s2"], self.env)
        self.assertEqual(code, 2)
        self.assertIn("that stage has not been attempted", err)
        self.assertEqual(out, "")
        self.assertFalse(os.path.exists(self.ledger()))
        self.assertEqual(pc_testutil.read_tripwire(self.bin), [])

    def test_an_unknown_empty_or_odd_stage_key_exits_2_without_an_echo(self) -> None:
        os.makedirs(self.home)
        self.record_attempt()
        marker = "zzprobe-s7"
        odd = (marker, "row1-s9", "row9-s1", "", "row1-s2 ", "ROW1-S2", "row1-s" + chr(0x0662), "row1-s" + chr(7), "a" * 70)
        for value in odd:
            code, out, err = run_main(["--authorize-retry", value], self.env)
            self.assertEqual(code, pc_exitcodes.USAGE, "a bad stage key was not refused with exit 2")
            self.assertEqual(out, "")
            self.assertIn("unknown stage key", err)
            self.assertNotIn("zzprobe", err)
        self.assertEqual(self.kinds(), ["launch"])

    def test_the_flag_cannot_be_combined_with_another_selection_or_a_dry_run(self) -> None:
        os.makedirs(self.home)
        self.record_attempt()
        for extra in (["--list"], ["--all"], ["--row", "row1-wrong-binding"], ["--layout", "plain-memory"], ["--dry-run"]):
            code, out, err = run_main(["--authorize-retry", "row1-s2"] + extra, self.env)
            self.assertEqual(code, pc_exitcodes.USAGE)
        self.assertEqual(self.kinds(), ["launch"])

    def test_the_flag_starts_no_process_of_any_kind(self) -> None:
        os.makedirs(self.home)
        self.record_attempt()
        with mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started")):
            code, out, err = run_main(["--authorize-retry", "row1-s2"], self.env)
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
