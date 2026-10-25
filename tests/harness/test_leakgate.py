"""Tests for pc_leakgate: the fail-closed leak scanner (EVID-03; D-14, D-16).

Every leak-shaped string comes from pc_seeds, assembled at run time. Assertions are boolean
checks with fixed messages so a failure never prints a seeded value. Scratch directories come
from tempfile.mkdtemp under the system temp directory; the tests never delete them and never
print their paths.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_CLI = os.path.join(HARNESS_DIR, "pc_leakgate.py")

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


if __name__ == "__main__":
    unittest.main()
