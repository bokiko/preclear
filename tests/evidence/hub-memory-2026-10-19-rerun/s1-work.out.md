Step 2 is done: `src/widget_export/csv_exporter.py` adds a pure `export_widgets_csv` built from two small helpers, using the CSV-first decision from memory.
The repo had no code or column list from step 1, so I assumed Python and defined the columns as `id, name, type, created_at` in `EXPORT_COLUMNS`. Adjust that tuple if step 1 meant different columns.
No tests run, nothing committed, step 3 untouched, and the plan checkbox is left for checkpointing.
