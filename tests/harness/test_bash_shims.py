"""Hygiene tests for the bash entry points under tests/harness (HARN-14; D-10, D-13).

The shims must run under the bash 3.2 that macOS ships as /bin/bash. Every file in the folder
whose first line is a bash or sh shebang (today selftest and checkpoint-wrapper) is checked:

  * it is executable and passes bash -n;
  * a text scan finds none of the constructs bash 3.2 lacks (associative arrays, mapfile,
    readarray, case-conversion expansions, [[ -v, &>>, |&, coproc, wait -n, local -n,
    declare -g) and no line assigns an array;
  * shellcheck -s bash passes when shellcheck is on PATH (a stated skip otherwise).

The run test then executes the real selftest shim under /bin/bash with a tripwire claude in
the one directory that also holds links to python3 and git, and records the bash version it
ran under. It never fails merely because that version is not 3.2: a different bash proves the
syntax travels, not the floor. The forbidden-construct scan applies everywhere.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Dict, List, Pattern

import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
BASH = "/bin/bash"
SHIM = os.path.join(HARNESS_DIR, "selftest")
EXPECTED_SHIMS = ("checkpoint-wrapper", "selftest")
NESTED_PATTERN = "test_preflight.py"
BANNER = re.compile(r"^preclear harness self-test: 0 model calls; claude directories removed from PATH: (\d+)$", re.M)

_SHEBANG = re.compile(rb"^#!\s*(?:\S*/)?(?:env\s+)?(?:bash|sh)(?:\s|$)")

# One pattern per construct bash 3.2 lacks. Each is searched on every line of the shim.
FORBIDDEN: Dict[str, Pattern[str]] = {
    "associative array": re.compile(r"\b(?:declare|typeset|local)\s+-[A-Za-z]*A"),
    "mapfile": re.compile(r"\bmapfile\b"),
    "readarray": re.compile(r"\breadarray\b"),
    "case conversion expansion": re.compile(r"\$\{[!#]?[A-Za-z_0-9@*]+(?:\[[^\]]*\])?(?:,|\^)"),
    "[[ -v": re.compile(r"\[\[\s*!?\s*-v\s"),
    "&>>": re.compile(r"&>>"),
    "|&": re.compile(r"\|&"),
    "coproc": re.compile(r"\bcoproc\b"),
    "wait -n": re.compile(r"\bwait\s+-[A-Za-z]*n"),
    "local -n": re.compile(r"\blocal\s+-[A-Za-z]*n"),
    "declare -g": re.compile(r"\b(?:declare|typeset)\s+-[A-Za-z]*g"),
    "array assignment": re.compile(r"(?:^|[\s;&|(])[A-Za-z_][A-Za-z0-9_]*\+?=\("),
}

# A synthetic line per construct, to prove each pattern fires.
SYNTHETIC: Dict[str, str] = {
    "associative array": "declare -A table",
    "mapfile": "mapfile -t lines < input",
    "readarray": "readarray -t lines < input",
    "case conversion expansion": 'echo "${name,,}"',
    "[[ -v": '[[ -v name ]] && echo set',
    "&>>": "echo hi &>> out.log",
    "|&": "ls |& cat",
    "coproc": "coproc cat",
    "wait -n": "wait -n",
    "local -n": "local -n ref=name",
    "declare -g": "declare -g name=1",
    "array assignment": "items=(one two)",
}


def find_shims(folder: str) -> List[str]:
    """Return the names of the files directly in folder whose first line is a bash or sh shebang."""
    found = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as handle:
            first = handle.readline(200)
        if _SHEBANG.match(first):
            found.append(name)
    return found


def forbidden_constructs(text: str) -> List[str]:
    """Return the names of the forbidden constructs found in text, in table order."""
    found = []
    for name, pattern in FORBIDDEN.items():
        for line in text.splitlines():
            if pattern.search(line):
                found.append(name)
                break
    return found


def bash_version() -> str:
    result = subprocess.run(
        [BASH, "-c", "printf '%s' \"$BASH_VERSION\""],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
    )
    return result.stdout.strip()


class ShimDiscoveryTests(unittest.TestCase):
    def test_selftest_and_checkpoint_wrapper_are_found_by_their_shebang(self) -> None:
        found = find_shims(HARNESS_DIR)
        for expected in EXPECTED_SHIMS:
            self.assertIn(expected, found, "%s was not found by its shebang" % expected)

    def test_python_modules_are_not_taken_for_shims(self) -> None:
        self.assertFalse(any(name.endswith(".py") for name in find_shims(HARNESS_DIR)))


class ScannerTests(unittest.TestCase):
    def test_every_forbidden_construct_has_a_synthetic_case(self) -> None:
        self.assertEqual(sorted(SYNTHETIC), sorted(FORBIDDEN))

    def test_each_forbidden_construct_is_caught_in_a_synthetic_shim(self) -> None:
        for construct, line in SYNTHETIC.items():
            with self.subTest(construct=construct):
                text = "#!/bin/bash\n%s\n" % line
                self.assertIn(construct, forbidden_constructs(text), "the scan missed this construct")

    def test_a_clean_bash_3_2_shim_passes_the_scan(self) -> None:
        text = (
            "#!/bin/bash\n"
            "here=${0%/*}\n"
            'name=${PY// /}\n'
            'case "$1" in\n  a) x=$((1 + 2)) ;;\nesac\n'
            'out=$(printf "%s" "$1")\n'
            'echo "${out:-,}"\n'
            "wait\n"
        )
        self.assertEqual(forbidden_constructs(text), [])

    def test_a_synthetic_shim_is_also_caught_through_the_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\nmapfile -t x < y\n")
            self.assertEqual(find_shims(folder), ["bad"])
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(forbidden_constructs(handle.read()), ["mapfile"])


class ShimFileTests(unittest.TestCase):
    def _shims(self) -> List[str]:
        return [os.path.join(HARNESS_DIR, name) for name in find_shims(HARNESS_DIR)]

    def test_every_shim_is_executable(self) -> None:
        for path in self._shims():
            with self.subTest(shim=os.path.basename(path)):
                self.assertTrue(os.access(path, os.X_OK), "the shim is not executable")

    def test_every_shim_passes_bash_n(self) -> None:
        for path in self._shims():
            with self.subTest(shim=os.path.basename(path)):
                result = subprocess.run(
                    [BASH, "-n", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, "bash -n failed")

    def test_no_shim_uses_a_construct_bash_3_2_lacks(self) -> None:
        for path in self._shims():
            with self.subTest(shim=os.path.basename(path)):
                with open(path, "r", encoding="utf-8") as handle:
                    found = forbidden_constructs(handle.read())
                self.assertEqual(found, [], "forbidden constructs: %s" % ", ".join(found))

    def test_every_shim_passes_shellcheck_when_it_is_installed(self) -> None:
        tool = shutil.which("shellcheck")
        if tool is None:
            self.skipTest("shellcheck is not on PATH; the forbidden-construct scan and bash -n still ran")
        for path in self._shims():
            with self.subTest(shim=os.path.basename(path)):
                result = subprocess.run(
                    [tool, "-s", "bash", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, "shellcheck reported findings:\n%s" % result.stdout)


class ShimRunTests(unittest.TestCase):
    def test_selftest_runs_to_exit_0_under_bin_bash_beside_a_tripwire_claude(self) -> None:
        if not os.access(BASH, os.X_OK):
            self.skipTest("/bin/bash is not available")
        git = shutil.which("git")
        if git is None:
            self.skipTest("git is not available on this machine")
        version = bash_version()
        sys.stderr.write("bash version used for the shim run: %s\n" % version)
        with tempfile.TemporaryDirectory() as parent:
            shared = pc_testutil.make_shared_dir(os.path.join(parent, "shared"), sys.executable, git)
            env = pc_testutil.minimal_env([shared])
            env["PC_SELFTEST_PATTERN"] = NESTED_PATTERN
            result = subprocess.run(
                [BASH, SHIM],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=180,
                cwd=tempfile.gettempdir(),
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertRegex(result.stdout, BANNER)
            self.assertRegex(result.stdout, r"(?m)^OK")
            self.assertNotIn("Ran 0 tests", result.stdout)
            self.assertEqual(pc_testutil.read_tripwire(shared), [], "the tripwire claude was reached")
        self.assertRegex(version, r"^\d+\.\d+", "could not read the bash version")


if __name__ == "__main__":
    unittest.main()
