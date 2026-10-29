---
phase: 03-walking-skeleton-row-1
plan: 06
subsystem: testing
tags: [paid-run, row-1, baseline-evidence, usage, cost-of-one-row, claude-sonnet-5-5]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_matrix driver, preflight, row 1 pipeline, checks, evidence filing, comparer, frozen-tree pins"
provides:
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5: the first real row 1 baseline, sanitized and leak-gated, verdict PENDING"
  - "The measured cost of one row: 0.2723 USD by the harness row total (see the cumulative question below for a possible 0.3210)"
affects: [phase-04]

status: gaps
actuals:
  tokens: 18600
  tasks: 3
  commits: 1
plan_head_before: baf8aa575212208b958bd10e5fc12048edbf4a73
plan_head_after: 663766964d58c6680e33d79051bf690f73c8b737

tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/README.md
    - tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/ (64 further files, written by the harness)
  modified: []

key-decisions:
  - "The paid command ran once on the 2.1.310 build with --budget 2.00 after bokiko's own go; no retry, no --authorize-retry"
  - "The six selftest failures were not fixed here: the plan forbids edits under tests/harness, so they go back to the orchestrator as a plan revision"

metrics:
  duration: "about 30 minutes, 20 minutes of it the selftest and the paid run"
  completed: 2026-10-29
---

# Phase 3 Plan 06: The Row 1 Baseline Run Summary

**One real row 1 run (three stages, two sessions) on Claude Code 2.1.310 and claude-sonnet-5-5 exited 0 and was filed as `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5`; the harness row total is 0.2723 USD of the 2.00 cap, but the zero-token selftest is red with the folder present (six failures, two causes, both in tests that assume no run exists).**

## The paid run

- Command: the pinned `pc_matrix.py --row row1-wrong-binding --claude <2.1.310 build> --budget 2.00`, run exactly once, from the worktree root, after bokiko's own `go` in the main conversation. Exit code 0. The build was found next to the PATH build (2.1.312, refused by the version gate) by a listing and a `--version` check; its path is not recorded in any file.
- Preflight before the run printed `OK: preflight passed for Claude Code 2.1.310`; the harness tree was clean and the destination did not exist.
- Printed lines: all three stages `success`, `filed: rerun-2026-10-29-claude-sonnet-5-5, 65 file(s)`, `row total: 0.27231170000000002 USD`.
- No stage ran twice, `--authorize-retry` was not used, nothing was pushed, no hook was skipped.

## Measured cost of one row (from usage.txt)

| Stage | Session | Turns | Input | Output | Cache creation | Cache read | Call cost (USD) | Reported total (USD) | Wall (s) |
|---|---|---|---|---|---|---|---|---|---|
| s1 work turn | e125001c | 5 | 6 | 854 | 8704 | 53425 | 0.0487105 | 0.0487105 | 20.0 |
| s2 /preclear (resume of s1) | e125001c | 20 | 22 | 5632 | 16672 | 353805 | 0.1584325 | 0.2071430 | 61.6 |
| s3 fresh resume | b7eb866d | 6 | 6 | 2222 | 9394 | 53607 | 0.0651687 | 0.0651687 | 19.5 |

- **Row total (usage.txt): 0.27231170000000002 USD, the measured cost of one row by the harness's own accounting (the s2 reported total plus the s3 total). Phase 4's spend is confirmed from this figure, with the caveat below.** Run total is the same number. The caps (0.30, 1.30, 0.40) were far from reached; the 2.00 worst case is about 7 times the measurement.
- **Open question on the number, recorded as measured and not judged.** The harness treats the stream's `total_cost_usd` on the resumed s2 call as cumulative (it subtracts s1's 0.0487 to get a call cost of 0.1584 and counts s1 inside the s2 chain). The filed token counts point the other way: priced at one fixed rate card, s1 and s3 (both fresh sessions, so the reported total is their own cost) come out at 0.79 and 0.77 of that card, while s2 comes out at 0.82 if its reported 0.2071 is its own cost and 0.63 if only 0.1584 is. If the reported total on a resumed call is that call's own cost, the real row cost is 0.0487 + 0.2071 + 0.0652 = 0.3210 USD, not 0.2723. This is an inference from token counts; the filed data cannot settle it, and it should be decided before Phase 4's matrix spend is projected from this row (it moves the figure by about 18 percent, which the 2.00 row cap and the 7-times headroom absorb either way).

## What the real run recorded (counts and ids)

- Init manifest assertions: all twelve per stage are yes for s1, s2 and s3. Isolation mode strict; permission mode default; model claude-sonnet-5-5; Claude Code 2.1.310 in every stage; memory path as set; 20 skills including preclear; zero MCP servers; instruction audit user=0 in every stage.
- Write boundary: snapshot paths outside the approved roots 0, executed write-tool paths outside the roots 0, Bash commands seen 6 with 0 outside path tokens and no write-capable programs, default memory folder absent.
- Git read-only: four states identical (same head, branch main, 0 staged); mutations total 0.
- Helper calls: s1 attempted 0; s2 attempted 4, executed 1, denied 0, compound refusals 3; s3 attempted 0. Correlated yes in all stages.
- Permission denials: s1 0, s2 6 (ids listed in mechanical-checks.md), s3 0.
- Ledger digests: ledger A, ledger B, binding, ledger roots and checkpoint log all unchanged.
- s3 read-only facts: ran; the resume line was extractable (resume-line.txt, one line); s3 session differs from s1; 0 helper calls, 0 denials, 0 git mutations.
- Checkpoint bytes: 2623 of the 4096 cap, no section over its own cap.
- Status result: status holds the s1 prefix and names ledger B (yes, yes); `status-begins-with-session` is no.

## The three unobserved questions

1. Does a resumed 2.1.310 session fire the instruction-load hook again? Yes in this run: s2 logged project entries 2 (s1 had 1, s3 had 1), and the resumed stage's hook assertions are marked yes (hook), not "not asserted on resume".
2. Does `--max-budget-usd` count a resumed session's cumulative cost? Not observable: no stage came near its cap. The related question of whether `total_cost_usd` is cumulative on resume is raised above and is not settled by the filed data.
3. Which result subtype does a limit hit have? Not observed: all three stages ended `success`.

## Checks run after the run

- Comparer against the committed row: exit 0, `old unchanged: yes`, `new unchanged: yes` (198 report lines, structural differences listed, none judged).
- Leak gate over the new folder: 65 files, 0 findings; over all of tests/evidence: 1311 files, 0 findings. gitleaks over the new folder and over tests/evidence: clean.
- Row README ends with exactly `Reviewer verdict: PENDING`; provenance files non-empty; no verdict word in the harness-authored files; no raw capture filed.
- Frozen paths: no difference against the base commit for SKILL.md, references, tests/fixtures and the publication evidence; SKILL.md is 11,994 bytes (cap 12,000); every file added outside .planning lies under tests/harness or the new folder.
- No attribution trailer in any commit message (the hook pattern list matches 0 lines).

## Deviations from Plan

### Open issue

**1. [Gate not green] The selftest fails with the new folder present (exit 1, 1117 tests, 6 failures, 3 skipped)**
- **Found during:** Task 3 step 6.
- **Cause 1, one test:** `test_allowlist.CorpusScopeTests.test_the_scoped_loader_equals_the_unscoped_walk_restricted_to_the_publication_folder` walks every `*full-trace.md` under tests/evidence and expects them all to sit in the publication folder. The new folder holds three (s1, s2, s3 full traces) that the scoped loader correctly ignores, so the unscoped walk is longer. The scoping itself works; the test's expectation does not allow a rerun folder.
- **Cause 2, five tests:** the five `test_matrix_cli.DryRunTests` cases that call the dry run without an injected destination exit 17 because the real destination name for today's UTC date (`rerun-2026-10-29-claude-sonnet-5-5`) now exists, which is the harness working as designed (a taken name is refused). They would pass again on another UTC date; the real dry run exits 17 today for the same reason.
- **Why not fixed here:** the plan forbids any edit under tests/harness and tells the executor to return code changes as a plan revision. Nothing was edited, skipped or retried.
- **Suggested revision:** make the corpus-scope test restrict its walk to the publication prefix or accept `rerun-*` folders, and have the DryRunTests inject a destination date or a temporary evidence root so they cannot depend on what is committed.

### Auto-fixed Issues

None. The plan was otherwise executed as written; Task 1 and Task 2 were completed before this instance started (see the checkpoint resolution).

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None. The only new files are the harness-written evidence folder, which passed the sanitizer, the leak gate and gitleaks.

## Commits

- 663766964d58c6680e33d79051bf690f73c8b737: test(03-06): file the row 1 baseline evidence

## Self-Check: PASSED (evidence and commit exist); the plan's selftest gate is FAILED as described above
