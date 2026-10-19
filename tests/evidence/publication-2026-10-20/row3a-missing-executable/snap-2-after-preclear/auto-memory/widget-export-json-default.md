---
name: widget-export-json-default
description: widget-export defaults to JSON; CSV only on explicit request (supersedes CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: cc87f6fa-45b3-4e08-996f-6c15d690d171
  modified: 2026-10-19T23:14:33.336Z
---

widget-export (sample-project) exports JSON by default; CSV is supported only on explicit request. This supersedes the earlier CSV-first decision recorded in the continuity ledger.

**Why:** the downstream owner confirmed the consumer migrated to a JSON API in the week of 2026-10-12 (confirmed to bokiko by 2026-10-20).

**How to apply:** treat any "CSV first" text in the widget-export ledger or plan as superseded; new export work targets JSON, keeping CSV as an opt-in path.
