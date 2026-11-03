---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: 9d92912e-73f9-45e5-913b-471de4dd6983
  modified: 2026-11-03T06:05:03.170Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the user on 2026-11-03 from the downstream owner; this supersedes the "CSV first, JSON deferred" decision of 2026-10-15 in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV.

**How to apply:** in future sessions treat JSON as the default and keep the CSV exporter (`src/widget-export.js`, written 2026-11-03 under the old decision) as the explicit-request path. Do not make CSV the default again. A JSON-default change is only a proposed diff for user review until the user approves applying it.
