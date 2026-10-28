"""Zero-token tests for the mechanical checks (plan 03-03; HARN-09, D-03, D-09).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every
folder comes from tempfile or RowRig and is never deleted. pc_checks is imported inside each test, so a
missing module is one error per test and not one load failure of the file. Assertion labels are fixed text.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import pc_exitcodes
import pc_row1
import pc_testutil

SNAP_SETUP = "snap-0-setup"
SNAP_ONE = "snap-1-after-work"
SNAP_TWO = "snap-2-after-preclear"
SNAP_THREE = "snap-3-after-resume"


def checks():
    import pc_checks

    return pc_checks


def digest(last: str = "0") -> str:
    return "a" * 63 + last


def file_entry(path: str, sha: str = None, size: int = 3) -> dict:
    return {"path": path, "kind": "f", "size": size, "sha256": sha if sha is not None else digest(), "target": None}


def dir_entry(path: str) -> dict:
    return {"path": path, "kind": "d", "size": None, "sha256": None, "target": None}


def write_manifest(folder: str, entries) -> str:
    """Create folder and a manifest.jsonl in it from entry mappings; return folder."""
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "manifest.jsonl"), "w", encoding="utf-8") as handle:
        for item in entries:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    return folder


def mapping(entries) -> dict:
    return dict((item["path"], item) for item in entries)


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class Run(object):
    """A rig, a context and the outcome of one run_row call."""

    def __init__(self, stages=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.ctx = self.rig.context()
        self.outcome = pc_row1.run_row(self.ctx)

    @property
    def run_root(self) -> str:
        names = os.listdir(self.ctx.runs_root)
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    def facts(self):
        return checks().compute_facts(self.run_root, self.ctx.config_dir)


class BoundaryTests(unittest.TestCase):
    def test_load_manifest_reads_a_snapshot_and_refuses_a_missing_or_malformed_file(self) -> None:
        c = checks()
        base = tempfile.mkdtemp(prefix="pc-checks-")
        good = write_manifest(os.path.join(base, "good"), [dir_entry("project"), file_entry("project/a", digest("7"))])
        loaded = c.load_manifest(good)
        self.assertEqual(sorted(loaded), ["project", "project/a"], "both paths are loaded")
        self.assertEqual(loaded["project/a"]["kind"], "f", "the kind is kept")
        self.assertEqual(loaded["project/a"]["size"], 3, "the size is kept")
        self.assertEqual(loaded["project/a"]["sha256"], digest("7"), "the whole digest is kept")
        self.assertEqual(loaded["project"]["kind"], "d", "a directory entry is kept")
        with self.assertRaises(c.CheckError, msg="a missing snapshot folder is refused"):
            c.load_manifest(os.path.join(base, "no-such-folder"))
        bad_lines = [
            "not json at all",
            "[1, 2]",
            json.dumps({"path": "x", "kind": "f", "size": 1}),
            json.dumps({"path": "x", "kind": "f", "size": 1, "sha256": "abc"}),
            json.dumps({"path": "x", "kind": "f", "size": 1, "sha256": "A" * 64}),
            json.dumps({"path": "x", "kind": "q", "size": None, "sha256": None}),
            json.dumps({"path": 7, "kind": "d", "size": None, "sha256": None}),
        ]
        for number, line in enumerate(bad_lines):
            folder = os.path.join(base, "bad%d" % number)
            os.makedirs(folder)
            with open(os.path.join(folder, "manifest.jsonl"), "w", encoding="utf-8") as handle:
                handle.write(line + "\n")
            with self.assertRaises(c.CheckError, msg="a malformed line is refused (case %d)" % number):
                c.load_manifest(folder)
        twice = os.path.join(base, "twice")
        write_manifest(twice, [dir_entry("project"), dir_entry("project")])
        with self.assertRaises(c.CheckError, msg="a repeated path is refused"):
            c.load_manifest(twice)

    def test_diff_lists_added_changed_and_removed_paths(self) -> None:
        c = checks()
        before = mapping([file_entry("a"), file_entry("b"), file_entry("c"), dir_entry("d")])
        after = mapping([file_entry("a"), file_entry("b", digest("1")), file_entry("e"), dir_entry("d")])
        found = c.diff_manifests(before, after)
        self.assertEqual(sorted(found), [("added", "e"), ("changed", "b"), ("removed", "c")], "one entry per change")

    def test_a_digest_that_differs_only_in_the_last_character_is_a_change(self) -> None:
        c = checks()
        before = mapping([file_entry("x", digest("0"))])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("1"))])), [("changed", "x")])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("0"))])), [], "same digest, no change")

    def test_a_change_of_kind_or_size_is_a_change(self) -> None:
        c = checks()
        before = mapping([file_entry("x", digest("0"), 3)])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("0"), 4)])), [("changed", "x")])
        self.assertEqual(c.diff_manifests(before, mapping([dir_entry("x")])), [("changed", "x")])

    def test_the_approved_roots_and_the_expected_change_are_the_documented_ones(self) -> None:
        c = checks()
        self.assertEqual(tuple(c.APPROVED_ROOTS), ("project", "ckpt", "auto-memory"))
        self.assertEqual(tuple(c.EXPECTED_CHANGES), ("wrapper/calls.log",))

    def test_the_root_match_is_component_aware(self) -> None:
        c = checks()
        inside = ["project/x", "ckpt/ledgers/x", "auto-memory/y", "project", "ckpt", "auto-memory"]
        outside = [
            "project-other/x",
            "project.bak",
            "ckpt2/x",
            "auto-memory-old/x",
            "wrapper/py",
            "wrapper/stub",
            "settings.json",
            "newtop/file",
            "newtop",
        ]
        for path in inside:
            found = c.outside_changes([("added", path)], c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
            self.assertEqual(found, [], "inside the approved roots: %s" % path)
        for path in outside:
            found = c.outside_changes([("added", path)], c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
            self.assertEqual(found, [path], "outside the approved roots: %s" % path)

    def test_a_changed_call_log_is_expected_and_a_removed_outside_file_is_listed(self) -> None:
        c = checks()
        diff = [("changed", "wrapper/calls.log"), ("removed", "stray.txt"), ("changed", "wrapper/checkpoint")]
        found = c.outside_changes(diff, c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
        self.assertEqual(found, ["stray.txt", "wrapper/checkpoint"], "the log is excluded and nothing else is")
        self.assertEqual(c.outside_changes([("removed", "wrapper/calls.log.bak")], c.APPROVED_ROOTS, c.EXPECTED_CHANGES),
                         ["wrapper/calls.log.bak"], "only the exact expected path is excluded")

    def test_write_boundary_diffs_consecutive_pairs_and_first_against_last_and_counts_a_path_once(self) -> None:
        c = checks()
        base = tempfile.mkdtemp(prefix="pc-checks-")
        common = [dir_entry("project"), file_entry("project/a"), file_entry("wrapper/calls.log", digest("0"))]
        write_manifest(os.path.join(base, SNAP_SETUP), common)
        write_manifest(os.path.join(base, SNAP_ONE), common + [file_entry("stray.txt")])
        write_manifest(os.path.join(base, SNAP_TWO), common + [file_entry("stray.txt", digest("9")), file_entry("project/b")])
        found = c.write_boundary(base, [SNAP_SETUP, SNAP_ONE, SNAP_TWO])
        self.assertEqual(found["paths"], ["stray.txt"], "the same path in three pairs is listed once")
        self.assertEqual(found["count"], 1, "and counted once")
        quiet = c.write_boundary(base, [SNAP_SETUP])
        self.assertEqual(quiet["count"], 0, "one snapshot has nothing to compare")
        changed_log = os.path.join(base, "log")
        os.makedirs(changed_log)
        write_manifest(os.path.join(changed_log, SNAP_SETUP), common)
        write_manifest(os.path.join(changed_log, SNAP_ONE),
                       [dir_entry("project"), file_entry("project/a"), file_entry("wrapper/calls.log", digest("5"))])
        self.assertEqual(c.write_boundary(changed_log, [SNAP_SETUP, SNAP_ONE])["count"], 0, "the call log may change")


class TracerTests(unittest.TestCase):
    def test_a_clean_default_run_reports_zero_and_returns_zero(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertEqual(facts["write_boundary"]["count"], 0, "no write outside the approved roots")
        self.assertEqual(checks().breaches(facts), [], "no breach")

    def test_a_seeded_write_outside_the_roots_is_reported_and_ends_the_row_with_11(self) -> None:
        stages = pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1)
        run = Run(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertGreaterEqual(facts["write_boundary"]["count"], 1, "the write is counted")
        self.assertIn("outside.txt", facts["write_boundary"]["paths"], "the path is run-root relative text")
        ids = [name for name, _count in checks().breaches(facts)]
        self.assertIn("writes-outside-approved-roots", ids, "the breach is named")
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: writes outside approved roots: [1-9][0-9]*", "count in text")
        self.assertNotIn("outside.txt", text, "no path in the text")
        self.assertNotIn(run.rig.base, text, "no folder in the text")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s2.stdout")), "the raw bytes stay")
        for name in (SNAP_SETUP, SNAP_ONE, SNAP_TWO):
            self.assertTrue(os.path.isdir(os.path.join(run.run_root, "snaps", name)), "snapshot kept: " + name)
        self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")
        self.assertFalse(os.path.exists(os.path.join(raw, "s3.stdout")), "no third stage output")

    def test_the_facts_are_computed_from_files_alone_and_repeat(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        first = run.facts()
        second = run.facts()
        self.assertEqual(first, second, "the same call gives equal facts")
        self.assertEqual(json.loads(json.dumps(first)), first, "the facts are plain values")


if __name__ == "__main__":
    unittest.main()
