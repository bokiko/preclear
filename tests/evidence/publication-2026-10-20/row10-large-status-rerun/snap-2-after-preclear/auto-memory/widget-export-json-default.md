---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 4df7d287-0216-46a6-b950-f7e298084213
  modified: 2026-10-19T23:40:45.395Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested. Supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream owner confirmed (reported by bokiko 2026-10-20) that the consumer migrated to a JSON API in the week of 2026-10-12, so the CSV-only premise no longer holds.

**How to apply:** new export work defaults to JSON; keep the CSV path as an opt-in, not the default. Don't treat the plan's old CSV-first line as current.
