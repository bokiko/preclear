"""Zero-token tests for filing a finished row into tests/evidence (plan 03-04; EVID-04, EVID-05, HARN-05, WR-14).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every folder
comes from RowRig or tempfile and is never deleted; the filing tests write into the temporary repository of the
rig and never into the real tests/evidence. pc_evidence is imported inside each test, so a missing module is one
error per test and not one load failure of the file. Assertion labels are fixed text, and leak-shaped values are
built at run time from fragments, so no source line holds one whole.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import unittest
from unittest import mock

import pc_exitcodes
import pc_leakgate
import pc_promote
import pc_sanitize
import pc_testutil

ROW1 = "row1-wrong-binding"
DEST_NAME = "rerun-2026-10-28-claude-sonnet-5-5"
VERDICT_LINE = "Reviewer verdict: PENDING"
SYNTHETIC_LOGIN = "pcsynth" + "login" + "zq"
RAW_SUFFIXES = (".stdout", ".stderr", ".raw", ".prompt", ".record.json", ".git.json")
RAW_NAMES = ("run.json", "hooklog.jsonl", "chain.json")


def evidence():
    import pc_evidence

    return pc_evidence


def row1():
    import pc_row1

    return pc_row1


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def fixed_clock() -> datetime.datetime:
    return datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)


def tree_bytes(root: str) -> dict:
    """Return {relative path: bytes} for every file under root."""
    found = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            with open(full, "rb") as handle:
                found[os.path.relpath(full, root)] = handle.read()
    return found


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


class World(object):
    """A rig and the outcome of the whole row run through the driver (the real path, filing included)."""

    def __init__(self, stages=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.code = matrix().main(
            ["--row", ROW1, "--claude", self.rig.claude, "--budget", "2.00"],
            env=dict(self.rig.env),
            repo_root=self.rig.repo,
            clock=fixed_clock,
            out=self.out,
            err=self.err,
        )

    @property
    def text(self) -> str:
        return self.out.getvalue() + self.err.getvalue()

    @property
    def evidence_dir(self) -> str:
        return os.path.join(self.rig.repo, "tests", "evidence")

    @property
    def destination(self) -> str:
        return os.path.join(self.evidence_dir, DEST_NAME)

    @property
    def row_dir(self) -> str:
        return os.path.join(self.destination, ROW1)


class Unfiled(object):
    """A rig whose row ran to the end with the filing refused by a stand-in, so the run root is complete and
    nothing is filed. The real filing is then called by the test."""

    def __init__(self, stages=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.ctx = self.rig.context()
        refusal = rows().RowOutcome(pc_exitcodes.PROMOTE_REFUSED, ("refused by the test stand-in",))
        with mock.patch.object(evidence(), "file_row", return_value=refusal):
            self.outcome = row1().run_row(self.ctx)

    @property
    def run_root(self) -> str:
        names = os.listdir(self.ctx.runs_root)
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    @property
    def destination(self) -> str:
        return self.ctx.destination

    def sanitizer(self, login: str = "") -> object:
        """A sanitizer built the way run_row builds one; with a login, one that knows only that synthetic login."""
        paths = row1().paths_for(self.run_root)
        mapping = row1().caller_map(paths, self.ctx.runs_root)
        if login:
            sources = pc_sanitize.Sources([], login, [], [self.rig.base], self.rig.repo)
            return pc_sanitize.Sanitizer.from_machine(self.rig.repo, mapping, sources=sources)
        return pc_sanitize.Sanitizer.from_machine(self.rig.repo, mapping)

    def file_context(self, sanitizer: object = None, proxy: object = None) -> object:
        san = sanitizer if sanitizer is not None else self.sanitizer()
        return self.ctx._replace(
            run_root=self.run_root, sanitizer=proxy if proxy is not None else san, deny_entries=san.deny_entries()
        )

    def file(self, sanitizer: object = None, proxy: object = None) -> object:
        return evidence().file_row(self.file_context(sanitizer, proxy), self.run_root)


class Bypass(object):
    """A sanitizer stand-in that leaves the bytes of one file alone (the ones that hold the marker)."""

    def __init__(self, inner: object, marker: str) -> None:
        self._inner = inner
        self._marker = marker.encode("utf-8")

    def sanitize_bytes(self, data: bytes) -> bytes:
        if self._marker in bytes(data):
            return bytes(data)
        return self._inner.sanitize_bytes(data)

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def append_bytes(path: str, data: bytes) -> None:
    with open(path, "ab") as handle:
        handle.write(data)


class FilingTests(unittest.TestCase):
    def test_the_whole_row_through_the_driver_files_a_new_dated_folder(self) -> None:
        world = World()
        self.assertEqual(world.code, 0, world.text)
        self.assertTrue(os.path.isdir(world.destination), "the evidence folder was created")
        self.assertTrue(os.path.isfile(os.path.join(world.destination, "README.md")), "the folder README is filed")
        self.assertTrue(os.path.isdir(world.row_dir), "the row folder is filed")
        for name in ("README.md", "usage.txt", "model-id.txt"):
            self.assertTrue(os.path.isfile(os.path.join(world.row_dir, name)), "row folder holds " + name)
        with open(os.path.join(world.row_dir, "README.md"), "rb") as handle:
            data = handle.read()
        self.assertTrue(data.endswith(("\n" + VERDICT_LINE + "\n").encode("utf-8")), "the README ends with the line")
        self.assertEqual(data.count(VERDICT_LINE.encode("utf-8")), 1, "the line occurs once")
        self.assertIn(DEST_NAME, world.text, "the printed outcome names the folder")
        self.assertRegex(world.text, r"row total: 0\.13", "the row total is printed as decimal text")

    def test_nothing_raw_is_staged_and_the_promoted_folder_scans_clean(self) -> None:
        world = World()
        self.assertEqual(world.code, 0, world.text)
        found = tree_bytes(world.destination)
        self.assertGreater(len(found), 3, "several files were filed")
        for relative, data in found.items():
            base = os.path.basename(relative)
            self.assertFalse(base.endswith(RAW_SUFFIXES), "no raw capture suffix is filed")
            self.assertNotIn(base, RAW_NAMES, "no raw record name is filed")
            self.assertNotIn(b"\x00", data, "no NUL byte in a filed file")
        deny = pc_leakgate.build_deny_entries(world.rig.repo, None, None)
        report = pc_leakgate.scan_tree(world.destination, deny)
        self.assertEqual(report.findings, [], "the promoted folder holds no finding")
        self.assertGreater(report.files, 3, "the scan saw the files")

    def test_a_second_filing_is_refused_with_17_and_changes_nothing(self) -> None:
        run = Unfiled()
        first = run.file()
        self.assertEqual(first.code, 0, "\n".join(first.lines))
        before = tree_bytes(run.destination)
        evidence_dir = os.path.dirname(run.destination)
        listing = sorted(os.listdir(evidence_dir))
        second = run.file()
        self.assertEqual(second.code, pc_exitcodes.PROMOTE_REFUSED, "\n".join(second.lines))
        self.assertEqual(tree_bytes(run.destination), before, "the first filing is unchanged")
        self.assertEqual(sorted(os.listdir(evidence_dir)), listing, "no second folder appeared")
        self.assertNotIn(run.rig.base, "\n".join(second.lines), "no folder in the text")

    def test_an_existing_destination_still_stops_the_row_before_any_ledger_line(self) -> None:
        rig = pc_testutil.RowRig()
        ctx = rig.context()
        os.makedirs(ctx.destination)
        outcome = row1().run_row(ctx)
        self.assertEqual(outcome.code, pc_exitcodes.PROMOTE_REFUSED, "\n".join(outcome.lines))
        import pc_spend

        self.assertEqual(pc_spend.read_records(ctx.harness_home), [], "no ledger line was written")
        self.assertEqual(rig.calls(), [], "no stage was launched")

    def test_a_seeded_breach_ends_with_11_and_creates_no_evidence_folder(self) -> None:
        stages = pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1)
        world = World(stages=stages)
        self.assertEqual(world.code, pc_exitcodes.PREFLIGHT_FAIL, world.text)
        created = [name for name in os.listdir(world.evidence_dir) if name != "publication-2026-10-20"]
        self.assertEqual(created, [], "nothing was created under tests/evidence")

    def test_a_sanitizer_error_on_a_staged_file_is_15_and_files_nothing(self) -> None:
        run = Unfiled()
        append_bytes(os.path.join(run.run_root, "snaps", "snap-1-after-work", "ledgers-ls.txt"), b"\xff\xfe")
        outcome = run.file()
        self.assertEqual(outcome.code, pc_exitcodes.SCANNER_ERROR, "\n".join(outcome.lines))
        self.assertFalse(os.path.lexists(run.destination), "no destination was created")
        self.assertNotIn(run.rig.base, "\n".join(outcome.lines), "no folder in the text")

    def test_stage_folders_are_exclusive_and_numbered_and_never_reused(self) -> None:
        run = Unfiled()
        self.assertEqual(run.file().code, 0, "the first filing succeeds")
        first_stage = os.path.join(run.run_root, "stage-1")
        self.assertTrue(os.path.isdir(first_stage), "the first filing used stage-1")
        kept = tree_bytes(first_stage)
        self.assertEqual(run.file().code, pc_exitcodes.PROMOTE_REFUSED, "the second filing is refused")
        self.assertTrue(os.path.isdir(os.path.join(run.run_root, "stage-2")), "the second attempt used stage-2")
        self.assertEqual(tree_bytes(first_stage), kept, "stage-1 was not touched")

    def test_the_staged_names_hold_no_raw_capture(self) -> None:
        run = Unfiled()
        self.assertEqual(run.file().code, 0, "filing succeeds")
        staged = tree_bytes(os.path.join(run.run_root, "stage-1"))
        for relative in staged:
            base = os.path.basename(relative)
            self.assertFalse(base.endswith(RAW_SUFFIXES), "no raw capture suffix is staged")
            self.assertNotIn(base, RAW_NAMES, "no raw record name is staged")
            self.assertNotEqual(base, "status.raw", "the NUL status capture is not staged")


class Wr14Tests(unittest.TestCase):
    def test_promote_receives_the_deny_entries_and_the_config_folder_of_the_context(self) -> None:
        run = Unfiled()
        san = run.sanitizer(SYNTHETIC_LOGIN)
        ctx = run.file_context(san)
        real = pc_promote.promote
        seen = []

        def spy(*args, **kwargs):
            seen.append(kwargs)
            return real(*args, **kwargs)

        with mock.patch.object(pc_promote, "promote", spy):
            outcome = evidence().file_row(ctx, run.run_root)
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        self.assertEqual(len(seen), 1, "promote was called once")
        self.assertEqual(seen[0].get("deny_entries"), san.deny_entries(), "the deny entries are the sanitizer's")
        self.assertTrue(seen[0].get("deny_entries"), "the deny entries are not empty")
        self.assertIn(SYNTHETIC_LOGIN, seen[0]["deny_entries"], "the synthetic login is among the entries")
        self.assertEqual(seen[0].get("config_dir"), ctx.config_dir, "the config folder is passed")

    def test_a_file_that_still_holds_the_login_is_refused_by_the_entries_and_accepted_without_them(self) -> None:
        run = Unfiled()
        san = run.sanitizer(SYNTHETIC_LOGIN)
        append_bytes(
            os.path.join(run.run_root, "snaps", "snap-1-after-work", "status.txt"),
            ("\nnote " + SYNTHETIC_LOGIN + "\n").encode("utf-8"),
        )
        outcome = run.file(sanitizer=san, proxy=Bypass(san, SYNTHETIC_LOGIN))
        self.assertEqual(outcome.code, pc_exitcodes.LEAK_REFUSED, "\n".join(outcome.lines))
        self.assertFalse(os.path.lexists(run.destination), "nothing was created")
        self.assertNotIn(SYNTHETIC_LOGIN, "\n".join(outcome.lines), "the login is never printed")
        self.assertNotIn(run.rig.base, "\n".join(outcome.lines), "no folder in the text")
        self.assertRegex("\n".join(outcome.lines), r"[0-9]+ finding", "counts are printed")
        staged = os.path.join(run.run_root, "stage-1")
        self.assertIn(
            SYNTHETIC_LOGIN.encode("utf-8"),
            tree_bytes(staged)[os.path.join("row1-wrong-binding", "snap-1-after-work", "status.txt")],
            "the staged file still holds the login",
        )
        control = os.path.join(run.rig.repo, "tests", "evidence", "negative-control")
        result = pc_promote.promote(staged, control, run.rig.repo, config_dir=run.ctx.config_dir, deny_entries=None)
        self.assertEqual(result.code, 0, "the same bytes without the entries are accepted: " + result.message)


if __name__ == "__main__":
    unittest.main()
