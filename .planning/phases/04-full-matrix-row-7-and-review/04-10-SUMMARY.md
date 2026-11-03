---
phase: 04-full-matrix-row-7-and-review
plan: 10
subsystem: testing
tags: [harness, row10, hostile-names, status-form, git-calls-join, static-allowlist-scan, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-09 git shapes and shared git test helpers, 04-07 pc_review.ANALYSES and the analysis signature, 04-01 row-generic engine
provides:
  - row 10 (row10-large-status) registered as implemented, three stages (15/0.30, 60/1.30, 15/0.40), PROFILE_GIT (33 rules), memory pinned, resume-line chain, analyses ("status-form",), reading the committed rerun folder
  - pc_rowseeds.SHAPE_LARGE (GIT_SHAPES now six), hostile_names(), hostile_text(), seed_row10 (124 untracked entries built from code points)
  - pc_review.status_form_counts, render_status_form, sidecar_facts, bash_parts, git_argv, has_nul_flag, is_quoted_status and the analysis id status-form (section "Row 10 status form")
  - pc_review.parse_git_calls_log, join_ids, git_call_counts, render_git_calls, unquote_printf_q, wrapper_digest_state and the analysis id git-calls (section "Git wrapper calls", files git-calls-correlated.txt, git-calls.log, injection.log, wrapper-git.sh)
  - pc_rows.ROW10, ANALYSIS_STATUS_FORM, ROW10_ANALYSES, ANALYSIS_GIT_CALLS
  - row 10 README checklist line with the expected outcome and the counts beside it (pc_evidence)
  - test_rows_git.AllowlistStaticTests (static scan over every buildable allowlist and the committed tools.txt of rows 10 and 11)
affects: [04-11, 04-12, 04-13, 04-14, 04-19, 04-21]

actuals:
  tokens: 22395
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 5bd8a4ff7e8659f8eee551ca12e942f7aea8da9d
plan_head_after: 8fe3d005f79a0d992189f9de957d8e261aa6f79d

tech-stack:
  added: []
  patterns:
    - "an analysis that counts what the model ran splits each Bash command with pc_allowlist.split_compound, reads redirections with pc_checks._read_redirections and tokenises the blanked text with pc_checks._tokens; denied versus executed comes from the structured denial union only"
    - "a log whose lines can interleave is parsed with a strict per-line regex plus an inside-start detector; an unreadable line stays in the list as an unreadable call and is counted as UNCONFIRMED, never dropped"
    - "a hostile tree is a table of names built from escaped code points in an ASCII source, created only through pc_runroot"

key-files:
  created: []
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_review.py
    - tests/harness/pc_evidence.py
    - tests/harness/test_rows_git.py
    - tests/harness/test_review.py
    - tests/harness/README.md

key-decisions:
  - "The NUL form is any git part holding -z, a short cluster with z, or --null (words after the verb, stopping at --); non-git parts such as sort -z are not counted"
  - "A denied call is judged on its whole command (a NUL git part and an output redirection anywhere in it); an executed call is judged per part"
  - "The quoted form is recognised by its three flags and no NUL flag on a git status call, so a stderr redirection or a global option does not hide it"
  - "join_ids never consumes log lines in order: a call equal to several executed parts is ambiguous with all candidate ids (a command with the same argv twice is ambiguous with its one id); a call matching no part is unmatched; denied parts are never candidates"
  - "raw/gitwrap-digests.json is read as a JSON object of file name (inside ckpt/gitwrap) to 64 hex digits; yes, no, not recorded or UNCONFIRMED (malformed record). Plan 04-12 must write this shape"
  - "The wrapper log and injection log are read from ckpt/gitwrap/git-calls.log and ckpt/gitwrap/injection.log; the shim copy is read from tests/harness/git-wrapper when that file exists"

patterns-established:
  - "the row README checklist grows one line for a row whose analyses include status-form"

requirements-completed: [HARN-10, HARN-11, RERUN-02]

coverage:
  - id: D1
    description: "--dry-run --row row10-large-status prints 3 stages, 2 sessions, turns and caps 15/0.30, 60/1.30, 15/0.40, worst case 2.00 USD, allowlist 33 rules, exits 0, starts no process and creates no harness home; --list marks it implemented"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#Row10Tests"
        status: pass
    human_judgment: false
  - id: D2
    description: "seed_row10 leaves exactly 124 untracked hostile entries (90 sample files, 15 each in the two non-Latin folders, newline, quote-and-tab and leading-space names, NOTES.md with non-Latin text) on one commit, built from code points with no non-ASCII character in the source; CLAUDE.md equals the committed rerun fixture byte for byte and the plan equals the plain plan"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#Row10Tests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A scripted row 10 chain files through the real sanitizer, leak gate and promote: snapshot listings hold the newline name as one escaped line, no filed file holds a NUL byte, no raw capture is filed, s3 makes zero Write/Edit calls and the s2 and s3 snapshots hash alike"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#Row10Tests"
        status: pass
    human_judgment: false
  - id: D4
    description: "The status-form counts (quoted form executed, NUL form executed with and without a redirection, denied NUL redirect calls with ids, sidecar present or absent with size and NUL bytes) come from the stream and the filed sidecar copy, split per part of a compound command, and the section holds counts, ids and present or absent only with no verdict word; a scripted row 10 chain files the section and the README checklist line"
    requirement: RERUN-02
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#StatusFormTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_rows_git.py#Row10StatusFormChainTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "parse_git_calls_log and join_ids label internal (-c), single-match tool_use id, ambiguous with every candidate id and unmatched calls, report an interleaved or cut line as UNCONFIRMED with a count, give zero counts for an empty log, and the digest state of the wrapper files reads yes, no, not recorded or UNCONFIRMED"
    requirement: HARN-11
    verification:
      - kind: unit
        ref: "tests/harness/test_review.py#GitCallJoinTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "No rule of any allowlist the harness can build (every profile with every extra set of the registry) and no rule in the committed tools.txt of rows 10 and 11 holds -z, a redirection character, tee, --output, a NUL or status.txt, and the same scan fails on hand-built lists"
    requirement: HARN-10
    verification:
      - kind: unit
        ref: "tests/harness/test_rows_git.py#AllowlistStaticTests"
        status: pass
    human_judgment: false
  - id: D7
    description: "Whether the real model attempts the NUL redirect, how the binary words its refusal and whether it falls back to the quoted form is unobserved on 2.1.310 until wave B; the scripted claude proves the counting and the real run records the facts, and the Codex round judges them"
    verification: []
    human_judgment: true
    rationale: "Backstop truth of the plan: only a real stream shows what the pinned build and model do with a large hostile status"

duration: not recorded (start time was not captured); the full suite run took about 12 min
completed: 2026-11-03
status: complete
---

# Phase 4 Plan 10: Row 10 and the status-form analysis Summary

**Row 10 (large status, hostile names, non-Latin text) now runs three stages through the engine on the 33-rule baseline alone with a 124-entry hostile tree built from code points, and its expected outcome is checkable from structure: counts of the quoted-porcelain form, the NUL form with and without a redirection, the denied NUL redirect calls with their ids and the sidecar bytes, with a static test proving no redirection or NUL-form rule exists in any allowlist.**

## Accomplishments

- Row 10 registered (`ROW10`): the committed rerun folder's s2 prompt and fixture, `PROFILE_GIT` (33 rules), memory pinned, three stages, resume-line chain, analyses `("status-form",)`, harness-worded Setup paragraph.
- `seed_row10` on a new `large` shape: one commit, then 124 untracked files created exclusively (90 `data/raw files/sample N.csv`, 15 files in each of the Japanese and Arabic folders, the newline, quote-and-tab and two-leading-space names, `NOTES.md` with text of both scripts). Names come from escaped code points; the sources are ASCII (pc_review.py keeps the one pre-existing non-ASCII line from plan 04-07, checked by a test).
- `status-form` analysis and the README checklist line "expected outcome, quoted-porcelain fallback and NUL redirect refused" with the counts beside it.
- `git-calls` analysis plus the pure `parse_git_calls_log` / `join_ids` for plan 04-12.
- `AllowlistStaticTests` (8 tests) and a README paragraph.
- Tests added: `Row10Tests` (20), `Row10StatusFormChainTests` (7), `StatusFormTests` (20), `GitCallJoinTests` (14), `AllowlistStaticTests` (8). Suite 1878 -> 1947 (3 skipped as before); `test_rows_git.py` and `test_review.py` also green on the 3.9.6 system interpreter.

Suite count: 1947

## Task Commits

1. **Task 1 (tracer): row 10 runs three stages with its hostile tree on the baseline allowlist** - `47585df` (feat)
2. **Task 2: the status-form analysis and the git-call id join** - `de8aeeb` (feat)
3. **Task 3: static allowlist scan and README paragraph** - `8fe3d00` (feat)

_Tracer gate: the tracer `<verify>` (Row10 tests, the tripwire dry run, test_manifest) ran and passed before the Task 1 commit; no `blocking-human` gate._

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Three tests that encoded old meanings were moved, none deleted**
- `test_the_shape_words_are_the_five_the_plan_names` (test_rows_git) now lists six shape words (the sixth is `large`); renamed accordingly.
- `test_the_registry_names_the_two_analyses_for_row_7_only_and_pc_review_has_both` (test_review) now expects four analysis ids and row 10 naming `status-form`.
- Commits: 47585df, de8aeeb.

**2. [Rule 2 - Missing functionality] The README checklist line needed `pc_evidence.py` (not in `files_modified`)**
- The plan says the README checklist line for row 10 reads as the expected outcome with the counts; checklist lines are generated in `pc_evidence.checklist_lines`, so a small lazy-import hook was added there (a line only for a row whose analyses hold `status-form`). Still inside tests/harness. Commit de8aeeb.

**3. [Plan assumption corrected] The harness allowlist matcher does not refuse a redirect**
- `pc_allowlist.is_allowed` models prefix rules only, so it allows `git ... status -z > file`; the refusal in the committed trace is the binary's own permission layer ("Output redirection ... needs approval"). The static test therefore proves "no rule exists", and a test records that the matcher allows the prefix while the committed trace shows the binary's refusal text. No claim in code or README says a rule refuses the redirect.

**4. [Plan wording] Non-ASCII in pc_review.py**
- `pc_review.py` already held one non-ASCII line (the `_CONTROL` character class from plan 04-07); this plan adds none, and the test says so.

**5. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- A failing test commit would break the green-suite rule; tests were written with the code and run before each commit.

**Total deviations:** 5, none changing earlier behaviour for rows other than row 10.

## Known Stubs

None.

## Threat Flags

None. The new reading surface is the harness reading a sidecar copy and a wrapper log it is given; the join and the counts print counts, labels and strictly patterned ids only (a hostile id prints as `?`).

## Notes for plan 04-11 (paid wave B: rows 8a, 8b, 8c, 9, 10) and 04-12

- **Driver invocation:** there is no new flag; run the five rows by `--row <id>` (or `--all` once the wave is chosen) with the same driver and flags as wave A; row 10's id is `row10-large-status`. Dry run: `--dry-run --row row10-large-status` prints `3 stages, 2 sessions`, `worst case 2.00 USD`, `allowlist 33 rules`.
- **Wave B worst case:** each of the five rows is three stages, 2.00 USD, so rows 8a, 8b, 8c, 9 and 10 together are 10.00 USD. `--all` over the thirteen implemented rows now sums to 18.40 + 2.00 = 20.40 USD, under the 25.00 ceiling; rows 11 and 12 will add to it, so check the ceiling when plan 04-12 lands.
- **What to read after the row 10 run:** the `Row 10 status form` section of `mechanical-checks.md`, the README checklist line, and `snap-2-after-preclear/preclear/<task>/status.txt` if present. A model that tries the NUL redirect leaves a denied call id in `nul-git-calls-denied-with-redirection`; an executed `-z` command with no redirect is a fact, not a defect. A NUL byte in a filed sidecar is refused by the leak gate (exit 14) and the row is not filed; that is recorded as a fact.
- **For plan 04-12 (row 11 wrapper):** write `raw/gitwrap-digests.json` as a JSON object of file name inside `ckpt/gitwrap` to its sha256 hex (`git`, `real-git`, `match-argv`, `fire-on`, `inject-file`); keep the logs at `ckpt/gitwrap/git-calls.log` and `ckpt/gitwrap/injection.log`; log lines `T=<utc> PID=<pid> EXIT=<code> ORD=<k or -> ARGV=<printf %q arguments>` (a leading space before the first argument is fine; `$'...'` and backslash forms decode). Name the analysis id `git-calls` (constant `pc_rows.ANALYSIS_GIT_CALLS`) in the ROW11 entry. The analysis reads the shim copy from `tests/harness/git-wrapper`.
- **Unobserved until wave B:** how the real model reads a 124-entry status with newline, quote and tab names, whether it tries the NUL redirect, how the binary words the refusal, and whether the quoted fallback is used.

## Self-Check: PASSED

- Modified files exist; task commits `47585df`, `de8aeeb`, `8fe3d00` are ancestors of HEAD.
- `commits: 3` measured from the persisted ledger (`plan_head_before` 5bd8a4f).
- Final gates: `tests/harness/selftest` 1947 tests OK (3 skipped) with the `0 model calls` banner (floor 1878); `scripts/test-hooks.sh` 29 PASS, 0 FAIL; leak gate over tests/harness 85 files, 0 findings; gitleaks clean; frozen paths, `tests/evidence` and SKILL.md (11994 bytes) unchanged; no attribution trailer in the range; change list names only tests/harness files plus this summary.
