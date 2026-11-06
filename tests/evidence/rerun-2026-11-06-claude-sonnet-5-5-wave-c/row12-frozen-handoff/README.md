# Row 12: frozen handoff, external plan change, resume and refresh (2P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. A work turn comes first. The /preclear turn that follows, in the same session, also asks for a frozen handoff copy of the checkpoint. After it the harness appends one note line, from another session, to the plan file and takes an extra snapshot (`snap-2b-after-external-plan-edit`); a fresh session then resumes from the line the /preclear turn printed, and the fourth stage resumes that fresh session with an ordinary /preclear refresh, so the frozen copy is still in the project when the refresh runs.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 97409728-53cc-41b5-a034-1a474f27d749 | 0 | 4 | success |
| s2 | 97409728-53cc-41b5-a034-1a474f27d749 | 0 | 22 | success |
| s3 | ef29f812-70fc-4e44-a3fd-0b2b1803b8fe | 0 | 5 | success |
| s4 | ef29f812-70fc-4e44-a3fd-0b2b1803b8fe | 0 | 12 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s3: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s4: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a absent-both, ledger-b absent-both, binding absent-both, ledger-roots absent-both, checkpoint-log absent-both
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md, s4-preclear-refresh-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-4-after-refresh: yes (source: snap-0-setup/sha.txt, snap-4-after-refresh/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md, s4-preclear-refresh-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 3273/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 97409728-53cc-41b5-a034-1a474f27d749, s2 97409728-53cc-41b5-a034-1a474f27d749, s3 ef29f812-70fc-4e44-a3fd-0b2b1803b8fe, s4 ef29f812-70fc-4e44-a3fd-0b2b1803b8fe (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.045649 and 4 turns, s2 cost 0.21729389999999998 and 22 turns, s3 cost 0.05670410000000001 and 5 turns, s4 cost 0.15453319999999998 and 12 turns (source: usage.txt)
Reviewer verdict: PENDING
