# Evidence: plain-memory layout, 2026-10-19

**Status: accepted on 2026-10-19 after three runs.** Codex failed the first two on evidence
gaps, then passed the layout once the targeted memory-update run closed the last one.
The history below is kept as it happened; checks are not relabelled.

Roll-up: which run establishes each criterion

| Criterion | Established by |
| --- | --- |
| Plan step update, same-path reuse, collision preserved, useful continuation | first run (this folder) |
| Blocked next action is one question; checkpoint untouched by the fresh session; same-status content change detected; sections measured in cap | `supplemental/` |
| Durable memory updated by preclear itself, in place, inside the fixture, no duplicates | `targeted-memory-update/` |
| No git mutation, no deletion, no write outside the fixture | all three (the first attempt that hit the legacy skill is kept apart in `failed-attempt-name-collision/`) |

Headless runs (`claude -p`, Claude Code 2.1.303) on a copy of `tests/fixtures/plain-memory/`
with the skill installed as a project skill and `--setting-sources project,local` so the
author's user-level skills and instructions were excluded. Skill under test: SKILL.md as
committed in 600f366. Paths are sanitized to `<scratch>`; byte measurements in
`measurements.md` were taken on the originals before sanitizing.

Provenance: `run1-checkpoint.md` is the checkpoint the first `/preclear` wrote, recovered
from the session transcript's Write call. `after-fresh-session-checkpoint.md` is the same
file after the fresh session rewrote it (finding 2). An earlier copy of this folder had those
two mislabelled.

## Sequence and results

| Step | What ran | Result |
| --- | --- | --- |
| 0 | First attempt without `--setting-sources`: the author's legacy user-level skill of the same name ran instead of the project skill. It wrote a real ledger and bound a session on the author's machine. | Name collision; see finding 1 below. Rerun isolated. |
| 1 | Fake work: create `exporter.py` (plan step 2), no tests, no commit. Then `/preclear` in the same session. | Checkpoint 3,110 bytes, six headings, one next action. PLAN.md step 2 ticked. No memory write (decision already recorded). No hub files. Git untouched. Resume line last. Line 235 chars, reported as an exception. Package 4,240 bytes. |
| 2 | Fresh session, resume line pasted. | Read checkpoint, PLAN.md, exporter.py; verified branch, HEAD, digests; wrote the step-3 test; ticked step 3; rewrote the checkpoint. 9 turns. Usage: input 162, cache creation 13,534, cache read 148,372, output 3,384. These categories do not isolate the skill's resume cost; the byte package is the proxy. No broad rediscovery. |
| 3 | `/preclear` again in that session. | Same path `.preclear/widget-export/checkpoint.md` reused. |
| 4 | Project path inside the checkpoint changed to another project, then `/preclear`. | Original byte-identical before and after. New checkpoint at `widget-export-2/`. Reply warned about the external edit. |

## Common checks

- [x] No git mutation, no deletion.
- [x] No configuration change, no external write.
- [x] Files read back; checkpoint reread by the fresh session matched.
- [x] Branch, HEAD, status agree with the checkpoint.
- [ ] Exactly one presently authorized next action. Run 1: yes. Runs 2 and 3: the
      next action was a conditional test-then-commit plan under a standing no-test
      boundary. Skill text tightened after this run.
- [ ] Bytes within caps. Run 1: all sections in cap (manifest). Run 3: Boundaries
      608/600 and Evidence 1,059/1,000 with no measured exception; the model's
      `awk` measurement was denied by the harness and it estimated instead.
- [x] Fresh session reached the next action without broad rediscovery.
- [ ] Checkpoint left unchanged by the fresh session: no, it rewrote it (finding 2).
      Rule added to the skill after this run.
- [x] Output ends with one fenced single-line block (harness exit annotations aside).

## plain-memory checks

- [ ] Durable memory update: **not exercised**. Nothing new was durable, so the
      correct no-op is shown, but the update path still needs a run.
- [x] One plan step updated in PLAN.md.
- [x] Volatile state only in the checkpoint.
- [x] No hub files created.
- [x] Second run reused the same path.
- [x] Collision left the original byte-identical (sha in manifest) and selected `-2`.

## Follow-up runs (same day)

1. Durable memory update with a real new correction: `targeted-memory-update/`, passed.
2. Blocked case, one-question next action: `supplemental/`, passed.
3. Freshness case, same-status content change: `supplemental/`, passed.
4. Lifecycle, checkpoint byte-identical after the fresh session: `supplemental/`, passed.

## Findings

1. **Name collision with an older skill of the same name.** User-level `preclear` won over the project-level one. Users migrating from a private version must remove or rename it. README needs an install note.
2. **The fresh session rewrote the checkpoint on its own** after finishing the step, without `/preclear` being invoked. Behaviour was correct, but it is not specified anywhere.
3. **Untracked count wording** in Evidence ("untracked 4 (plus this .preclear/ tree)") is ambiguous about whether preclear's own files are inside the count.
4. The harness denied an `awk` call the skill wanted for per-section byte checks; the skill fell back to estimates and said so. Not a skill defect.

Files in this folder are the raw sanitized outputs for each step.
