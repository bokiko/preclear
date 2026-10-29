---
phase: 03-walking-skeleton-row-1
plan: 09
subsystem: testing
tags: [harn-09, evid-04, harn-05, refile, chain-rule, git-pin, nested-repository, usage-consistency, gap-closure, zero-token]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "the pin, GIT_HARDENING, gitdir_digest and the git mutation rule of plans 03-07 and 03-08; _unfileable, the deny entries and Harn09ReproofTests of plan 03-08"
provides:
  - "file_row, and so the live path and --refile alike, files a run only when its stage records are exactly the chain the registry defines for row 1 (second-pass CR-01)"
  - "pinned_gitdir(raw_dir, setup) takes the boundary as a required argument; a missing or malformed pin file after setup is a CheckError and starts no git process (WR-03)"
  - "nested_git_present: the harness runs no git command in a project that holds an entry named .git below the top level; the state reads not-read and counts as a git mutation (WR-03)"
  - "cumulative_consistent reads unknown when the call's own cost was derived from the totals (WR-04)"
  - "HARN-09 git half re-proved at zero tokens through the driver: a clean control, nine seeded failures and the removed pin file"
affects: [03-10, 03-verification, REQUIREMENTS.md HARN-09 (orchestrator)]

status: complete
actuals:
  tokens: 16800
  tasks: 2
  commits: 4
plan_head_before: e233020fe6b3f0c984c292b584a220d3a7801e82
plan_head_after: 2959732b36eb261546deef95ec6d860801c26c27

tech-stack:
  added: []
  patterns:
    - "A completeness rule shared by the live path and the refile path through one function (_unfileable then _chain_incomplete), with the expected stage names read from the registry entry run_row walks"
    - "A safety input made a required argument, so no caller can reach the unsafe path by omission"
    - "A control in the test that proves a planted command runs on plain git before asserting the harness never runs it"

key-files:
  created: []
  modified:
    - tests/harness/pc_evidence.py
    - tests/harness/pc_matrix.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_manifest.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_spend.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_evidence.py
    - tests/harness/test_checks.py
    - tests/harness/test_stages.py
    - tests/harness/test_row1_seed.py
    - tests/harness/README.md

key-decisions:
  - "The chain rule takes its stage names from the registry entry, requires the third stage exactly when the chain record's marker is found, and returns a new fixed line (a stage did not run) after the per-stage cleanliness rule, so an unclean stage still reports the not-clean line"
  - "A CheckError from a missing pin file propagates out of run_row and the driver prints the generic stopped line with exit 11 (FA-3); the first-review WR-04 stays deferred"
  - "The nested repository is a git mutation by the existing rule: git_state returns the not-read state, which differs from the setup state; no new breach id. At setup it is a CheckError"
  - "The scripted claude's default results for s1 and s3 now carry the per-call cost block (delta), so the default run still reads yes three times under the new rule"

metrics:
  duration: "about 2 hours"
  completed: 2026-10-29
---

# Phase 3 Plan 09: Refile Chain Rule, Required Git Pin, Nested Repository Refusal And The Unknown Consistency Value Summary

**A run that stopped early can no longer be filed or refiled, a removed pin file refuses instead of unpinning the harness's git calls, the harness runs no git command in a project that holds a nested repository, and the cumulative-consistent line reads unknown unless two independent numbers were compared.**

## What was built

**Task 1 (tracer): the chain rule (second-pass CR-01, EVID-04, D-05).** `pc_evidence._unfileable` keeps its order (no stages, then each stage's prompt, stream and cleanliness) and then calls `_chain_incomplete`. That function requires the chain record to be a mapping whose marker is `MARKER_FOUND` or `MARKER_NONE`, and the stage records present to be, in order, the stage names of row 1's registry entry (the list `run_row` walks): s1 and s2, plus s3 exactly when the marker is found. Anything else returns the new fixed line `MESSAGE_STAGE_MISSING` (a stage did not run, nothing is filed), exit 11, nothing created. Docstrings in `pc_matrix.py` and the README no longer call a run folder "finished": the run record is all that makes it usable, and the filing judges the chain.

**Task 2: the pin, the nested repository, the unknown value (WR-03, WR-04).**
- `pc_checks.pinned_gitdir(raw_dir, setup)`: setup true returns None; setup false requires `raw/setup.git.json` and raises `CheckError` when it is missing or malformed. `take_snapshot` gained a `setup=False` keyword (looked up first, so a refusal leaves no partial snapshot folder) and `run_row` passes `setup=True` for the setup snapshot. `capture_boundary_state` derives the flag from the name.
- `pc_manifest.nested_git_present` walks the project once without following links, skips the top-level `.git` entry whatever its kind, returns true at the first `.git` entry below it and fails closed on a walk error. `NestedRepository` (a `GitDirChanged`) is raised by `capture_git_status` before any process starts and before the pin comparison. `git_state` returns the not-read state for it, `take_snapshot` writes the fixed `STATUS_NOT_RUN_NESTED` line, and `capture_boundary_state` refuses a nested repository at setup.
- `pc_spend.has_call_block` is the pure test `call_cost` already made; `call_cost` now calls it. `_consistent` takes the flag as a required fourth argument and returns unknown without it; `run_stage` passes `has_call_block(result_event)` (false with no result event).

## Test counts

Before: 1190 (selftest, OK, skipped 3). After: 1218 (selftest and system Python 3.9.6 discovery, both OK, skipped 3). The 28 new tests: 8 in test_evidence.py for Task 1 (7 RefileChainTests and 1 README case); 12 in test_checks.py (5 PinRequiredTests, 7 NestedRepositoryTests); 5 ConsistencyUnknownTests in test_stages.py; 3 more in test_evidence.py for Task 2 (the unknown rendering in UsageConsistencyTests, the removed pin file through the driver in Harn09ReproofTests, a README case). The nine-case seeded failure test grew inside one existing test, and the changed CostTests case is not new.

## Red steps

**Task 1** (commit bc17be6): 4 failures and 1 error, all on the missing behaviour: s1 only filed 57 files (exit 0), no s3 filed 62, s3 with marker none filed 67, no chain record filed 67, and the pure rule errored on the missing `MESSAGE_STAGE_MISSING` attribute. The s2-missing case already refused before the fix (the run record guard).

Which fixed line fires after the fix, per stopped shape:

| Shape | Exit | Line that fired |
|---|---|---|
| s1 only | 11 | stage line (a stage did not run) |
| s1 and s2, marker found, no s3 | 11 | stage line |
| s3 present, marker none | 11 | stage line |
| chain record absent | 11 | stage line |
| chain record holds another marker | 11 | stage line |
| s2 record missing, s1 and s3 present | 11 | breach line from the run record guard ("changes to the run's own record files"), before the chain rule is reached |

**Task 2** (commit a2602e3): 5 failures and 6 errors in test_checks.py (pinned_gitdir took one argument; `take_snapshot` had no `setup` keyword; `nested_git_present` and `NestedRepository` did not exist; a process was started with the pin file moved aside and with a nested repository at setup), 2 errors and 3 failures in test_stages.py (no `has_call_block`, `_consistent` took three arguments, the no-block case read yes, the changed CostTests case still got yes), 3 failures in test_evidence.py (unknown rendering, README phrases, the nested plant), 2 errors in test_row1_seed.py (the `setup` keyword).

**The nested plant created its marker before the fix, with the planned recipe and no change to it.** The direct control (the harness's own status command, run without the walk, against a nested repository holding a committed file, a gitlink at its real commit, a clean filter in its own configuration, an attributes file and a new modification time) created the marker. The end-to-end seed (`seed_nested_repo_plant`, a gitlink with an object name built at run time that matches no commit) also created `planted-nested` before the fix (`True is not false: the planted command never ran`), and after the fix the row ends with exit 11, `git mutations: N` with N at least 1, the not-read text in `raw/s1.git.json` and the fixed nested line in the snapshot. No same-size rewrite was needed. The top-level `gitdir_digest` is unchanged by the plant, which a test asserts.

## Tests changed to new truths

- `test_pinned_gitdir_reads_the_setup_state_file` (test_checks.py): now the two-argument contract; a missing file with setup true gives None and with setup false a CheckError.
- `CostTests.test_without_the_since_last_result_mapping_the_delta_is_the_difference_of_totals` (test_stages.py): expects `unknown` instead of `yes`, because the delta came from the totals.
- `Seeded.guard_setup` (test_row1_seed.py): also writes the setup git state through `capture_boundary_state`, so the three direct `run_stage` calls run under the required pin. The two setup-named snapshot tests pass `setup=True`; the symlink snapshot test (a later boundary on a bare run root) calls `guard_setup` first.
- `Harn09ReproofTests` seeded count: eight to nine (the nested clean filter, marker `planted-nested`), plus one separate case for the removed pin file.
- `pc_testutil.default_row1_stages`: the s1 and s3 results now carry `delta` equal to their totals, so every default result has the per-call block. Without this the default run would read unknown for s1 and s3 under the new rule. This is test scaffolding, not a loosened assertion.

## What a future filed usage.txt shows differently

`cumulative-consistent` reads `unknown` (and no warning line follows) for any stage whose result event lacked `model_usage_since_last_result` as a non-empty mapping, for example `cumulative-consistent s2: unknown`. A real run whose stream carries the block still shows `yes`. The stage lines, row total and run total are unchanged.

## Deviations from Plan

None - plan executed as written. Two notes that are not deviations: the s2-missing refile is refused by the run record guard before the chain rule, as FA-2 predicted, and the removed-pin driver case ends with exit 11 and the generic stopped line (FA-3). The removed-pin driver test also passes before the fix because the run record guard catches the removed file; the direct test that `run_row` raises `CheckError` is the one that distinguishes the behaviours.

## Verification gates (final state, HEAD 2959732)

- `tests/harness/selftest`: banner "0 model calls", `Ran 1218 tests`, OK (skipped=3), exit 0.
- `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` (Python 3.9.6): `Ran 1218 tests`, OK.
- Leak gate over `tests/harness`: 71 files scanned, 0 findings. gitleaks over `tests/harness`: exit 0.
- `git diff --name-only 56e155c -- SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20`: empty. `git diff --name-only e233020 HEAD -- tests/evidence`: empty. SKILL.md is 11994 bytes.
- The read-only comparer over the two evidence trees: exit 0, `old unchanged: yes`, `new unchanged: yes`.
- `pc_matrix.py --list`: exit 0, row1-wrong-binding implemented. `scripts/test-hooks.sh`: 29 PASS, 0 FAIL.
- No commit message carries an attribution trailer; the four commits alternate `test(03-09)` and `feat(03-09)`.

## Facts plan 03-10 needs

- `Harn09ReproofTests` now holds the clean control, the nine seeded failures inside `test_each_seeded_failure_ends_with_11_files_nothing_and_leaves_no_marker` (the count assertion reads nine) and `test_a_removed_pin_file_ends_with_11_files_nothing_and_starts_no_git_command`. Plan 03-10 adds the env-wrapped shell write as the tenth.
- The suite count is 1218 (the next plan starts from there).
- `pinned_gitdir(raw_dir, setup)` is the only signature; `take_snapshot(..., setup=False)`; `_consistent` has four required arguments.
- The scripted claude has a `remove` op (a file of the test's own run root only); `seed_pin_removed` and `seed_nested_repo_plant` exist in `pc_testutil.py`.
- README passages to extend in plan 03-10 sit in the Git read-only bullet of "What the mechanical checks measure" and the refile paragraph of "What a run files".

## Known Stubs

None.

## Threat Flags

None. The new code only reads (a directory walk, state files) and writes through `pc_runroot.write_exclusive`; the one deletion is the scripted claude's `remove` op inside `pc_testutil.py`.

## Self-Check: PASSED

- Files modified exist: all twelve listed in `key-files`.
- Commits exist: bc17be6, 0059c69, a2602e3, 2959732 (all ancestors of HEAD).
