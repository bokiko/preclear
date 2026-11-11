---
name: widget-export-json-default
description: "widget-export format decision — JSON is the default export, CSV only on explicit request (supersedes CSV-first)"
metadata:
  node_type: memory
  type: project
  originSessionId: 2b542a48-2e28-40e9-962d-4e7679c94bb7
  modified: 2026-11-11T07:01:47.293Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested. This supersedes the 2026-10-15 "CSV first" plan decision.

**Why:** the downstream owner confirmed (2026-11-11) that the consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** design and review exports JSON-first; keep the existing CSV exporter (`src/widget-export.js`) as the explicit-request path. Progress and the pending JSON implementation live in the plan `thoughts/plans/2026-10-15-widget-export.md`.
