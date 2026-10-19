---
name: project-widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes CSV-first ledger decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 8a89dcec-3653-4550-8f97-96596879c3b3
  modified: 2026-10-19T23:14:45.339Z
---

widget-export (preclear/<run>/project): JSON is the default export format; CSV is supported only on explicit request. Confirmed by the downstream owner, recorded 2026-10-20. Supersedes the ledger's "CSV first, JSON deferred" decision.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12.

**How to apply:** treat the ledger's CSV-first decision as stale; new exporter work defaults to JSON and keeps CSV as an opt-in path.
