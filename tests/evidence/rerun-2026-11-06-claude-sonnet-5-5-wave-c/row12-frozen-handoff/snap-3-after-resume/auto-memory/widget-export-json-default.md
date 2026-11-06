---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 97409728-53cc-41b5-a034-1a474f27d749
  modified: 2026-11-06T23:20:33.249Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner on 2026-11-07. This supersedes the "CSV first, JSON deferred" decision dated 2026-10-15 in thoughts/plans/2026-10-15-widget-export.md, which is now stale.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** new export work targets JSON by default; keep the existing CSV exporter (src/widget_export.py) available as the explicit-request path. Do not treat the plan's CSV-first line as current.
