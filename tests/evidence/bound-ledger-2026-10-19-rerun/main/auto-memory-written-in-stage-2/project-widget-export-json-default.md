---
name: project-widget-export-json-default
description: widget-export defaults to JSON since 2026-10-19; CSV only on explicit request (user correction)
metadata:
  node_type: memory
  type: project
  originSessionId: 62e4c5c9-4ceb-4b0f-baad-2cf36bc4f902
  modified: 2026-10-19T09:59:05.135Z
---

For the widget-export task, JSON is the default export format and CSV is supported only on explicit request. bokiko confirmed this on 2026-10-19 from the downstream owner: the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the earlier CSV-first decision.

**Why:** the only consumer no longer reads CSV by default, so a CSV-first exporter would ship the wrong default.

**How to apply:** treat JSON as the default in any exporter design or review; do not reintroduce CSV-first. The task's continuity ledger (`CONTINUITY_CLAUDE-widget-export.md`, Decisions section) is the authoritative decision record.
