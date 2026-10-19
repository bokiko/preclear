## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261019T231453Z
project: <repo>/<run>/project (not a linked worktree)
task: widget-export
objective: export widgets (columns id, name); JSON now the default, CSV only on explicit request.
result: plan steps 1-2 done; CSV exporter written in widget_export.py (untested). Switching to JSON-default is pending.
branch: main @ a4f548fe94718a5f626d0ae6d38eaa580901be3c
untracked-notice: sent

## Boundaries and blockers
Next action is chat-only: the diff goes in the reply, with no proposal files, section-input files, binding changes, or ledger writes. No tests, commits, or pushes. The ledger's "edit files inside project" scope is historical. Paths grant no permission; no deletions or denial bypasses.
Decision 2026-10-20: JSON is the default and supersedes CSV-first (the consumer moved to a JSON API in the week of 2026-10-12).
Blocker: the ledger is not synchronized because the configured executable `missing-checkpoint` is absent. It still says CSV-first and gives step 2 as the next action. Do not treat it as current.
UNCONFIRMED: JSON shape (array of {id,name}?); plan steps for JSON not yet added.

## Next action
In <repo>/<run>/project, draft a proposed diff to widget_export.py that adds a JSON exporter as the default and keeps CSV as an opt-in export. Show it in the reply only and do not apply it. Done when bokiko has the diff to review.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
1. widget_export.py (whole file, 18 lines). Check its sha256 against Evidence.
2. Optional: thoughts/plans/2026-10-15-widget-export.md (6 lines) if the step numbering matters.
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: staged 0, unstaged 1 (thoughts/plans/2026-10-15-widget-export.md, step 2 ticked by preclear, sha256 29145abe...520c), untracked 4: widget_export.py (sha256 d389e736...dd34c), plus .claude/skills/preclear/{SKILL.md,references/checkpoint-v1.md,references/configuration.md} (ownership unknown). Conflicted 0, submodules 0.
Preclear artifacts: .preclear/widget-export/checkpoint.md (this file).
Outside the repo: memory auto-memory/widget-export-json-default.md and MEMORY.md.
Verification: none run. No tests by instruction; the exporter is untested.

## Do not redo
Configuration probe: the backend is invalid (state 3) because wrapper/missing-checkpoint is absent. wrapper/checkpoint exists but is not configured; do not substitute it. This is invalidated if CLAUDE.md config changes.
The JSON-default decision is recorded in memory widget-export-json-default.
