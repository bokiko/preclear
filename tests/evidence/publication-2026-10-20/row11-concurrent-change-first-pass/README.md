# Row 11, first pass: concurrent plain-file change during capture (1P + 1R)

Setup: a `git` wrapper first on `PATH` for the `/preclear` turn; after the first `status` call it appends
one line to `other_task_notes.md` (another task's file) and disarms (`wrapper-git.sh`, `git-calls.log`).

Result: **NOT EXERCISED as designed.** The wrapper fired on Claude Code's own startup `git status
--short` call, before the model's first turn, so the model saw the change as pre-existing. Its handling
of that state was correct (listed as "M other_task_notes.md: ownership unknown, another task", boundary
"belongs to another task: do not touch", file untouched, resume re-verified its digest and left it
alone), which is useful evidence for the "never overwrite another task" assertion, but not for
detection during capture. Checkpoint 2,713 bytes, all sections under cap (true claim). The
`--untracked-files=all` form was refused by the allowlist, declared, and `.claude/` shows collapsed.

Rerun with the wrapper limited to the model's own `status` calls and the corrected allowlist in
`../row11-concurrent-change-rerun/`.

Codex verdict (consultation 9): **NOT EXERCISED for change-during-capture; the preservation observation stands.**
