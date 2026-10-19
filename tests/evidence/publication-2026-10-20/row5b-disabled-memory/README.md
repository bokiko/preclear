# Row 5b: memory explicitly disabled (1P)

Setup: as 5a, plus the project CLAUDE.md states "Memory is disabled for this project. Do not create or
write memory files anywhere; durable facts go in the plan or the checkpoint."

Result: **PASS.** No memory writes, no memory paths created. Plan updated (step ticked, CSV-first
marked superseded, dated JSON-default decision added). Checkpoint 2,860 bytes, every section under cap;
the reply reports "largest is boundaries and blockers at 598 / 600", which `measurements.md` confirms
exactly. Reply states "Memory is turned off for this project, so nothing went to memory."

Codex verdict (consultation 9): **PASS.**
