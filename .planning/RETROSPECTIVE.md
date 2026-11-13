# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Public and Reproducible

**Shipped:** 2026-11-13
**Phases:** 4 | **Plans:** 47 | **Sessions:** not tracked

### What Was Built
- A public repository behind fail-closed identity, leak and attribution hooks, a full-history gitleaks scan with 15 accepted fingerprints, and a recorded pre-flip inventory (Phase 1).
- A standard-library Python 3.9 harness: `checkpoint-v1` stub, exclusive run roots, filename-safe snapshots, run-time deny-list sanitizer, fail-closed leak gate, allowlist self-test, two paid spikes that pinned Claude Code 2.1.310 and claude-sonnet-5-5 (Phase 2).
- Row 1 end to end through the real `claude -p`, filed as sanitized mechanical evidence, with mechanical write-boundary and git-read-only nets (Phase 3).
- A spec-driven engine for all 21 matrix entries, paid waves A to D, the row 7 triple with its review tables, a clean-clone bootstrap, and the Codex-reviewed baseline `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5` (Phase 4).

### What Worked
- Zero-token first: every row ran green against a scripted `claude` before any money was spent, so paid runs were attribution runs, not debugging runs. All six paid plans filed every chain on the first attempt.
- Measured cost drove the budgets: one row at 0.2723 USD projected Phase 4 at about 11 USD; the actual total was 11.74 USD.
- Facts-only evidence with a reviewer verdict line kept the harness out of the judging seat; Codex reviews stayed meaningful.
- Review passes after each phase (five in Phase 3) found real gaps that became gap-closure plans with tests instead of silent fixes.

### What Was Inefficient
- Paid plans needed the main conversation to run them: executors refused relayed go words, so each paid wave cost an extra dispatch before the orchestrator ran the command itself.
- Verification reports of Phases 1 to 3 went stale when Phase 4 touched shared harness files; they had to be regenerated at milestone close.
- The Claude Code auto-updater pruned the pinned build between waves; the clean-clone run lost a day to the reinstall and the Keychain login question (HOME plus USER).
- Phase 3 took twelve plans for one row because the write-escape rule grew through six gap-closure rounds; the rule's scope could have been decided up front.

### Patterns Established
- Paid runs happen only on bokiko's own go word in the conversation, run by the orchestrator after a green zero-token gate and a clean tree.
- Evidence folders are frozen when filed; later knowledge is added as new parts or a single verdict line, never by editing.
- Every committed file passes the sanitizer and the leak gate; planning text uses repo-relative paths and the name bokiko only.
- Security audits (`/gsd-secure-phase`) run per phase and close with a SECURITY.md; accepted risks carry an AR id and a follow-up in STATE.md.

### Key Lessons
1. Pin the test build by reinstall, not by assumption: an auto-updater can remove it between waves.
2. Verify provenance from the tools at hand (the Herdr pane for the Codex review) instead of asking the owner to report back.
3. A conservative classifier over command text needs a mechanical backstop (snapshot diff plus realpath boundary); neither alone would have been accepted.
4. Re-verify earlier phases before a milestone close whenever later phases touched their covered files; a stale report is not a failed one, but it blocks a verified closeout.

### Cost Observations
- Model mix: orchestration in the main conversation; every subagent (executors, verifiers, reviewers, auditors) on Sonnet; token shares not measured.
- Sessions: not tracked.
- Notable: paid Claude Code spend for the whole milestone was 12.27 USD (spikes 0.26, row 1 0.27, Phase 4 11.74) against caps that summed to far more; per-row cost 0.17 to 0.48 USD.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | not tracked | 4 | GSD adopted for an already-accepted skill; zero-token gates before every paid run |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 2,405 zero-token tests | not measured | standard-library Python only; no new dependency |

### Top Lessons (Verified Across Milestones)

1. One milestone so far; lessons above await a second milestone for cross-validation.
