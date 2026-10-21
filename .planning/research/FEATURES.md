# Feature Research

**Domain:** Reproducible acceptance harness for a Claude Code skill (preclear), plus public release of the skill's repository
**Researched:** 2026-10-21
**Confidence:** MEDIUM overall. HIGH on Claude Code headless flags (official docs read today). MEDIUM on what other skill repos ship (few repos publish tests; the ones found are thin). LOW-MEDIUM on cost per full matrix (no dollar figures exist in the committed evidence).

## How this domain works (short version)

AI-skill test harnesses cluster into four shapes. Preclear's existing evidence is closest to the first and should borrow selectively from the others.

| Shape | Example | What it does | Fit for preclear |
|-------|---------|--------------|------------------|
| Headless-run plus shell assertions | Superpowers `tests/claude-code/` (`run-skill-tests.sh`, `test-helpers.sh` with `assert_contains`, `assert_not_contains`, `assert_count`, `assert_order`; fast tests by default, `--integration` for slow ones, `--test`, `--verbose`, `--timeout`) | Runs `claude -p`, greps the output | Closest. But it asserts on reply text; preclear's claims are about files, bytes, tool calls and hashes |
| Trace plus judges | MLflow skill evaluation (YAML config naming project, setup script, skills, prompt, timeout, allowed tools; copies the skill into `.claude/skills/`; runs `claude -p`; rule-based judges check side effects, LLM judges read the span tree) | Judges what Claude actually did, not what it said | Take the idea (judge tool calls and side effects), not the stack (MLflow server is a heavy dependency for a stranger) |
| Eval file with baseline | skill-creator `evals/evals.json` (prompts plus verifiable expectations, `with_skill` vs `without_skill`, pass-rate delta, viewer) | Measures uplift of the skill over no skill | Wrong question. Preclear's claim is "behaves per its own contract", not "beats no skill" |
| Record and replay | cendor-cassette, LLMReplay (coding-agent-vcr), reflight | Record an agent run, replay offline, redact secrets on write | Useful ideas: redact-at-write, drift reported without overwriting. Replay itself does not fit: the thing under test is the live model following SKILL.md |

Cross-cutting practice from prompt-testing tooling (promptfoo and similar): gate on deterministic assertions, use model-graded judges sparingly because they are slow, non-deterministic and cost tokens, set budget and timeout caps, pin tool versions.

Preclear's own history adds three things the public examples mostly lack: independent measurement (byte counts taken by a separate script, not the model's claim), frozen per-stage snapshots, and an executed-versus-attempted helper-call log. Defect D1 (the model's cap statements disagreed with the independent manifest in 5 of 12 runs) is the proof that measurement must never be delegated to the model under test.

Framing decision for requirements: the harness produces mechanically checkable facts and complete evidence. It does not issue the acceptance verdict. Verdicts remain a reviewer step (Codex consultation) because several checks are semantic (for example, "no unsupported Do-not-redo entry" in row 7).

## Feature Landscape

### Table Stakes (A Stranger or Reviewer Expects These)

Missing any of these and the harness either cannot be run from a clean clone, cannot be trusted, or is unsafe to publish.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| One-command entry point with row selection | Superpowers, MLflow and every credible harness have a single runner; a stranger will not read twelve scripts | LOW-MEDIUM | One script under `tests/` with `--list`, `--row <id>`, `--layout <name>`, `--all`, `--dry-run`. Rows keyed by the existing ids (1, 2, 3a, 3b, 3c, 4a, 4b, 5a, 5b, 6, 7, 8a-8c, 9, 10, 11, 12). `--dry-run` prints what would run and the number of model sessions without spending anything |
| Preflight with explicit SKIP vs FAIL vs BLOCKED | "Skip-when-missing" is the stated requirement; skipped must never read as passed | LOW | Check `claude` on PATH and version, authentication, `git`, `python3`, a usable hash tool (`shasum` or `sha256sum`). Distinct exit codes (convention: 0 pass, 1 fail, 77 skip). Final summary counts each state per row. A missing prerequisite yields SKIP with the reason, not a crash mid-row |
| Provenance record before every run | `tests/acceptance.md` already requires it; without it a rerun is not comparable | LOW | Claude Code version, enabled setting sources, installed skill path and sha256, adapter digests, helper-or-stub digest, wrapper digest. Same `digests.txt` shape as existing evidence |
| Isolated fixture copy per row, exclusive creation | Required by project constraints (no `rm -rf`, fail on collision) and by the "never touch real ledger roots" rule | MEDIUM | New run root created with exclusive `mkdir` (no `-p` on the leaf), abort if it exists. Own `CKPT_HOME`, ledger root, handoff root. Auto-memory pinned with `--settings` `autoMemoryDirectory`. `--setting-sources project,local`. Skill copied into the fixture's `.claude/skills/preclear/`. Cleanup is never automatic: print the path, let the user remove it |
| Pinned, committed permission policy | Headless runs deny anything unlisted; an uncommitted allowlist makes results irreproducible | MEDIUM | Committed per-row `tools.txt`. Lesson from rows 10 and 11: the allowlist must match the skill's exact status command, or the run silently exercises a fallback. Add a self-check that the skill's prescribed commands match an allowlist entry. Use manual or `dontAsk` style denial, never bypass-permissions (see anti-features) |
| Staged freezing of evidence | Already a harness rule in `tests/acceptance.md`; stage-named files are what make row-for-row comparison possible | MEDIUM | Snapshot checkpoint tree, git status, tree hashes, bindings, memory after each stage (work, `/preclear`, fresh resume, repeat, collision). Manifests use NUL-delimited listing so newline filenames survive (the old harness bug) |
| Independent measurement script | D1: model-reported caps were wrong in 5 of 12 runs | LOW-MEDIUM | Heading-inclusive UTF-8 byte counts, total and per section, taken on the original files before sanitizing. A measurement the harness cannot take is `UNCONFIRMED`, never a pass |
| Write-boundary and git-read-only assertions | Core hard rules of the skill (git read-only, never delete, no write outside) are the cheapest mechanical checks and the most valuable | MEDIUM | Tree hash of everything outside the fixture copy and evidence folder before and after; git HEAD, status, refs unchanged; attempted-but-denied writes reported separately from successful ones |
| Executed-versus-attempted helper-call log | Needed to prove stop-after-first-denial and bounded conflict retry | MEDIUM | Logging wrapper as the configured executable records argv and exit code and delegates to the stub (or a user-supplied helper). Attempted-but-denied calls come from the trace, executed calls from the wrapper log, as in the existing evidence |
| Test-only stub for the `checkpoint-v1` interface | Explicit milestone requirement; a stranger has no access to the private helper | MEDIUM-HIGH | Implements the documented table: `status`, `show`, `validate`, `update` with expected-hash, `note`, `lint`, `handoff`; exit codes 0 to 6; conflict file naming; unbound status line; block rules (six sections, 4,096 bytes, `Authorization boundaries` non-empty and at most 600 chars). Lives in `tests/`, clearly labelled test-only. Must reproduce output formats exactly (the skill treats non-matching output as failure) |
| Model-free self-tests of the harness itself | A public harness whose own parts are untested will rot; this suite costs zero tokens and can run anywhere | MEDIUM | Covers: stub conformance against the interface table, measurement script on edge inputs (non-Latin text, headings), sanitizer and leak scan, run-root collision refusal, NUL manifest with newline filenames, preflight SKIP paths, allowlist-matches-skill-commands check. Shell plus Python standard library only |
| Sanitization pass plus leak-scan gate before anything is committed | The repo is going public; project constraint forbids home paths, hostnames, credentials in committed files | MEDIUM | Reuse existing token vocabulary (`<run>`, `<helper>`, `<auto-memory-root>`, `<repo>`, `<home>`) so new evidence is comparable with old. Gate fails on home-folder path patterns, the local username, hostnames, IP addresses, key-like strings. Needs a `promote` step (run root to `tests/evidence/<name>/`) that refuses to copy if the scan fails |
| Cost and runtime guardrails | Unbounded model sessions are the usual way a harness hurts a stranger | LOW | Per-session `--max-turns` and `--max-budget-usd` (both confirmed print-mode flags) plus a wall-clock timeout; print the session count in `--dry-run`; record token usage by category and `total_cost_usd` per session (the result message carries cost; docs call it a client-side estimate, not billing) |
| Run guide and result-reading guide | A stranger needs to know prerequisites, expected duration, what SKIP means, what a pass proves and does not prove | LOW | One README under `tests/`; states that token usage does not prove the 2,000-token target (byte package is the proxy), that results are model-dependent, and which defects are known and disclosed |
| Portability to a stock macOS or Linux shell | "Anyone with Claude Code" includes macOS with bash 3.2 and BSD userland | MEDIUM | Avoid bash 4 features, GNU-only flags, `sha256sum`-only; Python 3 standard library only. Windows is documented as unsupported rather than half-supported |
| Machine-readable per-row summary | Needed for the harness to report ran, skipped, mechanical-pass, mechanical-fail without scraping prose | LOW | Small facts file per row (ids, digests, byte counts, executed-call count, denial count, write-boundary result) plus a human summary table |

### Differentiators (What Makes This Harness Better Than a Typical Skill Test Folder)

Aligned with the Core Value (every fact verified when written, unknown marked `UNCONFIRMED`): the harness's job is to catch the model asserting what it did not check.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Per-row evidence comparison against the committed baseline | Delivers "compare row for row with existing evidence" without brittle text diffs | MEDIUM-HIGH | Compare structured facts, not prose: skill digest, section byte counts versus caps, executed helper-call classes and counts, denial counts, stop-after-denial, fallback label present, zero writes during fresh resume, frozen-copy hash identical across stages. Risk: the existing evidence has no facts file, so the baseline must be derived from the committed `measurements.md`, `wrapper-calls.log` and README tables; define a per-row contract (list of assertions) rather than a byte diff |
| Trace-based assertions over stream-json | MLflow's insight: judge what Claude did. Preclear already reasons this way (seven fresh-resume runs, zero Write or Edit calls) | MEDIUM | Parse stream-json tool_use and result events (the final result message lists `permission_denials`; the init event records session metadata). Assertions: no Write or Edit in resume; no git mutation commands; order of calls; same syntax not retried after a denial |
| Stub with fault-injection modes | Replaces the counting conflict wrapper with a first-class, documented switch; makes rows 2, 3a, 3b, 4a reproducible by design | MEDIUM | Modes: conflict once, conflict twice (UNSTABLE), deny write, kill switch (exit 5), lock timeout (exit 6), invalid block (exit 4). Each mode logged in the wrapper log so the evidence shows which branch was forced |
| Bring-your-own-helper mode | Lets bokiko, or anyone with a conforming helper, run the same rows against a different build without changing the harness | LOW-MEDIUM | One setting for the helper executable; digest recorded. Output differing from the interface table counts as a failure, which is the skill's own rule. Also a drift detector for the real helper |
| Run, then promote | Separates cheap local reproducibility (strangers keep results in their run root) from publishing evidence (bokiko promotes a sanitized, scanned copy into `tests/evidence/`) | MEDIUM | Reuses the sanitizer and leak-scan gate; never overwrites an existing evidence folder; new reruns add new dated folders, honouring "historical evidence is preserved, never repaired" |
| Resumable matrix | A 12-row run that dies at row 9 should not repeat rows 1 to 8 | MEDIUM | Skip rows whose evidence folder is complete; never overwrite partial ones (mark as failed-setup, run into a fresh suffix) |
| Reviewer checklist emitted per row | Semantic checks stay explicit instead of being faked as automation | LOW | Generates the list of judgement items per row (for example, row 7: every Do-not-redo entry has a supporting tool call; row 10: NUL form executed or exception disclosed) with pointers to the evidence file to open |
| Heuristic unsupported-claim flag | Targets the one open correctness defect (row 7) | HIGH | For each Do-not-redo or Evidence line naming a check (for example a registry lookup), look for a matching tool call in the trace. Heuristic, will have false positives; ship as a warning feeding the reviewer checklist, not a gate. Defer until the row 7 rerun shows whether it is needed |
| Repeat mode (`--repeat N`) with per-row stability | Surfaces non-determinism instead of hiding it behind one lucky run | MEDIUM | Multiplies cost by N; off by default. Not needed for acceptance, useful for investigating flaky rows. Defer |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| GitHub Actions running the live matrix | Looks professional; "tests run on every PR" | Needs an API key as a repo secret, spends tokens per run, and fork PRs either cannot use secrets or invite abuse. Already Out of Scope in PROJECT.md | If CI is ever added: model-free self-tests, shell lint and the leak scan only. Zero tokens, no secrets |
| Committing raw stream-json transcripts | "Full evidence" and easy reproduction | Raw transcripts carry the working directory, home paths, session ids, tool lists and injected system context; that is the known source of the home-path finding in commit d437af2 | Keep raw transcripts in the gitignored run root; commit sanitized full traces plus the sha256 of the raw file (existing practice: "raw transcript digest") |
| Byte-for-byte golden output comparison | Makes tests simple | The model's prose varies run to run; every rerun would fail for meaningless reasons | Compare structured facts and caps (per-row contract) |
| LLM-as-judge inside the harness as the verdict | Automates "was this good?" | Non-deterministic, costs tokens, needs a second model, and circular for a skill about verified facts | Mechanical assertions in the harness; semantic verdict stays with the Codex consultation, driven by the emitted reviewer checklist |
| Harness that prints "ACCEPTED" | Closure feeling | Acceptance is a review claim in this project; auto-accept would also hide the disclosed exceptions (rows 7, 10, 11, 12) | Print per-row mechanical results and list open exceptions; wording says "mechanical checks passed", never "accepted" |
| `--bare` as the default run mode | Documented as the recommended mode for scripted calls; faster, no host config leakage | Bare mode does not read OAuth or keychain credentials (needs `ANTHROPIC_API_KEY`) and skips skill auto-discovery, so a stranger on a subscription cannot run it and the project skill would not load. Also changes what is being tested | Keep `--setting-sources project,local`, isolate user config via per-run settings and pinned auto-memory. Offer `--bare` plus explicit `--add-dir` only as an optional documented variant, if at all |
| `--dangerously-skip-permissions` or bypass mode to "make runs pass" | Removes harness-policy refusals such as compound-command denials | Defeats the denial rows (3b, 6, 7) and the stop-after-denial and write-boundary assertions | Pinned allowlist; treat harness policy refusals as counted events, as the existing traces do |
| Retry-until-green loops | Smooths flakiness | Masks real defects (D1 was only visible because failures were kept); violates "reruns supersede by adding new folders" | Record the failure, rerun into a new run root, keep both |
| Automatic cleanup or overwrite of run roots | Tidy disk, idempotent reruns | Violates the no-`rm -rf`, exclusive-creation constraint and destroys evidence | Collision is a hard error; harness prints the removal command for the user to run |
| Depending on a test framework (promptfoo, MLflow server, pytest plugins, Node toolchain) | Reuse of dashboards and judges | A stranger "with Claude Code" should not need a second toolchain; every added dependency is a skip condition | Bash plus Python 3 standard library |
| Parallel row execution | Faster matrix | Shared rate limits, interleaved cost, harder-to-read evidence, risk of leaking state through shared environment | Serial by default; rows are already isolated if a user wants to run separate processes |
| Bundling or referencing the author's real helper | "Makes backend rows realistic" | The helper is a separate, unaudited project and its install path is a private path; the interface text already warns builds differ | Stub for the tested interface; bring-your-own-helper variable for anyone with a conforming build |
| Changing SKILL.md to make a harness check pass | Convenient | SKILL.md is at 11,994 of 12,000 bytes and accepted; changes reopen acceptance | Only edit the skill to fix a defect the rerun exposes, then rerun the affected rows |

## Feature Dependencies

```
Preflight (SKIP/FAIL/BLOCKED)
    └──required by──> One-command runner
                           ├──requires──> Isolated fixture copy (exclusive creation)
                           │                  └──requires──> Pinned permission policy
                           ├──requires──> Provenance record
                           └──produces──> Staged freezing of evidence
                                              ├──feeds──> Independent measurement
                                              ├──feeds──> Write-boundary and git-read-only assertions
                                              └──feeds──> Machine-readable per-row summary
                                                              └──enables──> Per-row comparison against baseline

Stub for checkpoint-v1
    ├──requires──> Interface table in references/checkpoint-v1.md (single source of truth)
    ├──wrapped by──> Executed-versus-attempted call log
    ├──verified by──> Model-free self-tests (stub conformance)
    └──extended by──> Fault-injection modes ──enhances──> backend rows 1, 2, 3a, 3b, 3c, 4a, 4b

Sanitizer + leak scan
    ├──required by──> Promote to tests/evidence
    └──verified by──> Model-free self-tests

Trace-based assertions ──requires──> stream-json capture (already pinned) ──enhances──> Write-boundary assertions

Resumable matrix ──requires──> Staged evidence with completeness marker

Bring-your-own-helper ──conflicts (soft)──> Fault-injection modes (only the stub can be told to misbehave)

Repeat mode ──conflicts──> Cost guardrails unless a total budget is enforced across repeats

CI running live matrix ──conflicts──> Out of Scope (API key secret, token spend)
```

### Dependency Notes

- **The runner requires the permission policy and the isolated fixture:** without a pinned allowlist the run depends on the host's settings; without exclusive creation it can overwrite evidence. Both come before any model session.
- **Stub conformance requires the interface table, not the real helper:** the stub is written from `references/checkpoint-v1.md`. The doc says interface facts were verified against a 2026-10-04 build; the stub's self-tests encode that table, so a doc change forces a stub change by failing the self-test.
- **Per-row comparison requires a facts file that the old evidence lacks:** derive the baseline from committed `measurements.md`, `wrapper-calls.log` and README tables once, then store it as the per-row contract. Do not edit historical evidence to add fields.
- **Promote requires sanitizer plus scan:** nothing enters `tests/evidence/` by hand. This is the control that prevents a second d437af2.
- **Row 10 needs a policy decision before it can be fully exercised:** the NUL `-z` status form needs output redirection, which headless policy has denied. Either the pinned policy permits that single redirection for row 10 (a documented, scoped exception) or the row keeps the declared quoted-porcelain fallback and the comparison records that as the expected outcome. This changes what the harness is allowed to claim.
- **Fault-injection and bring-your-own-helper cannot be combined:** fault modes are a property of the stub; a user-supplied helper is judged on its own behaviour.

## MVP Definition

### Launch With (this milestone)

- [ ] One-command runner with `--list`, `--row`, `--layout`, `--all`, `--dry-run` — entry point a stranger can find
- [ ] Preflight with SKIP/FAIL/BLOCKED and honest summary — "skip-when-missing" requirement
- [ ] Provenance record, isolated exclusive run root, pinned committed permission policy — reproducibility and safety
- [ ] Staged freezing, independent measurement, write-boundary and git-read-only assertions, per-row facts summary — deterministic evidence
- [ ] Logging wrapper and test-only stub covering the interface table, with the fault modes that rows 2, 3a, 3b, 4a, 4b already need — backend rows without the private helper
- [ ] Model-free self-test suite — proves the harness itself, costs nothing, gives a stranger a first success without an API call
- [ ] Sanitizer, leak scan and promote step — makes the public release and the committed rerun evidence safe
- [ ] Cost and runtime guardrails plus a run and result-reading guide — makes a full matrix rerun something a stranger can start knowingly
- [ ] Row 7 clean rerun and one full-matrix rerun from a clean clone, promoted as a new dated evidence folder — the milestone's definition of done

### Add After Validation (v1.x)

- [ ] Per-row comparison against the committed baseline — once the first promoted rerun exists, so the contract is built from two real data points rather than guessed
- [ ] Trace-based assertions beyond zero-write and no-git-mutation — when a reviewer finds a recurring semantic check worth automating
- [ ] Reviewer checklist emitter — after the first Codex review of the rerun shows which items recur
- [ ] Resumable matrix — when a full run proves long enough to be interrupted in practice
- [ ] Bring-your-own-helper mode — when a second conforming helper has a user

### Future Consideration (v2+)

- [ ] Repeat mode with per-row stability — only if a row shows run-to-run variance worth quantifying
- [ ] Heuristic unsupported-claim flag — only if row 7's defect recurs after the rerun
- [ ] Token-free CI (self-tests, shell lint, leak scan) — cheap and safe, but outside this milestone's stated scope; revisit after local reproducibility
- [ ] Second backend adapter harness — no second ledger system has a user

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| One-command runner and row selection | HIGH | LOW-MEDIUM | P1 |
| Preflight SKIP/FAIL/BLOCKED | HIGH | LOW | P1 |
| Isolated exclusive run root, pinned permission policy | HIGH | MEDIUM | P1 |
| Provenance record | HIGH | LOW | P1 |
| Staged freezing, NUL-safe manifests | HIGH | MEDIUM | P1 |
| Independent measurement script | HIGH | LOW-MEDIUM | P1 |
| Write-boundary and git-read-only assertions | HIGH | MEDIUM | P1 |
| Logging wrapper (executed vs attempted) | HIGH | MEDIUM | P1 |
| Test-only stub for checkpoint-v1 | HIGH | MEDIUM-HIGH | P1 |
| Model-free self-tests | HIGH | MEDIUM | P1 |
| Sanitizer, leak scan, promote | HIGH | MEDIUM | P1 |
| Cost and runtime guardrails | MEDIUM-HIGH | LOW | P1 |
| Run and result-reading guide | HIGH | LOW | P1 |
| Machine-readable per-row summary | MEDIUM-HIGH | LOW | P1 |
| Stub fault-injection modes | HIGH | MEDIUM | P1 (the rows need them) |
| Per-row baseline comparison | HIGH | MEDIUM-HIGH | P2 |
| Trace-based assertions (extended) | MEDIUM | MEDIUM | P2 |
| Reviewer checklist emitter | MEDIUM | LOW | P2 |
| Resumable matrix | MEDIUM | MEDIUM | P2 |
| Bring-your-own-helper mode | LOW-MEDIUM | LOW-MEDIUM | P2 |
| Repeat mode | LOW | MEDIUM | P3 |
| Heuristic unsupported-claim flag | MEDIUM | HIGH | P3 |
| Token-free CI | MEDIUM | LOW-MEDIUM | P3 (out of this milestone) |

**Priority key:**
- P1: Must have for this milestone
- P2: Should have, add after the first promoted rerun
- P3: Nice to have, future consideration

## Comparable Harnesses (what they ship, what to take)

| Feature | Superpowers `tests/claude-code` | MLflow skill evals | skill-creator evals | Record/replay tools | Our Approach |
|---------|---------------------------------|--------------------|---------------------|---------------------|--------------|
| Entry point | `run-skill-tests.sh` with `--integration`, `--test`, `--verbose`, `--timeout` | `test_skill.py` driven by YAML | `/skill-creator` evaluation phase | Library decorators or pytest plugins | Single `tests/` runner with row and layout selectors |
| Isolation | Not stated | Setup script, skills copied into `.claude/skills/` | Subagents with and without skill | Cassette per test | Exclusive-creation run root per row, own helper home and memory root |
| Assertions | Shell string and count helpers on reply text | Rule-based side-effect judges plus LLM judges over spans | Natural-language expectations graded by a model | Replay must match recorded calls | Mechanical facts (bytes, hashes, call logs, write boundary); semantic verdict by reviewer |
| Skip when tool missing | Not documented (README does not say) | Not documented | Not applicable | Replay needs no model | Explicit SKIP with reason and distinct exit code |
| Cost control | Timeout only (about 2 min fast suite, 10 to 30 min integration) | Timeout only | Not stated | None (offline) | Max turns, max budget, timeout, dry-run session count, usage by category |
| Secrets and privacy | Not addressed | Not addressed | Not addressed | Redact on write, keep match hashes | Token substitution plus leak-scan gate before promote |
| CI | README shows exit-code usage with `--timeout 900`; no confirmed pipeline | Not stated | Not applicable | Offline CI is the selling point | None this milestone; token-free only later |

## Sources

- Superpowers headless skill tests, file list and runner options: https://github.com/obra/superpowers/tree/main/tests/claude-code and its README (raw) — MEDIUM (fetched via summarizing tool; README states no skip behavior)
- MLflow, "Testing and Refining Claude Code Skills with MLflow": https://mlflow.org/blog/evaluating-skills-mlflow — MEDIUM
- skill-creator eval schema and with/without-skill benchmarking (third-party descriptions, no official page found): https://academy.conduction.nl/academy/claude-skills-tutorial-3-skill-evals and https://cdn.jsdelivr.net/npm/opencode-skill-creator@0.2.25/dist/skill/references/schemas.md — LOW-MEDIUM
- Claude Code headless documentation (`-p`, `--bare`, structured output, permissions in unattended runs, `permission_denials`, `system/init`): https://code.claude.com/docs/en/headless — HIGH (official, read 2026-10-21)
- Claude Code CLI reference (`--setting-sources`, `--max-budget-usd`, `--max-turns`, `--no-session-persistence`, `--restricted`, `--permission-mode`, `--settings`): https://code.claude.com/docs/en/cli-reference — HIGH (official, read 2026-10-21)
- Prompt regression testing practice (deterministic assertions first, judges sparingly, budgets, version pinning): https://medium.com/@alexrodriguesj/testing-llm-prompts-like-code-regression-evals-in-ci-cd-with-promptfoo-5242b4dcb9be and https://kinde.com/learn/ai-for-software-engineering/ai-devops/ci-cd-for-evals-running-prompt-and-agent-regression-tests-in-github-actions/ — LOW-MEDIUM (blog posts)
- Record and replay for agents (redaction on write, drift without overwrite): https://pypi.org/project/cendor-cassette/ and https://pypi.org/project/coding-agent-vcr/ — LOW-MEDIUM (package pages)
- Project inputs: `.planning/PROJECT.md`, `tests/acceptance.md`, `tests/evidence/publication-2026-10-20/README.md`, `references/checkpoint-v1.md` — HIGH (primary)

## Gaps

- No dollar cost per full matrix exists in the committed evidence; measure it in the first rerun and record `total_cost_usd` per session before telling strangers what to expect.
- Claude Code 2.1.304 produced the existing evidence; the flag set above was confirmed against current docs but not executed in this research. The first harness phase should verify each flag on the installed version (the headless docs note some flags need specific minimum versions).
- Whether any public skill repo ships a stub backend or evidence-comparison tooling: none found. This is likely novel territory, so treat the comparison feature as design work, not adoption.

---
*Feature research for: reproducible acceptance harness for a Claude Code skill and its public release*
*Researched: 2026-10-21*
