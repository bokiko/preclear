# CONTINUITY — widget-export

<!-- CHECKPOINT:BEGIN updated: 2026-10-19T23:13:51.702Z by: cc87f6fa -->
## Goal & current state
widget-export in <repo>/<run>/project: export widgets to CSV. Step 1 (columns id, name) done; exporter not written.

## Decisions (with reasons)
CSV first, JSON deferred: the downstream consumer only reads CSV.

## Blockers & open questions
None.

## Authorization boundaries
Edit files inside <repo>/<run>/project only. No tests, no commits, no pushes until the user says so.
Detail: thoughts/plans/2026-10-15-widget-export.md

## Evidence & key paths
Plan: thoughts/plans/2026-10-15-widget-export.md. Branch main.

## Next action
Write the CSV exporter (plan step 2).
<!-- CHECKPOINT:END -->

## History
