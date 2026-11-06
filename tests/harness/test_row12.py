"""Zero-token tests for row 12, the frozen handoff (plan 04-13; RERUN-02; D-04, Pitfall 13, FA-6).

Row 12 runs four stages in two sessions: a work turn, a /preclear turn in the same session that also asks for a frozen
copy of the checkpoint, then (after the harness appended one note line to the plan between the two stages) a fresh
session that resumes from the printed line, and a fourth stage that resumes that fresh session with an ordinary
/preclear refresh. These tests prove the seed is byte-tied to the committed row, the plan-note hook appends one fixed line
safely, the scripted chain runs through the engine with the committed prompts and the right session for each stage, and
the fourth stage is bounded by the spend ledger. No test starts a real claude: the only claude executed is the scripted
fake written by pc_testutil. Every folder comes from RowRig or a temporary folder and is never deleted. Modules are
imported inside small accessors so a missing module is one error per test, not one load failure of the file. Messages
that name a path are never asserted on by value; leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import hashlib
import io
import os
import tempfile
import unittest
from decimal import Decimal

import pc_exitcodes
import pc_spend
import pc_testutil
from test_row_generic import Registered, tree_names
from test_rows_git import SeededGit, dry_run_row
from test_rows_plain import (
    DATA,
    PLAN_DIGEST,
    committed,
    matrix,
    read_bytes,
    read_json,
    read_text,
    rowseeds,
    rows,
    spec_of,
    sha_lines,
)

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW12 = "row12-frozen-handoff"
ROW11 = "row11-concurrent-change"
ROW11_COMMITTED = "row11-concurrent-change-rerun"
PLAN_RELATIVE = "thoughts/plans/2026-10-15-widget-export.md"
PLAN_TOKEN = "$PROJECT/" + PLAN_RELATIVE
NOTE_LINE = "Note 2026-10-21 (other session): step 3 test must cover both JSON and CSV."
FROZEN_NAME = "checkpoint-20261019T233549Z-k7q2.md"
CHECKPOINT_DIR = "$PROJECT/.preclear/widget-export"
CLAUDE_MD_DIGEST_PREFIX = "ed03447e9df43888"
SNAPSHOTS = (
    "snap-0-setup",
    "snap-1-after-work",
    "snap-2-after-preclear",
    "snap-2b-after-external-plan-edit",
    "snap-3-after-resume",
    "snap-4-after-refresh",
)
DASH = "—"


def hooks():
    import pc_rowhooks

    return pc_rowhooks


def row1():
    import pc_row1

    return pc_row1


def resume_line_text() -> str:
    return (
        'Resume widget-export from "$PROJECT/.preclear/widget-export/checkpoint.md" '
        + DASH + " main @ abc1234 " + DASH + " CSV done; draft JSON-default diff for review"
    )


def with_costs(stages: list, deltas=("0.03", "0.06", "0.04", "0.06")) -> list:
    """Set each stage's own cost and cumulative total: s1 and s2 share a session chain, s3 and s4 share another."""
    updated = pc_testutil.stages_with(stages, 0)
    d1, d2, d3, d4 = [Decimal(text) for text in deltas]
    totals = (d1, d1 + d2, d3, d3 + d4)
    for index, (delta, total) in enumerate(zip((d1, d2, d3, d4), totals)):
        updated[index]["result"] = dict(updated[index].get("result", {}), delta=float(delta), total_cost_usd=float(total))
    return updated


def checkpoint_write(path: str, text: str) -> list:
    return [
        {"op": "write", "path": path, "text": text},
        {"op": "tool", "name": "Write", "input": {"file_path": path}, "content": "written"},
    ]


def row12_stages(deltas=("0.03", "0.06", "0.04", "0.06"), s2_ops=(), s4_ops=None, s3_ops=()) -> list:
    """The scripted stages of a clean row 12 run: the plain scripts, a frozen copy written by s2 and a refresh by s4.

    s2 also writes the frozen copy named like the committed run's; s4 rewrites the mutable checkpoint only (its ops are
    replaced by s4_ops when given). The /preclear reply of s2 prints the resume line the fresh session is fed with.
    """
    stages = pc_testutil.default_row_stages(spec_of(ROW12))
    for stage in stages:
        assert "$WRAPPER" not in str(stage), "a plain row script holds no wrapper op"
    stages[1]["result"] = dict(
        stages[1]["result"], text="Checkpoint and a frozen copy written.\n\n```\n" + resume_line_text() + "\n```\n"
    )
    frozen = checkpoint_write(CHECKPOINT_DIR + "/" + FROZEN_NAME, "frozen copy of the checkpoint\n")
    stages = pc_testutil._with_ops(stages, 1, frozen + list(s2_ops))
    if s3_ops:
        stages = pc_testutil._with_ops(stages, 2, list(s3_ops))
    refresh = s4_ops
    if refresh is None:
        refresh = checkpoint_write(CHECKPOINT_DIR + "/checkpoint.md", "## Identity and state\nrefreshed\n")
    stages = pc_testutil.stages_with(stages, 3, ops=list(refresh))
    return with_costs(stages, deltas)


class Row12Run(Registered):
    """One scripted row 12 run through the engine."""

    def __init__(self, stages=None, **config) -> None:
        super().__init__(ROW12, stages=stages if stages is not None else row12_stages(), **config)

    def project(self, *parts: str) -> str:
        return os.path.join(self.run_root, "project", *parts)

    def snapshot(self, name: str, *parts: str) -> str:
        return os.path.join(self.run_root, "snaps", name, *parts)


class Row12RegistryTests(unittest.TestCase):
    def test_the_entry_has_four_stages_two_sessions_the_s4_resume_of_the_third_session_and_the_ledger_bound(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW12)
        self.assertTrue(spec.implemented)
        self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2", "s3", "s4"])
        self.assertEqual([stage.kind for stage in spec.stages], ["work", "preclear", "resume", "preclear"])
        self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60, 15, 20])
        self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30", "0.40", "0.60"])
        self.assertEqual([stage.timeout for stage in spec.stages], [900, 1800, 900, 1200])
        self.assertEqual([stage.session for stage in spec.stages], ["new:A", "resume:A", "new:B", "resume:B"])
        self.assertEqual(pc_rows.session_count(spec), 2)
        self.assertEqual(sum(stage.cap for stage in spec.stages), Decimal("2.60"))
        self.assertEqual(pc_rows.worst_case(spec), Decimal("2.00"), "the ledger's own bound, not the sum of the caps")
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_GIT)
        self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
        self.assertEqual(spec.chain, pc_rows.CHAIN_RESUME_LINE)
        self.assertEqual(spec.hooks, (("s2", "append-plan-note"),))
        self.assertEqual(spec.analyses, ())  # the frozen-copy analysis is named in the entry by the last task of plan 04-13
        self.assertEqual(spec.path_prepend, ())
        self.assertEqual(spec.seed, "pc_rowseeds:seed_row12")
        self.assertEqual([name for name, _path in spec.prompts], ["s1", "s2", "s4"])
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        for relative, kind in spec.sources:
            full = os.path.join(ROOT, *relative.split("/"))
            self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), "a source is missing")

    def test_only_row_6_row_7_and_row_12_name_a_hook_and_the_snapshot_names_follow_one_rule(self) -> None:
        pc_rows = rows()
        named = [entry.row_id for entry in pc_rows.build_registry() if entry.hooks]
        self.assertEqual(named, ["row6-readonly-plan", "row7-all-destinations-denied", ROW12])
        spec = spec_of(ROW12)
        self.assertEqual(
            [pc_rows.snapshot_name(stage) for stage in spec.stages],
            ["snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume", "snap-4-after-refresh"],
        )
        self.assertEqual(
            [row1().snapshot_name(stage) for stage in spec.stages], [pc_rows.snapshot_name(stage) for stage in spec.stages]
        )
        planned = hooks().plan_boundaries(spec)
        self.assertEqual(
            planned,
            [
                ("setup", "snap-0-setup"),
                ("s1", "snap-1-after-work"),
                ("s2", "snap-2-after-preclear"),
                ("s2-append-plan-note", "snap-2b-after-external-plan-edit"),
                ("s3", "snap-3-after-resume"),
                ("s4", "snap-4-after-refresh"),
            ],
        )

    def test_the_hook_has_no_finalizer_and_no_perms_file_and_every_other_hook_still_has_both(self) -> None:
        pc_rowhooks = hooks()
        self.assertEqual(pc_rowhooks.HOOK_SNAPSHOTS["append-plan-note"], "snap-2b-after-external-plan-edit")
        self.assertEqual(pc_rowhooks.TARGETS["append-plan-note"], ((PLAN_RELATIVE, "file"),))
        self.assertIn("append-plan-note", pc_rowhooks.NO_FINALIZER)
        self.assertIn("append-plan-note", pc_rowhooks.NO_PERMS)
        self.assertNotIn("append-plan-note", pc_rowhooks.FINALIZER_OF)
        for hook in ("restrict-plan-444", "restrict-project-555"):
            self.assertNotIn(hook, pc_rowhooks.NO_FINALIZER)
            self.assertNotIn(hook, pc_rowhooks.NO_PERMS)
            self.assertIn(pc_rowhooks.FINALIZER_OF[hook], pc_rowhooks.FINALIZERS)

    def test_the_dry_run_prints_the_plan_lines_and_starts_no_process_and_no_harness_home(self) -> None:
        code, text, tripwire, base = dry_run_row(ROW12)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 4 stages, 2 sessions" % ROW12, text)
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith(("s1:", "s2:", "s3:", "s4:"))]
        self.assertEqual(len(lines), 4)
        self.assertIn("work turn, new session, 15 turns, cap 0.30", lines[0])
        self.assertIn("/preclear turn, resumes the s1 session, 60 turns, cap 1.30", lines[1])
        self.assertIn("fresh resume, new session, 15 turns, cap 0.40", lines[2])
        self.assertIn("/preclear turn, resumes the s3 session, 20 turns, cap 0.60", lines[3])
        self.assertIn("worst case 2.00 USD", text)
        self.assertIn("allowlist 33 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")

    def test_list_marks_row_12_implemented_with_four_stages_and_two_sessions(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        self.assertEqual(cells[ROW12][2:], ["4", "2", "yes"])
        self.assertEqual(cells[ROW11][2:], ["3", "2", "yes"])

    def test_dry_run_all_stays_under_the_ceiling_with_row_12_on_top(self) -> None:
        pc_rows = rows()
        implemented = [entry for entry in pc_rows.build_registry() if entry.implemented]
        total = sum((pc_rows.worst_case(entry) for entry in implemented), Decimal("0"))
        self.assertEqual(total, Decimal("24.40"))
        self.assertLessEqual(total, Decimal("25.00"))
        self.assertEqual(len(implemented), 13)


class Row12SeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = SeededGit(ROW12, "row12-seed")

    def test_the_seeded_claude_md_equals_the_committed_fixture_and_its_setup_digest(self) -> None:
        data = read_bytes(os.path.join(self.seeded.project, "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW12, "fixture-CLAUDE.md")), "byte for byte")
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, sha_lines(ROW12)["project/CLAUDE.md"])
        self.assertTrue(digest.startswith(CLAUDE_MD_DIGEST_PREFIX))

    def test_the_plan_equals_the_plain_data_file_and_hashes_to_the_committed_digest(self) -> None:
        data = read_bytes(os.path.join(self.seeded.project, *PLAN_RELATIVE.split("/")))
        self.assertEqual(data, read_bytes(os.path.join(DATA, "plain-plan.md")))
        self.assertEqual(hashlib.sha256(data).hexdigest(), PLAN_DIGEST)
        self.assertEqual(hashlib.sha256(data).hexdigest(), sha_lines(ROW12)["project/" + PLAN_RELATIVE])

    def test_one_commit_on_main_the_skill_copy_untracked_and_the_note_not_yet_in_the_plan(self) -> None:
        self.assertEqual(self.seeded.git("rev-list", "--count", "main").strip(), "1")
        self.assertEqual(self.seeded.git("symbolic-ref", "HEAD").strip(), "refs/heads/main")
        plan = read_text(os.path.join(self.seeded.project, *PLAN_RELATIVE.split("/")))
        self.assertNotIn("Note 2026", plan)
        self.assertTrue(plan.endswith("\n"))
        self.assertEqual(self.seeded.paths["wrapper"], os.path.join(str(self.seeded.paths["run_root"]), "wrapper", "checkpoint"))
        self.assertFalse(os.path.exists(str(self.seeded.paths["wrapper_dir"])), "a plain row has no wrapper folder")

    def test_the_row_names_the_memory_policy_and_the_run_record_carries_the_row_id(self) -> None:
        run = read_json(os.path.join(str(self.seeded.paths["raw"]), "run.json"))
        self.assertEqual(run["row"], ROW12)
        self.assertEqual(run["memory"], "pinned")
        self.assertEqual(run["bound_ledger"], "none")

    def test_the_committed_row_holds_the_two_prompts_the_registry_reads_in_place(self) -> None:
        s2 = committed(ROW12, "s2-preclear-prompt.md")
        s4 = committed(ROW12, "s4-preclear-prompt.md")
        spec = spec_of(ROW12)
        prompts = dict(spec.prompts)
        self.assertEqual(os.path.join(ROOT, *prompts["s2"].split("/")), s2)
        self.assertEqual(os.path.join(ROOT, *prompts["s4"].split("/")), s4)
        self.assertIn(b"frozen handoff copy", read_bytes(s2))
        self.assertIn(b"keep the frozen copy as it is", read_bytes(s4))
        other = committed(ROW11_COMMITTED, "s2-preclear-prompt.md")
        self.assertNotEqual(hashlib.md5(read_bytes(s2)).hexdigest(), hashlib.md5(read_bytes(other)).hexdigest())
        self.assertTrue(hashlib.md5(read_bytes(s2)).hexdigest().startswith("da2d9df3"))


class PlanNoteHookTests(unittest.TestCase):
    """The harness appends one fixed line to the plan itself, so it must not follow a path the model controls (T-04-58)."""

    def fresh(self, name: str = "row12-hook") -> SeededGit:
        return SeededGit(ROW12, name)

    def plan_path(self, seeded: SeededGit) -> str:
        return os.path.join(seeded.project, *PLAN_RELATIVE.split("/"))

    def append(self, seeded: SeededGit) -> None:
        hooks().append_plan_note(None, seeded.paths, None)

    def test_the_hook_appends_exactly_one_line_to_the_plan_and_changes_nothing_else(self) -> None:
        seeded = self.fresh()
        before = read_bytes(self.plan_path(seeded))
        mode = os.stat(self.plan_path(seeded)).st_mode & 0o777
        claude_md = read_bytes(os.path.join(seeded.project, "CLAUDE.md"))
        self.append(seeded)
        after = read_bytes(self.plan_path(seeded))
        self.assertEqual(after, before + (NOTE_LINE + "\n").encode("utf-8"))
        self.assertEqual(after.count(b"\n"), before.count(b"\n") + 1)
        self.assertEqual(os.stat(self.plan_path(seeded)).st_mode & 0o777, mode)
        self.assertEqual(read_bytes(os.path.join(seeded.project, "CLAUDE.md")), claude_md)
        self.assertEqual(hooks().PLAN_NOTE_LINE, NOTE_LINE)

    def test_a_newline_is_added_first_only_when_the_plan_does_not_end_in_one(self) -> None:
        seeded = self.fresh("row12-hook-nl")
        path = self.plan_path(seeded)
        before = read_bytes(path)
        self.assertTrue(before.endswith(b"\n"))
        with open(path, "wb") as handle:
            handle.write(before.rstrip(b"\n"))
        self.append(seeded)
        self.assertEqual(read_bytes(path), before.rstrip(b"\n") + b"\n" + NOTE_LINE.encode("utf-8") + b"\n")

    def test_an_empty_plan_gets_the_note_line_without_a_leading_newline(self) -> None:
        seeded = self.fresh("row12-hook-empty")
        path = self.plan_path(seeded)
        with open(path, "wb"):
            pass
        self.append(seeded)
        self.assertEqual(read_bytes(path), (NOTE_LINE + "\n").encode("utf-8"))

    def test_the_open_is_append_only_it_never_truncates_and_never_creates(self) -> None:
        pc_rowhooks = hooks()
        seen = []
        real_open = os.open

        def spy(path, flags, *args, **kwargs):
            if str(path).endswith(PLAN_RELATIVE):
                seen.append(flags)
            return real_open(path, flags, *args, **kwargs)

        seeded = self.fresh("row12-hook-flags")
        from unittest import mock

        with mock.patch.object(pc_rowhooks.os, "open", side_effect=spy):
            self.append(seeded)
        writers = [flags for flags in seen if flags & os.O_ACCMODE == os.O_WRONLY]
        self.assertEqual(len(writers), 1)
        self.assertTrue(writers[0] & os.O_APPEND)
        self.assertTrue(writers[0] & os.O_NOFOLLOW)
        self.assertFalse(writers[0] & os.O_TRUNC)
        self.assertFalse(writers[0] & os.O_CREAT)
        for flags in seen:
            self.assertFalse(flags & (os.O_TRUNC | os.O_CREAT))

    def test_a_missing_plan_is_refused_and_nothing_is_created(self) -> None:
        seeded = self.fresh("row12-hook-missing")
        path = self.plan_path(seeded)
        os.rename(path, path + ".moved")
        with self.assertRaises(hooks().HookRefused):
            self.append(seeded)
        self.assertFalse(os.path.lexists(path), "the hook never creates the plan")

    def test_a_symlink_at_the_plan_path_is_refused_and_the_outside_file_is_unchanged(self) -> None:
        seeded = self.fresh("row12-hook-link")
        outside = os.path.join(tempfile.mkdtemp(prefix="pc-note-"), "outside.txt")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write("outside\n")
        path = self.plan_path(seeded)
        os.rename(path, path + ".moved")
        os.symlink(outside, path)
        with self.assertRaises(hooks().HookRefused) as caught:
            self.append(seeded)
        self.assertNotIn(os.sep, str(caught.exception), "fixed text, no path")
        self.assertEqual(read_text(outside), "outside\n")

    def test_a_plan_folder_swapped_for_a_symlink_is_refused_and_the_target_is_unchanged(self) -> None:
        seeded = self.fresh("row12-hook-folder")
        plans = os.path.join(seeded.project, "thoughts", "plans")
        real = os.path.join(seeded.project, "thoughts", "plans-real")
        os.rename(plans, real)
        os.symlink(real, plans)
        before = read_bytes(os.path.join(real, os.path.basename(PLAN_RELATIVE)))
        with self.assertRaises(hooks().HookRefused):
            self.append(seeded)
        self.assertEqual(read_bytes(os.path.join(real, os.path.basename(PLAN_RELATIVE))), before)

    def test_a_second_name_a_read_only_plan_and_a_folder_in_its_place_are_refused(self) -> None:
        seeded = self.fresh("row12-hook-others")
        path = self.plan_path(seeded)
        before = read_bytes(path)
        os.chmod(path, 0o444)
        with self.assertRaises(hooks().HookRefused):
            self.append(seeded)
        os.chmod(path, 0o644)
        extra = os.path.join(tempfile.mkdtemp(prefix="pc-note-"), "second-name.txt")
        os.link(path, extra)
        with self.assertRaises(hooks().HookRefused):
            self.append(seeded)
        self.assertEqual(read_bytes(path), before)
        os.rename(path, path + ".moved")
        os.mkdir(path)
        with self.assertRaises(hooks().HookRefused):
            self.append(seeded)

    def test_a_target_that_is_not_in_the_table_is_never_reached_from_here(self) -> None:
        pc_rowhooks = hooks()
        self.assertEqual(pc_rowhooks.TARGETS["append-plan-note"], ((PLAN_RELATIVE, "file"),))
        self.assertNotIn("append-plan-note", pc_rowhooks.CHANGES)


class Row12ChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chain = Row12Run()
        assert cls.chain.outcome.code == 0, "\n".join(cls.chain.outcome.lines)

    def argv(self, index: int) -> list:
        return self.chain.rig.calls()[index]["args"]

    def flag(self, index: int, name: str) -> str:
        args = self.argv(index)
        return args[args.index(name) + 1]

    def test_four_stages_are_launched_once_each_with_the_pinned_turns_and_caps(self) -> None:
        calls = self.chain.rig.calls()
        self.assertEqual(len(calls), 4)
        self.assertEqual([self.flag(i, "--max-turns") for i in range(4)], ["15", "60", "15", "20"])
        self.assertEqual([self.flag(i, "--max-budget-usd") for i in range(4)], ["0.30", "1.30", "0.40", "0.60"])
        for index in range(4):
            self.assertEqual(len(self.flag(index, "--allowedTools").split(",")), 33)

    def test_s4_resumes_the_s3_session_not_the_s2_one_and_the_session_count_stays_two(self) -> None:
        first = read_json(self.chain.raw("run.json"))["session_id"]
        self.assertEqual(self.flag(0, "--session-id"), first)
        self.assertNotIn("--resume", self.argv(0))
        self.assertEqual(self.flag(1, "--resume"), first)
        third = self.flag(2, "--session-id")
        self.assertNotEqual(third, first)
        self.assertNotIn("--resume", self.argv(2))
        self.assertEqual(self.flag(3, "--resume"), third, "s4 carries s3's session id")
        self.assertNotEqual(self.flag(3, "--resume"), first)
        self.assertNotIn("--session-id", self.argv(3))
        records = [read_json(self.chain.raw("s%d.record.json" % n)) for n in range(1, 5)]
        self.assertEqual([r["session_id"] for r in records], [first, first, third, third])
        self.assertEqual(len(set(r["session_id"] for r in records)), 2)
        self.assertEqual([r["resume"] for r in records], [False, True, False, True])

    def test_the_prompts_are_the_plain_s1_prompt_the_committed_s2_and_s4_files_and_the_printed_resume_line(self) -> None:
        calls = self.chain.rig.calls()
        self.assertEqual(calls[1]["prompt"].encode("utf-8"), read_bytes(committed(ROW12, "s2-preclear-prompt.md")))
        self.assertEqual(calls[3]["prompt"].encode("utf-8"), read_bytes(committed(ROW12, "s4-preclear-prompt.md")))
        self.assertEqual(calls[0]["prompt"], read_text(os.path.join(DATA, "plain-s1-prompt.md")))
        self.assertTrue(calls[2]["prompt"].startswith("Resume widget-export from "))
        self.assertTrue(calls[2]["prompt"].replace(self.chain.run_root, "$RUN").endswith("CSV done; draft JSON-default diff for review"))
        for index in range(4):
            self.assertEqual(self.flag(index, "--model"), "claude-sonnet-5-5")

    def test_the_plan_ends_with_the_note_line_exactly_once_and_the_chain_record_is_the_resume_line_shape(self) -> None:
        plan = read_text(self.chain.project(*PLAN_RELATIVE.split("/")))
        self.assertTrue(plan.endswith(NOTE_LINE + "\n"))
        self.assertEqual(plan.count(NOTE_LINE), 1)
        chain = read_json(self.chain.raw("chain.json"))
        self.assertEqual(chain["marker"], "found")
        self.assertEqual(sorted(os.listdir(os.path.join(self.chain.run_root, "snaps"))), sorted(SNAPSHOTS))

    def test_the_plan_digest_differs_between_snapshot_2_and_2b_only_by_the_appended_line(self) -> None:
        before = dict(
            line.split("  ", 1)[::-1] for line in read_text(self.chain.snapshot("snap-2-after-preclear", "sha.txt")).splitlines()
        )
        after = dict(
            line.split("  ", 1)[::-1]
            for line in read_text(self.chain.snapshot("snap-2b-after-external-plan-edit", "sha.txt")).splitlines()
        )
        self.assertEqual(sorted(before), sorted(after), "the same files are listed")
        changed = sorted(name for name in before if before[name] != after[name])
        self.assertEqual(changed, ["project/" + PLAN_RELATIVE])
        original = read_bytes(os.path.join(DATA, "plain-plan.md"))
        self.assertEqual(before["project/" + PLAN_RELATIVE], hashlib.sha256(original).hexdigest())
        self.assertEqual(
            after["project/" + PLAN_RELATIVE], hashlib.sha256(original + (NOTE_LINE + "\n").encode("utf-8")).hexdigest()
        )

    def test_the_hook_takes_its_own_boundary_with_a_git_state_and_a_guard_and_no_perms_file(self) -> None:
        for suffix in (".git.json", ".guard.json"):
            self.assertTrue(os.path.isfile(self.chain.raw("s2-append-plan-note" + suffix)), suffix)
        self.assertFalse(os.path.exists(self.chain.snapshot("snap-2b-after-external-plan-edit", "perms.txt")))
        self.assertTrue(os.path.isfile(self.chain.snapshot("snap-2b-after-external-plan-edit", "status.txt")))
        boundaries = [pair["name"] for pair in read_json(self.chain.raw("boundaries.json"))["boundaries"]]
        self.assertEqual(boundaries, ["setup", "s1", "s2", "s2-append-plan-note", "s3", "s4"])

    def test_the_s4_delta_is_its_cumulative_total_minus_the_s3_chain_total(self) -> None:
        s3 = read_json(self.chain.raw("s3.record.json"))
        s4 = read_json(self.chain.raw("s4.record.json"))
        self.assertEqual(Decimal(s3["cumulative"]), Decimal("0.04"))
        self.assertEqual(Decimal(s4["cumulative"]), Decimal("0.10"))
        self.assertEqual(Decimal(s4["cumulative"]) - Decimal(s3["cumulative"]), Decimal(s4["delta"]))
        self.assertEqual(Decimal(s4["delta"]), Decimal("0.06"))
        self.assertEqual(s4["cumulative_consistent"], "yes")

    def test_the_ledger_holds_one_launch_and_one_settle_per_stage_in_order(self) -> None:
        self.assertEqual(
            [(r["kind"], r["stage"]) for r in self.chain.ledger()],
            [
                ("launch", "row12-s1"),
                ("settle", "row12-s1"),
                ("launch", "row12-s2"),
                ("settle", "row12-s2"),
                ("launch", "row12-s3"),
                ("settle", "row12-s3"),
                ("launch", "row12-s4"),
                ("settle", "row12-s4"),
            ],
        )
        self.assertEqual(self.chain.outcome.spent, Decimal("0.19"))

    def test_the_row_is_filed_as_one_folder_with_no_stop_label(self) -> None:
        self.assertEqual(os.listdir(self.chain.ctx.destination), [ROW12])
        names = tree_names(self.chain.row_dir)
        self.assertIn("README.md", names)
        self.assertIn("mechanical-checks.md", names)
        self.assertEqual(self.chain.outcome.code, pc_exitcodes.OK)


class Row12PlantedSymlinkTests(unittest.TestCase):
    def test_a_symlink_planted_at_the_plan_path_in_s2_stops_the_row_with_11_and_the_outside_file_is_unchanged(self) -> None:
        rig = pc_testutil.RowRig(
            stages=row12_stages(
                s2_ops=[
                    {"op": "rename", "path": PLAN_TOKEN, "to": PLAN_TOKEN + ".moved"},
                    {"op": "symlink", "path": PLAN_TOKEN, "target": "$OUTSIDE/target.txt"},
                ]
            )
        )
        outside = os.path.join(rig.outside, "target.txt")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write("outside\n")
        run = Registered(ROW12, rig=rig)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertIn(row1().MESSAGE_HOOK_REFUSED % "s2", run.outcome.lines)
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW12])
        self.assertEqual(read_text(outside), "outside\n")
        self.assertEqual(len(rig.calls()), 2, "s3 never started")
        self.assertFalse(os.path.lexists(os.path.join(run.run_root, "snaps", "snap-2b-after-external-plan-edit")))
        stop = read_text(os.path.join(run.ctx.destination, "STOPPED-" + ROW12, "stop.txt"))
        self.assertIn("reason: breach", stop.splitlines())


if __name__ == "__main__":
    unittest.main()
