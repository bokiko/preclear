"""Zero-token tests for the read-only comparer (plan 03-05; EVID-06, D-07, D-08).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. The old side
of the tracer is the real committed publication folder, which is only read. Every scratch folder comes from
tempfile.mkdtemp or RowRig and is never deleted by a test. Assertion labels are fixed text, and values that look
like leaks are built at run time from fragments. pc_compare is imported inside each test, so a missing module is
one error per test and not one load failure of the file.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import os
import unittest

import pc_exitcodes
import pc_manifest
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
PUBLICATION = os.path.join(REPO_ROOT, "tests", "evidence", "publication-2026-10-20")
ROW1 = "row1-wrong-binding"
DEST_NAME = "rerun-2026-10-28-claude-sonnet-5-5"

# The files that only a rerun produces (plan 03-04), relative to the row folder.
RERUN_ONLY_FILES = (
    "mechanical-checks.md",
    "usage.txt",
    "model-id.txt",
    "isolation-mode.txt",
    "harness-version.txt",
    "s1-work-prompt.md",
    "s1-work-full-trace.md",
    "settings.json",
    "s3-resume-trace.md",
    "s3-resume-full-trace.md",
    "s3-resume.err",
    "s3-resume.exit",
    "resume-line.txt",
    "session-resume.id",
    "snap-0-setup/manifest.jsonl",
    "snap-1-after-work/manifest.jsonl",
    "snap-2-after-preclear/manifest.jsonl",
    "snap-3-after-resume/sha.txt",
    "snap-3-after-resume/manifest.jsonl",
)


def compare():
    import pc_compare

    return pc_compare


def matrix():
    import pc_matrix

    return pc_matrix


def fixed_clock() -> datetime.datetime:
    return datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)


def run_compare(*args):
    """Call the comparer in process; return (exit code, stdout text, stderr text)."""
    out = io.StringIO()
    err = io.StringIO()
    code = compare().main(list(args), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def relative_files(root):
    """Return the set of 'path' and 'path/' entries (files and folders) below root, with forward slashes."""
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/") + "/")
        for name in filenames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/"))
    return found


def listed_after(text, header):
    """Return the indented entries that follow the line starting with header, up to the next unindented line."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(header):
            found = []
            for entry in lines[index + 1:]:
                if not entry.startswith("  "):
                    break
                found.append(entry[2:])
            return found
    raise AssertionError("a report header is missing")


def digest_line(text, prefix):
    """Return (old digest, new digest) from the line that starts with prefix."""
    for line in text.splitlines():
        if line.startswith(prefix):
            body = line[len(prefix):]
            old_part, new_part = body.split(", new ")
            assert old_part.startswith("old ")
            return old_part[len("old "):], new_part
    raise AssertionError("a digest line is missing")


class Fake(object):
    """A rig whose whole row ran through the driver with the scripted claude; the promoted folder is kept."""

    def __init__(self):
        import io as _io

        self.rig = pc_testutil.RowRig()
        out = _io.StringIO()
        err = _io.StringIO()
        self.code = matrix().main(
            ["--row", ROW1, "--claude", self.rig.claude, "--budget", "2.00"],
            env=dict(self.rig.env),
            repo_root=self.rig.repo,
            clock=fixed_clock,
            out=out,
            err=err,
        )

    @property
    def destination(self):
        return os.path.join(self.rig.repo, "tests", "evidence", DEST_NAME)


class TracerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = Fake()
        cls.publication_before = compare().tree_digest(PUBLICATION)
        cls.code, cls.out, cls.err = run_compare("--old", PUBLICATION, "--new", cls.fake.destination)

    def test_the_fake_pipeline_filed_a_new_side(self):
        self.assertEqual(self.fake.code, pc_exitcodes.OK, "the scripted row ran to the end and filed")
        self.assertTrue(os.path.isdir(os.path.join(self.fake.destination, ROW1)), "the new side holds the row folder")

    def test_the_comparison_exits_0_and_prints_a_report(self):
        self.assertEqual(self.code, pc_exitcodes.OK, "the comparer exits 0 when both trees were readable")
        self.assertTrue(self.out.strip() != "", "the report is not empty")
        self.assertEqual(self.err, "", "nothing is printed on the error stream")

    def test_the_digests_before_and_after_are_equal_for_both_trees(self):
        before = digest_line(self.out, "tree digest before: ")
        after = digest_line(self.out, "tree digest after: ")
        self.assertEqual(before, after, "the digests before and after are equal for both trees")
        for value in before + after:
            self.assertEqual(len(value), 64, "a digest is 64 hex characters")
            self.assertEqual(value, value.lower(), "a digest is lower case")
        self.assertIn("old unchanged: yes", self.out.splitlines(), "the old tree is reported unchanged")
        self.assertIn("new unchanged: yes", self.out.splitlines(), "the new tree is reported unchanged")

    def test_the_real_committed_folder_has_the_same_digest_before_and_after(self):
        self.assertEqual(self.publication_before, compare().tree_digest(PUBLICATION), "the committed folder is unchanged")
        before = digest_line(self.out, "tree digest before: ")
        self.assertEqual(before[0], self.publication_before, "the printed digest is the digest of the committed folder")

    def test_the_header_names_the_row_and_the_two_folder_base_names_only(self):
        first = self.out.splitlines()[0]
        self.assertEqual(
            first,
            "compare row %s: old %s, new %s" % (ROW1, os.path.basename(PUBLICATION), DEST_NAME),
            "the first line names the row and the folder base names",
        )
        self.assertNotIn(self.fake.rig.repo, self.out, "no scratch path is printed")
        self.assertNotIn(REPO_ROOT, self.out, "no repository path is printed")

    def test_the_rerun_only_files_are_listed_as_present_on_the_rerun_side_only(self):
        new_only = listed_after(self.out, "files only on the rerun side: ")
        for name in RERUN_ONLY_FILES:
            self.assertIn(name, new_only, "a rerun-only file is listed on the rerun side")
        self.assertIn("snap-3-after-resume/", new_only, "the resume snapshot folder is listed on the rerun side")
        self.assertIn("(a file only on the rerun side is a difference, not a fault)", self.out.splitlines(), "the neutral sentence is printed")

    def test_both_directions_equal_an_independent_walk_of_the_two_row_folders(self):
        old_row = os.path.join(PUBLICATION, ROW1)
        new_row = os.path.join(self.fake.destination, ROW1)
        old_entries = relative_files(old_row)
        new_entries = relative_files(new_row)
        self.assertEqual(
            set(listed_after(self.out, "files only on the old side: ")), old_entries - new_entries, "the old-side list equals the walk"
        )
        self.assertEqual(
            set(listed_after(self.out, "files only on the rerun side: ")), new_entries - old_entries, "the rerun-side list equals the walk"
        )

    def test_a_listing_is_sorted(self):
        for header in ("files only on the old side: ", "files only on the rerun side: "):
            entries = listed_after(self.out, header)
            self.assertEqual(entries, sorted(entries, key=lambda item: item.encode("utf-8")), "a listing is sorted")

    def test_the_differences_header_is_neutral(self):
        self.assertIn("differences, listed and not judged", self.out.splitlines(), "the neutral differences line is printed")


class DigestTests(unittest.TestCase):
    def test_tree_digest_is_the_sha256_of_the_lossless_manifest(self):
        folder = os.path.join(PUBLICATION, ROW1)
        expected = hashlib.sha256(pc_manifest.jsonl_bytes(pc_manifest.tree_manifest(folder))).hexdigest()
        self.assertEqual(compare().tree_digest(folder), expected, "the digest is sha256 over the manifest bytes")

    def test_the_digest_of_the_committed_folder_is_stable_across_two_comparison_runs(self):
        before = compare().tree_digest(PUBLICATION)
        run_compare("--old", PUBLICATION, "--new", PUBLICATION)
        run_compare("--old", PUBLICATION, "--new", PUBLICATION)
        self.assertEqual(compare().tree_digest(PUBLICATION), before, "two runs leave the committed folder unchanged")


class ExitTests(unittest.TestCase):
    def test_a_folder_compared_with_itself_exits_0(self):
        code, out, _err = run_compare("--old", PUBLICATION, "--new", PUBLICATION)
        self.assertEqual(code, pc_exitcodes.OK, "the same readable folder on both sides exits 0")
        self.assertEqual(listed_after(out, "files only on the old side: "), [], "nothing is only on the old side")
        self.assertEqual(listed_after(out, "files only on the rerun side: "), [], "nothing is only on the rerun side")

    def test_two_readable_trees_that_differ_still_exit_0(self):
        import tempfile

        old = tempfile.mkdtemp(prefix="pc-cmp-old-")
        new = tempfile.mkdtemp(prefix="pc-cmp-new-")
        os.makedirs(os.path.join(old, ROW1))
        os.makedirs(os.path.join(new, ROW1))
        with open(os.path.join(old, ROW1, "only-old.txt"), "w") as handle:
            handle.write("x\n")
        with open(os.path.join(new, ROW1, "only-new.txt"), "w") as handle:
            handle.write("y\n")
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "a readable pair exits 0 whatever they differ in")
        self.assertEqual(listed_after(out, "files only on the old side: "), ["only-old.txt"], "the old-only file is listed")
        self.assertEqual(listed_after(out, "files only on the rerun side: "), ["only-new.txt"], "the new-only file is listed")


if __name__ == "__main__":
    unittest.main()
