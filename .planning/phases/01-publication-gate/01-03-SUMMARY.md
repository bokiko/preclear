---
phase: 01-publication-gate
plan: 03
subsystem: infra
tags: [gitleaks, mirror-scan, inventory, read-only, disclosure, shellcheck]

requires:
  - phase: 01-publication-gate
    provides: "scan config, 15-fingerprint accepted list, hooks, deny-list check, scratch-guarded throwaway-clone test script"
provides:
  - "scripts/prepublish-check.sh: read-only pre-flip tool (fresh mirror scan, metadata and trailer checks, deny-list history scan, live-repo inventory against the reviewed baseline, exclusive-create record writer)"
  - "History mode for the deny-list check (--history GITDIR)"
  - "Negative-control test case: a seeded leak under a foreign identity makes the tool FAIL (18 named checks in total)"
  - "README section Known issues and limits (row 7, carried-forward rows, shipped skill digest never run, NUL -z form)"
  - "CHANGELOG Publication gate and disclosure bullets; publication sentence made true before and after the flip"
affects: [01-04-flip-checkpoint, phase-04]

actuals:
  tokens: 5477
  tasks: 2
  commits: 2
plan_head_before: 3569c5c9af62abe1aff028bcf10f6cb6a7681647
plan_head_after: 4f9fd169bd67867c83e76d9bc1277a6eaaebea16

tech-stack:
  added: []
  patterns:
    - "Pre-flip scan runs on a fresh --mirror clone, with config and accepted list taken from the mirror's HEAD, so the committed files are what is proven"
    - "A fingerprint set compared by python3 -I against the accepted list, printing counts only"
    - "Inventory compares the set of activity event types, not a push count that rises with every push"
    - "Record file created exclusively under noclobber; a rehearsal refuses --record outright"

key-files:
  created:
    - scripts/prepublish-check.sh
  modified:
    - .githooks/checks/denylist.sh
    - scripts/test-hooks.sh
    - README.md
    - CHANGELOG.md

key-decisions:
  - "The tool calls the local copy of the deny-list check in history mode, so it works even when the remote's HEAD predates the history mode"
  - "The anonymous HTTP status and anonymous ls-remote probes are one inventory category (public-probe)"
  - "A gh call that errors is reported as the observed value 'error', so an unreachable category fails closed instead of passing"
  - "The CHANGELOG replacement sentence names the paths in backticks, as the rest of the file does"

patterns-established:
  - "Every new tool behavior gets a negative-control case in the throwaway-clone script, so a green run cannot be vacuous"
  - "Scripts in this repo name no forbidden write verb even in comments, because a whole-file grep gates them"

requirements-completed: [PUB-02, PUB-05, PUB-06]

coverage:
  - id: D1
    description: "Rehearsal of the pre-flip tool on the real repository passes owner-clone-config, mirror-cloned, strict-equals-accepted (15 fingerprints, all in d437af2), gate-clean, tree-clean, one-identity, no-attribution-trailers and denylist-history, skips the remote tip check, and prints INVENTORY OK"
    requirement: PUB-02
    verification:
      - kind: integration
        ref: "sh scripts/prepublish-check.sh --rehearse"
        status: pass
    human_judgment: false
  - id: D2
    description: "The tool is not vacuous: a throwaway clone holding a seeded leak under a foreign identity makes it print FAIL for gate-clean, strict-equals-accepted and one-identity and exit non-zero, without printing the seed"
    requirement: PUB-02
    verification:
      - kind: integration
        ref: "sh scripts/test-hooks.sh#prepublish-detects-seed-and-foreign-identity"
        status: pass
    human_judgment: false
  - id: D3
    description: "The live-repository inventory compares 25 categories with the reviewed baseline and reports UNREVIEWED for any deviation (seen to fire on an unrelated public repository; INVENTORY OK on this one)"
    requirement: PUB-05
    verification:
      - kind: integration
        ref: "sh scripts/prepublish-check.sh --rehearse (INVENTORY OK); scratch clone pointed at an unrelated public repository (23 FAIL inv lines)"
        status: pass
    human_judgment: false
  - id: D4
    description: "The tool is read-only against GitHub: no write verb or flag in the file, rehearsal refuses --record and creates no file, a second record run refuses to overwrite"
    requirement: PUB-05
    verification:
      - kind: unit
        ref: "grep gate over scripts/prepublish-check.sh exits 1; rehearse plus record exits 2 with no file; second record run exits 2"
        status: pass
    human_judgment: false
  - id: D5
    description: "README and CHANGELOG disclose row 7, the rows carried forward, the shipped skill digest no matrix row ran, and the NUL -z form; the old publication sentence is gone; the Roadmap is byte-identical"
    requirement: PUB-06
    verification:
      - kind: other
        ref: "grep counts on README.md and CHANGELOG.md; digest claims re-checked against SKILL.md and tests/evidence; staged gitleaks run; diff against 56e155c over frozen paths empty"
        status: pass
    human_judgment: true
    rationale: "Whether the shipped-digest bullet is published as written is bokiko's decision at the plan 01-04 checkpoint; the facts are verified, the publishing choice is not automatable"

duration: 12min
completed: 2026-10-22
status: complete
---

# Phase 1 Plan 3: Pre-flip tool and disclosure Summary

**Read-only pre-flip tool that scans a fresh mirror (strict equals the 15 accepted fingerprints, gate and tree clean, one identity, no trailers, deny-list history) and checks the live repository against the reviewed inventory, proven non-vacuous by a seeded-leak negative control, plus the README and CHANGELOG disclosure of row 7, carried-forward rows, the never-run shipped digest and the NUL form**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-22T04:27:19Z
- **Completed:** 2026-10-22T04:39:19Z
- **Tasks:** 2
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- `scripts/prepublish-check.sh` clones a mirror into a new temporary directory and runs ten checks in the order the plan names, printing one PASS, SKIP or FAIL line each. Rehearsal on this repository passes every check, prints the tip-check skip line and INVENTORY OK.
- The strict check compares the scan's fingerprint set to `.gitleaksignore` as a set with `python3 -I`, and asserts 15 members, commit `d437af2` only and the two home-path rules only. Output is counts only.
- The inventory covers 25 categories (visibility, refs, tags, branches, hooks, keys, issues, pull requests, Actions runs, workflows, artifacts, secrets and variables, wiki, Pages, releases, forks, collaborators, invitations, environments, deployments, activity event types, an anonymous public probe). A deviating or erroring category prints FAIL and UNREVIEWED. INFO lines report the security setting, topic and label counts and the community health figure without asserting them.
- The record writer creates its file exclusively in default mode after a clean run, with the fixed layout 01-04 will verify. Rehearsal refuses `--record`.
- `.githooks/checks/denylist.sh` has a history mode that counts added lines across all refs of a git directory and prints counts only.
- The negative-control case (`prepublish-detects-seed-and-foreign-identity`) takes the suite to 18 PASS lines.
- README has `## Known issues and limits` above the Roadmap. CHANGELOG has the two new bullets and the corrected publication sentence.

## Task Commits

1. **Task 1: Read-only pre-flip tool with a negative-control test** - `2698cd9` (feat)
2. **Task 2: Disclose the known issues and correct the publication sentence** - `4f9fd16` (docs)

**Plan metadata:** committed after this file (docs: complete plan)

_TDD note: Task 1 carries `tdd="true"`. The RED step was run and observed before any tool code existed: the new case printed FAIL because the script was missing, with the other 17 cases passing. The plan specifies one commit for the task, so RED and GREEN share commit `2698cd9` rather than separate test and feat commits._

## Files Created/Modified

- `scripts/prepublish-check.sh` - the read-only pre-flip tool (mode 100755)
- `.githooks/checks/denylist.sh` - history mode added (second argument is a git directory)
- `scripts/test-hooks.sh` - negative-control case, 18 named checks
- `README.md` - Known issues and limits section
- `CHANGELOG.md` - Publication gate and disclosure bullets, corrected publication sentence

## Decisions Made

- The tool runs the local copy of the deny-list check in history mode, not the mirror's copy, so a remote whose HEAD predates the history mode still gets scanned.
- The two anonymous probes (HTTP status and anonymous ls-remote) form one inventory category, so one deviation shows as one UNREVIEWED line.
- A GitHub call that fails reports the observed value `error`, which never equals a baseline, so an unreachable category fails closed.
- The CHANGELOG replacement sentence puts the three paths in backticks, matching the file's convention. The plan's sentence had none.
- The README text states only what the plan specifies. It asserts no decision date for row 7.

## Deviations from Plan

None - plan executed exactly as written.

Two small defects in the new script were found and fixed before its commit, so they never reached history: a skipped inventory wrote its record row twice, and the security-setting INFO line printed empty instead of `null`. Both are covered by the re-run verification.

## Issues Encountered

- The first attempt to prove the inventory can fail used a git environment override for the origin URL. It only appended a second URL, so the run still checked this repository and passed. The proof was redone in a scratch clone whose origin points at an unrelated public repository; the tool then printed 23 FAIL and UNREVIEWED pairs, as it should. Only read calls were made.
- `scripts/test-hooks.sh` prints the path of its kept throwaway directory to the terminal, as it did before this plan. It is never written to a committed file.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

For plan 01-04:

- **Default mode will fail the tip check today.** The remote `main` is behind local HEAD (the earlier plan commits and this plan's are not pushed). `sh scripts/prepublish-check.sh` in default mode prints FAIL remote-tip-equals-head until the push the go-word authorizes. Rehearsal is unaffected.
- **Run default mode with `--record`** to write `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md`. The file must not already exist.
- **Needs bokiko's decision at the checkpoint:** whether the README bullet "Shipped skill digest not run" is published as written, edited or dropped. The digest `86e5b14e64b1` equals the SHA-256 prefix of the current `SKILL.md` and occurs nowhere under `tests/evidence`; `6d22a71e7f3c` occurs in the evidence tree.
- The disclosure commit `4f9fd16` is reachable from HEAD, so the ancestor check can use it.
- No history rewrite, push, visibility change or other GitHub write happened in this plan.

## Self-Check: PASSED

- Created and modified files exist: scripts/prepublish-check.sh, .githooks/checks/denylist.sh, scripts/test-hooks.sh, README.md, CHANGELOG.md
- Commits `2698cd9` and `4f9fd16` are ancestors of HEAD
- Plan-level checks re-run after the last task commit: rehearsal exits 0 with the named PASS lines and INVENTORY OK; the suite prints 18 PASS lines and no FAIL; the write-verb grep exits 1; rehearsal with record exits non-zero with no file; shellcheck is clean on all nine scripts; frozen and historical paths are unchanged since `56e155c`

---
*Phase: 01-publication-gate*
*Completed: 2026-10-22*
