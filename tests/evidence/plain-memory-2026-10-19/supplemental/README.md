# Supplemental run, 2026-10-19 (same day, after the skill was tightened)

Fresh copy of the plain-memory fixture, `--setting-sources project,local`, skill digest in
`measurements.md`. The harness allowlist now included `awk` and `python3 -c` so the model
could measure sections itself.

| Stage | What ran | Result |
| --- | --- | --- |
| 1 | Fake work with a real durable correction (JSON becomes the default export, consumer migrated to a JSON API) plus a standing "no tests, no commits" rule. Then `/preclear`. | The **work session** saved the correction and the rule to memory as it went. It wrote to Claude Code's auto-memory folder for the fixture path, not the fixture's `../memory`, which it reported `INACCESSIBLE` under the project-only permission scope. `/preclear` then found memory already current and wrote nothing. PLAN.md step 2 ticked by the work session. Checkpoint 3,230 bytes, all sections in cap (measured by the model, confirmed in the manifest). Next action: one question to the user. |
| 2 | Fresh session, resume line pasted. | Read checkpoint, the two memory files, PLAN.md; verified branch, HEAD, digests; stopped and asked the one question. Checkpoint byte-identical before and after (lifecycle rule honoured). 6 turns. Usage: input 66, cache creation 11,650, cache read 65,560, output 1,313. |
| 3 | A line appended to the already-dirty PLAN.md (status unchanged), then `/preclear` in session 2. | Digest recheck caught it. Checkpoint records "line 7 added by an unknown writer", new digest, and warns the user before clearing. All sections in cap. Same path reused. |

## Checks closed by this run

- [x] Blocked case: next action is one question, not a conditional workflow.
- [x] Lifecycle: fresh session leaves the checkpoint byte-identical until `/preclear`.
- [x] Freshness: same-status content change detected through the digest recheck.
- [x] Section caps measured and held in every checkpoint.
- [x] Same path reused on the second `/preclear`.

## Still open

- [ ] **Durable memory update performed by preclear itself.** In both runs the work
      session had already saved the fact, so preclear's write path was a correct no-op.
      To exercise it, the work session must be told not to save memory, or a correction
      must be given only in the `/preclear` turn.

## Findings

5. **Memory root under project-only scope.** The fixture's CLAUDE.md points memory at
   `../memory`, outside the project. With `--setting-sources project,local` the model could
   not read it and used the session-supplied auto-memory root instead, exactly as the
   skill's probe 5 says. Consequence for the harness: memory writes landed in
   `~/.claude/projects/<fixture-slug>/memory/` on the author's machine, outside the
   fixture copy. That is test residue to clean up with approval, and the fixture should
   keep memory inside the project or the harness should pass an explicit memory root.
6. The resume line was 243 and 240 characters because the scratch path is 150 characters.
   Reported as an exception each time, as specified.
