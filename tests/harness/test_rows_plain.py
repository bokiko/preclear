"""Zero-token tests for the plain rows 5a and 5b (plan 04-04; RERUN-02; D-04, D-12).

A plain row has no helper: no wrapper, no stub, no ledger, no binding. Its allowlist is the 33-rule baseline plus two
extra rules, its settings switch Claude Code's auto-memory off (the directory stays pinned inside the run root), and the
init assertion about the memory path follows the row's memory policy. These tests prove the seed is byte-tied to the
committed rows, the allowlist, the settings and the assertion behave as stated, and a scripted chain of each row runs
through the same engine as every other row and is filed. No test starts a real claude: the only claude executed is the
scripted fake written by pc_testutil. Folders come from RowRig and are never deleted. Modules are imported inside small
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
import pc_flags
import pc_testutil
from test_row_generic import Registered, tree_names

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW5A = "row5a-no-memory"
ROW5B = "row5b-disabled-memory"
PLAIN_ROWS = (ROW5A, ROW5B)
PUBLICATION = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")
DATA = os.path.join(ROOT, "tests", "harness", "data")
PLAN_DIGEST = "a4d70690252f755ea6b44d3c3362b345d5126962bb5b4bb40e99ed14a11adf0c"
CLAUDE_MD_DIGEST_PREFIX = {ROW5A: "de73808e", ROW5B: "ad08b998"}
VERDICT_LINE = "Reviewer verdict: PENDING"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
SHAPED = re.compile(r"(^|[\s(`\"'=])(/[A-Za-z0-9_.-]+/|~/|[A-Za-z]:\\)|@[A-Za-z0-9-]+\.[A-Za-z]|://")
EXTRA_RULES = ["Bash(chmod:*)", "Bash(touch:*)"]


def rows():
    import pc_rows

    return pc_rows


def row1():
    import pc_row1

    return pc_row1


def rowseeds():
    import pc_rowseeds

    return pc_rowseeds


def evidence():
    import pc_evidence

    return pc_evidence


def matrix():
    import pc_matrix

    return pc_matrix


def spec_of(row_id: str):
    pc_rows = rows()
    entry = pc_rows.find_entry(pc_rows.build_registry(), pc_rows.KIND_ROW, row_id)
    assert entry is not None, row_id
    return entry


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path: str) -> str:
    return read_bytes(path).decode("utf-8")


def read_json(path: str):
    return json.loads(read_text(path))


def committed(row_id: str, *parts: str) -> str:
    return os.path.join(PUBLICATION, row_id, *parts)


def sha_lines(row_id: str) -> dict:
    """The committed setup digests of a row: relative file name to sha256."""
    found = {}
    for line in read_text(committed(row_id, "snap-0-setup", "sha.txt")).splitlines():
        digest, _, name = line.partition("  ")
        found[name] = digest
    return found


def plain_stages(spec, memory_write: bool = False, init_override=None) -> list:
    """The scripted stages of a clean plain run: pc_testutil's scripts for a row with no helper.

    The /preclear script keeps the listing, the checkpoint file and its Write call, and has no wrapper call and no
    memory file (a plain row has no wrapper). memory_write adds one memory file inside the pinned auto-memory
    folder; init_override is an init override applied to every stage.
    """
    stages = pc_testutil.default_row_stages(spec)
    for stage in stages:
        assert "$WRAPPER" not in json.dumps(stage), "a plain script holds no wrapper op"
    if memory_write:
        stages[1]["ops"] = list(stages[1]["ops"]) + [{"op": "write", "path": "$AUTOMEM/note.md", "text": "a note\n"}]
    if init_override is not None:
        for stage in stages:
            stage["init"] = dict(stage.get("init", {}), **init_override)
    return stages


def run_plain(row_id: str = ROW5A, **options) -> Registered:
    return Registered(row_id, stages=plain_stages(spec_of(row_id), **options))


class SeededPlain(object):
    """A rig, a fresh run root and the paths a plain seed returns."""

    def __init__(self, row_id: str, name: str = "plain-seed-case") -> None:
        self.row_id = row_id
        self.rig = pc_testutil.RowRig(stages=plain_stages(spec_of(row_id)))
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

    def commit_count(self) -> int:
        env = pc_testutil.git_env({"PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS)})
        done = subprocess.run(
            ["git", "-C", self.paths["project"], "rev-list", "--count", "HEAD"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return int(done.stdout.decode("utf-8").strip())

    def tracked(self) -> list:
        env = pc_testutil.git_env({"PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS)})
        done = subprocess.run(
            ["git", "-C", self.paths["project"], "ls-files"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return sorted(done.stdout.decode("utf-8").split())


def tokenised_settings(seeded: SeededPlain) -> dict:
    """The seeded settings without the audit hook and with the run-root path replaced by the committed token."""
    settings = read_json(seeded.paths["settings"])
    settings.pop("hooks", None)
    text = json.dumps(settings, sort_keys=True).replace(os.path.realpath(seeded.run_root), "<repo>/<run>")
    return json.loads(text)


class DataFileTests(unittest.TestCase):
    def test_the_plain_plan_is_the_seven_committed_lines_and_hashes_to_the_committed_digest(self) -> None:
        data = read_bytes(os.path.join(DATA, "plain-plan.md"))
        self.assertEqual(hashlib.sha256(data).hexdigest(), PLAN_DIGEST)
        lines = data.decode("utf-8").split("\n")
        self.assertEqual(lines[-1], "", "every line ends in a newline")
        self.assertEqual(len(lines) - 1, 7)
        self.assertEqual(lines[0], "# Plan: widget-export")
        self.assertEqual(lines[1], "")
        self.assertEqual(lines[2][:6], "1. [x]")
        self.assertEqual(lines[3][:6], "2. [ ]")
        self.assertEqual(lines[4][:6], "3. [ ]")
        self.assertEqual(lines[5], "")
        self.assertTrue(lines[6].startswith("Decision 2026-10-15: CSV first"))

    def test_the_plan_digest_is_the_one_both_committed_rows_hold(self) -> None:
        for row_id in PLAIN_ROWS:
            digests = sha_lines(row_id)
            self.assertEqual(digests["project/thoughts/plans/2026-10-15-widget-export.md"], PLAN_DIGEST)

    def test_the_plain_prompt_is_the_row_1_prompt_with_the_ledger_clause_replaced(self) -> None:
        source = read_bytes(os.path.join(DATA, "row1-s1-prompt.md")).decode("utf-8")
        clause = "using the CSV decision in the project's continuity ledger at $LEDGER"
        self.assertEqual(source.count(clause), 1)
        derived = source.replace(clause, "following the CSV decision recorded in that plan")
        built = read_bytes(os.path.join(DATA, "plain-s1-prompt.md"))
        self.assertEqual(built, derived.encode("utf-8"))
        self.assertNotIn(b"$LEDGER", built)
        self.assertNotIn(b"ledger", built.lower())

    def test_the_data_files_and_every_setup_text_hold_no_path_shaped_string(self) -> None:
        for name in ("plain-plan.md", "plain-s1-prompt.md"):
            text = read_text(os.path.join(DATA, name))
            self.assertIsNone(SHAPED.search(text), name + " holds a path-shaped string")
            self.assertTrue(text.isascii())
        for row_id in PLAIN_ROWS:
            text = spec_of(row_id).setup_text
            self.assertTrue(text.startswith("Setup: "))
            self.assertIsNone(SHAPED.search(text), "a setup text holds a path-shaped string")
            self.assertTrue(text.isascii())


class RegistryTests(unittest.TestCase):
    def test_5a_and_5b_both_rows_are_registered_with_the_two_committed_stages_and_the_plain_policy(self) -> None:
        pc_rows = rows()
        for row_id in PLAIN_ROWS:
            spec = spec_of(row_id)
            self.assertTrue(spec.implemented)
            self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2"])
            self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60])
            self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30"])
            self.assertEqual([stage.session for stage in spec.stages], ["new:A", "resume:A"])
            self.assertEqual(pc_rows.session_count(spec), 1)
            self.assertEqual(spec.tools_profile, pc_rows.PROFILE_PLAIN)
            self.assertEqual(list(spec.extra_tools), EXTRA_RULES)
            self.assertEqual(spec.memory, pc_rows.MEMORY_DISABLED)
            self.assertEqual([name for name, _path in spec.prompts], ["s1", "s2"])
            self.assertEqual(dict(spec.prompts)["s1"], "tests/harness/data/plain-s1-prompt.md")
            self.assertEqual(dict(spec.prompts)["s2"].rsplit("/", 1)[0].rsplit("/", 1)[1], row_id)
            sources = [relative for relative, _kind in spec.sources]
            self.assertIn("tests/harness/data/plain-plan.md", sources)
            self.assertIn("tests/harness/data/plain-s1-prompt.md", sources)
            self.assertFalse([name for name in sources if "wrapper" in name or "stub" in name], "no helper source")
            for relative, kind in spec.sources:
                full = os.path.join(ROOT, *relative.split("/"))
                self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), "a source is missing")

    def test_the_new_fields_are_defaulted_so_old_constructions_still_work(self) -> None:
        pc_rows = rows()
        built = pc_rows.RowSpec("row0-x", "row", "x", (), False, None, None, ())
        self.assertEqual(built.extra_tools, ())
        self.assertEqual(built.memory, pc_rows.MEMORY_PINNED)
        for row_id in (pc_rows.ROW1, pc_rows.ROW4A):
            self.assertEqual(spec_of(row_id).memory, pc_rows.MEMORY_PINNED)
            self.assertEqual(spec_of(row_id).extra_tools, ())
            self.assertEqual(spec_of(row_id).tools_profile, pc_rows.PROFILE_HELPER)

    def test_the_profile_words_of_the_registry_and_of_the_flag_module_agree(self) -> None:
        pc_rows = rows()
        self.assertEqual(pc_rows.PROFILE_HELPER, pc_flags.PROFILE_HELPER)
        self.assertEqual(pc_rows.PROFILE_PLAIN, pc_flags.PROFILE_PLAIN)

    def test_5a_and_5b_list_marks_both_rows_implemented_with_two_stages_and_one_session(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        for row_id in PLAIN_ROWS:
            self.assertEqual(cells[row_id][2:], ["2", "1", "yes"])

    def dry_run(self, row_id: str):
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-plain-"))
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

    def test_5a_and_5b_the_dry_run_of_each_row_prints_the_plan_and_starts_no_process(self) -> None:
        for row_id in PLAIN_ROWS:
            code, text, tripwire, base = self.dry_run(row_id)
            self.assertEqual(code, 0, text)
            self.assertIn("%s: 2 stages, 1 sessions" % row_id, text)
            lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2"))]
            self.assertEqual(len(lines), 2)
            self.assertIn("15 turns", lines[0])
            self.assertIn("cap 0.30", lines[0])
            self.assertIn("60 turns", lines[1])
            self.assertIn("cap 1.30", lines[1])
            # The caps sum to 1.60: the plan reads the sum of the caps, as for row 4a (plan 04-01, deviation 1).
            self.assertIn("worst case 1.60 USD", text)
            self.assertIn("allowlist 35 rules", text)
            self.assertEqual(tripwire, [])
            self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")


class PlainSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = {ROW5A: SeededPlain(ROW5A, "plain-seed-5a"), ROW5B: SeededPlain(ROW5B, "plain-seed-5b")}

    def test_5a_and_5b_the_seeded_claude_md_equals_the_committed_fixture_and_its_setup_digest(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            data = read_bytes(os.path.join(seeded.paths["project"], "CLAUDE.md"))
            self.assertEqual(data, read_bytes(committed(row_id, "fixture-CLAUDE.md")), "byte for byte")
            digest = hashlib.sha256(data).hexdigest()
            self.assertEqual(digest, sha_lines(row_id)["project/CLAUDE.md"])
            self.assertTrue(digest.startswith(CLAUDE_MD_DIGEST_PREFIX[row_id]))

    def test_the_two_rows_hold_different_project_files_and_5b_says_memory_is_disabled(self) -> None:
        a = read_text(os.path.join(self.seeded[ROW5A].paths["project"], "CLAUDE.md"))
        b = read_text(os.path.join(self.seeded[ROW5B].paths["project"], "CLAUDE.md"))
        self.assertNotEqual(a, b)
        self.assertNotIn("emory", a, "5a mentions no memory anywhere")
        self.assertIn("Memory is disabled for this project.", b)

    def test_5a_and_5b_the_plan_equals_the_plain_data_file_and_hashes_to_the_committed_digest(self) -> None:
        for row_id in PLAIN_ROWS:
            plan = os.path.join(self.seeded[row_id].paths["project"], "thoughts", "plans", "2026-10-15-widget-export.md")
            data = read_bytes(plan)
            self.assertEqual(data, read_bytes(os.path.join(DATA, "plain-plan.md")))
            self.assertEqual(hashlib.sha256(data).hexdigest(), PLAN_DIGEST)

    def test_5a_and_5b_the_project_is_a_repository_on_main_with_one_commit_and_the_skill_untracked(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            self.assertEqual(seeded.commit_count(), 1)
            self.assertEqual(seeded.tracked(), ["CLAUDE.md", "thoughts/plans/2026-10-15-widget-export.md"])
            head = read_text(os.path.join(seeded.paths["project"], ".git", "HEAD")).strip()
            self.assertEqual(head, "ref: refs/heads/main")
            skill = os.path.join(seeded.paths["skill_dir"], "SKILL.md")
            self.assertEqual(read_bytes(skill), read_bytes(os.path.join(ROOT, "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(seeded.paths["skill_dir"], "references", "configuration.md")))

    def test_5a_and_5b_the_run_root_holds_an_empty_ledgers_folder_and_no_wrapper_ledger_or_binding(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            paths = seeded.paths
            self.assertEqual(sorted(os.listdir(paths["ckpt"])), ["ledgers"])
            self.assertEqual(os.listdir(paths["ledgers"]), [])
            self.assertFalse(os.path.lexists(os.path.join(seeded.run_root, "wrapper")), "no wrapper folder")
            self.assertFalse(os.path.lexists(os.path.join(paths["ckpt"], "bindings")), "no binding")
            everything = [name for _dir, _dirs, files in os.walk(seeded.run_root) for name in files]
            self.assertEqual([name for name in everything if name.startswith("CONTINUITY_CLAUDE-")], [])
            self.assertEqual(sorted(os.listdir(seeded.run_root)), sorted(
                ["auto-memory", "ckpt", "project", "raw", "settings.json", "snaps"]
            ))
            self.assertEqual(os.listdir(paths["auto_memory"]), [])
            self.assertEqual(sorted(os.listdir(paths["raw"])), ["run.json"])

    def test_5a_and_5b_the_returned_paths_are_the_ones_paths_for_rebuilds_and_the_helper_paths_do_not_exist(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            rebuilt = row1().paths_for(seeded.run_root)
            self.assertEqual(sorted(seeded.paths), sorted(rebuilt))
            self.assertEqual(dict((k, seeded.paths[k]) for k in rebuilt), dict(rebuilt))
            for key in ("wrapper_dir", "wrapper", "ledger_a", "ledger_b"):
                self.assertFalse(os.path.lexists(seeded.paths[key]), key + " must name nothing")

    def test_5a_and_5b_the_run_record_names_the_row_the_memory_policy_and_no_bound_ledger(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            record = read_json(os.path.join(seeded.paths["raw"], "run.json"))
            self.assertEqual(
                sorted(record),
                ["bound_ledger", "evidence_date", "isolation", "memory", "model", "row", "session_id"],
            )
            self.assertEqual(record["row"], row_id)
            self.assertEqual(record["bound_ledger"], "none")
            self.assertEqual(record["memory"], "disabled")
            self.assertEqual(record["session_id"], seeded.session)

    def test_5a_and_5b_the_settings_switch_memory_off_keep_the_directory_pinned_and_equal_the_committed_file(self) -> None:
        for row_id in PLAIN_ROWS:
            seeded = self.seeded[row_id]
            settings = read_json(seeded.paths["settings"])
            self.assertIs(settings["autoMemoryEnabled"], False)
            self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(seeded.paths["auto_memory"]))
            self.assertIn("InstructionsLoaded", settings["hooks"], "the audit hook stays")
            self.assertEqual(tokenised_settings(seeded), read_json(committed(row_id, "settings.json")))

    def test_the_5b_seed_is_the_committed_5b_file_and_its_digest_is_not_the_5a_digest(self) -> None:
        seeded = self.seeded[ROW5B]
        data = read_bytes(os.path.join(seeded.paths["project"], "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW5B, "fixture-CLAUDE.md")))
        digest = hashlib.sha256(data).hexdigest()
        self.assertTrue(digest.startswith("ad08b998"))
        self.assertEqual(digest, sha_lines(ROW5B)["project/CLAUDE.md"])
        self.assertNotEqual(digest, sha_lines(ROW5A)["project/CLAUDE.md"])
        self.assertEqual(read_json(seeded.paths["raw"] + "/run.json")["row"], ROW5B)
        self.assertEqual(read_json(self.seeded[ROW5A].paths["raw"] + "/run.json")["row"], ROW5A)

    def test_the_5b_seed_differs_from_the_5a_seed_in_exactly_the_project_instruction_file(self) -> None:
        a, b = self.seeded[ROW5A], self.seeded[ROW5B]

        def listing(seeded: SeededPlain) -> dict:
            found = {}
            for dirpath, dirnames, filenames in os.walk(seeded.run_root):
                dirnames[:] = [name for name in dirnames if name != ".git"]
                for name in filenames:
                    full = os.path.join(dirpath, name)
                    found[os.path.relpath(full, seeded.run_root)] = read_bytes(full)
            return found

        first, second = listing(a), listing(b)
        self.assertEqual(sorted(first), sorted(second), "the same files")
        differing = sorted(name for name in first if first[name] != second[name])
        skipped = {os.path.join("raw", "run.json"), "settings.json", os.path.join("raw", "hooklog.jsonl")}
        self.assertEqual([name for name in differing if name not in skipped], [os.path.join("project", "CLAUDE.md")])
        run_a, run_b = read_json(a.paths["raw"] + "/run.json"), read_json(b.paths["raw"] + "/run.json")
        for key in ("row", "session_id"):
            run_a.pop(key)
            run_b.pop(key)
        self.assertEqual(run_a, run_b, "the run records differ in the row and the session only")
        self.assertEqual(tokenised_settings(a), tokenised_settings(b))

    def test_5a_and_5b_a_second_seed_of_the_same_run_root_is_refused(self) -> None:
        seeded = self.seeded[ROW5A]
        with self.assertRaises(FileExistsError):
            rowseeds().seed_row5a(
                seeded.rig.repo,
                seeded.run_root,
                seeded.session,
                seeded.ctx.harness_home,
                seeded.ctx.runs_root,
                seeded.ctx.evidence_date,
                seeded.ctx.model,
            )

    def test_5a_and_5b_a_seed_refuses_an_odd_session_id_a_run_root_in_the_repository_and_a_missing_source(self) -> None:
        import pc_spike

        seeded = self.seeded[ROW5A]
        rig = seeded.rig
        fresh = rig.new_run_root(seeded.ctx, "plain-seed-odd")
        args = (rig.repo, fresh, "not-a-uuid", seeded.ctx.harness_home, seeded.ctx.runs_root, "2026-10-28", "m")
        with self.assertRaises(ValueError):
            rowseeds().seed_row5a(*args)
        upper = str(uuid.uuid4()).upper()
        with self.assertRaises(ValueError):
            rowseeds().seed_row5a(rig.repo, fresh, upper, seeded.ctx.harness_home, seeded.ctx.runs_root, "d", "m")
        with self.assertRaises(ValueError):
            rowseeds().seed_row5a(
                rig.repo, rig.repo, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root, "d", "m"
            )
        with self.assertRaises(ValueError):
            rowseeds().seed_plain_row(
                rig.repo, fresh, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root, "d", "m",
                ROW5A, "tests/evidence/publication-2026-10-20/row5a-no-memory/fixture-CLAUDE.md", "unknown-policy",
            )
        with self.assertRaises(pc_spike.SpikeError):
            rowseeds().seed_plain_row(
                rig.repo, fresh, str(uuid.uuid4()), seeded.ctx.harness_home, seeded.ctx.runs_root, "d", "m",
                ROW5A, "tests/evidence/publication-2026-10-20/row5a-no-memory/no-such-file.md", "disabled",
            )
        self.assertEqual(os.listdir(fresh), [], "nothing was created for a refused seed")


class PlainToolsTests(unittest.TestCase):
    WRAPPER = "/synthetic/wrapper/checkpoint"

    def test_the_plain_allowlist_is_the_baseline_plus_the_two_extras_and_no_wrapper_rule(self) -> None:
        rules = pc_flags.build_row_tools("plain", self.WRAPPER, EXTRA_RULES)
        self.assertEqual(len(rules), 35)
        self.assertEqual(list(rules[:33]), list(pc_flags.BASELINE_ALLOWED_TOOLS))
        self.assertEqual(list(rules[33:]), EXTRA_RULES)
        for rule in rules:
            self.assertNotIn("checkpoint", rule)
            self.assertNotIn("/", rule, "no path and so no bare executable prefix")
            for verb in pc_flags.DRIVER_ONLY_VERBS:
                self.assertNotIn(" %s" % verb, rule)
        self.assertEqual(pc_flags.build_row_tools("plain", "any text at all", ()), pc_flags.BASELINE_ALLOWED_TOOLS)
        self.assertEqual(pc_flags.build_row_tools("git", self.WRAPPER, ()), pc_flags.BASELINE_ALLOWED_TOOLS)

    def test_the_helper_profile_is_unchanged_and_takes_extras_after_the_wrapper_rules(self) -> None:
        plain_helper = pc_flags.build_row_tools("helper", self.WRAPPER, ())
        self.assertEqual(
            plain_helper, pc_flags.build_allowed_tools(self.WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        )
        self.assertEqual(len(plain_helper), 40)
        self.assertEqual(pc_flags.build_row_tools("helper", self.WRAPPER, ["Bash(touch:*)"])[-1], "Bash(touch:*)")

    def test_an_unknown_profile_and_a_malformed_or_repeated_extra_are_refused(self) -> None:
        for bad_profile in ("", "Plain", "wrapper", None, 5):
            with self.assertRaises(ValueError):
                pc_flags.build_row_tools(bad_profile, self.WRAPPER, ())
        for bad in ("Bash(a,b)", "", "Bash(x/y:*)", "Bash(a\nb)", " Bash(touch:*)", 7, None, "Bash(touch:*) "):
            with self.assertRaises(ValueError, msg=repr(bad)):
                pc_flags.build_row_tools("plain", self.WRAPPER, [bad])
        with self.assertRaises(ValueError):
            pc_flags.build_row_tools("plain", self.WRAPPER, ["Bash(touch:*)", "Bash(touch:*)"])
        with self.assertRaises(ValueError):
            pc_flags.build_row_tools("plain", self.WRAPPER, ["Read"])
        with self.assertRaises(ValueError):
            pc_flags.build_row_tools("plain", self.WRAPPER, "Bash(touch:*)")

    def test_the_row_engine_builds_the_list_from_the_entry(self) -> None:
        for row_id in PLAIN_ROWS:
            spec = spec_of(row_id)
            rules = row1().allowed_tools(spec.tools_profile, "/nowhere/checkpoint", spec.extra_tools)
            self.assertEqual(len(rules), 35)
            self.assertEqual(list(rules), list(pc_flags.BASELINE_ALLOWED_TOOLS) + EXTRA_RULES)
        pc_rows = rows()
        for row_id in (pc_rows.ROW1, pc_rows.ROW4A):
            spec = spec_of(row_id)
            self.assertEqual(len(row1().allowed_tools(spec.tools_profile, "/nowhere/checkpoint", spec.extra_tools)), 40)
        with self.assertRaises(ValueError):
            row1().allowed_tools("no-such-profile", "/nowhere/checkpoint")

    def test_the_settings_keep_memory_on_unless_told_otherwise(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pc-plain-set-") as folder:
            on = pc_flags.render_settings(folder)
            self.assertIs(on["autoMemoryEnabled"], True)
            self.assertEqual(on, pc_flags.render_settings(folder, None, True))
            off = pc_flags.render_settings(folder, None, memory_enabled=False)
            self.assertIs(off["autoMemoryEnabled"], False)
            self.assertEqual(off["autoMemoryDirectory"], on["autoMemoryDirectory"], "the directory stays pinned")
            self.assertEqual(sorted(off), sorted(on))
            hooked = pc_flags.render_settings(folder, "audit-command", False)
            self.assertIn("hooks", hooked)
            for bad in ("no", 0, 1, None):
                with self.assertRaises(ValueError):
                    pc_flags.render_settings(folder, None, bad)


class MemoryAssertionTests(unittest.TestCase):
    PINNED = "/synthetic/run/auto-memory"

    def ok(self, init: dict, enabled: bool) -> bool:
        return row1()._memory_path_ok(init, self.PINNED, enabled)

    def test_disabled_and_no_path_reported_passes(self) -> None:
        self.assertTrue(self.ok({}, False))
        self.assertTrue(self.ok({"memory_paths": None}, False))
        self.assertTrue(self.ok({"memory_paths": {}}, False))
        self.assertTrue(self.ok({"memory_paths": {"auto": None}}, False))

    def test_disabled_and_the_pinned_path_reported_passes_with_or_without_a_trailing_separator(self) -> None:
        self.assertTrue(self.ok({"memory_paths": {"auto": self.PINNED}}, False))
        self.assertTrue(self.ok({"memory_paths": {"auto": self.PINNED + "/"}}, False))

    def test_disabled_and_any_other_path_or_shape_fails(self) -> None:
        for auto in ("/synthetic/elsewhere/memory", self.PINNED + "-sibling", "relative/memory", "", "/", 5, ["x"]):
            self.assertFalse(self.ok({"memory_paths": {"auto": auto}}, False), repr(auto))
        for shape in ("text", 5, ["auto"], True):
            self.assertFalse(self.ok({"memory_paths": shape}, False), repr(shape))

    def test_pinned_and_no_path_reported_still_fails_as_in_phase_3(self) -> None:
        self.assertFalse(self.ok({}, True))
        self.assertFalse(self.ok({"memory_paths": None}, True))
        self.assertFalse(self.ok({"memory_paths": {}}, True))
        self.assertFalse(self.ok({"memory_paths": {"auto": None}}, True))
        self.assertFalse(row1()._memory_path_ok({}, self.PINNED), "the default is the pinned policy")
        self.assertTrue(self.ok({"memory_paths": {"auto": self.PINNED}}, True))
        self.assertFalse(self.ok({"memory_paths": {"auto": "/synthetic/elsewhere/memory"}}, True))

    def test_the_assertion_ids_and_their_order_are_unchanged(self) -> None:
        ids = row1().ROW_ASSERTION_IDS
        self.assertEqual(len(ids), 12)
        self.assertEqual(list(ids[9:]), ["memory-path-as-set", "cwd-is-project", "session-id-as-requested"])


class PlainChainTests(unittest.TestCase):
    """A scripted chain of each plain row through the same engine as every other row."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runs = {}
        for row_id in PLAIN_ROWS:
            run = run_plain(row_id)
            assert run.outcome.code == 0, "\n".join(run.outcome.lines)
            cls.runs[row_id] = run

    def read(self, row_id: str, name: str) -> str:
        return read_text(os.path.join(self.runs[row_id].row_dir, name))

    def test_5a_and_5b_a_scripted_chain_completes_with_two_launches_and_no_wrapper_folder(self) -> None:
        for row_id in PLAIN_ROWS:
            run = self.runs[row_id]
            self.assertEqual(len(run.rig.calls()), 2, "each stage is launched exactly once")
            self.assertFalse(os.path.lexists(os.path.join(run.run_root, "wrapper")), "no wrapper folder")
            self.assertEqual(
                [(r["kind"], r["stage"]) for r in run.ledger()],
                [("launch", "row5a-s1"), ("settle", "row5a-s1"), ("launch", "row5a-s2"), ("settle", "row5a-s2")]
                if row_id == ROW5A
                else [("launch", "row5b-s1"), ("settle", "row5b-s1"), ("launch", "row5b-s2"), ("settle", "row5b-s2")],
            )
            self.assertEqual(os.listdir(run.ctx.destination), [row_id])

    def test_5a_and_5b_the_stage_commands_carry_35_rules_the_disabled_settings_and_the_plain_prompts(self) -> None:
        for row_id in PLAIN_ROWS:
            run = self.runs[row_id]
            first, second = run.rig.calls()
            for call in (first, second):
                argv = call["args"]
                rules = argv[argv.index("--allowedTools") + 1].split(",")
                self.assertEqual(rules, list(pc_flags.BASELINE_ALLOWED_TOOLS) + EXTRA_RULES)
                self.assertEqual(call["env"]["CKPT_HOME"], os.path.join(run.run_root, "ckpt"))
            self.assertEqual(first["prompt"].encode("utf-8"), read_bytes(os.path.join(DATA, "plain-s1-prompt.md")))
            self.assertEqual(
                second["prompt"].encode("utf-8"), read_bytes(committed(row_id, "s2-preclear-prompt.md"))
            )
            settings_path = first["args"][first["args"].index("--settings") + 1]
            self.assertEqual(settings_path, os.path.join(run.run_root, "settings.json"))
            self.assertIs(read_json(settings_path)["autoMemoryEnabled"], False)

    def test_5a_and_5b_the_filed_folder_holds_the_committed_file_names_and_no_helper_file(self) -> None:
        for row_id in PLAIN_ROWS:
            names = tree_names(self.runs[row_id].row_dir)
            for expected in (
                "README.md", "claude-version.txt", "digests.txt", "fixture-CLAUDE.md", "measurements.md",
                "s1-work.out", "s1.err", "s1.exit", "s2-preclear-full-trace.md", "s2-preclear-prompt.md",
                "s2-preclear-trace.md", "s2-preclear.err", "s2-preclear.exit", "session.id", "settings.json",
                "snap-0-setup/", "snap-1-after-work/", "snap-2-after-preclear/", "tools.txt", "usage.txt",
                "mechanical-checks.md",
            ):
                self.assertIn(expected, names, expected)
            for absent in (
                "wrapper-calls.log", "wrapper-checkpoint.sh", "status-before.txt", "lint-before.txt",
                "s3-resume.exit", "snap-3-after-resume/", "session-resume.id",
            ):
                self.assertNotIn(absent, names, absent)

    def test_5a_and_5b_the_filed_project_file_equals_the_committed_one_and_the_settings_show_the_committed_switch(self) -> None:
        for row_id in PLAIN_ROWS:
            self.assertEqual(
                self.read(row_id, "fixture-CLAUDE.md"), read_text(committed(row_id, "fixture-CLAUDE.md"))
            )
            filed = read_json(os.path.join(self.runs[row_id].row_dir, "settings.json"))
            original = read_json(committed(row_id, "settings.json"))
            self.assertEqual(sorted(filed), sorted(original), "the same two keys")
            self.assertIs(filed["autoMemoryEnabled"], original["autoMemoryEnabled"])
            self.assertIs(filed["autoMemoryEnabled"], False)
            # The filing tokenises the run path as the Phase 3 baseline does (the committed 2026-10-20 file wrote its own token).
            self.assertEqual(filed["autoMemoryDirectory"], "<auto-memory-root>")

    def test_5a_and_5b_the_filed_tools_file_is_the_35_comma_joined_rules_with_no_wrapper_path(self) -> None:
        for row_id in PLAIN_ROWS:
            text = self.read(row_id, "tools.txt")
            self.assertEqual(text, ",".join(list(pc_flags.BASELINE_ALLOWED_TOOLS) + EXTRA_RULES) + "\n")
            self.assertNotIn("checkpoint", text)
            self.assertNotIn(self.runs[row_id].run_root, text)
            self.assertEqual(len(text.strip().split(",")), 35)

    def test_5a_and_5b_digests_list_the_skill_and_reference_files_only(self) -> None:
        for row_id in PLAIN_ROWS:
            lines = self.read(row_id, "digests.txt").splitlines()
            references = sorted(os.listdir(os.path.join(ROOT, "references")))
            self.assertEqual(len(lines), 1 + len(references))
            self.assertTrue(lines[0].endswith("/.claude/skills/preclear/SKILL.md"))
            for line, name in zip(lines[1:], references):
                self.assertTrue(line.endswith("/.claude/skills/preclear/references/" + name), line)
            text = "\n".join(lines)
            for word in ("wrapper", "stub", "UNCONFIRMED", "checkpoint_stub"):
                self.assertNotIn(word, text)
            self.assertIn(hashlib.sha256(read_bytes(os.path.join(ROOT, "SKILL.md"))).hexdigest(), lines[0])

    def test_5a_and_5b_the_mechanical_checks_hold_zero_helper_calls_absent_ledgers_and_unconfirmed_status_questions(self) -> None:
        for row_id in PLAIN_ROWS:
            text = self.read(row_id, "mechanical-checks.md")
            for stage in ("s1", "s2"):
                for key in ("attempted", "executed", "denied", "compound-refusals"):
                    self.assertIn("%s %s: 0" % (stage, key), text)
            for name in ("ledger-a", "ledger-b", "binding", "ledger-roots", "checkpoint-log"):
                self.assertIn("%s: absent-both" % name, text)
            self.assertIn("ledgers-unchanged: yes", text)
            for key in ("status-begins-with-session", "status-holds-s1-prefix", "status-names-ledger-b"):
                self.assertIn("%s: UNCONFIRMED" % key, text)
            self.assertIn("memory-path-as-set: yes", text)

    def test_5a_and_5b_the_memory_facts_are_counts_and_names_only(self) -> None:
        for row_id in PLAIN_ROWS:
            text = self.read(row_id, "mechanical-checks.md")
            for line in (
                "memory-setting: disabled",
                "auto-memory-files: 0",
                "project-memory-paths: 0",
                "default-memory-root: absent",
                "default-memory-folder: absent",
            ):
                self.assertIn(line, text.splitlines())

    def test_5a_and_5b_the_assertion_lines_come_in_the_order_of_the_assertion_ids(self) -> None:
        ids = list(row1().ROW_ASSERTION_IDS)
        for row_id in PLAIN_ROWS:
            lines = self.read(row_id, "mechanical-checks.md").splitlines()
            found = [line.split()[1].rstrip(":") for line in lines if line.startswith("s2 ") and line.split()[1].rstrip(":") in ids]
            self.assertEqual(found, ids)

    def test_5b_chain_is_filed_as_its_own_folder_with_its_own_project_file_and_setup_paragraph(self) -> None:
        run = self.runs[ROW5B]
        self.assertEqual(os.path.basename(run.row_dir), ROW5B)
        self.assertEqual(self.read(ROW5B, "fixture-CLAUDE.md"), read_text(committed(ROW5B, "fixture-CLAUDE.md")))
        self.assertNotEqual(self.read(ROW5B, "fixture-CLAUDE.md"), self.read(ROW5A, "fixture-CLAUDE.md"))
        readme = self.read(ROW5B, "README.md")
        self.assertEqual(readme.splitlines()[0].split(",")[0], "# Row 5b: memory explicitly disabled (1P)")
        self.assertIn("memory is disabled for this project", readme)
        self.assertNotIn("memory is disabled for this project", self.read(ROW5A, "README.md"))
        first = run.rig.calls()[0]
        self.assertEqual(first["args"][first["args"].index("--allowedTools") + 1].count(","), 34)

    def test_5a_and_5b_each_readme_ends_with_the_pending_line_holds_no_verdict_word_and_no_path(self) -> None:
        pattern = evidence().verdict_pattern()
        for row_id in PLAIN_ROWS:
            text = self.read(row_id, "README.md")
            self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"))
            self.assertEqual(text.count(VERDICT_LINE), 1)
            body = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(body), "no verdict word in the README")
            self.assertIn(spec_of(row_id).setup_text, body, "the Setup paragraph is the registry text")
            self.assertIsNone(SHAPED.search(body))
            self.assertNotIn(self.runs[row_id].rig.base, body)
            self.assertIn("helper calls in s1: attempted 0", body)

    def test_5a_and_5b_no_harness_authored_file_of_a_plain_row_holds_a_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        for row_id in PLAIN_ROWS:
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

    def test_5a_and_5b_the_setup_snapshot_lists_no_wrapper_and_no_ledger(self) -> None:
        for row_id in PLAIN_ROWS:
            listing = self.read(row_id, "snap-0-setup/sha.txt")
            self.assertNotIn("wrapper", listing)
            self.assertNotIn("CONTINUITY", listing)
            self.assertEqual(self.read(row_id, "snap-0-setup/ledgers-ls.txt"), "")
            self.assertEqual(self.read(row_id, "snap-0-setup/bindings-ls.txt"), "")
            self.assertIn("project/CLAUDE.md", listing)

    def test_5a_and_5b_the_row_runs_a_memory_file_inside_the_pinned_folder_without_a_breach_and_counts_it(self) -> None:
        run = run_plain(ROW5A, memory_write=True)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        text = read_text(os.path.join(run.row_dir, "mechanical-checks.md"))
        self.assertIn("auto-memory-files: 1", text.splitlines())
        self.assertIn("default-memory-root: absent", text.splitlines())

    def test_5a_and_5b_a_chain_whose_init_reports_no_memory_path_is_filed_for_a_disabled_row(self) -> None:
        for row_id in PLAIN_ROWS:
            run = run_plain(row_id, init_override={"memory_paths": "$DELETE"})
            self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
            self.assertIn("s1 memory-path-as-set: yes", read_text(os.path.join(run.row_dir, "mechanical-checks.md")))

    def test_5a_and_5b_a_chain_whose_init_reports_another_memory_path_stops_with_11_and_is_labelled(self) -> None:
        run = run_plain(ROW5A, init_override={"memory_paths": {"auto": "$OUTSIDE/"}})
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW5A])
        self.assertTrue(any("memory-path-as-set" in line for line in run.outcome.lines))
        self.assertEqual(len(run.rig.calls()), 1, "the chain ends at the stage that failed")

    def test_5a_and_5b_a_pinned_row_still_stops_when_init_reports_no_memory_path(self) -> None:
        pc_rows = rows()
        spec = spec_of(pc_rows.ROW4A)
        stages = pc_testutil.default_row_stages(spec)
        for stage in stages:
            stage["init"] = {"memory_paths": "$DELETE"}
        run = Registered(pc_rows.ROW4A, stages=stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertTrue(any("memory-path-as-set" in line for line in run.outcome.lines))

    def test_5a_and_5b_a_scripted_write_to_the_default_memory_root_ends_the_row_with_11_and_files_a_label(self) -> None:
        rig = pc_testutil.RowRig(stages=plain_stages(spec_of(ROW5A)))
        ctx = rig.context()
        import pc_checks

        run_name = "%s-%s" % (ROW5A, FIXED_DATE.strftime("%Y%m%dT%H%M%SZ"))
        project = os.path.join(ctx.runs_root, run_name, "project")
        folder = pc_checks.default_memory_path(ctx.config_dir, project)
        stages = plain_stages(spec_of(ROW5A))
        stages[1]["ops"] = list(stages[1]["ops"]) + [{"op": "write", "path": folder + "/stray.md", "text": "x\n"}]
        rig.configure(stages=stages)
        with mock.patch.object(row1(), "_utc_now", return_value=FIXED_DATE):
            run = Registered(ROW5A, rig=rig)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertTrue(any("writes outside approved roots" in line for line in run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), ["STOPPED-" + ROW5A])
        self.assertTrue(os.path.isdir(folder), "the stray folder is the scripted write")


if __name__ == "__main__":
    unittest.main()
