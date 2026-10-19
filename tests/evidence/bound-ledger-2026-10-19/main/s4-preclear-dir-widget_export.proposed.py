"""Widget exporter (plan step 2).

Format decision from the continuity ledger (2026-10-19): JSON is the default
export format; CSV only on explicit request. The downstream consumer moved to
a JSON API in the week of 2026-10-12, which supersedes the earlier CSV-first
decision.
"""

import json
from typing import Any, Callable, Iterable, Mapping, Sequence

# Step 1: the export columns, in output order.
EXPORT_COLUMNS: Sequence[str] = ("id", "name")

FORMAT_JSON = "json"
FORMAT_CSV = "csv"
DEFAULT_FORMAT = FORMAT_JSON

_DELIMITER = ","
_LINE_END = "\r\n"
_SPECIAL_CHARS = (_DELIMITER, '"', "\n", "\r")


def format_field(value: Any) -> str:
    """Render one value as a CSV field, quoting only when required."""
    text = "" if value is None else str(value)
    if any(ch in text for ch in _SPECIAL_CHARS):
        return '"' + text.replace('"', '""') + '"'
    return text


def format_row(fields: Iterable[Any]) -> str:
    """Join already-ordered field values into one CSV line."""
    return _DELIMITER.join(format_field(field) for field in fields)


def widget_fields(widget: Mapping[str, Any], columns: Sequence[str] = EXPORT_COLUMNS) -> list:
    """Pick the column values from a widget, in column order."""
    return [widget.get(column) for column in columns]


def widget_record(widget: Mapping[str, Any], columns: Sequence[str] = EXPORT_COLUMNS) -> dict:
    """Pick the column values from a widget as a mapping, in column order."""
    return {column: widget.get(column) for column in columns}


def export_widgets_csv(
    widgets: Iterable[Mapping[str, Any]], columns: Sequence[str] = EXPORT_COLUMNS
) -> str:
    """Build the full CSV text: a header line, then one line per widget."""
    lines = [format_row(columns)]
    lines.extend(format_row(widget_fields(widget, columns)) for widget in widgets)
    return _LINE_END.join(lines) + _LINE_END


def export_widgets_json(
    widgets: Iterable[Mapping[str, Any]], columns: Sequence[str] = EXPORT_COLUMNS
) -> str:
    """Build the JSON text: a list with one object per widget, keyed by column."""
    records = [widget_record(widget, columns) for widget in widgets]
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


_EXPORTERS: Mapping[str, Callable[..., str]] = {
    FORMAT_JSON: export_widgets_json,
    FORMAT_CSV: export_widgets_csv,
}


def export_widgets(
    widgets: Iterable[Mapping[str, Any]],
    columns: Sequence[str] = EXPORT_COLUMNS,
    fmt: str = DEFAULT_FORMAT,
) -> str:
    """Export widgets as JSON by default; CSV only when explicitly requested."""
    try:
        exporter = _EXPORTERS[fmt]
    except KeyError:
        raise ValueError(
            f"unknown export format {fmt!r}; expected one of {sorted(_EXPORTERS)}"
        ) from None
    return exporter(widgets, columns)
