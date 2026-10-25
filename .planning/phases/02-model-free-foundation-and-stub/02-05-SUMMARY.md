---
phase: 02-model-free-foundation-and-stub
plan: 05
subsystem: testing
tags: [python-stdlib, unittest, sanitizer, leak-gate, promote, gitleaks-parity, fail-closed, tdd]

requires:
  - phase: 01-publication-hardening
    provides: "the six gitleaks identifier rules, the two email allowlists and the denylist.sh floors this plan mirrors"
  - phase: 02-model-free-foundation-and-stub
    provides: "pc_exitcodes (14, 15, 17) from 02-01 and pc_runroot exclusive_dir/write_exclusive from 02-03"
provides:
  - "pc_seeds: run-time assembly of leak-shaped test strings (home paths, slug, temp root, addresses, host, email, key shapes)"
  - "pc_leakgate: fail-closed scanner (six mirrored identifier rules, two allowlists, two Python-only rules, five credential shapes, deny entries), counts-and-labels output, CLI exiting 0, 14, 15 or 2"
  - "pc_sanitize: runtime-built deny-list sanitizer with lower-case tokens, never prints an entry"
  - "pc_promote: gate-first, exclusive-creation copy into tests/evidence, exit 0, 14, 15 or 17"
affects: [02-07 exit-code agreement and README, 02-08 spike, 03 matrix driver and evidence filing, 04 evidence comparison]

actuals:
  tokens: 28100
  tasks: 3
  commits: 6
plan_head_before: 60b82162bdb5882a533de36d242ad46f894ceda1
plan_head_after: cf500f9f1c99deb38293f1395dcd2efe2c12ce90

tech-stack:
  added: []
  patterns:
    - "One shared fail-closed reader and one set of floors (pc_leakgate) used by both the gate and the sanitizer"
    - "Findings carry label bytes, rule id and count only; a name that itself matches relabels the file (file name)"
    - "Each file is read once into memory; the scanned bytes are the written bytes"
    - "Parity reader: a small line reader over the TOML, asserting the Python rule strings are byte-identical"

key-files:
  created:
    - tests/harness/pc_seeds.py
    - tests/harness/pc_sanitize.py
    - tests/harness/pc_leakgate.py
    - tests/harness/pc_promote.py
    - tests/harness/test_sanitize.py
    - tests/harness/test_leakgate.py
    - tests/harness/test_promote.py
  modified: []

key-decisions:
  - "A run of name characters longer than 1024 is refused (refused-longrun): the mirrored e-mail rule is quadratic on a backtracking engine, and 5 MiB of one run did not finish"
  - "Host names and deny-file entries are replaced wherever they occur, exactly as the gate looks for them; path forms never cut a longer word; the login matches as a whole word at four or more characters"
  - "With injected sources the sanitizer reads a deny file only when one is named, so tests never depend on the real machine"
  - "promote checks symlinks lexically from the repository root's tests folder down, so a temporary root reached through a system symlink is still accepted"
  - "The default config directory is claude-config under PRECLEAR_HARNESS_HOME, falling back to a .preclear-harness folder under the user's home"
  - "The gate relabels content findings of a file whose name matches as (file name), matching denylist.sh"

patterns-established:
  - "Messages and test assertions carry fixed labels only; no value, path, host or deny entry is ever echoed"
  - "Seeds come from pc_seeds, joined from fragments at run time, so the repository's own scan of tests/harness stays clean"

requirements-completed: [EVID-02, EVID-03]

coverage:
  - id: D1
    description: "Tracer: a seeded home path is refused by the gate and by promote with counts-only output and nothing created; a clean stage is promoted byte for byte by exclusive creation; a second promote exits 17"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_promote.py#TracerTests"
        status: pass
      - kind: unit
        ref: "tests/harness/test_leakgate.py#TracerTests"
        status: pass
    human_judgment: false
  - id: D2
    description: "Runtime-built sanitizer: every home form, name and host floors, temp and repo roots, longest match, idempotence, token preservation, empty entries, fail-closed deny file, order independence, live-machine check, output passes the gate"
    requirement: EVID-02
    verification:
      - kind: unit
        ref: "tests/harness/test_sanitize.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Gate parity with .gitleaks.toml (six rules, two allowlists, secretGroup, byte-identical), seeds against rules, credential and Python-only rules, edge cases (offset 0, end of file, chunk boundaries, size cap, NUL, undecodable, symlink, special, long run, empty), fail-closed injection, sorted counts-only output"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_leakgate.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "promote hardening: outside-evidence, existing, dot-dot, symlink, config-directory, NUL and empty-stage refusals with exit 17, no partial destination after a gate refusal, scan-to-copy tampering, racing promotes, partial-write reporting, stage never changed"
    requirement: EVID-03
    verification:
      - kind: unit
        ref: "tests/harness/test_promote.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Seeded leaks are assembled at run time; the repository's own scan of tests/harness stays clean and the Python gate passes its own sources"
    requirement: EVID-03
    verification:
      - kind: other
        ref: "gitleaks dir tests/harness --config .gitleaks.toml --no-banner --redact --exit-code 2 -l warn"
        status: pass
      - kind: unit
        ref: "tests/harness/test_leakgate.py#ParityTests.test_the_harness_sources_pass_their_own_gate"
        status: pass
    human_judgment: false
  - id: D6
    description: "NFD forms of a real non-ASCII account name: only a synthetic name proves the logic; behaviour on a real such account is unverified"
    requirement: EVID-02
    verification: []
    human_judgment: true
    rationale: "A real account with a non-ASCII login cannot be exercised on this machine (plan backstop)"

duration: not-recorded
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 05: Sanitizer, Leak Gate and Promote Summary

**A runtime-built deny-list sanitizer, a fail-closed Python leak gate that mirrors the repository's six identifier rules byte for byte and prints counts only, and a gate-first `promote` that creates evidence exclusively from the bytes it scanned, all standard library, zero tokens.**

## Performance

- **Duration:** not recorded (the start time was not captured at spawn)
- **Completed:** 2026-10-25
- **Tasks:** 3 (tracer, sanitizer, gate completion and promote hardening)
- **Files created:** 7 (four modules, three test modules); none modified
- **Suite:** 285 tests at the base, 392 now (sanitize 35, leakgate 44, promote 28); green under the PATH Python 3.14 and the system 3.9.6; `tests/harness/selftest` passes with 3 skips that were already there

## Accomplishments

- **Tracer (EVID-03).** A stage holding a run-time-assembled home path exits 14 from both the gate CLI and `promote`, the output names the file and a count and no part of the value, and no destination exists afterwards. A clean stage is promoted byte for byte; a second promote exits 17.
- **Sanitizer (EVID-02).** One left-to-right pass over every form (raw, realpath, both dash-slugs, URL-encoded with and without safe slashes, NFC and NFD, case-insensitive), longest first, tokens already present preserved, idempotent, independent of source order. Host and local-deny-file floors and the fail-closed file reader are shared with the gate. Only counts are ever exposed.
- **Gate (EVID-03).** Six identifier rules and two allowlists copied from `.gitleaks.toml` and proven byte-identical by a parity test that reads the TOML with a small line reader (no TOML parser). Two Python-only rules (superuser home, Windows home) in an explicit named set, five credential shapes, deny entries, and refusals (never skips) for NUL, undecodable bytes, symlinks, special files, oversize and over-long runs. Every scanner failure is exit 15.
- **Promote hardening (EVID-03).** Exit 17 for outside-evidence, existing, dot-dot, symlinked, config-directory, NUL and empty or unreadable stage cases; the whole set is gated before anything is created; a late change to a stage file cannot reach the destination; of two racing promotes exactly one wins; a write failure reports "partial promote in <destination>" and deletes nothing.
- **Side result.** The Python gate, run read-only over the committed `tests/evidence` tree (1246 files, live machine deny entries, no local deny file present on this machine), reports zero findings.

## Task Commits

1. **Task 1 (tracer):** `775e8e8` (test, RED) then `2a6e89b` (feat, GREEN)
2. **Task 2 (sanitizer):** `edb837b` (test, RED) then `5140326` (feat, GREEN)
3. **Task 3 (gate completion, promote hardening):** `751b250` (test, RED) then `cf500f9` (feat, GREEN)

**Plan metadata:** the commit that adds this file (docs).

No refactor commits: nothing needed restructuring after GREEN.

## TDD Gate Compliance

Every task has its `test(02-05)` commit before its `feat(02-05)` commit. RED was real in each case: the RED commits for tasks 1 and 2 carry skeleton modules whose functions raise `NotImplementedError`, so the target tests ran and errored or failed on the planned behaviour (task 1: 5 and 5 tests failing; task 2: 34 errors and 1 failure of 35); the task 3 RED run failed 7 leak-gate tests (5 assertions, 2 errors from missing names) and 10 promote tests on their planned behaviour. The machine classifier (`gsd_run check tdd-red-evidence`) was not available in this environment, so semantic assessment was done by reading the failure headers. One RED test, the whole-file single-run input, was excluded from the task 3 RED run because against the unguarded scanner it does not terminate (that is the defect it covers, see Deviations).

## Files Created/Modified

- `tests/harness/pc_seeds.py` - leak-shaped strings joined from fragments at run time (exempt from the no-delete scan by name)
- `tests/harness/pc_leakgate.py` - rules, allowlists, scan_bytes, scan_name, collect_tree, scan_entries, scan_tree, format_findings, deny-entry builders, CLI
- `tests/harness/pc_sanitize.py` - Sanitizer, Sources, machine_sources, TOKENS
- `tests/harness/pc_promote.py` - promote and CLI
- `tests/harness/test_leakgate.py`, `test_sanitize.py`, `test_promote.py` - the three test modules

## Decisions Made

See `key-decisions` above. The two worth repeating: the over-long run refusal (a real finding about running a linear-engine rule set on a backtracking engine), and the choice to scan the destination's own relative name as well as the file names, so a leak cannot enter through the folder name.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Over-long runs stalled the scan**
- **Found during:** Task 3 (running the cap-boundary tests)
- **Issue:** The plan assumed the mirrored gitleaks rules are linear-shaped and that the 5 MiB cap is a second guard. On Python's backtracking engine the e-mail rule restarts at every position of a run of name characters, so 5 MiB of one run (and the cap-sized test inputs built that way) did not finish. A hang is a denial of service against threat T-02-29.
- **Fix:** `MAX_RUN = 1024`: a run of `[A-Za-z0-9._%+-]` longer than that is refused as `refused-longrun`, never scanned and never skipped. A linear pass finds it before any rule runs. Measured worst case after the guard (many runs of exactly 1024) is a few seconds for 5 MiB. Test fillers for the cap and chunk-boundary tests became ordinary text.
- **Files modified:** `tests/harness/pc_leakgate.py`, `tests/harness/test_leakgate.py`
- **Verification:** `test_a_run_longer_than_the_limit_is_refused_instead_of_stalling_the_scan`, `test_a_whole_file_of_one_run_is_refused_quickly`, `test_a_long_run_next_to_a_leak_still_reports_the_refusal`
- **Committed in:** `cf500f9`

**2. [Rule 1 - Bug] Tracer test data held a NUL byte**
- **Found during:** Task 1 (first GREEN run)
- **Issue:** The clean-stage test used a file with a NUL byte, which the gate correctly refuses as binary, so promote exited 14 instead of 0.
- **Fix:** the file now holds CRLF and a multi-byte character with no trailing newline.
- **Files modified:** `tests/harness/test_promote.py`
- **Committed in:** `2a6e89b`

### Additions inside the plan's scope (not behaviour changes)

- `pc_leakgate.py` CLI takes optional `--repo-root` and `--deny-file` before `scan`, so a test can point the CLI at an unreadable deny file and observe exit 15.
- `pc_promote` also scans the destination's relative name (reported as `(destination name)`), and `pc_seeds.bearer_token` was added for the bearer-shape rule.
- Test expectations were corrected before the task 3 RED commit where they misread the TOML (the second allowlist is case-insensitive only inside its first group).

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1). **Impact:** the run limit is a documented refusal that the plan's own fail-closed stance calls for; no scope creep.

## Issues Encountered

- The worktree sandbox refused compound commands that mix `git` or `gitleaks` with other commands, so each was run on its own. A hung test run from the unguarded scanner was killed by me, and a later `grep` was then denied by the auto-mode classifier; I used the file reader instead and did not retry the denied form.
- `gsd_run` (the GSD CLI) was not available in this environment, so the RED-evidence classifier and the broken-windows ledger append were not run (see TDD Gate Compliance). There are no stubs, so nothing needed ledger entries.

## Authentication Gates

None.

## Known Stubs

None. The `NotImplementedError` skeletons in the two RED commits were replaced by the GREEN commits of the same tasks.

## Threat Flags

None beyond the plan's threat model: promote's write surface (tests/evidence) and the local deny file read were both in the register (T-02-24, T-02-26).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `pc_sanitize.Sanitizer.from_machine(repo_root, extra_map, deny_file, sources)` and `pc_leakgate.scan_tree`/`build_deny_entries` are ready for the Phase 3 evidence filing (EVID-04); `pc_promote.promote(stage, dest, repo_root, config_dir, deny_entries)` is the single door into `tests/evidence`.
- Plan 02-07 should list exit codes 14, 15 and 17 from `pc_exitcodes` and may reference `PRECLEAR_HARNESS_HOME` (promote reads it for the default config directory).
- Open limits to state in the guide: credential shapes are a documented subset (the commit hooks stay the second net); NFD handling of a real non-ASCII account is proven only on a synthetic name; runs of name characters above 1024 are refused.

## Self-Check: PASSED

- All seven created files exist.
- All six commits are on the branch; first and last were verified as ancestors of HEAD.
- Suite: 392 tests green under both interpreters; plan-level checks run: tracer shell check (exit 14, no destination), the three test modules under the system 3.9.6, `gitleaks dir tests/harness` clean, frozen paths unchanged since the reference commit (SKILL.md 11,994 bytes), no attribution trailer in this branch's commit messages.
