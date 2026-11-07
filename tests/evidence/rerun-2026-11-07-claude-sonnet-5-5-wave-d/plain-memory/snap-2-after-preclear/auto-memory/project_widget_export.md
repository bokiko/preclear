---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  node_type: memory
  type: project
  originSessionId: 51a9ef81-83e6-43b3-9ea1-6716153c7d5b
  modified: 2026-11-07T09:27:52.586Z
---

Widgets export as JSON by default. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; owner confirmed. Supersedes the earlier CSV-first decision.
