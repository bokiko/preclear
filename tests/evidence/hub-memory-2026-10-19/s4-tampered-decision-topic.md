---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  node_type: memory
  type: project
  originSessionId: 0d995b2d-2b4b-4d13-965a-0e7717e69ac1
  modified: 2026-10-19T09:10:15.431Z
---

Widgets export as JSON by default. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; the downstream owner confirmed this on 2026-10-19.
Supersedes the earlier decision (CSV first, JSON deferred, because the consumer then only read CSV).

Owner update 2026-10-19 (later the same day): the JSON export must be newline-delimited JSON, one object per line, not a JSON array. Supersedes any array assumption.
