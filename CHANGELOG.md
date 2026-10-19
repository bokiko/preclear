# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Generic `SKILL.md`.
- `references/configuration.md`.
- `references/checkpoint-v1.md`.
- Acceptance tests and fixtures.
- Plain-memory acceptance evidence (2026-10-19): three runs, accepted after review.
- Hub-memory acceptance evidence (2026-10-19): first run passed routing and failed
  fresh-session continuation; rerun accepted with one documented cap-reporting defect.
- Checkpoint Boundaries now persist user-authorized scope, scratch and draft limits, and
  the no-deletion rule; Resume reading ends with "no file output, binding, or backend write
  without authorization", so a fresh session that never loads the skill still inherits the
  limits.
- Status: the three layouts (plain-memory, hub-memory, bound-ledger) are accepted after
  review. The expanded publication matrix (wrong binding, double conflict, missing or denied
  helper, malformed configuration, no or disabled memory, read-only plan, all destinations
  denied, non-git, detached, unborn, linked worktree, hostile filenames, concurrent change,
  frozen handoff) has not run. The repository stays private until it does.
- Harness rules in `tests/acceptance.md`: isolation preflight, per-stage snapshots,
  original-file measurements, memory-root pinning, correction-in-the-`/preclear`-turn.
- Fixtures keep memory inside the project and ship a `runtime-settings.example.json`.
- Bound-ledger acceptance evidence (2026-10-19): backend path, BLOCKED policy, read-only
  resume, writable unbound fallback and real conflict recovery, run in isolation with the
  helper's `CKPT_HOME` override and a test-only wrapper for the conflict case.
- `references/checkpoint-v1.md`: resume is read-only for continuity state (never bind outside
  setup), backend inputs live in `backend-inputs/`, read-only bootstrap note recommended
  beside the configuration block.

### Changed

- `SKILL.md` after the first acceptance run: next action must be presently authorized
  and never a conditional workflow; the fresh session leaves the checkpoint unchanged
  until the next `/preclear`; evidence counts exclude preclear's own artifacts; digests
  are rechecked even when status is unchanged; a denied measurement is `UNCONFIRMED`.
- README: install note about a personal skill of the same name shadowing a project one,
  the after-resume lifecycle, and the measurement caveat.
