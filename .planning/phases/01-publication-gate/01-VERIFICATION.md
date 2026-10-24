---
phase: 01-publication-gate
verified: 2026-10-24T12:10:00Z
status: human_needed
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
covered_digest: "v3:sha256:b4f6f54c0a26591f73b30293aed4419bfa15d101eb1b87038f5b66ba2f97cf39"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Confirm you wrote the exact go-word (go public) in your own message before the visibility flip on 2026-10-24"
    expected: "Yes. The flip, both protection toggles and the read-back were run only after that message, by the main conversation."
    why_human: "The go-word lives in the conversation. No file, commit or API read can show who authorised the flip. The summary records it as human judgment, and the read-back timestamp (2026-10-24) is consistent with it but does not prove it."
---

# Phase 1: Publication Gate Verification Report

**Phase Goal:** The repository is public on GitHub with nothing unreviewed in its history, tree or live settings, and the visibility changes only after bokiko says so in the conversation.
**Verified:** 2026-10-24
**Status:** human_needed
**Re-verification:** No, initial verification

Every observable truth holds in the code and on the live repository. One item cannot be checked from files: that the flip followed bokiko's own go-word. It is listed for confirmation and is not a gap.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Three owner decisions dated in PROJECT.md; repo-local config pins identity with `user.useConfigOnly`; wrong-identity push and AI-trailer commit are refused | VERIFIED | PROJECT.md Key Decisions has the no-rewrite, public-identity and row 7 rows, each "Decided 2026-10-21". Local config shows `user.useconfigonly=true`, `user.name`, `user.email`, `preclear.pinnedidentity` and `core.hookspath=.githooks`. `sh scripts/test-hooks.sh` printed PASS for identity-wrong-author-committer, identity-committer-only, identity-wrong-tagger, trailer-commit-msg and trailer-bypassed-prepush. |
| 2 | Fresh `--mirror` scan with committed config yields exactly the 15 accepted fingerprints (the roadmap's two accepted findings, measured as eleven lines in ten files) and nothing else; config and accepted list are committed | VERIFIED | `sh scripts/prepublish-check.sh --skip-inventory` run live: strict-equals-accepted PASS (exit 2, 15 fingerprints equal the list, all in d437af2), gate-clean PASS, tree-clean PASS, one-identity PASS, no-attribution-trailers PASS, denylist-history PASS. `.gitleaks.toml` and `.gitleaksignore` are tracked; the ignore file has 15 fingerprint lines. The author email is covered by the one-identity metadata check. |
| 3 | Seeded fake leak blocked by pre-commit and pre-push, seed never in history, hook config committed, fresh clone enables with one command | VERIFIED | test-hooks PASS: leak-seed-precommit, leak-seed-prepush, leak-seed-absent-on-remote, fresh-clone-hooks-off-by-default, fresh-clone-enable-blocks-seed, fail-closed-no-scanner, real-origin-refs-unchanged. All hook files are tracked, mode 100755 except the two data files. Full-history gitleaks over the real repo passes. |
| 4 | Row 7, carried-forward rows and NUL `-z` form disclosed and committed before the flip; same-session live inventory shows nothing unreviewed | VERIFIED | README `## Known issues and limits` discloses row 7, rows 1, 2, 3c, 4b on earlier digests, the unrun shipped digest and the NUL form. Commit 4f9fd16 added it and is an ancestor of the flip tip 9a794e7. The committed pre-flip record reads Result PASS across 24 inventory categories and 10 checks, with tip ab2e345. |
| 5 | After the go-word the repo is public with secret scanning and push protection enabled; before it, private | VERIFIED (go-word provenance: human item) | Live `gh` read: visibility PUBLIC, not private, secret scanning enabled, push protection enabled. Anonymous page returns 200. The pre-flip record shows PRIVATE and an anonymous 404 before the flip. The read-back record matches the live state. |

**Score:** 5/5 truths verified, 0 behavior-unverified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.githooks/pre-push`, `pre-commit`, `commit-msg` | Hooks that fan out to checks | VERIFIED | Tracked, executable, exercised by the passing test script |
| `.githooks/checks/leaks.sh`, `identity.sh`, `denylist.sh` | Scan, identity and deny-list checks | VERIFIED | Tracked, executable, wired from the hooks |
| `.githooks/attribution.ere` | Single trailer pattern file | VERIFIED | Four patterns; zero history lines match |
| `.gitleaks.toml`, `.gitleaksignore` | Config and 15 fingerprints | VERIFIED | Used by the live mirror scan |
| `scripts/test-hooks.sh` | Throwaway-clone suite | VERIFIED | 18 PASS lines, no FAIL |
| `scripts/prepublish-check.sh` | Read-only pre-flip tool | VERIFIED | Ran live; negative control PASS in test-hooks |
| `README.md`, `CHANGELOG.md` | Disclosure | VERIFIED | Section present at README line 275; CHANGELOG carries the gate and disclosure bullets |
| `.claude/settings.json`, `.claude/CLAUDE.md` | No-trailer suppression | VERIFIED | Tracked; zero trailer matches in history |
| `01-PREFLIP-INVENTORY.md`, `01-POSTFLIP-READBACK.md` | Gate records | VERIFIED | Both present with the required lines |

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| pre-push | checks/*.sh | WIRED | Ranges file fans out; leak and identity refusals proven by test |
| identity check | attribution.ere | WIRED | trailer-bypassed-prepush PASS |
| pre-commit | denylist.sh | WIRED | denylist-precommit PASS |
| prepublish-check | config and ignore list | WIRED | Live mirror scan used the committed files |
| Post-flip record | live state | WIRED | Live re-read agrees on visibility and both toggles |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Hook suite | `sh scripts/test-hooks.sh` | 18 PASS, none FAIL, real origin refs unchanged | PASS |
| Mirror scan | `sh scripts/prepublish-check.sh --skip-inventory` | All scan checks PASS; one expected FAIL, see warning below | PASS |
| Two unpushed docs commits | `gitleaks git` over the range after the remote tip | No leaks found | PASS |
| Frozen paths untouched | `git diff` of SKILL.md, references, tests/fixtures, tests/evidence against the pre-phase tip | Empty; SKILL.md is 11,994 bytes, under the 12,000 cap | PASS |
| Independent bare-home-path probe | Count-only grep of tree and all history for a home path with no trailing slash | 0 and 0 | PASS |
| Private-range IPv4 in tree | Count-only grep | 0 | PASS |
| Single identity | `git log --all` author and committer, unique | 1 line | PASS |

### Probe Execution

No phase-declared probe scripts beyond the two scripts above. SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| PUB-01 | 01-01 | SATISFIED | Three dated decision rows in PROJECT.md |
| PUB-02 | 01-02, 01-03, 01-04 | SATISFIED | Live mirror scan equals the accepted list; pre-flip record PASS |
| PUB-03 | 01-01, 01-02 | SATISFIED | Seed blocked at both hooks; fresh-clone enable proven |
| PUB-04 | 01-01 | SATISFIED | Config pin plus identity and trailer refusals |
| PUB-05 | 01-03, 01-04 | SATISFIED | 24-category inventory recorded before the flip |
| PUB-06 | 01-03 | SATISFIED | README section precedes the flip tip |
| PUB-07 | 01-04 | SATISFIED, pending human confirmation | State verified live; go-word provenance is the human item |

All seven IDs appear in plan frontmatter and in REQUIREMENTS.md. No orphaned Phase 1 requirements.

### Anti-Patterns Found

No unreferenced TBD, FIXME or XXX markers surfaced in the scanned phase files. No stubs. Data flow is not applicable to shell tooling.

### Warnings (non-blocking)

- **Unpushed local commits.** Local HEAD is two documentation commits ahead of the public tip. The pre-flip tool reports remote-tip-equals-head FAIL for that reason only. The pending commits scan clean, and the pre-push hook will gate them.
- **Review CR-03 (bare home path rule).** The rule needs a trailing slash after the user segment. This weakens the scanner's recall going forward. I checked the tree and full history directly for the bare form and found none, so the public content is not affected. It should be fixed before Phase 2 commits.
- **Review CR-01 and CR-02 (hooks fail open if the pattern file is missing or a check loses its executable bit).** Hooks are tracked as executable and the pattern file is present, so the tested gate holds. The stranger-clone case is a hardening item.
- The other 17 review findings are advisory and all remain open in the disposition file.

### Human Verification Required

#### 1. Go-word provenance

**Test:** Confirm the flip followed your own message containing "go public".
**Expected:** Yes, and no subagent ran the visibility change or protection toggles.
**Why human:** The authorisation exists only in the conversation, not in any file or API record.

### Gaps Summary

No gaps. The repository is public with both protections on, history and tree are clean against the accepted list, the disclosure and pre-flip record precede the flip, and the hooks and identity pin work as specified. The single open item is a human confirmation of the go-word.

---

_Verified: 2026-10-24_
_Verifier: Claude (gsd-verifier)_
