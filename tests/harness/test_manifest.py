"""Tests for pc_manifest: byte-walk tree manifests, sha.txt and JSON-lines writers.

Awkward and non-Latin file names are built from code points and bytes at run time, so
this file stays ASCII. Scratch directories come from tempfile.mkdtemp, are never
deleted and are never printed.
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
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


def empty_dir():
    return tempfile.mkdtemp(prefix="preclear-mf-")


def entry_for(path_bytes, content=b""):
    """An in-memory regular-file entry, for cases a filesystem may refuse to hold."""
    return {"path": path_bytes, "kind": "f", "size": len(content), "sha256": sha(content), "target": None}


def create_exclusive(directory, name_bytes, content=b"x\n"):
    """Create one file by raw byte name; raises OSError if the filesystem refuses the name."""
    full = os.path.join(os.fsencode(directory), name_bytes)
    fd = os.open(full, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, content)
    finally:
        os.close(fd)


class RefuseUnderTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="preclear-mf-")
        cls.config_dir = os.path.join(cls.base, "config-dir")
        os.mkdir(cls.config_dir)
        os.mkdir(os.path.join(cls.config_dir, "inner"))
        cls.sibling = os.path.join(cls.base, "config-dir-sibling")
        os.mkdir(cls.sibling)
        with open(os.path.join(cls.sibling, "a.txt"), "xb") as handle:
            handle.write(b"a")

    def test_a_root_equal_to_a_listed_path_is_refused(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(self.config_dir, refuse_under=(self.config_dir,))

    def test_a_root_under_a_listed_path_is_refused(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(os.path.join(self.config_dir, "inner"), refuse_under=(self.config_dir,))

    def test_a_root_reached_through_a_symlink_into_a_listed_path_is_refused(self):
        link = os.path.join(self.base, "link-into-config")
        os.symlink(self.config_dir, link)
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(link, refuse_under=(self.config_dir,))

    def test_a_listed_path_given_with_a_trailing_separator_still_matches(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(self.config_dir, refuse_under=(self.config_dir + os.sep,))

    def test_a_sibling_that_only_shares_a_name_prefix_is_accepted(self):
        entries = pc_manifest.tree_manifest(self.sibling, refuse_under=(self.config_dir,))
        self.ok([e["path"] for e in entries] == [b"a.txt"], "the sibling is walked")

    def test_a_root_under_a_listed_ancestor_folder_is_refused(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(os.path.join(self.config_dir, "inner"), refuse_under=(self.base,))

    def test_an_empty_listed_path_is_refused_as_unusable_rather_than_matching_the_working_folder(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(self.sibling, refuse_under=("",))

    def test_no_refuse_under_means_nothing_is_refused(self):
        self.ok(len(pc_manifest.tree_manifest(self.config_dir)) == 1, "the inner folder is listed")
        self.ok(len(pc_manifest.tree_manifest(self.config_dir, refuse_under=())) == 1, "an empty tuple refuses nothing")


class OrderingAndDeterminismTests(HarnessTestCase):
    def test_entries_are_sorted_by_raw_path_bytes_never_by_locale(self):
        root = empty_dir()
        e_acute = chr(0xE9).encode("utf-8")        # two bytes: c3 a9
        cjk = chr(0x6587).encode("utf-8")           # three bytes: e6 96 87
        for name in (cjk, e_acute, b"a", b"B"):    # created out of order on purpose
            create_exclusive(root, name)
        paths = [e["path"] for e in pc_manifest.tree_manifest(root)]
        self.ok(paths[0] == b"B" and paths[1] == b"a", "B (0x42) sorts before a (0x61)")
        self.ok(paths[3] == cjk, "the three-byte character sorts last")
        self.ok(paths[2] in (e_acute, b"e" + chr(0x301).encode("utf-8")), "the two-byte letter sorts third")
        self.ok(paths == sorted(paths), "entries equal their own raw byte sort")

    def test_a_nested_path_sorts_by_its_whole_byte_string(self):
        root = empty_dir()
        os.mkdir(os.path.join(root, "a"))
        create_exclusive(os.path.join(root, "a"), b"z")
        create_exclusive(root, b"a.txt")      # "a.txt" < "a/z" because "." (0x2e) < "/" (0x2f)
        paths = [e["path"] for e in pc_manifest.tree_manifest(root)]
        self.ok(paths == [b"a", b"a.txt", b"a/z"], "sorted by full relative path bytes")

    def test_two_manifests_of_one_unchanged_tree_are_byte_identical(self):
        root, _files = make_tree()
        first = pc_manifest.tree_manifest(root)
        second = pc_manifest.tree_manifest(root)
        self.ok(first == second, "entries equal")
        self.ok(pc_manifest.sha_txt_bytes(first) == pc_manifest.sha_txt_bytes(second), "sha.txt bytes equal")
        self.ok(pc_manifest.jsonl_bytes(first) == pc_manifest.jsonl_bytes(second), "manifest.jsonl bytes equal")


class LoneSurrogateTests(HarnessTestCase):
    NAME = b"bad-" + bytes([0xFF]) + b"-name.txt"

    def test_an_in_memory_non_utf8_name_round_trips_through_jsonl_to_identical_bytes(self):
        entry = entry_for(self.NAME, b"payload")
        data = pc_manifest.jsonl_bytes([entry])
        data.decode("ascii")
        record = json.loads(data.decode("ascii"))
        self.ok(os.fsencode(record["path"]) == self.NAME, "the name round-trips byte for byte")

    def test_an_in_memory_non_utf8_name_is_written_to_sha_txt_as_its_raw_bytes(self):
        text = pc_manifest.sha_txt_bytes([entry_for(self.NAME, b"payload")])
        self.ok(text == sha(b"payload").encode("ascii") + b"  " + self.NAME + b"\n", "raw bytes carried through")

    def test_a_real_file_with_a_non_utf8_name_is_listed_or_the_filesystem_refuses_it(self):
        root = empty_dir()
        try:
            create_exclusive(root, self.NAME)
        except OSError as exc:
            self.skipTest("this filesystem refuses non-UTF-8 file names (errno %s); the in-memory cases above still prove the byte round trip" % errno.errorcode.get(exc.errno, "unknown"))
        paths = [e["path"] for e in pc_manifest.tree_manifest(root)]
        self.ok(paths == [self.NAME], "the raw-byte name is listed unchanged")


class AdjacencyTests(HarnessTestCase):
    def test_a_real_newline_and_a_literal_backslash_n_stay_distinct_lines(self):
        root = empty_dir()
        create_exclusive(root, b"x" + b"\n" + b"y", b"newline\n")
        create_exclusive(root, b"x" + b"\\" + b"ny", b"backslash\n")
        text = pc_manifest.sha_txt_bytes(pc_manifest.tree_manifest(root))
        lines = text.split(b"\n")[:-1]
        self.ok(len(lines) == 2 and len(set(lines)) == 2, "two distinct lines, one per file")
        self.ok(all(line.startswith(b"\\") for line in lines), "both are written with the escape prefix")
        names = sorted(line.split(b"  ", 1)[1] for line in lines)
        self.ok(names == sorted([b"x" + b"\\n" + b"y", b"x" + b"\\\\" + b"ny"]), "escaped names differ")

    def test_in_memory_case_nfc_and_nfd_names_are_all_distinct_and_byte_sorted(self):
        nfc = chr(0xE9).encode("utf-8") + b".txt"
        nfd = b"e" + chr(0x301).encode("utf-8") + b".txt"
        entries = sorted(
            [entry_for(n, n) for n in (b"case.txt", b"Case.txt", nfc, nfd)],
            key=lambda e: e["path"],
        )
        text = pc_manifest.sha_txt_bytes(entries)
        lines = text.split(b"\n")[:-1]
        self.ok(len(set(lines)) == 4, "four distinct lines")
        self.ok([line.split(b"  ", 1)[1] for line in lines] == [b"Case.txt", b"case.txt", nfd, nfc], "sorted by raw bytes")

    def test_names_differing_only_by_case_are_distinct_where_the_filesystem_allows_both(self):
        root = empty_dir()
        create_exclusive(root, b"Case.txt")
        try:
            create_exclusive(root, b"case.txt")
        except FileExistsError:
            self.skipTest("this filesystem is case-insensitive, so two names differing only by case cannot both exist; the in-memory case above covers the logic")
        paths = [e["path"] for e in pc_manifest.tree_manifest(root)]
        self.ok(paths == [b"Case.txt", b"case.txt"], "both case variants are listed")

    def test_nfc_and_nfd_forms_are_distinct_where_the_filesystem_allows_both(self):
        root = empty_dir()
        nfc = chr(0xE9).encode("utf-8") + b".txt"
        nfd = b"e" + chr(0x301).encode("utf-8") + b".txt"
        create_exclusive(root, nfc)
        try:
            create_exclusive(root, nfd)
        except FileExistsError:
            self.skipTest("this filesystem treats NFC and NFD spellings as one name, so both cannot exist; the in-memory case above covers the logic")
        paths = sorted(e["path"] for e in pc_manifest.tree_manifest(root))
        self.ok(paths == sorted([nfc, nfd]), "both normalisation forms are listed")


class EmptyAndZeroByteTests(HarnessTestCase):
    def test_an_empty_tree_gives_zero_byte_files(self):
        root = empty_dir()
        entries = pc_manifest.tree_manifest(root)
        self.ok(entries == [], "no entries")
        self.ok(pc_manifest.sha_txt_bytes(entries) == b"" and pc_manifest.jsonl_bytes(entries) == b"", "zero bytes each")
        out = tempfile.mkdtemp(prefix="preclear-snap-")
        stage = os.path.join(out, "snap-empty")
        pc_manifest.write_snapshot(stage, entries)
        self.ok(os.path.getsize(os.path.join(stage, "sha.txt")) == 0, "sha.txt is zero bytes")
        self.ok(os.path.getsize(os.path.join(stage, "manifest.jsonl")) == 0, "manifest.jsonl is zero bytes")

    def test_a_zero_byte_file_hashes_to_the_sha256_of_nothing(self):
        root = empty_dir()
        create_exclusive(root, b"empty.bin", b"")
        entries = pc_manifest.tree_manifest(root)
        self.ok(len(entries) == 1 and entries[0]["size"] == 0, "one zero-size entry")
        self.ok(entries[0]["sha256"].startswith("e3b0c44298fc1c14"), "the SHA-256 of nothing")
        self.ok(entries[0]["sha256"] == hashlib.sha256(b"").hexdigest(), "the full digest of nothing")

    def test_a_missing_root_is_an_error_never_an_empty_manifest(self):
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.tree_manifest(os.path.join(empty_dir(), "no-such-root"))


class OtherKindsTests(HarnessTestCase):
    def test_a_symlink_is_listed_with_its_target_and_is_never_followed(self):
        root = empty_dir()
        os.mkdir(os.path.join(root, "real-dir"))
        create_exclusive(os.path.join(root, "real-dir"), b"inside.txt")
        os.symlink("real-dir", os.path.join(root, "link-to-dir"))
        entries = {e["path"]: e for e in pc_manifest.tree_manifest(root)}
        self.ok(entries[b"link-to-dir"]["kind"] == "l" and entries[b"link-to-dir"]["target"] == b"real-dir", "link entry")
        self.ok(b"link-to-dir/inside.txt" not in entries, "the link was not followed")
        self.ok(b"real-dir/inside.txt" in entries, "the real folder was walked")
        text = pc_manifest.sha_txt_bytes(list(entries.values()))
        self.ok(b"link-to-dir" not in text, "a symlink gets no sha.txt line")

    def test_a_special_file_is_kind_o_and_is_not_hashed(self):
        root = empty_dir()
        os.mkfifo(os.path.join(root, "pipe"))
        entries = pc_manifest.tree_manifest(root)
        self.ok(entries[0]["kind"] == "o" and entries[0]["sha256"] is None, "special file listed, not read")
        self.ok(pc_manifest.sha_txt_bytes(entries) == b"", "no sha.txt line for a special file")


def git_path():
    return shutil.which("git")


def git_env():
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    env.update(pc_manifest.GIT_ENV_OVERRIDES)
    # A placeholder identity on a reserved example domain.
    env.update({
        "GIT_AUTHOR_NAME": "Harness Test", "GIT_AUTHOR_EMAIL": "harness@example.com",
        "GIT_COMMITTER_NAME": "Harness Test", "GIT_COMMITTER_EMAIL": "harness@example.com",
    })
    return env


def run_git(repo, *args):
    result = subprocess.run(
        [git_path(), "-C", repo] + list(args), env=git_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise AssertionError("temporary-repository setup command failed")
    return result.stdout


class GitStatusCaptureTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        if git_path() is None:
            raise unittest.SkipTest("git is not installed on this machine")
        cls.repo = tempfile.mkdtemp(prefix="preclear-git-")
        run_git(cls.repo, "init", "-q")
        base = os.fsencode(cls.repo)
        for name in (b"old-name.txt", b"tracked.txt"):
            with open(os.path.join(base, name), "xb") as handle:
                handle.write(b"content of " + name + b"\n")
        run_git(cls.repo, "add", "-A")
        run_git(cls.repo, "commit", "-q", "-m", "initial")
        run_git(cls.repo, "mv", "old-name.txt", "new-name.txt")
        untracked = [
            b"with space.txt", b'quote"mark.txt', b"line-one" + b"\n" + b"line-two.txt",
            chr(0x6587).encode("utf-8") + b".txt", b"untracked.txt",
        ]
        for name in untracked:
            with open(os.path.join(base, name), "xb") as handle:
                handle.write(b"untracked " + name + b"\n")
        # Make a tracked file stat-dirty, which a plain git status would refresh in the index.
        os.utime(os.path.join(base, b"tracked.txt"), (1, 1))
        cls.raw, cls.text = pc_manifest.capture_git_status(cls.repo, git_path())

    def test_the_raw_form_is_nul_separated_and_keeps_the_newline_name_whole(self):
        self.ok(b"\x00" in self.raw, "NUL separated")
        self.ok(b"?? line-one" + b"\n" + b"line-two.txt" + b"\x00" in self.raw, "the newline-named file is one record")
        self.ok(b"R  new-name.txt\x00old-name.txt\x00" in self.raw, "the rename is one NUL-separated record pair")
        self.ok(b"?? untracked.txt\x00" in self.raw, "the untracked file is listed (untracked-files=all)")

    def test_the_text_form_carries_gits_quoting_for_the_newline_name(self):
        self.ok(b'?? "line-one\\nline-two.txt"' in self.text, "git quotes the newline name in the plain form")
        self.ok(b"R  old-name.txt -> new-name.txt" in self.text, "the rename record is printed verbatim")
        self.ok(b"\x00" not in self.text, "the text form has no NUL bytes")

    def test_both_forms_cover_the_same_changes(self):
        self.ok(self.text.count(b"\n") >= 2 and self.raw.count(b"\x00") >= 3, "both forms list the changes")

    def test_two_captures_leave_the_index_file_bytes_unchanged(self):
        index_path = os.path.join(self.repo, ".git", "index")
        with open(index_path, "rb") as handle:
            before = hashlib.sha256(handle.read()).hexdigest()
        pc_manifest.capture_git_status(self.repo, git_path())
        pc_manifest.capture_git_status(self.repo, git_path())
        with open(index_path, "rb") as handle:
            after = hashlib.sha256(handle.read()).hexdigest()
        self.ok(before == after, "the index digest is identical before and after two captures")

    def test_a_failing_status_raises(self):
        not_a_repo = tempfile.mkdtemp(prefix="preclear-git-")
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.capture_git_status(not_a_repo, git_path())

    def test_the_environment_overrides_are_the_four_hygiene_variables(self):
        self.ok(pc_manifest.GIT_ENV_OVERRIDES == {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        }, "overrides match the plan")


if __name__ == "__main__":
    unittest.main()
