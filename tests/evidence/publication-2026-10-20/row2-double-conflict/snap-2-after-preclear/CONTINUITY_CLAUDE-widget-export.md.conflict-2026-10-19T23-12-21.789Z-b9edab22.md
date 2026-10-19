# Conflict on section "Goal & current state"
ledger: <repo>/<run>/ledgers/CONTINUITY_CLAUDE-widget-export.md
your base hash: 50956c029e720f52bd0e21f27b34415668f294f539feb9e2da986d4e2f68a580
current hash: 77df246feea4658469b18544021452fe0c2d961ace1d7dd4b47b39584b566465

## Yours (not applied)
widget-export in <repo>/<run>/project (git main @ 0cc011a4284088307ec353fab1842c285a0330ff; not a linked worktree). Objective: export widgets (columns id, name). Plan steps 1-2 done: CSV exporter in widget_export.py (untested, uncommitted). Pending: make JSON the default format per D2, keeping CSV for explicit requests. Plan step 3 (empty-input test) not started. untracked-notice: sent (.preclear/).

## Current (kept)
widget-export in <repo>/<run>/project: export widgets to CSV. Step 1 (columns id, name) done; exporter not written.

- Concurrent fact 1 (second writer, 2026-10-20): CI runner for this project was renamed to ci-02; nothing else changed.
