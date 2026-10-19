---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  node_type: memory
  type: project
  originSessionId: 69dca67b-3414-41fe-b290-7619f2a8de86
  modified: 2026-10-19T08:56:16.558Z
---

Widgets export as JSON by default; CSV only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; the downstream owner confirmed this on 2026-10-19.
Supersedes the earlier CSV-first decision (made when the consumer only read CSV). Applies to all future sessions.
