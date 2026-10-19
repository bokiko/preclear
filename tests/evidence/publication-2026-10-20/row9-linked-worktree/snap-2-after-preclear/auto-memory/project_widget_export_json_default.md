---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes the 2026-10-15 CSV-first plan decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 85b3098a-6509-429c-a1d8-08b38d2a56e2
  modified: 2026-10-19T23:35:39.633Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Recorded 2026-10-20; supersedes the "CSV first, JSON deferred" decision dated 2026-10-15 in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream owner confirmed the consumer moved to a JSON API during the week of 2026-10-12, so the old reason (the consumer only reads CSV) no longer holds.

**How to apply:** new export work makes JSON the default path and keeps CSV behind an explicit option. Don't follow the plan's CSV-first line.
