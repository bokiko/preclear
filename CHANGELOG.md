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
  the no-deletion rule; Resume reading ends with "no file output without authorization",
  so a fresh session that never loads the skill still inherits the limits.
- Harness rules in `tests/acceptance.md`: isolation preflight, per-stage snapshots,
  original-file measurements, memory-root pinning, correction-in-the-`/preclear`-turn.
- Fixtures keep memory inside the project and ship a `runtime-settings.example.json`.

### Changed

- `SKILL.md` after the first acceptance run: next action must be presently authorized
  and never a conditional workflow; the fresh session leaves the checkpoint unchanged
  until the next `/preclear`; evidence counts exclude preclear's own artifacts; digests
  are rechecked even when status is unchanged; a denied measurement is `UNCONFIRMED`.
- README: install note about a personal skill of the same name shadowing a project one,
  the after-resume lifecycle, and the measurement caveat.
