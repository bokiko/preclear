# Rerun 2026-10-29 on claude-sonnet-5-5

This folder is a new baseline on the pinned model and build (model claude-sonnet-5-5, Claude Code 2.1.310). It is not a replication of the 2026-10-20 run: that run recorded no model, so the model cannot be matched.

Row total: 0.27231170000000002. Run total: 0.27231170000000002. Both are quoted from `row1-wrong-binding/usage.txt`.

Differences from the 2026-10-20 run:

- Claude Code 2.1.310 against 2.1.304
- the pinned flag set
- the stub in place of the real helper
- per-verb allowlist
- run roots outside the home folder
- strict isolation

The committed folder stays the reference: `tests/evidence/publication-2026-10-20`. Every file written by the harness holds facts, counts and ids; each row README ends with a checklist for the reviewer.
