Created `exporter.py` with `export_widgets(widgets)`, which writes a `id,name` header via `csv.DictWriter` and one row per widget dict, ignoring extra keys and blanking missing ones.
Empty input yields just the header line, which matches the CSV-first decision in memory and sets up step 3's empty-input test.
Tests were not run and nothing was committed; PLAN.md step 2 is left unchecked for you to mark.
