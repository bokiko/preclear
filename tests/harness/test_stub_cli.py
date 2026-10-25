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


def tree_digest(root: str) -> str:
    """One digest over every folder and file under root: sorted relative path bytes plus content."""
    digest = hashlib.sha256()
    for folder, dirs, files in os.walk(root):
        dirs.sort()
        rel_folder = os.path.relpath(folder, root)
        digest.update(b"D:" + os.fsencode(rel_folder) + b"\n")
        for name in sorted(files):
            path = os.path.join(folder, name)
            digest.update(b"F:" + os.fsencode(os.path.relpath(path, root)) + b"\n")
            with open(path, "rb") as handle:
                digest.update(hashlib.sha256(handle.read()).digest())
    return digest.hexdigest()


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
    def test_exit_0_2_3_4_64_are_each_reachable(self) -> None:
        rig = Rig()
        self.assertEqual(0, rig.run(["status"])[0])
        self.assertEqual(2, rig.run(["status"], session=None)[0])
        body = rig.file("body.md", "new")
        self.assertEqual(3, rig.run(["update", "--section", "Next action", "--expect-section", "e" * 64, "--from", body])[0])
        bad = rig.file("bad.md", block_text(names=SECTIONS[:5]))
        self.assertEqual(4, rig.run(["validate", "--from", bad])[0])
        self.assertEqual(64, run_stub(["status"], home=None)[0])

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


class ShowTests(unittest.TestCase):
    def test_show_layout_and_hash_is_sha256_of_the_displayed_body(self) -> None:
        rig = Rig(text=ledger_text({"Decisions (with reasons)": "Line one.\nLine two with é and 中."}))
        code, out, err = rig.run(["show"])
        self.assertEqual(0, code)
        shown = parse_show(out)
        self.assertEqual(["ledger", "file-fingerprint", "checkpoint-updated"], list(shown["header"]))
        self.assertEqual(rig.ledger, shown["header"]["ledger"])
        self.assertEqual(hashlib.sha256(rig.read()).hexdigest(), shown["header"]["file-fingerprint"])
        self.assertEqual("2026-10-19T23:10:27.227Z by %s" % ID8, shown["header"]["checkpoint-updated"])
        self.assertEqual(SECTIONS, [name for name, _h, _b in shown["sections"]])
        for name, digest, body in shown["sections"]:
            self.assertEqual(hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest(), digest, name)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertTrue(out.endswith("\n\n"))

    def test_show_section_prints_the_header_and_one_section(self) -> None:
        rig = Rig()
        code, out, err = rig.run(["show", "--section", "Next action"])
        shown = parse_show(out)
        self.assertEqual(0, code)
        self.assertEqual(["Next action"], [n for n, _h, _b in shown["sections"]])
        self.assertEqual(3, len(shown["header"]))

    def test_repeated_section_flag_uses_the_first_value(self) -> None:
        rig = Rig()
        code, out, err = rig.run(["show", "--section", "Next action", "--section", "Goal & current state"])
        self.assertEqual(["Next action"], [n for n, _h, _b in parse_show(out)["sections"]])

    def test_empty_body_has_the_digest_of_the_empty_string(self) -> None:
        rig = Rig(text=ledger_text({"Blockers & open questions": ""}))
        code, out, err = rig.run(["show", "--section", "Blockers & open questions"])
        self.assertEqual(0, code)
        self.assertEqual(hashlib.sha256(b"").hexdigest(), parse_show(out)["hashes"]["Blockers & open questions"])

    def test_show_without_a_block_exits_2(self) -> None:
        rig = Rig(text="# CONTINUITY — demo\n")
        self.assertEqual(2, rig.run(["show"])[0])

    def test_show_explicit_ledger_without_binding(self) -> None:
        rig = Rig()
        code, out, err = rig.run(["show", "--ledger", rig.ledger], session=OTHER)
        self.assertEqual(0, code, err)
        self.assertEqual(rig.ledger, parse_show(out)["header"]["ledger"])

    def test_committed_path_free_hashes_reproduce_from_the_committed_ledger(self) -> None:
        rig = Rig()
        committed = os.path.join(EVIDENCE, "row2-double-conflict", "snap-0-setup", "CONTINUITY_CLAUDE-widget-export.md")
        with open(committed, "rb") as handle:
            data = handle.read()
        rig.write(rig.ledger, data.decode("utf-8"))
        code, out, err = rig.run(["show", "--ledger", rig.ledger])
        self.assertEqual(0, code, err)
        hashes = parse_show(out)["hashes"]
        self.assertEqual("903ea500e7ccf842c1312b6c2f964e3e98ff146456cecec717e9a0e122bf735f", hashes["Blockers & open questions"])
        self.assertEqual("ce26d74e1d4ccc3ec8ba4add6a30df523b974bf263b5d32b353d115e7744529e", hashes["Next action"])
        self.assertEqual("2b0f84aac189b468066ae72aae01359d73b6c64b25e2de7f39406441014ce366", hashes["Decisions (with reasons)"])
        self.assertEqual("2caab006bb9d0bba2c4f412d9522c4181baf140aadef7e5a186025be7f06fb01", hashes["Evidence & key paths"])


class ValidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rig = Rig()

    def validate(self, text: str):
        return self.rig.run(["validate", "--from", self.rig.file("candidate.md", text)])

    def assert_rejected(self, text: str, fragment: str) -> None:
        code, out, err = self.validate(text)
        self.assertEqual(4, code, err)
        self.assertEqual("", out)
        self.assertIn("checkpoint: invalid checkpoint: ", err)
        self.assertIn(fragment, err)

    def test_committed_block_files_are_accepted(self) -> None:
        for row in ("row2-double-conflict", "row3b-denied-helper-write", "row3b-denied-helper-write-rerun"):
            path = os.path.join(EVIDENCE, row, "snap-2-after-preclear", "preclear", "backend-inputs", "block.md")
            code, out, err = self.rig.run(["validate", "--from", path])
            self.assertEqual(0, code, (row, err))
            self.assertRegex(out, VALID_RE)

    def test_success_line_counts_authorization_chars_without_the_trailing_newline(self) -> None:
        code, out, err = self.validate(block_text({"Authorization boundaries": "Edit 中文 only.\n"}))
        self.assertEqual(0, code, err)
        self.assertRegex(out, VALID_RE)
        self.assertIn("Authorization %d chars" % len("Edit 中文 only."), out)
        size = int(re.search(r"checkpoint: (\d+) bytes", out).group(1))
        rendered = ("<!-- CHECKPOINT:BEGIN updated: 1970-01-01T00:00:00.000Z by: %s -->\n" % ID8)
        parts = []
        for name in SECTIONS:
            body = "Edit 中文 only." if name == "Authorization boundaries" else body_for(name)
            parts.append("## %s\n%s" % (name, body))
        rendered += "\n\n".join(parts) + "\n<!-- CHECKPOINT:END -->"
        self.assertEqual(len(rendered.encode("utf-8")), size)

    def test_missing_section_is_rejected(self) -> None:
        self.assert_rejected(block_text(names=SECTIONS[:5]), "missing section: Next action")

    def test_extra_section_is_rejected(self) -> None:
        self.assert_rejected(block_text(names=SECTIONS + ["Unplanned"]), "extra section: Unplanned")

    def test_duplicate_section_is_rejected(self) -> None:
        self.assert_rejected(block_text(names=SECTIONS + [SECTIONS[0]]), "duplicate section")

    def test_misordered_sections_are_rejected(self) -> None:
        names = list(SECTIONS)
        names[0], names[1] = names[1], names[0]
        self.assert_rejected(block_text(names=names), "out of order")

    def test_empty_authorization_is_rejected(self) -> None:
        self.assert_rejected(block_text({"Authorization boundaries": ""}), "Authorization boundaries is empty")

    def test_authorization_over_600_chars_is_rejected_and_600_passes(self) -> None:
        self.assert_rejected(block_text({"Authorization boundaries": "a" * 601}), "601 chars")
        code, out, err = self.validate(block_text({"Authorization boundaries": "a" * 600}))
        self.assertEqual(0, code, err)

    def test_block_over_4096_bytes_is_rejected(self) -> None:
        self.assert_rejected(block_text({"Evidence & key paths": "e" * 4100}), "bytes (limit 4096)")

    def test_missing_markers_and_text_before_the_first_section(self) -> None:
        self.assert_rejected("## Goal & current state\nx\n", "missing begin marker")
        self.assert_rejected(block_text().replace("<!-- CHECKPOINT:END -->\n", ""), "missing end marker")
        stray = block_text().replace("-->\n## Goal", "-->\nstray line\n## Goal", 1)
        self.assert_rejected(stray, "text before the first section")

    def test_undecodable_bytes_exit_4_and_missing_file_exits_2(self) -> None:
        path = os.path.join(self.rig.project, "binary.md")
        with open(path, "wb") as handle:
            handle.write(b"\xff\xfe\x00bad")
        code, out, err = self.rig.run(["validate", "--from", path])
        self.assertEqual(4, code)
        self.assertEqual(2, self.rig.run(["validate", "--from", os.path.join(self.rig.project, "none.md")])[0])

    def test_validate_writes_nothing(self) -> None:
        before = self.rig.read()
        self.validate(block_text())
        self.assertEqual(before, self.rig.read())
        self.assertEqual([], self.rig.conflicts())


class UpdateTests(unittest.TestCase):
    def test_update_with_the_current_hash_replaces_only_that_section(self) -> None:
        text = ledger_text() + "Existing history line.\n"
        rig = Rig(text=text)
        before = rig.show_hashes()
        body = rig.file("goal.md", "Fresh goal.\nSecond line.\n\n")
        code, out, err = rig.run(
            ["update", "--section", "Goal & current state", "--expect-section", before["Goal & current state"], "--from", body]
        )
        self.assertEqual(0, code, err)
        self.assertEqual('updated "Goal & current state" in %s\n' % rig.ledger, out)
        after = rig.show_hashes()
        for name in SECTIONS:
            if name == "Goal & current state":
                self.assertEqual(hashlib.sha256(b"Fresh goal.\nSecond line.").hexdigest(), after[name])
            else:
                self.assertEqual(before[name], after[name], name)
        data = rig.read().decode("utf-8")
        self.assertTrue(data.startswith("# CONTINUITY — demo\n\n<!-- CHECKPOINT:BEGIN updated: "))
        self.assertTrue(data.endswith("<!-- CHECKPOINT:END -->\n\n## History\nExisting history line.\n"))
        marker = re.search(r"<!-- CHECKPOINT:BEGIN updated: (\S+) by: (\S+) -->", data)
        self.assertRegex(marker.group(1), ISO_MS)
        self.assertNotEqual("2026-10-19T23:10:27.227Z", marker.group(1))
        self.assertEqual(ID8, marker.group(2))
        self.assertFalse(data.split("<!-- CHECKPOINT:END -->")[0].endswith("\n\n"))

    def test_update_appends_one_audit_line_beside_the_ledger(self) -> None:
        rig = Rig()
        hashes = rig.show_hashes()
        body = rig.file("n.md", "Next.")
        rig.run(["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", body])
        log = os.path.join(rig.ledgers, ".checkpoint-log.jsonl")
        with open(log, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        self.assertTrue(lines[-1].startswith("{"))
        self.assertIn('"verb": "update"', lines[-1])

    def test_update_with_a_stale_hash_exits_3_and_writes_only_the_conflict_file(self) -> None:
        rig = Rig()
        before = rig.read()
        names_before = sorted(os.listdir(rig.ledgers))
        body = rig.file("goal.md", "Yours.\n")
        stale = "a" * 64
        code, out, err = rig.run(["update", "--section", "Goal & current state", "--expect-section", stale, "--from", body])
        self.assertEqual(3, code)
        self.assertEqual("", out)
        self.assertEqual(before, rig.read())
        created = sorted(set(os.listdir(rig.ledgers)) - set(names_before))
        self.assertEqual(1, len(created), created)
        name = created[0]
        self.assertRegex(
            name,
            r"^CONTINUITY_CLAUDE-demo\.md\.conflict-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z-%s\.md$" % ID8,
        )
        current = rig.show_hashes()["Goal & current state"]
        with open(os.path.join(rig.ledgers, name), "rb") as handle:
            content = handle.read().decode("utf-8")
        self.assertEqual(
            '# Conflict on section "Goal & current state"\n'
            "ledger: %s\nyour base hash: %s\ncurrent hash: %s\n\n"
            "## Yours (not applied)\nYours.\n\n## Current (kept)\n%s\n"
            % (rig.ledger, stale, current, body_for("Goal & current state")),
            content,
        )
        self.assertIn('checkpoint: conflict: "Goal & current state" changed since your read. Nothing written.', err)
        self.assertIn("Details: %s" % os.path.join(rig.ledgers, name), err)

    def test_repeated_stale_update_conflicts_again_with_a_new_file(self) -> None:
        rig = Rig()
        body = rig.file("goal.md", "Yours.\n")
        args = ["update", "--section", "Goal & current state", "--expect-section", "b" * 64, "--from", body]
        self.assertEqual(3, rig.run(args)[0])
        self.assertEqual(3, rig.run(args)[0])
        self.assertEqual(2, len(rig.conflicts()))

    def test_update_with_an_unchanged_body_succeeds(self) -> None:
        rig = Rig()
        hashes = rig.show_hashes()
        body = rig.file("same.md", body_for("Next action") + "\n")
        code, out, err = rig.run(["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", body])
        self.assertEqual(0, code, err)
        self.assertEqual(hashes, rig.show_hashes())

    def test_invalid_result_exits_4_and_leaves_the_ledger_unchanged(self) -> None:
        rig = Rig()
        before = rig.read()
        hashes = rig.show_hashes()
        empty = rig.file("empty.md", "\n")
        code, out, err = rig.run(
            ["update", "--section", "Authorization boundaries", "--expect-section", hashes["Authorization boundaries"], "--from", empty]
        )
        self.assertEqual(4, code)
        self.assertEqual(before, rig.read())
        heading = rig.file("heading.md", "text\n## Smuggled\nmore\n")
        code, out, err = rig.run(["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", heading])
        self.assertEqual(4, code)
        self.assertEqual(before, rig.read())

    def test_update_without_a_block_exits_2(self) -> None:
        rig = Rig(text="# CONTINUITY — demo\n")
        body = rig.file("b.md", "x")
        code, out, err = rig.run(["update", "--section", "Next action", "--expect-section", "c" * 64, "--from", body])
        self.assertEqual(2, code)
        self.assertIn("no checkpoint block", err)

    def test_missing_input_file_exits_2(self) -> None:
        rig = Rig()
        hashes = rig.show_hashes()
        code, out, err = rig.run(
            ["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", os.path.join(rig.project, "gone.md")]
        )
        self.assertEqual(2, code)


class LintTests(unittest.TestCase):
    def test_lint_ok_for_a_good_ledger_and_conflict_files_are_not_linted(self) -> None:
        rig = Rig()
        body = rig.file("g.md", "x")
        rig.run(["update", "--section", "Next action", "--expect-section", "d" * 64, "--from", body])
        self.assertEqual(1, len(rig.conflicts()))
        code, out, err = rig.run(["lint"])
        self.assertEqual((0, "ledger lint OK\n"), (code, out))

    def test_lint_warns_per_problem_naming_the_ledger_and_exits_0(self) -> None:
        rig = Rig()
        broken = os.path.join(rig.ledgers, "CONTINUITY_CLAUDE-broken.md")
        rig.write(broken, "# CONTINUITY — broken\n\n## History\n")
        rig.write(os.path.join(rig.ledgers, "CONTINUITY_CLAUDE-thin.md"), ledger_text({"Authorization boundaries": ""}))
        code, out, err = rig.run(["lint"], session=None)
        self.assertEqual(0, code)
        lines = out.splitlines()
        self.assertEqual(2, len(lines), out)
        self.assertTrue(all(line.startswith("warning: ") for line in lines))
        self.assertIn(broken, lines[0])
        self.assertIn("no checkpoint block", lines[0])
        self.assertIn("CONTINUITY_CLAUDE-thin.md", lines[1])

    def test_lint_with_no_registered_root_is_ok(self) -> None:
        home = scratch()
        self.assertEqual((0, "ledger lint OK\n"), run_stub(["lint"], home=home)[:2])


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

    def test_show_refuses_a_ledger_outside_a_registered_root(self) -> None:
        rig = Rig()
        other = os.path.join(rig.home, "unregistered")
        os.mkdir(other)
        path = os.path.join(other, "CONTINUITY_CLAUDE-x.md")
        rig.write(path, ledger_text())
        self.assertEqual(2, rig.run(["show", "--ledger", path])[0])
        self.assertEqual(2, rig.run(["show", "--ledger", os.path.join(scratch(), "x.md")])[0])

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


KILL_SWITCH = "CKPT_STUB_KILL_SWITCH"
NOTE_ENTRY = re.compile(r"\n### (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) \(%s\)\n" % ID8)


class NoteTests(unittest.TestCase):
    def test_note_appends_a_history_entry_and_leaves_the_block_bytes_unchanged(self) -> None:
        rig = Rig(text=ledger_text() + "Existing history line.\n")
        before = rig.read().decode("utf-8")
        body = rig.file("note.md", "Decided to keep CSV.\nSecond line.\n\n\n")
        code, out, err = rig.run(["note", "--from", body])
        self.assertEqual(0, code, err)
        self.assertEqual("noted in %s\n" % rig.ledger, out)
        after = rig.read().decode("utf-8")
        end = "<!-- CHECKPOINT:END -->"
        self.assertEqual(before.split(end)[0] + end, after.split(end)[0] + end)
        self.assertTrue(after.startswith(before), "existing History content must stay as it was")
        added = after[len(before):]
        entry = re.compile(
            r"\n### \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z \(%s\)\nDecided to keep CSV\.\nSecond line\.\n\n" % ID8
        )
        self.assertIsNotNone(entry.fullmatch(added), added)
        with open(os.path.join(rig.ledgers, ".checkpoint-log.jsonl"), "r", encoding="utf-8") as handle:
            self.assertIn('"verb": "note"', handle.read().splitlines()[-1])

    def test_second_note_goes_after_the_first(self) -> None:
        rig = Rig()
        first = rig.file("one.md", "First.")
        second = rig.file("two.md", "Second.")
        self.assertEqual(0, rig.run(["note", "--from", first])[0])
        self.assertEqual(0, rig.run(["note", "--from", second])[0])
        data = rig.read().decode("utf-8")
        self.assertEqual(2, len(NOTE_ENTRY.findall(data)))
        self.assertLess(data.index("First."), data.index("Second."))
        self.assertTrue(data.endswith("Second.\n\n"))

    def test_note_on_a_ledger_without_a_history_heading_adds_one(self) -> None:
        text = ledger_text().replace("\n## History\n", "\n")
        self.assertNotIn("## History", text)
        rig = Rig(text=text)
        body = rig.file("n.md", "Appended.")
        code, out, err = rig.run(["note", "--from", body])
        self.assertEqual(0, code, err)
        data = rig.read().decode("utf-8")
        self.assertEqual(1, data.count("\n## History\n"))
        self.assertLess(data.index("<!-- CHECKPOINT:END -->"), data.index("## History"))
        self.assertLess(data.index("## History"), data.index("Appended."))

    def test_note_takes_an_explicit_ledger_and_refuses_a_missing_input(self) -> None:
        rig = Rig()
        body = rig.file("n.md", "x")
        self.assertEqual(0, rig.run(["note", "--from", body, "--ledger", rig.ledger], session=OTHER)[0])
        code, out, err = rig.run(["note", "--from", os.path.join(rig.project, "none.md")])
        self.assertEqual(2, code)
        self.assertEqual("", out)


class KillSwitchTests(unittest.TestCase):
    def test_kill_switch_stops_update_note_and_bind_with_exit_5_and_writes_nothing(self) -> None:
        rig = Rig()
        fresh = Rig(bind=False)
        hashes = rig.show_hashes()
        body = rig.file("b.md", "Changed.")
        before = tree_digest(rig.home)
        before_fresh = tree_digest(fresh.home)
        env = {KILL_SWITCH: "1"}
        runs = [
            (rig, ["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", body]),
            (rig, ["note", "--from", body]),
            (fresh, ["bind", "--ledger", fresh.ledger]),
        ]
        for target, args in runs:
            code, out, err = target.run(args, env_extra=env)
            self.assertEqual(5, code, args[0])
            self.assertEqual("", out, args[0])
            self.assertEqual([BRAND, "checkpoint: kill switch active"], err.splitlines(), args[0])
        self.assertEqual(before, tree_digest(rig.home))
        self.assertEqual(before_fresh, tree_digest(fresh.home))

    def test_kill_switch_leaves_read_verbs_working(self) -> None:
        rig = Rig()
        good = rig.file("block.md", block_text())
        env = {KILL_SWITCH: "1"}
        for args in (["status"], ["show"], ["validate", "--from", good], ["lint"], ["--version"], ["--help"]):
            code, out, err = rig.run(args, env_extra=env)
            self.assertEqual(0, code, (args, err))

    def test_other_kill_switch_values_leave_it_off(self) -> None:
        rig = Rig()
        for value in ("0", "", "2", "true"):
            hashes = rig.show_hashes()
            body = rig.file("b.md", "Value %s." % (value or "empty"))
            args = ["update", "--section", "Next action", "--expect-section", hashes["Next action"], "--from", body]
            code, out, err = rig.run(args, env_extra={KILL_SWITCH: value})
            self.assertEqual(0, code, (value, err))


class SourceHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        with open(STUB, "r", encoding="utf-8") as handle:
            self.source = handle.read()

    def test_stub_has_no_call_log_and_no_injection(self) -> None:
        for word in ("calls.log", "injection", "armed"):
            self.assertNotIn(word, self.source, word)
        names = set(re.findall(r"CKPT_STUB_[A-Z_]+", self.source))
        self.assertLessEqual(names, {"CKPT_STUB_KILL_SWITCH", "CKPT_STUB_LOCK_TIMEOUT_MS"})

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
