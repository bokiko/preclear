# Row 10 rerun: large status, hostile filenames, non-Latin text, corrected allowlist (1P + 1R)

Same fixture as the first pass; the allowlist now matches the skill's exact
`git --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none`
and `pwd -P`. No status command was refused (`s2-preclear-full-trace.md`).

Result: **PASS with explicit format and measurement exceptions (Codex).** The non-NUL form of the prescribed command ran for capture and twice more for verification. Sidecar
`status.txt` (6,097 bytes) carries a header naming the command, the capture time and HEAD, and lists
all 128 non-preclear entries in git's quoted porcelain form, including the newline-, quote- and
tab-named files and the Japanese and Arabic names; the model's own two artifacts are excluded and said
so. Honest exception: the `-z` NUL-separated form was not written because the shell redirect needed
approval under the tool policy, so the quoted form was used and declared in the sidecar header, the
Evidence section and the reply. Inline counts (staged 0, unstaged 1, untracked 128) match the harness
(130 minus the two artifacts). Checkpoint 3,273 bytes, every section under cap (true claim); the
required-reads allocation exception is disclosed and the unmeasured freshness output is `UNCONFIRMED`.
Package: the reply's "about 5,396 of 6,000" excludes the unmeasured freshness output and the resume line, so it is an estimate, not a verified complete-package total; required reads (2,123) exceed their 1,392 allocation, disclosed. Fresh resume: HEAD and digests verified, the plan edit recognised as the user's own, chat-only diff,
zero Write/Edit calls, no file changed.

Manifest limit: the harness snapshot in this rerun still used a newline-splitting pipeline, so `sha.txt` omits the newline-named file; the zero-write trace and the model's exact status-body comparison are the preservation evidence for that file. Later runs use `-print0`.
