---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 1ea9ce21-32b3-4b17-9281-74c935e29558
  modified: 2026-11-05T06:11:24.328Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request.

**Why:** the downstream owner confirmed (user-relayed, 2026-11-05) that the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**How to apply:** new export work defaults to JSON; keep the existing CSV exporter (widget_export.py) as the explicit-request path. Do not assume the plan's older CSV-first line is current.
