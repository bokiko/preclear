---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first plan decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 81023b26-ffc3-4062-bcf6-c3e2cb6bfe90
  modified: 2026-11-09T21:55:00.245Z
---

For widget-export, JSON is the default export format; CSV is supported only when explicitly requested. Confirmed by the user on 2026-11-10 from the downstream owner. This supersedes the "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** in future sessions, design and implement exports as JSON-first and keep the existing CSV exporter (`src/widget_export.py`) as the explicit-request path. Do not treat the plan's CSV-first line as current.
