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

import datetime
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
from decimal import Decimal

import pc_exitcodes
import pc_spend
import pc_testutil
from test_evidence import verdict_pattern
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
DASH = "\u2014"
FIRST_DESTINATION = "rerun-2026-10-28-claude-sonnet-5-5-first"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
S4_NAMES = (
    "s4-preclear-prompt.md",
    "s4-preclear-refresh-trace.md",
    "s4-preclear-refresh-full-trace.md",
    "s4.err",
    "s4.exit",
)


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


def row12_stages(deltas=("0.03", "0.06", "0.04", "0.06"), s2_ops=(), s4_ops=None, s3_ops=(), frozen=True) -> list:
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
    frozen_ops = checkpoint_write(CHECKPOINT_DIR + "/" + FROZEN_NAME, "frozen copy of the checkpoint\n") if frozen else []
    stages = pc_testutil._with_ops(stages, 1, frozen_ops + list(s2_ops))
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
        self.assertEqual(spec.analyses, ("frozen-copy",))
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
        # row 2 names the hook that arms the wrapper (plan 04-15)
        # the bound-ledger layout names the lint hook (plan 04-15; it comes first in the registry)
        self.assertEqual(named, ["bound-ledger", "row2-double-conflict", "row6-readonly-plan", "row7-all-destinations-denied", ROW12])
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

    def test_dry_run_all_total_is_the_sum_of_the_worst_cases_and_each_entry_fits_the_row_cap_and_the_invocation_budget(self) -> None:
        # Plan 04-15 adds row 2, rows 3a, 3b, 3c and 4b at 1.60 each and three layouts at 2.00 each: 13 entries at 24.40 became
        # 21 at 38.40. The sum of the worst cases is no longer under the
        # 25.00 invocation ceiling (pc_flags.INVOCATION_BUDGET_MAX); that ceiling is not raised. The driver does not refuse a
        # plan whose sum is above the budget: it stops before the row whose worst case would take the settled spend above it.
        import pc_flags

        pc_rows = rows()
        implemented = [entry for entry in pc_rows.build_registry() if entry.implemented]
        total = sum((pc_rows.worst_case(entry) for entry in implemented), Decimal("0"))
        self.assertEqual(total, Decimal("38.40"))
        self.assertEqual(len(implemented), 21)
        self.assertEqual(Decimal(pc_flags.format_invocation_budget("25.00")), Decimal("25.00"), "the ceiling is unchanged")
        for entry in implemented:
            self.assertLessEqual(pc_rows.worst_case(entry), pc_rows.ROW_CAP, entry.row_id)


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


    def test_the_filed_s4_files_carry_the_committed_names_and_every_one_exists_in_the_committed_row(self) -> None:
        filed = set(tree_names(self.chain.row_dir))
        committed_names = set(tree_names(committed(ROW12)))
        for name in S4_NAMES:
            self.assertIn(name, filed, name)
            self.assertIn(name, committed_names, name)
        for folder in ("snap-2b-after-external-plan-edit/", "snap-4-after-refresh/"):
            self.assertIn(folder, filed)
            self.assertIn(folder, committed_names)
        stage_files = sorted(name for name in filed if name[:2] in ("s1", "s2", "s3", "s4") and "/" not in name)
        self.assertEqual(
            [name for name in stage_files if name.startswith("s4")], sorted(S4_NAMES), "no other s4 name is filed"
        )
        self.assertNotIn("s4-preclear-trace.md", filed)
        self.assertNotIn("s4-preclear.exit", filed)

    def test_the_filed_s4_prompt_is_the_committed_prompt_and_the_s4_exit_file_reads_exit_zero(self) -> None:
        self.assertEqual(
            read_bytes(os.path.join(self.chain.row_dir, "s4-preclear-prompt.md")),
            read_bytes(committed(ROW12, "s4-preclear-prompt.md")),
        )
        self.assertEqual(read_text(os.path.join(self.chain.row_dir, "s4.exit")), read_text(committed(ROW12, "s4.exit")))
        self.assertEqual(read_text(os.path.join(self.chain.row_dir, "s4.err")), "")

    def test_the_filed_snapshot_of_s4_holds_the_refreshed_checkpoint_and_the_frozen_copy_of_s2(self) -> None:
        folder = os.path.join(self.chain.row_dir, "snap-4-after-refresh", "preclear", "widget-export")
        self.assertEqual(sorted(os.listdir(folder)), [FROZEN_NAME, "checkpoint.md"])
        self.assertIn("refreshed", read_text(os.path.join(folder, "checkpoint.md")))


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


def first_destination_chain(stages):
    """A chain filed into a side folder, so the dated folder is free for the refile (as test_row7 does)."""
    rig = pc_testutil.RowRig(stages=stages)
    first = os.path.join(rig.repo, "tests", "evidence", FIRST_DESTINATION)
    ctx = rig.context(destination=first)
    outcome = row1().run_registered_row(ctx, ROW12)
    assert outcome.code == 0, "\n".join(outcome.lines)
    names = sorted(os.listdir(ctx.runs_root))
    assert len(names) == 1, names
    return rig, ctx, os.path.join(ctx.runs_root, names[0])


def rewrite_chain(run_root: str, **changes) -> None:
    path = os.path.join(run_root, "raw", "chain.json")
    record = read_json(path)
    record.update(changes)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle)


def no_resume_line_stages() -> list:
    stages = row12_stages()
    stages[1]["result"] = dict(stages[1]["result"], text="Checkpoint written, nothing to paste.\n")
    return stages


class Row12ShapeTests(unittest.TestCase):
    """The chain has two valid shapes: found with s1 to s4, and none with s1 and s2 only."""

    def refile(self, rig, run_root):
        out, err = io.StringIO(), io.StringIO()
        code = matrix().main(
            ["--refile", run_root], env=dict(rig.env), repo_root=rig.repo, clock=lambda: FIXED_DATE, out=out, err=err
        )
        return code, out.getvalue() + err.getvalue()

    def dated(self, rig) -> str:
        return os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5")

    def test_a_chain_with_no_resume_line_runs_s1_and_s2_only_records_none_and_is_filed(self) -> None:
        run = Registered(ROW12, stages=no_resume_line_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), 2, "no s3 and no s4 was launched")
        self.assertEqual(read_json(run.raw("chain.json"))["marker"], "NO-RESUME-LINE")
        names = tree_names(run.row_dir)
        self.assertIn("s2-preclear-trace.md", names)
        for name in S4_NAMES + ("s3-resume-trace.md", "s3-resume.exit"):
            self.assertNotIn(name, names, name)
        snaps = sorted(os.listdir(os.path.join(run.run_root, "snaps")))
        self.assertEqual(snaps, ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-2b-after-external-plan-edit"])
        self.assertEqual(sorted(r["stage"] for r in run.ledger() if r["kind"] == "launch"), ["row12-s1", "row12-s2"])
        plan = read_text(os.path.join(run.run_root, "project", *PLAN_RELATIVE.split("/")))
        self.assertTrue(plan.endswith(NOTE_LINE + "\n"), "the hook ran after s2 even though the chain ended")

    def test_refile_accepts_the_found_run_with_four_stages_and_the_none_run_with_two_and_starts_no_process(self) -> None:
        for stages, expect_s4 in ((row12_stages(), True), (no_resume_line_stages(), False)):
            rig, ctx, run_root = first_destination_chain(stages)
            calls = len(rig.calls())
            code, text = self.refile(rig, run_root)
            self.assertEqual(code, 0, text)
            self.assertEqual(len(rig.calls()), calls, "a refile starts no process")
            names = tree_names(os.path.join(self.dated(rig), ROW12))
            self.assertEqual("s4-preclear-refresh-trace.md" in names, expect_s4)
            self.assertIn("s2-preclear-trace.md", names)

    def test_refile_refuses_a_found_marker_with_three_stages(self) -> None:
        rig, ctx, run_root = first_destination_chain(row12_stages())
        trimmed = run_root + "-no-s4"
        shutil.copytree(
            run_root,
            trimmed,
            symlinks=True,
            ignore=lambda folder, names: [
                name for name in names if name.startswith(("s4.", "s4-")) or name == "snap-4-after-refresh"
            ],
        )
        self.assertFalse(os.path.lexists(os.path.join(trimmed, "raw", "s4.record.json")))
        self.assertEqual(read_json(os.path.join(trimmed, "raw", "chain.json"))["marker"], "found")
        code, text = self.refile(rig, trimmed)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, text)
        self.assertFalse(os.path.lexists(self.dated(rig)), "nothing was filed")

    def test_refile_refuses_the_none_marker_with_four_stages_and_the_odd_marker_words(self) -> None:
        for marker in ("NO-RESUME-LINE", "NO-PRINTED-CHECKPOINT", "", None, "other"):
            rig, ctx, run_root = first_destination_chain(row12_stages())
            rewrite_chain(run_root, marker=marker)
            code, text = self.refile(rig, run_root)
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, "%r %s" % (marker, text))
            self.assertFalse(os.path.lexists(self.dated(rig)))

    def test_the_chain_rule_drops_every_stage_from_the_first_resume_stage_on_when_the_marker_is_none(self) -> None:
        import pc_evidence

        rig, ctx, run_root = first_destination_chain(row12_stages())
        data = pc_evidence.load_stage_data(run_root)
        spec = spec_of(ROW12)
        self.assertEqual([stage.name for stage in data.stages], ["s1", "s2", "s3", "s4"])
        self.assertIsNone(pc_evidence._chain_incomplete(data, spec))
        missing = pc_evidence.MESSAGE_STAGE_MISSING
        found3 = data._replace(stages=data.stages[:3])
        self.assertEqual(pc_evidence._chain_incomplete(found3, spec), missing)
        none = dict(data.chain, marker="NO-RESUME-LINE")
        for stages, ok in (
            (data.stages[:2], True),
            (data.stages[:1], False),
            (data.stages[:3], False),
            (data.stages, False),
            ([data.stages[0], data.stages[1], data.stages[3]], False),
        ):
            result = pc_evidence._chain_incomplete(data._replace(stages=stages, chain=none), spec)
            self.assertEqual(result is None, ok, [stage.name for stage in stages])

    def test_a_row_with_a_single_preclear_stage_names_its_files_as_before(self) -> None:
        import pc_evidence

        row1_spec = spec_of("row1-wrong-binding")
        self.assertEqual(
            [pc_evidence.stage_label(row1_spec, name) for name in ("s1", "s2", "s3")], ["s1-work", "s2-preclear", "s3-resume"]
        )
        self.assertEqual([pc_evidence.exit_label(row1_spec, name) for name in ("s1", "s2", "s3")], ["s1", "s2-preclear", "s3-resume"])
        spec = spec_of(ROW12)
        self.assertEqual(
            [pc_evidence.stage_label(spec, name) for name in ("s1", "s2", "s3", "s4")],
            ["s1-work", "s2-preclear", "s3-resume", "s4-preclear-refresh"],
        )
        self.assertEqual(
            [pc_evidence.prompt_label(spec, name) for name in ("s2", "s4")], ["s2-preclear", "s4-preclear"]
        )
        self.assertEqual([pc_evidence.exit_label(spec, name) for name in ("s1", "s2", "s3", "s4")], ["s1", "s2-preclear", "s3-resume", "s4"])


class Row12CapTests(unittest.TestCase):
    """The fourth stage never takes the row past 2.00: the ledger refuses the launch and the harness never raises the cap."""

    def execute(self, deltas):
        rig = pc_testutil.RowRig(stages=row12_stages(deltas=deltas))
        out, err = io.StringIO(), io.StringIO()
        code = matrix().execute_row(spec_of(ROW12), rig.context(), out, err)
        return rig, code, out.getvalue() + err.getvalue()

    def ledger(self, rig) -> list:
        return pc_spend.read_records(rig.context().harness_home)

    def test_the_s4_launch_is_refused_with_18_before_any_process_when_the_first_three_settled_past_the_bound(self) -> None:
        rig, code, text = self.execute(("0.30", "0.71", "0.40", "0.06"))  # 1.41 settled; 1.41 + 0.60 passes 2.00
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, text)
        self.assertEqual(len(rig.calls()), 3, "no fourth process was started")
        stages = [(r["kind"], r["stage"]) for r in self.ledger(rig)]
        self.assertEqual(
            stages,
            [("launch", "row12-s1"), ("settle", "row12-s1"), ("launch", "row12-s2"), ("settle", "row12-s2"), ("launch", "row12-s3"), ("settle", "row12-s3")],
        )
        self.assertNotIn("row12-s4", [stage for _kind, stage in stages], "the ledger holds no s4 launch line")
        self.assertEqual(rig.tripwire(), [])

    def test_the_refusal_writes_no_authorization_line_and_changes_no_cap(self) -> None:
        rig, code, text = self.execute(("0.30", "0.71", "0.40", "0.06"))
        self.assertEqual(code, pc_exitcodes.BUDGET_REFUSED, text)
        self.assertEqual({r["kind"] for r in self.ledger(rig)}, {"launch", "settle"})
        self.assertEqual(
            [str(stage.cap) for stage in spec_of(ROW12).stages], ["0.30", "1.30", "0.40", "0.60"], "the registry caps are untouched"
        )
        self.assertEqual(rows().worst_case(spec_of(ROW12)), Decimal("2.00"))
        self.assertEqual(rows().ROW_CAP, Decimal("2.00"))

    def test_the_boundary_is_exact_1_40_settled_still_launches_s4_and_the_row_ends_at_2_00_pessimistic(self) -> None:
        rig, code, text = self.execute(("0.30", "0.70", "0.40", "0.06"))  # 1.40 + 0.60 is exactly 2.00
        self.assertEqual(code, pc_exitcodes.OK, text)
        self.assertEqual(len(rig.calls()), 4)
        launches = [r for r in self.ledger(rig) if r["kind"] == "launch"]
        self.assertEqual([r["stage"] for r in launches], ["row12-s1", "row12-s2", "row12-s3", "row12-s4"])
        self.assertEqual(launches[3]["cap"], Decimal("0.60"))
        self.assertEqual(pc_spend.row_pessimistic_total(rig.context().harness_home, "row12-frozen-handoff"), Decimal("1.46"))

    def test_the_s4_delta_is_taken_against_the_s3_chain_total_not_the_s2_one(self) -> None:
        rig = pc_testutil.RowRig(stages=row12_stages(deltas=("0.30", "0.50", "0.20", "0.07")))
        run = Registered(ROW12, rig=rig)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        s2 = read_json(run.raw("s2.record.json"))
        s3 = read_json(run.raw("s3.record.json"))
        s4 = read_json(run.raw("s4.record.json"))
        self.assertEqual(Decimal(s2["cumulative"]), Decimal("0.80"))
        self.assertEqual(Decimal(s3["cumulative"]), Decimal("0.20"))
        self.assertEqual(Decimal(s4["cumulative"]), Decimal("0.27"))
        self.assertEqual(Decimal(s4["delta"]), Decimal("0.07"))
        self.assertEqual(Decimal(s4["cumulative"]) - Decimal(s3["cumulative"]), Decimal(s4["delta"]))
        self.assertEqual(s4["cumulative_consistent"], "yes")


def section_lines(run, title: str = "Frozen copy") -> list:
    text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
    return text.split("## %s\n" % title, 1)[1].split("\n## ", 1)[0].splitlines()


def sha_of_file(path: str) -> str:
    return hashlib.sha256(read_bytes(path)).hexdigest()


def review():
    import pc_review

    return pc_review


class FrozenCopyTests(unittest.TestCase):
    """The Frozen copy section prints digests, counts and yes or no equality read from the filed snapshot copies only."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.kept = Row12Run()
        assert cls.kept.outcome.code == 0, "\n".join(cls.kept.outcome.lines)
        rewriting = checkpoint_write(CHECKPOINT_DIR + "/" + FROZEN_NAME, "the frozen copy was rewritten\n") + checkpoint_write(
            CHECKPOINT_DIR + "/checkpoint.md", "## Identity and state\nrefreshed\n"
        )
        cls.rewritten = Row12Run(stages=row12_stages(s4_ops=rewriting))
        assert cls.rewritten.outcome.code == 0, "\n".join(cls.rewritten.outcome.lines)
        cls.without = Row12Run(stages=row12_stages(frozen=False))
        assert cls.without.outcome.code == 0, "\n".join(cls.without.outcome.lines)
        cls.stopped_early = Registered(ROW12, stages=no_resume_line_stages())
        assert cls.stopped_early.outcome.code == 0, "\n".join(cls.stopped_early.outcome.lines)

    def test_the_registry_names_the_analysis_and_the_section_is_filed_once_at_the_end_of_the_checks(self) -> None:
        self.assertIn("frozen-copy", review().ANALYSES)
        self.assertEqual(review().FROZEN_COPY_SECTION, "Frozen copy")
        text = read_text(os.path.join(self.kept.row_dir, "mechanical-checks.md"))
        self.assertEqual(text.count("## Frozen copy\n"), 1)
        self.assertTrue(text.rstrip("\n").splitlines()[-1].startswith("frozen-copy "), "the section is the last one")

    def test_an_untouched_frozen_copy_lists_its_digest_in_all_four_snapshots_and_equal_yes(self) -> None:
        lines = section_lines(self.kept)
        frozen = sha_of_file(os.path.join(self.kept.snapshot("snap-2-after-preclear"), "preclear", "widget-export", FROZEN_NAME))
        for snapshot in review().FROZEN_SNAPSHOTS:
            self.assertIn("%s: frozen-copies 1" % snapshot, lines)
            self.assertIn("%s: frozen-copy widget-export/%s sha256 %s" % (snapshot, FROZEN_NAME, frozen), lines)
            checkpoint = sha_of_file(os.path.join(self.kept.snapshot(snapshot), "preclear", "widget-export", "checkpoint.md"))
            self.assertIn("%s: checkpoint widget-export/checkpoint.md sha256 %s" % (snapshot, checkpoint), lines)
        self.assertIn("frozen-copy-names-in-any-snapshot: 1", lines)
        self.assertIn(
            "frozen-copy widget-export/%s: held-in-snapshots 4 of 4, digest-same-in-every-snapshot-that-holds-it yes" % FROZEN_NAME,
            lines,
        )

    def test_the_mutable_checkpoint_digest_changes_with_the_refresh_and_the_frozen_digest_does_not(self) -> None:
        lines = section_lines(self.kept)
        checkpoint = [line.split(" ")[-1] for line in lines if " checkpoint widget-export/checkpoint.md sha256 " in line]
        self.assertEqual(len(checkpoint), 4)
        self.assertNotEqual(checkpoint[0], checkpoint[3], "the scripted s4 rewrote the mutable checkpoint")
        self.assertEqual(checkpoint[0], checkpoint[1])
        self.assertEqual(checkpoint[1], checkpoint[2])
        frozen = set(line.split(" ")[-1] for line in lines if " frozen-copy widget-export/" in line and " sha256 " in line)
        self.assertEqual(len(frozen), 1)

    def test_a_scripted_s4_that_rewrites_the_frozen_copy_gives_equal_no_and_still_no_verdict_word(self) -> None:
        lines = section_lines(self.rewritten)
        self.assertIn(
            "frozen-copy widget-export/%s: held-in-snapshots 4 of 4, digest-same-in-every-snapshot-that-holds-it no" % FROZEN_NAME,
            lines,
        )
        digests = [line.split(" ")[-1] for line in lines if " frozen-copy widget-export/" in line and " sha256 " in line]
        self.assertEqual(len(digests), 4)
        self.assertEqual(len(set(digests[:3])), 1)
        self.assertNotEqual(digests[2], digests[3])
        for run in (self.kept, self.rewritten, self.without, self.stopped_early):
            text = "\n".join(section_lines(run))
            self.assertIsNone(verdict_pattern().search(text), "no verdict word")
            for word in ("correct", "wrong", "good", "bad", "unchanged", "violat", "intact", "broken"):
                self.assertNotIn(word, text.lower(), word)

    def test_a_run_with_no_frozen_copy_prints_zero_copies_and_no_error(self) -> None:
        lines = section_lines(self.without)
        for snapshot in review().FROZEN_SNAPSHOTS:
            self.assertIn("%s: frozen-copies 0" % snapshot, lines)
        self.assertIn("frozen-copy-names-in-any-snapshot: 0", lines)
        self.assertEqual([line for line in lines if line.startswith("frozen-copy ")], [])
        self.assertNotIn("UNCONFIRMED", "\n".join(lines))

    def test_a_chain_that_ended_after_s2_reports_the_later_snapshot_folders_as_absent(self) -> None:
        lines = section_lines(self.stopped_early)
        self.assertIn("snap-3-after-resume: snapshot folder absent", lines)
        self.assertIn("snap-4-after-refresh: snapshot folder absent", lines)
        self.assertIn("snap-2b-after-external-plan-edit: frozen-copies 1", lines)
        self.assertIn("frozen-copy widget-export/%s: held-in-snapshots 2 of 4, digest-same-in-every-snapshot-that-holds-it yes" % FROZEN_NAME, lines)

    def test_the_section_adds_no_file_to_the_row_folder_and_holds_no_path_or_session_id(self) -> None:
        names = set(tree_names(self.kept.row_dir))
        self.assertFalse(any("frozen" in name for name in names if "/" not in name), "no extra flat file")
        text = "\n".join(section_lines(self.kept))
        self.assertNotIn(self.kept.run_root, text)
        self.assertNotIn(os.sep + "tmp", text)

    def snaps(self, layout: dict) -> str:
        base = tempfile.mkdtemp(prefix="pc-frozen-")
        for snapshot, files in layout.items():
            folder = os.path.join(base, snapshot)
            os.makedirs(folder)
            if files is None:
                continue
            os.makedirs(os.path.join(folder, "preclear"))
            for relative, text in files.items():
                full = os.path.join(folder, "preclear", *relative.split("/"))
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "w", encoding="utf-8") as handle:
                    handle.write(text)
        return base

    def test_a_snapshot_folder_without_a_preclear_copy_prints_absent_and_a_missing_folder_prints_absent(self) -> None:
        base = self.snaps({"snap-2-after-preclear": None, "snap-2b-after-external-plan-edit": {"w/checkpoint.md": "a\n"}})
        lines = review().frozen_copy_lines(base)
        self.assertIn("snap-2-after-preclear: preclear copy absent", lines)
        self.assertIn("snap-2b-after-external-plan-edit: frozen-copies 0", lines)
        self.assertIn("snap-3-after-resume: snapshot folder absent", lines)
        self.assertIn("snap-4-after-refresh: snapshot folder absent", lines)
        self.assertEqual(review().frozen_copy_lines(tempfile.mkdtemp(prefix="pc-frozen-"))[0], "snap-2-after-preclear: snapshot folder absent")

    def test_only_names_of_the_frozen_pattern_count_and_a_link_or_a_folder_of_that_name_is_skipped(self) -> None:
        good = "checkpoint-20261019T233549Z-k7q2.md"
        base = self.snaps(
            {
                "snap-2-after-preclear": {
                    "w/checkpoint.md": "mutable\n",
                    "w/" + good: "frozen\n",
                    "w/checkpoint-notatime-k7q2.md": "x\n",
                    "w/checkpoint-20261019T233549Z.md": "x\n",
                    "w/checkpoint-20261019T233549Z-k7q2.txt": "x\n",
                    "w/old-" + good: "x\n",
                    "other/" + good: "second\n",
                }
            }
        )
        folder = os.path.join(base, "snap-2-after-preclear", "preclear")
        os.symlink(os.path.join(folder, "w", good), os.path.join(folder, "w", "checkpoint-20261019T233550Z-zzzz.md"))
        os.makedirs(os.path.join(folder, "w", "checkpoint-20261019T233551Z-dirs.md"))
        lines = review().frozen_copy_lines(base)
        self.assertIn("snap-2-after-preclear: frozen-copies 2", lines)
        self.assertEqual(len([line for line in lines if line.startswith("snap-2-after-preclear: frozen-copy ")]), 2)
        self.assertIn("frozen-copy-names-in-any-snapshot: 2", lines)

    def test_the_list_of_one_snapshot_is_capped_and_the_rest_is_counted(self) -> None:
        files = dict(("w/checkpoint-20261019T2335%02dZ-a%d.md" % (n % 60, n), "x%d\n" % n) for n in range(review().MAX_FROZEN_FILES + 3))
        lines = review().frozen_copy_lines(self.snaps({"snap-2-after-preclear": files}))
        listed = [line for line in lines if line.startswith("snap-2-after-preclear: frozen-copy ")]
        self.assertEqual(len(listed), review().MAX_FROZEN_FILES)
        self.assertIn("snap-2-after-preclear: frozen-copies %d" % (review().MAX_FROZEN_FILES + 3), lines)
        self.assertIn("snap-2-after-preclear: frozen-copies-not-listed 3", lines)

    def test_read_over_the_committed_row_12_snapshots_in_place_the_one_frozen_copy_is_equal_in_all_four(self) -> None:
        lines = review().frozen_copy_lines(committed(ROW12))
        self.assertIn("frozen-copy-names-in-any-snapshot: 1", lines)
        self.assertIn(
            "frozen-copy widget-export/%s: held-in-snapshots 4 of 4, digest-same-in-every-snapshot-that-holds-it yes" % FROZEN_NAME,
            lines,
        )
        digests = set(line.split(" ")[-1] for line in lines if " frozen-copy widget-export/" in line and " sha256 " in line)
        self.assertEqual(len(digests), 1)
        # the committed copies are the sanitized ones, so their digest is not the one measured on the original file
        checkpoints = set(line.split(" ")[-1] for line in lines if " checkpoint widget-export/checkpoint.md sha256 " in line)
        self.assertGreaterEqual(len(checkpoints), 2, "the refresh changed the mutable checkpoint")

    def test_the_analysis_returns_the_section_and_no_extra_file(self) -> None:
        import pc_evidence

        data = pc_evidence.load_stage_data(self.kept.run_root)
        title, lines, files = review().analyse_frozen_copy(spec_of(ROW12), data, {}, lambda text: text)
        self.assertEqual(title, "Frozen copy")
        self.assertEqual(files, {})
        self.assertEqual(lines, section_lines(self.kept))


if __name__ == "__main__":
    unittest.main()
