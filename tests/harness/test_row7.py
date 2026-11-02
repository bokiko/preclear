"""Zero-token tests for row 7, all checkpoint destinations denied (plan 04-06; HARN-12, RERUN-01; D-04, D-05, D-08).

Row 7 has three stages: s1 a work turn, then the harness sets the project folder to mode 555 and takes the extra
snapshot, s2 the /preclear turn, which cannot save a checkpoint file, and s3 a fresh session whose prompt is the
checkpoint the s2 reply printed. Before any session a live probe proves on the machine that a folder at mode 555 refuses
a create; a machine where it does not is filed as SKIPPED with exit 10, no session and no ledger line. These tests prove
the probe, the skip, the chain, the restriction and its restore, and the fence scanner that finds the printed checkpoint
(also against the committed replies, read in place and never copied). No test starts a real claude: the only claude
executed is the scripted fake written by pc_testutil. Folders come from RowRig and are never deleted. Modules are
imported inside small accessors so a missing module is one error per test, not one load failure of the file. Messages
that name a path are never asserted on by value; leak-shaped strings are never typed in this file.
"""
from __future__ import annotations

import errno
import hashlib
import io
import json
import os
import re
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import pc_exitcodes
import pc_testutil
from test_row_generic import Registered, tree_names
from test_rows_plain import (
    FIXED_DATE,
    PLAN_DIGEST,
    SHAPED,
    VERDICT_LINE,
    EXTRA_RULES,
    checks,
    committed,
    evidence,
    matrix,
    read_bytes,
    read_json,
    read_text,
    row1,
    rowhooks,
    rows,
    sha_lines,
    spec_of,
)

ROW7 = "row7-all-destinations-denied"
RESTRICTION_SNAPSHOT = "snap-1b-after-restriction"
HOOK_BOUNDARY = "s1-restrict-project-555"
PLANS_RELATIVE = "thoughts/plans"
PERMS_LINE = re.compile(r"(\.|[A-Za-z0-9_./-]+) [0-7]{3}\n\Z")
EXPECTED_BOUNDARIES = [
    {"name": "setup", "snapshot": "snap-0-setup"},
    {"name": "s1", "snapshot": "snap-1-after-work"},
    {"name": HOOK_BOUNDARY, "snapshot": RESTRICTION_SNAPSHOT},
    {"name": "s2", "snapshot": "snap-2-after-preclear"},
    {"name": "s3", "snapshot": "snap-3-after-resume"},
]
SECTIONS = ("Identity and state", "Boundaries and blockers", "Next action", "Resume reading",
            "Evidence and working changes", "Do not redo")
NEEDED = ("## Identity and state", "## Do not redo")
CREATE_REFUSED = "the create inside the folder at mode 555 was refused with an error other than permission denied"


def varied(length: int) -> str:
    """Deterministic text of exactly this many characters with no long run of one character (the leak gate refuses one)."""
    words = " ".join("word%d" % index for index in range(length // 4 + 8))
    return words[:length]


def mode_of(path: str) -> int:
    return os.stat(path).st_mode & 0o777


def project_of(run_root: str) -> str:
    return os.path.join(run_root, "project")


def plans_of(run_root: str) -> str:
    return os.path.join(run_root, "project", *PLANS_RELATIVE.split("/"))


def checkpoint_block(headings=SECTIONS, filler="A short body for this section.") -> str:
    """A printed checkpoint: the committed section headings, each with one body line, no trailing newline."""
    return "\n".join("## %s\n%s\n" % (name, filler) for name in headings).rstrip("\n")


def reply_with(block: str, fence: str = "```markdown", closing: str = "```", before: str = "Persistence is BLOCKED.\n\n",
               after: str = "\n\nPaste the checkpoint above into a new session.\n") -> str:
    return before + fence + "\n" + block + "\n" + closing + after


def row7_stages(reply=None, extra_s2_ops=(), s3_ops=None, spec=None) -> list:
    """The scripted row 7 stages: s1 work, s2 a denied create then the reply, s3 a fresh read-only session.

    s2 tries an exclusive create under the project (a folder at mode 555 refuses it) and ends with the reply text,
    which by default holds one fenced checkpoint; s3 loads the project instruction file and only reads.
    """
    stages = pc_testutil.default_row_stages(spec if spec is not None else spec_of(ROW7))
    stages[1] = {
        "ops": [
            {"op": "tool", "name": "Bash", "input": {"command": "ls"}, "content": "CLAUDE.md"},
            {"op": "try_write", "path": "$PROJECT/.preclear/widget-export/checkpoint.md", "text": "a checkpoint\n"},
        ]
        + list(extra_s2_ops)
        + [{"op": "text", "text": "the checkpoint could not be saved"}],
        "result": {
            "text": reply if reply is not None else reply_with(checkpoint_block()),
            "total_cost_usd": 0.09, "delta": 0.06, "num_turns": 5,
        },
    }
    if s3_ops is not None:
        stages[2]["ops"] = list(s3_ops)
    return stages


class Row7Run(object):
    """One scripted row 7 run; the mode of the project and plans folders is recorded at the start of every stage.

    prepare is called with the rig before the run. patches are started around the run and stopped after it. When raises names an exception class, the run is expected
    to end with it: it is kept in error and run is None (run_root still names the run folder the rig holds).
    """

    def __init__(self, stages=None, wrap=None, patches=(), raises=None, prepare=None) -> None:
        self.spec = spec_of(ROW7)
        scripted = stages if stages is not None else row7_stages()
        self.modes = {}
        self.error = None
        original = row1().run_stage
        recorder = self

        def watching(ctx, paths, spec, *args, **kwargs):
            root = str(paths["run_root"])
            recorder.modes[spec.name] = (mode_of(project_of(root)), mode_of(plans_of(root)))
            if wrap is not None:
                wrap(ctx, paths, spec)
            return original(ctx, paths, spec, *args, **kwargs)

        self.rig = pc_testutil.RowRig(stages=scripted)
        self.ctx = self.rig.context()
        if prepare is not None:
            prepare(self.rig)
        managers = [mock.patch.object(row1(), "run_stage", watching)] + list(patches)
        for manager in managers:
            manager.start()
        try:
            if raises is None:
                self.run = Registered(ROW7, rig=self.rig)
            else:
                self.run = None
                try:
                    Registered(ROW7, rig=self.rig)
                except raises as problem:
                    self.error = problem
        finally:
            for manager in reversed(managers):
                manager.stop()

    @property
    def run_root(self) -> str:
        names = [n for n in sorted(os.listdir(self.rig.runs)) if "skipped" not in n]
        assert len(names) == 1, names
        return os.path.join(self.rig.runs, names[0])

    def __getattr__(self, name):
        if name == "run":
            raise AttributeError(name)
        return getattr(self.run, name)

    def raw(self, name: str) -> str:
        return os.path.join(self.run_root, "raw", name)

    def read(self, name: str) -> str:
        return read_text(os.path.join(self.run.row_dir, name))

    def lines(self) -> str:
        return "\n".join(self.run.outcome.lines)


def runs_of(chain) -> list:
    return sorted(os.listdir(chain.ctx.runs_root))


# ---------------------------------------------------------------------------------------------
# The registry entry and the seed
# ---------------------------------------------------------------------------------------------


class Row7RegistryTests(unittest.TestCase):
    def test_row7_is_registered_with_the_three_committed_stages_the_plain_policy_and_the_printed_checkpoint_chain(self) -> None:
        pc_rows = rows()
        spec = spec_of(ROW7)
        self.assertTrue(spec.implemented)
        self.assertEqual([stage.name for stage in spec.stages], ["s1", "s2", "s3"])
        self.assertEqual([stage.kind for stage in spec.stages], ["work", "preclear", "resume"])
        self.assertEqual([stage.max_turns for stage in spec.stages], [15, 60, 15])
        self.assertEqual([str(stage.cap) for stage in spec.stages], ["0.30", "1.30", "0.40"])
        self.assertEqual([stage.timeout for stage in spec.stages], [900, 1800, 900])
        self.assertEqual([stage.session for stage in spec.stages], ["new:A", "resume:A", "new:B"])
        self.assertEqual(pc_rows.session_count(spec), 2)
        self.assertEqual(pc_rows.worst_case(spec), Decimal("2.00"))
        self.assertEqual(spec.tools_profile, pc_rows.PROFILE_PLAIN)
        self.assertEqual(list(spec.extra_tools), EXTRA_RULES)
        self.assertEqual(spec.memory, pc_rows.MEMORY_PINNED)
        self.assertEqual(spec.hooks, (("s1", "restrict-project-555"),))
        self.assertEqual(spec.chain, pc_rows.CHAIN_PRINTED_CHECKPOINT)
        self.assertEqual(spec.probe, pc_rows.PROBE_CHMOD)
        self.assertTrue(callable(spec.precondition))
        self.assertEqual([name for name, _path in spec.prompts], ["s1", "s2"], "s3 has no prompt file: it is the printed block")
        self.assertEqual(dict(spec.prompts)["s2"], "tests/evidence/publication-2026-10-20/row7-all-destinations-denied/s2-preclear-prompt.md")
        self.assertTrue(spec.setup_text.startswith("Setup: "))
        self.assertIsNone(SHAPED.search(spec.setup_text))
        self.assertTrue(spec.setup_text.isascii())
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for relative, kind in spec.sources:
            full = os.path.join(root, *relative.split("/"))
            self.assertTrue(os.path.isdir(full) if kind == "dir" else os.path.isfile(full), "a source is missing")

    def test_row7_the_chain_and_probe_fields_are_defaulted_and_only_row7_names_them(self) -> None:
        pc_rows = rows()
        built = pc_rows.RowSpec("row0-x", "row", "x", (), False, None, None, ())
        self.assertEqual(built.chain, pc_rows.CHAIN_RESUME_LINE)
        self.assertEqual(built.probe, "")
        self.assertEqual([e.row_id for e in pc_rows.build_registry() if e.chain != pc_rows.CHAIN_RESUME_LINE], [ROW7])
        self.assertEqual([e.row_id for e in pc_rows.build_registry() if e.probe], [ROW7])
        self.assertEqual([e.row_id for e in pc_rows.build_registry() if e.precondition is not None], [ROW7])

    def test_row7_the_hook_is_known_names_a_stage_has_a_snapshot_a_finalizer_and_a_changes_table_of_the_folder_alone(self) -> None:
        hooks = rowhooks()
        self.assertIn("restrict-project-555", hooks.HOOKS)
        self.assertEqual(hooks.HOOK_SNAPSHOTS["restrict-project-555"], RESTRICTION_SNAPSHOT)
        self.assertEqual(hooks.FINALIZER_OF["restrict-project-555"], "restore-project-755")
        self.assertIn("restore-project-755", hooks.FINALIZERS)
        self.assertEqual(hooks.TARGETS["restrict-project-555"], ((".", "dir"), (PLANS_RELATIVE, "dir")))
        self.assertEqual(hooks.CHANGES["restrict-project-555"], ((".", "dir"),), "only the project folder is changed")
        self.assertEqual(hooks.PROBES[rows().PROBE_CHMOD], hooks.chmod_denial_probe)
        self.assertEqual(hooks.PROBE_CHMOD, rows().PROBE_CHMOD)

    def test_row7_list_marks_the_row_implemented_with_three_stages_and_two_sessions(self) -> None:
        lines = matrix().list_lines(rows().build_registry())
        cells = dict((line.split()[1], line.split()) for line in lines[1:])
        self.assertEqual(cells[ROW7][2:], ["3", "2", "yes"])

    def dry_run(self, root_user: bool):
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-row7-"))
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
        patches = [mock.patch("subprocess.Popen", side_effect=AssertionError("a process was started"))]
        if root_user:
            patches.append(mock.patch.object(rowhooks(), "_effective_user", return_value=0))
        for patch in patches:
            patch.start()
        try:
            code = matrix().main(["--dry-run", "--row", ROW7], env=env, clock=lambda: FIXED_DATE, out=out, err=err)
        finally:
            for patch in reversed(patches):
                patch.stop()
        return code, out.getvalue() + err.getvalue(), pc_testutil.read_tripwire(bin_dir), base

    @unittest.skipIf(os.geteuid() == 0, "the dry run of a root account reads as a skip")
    def test_row7_the_dry_run_prints_the_plan_and_starts_no_process_and_creates_nothing(self) -> None:
        code, text, tripwire, base = self.dry_run(False)
        self.assertEqual(code, 0, text)
        self.assertIn("%s: 3 stages, 2 sessions" % ROW7, text)
        lines = [line for line in text.splitlines() if line.strip().startswith(("s1", "s2", "s3"))]
        self.assertEqual(len(lines), 3)
        for line, (turns, cap) in zip(lines, (("15", "0.30"), ("60", "1.30"), ("15", "0.40"))):
            self.assertIn("%s turns" % turns, line)
            self.assertIn("cap %s" % cap, line)
        self.assertIn("worst case 2.00 USD", text)
        self.assertIn("allowlist 35 rules", text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")), "a dry run creates no harness home")
        self.assertFalse(os.path.exists(os.path.join(base, "runs-root")), "a dry run creates no run folder")

    def test_row7_the_dry_run_of_a_root_account_names_the_skip_and_still_creates_nothing(self) -> None:
        code, text, tripwire, base = self.dry_run(True)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_SKIP, text)
        self.assertIn("SKIPPED: " + rowhooks().REASON_PROBE_ROOT, text)
        self.assertEqual(tripwire, [])
        self.assertFalse(os.path.exists(os.path.join(base, "hh")))
        self.assertFalse(os.path.exists(os.path.join(base, "runs-root")))


class Row7SeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from test_rows_plain import SeededPlain

        cls.seeded = SeededPlain(ROW7, "plain-seed-row7")

    def test_row7_the_seeded_claude_md_equals_the_committed_fixture_and_the_digest_rows_6_to_12_share(self) -> None:
        data = read_bytes(os.path.join(self.seeded.paths["project"], "CLAUDE.md"))
        self.assertEqual(data, read_bytes(committed(ROW7, "fixture-CLAUDE.md")))
        digest = hashlib.sha256(data).hexdigest()
        self.assertTrue(digest.startswith("ed03447e9df43888"), digest)
        self.assertEqual(digest, sha_lines(ROW7)["project/CLAUDE.md"])

    def test_row7_the_plan_equals_the_plain_data_file_and_hashes_to_the_committed_digest(self) -> None:
        plan = os.path.join(self.seeded.run_root, "project", "thoughts", "plans", "2026-10-15-widget-export.md")
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "plain-plan.md")
        self.assertEqual(read_bytes(plan), read_bytes(data_file))
        self.assertEqual(hashlib.sha256(read_bytes(plan)).hexdigest(), PLAN_DIGEST)
        self.assertEqual(sha_lines(ROW7)["project/thoughts/plans/2026-10-15-widget-export.md"], PLAN_DIGEST)

    def test_row7_memory_is_pinned_the_settings_show_the_enabled_switch_and_the_run_record_names_the_row(self) -> None:
        settings = read_json(self.seeded.paths["settings"])
        self.assertIs(settings["autoMemoryEnabled"], True)
        self.assertEqual(settings["autoMemoryDirectory"], os.path.realpath(self.seeded.paths["auto_memory"]))
        self.assertIs(read_json(committed(ROW7, "settings.json"))["autoMemoryEnabled"], True)
        record = read_json(os.path.join(self.seeded.paths["raw"], "run.json"))
        self.assertEqual(record["row"], ROW7)
        self.assertEqual(record["memory"], rows().MEMORY_PINNED)

    def test_row7_the_seed_leaves_the_project_unrestricted_and_makes_no_probe_folder_and_no_boundary_list(self) -> None:
        self.assertEqual(mode_of(project_of(self.seeded.run_root)), 0o700)
        self.assertFalse(os.path.lexists(os.path.join(self.seeded.paths["raw"], "probe-chmod")))
        self.assertFalse(os.path.lexists(os.path.join(self.seeded.paths["raw"], "boundaries.json")))
        self.assertEqual(os.listdir(self.seeded.paths["ledgers"]), [])


# ---------------------------------------------------------------------------------------------
# The live probe, the SKIPPED label and the exit code
# ---------------------------------------------------------------------------------------------


def fresh_raw_dir() -> str:
    base = os.path.realpath(tempfile.mkdtemp(prefix="pc-probe-"))
    raw = os.path.join(base, "raw")
    os.makedirs(raw)
    return raw


@unittest.skipIf(os.geteuid() == 0, "the probe of a root account is a skip by design")
class ChmodProbeTests(unittest.TestCase):
    def test_probe_a_normal_account_holds_the_denial_and_the_folder_is_back_at_755_and_empty(self) -> None:
        raw = fresh_raw_dir()
        self.assertIsNone(rowhooks().chmod_denial_probe(raw))
        probe = os.path.join(raw, "probe-chmod")
        self.assertTrue(os.path.isdir(probe) and not os.path.islink(probe))
        self.assertEqual(mode_of(probe), 0o755)
        self.assertEqual(os.listdir(probe), [], "the exclusive create inside the folder at mode 555 made nothing")
        self.assertEqual(os.listdir(raw), ["probe-chmod"], "the probe touches nothing else")

    def test_probe_the_folder_is_created_exclusively_so_a_second_probe_in_the_same_raw_folder_is_a_reason(self) -> None:
        raw = fresh_raw_dir()
        self.assertIsNone(rowhooks().chmod_denial_probe(raw))
        self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_SETUP)
        self.assertEqual(mode_of(os.path.join(raw, "probe-chmod")), 0o755)

    def test_probe_a_planted_link_in_place_of_the_folder_is_refused_and_nothing_outside_is_changed(self) -> None:
        raw = fresh_raw_dir()
        outside = os.path.join(os.path.dirname(raw), "elsewhere")
        os.makedirs(outside)
        os.chmod(outside, 0o700)
        os.symlink(outside, os.path.join(raw, "probe-chmod"))
        self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_SETUP)
        self.assertEqual(mode_of(outside), 0o700, "a mode was changed through a planted link")
        self.assertEqual(os.listdir(outside), [])

    def test_probe_the_check_before_a_mode_change_refuses_a_link_a_file_and_a_folder_of_another_name(self) -> None:
        hooks = rowhooks()
        raw = fresh_raw_dir()
        outside = os.path.join(os.path.dirname(raw), "elsewhere")
        os.makedirs(outside)
        os.chmod(outside, 0o700)
        link = os.path.join(raw, "probe-chmod")
        os.symlink(outside, link)
        with self.assertRaises(OSError):
            hooks._probe_chmod(raw, link, 0o555)
        other = os.path.join(raw, "another")
        os.makedirs(other)
        with self.assertRaises(OSError):
            hooks._probe_chmod(raw, other, 0o555)
        self.assertEqual(mode_of(outside), 0o700)

    def test_probe_a_root_account_is_a_reason_and_nothing_is_made(self) -> None:
        raw = fresh_raw_dir()
        with mock.patch.object(rowhooks(), "_effective_user", return_value=0):
            self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_ROOT)
        self.assertEqual(os.listdir(raw), [])

    def test_probe_a_mount_that_ignores_the_mode_lets_the_create_succeed_and_that_is_a_reason(self) -> None:
        raw = fresh_raw_dir()
        with mock.patch.object(rowhooks(), "_chmod_path", lambda path, mode: None):
            self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_CREATED)
        self.assertEqual(os.listdir(os.path.join(raw, "probe-chmod")), ["x"], "the created file is left, never deleted")

    def test_probe_any_other_error_than_permission_denied_is_a_reason_and_the_folder_is_still_returned_to_755(self) -> None:
        for error in (PermissionError(errno.EPERM, "refused"), OSError(errno.EIO, "io"), PermissionError(errno.EROFS, "ro")):
            raw = fresh_raw_dir()
            with mock.patch.object(rowhooks(), "_create_probe_file", side_effect=error):
                self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_OTHER, repr(error))
            self.assertEqual(mode_of(os.path.join(raw, "probe-chmod")), 0o755)

    def test_probe_a_denial_with_the_right_errno_is_the_only_effective_result(self) -> None:
        raw = fresh_raw_dir()
        error = PermissionError(errno.EACCES, "denied")
        with mock.patch.object(rowhooks(), "_create_probe_file", side_effect=error):
            self.assertIsNone(rowhooks().chmod_denial_probe(raw))
        self.assertEqual(mode_of(os.path.join(raw, "probe-chmod")), 0o755)

    def test_probe_a_folder_that_cannot_be_returned_to_its_normal_mode_is_a_reason_even_when_the_denial_held(self) -> None:
        raw = fresh_raw_dir()
        calls = []

        def only_the_first(path, mode):
            calls.append(mode)
            if len(calls) == 1:
                os.chmod(path, mode)
            else:
                raise OSError(errno.EPERM, "refused")

        try:
            with mock.patch.object(rowhooks(), "_chmod_path", only_the_first):
                self.assertEqual(rowhooks().chmod_denial_probe(raw), rowhooks().REASON_PROBE_SETUP)
        finally:
            os.chmod(os.path.join(raw, "probe-chmod"), 0o755)  # the test's own tidy-up of its own folder
        self.assertEqual(calls, [0o555, 0o755])

    def test_probe_the_reasons_are_fixed_words_with_no_path_digit_or_name(self) -> None:
        hooks = rowhooks()
        for reason in (hooks.REASON_PROBE_ROOT, hooks.REASON_PROBE_CREATED, hooks.REASON_PROBE_OTHER, hooks.REASON_PROBE_SETUP):
            self.assertTrue(reason.isascii())
            self.assertIsNone(SHAPED.search(reason))
            self.assertFalse(any(ch.isdigit() for ch in reason.replace("555", "")), reason)
            self.assertNotIn("/", reason)
        self.assertEqual(len(set((hooks.REASON_PROBE_ROOT, hooks.REASON_PROBE_CREATED, hooks.REASON_PROBE_OTHER,
                                  hooks.REASON_PROBE_SETUP))), 4)

    def test_probe_an_unknown_probe_id_is_a_reason_and_makes_nothing(self) -> None:
        raw = fresh_raw_dir()
        self.assertEqual(rowhooks().run_probe("no-such-probe", {"raw": raw}), rowhooks().REASON_PROBE_SETUP)
        self.assertEqual(os.listdir(raw), [])

    def test_probe_the_precondition_is_write_free_a_reason_for_root_and_none_otherwise(self) -> None:
        hooks = rowhooks()
        before = set(os.listdir(tempfile.gettempdir()))
        self.assertIsNone(hooks.chmod_precondition())
        with mock.patch.object(hooks, "_effective_user", return_value=0):
            self.assertEqual(hooks.chmod_precondition(), hooks.REASON_PROBE_ROOT)
        self.assertEqual(set(os.listdir(tempfile.gettempdir())) - before, set(), "the precondition wrote something")
        self.assertIsNone(spec_of(ROW7).precondition())

    def test_probe_the_live_probe_runs_in_the_runner_and_the_setup_guard_lists_the_probe_folder(self) -> None:
        chain = Row7Run()
        self.assertEqual(chain.outcome.code, 0, chain.lines())
        guard = read_json(chain.raw("setup.guard.json"))
        self.assertIn("probe-chmod", json.dumps(guard["raw"]), "the guard's first raw listing holds the probe folder")
        self.assertEqual(mode_of(os.path.join(chain.raw("probe-chmod"))), 0o755)
        self.assertEqual(os.listdir(chain.raw("probe-chmod")), [])
        self.assertEqual(len(chain.rig.calls()), 3)


def skip_case(patches):
    chain = Row7Run(patches=patches)
    return chain


class SkippedRowTests(unittest.TestCase):
    """The probe fails in three ways (root, a created file, another error): each is a label, exit 10 and no spend."""

    @classmethod
    def setUpClass(cls) -> None:
        hooks = rowhooks()
        cls.cases = {
            "root": (hooks.REASON_PROBE_ROOT, [mock.patch.object(hooks, "_effective_user", return_value=0)]),
            "created": (hooks.REASON_PROBE_CREATED, [mock.patch.object(hooks, "_chmod_path", lambda path, mode: None)]),
            "other": (hooks.REASON_PROBE_OTHER,
                      [mock.patch.object(hooks, "_create_probe_file", side_effect=OSError(errno.EIO, "io"))]),
        }
        cls.chains = {name: Row7Run(patches=patches) for name, (_reason, patches) in cls.cases.items()}

    def each(self):
        for name, chain in self.chains.items():
            yield name, chain, self.cases[name][0]

    def test_skip_each_kind_exits_10_files_the_skipped_label_and_never_reads_as_success(self) -> None:
        for name, chain, reason in self.each():
            self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_SKIP, name)
            self.assertNotEqual(chain.outcome.code, 0)
            self.assertEqual(os.listdir(chain.ctx.destination), ["SKIPPED-" + ROW7], name)
            self.assertEqual(chain.outcome.lines[0], "SKIPPED: " + reason, name)

    def test_skip_no_session_ran_and_the_ledger_holds_no_line_and_no_stage_record_exists(self) -> None:
        for name, chain, _reason in self.each():
            self.assertEqual(chain.rig.calls(), [], name)
            self.assertEqual(chain.rig.tripwire(), [], name)
            self.assertEqual(chain.ledger(), [], name)
            self.assertEqual(chain.outcome.spent, Decimal("0"), name)
            made = [d for d in runs_of(chain) if "skipped" not in d]
            self.assertEqual(len(made), 1, name)
            raw = os.path.join(chain.ctx.runs_root, made[0], "raw")
            self.assertEqual([n for n in os.listdir(raw) if n.startswith("s1")], [], name)
            self.assertFalse(os.path.lexists(os.path.join(chain.ctx.runs_root, made[0], "snaps", "snap-0-setup")), name)

    def test_skip_the_project_stays_unrestricted_and_the_probe_folder_is_at_755_and_never_deleted(self) -> None:
        for name, chain, _reason in self.each():
            made = [d for d in runs_of(chain) if "skipped" not in d][0]
            root = os.path.join(chain.ctx.runs_root, made)
            self.assertEqual(mode_of(project_of(root)), 0o700, name)
            if name != "root":
                probe = os.path.join(root, "raw", "probe-chmod")
                self.assertTrue(os.path.isdir(probe), name)
                # In the created case the mode change itself is stood in for by a no-op, so the folder keeps its own 700.
                self.assertEqual(mode_of(probe), 0o700 if name == "created" else 0o755, name)
            else:
                self.assertFalse(os.path.lexists(os.path.join(root, "raw", "probe-chmod")))

    def test_skip_the_readme_names_the_cause_in_fixed_words_holds_no_path_and_ends_with_the_pending_line(self) -> None:
        for name, chain, reason in self.each():
            text = read_text(os.path.join(chain.ctx.destination, "SKIPPED-" + ROW7, "README.md"))
            self.assertIn(reason, text, name)
            self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"), name)
            self.assertIsNone(SHAPED.search(text), name)
            self.assertIn("No session was run", text)
            self.assertEqual(sorted(tree_names(os.path.join(chain.ctx.destination, "SKIPPED-" + ROW7))), ["README.md"])

    def test_skip_the_printed_lines_hold_no_path_and_no_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        for name, chain, _reason in self.each():
            for line in chain.outcome.lines:
                self.assertIsNone(SHAPED.search(line), name)
                self.assertIsNone(pattern.search(line), name)
            self.assertTrue(any(line.startswith("filed: ") and "SKIPPED-" + ROW7 in line for line in chain.outcome.lines))
            self.assertTrue(any("no session was run" in line for line in chain.outcome.lines))

    def test_skip_a_second_run_of_the_row_after_a_skip_is_refused_only_by_the_skipped_label_collision_rule(self) -> None:
        # The SKIPPED label is a different folder name from the row folder, so a later real run is not refused by it.
        chain = self.chains["other"]
        self.assertFalse(os.path.lexists(os.path.join(chain.ctx.destination, ROW7)))


# ---------------------------------------------------------------------------------------------
# The chain, the restriction, the restore
# ---------------------------------------------------------------------------------------------


class Row7ChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.block = checkpoint_block()
        cls.chain = Row7Run(row7_stages(reply_with(cls.block)))
        assert cls.chain.outcome.code == 0, cls.chain.lines()

    def test_row7_a_scripted_chain_runs_three_stages_in_two_sessions_and_files_one_folder(self) -> None:
        chain = self.chain
        calls = chain.rig.calls()
        self.assertEqual(len(calls), 3)
        self.assertNotIn("--resume", calls[0]["args"])
        self.assertIn("--resume", calls[1]["args"])
        self.assertNotIn("--resume", calls[2]["args"], "s3 is a fresh session")
        first = calls[0]["args"][calls[0]["args"].index("--session-id") + 1]
        third = calls[2]["args"][calls[2]["args"].index("--session-id") + 1]
        self.assertNotEqual(first, third)
        self.assertEqual(calls[1]["args"][calls[1]["args"].index("--resume") + 1], first)
        self.assertEqual(os.listdir(chain.ctx.destination), [ROW7])
        self.assertTrue(any(line.startswith("row total:") for line in chain.outcome.lines))

    def test_row7_the_project_is_open_at_s1_555_at_s2_and_s3_and_755_again_before_filing_and_plans_never_change(self) -> None:
        chain = self.chain
        # The seed makes its folders mode 700; the restriction is the committed 555 and the restore is the planned 755.
        self.assertEqual(chain.modes, {"s1": (0o700, 0o700), "s2": (0o555, 0o700), "s3": (0o555, 0o700)})
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755, "restored before the row was filed")
        self.assertEqual(mode_of(plans_of(chain.run_root)), 0o700)

    def test_row7_s3_runs_with_the_printed_block_as_its_prompt_stored_verbatim_in_raw(self) -> None:
        chain = self.chain
        stored = read_text(chain.raw("s3.prompt"))
        self.assertEqual(stored, self.block)
        self.assertEqual(chain.rig.calls()[2]["prompt"], self.block)
        for heading in NEEDED:
            self.assertIn(heading, stored.splitlines())
        self.assertNotIn("```", stored, "the fences are not part of the prompt")

    def test_row7_the_chain_record_holds_the_marker_the_size_and_no_reason_and_never_the_text(self) -> None:
        record = read_json(self.chain.raw("chain.json"))
        self.assertEqual(sorted(record), ["checkpoint_bytes", "checkpoint_reason", "marker"])
        self.assertEqual(record["marker"], "found")
        self.assertEqual(record["checkpoint_bytes"], len(self.block.encode("utf-8")))
        self.assertIsNone(record["checkpoint_reason"])

    def test_row7_the_boundary_list_names_setup_the_stages_and_the_hook_boundary_in_order(self) -> None:
        chain = self.chain
        self.assertEqual(read_json(chain.raw("boundaries.json")), {"boundaries": EXPECTED_BOUNDARIES})
        planned = checks().read_boundaries(os.path.join(chain.run_root, "raw"))
        self.assertEqual(rowhooks().plan_boundaries(chain.spec), planned)
        facts = checks().compute_facts(chain.run_root, chain.ctx.config_dir)
        self.assertEqual(facts["boundaries"], [item["name"] for item in EXPECTED_BOUNDARIES])
        self.assertEqual(facts["stages"], ["s1", "s2", "s3"])
        self.assertEqual(facts["guard"]["count"], 0)
        self.assertEqual(checks().breaches(facts), [])

    def test_row7_the_restriction_snapshot_holds_a_mode_only_perms_file_for_the_two_targets_and_is_filed(self) -> None:
        chain = self.chain
        text = read_text(os.path.join(chain.run_root, "snaps", RESTRICTION_SNAPSHOT, "perms.txt"))
        self.assertEqual(text, ". 555\n%s 700\n" % PLANS_RELATIVE)
        for line in text.splitlines(True):
            self.assertIsNotNone(PERMS_LINE.match(line), "mode-only: a path and an octal mode, nothing else")
            self.assertEqual(len(line.split()), 2)
        filed = tree_names(chain.run.row_dir)
        self.assertEqual(chain.read(RESTRICTION_SNAPSHOT + "/perms.txt"), text)
        self.assertEqual(
            [n for n in filed if n.startswith("snap-") and n.endswith("/") and n.count("/") == 1],
            ["snap-0-setup/", "snap-1-after-work/", RESTRICTION_SNAPSHOT + "/", "snap-2-after-preclear/", "snap-3-after-resume/"],
        )
        for other in ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume"):
            self.assertNotIn(other + "/perms.txt", filed, "only the restriction boundary lists modes")

    def test_row7_perms_text_holds_no_owner_group_date_size_or_login_name(self) -> None:
        import pwd

        text = self.chain.read(RESTRICTION_SNAPSHOT + "/perms.txt")
        self.assertNotIn(pwd.getpwuid(os.getuid()).pw_name, text)
        self.assertIsNone(SHAPED.search(text))
        self.assertTrue(text.isascii())
        self.assertEqual(text.count("\n"), 2)
        self.assertEqual([len(line.split()) for line in text.splitlines()], [2, 2])

    def test_row7_the_snapshots_after_the_restriction_show_no_change_in_the_scripted_s3_and_the_plan_digest_is_kept(self) -> None:
        chain = self.chain
        names = ("snap-1-after-work", RESTRICTION_SNAPSHOT, "snap-2-after-preclear", "snap-3-after-resume")
        sha = [chain.read(name + "/sha.txt") for name in names]
        self.assertEqual(sha[1], sha[2], "s2 changed nothing in the restricted project")
        self.assertEqual(sha[2], sha[3], "s3 changed nothing in the restricted project")
        for text in [chain.read("snap-0-setup/sha.txt")] + sha:
            digests = [line.split("  ")[0] for line in text.splitlines() if line.endswith("project/" + PLANS_RELATIVE + "/2026-10-15-widget-export.md")]
            self.assertEqual(digests, [PLAN_DIGEST])

    def test_row7_a_scripted_write_into_the_restricted_folder_gets_the_structured_error_flag_and_the_word_eacces(self) -> None:
        stream = [json.loads(line) for line in read_text(self.chain.raw("s2.stdout")).splitlines() if line.strip()]
        results = []
        for event in stream:
            message = event.get("message") if isinstance(event, dict) else None
            if event.get("type") == "user" and isinstance(message, dict):
                results.extend(item for item in message.get("content", []) if item.get("type") == "tool_result")
        flagged = [item for item in results if item.get("is_error") is True]
        self.assertEqual(len(flagged), 1)
        self.assertIn("EACCES", flagged[0]["content"])
        self.assertFalse(os.path.lexists(os.path.join(self.chain.run_root, "project", ".preclear")))

    def test_row7_the_stage_commands_carry_the_35_plain_rules_and_the_enabled_memory_switch(self) -> None:
        import pc_flags

        wanted = list(pc_flags.BASELINE_ALLOWED_TOOLS) + EXTRA_RULES
        self.assertEqual(len(wanted), 35)
        for call in self.chain.rig.calls():
            argv = call["args"]
            self.assertEqual(argv[argv.index("--allowedTools") + 1].split(","), wanted)
            self.assertIs(read_json(argv[argv.index("--settings") + 1])["autoMemoryEnabled"], True)
        self.assertEqual(self.chain.read("tools.txt"), ",".join(wanted) + "\n")

    def test_row7_the_ledger_holds_three_launches_and_three_settlements_for_the_row(self) -> None:
        self.assertEqual(
            [(r["kind"], r["stage"]) for r in self.chain.ledger()],
            [("launch", "row7-s1"), ("settle", "row7-s1"), ("launch", "row7-s2"), ("settle", "row7-s2"),
             ("launch", "row7-s3"), ("settle", "row7-s3")],
        )

    def test_row7_the_readme_names_the_chain_shape_ends_with_the_pending_line_and_holds_no_verdict_word(self) -> None:
        text = self.chain.read("README.md")
        self.assertTrue(text.endswith("\n" + VERDICT_LINE + "\n"))
        self.assertEqual(text.count(VERDICT_LINE), 1)
        body = text[: -len(VERDICT_LINE) - 1]
        self.assertIn(self.chain.spec.setup_text, body)
        self.assertIn("- chain shape: the /preclear reply printed a checkpoint (%d bytes) and a fresh session was started from it"
                      % len(self.block.encode("utf-8")), body)
        self.assertIsNone(evidence().verdict_pattern().search(body))
        self.assertEqual(body.splitlines()[0].split(",")[0], "# Row 7: all checkpoint destinations denied (1P)")
        self.assertIsNone(SHAPED.search(body))

    def test_row7_the_filed_folder_has_no_resume_line_file_because_the_row_prints_no_resume_line(self) -> None:
        filed = tree_names(self.chain.run.row_dir)
        self.assertNotIn("resume-line.txt", filed)
        self.assertIn("s3-resume-trace.md", filed)

    def test_row7_the_mechanical_checks_print_the_chmod_and_touch_counts_and_all_five_boundary_states(self) -> None:
        lines = self.chain.read("mechanical-checks.md").splitlines()
        self.assertIn("executed-chmod-commands: 0", lines)
        self.assertIn("executed-touch-commands: 0", lines)
        states = [line.split(":")[0] for line in lines if line.startswith("state ")]
        self.assertEqual(states, ["state setup", "state s1", "state " + HOOK_BOUNDARY, "state s2", "state s3"])
        self.assertIn("states: 5", lines)

    def test_row7_no_harness_authored_file_holds_a_verdict_word(self) -> None:
        pattern = evidence().verdict_pattern()
        dest = self.chain.ctx.destination
        names = []
        for dirpath, _dirnames, filenames in os.walk(dest):
            for name in filenames:
                names.append(os.path.relpath(os.path.join(dirpath, name), dest).replace(os.sep, "/"))
        authored = evidence().harness_authored_names(sorted(names))
        self.assertIn(ROW7 + "/" + RESTRICTION_SNAPSHOT + "/perms.txt", authored)
        for name in authored:
            text = read_text(os.path.join(dest, name))
            if name == ROW7 + "/README.md":
                text = text[: -len(VERDICT_LINE) - 1]
            self.assertIsNone(pattern.search(text), "no verdict word in " + name)


# ---------------------------------------------------------------------------------------------
# The fence scanner and the printed checkpoint
# ---------------------------------------------------------------------------------------------

TRACE_ROWS = ("row7-all-destinations-denied", "row3c-unbound-fallback-none", "row4b-conflicting-blocks")


def committed_final_reply(row_id: str) -> str:
    """The text after the Final reply heading of a committed s2 trace, read in place (never copied, never edited)."""
    text = read_text(committed(row_id, "s2-preclear-trace.md"))
    head = "\n## Final reply\n"
    assert head in text, row_id
    return text.split(head, 1)[1]


def printed(text):
    return row1().printed_checkpoint(text)


class PrintedCheckpointTests(unittest.TestCase):
    def test_extract_returns_the_block_between_prose_and_closing_text_without_the_fences(self) -> None:
        block = checkpoint_block()
        self.assertEqual(row1().extract_printed_checkpoint(reply_with(block)), block)
        self.assertEqual(printed(reply_with(block)), (block, ""))

    def test_extract_two_matching_blocks_give_the_last_one(self) -> None:
        first, second = checkpoint_block(filler="first body"), checkpoint_block(filler="second body")
        text = reply_with(first) + "\n" + reply_with(second, before="Again:\n\n")
        self.assertEqual(row1().extract_printed_checkpoint(text), second)

    def test_extract_a_matching_block_followed_by_a_block_without_the_headings_still_gives_the_matching_one(self) -> None:
        block = checkpoint_block()
        text = reply_with(block) + "\n```\nonly a command\n```\n"
        self.assertEqual(row1().extract_printed_checkpoint(text), block)

    def test_extract_an_inner_fence_shorter_than_the_outer_one_does_not_cut_the_block(self) -> None:
        inner = "```\nnot a closing fence for the long one\n```"
        block = checkpoint_block() + "\n" + inner
        text = reply_with(block, fence="````markdown", closing="````")
        self.assertEqual(row1().extract_printed_checkpoint(text), block)

    def test_extract_an_inner_fence_of_the_same_length_closes_the_block_at_that_line_as_documented(self) -> None:
        head = checkpoint_block(headings=("Identity and state",))
        text = "```markdown\n" + head + "\n```\n## Do not redo\nx\n```\n"
        self.assertEqual(printed(text), ("", "none"), "the block ended at the first fence and lacks the second heading")
        both = "```markdown\n" + checkpoint_block() + "\n```\ntail\n```\n"
        self.assertEqual(row1().extract_printed_checkpoint(both), checkpoint_block(), "the later lone fence opens nothing")

    def test_extract_a_longer_closing_fence_closes_and_an_indent_of_up_to_three_spaces_is_allowed(self) -> None:
        block = checkpoint_block()
        self.assertEqual(row1().extract_printed_checkpoint("```md\n" + block + "\n`````\n"), block)
        self.assertEqual(row1().extract_printed_checkpoint("   ```md\n" + block + "\n   ```\n"), block)
        self.assertEqual(row1().extract_printed_checkpoint("    ```md\n" + block + "\n    ```\n"), "", "four spaces is code")
        self.assertEqual(row1().extract_printed_checkpoint("``` markdown title\n" + block + "\n```\n"), block)

    def test_extract_no_block_an_unclosed_fence_and_a_text_that_is_not_a_string_give_none(self) -> None:
        self.assertEqual(printed("just prose"), ("", "none"))
        self.assertEqual(printed(""), ("", "none"))
        self.assertEqual(printed("```markdown\n" + checkpoint_block() + "\n"), ("", "none"), "never closed")
        for odd in (None, 7, b"```x```", ["a"]):
            self.assertEqual(printed(odd), ("", "none"))
            self.assertEqual(row1().extract_printed_checkpoint(odd), "")

    def test_extract_a_fenced_block_that_lacks_one_heading_gives_none(self) -> None:
        for headings in (("Identity and state", "Next action"), ("Do not redo", "Next action"), ("Next action",)):
            self.assertEqual(printed(reply_with(checkpoint_block(headings=headings))), ("", "none"), headings)

    def test_extract_heading_text_in_prose_or_not_as_a_whole_heading_line_does_not_count(self) -> None:
        prose = "The headings ## Identity and state and ## Do not redo are named here.\n\n```\nlist\n```\n"
        self.assertEqual(printed(prose), ("", "none"))
        outside = checkpoint_block() + "\n\n```\nonly this is fenced\n```\n"
        self.assertEqual(printed(outside), ("", "none"), "headings outside any fence do not make a block")
        for bad in ("## Do not redo today", "  ## Do not redo", "### Do not redo", "## do not redo"):
            block = "## Identity and state\nx\n" + bad + "\ny"
            self.assertEqual(printed(reply_with(block)), ("", "none"), bad)
        trailing = "## Identity and state  \nx\n## Do not redo\t\ny"
        self.assertEqual(row1().extract_printed_checkpoint(reply_with(trailing)), trailing, "trailing blanks are allowed")

    def test_extract_a_block_of_exactly_8192_bytes_passes_and_8193_does_not(self) -> None:
        base = checkpoint_block(filler="")
        for size, expect_found in ((8192, True), (8193, False)):
            block = base + "\n" + "a" * (size - len(base.encode("utf-8")) - 1)
            self.assertEqual(len(block.encode("utf-8")), size)
            found, reason = printed(reply_with(block))
            self.assertEqual(found, block if expect_found else "")
            self.assertEqual(reason, "" if expect_found else "too-large")
        self.assertEqual(row1().MAX_PRINTED_CHECKPOINT_BYTES, 8192)

    def test_extract_the_cap_counts_bytes_not_characters(self) -> None:
        base = checkpoint_block(filler="")
        pad = (8192 - len(base.encode("utf-8")) - 1) // 2
        within = base + "\n" + "é" * pad
        self.assertLessEqual(len(within.encode("utf-8")), 8192)
        self.assertEqual(row1().extract_printed_checkpoint(reply_with(within)), within)
        over = base + "\n" + "é" * (pad + 1)
        self.assertGreater(len(over.encode("utf-8")), 8192)
        self.assertLessEqual(len(over), 8192, "fewer characters than the cap, more bytes")
        self.assertEqual(printed(reply_with(over)), ("", "too-large"))

    def test_extract_a_nul_anywhere_in_the_block_gives_none_with_the_reason_nul(self) -> None:
        for position in (len("## Identity and state\n"), 40, -1):
            block = checkpoint_block()
            at = position if position >= 0 else len(block) - 1
            block = block[:at] + "\x00" + block[at:]
            self.assertEqual(printed(reply_with(block)), ("", "nul"), position)

    def test_extract_a_last_candidate_that_breaks_a_bound_is_not_replaced_by_an_earlier_one(self) -> None:
        good = checkpoint_block(filler="fine")
        too_big = checkpoint_block(filler="x" * 9000)
        self.assertEqual(printed(reply_with(good) + reply_with(too_big)), ("", "too-large"))
        nul = checkpoint_block(filler="has a \x00 inside")
        self.assertEqual(printed(reply_with(good) + reply_with(nul)), ("", "nul"))
        self.assertEqual(printed(reply_with(too_big) + reply_with(good)), (good, ""), "an oversize earlier block is skipped")

    def test_extract_a_windows_line_ending_text_gives_the_block_with_plain_newlines(self) -> None:
        block = checkpoint_block()
        text = reply_with(block).replace("\n", "\r\n")
        self.assertEqual(row1().extract_printed_checkpoint(text), block)

    def test_extract_the_fence_scanner_returns_every_closed_block_and_nothing_else(self) -> None:
        text = "a\n```\none\n```\nb\n~~~\nnot a fence\n~~~\n```x\ntwo\nthree\n```\n```\nnever closed\n"
        self.assertEqual(row1().fenced_blocks(text), ["one", "two\nthree"])
        self.assertEqual(row1().fenced_blocks(""), [])

    def test_extract_every_committed_reply_that_printed_a_checkpoint_gives_a_block_with_both_headings_committed_reply(self) -> None:
        for row_id in TRACE_ROWS:
            reply = committed_final_reply(row_id)
            found, reason = printed(reply)
            self.assertEqual(reason, "", row_id)
            self.assertGreater(len(found), 200, row_id)
            lines = found.splitlines()
            for heading in NEEDED:
                self.assertIn(heading, lines, row_id)
            self.assertLessEqual(len(found.encode("utf-8")), 8192, row_id)
            self.assertNotIn("\x00", found)
            self.assertNotIn("```", found)
            self.assertEqual(lines[0], "## Identity and state", row_id)

    def test_extract_the_committed_row_7_reply_gives_the_block_with_the_six_sections_committed_reply(self) -> None:
        reply = committed_final_reply("row7-all-destinations-denied")
        found = row1().extract_printed_checkpoint(reply)
        sections = [line for line in found.splitlines() if line.startswith("## ")]
        self.assertEqual(sections, ["## " + name for name in SECTIONS])
        self.assertTrue(found.rstrip().splitlines()[-1].startswith("- No Preclear configuration block"))
        self.assertIn("paste the checkpoint above", reply)

    def test_extract_the_committed_row_7_reply_holds_no_resume_line_so_the_old_rule_finds_none_committed_reply(self) -> None:
        self.assertEqual(row1().extract_resume_line(committed_final_reply("row7-all-destinations-denied")), "")


# ---------------------------------------------------------------------------------------------
# A chain whose s2 reply has no usable checkpoint
# ---------------------------------------------------------------------------------------------

NO_CHECKPOINT_CASES = {
    "no-block": ("Persistence is BLOCKED and nothing could be printed.\n", "none"),
    "oversize": (reply_with(checkpoint_block(filler=varied(9000))), "too-large"),
    "missing-heading": (reply_with(checkpoint_block(headings=("Identity and state", "Next action"))), "none"),
}


class NoPrintedCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chains = {name: Row7Run(row7_stages(reply)) for name, (reply, _reason) in NO_CHECKPOINT_CASES.items()}

    def test_none_each_case_runs_two_stages_files_them_and_exits_0(self) -> None:
        for name, chain in self.chains.items():
            self.assertEqual(chain.outcome.code, 0, name + chain.lines())
            self.assertEqual(len(chain.rig.calls()), 2, name)
            self.assertEqual(os.listdir(chain.ctx.destination), [ROW7], name)
            filed = tree_names(chain.run.row_dir)
            self.assertIn("s2-preclear-trace.md", filed)
            self.assertFalse([n for n in filed if n.startswith("s3")], name)
            self.assertFalse([n for n in filed if n.startswith("snap-3")], name)

    def test_none_the_chain_record_holds_the_marker_zero_bytes_and_the_reason(self) -> None:
        for name, (_reply, reason) in NO_CHECKPOINT_CASES.items():
            record = read_json(self.chains[name].raw("chain.json"))
            self.assertEqual(
                record, {"checkpoint_bytes": 0, "checkpoint_reason": reason, "marker": "NO-PRINTED-CHECKPOINT"}, name
            )
            self.assertFalse(os.path.lexists(self.chains[name].raw("s3.prompt")), name)
            self.assertFalse(os.path.lexists(self.chains[name].raw("s3.record.json")), name)

    def test_none_the_row_prints_the_not_run_line_with_the_marker_word_of_the_strategy(self) -> None:
        for name, chain in self.chains.items():
            self.assertIn("stage s3: not run (NO-PRINTED-CHECKPOINT)", chain.outcome.lines, name)
            self.assertNotIn("NO-RESUME-LINE", chain.lines(), name)

    def test_none_the_project_is_restored_before_filing_and_the_ledger_holds_two_stages_only(self) -> None:
        for name, chain in self.chains.items():
            self.assertEqual(chain.modes, {"s1": (0o700, 0o700), "s2": (0o555, 0o700)}, name)
            self.assertEqual(mode_of(project_of(chain.run_root)), 0o755, name)
            self.assertEqual([r["stage"] for r in chain.ledger()], ["row7-s1", "row7-s1", "row7-s2", "row7-s2"], name)
            self.assertNotIn("snap-3-after-resume", os.listdir(os.path.join(chain.run_root, "snaps")), name)

    def test_none_the_readme_states_the_shape_with_the_reason_and_the_facts_hold_two_stages(self) -> None:
        for name, (_reply, reason) in NO_CHECKPOINT_CASES.items():
            chain = self.chains[name]
            body = chain.read("README.md")
            self.assertIn(
                "- chain shape: the /preclear reply printed no checkpoint the harness could take "
                "(NO-PRINTED-CHECKPOINT: reason %s); no fresh session was run" % reason,
                body,
                name,
            )
            self.assertIsNone(evidence().verdict_pattern().search(body[: -len(VERDICT_LINE) - 1]), name)
            self.assertNotIn("resume-line.txt", tree_names(chain.run.row_dir))
            self.assertEqual(read_json(chain.raw("boundaries.json"))["boundaries"], EXPECTED_BOUNDARIES)
            facts = checks().compute_facts(chain.run_root, chain.ctx.config_dir)
            self.assertEqual(facts["stages"], ["s1", "s2"], name)
            self.assertEqual(checks().breaches(facts), [], name)

    def test_none_heading_text_inside_a_bash_result_is_not_a_checkpoint(self) -> None:
        shown = "```\n" + checkpoint_block() + "\n```"
        stages = row7_stages(
            "Nothing could be printed.\n",
            extra_s2_ops=[{"op": "tool", "name": "Bash", "input": {"command": "cat notes"}, "content": shown}],
        )
        chain = Row7Run(stages)
        self.assertEqual(chain.outcome.code, 0, chain.lines())
        self.assertEqual(len(chain.rig.calls()), 2)
        self.assertEqual(read_json(chain.raw("chain.json"))["marker"], "NO-PRINTED-CHECKPOINT")


class NulReplyTests(unittest.TestCase):
    """A reply whose checkpoint block holds a NUL: no s3, the marker with the reason nul, and no filing at all.

    The leak gate refuses any file that holds a NUL byte (a binary file), so the s2 trace cannot be promoted; the row ends
    with the gate's own exit code and its fixed lines, and the raw files stay in the run root. That is the existing gate
    rule and not a new one: a NUL in a model reply is never filed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.chain = Row7Run(row7_stages(reply_with(checkpoint_block(filler="a \x00 byte"))))

    def test_nul_no_third_session_runs_and_the_chain_record_names_the_reason(self) -> None:
        chain = self.chain
        self.assertEqual(len(chain.rig.calls()), 2)
        self.assertEqual(
            read_json(chain.raw("chain.json")),
            {"checkpoint_bytes": 0, "checkpoint_reason": "nul", "marker": "NO-PRINTED-CHECKPOINT"},
        )
        self.assertFalse(os.path.lexists(chain.raw("s3.prompt")))

    def test_nul_the_gate_refuses_the_filing_with_14_and_nothing_reaches_the_evidence_folder(self) -> None:
        chain = self.chain
        self.assertEqual(chain.outcome.code, pc_exitcodes.LEAK_REFUSED, chain.lines())
        self.assertFalse(os.path.lexists(os.path.join(chain.ctx.destination, ROW7)))
        self.assertIsNone(SHAPED.search(chain.lines()))

    def test_nul_the_project_is_restored_before_the_filing_was_tried(self) -> None:
        self.assertEqual(mode_of(project_of(self.chain.run_root)), 0o755)


# ---------------------------------------------------------------------------------------------
# --refile accepts exactly two shapes for this row
# ---------------------------------------------------------------------------------------------


def first_destination_chain(stages):
    """A chain filed into a side folder, so the dated folder is free for the refile."""
    rig = pc_testutil.RowRig(stages=stages)
    first = os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5-first")
    ctx = rig.context(destination=first)
    outcome = row1().run_registered_row(ctx, ROW7)
    assert outcome.code == 0, "\n".join(outcome.lines)
    names = sorted(os.listdir(ctx.runs_root))
    assert len(names) == 1, names
    return rig, os.path.join(ctx.runs_root, names[0])


def rewrite_chain(run_root: str, **changes) -> None:
    path = os.path.join(run_root, "raw", "chain.json")
    record = read_json(path)
    record.update(changes)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle)


class RefileShapeTests(unittest.TestCase):
    def refile(self, rig, run_root):
        out, err = io.StringIO(), io.StringIO()
        code = matrix().main(
            ["--refile", run_root], env=dict(rig.env), repo_root=rig.repo, clock=lambda: FIXED_DATE, out=out, err=err
        )
        return code, out.getvalue() + err.getvalue()

    def dated(self, rig):
        return os.path.join(rig.repo, "tests", "evidence", "rerun-2026-10-28-claude-sonnet-5-5")

    def test_refile_the_found_run_with_three_stages_is_accepted_with_zero_tokens(self) -> None:
        rig, run_root = first_destination_chain(row7_stages())
        calls = len(rig.calls())
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, 0, text)
        self.assertEqual(len(rig.calls()), calls, "a refile starts no process")
        self.assertIn("filed: %s %s" % (os.path.basename(self.dated(rig)), ROW7), text)
        self.assertTrue(os.path.isfile(os.path.join(self.dated(rig), ROW7, "s3-resume-trace.md")))
        self.assertEqual(mode_of(project_of(run_root)), 0o755)

    def test_refile_the_none_run_with_two_stages_is_accepted(self) -> None:
        rig, run_root = first_destination_chain(row7_stages("No checkpoint could be printed.\n"))
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, 0, text)
        self.assertTrue(os.path.isfile(os.path.join(self.dated(rig), ROW7, "s2-preclear-trace.md")))
        self.assertFalse(os.path.lexists(os.path.join(self.dated(rig), ROW7, "s3-resume-trace.md")))

    def test_refile_a_found_marker_with_two_stages_is_refused(self) -> None:
        rig, run_root = first_destination_chain(row7_stages("No checkpoint could be printed.\n"))
        rewrite_chain(run_root, marker="found", checkpoint_bytes=10, checkpoint_reason=None)
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, text)
        self.assertFalse(os.path.lexists(self.dated(rig)), "nothing was filed")

    def test_refile_the_none_marker_with_three_stages_is_refused(self) -> None:
        rig, run_root = first_destination_chain(row7_stages())
        rewrite_chain(run_root, marker="NO-PRINTED-CHECKPOINT", checkpoint_bytes=0, checkpoint_reason="none")
        code, text = self.refile(rig, run_root)
        self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, text)
        self.assertFalse(os.path.lexists(self.dated(rig)))

    def test_refile_the_resume_line_marker_word_is_not_a_shape_of_this_row_and_nothing_else_is_either(self) -> None:
        for marker in ("NO-RESUME-LINE", "", None, "other", 7):
            rig, run_root = first_destination_chain(row7_stages("No checkpoint could be printed.\n"))
            rewrite_chain(run_root, marker=marker)
            code, text = self.refile(rig, run_root)
            self.assertEqual(code, pc_exitcodes.PREFLIGHT_FAIL, "%r %s" % (marker, text))
            self.assertFalse(os.path.lexists(self.dated(rig)))

    def test_refile_a_chain_record_of_the_wrong_shape_is_refused(self) -> None:
        rig, run_root = first_destination_chain(row7_stages())
        with open(os.path.join(run_root, "raw", "chain.json"), "w", encoding="utf-8") as handle:
            handle.write("[]")
        code, text = self.refile(rig, run_root)
        self.assertNotEqual(code, 0, text)
        self.assertFalse(os.path.lexists(self.dated(rig)))

    def test_refile_the_resume_line_rows_keep_their_own_two_shapes_and_refuse_the_new_marker(self) -> None:
        pc_evidence = evidence()
        spec = spec_of("row1-wrong-binding")
        self.assertEqual(spec.chain, rows().CHAIN_RESUME_LINE)
        data = pc_evidence.RunData({}, {"marker": "NO-PRINTED-CHECKPOINT"}, [], {})
        self.assertEqual(pc_evidence._chain_incomplete(data, spec), pc_evidence.MESSAGE_STAGE_MISSING)
        data = pc_evidence.RunData({}, {"marker": "NO-RESUME-LINE"}, [], {})
        self.assertEqual(pc_evidence._chain_incomplete(data, spec_of(ROW7)), pc_evidence.MESSAGE_STAGE_MISSING)


# ---------------------------------------------------------------------------------------------
# The restriction and its restore on every exit path
# ---------------------------------------------------------------------------------------------


class Row7RestoreTests(unittest.TestCase):
    def test_restore_a_stop_in_s3_files_a_label_and_restores_the_project(self) -> None:
        chain = Row7Run(pc_testutil.stages_with(row7_stages(), 2, exit=1))
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, chain.lines())
        self.assertEqual(os.listdir(chain.ctx.destination), ["STOPPED-" + ROW7])
        self.assertEqual(chain.modes["s3"][0], 0o555, "s3 ran in the restricted project")
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)

    def test_restore_an_exception_in_s3_restores_the_project_and_goes_on(self) -> None:
        def boom(ctx, paths, spec):
            if spec.name == "s3":
                raise RuntimeError("a harness error in s3")

        chain = Row7Run(wrap=boom, raises=RuntimeError)
        self.assertIsNotNone(chain.error)
        self.assertEqual(chain.modes["s3"][0], 0o555)
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755, "restored on the exception path")
        self.assertEqual(len(chain.rig.calls()), 2)

    def test_restore_an_exception_in_s2_restores_the_project(self) -> None:
        def boom(ctx, paths, spec):
            if spec.name == "s2":
                raise RuntimeError("a harness error in s2")

        chain = Row7Run(wrap=boom, raises=RuntimeError)
        self.assertEqual(chain.modes["s2"][0], 0o555)
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)

    def test_restore_a_stop_in_s2_restores_the_project_and_files_a_label(self) -> None:
        chain = Row7Run(pc_testutil.stages_with(row7_stages(), 1, exit=1))
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, chain.lines())
        self.assertEqual(os.listdir(chain.ctx.destination), ["STOPPED-" + ROW7])
        self.assertEqual(chain.modes["s2"][0], 0o555)
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)

    def test_restore_a_stop_in_s1_never_applies_the_hook_and_leaves_the_project_as_seeded(self) -> None:
        chain = Row7Run(pc_testutil.stages_with(row7_stages(), 0, exit=1))
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, chain.lines())
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o700, "no restriction and no restore")
        self.assertFalse(os.path.lexists(os.path.join(chain.run_root, "snaps", RESTRICTION_SNAPSHOT)))
        self.assertEqual(sorted(chain.modes), ["s1"])

    def test_restore_a_write_outside_the_roots_in_s3_ends_the_row_with_11_and_restores_the_project(self) -> None:
        chain = Row7Run(pc_testutil.seed_outside_write(row7_stages(), 2))
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, chain.lines())
        self.assertEqual(os.listdir(chain.ctx.destination), ["STOPPED-" + ROW7])
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)
        snaps = os.path.join(chain.run_root, "snaps")
        found = checks().write_boundary(snaps, ["snap-2-after-preclear", "snap-3-after-resume"])
        self.assertEqual(found["paths"], ["outside.txt"])

    def test_restore_a_commit_in_s2_is_seen_against_the_restriction_state_and_the_project_is_restored(self) -> None:
        chain = Row7Run(pc_testutil.seed_git_commit(row7_stages(), 1))
        self.assertEqual(chain.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, chain.lines())
        states = checks().compute_facts(chain.run_root, chain.ctx.config_dir)["git"]["states"]
        self.assertEqual(states[1]["head"], states[2]["head"], "no change in the hook window")
        self.assertNotEqual(states[2]["head"], states[3]["head"])
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)


class Row7CommandCountTests(unittest.TestCase):
    def test_commands_a_scripted_chmod_is_allowed_counted_and_the_row_is_still_filed(self) -> None:
        ops = [{"op": "tool", "name": "Bash", "input": {"command": "chmod 755 ."}, "content": ""}]
        chain = Row7Run(row7_stages(extra_s2_ops=ops))
        self.assertEqual(chain.outcome.code, 0, chain.lines())
        lines = chain.read("mechanical-checks.md").splitlines()
        self.assertIn("executed-chmod-commands: 1", lines)
        self.assertIn("executed-touch-commands: 0", lines)
        for call in chain.rig.calls():
            argv = call["args"]
            self.assertIn("Bash(chmod:*)", argv[argv.index("--allowedTools") + 1].split(","))
        self.assertEqual(mode_of(project_of(chain.run_root)), 0o755)

    def test_commands_a_denied_chmod_never_ran_and_is_not_counted(self) -> None:
        ops = [{"op": "tool", "name": "Bash", "input": {"command": "chmod 755 ."}, "denied": True}]
        chain = Row7Run(row7_stages(extra_s2_ops=ops))
        self.assertEqual(chain.outcome.code, 0, chain.lines())
        self.assertIn("executed-chmod-commands: 0", chain.read("mechanical-checks.md").splitlines())


# ---------------------------------------------------------------------------------------------
# Hook safety for the project folder (T-04-23, T-04-24)
# ---------------------------------------------------------------------------------------------


def fake_run_root():
    """A run root shaped like a real one: a folder holding project/thoughts/plans and a raw folder."""
    base = os.path.realpath(tempfile.mkdtemp(prefix="pc-r7hook-"))
    run_root = os.path.join(base, "run")
    os.makedirs(os.path.join(run_root, "project", "thoughts", "plans"))
    os.makedirs(os.path.join(run_root, "raw"))
    paths = {"run_root": run_root, "raw": os.path.join(run_root, "raw"), "snaps": os.path.join(run_root, "snaps")}
    return paths, base


class Row7HookSafetyTests(unittest.TestCase):
    def test_hook_the_restriction_changes_the_project_folder_only_and_the_restore_returns_it(self) -> None:
        hooks = rowhooks()
        paths, _base = fake_run_root()
        run_root = paths["run_root"]
        plan = os.path.join(plans_of(run_root), "p.md")
        with open(plan, "w", encoding="utf-8") as handle:
            handle.write("plan\n")
        os.chmod(plan, 0o644)
        before = (mode_of(plans_of(run_root)), mode_of(plan), mode_of(paths["raw"]), mode_of(run_root))
        hooks.restrict_project_555(None, paths, None)
        self.assertEqual(mode_of(project_of(run_root)), 0o555)
        self.assertEqual((mode_of(plans_of(run_root)), mode_of(plan), mode_of(paths["raw"]), mode_of(run_root)), before)
        with self.assertRaises(PermissionError):
            os.mkdir(os.path.join(project_of(run_root), ".preclear"))
        with open(plan, "a", encoding="utf-8") as handle:
            handle.write("existing files stay writable\n")
        hooks.restore_project_755(None, paths, None)
        self.assertEqual(mode_of(project_of(run_root)), 0o755)
        self.assertEqual(mode_of(plans_of(run_root)), before[0])

    def test_hook_perms_text_lists_the_project_as_a_dot_and_the_plans_folder_mode_only(self) -> None:
        hooks = rowhooks()
        paths, _base = fake_run_root()
        hooks.restrict_project_555(None, paths, None)
        try:
            text = hooks.perms_text(paths, hooks.TARGETS["restrict-project-555"]).decode("ascii")
        finally:
            hooks.restore_project_755(None, paths, None)
        self.assertEqual(text, ". 555\nthoughts/plans %03o\n" % mode_of(plans_of(paths["run_root"])))

    def test_hook_a_project_folder_that_is_a_link_is_refused_and_nothing_outside_changes(self) -> None:
        hooks = rowhooks()
        paths, base = fake_run_root()
        run_root = paths["run_root"]
        outside = os.path.join(base, "outside")
        os.makedirs(os.path.join(outside, "thoughts", "plans"))
        os.chmod(outside, 0o700)
        os.rename(project_of(run_root), os.path.join(run_root, "moved"))
        os.symlink(outside, project_of(run_root))
        for call in (hooks.restrict_project_555, hooks.restore_project_755):
            with self.assertRaises(hooks.HookRefused):
                call(None, paths, None)
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text(paths, hooks.TARGETS["restrict-project-555"])
        self.assertEqual(mode_of(outside), 0o700)

    def test_hook_a_plans_folder_that_is_a_link_is_refused_by_perms_and_not_changed(self) -> None:
        hooks = rowhooks()
        paths, base = fake_run_root()
        outside = os.path.join(base, "outside")
        os.makedirs(outside)
        os.chmod(outside, 0o700)
        os.rename(plans_of(paths["run_root"]), os.path.join(base, "plans-moved"))
        os.symlink(outside, plans_of(paths["run_root"]))
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text(paths, hooks.TARGETS["restrict-project-555"])
        self.assertEqual(mode_of(outside), 0o700)

    def test_hook_a_thoughts_folder_that_is_a_link_is_refused_by_perms(self) -> None:
        hooks = rowhooks()
        paths, base = fake_run_root()
        thoughts = os.path.join(project_of(paths["run_root"]), "thoughts")
        outside = os.path.join(base, "outside-thoughts")
        os.makedirs(os.path.join(outside, "plans"))
        os.rename(thoughts, os.path.join(base, "thoughts-moved"))
        os.symlink(outside, thoughts)
        with self.assertRaises(hooks.HookRefused):
            hooks.perms_text(paths, hooks.TARGETS["restrict-project-555"])

    def test_hook_the_project_entry_is_a_folder_entry_only_and_the_table_parts_stay_checked(self) -> None:
        hooks = rowhooks()
        paths, _base = fake_run_root()
        for relative, kind in (
            (".", "file"), ("..", "dir"), ("", "dir"), ("./x", "dir"), ("thoughts/../plans", "dir"),
            ("thoughts//plans", "dir"), (".", "other"),
        ):
            with self.assertRaises(hooks.HookRefused, msg=repr((relative, kind))):
                hooks._open_target(paths, relative, kind)
        descriptor = hooks._open_target(paths, ".", "dir")
        try:
            self.assertEqual(os.fstat(descriptor).st_ino, os.stat(project_of(paths["run_root"])).st_ino)
        finally:
            os.close(descriptor)

    def test_hook_a_project_folder_of_another_owner_is_refused(self) -> None:
        hooks = rowhooks()
        paths, _base = fake_run_root()
        before = mode_of(project_of(paths["run_root"]))
        with mock.patch.object(hooks.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaises(hooks.HookRefused):
                hooks._open_target(paths, ".", "dir")
        self.assertEqual(mode_of(project_of(paths["run_root"])), before)

    def test_hook_a_swapped_project_folder_in_s2_never_lets_the_restore_follow_the_planted_link(self) -> None:
        import pc_manifest

        ops = [
            {"op": "rename", "path": "$RUN/project", "to": "$RUN/project-moved"},
            {"op": "symlink", "path": "$RUN/project", "target": "$OUTSIDE"},
        ]
        chain = Row7Run(
            row7_stages(extra_s2_ops=ops),
            prepare=lambda rig: os.chmod(rig.outside, 0o700),
            raises=pc_manifest.ManifestError,
        )
        # The engine cannot read its own project snapshot through the link: the row ends on an exception (nothing is
        # filed), the restore on that path is refused because the project is now a link, and nothing outside changed.
        self.assertIsNotNone(chain.error)
        self.assertEqual(mode_of(chain.rig.outside), 0o700, "the finalizer never followed the planted link")
        self.assertEqual(os.listdir(chain.rig.outside), [])
        self.assertFalse(os.path.lexists(chain.ctx.destination), "nothing was filed")
        self.assertEqual(mode_of(os.path.join(chain.run_root, "project-moved")), 0o555, "left restricted, inside the run root")


# ---------------------------------------------------------------------------------------------
# The scripted op that stands in for a model write into a folder that may be restricted
# ---------------------------------------------------------------------------------------------


class TryWriteOpTests(unittest.TestCase):
    def test_try_write_in_a_writable_project_creates_the_file_and_the_tool_result_is_accepted(self) -> None:
        spec = spec_of("row6-readonly-plan")
        stages = pc_testutil.default_row_stages(spec)
        stages[1]["ops"] = list(stages[1]["ops"]) + [
            {"op": "try_write", "path": "$PROJECT/note.txt", "text": "a note\n"}
        ]
        run = Registered("row6-readonly-plan", stages=stages)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        # The row 6 hook leaves the project folder itself writable, so the create succeeds.
        self.assertEqual(read_text(os.path.join(run.run_root, "project", "note.txt")), "a note\n")
        events = [json.loads(line) for line in read_text(run.raw("s2.stdout")).splitlines() if line.strip()]
        results = []
        for event in events:
            message = event.get("message")
            if event.get("type") == "user" and isinstance(message, dict):
                results.extend(item for item in message.get("content", []) if item.get("type") == "tool_result")
        self.assertEqual([item["is_error"] for item in results if "created" in str(item["content"])], [False])

    def test_try_write_never_overwrites_an_existing_file_and_the_op_is_documented(self) -> None:
        text = read_text(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_testutil.py"))
        self.assertIn("#   try_write path, text:", text)
        self.assertIn("os.O_CREAT | os.O_EXCL", text.split("def do_try_write", 1)[1].split("def do_git", 1)[0])

    def test_the_default_stages_of_row_7_print_a_checkpoint_the_extractor_finds_and_write_nothing_under_the_project(self) -> None:
        stages = pc_testutil.default_row_stages(spec_of(ROW7))
        self.assertEqual(len(stages), 3)
        found = row1().extract_printed_checkpoint(stages[1]["result"]["text"])
        for heading in NEEDED:
            self.assertIn(heading, found.splitlines())
        self.assertEqual([op["op"] for op in stages[1]["ops"]], ["tool", "try_write", "text"])
        self.assertEqual(stages[1], pc_testutil.printed_checkpoint_stage())
        for other in ("row1-wrong-binding", "row6-readonly-plan"):
            self.assertNotIn("try_write", json.dumps(pc_testutil.default_row_stages(spec_of(other))))


if __name__ == "__main__":
    unittest.main()
