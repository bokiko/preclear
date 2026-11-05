---
phase: 04-full-matrix-row-7-and-review
plan: 12
subsystem: testing
tags: [harness, row11, git-wrapper, injector, path-prepend, exact-argv, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-10 git-calls analysis, parse_git_calls_log and the raw/gitwrap-digests.json shape; plan 04-09 git row seeds; plan 04-01 row-generic engine
provides:
  - tests/harness/git-wrapper, a bash 3.2 transparent logging git wrapper with an exact-argv n-th-match injector
  - row 11 (row11-concurrent-change) registered as implemented, three stages (15/0.30, 60/1.30, 15/0.40), PROFILE_GIT (33 rules), memory pinned, resume-line chain, analyses ("git-calls",), path_prepend (("s2", "ckpt/gitwrap"),)
  - pc_rows.RowSpec.path_prepend and pc_rows.ROW11; pc_row1._apply_path_prepend applied in run_stage
  - pc_rowseeds.seed_row11, install_git_wrapper, MATCH_ARGV_LINES, OTHER_NOTES_NAME/TEXT, extra_files parameter of seed_git_row and seed_plain_row
  - pc_testutil scripted op run_git (optionally silent) and the child's PATH in the scripted call record
  - tests/harness/test_git_wrapper.py (52 tests)
affects: [04-13, 04-14, 04-19, 04-21]

actuals:
  tokens: 45000
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 2a23cecc82b9eb223d3edab4c322fbac6930ac5d
plan_head_after: a70fb71eb52b2860012836ee4befce58353df35f

key-files:
  created:
    - tests/harness/git-wrapper
    - tests/harness/test_git_wrapper.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_review.py
    - tests/harness/test_bash_shims.py
    - tests/harness/README.md

key-decisions:
  - "Whole-argv equality against exact printf %q lines in match-argv; the rendering has no leading space, and a blank listed line never matches a no-argument call"
  - "The ordinal is the line number of the call's own unique token in matches.log (one append, then grep -n); mkdir fired.lock is the second guard, so exactly one racer injects"
  - "The inject-file is validated as a plain relative name (no leading slash, no dot-dot part), a regular non-link file whose physical folder lies inside the project; anything else injects nothing and writes no INJECTED line"
  - "INJECTED is written only after the append to the inject-file succeeded; every auxiliary step runs in a function with its streams sent to the null device, so no failure shows to the caller"
  - "Claude Code's own calls are simulated by a silent run_git op (no tool_use), because a model-issued git -c is counted as a config-command mutation by pc_checks.git_mutations"
  - "The real git path is taken with pc_row1._git_executable(os.environ) at seed time and lives only in ckpt/gitwrap/real-git inside the run root"

patterns-established:
  - "a per-stage environment change is declared in the registry (path_prepend) and applied in run_stage after build_env, resolved with realpath and confined to the run root"
  - "an auxiliary shim step is best effort: its function is called with all three streams redirected and its status ignored, and the real command's exit code is the shim's exit code"

requirements-completed: [HARN-11, RERUN-02]

duration: about 1 hour 10 minutes wall time including two full suite runs and one system-interpreter run
completed: 2026-11-05
status: complete
---

# Phase 4 Plan 12: Row 11 injector Summary

**Row 11 now runs three stages with a transparent logging git wrapper first on the PATH of the /preclear stage only; it fires one concurrent change into another task's notes file on the first model-issued status call whose whole argument list equals one of two exact lines, never on a `-c`-prefixed call and never on a harness call, with a race-free ordinal and an empty injection log in a session that never matches.**

## Accomplishments

- `tests/harness/git-wrapper` (bash 3.2, shellcheck clean): runs the real git named in `real-git` first with stdin, stdout, stderr and exit code untouched, then counts and injects, then writes one line `T=<utc> PID=<pid> EXIT=<code> ORD=<k or -> ARGV=<printf %q>` with a single write. Exit 70 and nothing run when `real-git` is missing.
- Injector: match by whole-argv equality with a line of `match-argv`; the ordinal is the call's own line number in `matches.log`; the match whose number equals `fire-on` takes `mkdir fired.lock` and appends the fixed line to the inject-file, then records `INJECTED ORD=<k>`. A session with no match leaves `matches.log`, `fired.lock` and `injection.log` absent.
- Row 11 registered (`ROW11`), implemented, `--list` shows 3 stages and 2 sessions; the dry run prints `3 stages, 2 sessions`, caps 0.30/1.30/0.40, `worst case 2.00 USD`, `allowlist 33 rules`, starts no process and creates no harness home.
- `seed_row11`: base commit holds `other_task_notes.md`; `ckpt/gitwrap` holds `git` (mode 755 copy of the shim), `real-git`, `match-argv` (the NUL form and the quoted-porcelain form), `fire-on` (1) and `inject-file`; `raw/gitwrap-digests.json` holds their sha256 (the shape plan 04-10 reads; the filed section reads `wrapper-files-equal-setup-digests: yes`).
- `pc_row1._apply_path_prepend`: s2 gets the wrapper folder first on its PATH; s1 and s3 keep the PATH build_env produced; the harness's own git calls keep the absolute path from the driver environment, so the wrapper log of a scripted chain holds exactly the scripted calls and none of the harness's.
- Tests: 52 in `test_git_wrapper.py` (GitWrapperTests 10, ExactArgvTests 5, OrdinalRaceTests 6, NoOpSessionTests 2, WrapperSafetyTests 7, Row11RegistryTests 4, PathPrependTests 3, Row11SeedTests 6, Row11ChainTests 9). Every complete `-c` line of the committed row 11 `git-calls.log` is replayed against the matcher and none matches; the committed model call (the quoted form) does.
- Suite: 1947 -> 1999 tests (3 skipped as before), green through `tests/harness/selftest` (banner `0 model calls`) and through `/usr/bin/python3 -I -B -m unittest discover`.

Suite count: 1999

## Task Commits

1. **Task 1 (tracer): row 11 runs with the git wrapper first on the PATH of s2 only** - `b606ddc` (feat)
2. **Task 2: the injector contract** - `065718b` (feat)
3. **Task 3: shim list and README** - `a70fb71` (feat)

_Tracer gate: the tracer `<verify>` (the Task 1 tests, the tripwire dry run of row 11, shellcheck and bash -n) ran and passed before the Task 1 commit; no `blocking-human` gate was set. The SUMMARY commit that follows is the fourth commit of the range; `commits:` above is measured before it._

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two tests outside `files_modified` encoded the old meaning and were moved, none deleted**
- `test_review.py`: the registry tests for the analyses of row 7 and row 10 asserted every other row has no analysis. Both now accept `("git-calls",)` for row 11. Commit b606ddc.

**2. [Rule 3 - Blocking] A scripted internal-style call must be silent**
- A scripted `git -c ...` announced as a Bash tool call was counted by `pc_checks.git_mutations` as a `config-command` mutation and stopped the chain (exit code for an isolation or git breach). Claude Code's own calls have no tool_use, so `run_git` takes `silent: true` and the chain test uses it. Commit b606ddc.

**3. [Rule 3 - Blocking] The README Layout lines came with Task 1**
- `test_readme` requires every new file in the Layout list in the commit that adds it (same as plans 04-04 and 04-09). The injector paragraph and the Requirements line are in the Task 3 commit.

**4. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- A failing test commit would break the green-suite rule; tests were written with the code and run before each commit.

**5. [Process] The commit guard refused `main`**
- This project runs `git.branching_strategy: none`, so the Step 0 guard refused every commit; per the dispatch the orchestrator made the three task commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.

**6. [Plan wording] The committed log has only a few complete internal lines**
- The committed `git-calls.log` is partly garbled (two writers interleaved in it). The replay test takes the complete CALL lines and the continuation lines that start with a `-c` option (at least 4, the test asserts it) rather than the 6 first guessed.

**Total deviations:** 6, none changing the behaviour of any earlier row.

## Known Stubs

None.

## Threat Flags

None. The new surface (a wrapper first on the PATH of one stage, writing one line into one file of the project) is the plan's threat model, T-04-53 to T-04-57. The shim holds no path, host, address or email (a test scans it), the real git path lives only in `ckpt/gitwrap/real-git` inside the run root and is not filed (a chain test checks no filed file holds it), and no allowlist rule was added (a test checks the 33-rule baseline names no wrapper).

## Notes for plan 04-13 (row 12) and 04-14 (paid wave C)

- **Row ids and cost:** wave C rows are `--row row11-concurrent-change` and `--row row12-frozen-handoff`. Row 11 is three stages, 2 sessions, worst case 2.00 USD, 33 rules. `--dry-run --all` now prints `total: 12 row(s), 32 stage(s), 20 session(s), worst case 22.40 USD` (eleven earlier rows at 20.40, which is 11 rows and not 13 as the carry-over text said, plus 2.00). Row 12 adds its own worst case; keep the sum under the 25.00 ceiling.
- **Row 12 and `STAGE_ORDER`:** nothing here touched `pc_evidence.STAGE_ORDER`; plan 04-13 widens it for four stages. A row that sets `path_prepend` entries for a stage name must name stages its own spec has.
- **What to read after the row 11 run:** the `Git wrapper calls` section of `mechanical-checks.md`; `git-calls-correlated.txt`, `git-calls.log`, `injection.log` and `wrapper-git.sh` in the row folder; the README line. `injection-log: absent` means the model never issued either listed argument list; that is a recorded fact, not a defect (FA-4). `wrapper-files-equal-setup-digests: no` means a model write changed the wrapper folder (it sits in an approved root, so it is not a boundary breach).
- **Unobserved until wave C:** which exact argv the real model issues for its first status call (the committed run fired on the quoted form `--no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none`), and whether the real binary's own calls look any different to a wrapper first on PATH. Wave B showed the real binary refuses an output redirect, so the NUL form with a redirect never runs; a bare NUL form still would and is listed.
- **Join caveat:** if the model issues the identical argument list twice, `join_ids` labels both calls ambiguous with both tool_use ids; that is plan 04-10's rule, not an error.
- **Driver:** no new flag. The wrapper only lights up for the /preclear stage, and the other stages run with the unchanged PATH.

## Self-Check: PASSED

- Created files exist: `tests/harness/git-wrapper`, `tests/harness/test_git_wrapper.py`, this summary.
- Task commits `b606ddc`, `065718b`, `a70fb71` are ancestors of HEAD (`git rev-list --count 2a23cec..HEAD` was 3 before this summary).
- `commits: 3` measured from the persisted ledger (base 2a23cec).
- Final gates: `tests/harness/selftest` 1999 tests OK (3 skipped) with the `0 model calls` banner (floor 1947); the system-interpreter unit suite 1999 tests OK; `scripts/test-hooks.sh` 29 PASS, 0 FAIL; leak gate over `tests/harness` 87 files, 0 findings; gitleaks clean; frozen paths against 56e155c unchanged and SKILL.md 11994 bytes; no attribution trailer in the range; nothing under `tests/evidence` changed in `2a23cec..HEAD`.
