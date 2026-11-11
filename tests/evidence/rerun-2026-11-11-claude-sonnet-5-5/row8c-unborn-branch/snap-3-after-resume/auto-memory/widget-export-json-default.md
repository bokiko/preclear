---
name: widget-export-json-default
description: "widget-export default format is JSON, CSV only on explicit request; supersedes the 2026-10-15 CSV-first plan decision"
metadata:
  node_type: memory
  type: project
  originSessionId: 52fa3032-6149-423a-a0d5-7ff597f1d0bb
  modified: 2026-11-11T07:03:04.759Z
---

For widget-export, JSON is the default export format. CSV is supported only when explicitly requested. This supersedes the "CSV first, JSON deferred" decision of 2026-10-15 in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream owner confirmed (relayed by the user on 2026-11-11) that the consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** new export work targets JSON first and keeps CSV as an opt-in path. Treat the plan's Decision line as stale. The CSV exporter in `src/widget-export.js` (plan step 2) is already written and is kept as the explicit-request path.
