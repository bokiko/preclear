# Row 2: two real same-section conflicts (1P), rerun on the pinned model and build

Setup: one ledger, ledger A (`CONTINUITY_CLAUDE-widget-export.md`), named by the configuration; the harness bound two sessions to it through the checkpoint stub, the model's session and a second session that stands for another writer. A work turn comes first. After it the harness arms the wrapper with a count of 2: before each of the model's first two `update` calls to one section, the wrapper has the second writer update that same section through the stub, so the stub itself returns exit 3 to the model. The wrapper changes nothing about the model's arguments, hashes or output, and the two second-writer updates are recorded in `wrapper-injection.log`. The /preclear turn follows in the same session; no fresh session follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4 | 0 | 5 | success |
| s2 | 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4 | 0 | 41 | success |

## Mechanical facts

- helper calls in s1: attempted 0, executed 0, denied 0, compound refusals 0
- helper calls in s2: attempted 7, executed 7, denied 0, compound refusals 0
- ledger digests: ledger-a changed, ledger-b absent-both, binding unchanged, ledger-roots unchanged, checkpoint-log changed
- the full list of facts is in mechanical-checks.md and usage.txt

## Reviewer checklist

- [ ] helper calls (all stages): attempted 7, executed 7, denied 0, compound refusals 0 (source: wrapper-calls.log, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] ledger digests unchanged, setup to snap-2-after-preclear: no (source: snap-0-setup/sha.txt, snap-2-after-preclear/sha.txt)
- [ ] writes outside approved roots: 0; snapshot paths 0, tool paths 0, Bash writes 0, default memory folder absent (source: the sha.txt of each snapshot, mechanical-checks.md, s1-work-full-trace.md, s2-preclear-full-trace.md)
- [ ] git mutations: 0; state changes 0, staged entries 0, executed forms 0 (source: status.txt of each snapshot, mechanical-checks.md)
- [ ] checkpoint bytes versus cap: 3002/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4, s2 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.0510427 and 5 turns, s2 cost 0.38997249999999994 and 41 turns (source: usage.txt)
Reviewer verdict: PENDING
