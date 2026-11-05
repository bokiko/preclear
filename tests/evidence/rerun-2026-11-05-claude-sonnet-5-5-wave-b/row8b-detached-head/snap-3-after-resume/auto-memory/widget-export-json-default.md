---
name: widget-export-json-default
description: widget-export default format is JSON (CSV only on explicit request); supersedes the 2026-10-15 CSV-first plan decision
metadata:
  node_type: memory
  type: project
  originSessionId: a7760e28-08f3-4fc8-87ae-8f7881ad7dc9
  modified: 2026-11-05T06:22:23.708Z
---

Decision (user-confirmed 2026-11-05): JSON is the default export format for widget-export; CSV is supported only on explicit request. This supersedes the "CSV first, JSON deferred" decision in thoughts/plans/2026-10-15-widget-export.md.

**Why:** the downstream owner confirmed the consumer migrated to a JSON API in the week of 2026-10-12, so it no longer reads CSV by default.

**How to apply:** treat any new export work as JSON-first; keep the existing CSV exporter (widget_export.py `to_csv`) as the explicit-request path. Do not apply a JSON-default change until the user has reviewed the proposed diff.
