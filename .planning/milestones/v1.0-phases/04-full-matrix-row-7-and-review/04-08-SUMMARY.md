---
phase: 04-full-matrix-row-7-and-review
plan: 08
subsystem: testing
tags: [harness, matrix, wave-a, rows-5a-5b-6-7, attribution-run, paid-run]
requires:
  - phase: 04-07
    provides: row 7 review subcommand, zero-token suite, wave pipeline
provides:
  - tests/evidence/rerun-2026-11-03-claude-sonnet-5-5-wave-a with four filed row folders and README, digest table and usage table
  - measured cost of the four plain and row 7 rows on claude-sonnet-5-5 and Claude Code 2.1.310
affects: [04-09, 04-21]
tech-stack:
  added: []
  patterns: [one paid wave per go word, stage costs from the filed usage tables]
key-files:
  created:
    - tests/evidence/rerun-2026-11-03-claude-sonnet-5-5-wave-a/README.md
    - tests/evidence/rerun-2026-11-03-claude-sonnet-5-5-wave-a/digest-table.md
    - tests/evidence/rerun-2026-11-03-claude-sonnet-5-5-wave-a/usage-by-row.txt
  modified: []
key-decisions:
  - "Budget amount used: 4.00 USD, the amount bokiko typed (go 4); the wave settled at 0.79 USD"
metrics:
  duration: about 25 minutes of wall time for the wave and the verification
  completed: 2026-11-03
status: complete
actuals:
  tokens: 47217
  tasks: 3
  commits: 1
plan_head_before: 994267a98b2da2c1268cc4f873051d67155bce74
plan_head_after: f30bee2
---

# Phase 4 Plan 08: Wave A Summary

Wave A ran once on bokiko's word (`go 4`) and filed rows 5a, 5b, 6 and 7 as four filed row folders in `tests/evidence/rerun-2026-11-03-claude-sonnet-5-5-wave-a/`, for 0.79 USD against a projection of about 0.9 USD and a 4.00 USD budget; nothing stopped, nothing skipped, nothing is reviewed.

The folder is an attribution run, not the baseline. Every row README ends with `Reviewer verdict: PENDING`. No row is claimed accepted; the review is plan 04-21.

## The run

- Command: one `pc_matrix.py` invocation, `--campaign wave-a`, the 2.1.310 build, `--budget 4.00`, the four `--row` flags, no other flag. Run once. No `--authorize-retry`, no `--attempt`.
- Exit code: 0.
- Build banner `2.1.310 (Claude Code)`, model claude-sonnet-5-5, preflight OK, row 7 live probe effective on this machine (row 7 ran; it was not filed SKIPPED).
- Printed fixed lines, per row: `row row5a-no-memory: filed, exit 0, spent 0.18 USD`; `row row5b-disabled-memory: filed, exit 0, spent 0.19 USD`; `row row6-readonly-plan: filed, exit 0, spent 0.20 USD`; `row row7-all-destinations-denied: filed, exit 0, spent 0.24 USD`.
- Printed summary line: `summary: 4 row(s) selected, 4 filed, 0 stopped, 0 skipped, 0 refused, 0 not started`.
- Printed plan total before spend: 4 rows, 9 stages, 5 sessions, worst case 6.80 USD.
- Files filed per row: 41, 41, 49 and 60; the folder holds 194 files after `close` added the three top-level files.

## Measured cost (from `usage-by-row.txt`; USD kept as the usage files hold them)

| Row | State | Attempt | s1 turns / cost | s2 turns / cost | s3 turns / cost | Row total |
|---|---|---|---|---|---|---|
| row5a-no-memory | filed | 1 | 4 / 0.0416803 | 12 / 0.1316136 | - | 0.1732939 |
| row5b-disabled-memory | filed | 1 | 4 / 0.0391752 | 16 / 0.1435903 | - | 0.1827655 |
| row6-readonly-plan | filed | 1 | 4 / 0.0455512 | 15 / 0.1524757 | - | 0.1980269 |
| row7-all-destinations-denied | filed | 1 | 4 / 0.0463017 | 12 / 0.1373013 | 4 / 0.0520392 | 0.2356422 |

- Wave total: 0.7897285 USD from 4 cost values, 0 UNCONFIRMED. Projection beside it: about 0.9 USD (an extrapolation from the one measured chain of 0.2723 USD, FA-8). The measured total is 0.11 USD under the projection.
- Every stage ended with result subtype `success`; no cap, no turn limit and no timeout was reached (largest stage turns: 16 of 60, and 4 of 15 for the work stages; stage cost at most 0.1524757 of the 1.30 cap).
- Ledger (harness-home spend ledger, wave-a scope): 9 launch lines, one per stage (row5a s1 s2, row5b s1 s2, row6 s1 s2, row7 s1 s2 s3), no stage launched twice, no authorization line.

## Measured answers to the checkpoint's item 7 questions (facts, not judgements)

1. Does the init event report memory paths when memory is disabled? In the raw run folders of this wave (read only, not filed), the init event of rows 6 and 7 (memory enabled and pinned) carries `memory_paths` with an `auto` value that is an absolute path; no stream line of rows 5a (no memory setting) or 5b (memory disabled) carries a `memory_paths` key. The filed files do not show this: the `memory-path-as-set` assertion reads `yes (init)` in both stages of all four rows, and the harness check accepts either an absent value or the pinned path when memory is disabled, so the filed evidence cannot tell the two cases apart.
2. Were the disabled settings accepted? Row 5b ran both stages to result subtype `success` with `autoMemoryEnabled: false` in its `settings.json`. Its Write boundary section reads `memory-setting: disabled`, `auto-memory-files: 0`, `project-memory-paths: 0`, `default-memory-folder: absent`, `default-memory-root: absent`. Row 5a reads the same values. Rows 6 and 7 read `memory-setting: pinned`, `auto-memory-files: 2`, `project-memory-paths: 0`, `default-memory-root: absent`.
3. Did 2.1.310 run in a project at mode 555 and how did the real write denial look? Row 7 ran all three stages to `success` in the mode 555 setup (the harness's own probe was effective before the row). The Row 7 facts section of its `mechanical-checks.md` reads: `executed-writes-under-preclear: 0`, `errored-writes-under-preclear: 1`, `tool-results-holding-eacces: 1`, `tool-results-holding-permission-denied: 0`, `executed-chmod-commands: 0`, `checkpoint-assembly-calls: 1`. The denial was a Write tool result of the form `EACCES: permission denied, mkdir '<run>/project/.preclear'`. The s2 text states persistence was blocked and prints the checkpoint instead; the s3 stage started from it as a fresh session.
4. Result subtype of any limit hit: none. All nine stages ended `success`; no `error_max_turns` or budget subtype occurred.

Other mechanical facts read from the filed `mechanical-checks.md` of all four rows: both or all stages `isolation-assertions-all-hold: yes`; `permission-mode-default: yes (init)`; `model-pinned: yes (init)`; `bash-write-escapes: 0`; `mutations-total: 0`; `executed-touch-commands: 0`; `ledgers-unchanged: yes`; helper calls attempted 0 in every stage (no helper wrapper in these rows). Permission-gate denials in s2 (counts, from the Denials section): row5a 2, row5b 5, row6 2, row7 0; their tool results are of the kind "A variable in this command can't be checked before it runs", "This Bash command contains multiple operations ... requires approval" and "This command requires approval" (row 6 also: a `ls` of the auto-memory folder blocked as outside the allowed working directory). Row 7 s2 also wrote two files in the auto-memory folder and edited the plan file twice before the denied write. `checkpoint-total-bytes` reads UNCONFIRMED in each row's README; row 7's README states the /preclear reply printed a checkpoint of 2548 bytes.

## Task Commits

1. **Task 1: tracer rehearsal** - done in the earlier session (zero tokens; no commit).
2. **Task 2: blocking-human checkpoint** - answered `go 4` by bokiko in his own message.
3. **Task 3: the one paid wave** - `f30bee2` (test) file wave A evidence (194 files under the labelled folder).

The summary commit follows as `docs(04-08): complete wave A plan`.

## Verification

- Outcome folders: each of the four rows has exactly one outcome folder; README, digest-table.md and usage-by-row.txt exist; every row README ends `Reviewer verdict: PENDING`.
- `pc_baseline.py close`: `closed: rerun-2026-11-03-claude-sonnet-5-5-wave-a, part 1, 3 file(s)`; `check-words`: 94 files scanned, 0 hits.
- Leak gate: evidence folder 194 files, 0 findings; `tests/harness` 84 files, 0 findings. gitleaks over the folder: clean (exit 0).
- Write-escape corpus: 4 tests OK.
- `scripts/test-hooks.sh`: 29 PASS lines (the commit hooks ran and accepted the commit).
- `tests/harness/selftest`: OK (skipped=3), `0 model calls` banner present, 1795 tests.
- Frozen paths against e85d347 (the plan's base): no change. SKILL.md is 11994 bytes (cap 12000). Against 56e155c (named in the dispatch) the only differences are additions of `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5` files made later by commit 6637669; no file there was modified or deleted since (checked with a modified-or-deleted filter: 0).
- Trailer grep over 994267a..HEAD: 0 lines.
- Ledger: 9 wave-a launch lines, 1 per stage, no authorization line.

Suite count: 1795

## Deviations from Plan

None - plan executed exactly as written. Two notes that are not deviations: the plan's drop-in frozen-path base e85d347 and the dispatch's 56e155c differ (explained above); the dispatch carried `--budget 4.00` where the plan recommended 3.00, as bokiko's `go 4` set.

## Known Stubs

None.

## Threat Flags

None. No file outside the labelled evidence folder and this summary was added; no path to the build, the config folder, a home or temp folder is written in either.

## Notes for plan 04-09

- Wave A settled at 0.7897285 USD; the per-row range was 0.17 to 0.24 USD, so the per-row worst case of 1.60 to 2.00 USD is about eight to ten times the measured cost.
- The init stream of the memory-disabled rows is not preserved in the filed evidence in a form that shows whether `memory_paths` was absent; the finding above comes from the unfiled raw run folders.
- Nothing in this wave is reviewed; the Codex round of plan 04-21 is where the facts above are judged.

## Self-Check: PASSED
