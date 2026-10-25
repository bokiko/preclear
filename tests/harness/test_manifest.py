"""Tests for pc_manifest: byte-walk tree manifests, sha.txt and JSON-lines writers.

Awkward and non-Latin file names are built from code points and bytes at run time, so
this file stays ASCII. Scratch directories come from tempfile.mkdtemp, are never
deleted and are never printed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_CLI = os.path.join(HARNESS_DIR, "pc_manifest.py")

import pc_manifest  # noqa: E402  (the harness folder is on sys.path via discovery)

# Names as raw bytes, built from code points.
NAME_NEWLINE = b"line-one" + b"\n" + b"line-two.txt"
NAME_CR = b"cr" + b"\r" + b"name.txt"
NAME_BACKSLASH_N = b"back" + b"\\" + b"n-slash.txt"
NAME_CJK = (chr(0x6587) + chr(0x4EF6) + ".txt").encode("utf-8")
NAME_EMOJI = (chr(0x1F600) + ".txt").encode("utf-8")
NAME_HEBREW = (chr(0x5E9) + chr(0x5DC) + chr(0x5D5) + chr(0x5DD) + ".txt").encode("utf-8")
NAME_PLAIN = b"ordinary.txt"

SHA_LINE = re.compile(rb"^\\?[0-9a-f]{64}  [^\n]+$")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_tree():
    """Build a fresh tree holding awkward names. Returns (root, {relpath bytes: content})."""
    root = tempfile.mkdtemp(prefix="preclear-mf-")
    base = os.fsencode(root)
    files = {
        NAME_PLAIN: b"plain content\n",
        b"sub/nested.txt": b"nested\n",
        NAME_NEWLINE: b"newline name\n",
        NAME_CR: b"carriage return name\n",
        NAME_BACKSLASH_N: b"backslash n name\n",
        NAME_CJK: b"cjk\n",
        NAME_EMOJI: b"emoji\n",
        NAME_HEBREW: b"right to left\n",
    }
    os.mkdir(os.path.join(base, b"sub"))
    for rel, content in files.items():
        with open(os.path.join(base, rel), "xb") as handle:
            handle.write(content)
    return root, files


class HarnessTestCase(unittest.TestCase):
    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)


class EscapeNameTests(HarnessTestCase):
    def test_plain_name_is_unchanged_and_reports_no_escape(self):
        self.ok(pc_manifest.escape_name(NAME_PLAIN) == ("ordinary.txt", False), "plain name")

    def test_non_latin_names_are_decoded_without_escape(self):
        text, escaped = pc_manifest.escape_name(NAME_CJK)
        self.ok(text == chr(0x6587) + chr(0x4EF6) + ".txt" and not escaped, "cjk name stays as written")

    def test_newline_carriage_return_and_backslash_are_escaped(self):
        self.ok(pc_manifest.escape_name(b"a\nb") == ("a" + "\\" + "nb", True), "newline becomes backslash n")
        self.ok(pc_manifest.escape_name(b"a\rb") == ("a" + "\\" + "rb", True), "carriage return becomes backslash r")
        self.ok(pc_manifest.escape_name(b"a\\b") == ("a" + "\\\\" + "b", True), "backslash is doubled")

    def test_a_real_newline_and_a_literal_backslash_n_never_collide(self):
        real = pc_manifest.escape_name(b"x" + b"\n" + b"y")
        literal = pc_manifest.escape_name(b"x" + b"\\" + b"ny")
        self.ok(real[0] != literal[0], "escaped forms differ")


class TreeManifestTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.files = make_tree()
        cls.entries = pc_manifest.tree_manifest(cls.root)

    def regular(self):
        return [e for e in self.entries if e["kind"] == "f"]

    def test_every_regular_file_is_listed_once_with_size_and_digest(self):
        got = {e["path"]: (e["size"], e["sha256"]) for e in self.regular()}
        want = {rel: (len(content), sha(content)) for rel, content in self.files.items()}
        self.ok(got == want, "regular files, sizes and digests match what was written")
        self.ok(len(self.regular()) == len(self.files), "one entry per regular file")

    def test_the_directory_is_listed_with_kind_d(self):
        kinds = {e["path"]: e["kind"] for e in self.entries}
        self.ok(kinds.get(b"sub") == "d", "directory entry")

    def test_missing_root_and_non_directory_root_raise(self):
        missing = os.path.join(self.root, "no-such-root")
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(missing)
        a_file = os.path.join(self.root, os.fsdecode(NAME_PLAIN))
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(a_file)


class ShaTxtTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.files = make_tree()
        cls.entries = pc_manifest.tree_manifest(cls.root)
        cls.text = pc_manifest.sha_txt_bytes(cls.entries)

    def test_one_line_per_regular_file_and_no_name_is_split(self):
        lines = self.text.split(b"\n")
        self.ok(lines[-1] == b"", "the text ends with a newline")
        lines = lines[:-1]
        self.ok(len(lines) == len(self.files), "line count equals regular file count")
        self.ok(all(SHA_LINE.match(line) for line in lines), "every line is digest, two spaces, name")

    def test_ordinary_names_keep_the_committed_shape(self):
        want = (sha(self.files[NAME_PLAIN]) + "  ordinary.txt").encode("ascii")
        self.ok(want in self.text.split(b"\n"), "ordinary name line is unescaped and unprefixed")
        nested = (sha(self.files[b"sub/nested.txt"]) + "  sub/nested.txt").encode("ascii")
        self.ok(nested in self.text.split(b"\n"), "nested name uses forward slashes")
        cjk = sha(self.files[NAME_CJK]).encode("ascii") + b"  " + NAME_CJK
        self.ok(cjk in self.text.split(b"\n"), "non-Latin names are written as UTF-8 without a prefix")

    def test_names_needing_escapes_get_a_leading_backslash_and_backslash_escapes(self):
        lines = self.text.split(b"\n")
        newline_line = b"\\" + sha(self.files[NAME_NEWLINE]).encode("ascii") + b"  line-one" + b"\\n" + b"line-two.txt"
        cr_line = b"\\" + sha(self.files[NAME_CR]).encode("ascii") + b"  cr" + b"\\r" + b"name.txt"
        backslash_line = b"\\" + sha(self.files[NAME_BACKSLASH_N]).encode("ascii") + b"  back" + b"\\\\" + b"n-slash.txt"
        self.ok(newline_line in lines, "newline name is escaped with a leading backslash")
        self.ok(cr_line in lines, "carriage return name is escaped with a leading backslash")
        self.ok(backslash_line in lines, "literal backslash n name is escaped with a leading backslash")

    def test_empty_entry_list_gives_zero_bytes(self):
        self.ok(pc_manifest.sha_txt_bytes([]) == b"", "empty list gives zero bytes")


class JsonlTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.files = make_tree()
        cls.entries = pc_manifest.tree_manifest(cls.root)
        cls.data = pc_manifest.jsonl_bytes(cls.entries)

    def test_every_name_round_trips_to_identical_bytes(self):
        lines = self.data.split(b"\n")[:-1]
        self.ok(len(lines) == len(self.entries), "one JSON object per entry")
        recovered = [os.fsencode(json.loads(line.decode("ascii"))["path"]) for line in lines]
        self.ok(recovered == [e["path"] for e in self.entries], "paths round-trip byte for byte, in order")
        self.ok(NAME_NEWLINE in recovered and NAME_BACKSLASH_N in recovered, "awkward names are present")

    def test_json_lines_are_ascii_and_carry_kind_size_and_digest(self):
        self.data.decode("ascii")
        by_path = {os.fsencode(json.loads(l)["path"]): json.loads(l) for l in self.data.split(b"\n")[:-1]}
        record = by_path[NAME_PLAIN]
        self.ok(record["kind"] == "f" and record["size"] == len(self.files[NAME_PLAIN]), "kind and size")
        self.ok(record["sha256"] == sha(self.files[NAME_PLAIN]), "digest")
        self.ok(by_path[b"sub"]["kind"] == "d" and by_path[b"sub"]["sha256"] is None, "directory has no digest")


class WriteSnapshotTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.files = make_tree()
        cls.entries = pc_manifest.tree_manifest(cls.root)
        cls.out_parent = tempfile.mkdtemp(prefix="preclear-snap-")

    def test_write_snapshot_creates_the_stage_folder_with_both_files(self):
        stage = os.path.join(self.out_parent, "snap-0-setup")
        pc_manifest.write_snapshot(stage, self.entries)
        self.ok(os.path.isdir(stage), "stage folder created")
        with open(os.path.join(stage, "sha.txt"), "rb") as handle:
            self.ok(handle.read() == pc_manifest.sha_txt_bytes(self.entries), "sha.txt content")
        with open(os.path.join(stage, "manifest.jsonl"), "rb") as handle:
            self.ok(handle.read() == pc_manifest.jsonl_bytes(self.entries), "manifest.jsonl content")

    def test_write_snapshot_refuses_an_existing_stage_folder_and_keeps_its_files(self):
        stage = os.path.join(self.out_parent, "snap-1-after-work")
        pc_manifest.write_snapshot(stage, self.entries)
        with open(os.path.join(stage, "sha.txt"), "rb") as handle:
            before = handle.read()
        with self.assertRaises(FileExistsError):
            pc_manifest.write_snapshot(stage, [])
        with open(os.path.join(stage, "sha.txt"), "rb") as handle:
            self.ok(handle.read() == before, "existing snapshot content is untouched")


class CliTests(HarnessTestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-E", "-s", "-B", MANIFEST_CLI] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_cli_prints_the_text_form_and_the_jsonl_form(self):
        root, _files = make_tree()
        entries = pc_manifest.tree_manifest(root)
        text = self.run_cli(root)
        self.ok(text.returncode == 0, "text form exits 0")
        self.ok(text.stdout == pc_manifest.sha_txt_bytes(entries), "text form equals sha_txt_bytes")
        jsonl = self.run_cli(root, "--jsonl")
        self.ok(jsonl.returncode == 0, "jsonl form exits 0")
        self.ok(jsonl.stdout == pc_manifest.jsonl_bytes(entries), "jsonl form equals jsonl_bytes")

    def test_cli_exits_2_on_a_bad_root_or_bad_usage(self):
        root, _files = make_tree()
        self.ok(self.run_cli(os.path.join(root, "nope")).returncode == 2, "missing root exits 2")
        self.ok(self.run_cli().returncode == 2, "no arguments exits 2")


if __name__ == "__main__":
    unittest.main()
