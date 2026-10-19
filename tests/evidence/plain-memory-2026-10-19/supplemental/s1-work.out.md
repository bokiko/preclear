Created `exporter.py` with `export_widgets(widgets, fmt='json')`: JSON array text by default, CSV with header `id,name` when `fmt='csv'`, and a `ValueError` for any other format.
Marked step 2 done in PLAN.md and recorded the corrected decision (JSON default, consumer moved to a JSON API) plus the no-tests/no-commit rule in memory.
No tests were run and nothing was committed; step 3 (empty-input test) is next when you give the go-ahead.
