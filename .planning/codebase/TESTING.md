---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# Testing Patterns

**Analysis Date:** 2026-10-21

## Test Framework

**Runner:**
- None. There is no unit-test framework or CI. Tests are manual-checklist acceptance runs defined in `tests/acceptance.md`, executed as headless Claude Code sessions (`claude -p`, version recorded per run, e.g. 2.1.303 and 2.1.304) against fixtures in `tests/fixtures/`.
- Harness scripts and raw transcripts live in the gitignored `runs/` folder and are not part of the shipped project.

**Assertion Library:**
- Human/reviewer judgment against checkbox criteria; byte counts and SHA-256 digests as machine-checkable evidence.

**Run Commands:**

```text
Manual procedure (tests/acceptance.md "How to run"):
1. Copy one fixture from tests/fixtures/ to a scratch folder outside the repo.
2. Start a Claude Code session there with preclear installed
   (project skill, --setting-sources project,local).
3. Do a small piece of fake work on the "widget-export" task.
4. Run /preclear.
5. Start a fresh session in the same folder; paste the printed resume line.

```

Pin memory per run with `--settings` containing `autoMemoryDirectory`, generated from the fixture's `runtime-settings.example.json`.

## Test File Organization

**Location:**
- Spec: `tests/acceptance.md`.
- Fixtures: `tests/fixtures/plain-memory/`, `tests/fixtures/hub-memory/`, `tests/fixtures/bound-ledger/` (each: `README.md`, `project/` with `CLAUDE.md`, `PLAN.md`, memory files; `runtime-settings.example.json` for the memory layouts).
- Evidence: `tests/evidence/<layout>-<date>[-rerun]/` and `tests/evidence/publication-2026-10-20/row*/`.

**Naming:** see Files in `CONVENTIONS.md`; stages are `s1` (work), `s2` (`/preclear`), `s3` (fresh resume), `s4` (tamper or unbound variant), `s5` (repeat `/preclear`).

**Structure (per evidence run):**

```text
README.md              verdicts, sequence table, findings
digests.txt            sha256 of skill, references, helper, wrapper
fixture-CLAUDE.md      configuration block used
tools.txt              allowed tools
measurements.md        UTF-8 bytes total and per section (originals, pre-sanitize)
s2-preclear-prompt.md  exact prompt incl. the correction introduced in the /preclear turn
s2-preclear-trace.md   short trace + raw final reply
snap-0-setup/ snap-1-after-work/ snap-2-after-preclear/  frozen stage copies (ledger, sha.txt, status.txt)
wrapper-calls.log      executed helper calls (row cases with a helper)
```

## Test Structure

**Suite organization:** three layout suites (plain-memory, hub-memory, bound-ledger), each a checklist of `- [ ]` criteria in `tests/acceptance.md`, preceded by "Common checks (all layouts)". After the layouts pass, a 12-row publication matrix runs one isolated fixture copy per row, in the stated order.

**Patterns:**
- Setup: record Claude Code version, setting sources, installed skill path and digest; verify instruction-named memory root equals the effective auto-memory root, else fail setup.
- Freeze each stage (copy checkpoint tree) before the next runs.
- Introduce durable corrections in the `/preclear` turn itself, otherwise only the no-op path is exercised.
- Teardown: none; run folders stay local, sanitized evidence is copied into `tests/evidence/`.
- Assertions: no git mutation, no deletion, no writes outside fixture/evidence, exactly one next action, caps respected, output ends with one fenced single-line block, fresh session leaves checkpoint byte-identical until `/preclear` runs again.
- Verdicts are recorded per row (PASS / FAIL / FIX FIRST) with reviewer attribution in evidence READMEs; failed first passes are kept as `-first-pass` beside the `-rerun`, never relabelled.

## Mocking

**Framework:** none; isolation instead.
- Isolation: fixture copies, per-run `CKPT_HOME` for the bound-ledger helper, `--setting-sources project,local` so personal skills cannot shadow the project skill.
- Helper-backed rows use a logging wrapper (`wrapper-checkpoint.sh`) as the configured executable. It records argv and exit code, then delegates unchanged to the real helper. Attempted-but-denied calls appear only in traces.
- The bound-ledger layout needs the author's helper, which is not bundled; edit the paths in the configuration block first.

**What to mock/isolate:** helper state registry, memory root, ledger roots, home config.
**What NOT to do:** never bind a real session, touch real ledger roots, or provoke conflict/collision/denial cases in a live session.

## Fixtures and Factories

**Test data:** a fake "widget-export" task (JSON/CSV exporter, plan steps, a memory topic file `project_widget_export.md`, index `MEMORY.md`; hub-memory adds `hub_feedback.md`, `hub_projects.md`).

```json
{ "autoMemoryDirectory": "/ABSOLUTE/PATH/TO/FIXTURE-COPY/project/memory" }
```

**Location:** `tests/fixtures/*/`. Scenario variants (collision, tamper, controlled conflict, hostile filenames, concurrent change) are staged on copies by the harness, not stored as fixtures.

## Coverage

**Requirements:** none numeric. Coverage is the acceptance checklist plus the 12-case publication matrix (wrong binding; double conflict; missing/denied helper and `fallback_directory: none`; malformed/conflicting config; no/disabled memory; read-only plan; all destinations denied; non-git/detached/unborn; linked worktree; hostile filenames; concurrent change; frozen handoff).
- Token usage is reported by category but does not prove the 2,000-token target; the byte package (<=6,000) is the proxy.
- Known open defect (per `CHANGELOG.md`): row 7 printed checkpoint carries an unsupported Do-not-redo entry. Publication stays unapproved until the content and history audit passes.

**View coverage:** read `tests/evidence/publication-2026-10-20/README.md` (verdict table) and each layout's `README.md` roll-up.

## Test Types

**Unit tests:** none.
**Integration tests:** the headless end-to-end runs above (work, `/preclear`, fresh resume, repeat, collision).
**E2E tests:** same; no browser or CI automation.

## Common Patterns

**Measuring caps (by command, on originals):**

```text
total 3494 bytes (cap 4096), sha256 <digest>
- Identity and state: 734   (cap 800)

```

Take measurements before sanitizing paths; an unmeasurable item stays `UNCONFIRMED`, never a pass.

**Separating harness noise:** keep harness annotations (exit codes, `s1.exit`, `s2-preclear.exit`) apart from the assistant output when judging the final-code-block check.

**Denial/error testing:** count blocked attempts separately from successful filesystem changes; fail resume-safety on any unauthorized deletion or write attempt even if blocked; compound-shell refusals are harness policy events, not helper denials.

**Adding a test:** add a `- [ ]` criterion under the right layout in `tests/acceptance.md`, run it on a fixture copy, sanitize paths to the tokens in `CONVENTIONS.md`, add an evidence folder with the files above, and update `CHANGELOG.md`.

---

*Testing analysis: 2026-10-21*
