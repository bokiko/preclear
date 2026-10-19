---
name: widget-export-json-default
description: widget-export project defaults to JSON export; CSV only on explicit request (supersedes CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: baf198cb-90b5-487c-8bc6-29a4d1b8efa7
  modified: 2026-10-19T23:14:46.080Z
---

For the widget-export project (<repo>/<run>/project), JSON is the default export format. CSV is supported only when someone explicitly asks for it. This replaces the earlier "CSV first, JSON deferred" decision that is still written in the continuity ledger.

**Why:** the downstream owner confirmed that the consumer moved to a JSON API in the week of 2026-10-12. bokiko passed this on during the 2026-10-20 session.

**How to apply:** if the ledger still says CSV-first, this note wins. Keep the existing CSV exporter (`widget_export.py`) as the explicit-request path, and make JSON the default.
