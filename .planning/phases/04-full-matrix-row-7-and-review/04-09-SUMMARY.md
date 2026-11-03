---
phase: 04-full-matrix-row-7-and-review
plan: 09
subsystem: testing
tags: [harness, git-rows, row8a, row8b, row8c, row9, worktree, no-git-state, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-04 plain rows and seed_plain_row, 04-05 boundary list and hooks, 04-06 and 04-07 row 7 chain and review, 04-08 wave A
provides:
  - rows 8a (no repository), 8b (detached HEAD), 8c (unborn branch) and 9 (linked worktree) registered as implemented, three stages each, PROFILE_GIT (the 33-rule baseline alone), memory pinned, resume-line chain
  - pc_rowseeds.seed_git_row(shape, ...) with shapes commit, detached, unborn, none, worktree; seed_row8a, seed_row8b, seed_row8c, seed_row9
  - pc_manifest.NO_GIT_DIGEST, NO_GIT_STATUS_LINE, gitdir_digest answering for no .git and for a worktree .git file, worktree_git_folders, GitEntryUnreadable
  - pc_checks.git_state returning the fixed n/a state for a project with no .git (no process started)
  - pc_row1._excluded leaving out main-checkout/.git; pc_row1.STATUS_NO_GIT
affects: [04-10, 04-12, 04-13, 04-15, 04-16, 04-18, 04-19, 04-21]

# Actuals (#2632): chars/4 over the realized diff of tests/harness against the plan base commit
actuals:
  tokens: 27540
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 3f7f2a1a29fc9764716c6cf18acde5d0714b347e
plan_head_after: d0defcbe70a4ac0aeae46ee9681a2575a3b5fca6

tech-stack:
  added: []
  patterns:
    - "a git-shaped row is a plain row whose seed names a git shape word: seed_git_row passes it to seed_plain_row, which builds the project (and main-checkout for the worktree shape) inside the run root"
    - "the pinned git digest answers for four kinds of project: a .git folder (index entries left out), no .git at all (fixed marker digest), a linked worktree (pointer plus own and common git folders, index entries left out) and, as an error, anything else"
    - "a pinned capture treats a .git entry it cannot read as a difference from setup (GitDirChanged), so a planted or rewritten entry ends the row as a filed breach instead of an exception"

key-files:
  created:
    - tests/harness/test_rows_git.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_manifest.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_row1.py
    - tests/harness/test_manifest.py
    - tests/harness/test_matrix_cli.py
    - tests/harness/README.md

key-decisions:
  - "The no-git digest is the sha256 of a fixed marker text; the no-git state is head and branch n/a, the digest of empty text as refs_digest, staged 0; capture_git_status returns an empty raw result and the fixed line NO_GIT_STATUS_LINE without starting git, pinned or not"
  - "The worktree digest frames three parts (the pointer bytes, the worktree git folder manifest, the common git folder manifest) and leaves out only real index files: index and index.lock at the top of either folder and worktrees/<name>/index and index.lock in the common folder; a reference or file that merely shares the name deeper in the tree is kept (a branch called index is a change)"
  - "A pointer must lead to a folder directly under main-checkout/.git/worktrees, the worktree's commondir must lead back to main-checkout/.git, and neither folder nor the pointer may be a link; any other shape raises GitEntryUnreadable (a ManifestError), never a guess"
  - "A project that is itself a link or not a folder makes gitdir_digest raise a plain ManifestError, so a swapped project folder is never followed (the row 7 swapped-folder test keeps its exception behaviour)"
  - "The main-checkout exclusion is exactly main-checkout/.git and its contents; .gitignore, .github and a nested .git below the top level of main-checkout stay in the manifest"

patterns-established:
  - "tests that prove no git process starts put a tripwire git first on the path and filter its log to calls that name the run root (the engine's own calls aimed at the rig repository are legitimate)"
  - "git-row chain tests loop over GIT_ROWS in test_rows_git.py; plan 04-10 adds row 10 to the same file"

requirements-completed: [RERUN-02]

coverage:
  - id: D1
    description: "Each of rows 8a, 8b, 8c and 9 dry-runs as 3 stages, 2 sessions with turns and caps 15/0.30, 60/1.30, 15/0.40, worst case 2.00 USD, allowlist 33 rules, exit 0, no process and no harness home; --list marks all four implemented"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#GitRegistryTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each seed is byte-tied to its committed row (project CLAUDE.md equals fixture-CLAUDE.md, sha256 ed03447e..., the plan equals data/plain-plan.md) and has the committed git shape: 8b two commits and a detached HEAD at the first with no NOTES.md in the work tree, 8c a repository on main with no commit and everything untracked, 8a no .git anywhere, 9 main-checkout with the files committed on main and project a linked worktree on feature/widget-export whose .git is a file"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#GitShapeSeedTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_git.py#ShapeSeedTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A project with no .git has the fixed n/a state and the marker digest, no git process is started for the state or the snapshot (tripwire git silent), and a .git folder, a garbage .git file or a nested .git planted later changes the digest, starts no git and is counted by the mutation rule or refused as a nested repository"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#NoGitStateTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_git.py#NoGitChainTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "A linked worktree digests the pointer, its git folder and the common git folder without index entries: a refreshing git status leaves it unchanged, a changed common or worktree configuration, a new reference, a new commit or a re-spelled pointer changes it, git is not started on a change and the change is counted; a pointer outside main-checkout, a malformed or linked .git and a wrong commondir are refused"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#WorktreeStateTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "The run-root manifest leaves out main-checkout/.git and keeps every other main-checkout entry: the main checkout's two listed hashes are identical at setup and after s1, s2 and s3 and equal the committed digests, a scripted new file or edit in main-checkout ends the row with 11 and a STOPPED folder, a git status that refreshes an index in the worktree is not a breach, a planted common configuration runs no planted command (the digest catches it) and a rewritten pointer ends the row as a filed breach"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#MainCheckoutTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_git.py#WorktreeChainTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "A scripted s3 of each row makes zero Write or Edit calls and the filed snapshots of s2 and s3 hash identically; each row README ends with Reviewer verdict: PENDING and holds no verdict word, no path and the registry Setup paragraph (row 8a's paragraph names its difference from the committed run, row 9's names the content-preservation scope)"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#GitRowChainTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "How the real model reports a detached, unborn, linked or absent repository, and whether the real binary's own git calls disturb the pinned digests, is unobserved until wave B; the scripted claude proves the pipeline and the real run records the facts"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan: only a real stream shows what the pinned build does inside these four shapes"

duration: about 2 h 30 min (estimate; the start time was not recorded), of which about 36 min were three full-suite runs (one failed and was fixed)
completed: 2026-11-03
status: complete
---

# Phase 4 Plan 9: Git-shaped rows 8a, 8b, 8c and 9 Summary

**Rows 8a (no repository), 8b (detached HEAD), 8c (unborn branch) and 9 (linked worktree beside the main checkout) now run three stages through the same engine as every other row: byte-tied seeds with the committed git shapes, a fixed pinned git state for a project with no .git, a pinned pointer-aware state for a linked worktree, and a run-root manifest that keeps the main checkout's content under watch while leaving its git metadata out.**

## Performance

- **Duration:** about 2 h 30 min (estimate; the start time was not recorded)
- **Completed:** 2026-11-03
- **Tasks:** 3
- **Files modified:** 9 (1 created)

## Accomplishments

- `pc_rows`: `PROFILE_GIT`, `ROW8A`, `ROW8B`, `ROW8C`, `ROW9` and four registry entries (the committed three stages with caps 0.30, 1.30 and 0.40, the resume-line chain, the baseline allowlist alone, memory pinned, no hook, no probe) with harness-worded Setup paragraphs; 8a's states its difference from the committed run (no enclosing repository), 9's states the content-preservation scope.
- `pc_rowseeds`: `seed_git_row(shape, ...)` over `seed_plain_row(..., shape=)`; shapes commit, detached (two commits, the second adds `NOTES.md`, then `checkout --detach HEAD~1`), unborn, none and worktree (`main-checkout` committed on main, `project` made by `git worktree add -b feature/widget-export` into the empty project folder); `seed_row8a/8b/8c/9`. Spike identity only; every repository lives inside the run root.
- `pc_manifest`: `NO_GIT_DIGEST`, `NO_GIT_STATUS_LINE`, `has_git_entry`, `worktree_git_folders`, `GitEntryUnreadable`, and a `gitdir_digest` that answers for no `.git`, a `.git` folder (unchanged) and a worktree pointer file; `capture_git_status` returns the fixed line for no `.git` without a process and turns an unreadable entry into `GitDirChanged` when pinned.
- `pc_checks.git_state`: the fixed `NO_GIT_STATE` (head and branch n/a, empty refs digest, marker digest, staged 0) for a project with no `.git`.
- `pc_row1`: `_excluded` leaves out `main-checkout/.git` and everything under it; `STATUS_NO_GIT`.
- `test_rows_git.py` (82 tests): `GitShapeSeedTests`, `GitRegistryTests`, `NoGitStateTests`, `GitShapeStateTests`, `GitRowChainTests`, `NoGitChainTests`, `ShapeSeedTests`, `WorktreeStateTests`, `MainCheckoutTests`, `WorktreeChainTests`.
- README: Layout line and a three-paragraph section under "What a row run does" on the git shapes, the two git states and the exclusion with its scope.
- Suite: 1795 -> 1878 tests (3 skipped as before), green through `tests/harness/selftest` with the `0 model calls` banner; `test_rows_git.py` also green on the 3.9.6 system interpreter.

Suite count: 1878

## Task Commits

1. **Task 1 (tracer): row 8b runs three stages through the engine** - `2970b60` (feat)
2. **Task 2: rows 8c and 8a and a defined git state for a project with no .git** - `fe43a54` (feat)
3. **Task 3: row 9, the worktree git state and the main-checkout exclusion** - `d0defcb` (feat)

**Plan metadata:** the SUMMARY commit that follows (docs).

_Tracer gate: the tracer `<verify>` (test_rows_git, the tripwire dry run of row 8b, and test_rows_plain, test_row7, test_boundaries) was run and passed before the Task 1 commit; no `blocking-human` gate was set, and the scripted chain verified end to end before rows 8c, 8a and 9 were added._

## Files Created/Modified

- `tests/harness/pc_rows.py` - profile word, row constants, four entries, setup texts
- `tests/harness/pc_rowseeds.py` - shape constants, `_build_plain_project`, `seed_git_row`, four seeds
- `tests/harness/pc_manifest.py` - no-git and worktree digests, the unreadable-entry class, the no-git status
- `tests/harness/pc_checks.py` - the fixed no-git state
- `tests/harness/pc_row1.py` - main-checkout exclusion, `STATUS_NO_GIT`
- `tests/harness/test_rows_git.py` - new
- `tests/harness/test_manifest.py`, `tests/harness/test_matrix_cli.py` - one old-meaning case each moved (see deviations)
- `tests/harness/README.md` - Layout line and the git-shapes section

## Decisions Made

See `key-decisions` above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two tests outside `files_modified` encoded the old meaning and were moved**
- **Found during:** Task 2 (test_manifest) and the first full suite (test_matrix_cli)
- **Issue:** `test_manifest.test_a_failing_status_raises` used a folder with no `.git` at all as "not a repository", which now has its own defined answer; `test_matrix_cli`'s odd-stage-key test listed `row9-s1` as an unknown stage key because row 9 was unimplemented, and it is now a valid key.
- **Fix:** the first test uses a folder with an empty `.git` folder (git status still fails) and a new test asserts the no-git answer; the second uses `row99-s1` (a row that can never exist). No test was deleted or weakened.
- **Files modified:** tests/harness/test_manifest.py, tests/harness/test_matrix_cli.py
- **Commits:** fe43a54, d0defcb

**2. [Rule 2 - Missing critical functionality] An unreadable `.git` entry must be a filed breach, not an exception, and a swapped project folder must still be refused**
- **Found during:** Task 3 (a rewritten worktree pointer crashed `take_snapshot` with a raw ManifestError) and the first full suite (the row 7 swapped-folder test)
- **Issue:** a pinned `capture_git_status` called `gitdir_digest`, which raised ManifestError for a pointer the harness cannot read; and with the new "missing `.git` is the no-git digest" rule a project folder replaced by a link to a folder without `.git` would have read as a graceful no-git change instead of the refused swap the row 7 hook test proves.
- **Fix:** `GitEntryUnreadable` (a ManifestError) names the unreadable-entry cases and a pinned capture turns it into `GitDirChanged` (git not started, the fixed not-run line, then the boundary state check ends the row with 11 and a STOPPED label); `gitdir_digest` raises a plain ManifestError when the project folder is itself a link or not a folder, which keeps the row 7 swapped-folder behaviour (an exception, nothing filed) exactly as before.
- **Files modified:** tests/harness/pc_manifest.py
- **Commit:** d0defcb

**3. [Rule 1 - Refinement] Index entries are left out by name and place, not "at any depth"**
- **Issue:** the plan says every entry named `index` or `index.lock` at any depth is left out of the worktree digest; a reference file named `index` (a branch called `index` under `refs/heads`) would then hide a real ref change.
- **Fix:** only real index files are left out: `index` and `index.lock` at the top of the worktree git folder and of the common folder, and `worktrees/<name>/index` and `index.lock` in the common folder. A test proves a refreshed index and an `index.lock` change nothing and a branch named `index` does.
- **Commit:** d0defcb

**4. [Rule 3 - Blocking] The README Layout line came with Task 1**
- **Issue:** `test_readme` requires every new file in the Layout list in the commit that adds it (the same as plan 04-04, deviation 4).
- **Fix:** the Layout line is in the Task 1 commit, the git-shapes paragraphs in the Task 3 commit.

**5. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- **Issue:** the plan requires a green suite at every commit, so a committed failing `test(...)` commit is not possible (same as plans 04-01 to 04-08).
- **Fix:** tests were written with the code and run before each commit. See TDD Gate Compliance.

**6. [Plan defect, none to record]** the plan's dry-run clause `worst case 2.00 USD` holds here: all four rows have three stages (0.30 + 1.30 + 0.40 = 2.00); the earlier two-stage defect does not apply.

---

**Total deviations:** 5 (2 blocking test moves and process notes, 1 missing critical, 1 refinement, 1 TDD note). **Impact:** deviation 2 changes what a model-planted `.git` file or rewritten pointer does (a filed breach with exit 11, a STOPPED folder) and adds a project-is-a-link refusal to `gitdir_digest`; no earlier behaviour changed for a project with a `.git` folder.

## TDD Gate Compliance

Plan type is `execute` (not `type: tdd`), so the gate commands do not run; the tasks carry `tdd="true"`. The failing state was not committed because the plan requires a green suite at every commit.

## Authentication Gates

None. The plan is model-free: no real `claude` was started and nothing was spent.

## Issues Encountered

- The first full suite (1876 tests) failed twice, both because of this plan's change (deviations 1 and 2). After the fixes the whole suite (the `selftest` run, 727 s) is green: 1878 tests, 3 skipped.
- The engine's own preflight calls git against the rig repository, so tripwire-git tests filter the log to calls that name the run root.
- The sandbox did not reject any command in this plan; no hook was bypassed.

## Known Stubs

None.

## Threat Flags

None. The new surface is the harness reading a worktree pointer and two git folders inside the run root; it is in the plan's threat model (T-04-39 to T-04-42). The pointer is followed only into `main-checkout/.git/worktrees/<name>` with no link in the path, a planted `.git` or pointer starts no git process, and the filed git facts are heads, branches, digests and counts only.

## User Setup Required

None - no external service configuration required.

## Notes for plan 04-10 (row 10 and git-call correlation)

- `test_rows_git.py` is shared with plan 04-10: add row 10 to its own seed class and tests; the helpers `git_here`, `git_out`, `make_git_tripwire`, `calls_aimed_at`, `real_git_path`, `dry_run_row` and `SeededGit` are there. `GIT_ROWS` and `SHAPE_WORDS` list the four rows built here; row 10 is a plain-profile or git-profile row of its own and needs its own shape word if it prints a resume line.
- `seed_git_row(shape, ...)` takes a shape word from `rowseeds.GIT_SHAPES`; a large-status project (row 10) is one more shape (or a post-seed step) built in `_build_plain_project`; the commit shape already makes one commit on main.
- `PROFILE_GIT` is registered (`pc_rows.PROFILE_GIT`, equal to `pc_flags.PROFILE_GIT`) and the entries of 8a to 9 use it; a row that needs chmod or touch keeps `PROFILE_PLAIN` with its extra rules.
- Git calls the harness itself starts: only `capture_git_status` (two `status` calls) and `git_state` (`rev-parse HEAD`, `symbolic-ref -q HEAD`, `for-each-ref`, plus a status), all through `GIT_HARDENING`, only after the nested-repository check and the pin comparison. A no-git project starts none. For correlation of the model's own git calls with these digests, `pc_checks.git_mutations` reads the executed Bash forms from the stream; a model `git status` in a worktree refreshes `worktrees/<name>/index`, which the digest leaves out.
- Real-build behaviour is unobserved: whether the pinned build's own git use inside the worktree or the detached and unborn shapes writes anything the digest sees (for example under the common git folder), and what the model reports for each shape. If a real run shows a digest change from a read-only git call, the fix is in `_is_index_entry` (leave that file out), never in the pin.
- The `--all` worst cases now sum to 2.00 + 1.60 x 4 + 2.00 + 2.00 x 4 = 18.40 USD for the twelve implemented rows (rows 1, 4a, 5a, 5b, 6, 7, 8a, 8b, 8c, 9), below the 25.00 ceiling; rows 10, 11 and 12 will add to it.
- Row 8a's filed `snap-*/status.txt` holds the single no-git line and the Git section's states read `head n/a, branch n/a`; the committed 8a run held git facts from an enclosing repository, and the comparer lists that difference without judging it. If a stranger sets `PRECLEAR_RUNS_ROOT` inside another repository the model's own git commands would find that one; the harness's state capture still starts no git process for the project (flagged assumption FA-3).

## Self-Check: PASSED

- Created files exist: `tests/harness/test_rows_git.py`, this summary.
- Task commits are ancestors of HEAD: `2970b60`, `fe43a54`, `d0defcb`.
- `commits:` was measured from the persisted ledger (3 commits before this summary commit).
- Final gates: `tests/harness/selftest` 1878 tests OK (3 skipped) with the `0 model calls` banner (floor 1795); `scripts/test-hooks.sh` 29 PASS; `test_rows_git.py` green on the 3.9.6 system interpreter; leak gate over `tests/harness` 85 files, 0 findings; the secret scanner over `tests/harness` clean; frozen paths (`SKILL.md` 11994 bytes, `references`, `tests/fixtures`, `publication-2026-10-20`, the Phase 3 rerun folder) unchanged; nothing under `tests/evidence` changed against the plan base; no attribution trailer in any commit of the range; the change list against the plan base names only files under `tests/harness` plus this summary.

---
*Phase: 04-full-matrix-row-7-and-review*
*Completed: 2026-11-03*
