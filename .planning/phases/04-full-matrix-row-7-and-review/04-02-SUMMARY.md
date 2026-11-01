---
phase: 04-full-matrix-row-7-and-review
plan: 02
subsystem: testing
tags: [harness, campaign, attempt, multi-row-loop, exit-aggregation, invocation-budget, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-01 registry engine, per-row filing, row 4a (the scripted second implemented row)
provides:
  - campaign labels (--campaign) with a labelled dated folder and scoped ledger rows, ledger stage keys and run-root names
  - attempt scoping (--attempt N) with <row id>-attempt-N folders, aN ledger scope and the earlier-attempt-on-record rule
  - --evidence-date override, repeatable and combinable --row and --layout, the multi-row loop with one honest exit code
  - per-invocation budget (format_invocation_budget, ceiling 25.00) with the stop-before-row rule
  - row-folder gate (row, STOPPED- and SKIPPED- folders), --refile for any registered row with a scope record
affects: [04-03, 04-04, 04-05, 04-06, 04-09, 04-10, 04-12, 04-13, 04-15, 04-16, 04-19]

# Actuals (#2632): chars/4 over the realized diff of tests/harness against the plan base commit
actuals:
  tokens: 34847
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 1e413a90502b154cd7d9c99a7065ed030ff34b69
plan_head_after: ffce6f2bda1806257d0c6ab40097d166b50dd07a

tech-stack:
  added: []
  patterns:
    - "every ledger identity and folder name is built from the registry id, the campaign and the attempt by scoped_row, scoped_stage_key and row_folder_name, never from command-line text"
    - "a run that carries a campaign or an attempt records both in raw/scope.json before the setup snapshot, so a refile files where the original run would have"
    - "row-level outcomes 10, 11 and 19 continue the loop; 14 to 18 end the invocation; the exit code is ending, else 19, else 11, else 10, else 0"

key-files:
  created:
    - tests/harness/test_driver_matrix.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_matrix.py
    - tests/harness/pc_flags.py
    - tests/harness/pc_evidence.py
    - tests/harness/test_matrix_preflight.py
    - tests/harness/test_evidence.py
    - tests/harness/README.md

key-decisions:
  - "A campaign label may not hold any hyphen-separated part from a1 to a9 (not only the whole label), because wave-a2 would otherwise build the same ledger id as wave on its second attempt (T-04-08)"
  - "The scope of a run (campaign, attempt, matrix flag) is recorded in raw/scope.json only when it is not the Phase 3 default, written before the setup snapshot so the setup guard holds it"
  - "RowOutcome.spent is read from the spend ledger (pessimistic total of the scoped row) by run_registered_row; the driver falls back to the same reading for a runner that reports nothing or raises"
  - "A real run whose selected rows are all skipped needs neither a budget nor a claude: skips are filed by the claude-free path as before"
  - "The invocation budget minimum is the largest single worst case among the selected rows for both dry and real runs"

patterns-established:
  - "_run_rows is the one loop; _execute returns (code, spent) and execute_row stays a thin int-returning wrapper for the older tests"
  - "summary_lines prints only registry ids, the words filed, stopped, skipped, refused, exit codes and amounts"

requirements-completed: [RERUN-02, RERUN-03]

coverage:
  - id: D1
    description: "--campaign names the dated folder rerun-<date>-<model>-<LABEL> and scopes ledger row ids, stage keys and run-root names; bad labels (25 characters, upper case, empty, a1 to a9, any a1 to a9 part) exit 2 with fixed text; two labels never share an attempt count"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#ScopingTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#CampaignTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "--attempt N names <row id>-attempt-N, scopes the ledger with aN, needs a launch line of attempt N-1 (exit 18 otherwise, nothing created) and is refused with --all or more than one entry"
    requirement: RERUN-03
    verification:
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#AttemptTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "--row and --layout repeat and combine, entries run in registry order, --evidence-date overrides the date, the loop continues after 10, 11 and 19 and ends at once for 14 to 18, the exit code never reads as success after a skip or stop"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#SelectionTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#LoopTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#MatrixScopeTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "The gate refuses only through the row (row, STOPPED- and SKIPPED- folders of the attempt); --refile accepts any registered row and reads its scope record"
    requirement: RERUN-03
    verification:
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#RowFolderGateTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#RefileAnyRowTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "--budget is per invocation (two decimals, at most 25.00, at least the largest single worst case), the loop stops before a row whose worst case on top of the settled spend passes it, worst_case is min(sum of caps, ROW_CAP) and the ledger refuses the launch past 2.00"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#BudgetTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#InvocationBudgetParserTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_driver_matrix.py#WorstCaseTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "Who typed a budget amount, a campaign label or an attempt number cannot be proven mechanically; the rule that only bokiko's word in the conversation starts a paid wave is enforced by the paid plans' blocking checkpoints"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan: the ledger line shows the flag ran, not who typed it"

duration: 80 min
completed: 2026-11-01
status: complete
---

# Phase 4 Plan 2: Campaign driver Summary

**The driver now runs a campaign: labelled dated folders, attempt folders that never collide, a date override, several rows in one invocation that keep going after a skipped or stopped row, an exit code that never reads as success when something was skipped or stopped, and a per-invocation budget that stops before a row would take the invocation past it.**

## Performance

- **Duration:** about 80 min (estimate; the start time was not recorded)
- **Completed:** 2026-11-01T20:30:00Z
- **Tasks:** 3
- **Files modified:** 9 (1 created)

## Accomplishments

- `pc_rows`: `scoped_row`, `scoped_stage_key`, `row_folder_name`, `is_valid_campaign`, `parse_evidence_date`, `evidence_folder_name(date, model, campaign)`, `RunContext.campaign/attempt/matrix`, `RowOutcome.spent`, and `worst_case` as `min(sum of caps, ROW_CAP)`. The longest id (28-character row id, 24-character label, attempt 9) is 56 characters, inside the 64-character ledger rule; a test builds every row, stage, label and attempt pair and asserts no two selections share an id.
- `pc_row1`: `run_stage` reserves and settles under the scoped row id and stage key with the scoped allowed-stage tuple; the run-root name is the scoped row id plus the stamp; `raw/scope.json` records a non-default scope before the setup snapshot; `run_registered_row` reports the ledger's settled total in `RowOutcome.spent`.
- `pc_matrix`: `--campaign`, `--evidence-date` (malformed, non-calendar and future dates exit 2), `--attempt` (single digit 1 to 9, exit 18 without an earlier launch line, exit 2 with `--all` or more than one entry), repeatable combined `--row` and `--layout`, `_run_rows` with `summary_lines` and `_aggregate_code`, the row-folder gate (`_taken_label`), `--refile` for any registered row reading the scope record, the invocation budget with the stop-before-row rule, and per-row allowlist size in the plan.
- `pc_flags`: `INVOCATION_BUDGET_MAX` (25.00) and `format_invocation_budget` over one shared amount parser; `format_budget` keeps its 5.00 ceiling and its tests.
- `test_driver_matrix.py` (new, 80 tests): `ScopingTests`, `CampaignTests`, `SelectionTests`, `LoopTests`, `MatrixScopeTests`, `AttemptTests`, `RowFolderGateTests`, `RefileAnyRowTests`, `InvocationBudgetParserTests`, `WorstCaseTests`, `BudgetTests`, `PlanLineTests`, all on the scripted claude or injected runners; nothing was spent.
- Suite: 1343 -> 1424 tests (3 skipped as before), green through `tests/harness/selftest` with the `0 model calls` banner, on the 3.9 system interpreter.

Suite count: 1424

## Task Commits

1. **Task 1 (tracer): campaign label, evidence-date override and scoped ledger identities** - `b7a2f5f` (feat)
2. **Task 2: attempts, the multi-row loop, one honest exit code and the row-folder gate** - `953d8ad` (feat)
3. **Task 3: per-invocation budget, per-row allowlist size in the plan, README** - `ffce6f2` (feat)

**Plan metadata:** the SUMMARY commit that follows (docs: complete plan).

_Tracer gate: the tracer `<verify>` (the new test module, the tripwire dry run with `--campaign` and `--evidence-date`, `test_matrix_cli`) was run and passed before Task 2; the full suite also passed at the Task 1 state (1362 tests)._

## Files Created/Modified

- `tests/harness/pc_rows.py` - scoping and naming functions, new record fields, bounded worst case
- `tests/harness/pc_row1.py` - scoped spend identities, run-root name, scope record, spent figure
- `tests/harness/pc_matrix.py` - flags, selection, loop, summary, aggregation, gate, refile, budget
- `tests/harness/pc_flags.py` - the invocation budget parser
- `tests/harness/pc_evidence.py` - the row folder name follows the attempt; `file_skipped` takes the folder name; `STOPPED_PREFIX`
- `tests/harness/test_driver_matrix.py` - new (see above)
- `tests/harness/test_matrix_preflight.py`, `tests/harness/test_evidence.py` - literals that described the old budget ceiling and the refused dated folder
- `tests/harness/README.md` - the new flags, the budget meaning, the loop and the exit aggregation

## Decisions Made

See `key-decisions` above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan defect] The budget examples of Task 3 do not follow the plan's own rule**
- **Found during:** Task 3 (writing `BudgetTests`)
- **Issue:** the behaviour block says rows spending 0.30, 0.30 and 0.30 all run under a 2.50 budget, and that under 2.20 "the third row is not started because 0.60 plus 2.00 is above 2.20". By the stated rule (settled spend of finished rows plus the next row's worst case, stop when above the budget) the third row of a three-row run needs 0.60 + 2.00 = 2.60, so it would not start under 2.50, and under 2.20 the second row (0.30 + 2.00 = 2.30) would already not start.
- **Fix:** implemented the rule as written in the prose and tested the coherent boundaries: 2.60 runs all three rows, 2.59 stops before the third, 2.29 stops before the second, plus an exact-Decimal case (0.50 runs, 0.49 stops).
- **Files modified:** tests/harness/test_driver_matrix.py
- **Commit:** ffce6f2

**2. [Rule 2 - Missing critical functionality] Labels with an `a1` to `a9` part are refused, not only the labels `a1` to `a9`**
- **Found during:** Task 1 (the T-04-08 collision test)
- **Issue:** with only the whole-label rule, the label `wave-a2` at attempt 1 builds `wave-a2-<row id>`, the ledger row id the label `wave` builds at attempt 2, so a label could obtain an extra attempt (T-04-08 requires that no two selections share an id).
- **Fix:** `is_valid_campaign` rejects any hyphen-separated part from `a1` to `a9`; a test builds ids for every label and attempt pair. Labels such as `a`, `a10` and `wave-a0` stay valid.
- **Files modified:** tests/harness/pc_rows.py, tests/harness/test_driver_matrix.py
- **Commit:** b7a2f5f

**3. [Rule 3 - Blocking] Filing and refile needed the attempt and the scope, so `pc_evidence.py` changed**
- **Found during:** Task 1 and Task 2
- **Issue:** `file_row` promoted to `<dated folder>/<row id>` and `file_skipped` to `SKIPPED-<row id>`; an attempt above 1 therefore could not file into `<row id>-attempt-N`. `pc_evidence.py` is not in the plan's `files_modified`. A retry's refile also needed the campaign and the attempt, which the run folder did not hold.
- **Fix:** `file_row` uses `row_folder_name(entry.row_id, ctx.attempt)`; `file_skipped` takes an optional `folder_name`; `pc_row1` writes `raw/scope.json` (campaign, attempt, matrix) for a non-default scope before the setup snapshot, and `--refile` reads and validates it. `pc_rowseeds.py` was not touched (the seed signature stays the one tests inject).
- **Files modified:** tests/harness/pc_evidence.py, tests/harness/pc_row1.py, tests/harness/pc_matrix.py
- **Commit:** b7a2f5f, 953d8ad

**4. [Rule 3 - Blocking] Phase 3 tests that encoded a refused dated folder or the 5.00 budget ceiling were moved to the new meaning**
- **Found during:** Tasks 2 and 3
- **Issue:** `test_matrix_preflight.py` (existing destination, accepted and refused budgets, the no-echo budgets) and `test_evidence.py` (a skip into an existing dated folder) asserted behaviour the plan changes. `test_evidence.py` is not in `files_modified`.
- **Fix:** the existing-destination tests now create the row folder or the `SKIPPED-` folder inside the dated folder (same meaning, aimed at the row); one test says an existing dated folder alone is not refused; the budget lists moved their above-ceiling values (5.01 is now accepted, 25.01 and 26 refused, 77.77 replaces 7.77 in the no-echo test). No assertion was dropped and no test deleted.
- **Files modified:** tests/harness/test_matrix_preflight.py, tests/harness/test_evidence.py
- **Commit:** 953d8ad, ffce6f2

**5. [Rule 3 - Blocking] `worst_case` moved to Task 1**
- **Found during:** Task 1
- **Issue:** the `worst_case` change sits in the plan's Task 3, but it lives in the file whose records and naming functions Task 1 edited and is one line with no dependency on later work.
- **Fix:** committed with Task 1; Task 3 adds its tests.
- **Commit:** b7a2f5f

**6. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- **Issue:** the plan requires every commit to leave the suite green, so a committed failing `test(...)` commit is not possible (same as plan 04-01 deviation 6).
- **Fix:** tests were written together with the code and run before each commit; each task commit is green. See TDD Gate Compliance.

---

**Total deviations:** 6 (1 plan defect, 1 missing critical, 4 blocking). **Impact:** none changes behaviour beyond the plan except the stricter label rule (2) and the figures corrected in (1).

## TDD Gate Compliance

Plan type is `execute` (not `type: tdd`), so the gate commands do not run; Tasks 2 and 3 carry `tdd="true"` and Task 1 is the tracer with `tdd="true"`. The failing state was not committed because the plan requires a green suite at every commit; the module and the code were developed together and the module run per task (Task 1: 19 tests, after Task 2: 58, after Task 3: 80). No REFACTOR commit.

## Authentication Gates

None.

## Issues Encountered

- The sandbox guard of this worktree refuses commands that name the version control tool next to computed values or complex forms; scripts that patch files were written to the scratchpad and run with literal paths. No repository file was affected.
- Full-suite runs take about 8 minutes; the suite was run at the Task 1 state (1362 tests) and at the final state (1424 tests); Tasks 2 and 3 were checked by the affected modules between those runs.

## Known Stubs

None.

## Threat Flags

None. The scope record is one more small file in the run root's raw folder (created exclusively, covered by the setup guard); no network endpoint, auth path or trust boundary was added.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 04-03 files stopped rows: `pc_evidence.STOPPED_PREFIX` ("STOPPED-") exists and the driver gate already refuses an existing `STOPPED-<row folder>`; `file_skipped(..., folder_name=...)` is the pattern to copy. A stopped row still files nothing and returns its Phase 3 code (11 or 19), which the loop treats as continue (FA-1 of the plan).
- `RowOutcome.spent` is the ledger's pessimistic total for the scoped row; a new row runner that does not return it is read from the ledger by the driver.
- `--authorize-retry` still takes bare stage keys (`row1-s2`); a stage of a campaign or attempt-scoped row has a scoped key that it does not accept. Retries of scoped rows go through `--attempt` instead (a new attempt is a new scoped identity). If a later plan needs authorizations for scoped stages, `_stage_catalog` is the place.
- The driver prints the per-row and summary lines for single-row runs too; any later plan that asserts exact driver output must expect them (the existing tests already do).
- Row 4a's worst case stays 1.60 (sum of caps, below ROW_CAP); a four-stage row prints 2.00.

## Self-Check: PASSED

- Created file exists: `tests/harness/test_driver_matrix.py`, this summary.
- Task commits are ancestors of HEAD: `b7a2f5f`, `953d8ad`, `ffce6f2`.
- `commits:` was measured against the plan base commit (3 task commits before this summary commit).
- Final gates: `tests/harness/selftest` 1424 tests OK with the `0 model calls` banner (floor 1343); `scripts/test-hooks.sh` 29 PASS; leak gate over `tests/harness` 74 files, 0 findings; the secret scanner over `tests/harness` clean; frozen paths (`SKILL.md` 11994 bytes, `references`, `tests/fixtures`, `publication-2026-10-20`, the Phase 3 rerun folder) unchanged against the plan base; the commits carry no attribution trailer; the change list against the plan base names only files under `tests/harness`.

---
*Phase: 04-full-matrix-row-7-and-review*
*Completed: 2026-11-01*
