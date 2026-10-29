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
        result = pc_promote.promote(
            staged, control, run.rig.repo, config_dir=run.ctx.config_dir, deny_entries=None, allow_default_deny=True
        )
        self.assertEqual(result.code, 0, "the same bytes without the entries are accepted: " + result.message)


# ---------------------------------------------------------------------------------------------
# Task 2: the full per-row file set
# ---------------------------------------------------------------------------------------------

COMMITTED_SET = (
    "README.md", "claude-version.txt", "digests.txt", "fixture-CLAUDE.md", "tools.txt", "measurements.md",
    "measurements.txt", "s1-work.out", "s1.err", "s1.exit", "s2-preclear-prompt.md", "s2-preclear-trace.md",
    "s2-preclear-full-trace.md", "s2-preclear.err", "s2-preclear.exit", "session.id", "status-before.txt",
    "lint-before.txt", "wrapper-calls.log", "wrapper-checkpoint.sh", "snap-0-setup", "snap-1-after-work",
    "snap-2-after-preclear",
)
NEW_SET = (
    "mechanical-checks.md", "usage.txt", "model-id.txt", "isolation-mode.txt", "harness-version.txt",
    "s1-work-prompt.md", "s1-work-full-trace.md", "settings.json",
)
S3_SET = (
    "s3-resume-trace.md", "s3-resume-full-trace.md", "s3-resume.err", "s3-resume.exit", "resume-line.txt",
    "session-resume.id", "snap-3-after-resume",
)
SNAPSHOT_SET = ("sha.txt", "manifest.jsonl", "status.txt", "ledgers-ls.txt", "bindings-ls.txt")
LEDGER_NAMES = ("CONTINUITY_CLAUDE-other-task.md", "CONTINUITY_CLAUDE-widget-export.md")
ASSERTION_IDS = (
    "permission-mode-default", "model-pinned", "skill-preclear-present", "mcp-servers-empty",
    "no-non-builtin-plugins", "user-names-absent", "no-user-instruction-outside-config",
    "project-claude-md-loaded", "project-local-inside-run-root", "memory-path-as-set", "cwd-is-project",
    "session-id-as-requested",
)
SECTION_NAMES = (
    "Init manifest", "Instruction audit", "Assertions", "Write boundary", "Git", "Helper calls", "Ledgers",
    "Sessions", "Denials", "Checkpoint bytes",
)
CHECKLIST_PREFIXES = (
    "helper calls", "ledger digests unchanged", "writes outside approved roots", "git mutations",
    "checkpoint bytes versus cap", "session ids per stage", "cost and turns per stage",
)
PUBLICATION_ROW = os.path.join("tests", "evidence", "publication-2026-10-20", "row1-wrong-binding")


def verdict_words() -> tuple:
    """The words no harness-authored file may hold, assembled from fragments at run time."""
    return (
        "pa" + "ss", "pa" + "ssed", "fa" + "il", "fa" + "iled", "fail" + "ure", "acc" + "ept", "acc" + "epted",
        "ver" + "dict",
    )


def verdict_pattern():
    import re

    return re.compile(r"\b(?:%s)\b" % "|".join(verdict_words()), re.IGNORECASE)


def with_result(stages: list, index: int, **changes) -> list:
    copied = json.loads(json.dumps(stages))
    copied[index]["result"].update(changes)
    return copied


def with_ops(stages: list, index: int, ops: list) -> list:
    copied = json.loads(json.dumps(stages))
    copied[index]["ops"] = list(copied[index].get("ops", [])) + json.loads(json.dumps(ops))
    return copied


def sha256_of(path: str) -> str:
    import hashlib

    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


_FILED = {}


def default_filed() -> "Filed":
    """One filed default run, built once and only read by the tests that use it."""
    if "default" not in _FILED:
        _FILED["default"] = Filed()
    return _FILED["default"]


class Filed(object):
    """An Unfiled world that has been filed once into its own temporary repository."""

    def __init__(self, stages=None, **config) -> None:
        self.run = Unfiled(stages=stages, **config)
        self.sanitizer = self.run.sanitizer()
        self.outcome = self.run.file(sanitizer=self.sanitizer)

    @property
    def row_dir(self) -> str:
        return os.path.join(self.run.destination, ROW1)

    def path(self, name: str) -> str:
        return os.path.join(self.row_dir, name)

    def read(self, name: str) -> str:
        return read_text(self.path(name))

    def raw(self, name: str) -> str:
        return os.path.join(self.run.run_root, "raw", name)


class FileSetTests(unittest.TestCase):
    def test_the_row_folder_holds_exactly_the_committed_set_the_new_files_and_the_s3_set(self) -> None:
        filed = default_filed()
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        expected = sorted(COMMITTED_SET + NEW_SET + S3_SET)
        self.assertEqual(sorted(os.listdir(filed.row_dir)), expected, "the row folder file set")
        for snap in ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"):
            names = os.listdir(filed.path(snap))
            for needed in SNAPSHOT_SET + LEDGER_NAMES:
                self.assertIn(needed, names, "%s holds %s" % (snap, needed))
            self.assertNotIn("status.raw", names, "the NUL status capture is not filed")

    def test_with_no_resume_line_the_s3_files_are_absent_and_the_marker_is_filed(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 1, text="Checkpoint written. Nothing to resume from.")
        filed = Filed(stages)
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        names = sorted(os.listdir(filed.row_dir))
        self.assertEqual(names, sorted(COMMITTED_SET + NEW_SET + ("resume-line.txt",)), "no s3 file is filed")
        self.assertEqual(filed.read("resume-line.txt"), "NO-RESUME-LINE\n", "the marker and nothing else")

    def test_a_stage_with_empty_stderr_still_files_a_zero_byte_err_file(self) -> None:
        filed = default_filed()
        for name in ("s1.err", "s2-preclear.err", "s3-resume.err"):
            self.assertTrue(os.path.isfile(filed.path(name)), name + " is filed")
            self.assertEqual(os.path.getsize(filed.path(name)), 0, name + " is empty")
        stages = pc_testutil.default_row1_stages()
        stages[0] = dict(stages[0], stderr="a warning line\n")
        other = Filed(stages)
        self.assertEqual(other.read("s1.err"), "a warning line\n", "a stderr text is filed as it is")

    def test_the_s2_prompt_is_a_byte_copy_of_the_committed_file(self) -> None:
        filed = default_filed()
        committed = os.path.join(filed.run.rig.repo, PUBLICATION_ROW, "s2-preclear-prompt.md")
        self.assertEqual(sha256_of(filed.path("s2-preclear-prompt.md")), sha256_of(committed), "same digest")

    def test_the_s1_prompt_is_the_stored_prompt_with_the_ledger_path_tokenised(self) -> None:
        filed = default_filed()
        stored = read_text(filed.raw("s1.prompt"))
        self.assertEqual(filed.read("s1-work-prompt.md"), filed.sanitizer.sanitize_text(stored), "tokenised copy")
        self.assertIn("<run>", filed.read("s1-work-prompt.md"), "the ledger path is a run token")

    def test_the_resume_line_and_the_two_session_ids_are_filed(self) -> None:
        filed = default_filed()
        calls = filed.run.rig.calls()
        sent = calls[2]["prompt"]
        self.assertFalse(sent.endswith("\n"), "the prompt that was sent had no newline")
        line = filed.read("resume-line.txt")
        self.assertEqual(line, filed.sanitizer.sanitize_text(sent) + "\n", "the sanitized line and one newline")
        first = filed.read("session.id").strip()
        second = filed.read("session-resume.id").strip()
        self.assertRegex(first, r"^[0-9a-f-]{36}$", "the work session id")
        self.assertRegex(second, r"^[0-9a-f-]{36}$", "the resume session id")
        self.assertNotEqual(first, second, "the two ids differ")
        self.assertEqual(filed.read("s1.exit"), "exit 0\n", "an exit file")
        self.assertEqual(filed.read("s2-preclear.exit"), "exit 0\n", "an exit file")

    def test_the_snapshot_listing_is_rebuilt_without_the_helper_path_files(self) -> None:
        filed = default_filed()
        stored = os.path.join(filed.run.run_root, "snaps", "snap-2-after-preclear")
        full = read_text(os.path.join(stored, "sha.txt"))
        self.assertIn("wrapper/py", full, "the stored listing holds the interpreter path file")
        for snap in ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"):
            for name in ("sha.txt", "manifest.jsonl"):
                text = filed.read(os.path.join(snap, name))
                self.assertNotIn("wrapper/py", text, "%s/%s has no interpreter path entry" % (snap, name))
                self.assertNotIn("wrapper/stub", text, "%s/%s has no stub path entry" % (snap, name))
                self.assertIn("wrapper/checkpoint", text, "%s/%s keeps the wrapper entry" % (snap, name))
        rebuilt = filed.read(os.path.join("snap-2-after-preclear", "sha.txt"))
        kept = [line for line in full.splitlines() if "wrapper/py" not in line and "wrapper/stub" not in line]
        self.assertEqual(rebuilt.splitlines(), kept, "the rest of the listing is the stored one")
        self.assertTrue(os.path.isfile(filed.path(os.path.join("snap-2-after-preclear", "preclear", "widget-export", "checkpoint.md"))))
        self.assertTrue(os.path.isdir(filed.path(os.path.join("snap-2-after-preclear", "auto-memory"))), "memory tree")

    def test_filing_one_run_twice_gives_the_same_files_except_the_harness_version(self) -> None:
        run = Unfiled()
        first = run.file()
        self.assertEqual(first.code, 0, "\n".join(first.lines))
        second_ctx = run.file_context()
        second_dest = os.path.join(os.path.dirname(run.destination), "rerun-2026-10-28-second")
        second = evidence().file_row(second_ctx._replace(destination=second_dest), run.run_root)
        self.assertEqual(second.code, 0, "\n".join(second.lines))
        one = tree_bytes(run.destination)
        two = tree_bytes(second_dest)
        self.assertEqual(sorted(one), sorted(two), "equal file lists")
        for relative in sorted(one):
            if relative.endswith("harness-version.txt"):
                continue
            self.assertEqual(one[relative], two[relative], "equal bytes: " + relative)
        self.assertEqual(sorted(one), list(sorted(one)), "the listing is sorted")


class ProvenanceTests(unittest.TestCase):
    def test_every_provenance_file_is_filled(self) -> None:
        filed = default_filed()
        self.assertEqual(filed.read("claude-version.txt"), "2.1.310 (Claude Code)\n", "the banner line")
        self.assertEqual(filed.read("model-id.txt"), "claude-sonnet-5-5\n", "the pinned model id")
        lines = filed.read("isolation-mode.txt").splitlines()
        self.assertEqual(len(lines), 3, "three lines")
        self.assertEqual(lines[0], "isolation: strict")
        self.assertEqual(lines[1], "setting-sources: project,local")
        import pc_flags

        self.assertEqual(lines[2], pc_flags.ISOLATION_CLAIM, "the claim sentence")
        version = filed.read("harness-version.txt").splitlines()
        self.assertEqual(len(version), 3, "three lines")
        self.assertRegex(version[0], r"^tree-sha256: [0-9a-f]{64}$")
        self.assertRegex(version[1], r"^head: ([0-9a-f]{40}|unknown)$")
        self.assertRegex(version[2], r"^harness-tree-clean: (yes|no|unknown)$")
        for name in ("claude-version.txt", "model-id.txt", "isolation-mode.txt", "harness-version.txt", "digests.txt",
                     "tools.txt", "usage.txt"):
            self.assertTrue(filed.read(name).strip(), name + " is not blank")

    def test_digests_list_the_skill_the_references_the_stub_and_the_wrapper(self) -> None:
        filed = default_filed()
        lines = filed.read("digests.txt").splitlines()
        self.assertEqual(len(lines), 6, "SKILL.md, three references, the stub and the wrapper")
        repo = filed.run.rig.repo
        tails = [
            "<run>/project/.claude/skills/preclear/SKILL.md",
            "<run>/project/.claude/skills/preclear/references/checkpoint-v1.md",
            "<run>/project/.claude/skills/preclear/references/configuration.md",
            "<run>/project/.claude/skills/preclear/references/status-sidecar.md",
            "tests/harness/checkpoint_stub.py",
            "<run>/wrapper/checkpoint",
        ]
        for line, tail in zip(lines, tails):
            self.assertRegex(line, r"^[0-9a-f]{64}  ", "a digest and two spaces")
            self.assertTrue(line.endswith("  " + tail), "line for " + tail)
        self.assertEqual(lines[0][:64], sha256_of(os.path.join(repo, "SKILL.md")), "the skill digest")
        self.assertEqual(lines[4][:64], sha256_of(os.path.join(repo, "tests", "harness", "checkpoint_stub.py")))

    def test_tools_txt_is_the_forty_rules_with_the_wrapper_path_tokenised(self) -> None:
        filed = default_filed()
        text = filed.read("tools.txt")
        self.assertTrue(text.endswith("\n") and text.count("\n") == 1, "one line")
        rules = text.strip().split(",")
        self.assertEqual(len(rules), 40, "forty rules")
        self.assertIn("Bash(<run>/wrapper/checkpoint status:*)", rules, "the wrapper rule is tokenised")
        self.assertNotIn(filed.run.rig.base, text, "no folder in the allowlist")

    def test_the_init_manifest_block_names_the_tool_count_and_every_tool(self) -> None:
        filed = default_filed()
        sections = parse_sections(filed.read("mechanical-checks.md"))
        block = sections["Init manifest"]
        for stage in ("s1", "s2", "s3"):
            self.assertIn(stage + " tool-count: 4", block, "the tool count of " + stage)
            tools = [line for line in block if line.startswith(stage + " tools: ")]
            self.assertEqual(len(tools), 1, "one tools line")
            for name in ("Bash", "Read", "Write", "Edit"):
                self.assertIn(name, tools[0], "tool " + name)

    def test_a_stage_without_a_usage_block_prints_unconfirmed_in_each_field(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 1, omit=["usage"])
        filed = Filed(stages)
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        line = [item for item in filed.read("usage.txt").splitlines() if item.startswith("stage s2:")][0]
        self.assertIn("input UNCONFIRMED, cache creation UNCONFIRMED, cache read UNCONFIRMED, output UNCONFIRMED", line)
        for item in filed.read("usage.txt").splitlines():
            self.assertNotIn(": ,", item, "no blank field")
            self.assertFalse(item.endswith(":"), "no blank field")

    def test_measurements_are_taken_on_the_original_checkpoint(self) -> None:
        import pc_measure

        filed = default_filed()
        original = os.path.join(filed.run.run_root, "project", ".preclear", "widget-export", "checkpoint.md")
        report = pc_measure.format_report(original, pc_measure.measure_file(original))
        self.assertEqual(filed.read("measurements.txt"), filed.sanitizer.sanitize_text(report), "per section actual/cap")
        md = filed.read("measurements.md")
        self.assertTrue(md.startswith("# Measurements (UTF-8 bytes on ORIGINAL unsanitized files)\n"), "title")
        self.assertIn(filed.sanitizer.sanitize_text(report), md, "the same report is inside")
        ledgers = os.path.join(filed.run.run_root, "ckpt", "ledgers")
        for name in sorted(os.listdir(ledgers)):
            path = os.path.join(ledgers, name)
            expected = "ledger file %s: %d bytes sha256 %s" % (name, os.path.getsize(path), sha256_of(path))
            self.assertIn(expected, md.splitlines(), "inventory line for " + name)
        self.assertIn("auto-memory files: ['widget-export-json-default.md']", md.splitlines(), "memory list")

    def test_a_checkpoint_of_exactly_the_cap_is_within_it_and_one_more_byte_is_over_by_one(self) -> None:
        for extra, over in ((0, False), (1, True)):
            run = Unfiled()
            path = os.path.join(run.run_root, "project", ".preclear", "widget-export", "checkpoint.md")
            head = b"## Identity and state\n"
            with open(path, "wb") as handle:
                handle.write(head + b"a" * (4096 + extra - len(head)))
            self.assertEqual(run.file().code, 0, "filing succeeds")
            text = read_text(os.path.join(run.destination, ROW1, "measurements.txt"))
            total = [line for line in text.splitlines() if line.startswith("total ")][0]
            self.assertTrue(total.startswith("total %d/4096 bytes" % (4096 + extra)), "the total is actual/cap")
            self.assertEqual(total.endswith(" over by 1"), over, "over by one only for the larger file")
            self.assertEqual("over by" in total, over, "nothing is over at exactly the cap")

    def test_without_a_checkpoint_file_both_measurement_files_say_unconfirmed(self) -> None:
        stages = pc_testutil.default_row1_stages()
        stages[1] = {
            "ops": [{"op": "text", "text": "no checkpoint was written"}],
            "result": stages[1]["result"],
        }
        filed = Filed(stages)
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        for name in ("measurements.txt", "measurements.md"):
            text = filed.read(name)
            self.assertIn("UNCONFIRMED", text, name + " says so")
            self.assertNotIn("total ", text, name + " invents no total")


def parse_sections(text: str) -> dict:
    """Map each '## ' heading of a file to its non-empty lines."""
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:]
            sections[current] = []
        elif current is not None and line.strip():
            sections[current].append(line)
    return sections


class UsageTests(unittest.TestCase):
    LINE = (
        r"^stage (s[123]): session ([0-9a-f-]{36}), subtype (\S+), turns ([0-9]+), input ([0-9]+), "
        r"cache creation ([0-9]+), cache read ([0-9]+), output ([0-9]+), cost ([0-9.]+), "
        r"cumulative ([0-9.]+), wall ([0-9.]+) seconds$"
    )

    def test_the_stages_are_listed_in_order_with_their_own_cost_and_the_row_total(self) -> None:
        import re

        filed = default_filed()
        lines = filed.read("usage.txt").splitlines()
        stage_lines = [line for line in lines if line.startswith("stage ")]
        self.assertEqual([line.split(":")[0] for line in stage_lines], ["stage s1", "stage s2", "stage s3"])
        found = [re.match(self.LINE, line) for line in stage_lines]
        for line, match in zip(stage_lines, found):
            self.assertIsNotNone(match, "a usage line has the documented fields")
        costs = [match.group(9) for match in found]
        cumulative = [match.group(10) for match in found]
        self.assertEqual(costs, ["0.03", "0.06", "0.04"], "each call's own cost")
        self.assertEqual(cumulative, ["0.03", "0.09", "0.04"], "the reported cumulative totals")
        self.assertEqual([m.group(5) for m in found], ["10", "10", "10"], "input tokens")
        self.assertEqual([m.group(6) for m in found], ["20", "20", "20"], "cache creation tokens")
        self.assertEqual([m.group(7) for m in found], ["30", "30", "30"], "cache read tokens")
        self.assertEqual([m.group(8) for m in found], ["5", "5", "5"], "output tokens")
        self.assertEqual([m.group(4) for m in found], ["2", "5", "2"], "turns")
        self.assertIn("row total: 0.13", lines, "the s2 cumulative plus the s3 total")
        self.assertIn("run total: 0.13", lines, "the run total")
        self.assertNotIn("0.16", "\n".join(lines), "s1 is never added into s2")
        self.assertEqual(found[0].group(2), found[1].group(2), "s1 and s2 share a session")
        self.assertNotEqual(found[1].group(2), found[2].group(2), "s3 is another session")

    def test_without_an_s3_the_row_total_is_the_s2_cumulative_total(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 1, text="Checkpoint written. Nothing to resume.")
        filed = Filed(stages)
        lines = filed.read("usage.txt").splitlines()
        self.assertEqual([line.split(":")[0] for line in lines if line.startswith("stage ")], ["stage s1", "stage s2"])
        self.assertIn("row total: 0.09", lines, "only the s2 chain")

    def test_costs_are_the_decimal_text_as_parsed(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 0, total_cost_usd=0.1)
        stages = with_result(stages, 1, total_cost_usd=0.3, delta=0.2)
        filed = Filed(stages)
        text = filed.read("usage.txt")
        self.assertIn("cumulative 0.1,", text, "the text 0.1 is kept")
        self.assertIn("cost 0.2,", text, "the delta is kept as text")
        self.assertIn("row total: 0.34", text, "0.3 plus 0.04 added as decimals")


def copied(facts: dict) -> dict:
    return json.loads(json.dumps(facts))


class UsageConsistencyTests(unittest.TestCase):
    """IN-01: usage.txt shows the cumulative-consistent flag behind the row total, and warns on a no."""

    def lines_of(self, filed) -> list:
        return filed.read("usage.txt").splitlines()

    def test_the_default_run_shows_yes_for_each_stage_in_order_and_no_warning(self) -> None:
        import re

        lines = self.lines_of(default_filed())
        flags = [line for line in lines if line.startswith("cumulative-consistent ")]
        self.assertEqual(
            flags,
            ["cumulative-consistent s1: yes", "cumulative-consistent s2: yes", "cumulative-consistent s3: yes"],
            "one flag per stage in stage order",
        )
        self.assertEqual([line for line in lines if line.startswith("warning")], [], "no warning line")
        first = max(index for index, line in enumerate(lines) if line.startswith("stage "))
        self.assertLess(first, lines.index(flags[0]), "the flags follow the stage lines")
        self.assertLess(lines.index(flags[-1]), lines.index("row total: 0.13"), "and come before the row total")
        pattern = re.compile(UsageTests.LINE)
        stage_lines = [line for line in lines if line.startswith("stage ")]
        self.assertEqual(len(stage_lines), 3, "the stage lines are unchanged in number")
        for line in stage_lines:
            self.assertIsNotNone(pattern.match(line), "a stage line keeps its documented fields")
        self.assertIn("row total: 0.13", lines)
        self.assertIn("run total: 0.13", lines)

    def test_a_cumulative_total_that_disagrees_gives_a_no_and_exactly_one_warning_naming_the_stage(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 1, total_cost_usd=0.20)
        filed = Filed(stages)
        lines = self.lines_of(filed)
        self.assertIn("cumulative-consistent s2: no", lines, "the flag reads no")
        self.assertIn("cumulative-consistent s1: yes", lines)
        warnings = [line for line in lines if line.startswith("warning")]
        self.assertEqual(len(warnings), 1, "one warning line")
        self.assertIn("s2", warnings[0], "it names the stage")
        self.assertIsNone(verdict_pattern().search("\n".join(lines)), "no line holds a verdict word")

    def test_a_record_without_the_key_shows_unconfirmed_and_no_warning(self) -> None:
        run = Unfiled()
        path = os.path.join(run.run_root, "raw", "s2.record.json")
        record = json.loads(read_text(path))
        del record["cumulative_consistent"]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
        self.assertEqual(run.file().code, 0, "the run still files")
        lines = read_text(os.path.join(run.destination, ROW1, "usage.txt")).splitlines()
        self.assertIn("cumulative-consistent s2: UNCONFIRMED", lines)
        self.assertEqual([line for line in lines if line.startswith("warning")], [], "no warning for a missing key")


class MechanicalFactLineTests(unittest.TestCase):
    """EVID-04, D-09: the filed counters and the checklist hold the numbers the exit rule uses."""

    def parts(self):
        import pc_checks

        run = default_filed().run
        data = evidence().load_stage_data(run.run_root)
        facts = pc_checks.compute_facts(run.run_root, run.ctx.config_dir)
        return data, facts

    def test_the_default_run_lists_both_counters_in_the_write_boundary_section(self) -> None:
        filed = default_filed()
        section = parse_sections(filed.read("mechanical-checks.md"))["Write boundary"]
        self.assertIn("bash-write-escapes: 0", section)
        self.assertIn("run-record-changes: 0", section)

    def test_the_rendered_lines_show_the_counts_of_the_facts(self) -> None:
        data, facts = self.parts()
        changed = copied(facts)
        changed["bash_mentions"]["write_escapes"] = {"count": 2, "programs": {"mkdir": 2}}
        changed["guard"] = {"count": 3, "kinds": {"raw-entry-changed": 3}}
        text = evidence().render_mechanical_checks(data, changed).decode("utf-8")
        section = parse_sections(text)["Write boundary"]
        self.assertIn("bash-write-escapes: 2", section)
        self.assertIn("run-record-changes: 3", section)

    def test_the_checklist_writes_number_equals_the_count_the_exit_rule_uses(self) -> None:
        import re

        import pc_checks

        data, facts = self.parts()
        changed = copied(facts)
        changed["write_boundary"]["count"] = 1
        changed["trace_writes"]["count"] = 1
        changed["bash_mentions"]["write_escapes"] = {"count": 2, "programs": {"mkdir": 2}}
        changed["memory_probe"] = "present"
        line = [item for item in evidence().checklist_lines(data, changed) if "writes outside approved roots" in item]
        self.assertEqual(len(line), 1, "one writes line")
        match = re.search(r"writes outside approved roots: ([0-9]+);", line[0])
        self.assertIsNotNone(match, "the line carries the total")
        self.assertEqual(int(match.group(1)), 5, "1 snapshot path, 1 tool path, 2 Bash writes and the memory folder")
        self.assertIn("Bash writes 2", line[0], "the Bash writes are named")
        used = dict(pc_checks.breaches(changed))[pc_checks.BREACH_WRITES]
        self.assertEqual(int(match.group(1)), used, "the number a reviewer reads is the number breaches() uses")


class TraceTests(unittest.TestCase):
    def test_the_short_trace_has_the_committed_shape(self) -> None:
        import re

        filed = default_filed()
        text = filed.read("s2-preclear-trace.md")
        lines = text.splitlines()
        self.assertEqual(lines[0], "# row1-wrong-binding: s2-preclear")
        bullets = [line for line in lines if line.startswith("- ")]
        self.assertEqual(len(bullets), 5, "one bullet per tool call")
        self.assertTrue(any(re.match(r"^Turns 5\. Write/Edit calls 2: \[.*\]\. Bash calls naming the configured "
                                     r"executable: 2\. Results flagged .*: 1\.$", line) for line in lines),
                        "the footer line")
        self.assertIn("Usage: input 10, cache creation 20, cache read 30, output 5.", lines)
        self.assertIn("## Final reply", lines)
        self.assertIn("Checkpoint written.", text.split("## Final reply", 1)[1], "the reply text follows")

    def test_the_full_trace_has_the_committed_header_and_one_block_per_call(self) -> None:
        import re

        filed = default_filed()
        record = json.loads(read_text(filed.raw("s2.record.json")))
        text = filed.read("s2-preclear-full-trace.md")
        lines = text.splitlines()
        self.assertEqual(lines[0], "# row1-wrong-binding: s2-preclear: complete sanitized tool calls and results")
        self.assertIn(
            "raw transcript sha256 %s, %d bytes (retained privately in the run root)"
            % (record["stdout_sha256"], record["stdout_size"]),
            lines,
        )
        self.assertIn("Calls 5; results flagged as refusal/denial: 1.", lines)
        heads = [line for line in lines if line.startswith("### ")]
        self.assertEqual(len(heads), 5, "one heading per call")
        self.assertRegex(heads[0], r"^### 1\. Bash \(toolu_0001\)$")
        self.assertRegex(heads[4], r"^### 5\. Bash \(toolu_0005\)  ERROR  REFUSAL/DENIAL$")
        self.assertTrue(heads[2].startswith("### 3. Write (toolu_0003)"), "a Write block")
        self.assertTrue(re.match(r"^### 3\. Write \(toolu_0003\)$", heads[2]), "no flag on an executed write")

    def test_the_full_trace_parses_through_the_trace_reader_with_flags_from_the_denial_union(self) -> None:
        import pc_mine

        filed = default_filed()
        calls = pc_mine.parse_trace(filed.read("s2-preclear-full-trace.md"))
        self.assertEqual(len(calls), 3, "three Bash calls")
        self.assertEqual([call["refusal"] for call in calls], [False, False, True], "flags equal the denial union")
        self.assertTrue(calls[0]["command"].endswith("<run>/wrapper/checkpoint status"), "the helper command")
        self.assertEqual(calls[1]["command"], "ls", "an ordinary command")

    def test_no_flag_is_decided_by_reply_or_result_text(self) -> None:
        import pc_mine

        words = "permission " + "denied REFUSAL/" + "DENIAL blocked"
        stages = with_ops(
            pc_testutil.default_row1_stages(), 1,
            [{"op": "tool", "name": "Bash", "input": {"command": "pwd"}, "content": words}],
        )
        stages = with_result(stages, 1, text="Checkpoint written.\n\n" + words + "\n\n```\nResume widget-export now\n```\n")
        filed = Filed(stages)
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        calls = pc_mine.parse_trace(filed.read("s2-preclear-full-trace.md"))
        self.assertEqual([call["refusal"] for call in calls], [False, False, True, False], "only the structured one")
        self.assertIn("Calls 6; results flagged as refusal/denial: 1.", filed.read("s2-preclear-full-trace.md"))

    def test_the_work_and_resume_turns_have_full_traces_and_the_resume_turn_a_short_one(self) -> None:
        filed = default_filed()
        self.assertTrue(filed.read("s1-work-full-trace.md").startswith("# row1-wrong-binding: s1-work: complete"))
        self.assertTrue(filed.read("s3-resume-trace.md").startswith("# row1-wrong-binding: s3-resume\n"))
        self.assertIn("Calls 1; results flagged as refusal/denial: 0.", filed.read("s3-resume-full-trace.md"))
        self.assertRegex(filed.read("s3-resume-full-trace.md"), r"### 1\. Read \(toolu_0001\): `.*` -> result [0-9]+ chars")


class VocabularyTests(unittest.TestCase):
    def authored(self, filed: "Filed") -> list:
        names = []
        for dirpath, _dirnames, filenames in os.walk(filed.run.destination):
            for name in filenames:
                names.append(os.path.relpath(os.path.join(dirpath, name), filed.run.destination).replace(os.sep, "/"))
        return evidence().harness_authored_names(sorted(names))

    def test_no_harness_authored_file_holds_a_verdict_word_except_the_one_last_line(self) -> None:
        filed = default_filed()
        names = self.authored(filed)
        self.assertGreater(len(names), 10, "the scan covers many files")
        self.assertIn("README.md", names, "the folder README is scanned")
        self.assertIn(ROW1 + "/README.md", names, "the row README is scanned")
        pattern = verdict_pattern()
        for name in names:
            text = read_text(os.path.join(filed.run.destination, name))
            if name == ROW1 + "/README.md":
                self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"), "the line closes the row README")
                text = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(text), "no verdict word in " + name)

    def test_the_verdict_line_occurs_once_in_the_whole_folder_of_harness_files(self) -> None:
        filed = default_filed()
        count = 0
        for name in self.authored(filed):
            count += read_text(os.path.join(filed.run.destination, name)).count(VERDICT_LINE)
        self.assertEqual(count, 1, "once")

    def test_a_reply_with_verdict_words_is_outside_the_scan_and_fails_nothing(self) -> None:
        reply = "The " + "pa" + "ss and the " + "ver" + "dict were " + "fa" + "iled and " + "acc" + "epted."
        stages = with_result(pc_testutil.default_row1_stages(), 1, text=reply + "\n\n```\nResume widget-export\n```\n")
        filed = Filed(stages)
        self.assertEqual(filed.outcome.code, 0, "\n".join(filed.outcome.lines))
        pattern = verdict_pattern()
        self.assertIsNotNone(pattern.search(filed.read("s2-preclear-trace.md")), "the reply is filed as written")
        for name in self.authored(filed):
            text = read_text(os.path.join(filed.run.destination, name))
            if name == ROW1 + "/README.md":
                text = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(text), "no verdict word in " + name)
        self.assertNotIn("s2-preclear-trace.md", " ".join(self.authored(filed)), "a trace is outside the scan")


class ChecklistTests(unittest.TestCase):
    def test_the_row_readme_has_the_setup_the_stage_table_the_facts_and_the_checklist_last(self) -> None:
        filed = default_filed()
        text = filed.read("README.md")
        lines = text.splitlines()
        self.assertEqual(lines[-1], VERDICT_LINE, "the last line")
        self.assertTrue(text.endswith(VERDICT_LINE + "\n") and not text.endswith("\n\n"), "one newline, nothing after")
        self.assertTrue(any(line.startswith("Setup: ") for line in lines), "the Setup paragraph")
        self.assertIn("| Stage | Session | Exit | Turns | Subtype |", lines, "the stage table")
        self.assertTrue(any(line.startswith("| s2 | ") for line in lines), "a stage row")
        checklist = [line for line in lines if line.startswith("- [ ] ")]
        self.assertEqual(len(checklist), 7, "one line per fact")
        self.assertTrue(lines[-2].startswith("- [ ] "), "the line before the verdict is a checklist line")
        self.assertEqual(lines[-1 - len(checklist):-1], checklist, "the checklist is the last block, no gaps")
        for line, prefix in zip(checklist, CHECKLIST_PREFIXES):
            self.assertTrue(line.startswith("- [ ] " + prefix), "order: " + prefix)
            self.assertRegex(line, r"\(source: [^)]+\)$", "a source in parentheses")
        self.assertIn("compound refusals 0", checklist[0], "a zero is printed as 0")
        self.assertIn("denied 1", checklist[0], "the denied call")
        self.assertIn("attempted 2, executed 1", checklist[0], "attempted and executed")
        self.assertRegex(checklist[3], r"git mutations: 0", "a zero git count")
        self.assertRegex(checklist[2], r"writes outside approved roots: 0", "a zero write count")
        self.assertIn("/4096", checklist[4], "bytes against the cap")
        self.assertIn("0.06", checklist[6], "the s2 call cost")

    def test_mechanical_checks_has_the_ten_sections_in_order_with_name_value_lines(self) -> None:
        import re

        filed = default_filed()
        text = filed.read("mechanical-checks.md")
        headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, list(SECTION_NAMES), "the ten sections in order")
        sections = parse_sections(text)
        for name, block in sections.items():
            self.assertGreater(len(block), 0, name + " is not empty")
            for line in block:
                self.assertRegex(line, r"^[^:]+: .+$", "name: value in " + name)
        for stage in ("s1", "s2", "s3"):
            found = []
            for line in sections["Assertions"]:
                match = re.match(r"^%s ([a-z0-9-]+): (yes|no) \(([a-z0-9-]+)\)$" % stage, line)
                if match:
                    found.append(match.group(1))
            self.assertEqual(found, list(ASSERTION_IDS), "the twelve ids in declared order for " + stage)
        self.assertIn("ledgers-unchanged: yes", sections["Ledgers"])
        self.assertIn("s2 attempted: 2", sections["Helper calls"])
        self.assertIn("s2 denied: 1", sections["Helper calls"])
        self.assertIn("s2 compound-refusals: 0", sections["Helper calls"])
        self.assertIn("mutations-total: 0", sections["Git"])
        self.assertIn("default-memory-folder: absent", sections["Write boundary"])


class FolderReadmeTests(unittest.TestCase):
    def test_the_folder_readme_labels_the_run_and_states_the_differences(self) -> None:
        import pc_flags

        filed = default_filed()
        text = read_text(os.path.join(filed.run.destination, "README.md"))
        usage = filed.read("usage.txt")
        row_total = [line for line in usage.splitlines() if line.startswith("row total: ")][0][len("row total: "):]
        run_total = [line for line in usage.splitlines() if line.startswith("run total: ")][0][len("run total: "):]
        self.assertIn("new baseline", text, "the baseline label")
        self.assertIn("claude-sonnet-5-5", text, "the pinned model")
        self.assertIn("2.1.310", text, "the build")
        self.assertIn(row_total, text, "the row total quoted")
        self.assertIn(run_total, text, "the run total quoted")
        self.assertIn("not a replication", text, "not a replication")
        self.assertIn("2026-10-20", text, "the earlier run is named")
        self.assertIn("recorded no model", text, "the reason")
        self.assertIn("Claude Code 2.1.310 against %s" % pc_flags.COMMITTED_EVIDENCE_VERSION, text, "build difference")
        for phrase in ("the pinned flag set", "the stub in place of the real helper", "per-verb allowlist",
                       "run roots outside the home folder", "strict isolation"):
            self.assertIn(phrase, text, "difference: " + phrase)
        self.assertIn("committed folder stays the reference", text, "reference statement")
        self.assertIn("the reviewer", text, "says the reviewer")
        self.assertNotIn("bokiko", text.lower(), "never the owner's login")
        self.assertIsNone(verdict_pattern().search(text), "no verdict word")


# ---------------------------------------------------------------------------------------------
# Task 3: a SKIPPED row, the zero-token refile, the race and the README
# ---------------------------------------------------------------------------------------------

SKIP_ID = "row0-skip-case"
FIXED_REASON = "the precondition of this test row is not met"
USAGE_TEXT = "the run folder is not usable"


def skip_registry(reason: str):
    from decimal import Decimal

    pc_rows = rows()
    stages = (pc_rows.StageSpec("s1", "work turn", "work", 5, Decimal("0.10"), 60, "new:A"),)
    row = pc_rows.RowSpec(SKIP_ID, "row", "injected test row", stages, True, lambda: reason, None, ())
    return pc_rows.build_registry([row])


def run_skip(reason: str, precreate: bool = False):
    rig = pc_testutil.RowRig()
    out = io.StringIO()
    err = io.StringIO()
    destination = os.path.join(rig.repo, "tests", "evidence", DEST_NAME)
    if precreate:
        os.makedirs(destination)
    code = matrix().main(
        ["--row", SKIP_ID, "--claude", rig.claude, "--budget", "2.00"],
        env=dict(rig.env),
        repo_root=rig.repo,
        registry=skip_registry(reason),
        clock=fixed_clock,
        out=out,
        err=err,
    )
    return rig, code, out.getvalue() + err.getvalue(), destination


def rerun_folders(rig) -> list:
    return [name for name in os.listdir(os.path.join(rig.repo, "tests", "evidence")) if name.startswith("rerun-")]


class SkippedTests(unittest.TestCase):
    def test_a_real_run_skip_files_a_label_folder_and_exits_10(self) -> None:
        import pc_spend

        rig, code, text, destination = run_skip(FIXED_REASON)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_SKIP, text)
        self.assertEqual(rig.calls(), [], "no stage was launched")
        self.assertEqual(rig.tripwire(), [], "no other claude call was made")
        self.assertEqual(pc_spend.read_records(rig.context().harness_home), [], "no ledger line was written")
        folder = os.path.join(destination, "SKIPPED-" + SKIP_ID)
        self.assertEqual(os.listdir(destination), ["SKIPPED-" + SKIP_ID], "only the label folder")
        self.assertEqual(os.listdir(folder), ["README.md"], "the label folder holds one README and no result files")
        body = read_text(os.path.join(folder, "README.md"))
        self.assertEqual(body.splitlines()[0], "# SKIPPED: " + SKIP_ID, "the heading")
        self.assertIn("No session was run", body, "says no session was run")
        self.assertIn(FIXED_REASON, body, "names the reason")
        self.assertTrue(body.endswith("\n" + VERDICT_LINE + "\n"), "ends with the exact line")
        self.assertIsNone(verdict_pattern().search(body[: -len(VERDICT_LINE) - 1]), "no verdict word")
        self.assertIn("SKIPPED", text, "the driver printed the label")

    def test_a_reason_shaped_like_a_home_path_is_refused_with_14_and_files_nothing(self) -> None:
        import pc_seeds

        reason = "the folder " + pc_seeds.home_path("pcsynthhome") + "/data is missing"
        rig, code, text, destination = run_skip(reason)
        self.assertEqual(code, pc_exitcodes.LEAK_REFUSED, text)
        self.assertEqual(rerun_folders(rig), [], "nothing was created")

    def test_an_existing_destination_is_17_and_a_skip_never_exits_0(self) -> None:
        rig, code, text, destination = run_skip(FIXED_REASON, precreate=True)
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, text)
        self.assertEqual(os.listdir(destination), [], "the existing folder was not written into")
        self.assertNotEqual(code, 0, "a skip is never a success")


def refile(run: "Unfiled", extra=(), env=None, clock=fixed_clock, path=None):
    out = io.StringIO()
    err = io.StringIO()
    code = matrix().main(
        ["--refile", path if path is not None else run.run_root] + list(extra),
        env=env if env is not None else dict(run.rig.env),
        repo_root=run.rig.repo,
        clock=clock,
        out=out,
        err=err,
    )
    return code, out.getvalue() + err.getvalue()


class RefileTests(unittest.TestCase):
    def test_a_refile_files_the_same_tree_with_zero_tokens(self) -> None:
        import pc_spend
        import tempfile

        run = Unfiled()
        calls = len(run.rig.calls())
        ledger = pc_spend.read_records(run.ctx.harness_home)
        wire = tempfile.mkdtemp(prefix="pc-wire-")
        pc_testutil.make_tripwire(wire)
        env = dict(run.rig.env)
        env["PATH"] = os.pathsep.join([wire, env["PATH"]])
        code, text = refile(run, env=env)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(run.rig.calls()), calls, "no stage process was started")
        self.assertEqual(pc_testutil.read_tripwire(wire), [], "no claude was run")
        self.assertEqual(pc_spend.read_records(run.ctx.harness_home), ledger, "no ledger line was written")
        self.assertTrue(os.path.isdir(run.destination), "the destination was created")
        fresh = os.path.join(os.path.dirname(run.destination), "rerun-2026-10-28-fresh")
        outcome = evidence().file_row(run.file_context()._replace(destination=fresh), run.run_root)
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        one = tree_bytes(run.destination)
        two = tree_bytes(fresh)
        self.assertEqual(sorted(one), sorted(two), "the same files as a fresh filing")
        for relative in sorted(one):
            if not relative.endswith("harness-version.txt"):
                self.assertEqual(one[relative], two[relative], "same bytes: " + relative)

    def test_a_refile_needs_no_claude_and_no_budget(self) -> None:
        run = Unfiled()
        env = dict(run.rig.env)
        env["PATH"] = os.pathsep.join(pc_testutil.SYSTEM_DIRS)
        code, text = refile(run, env=env)
        self.assertEqual(code, 0, text)

    def test_unusable_run_folders_are_exit_2_with_fixed_text_and_no_echo(self) -> None:
        import tempfile

        run = Unfiled()
        run_root = run.run_root
        outside = tempfile.mkdtemp(prefix="pc-outside-")
        os.makedirs(os.path.join(outside, "raw"))
        with open(os.path.join(outside, "raw", "run.json"), "w", encoding="utf-8") as handle:
            handle.write("{}")
        empty = os.path.join(run.ctx.runs_root, "empty-run")
        os.makedirs(empty)
        cases = {
            "relative": "relative-run-folder",
            "missing": run_root + "-missing",
            "a file": os.path.join(run_root, "raw", "run.json"),
            "outside the runs root": outside,
            "no run record": empty,
        }
        for label, value in cases.items():
            code, text = refile(run, path=value)
            self.assertEqual(code, pc_exitcodes.USAGE, label + ": " + text)
            self.assertIn(USAGE_TEXT, text, label + ": the fixed text")
            self.assertNotIn(os.path.basename(value), text, label + ": the value is not echoed")
        self.assertEqual(rerun_folders(run.rig), [], "nothing was filed")

    def test_an_existing_destination_is_17(self) -> None:
        run = Unfiled()
        self.assertEqual(run.file().code, 0, "the first filing")
        before = tree_bytes(run.destination)
        code, text = refile(run)
        self.assertEqual(code, pc_exitcodes.PROMOTE_REFUSED, text)
        self.assertEqual(tree_bytes(run.destination), before, "the folder is unchanged")

    def test_a_run_with_a_breach_is_11_and_files_nothing(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1))
        ctx = rig.context()
        outcome = row1().run_row(ctx)
        self.assertEqual(outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "the row stopped with the breach")
        names = os.listdir(ctx.runs_root)
        out = io.StringIO()
        err = io.StringIO()
        code = matrix().main(
            ["--refile", os.path.join(ctx.runs_root, names[0])],
            env=dict(rig.env), repo_root=rig.repo, clock=fixed_clock, out=out, err=err,
        )
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, out.getvalue() + err.getvalue())
        self.assertEqual(rerun_folders(rig), [], "nothing was filed")

    def test_a_missing_stored_prompt_is_11_and_files_nothing(self) -> None:
        run = Unfiled()
        raw = os.path.join(run.run_root, "raw")
        os.rename(os.path.join(raw, "s2.prompt"), os.path.join(raw, "s2.prompt.moved"))
        code, text = refile(run)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, text)
        self.assertEqual(rerun_folders(run.rig), [], "nothing was filed")

    def test_the_destination_uses_the_date_recorded_in_the_run(self) -> None:
        run = Unfiled()
        later = lambda: datetime.datetime(2026, 11, 5, 9, 0, 0, tzinfo=datetime.timezone.utc)  # noqa: E731
        code, text = refile(run, clock=later)
        self.assertEqual(code, 0, text)
        self.assertEqual(rerun_folders(run.rig), [DEST_NAME], "the original date, not today's")

    def test_refile_is_its_own_selection_mode(self) -> None:
        run = Unfiled()
        for extra in (["--row", ROW1], ["--dry-run"], ["--list"], ["--all"], ["--layout", "plain-memory"]):
            code, text = refile(run, extra=extra)
            self.assertEqual(code, pc_exitcodes.USAGE, " ".join(extra) + ": " + text)
        self.assertEqual(rerun_folders(run.rig), [], "nothing was filed")

    def test_a_fresh_run_and_a_refile_file_through_the_same_function(self) -> None:
        ev = evidence()
        with mock.patch.object(ev, "file_row", wraps=ev.file_row) as spy:
            world = World()
            self.assertEqual(world.code, 0, world.text)
        self.assertEqual(spy.call_count, 1, "a fresh run calls file_row once")
        run = Unfiled()
        with mock.patch.object(ev, "file_row", wraps=ev.file_row) as spy:
            code, text = refile(run)
        self.assertEqual(code, 0, text)
        self.assertEqual(spy.call_count, 1, "a refile calls file_row once")


def tripwire_env(run: "Unfiled") -> tuple:
    """The rig's environment with a tripwire claude first on PATH, and the folder that holds its log."""
    import tempfile

    wire = tempfile.mkdtemp(prefix="pc-wire-")
    pc_testutil.make_tripwire(wire)
    env = dict(run.rig.env)
    env["PATH"] = os.pathsep.join([wire, env["PATH"]])
    return wire, env


NOT_CLEAN_TEXT = "did not finish cleanly"
STAGE_MISSING_TEXT = "a stage did not run"
UNREADABLE_TEXT = "could not be read for filing"
BREACH_TEXT = "breach"
FIXED_LINES = {
    NOT_CLEAN_TEXT: "the not-clean line",
    STAGE_MISSING_TEXT: "the stage line",
    UNREADABLE_TEXT: "the unreadable line",
    BREACH_TEXT: "the breach line",
}


def assert_refused_for_nothing_filed(case: unittest.TestCase, run: "Unfiled", label: str, expected=NOT_CLEAN_TEXT) -> str:
    """A refile of the run exits 11 and creates and starts nothing. expected is one fixed text or a tuple of
    texts of which exactly one fixed line must be printed; the name of the line that fired is returned."""
    import pc_spend

    wanted = (expected,) if isinstance(expected, str) else tuple(expected)
    wire, env = tripwire_env(run)
    ledger = pc_spend.read_records(run.ctx.harness_home)
    calls = len(run.rig.calls())
    before = sorted(os.listdir(run.run_root))
    code, text = refile(run, env=env)
    case.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, label + ": " + text)
    fired = [FIXED_LINES.get(item, item) for item in wanted if item in text]
    case.assertEqual(len(fired), 1, label + ": one expected fixed line is printed: " + text)
    case.assertNotIn(run.rig.base, text, label + ": no folder in the text")
    case.assertEqual(rerun_folders(run.rig), [], label + ": no evidence folder")
    case.assertEqual(sorted(os.listdir(run.run_root)), before, label + ": no stage folder in the run root")
    case.assertEqual(len(run.rig.calls()), calls, label + ": no stage process was started")
    case.assertEqual(pc_testutil.read_tripwire(wire), [], label + ": no claude was run")
    case.assertEqual(pc_spend.read_records(run.ctx.harness_home), ledger, label + ": no ledger line was written")
    return fired[0]


class RefileCleanRunTests(unittest.TestCase):
    """CR-01: a run the live path refused cannot be refiled; the rule is the live path's own."""

    def assert_refused_for_nothing_filed(self, run: "Unfiled", label: str) -> None:
        assert_refused_for_nothing_filed(self, run, label)

    def test_a_chain_stopped_at_s2_by_an_error_subtype_cannot_be_refiled(self) -> None:
        stages = with_result(pc_testutil.default_row1_stages(), 1, subtype="error_during_execution")
        run = Unfiled(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "the live path refused the run")
        self.assert_refused_for_nothing_filed(run, "error_during_execution")

    def test_every_unclean_stage_shape_is_refused(self) -> None:
        base = pc_testutil.default_row1_stages()
        cases = {
            "max turns subtype": with_result(base, 1, subtype="error_max_turns"),
            "error flag": with_result(base, 1, is_error=True),
            "terminal reason": with_result(base, 1, terminal_reason="max_turns"),
            "process exit": pc_testutil.stages_with(base, 1, exit=1),
            "failed isolation assertion": pc_testutil.stages_with(base, 0, init={"model": "some-other-model"}),
        }
        for label, stages in sorted(cases.items()):
            run = Unfiled(stages)
            self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, label + ": the live path refused")
            self.assert_refused_for_nothing_filed(run, label)

    def test_a_record_without_its_problem_or_evaluation_key_or_with_a_stop_is_refused(self) -> None:
        def drop(key):
            def change(record):
                del record[key]

            return change

        def stop(record):
            record["evaluation"] = "stop"

        cases = {"no problem key": drop("problem"), "no evaluation key": drop("evaluation"), "stop": stop}
        for label, change in sorted(cases.items()):
            run = Unfiled()
            path = os.path.join(run.run_root, "raw", "s2.record.json")
            record = json.loads(read_text(path))
            change(record)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
            self.assert_refused_for_nothing_filed(run, label)

    def test_the_clean_default_run_and_a_run_with_no_s3_still_refile(self) -> None:
        run = Unfiled()
        code, text = refile(run)
        self.assertEqual(code, 0, "the clean default run: " + text)
        stages = with_result(pc_testutil.default_row1_stages(), 1, text="Checkpoint written. Nothing to resume.")
        run = Unfiled(stages)
        code, text = refile(run)
        self.assertEqual(code, 0, "a run with no s3: " + text)


def move_aside(run: "Unfiled", name: str) -> None:
    """Move a raw file of the run root to a name beside it (tests never delete)."""
    raw = os.path.join(run.run_root, "raw")
    os.rename(os.path.join(raw, name), os.path.join(raw, name + ".moved"))


def rewrite_chain(run: "Unfiled", **changes) -> None:
    path = os.path.join(run.run_root, "raw", "chain.json")
    record = json.loads(read_text(path))
    record.update(changes)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")


def hand_stage(name: str, clean: bool = True) -> object:
    record = {"problem": "" if clean else "stopped", "evaluation": row1().STATUS_PASS}
    return evidence().StageData(name, record, b"", b"", "prompt", [])


def hand_run(names: tuple, marker) -> object:
    chain = None if marker is None else {"marker": marker}
    return evidence().RunData({}, chain, [hand_stage(name) for name in names], {})


class RefileChainTests(unittest.TestCase):
    """CR-01 of the second pass: a run whose chain stopped early is neither filed nor refiled."""

    def test_a_run_with_only_a_clean_s1_is_refused(self) -> None:
        run = Unfiled()
        for name in ("s2.record.json", "s3.record.json", "chain.json"):
            move_aside(run, name)
        self.assertEqual(assert_refused_for_nothing_filed(self, run, "s1 only", STAGE_MISSING_TEXT), "the stage line")

    def test_s1_and_s2_with_a_found_marker_and_no_s3_is_refused(self) -> None:
        run = Unfiled()
        move_aside(run, "s3.record.json")
        self.assertEqual(
            assert_refused_for_nothing_filed(self, run, "no s3", STAGE_MISSING_TEXT), "the stage line"
        )

    def test_s3_present_with_a_marker_none_is_refused(self) -> None:
        run = Unfiled()
        rewrite_chain(run, marker=row1().MARKER_NONE, resume_line=None, resume_line_bytes=0)
        fired = assert_refused_for_nothing_filed(
            self, run, "s3 with marker none", (STAGE_MISSING_TEXT, BREACH_TEXT, UNREADABLE_TEXT)
        )
        self.assertIn(fired, ("the stage line", "the breach line", "the unreadable line"))

    def test_s2_missing_is_refused(self) -> None:
        run = Unfiled()
        move_aside(run, "s2.record.json")
        fired = assert_refused_for_nothing_filed(
            self, run, "s2 missing", (STAGE_MISSING_TEXT, BREACH_TEXT, UNREADABLE_TEXT)
        )
        self.assertIn(fired, ("the stage line", "the breach line", "the unreadable line"))

    def test_a_chain_record_that_is_absent_or_holds_another_marker_is_refused(self) -> None:
        run = Unfiled()
        move_aside(run, "chain.json")
        assert_refused_for_nothing_filed(
            self, run, "no chain record", (STAGE_MISSING_TEXT, BREACH_TEXT, UNREADABLE_TEXT)
        )
        run = Unfiled()
        rewrite_chain(run, marker="something-else")
        assert_refused_for_nothing_filed(
            self, run, "another marker", (STAGE_MISSING_TEXT, BREACH_TEXT, UNREADABLE_TEXT)
        )

    def test_the_rule_itself_over_hand_built_runs(self) -> None:
        found, none = row1().MARKER_FOUND, row1().MARKER_NONE
        ev = evidence()
        self.assertIsNone(ev._unfileable(hand_run(("s1", "s2"), none)), "s1, s2, marker none")
        self.assertIsNone(ev._unfileable(hand_run(("s1", "s2", "s3"), found)), "s1, s2, s3, marker found")
        stage_line = ev.MESSAGE_STAGE_MISSING
        self.assertIn(STAGE_MISSING_TEXT, stage_line)
        cases = {
            "s1 alone": hand_run(("s1",), none),
            "s1 alone with a found marker": hand_run(("s1",), found),
            "s1, s2, found, no s3": hand_run(("s1", "s2"), found),
            "s1, s2, s3, marker none": hand_run(("s1", "s2", "s3"), none),
            "s1 and s3": hand_run(("s1", "s3"), found),
            "all three, no chain": hand_run(("s1", "s2", "s3"), None),
            "s1, s2, another marker": hand_run(("s1", "s2"), "other"),
        }
        for label, data in sorted(cases.items()):
            self.assertEqual(ev._unfileable(data), stage_line, label)
        unclean = ev.RunData({}, None, [hand_stage("s1", clean=False)], {})
        self.assertIn(NOT_CLEAN_TEXT, ev._unfileable(unclean), "the per-stage rule still comes first")
        self.assertIn(UNREADABLE_TEXT, ev._unfileable(ev.RunData({}, None, [], {})), "no stages")

    def test_the_controls_still_refile(self) -> None:
        code, text = refile(Unfiled())
        self.assertEqual(code, 0, "the clean default run: " + text)
        stages = with_result(pc_testutil.default_row1_stages(), 1, text="Checkpoint written. Nothing to resume.")
        code, text = refile(Unfiled(stages))
        self.assertEqual(code, 0, "a run with no s3: " + text)


class DenyEntriesContractTests(unittest.TestCase):
    """WR-03: filing needs the sanitizer's deny entries, so the login check is not left to the caller."""

    def test_file_row_without_deny_entries_is_15_and_does_nothing(self) -> None:
        run = Unfiled()
        ctx = run.file_context()._replace(deny_entries=None)
        before = sorted(os.listdir(run.run_root))
        with mock.patch.object(pc_promote, "promote") as spy, mock.patch.object(
            evidence(), "load_stage_data"
        ) as reader:
            outcome = evidence().file_row(ctx, run.run_root)
        self.assertEqual(outcome.code, pc_exitcodes.SCANNER_ERROR, "\n".join(outcome.lines))
        self.assertEqual(spy.call_count, 0, "promote was not called")
        self.assertEqual(reader.call_count, 0, "the run root was not read")
        self.assertEqual(sorted(os.listdir(run.run_root)), before, "no stage folder was made")
        self.assertFalse(os.path.lexists(run.destination), "the destination was not created")
        self.assertIn("deny entries", "\n".join(outcome.lines), "the fixed line")
        self.assertNotIn(run.rig.base, "\n".join(outcome.lines), "no folder in the text")

    def test_file_skipped_without_deny_entries_is_15_and_creates_nothing(self) -> None:
        import pc_sanitize

        rig = pc_testutil.RowRig()
        ctx = rig.context()
        sanitizer = pc_sanitize.Sanitizer.from_machine(rig.repo)
        runs_before = sorted(os.listdir(ctx.runs_root))
        evidence_before = sorted(os.listdir(os.path.dirname(ctx.destination)))
        with mock.patch.object(pc_promote, "promote") as spy:
            outcome = evidence().file_skipped(
                rig.repo, ctx.destination, ROW1, FIXED_REASON, sanitizer, None, ctx.config_dir, ctx.runs_root,
                fixed_clock,
            )
        self.assertEqual(outcome.code, pc_exitcodes.SCANNER_ERROR, "\n".join(outcome.lines))
        self.assertEqual(spy.call_count, 0, "promote was not called")
        self.assertEqual(sorted(os.listdir(ctx.runs_root)), runs_before, "nothing in the runs root")
        self.assertEqual(sorted(os.listdir(os.path.dirname(ctx.destination))), evidence_before, "nothing filed")


class RaceTests(unittest.TestCase):
    def test_two_filings_of_one_run_give_exactly_one_winner_and_one_17(self) -> None:
        import threading

        run = Unfiled()
        contexts = [run.file_context(), run.file_context()]
        barrier = threading.Barrier(2)
        codes = []
        lock = threading.Lock()

        def work(ctx) -> None:
            barrier.wait()
            outcome = evidence().file_row(ctx, run.run_root)
            with lock:
                codes.append(outcome.code)

        threads = [threading.Thread(target=work, args=(ctx,)) for ctx in contexts]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(codes), [0, pc_exitcodes.PROMOTE_REFUSED], "one winner and one refusal")
        self.assertTrue(os.path.isdir(os.path.join(run.run_root, "stage-1")), "stage-1 exists")
        self.assertTrue(os.path.isdir(os.path.join(run.run_root, "stage-2")), "stage-2 exists")
        filed = tree_bytes(run.destination)
        self.assertEqual(filed, tree_bytes(os.path.join(run.run_root, "stage-1")), "one complete tree")
        self.assertEqual(filed, tree_bytes(os.path.join(run.run_root, "stage-2")), "from either stage")


class Harn09ReproofTests(unittest.TestCase):
    """HARN-09 re-proved at zero tokens through the driver (matrix.main), the entry a person types.

    The scripted claude is the only claude; every case also checks its tripwire log. The cases are the routes the
    verification and the review found: a snapshot-path write, a Write-tool path, a commit, a Bash write outside
    the roots that was really written, a Bash expansion-form write, a planted fsmonitor command, a planted clean
    filter and a rewritten hook log.
    """

    def seeded(self) -> list:
        base = pc_testutil.default_row1_stages()
        return [
            ("snapshot-path write", pc_testutil.seed_outside_write(base, 1), None),
            ("write-tool path", pc_testutil.seed_trace_write(base, 1), None),
            ("commit", pc_testutil.seed_git_commit(base, 1), None),
            ("bash write outside, really written", pc_testutil.seed_bash_outside_write(base, 1), None),
            (
                "bash expansion-form write",
                pc_testutil.seed_bash_outside_write(base, 1, command="mkdir ~/x", write_file=False),
                None,
            ),
            ("planted fsmonitor command", pc_testutil.seed_git_config_plant(base, 0, "fsmonitor"), "planted-fsmonitor"),
            ("planted clean filter", pc_testutil.seed_git_config_plant(base, 0, "filter"), "planted-filter"),
            ("rewritten hook log", pc_testutil.seed_run_record_tamper(base, "hooklog"), None),
        ]

    def test_the_clean_control_files_through_the_driver_and_exits_0(self) -> None:
        world = World()
        self.assertEqual(world.code, 0, world.text)
        self.assertTrue(os.path.isdir(world.destination), "the dated folder was created")
        self.assertEqual(world.rig.tripwire(), [], "no other claude was started")
        mechanical = read_text(os.path.join(world.row_dir, "mechanical-checks.md"))
        self.assertIn("bash-write-escapes: 0", mechanical)
        self.assertIn("run-record-changes: 0", mechanical)
        self.assertIn("status-begins-with-session: yes", mechanical)
        usage = read_text(os.path.join(world.row_dir, "usage.txt")).splitlines()
        for stage in ("s1", "s2", "s3"):
            self.assertIn("cumulative-consistent %s: yes" % stage, usage)
        self.assertEqual([line for line in usage if line.startswith("warning")], [], "no warning line")

    def test_each_seeded_failure_ends_with_11_files_nothing_and_leaves_no_marker(self) -> None:
        cases = self.seeded()
        self.assertEqual(len(cases), 8, "eight seeded failures")
        for label, stages, marker in cases:
            world = World(stages=stages)
            self.assertEqual(world.code, pc_exitcodes.PREFLIGHT_FAIL, label + ": " + world.text)
            self.assertIn("isolation or git breach", world.text, label + ": a breach line is printed")
            created = [name for name in os.listdir(world.evidence_dir) if name != "publication-2026-10-20"]
            self.assertEqual(created, [], label + ": nothing was created under tests/evidence")
            self.assertNotIn(world.rig.base, world.text, label + ": no folder of the rig is printed")
            self.assertEqual(world.rig.tripwire(), [], label + ": no other claude was started")
            if marker is not None:
                self.assertFalse(
                    os.path.exists(os.path.join(world.rig.outside, marker)), label + ": the planted command never ran"
                )


class ReadmeTests(unittest.TestCase):
    def readme(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        return read_text(os.path.join(here, "README.md"))

    def test_the_readme_describes_what_a_run_files(self) -> None:
        text = self.readme()
        self.assertIn("### What a run files", text, "the subsection")
        section = text.split("### What a run files", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
        for phrase in ("rerun-", "SKIPPED-", "--refile", "zero tokens", VERDICT_LINE, "raw", "never filed"):
            self.assertIn(phrase, section, "the subsection says: " + phrase)

    def test_the_readme_states_the_new_rules(self) -> None:
        text = self.readme()
        for phrase in (
            "write escape",
            "run record guard",
            "core.fsmonitor=false",
            "first five lines",
            "did not finish cleanly",
            "cumulative-consistent",
        ):
            self.assertIn(phrase, text, "the guide says: " + phrase)
        section = text.split("### What a run files", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
        for phrase in ("rerun-", "SKIPPED-", "--refile", "zero tokens", VERDICT_LINE, "raw", "never filed"):
            self.assertIn(phrase, section, "the subsection still says: " + phrase)
        for phrase in ("did not finish cleanly", "cumulative-consistent", "deny entries"):
            self.assertIn(phrase, section, "the subsection says: " + phrase)

    def test_the_readme_says_a_refile_needs_the_whole_chain(self) -> None:
        text = self.readme()
        self.assertIn("a stage did not run", text, "the guide names the refusal")
        self.assertNotIn("a finished run folder", text, "the old phrase is gone")
        self.assertIn("whole chain", text, "the guide says the chain must be whole")

    def test_the_replacement_tokens_name_the_scratch_token(self) -> None:
        text = self.readme().split("## Replacement tokens", 1)[1].split("\n## ", 1)[0]
        self.assertIn("<scratch>", text, "the scratch token is listed")

    def test_the_two_new_files_are_named_once_each_in_the_layout(self) -> None:
        text = self.readme()
        layout = text.split("\n## Layout\n", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(layout.count("- `pc_evidence.py` - "), 1, "pc_evidence.py once")
        self.assertEqual(layout.count("- `test_evidence.py` - "), 1, "test_evidence.py once")


if __name__ == "__main__":
    unittest.main()
