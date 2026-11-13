---
phase: 03-walking-skeleton-row-1
plan: 03
subsystem: testing
tags: [write-boundary, git-read-only, snapshots, trace-paths, helper-calls, seeded-failures, checkpoint-stub, python-stdlib, unittest]

requires:
  - phase: 03-walking-skeleton-row-1
    provides: "pc_row1 (run_row, run_stage, take_snapshot, stage records, snapshots snap-0-setup to snap-3-after-resume, raw/run.json), pc_testutil (make_scripted_claude, default_row1_stages, stages_with, RowRig)"
  - phase: 02-model-free-foundation-and-stub
    provides: "pc_stream (tool_calls, denial_report), pc_manifest (tree_manifest, jsonl_bytes, capture_git_status, git environment), pc_mine.parse_log, pc_allowlist (split_compound, strip_wrappers), pc_runroot.write_exclusive, the stub and the logging wrapper"
provides:
  - "pc_checks: load_manifest, diff_manifests, outside_changes, write_boundary, executed_bash_commands, trace_write_paths, bash_mentions, default_memory_path, memory_probe, git_state, capture_boundary_state, load_git_state, git_mutations, ledger_digests, slice_log, helper_calls, first_status_text, session_facts, compute_facts, breaches, CheckError"
  - "pc_row1.breach_outcome: the checks run after every stage and in finish; a breach is exit 11 with counts only and nothing filed"
  - "raw/setup.git.json and raw/s1.git.json, raw/s2.git.json, raw/s3.git.json (one per boundary, exclusive)"
  - "pc_testutil seeds: seed_outside_write, seed_trace_write, seed_git_commit, seed_git_branch, seed_denied_git_add, seed_outside_mention"
  - "checkpoint_stub: update refuses a body line that is a checkpoint marker (review WR-03), exit 4"
  - "README: Layout lines for pc_checks.py and test_checks.py and a What the mechanical checks measure subsection"
affects: [03-04, 03-05, 03-06]

actuals:
  tokens: 26032
  tasks: 3
  commits: 6
plan_head_before: e55d3399c686f4c7579e752fbbd18465ade7a15b
plan_head_after: c232d4ca24bd90138218b6cd92b0cd8f69362b8e

tech-stack:
  added: []
  patterns:
    - "Facts, not verdicts: every count is derived from snapshots, stream structure and logs on disk; only a concrete write outside the approved roots or a git mutation is a breach (exit 11), everything else is left for the reviewer"
    - "Three independent nets for the same risk (snapshot diff, executed Write and Edit paths, one lstat of the default memory folder), each proven by a seeded failing run and silent on the clean control"
    - "Seeds are small helpers over the scripted claude's existing operations; they return a changed copy of the stage list"

key-files:
  created:
    - tests/harness/pc_checks.py
    - tests/harness/test_checks.py
  modified:
    - tests/harness/pc_row1.py
    - tests/harness/pc_testutil.py
    - tests/harness/checkpoint_stub.py
    - tests/harness/test_stub_cli.py
    - tests/harness/data/branch-table.md
    - tests/harness/README.md

key-decisions:
  - "The checks run after every stage, not only in finish, so a breach found after s2 ends the row before s3 is launched and nothing more is spent; finish repeats the check for the last stage"
  - "A run root the checks cannot read (CheckError) is a broken harness and is also exit 11 with fixed text, because a run whose isolation cannot be shown must not be filed"
  - "git_mutations takes the largest staged count of any state (not the sum), so one staged file that persists across stages counts once"
  - "The wrapper path (the helper itself) is not counted as an outside path mention, so a clean run reports zero for every count including mentions"

patterns-established:
  - "compute_facts(run_root, config_dir) returns plain JSON values with the names snapshots, stages, streams, write_boundary, trace_writes, bash_mentions, memory_probe, git, ledgers, helper_calls, session, denials; plan 03-04 renders them"
  - "Boundary git state files: raw/<name>.git.json with head, branch, refs_digest, gitdir_digest, staged"

requirements-completed: [HARN-09]

coverage:
  - id: C1
    description: "The write boundary is derived from the snapshots alone: consecutive pairs and the first against the last are diffed by path and the whole 64-hex digest (a digest differing only in the last character is a change, kind and size and link target also count), a path outside the approved roots project, ckpt and auto-memory is listed except exactly wrapper/calls.log, the root match is component-aware (project-other, project.bak, ckpt2 and auto-memory-old are outside), directory entries and removals count, and load_manifest is strict"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (BoundaryTests)"
        status: pass
    human_judgment: false
  - id: C2
    description: "Three seeded runs against the scripted claude each report a non-zero count and end run_row with 11, fixed text holding a count and no path, the raw bytes and snapshots on disk and no later stage launched: a file written under the run root outside the approved roots in s2 (snapshot path), a Write tool call to a file outside the run root that was really written (trace path, invisible to the snapshot), a commit in the project (git path); an executed git branch also ends with 11; the clean default run reports zero for every count and returns 0"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (SeededBreachTests, TracerTests)"
        status: pass
    human_judgment: false
  - id: C3
    description: "Write, Edit, NotebookEdit and MultiEdit paths are resolved with realpath (relative against the project, links and dot-dot followed) and listed only when the call was executed (not in the structured denial union); output is run-root relative text or the fixed token outside-run-root; Bash absolute-path words outside the roots and write-capable programs are listed as counts and names and never decide a breach"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (TraceTests, MentionTests)"
        status: pass
    human_judgment: false
  - id: C4
    description: "Git read-only is state-based: HEAD, branch, a digest of for-each-ref and a digest of the git folder without index and index.lock are captured at setup and after every stage, staged entries are counted from the porcelain text, executed mutating forms are counted (the full list of the plan, branch with a name or a mutating flag, symbolic-ref with two arguments, worktree add or remove, any --output argument, global options such as -C and -c skipped, timeout and env prefixes unwrapped); a denied mutating call and an index refresh by a plain status are not counted"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (GitTests, SeededBreachTests)"
        status: pass
    human_judgment: false
  - id: C5
    description: "The default auto-memory folder is looked at with a single lstat on a constructed path; the config folder is never opened, listed, walked or snapshotted (tests patch open, listdir, scandir and walk to raise under it and count exactly one lstat); a present folder counts as one write outside the approved roots; a planted sentinel name never appears in any output"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (MemoryProbeTests)"
        status: pass
    human_judgment: false
  - id: C6
    description: "Helper-call facts are four counts from structure only (attempted, executed from the stage's slice of wrapper/calls.log using the stage records' cumulative call counts, denied for single-part denials, compound refusals for denied multi-part commands naming the helper) with correlated yes, no or UNCONFIRMED; the default s2 gives 2, 1, 1, 0 and yes; a call made in s1 is never counted for s2"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (HelperCallTests)"
        status: pass
    human_judgment: false
  - id: C7
    description: "Ledger digests (ledger A, ledger B, binding file, ledger-roots file, checkpoint log) are compared first snapshot against last by sha256 and reported unchanged, changed, absent-before, absent-after or absent-both; a changed ledger is a finding and not a breach; session facts report init and result session agreement, denial ids per stage and three status questions (UNCONFIRMED without a status call); reply text claiming no writes changes no count"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (LedgerFactTests, SessionFactTests)"
        status: pass
    human_judgment: false
  - id: C8
    description: "compute_facts reads only files in the run root and is repeatable (equal results on a second call, including after the breach ended the row); the per-boundary git state files exist and are created exclusively (a second capture with an existing name raises FileExistsError)"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_checks.py (RefileFactsTests, TracerTests)"
        status: pass
    human_judgment: false
  - id: C9
    description: "The stub's update refuses a body holding a line equal to the end marker or matching a begin marker with exit 4 and the fixed message, after the stale-hash check and before any write: the folder tree digest is unchanged (no conflict file, no audit line), lint still reports OK, show prints all six sections and a later valid update succeeds; a marker inside a longer line and one-character variants are accepted; the heading refusal and the usage error are unchanged; the branch table has the STUB-ONLY row in position and the replay of the 15 recorded calls, concurrency and wrapper suites pass"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/test_stub_cli.py (MarkerLineTests) and tests/harness/test_branch_table.py"
        status: pass
    human_judgment: false
  - id: C10
    description: "Zero model calls: 992 tests (926 before) pass on the PATH interpreter through the selftest shim (0 model calls, OK (skipped=3)) and on the system Python 3.9.6; the leak gate reports 0 findings over 66 files, gitleaks dir over tests/harness is clean, pc_mine --check is green, and SKILL.md, references/, tests/fixtures/ and the publication evidence folder are unchanged"
    requirement: HARN-09
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 992 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p 'test_*.py' (Ran 992 tests, OK (skipped=3))"
        status: pass
    human_judgment: false
  - id: C11
    description: "Assumption A3: the default auto-memory folder name is taken as the project path with every non-alphanumeric character turned into a hyphen under the config folder's projects directory, then memory; if the real build names it differently the single lstat reports absent and misses that breach, so the snapshot and trace paths remain the primary detection"
    requirement: HARN-09
    verification:
      - kind: other
        ref: "backstop: plan 03-06 paid-run checkpoint (the real build's folder name is unobserved)"
        status: unknown
    human_judgment: true
  - id: C12
    description: "Snapshots are taken at stage boundaries only, so a write made and undone inside one stage is invisible to the diff and is covered only by the executed Write and Edit path scan (a Bash-made write that is undone in the same stage is not caught)"
    requirement: HARN-09
    verification:
      - kind: other
        ref: "backstop: stated limit of the design; the README names it"
        status: unknown
    human_judgment: true

# Metrics
duration: not recorded (start time was not captured)
completed: 2026-10-29
status: complete
---

# Phase 3 Plan 03: The mechanical checks - write boundary, git read-only, helper-call facts, and the stub marker-line fix Summary

**The write-boundary and git-read-only claims of row 1 are now mechanical: three independent nets (snapshot diff by full digest, executed Write and Edit paths through realpath, one lstat of the default memory folder) plus git state compared at every boundary, proven by three seeded failing runs that each end the row with exit 11 and by a clean control that reports zero everywhere. The stub's update verb also refuses a body holding a checkpoint marker line (review WR-03). No model was called.**

## Performance

- **Duration:** not recorded
- **Completed:** 2026-10-29
- **Tasks:** 3 (each a `test(03-03)` commit then a `feat(03-03)` commit; Task 1 is the tracer)
- **Files:** 2 new (`pc_checks.py`, `test_checks.py`), 6 modified (`pc_row1.py`, `pc_testutil.py`, `checkpoint_stub.py`, `test_stub_cli.py`, `data/branch-table.md`, `README.md`)
- **Suite:** 926 tests before, 992 after (66 new: 57 in `test_checks.py`, 9 in `MarkerLineTests`), `OK (skipped=3)`, 0 model calls, on both interpreters

## Accomplishments

- **Task 1, tracer (HARN-09, D-03).** `load_manifest` (strict), `diff_manifests` (kind, size, whole digest, link target), `outside_changes` (component-aware, only `wrapper/calls.log` expected), `write_boundary`, `compute_facts` and `breaches`. `pc_row1` runs the checks and turns a breach into exit 11 with counts only. A seeded file under the run root, outside the approved roots, ends the row with 11; the clean run reports zero.
- **Task 2, remaining checks (HARN-09, D-09).** `trace_write_paths`, `bash_mentions`, `memory_probe` (one lstat), `git_state` / `capture_boundary_state` / `git_mutations`, `ledger_digests`, `helper_calls` with `slice_log`, `session_facts`. Six seed helpers in `pc_testutil`. The boundary git state files are written at setup and after every stage.
- **Task 3, stub fix and README (review WR-03).** `verb_update` refuses a marker-bearing body with exit 4 after the stale-hash and heading checks; `note` and `init` are unchanged. A STUB-ONLY branch-table row, the docstring note, and the README subsection.

## compute_facts names (plan 03-04 renders these)

`compute_facts(run_root, config_dir)` returns exactly these keys, all plain JSON values:

| Name | Shape |
|---|---|
| `snapshots` | list of snapshot names found, in order |
| `stages` | list of stage names that have a record (`s1`, `s2`, `s3`) |
| `streams` | stage name to `ok` or `unreadable` |
| `write_boundary` | `count`, `paths` (run-root relative text) |
| `trace_writes` | `count`, `paths` (run-root relative text or `outside-run-root`) |
| `bash_mentions` | `commands`, `outside_path_tokens`, `unparsed_parts`, `write_programs` (name to count) |
| `memory_probe` | `absent`, `present` or `unknown` |
| `git` | `states` (list of `head`, `branch`, `refs_digest`, `gitdir_digest`, `staged`) and `mutations` (`state_changes`, `changed_fields`, `staged`, `executed`, `forms`, `total`) |
| `ledgers` | `names` (`ledger-a`, `ledger-b`, `binding`, `ledger-roots`, `checkpoint-log` to a status) and `unchanged` |
| `helper_calls` | stage name to `attempted`, `executed`, `denied`, `compound_refusals`, `correlated` (`yes`, `no`, `UNCONFIRMED`) |
| `session` | `stages` (per stage `init_session_as_requested`, `result_session_as_requested`, `denial_ids`) and `status_begins_with_session`, `status_holds_s1_prefix`, `status_names_ledger_b` |
| `denials` | stage name to the sorted denial ids |

`breaches(facts)` returns `(id, count)` pairs: `writes-outside-approved-roots` (snapshot paths plus executed trace paths plus one for a present default memory folder) and `git-mutations` (the `mutations.total`).

## Task Commits

1. Task 1 tracer: `d35db0c` test, `f0b8486` feat - write boundary from snapshots, breach to exit 11
2. Task 2: `6475084` test, `0c04651` feat - trace, mention, memory, git, ledger, helper-call and session facts
3. Task 3: `768c59f` test, `c232d4c` feat - marker-line refusal in the stub, branch-table row, README

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] The checks also run after every stage, not only in `finish`**
- **Found during:** Task 1, writing the tracer test
- **Issue:** The plan's tracer test asks for exit 11 with "no later stage launched", but a check that lives only in `finish` runs after the third stage, so a breach in s2 would still fund s3. The threat model (T-03-18, T-03-23) wants a breach to end the row and keep the raw bytes.
- **Fix:** `pc_row1.breach_outcome` is called right after each stage (the stage record, snapshot and git state are already on disk) and again in `finish`. If the stage also failed, its stop line is appended after the breach lines.
- **Files modified:** `tests/harness/pc_row1.py`
- **Commit:** `f0b8486`, extended in `0c04651`

**2. [Rule 2 - Missing critical functionality] A run root the checks cannot read is exit 11**
- **Found during:** Task 1
- **Issue:** `compute_facts` raises `CheckError` on a missing or malformed snapshot, record or git state file. Letting it propagate after money is spent would crash without a verdict; ignoring it would let an unverifiable run be filed.
- **Fix:** `breach_outcome` maps `CheckError` to exit 11 with fixed text (nothing filed, raw files stay).
- **Commit:** `f0b8486`

### Additions inside the plan's intent

- `trace_write_paths` also covers `MultiEdit`; `bash_mentions` also lists `sed -i`, `find -delete/-ok/-execdir` and `gawk/mawk`, and takes an `ignore` list (the wrapper path) so a clean run reports zero mentions; `git_mutations` keeps the most staged entries of any state rather than a sum.
- `compute_facts` adds a `streams` fact (`ok` or `unreadable` per stage) so an unreadable stream is a visible fact and not a crash; an unreadable stream contributes no trace or helper facts.
- `session_facts` reads the helper's own `status` tool-result text (the first executed status call in s2), only to answer three yes or no questions. This is the helper's output, not the model's reply; it is the one place a tool-result text is read, and the plan's "no fact from result text" is kept in spirit (reply text is never read and a test shows a false "no writes" claim changes nothing).

### Test edit between a test commit and its feat commit

In `test_checks.py` (Task 2 feat commit): the clean-control test gained an assertion that the outside-path mention count is 0, which is what led to the `ignore` parameter above (the wrapper path was counted as one mention in a clean run). Nothing else in a test file moved between its test and feat commits.

### Observation, out of scope (not changed)

`checkpoint_stub.append_history` finds the end of the block with a substring search for the end marker, so a body line that merely starts with the marker followed by more text (accepted by the plan, per the one-character-variant rule) could move where `note` cuts. `note` still appends under the History heading it finds afterwards, so this is low impact; the plan scoped the fix to `update` and left `note` unchanged.

## Authentication gates

None. No real `claude` was started; the only claudes executed were the scripted fake and the tripwire of `pc_testutil`.

## Known Stubs

None. Every value shown by the checks is computed from files on disk.

## Threat Flags

None. No network endpoint, auth path or schema was added. The new module only reads (and writes the per-boundary git state files through `pc_runroot.write_exclusive`); the memory probe is one lstat on a constructed path and nothing under the harness config folder is opened, listed or walked.

## Self-Check: PASSED

- Created files exist: `tests/harness/pc_checks.py`, `tests/harness/test_checks.py`.
- Commits `d35db0c`, `f0b8486`, `6475084`, `0c04651`, `768c59f`, `c232d4c` are ancestors of HEAD; `git diff` against the plan's start lists only files under `tests/harness/`; `SKILL.md`, `references/`, `tests/fixtures/` and the publication evidence folder are unchanged; no commit carries an attribution trailer and no hook was bypassed.
- Full suite, leak gate (0 findings over 66 files), gitleaks dir over `tests/harness` and `pc_mine.py --check` all green after the last feat commit.
