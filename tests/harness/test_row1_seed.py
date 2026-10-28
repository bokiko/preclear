"""Zero-token tests for the row 1 seed, the snapshots and the first stage (plan 03-02 Task 1).

HARN-05 (usage and cost per stage) and HARN-07 (the setup the isolation baseline is asserted on).
No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil.
Every folder comes from RowRig (a temporary repository, harness home and runs folder) or from
tempfile.mkdtemp and is never deleted. pc_row1 is imported inside each test, so a missing module is
one error per test and not one load failure of the file.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from decimal import Decimal

import pc_flags
import pc_manifest
import pc_spend
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
PUBLICATION = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20", "row1-wrong-binding")
PLAN_RELATIVE = "project/thoughts/plans/2026-10-15-widget-export.md"
LEDGER_A_NAME = "CONTINUITY_CLAUDE-widget-export.md"
LEDGER_B_NAME = "CONTINUITY_CLAUDE-other-task.md"
ROW1 = "row1-wrong-binding"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def row1():
    import pc_row1

    return pc_row1


def rows():
    import pc_rows

    return pc_rows


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path: str) -> str:
    return read_bytes(path).decode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_plan_digest() -> str:
    for line in read_text(os.path.join(PUBLICATION, "snap-0-setup", "sha.txt")).splitlines():
        digest, _sep, name = line.partition("  ")
        if name == PLAN_RELATIVE:
            return digest
    raise AssertionError("the committed setup digest list has no plan line")


def repo_digest(repo: str) -> str:
    entries = [e for e in pc_manifest.tree_manifest(repo) if not e["path"].startswith(b".git")]
    return sha(pc_manifest.sha_txt_bytes(entries))


def stub_output(rig, paths, session: str, verb: str) -> str:
    stub = os.path.join(rig.repo, "tests", "harness", "checkpoint_stub.py")
    args = [os.path.realpath(sys.executable), "-I", "-B", stub, verb]
    if verb == "status":
        args += ["--session", session]
    done = subprocess.run(
        args,
        env={"PATH": os.environ.get("PATH", ""), "CKPT_HOME": paths["ckpt"]},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=paths["project"],
    )
    return done.stdout.decode("utf-8")


class Seeded(object):
    """A rig, its context, a fresh run root and the seeded paths."""

    def __init__(self, rig=None, name="row1-seed-case") -> None:
        self.rig = rig if rig is not None else pc_testutil.RowRig()
        self.ctx = self.rig.context()
        self.run_root = self.rig.new_run_root(self.ctx, name)
        self.session = str(uuid.uuid4())
        self.paths = row1().seed_row1(
            self.rig.repo,
            self.run_root,
            self.session,
            self.ctx.harness_home,
            self.ctx.runs_root,
            self.ctx.evidence_date,
            self.ctx.model,
        )


class SeedTests(unittest.TestCase):
    def test_a_seed_creates_exactly_the_documented_layout(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        self.assertEqual(
            sorted(os.listdir(seeded.run_root)),
            ["auto-memory", "ckpt", "project", "raw", "settings.json", "snaps", "wrapper"],
        )
        project = p["project"]
        self.assertTrue(os.path.isfile(os.path.join(project, "CLAUDE.md")))
        self.assertTrue(os.path.isfile(os.path.join(project, "thoughts", "plans", "2026-10-15-widget-export.md")))
        branch = subprocess.run(
            ["git", "-C", project, "symbolic-ref", "--short", "HEAD"], stdout=subprocess.PIPE, check=True
        ).stdout.decode().strip()
        self.assertEqual(branch, "main")
        count = subprocess.run(
            ["git", "-C", project, "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE, check=True
        ).stdout.decode().strip()
        self.assertEqual(count, "1")
        skill_dir = os.path.join(project, ".claude", "skills", "preclear")
        self.assertEqual(read_bytes(os.path.join(skill_dir, "SKILL.md")), read_bytes(os.path.join(seeded.rig.repo, "SKILL.md")))
        references = sorted(os.listdir(os.path.join(seeded.rig.repo, "references")))
        self.assertEqual(sorted(os.listdir(os.path.join(skill_dir, "references"))), references)
        for name in references:
            self.assertEqual(
                read_bytes(os.path.join(skill_dir, "references", name)),
                read_bytes(os.path.join(seeded.rig.repo, "references", name)),
            )
        status = subprocess.run(
            ["git", "-C", project, "status", "--porcelain", "--untracked-files=all"], stdout=subprocess.PIPE, check=True
        ).stdout.decode()
        self.assertIn("?? .claude/skills/preclear/SKILL.md", status)
        wrapper_dir = p["wrapper_dir"]
        self.assertEqual(sorted(os.listdir(wrapper_dir)), ["calls.log", "checkpoint", "py", "stub"])
        self.assertEqual(stat.S_IMODE(os.stat(p["wrapper"]).st_mode), 0o755)
        names = [n for n in os.listdir(p["ledgers"]) if not n.startswith(".")]
        self.assertEqual(sorted(names), sorted([LEDGER_A_NAME, LEDGER_B_NAME]))
        self.assertEqual(len(os.listdir(os.path.join(p["ckpt"], "bindings"))), 1)
        self.assertTrue(os.path.isfile(os.path.join(p["ckpt"], "ledger-roots.json")))
        self.assertEqual(sorted(os.listdir(p["raw"])), ["lint-before.txt", "run.json", "status-before.txt"])
        self.assertEqual(os.listdir(p["snaps"]), [])
        self.assertEqual(os.listdir(p["auto_memory"]), [])

    def test_the_plan_digest_is_the_committed_one_and_the_configuration_is_filled(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        plan = read_bytes(os.path.join(p["project"], "thoughts", "plans", "2026-10-15-widget-export.md"))
        self.assertEqual(sha(plan), committed_plan_digest())
        self.assertIn(b"widget-export", plan)
        self.assertFalse(os.path.exists(os.path.join(p["project"], "thoughts", "ledgers")))
        config = read_text(os.path.join(p["project"], "CLAUDE.md"))
        self.assertIn("executable: " + p["wrapper"], config)
        self.assertIn("project: " + p["project"], config)
        self.assertIn("ledger: " + p["ledger_a"], config)
        self.assertEqual(os.path.dirname(p["ledger_a"]), p["ledgers"])
        self.assertEqual(os.path.basename(p["ledger_a"]), LEDGER_A_NAME)
        self.assertEqual(os.path.basename(p["ledger_b"]), LEDGER_B_NAME)
        self.assertIn("fallback_directory: " + os.path.join(p["project"], ".preclear"), config)
        self.assertIn("Resuming from this ledger requires no binding", config)
        self.assertNotIn("/path/to/", config)

    def test_the_ledgers_carry_the_real_project_path_and_the_stub_state_is_recorded(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        for ledger in (p["ledger_a"], p["ledger_b"]):
            text = read_text(ledger)
            self.assertIn(p["project"], text)
            self.assertNotIn("<repo>", text)
            self.assertNotIn("<run>", text)
        status = stub_output(seeded.rig, p, seeded.session, "status")
        self.assertIn("session " + seeded.session[:8], status)
        self.assertIn(p["ledger_b"], status)
        self.assertNotIn(p["ledger_a"], status)
        lint = stub_output(seeded.rig, p, seeded.session, "lint")
        self.assertIn("ledger lint OK", lint)
        self.assertEqual(read_text(os.path.join(p["raw"], "status-before.txt")), status)
        self.assertEqual(read_text(os.path.join(p["raw"], "lint-before.txt")), lint)
        self.assertEqual(os.path.getsize(os.path.join(p["wrapper_dir"], "calls.log")), 0)

    def test_a_second_seed_is_refused_the_repository_is_untouched_and_bad_arguments_are_refused(self) -> None:
        m = row1()
        rig = pc_testutil.RowRig()
        before = repo_digest(rig.repo)
        seeded = Seeded(rig)
        self.assertEqual(repo_digest(rig.repo), before)
        with self.assertRaises(FileExistsError):
            m.seed_row1(
                rig.repo, seeded.run_root, seeded.session, seeded.ctx.harness_home, seeded.ctx.runs_root,
                seeded.ctx.evidence_date, seeded.ctx.model,
            )
        self.assertEqual(repo_digest(rig.repo), before)
        fresh = rig.new_run_root(seeded.ctx, "row1-refusal-case")
        elsewhere = tempfile.mkdtemp(prefix="pc-outside-")
        inside = os.path.join(rig.repo, "tests", "evidence")
        for run_root in (elsewhere, inside):
            with self.assertRaises(ValueError):
                m.seed_row1(
                    rig.repo, run_root, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root,
                    seeded.ctx.evidence_date, seeded.ctx.model,
                )
        for bad in (str(uuid.uuid4()).upper(), "not-a-uuid", ""):
            with self.assertRaises(ValueError):
                m.seed_row1(
                    rig.repo, fresh, bad, seeded.ctx.harness_home, seeded.ctx.runs_root,
                    seeded.ctx.evidence_date, seeded.ctx.model,
                )
        self.assertEqual(os.listdir(fresh), [])

    def test_a_missing_source_names_only_the_repository_relative_file(self) -> None:
        import pc_spike

        rig = pc_testutil.RowRig()
        ctx = rig.context()
        missing = os.path.join(rig.repo, "tests", "harness", "pc_hooklog.py")
        os.rename(missing, missing + ".moved")
        run_root = rig.new_run_root(ctx, "row1-missing-case")
        with self.assertRaises(pc_spike.SpikeError) as caught:
            row1().seed_row1(
                rig.repo, run_root, str(uuid.uuid4()), ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model
            )
        self.assertIn("tests/harness/pc_hooklog.py", str(caught.exception))
        self.assertNotIn(rig.base, str(caught.exception))
        self.assertEqual(os.listdir(run_root), [])

    def test_settings_and_run_json_record_the_audit_hook_the_memory_folder_and_the_isolation_mode(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        settings = json.loads(read_text(p["settings"]))
        self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(p["auto_memory"]))
        command = settings["hooks"]["InstructionsLoaded"][0]["hooks"][0]["command"]
        self.assertIn(os.path.join(p["raw"], "hooklog.jsonl"), command)
        self.assertEqual(p["hooklog"], os.path.join(p["raw"], "hooklog.jsonl"))
        run = json.loads(read_text(os.path.join(p["raw"], "run.json")))
        self.assertEqual(run["row"], ROW1)
        self.assertEqual(run["model"], pc_flags.PINNED_MODEL)
        self.assertEqual(run["evidence_date"], "2026-10-28")
        self.assertEqual(run["session_id"], seeded.session)
        self.assertEqual(run["isolation"], "strict")

    def test_the_two_prompts_come_from_the_data_file_and_the_committed_file_read_in_place(self) -> None:
        seeded = Seeded()
        m = row1()
        s1, s2 = m.read_stage_prompts(seeded.rig.repo, seeded.paths["ledger_a"])
        data = read_text(os.path.join(ROOT, "tests", "harness", "data", "row1-s1-prompt.md"))
        self.assertIn("$LEDGER", data)
        self.assertEqual(s1, data.replace("$LEDGER", seeded.paths["ledger_a"]))
        self.assertTrue(s1.startswith("Implement only step 2"))
        self.assertTrue(s1.endswith("three lines.\n"))
        committed = read_bytes(os.path.join(PUBLICATION, "s2-preclear-prompt.md"))
        self.assertEqual(s2.encode("utf-8"), committed)
        self.assertEqual(sha(s2.encode("utf-8")), sha(committed))


class SnapshotTests(unittest.TestCase):
    def snapshot(self, seeded, name, **kwargs):
        git = shutil.which("git", path=os.pathsep.join(pc_testutil.SYSTEM_DIRS))
        return row1().take_snapshot(seeded.paths, name, git, **kwargs)

    def test_a_snapshot_holds_the_filtered_manifest_status_listings_and_copies(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        os.makedirs(os.path.join(p["project"], ".preclear", "widget-export"))
        with open(os.path.join(p["project"], ".preclear", "widget-export", "checkpoint.md"), "wb") as handle:
            handle.write(b"checkpoint body\n")
        with open(os.path.join(p["auto_memory"], "note.md"), "wb") as handle:
            handle.write(b"memory body\n")
        os.makedirs(os.path.join(seeded.run_root, "stage-extra"))
        skipped = self.snapshot(seeded, "snap-0-setup")
        self.assertEqual(list(skipped), [])
        snap = os.path.join(p["snaps"], "snap-0-setup")
        names = sorted(os.listdir(snap))
        for needed in ("sha.txt", "manifest.jsonl", "status.txt", "status.raw", "ledgers-ls.txt", "bindings-ls.txt",
                       LEDGER_A_NAME, LEDGER_B_NAME, "preclear", "auto-memory"):
            self.assertIn(needed, names)
        sha_lines = read_text(os.path.join(snap, "sha.txt")).splitlines()
        paths = [line.split("  ", 1)[1] for line in sha_lines]
        for path in paths:
            self.assertFalse(path.startswith("raw"), "raw entry listed")
            self.assertFalse(path.startswith("snaps"), "snaps entry listed")
            self.assertFalse(path.startswith("stage"), "stage entry listed")
            self.assertFalse(path.startswith("project/.git/"), ".git entry listed")
        self.assertIn(PLAN_RELATIVE, paths)
        calls = [line for line in sha_lines if line.endswith("  wrapper/calls.log")]
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith(EMPTY_SHA))
        self.assertEqual(read_text(os.path.join(snap, "preclear", "widget-export", "checkpoint.md")), "checkpoint body\n")
        self.assertEqual(read_text(os.path.join(snap, "auto-memory", "note.md")), "memory body\n")
        self.assertEqual(
            read_text(os.path.join(snap, "ledgers-ls.txt")).splitlines(), sorted([LEDGER_A_NAME, LEDGER_B_NAME])
        )
        bindings = read_text(os.path.join(snap, "bindings-ls.txt")).splitlines()
        self.assertEqual(bindings, [seeded.session + ".json"])
        self.assertIn("?? .claude/", read_text(os.path.join(snap, "status.txt")))
        self.assertIn(b"\x00", read_bytes(os.path.join(snap, "status.raw")))
        with open(os.path.join(snap, "manifest.jsonl"), "r", encoding="utf-8") as handle:
            kinds = set(json.loads(line)["kind"] for line in handle.read().splitlines())
        self.assertTrue(kinds <= set(["f", "d"]))

    def test_a_second_snapshot_of_the_same_name_is_refused(self) -> None:
        seeded = Seeded()
        self.snapshot(seeded, "snap-0-setup")
        with self.assertRaises(FileExistsError):
            self.snapshot(seeded, "snap-0-setup")

    def test_a_symlink_in_a_model_written_tree_skips_that_one_copy_only(self) -> None:
        seeded = Seeded()
        p = seeded.paths
        os.makedirs(os.path.join(p["project"], ".preclear"))
        os.symlink(seeded.run_root, os.path.join(p["project"], ".preclear", "link"))
        with open(os.path.join(p["auto_memory"], "note.md"), "wb") as handle:
            handle.write(b"memory body\n")
        skipped = self.snapshot(seeded, "snap-1-after-work")
        self.assertEqual(list(skipped), ["preclear"])
        snap = os.path.join(p["snaps"], "snap-1-after-work")
        self.assertFalse(os.path.exists(os.path.join(snap, "preclear")))
        self.assertEqual(read_text(os.path.join(snap, "auto-memory", "note.md")), "memory body\n")
        with open(os.path.join(snap, "manifest.jsonl"), "r", encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle.read().splitlines()]
        links = [e for e in entries if e["path"] == "project/.preclear/link"]
        self.assertEqual([e["kind"] for e in links], ["l"])


class TracerTests(unittest.TestCase):
    def test_stage_s1_runs_with_the_pinned_argv_a_ledger_reservation_a_record_and_a_snapshot(self) -> None:
        m = row1()
        seeded = Seeded()
        ctx, p, session = seeded.ctx, seeded.paths, seeded.session
        spec = rows().find_entry(rows().build_registry(), "row", ROW1).stages[0]
        prompt = m.read_stage_prompts(seeded.rig.repo, p["ledger_a"])[0]
        result = m.run_stage(ctx, p, spec, session, prompt, False, None, 120)
        self.assertTrue(result.ok, result.problem)
        calls = seeded.rig.calls()
        self.assertEqual(len(calls), 1)
        argv = calls[0]["args"]
        self.assertEqual(argv[argv.index("--session-id") + 1], session)
        self.assertEqual(argv[argv.index("--max-turns") + 1], "15")
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.30")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "default")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertIn("--verbose", argv)
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "project,local")
        self.assertEqual(argv[argv.index("--model") + 1], pc_flags.PINNED_MODEL)
        rules = argv[argv.index("--allowedTools") + 1].split(",")
        self.assertEqual(len(rules), 40)
        self.assertEqual(rules, list(pc_flags.build_allowed_tools(p["wrapper"], pc_flags.MODEL_FACING_WRAPPER_VERBS)))
        for absent in ("--resume", "--dangerously-skip-permissions", "--include-hook-events"):
            self.assertNotIn(absent, argv)
        self.assertEqual(os.path.realpath(calls[0]["cwd"]), os.path.realpath(p["project"]))
        self.assertEqual(calls[0]["env"]["CLAUDE_CONFIG_DIR"], ctx.config_dir)
        self.assertEqual(calls[0]["env"]["CKPT_HOME"], p["ckpt"])
        self.assertEqual(calls[0]["env"]["DISABLE_AUTOUPDATER"], "1")
        inherited = [n for n in calls[0]["names"] if n.startswith(("ANTHROPIC", "CLAUDE_CODE", "CLAUDECODE"))]
        self.assertEqual(inherited, ["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"])
        self.assertEqual(calls[0]["prompt"], prompt)
        self.assertIn(p["ledger_a"], prompt)
        self.assertNotIn("$LEDGER", prompt)
        for stem in ("s1.stdout", "s1.stderr"):
            self.assertTrue(os.path.isfile(os.path.join(p["raw"], stem)), stem)
        records = pc_spend.read_records(ctx.harness_home)
        self.assertEqual([r["kind"] for r in records], ["launch", "settle"])
        self.assertEqual(records[0]["stage"], "row1-s1")
        self.assertEqual(records[0]["cap"], Decimal("0.30"))
        self.assertEqual(records[1]["delta"], Decimal("0.03"))
        self.assertEqual(records[1]["cumulative"], Decimal("0.03"))
        self.assertEqual(records[1]["subtype"], "success")
        record = json.loads(read_text(os.path.join(p["raw"], "s1.record.json")))
        self.assertEqual(record["session_id"], session)
        self.assertEqual(record["returncode"], 0)
        self.assertIs(record["timed_out"], False)
        self.assertEqual(record["attempt"], 1)
        self.assertEqual(record["wrapper_calls"], 0)
        self.assertEqual(record["hooklog_lines"], 1)
        self.assertEqual(record["snapshot"], "snap-1-after-work")
        self.assertIn("wall_seconds", record)
        self.assertEqual(record["delta"], "0.03")
        self.assertEqual(record["cumulative"], "0.03")
        self.assertEqual(
            sorted(record["usage"]),
            ["cache_creation_input_tokens", "cache_read_input_tokens", "input_tokens", "output_tokens"],
        )
        snap = os.path.join(p["snaps"], "snap-1-after-work")
        self.assertIn("  project/widget_export.py", read_text(os.path.join(snap, "sha.txt")))

    def test_a_stage_is_reserved_before_its_process_and_never_started_twice(self) -> None:
        m = row1()
        seeded = Seeded()
        ctx, p = seeded.ctx, seeded.paths
        spec = rows().find_entry(rows().build_registry(), "row", ROW1).stages[0]
        m.run_stage(ctx, p, spec, seeded.session, "prompt", False, None, 120)
        with self.assertRaises(pc_spend.SpendRefused):
            m.run_stage(ctx, p, spec, seeded.session, "prompt", False, None, 120)
        self.assertEqual(len(seeded.rig.calls()), 1)


class SharedHelperTests(unittest.TestCase):
    def test_the_sibling_helpers_this_plan_reuses_still_exist(self) -> None:
        import pc_spike

        for name in (
            "run_claude", "_run_git", "_fill_configuration", "_copy_tree_with", "s1_evaluation",
            "hit_candidates", "binary_defines", "local_user_names", "runs_root", "ensure_config_dir",
        ):
            self.assertTrue(callable(getattr(pc_spike, name, None)), "a shared pc_spike helper is missing")
        for name in ("tree_manifest", "write_snapshot", "capture_git_status"):
            self.assertTrue(callable(getattr(pc_manifest, name, None)), "a shared pc_manifest helper is missing")


if __name__ == "__main__":
    unittest.main()
