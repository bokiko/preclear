# Layout plain-memory: flat memory index kept inside the project (1P + 1R), rerun on the pinned model and build

Setup: the frozen plain-memory fixture project copied in place: its instruction file, `PLAN.md` and a flat `MEMORY.md` index with one topic file. The auto-memory directory is pinned to the `memory` folder inside the project, so a memory write lands in the project, which is an approved root and is under watch in every snapshot. No helper wrapper, no ledger and no binding. A work turn comes first, then the /preclear turn with the JSON-default correction in the same session, then a fresh session that pastes the resume line the /preclear turn printed. The work-turn prompt is new text written for this harness, so this run is a new baseline and not a replication of the committed layout run. The harness prints counts, names and digests of the project and memory files. The harness does not exercise the identity collision, blocked instruction, freshness edit, tamper or repeat /preclear checks of the committed layout run; those stay manual.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 9324af7b-da8d-4a06-80a0-ad439c1109bd | 0 | 5 | success |
| s2 | 9324af7b-da8d-4a06-80a0-ad439c1109bd | 0 | 11 | success |
| s3 | 3c77c0dc-d3df-4f68-bf56-c341673190e7 | 0 | 3 | success |

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
- [ ] checkpoint bytes versus cap: 2618/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 9324af7b-da8d-4a06-80a0-ad439c1109bd, s2 9324af7b-da8d-4a06-80a0-ad439c1109bd, s3 3c77c0dc-d3df-4f68-bf56-c341673190e7 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0527334 and 5 turns, s2 cost 0.12074100000000001 and 11 turns, s3 cost 0.046545100000000006 and 3 turns (source: usage.txt)
Reviewer verdict: PENDING
