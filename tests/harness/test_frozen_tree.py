"""The skill, its references, the fixtures and the committed evidence are pinned (HARN-13; T-03-34).

SKILL.md is at most 12,000 bytes, read from the file at test time. The sha256 of SKILL.md and the tree digests of
references/, tests/fixtures/ and tests/evidence/publication-2026-10-20/ are pinned below. Each pinned value was
computed once from a tree for which

    git diff --name-only 56e155c -- SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20

printed nothing, so the constants describe the base commit and not a later edit. A tree digest is the one the
read-only comparer prints: sha256 over the lossless manifest bytes of the whole folder (names, bytes, empty
folders and symlink targets; file modes and timestamps are not part of it).

A legitimate fix to a defect that a rerun exposes must change the matching constant in the same commit, on
purpose. That friction is the point: the skill, the fixtures and the committed evidence cannot change silently.
A pinned value is never edited to make a changed tree pass.

Plain file reads only; no git command runs here. A failure names which tree differs and never a path.
"""
from __future__ import annotations

import hashlib
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

SKILL = os.path.join(ROOT, "SKILL.md")
REFERENCES = os.path.join(ROOT, "references")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
PUBLICATION = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")

SKILL_MAX_BYTES = 12000

SKILL_SHA256 = "0" * 64
REFERENCES_TREE_SHA256 = "0" * 64
FIXTURES_TREE_SHA256 = "0" * 64
PUBLICATION_TREE_SHA256 = "0" * 64

HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def skill_sha256():
    with open(SKILL, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def tree_digest(folder):
    import pc_compare

    return pc_compare.tree_digest(folder)


class SkillSizeTests(unittest.TestCase):
    def test_skill_md_is_at_or_under_its_size_cap(self):
        self.assertTrue(os.path.isfile(SKILL), "SKILL.md exists")
        size = os.path.getsize(SKILL)
        self.assertLessEqual(size, SKILL_MAX_BYTES, "SKILL.md is over its size cap")

    def test_the_cap_is_twelve_thousand_bytes(self):
        self.assertEqual(SKILL_MAX_BYTES, 12000, "the cap constant")


class FrozenTreeTests(unittest.TestCase):
    def test_every_pinned_value_is_64_lower_case_hex_characters(self):
        for name, value in (
            ("SKILL_SHA256", SKILL_SHA256),
            ("REFERENCES_TREE_SHA256", REFERENCES_TREE_SHA256),
            ("FIXTURES_TREE_SHA256", FIXTURES_TREE_SHA256),
            ("PUBLICATION_TREE_SHA256", PUBLICATION_TREE_SHA256),
        ):
            self.assertIsNotNone(HEX64.match(value), "%s is not 64 lower-case hex characters" % name)

    def test_the_pinned_values_are_not_the_placeholder(self):
        for name, value in (
            ("SKILL_SHA256", SKILL_SHA256),
            ("REFERENCES_TREE_SHA256", REFERENCES_TREE_SHA256),
            ("FIXTURES_TREE_SHA256", FIXTURES_TREE_SHA256),
            ("PUBLICATION_TREE_SHA256", PUBLICATION_TREE_SHA256),
        ):
            self.assertNotEqual(value, "0" * 64, "%s is still the placeholder" % name)

    def test_the_four_pinned_values_are_different_from_each_other(self):
        values = [SKILL_SHA256, REFERENCES_TREE_SHA256, FIXTURES_TREE_SHA256, PUBLICATION_TREE_SHA256]
        self.assertEqual(len(set(values)), 4, "each pinned value describes a different tree")

    def test_skill_md_matches_its_pinned_digest(self):
        self.assertEqual(skill_sha256(), SKILL_SHA256, "SKILL.md differs from its pinned digest")

    def test_the_references_tree_matches_its_pinned_digest(self):
        self.assertEqual(tree_digest(REFERENCES), REFERENCES_TREE_SHA256, "the references tree differs from its pinned digest")

    def test_the_fixtures_tree_matches_its_pinned_digest(self):
        self.assertEqual(tree_digest(FIXTURES), FIXTURES_TREE_SHA256, "the fixtures tree differs from its pinned digest")

    def test_the_committed_publication_evidence_matches_its_pinned_digest(self):
        self.assertEqual(tree_digest(PUBLICATION), PUBLICATION_TREE_SHA256, "the publication evidence differs from its pinned digest")


if __name__ == "__main__":
    unittest.main()
