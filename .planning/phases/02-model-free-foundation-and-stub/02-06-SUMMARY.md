---
phase: 02-model-free-foundation-and-stub
plan: 06
subsystem: testing
tags: [python-stdlib, unittest, checkpoint-v1, stub, flock, kill-switch, concurrency]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "plan 02-02 stub core (status, show, validate, update, lint, bind), the write-guard hook point and the replay suite"
provides:
  - "tests/harness/checkpoint_stub.py completed: note, handoff, create, init, the shared write guard with the exit 5 kill switch, the dedicated flock lock with the exit 6 timeout switch, atomic-write failure handling and one containment gate"
  - "tests/harness/test_stub_cli.py extended and tests/harness/test_stub_concurrency.py added: boundary, encoding, precision, read-only, ordering, containment, switch inventory and exit-code coverage proofs"
affects: [02-04 wrapper and branch table, 02-07 README, 02-08 findings, phase 3 runner]

actuals:
  tokens: 16000
  tasks: 3
  commits: 5
plan_head_before: 60b82162bdb5882a533de36d242ad46f894ceda1
plan_head_after: 9c752d3d47a3eafe6633cdd15f51f6db1a72f0b9

tech-stack:
  added: []
  patterns:
    - "write verbs wrapped once: guard (kill switch) first, then CKPT_HOME/.lock held across read, compare and atomic replace"
    - "create_exclusive: temp file in the target folder, fsync, os.link (fails if the target exists), unlink the stub's own temp"
    - "tests assert refusals by tree digest (sorted relative paths plus content hash) before and after"

key-files:
  created:
    - tests/harness/test_stub_concurrency.py
  modified:
    - tests/harness/checkpoint_stub.py
    - tests/harness/test_stub_cli.py

key-decisions:
  - "The kill switch arms only on CKPT_STUB_KILL_SWITCH equal to 1; it runs before the lock is taken and before any file is touched, so a refused write leaves the tree digest unchanged"
  - "CKPT_STUB_LOCK_TIMEOUT_MS must be digits only; unset gives 5000 ms, anything else (negative, text, a space, empty) is exit 2; read verbs never look at it and never create the lock file"
  - "The lock is the dedicated file CKPT_HOME/.lock opened with O_NOFOLLOW; the ledger is never locked because os.replace swaps its inode"
  - "handoff resolves the session ledger like note does (binding or --ledger, containment checked) and writes the body unchanged to CKPT_HOME/handoffs/ by exclusive creation; a name collision moves one millisecond on"
  - "create takes --task (required), --root, --project, --workstream (the last two go to the audit line only); init takes --ledger and --from; both live inside the existing UNCONFIRMED item for bind, create and init shapes"
  - "Every write path goes through require_within (realpath of both sides, component-aware prefix); a registered root outside CKPT_HOME is skipped by lint and refused by every verb"

patterns-established:
  - "Switch inventory test: the stub source names exactly two CKPT_STUB_ variables and every os.environ read is one of four known names"
  - "Exit-code table in test_stub_cli.py maps 0 to 6 and 64 to named tests and fails when a named test disappears"

requirements-completed: [STUB-01, STUB-02, STUB-04]

coverage:
  - id: D1
    description: "note appends a History entry after the checkpoint block without touching a block byte, adds a History heading when absent, and goes after earlier entries"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#NoteTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "CKPT_STUB_KILL_SWITCH=1 makes update, note, handoff, bind, create and init exit 5 with the kill-switch line after the brand line and an unchanged CKPT_HOME tree digest; read verbs, --version and --help ignore it; the values 0, empty, 2 and true leave it off"
    requirement: STUB-04
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#KillSwitchTests and DriverVerbTests.test_driver_kill_switch_stops_handoff_create_and_init"
        status: pass
    human_judgment: false
  - id: D3
    description: "Four parallel updates presenting one expected hash end with exactly one exit 0, three exit 3 and a ledger that lints OK; a lock really held by another process gives exit 6 within two seconds; invalid timeout values give exit 2"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_concurrency.py (RaceTests, LockTests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "A failed os.replace leaves the ledger bytes unchanged and no temporary file, and exits 1 with only the exception class name, for update and note"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#ReplaceFailureTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "handoff writes one new immutable file under CKPT_HOME/handoffs and never overwrites; create, init and bind build a bound, checkpointed ledger that status, show and lint accept; driver verbs refuse roots and ledgers outside CKPT_HOME"
    requirement: STUB-02
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py (HandoffTests, DriverVerbTests)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Boundary and encoding: blocks of 4,096 and 4,097 bytes, Authorization bodies of 600 and 601 characters, 600 CJK characters (1,800 bytes) passing the character cap and stopped by the byte cap in an oversized block, through validate and update"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#BoundaryTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "Timestamp truncation proven with nanosecond values at, just below and just above a millisecond edge and across a second edge; read verbs leave the tree digest unchanged and print identically twice; lint walks roots and ledgers in byte order identically across runs"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py (PrecisionTests, ReadOnlyTests, OrderingTests)"
        status: pass
    human_judgment: false
  - id: D8
    description: "Containment: a sibling directory named like CKPT_HOME plus a suffix, a dot-dot traversal after resolution, file, folder and root symlinks resolving outside, an unregistered ledger, a registered root outside CKPT_HOME and a handoffs folder resolving outside are each refused for show, update, note and handoff with an unchanged digest; a ledger inside a registered root still works"
    requirement: STUB-02
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#ContainmentTests"
        status: pass
    human_judgment: false
  - id: D9
    description: "The stub names exactly the two labelled CKPT_STUB_ switches, holds none of the wrapper's concerns, reads only four environment names, and every exit code 0 to 6 and 64 maps to an existing producing test"
    requirement: STUB-04
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#InventoryTests"
        status: pass
    human_judgment: false

duration: 55min
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 06: Stub Completion Summary

**The checkpoint-v1 stub now implements every verb (note, handoff, create, init added), takes one flock lock across each mutation, stops writes with the labelled exit 5 and 6 switches, and is proven against boundary, encoding, precision, read-only, ordering, containment and four-way race tests that produce every exit code from 0 to 6 and 64.**

## Performance

- **Duration:** about 55 min (start time not captured at launch)
- **Completed:** 2026-10-25
- **Tasks:** 3 (one tracer, two auto), 5 commits
- **Files:** 2 modified, 1 created, all under `tests/harness/`
- **Suite:** `tests/harness/selftest` went from 285 to 329 tests, all passing (3 skipped as before); the stub suite (`test_stub_*.py`, 103 tests) also passes under `/usr/bin/python3` 3.9.6

## Accomplishments

- A single write guard and one `write_verb` wrapper: every write verb checks `CKPT_STUB_KILL_SWITCH` first (exit 5, before lock and files), then holds `CKPT_HOME/.lock` for its whole body. Four racing updates without the lock ended `[0, 0, 0, 3]` (lost updates); with it they end `[0, 3, 3, 3]`.
- `note`, `handoff`, `create` and `init` implemented as the reference and the driver need; `bind` now sits behind the guard and the lock.
- One containment gate (`require_within`) for every write path; the sibling-prefix form is proven refused even when the sibling is hand-registered as a root.
- The proof suites carry teeth: each was run against a deliberately broken stub (naive prefix check, rounded milliseconds, bytes counted for Authorization, characters counted for the block, case-insensitive lint order) and failed as expected, then the stub was restored with `git checkout` of that one file.

## Task Commits

1. **Task 1 (tracer): write guard, exit 5 kill switch, note verb**
   - RED `914a71a` (test): note and kill-switch tests
   - GREEN `ff34cb4` (feat): `guard_write`, `append_history`, `verb_note`
2. **Task 2: lock, timeout switch, handoff, driver verbs, concurrency tests**
   - RED `8a0f415` (test): lock, handoff, driver, race tests
   - GREEN `e87aab5` (feat): `WriteLock`, `write_verb`, `create_exclusive`, `verb_handoff`, `verb_create`, `verb_init`, `parse_serialized`
3. **Task 3: boundary, encoding, precision, read-only, ordering, containment, inventory proofs**
   - `9c752d3` (test): the proofs; no stub change was needed (see TDD Notes)

**Plan metadata:** the SUMMARY commit follows this file.

## Files Created/Modified

- `tests/harness/checkpoint_stub.py` - completed stub; docstring now lists the driver-only verbs, both switches, failure handling and the updated UNCONFIRMED wording
- `tests/harness/test_stub_cli.py` - adds `tree_digest`, `run_in_process`, NoteTests, KillSwitchTests, HandoffTests, DriverVerbTests, ReplaceFailureTests, BoundaryTests, PrecisionTests, ReadOnlyTests, OrderingTests, ContainmentTests, InventoryTests
- `tests/harness/test_stub_concurrency.py` - RaceTests (barrier-file release of four processes) and LockTests (contended lock, zero timeout, invalid values, read verbs ignore the variable)

## Decisions Made

See `key-decisions` above. Points the branch table of plan 02-04 should know, all inside the existing UNCONFIRMED items (no new label): `note` on a ledger without a block exits 2; `handoff` needs a bound session or `--ledger` (exit 2 otherwise); an empty `CKPT_STUB_LOCK_TIMEOUT_MS` is a usage error while an empty `CKPT_STUB_KILL_SWITCH` is simply off.

## TDD Notes

- The plan is `type: execute` with `tdd="true"` tasks and `workflow.tdd_mode` is not enabled, so the `tdd-red-evidence` classifier (`gsd_run`) was not available or required; RED was recorded from real `unittest` runs and assessed by reading the failures.
- **Task 1 RED (semantic assessment):** 5 note/kill-switch tests failed on the planned assertions (`note` exited 1 "not implemented", update exited 0 where 5 was expected, `--ledger` rejected by the parser); no load, import or fixture fault.
- **Task 2 RED (semantic assessment):** 10 CLI and 6 concurrency tests failed on the planned assertions; the race failed as `[0, 0, 0, 3] != [0, 3, 3, 3]`, a genuine lost-update result. **Unexpected green, investigated:** the two `ReplaceFailureTests` already passed at RED because plan 02-02's `atomic_write` and the exit 1 mapping in `main` already deliver that behaviour. They are kept as proofs of it.
- **Task 3 (unexpected green, investigated):** the proof tests passed on first run because the stub from Tasks 1 and 2 already satisfied them (the plan says to edit the stub only when a proof exposes a defect; none did). To show the tests are not vacuous they were run against five deliberate stub mutations (listed above) and each failed. Task 3 therefore has a `test(02-06)` commit and no `feat` commit, which is a TDD gate gap by shape, not a skipped step.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan 02-02 hygiene test forbade any `CKPT_STUB_` text**
- **Found during:** Task 1
- **Issue:** `test_stub_has_no_call_log_no_injection_and_no_switches_yet` asserted `CKPT_STUB_` absent from the stub, which this plan makes false by design.
- **Fix:** Replaced by an allowed-names check in Task 1 and by the exact-equality inventory test in Task 3. The `armed` word check was dropped; the call-log and injection words are still forbidden.
- **Files modified:** `tests/harness/test_stub_cli.py`
- **Committed in:** `914a71a`, `9c752d3`

**2. [Rule 1 - Bug] Two of my own new tests changed the digest they compared**
- **Found during:** Task 2 GREEN
- **Issue:** the driver-refusal test wrote its input file under `CKPT_HOME` after taking the digest, and ran on an unbound rig where the first (refused) write verb creates the empty `.lock` file; the read-verb lock test used a bound rig, where `.lock` already existed from bind.
- **Fix:** input files are written before the digest, the refusal test uses a bound rig (bind is a write verb, so the lock file already exists), and the read-verb test uses an unbound rig so `.lock` can be proven absent.
- **Files modified:** `tests/harness/test_stub_cli.py`, `tests/harness/test_stub_concurrency.py`
- **Committed in:** `e87aab5`

---

**Total deviations:** 2 auto-fixed (both Rule 1, test-side); no stub behaviour changed by them.
**Impact on plan:** none on scope.

### Interpretations (not deviations)

- Plan 02-02's parser accepted `--ledger --project --workstream --task` on both `create` and `init`; this plan narrows them to the shapes the plan text gives (`create --task T [--project P] [--root R]`, `init --ledger P --from F`, plus `--workstream` on create). The docstring item "bind, create and init argument shapes" is reworded accordingly and stays UNCONFIRMED.
- The plan's example commit subjects are plain sentences; the subjects use `test(02-06):` and `feat(02-06):` as wave 1 did.
- `gitleaks` flagged a `.pyc` once, produced by a debug run of mine without `-B`; the file was untracked and I removed that one generated file.

## Issues Encountered

None beyond the items above. The race test is timing-independent: the lock serialises the four processes whatever order they start in, and it passed on five consecutive runs.

## Known Stubs

None. `note`, `handoff`, `create` and `init` no longer exit 1; `guard_write` is the live kill switch.

## Threat Flags

None. The only new filesystem surface is `CKPT_HOME/.lock` (opened `O_NOFOLLOW`) and `CKPT_HOME/handoffs/`, both inside the plan's `CKPT_HOME` boundary (T-02-07, T-02-08, T-02-49 mitigated and tested; T-02-12 boundary tests added).

## Self-Check: PASSED

- All three files exist: `tests/harness/checkpoint_stub.py`, `tests/harness/test_stub_cli.py`, `tests/harness/test_stub_concurrency.py`
- Commits `914a71a`, `ff34cb4`, `8a0f415`, `e87aab5`, `9c752d3` are ancestors of HEAD
- `tests/harness/selftest` 329 tests OK; stub suite OK under 3.14 and `/usr/bin/python3` 3.9.6; `gitleaks dir tests/harness` clean; frozen paths unchanged since `56e155c`; no attribution trailer in any commit message
