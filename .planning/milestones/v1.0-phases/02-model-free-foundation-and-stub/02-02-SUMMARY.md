---
phase: 02-model-free-foundation-and-stub
plan: 02
subsystem: testing
tags: [python-stdlib, unittest, checkpoint-v1, stub, replay, wrapper-log-miner]

requires:
  - phase: 01-publication-gate
    provides: committed publication evidence (wrapper-calls.log files, traces, snapshots) and the leak, identity and attribution hooks
provides:
  - "tests/harness/checkpoint_stub.py: single-file stub of checkpoint-v1 (status, show, validate, update, lint, bind) behind a CKPT_HOME refusal and a one-line stderr brand"
  - "tests/harness/pc_mine.py and replay-cases.json: nine mined cases, fifteen recorded calls, canonical JSON, --check"
  - "zero-token replay of every recorded call against the stub with a test-side second writer for the exit 3 cases"
affects: [02-04 wrapper and branch table, 02-06 stub completion, 02-08 findings, phase 3 runner]

actuals:
  tokens: 29000
  tasks: 2
  commits: 4
plan_head_before: c3c615305b83d704d64fa3080c57046176405ce5
plan_head_after: d23257ff1c90edcb068f895b413e49827cc2b919

tech-stack:
  added: []
  patterns:
    - "flat tests/harness modules, Python 3.9 floor, standard library only, unittest"
    - "scratch CKPT_HOME per replay case, state built with the stub's own bind verb"
    - "one normalisation applied to both sides, masked values checked by shape first"

key-files:
  created:
    - tests/harness/checkpoint_stub.py
    - tests/harness/pc_mine.py
    - tests/harness/replay-cases.json
    - tests/harness/test_mine.py
    - tests/harness/test_stub_cli.py
    - tests/harness/test_stub_replay.py
  modified: []

key-decisions:
  - "A section hash is the SHA-256 hex of the body as UTF-8 with trailing newlines stripped (D-07); the four path-free committed hashes reproduce exactly"
  - "replay-cases.json records an --expect-section value as a last-show reference (argv token <last-show-hash>) and each --from file as a committed snapshot source plus a replay path"
  - "An update with a recorded exit 3 replays the input the committed conflict file records under Yours (not applied), because the snapshot copy of goal.md is the model's last version"
  - "bind refuses a ledger that is not strictly inside CKPT_HOME; the root registered is the ledger's own folder"
  - "validate and update share one check_block routine, so the 600-character and 4,096-byte limits and the six-section rule cannot differ between them"

patterns-established:
  - "Brand once on stderr in main() before parsing, so every path (help, version, usage error, refusal) carries exactly one marker line"
  - "Every write verb calls guard_write first; plan 02-06 turns it into the kill switch and the lock"

requirements-completed: [STUB-01, STUB-02, STUB-03]

coverage:
  - id: D1
    description: "pc_mine mines all nine committed wrapper-calls.log files (five non-empty, fifteen calls, four empty cases) in file line order, byte-identical on a second run and equal to the committed replay-cases.json"
    requirement: STUB-03
    verification:
      - kind: unit
        ref: "tests/harness/test_mine.py (MineInventoryTests, ParseLogTests, DeterminismTests, WritesNothingTests)"
        status: pass
      - kind: other
        ref: "python3 -E -s -B tests/harness/pc_mine.py --check"
        status: pass
    human_judgment: false
  - id: D2
    description: "The stub refuses to run without CKPT_HOME (unset, empty, missing path, a file) with exit 64, brands itself with one stderr line, and adds nothing to stdout; --version and --help work without it"
    requirement: STUB-02
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#NoCkptHomeTests and BrandTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "Core stub verbs status, show, validate, update, lint and bind with 64-character SHA-256 section hashes, six-section validation, the hash-guarded update and the conflict file on exit 3"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py (StatusTests, ShowTests, ValidateTests, UpdateTests, LintTests, ContainmentBasicsTests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "All fifteen recorded calls replay against the stub with the recorded exit codes; thirteen match their committed decisive output after the stated normalisation, two are asserted by exit code plus validate pattern or committed conflict file"
    requirement: STUB-03
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_replay.py#ReplayTests.test_replay_every_mined_call_against_the_committed_outputs"
        status: pass
    human_judgment: false
  - id: D5
    description: "The stub docstring lists every behaviour FA-1 names as UNCONFIRMED so the branch table in plan 02-04 can mirror it"
    requirement: STUB-01
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py#SourceHygieneTests.test_docstring_lists_every_unconfirmed_behaviour"
        status: pass
    human_judgment: true
    rationale: "A test proves the named behaviours are mentioned; whether the wording is the right reading of the reference is a judgment the branch-table review in plan 02-04 makes"

duration: 20min
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 02: Replay Miner and Checkpoint Stub Core Summary

**A single-file checkpoint-v1 stub (status, show, validate, update, lint, bind) behind a CKPT_HOME refusal, plus a miner that turns the nine committed wrapper logs into replay-cases.json and a zero-token replay that reproduces all fifteen recorded calls.**

## Performance

- **Duration:** about 20 min (start time not captured at launch; estimated from worktree creation)
- **Completed:** 2026-10-25
- **Tasks:** 2 (tracer plus one auto), each as a RED then GREEN commit pair
- **Files created:** 6 (three modules, one data file, three test modules; no file modified outside tests/harness)

## Accomplishments

- `pc_mine.py` reads the nine `wrapper-calls.log` files (five non-empty with fifteen calls, four empty), recovers argv with `shlex.split`, keeps file line order, and prints canonical JSON; `--check` compares with the committed `replay-cases.json` and the file is byte-identical on a second run.
- `checkpoint_stub.py` refuses to run without a valid `CKPT_HOME` (exit 64), prints exactly one stub-marker line on stderr per invocation and nothing of the brand on stdout (the `--version` banner excepted), and keeps all state under `CKPT_HOME`.
- The section hash derivation (SHA-256 of the UTF-8 body, trailing newlines stripped) reproduces the four path-free hashes in committed evidence; every displayed hash equals the digest of its displayed body.
- Hash-guarded `update`: a stale hash exits 3, writes only the conflict file in the committed layout and leaves the ledger bytes unchanged; a current hash replaces one section and rewrites the begin marker.
- The replay rebuilds each case in a scratch `CKPT_HOME`, plays the concurrent writer test-side from the committed conflict files, and passes 15 of 15 calls (13 against committed output, 2 by exit code plus pattern or conflict file).

## Task Commits

1. **Task 1: Tracer, mine the logs and run status from a scratch CKPT_HOME**
   - RED `ecbbf0e` (test): miner, CLI refusal/brand and status replay tests, failing with the implementation absent
   - GREEN `b5800aa` (feat): `pc_mine.py`, `replay-cases.json`, stub with status and bind
2. **Task 2: Show, validate, lint and update with the conflict path, and the full replay**
   - RED `9c60577` (test): show/validate/update/lint tests and the full fifteen-call replay, failing on `show is not implemented`
   - GREEN `d23257f` (feat): the remaining verbs and the replay passing

**Plan metadata:** the SUMMARY commit follows this file.

## Files Created/Modified

- `tests/harness/checkpoint_stub.py` - single-file stub, mode 100755, stdlib only, UNCONFIRMED list in the module docstring
- `tests/harness/pc_mine.py` - miner (`parse_log`, `parse_trace`, `mine`, `canonical_json`), writes nothing
- `tests/harness/replay-cases.json` - canonical JSON, schema 1, nine cases, inventory 9/5/4/15
- `tests/harness/test_mine.py` - inventory, ordering, empty cases, determinism, no write-mode open
- `tests/harness/test_stub_cli.py` - refusal, brand, exit codes 0/2/3/4/64, status, show, validate, update, lint, containment basics, source hygiene
- `tests/harness/test_stub_replay.py` - the replay and its listed normalisation

## Decisions Made

- Hash derivation, schema shape and the bind containment rule are listed in `key-decisions` above. `replay-cases.json` fields: `calls[].argv`, `exit`, `position`, `refs` (hash references), `inputs` (replay path plus committed source), `output` (kind `status-before`, `trace` or `none`), and per case `ledgers`, `bound_ledger`, `conflict_files`, `session_id`, `writer2_session`. Plan 02-04's `canonical_commands` can read `cases[].calls[].argv` directly.
- The two switches for exits 5 and 6, the lock, `note`, `handoff`, `create` and `init` are not here; those verbs exit 1 with "not implemented in this build step". That is the plan's split (plan 02-06), recorded under Known Stubs.

## TDD Notes

- The plan is `type: execute` with `tdd="true"` tasks, and `workflow.tdd_mode` is not enabled, so the `tdd-red-evidence` classifier gate was not run. RED was recorded from the real `unittest` runs: each RED commit has target tests failing on the planned behaviour (exit 64, `show` exit 0, the replay count) rather than on a load fault, apart from the replay module whose class setup asserts the miner and `replay-cases.json` exist.
- Candour about order: the implementation drafts existed on disk before the first RED commit. To produce a genuine RED I moved the implementation files out of the tree, ran the tests (failures: miner 1 failure and 4 errors, CLI 17 failures and 4 errors, replay 1 load-class error), committed only the tests, then restored the files. Task 1's stub was derived from the full stub by removing the show, validate, update and lint verbs so the Task 1 GREEN commit matches the Task 1 scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan defect] The snapshot goal.md is not what the first conflicting update presented**
- **Found during:** Task 2 (full replay)
- **Issue:** The plan copies each recorded input from the snapshot. The snapshot `goal.md` is the model's last version, written after it read the first conflict, so replaying update 1 with it made the conflict file's `Yours (not applied)` differ from the committed one (the committed update 2 conflict file matches the snapshot).
- **Fix:** For an update with a recorded exit 3 the replay writes the text the committed conflict file records under `Yours (not applied)`; for the last conflict it asserts that text equals the snapshot input, for the earlier one that the snapshot extends it. The miner and `replay-cases.json` are unchanged.
- **Files modified:** `tests/harness/test_stub_replay.py`
- **Verification:** replay passes, conflict files match after the stated normalisation
- **Committed in:** `d23257f`

**2. [Rule 1 - Bug] Two RED checks asserted more than their task could deliver**
- **Found during:** Task 1 GREEN
- **Issue:** The no-write check flagged `str.replace` as if it were `os.replace`; one usage test needed the `show` and `update` verbs that belong to Task 2.
- **Fix:** The write check now flags only `os`/`shutil` mutation calls and `write_text`/`write_bytes`; the two later-verb assertions moved out of the Task 1 version (the full version in the Task 2 RED commit keeps them).
- **Files modified:** `tests/harness/test_mine.py`, `tests/harness/test_stub_cli.py`
- **Committed in:** `b5800aa`

**3. [Rule 1 - Bug] A Task 2 test used an unregistered ledger root**
- **Found during:** Task 2 GREEN
- **Issue:** The committed-hash test built its rig without bind, so no root was registered and the stub (correctly) refused the ledger.
- **Fix:** Use a bound rig and overwrite the ledger text with the committed ledger.
- **Files modified:** `tests/harness/test_stub_cli.py`
- **Committed in:** `d23257f`

---

**Total deviations:** 3 auto-fixed (all Rule 1, test or plan-defect corrections; no stub behaviour changed by them)
**Impact on plan:** None on scope. Deviation 1 means one recorded input is replayed from the conflict file, not the snapshot, which the replay test docstring states.

### Interpretations (not deviations)

- The plan says the refusal leaves "exactly one brand line" on stderr and also specifies the message `checkpoint: CKPT_HOME is not set to an existing directory`. The stub prints both; the tests assert exactly one brand line (first line) plus the message, and an empty stdout.
- Commit subjects use the `test(02-02):` and `feat(02-02):` prefixes of the git-integration reference instead of the plan's plain example sentences. They are still one imperative sentence, with no attribution trailer; the hooks accepted all four.

## Issues Encountered

- `gitleaks` flagged a `generic-api-key` on a line pairing the label "Evidence & key paths" with a full digest. The replay test now holds the four path-free section bodies and 12-character digest prefixes and derives the full digest itself.
- Two directly measured facts the plan leaves open: the committed show output cannot tell whether it ends with a blank line, so trace comparisons strip trailing newlines on both sides; status comparisons against `status-before.txt` are byte for byte.

## Known Stubs

- `note`, `handoff`, `create` and `init` exit 1 ("not implemented in this build step") in `tests/harness/checkpoint_stub.py`; `guard_write` is a pass-through. These are intentional and owned by plan 02-06 (the two labelled exit 5 and 6 switches and the lock come with it). They do not block this plan's goal, which uses only status, show, validate, update, lint and bind.

## Threat Flags

None. The stub's only filesystem reach outside the ledger folder is the `--from` file it reads, already accepted in T-02-09; it writes only under `CKPT_HOME`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-04 can build the wrapper on this stub (`--session` is accepted after the verb) and read the argv sequences from `replay-cases.json`.
- Plan 02-06 completes the stub: the verbs above, exit codes 1, 5 and 6, the lock, and the numeric-limit and containment proofs. `guard_write` and the `NOT_IMPLEMENTED` tuple are the two places it hooks in.
- Verified: the full unittest suite (79 tests) passes on Python 3.14 and the stub tests (59) pass on the system Python 3.9.6; `pc_mine.py --check` exits 0; `gitleaks dir tests/harness` is clean; SKILL.md (11,994 bytes), `references/`, `tests/fixtures/` and `tests/evidence/` are unchanged since commit 56e155c; no commit message carries an attribution trailer.

---
*Phase: 02-model-free-foundation-and-stub*
*Completed: 2026-10-25*

## Self-Check: PASSED

All six created files exist on disk; commits ecbbf0e, b5800aa, 9c60577 and d23257f are ancestors of HEAD; the plan-level verification commands were re-run and pass.
