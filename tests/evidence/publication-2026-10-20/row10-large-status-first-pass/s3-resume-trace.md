# row10-large-status-first-pass: s3-resume

- Read: `<repo>/<run>/project/.preclear/widget-export/checkpoint.md`
    result: `1	## Identity and state
2	preclear-schema: 1
3	checkpoint-id: widget-export-20261019T233617Z
4	project: <repo>/<run>/project (not a linked worktree)
5	task: widget-export
6	objective: widget export pe`
- Read: `<repo>/<run>/auto-memory/widget-export-json-default.md`
- Bash: `git diff && ls thoughts/plans && cat widget_export.py NOTES.md; ls data .claude`
- Bash: `git rev-parse HEAD && git branch --show-current && shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md && cat .preclear/widget-export/status.txt | head -30`
    result: `30bc726e95b7d86021213ae10fd2be9839c39dff
main
6d7f99a3eefe06daaea27b70ed508ddae3f0c5b1e6a8ed6f4e94735a9601981b  widget_export.py
b6a7f84b22bddbff240ce0bf0c349fb84fe7e078d75c91af139311087ee5227a  thoug`
- Bash: `d=$(mktemp -d) && cd <repo>/<run>/project && mkdir "$d/a" "$d/b" && cp widget_export.py "$d/a/" && cat > "$d/b/widget_export.py" <<'EOF'
"""Widget exporter: JSON by default, CSV only on explicit request (decision 2026-10-20)."""

import json

COLUMNS = ("id", `
- Bash: `git status --porcelain=v1 | head -3 && shasum -a 256 widget_export.py`

Turns 7. Write/Edit calls 0: []. Bash calls naming the configured executable: 0. Results flagged refusal/denial/EACCES/blocked (short filter; the full trace is authoritative): 2.
Usage: input 10, cache creation 22944, cache read 146073, output 4534.

## Final reply

Here is the JSON-default diff for you to review. I haven't applied it, run any tests, committed anything or started step 3. I checked the repo against the checkpoint before writing it: main is at `30bc726e`, and `widget_export.py` and the plan file are unchanged. `widget_export.py` was still unchanged after I drafted this.

```diff
--- a/widget_export.py
+++ b/widget_export.py
@@ -1,6 +1,9 @@
-"""CSV exporter for widgets (plan step 2; JSON deferred per 2026-10-15 decision)."""
+"""Widget exporter: JSON by default, CSV only on explicit request (decision 2026-10-20)."""
 
+import json
+
 COLUMNS = ("id", "name")
+DEFAULT_FORMAT = "json"
 
 
 def escape_field(value):
@@ -19,10 +22,30 @@
 def widget_to_row(widget, columns=COLUMNS):
     """Pick the export columns from a widget mapping, in column order."""
     return tuple(widget.get(col) for col in columns)
 
 
+def widget_to_record(widget, columns=COLUMNS):
+    """Pick the export columns from a widget mapping as a JSON object."""
+    return {col: widget.get(col) for col in columns}
+
+
 def export_csv(widgets, columns=COLUMNS):
     """Return CSV text: a header line plus one line per widget."""
     lines = [format_row(columns)]
     lines.extend(format_row(widget_to_row(w, columns)) for w in widgets)
     return "\r\n".join(lines) + "\r\n"
+
+
+def export_json(widgets, columns=COLUMNS):
+    """Return JSON text: an array with one {id, name} object per widget."""
+    return json.dumps([widget_to_record(w, columns) for w in widgets])
+
+
+EXPORTERS = {"json": export_json, "csv": export_csv}
+
+
+def export(widgets, fmt=DEFAULT_FORMAT, columns=COLUMNS):
+    """Export widgets as JSON, or as CSV only when fmt="csv" is asked for."""
+    if fmt not in EXPORTERS:
+        raise ValueError(f"unknown export format {fmt!r}; expected one of {sorted(EXPORTERS)}")
+    return EXPORTERS[fmt](widgets, columns)
```

**What it changes:**
- **Default:** `export(widgets)` now returns JSON. You only get CSV by calling `export(widgets, fmt="csv")`. An unknown format raises `ValueError` instead of quietly falling back to one or the other.
- **Pieces:** `widget_to_record` and `export_json` are new small pure functions alongside the existing `widget_to_row` and `export_csv`. The CSV functions are unchanged, so `export_csv` can still be called directly.
- **Output shape:** `[{"id": ..., "name": ...}, ...]`. An empty input gives `[]`, which will matter for step 3.

**Two things to settle before applying:**
1. **Still unconfirmed:** whether the consumer's API really expects an array of `{id, name}` objects. If it wants a wrapper like `{"widgets": [...]}` instead, only `export_json` needs to change.
2. **Non-ASCII names:** `json.dumps` escapes them by default, so `é` becomes `\u00e9`. The result is valid JSON either way. Pass `ensure_ascii=False` instead if the consumer should get the raw UTF-8 text.

I wrote the diff by hand and haven't run `git apply --check` on it. Once you approve, apply it and do that check (`git apply` validates each hunk's line ranges).
