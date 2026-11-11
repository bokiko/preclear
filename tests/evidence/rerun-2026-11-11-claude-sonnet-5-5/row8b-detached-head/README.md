# Row 8b: detached HEAD (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The repository holds two commits on main, the second adding `NOTES.md`; before the work turn the work tree is switched to the first commit with a detached HEAD, so `NOTES.md` is absent. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 2b542a48-2e28-40e9-962d-4e7679c94bb7 | 0 | 4 | success |
| s2 | 2b542a48-2e28-40e9-962d-4e7679c94bb7 | 0 | 14 | success |
| s3 | 84ef8bc3-5376-43ca-9299-68f58d75b4c8 | 0 | 6 | success |

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
- [ ] checkpoint bytes versus cap: 2571/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 2b542a48-2e28-40e9-962d-4e7679c94bb7, s2 2b542a48-2e28-40e9-962d-4e7679c94bb7, s3 84ef8bc3-5376-43ca-9299-68f58d75b4c8 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.04762999999999999 and 4 turns, s2 cost 0.1426712 and 14 turns, s3 cost 0.08207729999999999 and 6 turns (source: usage.txt)
Reviewer verdict: Detached identity checked: resume verified full HEAD and made no writes; its additional git apply --check attempt was blocked. (see codex-review.md)
