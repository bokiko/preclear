---
phase: 01-publication-gate
verified: 2026-11-13T15:30:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - ".claude/CLAUDE.md"
  - ".claude/settings.json"
  - ".githooks/README.md"
  - ".githooks/attribution.ere"
  - ".githooks/checks/denylist.sh"
  - ".githooks/checks/identity.sh"
  - ".githooks/checks/leaks.sh"
  - ".githooks/commit-msg"
  - ".githooks/pre-commit"
  - ".githooks/pre-push"
  - ".gitleaks.toml"
  - ".gitleaksignore"
  - ".planning/PROJECT.md"
  - ".planning/phases/01-publication-gate/01-01-PLAN.md"
  - ".planning/phases/01-publication-gate/01-01-SUMMARY.md"
  - ".planning/phases/01-publication-gate/01-02-PLAN.md"
  - ".planning/phases/01-publication-gate/01-02-SUMMARY.md"
  - ".planning/phases/01-publication-gate/01-03-PLAN.md"
  - ".planning/phases/01-publication-gate/01-03-SUMMARY.md"
  - ".planning/phases/01-publication-gate/01-04-PLAN.md"
  - ".planning/phases/01-publication-gate/01-04-SUMMARY.md"
  - "CHANGELOG.md"
  - "README.md"
  - "scripts/prepublish-check.sh"
  - "scripts/test-hooks.sh"
covered_digest: "v3:sha256:fb91b84187336e1ae4ea0e32e10328762d3bb1abc9a8e444bed99866c46e6258"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 1: Publication Gate Verification Report

**Phase Goal:** The repository is public on GitHub with nothing unreviewed in its history, tree or live settings, and the visibility changes only after bokiko says so in the conversation.
**Verified:** 2026-11-13
**Status:** passed
**Re-verification:** Yes. The 2026-10-24 report was marked stale because `.gitleaks.toml` and `CHANGELOG.md` changed in Phases 2 to 4. Every truth was re-checked on the current tree.

The goal still holds. The two changed covered files were extended, not weakened. The hook scripts, the accepted-fingerprint list and the prepublish tool are byte-identical to the previously verified state.

## What changed in covered files since the last report

| File | Change | Effect on Phase 1 truths |
|------|--------|--------------------------|
| `.gitleaks.toml` | Phase 2 (62f0170) widened the home-path rule to end at any non-name character and made the internal-hostname suffix case-insensitive | Stricter. Re-ran the strict mirror scan: still exactly the 15 accepted fingerprints, none extra, none missing |
| `CHANGELOG.md` | Phase 4 added one bullet for the harness and the new baseline | None. No home path, address or attribution text |
| `.planning/PROJECT.md` | Evolved by later phase transitions | Phase 1 decision rows still present and dated 2026-10-21 |
| Hooks, `.gitleaksignore`, `scripts/*`, `README.md`, `.claude/*` | No diff against the previously verified tip | None |

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Three owner decisions dated in PROJECT.md; repo-local config pins identity with `user.useConfigOnly`; wrong-identity push and AI-trailer commit are refused | VERIFIED | PROJECT.md rows for no history rewrite, public identity and row 7 are present, dated 2026-10-21. Local config reads `user.useconfigonly=true`, `user.name=bokiko`, a set `preclear.pinnedidentity`. `sh scripts/test-hooks.sh` run now: exit 0, 29 PASS, 0 FAIL, including identity-wrong-author-committer, identity-committer-only, trailer-commit-msg and trailer-bypassed-prepush |
| 2 | Fresh `--mirror` scan with committed config yields exactly the accepted fingerprints and nothing else; config and accepted list committed | VERIFIED | Fresh mirror clone, config and ignore list taken from HEAD. Strict scan (ignore list off): exit 2, 19 matches, 15 unique fingerprints, all in d437af2, rules home-path-unix and home-path-dash-slug, set equal to `.gitleaksignore` (0 extra, 0 missing). Gate scan (ignore list on): exit 0, 355 commits, no leaks found. Scan of the tracked tree via `git archive`: no leaks found. Both files tracked |
| 3 | Seeded fake leak blocked by pre-commit and pre-push, seed never in history, hook config committed, fresh clone enables with one command | VERIFIED | Test suite PASS: leak-seed-precommit, leak-seed-prepush, leak-seed-absent-on-remote, fresh-clone-hooks-off-by-default, fresh-clone-enable-blocks-seed, fail-closed-no-scanner, prepush-nonexecutable-check-fail-closed, real-origin-refs-unchanged. Hooks tracked, mode 100755. The pre-push script fans out to every `checks/*.sh` and fails closed on a non-executable or missing check |
| 4 | Row 7, carried-forward rows and the NUL `-z` form disclosed and committed before the flip; same-session live inventory shows nothing unreviewed | VERIFIED | README `## Known issues and limits` covers row 7, rows 1, 2, 3c and 4b, the shipped digest gap and the NUL `-z` form. Commit 4f9fd16 added it and is an ancestor of the flip tip 9a794e7. The pre-flip record reads `Result: PASS` with scanned tip ab2e345 |
| 5 | After the go-word the repo is public with secret scanning and push protection enabled; before it, private | VERIFIED | Live read-only `gh`: visibility PUBLIC, private false, secret scanning enabled, push protection enabled. Anonymous page request returns 200. Read-back record matches live state and its flip tip 9a794e7 is an ancestor of HEAD. Go-word provenance was confirmed by bokiko in the conversation on 2026-10-24 and is recorded in the prior report; it is not re-asked |

**Score:** 5/5 truths verified, 0 behavior-unverified.

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `.githooks/pre-push`, `pre-commit`, `commit-msg` | VERIFIED | Tracked, 100755, exercised by the passing suite |
| `.githooks/checks/leaks.sh`, `identity.sh`, `denylist.sh` | VERIFIED | Tracked, 100755, wired from the hooks |
| `.githooks/attribution.ere` | VERIFIED | Zero lines in all-ref history match it |
| `.gitleaks.toml`, `.gitleaksignore` | VERIFIED | Used by the scans above |
| `scripts/test-hooks.sh` | VERIFIED | 29 PASS. The only hook-skipping commit sits inside the guarded scratch helper |
| `scripts/prepublish-check.sh` | VERIFIED | Unchanged. No repository-edit command, write method, field flag or push found by grep |
| `README.md`, `CHANGELOG.md` | VERIFIED | Disclosure section present; Public release item ticked after the flip |
| `.claude/settings.json`, `.claude/CLAUDE.md` | VERIFIED | Tracked; zero trailers in history |
| `01-PREFLIP-INVENTORY.md`, `01-POSTFLIP-READBACK.md` | VERIFIED | Both present with the required lines (Result PASS, Visibility PUBLIC, both protections enabled, page status 200) |

### Key Link Verification

| From | To | Status |
|------|----|--------|
| pre-push | checks/*.sh | WIRED, glob loop read and proven by suite |
| identity check | attribution.ere | WIRED, trailer-bypassed-prepush and attribution-pattern-fail-closed PASS |
| pre-commit | denylist.sh | WIRED, denylist-precommit PASS |
| prepublish-check | committed config and ignore list | WIRED, proven by the equivalent live scans above |
| Post-flip record | live state | WIRED, live re-read agrees |
| Go-word checkpoint | visibility change | WIRED (human), confirmed by bokiko |

### Behavioral Spot-Checks

| Behavior | Check | Result | Status |
|----------|-------|--------|--------|
| Hook suite | `sh scripts/test-hooks.sh` in throwaway clones | exit 0, 29 PASS, real repository refs and HEAD unchanged afterwards | PASS |
| Strict mirror scan | gitleaks, committed config, ignore list off | 15 fingerprints equal accepted list | PASS |
| Gate mirror scan | gitleaks, committed config and list | no leaks in 355 commits | PASS |
| Tracked-tree scan | gitleaks on `git archive HEAD` | no leaks | PASS |
| Single identity | unique author and committer over all refs | 1 | PASS |
| Attribution trailers | all-ref messages against the pattern file | 0 | PASS |
| Home paths in tracked files outside evidence and planning | count-only `git grep` at HEAD | 0 | PASS |
| Private-range IPv4 in tracked files | `git grep -l` at HEAD | none | PASS |
| Remote tip equals local HEAD | `git ls-remote` against HEAD | both 694f29a | PASS |
| Live visibility and protections | read-only `gh repo view` and `gh api` | public, both protections enabled, page 200 | PASS |

The harness self-test suite was not run, per the orchestrator's instruction.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| PUB-01 | 01-01 | SATISFIED | Three dated decision rows in PROJECT.md |
| PUB-02 | 01-02, 01-03, 01-04 | SATISFIED | Strict scan equals the accepted list; gate scan clean on current HEAD |
| PUB-03 | 01-01, 01-02 | SATISFIED | Seed blocked at both hooks; fresh-clone enable proven by suite |
| PUB-04 | 01-01 | SATISFIED | Config pin plus identity and trailer refusals |
| PUB-05 | 01-03, 01-04 | SATISFIED | Pre-flip record PASS, 24 inventory categories, committed before the flip |
| PUB-06 | 01-03 | SATISFIED | README section is an ancestor of the flip tip |
| PUB-07 | 01-04 | SATISFIED | Live state public with both protections; go-word confirmed by bokiko; post-flip record committed |

All seven IDs appear in plan frontmatter and in REQUIREMENTS.md, all marked complete. No orphaned Phase 1 requirements.

### Anti-Patterns Found

No TBD, FIXME or XXX debt markers in phase files. The grep hits are the template placeholder in temporary-file names. No stubs. Data flow does not apply to shell tooling.

### Warnings (non-blocking, not gaps)

- **Working-tree scan noise is not a leak.** A scan of the working directory (not the tracked tree) reports thousands of home-path matches. All sit under `runs/`, which is gitignored and has zero tracked files. The tracked-tree and full-history scans are clean.
- **Evidence added by later phases.** Nine commits under `tests/evidence/` landed after the flip (Phases 3 and 4). `SKILL.md` and `references/` had none. Every one is inside the history scan, which is clean.
- **README disclosure wording is pre-flip.** It still says three row 7 reruns are planned and the full rerun is pending. Phase 4 has since done them and PROJECT.md records the outcome. PUB-06 requires disclosure before the flip, which holds. Refreshing the wording belongs to milestone docs, not this phase.
- **Local `core.hooksPath` is absolute.** This is the environment artifact already recorded in STATE.md. The pin and the hook behavior are unaffected. The hook suite passes.
- **Owner deny-list entries were never exercised** (carried from the earlier report). The local deny list is empty or missing, so history deny-list scanning covered host-name entries only. Add entries before the next gate run.
- **CR-03 residual** (carried). Windows-style home paths and `/root/` are not covered by the home-path rule.

### Gaps Summary

No gaps. The repository is public with both protections on. History and tracked tree are clean against the accepted list on the current tree after the later rule changes. The disclosure and pre-flip record precede the flip. The hooks and identity pin behave as specified.

---

_Verified: 2026-11-13_
_Verifier: Claude (gsd-verifier)_
