---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  node_type: memory
  type: project
  originSessionId: eec13221-7279-4747-b4ac-de2fdf27b35b
  modified: 2026-11-07T09:29:09.704Z
---

Widgets export as JSON by default. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; the owner confirmed JSON as default.
Supersedes the earlier CSV-first decision (consumer then read only CSV).
