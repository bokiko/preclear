---
phase: 02-model-free-foundation-and-stub
plan: 09
subsystem: testing
tags: [sanitizer, leak-gate, gitleaks, json-escapes, deny-list, python-stdlib, unittest, gap-closure]

requires:
  - phase: 02-model-free-foundation-and-stub
    provides: "plans 02-05 (pc_sanitize, pc_leakgate, .gitleaks.toml parity) and 02-08 (the committed fixtures under tests/harness/data and the spike driver that hands deny entries to the gate)"
provides:
  - "pc_sanitize: the word-kind login match accepts a JSON letter escape (backslash plus n, r, t, b or f) as its boundary; Sanitizer.deny_entries() carries the login in raw, NFC and NFD forms (not when it occurs inside a fixed token)"
  - "pc_leakgate: home paths end at any non-name character (macOS-style, Linux-style, superuser, Windows-style), every rule compiles with re.ASCII, the private host suffix is case-insensitive, an unlocatable deny list is ScannerError (exit 15), a byte-order mark and padding no longer disable a deny entry"
  - ".gitleaks.toml: the twin of the two tightened identifier rules, byte-identical to the Python strings"
  - "table-driven boundary tests in test_sanitize.py and test_leakgate.py, each ending with the committed-fixtures-scan-clean assertion (IN-07)"
affects: [phase-03, phase-04]

actuals:
  tokens: 7400
  tasks: 3
  commits: 6
plan_head_before: 1e937f20e073822ee15bdc21a70791cb1f868280
plan_head_after: 6ad2fd535b2fdc709c52cf4b08bca717d70ce176

tech-stack:
  added: []
  patterns:
    - "A mirrored identifier rule ends in a consuming negated class (any character that is not a name character, or end of text) so it compiles in the commit hooks' engine, which has no lookaround; lookarounds appear only in Python-only rules"
    - "A JSON letter escape counts as a word boundary for the login; an ambiguous escape is replaced, never kept (over-replacing is the safe direction)"
    - "The sanitizer hands the gate a login entry through deny_entries(); the gate's default entry builder deliberately does not carry it"
    - "A deny list that cannot be located fails closed; the only quiet case is a tree with no .git entry in itself or any ancestor, decided by a filesystem check"

key-files:
  created: []
  modified:
    - tests/harness/pc_sanitize.py
    - tests/harness/pc_leakgate.py
    - .gitleaks.toml
    - tests/harness/test_sanitize.py
    - tests/harness/test_leakgate.py

key-decisions:
  - "The login joins the gate through Sanitizer.deny_entries(), not pc_leakgate.build_deny_entries(): the login is also the owner's public alias and appears in committed prose, so a gate that refused it everywhere would refuse the committed corpus (FA-3); the Phase 3 runner must pass sanitizer.deny_entries() to promote when it has sanitised a run"
  - "The tightened mirrored rules were committed to .gitleaks.toml (no Python-only fallback): scripts/test-hooks.sh stayed at 29 PASS with no FAIL before the edit, after the edit and after the feat commit"
  - "home-path-dash-slug keeps its closing dash (FA-6); the superuser and Windows-style shapes stay Python-only (FA-7)"

patterns-established:
  - "assert_fixtures_clean: every boundary test also proves the committed fixtures scan with 0 findings and that at least one fixture file was scanned"

requirements-completed: [EVID-02, EVID-03]

coverage:
  - id: G1
    description: "The sanitizer replaces a login of four or more characters after a JSON letter escape (n, r, t, b, f), keeps the escape, still leaves the login alone after a plain letter and inside a longer word, and does so in NFC and NFD form and for the real login (CR-01, EVID-02)"
    requirement: EVID-02
    verification:
      - kind: unit
        ref: "tests/harness/test_sanitize.py (LoginBoundaryTests)"
        status: pass
    human_judgment: false
  - id: G2
    description: "Sanitizer.deny_entries() carries the login in NFC and NFD forms so the gate refuses the unsanitised text with a count per occurrence and passes the sanitised text; a login inside a fixed token, below four characters or empty is not an entry; no report, repr or message holds the login (CR-01, D-15, D-16)"
    requirement: EVID-02
    verification:
      - kind: unit
        ref: "tests/harness/test_sanitize.py (LoginBoundaryTests.test_the_gate_refuses_the_unsanitised_text_and_passes_the_sanitised_text, test_a_login_inside_a_fixed_token_or_below_the_floor_is_not_a_gate_entry)"
        status: pass
    human_judgment: false
  - id: G3
    description: "A home path (macOS-style, Linux-style, Windows-style, superuser) followed by a JSON newline, tab, return or quote escape, a double or single backslash, a closing angle bracket, a closing brace, a pipe, an equals sign, an asterisk, a tilde or a sentence dot is a finding; every boundary found before is still found; bare folder words and the superuser folder next to a name character stay clean (CR-02, EVID-03)"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_leakgate.py (HomePathBoundaryTests)"
        status: pass
    human_judgment: false
  - id: G4
    description: "The Python RULES and .gitleaks.toml stay byte-identical with the tightened home-path-unix and internal-hostname strings; the engine flags the escaped-newline path and the upper-case host; scripts/test-hooks.sh prints the same 29 PASS lines, no FAIL, before and after (CR-02, D-14)"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_leakgate.py (ParityTests)"
        status: pass
      - kind: other
        ref: "sh scripts/test-hooks.sh (29 PASS, no FAIL, three runs) and gitleaks dir over a scratch folder (escaped-newline path and upper-case host both flagged)"
        status: pass
    human_judgment: false
  - id: G5
    description: "The email and internal-hostname rules find a value next to a non-ASCII letter and a host under an upper-case or title-case private suffix; a suffix look-alike is not a finding; a reserved-domain address next to a non-ASCII letter stays allowed (WR-01)"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_leakgate.py (AsciiAndCaseTests, IdentifierBoundaryTests)"
        status: pass
    human_judgment: false
  - id: G6
    description: "A wrong repository root, a git that cannot run or times out, and a .git entry git cannot use raise ScannerError (CLI exit 15, fixed message, no path); a tree with no repository above it has no local deny list; a byte-order mark, padded lines and an indented comment in the deny file are tolerated; Sanitizer.from_machine raises SanitizerError with a fixed message (WR-02)"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_leakgate.py (DenyListLocationTests) and tests/harness/test_sanitize.py (LocationFailClosedTests)"
        status: pass
    human_judgment: false
  - id: G7
    description: "Zero model calls; the full suite is green on the PATH interpreter and the system Python 3.9; the leak gate over tests/harness reports 0 findings in the same 52 files; the committed fixtures scan with 0 findings after every change (IN-07)"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/selftest (Ran 753 tests, OK (skipped=3), 0 model calls) and /usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py' (Ran 753 tests, OK (skipped=3))"
        status: pass
    human_judgment: false

# Metrics
duration: about 45 minutes
completed: 2026-10-26
status: complete
---

# Phase 2 Plan 09: Gap closure for the privacy layer Summary

**The sanitizer now replaces the login after a JSON letter escape and hands it to the gate, and the gate's home-path, hostname and email rules end at any non-name character, ignore non-ASCII neighbours and suffix case, with the commit hooks' twin tightened identically and a deny list that fails closed when it cannot be located.**

## Performance

- **Duration:** about 45 minutes
- **Completed:** 2026-10-26
- **Tasks:** 3 (each a `test(02-09)` commit then a `feat(02-09)` commit)
- **Files modified:** 5 (no new file)
- **Suite:** 724 tests before, 753 after (29 new), `OK (skipped=3)`, 0 model calls

## Accomplishments

- **CR-01 (login after a JSON escape).** `_PREFIX["word"]` is now `(?:(?<!\w)|(?<=\\[nrtbf]))`. A login that follows a backslash plus n, r, t, b or f is replaced with the escape kept; the login after a plain letter or inside a longer word is left alone; an ambiguous escape is replaced (FA-2). `Sanitizer.deny_entries()` also returns the login in raw, NFC and NFD form when it has four or more characters and does not occur inside a fixed token (FA-4), so the gate refuses what the sanitizer misses, with a count and no value.
- **CR-02 (home-path boundaries).** `home-path-unix` ends in `(?:[^A-Za-z0-9._-]|$)`; the two Python-only rules (`home-path-root` with a lookahead, `home-path-windows` with the same negated class) follow. Every boundary in the plan's table is a finding for all four folder shapes, including the JSON escapes that the old closing-delimiter list missed.
- **WR-01 (ASCII and case).** `make_rule` compiles with `re.ASCII`; the private host suffix is the scoped case-insensitive group `(?i:...)`, in both the Python rule and the TOML twin.
- **WR-02 (deny list).** `_git_deny_path` fails closed (`ScannerError`, fixed text, exit 15 from the CLI) for a root that is not a folder, git missing or timing out, a failing git while a `.git` entry exists, and an empty answer; a tree with no `.git` entry anywhere above it has no local list and no error (a downloaded archive still passes the suite, FA-5). `local_file_entries` decodes `utf-8-sig` and strips every line before the comment and floor checks.
- **IN-07.** Every new boundary test ends with `assert_fixtures_clean`: the committed fixtures under `tests/harness/data` scan with 0 findings and the folder's file count equals the scanned count (at least one).

## The `.gitleaks.toml` twin: tightened, no fallback

The tightened `home-path-unix` and `internal-hostname` strings were committed to `.gitleaks.toml`, byte-identical to the Python `RULES` (ParityTests pass). The plan's fallback (moving the patterns into Python-only rules) was **not** needed:

- `sh scripts/test-hooks.sh`: 29 PASS lines, no FAIL, before any edit, after the TOML edit was committed, and again at the end; the PASS lines are identical across runs.
- `gitleaks dir` over `tests/harness` exits 0 under the tightened config after each task.
- `gitleaks dir` over a scratch folder holding an escaped-newline home path and an upper-case host flags both files under the repository's config.
- The two engine-incompatible constructs the review suggested (lookahead) are used only in the two Python-only rules, which have no TOML twin (FA-1, FA-7).

## Task Commits

1. **Task 1: login after a JSON escape, login as a gate entry** - `32057d0` (test), `3b73502` (feat)
2. **Task 2: home-path boundaries, ASCII, suffix case, TOML twin** - `bb5516d` (test), `62f0170` (feat)
3. **Task 3: deny list location fails closed, byte-order mark and padding** - `83ec092` (test), `6ad2fd5` (feat)

**Plan metadata:** the commit that adds this summary.

## Files Created/Modified

- `tests/harness/pc_sanitize.py` - word boundary accepts a JSON letter escape; `login_entries` keyword; `deny_entries()` carries the login; new fixed error text for an unlocatable deny list
- `tests/harness/pc_leakgate.py` - `re.ASCII` compile; tightened `RULES` and `PYTHON_ONLY_RULES` strings; `_inside_a_repository`; fail-closed `_git_deny_path`; `utf-8-sig` and per-line strip in `local_file_entries`
- `.gitleaks.toml` - the two tightened `regex` lines, nothing else
- `tests/harness/test_sanitize.py` - `LoginBoundaryTests`, `LocationFailClosedTests`, `assert_fixtures_clean`
- `tests/harness/test_leakgate.py` - `HomePathBoundaryTests`, `IdentifierBoundaryTests`, `AsciiAndCaseTests`, `DenyListLocationTests`, `assert_fixtures_clean`

## Decisions Made

See key-decisions. The one item the Phase 3 runner must carry: when it has sanitised a run, pass `sanitizer.deny_entries()` to promote (the gate CLI and `build_deny_entries()` do not hold the login, FA-3).

## Deviations from Plan

### Auto-fixed Issues

None to the code. Test-authoring adjustments made while writing the red step:

**1. [Rule 1 - Test correctness] Boundary table placement of the sentence dot**
- **Found during:** Task 2 (red run)
- **Issue:** The plan lists "dot" among the boundaries already found at HEAD, but the superuser rule's old delimiter list did not name a dot, so the case failed at HEAD for that shape only and made the "still found" test red for a reason outside its name.
- **Fix:** moved the dot case to the table of new boundaries (all four shapes still assert exactly one finding); the "found before" table keeps only boundaries that held at HEAD.
- **Files modified:** tests/harness/test_leakgate.py
- **Commit:** `bb5516d`

**2. [Rule 1 - Test correctness] A bare word in angle brackets is not a token**
- **Found during:** Task 1 (red run)
- **Issue:** the draft token-word test appended an angle-bracketed copy of the login word (for example the repository folder word); only the fixed set is a token, so the sanitizer correctly replaced the word inside the brackets.
- **Fix:** the test asserts the exact output `who <user> said <auto-memory-root>/b` instead.
- **Commit:** `32057d0`

### Not run in this environment

- `gitleaks git .` (history scan with the repository's config) could not be run: the worktree sandbox refused any gitleaks invocation with a git operand. The same rules ran on every commit of this plan through the pre-commit hooks (none was bypassed), `gitleaks dir tests/harness` passed after each task, and `scripts/test-hooks.sh` (whose release-gate cases read the committed config) passed three times. The orchestrator should run `gitleaks git . --config .gitleaks.toml --no-banner --redact --exit-code 2 -l warn` once on the merged result; the plan's baseline is exit 0 (an accepted-findings fingerprint list does not depend on a regex change).

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or trust boundary; the change tightens existing ones (T-02-51 to T-02-58 mitigated as planned).

## Issues Encountered

- The planner's observation (d) stands: a login equal to the numbered label of a run or helper token is not excluded by the fixed-token containment check. Left for Phase 3 hardening, as recorded in the plan.

## Next Phase Readiness

- Phase 3 success criterion 1 ("every filed file passed the leak gate") now covers the escape-shaped leaks of the login and of home paths.
- The deferred WR-03 to WR-11 and IN-01 to IN-06 are untouched, as instructed.

## Self-Check: PASSED

- Files modified exist: `tests/harness/pc_sanitize.py`, `tests/harness/pc_leakgate.py`, `.gitleaks.toml`, `tests/harness/test_sanitize.py`, `tests/harness/test_leakgate.py` (all five listed by `git diff --name-only` against the plan base; nothing else outside `.planning`).
- Commits present on the branch: `32057d0`, `3b73502`, `bb5516d`, `62f0170`, `83ec092`, `6ad2fd5` (`git rev-list --count` from the base is 6, matching `actuals.commits`).
- `SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/`, STATE.md and ROADMAP.md untouched.
