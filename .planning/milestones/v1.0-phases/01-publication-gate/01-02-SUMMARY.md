---
phase: 01-publication-gate
plan: 02
subsystem: infra
tags: [gitleaks, git-hooks, pre-commit, deny-list, identifier-scan, shellcheck]

requires:
  - phase: 01-publication-gate
    provides: "pre-push gate, leak and identity checks, commit-msg hook, scratch-guarded throwaway-clone test script"
provides:
  - "Full scan config: default ruleset, six identifier rules, two scoped allowlists"
  - "15-fingerprint accepted-findings list generated from a strict mirror scan"
  - "pre-commit hook: gitleaks over the staged diff plus the local deny-list check, fail closed"
  - "Deny-list check for staged content and pushed ranges, counts and file names only"
  - "Hooks README with the one-command enable, owner pin setup, scanner version and limits"
  - "Seven more throwaway-clone cases, 17 named checks in total"
affects: [01-03-prepublish-scan, 01-04-flip-checkpoint, phase-02, phase-03, phase-04]

actuals:
  tokens: 7530
  tasks: 3
  commits: 3
plan_head_before: 01c4ffca2bc438b2ec33fc66122ad44c4da26a60
plan_head_after: 10263c7ccd04334f52f1c9c6bd75c05b2ae34421

tech-stack:
  added: []
  patterns:
    - "Strict scan (accepted list off) must equal the committed accepted list as a set, so the list cannot go stale or be padded"
    - "Deny-list entries are built at run time from the machine plus a git-dir-only file, and are never printed"
    - "Flagged test values are assembled from separate words at run time, so no source line holds a complete one"
    - "Diff streams are parsed in one awk pass that tells file headers from hunk bodies"

key-files:
  created:
    - .gitleaksignore
    - .githooks/pre-commit
    - .githooks/checks/denylist.sh
    - .githooks/README.md
  modified:
    - .gitleaks.toml
    - scripts/test-hooks.sh

key-decisions:
  - "The public-address allowlist matches .planning markdown at any depth, so git-mode and directory-mode scans agree"
  - "The deny-list check reads the diff in one awk pass instead of one grep per file, so unusual file names cannot make it skip a file"
  - "The pre-commit hook checks for the scanner before it changes directory, so a missing scanner is reported even if git is unusable"

patterns-established:
  - "Every new hook behavior gets a named PASS or FAIL case in the throwaway-clone script before it is implemented"
  - "A fresh clone of the real repository is made with its origin removed at once, so nothing in it can be pushed"

requirements-completed: [PUB-02, PUB-03]

coverage:
  - id: D1
    description: "Strict scan of a mirror of the full history equals the accepted list exactly (19 matches, 15 fingerprints, all in d437af2, two home-path rules); the gate scan and the committed-tree scan are clean"
    requirement: PUB-02
    verification:
      - kind: integration
        ref: "mirror strict, gate and tree scans from the Task 1 verify, prints strict=2 gate=0 tree=0 and True"
        status: pass
    human_judgment: false
  - id: D2
    description: "A seeded fake credential is refused by pre-commit with no commit created, and by pre-push when pre-commit is skipped"
    requirement: PUB-03
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#leak-seed-precommit, leak-seed-prepush"
        status: pass
    human_judgment: false
  - id: D3
    description: "Home paths with a name segment, private addresses, internal-suffix hosts and non-allowlisted emails are refused; example-domain addresses, npm version specs, the local settings file name and bare-prefix prose are not"
    requirement: PUB-02
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#identifiers-precommit, identifier-false-positive-guards"
        status: pass
    human_judgment: false
  - id: D4
    description: "A local deny-list entry blocks a commit and is never printed; a missing scanner stops the commit (exit 1)"
    requirement: PUB-03
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#denylist-precommit, fail-closed-no-scanner"
        status: pass
    human_judgment: false
  - id: D5
    description: "A fresh clone has hooks off and a seeded commit succeeds there; after git config core.hooksPath .githooks the same commit is refused"
    requirement: PUB-03
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#fresh-clone-hooks-off-by-default, fresh-clone-enable-blocks-seed"
        status: pass
    human_judgment: false
  - id: D6
    description: "Hooks README states the enable command, owner pin setup, tested scanner version and that the hooks are not enforcement"
    requirement: PUB-03
    verification:
      - kind: other
        ref: "grep for the enable command, 8.30.0, user.useConfigOnly, preclear.pinnedIdentity and the limits wording"
        status: pass
    human_judgment: true
    rationale: "Grep proves the required strings exist; whether the prose reads clearly to a stranger needs a human"

duration: 6min
completed: 2026-10-22
status: complete
---

# Phase 1 Plan 02: Identifier Scan, Pre-commit Hook and Fresh-clone Proof Summary

**A gitleaks config with six identifier rules and a 15-fingerprint accepted list proven equal to the strict mirror scan, a fail-closed pre-commit hook with a run-time deny-list check, and a hooks README, backed by 17 passing throwaway-clone cases including a fresh-clone enable proof.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-22T04:17:58Z
- **Completed:** 2026-10-22T04:24:15Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- The strict scan of a mirror of the full history exits 2 with 19 matches and 15 fingerprints, all in commit d437af2 and from the two home-path rules. The fingerprint set equals the accepted list exactly. The gate scan exits 0 and the committed-tree scan exits 0 with no research file reworded.
- pre-commit refuses a seeded fake credential, the four identifier shapes and a deny-list entry. It lets the false-positive look-alikes through. With the scanner missing from the path it exits 1.
- A fresh clone commits the seed with hooks off. After the one documented enable command the same commit is refused.
- `sh scripts/test-hooks.sh` prints 17 PASS lines and no FAIL line. `shellcheck -s sh` is clean over every hook, check and the test script.
- A scan of the real repository's full history with the committed config exits 0. The seed literal built at run time appears in no commit.

## Task Commits

1. **Task 1: Full identifier rules, scoped allowlists and the 15-fingerprint accepted list** - `8938188` (feat)
2. **Task 2: Pre-commit hook, local deny-list check and five cases** - `2f09d36` (feat, TDD)
3. **Task 3: Hooks README and the fresh-clone proof** - `10263c7` (docs)

**Plan metadata:** recorded by the docs commit that follows this file.

## Files Created/Modified

- `.gitleaks.toml` - Default ruleset plus six identifier rules and two allowlists
- `.gitleaksignore` - Two comment lines and 15 immutable fingerprints, generated from the strict report
- `.githooks/pre-commit` - Scanner guard, gitleaks over the staged diff, then the deny-list check
- `.githooks/checks/denylist.sh` - Deny-list check for the staged diff and for pushed ranges
- `.githooks/README.md` - Enable, owner setup, what runs, test, scanner, local deny list, limits
- `scripts/test-hooks.sh` - Seven more cases, 17 in total, all commits through the scratch guard

## Decisions Made

- The allowlist for the public address matches `.planning` markdown at any directory depth. Git mode reports repository-relative paths and directory mode reports the path as given, so a start-anchored pattern only worked in one of them.
- The deny-list check reads the diff stream in a single awk pass and tracks the current file from the diff headers. A per-file loop would have skipped a file whose quoted name could not be passed back to git.
- The deny-list file is never created by this plan. The owner adds a real name to it if wanted. See Open Items.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Public-address allowlist path anchor failed in directory mode**
- **Found during:** Task 1 (committed-tree scan)
- **Issue:** The planned path pattern was anchored at the start of a repository-relative path. The committed-tree scan extracts the tree to a folder and scans it by absolute path, so the two document lines holding the public address were reported and the tree scan exited 2 instead of 0.
- **Fix:** The path pattern now matches `.planning` markdown at the start of the path or after a slash. The address match stays exact, the condition stays AND, and the scope stays `.planning` markdown only.
- **Files modified:** `.gitleaks.toml`
- **Verification:** The Task 1 verify then printed strict=2 gate=0 tree=0 and True, and the same result held at the final tip.
- **Committed in:** 8938188 (part of the task commit)

**2. [Rule 2 - Missing Critical] Deny-list diff parsing made robust to file names**
- **Found during:** Task 2 (denylist.sh design)
- **Issue:** The plan counts matches per file with one grep per staged file. A file name that git quotes would return an empty diff and the file would pass unchecked, which reads as clean.
- **Fix:** One awk pass over the whole diff, telling file headers from hunk bodies by the diff header line and the first hunk marker. A failed git diff or an unreadable ranges file exits 1 with a message. The output contract is unchanged: counts and file names only.
- **Files modified:** `.githooks/checks/denylist.sh`
- **Verification:** The deny-list case passes. A by-hand run of ranges mode in a throwaway repository refused a range holding an entry, passed an empty range and never printed the entry.
- **Committed in:** 2f09d36 (part of the task commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both were needed for the stated results. No scope creep.

## TDD Notes (Task 2)

- **RED:** The five cases were added first and run against the task 1 state. leak-seed-precommit, identifiers-precommit, denylist-precommit and fail-closed-no-scanner failed for the right reason: no pre-commit hook existed, so the commits succeeded and the scanner-less run exited 127. identifier-false-positive-guards passed at RED because nothing refused anything yet. It only proves something once the hook exists.
- **GREEN:** Adding the hook and the deny-list check made all 15 cases pass.
- The plan specifies one commit per task, so RED and GREEN share the task 2 commit, as in plan 01-01. The RED output is a custom PASS or FAIL format that the red-evidence classifier does not support, so the semantic assessment above was done by hand.

## Issues Encountered

None beyond the deviations above.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None. The deny-list check reads machine host names and writes temporary files, both covered by T-01-10 and T-01-11 in the plan.

## Open Items for bokiko

- The local deny list covers this machine's host names only. The real name is not derivable at run time, so it is covered only if the owner adds it to the git-dir-only deny file described in the hooks README. Nothing was created there.
- Whether to stay on gitleaks 8.30.0 or move to 8.30.1 is still bokiko's call at the plan 01-04 checkpoint. The README says 8.30.x, tested on 8.30.0.
- The strict, gate and tree scans here ran on a mirror of the local repository. Plans 01-03 and 01-04 repeat them on a mirror of the remote after the last push.
- PUB-02 in the requirements still says ten home-path lines. The measured count is eleven lines in ten files. Wording is unedited, as planned.

## Next Phase Readiness

- Plan 01-03 can add a history mode to the deny-list check and build the pre-publish script on the same strict, gate and tree commands.
- The hooks are enabled in the owner clone. A fresh clone needs `git config core.hooksPath .githooks`, now documented and tested.

## Self-Check: PASSED

- All six created or modified files exist on disk.
- Commits 8938188, 2f09d36 and 10263c7 are ancestors of HEAD.
- `sh scripts/test-hooks.sh` exits 0 with 17 PASS lines and no FAIL line.
- No commit message in this plan matches the attribution patterns, and history holds one identity.
- No file under the frozen paths changed since commit 56e155c.

---
*Phase: 01-publication-gate*
*Completed: 2026-10-22*
