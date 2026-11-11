---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: f43fe444-2783-4b09-9774-bbda070d6560
  modified: 2026-11-11T06:58:34.153Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner, 2026-11-11. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** new or changed export code should default to JSON and keep CSV as an opt-in path (the CSV exporter in src/widget-export.js stays). Do not follow the plan's older CSV-first decision line.
