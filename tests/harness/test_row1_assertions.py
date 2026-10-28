"""Zero-token tests for the init manifest and instruction-audit assertions of a row run (plan 03-02 Task 3).

HARN-07: the init manifest (permission mode, model, skills, memory paths, cwd, session ids) and the
instruction audit are asserted after every stage, each assertion has a failing variant, and the
isolation mode is recorded from the pinned claim. No test starts a real claude; the only claude executed
is the scripted fake of pc_testutil. Synthetic events are copies of the shape of the committed init
manifest with path values taken from a temporary world. pc_row1 is imported inside each test.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import tempfile
import unittest
import uuid
from unittest import mock

import pc_flags
import pc_exitcodes
import pc_spend
import pc_testutil

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HARNESS_DIR))
ROW1 = "row1-wrong-binding"
EXPECTED_IDS = (
    "permission-mode-default",
    "model-pinned",
    "skill-preclear-present",
    "mcp-servers-empty",
    "no-non-builtin-plugins",
    "user-names-absent",
    "no-user-instruction-outside-config",
    "project-claude-md-loaded",
    "project-local-inside-run-root",
    "memory-path-as-set",
    "cwd-is-project",
    "session-id-as-requested",
)
HOOK_IDS = EXPECTED_IDS[6:9]
USER_NAME = "zz-user-skill"


def row1():
    import pc_row1

    return pc_row1


def rows():
    import pc_rows

    return pc_rows


def matrix():
    import pc_matrix

    return pc_matrix


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.loads(handle.read())


class World(object):
    """Folders for synthetic events: a run root with a project and an auto-memory folder, a config folder."""

    def __init__(self) -> None:
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="pc-assert-"))
        self.run_root = os.path.join(self.base, "run")
        self.project = os.path.join(self.run_root, "project")
        self.auto_memory = os.path.join(self.run_root, "auto-memory")
        self.config = os.path.join(self.base, "config")
        self.outside = os.path.join(self.base, "outside")
        for folder in (self.project, self.auto_memory, self.config, self.outside):
            os.makedirs(folder)
        self.paths = {"run_root": self.run_root, "project": self.project, "auto_memory": self.auto_memory}
        self.session = str(uuid.uuid4())

    def init(self, **changes):
        event = {
            "type": "system",
            "subtype": "init",
            "session_id": self.session,
            "cwd": self.project,
            "tools": ["Bash", "Read"],
            "mcp_servers": [],
            "model": pc_flags.PINNED_MODEL,
            "permissionMode": "default",
            "slash_commands": ["preclear"],
            "skills": ["preclear", "update-config"],
            "plugins": [
                {"name": "cc-plugin-agents-md", "path": "builtin", "source": "cc-plugin-agents-md@builtin"},
                {"name": "cc-plugin-telemetry", "path": "builtin", "source": "cc-plugin-telemetry@builtin"},
            ],
            "agents": ["general-purpose"],
            "apiKeySource": "none",
            "memory_paths": {"auto": self.auto_memory + "/"},
        }
        for key, value in changes.items():
            if value == "$DELETE":
                event.pop(key, None)
            else:
                event[key] = value
        return event

    def result(self, **changes):
        event = {"type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
                 "session_id": self.session, "total_cost_usd": 0.01, "permission_denials": [],
                 "terminal_reason": "completed"}
        event.update(changes)
        return event

    def events(self, init=None, result=None):
        return [init if init is not None else self.init(), result if result is not None else self.result()]

    def entries(self, *extra):
        base = [{"file_path": os.path.join(self.project, "CLAUDE.md"), "memory_type": "Project", "load_reason": "session_start"}]
        return base + list(extra)

    def user_entry(self, inside=True):
        folder = self.config if inside else self.outside
        return {"file_path": os.path.join(folder, "CLAUDE.md"), "memory_type": "User", "load_reason": "session_start"}

    def assertions(self, events=None, entries=None, kind="fresh", user_names=frozenset(), defined=frozenset()):
        return row1().stage_assertions(
            events if events is not None else self.events(),
            self.entries() if entries is None else entries,
            self.paths,
            self.session,
            kind,
            user_names,
            defined,
            self.config,
        )


def failed(triples):
    return [name for name, _how, ok in triples if not ok]


class InitAssertionTests(unittest.TestCase):
    def test_twelve_assertions_come_back_in_the_declared_order_and_all_pass_on_a_clean_stage(self) -> None:
        world = World()
        triples = world.assertions()
        self.assertEqual(tuple(name for name, _how, _ok in triples), EXPECTED_IDS)
        self.assertEqual(tuple(row1().ROW_ASSERTION_IDS), EXPECTED_IDS)
        self.assertEqual(failed(triples), [])
        hows = dict((name, how) for name, how, _ok in triples)
        for name in EXPECTED_IDS[:6] + EXPECTED_IDS[9:]:
            self.assertEqual(hows[name], "init", name)
        for name in HOOK_IDS:
            self.assertEqual(hows[name], "hook", name)

    def test_each_variant_fails_exactly_its_own_assertion(self) -> None:
        world = World()
        other = os.path.join(world.base, "elsewhere")
        os.makedirs(other)
        other_session = str(uuid.uuid4())
        variants = [
            ("permission-mode-default", dict(events=world.events(init=world.init(permissionMode="acceptEdits")))),
            ("model-pinned", dict(events=world.events(init=world.init(model="some-other-model")))),
            ("skill-preclear-present", dict(events=world.events(init=world.init(skills=["update-config"])))),
            ("mcp-servers-empty", dict(events=world.events(init=world.init(mcp_servers=[{"name": "extra"}])))),
            (
                "no-non-builtin-plugins",
                dict(events=world.events(init=world.init(plugins=[{"name": "p", "path": "x", "source": "p@market"}]))),
            ),
            (
                "user-names-absent",
                dict(
                    events=world.events(init=world.init(skills=["preclear", USER_NAME])),
                    user_names=frozenset([USER_NAME]),
                ),
            ),
            ("no-user-instruction-outside-config", dict(entries=world.entries(world.user_entry(inside=False)))),
            ("project-claude-md-loaded", dict(entries=[world.user_entry(inside=True)])),
            (
                "project-local-inside-run-root",
                dict(entries=world.entries({"file_path": os.path.join(other, "CLAUDE.md"), "memory_type": "Project",
                                            "load_reason": "session_start"})),
            ),
            ("memory-path-as-set", dict(events=world.events(init=world.init(memory_paths={"auto": other + "/"})))),
            ("cwd-is-project", dict(events=world.events(init=world.init(cwd=other)))),
            ("session-id-as-requested", dict(events=world.events(init=world.init(session_id=other_session)))),
            ("session-id-as-requested", dict(events=world.events(result=world.result(session_id=other_session)))),
        ]
        for expected, kwargs in variants:
            self.assertEqual(failed(world.assertions(**kwargs)), [expected], "variant for " + expected)

    def test_absent_or_empty_init_keys_are_failures_never_vacuous_passes(self) -> None:
        world = World()
        cases = [
            ("memory-path-as-set", world.init(memory_paths="$DELETE")),
            ("memory-path-as-set", world.init(memory_paths="a plain string")),
            ("memory-path-as-set", world.init(memory_paths={})),
            ("memory-path-as-set", world.init(memory_paths={"auto": ""})),
            ("memory-path-as-set", world.init(memory_paths={"auto": "/"})),
            ("memory-path-as-set", world.init(memory_paths={"auto": 7})),
            ("memory-path-as-set", world.init(memory_paths={"auto": "relative/auto-memory"})),
            ("skill-preclear-present", world.init(skills=[])),
            ("skill-preclear-present", world.init(skills="$DELETE")),
            ("cwd-is-project", world.init(cwd="$DELETE")),
            ("cwd-is-project", world.init(cwd="")),
            ("session-id-as-requested", world.init(session_id="$DELETE")),
        ]
        for expected, init in cases:
            triples = world.assertions(events=world.events(init=init))
            self.assertIn(expected, failed(triples), "an absent or empty key passed: " + expected)

    def test_the_memory_path_compares_by_realpath_with_a_trailing_slash_tolerated(self) -> None:
        world = World()
        for value in (world.auto_memory, world.auto_memory + "/"):
            triples = world.assertions(events=world.events(init=world.init(memory_paths={"auto": value})))
            self.assertEqual(failed(triples), [])
        sibling = world.auto_memory + "-extra"
        os.makedirs(sibling)
        triples = world.assertions(events=world.events(init=world.init(memory_paths={"auto": sibling + "/"})))
        self.assertEqual(failed(triples), ["memory-path-as-set"])
        link = os.path.join(world.base, "link-to-memory")
        os.symlink(world.auto_memory, link)
        triples = world.assertions(events=world.events(init=world.init(memory_paths={"auto": link + "/"})))
        self.assertEqual(failed(triples), [])


class HookAuditTests(unittest.TestCase):
    def test_a_fresh_stage_with_no_instruction_entry_is_not_assertable_and_stops(self) -> None:
        world = World()
        triples = world.assertions(entries=[], kind="fresh")
        hows = dict((name, (how, ok)) for name, how, ok in triples)
        for name in HOOK_IDS:
            self.assertEqual(hows[name], ("not-assertable", False), name)
        evaluation = row1().evaluate_stage(
            world.events(), [], world.paths, world.session, "fresh", frozenset(), row1().BinaryScan("unused"), world.config
        )
        self.assertEqual(evaluation.status, "stop")
        self.assertIn("instruction", evaluation.reason)

    def test_a_resumed_stage_with_no_new_entry_is_recorded_as_not_asserted_and_passes(self) -> None:
        world = World()
        triples = world.assertions(entries=[], kind="resume")
        hows = dict((name, (how, ok)) for name, how, ok in triples)
        for name in HOOK_IDS:
            self.assertEqual(hows[name], ("not-asserted-on-resume", True), name)
        evaluation = row1().evaluate_stage(
            world.events(), [], world.paths, world.session, "resume", frozenset(), row1().BinaryScan("unused"), world.config
        )
        self.assertEqual(evaluation.status, "pass")
        self.assertEqual(evaluation.counts["entries_project"], 0)
        self.assertEqual(evaluation.counts["entries_user"], 0)

    def test_a_boundary_violation_in_a_non_empty_slice_fails_in_both_kinds(self) -> None:
        world = World()
        for kind in ("fresh", "resume"):
            outside_user = world.entries(world.user_entry(inside=False))
            self.assertEqual(failed(world.assertions(entries=outside_user, kind=kind)), ["no-user-instruction-outside-config"])
            outside_project = world.entries(
                {"file_path": os.path.join(world.outside, "CLAUDE.md"), "memory_type": "Project", "load_reason": "x"}
            )
            self.assertEqual(failed(world.assertions(entries=outside_project, kind=kind)), ["project-local-inside-run-root"])

    def test_a_fresh_stage_with_a_valid_slice_passes_and_counts_the_entries(self) -> None:
        world = World()
        entries = world.entries(world.user_entry(inside=True))
        evaluation = row1().evaluate_stage(
            world.events(), entries, world.paths, world.session, "fresh", frozenset(), row1().BinaryScan("unused"), world.config
        )
        self.assertEqual(evaluation.status, "pass")
        self.assertEqual(evaluation.counts["entries_project"], 1)
        self.assertEqual(evaluation.counts["entries_user"], 1)
        self.assertEqual(evaluation.counts["audit_source"], "logger")

    def test_evaluate_stage_stops_on_any_false_triple_on_either_kind(self) -> None:
        world = World()
        events = world.events(init=world.init(model="some-other-model"))
        for kind in ("fresh", "resume"):
            evaluation = row1().evaluate_stage(
                events, world.entries(), world.paths, world.session, kind, frozenset(), row1().BinaryScan("unused"), world.config
            )
            self.assertEqual(evaluation.status, "stop")
            self.assertIn("model-pinned", evaluation.reason)

    def test_the_printed_lines_hold_ids_yes_or_no_and_counts_only(self) -> None:
        world = World()
        events = world.events(init=world.init(skills=["preclear", USER_NAME]))
        evaluation = row1().evaluate_stage(
            events,
            world.entries(world.user_entry(inside=True)),
            world.paths,
            world.session,
            "fresh",
            frozenset([USER_NAME]),
            row1().BinaryScan("unused", lookup=lambda path, names: frozenset()),
            world.config,
        )
        lines = row1().describe_evaluation("s1", evaluation)
        text = "\n".join(lines)
        self.assertIn("assertion user-names-absent: no", text)
        self.assertIn("assertion model-pinned: yes", text)
        for forbidden in (USER_NAME, world.base, world.config, world.session):
            self.assertNotIn(forbidden, text)
        for line in lines:
            self.assertRegex(line, r"^[A-Za-z0-9 :=,()_.-]+$")


class BinaryScanTests(unittest.TestCase):
    def evaluate(self, world, scan, names):
        events = world.events(init=world.init(skills=["preclear"] + sorted(names)))
        return row1().evaluate_stage(
            events, world.entries(), world.paths, world.session, "fresh", frozenset(names), scan, world.config
        )

    def test_the_binary_is_read_only_when_there_are_candidate_hits_and_the_answer_is_cached(self) -> None:
        import pc_spike

        world = World()
        with mock.patch.object(pc_spike, "binary_defines", return_value=frozenset()) as counting:
            scan = row1().BinaryScan("claude-path-stand-in")
            clean = self.evaluate(world, scan, [])
            self.assertEqual(clean.status, "pass")
            self.assertEqual(counting.call_count, 0)
            hit = self.evaluate(world, scan, [USER_NAME])
            self.assertEqual(counting.call_count, 1)
            self.assertEqual(hit.status, "stop")
            self.assertEqual(hit.counts["user_name_hits"], 1)
            self.evaluate(world, scan, [USER_NAME])
            self.assertEqual(counting.call_count, 1)

    def test_a_name_the_binary_defines_is_a_collision_and_not_a_leak(self) -> None:
        import pc_spike

        world = World()
        with mock.patch.object(pc_spike, "binary_defines", return_value=frozenset([USER_NAME])) as counting:
            evaluation = self.evaluate(world, row1().BinaryScan("claude-path-stand-in"), [USER_NAME])
            self.assertEqual(counting.call_count, 1)
        self.assertEqual(evaluation.status, "pass")
        self.assertEqual(evaluation.counts["user_name_hits"], 0)
        self.assertEqual(evaluation.counts["user_name_collisions"], 1)


class ChainAssertionTests(unittest.TestCase):
    def run_chain(self, stages, **kwargs):
        rig = pc_testutil.RowRig(stages=stages)
        for name in kwargs.get("user_skills", ()):
            os.makedirs(os.path.join(rig.user_home, ".claude", "skills", name))
        ctx = rig.context()
        return rig, ctx, row1().run_row(ctx)

    def raw(self, ctx, name):
        run_root = os.path.join(ctx.runs_root, os.listdir(ctx.runs_root)[0])
        return os.path.join(run_root, "raw", name)

    def test_the_default_script_completes_and_each_record_carries_the_triples_and_entry_counts(self) -> None:
        rig, ctx, outcome = self.run_chain(pc_testutil.default_row1_stages())
        self.assertEqual(outcome.code, 0, "\n".join(outcome.lines))
        records = [read_json(self.raw(ctx, "s%d.record.json" % n)) for n in (1, 2, 3)]
        for record in records:
            self.assertEqual([entry[0] for entry in record["assertions"]], list(EXPECTED_IDS))
            self.assertEqual(record["evaluation"], "pass")
            self.assertEqual(sorted(record["hook_entries"]),
                             ["local", "managed", "project", "unknown", "user"])
        self.assertEqual([r["hook_entries"]["project"] for r in records], [1, 0, 1])
        self.assertEqual([r["hooklog_lines"] for r in records], [1, 1, 2])
        hows = dict((entry[0], entry[1]) for entry in records[1]["assertions"])
        for name in HOOK_IDS:
            self.assertEqual(hows[name], "not-asserted-on-resume")
        hows = dict((entry[0], entry[1]) for entry in records[0]["assertions"])
        for name in HOOK_IDS:
            self.assertEqual(hows[name], "hook")
        run = read_json(self.raw(ctx, "run.json"))
        self.assertEqual(run["isolation"], "strict")

    def test_the_isolation_mode_is_the_first_word_after_the_claim_prefix(self) -> None:
        claim = pc_flags.ISOLATION_CLAIM
        prefix = "Isolation claim: "
        self.assertTrue(claim.startswith(prefix))
        expected = re.match(r"[A-Za-z]+", claim[len(prefix):]).group(0)
        self.assertEqual(row1().isolation_mode(), expected)
        self.assertEqual(expected, "strict")

    def test_a_failed_assertion_stops_the_chain_with_11_and_no_later_launch(self) -> None:
        stages = pc_testutil.stages_with(pc_testutil.default_row1_stages(), 0, init={"model": "some-other-model"})
        rig, ctx, outcome = self.run_chain(stages)
        self.assertEqual(outcome.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertEqual(len(rig.calls()), 1)
        self.assertEqual([r["kind"] for r in pc_spend.read_records(ctx.harness_home)], ["launch", "settle"])
        text = "\n".join(outcome.lines)
        self.assertIn("model-pinned", text)
        self.assertNotIn(rig.base, text)
        record = read_json(self.raw(ctx, "s1.record.json"))
        self.assertEqual(record["evaluation"], "stop")

    def test_a_fresh_stage_without_instruction_entries_stops_the_chain(self) -> None:
        stages = pc_testutil.default_row1_stages()
        stages[0]["ops"] = [op for op in stages[0]["ops"] if op["op"] != "hook"]
        rig, ctx, outcome = self.run_chain(stages)
        self.assertEqual(outcome.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertEqual(len(rig.calls()), 1)

    def test_a_resumed_stage_without_entries_does_not_stop_the_chain(self) -> None:
        rig, ctx, outcome = self.run_chain(pc_testutil.default_row1_stages())
        self.assertEqual(outcome.code, 0)
        self.assertEqual(len(rig.calls()), 3)

    def test_a_user_name_hit_stops_the_chain_and_the_binary_is_read_once(self) -> None:
        import pc_spike

        stages = pc_testutil.default_row1_stages()
        for stage in stages:
            stage["init"] = {"skills": ["preclear", USER_NAME]}
        with mock.patch.object(pc_spike, "binary_defines", return_value=frozenset()) as counting:
            rig, ctx, outcome = self.run_chain(stages, user_skills=[USER_NAME])
        self.assertEqual(outcome.code, pc_exitcodes.PREFLIGHT_FAIL)
        self.assertEqual(counting.call_count, 1)
        self.assertNotIn(USER_NAME, "\n".join(outcome.lines))

    def test_a_clean_run_never_reads_the_binary(self) -> None:
        import pc_spike

        with mock.patch.object(pc_spike, "binary_defines", return_value=frozenset()) as counting:
            rig, ctx, outcome = self.run_chain(pc_testutil.default_row1_stages())
        self.assertEqual(outcome.code, 0)
        self.assertEqual(counting.call_count, 0)

    def test_the_registry_sources_name_the_two_data_files_and_the_real_dry_run_still_passes(self) -> None:
        entry = rows().find_entry(rows().build_registry(), "row", ROW1)
        sources = [path for path, _kind in entry.sources]
        self.assertIn("tests/harness/data/row1-s1-prompt.md", sources)
        self.assertIn("tests/harness/data/row1-plan.md", sources)
        scratch = os.path.realpath(tempfile.mkdtemp(prefix="pc-dry-"))
        env = {
            "PATH": os.pathsep.join(pc_testutil.SYSTEM_DIRS),
            "HOME": os.path.join(scratch, "home"),
            "LANG": "en_US.UTF-8",
            "PRECLEAR_RUNS_ROOT": os.path.join(scratch, "runs"),
            "PRECLEAR_HARNESS_HOME": os.path.join(scratch, "hh"),
        }
        os.makedirs(env["PRECLEAR_RUNS_ROOT"])
        out = io.StringIO()
        err = io.StringIO()
        code = matrix().main(
            ["--dry-run", "--row", ROW1, "--budget", "2.00"],
            env=env,
            repo_root=ROOT,
            clock=lambda: datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc),
            out=out,
            err=err,
        )
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        self.assertIn("3 stages, 2 sessions", out.getvalue())


if __name__ == "__main__":
    unittest.main()
