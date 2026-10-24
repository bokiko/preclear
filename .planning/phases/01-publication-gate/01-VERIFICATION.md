---
phase: 01-publication-gate
verified: 2026-10-24T16:10:00Z
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
covered_digest: "v3:sha256:dee26139d75f086df980a0b459003631eecedb153e269db778d75560a8684b66"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  human_items_resolved:
    - "Go-word provenance: bokiko confirmed in his own message in the conversation on 2026-10-24 that he wrote the exact go-word (go public) before the visibility flip."
---

# Phase 1: Publication Gate Verification Report

**Phase Goal:** The repository is public on GitHub with nothing unreviewed in its history, tree or live settings, and the visibility changes only after bokiko says so in the conversation.
**Verified:** 2026-10-24
**Status:** passed
**Re-verification:** Yes. The prior report was human_needed with one open item. The code-review fix pass (eleven commits, 6235b16 to b4ae0bd) changed covered files afterwards, so every truth was re-checked at current HEAD.

All five roadmap truths hold at HEAD. The one open human item, go-word provenance, was resolved by bokiko in the conversation. No gaps remain.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Three owner decisions dated in PROJECT.md; repo-local config pins identity with `user.useConfigOnly`; wrong-identity push and AI-trailer commit are refused | VERIFIED | PROJECT.md decision rows are present and dated. Local config reads `user.useconfigonly=true`, `core.hookspath=.githooks` and a set `preclear.pinnedidentity`. `sh scripts/test-hooks.sh` at HEAD printed PASS for identity-wrong-author-committer, identity-committer-only, identity-wrong-tagger, trailer-commit-msg, trailer-bypassed-prepush and the new attribution-pattern-fail-closed. |
| 2 | Fresh `--mirror` scan with committed config yields exactly the accepted fingerprints and nothing else; config and accepted list committed | VERIFIED | `sh scripts/prepublish-check.sh --rehearse --skip-inventory` at HEAD: strict-equals-accepted PASS (exit 2, 15 fingerprints equal the list, all in d437af2), gate-clean PASS, tree-clean PASS, one-identity PASS, no-attribution-trailers PASS. The CR-03 and WR-07 rule changes did not alter the accepted set. `.gitleaks.toml` and `.gitleaksignore` are tracked. Independent count of home-path lines added in any commit shows only d437af2 (11 lines, the accepted cluster). |
| 3 | Seeded fake leak blocked by pre-commit and pre-push, seed never in history, hook config committed, fresh clone enables with one command | VERIFIED | test-hooks PASS: leak-seed-precommit, leak-seed-prepush, leak-seed-absent-on-remote, fresh-clone-hooks-off-by-default, fresh-clone-enable-blocks-seed, fail-closed-no-scanner, prepush-nonexecutable-check-fail-closed, real-origin-refs-unchanged. Hook files are tracked, mode 100755 except the two data files. |
| 4 | Row 7, carried-forward rows and NUL `-z` form disclosed and committed before the flip; same-session live inventory shows nothing unreviewed | VERIFIED | README `## Known issues and limits` is present. Commit 4f9fd16 added it and is an ancestor of the flip tip 9a794e7. The committed pre-flip record reads Result PASS, 24 inventory categories, scanned tip ab2e345. The flip tip differs from that scanned tip by exactly the record file. |
| 5 | After the go-word the repo is public with secret scanning and push protection enabled; before it, private | VERIFIED | Live read-only `gh` at HEAD: visibility PUBLIC, not private, secret scanning enabled, push protection enabled. Anonymous page returns 200. Pre-flip record shows PRIVATE and anonymous 404. Read-back record matches live state; its flip tip 9a794e7 is an ancestor of HEAD. Go-word provenance: resolved by the human, see below. |

**Score:** 5/5 truths verified, 0 behavior-unverified.

### Human item resolved

| Item | Resolution |
|------|------------|
| Confirm bokiko wrote the exact go-word (go public) in his own message before the flip on 2026-10-24 | Resolved by the human. bokiko confirmed in his own conversation message ("confirmed", 2026-10-24). No longer open. |

### Effect of the fix pass on must-haves

| Change | Effect on a must-have |
|--------|-----------------------|
| Fail-closed hooks (missing pattern file, non-executable check, failed git log, failed awk) | Strengthens truths 1 and 3. Each has a new test case that passes at HEAD. |
| Bare home-path rule (CR-03) and narrowed email allowlist (WR-07) | Truth 2 unchanged: the strict scan still yields exactly the 15 accepted fingerprints. Independent tree and history probes find no unaccepted home path or private IPv4. |
| Default mode of `scripts/prepublish-check.sh` now FAILS the deny-list step when the local deny list is empty | Observed at HEAD: default mode prints FAIL for denylist-history only, every other check PASS; `--rehearse` exits PASS with a SKIP-equivalent note. No must-have is affected. The flip already happened, and its pre-flip and post-flip records are committed and unchanged. The change only makes any future gate run stricter. |
| Test assertions (WR-08) | Negative control now asserts the specific detections. 29 of 29 cases PASS. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.githooks/pre-push`, `pre-commit`, `commit-msg` | Hooks that fan out to checks | VERIFIED | Tracked, executable, exercised by the passing suite |
| `.githooks/checks/leaks.sh`, `identity.sh`, `denylist.sh` | Scan, identity and deny-list checks | VERIFIED | Tracked, executable, wired from the hooks |
| `.githooks/attribution.ere` | Single trailer pattern file | VERIFIED | Zero history lines match it |
| `.gitleaks.toml`, `.gitleaksignore` | Config and 15 fingerprints | VERIFIED | Used by the live mirror scan |
| `scripts/test-hooks.sh` | Throwaway-clone suite | VERIFIED | 29 PASS lines, no FAIL. Commits happen only through the guarded helper |
| `scripts/prepublish-check.sh` | Read-only pre-flip tool | VERIFIED | Ran live. No write verb, no push. Only a read of visibility |
| `README.md`, `CHANGELOG.md` | Disclosure | VERIFIED | Section present; Roadmap item Public release now ticked after the flip |
| `.claude/settings.json`, `.claude/CLAUDE.md` | No-trailer suppression | VERIFIED | Tracked; zero trailer matches in history |
| `01-PREFLIP-INVENTORY.md`, `01-POSTFLIP-READBACK.md` | Gate records | VERIFIED | Both present with the required lines |

CLI check of plan frontmatter: artifacts 9/9, 6/6, 5/5 and 2/2 pass.

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| pre-push | checks/*.sh | WIRED | Fan-out proven by test |
| identity check | attribution.ere | WIRED | trailer-bypassed-prepush and attribution-pattern-fail-closed PASS |
| pre-commit | denylist.sh | WIRED | denylist-precommit PASS |
| prepublish-check | config and ignore list | WIRED | Script reads both from the mirror HEAD; the CLI pattern miss for the config-to-ignore link is a convention link, proven by the live strict and gate scans |
| Post-flip record | live state | WIRED | Live re-read agrees |
| go or no-go checkpoint | visibility change | WIRED (human) | The CLI cannot parse this non-file link. The go-word was confirmed by bokiko |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Hook suite | `sh scripts/test-hooks.sh` | 29 PASS, none FAIL, real origin refs unchanged | PASS |
| Mirror scan, rehearsal | `sh scripts/prepublish-check.sh --rehearse --skip-inventory` | RESULT PASS | PASS |
| Mirror scan, default mode | `sh scripts/prepublish-check.sh --skip-inventory` | All scan checks PASS; denylist-history FAIL because the local list is empty, the intended WR-03 effect | EXPECTED |
| Remote tip equals local HEAD | default-mode check and `git ls-remote` | Both report a778361 | PASS |
| Frozen paths | `git log` over SKILL.md, references, tests/fixtures, tests/evidence after the last pre-phase change | 0 commits; SKILL.md is 11,994 bytes, under the 12,000 cap | PASS |
| Home-path probe, tree | count-only git grep at HEAD | 0 | PASS |
| Private-range IPv4, tree | count-only git grep at HEAD | 0 | PASS |
| Single identity | `git log --all` author and committer, unique | 1 | PASS |
| Attribution trailers | `git log --all` messages against the pattern file | 0 | PASS |

### Probe Execution

No phase-declared probe scripts beyond the two scripts above. SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| PUB-01 | 01-01 | SATISFIED | Three dated decision rows in PROJECT.md |
| PUB-02 | 01-02, 01-03, 01-04 | SATISFIED | Mirror scan equals the accepted list at HEAD; pre-flip record PASS |
| PUB-03 | 01-01, 01-02 | SATISFIED | Seed blocked at both hooks; fresh-clone enable proven |
| PUB-04 | 01-01 | SATISFIED | Config pin plus identity and trailer refusals |
| PUB-05 | 01-03, 01-04 | SATISFIED | 24-category inventory recorded before the flip |
| PUB-06 | 01-03 | SATISFIED | README section precedes the flip tip |
| PUB-07 | 01-04 | SATISFIED | Live state public with both protections; go-word confirmed by bokiko |

All seven IDs appear in plan frontmatter and in REQUIREMENTS.md, all marked complete. No orphaned Phase 1 requirements.

### Anti-Patterns Found

No TBD, FIXME or XXX debt markers in phase files. Fifteen textual hits are the XXXXXX placeholder in temporary-file templates, not markers. No stubs. Data flow is not applicable to shell tooling.

### Warnings (non-blocking, not gaps)

- **Owner deny-list entries were never exercised.** Per the fix report, the local deny list is empty or missing, so the history deny-list scan covered host-name entries only, both before and after the flip. The shape rules and the independent probes found nothing. Default-mode pre-flip runs now fail until bokiko adds entries. Add them before the next gate run.
- **CR-03 residual.** Windows-style home paths and `/root/` are not covered by the home-path rule. Adding rules needs its own accepted-list review.
- **Fix pass landed after the flip.** The eleven fix commits and the review docs reached the public branch after publication. The full-history scan at HEAD covers them and is clean.

### Gaps Summary

No gaps. The repository is public with both protections on. History and tree are clean against the accepted list at current HEAD. The disclosure and pre-flip record precede the flip. The hooks and identity pin work as specified and are stricter after the fix pass. The go-word provenance item is resolved by bokiko.

---

_Verified: 2026-10-24_
_Verifier: Claude (gsd-verifier)_
