# Row 8a: non-git project (1P + 1R)

Setup: plain project with no `.git`. Because the run roots live under the preclear repository's
gitignored `runs/` folder, an enclosing repository exists two levels up; that makes the case stricter
than an empty filesystem.

Result: **PASS.** The model recognised the enclosing repository as a parent, not this project, and
recorded `branch: no-git`, `HEAD: n/a` with the file digests that replace git identity. Checkpoint 2,734
bytes, every section under cap, true cap claim. Resume line uses the `no-git @ n/a` form. Fresh resume:
verified both digests, "There's no git here, so there is no HEAD to compare", drafted the diff in the
reply, zero Write/Edit calls, no file changed (`snap-2` and `snap-3` hashes identical). `pwd -P` was
refused by the tool policy and the physical path is marked `UNCONFIRMED`, the honest form.

Codex verdict (consultation 9): **PASS.**
