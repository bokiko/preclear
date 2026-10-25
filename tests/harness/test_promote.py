"""Tests for pc_promote: gate first, then exclusive creation into tests/evidence (EVID-03; D-16).

Every test works on a temporary directory standing in for the repository root, never on the
real tests/evidence. Seeds come from pc_seeds. Assertions use fixed messages so a failure never
prints a seeded value or a path. Scratch directories are never deleted by the tests.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
PROMOTE_CLI = os.path.join(HARNESS_DIR, "pc_promote.py")

import pc_exitcodes  # noqa: E402  (the harness folder is on sys.path via discovery)
import pc_leakgate  # noqa: E402
import pc_promote  # noqa: E402
import pc_runroot  # noqa: E402
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
        files = {"a.txt": b"alpha\n", "sub/b.bin": b"beta\r\n\xc3\xa9 no newline", "sub/deeper/c.txt": b""}
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


REFUSED = pc_exitcodes.PROMOTE_REFUSED


def evidence_of(repo):
    return os.path.join(repo, "tests", "evidence")


def snapshot(root):
    """Every entry under ROOT as (relative path, kind, bytes or link target), for before and after checks."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in sorted(dirnames) + sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                found.append((rel, "link", os.readlink(path)))
            elif os.path.isdir(path):
                found.append((rel, "dir", b""))
            else:
                with open(path, "rb") as handle:
                    found.append((rel, "file", handle.read()))
    return sorted(found)


class RefusalTests(HarnessTestCase):
    def setUp(self):
        self.repo = make_repo()
        self.stage = make_stage({"a.txt": b"alpha\n"})
        self.evidence = evidence_of(self.repo)

    def assert_refused(self, result, label):
        self.ok(result.code == REFUSED, label + ": exit 17")
        self.ok(self.repo not in result.message and self.stage not in result.message, label + ": the message holds no path")

    def test_a_destination_outside_the_evidence_folder(self):
        outside = os.path.join(self.repo, "tests", "elsewhere")
        self.assert_refused(pc_promote.promote(self.stage, outside, self.repo, None, []), "a sibling of the evidence folder")
        self.assert_refused(pc_promote.promote(self.stage, self.evidence, self.repo, None, []), "the evidence folder itself")
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.repo, "x"), self.repo, None, []), "the repository root")
        other = tempfile.mkdtemp(prefix="preclear-pr-")
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(other, "dst"), self.repo, None, []), "an unrelated folder")
        self.ok(not os.path.lexists(outside), "nothing was created outside")

    def test_an_existing_destination_is_left_alone(self):
        dest = os.path.join(self.evidence, "taken")
        os.mkdir(dest)
        with open(os.path.join(dest, "keep.txt"), "xb") as handle:
            handle.write(b"keep\n")
        before = snapshot(dest)
        self.assert_refused(pc_promote.promote(self.stage, dest, self.repo, None, []), "existing directory")
        file_dest = os.path.join(self.evidence, "taken-file")
        with open(file_dest, "xb") as handle:
            handle.write(b"x")
        self.assert_refused(pc_promote.promote(self.stage, file_dest, self.repo, None, []), "existing file")
        os.symlink("no-such-target", os.path.join(self.evidence, "dangling"))
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.evidence, "dangling"), self.repo, None, []), "dangling link")
        self.ok(snapshot(dest) == before, "the existing destination is unchanged")

    def test_a_dot_dot_segment_in_the_destination_or_the_stage(self):
        sneaky = os.path.join(self.evidence, "a", "..", "b")
        self.assert_refused(pc_promote.promote(self.stage, sneaky, self.repo, None, []), "dot-dot in the destination")
        escape = os.path.join(self.evidence, "..", "..", "..", "escaped")
        self.assert_refused(pc_promote.promote(self.stage, escape, self.repo, None, []), "dot-dot out of the repository")
        with_dots = os.path.join(self.stage, "..", os.path.basename(self.stage))
        self.assert_refused(pc_promote.promote(with_dots, os.path.join(self.evidence, "ok"), self.repo, None, []), "dot-dot in the stage")
        self.ok(not os.path.lexists(os.path.join(self.evidence, "b")), "nothing was created")

    def test_a_symlinked_parent_inside_the_evidence_folder(self):
        real = os.path.join(self.evidence, "real")
        os.mkdir(real)
        os.symlink(real, os.path.join(self.evidence, "via"))
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.evidence, "via", "new"), self.repo, None, []), "symlinked parent")
        self.ok(os.listdir(real) == [], "nothing was written through the link")

    def test_an_evidence_folder_that_is_itself_a_symlink(self):
        repo = tempfile.mkdtemp(prefix="preclear-pr-")
        target = tempfile.mkdtemp(prefix="preclear-pt-")
        os.makedirs(os.path.join(repo, "tests"))
        os.symlink(target, os.path.join(repo, "tests", "evidence"))
        result = pc_promote.promote(self.stage, os.path.join(repo, "tests", "evidence", "dst"), repo, None, [])
        self.ok(result.code == REFUSED, "exit 17")
        self.ok(os.listdir(target) == [], "nothing was created behind the link")

    def test_a_stage_that_is_a_symlink(self):
        link = os.path.join(tempfile.mkdtemp(prefix="preclear-pl-"), "stage-link")
        os.symlink(self.stage, link)
        self.assert_refused(pc_promote.promote(link, os.path.join(self.evidence, "dst"), self.repo, None, []), "symlinked stage")
        self.ok(not os.path.lexists(os.path.join(self.evidence, "dst")), "nothing was created")

    def test_a_stage_under_the_config_directory(self):
        config = tempfile.mkdtemp(prefix="preclear-cfg-")
        inside = os.path.join(config, "stage")
        os.mkdir(inside)
        with open(os.path.join(inside, "a.txt"), "xb") as handle:
            handle.write(b"alpha\n")
        self.assert_refused(pc_promote.promote(inside, os.path.join(self.evidence, "dst"), self.repo, config, []), "stage under the config directory")
        self.assert_refused(pc_promote.promote(config, os.path.join(self.evidence, "dst2"), self.repo, config, []), "the config directory itself")
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.evidence, "dst3"), self.repo, self.evidence, []), "destination under the config directory")
        self.ok(os.listdir(self.evidence) == [], "nothing was created")

    def test_the_default_config_directory_follows_the_harness_home_variable(self):
        home = tempfile.mkdtemp(prefix="preclear-hh-")
        inside = os.path.join(home, "claude-config", "stage")
        os.makedirs(inside)
        with open(os.path.join(inside, "a.txt"), "xb") as handle:
            handle.write(b"alpha\n")
        with mock.patch.dict(os.environ, {"PRECLEAR_HARNESS_HOME": home}):
            result = pc_promote.promote(inside, os.path.join(self.evidence, "dst"), self.repo, None, [])
        self.assert_refused(result, "stage under the default config directory")
        self.ok(os.listdir(os.path.join(home, "claude-config")) == ["stage"], "promote created nothing in the harness home")

    def test_a_destination_with_a_nul_is_refused_not_a_crash(self):
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.evidence, "a" + chr(0) + "b"), self.repo, None, []), "NUL in the destination")
        self.assert_refused(pc_promote.promote(self.stage + chr(0), os.path.join(self.evidence, "ok"), self.repo, None, []), "NUL in the stage")

    def test_an_empty_or_unreadable_or_missing_stage(self):
        empty = tempfile.mkdtemp(prefix="preclear-pe-")
        self.assert_refused(pc_promote.promote(empty, os.path.join(self.evidence, "e1"), self.repo, None, []), "empty stage")
        only_dirs = tempfile.mkdtemp(prefix="preclear-pe-")
        os.makedirs(os.path.join(only_dirs, "sub", "deeper"))
        self.assert_refused(pc_promote.promote(only_dirs, os.path.join(self.evidence, "e2"), self.repo, None, []), "stage with only directories")
        missing = os.path.join(empty, "nowhere")
        self.assert_refused(pc_promote.promote(missing, os.path.join(self.evidence, "e3"), self.repo, None, []), "missing stage")
        locked = tempfile.mkdtemp(prefix="preclear-pe-")
        with open(os.path.join(locked, "a.txt"), "xb") as handle:
            handle.write(b"alpha\n")
        os.chmod(locked, 0)
        try:
            if os.access(locked, os.R_OK):
                self.skipTest("this account can read a mode 0 directory (running as the superuser)")
            self.assert_refused(pc_promote.promote(locked, os.path.join(self.evidence, "e4"), self.repo, None, []), "unreadable stage")
        finally:
            os.chmod(locked, stat.S_IRWXU)
        self.ok(os.listdir(self.evidence) == [], "nothing was created")

    def test_a_stage_holding_a_symlink_or_special_file_is_a_gate_refusal(self):
        stage = make_stage({"a.txt": b"alpha\n"})
        os.symlink(os.path.join(stage, "a.txt"), os.path.join(stage, "link.txt"))
        result = pc_promote.promote(stage, os.path.join(self.evidence, "dst"), self.repo, None, [])
        self.ok(result.code == pc_exitcodes.LEAK_REFUSED, "exit 14")
        self.ok(not os.path.lexists(os.path.join(self.evidence, "dst")), "nothing was created")

    def test_a_refusal_does_not_stop_a_later_clean_promote(self):
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(self.repo, "nope"), self.repo, None, []), "first, a refusal")
        result = pc_promote.promote(self.stage, os.path.join(self.evidence, "dst"), self.repo, None, [])
        self.ok(result.code == 0 and result.message == "promoted 1 file(s)", "then a clean promote works")

    def test_intermediate_folders_are_created_and_a_file_in_the_way_is_refused(self):
        dest = os.path.join(self.evidence, "one", "two", "three")
        self.ok(pc_promote.promote(self.stage, dest, self.repo, None, []).code == 0, "missing levels are created")
        self.ok(tree_bytes(dest) == {"a.txt": b"alpha\n"}, "the files arrived")
        blocker = os.path.join(self.evidence, "blocker")
        with open(blocker, "xb") as handle:
            handle.write(b"x")
        self.assert_refused(pc_promote.promote(self.stage, os.path.join(blocker, "inside"), self.repo, None, []), "a file where a folder is needed")

    def test_the_stage_is_never_changed(self):
        stage = make_stage({"a.txt": b"alpha\n", "sub/b.txt": b"beta\n"})
        before = snapshot(stage)
        self.ok(pc_promote.promote(stage, os.path.join(self.evidence, "dst"), self.repo, None, []).code == 0, "promoted")
        self.ok(snapshot(stage) == before, "nothing in the stage was deleted, moved or changed")


class GateRefusalTests(HarnessTestCase):
    def test_a_refusal_leaves_no_partial_destination(self):
        repo = make_repo()
        leak = pc_seeds.home_path(SYNTHETIC_USER)
        stage = make_stage({"a-clean.txt": b"fine\n", "z-leak.txt": ("x " + leak + "\n").encode("utf-8"), "sub/ok.txt": b"fine\n"})
        result = pc_promote.promote(stage, os.path.join(evidence_of(repo), "dst"), repo, None, [])
        self.ok(result.code == pc_exitcodes.LEAK_REFUSED, "exit 14")
        self.ok(os.listdir(evidence_of(repo)) == [], "the evidence folder is still empty")
        self.ok("z-leak.txt" in result.report_text and SYNTHETIC_USER not in result.report_text, "labels and counts, no value")

    def test_a_leaking_destination_name_is_refused(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"fine\n"})
        dest = os.path.join(evidence_of(repo), pc_seeds.dash_slug(SYNTHETIC_USER) + "run")
        result = pc_promote.promote(stage, dest, repo, None, [])
        self.ok(result.code == pc_exitcodes.LEAK_REFUSED, "exit 14")
        self.ok(os.listdir(evidence_of(repo)) == [], "nothing was created")

    def test_a_deny_entry_in_a_file_is_refused(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"has pcdenyword inside\n"})
        result = pc_promote.promote(stage, os.path.join(evidence_of(repo), "dst"), repo, None, ["pcdenyword"])
        self.ok(result.code == pc_exitcodes.LEAK_REFUSED and "pcdenyword" not in result.message + result.report_text, "refused, entry not echoed")

    def test_a_scanner_error_is_exit_15_and_creates_nothing(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"fine\n"})
        with mock.patch.object(pc_leakgate, "scan_entries", side_effect=pc_leakgate.ScannerError("scanner error")):
            result = pc_promote.promote(stage, os.path.join(evidence_of(repo), "dst"), repo, None, [])
        self.ok(result.code == pc_exitcodes.SCANNER_ERROR, "exit 15")
        self.ok(os.listdir(evidence_of(repo)) == [], "nothing was created")

    def test_a_scanner_that_returns_nothing_usable_is_not_a_pass(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"fine\n"})
        with mock.patch.object(pc_leakgate, "RULES", ()):
            result = pc_promote.promote(stage, os.path.join(evidence_of(repo), "dst"), repo, None, [])
        self.ok(result.code == pc_exitcodes.SCANNER_ERROR, "zero rules is exit 15")
        self.ok(os.listdir(evidence_of(repo)) == [], "nothing was created")

    def test_an_unreadable_deny_file_is_exit_15_through_the_default_entries(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"fine\n"})
        with mock.patch.object(pc_leakgate, "build_deny_entries", side_effect=pc_leakgate.ScannerError("could not read the local deny list")):
            result = pc_promote.promote(stage, os.path.join(evidence_of(repo), "dst"), repo, None, None)
        self.ok(result.code == pc_exitcodes.SCANNER_ERROR, "exit 15")
        self.ok(os.listdir(evidence_of(repo)) == [], "nothing was created")


class ConcurrencyTests(HarnessTestCase):
    def test_content_changed_after_the_scan_cannot_reach_the_destination(self):
        repo = make_repo()
        original = b"clean original\n"
        stage = make_stage({"a.txt": original})
        real_scan = pc_leakgate.scan_entries

        def scan_then_tamper(entries, deny_entries):
            report = real_scan(entries, deny_entries)
            with open(os.path.join(stage, "a.txt"), "r+b") as handle:
                handle.write(("x " + pc_seeds.home_path(SYNTHETIC_USER) + "\n").encode("utf-8"))
            return report

        dest = os.path.join(evidence_of(repo), "dst")
        with mock.patch.object(pc_leakgate, "scan_entries", side_effect=scan_then_tamper):
            result = pc_promote.promote(stage, dest, repo, None, [])
        self.ok(result.code == 0, "the scanned bytes were promoted")
        self.ok(tree_bytes(dest) == {"a.txt": original}, "the written bytes are the scanned bytes, not the tampered file")

    def test_two_racing_promotes_give_exactly_one_success(self):
        repo = make_repo()
        files = dict(("f%02d.txt" % index, ("content %d\n" % index).encode("ascii") * 200) for index in range(40))
        stage = make_stage(files)
        dest = os.path.join(evidence_of(repo), "race")
        command = [sys.executable, "-E", "-s", "-B", PROMOTE_CLI, "--repo-root", repo, stage, dest]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        codes = sorted([first.wait(), second.wait()])
        first.stdout.close(), first.stderr.close(), second.stdout.close(), second.stderr.close()
        self.ok(codes == [0, REFUSED], "exactly one promote wins and the other exits 17")
        self.ok(tree_bytes(dest) == files, "the winner's copy is complete and byte-identical")


class PartialFailureTests(HarnessTestCase):
    def test_a_failure_while_writing_reports_a_partial_promote_and_deletes_nothing(self):
        repo = make_repo()
        stage = make_stage({"a.txt": b"alpha\n", "b.txt": b"beta\n"})
        dest = os.path.join(evidence_of(repo), "half", "way")
        real_write = pc_runroot.write_exclusive
        calls = []

        def fail_second(path, data, mode):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("planted failure")
            return real_write(path, data, mode)

        with mock.patch.object(pc_runroot, "write_exclusive", side_effect=fail_second):
            result = pc_promote.promote(stage, dest, repo, None, [])
        self.ok(result.code == REFUSED, "exit 17")
        self.ok(result.message == "partial promote in half/way", "the message names the destination relative to the evidence folder")
        self.ok(os.path.isdir(dest) and tree_bytes(dest) == {"a.txt": b"alpha\n"}, "what was written stays, nothing is deleted")
        self.ok("planted" not in result.message, "no detail text")


if __name__ == "__main__":
    unittest.main()
