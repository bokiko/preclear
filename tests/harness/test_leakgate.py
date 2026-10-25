"""Tests for pc_leakgate: the fail-closed leak scanner (EVID-03; D-14, D-16).

Every leak-shaped string comes from pc_seeds, assembled at run time. Assertions are boolean
checks with fixed messages so a failure never prints a seeded value. Scratch directories come
from tempfile.mkdtemp under the system temp directory; the tests never delete them and never
print their paths.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
GATE_CLI = os.path.join(HARNESS_DIR, "pc_leakgate.py")
GITLEAKS_TOML = os.path.join(REPO_ROOT, ".gitleaks.toml")

import pc_exitcodes  # noqa: E402  (the harness folder is on sys.path via discovery)
import pc_leakgate  # noqa: E402
import pc_seeds  # noqa: E402

SYNTHETIC_USER = "pcseedtester"


def run_gate(*args):
    """Run the gate CLI the way a stranger would: python3 -E -s -B script args."""
    return subprocess.run(
        [sys.executable, "-E", "-s", "-B", GATE_CLI] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def filler(size):
    """Leak-free, realistic text of exactly SIZE bytes: short words and line breaks."""
    unit = b"lorem ipsum dolor sit amet\n"
    return (unit * (size // len(unit) + 1))[:size]


def make_stage(files):
    """Create a fresh temporary directory holding FILES (name -> bytes) and return it."""
    root = tempfile.mkdtemp(prefix="preclear-lg-")
    for name, data in files.items():
        path = os.path.join(root, name)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "xb") as handle:
            handle.write(data)
    return root


class HarnessTestCase(unittest.TestCase):
    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)


class TracerTests(HarnessTestCase):
    def test_a_seeded_home_path_is_refused_by_scan_tree(self):
        seed = pc_seeds.home_path(SYNTHETIC_USER)
        stage = make_stage({"f.txt": ("x " + seed + "\n").encode("utf-8")})
        report = pc_leakgate.scan_tree(stage, [])
        rules = [finding.rule for finding in report.findings]
        self.ok("home-path-unix" in rules, "the home path rule fired")
        self.ok(all(finding.label == b"f.txt" for finding in report.findings), "findings carry the file label")

    def test_the_cli_refuses_a_seeded_stage_with_exit_14_and_prints_no_value(self):
        seed = pc_seeds.home_path(SYNTHETIC_USER)
        stage = make_stage({"f.txt": ("x " + seed + "\n").encode("utf-8")})
        result = run_gate("scan", stage)
        self.ok(result.returncode == pc_exitcodes.LEAK_REFUSED, "exit 14 on a seeded leak")
        output = result.stdout + result.stderr
        self.ok(b"f.txt" in output, "the file label is named")
        self.ok(b"1 match" in output, "a count is printed")
        self.ok(SYNTHETIC_USER.encode("ascii") not in output, "the seeded name is not echoed")
        self.ok(seed.encode("utf-8") not in output, "the seeded path is not echoed")
        self.ok(stage.encode("utf-8") not in output, "the stage path is not echoed")

    def test_a_clean_tree_passes_with_exit_0(self):
        stage = make_stage({"a.txt": b"nothing to see here\n", "sub/b.txt": b"still clean\n"})
        result = run_gate("scan", stage)
        self.ok(result.returncode == 0, "exit 0 on a clean tree")

    def test_scanning_zero_files_is_a_refusal(self):
        stage = tempfile.mkdtemp(prefix="preclear-lg-")
        result = run_gate("scan", stage)
        self.ok(result.returncode == pc_exitcodes.LEAK_REFUSED, "an empty directory is refused with exit 14")
        self.ok(b"no files to scan" in result.stdout + result.stderr, "the refusal says why")

    def test_a_missing_command_or_path_is_a_usage_error(self):
        self.ok(run_gate("scan").returncode == pc_exitcodes.USAGE, "scan with no path is a usage error")
        self.ok(run_gate().returncode == pc_exitcodes.USAGE, "no command is a usage error")


def read_toml(path):
    """A small line reader for exactly the shapes .gitleaks.toml uses (no TOML parser, D-11).

    Returns {"rules": [dict, ...], "allowlists": [dict, ...]}. Shapes handled: key = "string",
    key = 'literal triple-quoted string', key = integer, key = [list on one line] and a list
    spread over several lines that ends with a line holding only a closing bracket.
    """
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    blocks = {"rules": [], "allowlists": []}
    current = None
    pending = None

    def parse_value(text):
        text = text.strip()
        if text.startswith("["):
            found = re.findall(r"'''(.*?)'''|\"([^\"]*)\"", text, re.S)
            return [first if first != "" else second for first, second in found]
        if text.startswith("'''"):
            return re.match(r"^'''(.*)'''$", text, re.S).group(1)
        if text.startswith('"'):
            return text[1:-1]
        return int(text)

    for line in lines:
        stripped = line.strip()
        if pending is not None:
            pending[1].append(line)
            if stripped.startswith("]"):
                current[pending[0]] = parse_value("\n".join(pending[1]))
                pending = None
            continue
        if stripped == "[[rules]]":
            current = {}
            blocks["rules"].append(current)
            continue
        if stripped == "[[allowlists]]":
            current = {}
            blocks["allowlists"].append(current)
            continue
        if stripped.startswith("["):
            current = None
            continue
        if current is None or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if value == "[":
            pending = (key, [value])
            continue
        current[key] = parse_value(value)
    return blocks


class ParityTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.toml = read_toml(GITLEAKS_TOML)

    def test_the_reader_finds_six_identifier_rules_and_two_allowlists(self):
        self.ok(len(self.toml["rules"]) == 6, "six rules in the TOML")
        self.ok(len(self.toml["allowlists"]) == 2, "two allowlists in the TOML")
        self.ok(len(pc_leakgate.RULES) == 6, "six rules in Python")
        self.ok(len(pc_leakgate.ALLOWLISTS) == 2, "two allowlists in Python")

    def test_every_rule_has_the_same_id_regex_and_secret_group(self):
        python = dict((rule.id, rule) for rule in pc_leakgate.RULES)
        self.ok(sorted(python) == sorted(rule["id"] for rule in self.toml["rules"]), "the same rule ids")
        for rule in self.toml["rules"]:
            mirrored = python[rule["id"]]
            self.ok(mirrored.pattern == rule["regex"], "regex of " + rule["id"] + " is byte-identical")
            self.ok(mirrored.secret_group == rule.get("secretGroup"), "secretGroup of " + rule["id"] + " is identical")

    def test_every_allowlist_has_the_same_fields(self):
        for toml, python in zip(self.toml["allowlists"], pc_leakgate.ALLOWLISTS):
            self.ok(python.description == toml["description"], "allowlist description")
            self.ok(python.condition == toml.get("condition", "OR"), "allowlist condition")
            self.ok(list(python.target_rules) == toml["targetRules"], "allowlist target rules")
            self.ok(list(python.paths) == toml.get("paths", []), "allowlist paths")
            self.ok(list(python.regexes) == toml.get("regexes", []), "allowlist regexes")
            self.ok(python.regex_target == toml["regexTarget"], "allowlist regex target")

    def test_the_extra_python_rules_are_exactly_the_named_set(self):
        ids = set(rule.id for rule in pc_leakgate.PYTHON_ONLY_RULES)
        self.ok(ids == set(["home-path-root", "home-path-windows"]), "the two Python-only rules")
        toml_ids = set(rule["id"] for rule in self.toml["rules"])
        self.ok(not (ids & toml_ids), "no overlap with the TOML rules")

    def test_no_rule_matches_its_own_source_text(self):
        for rule in pc_leakgate.RULES + pc_leakgate.PYTHON_ONLY_RULES + pc_leakgate.CREDENTIAL_RULES:
            self.ok(rule.regex.search(rule.pattern) is None, "rule " + rule.id + " does not match itself")

    def test_the_credential_list_is_a_documented_subset(self):
        ids = set(rule.id for rule in pc_leakgate.CREDENTIAL_RULES)
        expected = set(["aws-access-key", "github-token", "anthropic-key", "private-key-header", "bearer-token"])
        self.ok(ids == expected, "the credential shapes")
        self.ok("credential" in (pc_leakgate.__doc__ or "").lower(), "the module documents the limit")

    def test_the_harness_sources_pass_their_own_gate(self):
        for name in sorted(os.listdir(HARNESS_DIR)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(HARNESS_DIR, name), "rb") as handle:
                data = handle.read()
            self.ok(pc_leakgate.scan_bytes("tests/harness/" + name, data, []) == [], name + " is clean under the Python gate")


SEED_RULES = (
    ("home path", lambda: pc_seeds.home_path(SYNTHETIC_USER), "home-path-unix"),
    ("linux home path", lambda: pc_seeds.home_path_linux(SYNTHETIC_USER), "home-path-unix"),
    ("dash slug", lambda: pc_seeds.dash_slug(SYNTHETIC_USER) + "proj", "home-path-dash-slug"),
    ("temp root", pc_seeds.mac_temp_root, "mac-temp-root"),
    ("private address", pc_seeds.private_ipv4, "private-ipv4"),
    ("shared address", pc_seeds.cgnat_ipv4, "private-ipv4"),
    ("internal host", lambda: pc_seeds.internal_host("pcbox"), "internal-hostname"),
    ("email", lambda: pc_seeds.email("someone", "corp.invalid"), "email-address"),
    ("aws key", pc_seeds.aws_key, "aws-access-key"),
    ("github token", pc_seeds.github_token, "github-token"),
    ("anthropic key", pc_seeds.anthropic_key, "anthropic-key"),
    ("private key header", pc_seeds.private_key_header, "private-key-header"),
    ("windows home", lambda: pc_seeds.windows_home(SYNTHETIC_USER), "home-path-windows"),
    ("root home", pc_seeds.root_home, "home-path-root"),
    ("bearer token", pc_seeds.bearer_token, "bearer-token"),
)


class SeedTests(HarnessTestCase):
    def test_every_seed_is_found_exactly_once_under_its_own_rule(self):
        for label, make, rule in SEED_RULES:
            data = ("x " + make() + "\n").encode("utf-8")
            self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [(rule, 1)], label + " is found once as " + rule)

    def test_the_public_address_is_allowed_only_in_a_planning_document(self):
        data = (pc_seeds.email("bokiko", "gmail.com") + "\n").encode("utf-8")
        found = [(rule, 1) for rule in ("email-address",)]
        self.ok(pc_leakgate.scan_bytes(".planning/notes.md", data, []) == [], "allowed in a planning document")
        self.ok(pc_leakgate.scan_bytes("x/.planning/a/b.md", data, []) == [], "allowed in a nested planning document")
        self.ok(pc_leakgate.scan_bytes("notes/n.md", data, []) == found, "refused elsewhere")
        self.ok(pc_leakgate.scan_bytes(".planning/notes.txt", data, []) == found, "refused in a planning file that is not markdown")
        other = (pc_seeds.email("someone", "gmail.com") + "\n").encode("utf-8")
        self.ok(pc_leakgate.scan_bytes(".planning/notes.md", other, []) == found, "another address is refused even there")

    def test_reserved_domains_and_role_addresses_are_allowed(self):
        for local, domain in (("a", "example.org"), ("b", "sub.example.com"), ("noreply", "anthropic.com"), ("SUPPORT", "anthropic.com"), ("id", "users.noreply.github.com")):
            data = (pc_seeds.email(local, domain) + "\n").encode("utf-8")
            self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [], "allowed: " + domain)
        data = (pc_seeds.email("other", "anthropic.com") + "\n").encode("utf-8")
        self.ok(len(pc_leakgate.scan_bytes("f.txt", data, [])) == 1, "another address at that domain is refused")

    def test_a_deny_entry_is_found_case_insensitively_and_counted(self):
        data = b"one PCDENYWORD two pcdenyword three\n"
        self.ok(pc_leakgate.scan_bytes("f.txt", data, ["pcDenyWord"]) == [("deny-list", 2)], "two deny hits")
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [], "no entries, no hits")


class EdgeCaseTests(HarnessTestCase):
    def seed(self):
        return pc_seeds.home_path(SYNTHETIC_USER)

    def test_a_leak_at_offset_zero_is_found(self):
        data = (self.seed() + " tail\n").encode("utf-8")
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("home-path-unix", 1)], "offset 0")

    def test_a_leak_at_the_end_without_a_trailing_newline_is_found(self):
        data = ("tail " + self.seed()).encode("utf-8")
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("home-path-unix", 1)], "end of file")

    def test_a_leak_across_every_plausible_chunk_boundary_is_found(self):
        seed = self.seed().encode("utf-8")
        for size in (4096, 8192, 65536, 1024 * 1024, 2 * 1024 * 1024):
            for back in (1, 3, len(seed) - 1):
                data = filler(size - back) + seed + b" " + filler(100)
                self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("home-path-unix", 1)], "boundary at %d" % size)

    def test_a_file_of_exactly_the_size_cap_is_scanned_and_one_byte_more_is_refused(self):
        cap = pc_leakgate.MAX_FILE_BYTES
        self.ok(cap == 5 * 1024 * 1024, "the cap is 5 MiB")
        self.ok(pc_leakgate.scan_bytes("f.txt", filler(cap), []) == [], "exactly the cap passes")
        self.ok(pc_leakgate.scan_bytes("f.txt", filler(cap + 1), []) == [("refused-oversize", 1)], "one byte over is refused")
        stage = make_stage({"big.txt": filler(cap + 1), "ok.txt": filler(cap)})
        report = pc_leakgate.scan_tree(stage, [])
        self.ok([(f.label, f.rule) for f in report.findings] == [(b"big.txt", "refused-oversize")], "on disk: one over is refused, exactly the cap is not")

    def test_a_leak_past_the_cap_is_a_refusal_not_a_skip(self):
        data = filler(pc_leakgate.MAX_FILE_BYTES) + self.seed().encode("utf-8")
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("refused-oversize", 1)], "oversize wins")

    def test_a_run_longer_than_the_limit_is_refused_instead_of_stalling_the_scan(self):
        limit = pc_leakgate.MAX_RUN
        self.ok(limit == 1024, "the run limit is 1024 characters")
        self.ok(pc_leakgate.scan_bytes("f.txt", b"a" * limit, []) == [], "a run of exactly the limit is scanned")
        self.ok(pc_leakgate.scan_bytes("f.txt", b"a" * (limit + 1), []) == [("refused-longrun", 1)], "one more is refused")

    def test_a_whole_file_of_one_run_is_refused_quickly(self):
        # Against a scanner without the run limit this input does not finish: the e-mail rule
        # backtracks over the run from every start position.
        started = time.monotonic()
        data = b"a" * pc_leakgate.MAX_FILE_BYTES
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("refused-longrun", 1)], "a whole file of one run is refused")
        self.ok(time.monotonic() - started < 30, "and quickly (a backtracking rule never saw the run)")

    def test_a_long_run_next_to_a_leak_still_reports_the_refusal(self):
        data = b"a" * 2000 + b" " + self.seed().encode("utf-8") + b"\n"
        self.ok(pc_leakgate.scan_bytes("f.txt", data, []) == [("refused-longrun", 1)], "refusal, never a pass")

    def test_nul_and_undecodable_bytes_are_refusals_with_their_own_ids(self):
        self.ok(pc_leakgate.scan_bytes("f.txt", b"abc\x00def", []) == [("refused-binary", 1)], "NUL byte")
        self.ok(pc_leakgate.scan_bytes("f.txt", b"abc \xff\xfe def", []) == [("refused-undecodable", 1)], "invalid UTF-8")

    def test_a_symlink_and_a_special_file_are_refusals_never_followed(self):
        outside = make_stage({"secret.txt": (self.seed() + "\n").encode("utf-8")})
        stage = make_stage({"plain.txt": b"fine\n"})
        os.symlink(os.path.join(outside, "secret.txt"), os.path.join(stage, "link.txt"))
        os.mkfifo(os.path.join(stage, "pipe.fifo"))
        report = pc_leakgate.scan_tree(stage, [])
        found = sorted((f.label, f.rule) for f in report.findings)
        self.ok(found == [(b"link.txt", "refused-symlink"), (b"pipe.fifo", "refused-special")], "own rule ids, content never read")

    def test_a_symlinked_directory_is_a_refusal(self):
        outside = make_stage({"a.txt": b"x\n"})
        stage = make_stage({"plain.txt": b"fine\n"})
        os.symlink(outside, os.path.join(stage, "dirlink"))
        report = pc_leakgate.scan_tree(stage, [])
        self.ok([(f.label, f.rule) for f in report.findings] == [(b"dirlink", "refused-symlink")], "the link is refused, not walked")

    def test_an_empty_file_passes_and_zero_files_do_not(self):
        report = pc_leakgate.scan_tree(make_stage({"empty.txt": b""}), [])
        self.ok(report.findings == [] and report.files == 1, "an empty file passes with zero findings")
        empty = pc_leakgate.scan_tree(tempfile.mkdtemp(prefix="preclear-lg-"), [])
        self.ok(empty.files == 0, "zero files are reported as zero")
        self.ok(run_gate("scan", tempfile.mkdtemp(prefix="preclear-lg-")).returncode == pc_exitcodes.LEAK_REFUSED, "and the CLI refuses")

    def test_a_single_file_argument_is_scanned(self):
        stage = make_stage({"one.txt": (self.seed() + "\n").encode("utf-8")})
        result = run_gate("scan", os.path.join(stage, "one.txt"))
        self.ok(result.returncode == pc_exitcodes.LEAK_REFUSED, "a file path works too")

    def test_several_paths_keep_their_findings_apart(self):
        leak = make_stage({"f.txt": (self.seed() + "\n").encode("utf-8")})
        clean = make_stage({"f.txt": b"fine\n"})
        result = run_gate("scan", clean, leak)
        self.ok(result.returncode == pc_exitcodes.LEAK_REFUSED, "refused")
        self.ok(b"2/f.txt" in result.stderr and b"1/f.txt" not in result.stderr, "labels carry the argument number")


class FailClosedTests(HarnessTestCase):
    class Boom(object):
        def finditer(self, text):
            raise RuntimeError("planted failure")

    def run_main(self, args):
        err = io.StringIO()
        out = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = pc_leakgate.main(args)
        return code, out.getvalue() + err.getvalue()

    def test_an_exception_inside_a_rule_is_scanner_error_exit_15(self):
        boom = pc_leakgate.Rule("boom", "x", None, self.Boom())
        stage = make_stage({"f.txt": b"fine\n"})
        with mock.patch.object(pc_leakgate, "RULES", (boom,)):
            with self.assertRaises(pc_leakgate.ScannerError) as caught:
                pc_leakgate.scan_bytes("f.txt", b"fine\n", [])
            self.ok(str(caught.exception) == "scanner error", "the message is fixed text")
            code, text = self.run_main(["scan", stage])
        self.ok(code == pc_exitcodes.SCANNER_ERROR, "exit 15")
        self.ok("planted" not in text, "no detail text")

    def test_zero_rules_is_scanner_error_never_a_clean_result(self):
        stage = make_stage({"f.txt": b""})
        with mock.patch.object(pc_leakgate, "RULES", ()):
            with mock.patch.object(pc_leakgate, "PYTHON_ONLY_RULES", ()):
                with mock.patch.object(pc_leakgate, "CREDENTIAL_RULES", ()):
                    with self.assertRaises(pc_leakgate.ScannerError):
                        pc_leakgate.scan_bytes("f.txt", b"", [])
                    with self.assertRaises(pc_leakgate.ScannerError):
                        pc_leakgate.scan_tree(stage, [])
                    code, _text = self.run_main(["scan", stage])
        self.ok(code == pc_exitcodes.SCANNER_ERROR, "exit 15 with an empty rule set")

    def test_a_rule_that_does_not_compile_is_refused_at_construction(self):
        with self.assertRaises(pc_leakgate.ScannerError):
            pc_leakgate.make_rule("bad", "(unclosed")
        with self.assertRaises(pc_leakgate.ScannerError):
            pc_leakgate.make_rule("", "fine")

    def test_an_unreadable_deny_file_is_exit_15_from_the_cli(self):
        stage = make_stage({"f.txt": b"fine\n"})
        undecodable = os.path.join(make_stage({"d.txt": b"\xff\xfe\xfa\n"}), "d.txt")
        result = run_gate("--deny-file", undecodable, "scan", stage)
        self.ok(result.returncode == pc_exitcodes.SCANNER_ERROR, "an undecodable deny file is exit 15")
        folder = tempfile.mkdtemp(prefix="preclear-lg-")
        result = run_gate("--deny-file", folder, "scan", stage)
        self.ok(result.returncode == pc_exitcodes.SCANNER_ERROR, "a deny file that cannot be read is exit 15")
        self.ok(b"fine" not in result.stdout + result.stderr, "no content is echoed")

    def test_a_missing_input_is_exit_15(self):
        folder = tempfile.mkdtemp(prefix="preclear-lg-")
        result = run_gate("scan", os.path.join(folder, "no-such-entry"))
        self.ok(result.returncode == pc_exitcodes.SCANNER_ERROR, "unreadable input is exit 15")

    def test_a_deny_entry_that_is_not_text_is_scanner_error(self):
        with self.assertRaises(pc_leakgate.ScannerError):
            pc_leakgate.scan_bytes("f.txt", b"x", [b"bytes"])


class DenyEntryTests(HarnessTestCase):
    def write(self, data):
        folder = tempfile.mkdtemp(prefix="preclear-dn-")
        path = os.path.join(folder, "deny.txt")
        with open(path, "xb") as handle:
            handle.write(data)
        return path

    def test_host_entries_keep_six_or_more_characters_and_drop_generic_names(self):
        kept = pc_leakgate.host_entries(["short", "sixsix", "LocalHost", "workstation", "mac-mini", "plainbox1", "  padded1  "])
        self.ok(kept == ["padded1", "plainbox1", "sixsix"], "floors and generic names")

    def test_local_file_entries_skip_comments_blanks_and_short_lines(self):
        path = self.write(b"# note\n\n   \nabc\nkeep-me\r\nsecond entry\n")
        self.ok(pc_leakgate.local_file_entries(REPO_ROOT, path) == ["keep-me", "second entry"], "usable entries only")

    def test_an_absent_deny_file_means_no_entries_and_an_unreadable_one_raises(self):
        folder = tempfile.mkdtemp(prefix="preclear-dn-")
        self.ok(pc_leakgate.local_file_entries(REPO_ROOT, os.path.join(folder, "none.txt")) == [], "absent: no entries")
        with self.assertRaises(pc_leakgate.ScannerError) as caught:
            pc_leakgate.local_file_entries(REPO_ROOT, folder)
        self.ok(str(folder) not in str(caught.exception), "the message holds no path")
        with self.assertRaises(pc_leakgate.ScannerError):
            pc_leakgate.local_file_entries(REPO_ROOT, self.write(b"\xff\xfe"))

    def test_build_deny_entries_is_the_sorted_unique_union(self):
        path = self.write(b"zeta-entry\nalpha-entry\nsixsix\n")
        built = pc_leakgate.build_deny_entries(REPO_ROOT, ["sixsix", "tiny"], path)
        self.ok(built == ["alpha-entry", "sixsix", "zeta-entry"], "sorted unique union")


class OutputShapeTests(HarnessTestCase):
    def test_findings_are_sorted_and_hold_counts_and_labels_only(self):
        home = pc_seeds.home_path(SYNTHETIC_USER)
        ip = pc_seeds.private_ipv4()
        slug_name = pc_seeds.dash_slug(SYNTHETIC_USER) + "x.txt"
        stage = make_stage(
            {
                "b.txt": (home + " " + ip + " " + home + "\n").encode("utf-8"),
                "a.txt": (ip + "\n").encode("utf-8"),
                slug_name: b"clean content\n",
                "pcdenyword-note.txt": b"clean content\n",
            }
        )
        report = pc_leakgate.scan_tree(stage, ["pcdenyword"])
        order = [(f.label, f.rule) for f in report.findings]
        self.ok(order == sorted(order), "sorted by label bytes then rule id")
        self.ok(order == [
            (b"(file name)", "deny-list"),
            (b"(file name)", "home-path-dash-slug"),
            (b"a.txt", "private-ipv4"),
            (b"b.txt", "home-path-unix"),
            (b"b.txt", "private-ipv4"),
        ], "the findings, with matching names labelled")
        counts = dict(((f.label, f.rule), f.count) for f in report.findings)
        self.ok(counts[(b"b.txt", "home-path-unix")] == 2, "two matches are counted as two")
        text = pc_leakgate.format_findings(report)
        lines = text.splitlines()
        self.ok(len(lines) == 5, "one line per finding")
        pattern = re.compile(r"^leak gate FAILED: .+ \(\d+ match\(es\), rule [a-z0-9-]+\)$")
        self.ok(all(pattern.match(line) for line in lines), "every line has the counted shape")
        for fragment in (SYNTHETIC_USER, "pcdenyword", ip, stage):
            self.ok(fragment not in text, "no value, entry or path in the output")

    def test_a_label_with_a_control_character_is_printed_safely(self):
        entry = pc_leakgate.Entry(b"bad\nname.txt", "symlink", None, 0)
        report = pc_leakgate.scan_entries([entry], [])
        text = pc_leakgate.format_findings(report)
        self.ok(len(text.splitlines()) == 1 and "\\n" in text, "a control character is escaped")

    def test_an_undecodable_name_is_a_labelled_refusal(self):
        entry = pc_leakgate.Entry(b"bad\xffname.txt", "file", b"fine\n", 0o644)
        report = pc_leakgate.scan_entries([entry], [])
        self.ok([(f.label, f.rule) for f in report.findings] == [(b"(file name)", "refused-undecodable")], "refused, never echoed")

    def test_the_cli_prints_counts_and_labels_only_for_a_name_hit(self):
        stage = make_stage({pc_seeds.dash_slug(SYNTHETIC_USER) + "x.txt": b"clean\n"})
        result = run_gate("scan", stage)
        output = result.stdout + result.stderr
        self.ok(result.returncode == pc_exitcodes.LEAK_REFUSED, "refused")
        self.ok(b"(file name)" in output and SYNTHETIC_USER.encode("ascii") not in output, "a matching name is labelled, not echoed")


if __name__ == "__main__":
    unittest.main()
