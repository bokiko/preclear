---
phase: 03-walking-skeleton-row-1
plan: 12
subsystem: testing
tags: [harn-09, write-boundary, awk-reader, working-folder, certain-cd, attached-options, sort-gate, gap-closure, zero-token]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "the open-world write rule, the shell grammar pre-pass, the working-folder tally, the awk statement reader, the attached-option candidates and the corpus test of plans 03-07 to 03-11; Harn09ReproofTests with its twelve seeded failures"
provides:
  - "an awk program with a double quote after a slash or a hash (the blanker may have read a quote inside a regular expression or a comment as a string) is also read as raw program text by the keyword test and the print redirect test; a print statement whose parentheses never close is read again with the depth ignored; the literal scan of such a program also reads the text between every two consecutive double quotes (fourth-pass CR-01)"
  - "the working folder moves on a cd only when the cd is certain to run in the main shell and certain to succeed (next separator is a double ampersand, previous is not a double bar, pipe or pipe with ampersand, the and-or list does not end with a single ampersand, no reserved construct or parenthesis group opened earlier, the target is inside a root and is a folder when judged); every other literal cd leaves the folder strict so a later dot-dot word is an escape (CR-02)"
  - "a cd or env -C to an expansion leaves the folder loose: no escape flag, and a dot-dot word is resolved against the project (the start folder); cd to the output of git rev-parse --show-toplevel followed by a memory-folder write is zero escapes (WR-01)"
  - "the text after each option letter of the leading run of letters of a short option is judged, with the four-letter rule kept for a slash or tilde start; the sort gate refuses an o inside a cluster (CR-03)"
  - "pc_allowlist.split_compound_connected returns each part with the separator that follows it; split_compound is its parts"

key-files:
  created: []
  modified:
    - tests/harness/pc_checks.py
    - tests/harness/pc_allowlist.py
    - tests/harness/test_checks.py
    - tests/harness/test_evidence.py
    - tests/harness/README.md

key-decisions:
  - "The raw awk view is read only when the program is suspect (a double quote stands after a slash or hash still visible in the blanked text); read unconditionally it would turn the harmless 03-11 forms (print of a string holding an arrow, print of the text system(x)) into escapes"
  - "The working folder has three states: a real path (known), None (strict, every dot-dot word escapes) and a loose marker (a dot-dot word is resolved against the start folder); the escaped-cd flag stays a separate third thing"
  - "The pre-pass leaves a marker part (a word with a dollar sign) between two separators for each unquoted parenthesis; the unit reader turns it, a reserved lead or standalone word and a for, select or case header into a compound flag that stays set for the rest of the unit"
  - "A relative literal cd made while the folder is unknown keeps that unknown state; an absolute literal cd inside a root that is certain and exists makes the folder known again"
  - "The cluster pattern constant of 03-11 is removed; the per-letter rule contains its cases"

metrics:
  duration: "under two hours"
  completed: 2026-10-29

status: complete
actuals:
  tokens: 42000
  tasks: 1
  commits: 2
plan_head_before: 6d3fe5684cd1c27ddd26da308cfce55d78f8dac0
plan_head_after: 7652b40569ec9db4ec75922e90cb7f816de6284a
---

# Phase 3 Plan 12: Awk raw view, certain cd, expansion cd and cluster values Summary

The write rule now reads an awk program as raw text when a quote may hide a statement, moves the working folder only on a cd that is certain to run in the main shell and succeed, resolves a dot-dot word after an expansion cd against the project, and judges the text after every option letter of a short-option cluster; the committed corpus still gives zero escapes and zero mutations.

## Commits

| Step | Hash | Subject |
|------|------|---------|
| red | 7856600 | test(03-12): add failing tests for the awk raw view, the certain cd, the expansion cd and the cluster value |
| green | 7652b40 | feat(03-12): read the raw awk program when a quote may hide, move the folder only on a certain cd, resolve an expansion cd against the project and judge every cluster value |

## Test counts

| | test_checks.py | whole suite (selftest) |
|---|---|---|
| before (HEAD 6d3fe56) | 189 | 1289 |
| after | 205 | 1305 (skipped 3, as before) |

Sixteen tests added: AwkRawProgramTests 4, WorkingFolderCertaintyTests 7, AttachedClusterValueTests 4 (all in test_checks.py), plus one README phrase test in test_evidence.py. The new rows in OpenWorldRunTests are added to its two existing list tests, so they add no test. The suite passes on the system Python 3.9.6 and through the bash 3.2 shim.

## Red step (what failed and what already passed at the head)

- AwkRawProgramTests: 3 of 4 failed on an assertion (zero escapes where one was expected, an unlisted program). The harmless-forms test passed at the head, as the plan marks.
- WorkingFolderCertaintyTests: 3 failures and 1 error of 7. The error is the splitter test: AttributeError on the missing split_compound_connected (the stated reason, not an import error). The failures: the strict table (zero escapes where one was expected), the loose table and the two-states test (an escape on a cd to an expansion). The still-one table, the certain table and the per-call boundary pair passed at the head.
- AttachedClusterValueTests: 3 of 4 failed (the cluster values, the sort tilde value, the sort listing); the zero table passed at the head.
- WriteEscapeDotDotTests (set-up change only): all its tests passed before and after.
- OpenWorldRunTests: 2 of 3 failed (the new escaping rows returned 0 instead of 11; the new harmless cd-to-substitution row returned 11 instead of 0).
- ReadmeTests: the new phrase test failed (phrase missing).

## Corpus numbers (read from disk, no edit to the corpus tests)

35 full traces, 348 Bash calls parsed, 231 judged, zero write escapes and zero git mutations over the 231; 13 calls hold ../auto-memory (9 judged or not run), all zero; the refused temporary-folder control (publication row10 s3 call 5) is still an escape through the mktemp and the rm. The suspect test did not need narrowing: no harmless committed program was caught by the raw-view over-count.

## Final gate

| Gate | Result |
|------|--------|
| tests/harness/selftest | "0 model calls" banner, Ran 1305 tests, OK (skipped=3) |
| system Python 3.9 unittest discover over test_*.py | Ran 1305 tests, OK (skipped=3) |
| pc_leakgate scan of tests/harness | 71 files, 0 findings |
| gitleaks dir tests/harness | exit 0 |
| frozen-path diff against 56e155c (SKILL.md, references, tests/fixtures, publication evidence) | empty |
| diff of tests/evidence from the plan base | empty |
| read-only comparer over the two evidence trees | exit 0, "old unchanged: yes", "new unchanged: yes" |
| scripts/test-hooks.sh | 29 PASS, 0 FAIL |
| pc_matrix.py --list | row1-wrong-binding shown as implemented (no dry run made) |
| files changed outside the plan list (excluding .planning) | none |

## Findings closed

| Finding | Closed by |
|---------|-----------|
| CR-01 (awk raw view) | _awk_suspect, _awk_views, the depth-ignoring fallback, _quote_pairs; eleven escaping forms are exactly one escape under awk, directly and four of them at run level; harmless string forms stay read-only and unlisted; the named over-count is one escape and is in the README |
| CR-02 (working-folder certainty) | split_compound_connected, the pre-pass marker, the compound flag, the background-list test, the existence test in _Tally.move; eighteen strict forms are one escape, eleven certain forms are zero |
| CR-03 (attached cluster values) | per-letter _attached_candidates with the four-letter rule for a slash or tilde, _SORT_CLUSTER in the sort gate; tar, cp and sort forms are one escape with and without env |
| WR-01 (loose folder) | the loose marker; a cd to an expansion no longer sets the escape flag and a dot-dot word resolves against the project; the call boundary is tested and documented |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in the plan's test table] A certain-cd form that cannot be zero**
- **Found during:** Task 1, green step
- **Issue:** the table for certain cd forms listed `mkdir y && cd sub && mkdir ../z; true; cd sub && mkdir ../x` as zero. The first cd moves the folder to sub, so the second `cd sub` names a folder that does not exist (sub inside sub); in a real shell that cd fails and the later mkdir does not run. The rule reads the missing folder as unknown, so the form is one escape (strictly more conservative than the head, where it was zero).
- **Fix:** the form in WorkingFolderCertaintyTests.CERTAIN became `mkdir y && cd sub && mkdir ../z; true; cd .. && cd sub && mkdir ../x`, which keeps the intent (certain cds around a semicolon-separated true) and is zero. No rule was changed to make the plan's form pass.
- **Files modified:** tests/harness/test_checks.py
- **Commit:** 7652b40 (the red commit carried the original form)

**2. [Set-up change named by the plan] WriteEscapeDotDotTests seeds a sub folder**
- WriteEscapeDotDotTests got a setUp that makes a sub folder in its project (FA-6). No assertion changed. No run-level row needed a folder seeded: the existing row `cd ../auto-memory && mkdir -p sub` still returns 0 because the rig makes the memory folder at set-up.

### Conservative cases met in practice

- The raw-view over-count: a regular expression, a division or a comment before a string literal that holds a greater-than, a pipe or a call word counts (`awk '/x/ {print "a -> b"}' <outside file>` is one escape). The corpus holds no such program.
- A cd followed by a semicolon, a newline or a pipe now leaves the folder unknown, so a later dot-dot word escapes even when the cd would have run; the corpus holds no such judged command.
- A cd inside a background list, an if, loop or brace body, or after a parenthesis group reads as unknown.
- A `||` after a certain cd's list is not treated as uncertain (the plan's five conditions do not include it), so `false && cd sub && true || mkdir ../x` still reads the folder as sub; this is a shape for Phase 4 hardening, not a regression.
- The sort cluster over-count: any sort word of a dash, letters and an o (for example `-to` with a separator letter o) is write-capable and listed.

### What a future filed mechanical-checks.md shows differently

More awk parts listed as write-capable (suspect programs whose raw text holds a redirect, call or pipe), a sort part listed when its cluster holds an o, and a mkdir or redirect through a dot-dot path after a cd to a substitution no longer counted as an escape. A mkdir or redirect through a dot-dot path after a semicolon, pipeline, subshell or missing-folder cd now counts.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path, file access or schema; the change only decides which commands count as write escapes, and the rule reads (os.path.isdir is a read).

## Dispositions and residual limits

CR-01, CR-02, CR-03 and WR-01 of the fourth pass are closed by this plan. pc_allowlist.py was edited (one new function, split_compound delegating to it); test_allowlist.py is unchanged and passes. split_compound returns the same output for every input (a test compares it with the parts of the connected splitter over every command of the new tables).

Residual limits named in the README, the plan and here: a cd to a variable or substitution that stands for a folder outside the project leaves the folder loose, so a later dot-dot word that resolves inside the roots from the project is not an escape (the price of removing the false breach on cd to the output of git rev-parse --show-toplevel); a working folder between Bash calls is not known (each call is judged from the project); a cd target's existence is read when the command is judged, not when it ran; a leading assignment or an awk ENVIRON lookup that holds a place is not read; a redirect target held in a variable; paths built at run time. The snapshot diff and the realpath boundary are the nets behind them.

Deferred, not planned here: WR-02, IN-01 and IN-02 of the fourth pass (to Phase 4 hardening by 03-REVIEW-4-DISPOSITION.md), WR-03 of the third pass, and the deferred items of the earlier reviews.

## Self-Check: PASSED

- tests/harness/pc_checks.py, pc_allowlist.py, test_checks.py, test_evidence.py and README.md: present and changed in 7652b40.
- Commits 7856600 and 7652b40 are ancestors of HEAD.
- No paid run was made; no real claude was started; REQUIREMENTS.md, ROADMAP.md, STATE.md and state.json were not touched.
