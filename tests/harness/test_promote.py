"""Tests for pc_promote: gate first, then exclusive creation into tests/evidence (EVID-03; D-16).

Every test works on a temporary directory standing in for the repository root, never on the
real tests/evidence. Seeds come from pc_seeds. Assertions use fixed messages so a failure never
prints a seeded value or a path. Scratch directories are never deleted by the tests.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
PROMOTE_CLI = os.path.join(HARNESS_DIR, "pc_promote.py")

import pc_exitcodes  # noqa: E402  (the harness folder is on sys.path via discovery)
import pc_promote  # noqa: E402
import pc_seeds  # noqa: E402

SYNTHETIC_USER = "pcseedtester"


def make_repo():
    """A temporary directory standing in for the repository root, holding an empty tests/evidence."""
    root = tempfile.mkdtemp(prefix="preclear-pr-")
    os.makedirs(os.path.join(root, "tests", "evidence"))
    return root


def make_stage(files):
    root = tempfile.mkdtemp(prefix="preclear-ps-")
    for name, data in files.items():
        path = os.path.join(root, name)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "xb") as handle:
            handle.write(data)
    return root


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-E", "-s", "-B", PROMOTE_CLI] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def tree_bytes(root):
    """Return {relative path: bytes} for every file under ROOT."""
    found = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, root)] = handle.read()
    return found


class HarnessTestCase(unittest.TestCase):
    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)


class TracerTests(HarnessTestCase):
    def test_a_seeded_stage_is_refused_with_exit_14_and_nothing_is_created(self):
        repo = make_repo()
        seed = pc_seeds.home_path(SYNTHETIC_USER)
        stage = make_stage({"f.txt": ("x " + seed + "\n").encode("utf-8")})
        dest = os.path.join(repo, "tests", "evidence", "dst")
        result = pc_promote.promote(stage, dest, repo, None, [])
        self.ok(result.code == pc_exitcodes.LEAK_REFUSED, "exit 14 on a seeded leak")
        self.ok(not os.path.lexists(dest), "no destination exists afterwards")
        text = result.message
        self.ok(SYNTHETIC_USER not in text and seed not in text, "the message holds no seeded value")

    def test_a_clean_stage_is_promoted_byte_for_byte(self):
        repo = make_repo()
        files = {"a.txt": b"alpha\n", "sub/b.bin": b"beta\x00no newline", "sub/deeper/c.txt": b""}
        stage = make_stage(files)
        dest = os.path.join(repo, "tests", "evidence", "dst")
        result = pc_promote.promote(stage, dest, repo, None, [])
        self.ok(result.code == 0, "exit 0 on a clean stage")
        self.ok(result.message == "promoted 3 file(s)", "one-line count message")
        self.ok(tree_bytes(dest) == files, "every file is byte-identical")

    def test_a_second_promote_to_the_same_destination_exits_17_and_changes_nothing(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"alpha\n"})
        dest = os.path.join(repo, "tests", "evidence", "dst")
        self.ok(pc_promote.promote(stage, dest, repo, None, []).code == 0, "first promote succeeds")
        before = tree_bytes(dest)
        other = make_stage({"a.txt": b"different\n", "z.txt": b"extra\n"})
        result = pc_promote.promote(other, dest, repo, None, [])
        self.ok(result.code == pc_exitcodes.PROMOTE_REFUSED, "second promote exits 17")
        self.ok(tree_bytes(dest) == before, "the destination is unchanged")

    def test_the_cli_exits_14_17_and_0_with_a_temporary_repo_root(self):
        repo = make_repo()
        leak = make_stage({"f.txt": ("x " + pc_seeds.home_path(SYNTHETIC_USER) + "\n").encode("utf-8")})
        clean = make_stage({"a.txt": b"alpha\n"})
        dest_leak = os.path.join(repo, "tests", "evidence", "leaky")
        dest_ok = os.path.join(repo, "tests", "evidence", "fine")
        refused = run_cli("--repo-root", repo, leak, dest_leak)
        self.ok(refused.returncode == pc_exitcodes.LEAK_REFUSED, "seeded stage exits 14")
        self.ok(SYNTHETIC_USER.encode("ascii") not in refused.stdout + refused.stderr, "no seeded value is printed")
        self.ok(not os.path.lexists(dest_leak), "no destination after a refusal")
        done = run_cli("--repo-root", repo, clean, dest_ok)
        self.ok(done.returncode == 0, "clean stage exits 0")
        again = run_cli("--repo-root", repo, clean, dest_ok)
        self.ok(again.returncode == pc_exitcodes.PROMOTE_REFUSED, "second promote exits 17")

    def test_the_cli_usage_errors_exit_2(self):
        self.ok(run_cli().returncode == pc_exitcodes.USAGE, "no arguments is a usage error")


if __name__ == "__main__":
    unittest.main()
