# Plan: widget-export

1. [x] Define the export columns (id, name).
2. [ ] Write the CSV exporter.
3. [ ] Add a test for empty input.

Decision 2026-10-15: CSV first, JSON deferred; the downstream consumer only reads CSV.
