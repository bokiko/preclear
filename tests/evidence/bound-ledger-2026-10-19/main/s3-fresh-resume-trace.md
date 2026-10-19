# Stage 3: fresh unbound conversation, resume line pointing at the ledger

- Bash: `<helper> status 2>&1; echo "---SHOW---"; <helper> show 2>&1`
- Bash: `<helper> menu 2>&1; echo "---BIND---"; <helper> bind <run>/ledgers/CONTINUITY_CLAUDE-widget-export.md 2>&1; echo "---SHOW---"; <helper> show 2>&1`
- Read: `<author-workspace-policy>`
- Bash: `git status --short && echo "---DIFF---" && git diff && echo "---TREE---" && find . -path ./.git -prune -o -type f -print | sort`
- Grep: `preclear|widget-export`
- Read: `<run>/project/widget_export.py`
- Read: `<run>/project/thoughts/plans/2026-10-15-widget-export.md`
- Bash: `shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md && wc -c widget_export.py && echo "---NEXT---" && cat .preclear/widget-export/next.md && echo "---NOTE---" && cat .preclear/widget-export/note.md && echo "---BLOCK---`
- Write: `<run>/project/.preclear/widget-export/widget_export.proposed.py`
- Bash: `<helper> update --help 2>&1 | head -40; echo "---NOTE HELP---"; <helper> note --help 2>&1 | head -20`
- Bash: `diff -u --label a/widget_export.py --label b/widget_export.py widget_export.py .preclear/widget-export/widget_export.proposed.py > .preclear/widget-export/json-default.diff; echo "diff exit $?"; cat .preclear/widget-export/json-default.diff`
- Bash: `<helper> 2>&1 | head -40; echo "---"; <helper> help 2>&1 | head -60`
- Bash: `diff -u --label a/widget_export.py --label b/widget_export.py widget_export.py .preclear/widget-export/widget_export.proposed.py`
- Bash: `shasum -a 256 widget_export.py .preclear/widget-export/widget_export.proposed.py`
- Write: `<run>/project/.preclear/widget-export/json-default.diff`
- Write: `<run>/project/.preclear/widget-export/upd-goal.md`
- Write: `<run>/project/.preclear/widget-export/upd-blockers.md`
- Write: `<run>/project/.preclear/widget-export/upd-evidence.md`
- Write: `<run>/project/.preclear/widget-export/upd-next.md`
- Write: `<run>/project/.preclear/widget-export/note-20261019-diff-drafted.md`
- Bash: `<helper> update --section "Goal & current state" --expect-section 41889872531ed7e1f9492b6aca3c849e865f9e358583672d412c384439fa8916 --from .preclear/widget-export/upd-goal.md`
- Bash: `<helper> update --section "Blockers & open questions" --expect-section 18f31eb7e42d4a774d58dd587fd5329943b5ec70ef336aae379f7be83ea3ccb3 --from .preclear/widget-export/upd-blockers.md`
- Bash: `<helper> update --section "Evidence & key paths" --expect-section 44baf5bd833647736bad9c49cd1e4e877c0df78b4937f6d50c077234fa66b8b8 --from .preclear/widget-export/upd-evidence.md`
- Bash: `<helper> update --section "Next action" --expect-section 2484404d40b25b80a3aaa616d01cf2e81ed6d255e1de89774571f31569bf8d44 --from .preclear/widget-export/upd-next.md`
- Bash: `<helper> note --from .preclear/widget-export/note-20261019-diff-drafted.md`
- Bash: `<helper> show 2>&1 | grep -E '^(section-hash|## )' ; echo "---SIZE---"; <helper> show 2>&1 | grep -vE '^(ledger:|file-fingerprint:|checkpoint-updated:|section-hash:)' | wc -c`
- Write: `<run>/project/.preclear/widget-export/upd-evidence.md`
- Write: `<run>/project/.preclear/widget-export/upd-next.md`
- Bash: `<helper> update --section "Evidence & key paths" --expect-section 44baf5bd833647736bad9c49cd1e4e877c0df78b4937f6d50c077234fa66b8b8 --from .preclear/widget-export/upd-evidence.md`
- Bash: `<helper> update --section "Next action" --expect-section 2484404d40b25b80a3aaa616d01cf2e81ed6d255e1de89774571f31569bf8d44 --from .preclear/widget-export/upd-next.md`
- Bash: `<helper> status 2>&1 && <helper> lint 2>&1 | tail -5`
- Bash: `shasum -a 256 widget_export.py && git status --short`

Turns 33. Usage: input 386, cache creation 43373, cache read 594013, output 15741.

## Final reply

Resumed widget-export and completed the ledger's Next action: the JSON-default diff is drafted and awaiting your review. Nothing was applied, tested, or committed.

**State check.** The session was unbound, so I bound it to the ledger you named (it also matches the project CLAUDE.md). Identity verified: main at 544b438, the plan and exporter digests match the checkpoint. The real `widget_export.py` is unchanged.

**Proposed diff** (saved at `.preclear/widget-export/json-default.diff`, full file beside it as `widget_export.proposed.py`):

```diff
--- a/widget_export.py
+++ b/widget_export.py
@@ -1,14 +1,21 @@
-"""CSV exporter for widgets (plan step 2).
+"""Widget exporter (plan step 2).
 
-Format decision from the continuity ledger: CSV first, JSON deferred,
-because the downstream consumer only reads CSV.
+Format decision from the continuity ledger (2026-10-19): JSON is the default
+export format; CSV only on explicit request. The downstream consumer moved to
+a JSON API in the week of 2026-10-12, which supersedes the earlier CSV-first
+decision.
 """
 
-from typing import Any, Iterable, Mapping, Sequence
+import json
+from typing import Any, Callable, Iterable, Mapping, Sequence
 
 # Step 1: the export columns, in output order.
 EXPORT_COLUMNS: Sequence[str] = ("id", "name")
 
+FORMAT_JSON = "json"
+FORMAT_CSV = "csv"
+DEFAULT_FORMAT = FORMAT_JSON
+
 _DELIMITER = ","
 _LINE_END = "\r\n"
 _SPECIAL_CHARS = (_DELIMITER, '"', "\n", "\r")
@@ -32,6 +39,11 @@
     return [widget.get(column) for column in columns]
 
 
+def widget_record(widget: Mapping[str, Any], columns: Sequence[str] = EXPORT_COLUMNS) -> dict:
+    """Pick the column values from a widget as a mapping, in column order."""
+    return {column: widget.get(column) for column in columns}
+
+
 def export_widgets_csv(
     widgets: Iterable[Mapping[str, Any]], columns: Sequence[str] = EXPORT_COLUMNS
 ) -> str:
@@ -39,3 +51,32 @@
     lines = [format_row(columns)]
     lines.extend(format_row(widget_fields(widget, columns)) for widget in widgets)
     return _LINE_END.join(lines) + _LINE_END
+
+
+def export_widgets_json(
+    widgets: Iterable[Mapping[str, Any]], columns: Sequence[str] = EXPORT_COLUMNS
+) -> str:
+    """Build the JSON text: a list with one object per widget, keyed by column."""
+    records = [widget_record(widget, columns) for widget in widgets]
+    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"
+
+
+_EXPORTERS: Mapping[str, Callable[..., str]] = {
+    FORMAT_JSON: export_widgets_json,
+    FORMAT_CSV: export_widgets_csv,
+}
+
+
+def export_widgets(
+    widgets: Iterable[Mapping[str, Any]],
+    columns: Sequence[str] = EXPORT_COLUMNS,
+    fmt: str = DEFAULT_FORMAT,
+) -> str:
+    """Export widgets as JSON by default; CSV only when explicitly requested."""
+    try:
+        exporter = _EXPORTERS[fmt]
+    except KeyError:
+        raise ValueError(
+            f"unknown export format {fmt!r}; expected one of {sorted(_EXPORTERS)}"
+        ) from None
+    return exporter(widgets, columns)
```

**Design.** The CSV functions stay intact, so the "do not redo step 2" decision holds. One new record builder, one JSON exporter, and a small dispatcher whose default is JSON. CSV comes only from an explicit `fmt="csv"`. Empty input yields `[]` for JSON, which lines up with plan step 3.

**Three questions for your review:**
- **JSON shape.** A top-level list of objects keyed by column. Confirm the downstream JSON API wants that rather than a wrapper object.
- **Formatting.** Two-space indent with a trailing newline. Say if compact output is preferred.
- **Plan text.** Steps 2 and 3 still say CSV. Decide whether the plan gets a JSON step.

**Caveat.** Tests are forbidden by the ledger, so neither the current file nor the proposal has been imported or syntax-checked. That stays UNCONFIRMED in the ledger.

**Ledger.** Goal, Blockers, Evidence, and Next action sections updated through the checkpoint helper, history note appended, lint OK. Next action now reads: await your verdict, then apply on approval or redraft on changes.
