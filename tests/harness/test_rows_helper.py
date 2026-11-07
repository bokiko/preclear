"""Zero-token tests for the helper-backed rows 2, 3a, 3b, 3c and 4b and the three layouts (plan 04-15; RERUN-02; D-04, D-13).

Row 2 runs the real checkpoint wrapper and the real stub from the scripted claude: after the work turn the harness arms
the wrapper, the model's first two updates to one section meet a genuine exit 3, and the wrapper's own files are expected
changes by exact name. The other helper rows are the row 1 seed with the committed difference of each row; the layouts
copy a frozen fixture project in place and print counts, names and digests. No test starts a real claude: the only claude
executed is the scripted fake written by pc_testutil. Folders come from RowRig and are never deleted. Modules are imported
inside small accessors so a missing module is one error per test, not one load failure of the file. Messages that name a
path are never asserted on by value; leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import re
import shlex
import tempfile
import unittest
import uuid
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_testutil
import test_wrapper_conflict as wrapper_rig
from test_row_generic import Registered, spec_of, tree_names

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
PUBLICATION = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")
DATA = os.path.join(HARNESS_DIR, "data")
ROW1 = "row1-wrong-binding"
ROW2 = "row2-double-conflict"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
LEDGER_A_NAME = "CONTINUITY_CLAUDE-widget-export.md"
LEDGER_B_NAME = "CONTINUITY_CLAUDE-other-task.md"
WRAPPER_MADE = (
    "wrapper/armed",
    "wrapper/target-section",
    "wrapper/injection.log",
    "wrapper/writer2-body-1.md",
    "wrapper/writer2-body-2.md",
)


def rows():
    import pc_rows

    return pc_rows


def row1():
    import pc_row1

    return pc_row1


def rowseeds():
    import pc_rowseeds

    return pc_rowseeds


def rowhooks():
    import pc_rowhooks

    return pc_rowhooks


def checks():
    import pc_checks

    return pc_checks


def evidence():
    import pc_evidence

    return pc_evidence


def matrix():
    import pc_matrix

    return pc_matrix


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path: str) -> str:
    return read_bytes(path).decode("utf-8")


def read_json(path: str):
    return json.loads(read_text(path))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed(folder: str, *parts: str) -> str:
    return os.path.join(PUBLICATION, folder, *parts)


def dry_run(*flags: str):
    """Run the driver's dry run for one selection with a tripwire claude first on the path; return (code, text, tripwire, base)."""
    base = os.path.realpath(tempfile.mkdtemp(prefix="pc-helper-dry-"))
    bin_dir = os.path.join(base, "bin")
    os.makedirs(bin_dir)
    pc_testutil.make_tripwire(bin_dir)
    env = {
        "PATH": os.pathsep.join([bin_dir] + list(pc_testutil.SYSTEM_DIRS)),
        "HOME": os.path.join(base, "home"),
        "PRECLEAR_HARNESS_HOME": os.path.join(base, "hh"),
        "PRECLEAR_RUNS_ROOT": os.path.join(base, "runs-root", "runs"),
        "LANG": "en_US.UTF-8",
    }
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started")):
        code = matrix().main(["--dry-run"] + list(flags), env=env, clock=lambda: FIXED_DATE, out=out, err=err)
    return code, out.getvalue() + err.getvalue(), pc_testutil.read_tripwire(bin_dir), base


def input_texts() -> dict:
    """The two input files the committed row 2 model wrote for its updates (the goal text and the block), read in place."""
    folder = committed("row2-double-conflict", "snap-2-after-preclear", "preclear", "backend-inputs")
    return {"goal": read_text(os.path.join(folder, "goal.md")), "block": read_text(os.path.join(folder, "block.md"))}


def wrapper_call(args: list) -> dict:
    """A scripted Bash call that really runs the wrapper with these arguments."""
    command = "$WRAPPER " + " ".join(shlex.quote(item) for item in args)
    return {"op": "tool", "name": "Bash", "input": {"command": command}, "run": "wrapper", "args": list(args)}


SECTION_HASH = "$HASH[" + wrapper_rig.GOAL + "]"  # the scripted claude reads the section hash the ledger holds at that moment


def row2_stages(extra_ops=()) -> list:
    """The scripted stages of a row 2 run: the default work turn and a /preclear turn that meets two real exit 3 results.

    The /preclear script reads the status and the ledger, writes its input files, validates the block, updates the goal
    section with the hash it just read (the wrapper has the second writer change that section first, so the stub returns
    exit 3), reads again, retries with the hash it reads then (exit 3 again), reads again and updates once more with the
    hash of that read (exit 0, the wrapper is spent). The rest of the default /preclear script follows. extra_ops are
    appended to the /preclear script.
    """
    texts = input_texts()
    inputs = wrapper_rig.INPUTS_REL
    goal_rel, block_rel = inputs + "/goal.md", inputs + "/block.md"
    name = wrapper_rig.GOAL
    update = wrapper_rig.update_args
    stages = pc_testutil.default_row_stages(spec_of(ROW2))
    opening = [
        wrapper_call(["status"]),
        wrapper_call(["show"]),
        {"op": "write", "path": "$PROJECT/" + block_rel, "text": texts["block"]},
        {"op": "write", "path": "$PROJECT/" + goal_rel, "text": texts["goal"]},
        wrapper_call(["validate", "--from", block_rel]),
        wrapper_call(update(name, SECTION_HASH, goal_rel)),
        wrapper_call(["show"]),
        wrapper_call(update(name, SECTION_HASH, goal_rel)),
        wrapper_call(["show"]),
        wrapper_call(update(name, SECTION_HASH, goal_rel)),
    ]
    rest = stages[1]["ops"][1:]  # everything after the default status call
    stages[1]["ops"] = opening + rest + list(extra_ops)
    return stages


def wrapper_exit_codes(run_root: str) -> list:
    """The exit codes of the wrapper log, one per call that reached an EXIT line, in order."""
    codes = []
    for line in read_text(os.path.join(run_root, "wrapper", "calls.log")).splitlines():
        found = re.search(r" EXIT ([0-9]+)$", line)
        if found:
            codes.append(int(found.group(1)))
    return codes


class Row2RegistryTests(unittest.TestCase):
    def test_row_2_is_registered_with_the_committed_two_stages_the_arm_hook_and_the_five_wrapper_names(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW2)
        self.assertTrue(spec.implemented)
        self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2"])
        self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60])
        self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30"])
        self.assertEqual([stage.session for stage in spec.stages], ["new:A", "resume:A"])
        self.assertEqual(pc_rows.session_count(spec), 1)
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_HELPER)
        self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
        self.assertEqual(spec.hooks, (("s1", "arm-wrapper-conflict"),))
        self.assertEqual(spec.analyses, ("wrapper-injection",))
        self.assertEqual(spec.expected_changes, WRAPPER_MADE)
        self.assertEqual(spec.expected_changes, checks().WRAPPER_MADE_NAMES, "the registry and the checks agree")
        self.assertEqual(dict(spec.prompts)["s1"], "tests/harness/data/row1-s1-prompt.md")
        self.assertEqual(dict(spec.prompts)["s2"], "tests/evidence/publication-2026-10-20/row2-double-conflict/s2-preclear-prompt.md")
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        for relative, kind in spec.sources:
            full = os.path.join(ROOT, *relative.split("/"))
            self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), relative)

    def test_a_spec_built_without_expected_changes_has_none(self) -> None:
        built = rows().RowSpec("row0-x", "row", "x", (), False, None, None, ())
        self.assertEqual(built.expected_changes, ())

    def test_the_dry_run_prints_two_stages_one_session_forty_rules_and_starts_nothing(self) -> None:
        code, text, tripwire, base = dry_run("--row", ROW2)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 2 stages, 1 sessions" % ROW2, text)
        self.assertIn("s1: work turn, new session, 15 turns, cap 0.30", text)
        self.assertIn("s2: /preclear turn, resumes the s1 session, 60 turns, cap 1.30", text)
        # The caps add up to 1.60: the plan text says 2.00 (the same plan defect as rows 4a, 5a, 5b and 6; plan 04-01 deviation 1).
        self.assertIn("worst case 1.60 USD", text)
        self.assertIn("allowlist 40 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")

    def test_list_marks_row_2_implemented(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        self.assertEqual(cells[ROW2][2:], ["2", "1", "yes"])


class ExpectedChangeNameTests(unittest.TestCase):
    def test_exactly_the_five_wrapper_names_are_accepted_in_any_order_and_subset(self) -> None:
        c = checks()
        self.assertEqual(c.validated_expected_changes([]), ())
        self.assertEqual(c.validated_expected_changes(list(WRAPPER_MADE)), WRAPPER_MADE)
        self.assertEqual(c.validated_expected_changes(["wrapper/injection.log", "wrapper/armed"]), ("wrapper/injection.log", "wrapper/armed"))

    def test_any_other_name_pattern_folder_repeat_or_shape_is_refused(self) -> None:
        c = checks()
        bad = [
            ["wrapper/other.txt"],
            ["wrapper/"],
            ["wrapper"],
            ["wrapper/*"],
            ["wrapper/armed/"],
            ["wrapper/../armed"],
            ["../wrapper/armed"],
            ["/wrapper/armed"],
            ["wrapper/calls.log"],
            ["project/armed"],
            ["wrapper/armed", "wrapper/armed"],
            list(WRAPPER_MADE) + ["wrapper/armed"],
            [None],
            [b"wrapper/armed"],
            "wrapper/armed",
            ("wrapper/armed",),
            {"wrapper/armed": 1},
            None,
        ]
        for value in bad:
            with self.assertRaises(c.CheckError, msg=repr(value)):
                c.validated_expected_changes(value)

    def test_outside_changes_skips_exactly_the_expected_names_and_nothing_else(self) -> None:
        c = checks()
        diff = [("added", "wrapper/armed"), ("added", "wrapper/other.txt"), ("changed", "wrapper/calls.log"), ("added", "stray.txt")]
        self.assertEqual(c.outside_changes(diff), ["stray.txt", "wrapper/armed", "wrapper/other.txt"])
        self.assertEqual(
            c.outside_changes(diff, c.APPROVED_ROOTS, c.EXPECTED_CHANGES + ("wrapper/armed",)), ["stray.txt", "wrapper/other.txt"]
        )


class Row2InjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ran = Registered(ROW2, stages=row2_stages())
        cls.root = cls.ran.run_root

    def test_the_chain_is_filed_and_the_wrapper_log_holds_the_two_exit_3_results_then_success(self) -> None:
        self.assertEqual(self.ran.outcome.code, pc_exitcodes.OK, self.ran.outcome.lines)
        # status, show, validate, update (3), show, update (3), show, update (0): the committed order.
        self.assertEqual(wrapper_exit_codes(self.root), [0, 0, 0, 3, 0, 3, 0, 0])

    def test_the_injection_log_holds_both_second_writer_updates_and_is_filed_with_the_row(self) -> None:
        text = read_text(os.path.join(self.root, "wrapper", "injection.log"))
        self.assertEqual(len(re.findall(r"(?m)^=== .* injection [12] to section \[Goal & current state\] as writer2 ", text)), 2)
        self.assertEqual(text.count("writer2 update exit 0"), 2)
        filed = os.path.join(self.ran.row_dir, "wrapper-injection.log")
        self.assertTrue(os.path.isfile(filed))
        self.assertEqual(read_text(filed).count("writer2 update exit 0"), 2)

    def test_the_second_writer_changed_the_ledger_twice_and_the_last_update_was_made_with_a_current_hash(self) -> None:
        snap0 = read_text(os.path.join(self.root, "snaps", "snap-0-setup", LEDGER_A_NAME))
        last = read_text(os.path.join(self.root, "snaps", "snap-2-after-preclear", LEDGER_A_NAME))
        self.assertNotEqual(snap0, last)
        injected = read_text(os.path.join(self.root, "wrapper", "injection.log"))
        self.assertEqual(injected.count("writer2 update exit 0"), 2, "the second writer changed the ledger twice")
        self.assertTrue(os.path.isfile(os.path.join(self.root, "wrapper", "writer2-body-2.md")))
        calls = read_text(os.path.join(self.root, "wrapper", "calls.log"))
        hashes = re.findall(r"--expect-section ([0-9a-f]{64})", calls)
        self.assertEqual(len(hashes), 3)
        self.assertEqual(len(set(hashes)), 3, "each update carried the hash the ledger held when it was read")
        self.assertEqual(wrapper_exit_codes(self.root)[-1], 0, "the last update, with a current hash, succeeded")

    def test_the_arm_hook_wrote_the_count_after_s1_and_before_s2(self) -> None:
        boundaries = [item["name"] for item in read_json(os.path.join(self.root, "raw", "boundaries.json"))["boundaries"]]
        self.assertEqual(boundaries, ["setup", "s1", "s1-arm-wrapper-conflict", "s2"])
        before = checks().load_manifest(os.path.join(self.root, "snaps", "snap-1-after-work"))
        armed = checks().load_manifest(os.path.join(self.root, "snaps", "snap-1b-after-arming"))
        self.assertNotIn("wrapper/armed", before)
        self.assertIn("wrapper/armed", armed)
        self.assertEqual(armed["wrapper/armed"]["sha256"], sha(b"2\n"), "the hook wrote the count 2")
        self.assertEqual(read_text(os.path.join(self.root, "wrapper", "armed")).strip(), "0", "the wrapper counted it down")

    def test_the_run_record_lists_the_five_names_and_the_bound_ledger_and_the_checks_find_no_write_outside(self) -> None:
        record = read_json(os.path.join(self.root, "raw", "run.json"))
        self.assertEqual(record["expected_changes"], list(WRAPPER_MADE))
        self.assertEqual(record["bound_ledger"], "A")
        facts = checks().compute_facts(self.root, self.ran.ctx.config_dir)
        self.assertEqual(facts["write_boundary"], {"count": 0, "paths": []})
        self.assertEqual(checks().breaches(facts), [])

    def test_the_wrapper_files_the_injection_made_are_in_the_final_manifest_and_all_are_expected(self) -> None:
        manifest = checks().load_manifest(os.path.join(self.root, "snaps", "snap-2-after-preclear"))
        made = sorted(path for path in manifest if path.startswith("wrapper/") and path in WRAPPER_MADE)
        self.assertEqual(made, sorted(WRAPPER_MADE))

    def test_the_status_questions_name_ledger_a_for_this_row(self) -> None:
        session = checks().compute_facts(self.root, self.ran.ctx.config_dir)["session"]
        self.assertEqual(session["status_names_ledger_a"], "yes")
        self.assertNotIn("status_names_ledger_b", session)
        text = read_text(os.path.join(self.ran.row_dir, "mechanical-checks.md"))
        self.assertIn("status-names-ledger-a: yes", text)
        self.assertNotIn("status-names-ledger-b", text)


class Row2BoundaryTests(unittest.TestCase):
    def test_a_scripted_write_to_another_name_under_the_wrapper_folder_ends_the_row_with_11(self) -> None:
        extra = [{"op": "write", "path": "$RUN/wrapper/other.txt", "text": "a model write\n"}]
        run = Registered(ROW2, stages=row2_stages(extra))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, run.outcome.lines)
        facts = checks().compute_facts(run.run_root, run.ctx.config_dir)
        self.assertEqual(facts["write_boundary"]["paths"], ["wrapper/other.txt"])
        self.assertEqual(checks().breaches(facts), [("writes-outside-approved-roots", 1)])

    def test_a_scripted_write_to_one_of_the_five_listed_names_is_not_counted(self) -> None:
        extra = [{"op": "write", "path": "$RUN/wrapper/writer2-body-1.md", "text": "rewritten\n"}]
        run = Registered(ROW2, stages=row2_stages(extra))
        self.assertEqual(run.outcome.code, pc_exitcodes.OK, run.outcome.lines)
        facts = checks().compute_facts(run.run_root, run.ctx.config_dir)
        self.assertEqual(facts["write_boundary"]["count"], 0)

    def test_a_run_record_that_lists_another_name_is_refused_by_the_checks(self) -> None:
        run = Registered(ROW2, stages=row2_stages())
        path = os.path.join(run.run_root, "raw", "run.json")
        record = read_json(path)
        record["expected_changes"] = ["wrapper/other.txt"]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle)
        with self.assertRaises(checks().CheckError):
            checks().compute_facts(run.run_root, run.ctx.config_dir)


class ArmHookTests(unittest.TestCase):
    def seeded(self):
        rig = pc_testutil.RowRig(stages=row2_stages())
        ctx = rig.context()
        run_root = rig.new_run_root(ctx, "arm-hook-case")
        paths = rowseeds().seed_row2(
            rig.repo, run_root, str(uuid.uuid4()), ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model
        )
        return paths, ctx

    def test_the_hook_creates_armed_exclusively_and_a_second_run_is_refused(self) -> None:
        paths, ctx = self.seeded()
        armed = os.path.join(str(paths["wrapper_dir"]), "armed")
        self.assertFalse(os.path.exists(armed))
        rowhooks().arm_wrapper_conflict(ctx, paths, spec_of(ROW2))
        self.assertEqual(read_bytes(armed), b"2\n")
        with self.assertRaises(rowhooks().HookRefused):
            rowhooks().arm_wrapper_conflict(ctx, paths, spec_of(ROW2))
        self.assertEqual(read_bytes(armed), b"2\n", "nothing was changed by the refused call")

    def test_a_planted_link_a_missing_second_writer_and_a_linked_wrapper_folder_are_refused(self) -> None:
        paths, ctx = self.seeded()
        wrapper_dir = str(paths["wrapper_dir"])
        os.symlink(os.path.join(wrapper_dir, "py"), os.path.join(wrapper_dir, "armed"))
        with self.assertRaises(rowhooks().HookRefused):
            rowhooks().arm_wrapper_conflict(ctx, paths, spec_of(ROW2))
        paths2, ctx2 = self.seeded()
        os.rename(os.path.join(str(paths2["wrapper_dir"]), "writer2.session"), os.path.join(str(paths2["wrapper_dir"]), "moved"))
        with self.assertRaises(rowhooks().HookRefused):
            rowhooks().arm_wrapper_conflict(ctx2, paths2, spec_of(ROW2))

    def test_the_hook_table_names_a_snapshot_a_boundary_and_no_finalizer_or_perms(self) -> None:
        h = rowhooks()
        self.assertEqual(h.HOOK_SNAPSHOTS["arm-wrapper-conflict"], "snap-1b-after-arming")
        self.assertEqual(h.TARGETS["arm-wrapper-conflict"], ())
        self.assertIn("arm-wrapper-conflict", h.NO_FINALIZER)
        self.assertIn("arm-wrapper-conflict", h.NO_PERMS)
        self.assertNotIn("arm-wrapper-conflict", h.NO_BOUNDARY)
        self.assertEqual(
            h.plan_boundaries(spec_of(ROW2)),
            [("setup", "snap-0-setup"), ("s1", "snap-1-after-work"), ("s1-arm-wrapper-conflict", "snap-1b-after-arming"), ("s2", "snap-2-after-preclear")],
        )


class SeededRow2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rig = pc_testutil.RowRig(stages=row2_stages())
        cls.ctx = cls.rig.context()
        cls.run_root = cls.rig.new_run_root(cls.ctx, "seed-row2")
        cls.session = str(uuid.uuid4())
        cls.paths = rowseeds().seed_row2(
            cls.rig.repo, cls.run_root, cls.session, cls.ctx.harness_home, cls.ctx.runs_root, cls.ctx.evidence_date, cls.ctx.model
        )

    def test_two_sessions_are_bound_to_the_one_ledger_and_the_second_id_is_in_the_wrapper_folder(self) -> None:
        ckpt = str(self.paths["ckpt"])
        bindings = sorted(os.listdir(os.path.join(ckpt, "bindings")))
        self.assertEqual(len(bindings), 2)
        writer2 = read_text(os.path.join(str(self.paths["wrapper_dir"]), "writer2.session")).strip()
        self.assertEqual(str(uuid.UUID(writer2)), writer2)
        self.assertNotEqual(writer2, self.session)
        names = [name for name in os.listdir(str(self.paths["ledgers"])) if not name.startswith(".")]
        self.assertEqual(names, [LEDGER_A_NAME], "one ledger, the configured one")
        self.assertFalse(os.path.exists(os.path.join(str(self.paths["wrapper_dir"]), "armed")), "armed only after s1")

    def test_the_seeded_configuration_differs_from_the_committed_fixture_only_in_the_four_values(self) -> None:
        seeded = read_text(os.path.join(str(self.paths["project"]), "CLAUDE.md")).split("\n")
        fixture = read_text(committed(ROW2, "fixture-CLAUDE.md")).split("\n")
        self.assertEqual(len(seeded), len(fixture))
        keys = ("executable", "project", "ledger", "fallback_directory")
        for line, base in zip(seeded, fixture):
            if line != base:
                self.assertTrue(line.strip().startswith(tuple(key + ":" for key in keys)), line)
        self.assertEqual(read_bytes(committed(ROW2, "fixture-CLAUDE.md")), read_bytes(committed(ROW1.replace("row1-wrong-binding", "row1-wrong-binding"), "fixture-CLAUDE.md")))

    def test_the_run_record_holds_the_five_names_and_ledger_a(self) -> None:
        record = read_json(os.path.join(str(self.paths["raw"]), "run.json"))
        self.assertEqual(record["row"], ROW2)
        self.assertEqual(record["bound_ledger"], "A")
        self.assertEqual(record["expected_changes"], list(WRAPPER_MADE))

    def test_a_seed_call_with_a_name_the_wrapper_does_not_create_is_refused(self) -> None:
        rig = pc_testutil.RowRig(stages=row2_stages())
        ctx = rig.context()
        run_root = rig.new_run_root(ctx, "seed-bad-name")
        with self.assertRaises(ValueError):
            rowseeds().seed_helper_row(
                rig.repo, run_root, str(uuid.uuid4()), ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model,
                ROW2, rowseeds().ROW2_FOLDER + "/fixture-CLAUDE.md",
                {"A": rowseeds().ROW2_FOLDER + "/snap-0-setup/" + LEDGER_A_NAME}, "A",
                expected_changes=["wrapper/other.txt"],
            )


class SessionFactsTests(unittest.TestCase):
    """The third status question names the ledger the session is bound to (plan 04-15; the row 1 shaped facts)."""

    def events(self):
        return [{"type": "system", "subtype": "init", "session_id": "sid"},
                {"type": "result", "subtype": "success", "is_error": False, "session_id": "sid", "permission_denials": []}]

    def ask(self, text, bound):
        return checks().session_facts({"s1": self.events()}, {"s1": "abcdefgh-1234"}, text, bound)

    def test_a_row_bound_to_ledger_a_asks_about_ledger_a_and_a_row_bound_to_b_asks_about_b(self) -> None:
        text = "brand\nsession abcdefgh\nledger: x/" + LEDGER_A_NAME + "\n"
        found = self.ask(text, "A")
        self.assertEqual(found["status_names_ledger_a"], "yes")
        self.assertNotIn("status_names_ledger_b", found)
        found = self.ask(text, "B")
        self.assertEqual(found["status_names_ledger_b"], "no")
        self.assertNotIn("status_names_ledger_a", found)
        other = "brand\nsession abcdefgh\nledger: x/" + LEDGER_B_NAME + "\n"
        self.assertEqual(self.ask(other, "B")["status_names_ledger_b"], "yes")
        self.assertEqual(self.ask(other, "A")["status_names_ledger_a"], "no")

    def test_the_default_is_the_phase_3_question_about_ledger_b(self) -> None:
        text = "brand\nsession abcdefgh\nledger: x/" + LEDGER_B_NAME + "\n"
        found = checks().session_facts({"s1": self.events()}, {"s1": "abcdefgh-1234"}, text)
        self.assertEqual(found["status_names_ledger_b"], "yes")
        self.assertEqual(sorted(key for key in found if key.startswith("status")), ["status_begins_with_session", "status_holds_s1_prefix", "status_names_ledger_b"])

    def test_no_binding_keeps_the_third_question_unconfirmed_under_its_old_key_and_asks_the_other_two(self) -> None:
        found = self.ask("brand\nsession abcdefgh\nno ledger\n", "none")
        self.assertEqual(found["status_names_ledger_b"], "UNCONFIRMED")
        self.assertNotIn("status_names_ledger_a", found)
        self.assertEqual(found["status_begins_with_session"], "yes")
        self.assertEqual(found["status_holds_s1_prefix"], "yes")

    def test_no_status_call_makes_all_three_unconfirmed_for_every_binding(self) -> None:
        for bound, key in (("A", "status_names_ledger_a"), ("B", "status_names_ledger_b"), ("none", "status_names_ledger_b")):
            found = self.ask(None, bound)
            for name in ("status_begins_with_session", "status_holds_s1_prefix", key):
                self.assertEqual(found[name], "UNCONFIRMED", (bound, name))

    def test_an_unknown_binding_word_is_refused(self) -> None:
        with self.assertRaises(checks().CheckError):
            self.ask("text", "C")

    def test_the_helper_key_is_found_in_a_facts_mapping(self) -> None:
        c = checks()
        self.assertEqual(c.status_ledger_key({"status_names_ledger_a": "yes"}), "status_names_ledger_a")
        self.assertEqual(c.status_ledger_key({"status_names_ledger_b": "yes"}), "status_names_ledger_b")

    def test_the_scripted_row_1_chain_prints_the_phase_3_status_lines_unchanged(self) -> None:
        run = Registered(ROW1, stages=pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, pc_exitcodes.OK, run.outcome.lines)
        text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
        lines = text.splitlines()
        start = lines.index("status-begins-with-session: yes")
        self.assertEqual(
            lines[start:start + 3],
            ["status-begins-with-session: yes", "status-holds-s1-prefix: yes", "status-names-ledger-b: yes"],
        )
        self.assertNotIn("status-names-ledger-a", text)



# ---------------------------------------------------------------------------------------------
# Rows 3a, 3b, 3c and 4b (plan 04-15, task 2)
# ---------------------------------------------------------------------------------------------

ROW3A = "row3a-missing-executable"
ROW3B = "row3b-denied-helper-write"
ROW3C = "row3c-unbound-fallback-none"
ROW4B = "row4b-conflicting-blocks"
# The committed folder each row's fixture and /preclear prompt come from (3a and 3b read the rerun folders).
COMMITTED_FOLDER = {
    ROW2: "row2-double-conflict",
    ROW3A: "row3a-missing-executable-rerun",
    ROW3B: "row3b-denied-helper-write-rerun",
    ROW3C: "row3c-unbound-fallback-none",
    ROW4B: "row4b-conflicting-blocks",
}
HELPER_ROWS = (ROW2, ROW3A, ROW3B, ROW3C, ROW4B)
ALLOWLIST_SIZE = {ROW2: 40, ROW3A: 40, ROW3B: 37, ROW3C: 40, ROW4B: 40}
CONFIG_KEYS = ("executable", "project", "ledger", "fallback_directory")
SHAPED = re.compile(r"(^|[\s(`\"'=])(/[A-Za-z0-9_.-]+/|~/|[A-Za-z]:\\)|@[A-Za-z0-9-]+\.[A-Za-z]|://")


def seed_of(row_id: str):
    return row1()._resolve_seed(spec_of(row_id).seed)


class SeededRow(object):
    """A rig, a fresh run root and the paths the seed of a registered row or layout returns."""

    def __init__(self, row_id: str, name: str = "helper-seed-case") -> None:
        self.row_id = row_id
        self.rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(row_id)))
        self.ctx = self.rig.context()
        self.run_root = self.rig.new_run_root(self.ctx, name)
        self.session = str(uuid.uuid4())
        self.paths = seed_of(row_id)(
            self.rig.repo, self.run_root, self.session, self.ctx.harness_home, self.ctx.runs_root, self.ctx.evidence_date, self.ctx.model
        )

    @property
    def project(self) -> str:
        return str(self.paths["project"])

    def record(self) -> dict:
        return read_json(os.path.join(str(self.paths["raw"]), "run.json"))

    def listing(self, folder: str) -> list:
        path = os.path.join(self.run_root, *folder.split("/"))
        return sorted(name for name in os.listdir(path) if not name.startswith(".")) if os.path.isdir(path) else []


def differing_lines(seeded: str, fixture: str) -> list:
    """The line numbers (from 1) at which two texts differ; the texts must have the same number of lines."""
    first, second = seeded.split("\n"), fixture.split("\n")
    assert len(first) == len(second), "the seeded and committed files must have the same number of lines"
    return [number for number, (one, two) in enumerate(zip(first, second), 1) if one != two]


def value_of(text: str, key: str) -> str:
    found = re.search(r"(?m)^\s*%s: (.*)$" % re.escape(key), text)
    assert found, key
    return found.group(1)


def assert_only_the_four_values_differ(case: unittest.TestCase, seeded: str, fixture: str) -> list:
    """Every differing line of the seeded file is a line of one of the four configuration keys; return those keys."""
    keys = []
    seeded_lines, fixture_lines = seeded.split("\n"), fixture.split("\n")
    for number in differing_lines(seeded, fixture):
        stripped = seeded_lines[number - 1].strip()
        key = stripped.split(":", 1)[0]
        case.assertIn(key, CONFIG_KEYS, "line %d differs and is not a configuration value" % number)
        case.assertEqual(fixture_lines[number - 1].strip().split(":", 1)[0], key)
        keys.append(key)
    return keys


class HelperRowSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = dict((row_id, SeededRow(row_id, "seed-" + row_id.split("-", 1)[0])) for row_id in HELPER_ROWS)

    def committed(self, row_id: str, *parts: str) -> str:
        return committed(COMMITTED_FOLDER[row_id], *parts)

    def test_every_helper_row_has_one_ledger_the_configured_one_and_a_working_wrapper(self) -> None:
        for row_id in HELPER_ROWS:
            seeded = self.seeded[row_id]
            self.assertEqual(seeded.listing("ckpt/ledgers"), [LEDGER_A_NAME], row_id)
            self.assertTrue(os.path.isfile(os.path.join(str(seeded.paths["wrapper_dir"]), "checkpoint")), row_id)
            self.assertEqual(seeded.record()["row"], row_id)

    def test_each_seeded_claude_md_differs_from_its_committed_fixture_only_in_the_four_values(self) -> None:
        for row_id in HELPER_ROWS:
            seeded = read_text(os.path.join(self.seeded[row_id].project, "CLAUDE.md"))
            fixture = read_text(self.committed(row_id, "fixture-CLAUDE.md"))
            keys = assert_only_the_four_values_differ(self, seeded, fixture)
            self.assertEqual(sorted(set(keys)), sorted(set(keys)), row_id)
            self.assertLessEqual(len(keys), 4, row_id)
            for key in CONFIG_KEYS:
                self.assertNotIn("<repo>", value_of(seeded, key), row_id + " " + key)

    def test_rows_2_3b_and_4b_are_on_row_1_text_and_3a_and_3c_differ_from_it_in_one_value_each(self) -> None:
        base = read_bytes(committed("row1-wrong-binding", "fixture-CLAUDE.md"))
        for row_id in (ROW2, ROW3B, ROW4B):
            self.assertEqual(read_bytes(self.committed(row_id, "fixture-CLAUDE.md")), base, row_id)
        for row_id, key in ((ROW3A, "executable"), (ROW3C, "fallback_directory")):
            text = read_text(self.committed(row_id, "fixture-CLAUDE.md"))
            keys = assert_only_the_four_values_differ(self, text, base.decode("utf-8"))
            self.assertEqual(keys, [key], row_id)

    def test_3a_names_an_executable_that_does_not_exist_beside_the_working_wrapper(self) -> None:
        seeded = self.seeded[ROW3A]
        text = read_text(os.path.join(seeded.project, "CLAUDE.md"))
        executable = value_of(text, "executable")
        self.assertEqual(executable, os.path.join(str(seeded.paths["wrapper_dir"]), "missing-checkpoint"))
        self.assertFalse(os.path.lexists(executable))
        self.assertTrue(os.path.isfile(str(seeded.paths["wrapper"])))
        self.assertEqual(os.path.dirname(executable), str(seeded.paths["wrapper_dir"]))
        self.assertEqual(seeded.record()["bound_ledger"], "A")
        self.assertEqual(len(seeded.listing("ckpt/bindings")), 1)

    def test_3c_has_the_word_none_as_fallback_and_no_binding_at_all(self) -> None:
        seeded = self.seeded[ROW3C]
        text = read_text(os.path.join(seeded.project, "CLAUDE.md"))
        self.assertEqual(value_of(text, "fallback_directory"), "none")
        self.assertEqual(seeded.record()["bound_ledger"], "none")
        self.assertFalse(os.path.lexists(os.path.join(str(seeded.paths["ckpt"]), "bindings")), "no bindings folder")
        calls = read_text(os.path.join(str(seeded.paths["wrapper_dir"]), "calls.log"))
        self.assertEqual(calls, "", "the harness never called the wrapper, and so no bind either")
        self.assertEqual(value_of(text, "task"), "widget-export")

    def test_4b_adds_a_local_file_that_differs_from_its_committed_fixture_only_in_the_four_values(self) -> None:
        seeded = self.seeded[ROW4B]
        local = read_text(os.path.join(seeded.project, "CLAUDE.local.md"))
        fixture = read_text(self.committed(ROW4B, "fixture-CLAUDE.local.md"))
        keys = assert_only_the_four_values_differ(self, local, fixture)
        self.assertLessEqual(len(keys), 3)
        self.assertEqual(value_of(local, "task"), "widget-export-v2")
        self.assertEqual(value_of(local, "fallback_directory"), "none")
        self.assertEqual(value_of(local, "executable"), str(seeded.paths["wrapper"]))
        self.assertEqual(value_of(local, "ledger"), str(seeded.paths["ledger_a"]))
        main = read_text(os.path.join(seeded.project, "CLAUDE.md"))
        self.assertEqual(value_of(main, "task"), "widget-export")
        self.assertNotEqual(value_of(main, "fallback_directory"), "none")
        self.assertEqual(seeded.record()["bound_ledger"], "A")

    def test_only_row_4b_has_a_local_file_and_the_local_file_is_committed_with_the_base(self) -> None:
        for row_id in HELPER_ROWS:
            exists = os.path.isfile(os.path.join(self.seeded[row_id].project, "CLAUDE.local.md"))
            self.assertEqual(exists, row_id == ROW4B, row_id)
        tracked = checks_git(self.seeded[ROW4B].project, "ls-files", "CLAUDE.local.md")
        self.assertEqual(tracked.strip(), "CLAUDE.local.md")

    def test_only_row_2_has_a_second_writer_and_only_row_2_lists_expected_changes(self) -> None:
        for row_id in HELPER_ROWS:
            seeded = self.seeded[row_id]
            has_writer = os.path.isfile(os.path.join(str(seeded.paths["wrapper_dir"]), "writer2.session"))
            self.assertEqual(has_writer, row_id == ROW2, row_id)
            self.assertEqual(seeded.record()["expected_changes"], list(WRAPPER_MADE) if row_id == ROW2 else [], row_id)

    def test_the_committed_row_3_and_4b_prompts_are_the_shared_s2_prompt_read_in_place(self) -> None:
        shared = read_bytes(committed("row1-wrong-binding", "s2-preclear-prompt.md"))
        for row_id in HELPER_ROWS:
            self.assertEqual(read_bytes(self.committed(row_id, "s2-preclear-prompt.md")), shared, row_id)
            path = dict(spec_of(row_id).prompts)["s2"]
            self.assertEqual(path, "tests/evidence/publication-2026-10-20/%s/s2-preclear-prompt.md" % COMMITTED_FOLDER[row_id])
            self.assertEqual(dict(spec_of(row_id).prompts)["s1"], "tests/harness/data/row1-s1-prompt.md")


def checks_git(folder: str, *args: str) -> str:
    import subprocess

    env = pc_testutil.git_env({"PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS)})
    done = subprocess.run(["git", "-C", folder] + list(args), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert done.returncode == 0, args
    return done.stdout.decode("utf-8")


class HelperAllowlistTests(unittest.TestCase):
    def rules(self, row_id: str, wrapper: str = "/run/wrapper/checkpoint") -> tuple:
        spec = spec_of(row_id)
        return row1().allowed_tools(spec.tools_profile, wrapper, spec.extra_tools)

    def test_row_3b_has_37_rules_the_baseline_plus_the_four_read_verbs_and_the_others_have_40(self) -> None:
        import pc_flags

        for row_id, size in ALLOWLIST_SIZE.items():
            self.assertEqual(len(self.rules(row_id)), size, row_id)
        wrapper = "/run/wrapper/checkpoint"
        rules = self.rules(ROW3B, wrapper)
        self.assertEqual(rules[: len(pc_flags.BASELINE_ALLOWED_TOOLS)], tuple(pc_flags.BASELINE_ALLOWED_TOOLS))
        self.assertEqual(
            rules[len(pc_flags.BASELINE_ALLOWED_TOOLS):],
            tuple("Bash(%s %s:*)" % (wrapper, verb) for verb in ("status", "show", "validate", "lint")),
        )
        for verb in ("update", "note", "handoff"):
            self.assertFalse([rule for rule in rules if rule.startswith("Bash(%s %s" % (wrapper, verb))], verb)

    def test_every_helper_profile_row_lists_wrapper_rules_by_verb_and_never_a_bare_prefix_or_a_driver_verb(self) -> None:
        import pc_flags

        wrapper = "/run/wrapper/checkpoint"
        for row_id in (ROW1, ROW2, ROW3A, ROW3B, ROW3C, "row4a-unknown-backend", ROW4B):
            own = [rule for rule in self.rules(row_id, wrapper) if wrapper in rule]
            self.assertTrue(own, row_id)
            for rule in own:
                found = re.match(r"Bash\(%s ([a-z]+):\*\)\Z" % re.escape(wrapper), rule)
                self.assertIsNotNone(found, row_id + " a wrapper rule is not by verb: " + rule)
                self.assertIn(found.group(1), pc_flags.MODEL_FACING_WRAPPER_VERBS)
                self.assertNotIn(found.group(1), pc_flags.DRIVER_ONLY_VERBS)
            self.assertNotIn("Bash(%s:*)" % wrapper, self.rules(row_id, wrapper), row_id)

    def test_the_profile_words_agree_between_the_registry_and_the_flag_builder(self) -> None:
        import pc_flags

        pc_rows = rows()
        self.assertEqual(pc_rows.PROFILE_HELPER_READ, pc_flags.PROFILE_HELPER_READ)
        self.assertEqual(spec_of(ROW3B).tools_profile, pc_rows.PROFILE_HELPER_READ)
        for row_id in (ROW2, ROW3A, ROW3C, ROW4B):
            self.assertEqual(spec_of(row_id).tools_profile, pc_rows.PROFILE_HELPER)
        with self.assertRaises(ValueError):
            pc_flags.build_row_tools("helper-write", "/run/wrapper/checkpoint")

    def test_the_read_profile_takes_extra_rules_like_the_others_and_refuses_a_repeat(self) -> None:
        import pc_flags

        wrapper = "/run/wrapper/checkpoint"
        plus = pc_flags.build_row_tools(pc_flags.PROFILE_HELPER_READ, wrapper, ("Bash(touch:*)",))
        self.assertEqual(len(plus), 38)
        with self.assertRaises(ValueError):
            pc_flags.build_row_tools(pc_flags.PROFILE_HELPER_READ, wrapper, ("Bash(touch:*)", "Bash(touch:*)"))
        self.assertEqual(len(pc_flags.build_row_tools(pc_flags.PROFILE_HELPER_READ, wrapper)), 37)

    def test_the_dry_runs_print_two_stages_one_session_and_the_right_allowlist_size_and_start_nothing(self) -> None:
        for row_id in (ROW3A, ROW3B, ROW3C, ROW4B):
            code, text, tripwire, base = dry_run("--row", row_id)
            self.assertEqual(code, 0, text)
            self.assertIn("%s: 2 stages, 1 sessions" % row_id, text)
            self.assertIn("allowlist %d rules" % ALLOWLIST_SIZE[row_id], text)
            self.assertIn("s1: work turn, new session, 15 turns, cap 0.30", text)
            self.assertIn("s2: /preclear turn, resumes the s1 session, 60 turns, cap 1.30", text)
            self.assertIn("worst case 1.60 USD", text)
            self.assertEqual(tripwire, [], row_id)
            self.assertFalse(os.path.exists(os.path.join(base, "hh")), row_id)


class HelperRegistryTests(unittest.TestCase):
    def test_every_helper_row_is_registered_with_two_stages_memory_pinned_and_a_harness_worded_setup(self) -> None:
        pattern = evidence().verdict_pattern()
        for row_id in HELPER_ROWS:
            spec = spec_of(row_id)
            self.assertTrue(spec.implemented, row_id)
            self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2"], row_id)
            self.assertEqual(spec.memory, rows().MEMORY_PINNED, row_id)
            self.assertEqual(spec.chain, rows().CHAIN_RESUME_LINE, row_id)
            self.assertTrue(spec.setup_text.startswith("Setup: "), row_id)
            self.assertTrue(spec.setup_text.isascii(), row_id)
            self.assertIsNone(SHAPED.search(spec.setup_text), row_id)
            self.assertEqual(pattern.findall(spec.setup_text), [], row_id)
            self.assertEqual(spec.seed, "pc_rowseeds:seed_" + row_id.split("-", 1)[0], row_id)
            for relative, kind in spec.sources:
                full = os.path.join(ROOT, *relative.split("/"))
                self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), relative)
            if row_id != ROW2:
                self.assertEqual((spec.hooks, spec.analyses, spec.expected_changes), ((), (), ()), row_id)

    def test_the_local_fixture_of_row_4b_is_a_source_and_no_other_row_names_one(self) -> None:
        for row_id in HELPER_ROWS:
            named = [relative for relative, _kind in spec_of(row_id).sources if relative.endswith("fixture-CLAUDE.local.md")]
            self.assertEqual(len(named), 1 if row_id == ROW4B else 0, row_id)

    def test_list_marks_the_five_helper_rows_implemented_with_two_stages_and_one_session(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        for row_id in HELPER_ROWS:
            self.assertEqual(cells[row_id][2:], ["2", "1", "yes"], row_id)

    def test_the_setup_texts_state_each_committed_difference(self) -> None:
        self.assertIn("missing-checkpoint", spec_of(ROW3A).setup_text)
        self.assertIn("update", spec_of(ROW3B).setup_text)
        self.assertIn("never bound", spec_of(ROW3C).setup_text)
        self.assertIn("CLAUDE.local.md", spec_of(ROW4B).setup_text)
        self.assertIn("second session", spec_of(ROW2).setup_text)


class HelperChainTests(unittest.TestCase):
    """A scripted two-stage chain of each of the four rows runs through the engine and files its folder."""

    def chain(self, row_id: str) -> Registered:
        run = Registered(row_id)
        self.assertEqual(run.outcome.code, pc_exitcodes.OK, "\n".join(run.outcome.lines))
        return run

    def test_each_row_is_filed_with_its_readme_checks_and_the_pending_verdict_line(self) -> None:
        for row_id in (ROW3A, ROW3B, ROW3C, ROW4B):
            run = self.chain(row_id)
            names = tree_names(run.row_dir)
            for name in ("README.md", "mechanical-checks.md", "tools.txt", "wrapper-calls.log", "s1.exit", "s2-preclear.exit"):
                self.assertIn(name, names, row_id + " " + name)
            self.assertNotIn("wrapper-injection.log", names, row_id)
            readme = read_text(os.path.join(run.row_dir, "README.md"))
            self.assertTrue(readme.rstrip("\n").endswith("Reviewer verdict: PENDING"), row_id)
            self.assertIn(spec_of(row_id).setup_text, readme, row_id)

    def test_the_filed_allowlist_has_the_row_size_and_row_3b_names_only_the_read_verbs(self) -> None:
        for row_id in (ROW3A, ROW3B, ROW3C, ROW4B):
            run = self.chain(row_id)
            rules = read_text(os.path.join(run.row_dir, "tools.txt")).strip().split(",")
            self.assertEqual(len(rules), ALLOWLIST_SIZE[row_id], row_id)
            wrapper_rules = [rule for rule in rules if "/wrapper/checkpoint " in rule]
            verbs = sorted(re.findall(r"checkpoint ([a-z]+):\*\)", "\n".join(wrapper_rules)))
            if row_id == ROW3B:
                self.assertEqual(verbs, ["lint", "show", "status", "validate"])
            else:
                self.assertEqual(verbs, ["handoff", "lint", "note", "show", "status", "update", "validate"], row_id)

    def test_the_run_records_name_the_binding_and_the_status_question_follows_it(self) -> None:
        expected = {ROW3A: ("A", "status-names-ledger-a"), ROW3B: ("A", "status-names-ledger-a"),
                    ROW3C: ("none", "status-names-ledger-b"), ROW4B: ("A", "status-names-ledger-a")}
        for row_id, (bound, key) in expected.items():
            run = self.chain(row_id)
            self.assertEqual(read_json(run.raw("run.json"))["bound_ledger"], bound, row_id)
            text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
            self.assertIn(key + ": ", text, row_id)
            if row_id == ROW3C:
                self.assertIn("status-names-ledger-b: UNCONFIRMED", text)
            else:
                self.assertIn("status-names-ledger-a: yes", text, row_id)

    def test_a_row_without_a_binding_has_no_bindings_folder_after_the_chain(self) -> None:
        run = self.chain(ROW3C)
        self.assertFalse(os.path.lexists(os.path.join(run.run_root, "ckpt", "bindings")), "nothing bound a session")
        self.assertEqual(read_json(run.raw("run.json"))["expected_changes"], [])




# ---------------------------------------------------------------------------------------------
# The three layouts (plan 04-15, task 3)
# ---------------------------------------------------------------------------------------------

LAYOUT_PLAIN = "plain-memory"
LAYOUT_HUB = "hub-memory"
LAYOUT_BOUND = "bound-ledger"
LAYOUTS = (LAYOUT_PLAIN, LAYOUT_HUB, LAYOUT_BOUND)
MEMORY_LAYOUTS = (LAYOUT_PLAIN, LAYOUT_HUB)
FIXTURE_TREE = {
    LAYOUT_PLAIN: os.path.join(ROOT, "tests", "fixtures", "plain-memory", "project"),
    LAYOUT_HUB: os.path.join(ROOT, "tests", "fixtures", "hub-memory", "project"),
}
LAYOUT_PROMPTS = os.path.join(DATA, "layout-s1-prompts.md")
LAYOUT_PROMPTS_SHA256 = "78c3c0f9263614b68ce925314154582b1bda014184431c7a7823085ce284a39a"
SHARED_CLOSING = (
    "Do not run tests, commit, or start step 3. Leave the plan checkbox for checkpointing to reconcile. "
    "Keep the reply to three lines."
)
NOT_EXERCISED = ("identity collision", "blocked instruction", "freshness edit", "tamper", "repeat /preclear")


def fixtures_digest() -> str:
    import pc_manifest

    entries = pc_manifest.tree_manifest(os.path.join(ROOT, "tests", "fixtures"))
    return sha(pc_manifest.jsonl_bytes(entries))


def tree_files(folder: str) -> dict:
    """Relative path to bytes of every regular file under folder."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(folder):
        for name in filenames:
            full = os.path.join(dirpath, name)
            found[os.path.relpath(full, folder).replace(os.sep, "/")] = read_bytes(full)
    return found


def layout_stages(layout_id: str, extra_s1=(), extra_s2=()) -> list:
    stages = pc_testutil.default_row_stages(spec_of(layout_id))
    stages[0]["ops"] = list(stages[0]["ops"]) + list(extra_s1)
    stages[1]["ops"] = list(stages[1]["ops"]) + list(extra_s2)
    return stages


class LayoutPromptTests(unittest.TestCase):
    def sections(self) -> dict:
        text = read_text(LAYOUT_PROMPTS)
        found = {}
        current = None
        for line in text.split("\n"):
            if line.startswith("## "):
                current = line[3:]
                found[current] = []
            elif current is not None:
                found[current].append(line)
        return dict((name, "\n".join(lines).strip("\n")) for name, lines in found.items())

    def test_the_prompts_file_is_pinned_by_digest(self) -> None:
        self.assertEqual(sha(read_bytes(LAYOUT_PROMPTS)), LAYOUT_PROMPTS_SHA256)

    def test_it_holds_one_level_two_heading_per_memory_layout_and_nothing_else_of_that_level(self) -> None:
        text = read_text(LAYOUT_PROMPTS)
        headings = [line for line in text.split("\n") if line.startswith("## ")]
        self.assertEqual(headings, ["## plain-memory", "## hub-memory"])
        self.assertEqual([line for line in text.split("\n") if line.startswith("# ")], ["# Work-turn prompts of the memory layouts"])

    def test_each_prompt_is_one_short_paragraph_then_the_shared_closing_sentences_and_names_no_path(self) -> None:
        pattern = evidence().verdict_pattern()
        for name, body in self.sections().items():
            paragraphs = body.split("\n\n")
            self.assertEqual(len(paragraphs), 2, name)
            lead, closing = paragraphs
            self.assertLessEqual(len(re.findall(r"[.!?](?:\s|$)", lead)), 3, name)
            self.assertEqual(closing, SHARED_CLOSING, name)
            self.assertNotIn("/", body, name)
            self.assertNotIn("\\", body, name)
            self.assertTrue(body.isascii(), name)
            self.assertIsNone(SHAPED.search(body), name)
            self.assertEqual(pattern.findall(body), [], name)
            self.assertIn("step 2", lead)
            self.assertIn("small and pure", lead)
            self.assertIn("CSV", lead)
            self.assertNotIn("ledger", body.lower(), name)
        self.assertIn("PLAN.md", self.sections()[LAYOUT_PLAIN])
        self.assertIn("memory topic", self.sections()[LAYOUT_HUB])

    def test_the_engine_reads_each_section_as_the_s1_prompt_and_bound_ledger_reuses_the_row_1_prompt(self) -> None:
        sections = self.sections()
        for layout_id in MEMORY_LAYOUTS:
            prompts = row1().read_prompts(ROOT, spec_of(layout_id), None)
            self.assertEqual(prompts["s1"], sections[layout_id] + "\n", layout_id)
            self.assertEqual(prompts["s2"], read_text(committed("row1-wrong-binding", "s2-preclear-prompt.md")))
        prompts = row1().read_prompts(ROOT, spec_of(LAYOUT_BOUND), "/run/ledger.md")
        self.assertEqual(prompts["s1"], read_text(os.path.join(DATA, "row1-s1-prompt.md")).replace("$LEDGER", "/run/ledger.md"))

    def test_a_missing_a_repeated_or_an_empty_section_is_refused(self) -> None:
        import pc_spike

        for text, name in (("## a\nx\n", "b"), ("## a\nx\n## a\ny\n", "a"), ("## a\n\n## b\nz\n", "a")):
            with self.assertRaises(pc_spike.SpikeError, msg=text):
                row1().prompt_section(text, name)
        self.assertEqual(row1().prompt_section("# t\n\n## a\n\nx\n\ny\n\n## b\nz\n", "a"), "x\n\ny\n")


class LayoutRegistryTests(unittest.TestCase):
    def test_the_three_layouts_are_registered_with_the_core_chain_and_their_profiles(self) -> None:
        pc_rows = rows()
        for layout_id in LAYOUTS:
            spec = spec_of(layout_id)
            self.assertEqual(spec.kind, pc_rows.KIND_LAYOUT)
            self.assertTrue(spec.implemented)
            self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2", "s3"])
            self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30", "0.40"])
            self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60, 15])
            self.assertEqual(pc_rows.session_count(spec), 2)
            self.assertEqual(pc_rows.worst_case(spec), pc_rows.ROW_CAP)
            self.assertEqual(spec.chain, pc_rows.CHAIN_RESUME_LINE)
            self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
            self.assertEqual(spec.analyses, ("layout-facts",))
            self.assertEqual(spec.seed, "pc_rowseeds:seed_layout_" + layout_id.split("-", 1)[0])
            self.assertEqual(spec.expected_changes, ())
            for relative, kind in spec.sources:
                full = os.path.join(ROOT, *relative.split("/"))
                self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), relative)
        for layout_id in MEMORY_LAYOUTS:
            self.assertEqual(spec_of(layout_id).tools_profile, pc_rows.PROFILE_PLAIN)
            self.assertEqual(spec_of(layout_id).extra_tools, ())
        self.assertEqual(spec_of(LAYOUT_BOUND).tools_profile, pc_rows.PROFILE_HELPER)
        self.assertEqual(spec_of(LAYOUT_BOUND).hooks, (("s2", "lint-after-s2"),))
        for layout_id in MEMORY_LAYOUTS:
            self.assertEqual(spec_of(layout_id).hooks, ())

    def test_the_s2_prompt_is_the_committed_shared_one_and_the_s1_prompts_are_the_pinned_sections_and_the_row_1_file(self) -> None:
        shared = "tests/evidence/publication-2026-10-20/row1-wrong-binding/s2-preclear-prompt.md"
        for layout_id in LAYOUTS:
            self.assertEqual(dict(spec_of(layout_id).prompts)["s2"], shared)
        self.assertEqual(dict(spec_of(LAYOUT_PLAIN).prompts)["s1"], "tests/harness/data/layout-s1-prompts.md#plain-memory")
        self.assertEqual(dict(spec_of(LAYOUT_HUB).prompts)["s1"], "tests/harness/data/layout-s1-prompts.md#hub-memory")
        self.assertEqual(dict(spec_of(LAYOUT_BOUND).prompts)["s1"], "tests/harness/data/row1-s1-prompt.md")

    def test_each_layout_setup_text_lists_the_five_checks_the_harness_does_not_exercise_and_holds_no_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        for layout_id in LAYOUTS:
            text = spec_of(layout_id).setup_text
            self.assertTrue(text.startswith("Setup: "))
            self.assertTrue(text.isascii())
            self.assertIsNone(SHAPED.search(text))
            self.assertEqual(pattern.findall(text), [], layout_id)
            self.assertIn("does not exercise", text)
            for name in NOT_EXERCISED:
                self.assertIn(name, text, layout_id)
        for layout_id in MEMORY_LAYOUTS:
            self.assertIn("new baseline", spec_of(layout_id).setup_text)

    def test_the_dry_runs_print_three_stages_two_sessions_and_the_allowlist_size_and_start_nothing(self) -> None:
        for layout_id, size in ((LAYOUT_PLAIN, 33), (LAYOUT_HUB, 33), (LAYOUT_BOUND, 40)):
            code, text, tripwire, base = dry_run("--layout", layout_id)
            self.assertEqual(code, 0, text)
            self.assertIn("%s: 3 stages, 2 sessions" % layout_id, text)
            self.assertIn("allowlist %d rules" % size, text)
            self.assertIn("worst case 2.00 USD", text)
            self.assertEqual(tripwire, [], layout_id)
            self.assertFalse(os.path.exists(os.path.join(base, "hh")), layout_id)

    def test_list_marks_all_21_entries_implemented(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        self.assertEqual(len(lines) - 1, 21)
        for line in lines[1:]:
            self.assertTrue(line.endswith(" yes"), line)

    def test_a_layout_is_found_by_the_engine_lookup_and_a_row_still_is_and_an_odd_id_is_not(self) -> None:
        pc_rows = rows()
        registry = pc_rows.build_registry()
        self.assertEqual(pc_rows.find_runnable(registry, LAYOUT_HUB).kind, pc_rows.KIND_LAYOUT)
        self.assertEqual(pc_rows.find_runnable(registry, ROW2).kind, pc_rows.KIND_ROW)
        for odd in ("hub", "hub-memory ", "HUB-MEMORY", None, 5, "", "hub-memory/../x"):
            self.assertIsNone(pc_rows.find_runnable(registry, odd), repr(odd))
        self.assertIsNone(pc_rows.find_entry(registry, pc_rows.KIND_ROW, LAYOUT_HUB), "the exact kind lookup is unchanged")

    def test_the_ledger_stage_keys_of_the_layouts_do_not_collide_with_any_row(self) -> None:
        pc_rows = rows()
        keys = []
        for entry in pc_rows.build_registry():
            keys.extend(pc_rows.stage_key(entry.row_id, stage.name) for stage in entry.stages)
        self.assertEqual(len(keys), len(set(keys)))


class LayoutSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before = fixtures_digest()
        cls.seeded = dict((layout_id, SeededRow(layout_id, "seed-" + layout_id)) for layout_id in LAYOUTS)
        cls.after = fixtures_digest()

    def test_the_memory_layouts_copy_every_fixture_file_byte_for_byte_and_nothing_else_of_the_fixture(self) -> None:
        for layout_id in MEMORY_LAYOUTS:
            project = self.seeded[layout_id].project
            copied = dict((name, data) for name, data in tree_files(project).items() if not name.startswith((".git/", ".claude/")))
            self.assertEqual(copied, tree_files(FIXTURE_TREE[layout_id]), layout_id)
            self.assertTrue(copied, layout_id)

    def test_the_fixture_tree_digest_is_unchanged_by_the_seeds_and_the_fixtures_were_read_in_place(self) -> None:
        self.assertEqual(self.before, self.after)

    def test_the_memory_is_pinned_inside_the_project_and_no_run_root_memory_folder_is_made(self) -> None:
        import pc_flags

        for layout_id in MEMORY_LAYOUTS:
            seeded = self.seeded[layout_id]
            memory = os.path.join(seeded.project, "memory")
            self.assertTrue(os.path.isdir(memory))
            self.assertEqual(str(seeded.paths["auto_memory"]), memory)
            settings = read_json(str(seeded.paths["settings"]))
            self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(memory))
            self.assertTrue(settings.get("autoMemoryEnabled", True))
            self.assertEqual(seeded.record()["auto_memory"], "project/memory")
            self.assertFalse(os.path.lexists(os.path.join(seeded.run_root, "auto-memory")), layout_id)
            self.assertEqual(settings["autoMemoryDirectory"], pc_flags.render_settings(memory, "x")["autoMemoryDirectory"])

    def test_the_memory_layouts_have_no_helper_no_wrapper_no_ledger_and_no_binding(self) -> None:
        for layout_id in MEMORY_LAYOUTS:
            seeded = self.seeded[layout_id]
            self.assertFalse(os.path.lexists(os.path.join(seeded.run_root, "wrapper")), layout_id)
            self.assertEqual(seeded.listing("ckpt/ledgers"), [], layout_id)
            self.assertFalse(os.path.lexists(os.path.join(seeded.run_root, "ckpt", "bindings")), layout_id)
            self.assertEqual(seeded.record()["bound_ledger"], "none")

    def test_one_commit_on_main_holds_the_fixture_and_the_skill_copy_is_untracked(self) -> None:
        for layout_id in MEMORY_LAYOUTS:
            project = self.seeded[layout_id].project
            self.assertEqual(checks_git(project, "rev-list", "--count", "main").strip(), "1")
            tracked = sorted(checks_git(project, "ls-files").split())
            self.assertEqual(tracked, sorted(tree_files(FIXTURE_TREE[layout_id])))
            self.assertTrue(all(line.startswith("?? .claude/") for line in checks_git(project, "status", "--porcelain").splitlines()))

    def test_bound_ledger_is_row_1s_seed_with_one_ledger_bound_to_the_configured_ledger_a(self) -> None:
        seeded = self.seeded[LAYOUT_BOUND]
        self.assertEqual(seeded.record()["bound_ledger"], "A")
        self.assertEqual(seeded.record()["row"], LAYOUT_BOUND)
        self.assertNotIn("auto_memory", seeded.record())
        self.assertEqual(seeded.listing("ckpt/ledgers"), [LEDGER_A_NAME])
        self.assertEqual(len(seeded.listing("ckpt/bindings")), 1)
        self.assertEqual(str(seeded.paths["auto_memory"]), os.path.join(seeded.run_root, "auto-memory"))
        text = read_text(os.path.join(seeded.project, "CLAUDE.md"))
        fixture = read_text(committed("row1-wrong-binding", "fixture-CLAUDE.md"))
        assert_only_the_four_values_differ(self, text, fixture)
        self.assertEqual(value_of(text, "ledger"), str(seeded.paths["ledger_a"]))

    def test_a_second_seed_on_the_same_run_root_is_refused_and_a_bad_memory_folder_name_is_refused(self) -> None:
        seeded = self.seeded[LAYOUT_PLAIN]
        with self.assertRaises(FileExistsError):
            seed_of(LAYOUT_PLAIN)(
                seeded.rig.repo, seeded.run_root, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root,
                seeded.ctx.evidence_date, seeded.ctx.model,
            )
        rig = pc_testutil.RowRig(stages=layout_stages(LAYOUT_PLAIN))
        ctx = rig.context()
        for bad in ("../memory", "a/b", ".hidden", "", "x."):
            run_root = rig.new_run_root(ctx, "bad-" + str(abs(hash(bad)) % 10000))
            with self.assertRaises(ValueError, msg=repr(bad)):
                rowseeds().seed_plain_row(
                    rig.repo, run_root, str(uuid.uuid4()), ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model,
                    LAYOUT_PLAIN, "tests/fixtures/plain-memory/project/CLAUDE.md", "pinned",
                    fixture_tree="tests/fixtures/plain-memory/project", memory_dir=bad,
                )


class PathsForTests(unittest.TestCase):
    def test_paths_for_reads_the_memory_location_from_the_run_record(self) -> None:
        for layout_id in MEMORY_LAYOUTS:
            seeded = SeededRow(layout_id, "paths-" + layout_id)
            found = row1().paths_for(seeded.run_root)
            self.assertEqual(found["auto_memory"], os.path.join(os.path.realpath(seeded.run_root), "project", "memory"))
        helper = SeededRow(LAYOUT_BOUND, "paths-bound")
        self.assertEqual(row1().paths_for(helper.run_root)["auto_memory"], os.path.join(os.path.realpath(helper.run_root), "auto-memory"))

    def test_only_the_two_known_places_are_honoured_and_anything_else_gives_the_default(self) -> None:
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-paths-"))
        raw = os.path.join(base, "raw")
        os.makedirs(raw)
        default = os.path.join(base, "auto-memory")
        self.assertEqual(row1().paths_for(base)["auto_memory"], default, "no record")
        cases = [
            ('{"auto_memory": "project/memory"}', os.path.join(base, "project", "memory")),
            ('{"auto_memory": "auto-memory"}', default),
            ('{"auto_memory": "../outside"}', default),
            ('{"auto_memory": "/etc"}', default),
            ('{"auto_memory": "project/other"}', default),
            ('{"auto_memory": "project/memory/"}', default),
            ('{"auto_memory": ["project/memory"]}', default),
            ('{"auto_memory": null}', default),
            ('["project/memory"]', default),
            ("not json", default),
            ("{}", default),
        ]
        for body, expected in cases:
            with open(os.path.join(raw, "run.json"), "w", encoding="utf-8") as handle:
                handle.write(body)
            self.assertEqual(row1().paths_for(base)["auto_memory"], expected, body)


def layout_memory_ops(hub: bool) -> list:
    """Scripted writes into the pinned memory folder: a new topic file, and for the plain layout nothing hub-shaped."""
    return [{"op": "write", "path": "$AUTOMEM/project_new_topic.md", "text": "a new topic\n"}]


class LayoutChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plain = Registered(LAYOUT_PLAIN, stages=layout_stages(LAYOUT_PLAIN, extra_s2=layout_memory_ops(False)))
        cls.hub = Registered(
            LAYOUT_HUB,
            stages=layout_stages(
                LAYOUT_HUB,
                extra_s2=layout_memory_ops(True)
                + [{"op": "write", "path": "$AUTOMEM/MEMORY.md", "text": "# Memory index\n\n- [hub_projects.md](hub_projects.md) - changed\n"}],
            ),
        )
        cls.bound = Registered(LAYOUT_BOUND)

    def test_every_layout_chain_is_filed_with_the_layout_id_as_the_folder_and_three_stages(self) -> None:
        for run in (self.plain, self.hub, self.bound):
            self.assertEqual(run.outcome.code, pc_exitcodes.OK, "\n".join(run.outcome.lines))
            names = tree_names(run.row_dir)
            for name in ("README.md", "mechanical-checks.md", "s1.exit", "s2-preclear.exit", "resume-line.txt"):
                self.assertIn(name, names, run.row_id + " " + name)
            self.assertTrue([name for name in names if name.startswith("s3") and name.endswith(".exit")], run.row_id)
            self.assertTrue(read_text(os.path.join(run.row_dir, "README.md")).rstrip("\n").endswith("Reviewer verdict: PENDING"))
            self.assertIn(run.spec.setup_text, read_text(os.path.join(run.row_dir, "README.md")))

    def test_the_memory_layouts_run_with_the_pinned_memory_inside_the_project_and_the_checks_find_no_breach(self) -> None:
        for run in (self.plain, self.hub):
            facts = checks().compute_facts(run.run_root, run.ctx.config_dir)
            self.assertEqual(facts["write_boundary"], {"count": 0, "paths": []}, run.row_id)
            self.assertEqual(facts["memory_probe"], "absent", run.row_id)
            self.assertEqual(checks().breaches(facts), [], run.row_id)
            init = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
            self.assertIn("memory-path-as-set: yes", init, run.row_id)
            self.assertTrue(os.path.isfile(os.path.join(run.row_dir, "snap-2-after-preclear", "auto-memory", "project_new_topic.md")))

    def test_the_layout_facts_section_of_plain_memory_lists_the_new_file_and_no_hub_style_files(self) -> None:
        text = read_text(os.path.join(self.plain.row_dir, "mechanical-checks.md"))
        self.assertIn("## Layout facts", text)
        self.assertIn("files-created-under-project: ", text)
        self.assertRegex(text, r"files-created-under-project [0-9]+: widget_export\.py")
        self.assertIn("files-created-under-project: 2", text)
        self.assertIn("files-created-under-memory: 1", text)
        self.assertIn("files-created-under-memory 1: project_new_topic.md", text)
        self.assertIn("hub-style-files-created: 0", text)
        self.assertIn("memory-files-before: 2", text)
        self.assertIn("memory-files-after: 3", text)
        self.assertRegex(text, r"memory-files-before 1: MEMORY\.md sha256 [0-9a-f]{64}")
        self.assertIn("not-exercised-by-the-harness: identity collision, blocked instruction, freshness edit, tamper, repeat /preclear", text)
        self.assertNotIn("memory-index-changed", text)

    def test_the_layout_facts_section_of_hub_memory_has_the_index_digests_the_list_and_the_new_file_count(self) -> None:
        text = read_text(os.path.join(self.hub.row_dir, "mechanical-checks.md"))
        before = sha(read_bytes(os.path.join(FIXTURE_TREE[LAYOUT_HUB], "memory", "MEMORY.md")))
        after = sha(b"# Memory index\n\n- [hub_projects.md](hub_projects.md) - changed\n")
        self.assertIn("memory-index-sha256-before: " + before, text)
        self.assertIn("memory-index-sha256-after: " + after, text)
        self.assertIn("memory-index-changed: yes", text)
        self.assertIn("new-memory-files: 1", text)
        self.assertIn("files-created-under-memory 1: project_new_topic.md", text)
        self.assertIn("memory-files-before: 6", text)
        self.assertIn("memory-files-after: 7", text)
        self.assertIn("memory-files-changed: 1", text)
        self.assertNotIn("hub-style-files-created", text)

    def test_the_layout_facts_section_of_bound_ledger_has_the_changed_flag_the_update_count_and_the_lint_text(self) -> None:
        text = read_text(os.path.join(self.bound.row_dir, "mechanical-checks.md"))
        self.assertIn("ledger-a-changed: no", text)
        self.assertIn("update-calls-in-wrapper-log: 0", text)
        self.assertIn("lint-after-s2: present", text)
        self.assertIn("lint-after-s2-lines: 1", text)
        self.assertIn("lint-after-s2 line 1: ledger lint OK", text)
        filed = os.path.join(self.bound.row_dir, "lint-after-s2.txt")
        self.assertEqual(read_text(filed), "ledger lint OK\n")
        self.assertIn("lint-after-s2-sha256: " + sha(b"ledger lint OK\n"), text)

    def test_the_memory_layouts_file_no_lint_text_and_no_injection_log(self) -> None:
        for run in (self.plain, self.hub):
            names = tree_names(run.row_dir)
            self.assertNotIn("lint-after-s2.txt", names)
            self.assertNotIn("wrapper-injection.log", names)
            self.assertFalse(os.path.exists(os.path.join(run.run_root, "raw", "lint-after-s2.txt")))

    def test_the_lint_hook_adds_no_boundary_no_snapshot_and_no_guard_window_of_its_own(self) -> None:
        boundaries = [item["name"] for item in read_json(os.path.join(self.bound.run_root, "raw", "boundaries.json"))["boundaries"]]
        self.assertEqual(boundaries, ["setup", "s1", "s2", "s3"])
        self.assertEqual(sorted(os.listdir(os.path.join(self.bound.run_root, "snaps"))),
                         ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"])
        self.assertTrue(os.path.isfile(os.path.join(self.bound.run_root, "raw", "lint-after-s2.txt")))
        facts = checks().compute_facts(self.bound.run_root, self.bound.ctx.config_dir)
        self.assertEqual(facts["guard"], {"count": 0, "kinds": {}})

    def test_the_status_question_of_bound_ledger_names_ledger_a(self) -> None:
        text = read_text(os.path.join(self.bound.row_dir, "mechanical-checks.md"))
        self.assertIn("status-names-ledger-a: yes", text)

    def test_a_layout_run_root_is_refiled_with_zero_tokens_and_finds_the_memory_folder_inside_the_project(self) -> None:
        for layout_id, stages in (
            (LAYOUT_PLAIN, layout_stages(LAYOUT_PLAIN, extra_s2=layout_memory_ops(False))),
            (LAYOUT_BOUND, None),
        ):
            rig = pc_testutil.RowRig(stages=stages if stages is not None else pc_testutil.default_row_stages(spec_of(layout_id)))
            first = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5-first")
            ctx = rig.context(destination=first)
            outcome = row1().run_registered_row(ctx, layout_id)
            self.assertEqual(outcome.code, pc_exitcodes.OK, "\n".join(outcome.lines))
            run_root = os.path.join(ctx.runs_root, sorted(os.listdir(ctx.runs_root))[0])
            calls = len(rig.calls())
            out, err = io.StringIO(), io.StringIO()
            code = matrix().main(["--refile", run_root], env=dict(rig.env), repo_root=rig.repo, clock=lambda: FIXED_DATE, out=out, err=err)
            self.assertEqual(code, 0, out.getvalue() + err.getvalue())
            self.assertEqual(len(rig.calls()), calls, "a refile starts no process")
            dated = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5", layout_id)
            self.assertTrue(os.path.isfile(os.path.join(dated, "README.md")), layout_id)
            if layout_id == LAYOUT_PLAIN:
                self.assertTrue(os.path.isfile(os.path.join(dated, "snap-2-after-preclear", "auto-memory", "project_new_topic.md")))
                self.assertIn("files-created-under-memory 1: project_new_topic.md", read_text(os.path.join(dated, "mechanical-checks.md")))
            else:
                self.assertEqual(read_text(os.path.join(dated, "lint-after-s2.txt")), "ledger lint OK\n")


class BoundLedgerUpdateTests(unittest.TestCase):
    def test_a_scripted_update_through_the_wrapper_changes_the_ledger_and_is_counted(self) -> None:
        texts = input_texts()
        goal_rel = wrapper_rig.INPUTS_REL + "/goal.md"
        extra = [
            {"op": "write", "path": "$PROJECT/" + goal_rel, "text": texts["goal"]},
            wrapper_call(["show"]),
            wrapper_call(wrapper_rig.update_args(wrapper_rig.GOAL, SECTION_HASH, goal_rel)),
        ]
        run = Registered(LAYOUT_BOUND, stages=layout_stages(LAYOUT_BOUND, extra_s2=extra))
        self.assertEqual(run.outcome.code, pc_exitcodes.OK, "\n".join(run.outcome.lines))
        text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
        self.assertIn("ledger-a-changed: yes", text)
        self.assertIn("update-calls-in-wrapper-log: 1", text)
        self.assertIn("update-calls-with-exit 0: 1", text)


class LayoutFactsTests(unittest.TestCase):
    def review(self):
        import pc_review

        return pc_review

    def pattern(self):
        return evidence().verdict_pattern()

    def test_update_calls_counts_update_verbs_skips_leading_session_options_and_tallies_exit_codes(self) -> None:
        log = "\n".join([
            "2026-11-07T10:00:00Z CALL status",
            "2026-11-07T10:00:00Z EXIT 0",
            "2026-11-07T10:00:01Z CALL --session abc update --section x",
            "2026-11-07T10:00:01Z EXIT 3",
            "2026-11-07T10:00:02Z CALL --session=abc update --section x",
            "2026-11-07T10:00:02Z EXIT 0",
            "2026-11-07T10:00:03Z CALL update --section y",
            "2026-11-07T10:00:04Z CALL show",
            "2026-11-07T10:00:04Z EXIT 0",
            "2026-11-07T10:00:05Z CALL",
            "2026-11-07T10:00:05Z EXIT 70",
            "2026-11-07T10:00:06Z CALL show update",
            "2026-11-07T10:00:06Z EXIT 0",
            "junk line",
        ])
        count, codes = self.review().update_calls(log)
        self.assertEqual(count, 3)
        self.assertEqual(codes, {"3": 1, "0": 1, "none": 1})
        self.assertEqual(self.review().update_calls(""), (0, {}))

    def test_a_file_name_or_lint_line_with_a_reserved_word_is_withheld_and_names_are_cleaned_and_capped(self) -> None:
        r = self.review()
        pattern = self.pattern()
        word = "fa" + "iled"
        before = {"project/memory/MEMORY.md": "a" * 64}
        after = {"project/memory/MEMORY.md": "a" * 64, "project/memory/%s.md" % word: "b" * 64, "project/" + "x" * 400: "c" * 64}
        lines = r.memory_layout_lines(before, after, lambda text: text, pattern, False)
        joined = "\n".join(lines)
        self.assertNotIn(word, joined)
        self.assertIn("(name withheld)", joined)
        self.assertIsNone(pattern.search(joined))
        self.assertTrue(all(len(line) < 400 for line in lines))
        lint = ("ledger lint " + word + "\nsecond line\n").encode("utf-8")
        shown = r.bound_ledger_lines({}, {}, None, lint, lambda text: text, pattern)
        self.assertIn("lint-after-s2 line 1: " + r.WITHHELD, shown)
        self.assertIn("lint-after-s2 line 2: second line", shown)
        self.assertIsNone(pattern.search("\n".join(shown)))
        self.assertIn("update-calls-in-wrapper-log: UNCONFIRMED", shown)

    def test_long_lists_are_capped_and_the_rest_is_counted(self) -> None:
        r = self.review()
        after = dict(("project/memory/t%03d.md" % number, "d" * 64) for number in range(r.MAX_LAYOUT_NAMES + 5))
        lines = r.memory_layout_lines({}, after, lambda text: text, self.pattern(), True)
        self.assertIn("files-created-under-memory: %d" % (r.MAX_LAYOUT_NAMES + 5), lines)
        self.assertIn("files-created-under-memory not listed: 5", lines)
        self.assertEqual(len([line for line in lines if line.startswith("files-created-under-memory ") and "not listed" not in line]), r.MAX_LAYOUT_NAMES)

    def test_hub_style_names_are_found_by_their_base_name_in_either_folder(self) -> None:
        r = self.review()
        after = {"project/memory/hub_extra.md": "e" * 64, "project/notes/Hub-notes.md": "f" * 64, "project/memory/topic_hub.md": "1" * 64}
        lines = r.memory_layout_lines({}, after, lambda text: text, self.pattern(), False)
        self.assertIn("hub-style-files-created: 2", lines)

    def test_the_analysis_reports_unconfirmed_without_snapshots_and_the_wrapper_injection_file_only_when_it_exists(self) -> None:
        r = self.review()
        spec = spec_of(LAYOUT_PLAIN)
        title, lines, files = r.analyse_layout_facts(spec, None, {}, lambda text: text)
        self.assertEqual((title, files), ("Layout facts", {}))
        self.assertEqual(lines, ["layout-facts: UNCONFIRMED"])
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-injection-"))
        os.makedirs(os.path.join(base, "wrapper"))

        class Data(object):
            paths = {"wrapper_dir": os.path.join(base, "wrapper")}

        self.assertEqual(r.analyse_wrapper_injection(spec, Data, {}, str), ("", [], {}))
        with open(os.path.join(base, "wrapper", "injection.log"), "wb") as handle:
            handle.write(b"x\n")
        self.assertEqual(r.analyse_wrapper_injection(spec, Data, {}, str), ("", [], {"wrapper-injection.log": b"x\n"}))


class LintHookTests(unittest.TestCase):
    def test_the_hook_files_the_lint_text_exclusively_and_a_second_run_is_refused(self) -> None:
        seeded = SeededRow(LAYOUT_BOUND, "lint-hook")
        target = os.path.join(str(seeded.paths["raw"]), "lint-after-s2.txt")
        rowhooks().lint_after_s2(seeded.ctx, seeded.paths, spec_of(LAYOUT_BOUND))
        self.assertEqual(read_bytes(target), b"ledger lint OK\n")
        with self.assertRaises(rowhooks().HookRefused):
            rowhooks().lint_after_s2(seeded.ctx, seeded.paths, spec_of(LAYOUT_BOUND))
        self.assertEqual(read_bytes(target), b"ledger lint OK\n")

    def test_a_wrapper_folder_without_the_interpreter_file_gives_the_fixed_line_and_a_linked_folder_is_refused(self) -> None:
        seeded = SeededRow(LAYOUT_BOUND, "lint-hook-2")
        with open(os.path.join(str(seeded.paths["wrapper_dir"]), "py"), "w", encoding="utf-8") as handle:
            handle.write("")
        rowhooks().lint_after_s2(seeded.ctx, seeded.paths, spec_of(LAYOUT_BOUND))
        self.assertEqual(read_text(os.path.join(str(seeded.paths["raw"]), "lint-after-s2.txt")), "lint did not run\n")
        plain = SeededRow(LAYOUT_PLAIN, "lint-hook-3")
        with self.assertRaises(rowhooks().HookRefused):
            rowhooks().lint_after_s2(plain.ctx, plain.paths, spec_of(LAYOUT_PLAIN))

    def test_the_hook_table_marks_it_without_boundary_finalizer_and_snapshot(self) -> None:
        h = rowhooks()
        self.assertIn("lint-after-s2", h.NO_BOUNDARY)
        self.assertIn("lint-after-s2", h.NO_FINALIZER)
        self.assertNotIn("lint-after-s2", h.HOOK_SNAPSHOTS)
        self.assertTrue(h.known_hook("lint-after-s2"))
        self.assertEqual(h.plan_boundaries(spec_of(LAYOUT_BOUND)), [
            ("setup", "snap-0-setup"), ("s1", "snap-1-after-work"), ("s2", "snap-2-after-preclear"), ("s3", "snap-3-after-resume")])
        self.assertEqual(h.hooks_of(spec_of(LAYOUT_BOUND), "s2"), ["lint-after-s2"])
        self.assertEqual(h.hooks_of(spec_of(LAYOUT_BOUND), "s1"), [])


class AllEntriesTests(unittest.TestCase):
    def test_dry_run_all_lists_21_entries_and_the_exact_worst_case_total_and_the_ceiling_is_unchanged(self) -> None:
        import pc_flags

        pc_rows = rows()
        implemented = [entry for entry in pc_rows.build_registry() if entry.implemented]
        self.assertEqual(len(implemented), 21)
        self.assertEqual(sum(len(entry.stages) for entry in implemented), 36 + 2 * 5 + 3 * 3)
        self.assertEqual(sum(pc_rows.session_count(entry) for entry in implemented), 22 + 5 + 6)
        self.assertEqual(sum((pc_rows.worst_case(entry) for entry in implemented), Decimal("0")), Decimal("38.40"))
        self.assertEqual(Decimal(pc_flags.format_invocation_budget("25.00")), Decimal("25.00"))
        with self.assertRaises(ValueError):
            pc_flags.format_invocation_budget("25.01")
        code, text, tripwire, base = dry_run("--all")
        self.assertEqual(code, 0, text)
        self.assertIn("total: 21 row(s), 55 stage(s), 33 session(s), worst case 38.40 USD", text)
        self.assertEqual([line.split(":")[0] for line in text.splitlines() if re.match(r"^[a-z0-9-]+: \d stages", line)][:3], list(LAYOUTS))
        self.assertEqual(tripwire, [])


if __name__ == "__main__":
    unittest.main()
