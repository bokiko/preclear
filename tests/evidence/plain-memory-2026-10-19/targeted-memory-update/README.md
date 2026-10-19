# Targeted run: durable memory update performed by preclear itself (2026-10-19)

Codex's design: ordinary CSV work first with no new facts, then one message that starts with
`/preclear` and carries a genuine last-minute correction (JSON becomes the default export).
Fresh copy of the plain-memory fixture in its new layout (memory inside the project),
`--setting-sources project,local`, and a per-run `--settings` file pinning
`autoMemoryDirectory` to the copy's `project/memory`. Prompt text is in
`preclear-turn-prompt.md`.

## Result: PASS on all five criteria

1. Transcript shows the project skill loaded and the topic update happening inside the
   `/preclear` turn (`preclear-turn-tool-calls.md`). Memory hashes were identical before
   and after the work session and changed only in that turn (`measurements.md`).
2. `project_widget_export.md` changed from CSV-first to JSON-default in place, keeping the
   file, its name, its reason line, and recording what it supersedes. `MEMORY.md` kept its
   single pointer line and only refreshed the description. Claude Code's memory tooling
   added `node_type`, `originSessionId`, and `modified` frontmatter fields; the model did
   not author those.
3. No duplicate topic, no hub, no open-thread note, no task-rule memory.
4. Checkpoint 3,150 bytes, every section in cap, points at the memory topic for the
   decision, records the unchanged implementation and the no-test/no-commit boundary, and
   names one next step. PLAN.md had step 2 ticked and gained step 4, appended after step 3
   with a "do before step 3" dependency note (existing step numbers kept). Routing is
   correct: the plan owns task sequence, memory owns the decision.
   Two qualifications recorded by Codex, to apply in future runs, not to rewrite this
   checkpoint: the plan checkbox is not an authorization source, the user's correction is;
   and `UNCONFIRMED` items (JSON shape, CSV opt-in interface) must stay proposals, not
   assumed requirements.
5. Readback and two verification passes in the trace; all memory writes inside the
   fixture copy; no memory files under the author's auto-memory tree for this path.

Resume line 2xx characters because of the scratch path; reported as an exception.
