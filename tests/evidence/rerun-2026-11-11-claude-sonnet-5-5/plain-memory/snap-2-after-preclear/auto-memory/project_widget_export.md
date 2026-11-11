---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  node_type: memory
  type: project
  originSessionId: 9324af7b-da8d-4a06-80a0-ad439c1109bd
  modified: 2026-11-11T06:44:38.460Z
---

Widgets export as JSON by default. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12 (confirmed by the downstream owner; user correction on 2026-11-11).
Supersedes the earlier CSV-first decision (JSON deferred, consumer read only CSV).
