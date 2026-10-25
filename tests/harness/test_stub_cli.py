"""Command-line tests for the checkpoint stub: CKPT_HOME refusal, branding, exit codes, verbs.

Zero tokens. The stub runs as a subprocess with the current interpreter and the
isolated, no-bytecode flags, from an explicit minimal environment. Scratch
directories live under the system temp directory; they are never deleted by the
test and their paths are never printed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STUB = os.path.join(HERE, "checkpoint_stub.py")
EVIDENCE = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20")

BRAND = "checkpoint-stub: STUB-BACKED test apparatus, not the real checkpoint helper"
BANNER = "checkpoint-stub 1 (stub-backed checkpoint-v1; test apparatus, not the real helper)"
NO_HOME_MESSAGE = "checkpoint: CKPT_HOME is not set to an existing directory"

SECTIONS = [
    "Goal & current state",
    "Decisions (with reasons)",
    "Blockers & open questions",
    "Authorization boundaries",
    "Evidence & key paths",
    "Next action",
]
SESSION = "%08x-%04x-4%03x-8%03x-%012x" % (0x5E551001, 0x1111, 0x222, 0x333, 0x444444444444)
OTHER = "%08x-%04x-4%03x-8%03x-%012x" % (0x0B5E4002, 0x2222, 0x333, 0x444, 0x555555555555)
ID8 = SESSION[:8]
ISO_MS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
VALID_RE = re.compile(r"^valid checkpoint: [0-9]+ bytes, Authorization [0-9]+ chars\n$")


def scratch(prefix: str = "pc-stub-cli-") -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix=prefix))


def run_stub(args, home=None, session=SESSION, env_extra=None, cwd=None, unset_home=False):
    """Run the stub; return (returncode, stdout, stderr) as text."""
    env = {"PATH": "/usr/bin:/bin"}
    if home is not None and not unset_home:
        env["CKPT_HOME"] = home
    if session is not None:
        env["CLAUDE_CODE_SESSION_ID"] = session
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "-I", "-B", STUB] + list(args),
        env=env,
        cwd=cwd or tempfile.gettempdir(),
        capture_output=True,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def body_for(name: str) -> str:
    return "Body of %s." % name


def ledger_text(bodies=None, updated="2026-10-19T23:10:27.227Z", by=ID8, title="demo") -> str:
    bodies = dict(bodies or {})
    parts = []
    for name in SECTIONS:
        parts.append("## %s\n%s" % (name, bodies.get(name, body_for(name))))
    return (
        "# CONTINUITY — %s\n\n<!-- CHECKPOINT:BEGIN updated: %s by: %s -->\n%s\n"
        "<!-- CHECKPOINT:END -->\n\n## History\n" % (title, updated, by, "\n\n".join(parts))
    )


def block_text(bodies=None, names=None) -> str:
    bodies = dict(bodies or {})
    parts = []
    for name in names if names is not None else SECTIONS:
        parts.append("## %s\n%s" % (name, bodies.get(name, body_for(name))))
    return (
        "<!-- CHECKPOINT:BEGIN updated: 1970-01-01T00:00:00Z by: preclear -->\n%s\n"
        "<!-- CHECKPOINT:END -->\n" % "\n\n".join(parts)
    )


class Rig(object):
    """A scratch CKPT_HOME with one ledger, bound to SESSION."""

    def __init__(self, text=None, bind=True) -> None:
        self.home = scratch()
        self.ledgers = os.path.join(self.home, "ledgers")
        os.mkdir(self.ledgers)
        self.project = os.path.join(self.home, "project")
        os.mkdir(self.project)
        self.ledger = os.path.join(self.ledgers, "CONTINUITY_CLAUDE-demo.md")
        self.write(self.ledger, ledger_text() if text is None else text)
        if bind:
            code, out, err = run_stub(["bind", "--ledger", self.ledger], home=self.home)
            assert code == 0, err

    def write(self, path, text) -> None:
        with open(path, "wb") as handle:
            handle.write(text.encode("utf-8"))

    def read(self, path=None) -> bytes:
        with open(path or self.ledger, "rb") as handle:
            return handle.read()

    def file(self, name, text) -> str:
        path = os.path.join(self.project, name)
        self.write(path, text)
        return path

    def run(self, args, **kwargs):
        kwargs.setdefault("cwd", self.project)
        return run_stub(args, home=self.home, **kwargs)

    def show_hashes(self) -> dict:
        code, out, err = self.run(["show"])
        assert code == 0, err
        return parse_show(out)["hashes"]

    def conflicts(self) -> list:
        prefix = os.path.basename(self.ledger) + ".conflict-"
        return sorted(n for n in os.listdir(self.ledgers) if n.startswith(prefix))


def parse_show(text: str) -> dict:
    head, _, rest = text.partition("\n\n")
    header = dict(line.split(": ", 1) for line in head.split("\n"))
    sections = []
    pattern = re.compile(
        r"(?ms)^## (?P<name>[^\n]+)\nsection-hash: (?P<hash>[0-9a-f]{64})\n(?P<body>.*?)(?=^## [^\n]+\nsection-hash: |\Z)"
    )
    for match in pattern.finditer(rest):
        sections.append((match.group("name"), match.group("hash"), match.group("body")))
    return {"header": header, "sections": sections, "hashes": {n: h for n, h, _ in sections}}


class NoCkptHomeTests(unittest.TestCase):
    def assert_refused(self, code, out, err) -> None:
        self.assertEqual(64, code)
        self.assertEqual("", out)
        lines = err.splitlines()
        self.assertEqual(BRAND, lines[0])
        self.assertEqual(1, err.count(BRAND))
        self.assertIn(NO_HOME_MESSAGE, lines)

    def test_unset_ckpt_home_exits_64(self) -> None:
        self.assert_refused(*run_stub(["status"], home=None))

    def test_empty_ckpt_home_exits_64(self) -> None:
        self.assert_refused(*run_stub(["status"], home=None, env_extra={"CKPT_HOME": ""}))

    def test_missing_path_exits_64(self) -> None:
        missing = os.path.join(scratch(), "does-not-exist")
        self.assert_refused(*run_stub(["status"], home=missing))

    def test_path_that_is_a_file_exits_64(self) -> None:
        path = os.path.join(scratch(), "a-file")
        with open(path, "wb") as handle:
            handle.write(b"x")
        self.assert_refused(*run_stub(["status"], home=path))

    def test_every_state_verb_refuses_without_ckpt_home(self) -> None:
        for args in (["show"], ["lint"], ["validate", "--from", "x"], ["bind", "--ledger", "x"],
                     ["update", "--section", "Next action", "--expect-section", "0" * 64, "--from", "x"]):
            self.assert_refused(*run_stub(args, home=None))

    def test_version_works_without_ckpt_home(self) -> None:
        code, out, err = run_stub(["--version"], home=None)
        self.assertEqual(0, code)
        self.assertEqual(BANNER + "\n", out)
        self.assertEqual(BRAND + "\n", err)

    def test_help_works_without_ckpt_home_and_has_no_brand_on_stdout(self) -> None:
        code, out, err = run_stub(["--help"], home=None)
        self.assertEqual(0, code)
        self.assertEqual(BRAND + "\n", err)
        self.assertNotIn("stub", out.lower())
        self.assertIn("status", out)


class BrandTests(unittest.TestCase):
    def test_every_invocation_path_prints_one_brand_line_and_no_brand_on_stdout(self) -> None:
        rig = Rig()
        unbound = Rig(bind=False)
        good_block = rig.file("block.md", block_text())
        paths = [
            (rig, ["status"]),
            (rig, ["show"]),
            (rig, ["show", "--section", "Next action"]),
            (rig, ["lint"]),
            (rig, ["validate", "--from", good_block]),
            (rig, ["validate", "--from", os.path.join(rig.project, "missing.md")]),
            (rig, []),
            (rig, ["nonsense"]),
            (rig, ["update", "--section", "No such section", "--expect-section", "0" * 64, "--from", good_block]),
            (rig, ["update", "--section", "Next action", "--expect-section", "f" * 64, "--from", good_block]),
            (rig, ["note"]),
            (rig, ["handoff"]),
            (rig, ["create"]),
            (rig, ["init"]),
            (unbound, ["status"]),
            (unbound, ["show"]),
            (rig, ["bind", "--ledger", os.path.join(tempfile.gettempdir(), "elsewhere.md")]),
        ]
        for target, args in paths:
            code, out, err = target.run(args)
            label = " ".join(args) or "(no arguments)"
            self.assertEqual(1, err.count(BRAND), label)
            self.assertEqual(BRAND, err.splitlines()[0], label)
            self.assertNotIn("STUB-BACKED", out, label)
            self.assertNotIn("stub-backed", out, label)
            self.assertNotIn("checkpoint-stub", out, label)

    def test_no_session_still_one_brand_line(self) -> None:
        rig = Rig()
        code, out, err = rig.run(["status"], session=None)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(1, err.count(BRAND))


class ExitCodeTests(unittest.TestCase):
    def test_usage_errors_exit_2(self) -> None:
        rig = Rig()
        for args in ([], ["frobnicate"], ["validate"], ["show", "--section", "Nope"], ["show", "--bogus"]):
            self.assertEqual(2, rig.run(args)[0], args)
        code, out, err = rig.run(["update", "--section", "Next action", "--expect-section", "NOTAHASH", "--from", "x"])
        self.assertEqual(2, code)
        self.assertEqual("", out)

    def test_session_flag_works_before_and_after_the_verb(self) -> None:
        rig = Rig()
        expected = "session %s → %s\n" % (ID8, rig.ledger)
        for args in (["status", "--session", SESSION], ["--session", SESSION, "status"]):
            code, out, err = rig.run(args, session=None)
            self.assertEqual(0, code, err)
            self.assertTrue(out.startswith(expected), out)

    def test_session_id_shape_is_checked(self) -> None:
        rig = Rig()
        for bad in ("../x", "short", "a/b/c/d/e/f/g/h"):
            self.assertEqual(2, rig.run(["status"], session=bad)[0], bad)


class StatusTests(unittest.TestCase):
    def test_bound_status_is_three_lines(self) -> None:
        rig = Rig()
        code, out, err = rig.run(["status"])
        self.assertEqual(0, code)
        self.assertEqual(
            "session %s → %s\ncheckpoint updated 2026-10-19T23:10:27.227Z by %s\nNext action: %s\n"
            % (ID8, rig.ledger, ID8, body_for("Next action")),
            out,
        )

    def test_unbound_status_is_one_line_exit_0(self) -> None:
        rig = Rig(bind=False)
        code, out, err = rig.run(["status"])
        self.assertEqual((0, "session %s: unbound\n" % ID8), (code, out))

    def test_ledger_without_a_block_prints_none(self) -> None:
        rig = Rig(text="# CONTINUITY — demo\n\n## History\n")
        code, out, err = rig.run(["status"])
        self.assertEqual(0, code)
        self.assertEqual(["session %s → %s" % (ID8, rig.ledger), "checkpoint: NONE"], out.splitlines())

    def test_next_action_line_shows_only_the_first_line(self) -> None:
        rig = Rig(text=ledger_text({"Next action": "First line.\nSecond line."}))
        code, out, err = rig.run(["status"])
        self.assertEqual("Next action: First line.", out.splitlines()[2])






class ContainmentBasicsTests(unittest.TestCase):
    def test_bind_refuses_a_ledger_outside_ckpt_home(self) -> None:
        rig = Rig(bind=False)
        outside = os.path.join(scratch(), "CONTINUITY_CLAUDE-out.md")
        with open(outside, "wb") as handle:
            handle.write(ledger_text().encode("utf-8"))
        code, out, err = rig.run(["bind", "--ledger", outside])
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertFalse(os.path.exists(os.path.join(rig.home, "bindings")))

    def test_bind_writes_the_binding_keys_and_registers_the_root(self) -> None:
        rig = Rig()
        with open(os.path.join(rig.home, "bindings", SESSION + ".json"), "r", encoding="utf-8") as handle:
            text = handle.read()
        data = json.loads(text)
        self.assertEqual(
            ["created", "ledger", "predecessor", "project", "retired", "session_id", "workstream"], sorted(data)
        )
        self.assertEqual(rig.ledger, data["ledger"])
        with open(os.path.join(rig.home, "ledger-roots.json"), "r", encoding="utf-8") as handle:
            roots = json.loads(handle.read())
        self.assertEqual({"roots": [rig.ledgers]}, roots)


class SourceHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        with open(STUB, "r", encoding="utf-8") as handle:
            self.source = handle.read()

    def test_stub_has_no_call_log_no_injection_and_no_switches_yet(self) -> None:
        for word in ("calls.log", "injection", "armed", "CKPT_STUB_"):
            self.assertNotIn(word, self.source, word)

    def test_stub_imports_no_harness_module(self) -> None:
        self.assertIsNone(re.search(r"(?m)^\s*(import|from)\s+pc_", self.source))

    def test_docstring_lists_every_unconfirmed_behaviour(self) -> None:
        head = self.source.split('"""', 2)[1]
        self.assertIn("STUB-BACKED", head)
        self.assertIn("UNCONFIRMED", head)
        for word in ("note", "handoff", "kill switch", "checkpoint: NONE", "carried-from", "lint warnings",
                     "validate rejection codes", "bind, create and init", "ledger-roots.json",
                     ".checkpoint-log.jsonl", "repeated --section"):
            self.assertIn(word, head, word)

    def test_stub_is_executable(self) -> None:
        self.assertTrue(os.access(STUB, os.X_OK))
        self.assertTrue(self.source.startswith("#!/usr/bin/env python3\n"))


if __name__ == "__main__":
    unittest.main()
