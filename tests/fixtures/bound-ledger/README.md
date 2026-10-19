# Fixture: bound-ledger

This layout uses the `checkpoint-v1` backend. It requires the author's ledger
helper, which is NOT bundled with this repository. Without the helper, run it
only to check the unbound or denied path: preclear should write the plain
fallback checkpoint and label synchronization pending.

Before use, replace `/path/to/sample-project` in `project/CLAUDE.md` with the
absolute path of your scratch copy, and set `executable` to your helper.
