Step 2 done: `widget_export/csv_exporter.py` adds three small pure functions, `escape_field`, `format_row`, and `to_csv`, with a header row and RFC 4180 quoting, per the CSV-first decision.
The repo holds no column list from step 1, so I assumed id, name, and created_at in one `COLUMNS` constant for you to adjust.
No tests run, nothing committed, plan checkbox and step 3 untouched.
