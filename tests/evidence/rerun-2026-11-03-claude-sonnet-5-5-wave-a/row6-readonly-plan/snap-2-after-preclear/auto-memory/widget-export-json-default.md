---
name: widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: e711c17d-7192-49f1-8ad9-e693612fe5ba
  modified: 2026-11-03T06:04:01.736Z
---

For widget-export, JSON is the default export format; CSV is supported only on explicit request. The downstream owner confirmed this on 2026-11-03 (user-reported). This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** new export work targets JSON by default; keep the existing CSV exporter (src/widget_export.py) as the explicit-request path. Don't build CSV-only features.
