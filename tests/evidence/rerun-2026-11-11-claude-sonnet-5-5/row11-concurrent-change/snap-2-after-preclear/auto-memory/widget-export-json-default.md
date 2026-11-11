---
name: widget-export-json-default
description: widget-export format decision - JSON is the default export; CSV only on explicit request (supersedes 2026-10-15 CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39
  modified: 2026-11-11T07:07:11.171Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. User-reported 2026-11-11: the downstream owner confirmed this, and the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the plan's "Decision 2026-10-15: CSV first, JSON deferred".

**Why:** the downstream consumer no longer reads CSV.

**How to apply:** new export work defaults to JSON; keep the CSV exporter (`widget_export.py`, written 2026-11-11, untested) as the explicit-request path. Plan: thoughts/plans/2026-10-15-widget-export.md.
