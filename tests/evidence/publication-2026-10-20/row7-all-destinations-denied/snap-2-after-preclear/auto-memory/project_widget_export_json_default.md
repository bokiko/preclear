---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: edbfff4f-455a-4b39-860b-9470b4c5939e
  modified: 2026-10-19T23:33:21.968Z
---

Decision 2026-10-20 for widget-export: JSON is the default export format; CSV is supported only on explicit request. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream owner confirmed the consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** new export work defaults to JSON; keep CSV behind an explicit opt-in. Do not treat the CSV-first line in the plan as current.
