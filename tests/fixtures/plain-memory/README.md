# Fixture: plain-memory

Claude Code auto-memory with a flat `MEMORY.md` index and one topic file, kept inside the
project at `project/memory/`. The project has a `PLAN.md`. No hubs, no ledger, no
configuration block.

Harness setup: copy this folder, then generate a per-run settings file from
`runtime-settings.example.json` with the absolute path of the copy's `project/memory`, and
launch with `--settings <that file>` and `--setting-sources project,local`. Verify before
work that the instruction-named root (CLAUDE.md) and the effective auto-memory root are the
same directory. Any model-directed memory write outside the copy fails isolation.
