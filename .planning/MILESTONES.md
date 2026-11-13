# Milestones

## v1.0 Public and Reproducible (Shipped: 2026-11-13)

**Delivered:** The preclear repository is public behind identity, leak and attribution gates, and its acceptance matrix (three layouts plus twelve publication rows) is reproducible by a stranger from a clean clone: one zero-token self-test, then one paid command that files a dated, leak-gated, Codex-reviewed baseline.

**Phases completed:** 1-4 (47 plans total)

**Key accomplishments:**
- Repository flipped public on 2026-10-24 on bokiko's own go-word, after a full-history gitleaks scan that reports exactly the 15 accepted fingerprints, with fail-closed pre-commit, pre-push and commit-msg hooks proven in throwaway clones and a 24-category live inventory recorded before the flip.
- Model-free foundation in standard-library Python 3.9: a single-file `checkpoint-v1` stub (15 of 15 recorded calls replay), exclusive run roots, filename-safe snapshots, a run-time deny-list sanitizer and a fail-closed leak gate, all behind `tests/harness/selftest` at zero tokens.
- Two paid spikes (0.26 USD) pinned Claude Code 2.1.310 and claude-sonnet-5-5 and decided strict isolation with run roots outside every home folder.
- Row 1 ran end to end through the real `claude -p` for 0.2723 USD and was filed as sanitized mechanical evidence; six gap-closure plans after five review passes made the write-boundary and git-read-only claims mechanical (open-world Bash write-escape rule, hardened git reads, refile refusals).
- Every one of the 21 matrix entries runs through one spec-driven engine; the paid waves A to D and the row 7 triple cost 5.99 USD and filed every chain, with the row 7 defect listed in a review table instead of hidden.
- The full matrix ran from a clean clone of the public repository (21 of 21 chains, every stage `success`, 5.7467 USD) and is filed as the new baseline `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5`, reviewed by Codex (GPT-6-Astra via Codex CLI 0.167.0, read from the Herdr pane) with 21 per-row verdict lines.

**Stats:**
- 2,852 files created or modified in the milestone range (155,094 insertions, most of them filed evidence)
- 60,532 lines of Python under `tests/harness/` (harness plus tests), 1,155 lines under `scripts/`
- 4 phases, 47 plans, 79 tasks; 2,405 zero-token tests green (3 skipped) on 2026-11-12
- 23 days from the first planning commit (2026-10-21) to ship (2026-11-13)
- Paid model spend for the whole milestone: 12.27 USD (spikes 0.26, row 1 0.27, Phase 4 11.74)

**Git range:** `c80e57a` (docs: map existing codebase) → `29af45e` (phase 1-3 verification refresh)

**Closeout:** verified_closeout. All four phases verified: Phase 4 passed 5/5 on 2026-11-12; Phases 1 to 3 were re-verified on 2026-11-13 (5/5, 6/6, 6/6) because later phases had changed their covered files and the earlier reports read stale. Four SECURITY.md files close with `threats_open: 0`; T-02-15 is an accepted risk (AR-02-03) with a follow-up in STATE.md. Pre-close artifact audit: all clear, 0 acknowledged items, 0 carried forward. No `/gsd-audit-milestone` was run; 40 of 40 v1 requirements are checked and every phase is verified.

**Known gaps carried forward:** row 7 has no clean rerun (Codex: safe denial, evidence claim overstated; attempt 3 of the triple printed its checkpoint unfenced); Codex flags on rows 6 and 10 of the baseline; Phase 4 review warnings WR-01 to WR-05 and the unreviewed 04-22 code; the T-02-15 `refuse_under` wiring; the harness README's "no network" opening line.

**What's next:** not yet defined. Candidates: close the measured defects (row 7, rows 6 and 10) with a paid rerun, wire the accepted security follow-up, and decide on CI.

---
