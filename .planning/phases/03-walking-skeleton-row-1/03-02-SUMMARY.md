---
phase: 03-walking-skeleton-row-1
plan: 02
subsystem: testing
tags: [row-1, seed, stage-chain, resume-line, delta-cost, init-manifest, instruction-audit, scripted-claude, python-stdlib, unittest]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_rows (RunContext, RowOutcome, StageSpec, registry, stage_key), pc_matrix.execute_row (resolves pc_row1:run_row), pc_spend (append_launch, settle, call_cost, row_total), the three-state preflight"
  - phase: 02-model-free-foundation-and-stub
    provides: "pc_flags (pinned argv, env scrub, allowlist), pc_spike (run_claude, s1_evaluation, hit_candidates, binary_defines, materialize helpers), pc_manifest, pc_runroot, pc_stream, pc_sanitize, pc_hooklog, pc_testutil, the stub and the logging wrapper"
provides:
  - "pc_row1: seed_row1 (the committed wrong-binding setup in a fresh run root), take_snapshot, run_stage (launch line, process, settle line, raw bytes, record, snapshot), run_row (three stages with stop rules and the pre-spend order), finish, extract_resume_line, caller_map, stage_assertions, evaluate_stage, BinaryScan, describe_evaluation, isolation_mode, read_stage_prompts"
  - "pc_testutil: make_scripted_claude (a scripted multi-stage fake claude), default_row1_stages, stages_with, RowRig (a temporary repository, harness home, runs folder, user home and environment)"
  - "data/row1-s1-prompt.md and data/row1-plan.md; row 1 registry sources name both"
  - "README: six Layout lines and a What a row run does subsection"
affects: [03-03, 03-04, 03-05, 03-06, phase-04]

actuals:
  tokens: 35182
  tasks: 3
  commits: 6
plan_head_before: c6b8b039a39ce8c4a8d101adf08c4211198e47c1
plan_head_after: 26afe8023cc66c705cf6046ce3906c0c6323c47c

tech-stack:
  added: []
  patterns:
    - "Every refusal that can precede spend comes before the first ledger line: destination (17), run root (16), sanitizer and deny entries (15), readable ledger, seed, git lookup; then one launch line before and one settle line after each process"
    - "The command of every stage is built only by pc_flags; the stage record, the raw bytes and the boundary snapshot are written whatever the outcome"
    - "Per-stage hook-log slices: the boundary is the line count the previous stage record stored, so a shared hook log never mixes stages"
    - "One scripted claude plays a list of stage scripts by a call counter file; tests change one stage with stages_with"

key-files:
  created:
    - tests/harness/pc_row1.py
    - tests/harness/data/row1-s1-prompt.md
    - tests/harness/data/row1-plan.md
    - tests/harness/test_row1_seed.py
    - tests/harness/test_stages.py
    - tests/harness/test_row1_assertions.py
  modified:
    - tests/harness/pc_testutil.py
    - tests/harness/pc_rows.py
    - tests/harness/README.md

key-decisions:
  - "A resume line that breaks a bound (over 2000 bytes or holding a NUL) gives the empty string and is not replaced by an earlier valid fence: the rule is about the last candidate, and a doubtful line must not start a paid third process"
  - "run_row maps SanitizerError and ScannerError to RowOutcome 15 itself; RunRootCollision is left to propagate so the driver answers 16; a taken destination is RowOutcome 17"
  - "A stage that completes cleanly but fails an assertion stops the chain with 11 and prints the assertion lines (ids, yes or no, counts); a stream without a single result is 19; timeout, non-zero exit, non-success subtype, error flag and a terminal reason other than completed are 11"
  - "The hook slice boundary is the total line count of raw/hooklog.jsonl stored in the previous stage record (hooklog_lines), so s3 sees only its own entries"
  - "isolation_mode() is defined with the seed (the seed records it in raw/run.json) and not only with the assertions; it is read from pc_flags.ISOLATION_CLAIM, never typed"

patterns-established:
  - "Stage record keys (raw/<stage>.record.json): stage, session_id, resume, returncode, timed_out, wall_seconds, attempt, cap, max_turns, version, wrapper_calls, hooklog_lines, snapshot, snapshot_copy_skipped, subtype, turns, delta, cumulative, cumulative_consistent, usage, problem, stdout_sha256, stdout_size, evaluation, assertions, hook_entries, audit_source"
  - "Run-root files later plans read: raw/run.json, status-before.txt, lint-before.txt, s1/s2/s3 .stdout .stderr .record.json, chain.json (marker found or NO-RESUME-LINE, the line itself, its byte size), hooklog.jsonl; snaps/snap-0-setup, snap-1-after-work, snap-2-after-preclear, snap-3-after-resume"

requirements-completed: [HARN-05, HARN-07]

coverage:
  - id: C1
    description: "seed_row1 builds the committed row 1 setup in a fresh run root with exclusive creation: the plan digest equals the committed setup digest, no project thoughts/ledgers folder, ledger A named in the configuration and ledger B bound to the work session both carry the real project path, wrapper/calls.log is empty, status-before and lint-before are the stub's own output, a second seed raises FileExistsError and the repository tree digest is unchanged, bad arguments and a missing source are refused before anything is created"
    requirement: HARN-07
    verification:
      - kind: unit
        ref: "tests/harness/test_row1_seed.py (SeedTests)"
        status: pass
    human_judgment: false
  - id: C2
    description: "Every stage runs through pc_flags: s1 has --session-id U1, 15 turns, 0.30; s2 has --resume U1 and no --session-id, 60 turns, 1.30; s3 has a new uuid4 session id, 15 turns, 0.40; all three carry --permission-mode default, the 40-rule allowlist, the pinned model, no skip-permissions flag, no hook-events flag, the prompt on stdin, the project folder as cwd and a scrubbed environment holding CLAUDE_CONFIG_DIR, CKPT_HOME and DISABLE_AUTOUPDATER"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_row1_seed.py (TracerTests) and tests/harness/test_stages.py (ChainTests)"
        status: pass
    human_judgment: false
  - id: C3
    description: "The s3 prompt is the resume line from the s2 result, byte for byte with no trailing newline; extract_resume_line takes the last fenced single line starting with the word Resume, accepts a language tag, ignores multi-line blocks and other lines, gives the empty string for a line over 2000 bytes, a NUL or no fence; with no line the run records NO-RESUME-LINE, runs no third process and ends with 0"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_stages.py (ChainTests, ResumeLineTests)"
        status: pass
    human_judgment: false
  - id: C4
    description: "Each stage writes one launch line before its process and one settle line after it; the s2 settle holds its own delta (0.06) and the cumulative (0.09), the row total is the s2 cumulative plus the s3 total (0.13), a missing since-last-result mapping gives the same delta by subtraction, a cumulative that disagrees with previous plus delta is recorded as cumulative-consistent no"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_stages.py (ChainTests, CostTests)"
        status: pass
    human_judgment: false
  - id: C5
    description: "The chain stops at the first stage that timed out (its settle keeps the cap), exited non-zero, has a non-success subtype, an error flag or a terminal reason other than completed (all 11), or whose stream has no single result event or malformed lines (19); raw bytes are kept; later stages are never launched; permission denials do not stop the chain"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_stages.py (StopRuleTests, ChainTests)"
        status: pass
    human_judgment: false
  - id: C6
    description: "Pre-spend refusals come before any ledger line: an existing destination (a dangling symlink included) is 17 with no run root, a taken run root is 16, a sanitizer that cannot be built is 15 with no process, a malformed spend ledger is refused before the first stage; the caller map sends the run root and the auto-memory folder to their tokens and the runs root, its parent and a two-component users or home prefix to the scratch token, and a test tells the mapped and unmapped sanitizer apart"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_stages.py (PreSpendTests, CallerMapTests)"
        status: pass
    human_judgment: false
  - id: C7
    description: "The init manifest is asserted after every stage in the fixed order of twelve ids; each synthetic variant fails exactly its own id (the session id has an init and a result variant); an absent memory_paths, an empty skills list or a missing key fails and never passes vacuously; the memory path compares by realpath with a trailing slash tolerated, a name-prefix sibling rejected and a symlinked equivalent accepted"
    requirement: HARN-07
    verification:
      - kind: unit
        ref: "tests/harness/test_row1_assertions.py (InitAssertionTests)"
        status: pass
    human_judgment: false
  - id: C8
    description: "Hook-log slices are per stage: a fresh stage with no instruction entry is not assertable and stops the chain; a resumed stage with none is recorded as not asserted on resume and passes; a User entry outside the harness config folder or a Project entry outside the run root fails in either kind; the binary is read only when the init lists show a candidate hit, once per run, and a name the binary defines is a collision and not a leak"
    requirement: HARN-07
    verification:
      - kind: unit
        ref: "tests/harness/test_row1_assertions.py (HookAuditTests, BinaryScanTests, ChainAssertionTests)"
        status: pass
    human_judgment: false
  - id: C9
    description: "The isolation mode strict is derived from the pinned isolation claim (first word after its prefix), recorded in raw/run.json at seed, and each stage record carries the assertion triples, the entry counts and the evaluation status"
    requirement: HARN-07
    verification:
      - kind: unit
        ref: "tests/harness/test_row1_seed.py (SeedTests) and tests/harness/test_row1_assertions.py (ChainAssertionTests)"
        status: pass
    human_judgment: false
  - id: C10
    description: "Zero model calls: the full suite is green on the PATH interpreter (3.14) through the selftest shim and on the system Python 3.9.6 with 926 tests (864 before), the leak gate reports 0 findings over 64 files, gitleaks dir over tests/harness is clean, the real-repository dry run exits 0 with a tripwire claude silent, and nothing outside tests/harness and the planning folder changed"
    requirement: HARN-07
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 926 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py' (Ran 926 tests, OK (skipped=3))"
        status: pass
    human_judgment: false
  - id: C11
    description: "Whether a resumed 2.1.310 session fires the InstructionsLoaded hook again is unobserved; the rule records the per-stage entry count and stops only on a boundary violation, and the real run in plan 03-06 settles the question"
    requirement: HARN-07
    verification:
      - kind: other
        ref: "backstop: plan 03-06 paid-run checkpoint"
        status: unknown
    human_judgment: true
  - id: C12
    description: "Whether --max-budget-usd on a resumed call counts the session's cumulative cost is unobserved; the 0.30, 1.30 and 0.40 split is safe under either reading and no capture can confirm it before the paid run"
    requirement: HARN-05
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

# Phase 3 Plan 02: The row 1 seed, the three-stage chain and the init and instruction-audit assertions Summary

**Row 1 now runs end to end against a scripted claude: a real seed of the committed wrong-binding setup, three `claude -p` stages (work turn, `/preclear` resumed on the same session, a fresh session that pastes the printed resume line) each behind a ledger reservation with delta cost, and the init manifest plus instruction audit asserted after every stage with the isolation mode recorded as strict. No model was called.**

## Performance

- **Duration:** not recorded
- **Completed:** 2026-10-29
- **Tasks:** 3 (each a `test(03-02)` commit then a `feat(03-02)` commit; Task 1 is the tracer)
- **Files:** 6 new (`pc_row1.py`, two data files, three test files), 3 modified (`pc_testutil.py`, `pc_rows.py`, `README.md`)
- **Suite:** 864 tests before, 926 after (62 new: 13 seed, 29 chain, 20 assertions), `OK (skipped=3)`, 0 model calls, on both interpreters

## Accomplishments

- **Task 1, tracer (HARN-07, D-01, D-03, D-04).** `seed_row1` builds the project (configuration filled from the committed fixture, the three-step plan whose sha256 equals the committed setup digest, a git repository on main, the frozen skill untracked), the wrapper folder with an empty `calls.log`, two ledgers (A named in the configuration, B bound to the work session through the stub's own bind, both carrying the real project path), the stub's status and lint output, the audit hook and `raw/run.json`. `take_snapshot` writes the filtered manifest, git status, ledger and binding listings and copies. `run_stage` proves the whole stage architecture against `make_scripted_claude`.
- **Task 2, chain (HARN-05, D-02, D-12, D-14).** `run_row` orders every refusal before the first ledger line, runs s1, s2 (resumed) and s3 (new session, resume line as the whole prompt), computes per-call delta cost, stops on the first stage that is not a clean success, and ends with fixed-text lines and the row total. `caller_map` sends the runs root, its parent and a two-component users or home prefix to the scratch token.
- **Task 3, assertions (HARN-07).** `stage_assertions` returns twelve triples in a fixed order; `evaluate_stage` stops on any false or not-assertable triple; the resume rule records silence as a fact; `BinaryScan` reads the binary once and only on a candidate hit. The README gained six Layout lines and a What a row run does subsection (no figure, no path).

## Task Commits

1. Task 1 tracer: `e9f040c` test, `2bed3d2` feat - seed, snapshots, stage s1, scripted claude and RowRig
2. Task 2: `b096f53` test, `dde9972` feat - three-stage chain, resume line, delta cost, stop rules, pre-spend order, caller map
3. Task 3: `b67acf8` test, `26afe80` feat - init and audit assertions, isolation mode, registry sources, README

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The runs folder was never created on the real driver path**
- **Found during:** Task 2, the `main` test (`--claude`, `--budget`) returned 11 with "a run folder could not be created"
- **Issue:** `pc_matrix.main` computes the runs root through `pc_spike.runs_root`, which creates nothing; only the rig had created it, so the first real run on a fresh machine would have failed after the gate.
- **Fix:** `run_row` calls `pc_spike.ensure_runs_root` right before allocating the run root (after the destination check, so a refused destination still creates nothing).
- **Files modified:** `tests/harness/pc_row1.py`
- **Commit:** `dde9972`

### Additions inside the plan's intent

- `isolation_mode()` is defined in Task 1 (the seed records it in `raw/run.json`); Task 3 tests it against the claim text.
- `StageResult` gained two defaulted fields (`evaluation`, `hooklog_lines`) and `run_stage` two keyword parameters (`hook_start`, `scan`) in Task 3, as the per-stage hook slice needs the previous boundary and the run shares one `BinaryScan`.
- The plan's "stage-prefixed folder" snapshot exclusion is implemented as: a top-level run-root folder whose name starts with `stage`.
- A last resume-line candidate that breaks a bound gives the empty string rather than falling back to an earlier fence (a conservative reading of "at most 2000 bytes with no NUL"); a test fixes it.
- `run_row` takes the s2 prompt and s1 prompt through `read_stage_prompts`; the committed `s2-preclear-prompt.md` is read in place and compared byte for byte in a test.

### Test edits between a test commit and its feat commit

In `test_stages.py`: the expected cumulative text for a float total of 0.20 is `0.2` (the stream carries the number, not its trailing zero); the users-prefix check for a home-rooted path was split into a direct test of the prefix rule (the `/home` root is an automount link on this machine, so a realpath of a made-up path moved); an unclosed file in a timeout test now uses a `with` block; unused imports were dropped.

### Scripted-claude operations later plans rely on

`make_scripted_claude(directory, config)`; config keys `banner`, `version`, `logged_in`, `outside_dir`, `stages`; a stage mapping has `ops`, `result`, `init` (init overrides, `"$DELETE"` removes a key), `no_result`, `exit`, `stderr`. Ops: `hook` (payloads), `init` (override), `text`, `tool` (name, input, `run: "wrapper"` runs the real wrapper with CKPT_HOME and the session id set, args, denied, reject, content; a denial also emits a `permission_denied` system event and a `permission_denials` entry; the user event carries `tool_result_meta` accept or reject), `write` (writes the file only, no events), `git`, `sleep`, `raw`. Result keys: `subtype`, `is_error`, `terminal_reason`, `text`, `total_cost_usd`, `delta` (adds `model_usage_since_last_result`), `usage`, `num_turns`, `session_id`, `omit`. Tokens: `$PROJECT`, `$CWD`, `$RUN`, `$AUTOMEM`, `$OUTSIDE`, `$CONFIG`, `$WRAPPER`, `$SID`. `default_row1_stages()` returns s1, s2, s3 (costs 0.03, 0.09 with delta 0.06, 0.04; s2 ends with a fenced resume line; s1 and s3 fire a Project entry for the project CLAUDE.md, s2 fires none). `stages_with(stages, index, **changes)` copies the list and replaces fields of one stage. `RowRig(stages=None, **config)` offers `.repo`, `.bin`, `.harness_home`, `.user_home`, `.runs`, `.env`, `.claude`, `.configure(...)`, `.calls()`, `.tripwire()`, `.context(**overrides)` and `.new_run_root(ctx, name)`.

## Authentication gates

None. No real `claude` was started; the only claudes executed were the scripted fake and the tripwire of `pc_testutil`.

## Known Stubs

None in the shipped behaviour. HARN-05 is marked complete at the orchestrator's instruction for this plan's share (per-stage usage, delta and cumulative cost, the row total); the provenance files half of that requirement (versions, digests, tool set, allowlist, harness version) is filed by plan 03-04.

## Threat Flags

None. No network endpoint, auth path or schema was added; new file access is confined to the run root and the harness home through exclusive creation.

## Self-Check: PASSED

- Created files exist: `pc_row1.py`, `data/row1-s1-prompt.md`, `data/row1-plan.md`, `test_row1_seed.py`, `test_stages.py`, `test_row1_assertions.py` under `tests/harness/`.
- Commits `e9f040c`, `2bed3d2`, `b096f53`, `dde9972`, `b67acf8`, `26afe80` are ancestors of HEAD; `git diff` against the plan's start lists only files under `tests/harness/`; `SKILL.md`, `references/`, `tests/fixtures/` and the publication evidence folder are unchanged; no commit carries an attribution trailer and no hook was bypassed.
