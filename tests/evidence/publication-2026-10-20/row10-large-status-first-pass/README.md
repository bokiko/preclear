# Row 10, first pass: large status with hostile filenames and non-Latin text (1P + 1R)

Setup: 128 untracked non-preclear entries including names with spaces, a leading space, a newline, a
double quote and a tab, Japanese and Arabic directory and file names, and non-Latin file content.

Result: **PASS on accounting and honesty, NOT a test of the prescribed command.** The harness allowlist
only matched `git status …`, so the skill's exact `git --no-optional-locks status --porcelain=v1 -z …`
form was refused ("requires approval", see the full trace). The model declared the exception in the
sidecar header, built a grouped inventory by hand from the plain porcelain output (128 non-preclear
untracked entries, matching the harness count of 130 minus its own two artifacts), listed the newline,
quote and tab names escaped, excluded its own artifacts, and counted them inline. Checkpoint 2,675 bytes,
all sections under cap (true claim). Fresh resume verified HEAD and digests, chat-only diff, zero writes.

Harness defect: the same allowlist gap applied to every earlier run (the prescribed status command had
never executed). Rerun with the corrected allowlist in `../row10-large-status-rerun/`. The harness
snapshot `sha.txt` misses the newline-named file because its own pipeline split on newlines; the
model's inventory does list it.

Codex verdict (consultation 9): **useful accounting and fallback evidence, not evidence that the prescribed command executed.**
