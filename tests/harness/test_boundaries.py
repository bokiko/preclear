"""Zero-token tests for the recorded boundary list and the between-stage hooks (plan 04-05; RERUN-02; T-04-19 to T-04-22).

The engine records the boundaries a row will take in raw/boundaries.json at setup, before the setup guard. The checks
read snapshots, stage records, git states and guards through that list: an unlisted snapshot folder, stage record, git
state file or guard file is a CheckError (nothing is filed), the present boundaries are a prefix of the plan, and only
a run root with no list file at all is read with the legacy fixed order. The hook framework restricts a plan file after
a stage and restores it before filing, and it must not be steerable outside the run root by anything the model planted.

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every folder comes
from RowRig or tempfile and is never deleted; planting a link or a special file is done by a scripted claude op or by a
creation call, never by removing anything. The outside file of a safety test is a scratch file made by the test. Modules
are imported inside small accessors, so a missing module is one error per test and not one load failure of the file.
Messages that name a path are never asserted on by value.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import socket
import tempfile
import unittest
from unittest import mock

import pc_exitcodes
import pc_testutil
from test_row_generic import Registered, tree_names
from test_rows_plain import (
    EXPECTED_BOUNDARIES,
    PLAN_NAME,
    PLAN_RELATIVE,
    RESTRICTION_SNAPSHOT,
    ROW6,
    SeededPlain,
    Row6Run,
    plan_mode,
    plan_path,
    read_bytes,
    read_json,
    read_text,
    spec_of,
)

HOOK = "restrict-plan-444"
ROW6_PLAN = [(item["name"], item["snapshot"]) for item in EXPECTED_BOUNDARIES]
HEX = "0123456789abcdef" * 4


def checks():
    import pc_checks

    return pc_checks


def rowhooks():
    import pc_rowhooks

    return pc_rowhooks


def row1():
    import pc_row1

    return pc_row1


def evidence():
    import pc_evidence

    return pc_evidence


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)


def chain_into_first(rig, row_id: str):
    """Run a registered row into a first folder (so the dated folder stays free for a refile); return (outcome, run root)."""
    first = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5-first")
    ctx = rig.context(destination=first)
    outcome = row1().run_registered_row(ctx, row_id)
    names = sorted(os.listdir(ctx.runs_root))
    assert len(names) == 1, names
    return outcome, os.path.join(ctx.runs_root, names[0]), first


def refile(rig, run_root: str):
    out, err = io.StringIO(), io.StringIO()
    code = matrix().main(
        ["--refile", run_root], env=dict(rig.env), repo_root=rig.repo, clock=lambda: FIXED_DATE, out=out, err=err
    )
    return code, out.getvalue() + err.getvalue(), os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5")


def digest(letter: str) -> str:
    return (letter * 64)[:64]


def make_guard(raw, snaps, size=0, sha=None, prefix="n/a"):
    return {"raw": dict(raw), "snaps": dict(snaps), "hooklog": {"size": size, "sha256": sha or digest("c"), "prefix_intact": prefix}}


def layout(raw_files=(), snap_dirs=(), boundaries=None):
    """A scratch raw folder and snaps folder; boundaries (a list of pairs) is written as the list file when given."""
    base = os.path.realpath(tempfile.mkdtemp(prefix="pc-bound-"))
    raw, snaps = os.path.join(base, "raw"), os.path.join(base, "snaps")
    os.makedirs(raw)
    os.makedirs(snaps)
    if boundaries is not None:
        checks().write_boundaries(raw, boundaries)
    for name in raw_files:
        with open(os.path.join(raw, name), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
    for name in snap_dirs:
        os.makedirs(os.path.join(snaps, name))
    return raw, snaps


def write_file(path: str, text: str = "{}\n") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class BoundaryListTests(unittest.TestCase):
    def test_the_validator_accepts_the_row6_plan_the_legacy_order_and_a_plan_with_two_hooks(self) -> None:
        c = checks()
        self.assertEqual(c.validate_boundaries(ROW6_PLAN), ROW6_PLAN)
        self.assertEqual(c.validate_boundaries(list(c.LEGACY_BOUNDARIES)), list(c.LEGACY_BOUNDARIES))
        two = ROW6_PLAN + [("s2-hook-two", "snap-2b-after-two")]
        self.assertEqual(c.validate_boundaries(two), two)

    def test_the_validator_refuses_a_repeated_name_a_repeated_snapshot_and_a_list_that_does_not_start_with_setup(self) -> None:
        c = checks()
        bad = {
            "repeated name": ROW6_PLAN + [("s2", "snap-3-after-resume")],
            "repeated snapshot": ROW6_PLAN + [("s3", "snap-2-after-preclear")],
            "no setup first": ROW6_PLAN[1:],
            "wrong setup snapshot": [("setup", "snap-9-other")] + ROW6_PLAN[1:],
            "empty": [],
            "not a list": "setup",
            "a mapping": {"setup": "snap-0-setup"},
        }
        for label, planned in bad.items():
            with self.assertRaises(c.CheckError, msg=label) as caught:
                c.validate_boundaries(planned)
            self.assertNotIn(os.sep, str(caught.exception), "fixed text, no path")

    def test_the_validator_refuses_an_unknown_shape_a_hook_with_no_stage_and_odd_types_and_sizes(self) -> None:
        c = checks()
        bad = {
            "unknown name": ROW6_PLAN + [("x1", "snap-3-after-resume")],
            "stage out of range": ROW6_PLAN + [("s10", "snap-3-after-resume")],
            "upper case": ROW6_PLAN + [("S3", "snap-3-after-resume")],
            "hook of another stage": ROW6_PLAN + [("s3-hook", "snap-3b-after-hook")],
            "hook before its stage": [ROW6_PLAN[0], ("s1-hook", "snap-1b-after-hook")] + ROW6_PLAN[1:],
            "snapshot shape": ROW6_PLAN + [("s3", "after-resume")],
            "snapshot with a slash": ROW6_PLAN + [("s3", "snap-3-after/resume")],
            "non text name": ROW6_PLAN + [(3, "snap-3-after-resume")],
            "three parts": ROW6_PLAN + [("s3", "snap-3-after-resume", "x")],
            "mapping with another key": [{"name": "setup", "snapshot": "snap-0-setup", "extra": 1}],
            "too long": ROW6_PLAN[:2] + [("s1-h%d" % number, "snap-1b-after-h%d" % number) for number in range(40)],
        }
        for label, planned in bad.items():
            with self.assertRaises(c.CheckError, msg=label):
                c.validate_boundaries(planned)

    def test_a_missing_list_file_reads_as_the_legacy_order_and_is_not_recorded(self) -> None:
        c = checks()
        raw, _snaps = layout()
        self.assertFalse(c.boundaries_recorded(raw))
        self.assertEqual(c.read_boundaries(raw), list(c.LEGACY_BOUNDARIES))
        self.assertEqual(
            [name for name, _snapshot in c.read_boundaries(raw)], ["setup", "s1", "s2", "s3"], "the legacy order"
        )

    def test_a_present_but_malformed_list_file_is_an_error_and_never_a_fallback(self) -> None:
        c = checks()
        good = {"boundaries": [{"name": n, "snapshot": s} for n, s in ROW6_PLAN]}
        cases = {
            "empty file": "",
            "not json": "not json",
            "a list": json.dumps([1, 2]),
            "no key": json.dumps({}),
            "another key": json.dumps(dict(good, extra=1)),
            "not setup first": json.dumps({"boundaries": good["boundaries"][1:]}),
            "repeated": json.dumps({"boundaries": good["boundaries"] + good["boundaries"][1:2]}),
            "unknown shape": json.dumps({"boundaries": good["boundaries"] + [{"name": "zz", "snapshot": "snap-8-zz"}]}),
            "bare words": json.dumps({"boundaries": ["setup", "s1"]}),
        }
        for label, text in cases.items():
            raw, _snaps = layout()
            write_file(os.path.join(raw, "boundaries.json"), text)
            self.assertTrue(c.boundaries_recorded(raw), label)
            with self.assertRaises(c.CheckError, msg=label):
                c.read_boundaries(raw)
        raw, _snaps = layout()
        os.makedirs(os.path.join(raw, "boundaries.json"))
        with self.assertRaises(c.CheckError, msg="a folder in place of the file"):
            c.read_boundaries(raw)
        raw, _snaps = layout()
        target = os.path.join(os.path.dirname(raw), "elsewhere.json")
        write_file(target, json.dumps(good))
        os.symlink(target, os.path.join(raw, "boundaries.json"))
        with self.assertRaises(c.CheckError, msg="a link in place of the file"):
            c.read_boundaries(raw)

    def test_write_boundaries_validates_creates_exclusively_and_round_trips(self) -> None:
        c = checks()
        raw, _snaps = layout()
        with self.assertRaises(c.CheckError):
            c.write_boundaries(raw, ROW6_PLAN[1:])
        self.assertFalse(os.path.lexists(os.path.join(raw, "boundaries.json")), "a refused list leaves no file")
        c.write_boundaries(raw, ROW6_PLAN)
        self.assertEqual(c.read_boundaries(raw), ROW6_PLAN)
        self.assertEqual(oct(os.stat(os.path.join(raw, "boundaries.json")).st_mode & 0o777), oct(0o600))
        with self.assertRaises(FileExistsError):
            c.write_boundaries(raw, ROW6_PLAN)

    def test_present_boundaries_accepts_any_in_order_prefix_of_the_plan(self) -> None:
        c = checks()
        stage = lambda n: ["%s.git.json" % n, "%s.guard.json" % n]  # noqa: E731
        setup = stage("setup")
        s1 = stage("s1") + ["s1.record.json"]
        hook = stage("s1-restrict-plan-444")
        s2 = stage("s2") + ["s2.record.json"]
        snap = {"setup": "snap-0-setup", "s1": "snap-1-after-work", "hook": RESTRICTION_SNAPSHOT, "s2": "snap-2-after-preclear"}
        cases = [
            (setup, [snap["setup"]], 1),
            (setup + s1, [snap["setup"], snap["s1"]], 2),
            (setup + s1 + hook, [snap["setup"], snap["s1"], snap["hook"]], 3),
            (setup + s1 + hook + s2, list(snap.values()), 4),
        ]
        for raw_files, snap_dirs, count in cases:
            raw, snaps = layout(raw_files, snap_dirs, ROW6_PLAN)
            planned, present = c.present_boundaries(raw, snaps)
            self.assertEqual(planned, ROW6_PLAN)
            self.assertEqual(present, ROW6_PLAN[:count])

    def test_a_stage_whose_record_is_missing_is_still_a_present_boundary_and_the_filing_refuses_the_row(self) -> None:
        c = checks()
        raw_files = ["setup.git.json", "setup.guard.json", "s1.git.json", "s1.guard.json"]
        raw, snaps = layout(raw_files, ["snap-0-setup", "snap-1-after-work"], ROW6_PLAN)
        _planned, present = c.present_boundaries(raw, snaps)
        self.assertEqual(present, ROW6_PLAN[:2], "the comparison against the stage's snapshot is kept")

    def test_present_boundaries_refuses_a_gap_and_a_boundary_missing_one_of_its_records(self) -> None:
        c = checks()
        base = ["setup.git.json", "setup.guard.json", "s1.git.json", "s1.guard.json", "s1.record.json"]
        s2 = ["s2.git.json", "s2.guard.json", "s2.record.json"]
        hook = ["s1-restrict-plan-444.git.json", "s1-restrict-plan-444.guard.json"]
        cases = {
            "a stage after a missing hook boundary": (base + s2, ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear"]),
            "a missing guard": (
                [name for name in base if name != "s1.guard.json"], ["snap-0-setup", "snap-1-after-work"]),
            "a missing git state": (
                [name for name in base if name != "s1.git.json"], ["snap-0-setup", "snap-1-after-work"]),
            "a missing snapshot folder": (base, ["snap-0-setup"]),
            "a hook boundary with no snapshot": (base + hook, ["snap-0-setup", "snap-1-after-work"]),
            "setup missing but s1 present": (base[2:], ["snap-1-after-work"]),
        }
        for label, (raw_files, snap_dirs) in cases.items():
            raw, snaps = layout(raw_files, snap_dirs, ROW6_PLAN)
            with self.assertRaises(c.CheckError, msg=label):
                c.present_boundaries(raw, snaps)

    def test_present_boundaries_refuses_a_snapshot_a_record_a_git_state_and_a_guard_the_plan_does_not_name(self) -> None:
        c = checks()
        base = ["setup.git.json", "setup.guard.json"]
        cases = {
            "an unlisted snapshot folder": (base, ["snap-0-setup", "snap-9-extra"]),
            "an unlisted snapshot that is a plain name": (base, ["snap-0-setup", "extra"]),
            "a stage record the plan does not name": (base + ["s3.record.json"], ["snap-0-setup"]),
            "a record of a hook boundary": (base + ["s1-restrict-plan-444.record.json"], ["snap-0-setup"]),
            "a record of setup": (base + ["setup.record.json"], ["snap-0-setup"]),
            "a git state the plan does not name": (base + ["s3.git.json"], ["snap-0-setup"]),
            "a guard the plan does not name": (base + ["s5.guard.json"], ["snap-0-setup"]),
            "an odd git state name": (base + ["whatever.git.json"], ["snap-0-setup"]),
        }
        for label, (raw_files, snap_dirs) in cases.items():
            raw, snaps = layout(raw_files, snap_dirs, ROW6_PLAN)
            with self.assertRaises(c.CheckError, msg=label) as caught:
                c.present_boundaries(raw, snaps)
            self.assertNotIn(os.sep, str(caught.exception))

    def test_without_the_list_the_legacy_rule_ignores_other_names_as_before(self) -> None:
        c = checks()
        raw, snaps = layout(["setup.git.json", "s3.record.json"], ["snap-0-setup", "snap-9-extra"])
        planned, present = c.present_boundaries(raw, snaps)
        self.assertEqual(planned, list(c.LEGACY_BOUNDARIES))
        self.assertEqual(present, [("setup", "snap-0-setup")])


class BoundaryRunTests(unittest.TestCase):
    """The list as the engine writes it, read through a real scripted row 6 run."""

    def test_a_run_root_with_only_a_prefix_of_the_plan_reads_without_error_when_s1_stopped_the_row(self) -> None:
        stages = pc_testutil.stages_with(pc_testutil.default_row_stages(spec_of(ROW6)), 0, exit=1)
        chain = Row6Run(stages)
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL)
        facts = checks().compute_facts(chain.run_root, chain.ctx.config_dir)
        self.assertEqual(facts["boundaries"], ["setup", "s1"])
        self.assertEqual(facts["snapshots"], ["snap-0-setup", "snap-1-after-work"])
        self.assertEqual(facts["stages"], ["s1"])

    def test_a_run_root_stopped_by_a_fault_after_the_hook_boundary_reads_as_a_prefix(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW6)))
        ctx = rig.context()
        original = row1().run_stage

        def failing(run_ctx, paths, spec, *args, **kwargs):
            if spec.name == "s2":
                raise RuntimeError("scripted fault")
            return original(run_ctx, paths, spec, *args, **kwargs)

        with mock.patch.object(row1(), "run_stage", failing):
            with self.assertRaises(RuntimeError):
                row1().run_registered_row(ctx, ROW6)
        names = sorted(os.listdir(ctx.runs_root))
        self.assertEqual(len(names), 1)
        run_root = os.path.join(ctx.runs_root, names[0])
        facts = checks().compute_facts(run_root, ctx.config_dir)
        self.assertEqual(facts["boundaries"], ["setup", "s1", "s1-restrict-plan-444"])
        self.assertEqual(facts["snapshots"], ["snap-0-setup", "snap-1-after-work", RESTRICTION_SNAPSHOT])
        self.assertEqual(plan_mode(run_root), 0o644, "the finalizer ran on the exception path")

    def test_a_row6_run_root_is_refiled_with_zero_tokens_with_the_restriction_snapshot_and_without_a_second_hook(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW6)))
        outcome, run_root, first = chain_into_first(rig, ROW6)
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        calls = len(rig.calls())
        code, text, dated = refile(rig, run_root)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(rig.calls()), calls, "no process was started")
        self.assertEqual(plan_mode(run_root), 0o644, "a refile runs no hook and changes no mode")
        self.assertEqual(tree_names(os.path.join(dated, ROW6)), tree_names(os.path.join(first, ROW6)))
        self.assertIn(RESTRICTION_SNAPSHOT + "/perms.txt", tree_names(os.path.join(dated, ROW6)))

    def planted_run(self, kind: str):
        """A completed row 6 run (the facts are computed on the run root) with one extra name planted afterwards."""
        chain = Row6Run()
        self.assertEqual(chain.outcome.code, 0, "\n".join(chain.outcome.lines))
        run_root = chain.run_root
        if kind == "snapshot":
            os.makedirs(os.path.join(run_root, "snaps", "snap-9-extra"))
        elif kind == "record":
            write_file(os.path.join(run_root, "raw", "s3.record.json"))
        elif kind == "git state":
            write_file(os.path.join(run_root, "raw", "s3.git.json"))
        elif kind == "guard":
            write_file(os.path.join(run_root, "raw", "s3.guard.json"))
        elif kind == "hook record":
            write_file(os.path.join(run_root, "raw", "s1-restrict-plan-444.record.json"))
        return chain

    def test_an_unlisted_snapshot_record_git_state_or_guard_is_a_check_error_for_the_facts(self) -> None:
        c = checks()
        for kind in ("snapshot", "record", "git state", "guard", "hook record"):
            chain = self.planted_run(kind)
            with self.assertRaises(c.CheckError, msg=kind):
                c.compute_facts(chain.run_root, chain.ctx.config_dir)

    def test_a_snapshot_folder_planted_by_the_model_in_s2_ends_the_row_with_11_files_a_label_and_restores_the_plan(self) -> None:
        stages = pc_testutil.default_row_stages(spec_of(ROW6))
        stages = pc_testutil._with_ops(stages, 1, [{"op": "write", "path": "$RUN/snaps/snap-9-extra/note.txt", "text": "x\n"}])
        chain = Row6Run(stages)
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(chain.outcome.lines))
        self.assertIn(row1().MESSAGE_CHECKS_UNREADABLE, chain.outcome.lines)
        self.assertEqual(os.listdir(chain.ctx.destination), ["STOPPED-" + ROW6])
        self.assertEqual(plan_mode(chain.run_root), 0o644)

    def test_a_stage_record_planted_for_a_stage_the_row_does_not_have_ends_the_row_with_11(self) -> None:
        stages = pc_testutil.default_row_stages(spec_of(ROW6))
        stages = pc_testutil._with_ops(stages, 1, [{"op": "write", "path": "$RUN/raw/s3.record.json", "text": "{}\n"}])
        chain = Row6Run(stages)
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(chain.outcome.lines))
        # The filing reads a stage record the row does not have as an unreadable run: exit 11 and nothing is filed.
        filed = os.listdir(chain.ctx.destination) if os.path.isdir(chain.ctx.destination) else []
        self.assertEqual(filed, [])
        self.assertEqual(plan_mode(chain.run_root), 0o644)


class LegacyOrderTests(unittest.TestCase):
    """A run root made before this plan has no list file; it is read with the fixed order and gives the same facts."""

    def legacy_run(self, row_id: str, stages=None):
        with mock.patch.object(rowhooks(), "write_boundary_list", lambda paths, spec: None):
            return Registered(row_id, stages=stages)

    def comparable(self, facts):
        """The facts of a run without the values that differ between two runs (commit ids, session ids)."""
        kept = dict(facts)
        git = dict(kept["git"])
        git["states"] = [dict((k, v) for k, v in state.items() if k in ("branch", "staged")) for state in git["states"]]
        kept["git"] = git
        kept.pop("session", None)
        return json.loads(json.dumps(kept, sort_keys=True))

    def test_the_engine_with_the_list_writer_off_leaves_no_list_file_and_the_row_is_still_filed(self) -> None:
        run = self.legacy_run(rows().ROW5A)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertFalse(os.path.lexists(run.raw("boundaries.json")))
        guard = read_json(run.raw("setup.guard.json"))
        self.assertNotIn("boundaries.json", guard["raw"])
        self.assertEqual(os.listdir(run.ctx.destination), [rows().ROW5A])

    def test_a_legacy_run_root_gives_the_same_facts_as_the_same_chain_with_the_list_for_a_row_with_no_hook(self) -> None:
        pc_rows = rows()
        for row_id, stages in (
            (pc_rows.ROW5A, None),
            (pc_rows.ROW1, pc_testutil.default_row1_stages()),
        ):
            old = self.legacy_run(row_id, stages)
            new = Registered(row_id, stages=stages)
            self.assertEqual(old.outcome.code, 0, "\n".join(old.outcome.lines))
            self.assertEqual(new.outcome.code, 0, "\n".join(new.outcome.lines))
            self.assertFalse(checks().boundaries_recorded(os.path.join(old.run_root, "raw")))
            self.assertTrue(checks().boundaries_recorded(os.path.join(new.run_root, "raw")))
            first = checks().compute_facts(old.run_root, old.ctx.config_dir)
            second = checks().compute_facts(new.run_root, new.ctx.config_dir)
            self.assertEqual(self.comparable(first), self.comparable(second), row_id)
            self.assertEqual(first["boundaries"], second["boundaries"])
            self.assertEqual(first["boundaries"][0], "setup")

    def test_a_legacy_run_is_filed_with_the_same_files_as_the_run_with_the_list(self) -> None:
        old = self.legacy_run(rows().ROW5A)
        new = Registered(rows().ROW5A)
        self.assertEqual(tree_names(old.row_dir), tree_names(new.row_dir))
        self.assertEqual(read_text(os.path.join(old.row_dir, "README.md")).count("Reviewer verdict: PENDING"), 1)

    def test_a_legacy_run_root_is_refiled_with_zero_tokens_and_the_same_files_as_the_first_filing(self) -> None:
        with mock.patch.object(rowhooks(), "write_boundary_list", lambda paths, spec: None):
            rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(rows().ROW5A)))
            outcome, run_root, first = chain_into_first(rig, rows().ROW5A)
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        self.assertFalse(checks().boundaries_recorded(os.path.join(run_root, "raw")))
        calls = len(rig.calls())
        code, text, dated = refile(rig, run_root)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(rig.calls()), calls, "no process was started")
        self.assertEqual(tree_names(os.path.join(dated, rows().ROW5A)), tree_names(os.path.join(first, rows().ROW5A)))

    def test_a_legacy_run_root_with_a_stray_snapshot_folder_is_read_as_it_always_was(self) -> None:
        run = self.legacy_run(rows().ROW5A)
        os.makedirs(os.path.join(run.run_root, "snaps", "snap-9-extra"))
        facts = checks().compute_facts(run.run_root, run.ctx.config_dir)
        self.assertEqual(facts["snapshots"], ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear"])

    def test_a_row_with_no_hook_plans_the_legacy_shaped_list_with_its_own_stages(self) -> None:
        pc_rows = rows()
        two = rowhooks().plan_boundaries(spec_of(pc_rows.ROW4A))
        self.assertEqual(two, list(checks().LEGACY_BOUNDARIES[:3]))
        three = rowhooks().plan_boundaries(spec_of(pc_rows.ROW1))
        self.assertEqual(three, list(checks().LEGACY_BOUNDARIES))
        self.assertEqual(rowhooks().plan_boundaries(spec_of(ROW6)), ROW6_PLAN)


class GuardChainTests(unittest.TestCase):
    """The guard chain compares each boundary with the previous one of the list."""

    def hook_previous(self):
        return make_guard(
            {"run.json": digest("1"), "s1.record.json": digest("2"), "s1.guard.json": digest("3"),
             "s1-restrict-plan-444.git.json": digest("4")},
            {"snap-0-setup": digest("5"), "snap-1-after-work": digest("6"), RESTRICTION_SNAPSHOT: digest("7")},
        )

    S2_WINDOW = ["s1-restrict-plan-444.guard.json", "s2.prompt", "s2.stdout", "s2.stderr", "s2.git.json", "s2.record.json"]

    def s2_current(self, raw_extra=(), snap_extra=("snap-2-after-preclear",), change_raw=(), change_snaps=(), prefix="yes"):
        previous = self.hook_previous()
        raw = dict(previous["raw"])
        for name in list(self.S2_WINDOW) + list(raw_extra):
            raw[name] = digest("8")
        for name in change_raw:
            raw[name] = digest("9")
        snaps = dict(previous["snaps"])
        for name in snap_extra:
            snaps[name] = digest("8")
        for name in change_snaps:
            snaps[name] = digest("9")
        return make_guard(raw, snaps, 10, digest("c"), prefix)

    def test_the_window_after_the_hook_boundary_holds_the_hook_s_guard_and_the_stage_s_own_names(self) -> None:
        c = checks()
        self.assertEqual(c.guard_violations(self.hook_previous(), self.s2_current(), "s2", ROW6_PLAN), [])

    def test_the_window_after_a_hook_of_s1_does_not_allow_chain_json_which_follows_the_guard_of_s2(self) -> None:
        c = checks()
        found = c.guard_violations(self.hook_previous(), self.s2_current(raw_extra=["chain.json"]), "s2", ROW6_PLAN)
        self.assertEqual(found, ["raw-entry-unexpected"])

    def test_the_window_after_a_hook_of_s2_allows_chain_json_like_the_window_after_s2(self) -> None:
        c = checks()
        plan = ROW6_PLAN[:3] + [("s2", "snap-2-after-preclear"), ("s2-restrict-plan-444", "snap-2b-after-restriction")]
        previous = make_guard({"s2.guard.json": digest("1"), "s2.record.json": digest("2")}, {"snap-2-after-preclear": digest("3")})
        raw = dict(previous["raw"], **{"chain.json": digest("4"), "s2-restrict-plan-444.git.json": digest("5")})
        snaps = dict(previous["snaps"], **{"snap-2b-after-restriction": digest("6")})
        current = make_guard(raw, snaps, 10, digest("c"), "yes")
        self.assertEqual(c.guard_violations(previous, current, "s2-restrict-plan-444", plan), [])

    def test_a_raw_entry_changed_during_the_restriction_window_is_a_violation(self) -> None:
        c = checks()
        for name in ("s1.record.json", "s1.guard.json", "run.json", "s1-restrict-plan-444.git.json"):
            current = self.s2_current(change_raw=[name])
            self.assertEqual(
                c.guard_violations(self.hook_previous(), current, "s2", ROW6_PLAN), ["raw-entry-changed"], name
            )

    def test_the_restriction_snapshot_changed_or_gone_in_the_next_window_is_a_violation(self) -> None:
        c = checks()
        current = self.s2_current(change_snaps=[RESTRICTION_SNAPSHOT])
        self.assertEqual(c.guard_violations(self.hook_previous(), current, "s2", ROW6_PLAN), ["snapshot-changed"])
        gone = self.s2_current()
        del gone["snaps"][RESTRICTION_SNAPSHOT]
        self.assertEqual(c.guard_violations(self.hook_previous(), gone, "s2", ROW6_PLAN), ["snapshot-changed"])

    def test_a_new_snapshot_that_is_not_the_boundary_s_own_is_unexpected_in_every_window(self) -> None:
        c = checks()
        current = self.s2_current(snap_extra=["snap-2-after-preclear", "snap-9-extra"])
        self.assertEqual(c.guard_violations(self.hook_previous(), current, "s2", ROW6_PLAN), ["snapshot-unexpected"])
        early = self.s2_current(snap_extra=[])
        hook_window = c.guard_violations(self.stage_previous(), self.hook_current(extra_snaps=["snap-2-after-preclear"]),
                                         "s1-restrict-plan-444", ROW6_PLAN)
        self.assertEqual(hook_window, ["snapshot-unexpected"], "the hook boundary takes its own snapshot only")
        self.assertEqual(early["snaps"].keys(), self.hook_previous()["snaps"].keys())

    def stage_previous(self):
        return make_guard(
            {"run.json": digest("1"), "s1.record.json": digest("2"), "s1.guard.json": digest("3")},
            {"snap-0-setup": digest("5"), "snap-1-after-work": digest("6")},
        )

    def hook_current(self, extra_raw=(), extra_snaps=(), change_raw=()):
        previous = self.stage_previous()
        raw = dict(previous["raw"], **{"s1-restrict-plan-444.git.json": digest("4")})
        for name in extra_raw:
            raw[name] = digest("8")
        for name in change_raw:
            raw[name] = digest("9")
        snaps = dict(previous["snaps"], **{RESTRICTION_SNAPSHOT: digest("7")})
        for name in extra_snaps:
            snaps[name] = digest("8")
        return make_guard(raw, snaps, 10, digest("c"), "yes")

    def test_the_hook_window_holds_the_hook_boundary_s_git_state_and_the_snapshot_and_nothing_else(self) -> None:
        c = checks()
        self.assertEqual(c.guard_violations(self.stage_previous(), self.hook_current(), "s1-restrict-plan-444", ROW6_PLAN), [])
        for extra in ("s2.prompt", "s2.stdout", "s1-restrict-plan-444.record.json", "extra.txt"):
            found = c.guard_violations(
                self.stage_previous(), self.hook_current(extra_raw=[extra]), "s1-restrict-plan-444", ROW6_PLAN
            )
            self.assertEqual(found, ["raw-entry-unexpected"], extra)
        changed = c.guard_violations(
            self.stage_previous(), self.hook_current(change_raw=["s1.record.json"]), "s1-restrict-plan-444", ROW6_PLAN
        )
        self.assertEqual(changed, ["raw-entry-changed"])

    def test_an_unknown_boundary_or_the_first_boundary_has_no_window(self) -> None:
        c = checks()
        for name in ("s7", "setup", "s1-other-hook"):
            with self.assertRaises(c.CheckError, msg=name):
                c.guard_violations(self.stage_previous(), self.hook_current(), name, ROW6_PLAN)

    def test_without_a_list_the_legacy_windows_are_used_as_before(self) -> None:
        c = checks()
        previous = make_guard({"run.json": digest("1"), "setup.guard.json": digest("2")}, {"snap-0-setup": digest("3")})
        raw = dict(previous["raw"], **{"s1.prompt": digest("4"), "s1.stdout": digest("4"), "s1.stderr": digest("4"),
                                      "s1.git.json": digest("4"), "s1.record.json": digest("4")})
        current = make_guard(raw, dict(previous["snaps"], **{"snap-1-after-work": digest("5")}), 5, digest("c"), "yes")
        self.assertEqual(c.guard_violations(previous, current, "s1"), [])
        self.assertEqual(c.guard_violations(previous, current, "s1", list(c.LEGACY_BOUNDARIES)), [])

    def test_capture_guard_follows_the_list_so_a_hook_boundary_is_guarded_against_the_stage_before_it(self) -> None:
        c = checks()
        raw, snaps = layout(boundaries=ROW6_PLAN)
        os.makedirs(os.path.join(snaps, "snap-0-setup"))
        write_file(os.path.join(snaps, "snap-0-setup", "manifest.jsonl"), "")
        paths = {"raw": raw, "snaps": snaps}
        c.capture_guard(paths, "setup")
        with self.assertRaises(c.CheckError, msg="the hook boundary needs the guard of the stage before it"):
            c.capture_guard(paths, "s1-restrict-plan-444")
        with self.assertRaises(c.CheckError, msg="a boundary the list does not name"):
            c.capture_guard(paths, "s3")
        os.makedirs(os.path.join(snaps, "snap-1-after-work"))
        write_file(os.path.join(snaps, "snap-1-after-work", "manifest.jsonl"), "")
        c.capture_guard(paths, "s1")
        os.makedirs(os.path.join(snaps, RESTRICTION_SNAPSHOT))
        write_file(os.path.join(snaps, RESTRICTION_SNAPSHOT, "manifest.jsonl"), "")
        c.capture_guard(paths, "s1-restrict-plan-444")
        guard = read_json(os.path.join(raw, "s1-restrict-plan-444.guard.json"))
        self.assertIn(RESTRICTION_SNAPSHOT, guard["snaps"])
        self.assertEqual(guard["hooklog"]["prefix_intact"], "yes")
        self.assertIn("s1.guard.json", guard["raw"])

    def tampered(self, op):
        stages = pc_testutil._with_ops(pc_testutil.default_row_stages(spec_of(ROW6)), 1, [op])
        return Row6Run(stages)

    def test_a_record_rewritten_in_the_restriction_window_is_a_breach_of_the_run_record(self) -> None:
        for op in (
            {"op": "write", "path": "$RUN/raw/s1.record.json", "text": "{}\n"},
            {"op": "write", "path": "$RUN/raw/s1-restrict-plan-444.git.json", "text": "{}\n"},
            {"op": "write", "path": "$RUN/raw/s1-restrict-plan-444.guard.json", "text": "{}\n"},
            {"op": "write", "path": "$RUN/snaps/%s/perms.txt" % RESTRICTION_SNAPSHOT, "text": PLAN_RELATIVE + " 644\n"},
            {"op": "write", "path": "$RUN/snaps/%s/manifest.jsonl" % RESTRICTION_SNAPSHOT, "text": ""},
            {"op": "write", "path": "$RUN/raw/boundaries.json", "text": "{}\n"},
        ):
            chain = self.tampered(op)
            self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, op["path"])
            self.assertEqual(os.listdir(chain.ctx.destination), ["STOPPED-" + ROW6], op["path"])
            self.assertEqual(plan_mode(chain.run_root), 0o644)
            joined = "\n".join(chain.outcome.lines)
            self.assertTrue(
                "changes to the run's own record files" in joined
                or row1().MESSAGE_CHECKS_UNREADABLE in joined
                or row1().MESSAGE_RECORD_UNREADABLE % "s2" in joined,
                op["path"],
            )


class HookSafetyTests(unittest.TestCase):
    """The harness changes a mode itself, so it must never follow a path the model controls (T-04-19)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = SeededPlain(ROW6, "hook-safety-seed")
        cls.paths = cls.seeded.paths
        cls.project = cls.paths["project"]
        cls.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-hook-"))

    def outside_file(self, name: str, mode: int = 0o640) -> str:
        path = os.path.join(self.base, name)
        write_file(path, "outside\n")
        os.chmod(path, mode)
        return path

    def targets(self, relative: str, kind: str = "file"):
        return mock.patch.dict(rowhooks().TARGETS, {HOOK: ((relative, kind),)})

    def mode_of(self, path: str) -> int:
        return os.stat(path).st_mode & 0o777

    def project_modes(self) -> dict:
        found = {}
        for dirpath, dirnames, filenames in os.walk(self.project):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for name in dirnames + filenames:
                full = os.path.join(dirpath, name)
                if not os.path.islink(full):
                    found[os.path.relpath(full, self.project)] = self.mode_of(full)
        return found

    # --- the real table -------------------------------------------------------------------

    def test_the_restriction_sets_444_on_the_plan_file_only_and_the_restore_sets_644_leaving_everything_else_alone(self) -> None:
        hooks = rowhooks()
        before = self.project_modes()
        hooks.restrict_plan_444(None, self.paths, None)
        restricted = self.project_modes()
        self.assertEqual(restricted[PLAN_RELATIVE], 0o444)
        self.assertEqual(dict((k, v) for k, v in restricted.items() if k != PLAN_RELATIVE),
                         dict((k, v) for k, v in before.items() if k != PLAN_RELATIVE))
        hooks.restore_plan_644(None, self.paths, None)
        self.assertEqual(self.project_modes(), dict(before, **{PLAN_RELATIVE: 0o644}))
        self.assertEqual(hashlib.sha256(read_bytes(plan_path(self.seeded.run_root))).hexdigest(),
                         "a4d70690252f755ea6b44d3c3362b345d5126962bb5b4bb40e99ed14a11adf0c", "the content never changed")

    def test_the_hook_and_finalizer_tables_agree_and_name_one_target_inside_the_project(self) -> None:
        hooks = rowhooks()
        self.assertEqual(hooks.TARGETS[HOOK], ((PLAN_RELATIVE, "file"),))
        self.assertEqual(hooks.HOOK_SNAPSHOTS[HOOK], RESTRICTION_SNAPSHOT)
        self.assertEqual(hooks.FINALIZER_OF[HOOK], "restore-plan-644")
        # Row 7 (plan 04-06) adds the project-folder hook and its finalizer to the same tables.
        self.assertEqual(set(hooks.HOOKS), {HOOK, "restrict-project-555"})
        self.assertEqual(set(hooks.FINALIZERS), {"restore-plan-644", "restore-project-755"})
        for relative, kind in hooks.TARGETS[HOOK]:
            self.assertFalse(relative.startswith("/"))
            self.assertNotIn("..", relative.split("/"))
            self.assertIn(kind, ("file", "dir"))

    def test_the_perms_text_is_one_sorted_mode_only_line_per_target_from_the_files_own_status(self) -> None:
        hooks = rowhooks()
        self.assertEqual(hooks.perms_text(self.paths, hooks.TARGETS[HOOK]), (PLAN_RELATIVE + " 644\n").encode("utf-8"))
        two = [("thoughts/plans/" + PLAN_NAME, "file"), ("CLAUDE.md", "file"), ("thoughts", "dir")]
        lines = hooks.perms_text(self.paths, two).decode("utf-8").splitlines()
        self.assertEqual([line.split(" ")[0] for line in lines], sorted(item[0] for item in two))
        for line in lines:
            path, mode = line.split(" ")
            self.assertEqual(len(line.split(" ")), 2)
            self.assertRegex(mode, r"^[0-7]{3}$")
            self.assertEqual(int(mode, 8), self.mode_of(os.path.join(self.project, path)))

    def test_write_perms_creates_one_file_exclusively_inside_the_named_hook_snapshot_only(self) -> None:
        hooks = rowhooks()
        snaps = self.paths["snaps"]
        os.makedirs(os.path.join(snaps, RESTRICTION_SNAPSHOT), exist_ok=True)
        hooks.write_perms(self.paths, hooks.TARGETS[HOOK], RESTRICTION_SNAPSHOT)
        written = os.path.join(snaps, RESTRICTION_SNAPSHOT, "perms.txt")
        self.assertEqual(read_text(written), PLAN_RELATIVE + " 644\n")
        with self.assertRaises(FileExistsError):
            hooks.write_perms(self.paths, hooks.TARGETS[HOOK], RESTRICTION_SNAPSHOT)
        for snapshot in ("snap-1-after-work", "../raw", "snap-0-setup", ""):
            with self.assertRaises(hooks.HookRefused, msg=snapshot):
                hooks.write_perms(self.paths, hooks.TARGETS[HOOK], snapshot)

    # --- a target the model replaced --------------------------------------------------------

    def refused(self, relative: str, kind: str = "file") -> None:
        hooks = rowhooks()
        with self.targets(relative, kind):
            with self.assertRaises(hooks.HookRefused, msg=relative) as caught:
                hooks.restrict_plan_444(None, self.paths, None)
            self.assertNotIn(os.sep, str(caught.exception), "fixed text, no path")
            with self.assertRaises(hooks.HookRefused, msg=relative):
                hooks.restore_plan_644(None, self.paths, None)
            with self.assertRaises(hooks.HookRefused, msg=relative):
                hooks.perms_text(self.paths, [(relative, kind)])

    def test_a_symlink_to_a_file_outside_the_run_root_is_refused_and_the_outside_mode_is_unchanged(self) -> None:
        outside = self.outside_file("outside-one.txt", 0o640)
        os.symlink(outside, os.path.join(self.project, "link-out.txt"))
        self.refused("link-out.txt")
        self.assertEqual(self.mode_of(outside), 0o640)

    def test_a_symlink_to_a_file_inside_the_project_is_refused_too(self) -> None:
        os.symlink(os.path.join(self.project, "CLAUDE.md"), os.path.join(self.project, "link-in.txt"))
        before = self.mode_of(os.path.join(self.project, "CLAUDE.md"))
        self.refused("link-in.txt")
        self.assertEqual(self.mode_of(os.path.join(self.project, "CLAUDE.md")), before)

    def test_a_dangling_symlink_is_refused(self) -> None:
        os.symlink(os.path.join(self.base, "no-such-file"), os.path.join(self.project, "link-dangling.txt"))
        self.refused("link-dangling.txt")

    def test_a_directory_where_a_file_is_expected_is_refused_and_its_mode_is_unchanged(self) -> None:
        os.makedirs(os.path.join(self.project, "a-folder"))
        before = self.mode_of(os.path.join(self.project, "a-folder"))
        self.refused("a-folder")
        self.assertEqual(self.mode_of(os.path.join(self.project, "a-folder")), before)

    def test_a_file_where_a_folder_is_expected_is_refused(self) -> None:
        write_file(os.path.join(self.project, "a-plain-file.txt"), "x\n")
        self.refused("a-plain-file.txt", "dir")

    def test_a_named_pipe_is_refused_without_blocking(self) -> None:
        os.mkfifo(os.path.join(self.project, "a-pipe"))
        self.refused("a-pipe")

    def test_a_socket_file_is_refused(self) -> None:
        here = os.getcwd()
        os.chdir(self.project)
        try:
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind("a-socket")
            listener.close()
        finally:
            os.chdir(here)
        self.refused("a-socket")

    def test_a_second_name_for_a_file_elsewhere_is_refused_and_the_outside_mode_is_unchanged(self) -> None:
        outside = self.outside_file("outside-two.txt", 0o640)
        os.link(outside, os.path.join(self.project, "hard.txt"))
        self.refused("hard.txt")
        self.assertEqual(self.mode_of(outside), 0o640)

    def test_a_parent_folder_swapped_for_a_symlink_is_refused_even_when_it_points_inside_the_project(self) -> None:
        real = os.path.join(self.project, "swap-real")
        os.makedirs(real)
        write_file(os.path.join(real, "file.txt"), "x\n")
        os.symlink(real, os.path.join(self.project, "swap-link"))
        before = self.mode_of(os.path.join(real, "file.txt"))
        self.refused("swap-link/file.txt")
        self.assertEqual(self.mode_of(os.path.join(real, "file.txt")), before)

    def test_a_parent_folder_that_is_a_symlink_to_an_outside_folder_is_refused_and_the_outside_file_is_unchanged(self) -> None:
        folder = os.path.join(self.base, "outside-folder")
        os.makedirs(folder)
        inner = os.path.join(folder, "file.txt")
        write_file(inner, "x\n")
        os.chmod(inner, 0o640)
        os.symlink(folder, os.path.join(self.project, "swap-out"))
        self.refused("swap-out/file.txt")
        self.assertEqual(self.mode_of(inner), 0o640)

    def test_a_missing_target_and_a_missing_parent_are_refused(self) -> None:
        self.refused("no-such-file.txt")
        self.refused("no-such-folder/file.txt")

    def test_a_table_entry_with_a_dot_dot_an_empty_part_a_dot_or_an_unknown_kind_is_refused(self) -> None:
        hooks = rowhooks()
        for relative, kind in (
            ("../raw/run.json", "file"), ("thoughts//plans", "dir"), ("./CLAUDE.md", "file"), ("", "file"),
            ("thoughts/../CLAUDE.md", "file"), ("CLAUDE.md", "socket"), ("CLAUDE.md", ""),
        ):
            with self.assertRaises(hooks.HookRefused, msg=repr(relative)):
                hooks.perms_text(self.paths, [(relative, kind)])

    def test_a_project_folder_that_is_a_symlink_or_not_a_folder_is_refused(self) -> None:
        hooks = rowhooks()
        root = os.path.realpath(tempfile.mkdtemp(prefix="pc-hook-root-"))
        real = os.path.join(root, "real-project")
        write_file(os.path.join(real, "file.txt"), "x\n")
        os.symlink(real, os.path.join(root, "project"))
        before = self.mode_of(os.path.join(real, "file.txt"))
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text({"run_root": root}, [("file.txt", "file")])
        self.assertEqual(self.mode_of(os.path.join(real, "file.txt")), before)
        other = os.path.realpath(tempfile.mkdtemp(prefix="pc-hook-root-"))
        write_file(os.path.join(other, "project"), "not a folder\n")
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text({"run_root": other}, [("file.txt", "file")])
        empty = os.path.realpath(tempfile.mkdtemp(prefix="pc-hook-root-"))
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text({"run_root": empty}, [("file.txt", "file")])

    # --- the run record of a hook -----------------------------------------------------------

    def test_the_finalizers_run_only_for_hooks_that_were_applied_and_only_once(self) -> None:
        hooks = rowhooks()
        spec = spec_of(ROW6)
        run = hooks.HookRun()
        self.assertEqual(hooks.run_finalizers(None, self.paths, spec, run), [], "nothing was applied")
        run.applied.append(HOOK)
        self.assertEqual(run.pending(), [HOOK])
        hooks.restrict_plan_444(None, self.paths, None)
        self.assertEqual(self.mode_of(plan_path(self.seeded.run_root)), 0o444)
        self.assertEqual(hooks.run_finalizers(None, self.paths, spec, run), ["restore-plan-644"])
        self.assertEqual(self.mode_of(plan_path(self.seeded.run_root)), 0o644)
        self.assertEqual(run.pending(), [])
        self.assertEqual(hooks.run_finalizers(None, self.paths, spec, run), [], "idempotent")

    def test_a_refused_finalizer_is_not_retried_and_raises_after_every_pending_finalizer_was_tried(self) -> None:
        hooks = rowhooks()
        spec = spec_of(ROW6)
        run = hooks.HookRun()
        run.applied.append(HOOK)
        with self.targets("link-out.txt"):
            with self.assertRaises(hooks.HookRefused):
                hooks.run_finalizers(None, self.paths, spec, run)
        self.assertEqual(run.pending(), [], "marked restored so the engine never loops on it")

    def test_the_hook_ids_a_row_names_are_checked_when_the_boundaries_are_planned(self) -> None:
        hooks = rowhooks()
        spec = spec_of(ROW6)
        with self.assertRaises(ValueError):
            hooks.plan_boundaries(spec._replace(hooks=(("s1", "no-such-hook"),)))
        with self.assertRaises(ValueError):
            hooks.plan_boundaries(spec._replace(hooks=(("s7", HOOK),)))
        with self.assertRaises(ValueError):
            hooks.hooks_of(spec._replace(hooks=(("s1", "no-such-hook"),)))
        self.assertEqual(hooks.hooks_of(spec, "s1"), [HOOK])
        self.assertEqual(hooks.hooks_of(spec, "s2"), [])


class HookChainSafetyTests(unittest.TestCase):
    """The engine, with the plan file replaced by the scripted claude before the hook or after it."""

    PLAN_TOKEN = "$PROJECT/" + PLAN_RELATIVE

    def planted(self, ops_s1=(), ops_s2=(), mode: int = 0o640, **config):
        """Run row 6 with the scripted claude doing ops_s1 in s1 and ops_s2 in s2; return (run, outside file path)."""
        stages = pc_testutil.default_row_stages(spec_of(ROW6))
        stages = pc_testutil._with_ops(stages, 0, list(ops_s1))
        stages = pc_testutil._with_ops(stages, 1, list(ops_s2))
        rig = pc_testutil.RowRig(stages=stages)
        outside = os.path.join(rig.outside, "target.txt")
        write_file(outside, "outside\n")
        os.chmod(outside, mode)
        return Row6Run(rig=rig), outside

    def assert_refused_stop(self, run, outside: str, mode: int = 0o640) -> None:
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW6])
        stop = read_text(os.path.join(run.ctx.destination, "STOPPED-" + ROW6, "stop.txt"))
        self.assertIn("reason: breach", stop.splitlines())
        readme = read_text(os.path.join(run.ctx.destination, "STOPPED-" + ROW6, "README.md"))
        self.assertIn("Reason: breach", readme.splitlines())
        self.assertEqual(os.stat(outside).st_mode & 0o777, mode, "the outside file's mode is unchanged")
        self.assertEqual(read_text(outside), "outside\n")

    def test_a_plan_replaced_by_a_symlink_to_an_outside_file_before_the_hook_stops_the_row_with_11_and_changes_nothing(self) -> None:
        run, outside = self.planted(
            ops_s1=[{"op": "remove", "path": self.PLAN_TOKEN}, {"op": "symlink", "path": self.PLAN_TOKEN, "target": "$OUTSIDE/target.txt"}]
        )
        self.assert_refused_stop(run, outside)
        self.assertIn(row1().MESSAGE_HOOK_REFUSED % "s1", run.outcome.lines)
        self.assertEqual(len(run.rig.calls()), 1, "s2 never started")
        self.assertFalse(os.path.lexists(os.path.join(run.run_root, "snaps", RESTRICTION_SNAPSHOT)))
        self.assertFalse(os.path.lexists(run.raw("s1-restrict-plan-444.git.json")))

    def test_a_plan_path_that_is_a_directory_a_named_pipe_a_socket_or_a_second_name_is_refused_with_11(self) -> None:
        remove = {"op": "remove", "path": self.PLAN_TOKEN}
        cases = {
            "directory": [remove, {"op": "write", "path": self.PLAN_TOKEN + "/inner.txt", "text": "x\n"}],
            "named pipe": [remove, {"op": "mkfifo", "path": self.PLAN_TOKEN}],
            "socket": [remove, {"op": "socket", "path": self.PLAN_TOKEN}],
            "second name": [remove, {"op": "link", "path": self.PLAN_TOKEN, "target": "$OUTSIDE/target.txt"}],
        }
        for label, ops in cases.items():
            run, outside = self.planted(ops_s1=ops)
            self.assert_refused_stop(run, outside)
            self.assertEqual(len(run.rig.calls()), 1, label)

    def test_a_plan_folder_swapped_for_a_symlink_before_the_hook_is_refused_with_11(self) -> None:
        plans = "$PROJECT/thoughts/plans"
        run, outside = self.planted(
            ops_s1=[
                {"op": "rename", "path": plans, "to": "$PROJECT/thoughts/plans-real"},
                {"op": "symlink", "path": plans, "target": "$PROJECT/thoughts/plans-real"},
            ]
        )
        self.assert_refused_stop(run, outside)
        real = os.path.join(run.run_root, "project", "thoughts", "plans-real", PLAN_NAME)
        self.assertEqual(os.stat(real).st_mode & 0o777, 0o644, "the file behind the link was not touched")

    def test_a_symlink_planted_after_the_hook_is_refused_by_the_finalizer_and_nothing_outside_is_changed(self) -> None:
        run, outside = self.planted(
            ops_s2=[{"op": "remove", "path": self.PLAN_TOKEN}, {"op": "symlink", "path": self.PLAN_TOKEN, "target": "$OUTSIDE/target.txt"}]
        )
        self.assert_refused_stop(run, outside)
        self.assertIn(row1().MESSAGE_RESTORE_REFUSED, run.outcome.lines)
        self.assertEqual(len(run.rig.calls()), 2, "both stages ran; the refusal came at the restore")
        self.assertEqual(run.modes, {"s1": 0o644, "s2": 0o444})

    def test_a_stop_with_a_symlink_planted_in_the_stopped_stage_keeps_the_stops_code_and_adds_the_restore_line(self) -> None:
        stages = pc_testutil.default_row_stages(spec_of(ROW6))
        stages = pc_testutil._with_ops(
            stages, 1,
            [{"op": "remove", "path": self.PLAN_TOKEN}, {"op": "symlink", "path": self.PLAN_TOKEN, "target": "$OUTSIDE/target.txt"}],
        )
        stages = pc_testutil.stages_with(stages, 1, exit=1)
        rig = pc_testutil.RowRig(stages=stages)
        outside = os.path.join(rig.outside, "target.txt")
        write_file(outside, "outside\n")
        os.chmod(outside, 0o640)
        run = Row6Run(rig=rig)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertIn(row1().MESSAGE_RESTORE_REFUSED, run.outcome.lines)
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW6])
        self.assertEqual(os.stat(outside).st_mode & 0o777, 0o640)

    def test_the_finalizer_restores_644_after_a_stop_after_a_breach_and_after_an_exception_in_a_later_stage(self) -> None:
        stop = Row6Run(pc_testutil.stages_with(pc_testutil.default_row_stages(spec_of(ROW6)), 1, exit=1))
        breach = Row6Run(pc_testutil.seed_outside_write(pc_testutil.default_row_stages(spec_of(ROW6)), 1))
        for label, run in (("stop", stop), ("breach", breach)):
            self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, label)
            self.assertEqual(run.modes["s2"], 0o444, label)
            self.assertEqual(plan_mode(run.run_root), 0o644, label)
        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW6)))
        ctx = rig.context()
        original = row1().run_stage
        seen = {}

        def failing(run_ctx, paths, spec, *args, **kwargs):
            seen[spec.name] = plan_mode(str(paths["run_root"]))
            if spec.name == "s2":
                raise RuntimeError("scripted fault")
            return original(run_ctx, paths, spec, *args, **kwargs)

        with mock.patch.object(row1(), "run_stage", failing):
            with self.assertRaises(RuntimeError):
                row1().run_registered_row(ctx, ROW6)
        run_root = os.path.join(ctx.runs_root, os.listdir(ctx.runs_root)[0])
        self.assertEqual(seen, {"s1": 0o644, "s2": 0o444})
        self.assertEqual(plan_mode(run_root), 0o644, "exception")

    def test_a_refused_restore_on_the_exception_path_leaves_the_outside_file_alone_and_the_original_error_comes_out(self) -> None:
        plan = self.PLAN_TOKEN
        stages = pc_testutil.default_row_stages(spec_of(ROW6))
        stages = pc_testutil._with_ops(
            stages, 1, [{"op": "remove", "path": plan}, {"op": "symlink", "path": plan, "target": "$OUTSIDE/target.txt"}]
        )
        rig = pc_testutil.RowRig(stages=stages)
        outside = os.path.join(rig.outside, "target.txt")
        write_file(outside, "outside\n")
        os.chmod(outside, 0o640)
        ctx = rig.context()
        original = row1().run_stage

        def failing(run_ctx, paths, spec, *args, **kwargs):
            result = original(run_ctx, paths, spec, *args, **kwargs)
            if spec.name == "s2":
                raise RuntimeError("scripted fault")
            return result

        with mock.patch.object(row1(), "run_stage", failing):
            with self.assertRaises(RuntimeError):
                row1().run_registered_row(ctx, ROW6)
        self.assertEqual(os.stat(outside).st_mode & 0o777, 0o640)
        self.assertEqual(read_text(outside), "outside\n")

    def test_the_harness_deletes_renames_and_moves_nothing_in_the_hook_module(self) -> None:
        import ast

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_rowhooks.py"), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
        for forbidden in ("remove", "unlink", "rmdir", "rename", "replace", "truncate", "rmtree", "move", "O_TRUNC"):
            self.assertNotIn(forbidden, names, forbidden)


if __name__ == "__main__":
    unittest.main()
