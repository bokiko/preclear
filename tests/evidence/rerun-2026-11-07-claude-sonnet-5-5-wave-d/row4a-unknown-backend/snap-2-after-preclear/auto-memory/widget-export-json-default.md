---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the earlier CSV-first ledger decision
metadata:
  node_type: memory
  type: project
  originSessionId: 007781ca-62c8-4df3-884c-209f72d5d28b
  modified: 2026-11-07T09:38:24.797Z
---

For widget-export, JSON is the default export format; CSV is supported only on explicit request. The downstream owner confirmed this, and the consumer moved to a JSON API in the week of 2026-10-12. This supersedes the "CSV first, JSON deferred" decision in the continuity ledger and applies to future sessions.

**Why:** the downstream consumer no longer reads CSV.
**How to apply:** when planning or drafting widget-export work, default to JSON and keep the existing CSV exporter (`widget_export.py`) as the explicit-request path.
