# Row 8c: unborn branch (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The project is a repository on main with no commit yet (an unborn branch), so every file is untracked. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 8ac348b9-b892-490c-93ef-d82272b34135 | 0 | 5 | success |
| s2 | 8ac348b9-b892-490c-93ef-d82272b34135 | 0 | 15 | success |
| s3 | 0213c7f8-7b63-4983-87d6-7ba9bbccb7b8 | 0 | 7 | success |

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
- [ ] checkpoint bytes versus cap: 2643/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 8ac348b9-b892-490c-93ef-d82272b34135, s2 8ac348b9-b892-490c-93ef-d82272b34135, s3 0213c7f8-7b63-4983-87d6-7ba9bbccb7b8 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0500394 and 5 turns, s2 cost 0.1428374 and 15 turns, s3 cost 0.0607904 and 7 turns (source: usage.txt)
Reviewer verdict: PENDING
