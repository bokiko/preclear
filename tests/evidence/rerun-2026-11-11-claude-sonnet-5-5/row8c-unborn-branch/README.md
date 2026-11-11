# Row 8c: unborn branch (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The project is a repository on main with no commit yet (an unborn branch), so every file is untracked. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 52fa3032-6149-423a-a0d5-7ff597f1d0bb | 0 | 4 | success |
| s2 | 52fa3032-6149-423a-a0d5-7ff597f1d0bb | 0 | 17 | success |
| s3 | e1128fe7-d1f5-404b-898c-82c554cf24ba | 0 | 8 | success |

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
- [ ] checkpoint bytes versus cap: 2679/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 52fa3032-6149-423a-a0d5-7ff597f1d0bb, s2 52fa3032-6149-423a-a0d5-7ff597f1d0bb, s3 e1128fe7-d1f5-404b-898c-82c554cf24ba (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0467351 and 4 turns, s2 cost 0.15344609999999997 and 17 turns, s3 cost 0.055925300000000004 and 8 turns (source: usage.txt)
Reviewer verdict: Unborn continuation observed: resume confirmed absent HEAD and matching digests; the canonical plan’s CSV-first decision remained stale. (see codex-review.md)
