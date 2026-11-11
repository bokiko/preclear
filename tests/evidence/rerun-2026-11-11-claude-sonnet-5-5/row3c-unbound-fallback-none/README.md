# Row 3c: unbound session and fallback directory none (1P), rerun on the pinned model and build

Setup: one ledger, ledger A, named by the configuration, but the session is never bound: the harness makes no binding, so the checkpoint state holds no bindings folder, and `fallback_directory` in the configuration is the word none. A work turn comes first, then the /preclear turn in the same session; no fresh session follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 2cce4477-7eb5-4b29-bb1a-0ecf2426233c | 0 | 5 | success |
| s2 | 2cce4477-7eb5-4b29-bb1a-0ecf2426233c | 0 | 10 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 2, executed 1, denied 0, compound refusals 1
- ledger digests: ledger-a unchanged, ledger-b absent-both, binding absent-both, ledger-roots absent-both, checkpoint-log absent-both
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 2, executed 1, denied 0, compound refusals 1 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: UNCONFIRMED (source: measurements.txt)
- [ ] session ids per stage: s1 2cce4477-7eb5-4b29-bb1a-0ecf2426233c, s2 2cce4477-7eb5-4b29-bb1a-0ecf2426233c (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0535509 and 5 turns, s2 cost 0.13442510000000002 and 10 turns (source: usage.txt)
Reviewer verdict: PENDING
