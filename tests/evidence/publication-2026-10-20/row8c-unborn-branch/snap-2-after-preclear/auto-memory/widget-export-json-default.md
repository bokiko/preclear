---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: c07ad3f7-4691-4e0e-97fe-1c4dd05f6e00
  modified: 2026-10-19T23:35:39.227Z
---

JSON is the default export format for widget-export. CSV is supported only when explicitly requested. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream owner confirmed (reported by bokiko 2026-10-20) that the consumer migrated to a JSON API in the week of 2026-10-12.

**How to apply:** new export work defaults to JSON; keep the CSV path as opt-in only. Don't treat the plan's CSV-first line as current.
