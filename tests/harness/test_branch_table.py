"""Tests for tests/harness/data/branch-table.md (STUB-05, D-06, D-07).

The branch table documents what the stub does branch by branch and marks every branch the
committed evidence does not show as UNCONFIRMED. These tests parse the Markdown table and check
its codes, statuses, ordering and evidence paths, and tie it to the stub's own docstring so the
two cannot drift. Plain file reads only.
"""
from __future__ import annotations

import ast
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pc_exitcodes  # noqa: E402

TABLE = os.path.join(HERE, "data", "branch-table.md")
STUB = os.path.join(HERE, "checkpoint_stub.py")
HEADER = ["Branch", "Command", "Exit", "Evidence", "Status"]
STATUSES = ("CONFIRMED", "UNCONFIRMED", "STUB-ONLY")
VERB_ORDER = ("status", "show", "validate", "update", "note", "lint", "handoff", "bind")
WRAPPER_ONLY = (70, 71)


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_rows():
    assert os.path.isfile(TABLE), "tests/harness/data/branch-table.md does not exist"
    lines = read_text(TABLE).split("\n")
    start = None
    for index, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells == HEADER:
            start = index
            break
    assert start is not None, "no table header with the columns " + ", ".join(HEADER)
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def verb_index(command):
    first = norm(command).split(" ")[0] if norm(command) else ""
    return VERB_ORDER.index(first) if first in VERB_ORDER else len(VERB_ORDER)


class TableShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()
        cls.text = read_text(TABLE)

    def test_the_stub_is_branded_and_the_table_parses(self):
        self.assertIn("STUB-BACKED", self.text)
        self.assertGreaterEqual(len(self.rows), 25)
        for row in self.rows:
            self.assertEqual(5, len(row), row)

    def test_every_exit_code_is_present_and_the_set_matches_the_named_codes(self):
        exits = set(int(row[2]) for row in self.rows)
        stub_codes = set(
            [
                pc_exitcodes.STUB_OK,
                pc_exitcodes.STUB_INTERNAL,
                pc_exitcodes.STUB_USAGE,
                pc_exitcodes.STUB_CONFLICT,
                pc_exitcodes.STUB_INVALID,
                pc_exitcodes.STUB_KILL_SWITCH,
                pc_exitcodes.STUB_LOCK_TIMEOUT,
                pc_exitcodes.STUB_NO_CKPT_HOME,
            ]
        )
        self.assertEqual(stub_codes | set(WRAPPER_ONLY), exits)
        self.assertEqual(set(range(0, 7)), set(range(0, 7)) & exits)

    def test_rows_are_in_ascending_exit_order_then_verb_order(self):
        keys = [(int(row[2]), verb_index(row[1])) for row in self.rows]
        self.assertEqual(sorted(keys), keys)

    def test_no_cell_is_empty_and_statuses_are_the_three_allowed_values(self):
        for row in self.rows:
            for cell in row:
                self.assertNotEqual("", cell, row)
            self.assertIn(row[4], STATUSES, row)
            self.assertRegex(row[2], r"^[0-9]+$")

    def test_no_two_rows_repeat_the_same_branch(self):
        seen = set()
        for row in self.rows:
            key = (norm(row[0]), norm(row[1]), row[2])
            self.assertNotIn(key, seen, row)
            seen.add(key)

    def test_stub_only_and_wrapper_only_codes_are_marked_stub_only(self):
        for row in self.rows:
            if int(row[2]) in (64, 70, 71):
                self.assertEqual("STUB-ONLY", row[4], row)

    def test_a_branch_with_no_committed_evidence_says_so_and_is_unconfirmed(self):
        for row in self.rows:
            evidence = row[3].lower()
            if "document only" in evidence or evidence.startswith("none"):
                self.assertEqual("UNCONFIRMED", row[4], row)


class UnconfirmedRowsTests(unittest.TestCase):
    PHRASES = (
        "note",
        "handoff",
        "exit 5",
        "exit 6",
        "checkpoint none",
        "carried from",
        "lint warning",
        "validate rejection",
        "exit 1",
        "bind create",
        "section hash derivation",
        "ledger roots json",
        "repeated section",
    )

    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()

    def unconfirmed_branches(self):
        return [norm(row[0]) for row in self.rows if row[4] == "UNCONFIRMED"]

    def test_the_named_branches_are_unconfirmed(self):
        branches = self.unconfirmed_branches()
        for phrase in self.PHRASES:
            if phrase in ("note", "handoff"):
                found = [b for b in branches if b.startswith(phrase)]
            else:
                found = [b for b in branches if phrase in b]
            self.assertTrue(found, "no UNCONFIRMED row for " + phrase)

    def test_no_named_branch_is_marked_confirmed(self):
        confirmed = [norm(row[0]) for row in self.rows if row[4] == "CONFIRMED"]
        for phrase in ("handoff", "exit 5", "exit 6", "lint warning", "bind create", "section hash derivation"):
            self.assertEqual([], [b for b in confirmed if phrase in b], phrase)
        self.assertEqual([], [b for b in confirmed if b.startswith("note")])

    def test_the_hash_derivation_row_records_what_is_and_is_not_provable(self):
        rows = [row for row in self.rows if "section hash derivation" in norm(row[0])]
        self.assertEqual(1, len(rows))
        text = " ".join(rows[0]).lower()
        for needle in ("sha.txt", "four path-free", "two path-bearing", "sanitised", "whitespace", "show output"):
            self.assertIn(needle, text)
        self.assertEqual("UNCONFIRMED", rows[0][4])

    def test_every_unconfirmed_behaviour_in_the_stub_docstring_has_an_unconfirmed_row(self):
        doc = ast.get_docstring(ast.parse(read_text(STUB))) or ""
        marker = "UNCONFIRMED behaviours."
        self.assertIn(marker, doc)
        listed = doc.split(marker, 1)[1]
        bullets = re.findall(r"(?ms)^  \* (.*?)(?=^  \* |\Z)", listed)
        self.assertGreaterEqual(len(bullets), 10)
        rows_text = [norm(" ".join(row[:2])) for row in self.rows if row[4] == "UNCONFIRMED"]
        for bullet in bullets:
            key = " ".join(norm(bullet).split(" ")[:3])
            self.assertTrue(
                any(key in text for text in rows_text),
                "the stub docstring lists %r but no UNCONFIRMED row names it" % key,
            )


class EvidencePathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()

    def paths(self, cell):
        return [token for token in re.findall(r"`([^`]+)`", cell) if "/" in token]

    def test_every_confirmed_row_names_an_existing_evidence_path(self):
        confirmed = [row for row in self.rows if row[4] == "CONFIRMED"]
        self.assertGreaterEqual(len(confirmed), 10)
        for row in confirmed:
            paths = self.paths(row[3])
            self.assertTrue(paths, "a CONFIRMED row names no evidence path: " + row[0])
            for path in paths:
                self.assertTrue(path.startswith("tests/evidence/"), path)

    def test_every_named_path_exists_in_the_repository(self):
        for row in self.rows:
            for path in self.paths(row[3]):
                self.assertFalse(os.path.isabs(path), path)
                self.assertTrue(os.path.exists(os.path.join(ROOT, *path.split("/"))), path)


class SectionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert os.path.isfile(TABLE), "tests/harness/data/branch-table.md does not exist"
        cls.text = read_text(TABLE)

    def section(self, title):
        match = re.search(r"(?ms)^## %s\n(.*?)(?=^## |\Z)" % re.escape(title), self.text)
        self.assertIsNotNone(match, "no section titled " + title)
        return match.group(1)

    def test_the_wrapper_section_names_its_files(self):
        body = self.section("Wrapper (outside the stub)")
        for name in ("calls.log", "injection.log", "armed", "target-section", "writer2.session", "`py`", "`stub`"):
            self.assertIn(name, body)

    def test_the_not_modelled_section_names_the_heuristics_and_the_indirect_routes(self):
        body = self.section("Not modelled")
        for needle in ("cd", "redirection", "path scope", "brace", "read-only", "env", "python3 -c", "awk", "find", "exit 71"):
            self.assertIn(needle, body)


if __name__ == "__main__":
    unittest.main()
