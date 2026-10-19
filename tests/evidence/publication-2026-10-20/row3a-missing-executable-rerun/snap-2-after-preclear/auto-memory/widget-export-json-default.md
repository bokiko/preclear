---
name: widget-export-json-default
description: widget-export project — JSON is the default export format; CSV only on explicit request (supersedes CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: e6a50e0e-a210-45da-9975-a00328e000e6
  modified: 2026-10-19T23:28:31.749Z
---

JSON is the default export format for the widget-export project; CSV is supported only on explicit request. Confirmed by the downstream owner, relayed by bokiko 2026-10-20; supersedes the ledger's earlier "CSV first, JSON deferred" decision.

**Why:** the consumer migrated to a JSON API in the week of 2026-10-12.
**How to apply:** treat JSON as the default in any widget-export design. The owning record is the ledger `ledgers/CONTINUITY_CLAUDE-widget-export.md` (Decisions); as of 2026-10-20 it still says CSV-first and needs syncing — see `project/.preclear/widget-export/checkpoint.md`.
