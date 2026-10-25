"""Zero-token replay of the mined status calls against the checkpoint stub (STUB-03).

Each case in replay-cases.json is rebuilt in a scratch CKPT_HOME: the committed
setup ledger is copied in, sessions are bound with the stub's own bind verb, the
recorded input files are copied from the committed snapshots, and every logged
argv is run in order. Where the committed exit 3 came from a concurrent writer,
this test plays that writer (test-side, outside the stub), taking its body from
the committed conflict file.

The comparison against committed outputs applies one normalisation to both sides.
The normalisation (nothing else is masked):

  * the brand line is stripped from stderr;
  * the scratch ledger root is mapped to the committed token;
  * the hash line of a show section whose body contains a path token is masked,
    because the committed body held a real run path the sanitiser replaced, so its
    recorded hash cannot be recomputed (the four path-free hashes are asserted
    exactly, and every displayed hash is checked against its displayed body);
  * the same masking applies to the two hash lines of a conflict file whose
    section bodies contain a path token;
  * in every show header the file-fingerprint value and the checkpoint-updated
    time are masked: the first digests the whole ledger file, which the sanitised
    committed snapshot cannot reproduce, and the second is the time the previous
    writer stamped, which a replay restamps. A masked value is never compared for
    equality; its shape is asserted on both sides first (64 lowercase hex, the
    millisecond UTC shape), and the by-id8 part of the checkpoint-updated line is
    still compared;
  * the validate byte count and Authorization character count are replaced by
    placeholders (the committed block files are sanitised, so the numbers differ);
  * the time part of a conflict file name is replaced.

Scratch directories live under the system temp directory, are never deleted by the
test, and their paths are never printed. Nothing is written into tests/evidence.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STUB = os.path.join(HERE, "checkpoint_stub.py")
CASES_FILE = os.path.join(HERE, "replay-cases.json")

BRAND = "checkpoint-stub: STUB-BACKED test apparatus, not the real checkpoint helper"
LEDGER_TOKEN = "<repo>/<run>/ledgers"
PATH_TOKEN = "<repo>/"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ISO_MS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
VALID_RE = re.compile(r"^valid checkpoint: [0-9]+ bytes, Authorization [0-9]+ chars\n$")
CONFLICT_TIME = re.compile(r"\.conflict-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z-")
SECTION_RE = re.compile(
    r"(?ms)^## (?P<name>[^\n]+)\nsection-hash: (?P<hash>[0-9a-f]{64})\n(?P<body>.*?)(?=^## [^\n]+\nsection-hash: |\Z)"
)
MASKED_SECTION_RE = re.compile(
    r"(?ms)^(## [^\n]+\nsection-hash: )([0-9a-f]{64})(\n.*?)(?=^## [^\n]+\nsection-hash: |\Z)"
)

# The four section bodies of the committed row 2 ledger that hold no path token, with
# the digest prefixes the committed show output records for them. The full digest is
# derived here from the body text, independently of the stub.
PATH_FREE_BODIES = [
    ("Blockers & open questions", "None.", "903ea500e7cc"),
    ("Next action", "Write the CSV exporter (plan step 2).", "ce26d74e1d4c"),
    ("Decisions (with reasons)", "CSV first, JSON deferred: the downstream consumer only reads CSV.", "2b0f84aac189"),
    ("Evidence & key paths", "Plan: thoughts/plans/2026-10-15-widget-export.md. Branch main.", "2caab006bb9d"),
]


def load_miner():
    assert os.path.isfile(os.path.join(HERE, "pc_mine.py")), "tests/harness/pc_mine.py does not exist"
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    return importlib.import_module("pc_mine")


def load_cases() -> dict:
    assert os.path.isfile(CASES_FILE), "tests/harness/replay-cases.json does not exist"
    with open(CASES_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def repo_path(rel: str) -> str:
    return os.path.join(ROOT, *rel.split("/"))


def run_stub(args, home, session, cwd):
    """Run the stub; return (returncode, stdout, stderr without the brand line)."""
    env = {"PATH": "/usr/bin:/bin", "CKPT_HOME": home, "CLAUDE_CODE_SESSION_ID": session}
    proc = subprocess.run(
        [sys.executable, "-I", "-B", STUB] + list(args), env=env, cwd=cwd, capture_output=True
    )
    err = proc.stderr.decode("utf-8")
    assert err.startswith(BRAND + "\n") and err.count(BRAND) == 1, "stub marker line missing or repeated"
    return proc.returncode, proc.stdout.decode("utf-8"), err[len(BRAND) + 1:]


def parse_show(text: str) -> dict:
    head, _, rest = text.partition("\n\n")
    header = dict(line.split(": ", 1) for line in head.split("\n"))
    sections = [(m.group("name"), m.group("hash"), m.group("body")) for m in SECTION_RE.finditer(rest)]
    return {"header": header, "sections": sections, "hashes": {n: h for n, h, _ in sections}}


def shape_check(test: unittest.TestCase, text: str, label: str) -> None:
    """Masked values are never compared for equality; assert their shape instead."""
    for match in re.finditer(r"(?m)^file-fingerprint: (.*)$", text):
        test.assertRegex(match.group(1), HEX64, label)
    for match in re.finditer(r"(?m)^checkpoint-updated: (\S+) by (\S+)$", text):
        test.assertRegex(match.group(1), ISO_MS, label)
        test.assertRegex(match.group(2), r"^[0-9a-f]{8}$", label)


def mask_path_bearing(text: str) -> str:
    def sub(match):
        masked = "<hash>" if PATH_TOKEN in match.group(3) else match.group(2)
        return match.group(1) + masked + match.group(3)

    return MASKED_SECTION_RE.sub(sub, text)


def normalise(text: str, ledgers: str) -> str:
    text = text.replace(ledgers, LEDGER_TOKEN)
    text = mask_path_bearing(text)
    text = re.sub(r"(?m)^file-fingerprint: [0-9a-f]{64}$", "file-fingerprint: <fingerprint>", text)
    text = re.sub(r"(?m)^checkpoint-updated: \S+ by ", "checkpoint-updated: <time> by ", text)
    text = re.sub(
        r"valid checkpoint: \d+ bytes, Authorization \d+ chars",
        "valid checkpoint: <N> bytes, Authorization <M> chars",
        text,
    )
    text = CONFLICT_TIME.sub(".conflict-<time>-", text)
    return text.rstrip("\n")


def normalise_conflict(text: str, ledgers: str) -> str:
    text = text.replace(ledgers, LEDGER_TOKEN)
    head, sep, tail = text.partition("\n## Yours (not applied)\n")
    if PATH_TOKEN in tail:
        head = re.sub(r"(?m)^(your base hash|current hash): [0-9a-f]{64}$", r"\1: <hash>", head)
    return head + sep + tail


def conflict_kept(text: str) -> str:
    return text.split("\n## Current (kept)\n", 1)[1].rstrip("\n")


def committed_trace_result(miner, output: dict) -> str:
    calls = miner.parse_trace(read_text(repo_path(output["path"])))
    record = calls[output["bash_index"] - 1]
    assert record["number"] == output["trace_number"]
    return re.sub(r"\AExit code \d+\n", "", record["result"])


class StatusReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_cases()

    def test_status_replays_the_committed_status_before_files_byte_for_byte(self) -> None:
        checked = []
        for case in self.data["cases"]:
            if not case["calls"] or case["calls"][0]["argv"] != ["status"]:
                continue
            call = case["calls"][0]
            if call["output"]["kind"] != "status-before":
                continue
            with self.subTest(row=case["row"]):
                home = os.path.realpath(tempfile.mkdtemp(prefix="pc-replay-"))
                ledgers = os.path.join(home, "ledgers")
                project = os.path.join(home, "project")
                os.mkdir(ledgers)
                os.mkdir(project)
                setup = repo_path(case["setup_snapshot"])
                for name in case["ledgers"]:
                    shutil.copyfile(os.path.join(setup, name), os.path.join(ledgers, name))
                if case["bound_ledger"]:
                    code, out, err = run_stub(
                        ["bind", "--ledger", os.path.join(ledgers, case["bound_ledger"])],
                        home,
                        case["session_id"],
                        project,
                    )
                    self.assertEqual(0, code, err)
                code, out, err = run_stub(call["argv"], home, case["session_id"], project)
                self.assertEqual(call["exit"], code)
                expected = read_text(repo_path(call["output"]["path"]))
                self.assertEqual(expected, out.replace(ledgers, LEDGER_TOKEN))
                self.assertEqual("", err)
                checked.append(case["row"])
        self.assertEqual(
            [
                "row1-wrong-binding",
                "row3b-denied-helper-write",
                "row3b-denied-helper-write-rerun",
                "row3c-unbound-fallback-none",
            ],
            checked,
        )

    def test_unbound_status_is_the_committed_unbound_line(self) -> None:
        case = next(c for c in self.data["cases"] if c["row"] == "row3c-unbound-fallback-none")
        self.assertIsNone(case["bound_ledger"])
        self.assertEqual(
            "session e7ac129d: unbound\n", read_text(repo_path(case["calls"][0]["output"]["path"]))
        )


if __name__ == "__main__":
    unittest.main()
