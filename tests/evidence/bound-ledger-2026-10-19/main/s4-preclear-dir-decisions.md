2026-10-19, supersedes CSV-first: JSON is the default export format; CSV only on explicit request. Reason: the downstream owner confirmed the consumer migrated to a JSON API in the week of 2026-10-12. Applies to future sessions.
Superseded 2026-10-19: "CSV first, JSON deferred: the downstream consumer only reads CSV" (its basis is gone).
Do not redo: plan step 2 (CSV exporter) is written in widget_export.py, sha256 5aad43c3…4cc4b9; invalid if that file changes. Columns id,name fixed by plan step 1.
Do not redo: JSON-default diff drafted 2026-10-19 (.preclear/widget-export/json-default.diff sha256 00eb97e0…e647d; proposed file 63c487c9…a3e01a); invalid if widget_export.py changes or bokiko requests changes.
