---
phase: 03-walking-skeleton-row-1
plan: 08
subsystem: testing
tags: [harn-05, evid-04, harn-09, refile, deny-entries, status-fact, usage-consistency, gap-closure, zero-token]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "the write-escape fact, the guard fact, the run-record breach and the seeds of plan 03-07; the filing, promote and the scripted claude of plans 03-02 to 03-06"
provides:
  - "A refile (or any file_row call) refuses a run whose stage records are not clean, by the live path's rule (CR-01)"
  - "file_row and file_skipped refuse a missing deny list with exit 15; promote raises unless the caller opts out (WR-03)"
  - "The status fact looks for the helper's session line in the first five lines, and the scripted claude returns the two output streams merged in time order (WR-02)"
  - "usage.txt carries cumulative-consistent per stage and a warning line for each no (IN-01)"
  - "mechanical-checks.md lists bash-write-escapes and run-record-changes; the checklist writes number equals the exit rule's (EVID-04, D-09)"
  - "HARN-09 re-proved through the driver at zero tokens: a clean control and eight seeded failures"
  - "The harness README describes all of the above"
affects: [03-verification, REQUIREMENTS.md HARN-09 (orchestrator)]

status: complete
actuals:
  tokens: 11900
  tasks: 3
  commits: 6
plan_head_before: fe89694c63e36be2e9d3adaa2b4faedb0b23c065
plan_head_after: 0375cdd18e6d86b5095014b7580d53483fbb8ee6

tech-stack:
  added: []
  patterns:
    - "A cleanliness rule shared by the live path and the refile path through one function (_unfileable)"
    - "An API that requires a safety input unless the caller opts out by keyword, pinned by a source scan over all callers"

key-files:
  created: []
  modified:
    - tests/harness/pc_evidence.py
    - tests/harness/pc_promote.py
    - tests/harness/pc_checks.py
    - tests/harness/pc_testutil.py
    - tests/harness/test_evidence.py
    - tests/harness/test_promote.py
    - tests/harness/test_checks.py
    - tests/harness/README.md

key-decisions:
  - "A stage record is clean when its problem is the empty string and its evaluation is pass; a record that lacks either key is not clean (fail closed)"
  - "A missing deny list is exit 15 (SCANNER_ERROR) for file_row and file_skipped; promote raises ValueError unless allow_default_deny=True, which only its command line passes"
  - "The key status_begins_with_session and the filed label status-begins-with-session keep their names; the meaning is now the helper's session line among the first five lines"
  - "The scripted claude merges standard error into standard output (time order), because the stub writes its brand line to standard error first"

metrics:
  duration: "about 1.5 hours"
  completed: 2026-10-29
---

# Phase 3 Plan 08: Refile Cleanliness, Deny Entries, Status Fact And HARN-09 Re-proof Summary

**A run the live path refused can no longer be refiled as a baseline, filing needs the sanitizer's deny entries in the API itself, a future baseline records the helper's session line as the fact it is and shows the cost-consistency flag and the two new counters, and HARN-09 is re-proved at zero tokens through the driver for a clean control and eight seeded failures.**

## What each task closed

| Task | Commits | Findings | Result |
|---|---|---|---|
| 1 (tracer) | bc471b3 test, b672c42 feat | CR-01, WR-03 | `_unfileable` refuses unclean stage records (exit 11, nothing created); `file_row` and `file_skipped` return exit 15 on None deny entries; `promote` raises without `allow_default_deny=True` |
| 2 | c571168 test, c2dbd1e feat | WR-02, IN-01 | status question over the first five lines; the fake returns the brand line first; `cumulative-consistent` lines and warnings; two mechanical lines; the checklist writes number includes Bash writes |
| 3 | d53fbbe test, 0375cdd feat | HARN-09 re-proof, README | `Harn09ReproofTests` (clean control plus eight seeded failures); README states every new rule and known limit |

Commits (in order): bc471b3 `test(03-08)` and b672c42 `feat(03-08)` (Task 1); c571168 `test(03-08)` and c2dbd1e `feat(03-08)` (Task 2); d53fbbe `test(03-08)` and 0375cdd `feat(03-08)` (Task 3).

## Test counts

- Before: 1167 tests (OK, 3 skipped), measured at the start on the system Python 3.9.
- After: 1190 tests (OK, 3 skipped) on `tests/harness/selftest` (banner "0 model calls") and on `/usr/bin/python3` 3.9 with `-I -B -m unittest discover`.
- New: 23 (Task 1: `RefileCleanRunTests` 4, `DenyEntriesContractTests` 2, `DenyEntriesRequiredTests` 4; Task 2: `StatusFactTests` 4, `UsageConsistencyTests` 3, `MechanicalFactLineTests` 3; Task 3: `Harn09ReproofTests` 2, README phrase test 1).

## The HARN-09 re-proof (through `matrix.main`, scripted claude, tripwire log empty in every case)

| Case | Seed | Exit | Result |
|---|---|---|---|
| clean control | default stages | 0 | files; `bash-write-escapes: 0`, `run-record-changes: 0`, `status-begins-with-session: yes`, `cumulative-consistent` yes for s1, s2, s3, no warning |
| snapshot-path write | `seed_outside_write` | 11 | breach line, no evidence folder |
| Write-tool path outside | `seed_trace_write` | 11 | breach line, no evidence folder |
| commit in the project | `seed_git_commit` | 11 | breach line, no evidence folder |
| Bash write outside, really written | `seed_bash_outside_write` | 11 | breach line, no evidence folder |
| Bash expansion-form write (`mkdir ~/x`, nothing written) | `seed_bash_outside_write(write_file=False)` | 11 | breach line, no evidence folder |
| planted fsmonitor command | `seed_git_config_plant(kind=fsmonitor)` | 11 | breach line, marker absent, no evidence folder |
| planted clean filter | `seed_git_config_plant(kind=filter)` | 11 | breach line, marker absent, no evidence folder |
| rewritten hook log | `seed_run_record_tamper(kind=hooklog)` | 11 | breach line, no evidence folder |

In every failing case no folder of the rig is printed. HARN-09 in REQUIREMENTS.md is left for the orchestrator.

## What a future baseline files differently from the filed one

The filed rerun folder `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5` is untouched and keeps its earlier values. A run filed from now on differs in three ways:

- `status-begins-with-session` reads yes on the real tool's shape (the stub's brand line first, the session line second); the filed baseline reads no under the earlier first-character rule (the README says so in one sentence).
- `usage.txt` gains one `cumulative-consistent STAGE: VALUE` line per stage before the row total, and one `warning:` line for each stage whose value is no. The stage lines, the row total and the run total keep their form.
- `mechanical-checks.md` lists `bash-write-escapes: N` and `run-record-changes: N` in its Write boundary section, and the checklist's writes line counts the Bash write escapes and names them, so the number a reviewer reads equals the number the exit rule uses.

## Deviations from Plan

None - plan executed as written. Small points worth recording:

- The red step of the "opt-out" promote test fails with a `TypeError` for the unknown keyword `allow_default_deny` (the keyword does not exist before the green step); the other promote tests fail on assertions about the missing behaviour. The source-scan test already passes at the red step because the two production callers already name `deny_entries`; its value is that it fails if a future caller omits it.
- The plan's test 3 of Task 1 edits a stage record in place after the run. The run record guard compares consecutive stored guard files, not live files against the last guard, so such an edit reaches `_unfileable` and is refused with the new fixed line (as the plan intends) and not by the guard.
- `Harn09ReproofTests` passes on its first run, as the plan predicted; the README phrase test is the red step of Task 3.

## Observations for bokiko's decision (not planned, not changed)

- An interrupted run that holds only a clean s1 record can still be refiled as a one-stage row (FA-3): the live path reaches the filing only after s2, but the cleanliness rule does not require s2 to exist.
- Whether the filed baseline needs a note or a refile for its `status-begins-with-session: no` is bokiko's decision (03-VERIFICATION.md); neither was added.
- Reading the unobserved-question-2 paragraph of 03-06-SUMMARY.md confirmed it already says the cumulative-cost question is settled (FA-6); it was not edited.

## Gates run at the end

| Gate | Result |
|---|---|
| `tests/harness/selftest` | OK, "0 model calls", 1190 tests, 3 skipped |
| `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | OK on 3.9, 1190 tests |
| leak gate over `tests/harness` | 71 files, 0 findings |
| gitleaks over `tests/harness` | exit 0 |
| `git diff --name-only 56e155c -- SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20` | empty |
| `git diff --name-only fe89694 HEAD -- tests/evidence` | empty |
| files changed since fe89694 | exactly the eight files in `files_modified` |
| `pc_compare.py` over the publication and the filed rerun folder | `old unchanged: yes`, `new unchanged: yes` |
| `pc_matrix.py --list` | row1-wrong-binding implemented |
| `scripts/test-hooks.sh` | 29 PASS lines |
| commit messages | no attribution trailer; subjects alternate `test(03-08)` and `feat(03-08)` |

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or file access outside the run root; the changes add refusals and documentation.

## Self-Check: PASSED

- The eight modified files exist and are committed; commits bc471b3, b672c42, c571168, c2dbd1e, d53fbbe and 0375cdd are ancestors of HEAD.
