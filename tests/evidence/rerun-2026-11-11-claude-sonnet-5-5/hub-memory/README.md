# Layout hub-memory: hub-only memory index kept inside the project (1P + 1R), rerun on the pinned model and build

Setup: the frozen hub-memory fixture project copied in place: its instruction file, the plan under `thoughts/plans`, a hub-only `MEMORY.md` index, two hub files and the topic files. The auto-memory directory is pinned to the `memory` folder inside the project, so a memory write lands in the project, which is an approved root and is under watch in every snapshot. No helper wrapper, no ledger and no binding. A work turn comes first, then the /preclear turn with the JSON-default correction in the same session, then a fresh session that pastes the resume line the /preclear turn printed. The work-turn prompt is new text written for this harness, so this run is a new baseline and not a replication of the committed layout run. The harness prints the `MEMORY.md` digest before and after, the memory file list and the number of new memory files. The harness does not exercise the identity collision, blocked instruction, freshness edit, tamper or repeat /preclear checks of the committed layout run; those stay manual.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | d844a56e-2a16-4e27-9dc0-0bf156839bd8 | 0 | 5 | success |
| s2 | d844a56e-2a16-4e27-9dc0-0bf156839bd8 | 0 | 17 | success |
| s3 | 574434b4-5f11-4d71-8408-660a74e0709b | 0 | 3 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s3: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a absent-both, ledger-b absent-both, binding absent-both, ledger-roots absent-both, checkpoint-log absent-both
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 2834/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s2 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s3 574434b4-5f11-4d71-8408-660a74e0709b (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.057078 and 5 turns, s2 cost 0.15339049999999999 and 17 turns, s3 cost 0.0486762 and 3 turns (source: usage.txt)
Reviewer verdict: PENDING
