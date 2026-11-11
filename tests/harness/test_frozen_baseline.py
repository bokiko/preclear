"""The frozen digest of a baseline folder and the one sanctioned edit of a filed README (plan 04-18; D-14; T-04-85, T-04-88).

PINNED_BASELINES holds the tree digest of each baseline folder that is pinned: the first baseline now, and the new
baseline's digest in plan 04-21 after its verdict lines are recorded. frozen_digest is the tree digest after the last
line of each row README that starts with the reviewer prefix is read as the pending line and after the single top-level
name codex-review.md is left out, so recording a reviewer line or filing the review file does not change it and any other
change does. record_verdict changes exactly that closing line of one row README of a non-frozen folder, with a positional
write, and refuses everything else with the file byte-identical.

Every scratch folder comes from the shared scripted world of test_baseline and is never deleted. Only reads touch the
committed folders. Leak-shaped strings come only from pc_seeds.
"""
from __future__ import annotations

import io
import os
import re
import unittest

import pc_exitcodes
import pc_seeds
import test_baseline as tb
import test_runroot

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EVIDENCE = os.path.join(ROOT, "tests", "evidence")

# Folder name to the digest of the folder as frozen. Plan 04-21 adds the new baseline here.
PINNED_BASELINES = {
    "rerun-2026-10-29-claude-sonnet-5-5": "f186124f797f320a18772dd44bc11144d773d34f8acf9c4ce7743fe383cd2477",
    "rerun-2026-11-11-claude-sonnet-5-5": "1e4f68bbf7f87c8b57df31414e80d6f2bccc2bee3a336769a71f1efa993dc805",
}
# The first baseline keeps its pending verdict lines, so its tree digest equals its frozen digest. The new baseline holds
# its filed reviewer lines and codex-review.md, so only its frozen digest equals the pin.
TREE_PINNED = frozenset(["rerun-2026-10-29-claude-sonnet-5-5"])

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PENDING = tb.VERDICT_LINE
PREFIX = PENDING[: -len("PENDING")]
SUFFIX = " (see codex-review.md)"


def compare():
    import pc_compare

    return pc_compare


def finalized_world():
    """A scratch copy of the scripted dated folder with finalize already run, so it is a baseline folder."""
    w = tb.fresh_copy_of_world()
    code, out, err = tb.run_baseline(w.rig, ["finalize", "--folder", w.relative()])
    assert code == 0, out + err
    return w


def row_readmes(w):
    found = []
    for name in sorted(os.listdir(w.dated)):
        path = os.path.join(w.dated, name, "README.md")
        if os.path.isfile(path):
            found.append(os.path.join("tests", "evidence", tb.DATED, name, "README.md"))
    return found


def record(w, readme, text, root=None):
    out = io.StringIO()
    err = io.StringIO()
    code = tb.baseline().record_verdict(readme, text, root=w.rig.repo if root is None else root, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def row1_readme():
    return os.path.join("tests", "evidence", tb.DATED, tb.ROW1, "README.md")


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


class PinnedTableTests(unittest.TestCase):
    def test_every_pinned_value_is_64_lower_case_hex_and_names_a_committed_folder(self):
        self.assertEqual(
            sorted(PINNED_BASELINES),
            ["rerun-2026-10-29-claude-sonnet-5-5", "rerun-2026-11-11-claude-sonnet-5-5"],
            "the first baseline and the new baseline",
        )
        for name, value in PINNED_BASELINES.items():
            self.assertIsNotNone(HEX64.match(value), name)
            self.assertTrue(os.path.isdir(os.path.join(EVIDENCE, name)), name)
        self.assertIn("rerun-2026-10-29-claude-sonnet-5-5", tb.baseline().FROZEN_FOLDERS, "the first baseline is frozen")

    def test_every_pinned_baseline_matches_through_the_tree_digest_and_the_frozen_digest(self):
        for name, value in PINNED_BASELINES.items():
            folder = os.path.join(EVIDENCE, name)
            before = tb.tree_snapshot(folder)
            if name in TREE_PINNED:
                self.assertEqual(compare().tree_digest(folder), value, name + ": tree digest")
            self.assertEqual(tb.baseline().frozen_digest(folder), value, name + ": frozen digest")
            self.assertEqual(tb.tree_snapshot(folder), before, name + " was only read")

    def test_the_first_baseline_row_readme_holds_the_pending_line_so_normalisation_changes_nothing(self):
        text = tb.read_text(os.path.join(EVIDENCE, "rerun-2026-10-29-claude-sonnet-5-5", "row1-wrong-binding", "README.md"))
        self.assertTrue(text.endswith("\n" + PENDING + "\n"))


class FrozenDigestTests(unittest.TestCase):
    """The frozen digest allows exactly the reviewer line of a row README and the file codex-review.md."""

    def setUp(self):
        self.w = finalized_world()
        self.digest = tb.baseline().frozen_digest(self.w.dated)

    def frozen(self):
        return tb.baseline().frozen_digest(self.w.dated)

    def test_it_is_the_tree_digest_while_no_reviewer_line_and_no_review_file_exist(self):
        self.assertEqual(self.digest, compare().tree_digest(self.w.dated))

    def test_recording_a_reviewer_line_on_every_row_readme_leaves_it_unchanged_and_changes_the_tree_digest(self):
        tree_before = compare().tree_digest(self.w.dated)
        readmes = row_readmes(self.w)
        self.assertGreaterEqual(len(readmes), 4)
        for index, readme in enumerate(readmes):
            code, out, err = record(self.w, readme, "a conclusion %d and the reason" % index)
            self.assertEqual(code, 0, out + err)
        self.assertEqual(self.frozen(), self.digest)
        self.assertNotEqual(compare().tree_digest(self.w.dated), tree_before)

    def test_adding_codex_review_md_at_the_top_leaves_it_unchanged(self):
        source = os.path.join(self.w.rig.base, "review.txt")
        with open(source, "xb") as handle:
            handle.write(b"the reviewer's own words\n")
        code, out, err = tb.run_baseline(self.w.rig, ["file-review", "--folder", self.w.relative(), "--from", source])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.frozen(), self.digest)
        self.assertNotEqual(compare().tree_digest(self.w.dated), self.digest)

    def test_a_codex_review_md_inside_a_row_folder_changes_it(self):
        with open(os.path.join(self.w.dated, tb.ROW1, "codex-review.md"), "xb") as handle:
            handle.write(b"x\n")
        self.assertNotEqual(self.frozen(), self.digest)

    def test_a_one_byte_change_to_a_trace_changes_it(self):
        path = os.path.join(self.w.dated, tb.ROW1, "s1-work-full-trace.md")
        with open(path, "ab") as handle:
            handle.write(b"x")
        self.assertNotEqual(self.frozen(), self.digest)

    def test_a_second_changed_readme_line_changes_it_even_with_a_recorded_reviewer_line(self):
        readme = row1_readme()
        self.assertEqual(record(self.w, readme, "a conclusion and the reason")[0], 0)
        self.assertEqual(self.frozen(), self.digest)
        path = os.path.join(self.w.rig.repo, readme)
        text = tb.read_text(path)
        first = [line for line in text.splitlines() if line.startswith("- [ ]")][0]
        with open(path, "wb") as handle:
            handle.write(text.replace(first, first + " ", 1).encode("utf-8"))
        self.assertNotEqual(self.frozen(), self.digest)

    def test_a_changed_closing_line_that_does_not_start_with_the_prefix_changes_it(self):
        path = os.path.join(self.w.dated, tb.ROW1, "README.md")
        text = tb.read_text(path)
        with open(path, "wb") as handle:
            handle.write(text[: -len(PENDING) - 1].encode("utf-8") + b"Reviewed: PENDING\n")
        self.assertNotEqual(self.frozen(), self.digest)

    def test_an_added_file_at_the_top_or_in_a_row_folder_changes_it(self):
        with open(os.path.join(self.w.dated, "extra.txt"), "xb") as handle:
            handle.write(b"x\n")
        self.assertNotEqual(self.frozen(), self.digest)
        other = finalized_world()
        digest = tb.baseline().frozen_digest(other.dated)
        with open(os.path.join(other.dated, tb.ROW1, "extra.txt"), "xb") as handle:
            handle.write(b"x\n")
        self.assertNotEqual(tb.baseline().frozen_digest(other.dated), digest)

    def test_a_changed_top_level_readme_changes_it(self):
        with open(os.path.join(self.w.dated, "README.md"), "ab") as handle:
            handle.write(b"x\n")
        self.assertNotEqual(self.frozen(), self.digest)

    def test_an_empty_added_folder_changes_it(self):
        os.makedirs(os.path.join(self.w.dated, "empty-folder"))
        self.assertNotEqual(self.frozen(), self.digest)


class VerdictLineTests(unittest.TestCase):
    """record_verdict: the in-place edit and every refusal (T-04-85)."""

    def setUp(self):
        self.w = finalized_world()
        self.readme = row1_readme()
        self.path = os.path.join(self.w.rig.repo, self.readme)

    def test_it_replaces_only_the_closing_line_in_place_and_the_file_only_grows(self):
        before = read_bytes(self.path)
        inode = os.stat(self.path).st_ino
        code, out, err = record(self.w, self.readme, "partly as expected, see the helper counts")
        self.assertEqual(code, 0, out + err)
        after = read_bytes(self.path)
        keep = len(before) - len((PENDING + "\n").encode("utf-8"))
        self.assertEqual(after[:keep], before[:keep], "every byte before the line is unchanged")
        self.assertEqual(after[keep:], (PREFIX + "partly as expected, see the helper counts" + SUFFIX + "\n").encode("utf-8"))
        self.assertGreater(len(after), len(before))
        self.assertEqual(os.stat(self.path).st_ino, inode, "written in place")
        self.assertEqual(out, "recorded: 1 line, %d byte(s) added\n" % (len(after) - len(before)))
        self.assertEqual(err, "")
        self.assertNotIn("partly", out + err, "the text is never printed")

    def test_the_other_files_of_the_folder_are_untouched(self):
        before = tb.tree_snapshot(self.w.dated)
        self.assertEqual(record(self.w, self.readme, "a conclusion")[0], 0)
        after = tb.tree_snapshot(self.w.dated)
        changed = [name for name in before if before[name] != after[name]]
        self.assertEqual(changed, [os.path.relpath(self.path, self.w.dated)])
        self.assertEqual(sorted(set(after) - set(before)), [])

    def test_a_text_of_exactly_400_characters_is_accepted_and_401_is_refused(self):
        self.assertEqual(record(self.w, self.readme, "a" * 401)[0], pc_exitcodes.USAGE)
        self.assertEqual(record(self.w, self.readme, "a b" * 133 + "c")[0], 0, "400 characters")

    def refused(self, readme, text="a conclusion", root=None, code=pc_exitcodes.USAGE):
        path = os.path.join(self.w.rig.repo if root is None else root, readme) if not os.path.isabs(readme) else readme
        before = read_bytes(path) if os.path.isfile(path) and not os.path.islink(path) else None
        result, out, err = record(self.w, readme, text, root=root)
        self.assertEqual(result, code, out + err)
        self.assertEqual(out, "")
        if before is not None:
            self.assertEqual(read_bytes(path), before, "the file is byte-identical")
        if isinstance(text, str) and text.strip():
            self.assertNotIn(text, out + err)
        return err

    def test_a_text_of_two_lines_or_with_a_control_character_or_blank_is_refused(self):
        for text in ("one\ntwo", "one\rtwo", "tab\there", "nul\x00here", "", "   ", "line break", 5, None):
            self.refused(self.readme, text)

    def test_a_readme_without_the_pending_line_is_refused(self):
        with open(self.path, "wb") as handle:
            handle.write(b"# Row\n\nno closing line\n")
        self.refused(self.readme)

    def test_a_readme_with_the_pending_line_twice_is_refused(self):
        with open(self.path, "ab") as handle:
            handle.write((PENDING + "\n").encode("utf-8"))
        self.refused(self.readme)

    def test_a_readme_with_another_line_that_starts_with_the_prefix_is_refused(self):
        text = tb.read_text(self.path)
        with open(self.path, "wb") as handle:
            handle.write((text.replace("## Stages", PREFIX + "x\n## Stages", 1)).encode("utf-8"))
        self.refused(self.readme)

    def test_a_readme_with_text_after_the_pending_line_is_refused(self):
        with open(self.path, "ab") as handle:
            handle.write(b"trailing\n")
        self.refused(self.readme)
        with open(self.path, "ab") as handle:
            handle.write(b"\n")
        self.refused(self.readme)

    def test_a_readme_that_does_not_end_with_a_newline_is_refused(self):
        text = tb.read_text(self.path)
        with open(self.path, "wb") as handle:
            handle.write(text.rstrip("\n").encode("utf-8"))
        self.refused(self.readme)

    def test_a_second_record_on_the_same_readme_is_refused(self):
        self.assertEqual(record(self.w, self.readme, "a conclusion")[0], 0)
        self.refused(self.readme)

    def test_a_readme_of_a_frozen_folder_is_refused(self):
        for name in sorted(tb.baseline().FROZEN_FOLDERS):
            folder = os.path.join(self.w.rig.repo, "tests", "evidence", name, tb.ROW1)
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "README.md")
            if not os.path.exists(path):
                with open(path, "xb") as handle:
                    handle.write(("# Row\n\n" + PENDING + "\n").encode("utf-8"))
            self.refused(os.path.join("tests", "evidence", name, tb.ROW1, "README.md"))

    def test_a_readme_outside_a_row_folder_or_outside_the_evidence_tree_or_of_another_name_is_refused(self):
        top = os.path.join("tests", "evidence", tb.DATED, "README.md")
        self.refused(top)
        deeper = os.path.join("tests", "evidence", tb.DATED, tb.ROW1, "snap-0-setup", "README.md")
        os.makedirs(os.path.join(self.w.rig.repo, os.path.dirname(deeper)), exist_ok=True)
        with open(os.path.join(self.w.rig.repo, deeper), "xb") as handle:
            handle.write((PENDING + "\n").encode("utf-8"))
        self.refused(deeper)
        outside = os.path.join(self.w.rig.base, "outside-readme.md")
        with open(outside, "xb") as handle:
            handle.write(("# x\n" + PENDING + "\n").encode("utf-8"))
        self.refused(outside)
        other = os.path.join("tests", "evidence", tb.DATED, tb.ROW1, "mechanical-checks.md")
        with open(os.path.join(self.w.rig.repo, other), "ab") as handle:
            handle.write((PENDING + "\n").encode("utf-8"))
        self.refused(other)
        for bad in ("", "..", "tests/evidence/../evidence/%s/%s/README.md" % (tb.DATED, tb.ROW1), "a\x00b", 5, None):
            result, out, err = record(self.w, bad, "a conclusion")
            self.assertEqual(result, pc_exitcodes.USAGE)

    def test_a_folder_that_is_not_a_dated_folder_or_a_row_folder_name_is_refused(self):
        for dated, row in (("not-dated", tb.ROW1), (tb.DATED, "not-a-row"), (tb.DATED, "row1-wrong-binding-extra")):
            folder = os.path.join(self.w.rig.repo, "tests", "evidence", dated, row)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "README.md"), "xb") as handle:
                handle.write(("# x\n" + PENDING + "\n").encode("utf-8"))
            self.refused(os.path.join("tests", "evidence", dated, row, "README.md"))

    def test_a_symlinked_readme_or_a_symlinked_folder_is_refused(self):
        real = os.path.join(self.w.dated, "linked-target")
        os.makedirs(os.path.join(self.w.dated, "row2-double-conflict"))
        target = os.path.join(self.w.rig.base, "target-readme.md")
        with open(target, "xb") as handle:
            handle.write((PENDING + "\n").encode("utf-8"))
        os.symlink(target, os.path.join(self.w.dated, "row2-double-conflict", "README.md"))
        self.refused(os.path.join("tests", "evidence", tb.DATED, "row2-double-conflict", "README.md"))
        self.assertEqual(read_bytes(target), (PENDING + "\n").encode("utf-8"))
        os.symlink(os.path.join(self.w.dated, tb.ROW1), os.path.join(self.w.dated, "row5a-no-memory"))
        self.refused(os.path.join("tests", "evidence", tb.DATED, "row5a-no-memory", "README.md"))
        self.assertFalse(os.path.exists(real))

    def test_a_leak_shaped_text_is_refused_with_14_and_the_file_is_unchanged(self):
        seeded = "see " + pc_seeds.home_path("pcsynthhome") + "/data"
        err = self.refused(self.readme, seeded, code=pc_exitcodes.LEAK_REFUSED)
        self.assertIn("leak gate", err)

    def test_the_static_scan_finds_no_truncating_open_delete_rename_or_overwrite_in_the_module(self):
        self.assertEqual(test_runroot.scan_source(tb.read_text(os.path.join(HERE, "pc_baseline.py")).encode("utf-8")), [])
        self.assertIn("os.pwrite", tb.read_text(os.path.join(HERE, "pc_baseline.py")), "the write is positional")

    def test_the_real_committed_row_readmes_are_refused_and_stay_as_they_are(self):
        for name in ("rerun-2026-10-29-claude-sonnet-5-5", "rerun-2026-11-09-claude-sonnet-5-5-triple"):
            folder = os.path.join(EVIDENCE, name)
            for row in sorted(os.listdir(folder)):
                path = os.path.join(folder, row, "README.md")
                if os.path.isfile(path):
                    before = read_bytes(path)
                    code, out, err = record(self.w, os.path.join("tests", "evidence", name, row, "README.md"), "x", root=ROOT)
                    self.assertEqual(code, pc_exitcodes.USAGE, name)
                    self.assertEqual(read_bytes(path), before)


if __name__ == "__main__":
    unittest.main()
