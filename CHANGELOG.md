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
  frozen handoff) has run: all twelve rows reviewed, with rows 3a, 3b, 10 and 11 rerun after
  fixes (see `tests/evidence/publication-2026-10-20/`). Known open content defect: row 7's
  printed checkpoint carries an unsupported Do-not-redo entry. The repository stays private
  until the public-content and history audit is accepted and publication is explicitly approved.
- Harness rules in `tests/acceptance.md`: isolation preflight, per-stage snapshots,
  original-file measurements, memory-root pinning, correction-in-the-`/preclear`-turn.
- Fixtures keep memory inside the project and ship a `runtime-settings.example.json`.
- Bound-ledger acceptance evidence (2026-10-19): backend path, BLOCKED policy, read-only
  resume, writable unbound fallback and real conflict recovery, run in isolation with the
  helper's `CKPT_HOME` override and a test-only wrapper for the conflict case.
- `references/checkpoint-v1.md`: resume is read-only for continuity state (never bind outside
  setup), backend inputs live in `backend-inputs/`, read-only bootstrap note recommended
  beside the configuration block.
- Publication matrix evidence (2026-10-20), rows 5–12: no or disabled memory, read-only plan,
  all destinations denied, non-git, detached HEAD, unborn branch, linked worktree, large status
  with hostile filenames, concurrent change during capture, frozen handoff with external edit,
  resume and refresh. Every fresh resume made zero writes.
- Publication matrix evidence (2026-10-20), rows 1–4: wrong active binding, two same-section
  conflicts, missing executable, denied helper write, unbound with `fallback_directory: none`,
  unknown backend, conflicting configuration blocks. Backend isolation and fallback policy held
  in every row. Two defects led to the changes below and to targeted reruns of rows 3a and 3b.

### Changed

- `SKILL.md` Step 4 after publication rows 1–4: artifacts are measured by command, UTF-8 bytes
  of the final file and of each section including its heading line, printed as actual/cap; an
  overrun is a measured exception, never a passed check; plain checkpoints start at the first
  heading. The installed-tokenizer preference was dropped to stay within the size ceiling.
- `references/checkpoint-v1.md`: after the first denied helper mutation no further mutation is
  attempted in the run (fallback with "helper write denied"); backend failure changes
  persistence, not ownership (memory holds a pointer, not a parallel rationale, when the ledger
  owns a decision).

- `SKILL.md` after the first acceptance run: next action must be presently authorized
  and never a conditional workflow; the fresh session leaves the checkpoint unchanged
  until the next `/preclear`; evidence counts exclude preclear's own artifacts; digests
  are rechecked even when status is unchanged; a denied measurement is `UNCONFIRMED`.
- README: install note about a personal skill of the same name shadowing a project one,
  the after-resume lifecycle, and the measurement caveat.
