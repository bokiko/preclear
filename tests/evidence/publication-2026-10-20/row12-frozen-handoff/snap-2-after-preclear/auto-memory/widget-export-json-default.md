---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 6761c8af-f4d7-4a6d-a349-0fde5ff616b7
  modified: 2026-10-19T23:35:39.421Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner, recorded 2026-10-20. Supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV only.

**How to apply:** new or changed export code should produce JSON by default and keep CSV as an opt-in path. Don't treat the plan's CSV-first line as current.
