# Row 9: linked worktree beside the main checkout (1P + 1R)

Setup: `main-checkout/` holds the repository; `project/` is a linked worktree on
`feature/widget-export` created with `git worktree add`. The session runs in the worktree.

Result: **PASS.** Identity names the worktree path with "linked worktree; common git dir
../main-checkout/.git", branch `feature/widget-export`, full HEAD. Checkpoint 2,834 bytes, all sections
under cap, written inside the worktree's `.preclear/`. `main-checkout/` hashes are identical from setup
through the resume (`snap-*/sha.txt`): no sibling writes. Fresh resume verified branch, HEAD and digest,
chat-only diff, zero Write/Edit calls, no file changed.

Codex verdict (consultation 9): **PASS; establishes content preservation of the main checkout, not absence of every git metadata access.**
