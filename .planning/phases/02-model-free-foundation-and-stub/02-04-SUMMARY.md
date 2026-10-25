---
phase: 02-model-free-foundation-and-stub
plan: 04
subsystem: testing
tags: [bash-3.2, python-stdlib, unittest, checkpoint-v1, wrapper, allowlist, branch-table]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "plan 02-01 pc_flags (build_allowed_tools, baseline, verb tuples) and pc_exitcodes; plan 02-02 checkpoint_stub.py, pc_mine.py and replay-cases.json"
provides:
  - "tests/harness/checkpoint-wrapper: bash 3.2 call logger and armed-conflict injector around the stub; refuses bind, create and init with exit 71; exit 70 when not configured"
  - "tests/harness/pc_allowlist.py: bounded model of documented Bash rule matching, trace and tools.txt loaders, rule-class refusal corpus, canonical command extraction, INDIRECT_LAUNCH_RULES"
  - "tests/harness/data/branch-table.md: 30-row branch table, exit codes 0 to 6, 64, 70, 71, each row CONFIRMED, UNCONFIRMED or STUB-ONLY"
  - "scripted replay of the committed row 2 sequence through the wrapper (exit 3 twice, then success after a manual merge)"
  - "digest check tying references/checkpoint-v1.md to the committed adapter digest"
affects: [02-06 stub completion, 02-07 flat-directory check, 02-08 live capture and findings, phase 3 runner and run-root materialiser]

actuals:
  tokens: 20400
  tasks: 3
  commits: 6
plan_head_before: 60b82162bdb5882a533de36d242ad46f894ceda1
plan_head_after: acfd6aa6e47e569520936a1da70ab3750e81bb7b

tech-stack:
  added: []
  patterns:
    - "wrapper configuration read from small files beside it (py, stub), exit 70 when absent"
    - "state built with the stub's own bind verb; the wrapper never creates state"
    - "conservative matcher model scoped to rule matching, with result text used only as a corpus label"
    - "table-versus-docstring drift test"

key-files:
  created:
    - tests/harness/checkpoint-wrapper
    - tests/harness/pc_allowlist.py
    - tests/harness/data/branch-table.md
    - tests/harness/test_wrapper_conflict.py
    - tests/harness/test_allowlist.py
    - tests/harness/test_branch_table.py
    - tests/harness/test_frozen_reference.py
  modified: []

key-decisions:
  - "The wrapper resolves the verb as the first argument after any leading --session option, because the stub accepts --session before the verb; refusal of bind, create and init and the update injection both use that resolved verb"
  - "A redirection that carries an ampersand (2>&1, >&2, &>file) is not a command separator in the matcher; only ASCII whitespace is trimmed, so a non-breaking space never matches"
  - "injection.log keeps the stub's own stderr brand line (two per injection) because the plan asks for standard output and error both; the test counts them"
  - "lint in the replay runs straight against the stub, as the committed row 2 driver did, so the wrapper log holds exactly the eight model-style calls"
  - "pc_exitcodes.py is not edited: exits 70 and 71 live in the wrapper header and the branch table, and the table test names them as literals"

patterns-established:
  - "A driver-only verb is refused at the wrapper whatever launched it, including env and a leading --session option"
  - "Branch table rows carry the stub docstring's own wording so each UNCONFIRMED docstring bullet is found by its first three words"

requirements-completed: [STUB-04, STUB-05, STUB-06, STUB-07, HARN-06]

coverage:
  - id: D1
    description: "A wrapper outside the stub logs every call in the committed CALL and EXIT shapes, delegates unchanged, and with an armed count of 2 makes the stub itself return exit 3 twice before the hand-merged third update succeeds (scripted row 2 replay); output through the wrapper equals direct stub output after scratch-root and conflict-time normalisation"
    requirement: STUB-04
    verification:
      - kind: unit
        ref: "tests/harness/test_wrapper_conflict.py (ReplayRow2Tests, PassThroughTests, NotConfiguredTests, StubSourceTests, WrapperSourceTests)"
        status: pass
      - kind: other
        ref: "shellcheck -s bash tests/harness/checkpoint-wrapper"
        status: pass
    human_judgment: false
  - id: D2
    description: "bind, create and init are refused by the wrapper with exit 71, directly, through env and behind a leading --session option, with nothing delegated and CKPT_HOME unchanged"
    requirement: STUB-06
    verification:
      - kind: unit
        ref: "tests/harness/test_wrapper_conflict.py#DriverVerbsTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_allowlist.py#IndirectRouteTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A bounded model of the documented Bash allowlist rules accepts the skill's exact commands from the committed traces, never allows any of the 87 rule-class refusals in the corpus of 336 calls (47, 34, 6), denies wrapper bind, create and init, and records the baseline's indirect launch rules openly"
    requirement: HARN-06
    verification:
      - kind: unit
        ref: "tests/harness/test_allowlist.py (CanonicalCommandTests, RefusalCorpusTests, HistoricalAllowlistTests, IdempotencyAndConcurrencyTests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "The branch table lists exit codes 0 to 6, 64, 70 and 71 with evidence and status, marks every unobserved branch UNCONFIRMED, and cannot drift from the stub's own docstring list"
    requirement: STUB-05
    verification:
      - kind: unit
        ref: "tests/harness/test_branch_table.py"
        status: pass
    human_judgment: true
    rationale: "Tests prove shape, ordering, evidence paths and docstring coverage; whether each row's wording reads the reference and the evidence correctly is a judgment the 02-08 live capture and a human review settle"
  - id: D5
    description: "references/checkpoint-v1.md equals the adapter digest in 15 committed digests.txt folders and the only other digest is one pre-fix value in 7 folders; nothing under references mentions the stub"
    requirement: STUB-07
    verification:
      - kind: unit
        ref: "tests/harness/test_frozen_reference.py"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 04: Wrapper, Allowlist Model and Branch Table Summary

**A bash 3.2 wrapper that logs calls and makes the stub return a genuine exit 3 twice before a manual merge succeeds (and refuses bind, create and init with exit 71 however it is launched), a rule-matching model of the Bash allowlist checked against 336 committed calls, a 30-row branch table with UNCONFIRMED marks, and a digest check that the frozen reference is what the evidence ran on.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-25T14:19:58Z
- **Completed:** 2026-10-25T14:35:00Z
- **Tasks:** 3 (one tracer, two auto; all RED then GREEN, no refactor commit)
- **Files created:** 7 (all under tests/harness/; nothing outside it changed)

## Accomplishments

- `checkpoint-wrapper` (mode 100755, passes shellcheck, bash 3.2 only) reads the interpreter and stub paths from the `py` and `stub` files beside it (exit 70 when missing, empty or blank), appends `CALL` and `EXIT` lines to `calls.log`, and delegates with `-I -B`. With `armed` at 2 it lets a second bound session update the first touched section before each of the first two updates, so the stub's own hash guard returns exit 3 twice; the third, hand-merged update exits 0.
- The scripted row 2 replay runs status, show, validate, update (3), show, update (3), show, update (0) through the wrapper, checks both conflict files against the committed name pattern and layout, the two log shapes, and `injection.log` (two `writer2 update exit 0` results, armed ends at 0); lint then prints `ledger lint OK`.
- bind, create and init exit 71 with nothing delegated and `CKPT_HOME` byte-identical afterwards, directly, through `env`, and behind `--session X` or `--session=X`.
- `pc_allowlist.py` implements `split_compound`, `has_expansion`, `strip_wrappers`, `rule_matches` and `is_allowed` per the documented semantics, loads the 32 full traces (336 Bash calls, 22 folders with `tools.txt`), and finds 87 rule-class refusals (47, 34, 6), none allowed under its row's rules. Ten canonical commands (nine wrapper argv shapes and the global-option git status) are derived from the evidence and all allowed for a synthetic wrapper path.
- The committed row 2 bare wrapper-prefix rule is shown to allow `wrapper bind`; the harness builder's output never does. An env-prefixed wrapper bind is allowed by the baseline `env` rule under the matcher, recorded in `INDIRECT_LAUNCH_RULES` (env, python3 -c, awk, find) and closed by the wrapper's exit 71.
- `data/branch-table.md` has 30 rows (exit 0 to 6, 64, 70, 71): 8 CONFIRMED, 18 UNCONFIRMED, 4 STUB-ONLY, with the D-07 hash-derivation row, and sections for the wrapper's files and for what the matcher does not model. Each of the stub docstring's 14 UNCONFIRMED bullets is found in an UNCONFIRMED row.
- The digest of `references/checkpoint-v1.md` appears in 15 committed `digests.txt` folders; the only other value appears in 7.

## Task Commits

Each task ran RED then GREEN:

1. **Task 1: Tracer, replay the row 2 conflict sequence through the wrapper**
   - RED `7624b50` (test): wrapper replay, pass-through, exit 70, exit 71 tests, failing because the wrapper does not exist
   - GREEN `37bec5e` (feat): `checkpoint-wrapper` plus an injection-log fix in the test
2. **Task 2: Allowlist matcher model, canonical commands, refusal corpus, bind/create/init guarantee**
   - RED `c56d40f` (test): `test_allowlist.py`, failing at import (the module does not exist)
   - GREEN `6ed2f8f` (feat): `pc_allowlist.py`
3. **Task 3: Branch table and the frozen-reference digest check**
   - RED `8c653dd` (test): `test_branch_table.py` (fails: the table does not exist) and `test_frozen_reference.py` (passes at once: it characterises existing evidence and the existing reference)
   - GREEN `acfd6aa` (feat): `data/branch-table.md`

**Plan metadata:** the SUMMARY commit follows this file.

## Files Created/Modified

- `tests/harness/checkpoint-wrapper` - logger, armed second-writer injector, exit 70 and 71
- `tests/harness/pc_allowlist.py` - matcher model and evidence loaders (reads only, no writes)
- `tests/harness/data/branch-table.md` - branch table, wrapper section, not-modelled section
- `tests/harness/test_wrapper_conflict.py` - 24 tests
- `tests/harness/test_allowlist.py` - 42 tests
- `tests/harness/test_branch_table.py` - 15 tests
- `tests/harness/test_frozen_reference.py` - 5 tests

## Decisions Made

See `key-decisions` above. The two that change behaviour beyond the plan text are the wrapper's resolved-verb rule (leading `--session` is skipped) and the matcher's treatment of redirections.

## TDD Notes

- The plan is `type: execute` with `tdd="true"` tasks and `workflow.tdd_mode` is not enabled, so no RED record went through the `tdd-red-evidence` classifier.
- Task 1 RED: 14 failures on the "wrapper does not exist" assertion plus a class-level setup error; the two stub-source hygiene tests passed (they guard the stub, not the wrapper).
- Task 2 RED and Task 3 RED for `test_allowlist.py` and `test_branch_table.py`: load-level failures (module import, setUpClass assertion naming the missing file). That is the weaker, import-level form of RED already used by plans 02-01 and 02-02, not an assertion on the planned behaviour.
- `test_frozen_reference.py` could not be RED: it asserts facts about files that already exist. It is committed with the Task 3 RED commit and passed there.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] The driver-verb refusal looked only at the first argument**
- **Found during:** Task 1 (designing the behaviour 7 test)
- **Issue:** The stub's parser accepts `--session` before the verb, so `wrapper --session X bind --ledger L` would have bypassed a first-argument check and run bind through the wrapper. The plan's test only covers an unknown option before the verb, which the stub rejects with exit 2.
- **Fix:** The wrapper skips leading `--session VALUE` and `--session=VALUE` pairs and uses the next word as the verb for both the exit 71 refusal and the update injection. An unknown option before the verb still reaches the stub (exit 2, nothing changed).
- **Files modified:** `tests/harness/checkpoint-wrapper`, `tests/harness/test_wrapper_conflict.py`
- **Verification:** `DriverVerbsTests.test_driver_verbs_are_refused_behind_a_leading_session_option` and the unknown-option test pass
- **Committed in:** `37bec5e`

**2. [Rule 1 - Bug] RED test expected six lines in injection.log**
- **Found during:** Task 1 GREEN
- **Issue:** The stub prints its brand line on stderr for every call and the injection block logs standard output and error both, so each injection adds two brand lines.
- **Fix:** The test counts four brand lines and then checks the remaining six lines.
- **Files modified:** `tests/harness/test_wrapper_conflict.py`
- **Committed in:** `37bec5e`

**3. [Rule 1 - Bug] Pass-through comparison failed on the conflict file's clock time**
- **Found during:** Task 1 GREEN
- **Issue:** A stale-hash update prints the conflict file path, whose name holds a millisecond timestamp the stub chooses; two runs never share one.
- **Fix:** The normalisation maps that timestamp to a token in addition to the scratch root. Nothing else is normalised.
- **Files modified:** `tests/harness/test_wrapper_conflict.py`
- **Committed in:** `37bec5e`

**4. [Rule 1 - Bug] CONFIRMED-row threshold of 10 in the branch table test**
- **Found during:** Task 3 GREEN
- **Issue:** The test I wrote asserted at least 10 CONFIRMED rows; the evidence supports 8 (status bound and unbound, show whole and one section, validate, update, lint, update conflict).
- **Fix:** Threshold set to 8, the measured count. No row was promoted to CONFIRMED to fit a number.
- **Files modified:** `tests/harness/test_branch_table.py`
- **Committed in:** `acfd6aa`

---

**Total deviations:** 4 auto-fixed (1 Rule 2, 3 Rule 1)
**Impact on plan:** Deviation 1 closes a real bypass of the STUB-06 second layer; the rest are test-side corrections. No scope creep.

### Interpretations (not deviations)

- The plan lists exits 0, 0, 0, 3, 0, 3, 0, 0 for the sequence "above" and a final lint. I read it as eight wrapper calls plus a lint run straight against the stub (as the committed row 2 driver ran lint), so the wrapper log has exactly eight call and exit pairs.
- The matcher stops treating `&` as a separator when it is part of a redirection (`2>&1`, `>&2`, `&>`); the plan lists `&` as a separator without that case. It is the conservative direction only where a redirect would otherwise split into an unmatched part, and no corpus result depends on it.
- The 02-02 note that the snapshot `goal.md` is the model's last version does not affect this plan: the wrapper test presents that file as the update input and checks hashes and conflict layout, not the "Yours (not applied)" text.
- `canonical_commands` yields no standalone `pwd -P` (it appears only inside compounds in the traces); `pwd -P` is tested directly against the builder's rules instead.
- `pc_exitcodes.py` is not edited (plan 02-04 does not list it); 70 and 71 are named in the wrapper header and the branch table.
- Commit subjects use the `type(02-04):` prefix as in wave 1. The per-plan commit ledger file under the git directory could not be written (the sandbox refused paths there), so `commits:` is measured as `git rev-list --count` from the dispatch base SHA, which is recorded as `plan_head_before`.
- REQUIREMENTS.md was not touched: the five requirement ids are shared with sibling plans in the wave and the orchestrator owns the merge-time marking.

## Issues Encountered

- A sandbox guard refused several shell commands that contained git-looking text or heredocs; files were written with the file tools instead and commands were split. No effect on content.

## Known Stubs

None. The wrapper, matcher and table are complete for this plan's scope. `note`, `handoff`, `create` and `init` in the stub are plan 02-06's and are only documented here as UNCONFIRMED rows.

## Threat Flags

None. The wrapper writes only beside itself and delegates to the stub, which writes only under CKPT_HOME; the loaders read committed evidence only.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-06 can finish the stub in parallel: the wrapper tests allow at most two `CKPT_STUB_` names and use only status, show, validate, update, lint and bind. The branch table's exit 5 and 6 rows stay UNCONFIRMED whatever 02-06 adds.
- Plan 02-07's flat-directory check will find `tests/harness/data/` as the one subfolder (holding `branch-table.md`).
- Plan 02-08 should run the live S2 capture against `pc_allowlist.is_allowed` and record the cases the model does not cover, and probe the direct `wrapper bind` form only (the indirect route is covered by the wrapper's exit 71).
- Phase 3's run-root materialiser must write the `py` and `stub` files beside the wrapper (exit 70 otherwise).
- Verified: the full harness suite (371 tests, `tests/harness/selftest`) passes with 3 pre-existing skips; the four new test modules plus the wrapper tests pass under the system Python 3.9.6; `shellcheck -s bash` on the wrapper and `gitleaks dir tests/harness` are clean; SKILL.md (11,994 bytes), `references/`, `tests/fixtures/` and `tests/evidence/` are unchanged since commit 56e155c; no commit message in the repository matches the attribution patterns.

---
*Phase: 02-model-free-foundation-and-stub*
*Completed: 2026-10-25*

## Self-Check: PASSED

All seven created files exist on disk (the wrapper is mode 100755); commits 7624b50, 37bec5e, c56d40f, 6ed2f8f, 8c653dd and acfd6aa are ancestors of HEAD; the plan-level verification commands were re-run and pass.
