---
phase: 04-full-matrix-row-7-and-review
plan: 11
subsystem: testing
tags: [harness, matrix, wave-b, rows-8a-8b-8c-9-10, git-shapes, status-form, attribution-run, paid-run]
requires:
  - phase: 04-10
    provides: row 10 and the status-form analysis, the git rows of 04-09, the wave pipeline and the review analyses of 04-07
provides:
  - tests/evidence/rerun-2026-11-05-claude-sonnet-5-5-wave-b with five filed row folders and README, digest table and usage table
  - measured cost of the five three-stage git-shaped rows on claude-sonnet-5-5 and Claude Code 2.1.310
  - the first real observations of the pinned git digests, the resume-line forms and the row 10 status form under the real binary
affects: [04-12, 04-14, 04-18, 04-20, 04-21]
tech-stack:
  added: []
  patterns: [one paid wave per go word, stage costs from the filed usage tables]
key-files:
  created:
    - tests/evidence/rerun-2026-11-05-claude-sonnet-5-5-wave-b/README.md
    - tests/evidence/rerun-2026-11-05-claude-sonnet-5-5-wave-b/digest-table.md
    - tests/evidence/rerun-2026-11-05-claude-sonnet-5-5-wave-b/usage-by-row.txt
  modified: []
key-decisions:
  - "Budget amount used: 3.50 USD, the plan's recommended figure; bokiko's word was `go` with no amount, so the orchestrator applied the recommendation he had in front of him; the wave settled at 1.43 USD"
  - "The evidence and this summary were committed on main by the orchestrator, not by the executor: the executor's commit guard refuses the default branch and the executor halted without committing, editing or bypassing anything"
metrics:
  duration: about 36 minutes of wall time for the wave and the verification
  completed: 2026-11-05
status: complete
actuals:
  tokens: 60000
  tasks: 3
  commits: 1
requirements-completed: []
plan_head_before: e55db62acc5ad665975cfe14c2e0b01701daf305
plan_head_after: 11e0317
---

# Phase 4 Plan 11: Wave B Summary

Wave B ran once on bokiko's word (`go`) and filed rows 8a, 8b, 8c, 9 and 10 as five filed row folders in `tests/evidence/rerun-2026-11-05-claude-sonnet-5-5-wave-b/`, for 1.43 USD against a projection of about 1.35 USD and a 3.50 USD budget; nothing stopped, nothing skipped, nothing is reviewed.

The folder is an attribution run, not the baseline. Every row README ends with `Reviewer verdict: PENDING`. No row is claimed accepted; the review is plan 04-21.

## The run

- Command: one `pc_matrix.py` invocation, `--campaign wave-b`, the 2.1.310 build, `--budget 3.50`, the five `--row` flags, no other flag. Run once. No `--authorize-retry`, no `--attempt`.
- Exit code: 0.
- Build banner `2.1.310 (Claude Code)` found next to the PATH build (the PATH build is 2.1.317), model claude-sonnet-5-5, preflight OK.
- Printed plan total before spend: 5 rows, 15 stages, 10 sessions, worst case 10.00 USD.
- Printed fixed lines, per row: `row row8a-non-git: filed, exit 0, spent 0.25 USD`; `row row8b-detached-head: filed, exit 0, spent 0.26 USD`; `row row8c-unborn-branch: filed, exit 0, spent 0.26 USD`; `row row9-linked-worktree: filed, exit 0, spent 0.27 USD`; `row row10-large-status: filed, exit 0, spent 0.42 USD`.
- Printed summary line: `summary: 5 row(s) selected, 5 filed, 0 stopped, 0 skipped, 0 refused, 0 not started`.
- Files filed per row: 57, 56, 56, 56 and 58; `close` added the three top-level files.
- The dated label carries 2026-11-05, the UTC date of the run (the rehearsal dry run two days earlier printed 2026-11-03).

## Measured cost (from `usage-by-row.txt`; USD kept as the usage files hold them)

| Row | State | Attempt | s1 turns / cost | s2 turns / cost | s3 turns / cost | Row total |
|---|---|---|---|---|---|---|
| row8a-non-git | filed | 1 | 4 / 0.0440391 | 16 / 0.1186342 | 10 / 0.0824424 | 0.2451157 |
| row8b-detached-head | filed | 1 | 4 / 0.0461112 | 17 / 0.1521936 | 6 / 0.0532835 | 0.2515883 |
| row8c-unborn-branch | filed | 1 | 5 / 0.0500394 | 15 / 0.1428374 | 7 / 0.0607904 | 0.2536672 |
| row9-linked-worktree | filed | 1 | 5 / 0.0497544 | 17 / 0.1552240 | 5 / 0.0598445 | 0.2648229 |
| row10-large-status | filed | 1 | 5 / 0.0547980 | 28 / 0.3109138 | 6 / 0.0535457 | 0.4192575 |

- Wave total: 1.4344516 USD from 5 cost values, 0 UNCONFIRMED. The projection (FA-8, from the one measured Phase 3 chain) was about 1.35 USD; the estimate at wave A's measured rate was about 1.2 USD. The budget was 3.50 USD, so the stop-before-row rule never triggered.
- Every one of the 15 stages ended with result subtype `success`. No cap, turn limit or timeout was hit. The largest stage was row 10 s2 at 28 of 60 turns and 0.31 of its 1.30 cap. Row 10 cost about 1.6 times each other row, mostly in s2.
- Spend ledger under the `wave-b-` scope: 15 launch lines, exactly one per stage, no stage launched twice, no authorization line.

## Measured answers to the checkpoint's questions (facts, not judgements)

1. Pinned digests of rows 8a and 9 under the real binary's own git calls: both rows were filed, not STOPPED, so no pin mismatch was raised. Row 8a's `## Git` section reads `head n/a, branch n/a, staged 0` in setup, s1, s2 and s3 with `mutations-total: 0`, `mutation-state-changes: 0`, `mutation-executed-forms: 0`. Row 9's reads the same head and `refs/heads/feature/widget-export` in all four states with the same zero counts. Every stage of every row reads `isolation-assertions-all-hold: yes`.
2. Resume-line forms the model printed (the part after the checkpoint path): absent repository (8a) `no-git @ n/a`; detached (8b) `detached @ fc8c6a2`; unborn (8c) `unborn @ n/a`; linked worktree (9) `feature/widget-export @ 4cc1a4a`; row 10 `main @ 5d6be30`. Row 8b's `## Git` section shows `branch UNCONFIRMED` and row 8c's shows `head UNCONFIRMED`.
3. The NUL status redirect on row 10: the model ran `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none > .preclear/widget-export/status.txt`; the binary refused it with a result beginning `Output redirection to '<run>/project/.preclear/widget-export/status.txt' needs approval. The path is inside the working directories for this session`. The model then wrote `status.txt` with the Write tool from a non-`-z` `git status --porcelain=v1` capture and said so in its final reply. Filed `## Row 10 status form` counts: `quoted-porcelain-parts-executed: 3`, `nul-git-parts-executed-with-redirection: 0`, `nul-git-calls-denied-with-redirection: 2`, `nul-git-parts-executed-without-redirection: 1`, `bash-parts-unparsed: 0`, `sidecar-status-txt: present`, `sidecar-status-txt-bytes: 6305`, `sidecar-status-txt-nul-bytes: 0`. Row 10 s2 had 4 permission-gate denials: the redirect refusal and "multiple operations ... requires approval" on piped or chained commands.
4. Executed `-z` commands without a redirect: 1 (a `git status -z | tr | wc -l` count).
5. Limit subtypes: none; all 15 stages ended `success`.

Other filed facts: the helper calls section reads attempted 0, executed 0, denied 0 in all stages of all rows. Row 10's checkpoint was 2793 of 4096 bytes with every section under its cap. The skill and adapter sha256 are identical across the five rows; the stub and wrapper digests read UNCONFIRMED in the digest table.

## Verification (all zero-token)

- Outcome folders: exactly one per selected entry; `README.md`, `digest-table.md` and `usage-by-row.txt` exist; every row README ends `Reviewer verdict: PENDING`.
- `pc_baseline.py close`: `closed: rerun-2026-11-05-claude-sonnet-5-5-wave-b, part 1, 3 file(s)`. `check-words`: 123 files scanned, 0 hits.
- Leak gate over the folder: `leak gate passed: 286 file(s) scanned, 0 findings`. gitleaks over the folder: exit 0.
- Row 10 `mechanical-checks.md` holds the `Row 10 status form` section. Write-escape corpus: 4 tests, OK.
- Frozen paths against e85d347: 0 changes. SKILL.md 11994 bytes. Files changed outside `.planning`, `tests/harness` and the labelled evidence folders: 0.
- Whole-suite `tests/harness/selftest` with the folder present: OK, `0 model calls`, 1947 tests (floor 1947 from 04-10).
- The evidence commit `test(04-11): file wave B evidence` passed the Phase 1 hooks; no trailer, no hook skipped.

Suite count: 1947

## Deviations

- The executor's Step 0 commit guard refuses commits on `main` (the sequential dispatch runs on the main checkout because the unpushed Phase 4 evidence makes worktree isolation degrade). The executor halted after the verification without committing; the orchestrator made the evidence commit and this summary's commit on main. No config was changed and no hook was bypassed.
- bokiko's word was `go` without an amount; the budget passed was the plan's recommended 3.50 USD.

## Notes for the next plans

- The wave cost 1.43 USD; the Phase 4 paid total is now 2.22 USD over nine rows.
- Row 10's s2 is the costliest stage so far (0.31 USD); the hostile tree and the refused redirect add turns.
- The real binary refuses an output redirection inside the project under default permission mode; the sidecar can be produced by the Write tool instead, without NUL bytes. Plan 04-18's comparer and plan 04-21's review brief should read the status-form counts with that in mind.
