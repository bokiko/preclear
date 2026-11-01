"""Zero-token tests for the row-generic engine (plan 04-01; RERUN-02, RERUN-03; D-03, D-04).

A row is defined by its registry entry alone. Row 4a (unknown backend) is the first row that runs that way: its
stage loop, its session keys, its prompts, its allowlist profile and its setup paragraph come from the RowSpec, and
it is filed as its own row folder inside a dated folder. No test starts a real claude: the only claude executed is
the scripted fake written by pc_testutil. Every folder comes from RowRig and is never deleted. Modules are imported
inside small accessors, so a missing module is one error per test and not one load failure of the file. Messages
that name a path are never asserted on by value; leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import subprocess
import sys
import unittest
import uuid
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_flags
import pc_spend
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW1 = "row1-wrong-binding"
ROW4A = "row4a-unknown-backend"
PUBLICATION = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")
BASELINE = os.path.join(ROOT, "tests", "evidence", "rerun-2026-10-29-claude-sonnet-5-5")
VERDICT_LINE = "Reviewer verdict: PENDING"
DEST_NAME = "rerun-2026-10-28-claude-sonnet-5-5"
FIXED_DATE = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
CONFIG_KEYS = ("executable", "project", "ledger", "fallback_directory")


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


def tree_names(root: str) -> list:
    """The sorted names under root, relative, forward slashes, folders listed with a trailing slash."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames:
            found.append(os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/") + "/")
        for name in filenames:
            found.append(os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/"))
    return sorted(found)


class Registered(object):
    """A rig, a context and the outcome of one run_registered_row call."""

    def __init__(self, row_id: str = ROW4A, stages=None, rig=None, **config) -> None:
        self.row_id = row_id
        self.spec = spec_of(row_id)
        if rig is None:
            scripted = stages if stages is not None else pc_testutil.default_row_stages(self.spec)
            rig = pc_testutil.RowRig(stages=scripted, **config)
        self.rig = rig
        self.ctx = rig.context()
        self.outcome = row1().run_registered_row(self.ctx, row_id)

    @property
    def run_root(self) -> str:
        names = sorted(os.listdir(self.ctx.runs_root))
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    @property
    def row_dir(self) -> str:
        return os.path.join(self.ctx.destination, self.row_id)

    def raw(self, name: str) -> str:
        return os.path.join(self.run_root, "raw", name)

    def ledger(self):
        return pc_spend.read_records(self.ctx.harness_home)


def with_result_text(stages, index, text):
    updated = pc_testutil.stages_with(stages, index)
    updated[index]["result"] = dict(updated[index].get("result", {}), text=text)
    return updated


class RegisteredRowTests(unittest.TestCase):
    def test_row_4a_is_registered_with_its_two_committed_stages_and_one_session(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW4A)
        self.assertTrue(spec.implemented)
        self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2"])
        self.assertEqual([stage.kind for stage in spec.stages], ["work", "preclear"])
        self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60])
        self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30"])
        self.assertEqual([stage.timeout for stage in spec.stages], [900, 1800])
        self.assertEqual([stage.session for stage in spec.stages], ["new:A", "resume:A"])
        self.assertEqual(pc_rows.session_count(spec), 1)
        self.assertEqual(pc_rows.worst_case(spec), Decimal("1.60"))
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_HELPER)
        self.assertIsNotNone(spec.seed)
        self.assertEqual([name for name, _path in spec.prompts], ["s1", "s2"])
        self.assertTrue(spec.setup_text.startswith("Setup: "), "the harness-authored Setup paragraph")
        for relative, kind in spec.sources:
            full = os.path.join(ROOT, *relative.split("/"))
            self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), "a source is missing")

    def test_the_four_new_fields_are_defaulted_so_old_constructions_still_work(self) -> None:
        pc_rows = rows()
        built = pc_rows.RowSpec("row0-x", "row", "x", (), False, None, None, ())
        self.assertIsNone(built.seed)
        self.assertEqual(built.prompts, ())
        self.assertEqual(built.setup_text, "")
        self.assertEqual(built.tools_profile, pc_rows.PROFILE_HELPER)

    def test_the_registry_is_importable_without_the_row_engine(self) -> None:
        code = (
            "import sys; sys.path.insert(0, %r); import pc_rows; pc_rows.build_registry(); "
            "sys.exit(1 if 'pc_row1' in sys.modules else 0)" % HARNESS_DIR
        )
        done = subprocess.run([sys.executable, "-E", "-s", "-B", "-c", code], stdin=subprocess.DEVNULL)
        self.assertEqual(done.returncode, 0, "importing pc_rows pulled in pc_row1")

    def test_every_runner_of_a_registered_row_is_lazy_and_names_run_registered_row(self) -> None:
        spec = spec_of(ROW4A)
        self.assertTrue(callable(spec.runner), "a registered row runner is a lazy callable")
        marker = object()
        with mock.patch.object(row1(), "run_registered_row", return_value=marker) as fake:
            self.assertIs(spec.runner("ctx"), marker)
        fake.assert_called_once_with("ctx", ROW4A, None)

    def test_the_dry_run_plan_reads_two_stages_one_session_and_starts_no_process(self) -> None:
        import tempfile

        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-generic-"))
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
            code = matrix().main(
                ["--dry-run", "--row", ROW4A], env=env, clock=lambda: FIXED_DATE, out=out, err=err
            )
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        text = out.getvalue()
        self.assertIn("%s: 2 stages, 1 sessions" % ROW4A, text)
        lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2"))]
        self.assertEqual(len(lines), 2)
        self.assertIn("15 turns", lines[0])
        self.assertIn("cap 0.30", lines[0])
        self.assertIn("new session", lines[0])
        self.assertIn("60 turns", lines[1])
        self.assertIn("cap 1.30", lines[1])
        self.assertIn("resumes the s1 session", lines[1])
        self.assertIn("worst case 1.60 USD", text)
        self.assertEqual(pc_testutil.read_tripwire(bin_dir), [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")

    def test_list_marks_row_4a_implemented_and_row_1_keeps_three_stages_and_two_sessions(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        self.assertEqual(len(lines), 22)
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        self.assertEqual(cells[ROW4A][2:], ["2", "1", "yes"])
        self.assertEqual(cells[ROW1][2:], ["3", "2", "yes"])

    def test_a_scripted_chain_runs_s1_new_and_s2_resumed_with_the_pinned_forms(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        calls = run.rig.calls()
        self.assertEqual(len(calls), 2, "each stage is launched exactly once and no third stage exists")
        first, second = [call["args"] for call in calls]
        session = read_json(run.raw("run.json"))["session_id"]
        self.assertEqual(first[first.index("--session-id") + 1], session)
        self.assertNotIn("--resume", first)
        self.assertEqual(first[first.index("--max-turns") + 1], "15")
        self.assertEqual(first[first.index("--max-budget-usd") + 1], "0.30")
        self.assertEqual(second[second.index("--resume") + 1], session)
        self.assertNotIn("--session-id", second)
        self.assertEqual(second[second.index("--max-turns") + 1], "60")
        self.assertEqual(second[second.index("--max-budget-usd") + 1], "1.30")
        for argv in (first, second):
            self.assertEqual(len(argv[argv.index("--allowedTools") + 1].split(",")), 40)
            self.assertEqual(argv[argv.index("--model") + 1], pc_flags.PINNED_MODEL)
        self.assertEqual(
            [(r["kind"], r["stage"]) for r in run.ledger()],
            [("launch", "row4a-s1"), ("settle", "row4a-s1"), ("launch", "row4a-s2"), ("settle", "row4a-s2")],
        )
        self.assertEqual(
            sorted(os.listdir(os.path.join(run.run_root, "snaps"))),
            ["snap-0-setup", "snap-1-after-work", "snap-2-after-preclear"],
        )

    def test_the_s1_prompt_names_ledger_a_and_the_s2_prompt_is_the_committed_row_4a_file(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        first, second = [call["prompt"] for call in run.rig.calls()]
        ledger_a = os.path.join(run.run_root, "ckpt", "ledgers", "CONTINUITY_CLAUDE-widget-export.md")
        data = read_text(os.path.join(ROOT, "tests", "harness", "data", "row1-s1-prompt.md"))
        self.assertEqual(first, data.replace("$LEDGER", ledger_a))
        committed = read_bytes(os.path.join(PUBLICATION, ROW4A, "s2-preclear-prompt.md"))
        self.assertEqual(second.encode("utf-8"), committed)

    def test_the_chain_ends_after_s2_whether_or_not_a_resume_line_was_printed(self) -> None:
        with_line = Registered()
        self.assertEqual(with_line.outcome.code, 0, "\n".join(with_line.outcome.lines))
        self.assertEqual(read_json(with_line.raw("chain.json"))["marker"], row1().MARKER_FOUND)
        self.assertEqual(len(with_line.rig.calls()), 2)
        spec = spec_of(ROW4A)
        stages = with_result_text(pc_testutil.default_row_stages(spec), 1, "Checkpoint written. Nothing to resume.")
        without = Registered(stages=stages)
        self.assertEqual(without.outcome.code, 0, "\n".join(without.outcome.lines))
        self.assertEqual(read_json(without.raw("chain.json"))["marker"], row1().MARKER_NONE)
        self.assertEqual(len(without.rig.calls()), 2)

    def test_the_stage_three_line_is_printed_only_for_a_spec_with_a_resume_stage(self) -> None:
        for stages in (None, with_result_text(pc_testutil.default_row_stages(spec_of(ROW4A)), 1, "No line.")):
            run = Registered(stages=stages)
            self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
            joined = "\n".join(run.outcome.lines)
            self.assertNotIn("stage s3", joined, "a two-stage spec prints no stage s3 line")
            self.assertNotIn(row1().MARKER_NONE, joined)
        self.assertTrue(any(line.startswith("stage s2: ") for line in run.outcome.lines))

    def test_an_unknown_or_odd_id_raises_before_anything_is_created(self) -> None:
        import pc_spike

        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW4A)))
        ctx = rig.context()
        odd = (
            "row4a",
            "row4a-unknown-backen",
            "row4a-unknown-backend-",
            "ROW4A-UNKNOWN-BACKEND",
            "row4a-unknown-backend ",
            "row4a-unknown-backend/../x",
            "../row4a-unknown-backend",
            "",
            None,
            5,
            "row2-double-conflict",
            "plain-memory",
        )
        for value in odd:
            with self.assertRaises(pc_spike.SpikeError, msg="an id that is not an implemented registry id"):
                row1().run_registered_row(ctx, value)
        self.assertEqual(os.listdir(ctx.runs_root), [], "no run root was made")
        self.assertFalse(os.path.exists(ctx.destination), "no evidence folder was made")
        self.assertFalse(os.path.exists(os.path.join(ctx.harness_home, "matrix-spend.jsonl")))
        self.assertEqual(rig.calls(), [])

    def test_an_existing_row_folder_is_refused_with_17_before_anything_is_created(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW4A)))
        ctx = rig.context()
        os.makedirs(os.path.join(ctx.destination, ROW4A))
        outcome = row1().run_registered_row(ctx, ROW4A)
        self.assertEqual(outcome.code, pc_exitcodes.PROMOTE_REFUSED, "\n".join(outcome.lines))
        self.assertEqual(os.listdir(ctx.runs_root), [], "no run root was made")
        self.assertEqual(rig.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(ctx.harness_home, "matrix-spend.jsonl")))
        self.assertEqual(os.listdir(os.path.join(ctx.destination, ROW4A)), [], "the folder is untouched")

    def test_a_dated_folder_that_exists_is_not_a_refusal(self) -> None:
        rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW4A)))
        ctx = rig.context()
        os.makedirs(ctx.destination)
        run = Registered(rig=rig)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertTrue(os.path.isdir(run.row_dir))

    def test_a_scripted_write_outside_the_run_root_ends_with_11_and_files_nothing(self) -> None:
        stages = pc_testutil.seed_outside_write(pc_testutil.default_row_stages(spec_of(ROW4A)), 1)
        run = Registered(stages=stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertFalse(os.path.exists(run.ctx.destination), "nothing was filed")
        self.assertTrue(any("writes outside approved roots" in line for line in run.outcome.lines))

    def test_every_setup_text_is_free_of_path_shaped_strings(self) -> None:
        shaped = re.compile(
            r"(^|[\s(`\"'=])(/[A-Za-z0-9_.-]+/|~/|[A-Za-z]:\\)|@[A-Za-z0-9-]+\.[A-Za-z]|://"
        )
        seen = 0
        for entry in rows().build_registry():
            if entry.setup_text:
                seen += 1
                self.assertIsNone(shaped.search(entry.setup_text), "a setup text holds a path-shaped string")
                self.assertTrue(entry.setup_text.isascii(), "a setup text is plain ASCII")
        self.assertGreaterEqual(seen, 1)

    def test_no_row_source_file_added_by_this_plan_uses_a_deletion_primitive(self) -> None:
        import test_runroot

        for name in ("pc_rowseeds.py", "pc_rows.py", "pc_row1.py", "pc_evidence.py"):
            findings = test_runroot.scan_source(read_bytes(os.path.join(HARNESS_DIR, name)))
            self.assertEqual(findings, [], "%s: %s" % (name, "; ".join(sorted(set(findings)))))
        self.assertNotIn("pc_rowseeds.py", test_runroot.SCAN_EXEMPT, "the new seed module is scanned like the rest")
        self.assertIn("pc_rowseeds.py", test_runroot.harness_modules())


class Seeded(object):
    """A rig, a fresh run root and the paths a seed of row 4a returns."""

    def __init__(self, name: str = "row4a-seed-case") -> None:
        self.rig = pc_testutil.RowRig(stages=pc_testutil.default_row_stages(spec_of(ROW4A)))
        self.ctx = self.rig.context()
        self.run_root = self.rig.new_run_root(self.ctx, name)
        self.session = str(uuid.uuid4())
        self.paths = rowseeds().seed_row4a(
            self.rig.repo,
            self.run_root,
            self.session,
            self.ctx.harness_home,
            self.ctx.runs_root,
            self.ctx.evidence_date,
            self.ctx.model,
        )


class SeedByteTieTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seeded = Seeded()

    def test_the_seeded_claude_md_differs_from_the_committed_fixture_only_in_the_four_values(self) -> None:
        committed = read_text(os.path.join(PUBLICATION, ROW4A, "fixture-CLAUDE.md")).split("\n")
        seeded = read_text(os.path.join(self.seeded.paths["project"], "CLAUDE.md")).split("\n")
        self.assertEqual(len(committed), len(seeded), "same number of lines")
        differing = []
        for before, after in zip(committed, seeded):
            if before != after:
                key_before = before.split(":", 1)[0].strip()
                key_after = after.split(":", 1)[0].strip()
                self.assertEqual(key_before, key_after, "a changed line keeps its key")
                differing.append(key_before)
        self.assertEqual(sorted(differing), sorted(["project", "ledger", "fallback_directory"]))
        for key in differing:
            self.assertIn(key, CONFIG_KEYS)

    def test_the_unknown_backend_and_the_relative_executable_are_kept_verbatim(self) -> None:
        text = read_text(os.path.join(self.seeded.paths["project"], "CLAUDE.md"))
        self.assertIn("\n  backend: checkpoint-v2\n", text)
        self.assertIn("\n  executable: wrapper/checkpoint\n", text)
        self.assertNotIn("<repo>", text)
        self.assertNotIn("<run>", text)

    def test_the_configured_paths_name_the_run_root_and_the_one_ledger(self) -> None:
        paths = self.seeded.paths
        text = read_text(os.path.join(paths["project"], "CLAUDE.md"))
        self.assertIn("\n  project: %s\n" % paths["project"], text)
        self.assertIn("\n  ledger: %s\n" % paths["ledger_a"], text)
        self.assertIn("\n  fallback_directory: %s\n" % os.path.join(paths["project"], ".preclear"), text)

    def test_the_run_root_holds_one_ledger_and_the_session_is_bound_to_it(self) -> None:
        paths = self.seeded.paths
        listed = sorted(name for name in os.listdir(paths["ledgers"]) if not name.startswith("."))
        self.assertEqual(listed, ["CONTINUITY_CLAUDE-widget-export.md"])
        self.assertTrue(os.path.isfile(paths["ledger_a"]))
        self.assertFalse(os.path.lexists(paths["ledger_b"]), "no second ledger is made")
        bindings = os.path.join(paths["ckpt"], "bindings")
        names = sorted(os.listdir(bindings))
        self.assertEqual(len(names), 1, "one binding")
        self.assertIn(self.seeded.session, names[0])
        self.assertIn("CONTINUITY_CLAUDE-widget-export.md", read_text(os.path.join(bindings, names[0])))
        everything = [name for _dir, _dirs, files in os.walk(self.seeded.run_root) for name in files]
        self.assertEqual(
            sum(1 for name in everything if name.startswith("CONTINUITY_CLAUDE-")), 1, "one ledger file in the run root"
        )

    def test_the_ledger_is_the_committed_row_4a_copy_with_the_real_project_path(self) -> None:
        paths = self.seeded.paths
        committed = read_text(
            os.path.join(PUBLICATION, ROW4A, "snap-0-setup", "CONTINUITY_CLAUDE-widget-export.md")
        )
        seeded = read_text(paths["ledger_a"])
        self.assertEqual(seeded, committed.replace("<repo>/<run>/project", paths["project"]))

    def test_the_run_record_names_the_row_and_the_bound_ledger(self) -> None:
        record = read_json(os.path.join(self.seeded.paths["raw"], "run.json"))
        self.assertEqual(record["row"], ROW4A)
        self.assertEqual(record["bound_ledger"], "A")
        self.assertEqual(record["session_id"], self.seeded.session)

    def test_the_seed_returns_the_same_path_keys_as_row_1(self) -> None:
        other = Seeded("row4a-seed-keys")
        keys = sorted(other.paths)
        rebuilt = row1().paths_for(other.run_root)
        self.assertEqual(keys, sorted(rebuilt))
        self.assertEqual(dict((k, other.paths[k]) for k in keys), dict((k, rebuilt[k]) for k in keys))

    def test_a_second_seed_of_the_same_run_root_is_refused(self) -> None:
        seeded = self.seeded
        with self.assertRaises(FileExistsError):
            rowseeds().seed_row4a(
                seeded.rig.repo,
                seeded.run_root,
                seeded.session,
                seeded.ctx.harness_home,
                seeded.ctx.runs_root,
                seeded.ctx.evidence_date,
                seeded.ctx.model,
            )


class FilingTests(unittest.TestCase):
    def test_a_filed_row_holds_the_stage_files_named_by_the_spec_and_nothing_at_the_top(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertEqual(os.listdir(run.ctx.destination), [ROW4A], "the dated folder holds only the row folder")
        names = tree_names(run.row_dir)
        for expected in (
            "README.md",
            "s1.exit",
            "s1.err",
            "s1-work.out",
            "s1-work-prompt.md",
            "s1-work-full-trace.md",
            "session.id",
            "s2-preclear.exit",
            "s2-preclear.err",
            "s2-preclear-prompt.md",
            "s2-preclear-trace.md",
            "s2-preclear-full-trace.md",
            "usage.txt",
            "tools.txt",
            "mechanical-checks.md",
            "snap-0-setup/",
            "snap-1-after-work/",
            "snap-2-after-preclear/",
            "resume-line.txt",
        ):
            self.assertIn(expected, names, "the row folder holds " + expected)
        for absent in ("s3-resume.exit", "s3-resume-trace.md", "session-resume.id", "snap-3-after-resume/"):
            self.assertNotIn(absent, names, "a two-stage spec files no stage three")
        self.assertEqual(os.listdir(os.path.join(run.run_root, "stage-1")), [ROW4A], "the staged tree is the row folder")

    def test_the_row_readme_has_the_setup_paragraph_of_the_entry_and_ends_with_the_verdict_line(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        data = read_bytes(os.path.join(run.row_dir, "README.md"))
        self.assertTrue(data.endswith(("\n" + VERDICT_LINE + "\n").encode("utf-8")))
        self.assertEqual(data.count(VERDICT_LINE.encode("utf-8")), 1, "the line occurs once")
        text = data.decode("utf-8")
        self.assertIn(spec_of(ROW4A).setup_text, text, "the Setup paragraph comes from the registry entry")
        self.assertIn("Row 4a", text.splitlines()[0], "the heading names the row")

    def test_the_tools_file_is_built_from_the_profile_of_the_entry(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        rules = read_text(os.path.join(run.row_dir, "tools.txt")).strip().split(",")
        self.assertEqual(len(rules), 40)

    def test_the_filed_line_names_the_dated_folder_and_the_row_folder(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        filed = [line for line in run.outcome.lines if line.startswith("filed: ")]
        self.assertEqual(len(filed), 1)
        self.assertIn(DEST_NAME, filed[0])
        self.assertIn(ROW4A, filed[0])
        self.assertNotIn(run.rig.base, filed[0])

    def test_a_second_filing_of_the_same_row_into_the_same_dated_folder_is_refused_with_17(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        before = evidence_tree(run.row_dir)
        again = evidence().file_row(
            run.ctx._replace(run_root=run.run_root, sanitizer=_sanitizer_of(run), deny_entries=_deny_of(run)),
            run.run_root,
            spec=spec_of(ROW4A),
        )
        self.assertEqual(again.code, pc_exitcodes.PROMOTE_REFUSED, "\n".join(again.lines))
        self.assertEqual(evidence_tree(run.row_dir), before, "the filed row is untouched")

    def test_two_different_rows_file_into_one_dated_folder(self) -> None:
        pc_rows = rows()
        stages = pc_testutil.default_row1_stages() + pc_testutil.default_row_stages(spec_of(ROW4A))
        rig = pc_testutil.RowRig(stages=stages)
        ctx = rig.context()
        refusal = pc_rows.RowOutcome(pc_exitcodes.PROMOTE_REFUSED, ("refused by the test stand-in",))
        with mock.patch.object(evidence(), "file_row", return_value=refusal):
            row1().run_row(ctx)
        self.assertFalse(os.path.exists(ctx.destination), "row 1 was run and not filed")
        first = Registered(rig=rig)
        self.assertEqual(first.outcome.code, 0, "\n".join(first.outcome.lines))
        runs = sorted(os.path.join(ctx.runs_root, name) for name in os.listdir(ctx.runs_root))
        self.assertEqual(len(runs), 2)
        second_root = [path for path in runs if os.path.basename(path).startswith("row1-")][0]
        sanitizer = _sanitizer_of_root(rig, second_root, ctx)
        second = evidence().file_row(
            ctx._replace(run_root=second_root, sanitizer=sanitizer, deny_entries=sanitizer.deny_entries()),
            second_root,
            spec=spec_of(ROW1),
        )
        self.assertEqual(second.code, 0, "\n".join(second.lines))
        self.assertEqual(sorted(os.listdir(ctx.destination)), [ROW1, ROW4A])
        self.assertEqual(first.ctx.destination, ctx.destination)

    def test_nothing_is_deleted_or_overwritten_when_a_row_is_refused(self) -> None:
        run = Registered()
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        before = evidence_tree(run.ctx.destination)
        outcome = row1().run_registered_row(run.ctx, ROW4A)
        self.assertEqual(outcome.code, pc_exitcodes.PROMOTE_REFUSED)
        self.assertEqual(evidence_tree(run.ctx.destination), before)


def verdict_pattern():
    """The words no harness-authored file may hold, assembled from fragments at run time."""
    words = (
        "pa" + "ss", "pa" + "ssed", "fa" + "il", "fa" + "iled", "fail" + "ure", "acc" + "ept", "acc" + "epted",
        "ver" + "dict",
    )
    return re.compile(r"\b(?:%s)\b" % "|".join(words), re.IGNORECASE)


def parity_stages():
    """The default row 1 scripts without the auto-memory write: the committed baseline filed no memory file."""
    stages = pc_testutil.default_row_stages(spec_of(ROW1))
    stages[1]["ops"] = [op for op in stages[1]["ops"] if "$AUTOMEM" not in json.dumps(op)]
    return stages


class VocabularyTests(unittest.TestCase):
    def authored(self, run: Registered) -> list:
        names = []
        for dirpath, _dirnames, filenames in os.walk(run.ctx.destination):
            for name in filenames:
                names.append(os.path.relpath(os.path.join(dirpath, name), run.ctx.destination).replace(os.sep, "/"))
        return evidence().harness_authored_names(sorted(names))

    def test_no_harness_authored_file_of_a_registered_row_holds_a_verdict_word(self) -> None:
        pattern = verdict_pattern()
        for row_id in (ROW4A, ROW1):
            run = Registered(row_id)
            self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
            names = self.authored(run)
            self.assertIn(row_id + "/README.md", names, "the row README is scanned")
            self.assertIn(row_id + "/usage.txt", names, "a provenance file is scanned")
            self.assertGreater(len(names), 8, "the scan covers many files")
            count = 0
            for name in names:
                text = read_text(os.path.join(run.ctx.destination, name))
                count += text.count(VERDICT_LINE)
                if name == row_id + "/README.md":
                    self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"), "the line closes the row README")
                    text = text[: -len(VERDICT_LINE) - 1]
                self.assertIsNone(pattern.search(text), "no verdict word in " + name)
            self.assertEqual(count, 1, "the closing line occurs once in " + row_id)

    def test_the_authored_names_cover_any_registered_row_id(self) -> None:
        names = []
        ids = [entry.row_id for entry in rows().build_registry()]
        for row_id in ids:
            names.append(row_id + "/README.md")
            names.append(row_id + "/snap-0-setup/ledgers-ls.txt")
            names.append(row_id + "/s1-work.out")
        names.append("not-a-registered-row/README.md")
        picked = evidence().harness_authored_names(names)
        for row_id in ids:
            self.assertIn(row_id + "/README.md", picked)
            self.assertIn(row_id + "/snap-0-setup/ledgers-ls.txt", picked)
            self.assertNotIn(row_id + "/s1-work.out", picked, "a model reply is outside the scan")
        self.assertNotIn("not-a-registered-row/README.md", picked)


class Row1ParityTests(unittest.TestCase):
    def test_the_registry_entry_of_row_1_carries_what_the_engine_reads(self) -> None:
        spec = spec_of(ROW1)
        self.assertEqual([name for name, _path in spec.prompts], ["s1", "s2"])
        self.assertIsNotNone(spec.seed)
        self.assertTrue(callable(spec.runner), "row 1 has the lazy runner too")
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        self.assertEqual(spec.tools_profile, rows().PROFILE_HELPER)

    def test_run_row_is_a_thin_wrapper_over_the_registered_chain_of_row_1(self) -> None:
        marker = object()
        with mock.patch.object(row1(), "run_registered_row", return_value=marker) as fake:
            self.assertIs(row1().run_row("ctx", 5), marker)
        fake.assert_called_once_with("ctx", ROW1, 5)

    def test_the_filed_names_equal_the_committed_baseline_names_none_added_none_missing(self) -> None:
        run = Registered(ROW1, stages=parity_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        filed = set(tree_names(run.row_dir))
        committed = set(tree_names(os.path.join(BASELINE, ROW1)))
        self.assertGreater(len(committed), 30, "the baseline row folder was read")
        self.assertEqual(
            (sorted(filed - committed), sorted(committed - filed)),
            ([], []),
            "names added by the filing, then names missing from it",
        )
        self.assertEqual(os.listdir(run.ctx.destination), [ROW1], "only the row folder is filed")

    def test_a_row_1_chain_with_no_resume_line_prints_the_stage_three_line_and_files_two_stages(self) -> None:
        stages = with_result_text(pc_testutil.default_row_stages(spec_of(ROW1)), 1, "Nothing to resume.")
        run = Registered(ROW1, stages=stages)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertIn("stage s3: not run (%s)" % row1().MARKER_NONE, run.outcome.lines)
        self.assertEqual(len(run.rig.calls()), 2)
        names = tree_names(run.row_dir)
        self.assertNotIn("s3-resume.exit", names)
        self.assertEqual(read_text(os.path.join(run.row_dir, "resume-line.txt")), "NO-RESUME-LINE\n")

    def test_a_row_1_chain_with_a_resume_line_runs_three_stages_in_two_sessions(self) -> None:
        run = Registered(ROW1)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        calls = [call["args"] for call in run.rig.calls()]
        self.assertEqual(len(calls), 3)
        first, second, third = calls
        session = read_json(run.raw("run.json"))["session_id"]
        self.assertEqual(first[first.index("--session-id") + 1], session)
        self.assertEqual(second[second.index("--resume") + 1], session)
        fresh = third[third.index("--session-id") + 1]
        self.assertNotEqual(fresh, session)
        self.assertNotIn("stage s3: not run (%s)" % row1().MARKER_NONE, run.outcome.lines)
        self.assertEqual(read_json(run.raw("run.json"))["bound_ledger"], "B")


def evidence_tree(root: str) -> dict:
    found = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            found[os.path.relpath(full, root)] = read_bytes(full)
    return found


def _sanitizer_of_root(rig, run_root: str, ctx):
    import pc_sanitize

    paths = row1().paths_for(run_root)
    return pc_sanitize.Sanitizer.from_machine(rig.repo, row1().caller_map(paths, ctx.runs_root))


def _sanitizer_of(run: Registered):
    return _sanitizer_of_root(run.rig, run.run_root, run.ctx)


def _deny_of(run: Registered):
    return _sanitizer_of(run).deny_entries()


if __name__ == "__main__":
    unittest.main()
