---
phase: 04-full-matrix-row-7-and-review
plan: 19
subsystem: testing
tags: [harness, clean-clone, bootstrap, scrubbed-environment, copy-back, zero-token]
requires:
  - phase: 04-18
    provides: finalize, the clone-facts schema, the partial-baseline README lines and the suite floor of 2248
provides:
  - pc_cleanclone.py, the bootstrap with the free --preflight-only probe and the full run from a clone
  - test_cleanclone.py, 99 zero-token tests on a scratch source repository and fake or scripted claude
  - a README section "The clean clone" and two Layout lines
affects: [04-20, 04-21]
key-files:
  created:
    - tests/harness/pc_cleanclone.py
    - tests/harness/test_cleanclone.py
  modified:
    - tests/harness/README.md
key-decisions:
  - "Every child process is the clone's own script under an environment built from an empty dict with seven names; the main tree's modules are imported only for the bootstrap's own checks"
  - "The preflight probe is a short inline program run by the clone's own interpreter call that uses the clone's pc_matrix stub check and preflight, so the printed fix lines are the driver's own and nothing is duplicated"
  - "A free step stops the run on any non-zero code except a 10 from the dry run; this is stricter than the plan's wording but equal in effect, because the matrix repeats every gate before spending"
  - "A matrix exit of 12 to 17 stops without finalize even if rows were filed (the plan's literal rule); the clone folder keeps them and a fixed line says so"
  - "Structural mismatches (a wrapper naming another stub or interpreter, a differing stub digest) end the run with 11 after the copy-back, like a non-zero other-helper call count"
  - "Child output is printed line by line after a scrub that replaces every known path with a token and any home, temp or system path with a generic token"
metrics:
  duration: about 2.5 hours including the full suite
  completed: 2026-11-10
status: complete
requirements-completed: [RERUN-02]
actuals:
  tokens: 60000
  tasks: 3
  commits: 3
commits: 3
plan_head_before: e3bccd2b649e1c8453b155561908153da2da625a
plan_head_after: ae75a55c8f8516dccf721ce04c5a2f34296334a2
---

# Phase 4 Plan 19: Clean-Clone Bootstrap Summary

**pc_cleanclone.py clones the repository into a never-used folder with a seven-name scrubbed environment and a throwaway home, proves before and after the run that no private helper was reachable or called, runs the matrix from the clone, finalizes with the clone facts and copies the baseline back through the leak gate, after a budget stop too; --preflight-only is the free probe for the throwaway-home login question. No model was started and nothing was spent.**

Suite count: 2347

## What was built

| Task | Commit | Result |
|---|---|---|
| 1 | dc328dd | folder layout, child environment, clone, pre-assertions and --preflight-only, with 42 tests and the README Layout lines |
| 2 | bc02895 | free steps, the matrix in the clone, post-assertions, the clone-facts file, finalize, copy-back and the listing, with the scripted full runs |
| 3 | ae75a55 | real-home, usage and no-path tests, the README section "The clean clone", the full suite and gates |

## Behaviour to know

- **Layout.** D is created exclusively under the caller's runs root as `clean-clone-<UTC stamp>` with `runs` and `home` made by the bootstrap and `repo` made by the clone. A second start in the same second exits 16 and leaves the first folder untouched. D is never deleted.
- **Environment.** Exactly HOME, PATH, PRECLEAR_HARNESS_HOME, PRECLEAR_RUNS_ROOT, DISABLE_AUTOUPDATER, TERM and LANG. HOME is D/home unless `--real-home`. PATH is the fixed system folders plus the folder of the pinned build. TERM and LANG are copied only when plain words.
- **Pre-assertions** (printed as counts, any non-zero ends with 11): runs folder or tracked runs path, checkpoint executables on the scrubbed PATH, a PATH search finding one, files named checkpoint in the clone and under D/home, identity keys and hook path keys in the clone's local configuration. Also: the runs root is usable under the child environment (12 if not) and the clone's own list has at least one entry.
- **Post-assertions**: per run root with a wrapper folder, the stub file must name the clone's stub and the py file the interpreter; per filed row the stub digest must equal the clone stub's digest; CALL lines are counted as stub calls or other calls. The counts go into D/clone-facts.json (validated with the reader of plan 04-18), outside the evidence tree.
- **Budget stop and stopped rows.** Matrix exits 10, 11, 18 and 19 with at least one outcome folder reach post-assertions, finalize and the copy-back. A scripted budget stop printed `entries: 21, folders: 3, not run: 18` with `Run state: partial` and exited 18 after the copy-back. A budget too small or malformed is refused with 18 by the dry run with nothing filed.
- **Copy-back** uses `pc_promote.promote` with the main tree's deny entries; an existing destination is refused with 17, a leak with 14.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] README Layout lines added in Task 1**
- **Found during:** Task 1 verification
- **Issue:** `test_readme` requires every file of the folder once in the Layout, so the suite was red after Task 1 without them.
- **Fix:** added the two Layout lines in the Task 1 commit; the paragraph stayed in Task 3.
- **Files modified:** tests/harness/README.md
- **Commit:** dc328dd

**2. [Rule 1 - Bug] A wrapper log line with no arguments was not counted**
- **Found during:** Task 2 tests
- **Issue:** the CALL pattern was matched against a line that still held its newline, so a call with no arguments (`<time> CALL`) did not count.
- **Fix:** the line is stripped before matching; a test covers it.
- **Files modified:** tests/harness/pc_cleanclone.py
- **Commit:** bc02895

### Judgement calls (no rule applied)

- The module was written before its tests in Task 1 (TDD_MODE was false); the tests were then written against the stated behaviour and a defect found by them was fixed (item 2).
- The free-step stop rule is stricter than the plan's text (any non-zero except a dry-run 10), with the same external result, because the matrix repeats every gate before any spend.
- A matrix exit of 12 to 17 with rows already filed is not finalized (the plan's literal rule); this is the one path where measured rows would stay in the clone, which a fixed line reports and which plan 04-20 should know.
- Exit 11 also covers structural mismatches (wrong stub, wrong interpreter, differing digest), not only a non-zero other-call count.

## Known Stubs

None.

## Threat Flags

None. The bootstrap adds no network endpoint; the clone step reads the source the caller names, with no credentials allowed in the address.

## Notes for plan 04-20 (rehearsal, checkpoint and the paid run)

- **Free rehearsal command:** `python3 -E -s -B tests/harness/pc_cleanclone.py --claude <ABSOLUTE BUILD PATH> --preflight-only` from the main tree, after the Phase 4 code is pushed. It clones, asserts, runs the stub check and strict preflight under the scrubbed environment and stops. Exit 0 means logged in under the throwaway home. Exit 12 prints the login fix line and means the throwaway home hides the login; the fallback is `--real-home`, which needs bokiko's word. Exit 13 is an untested build. Exit 11 is a pre-assertion count or a failed probe step.
- **Full-run command:** `python3 -E -s -B tests/harness/pc_cleanclone.py --claude <ABSOLUTE BUILD PATH> --budget <AMOUNT> [--selftest]`. The clone's self-test takes about 15 minutes. The dry run inside refuses a malformed or too small budget with 18. The `--all` worst case is above the 25.00 flag cap, so a stop with exit 18 after some rows is expected for a small budget and is filed as partial.
- **Env names the child gets:** HOME, PATH, PRECLEAR_HARNESS_HOME, PRECLEAR_RUNS_ROOT, DISABLE_AUTOUPDATER, TERM, LANG.
- **Exit codes:** 0 done; 2 usage; 10, 11, 18, 19 the matrix's own codes, passed through after filing; 11 also for a pre-assertion count, a helper call or wrapper naming anything but the clone stub, or a listing that does not add up; 12 blocked (runs root, harness home or login); 13 untested build; 14 leak at the copy-back; 15 scanner error; 16 folder name taken; 17 copy-back destination exists.
- **Where things land:** D is `clean-clone-<UTC stamp>` under the caller's runs root, holding `repo`, `runs`, `home` and `clone-facts.json`. The finalized baseline is copied into the main tree's `tests/evidence` under the clone's dated name `rerun-<date>-<model>`. The spend ledger lives in the caller's harness home under the scope word `matrix`.
- **The checkpoint message to bokiko must show:** the D-10 wording difference (the harness home is handed over and CLAUDE_CONFIG_DIR is never read from the caller); the seven names; the preflight-only result and whether `--real-home` is needed; the clone head against the main tree head and whether they are equal (a push is a routine step before the real run); the budget against the 38.40 worst case of all 21 entries; that a budget stop files a partial baseline and the matrix is not resumable; and that the paid run waits for bokiko's go word.
- **Nothing in this plan pushes, commits in a clone or runs a login.** `--real-home` was used only against scratch homes in tests.

## Self-Check: PASSED
- tests/harness/pc_cleanclone.py and tests/harness/test_cleanclone.py exist; commits dc328dd, bc02895 and ae75a55 are ancestors of HEAD.
- `git rev-list --count e3bccd2b649e1c8453b155561908153da2da625a..HEAD` was 3 before this summary; `commits: 3` is measured from that base.
- Full suite: 2347 tests OK, banner shows 0 model calls; test_cleanclone also OK on Python 3.9.6; leak gate 0 findings; gitleaks clean; hook tests 29 PASS; all frozen diffs empty; attribution grep 0 lines; evidence diff since the base empty.
