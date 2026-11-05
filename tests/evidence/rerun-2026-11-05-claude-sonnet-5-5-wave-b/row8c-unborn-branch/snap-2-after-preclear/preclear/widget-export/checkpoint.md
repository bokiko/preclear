## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261105T062726Z
project: <run>/project (not a linked worktree)
task: widget-export
objective: export widgets (id, name); JSON now the default format, CSV on explicit request
result: step 2 CSV exporter done (widget_export.py); JSON-default change pending, not started
branch: unborn (main, no commits); HEAD: n/a
untracked-notice: sent (.preclear/ is untracked)

## Boundaries and blockers
Authorized: draft a proposed JSON-default diff for user review only. Do not apply it, edit widget_export.py, run tests, commit, or start plan step 3. No deletion or denial bypass; paths grant no permission.
Pending: user approval of the draft before any implementation.
UNCONFIRMED: JSON shape (top-level array vs object, key names).
Detail: plan decision 2026-11-05; memory widget-export-json-default.

## Next action
In the project directory, write a proposed unified diff (JSON default, CSV kept for explicit request) against widget_export.py as reply text or a scratch file under .preclear/widget-export/. Done when the user has it for review; do not apply it.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
1. thoughts/plans/2026-10-15-widget-export.md (whole)
2. widget_export.py (whole)
3. Memory widget-export-json-default.md, only if the reason is needed.
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: staged 0, unstaged 0, untracked 7, conflicted 0, submodules 0. Untracked: CLAUDE.md, thoughts/plans/2026-10-15-widget-export.md, widget_export.py, .claude/skills/preclear/{SKILL.md,references/{checkpoint-v1,configuration,status-sidecar}.md}; ownership unknown except the plan and widget_export.py (this task).
Preclear artifacts: .preclear/widget-export/checkpoint.md.
Digests (sha256 prefix): widget_export.py a365afc2dc97; plan edbafe72753e (step 2 ticked, 2026-11-05 decision added).
Verification: no tests run (user instruction); binding UNCONFIRMED.

## Do not redo
Plan and memory already updated for the JSON decision (verified: plan digest above; memory file exists). Redo only if the plan digest differs.
CSV exporter written and reread; not tested. Invalidated if widget_export.py digest changes.
