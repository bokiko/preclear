---
phase: 04-full-matrix-row-7-and-review
plan: 22
subsystem: testing
tags: [harness, row7-review, unfenced-checkpoint, review-parts, frozen-folder-exception, gap-closure]
requires:
  - phase: 04-21
    provides: the filed Codex review of the baseline and the verification report that named the row 7 review gap
provides:
  - outside_fences in pc_row1.py, the lines of a reply outside every fence with the one fence rule of fenced_blocks
  - parse_full_trace and unfenced_reading in pc_review.py, a lower-confidence reading of a checkpoint printed as plain markdown
  - review parts with a preface and a quoted Review record note (--note FILE) in pc_baseline.py and pc_review.py
  - the one narrow exception that lets row7-review add a new part to the triple folder
  - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review-part-2.md, the table that lists attempt 3's two unfenced entries
affects: []
key-files:
  created:
    - tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review-part-2.md
  modified:
    - tests/harness/pc_row1.py
    - tests/harness/pc_review.py
    - tests/harness/pc_baseline.py
    - tests/harness/test_review.py
    - tests/harness/README.md
key-decisions:
  - "D-06: the pairings of row7-review.md are rejected. The owner's answer at the filing of the Codex review took the proposed default, which follows the row 7 line of that review (evidence claim overstated; the older table does not validate this run)"
  - "Corrected pointer: the Codex review is filed at tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md; the first part's introduction still names a file of the triple that does not exist and stays as filed"
  - "The candidate rule was not tuned: a bare name is not the same token as a longer path, so the two unfenced entries list no candidate"
metrics:
  duration: not recorded by this executor (no start time was captured)
  completed: 2026-11-11
status: complete
requirements-completed: [HARN-12, RERUN-01]
actuals:
  tokens: 21800
  tasks: 3
  commits: 3
commits: 3
plan_head_before: dbfe28cb2ea7c1f8c3c2950db0c4880bc7b772e3
plan_head_after: 9c028c9e8bfe80a500af55cb6d64739af33da152
---

# Phase 4 Plan 22: The Unfenced Row 7 Checkpoint in the Review Table Summary

**The row 7 review table of the triple now lists attempt 3's two Do-not-redo entries under the word unfenced, in one added file, `row7-review-part-2.md`. The first part is untouched. The part records that the pairings are rejected and where the Codex review is filed. No model was started, nothing was spent, and nothing was pushed or tagged.**

## What was built

- **Task 1 (commit `6e687f2`, tracer):**
  - `outside_fences` in `pc_row1.py` returns the lines of a reply that lie outside every closed fence. An unclosed fence runs to the end and is not outside. A test pins that it and `fenced_blocks` use one rule.
  - `parse_full_trace` in `pc_review.py` reads the filed full trace in the exact shape `render_full_trace` writes: the title line, one `Calls N` line, calls numbered 1, 2, 3 and so on, N at most 512. A forged call heading inside model text changes the count or the numbering, and the whole file is refused with a fixed message that echoes nothing.
  - `unfenced_reading` takes the reply after the first `## Final reply` line of the filed short trace. A fenced block that holds both headings (even one over the size bound or with a NUL byte) always wins and nothing is read. Otherwise both heading lines must stand outside the fences, and the entries of the section are paired with the calls by the unchanged whole-token rule.
  - `Attempt` has two new fields with defaults. A filed attempt whose marker is `NO-PRINTED-CHECKPOINT` prints the unfenced lines. `row7_attempts` reads the two filed traces for such an attempt, and an absent, oversized or damaged trace is printed as one fixed line.
- **Task 2 (commit `a5c5ca8`):**
  - A part numbered 2 or later starts with `part: N`, `earlier parts:` and one fixed sentence that the earlier parts are unchanged and the latest part is the complete table.
  - `--note FILE` quotes at most 12 lines under `## Review record`. The note must be a plain file of at most 4096 bytes outside the evidence tree, valid UTF-8, no NUL, at least one line. Anything else is refused with exit 2 before anything is staged. The leak gate refuses a path-shaped note line with exit 14.
  - The introduction of every table built from now on no longer points to a Codex review file of the triple.
  - `file_review` and `read_note` share one source reader (`_read_source`). The `file_review` messages and limits are unchanged and its tests still hold.
  - The README paragraphs describe the unfenced reading, the part preface, the note and the exception.
- **Task 3 (commit `9c028c9`):** the part was rehearsed on a scratch copy, read in full, and only then added to the real folder with `pc_baseline.py row7-review --note`. The real file equals the rehearsed one (`cmp`).

## Decision D-06 and the corrected pointer

- **Decision D-06 (reviewer confirmation of the row 7 pairings):** the pairings of `row7-review.md` are rejected. The owner's answer `go so it ur self`, given at the filing of the Codex review of the baseline, took the proposed default, and that default follows the row 7 line of the Codex review. That line holds the words `evidence claim overstated` and `the older table does not validate this run`. The answer reached this plan through the orchestrator's dispatch. It was not re-asked, and the plan did not verify it against the owner. The part states it in its Review record, naming the owner as `the owner`.
- **Corrected pointer:** the Codex review is filed at `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md`. The introduction of the first part, `row7-review.md`, still names a Codex review file of the triple folder that does not exist. It stays as filed, because it is never edited, and the Review record of part 2 says so.

## What part 2 shows for attempt 3

- Attempts 1 and 2 are the same lines as in the first part (compared with `cmp`).
- Attempt 3 keeps `chain marker: NO-PRINTED-CHECKPOINT` and gains these lines:

```
unfenced checkpoint: found
unfenced source: the final reply in s2-preclear-trace.md outside any fenced block, and the calls in s2-preclear-full-trace.md
unfenced confidence: lower than a fenced block, which has a closing fence; text after the last bullet of an unfenced section joins its last entry
unfenced match rule: whole tokens as for a fenced entry, so a bare name in an entry is not the same token as a longer path in a call
unfenced entries: 2
unfenced calls read: 10
unfenced results not searched: 2 (the filed trace holds Read, Glob and Grep results by length only)
unfenced assembly calls: 1
```

- The table headed `Unfenced entry` has `| 1 | 0 | UNSUPPORTED |` and `| 2 | 0 | UNSUPPORTED |`.
- **Candidate counts: 0 and 0.** The first entry names `widget_export.py` and the calls name `src/widget_export.py`. The second entry names two memory files and the Write calls name them by a longer path. Under the unchanged whole-token rule these are different tokens. This is exactly what the plan's prototype predicted, so the rule was not tuned and the part was added. Whether any entry is backed by what the model really checked stays a human judgement for Codex and the owner.

## Exception added to the harness (disclosure for FA-1 and FA-2)

`row7-review` refuses a frozen folder, as before, with one exception. The folder named `rerun-2026-11-09-claude-sonnet-5-5-triple` takes a new part when all three conditions hold:

1. the folder name is the one entry of `REVIEW_PART_FOLDERS`;
2. `row7-review.md` already exists in it;
3. the write only adds a file: `_add_flat_files` and `promote_into` create exclusively and never overwrite.

`close`, `finalize` and `file-review` still refuse every frozen folder, the triple included. `row7-review` still refuses the eleven other frozen names and refuses the triple when no first table exists. A scratch-repository test pins each of these. No test writes a committed evidence folder, and no test calls the command on the committed triple.

## Remaining limits

- **Attempt 3 still has no third stage.** The fresh-resume session never ran, because the harness found no fenced checkpoint to build its prompt from. Producing one needs a paid run, which this plan does not make. The part repeats the filed chain marker. This is a remaining limit of the triple, not a closed one.
- **Read, Glob and Grep results are not searched.** The unfenced reading uses the filed sanitized trace, which holds those results by length only. A fenced attempt's candidates came from the raw stream, so the unfenced reading can pair less. The part states the count of results not searched.
- **The unfenced reading is lower confidence.** There is no closing fence, so text after the last bullet joins the last entry.
- **No reviewer has judged the two unfenced entries.** The part says so.

## Verification results

Single-file runs by this executor. The whole-suite count is the orchestrator's gate.

| File | Tests before | Tests after | Result |
| --- | --- | --- | --- |
| test_review.py | 103 | 144 | OK |
| test_baseline.py | 102 | 102 | OK |
| test_readme.py | 41 | 41 | OK |
| test_imports.py | 17 | 17 | OK |
| test_boundaries.py | 62 | 62 | OK |
| test_frozen_baseline.py | 30 | 30 | OK |

| Check over the triple folder | Result |
| --- | --- |
| difference from commit 45d444d | exactly one added file, the part |
| first part `row7-review.md` against the committed bytes | identical |
| real part against the rehearsed part | `cmp` equal |
| check-words | 85 files scanned, 0 hits |
| leak gate | 173 files, 0 findings |
| gitleaks | exit 0 |
| other frozen paths and tests/harness after the commits | clean |
| attribution trailers in the three commits | 0 |

Suite count: 2405 (the orchestrator's wave 22 gate on head 47e3656: selftest and unit suite both 2405 OK, skipped=3; hooks 29/0, frozen paths unchanged apart from the one added part file, trailers 0, leak gate 0 after an untracked bytecode cache was removed, gitleaks 0)

## Deviations from Plan

None - plan executed as written. Two notes that are not deviations:

- The existing part-two test now compares from the first `## Attempt` line on, as flagged assumption FA-6 says, and still checks that earlier files are byte identical.
- The existing frozen-folder test gained the four wave folders. It never names the triple.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. The new `--note` input and the frozen-folder exception are the surfaces of T-04-112 and T-04-113, and both are covered by tests.

## Self-Check: PASSED

- `tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review-part-2.md` exists.
- Commits `6e687f2`, `a5c5ca8` and `9c028c9` are ancestors of HEAD.
- `outside_fences`, `unfenced_reading` and `REVIEW_PART_FOLDERS` are present in the tree.
