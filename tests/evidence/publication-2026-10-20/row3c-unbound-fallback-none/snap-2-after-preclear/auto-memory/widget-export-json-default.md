---
name: widget-export-json-default
description: widget-export project defaults to JSON export; CSV only on explicit request (supersedes CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: e7ac129d-a743-46ca-9478-85a8f57ee541
  modified: 2026-10-19T23:19:10.206Z
---

For the widget-export project (<repo>/<run>/project), JSON is the default export format. CSV is supported only when explicitly requested. This replaces the earlier "CSV first, JSON deferred" decision in the continuity ledger.

**Why:** the downstream owner confirmed that the consumer moved to a JSON API in the week of 2026-10-12. Confirmed by bokiko on 2026-10-20.

**How to apply:** build new export work JSON-first and keep the CSV exporter (`widget_export.py`) as the opt-in path. If the ledger still says CSV-first, this note is newer, so trust it until the ledger is reconciled.
