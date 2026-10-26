"""The stranger README must equal the code it describes (EVID-07, HARN-14; D-03, D-08, D-10, D-12).

README.md carries three tables between begin and end markers (flag table, exit codes, switches),
the isolation claim line and a layout list. Each is compared with the code at every run, so prose
and code cannot drift:

  * the flag table equals pc_flags.render_flag_table_markdown() exactly;
  * the exit-code table has one row per integer constant of pc_exitcodes, with its value and the
    describe() text;
  * the switch table names exactly CKPT_HOME, the two CKPT_STUB_ switches (which also equal the
    set in the stub's source), CLAUDE_CODE_SESSION_ID, PRECLEAR_HARNESS_HOME and PC_SELFTEST_PATTERN;
  * the Isolation claim line equals pc_flags.ISOLATION_CLAIM;
  * the layout names every file in the folder once and no file that is missing, except the files
    in PENDING_SPIKE_FILES (created by the spike plan, which asserts they exist);
  * data is the only subfolder, and the README holds no absolute path, home path, host name,
    temporary path, email address, cost figure or package-manager command.

Forbidden-path needles are assembled from fragments at run time; the machine's host name is read
at run time and compared only through boolean checks with fixed messages.
"""
from __future__ import annotations

import os
import re
import socket
import unittest
from typing import List, Optional, Tuple

import pc_exitcodes
import pc_flags

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HARNESS_DIR, "README.md")
STUB = os.path.join(HARNESS_DIR, "checkpoint_stub.py")
GITIGNORE = os.path.join(HARNESS_DIR, ".gitignore")

# The files the spike plan created, listed in the README by these names (relative to the harness
# folder). All of them exist since the spikes ran; the spike fixture test asserts that they do, and
# this tuple stays so a missing one is caught by name.
PENDING_SPIKE_FILES = (
    "pc_spike.py",
    "pc_hooklog.py",
    "test_spike.py",
    "test_spike_fixture.py",
    "data/spike-findings.md",
    "data/s1-init-manifest.json",
    "data/s2-stream.jsonl",
    "data/s2b-stream.jsonl",
    "data/s2-probe-labels.json",
)

SWITCH_NAMES = (
    "CKPT_HOME",
    "CKPT_STUB_KILL_SWITCH",
    "CKPT_STUB_LOCK_TIMEOUT_MS",
    "CLAUDE_CODE_SESSION_ID",
    "PRECLEAR_HARNESS_HOME",
    "PC_SELFTEST_PATTERN",
)

FLAG_MARKERS = ("<!-- flag-table:begin -->", "<!-- flag-table:end -->")
EXIT_MARKERS = ("<!-- exit-codes:begin -->", "<!-- exit-codes:end -->")
SWITCH_MARKERS = ("<!-- switches:begin -->", "<!-- switches:end -->")


def exit_code_constants() -> List[Tuple[str, int]]:
    """Return every integer constant of pc_exitcodes in definition order."""
    return [
        (name, value)
        for name, value in vars(pc_exitcodes).items()
        if name.isupper() and isinstance(value, int) and not isinstance(value, bool)
    ]


def render_exit_code_table() -> str:
    """Return the exit-code table the README must hold between its markers."""
    lines = ["| Constant | Value | Meaning |", "|---|---|---|"]
    for name, value in exit_code_constants():
        lines.append("| `%s` | %d | %s |" % (name, value, pc_exitcodes.describe(value)))
    return "\n".join(lines) + "\n"


def read_readme() -> str:
    with open(README, "r", encoding="utf-8") as handle:
        return handle.read()


def between(text: str, markers: Tuple[str, str]) -> Optional[str]:
    """Return the text between a begin and an end marker, minus the newline after the begin marker."""
    begin, end = markers
    if text.count(begin) != 1 or text.count(end) != 1:
        return None
    start = text.index(begin) + len(begin)
    stop = text.index(end)
    if stop < start:
        return None
    block = text[start:stop]
    if block.startswith("\n"):
        block = block[1:]
    return block


def table_rows(block: str) -> List[List[str]]:
    """Return the body rows of a Markdown table as lists of stripped cells."""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows[2:]


def section(text: str, heading: str) -> str:
    marker = "\n## %s\n" % heading
    if marker not in text:
        return ""
    rest = text.split(marker, 1)[1]
    return rest.split("\n## ", 1)[0]


def folder_files(folder: str) -> List[str]:
    """Return every file under folder as a slash-separated relative path, caches excluded."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(name for name in dirnames if name != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".pyc"):
                continue
            found.append(os.path.relpath(os.path.join(dirpath, name), folder).replace(os.sep, "/"))
    return sorted(found)


def layout_names(text: str) -> List[str]:
    names = []
    for line in section(text, "Layout").splitlines():
        match = re.match(r"^- `([^`]+)` - ", line)
        if match:
            names.append(match.group(1))
    return names


class StartTests(unittest.TestCase):
    def test_the_first_fenced_command_is_the_selftest(self) -> None:
        text = read_readme()
        self.assertIn("```", text)
        block = text.split("```", 2)[1]
        lines = [line for line in block.splitlines()[1:] if line.strip()]
        self.assertEqual(lines, ["tests/harness/selftest"])

    def test_the_selftest_claims_are_stated(self) -> None:
        text = section(read_readme(), "Run this first")
        self.assertIn("spends no tokens", text)
        self.assertIn("`claude` absent", text)
        self.assertIn("python3 -B -m unittest discover -s tests/harness", text)

    def test_what_it_proves_and_does_not_prove_are_both_present(self) -> None:
        text = read_readme()
        self.assertIn("\n## What a green run proves\n", text)
        self.assertIn("\n## What it does not prove\n", text)
        self.assertIn("Nothing about how the skill behaves", text)
        self.assertIn("No verdicts", text)

    def test_requirements_name_the_three_prerequisites_and_no_install(self) -> None:
        text = section(read_readme(), "Requirements")
        for needle in ("Claude Code", "git", "Python 3.9 or newer", "Nothing to install"):
            self.assertIn(needle, text)


class TableTests(unittest.TestCase):
    def test_flag_table_equals_the_rendered_table_exactly(self) -> None:
        block = between(read_readme(), FLAG_MARKERS)
        self.assertIsNotNone(block, "the flag-table markers are missing or repeated")
        self.assertEqual(block, pc_flags.render_flag_table_markdown())

    def test_exit_code_table_has_one_row_per_constant_with_value_and_meaning(self) -> None:
        block = between(read_readme(), EXIT_MARKERS)
        self.assertIsNotNone(block, "the exit-codes markers are missing or repeated")
        assert block is not None
        rows = table_rows(block)
        expected = [
            ("`%s`" % name, str(value), pc_exitcodes.describe(value)) for name, value in exit_code_constants()
        ]
        self.assertEqual([tuple(row) for row in rows], expected)
        self.assertEqual(block, render_exit_code_table())

    def test_every_pc_exitcodes_constant_appears_in_the_table(self) -> None:
        block = between(read_readme(), EXIT_MARKERS)
        assert block is not None
        for name, _value in exit_code_constants():
            self.assertIn("`%s`" % name, block, "a constant is missing from the exit-code table")
        self.assertGreaterEqual(len(exit_code_constants()), 20)

    def test_switch_table_names_exactly_the_documented_variables(self) -> None:
        block = between(read_readme(), SWITCH_MARKERS)
        self.assertIsNotNone(block, "the switches markers are missing or repeated")
        assert block is not None
        names = [row[0].strip("`") for row in table_rows(block)]
        self.assertEqual(sorted(names), sorted(SWITCH_NAMES))
        self.assertEqual(len(names), len(set(names)))

    def test_the_two_stub_switches_equal_the_set_in_the_stub_source(self) -> None:
        with open(STUB, "r", encoding="utf-8") as handle:
            in_source = sorted(set(re.findall(r"CKPT_STUB_[A-Z_]+", handle.read())))
        block = between(read_readme(), SWITCH_MARKERS)
        assert block is not None
        in_readme = sorted(row[0].strip("`") for row in table_rows(block) if row[0].strip("`").startswith("CKPT_STUB_"))
        self.assertEqual(in_readme, in_source)
        self.assertEqual(len(in_source), 2)

    def test_the_wrapper_codes_are_mentioned_beside_the_exit_table(self) -> None:
        text = section(read_readme(), "Exit codes")
        self.assertIn("70", text)
        self.assertIn("71", text)


class StatementTests(unittest.TestCase):
    def test_the_isolation_claim_line_equals_the_constant(self) -> None:
        lines = [line for line in read_readme().splitlines() if line.startswith("Isolation claim:")]
        self.assertEqual(lines, [pc_flags.ISOLATION_CLAIM])

    def test_the_findings_and_branch_table_files_are_named(self) -> None:
        text = read_readme()
        self.assertIn("tests/harness/data/spike-findings.md", text)
        self.assertIn("tests/harness/data/branch-table.md", text)

    def test_the_one_time_login_is_stated_with_the_command_shape_and_the_keychain_warning(self) -> None:
        text = section(read_readme(), "Isolation and the one-time login")
        self.assertIn("CLAUDE_CONFIG_DIR=", text)
        self.assertIn("claude auth login", text)
        self.assertIn("Keychain", text)
        self.assertIn("never reads, writes or copies credentials", text)
        self.assertIn("BLOCKED", text)

    def test_stub_backed_results_are_not_real_helper_results(self) -> None:
        text = section(read_readme(), "The stub")
        self.assertIn("STUB-BACKED", text)
        self.assertIn("not real-helper results", text)

    def test_platforms_name_macos_verified_and_linux_unverified(self) -> None:
        text = section(read_readme(), "Platforms")
        self.assertIn("macOS", text)
        self.assertIn("Linux", text)
        self.assertIn("unverified", text)

    def test_the_replacement_tokens_are_listed(self) -> None:
        text = section(read_readme(), "Replacement tokens")
        for token in ("<home>", "<user>", "<host>", "<tmp>", "<repo>", "<run>", "<helper>", "<auto-memory-root>", "<redacted>"):
            self.assertIn(token, text)

    def test_the_spike_section_points_at_the_findings_and_copies_no_number(self) -> None:
        text = section(read_readme(), "Spike spend")
        self.assertIn("Total spend line", text)
        self.assertNotRegex(text, r"\d")

    def test_the_readme_gives_no_cost_figure_and_no_package_manager_command(self) -> None:
        text = read_readme()
        self.assertNotIn("USD", text)
        self.assertIsNone(re.search(r"\$\s?\d", text), "a cost figure appears in the README")
        for command in ("pip install", "pip3 install", "npm install", "cargo add", "cargo install", "brew install"):
            self.assertNotIn(command, text)


class LayoutTests(unittest.TestCase):
    def test_every_file_in_the_folder_is_named_once_in_the_layout(self) -> None:
        listed = layout_names(read_readme())
        self.assertEqual(len(listed), len(set(listed)), "a layout entry is repeated")
        missing_from_layout = sorted(set(folder_files(HARNESS_DIR)) - set(listed))
        self.assertEqual(missing_from_layout, [], "files not named in the layout: %s" % ", ".join(missing_from_layout))

    def test_no_missing_file_is_named_except_the_pending_spike_files(self) -> None:
        listed = set(layout_names(read_readme()))
        absent = sorted(listed - set(folder_files(HARNESS_DIR)))
        unexpected = [name for name in absent if name not in PENDING_SPIKE_FILES]
        self.assertEqual(unexpected, [], "named in the layout but missing: %s" % ", ".join(unexpected))

    def test_the_pending_spike_files_are_all_listed_by_their_planned_names(self) -> None:
        listed = set(layout_names(read_readme()))
        for name in PENDING_SPIKE_FILES:
            self.assertIn(name, listed)

    def test_data_is_the_only_subfolder(self) -> None:
        folders = sorted(
            name
            for name in os.listdir(HARNESS_DIR)
            if os.path.isdir(os.path.join(HARNESS_DIR, name)) and name != "__pycache__"
        )
        self.assertEqual(folders, ["data"])
        for dirpath, dirnames, _filenames in os.walk(os.path.join(HARNESS_DIR, "data")):
            self.assertEqual([name for name in dirnames if name != "__pycache__"], [])

    def test_the_layout_section_follows_the_guide_order_and_ends_before_limits(self) -> None:
        text = read_readme()
        order = [text.index("\n## %s\n" % heading) for heading in ("Run this first", "Environment knobs", "The stub", "Exit codes", "Layout", "Limits")]
        self.assertEqual(order, sorted(order))


class HygieneTests(unittest.TestCase):
    def test_the_readme_holds_no_absolute_path_home_path_or_temp_path(self) -> None:
        text = read_readme()
        slash = "/"
        needles = (
            slash + "Users" + slash,
            slash + "home" + slash,
            slash + "private" + slash,
            slash + "var" + slash + "folders",
            slash + "tmp" + slash,
        )
        for needle in needles:
            self.assertNotIn(needle, text, "the README holds a forbidden path fragment")
        absolute = re.compile(r"(?<![\w.<>~-])/(?:usr|bin|sbin|etc|opt|var|tmp|private|Users|home|Volumes|Library|root)\b")
        self.assertIsNone(absolute.search(text), "the README holds an absolute path")

    def test_the_readme_holds_no_email_address(self) -> None:
        self.assertIsNone(re.search(r"[A-Za-z0-9._+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", read_readme()), "an email address appears")

    def test_the_readme_does_not_contain_this_machines_host_name(self) -> None:
        name = socket.gethostname().split(".")[0].lower()
        if len(name) < 6 or name in ("localhost", "localdomain"):
            self.skipTest("the host name is too short or generic to scan for")
        self.assertFalse(name in read_readme().lower(), "the README contains the machine's host name")

    def test_the_gitignore_keeps_bytecode_out(self) -> None:
        with open(GITIGNORE, "r", encoding="utf-8") as handle:
            lines = [line.strip() for line in handle.read().splitlines()]
        self.assertIn("__pycache__/", lines)
        self.assertIn("*.pyc", lines)

    def test_no_log_or_bytecode_file_sits_under_the_folder(self) -> None:
        bad = []
        for dirpath, dirnames, filenames in os.walk(HARNESS_DIR):
            in_cache = os.path.basename(dirpath) == "__pycache__"
            for name in filenames:
                if name.endswith(".log") or (name.endswith(".pyc") and not in_cache):
                    bad.append(name)
        self.assertEqual(bad, [], "files with a forbidden suffix: %s" % ", ".join(sorted(bad)))


if __name__ == "__main__":
    unittest.main()
