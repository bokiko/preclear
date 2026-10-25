"""Zero-token replay of every mined helper call against the checkpoint stub (STUB-03).

Each case in replay-cases.json is rebuilt in a scratch CKPT_HOME: the committed
setup ledger is copied in, sessions are bound with the stub's own bind verb, the
recorded input files are copied from the committed snapshots, and every logged
argv is run in order. Where the committed exit 3 came from a concurrent writer,
this test plays that writer (test-side, outside the stub), taking its body from
the committed conflict file.

One input is not the snapshot copy: the snapshot holds the model's last goal.md, so an
update with a recorded exit 3 is given the text the committed conflict file records under
Yours (not applied), which is what that call presented.

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


def conflict_yours(text: str) -> str:
    return text.split("\n## Yours (not applied)\n", 1)[1].split("\n\n## Current (kept)\n", 1)[0]


def committed_trace_result(miner, output: dict) -> str:
    calls = miner.parse_trace(read_text(repo_path(output["path"])))
    record = calls[output["bash_index"] - 1]
    assert record["number"] == output["trace_number"]
    return re.sub(r"\AExit code \d+\n", "", record["result"])


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.miner = load_miner()
        cls.data = load_cases()
        cls.decisive_compared = 0
        cls.none_checked = 0
        cls.calls_replayed = 0

    # ------------------------------------------------------------ scenario rig

    def build_state(self, case: dict) -> dict:
        home = os.path.realpath(tempfile.mkdtemp(prefix="pc-replay-"))
        ledgers = os.path.join(home, "ledgers")
        project = os.path.join(home, "project")
        os.mkdir(ledgers)
        os.mkdir(project)
        setup = repo_path(case["setup_snapshot"])
        for name in case["ledgers"]:
            shutil.copyfile(os.path.join(setup, name), os.path.join(ledgers, name))
        sessions = [s for s in (case["session_id"], case["writer2_session"]) if s]
        if case["bound_ledger"]:
            for session in sessions:
                code, out, err = run_stub(
                    ["bind", "--ledger", os.path.join(ledgers, case["bound_ledger"])], home, session, project
                )
                self.assertEqual(0, code, err)
        for call in case["calls"]:
            for item in call["inputs"]:
                dest = os.path.join(project, *item["replay_path"].split("/"))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(repo_path(item["source"]), dest)
        return {
            "home": home,
            "ledgers": ledgers,
            "project": project,
            "full_shows": [],
            "committed_shows": [],
            "injections": 0,
            "conflicts": 0,
            "last_hashes": {},
        }

    def stub(self, state, case, args, session=None):
        return run_stub(args, state["home"], session or case["session_id"], state["project"])

    def inject(self, state, case, section: str) -> None:
        """Test-side second writer: stands in for the wrapper's conflict injector."""
        k = state["injections"]
        self.assertIsNotNone(case["writer2_session"], "a recorded exit 3 needs a second writer")
        kept = conflict_kept(read_text(repo_path(case["conflict_files"][k])))
        shown_code, shown, shown_err = self.stub(state, case, ["show", "--section", section], case["writer2_session"])
        self.assertEqual(0, shown_code, shown_err)
        current = parse_show(shown)["hashes"][section]
        body_file = os.path.join(state["home"], "writer2-body-%d.md" % (k + 1))
        with open(body_file, "wb") as handle:
            handle.write((kept + "\n").encode("utf-8"))
        code, out, err = self.stub(
            state,
            case,
            ["update", "--section", section, "--expect-section", current, "--from", body_file],
            case["writer2_session"],
        )
        self.assertEqual(0, code, err)
        ledger = os.path.join(state["ledgers"], case["bound_ledger"])
        self.assertEqual('updated "%s" in %s\n' % (section, ledger), out)
        row_dir = os.path.dirname(repo_path(case["log"]))
        injected = [
            line
            for line in read_text(os.path.join(row_dir, "wrapper-injection.log")).splitlines()
            if line.startswith("updated ")
        ]
        self.assertEqual(injected[k], normalise(out, state["ledgers"]))
        state["injections"] = k + 1

    def present_historic_input(self, state, case, call, argv) -> None:
        """Give an exit 3 update the input file the model presented at that call.

        The snapshot copy of the input file is the model's last version of it; the
        model rewrote goal.md after reading the first conflict, so the snapshot holds
        what the second update presented. What each conflicting update presented is
        recorded in the committed conflict file under Yours (not applied).
        """
        k = state["conflicts"]
        yours = conflict_yours(read_text(repo_path(case["conflict_files"][k])))
        item = call["inputs"][0]
        snapshot = read_text(repo_path(item["source"])).rstrip("\n")
        if k == len(case["conflict_files"]) - 1:
            self.assertEqual(snapshot, yours, "the last conflicting update presented the snapshot input")
        else:
            self.assertNotEqual(snapshot, yours)
            self.assertTrue(snapshot.startswith(yours))
        dest = os.path.join(state["project"], *item["replay_path"].split("/"))
        with open(dest, "wb") as handle:
            handle.write((yours + "\n").encode("utf-8"))

    def check_conflict_file(self, state, case) -> None:
        k = state["conflicts"]
        committed_rel = case["conflict_files"][k]
        prefix = case["bound_ledger"] + ".conflict-"
        names = sorted(n for n in os.listdir(state["ledgers"]) if n.startswith(prefix))
        self.assertEqual(k + 1, len(names), "one new conflict file per exit 3")
        id8 = case["session_id"][:8]
        shape = r"^%s\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z-%s\.md$" % (re.escape(prefix), id8)
        self.assertRegex(names[k], shape)
        self.assertRegex(os.path.basename(committed_rel), shape)
        replayed = read_text(os.path.join(state["ledgers"], names[k]))
        committed = read_text(repo_path(committed_rel))
        for label, text in (("replayed", replayed), ("committed", committed)):
            for match in re.finditer(r"(?m)^(?:your base hash|current hash): (.*)$", text):
                self.assertRegex(match.group(1), HEX64, label)
        self.assertEqual(
            normalise_conflict(committed, state["ledgers"]),
            normalise_conflict(replayed, state["ledgers"]),
        )
        state["conflicts"] = k + 1

    def check_show_hashes(self, out: str) -> None:
        shown = parse_show(out)
        self.assertTrue(shown["sections"])
        for name, digest, body in shown["sections"]:
            self.assertEqual(hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest(), digest, name)

    @staticmethod
    def line_kind(line: str) -> str:
        for prefix, kind in (("file-fingerprint: ", "fingerprint"), ("checkpoint-updated: ", "updated"), ("section-hash: ", "hash")):
            if line.startswith(prefix):
                return kind
        return "other"

    def check_show_pair(self, first: str, second: str, label: str) -> None:
        """The second show differs from the first in the masked header values, in the
        Goal section hash line, and in the one concurrent paragraph added to Goal."""
        removed = Counter(first.split("\n")) - Counter(second.split("\n"))
        added = Counter(second.split("\n")) - Counter(first.split("\n"))
        self.assertEqual(
            {"fingerprint": 1, "updated": 1, "hash": 1},
            dict(Counter(self.line_kind(line) for line in removed.elements())),
            label,
        )
        self.assertEqual(
            {"fingerprint": 1, "updated": 1, "hash": 1, "other": 2},
            dict(Counter(self.line_kind(line) for line in added.elements())),
            label,
        )
        before, after = parse_show(first)["hashes"], parse_show(second)["hashes"]
        self.assertEqual(["Goal & current state"], [n for n in before if before[n] != after[n]], label)

    # ------------------------------------------------------------- one call

    def replay_call(self, state, case, call) -> None:
        argv = list(call["argv"])
        for ref in call["refs"]:
            argv[ref["index"]] = state["last_hashes"][ref["section"]]
        for item in call["inputs"]:
            argv[item["index"]] = item["replay_path"]
        label = "%s call %d (%s)" % (case["row"], call["position"], call["argv"][0])
        if argv[0] == "update" and call["exit"] == 3:
            self.present_historic_input(state, case, call, argv)
            self.inject(state, case, argv[argv.index("--section") + 1])
        code, out, err = self.stub(state, case, argv)
        ReplayTests.calls_replayed += 1
        self.assertEqual(call["exit"], code, label + ": " + err)
        if argv[0] == "show":
            self.check_show_hashes(out)
            shown = parse_show(out)
            if "--section" not in argv:
                state["last_hashes"] = shown["hashes"]
                state["full_shows"].append(out)
        output = call["output"]
        kind = output["kind"]
        if kind == "status-before":
            expected = read_text(repo_path(output["path"]))
            self.assertEqual(expected, out.replace(state["ledgers"], LEDGER_TOKEN), label)
            self.assertEqual("", err, label)
            ReplayTests.decisive_compared += 1
        elif kind == "trace":
            committed = committed_trace_result(self.miner, output)
            shape_check(self, committed, label + " committed")
            shape_check(self, out, label + " replayed")
            self.assertEqual(normalise(committed, state["ledgers"]), normalise(out + err, state["ledgers"]), label)
            if argv[0] == "show" and "--section" not in argv:
                state["committed_shows"].append(committed)
            ReplayTests.decisive_compared += 1
        else:
            self.assertEqual("none", kind)
            if argv[0] == "validate":
                self.assertRegex(out, VALID_RE, label)
                self.assertEqual("", err, label)
            else:
                self.assertEqual("update", argv[0], label)
            ReplayTests.none_checked += 1
        if argv[0] == "update" and call["exit"] == 3:
            self.assertEqual("", out, label)
            self.assertIn('checkpoint: conflict: "%s" changed since your read. Nothing written. Details: ' % argv[2], err)
            self.check_conflict_file(state, case)
        if case["row"] == "row2-double-conflict" and call["position"] == 2:
            shown_hashes = parse_show(out)["hashes"]
            for name, body, prefix in PATH_FREE_BODIES:
                derived = hashlib.sha256(body.encode("utf-8")).hexdigest()
                self.assertTrue(derived.startswith(prefix), name)
                self.assertEqual(derived, shown_hashes[name], name)

    # ------------------------------------------------------------- the tests

    def test_replay_every_mined_call_against_the_committed_outputs(self) -> None:
        cases = self.data["cases"]
        self.assertEqual(9, len(cases))
        for case in cases:
            if not case["calls"]:
                continue
            with self.subTest(row=case["row"]):
                state = self.build_state(case)
                for call in case["calls"]:
                    self.replay_call(state, case, call)
                if len(state["full_shows"]) == 2:
                    self.check_show_pair(state["full_shows"][0], state["full_shows"][1], "replayed")
                    self.check_show_pair(state["committed_shows"][0], state["committed_shows"][1], "committed")
                    self.assertEqual(
                        parse_show(state["committed_shows"][1])["header"]["checkpoint-updated"].split(" by ")[1],
                        parse_show(state["full_shows"][1])["header"]["checkpoint-updated"].split(" by ")[1],
                    )
        self.assertEqual(15, ReplayTests.calls_replayed)
        self.assertEqual(13, ReplayTests.decisive_compared)
        self.assertEqual(2, ReplayTests.none_checked)

    def test_zero_call_cases_replay_nothing(self) -> None:
        empty = [case for case in self.data["cases"] if not case["calls"]]
        self.assertEqual(4, len(empty))
        for case in empty:
            self.assertEqual(0, os.path.getsize(repo_path(case["log"])), case["row"])

    def test_row2_recorded_exit_sequence(self) -> None:
        case = next(c for c in self.data["cases"] if c["row"] == "row2-double-conflict")
        self.assertEqual([0, 0, 0, 3, 0, 3], [call["exit"] for call in case["calls"]])

    def test_test_side_writer_body_comes_from_the_committed_conflict_files(self) -> None:
        case = next(c for c in self.data["cases"] if c["row"] == "row2-double-conflict")
        first = conflict_kept(read_text(repo_path(case["conflict_files"][0])))
        second = conflict_kept(read_text(repo_path(case["conflict_files"][1])))
        self.assertIn("Concurrent fact 1", first)
        self.assertNotIn("Concurrent fact 2", first)
        self.assertIn("Concurrent fact 2", second)
        self.assertTrue(second.startswith(first))

    def test_normalisation_masks_only_what_it_lists(self) -> None:
        sample = (
            "ledger: /scratch/ledgers/x.md\nfile-fingerprint: %s\ncheckpoint-updated: 2026-01-01T00:00:00.000Z by abcd1234\n\n"
            "## Goal & current state\nsection-hash: %s\nIn <repo>/<run>/project.\n\n"
            "## Next action\nsection-hash: %s\nDo it.\n\n" % ("a" * 64, "b" * 64, "c" * 64)
        )
        text = normalise(sample, "/scratch/ledgers")
        self.assertIn("ledger: <repo>/<run>/ledgers/x.md", text)
        self.assertIn("file-fingerprint: <fingerprint>", text)
        self.assertIn("checkpoint-updated: <time> by abcd1234", text)
        self.assertIn("section-hash: <hash>\nIn <repo>/<run>/project.", text)
        self.assertIn("section-hash: %s\nDo it." % ("c" * 64), text)
        self.assertNotIn("b" * 64, text)


if __name__ == "__main__":
    unittest.main()
