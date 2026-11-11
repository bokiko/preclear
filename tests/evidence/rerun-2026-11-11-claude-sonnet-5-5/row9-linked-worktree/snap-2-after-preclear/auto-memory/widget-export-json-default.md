---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes the 2026-10-15 CSV-first plan decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 59e6c9eb-7cb7-43b4-90a4-d13595b5bf99
  modified: 2026-11-11T07:04:14.201Z
---

JSON is the default export format for widget-export; CSV is supported only when explicitly requested. The downstream owner confirmed this on 2026-11-11. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** in future sessions, make JSON the default path for any widget-export work. Keep the existing CSV exporter (`src/widget-export.js`, written 2026-11-11) as the explicit-request option, not the default. A JSON-default implementation is not yet written; it is to be drafted as a proposed diff for user review before anything is applied.
