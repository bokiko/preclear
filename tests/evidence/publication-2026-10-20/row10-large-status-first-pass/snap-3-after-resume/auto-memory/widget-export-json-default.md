---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 561214dd-31d7-44e1-9c8d-7b6426d71381
  modified: 2026-10-19T23:36:08.465Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested. Confirmed by the downstream owner, recorded 2026-10-20. Supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so the CSV-only premise no longer holds.

**How to apply:** new export work defaults to JSON; keep CSV as an opt-in path, never the default. Applies to future sessions.
