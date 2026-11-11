---
phase: 04-full-matrix-row-7-and-review
plan: 21
subsystem: testing
tags: [harness, readme, review-filing, verdict-lines, frozen-digest, changelog]
requires:
  - phase: 04-20
    provides: the baseline folder with every row README ending in the pending reviewer line, and its frozen digest
provides:
  - tests/harness/README.md as the stranger's entry point, with the measured cost block tied to the evidence by a test
  - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md, the Codex answer filed as pasted
  - a Codex verdict line on each of the 21 outcome folders of the baseline, none left pending
  - the baseline's frozen digest pinned in tests/harness/test_frozen_baseline.py
  - one CHANGELOG entry under Unreleased naming the harness and the baseline
affects: []
key-files:
  created:
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md
  modified:
    - tests/harness/README.md
    - tests/harness/test_readme.py
    - tests/acceptance.md
    - tests/harness/test_frozen_baseline.py
    - CHANGELOG.md
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/*/README.md
key-decisions:
  - "bokiko's word at the Task 2 checkpoint was file-only: the review is filed and the verdict lines are in place, and the reference was not moved"
  - "No commit 3: the default reference of the comparer stays the publication folder"
  - "The consultation date is the day bokiko pasted the answer; the Codex model was not stated and the filed header says so"
metrics:
  duration: Task 3 about 35 minutes (the filing, the 21 verdict lines, the pin, the changelog, this summary)
  completed: 2026-11-11
status: complete
requirements-completed: [RERUN-04, RERUN-05]
actuals:
  tokens: 10900
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 2be6afa578d0dbe2959ae86228f0922f0e8cd2c6
plan_head_after: 6fd685d1387618e6a1c612d1f62c04ac180bda31
---

# Phase 4 Plan 21: README, Codex Review Filing and Baseline Pin Summary

**The README is the stranger's entry point, the Codex review of the new baseline is filed as pasted, each of the 21 outcome folders carries Codex's line as its closing verdict line, the baseline's frozen digest is pinned, and the reference was not moved because bokiko's word was `file-only`. Nothing was pushed or tagged by this plan.**

## What was done

- **Task 1 (commit `deaeecc`):** the stranger-facing README content with the measured cost inside one marked block, the pointer paragraph in `tests/acceptance.md`, and the README tests that read the cost figures from the filed evidence.
- **Task 2:** the checkpoint. bokiko pasted the Codex answer (21 lines, one per layout and row). His word was `go so it ur self`, which under this project's convention accepts the recommended defaults, so the word is `file-only`. He did not state the Codex model.
- **Task 3, filing (commit `6ca9b14`):**
  - `file-review` filed `codex-review.md` (3557 bytes): two header lines, then his pasted text byte for byte, including the closing "Worked for" line.
  - `record-verdict` ran once per folder, one at a time, in the `--list` order: plain-memory, hub-memory, bound-ledger, then rows 1, 2, 3a, 3b, 3c, 4a, 4b, 5a, 5b, 6, 7, 8a, 8b, 8c, 9, 10, 11, 12. Each run printed `recorded: 1 line` with 107 to 241 bytes added. The text of each line is Codex's wording after the leading folder name, verbatim.
  - The frozen digest after the edits still equals the value recorded by plan 04-20 and is pinned in `PINNED_BASELINES`.
- **Task 3, changelog (commit `6fd685d`):** one entry under Unreleased, Added, naming the harness and the baseline folder and saying a Codex review is recorded in its `codex-review.md`. It contains no acceptance wording. Nothing else in the file changed.

## Folders whose verdict line was replaced

All 21 outcome folders of `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5`: `plain-memory`, `hub-memory`, `bound-ledger`, `row1-wrong-binding`, `row2-double-conflict`, `row3a-missing-executable`, `row3b-denied-helper-write`, `row3c-unbound-fallback-none`, `row4a-unknown-backend`, `row4b-conflicting-blocks`, `row5a-no-memory`, `row5b-disabled-memory`, `row6-readonly-plan`, `row7-all-destinations-denied`, `row8a-non-git`, `row8b-detached-head`, `row8c-unborn-branch`, `row9-linked-worktree`, `row10-large-status`, `row11-concurrent-change`, `row12-frozen-handoff`.

Folders left pending: none. A search for the pending line over the 21 README files finds no hit, and 21 files end with `(see codex-review.md)`.

## Pinned digest

`1e4f68bbf7f87c8b57df31414e80d6f2bccc2bee3a336769a71f1efa993dc805`, the frozen digest of `rerun-2026-11-11-claude-sonnet-5-5`. It equals the value recorded in the summary of plan 04-20, computed before the review was filed, after it was filed and again at the final verify. The publication folder's tree digest is unchanged (`268818206a76c809ce832ba245e5bda648b7f48a46a56c6d9da8b08ef2aea117`), and no path under SKILL.md, references, tests/fixtures, the publication folder or the first baseline differs from the Phase 4 base commit.

## The swap

No swap was made and there is no commit 3. The word was `file-only`, and the plan makes the reference swap only for `file-and-swap`. The comparer default is still the publication folder. The review is filed as Codex's own words; the harness and this plan state no acceptance.

## Notes on what the filing records

- **Codex model:** not stated by bokiko; the filed header line says so.
- **Consultation date:** 2026-11-11, the day the answer was pasted into the conversation.
- **Nothing pushed or tagged:** the commits made after the push of plan 04-20 (the baseline filing, the README commit, the review filing, the changelog entry and the commit of this summary) are local. Pushing them is bokiko's next step and the orchestrator pushes on his standing word.

## Verification results

Run by this executor, targeted only (the orchestrator runs the whole-suite gate):

| Check | Result |
| --- | --- |
| `pc_baseline.frozen_digest` of the baseline | equals the pinned value |
| `test_frozen_baseline.py` | 30 tests, OK |
| `test_readme.py` | 41 tests, OK |
| `check-words` on the baseline folder | 487 files scanned, 0 hits |
| leak gate over the baseline folder | 1203 files, 0 findings |
| gitleaks over the baseline folder | exit 0 |
| frozen-path diff against the Phase 4 base commit | empty |
| SKILL.md size | 11994 bytes, under the 12000 cap |
| attribution trailers in the phase's commit messages | 0 |
| working tree under tests/ | clean |

Suite count: 2347 (the 04-20 figure, not re-measured by this executor; the orchestrator gate re-measures it)

## Deviations from Plan

**1. [Rule 3 - Blocking] The leak gate refused the first filing.**
- **Found during:** Task 3, step 2.
- **Issue:** `file-review` exited 14 (deny-list). The two header lines written from bokiko's words contained his name, which is on the local deny list. The pasted Codex text had no finding; the same scan over each line pointed only at lines 1 and 2.
- **Fix:** the orchestrator restaged the file with the two header lines rewritten without the name ("Consultation date: 2026-11-11 (the answer was pasted into the conversation on this UTC day)" and "Codex model: not stated"). Lines 3 to 24 were untouched. The second attempt filed cleanly. The refusal was returned to the orchestrator first, as the plan says.
- **Commit:** `6ca9b14`.

**2. [Rule 1 - Bug] The pinned-baseline tests assumed the first baseline only.**
- **Found during:** Task 3, step 3.
- **Issue:** the table test required exactly one pinned folder "until plan 04-21", compared the tree digest to the pin and required the folder to be in the harness's frozen list. For a baseline that holds filed verdict lines and `codex-review.md`, only the frozen digest equals the pin, and adding the folder to the frozen list would change `pc_baseline.py`, which this plan does not list.
- **Fix:** in `test_frozen_baseline.py` only: both baselines are expected in the table, the tree digest is checked for the first baseline only, the frozen digest is checked for both, and the "is frozen" assertion stays for the first baseline. The first baseline's pin did not move.
- **Commit:** `6ca9b14`.

**3. [Plan input] bokiko's answer accepted the recommended defaults.** He said `go so it ur self` instead of naming the word, the model and the row 7 pairings; under the project's convention a plain go accepts the recommended defaults, so the word is `file-only`. The row 7 pairings were not decided by this plan: the filed review holds one line per layout and row and no pairing table, and nothing here acts on them. The model line is the one fact he did not give, and it is filed as "not stated".

## Known Stubs

None.

## Threat Flags

None. The plan filed text the leak gate had scanned, edited one closing line per README through the harness and added no endpoint, path or secret.

## Self-Check: PASSED

- `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md` exists.
- Commits `deaeecc`, `6ca9b14` and `6fd685d` are ancestors of HEAD.
- The pinned digest is present in `tests/harness/test_frozen_baseline.py` and equals the computed frozen digest.
- 21 of 21 outcome READMEs end with `(see codex-review.md)`; none ends with the pending line.
