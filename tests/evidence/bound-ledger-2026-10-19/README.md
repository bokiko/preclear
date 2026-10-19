# Evidence: bound-ledger layout, 2026-10-19 (first run)

**Codex verdict: FAIL for the layout.** Results kept distinct: backend write path PASS;
`fallback_directory: none` BLOCKED case PASS (as an unbound plus project-mismatch case, since
the reused initial block named the other run's path); fresh-session resume FAIL (unauthorized
bind, four ledger updates, one note, nine file outputs); writable unbound fallback NOT
EXERCISED; conflict recovery NOT EXERCISED. Stage 4 is a bound refresh, not a fallback test.
The stage 3 ledger (`main/snap-3-after-resume/ledger.md`) is failure evidence: it replaced the
single next action with a conditional workflow and kept the old checkpoint id.

Root cause per Codex: the fresh session's bare `show` fails when unbound, so it bound to make
it work, before it had read the ledger's persisted restrictions. Fix applied after this run:
the adapter now persists "Resume is read-only for continuity state: never bind" into the
ledger's Authorization boundaries and Evidence first line, the generic Resume reading last
line now says "no file output, binding, or backend write", and the fixture CLAUDE.md carries a
read-only bootstrap note next to the configuration block. Rerun in `../bound-ledger-2026-10-19-rerun/`.

Isolation per Codex's design: the helper's `CKPT_HOME` pointed at a run-local state folder
(own `ledger-roots.json`, own `bindings/`), fixture ledger and handoff roots under the run
folder, a fixture session id bound by the harness, the helper's `menu` showing only the
fixture ledger, `lint OK` before start. Nothing touched the author's real ledgers or bindings.
Paths sanitized: `<run>`, `<run-none>`, `<helper>`. Snapshots per stage in `main/snap-*/`
with ledger text, binding files, hashes and status.

## main/

| Stage | Result |
| --- | --- |
| 1 work (bound session) | Created `widget_export.py` from the ledger's CSV decision. No ledger change. |
| 2 `/preclear` + correction (bound) | **Backend path correct.** `status`, `show` (hashes), six bodies assembled, serialized block, `validate`, per-section `update` with expected hashes, one `note`, `lint OK`, readback. Ledger changed only through the helper. Decision superseded in the ledger's Decisions section; plan step 2 ticked; no memory write (root supplied but empty). Temp bodies kept in `.preclear/widget-export/` as the reference allows. Resume line points at the ledger. Package 5,740 bytes. |
| 3 fresh unbound resume | **FAIL.** Read the ledger via `show`, saw it was unbound, and **ran `checkpoint bind` itself**, then four `update` calls and a `note`, and wrote nine files under `.preclear/` (proposal file, diff, section bodies). The drafted diff itself was in scope; the binding, ledger writes and file outputs were not. The persisted Resume reading line ("Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output without authorization.") was present in the ledger block and ignored. The skill was never loaded by this session, so its "never bind a session" rule was not in context. |
| 4 `/preclear` in that session | Ran the backend path correctly again (now bound, so preconditions held): validate, six updates, lint OK, status sidecar. Honest exceptions: package 8,936 bytes because the diff under review is required reading; Evidence body 1,005/1,000. **This stage no longer tests the unbound fallback**, because stage 3 had bound the session. |

Bindings after the run: two (the harness-bound session A and the self-bound session B).

## fallback-none/

Separate isolated copy, `fallback_directory: none`, ledger present, session never bound.
`/preclear`: configuration validated, helper `status` reported unbound, preconditions failed,
no backend write, no bind, no checkpoint file, plan step ticked (plan is an owner), full
checkpoint printed in the reply, persistence **BLOCKED**, no resume line. **PASS.** It also
noticed that the harness had reused the other run's initial block, whose Goal named the other
project path; that is a harness artifact, and the detection is correct behaviour.

## Not exercised

- Controlled expected-hash conflict (exit 3). Needs a change between the model's `show` and
  `update`, which cannot be staged in a headless single-turn run.
- Unbound fallback to a real `fallback_directory` path (the `none` variant is covered).
