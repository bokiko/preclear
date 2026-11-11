# Row 4a: unknown backend and relative executable (1P), rerun on the pinned model and build

Setup: the configuration names `backend: checkpoint-v2`, which is not a known backend, and `executable: wrapper/checkpoint`, a relative path. The session is bound to the one ledger the row seeds (`CONTINUITY_CLAUDE-widget-export.md`), and a working helper wrapper exists at an absolute path in the run root. A work turn comes first, then the /preclear turn with the JSON-default correction in the same session; no fresh session follows.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | 3f99f947-f802-49e5-8095-81f4a4cfe813 | 0 | 5 | success |
| s2 | 3f99f947-f802-49e5-8095-81f4a4cfe813 | 0 | 16 | success |

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
- [ ] checkpoint bytes versus cap: 2834/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 3f99f947-f802-49e5-8095-81f4a4cfe813, s2 3f99f947-f802-49e5-8095-81f4a4cfe813 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.05551120000000001 and 5 turns, s2 cost 0.1725806 and 16 turns (source: usage.txt)
Reviewer verdict: Backend rejected: no helper ran; authorized plain fallback preserved the pending correction. (see codex-review.md)
