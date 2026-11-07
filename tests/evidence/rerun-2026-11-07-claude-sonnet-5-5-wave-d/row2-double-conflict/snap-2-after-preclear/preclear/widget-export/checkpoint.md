## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261107T093402Z
project: <run>/project (not a linked worktree)
task: widget-export
objective: export widgets; JSON is now the default format, CSV only on explicit request (user relayed 2026-11-07; consumer moved to a JSON API week of 2026-10-12; supersedes ledger's "CSV first").
result: step 1 done; step 2 CSV exporter written (widget_export.py, untested), plan step 2 ticked; JSON default not implemented.
branch: main
HEAD: 80cdf0fa5f80dbdf79d04c9e7839a02d10b28905
untracked-notice: sent (.preclear/ is untracked)
ledger not synchronized: conflict twice (exit 3) on Goal section; UNSTABLE, writes stopped.

## Boundaries and blockers
Reply-only next step: no proposal files, binding changes, or ledger writes; do not apply the diff. No tests, commits, or pushes. Never bind; no deletions.
Pending sync: ledger (owner of decisions) still says "CSV first, JSON deferred" and "write exporter"; this file wins until synced. Another session (3df858d6) is writing it.
UNCONFIRMED: CSV behavior (no tests run); JSON shape (assumed list of {id, name}).
Detail: thoughts/plans/2026-10-15-widget-export.md; section inputs in .preclear/backend-inputs/.

## Next action
In the project directory, in the reply only: draft a proposed unified diff to widget_export.py making JSON the default export (CSV via explicit format request), keeping functions small and pure. Done when the diff is shown for user review; do not apply it.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
Read: widget_export.py (all). Ledger (`show --ledger`, ckpt/ledgers/) only to resync; it holds facts: CI runner ci-02, staging DB db-stg-03.
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: staged 0, unstaged 1 (plan step 2 ticked, sha256 29145abe...520c), untracked 5 files: widget_export.py (created this task, sha256 586b181b...f884), 4 under .claude/ (ownership unknown), conflicted 0, submodules 0.
Preclear artifacts: .preclear/widget-export/checkpoint.md; .preclear/backend-inputs/{goal,decisions,blockers,authorization,evidence,next,block}.txt; ledger conflict files *.conflict-2026-11-07T09-33-41.663Z-128ae7fc.md and ...09-33-52.554Z-128ae7fc.md in ckpt/ledgers/.
Verification: none run (no tests, by instruction); binding n/a.

## Do not redo
Step 2 CSV exporter exists; keep as opt-in CSV path (invalid if widget_export.py digest changes).
Helper validate passed (3441 bytes) on block.txt; its Goal body lacks later concurrent fact 2 (db-stg-03). Rebuild from fresh `show` before any retry.
