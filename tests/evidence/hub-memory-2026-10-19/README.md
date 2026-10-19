# Evidence: hub-memory layout, 2026-10-19 (first run)

**Status: routing accepted, continuation FAILED.** Codex passed every hub-specific check
(topic corrected in place, hub line refreshed, index untouched, no duplicates, unrelated
topic never read, checkpoint bytes preserved, invalidation detected). It failed the run on
fresh-session behaviour: stage 3 twice attempted `rm -rf` on a fixed `/tmp` scratch path
(denied by the harness, nothing deleted) instead of using the authorized chat output, and
stage 4 wrote a new proposal sidecar although its next action was only to ask. The skill
now persists write roots, scratch limits, and the no-deletion rule into the checkpoint's
Boundaries and Resume reading; the rerun is in `../hub-memory-2026-10-19-rerun/`.

Accounting correction: the stage 2 reply measured the decision topic at 561 bytes; the
manifest measures 728 after Claude Code's runtime metadata was added. Package after stage 2
is 3,603 + 248 + 2,451 = 6,302 bytes before freshness output. Over target, reported as such.
Both saved diffs are unverified drafts; their blank context lines lack the leading space.

Run per Codex's outline: ordinary work and `/preclear` in one conversation (the correction
arrives in the `/preclear` turn), a fresh conversation for the resume, a repeat `/preclear`
in that conversation, then an in-place invalidation (a newer owner update appended to the
already-dirty decision topic) followed by a third fresh conversation. Isolated copy of
`tests/fixtures/hub-memory/`, `--setting-sources project,local`, per-run `--settings` pinning
`autoMemoryDirectory` to the copy. Paths sanitized to `<scratch>`; `measurements.md` has
original-file bytes and hashes. Snapshots per stage are in `snap-*/` (hashes and status).

| Stage | Result |
| --- | --- |
| 1 work | Created `widget_export/csv_exporter.py` and `__init__.py` with small pure functions. No memory or plan change. Noted that no column list exists and assumed three columns. |
| 2 `/preclear` + correction | Decision topic rewritten in place to JSON-default with reason and supersession; `hub_projects.md` line refreshed; `MEMORY.md` byte-identical; unrelated reference untouched and unread; plan step 2 ticked; no duplicate topic or note. Checkpoint 3,603 bytes, all sections in cap. Next action: draft the JSON-default diff for review. Package 6,400 bytes, reported as an exception because two exporter files are required reads. |
| 3 fresh resume | Read checkpoint, plan, decision topic, two exporter files. Did not read the unrelated reference. Verified branch, HEAD, digests. Tried to build the diff in `/tmp`, denied by the harness allowlist, then presented the diff in chat without applying anything. Checkpoint byte-identical. |
| 5 repeat `/preclear` | Same path reused. No memory, hub, or plan rewrite. Saved the drafted diff as a sidecar `proposed-json-default.diff` because it was the session's only non-recoverable output. Package 7,450 bytes, reported as an exception. Noted `git apply --check` was denied so the diff is unverified. |
| 4 invalidation | Fresh conversation found the newer owner update (newline-delimited JSON) in the decision topic, declared the drafted diff out of date, left the original sidecar untouched, wrote a second sidecar for the new format, left the checkpoint byte-identical, and asked the user to choose. Did not trust Do not redo over the changed decision. |

## Hub-specific checks

- [x] Relevant topic corrected in place with conventions kept.
- [x] Hub description refreshed only because it was stale; unrelated-reference entry preserved.
- [x] `MEMORY.md` stayed hub-only and byte-identical.
- [x] No duplicate decision topic, task-rule memory, or open-thread note.
- [x] Plan marks only completed work complete and records nothing twice.
- [x] Implementation unchanged during `/preclear`; no tests, no commits.
- [x] One authorized next action (draft the diff for review).
- [x] Unrelated topic never read in any stage.
- [x] Fresh sessions left the checkpoint byte-identical.
- [x] Invalidation: changed decision reconciled before proposing implementation.
- [x] Isolation: zero memory files in the author's auto-memory tree for this path.

## Open questions for review

1. Stage 3 attempted a write to `/tmp` for scratch work. Denied by the harness, but it is a
   write attempt outside the project by the fresh session, not by preclear.
2. Stage 4's fresh session wrote a new sidecar inside `.preclear/` without `/preclear` being
   invoked. The checkpoint itself was untouched. Is a fresh session allowed to add
   preclear-owned sidecars?
3. Stage 5 saved the chat-drafted diff as a sidecar and counted it as required reading,
   pushing the package to 7,450 bytes. Reported honestly as an exception.
