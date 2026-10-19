# Row 4a: unknown backend and relative executable (1P)

Setup: `backend: checkpoint-v2` (not a known backend) and `executable: wrapper/checkpoint` (relative).
Session bound to the configured ledger; a working helper exists at the absolute path.

Result: **PASS on behaviour.** Zero helper calls. State 3 recorded with both reasons; plain checkpoint
to the fallback directory; ledger byte-identical; plan and memory updated.

Defect D1: Resume reading 619/600 and a 41-byte title line above the first heading
(`measurements.md`). The reply states only the whole-file size.

Codex verdict: **PASS for invalid-config isolation; FAIL for cap disclosure.** Helper operations:
attempted 0, executed 0. Ledger, registry and binding hashes unchanged. Not rerun: the measurement
regression is covered by the row 3a rerun.
