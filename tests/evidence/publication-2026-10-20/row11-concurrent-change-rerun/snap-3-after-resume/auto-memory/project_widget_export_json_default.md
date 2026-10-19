---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: 49eb3854-a270-441d-bdca-e5e67efc2e84
  modified: 2026-10-19T23:40:42.519Z
---

widget-export exports JSON by default; CSV is supported only when explicitly requested. This replaces the 2026-10-15 "CSV first, JSON deferred" decision.

**Why:** the downstream owner confirmed (reported by bokiko 2026-10-20) that the consumer moved to a JSON API in the week of 2026-10-12.

**How to apply:** new export work defaults to JSON. Keep CSV only as an opt-in path. Decision is also recorded in thoughts/plans/2026-10-15-widget-export.md.
