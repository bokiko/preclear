---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first plan decision)
metadata:
  node_type: memory
  type: project
  originSessionId: b4a45f8c-a4a1-46a1-93d2-41b7ede438c5
  modified: 2026-10-19T23:33:13.619Z
---

widget-export: JSON is the default export format; CSV is supported only on explicit request. Confirmed by the downstream owner (bokiko relayed it 2026-10-20).

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the "CSV first, JSON deferred" decision dated 2026-10-15 in `thoughts/plans/2026-10-15-widget-export.md` line 7. That plan file is read-only (mode r--r--r--), so its line is stale and was not edited.

**How to apply:** new export work defaults to JSON. Keep a CSV path only behind an explicit opt-in. Treat the plan's CSV-first line as superseded.
