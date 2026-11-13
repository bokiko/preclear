---
phase: 04-full-matrix-row-7-and-review
plan: 06
subsystem: testing
tags: [harness, row7, chmod-probe, printed-checkpoint, skipped-label, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-05 between-stage hook framework and boundary list, 04-04 plain rows, 04-03 stopped-row filing, 04-01 row-generic engine
provides:
  - pc_rows.ROW7, CHAIN_RESUME_LINE, CHAIN_PRINTED_CHECKPOINT, PROBE_NONE, PROBE_CHMOD, RowSpec.chain and RowSpec.probe, the row 7 registry entry (three stages, hook s1 restrict-project-555, probe chmod-denial, precondition chmod_precondition)
  - pc_rowseeds.seed_row7
  - pc_rowhooks.chmod_denial_probe, chmod_precondition, run_probe, PROBES, CHANGES, hook restrict-project-555 (snapshot snap-1b-after-restriction) with finalizer restore-project-755
  - pc_row1.printed_checkpoint, extract_printed_checkpoint, fenced_blocks, MAX_PRINTED_CHECKPOINT_BYTES, MARKER_NO_CHECKPOINT, the chain strategy dispatch, the probe call and the SKIPPED path in run_registered_row
  - raw/chain.json keys marker, checkpoint_bytes, checkpoint_reason for the printed-checkpoint chain; raw/probe-chmod/
  - pc_testutil scripted op try_write and printed_checkpoint_stage (default_row_stages is aware of row 7)
affects: [04-07, 04-17, 04-18, 04-19, 04-21]

# Actuals (#2632): chars/4 over the realized diff of tests/harness against the plan base commit
actuals:
  tokens: 30000
  tasks: 3
  commits: 1

commits: 1
plan_head_before: 616b49b77163050fe9083775a6c0101514b6d0f5
plan_head_after: 00b12ccf8ec0bf788b10ac29b69e712e2615a363

tech-stack:
  added: []
  patterns:
    - "a row names a chain strategy (RowSpec.chain) and a live probe (RowSpec.probe); the engine dispatches on them, so a later row that feeds its resume stage differently adds a constant, not a branch on a row id"
    - "a probe runs after the seed and before snapshot 0 and the setup guard, so its folder is already in the guard's first raw listing and a skip costs nothing"
    - "a hook's perms.txt target table may list more than the hook changes (CHANGES holds what is actually changed)"

key-files:
  created:
    - tests/harness/test_row7.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_rowhooks.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_evidence.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_boundaries.py
    - tests/harness/test_rows_plain.py
    - tests/harness/README.md

key-decisions:
  - "The probe and the precondition both read the effective user through one function (_effective_user) and the probe's mode change and create each go through one small function (_chmod_path, _create_probe_file), so a test stands in a root account, a mount that ignores modes or another error without patching the os module for the whole run"
  - "The row 7 hook changes the project folder only (CHANGES), while its perms.txt lists the project folder as a dot and thoughts/plans (TARGETS); '.' is accepted in a table only as a folder entry"
  - "The printed checkpoint is the body of the last closed fenced block whose lines include both headings as whole lines; the reason none, too-large or nul goes to chain.json; the text is never repeated there"
  - "A row on the printed-checkpoint chain files no resume-line.txt (the committed row has none and the row prints no resume line); the README says which shape the run had"
  - "The restore mode is 755 as planned although the seed makes its folders 700; the committed row listed 755 and the run root itself is private"

patterns-established:
  - "Row7Run in test_row7 records the project and plans modes at the start of every stage by wrapping run_stage, and can end on an expected exception"

requirements-completed: [HARN-12, RERUN-01]

coverage:
  - id: D1
    description: "--dry-run --row row7-all-destinations-denied prints 3 stages, 2 sessions, the turns and caps 15/0.30, 60/1.30, 15/0.40, worst case 2.00 USD (the caps sum to exactly the row cap, so the plan text is true) and allowlist 35 rules, exits 0, starts no process and creates no harness home or run folder; with the effective user patched to root it names the skip and still creates nothing"
    requirement: HARN-12
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#Row7RegistryTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "The live probe creates raw/probe-chmod exclusively, sets 555, requires PermissionError with errno EACCES from an exclusive create, returns the folder to 755 on every path and never deletes it; root, a created file, any other error, an unpreparable folder and an unknown probe id are fixed-words reasons with no path; a planted link in place of the folder is refused and nothing outside changes; the setup guard's first raw listing holds the probe folder"
    requirement: HARN-12
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#ChmodProbeTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A failed probe (root, created file, other error) files SKIPPED-row7-all-destinations-denied with a README naming the cause and ending Reviewer verdict: PENDING, exits 10, starts no session, writes no ledger line and no stage record, leaves the project at its seeded mode, and prints lines with no path and no verdict word"
    requirement: HARN-12
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#SkippedRowTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "A scripted row 7 chain runs three stages in two sessions: the project is 700 at s1 (as seeded), 555 at s2 and s3, 755 again before filing; snap-1b-after-restriction holds a mode-only perms.txt of two lines; s3's stored prompt equals the printed block verbatim; the boundary list names setup, s1, s1-restrict-project-555, s2 and s3; the ledger holds three launches and three settlements; the snapshots after the restriction show no change; the mechanical checks count a scripted chmod and print five states"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#Row7ChainTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_row7.py#Row7CommandCountTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "extract_printed_checkpoint: a line-based scanner honouring the opening fence length; last matching block wins; a shorter inner fence does not cut it and a same-length inner fence closes it (documented); both headings must be whole lines inside a closed fenced block; 8192 bytes pass and 8193 do not (bytes, not characters); a NUL gives reason nul; a last candidate that breaks a bound is not replaced by an earlier one; it finds the block in the committed Final replies of rows 7, 3c and 4b, read in place"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#PrintedCheckpointTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "A reply with no usable block (none, oversize, missing heading, heading text only in a Bash result) records NO-PRINTED-CHECKPOINT with the reason, runs no s3, prints stage s3: not run (NO-PRINTED-CHECKPOINT), files two stages and exits 0; a block with a NUL cannot be filed because the leak gate refuses a NUL byte (exit 14) and no third process runs"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#NoPrintedCheckpointTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_row7.py#NulReplyTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "--refile accepts exactly two shapes for row 7: marker found with three stages and NO-PRINTED-CHECKPOINT with two; found with two, none with three, NO-RESUME-LINE, an empty, missing or odd marker and a chain record of the wrong shape are refused and nothing is filed; the resume-line rows keep their own two shapes and refuse the new marker word"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#RefileShapeTests"
        status: pass
    human_judgment: false
  - id: D8
    description: "The project folder is restored to 755 after the last snapshot and the breach check and before filing on every exit path: a stop in s1 (never applied, stays as seeded), s2 and s3, a breach in s2 or s3, an exception in s2 or s3; the hook changes the project folder only; a link, a swapped parent, a non-folder entry, another owner and a dot-dot, empty or odd table part are refused; a project swapped for a link inside s2 ends the row on an exception with nothing outside changed"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_row7.py#Row7RestoreTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_row7.py#Row7HookSafetyTests"
        status: pass
    human_judgment: false
  - id: D9
    description: "Whether Claude Code 2.1.310 runs normally in a project folder at mode 555 and what the real denial looks like are unobserved until the row 7 run of wave A; the scripted claude proves the pipeline and the live probe proves the denial on the machine that runs the matrix (it holds on the machine that built this plan: result None, probe folder back at 755)"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan: only a real stream shows the tool result for a create under a project folder at mode 555"

duration: about 2 h 30 min (estimate; the start time was not recorded), of which about 25 min were the full-suite runs
completed: 2026-11-02
status: complete
---

# Phase 4 Plan 6: Row 7 with the live chmod probe and the printed-checkpoint chain Summary

**Row 7 (all destinations denied) runs through the engine: a live probe proves on the machine that a folder at mode 555 refuses a create before any spend (otherwise the row is filed SKIPPED with exit 10), the harness sets the project folder to 555 after the work turn and back to 755 before filing on every exit path, and the third stage is a fresh session whose prompt is the checkpoint the `/preclear` reply printed, found by a line-based fence scanner (or the marker NO-PRINTED-CHECKPOINT and no third stage).**

## Performance

- **Duration:** about 2 h 30 min (estimate; the start time was not recorded)
- **Completed:** 2026-11-02
- **Tasks:** 3
- **Files modified:** 10 (1 created)

## Accomplishments

- `pc_rows`: `ROW7`, `CHAIN_RESUME_LINE`, `CHAIN_PRINTED_CHECKPOINT`, `PROBE_NONE`, `PROBE_CHMOD`, the `RowSpec` fields `chain` and `probe` (defaulted, so older constructions work), and the row 7 entry: the committed three stages (0.30, 1.30 and 0.40 with 15, 60 and 15 turns), the plain profile with the chmod and touch extras, memory pinned, the committed row 7 fixture and `/preclear` prompt, a harness-worded setup paragraph, the hook `("s1", "restrict-project-555")` and the write-free precondition (lazy, so the module still imports nothing heavy). `seed_row7` in `pc_rowseeds`.
- `pc_rowhooks`: `chmod_denial_probe` (exclusive `raw/probe-chmod`, 555, an exclusive create that must raise EACCES, 755 on every path, never deleted), `chmod_precondition` (a reason only for the root account), `run_probe`/`PROBES`, the hook `restrict-project-555` with finalizer `restore-project-755` and the snapshot `snap-1b-after-restriction`. `CHANGES` separates what a hook changes (the project folder) from what `perms.txt` lists (the project folder as `.` and `thoughts/plans`); `.` is accepted in a table only as a folder entry and goes through the same checks (real folder in the run root, owner, realpath, no links below it).
- `pc_row1`: `fenced_blocks` (line-based, honours the opening fence length, at most three spaces of indent, unclosed fences are not blocks), `printed_checkpoint` (text and reason), `extract_printed_checkpoint`, `MAX_PRINTED_CHECKPOINT_BYTES` (8192), `MARKER_NO_CHECKPOINT`, the chain dispatch on `spec.chain` (the resume stage takes the block as its prompt, stored in raw like every prompt; no block means no s3), `_write_chain_checkpoint`, the probe call after the seed and boundary list and before snapshot 0, and `_skipped` (SKIPPED label through `pc_evidence.file_skipped`, exit 10, `SKIPPED: <reason>` first line, no ledger line).
- `pc_evidence`: `_chain_incomplete` takes the none-marker word from the row's chain strategy (a row never accepts the other row type's word); no `resume-line.txt` for the printed-checkpoint chain; one README line says which shape the run had.
- `pc_testutil`: scripted op `try_write` (folders first, exclusive create, on PermissionError a Write tool_use and a tool_result with `is_error` true and a content text beginning `EACCES: permission denied`), `printed_checkpoint_stage`, and `default_row_stages` gives row 7 that script for its `/preclear` stage (so `--all` tests, which run every implemented row on defaults, keep working).
- Tests: `test_row7.py` (98 tests: registry and seed, the probe, the skip, the chain, the printed checkpoint including the committed replies of rows 7, 3c and 4b, no-checkpoint chains, NUL, refile shapes, restore on every exit path, command counts, hook safety, the `try_write` op). Two earlier tests that encoded "only row 6 names a hook / the hook table holds one hook" were moved onto the new meaning without deleting any test.
- Suite: 1625 -> 1723 tests (3 skipped as before), green through `tests/harness/selftest` with the `0 model calls` banner.

Suite count: 1723

## Task Commits

1. **Tasks 1 to 3 (tracer, live probe and SKIPPED label, edge cases and README): row 7 end to end** - `00b12cc` (feat)

**Plan metadata:** the SUMMARY commit that follows (docs: complete plan). STATE.md, ROADMAP.md, WINDOWS.md and state.json were not touched; the orchestrator updates tracking.

_Tracer gate: the tracer `<verify>` (the row 7 tests, the tripwire dry run, `test_stages.py`, `test_boundaries.py`, `test_rows_plain.py`) was run and passed before the commit, and the whole suite also passed. No `blocking-human` gate was set. The model-free live probe was run in a fresh folder under the session scratch area: root False, precondition None, probe result None (the denial holds), probe folder back at 755 and empty._

## Files Created/Modified

- `tests/harness/test_row7.py` - new
- `tests/harness/pc_rows.py`, `pc_rowseeds.py`, `pc_rowhooks.py`, `pc_row1.py`, `pc_evidence.py`, `pc_testutil.py` - as above
- `tests/harness/test_boundaries.py`, `test_rows_plain.py` - one assertion each moved onto the new meaning
- `tests/harness/README.md` - the Layout line for `test_row7.py`, updated lines for `pc_row1.py` and `pc_rowhooks.py`, and one paragraph on the probe, the 555 restriction, the SKIPPED outcome and the printed-checkpoint chain

## Decisions Made

See `key-decisions` above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two Phase 4 tests encoded the old meaning and were moved, not deleted**
- **Found during:** full-suite run
- **Issue:** `test_boundaries.py` asserted the hook and finalizer tables hold exactly row 6's ids, and `test_rows_plain.py` asserted only row 6 names a hook; both now see row 7's hook.
- **Fix:** each assertion now lists both hooks, with a comment; no test deleted or weakened. Neither file is in `files_modified`.
- **Commit:** 00b12cc

**2. [Rule 3 - Blocking] The `--all` driver tests ran row 7 on the default row scripts**
- **Found during:** full-suite run (`MatrixScopeTests`, two failures)
- **Issue:** `default_row_stages` gave row 7 the generic `/preclear` script, which writes the checkpoint file and raises inside a project folder at mode 555.
- **Fix:** `printed_checkpoint_stage()` and a branch in `default_row_stages` for a spec on the printed-checkpoint chain (in `pc_testutil`, which is in `files_modified`).
- **Commit:** 00b12cc

**3. [Rule 1 - Bug in plan text] The restore mode widens the seeded mode**
- **Issue:** the seed makes the project and `thoughts/plans` mode 700; the plan fixes the restriction at 555 and the restore at 755 (the committed row listed 755).
- **Fix:** followed the plan. `perms.txt` therefore reads `. 555` and `thoughts/plans 700`; the project ends at 755 inside a private run root. Not changed to a "restore the previous mode" rule because the plan and its truths name 755.

**4. [Rule 2 - Missing critical functionality] A NUL in the printed block cannot be filed**
- **Issue:** the plan says a block holding a NUL records the marker and files the stages that ran, but the leak gate refuses any file with a NUL byte (`refused-binary`), and the full s2 trace holds the reply.
- **Fix:** none in the gate (it is correct to refuse binary content). The marker, reason `nul` and "no s3" are recorded and tested; the row ends with the gate's exit 14 and its fixed lines, and the raw files stay in the run root. Documented in the README paragraph and tested in `NulReplyTests`.

**5. [Rule 3 - Blocking] Test seams in `pc_rowhooks`**
- **Issue:** the plan names patches of "the effective user id function, os.chmod inside the probe module, the exclusive writer"; those names are the global `os` and `pc_runroot` objects, which the rest of a row run also uses.
- **Fix:** three one-line functions (`_effective_user`, `_chmod_path`, `_create_probe_file`) are the seams; behaviour is identical.

**6. [Rule 3 - Blocking] A project swapped for a link inside s2 ends on an exception, not a STOPPED label**
- **Issue:** the plan mentions the finalizer re-check ending as exit 11 with a STOPPED folder; when the project itself becomes a link mid-stage the engine's own project snapshot raises `ManifestError` first (existing behaviour, fail closed, nothing filed).
- **Fix:** the engine test asserts that path (the restore on the exception path is refused, nothing outside changes, nothing filed, the moved folder stays at 555 inside the run root); the finalizer's own refusal of a link, a swapped parent and a wrong owner is covered directly in `Row7HookSafetyTests`.

**7. [Rule 3 - Blocking] Tasks 1 to 3 are one commit**
- **Issue:** the README Layout test needs `test_row7.py` in the same commit that adds it, the probe tests need Task 1's registry entry, and the plan requires a green suite at every commit.
- **Fix:** one feature commit; the three tasks' tests and gates were all run on it.

**8. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- **Issue:** a failing `test(...)` commit would break the green-suite-per-commit rule (same as plans 04-01 to 04-05).
- **Fix:** tests were written with the code and run before the commit. See TDD Gate Compliance.

**9. [Plan text note] The frozen-path guard names `e85d347`; the orchestrator's command names `56e155c`**
- Used `56e155c` as instructed: no difference for SKILL.md, references, tests/fixtures and the 2026-10-20 evidence (0 files), SKILL.md is 11994 bytes. Worst case is truthfully 2.00 USD for this row, so no wording deviation arose there.

---

**Total deviations:** 9 (1 bug in plan text, 1 missing critical, 7 blocking or notes). **Impact:** none changes behaviour outside row 7's own code paths and test support; deviations 1, 2 and 5 touch shared test files in a way that keeps every earlier test meaning.

## TDD Gate Compliance

Plan type is `execute` (not `type: tdd`), so the gate commands do not run; the tasks carry `tdd="true"`. The failing state was not committed because the plan requires a green suite at every commit.

## Authentication Gates

None.

## Issues Encountered

- The sandbox guard refuses commands that name the version control tool next to computed values and long inline scripts; patches and the append of test text were done from small files in the session scratch folder with literal paths. The per-plan head ledger file was not created because the first attempt was refused; `plan_head_before` is the verified base commit (`git rev-parse HEAD` and the merge base both equalled it before any edit), and the measured count is 1 commit.
- The first row 7 run of the no-checkpoint cases failed to file because the leak gate refuses a long run of one repeated character and a NUL byte in a trace; the tests use varied filler text, and the NUL case became its own documented class (deviation 4).

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. The new write surface is `os.chmod` on the probe folder this module created (T-04-23: lstat, owner and realpath check before every change, restored on every path, never deleted, no path from the model, environment or command line) and `os.fchmod` on one opened descriptor of the project folder (T-04-24: the same checks as plan 04-05, tested with a link, a swapped parent, a wrong owner and a malformed table entry). A harness process killed between the hook and the finalizer leaves the project folder at 555 inside the run root (accepted, as in plan 04-05).

## User Setup Required

None - no external service configuration required.

## Notes for plan 04-07 (pc_review.py) and later

- Import `pc_row1.printed_checkpoint(text)` (returns `(text, reason)`) or `extract_printed_checkpoint(text)`; `fenced_blocks(text)` is the scanner. A block is the lines between the fences, joined with newlines, no fences, at most 8192 bytes, no NUL. Both headings must be whole lines (trailing blanks allowed). A same-length inner fence closes the block (documented and tested). Do not use `extract_resume_line` for row 7.
- The reviewer's Do-not-redo parsing is not here: `04-RESEARCH.md` has the sketch (bulleted entries, plain lines when there is no bullet for row 4b).
- Run record of a row 7 chain: `raw/chain.json` has exactly `marker` (`found` or `NO-PRINTED-CHECKPOINT`), `checkpoint_bytes` and `checkpoint_reason` (null when found, else `none`, `too-large` or `nul`). The checkpoint text is only in `raw/s3.prompt` (and inside the stored s2 stream); `raw/s3.prompt` exists only when s3 ran.
- Filed names: `s1-work-*`, `s2-preclear-*`, `s3-resume-*` files plus five snapshot folders (`snap-0-setup`, `snap-1-after-work`, `snap-1b-after-restriction` with `perms.txt`, `snap-2-after-preclear`, `snap-3-after-resume`). A row 7 folder has no `resume-line.txt`. Its README line `- chain shape:` states found (with bytes) or NO-PRINTED-CHECKPOINT (with the reason).
- Boundary names for row 7: `setup`, `s1`, `s1-restrict-project-555`, `s2`, `s3`. `pc_evidence.STAGE_ORDER` is still `s1, s2, s3`, which is exactly row 7's stages.
- The perms lines of a real run read `. 555` and `thoughts/plans 700` (the seed's folder modes are 700); a SKIPPED folder holds only a README and the line `SKIPPED: <fixed-words reason>` is the first printed line.
- A reply whose checkpoint holds a NUL byte cannot be filed (exit 14 from the gate); `--refile` of such a run root stays refused for the same reason. Three attempts of the triple that hit this would show as raw-only runs: plan 04-07's table has to be able to read them from the run root or list them as unfiled.
- The real tool result for a create under a project folder at mode 555 with 2.1.310 is unobserved (D9); the first real row 7 stream in wave A settles it, and the probe result on the machine that runs the matrix is the proof the denial works there.

## Self-Check: PASSED

- Created files exist: `tests/harness/test_row7.py`, this summary.
- The task commit is an ancestor of HEAD: `00b12cc`.
- `commits:` was measured as the count from the verified base to HEAD before this summary commit (1).
- Final gates: `tests/harness/selftest` 1723 tests OK with the `0 model calls` banner (floor 1625); `scripts/test-hooks.sh` 29 PASS; `test_row7.py` also green on the 3.9.6 system interpreter; leak gate over `tests/harness` 82 files, 0 findings; the secret scanner over `tests/harness` clean; frozen paths (`SKILL.md` 11994 bytes, `references`, `tests/fixtures`, the 2026-10-20 evidence) unchanged against `56e155c`; no attribution trailer in any commit of the range; the change list names only files under `tests/harness` plus this summary.

---
*Phase: 04-full-matrix-row-7-and-review*
*Completed: 2026-11-02*
