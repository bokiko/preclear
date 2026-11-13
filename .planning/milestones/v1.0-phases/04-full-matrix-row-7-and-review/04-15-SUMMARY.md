---
phase: 04-full-matrix-row-7-and-review
plan: 15
subsystem: testing
tags: [harness, helper-rows, layouts, wrapper-injection, expected-changes, layout-facts, zero-token]
requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-07 analyses registry, 04-09 shared git-row test helpers, 04-12 path_prepend and git wrapper, 04-13 four-stage chain, 04-14 verdict-word guard over setup texts
provides:
  - rows 2, 3a, 3b, 3c and 4b registered and implemented (two stages, one session each); layouts plain-memory, hub-memory and bound-ledger registered and implemented (three stages, two sessions each); all 21 entries of --list implemented
  - RowSpec.expected_changes, pc_checks.WRAPPER_MADE_NAMES, validated_expected_changes, write_boundary and compute_facts taking the run record's exact names
  - PROFILE_HELPER_READ (helper-read, 37 rules) in pc_rows and pc_flags
  - pc_rowseeds seed_row2, seed_row3a, seed_row3b, seed_row3c, seed_row4b, seed_layout_plain, seed_layout_hub, seed_layout_bound; seed_helper_row parameters second_writer, local_fixture, local_values, expected_changes; seed_plain_row parameters fixture_tree and memory_dir
  - pc_rowhooks arm-wrapper-conflict (snapshot snap-1b-after-arming) and lint-after-s2 (NO_BOUNDARY: no snapshot, no boundary)
  - pc_review analyses wrapper-injection and layout-facts; pc_row1.paths_for reading auto_memory from raw/run.json; prompt files with a #section suffix
  - session facts that name the bound ledger (status-names-ledger-a for A, the old key for B and none)
  - tests/harness/data/layout-s1-prompts.md pinned by digest and tests/harness/test_rows_helper.py (93 tests)
affects: [04-16, 04-17, 04-18, 04-19, 04-20, 04-21]
key-files:
  created:
    - tests/harness/test_rows_helper.py
    - tests/harness/data/layout-s1-prompts.md
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_rowhooks.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_review.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_flags.py
    - tests/harness/pc_evidence.py
    - tests/harness/pc_matrix.py
    - tests/harness/pc_testutil.py
    - tests/harness/README.md
    - tests/harness/test_boundaries.py
    - tests/harness/test_driver_matrix.py
    - tests/harness/test_matrix_cli.py
    - tests/harness/test_review.py
    - tests/harness/test_row12.py
    - tests/harness/test_row_generic.py
    - tests/harness/test_rows_plain.py
key-decisions:
  - "The expected changes of a run are exact names from a fixed set of five (armed, target-section, injection.log, writer2-body-1.md, writer2-body-2.md under wrapper/), listed in raw/run.json, which the guard already pins; a record naming anything else is a check error, and a model write to any other name under wrapper/ ends the row with 11"
  - "The third status question names the ledger the session is bound to: key status_names_ledger_a for a row bound to A, status_names_ledger_b unchanged for row 1, and for a row with no binding the old key with UNCONFIRMED, so every filed plain row still reproduces byte for byte"
  - "A scripted hash a seeded ledger gives cannot be written before the run root exists (the ledger text holds the run path), so the scripted claude got a $HASH[section] token read through the stub directly, which leaves the wrapper log untouched"
  - "lint-after-s2 takes no snapshot and adds no boundary; its output file is an allowed raw name in the window after s2, and the file holds the stub's standard output only, as the committed lint-after-s2.txt does"
  - "The layouts are found by pc_rows.find_runnable (row first, then layout); the exact-kind find_entry is unchanged"
  - "The layout facts print counts, names and digests; a file name or lint line that holds a whole verdict word is withheld, so the filed checks file never holds one"
patterns-established:
  - "a hook that adds no boundary is listed in NO_BOUNDARY and skipped by plan_boundaries and run_after_stage"
  - "a prompt path may end in #<name> to take one level-two section of a prompts file"
duration: about 3 hours wall time including two full suite runs
completed: 2026-11-07
status: complete
requirements-completed: [RERUN-02]
actuals:
  tokens: 37000
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 28ce0c7ef64ca6140d1420802f8e1d90cdb69498
plan_head_after: f62941c3a12fb934d5bc587fe36882fc6c56a4c1
---
# Phase 4 Plan 15: Helper rows and layouts Summary

**Rows 2, 3a, 3b, 3c and 4b and the three layouts now run on the scripted claude, so every one of the 21 entries of `--list` is implemented; row 2 meets two genuine exit 3 results through the real wrapper and stub, and nothing was spent.**

## Accomplishments
- **Row 2.** The seed binds the model's session and a second session to the one ledger and writes the second id beside the wrapper. After the work turn the hook `arm-wrapper-conflict` writes the count 2 into `wrapper/armed`. The scripted /preclear turn then gets exit 3 twice and exit 0 on the third update (wrapper log exits 0, 0, 0, 3, 0, 3, 0, 0, as in the committed run). The injection log is filed as `wrapper-injection.log`.
- **Exact expected changes.** `raw/run.json` lists the five names the wrapper creates; the write boundary skips exactly those. A scripted write to `wrapper/other.txt` is a breach (exit 11). A forged record naming another name is refused by the checks.
- **Rows 3a, 3b, 3c, 4b.** Each seed differs from its committed fixture only in the values of the four configuration keys: 3a names `wrapper/missing-checkpoint` (absent, the working wrapper beside it), 3c has `none` as fallback and no binding at all (no bindings folder, no bind call), 4b adds `CLAUDE.local.md` from the committed local fixture. Row 3b has the new helper-read profile: baseline plus status, show, validate and lint only.
- **Layouts.** plain-memory and hub-memory copy the frozen fixture project in place (byte for byte, compared file by file), commit once, pin auto-memory at `project/memory`, and have no helper. bound-ledger is row 1's seed with ledger A only. `paths_for` and `--refile` find the memory folder from the run record.
- **Prompts and facts.** `data/layout-s1-prompts.md` (sha256 78c3c0f9...a39a) holds the two new work-turn prompts, pinned in a test. `layout-facts` prints counts, names and digests, plus the ledger digest change, the update count and the lint text for bound-ledger. Each layout README states the five checks the harness does not exercise.
- Suite: 2055 -> 2148 tests (3 skipped as before), green through `tests/harness/selftest` (banner `0 model calls`); the new test file also passes on Python 3.9.6.

Suite count: 2148

## Task Commits
1. **Task 1 (tracer): row 2 with a second bound writer, armed after s1, and exact expected changes** - `013596e` (feat)
2. **Task 2: rows 3a, 3b, 3c and 4b** - `c8614d4` (feat)
3. **Task 3: the three layout core chains, prompts, facts and README** - `f62941c` (feat)

_Tracer gate: the Task 1 `<verify>` (the new tests, the tripwire dry run, the wrapper conflict, evidence and stages guards) passed before the commit; no `blocking-human` gate was set. The SUMMARY commit that follows is the fourth commit of the range; `commits:` above is measured before it. The code of all three tasks was written in one pass and each task commit activated its own registry entries and tests._

## Facts recorded
| Item | Value |
|---|---|
| Two-stage worst case (rows 2, 3a, 3b, 3c, 4b) | 1.60 USD (0.30 + 1.30); the plan text says 2.00, the same plan defect as rows 4a, 5a, 5b and 6 |
| Layout worst case | 2.00 USD each (0.30 + 1.30 + 0.40 = 2.00) |
| `--all` after this plan | 21 rows, 55 stages, 33 sessions, worst case 38.40 USD |
| `--all` before this plan | 13 rows, 36 stages, 22 sessions, 24.40 USD |
| Invocation ceiling | 25.00 USD on the `--budget` flag, unchanged; the sum of worst cases is not a limit, the driver stops before the row that would take settled spend over the budget |

## Deviations from Plan
### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan text says 2.00 worst case for two-stage rows**
- The caps sum to 1.60. Tests and the dry-run checks assert 1.60, as for rows 4a to 6. No cap was changed.

**2. [Rule 3 - Blocking] The `--all` sum passed the 25.00 figure**
- Row 2 alone took 24.40 to 26.00. The old test asserted a sum under 25.00; it now asserts the exact total, the entry count, each entry at or under the row cap and the unchanged `--budget` ceiling. The orchestrator confirmed the ceiling belongs to the flag, not to the matrix sum.

**3. [Rule 3 - Blocking] Files outside the plan's list**
- Code: `pc_flags.py` (the helper-read profile), `pc_evidence.py` (print the bound-ledger status key, treat helper-read as a wrapper profile), `pc_row1.py` (`paths_for` from the run record, `#section` prompts, the engine lookups), `pc_matrix.py` and `pc_rowseeds.py` (engine lookup), `pc_testutil.py` (the `$HASH[section]` token, the helper-read profile in the default scripts), `pc_checks.py` (also the lint-after-s2 raw name allowed in the window after s2).
- Tests moved onto the new truth, none deleted: `test_boundaries.py` (hook table), `test_review.py` (analyses), `test_row12.py` (`--all` figures and hook list), `test_rows_plain.py` (hook list and the no-snapshot hook), `test_row_generic.py` (lookup of layouts, two ids that are now implemented), `test_matrix_cli.py` (a row plus a layout is a valid selection), `test_driver_matrix.py` (`--all` now runs the layouts too).

**4. [Rule 1 - Bug] The lint text held the stub's brand line**
- First version merged standard error into the file; the committed `lint-after-s2.txt` is standard output only. Fixed before the Task 3 commit.

**5. [Plan wording] plain-memory prompt**
- The plan says plain-memory names its PLAN.md as the place the CSV decision is recorded. In the frozen fixture the plan holds no decision; it lives in the memory topic file. The prompt names `PLAN.md` as the plan and the project memory as the place of the decision, and names no path. The hub-memory prompt names the memory topic for widget-export.

**6. [Process] RED commits not made (tdd="true")**
- A failing-test commit would break the green-suite rule; tests were written with the code and run before each commit.

**7. [Process] The commit guard refuses `main`**
- Per the dispatch the orchestrator made the three task commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.

**Total deviations:** 7, none changing the behaviour of an earlier row. Filed evidence still reproduces: plain rows keep `status-names-ledger-b: UNCONFIRMED`.

## Interpretations worth review
- A row with no binding keeps all three status questions under their old keys: the first two are asked when s2 made a status call, the third prints UNCONFIRMED. The plan sentence could also be read as UNCONFIRMED for all three.
- The hub-style test of the plain-memory facts is a base name starting with `hub_` or `hub-` and ending `.md`, case-insensitive.

## Known Stubs
None.

## Threat Flags
None beyond the plan's register (T-04-68 to T-04-72). The new surface is one file the harness creates in the wrapper folder, one raw file the lint hook writes, and a memory folder inside the project, each covered by tests: exact names, exclusive creates that refuse links, the default memory root probed absent, and the checks reading the run record only for the two known memory places.

## Notes for plan 04-16 (paid wave D)
- **Entry ids:** rows `row2-double-conflict`, `row3a-missing-executable`, `row3b-denied-helper-write`, `row3c-unbound-fallback-none`, `row4b-conflicting-blocks`; layouts `plain-memory`, `hub-memory`, `bound-ledger` (use `--layout`, not `--row`). A row and layouts may be combined in one invocation; `--all` may not be combined with them.
- **Per entry:**

| Entry | Stages | Sessions | Stage split (turns and cap) | Worst case | Allowlist rules |
|---|---|---|---|---|---|
| row2, row3a, row3c, row4b | 2 | 1 | s1 15 / 0.30, s2 60 / 1.30 | 1.60 USD | 40 |
| row3b | 2 | 1 | same | 1.60 USD | 37 |
| plain-memory, hub-memory | 3 | 2 | s1 15 / 0.30, s2 60 / 1.30, s3 15 / 0.40 | 2.00 USD | 33 |
| bound-ledger | 3 | 2 | same | 2.00 USD | 40 |

- **Wave D totals:** the eight entries have a worst case of 14.00 USD (5 x 1.60 + 3 x 2.00), 19 stages and 11 sessions. The budget flag must be at least 2.00, the largest single worst case, and at most 25.00.
- **Budget arithmetic from the measured waves:** measured per stage on the pinned build: work turn about 0.05 USD, /preclear turn 0.16 to 0.26 USD (row 11 0.164, row 12 0.217), fresh resume about 0.06 USD. Whole rows measured: row 1 0.27, rows 11 and 12 0.27 and 0.47, wave A 0.79, wave B 1.43, wave C 0.75. A two-stage helper row is therefore projected near 0.30 USD (row 2 heavier, near 0.40, for its extra helper calls) and a layout near 0.40 USD (the memory layouts read more files). Projection for the wave: about 2.7 USD, not measured for these entries. Recommended budget 4.00 USD (about 1.5 times the projection); the stop-before-row rule protects it, and a plain `go` takes the recommendation. Spent so far in Phase 4: 2.97 USD.
- **What to read after the run:** row 2 files `wrapper-injection.log`, and its `mechanical-checks.md` shows `status-names-ledger-a`. bound-ledger files `lint-after-s2.txt` and a `Layout facts` section with the ledger digests and the update count. The memory layouts file `Layout facts` with file lists and digests; `memory-files-created` under the memory folder are facts, not defects.
- **Unobserved until wave D:** the real model's behaviour under two injected conflicts, a missing executable, a denied helper write, conflicting configuration blocks and each memory layout; whether the real binary reports `memory_paths` inside the project as the pinned path; whether real `/preclear` turns in the layouts write to the memory folder. The scripted claude proves the pipeline only.
- `pc_compare.TRACES` still lists s1 to s3 only, which fits the layouts; row 12's s4 remains plan 04-18's concern.

## Self-Check: PASSED
Created files found (`test_rows_helper.py`, `layout-s1-prompts.md`); the three task commits are ancestors of HEAD; no stray placeholder is left in the registry; nothing outside `tests/harness` and this file changed.
