# Fixture: hub-memory

Claude Code auto-memory organised around hubs. Canonical memory is project-local at
`project/memory/`. `MEMORY.md` is a hub-only index: it lists `hub_projects.md` and
`hub_feedback.md`, never individual topics. Topic files are indexed in the matching hub.
The plan lives in `project/thoughts/plans/`.

Harness setup: copy this folder, then have the launcher generate a per-run settings file
from `runtime-settings.example.json`, replacing the placeholder with the absolute path of
the copy's `project/memory` (the `autoMemoryDirectory` override). Launch with
`--settings <that file>` and `--setting-sources project,local`. Verify before work that the
instruction-named root (CLAUDE.md) and the effective auto-memory root are the same
directory. Any model-directed memory write outside the copy fails isolation.

Run ordinary work and `/preclear` in the same conversation. Start a fresh conversation only for the resume stage.
The durable correction for the memory test is introduced in the `/preclear` turn, not
during work.
