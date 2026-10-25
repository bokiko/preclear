"""Concurrency tests for the checkpoint stub: racing updates, a contended lock, the timeout switch.

Zero tokens. Several stub processes run at once against one scratch CKPT_HOME; the
lock is a dedicated file under CKPT_HOME that the tests take with fcntl.flock from
this process. Scratch directories live under the system temp directory, are never
deleted by the test and their paths are never printed.
"""
from __future__ import annotations

import fcntl
import hashlib
import os
import subprocess
import sys
import time
import unittest

import test_stub_cli as cli

LOCK_VAR = "CKPT_STUB_LOCK_TIMEOUT_MS"
RACERS = 4

# A barrier written in shell: every racer polls for the file, then replaces itself with the stub.
BARRIER_SCRIPT = 'while [ ! -e "$1" ]; do sleep 0.01; done; shift; exec "$@"'


class HeldLock(object):
    """Hold the stub's dedicated lock file exclusively for the length of a with block."""

    def __init__(self, home: str) -> None:
        self.path = os.path.join(home, ".lock")
        self.handle = None

    def __enter__(self):
        self.handle = open(self.path, "a+b")
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc) -> None:
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()


def update_args(rig: "cli.Rig", name: str, expect: str, body: str) -> list:
    return ["update", "--section", name, "--expect-section", expect, "--from", rig.file(body + ".md", body)]


class RaceTests(unittest.TestCase):
    def test_race_of_four_updates_with_one_hash_has_one_winner(self) -> None:
        rig = cli.Rig()
        name = "Goal & current state"
        expect = rig.show_hashes()[name]
        barrier = os.path.join(rig.project, "barrier")
        env = {"PATH": "/usr/bin:/bin", "CKPT_HOME": rig.home, "CLAUDE_CODE_SESSION_ID": cli.SESSION, LOCK_VAR: "30000"}
        procs = []
        for index in range(RACERS):
            args = update_args(rig, name, expect, "racer %d body" % index)
            command = ["/bin/sh", "-c", BARRIER_SCRIPT, "sh", barrier, sys.executable, "-I", "-B", cli.STUB] + args
            procs.append(
                subprocess.Popen(command, env=env, cwd=rig.project, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            )
        with open(barrier, "wb") as handle:
            handle.write(b"go")
        codes = []
        for proc in procs:
            proc.communicate(timeout=120)
            codes.append(proc.returncode)
        self.assertEqual([0, 3, 3, 3], sorted(codes))
        self.assertEqual(RACERS - 1, len(rig.conflicts()))
        code, out, err = rig.run(["lint"])
        self.assertEqual((0, "ledger lint OK\n"), (code, out), err)
        shown = cli.parse_show(rig.run(["show", "--section", name])[1])
        winners = [i for i in range(RACERS) if "racer %d body" % i == shown["sections"][0][2].strip()]
        self.assertEqual(1, len(winners), shown["sections"])
        digest = hashlib.sha256(("racer %d body" % winners[0]).encode("utf-8")).hexdigest()
        self.assertEqual(digest, shown["hashes"][name])


class LockTests(unittest.TestCase):
    def test_lock_contended_by_another_holder_exits_6_within_two_seconds(self) -> None:
        rig = cli.Rig()
        hashes = rig.show_hashes()
        args = update_args(rig, "Next action", hashes["Next action"], "Blocked body")
        before = rig.read()
        names_before = sorted(os.listdir(rig.ledgers))
        with HeldLock(rig.home):
            started = time.monotonic()
            code, out, err = rig.run(args, env_extra={LOCK_VAR: "200"})
            elapsed = time.monotonic() - started
        self.assertEqual(6, code)
        self.assertEqual("", out)
        self.assertEqual([cli.BRAND, "checkpoint: lock timeout"], err.splitlines())
        self.assertLess(elapsed, 2.0)
        self.assertEqual(before, rig.read())
        self.assertEqual(names_before, sorted(os.listdir(rig.ledgers)))

    def test_lock_times_out_for_every_write_verb(self) -> None:
        rig = cli.Rig()
        body = rig.file("b.md", "Body.")
        with HeldLock(rig.home):
            for verb in (["note", "--from", body], ["handoff", "--from", body], ["create", "--task", "other"]):
                code, out, err = rig.run(verb, env_extra={LOCK_VAR: "100"})
                self.assertEqual(6, code, verb[0])
        self.assertFalse(os.path.exists(os.path.join(rig.home, "handoffs")))

    def test_lock_is_a_dedicated_file_and_the_ledger_is_not_the_lock(self) -> None:
        rig = cli.Rig()
        hashes = rig.show_hashes()
        with open(rig.ledger, "rb") as ledger_handle:
            fcntl.flock(ledger_handle.fileno(), fcntl.LOCK_EX)
            code, out, err = rig.run(update_args(rig, "Next action", hashes["Next action"], "Fine"))
            fcntl.flock(ledger_handle.fileno(), fcntl.LOCK_UN)
        self.assertEqual(0, code, err)
        self.assertTrue(os.path.isfile(os.path.join(rig.home, ".lock")))

    def test_lock_timeout_value_zero_fails_at_once_and_default_waits_for_release(self) -> None:
        rig = cli.Rig()
        hashes = rig.show_hashes()
        args = update_args(rig, "Next action", hashes["Next action"], "Zero wait")
        with HeldLock(rig.home):
            self.assertEqual(6, rig.run(args, env_extra={LOCK_VAR: "0"})[0])
        self.assertEqual(0, rig.run(args, env_extra={LOCK_VAR: "0"})[0])

    def test_lock_invalid_timeout_values_exit_2_and_write_nothing(self) -> None:
        rig = cli.Rig()
        hashes = rig.show_hashes()
        args = update_args(rig, "Next action", hashes["Next action"], "Never lands")
        before = rig.read()
        for value in ("-1", "abc", " ", "", "1.5", "5000ms", "0x10"):
            code, out, err = rig.run(args, env_extra={LOCK_VAR: value})
            self.assertEqual(2, code, repr(value))
            self.assertEqual("", out, repr(value))
            self.assertIn("checkpoint: usage error: ", err)
            self.assertIn(LOCK_VAR, err)
        self.assertEqual(before, rig.read())

    def test_lock_timeout_variable_is_ignored_by_read_verbs(self) -> None:
        rig = cli.Rig()
        for args in (["status"], ["show"], ["lint"]):
            self.assertEqual(0, rig.run(args, env_extra={LOCK_VAR: "nonsense"})[0], args)
        self.assertFalse(os.path.exists(os.path.join(rig.home, ".lock")))


if __name__ == "__main__":
    unittest.main()
