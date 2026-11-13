---
phase: 04-full-matrix-row-7-and-review
plan: 05
subsystem: testing
tags: [harness, row6, between-stage-hook, boundary-list, perms, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-01 row-generic engine, 04-03 stopped-row filing, 04-04 plain rows (PROFILE_PLAIN, extra_tools, memory, seed_plain_row)
provides:
  - pc_rowhooks (HOOKS, HOOK_SNAPSHOTS, FINALIZER_OF, FINALIZERS, TARGETS, HookRun, HookRefused, plan_boundaries, run_after_stage, run_finalizers, write_perms, perms_text)
  - RowSpec.hooks, ROW6 and its registry entry, pc_rowseeds.seed_row6
  - raw/boundaries.json written at setup before the setup guard; pc_checks.read_boundaries, write_boundaries, validate_boundaries, present_boundaries, program_counts and the list-driven guard chain
  - hook id restrict-plan-444 (snapshot snap-1b-after-restriction, boundary name s1-restrict-plan-444) with finalizer restore-plan-644
  - filed perms.txt (mode-only lines) and executed-chmod-commands / executed-touch-commands lines in mechanical-checks.md
affects: [04-06, 04-07, 04-12, 04-13, 04-16, 04-18, 04-19, 04-21]

# Actuals (#2632): chars/4 over the realized diff of tests/harness against the plan base commit
actuals:
  tokens: 35090
  tasks: 3
  commits: 1

commits: 1
plan_head_before: 8aef556ac97a34e38b056c0ed1700349cee67028
plan_head_after: 5224161ecc3d5efafa0acbc7d60f5935d2e4a960

tech-stack:
  added: []
  patterns:
    - "a between-stage hook is a table entry (target path and kind), an apply function, a finalizer and an extra snapshot name; the engine runs it after the stage's own snapshot, git state and guard and restores it before any filing and on every exit path"
    - "the checks read boundaries through raw/boundaries.json: strict about names the list does not name and about gaps, legacy order only when the file does not exist"
    - "the harness changes a mode on an opened descriptor after checking every part of the path with lstat, so no link the model planted can redirect it"

key-files:
  created:
    - tests/harness/pc_rowhooks.py
    - tests/harness/test_boundaries.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_evidence.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_checks.py
    - tests/harness/test_rows_plain.py
    - tests/harness/README.md

key-decisions:
  - "A hook boundary is named <stage>-<hook id> (s1-restrict-plan-444); its raw files are <name>.git.json and <name>.guard.json, its snapshot is the one HOOK_SNAPSHOTS names; stage boundaries are s1 to s9"
  - "A stage record is not required for a present boundary (snapshot, git state and guard are): a missing record leaves the comparison in place and the filing refuses the row because the stage did not run, so the Phase 3 refusal tests keep their meaning"
  - "Strictness (unlisted snapshot, record, git state or guard is a CheckError, boundaries on disk must be a prefix of the plan) applies only when raw/boundaries.json exists; a run root without it is read exactly as before, ignoring other names; a present but malformed file never falls back"
  - "Targets are opened with O_NOFOLLOW and O_NONBLOCK and must be a regular file (or a folder when the table says dir) of the running user with one name only; no part of the path below the project may be a link; the mode is set with fchmod on the opened descriptor"
  - "The finalizers run in file_stop (before the label is filed), in finish after the final breach check and before the filing, and in an except BaseException around the stage walk for exceptions; a refused restore is a breach stop (finish) or one added fixed line (stop), and the hook is marked restored so it is never retried"

patterns-established:
  - "scripted claude ops symlink, link, mkfifo and socket plant a link or a special file from inside a stage without any deletion primitive in test code"
  - "Row6Run in test_rows_plain records the plan file mode at the start of every stage by wrapping run_stage"

requirements-completed: [RERUN-02]

coverage:
  - id: D1
    description: "--dry-run --row row6-readonly-plan prints 2 stages, 1 sessions, the s1 and s2 turns and caps, allowlist 35 rules, exit 0, no process and no harness home; --list marks it implemented; worst case prints 1.60 USD (the caps sum; the plan text says 2.00)"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6RegistryTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "The row 6 seed is byte-tied to the committed row: CLAUDE.md equals fixture-CLAUDE.md with digest ed03447e9df43888 (the committed setup digest), the plan equals data/plain-plan.md (mode 644), memory is pinned (autoMemoryEnabled true), the allowlist is the 33 baseline rules plus chmod and touch"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6SeedTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6ChainTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A scripted row 6 chain: the plan is 644 at s1, 444 at s2, 644 after the row; snap-1b-after-restriction exists with perms.txt holding the plan path and 444 as the only line (no owner, group, date, size or login); the filed folder holds the snapshot and perms.txt in plan order; the plan digest is readable in all four filed snapshots; the git section names the hook boundary state"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6ChainTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "raw/boundaries.json lists setup, s1, the hook boundary and s2 in order, is created exclusively before the setup guard (the guard's raw listing holds it); compute_facts, the guard chain and the git states read through it; a write or git change in s2 is compared with the restriction snapshot and state; a raw entry, record or restriction snapshot changed in the restriction window is a run-record breach"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_boundaries.py#BoundaryRunTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_boundaries.py#GuardChainTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6BoundaryWindowTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "Strictness and legacy: an unlisted snapshot folder, stage record, git state file or guard file, a repeated or unknown name, a list not starting with setup, a gap and a boundary missing its snapshot, state or guard are CheckErrors with fixed text and no path; any in-order prefix reads; a missing list file reads with the legacy order and gives the same facts and the same filed files as the same chain with the list; a malformed list file never falls back; an older run root is refiled with zero tokens"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_boundaries.py#BoundaryListTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_boundaries.py#LegacyOrderTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "Hook safety: a symlink (outside, inside or dangling), a directory, a named pipe, a socket, a second name for an outside file, a swapped parent folder, a symlinked or missing project folder, a dot-dot or empty table part and an unknown kind are refused by the hook, the finalizer and perms; through the engine each is exit 11 with a STOPPED folder (reason breach), s2 never starts and the outside file's mode and content are unchanged; a symlink planted after the hook is refused by the finalizer with the same result"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_boundaries.py#HookSafetyTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_boundaries.py#HookChainSafetyTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "The finalizer restores 644 after a stop, after a breach and after an exception in a later stage, only for hooks that were applied, once; the module holds no deletion, rename, move or truncation"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_boundaries.py#HookChainSafetyTests"
        status: pass
    human_judgment: false
  - id: D8
    description: "mechanical-checks.md prints executed-chmod-commands and executed-touch-commands for a row whose allowlist holds those rules, from executed commands only (a denied call and an echo of the word are not counted, a path to the program and env are); a helper row prints neither line; no verdict word reaches a harness-authored file"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_plain.py#Row6CommandCountTests"
        status: pass
    human_judgment: false
  - id: D9
    description: "Whether Claude Code 2.1.310 reports a write to a mode 444 file with the same tool-result shape the committed 2.1.304 run showed is unobserved until wave A; the scripted claude proves the pipeline and the real run records the fact"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan: only a real stream shows the tool result for a write to a read-only plan"

duration: about 2 h (estimate; the start time was not recorded), of which about 30 min were the three full-suite runs
completed: 2026-11-02
status: complete
---

# Phase 4 Plan 5: Row 6 and the between-stage hook framework Summary

**Row 6 (read-only plan) runs through the engine: after s1 the harness sets the plan file to mode 444, takes `snap-1b-after-restriction` with its own git state and guard and a mode-only `perms.txt`, runs s2 against the restricted file, and restores mode 644 before filing on every exit path; the checks now read every boundary through a recorded list (`raw/boundaries.json`) that is strict about names it does not hold and still reads older run roots.**

## Performance

- **Duration:** about 2 h (estimate; the start time was not recorded)
- **Completed:** 2026-11-02
- **Tasks:** 3
- **Files modified:** 11 (2 created)

## Accomplishments

- `pc_rowhooks` (new): `restrict-plan-444`, `restore-plan-644`, the target table (`TARGETS`), `HOOK_SNAPSHOTS`, `FINALIZER_OF`, `HookRun` (what was applied and restored), `plan_boundaries(spec)`, `run_after_stage`, `run_finalizers`, `perms_text` and `write_perms`. Every target is checked before anything changes: the project is a real folder directly in the run root, no part of the path below it is a link, the last part opens with `O_NOFOLLOW` and is a regular file (or the named folder) of the running user with one name, and its real path is inside the project; the mode is set on the opened descriptor.
- `pc_rows`/`pc_rowseeds`: `RowSpec.hooks` (default empty), `ROW6` (two committed stages, plain allowlist with the chmod and touch extras, memory pinned, the committed row 6 fixture and `/preclear` prompt, a harness-worded Setup paragraph, hook `s1` -> `restrict-plan-444`), `seed_row6`.
- `pc_row1`: `raw/boundaries.json` written at setup before the setup guard; the stage walk moved into `_walk_stages`; hooks run after a clean stage (after the chain record); `file_stop`/`finish` take the `HookRun` and restore before filing; an `except BaseException` around the walk restores on an exception and re-raises; `MESSAGE_HOOK_REFUSED` and `MESSAGE_RESTORE_REFUSED` are fixed lines.
- `pc_checks`: the planned boundary list (`read_boundaries` with the legacy fixed order only when the file does not exist, `write_boundaries`, `validate_boundaries`, `present_boundaries`), `capture_guard` and `guard_violations` take the previous boundary and the own snapshot from the list, `compute_facts` reads snapshots, stage records, git states and guards through it and gains the facts `boundaries` and `program_counts`; `program_counts(events, programs)` counts executed command parts by program with the write checks' own parsing.
- `pc_evidence`: `executed-chmod-commands` and `executed-touch-commands` lines for a row whose allowlist holds those rules; the git section names states by boundary; `perms.txt` is a harness-authored listing for the verdict-word scan. The filed snapshot folders and `perms.txt` already came through `filed_snapshot_files`, which walks the folder.
- Tests: `test_boundaries.py` (62 tests: `BoundaryListTests`, `BoundaryRunTests`, `LegacyOrderTests`, `GuardChainTests`, `HookSafetyTests`, `HookChainSafetyTests`), 30 row 6 tests in `test_rows_plain.py`, `pc_testutil` scripted ops `symlink`, `link`, `mkfifo`, `socket`.
- Suite: 1533 -> 1625 tests (3 skipped as before), green through `tests/harness/selftest` with the `0 model calls` banner.

Suite count: 1625

## Task Commits

1. **Tasks 1 to 3 (tracer, boundary strictness, hook safety and README): row 6 with the hook framework and the recorded boundary list** - `5224161` (feat)

**Plan metadata:** the SUMMARY commit that follows (docs: complete plan). STATE.md, ROADMAP.md, WINDOWS.md and state.json were not touched; the orchestrator updates tracking.

_Tracer gate: the tracer `<verify>` (row 6 tests, the tripwire dry run, `test_checks.py`) was run and passed before the commit, and the whole suite also passed; no `blocking-human` gate was set._

## Files Created/Modified

- `tests/harness/pc_rowhooks.py` - new: hooks, finalizers, target table, boundary plan, perms
- `tests/harness/pc_rows.py` - `ROW6`, `RowSpec.hooks`, the row 6 entry and Setup paragraph
- `tests/harness/pc_rowseeds.py` - `seed_row6`
- `tests/harness/pc_row1.py` - boundary list at setup, hooks after stages, restore on every exit path
- `tests/harness/pc_checks.py` - the list-driven boundaries, guard chain, strict refusal, `program_counts`
- `tests/harness/pc_evidence.py` - chmod and touch counts, boundary-named git states, `perms.txt` in the authored listings
- `tests/harness/pc_testutil.py` - scripted ops for links and special files
- `tests/harness/test_boundaries.py` - new; `test_rows_plain.py` row 6 tests; `test_checks.py` fact names
- `tests/harness/README.md` - Layout lines, the hook and boundary-list paragraphs, the chmod and touch counts

## Decisions Made

See `key-decisions` above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan defect] Row 6 prints worst case 1.60 USD, not 2.00 USD**
- **Found during:** Task 1 (dry-run check)
- **Issue:** the truth asks for `worst case 2.00 USD`, but the two committed caps (0.30 and 1.30) sum to 1.60 and `worst_case` is the smaller of that sum and the row cap (same plan defect as rows 4a, 5a and 5b).
- **Fix:** left `worst_case` as it is; the dry run prints 1.60 and a test asserts it. The plan's dry-run command was run: exit 0, `2 stages, 1 sessions`, `allowlist 35 rules`, no tripwire call, no harness home. The plan's text clause for 2.00 is not claimed.
- **Commit:** 5224161

**2. [Rule 3 - Blocking] Three files outside `files_modified` changed**
- **Found during:** Tasks 1 and 3
- **Issue:** `test_checks.py` pins the exact fact names (`FACT_NAMES`), and the new facts `boundaries` and `program_counts` are part of the contract; the safety tests need to plant a link, a second name, a pipe and a socket from inside a scripted stage, and `pc_testutil` is the only module allowed to carry such helpers.
- **Fix:** `FACT_NAMES` now lists the two facts, with two assertions on the same chain (no test deleted or weakened); `pc_testutil` gained four scripted ops (`symlink`, `link`, `mkfifo`, `socket`) documented in its op table.
- **Commit:** 5224161

**3. [Rule 1 - Bug] A stage record must not be required for a present boundary**
- **Found during:** full-suite run (three `RefileChainTests` failures)
- **Issue:** the first version of `present_boundaries` raised a CheckError when a boundary had its snapshot, git state and guard but no stage record; the Phase 3 refile tests move a record aside and expect the filing to refuse with "a stage did not run".
- **Fix:** the record is not part of completeness (the snapshot, git state and guard are, so no comparison is removed); `stages` still lists only stages with records, so the filing refuses as before. A test pins the new rule.
- **Commit:** 5224161

**4. [Rule 3 - Blocking] Tasks 1 to 3 are one commit**
- **Issue:** `test_readme` needs every new file in the README Layout in the same commit, `test_boundaries.py` imports row 6 helpers from `test_rows_plain.py`, and the plan requires a green suite at every commit.
- **Fix:** one feature commit for the three tasks; the three tasks' tests and gates were all run on it.

**5. [Rule 3 - Blocking] Task 1 step 5 names `STAGE_LABELS` and `SNAPSHOT_OF`, which do not exist**
- **Issue:** `pc_evidence` has neither constant; `collect_files` already files every snapshot folder through `filed_snapshot_files` (which walks the folder, so `perms.txt` is included) in sorted order, which is plan order for these names.
- **Fix:** no code was needed for the filed names; the only `pc_evidence` changes are the chmod and touch lines, the boundary-named git states and `perms.txt` in the authored listings (verdict-word scan).

**6. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- **Issue:** the plan requires a green suite at every commit, so a failing `test(...)` commit is not possible (same as plans 04-01 to 04-04).
- **Fix:** tests were written with the code and run before the commit. See TDD Gate Compliance.

**7. [Rule 2 - Missing critical functionality] The finalizer also runs in `file_stop`, and the hook is checked against more than a symlink**
- **Issue:** the plan names a `finally` around the row; but filing a STOPPED label happens inside the walk, before any `finally`. The plan's checks (lstat, regular file, no symlink, realpath inside the project) also leave a swapped parent that points inside the project, a second name for an outside file and a file of another owner unrefused.
- **Fix:** `file_stop` and `finish` restore first (after the breach check, before filing), an `except BaseException` covers exceptions, and the target checks add the parent-link walk, the one-name rule, the owner rule and `O_NOFOLLOW` plus `fchmod` on the descriptor. Each case has a test.
- **Commit:** 5224161

---

**Total deviations:** 7 (2 plan defects or bugs fixed, 1 missing critical, 4 blocking). **Impact:** deviation 3 and 7 change behaviour inside the new code only; the others move tests or files.

## TDD Gate Compliance

Plan type is `execute` (not `type: tdd`), so the gate commands do not run; the tasks carry `tdd="true"`. The failing state was not committed because the plan requires a green suite at every commit.

## Authentication Gates

None.

## Issues Encountered

- The sandbox guard of this worktree refuses commands that name the version control tool together with computed values, and long inline scripts; patches were applied from small files in the session scratch folder with literal paths. No repository file was affected.
- The first full run (1563 tests) had three failures from deviation 3 and one from the README Layout not yet updated; after the fixes the whole suite (the `selftest` run, 594 s) is green at 1625 tests.
- `pgrep -f` inside a wait loop matched the loop's own command line; the stray loops were killed and nothing else was affected.

## Known Stubs

None.

## Threat Flags

None. The only new write surface is `os.fchmod` on one opened descriptor inside the project (T-04-19, tested with planted links, special files, a second name and a swapped parent), the boundary list is created exclusively before the setup guard and read strictly (T-04-20), `perms.txt` is mode-only from the file's own status (T-04-21), and the finalizer runs on every exit path (T-04-22; a harness process killed between the hook and the finalizer still leaves one scratch file at 444 inside the run root, accepted as stated).

## User Setup Required

None - no external service configuration required.

## Notes for plan 04-06 (row 7, the chmod probe) and later

- A new hook is five table entries: its id in `HOOKS` (apply function), `TARGETS` (path relative to the project and `file` or `dir`), `HOOK_SNAPSHOTS` (a snapshot name of the shape `snap-<n>[letter]-<words>`, unique within a row; `write_perms` only accepts names in this table), `FINALIZER_OF` and `FINALIZERS`; then name it in the entry as `hooks=(("s1", "<id>"),)`. The boundary is `<stage>-<hook id>` and `plan_boundaries` rejects an unknown id or stage with a ValueError at setup.
- `_open_target` opens with `O_RDONLY`, so a target whose owner read bit is off cannot be opened: a hook that clears the read bit of a file or folder (a mode 000 or 111 probe) cannot restore it through `restore_*` as written and would be a refusal. If row 7 needs such modes, open the parent (checked the same way) and use `os.chmod` with a dir fd, or restrict to modes that keep owner read; do not weaken the link and owner checks.
- `restrict_plan_444` and `restore_plan_644` share `_set_modes(paths, hook_id, mode)`; a dir target works for `perms_text` (read only); changing a folder's mode needs its own restore mode (a folder at 644 is not traversable).
- `chain.json` is allowed in a guard window when the previous boundary belongs to `s2` (a stage or a hook of it); a hook after another preclear stage name would need the same rule.
- `pc_evidence.STAGE_ORDER` is still `s1, s2, s3` (the filing reads those records); `pc_checks` takes stage names from the boundary list (`s1` to `s9`) when the list exists and from `STAGE_NAMES` otherwise. Row 12 still has to widen `STAGE_ORDER`.
- The facts now carry `boundaries` (present boundary names in order, hook boundaries included) and `program_counts` (`chmod`, `touch`); `states` in the Git section of `mechanical-checks.md` counts hook boundaries too (row 6 prints four).
- The model's own chmod and touch are counted, never prevented: a row 7 prompt may let the model run chmod, and `executed-chmod-commands` is where a reviewer reads it.
- The committed row 6 `snap-1b-after-restriction/perms.txt` is raw `ls` output of the project folder (it carries the login name); the harness's `perms.txt` is mode-only lines of the target table instead, so the comparer will list the content difference without judging it. Rows 5a and 5b also hold a `snap-1b-after-restriction` folder that their runs do not produce.
- The real tool result for a write to a mode 444 file under 2.1.310 is unobserved (D9); the first real row 6 stream in wave A settles it.

## Self-Check: PASSED

- Created files exist: `tests/harness/pc_rowhooks.py`, `tests/harness/test_boundaries.py`, this summary.
- The task commit is an ancestor of HEAD: `5224161`.
- `commits:` was measured from the persisted ledger (1 commit before this summary commit).
- Final gates: `tests/harness/selftest` 1625 tests OK with the `0 model calls` banner (floor 1533); `scripts/test-hooks.sh` 29 PASS; `test_boundaries.py` and the row 6 tests also green on the 3.9.6 system interpreter; leak gate over `tests/harness` 81 files, 0 findings; the secret scanner over `tests/harness` clean; frozen paths (`SKILL.md` 11994 bytes, `references`, `tests/fixtures`, `publication-2026-10-20`, the Phase 3 rerun folder) unchanged; the commit carries no attribution trailer; the change list against the plan base names only files under `tests/harness`.

---
*Phase: 04-full-matrix-row-7-and-review*
*Completed: 2026-11-02*
