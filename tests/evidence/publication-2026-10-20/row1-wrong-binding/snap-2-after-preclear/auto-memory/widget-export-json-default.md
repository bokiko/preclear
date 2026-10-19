---
name: widget-export-json-default
description: widget-export exports JSON by default since the week of 2026-10-12; CSV only on explicit request (supersedes the CSV-first ledger decision)
metadata:
  node_type: memory
  type: project
  originSessionId: eace4601-2792-4d29-a7f1-937d1c3ac5ed
  modified: 2026-10-19T23:08:08.690Z
---

For the widget-export task in <repo>/<run>/project, JSON is the default export format and CSV is supported only on explicit request. bokiko confirmed this on 2026-10-20 after the downstream owner reported the consumer migrated to a JSON API in the week of 2026-10-12. This supersedes the "CSV first, JSON deferred" decision recorded in the continuity ledger on 2026-10-19.

**Why:** the only downstream consumer no longer reads CSV by default.

**How to apply:** make JSON the default entry point in any exporter design and keep CSV as an opt-in path. The ledger's CSV-first entry is stale until the ledger is rebound and updated through the checkpoint helper. See [[widget-export-ledger-binding]].
