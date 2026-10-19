# Evidence: bound-ledger layout, rerun 2026-10-19

After the first run's stage-3 failure (fresh session bound itself), three changes were made
and the sequence reran on a fresh isolated copy: the adapter persists "Resume is read-only
for continuity state: never bind" into the ledger's Authorization boundaries and Evidence
first line; the generic Resume reading last line says "no file output, binding, or backend
write without authorization"; the fixture CLAUDE.md carries a read-only bootstrap note next
to the configuration block (`main/fixture-CLAUDE.md`). Same isolation as before (`CKPT_HOME`,
fixture roots, harness-bound fixture session). Skill and adapter digests in `main/digests.txt`.

## main/

| Stage | Result |
| --- | --- |
| 2 `/preclear` + correction (bound) | Backend path as before: show, validate, per-section updates with hashes, lint OK (no history note this time; an earlier draft of this table said otherwise). Both persisted rules present in the ledger block, in Authorization boundaries only; the adapter also asks for it as the Evidence first line, which this run omitted. The session also wrote a decision topic and index into Claude Code's auto-memory root for the fixture path (copies and hashes in `main/auto-memory-written-in-stage-2/`). That root is outside the fixture copy, so under the harness rule it is an isolation finding, and the rationale duplicates what the ledger already owns. |
| 3 fresh unbound resume | **PASS.** Four turns. Read the ledger read-only, verified identity and digests, produced the diff in chat. Zero Write/Edit calls, zero helper calls, session still unbound, no file changed. |
| 4 `/preclear` in the still-unbound session | **PASS, writable unbound fallback.** Configuration valid, helper `status` unbound, precondition failed, no bind, ledger read via `show --ledger` and left byte-identical. Plain checkpoint written to `fallback_directory`, 4,045 bytes, all sections in cap, "ledger not synchronized: session unbound" recorded, resume line points at the fallback file. Honest exceptions: required reads over the excerpt allocation; it kept the diff as a design summary because the ledger boundary forbids proposal files. |

Bindings at the end: one (the harness-bound session A only).

**Defect in stage 4 (same class as the hub rerun):** the reply says "All caps hold now",
but `main/measurements.md` shows Boundaries 609/600, Resume reading 615/600 and Do not redo
597/596, and a stray top-level title line above the first heading. Three small overruns and a
false cap claim. Recorded as reviewer-observed exceptions with missed disclosure; the raw reply
is unchanged. This is now the second run where the model's own byte check disagreed with the
manifest, so it is a pattern to fix, not noise.

Two more stage-4 content defects noted by Codex: the fallback Next action reintroduced a
conditional ("if the resume message itself carries approval...") instead of one step, and it
marked "whether CSV stays or is replaced" UNCONFIRMED although the correction explicitly kept
CSV on request. Kept as generated-state defects; the raw checkpoint is unchanged.

Conflict wrapper: the tested wrapper's body extraction (`sed '1,2d'`) left show metadata in the
second writer's body, visible in `conflict/conflict-file.md`; the model removed it while
merging. `conflict/wrapper-checkpoint.fixed.sh` corrects the extraction and has not been used in
any run yet.

## conflict/

Controlled conflict recovery with a test-only wrapper. PASS; see its README.

## Result matrix for the layout

| Check | Result | Where |
| --- | --- | --- |
| Backend write path through the helper | PASS | first run stage 2, rerun stage 2, conflict stage 2 |
| `fallback_directory: none` → BLOCKED | PASS (unbound plus project-mismatch case) | first run `fallback-none/` |
| Fresh-session resume read-only, no bind | PASS after fix (FAIL in first run) | rerun stage 3 |
| Writable unbound fallback | PASS | rerun stage 4 |
| Controlled conflict, bounded retry, merge preserved | PASS | `conflict/` |
| Second conflict before retry → UNSTABLE and fallback | NOT EXERCISED | |
| Mismatched bound ledger → fallback | NOT EXERCISED | |
