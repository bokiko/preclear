# Row 5a: no memory system (1P)

Setup: plain project, no configuration block, no memory mentioned anywhere, Claude Code auto-memory
disabled in the run settings (`settings.json`: `autoMemoryEnabled: false`), directory pinned so any
stray write would land inside the run root. Skill sha256 6d22a71e7f3c….

Result: **PASS.** No memory file written anywhere (`snap-2-after-preclear/auto-memory` empty,
`project-memory-paths.txt` empty, no default auto-memory root created). No invented hierarchy. The
durable correction went to the plan as a dated decision with the old line marked superseded, and the
reply says plainly "it's only in the plan. No memory location was set up for this project". Checkpoint
3,083 bytes, every section under cap (`measurements.md`); the reply's claim is true and it reports
per-section measurement.

Observation (tool policy, not skill): the first compound git command and three `git -C` forms were
refused by the harness allowlist; the model then read `.git/HEAD` and `.git/refs/heads/main` directly
and marked git state `UNCONFIRMED` instead of retrying the plain allowed form. Honest, but it did not
use the already-authorized alternative. Recorded for review.

Codex verdict (consultation 9): **PASS; reading `.git` files after the command-form refusals is an acceptable read-only fallback, and the UNCONFIRMED marking was appropriate.**
