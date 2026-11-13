---
phase: 02-model-free-foundation-and-stub
plan: 07
subsystem: testing
tags: [python-stdlib, unittest, bash-3.2, readme, hygiene, exit-codes, zero-token]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "plans 02-01 to 02-06: the selftest shim, pc_flags, pc_exitcodes, pc_runroot, the stub, the wrapper, the branch table and every test module"
provides:
  - "tests/harness/test_imports.py: stdlib-by-origin import scan, 3.9 parse, 3.10-plus construct checks, stem-versus-stdlib shadowing, naming rule, single-file stub check"
  - "tests/harness/test_bash_shims.py: shebang discovery, executable bit, bash -n, twelve forbidden-construct patterns with a synthetic case each, shellcheck, a real run of selftest under the system bash that records the bash version"
  - "tests/harness/test_exitcode_agreement.py: exit literals outside pc_exitcodes proved equal by running the allocator, the stub and the wrapper"
  - "tests/harness/README.md: the stranger guide whose first command is tests/harness/selftest"
  - "tests/harness/test_readme.py: README versus code (flag table, exit-code table, switch table, isolation line, layout, hygiene) and the PENDING_SPIKE_FILES constant that plan 02-08 imports"
affects: [02-08, phase-03, phase-04]

actuals:
  tokens: 15800
  tasks: 2
  commits: 3
plan_head_before: bb60727c57881f619a35add5ac638fb01a9282fe
plan_head_after: eefdaaa2f5e059474f633ace8ece46080d9e9616

tech-stack:
  added: []
  patterns:
    - "Hygiene tests classify imports by origin under the running interpreter's stdlib paths, never by a name list"
    - "README tables sit between begin and end markers and are compared with the code by exact text or parsed rows"
    - "Forbidden-path needles assembled from fragments; the host name is read at run time and compared only by boolean checks"

key-files:
  created:
    - tests/harness/test_imports.py
    - tests/harness/test_bash_shims.py
    - tests/harness/test_exitcode_agreement.py
    - tests/harness/README.md
    - tests/harness/test_readme.py
  modified:
    - .planning/REQUIREMENTS.md

key-decisions:
  - "pc_exitcodes.py was not edited: the wrapper's 70 and 71 stay out of it (02-04 chose that), and test_exitcode_agreement runs the wrapper to prove both and proves they collide with no constant"
  - "The README exit-code table has one row per integer constant, so the STUB_ rows for 0 and 2 show the harness meaning (describe() returns the harness text on shared numbers); the prose under the table says so"
  - "PENDING_SPIKE_FILES is a module-level tuple of paths relative to tests/harness, so plan 02-08's fixture test can import it"
  - "A .pyc inside a __pycache__ folder is ignored by test_readme's stray-file check (it is gitignored); the phase gate's find still requires no __pycache__ at all"

patterns-established:
  - "Two HTML-comment anchors in the README (login step, further spike pointers) mark where plan 02-08 adds text without touching the tables"

requirements-completed: [HARN-14]

coverage:
  - id: D1
    description: "Every Python file under tests/harness imports only standard library (by origin), sibling modules or built-ins, parses at feature version 3.9, uses no tomllib, no stdlib_module_names, no zip strict and no parenthesized multi-item with; the stub imports no pc_ module; no stem shadows a standard-library name; the naming rule holds"
    requirement: HARN-14
    verification:
      - kind: unit
        ref: "tests/harness/test_imports.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "selftest and checkpoint-wrapper are executable, pass bash -n, shellcheck -s bash, hold none of the twelve forbidden constructs; each construct is caught in a synthetic shim; selftest runs to exit 0 under the system bash 3.2.57 beside a tripwire claude with links to python3 and git, tripwire log empty"
    requirement: HARN-14
    verification:
      - kind: unit
        ref: "tests/harness/test_bash_shims.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "The allocator's second call exits RUNROOT_COLLISION (16); the stub exits STUB_NO_CKPT_HOME (64) without CKPT_HOME and STUB_USAGE (2) on an unknown verb; stub and allocator constants equal the pc_exitcodes mirrors; the wrapper exits 70 unconfigured and 71 for bind, create and init"
    requirement: EVID-07
    verification:
      - kind: unit
        ref: "tests/harness/test_exitcode_agreement.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "The stranger's whole path: tests/harness/selftest under the system bash with a tripwire claude first on PATH runs all 588 tests to OK (3 skipped), tripwire log never created; the same full discovery passes under the system 3.9.6 interpreter and the PATH 3.14.7 interpreter"
    requirement: EVID-07
    verification:
      - kind: command
        ref: "tests/harness/selftest (tripwire run, 560 tests at tracer time, 588 after the README tests)"
        status: pass
      - kind: command
        ref: "/usr/bin/python3 -I -B -m unittest discover -s tests/harness -t tests/harness"
        status: pass
    human_judgment: false
  - id: D5
    description: "README starts with the selftest command, states what a green run proves and does not prove, the requirements, the knobs, the stub, exit codes, the pinned flag table, the isolation claim and one-time login with the Keychain warning, spike spend pointer, replacement tokens, platforms and layout; every table and the isolation line equal the code"
    requirement: EVID-07
    verification:
      - kind: unit
        ref: "tests/harness/test_readme.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "Whether the README reads clearly to a stranger who has never seen the repository"
    requirement: EVID-07
    human_judgment: true
    rationale: "Tests prove the README equals the code and says the required things; clarity for a first-time reader needs a human read"

duration: not captured
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 07: Stranger Path, Hygiene Tests and README Summary

**The stranger's one command, `tests/harness/selftest`, runs all 588 tests green under bash 3.2 with a tripwire `claude` first on PATH and under both a 3.9 and a 3.14 interpreter; hygiene tests prove stdlib-only imports, no shadowing, bash 3.2-safe shims and exit-code agreement; and a README whose three tables and isolation line are compared with the code at every run puts that command first.**

## Performance

- **Duration:** not captured (start time was not recorded at launch)
- **Completed:** 2026-10-25
- **Tasks:** 2 (one tracer, one auto), 3 commits plus the SUMMARY commit
- **Files:** 5 created under `tests/harness/`, 1 planning file modified
- **Suite:** 522 tests at the wave base, 560 after Task 1, 588 after Task 2 (3 skipped, the APFS ones); about 65 s under the shim, about 85 s under the system 3.9.6

## Accomplishments

- `test_imports.py` (17 tests): the classifier decides by where a module lives under the running interpreter, so `json`, `fcntl` and `unittest` pass and a made-up name fails; the scan is proven on synthetic files for a non-standard import, a relative import, `stdlib_module_names`, `zip` with the new keyword, a `match` statement and a parenthesized multi-item `with` (an extra guard beyond the plan, because the 3.9 parse alone accepts it).
- `test_bash_shims.py` (11 tests): `selftest` and `checkpoint-wrapper` are found by shebang; twelve patterns (including array assignment) each fire on a synthetic line; `shellcheck -s bash` ran and passed (shellcheck is installed here); the run test executes the real shim under the system bash 3.2.57 and prints the version.
- `test_exitcode_agreement.py` (10 tests): runs the CLIs, compares the stub's own `EXIT_*` constants with the `STUB_*` mirrors, and also covers the wrapper's 70 and 71, which `pc_exitcodes` deliberately does not hold.
- `README.md` and `test_readme.py` (28 tests): see Task 2 below.
- Tracer: the real shim with a tripwire `claude` first on PATH ran the full suite to `OK` with the tripwire log never created (the file does not exist), also in the layout where the tripwire shares a directory with python3 and git.

## Task Commits

1. **Task 1 (tracer): hygiene tests, then the stranger's real command**
   - `f7f9ddf` (test): `test_imports.py`, `test_bash_shims.py`, `test_exitcode_agreement.py`
2. **Task 2: README tied to the code, and the phase gate**
   - `438398d` (test, RED): `test_readme.py`
   - `eefdaaa` (feat, GREEN): `README.md` with the three tables filled from the code

**Plan metadata:** the SUMMARY and REQUIREMENTS commit follows this file.

## Phase gate results (model-free, no login, no spend)

- `tests/harness/selftest` exits 0, banner present, `OK`, not "Ran 0 tests"; 588 tests, 3 skipped.
- Tripwire run: full suite under `/bin/bash` shebang with a tripwire `claude` first on PATH, `OK`, tripwire log not created.
- Full folder under the system Python 3.9.6: `OK` (588, 3 skipped). Under the PATH Python 3.14.7: `OK` (via the shim).
- `pc_leakgate.py scan tests/harness`: 43 files, 0 findings. `gitleaks dir tests/harness`: no findings.
- Frozen paths (`SKILL.md`, `references`, `tests/fixtures`, `tests/evidence`) unchanged since 56e155c; `SKILL.md` is 11,994 bytes (cap 12,000).
- No `.log`, `.pyc` or `__pycache__` under `tests/harness`; no attribution trailer in any commit message (pattern file matched 0 lines over `git log --all`).

## Decisions Made

See `key-decisions` above. The plan's note that `pc_exitcodes.py` might gain 70 and 71 was left unused: the table lists every constant the module holds, and the wrapper codes get prose plus a test that runs the wrapper.

## TDD Notes

- The plan is `type: execute` with `tdd="true"` tasks and `workflow.tdd_mode` is not enabled, so the `tdd-red-evidence` classifier was not required; RED was taken from real `unittest` runs.
- **Task 1 (unexpected green, investigated):** the three modules are guard tests over files that already exist, so they passed on first run, as the plan's reversibility note anticipates. The scanners are not vacuous: each has synthetic positive cases that fail the scan (non-standard import, each forbidden bash construct, a `match` statement and so on). Task 1 therefore has a `test(02-07)` commit and no `feat` commit, a TDD gate gap by shape.
- **Task 2 RED (semantic assessment):** with the README present but its three generated blocks still holding placeholders, `test_readme.py` ran 28 tests and 4 failed on the planned assertions (flag table, exit-code table row set, every-constant check, isolation line); the other 24 passed. No load, import or fixture fault. The `test(02-07)` commit holds the test alone, the `feat(02-07)` commit holds the filled README, and all 28 then pass.

## Deviations from Plan

### Auto-fixed Issues

None needing a rule: no bug, blocker or missing critical piece surfaced in existing code. Two small judgement calls inside the plan's scope:

**1. README wording on the allowlist model**
- **Found during:** Task 2
- **Issue:** the plan's "what a green run proves" list says the allowlist model agrees with "the committed traces and the real capture", but the real capture is produced by plan 02-08 and does not exist yet.
- **Fix:** the README says the model agrees with the committed traces and that a real capture joins them after the spikes, so no claim outruns the evidence.
- **Files modified:** `tests/harness/README.md`
- **Commit:** `eefdaaa`

**2. Extra tests beyond the plan's list**
- **Issue:** none; added a parenthesized-`with` check in `test_imports.py`, the wrapper 70/71 and constant-mirror checks in `test_exitcode_agreement.py`, and a no-cost-figure, no-install-command and no-email check in `test_readme.py`, each cheap and tied to a stated prohibition.
- **Commits:** `f7f9ddf`, `438398d`

**Total deviations:** 0 auto-fixed, 2 judgement calls. **Impact:** none on scope; the README is slightly more conservative than the plan text on one claim.

## Authentication Gates

None. This plan needs no login; the README documents the one-time login that plan 02-08 asks bokiko to run.

## Known Stubs

None. The README holds two HTML-comment anchors and lists nine files as "planned" by design (plan 02-08 creates them and its fixture test asserts they exist); these are documented forward references, not stubs.

## Threat Flags

None. No new network endpoint, auth path or trust boundary; every new file is a read-only test or documentation under `tests/harness`.

## Next Phase Readiness

Plan 02-08 (spikes) can start after the orchestrator merges this plan. It should:

- import `PENDING_SPIKE_FILES` from `test_readme` (a tuple of paths relative to `tests/harness`);
- regenerate only the text between `<!-- flag-table:begin -->` and `<!-- flag-table:end -->` after it changes `confirmed_by` fields, using `pc_flags.render_flag_table_markdown()`;
- put the login step as it ran at the first anchor comment under "Isolation and the one-time login", and further findings pointers at the anchor under "Spike spend" (that section must stay digit-free; `test_readme` asserts it);
- keep the layout list in step: planned entries are already present, and the "planned:" prefix in their descriptions can be dropped once the files exist.

`TESTED_VERSIONS` is still empty, so a real preflight returns 13 today, and the README says so.

## Self-Check: PASSED

- Created files exist: `tests/harness/test_imports.py`, `test_bash_shims.py`, `test_exitcode_agreement.py`, `test_readme.py`, `README.md`.
- Commits `f7f9ddf`, `438398d` and `eefdaaa` are ancestors of HEAD.
- Acceptance criteria and the plan-level verification were re-run after the last code commit and passed (results above).
