# Acceptance tests

Manual checklist. There is no test runner.

## How to run

1. Copy one fixture from `tests/fixtures/` to a scratch folder outside this repo.
2. Start a Claude Code session in the scratch folder with preclear installed.
3. Do a small piece of fake work on the "widget-export" task.
4. Run `/preclear`.
5. Start a fresh session in the same folder and paste the line it printed.

Conflict, collision and denial cases use fixture copies. Never provoke them in a
live session.

## Common checks (all layouts)

- [ ] No git mutation and no deletion.
- [ ] No unauthorized configuration change and no external write.
- [ ] Every file written was read back and matches.
- [ ] Branch, full HEAD and status agree with the checkpoint after all writes.
- [ ] Exactly one concrete next action.
- [ ] Measured bytes reported; package within budget, or an explicit exception.
- [ ] A fresh session reaches the next action without broad rediscovery.
- [ ] Output ends with one fenced single-line block and nothing after it.

## plain-memory

Fixture: `tests/fixtures/plain-memory/`

- [ ] Updates one genuinely durable existing topic file or index entry, using its convention.
- [ ] Updates one authorized plan step.
- [ ] Volatile state appears only in the fallback checkpoint.
- [ ] Creates no hub files.
- [ ] A second run reuses the same task path.
- [ ] Simulated identity collision (copy the checkpoint, change its project path) leaves the original untouched and selects `-2`.

## hub-memory

Fixture: `tests/fixtures/hub-memory/`

- [ ] Updates one relevant topic and its established hub, only if needed.
- [ ] Preserves the index conventions.
- [ ] Creates no duplicate open-thread memory.
- [ ] Checkpoint references the canonical plan and evidence.
- [ ] Fresh session reads only the required excerpts.
- [ ] Fresh session honors the invalidation conditions in Do not redo.

## bound-ledger

Fixture: `tests/fixtures/bound-ledger/`. Needs the author's helper, which is not bundled. Edit the paths in the configuration block first.

- [ ] Confirms the exact configured binding.
- [ ] Updates changed sections only through expected-hash helper operations.
- [ ] `lint` and readback pass.
- [ ] Never edits the ledger directly.
- [ ] A controlled conflict (staged on a fixture copy) is handled without force.
- [ ] An unbound or denied run delivers the authorized fallback and labels synchronization pending.

## Evidence to record

Keep in project-local test evidence, sanitized:

- [ ] File inventory before and after.
- [ ] Commands run and observed results.
- [ ] Measured bytes per artifact and total.
- [ ] What the fresh session actually read.

Do not claim publication readiness until expanded coverage passes.
