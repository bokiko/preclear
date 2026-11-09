---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: d97173e1-76a7-4a9e-820b-e77304e87a26
  modified: 2026-11-09T21:53:51.496Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. The downstream owner confirmed this to the user on 2026-11-10, and the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the "CSV first, JSON deferred" decision of 2026-10-15 in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer no longer reads CSV by default, so a CSV-first exporter no longer serves it.

**How to apply:** in future sessions, treat JSON as the default and keep CSV as an opt-in path. Step 2 (CSV exporter, `src/widget-export.js`) is already written and stays as the explicit-request path. A proposed JSON-default diff is to be drafted for user review, not applied, until the user approves it.
