---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 8ac348b9-b892-490c-93ef-d82272b34135
  modified: 2026-11-05T06:27:20.654Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner on 2026-11-05 and supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** new export work defaults to JSON; keep the existing CSV exporter (widget_export.py) available for explicit CSV requests. Do not treat the older CSV-first plan line as current.
