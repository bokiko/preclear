## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261111T071009Z
project: <run>/project (not a linked worktree)
task: widget-export
objective: export widgets (id, name); JSON is the default format, CSV only on explicit request.
result: plan steps 1-2 done (CSV exporter written, untested). JSON-default diff was shown in reply and awaits user review; not applied. Step 3 not started.
branch: main
HEAD: 2e44702137af1166e157bc1162076b95c188d11d
untracked-notice: sent (.preclear/ is untracked)

## Boundaries and blockers
Authorized: show a proposed JSON-default diff for review, in the reply only. Not authorized: applying it, editing src/, running tests, commits, step 3, deleting files. Paths grant no permission.
Decision 2026-11-11 (plan, memory widget-export-json-default): JSON default, CSV explicit-only; supersedes CSV-first.
Pending: user review/approval of the diff.
UNCONFIRMED: how work reaches the colleague's machine (uncommitted, untracked; absolute paths are machine-specific).
Detail: thoughts/plans/2026-10-15-widget-export.md

## Next action
In the project directory, reprint (reply only; the earlier reply is lost on /clear) the proposed diff to src/widget-export.js: keep CSV functions; add pure toRecord, exportWidgetsJson, and exportWidgets(widgets, {format = "json"}) using a FORMATS map checked with Object.hasOwn, throwing on unknown formats. Ask the user to approve. Done when shown.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
Read: plan Decision/Note lines (project-relative); src/widget-export.js (whole, 12 lines).
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: staged 0; unstaged 1 (M thoughts/plans/2026-10-15-widget-export.md: step 2 checked, 2026-11-11 decision, 2026-10-21 note); untracked 1 (src/widget-export.js); conflicted 0; submodules 0.
Ownership unknown: untracked .claude/skills/preclear/ (4 files).
Preclear artifacts: .preclear/widget-export/checkpoint.md; frozen copy checkpoint-20261111T070840Z-k7q3.md (unchanged, sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3). No sidecar.
Verification: none run (tests not authorized); binding UNCONFIRMED.
sha256 src/widget-export.js 4c231fad03d9d5ab0b2182027e6eb226c2f72a24f9049f92620933882b46db65
sha256 plan 304a5a8724f7ad1efddc4f53ac99bc07b26a97ccf5fa66fcd614a8151fec9e9a (frozen copy lists 38bd6354...; cause of change UNCONFIRMED)
Memory (outside project): widget-export-json-default.md plus MEMORY.md index.

## Do not redo
No Preclear configuration block in project CLAUDE.md (read 2026-11-11, CLAUDE.md sha256 ed03447e...; invalid if it changes), so the plain-file backend applies.
Memory root had only the preclear-created index and topic file (read 2026-11-11; invalid if other files appear).
