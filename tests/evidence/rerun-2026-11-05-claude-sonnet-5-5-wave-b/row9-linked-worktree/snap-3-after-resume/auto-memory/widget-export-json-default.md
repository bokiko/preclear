---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 0f773444-f253-44e9-a657-a3258c7dc681
  modified: 2026-11-05T06:28:41.302Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the user on 2026-11-05 from the downstream owner. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** future work on widget-export should default to JSON output and keep CSV as an opt-in path. The existing CSV exporter (src/widget_export.py) is kept, not removed. A JSON-default change is only proposed as a diff for user review until the user approves applying it.
