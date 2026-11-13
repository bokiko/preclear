---
phase: 03-walking-skeleton-row-1
plan: 07
subsystem: testing
tags: [harn-09, write-boundary, git-safety, run-record-guard, gap-closure, zero-token]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_checks, pc_manifest, pc_row1, the scripted claude and the row rig (plans 03-02, 03-03)"
provides:
  - "GIT_HARDENING on every harness git call against the project, and a setup-digest pin that stops all git commands once the project's .git folder changed (CR-03)"
  - "write_escapes in bash_mentions, folded into the writes-outside-approved-roots breach (CR-02)"
  - "memory_probe and the git state files fail closed (WR-05)"
  - "A per-boundary run-root guard (raw/<name>.guard.json), the fact guard and the breach id run-record-changes (WR-01)"
affects: [03-08]

status: complete
actuals:
  tokens: 105000
  tasks: 3
  commits: 6
plan_head_before: 48e1cd2dc006deca4680ba794a0c795fd9f62854
plan_head_after: 679b75831325394540cf7c8ada1495f943eb5e0b

tech-stack:
  added: []
  patterns:
    - "A pin recorded at setup gates whether any command is started in a model-writable repository"
    - "A per-boundary guard file compared pairwise, with the harness's own writes named per window"

key-files:
  created: []
  modified:
    - tests/harness/pc_manifest.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_checks.py
    - tests/harness/test_row1_seed.py

key-decisions:
  - "The guard of a stage is written after that stage's record, not before it (deviation from the plan's placement; see below)"
  - "An env -C directory change is scoped to its own part, not carried to later parts of the command"
  - "env -S strings are split and read as the command they hold"

metrics:
  duration: "about 2 hours"
  completed: 2026-10-29
---

# Phase 3 Plan 07: Write Boundary And Git Safety Hardening Summary

**A command planted in the project's git configuration (core.fsmonitor or a clean-filter driver) never runs under the harness, an executed Bash command that writes outside the approved roots ends the row with exit 11, the run root's own record is guarded at every boundary, and two inputs that failed open now fail closed; all proved at zero tokens against the scripted claude.**

## What each task closed

| Task | Commits | Finding | Result |
|---|---|---|---|
| 1 (tracer) | 2f9853c test, 0bdb2bc feat | CR-03 (both command-execution routes) | Both options on all five git call sites; setup digest pin; planted fsmonitor and clean-filter never run; the row ends with 11 |
| 2 | 3595fd7 test, 8b4a1cf feat | CR-02, WR-05 | Executed write-capable Bash parts naming an outside place are a breach; memory probe and git state files fail closed |
| 3 | 7d6f03c test, 679b758 feat | WR-01 | Guard files, fact guard, breach run-record-changes, stage-prefixed folders listed by the snapshot |

## Test counts

- Before: 1117 tests (OK, 3 skipped), measured at the start on the system Python 3.9.
- After: 1167 tests (OK, 3 skipped) on `tests/harness/selftest` (banner "0 model calls") and on `/usr/bin/python3` 3.9.6 with `-I -B -m unittest discover`.
- New: 12 (Task 1), 21 (Task 2; the old memory-probe case was changed, not added) and 17 (Task 3), 50 in all.

## Facts for plan 03-08

- `bash_mentions(...)["write_escapes"]` is `{"count": int, "programs": {label: int}}`; `compute_facts(...)["bash_mentions"]["write_escapes"]` sums it over the stages. Labels are the existing `write_programs` labels plus `redirect` (a read-only program with an output redirection).
- `compute_facts(...)["guard"]` is `{"count": int, "kinds": {kind: int}}` with the kinds `raw-entry-changed`, `raw-entry-unexpected`, `snapshot-changed`, `snapshot-unexpected`, `hooklog-rewritten`. A clean run is `{"count": 0, "kinds": {}}`.
- New breach id `pc_checks.BREACH_RECORD = "run-record-changes"`; printed line: `isolation or git breach: changes to the run's own record files: N`. Write escapes are folded into the existing `writes-outside-approved-roots` count, so the line text for them is unchanged.
- `compute_facts` now raises `CheckError` for a missing `raw/setup.git.json`, a missing git state file of a stage with a record, and a missing or malformed guard file; a run root made before this plan therefore cannot be refiled (FA-8).
- When the project's git folder differs from the setup digest, a snapshot's `status.txt` holds the one line in `pc_row1.STATUS_NOT_RUN`, and the git state reads `not-read` for head, branch and refs (`pc_checks.GIT_NOT_READ`); the existing state-change rule counts that as git mutations.
- `memory_probe` returns only `absent` or `present` now (the `unknown` value is gone); `pc_evidence` renders `facts["memory_probe"]` as text and needs no change for that.

## Findings recorded for the record

- Task 1 red step: the touch operation made the planted clean filter run on the local git (Apple Git 2.50.1) with no fallback. Both controls (plain `git status` under the harness git environment) created their marker, and both end-to-end plants created theirs before the fix, so the plants were real.
- Conservative cases seen in practice: `python3 -c` that only reads an outside path is counted, `find` with `-exec` aimed at an outside folder is counted, a relative word with a dot-dot segment inside an `--expression=` value is counted. No false positive was found among the twelve Bash commands of the filed baseline traces (replayed read-only through the new rule in a scratch script, not committed).
- Not resolved by design (backstop truths of the plan): code that builds its target at run time, variable expansions other than HOME, and a working directory kept between separate Bash calls; the pinned allowlist, the snapshot diff and the Write and Edit trace are the other nets. An append of a well-formed line to the hook log by a Bash program cannot be told from the hook's own append; the guard proves earlier lines were not rewritten.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The stage guard is written after the stage record, not before it**
- **Found during:** Task 3 (red step design of the `record` tamper case)
- **Issue:** The plan placed `capture_guard` in `run_stage` right after `capture_boundary_state`, before the stage record is written. A record the model replaces during the next stage would then be seen for the first time, already replaced, by the next guard, so the plan's own test 5 case `record` (replacing `raw/s1.record.json` in s2) could not be detected.
- **Fix:** `run_stage` calls `capture_guard` as its last step, after the record write. The model is not running between the two, so nothing is lost; the window name set in `guard_violations` also accepts the previous stage's record and the current stage's record, which keeps the plan's listed names valid.
- **Files modified:** tests/harness/pc_row1.py, tests/harness/pc_checks.py
- **Commit:** 679b758

**2. [Rule 3 - Blocking] Two direct `run_stage` tests needed the setup guard**
- **Found during:** Task 3 green step
- **Issue:** `test_row1_seed.py` calls `run_stage` on a bare seeded run root, which has no setup guard to compare against.
- **Fix:** a `guard_setup` helper on the test's `Seeded` class writes the setup guard the way `run_row` does.
- **Files modified:** tests/harness/test_row1_seed.py
- **Commit:** 679b758

**3. [Rule 2 - Scope refinement] env -C is scoped to its own part, and env -S is read**
- **Found during:** Task 2 implementation
- **Issue:** The plan says an escaping `env -C` directory sets the same flag as `cd`, which would also taint later parts of the command although `env -C` only moves its own command. Separately, `env -S 'mkdir x'` hid the program from the rule.
- **Fix:** the env directory change makes only its own part escaping; the `-S` string is split and its words are read as the command.
- **Files modified:** tests/harness/pc_checks.py
- **Commit:** 8b4a1cf

**4. [Cosmetic] A formatting slip in the first commit of pc_testutil.py**
- The constant `_PLANT_CORE` was committed as `_PLANT_CORE ="..."` (missing space); corrected in the Task 3 test commit.

Otherwise the plan was executed as written. Deferred and untouched as planned: WR-04, WR-06, IN-02 to IN-10, the README (plan 03-08).

## Gates run at the end

| Gate | Result |
|---|---|
| `tests/harness/selftest` | OK, "0 model calls", 1167 tests, 3 skipped |
| `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | OK on 3.9.6, 1167 tests |
| leak gate over `tests/harness` | 71 files, 0 findings |
| gitleaks over `tests/harness` | exit 0 |
| frozen paths (`SKILL.md`, `references`, `tests/fixtures`, publication evidence) since 56e155c | empty |
| `tests/evidence` since a61283a | empty (the filed rerun folder is untouched) |
| files changed outside `.planning` since a61283a | exactly the six files in `files_modified` |
| `pc_matrix.py --list` | row1-wrong-binding implemented |
| `scripts/test-hooks.sh` | 29 PASS lines |
| commit messages | no attribution trailer; subjects alternate `test(03-07)` and `feat(03-07)` |

## Known Stubs

None.

## Threat Flags

None. The new surfaces (the guard files, the pin) are all inside the run root and read-only except the exclusive guard write.

## Self-Check: PASSED

- The six modified files exist and are committed; commits 2f9853c, 0bdb2bc, 3595fd7, 8b4a1cf, 7d6f03c and 679b758 are ancestors of HEAD.
