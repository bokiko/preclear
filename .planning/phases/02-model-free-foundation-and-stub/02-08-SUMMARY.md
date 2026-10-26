---
phase: 02-model-free-foundation-and-stub
plan: 08
subsystem: testing
tags: [claude-code, stream-json, isolation, spike, allowlist, python-stdlib, unittest]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "plans 02-01 to 02-07: pc_flags, pc_preflight, pc_stream, pc_runroot, pc_manifest, pc_sanitize, pc_leakgate, pc_allowlist, the stub, the wrapper and the README with its pending-file list"
provides:
  - "tests/harness/pc_spike.py: the only token-spending code of the phase: harness home, separate runs root outside every home folder, run-root materialiser, spend guard with a pessimistic launch line, S1 assertions, S2 probe, sanitised fixture writers"
  - "tests/harness/pc_hooklog.py: InstructionsLoaded hook logger (the only source of the instruction audit on 2.1.310)"
  - "tests/harness/data/spike-findings.md: isolation claim and evidence, scratch login probe, one-time login, probe table, stream facts, session-id handling, flag confirmations, per-call spend"
  - "tests/harness/data/s1-init-manifest.json, s2-stream.jsonl, s2b-stream.jsonl, s2-probe-labels.json: sanitised, leak-gated real captures"
  - "pc_flags.TESTED_VERSIONS seeded with the one build that ran (2.1.310); FLAG_TABLE rows confirmed by S1 or S2"
  - "tests/harness/test_spike_fixture.py: zero-token checks that keep the denial detector, the allowlist model and the version gate honest against the real capture"
affects: [phase-03, phase-04]

actuals:
  tokens: 81400
  tasks: 4
  commits: 13
plan_head_before: 1e308f5041efd57641dda4bce0a22859d3c4a8ed
plan_head_after: 45326ab6db5db1c8796bf73fdc3a7b0e019c476a

tech-stack:
  added: []
  patterns:
    - "Append-only spend ledger with a pessimistic launch line (unknown cost counts as the call's cap) that a later line for the same attempt supersedes"
    - "Run roots live under a runs root outside every home folder, because Claude Code loads the instruction files of every ancestor folder as Project instructions"
    - "Paid paths are tested through a scripted fake claude; no test starts a real model"
    - "Captures pass the sanitiser, the Python leak gate and an exclusive write before any byte lands under the repository"

key-files:
  created:
    - tests/harness/pc_spike.py
    - tests/harness/pc_hooklog.py
    - tests/harness/test_spike.py
    - tests/harness/test_spike_fixture.py
    - tests/harness/data/spike-findings.md
    - tests/harness/data/s1-init-manifest.json
    - tests/harness/data/s2-stream.jsonl
    - tests/harness/data/s2b-stream.jsonl
    - tests/harness/data/s2-probe-labels.json
  modified:
    - tests/harness/pc_flags.py
    - tests/harness/test_flags.py
    - tests/harness/test_preflight.py
    - tests/harness/test_readme.py
    - tests/harness/README.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Run roots moved out of the home tree (bokiko, 2026-10-26): S1 attempt 1 showed the user's global rules loading as Project instructions through ancestor traversal; the driver now takes PRECLEAR_RUNS_ROOT, defaults to a shared folder for all users, and refuses a home folder, the repository, the user's Claude folder or an ancestor that holds an instruction file or folder"
  - "Two S1 assertions refined (bokiko, 2026-10-26): no-non-builtin-plugins replaces plugins-empty (3 plugins ship with the binary, all source @builtin), and a user name the binary itself defines is a collision, not a leak; preclear is excluded; counts only are recorded"
  - "The spend ledger stays append-only but a later line for the same (call, attempt) supersedes the earlier one, so the pessimistic launch record is reconciled without a double count"
  - "The matcher model was not changed for the two probe rows the binary allowed (echo from the built-in read-only set, a double-quoted PWD variable); both are flagged outside the model in the labels"
  - "TESTED_VERSIONS is the one-entry tuple 2.1.310, equal to claude --version and to init.claude_code_version of S1, S2a and S2b"

patterns-established:
  - "A model-facing STOP: a failed or unassertable isolation assertion exits 11, prints STOP and writes no manifest and no findings; only a dated decision by the owner changes the assertion"
  - "Fixture tests recompute the stored matcher answer, so a stale label or an unflagged disagreement fails"

requirements-completed: [HARN-04, HARN-06]

coverage:
  - id: D1
    description: "The spike driver spends nothing unless --run is given; every paid call passes --max-budget-usd and --max-turns, the guard allows at most two attempts per call name and recorded spend plus the next cap never above 5.00 USD, with a pessimistic ledger line written before each launch"
    requirement: HARN-04
    verification:
      - kind: unit
        ref: "tests/harness/test_spike.py (SpendGuardTests, SupersedeLedgerTests, PaidS1Tests, PaidS2Tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "S1 measured isolation against the real binary: nine pre-declared assertions all pass on the rerun with the runs root outside home folders; the ancestor-instruction leak of attempt 1 is recorded as the reason, with the two dated refinements"
    requirement: HARN-04
    verification:
      - kind: unit
        ref: "tests/harness/test_spike.py (S1AssertionTests, RefinedAssertionTests, RunsRootTests) and tests/harness/test_spike_fixture.py (ManifestTests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "S2 real stream capture and the seven-command probe: the wrapper bind was denied live with both structured signals naming one tool_use id; two probe rows the binary allowed are flagged outside the model; labels, fixtures and findings are sanitised and leak-gated"
    requirement: HARN-06
    verification:
      - kind: unit
        ref: "tests/harness/test_spike_fixture.py (ProbeLabelTests, StreamFixtureTests, FindingsTests, HygieneTests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Session-id handling (init and result ids match the requested id for S2a and S2b, --resume honoured) and the verbose probe (stream-json without --verbose is refused, exit 1) confirm the pinned pair and the session pin"
    requirement: HARN-04
    verification:
      - kind: unit
        ref: "tests/harness/test_spike_fixture.py (StreamFixtureTests.test_the_resume_turn_kept_the_session_and_each_call_reports_its_own_id, FindingsTests.test_the_session_id_facts_for_both_calls_are_present)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The version gate is seeded from the real run and the README flag table is regenerated from the code; the whole folder is green on the PATH interpreter and on the system 3.9 interpreter with zero model calls"
    requirement: HARN-04
    verification:
      - kind: unit
        ref: "tests/harness/selftest and python3 -I -B -m unittest discover -s tests/harness (3.9.6 and PATH interpreter)"
        status: pass
    human_judgment: false
  - id: D6
    description: "The isolation level the matrix may claim: strict, as the owner decided, shown by nine assertions on one build; the unproven parts are listed under Not asserted in the findings"
    verification: []
    human_judgment: true
    rationale: "Whether the evidence is strong enough to label every Phase 3 and Phase 4 evidence folder with the strict claim is the owner's call (D-02); the findings state exactly what was and was not machine-asserted"

# Metrics
duration: 2h 10m across two executor sessions (a checkpoint and a resume)
completed: 2026-10-26
status: complete
---

# Phase 2 Plan 08: Spikes S1 and S2 Summary

**The two paid spikes ran against Claude Code 2.1.310 for 0.26 USD in total: strict isolation holds once run roots sit outside every home folder, the wrapper bind is denied live, the real stream and probe are committed as sanitised fixtures, and the version gate is seeded.**

## Performance

- **Duration:** about 2 h 10 min across two executor sessions, including the checkpoint that waited for the owner's decision
- **Completed:** 2026-10-26
- **Tasks:** 4 (Task 2 was the owner's one-time login)
- **Files modified:** 15 (nine created, six modified, counting REQUIREMENTS.md)

## Accomplishments

- **Isolation measured, and a real leak found and fixed.** Attempt 1 of S1 ran with the run root under the harness home inside the user's home folder. Three assertions failed. The decisive one: the user's global `CLAUDE.md` and six rule files loaded as Project instructions, because Claude Code walks up the ancestor folders of the working directory and loads each one's `.claude/CLAUDE.md` and `.claude/rules`. With the runs root outside every home folder (owner's decision, 2026-10-26) the rerun loaded exactly one Project entry, the fixture's own, and all nine assertions passed. Two assertions were refined by the owner on the same date (built-in plugins, binary-defined name collisions), recorded with their counts in the findings and the frozen manifest.
- **The instruction audit is assertable, through the hook logger, not the stream.** The InstructionsLoaded hook fires in print mode and the logger file records file path, memory type and reason. With `--include-hook-events` accepted, the stream still carried no hook events, so the logger was the only source; this corrected an earlier statement in the S1 findings.
- **Live policy probe (HARN-06).** Seven commands, expectations written before the run. The wrapper bind was denied by the binary, with the `permission_denied` event and the `result.permission_denials` entry naming the same tool_use id: live proof of the first layer of STUB-06. The binary allowed two commands the expectation and the model called denied (`echo`, from its built-in read-only set, and a double-quoted `$PWD` for `wc`); both are flagged outside the model and the model stays conservative.
- **Stream, session and verbose facts pinned.** `--verbose` is required with stream-json (refused with exit 1 and a stderr message before any model call). `--session-id` and `--resume` behave as pinned: init and result report the requested id for S2a and S2b, and the resumed turn continued the same session. `effort` is absent from init on this build.
- **Version gate seeded.** `TESTED_VERSIONS` is `("2.1.310",)`, equal to `claude --version` and to `init.claude_code_version` of all three captures; 18 flag rows now carry S1 or S2 as their confirmation and three row texts were corrected to the observed behaviour.
- **Spend.** 0.26 USD of the 5.00 USD cap (exact sum 0.2544077 USD with the refused verbose probe counted at its 0.05 cap): s1 attempt 1 0.0599855, s1 attempt 2 0.0264356, verbose 0.05, s2a 0.0576893, s2b 0.0602973. No per-call cap was exceeded; s1 used both attempts, every other call one.

## Task Commits

Task 1 (earlier executor, already merged):

1. **Task 1: spike driver, spend guard, dry run, login check** - `af405d3` (test), `54c9b4c` (feat)

Task 2 was the owner's login (no commit).

3. **Task 3: spike S1** - `cb26797` (test), `470e7ee` (feat: assertions, STOP outcome, paid S1 path), then after the owner's decision `8bbebed` (test), `99cdc9d` (feat: runs root and refined assertions), `651cf58` (feat: socket-path scrub), `3955fb7` (feat: S1 manifest and findings)
4. **Task 4: spike S2** - `734f9c0` (test), `ba772b5` (feat: S2a, S2b and verbose paths), `08f2c54` (test: fixture tests), `5836e29` (feat: S2 fixtures, labels, findings), `45326ab` (feat: version seed, flag confirmations, README)

**Plan metadata:** the commit that adds this summary and marks HARN-04 complete.

## Files Created/Modified

- `tests/harness/pc_spike.py` - the spike driver (home, runs root, spend guard, S1 and S2 paid paths, sanitised writers)
- `tests/harness/pc_hooklog.py` - hook logger
- `tests/harness/test_spike.py`, `tests/harness/test_spike_fixture.py` - zero-token tests (a scripted fake claude drives the paid paths)
- `tests/harness/data/` - findings, init manifest, two streams, probe labels
- `tests/harness/pc_flags.py` - tested version seeded, confirmations, three row texts corrected
- `tests/harness/test_flags.py`, `test_preflight.py`, `test_readme.py` - adjusted for the seeded gate and the landed files
- `tests/harness/README.md` - flag table regenerated, login and findings anchors filled, layout updated
- `.planning/REQUIREMENTS.md` - HARN-04 marked complete

## Decisions Made

See key-decisions. The two owner decisions (runs root outside home folders; refined plugin and name assertions) are dated 2026-10-26 and stated in the findings.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Pessimistic spend record before each launch**
- **Found during:** Task 3
- **Issue:** The ledger was one line per attempt written after the call, so a crash mid-call would leave the spend unrecorded; the orchestrator required the cap to be recorded before launch and reconciled after.
- **Fix:** `run_*` append a `launched` line (unknown cost, counted as the cap) first; a later line for the same (call, attempt) supersedes it, so the pair is one attempt and one cost.
- **Files modified:** tests/harness/pc_spike.py, tests/harness/test_spike.py
- **Commit:** `470e7ee`

**2. [Rule 3 - Blocking] Tests that assumed an empty tested-version set**
- **Found during:** Task 4
- **Issue:** `test_flags` asserted every `confirmed_by` equals research, and `test_preflight` expected exit 13 for the default tested set; seeding the gate and confirming rows (both required by the plan) made them fail.
- **Fix:** `confirmed_by` must be research, S1 or S2; the preflight CLI case now passes an explicit tested set that lacks the build to keep the UNTESTED path covered. The plan's "test_flags passes unchanged" could not hold literally.
- **Commit:** `45326ab`

**3. [Rule 2 - Missing critical functionality] The init event's temp socket path**
- **Found during:** Task 3 (manifest review)
- **Issue:** `messaging_socket_path` holds a temp path with a process id, which the project rules forbid in committed files and the gate did not flag.
- **Fix:** `scrub_volatile` replaces it with a token inside `sanitize_to_data`; the already-written S1 manifest got the same replacement by a one-line edit before commit.
- **Commit:** `651cf58`, `3955fb7`

**4. [Rule 1 - Bug] Findings claimed the stream showed that the hook ran**
- **Found during:** Task 4 (flag confirmation)
- **Issue:** The S1 findings said the stream showed hook events; the captures contain none.
- **Fix:** Corrected in the findings, in the `--include-hook-events` row text and in this summary.
- **Commit:** `5836e29`, `45326ab`

### Plan-text conflicts and owner decisions (not bugs)

- The plan's Task 3 manifest check requires `plugins == []`; the owner's refinement replaces it with "no plugin whose source is not @builtin", so the manifest holds three built-in plugins.
- Expectations for `pwd-and-echo` and `variable-expansion` (written as denied before the run) were wrong against the binary; the labels keep the original expectation and the observed truth, and the findings record the correction.
- The hooks documentation page was not fetched (the run rules allow no network beyond the Claude Code calls); the hook payload and settings shape were confirmed against the installed binary's schema and by the hook firing.
- Task 3 and Task 4 each produced several commits (test, feature, data) instead of one, because of the TDD split and the checkpoint.
- A stray bytecode file from one of my own helper scripts briefly appeared under tests/harness and was removed before any commit.

## Authentication Gates

Task 2 (the one-time login into the harness-owned config directory) was a blocking human action performed by the owner; the first zero-token check reported logged out (exit 12) and the check after reported logged in. Normal flow, not a deviation.

## Known Stubs

None. No placeholder text or empty-data stubs were introduced.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: shared-folder-write | tests/harness/pc_spike.py | The default runs root sits in a shared folder whose parent is world-writable (sticky); the driver creates it with mode 0700 and refuses ancestors that hold instruction files, but another local user could pre-create the folder name |

## Issues Encountered

- The three failed assertions of S1 attempt 1 stopped the plan at a checkpoint; the owner's decision resolved all three (see Accomplishments). S1 therefore used both of its attempts, and any further S1 rerun would need a decision to change the attempt limit.

## Next Phase Readiness

- Phase 3 and Phase 4 must place their run roots outside every home folder (same runs-root mechanism) and choose the matrix baseline model separately; both items are recorded as open in the findings.
- The model-free gate passes again with the seeded gate: 724 tests green on the PATH interpreter and on the system 3.9 interpreter, 0 leak-gate findings, gitleaks clean, no bytecode or log files, frozen paths unchanged since 56e155c, no attribution trailers in any commit message of this plan.

## Self-Check: PASSED

All eleven `files_modified` paths exist; every commit listed above appears in the history of HEAD.
