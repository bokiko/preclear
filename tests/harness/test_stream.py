"""Tests for pc_stream: the strict stream-json parser and structured denial detection (HARN-06).

Streams are synthetic: Python dicts serialised to bytes. No test runs claude, and no string
here is shaped like a path, address or credential.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from typing import Any, Dict, List

import pc_exitcodes
import pc_stream

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
STREAM_SCRIPT = os.path.join(HARNESS_DIR, "pc_stream.py")
MISSING = "<missing-id>"


def init_event(**extra: Any) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "type": "system",
        "subtype": "init",
        "session_id": "11111111-2222-4333-8444-555555555555",
        "claude_code_version": "2.1.310",
        "cwd": "/work/run",
        "tools": ["Bash", "Read"],
        "mcp_servers": [],
        "model": "claude-sonnet-5-5",
        "permissionMode": "default",
        "slash_commands": [],
        "skills": [],
        "plugins": [],
        "apiKeySource": "none",
    }
    event.update(extra)
    return event


def tool_use(tool_id: Any, name: str = "Bash", **tool_input: Any) -> Dict[str, Any]:
    block: Dict[str, Any] = {"type": "tool_use", "name": name, "input": tool_input}
    if tool_id is not None:
        block["id"] = tool_id
    return {"type": "assistant", "message": {"role": "assistant", "content": [block]}}


def tool_result(tool_id: str, content: Any = "ok", is_error: bool = False) -> Dict[str, Any]:
    block = {"type": "tool_result", "tool_use_id": tool_id, "content": content, "is_error": is_error}
    return {"type": "user", "message": {"role": "user", "content": [block]}}


def denied_event(tool_id: Any = "t1") -> Dict[str, Any]:
    event: Dict[str, Any] = {"type": "system", "subtype": "permission_denied", "tool_name": "Bash"}
    if tool_id is not None:
        event["tool_use_id"] = tool_id
    return event


def result_event(denials: Any = None, **extra: Any) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 2,
        "session_id": "11111111-2222-4333-8444-555555555555",
    }
    if denials is not None:
        event["permission_denials"] = denials
    event.update(extra)
    return event


def encode(events: List[Dict[str, Any]]) -> bytes:
    return b"\n".join(json.dumps(e, ensure_ascii=False).encode("utf-8") for e in events) + b"\n"


def good_stream() -> bytes:
    return encode(
        [
            init_event(),
            tool_use("t1", command="ls"),
            tool_result("t1"),
            result_event(),
        ]
    )


class ParseTests(unittest.TestCase):
    def test_well_formed_stream_parses_and_manifest_has_every_key(self) -> None:
        events = pc_stream.parse_stream(good_stream())
        self.assertEqual([e["type"] for e in events], ["system", "assistant", "user", "result"])
        manifest = pc_stream.init_manifest(events)
        expected_keys = {
            "session_id",
            "claude_code_version",
            "cwd",
            "tools",
            "mcp_servers",
            "model",
            "permissionMode",
            "slash_commands",
            "skills",
            "plugins",
            "agents",
            "apiKeySource",
            "memory_paths",
            "effort",
        }
        self.assertEqual(set(manifest), expected_keys)
        self.assertEqual(manifest["model"], "claude-sonnet-5-5")
        self.assertIsNone(manifest["agents"])
        self.assertIsNone(manifest["memory_paths"])
        self.assertIsNone(manifest["effort"])

    def test_malformed_inputs_each_raise_stream_error_without_echoing_content(self) -> None:
        marker = "CONTENT-MARKER-XYZ"
        ok_lines = [json.dumps(init_event()), json.dumps(result_event())]
        cases = {
            "empty": b"",
            "only newline": b"\n",
            "blank line in the middle": (ok_lines[0] + "\n\n" + ok_lines[1] + "\n").encode(),
            "invalid utf-8": ok_lines[0].encode() + b"\n" + b'{"type": "x", "v": "' + marker.encode() + b'\xff"}\n',
            "truncated json": (ok_lines[0] + "\n" + '{"type": "result", "v": "%s"' % marker).encode(),
            "array line": (ok_lines[0] + "\n" + json.dumps([marker]) + "\n").encode(),
            "missing type": (ok_lines[0] + "\n" + json.dumps({"v": marker}) + "\n").encode(),
            "non-string type": (ok_lines[0] + "\n" + json.dumps({"type": 5, "v": marker}) + "\n").encode(),
            "zero results": (ok_lines[0] + "\n").encode(),
            "two results": (ok_lines[0] + "\n" + ok_lines[1] + "\n" + ok_lines[1] + "\n").encode(),
            "nan constant": (ok_lines[0] + '\n{"type": "x", "v": NaN}\n').encode(),
        }
        for label, data in cases.items():
            with self.assertRaises(pc_stream.StreamError, msg=label) as caught:
                events = pc_stream.parse_stream(data)
                pc_stream.require_single_result(events)
            self.assertNotIn(marker, str(caught.exception), label)
        with self.assertRaises(pc_stream.StreamError) as caught:
            pc_stream.parse_stream(cases["truncated json"])
        self.assertRegex(str(caught.exception), r"line 2\b")

    def test_stream_error_is_a_value_error(self) -> None:
        self.assertTrue(issubclass(pc_stream.StreamError, ValueError))

    def test_non_bytes_input_is_refused(self) -> None:
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.parse_stream("text, not bytes")  # type: ignore[arg-type]

    def test_unicode_line_separators_stay_inside_one_event(self) -> None:
        sneaky = "before after\u0085end tail"
        events = pc_stream.parse_stream(
            encode([init_event(), tool_use("t1", command=sneaky), result_event()])
        )
        self.assertEqual(len(events), 3)
        block = events[1]["message"]["content"][0]
        self.assertEqual(block["input"]["command"], sneaky)

    def test_carriage_return_line_endings_and_missing_final_newline(self) -> None:
        body = b"\r\n".join(
            json.dumps(e).encode() for e in [init_event(), result_event()]
        )
        events = pc_stream.parse_stream(body)
        self.assertEqual(len(events), 2)

    def test_two_init_events_are_refused_by_the_manifest(self) -> None:
        events = pc_stream.parse_stream(encode([init_event(), init_event(), result_event()]))
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.init_manifest(events)
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.init_manifest(pc_stream.parse_stream(encode([result_event()])))


class ResultSummaryTests(unittest.TestCase):
    def test_cost_is_a_decimal_built_from_the_number_text(self) -> None:
        data = (
            json.dumps(init_event())
            + "\n"
            + '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 3, '
            + '"total_cost_usd": 0.1234567890123456789, "terminal_reason": "completed", '
            + '"session_id": "s", "permission_denials": []}\n'
        ).encode()
        summary = pc_stream.result_summary(pc_stream.parse_stream(data))
        self.assertIsInstance(summary["total_cost_usd"], Decimal)
        self.assertEqual(summary["total_cost_usd"], Decimal("0.1234567890123456789"))
        self.assertEqual(summary["subtype"], "success")
        self.assertIs(summary["is_error"], False)
        self.assertEqual(summary["num_turns"], 3)
        self.assertEqual(summary["terminal_reason"], "completed")
        self.assertEqual(summary["permission_denials"], 0)

    def test_cost_is_none_when_absent_and_integer_costs_become_decimals(self) -> None:
        events = pc_stream.parse_stream(encode([init_event(), result_event()]))
        self.assertIsNone(pc_stream.result_summary(events)["total_cost_usd"])
        events = pc_stream.parse_stream(encode([init_event(), result_event(total_cost_usd=0)]))
        self.assertEqual(pc_stream.result_summary(events)["total_cost_usd"], Decimal(0))

    def test_denial_count_reflects_the_result_list(self) -> None:
        events = pc_stream.parse_stream(
            encode([init_event(), result_event([{"tool_use_id": "a"}, {"tool_use_id": "b"}])])
        )
        self.assertEqual(pc_stream.result_summary(events)["permission_denials"], 2)


class DenialTests(unittest.TestCase):
    def report(self, events: List[Dict[str, Any]]):
        return pc_stream.denial_report(pc_stream.parse_stream(encode(events)))

    def test_event_alone(self) -> None:
        report = self.report([init_event(), denied_event("t1"), result_event()])
        self.assertEqual(report.event_ids, frozenset({"t1"}))
        self.assertEqual(report.result_ids, frozenset())
        self.assertEqual(report.union, frozenset({"t1"}))
        self.assertEqual(report.only_in_events, frozenset({"t1"}))
        self.assertEqual(report.only_in_result, frozenset())

    def test_result_entry_alone(self) -> None:
        report = self.report([init_event(), result_event([{"tool_name": "Bash", "tool_use_id": "t2"}])])
        self.assertEqual(report.result_ids, frozenset({"t2"}))
        self.assertEqual(report.only_in_result, frozenset({"t2"}))
        self.assertEqual(report.only_in_events, frozenset())

    def test_both_signals_equal(self) -> None:
        report = self.report(
            [init_event(), denied_event("t3"), result_event([{"tool_use_id": "t3"}])]
        )
        self.assertEqual(report.union, frozenset({"t3"}))
        self.assertEqual(report.only_in_events, frozenset())
        self.assertEqual(report.only_in_result, frozenset())

    def test_both_signals_different_report_each_side(self) -> None:
        report = self.report(
            [init_event(), denied_event("left"), result_event([{"tool_use_id": "right"}])]
        )
        self.assertEqual(report.union, frozenset({"left", "right"}))
        self.assertEqual(report.only_in_events, frozenset({"left"}))
        self.assertEqual(report.only_in_result, frozenset({"right"}))

    def test_the_words_denied_and_refused_are_never_a_signal(self) -> None:
        words = "denied, permission denied and refused"
        events = [
            init_event(),
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": words}]}},
            tool_use("t1", command="ls"),
            tool_result("t1", content=words),
            result_event(result=words),
        ]
        report = self.report(events)
        self.assertEqual(report.union, frozenset())
        self.assertEqual(report.tool_errors, frozenset())
        stream = pc_stream.parse_stream(encode(events))
        self.assertEqual(pc_stream.unexpected_denials(stream, set()), [])
        self.assertFalse(pc_stream.row_failed(stream, set()))

    def test_error_tool_result_without_structured_signal_is_a_tool_error_not_a_denial(self) -> None:
        report = self.report(
            [
                init_event(),
                tool_use("t1"),
                tool_result("t1", content="was blocked", is_error=True),
                tool_use("t2"),
                tool_result("t2", is_error=True),
                denied_event("t2"),
                result_event(),
            ]
        )
        self.assertEqual(report.tool_errors, frozenset({"t1"}))
        self.assertEqual(report.union, frozenset({"t2"}))

    def test_missing_tool_use_id_is_counted_under_the_placeholder(self) -> None:
        report = self.report(
            [init_event(), denied_event(None), result_event([{"tool_name": "Bash"}])]
        )
        self.assertEqual(report.event_ids, frozenset({MISSING}))
        self.assertEqual(report.result_ids, frozenset({MISSING}))
        report = self.report([init_event(), denied_event(""), result_event()])
        self.assertEqual(report.event_ids, frozenset({MISSING}))

    def test_non_list_denials_is_a_stream_error(self) -> None:
        events = pc_stream.parse_stream(encode([init_event(), result_event({"tool_use_id": "t1"})]))
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.denial_report(events)
        events = pc_stream.parse_stream(encode([init_event(), result_event(["not a dict"])]))
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.denial_report(events)

    def test_report_on_a_stream_without_a_result_is_a_stream_error(self) -> None:
        events = pc_stream.parse_stream(encode([init_event(), denied_event("t1")]))
        with self.assertRaises(pc_stream.StreamError):
            pc_stream.denial_report(events)

    def test_unexpected_denials_returns_only_ids_outside_the_expected_set_sorted(self) -> None:
        events = pc_stream.parse_stream(
            encode(
                [
                    init_event(),
                    denied_event("zeta"),
                    denied_event("alpha"),
                    result_event([{"tool_use_id": "beta"}, {"tool_use_id": "gamma"}]),
                ]
            )
        )
        self.assertEqual(pc_stream.unexpected_denials(events, {"gamma"}), ["alpha", "beta", "zeta"])
        self.assertEqual(pc_stream.unexpected_denials(events, {"alpha", "beta", "gamma", "zeta"}), [])
        self.assertTrue(pc_stream.row_failed(events, {"gamma"}))
        self.assertFalse(pc_stream.row_failed(events, {"alpha", "beta", "gamma", "zeta"}))

    def test_row_failed_is_true_for_an_incomplete_stream(self) -> None:
        events = pc_stream.parse_stream(encode([init_event()]))
        self.assertTrue(pc_stream.row_failed(events, set()))


class ProbeTableTests(unittest.TestCase):
    def test_calls_results_and_table_join(self) -> None:
        events = pc_stream.parse_stream(
            encode(
                [
                    init_event(),
                    tool_use("t1", name="Bash", command="ls -la"),
                    tool_result("t1", content="listing"),
                    tool_use("t2", name="Read", file_path="x"),
                    denied_event("t2"),
                    tool_result("t2", content=["a", "b", "c"], is_error=True),
                    result_event([{"tool_use_id": "t2"}]),
                ]
            )
        )
        self.assertEqual(
            pc_stream.tool_calls(events),
            [("t1", "Bash", {"command": "ls -la"}), ("t2", "Read", {"file_path": "x"})],
        )
        results = pc_stream.tool_results(events)
        self.assertEqual(results["t1"], (False, "str", 7))
        self.assertEqual(results["t2"], (True, "list", 3))
        table = pc_stream.probe_table(events)
        self.assertEqual(
            table,
            [
                ("t1", "Bash", "ls -la", False, False, False),
                ("t2", "Read", None, True, True, True),
            ],
        )
        flat = repr(results)
        self.assertNotIn("listing", flat)


class SourceDisciplineTests(unittest.TestCase):
    def _source_lines(self) -> List[str]:
        with open(STREAM_SCRIPT, "r", encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_no_code_searches_text_for_denial_words(self) -> None:
        pattern = re.compile(
            r"""(['"])(denied|refused|permission denied)\1\s+in\b"""
            r"""|\.(find|count|index|startswith|endswith)\(\s*['"][^'"]*(denied|refused)"""
            r"""|re\.\w+\(.*(denied|refused)""",
            re.IGNORECASE,
        )
        for number, line in enumerate(self._source_lines(), 1):
            if line.lstrip().startswith("#"):
                continue
            self.assertIsNone(pattern.search(line), "line %d searches text for a denial word" % number)

    def test_module_is_read_only(self) -> None:
        forbidden = re.compile(r"os\.(remove|unlink|rename|replace|rmdir|mkdir|makedirs)|shutil|tempfile|os\.open")
        for number, line in enumerate(self._source_lines(), 1):
            if line.lstrip().startswith("#"):
                continue
            self.assertIsNone(forbidden.search(line), "line %d changes the file system" % number)
            if "open(" in line and "def " not in line:
                self.assertIn('"rb"', line, "line %d opens a file other than read-only bytes" % number)
            if ".write(" in line:
                self.assertTrue(
                    "sys.stdout.write" in line or "sys.stderr.write" in line,
                    "line %d writes somewhere other than a standard stream" % number,
                )


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = tempfile.mkdtemp(prefix="pc-stream-")

    def _write(self, name: str, data: bytes) -> str:
        path = os.path.join(self.parent, name)
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def _check(self, *args: str):
        return subprocess.run(
            [sys.executable, "-E", "-s", "-B", STREAM_SCRIPT] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60,
        )

    def test_clean_stream_exits_0_and_prints_counts_only(self) -> None:
        path = self._write("clean.jsonl", good_stream())
        done = self._check("check", path)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("result subtype: success", done.stdout)
        self.assertIn("denial ids: 0", done.stdout)
        self.assertIn("events: assistant=1 result=1 system=1 user=1", done.stdout)
        self.assertEqual(len(done.stdout.splitlines()), 3)

    def test_unexpected_denial_exits_19_and_expected_denial_exits_0(self) -> None:
        data = encode(
            [init_event(), tool_use("t9"), denied_event("t9"), tool_result("t9", is_error=True), result_event()]
        )
        path = self._write("denied.jsonl", data)
        done = self._check("check", path)
        self.assertEqual(done.returncode, pc_exitcodes.DENIAL_FOUND)
        self.assertIn("t9", done.stdout)
        done = self._check("check", path, "--expect-denied", "t9")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_incomplete_and_unparseable_streams_exit_19(self) -> None:
        incomplete = self._write("incomplete.jsonl", encode([init_event()]))
        self.assertEqual(self._check("check", incomplete).returncode, 19)
        broken = self._write("broken.jsonl", b'{"type": "system"\n')
        done = self._check("check", broken)
        self.assertEqual(done.returncode, 19)
        self.assertNotIn('"type"', done.stdout + done.stderr)

    def test_missing_file_and_bad_usage_exit_2(self) -> None:
        self.assertEqual(self._check("check", os.path.join(self.parent, "absent.jsonl")).returncode, 2)
        self.assertEqual(self._check().returncode, 2)
        self.assertEqual(self._check("frobnicate").returncode, 2)

    def test_the_checker_does_not_modify_its_input(self) -> None:
        path = self._write("clean.jsonl", good_stream())
        before = os.stat(path).st_mtime_ns
        self._check("check", path)
        self.assertEqual(os.stat(path).st_mtime_ns, before)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), good_stream())


if __name__ == "__main__":
    unittest.main()
