---
phase: 01-publication-gate
plan: 04
subsystem: infra
tags: [publication, visibility-flip, secret-scanning, push-protection, human-gate, read-back]

requires:
  - phase: 01-publication-gate
    provides: "pre-flip tool, scan config, 15-fingerprint accepted list, hooks, disclosure commit"
provides:
  - "01-PREFLIP-INVENTORY.md: generated record of the fresh-mirror scan (9 checks PASS) and the 24-category live inventory against the remote, Result PASS"
  - "01-POSTFLIP-READBACK.md: committed read-back of the flip (PUBLIC, secret scanning enabled, push protection enabled, anonymous page 200, Result PASS)"
  - "The repository is public, with secret scanning and push protection on, flipped only on bokiko's own go-word"
affects: [phase-02, phase-03, phase-04]

actuals:
  tokens: 717
  tasks: 5
  commits: 3
plan_head_before: eecc86a23ffae7752c1f8c7e10706412c8c195ae
plan_head_after: 55835ad80817ba4f0b31bfde6b3d74621e5cf6ff

tech-stack:
  added: []
  patterns:
    - "Gated one-way step: evidence record, then an explicit go-word in the owner's own message, then released steps run by the main conversation only, then a committed read-back checked read-only"
    - "Anonymous probes run with global and system git config disabled and credential helpers off, so stored credentials cannot make a private repository look reachable"

key-files:
  created:
    - .planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md
    - .planning/phases/01-publication-gate/01-POSTFLIP-READBACK.md
  modified:
    - .planning/config.json

key-decisions:
  - "Go-word given by bokiko in his own message on 2026-10-24; checkpoint items a to e kept their defaults and item f needed no change, so no commit sits between the record push and the flip"
  - "The flip tip is the pre-flip record commit; the read-back commit is its only child"

patterns-established:
  - "An anonymous-access probe is only valid with git config and credential helpers disabled; the first unconfigured probe is not evidence"

requirements-completed: [PUB-02, PUB-05, PUB-07]

coverage:
  - id: D1
    description: "Fresh mirror of the remote scanned at tip ab2e345: strict equals the 15 accepted fingerprints (all in d437af2), gate and tree clean, one identity, no attribution trailers, deny-list history 0, inventory PASS across 24 categories"
    requirement: PUB-02
    verification:
      - kind: integration
        ref: "sh scripts/prepublish-check.sh --record .planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md (rc 0, Result PASS)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Live-repo inventory recorded in the same session as the go or no-go, nothing unreviewed"
    requirement: PUB-05
    verification:
      - kind: integration
        ref: "01-PREFLIP-INVENTORY.md category table, 24 rows, expected equals observed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Before the go-word the repository was PRIVATE, the anonymous page returned 404 and anonymous ls-remote was refused; after the released steps it reads PUBLIC with secret scanning and push protection enabled and the anonymous page returns 200"
    requirement: PUB-07
    verification:
      - kind: integration
        ref: "01-POSTFLIP-READBACK.md plus the five task 5 verify commands (record lines, tip lineage, live re-read, identity and trailer, frozen paths)"
        status: pass
    human_judgment: false
  - id: D4
    description: "The flip happened only on bokiko's explicit go-word, run by the main conversation alone, with no hook skipped and no history rewrite or deletion"
    requirement: PUB-07
    verification:
      - kind: other
        ref: "Task 3 checkpoint answer and task 4 transcript, reviewed by the main conversation"
        status: pass
    human_judgment: true
    rationale: "The go-word is bokiko's own message; no script can verify who said it"

duration: 2 days wall clock (waiting on the human decision; active work about one session)
completed: 2026-10-24
status: complete
---

# Phase 1 Plan 4: Pre-flip record, go-word and visibility flip Summary

**Fresh-mirror scan and 24-category inventory recorded against the remote (PASS), then, on bokiko's own go-word, the repository was flipped public with secret scanning and push protection enabled and the read-back committed and checked**

## Performance

- **Duration:** 2 days wall clock, most of it waiting on the go or no-go decision
- **Started:** 2026-10-22
- **Completed:** 2026-10-24
- **Tasks:** 5 (two human-gated checkpoints, one decision checkpoint, two automated)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- The Phase 1 commits were pushed to the private origin with the hooks on, so the scan read exactly what GitHub held. The repository was confirmed private afterwards.
- The pre-flip tool ran in record mode against a fresh mirror. Every check passed: owner clone config, mirror cloned, remote tip equals head, strict equals accepted (15 fingerprints, all in `d437af2`), gate clean, tree clean, one identity, no attribution trailers, deny-list history 0. The inventory passed across 24 categories. Scanned tip `ab2e34509ed9a45af649127c8774fae9d988fa92`, gitleaks 8.30.0.
- bokiko answered the go or no-go checkpoint on 2026-10-24 and wrote "go public" in his own message.
- The main conversation re-asserted the private state, pushed the record commit, flipped visibility, enabled secret scanning and push protection, read all three back, and wrote and pushed the read-back record. The flip tip is `9a794e775f79bc54d900a0226c0a5877f0abfcae`.
- Task 5 passed all five read-only checks, including a live re-read that agrees with the record.

## Task Commits

1. **Task 1: Push the Phase 1 commits to the private origin** - no commit; pushes `56e155c..eecc86a` and `eecc86a..ab2e345` run by the main conversation on bokiko's instruction, hooks on
2. **Task 2: Pre-flip gate against the remote, record, commit only the record** - `9a794e7` (Record the pre-publication scan and live-repo inventory)
3. **Task 3: Go or no-go checkpoint** - no commit; "go public" received 2026-10-24
4. **Task 4: Released steps and read-back record** - `55835ad` (Record the post-flip read-back); record push `ab2e345..9a794e7` and read-back push `9a794e7..55835ad`
5. **Task 5: Read-only check of the record and live state** - no commit, all verifies PASS

Between task 1's two pushes, `ab2e345` (chore: clear the stale auto-chain flag in config) was committed to clear a stale orchestrator flag. It sits before the scan, so it is part of the scanned tip.

**Plan metadata:** committed after this file (docs: update state, roadmap and requirements)

## Files Created/Modified

- `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md` - generated pre-flip record, Result PASS
- `.planning/phases/01-publication-gate/01-POSTFLIP-READBACK.md` - read-back record: Visibility PUBLIC, Secret scanning enabled, Push protection enabled, Unauthenticated page status 200, Result PASS
- `.planning/config.json` - stale auto-chain flag cleared (`ab2e345`)

## Decisions Made

- Checkpoint items a to e kept their defaults: the digest-gap README bullet is published as drafted, the PROJECT.md row 7 date is kept, the two Claude Code files are published, the 154 session-id-shaped UUIDs are accepted without adding a decisions line (bokiko did not ask for one), and gitleaks stays on 8.30.0.
- Item f: on 2026-10-24 the main conversation reported that the local deny-list file did not exist, so the name scan covered only machine hostnames. bokiko confirmed there is no other name to scan for, so nothing was added and no re-run was needed.
- Item g: push protection on the free public repository enabled without error on the first attempt; both statuses read enabled on the first read.

## Deviations from Plan

None - plan executed exactly as written.

Notes on how it ran:

- **Anonymous probe false positive:** the first anonymous `ls-remote` probe before the flip unexpectedly succeeded, because the global git credential helper supplied stored credentials. It was repeated with global and system git config disabled and the credential helper empty, and it was refused (exit 128) as the private state requires. The first result was not treated as evidence of anything. The page request (404) and `gh` (PRIVATE) agreed throughout.
- **Executor model:** tasks 1, 3 and 4 were run by the main conversation on bokiko's messages, and task 2 and task 5 as read-only automated checks. No subagent ran any released step.
- **Plan commit count:** the measured count since the plan began is 3 (`ab2e345`, `9a794e7`, `55835ad`); only the last two are plan task commits.

## Issues Encountered

None beyond the probe note above. No FAIL or UNREVIEWED line appeared, so there was no history rewrite, no deletion, no hook skip and no allow-list edit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 execution is complete; phase verification is the remaining step before the orchestrator marks the phase done.
- The repository is public. Phases 2 to 4 commit to a public history, and the hooks and push protection are on.
- The README Roadmap item "Public release" is ticked in a separate commit after this plan.
- Open carry-forward from earlier plans is unchanged: row 7 clean rerun (Phase 4) and the disclosed carried-forward rows.

## Self-Check: PASSED

- Created files exist: `01-PREFLIP-INVENTORY.md`, `01-POSTFLIP-READBACK.md`
- Commits `9a794e7`, `55835ad` and `ab2e345` are ancestors of HEAD
- The read-back record carries exactly one each of the five required lines and no path or at-sign; the flip tip differs from the scanned tip only by the pre-flip record; the read-back commit is its direct child

---
*Phase: 01-publication-gate*
*Completed: 2026-10-24*
