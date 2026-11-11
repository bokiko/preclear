## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261111T065839Z
project: <run>/project (not a linked worktree)
task: widget-export
objective: export widgets (id, name); JSON now default, CSV opt-in
result: plan step 2 done (CSV exporter in src/widget-export.js, tests not run); step 3 not started; JSON-default not implemented
branch: main
HEAD: 8fba1dbb6a054967980dc29b8e7fd02c638c5828
untracked-notice: sent (.preclear/ is untracked)

## Boundaries and blockers
Scope: draft only. Do not apply the JSON diff, edit src/, run tests, commit, or start step 3. No deletions, no git mutation.
Pending: user review of the drafted JSON-default diff.
Decision 2026-11-11: JSON default, CSV only on explicit request (consumer moved to JSON API week of 2026-10-12); supersedes CSV-first.
UNCONFIRMED: JSON shape (array of {id,name}?) and how CSV is requested (option vs separate function).
Detail: memory widget-export-json-default; plan decision lines.

## Next action
In the project dir, draft a proposed unified diff for src/widget-export.js making JSON the default export and CSV opt-in, with small pure functions. Show it in the reply for review without applying it. Done when the diff is shown and src/ is unchanged.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
1. thoughts/plans/2026-10-15-widget-export.md (whole)
2. src/widget-export.js (whole)
3. Memory widget-export-json-default.md only if the reason is needed.
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: staged 0, unstaged 1 (plan, ticked step 2 + 2026-11-11 decision line), untracked 5 (src/widget-export.js from this task; 4 under .claude/skills/preclear/ ownership unknown), conflicted 0, submodules 0.
Preclear artifacts: .preclear/widget-export/checkpoint.md
Digests (sha256): src/widget-export.js a0ac64e795642878175ce2aed2eb629e57ecc9932fab7e650aed073a1a8636ed; plan c83247bc0e39d65e8a17f377ddf4b9f9a6b610a0880579f18174ff8ab74cb1f6
Verification: none run; no tests, by instruction. Test binding UNCONFIRMED.
No sidecar needed.

## Do not redo
Git state and digests above were checked 2026-11-11 at HEAD 8fba1db; invalid if HEAD or digests differ.
Preclear config: no block in CLAUDE.md, so plain file. Invalid if CLAUDE.md gains a block.
