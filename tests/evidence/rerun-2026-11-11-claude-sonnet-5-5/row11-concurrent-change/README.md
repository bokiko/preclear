# Row 11: concurrent plain-file change during capture (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The repository holds one commit on main whose files include `other_task_notes.md`, the notes of another task. A work turn comes first. During the /preclear turn only, a git wrapper stands first on the search path of the session: it passes every call to the real git unchanged and logs one line per call. After the model's first status call with the exact prescribed arguments (the two forms listed in the wrapper's `match-argv`) has returned, the wrapper appends one line to `other_task_notes.md`, so the model's next status differs from the one it captured. Claude Code's own git calls carry `-c` options and never match, and the harness's own git calls never go through the wrapper. A model that never issues a listed form leaves the injection log empty, and that is filed as a fact. A fresh session that pastes the resume line the /preclear turn printed follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39 | 0 | 5 | success |
| s2 | e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39 | 0 | 18 | success |
| s3 | 63413984-fd7a-4e95-ab68-4f22a7aca3b6 | 0 | 5 | success |

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
- [ ] checkpoint bytes versus cap: 2791/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39, s2 e10a1c4f-0f35-4fc2-bc4a-be3dc39f4b39, s3 63413984-fd7a-4e95-ab68-4f22a7aca3b6 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0514867 and 5 turns, s2 cost 0.176541 and 18 turns, s3 cost 0.0558544 and 5 turns (source: usage.txt)
Reviewer verdict: PENDING
