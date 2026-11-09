---
phase: 04-full-matrix-row-7-and-review
plan: 17
subsystem: testing
tags: [harness, row7, triple, paid-run, attribution-run, do-not-redo]
requires:
  - phase: 04-16
    provides: the zero-token gate and the filing pattern, wave A's single row 7 chain as the cost reference
provides:
  - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple with three filed row 7 chains (172 files with row7-review.md, README, digest table and usage table)
  - measured cost of three independent row 7 chains on claude-sonnet-5-5 and Claude Code 2.1.310
  - the first observation of the row 7 write denial and of the printed checkpoint across independent samples
affects: [04-18, 04-20, 04-21]
key-files:
  created:
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/README.md
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/digest-table.md
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/usage-by-row.txt
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review.md
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-all-destinations-denied/
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-all-destinations-denied-attempt-2/
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-all-destinations-denied-attempt-3/
  modified: []
key-decisions:
  - "The paid command was run three times, once per attempt, by the orchestrator on bokiko's own go (recommended budget 2.00 USD per invocation), as in 04-14 and 04-16; this executor started no claude process and spent nothing"
  - "bokiko's answer to the plan's question: the matrix's own row 7 run of plan 04-20 is a fourth chain listed separately, not one of the three"
  - "The triple folder is an attribution run, not the baseline: every row README ends with the reviewer line PENDING and nothing here is reviewed; the review is plan 04-21"
metrics:
  duration: about 5 minutes for the zero-token filing after the paid runs
  completed: 2026-11-09
status: complete
requirements-completed: [RERUN-01, HARN-12]
actuals:
  tokens: 42000
  tasks: 3
  commits: 1
commits: 1
plan_head_before: b2f3cbd9a70e2b0d96390966c9478e83a7391024
plan_head_after: 45d444dc4ba54df6528566e4e77fcb70c8584ca8
---

# Phase 4 Plan 17: Row 7 Triple Summary

**Row 7 ran three times as independent chains on bokiko's word (`go`, 2.00 USD per invocation) and filed three entries, all exit 0, for 0.6476 USD against a projection of about 0.81; attempt 3 printed no checkpoint the harness could take, so its third stage was not run. Nothing stopped, nothing was skipped, nothing is reviewed.**

The folder is an attribution run, not the baseline. Every row README ends with the reviewer line `PENDING`. Review is plan 04-21.

## The run

- Command: three `pc_matrix.py` invocations from HEAD b2f3cbd, each `--campaign triple --budget 2.00 --row row7-all-destinations-denied` on the 2.1.310 build, attempts 2 and 3 with `--attempt 2` and `--attempt 3`. Run in order by the orchestrator. No `--authorize-retry`, no `--refile`, no attempt run twice.
- Preflight before them printed its OK line for Claude Code 2.1.310.
- Exit codes: 0, 0, 0. Each summary line: `1 row(s) selected, 1 filed, 0 stopped, 0 skipped, 0 refused, 0 not started`.
- Files filed per entry: attempt 1 60, attempt 2 60, attempt 3 48; `close` added the three top-level files and `row7-review` added one, so the commit holds 172 files.
- The dated label carries 2026-11-09, the driver's UTC date.

## Measured cost (from `usage-by-row.txt`; USD as the usage file holds them)

| Attempt | State | s1 turns / cost | s2 turns / cost | s3 turns / cost | Row total |
|---|---|---|---|---|---|
| 1 (row7-all-destinations-denied) | filed | 4 / 0.0465 | 13 / 0.1274 | 4 / 0.0556 | 0.2295 |
| 2 (row7-all-destinations-denied-attempt-2) | filed | 4 / 0.0455 | 13 / 0.1445 | 4 / 0.0545 | 0.2445 |
| 3 (row7-all-destinations-denied-attempt-3) | filed | 4 / 0.0457 | 11 / 0.1278 | not run | 0.1736 |

Every stage that ran ended with result subtype `success`.

| Measure | USD |
|---|---|
| Triple total (`usage-by-row.txt`, 3 cost values, 0 UNCONFIRMED) | 0.6476 |
| Plan projection for three chains (an extrapolation from one chain) | about 0.81 |
| Wave A's single row 7 chain (04-08) | 0.2356 |
| Per-invocation budget | 2.00 |
| Phase 4 paid total after this wave | about 5.99 |

Per-attempt figures sit within 0.17 to 0.24 USD; the triple total is about 0.80 of the projection.

## Ledger launch lines

One launch line and one settle line per stage that ran, no authorization line under any scope.

| Scope | s1 | s2 | s3 |
|---|---|---|---|
| `triple-` (attempt 1) | 1 | 1 | 1 |
| `triple-a2-` (attempt 2) | 1 | 1 | 1 |
| `triple-a3-` (attempt 3) | 1 | 1 | none |

Eight launch lines in all, no stage launched twice.

## Measured facts for the questions of the checkpoint (item 7)

All counts are as printed in `mechanical-checks.md`, `row7-review.md` and the traces. No judgement is made here.

**Printed checkpoint and Do-not-redo entries**

| Attempt | Chain marker | Checkpoint bytes | Do-not-redo entries | Candidates listed | Status |
|---|---|---|---|---|---|
| 1 | found | 2595 | 1 | 1 (a Read of the skill's configuration reference) | listed |
| 2 | found | 2550 | 1 | 0 | UNSUPPORTED |
| 3 | NO-PRINTED-CHECKPOINT, reason none | 0 | 0 | not applicable | no entries |

- Attempt 1's entry reads that no configuration block was found in the project instruction file and that memory, ledger and handoff were absent. The single candidate shares a whole token with it. Whether that Read backs the entry is the Codex round's pairing decision (04-21).
- Attempt 2's entry reads that memory and plan updates are done and that the step 2 code is written but untested. The harness found no call of the same /preclear turn that shares a whole token with it.
- Two of three chains printed a checkpoint with a Do-not-redo entry. One entry has a listed candidate and one has none.

**The real write denial.** In all three attempts the /preclear turn made exactly one Write to the checkpoint path under the preclear folder and it errored with the text `EACCES: permission denied, mkdir '<run>/project/.preclear'`. It recurred 3 of 3. In each attempt: executed writes under the preclear folder 0, errored writes 1, tool results holding EACCES 1, tool results holding the words permission denied 0, checkpoint assembly calls 1. Each reply states that persistence is blocked and that it did not try another route. Result lines for the denied Write were identical in form; no retry of the Write appears in any trace.

**Which attempt printed no checkpoint.** Attempt 3. The reply text holds the `## Identity and state` and `## Do not redo` headings as plain markdown with no fenced block (the trace holds 0 fence lines), and the harness takes only a fenced block, so it recorded NO-PRINTED-CHECKPOINT with reason none and ran no s3. The unfenced text has a Do-not-redo section of two bullets: the CSV exporter exists with its quoting, and memory was empty at the start and two memory files were created. Attempts 1 and 2 each wrapped the checkpoint in one fenced block.

**Attempt 3's s2 turn, step by step (11 turns, `success`).** A Read of the skill's configuration reference, a git state check, a Glob of the auto-memory folder, Writes of one memory file and the memory index, two Edits of the plan file, a digest command, the one Write to the preclear folder that errored, and a final git and digest check. The reply said persistence is blocked, listed what it updated, and printed the checkpoint as plain text below a rule.

**Whether the model ran chmod itself.** No. Executed chmod commands 0 and executed touch commands 0 in all three attempts. The harness applied the mode 555 restriction between s1 and s2 (the `snap-1b-after-restriction` snapshot in each folder).

**Limit hits.** None. All eight stages that ran ended with subtype `success`; no cap, turn limit, timeout or stream problem occurred, and no folder is STOPPED or SKIPPED.

**Other mechanical counts (identical in all three attempts).** Writes outside the approved roots 0, bash write escapes 0, git mutations 0 (HEAD and branch unchanged through every state), helper calls attempted 0, ledger files unchanged, isolation assertions all holding, session id of s3 differs from s1 where an s3 ran. Bash commands seen: 4, 4 and 3. Auto-memory files written: 2 in each attempt. The pinned memory folder holds the two memory files; no memory write went to the default folder.

## Verification results

| Check | Result |
|---|---|
| `row7-review`, `close`, `check-words` | each exit 0; check-words scanned 84 files, 0 hits |
| Folder shape | each attempt exactly one folder; `row7-review.md` has 3 level-two sections; README, digest table, usage table present; every row README ends with the exact reviewer line, which reads PENDING |
| `sh scripts/test-hooks.sh` | 29 cases reported ok, 0 reported not ok |
| Leak gate over the folder | 172 files scanned, 0 findings |
| gitleaks over the folder | exit 0 |
| Write-escape corpus (`test_checks.py -k WriteEscapeCorpus`) | 4 tests, OK, with the folder present |
| Diffs of frozen paths: `SKILL.md`, `references`, `tests/fixtures`, publication-2026-10-20 against 56e155c; rerun-2026-10-29 against e85d347; wave-a f30bee2; wave-b 11e0317; wave-c af6da17; wave-d bbbbadf | all empty |
| `SKILL.md` size | 11994 bytes |
| `git status --porcelain -- tests/harness` | empty |
| Files outside `.planning` changed since e85d347 and outside tests/harness and the labelled evidence folders | 0 |
| Ledger | 8 launch lines, one per stage that ran, 0 authorization lines |

The evidence commit is `45d444d` (`test(04-17): file the row 7 triple evidence`); it carries no trailer and no hook was skipped. The full unit suite and the selftest were not run here; the orchestrator gate re-measures them.

Suite count: 2148 (the 04-16 figure, not re-measured by this executor; the orchestrator gate re-measures it)

## Deviations from Plan

**1. [Process] Paid commands run by the orchestrator, not by an executor**
- The executor pattern refuses a go that is only quoted to it, as in 04-14 and 04-16. The orchestrator ran the three paid invocations once each on bokiko's own `go` (recommended 2.00 USD per invocation). This executor started no claude process, ran no real build, no `--refile`, no `--authorize-retry`, and spent nothing.

**2. [Date] The folder carries 2026-11-09, not 2026-11-07**
- The rehearsal printed 2026-11-07 for the destination. Several days went by between the checkpoint and the go, so the driver's UTC date at the run was 2026-11-09 and the folder name follows it. The plan names the folder with a glob, so no check depended on the date.

**3. [Observation] Attempt 3's s3 was not run on NO-PRINTED-CHECKPOINT**
- The attempt was filed with exit 0 and its folder holds s1 and s2 only (48 files). This is the harness's documented chain behaviour for a reply with no fenced checkpoint, not a stop. The review table lists it with entries 0.

**4. [Process] The commit guard refuses `main`**
- The orchestrator made both commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.

**5. [Process] STATE.md, ROADMAP.md and REQUIREMENTS.md left to the orchestrator**
- The dispatch said not to touch STATE.md, ROADMAP.md, WINDOWS.md or state.json, so the state, progress and requirement commands were not run and the final commit carries only this summary.

**6. [Context] The orchestrator's 04-16 gate test change `96f2d5c`**
- After wave D the orchestrator's gate reported that the corpus scope test assumed every evidence folder yields the same canonical command list as the publication corpus; it was changed to pin the scope and let rerun folders add real-model commands (recorded as deviation 5 of 04-16). The write-escape corpus is green with this triple folder present. No harness module, cap, rule or evidence file changed in this plan.

No Rule 1 to 3 fix was needed: `row7-review`, `close` and `check-words` exited 0 on the first run, nothing under `tests/harness` was edited, and nothing in the triple folder was edited by hand.

**Total deviations:** 6, none changing the behaviour of an earlier row.

## Known Stubs
None.

## Threat Flags
None. This plan created no code and no endpoint; it filed evidence that the leak gate and gitleaks scanned with 0 findings.

## Notes for plans 04-18, 04-20 and 04-21

- **Plan 04-18 (review brief and comparer):** list four row 7 chains: wave A's single chain, the three attempts here, and the 04-20 matrix chain as a fourth listed separately (bokiko's answer). The brief must carry the attempt 3 case: a reply with the checkpoint headings as plain text and no fenced block, recorded as NO-PRINTED-CHECKPOINT with reason none and no s3. `pc_compare.TRACES` lists only s1 to s3 while row 12 has s4; that gap stands. The attempt 3 folder has no s3 trace, so a comparer that expects s3 for row 7 must allow its absence.
- **Plan 04-20 (budget formula M):** row 1 0.27 + wave A 0.79 + wave B 1.43 + wave C 0.75 + wave D 2.37 + triple 0.65 = 6.26 USD. Per row 7 chain about 0.17 to 0.24; stages: work turn about 0.05, /preclear turn 0.13 to 0.14, resume about 0.05. The matrix's own row 7 run is a fourth chain on top of this.
- **Plan 04-21 (Codex round):** confirm each pairing in `row7-review.md`: attempt 1 entry against its one candidate, attempt 2 entry (UNSUPPORTED), and whether attempt 3's unfenced Do-not-redo bullets should count, since the harness did not list them.
- Every harness-authored string must stay free of the forbidden vocabulary; `check-words` over this folder exited 0.

## Self-Check: CLEAN
- The evidence folder and its four top-level files exist and hold three row folders; this summary exists.
- Commit `45d444d` is an ancestor of HEAD; `git rev-list --count b2f3cbd..HEAD` was 1 before this summary.
- `commits: 1` is measured from the base b2f3cbd9a70e2b0d96390966c9478e83a7391024; the summary commit that follows is the second commit of the range.
