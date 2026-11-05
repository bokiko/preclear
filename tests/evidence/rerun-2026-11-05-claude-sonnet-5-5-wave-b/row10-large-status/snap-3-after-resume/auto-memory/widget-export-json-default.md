---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: c0c41f70-a354-47e5-9121-50a72f7df366
  modified: 2026-11-05T06:30:06.089Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested.

**Why:** the downstream owner confirmed (2026-11-05) the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**How to apply:** new export work defaults to JSON; keep CSV as an opt-in path. The existing CSV exporter (widget_export.py) predates this and is not yet changed.
