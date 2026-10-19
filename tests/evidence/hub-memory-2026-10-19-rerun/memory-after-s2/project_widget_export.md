---
name: widget-export
description: Export format decision for the widget-export task in sample-project (JSON default since 2026-10-19; CSV only on explicit request)
metadata:
  node_type: memory
  type: project
  originSessionId: 957eea4b-3b2f-4f13-ba2f-d6a589273298
  modified: 2026-10-19T09:25:40.985Z
---

Widgets export as JSON by default. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; the downstream owner confirmed this on 2026-10-19.
Supersedes the earlier CSV-first decision (CSV first, JSON deferred, because the consumer only read CSV). That decision was implemented as the CSV exporter in src/widget_export/ on 2026-10-19 and is kept as the explicit-request path.
