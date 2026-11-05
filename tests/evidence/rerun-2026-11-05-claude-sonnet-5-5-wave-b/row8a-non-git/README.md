# Row 8a: non-git project (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger, and no git repository at all: the project folder holds no `.git` entry, and the run root lies under no repository either, which differs from the committed run (that one sat inside an enclosing repository two levels up). A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed. The harness reads the git state of this project as not applicable and starts no git process for it.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 1ea9ce21-32b3-4b17-9281-74c935e29558 | 0 | 4 | success |
| s2 | 1ea9ce21-32b3-4b17-9281-74c935e29558 | 0 | 16 | success |
| s3 | 6bb00788-f6a8-4374-bebb-2ca9c4b130a4 | 0 | 10 | success |

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
- [ ] checkpoint bytes versus cap: 2706/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 1ea9ce21-32b3-4b17-9281-74c935e29558, s2 1ea9ce21-32b3-4b17-9281-74c935e29558, s3 6bb00788-f6a8-4374-bebb-2ca9c4b130a4 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0440391 and 4 turns, s2 cost 0.11863420000000001 and 16 turns, s3 cost 0.0824424 and 10 turns (source: usage.txt)
Reviewer verdict: PENDING
