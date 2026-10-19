---
name: widget-export
description: Export format decision for the widget-export task in sample-project
metadata:
  type: project
---
Widgets export as CSV first. JSON is deferred.
Reason: the downstream consumer only reads CSV.
