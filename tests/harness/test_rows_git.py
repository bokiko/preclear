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
CLAUDE_MD_DIGEST_PREFIX = "ed03447e9df43888"
PLAN_RELATIVE = "thoughts/plans/2026-10-15-widget-export.md"
DASH = "—"
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
        cls.seeded = {ROW8B: SeededGit(ROW8B, "git-seed-8b")}

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

    def test_the_shape_words_are_the_five_the_plan_names(self) -> None:
        self.assertEqual(
            rowseeds().GIT_SHAPES, ("commit", "detached", "unborn", "none", "worktree")
        )


class GitRegistryTests(unittest.TestCase):
    def test_8b_is_registered_with_the_three_committed_stages_the_git_profile_and_the_resume_line_chain(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW8B)
        self.assertTrue(spec.implemented)
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
        self.assertEqual(spec.seed, "pc_rowseeds:seed_row8b")

    def test_the_git_profile_word_of_the_registry_and_of_the_flag_module_agree(self) -> None:
        import pc_flags

        self.assertEqual(rows().PROFILE_GIT, pc_flags.PROFILE_GIT)

    def test_8b_the_dry_run_prints_the_plan_and_starts_no_process(self) -> None:
        code, text, tripwire, base = dry_run_row(ROW8B)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 3 stages, 2 sessions" % ROW8B, text)
        lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
        self.assertEqual(len(lines), 3)
        for line, turns, cap in zip(lines, ("15 turns", "60 turns", "15 turns"), ("cap 0.30", "cap 1.30", "cap 0.40")):
            self.assertIn(turns, line)
            self.assertIn(cap, line)
        self.assertIn("worst case 2.00 USD", text)
        self.assertIn("allowlist 33 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")

    def test_8b_list_marks_the_row_implemented_with_three_stages_and_two_sessions(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        self.assertEqual(cells[ROW8B][2:], ["3", "2", "yes"])


class GitRowChainTests(unittest.TestCase):
    """A scripted chain of each git row through the same engine as every other row."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runs = {ROW8B: run_git_row(ROW8B, "detached @ abc1234")}
        for row_id, run in cls.runs.items():
            assert run.outcome.code == 0, "\n".join(run.outcome.lines)

    def read(self, row_id: str, name: str) -> str:
        return read_text(os.path.join(self.runs[row_id].row_dir, name))

    def test_8b_a_scripted_chain_completes_with_three_launches_and_no_wrapper_folder(self) -> None:
        run = self.runs[ROW8B]
        self.assertEqual(len(run.rig.calls()), 3, "each stage is launched exactly once")
        self.assertFalse(os.path.lexists(os.path.join(run.run_root, "wrapper")), "no wrapper folder")
        self.assertEqual(
            [(r["kind"], r["stage"]) for r in run.ledger()],
            [("launch", "row8b-s1"), ("settle", "row8b-s1"), ("launch", "row8b-s2"), ("settle", "row8b-s2"),
             ("launch", "row8b-s3"), ("settle", "row8b-s3")],
        )
        self.assertEqual(os.listdir(run.ctx.destination), [ROW8B])

    def test_8b_the_stage_commands_carry_the_33_baseline_rules_alone_and_the_pinned_memory_switch(self) -> None:
        import pc_flags

        run = self.runs[ROW8B]
        for call in run.rig.calls():
            argv = call["args"]
            rules = argv[argv.index("--allowedTools") + 1].split(",")
            self.assertEqual(rules, list(pc_flags.BASELINE_ALLOWED_TOOLS))
            self.assertEqual(len(rules), 33)
        first = run.rig.calls()[0]
        settings_path = first["args"][first["args"].index("--settings") + 1]
        self.assertIs(read_json(settings_path)["autoMemoryEnabled"], True)

    def test_8b_the_third_stage_is_a_fresh_session_fed_the_resume_line_the_second_printed(self) -> None:
        run = self.runs[ROW8B]
        calls = run.rig.calls()
        prompt = calls[2]["prompt"]
        self.assertTrue(prompt.startswith("Resume "))
        self.assertTrue(re.search(r"detached @ [0-9a-f]{7} " + DASH, prompt) is not None, prompt)
        self.assertEqual(self.read(ROW8B, "resume-line.txt").rstrip("\n").replace("<run>", "$RUNROOT"),
                         prompt.replace(run.run_root, "$RUNROOT"))
        self.assertNotIn("--resume", calls[2]["args"], "s3 starts a new session")
        self.assertIn("--resume", calls[1]["args"], "s2 continues the session of s1")

    def test_8b_s3_makes_no_write_or_edit_call_and_the_s2_and_s3_snapshots_hash_alike(self) -> None:
        self.assertIn("Write/Edit calls 0: []", self.read(ROW8B, "s3-resume-trace.md"))
        self.assertEqual(
            self.read(ROW8B, "snap-2-after-preclear/sha.txt"), self.read(ROW8B, "snap-3-after-resume/sha.txt")
        )

    def test_8b_the_filed_folder_holds_the_committed_file_names_and_the_s3_files(self) -> None:
        names = tree_names(self.runs[ROW8B].row_dir)
        for expected in (
            "README.md", "claude-version.txt", "digests.txt", "fixture-CLAUDE.md", "measurements.md",
            "mechanical-checks.md", "resume-line.txt", "s1-work.out", "s1.err", "s1.exit",
            "s2-preclear-full-trace.md", "s2-preclear-prompt.md", "s2-preclear-trace.md", "s2-preclear.err",
            "s2-preclear.exit", "s3-resume-full-trace.md", "s3-resume-trace.md", "s3-resume.err", "s3-resume.exit",
            "session-resume.id", "session.id", "settings.json", "snap-0-setup/", "snap-1-after-work/",
            "snap-2-after-preclear/", "snap-3-after-resume/", "tools.txt", "usage.txt",
        ):
            self.assertIn(expected, names, expected)
        for absent in ("wrapper-calls.log", "wrapper-checkpoint.sh", "status-before.txt", "lint-before.txt"):
            self.assertNotIn(absent, names, absent)

    def test_8b_the_filed_project_file_equals_the_committed_one(self) -> None:
        self.assertEqual(self.read(ROW8B, "fixture-CLAUDE.md"), read_text(committed(ROW8B, "fixture-CLAUDE.md")))

    def test_8b_the_setup_snapshot_status_is_the_committed_untracked_skill_list_and_lists_no_notes_file(self) -> None:
        self.assertEqual(self.read(ROW8B, "snap-0-setup/status.txt"), skill_status())
        listing = self.read(ROW8B, "snap-0-setup/sha.txt")
        self.assertNotIn("NOTES.md", listing)
        self.assertNotIn("project/.git", listing, "the git folder is left out of the manifest")
        self.assertIn("project/CLAUDE.md", listing)

    def test_8b_the_git_facts_are_a_head_a_missing_branch_and_zero_mutations(self) -> None:
        text = self.read(ROW8B, "mechanical-checks.md")
        self.assertIn("states: 4", text)
        self.assertIn("mutations-total: 0", text)
        self.assertIn("mutation-changed-fields: none", text)
        heads = set(re.findall(r"^state \S+: head ([0-9a-f]{40}),", text, re.M))
        self.assertEqual(len(heads), 1, "the detached HEAD never moves")

    def test_8b_the_readme_ends_with_the_pending_line_holds_no_verdict_word_and_no_path(self) -> None:
        pattern = evidence().verdict_pattern()
        text = self.read(ROW8B, "README.md")
        self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"))
        self.assertEqual(text.count(VERDICT_LINE), 1)
        body = text[: -len(VERDICT_LINE) - 1]
        self.assertIsNone(pattern.search(body), "no verdict word in the README")
        self.assertIn(spec_of(ROW8B).setup_text, body, "the Setup paragraph is the registry text")
        self.assertIsNone(SHAPED.search(body))
        self.assertNotIn(self.runs[ROW8B].rig.base, body)

    def test_8b_no_harness_authored_file_holds_a_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        run = self.runs[ROW8B]
        names = []
        for dirpath, _dirnames, filenames in os.walk(run.ctx.destination):
            for name in filenames:
                names.append(os.path.relpath(os.path.join(dirpath, name), run.ctx.destination).replace(os.sep, "/"))
        authored = evidence().harness_authored_names(sorted(names))
        self.assertGreater(len(authored), 8)
        for name in authored:
            text = read_text(os.path.join(run.ctx.destination, name))
            if name == ROW8B + "/README.md":
                text = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(text), "no verdict word in " + name)

    def test_8b_a_reply_without_a_resume_line_ends_the_chain_after_the_second_stage(self) -> None:
        spec = spec_of(ROW8B)
        stages = pc_testutil.default_row_stages(spec)
        stages[1]["result"] = dict(stages[1]["result"], text="Checkpoint written, no resume line.")
        run = run_git_row(ROW8B, stages=stages)
        self.assertEqual(len(run.rig.calls()), 2, "the chain ends there; no resume line is invented")


if __name__ == "__main__":
    unittest.main()
