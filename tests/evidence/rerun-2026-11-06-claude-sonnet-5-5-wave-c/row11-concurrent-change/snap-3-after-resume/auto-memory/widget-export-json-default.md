---
name: widget-export-json-default
description: widget-export format decision — JSON is the default export; CSV only on explicit request (supersedes 2026-10-15 CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: 129ee91b-9b97-48ff-aeb6-ae27c7668378
  modified: 2026-11-06T23:19:00.588Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. The downstream owner confirmed this on 2026-11-07, and the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer no longer reads CSV, so a CSV-default exporter would not serve it.

**How to apply:** in future sessions, treat JSON as the default when designing or changing the exporter, and keep CSV behind an explicit request. The CSV exporter (`widget_export.py`, plan step 2) already exists, so the pending work is a JSON-default change, which the user wants drafted as a diff for review before anything is applied.
