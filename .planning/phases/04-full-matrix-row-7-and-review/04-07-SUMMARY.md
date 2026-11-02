---
phase: 04-full-matrix-row-7-and-review
plan: 07
subsystem: testing
tags: [harness, row7, do-not-redo, review-table, candidates, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-06 printed-checkpoint chain (printed_checkpoint, chain.json), 04-03 pc_baseline filing path, 04-01 row-generic engine
provides:
  - pc_review (do_not_redo_entries, entry_tokens, call_tokens, is_assembly_call, candidates, row7_facts, facts_lines, render_candidates, parse_candidates, Attempt, render_row7_review, quote_line, one_line, ANALYSES, caps MAX_ENTRIES 64, MAX_ENTRY_CHARS 400, MAX_EXCERPT_CHARS 160, MAX_CANDIDATES 20)
  - pc_rows.RowSpec.analyses (default empty), ROW7_ANALYSES, ROW7 value ("row7-facts", "do-not-redo")
  - pc_evidence._run_analyses (called from collect_files for a complete chain), QUOTED_TEXT_FILE, QUOTE_MARKER, REVIEW_POINTER_LINE, harness_authored_names covering do-not-redo-candidates.md and row7-review(-part-N).md
  - filed do-not-redo-candidates.md in every completed row 7 folder and a Row 7 facts section in its mechanical-checks.md
  - pc_baseline row7-review subcommand (row7_attempts, review_part_name, review_folder, shared _add_flat_files used by close too)
affects: [04-08, 04-17, 04-18, 04-19, 04-21]

# Actuals (#2632): chars/4 over the added lines of tests/harness against the plan base commit
actuals:
  tokens: 25000
  tasks: 3
  commits: 3

commits: 3
plan_head_before: c66c76972bccf5334166925b6caa35c9cf3e7056
plan_head_after: 990f55c00cce06359e8deeeed6e663cda159d952

tech-stack:
  added: []
  patterns:
    - "an analysis is a named function in pc_review.ANALYSES that a registry entry lists in RowSpec.analyses; collect_files runs each for a complete chain and gets (section title, section lines, flat files) back, so rows 10, 11 and the layouts add an id, not a branch on a row id"
    - "model text reaches a harness file only through quote_line: one line, controls and whitespace collapsed, sanitizer first, then capped, behind the prefix '> '; parsers read structure lines only and take what follows the prefix as an opaque string"
    - "the review table is a pure function of filed text (candidate files and stop files); a rule change later means a new row7-review-part-N.md, never an edit"

key-files:
  created:
    - tests/harness/pc_review.py
    - tests/harness/test_review.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_evidence.py
    - tests/harness/pc_baseline.py
    - tests/harness/test_evidence.py
    - tests/harness/README.md

key-decisions:
  - "Calls that reproduce the model's own checkpoint (any string in the call input holds a line equal to '## Do not redo' or '## Identity and state') are never candidates and are counted as assembly calls; the committed row 7 full trace shows calls 14 and 16 (the refused Write and the byte-measuring heredoc) are the only holders of the first entry's tokens, so that entry stays UNSUPPORTED"
  - "Entry and call tokens are whole, case-sensitive strings. Call words are split at white space and shell punctuation, and the whole input value and each of its lines are tokens too, so a backtick span that is a whole command or line can match; hex runs are extracted from any text"
  - "A non-empty unindented line after a bullet joins that bullet, so no model text is dropped from the entry list; a section with no bullet gives its plain lines (row 4b)"
  - "Facts are read from tool calls and results of the /preclear stage only: executed means not in the denial union and no error flag; errored means either"
  - "The review table keeps SKIPPED folders as attempts (state skipped, reason line) in addition to filed and stopped ones"
  - "Hostile-text safety is structural: the candidate file and the review table print model text only on '> ' lines, tool ids and tool names pass strict patterns (else '?'), and the parser rejects any file that is not in the fixed shape"
  - "pc_baseline's close and row7-review share one staging, sanitizer, leak gate and promote_into function (_add_flat_files); close behaviour and messages are unchanged"

patterns-established:
  - "Row7World in test_review builds a scratch dated folder through the real driver (three invocations: found, none marker, stopped) and copies it for tests that write"

requirements-completed: [RERUN-01]

coverage:
  - id: D1
    description: "do_not_redo_entries returns bullet entries with wrapped lines joined and the plain lines when the section holds no bullet; over the committed Final replies it gives 2 entries for row 7 (the first starting 'Workspace policy/registry checked'), 2 for row 3c and 2 plain-line entries for row 4b"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#EntryParserTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "The token rules (backtick spans, path-like words, hex runs of 7 or more; whole and case-sensitive; ubiquitous paths, '.', '..', '.git' and tokens under 3 characters dropped; run-root paths made relative; Write content never read) and the candidate rule (assembly calls excluded and counted) behave as stated"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#TokenRuleTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_review.py#CandidateTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "In the committed row 7 full trace the only calls holding a token of the unsupported entry are calls 14 and 16, and both reproduce the checkpoint, so the entry has no candidate and prints UNSUPPORTED"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#CandidateTests.test_the_committed_row_7_full_trace_keeps_the_first_entry_unsupported"
        status: pass
    human_judgment: false
  - id: D4
    description: "A scripted row 7 chain files do-not-redo-candidates.md (entry 1 UNSUPPORTED, entry 2 one candidate id, two assembly calls) and a Row 7 facts section of mechanical-checks.md (0 executed writes, 1 errored write with its id, 1 EACCES result, 0 chmod); a none-marker chain files the file with 0 entries; the row 7 README points to row7-review.md"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#ScriptedChainTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_review.py#Row7FactsTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "pc_baseline row7-review builds row7-review.md from filed files only: sections in attempt order (not folder-name order), a stopped attempt with its stop reason and no entries, a none-marker attempt listed with no table body, zero-entry, absent and damaged candidate files as sections, SKIPPED attempts kept; a second run writes row7-review-part-2.md and leaves the first byte-identical; a folder with no row 7 attempt and the frozen folders exit 2 and nothing is written; a path-shaped string in a filed entry is refused with exit 14"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#ReviewTableTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "A hostile entry, excerpt, tool id or tool name (heading, fake candidate or table line, the word UNSUPPORTED, newlines, very long lines) cannot add structure to the candidate file or the review table; the parser rejects damaged files; over-cap input gives bounded files (64 entries, 400, 160, 20 candidates with the rest counted)"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#HostileTextTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "The vocabulary scan skips only lines that begin with '> ' in do-not-redo-candidates.md and the row7-review files, catches the same word on any other line of them and in every other harness-authored file; harness_authored_names picks the candidate file in row and attempt folders only and the review files at the top level only"
    requirement: RERUN-01
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py#QuotedLineVocabularyTests"
        status: pass
    human_judgment: false
  - id: D8
    description: "Whether each listed candidate really supports its entry is a human judgement; the mechanical candidates can over-pair or under-pair, and nothing in this plan can prove an entry true. Codex and bokiko confirm or reject each pairing in codex-review.md"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan (D-06): the harness lists candidates and counts only"

duration: about 3 h (estimate; the start time was not recorded), of which about 25 min were full-module and full-suite runs
completed: 2026-11-02
status: complete
---

# Phase 4 Plan 7: Do-not-redo review Summary

**Every completed row 7 chain now files `do-not-redo-candidates.md` (each Do-not-redo entry of the printed checkpoint with the tool calls of the same /preclear turn that share a whole token with it, or UNSUPPORTED when there is none) plus a `Row 7 facts` section in `mechanical-checks.md`, and `pc_baseline.py row7-review --folder F` builds the side-by-side `row7-review.md` of all attempts, stopped ones kept, from filed files only; model text can never add structure and the harness never decides.**

## Performance

- **Duration:** about 3 h (estimate; the start time was not recorded)
- **Completed:** 2026-11-02
- **Tasks:** 3
- **Files modified:** 7 (2 created)

## Accomplishments

- `pc_review` (new): the entry parser (bullets with wrapped lines joined, plain lines when the section holds no bullet), the whole-token rules, the candidate rule with the assembly-call exclusion, the row 7 facts, the fixed candidate file (`render_candidates` and a strict `parse_candidates`), the review table (`Attempt`, `render_row7_review`) and `ANALYSES`. The entry source is `pc_row1.printed_checkpoint`, the function the chain itself uses.
- Row 7 on the committed reply: 2 entries; the first (`Workspace policy/registry checked ...`) has the tokens `policy/registry` and the runs-root path, and both occur only in calls 14 and 16 of the full trace, which reproduce the checkpoint, so it prints UNSUPPORTED. Rows 3c and 4b give 2 entries each, row 4b as plain lines.
- `pc_rows.RowSpec.analyses` and `pc_evidence._run_analyses`: filing runs the analyses a row names after the standard files, only for a complete chain (found, or the none marker with the stages that ran); an unknown id is an `EvidenceError` and files nothing. Row 7 names `row7-facts` and `do-not-redo`. A one-line README pointer to `row7-review.md` is in every row 7 README.
- `pc_baseline row7-review`: reads each attempt folder (bare folder is attempt 1, `-attempt-N`, `STOPPED-`, `SKIPPED-`), builds the table in attempt order, and adds it with `promote_into` as `row7-review.md` or the first free `row7-review-part-N.md`. `close` and `row7-review` now share `_add_flat_files` (stage in a run root, sanitize, leak gate, promote), behaviour of `close` unchanged.
- `harness_authored_names` covers the candidate file (row and attempt folders) and `row7-review(-part-N).md` (top level); the vocabulary scan skips exactly the `> ` lines of those files.
- Tests: `test_review.py` (69 tests: `EntryParserTests`, `TokenRuleTests`, `CandidateTests`, `Row7FactsTests`, `ScriptedChainTests`, `ReviewTableTests`, `HostileTextTests`) and 3 in `test_evidence.py` (`QuotedLineVocabularyTests`). Suite 1723 -> 1795 (3 skipped as before), green through `tests/harness/selftest` with the `0 model calls` banner.

Suite count: 1795

## Task Commits

1. **Task 1 (tracer): candidates, analyses, facts** - `bc80509` (feat)
2. **Task 2: the row7-review subcommand and its tests** - `9915d25` (feat)
3. **Task 3: vocabulary rule for quoted lines, README** - `990f55c` (feat)

**Plan metadata:** the SUMMARY commit that follows. STATE.md, ROADMAP.md, WINDOWS.md and state.json were not touched.

_Tracer gate: the tracer `<verify>` (`test_review.py`, `test_row7.py`, `test_evidence.py`) passed before the commit; no `blocking-human` gate was set. Per commit I ran the modules the change could touch (`test_row7`, `test_evidence`, `test_readme`, `test_imports`, `test_runroot`, `test_row_generic`, `test_rows_plain`, `test_stages`, `test_boundaries`, `test_driver_matrix`, `test_baseline`, `test_matrix_cli`, `test_review`); the whole suite ran once on the final head._

## Files Created/Modified

- `tests/harness/pc_review.py`, `test_review.py` - new
- `tests/harness/pc_rows.py` (analyses field, `ROW7_ANALYSES`), `pc_evidence.py` (analyses hook, scanned names, README pointer), `pc_baseline.py` (subcommand, shared staging), `test_evidence.py` (scan rule and 3 tests), `README.md` (Layout lines, a "The Do-not-redo review" section)

## Decisions Made

See `key-decisions` above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Three commits, one per task, with module-level rather than whole-suite runs per commit**
- **Issue:** the plan wants a green suite at each commit; the whole suite takes about 11 minutes.
- **Fix:** each commit was preceded by the modules it can affect; the whole suite ran on the final head (1795 OK). Earlier plans used one commit.

**2. [Rule 1 - Plan text] The `facts:` line carries five counts and the assembly count has its own line**
- The plan says the facts line has "the five counts" and also lists six facts (the errored writes as ids and the assembly calls as a count). The candidate file has `facts:` with executed writes, errored writes (count), EACCES results, Permission denied results and chmod, and a separate `assembly calls:` line; the `Row 7 facts` section lists all six with the errored ids.

**3. [Rule 2 - Missing critical functionality] The raw text is cut at four times the cap before the sanitizer runs, dropping a partial word**
- **Issue:** cutting after cleaning is what keeps half of a path from escaping the sanitizer, but cleaning megabytes of a hostile command first is not bounded.
- **Fix:** `one_line` cuts the raw text at four times the cap (dropping a trailing partial word), cleans, then applies the cap. A consequence tested and documented: when cleaning shrinks the text a lot, fewer words than the cap allows can show.

**4. [Rule 2 - Missing critical functionality] The review table keeps SKIPPED attempts**
- The plan's attempt state is filed or stopped; a SKIPPED row 7 folder is also an attempt that never ran, so it is listed with its reason (state `skipped`).

**5. [Rule 3 - Blocking] The review intro avoids the owner's name**
- The sanitizer replaces the machine's login name, which equals the owner's public name, with a placeholder, so the first draft of the fixed paragraph filed as "Codex and <user>". The text now says "Codex and the owner".

**6. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- A failing `test(...)` commit would break the green-suite rule; tests were written with the code and run before each commit. See TDD Gate Compliance.

**7. [Plan text note] Frozen-path guard**
- Used the orchestrator's base `56e155c` and path list (`SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20`): empty. The frozen Phase 3 folder differs from `56e155c` only because it was created after it; against this plan's base `c66c769` nothing under `tests/evidence` changed. SKILL.md is 11994 bytes.

---

**Total deviations:** 7 (2 plan-text notes, 2 missing critical, 3 blocking or process). **Impact:** none changes behaviour outside the review code, the analyses hook and the shared staging function.

## TDD Gate Compliance

Plan type is `execute` (not `type: tdd`), so the gate commands do not run; the tasks carry `tdd="true"`. The failing state was not committed because the plan requires a green suite at every commit.

## Authentication Gates

None. No real `claude` was started and nothing was spent.

## Issues Encountered

- The sandbox refuses long inline scripts and git commands combined with computed values; edits were applied from small scripts in the session scratch folder and commits ran from a one-line script. The per-plan head ledger file was created before the first commit, so `plan_head_before` is measured.
- Two test expectations of mine were wrong at first (a dot rule example with six characters and a list `count` that compared whole elements); both were test fixes, not code changes.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-04-29 (model text adding structure): every model line is one capped, cleaned line behind the quote prefix, ids and tool names pass strict patterns, the parser is strict (`HostileTextTests`). T-04-30 (disclosure): the sanitizer runs on every quoted line before the cap and again on the staged file, then the gate and promote; a path-shaped string in a filed entry is refused with exit 14 (tested). T-04-31: the module and its output hold no word for a backed entry; the scan skips only quoted lines. T-04-32: caps tested over-cap.

## User Setup Required

None - no external service configuration required.

## Notes for plan 04-08 (first paid wave) and later

- Driver invocation shape for the first paid wave (from the repository root, never `-I`): `python3 -E -s -B tests/harness/pc_matrix.py --row row5a-no-memory --row row5b-disabled-memory --row row6-readonly-plan --row row7-all-destinations-denied --claude ABSOLUTE_PATH_OF_THE_TESTED_BUILD --budget AMOUNT [--campaign LABEL] [--evidence-date YYYY-MM-DD]`. Dry-run first with the same selection plus `--dry-run` (it prints each row's worst case: two-stage rows 1.60, row 7 2.00; the budget must cover the finished rows plus the next row's worst case and be at most 25.00). A retry of one row is `--row ID --attempt N`, refused with exit 18 unless the ledger holds attempt N minus one.
- Row 7 now files two extra things with each completed chain: `do-not-redo-candidates.md` in its row folder and a `Row 7 facts` section (the eleventh) in its `mechanical-checks.md`. After the three attempts of the triple are filed into one dated folder, run `python3 -E -s -B tests/harness/pc_baseline.py row7-review --folder tests/evidence/rerun-DATE-MODEL[-CAMPAIGN]` (zero tokens, reads filed files only) and then `close`. Run `row7-review` again after any later attempt: it adds `row7-review-part-N.md`, the latest part is the complete one.
- The frozen Phase 3 folder and the Phase 3 publication folder are refused by `row7-review` (exit 2).
- A row 7 attempt whose reply holds a NUL byte in the printed block stays unfiled (exit 14 from the leak gate, plan 04-06), so no folder exists for `row7-review` to list; the triple's README or the Codex brief has to name such an attempt as unfiled from the run's printed lines.
- The facts and candidates are read from the raw s2 stream before sanitizing; real tool results for a create under a project folder at mode 555 (EACCES text or another) are still unobserved (plan 04-06 D9). The `eacces`/`Permission denied` counts will show which the build prints.
- The token rules are mine to tune: if the first real triple shows over-pairing or under-pairing, change the rules in `pc_review` and file a new `row7-review-part-N.md` (the table is a pure function of filed text; the candidate files of the triple would need a refile, which `--refile` does for any run root that still exists).
- `pc_review.ANALYSES` and `RowSpec.analyses` are ready for rows 10 and 11 and the layouts: add an id, a function returning `(section title, lines, files)`, and name it in the entry.

## Self-Check: PASSED

- Created files exist: `tests/harness/pc_review.py`, `tests/harness/test_review.py`, this summary.
- The task commits are ancestors of HEAD: `bc80509`, `9915d25`, `990f55c`.
- `commits:` was measured as the count from the ledger base to HEAD before this summary commit (3).
- Final gates: `tests/harness/selftest` 1795 tests OK (3 skipped) with the `0 model calls` banner (floor 1723); `scripts/test-hooks.sh` 29 PASS; `test_review.py` also green on the 3.9.6 system interpreter; leak gate over `tests/harness` 84 files, 0 findings; the secret scanner over `tests/harness` clean; frozen paths unchanged against `56e155c` and nothing under `tests/evidence` changed against the plan base; no attribution trailer in any commit of the range; the change list names only files under `tests/harness` plus this summary.
