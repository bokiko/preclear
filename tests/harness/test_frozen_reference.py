"""The frozen reference is byte for byte what the committed evidence ran on (STUB-07).

references/checkpoint-v1.md is read and hashed, never edited. Every digests.txt under the
publication evidence records the adapter digest of the run it belongs to: 15 folders carry the
current digest (the post-fix runs) and 7 carry one earlier value (the pre-fix runs). The digest
values are read from the evidence at test time and never typed here. Plain file reads only; no
git command is run against the repository.

Stub documentation lives under tests/harness only: nothing under references/ mentions the stub.
"""
from __future__ import annotations

import hashlib
import os
import re
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REFERENCE = os.path.join(ROOT, "references", "checkpoint-v1.md")
EVIDENCE = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")

POST_FIX_FOLDERS = 15
PRE_FIX_FOLDERS = 7
SUFFIX = "references/checkpoint-v1.md"
DIGEST_LINE = re.compile(r"^([0-9a-f]{64})  (\S.*)$")


def current_digest():
    with open(REFERENCE, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def committed_digests():
    """One (folder, digest) pair for every digests.txt line that names the reference."""
    found = []
    for current, dirs, files in os.walk(EVIDENCE):
        dirs.sort()
        if "digests.txt" not in files:
            continue
        with open(os.path.join(current, "digests.txt"), "r", encoding="utf-8") as handle:
            for line in handle.read().splitlines():
                match = DIGEST_LINE.match(line)
                if match is not None and match.group(2).endswith(SUFFIX):
                    found.append((os.path.relpath(current, EVIDENCE), match.group(1)))
    return found


class FrozenReferenceTests(unittest.TestCase):
    def test_the_reference_exists_and_the_evidence_holds_digest_lines(self):
        self.assertTrue(os.path.isfile(REFERENCE))
        self.assertTrue(committed_digests())

    def test_the_current_digest_appears_in_the_post_fix_folders(self):
        current = current_digest()
        folders = [folder for folder, digest in committed_digests() if digest == current]
        self.assertGreaterEqual(len(folders), POST_FIX_FOLDERS)
        self.assertEqual(len(folders), len(set(folders)), "one reference line per folder")

    def test_the_only_other_digest_is_one_pre_fix_value_in_seven_folders(self):
        current = current_digest()
        pairs = committed_digests()
        others = Counter(digest for _, digest in pairs if digest != current)
        self.assertEqual(1, len(others), "evidence holds exactly one other adapter digest")
        self.assertEqual(PRE_FIX_FOLDERS, list(others.values())[0])
        self.assertEqual(set([current]) | set(others), set(digest for _, digest in pairs))

    def test_every_folder_names_the_reference_once(self):
        counts = Counter(folder for folder, _ in committed_digests())
        self.assertEqual(POST_FIX_FOLDERS + PRE_FIX_FOLDERS, len(counts))
        self.assertEqual(set([1]), set(counts.values()))

    def test_nothing_under_references_mentions_the_stub(self):
        folder = os.path.join(ROOT, "references")
        for name in sorted(os.listdir(folder)):
            self.assertNotIn("stub", name.lower(), name)
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                with open(path, "rb") as handle:
                    data = handle.read().lower()
                self.assertNotIn(b"stub-backed", data, name)
                self.assertNotIn(b"checkpoint_stub", data, name)


if __name__ == "__main__":
    unittest.main()
