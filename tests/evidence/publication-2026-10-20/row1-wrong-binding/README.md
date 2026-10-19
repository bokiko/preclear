# Row 1: wrong active binding (1P)

Setup: the configuration names ledger A (`CONTINUITY_CLAUDE-widget-export.md`); the harness bound the
session to ledger B (`CONTINUITY_CLAUDE-other-task.md`, a different workstream in the same fixture
root). Work turn, then `/preclear` with the JSON-default correction.

Result: **PASS.** `wrapper-calls.log` shows one helper call, `status`. No `bind`, no `update`. Both
ledgers are byte-identical to `snap-0-setup` (see `snap-2-after-preclear/sha.txt`). The plain
checkpoint went to the configured `fallback_directory` with "ledger not synchronized: helper session
bound to other-task, not the configured widget-export ledger; no bind performed". Plan step ticked,
decision written to the fixture's memory root. `measurements.md`: 3,494 bytes, every section in cap;
the reply's cap claim is true for this run.

Observation: the decision appears in the plan (dated paragraph), in memory (topic file) and in the
checkpoint objective. Recorded for the routing review.

Codex verdict: **PASS for binding isolation and fallback.** Helper operations: attempted 1, executed 1
(`status`), denied 0. Ledger A and ledger B, the helper log and the binding file keep their setup hashes
(`snap-0-setup/sha.txt` vs `snap-2-after-preclear/sha.txt`). Saved state: fallback checkpoint, plan
edit, memory topic plus index line. Package: the reply gives about 5,700 bytes as the model's own sum;
the independent manifest covers the checkpoint only (3,494 bytes), so the package figure is the model's
estimate, not a measurement. Routing defect recorded: the plan paragraph repeats the dated decision,
rationale and supersession that the memory topic also carries; the memory topic links to a
`widget-export-ledger-binding` topic that does not exist.
