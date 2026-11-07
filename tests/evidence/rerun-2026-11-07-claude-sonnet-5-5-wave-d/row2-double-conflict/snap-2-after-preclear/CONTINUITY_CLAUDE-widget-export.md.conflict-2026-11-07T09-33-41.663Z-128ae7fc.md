# Conflict on section "Goal & current state"
ledger: <run>/ckpt/ledgers/CONTINUITY_CLAUDE-widget-export.md
your base hash: 0c381d360ac6594e7013982f3d25cbf893fad9b8f7f88c917d79da412e76d69f
current hash: 40c9fa3cbc78e8a150b0429e18eaf06a178419d93acc1340fa2279f662522a77

## Yours (not applied)
widget-export in <run>/project: export widgets. Step 1 (columns id, name) done. Step 2 CSV exporter written in widget_export.py (escape_field, widget_to_row, widgets_to_csv); untested. Pending: export default changed to JSON (CSV on explicit request only); not implemented. Branch main.

## Current (kept)
widget-export in <run>/project: export widgets to CSV. Step 1 (columns id, name) done; exporter not written.

- Concurrent fact 1 (second writer, 2026-10-20): CI runner for this project was renamed to ci-02; nothing else changed.
