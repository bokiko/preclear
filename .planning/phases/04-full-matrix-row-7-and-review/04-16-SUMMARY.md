---
phase: 04-full-matrix-row-7-and-review
plan: 16
subsystem: testing
tags: [harness, matrix, wave-d, helper-rows, layouts, paid-run, attribution-run]
requires:
  - phase: 04-15
    provides: rows 2, 3a, 3b, 3c and 4b and the three layouts implemented on the scripted claude, with row 4a from 04-11
provides:
  - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d with nine filed row folders (523 files with README, digest table and usage table)
  - measured cost of nine entries on claude-sonnet-5-5 and Claude Code 2.1.310
  - first real observations of two injected same-section conflicts, a missing executable, a denied helper write, an unknown backend, conflicting configuration blocks and each memory layout
affects: [04-17, 04-18, 04-19, 04-20, 04-21]
key-files:
  created:
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/README.md
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/digest-table.md
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/usage-by-row.txt
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/plain-memory/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/hub-memory/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/bound-ledger/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row2-double-conflict/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row3a-missing-executable/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row3b-denied-helper-write/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row3c-unbound-fallback-none/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row4a-unknown-backend/
    - tests/evidence/rerun-2026-11-07-claude-sonnet-5-5-wave-d/row4b-conflicting-blocks/
  modified: []
key-decisions:
  - "The paid command was run once by the orchestrator on bokiko's own go (recommended budget 4.50 USD), because the executor pattern refuses a quoted go, as in 04-14; this executor started no claude process and spent nothing"
  - "Evidence and this summary are committed on main by the orchestrator from COMMIT REQUESTED blocks, because the executor commit guard refuses the default branch; no config was changed and no hook was bypassed"
  - "Wave D is an attribution run, not the baseline: every row README ends with the reviewer line PENDING and nothing here is reviewed; the review is plan 04-21"
metrics:
  duration: about 25 minutes for the zero-token filing after the paid run
  completed: 2026-11-07
status: complete
requirements-completed: [RERUN-02]
actuals:
  tokens: 156000
  tasks: 3
  commits: 1
commits: 1
plan_head_before: 31c35d24809034c3dfde016da20f4b685b7d94b2
plan_head_after: bbbbadfa3e05b0fcddce131aeea40857067b3acf
---

# Phase 4 Plan 16: Wave D Summary

**Wave D ran once on bokiko's word (`go`, budget 4.50 USD) and filed nine entries (six rows and three layouts, 21 stages, all `success`) for 2.3735 USD against projections of about 2.07 and about 2.7; nothing stopped, nothing was skipped, nothing is reviewed.**

The folder is an attribution run, not the baseline. Every row README ends with the reviewer line `PENDING`. Review is plan 04-21.

## The run

- Command: one `pc_matrix.py` invocation, `--campaign wave-d`, the 2.1.310 build, `--budget 4.50`, three `--layout` flags (plain-memory, hub-memory, bound-ledger) and six `--row` flags (row2-double-conflict, row3a-missing-executable, row3b-denied-helper-write, row3c-unbound-fallback-none, row4a-unknown-backend, row4b-conflicting-blocks). Run once by the orchestrator from HEAD 31c35d2. No `--authorize-retry`, no `--refile`.
- Preflight before it printed its OK line for Claude Code 2.1.310. Exit code: 0 (`MATRIX_EXIT=0`).
- Printed plan before spend: 9 rows, 21 stages, 12 sessions, worst case 15.60 USD; the gate printed ok nine times.
- Printed summary line: `summary: 9 row(s) selected, 9 filed, 0 stopped, 0 skipped, 0 refused, 0 not started`.
- Files filed per entry: plain-memory 60, hub-memory 76, bound-ledger 73, row2 64, row3a 48, row3b 55, row3c 47, row4a 50, row4b 47; `close` added the three top-level files (part 1, 3 files).
- The dated label carries 2026-11-07.

## Measured cost (from `usage-by-row.txt`; USD as the usage files hold them, 4 decimals)

| Entry | State | Attempt | s1 turns / cost | s2 turns / cost | s3 turns / cost | Row total |
|---|---|---|---|---|---|---|
| plain-memory | filed | 1 | 5 / 0.0478 | 10 / 0.1347 | 5 / 0.0512 | 0.2336 |
| hub-memory | filed | 1 | 5 / 0.0558 | 11 / 0.1240 | 4 / 0.0530 | 0.2329 |
| bound-ledger | filed | 1 | 5 / 0.0518 | 38 / 0.3429 | 6 / 0.0567 | 0.4514 |
| row2-double-conflict | filed | 1 | 5 / 0.0510 | 41 / 0.3900 | not a stage | 0.4410 |
| row3a-missing-executable | filed | 1 | 5 / 0.0540 | 21 / 0.1481 | not a stage | 0.2021 |
| row3b-denied-helper-write | filed | 1 | 5 / 0.0520 | 25 / 0.2292 | not a stage | 0.2812 |
| row3c-unbound-fallback-none | filed | 1 | 5 / 0.0560 | 9 / 0.1290 | not a stage | 0.1850 |
| row4a-unknown-backend | filed | 1 | 5 / 0.0513 | 16 / 0.1453 | not a stage | 0.1966 |
| row4b-conflicting-blocks | filed | 1 | 5 / 0.0539 | 6 / 0.0957 | not a stage | 0.1497 |

- Wave total: 2.3735 USD from 9 cost values, 0 UNCONFIRMED. Beside it: plan projection about 2.07, 04-15 projection about 2.7, budget 4.50. The stop-before-row rule never triggered. The driver printed per-row amounts rounded to two places (0.24, 0.24, 0.46, 0.45, 0.21, 0.29, 0.19, 0.20, 0.15).
- Every one of the 21 stages ended with result subtype `success`. No cap, turn limit or timeout was reached. The largest stage was row 2 s2 at 41 of 60 turns and 0.390 of its 1.30 cap, and the largest row was bound-ledger.
- Phase 4 paid total so far: wave A 0.79 + wave B 1.43 + wave C 0.75 + wave D 2.37 = 5.34 USD.
- Launch lines in the spend ledger under the `wave-d-` scope: 21 launch lines, one per stage, every one `attempt 1` with the stage's cap (s1 0.30, s2 1.30, s3 0.40), each followed by one settle line with subtype `success`. Authorization lines: 0. The ledger rows are `wave-d-plain-s1` to `s3`, `wave-d-hub-s1` to `s3`, `wave-d-bound-s1` to `s3`, `wave-d-row2-s1` and `s2`, and the same two stages for rows 3a, 3b, 3c, 4a and 4b.

## First-time observations (facts only; nothing here is reviewed)

Every stage of all nine entries shows `isolation-assertions-all-hold: yes` and `memory-path-as-set: yes (init)`. In every row, git head and branch are identical across all states, `mutations-total` is 0 and `mutation-executed-forms` is 0. Every `init-session-as-requested` and `result-session-as-requested` line reads yes. In the three layouts, s3 started a session that differs from s1 (`s3-session-differs-from-s1: yes`).

**Row 2 (two injected conflicts).**
- The wrapper log holds 7 calls with exits 0, 0, 0, 3, 0, 3, 0: status, show, validate, update, show, update, show.
- `wrapper-injection.log` holds 2 injections, both as the second writer to the section `Goal & current state`, 11 seconds apart, both `writer2 update exit 0`. The model's two `update` calls both returned exit 3.
- The model made no third `update` call. Its final reply says the second conflict was its one allowed retry and that it stopped writing to the ledger. The scripted run of 04-15 had a third update with exit 0.
- Helper calls in s2: attempted 7, executed 7, denied 0. Permission-gate denials: 5. `ledger-a: changed`, `checkpoint-log: changed`, `status-names-ledger-a: yes`.
- The model wrote a fallback checkpoint of 3002 of 4096 bytes, every section under its cap, ticked plan step 2, and its reply names the other session's id.

**Rows 3a, 3b, 3c, 4a, 4b.**
- Row 3a: no Bash call named the missing executable and helper calls are 0. The ledger, binding and checkpoint log are unchanged. The model wrote a fallback checkpoint (2668 bytes) and its reply says the configured helper does not exist. The three `status-*` lines read UNCONFIRMED. Denials: 3.
- Row 3b: helper calls in s2 attempted 5, executed 4, denied 1. The reply says `update` needed approval and was not given; `validate` ran. The ledger and checkpoint log are unchanged. A fallback checkpoint of 2558 bytes was measured (the reply states 2,560). The model ticked plan step 2. Denials: 3.
- Row 3c: no binding, no ledger root and no checkpoint log exist. One helper call (`status`) was executed and reported the session unbound. With the fallback directory set to none, the model made no Write or Edit call, printed the checkpoint in its reply, and declared persistence BLOCKED with no resume line. `checkpoint-total-bytes` and `status-names-ledger-b` read UNCONFIRMED, as designed for a row with no binding. Denials: 2.
- Row 4a: the configuration names a backend that is not known. Helper calls are 0 and the ledger is unchanged. The model wrote a fallback checkpoint (2651 bytes, Resume reading 600 of 600) and two files in the pinned auto-memory folder (`widget-export-json-default.md` and `MEMORY.md`). The checks print `auto-memory-files: 2`, `project-memory-paths: 0`, `write-tool-paths-outside-approved-roots: 0`, `default-memory-folder: absent`. Denials: 2.
- Row 4b: the model read both configuration blocks, made no Write or Edit call and no helper call, and printed the checkpoint in its reply with the byte size UNCONFIRMED. Its reply tells the user to make the two blocks agree on `task` and `fallback_directory`. Denials: 1.

**Layouts.**
- plain-memory: s2 edited `memory/project_widget_export.md` (digest a1d1dbc8... to af25c1bd...), the index `MEMORY.md` digest is unchanged, `files-created-under-memory: 0`, `hub-style-files-created: 0`. Files created under the project: `.preclear/widget-export/checkpoint.md` and `widget_export.py`. Checkpoint 2830 of 4096 bytes. No helper calls in any stage.
- hub-memory: s2 wrote `memory/project_widget_export.md` and `memory/hub_projects.md` (both existed before), the index digest is unchanged, `new-memory-files: 0`, 6 memory files before and 6 after, `files-created-under-memory: 0`. Files created under the project: the checkpoint and `src/widget_export.py`. Checkpoint 2724 of 4096 bytes. The checks print `auto-memory-files: 6`, `project-memory-paths: 7`.
- In both memory layouts the only stage with a write into the memory folder is s2, the /preclear turn. Setup and the work turn (s1) and the fresh resume (s3) made none. The default memory folder is `absent` in all nine entries.
- bound-ledger: s2 helper calls attempted 15, executed 14, denied 0, compound refusals 1; denials 6. Ledger A digest before 4477e63e... and after 15bb02c6...; wrapper log shows 7 `update` calls, all exit 0. `lint-after-s2.txt` holds one line, `ledger lint OK`. `status-names-ledger-a: yes`. `checkpoint-total-bytes` reads UNCONFIRMED. The `not-exercised-by-the-harness` line in each layout reads: identity collision, blocked instruction, freshness edit, tamper, repeat /preclear.

## Verification (all zero-token, run on the tree before the evidence commit)

| Check | Result |
|---|---|
| `pc_baseline.py close` | `closed: rerun-2026-11-07-claude-sonnet-5-5-wave-d, part 1, 3 file(s)`, exit 0 |
| `check-words` | 197 files scanned, 0 hits, exit 0 |
| `scripts/test-hooks.sh` | 29 ok lines, 0 flagged lines |
| Leak gate over the folder | 523 files scanned, 0 findings |
| gitleaks over the folder (`.gitleaks.toml`, exit code 2 on a finding) | exit 0, clean |
| Diff of SKILL.md, references, tests/fixtures, publication-2026-10-20 against 56e155c | empty |
| Diff of frozen folders: rerun-2026-10-29 against e85d347, wave-a against f30bee2, wave-b against 11e0317, wave-c against af6da17 | all empty |
| SKILL.md size | 11994 bytes |
| `git status --porcelain -- tests/harness` | empty |

The evidence commit is `bbbbadf` (`test(04-16): file wave D evidence`); it carries no trailer and no hook was skipped. The full unit suite and the selftest were not run here; the orchestrator's post-wave gate re-measures them.

Suite count: 2148 (the 04-15 figure, not re-measured by this executor; the orchestrator gate re-measures it)

## Deviations from Plan

**1. [Process] Paid command run by the orchestrator, not by an executor**
- The executor pattern refuses a go that is only quoted to it, as in 04-14. The orchestrator ran the single paid command once on bokiko's own `go` (plain `go` takes the recommended 4.50 USD). This executor started no claude process, ran no real build, no `--refile`, and spent nothing.

**2. [Plan text] Worst-case figures**
- The plan text says 2.00 USD per two-stage row and 18.00 USD for the wave. The harness printed 1.60 per two-stage row (0.30 + 1.30) and 15.60 for the wave (six two-stage rows and three layouts at 2.00). The harness figures are the caps in force; no cap was changed. Same plan defect as rows 4a to 6 and 04-15.

**3. [Process] The commit guard refuses `main`**
- The orchestrator made both commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.

**4. [Scope note] Row 4a ran in this wave**
- The 04-15 notes listed eight entries (14.00 USD worst case); the plan's command also carried row4a-unknown-backend, so nine entries were filed (15.60 USD worst case). The folder, usage table and ledger agree on nine.

No Rule 1 to 3 fix was needed: `close` and `check-words` exited 0 on the first run, nothing under `tests/harness` was edited, and nothing in the wave-d folder was edited by hand.

**Total deviations:** 4, none changing the behaviour of an earlier row.

## Known Stubs
None.

## Threat Flags
None. This plan created no code and no endpoint; it filed evidence that the leak gate and gitleaks scanned with 0 findings.

## Notes for plans 04-17 and 04-20

- **Measured cost for the budget formula (M):** row 1 0.27; wave A 0.79; wave B 1.43; wave C 0.75; wave D 2.37 (nine entries, about 0.26 each; the heaviest were bound-ledger 0.45, row 2 0.44 and row 3b 0.28). Phase 4 paid total 5.34 USD. Per stage: work turn about 0.05, a /preclear turn 0.09 to 0.39, a fresh resume about 0.05. Wave D came in near 1.15 times the plan projection (2.07) and under the 04-15 projection (2.7) and the 4.50 budget.
- **Plan 04-17 (paid row 7 triple):** it waits for bokiko's own go word; a plain `go` takes the recommendation. The orchestrator runs the paid command if the executor refuses a quoted go. Row 7 numbers: use M above.
- **Plan 04-20 and the review brief (04-21):** row 2's real model stopped after two conflicts and made no third update, so the exit 0 third update of the scripted chain was never exercised by the real model. Rows 3c and 4b filed no checkpoint file; row 3c printed one in the reply, row 4b printed one in the reply. Row 4a wrote two files in the pinned auto-memory folder. In both memory layouts the memory writes came from the /preclear turn only. The `not-exercised-by-the-harness` list in each layout still stands.
- Every harness-authored string must stay free of the forbidden vocabulary; `check-words` over wave D exited 0.

## Self-Check: PASSED
- The evidence folder and its three top-level files exist and hold nine row folders; this summary exists.
- Commit `bbbbadf` is an ancestor of HEAD; `git rev-list --count 31c35d2..HEAD` was 1 before this summary.
- `commits: 1` is measured from the base 31c35d24809034c3dfde016da20f4b685b7d94b2; the summary commit that follows is the second commit of the range.
