# row8c-unborn-branch: s3-resume

- Read: `<run>/project/.preclear/widget-export/checkpoint.md`
- Read: `<run>/project/widget_export.py`
- Read: `<auto-memory-root>/widget-export-json-default.md`
- Glob: `thoughts/**/*`
- Read: `<run>/project/thoughts/plans/2026-10-15-widget-export.md`
- Bash: `git status --short --branch && git rev-parse HEAD 2>&1 | tail -1 && shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md | cut -c1-12`

Turns 7. Write/Edit calls 0: []. Bash calls naming the configured executable: 0. Results flagged as refusal/denial (structured signals; the full trace is authoritative): 0.
Usage: input 6, cache creation 8004, cache read 56424, output 2312.

## Final reply

The checkpoint matches the repo. `main` is unborn with no commits, and both file digests match (`widget_export.py` a365afc2dc97, plan edbafe72753e). I haven't applied or edited anything. This is the draft for your review.

**Proposed diff against `widget_export.py`**

```diff
@@ -1,3 +1,5 @@
-"""CSV exporter for widgets."""
+"""Exporters for widgets: JSON by default, CSV on explicit request."""
+
+import json
 
 COLUMNS = ("id", "name")
 
@@ -18,3 +20,15 @@
     lines = [",".join(COLUMNS)]
     lines.extend(widget_to_row(widget) for widget in widgets)
     return "\r\n".join(lines) + "\r\n"
+
+
+def widgets_to_json(widgets):
+    return json.dumps([{column: widget[column] for column in COLUMNS} for widget in widgets])
+
+
+def export_widgets(widgets, fmt="json"):
+    if fmt == "json":
+        return widgets_to_json(widgets)
+    if fmt == "csv":
+        return widgets_to_csv(widgets)
+    raise ValueError(f"unsupported export format: {fmt!r}")
```

- **Default format:** `export_widgets` is the single entry point, and `fmt` defaults to `"json"`. CSV is only produced when a caller passes `fmt="csv"`, as the 2026-11-05 decision requires.
- **CSV exporter:** `widgets_to_csv` and its helpers are unchanged, so existing CSV behavior is preserved.
- **Bad formats:** an unknown format raises `ValueError` instead of silently falling back.
- **JSON shape, still unconfirmed:** I assumed a top-level array of `{"id": ..., "name": ...}` objects, reusing `COLUMNS` for the keys. The alternative is an envelope such as `{"widgets": [...]}`, or different key names. Please confirm which one the downstream JSON API expects before I implement.
- **Not done:** I ran no tests, and plan step 3 (the empty-input test) hasn't been started. With this draft, empty input gives `[]` for JSON and a header-only file for CSV.

If you approve this (or tell me the shape to use), I'll apply it to `widget_export.py`.
