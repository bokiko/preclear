---
phase: 04-full-matrix-row-7-and-review
plan: 14
subsystem: testing
tags: [harness, matrix, wave-c, rows-11-12, git-wrapper, injector, frozen-copy, four-stage-chain, attribution-run, paid-run]
requires:
  - phase: 04-12
    provides: row 11 with the git wrapper first on the search path of the /preclear stage and the injector
  - phase: 04-13
    provides: row 12 with four stages, the plan-note hook, the fourth stage bounded by the ledger and the frozen-copy section
provides:
  - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c with two filed row folders (60 and 81 files) and README, digest table and usage table
  - measured cost of rows 11 and 12 on claude-sonnet-5-5 and Claude Code 2.1.310
  - the first real observations of the git-wrapper injector, the wrapper's log against the model's tool calls, the between-stage plan edit and a second resumed session
affects: [04-15, 04-18, 04-19, 04-21]
key-files:
  created:
    - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/README.md
    - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/digest-table.md
    - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/usage-by-row.txt
    - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/row11-concurrent-change/
    - tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/row12-frozen-handoff/
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/test_rows_plain.py
key-decisions:
  - "Budget amount used: 2.50 USD, the plan's recommended figure; bokiko's word was a plain `go`, so the orchestrator applied the recommendation; the wave settled at 0.7484 USD"
  - "The paid command was run once by the orchestrator directly on bokiko's own `go` typed in the conversation, because the executor dispatched for it declined a go that was only quoted to it; this executor ran no model process and spent nothing"
  - "The evidence and this summary were committed on main by the orchestrator from COMMIT REQUESTED blocks: the executor's commit guard refuses the default branch, and no config was changed and no hook was bypassed"
  - "The row 11 setup text was reworded by one word (never pass through the wrapper became never go through the wrapper) and a test now checks the setup text of every registered row against the verdict vocabulary"
metrics:
  duration: not measured as one figure; the suite gate alone took 795 seconds
  completed: 2026-11-07
status: complete
actuals:
  tokens: 53000
  tasks: 3
  commits: 2
requirements-completed: [HARN-11, RERUN-02]
commits: 2
plan_head_before: 1725a7b24741c1f992fa1215e8afaa79d3beb3ec
plan_head_after: af6da17ab7afb3cc8e5944fc39baba414cf2885a
---

# Phase 4 Plan 14: Wave C Summary

Wave C ran once on bokiko's word (`go`) and filed rows 11 and 12 as two row folders in `tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/`, for 0.7484 USD against a projection of about 0.72 USD and a 2.50 USD budget; nothing stopped, nothing was skipped, nothing is reviewed.

The folder is an attribution run, not the baseline. Both row READMEs end with `Reviewer verdict: PENDING`. No row is claimed accepted; the review is plan 04-21.

## The run

- Command: one `pc_matrix.py` invocation, `--campaign wave-c`, the 2.1.310 build, `--budget 2.50`, `--row row11-concurrent-change` and `--row row12-frozen-handoff`, no other flag. Run once by the orchestrator. No `--authorize-retry`.
- Exit code: 0.
- Printed plan total before spend: 2 rows, 7 stages, 4 sessions, worst case 4.00 USD; the gate was ok twice.
- Printed per-row lines: `row row11-concurrent-change: filed, exit 0, spent 0.28 USD` and `row row12-frozen-handoff: filed, exit 0, spent 0.48 USD`.
- Printed summary line: `summary: 2 row(s) selected, 2 filed, 0 stopped, 0 skipped, 0 refused, 0 not started`.
- Files filed per row: 60 and 81; `close` added the three top-level files (144 files in the evidence commit). Every stage exit file reads `exit 0`.
- The dated label carries 2026-11-06: the run started before UTC midnight.

## Measured cost (from `usage-by-row.txt`; USD kept as the usage files hold them)

| Row | State | Attempt | s1 turns / cost | s2 turns / cost | s3 turns / cost | s4 turns / cost | Row total |
|---|---|---|---|---|---|---|---|
| row11-concurrent-change | filed | 1 | 5 / 0.0498027 | 19 / 0.1640106 | 5 / 0.0604208 | not a stage of this row | 0.2742341 |
| row12-frozen-handoff | filed | 1 | 4 / 0.045649 | 22 / 0.2172939 | 5 / 0.0567041 | 12 / 0.1545332 | 0.4741802 |

- Wave total: 0.7484143 USD from 2 cost values, 0 UNCONFIRMED. Projection: about 0.72 USD (row 11 about 0.27, row 12 about 0.45). Budget 2.50 USD, so the stop-before-row rule never triggered.
- Cumulative within a session: row 11 s2 0.2138133 (s1 plus s2); row 12 s2 0.2629429 and s4 0.2112373 (s3 plus s4). Every `cumulative-consistent` line reads yes.
- Every one of the 7 stages ended with result subtype `success`. The largest stage was row 12 s2 at 22 of 60 turns and 0.217 of its 1.30 cap.
- Spend ledger under the `wave-c-` scope: 7 launch lines, exactly one per stage (row 11: s1, s2, s3; row 12: s1 to s4), no stage launched twice, no authorization line.
- Phase 4 paid total so far: wave A 0.79 + wave B 1.43 + wave C 0.75 = 2.97 USD.

## Measured answers to the checkpoint's questions (facts, not judgements)

1. **Injector and the model's first status call (row 11).** `injection.log` holds one line, `INJECTED ORD=1`. The wrapper log holds 20 calls, all from the /preclear stage. Calls 1 to 9 carry `-c` options, ran in one second before any model call, and are marked internal; none carries an ordinal. Calls 10 to 20 are the model's. The exact prescribed status argument list (`--no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none`) was logged three times with ordinals 1, 2 and 3; the injection fired on ordinal 1 only, and nothing fired on ordinals 2 and 3. The model's first Bash call held that form inside a compound command; the permission gate refused the compound (a trailing part needed approval) and no git ran for it. The first executed prescribed call was therefore in the model's second Bash call, and it carries ordinal 1.
2. **Internal and model-initiated git calls.** Calls logged: 20. Internal (`-c` prefix): 9. Model-initiated: 11, of which 3 are the prescribed status form.
3. **Join to tool_use ids.** Calls matched to exactly one tool_use: 2. Ambiguous (several executed parts share the arguments, so every candidate id is listed and none is chosen): 9, including all three prescribed status calls. Unmatched: 0. Unreadable lines: 0. The 9 internal calls have no tool_use by definition. `wrapper-files-equal-setup-digests: yes`.
4. **What the model did after the injection (row 11).** Its s2 final reply says `other_task_notes.md` gained 2 lines during the run that the model did not make, and the checkpoint records the file with its digest and an unknown owner. The s3 fresh session's reply says the digests of `widget_export.py`, the plan and `other_task_notes.md` all match the checkpoint. Git facts: head and branch identical in all four states (setup, s1, s2, s3), `mutations-total: 0`, `mutation-executed-forms: 0`. Helper calls attempted, executed and denied: 0 in all stages. s2 had 2 permission-gate denials (the compound command and a command with a variable). Checkpoint 2778 of 4096 bytes, every section under its cap. s3 started a different session from s1 (`s3-session-differs-from-s1: yes`).
5. **Row 12 s4 resumed the s3 session.** Yes by the filed session ids: s1 and s2 share one session id, s3 and s4 share a different one, and `s3-session-differs-from-s1: yes`. Every `init-session-as-requested` and `result-session-as-requested` line reads yes for s1 to s4.
6. **Frozen copy survived untouched.** The row 12 `## Frozen copy` section lists one frozen copy, `checkpoint-<UTC timestamp>-q7k2.md` under the snapshot's preclear copy, `held-in-snapshots 4 of 4, digest-same-in-every-snapshot-that-holds-it yes`. The mutable checkpoint digest is the same in snapshots 2, 2b and 3 and different in snapshot 4 (the refresh). The s4 final reply says the frozen copy is untouched and that it now differs from the mutable file because it predates the refresh.
7. **Plan edit between stages.** The harness appended its fixed note to the plan after s2 (snapshot `snap-2b-after-external-plan-edit` exists; git state unchanged there). The s4 final reply says the plan digest changed because a note on line 8 was added by another session, and says the evidence section records it.
8. **Whether 0.60 and 20 turns sufficed for the refresh.** s4 used 12 of 20 turns and 0.1545332 USD of 0.60. It wrote and edited the checkpoint (3273 of 4096 bytes; the Boundaries section is 599 of 600 after two trims by the model) and printed a resume line. One s4 command was refused by the permission gate (a variable in the command) and the model reran it in another form.
9. **Limits.** None hit. All 7 stages ended `success`; no cap, turn limit or timeout was reached.
10. **Row 12 git and helper facts.** Six states (setup, s1, s2, s2-append-plan-note, s3, s4) with the same head and branch; `mutations-total: 0`; helper calls attempted, executed and denied 0 in s1 to s4. Denials: s2 4, s4 1. The skill and adapter sha256 are identical in both rows; the stub and wrapper digests read UNCONFIRMED in the digest table, as in wave B.

## Verification (all zero-token, run on the tree of 991cf6b before the evidence commit)

- `pc_baseline.py close`: `closed: rerun-2026-11-06-claude-sonnet-5-5-wave-c, part 1, 3 file(s)`.
- `check-words`: first run 56 files scanned, 1 hit (exit 11); after the fix below, 56 files scanned, 0 hits (exit 0).
- Folder shape: exactly one outcome folder per selected entry; `README.md`, `digest-table.md` and `usage-by-row.txt` exist; both row READMEs end `Reviewer verdict: PENDING`.
- Leak gate over the folder: `leak gate passed: 144 file(s) scanned, 0 findings`. gitleaks over the folder: exit 0. Both were run again after the README correction with the same result.
- Row 11 `git-calls-correlated.txt` and row 12 `s4-preclear-refresh-trace.md` exist. Write-escape corpus: 4 tests, OK.
- Ledger check: `launches 7`, every stage once, no authorization line.
- Frozen paths against e85d347: 0 changes. SKILL.md 11994 bytes. Files changed outside `.planning`, `tests/harness` and the labelled evidence folders: 0.
- `pc_baseline.py report` printed the digest and usage tables and wrote nothing. `scripts/test-hooks.sh`: 29 PASS, 0 FAIL.
- Whole-suite `tests/harness/selftest`: OK, `0 model calls`, 2055 tests (3 skipped), floor 2054 from 04-13; the extra test is the one added by the fix below.
- The evidence commit `test(04-14): file wave C evidence` (af6da17) passed the hooks; no trailer, no hook skipped.

Suite count: 2055

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Row 11 setup text held a verdict word, so check-words refused the filed folder**
- **Found during:** Task 3, `check-words` after `close`.
- **Issue:** the harness-authored row 11 Setup paragraph (from plan 04-12, in `tests/harness/pc_rows.py`) said the harness's own git calls "never pass through the wrapper"; the whole word `pass` is in the forbidden vocabulary, so `check-words` printed 1 hit and exited 11. Nothing in the model's output was involved.
- **Fix, made by the orchestrator (this executor edits nothing under tests/harness):** the word was changed to "never go through the wrapper", and `tests/harness/test_rows_plain.py` gained `test_every_registered_row_setup_text_holds_no_verdict_word`, which checks every registered row's setup text against the verdict pattern. Commit 991cf6b.
- **Files modified:** `tests/harness/pc_rows.py`, `tests/harness/test_rows_plain.py`.

### Deviation from the plan's rule that the folder is never edited by hand

**2. [Rule 1 - Bug] One word corrected by hand in the already filed row 11 README**
- The same word was changed in line 3 of `tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/row11-concurrent-change/README.md` by the orchestrator, before the evidence commit. Reason: `--refile` refuses a dated folder that already holds the row folder, and deleting the folder is forbidden. This is the single exception to "`close` is the only writer there"; it changed harness-authored text only.
- No digest covers that README: the digest table digests skill, adapter, stub and wrapper, and the row's `digests.txt` holds four other files. No digest changed. The leak gate and gitleaks were run again afterwards with 0 findings.

### Process

- The Step 0 commit guard refuses `main`, so the orchestrator made the commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.
- Two background wait loops that this executor started to wait for the suite match their own command line and never exit; a request to end them was declined by the permission system and the orchestrator said to leave them alone. They only sleep and read; they write nothing in the repository.

**Total deviations:** 2 plan deviations (one harness text fix, one by-hand README word), 1 process note.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or trust boundary was added; the only changes are one reworded setup string, one added test and the filed evidence, which passed the leak gate and gitleaks.

## Notes for the next plans

- **Plan 04-15 and later paid waves:** wave C cost 0.7484 USD; the Phase 4 paid total is 2.97 USD over eleven rows. Row 12 s2 (0.217) and s4 (0.155) were its costliest stages. Each paid wave still waits for bokiko's own go word.
- **Plan 04-18:** `pc_compare.TRACES` lists only s1 to s3 (the 04-13 observation stands); row 12's filed s4 trace is `s4-preclear-refresh-trace.md` with `s4-preclear-refresh-full-trace.md`, and its snapshot is `snap-4-after-refresh`. `pc_evidence.measure_checkpoint` and the row 10 checklist read the first /preclear stage's snapshot.
- **For the review brief (plan 04-21):** row 11's three prescribed status calls all show as ambiguous in `git-calls-correlated.txt` because three tool_use entries share the arguments; only the injection ordinal tells them apart. The row 12 refresh is the first filed run of a second resumed session.
- Every harness-authored string (row setup texts, section text) must stay free of the verdict vocabulary; the new row-setup test covers the registry only.

## Self-Check: PASSED

- Created files exist: the three top-level files and both row folders under `tests/evidence/rerun-2026-11-06-claude-sonnet-5-5-wave-c/`, and this summary.
- Commits 991cf6b and af6da17 are ancestors of HEAD (`git rev-list --count 1725a7b..HEAD` was 2 before this summary).
- `commits: 2` measured from the base 1725a7b24741c1f992fa1215e8afaa79d3beb3ec.
