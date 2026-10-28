"""Zero-token tests for the read-only comparer (plan 03-05; EVID-06, D-07, D-08).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. The old side
of the tracer is the real committed publication folder, which is only read. Every scratch folder comes from
tempfile.mkdtemp or RowRig and is never deleted by a test. Assertion labels are fixed text, and values that look
like leaks are built at run time from fragments. pc_compare is imported inside each test, so a missing module is
one error per test and not one load failure of the file.
"""
from __future__ import annotations

import builtins
import contextlib
import datetime
import hashlib
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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


_SHARED = []


def shared_fake():
    """One fake-pipeline world for every class of this file (built on first use, never deleted)."""
    if not _SHARED:
        _SHARED.append(Fake())
    return _SHARED[0]


class TracerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = shared_fake()
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


SHA_X = hashlib.sha256(b"x").hexdigest()
SHA_Y = hashlib.sha256(b"y").hexdigest()


def make_tree(files, row=ROW1):
    """Build a scratch tree holding the row folder; a key ending in a slash is an empty folder."""
    base = tempfile.mkdtemp(prefix="pc-cmp-")
    row_dir = os.path.join(base, row)
    os.makedirs(row_dir)
    for rel, data in files.items():
        full = os.path.join(row_dir, *rel.rstrip("/").split("/"))
        if rel.endswith("/"):
            os.makedirs(full, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    return base


def trace_text(calls, header_calls=None, flagged=0, old_header=False):
    """A full-trace text with the committed heading shapes. calls: (name, flags) pairs."""
    count = len(calls) if header_calls is None else header_calls
    tail = "refusal/denial/permission/EACCES" if old_header else "refusal/denial"
    lines = ["# r: s: complete sanitized tool calls and results", "", "Calls %d; results flagged as %s: %d." % (count, tail, flagged), ""]
    for number, (name, flags) in enumerate(calls, 1):
        suffix = "".join("  " + flag for flag in flags)
        if name in ("Read", "Glob", "Grep"):
            lines.append("### %d. %s (toolu_%04d): `<run>/x` -> result 5 chars%s" % (number, name, number, suffix))
        else:
            lines.append("### %d. %s (toolu_%04d)%s" % (number, name, number, suffix))
            lines.extend(["```", "cmd", "```", "result:", "```", "out", "```"])
    return "\n".join(lines) + "\n"


def old_measurement(total, sections):
    lines = ["## <repo>/<run>/project/.preclear/x/checkpoint.md", "total %d bytes (cap 4096), sha256 %s" % (total, SHA_X)]
    lines.extend("- %s: %d" % (name, size) for name, size in sections)
    return "\n".join(lines) + "\n"


def new_measurement(total, sections, caps):
    over = " over by %d" % (total - 4096) if total > 4096 else ""
    lines = ["## <run>/project/.preclear/x/checkpoint.md", "total %d/4096 bytes, sha256 %s%s" % (total, SHA_X, over)]
    for name, size in sections:
        cap = caps.get(name)
        if cap is None:
            lines.append("- %s: %d" % (name, size))
        else:
            lines.append("- %s: %d/%d%s" % (name, size, cap, " over by %d" % (size - cap) if size > cap else ""))
    return "\n".join(lines) + "\n"


CAPS = {
    "Identity and state": 800,
    "Boundaries and blockers": 600,
    "Next action": 500,
    "Resume reading": 600,
    "Evidence and working changes": 1000,
    "Do not redo": 596,
}


def sha_text(pairs):
    return "".join("%s  %s\n" % (digest, path) for path, digest in pairs)


class StructuralTests(unittest.TestCase):
    def test_file_sets_are_listed_in_the_right_direction_and_sorted(self):
        old = make_tree({"b-old.txt": "1", "both.txt": "same name, old bytes", "olddir/inner.txt": "1", "a-old.txt": "1"})
        new = make_tree({"z-new.txt": "1", "both.txt": "same name, new bytes!", "newdir/": b""})
        result = compare().compare_rows(old, new, ROW1)
        self.assertEqual(result["only_old"], ["a-old.txt", "b-old.txt", "olddir/", "olddir/inner.txt"], "old-only entries, sorted")
        self.assertEqual(result["only_new"], ["newdir/", "z-new.txt"], "new-only entries, sorted")
        self.assertNotIn("both.txt", result["only_old"] + result["only_new"], "a name on both sides is not a file-set difference")

    def test_an_empty_row_folder_on_either_side_gives_exit_0_and_empty_lists(self):
        empty = make_tree({})
        full = make_tree({"a.txt": "1"})
        for old, new, label in ((empty, full, "old empty"), (full, empty, "new empty"), (empty, empty, "both empty")):
            code, _out, err = run_compare("--old", old, "--new", new)
            self.assertEqual(code, pc_exitcodes.OK, "exit 0 with " + label)
            self.assertEqual(err, "", "no error text with " + label)
        _code, out, _err = run_compare("--old", empty, "--new", empty)
        self.assertEqual(listed_after(out, "files only on the old side: "), [], "empty old list")
        self.assertEqual(listed_after(out, "files only on the rerun side: "), [], "empty rerun list")

    def test_readme_headings_that_differ_are_listed_with_counts_and_equal_ones_are_not(self):
        old = make_tree({"README.md": "# Title A\ntext\n## Same\nmore\n### Old only\n"})
        new = make_tree({"README.md": "# Title B\n## Same\ntext\n## New one\n## Another\n"})
        result = compare().compare_rows(old, new, ROW1)
        headings = result["headings"]
        self.assertEqual((headings["old"]["count"], headings["new"]["count"]), (3, 4), "heading counts per side")
        self.assertEqual(headings["only_old"], ["# Title A", "### Old only"], "old-only headings")
        self.assertEqual(headings["only_new"], ["# Title B", "## New one", "## Another"], "new-only headings")
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "headings do not change the exit code")
        self.assertIn("  content: # Title A", out.splitlines(), "the heading text is shown as content")
        self.assertNotIn("content: ## Same", out, "an equal heading is not listed")

    def test_a_row_without_a_readme_is_reported_absent_and_the_run_continues(self):
        old = make_tree({})
        new = make_tree({"README.md": "# T\n"})
        result = compare().compare_rows(old, new, ROW1)
        self.assertEqual(result["headings"]["old"]["state"], "absent", "no README on the old side")
        self.assertEqual(result["headings"]["new"]["state"], "ok", "README on the new side")

    def test_helper_call_counts_on_the_committed_row(self):
        result = compare().compare_rows(PUBLICATION, shared_fake().destination, ROW1)
        self.assertEqual(
            result["helper"]["old"], {"state": "ok", "total": 1, "verbs": {"status": 1}, "exits": [0]}, "committed row 1 made one status call"
        )
        self.assertEqual(result["helper"]["new"]["state"], "ok", "the rerun log parses")

    def test_helper_calls_count_verbs_and_the_exit_code_multiset(self):
        log = "t CALL status\nt EXIT 0\nt CALL show --x\nt EXIT 3\nt CALL status\nt EXIT 0\n"
        old = make_tree({"wrapper-calls.log": log})
        new = make_tree({"wrapper-calls.log": ""})
        result = compare().compare_rows(old, new, ROW1)
        self.assertEqual(
            result["helper"]["old"], {"state": "ok", "total": 3, "verbs": {"show": 1, "status": 2}, "exits": [0, 0, 3]}, "verbs and exit multiset"
        )
        self.assertEqual(result["helper"]["new"], {"state": "ok", "total": 0, "verbs": {}, "exits": []}, "an empty log is zero calls")

    def test_a_log_that_does_not_parse_is_unreadable_for_that_side_and_the_run_continues(self):
        old = make_tree({"wrapper-calls.log": "this is not a log line\n"})
        new = make_tree({"wrapper-calls.log": "t CALL status\nt EXIT 0\n"})
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "an unreadable log keeps exit 0")
        result = compare().compare_rows(old, new, ROW1)
        self.assertEqual(result["helper"]["old"]["state"], "unreadable", "the bad log is reported unreadable")
        self.assertEqual(result["helper"]["new"]["total"], 1, "the other side is still counted")
        self.assertIn("helper calls", out, "the helper section is printed")

    def test_tool_call_counts_on_the_committed_s2_trace(self):
        path = os.path.join(PUBLICATION, ROW1, "s2-preclear-full-trace.md")
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        heads = [line for line in lines if line.startswith("### ")]
        side = compare().compare_rows(PUBLICATION, shared_fake().destination, ROW1)["tools"]["s2-preclear"]["old"]
        self.assertEqual(side["state"], "ok", "the committed trace parses")
        self.assertEqual(side["calls"], len(heads), "the count equals the independent heading count")
        self.assertEqual(side["calls"], 48, "the committed header says 48 calls")
        self.assertEqual(side["header_calls"], 48, "the Calls header value")
        self.assertEqual(side["header_flagged"], 7, "the header flag count")
        self.assertEqual(side["refusal"], sum(1 for line in heads if line.endswith("REFUSAL/DENIAL")), "refusal flags counted")
        self.assertEqual(side["error"], sum(1 for line in heads if "  ERROR" in line), "error flags counted")
        self.assertEqual(sum(side["by_tool"].values()), 48, "per tool counts sum to the calls")
        self.assertEqual(side["by_tool"]["Bash"], sum(1 for line in heads if ". Bash (" in line), "Bash count")

    def test_the_resume_trace_is_reported_on_the_rerun_side_only(self):
        tools = compare().compare_rows(PUBLICATION, shared_fake().destination, ROW1)["tools"]
        self.assertEqual(tools["s3-resume"]["old"]["state"], "absent", "no resume trace on the committed side")
        self.assertEqual(tools["s3-resume"]["new"]["state"], "ok", "a resume trace on the rerun side")
        self.assertEqual(tools["s1-work"]["old"]["state"], "absent", "no work-turn trace on the committed side")
        self.assertEqual(tools["s1-work"]["new"]["state"], "ok", "a work-turn trace on the rerun side")

    def test_flags_and_tool_names_are_counted_from_the_heading_shapes(self):
        text = trace_text(
            [("Read", []), ("Bash", ["ERROR"]), ("Bash", ["ERROR", "REFUSAL/DENIAL"]), ("Edit", []), ("Grep", ["ERROR"])],
            flagged=1,
            old_header=True,
        )
        old = make_tree({"s2-preclear-full-trace.md": text})
        new = make_tree({})
        side = compare().compare_rows(old, new, ROW1)["tools"]["s2-preclear"]["old"]
        self.assertEqual(side["by_tool"], {"Bash": 2, "Edit": 1, "Grep": 1, "Read": 1}, "per tool counts")
        self.assertEqual((side["calls"], side["header_calls"], side["header_flagged"]), (5, 5, 1), "calls and header")
        self.assertEqual((side["error"], side["refusal"]), (3, 1), "flag counts")

    def test_a_flag_word_inside_a_call_argument_is_not_a_flag(self):
        text = "Calls 1; results flagged as refusal/denial: 0.\n\n### 1. Read (toolu_0001): `<run>/ERROR` -> result 5 chars\n"
        old = make_tree({"s2-preclear-full-trace.md": text})
        side = compare().compare_rows(old, make_tree({}), ROW1)["tools"]["s2-preclear"]["old"]
        self.assertEqual((side["error"], side["refusal"]), (0, 0), "only the trailing flags count")

    def test_the_committed_token_is_equal_to_the_new_token_before_text_dependent_counts(self):
        compare_module = compare()
        self.assertEqual(compare_module.normalise("a <repo>/<run>/b <run>/c"), "a <run>/b <run>/c", "the committed token becomes the new one")
        old = make_tree({"tools.txt": "Read,Bash(<repo>/<run>/wrapper/checkpoint:*)\n"})
        new = make_tree({"tools.txt": "Read,Bash(<run>/wrapper/checkpoint:*)\n"})
        rules = compare_module.compare_rows(old, new, ROW1)["rules"]
        self.assertEqual((rules["only_old"], rules["only_new"]), ([], []), "the two spellings of the wrapper rule are equal")

    def test_tools_rules_difference_is_listed_with_both_counts(self):
        old = make_tree({"tools.txt": "Read,Bash(a:*),Bash(<run>/wrapper/checkpoint:*)\n"})
        new = make_tree({"tools.txt": "Read,Bash(b:*),Bash(<run>/wrapper/checkpoint status:*),Bash(<run>/wrapper/checkpoint show:*)\n"})
        rules = compare().compare_rows(old, new, ROW1)["rules"]
        self.assertEqual((rules["old"]["count"], rules["new"]["count"]), (3, 4), "both rule counts")
        self.assertEqual(rules["only_old"], ["Bash(<run>/wrapper/checkpoint:*)", "Bash(a:*)"], "rules only on the old side")
        self.assertEqual(
            rules["only_new"],
            ["Bash(<run>/wrapper/checkpoint show:*)", "Bash(<run>/wrapper/checkpoint status:*)", "Bash(b:*)"],
            "rules only on the rerun side",
        )

    def test_sha_paths_are_normalised_to_ckpt_and_compared_by_digest(self):
        old_sha = sha_text(
            [
                ("helper-state/ledger-roots.json", SHA_X),
                ("helper-state/bindings/b.json", SHA_X),
                ("ledgers/L1.md", SHA_X),
                ("ledgers/L2.md", SHA_X),
                ("project/CLAUDE.md", SHA_X),
                ("wrapper/calls.log", SHA_X),
            ]
        )
        new_sha = sha_text(
            [
                ("ckpt/ledger-roots.json", SHA_X),
                ("ckpt/bindings/b.json", SHA_X),
                ("ckpt/ledgers/L1.md", SHA_X),
                ("ckpt/ledgers/L2.md", SHA_Y),
                ("project/CLAUDE.md", SHA_Y),
                ("ckpt/.lock", SHA_X),
            ]
        )
        old = make_tree({"snap-0-setup/sha.txt": old_sha})
        new = make_tree({"snap-0-setup/sha.txt": new_sha})
        snap = compare().compare_rows(old, new, ROW1)["snapshots"]["snap-0-setup"]
        self.assertEqual(snap["differ"], ["ckpt/ledgers/L2.md", "project/CLAUDE.md"], "paths with a digest that differs")
        self.assertEqual(snap["only_old"], ["wrapper/calls.log"], "paths only on the old side")
        self.assertEqual(snap["only_new"], ["ckpt/.lock"], "paths only on the rerun side")
        self.assertEqual(snap["same"], 3, "paths with equal digests after normalising")

    def test_a_snapshot_folder_on_one_side_is_reported_by_side(self):
        old = make_tree({})
        new = make_tree({"snap-3-after-resume/sha.txt": sha_text([("a", SHA_X)])})
        snap = compare().compare_rows(old, new, ROW1)["snapshots"]["snap-3-after-resume"]
        self.assertEqual((snap["old_state"], snap["new_state"]), ("absent", "ok"), "the resume snapshot is on the rerun side only")

    def test_digests_version_and_usage_are_listed_as_content(self):
        old = make_tree({"digests.txt": "aaa  <repo>/<run>/x\n", "claude-version.txt": "2.1.304 (Claude Code)\n"})
        new = make_tree({"digests.txt": "bbb  <run>/x\n", "claude-version.txt": "2.1.310 (Claude Code)\n", "usage.txt": "u1\nu2\n"})
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "exit 0")
        lines = out.splitlines()
        self.assertIn("listed, not judged", lines, "the neutral section heading")
        for expected in ("  content: aaa  <run>/x", "  content: bbb  <run>/x", "  content: 2.1.304 (Claude Code)", "  content: 2.1.310 (Claude Code)", "  content: u1"):
            self.assertIn(expected, lines, "a listed content line")
        self.assertIn("usage.txt, old side: absent", lines, "usage.txt is absent on the old side")


class MeasurementTests(unittest.TestCase):
    def test_the_old_shape_parses(self):
        reports = compare().parse_measurements(old_measurement(3494, [("Identity and state", 734), ("Next action", 331)]))
        self.assertEqual(len(reports), 1, "one report")
        self.assertEqual(reports[0]["total"], 3494, "the total")
        self.assertEqual(reports[0]["sections"], [("Identity and state", 734, 800), ("Next action", 331, 500)], "sections with their caps by name")
        self.assertEqual(reports[0]["above"], [], "nothing above the cap")

    def test_the_new_shape_parses(self):
        reports = compare().parse_measurements(new_measurement(321, [("Identity and state", 54), ("Do not redo", 47)], CAPS))
        self.assertEqual(reports[0]["total"], 321, "the total")
        self.assertEqual(reports[0]["sections"], [("Identity and state", 54, 800), ("Do not redo", 47, 596)], "sections with caps")

    def test_a_total_of_4096_is_within_and_4097_is_above_by_one(self):
        within = compare().parse_measurements(old_measurement(4096, []))[0]
        above = compare().parse_measurements(old_measurement(4097, []))[0]
        self.assertEqual(within["above"], [], "4096 is within the cap")
        self.assertEqual(above["above"], [("total", 4097, 4096)], "4097 is above the cap")
        within_new = compare().parse_measurements(new_measurement(4096, [], CAPS))[0]
        above_new = compare().parse_measurements(new_measurement(4097, [], CAPS))[0]
        self.assertEqual(within_new["above"], [], "4096 is within the cap in the new shape")
        self.assertEqual(above_new["above"], [("total", 4097, 4096)], "4097 is above the cap in the new shape")

    def test_a_section_at_its_cap_is_within_and_one_byte_more_is_above(self):
        for name, cap in CAPS.items():
            at_cap = compare().parse_measurements(old_measurement(100, [(name, cap)]))[0]
            one_more = compare().parse_measurements(old_measurement(100, [(name, cap + 1)]))[0]
            self.assertEqual(at_cap["above"], [], "a section at its cap is within: " + name)
            self.assertEqual(one_more["above"], [(name, cap + 1, cap)], "one byte more is above: " + name)
            new_at = compare().parse_measurements(new_measurement(100, [(name, cap)], CAPS))[0]
            new_more = compare().parse_measurements(new_measurement(100, [(name, cap + 1)], CAPS))[0]
            self.assertEqual(new_at["above"], [], "new shape at the cap: " + name)
            self.assertEqual(new_more["above"], [(name, cap + 1, cap)], "new shape one more: " + name)

    def test_a_row_without_a_cap_is_never_above(self):
        report = compare().parse_measurements(old_measurement(100, [("(preamble)", 9000), ("(other)", 9000)]))[0]
        self.assertEqual(report["above"], [], "preamble and other rows have no cap")

    def test_the_caps_come_from_the_measurer_constants(self):
        import pc_measure

        self.assertEqual(dict(pc_measure.SECTIONS), CAPS, "the test caps equal the measurer caps")
        self.assertEqual(pc_measure.FILE_CAP, 4096, "the file cap")

    def test_the_report_lists_what_is_above_the_cap_for_each_side(self):
        old = make_tree({"measurements.txt": old_measurement(4097, [("Next action", 501)])})
        new = make_tree({"measurements.txt": new_measurement(4096, [("Next action", 500)], CAPS)})
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "exit 0")
        lines = out.splitlines()
        self.assertIn("old side above the cap: total 4097 (by 1), Next action 501 (by 1)", lines, "old side above the cap")
        self.assertIn("rerun side above the cap: none", lines, "rerun side within the cap")

    def test_a_side_without_a_measurement_file_is_absent_and_the_run_continues(self):
        old = make_tree({})
        new = make_tree({"measurements.txt": new_measurement(10, [], CAPS)})
        code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "exit 0")
        self.assertIn("measurements, old side: absent", out.splitlines(), "the old side is absent")

    def test_an_unmeasured_file_is_reported_without_a_number(self):
        old = make_tree({"measurements.txt": "UNCONFIRMED: no plain-file checkpoint was found\n"})
        result = compare().compare_rows(old, make_tree({}), ROW1)
        self.assertEqual(result["measurements"]["old"]["state"], "none", "no report in the file")

    def test_the_committed_row_measures_3494_within_the_cap(self):
        result = compare().compare_rows(PUBLICATION, shared_fake().destination, ROW1)
        report = result["measurements"]["old"]["reports"][0]
        self.assertEqual(report["total"], 3494, "committed total")
        self.assertEqual(report["above"], [], "committed row is within the cap")
        self.assertEqual(result["measurements"]["new"]["reports"][0]["total"], 321, "the fake checkpoint measures 321 bytes")


def mode_has_write(mode):
    return any(flag in mode for flag in "wax+")


class ReadOnlyTests(unittest.TestCase):
    def test_write_protected_copies_compare_successfully(self):
        old = tempfile.mkdtemp(prefix="pc-cmp-ro-old-")
        new = tempfile.mkdtemp(prefix="pc-cmp-ro-new-")
        shutil.copytree(os.path.join(PUBLICATION, ROW1), os.path.join(old, ROW1))
        shutil.copytree(os.path.join(shared_fake().destination, ROW1), os.path.join(new, ROW1))
        protected = []
        for root in (old, new):
            for dirpath, _dirnames, filenames in os.walk(root):
                for name in filenames:
                    full = os.path.join(dirpath, name)
                    os.chmod(full, stat.S_IMODE(os.stat(full).st_mode) & ~0o222)
                    protected.append(full)
            for dirpath, _dirnames, _filenames in os.walk(root, topdown=False):
                os.chmod(dirpath, stat.S_IMODE(os.stat(dirpath).st_mode) & ~0o222)
                protected.append(dirpath)
        try:
            code, out, err = run_compare("--old", old, "--new", new)
        finally:
            for path in protected:
                os.chmod(path, stat.S_IMODE(os.stat(path).st_mode) | 0o200)
        self.assertEqual(code, pc_exitcodes.OK, "write-protected copies compare with exit 0")
        self.assertEqual(err, "", "no error text")
        self.assertIn("old unchanged: yes", out.splitlines(), "the old copy is unchanged")
        self.assertIn("new unchanged: yes", out.splitlines(), "the new copy is unchanged")

    def test_every_write_primitive_patched_to_raise_leaves_the_comparison_working(self):
        real_open = builtins.open
        calls = []

        def guarded_open(*args, **kwargs):
            mode = kwargs.get("mode", args[1] if len(args) > 1 else "r")
            if isinstance(mode, str) and mode_has_write(mode):
                calls.append("open")
                raise AssertionError("a write-mode open was attempted")
            return real_open(*args, **kwargs)

        def refuse(*_args, **_kwargs):
            calls.append("primitive")
            raise AssertionError("a write primitive was called")

        names = ["replace", "rename", "remove", "unlink", "rmdir", "mkdir", "makedirs", "utime", "chmod"]
        shutil_names = ["copy", "copy2", "copyfile", "copytree", "move", "rmtree"]
        old = make_tree({"README.md": "# a\n", "wrapper-calls.log": "t CALL status\nt EXIT 0\n"})
        new = make_tree({"README.md": "# b\n", "s2-preclear-full-trace.md": trace_text([("Bash", [])])})
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(builtins, "open", guarded_open))
            for name in names:
                stack.enter_context(mock.patch.object(os, name, refuse))
            for name in shutil_names:
                stack.enter_context(mock.patch.object(shutil, name, refuse))
            code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "the comparison succeeds with every write primitive patched")
        self.assertEqual(calls, [], "no write primitive was reached")
        self.assertIn("old unchanged: yes", out.splitlines(), "unchanged under the patches")

    def test_the_real_publication_folder_has_equal_digests_before_and_after(self):
        code, out, _err = run_compare("--old", PUBLICATION, "--new", shared_fake().destination)
        self.assertEqual(code, pc_exitcodes.OK, "exit 0")
        self.assertEqual(digest_line(out, "tree digest before: ")[0], digest_line(out, "tree digest after: ")[0], "equal old digests")

    def test_a_tree_that_changes_during_the_run_is_reported_unchanged_no_with_exit_0(self):
        old = make_tree({"a.txt": "1"})
        new = make_tree({"b.txt": "1"})
        module = compare()
        real = module.compare_rows

        def changing(old_tree, new_tree, row):
            with open(os.path.join(new_tree, row, "b.txt"), "ab") as handle:
                handle.write(b"more")
            return real(old_tree, new_tree, row)

        with mock.patch.object(module, "compare_rows", changing):
            code, out, _err = run_compare("--old", old, "--new", new)
        self.assertEqual(code, pc_exitcodes.OK, "a changed tree still exits 0")
        lines = out.splitlines()
        self.assertIn("new unchanged: no", lines, "the changed side is reported")
        self.assertIn("old unchanged: yes", lines, "the other side is reported unchanged")
        self.assertNotEqual(digest_line(out, "tree digest before: ")[1], digest_line(out, "tree digest after: ")[1], "the new digests differ")


class DigestSensitivityTests(unittest.TestCase):
    def test_the_digest_changes_for_a_byte_a_name_an_empty_folder_and_a_symlink_target(self):
        digest = compare().tree_digest
        base = make_tree({"a.txt": "hello", "dir/b.txt": "x"})
        first = digest(base)
        with open(os.path.join(base, ROW1, "a.txt"), "wb") as handle:
            handle.write(b"hellp")
        second = digest(base)
        self.assertNotEqual(first, second, "one changed byte changes the digest")
        os.rename(os.path.join(base, ROW1, "a.txt"), os.path.join(base, ROW1, "a2.txt"))
        third = digest(base)
        self.assertNotEqual(second, third, "a renamed file changes the digest")
        os.mkdir(os.path.join(base, ROW1, "empty-folder"))
        fourth = digest(base)
        self.assertNotEqual(third, fourth, "an added empty folder changes the digest")
        os.symlink("target-one", os.path.join(base, ROW1, "link"))
        fifth = digest(base)
        self.assertNotEqual(fourth, fifth, "an added symlink changes the digest")
        os.unlink(os.path.join(base, ROW1, "link"))
        os.symlink("target-two", os.path.join(base, ROW1, "link"))
        self.assertNotEqual(fifth, digest(base), "a changed symlink target changes the digest")

    def test_equal_contents_and_names_give_equal_digests_whatever_the_root_and_times(self):
        one = make_tree({"a.txt": "same", "d/b.txt": "same too"})
        two = make_tree({"d/b.txt": "same too", "a.txt": "same"})
        os.utime(os.path.join(two, ROW1, "a.txt"), (1, 1))
        os.chmod(os.path.join(two, ROW1, "d", "b.txt"), 0o600)
        self.assertEqual(compare().tree_digest(one), compare().tree_digest(two), "modes, times and the root name are not part of the digest")

    def test_the_report_says_modes_and_timestamps_are_not_part_of_the_digest(self):
        _code, out, _err = run_compare("--old", make_tree({}), "--new", make_tree({}))
        self.assertIn("file modes and timestamps are not part of the digest", out.splitlines(), "the sentence is printed")


class BadInputTests(unittest.TestCase):
    def assert_fixed_refusal(self, args, label, scratch):
        code, out, err = run_compare(*args)
        self.assertEqual(code, pc_exitcodes.USAGE, "exit 2 for " + label)
        self.assertEqual(out, "", "nothing on stdout for " + label)
        for value in scratch:
            self.assertNotIn(value, err, "no path in the output for " + label)
        for value in args:
            if value.startswith("--") or value == "":
                continue
            self.assertNotIn(value, err, "no argument value echoed for " + label)
        return err

    def test_bad_inputs_exit_2_with_fixed_text_and_no_path(self):
        good = make_tree({"a.txt": "1"})
        no_row = tempfile.mkdtemp(prefix="pc-cmp-norow-")
        a_file = os.path.join(good, "a-plain-file")
        with open(a_file, "w") as handle:
            handle.write("x")
        link = os.path.join(tempfile.mkdtemp(prefix="pc-cmp-link-"), "link")
        os.symlink(good, link)
        row_link_tree = tempfile.mkdtemp(prefix="pc-cmp-rowlink-")
        os.symlink(os.path.join(good, ROW1), os.path.join(row_link_tree, ROW1))
        missing = os.path.join(good, "missing-folder")
        scratch = [good, no_row, link, row_link_tree]
        cases = (
            (("--old", missing, "--new", good), "a missing old folder"),
            (("--old", good, "--new", missing), "a missing new folder"),
            (("--old", good, "--new", a_file), "a new path that is a file"),
            (("--old", link, "--new", good), "a root that is a symlink"),
            (("--old", good, "--new", no_row), "a missing row folder on the new side"),
            (("--old", no_row, "--new", good), "a missing row folder on the old side"),
            (("--old", good, "--new", row_link_tree), "a row folder that is a symlink"),
            (("--old", good, "--new", good, "--row", "nonexistent-row"), "an unknown row id"),
            (("--old", good, "--new", good, "--row", "../escape"), "a row id with a separator"),
            (("--old", good, "--new", good, "--row", ""), "an empty row id"),
            (("--old", good, "--new", good, "--bogus", "x"), "an unknown option"),
            (("--old", good), "a missing option"),
            ((), "no arguments"),
        )
        for args, label in cases:
            self.assert_fixed_refusal(args, label, scratch)

    def test_the_refusal_text_is_the_same_for_two_different_bad_values(self):
        good = make_tree({"a.txt": "1"})
        first = self.assert_fixed_refusal(("--old", os.path.join(good, "m1"), "--new", good), "first", [good])
        second = self.assert_fixed_refusal(("--old", os.path.join(good, "m2"), "--new", good), "second", [good])
        self.assertEqual(first, second, "the same fixed text whatever the value")

    def test_every_readable_pair_exits_0(self):
        trees = [make_tree({}), make_tree({"a": "1"}), make_tree({"README.md": "# t\n", "wrapper-calls.log": ""})]
        for old in trees:
            for new in trees:
                code, _out, _err = run_compare("--old", old, "--new", new)
                self.assertEqual(code, pc_exitcodes.OK, "a readable pair exits 0")

    def test_malformed_files_never_raise_past_main(self):
        junk = b"\xff\xfe\x00 binary junk \x80\n### x\n"
        files = {
            "README.md": junk,
            "wrapper-calls.log": junk,
            "s2-preclear-full-trace.md": junk,
            "measurements.txt": junk,
            "tools.txt": junk,
            "digests.txt": junk,
            "claude-version.txt": junk,
            "usage.txt": junk,
            "snap-0-setup/sha.txt": junk,
        }
        code, _out, err = run_compare("--old", make_tree(files), "--new", make_tree(files))
        self.assertEqual(code, pc_exitcodes.OK, "malformed files are reported and the run continues")
        self.assertEqual(err, "", "no error text")

    def test_the_command_line_entry_point_exits_2_for_a_bad_call_and_0_for_a_good_one(self):
        script = os.path.join(HARNESS_DIR, "pc_compare.py")
        bad = subprocess.run([sys.executable, "-E", "-s", "-B", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(bad.returncode, pc_exitcodes.USAGE, "no arguments exit 2")
        good = make_tree({"a.txt": "1"})
        ran = subprocess.run(
            [sys.executable, "-E", "-s", "-B", script, "--old", good, "--new", good], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(ran.returncode, pc_exitcodes.OK, "a readable pair exits 0")
        self.assertEqual(ran.stderr, b"", "nothing on stderr")


def verdict_words():
    fragments = (("pa", "ss"), ("pa", "ssed"), ("fa", "il"), ("fa", "iled"), ("fa", "ilure"), ("acc", "ept"), ("acc", "epted"), ("ver", "dict"))
    return ["".join(pair) for pair in fragments]


def own_words(text):
    """The comparer's own words: every line with quoted content removed."""
    kept = []
    for line in text.splitlines():
        if "content: " in line:
            line = line[: line.index("content: ")]
        kept.append(line)
    return "\n".join(kept)


def has_verdict_word(text):
    return any(re.search(r"\b%s\b" % re.escape(word), text, re.I) for word in verdict_words())


class VocabularyTests(unittest.TestCase):
    def test_the_comparers_words_hold_no_verdict_word_for_the_committed_row_against_the_fake_pipeline(self):
        code, out, _err = run_compare("--old", PUBLICATION, "--new", shared_fake().destination)
        self.assertEqual(code, pc_exitcodes.OK, "exit 0")
        self.assertFalse(has_verdict_word(own_words(out)), "no verdict word in the comparer's own words")

    def test_quoted_heading_text_is_content_and_is_outside_the_check(self):
        old = make_tree({"README.md": "# Result: " + verdict_words()[0].upper() + "\n"})
        new = make_tree({"README.md": "# Other\n"})
        _code, out, _err = run_compare("--old", old, "--new", new)
        self.assertIn(verdict_words()[0].upper(), out, "the quoted heading is printed as written")
        self.assertFalse(has_verdict_word(own_words(out)), "the quoted word is outside the check")

    def test_the_check_can_see_a_verdict_word_in_a_plain_line(self):
        self.assertTrue(has_verdict_word(own_words("row 1 " + verdict_words()[2])), "the check sees a verdict word in a plain line")
        self.assertFalse(has_verdict_word(own_words("  content: row 1 " + verdict_words()[2])), "the check skips quoted content")


if __name__ == "__main__":
    unittest.main()
