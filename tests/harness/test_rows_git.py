"""Zero-token tests for the git-shaped rows 8a, 8b, 8c and 9 (plan 04-09; RERUN-02; D-04, Pitfalls 3 and 4).

The four rows share the plain setup (no helper, no wrapper, no ledger, no binding) and the baseline allowlist, and run
the three-stage resume-line chain of row 1. Only the git shape the seed builds differs: no repository at all (8a), a
detached HEAD (8b), an unborn branch (8c) and a linked worktree beside the main checkout (9). These tests prove the
seeds are byte-tied to the committed rows and have the committed git shapes, the state and snapshot code reads the
shapes it could not read before without starting git when it must not, the main checkout's content stays under watch
while its git metadata is left out, and a scripted chain of each row runs through the same engine as every other row.
No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every git process a
test starts is aimed at a folder the test made itself (a run root under the rig or a temporary folder); this
repository's own .git is never named. Folders come from RowRig and are never deleted. Modules are imported inside small
accessors so a missing module is one error per test, not one load failure of the file. Messages that name a path are
never asserted on by value; leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
import uuid
from unittest import mock

import pc_exitcodes
import pc_testutil
from test_row_generic import Registered, tree_names
from test_rows_plain import (
    DATA,
    PLAN_DIGEST,
    SHAPED,
    VERDICT_LINE,
    committed,
    evidence,
    matrix,
    read_bytes,
    read_json,
    read_text,
    row1,
    rowseeds,
    rows,
    sha_lines,
    spec_of,
)

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW8A = "row8a-non-git"
ROW8B = "row8b-detached-head"
ROW8C = "row8c-unborn-branch"
ROW9 = "row9-linked-worktree"
GIT_ROWS = (ROW8A, ROW8B, ROW8C, ROW9)
CLAUDE_MD_DIGEST_PREFIX = "ed03447e9df43888"
PLAN_RELATIVE = "thoughts/plans/2026-10-15-widget-export.md"
DASH = "\u2014"
SHAPE_WORDS = {
    ROW8A: "no-git @ n/a",
    ROW8B: "detached @ abc1234",
    ROW8C: "unborn @ n/a",
    ROW9: "feature/widget-export @ abc1234",
}
GIT_TRIPWIRE_LOG = "git-tripwire.log"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)


def skill_status() -> str:
    """The porcelain status of a project holding only the untracked skill copy: SKILL.md and each reference file.

    The references folder of this repository has grown since the committed runs (the committed status lists the
    three files it held then), so the expected text is built from the folder and the committed lines are a subset.
    """
    names = [".claude/skills/preclear/SKILL.md"]
    names.extend(".claude/skills/preclear/references/" + name for name in sorted(os.listdir(os.path.join(ROOT, "references"))))
    return "".join("?? %s\n" % name for name in sorted(names))


def committed_status_lines(row_id: str) -> list:
    return read_text(committed(row_id, "snap-0-setup", "status.txt")).splitlines()


def make_git_tripwire(directory: str) -> str:
    """Write a git whose every call is a violation (it logs its arguments and exits 97) and return its path."""
    path = os.path.join(directory, "git")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(
            '#!/bin/sh\nhere=$(cd "$(dirname "$0")" && pwd)\nprintf \'%s\\n\' "$*" >> "$here/' + GIT_TRIPWIRE_LOG + '"\nexit 97\n'
        )
    os.chmod(path, 0o755)
    return path


def read_git_tripwire(directory: str) -> list:
    path = os.path.join(directory, GIT_TRIPWIRE_LOG)
    if not os.path.exists(path):
        return []
    return read_text(path).splitlines()


def calls_aimed_at(directory: str, folder: str) -> list:
    """The logged tripwire git calls that name FOLDER (the engine's own calls aimed at the rig repository are not these)."""
    return [line for line in read_git_tripwire(directory) if folder in line]


def real_git_path() -> str:
    import shutil

    found = shutil.which("git", path=os.pathsep.join(pc_testutil.SYSTEM_DIRS))
    assert found is not None, "git is needed for these tests"
    return found


def git_here_init(folder: str) -> None:
    done = git_here(folder, "init", "-q")
    assert done.returncode == 0


def git_here(folder: str, *args: str) -> subprocess.CompletedProcess:
    """Run git against a folder a test made (never this repository) with the hygiene environment of the rig."""
    env = pc_testutil.git_env({"PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS)})
    return subprocess.run(
        ["git", "-C", folder] + list(args),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_out(folder: str, *args: str) -> str:
    done = git_here(folder, *args)
    assert done.returncode == 0, args
    return done.stdout.decode("utf-8")


def resume_line(shape_word: str) -> str:
    """A resume line of the committed shape for a git shape word, as a scripted /preclear reply prints it."""
    return (
        'Resume widget-export from "$PROJECT/.preclear/widget-export/checkpoint.md" '
        + DASH + " " + shape_word + " " + DASH + " step 2 done untested; JSON-default diff pending"
    )


def git_stages(spec, shape_word: str = "detached @ abc1234") -> list:
    """The scripted stages of a clean git-row run: the plain scripts, with the /preclear reply printing a shaped line."""
    stages = pc_testutil.default_row_stages(spec)
    for stage in stages:
        assert "$WRAPPER" not in json.dumps(stage), "a git-row script holds no wrapper op"
    stages[1]["result"] = dict(stages[1]["result"], text="Checkpoint written.\n\n```\n" + resume_line(shape_word) + "\n```\n")
    return stages


def run_git_row(row_id: str, shape_word: str = "detached @ abc1234", stages=None) -> Registered:
    spec = spec_of(row_id)
    return Registered(row_id, stages=stages if stages is not None else git_stages(spec, shape_word))


def dry_run_row(row_id: str):
    """Run the dry run of one row with a tripwire claude on the path; return (code, text, tripwire calls, base)."""
    base = os.path.realpath(tempfile.mkdtemp(prefix="pc-gitrow-"))
    bin_dir = os.path.join(base, "bin")
    os.makedirs(bin_dir)
    pc_testutil.make_tripwire(bin_dir)
    env = {
        "PATH": os.pathsep.join([bin_dir] + list(pc_testutil.SYSTEM_DIRS)),
        "HOME": os.path.join(base, "home"),
        "PRECLEAR_HARNESS_HOME": os.path.join(base, "hh"),
        "PRECLEAR_RUNS_ROOT": os.path.join(base, "runs-root", "runs"),
        "LANG": "en_US.UTF-8",
    }
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started")):
        code = matrix().main(["--dry-run", "--row", row_id], env=env, clock=lambda: FIXED_DATE, out=out, err=err)
    return code, out.getvalue() + err.getvalue(), pc_testutil.read_tripwire(bin_dir), base


class SeededGit(object):
    """A rig, a fresh run root and the paths a git-row seed returns."""

    def __init__(self, row_id: str, name: str = "git-seed-case") -> None:
        self.row_id = row_id
        self.rig = pc_testutil.RowRig(stages=git_stages(spec_of(row_id)))
        self.ctx = self.rig.context()
        self.run_root = self.rig.new_run_root(self.ctx, name)
        self.session = str(uuid.uuid4())
        seed = getattr(rowseeds(), "seed_" + row_id.split("-", 1)[0])
        self.paths = seed(
            self.rig.repo,
            self.run_root,
            self.session,
            self.ctx.harness_home,
            self.ctx.runs_root,
            self.ctx.evidence_date,
            self.ctx.model,
        )

    @property
    def project(self) -> str:
        return str(self.paths["project"])

    def git(self, *args: str) -> str:
        return git_out(self.project, *args)


class GitShapeSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = dict((row_id, SeededGit(row_id, "git-seed-" + row_id.split("-", 1)[0])) for row_id in GIT_ROWS)

    def test_8b_the_seeded_claude_md_equals_the_committed_fixture_and_its_setup_digest(self) -> None:
        seeded = self.seeded[ROW8B]
        data = read_bytes(os.path.join(seeded.project, "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW8B, "fixture-CLAUDE.md")), "byte for byte")
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, sha_lines(ROW8B)["project/CLAUDE.md"])
        self.assertTrue(digest.startswith(CLAUDE_MD_DIGEST_PREFIX))

    def test_8b_the_plan_equals_the_plain_data_file_and_hashes_to_the_committed_digest(self) -> None:
        seeded = self.seeded[ROW8B]
        data = read_bytes(os.path.join(seeded.project, *PLAN_RELATIVE.split("/")))
        self.assertEqual(data, read_bytes(os.path.join(DATA, "plain-plan.md")))
        self.assertEqual(hashlib.sha256(data).hexdigest(), PLAN_DIGEST)
        self.assertEqual(hashlib.sha256(data).hexdigest(), sha_lines(ROW8B)["project/" + PLAN_RELATIVE])

    def test_8b_two_commits_on_main_and_a_detached_head_at_the_first(self) -> None:
        seeded = self.seeded[ROW8B]
        self.assertEqual(seeded.git("rev-list", "--count", "main").strip(), "2", "two commits on main")
        first = seeded.git("rev-parse", "main~1").strip()
        self.assertEqual(seeded.git("rev-parse", "HEAD").strip(), first, "HEAD is the first commit")
        self.assertEqual(git_here(seeded.project, "symbolic-ref", "-q", "HEAD").returncode, 1, "HEAD is detached")
        self.assertEqual(seeded.git("rev-list", "--count", "HEAD").strip(), "1")

    def test_8b_the_second_commit_adds_notes_and_the_work_tree_holds_no_notes_file(self) -> None:
        seeded = self.seeded[ROW8B]
        names = rowseeds().NOTES_NAME
        self.assertEqual(seeded.git("diff", "--name-only", "main~1", "main").split(), [names])
        self.assertFalse(os.path.lexists(os.path.join(seeded.project, names)), "the detached work tree has no NOTES.md")
        self.assertEqual(seeded.git("ls-files").split(), ["CLAUDE.md", PLAN_RELATIVE])

    def test_8b_the_skill_copy_is_untracked_and_the_status_equals_the_committed_setup_status(self) -> None:
        seeded = self.seeded[ROW8B]
        status = seeded.git("status", "--porcelain=v1", "--untracked-files=all")
        self.assertEqual(status, skill_status())
        for line in committed_status_lines(ROW8B):
            self.assertIn(line, status.splitlines(), "every committed status line is still there")
        skill = os.path.join(seeded.paths["skill_dir"], "SKILL.md")
        self.assertEqual(read_bytes(skill), read_bytes(os.path.join(ROOT, "SKILL.md")))

    def test_8b_the_commits_carry_the_spike_identity_and_no_machine_identity(self) -> None:
        seeded = self.seeded[ROW8B]
        people = seeded.git("log", "main", "--format=%an <%ae>|%cn <%ce>").split("\n")
        for line in people:
            if line:
                self.assertEqual(line, "Harness Spike <harness-spike@example.com>|Harness Spike <harness-spike@example.com>")

    def test_8b_the_run_root_holds_no_wrapper_ledger_or_binding_and_the_record_names_the_row(self) -> None:
        seeded = self.seeded[ROW8B]
        self.assertFalse(os.path.lexists(os.path.join(seeded.run_root, "wrapper")))
        self.assertEqual(os.listdir(str(seeded.paths["ledgers"])), [])
        record = read_json(os.path.join(seeded.run_root, "raw", "run.json"))
        self.assertEqual(record["row"], ROW8B)
        self.assertEqual(record["memory"], "pinned")
        self.assertEqual(record["bound_ledger"], "none")

    def test_the_seed_refuses_a_shape_word_it_does_not_know_and_a_second_call_on_the_same_run_root(self) -> None:
        seeded = self.seeded[ROW8B]
        rs = rowseeds()
        with self.assertRaises(ValueError):
            rs.seed_git_row(
                "bogus", seeded.rig.repo, seeded.run_root, str(uuid.uuid4()), seeded.ctx.harness_home,
                seeded.ctx.runs_root, seeded.ctx.evidence_date, seeded.ctx.model, ROW8B,
                rs.ROW8B_FOLDER + "/fixture-CLAUDE.md", "pinned",
            )
        with self.assertRaises(FileExistsError):
            rs.seed_row8b(
                seeded.rig.repo, seeded.run_root, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root,
                seeded.ctx.evidence_date, seeded.ctx.model,
            )

    def test_the_shape_words_are_the_five_of_plan_04_09_and_large_of_plan_04_10(self) -> None:
        self.assertEqual(
            rowseeds().GIT_SHAPES, ("commit", "detached", "unborn", "none", "worktree", "large")
        )


class GitRegistryTests(unittest.TestCase):
    def test_each_git_row_is_registered_with_the_three_committed_stages_the_git_profile_and_the_resume_line_chain(self) -> None:
        pc_rows = rows()
        for row_id in GIT_ROWS:
            spec = spec_of(row_id)
            self.assertTrue(spec.implemented, row_id)
            self.assertEqual(
                [(s.name, s.max_turns, str(s.cap), s.timeout, s.session) for s in spec.stages],
                [("s1", 15, "0.30", 900, "new:A"), ("s2", 60, "1.30", 1800, "resume:A"), ("s3", 15, "0.40", 900, "new:B")],
            )
            self.assertEqual(spec.tools_profile, pc_rows.PROFILE_GIT)
            self.assertEqual(spec.extra_tools, ())
            self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
            self.assertEqual(spec.chain, pc_rows.CHAIN_RESUME_LINE)
            self.assertEqual(spec.hooks, ())
            self.assertEqual(spec.probe, pc_rows.PROBE_NONE)
            self.assertEqual(spec.analyses, ())
            self.assertEqual(spec.seed, "pc_rowseeds:seed_" + row_id.split("-", 1)[0])
            self.assertTrue(spec.setup_text.startswith("Setup: "))

    def test_the_git_profile_word_of_the_registry_and_of_the_flag_module_agree(self) -> None:
        import pc_flags

        self.assertEqual(rows().PROFILE_GIT, pc_flags.PROFILE_GIT)

    def test_the_dry_run_of_each_git_row_prints_the_plan_and_starts_no_process(self) -> None:
        for row_id in GIT_ROWS:
            code, text, tripwire, base = dry_run_row(row_id)
            self.assertEqual(code, 0, text)
            self.assertIn("%s: 3 stages, 2 sessions" % row_id, text)
            lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
            self.assertEqual(len(lines), 3)
            for line, turns, cap in zip(lines, ("15 turns", "60 turns", "15 turns"), ("cap 0.30", "cap 1.30", "cap 0.40")):
                self.assertIn(turns, line)
                self.assertIn(cap, line)
            self.assertIn("worst case 2.00 USD", text)
            self.assertIn("allowlist 33 rules", text)
            self.assertEqual(tripwire, [])
            self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")

    def test_list_marks_each_git_row_implemented_with_three_stages_and_two_sessions(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        for row_id in GIT_ROWS:
            self.assertEqual(cells[row_id][2:], ["3", "2", "yes"], row_id)

    def test_the_setup_texts_hold_no_path_shaped_string_and_8a_names_its_difference_from_the_committed_run(self) -> None:
        for row_id in GIT_ROWS:
            self.assertIsNone(SHAPED.search(spec_of(row_id).setup_text), row_id)
        text = spec_of(ROW8A).setup_text
        self.assertIn("no `.git` entry", text)
        self.assertIn("no repository above", text.replace("run root lies under no repository either", "no repository above"))
        self.assertIn("differs from the committed run", text)


class NoGitStateTests(unittest.TestCase):
    """A project with no .git has a defined, pinned git state and starts no git process (Pitfall 3, T-04-39, T-04-40)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-nogit-"))
        cls.bin = os.path.join(cls.base, "bin")
        os.makedirs(cls.bin)
        cls.git_tripwire = make_git_tripwire(cls.bin)

    def project(self, name: str) -> str:
        folder = os.path.join(self.base, name)
        os.makedirs(folder)
        with open(os.path.join(folder, "file.txt"), "w", encoding="utf-8") as handle:
            handle.write("a plain file\n")
        return folder

    def tripped(self) -> list:
        return read_git_tripwire(self.bin)

    def test_the_marker_digest_is_a_fixed_64_hex_value_equal_to_the_hash_of_its_marker_text(self) -> None:
        import pc_manifest

        self.assertRegex(pc_manifest.NO_GIT_DIGEST, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(pc_manifest.NO_GIT_DIGEST, hashlib.sha256(pc_manifest._NO_GIT_MARKER).hexdigest())
        self.assertNotEqual(pc_manifest.NO_GIT_DIGEST, hashlib.sha256(b"").hexdigest())

    def test_gitdir_digest_of_a_project_with_no_git_entry_is_the_marker_digest(self) -> None:
        import pc_manifest

        self.assertEqual(pc_manifest.gitdir_digest(self.project("digest-none")), pc_manifest.NO_GIT_DIGEST)

    def test_gitdir_digest_of_a_git_folder_is_unchanged_and_never_the_marker(self) -> None:
        import pc_manifest

        folder = self.project("digest-folder")
        git_here_init(folder)
        entries = pc_manifest.tree_manifest(os.path.join(folder, ".git"))
        kept = [e for e in entries if e["path"] not in (b"index", b"index.lock")]
        expected = hashlib.sha256(pc_manifest.jsonl_bytes(kept)).hexdigest()
        self.assertEqual(pc_manifest.gitdir_digest(folder), expected)
        self.assertNotEqual(expected, pc_manifest.NO_GIT_DIGEST)

    def test_a_symlinked_a_special_and_an_unreadable_git_entry_are_refused_never_guessed_at(self) -> None:
        import pc_manifest

        linked = self.project("digest-link")
        target = os.path.join(self.base, "link-target")
        os.makedirs(target)
        os.symlink(target, os.path.join(linked, ".git"))
        special = self.project("digest-fifo")
        os.mkfifo(os.path.join(special, ".git"))
        garbage = self.project("digest-garbage")
        with open(os.path.join(garbage, ".git"), "w", encoding="utf-8") as handle:
            handle.write("not a pointer\n")
        for folder in (linked, special, garbage):
            with self.assertRaises(pc_manifest.ManifestError):
                pc_manifest.gitdir_digest(folder)

    def test_a_project_that_is_itself_a_link_or_missing_is_refused_and_an_unreadable_entry_is_the_named_error(self) -> None:
        import pc_manifest

        folder = self.project("digest-real")
        link = os.path.join(self.base, "digest-project-link")
        os.symlink(folder, link)
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.gitdir_digest(link)
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.gitdir_digest(os.path.join(self.base, "digest-missing"))
        garbage = self.project("digest-garbage-class")
        with open(os.path.join(garbage, ".git"), "w", encoding="utf-8") as handle:
            handle.write("not a pointer\n")
        with self.assertRaises(pc_manifest.GitEntryUnreadable):
            pc_manifest.gitdir_digest(garbage)
        self.assertTrue(issubclass(pc_manifest.GitEntryUnreadable, pc_manifest.ManifestError))
        self.assertFalse(issubclass(pc_manifest.GitEntryUnreadable, pc_manifest.GitDirChanged))

    def test_a_pinned_capture_in_a_no_git_project_where_a_garbage_git_file_appeared_is_a_change_not_a_crash(self) -> None:
        import pc_manifest

        folder = self.project("garbage-appeared")
        pin = pc_manifest.gitdir_digest(folder)
        with open(os.path.join(folder, ".git"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        before = self.tripped()
        with self.assertRaises(pc_manifest.GitDirChanged):
            pc_manifest.capture_git_status(folder, self.git_tripwire, pin)
        self.assertEqual(self.tripped(), before)

    def test_git_state_of_a_no_git_project_is_na_with_the_empty_refs_digest_and_the_marker_and_starts_no_process(self) -> None:
        import pc_checks
        import pc_manifest

        folder = self.project("state-none")
        before = self.tripped()
        for pinned in (None, pc_manifest.NO_GIT_DIGEST):
            state = pc_checks.git_state(folder, self.git_tripwire, pinned)
            self.assertEqual(
                state,
                {
                    "head": "n/a",
                    "branch": "n/a",
                    "refs_digest": hashlib.sha256(b"").hexdigest(),
                    "gitdir_digest": pc_manifest.NO_GIT_DIGEST,
                    "staged": 0,
                },
            )
        self.assertEqual(self.tripped(), before, "a tripwire git on the path stayed silent")

    def test_capture_git_status_of_a_no_git_project_returns_the_fixed_line_and_starts_no_process(self) -> None:
        import pc_manifest

        folder = self.project("status-none")
        before = self.tripped()
        for pinned in (None, pc_manifest.NO_GIT_DIGEST):
            raw, text = pc_manifest.capture_git_status(folder, self.git_tripwire, pinned)
            self.assertEqual(raw, b"")
            self.assertEqual(text, (pc_manifest.NO_GIT_STATUS_LINE + "\n").encode("utf-8"))
        self.assertEqual(self.tripped(), before)

    def test_a_pinned_capture_refuses_a_git_entry_that_appeared_after_the_pin_and_starts_no_process(self) -> None:
        import pc_checks
        import pc_manifest

        folder = self.project("appeared")
        pin = pc_manifest.gitdir_digest(folder)
        os.makedirs(os.path.join(folder, ".git"))
        with open(os.path.join(folder, ".git", "config"), "w", encoding="utf-8") as handle:
            handle.write("[core]\n")
        before = self.tripped()
        with self.assertRaises(pc_manifest.GitDirChanged):
            pc_manifest.capture_git_status(folder, self.git_tripwire, pin)
        state = pc_checks.git_state(folder, self.git_tripwire, pin)
        self.assertEqual(self.tripped(), before, "no git process was started")
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], pc_checks.GIT_NOT_READ, key)
        self.assertNotEqual(state["gitdir_digest"], pin)
        setup = pc_checks.git_state(self.project("appeared-twin"), self.git_tripwire, None)
        mutations = pc_checks.git_mutations([setup, state], [])
        self.assertEqual(mutations["changed_fields"], list(pc_checks.GIT_STATE_FIELDS), "all four fields changed")
        self.assertGreater(mutations["total"], 0, "the existing mutation rule counts a planted .git")

    def test_a_nested_repository_in_a_no_git_project_is_refused_before_any_process(self) -> None:
        import pc_manifest

        folder = self.project("nested")
        os.makedirs(os.path.join(folder, "inner", ".git"))
        before = self.tripped()
        with self.assertRaises(pc_manifest.NestedRepository):
            pc_manifest.capture_git_status(folder, self.git_tripwire, None)
        self.assertEqual(self.tripped(), before)

    def test_an_unpinned_status_in_a_folder_with_an_empty_git_folder_still_fails_as_before(self) -> None:
        import pc_manifest

        folder = self.project("empty-git-folder")
        os.makedirs(os.path.join(folder, ".git"))
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.capture_git_status(folder, real_git_path(), None)


class GitShapeStateTests(unittest.TestCase):
    """The state and snapshot of the detached and unborn shapes come from the same code as a plain repository."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = {row: SeededGit(row, "git-state-" + row.split("-", 1)[0]) for row in (ROW8B, ROW8C)}

    def state(self, row_id: str) -> dict:
        import pc_checks

        return pc_checks.git_state(self.seeded[row_id].project, real_git_path(), None)

    def test_the_detached_state_has_a_head_and_no_branch(self) -> None:
        state = self.state(ROW8B)
        self.assertRegex(state["head"], r"\A[0-9a-f]{40}\Z")
        self.assertEqual(state["branch"], "")
        self.assertEqual(state["staged"], 0)

    def test_the_unborn_state_has_no_head_and_the_main_branch_and_an_empty_reference_list(self) -> None:
        import pc_checks

        state = self.state(ROW8C)
        self.assertEqual(state["head"], "")
        self.assertEqual(state["branch"], "refs/heads/main")
        self.assertEqual(state["refs_digest"], hashlib.sha256(b"").hexdigest())
        self.assertEqual(state["staged"], 0)
        self.assertNotEqual(state["gitdir_digest"], pc_checks.pc_manifest.NO_GIT_DIGEST)

    def test_the_status_of_a_plain_status_call_never_moves_the_digest(self) -> None:
        import pc_checks

        for row_id in (ROW8B, ROW8C):
            before = self.state(row_id)
            git_out(self.seeded[row_id].project, "status")
            self.assertEqual(self.state(row_id), before, row_id)
            self.assertEqual(pc_checks.git_mutations([before, self.state(row_id)], [])["total"], 0)


class GitRowChainTests(unittest.TestCase):
    """A scripted chain of each git row through the same engine as every other row."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runs = {}
        for row_id in GIT_ROWS:
            cls.runs[row_id] = run_git_row(row_id, SHAPE_WORDS[row_id])
            assert cls.runs[row_id].outcome.code == 0, row_id + "\n" + "\n".join(cls.runs[row_id].outcome.lines)

    def read(self, row_id: str, name: str) -> str:
        return read_text(os.path.join(self.runs[row_id].row_dir, name))

    def test_a_scripted_chain_of_each_row_completes_with_three_launches_and_no_wrapper_folder(self) -> None:
        for row_id in GIT_ROWS:
            run = self.runs[row_id]
            key = row_id.split("-", 1)[0]
            self.assertEqual(len(run.rig.calls()), 3, "each stage is launched exactly once")
            self.assertFalse(os.path.lexists(os.path.join(run.run_root, "wrapper")), "no wrapper folder")
            self.assertEqual(
                [(r["kind"], r["stage"]) for r in run.ledger()],
                [(kind, "%s-%s" % (key, stage)) for stage in ("s1", "s2", "s3") for kind in ("launch", "settle")],
            )
            self.assertEqual(os.listdir(run.ctx.destination), [row_id])

    def test_the_stage_commands_carry_the_33_baseline_rules_alone_and_the_pinned_memory_switch(self) -> None:
        import pc_flags

        for row_id in GIT_ROWS:
            run = self.runs[row_id]
            for call in run.rig.calls():
                argv = call["args"]
                rules = argv[argv.index("--allowedTools") + 1].split(",")
                self.assertEqual(rules, list(pc_flags.BASELINE_ALLOWED_TOOLS))
                self.assertEqual(len(rules), 33)
            first = run.rig.calls()[0]
            settings_path = first["args"][first["args"].index("--settings") + 1]
            self.assertIs(read_json(settings_path)["autoMemoryEnabled"], True)
            self.assertEqual(first["prompt"].encode("utf-8"), read_bytes(os.path.join(DATA, "plain-s1-prompt.md")))
            self.assertEqual(
                run.rig.calls()[1]["prompt"].encode("utf-8"), read_bytes(committed(row_id, "s2-preclear-prompt.md"))
            )

    def test_the_third_stage_is_a_fresh_session_fed_the_resume_line_the_second_printed(self) -> None:
        for row_id in GIT_ROWS:
            run = self.runs[row_id]
            calls = run.rig.calls()
            prompt = calls[2]["prompt"]
            self.assertTrue(prompt.startswith("Resume "))
            self.assertTrue(prompt.endswith(" step 2 done untested; JSON-default diff pending"))
            self.assertIn(DASH + " " + SHAPE_WORDS[row_id] + " " + DASH, prompt)
            self.assertEqual(
                self.read(row_id, "resume-line.txt").rstrip("\n").replace("<run>", "$RUNROOT"),
                prompt.replace(run.run_root, "$RUNROOT"),
            )
            self.assertNotIn("--resume", calls[2]["args"], "s3 starts a new session")
            self.assertIn("--resume", calls[1]["args"], "s2 continues the session of s1")

    def test_8b_the_resume_line_ends_with_detached_at_and_seven_hex_characters_before_the_dash(self) -> None:
        prompt = self.runs[ROW8B].rig.calls()[2]["prompt"]
        self.assertIsNotNone(re.search(r"detached @ [0-9a-f]{7} " + DASH, prompt), prompt)

    def test_s3_makes_no_write_or_edit_call_and_the_s2_and_s3_snapshots_hash_alike(self) -> None:
        for row_id in GIT_ROWS:
            self.assertIn("Write/Edit calls 0: []", self.read(row_id, "s3-resume-trace.md"))
            self.assertEqual(
                self.read(row_id, "snap-2-after-preclear/sha.txt"), self.read(row_id, "snap-3-after-resume/sha.txt")
            )

    def test_the_filed_folder_holds_the_committed_file_names_and_the_s3_files_and_no_helper_file(self) -> None:
        for row_id in GIT_ROWS:
            names = tree_names(self.runs[row_id].row_dir)
            for expected in (
                "README.md", "claude-version.txt", "digests.txt", "fixture-CLAUDE.md", "measurements.md",
                "mechanical-checks.md", "resume-line.txt", "s1-work.out", "s1.err", "s1.exit",
                "s2-preclear-full-trace.md", "s2-preclear-prompt.md", "s2-preclear-trace.md", "s2-preclear.err",
                "s2-preclear.exit", "s3-resume-full-trace.md", "s3-resume-trace.md", "s3-resume.err",
                "s3-resume.exit", "session-resume.id", "session.id", "settings.json", "snap-0-setup/",
                "snap-1-after-work/", "snap-2-after-preclear/", "snap-3-after-resume/", "tools.txt", "usage.txt",
            ):
                self.assertIn(expected, names, row_id + " " + expected)
            for absent in ("wrapper-calls.log", "wrapper-checkpoint.sh", "status-before.txt", "lint-before.txt"):
                self.assertNotIn(absent, names, absent)

    def test_the_filed_project_file_equals_the_committed_one_and_tools_are_the_33_rules(self) -> None:
        import pc_flags

        for row_id in GIT_ROWS:
            self.assertEqual(self.read(row_id, "fixture-CLAUDE.md"), read_text(committed(row_id, "fixture-CLAUDE.md")))
            self.assertEqual(self.read(row_id, "tools.txt"), ",".join(pc_flags.BASELINE_ALLOWED_TOOLS) + "\n")

    def test_the_setup_snapshot_lists_the_project_files_and_never_a_git_entry_of_the_project(self) -> None:
        for row_id in GIT_ROWS:
            listing = self.read(row_id, "snap-0-setup/sha.txt")
            self.assertIn("project/CLAUDE.md", listing)
            self.assertIn("project/" + PLAN_RELATIVE, listing)
            self.assertNotIn("NOTES.md", listing)
            self.assertNotIn("project/.git", listing, "the git folder is left out of the manifest")
            self.assertNotIn("wrapper", listing)
            self.assertNotIn("CONTINUITY", listing)

    def test_8b_the_setup_status_is_the_committed_untracked_skill_list(self) -> None:
        self.assertEqual(self.read(ROW8B, "snap-0-setup/status.txt"), skill_status())

    def test_8c_every_file_is_untracked_in_the_setup_status_and_the_committed_lines_are_all_there(self) -> None:
        lines = sorted(self.read(ROW8C, "snap-0-setup/status.txt").splitlines())
        self.assertEqual(lines, sorted(skill_status().splitlines() + ["?? CLAUDE.md", "?? " + PLAN_RELATIVE]))
        for line in committed_status_lines(ROW8C):
            self.assertIn(line, lines)

    def test_8a_the_setup_snapshot_status_is_the_fixed_no_git_line_and_the_raw_status_is_empty(self) -> None:
        import pc_manifest

        run = self.runs[ROW8A]
        for name in ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"):
            self.assertEqual(self.read(ROW8A, name + "/status.txt"), pc_manifest.NO_GIT_STATUS_LINE + "\n", name)
            self.assertEqual(os.path.getsize(os.path.join(run.run_root, "snaps", name, "status.raw")), 0, name)
        self.assertEqual(row1().STATUS_NO_GIT, pc_manifest.NO_GIT_STATUS_LINE)

    def test_8a_the_git_facts_are_na_at_every_boundary_with_zero_mutations(self) -> None:
        text = self.read(ROW8A, "mechanical-checks.md")
        self.assertIn("states: 4", text)
        for name in ("setup", "s1", "s2", "s3"):
            self.assertIn("state %s: head n/a, branch n/a, staged 0" % name, text)
        self.assertIn("mutations-total: 0", text)
        self.assertIn("mutation-changed-fields: none", text)

    def test_8b_and_8c_the_git_facts_are_a_fixed_head_and_zero_mutations(self) -> None:
        for row_id in (ROW8B, ROW8C):
            text = self.read(row_id, "mechanical-checks.md")
            self.assertIn("states: 4", text)
            self.assertIn("mutations-total: 0", text)
            self.assertIn("mutation-changed-fields: none", text)
        heads = set(re.findall(r"^state \S+: head (\S+),", self.read(ROW8B, "mechanical-checks.md"), re.M))
        self.assertEqual(len(heads), 1, "the detached HEAD never moves")
        self.assertRegex(next(iter(heads)), r"\A[0-9a-f]{40}\Z")
        unborn = set(re.findall(r"^state \S+: head (\S+),", self.read(ROW8C, "mechanical-checks.md"), re.M))
        self.assertEqual(unborn, {"UNCONFIRMED"}, "an unborn branch has no head, said in the harness's own word")

    def test_each_readme_ends_with_the_pending_line_holds_no_verdict_word_and_no_path(self) -> None:
        pattern = evidence().verdict_pattern()
        for row_id in GIT_ROWS:
            text = self.read(row_id, "README.md")
            self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"))
            self.assertEqual(text.count(VERDICT_LINE), 1)
            body = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(body), "no verdict word in the README")
            self.assertIn(spec_of(row_id).setup_text, body, "the Setup paragraph is the registry text")
            self.assertIsNone(SHAPED.search(body))
            self.assertNotIn(self.runs[row_id].rig.base, body)

    def test_no_harness_authored_file_of_a_git_row_holds_a_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        for row_id in GIT_ROWS:
            run = self.runs[row_id]
            names = []
            for dirpath, _dirnames, filenames in os.walk(run.ctx.destination):
                for name in filenames:
                    names.append(os.path.relpath(os.path.join(dirpath, name), run.ctx.destination).replace(os.sep, "/"))
            authored = evidence().harness_authored_names(sorted(names))
            self.assertGreater(len(authored), 8)
            for name in authored:
                text = read_text(os.path.join(run.ctx.destination, name))
                if name == row_id + "/README.md":
                    text = text[: -len(VERDICT_LINE) - 1]
                self.assertIsNone(pattern.search(text), "no verdict word in " + name)

    def test_a_reply_without_a_resume_line_ends_the_chain_after_the_second_stage(self) -> None:
        spec = spec_of(ROW8B)
        stages = pc_testutil.default_row_stages(spec)
        stages[1]["result"] = dict(stages[1]["result"], text="Checkpoint written, no resume line.")
        run = run_git_row(ROW8B, stages=stages)
        self.assertEqual(len(run.rig.calls()), 2, "the chain ends there; no resume line is invented")


class NoGitChainTests(unittest.TestCase):
    """Row 8a through the engine with a tripwire git first on the path: no git process starts for the project."""

    def run_with_tripwire(self, stages) -> tuple:
        rig = pc_testutil.RowRig(stages=stages)
        tripwire = make_git_tripwire(rig.bin)
        run = Registered(ROW8A, rig=rig)
        return run, tripwire, rig

    def test_a_clean_8a_chain_never_starts_git_and_files_the_row(self) -> None:
        run, _tripwire, rig = self.run_with_tripwire(git_stages(spec_of(ROW8A), SHAPE_WORDS[ROW8A]))
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertEqual(calls_aimed_at(rig.bin, run.run_root), [], "no git process was started for the run root")
        self.assertFalse(os.path.lexists(os.path.join(run.run_root, "project", ".git")))
        self.assertEqual(os.listdir(run.ctx.destination), [ROW8A])

    def test_a_scripted_s2_that_plants_a_git_folder_is_counted_stops_with_11_and_starts_no_git(self) -> None:
        stages = git_stages(spec_of(ROW8A), SHAPE_WORDS[ROW8A])
        stages = pc_testutil.stages_with(stages, 1, ops=list(stages[1]["ops"]) + [
            {"op": "write", "path": "$PROJECT/.git/config", "text": "[core]\n\tfsmonitor = false\n"},
        ])
        run, _tripwire, rig = self.run_with_tripwire(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(calls_aimed_at(rig.bin, run.run_root), [], "git was not started for the planted folder")
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW8A])
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: git mutations: [1-9][0-9]*")
        self.assertNotIn(rig.base, text)
        state = read_json(os.path.join(run.run_root, "raw", "s2.git.json"))
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], "not-read", key)
        snapshot = read_text(os.path.join(run.run_root, "snaps", "snap-2-after-preclear", "status.txt"))
        self.assertEqual(snapshot.strip(), row1().STATUS_NOT_RUN, "the fixed not-run line, not the no-git line")

    def test_a_scripted_s1_that_plants_a_nested_git_folder_never_starts_git_either(self) -> None:
        stages = git_stages(spec_of(ROW8A), SHAPE_WORDS[ROW8A])
        stages = pc_testutil.stages_with(stages, 0, ops=list(stages[0]["ops"]) + [
            {"op": "write", "path": "$PROJECT/inner/.git/config", "text": "[core]\n"},
        ])
        run, _tripwire, rig = self.run_with_tripwire(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(calls_aimed_at(rig.bin, run.run_root), [], "git was not started for the nested folder")
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW8A])
        state = read_json(os.path.join(run.run_root, "raw", "s1.git.json"))
        self.assertEqual(state["head"], "not-read")


class ShapeSeedTests(unittest.TestCase):
    """The git shape of each seed equals the committed setup facts of its row (rows 8a, 8c and 9; 8b is above)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = dict((row_id, SeededGit(row_id, "git-shape-" + row_id.split("-", 1)[0])) for row_id in GIT_ROWS)

    def project(self, row_id: str) -> str:
        return self.seeded[row_id].project

    def test_every_seed_is_byte_tied_to_its_committed_project_file_and_plain_plan(self) -> None:
        for row_id in GIT_ROWS:
            data = read_bytes(os.path.join(self.project(row_id), "CLAUDE.md"))
            self.assertEqual(data, read_bytes(committed(row_id, "fixture-CLAUDE.md")), row_id)
            digest = hashlib.sha256(data).hexdigest()
            self.assertEqual(digest, sha_lines(row_id)["project/CLAUDE.md"], row_id)
            self.assertTrue(digest.startswith(CLAUDE_MD_DIGEST_PREFIX), "the digest rows 6 to 12 share")
            plan = read_bytes(os.path.join(self.project(row_id), *PLAN_RELATIVE.split("/")))
            self.assertEqual(plan, read_bytes(os.path.join(DATA, "plain-plan.md")), row_id)
            self.assertEqual(hashlib.sha256(plan).hexdigest(), PLAN_DIGEST)

    def test_every_seed_is_byte_tied_to_the_committed_row_s2_prompt_and_skill_copy(self) -> None:
        for row_id in GIT_ROWS:
            skill = os.path.join(self.seeded[row_id].paths["skill_dir"], "SKILL.md")
            self.assertEqual(read_bytes(skill), read_bytes(os.path.join(ROOT, "SKILL.md")), row_id)
            self.assertEqual(
                read_bytes(committed(row_id, "s2-preclear-prompt.md")),
                read_bytes(committed(ROW8B, "s2-preclear-prompt.md")),
                "the four committed prompts are one text",
            )

    def test_every_seed_commits_with_the_spike_identity_only(self) -> None:
        for row_id in (ROW8B, ROW9):
            folder = self.project(row_id)
            for line in git_out(folder, "log", "--all", "--format=%an <%ae>|%cn <%ce>").splitlines():
                self.assertEqual(line, "Harness Spike <harness-spike@example.com>|Harness Spike <harness-spike@example.com>")

    def test_8c_a_repository_on_main_with_no_commit_and_everything_untracked(self) -> None:
        folder = self.project(ROW8C)
        self.assertEqual(read_text(os.path.join(folder, ".git", "HEAD")).strip(), "ref: refs/heads/main")
        self.assertNotEqual(git_here(folder, "rev-parse", "--verify", "-q", "HEAD").returncode, 0, "no commit")
        self.assertEqual(git_out(folder, "rev-list", "--all", "--count").strip(), "0")
        self.assertEqual(git_out(folder, "ls-files"), "", "nothing is tracked")
        self.assertEqual(git_out(folder, "symbolic-ref", "HEAD").strip(), "refs/heads/main")
        lines = git_out(folder, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        self.assertTrue(lines and all(line.startswith("?? ") for line in lines), "everything is untracked")
        self.assertEqual(sorted(lines), sorted(skill_status().splitlines() + ["?? CLAUDE.md", "?? " + PLAN_RELATIVE]))
        for line in committed_status_lines(ROW8C):
            self.assertIn(line, lines, "every committed status line is there")

    def test_8a_the_project_has_no_git_entry_and_the_run_root_holds_none_anywhere(self) -> None:
        seeded = self.seeded[ROW8A]
        self.assertFalse(os.path.lexists(os.path.join(seeded.project, ".git")))
        found = []
        for dirpath, dirnames, filenames in os.walk(seeded.run_root):
            found.extend(name for name in list(dirnames) + list(filenames) if name.lower() == ".git")
        self.assertEqual(found, [], "no repository metadata anywhere under the run root")
        self.assertEqual(
            sorted(os.listdir(seeded.project)), [".claude", "CLAUDE.md", "thoughts"], "the files and the skill copy only"
        )

    def test_9_the_main_checkout_holds_the_repository_with_the_files_committed_on_main(self) -> None:
        seeded = self.seeded[ROW9]
        main = os.path.join(seeded.run_root, "main-checkout")
        self.assertTrue(os.path.isdir(os.path.join(main, ".git")), "a real git folder")
        self.assertEqual(git_out(main, "symbolic-ref", "HEAD").strip(), "refs/heads/main")
        self.assertEqual(git_out(main, "rev-list", "--count", "main").strip(), "1")
        self.assertEqual(git_out(main, "ls-files").split(), ["CLAUDE.md", PLAN_RELATIVE])
        self.assertEqual(
            read_bytes(os.path.join(main, "CLAUDE.md")), read_bytes(committed(ROW9, "fixture-CLAUDE.md"))
        )
        listing = sha_lines(ROW9)
        for name in ("CLAUDE.md", PLAN_RELATIVE):
            digest = hashlib.sha256(read_bytes(os.path.join(main, *name.split("/")))).hexdigest()
            self.assertEqual(digest, listing["main-checkout/" + name], name)
        self.assertFalse(os.path.lexists(os.path.join(main, ".claude")), "the skill copy sits in the project only")

    def test_9_the_project_is_a_linked_worktree_on_the_feature_branch_whose_git_entry_is_a_file(self) -> None:
        seeded = self.seeded[ROW9]
        pointer = os.path.join(seeded.project, ".git")
        self.assertTrue(os.path.isfile(pointer) and not os.path.islink(pointer))
        self.assertEqual(read_text(pointer).count("\n"), 1)
        self.assertTrue(read_text(pointer).startswith("gitdir: "))
        self.assertEqual(git_out(seeded.project, "symbolic-ref", "HEAD").strip(), "refs/heads/feature/widget-export")
        main = os.path.join(seeded.run_root, "main-checkout")
        self.assertEqual(git_out(seeded.project, "rev-parse", "HEAD"), git_out(main, "rev-parse", "main"))
        worktrees = [line for line in git_out(main, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")]
        self.assertEqual(len(worktrees), 2, "the main checkout and one linked worktree")
        self.assertEqual(git_out(seeded.project, "ls-files").split(), ["CLAUDE.md", PLAN_RELATIVE])
        self.assertEqual(
            git_out(seeded.project, "status", "--porcelain=v1", "--untracked-files=all"), skill_status(),
            "the skill copy is the only untracked thing",
        )
        for line in committed_status_lines(ROW9):
            self.assertIn(line, skill_status().splitlines())

    def test_9_the_worktree_was_made_by_worktree_add_and_the_branch_is_not_main(self) -> None:
        seeded = self.seeded[ROW9]
        main = os.path.join(seeded.run_root, "main-checkout")
        branches = git_out(main, "branch", "--format=%(refname:short)").split()
        self.assertEqual(sorted(branches), ["feature/widget-export", "main"])
        self.assertTrue(os.path.isdir(os.path.join(main, ".git", "worktrees", "project")))


class WorktreeStateTests(unittest.TestCase):
    """The git state of a linked worktree: pointer, own git folder and common git folder, no index entry (FA-1, T-04-40)."""

    def setUp(self) -> None:
        self.seeded = SeededGit(ROW9, "git-worktree-state")
        self.main = os.path.join(self.seeded.run_root, "main-checkout")
        self.project = self.seeded.project
        self.worktree_git = os.path.join(self.main, ".git", "worktrees", "project")
        base = os.path.dirname(self.seeded.run_root)
        self.bin = os.path.join(base, "tripwire-bin")
        os.makedirs(self.bin, exist_ok=True)
        self.tripwire = make_git_tripwire(self.bin)

    def digest(self) -> str:
        import pc_manifest

        return pc_manifest.gitdir_digest(self.project)

    def test_the_digest_is_a_fixed_64_hex_value_that_is_neither_the_marker_nor_a_folder_digest(self) -> None:
        import pc_manifest

        value = self.digest()
        self.assertRegex(value, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(value, self.digest(), "stable")
        self.assertNotEqual(value, pc_manifest.NO_GIT_DIGEST)
        self.assertNotEqual(value, pc_manifest.gitdir_digest(self.main), "the main checkout digests as a folder")

    def test_the_pointer_resolves_to_the_worktree_folder_and_back_to_the_main_checkouts_git_folder(self) -> None:
        import pc_manifest

        pointer, worktree_git, common = pc_manifest.worktree_git_folders(self.project)
        self.assertEqual(pointer, read_bytes(os.path.join(self.project, ".git")))
        self.assertEqual(worktree_git, os.path.realpath(self.worktree_git))
        self.assertEqual(common, os.path.realpath(os.path.join(self.main, ".git")))

    def test_a_refresh_of_the_worktree_index_never_changes_the_digest(self) -> None:
        index = os.path.join(self.worktree_git, "index")
        before_digest = self.digest()
        before_index = hashlib.sha256(read_bytes(index)).hexdigest()
        os.utime(os.path.join(self.project, "CLAUDE.md"), (1700000000, 1700000000))
        git_out(self.project, "update-index", "--refresh")
        git_out(self.project, "status")
        self.assertNotEqual(hashlib.sha256(read_bytes(index)).hexdigest(), before_index, "the index really was rewritten")
        self.assertEqual(self.digest(), before_digest, "index entries are left out")
        main_index = os.path.join(self.main, ".git", "index")
        os.utime(os.path.join(self.main, "CLAUDE.md"), (1700000001, 1700000001))
        git_out(self.main, "update-index", "--refresh")
        self.assertEqual(self.digest(), before_digest, "so is the main checkout's own index")
        self.assertTrue(os.path.isfile(main_index))

    def test_an_index_lock_file_anywhere_a_git_folder_may_hold_one_is_left_out(self) -> None:
        before = self.digest()
        for folder in (self.worktree_git, os.path.join(self.main, ".git")):
            with open(os.path.join(folder, "index.lock"), "wb") as handle:
                handle.write(b"x")
        self.assertEqual(self.digest(), before)

    def test_a_reference_that_merely_shares_the_name_index_is_not_left_out(self) -> None:
        before = self.digest()
        folder = os.path.join(self.main, ".git", "refs", "heads")
        with open(os.path.join(folder, "index"), "w", encoding="utf-8") as handle:
            handle.write(git_out(self.main, "rev-parse", "main"))
        self.assertNotEqual(self.digest(), before, "a branch named index is a change")

    def test_a_changed_common_configuration_a_moved_reference_and_a_new_commit_each_change_the_digest(self) -> None:
        seen = [self.digest()]
        with open(os.path.join(self.main, ".git", "config"), "a", encoding="utf-8") as handle:
            handle.write("[alias]\n\tx = status\n")
        seen.append(self.digest())
        git_out(self.project, "branch", "another")
        seen.append(self.digest())
        git_out(self.project, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "an empty commit")
        seen.append(self.digest())
        self.assertEqual(len(set(seen)), len(seen), "four different digests")

    def test_a_changed_worktree_configuration_and_a_changed_pointer_text_change_the_digest(self) -> None:
        before = self.digest()
        with open(os.path.join(self.worktree_git, "config.worktree"), "w", encoding="utf-8") as handle:
            handle.write("[core]\n\tbare = false\n")
        after_config = self.digest()
        self.assertNotEqual(after_config, before)
        pointer_path = os.path.join(self.project, ".git")
        text = read_text(pointer_path)
        relative = os.path.relpath(text[len("gitdir: "):].strip(), self.project)
        with open(pointer_path, "w", encoding="utf-8") as handle:
            handle.write("gitdir: " + relative + "\n")
        self.assertNotEqual(self.digest(), after_config, "the same target spelled differently is a different pointer")

    def test_a_pointer_that_leads_outside_the_main_checkout_a_malformed_one_and_a_link_are_refused(self) -> None:
        import pc_manifest

        pointer_path = os.path.join(self.project, ".git")
        original = read_bytes(pointer_path)

        def rewrite(data: bytes) -> None:
            with open(pointer_path, "wb") as handle:
                handle.write(data)

        for label, data in (
            ("outside", ("gitdir: " + os.path.join(self.seeded.run_root, "ckpt") + "\n").encode("utf-8")),
            ("main git itself", ("gitdir: " + os.path.join(self.main, ".git") + "\n").encode("utf-8")),
            ("two lines", original + original),
            ("no prefix", b"somewhere\n"),
            ("empty target", b"gitdir: \n"),
            ("not text", b"gitdir: \xff\xfe\n"),
            ("too large", b"gitdir: " + b"a" * 5000 + b"\n"),
        ):
            rewrite(data)
            with self.assertRaises(pc_manifest.ManifestError, msg=label):
                pc_manifest.gitdir_digest(self.project)
        rewrite(original)
        self.assertRegex(self.digest(), r"\A[0-9a-f]{64}\Z", "restored")
        elsewhere = os.path.join(self.seeded.run_root, "pointer-copy")
        with open(elsewhere, "wb") as handle:
            handle.write(original)
        os.rename(pointer_path, pointer_path + ".held")
        os.symlink(elsewhere, pointer_path)
        with self.assertRaises(pc_manifest.ManifestError, msg="symlinked pointer"):
            pc_manifest.gitdir_digest(self.project)

    def test_a_commondir_that_leads_elsewhere_and_a_missing_main_checkout_are_refused(self) -> None:
        import pc_manifest

        with open(os.path.join(self.worktree_git, "commondir"), "w", encoding="utf-8") as handle:
            handle.write("../../../ckpt\n")
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.gitdir_digest(self.project)
        lone = os.path.join(os.path.dirname(self.seeded.run_root), "lone-worktree")
        os.makedirs(lone)
        with open(os.path.join(lone, ".git"), "w", encoding="utf-8") as handle:
            handle.write("gitdir: " + self.worktree_git + "\n")
        with self.assertRaises(pc_manifest.ManifestError):
            pc_manifest.gitdir_digest(lone)

    def test_the_state_of_an_untouched_worktree_is_read_normally_with_the_branch_and_the_head(self) -> None:
        import pc_checks

        pin = self.digest()
        state = pc_checks.git_state(self.project, real_git_path(), pin)
        self.assertEqual(state["gitdir_digest"], pin)
        self.assertEqual(state["branch"], "refs/heads/feature/widget-export")
        self.assertEqual(state["head"], git_out(self.main, "rev-parse", "main").strip())
        self.assertEqual(state["staged"], 0)
        self.assertNotIn(state["head"], (pc_checks.GIT_NOT_READ, ""))

    def test_a_planted_common_configuration_starts_no_git_process_and_is_counted_as_a_mutation(self) -> None:
        import pc_checks
        import pc_manifest

        pin = self.digest()
        setup = pc_checks.git_state(self.project, real_git_path(), pin)
        marker = os.path.join(self.seeded.run_root, "planted-marker")
        with open(os.path.join(self.main, ".git", "config"), "a", encoding="utf-8") as handle:
            handle.write("[filter \"planted\"]\n\tclean = touch " + marker + " #\n")
        with open(os.path.join(self.project, ".gitattributes"), "w", encoding="utf-8") as handle:
            handle.write("* filter=planted\n")
        os.utime(os.path.join(self.project, "CLAUDE.md"), (1700000002, 1700000002))
        before = read_git_tripwire(self.bin)
        with self.assertRaises(pc_manifest.GitDirChanged):
            pc_manifest.capture_git_status(self.project, self.tripwire, pin)
        state = pc_checks.git_state(self.project, self.tripwire, pin)
        self.assertEqual(read_git_tripwire(self.bin), before, "no git process was started")
        self.assertFalse(os.path.exists(marker), "the planted command never ran")
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], pc_checks.GIT_NOT_READ, key)
        self.assertNotEqual(state["gitdir_digest"], pin)
        mutations = pc_checks.git_mutations([setup, state], [])
        self.assertIn("gitdir_digest", mutations["changed_fields"])
        self.assertGreater(mutations["total"], 0)

    def test_a_pointer_the_harness_cannot_read_against_the_pin_is_a_change_and_starts_no_git_process(self) -> None:
        import pc_checks
        import pc_manifest

        pin = self.digest()
        with open(os.path.join(self.project, ".git"), "w", encoding="utf-8") as handle:
            handle.write("gitdir: " + os.path.join(self.seeded.run_root, "ckpt") + "\n")
        before = read_git_tripwire(self.bin)
        with self.assertRaises(pc_manifest.GitDirChanged):
            pc_manifest.capture_git_status(self.project, self.tripwire, pin)
        with self.assertRaises(pc_checks.CheckError):
            pc_checks.git_state(self.project, self.tripwire, pin)
        self.assertEqual(read_git_tripwire(self.bin), before, "no git process was started")

    def test_a_nested_repository_in_a_worktree_project_is_refused_before_any_process(self) -> None:
        import pc_manifest

        os.makedirs(os.path.join(self.project, "inner", ".git"))
        before = read_git_tripwire(self.bin)
        with self.assertRaises(pc_manifest.NestedRepository):
            pc_manifest.capture_git_status(self.project, self.tripwire, None)
        self.assertEqual(read_git_tripwire(self.bin), before)

    def test_the_harness_status_of_the_worktree_is_real_and_never_a_mutation(self) -> None:
        import pc_checks
        import pc_manifest

        pin = self.digest()
        _raw, text = pc_manifest.capture_git_status(self.project, real_git_path(), pin)
        self.assertEqual(text.decode("utf-8"), skill_status())
        before = pc_checks.git_state(self.project, real_git_path(), pin)
        pc_manifest.capture_git_status(self.project, real_git_path(), pin)
        after = pc_checks.git_state(self.project, real_git_path(), pin)
        self.assertEqual(pc_checks.git_mutations([before, after], [])["total"], 0)


class MainCheckoutTests(unittest.TestCase):
    """The run-root manifest keeps the main checkout's content under watch and leaves its git metadata out."""

    def test_the_exclusion_leaves_out_main_checkout_git_and_everything_under_it_and_nothing_else(self) -> None:
        excluded = row1()._excluded
        for path in (b"main-checkout/.git", b"main-checkout/.git/HEAD", b"main-checkout/.git/worktrees/project/index",
                     b"project/.git", b"raw/x", b"snaps/x"):
            self.assertTrue(excluded(path), path)
        for path in (b"main-checkout", b"main-checkout/CLAUDE.md", b"main-checkout/thoughts/plans/p.md",
                     b"main-checkout/.gitignore", b"main-checkout/.github/x", b"main-checkout/sub/.git",
                     b"main-checkout/.gitx", b"project/.gitignore", b"project/CLAUDE.md"):
            self.assertFalse(excluded(path), path)

    def test_a_snapshot_of_a_seeded_row_9_lists_the_main_checkout_files_and_no_git_entry(self) -> None:
        seeded = SeededGit(ROW9, "git-main-checkout-snapshot")
        row = row1()
        row.take_snapshot(row.paths_for(seeded.run_root), "snap-0-setup", real_git_path(), setup=True)
        listing = read_text(os.path.join(seeded.run_root, "snaps", "snap-0-setup", "sha.txt"))
        names = [line.split("  ", 1)[1] for line in listing.splitlines()]
        self.assertIn("main-checkout/CLAUDE.md", names)
        self.assertIn("main-checkout/" + PLAN_RELATIVE, names)
        self.assertEqual([n for n in names if n.startswith("main-checkout/.git")], [])
        self.assertEqual([n for n in names if n.startswith("project/.git")], [])
        manifest = read_text(os.path.join(seeded.run_root, "snaps", "snap-0-setup", "manifest.jsonl"))
        self.assertNotIn("main-checkout/.git", manifest)
        status = read_text(os.path.join(seeded.run_root, "snaps", "snap-0-setup", "status.txt"))
        self.assertEqual(status, skill_status())


class WorktreeChainTests(unittest.TestCase):
    """Row 9 through the engine: the main checkout is watched, the worktree's own git use is not a breach."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.chain = run_git_row(ROW9, SHAPE_WORDS[ROW9])
        assert cls.chain.outcome.code == 0, "\n".join(cls.chain.outcome.lines)

    def read(self, name: str) -> str:
        return read_text(os.path.join(self.chain.row_dir, name))

    def main_lines(self, snapshot: str) -> list:
        return [line for line in self.read(snapshot + "/sha.txt").splitlines() if "  main-checkout/" in line]

    def test_the_main_checkouts_listed_hashes_are_identical_at_setup_and_after_each_stage(self) -> None:
        snapshots = ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume")
        first = self.main_lines(snapshots[0])
        self.assertEqual(len(first), 2, "the project file and the plan")
        for name in snapshots[1:]:
            self.assertEqual(self.main_lines(name), first, name)
        listing = sha_lines(ROW9)
        for line in first:
            digest, _, name = line.partition("  ")
            self.assertEqual(digest, listing[name], name + " equals the committed digest")

    def test_no_filed_snapshot_lists_a_git_entry_of_either_checkout(self) -> None:
        for name in ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"):
            listing = self.read(name + "/sha.txt")
            self.assertNotIn("main-checkout/.git", listing)
            self.assertNotIn("project/.git", listing)

    def test_s3_makes_no_write_and_the_s2_and_s3_snapshots_hash_alike(self) -> None:
        self.assertIn("Write/Edit calls 0: []", self.read("s3-resume-trace.md"))
        self.assertEqual(self.read("snap-2-after-preclear/sha.txt"), self.read("snap-3-after-resume/sha.txt"))

    def test_the_git_facts_name_the_feature_branch_and_a_head_that_never_moves(self) -> None:
        text = self.read("mechanical-checks.md")
        self.assertIn("states: 4", text)
        self.assertEqual(
            len(re.findall(r"^state \S+: head [0-9a-f]{40}, branch refs/heads/feature/widget-export, staged 0$", text, re.M)), 4
        )
        self.assertIn("mutations-total: 0", text)
        self.assertIn("mutation-changed-fields: none", text)
        self.assertIn("snapshot-paths-outside-approved-roots: 0", text)

    def test_the_setup_status_is_the_skill_copy_untracked_in_the_worktree(self) -> None:
        self.assertEqual(self.read("snap-0-setup/status.txt"), skill_status())

    def test_the_readme_says_what_the_row_claims_and_what_it_does_not_and_ends_pending(self) -> None:
        text = self.read("README.md")
        self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"))
        self.assertIn("content preservation of the main checkout", text)
        self.assertIn("not to the absence of every git metadata access", text)
        self.assertIsNone(evidence().verdict_pattern().search(text[: -len(VERDICT_LINE) - 1]))
        self.assertIsNone(SHAPED.search(text))

    def stages_with_ops(self, index: int, ops: list) -> list:
        stages = git_stages(spec_of(ROW9), SHAPE_WORDS[ROW9])
        return pc_testutil.stages_with(stages, index, ops=list(stages[index]["ops"]) + ops)

    def stopped(self, run: Registered) -> None:
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW9])
        self.assertNotIn(run.rig.base, "\n".join(run.outcome.lines), "no path in the text")

    def test_a_scripted_new_file_in_the_main_checkout_is_a_write_outside_the_roots_and_ends_with_11(self) -> None:
        run = Registered(ROW9, stages=self.stages_with_ops(1, [
            {"op": "write", "path": "$RUN/main-checkout/stray.txt", "text": "a stray file\n"},
        ]))
        self.stopped(run)
        self.assertTrue(any("writes outside approved roots" in line for line in run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), 2, "the chain ended at the stage that wrote")

    def test_a_scripted_edit_of_a_main_checkout_file_is_a_write_outside_the_roots_and_ends_with_11(self) -> None:
        run = Registered(ROW9, stages=self.stages_with_ops(0, [
            {"op": "write", "path": "$RUN/main-checkout/CLAUDE.md", "text": "changed\n"},
        ]))
        self.stopped(run)
        self.assertTrue(any("writes outside approved roots" in line for line in run.outcome.lines))

    def test_a_git_status_in_the_worktree_that_refreshes_an_index_is_not_a_breach(self) -> None:
        run = Registered(ROW9, stages=self.stages_with_ops(1, [
            {"op": "touch", "path": "$PROJECT/CLAUDE.md"},
            {"op": "git", "args": ["update-index", "--refresh"]},
            {"op": "tool", "name": "Bash", "input": {"command": "git status"}, "content": "On branch feature/widget-export"},
            {"op": "tool", "name": "Bash", "input": {"command": "git log --oneline -3"}, "content": "abc1234 x"},
        ]))
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
        self.assertIn("mutations-total: 0", text)
        self.assertIn("snapshot-paths-outside-approved-roots: 0", text)

    def test_a_scripted_write_into_the_main_checkouts_git_folder_is_counted_through_the_digest_and_runs_no_planted_command(self) -> None:
        config = (
            "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = true\n"
            "[filter \"planted\"]\n\tclean = touch $OUTSIDE/planted-worktree #\n"
        )
        run = Registered(ROW9, stages=self.stages_with_ops(0, [
            {"op": "write", "path": "$RUN/main-checkout/.git/config", "text": config},
            {"op": "write", "path": "$PROJECT/.gitattributes", "text": "* filter=planted\n"},
            {"op": "touch", "path": "$PROJECT/CLAUDE.md"},
        ]))
        self.stopped(run)
        self.assertRegex("\n".join(run.outcome.lines), r"isolation or git breach: git mutations: [1-9][0-9]*")
        self.assertFalse(os.path.exists(os.path.join(run.rig.outside, "planted-worktree")), "the planted command never ran")
        state = read_json(os.path.join(run.run_root, "raw", "s1.git.json"))
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], "not-read", key)
        status = read_text(os.path.join(run.run_root, "snaps", "snap-1-after-work", "status.txt"))
        self.assertEqual(status.strip(), row1().STATUS_NOT_RUN)
        self.assertEqual(len(run.rig.calls()), 1, "the second stage was never launched")

    def test_a_scripted_rewrite_of_the_worktree_pointer_ends_the_row_without_starting_git(self) -> None:
        run = Registered(ROW9, stages=self.stages_with_ops(0, [
            {"op": "write", "path": "$PROJECT/.git", "text": "gitdir: $RUN/ckpt\n"},
        ]))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW9])
        self.assertTrue(any("could not be checked against the setup record" in line for line in run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), 1)


ROW10 = "row10-large-status"
ROW10_COMMITTED = "row10-large-status-rerun"
JA_FOLDER_POINTS = [0x30C7, 0x30FC, 0x30BF]
JA_FILE_POINTS = [0x30C6, 0x30B9, 0x30C8]
AR_FOLDER_POINTS = [0x0645, 0x0644, 0x0641, 0x0627, 0x062A]
AR_FILE_POINTS = [0x0645, 0x0644, 0x0641]
HARNESS_SOURCES_OF_ROW10 = ("pc_rows.py", "pc_rowseeds.py", "pc_review.py", "test_rows_git.py", "test_review.py")


def text_of(points: list) -> str:
    return "".join(chr(point) for point in points)


def untracked_hostile(folder: str) -> list:
    """The untracked entries of a seeded project that are not the skill copy, from the NUL form (no quoting)."""
    raw = git_out(folder, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [item for item in raw.split("\0") if item]
    names = []
    for entry in entries:
        assert entry.startswith("?? "), entry
        name = entry[3:]
        if not name.startswith(".claude/skills/preclear/"):
            names.append(name)
    return names


class Row10Tests(unittest.TestCase):
    """Row 10 (plan 04-10; HARN-10): the hostile tree, the baseline allowlist and a scripted three-stage chain."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = SeededGit(ROW10, "git-seed-row10")
        cls.chain = run_git_row(ROW10, "main @ abc1234")
        assert cls.chain.outcome.code == 0, "\n".join(cls.chain.outcome.lines)

    def read(self, name: str) -> str:
        return read_text(os.path.join(self.chain.row_dir, name))

    # -- the seed ---------------------------------------------------------------------------------------------

    def test_the_seeded_claude_md_equals_the_committed_rerun_fixture_and_the_plan_equals_the_plain_plan(self) -> None:
        data = read_bytes(os.path.join(self.seeded.project, "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW10_COMMITTED, "fixture-CLAUDE.md")), "byte for byte")
        self.assertEqual(hashlib.sha256(data).hexdigest(), sha_lines(ROW10_COMMITTED)["project/CLAUDE.md"])
        self.assertTrue(hashlib.sha256(data).hexdigest().startswith(CLAUDE_MD_DIGEST_PREFIX))
        plan = read_bytes(os.path.join(self.seeded.project, *PLAN_RELATIVE.split("/")))
        self.assertEqual(plan, read_bytes(os.path.join(DATA, "plain-plan.md")))
        self.assertEqual(hashlib.sha256(plan).hexdigest(), PLAN_DIGEST)

    def test_one_commit_on_main_holds_only_the_instruction_file_and_the_plan(self) -> None:
        self.assertEqual(self.seeded.git("rev-list", "--count", "HEAD").strip(), "1")
        self.assertEqual(self.seeded.git("symbolic-ref", "-q", "HEAD").strip(), "refs/heads/main")
        self.assertEqual(self.seeded.git("ls-files").split(), ["CLAUDE.md", PLAN_RELATIVE])

    def test_exactly_124_hostile_entries_are_untracked_and_they_are_the_named_set(self) -> None:
        found = untracked_hostile(self.seeded.project)
        self.assertEqual(len(found), 124)
        self.assertEqual(sorted(found), sorted(rowseeds().hostile_names()))
        self.assertEqual(rowseeds().HOSTILE_COUNT, 124)
        status = self.seeded.git("status", "--porcelain=v1", "--untracked-files=all")
        self.assertNotIn("\n M ", "\n" + status, "nothing is modified and nothing is staged")
        self.assertEqual(self.seeded.git("diff", "--cached", "--name-only"), "")

    def test_the_sample_folder_holds_90_files_and_each_non_latin_folder_15_with_the_stated_code_points(self) -> None:
        found = untracked_hostile(self.seeded.project)
        samples = [name for name in found if name.startswith("data/raw files/sample ")]
        self.assertEqual(sorted(samples), sorted("data/raw files/sample %d.csv" % number for number in range(1, 91)))
        ja = text_of(JA_FOLDER_POINTS) + "/" + text_of(JA_FILE_POINTS) + " "
        ar = text_of(AR_FOLDER_POINTS) + "/" + text_of(AR_FILE_POINTS) + " "
        self.assertEqual(sorted(name for name in found if name.startswith(ja)), sorted(ja + "%d.txt" % n for n in range(1, 16)))
        self.assertEqual(sorted(name for name in found if name.startswith(ar)), sorted(ar + "%d.txt" % n for n in range(1, 16)))

    def test_the_three_special_names_have_the_stated_shapes(self) -> None:
        found = untracked_hostile(self.seeded.project)
        with_newline = [name for name in found if "\n" in name]
        self.assertEqual(with_newline, ["odd\nname.txt"])
        quoted = [name for name in found if '"' in name]
        self.assertEqual(quoted, ['quote"and"tab\tname.md'])
        self.assertEqual(quoted[0].count('"'), 2)
        self.assertEqual(quoted[0].count("\t"), 1)
        spaced = [name for name in found if name.startswith(" ")]
        self.assertEqual(spaced, ["  leading-space.txt"])

    def test_notes_md_holds_text_of_both_scripts_and_every_hostile_file_is_small_text(self) -> None:
        notes = read_bytes(os.path.join(self.seeded.project, "NOTES.md")).decode("utf-8")
        self.assertTrue(any(0x3040 <= ord(ch) <= 0x30FF for ch in notes), "Japanese text")
        self.assertTrue(any(0x0600 <= ord(ch) <= 0x06FF for ch in notes), "Arabic text")
        for name in rowseeds().hostile_names():
            data = read_bytes(os.path.join(self.seeded.project, *name.split("/")))
            self.assertTrue(0 < len(data) < 200, name)
            self.assertNotIn(b"\0", data)

    def test_no_harness_source_of_the_row_holds_a_non_ascii_character(self) -> None:
        for name in HARNESS_SOURCES_OF_ROW10:
            path = os.path.join(HARNESS_DIR, name)
            if not os.path.exists(path):
                continue
            wide = [line for line in read_bytes(path).decode("utf-8").split("\n") if not line.isascii()]
            if name == "pc_review.py":
                # plan 04-07 left one character class with literal spacing characters; this plan adds none
                self.assertEqual(len(wide), 1, name)
                self.assertTrue(wide[0].startswith("_CONTROL = re.compile("), name)
            else:
                self.assertEqual(wide, [], name)

    def test_the_hostile_tree_exists_only_inside_the_run_root(self) -> None:
        for name in ("odd\nname.txt", "  leading-space.txt", "NOTES.md"):
            self.assertFalse(os.path.lexists(os.path.join(ROOT, name)), name)
        self.assertFalse(os.path.lexists(os.path.join(ROOT, "data", "raw files")))

    def test_the_manifest_listing_holds_the_newline_name_escaped_on_one_line(self) -> None:
        import pc_manifest

        entries = pc_manifest.tree_manifest(self.seeded.project)
        listing = pc_manifest.sha_txt_bytes(entries).decode("utf-8")
        lines = listing.split("\n")
        self.assertEqual(lines[-1], "")
        escaped = [line for line in lines if line.endswith("odd\\nname.txt")]
        self.assertEqual(len(escaped), 1)
        self.assertTrue(escaped[0].startswith("\\"), "the escape marker leads the line")
        for line in lines[:-1]:
            self.assertRegex(line, r"\A\\?[0-9a-f]{64}  .+\Z")
        self.assertEqual(len(lines) - 1, len([e for e in entries if e["kind"] == "f"]))
        companion = pc_manifest.jsonl_bytes(entries)
        self.assertTrue(companion.isascii(), "the lossless companion is ASCII JSON")
        self.assertEqual(len(companion.splitlines()), len(entries))

    # -- the registry entry -----------------------------------------------------------------------------------

    def test_row_10_is_registered_with_three_stages_the_baseline_allowlist_and_the_resume_line_chain(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW10)
        self.assertTrue(spec.implemented)
        self.assertEqual(
            [(s.name, s.kind, s.max_turns, str(s.cap), s.timeout, s.session) for s in spec.stages],
            [("s1", "work", 15, "0.30", 900, "new:A"), ("s2", "preclear", 60, "1.30", 1800, "resume:A"),
             ("s3", "resume", 15, "0.40", 900, "new:B")],
        )
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_GIT)
        self.assertEqual(spec.extra_tools, ())
        self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
        self.assertEqual(spec.chain, pc_rows.CHAIN_RESUME_LINE)
        self.assertEqual((spec.hooks, spec.probe), ((), pc_rows.PROBE_NONE))
        self.assertEqual(spec.seed, "pc_rowseeds:seed_row10")
        self.assertEqual(pc_rows.worst_case(spec), pc_rows.Decimal("2.00") if hasattr(pc_rows, "Decimal") else spec.stages[0].cap + spec.stages[1].cap + spec.stages[2].cap)
        self.assertEqual(dict(spec.prompts)["s2"], rowseeds().ROW10_FOLDER + "/s2-preclear-prompt.md")
        self.assertIn((rowseeds().ROW10_FOLDER + "/fixture-CLAUDE.md", "file"), spec.sources)
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        self.assertIsNone(SHAPED.search(spec.setup_text))
        self.assertTrue(spec.setup_text.isascii())

    def test_the_dry_run_prints_the_plan_and_starts_no_process_and_list_marks_the_row_implemented(self) -> None:
        code, text, tripwire, base = dry_run_row(ROW10)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 3 stages, 2 sessions" % ROW10, text)
        lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
        self.assertEqual(len(lines), 3)
        for line, turns, cap in zip(lines, ("15 turns", "60 turns", "15 turns"), ("cap 0.30", "cap 1.30", "cap 0.40")):
            self.assertIn(turns, line)
            self.assertIn(cap, line)
        self.assertIn("worst case 2.00 USD", text)
        self.assertIn("allowlist 33 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")))
        cells = dict((line.split()[1], line.split()) for line in matrix().list_lines(rows().build_registry())[1:])
        self.assertEqual(cells[ROW10][2:], ["3", "2", "yes"])

    # -- the scripted chain -------------------------------------------------------------------------------------

    def test_the_chain_runs_three_launches_on_the_33_baseline_rules_alone_with_memory_pinned(self) -> None:
        import pc_flags

        calls = self.chain.rig.calls()
        self.assertEqual(len(calls), 3)
        for call in calls:
            argv = call["args"]
            rules = argv[argv.index("--allowedTools") + 1].split(",")
            self.assertEqual(rules, list(pc_flags.BASELINE_ALLOWED_TOOLS))
            self.assertEqual(len(rules), 33)
        self.assertEqual(self.read("tools.txt"), ",".join(pc_flags.BASELINE_ALLOWED_TOOLS) + "\n")
        self.assertEqual(calls[1]["prompt"].encode("utf-8"), read_bytes(committed(ROW10_COMMITTED, "s2-preclear-prompt.md")))
        self.assertEqual(calls[0]["prompt"].encode("utf-8"), read_bytes(os.path.join(DATA, "plain-s1-prompt.md")))
        self.assertIs(read_json(calls[0]["args"][calls[0]["args"].index("--settings") + 1])["autoMemoryEnabled"], True)

    def test_the_baseline_holds_the_status_rules_and_pwd_and_no_rule_for_the_nul_form_a_redirection_or_the_sidecar(self) -> None:
        import pc_flags

        rules = list(pc_flags.BASELINE_ALLOWED_TOOLS)
        for wanted in ("Bash(git --no-optional-locks status:*)", "Bash(git --no-optional-locks rev-parse:*)", "Bash(pwd -P)"):
            self.assertIn(wanted, rules)
        for rule in rules:
            for banned in ("-z", ">", "<", "tee", "--output", "\0", "status.txt"):
                self.assertNotIn(banned, rule, rule)

    def test_the_third_stage_is_a_fresh_session_fed_the_resume_line_the_second_printed(self) -> None:
        calls = self.chain.rig.calls()
        self.assertTrue(calls[2]["prompt"].startswith("Resume "))
        self.assertNotIn("--resume", calls[2]["args"])
        self.assertIn("--resume", calls[1]["args"])
        self.assertEqual(
            self.read("resume-line.txt").rstrip("\n").replace("<run>", "$RUNROOT"),
            calls[2]["prompt"].replace(self.chain.run_root, "$RUNROOT"),
        )

    def test_s3_makes_no_write_or_edit_call_and_the_s2_and_s3_snapshots_hash_alike(self) -> None:
        self.assertIn("Write/Edit calls 0: []", self.read("s3-resume-trace.md"))
        self.assertEqual(self.read("snap-2-after-preclear/sha.txt"), self.read("snap-3-after-resume/sha.txt"))

    def test_the_chain_files_the_row_through_the_real_sanitizer_gate_and_promote_with_the_names_escaped(self) -> None:
        self.assertEqual(os.listdir(self.chain.ctx.destination), [ROW10])
        listing = self.read("snap-0-setup/sha.txt")
        lines = listing.split("\n")
        self.assertEqual(lines[-1], "")
        escaped = [line for line in lines if line.endswith("project/odd\\nname.txt")]
        self.assertEqual(len(escaped), 1, "the newline name is one escaped line")
        self.assertTrue(escaped[0].startswith("\\"))
        for line in lines[:-1]:
            self.assertRegex(line, r"\A\\?[0-9a-f]{64}  .+\Z", "a hostile name never breaks a listing line")
        self.assertIn("project/" + "data/raw files/sample 1.csv", listing)
        self.assertIn("project/" + text_of(JA_FOLDER_POINTS) + "/" + text_of(JA_FILE_POINTS) + " 1.txt", listing)
        self.assertIn("project/" + text_of(AR_FOLDER_POINTS) + "/" + text_of(AR_FILE_POINTS) + " 1.txt", listing)
        self.assertIn('project/quote"and"tab\tname.md', listing)
        self.assertIn("project/  leading-space.txt", listing)

    def test_no_filed_file_holds_a_nul_byte_and_no_raw_status_capture_is_filed(self) -> None:
        for relative in tree_names(self.chain.row_dir):
            if relative.endswith("/"):
                continue
            self.assertNotIn(b"\0", read_bytes(os.path.join(self.chain.row_dir, *relative.split("/"))), relative)
            self.assertNotEqual(os.path.basename(relative), "status.raw", relative)

    def test_the_filed_status_of_each_snapshot_is_the_plain_listing_of_the_124_entries_and_the_skill_copy(self) -> None:
        text = self.read("snap-0-setup/status.txt")
        self.assertGreaterEqual(len(text.splitlines()), 124 + len(skill_status().splitlines()))
        self.assertIn("?? NOTES.md", text)
        self.assertEqual(self.read("snap-2-after-preclear/status.txt"), self.read("snap-3-after-resume/status.txt"))

    def test_the_filed_folder_holds_the_standard_files_and_no_helper_file(self) -> None:
        names = tree_names(self.chain.row_dir)
        for expected in ("README.md", "mechanical-checks.md", "resume-line.txt", "s2-preclear-full-trace.md",
                         "s3-resume-trace.md", "tools.txt", "fixture-CLAUDE.md", "snap-0-setup/"):
            self.assertIn(expected, names)
        for absent in ("wrapper-calls.log", "wrapper-checkpoint.sh", "status-before.txt", "lint-before.txt"):
            self.assertNotIn(absent, names)
        self.assertEqual(self.read("fixture-CLAUDE.md"), read_text(committed(ROW10_COMMITTED, "fixture-CLAUDE.md")))

    def test_the_readme_ends_with_the_pending_line_and_holds_the_setup_paragraph_and_no_verdict_word(self) -> None:
        readme = self.read("README.md")
        self.assertTrue(readme.endswith(VERDICT_LINE + "\n"))
        self.assertIn(spec_of(ROW10).setup_text, readme)
        self.assertIsNone(re.search(r"\b(?:" + "|".join(("pa" + "ss", "fa" + "il", "acc" + "ept", "ver" + "dict")) + r")\b", readme.replace(VERDICT_LINE, ""), re.I))


if __name__ == "__main__":
    unittest.main()
