# Conflict on section "Goal & current state"
ledger: <run>/ckpt/ledgers/CONTINUITY_CLAUDE-widget-export.md
your base hash: 4385dd704b2ad305753247adff64d51017b0a3d9c07d2aa74f6421823989c3a4
current hash: bb3bb61d21ecf60b6bc556a22095e29d71319ffc2627152d36bef281e041820c

## Yours (not applied)
widget-export in <run>/project: export widgets. Step 1 (columns id, name) done. Step 2 done: CSV exporter in widget_export.py (untested by instruction, uncommitted); plan step 2 checkbox marked [x]. Step 3 (empty-input test) not started. Pending format change (2026-11-11): JSON becomes the default export, CSV only on explicit request; JSON-default implementation not yet written. Branch main, HEAD eb56094803f8b28a4a232eec4018bed55e9f5242.

- Concurrent fact 1 (second writer, 2026-10-20): CI runner for this project was renamed to ci-02; nothing else changed.

## Current (kept)
widget-export in <run>/project: export widgets to CSV. Step 1 (columns id, name) done; exporter not written.

- Concurrent fact 1 (second writer, 2026-10-20): CI runner for this project was renamed to ci-02; nothing else changed.

- Concurrent fact 2 (second writer, 2026-10-20): the staging database moved to db-stg-03; nothing else changed.
