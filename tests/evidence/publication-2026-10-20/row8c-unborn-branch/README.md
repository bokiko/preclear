# Row 8c: unborn branch (1P + 1R)

Setup: `git init -b main` with no commit; everything untracked.

Result: **PASS.** Identity records `branch: main, unborn; HEAD: n/a`; resume line `unborn @ n/a`.
Checkpoint 2,775 bytes, every section under cap, true claim ("Resume reading is 599 of 600" matches the
manifest exactly); required-reads exception disclosed. Fresh resume: "the branch is unborn", digests and
untracked count re-verified, chat-only diff, zero Write/Edit calls, no file changed.

Codex verdict (consultation 9): **PASS with disclosed package-allocation exception.**
