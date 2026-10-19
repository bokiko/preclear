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

## Harness rules

- Record the Claude Code version, the enabled setting sources, the installed
  skill path and its content digest before invoking. For a project-skill test
  use `--setting-sources project,local` so a personal skill of the same name
  cannot shadow it, and confirm from the transcript which skill text loaded.
- Fail the test on any write outside the fixture copy or the evidence folder.
  Never bind a real session or touch real ledger roots.
- Freeze each stage before the next one runs: copy the checkpoint tree after
  `/preclear`, after the fresh session acts, after the repeat run, and after the
  collision run. Evidence files are named by the stage that produced them.
- Measure total and per-section UTF-8 bytes on the original files before
  sanitizing paths, and keep that manifest. A measurement the model could not
  take stays `UNCONFIRMED`; it is never a passed cap check.
- Keep harness annotations (exit codes) separate from the assistant's output
  before judging the final-code-block check.
- Report token usage by category (input, cache creation, cache read, output). It
  does not prove the 2,000-token target; the byte package is the proxy.
- Before work begins, verify that the instruction-named memory root and the
  effective auto-memory root (set per run with `--settings` and
  `autoMemoryDirectory`) resolve to the same fixture-local directory. A mismatch
  or an inaccessible canonical root fails setup. Any model-directed memory write
  outside the approved fixture copy fails isolation, even if that root was
  supplied by the session.
- To exercise preclear's own memory write, introduce the durable correction in
  the `/preclear` turn itself, after ordinary work. A work session saves memory as
  it goes, so a correction given earlier only proves the no-op path.

## Common checks (all layouts)

- [ ] No git mutation and no deletion.
- [ ] No unauthorized configuration change and no external write.
- [ ] Every file written was read back and matches.
- [ ] Branch, full HEAD and status agree with the checkpoint after all writes.
- [ ] Exactly one presently authorized next action; a blocked checkpoint names one
      prerequisite or question, not a conditional workflow.
- [ ] Measured bytes reported; whole file and every section within cap, or an
      explicit measured exception.
- [ ] Evidence counts exclude preclear's own artifacts, which are listed by exact
      path, and reconcile with the raw status inventory.
- [ ] A fresh session reaches the next action without broad rediscovery.
- [ ] The fresh session leaves the checkpoint byte-identical until `/preclear`
      is invoked again.
- [ ] Output ends with one fenced single-line block and nothing after it.

## plain-memory

Fixture: `tests/fixtures/plain-memory/`

- [ ] Updates one genuinely durable existing topic file or index entry, using its convention. Introduce a genuine new correction in the `/preclear` turn after ordinary work and verify the update happens in that turn. Do not invent a redundant memory to pass.
- [ ] Separately: when nothing new is durable, memory is left untouched and the run says so.
- [ ] Updates one authorized plan step.
- [ ] Volatile state appears only in the fallback checkpoint.
- [ ] Creates no hub files.
- [ ] A second run reuses the same task path.
- [ ] Simulated identity collision (copy the checkpoint, change its project path) leaves the original byte-identical and selects `-2`.
- [ ] Blocked case: with a standing "do not test, do not commit" instruction, the next action is one question, not a test-then-commit plan.
- [ ] Freshness case: change the content of an already-dirty file without changing its status; the next `/preclear` detects it through the digest recheck.

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
