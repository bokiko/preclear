"""Exit-code literals outside pc_exitcodes must agree with its constants (EVID-07, D-13).

Several entry points carry their own exit numbers: the run-root allocator (16 for a collision),
the stub (0 to 6 and 64) and the wrapper shim (70 and 71). pc_exitcodes names the numbers the
documentation and the other tests use. This module owns the comparison, and it compares by
running the command-line entry points, not by reading source text:

  * the allocator called twice with one name exits with RUNROOT_COLLISION the second time;
  * the stub with CKPT_HOME unset exits with STUB_NO_CKPT_HOME, and with an unknown verb exits
    with STUB_USAGE;
  * the stub's own constants equal the STUB_ mirrors, and the allocator's equal the harness codes;
  * the wrapper exits 70 when it is not configured and 71 for a driver-only verb. Those two are
    named here and in the README only: pc_exitcodes deliberately holds harness and stub codes.

Nothing here prints a path. Failure messages carry exit codes and fixed text only.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from typing import Dict, List, Optional

import checkpoint_stub
import pc_exitcodes
import pc_runroot

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
RUNROOT = os.path.join(HARNESS_DIR, "pc_runroot.py")
STUB = os.path.join(HARNESS_DIR, "checkpoint_stub.py")
WRAPPER = os.path.join(HARNESS_DIR, "checkpoint-wrapper")

# The wrapper's own codes, documented in its header and in data/branch-table.md.
WRAPPER_UNCONFIGURED = 70
WRAPPER_DRIVER_VERB = 71


def _env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8", "HOME": tempfile.gettempdir()}
    if extra:
        env.update(extra)
    return env


def _run(argv: List[str], env: Dict[str, str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        argv,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=60,
        cwd=tempfile.gettempdir(),
    )


class ConstantAgreementTests(unittest.TestCase):
    def test_the_allocator_constants_equal_the_harness_codes(self) -> None:
        self.assertEqual(pc_runroot.EXIT_COLLISION, pc_exitcodes.RUNROOT_COLLISION)
        self.assertEqual(pc_runroot.EXIT_USAGE, pc_exitcodes.USAGE)
        self.assertEqual(pc_exitcodes.RUNROOT_COLLISION, 16)

    def test_the_stub_constants_equal_the_stub_mirrors(self) -> None:
        pairs = (
            (checkpoint_stub.EXIT_OK, pc_exitcodes.STUB_OK),
            (checkpoint_stub.EXIT_INTERNAL, pc_exitcodes.STUB_INTERNAL),
            (checkpoint_stub.EXIT_USAGE, pc_exitcodes.STUB_USAGE),
            (checkpoint_stub.EXIT_CONFLICT, pc_exitcodes.STUB_CONFLICT),
            (checkpoint_stub.EXIT_INVALID, pc_exitcodes.STUB_INVALID),
            (checkpoint_stub.EXIT_KILL, pc_exitcodes.STUB_KILL_SWITCH),
            (checkpoint_stub.EXIT_LOCK, pc_exitcodes.STUB_LOCK_TIMEOUT),
            (checkpoint_stub.EXIT_NO_HOME, pc_exitcodes.STUB_NO_CKPT_HOME),
        )
        for stub_value, mirror in pairs:
            self.assertEqual(stub_value, mirror, "a stub exit code differs from its mirror")

    def test_harness_codes_avoid_the_stub_range_and_the_shell_signal_range(self) -> None:
        for code in range(pc_exitcodes.PREFLIGHT_SKIP, pc_exitcodes.DENIAL_FOUND + 1):
            self.assertNotIn(code, (0, 1, 2, 3, 4, 5, 6, 64, WRAPPER_UNCONFIGURED, WRAPPER_DRIVER_VERB))
            self.assertFalse(124 <= code <= 143)


class AllocatorExitTests(unittest.TestCase):
    def test_second_allocation_of_one_name_exits_with_runroot_collision(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            argv = [sys.executable, "-E", "-s", "-B", RUNROOT, parent, "agreement-run"]
            first = _run(argv, _env())
            second = _run(argv, _env())
        self.assertEqual(first.returncode, 0, "the first allocation did not exit 0 (exit %d)" % first.returncode)
        self.assertEqual(
            second.returncode,
            pc_exitcodes.RUNROOT_COLLISION,
            "the second allocation exited %d, expected %d" % (second.returncode, pc_exitcodes.RUNROOT_COLLISION),
        )
        self.assertEqual(second.returncode, 16)

    def test_allocator_without_arguments_exits_with_usage(self) -> None:
        result = _run([sys.executable, "-E", "-s", "-B", RUNROOT], _env())
        self.assertEqual(result.returncode, pc_exitcodes.USAGE, "exit %d, expected %d" % (result.returncode, pc_exitcodes.USAGE))


class StubExitTests(unittest.TestCase):
    def test_stub_without_ckpt_home_exits_with_stub_no_ckpt_home(self) -> None:
        env = _env()
        self.assertNotIn("CKPT_HOME", env)
        result = _run([sys.executable, "-I", "-B", STUB, "status"], env)
        self.assertEqual(
            result.returncode,
            pc_exitcodes.STUB_NO_CKPT_HOME,
            "exit %d, expected %d" % (result.returncode, pc_exitcodes.STUB_NO_CKPT_HOME),
        )
        self.assertEqual(result.returncode, 64)

    def test_stub_with_an_unknown_verb_exits_with_stub_usage(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = _run(
                [sys.executable, "-I", "-B", STUB, "no-such-verb"],
                _env({"CKPT_HOME": home}),
            )
        self.assertEqual(
            result.returncode,
            pc_exitcodes.STUB_USAGE,
            "exit %d, expected %d" % (result.returncode, pc_exitcodes.STUB_USAGE),
        )
        self.assertEqual(result.returncode, 2)


class WrapperExitTests(unittest.TestCase):
    def _copy(self, folder: str) -> str:
        target = os.path.join(folder, "checkpoint-wrapper")
        with open(WRAPPER, "rb") as source:
            data = source.read()
        with open(target, "wb") as handle:
            handle.write(data)
        os.chmod(target, 0o755)
        return target

    def test_an_unconfigured_wrapper_exits_70(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            wrapper = self._copy(folder)
            result = _run(["/bin/bash", wrapper, "status"], _env())
        self.assertEqual(result.returncode, WRAPPER_UNCONFIGURED, "exit %d, expected 70" % result.returncode)

    def test_a_driver_only_verb_exits_71_without_reaching_the_stub(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            wrapper = self._copy(folder)
            with open(os.path.join(folder, "py"), "w", encoding="utf-8") as handle:
                handle.write(sys.executable)
            with open(os.path.join(folder, "stub"), "w", encoding="utf-8") as handle:
                handle.write(STUB)
            for verb in ("bind", "create", "init"):
                with self.subTest(verb=verb):
                    result = _run(["/bin/bash", wrapper, verb], _env())
                    self.assertEqual(result.returncode, WRAPPER_DRIVER_VERB, "exit %d, expected 71" % result.returncode)

    def test_the_wrapper_codes_stay_out_of_the_harness_and_stub_codes(self) -> None:
        taken = {
            value
            for name, value in vars(pc_exitcodes).items()
            if name.isupper() and isinstance(value, int) and not isinstance(value, bool)
        }
        self.assertNotIn(WRAPPER_UNCONFIGURED, taken)
        self.assertNotIn(WRAPPER_DRIVER_VERB, taken)


if __name__ == "__main__":
    unittest.main()
