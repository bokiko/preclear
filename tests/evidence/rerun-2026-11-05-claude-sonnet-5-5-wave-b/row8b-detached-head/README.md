# Row 8b: detached HEAD (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The repository holds two commits on main, the second adding `NOTES.md`; before the work turn the work tree is switched to the first commit with a detached HEAD, so `NOTES.md` is absent. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | a7760e28-08f3-4fc8-87ae-8f7881ad7dc9 | 0 | 4 | success |
| s2 | a7760e28-08f3-4fc8-87ae-8f7881ad7dc9 | 0 | 17 | success |
| s3 | 4135a90f-3635-4647-a2f2-a267e5b45225 | 0 | 6 | success |

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
- [ ] checkpoint bytes versus cap: 2484/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 a7760e28-08f3-4fc8-87ae-8f7881ad7dc9, s2 a7760e28-08f3-4fc8-87ae-8f7881ad7dc9, s3 4135a90f-3635-4647-a2f2-a267e5b45225 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0461112 and 4 turns, s2 cost 0.1521936 and 17 turns, s3 cost 0.053283500000000004 and 6 turns (source: usage.txt)
Reviewer verdict: PENDING
