# Row 10: large status, hostile file names, non-Latin text (1P + 1R), rerun on the pinned model and build

Setup: a plain project with memory enabled and pinned inside the run root, no helper wrapper and no ledger. The repository holds one commit on main and then 124 untracked files that make a large status listing hard to read: 90 sample files in a folder whose name holds a space, two folders with Japanese and Arabic names holding 15 files each, files whose names hold a newline, two double quotes and a tab, or two leading spaces, and a notes file with Japanese and Arabic text. The allowlist is the 33-rule baseline alone: it holds no rule for the NUL form of the status command, for a redirection or for a status file. A work turn comes first, then the /preclear turn in the same session, then a fresh session that pastes the resume line the /preclear turn printed. The harness reads the status form from the stream afterwards and counts it; it does not say which form was right.

## Stages

| Stage | Session | Exit | Turns | Subtype |
| --- | --- | --- | --- | --- |
| s1 | c0c41f70-a354-47e5-9121-50a72f7df366 | 0 | 5 | success |
| s2 | c0c41f70-a354-47e5-9121-50a72f7df366 | 0 | 28 | success |
| s3 | 2b31dcdc-2f9e-4667-86c2-07626608c534 | 0 | 6 | success |

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
- [ ] checkpoint bytes versus cap: 2793/4096 (source: measurements.txt)
- [ ] session ids per stage: s1 c0c41f70-a354-47e5-9121-50a72f7df366, s2 c0c41f70-a354-47e5-9121-50a72f7df366, s3 2b31dcdc-2f9e-4667-86c2-07626608c534 (source: session.id, session-resume.id, usage.txt)
- [ ] cost and turns per stage: s1 cost 0.054798 and 5 turns, s2 cost 0.3109138 and 28 turns, s3 cost 0.0535457 and 6 turns (source: usage.txt)
- [ ] expected outcome, quoted-porcelain fallback and NUL redirect refused: quoted form executed 3, NUL form executed with a redirection 0, NUL form denied with a redirection 2, NUL form executed without a redirection 1, sidecar status.txt present, 6305 bytes, 0 NUL bytes (source: mechanical-checks.md Row 10 status form, the /preclear full trace, snap-2-after-preclear/preclear)
Reviewer verdict: PENDING
