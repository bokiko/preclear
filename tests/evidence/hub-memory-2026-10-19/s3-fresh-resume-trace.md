# Stage 3: fresh conversation B, resume line pasted

- Read: `<scratch>/project/.preclear/widget-export/checkpoint.md`
- Read: `<scratch>/project/thoughts/plans/2026-10-15-widget-export.md`
- Read: `<scratch>/project/memory/project_widget_export.md`
- Bash: `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git status --porcelain && shasum -a 256 widget_export/csv_exporter.py widget_export/__init__.py`
- Read: `<scratch>/project/widget_export/csv_exporter.py`
- Read: `<scratch>/project/widget_export/__init__.py`
- Bash: `set -e
S=/tmp/widget-export-draft && rm -rf "$S" && mkdir -p "$S/old/widget_export" "$S/new/widget_export"
P=<scratch>/project
cp "$P/widget_export/csv_exporter.py" "$P/widget_export/__init__.py" "$S/old/widget_export/"
`
- Bash: `S=/tmp/widget-export-draft && rm -rf "$S" && mkdir -p "$S/old/widget_export" "$S/new/widget_export" && P=<scratch>/project && cp "$P/widget_export/csv_exporter.py" "$P/widget_export/__init__.py" "$S/old/widget_export/" &`

Turns 9. Usage: input 130, cache creation 15602, cache read 125944, output 6003.

## Final reply

The scratch-directory route needs approvals this session can't grant, so I'll present the diff directly. The old content is small and fully known, so the hunks below are hand-written against the current untracked files.

**Proposed diff: JSON becomes the default, CSV stays available only on explicit request.** Nothing has been written to the tree. The diff is relative to the untracked files at HEAD 3d9865f and follows the plan boundaries: pure functions, reuse of `COLUMNS`, and `to_csv` left untouched. `csv_exporter.py` has no changes.

```diff
--- /dev/null
+++ b/widget_export/json_exporter.py
@@ -0,0 +1,27 @@
+"""JSON exporter for widgets (default format, see memory/project_widget_export.md).
+
+Every function here is pure: no I/O, no mutation of inputs. Callers decide
+where the resulting string goes.
+"""
+
+import json
+from typing import Any, Iterable, Mapping, Sequence
+
+from .csv_exporter import COLUMNS
+
+
+def select_fields(widget: Mapping[str, Any], columns: Sequence[str] = COLUMNS) -> dict[str, Any]:
+    """Project one widget onto the export columns, in column order.
+
+    Missing keys become null, mirroring the empty field in the CSV exporter.
+    """
+    return {column: widget.get(column) for column in columns}
+
+
+def to_json(widgets: Iterable[Mapping[str, Any]], columns: Sequence[str] = COLUMNS) -> str:
+    """Render widgets as a JSON array of objects.
+
+    Empty input yields "[]". Values JSON cannot encode natively (e.g. datetimes)
+    fall back to str(), matching the CSV exporter's rendering.
+    """
+    return json.dumps([select_fields(widget, columns) for widget in widgets], default=str)
```

```diff
--- a/widget_export/__init__.py
+++ b/widget_export/__init__.py
@@ -1,5 +1,38 @@
-"""Widget export. CSV first; JSON deferred (see memory/project_widget_export.md)."""
+"""Widget export. JSON by default; CSV only on explicit request (see memory/project_widget_export.md)."""
+
+from typing import Any, Callable, Iterable, Mapping, Sequence
 
 from .csv_exporter import COLUMNS, escape_field, format_row, to_csv
+from .json_exporter import select_fields, to_json
+
+DEFAULT_FORMAT = "json"
+
+_EXPORTERS: dict[str, Callable[[Iterable[Mapping[str, Any]], Sequence[str]], str]] = {
+    "json": to_json,
+    "csv": to_csv,
+}
+
+
+def export(
+    widgets: Iterable[Mapping[str, Any]],
+    fmt: str = DEFAULT_FORMAT,
+    columns: Sequence[str] = COLUMNS,
+) -> str:
+    """Render widgets in the requested format; JSON unless the caller asks for CSV."""
+    try:
+        exporter = _EXPORTERS[fmt]
+    except KeyError:
+        raise ValueError(f"unknown export format {fmt!r}; expected one of {sorted(_EXPORTERS)}") from None
+    return exporter(widgets, columns)
 
-__all__ = ["COLUMNS", "escape_field", "format_row", "to_csv"]
+__all__ = [
+    "COLUMNS",
+    "DEFAULT_FORMAT",
+    "escape_field",
+    "export",
+    "format_row",
+    "select_fields",
+    "to_csv",
+    "to_json",
+]
```

Design choices worth a glance before you approve:

- **Default lives in one place.** `export(widgets)` yields JSON. CSV requires `fmt="csv"`, so no caller gets CSV by accident. Unknown formats raise `ValueError` rather than silently falling back.
- **Column parity.** `select_fields` reuses `COLUMNS` and the same missing-key behaviour as `format_row`, so JSON and CSV output agree on shape. The assumed column list from step 1 still stands as unconfirmed.
- **Serialisation fallback.** `json.dumps(..., default=str)` keeps datetimes and similar values exportable, matching how the CSV path stringifies them. If the downstream JSON API expects ISO 8601 specifically, that would be a follow-up.
- **No trailing newline on JSON output.** CSV ends with CRLF because RFC 4180 lines do. JSON has no such convention, so I left it bare. Easy to add if your file writer wants it.

I did not compile, test, write, stage, or commit anything, per the checkpoint boundaries. Plan step 3 is untouched. The checkpoint file is unchanged and still waiting for the next `/preclear`.

Next step is yours: say the word and I'll apply this to `widget_export/`, or tell me what to change first.
