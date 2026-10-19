# Ledger: widget-export

Note: the hash lines are added by the helper and are omitted in this fixture.

## Goal & current state
Export widgets to CSV. Columns defined; exporter not yet written.

## Decisions (with reasons)
CSV first, JSON deferred. The downstream consumer only reads CSV.

## Blockers & open questions
None.

## Authorization boundaries
Edit files in sample-project only. No pushes, no installs.

## Evidence & key paths
Plan: thoughts/plans/ (placeholder). Columns spec: placeholder.

## Next action
Write the CSV exporter in src/export.py (placeholder path).
