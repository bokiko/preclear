---
name: project-widget-export-json-default
description: widget-export default format is JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 0d70631a-cda9-4357-a00f-ec27bcb82847
  modified: 2026-10-19T23:35:57.299Z
---

Decision 2026-10-20 (bokiko, confirmed by the downstream owner): JSON is the default export format for widget-export. CSV is supported only when explicitly requested. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream consumer moved to a JSON API in the week of 2026-10-12, so it no longer reads only CSV.

**How to apply:** new export work makes JSON the default output and keeps CSV behind an explicit opt-in. Do not treat the plan's 2026-10-15 decision line as current.
