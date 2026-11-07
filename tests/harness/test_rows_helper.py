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


if __name__ == "__main__":
    unittest.main()
