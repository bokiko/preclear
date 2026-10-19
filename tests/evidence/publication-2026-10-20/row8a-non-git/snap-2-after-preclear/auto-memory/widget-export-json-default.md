---
name: widget-export-json-default
description: widget-export defaults to JSON; CSV only on explicit request (supersedes 2026-10-15 CSV-first decision)
metadata:
  node_type: memory
  type: project
  originSessionId: 3778b576-e222-4a3c-9d10-c3f27d7c374f
  modified: 2026-10-19T23:35:41.370Z
---

widget-export uses JSON as the default export format. CSV is produced only when a caller explicitly asks for it. This supersedes the 2026-10-15 "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream owner confirmed on 2026-10-20 that the consumer moved to a JSON API in the week of 2026-10-12.

**How to apply:** new or changed export code and tests treat JSON as the default and CSV as opt-in. Don't follow the old CSV-first line in the plan.
