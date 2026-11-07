SUPERSEDED: CSV first, JSON deferred (consumer then read only CSV).
CURRENT (user, 2026-11-07): JSON is the default export; CSV only on explicit request. Why: consumer migrated to a JSON API in week of 2026-10-12. Applies to future sessions.
Do not redo: CSV exporter is written; reuse it as the explicit-CSV path. Invalid if widget_export.py digest changes.
