# Row 5a: no memory system (1P), rerun on the pinned model and build

Setup: a plain project with no configuration block and no memory mentioned anywhere in it, no helper wrapper and no ledger. Claude Code auto-memory is switched off in the run settings, with its directory still pinned inside the run root so that a stray write would land there. A work turn comes first, then the /preclear turn with the JSON-default correction in the same session; no fresh session follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc | 0 | 4 | success |
| s2 | 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc | 0 | 10 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 0, executed 0, denied 0, compound refusals 0
- ledger digests: ledger-a absent-both, ledger-b absent-both, binding absent-both, ledger-roots absent-both, checkpoint-log absent-both
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 0, executed 0, denied 0, compound refusals 0 (source: s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-2-after-preclear: yes (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 2476/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc, s2 0c62d8cd-635d-4c80-8aae-4a2d7545a9bc (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0447066 and 4 turns, s2 cost 0.1205753 and 10 turns (source: usage.txt)
Reviewer verdict: PENDING
