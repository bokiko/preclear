# Row 9: linked worktree beside the main checkout (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The repository sits in a sibling folder, `main-checkout`, with the plain files committed on main; the project is a linked worktree of it on the branch `feature/widget-export`, so the project's `.git` is a file that points into the main checkout. The session runs in the worktree. The harness leaves the main checkout's git metadata out of its snapshots and keeps every other file of the main checkout under watch, so the row speaks to content preservation of the main checkout and not to the absence of every git metadata access. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 0f773444-f253-44e9-a657-a3258c7dc681 | 0 | 5 | success |
| s2 | 0f773444-f253-44e9-a657-a3258c7dc681 | 0 | 17 | success |
| s3 | 06b1db40-8814-4692-9c33-b9c012b68373 | 0 | 5 | success |

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
- [ ] checkpoint bytes versus cap: 2751/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 0f773444-f253-44e9-a657-a3258c7dc681, s2 0f773444-f253-44e9-a657-a3258c7dc681, s3 06b1db40-8814-4692-9c33-b9c012b68373 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.04975439999999999 and 5 turns, s2 cost 0.155224 and 17 turns, s3 cost 0.0598445 and 5 turns (source: usage.txt)
Reviewer verdict: PENDING
