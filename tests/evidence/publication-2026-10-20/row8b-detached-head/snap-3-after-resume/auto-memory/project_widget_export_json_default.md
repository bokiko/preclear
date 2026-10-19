---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes CSV-first decision of 2026-10-15)
metadata:
  node_type: memory
  type: project
  originSessionId: bbbf30c2-8aea-4b02-a359-353ba0925431
  modified: 2026-10-19T23:35:42.321Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested. Confirmed by the downstream owner (relayed by bokiko 2026-10-20).

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the plan's "Decision 2026-10-15: CSV first, JSON deferred".

**How to apply:** new export work defaults to JSON; keep CSV as an opt-in path, not the default. Don't re-derive the format from the old plan decision.
