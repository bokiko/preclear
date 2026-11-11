---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: bf313c82-a6c4-43de-9326-3c7f2c47f7a3
  modified: 2026-11-11T06:59:29.653Z
---

For widget-export, JSON is the default export format. CSV is supported only when explicitly requested. Confirmed by the downstream owner on 2026-11-11; this supersedes the 2026-10-15 "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** treat JSON as the default in any new export work. Keep the existing CSV exporter (`src/widget-export.js`, written 2026-11-11 under the old decision) as the explicit-request path. Do not drop it.
