"""Zero-token checks of the committed spike captures (plan 02-08, task 4; HARN-04, HARN-06).

This module reads only committed files under tests/harness/data and the pc_ modules. It never
starts claude and never reads a harness home, a credential or a Claude folder. It keeps four
things honest against the real captures:

  * the real streams parse with pc_stream (one init and one result each) and the version they ran
    against is the tested version (T-02-35);
  * the seven-command probe labels replay against the allowlist model and the structured denial
    detector, and every disagreement is flagged in the labels and named in the findings;
  * the init manifest still holds the frozen S1 baseline (the nine assertions, counts only);
  * the findings carry the lines the plan requires (spend, isolation claim and evidence, scratch
    login probe, version, session-id facts, the probe table), and every file the README lists as
    pending now exists.
"""
from __future__ import annotations

import decimal
import json
import os
import re
import unittest
from typing import Any, Dict, List

import pc_allowlist
import pc_flags
import pc_leakgate
import pc_spike
import pc_stream
import test_readme

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HARNESS_DIR, "data")
README = os.path.join(HARNESS_DIR, "README.md")

SYNTHETIC_WRAPPER = "/synthetic/wrapper/checkpoint"
SYNTHETIC_RUN = "/synthetic/run"


def read_bytes(name: str) -> bytes:
    with open(os.path.join(DATA, name), "rb") as handle:
        return handle.read()


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def events_of(name: str) -> List[Dict[str, Any]]:
    return pc_stream.parse_stream(read_bytes(name))


def labels() -> Dict[str, Any]:
    return json.loads(read_bytes("s2-probe-labels.json").decode("utf-8"))


def findings() -> str:
    return read_text(os.path.join(DATA, "spike-findings.md"))


def line_starting(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError("no line starts with %r" % prefix)


class StreamFixtureTests(unittest.TestCase):
    def test_each_stream_has_one_init_and_one_result_and_parses_strictly(self) -> None:
        for name in ("s2-stream.jsonl", "s2b-stream.jsonl"):
            events = events_of(name)
            init = pc_stream.init_manifest(events)
            summary = pc_stream.result_summary(events)
            self.assertEqual(init["permissionMode"], "default", name)
            self.assertEqual(init["model"], pc_flags.PINNED_MODEL, name)
            self.assertEqual(summary["subtype"], "success", name)
            self.assertIs(summary["is_error"], False, name)

    def test_the_version_in_every_capture_is_the_one_tested_version(self) -> None:
        versions = set()
        for name in ("s2-stream.jsonl", "s2b-stream.jsonl"):
            versions.add(pc_stream.init_manifest(events_of(name))["claude_code_version"])
        manifest = json.loads(read_bytes("s1-init-manifest.json").decode("utf-8"))
        versions.add(manifest["claude_code_version"])
        self.assertEqual(len(versions), 1, "the captures ran against different builds")
        self.assertEqual(tuple(versions), tuple(pc_flags.TESTED_VERSIONS))
        self.assertEqual(len(pc_flags.TESTED_VERSIONS), 1)

    def test_the_resume_turn_kept_the_session_and_each_call_reports_its_own_id(self) -> None:
        first = events_of("s2-stream.jsonl")
        second = events_of("s2b-stream.jsonl")
        sessions = set()
        for events in (first, second):
            init_id = pc_stream.init_manifest(events)["session_id"]
            result_id = pc_stream.result_summary(events)["session_id"]
            self.assertEqual(init_id, result_id)
            sessions.add(init_id)
        self.assertEqual(len(sessions), 1, "--resume did not continue the same session")

    def test_the_stream_carries_the_two_structured_denial_signals_for_the_bind_only(self) -> None:
        events = events_of("s2-stream.jsonl")
        report = pc_stream.denial_report(events)
        self.assertEqual(report.event_ids, report.result_ids)
        self.assertEqual(len(report.union), 1)
        self.assertEqual(report.tool_errors, frozenset())
        self.assertEqual(pc_stream.unexpected_denials(events, set(report.union)), [])

    def test_the_fixtures_hold_the_sanitised_tokens_and_no_raw_machine_path(self) -> None:
        text = read_bytes("s2-stream.jsonl").decode("utf-8")
        self.assertIn("<run>", text)
        self.assertIn("<helper>", text)
        self.assertIn("<auto-memory-root>", text)


class ProbeLabelTests(unittest.TestCase):
    def test_the_labels_keep_the_declared_order_and_the_expectations_written_before_the_run(self) -> None:
        rows = labels()["probes"]
        self.assertEqual([row["key"] for row in rows], [probe.key for probe in pc_spike.PROBE_COMMANDS])
        self.assertEqual([row["expected"] for row in rows], [probe.expected for probe in pc_spike.PROBE_COMMANDS])
        for row in rows:
            for key in ("command", "observed", "tool_use_id", "is_error", "permission_denied_event", "permission_denials_entry", "matcher", "heuristic", "outside_model"):
                self.assertIn(key, row)

    def test_the_labels_are_reproduced_from_the_committed_stream(self) -> None:
        events = events_of("s2-stream.jsonl")
        again = pc_spike.probe_rows(events, pc_spike.probe_commands("<helper>", "<run>"))
        for row, fresh in zip(labels()["probes"], again):
            for key in ("key", "command", "status", "tool_use_id", "is_error", "permission_denied_event", "permission_denials_entry", "observed"):
                self.assertEqual(row[key], fresh[key], "%s %s" % (row["key"], key))

    def test_the_denial_detector_and_the_labels_name_the_same_tool_use_ids(self) -> None:
        events = events_of("s2-stream.jsonl")
        report = pc_stream.denial_report(events)
        denied = set(row["tool_use_id"] for row in labels()["probes"] if row["observed"] == "denied")
        self.assertEqual(denied, set(report.union))
        self.assertEqual(report.event_ids, report.result_ids)

    def test_the_wrapper_bind_was_denied_live_which_is_the_first_layer_of_stub_06(self) -> None:
        bind = [row for row in labels()["probes"] if row["key"] == "wrapper-bind"][0]
        self.assertEqual(bind["observed"], "denied")
        self.assertIs(bind["permission_denied_event"], True)
        self.assertIs(bind["permission_denials_entry"], True)
        self.assertIs(bind["is_error"], True)

    def test_the_matcher_model_agrees_with_every_modelable_observed_outcome(self) -> None:
        rules = pc_flags.build_allowed_tools(SYNTHETIC_WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        for row in labels()["probes"]:
            command = row["command"].replace("<helper>", SYNTHETIC_WRAPPER).replace("<run>", SYNTHETIC_RUN)
            verdict = "allowed" if pc_allowlist.is_allowed(command, rules).allowed else "denied"
            self.assertEqual(verdict, row["matcher"], "%s: the stored matcher answer is stale" % row["key"])
            if row["outside_model"] or row["heuristic"]:
                self.assertNotEqual(verdict, row["observed"], "%s is flagged but the model agrees" % row["key"])
            else:
                self.assertEqual(verdict, row["observed"], "%s: unflagged disagreement" % row["key"])

    def test_every_flagged_row_is_named_in_the_findings_with_a_reason(self) -> None:
        text = findings()
        for row in labels()["probes"]:
            if row["outside_model"] or row["heuristic"]:
                self.assertIn(row["key"], text)
                self.assertTrue(row["outside_model_reason"] or row["heuristic"], row["key"])


class ManifestTests(unittest.TestCase):
    def manifest(self) -> Dict[str, Any]:
        return json.loads(read_bytes("s1-init-manifest.json").decode("utf-8"))

    def test_the_frozen_s1_baseline_holds_the_isolation_facts(self) -> None:
        m = self.manifest()
        self.assertEqual(m["permissionMode"], "default")
        self.assertEqual(m["model"], pc_flags.PINNED_MODEL)
        self.assertIn("preclear", m["skills"])
        self.assertEqual(m["mcp_servers"], [])
        self.assertTrue(all(item["source"].endswith("@builtin") for item in m["plugins"]))
        baseline = m["baseline"]
        self.assertEqual(sorted(baseline["assertions"]), sorted(pc_spike.S1_ASSERTION_IDS))
        self.assertTrue(set(baseline["assertions"].values()) <= {"init", "hook"})
        self.assertEqual(baseline["counts"]["user_name_hits"], 0)
        self.assertEqual(baseline["counts"]["entries_user"], 0)
        self.assertEqual(baseline["counts"]["entries_project"], 1)
        self.assertEqual(baseline["builtin_plugins"], sorted(item["source"] for item in m["plugins"]))

    def test_the_manifest_matches_the_stream_capture_on_the_pinned_facts(self) -> None:
        m = self.manifest()
        init = pc_stream.init_manifest(events_of("s2-stream.jsonl"))
        for key in ("permissionMode", "model", "apiKeySource", "claude_code_version"):
            self.assertEqual(m[key], init[key], key)
        self.assertEqual(m["skills"], init["skills"])


class FindingsTests(unittest.TestCase):
    def test_the_total_spend_line_is_two_decimals_and_at_most_the_cap(self) -> None:
        match = re.search(r"^Total spend: ([0-9]+[.][0-9]{2}) USD$", findings(), re.M)
        self.assertIsNotNone(match)
        self.assertLessEqual(decimal.Decimal(match.group(1)), decimal.Decimal("5.00"))

    def test_the_version_line_equals_the_tested_version(self) -> None:
        line = line_starting(findings(), "Claude Code version: ")
        self.assertEqual(line.split(": ", 1)[1].strip(), pc_flags.TESTED_VERSIONS[0])

    def test_the_isolation_claim_line_is_the_constant_and_the_readme_line(self) -> None:
        claim_line = line_starting(findings(), "Isolation claim:")
        self.assertEqual(claim_line, pc_flags.ISOLATION_CLAIM)
        self.assertEqual(line_starting(read_text(README), "Isolation claim:"), pc_flags.ISOLATION_CLAIM)

    def test_the_evidence_and_scratch_login_lines_are_present(self) -> None:
        text = findings()
        self.assertGreater(len(line_starting(text, "Isolation evidence: ")), len("Isolation evidence: "))
        self.assertGreater(len(line_starting(text, "Scratch login probe: ")), len("Scratch login probe: "))
        self.assertIn("One-time login", text)
        self.assertIn("by-construction", text)  # only to say that no such label is used

    def test_the_session_id_facts_for_both_calls_are_present(self) -> None:
        text = findings()
        for call in ("S2a", "S2b"):
            for field in ("init.session_id", "result.session_id"):
                line = line_starting(text, "%s %s equals the requested id: " % (call, field))
                self.assertTrue(line.endswith("yes"), line)

    def test_the_probe_table_matches_the_labels_row_for_row(self) -> None:
        text = findings()
        for row in labels()["probes"]:
            matches = [line for line in text.splitlines() if line.startswith("| `%s` |" % row["key"])]
            self.assertEqual(len(matches), 1, row["key"])
            cells = [cell.strip() for cell in matches[0].strip("|").split("|")]
            self.assertEqual(cells[2], row["expected"], row["key"])
            self.assertEqual(cells[3], row["observed"], row["key"])

    def test_the_verbose_probe_and_the_not_asserted_list_are_recorded(self) -> None:
        text = findings()
        self.assertIn("requires --verbose", text)
        self.assertIn("Not asserted", text)
        for name in ("env-prefixed", "python3 -c", "awk", "find"):
            self.assertIn(name, text)

    def test_no_findings_text_weakens_the_isolation_claim(self) -> None:
        text = findings().lower()
        self.assertNotIn("holds by construction", text)
        self.assertNotIn("isolation holds only", text)


class HygieneTests(unittest.TestCase):
    def test_every_committed_data_file_passes_the_python_leak_gate_with_no_findings(self) -> None:
        report = pc_leakgate.scan_tree(DATA, [])
        self.assertEqual(report.findings, [])
        self.assertGreaterEqual(report.files, 6)

    def test_every_file_the_readme_lists_as_pending_now_exists(self) -> None:
        for name in test_readme.PENDING_SPIKE_FILES:
            self.assertTrue(os.path.isfile(os.path.join(HARNESS_DIR, name)), name)

    def test_no_data_file_names_a_user_skill_or_a_home_path(self) -> None:
        for name in os.listdir(DATA):
            text = read_bytes(name).decode("utf-8")
            self.assertNotRegex(text, r"/(?:Users|home)/[A-Za-z0-9._-]+")


if __name__ == "__main__":
    unittest.main()
