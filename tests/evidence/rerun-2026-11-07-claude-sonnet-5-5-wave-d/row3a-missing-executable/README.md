# Row 3a: missing executable (1P), rerun on the pinned model and build

Setup: one ledger, ledger A, named by the configuration, with the session bound to it through the checkpoint stub. The configuration's `executable` names `wrapper/missing-checkpoint`, a file that does not exist; the working wrapper stands beside it as `wrapper/checkpoint`. A work turn comes first, then the /preclear turn in the same session; no fresh session follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 417ecf26-580e-4a49-bdb0-e3d763f0c357 | 0 | 5 | success |
| s2 | 417ecf26-580e-4a49-bdb0-e3d763f0c357 | 0 | 21 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a unchanged, ledger-b absent-both, binding unchanged, ledger-roots unchanged, checkpoint-log unchanged
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 2668/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 417ecf26-580e-4a49-bdb0-e3d763f0c357, s2 417ecf26-580e-4a49-bdb0-e3d763f0c357 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.05397550000000001 and 5 turns, s2 cost 0.14811020000000003 and 21 turns (source: usage.txt)
Reviewer verdict: PENDING
