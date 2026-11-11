---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: fe615e8c-42e7-4326-9890-b2a64ef5d23d
  modified: 2026-11-11T07:00:39.961Z
---

JSON is the default export format for widget-export; CSV is supported only on explicit request. Confirmed by the downstream owner on 2026-11-11. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in `thoughts/plans/2026-10-15-widget-export.md`.

**Why:** the downstream consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** new export work, and plan step 3 (empty-input test), target the JSON default; keep the existing CSV exporter (`src/widget-export.js`, written 2026-11-11 under the old decision) as the explicit-request path. Any change to it needs the user's review of a proposed diff first.
