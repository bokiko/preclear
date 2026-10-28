---
phase: 03-walking-skeleton-row-1
plan: 04
subsystem: testing
tags: [evidence-filing, sanitizer, leak-gate, promote, provenance, usage, reviewer-checklist, skipped-label, refile, python-stdlib, unittest]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_row1 (run_row, run_stage, finish, take_snapshot, caller_map, stage records, raw/run.json, raw/chain.json, snapshots snap-0-setup to snap-3-after-resume), pc_checks (compute_facts, breaches, breach fact names), pc_spend (call_cost, row_total), pc_rows (RunContext, RowOutcome, evidence_folder_name), pc_testutil (RowRig, scripted claude, seeds)"
  - phase: 02-model-free-foundation-and-stub
    provides: "pc_sanitize (Sanitizer, deny_entries), pc_leakgate, pc_promote (gate-first exclusive promote), pc_measure, pc_manifest, pc_mine.parse_trace, pc_stream, pc_flags, pc_runroot, pc_spike (scrub_volatile, runs_root, harness_home)"
provides:
  - "pc_evidence: load_stage_data, file_row (stage, sanitize, gate, promote with config_dir and deny_entries), file_skipped, stage_tree, new_stage_dir, collect_files, the renderers (usage, provenance files, digests, tools, settings, measurements, short and full traces, mechanical checks, checklist, row README, folder README), filed_snapshot_files, harness_authored_names, VERDICT_LINE"
  - "pc_row1: finish files the row after clean checks (last step); run_stage stores raw/<stage>.prompt verbatim after the ledger reservation; paths_for(run_root) rebuilds the paths mapping from a run root"
  - "pc_matrix: --refile RUNROOT (its own selection mode, zero tokens) and a real-run SKIP filed as SKIPPED-<row id> before exit 10"
  - "README: What a run files subsection, the scratch token, Layout lines for pc_evidence.py and test_evidence.py"
affects: [03-05, 03-06, phase-04]

actuals:
  tokens: 32943
  tasks: 3
  commits: 6
plan_head_before: 66e4477b0faf772ba57f28759c2dfe1e2b8aeefd
plan_head_after: bc8503aea288436b4d60a11adb394b4d57b27e87

tech-stack:
  added: []
  patterns:
    - "One route into tests/evidence: stage inside the run root, sanitize every file with the sanitizer built before spend, gate the whole tree with the sanitizer's deny entries, promote once; the stage folder is the first free stage-N and is never reused"
    - "Renderers are pure functions over files already on disk; filing and refile therefore give the same files, and a refusal after the paid stages is repeated for zero tokens"
    - "Harness-authored evidence is name: value lines (yes and no, UNCONFIRMED for an unmeasured value) and never a verdict word; the row README ends with the checklist and then the one verdict line"
    - "Facts for the reviewer are read from structured fields and files; the only model text in the filed folder is in files outside the harness-authored set (traces, replies, prompts, copies, stderr)"

key-files:
  created:
    - tests/harness/pc_evidence.py
    - tests/harness/test_evidence.py
  modified:
    - tests/harness/pc_row1.py
    - tests/harness/pc_matrix.py
    - tests/harness/test_stages.py
    - tests/harness/README.md

key-decisions:
  - "FA-2 reading kept: the checklist sits directly above Reviewer verdict: PENDING and the row README ends with that line; if the owner meant the checklist after the line it is a one-function change in render_row_readme"
  - "The checklist has seven lines, one per D-09 fact group (helper calls as one line holding attempted, executed, denied and compound refusals), each with a blank box, the value and the source files in parentheses; a zero is printed as 0"
  - "run_stage stores raw/<stage>.prompt after the ledger reservation and before the process, so a second launch of a stage is still refused by the ledger first (the earlier plan's test) and a refile needs nothing from memory"
  - "model-id.txt records the first readable init event's model; the model-pinned assertion of the stage chain already stops a run whose model differs, so filing never meets a different id"
  - "finish prints the stage lines, then one filed line (folder name and file count), then the row total line; a filing refusal returns only its own fixed lines and its exit code, with the raw files left in the run root"
  - "A real-run SKIP is filed before the budget and preflight checks (it needs neither); the label folder is created under the dated rerun folder, so a later real run on the same day finds that name taken (exit 17) by design"
  - "--refile validates the folder as a direct child of the runs root holding raw/run.json for row 1; any other value is exit 2 with the fixed text the run folder is not usable and no echo"

patterns-established:
  - "Filed row folder (row1-wrong-binding): README.md, claude-version.txt, digests.txt, fixture-CLAUDE.md, tools.txt, measurements.md, measurements.txt, s1-work.out, s1.err, s1.exit, s2-preclear-prompt.md, s2-preclear-trace.md, s2-preclear-full-trace.md, s2-preclear.err, s2-preclear.exit, session.id, status-before.txt, lint-before.txt, wrapper-calls.log, wrapper-checkpoint.sh, mechanical-checks.md, usage.txt, model-id.txt, isolation-mode.txt, harness-version.txt, s1-work-prompt.md, s1-work-full-trace.md, settings.json, s3-resume-trace.md, s3-resume-full-trace.md, s3-resume.err, s3-resume.exit, resume-line.txt, session-resume.id, and snap-0-setup, snap-1-after-work, snap-2-after-preclear, snap-3-after-resume (each with sha.txt, manifest.jsonl, status.txt, ledgers-ls.txt, bindings-ls.txt, the two ledger copies, and the preclear and auto-memory trees when present); with no resume line the s3 files and snap-3-after-resume are absent and resume-line.txt holds NO-RESUME-LINE"
  - "The folder above it holds README.md (new-baseline label, row and run totals, not a replication of 2026-10-20, five differences, the committed folder stays the reference)"
  - "Stage folders inside a run root: stage-1, stage-2 and so on, exclusive, numbered, kept"

requirements-completed: [HARN-05, EVID-04, EVID-05]

coverage:
  - id: C1
    description: "A finished run is filed only through stage, sanitize, leak gate and promote(stage, destination, repo_root, config_dir, deny_entries): the destination is created exclusively (a second filing is 17 with the first folder unchanged), no raw stream, NUL status capture, hook log, stage record, git state file or run.json is staged, and a gate scan of the promoted folder reports 0 findings; a seeded breach creates no folder (exit 11)"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (FilingTests)"
        status: pass
    human_judgment: false
  - id: C2
    description: "WR-14: a spy on promote sees deny_entries equal to the sanitizer's (non-empty, holding the synthetic login) and the config folder; a staged file that still holds the synthetic login is refused with 14 because of those entries and the same bytes promoted with deny_entries None are accepted, so the test can tell the two apart; a sanitizer error is 15"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (Wr14Tests, FilingTests)"
        status: pass
    human_judgment: false
  - id: C3
    description: "The filed row folder holds the committed per-row file set plus mechanical-checks.md, usage.txt, model-id.txt, isolation-mode.txt, harness-version.txt, the work-turn prompt and full trace, settings.json, the s3 set and a manifest in each snapshot; the s2 prompt is a byte copy of the committed file; with no resume line the s3 files are absent and the marker is filed; zero-byte stderr files are filed; two filings of one run root give equal files except harness-version.txt"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (FileSetTests)"
        status: pass
    human_judgment: false
  - id: C4
    description: "Provenance is filled in every field (banner line, pinned model id, isolation word with setting sources and claim sentence, tree digest with full HEAD and clean flag, digests of SKILL.md, the three reference files, the stub and the wrapper, the 40 allowlist rules, the Init manifest block with tool count and names); an unmeasured value is UNCONFIRMED; measurements are taken on the original checkpoint with 4096 bytes within the cap and 4097 over by one, and UNCONFIRMED without a checkpoint"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (ProvenanceTests)"
        status: pass
    human_judgment: false
  - id: C5
    description: "usage.txt lists s1, s2, s3 in order with session id, subtype, turns, the four token categories, the call's own cost (a delta), the reported cumulative total and wall seconds as text exactly as parsed; the row total is the s2 cumulative plus the s3 total (s1 is never added), the run total equals it; an absent usage block prints UNCONFIRMED in each token field"
    requirement: HARN-05
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (UsageTests, ProvenanceTests)"
        status: pass
    human_judgment: false
  - id: C6
    description: "The short and full traces have the committed shapes; the full trace parses through pc_mine.parse_trace and its REFUSAL/DENIAL flags equal the structured denial union; a result text or reply that holds denial words changes no flag"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (TraceTests)"
        status: pass
    human_judgment: false
  - id: C7
    description: "No harness-authored file holds a verdict word (pass, passed, fail, failed, failure, accept, accepted, verdict, case-insensitive whole words) except the one exact last line of the row README, Reviewer verdict: PENDING, which occurs once in the harness-authored set; a reply with those words is filed as written and sits outside the scan; the row README ends with seven checklist lines (D-09 order, blank box, value, source in parentheses, a zero printed as 0) directly above that line; mechanical-checks.md has the ten sections in order with name: value lines and the twelve assertion ids in declared order per stage"
    requirement: EVID-05
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (VocabularyTests, ChecklistTests)"
        status: pass
    human_judgment: false
  - id: C8
    description: "The folder README labels the run a new baseline on the pinned model and build, quotes the row and run totals from usage.txt, says it is not a replication of 2026-10-20 because that run recorded no model, lists the five differences (Claude Code 2.1.310 against 2.1.304, the pinned flag set, the stub in place of the real helper, per-verb allowlist, run roots outside the home folder, strict isolation), says the committed folder stays the reference, says the reviewer and never names the owner's login"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (FolderReadmeTests)"
        status: pass
    human_judgment: false
  - id: C9
    description: "A real-run SKIP files SKIPPED-<row id>/README.md (no session was run, the reason, the verdict line last, no usage or snapshots), starts no stage, writes no ledger line and exits 10; a reason shaped like a home path is refused with 14 and files nothing; an existing destination is 17; a skip is never exit 0"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (SkippedTests)"
        status: pass
    human_judgment: false
  - id: C10
    description: "--refile RUNROOT re-runs the checks and the same file_row from disk with no claude process, no budget and no ledger line, files under the date and model recorded in the run, refuses a relative, missing, file, outside-the-runs-root or record-less path with exit 2 and fixed text that does not echo the value, an existing destination with 17, a breach and a missing stored prompt with 11, and cannot be combined with another selection or --dry-run; two concurrent filings of one run give exactly one 0 and one 17 with stage-1 and stage-2 kept and one complete tree"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/test_evidence.py (RefileTests, RaceTests)"
        status: pass
    human_judgment: false
  - id: C11
    description: "Zero model calls: 1048 tests (992 before) pass on the PATH interpreter (3.14) through the selftest shim (0 model calls, OK (skipped=3)) and on the system Python 3.9.6; the leak gate reports 0 findings over 68 files, gitleaks dir over tests/harness is clean, pc_mine --check is green, and SKILL.md, references/, tests/fixtures/ and tests/evidence are unchanged"
    requirement: EVID-04
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 1048 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p 'test_*.py' (Ran 1048 tests, OK (skipped=3))"
        status: pass
    human_judgment: false
  - id: C12
    description: "A filing interrupted part-way through promote leaves a partial destination folder that promote reports as a partial promote with exit 17; no zero-token test can interrupt a real promote midway, and the folder is never reused or repaired by the harness"
    requirement: EVID-04
    verification:
      - kind: other
        ref: "backstop: promote's own partial-promote report; not reproducible without killing a real promote"
        status: unknown
    human_judgment: true
  - id: C13
    description: "FA-2: the D-09 ordering (checklist directly above the verdict line, file ends with the verdict line) is the planner's reading; whether the owner meant the checklist after the line is to be confirmed at the plan 03-06 checkpoint"
    requirement: EVID-05
    verification:
      - kind: other
        ref: "backstop: plan 03-06 human review of the filed README"
        status: unknown
    human_judgment: true

# Metrics
duration: not recorded (start time was not captured)
completed: 2026-10-29
status: complete
---

# Phase 3 Plan 04: Filing the run - sanitized, gated, mechanical evidence with a PENDING verdict Summary

**A finished row 1 run root is now filed into a new exclusive `tests/evidence/rerun-<date>-<model>` folder only through the stage, sanitize, leak gate and promote route with the sanitizer's deny entries (a test fails if they are ever dropped), in the committed per-row file set plus the provenance, usage and mechanical-check files, with a seven-line reviewer checklist directly above the single line `Reviewer verdict: PENDING` and no verdict word anywhere the harness wrote itself. A SKIPPED row is filed as a label folder and exits 10, and `--refile RUNROOT` repeats a refused filing for zero tokens. No model was called.**

## Performance

- **Duration:** not recorded
- **Completed:** 2026-10-29
- **Tasks:** 3 (each a `test(03-04)` commit then a `feat(03-04)` commit; Task 1 is the tracer)
- **Files:** 2 new (`pc_evidence.py`, `test_evidence.py`), 4 modified (`pc_row1.py`, `pc_matrix.py`, `test_stages.py`, `README.md`)
- **Suite:** 992 tests before, 1048 after (56 new, all in `test_evidence.py`), `OK (skipped=3)`, 0 model calls, on Python 3.14 (through the shim) and the system 3.9.6

## Accomplishments

- **Task 1, tracer (EVID-04, WR-14).** `file_row` stages one tree inside the run root, sanitizes every file, and promotes once with `config_dir` and `deny_entries`. `finish` files after clean checks; `run_stage` stores each stage prompt under raw; `paths_for` rebuilds the paths mapping from a run root. Wr14Tests discriminate: the same staged bytes are refused (14) with the entries and accepted without them.
- **Task 2, the full file set (EVID-04, EVID-05, HARN-05).** Provenance files, digests, tools, settings, measurements (original checkpoint, cap edge), usage with per-call deltas, short and full traces in the committed shapes (flags from the structured denial union only), `mechanical-checks.md` in ten sections, the row README with its checklist and the single verdict line, the folder README, and rebuilt snapshot listings without the interpreter and stub path entries.
- **Task 3, SKIPPED, refile, race, README (D-10, HARN-02).** `file_skipped`, `--refile` as its own selection mode (exit 2 with fixed text for any unusable folder), the real-run skip filed before the exit 10, a two-thread race with one winner, and the README subsection.

## Filed row 1 file names

See `patterns-established` in the frontmatter for the complete list. The row README checklist wording did not change from the plan's order: helper calls, ledger digests unchanged, writes outside approved roots, git mutations, checkpoint bytes versus cap, session ids per stage, cost and turns per stage.

## Task Commits

1. Task 1 tracer: `9ed8219` test, `db88003` feat
2. Task 2: `30340eb` test, `137a94c` feat
3. Task 3: `69ee841` test, `bc8503a` feat

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] The earlier stage test checked every outcome line against a fixed pattern**
- **Found during:** Task 1
- **Issue:** `test_stages.py` asserts that each line of a completed row's outcome is a stage line or the row total line. Filing adds one fixed line (`filed: <folder name>, <n> file(s)`), which the plan requires (the printed outcome names the destination folder).
- **Fix:** the pattern in that one assertion also accepts the filed line.
- **Files modified:** `tests/harness/test_stages.py`
- **Commit:** `db88003`

**2. [Rule 1 - Bug] The stage prompt is stored after the ledger reservation, not before**
- **Found during:** Task 1
- **Issue:** storing `raw/<stage>.prompt` first made a second launch of the same stage fail with a file-exists error before the ledger could refuse it, which broke `test_a_stage_is_reserved_before_its_process_and_never_started_twice` (plan 03-02).
- **Fix:** the prompt is written right after the launch line and before the process starts, so the ledger refusal (`SpendRefused`) still comes first.
- **Files modified:** `tests/harness/pc_row1.py`
- **Commit:** `db88003`

### Test edit between a test commit and its feat commit

In `test_evidence.py` (Task 3 feat commit): `test_unusable_run_folders_are_exit_2_with_fixed_text_and_no_echo` read `run.run_root` after the test had created a second folder under the runs root; it now captures the run root first. Nothing else in a test file moved between its test and feat commits.

### Notes on the plan's wording

- Some Task 2 and Task 3 tests passed on their first run before the matching implementation existed where they cover behaviour that Task 1 already gave (an existing destination is 17, a seeded breach files nothing, a mutually exclusive selection is a usage error because the flag was unknown). They are regression guards, not new behaviour.
- `model-id.txt` records the model the first readable init event reported rather than re-asserting the pinned id at filing time; the stage chain's `model-pinned` assertion already stops a run with another model before anything is filed.
- The Task 1 slice stages the snapshots as plain copies (minus `status.raw`); Task 2 replaces the two listings by rebuilt ones without the interpreter and stub path entries.

### Threat flags

None. No network endpoint, auth path or schema was added. The only new write route into `tests/evidence` is the one the plan specifies, and every file on it passes the sanitizer, the gate and promote with the deny entries.

## Authentication gates

None. No real `claude` was started; the only claudes executed were the scripted fake and the tripwire of `pc_testutil`.

## Known Stubs

None. Every filed value is computed from files on disk, and an unmeasured value is written UNCONFIRMED.

## Self-Check: PASSED

- Created files exist: `tests/harness/pc_evidence.py`, `tests/harness/test_evidence.py`.
- Commits `9ed8219`, `db88003`, `30340eb`, `137a94c`, `69ee841`, `bc8503a` are ancestors of HEAD; the diff against the plan's start lists only files under `tests/harness/`; `SKILL.md`, `references/`, `tests/fixtures/` and `tests/evidence/` are unchanged (`git status` for `tests/evidence` is empty); no commit carries an attribution trailer and no hook was bypassed.
- Full suite on both interpreters, the leak gate over `tests/harness` (0 findings), gitleaks dir over `tests/harness`, `pc_mine.py --check` and the refile fixed-text check against a tripwire claude are all green after the last feat commit.
