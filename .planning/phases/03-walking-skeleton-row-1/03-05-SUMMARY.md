---
phase: 03-walking-skeleton-row-1
plan: 05
subsystem: testing
tags: [read-only-comparer, tree-digest, frozen-trees, pinned-digests, allowlist-corpus, evidence-comparison, python-stdlib, unittest]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_evidence (the per-row file set the new side holds), pc_matrix.main (the fake-pipeline world used by the tests), pc_testutil.RowRig, pc_manifest (tree_manifest, jsonl_bytes, escape_name), pc_mine.parse_log, pc_measure (SECTIONS, FILE_CAP), pc_allowlist.row_rules"
provides:
  - "pc_compare: tree_digest, compare_rows, report_lines, parse_measurements, count_trace_calls, normalise, main; CLI --old DIR --new DIR [--row ID]; exit 0 whenever both trees were readable, 2 otherwise with fixed text"
  - "test_frozen_tree: SKILL_MAX_BYTES (12000) and pinned SKILL_SHA256, REFERENCES_TREE_SHA256, FIXTURES_TREE_SHA256, PUBLICATION_TREE_SHA256"
  - "pc_allowlist: CORPUS_FOLDER and load_trace_calls(repo_root, evidence_folder=CORPUS_FOLDER), so a rerun baseline never enters the refusal corpus"
  - "README: a Comparing a rerun with the committed row subsection, a pinned-guard bullet, three Layout lines"
affects: [03-06, phase-04]

actuals:
  tokens: 19700
  tasks: 3
  commits: 6
plan_head_before: 597fb0f225092ff0446240c949f1f630f52badb1
plan_head_after: d76431d82b2b599db0277540e720d105eeaf0cc0

tech-stack:
  added: []
  patterns:
    - "A comparer that proves itself read-only four ways: write-protected copies, every write primitive patched to raise, whole-tree digests before and after, and a tree that changes mid-run reported as unchanged: no"
    - "Quoted file text is printed on lines of the form `  content: <text>`, so the comparer's own words can be checked for verdict words by cutting everything after that mark"
    - "Pinned digests computed once from a tree for which git diff against the base commit is empty; a deliberate skill fix changes the constant in the same commit"

key-files:
  created:
    - tests/harness/pc_compare.py
    - tests/harness/test_compare.py
    - tests/harness/test_frozen_tree.py
  modified:
    - tests/harness/pc_allowlist.py
    - tests/harness/test_allowlist.py
    - tests/harness/README.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The digest of a whole tree is sha256 over pc_manifest.jsonl_bytes of tree_manifest, taken for the whole folder named by --old and by --new (not only the row folder), before and after the comparison"
  - "--old and --new name a folder that holds the row folder (the dated publication or rerun folder); a symlink, a file, a missing folder, a missing row folder, an odd row id shape and any unknown or missing option are exit 2 with fixed text that echoes nothing"
  - "A file that is absent or malformed is reported per side (absent, unreadable, none) and the run goes on with exit 0; only an unreadable tree is exit 2"
  - "sha.txt paths are compared by digest after a leading helper-state folder is read as ckpt and a leading ledgers folder as ckpt/ledgers; the committed token <repo>/<run> is replaced by <run> in memory before any text-dependent count"
  - "Section caps are the measurer's constants by section name, never the caps printed in a file; strictly greater than the cap is above it"
  - "The pinned digests include references/ and tests/fixtures/ as whole folders, so a stray file in either (for example a Finder file on a developer machine) changes the digest; that is the intended friction"

patterns-established:
  - "Report order: header, digests before, files on one side only, README headings, helper calls, tool calls, byte measurements, the listed, not judged section (snapshots, rules, digests, version, usage), digests after, unchanged lines, the modes-and-timestamps sentence"

requirements-completed: [EVID-06, HARN-13]

coverage:
  - id: C1
    description: "The comparer opens both evidence trees for reading only; it exits 0 whenever both trees were readable and 2 when a tree is missing, a file, a symlink, lacks the row folder or the usage is wrong, with fixed text that never echoes a path or an argument; it prints no per-row verdict"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (ExitTests, BadInputTests, VocabularyTests)"
        status: pass
    human_judgment: false
  - id: C2
    description: "Tree digests of both whole trees are printed before and after and are identical for an untouched run; the digest changes for a changed byte, a renamed file, an added empty folder and a changed symlink target, and not for modes, timestamps or the root name; a tree changed during the run prints new unchanged: no and still exits 0"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (TracerTests, DigestTests, DigestSensitivityTests, ReadOnlyTests)"
        status: pass
    human_judgment: false
  - id: C3
    description: "Read-only is proven four ways: write-protected copies compare with exit 0; with builtins.open in any write mode, os.replace, rename, remove, unlink, rmdir, mkdir, makedirs, utime, chmod and the shutil copy, copy2, copyfile, copytree, move and rmtree functions patched to raise the comparison still succeeds and none is reached; the real committed publication folder has equal digests before and after; and git status for tests/evidence is empty after the suite"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (ReadOnlyTests)"
        status: pass
    human_judgment: false
  - id: C4
    description: "The comparison lists, per D-07: files and folders on one side only in both directions (sorted), row README headings that differ with counts, helper-call totals with the per-verb counts and the sorted exit-code multiset from wrapper-calls.log, tool-call counts per tool name with the Calls header and the ERROR and REFUSAL/DENIAL flag counts for s1, s2 and s3 (a trace on one side only is reported on that side), and byte measurements read from both shapes with a total of 4096 within the cap, 4097 above it, and each section at its cap within and one byte more above"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (StructuralTests, MeasurementTests)"
        status: pass
    human_judgment: false
  - id: C5
    description: "Everything else is listed and never judged: sha.txt paths whose digests differ after helper-state and ledgers read as ckpt, paths on one side only, the tools.txt rule difference with both counts, digests.txt, claude-version.txt and usage.txt as quoted content; the committed token <repo>/<run> equals <run> before text-dependent counts"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (StructuralTests)"
        status: pass
    human_judgment: false
  - id: C6
    description: "Against the committed row 1 and a fake-pipeline new side the report is non-empty, names the rerun-only files (mechanical-checks.md, usage.txt, model-id.txt, isolation-mode.txt, harness-version.txt, s1-work-prompt.md, s1-work-full-trace.md, settings.json, the s3 files, snap-3-after-resume and a manifest in each snapshot) as present on the rerun side only, exits 0, and the comparer's own words hold none of the verdict words (quoted content is outside that check)"
    requirement: EVID-06
    verification:
      - kind: unit
        ref: "tests/harness/test_compare.py (TracerTests, VocabularyTests)"
        status: pass
    human_judgment: false
  - id: C7
    description: "SKILL.md is at or under 12,000 bytes (11,994 now) by a permanent test, and pinned sha256 values hold for SKILL.md, references/, tests/fixtures/ and tests/evidence/publication-2026-10-20, computed from the tree for which git diff 56e155c over those paths was empty"
    requirement: HARN-13
    verification:
      - kind: unit
        ref: "tests/harness/test_frozen_tree.py (SkillSizeTests, FrozenTreeTests)"
        status: pass
    human_judgment: false
  - id: C8
    description: "The allowlist corpus is the committed publication evidence only: load_trace_calls reads the publication folder by default, a rerun folder next to it is not loaded, another evidence_folder name reads that folder, and the measured counts (336 calls, 32 traces, 22 folders, refusals 47, 34 and 6, 87 in total) and canonical_commands are unchanged"
    requirement: HARN-13
    verification:
      - kind: unit
        ref: "tests/harness/test_allowlist.py (CorpusScopeTests, RefusalCorpusTests)"
        status: pass
    human_judgment: false
  - id: C9
    description: "Zero model calls: 1117 tests (1048 before) pass on the PATH interpreter (3.14) through the selftest shim (0 model calls, OK (skipped=3)), through the bash 3.2 shim form with a tripwire claude on PATH (tripwire log empty), and on the system Python 3.9.6; the leak gate reports 0 findings over 71 files and gitleaks dir over tests/harness is clean"
    requirement: HARN-13
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 1117 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p 'test_*.py' (Ran 1117 tests, OK (skipped=3))"
        status: pass
    human_judgment: false
  - id: C10
    description: "The phrase that all new code sits under tests/harness is checked by a git command in the phase gate and not by a permanent test, because later phases legitimately add files elsewhere"
    requirement: HARN-13
    verification:
      - kind: other
        ref: "backstop: phase gate item 5, git diff --name-only 799ccab HEAD -- . ':!.planning' lists only files under tests/harness (run, green)"
        status: pass
    human_judgment: false

# Metrics
duration: not recorded (start time was not captured)
completed: 2026-10-29
status: complete
---

# Phase 3 Plan 05: The read-only comparer, the pinned frozen trees and the zero-token phase gate Summary

**`pc_compare.py` lines a rerun up against the committed row 1 and prints facts only: files on one side only, README heading differences, helper-call and tool-call counts, byte measurements against the cap (both file shapes), and a listed-not-judged section, with sha256 digests of both whole trees before and after to show nothing was touched. SKILL.md (11,994 of 12,000 bytes), references/, tests/fixtures/ and the committed publication evidence are now pinned by digest in a permanent test, and the allowlist corpus is scoped to the publication folder so filing a new baseline cannot break it. No model was called.**

## Performance

- **Duration:** not recorded
- **Completed:** 2026-10-29
- **Tasks:** 3 (each a `test(03-05)` commit then a `feat(03-05)` commit; Task 1 is the tracer)
- **Files:** 3 new (`pc_compare.py`, `test_compare.py`, `test_frozen_tree.py`), 4 modified (`pc_allowlist.py`, `test_allowlist.py`, `README.md`, `.planning/REQUIREMENTS.md`)
- **Suite:** 1048 tests before, 1117 after (54 in `test_compare.py`, 9 in `test_frozen_tree.py`, 6 in `test_allowlist.py`), `OK (skipped=3)`, 0 model calls, on Python 3.14 through the shim and on the system 3.9.6

## Accomplishments

- **Task 1, tracer (EVID-06).** `tree_digest` and a first report: the committed row 1 against a new side produced by the fake pipeline gives exit 0, a non-empty list of files on the rerun side only (the five new provenance files, the work-turn prompt and trace, `settings.json`, the s3 files, `snap-3-after-resume` and a manifest in each snapshot), and equal digests before and after for both whole trees.
- **Task 2, the D-07 comparison (EVID-06).** README headings, helper calls (total, per verb, exit-code multiset), tool calls per tool name with header and flag counts for s1, s2, s3, measurements in both shapes with exact boundary behaviour, and the `listed, not judged` section (snapshot digests after `helper-state` and `ledgers` read as `ckpt`, rule difference with counts, digests, version, usage). Four read-only proofs and a vocabulary check on the comparer's own words.
- **Task 3, pins and corpus scope (HARN-13).** Four pinned digests computed from the unchanged tree, the size cap test, `CORPUS_FOLDER` and the scoped loader with its test, the README subsection.

## What the comparer reports for the committed row 1 against the fake pipeline

Sections in order: 1 file only on the old side (`snap-2-after-preclear/auto-memory/MEMORY.md`), 30 entries only on the rerun side; README headings 1 against 4; helper calls total 1 status call on both sides; tool calls s2 48 against 5 (the committed header says 48 calls, 7 flagged), s1 and s3 reported on the rerun side only; measurements 3494 against 321 bytes, none above a cap; snapshot digests; tools rules 28 against 40; version 2.1.304 against 2.1.310. Every one of those is listed and none is judged.

## Task Commits

1. Task 1 tracer: `ae0227f` test, `5e0437c` feat
2. Task 2: `2f31318` test, `d840933` feat
3. Task 3: `1f0e413` test, `d76431d` feat

## Phase gate (zero tokens) results

| # | Check | Result |
|---|-------|--------|
| 1 | `tests/harness/selftest` | green: "0 model calls", `OK (skipped=3)`, 1117 tests (above the 1048 of plan 03-04) |
| 2 | `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p 'test_*.py'` (3.9.6) | green: 1117 tests, `OK (skipped=3)` |
| 3 | bash 3.2 shim form with a tripwire claude | green: exit 0, `claude directories removed from PATH: 1`, the line starting `OK`, tripwire log empty; this run printed `OK (skipped=4)` (one more skip than the PATH-interpreter run; the gate requires only the `OK` line) |
| 4 | `git diff --name-only 56e155c -- SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20` empty, SKILL.md 11,994 bytes | green |
| 5 | `git diff --name-only 799ccab HEAD -- . ':!.planning'` lists only files under `tests/harness`; `git status --porcelain -- tests/evidence` empty | green |
| 6 | leak gate over `tests/harness` and `gitleaks dir tests/harness` | green: 0 findings over 71 files; gitleaks clean |
| 7 | `pc_mine.py --check`, `scripts/test-hooks.sh`, attribution scan of `git log --all` | green: exit 0, 29 PASS lines, 0 attribution hits over 4 patterns |
| 8 | `pc_matrix.py --dry-run --row row1-wrong-binding --budget 2.00` | green: exit 0, output saved below |

Dry-run output kept for bokiko to read at the gate of plan 03-06 (it holds no path):

```
row1-wrong-binding: 3 stages, 2 sessions
  s1: work turn, new session, 15 turns, cap 0.30
  s2: /preclear turn, resumes the s1 session, 60 turns, cap 1.30
  s3: fresh resume, new session, 15 turns, cap 0.40
worst case 2.00 USD
allowlist 40 rules
model claude-sonnet-5-5
destination tests/evidence/rerun-2026-10-28-claude-sonnet-5-5
gate ok: the runs root, the row sources and the destination name are usable
```

The gate is green, so the paid run of plan 03-06 may be offered to bokiko.

## Deviations from Plan

### Auto-fixed Issues

None in code. One plan expectation did not hold against the fake pipeline:

**1. [Rule 1 - Test expectation] "lists no file as only on the old side" is false for the fake pipeline**
- **Found during:** Task 1 (the first full run of the tracer)
- **Issue:** the committed row 1 has `snap-2-after-preclear/auto-memory/MEMORY.md` (the real model wrote a memory index); the scripted claude writes only the topic file, so that one file really is present on the old side only. The plan's Test 2 said no file is listed on the old side.
- **Fix:** the test checks each direction against an independent `os.walk` of the two row folders (old-only equals old minus new, rerun-only equals new minus old) and checks that every named rerun-only file is in the rerun list. The comparer was not changed: it correctly lists the one file.
- **Files modified:** `tests/harness/test_compare.py` (written that way from the first commit)
- **Commit:** `ae0227f`

### Notes on the plan's wording

- Several Task 2 tests (the read-only proofs, digest sensitivity, bad inputs, malformed files) passed on their first run, because Task 1's module already read in read mode only and already validated its inputs. They are regression guards and were committed with the red step as written; the other 20 Task 2 tests failed for the stated reasons (a missing section, key or function).
- The new file test for Task 3 `test_canonical_commands_are_unchanged_by_the_scope` calls the new `evidence_folder` argument for each folder under `tests/evidence`, so it is red before the change and compares the scoped list with the all-folders list afterwards.
- The shim-form gate printed `OK (skipped=4)` where the PATH-interpreter run prints `OK (skipped=3)`; no test fails and the gate only needs the `OK` line.

### Threat flags

None. The comparer adds no network endpoint, auth path or write route; it reads two trees and prints. The scoped loader only narrows what an existing reader walks.

## Authentication gates

None. No real `claude` was started; the only claudes executed were the scripted fake and the tripwire of `pc_testutil`.

## Known Stubs

None. Every printed value is read from files on disk; a missing or malformed file is reported as absent, unreadable or none.

## Self-Check: PASSED

- Created files exist: `tests/harness/pc_compare.py`, `tests/harness/test_compare.py`, `tests/harness/test_frozen_tree.py`.
- Commits `ae0227f`, `5e0437c`, `2f31318`, `d840933`, `1f0e413`, `d76431d` are ancestors of HEAD (six commits since the plan's base `597fb0f`, measured from the ledger); the diff against `799ccab` outside `.planning` lists only files under `tests/harness/`; `SKILL.md`, `references/`, `tests/fixtures/` and `tests/evidence/` are unchanged (`git status` for `tests/evidence` is empty); no commit carries an attribution trailer and no hook was bypassed.
- STATE.md and ROADMAP.md were not touched; `.planning/REQUIREMENTS.md` has EVID-06 and HARN-13 marked complete (checkboxes and table rows).
