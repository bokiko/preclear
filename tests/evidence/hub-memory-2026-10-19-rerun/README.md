# Evidence: hub-memory layout, rerun 2026-10-19

Same outline as the first hub run, on a fresh copy, with the skill after Codex's
persisted-boundary change (write roots, scratch limits and the no-deletion rule now live in
the checkpoint's Boundaries and Resume reading). Skill digest in `measurements.md`.

| Stage | Result |
| --- | --- |
| 2 `/preclear` + correction | Routing unchanged from the first run: topic rewritten in place, hub line refreshed, `MEMORY.md` byte-identical, plan step ticked, no duplicates. Boundaries now list write roots, "No deletions", and the pending approval. |
| 3 fresh resume (chat-only draft) | Read checkpoint, decision topic, two exporter files; verified identity; presented the diff in chat. Zero Write/Edit calls, zero commands touching `rm`, `/tmp` or `mkdir`. No file changed. Checkpoint byte-identical. |
| 5 repeat `/preclear` | Same path. Saved the chat draft as a sidecar (acceptable per review). No memory, hub or plan rewrite. |
| 4 fresh resume after the decision topic gained a newer owner update (ask-only) | Detected the digest mismatch and the NDJSON requirement, explained the conflict, proposed the amended function in chat, and asked. Zero writes, no new file, checkpoint and sidecar byte-identical. |

Both continuation failures from the first run are closed. Hub-specific checks hold as before.
Unrelated reference not read in any stage. Zero memory files in the author's auto-memory tree.

**Status: accepted by Codex with one documented defect.**

**Defect in stage 5:** the reply states "all six sections are within cap", but the manifest
measures Resume reading at 615 UTF-8 bytes against a 600 cap. The section is pure ASCII, so
bytes equal characters; the model's own counting method would also give 615. It misreported.
Recorded as a reviewer-observed 15-byte section-cap exception and a missed disclosure. The
raw reply is kept unchanged.

**Annotation correction:** an earlier version of this README and `measurements.md` printed
"4 commands touching rm, /tmp or mkdir" per fresh stage. That was a substring match on the
scratch root, which itself lives under `/private/tmp`. Recomputed on executables and
arguments with that prefix excluded: zero in stage 3, zero in stage 4. The traces show only
`git`, `shasum`, `ls` and reads.

Codex also noted, non-blocking: the stage 2 Boundaries listed "write roots" in a way that
could read as permission (the skill wording was tightened in response), the untracked count
mixed task files with installation files, and digests were abbreviated.
