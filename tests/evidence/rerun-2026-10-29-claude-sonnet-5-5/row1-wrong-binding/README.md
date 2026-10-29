# Row 1: wrong active binding (1P), rerun on the pinned model and build

Setup: the configuration names ledger A (`CONTINUITY_CLAUDE-widget-export.md`); the harness bound the session to ledger B (`CONTINUITY_CLAUDE-other-task.md`, a different workstream in the same fixture root). A work turn comes first, then the /preclear turn with the JSON-default correction in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | e125001c-ff38-49aa-a88c-5d19975cfbc5 | 0 | 5 | success |
| s2 | e125001c-ff38-49aa-a88c-5d19975cfbc5 | 0 | 20 | success |
| s3 | b7eb866d-54f5-46f0-9a7a-97a484230f77 | 0 | 6 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 4, executed 1, denied 0, compound refusals 3
- helper calls in s3: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a unchanged, ledger-b unchanged, binding unchanged, ledger-roots unchanged, checkpoint-log unchanged
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 4, executed 1, denied 0, compound refusals 3 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-3-after-resume: yes (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, default memory folder absent (source: the sha.txt of each snapshot, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 2623/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 e125001c-ff38-49aa-a88c-5d19975cfbc5, s2 e125001c-ff38-49aa-a88c-5d19975cfbc5, s3 b7eb866d-54f5-46f0-9a7a-97a484230f77 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.048710500000000004 and 5 turns, s2 cost 0.15843250000000003 and 20 turns, s3 cost 0.0651687 and 6 turns (source: usage.txt)
Reviewer verdict: PENDING
