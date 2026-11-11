---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first plan decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 360ff92c-5213-4b02-bea0-88537c3ea862
  modified: 2026-11-11T07:05:29.264Z
---

widget-export: JSON is the default export format; CSV is supported only on explicit request. Confirmed by the downstream owner (user report, 2026-11-11). Supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** new or changed export code should default to JSON and keep CSV behind an explicit request. The existing CSV exporter (src/widget-export.js) predates this change and still needs rework; do not treat the plan's CSV-first line as current.
