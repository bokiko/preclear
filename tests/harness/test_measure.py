"""Tests for pc_measure: the heading-inclusive UTF-8 byte measurer (EVID-01).

Fixtures are synthetic byte strings with hand-computed sizes (the committed evidence is
sanitized, so it cannot serve as an oracle). Non-ASCII text is built from code points so
this file stays ASCII. Scratch files come from tempfile.mkdtemp and are never deleted.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
MEASURE_CLI = os.path.join(HARNESS_DIR, "pc_measure.py")
MEASURE_SOURCE = os.path.join(HARNESS_DIR, "pc_measure.py")
SKILL_PATH = os.path.join(REPO_ROOT, "SKILL.md")

import pc_measure  # noqa: E402  (the harness folder is on sys.path via discovery)

HEADINGS = (
    "Identity and state",
    "Boundaries and blockers",
    "Next action",
    "Resume reading",
    "Evidence and working changes",
    "Do not redo",
)

E_ACUTE = chr(0xE9)          # 2 bytes in UTF-8
CJK = chr(0x6587) + chr(0x4EF6)  # 3 bytes each, 6 in all
EMOJI = chr(0x1F600)         # 4 bytes


def section(name, body):
    """One section as bytes: heading line, newline, body. Nothing is stripped."""
    return b"## " + name.encode("utf-8") + b"\n" + body


def six_sections(bodies):
    return b"".join(section(h, b) for h, b in zip(HEADINGS, bodies))


def rows_by_name(measurement):
    return [(name, size, cap) for name, size, cap in measurement["rows"]]


class MeasureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.mkdtemp(prefix="preclear-ms-")  # never deleted, never printed
        cls.counter = 0

    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)

    def write_fixture(self, data):
        type(self).counter += 1
        path = os.path.join(self.scratch, "fixture-%d.md" % type(self).counter)
        with open(path, "xb") as handle:
            handle.write(data)
        return path


class AsciiFixtureTests(MeasureTestCase):
    def test_each_section_is_heading_line_plus_body_and_the_total_is_the_file_size(self):
        bodies = [b"a\n", b"bb\n", b"ccc\n", b"dddd\n", b"eeeee\n", b"ffffff\n"]
        data = six_sections(bodies)
        # Hand computation: a heading line is 3 ("## ") + name length + 1 (newline).
        #   Identity and state          3 + 18 + 1 = 22, body 2  -> 24
        #   Boundaries and blockers     3 + 23 + 1 = 27, body 3  -> 30
        #   Next action                 3 + 11 + 1 = 15, body 4  -> 19
        #   Resume reading              3 + 14 + 1 = 18, body 5  -> 23
        #   Evidence and working changes 3 + 28 + 1 = 32, body 6 -> 38
        #   Do not redo                 3 + 11 + 1 = 15, body 7  -> 22
        expected = [24, 30, 19, 23, 38, 22]
        path = self.write_fixture(data)
        measured = pc_measure.measure_file(path)
        self.ok([size for _n, size, _c in measured["rows"]] == expected, "per-section sizes")
        self.ok([n for n, _s, _c in measured["rows"]] == list(HEADINGS), "section names in file order")
        self.ok(measured["total"] == sum(expected) == 156, "total is the sum of the sections")
        self.ok(measured["total"] == os.path.getsize(path), "total equals the file size")
        self.ok(measured["sha256"] == hashlib.sha256(data).hexdigest(), "digest is over the original bytes")
        self.ok(measured["missing"] == [], "no expected heading is missing")

    def test_caps_travel_with_the_rows(self):
        measured = pc_measure.measure_bytes(six_sections([b"x\n"] * 6))
        self.ok([c for _n, _s, c in measured["rows"]] == [800, 600, 500, 600, 1000, 596], "caps per section")


class MultibyteFixtureTests(MeasureTestCase):
    def test_a_two_byte_letter_counts_two_bytes(self):
        # Heading "Next action" line is 15; body "caf" + e-acute + newline is 3 + 2 + 1 = 6.
        data = section("Next action", ("caf" + E_ACUTE + "\n").encode("utf-8"))
        measured = pc_measure.measure_bytes(data)
        self.ok(measured["rows"] == [("Next action", 21, 500)], "two-byte letter measured by bytes, not characters")
        self.ok(measured["total"] == 21, "total in bytes")

    def test_a_three_byte_cjk_character_counts_three_bytes_each(self):
        # Two CJK characters are 6 bytes, plus the newline: 7. Heading 15.
        data = section("Next action", (CJK + "\n").encode("utf-8"))
        self.ok(pc_measure.measure_bytes(data)["rows"] == [("Next action", 22, 500)], "cjk measured by bytes")

    def test_a_four_byte_emoji_counts_four_bytes(self):
        # One emoji is 4 bytes, plus the newline: 5. Heading 15.
        data = section("Do not redo", (EMOJI + "\n").encode("utf-8"))
        self.ok(pc_measure.measure_bytes(data)["rows"] == [("Do not redo", 20, 596)], "emoji measured by bytes")

    def test_a_heading_with_a_non_ascii_name_is_measured_by_bytes(self):
        data = b"## Caf" + E_ACUTE.encode("utf-8") + b"\nx\n"
        measured = pc_measure.measure_bytes(data)
        self.ok(measured["total"] == 3 + 3 + 2 + 1 + 2 == 11, "heading and body bytes")

    def test_sizes_agree_with_file_size_and_with_wc_where_wc_exists(self):
        body = ("caf" + E_ACUTE + " " + CJK + " " + EMOJI + "\n").encode("utf-8")
        data = section("Next action", body)
        path = self.write_fixture(data)
        measured = pc_measure.measure_file(path)
        self.ok(measured["total"] == os.path.getsize(path) == len(data), "agrees with file size")
        wc = shutil.which("wc")
        if wc is None:
            self.skipTest("wc is not installed on this machine, the file-size oracle above still ran")
        with open(path, "rb") as handle:
            result = subprocess.run([wc, "-c"], stdin=handle, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.ok(result.returncode == 0, "wc ran")
        self.ok(int(result.stdout.split()[0]) == measured["total"], "agrees with wc -c")


class CrlfFixtureTests(MeasureTestCase):
    def test_crlf_line_ends_count_two_bytes_each_and_nothing_is_translated(self):
        # Heading "Resume reading" line with CRLF: 3 + 14 + 2 = 19. Body "a", CRLF, "b", CRLF = 6.
        data = b"## Resume reading\r\n" + b"a\r\nb\r\n"
        path = self.write_fixture(data)
        measured = pc_measure.measure_file(path)
        self.ok(measured["rows"] == [("Resume reading", 25, 600)], "CRLF bytes are counted")
        self.ok(measured["total"] == 25 == os.path.getsize(path), "file size agrees")
        self.ok(measured["rows"][0][0] == "Resume reading", "a trailing carriage return is not part of the heading name")

    def test_crlf_file_still_splits_at_every_heading(self):
        data = b"## Identity and state\r\nx\r\n## Next action\r\ny\r\n"
        rows = pc_measure.measure_bytes(data)["rows"]
        self.ok([n for n, _s, _c in rows] == ["Identity and state", "Next action"], "two sections found")
        self.ok(sum(s for _n, s, _c in rows) == len(data), "sections sum to the total")


class PreambleAndOtherTests(MeasureTestCase):
    def test_a_title_line_is_a_preamble_row_and_the_sum_still_equals_the_total(self):
        data = b"# Title\n\n" + six_sections([b"x\n"] * 6)
        measured = pc_measure.measure_bytes(data)
        names = [n for n, _s, _c in measured["rows"]]
        self.ok(names[0] == "(preamble)" and names[1:] == list(HEADINGS), "preamble row first")
        self.ok(measured["rows"][0] == ("(preamble)", 9, None), "preamble is 9 bytes with no cap")
        self.ok(sum(s for _n, s, _c in measured["rows"]) == measured["total"] == len(data), "rows sum to the total")

    def test_an_unknown_heading_is_an_other_row_without_a_cap(self):
        data = six_sections([b"x\n"] * 6) + b"## Extra\nxx\n"
        measured = pc_measure.measure_bytes(data)
        self.ok(measured["rows"][-1] == ("(other)", 12, None), "other row: 3 + 5 + 1 + 3 = 12 bytes, no cap")
        self.ok(sum(s for _n, s, _c in measured["rows"]) == measured["total"], "rows sum to the total")

    def test_missing_headings_are_listed_and_duplicates_are_separate_rows(self):
        data = section("Next action", b"a\n") + section("Next action", b"b\n")
        measured = pc_measure.measure_bytes(data)
        self.ok([n for n, _s, _c in measured["rows"]] == ["Next action", "Next action"], "duplicates stay separate")
        self.ok("Identity and state" in measured["missing"] and "Next action" not in measured["missing"], "missing list")

    def test_a_sub_heading_is_part_of_its_section_not_a_new_one(self):
        data = section("Next action", b"### detail\ntext\n")
        self.ok(len(pc_measure.measure_bytes(data)["rows"]) == 1, "### does not start a section")

    def test_an_empty_file_has_no_rows_and_every_heading_missing(self):
        measured = pc_measure.measure_bytes(b"")
        self.ok(measured["total"] == 0 and measured["rows"] == [], "nothing measured")
        self.ok(measured["missing"] == list(HEADINGS), "every heading is missing")
        self.ok(measured["sha256"] == hashlib.sha256(b"").hexdigest(), "digest of nothing")


def exact_size_sections(sizes):
    """Six sections whose byte lengths (heading included) are exactly SIZES."""
    pieces = []
    for name, size in zip(HEADINGS, sizes):
        head = b"## " + name.encode("utf-8") + b"\n"
        pieces.append(head + b"x" * (size - len(head) - 1) + b"\n")
    return b"".join(pieces)


class ReportTests(MeasureTestCase):
    def test_report_prints_actual_over_cap_per_section_in_file_order(self):
        data = six_sections([b"a\n", b"bb\n", b"ccc\n", b"dddd\n", b"eeeee\n", b"ffffff\n"])
        lines = pc_measure.format_report("fixture", pc_measure.measure_bytes(data)).splitlines()
        self.ok(lines[0] == "## fixture", "heading line carries the label")
        self.ok(lines[1] == "total 156/4096 bytes, sha256 " + hashlib.sha256(data).hexdigest(), "total line")
        self.ok(lines[2:] == [
            "- Identity and state: 24/800",
            "- Boundaries and blockers: 30/600",
            "- Next action: 19/500",
            "- Resume reading: 23/600",
            "- Evidence and working changes: 38/1000",
            "- Do not redo: 22/596",
        ], "one actual/cap line per section, in file order")

    def test_a_file_of_exactly_4096_bytes_shows_no_over_by_and_exits_0(self):
        data = exact_size_sections([800, 600, 500, 600, 1000, 596])
        self.ok(len(data) == 4096, "fixture is exactly 4096 bytes")
        report = pc_measure.format_report("at-cap", pc_measure.measure_bytes(data))
        self.ok("total 4096/4096 bytes" in report, "total at the cap")
        self.ok("over by" not in report, "no over-by suffix at the cap")
        self.ok(self.run_cli(self.write_fixture(data)).returncode == 0, "CLI exits 0")

    def test_a_file_of_4097_bytes_shows_over_by_1_and_still_exits_0(self):
        data = exact_size_sections([800, 600, 500, 600, 1000, 597])
        self.ok(len(data) == 4097, "fixture is exactly 4097 bytes")
        report = pc_measure.format_report("over-cap", pc_measure.measure_bytes(data))
        self.ok(re.search(r"^total 4097/4096 bytes, sha256 [0-9a-f]{64} over by 1$", report, re.M), "total over by 1")
        self.ok("- Do not redo: 597/596 over by 1" in report.splitlines(), "row over by 1")
        result = self.run_cli(self.write_fixture(data))
        self.ok(result.returncode == 0, "CLI exits 0 for an over-cap file")
        self.ok(b"over by 1" in result.stdout, "CLI prints the over-by fact")

    def test_rows_without_a_cap_and_missing_headings_are_printed_as_facts(self):
        data = b"# Title\n" + section("Next action", b"a\n") + b"## Extra\nb\n"
        lines = pc_measure.format_report("odd", pc_measure.measure_bytes(data)).splitlines()
        self.ok("- (preamble): 8" in lines, "preamble row without a cap")
        self.ok("- Next action: 17/500" in lines, "section row")
        self.ok("- (other): 11" in lines, "other row without a cap")
        self.ok(lines[-1].startswith("missing: Identity and state, "), "missing headings on the last line")

    def test_the_report_states_facts_and_never_a_verdict_word(self):
        data = exact_size_sections([900, 600, 500, 600, 1000, 600])
        report = pc_measure.format_report("over", pc_measure.measure_bytes(data))
        verdicts = re.compile(r"\b(pass|passed|fail|failed|ok|valid|invalid|error|violation|exceeds|too large)\b", re.I)
        self.ok(verdicts.search(report) is None, "no verdict word in the report")

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-E", "-s", "-B", MEASURE_CLI] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_cli_exits_2_with_no_arguments_or_an_unreadable_file(self):
        self.ok(self.run_cli().returncode == 2, "no arguments exits 2")
        self.ok(self.run_cli(os.path.join(self.scratch, "no-such-file")).returncode == 2, "unreadable file exits 2")

    def test_cli_prints_one_report_per_readable_file(self):
        first = self.write_fixture(section("Next action", b"a\n"))
        second = self.write_fixture(section("Do not redo", b"b\n"))
        result = self.run_cli(first, second)
        self.ok(result.returncode == 0, "readable files exit 0")
        self.ok(result.stdout.decode("utf-8").count("total ") == 2, "one total line per file")


class SchemaConstantsTests(MeasureTestCase):
    def test_constants_equal_the_schema_table_read_from_skill_md(self):
        with open(SKILL_PATH, "rb") as handle:
            text = handle.read().decode("utf-8")
        rows = re.findall(r"^\| `## (.+?)` \| ([0-9,]+) \|", text, re.M)
        parsed = [(name, int(cap.replace(",", ""))) for name, cap in rows]
        self.ok(len(parsed) == 6, "six schema rows found in SKILL.md")
        self.ok(list(pc_measure.SECTIONS) == parsed, "section names and caps equal the Schema table")
        whole = re.search(r"Whole file under \*\*([0-9,]+) bytes\*\*", text)
        self.ok(whole is not None, "file cap sentence found in SKILL.md")
        self.ok(pc_measure.FILE_CAP == int(whole.group(1).replace(",", "")) == 4096, "file cap equals SKILL.md")

    def test_section_caps_sum_to_the_file_cap(self):
        self.ok(sum(cap for _n, cap in pc_measure.SECTIONS) == pc_measure.FILE_CAP, "caps sum to 4096")


class StaticShapeTests(MeasureTestCase):
    @classmethod
    def setUpClass(cls):
        super(StaticShapeTests, cls).setUpClass()
        with open(MEASURE_SOURCE, "rb") as handle:
            cls.tree = ast.parse(handle.read())

    @staticmethod
    def call_names(node):
        names = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name):
                    names.append(func.id)
                elif isinstance(func, ast.Attribute):
                    names.append(func.attr)
        return names

    def test_measure_file_contains_exactly_one_open_call(self):
        funcs = [n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef) and n.name == "measure_file"]
        self.ok(len(funcs) == 1, "measure_file is defined once")
        self.ok(self.call_names(funcs[0]).count("open") == 1, "exactly one open call in measure_file")

    def test_the_module_opens_one_file_and_writes_none(self):
        names = self.call_names(self.tree)
        self.ok(names.count("open") == 1, "the only open call in the module is the one in measure_file")
        # str.replace is not a file operation, so it is left out; test_runroot's harness-wide
        # scan covers os.replace and the one-argument Path.replace.
        for forbidden in ("write", "writelines", "write_text", "write_bytes", "truncate", "unlink", "remove", "rename"):
            self.ok(forbidden not in names, "pc_measure makes no %s call" % forbidden)


if __name__ == "__main__":
    unittest.main()
