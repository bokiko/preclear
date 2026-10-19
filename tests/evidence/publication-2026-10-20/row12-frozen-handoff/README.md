# Row 12: frozen handoff, external change, resume, refresh (2P + 1R)

Stages: `/preclear` with the correction plus "make a frozen handoff copy" (s2); the harness then appends
a note dated 2026-10-21 to the plan (`snap-2b-after-external-plan-edit`); a fresh session resumes from
the line (s3); that session runs an ordinary `/preclear` refresh (s4).

Result: **PASS with disclosed section exception (Codex).** s2 wrote the mutable checkpoint and `checkpoint-20261019T233549Z-k7q2.md`, 2,900 bytes
each, identical SHA-256, reported in the reply; it also warned that untracked files will not travel
with a push. Disclosed exception: Resume reading 712/600 (the manifest agrees), kept so both copies stay
identical (Codex: unnecessary, since the files could have been shortened before freezing, but honestly disclosed). The s2 trace shows a `cp -n` refused by the tool policy ("cp with flags requires manual approval"); the frozen file was then created by a Write, so no copy was overwritten. s3 detected the plan change ("someone added this line after the checkpoint was written"),
judged it relevant only to the unauthorized step 3, flagged the future date, and drafted the diff
chat-only with zero writes. s4 refreshed the mutable checkpoint (3,163 bytes, all sections under cap,
per-section figures printed and confirmed by the manifest), saved the drafted diff as a sidecar so it
survives `/clear`, left the frozen copy untouched (its hash `5f4fea0d…` is identical in snapshots 2, 2b,
3 and 4), made no new frozen copy, and re-reported the plan note as unconfirmed provenance.
