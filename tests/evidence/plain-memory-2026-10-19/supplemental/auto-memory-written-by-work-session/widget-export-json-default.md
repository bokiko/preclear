---
name: widget-export-json-default
description: "Widget export format decision — JSON is the default, CSV only on request (supersedes the earlier CSV-only decision)"
metadata:
  node_type: memory
  type: project
  originSessionId: 1ba7eef4-5a70-4b18-b19d-91343722a179
  modified: 2026-10-19T08:44:57.152Z
---

Widgets export as JSON by default; CSV (header `id,name`) only when explicitly requested via `fmt='csv'`. This corrects the earlier "CSV exporter" decision in PLAN.md step 2.

**Why:** The downstream consumer migrated to a JSON API in the week of 2026-10-12, so it now accepts JSON as well. User stated this on 2026-10-19.

**How to apply:** Keep `export_widgets(widgets, fmt='json')` defaulting to JSON. Don't reintroduce CSV as the default. See [[widget-export-no-tests-no-commit]].
