# CONTINUITY — widget-export

<!-- CHECKPOINT:BEGIN updated: 2026-11-07T09:33:52.505Z by: 3df858d6 -->
## Goal & current state
widget-export in <run>/project: export widgets to CSV. Step 1 (columns id, name) done; exporter not written.

- Concurrent fact 1 (second writer, 2026-10-20): CI runner for this project was renamed to ci-02; nothing else changed.

- Concurrent fact 2 (second writer, 2026-10-20): the staging database moved to db-stg-03; nothing else changed.

## Decisions (with reasons)
CSV first, JSON deferred: the downstream consumer only reads CSV.

## Blockers & open questions
None.

## Authorization boundaries
Edit files inside <run>/project only. No tests, no commits, no pushes until the user says so.
Detail: thoughts/plans/2026-10-15-widget-export.md

## Evidence & key paths
Plan: thoughts/plans/2026-10-15-widget-export.md. Branch main.

## Next action
Write the CSV exporter (plan step 2).
<!-- CHECKPOINT:END -->

## History
