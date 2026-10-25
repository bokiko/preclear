"""Tests for pc_runroot: exclusive run-root allocation and exclusive creation helpers.

Scratch directories come from tempfile.mkdtemp under the system temp directory. The
tests never delete them and never print their paths (failure messages carry labels
only). Names that cannot be typed safely are built from code points at run time.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
RUNROOT_CLI = os.path.join(HARNESS_DIR, "pc_runroot.py")

import pc_runroot  # noqa: E402  (the harness folder is on sys.path via discovery)


def run_cli(*args):
    """Run the allocator CLI the way a stranger would: python3 -E -s -B script args."""
    return subprocess.run(
        [sys.executable, "-E", "-s", "-B", RUNROOT_CLI] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class HarnessTestCase(unittest.TestCase):
    """Shared helpers. Messages never include a path value."""

    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)

    @classmethod
    def fresh_parent(cls):
        # Never deleted, never printed (HARN-03: the harness removes nothing).
        return tempfile.mkdtemp(prefix="preclear-rr-")


class AllocateRunRootTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_first_allocation_creates_a_private_directory_and_returns_its_realpath(self):
        created = pc_runroot.allocate_run_root(self.parent, "run-first")
        expected = os.path.realpath(os.path.join(self.parent, "run-first"))
        self.ok(created == expected, "returned path is the realpath of the new directory")
        self.ok(os.path.isdir(created), "the run root exists as a directory")
        mode = stat.S_IMODE(os.stat(created).st_mode)
        self.ok(mode == 0o700, "the run root is owner-only (0o700)")

    def test_second_allocation_of_same_name_raises_collision(self):
        pc_runroot.allocate_run_root(self.parent, "run-twice")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "run-twice")

    def test_collision_is_a_run_root_error(self):
        self.ok(issubclass(pc_runroot.RunRootCollision, pc_runroot.RunRootError), "collision subclasses RunRootError")

    def test_existing_regular_file_is_a_collision_and_is_left_alone(self):
        path = os.path.join(self.parent, "taken-by-file")
        with open(path, "xb") as handle:
            handle.write(b"keep me")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "taken-by-file")
        with open(path, "rb") as handle:
            self.ok(handle.read() == b"keep me", "the existing file is untouched")

    def test_symlink_to_existing_directory_is_a_collision(self):
        target = os.path.join(self.parent, "link-target-dir")
        os.mkdir(target)
        os.symlink(target, os.path.join(self.parent, "link-to-dir"))
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "link-to-dir")

    def test_dangling_symlink_is_a_collision(self):
        os.symlink("no-such-target-anywhere", os.path.join(self.parent, "dangling"))
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "dangling")
        self.ok(os.path.islink(os.path.join(self.parent, "dangling")), "the dangling link is untouched")

    def test_parent_with_trailing_separator_reaches_the_same_entry(self):
        pc_runroot.allocate_run_root(self.parent, "run-trailing")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent + os.sep, "run-trailing")

    def test_symlinked_parent_resolves_to_the_existing_entry(self):
        real_parent = self.fresh_parent()
        pc_runroot.allocate_run_root(real_parent, "run-via-link")
        link_parent = os.path.join(self.parent, "parent-link")
        os.symlink(real_parent, link_parent)
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(link_parent, "run-via-link")

    def test_sibling_that_only_shares_a_name_prefix_is_allowed(self):
        pc_runroot.allocate_run_root(self.parent, "run-prefix")
        sibling = pc_runroot.allocate_run_root(self.parent, "run-prefix-2")
        shorter = pc_runroot.allocate_run_root(self.parent, "run-pre")
        self.ok(os.path.isdir(sibling) and os.path.isdir(shorter), "prefix siblings are created")

    def test_name_of_exactly_255_bytes_is_accepted(self):
        created = pc_runroot.allocate_run_root(self.parent, "n" * 255)
        self.ok(os.path.isdir(created), "a 255-byte name is a valid run root name")


class InvalidNameTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def assert_refused_before_creation(self, name, label):
        before = sorted(os.listdir(self.parent))
        with self.assertRaises(pc_runroot.RunRootError) as caught:
            pc_runroot.allocate_run_root(self.parent, name)
        self.ok(
            not isinstance(caught.exception, pc_runroot.RunRootCollision),
            label + ": refused as an invalid name, not as a collision",
        )
        self.ok(sorted(os.listdir(self.parent)) == before, label + ": nothing was created")

    def test_empty_name(self):
        self.assert_refused_before_creation("", "empty")

    def test_dot_and_dot_dot(self):
        self.assert_refused_before_creation(".", "dot")
        self.assert_refused_before_creation("..", "dot-dot")

    def test_names_holding_a_separator(self):
        self.assert_refused_before_creation("a" + os.sep + "b", "inner separator")
        self.assert_refused_before_creation("a" + os.sep, "trailing separator")
        self.assert_refused_before_creation(os.sep + "a", "leading separator")

    def test_name_holding_a_nul(self):
        self.assert_refused_before_creation("a" + chr(0) + "b", "NUL")

    def test_name_over_255_utf8_bytes(self):
        self.assert_refused_before_creation("n" * 256, "256 ASCII bytes")
        # 128 two-byte letters are 128 characters but 256 bytes.
        self.assert_refused_before_creation(chr(0xE9) * 128, "256 bytes in 128 characters")

    def test_name_that_cannot_be_encoded_as_utf8(self):
        self.assert_refused_before_creation("bad" + chr(0xDCFF), "lone surrogate")

    def test_missing_parent(self):
        missing = os.path.join(self.parent, "no-such-parent")
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.allocate_run_root(missing, "run-x")
        self.ok(not os.path.exists(missing), "the missing parent was not created")

    def test_parent_that_is_a_file(self):
        path = os.path.join(self.parent, "parent-is-a-file")
        with open(path, "xb"):
            pass
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.allocate_run_root(path, "run-x")


class ExclusiveHelperTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_exclusive_dir_creates_with_the_given_mode_and_refuses_a_second_call(self):
        path = os.path.join(self.parent, "dir-a")
        self.ok(pc_runroot.exclusive_dir(path, 0o700) is None, "exclusive_dir returns None")
        self.ok(os.path.isdir(path), "the directory exists")
        self.ok(stat.S_IMODE(os.stat(path).st_mode) == 0o700, "mode applied")
        with self.assertRaises(FileExistsError):
            pc_runroot.exclusive_dir(path, 0o700)

    def test_write_exclusive_writes_all_bytes_and_refuses_an_existing_file(self):
        path = os.path.join(self.parent, "file-a")
        payload = bytes(range(256)) * 300
        pc_runroot.write_exclusive(path, payload, 0o600)
        with open(path, "rb") as handle:
            self.ok(handle.read() == payload, "every byte was written")
        self.ok(stat.S_IMODE(os.stat(path).st_mode) == 0o600, "mode applied")
        with self.assertRaises(FileExistsError):
            pc_runroot.write_exclusive(path, b"other", 0o600)
        with open(path, "rb") as handle:
            self.ok(handle.read() == payload, "the existing file was not overwritten")

    def test_write_exclusive_refuses_a_dangling_symlink_and_does_not_follow_it(self):
        link = os.path.join(self.parent, "file-link")
        victim = os.path.join(self.parent, "file-link-victim")
        os.symlink(victim, link)
        with self.assertRaises(FileExistsError):
            pc_runroot.write_exclusive(link, b"data", 0o600)
        self.ok(not os.path.exists(victim), "the link target was not created through the link")


class CliTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_first_allocation_prints_the_path_and_exits_0(self):
        result = run_cli(self.parent, "cli-run-a")
        self.ok(result.returncode == 0, "first allocation exits 0")
        printed = result.stdout.decode("utf-8").strip()
        self.ok(printed == os.path.realpath(os.path.join(self.parent, "cli-run-a")), "stdout is the created realpath")
        self.ok(os.path.isdir(printed), "the printed directory exists")

    def test_second_allocation_of_the_same_name_exits_16(self):
        first = run_cli(self.parent, "cli-run-b")
        self.ok(first.returncode == 0, "first allocation exits 0")
        second = run_cli(self.parent, "cli-run-b")
        self.ok(second.returncode == 16, "collision exits 16")
        self.ok(b"run root collision" in second.stderr, "stderr names the collision")
        self.ok(second.stdout == b"", "nothing is printed to stdout on a collision")

    def test_invalid_name_and_missing_parent_and_bad_usage_exit_2(self):
        before = sorted(os.listdir(self.parent))
        self.ok(run_cli(self.parent, "..").returncode == 2, "dot-dot exits 2")
        self.ok(run_cli(self.parent, "a" + os.sep + "b").returncode == 2, "separator exits 2")
        self.ok(run_cli(self.parent, "a" + os.sep).returncode == 2, "trailing separator exits 2")
        self.ok(run_cli(os.path.join(self.parent, "nope"), "x").returncode == 2, "missing parent exits 2")
        self.ok(run_cli().returncode == 2, "no arguments exits 2")
        self.ok(run_cli(self.parent).returncode == 2, "one argument exits 2")
        self.ok(sorted(os.listdir(self.parent)) == before, "no run root was created by a refusal")


if __name__ == "__main__":
    unittest.main()
