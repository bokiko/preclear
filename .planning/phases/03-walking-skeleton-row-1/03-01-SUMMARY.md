---
phase: 03-walking-skeleton-row-1
plan: 01
subsystem: testing
tags: [matrix-driver, row-registry, dry-run, preflight, spend-ledger, decimal, python-stdlib, unittest]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "pc_flags (pinned argv, budget format, version gate), pc_preflight, pc_spike (harness home, runs root), pc_runroot, pc_stream, pc_testutil (fake and tripwire claude), the README and its drift tests"
provides:
  - "pc_rows: three layouts, eighteen row ids in acceptance order, StageSpec/RowSpec/RunContext/RowOutcome, row 1 as three stages (15 turns 0.30, 60 turns 1.30, 15 turns 0.40) with Decimal caps, exact whole-id lookup, evidence folder naming"
  - "pc_matrix: the driver CLI (--list, --row, --layout, --all, --dry-run, --claude, --budget, --authorize-retry), the claude-free gate (BLOCKED 12, FAIL 11, REFUSED 17, SKIP 10), check_stub, execute_row with a fixed exception-to-exit-code mapping, BLOCKED_FIXES equal to five README bullets"
  - "pc_preflight: run_preflight(claude_path=...), a cause on every non-OK result, the banner and the used path on OK, --claude on the command line"
  - "pc_spend: the file-locked matrix spend ledger (launch, settle, authorize lines), one attempt per stage, a row limit of 2.00 plus authorization caps, per-call delta cost and the row total"
  - "README: a Running one row section (flags, the claude-free gate, the three states, the five fix bullets, the spend gate in words) and Layout lines for the six new files"
affects: [03-02, 03-03, 03-04, 03-05, 03-06, phase-04]

actuals:
  tokens: 38684
  tasks: 3
  commits: 6
plan_head_before: db05d74c22fe8e55b19bb7a23b34e70f15aa713f
plan_head_after: d82a258380dc881888639cde36e758d8db8edf08

tech-stack:
  added: []
  patterns:
    - "An id reaches a path only after a whole-string pattern match and an exact registry match; every refusal is fixed text that never repeats the value"
    - "The dry run is proven process-free three ways: a tripwire claude first on PATH, an in-process trap on subprocess.Popen, and an assertion that the harness home was never created"
    - "The claude-free gate maps each condition to its own exit code (runs root 12, source 11, destination 17, precondition 10) before any process; BLOCKED results print a fix line equal to a README bullet"
    - "Ledger reservation: read, check and append under one exclusive file lock; a malformed line is refused (fail closed), never skipped; a pessimistic cap is replaced by the settled delta"

key-files:
  created:
    - tests/harness/pc_rows.py
    - tests/harness/pc_matrix.py
    - tests/harness/pc_spend.py
    - tests/harness/test_matrix_cli.py
    - tests/harness/test_matrix_preflight.py
    - tests/harness/test_spend.py
  modified:
    - tests/harness/pc_preflight.py
    - tests/harness/test_preflight.py
    - tests/harness/README.md

key-decisions:
  - "Ledger keys: row is the row id, stage is the stage key (row1-s2, from pc_rows.stage_key); the three line kinds have fixed key sets and every cost is decimal text"
  - "A second authorization for a stage is refused while an earlier one is still waiting for its retry, so authorizations cannot pile up (one authorization, one more attempt)"
  - "StageNotAttempted is a subclass of SpendRefused, so the driver can answer exit 2 for a never-attempted stage and exit 18 for every other spend refusal"
  - "BLOCKED causes no-config maps to the logged-out fix; the harness-home refusal prints BLOCKED with no fix line because the README holds exactly five fix bullets"
  - "Real run of row 1 ends, for now, at execute_row with FAIL 11 (the row runner is not available): pc_row1:run_row arrives in plan 03-02; every earlier step (gate, budget, stub, strict preflight) is already live and writes no ledger line"

patterns-established:
  - "Fix lines live once in BLOCKED_FIXES and once in the README as '- `cause`: line'; a test compares them byte for byte"
  - "Tests import the module under test inside each test so a missing module is one error per test, not one load failure"

requirements-completed: [HARN-01, HARN-02]

coverage:
  - id: C1
    description: "pc_matrix.py --list prints the three layouts then the eighteen row ids in acceptance order, one fixed-column line each (kind, id, stages, sessions, implemented), ASCII only, byte-identical on a second run; only row1-wrong-binding is implemented"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_cli.py (RegistryTests, ListTests)"
        status: pass
    human_judgment: false
  - id: C2
    description: "--dry-run --row row1-wrong-binding prints 3 stages, 2 sessions, the per-stage turns and caps, worst case 2.00, the 40-rule allowlist, the model and the destination name, exits 0, starts no process (tripwire claude and Popen trap silent), creates no harness home and no ledger"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_cli.py (DryRunTests)"
        status: pass
    human_judgment: false
  - id: C3
    description: "An unknown or unimplemented --row or --layout exits 2 with fixed text that never echoes the value; a prefix, another case, an empty value, a trailing space, a non-ASCII or control character and 65 characters are each refused; matching is exact and whole-id"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_cli.py (SelectionTests)"
        status: pass
    human_judgment: false
  - id: C4
    description: "--budget equal to the worst case is accepted and one cent less is refused with 18 before any process; float, exponent, three-decimal, zero, negative, empty and above-5.00 forms are refused with 18; worst case is exact Decimal arithmetic (three caps of 0.10 sum to 0.30)"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_preflight.py (BudgetBoundaryTests)"
        status: pass
    human_judgment: false
  - id: C5
    description: "The claude-free gate inside --dry-run gives BLOCKED 12 for a runs root under a home folder, FAIL 11 for a missing row source, 17 for an existing destination (a dangling symlink included) and SKIP 10 printed as SKIPPED with its reason, each a distinct code, with no process"
    requirement: HARN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_preflight.py (ThreeStateTests)"
        status: pass
    human_judgment: false
  - id: C6
    description: "--claude PATH feeds the preflight and the row context from one absolute path; the default PATH build outside the tested set answers 13 with the untested-version fix; a relative, missing, folder or non-executable path is BLOCKED 12; BLOCKED fix lines equal README bullets byte for byte; the stub check runs before the preflight on the real path only"
    requirement: HARN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_preflight.py (ExplicitClaudePathTests, ExplicitClaudeCliTests) and tests/harness/test_matrix_preflight.py (ClaudePathTests, StubGateTests, FixLineTests)"
        status: pass
    human_judgment: false
  - id: C7
    description: "execute_row maps BudgetRefused/SpendRefused to 18, RunRootCollision to 16, SanitizerError and ScannerError to 15, HomeRefused to 12, SpikeError and SpendError and ImportError to 11, StreamError to 19, with fixed text and no traceback; an unresolvable runner is FAIL 11"
    requirement: HARN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_preflight.py (ExecuteMappingTests)"
        status: pass
    human_judgment: false
  - id: C8
    description: "The matrix spend ledger reserves a stage cap under a file lock, refuses a second launch of a stage until an authorization line exists, lets one authorization permit exactly one more attempt and raise the row limit by that stage's cap, gives exactly one winner for concurrent launches, and refuses a malformed line instead of skipping it"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_spend.py (ReservationTests, AuthorizationTests, RowLimitTests, RaceTests)"
        status: pass
    human_judgment: false
  - id: C9
    description: "Per-call cost is a delta: the committed S2a stream gives 0.057689300000000006 and the committed S2b resume stream 0.002608 (cumulative 0.060297300000000005); the row total adds each session chain's final total once"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_spend.py (CostTests)"
        status: pass
    human_judgment: false
  - id: C10
    description: "--authorize-retry ROW-STAGE appends one authorization line, prints counts only, starts no claude process and refuses an unknown or never-attempted stage with exit 2; no task of this phase ran it"
    requirement: HARN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_matrix_cli.py (AuthorizeRetryTests)"
        status: pass
    human_judgment: false
  - id: C11
    description: "Zero model calls: the full suite is green on the PATH interpreter (3.14) and the system Python 3.9.6 with 864 tests (753 before), the leak gate reports 0 findings over 58 files, gitleaks dir over tests/harness is clean"
    requirement: HARN-02
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 864 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py' (Ran 864 tests, OK (skipped=3))"
        status: pass
    human_judgment: false
  - id: C12
    description: "Who typed an --authorize-retry line cannot be proven mechanically; the ledger line shows the flag ran, and the rule that only bokiko's word in the conversation may trigger it rests on the plan text and the paid-run checkpoint, not on code"
    requirement: HARN-01
    verification:
      - kind: other
        ref: "backstop: plan 03-06 paid-run checkpoint"
        status: unknown
    human_judgment: true

# Metrics
duration: not recorded (start time was not captured)
completed: 2026-10-29
status: complete
---

# Phase 3 Plan 01: The matrix driver front door and the spend ledger Summary

**One command under tests/harness lists every layout and row, dry-runs row 1 with zero processes and zero tokens, validates ids exactly, separates SKIP 10, FAIL 11 and BLOCKED 12 (13 for an untested build) with README-backed fix lines, points at the tested build by `--claude PATH`, refuses any real run whose `--budget` is below the printed worst case, and a file-locked spend ledger gives each stage one attempt with delta cost accounting.**

## Performance

- **Duration:** not recorded
- **Completed:** 2026-10-29
- **Tasks:** 3 (each a `test(03-01)` commit then a `feat(03-01)` commit; Task 1 is the tracer)
- **Files:** 6 new (3 modules, 3 test files), 3 modified (`pc_preflight.py`, `test_preflight.py`, `README.md`)
- **Suite:** 753 tests before, 864 after (111 new), `OK (skipped=3)`, 0 model calls, on both interpreters

## Accomplishments

- **Task 1, tracer (HARN-01).** `pc_rows.py` holds the registry (3 layouts, 18 row ids, row 1 as s1/s2/s3 with Decimal caps summing to exactly 2.00, 2 sessions). `pc_matrix.py` prints `--list` (22 lines, byte-identical across runs, ASCII), prints the dry-run plan, and refuses every near-miss id with exit 2 and fixed text. The tripwire claude, a `subprocess.Popen` trap and a missing-harness-home assertion all stay silent.
- **Task 2, three states (HARN-02, D-10, D-13).** `run_preflight` takes `claude_path` (absolute, executable file, never searched) and every non-OK result carries a cause. The gate runs inside `--dry-run` with no process: runs root under a home folder gives BLOCKED 12, a missing source FAIL 11, an existing destination 17, a precondition reason SKIP 10 printed as `SKIPPED: <reason>`. The real path orders selection, plan, gate, budget, stub check, strict preflight, runner; a real run without a sufficient `--budget` exits 18 first. The five fix lines in `BLOCKED_FIXES` are five README bullets, byte for byte.
- **Task 3, spend ledger (D-12, D-14).** `pc_spend.py` reserves under `fcntl.flock`, allows one attempt per stage, raises the row limit only by an authorization's cap, validates every ledger line strictly, and computes per-call cost as a delta (S2a 0.057689300000000006, S2b resume 0.002608). `--authorize-retry` appends one line and starts nothing.

## Task Commits

1. Task 1 tracer: `6edb5e8` test, `784142d` feat - registry, list, selection, dry run
2. Task 2: `6d5b1fd` test, `ef5288c` feat - claude path, gate, budget, three states, fix lines
3. Task 3: `497300f` test, `d82a258` feat - spend ledger, delta cost, retry authorization flag

## Deviations from Plan

### Auto-fixed Issues

None. The plan executed as written. Additions that stay inside the plan's intent:

**1. [Rule 2 - Missing critical functionality] Pending-authorization refusal**
- **Found during:** Task 3
- **Issue:** Nothing stopped two `--authorize-retry` calls in a row from granting two more attempts for one typed intent.
- **Fix:** `authorize_retry` refuses while an earlier authorization for the stage has not been used by a retry (SpendRefused, exit 18 from the driver). Tested in `AuthorizationTests`.
- **Files modified:** `tests/harness/pc_spend.py`, `tests/harness/test_spend.py`, `tests/harness/test_matrix_cli.py`

**2. [Rule 2 - Missing critical functionality] Ledger cross-checks**
- **Found during:** Task 3
- **Issue:** A hand-edited ledger could hold a settle without a launch, attempts out of order or an authorization for a stage never launched, and still parse line by line.
- **Fix:** `read_records` cross-checks the history (attempts count up from one, a settle follows its launch, a retry line follows a launch) and raises SpendError otherwise.
- **Files modified:** `tests/harness/pc_spend.py`

**3. Small API additions (no behaviour change to the plan):** `PreflightResult.claude` (the path actually used, so the driver passes one path onward), `StageNotAttempted(SpendRefused)`, `effective_records`, and `GateResult.cause`. The `--dry-run --all` closing line is `total: N row(s), N stage(s), N session(s), worst case X USD` as the action text wrote it; an empty registry prints `0 row(s), 0 stage(s), 0 session(s)`.

**Test edits between a test commit and its feat commit:** in `test_matrix_cli.py` the helper environment gained a scratch `PRECLEAR_RUNS_ROOT` (Task 2 made the gate part of the dry run, so the tests must not depend on the machine's default runs root) and the dry-run-all assertion reads the `total:` line instead of the last line (the gate line follows it).

README wording: the five fix lines and bullet text are exactly those the plan specifies; no wording was changed after being written.

## Authentication gates

None. No real `claude` was started; the only claudes executed were the scripted fake and tripwire of `pc_testutil`.

## Known Stubs

None in the shipped behaviour. One intentional gap: row 1's registry entry names the runner `pc_row1:run_row`, which plan 03-02 creates. Until then a real run of row 1 passes the gate, budget, stub check and strict preflight and then stops with `FAIL: the row runner is not available` (exit 11), writing no ledger line.

## Self-Check: PASSED

- Created files exist: `pc_rows.py`, `pc_matrix.py`, `pc_spend.py`, `test_matrix_cli.py`, `test_matrix_preflight.py`, `test_spend.py` under `tests/harness/`.
- Commits `6edb5e8`, `784142d`, `6d5b1fd`, `ef5288c`, `497300f`, `d82a258` are ancestors of HEAD; `git diff` against the plan's start lists only files under `tests/harness/`; `SKILL.md` is 11,994 bytes; `references/`, `tests/fixtures/` and the publication evidence folder are unchanged; no commit carries an attribution trailer and no hook was bypassed.
