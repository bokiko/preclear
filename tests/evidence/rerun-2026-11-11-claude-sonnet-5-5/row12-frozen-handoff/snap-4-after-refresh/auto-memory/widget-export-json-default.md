---
name: widget-export-json-default
description: "widget-export format decision — JSON is the default export, CSV only on explicit request (supersedes 2026-10-15 CSV-first)"
metadata:
  node_type: memory
  type: project
  originSessionId: 36ffc8c3-bb43-4a3f-87ca-00de30e41ca9
  modified: 2026-11-11T07:08:36.134Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner on 2026-11-11; the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer no longer reads CSV, so a CSV-default exporter would not serve it.

**How to apply:** in future sessions, treat JSON as the default for any export work and add CSV only behind an explicit request option. The existing CSV exporter (`src/widget-export.js`) predates this decision and still needs a JSON-default rework, which is awaiting user review of a proposed diff.
