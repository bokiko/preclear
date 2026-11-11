---
name: widget-export
description: "Export format decision for the widget-export task in sample-project (JSON default, CSV on request)"
metadata:
  node_type: memory
  type: project
  originSessionId: d844a56e-2a16-4e27-9dc0-0bf156839bd8
  modified: 2026-11-11T06:45:41.484Z
---

JSON is the default export format. CSV is supported only on explicit request.
Reason: the downstream consumer migrated to a JSON API in the week of 2026-10-12; the owner confirmed this on 2026-11-11.
Supersedes the earlier "CSV first, JSON deferred" decision (the consumer then only read CSV).
