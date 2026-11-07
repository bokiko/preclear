# Layout bound-ledger: one ledger bound to the session (1P + 1R), rerun on the pinned model and build

Setup: the row 1 setup with ledger A only: the configuration names ledger A (`CONTINUITY_CLAUDE-widget-export.md`) and the harness bound the session to it through the checkpoint stub; there is no ledger B. The auto-memory directory is pinned inside the run root as in row 1. A work turn comes first with the row 1 work-turn prompt, then the /preclear turn with the JSON-default correction in the same session, then a fresh session that pastes the resume line the /preclear turn printed. After the /preclear turn the harness runs the stub's lint directly and files its text. The harness prints whether the ledger digest changed, the number of executed `update` calls in the wrapper log and the lint text. The harness does not exercise the identity collision, blocked instruction, freshness edit, tamper or repeat /preclear checks of the committed layout run; those stay manual.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 896198d6-f642-49bc-953b-64608d694c26 | 0 | 5 | success |
| s2 | 896198d6-f642-49bc-953b-64608d694c26 | 0 | 38 | success |
| s3 | b9f578e0-6e3c-430b-84cd-239453036040 | 0 | 6 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 15, executed 14, denied 0, compound refusals 1
- helper calls in s3: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a changed, ledger-b absent-both, binding unchanged, ledger-roots unchanged, checkpoint-log changed
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 15, executed 14, denied 0, compound refusals 1 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-3-after-resume: no (source: snap-0-setup/sha.txt, snap-3-after-resume/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md, s3-resume-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
- [ ] session ids per stage: s1 896198d6-f642-49bc-953b-64608d694c26, s2 896198d6-f642-49bc-953b-64608d694c26, s3 b9f578e0-6e3c-430b-84cd-239453036040 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.05176410000000001 and 5 turns, s2 cost 0.3429076999999999 and 38 turns, s3 cost 0.056726900000000004 and 6 turns (source: usage.txt)
Reviewer verdict: PENDING
