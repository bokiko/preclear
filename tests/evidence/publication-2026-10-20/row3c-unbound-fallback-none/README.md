# Row 3c: unbound session, `fallback_directory: none`, correct project identity (1P)

Setup: ledger block names this fixture's project path and task; the session was never bound;
`fallback_directory: none`.

Result: **PASS.** One helper call, `status` (unbound). No bind. No file written anywhere in the project
(`snap-2-after-preclear` has no `.preclear`). Persistence BLOCKED, no resume line, the full checkpoint
printed in the reply with the recovery options (bind as a separate setup action, or allow a fallback
directory). Plan step ticked and decision written to the fixture's memory root. This closes the gap
from the first bound-ledger run, where the BLOCKED case had a project-path mismatch as a harness artifact.

Codex verdict: **PASS.** Helper operations: attempted 2 (`status` twice; the first sat inside a compound command that the
permission layer refused as a whole, so nothing ran), executed 1 (`wrapper-calls.log`), helper
mutations attempted 0. No checkpoint file and no resume line; authorized plan and memory
updates did occur, so this is "no fallback file", not "nothing written". Ledger hash unchanged; no
bindings folder exists in the helper state after the run.
