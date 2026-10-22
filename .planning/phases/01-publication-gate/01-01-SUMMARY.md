---
phase: 01-publication-gate
plan: 01
subsystem: infra
tags: [git-hooks, gitleaks, pre-push, commit-msg, identity-pin, shellcheck]

requires: []
provides:
  - "Committed pre-push hook that fans out to leak, identity and attribution checks"
  - "commit-msg hook and a single attribution pattern file shared with pre-push"
  - "Throwaway-clone test suite with a scratch guard on every commit it makes"
  - "Owner clone pinned to the public identity; agent attribution suppressed at the source"
  - "Three dated, decided owner rows in PROJECT.md Key Decisions"
affects: [01-02-identifier-rules, 01-03-prepublish-scan, 01-04-flip-checkpoint, phase-02, phase-03, phase-04]

actuals:
  tokens: 5243
  tasks: 3
  commits: 3
plan_head_before: e2a7e2de3b6ac26fd6eb405859efe9bbd2f1c3e8
plan_head_after: 340dd6732ec42af19c1e88842a132f0a28550fca

tech-stack:
  added: []
  patterns:
    - "pre-push parses stdin once into a ranges file, then runs every executable checks/*.sh with it"
    - "gitleaks --exit-code 2 separates a finding from a tool error; a missing scanner exits 1"
    - "Hook tests build fake secrets from run-time fragments inside a throwaway clone"
    - "Every test commit goes through one guarded helper that proves the target is isolated"

key-files:
  created:
    - .githooks/pre-push
    - .githooks/commit-msg
    - .githooks/attribution.ere
    - .githooks/checks/leaks.sh
    - .githooks/checks/identity.sh
    - .gitleaks.toml
    - scripts/test-hooks.sh
    - .claude/settings.json
    - .claude/CLAUDE.md
  modified:
    - .planning/PROJECT.md

key-decisions:
  - "Identity and attribution checks run only in a clone that sets the pin, so contributors' clones are not forced into the owner identity; the leak check stays on for everyone"
  - "Attribution is enforced by the pre-push identity check only when the pin is set, because co-author trailers are legitimate for outside contributors"
  - "Checks fail closed: a failed git log or a missing pattern file refuses the push instead of passing silently"

patterns-established:
  - "Plain imperative commit messages with no trailer; verified after each commit against attribution.ere"
  - "One PASS or FAIL line per named test case; the script exits 1 on any FAIL"

requirements-completed: [PUB-01, PUB-03, PUB-04]

coverage:
  - id: D1
    description: "Pre-push hook refuses a push whose range holds a non-pinned author, committer or annotated-tag tagger, and the commit never reaches the throwaway remote"
    requirement: PUB-04
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#identity-wrong-author-committer, identity-committer-only, identity-wrong-tagger"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pre-push hook refuses a seeded fake credential built at run time, even when the commit hook was skipped, and the seed commit is absent from the remote"
    requirement: PUB-03
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#leak-seed-prepush, leak-seed-absent-on-remote"
        status: pass
    human_judgment: false
  - id: D3
    description: "commit-msg refuses an attribution trailer at commit time, and pre-push refuses it when commit-msg was skipped"
    requirement: PUB-04
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#trailer-commit-msg, trailer-bypassed-prepush"
        status: pass
    human_judgment: false
  - id: D4
    description: "An unpinned clone skips the identity check with a visible message while the leak check stays enforced"
    requirement: PUB-04
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#unpinned-skips-identity"
        status: pass
    human_judgment: false
  - id: D5
    description: "No test commit can land in the real repository, and the real repository's refs are unchanged by a run"
    requirement: PUB-03
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#real-origin-refs-unchanged"
        status: pass
      - kind: other
        ref: "awk static gate: every commit invocation sits in scratch_commit after assert_scratch"
        status: pass
    human_judgment: false
  - id: D6
    description: "Owner clone is pinned (useConfigOnly, name, address, pinnedIdentity, hooksPath) and git resolves the pinned identity for new commits"
    requirement: PUB-04
    verification:
      - kind: other
        ref: "git config --local checks and git var GIT_AUTHOR_IDENT comparison from the plan verify"
        status: pass
    human_judgment: false
  - id: D7
    description: "PROJECT.md Key Decisions holds three dated, decided rows for history, public identity and row 7"
    requirement: PUB-01
    verification:
      - kind: other
        ref: "grep row count equals 3 and no Pending in those rows"
        status: pass
    human_judgment: true
    rationale: "Row 7's date of 2026-10-21 is inferred (FA-3); bokiko confirms it at the plan 01-04 checkpoint"
  - id: D8
    description: "Claude Code honors the committed attribution suppression in this repo"
    verification: []
    human_judgment: true
    rationale: "Observable only through later commits passing commit-msg and the pre-push attribution check; no test asserts the harness behavior"

duration: 5min
completed: 2026-10-22
status: complete
---

# Phase 1 Plan 01: Hook Gate and Identity Pin Summary

**A committed POSIX-sh pre-push gate (gitleaks leak check, pinned-identity check, AI-attribution check) plus a commit-msg hook, proven by ten PASS cases in a throwaway clone behind a scratch guard, with the owner clone pinned and three owner decisions recorded.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-22T04:10:12Z
- **Completed:** 2026-10-22T04:15:39Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- The phase tracer works end to end: a clean push passes, a wrong-identity push and a seeded-leak push are each refused with a non-zero exit, and neither refused commit reaches the throwaway remote.
- AI attribution trailers are refused at commit time and, if that hook is skipped, at push time. Both read one pattern file.
- `sh scripts/test-hooks.sh` prints ten PASS lines and no FAIL line. `shellcheck -s sh` is clean over every hook, check and the test script.
- The owner clone holds the five local git config keys. `git var GIT_AUTHOR_IDENT` resolves to the pinned identity, and all history still has exactly one author-and-committer identity.
- PROJECT.md Key Decisions now has three decided rows dated 2026-10-21. The history row records eleven home-folder path lines across ten files and 15 fingerprints.

## Task Commits

1. **Task 1: Tracer, pre-push refuses a wrong-identity push and a seeded-leak push** - `6adf923` (feat)
2. **Task 2: Refuse AI attribution trailers at commit-msg and pre-push; extend identity cases** - `afdaf55` (feat, TDD)
3. **Task 3: Suppress agent attribution and record the owner decisions** - `340dd67` (chore)

**Plan metadata:** recorded by the docs commit that follows this file.

## Files Created/Modified

- `.githooks/pre-push` - Parses pushed refs once and fans out to the checks
- `.githooks/checks/leaks.sh` - gitleaks over each pushed range, fail closed, redacted
- `.githooks/checks/identity.sh` - Pinned-identity check and attribution check over each range and annotated tag
- `.githooks/attribution.ere` - Four forbidden-pattern lines, the single source of truth
- `.githooks/commit-msg` - Refuses an attribution trailer at commit time
- `.gitleaks.toml` - Default ruleset only; plan 01-02 adds identifier rules
- `scripts/test-hooks.sh` - Ten-case throwaway-clone suite and the scratch guard
- `.claude/settings.json` - Empty commit and pull request attribution, session URL off
- `.claude/CLAUDE.md` - One-line no-trailer rule
- `.planning/PROJECT.md` - Three decided Key Decisions rows

## Decisions Made

- The attribution check lives inside the pinned section of the identity check, so an unpinned contributor clone is not blocked from legitimate co-author trailers. The leak check applies to every clone.
- Git's own comment lines are dropped before the commit-msg pattern match, so a commented trailer line does not refuse a commit.
- The test script's remote is created with an explicit initial branch so a clone of it checks out the committed hooks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fail closed on git and pattern-file errors in the identity check**
- **Found during:** Task 1 and Task 2 (identity.sh)
- **Issue:** The research text passes silently when `git log` fails on a range, and the attribution grep exits 2 with no output when the pattern file is missing. Both would read as clean.
- **Fix:** A failed `git log` refuses the push for that ref. A missing or unreadable pattern file exits 1 with a visible message.
- **Files modified:** `.githooks/checks/identity.sh`
- **Verification:** `scripts/test-hooks.sh` all ten PASS; `shellcheck -s sh` clean
- **Committed in:** 6adf923 and afdaf55

**2. [Rule 1 - Bug] Bare remote had no default branch matching the pushed branch**
- **Found during:** Task 2 (unpinned-skips-identity, RED run)
- **Issue:** `git init --bare` defaulted to a different branch name, so a clone of the throwaway remote checked out nothing and no hooks ran in the unpinned clone. The case then failed for a setup reason.
- **Fix:** The bare remote is created with initial branch main.
- **Files modified:** `scripts/test-hooks.sh`
- **Verification:** unpinned-skips-identity passes and shows the skip message and the leak refusal
- **Committed in:** afdaf55

**3. [Rule 3 - Blocking] Push guard and seed builder generalised for a second clone**
- **Found during:** Task 2
- **Issue:** The task 1 push helper was bound to the first work repository, and the unpinned case needs a second clone.
- **Fix:** The push helper takes the repository as an argument, asserts the scratch guard and still checks that origin sits inside the throwaway directory. The seed is built by one helper from run-time fragments.
- **Files modified:** `scripts/test-hooks.sh`
- **Verification:** The static gate still passes: every commit invocation sits in `scratch_commit` after `assert_scratch`.
- **Committed in:** afdaf55

---

**Total deviations:** 3 auto-fixed (1 missing critical, 1 bug, 1 blocking)
**Impact on plan:** All three were needed for correctness or to complete the planned cases. No scope creep.

## TDD Notes (Task 2)

- **RED:** The five new cases were added first. Run against the task 1 state, trailer-commit-msg and trailer-bypassed-prepush failed for the right reason, because no commit-msg hook and no attribution check existed. The other three new cases already passed, because they exercise identity logic that task 1 had implemented.
- **GREEN:** Adding `attribution.ere`, `commit-msg` and the attribution half of the identity check made all ten cases pass.
- The plan specifies one commit per task, so RED and GREEN share the task 2 commit. There is no separate test commit.
- The RED output is a custom PASS or FAIL format, not a report format the red-evidence classifier supports. The semantic assessment above was done by hand.

## Issues Encountered

None beyond the deviations above.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None. All new surface (hooks, test script, config) is covered by the plan's threat model.

## Open Items for bokiko

- Row 7's decision date of 2026-10-21 is inferred from the day PUB-01 was written (FA-3). Confirm it at the plan 01-04 checkpoint.
- The committed Claude Code attribution suppression and the one-line CLAUDE.md rule become public files. Plan 01-04 asks for acceptance.
- Whether the harness honors the suppression is only observable in later commits. All three commits of this plan were made with no trailer and passed the checks.

## Next Phase Readiness

- Plan 01-02 can extend `.gitleaks.toml` with identifier rules and add `pre-commit`, `denylist.sh` and the README under the same test script and scratch guard.
- Hooks are enabled in the owner clone only. A fresh clone needs `git config core.hooksPath .githooks`, which plan 01-02 documents.

## Self-Check: PASSED

- All ten created or modified files exist on disk.
- Commits 6adf923, afdaf55 and 340dd67 are ancestors of HEAD.
- `sh scripts/test-hooks.sh` exits 0 with ten PASS lines and no FAIL line.
- No commit message in history matches the attribution patterns, and history holds one identity.

---
*Phase: 01-publication-gate*
*Completed: 2026-10-22*
