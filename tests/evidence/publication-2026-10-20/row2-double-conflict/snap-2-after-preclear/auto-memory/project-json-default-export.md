---
name: project-json-default-export
description: widget-export project exports JSON by default; CSV only on explicit request (supersedes CSV-first)
metadata:
  node_type: memory
  type: project
  originSessionId: b9edab22-c5c1-476e-a6eb-3a18c7e77182
  modified: 2026-10-19T23:11:28.918Z
---

JSON is the default export format for the widget-export project; CSV is supported only when explicitly requested. This supersedes the earlier "CSV first, JSON deferred" decision.

**Why:** the downstream owner confirmed (told to bokiko, recorded 2026-10-20) that the consumer migrated to a JSON API during the week of 2026-10-12.

**How to apply:** new or changed export code makes JSON the default path and keeps CSV behind an explicit option; don't reintroduce CSV as the default.
