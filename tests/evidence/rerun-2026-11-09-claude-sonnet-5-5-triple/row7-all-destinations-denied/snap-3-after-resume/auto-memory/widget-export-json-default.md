---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 5e6c0f17-2bf4-423c-a2d7-a87c516fa8b4
  modified: 2026-11-09T21:52:36.123Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Downstream owner confirmed 2026-11-10 (user relayed).

**Why:** The downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV. This supersedes "Decision 2026-10-15: CSV first, JSON deferred" in thoughts/plans/2026-10-15-widget-export.md.

**How to apply:** Any widget-export work defaults to JSON output; keep the existing CSV exporter (src/widget-export.js) as the opt-in path. Do not treat the plan's CSV-first line as current.
