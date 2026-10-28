# Phase 3: Walking Skeleton (Row 1) - Research

**Researched:** 2026-10-28
**Domain:** Python 3.9 standard-library test harness that drives the real `claude -p` (Claude Code 2.1.310) against a stub checkpoint helper, files sanitized mechanical evidence, and compares it read-only with committed evidence
**Confidence:** HIGH for every in-repo fact (each read this session); MEDIUM for the design recommendations; LOW only where tagged `[ASSUMED]` (limit-hit behaviour, cost projection for the Sonnet model)

**Provenance tags used below.** `[VERIFIED: path:lines]` means I opened that file this session and the quoted text is verbatim. `[CITED: ...]` means a repository document that itself cites a source. `[DERIVED]` means computed this session from files I read (the inputs are named). `[ASSUMED]` means not verified here and it is listed in the Assumptions Log. No web search and no Context7 call was made, and the real `claude` binary was never started (zero tokens spent by this research).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Row 1 session shape (discussed with bokiko)
- **D-01:** The work turn (s1) and the `/preclear` turn (s2) are **one session, resumed**: s1 runs
  with a pinned `--session-id`, s2 runs with `--resume` on that id, exactly as spike S2b proved on
  Claude Code 2.1.310. One session id ties both stages together in the evidence.
- **D-02:** The **fresh-resume stage (s3) is part of row 1 in this phase**: a third, new session
  pastes the resume line the checkpoint printed and must stay read-only (zero Write or Edit calls),
  the behaviour the committed evidence recorded and PROJECT.md lists as validated. Row 1 files s1,
  s2 and s3.
- **D-03:** The work turn runs under the **pinned allowlist with `--permission-mode default` and no
  approvals**, never `--dangerously-skip-permissions`. Anything outside the list is denied by the
  binary, lands in `permission_denials`, and the write-boundary check reports it. Nothing can leave
  the scratch project.
- **D-04 (Claude's call, bokiko said "you decide"):** Prompts. Reuse the committed prompts
  (`s2-preclear-prompt.md` byte for byte, and the committed work-turn instruction for s1). Add a
  short pinned preamble only if the zero-token dry run shows the pinned allowlist alone cannot
  contain the work turn; if a preamble is added, it is recorded in the row's evidence and named in
  the plan as a deviation from the committed prompt.

### Evidence folder and comparison (discussed with bokiko)
- **D-05:** The new evidence folder is `tests/evidence/rerun-<date>-<model>/` (for example
  `rerun-2026-10-28-claude-sonnet-5-5/`), created exclusively; row folders inside keep the committed
  names (`row1-wrong-binding`). A name that already exists is refused, never reused.
  — **Reversibility:** costly — the folder name is the label every later comparison and the Phase 4
  review refer to; renaming after filing means a second promote and new digests.
- **D-06:** The folder's top-level README labels the run a **new baseline on the pinned model and
  build**, states the measured cost, and says it is **not a replication** of 2026-10-20 because that
  run recorded no model. The committed folder stays the reference until a reviewer accepts the new
  one; the replacement question belongs to Phase 4.
- **D-07:** The read-only comparer treats as structural differences: files present on one side
  only, README section headings that differ, helper-call and tool-call counts that differ, and byte
  measurements outside the cap. Content digests are expected to differ and are **listed, never
  judged**.
- **D-08:** The comparer **only reports**: it exits 0 whenever both trees were readable, and never
  emits PASS or FAIL for a row (EVID-05). A non-zero exit means it could not read a tree, nothing
  else. Tree digests of both evidence trees are identical before and after it runs (EVID-06).

### Reviewer checklist and preflight (discussed with bokiko)
- **D-09:** The row README ends with `Reviewer verdict: PENDING` followed by a checklist of
  **mechanical facts, one per line, each naming its source file**: helper calls attempted, executed
  and denied (wrapper log); ledger digests unchanged from setup to after (`snap-*/sha.txt`); writes
  outside approved roots (snapshot diff); git mutations (git status capture); checkpoint bytes
  versus cap (measurements); session ids per stage; cost and turns per stage (usage). Blank boxes
  for the reviewer, no prose from the model.
- **D-10:** Preflight has **three states with three distinct exit codes**: SKIP (row not applicable
  on this machine) is filed under a `SKIPPED` label with the reason and can never read as PASS;
  FAIL (harness or fixture broken) exits with its own code and files nothing; BLOCKED (no login,
  untested Claude Code version, stub unreachable, runs root under a home folder) exits with a third
  code, prints the one-line fix from the README and files nothing. `--dry-run` exercises all three
  with no `claude` process and no usage recorded (HARN-01, HARN-02).
- **D-11:** Cost is recorded as **`usage.txt` per row** with per-stage input, output and cache
  tokens, turns and `total_cost_usd` taken from the `result` events, and the folder README repeats
  the row total and the run total. The Phase 3 SUMMARY quotes that number; Phase 4's spend is
  confirmed from it.
- **D-12 (bokiko's decision, 2026-10-28):** The matrix baseline model is **`claude-sonnet-5-5`**,
  the same full id the spikes pinned, so the committed S2 fixture is the same model's stream. The
  **one real row 1 run is capped at 2 USD across its three stages** with a small `--max-turns` per
  stage; a second attempt needs bokiko's explicit word in the conversation. The dry run and every
  test spend nothing. — **Reversibility:** costly — the model id is in the evidence folder name and
  in `model-id.txt`; changing it means a new baseline folder.

### Carried forward from Phase 2 (locked, do not re-ask)
- Strict isolation: harness-owned `CLAUDE_CONFIG_DIR` outside the repository and outside the
  user's own Claude config, `--setting-sources project,local`; the `system/init` manifest is
  asserted every run (the `preclear` skill listed, permission mode as pinned, memory paths as set,
  no plugin whose source is not `@builtin`); the isolation mode recorded per row is `strict`.
- Run roots live under a runs root outside every home folder (`PRECLEAR_RUNS_ROOT`, shared-folder
  default, home folders refused), because Claude Code loads ancestor instruction files as Project
  instructions.
- Pinned argv from `pc_flags` (stream-json, verbose, settings with a realpath auto-memory dir,
  `--session-id`, `--permission-mode default`, literal `--allowedTools`, one full model id,
  `--max-turns`, `--max-budget-usd`, `DISABLE_AUTOUPDATER=1`); the version gate refuses any build
  outside `TESTED_VERSIONS` (2.1.310 today) with the BLOCKED exit.
- Sanitizer tokens are lower-case `<home>`, `<user>`, `<host>`, `<tmp>`, `<repo>`; every file passes
  the Python leak gate before `promote`; `promote` fails closed and prints counts only.
- Runner contract from review WR-14: after sanitising a run, the runner **must pass
  `sanitizer.deny_entries()` to `promote`**; the gate CLI and `promote` defaults carry no login by
  design. A test must fail when a sanitised run is promoted without those entries.
- Python 3.9 floor, standard library only, bash 3.2 shim; everything new under `tests/harness/`;
  `SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/publication-2026-10-20/` unchanged
  (HARN-13); no deletion primitives outside the test utilities; no home paths, hostnames, IPs or
  emails in any committed file; commits carry no attribution trailer.

### Claude's Discretion
- Prompt reuse versus preamble (D-04), decided by the dry run.
- CLI surface details of the driver (`--list` output format, `--row` and `--layout` id spelling,
  `--all` ordering), the exact SKIP, FAIL and BLOCKED exit code values (distinct, documented in the
  README table, reusing the `pc_exitcodes` family already reserved), and the `max-turns` per stage
  under the 2 USD row cap.
- How the per-row fixture seeds the stub's `CKPT_HOME` and the two ledgers, how the wrapper log
  lines are correlated with `tool_use` ids, and the staging layout before `promote`.
- Which of the spike driver's robustness warnings (review WR-12, WR-03) are fixed as part of
  building the real runner, provided the fix stays inside `tests/harness/`.

### Deferred Ideas (OUT OF SCOPE)
- Whether the rerun folder replaces `publication-2026-10-20` as the reference — Phase 4, after the
  Codex review (RERUN-04).
- Fixing the remaining Phase 2 review warnings that do not touch the runner (WR-04 to WR-11,
  WR-13, the Info items) — Phase 4 hygiene, or a dedicated hardening pass.
- Per-row extra allowlist rules beyond the committed `tools.txt` — only if a later row needs them
  (Phase 4 rows 10 and 11).
- Linux location of the login credentials (file under the config dir instead of the Keychain) is
  documented, untested — Phase 4 stranger-clone criterion (RERUN-02).
</user_constraints>

## Project Constraints (from CLAUDE.md)

There is no root `CLAUDE.md`. `.claude/CLAUDE.md` holds one directive. [VERIFIED: .claude/CLAUDE.md:1] `Commits in this repo carry no co-author or generated-by trailer.`

Other binding constraints the planner must carry (all from files read this session):

- `.claude/settings.json` blanks the attribution fields and `.githooks/commit-msg` refuses an AI attribution trailer. [VERIFIED: .claude/settings.json:1-7; .githooks/README.md "What runs"]
- Hooks are on for this clone (`core.hooksPath` is `.githooks`) and every commit runs `gitleaks` 8.30.0 with `.gitleaks.toml` plus a deny-list check. Any file the harness files under `tests/evidence/` and any file under `.planning/` must be free of home paths (`/Users/<name>/`), temp roots, private hosts and IPs, and emails. The shared-folder default runs root is itself matched by the `home-path-unix` rule, so RESEARCH, PLAN and SUMMARY text must not spell it out. [VERIFIED: .gitleaks.toml rule `home-path-unix`; tests this session, see Pitfall 7]
- Python 3.9 floor, standard library only, sibling-module imports only, `pc_` prefix for library modules and `test_` for tests, no module stem equal to a standard-library module, bash 3.2 for any shim. [VERIFIED: tests/harness/test_imports.py:1-30,38-39]
- `SKILL.md` is 11,994 bytes today (cap 12,000); `SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/publication-2026-10-20/` must show an empty `git diff` against the phase base commit `0a97367e5c7b876163f68b1ac3f2c960ff5f70bc`. [VERIFIED: `wc -c SKILL.md` and `git rev-parse HEAD` this session]
- `workflow.nyquist_validation` is `false` in `.planning/config.json`; the caller explicitly asked for a Validation Architecture section, so it is included. `security_enforcement` is `true` (ASVS level 1), so a Security Domain section is included. [VERIFIED: .planning/config.json]
- No `.claude/skills/` directory exists in this working tree. The frozen skill is the repository-root `SKILL.md` plus `references/`; the harness installs byte-exact copies into each run's `project/.claude/skills/preclear/`. [VERIFIED: `ls .claude/skills` reported no such directory]

<phase_requirements>
## Phase Requirements

| ID | Description (verbatim from REQUIREMENTS.md) | Research Support |
|----|---------------------------------------------|------------------|
| HARN-01 | A stranger runs one command under `tests/harness/` with `--list`, `--row <id>`, `--layout <name>`, `--all` and `--dry-run`; dry run prints the session count and spends no tokens | Driver CLI as a new `pc_` module run as `python3 -E -s -B`; row registry of 18 row ids and 3 layouts; dry run proven by tripwire `claude` plus an in-process `subprocess` trap (sections Preflight and dry run, Validation Architecture) |
| HARN-02 | Preflight distinguishes SKIP, FAIL and BLOCKED with distinct exit codes, and a skipped row can never be read as a pass | Codes 10, 11, 12 already exist and 13 is the untested-version code; the test that pins the closed set of twelve constants must change only if a constant is added (recommendation: add none); SKIPPED filed under a visible folder name (Evidence filing) |
| HARN-05 | Each run records provenance: Claude Code version, `init.model`, skill and adapter digests, harness version, isolation mode, tool set, allowlist, and per-stage usage and `total_cost_usd` | Field-to-file table (Evidence filing); cost is cumulative across `--resume` so per-stage cost is a delta (Cost section) |
| HARN-07 | The `system/init` manifest (skills, permission mode, memory paths) is asserted every run, and the isolation mode in force (default or strict) is recorded per row after spike S1 decides which the matrix claims | `pc_spike.s1_evaluation` already asserts permission mode, model, skill, MCP, plugins, user names and three hook-log facts; a memory-path assertion is missing and must be added; isolation mode is `strict` |
| HARN-09 | Write-boundary and git-read-only assertions are mechanical: zero writes outside approved roots, no git mutation, derived from snapshots and traces rather than the model's claims | Check derivation, approved roots, Bash escape holes in the committed allowlist, seeded zero-token failure fixture (Write boundary section) |
| HARN-13 | Everything new lives under `tests/harness/`; `SKILL.md`, `references/` and `tests/fixtures/` are unchanged unless a rerun exposes a defect, and `SKILL.md` stays at or under 12,000 bytes | Base commit and the verification commands (Validation Architecture); no existing test enforces the 12,000-byte cap, so one must be added |
| EVID-04 | Filed rows follow the committed per-row file set (README, tools, digests, short and full traces, snapshots, measurements) plus `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt`, `harness-version.txt`, and are written with exclusive creation into a new dated folder | Per-file derivation table with gaps; stage then sanitize then gate then `promote` into `tests/evidence/rerun-<date>-<model>/` |
| EVID-05 | The harness never prints a verdict; each row ends with `Reviewer verdict: PENDING` and a reviewer checklist of mechanical facts | Neutral vocabulary rule for harness-authored files; checklist lines named after their source files; the original architecture note that proposed PASS/FAIL words in `mechanical-checks.md` is superseded |
| EVID-06 | A read-only structural comparer reports per-row differences between a rerun and `tests/evidence/publication-2026-10-20/` without editing either | Comparer algorithm and tree-digest proof via `pc_manifest` (Comparer section) |
</phase_requirements>

## Summary

Phase 2 left almost every building block this phase needs. `pc_flags.build_argv` already builds both the `--session-id` and the `--resume` form with a per-call `--max-turns` and `--max-budget-usd`; `pc_stream` parses and cross-checks structured denial signals; `pc_manifest`, `pc_measure`, `pc_runroot`, `pc_sanitize`, `pc_leakgate` and `pc_promote` cover snapshots, measurement, exclusive creation and the fail-closed filing path; `pc_spike` holds a materializer, the init and hook-log assertions, a spend ledger and `run_claude`. What is missing is the row layer on top: a two-ledger seed for row 1, a stage chain with correct cost accounting, trace and README renderers, the mechanical checks, a comparer, and the CLI. The committed row 1 evidence was produced by gitignored shell scripts under `runs/` (not reproducible by a stranger), so the real work of this phase is turning that procedure into tested Python that is proven end to end against a scripted fake `claude` before the one paid run.

Reading the committed row, the raw streams and the harness together surfaced eight facts that change the plan and are not in CONTEXT.md. Each is detailed in its section and has a mitigation: (1) the committed row 1 has no third stage and no s1 prompt file, and the s1 prompt text exists only in a gitignored script; (2) the `claude` on PATH is now 2.1.312, so the exact-match version gate answers 13 unless the driver can point at the retained 2.1.310 executable; (3) `total_cost_usd` is cumulative across `--resume`, so the stage cost of s2 is a delta and the Phase 2 spend ledger double counts the S2b call; (4) the committed `/preclear` turn took 49 turns, so "a small `--max-turns` per stage" cannot apply to s2; (5) adding the new evidence folder will change the corpus counts hard-coded in `test_allowlist.py`, and the README layout, exit-code and readme-hygiene tests constrain every new file; (6) the committed allowlist has bare `Write` and `Edit`, so D-03's containment is detected after the fact, not prevented; (7) the leak gate flags the shared runs-root parent folder unless the sanitizer is given extra mappings; (8) a stream denial is expected in row 1 (the committed run had nine), which collides with the HARN-06 wording "fails the row" unless denials are reported as facts.

**Primary recommendation:** Build the row layer as four small `pc_` modules plus tests (registry and CLI, row 1 seed and stage chain with checks and a new matrix spend ledger, evidence renderers and filer, read-only comparer), prove all of it against a scripted fake `claude` that also performs the seeded out-of-root write, run the driver's own `--dry-run` as the pre-spend gate, then spend once: stage caps of 0.30 / 1.30 / 0.40 USD (sum 2.00), `--max-turns` 15 / 60 / 15, pointed at the retained 2.1.310 executable by an explicit `--claude` path, with every pre-spend refusal (destination name free, sanitizer built, deny entries obtained, runs root accepted, budget flag present) evaluated before the first token.

## Critical Findings That Change The Plan

| # | Finding | Evidence | What the plan must do |
|---|---------|----------|-----------------------|
| C1 | Committed row 1 holds no s3 files and no s1 prompt file; D-04's "committed work-turn instruction" is not committed anywhere in tracked files | `find` of the row folder lists no `s3-*`, `resume-line.txt`, `session-resume.id` or `s1-work-prompt`; `grep -r "Implement only step 2"` over tracked files returns nothing; the text exists at `runs/pub-lib.sh:109`, `runs/pub-env.sh:86`, `runs/pub-plain.sh:37` (gitignored) | Commit the s1 prompt as a data file under `tests/harness/data/`; accept that the comparer will list s3 files and `s1-work-prompt.md` as present on the new side only (D-07 says list, never judge) |
| C2 | The `claude` on PATH is 2.1.312; `TESTED_VERSIONS` is exactly `("2.1.310",)`; 2.1.310 still exists as an executable in the installer's versions folder (also 2.1.307, 2.1.309, 2.1.311) | `ls -l` of the PATH symlink and of the versions folder this session; [VERIFIED: tests/harness/pc_flags.py:38] `TESTED_VERSIONS: Tuple[str, ...] = ("2.1.310",)` | Driver option `--claude <absolute path>` that feeds preflight, argv and `binary_defines`; `pc_preflight.find_claude` only searches directories by the name `claude`, so it needs a small explicit-path extension; do not rerun spikes to widen the set in this phase |
| C3 | `total_cost_usd` and `modelUsage` are cumulative across a resumed session; `usage` and `model_usage_since_last_result` are per call | s2 fixture line 23: `"total_cost_usd": 0.057689300000000006`; s2b fixture line 4: `"total_cost_usd": 0.060297300000000005` and `"costUSD": 0.002608` under `model_usage_since_last_result`; 0.057689300000000006 + 0.002608 = 0.060297300000000006; cumulative `inputTokens` 16 = 14 + 2 | Row total = `total_cost_usd` of the s2 result + `total_cost_usd` of the s3 result (s1 is inside s2); stage cost of s2 = s2 total minus s1 total (or the `model_usage_since_last_result` sum); the ledger must record deltas |
| C4 | The committed s2 stage took 49 turns; across 21 private raw s2 streams on another model, s2 took 11 to 45 turns | committed `s2-preclear-trace.md` line "Turns 49."; table in the Cost section | `--max-turns` for s2 must be about 60; "small" applies to s1 and s3 only; a turn cap hit mid-checkpoint leaves a half-written state and wastes the spend |
| C5 | `test_allowlist.py` pins the corpus to 336 calls, 32 traces, 22 folders and a 47/34/6 refusal split by walking all of `tests/evidence`; the new folder adds traces | `pc_allowlist.load_trace_calls` walks `tests/evidence` for every `*full-trace.md` that has a `tools.txt` beside it; `test_allowlist.py:252-264` asserts the numbers | Scope the loader to the publication folder (or update the numbers and review the new corpus entries) in the same plan that files the folder |
| C6 | Bare `Write` and `Edit` in the allowlist let the model write anywhere on disk; D-03's "nothing can leave the scratch project" is not enforced by the binary | `BASELINE_ALLOWED_TOOLS` starts `"Read", "Write", "Edit", "Glob", "Grep"`; the committed trace has a `Write` to the auto-memory folder, which is outside the project working directory | Treat containment as detection: snapshot diff plus a trace scan of every `Write`/`Edit` `file_path` and every Bash absolute path |
| C7 | The leak gate refuses a sanitized capture that names the runs-root parent folder, because the default runs root starts with the shared users folder, which the `home-path-unix` pattern reads as a home folder named "Shared" | In-memory run this session: with only the run root mapped to `<run>`, text naming the runs root or its parent gave `('home-path-unix', 2)`; mapping the runs root and its parent to `<scratch>` gave no findings | Add the runs root and its parent to the sanitizer's caller map (token `<scratch>`) before any paid run |
| C8 | A row 1 run emits permission denials (nine `permission_denied` events in the committed raw stream) | Private raw stream `runs/pub-row1-wrong-binding/evidence/s2-preclear.jsonl`: `('system', 'permission_denied'): 9` | Report denials as counted facts with ids; do not let HARN-06's "fails the row" turn a fully paid run into a filed-nothing FAIL (Open Question 4) |

## Architectural Responsibility Map

This is a test harness, not a web application, so the tiers are the harness components. The rule that matters: only the stage runner may start `claude`; everything else is a pure function over bytes or files, which is what makes the zero-token proof possible.

| Capability | Primary tier | Secondary tier | Rationale |
|------------|-------------|----------------|-----------|
| Row and layout registry, `--list`, argument validation, `--dry-run` plan | Driver CLI (new `pc_` module) | Row registry data | The only code a stranger types; must start no process in dry-run, so it may not import the paid path at call time |
| Preflight states and exit-code mapping (SKIP, FAIL, BLOCKED, untested version) | Driver CLI | `pc_preflight`, `pc_exitcodes` | One mapping table; reuses the existing zero-token preflight |
| Run-root allocation, row seed (two ledgers, plan, config, wrapper, stub state, settings) | Fixture materializer (new, row 1 first) | `pc_runroot`, `pc_spike` helpers | Exclusive creation; copies `tests/fixtures/` and committed evidence setup files read-only |
| Stage chain s1, s2 (resume), s3 (new session), caps, timeouts, spend ledger | Stage runner (new) | `pc_flags.build_argv`, `pc_spike.run_claude` | The only paid path; cost and attempt accounting live here |
| Helper behaviour and call log | Stub plus wrapper (existing, unchanged) | Run-root `ckpt/` state | Test apparatus the model calls; the harness never calls the wrapper itself (driver-side calls go to the stub directly) |
| Init manifest assertions, hook-log audit | Assertion layer | `pc_spike.s1_evaluation`, `pc_stream.init_manifest` | Facts from `system/init` and the logger file; stream carries no hook events |
| Snapshots, git capture, write-boundary and git-read-only checks, helper-call correlation | Mechanical checks (new) | `pc_manifest`, `pc_stream`, `pc_mine.parse_log` | Derived from snapshots and traces, never from model text |
| Byte measurement of the checkpoint | Measurer (existing) | — | Runs on originals before sanitizing |
| Trace, README, checklist, usage and provenance files | Evidence renderers (new) | `pc_stream`, `pc_measure` | Harness-authored files use neutral vocabulary (no verdict words) |
| Sanitize, leak-gate, exclusive filing | Evidence filer | `pc_sanitize`, `pc_leakgate`, `pc_promote` | Fail closed; must pass `sanitizer.deny_entries()` to `promote` (WR-14) |
| Structural comparison with the committed row | Comparer (new, read-only) | `pc_manifest`, `pc_mine`, `pc_measure` | Opens both trees read-only; proves both unchanged by tree digest |

## Standard Stack

### Core (all in the repository; nothing is installed)

| Component | Version / location | Purpose | Why standard here |
|-----------|--------------------|---------|-------------------|
| Python | 3.9 floor; `/usr/bin` 3.9.6 and PATH 3.14.7 both present | All new code | Project constraint; `test_imports.py` parses every file with feature version 3.9 |
| `pc_flags` | `tests/harness/pc_flags.py` | `build_argv` (session-id or resume form), `build_env`, `build_allowed_tools`, `render_settings`, `check_version`, `format_budget` | The single pinned `claude -p` contract; tests keep README equal to it |
| `pc_spike` | `tests/harness/pc_spike.py` | `runs_root`, `materialize` pieces, `s1_evaluation`/`hook_entries`/`binary_defines`/`local_user_names`, `sanitize_to_data`, `scrub_volatile`, `run_claude`, `append_spend` pattern | Proven by two paid spikes and a fake-claude test rig |
| `pc_stream` | `tests/harness/pc_stream.py` | `parse_stream`, `result_summary`, `init_manifest`, `denial_report`, `tool_calls`, `tool_results` | Strict parser; Decimal costs; structured denial signals only |
| `pc_manifest` | `tests/harness/pc_manifest.py` | `tree_manifest`, `sha_txt_bytes`, `jsonl_bytes`, `write_snapshot`, `capture_git_status` | Byte-walk, filename-safe, never follows symlinks |
| `pc_measure` | `tests/harness/pc_measure.py` | `measure_file`, `format_report` | Same six sections and caps as the committed evidence |
| `pc_runroot` | `tests/harness/pc_runroot.py` | `allocate_run_root`, `exclusive_dir`, `write_exclusive` | `O_EXCL`, `O_NOFOLLOW`; no deletion |
| `pc_sanitize`, `pc_leakgate`, `pc_promote` | `tests/harness/` | Sanitize, gate, exclusive filing | Fail closed; counts only |
| `pc_mine` | `tests/harness/pc_mine.py` | `parse_log` and `parse_trace` readers for committed `wrapper-calls.log` and full traces | Already parses the committed shapes; the new renderers must emit the same shape |
| `pc_allowlist` | `tests/harness/pc_allowlist.py` | `split_compound`, `is_allowed`, `row_rules` | Annotation only; never a gate for the binary's decisions |
| `pc_testutil` | `tests/harness/pc_testutil.py` | `make_tripwire`, `make_fake_claude`, `minimal_env`, `git_env` | The proven zero-token double for `claude` |
| Stub and wrapper | `tests/harness/checkpoint_stub.py`, `checkpoint-wrapper` | The helper the model calls | Unchanged; the wrapper log is the executed-call record |
| Claude Code | exactly 2.1.310 (`TESTED_VERSIONS`) | System under test | Exact-match gate; the PATH binary is 2.1.312 (C2) |
| git | 2.50.1 | Fixture repo, read-only status capture | Already used with a hygiene environment |

### Alternatives considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| New matrix spend ledger | Extend `spike-spend.jsonl` and `CALLS` | The spike ledger is lifetime-capped (two attempts per call name, 5.00 USD total shared with the spikes) and its tests pin `CALLS`; a separate ledger leaves Phase 2 tests untouched and lets Phase 4 size its own cap |
| New row-seed function | Generalize `pc_spike.materialize` | `materialize` is pinned by the 12-test `MaterializeTests` class in `test_spike.py` (one ledger, bound; fixture project copied verbatim); a sibling function avoids touching them |
| `unittest.mock` trap on `subprocess` | Tripwire `claude` only | Use both: the tripwire proves no `claude` argv; the trap proves no process of any kind in dry-run |

**Installation:** none. Standard library only. `tests/harness/selftest` is the first command.

## Package Legitimacy Audit

No external package is installed or recommended by this phase, so the legitimacy gate has nothing to check.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System architecture diagram

```
 argv (--list | --row ID | --layout NAME | --all | --dry-run [--claude PATH] [budget flag])
   |
   v
 [Driver CLI] -- unknown id --> exit 2 (USAGE)
   |  --list --> registry table (3 layouts, 18 row ids, implemented flag) --> exit 0
   |  --dry-run --> plan (stages, sessions, caps, worst case) --> exit 0  [no process, no ledger write]
   v
 [Zero-claude gate, evaluated BEFORE any spend]
   runs root accepted? (home-folder / ancestor-instruction refusal) -- no --> BLOCKED (12)
   sources readable, destination name free, sanitizer built, deny entries obtained --> else FAIL (11)
   row precondition unmet --> SKIP (10), filed as SKIPPED
   |
   v
 [Preflight, real runs only]  claude path -> --version (exact 2.1.310) -> auth status (boolean only)
   untested version --> 13 | absent or logged out --> 12 | unusable answer --> 11
   |
   v
 [Spend guard]  reserve "launched" line (counts as the stage cap) under a file lock
   |
   v
 [Row seed]  run root: project/ (git repo, skill copy, plan, CLAUDE.md config: ledger A named)
                       ckpt/  (CKPT_HOME: ledgers A and B, session bound to B, roots registered)
                       wrapper/ (checkpoint, py, stub, empty calls.log)  auto-memory/  raw/  settings.json
   snap-0-setup, status-before, lint-before (driver calls the STUB directly, never the wrapper)
   |
   v
 [Stage chain]   s1: -p --session-id U1  (work prompt)           --> raw/s1.stdout  snap-1-after-work
                 s2: -p --resume     U1  (/preclear prompt)      --> raw/s2.stdout  snap-2-after-preclear
                 resume line = last fenced single line of s2 reply starting "Resume "
                 s3: -p --session-id U2  (resume line only)      --> raw/s3.stdout  snap-3-after-resume
     each stage: init assertions + hook-log audit; result -> usage delta; stop chain on non-success
   |
   v
 [Mechanical checks]  write boundary (snap diff + trace paths), git read-only (HEAD, refs, .git minus index),
                      ledger digests unchanged, helper calls (wrapper log vs tool_use), bytes vs cap, session ids
   |
   v
 [Evidence staging in the run root]  render traces, usage, README, checklist; measure ORIGINAL checkpoint first
   -> sanitize every file (caller map: run, auto-memory, runs root and parent -> <scratch>) -> leak gate
   -> promote(stage, tests/evidence/rerun-<date>-<model>, repo, deny_entries=sanitizer.deny_entries())  [exclusive]
   |
   v
 [Comparer, separate command]  tree digests of OLD and NEW  -> read-only diff report -> same digests re-computed -> exit 0
```

### Recommended project structure (all under `tests/harness/`; `data/` stays the only subfolder and holds non-code)

```
tests/harness/
├── pc_rows.py          # row and layout registry (ids from the 22 committed folders collapsed to 18 row ids), stage specs, caps
├── pc_matrix.py        # driver CLI: --list, --row, --layout, --all, --dry-run, --claude, preflight mapping, provenance
├── pc_row1.py          # row 1 seed (two ledgers), prompts loader, stage chain, snapshots (or split: pc_seed_rows.py, pc_stages.py)
├── pc_checks.py        # write boundary, git read-only, helper-call correlation, ledger-unchanged, session-id facts
├── pc_spend.py         # matrix ledger: file-locked reservation, delta accounting, per-row cap
├── pc_evidence.py      # trace and README renderers, usage.txt, provenance files, stage -> sanitize -> gate -> promote
├── pc_compare.py       # read-only comparer and tree digest
├── test_matrix_cli.py  test_row1_seed.py  test_stages.py  test_checks.py  test_spend.py
├── test_evidence.py    test_compare.py                      # one scripted fake claude shared via a test-support module
└── data/               # row1-s1-prompt.md, row1-s2-prompt.md (byte copy), ledger-A/B seeds, CLAUDE.md template, plan text
```

New files must each be named once in the README Layout list (`test_readme.py` enforces both directions) and every `data/` file must scan clean with the leak gate (`test_leakgate.assert_fixtures_clean`).

### Pattern 1: stage chain with delta cost accounting

**What:** Run s1 then s2 then s3 as three `claude -p` processes; parse each stdout with `pc_stream.parse_stream`; stop the chain at the first stage whose result subtype is not `success`.
**When to use:** every row with a resume.
**Example (shape only; names are proposals, constants are quoted from the repository):**

```python
# argv for the three stages (pc_flags.build_argv already supports both forms)
# [VERIFIED: tests/harness/pc_flags.py:300-368] signature: build_argv(claude_path, session_id, settings_path,
#   allowed_tools, max_turns, max_budget_usd, resume=False, include_hook_events=False, model=PINNED_MODEL)
s1 = pc_flags.build_argv(claude, U1, settings, tools, 15, "0.30")                 # --session-id U1
s2 = pc_flags.build_argv(claude, U1, settings, tools, 60, "1.30", resume=True)    # --resume U1
s3 = pc_flags.build_argv(claude, U2, settings, tools, 15, "0.40")                 # --session-id U2 (new uuid4)
# cost: s2.total_cost_usd already contains s1; row total = s2.total_cost_usd + s3.total_cost_usd  [DERIVED, finding C3]
```

### Pattern 2: wrapper log to `tool_use` correlation

**What:** the wrapper logs `<UTC second> CALL <argv, printf %q>` then `<UTC second> EXIT <n>` and nothing else (no session id). [VERIFIED: tests/harness/checkpoint-wrapper "calls.log one `<UTC second> CALL <argv, printf %q>` and one `<UTC second> EXIT <n>` per call"]. Correlate by order and argv, with two structured cross-checks from the stream:

1. Take the stage's Bash `tool_use` blocks in stream order (`pc_stream.tool_calls`). For each, split the command with `pc_allowlist.split_compound`; every part whose first word is the wrapper path is one *invocation*; record its argv with `shlex.split`.
2. Drop invocations whose tool_use id is in the denial set (`pc_stream.denial_report(events).union`), and invocations in a command that was refused as a whole.
3. The remaining invocation sequence must equal the stage's slice of the wrapper log (`pc_mine.parse_log`, line order, never timestamp order). The slice boundary is the line count of `calls.log` at the end of the previous stage (record it per snapshot).
4. Cross-check A (structured): each user event carries `tool_result_meta[].permission_decision`; executed calls show `"decision": "accept"` and no `non_execution_kind`; a refused call shows `"non_execution_kind": "user-rejected"` and `"decision": "reject"`. [VERIFIED: tests/harness/data/s2-stream.jsonl line 21 (the refused wrapper bind) and line 4 (accepted status)]
5. Cross-check B (time): the wrapper's second-resolution stamp must lie between the assistant event's `timestamp` (millisecond, `tool_use`) and the following user event's `timestamp`, give or take one second. [VERIFIED: s2 fixture `2026-10-26T07:23:40.342Z` then `2026-10-26T07:23:40.822Z` for the executed status call]

Report four counts, never a verdict: Bash calls naming the helper; helper calls executed (wrapper CALL lines); helper calls denied (single-part invocations in `permission_denials`); compound-command refusals that name the helper. The committed README counts only helper operations ("attempted 1, executed 1 (`status`), denied 0") and says compound refusals "are harness tool-policy events, not helper denials", while its trace footer counts six Bash calls naming the executable; the four counts reproduce both views.

### Pattern 3: stage, sanitize, gate, promote (one atomic filing)

Build the final tree (`README.md` plus `row1-wrong-binding/...`) in `<run>/stage/`, in the shape that will land in the repository. Sanitize each file with one `Sanitizer` instance (built before any spend), write it exclusively, then call `promote` once with `deny_entries=sanitizer.deny_entries()`. `promote` creates missing parent folders but refuses an existing destination, so one `promote` of the whole tree into `tests/evidence/rerun-<date>-<model>` gives D-05's exclusive creation and refuses a reused name. [VERIFIED: tests/harness/pc_promote.py:140 `def promote(stage, dest, repo_root, config_dir=None, deny_entries=None):` and `_check_destination`: "the destination already exists"]. Check `os.path.lexists(destination)` before the first spend, too (WR-05 pattern: refuse before money is gone).

### Pattern 4: three-state preflight with the existing codes

| State | Exit | Existing constant | Typical trigger in this phase | Files anything? |
|-------|------|-------------------|--------------------------------|-----------------|
| SKIP | 10 | `PREFLIGHT_SKIP` | row precondition unmet (row 7's chmod probe is Phase 4; row 1 has none) | yes: `SKIPPED` folder with reason |
| FAIL | 11 | `PREFLIGHT_FAIL` | fixture or harness source missing, malformed `--version`, unusable `auth status` | no |
| BLOCKED | 12 | `PREFLIGHT_BLOCKED` | no `claude`, not logged in, runs root under a home folder | no; prints the one-line fix |
| BLOCKED (version) | 13 | `VERSION_UNTESTED` | well-formed version outside the tested set | no; prints the one-line fix |

`pc_spike.HomeRefused` currently carries exit 2 (`USAGE`); D-10 lists "runs root under a home folder" under BLOCKED, so the driver must map it to 12 itself.

### Anti-patterns to avoid

- **Reusing `spike_preflight`:** it deliberately allows an untested build (the spikes create the tested set). The row runner must call the strict `pc_preflight.run_preflight`.
- **Reading reply text for denials, verdicts or counts:** only the two structured denial signals, `tool_result_meta` and the wrapper log.
- **Reading the checkpoint from sanitized copies:** measure originals in the run root first (EVID-01).
- **Adding an environment variable:** `test_readme.py` pins the switch table to exactly six names; use flags and injected callables.
- **Calling the wrapper from the driver:** driver-side state and `status-before`/`lint-before` go straight to the stub with `CKPT_HOME` set, so `calls.log` stays empty until the model's first call (the committed setup snapshot hashes an empty log: `e3b0c442...`).

## How The Committed Row 1 Was Actually Produced (research question 1)

The committed folder is `tests/evidence/publication-2026-10-20/row1-wrong-binding/` (20 top-level files plus three snapshot folders; 41 files in all). It was produced by gitignored shell scripts that still exist locally under `runs/` (`pub-lib.sh`, `pub-row.sh`, `pub-env.sh`, `pub-plain.sh`, `pub-measure.py`) and by a row-1-specific driver that was not preserved. A stranger cannot reproduce it, which is the reason this phase exists. What can be established:

- **Fixture.** `make_root` copied `tests/fixtures/bound-ledger/project/`, then deleted `thoughts/ledgers`, then wrote a three-step plan and a `CLAUDE.md` whose configuration block names ledger A and the logging wrapper, then `git init -b main` with one commit, then copied the skill into `project/.claude/skills/preclear/`. [VERIFIED: runs/pub-lib.sh:10-66] The plan text is exactly: `# Plan: widget-export`, blank line, `1. [x] Define the export columns (id, name).`, `2. [ ] Write the CSV exporter.`, `3. [ ] Add a test for empty input.` and I confirmed it reproduces the committed setup digest: `3ccf15ec14c70586d5c0c8d289c3a0b79211410bfffbf0a1e31c3fcfa3d335b8  project/thoughts/plans/2026-10-15-widget-export.md` [VERIFIED: `shasum -a 256` of that text this session equals row1 `snap-0-setup/sha.txt`].
- **Two ledgers.** Ledger A (`CONTINUITY_CLAUDE-widget-export.md`, named in the configuration) and ledger B (`CONTINUITY_CLAUDE-other-task.md`) were created in one ledger root with the real helper's `create ... --from initial-A.md --session SID`; the session was then bound to B. The scratch files `initial-A.md` and `initial-B.md` and the helper-state folder survive locally; their sanitized copies are the committed `snap-0-setup/*.md`. `status-before.txt` proves the binding: `session eace4601 → <repo>/<run>/ledgers/CONTINUITY_CLAUDE-other-task.md`. [VERIFIED: row1 `status-before.txt`; runs/pub-row.sh:39-41 shows the create, bind, status and lint sequence for the sibling rows]
- **Stage 1 (work turn).** One text-mode `claude -p` (no stream-json, so no usage and no cost were captured for it) with `--setting-sources project,local --settings <run>/scratch/settings.json --allowedTools <tools> --session-id <SID>`, prompt on stdin. The prompt text, from the only place it is written down: [VERIFIED: runs/pub-lib.sh:109] `Implement only step 2 of thoughts/plans/2026-10-15-widget-export.md for widget-export, using the CSV decision in the project's continuity ledger at $4. Keep functions small and pure. Do not run tests, commit, or start step 3. Leave the plan checkbox for checkpointing to reconcile. Keep the reply to three lines.` where `$4` is the ledger A path. That row 1 used this variant (not the plan-decision variant of `pub-env.sh`/`pub-plain.sh`) is inferred from `s1-work.out`, which says "CSV only per the ledger decision" and has three lines; the row 1 plan carries no decision line. `[ASSUMED]` (A2)
- **Stage 2 (`/preclear` turn).** `claude -p ... --resume <SID> --output-format stream-json --verbose < s2-preclear-prompt.md`. The prompt is the committed `s2-preclear-prompt.md`, 569 bytes, ending in one newline. [VERIFIED: `wc -c` and `od -c` this session] It opens with `/preclear` and gives the JSON-default correction.
- **Stage 3.** None in row 1. Rows 8a, 8b, 8c, 9, 10, 11 and 12 have it: the resume line is extracted from the s2 result, then `printf '%s' "$RL" | claude -p --session-id <new uuid> --output-format stream-json --verbose`; files `resume-line.txt`, `session-resume.id`, `s3-resume.jsonl/.err/.exit`, `s3-resume-trace.md`, `s3-resume-full-trace.md`, `snap-3-after-resume/`. [VERIFIED: runs/pub-env.sh:104-108; row8b folder listing] CONTEXT D-02 says the committed evidence recorded the read-only fresh resume for row 1; it recorded it for those other rows and for the layouts, not for row 1 (finding C1). The discussion log shows bokiko chose "Yes, include it" explicitly, so D-02 stands.
- **Flags and tools.** Committed argv carried only `-p --setting-sources project,local --settings --allowedTools --session-id/--resume [--output-format stream-json --verbose]`; no `--model`, `--permission-mode`, `--max-turns`, `--max-budget-usd`, `--strict-mcp-config` or `--effort`, no `CLAUDE_CONFIG_DIR`, and the run roots were under the repository (so ancestor instruction files from the user's folders were loaded). The tool set was `BASE_TOOLS,Bash(<wrapper>:*),Bash(env:*)` with a bare wrapper prefix. [VERIFIED: runs/pub-lib.sh:107-118; row1 `tools.txt`] The new run therefore is a new baseline (D-06), not a replication.
- **Wrapper.** An 8-line bash script that appended `<UTC second> CALL <argv, printf %q>` to `calls.log` and `<UTC second> EXIT <rc>` after delegating unchanged to the real helper. [VERIFIED: row1 `wrapper-checkpoint.sh`] The committed log for row 1 is two lines: `... CALL status` and `... EXIT 0`.
- **Snapshots.** `snap()` at `runs/pub-lib.sh:95`: `ledgers-ls.txt`, copies of `ledgers/*.md`, a copy of `project/.preclear` as `preclear/`, a copy of `auto-memory/`, `status.txt` (`git status --porcelain --untracked-files=all`), `sha.txt` (`shasum -a 256` over `ledgers helper-state project/.preclear project/thoughts project/CLAUDE.md project/CLAUDE.local.md auto-memory wrapper`), `bindings-ls.txt`. `sha.txt` line shape: 64 hex, two spaces, run-root-relative path, for example `2bfb831eb6914381861dfe91338bd017f28fd8e8978fa2a5c2128f993946498e  ledgers/CONTINUITY_CLAUDE-widget-export.md`. Row 1 snap-0 lists nine paths: bindings file, `helper-state/ledger-roots.json`, `ledgers/.checkpoint-log.jsonl`, two ledgers, `project/CLAUDE.md`, the plan, `wrapper/calls.log`, `wrapper/checkpoint`. The first `shasum` digest of `wrapper/calls.log` at setup is `e3b0c442...` (the empty file). Sanitized ledger copies in the snapshot are 735 and 662 bytes while the originals measured 829 and 756 (the path tokens are shorter).
- **Measurements.** `runs/pub-measure.py` splits on `## ` lines and prints `total N bytes (cap 4096), sha256 H` then `- <section>: N` lines on the ORIGINAL checkpoint; `measurements.md` adds one `ledger file NAME: N bytes sha256 H` line per file in the ledger folder and an `auto-memory files: [...]` list. [VERIFIED: runs/pub-measure.py; row1 `measurements.md`]
- **`digests.txt`.** `shasum -a 256` over the installed `SKILL.md`, the two reference files then present, the real helper, its dist bundle and the wrapper, with paths sanitized. [VERIFIED: runs/pub-lib.sh:58-66 `finish_project`; row1 `digests.txt`]
- **`session.id`.** Lowercase UUID (`uuidgen | tr`), one line. [VERIFIED: runs/pub-row.sh:37] It is the one session shared by s1 and s2.
- **Traces.** `s2-preclear-trace.md` is a short bullet list of tool calls, then a footer (`Turns 49. Write/Edit calls 8: [...]. Bash calls naming the configured executable: 6. Results flagged refusal/denial/EACCES/blocked ...: 8.` and `Usage: input 484, cache creation 31672, cache read 844165, output 16301.`), then `## Final reply` with the raw reply. `s2-preclear-full-trace.md` starts with `raw transcript sha256 89a5fca6..., 257861 bytes (retained privately in the run root)`; I confirmed both numbers equal the size and digest of the private raw stream `runs/pub-row1-wrong-binding/evidence/s2-preclear.jsonl` (the stage's whole stdout). Then `Calls 48; results flagged as refusal/denial/permission/EACCES: 7.` and one `### N. Tool (tool_use id)  ERROR  REFUSAL/DENIAL` block per call: Bash, Write and Edit with full command and result, Read, Glob and Grep as one line with the result length.
- **The committed resume line.** The s2 final reply ends with one fenced single line: `Resume widget-export from "<repo>/<run>/project/.preclear/widget-export/checkpoint.md" — main @ 7793e5e — step 2 done untested; JSON-default diff pending`. SKILL.md Step 5 fixes the shape: `Resume <task-slug> from "<absolute checkpoint path>" — <branch|detached|unborn|no-git> @ <short-sha|n/a> — <one-phrase state>`. [VERIFIED: row1 `s2-preclear-trace.md` last lines; SKILL.md:175-186]
- **Model and version.** The committed README names neither. The private raw streams show the committed matrix ran Claude Code 2.1.304 on `claude-opus-5-5` (31 streams) and, for row 1's s2 stage alone, `claude-fable-5-1` [VERIFIED: init events of the files under `runs/pub-row*/evidence/`, counted this session]. Not filed anywhere, so D-06's "recorded no model" is true of the committed folder; it is one more reason the new run is not a replication.

### Per-file derivation table (deliverable for question 1)

"Module today" names what Phase 2 provides; "Gap" is what must be written. Files marked NEW are not in the committed row 1.

| File | How derived | Phase 2 module that helps today | Gap and notes for the new run |
|------|-------------|---------------------------------|--------------------------------|
| `README.md` | hand-written after the run (Setup, Result, Observation, Codex verdict); headings: H1 only | none | Generator: setup sentence, stage table, mechanical facts, checklist, last line `Reviewer verdict: PENDING`; heading set will differ (listed by the comparer, not judged) |
| `claude-version.txt` | `claude --version` banner, one line | `pc_preflight._run`, `pc_spike.detect_version` (returns only X.Y.Z) | Keep the raw banner line `X.Y.Z (Claude Code)` from the preflight call |
| `model-id.txt` NEW | init event `model` | `pc_stream.init_manifest(events)["model"]` | Assert equal to `pc_flags.PINNED_MODEL` in every stage, write once |
| `isolation-mode.txt` NEW | spike S1 decision | `pc_flags.ISOLATION_CLAIM` | One word `strict` first line, then the setting sources and the claim sentence; no home path in the claim |
| `harness-version.txt` NEW | none committed | `pc_manifest.tree_manifest` over `tests/harness`; `git rev-parse` read-only | Tree digest of the harness folder, full HEAD, harness-tree-clean flag (see Evidence filing); never `git describe` output with a path |
| `digests.txt` | `shasum -a 256` of skill, adapter files, helper, wrapper | `pc_manifest` hashing | Writer over `SKILL.md`, `references/*.md` (three files now), the stub, the wrapper copy; token paths; `<helper-dist>` has no analogue |
| `fixture-CLAUDE.md` | the project `CLAUDE.md` after path fill | `pc_spike._fill_configuration` | The frozen fixture `CLAUDE.md` has no intro paragraph and no read-only bootstrap sentence; the committed rows used a richer file written by `claude_md()`; use the committed row's `fixture-CLAUDE.md` as the template (see Seeding) |
| `tools.txt` | the comma-joined allowlist | `pc_flags.build_allowed_tools` (40 rules) | Differs from committed: committed 28 rules with a bare wrapper prefix; new has the 33-rule baseline plus seven per-verb wrapper rules. Listed by the comparer |
| `s1-work.out`, `s1.err`, `s1.exit` | stdout text, stderr, `exit N` | `run_claude` keeps raw `.stdout/.stderr`; `pc_stream.result_summary` | `s1-work.out` = result text plus newline from the s1 result event; `s1.exit` = `exit <rc>` text; sanitize `s1.err` |
| `s1-work-prompt.md` NEW | not committed | none | Data file; `$LEDGER` placeholder filled with the ledger A path then sanitized. Records any D-04 preamble |
| `s2-preclear-prompt.md` | copy of the prompt bytes | none | Data file byte-identical to the committed file (test compares digest) |
| `s2-preclear.err`, `s2-preclear.exit` | as s1 | same | same |
| `s2-preclear-trace.md` | short trace renderer | `pc_stream.tool_calls`, `result_summary` | Renderer for the footer and `## Final reply`; needs `usage` token fields (not in `result_summary`) |
| `s2-preclear-full-trace.md` | full trace renderer | `pc_stream.tool_calls`, `tool_results` (lengths only), `denial_report`; `pc_mine.parse_trace` reads the shape | Renderer with full result content, ERROR and REFUSAL/DENIAL flags, header with raw stdout sha256 and size; must match `_TRACE_HEAD` and `_TRACE_BODY` so existing readers keep working |
| `s3-resume-trace.md`, `s3-resume-full-trace.md`, `resume-line.txt`, `session-resume.id`, `s3-resume.err`, `s3-resume.exit` NEW to row 1 | as rows 8 to 12 | same renderers; resume-line regex from `runs/pub-env.sh:71` | One extractor function; `resume-line.txt` holds the sanitized line plus newline while the prompt sent has no trailing newline |
| `session.id` | one UUID line | `pc_flags._check_session_id` | `uuid.uuid4()` canonical form |
| `settings.json` (rows 8 to 12, not row 1) | the `--settings` file | `pc_flags.render_settings(auto_memory, None)` shape | File it without the hooks entry so it equals the committed shape (`autoMemoryDirectory`, `autoMemoryEnabled`) |
| `lint-before.txt`, `status-before.txt` | `lint` and `status --session SID` of the helper before stage 1 | the stub verbs (`status`, `lint`) | Driver calls the stub directly with `CKPT_HOME`; keep stdout only (the stub's brand goes to stderr) so the three-line shape matches |
| `measurements.txt`, `measurements.md` | `pub-measure.py` on the original checkpoint | `pc_measure.measure_file`, `format_report` | Text shape differs (`total 3494/4096 bytes` vs `total 3494 bytes (cap 4096)`; `- Section: 734/800` vs `- Section: 734`); inventory lines for ledgers and memory are new code; locate the checkpoint by globbing the fallback folder; no file found means the line reads UNCONFIRMED |
| `snap-0-setup`, `snap-1-after-work`, `snap-2-after-preclear` (+ `snap-3-after-resume` NEW) | `snap()` | `pc_manifest.tree_manifest`, `write_snapshot`, `capture_git_status` | Choose roots and prefixes (`ckpt/...` replaces `helper-state/` and `ledgers/`), copy the ledgers, `preclear/` and `auto-memory/` trees, write `*-ls.txt`; `write_snapshot` also writes `manifest.jsonl` (new-only file); filter `.git`, `raw`, skill folder and the machine-specific `wrapper/py` and `wrapper/stub` |
| `wrapper-calls.log` | copy of `wrapper/calls.log` | wrapper writes it; `pc_mine.parse_log` reads it | Copy after the last stage (the log is cumulative); sanitize paths in argv |
| `wrapper-checkpoint.sh` | wrapper source | byte copy of `tests/harness/checkpoint-wrapper` | No paths inside; digest it in `digests.txt` |
| `mechanical-checks.md`, `usage.txt` NEW | none | `pc_stream`, `pc_checks` (new) | Neutral vocabulary; see Evidence filing |

### Session shape (research question 2)

| Stage | argv builder call | Prompt | Result handling |
|-------|-------------------|--------|-----------------|
| s1 | `build_argv(claude, U1, settings, tools, 15, "0.30")` gives `--session-id U1` | row 1 s1 prompt on stdin | init assertions; result delta cost; `s1-work.out` |
| s2 | `build_argv(..., 60, "1.30", resume=True)` gives `--resume U1` (no `--session-id`) | committed s2 prompt bytes | spike S2b proved `--resume` keeps the session id: init and result `session_id` equal the requested id. [VERIFIED: tests/harness/data/spike-findings.md "S2b init.session_id equals the requested id: yes"] |
| s3 | `build_argv(..., 15, "0.40")` with a new `uuid4` | the resume line only | read-only facts: Write/Edit count, checkpoint digest unchanged |

`pc_spike.run_claude(argv, env, cwd, prompt, timeout, raw_dir, stem)` already runs any of these (prompt to stdin, never argv; raw `.stdout` and `.stderr` kept by exclusive creation). Additions needed: a stage record (returncode, timed_out, wall seconds) for `.exit` files; per-stage `usage` extraction (the four token categories) and `model_usage_since_last_result`; calling it with `cwd` = the project folder for all three stages (a resumed session must start in the same working directory).

### Seeding row 1 (research question 3)

Today `pc_spike.materialize` builds: project (fixture copied verbatim, config block filled by `_fill_configuration`, git repo on `main`, skill copies), wrapper folder (`checkpoint` 0755, `py`, `stub`), `ckpt/` with the committed row 2 ledger registered and bound to the session by the stub's `bind`, `auto-memory`, `raw`, `settings.json` (with the logger hook when `audit_hook`). [VERIFIED: tests/harness/pc_spike.py:464-583] Row 1 needs a sibling function. The deltas:

1. **Two ledgers, one bound.** Write ledger A and ledger B into `ckpt/ledgers/` (sources: the committed `row1-wrong-binding/snap-0-setup/CONTINUITY_CLAUDE-widget-export.md` and `...-other-task.md`, read-only, the same pattern as `ROW2_SETUP`), then `stub bind --ledger <B> --session U1`. `bind` registers the ledger folder as a root, so ledger A (same folder) is also readable by `show --ledger`. The configuration's `ledger:` value names A. Both ledgers start with `# CONTINUITY` so stub `lint` reports `ledger lint OK` like the committed `lint-before.txt`.
2. **Do not copy `thoughts/ledgers`.** The frozen fixture project holds `thoughts/ledgers/CONTINUITY_CLAUDE-widget-export.md`; `materialize` copies it and the committed rows deleted it. A stale third ledger in the project would confuse the model. `_copy_tree_with` has no exclusion parameter, so the sibling function needs one.
3. **Add the plan file** with the exact committed text above.
4. **Render `CLAUDE.md` from the committed row 1 `fixture-CLAUDE.md`** (it carries the "Resuming from this ledger requires no binding..." sentence the bound-ledger first run showed was necessary), replacing the four tokenised values.
5. **Ledger text paths.** The committed ledger copies contain the literal token text `<repo>/<run>/project`. Copied verbatim, the model reads token text where the original had a real path; the bound-ledger README records the same kind of harness artifact ("the harness had reused the other run's initial block, whose Goal named the other project path"). Recommend replacing `<repo>/<run>/project` with the real project path in the seeded bytes; either way the digest differs from the committed one, which is expected. (Open Question 6)
6. **Create an empty `wrapper/calls.log`** at setup so snapshot 0 lists it like the committed setup digest.
7. **Audit hook on:** `audit_hook=True` so `raw/hooklog.jsonl` exists; the hook log is the only source of the instruction audit (the stream carries no hook events).
8. **Bind id.** The stub's session identity comes from `--session` or `CLAUDE_CODE_SESSION_ID`; the model's Bash inherits the variable, which is how the stub knows the session. [VERIFIED: tests/harness/checkpoint_stub.py docstring "Session identity: --session (before or after the verb), else the CLAUDE_CODE_SESSION_ID variable, else exit 2"] STACK research reproduced on 2.1.306 that a resumed run reports the same `session_id` and the Bash tool's `CLAUDE_CODE_SESSION_ID` equals it. [CITED: .planning/research/STACK.md:35] The 2.1.310 spike did not observe it through the wrapper (findings: "the resumed Bash tool reporting the same session through the wrapper's status was not observed"), so add a mechanical fact: the first `status` result in s2 must start with `session <U1 first eight characters>` and name ledger B.
9. **Brand line.** The stub prints a one-line brand on stderr, and the model sees it in tool results. 02-RESEARCH assumption A9 said row 1 would show whether this changes behaviour. [CITED: .planning/phases/02-model-free-foundation-and-stub/02-RESEARCH.md:614] Record it as a difference in the README note; nothing to fix.

## Preflight States, Exit Codes And The Dry-Run Proof (research question 4)

Reserved today, verbatim: [VERIFIED: tests/harness/pc_exitcodes.py:34-45]

```
OK = 0
USAGE = 2
PREFLIGHT_SKIP = 10
PREFLIGHT_FAIL = 11
PREFLIGHT_BLOCKED = 12
VERSION_UNTESTED = 13
LEAK_REFUSED = 14
SCANNER_ERROR = 15
RUNROOT_COLLISION = 16
PROMOTE_REFUSED = 17
BUDGET_REFUSED = 18
DENIAL_FOUND = 19
```

- **No code is free in the harness range.** `test_preflight.py` pins the harness constants to exactly these twelve and requires every non-OK, non-USAGE code to lie in 10 to 19; `test_exitcode_agreement.py` checks the same range against 0 to 6, 64, 70, 71 and 124 to 143; README's exit table is rendered from the constants. [VERIFIED: tests/harness/test_preflight.py:34-48,72; tests/harness/test_exitcode_agreement.py (`test_harness_codes_avoid_the_stub_range_and_the_shell_signal_range`)] A new constant means editing two tests and the README table in the same plan. **Recommendation: add none.** SKIP, FAIL and BLOCKED already have three distinct codes (10, 11, 12) and 13 is the version-specific BLOCKED. The existing meanings in `pc_exitcodes.describe` ("PREFLIGHT_FAIL: claude answered with an unusable result") should be widened only if the planner also routes harness-fixture failures to 11; if so edit `describe` and the README table together.
- **Existing producers.** `pc_preflight.run_preflight` already returns SKIP (via an injected `row_check` returning a reason), FAIL, BLOCKED and UNTESTED with the codes above and one line `STATE: message`. [VERIFIED: tests/harness/pc_preflight.py:106-178] `pc_spike.HomeRefused` maps to 2 and `SpikeError` to 11; the new driver must map "runs root under a home folder" to 12 (D-10), "fixture or source missing" to 11, and unknown `--row` or `--layout` to 2.
- **One-line fixes.** D-10 requires BLOCKED to print "the one-line fix from the README". `pc_preflight._login_instruction` already prints `the harness is not logged in; run this once, then rerun: CLAUDE_CONFIG_DIR=<dir> claude auth login`. Add a README "BLOCKED fixes" list with one line per BLOCKED cause (no claude, not logged in, untested version with the `--claude` hint, runs root under a home folder) and a test that each message equals its README line. The README may not contain absolute paths, `USD` or a dollar figure (`test_readme.py`).
- **The 2.1.312 problem (C2).** With the PATH `claude` the real preflight answers 13. The driver needs `--claude <absolute path>`. `pc_preflight.find_claude(search_path, name)` only does `shutil.which(name, path=...)`, so either extend `run_preflight` with an explicit `claude_path` parameter or have the driver create a one-link shim folder under the harness home. `build_argv` already takes the claude path and `pc_spike.binary_defines(os.path.realpath(claude), ...)` scans that file, so the same path serves every use.

### Dry run: how to prove "no `claude` process and no usage recorded"

1. **Tripwire at the CLI.** Put `pc_testutil.make_tripwire(dir)` first on PATH and pass it as `--claude` too; run `--dry-run --row row1-wrong-binding` and `--dry-run --all`; assert exit 0 and `pc_testutil.read_tripwire(dir) == []`. This is the pattern `DryRunTests` in `test_spike.py` already uses (setUpClass builds a tripwire, `run_ok` asserts the tripwire log is empty). A tripwire logs even `--version`, so a dry run must not run the preflight probes.
2. **In-process trap.** Call `pc_matrix.main([...,"--dry-run"])` under `unittest.mock.patch("subprocess.Popen", side_effect=AssertionError)` (`subprocess.run` calls `Popen`); proves no process of any kind (git, stub, claude).
3. **No usage recorded.** Point the harness home at an empty temp folder; assert it still does not exist after the run (existing test `test_a_dry_run_needs_no_claude_and_creates_nothing` does exactly this), or that the matrix ledger and `auth-probes.jsonl` are byte-identical.
4. **Via the shim.** `selftest` already removes every directory holding an executable `claude` from PATH and refuses to start if one remains; the dry-run tests run inside that.
5. **What dry run prints.** Per row: stage count and session count (row 1: 3 stages, 2 sessions, because s1 and s2 share one), per-stage `--max-turns` and cap, the worst case (sum of caps) and the allowlist length; `pc_spike.describe_call` is the model (role tokens, no real path). For `--all`: only implemented rows are counted and the rest are listed as not implemented.
6. **Exercising the three states without `claude`.** The claude-free gate (runs root, sources, destination name, sanitizer) can answer 12 and 11 in a dry run without a process. SKIP needs a registry row whose precondition callable returns a reason: add a test-only row injected through the registry function parameter (no environment variable, because the switch table is closed). The `claude`-dependent BLOCKED causes (absent, logged out, untested version) are tested through the real path with `pc_testutil.make_fake_claude` doubles, as `test_preflight.py` does. How literally D-10's "`--dry-run` exercises all three" must be read is Open Question 3.
7. **Paid-run refusal by default.** `--row` without `--dry-run` would spend. Recommend requiring an explicit budget flag on real runs (value must be at least the printed worst case or the run is refused with `BUDGET_REFUSED` 18); absent the flag, print the plan and exit 18. This costs nothing, uses an existing code, and makes accidental spend impossible. (Open Question 5)

## Evidence Filing (research question 5)

**Folder.** `tests/evidence/rerun-<UTC date>-<model id>/` (for example the model id `claude-sonnet-5-5` from `PINNED_MODEL`, taken from `init.model` after asserting equality). Destination preconditions are evaluated before the first spend: name does not exist (`lexists`), parent `tests/evidence` is a real folder, and `pc_promote._check_destination` rules hold. The date is computed once at start and reused.

**File set per row (target).** The committed 20 top-level files, minus the ones no longer produced, plus: `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt`, `harness-version.txt` (EVID-04); the s3 set; recommended `s1-work-prompt.md` and `settings.json`; four snapshot folders. Each snapshot folder carries `sha.txt` and also `manifest.jsonl` because `pc_manifest.write_snapshot` writes both; the choice to promote both is open from Phase 2 (02-03 summary). [CITED: .planning/phases/02-model-free-foundation-and-stub/02-03-SUMMARY.md:260] Promoting both is harmless (ASCII JSON lines) and the comparer lists `manifest.jsonl` as new-only.

**Top-level folder README (D-06).** Written by the harness into the stage root: names the run a new baseline on the pinned model and build, states the row total and the run total of cost (quoted from `usage.txt`), and states it is not a replication of 2026-10-20 because that run recorded no model; also lists the other differences (Claude Code 2.1.310 versus 2.1.304, the pinned flag set, the stub instead of the real helper, per-verb allowlist, run roots outside the home folder, strict isolation). It must say the committed folder stays the reference. It must not name the owner's login (the sanitizer rewrites it to `<user>` and the gate refuses it), so write "the reviewer".

**Row README (D-09).** Setup paragraph, stage table (session ids, exit codes, turns, subtype), then mechanical facts one per line with the source file in parentheses, then a blank-box checklist, and the last line `Reviewer verdict: PENDING`. Suggested fact lines, each from a named file:

- helper calls attempted, executed, denied, and compound refusals naming the helper (`wrapper-calls.log`, `s2-preclear-full-trace.md`)
- ledger A, ledger B, bindings file and registry digests: setup versus after each stage (`snap-*/sha.txt`)
- writes outside approved roots: count and paths (`snap-*/sha.txt`, `s*-full-trace.md`)
- git mutations: HEAD, refs and git-directory digest before and after (`snap-*/status.txt`, trace scan)
- checkpoint bytes versus cap: total and per section, actual/cap (`measurements.txt`)
- session ids per stage and whether each init and result reported the requested id (`session.id`, `session-resume.id`)
- cost and turns per stage (`usage.txt`)
- s3: Write/Edit calls and checkpoint digest before and after (`s3-resume-full-trace.md`, `snap-2-after-preclear/sha.txt`, `snap-3-after-resume/sha.txt`)

**Vocabulary rule (EVID-05, SC4).** No harness-authored file may contain a verdict. Define "harness-authored" as every file except model-authored content (final replies inside traces, `s1-work.out`, the model's plan, memory and checkpoint files in snapshots, and `.err` files). Write facts as `name: value` and booleans as `yes` or `no`; never `pass`, `passed`, `fail`, `failed`, `accepted`. A test scans the harness-authored files with that word list (and `Reviewer verdict: PENDING` must be the last line of each row README). Two traps: `describe_s1` prints `pass` and `FAIL` words (stdout only, never filed, but do not reuse its strings in files), and the early architecture research (`.planning/research/ARCHITECTURE.md`, component 10) proposed PASS/FAIL/UNCONFIRMED in `mechanical-checks.md`; EVID-05 supersedes it, UNCONFIRMED may stay as a state for something that could not be measured (acceptance harness rule: "A measurement the model could not take stays `UNCONFIRMED`").

**Provenance fields to files (HARN-05, SC2 "non-empty in every field").**

| Field | File | Source |
|-------|------|--------|
| Claude Code version | `claude-version.txt` | preflight banner |
| `init.model` | `model-id.txt` | init event, equal to the pinned id in every stage |
| skill and adapter digests | `digests.txt` | sha256 of `SKILL.md` and `references/*.md` (the adapter is `checkpoint-v1.md`) |
| harness version | `harness-version.txt` | see below |
| isolation mode | `isolation-mode.txt` | `strict` (+ setting sources) |
| tool set | `mechanical-checks.md` "Init manifest" block (names and count of `init.tools`) | init event; 27 names on 2.1.310 [VERIFIED: tests/harness/data/spike-findings.md "tools: 27 names"] |
| allowlist | `tools.txt` | `build_allowed_tools` |
| per-stage usage and `total_cost_usd` | `usage.txt` | result events |

**Harness version.** Recommended content, three lines and no path: the sha256 of `pc_manifest.sha_txt_bytes(tree_manifest("tests/harness"))` (a digest of every harness file, tests and data included, `__pycache__` excluded), the full `git rev-parse HEAD`, and `harness-tree-clean: yes|no|unknown` from a read-only `git status --porcelain -- tests/harness`. Why not `git describe`: a fresh clone has no tags (`--always` gives only a short sha), and a dirty working tree is invisible to it. Why not a constant: it drifts silently. Run the paid row from a committed clean tree so the line is reproducible.

**Using `promote` correctly (WR-14).** After sanitizing, call `pc_promote.promote(stage, dest, repo_root, deny_entries=sanitizer.deny_entries())`. The gate CLI and `promote` defaults hold no login by design. Build the `Sanitizer` before any spend (WR-12), map `SanitizerError` to a pre-spend refusal, and add the caller map entries: run root to `<run>`, auto-memory to `<auto-memory-root>`, and the runs root and its parent to `<scratch>` (C7). Test that fails when the runner promotes without the entries: inject `Sanitizer.from_machine(repo, extra_map, sources=Sources([...], "<synthetic login>", ...))` with a synthetic login (the pattern in `test_sanitize.py`/`pc_seeds`), stage a file holding the synthetic login in a form the sanitizer would have replaced, assert the runner's call carries the entries and `promote` returns 14; and as the negative control assert that the same bytes promoted with `deny_entries=None` are accepted, so the test can tell the two apart. [VERIFIED: tests/harness/pc_promote.py:140,171 and 02-REVIEW.md WR-14]

**`SKIPPED` filing.** A SKIP writes `tests/evidence/rerun-<date>-<model>/SKIPPED-<row id>/README.md` holding the reason in neutral words (no verdict vocabulary); the folder name starts `SKIPPED-` so it is visible in a listing. A FAIL or BLOCKED files nothing (D-10); the run root stays (raw bytes are never deleted).

**`harness/README.md` constraints for the Phase 3 additions.** Keep the first fenced command `tests/harness/selftest`; keep headings in the order Run this first, Environment knobs, The stub, Exit codes, Layout, Limits (new sections may sit between, not reorder them); the Spike spend section must stay digit-free; the file may not contain `USD`, a dollar figure, an absolute or home path, a host name, an email, or a package-manager command; every new file is added to Layout in the plan that creates it (`PENDING_SPIKE_FILES` exists only for files named before they exist; avoid it by editing the README in the creating plan, and give README edits a single owner per wave because `parallelization` is on). The measured cost therefore goes in the evidence README and the SUMMARY, not in the harness README (Phase 4's RERUN-05 will need to relax that test).

## Read-Only Comparer (research question 6)

**Input and output.** `pc_compare.py --old <tests/evidence/publication-2026-10-20> --new <tests/evidence/rerun-...> --row row1-wrong-binding` prints a report; exit 0 whenever both trees were readable; exit 2 for an unreadable tree or bad usage (precedent: `pc_measure`, `pc_stream check` and `pc_manifest` all return 2 for an unreadable input). It never prints a per-row PASS or FAIL (D-08, EVID-05).

**What it compares (D-07), all mechanically:**

1. **File sets.** Relative paths under the row folder, each side, set differences both ways. Expected on this run: new-only `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt`, `harness-version.txt`, the s3 files, `s1-work-prompt.md`, `settings.json`, `snap-3-after-resume/` and `manifest.jsonl` in each snapshot; old-only none expected.
2. **README headings.** Lines starting with `#` in the row README and the folder README. The committed row 1 README has one heading (`# Row 1: wrong active binding (1P)`), so every added heading shows as a difference.
3. **Helper-call counts.** `pc_mine.parse_log` on both `wrapper-calls.log`: total and per verb, and the multiset of exit codes. Committed: one `status`, exit 0.
4. **Tool-call counts.** Count `### N. Name (id)` headings per tool name and the REFUSAL/DENIAL and ERROR flags in each side's `s2-preclear-full-trace.md`, plus the `Calls N;` header. Committed s2: 48 calls. Also report the s3 trace on the new side.
5. **Byte measurements.** Parse both `measurements.txt` shapes (old `total N bytes (cap 4096)` and `- Section: N`; new `total N/4096 bytes` and `- Section: N/cap`) and list any total or section above the cap, using `pc_measure.SECTIONS` and `FILE_CAP`. Committed: 3,494 of 4,096, every section within cap.
6. **Listed, never judged:** `sha.txt` entries that differ (after normalising `helper-state/` and `ledgers/` to `ckpt/`), the `tools.txt` rule set difference (28 versus 40 rules), `digests.txt` lines, `claude-version.txt`, `usage.txt`.

**Normalisation.** Committed tokens are `<repo>/<run>/...`; the new run root is outside the repository so tokens are `<run>/...`. Treat `<repo>/<run>` and `<run>` as equal before comparing trace-derived counts. Wrapper path: committed `<repo>/<run>/wrapper/checkpoint`; new `<run>/wrapper/checkpoint` unless the caller map is changed to emit `<helper>` (not recommended: it breaks `pc_allowlist.WRAPPER_TOKEN` matching for new traces).

**Proving both trees unchanged (EVID-06).** `digest(root) = sha256(pc_manifest.jsonl_bytes(pc_manifest.tree_manifest(root)))` covers paths, kinds, sizes and sha256 of every file and directory (`sha_txt_bytes` alone omits directories and symlinks). Compute for both whole evidence trees at start, print them, compute again at the end, print them, and report `unchanged: yes|no` for each. Tests: (a) synthetic trees: digests equal before and after; and the digest function changes when a byte, a file name or an empty folder changes (sensitivity check); (b) the real committed publication folder as the old side and a synthetic new folder; (c) run the comparer on copies with all write bits removed (`chmod -R a-w`); success shows it opens nothing for writing; (d) patch `builtins.open` for write modes and `os.replace`, `os.rename`, `os.remove`, `os.mkdir`, `os.utime`, `os.chmod` to raise during the run. File modes and timestamps are not part of the digest; say so in the report line.

## Write Boundary And Git Read-Only (research question 7)

**Approved roots for the model in row 1** (names are the run-root children): `project/` (includes the fallback folder `project/.preclear`), `ckpt/` (the stub's `CKPT_HOME`: ledgers, bindings, root registry, handoffs, lock file) and `auto-memory/`. `raw/` and `stage/` are harness-owned: the snapshot diff skips them because the harness writes there, but a model `Write` into them is still listed by the trace scan. `wrapper/calls.log` is appended by the wrapper apparatus and is the only expected change under `wrapper/`. Everything else in the run root, and everything outside it, is outside.

**What the committed allowlist leaves open (C6).** [VERIFIED: tests/harness/pc_flags.py:53-87 BASELINE_ALLOWED_TOOLS] bare `Read`, `Write`, `Edit`, `Glob`, `Grep`; `Bash(mkdir:*)`, `Bash(python3 -c:*)`, `Bash(awk:*)`, `Bash(sed -n:*)`, `Bash(find:*)`, `Bash(env:*)`, `Bash(git branch:*)`, `Bash(git symbolic-ref:*)`, `Bash(git diff:*)`, `Bash(git log:*)`. `Write` and `Edit` reach any path (the committed trace has a `Write` to the auto-memory folder, outside the working directory); `python3 -c`, `mkdir`, `awk`, `sed -n 'w ...'`, `find -fprint`, `git diff --output=...`, `git branch <name>`, `git symbolic-ref HEAD <ref>` can write or mutate. Output redirection needs approval and is refused in this headless policy (publication README: "output redirection needs approval"). So D-03's "Nothing can leave the scratch project" is a goal the checks detect, not a property the binary enforces.

**Derivation (no model text involved):**

1. *Snapshot diff.* Manifest the run root with `tree_manifest`, filtering out `.git/`, `raw/`, `stage/` and the machine-specific `wrapper/py`, `wrapper/stub` (`tree_manifest` has no exclude parameter; filter the returned entries). Compare consecutive stages by path set and digest; every added, changed or removed path outside the approved roots, except `wrapper/calls.log`, is listed. Count is the headline fact.
2. *Trace paths.* For each `Write`, `Edit` and `NotebookEdit` tool_use, resolve `file_path` (relative paths against the project) with `os.path.realpath`; outside the approved roots is listed. For each Bash command part, list absolute paths outside the approved roots and any use of the write-capable programs above. Report as "listed", not as a judgement; a conservative list is acceptable (Bash cannot be fully modelled; the 02-08 spike found the binary allows `echo` and a double-quoted `$PWD` that the matcher model refuses).
3. *Outside memory root.* A single `lstat` of the default auto-memory path under the harness config folder (`<config>/projects/<slug of the project path>/memory`). Never walk or read the config folder (it holds credentials; `tree_manifest(refuse_under=(config,))` exists to refuse it). The slug rule (non-alphanumerics to hyphens) is `[ASSUMED]`: the old harness listed that folder with `sed 's#/#-#g'` (`runs/pub-env.sh` esnap). (A3)
4. *Git.* `capture_git_status(project, git)` before s1 and after each stage (raw NUL form stays in `raw/`, text form goes to `status.txt`). Mutation facts: `git rev-parse HEAD` and branch unchanged; `git for-each-ref` output digest unchanged; `.git` manifest digest unchanged **excluding `index` and `index.lock`** (a plain `git status` may refresh the index without mutating anything); zero staged entries (first status column neither blank nor `?`). Plus the trace scan for mutating git forms: `add commit rm mv reset checkout switch restore stash merge rebase cherry-pick revert clean tag push pull fetch config init gc apply update-index`, `branch` with a name or `-d -D -m -c`, `symbolic-ref` with two or more arguments, `worktree add|remove`, and any `--output`.
5. *Ledger digests unchanged* (D-09 line): the setup versus after digests of ledger A, ledger B, the binding file, the registry file and `.checkpoint-log.jsonl` from `snap-*/sha.txt`.

**Seeded zero-token failure fixture (SC3).** A scripted fake `claude` (extend the `FAKE_CLAUDE` double of `test_spike.py`: it already reads canned `events`, substitutes `$SID`, `$CWD`, `$RUN`, `$WRAPPER`, and can run hooks) with three seeds, each driven through the same `run_row` function the real run uses: (i) the fake writes `<run>/outside.txt` during stage 2 (snapshot path); (ii) the canned stream carries a `Write` tool_use whose `file_path` is in a temp folder outside the run root and the fake really writes it (trace path); (iii) the fake makes a commit in the project (git path). Assert each is reported with a non-zero count, the driver exits non-zero and nothing is promoted. Add the clean seed as the control (all counts zero, filed).

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Parsing the stream | line-by-line `json.loads` with float costs | `pc_stream.parse_stream`, `result_summary`, `init_manifest` | Strict: rejects blank lines, non-objects, non-finite numbers, more or fewer than one `result`; costs become `Decimal` |
| Detecting refusals | substring search for "denied" or "approval" in replies | `pc_stream.denial_report` (the `permission_denied` events and `result.permission_denials`, cross-checked) plus `tool_result_meta` | A reply that merely contains the word is not a signal (Pitfall 9 of the research) |
| Argument list and environment | string-built command lines | `pc_flags.build_argv`, `build_env`, `build_allowed_tools`, `render_settings` | One pinned contract; a test keeps README equal to it; the prompt never goes in argv |
| Exclusive creation | `os.makedirs(exist_ok=True)`, `open(..., "w")` | `pc_runroot.allocate_run_root`, `exclusive_dir`, `write_exclusive` | `O_EXCL` and `O_NOFOLLOW`; a collision is exit 16 |
| Tree hashing and snapshots | `find` piped into `shasum` | `pc_manifest.tree_manifest`, `sha_txt_bytes`, `jsonl_bytes` | Newline, backslash and non-Latin names survive; symlinks never followed |
| Byte caps | `wc -c` on sanitized files | `pc_measure.measure_file` on originals | Same sections and caps as the committed evidence; the model's own cap statements were wrong in 5 of 12 runs (publication README, defect D1) |
| Sanitizing and gating | regex replace plus `grep` | `Sanitizer.from_machine` (+ caller map), `pc_leakgate`, `pc_promote.promote(..., deny_entries=...)` | Escape-aware login handling and fail-closed behaviour were hardened in 02-09 |
| Money arithmetic | floats | `Decimal`; `pc_flags.format_budget` | `build_argv` refuses floats; stream costs are already `Decimal` |
| Shell splitting | `str.split` on commands | `shlex.split` and `pc_allowlist.split_compound` | Quoting and compound operators |
| Fake `claude` for tests | a new mock framework | `pc_testutil.make_tripwire` and `make_fake_claude`, and the scripted `FAKE_CLAUDE` pattern in `test_spike.py` | Already proven; never talks to a model |
| Wrapper log reading | regex on raw lines | `pc_mine.parse_log` | Enforces CALL and EXIT pairing; line order, never timestamps (note WR-10: a `%q`-escaped control character in an argument will not parse) |

**Key insight:** every hard part of this phase (strictness, exclusivity, leak safety, byte-exact measurement) already has a tested Phase 2 implementation. New code should be thin composition plus renderers; anything that re-implements one of those is a defect waiting for the paid run.

## Common Pitfalls

### Pitfall 1: the PATH `claude` is not the tested build (C2)
**What goes wrong:** the real preflight answers 13 and the paid run never starts, or a "fix" widens `TESTED_VERSIONS` without a spike on that build.
**How to avoid:** `--claude <absolute path to the 2.1.310 executable>`; gate stays exact-match; record the banner in `claude-version.txt`. Warning sign: `VERSION_UNTESTED` on a machine where `claude --version` was fine yesterday (the installer updates the PATH link; `DISABLE_AUTOUPDATER=1` is set only for the child).

### Pitfall 2: cost double counting across `--resume` (C3)
**What goes wrong:** the ledger or `usage.txt` adds s1 and s2 `total_cost_usd` and overstates the row by the s1 cost (the spike ledger did this for S2b: it recorded 0.0602973 for a resumed call that added 0.002608).
**How to avoid:** stage cost is `model_usage_since_last_result` summed (equal to the total for a first call), or the difference of consecutive totals; the row total is the last total of each session chain. Tests with the committed S2a and S2b fixtures: 0.057689300000000006 plus 0.002608 equals 0.060297300000000006.

### Pitfall 3: `--max-turns` too small for the `/preclear` turn (C4)
**What goes wrong:** a 5 to 12 turn cap stops s2 mid-checkpoint: money spent, a half-written `.preclear` file, no resume line, so s3 cannot run. STACK research: print mode "exits with an error at the limit"; treat a hit as a failed run. [CITED: .planning/research/STACK.md:38]
**How to avoid:** s2 around 60; s1 and s3 small. Do not hard-code the result subtype name for a limit hit (never observed on 2.1.310, `[ASSUMED]` A1): treat any `subtype` other than `success`, `is_error` true, or `terminal_reason` other than `completed` as an incomplete stage, stop the chain, keep the raw bytes.

### Pitfall 4: stream shape on 2.1.310 (spike findings)
**What goes wrong and how to avoid:**
- *No hook events in the stream*, even with `--include-hook-events`: the InstructionsLoaded logger file under `raw/` is the only audit source. Run every row with `audit_hook=True`, record the log's line count at each stage boundary, and keep `--include-hook-events` out of matrix argv (flag table: "spike audit only").
- *Three built-in plugins* (`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-plugin-authoring`, all `@builtin`): the assertion is "no plugin whose source is not `@builtin`", not "plugins empty".
- *Binary-defined name collision*: the user's own skill set contains a name that the binary also defines; `ABSENCE_EXCLUDED` handles `preclear`, and `binary_defines(realpath(claude), candidates)` reads the executable (about 274 MB, 16 MB chunks) only when candidates exist; cache the answer per run.
- *`--verbose` is required* with `--print` and stream-json (refused with exit 1 otherwise); `build_argv` always passes it.
- *`effort` is absent* from the init event although `--effort high` is accepted; do not assert it.
- *`--max-turns` is hidden* from `--help` but accepted; the table says the limit was not reached.
- *`echo` and a double-quoted `$PWD` are allowed by the binary* although the matcher model refuses them: never use `pc_allowlist` to decide what the binary did; only the structured signals.
- *Event types beyond the obvious* (`rate_limit_event`, `system/thinking_tokens`, 73 of the latter in one committed stream) are normal; `parse_stream` accepts any string `type`.

### Pitfall 5: D-03's containment is not enforced by the allowlist (C6)
**How to avoid:** detection by snapshot diff and trace scan; word the README facts as "writes outside approved roots: N", not "cannot".

### Pitfall 6: tests that walk the whole evidence tree (C5)
**What goes wrong:** the first time the new folder is committed, `test_allowlist.py` fails (336, 32, 22, 47/34/6, 87) and possibly the "no refusal is allowed under its row's rules" test, now evaluated against the new row with the new allowlist.
**How to avoid:** in the plan that files evidence, restrict `load_trace_calls` to the publication folder (a `folder_prefix` argument) or deliberately update the numbers after reading the new corpus entries; run the suite with the new folder present in a temporary repo root. Also check `test_frozen_reference.py` (reads only the publication folder; safe) and `test_mine.py` (publication folder only; safe).

### Pitfall 7: the leak gate refuses the runs-root parent (C7)
**How to avoid:** add the runs root and its parent folder to the caller map with `<scratch>`; verified in memory this session that this removes the finding while `<run>/project` still maps to `<run>`. Warning sign: a gate refusal of a trace whose only path is a `ls ..` or `realpath` of a folder above the run root.

### Pitfall 8: building the sanitizer, the destination check or the deny entries after the money is spent (WR-12, WR-05, WR-14)
**How to avoid:** order every pre-spend refusal first: runs root, sources, destination name free, `Sanitizer.from_machine` built (a `SanitizerError` is a refusal, exit 15 family), `deny_entries()` obtained, matrix ledger readable, budget flag present. Add a test that patches `pc_leakgate.subprocess.run` to fail and asserts no ledger line was written.

### Pitfall 9: the allowlist change alters model behaviour (new baseline)
**What goes wrong:** the new allowlist has per-verb wrapper rules (the committed one had a bare prefix) and the 33-rule baseline (committed 28). The exact status command and `pwd -P` are now allowed, so fewer refusal turns are expected, and a model that tried `bind` would be refused where the committed run would have run it (the wrapper exits 71 for it either way).
**How to avoid:** state it in the folder README as a difference; compare counts, do not judge.

### Pitfall 10: `calls.log` is cumulative and shared by stages
**How to avoid:** record the log's line count in each snapshot; each stage's correlation uses only its slice. s3 runs in a new session but the same run root, so its wrapper calls append to the same file.

### Pitfall 11: filing partial or mislabelled rows
**What goes wrong:** a non-success s2 still gets filed as if complete; or a SKIP reads as quiet absence.
**How to avoid:** the stage chain records which stages ran; a non-success stage stops the chain and nothing is promoted (FAIL files nothing); a SKIP is filed under a `SKIPPED-` folder; a missing resume line is a recorded fact (`NO-RESUME-LINE` marker as the old harness wrote), s3 is then not run, and no cost is spent on it.

### Pitfall 12: harness text that trips the gate or the verdict scan
**How to avoid:** never write the owner's login in harness-authored text (write "the reviewer"); never use verdict words; do not copy `describe_s1` strings; keep `<run>` style tokens, not absolute paths, in every generated line.

### Pitfall 13: README and layout drift
**How to avoid:** each plan adds its files to the README Layout list and its exit or flag rows with the code; run `test_readme.py` in the same plan; remember `data/` files must also scan clean.

### Pitfall 14: spend guard races and lifetime caps (WR-06, WR-05)
**How to avoid:** a new matrix ledger with a file-locked reservation (`fcntl.flock` on a lock file beside it) written before the run starts; attempts per row-stage limited to one unless a human-initiated authorization line exists (D-12); never reuse `spike-spend.jsonl`.

### Pitfall 15: the stub's end-marker bug (WR-03)
**What goes wrong:** a model `update` whose body quotes the end marker permanently corrupts the stub ledger, which would look like a skill failure. Row 1 is the wrong-binding case, so the correct run has zero `update` calls and the risk is low in this phase. The fix is three lines and lies inside `tests/harness/` (review WR-03). [VERIFIED: 02-REVIEW.md WR-03 "reject any line equal to `END_LINE`..."] Fix it now if the plan has room; it must come with a CLI test and a branch-table row.

### Pitfall 16: sessions and cwd on resume
**How to avoid:** run all three stages with the project folder as cwd, never pass `--no-session-persistence` on these rows (flag table: "not passed on real rows"), never reuse a session id (`--session-id` reuse is an error, STACK probe), and generate s3's id with `uuid4`.

## Cost Of One Row (research question 9)

**Result event fields.** [VERIFIED: tests/harness/data/s2-stream.jsonl line 23, s2b-stream.jsonl line 4] Result keys include `subtype`, `is_error`, `num_turns`, `terminal_reason`, `total_cost_usd`, `usage` (`input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`, plus `output_tokens_details`, `iterations`, ...), `modelUsage` (per model, `costUSD`, `costBasis: "list"`), `model_usage_since_last_result`, `permission_denials`, `duration_ms`. `apiKeySource` is `none`, a subscription login: the dollar figure is a list-price estimate, not a bill.

| Observation | Source | Turns | `total_cost_usd` | Per-call usage |
|-------------|--------|-------|------------------|----------------|
| Spike S2a, `claude-sonnet-5-5`, 2.1.310 | `s2-stream.jsonl:23` | 8 | 0.057689300000000006 | in 14, cache creation 8,644, cache read 134,953, out 959 |
| Spike S2b, same session resumed | `s2b-stream.jsonl:4` | 1 | 0.060297300000000005 (cumulative; delta 0.002608) | in 2, cache creation 100, cache read 21,540, out 5 |
| Committed row 1 s2, `claude-fable-5-1`, 2.1.304 | private raw `runs/pub-row1-wrong-binding/evidence/s2-preclear.jsonl` | 49 | 2.2266915 | in 484, cache creation 31,672, cache read 844,165, out 16,301; 186 s |
| Committed matrix s2 stages, `claude-opus-5-5`, 2.1.304 (21 streams) | private raw `runs/pub-row*/evidence/` | 11 to 45 | 0.46 to 1.05 | n/a |
| Committed matrix s3 stages, same model (9 streams) | same | 4 to 9 | 0.22 to 0.38 | n/a |

[DERIVED] from those files; the private raw streams exist only on bokiko's machine. No Sonnet per-token price is available in the repository and the two Sonnet data points cannot fix four rates, so a Sonnet cost for a 49-turn `/preclear` turn is not computable here. If the Sonnet model costs no more per token than the Opus one (`[ASSUMED]` A5), a row would cost roughly s1 (unmeasured, small) plus up to about 1.05 plus up to about 0.4, below the 2.00 cap with margin. If it were priced like the Fable run, the cap would bind. The measured number is the point of the phase.

**Recommended split of the 2.00 USD row cap (D-12; `--max-turns` is in the Discretion list):**

| Stage | `--max-turns` | `--max-budget-usd` | Why |
|-------|---------------|--------------------|-----|
| s1 work turn | 15 | 0.30 | read plan and ledger, write one small file; the spike S1 call cost 0.0264 for a trivial turn |
| s2 `/preclear` resume | 60 | 1.30 | committed turns 49 (row 1) and up to 45 elsewhere; cap binds before turns do |
| s3 fresh resume | 15 | 0.40 | committed s3 turns 4 to 9, cost up to 0.38 on a more expensive model |
| Sum | | 2.00 | the pessimistic sum of launch lines never exceeds the row cap |

`--max-budget-usd` is a client-side estimate that "may overshoot slightly" (flag table); whether it measures the call or the resumed session's cumulative cost on `--resume` is not shown by any capture (`[ASSUMED]` A4). The split above is safe either way: if cumulative, s2's cap of 1.30 bounds the s1+s2 chain; if per call, the three caps sum to 2.00.

**Ledger pattern.** Copy the spike's pessimistic launch line: before each stage append `(row-stage name, attempt, total_cost_usd null, subtype "launched", version)`; an unknown cost counts as that stage's cap; after the stage append the reconciling line with the stage delta and the subtype; a later line for the same (name, attempt) supersedes the earlier one and is still one attempt. [VERIFIED: tests/harness/pc_spike.py:672-705 `_effective`, `_total_of`; `append_spend` at 619] Differences for the matrix ledger: names `row1-s1`, `row1-s2`, `row1-s3`; a per-row cap of 2.00 instead of the spikes' shared 5.00; one attempt per stage (a second needs a human-initiated authorization line, D-12); a file-locked reservation; `Decimal` throughout. Printing: round totals up to cents as `_money(..., ROUND_UP)` does. Note for the record: the spike ledger's `Total spend 0.26 USD` includes the S2b cumulative figure (about 0.0577 USD too much) and counts the refused verbose probe at its 0.05 cap although it never reached a model, so actual spike spend is nearer 0.15 USD; informational only, the findings file is not to be edited here.

**Usage and cost files.** `usage.txt` per stage: session id, subtype, turns, the four token categories from `usage`, the call's own cost (delta), the cumulative `total_cost_usd` as reported, wall seconds; then `row total` (s2 cumulative total plus s3 total) and, in the folder README, the run total. Use `Decimal` text exactly as parsed.

## Code Examples

### Resume line extraction (the old harness rule, reproducible)
```python
# Source: runs/pub-env.sh:71-80 (gitignored local script), same rule as the committed rows 8 to 12
import re
def resume_line(result_text):
    blocks = re.findall(r"```[a-z]*\n(.*?)\n```", result_text or "", re.S)
    candidates = [b.strip() for b in blocks if b.strip().startswith("Resume ")]
    return candidates[-1] if candidates else ""   # empty: record NO-RESUME-LINE, do not run s3
# prompt for s3 is the line itself with no trailing newline: printf '%s' "$RL"
```

### Per-call cost from a result event
```python
# Source: tests/harness/data/s2b-stream.jsonl:4 (keys total_cost_usd, model_usage_since_last_result, costUSD)
from decimal import Decimal
def call_cost(result):
    since = result.get("model_usage_since_last_result")
    if isinstance(since, dict) and since:
        return sum(Decimal(str(v["costUSD"])) for v in since.values())   # parse_stream already gives Decimal
    return result["total_cost_usd"]                                      # first call of a session
```

### Tree digest for the comparer proof
```python
# Source: tests/harness/pc_manifest.py:123,194 (tree_manifest, jsonl_bytes)
import hashlib, pc_manifest
def tree_digest(root):
    return hashlib.sha256(pc_manifest.jsonl_bytes(pc_manifest.tree_manifest(root))).hexdigest()
```

### Filing call (WR-14)
```python
# Source: tests/harness/pc_promote.py:140 (promote signature)
result = pc_promote.promote(stage, dest, repo_root, deny_entries=sanitizer.deny_entries())
# result.code: 0 promoted, 14 leak, 15 scanner error, 17 refused; never print deny_entries()
```

### Dry-run tripwire test (existing pattern)
```python
# Source: tests/harness/test_spike.py:448-467 (DryRunTests) and tests/harness/pc_testutil.py make_tripwire/read_tripwire
pc_testutil.make_tripwire(bin_dir)            # any argv, even --version, is logged and exits 97
code, out, err = run_cli(["--dry-run", "--row", "row1-wrong-binding"], env_with_bin_first)
assert code == 0 and pc_testutil.read_tripwire(bin_dir) == []
```

## State Of The Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-run shell scripts under gitignored `runs/` | Python harness under `tests/harness/` with a fake-`claude` test rig | Phase 2 | Row 1 becomes reproducible and testable at zero tokens |
| Text-mode s1 stage (no usage) | stream-json on every stage | this phase | Per-stage usage and cost exist for the first time |
| Real helper behind the wrapper | stub behind the wrapper | Phase 2 | Hash strings differ by design; compare structure, not digests |
| Run roots inside the repository (ancestor instruction files loaded) | run roots in a shared folder outside every home folder, harness-owned config dir | spike S1, 2026-10-26 | Strict isolation; tokens are `<run>/...` not `<repo>/<run>/...` |

**Deprecated or drifting:** Claude Code 2.1.304 (committed evidence) and 2.1.312 (PATH) are both outside the tested set; only 2.1.310 is gated in.

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | The result `subtype` names for a turn-limit or budget-limit stop (not observed on 2.1.310; the limit was never reached in the spikes) | Pitfall 3 | A hard-coded name would miss the stop; mitigated by treating anything but `success`, or `is_error`, or a `terminal_reason` other than `completed` as incomplete |
| A2 | Committed row 1's s1 prompt was the `pub-lib.sh` `work_turn` text with the ledger A path (inferred from `s1-work.out` and the absence of a decision line in the plan) | How the committed row was produced | s1 behaves differently (for example reads the plan only); low impact because the new run is a new baseline |
| A3 | Claude Code's default auto-memory folder name is the project path with non-alphanumerics replaced by hyphens, under `<config>/projects/<slug>/memory` | Write boundary | The one-line existence check would look in the wrong place and report zero |
| A4 | `--max-budget-usd` on a `--resume` call may count the session's cumulative cost; no capture shows which | Cost | Under the cumulative reading a too-small s2 cap truncates the stage; the recommended split is safe under both readings |
| A5 | The Sonnet model costs no more per token than the Opus model whose committed costs are the anchor | Cost | The projected row cost (up to about 1.5) could be exceeded; the cap and the pessimistic ledger bound the spend |
| A6 | Running the retained 2.1.310 executable by explicit path behaves like reaching it through the PATH link (no re-exec into a newer build) when `DISABLE_AUTOUPDATER=1` is set | Pitfall 1 | Preflight would still answer by the banner it prints, so a mismatch shows as 13 before any spend |
| A7 | The harness config folder is still logged in (last recorded probe 2026-10-26 reported `loggedIn=true`) | Environment Availability | Preflight answers 12 with the one-line login fix; no spend |
| A8 | `python3 -c`, `awk`, `sed -n 'w'`, `find -fprint` and `git diff --output` can write outside the project when the baseline rules allow the program | Write boundary | Overstates the escape routes; the trace scan only lists, so a false route costs a noisy list, not a wrong verdict |
| A9 | Compound-command refusals in 2.1.310 produce `permission_denied` events as they did in the 2.1.304 raw stream (nine events) | C8 | Denial counts could read lower; `tool_result_meta` and the wrapper log cross-check |
| A10 | The new per-verb allowlist and the pinned flags change the number of refusal turns in s2 compared with the committed 49 turns | Cost | Turn and cost projections shift; the caps are sized to the committed maximum |

## Open Questions For The Planner

1. **Which executable runs the paid row?** Recommendation: add `--claude <absolute path>` (feeds preflight, argv and `binary_defines`), point it at the retained 2.1.310 executable, keep the exact-match gate. Alternative: rerun spike S2 on 2.1.312 and extend `TESTED_VERSIONS`, which costs spend, hits the lifetime attempt limits (WR-05) and the existing `data/` outputs, and is out of scope here. Needs bokiko's awareness because the default PATH command will answer 13.
2. **s1 prompt and any preamble (D-04).** The text is not committed anywhere tracked (C1). Recommendation: commit it as a data file with a `$LEDGER` placeholder, reuse it byte for byte, add no preamble. The "dry run decides" test cannot prove containment of `Read` and `Write` (the matcher models only Bash rules), so say in the plan that the decision rests on the committed row having run the same bare `Read` and `Write` rules inside the project. The prompt names a ledger path outside the project; bare `Read` allows it.
3. **How literally does D-10 mean "`--dry-run` exercises all three states"?** Recommendation: the claude-free gate answers 12 (runs root under a home folder) and 11 (a source missing) inside `--dry-run` with no process, SKIP is shown through a test-only registry row, and the `claude`-dependent BLOCKED causes are proven through the real path with fake `claude` doubles. If bokiko means the CLI itself must print all three in one dry run, add a `--dry-run --self-check` listing that runs those cases against synthetic inputs.
4. **Denials and isolation findings versus "FAIL files nothing".** HARN-06 says an unexpected denial "fails the row"; D-03 says denials are reported; EVID-05 forbids verdicts; D-10 says FAIL files nothing. Row 1 will almost certainly show denials (C8). Recommendation: report all denials as counted facts with ids (exit 0 path); reserve exit 19 for an incomplete or unparseable stream; treat a non-zero write-boundary or git-mutation count as FAIL (exit 11), file nothing, keep the run root and print where the raw bytes are. Also decide what a non-success stage does after money is spent (recommended: same, files nothing). This needs bokiko's confirmation because it edits the reading of HARN-06.
5. **Spend gate for real runs.** Recommendation: a real run requires an explicit budget flag whose value is at least the printed worst case (refused with 18 otherwise), one attempt per stage in the ledger, and a human-initiated authorization line (appended by a separate zero-token subcommand) for any retry, so "needs bokiko's explicit word" has a mechanical hook.
6. **Ledger seed text.** Replace `<repo>/<run>/project` with the real project path in the seeded ledger bytes (recommended) or copy the committed bytes verbatim.
7. **Stage caps.** Recommended 0.30 / 1.30 / 0.40 USD and 15 / 60 / 15 turns. "Small `--max-turns` per stage" cannot hold for s2 (C4); confirm 60.
8. **Ledger and attempt policy.** New matrix ledger (recommended) versus extending the spike ledger; whether to fix WR-05, WR-06 and WR-12 in the new code rather than in `pc_spike` (recommended, and leave `pc_spike` untouched). CONTEXT calls WR-03 a spike-driver warning; the review shows it is the stub's `update` end-marker bug, a three-line fix in `checkpoint_stub.py` that needs a CLI test and a branch-table row. Fix now (recommended) or defer.
9. **Extra filed files.** `s1-work-prompt.md`, `settings.json` (without the hook entry), `manifest.jsonl` per snapshot, and where the tool set (`init.tools`) is recorded (recommended: the Init manifest block of `mechanical-checks.md`, not a new file). Each will show as new-only in the comparer.
10. **`test_allowlist.py` corpus.** Scope `load_trace_calls` to the publication folder (recommended) or update 336/32/22/47/34/6/87 after reading the new entries; same plan as the filing.
11. **Registry details.** `--row` id spelling (recommended: the committed folder names, `-rerun` and `-first-pass` suffixes collapse to 18 ids), `--list` columns (id, kind, stages, sessions, implemented), exit code for a known but unimplemented id (recommended 2 with a message) and `--all` ordering (layouts first, then rows in acceptance order, Phase 3 implements only row 1).
12. **Plan split and README ownership.** Follow the roadmap's three plans; one plan owns each README edit per wave because `parallelization` is on; the paid run is a separate human-gated task after the plans pass, and its SUMMARY quotes the measured row total.
13. **Token for the wrapper path in new traces.** Keep `<run>/wrapper/checkpoint` (recommended; matches how the committed rows show it modulo the `<repo>/` prefix) rather than mapping it to `<helper>` as the spike fixtures do.

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3 | all code, selftest | yes | `/usr/bin` 3.9.6 (floor) and PATH 3.14.7 | none needed; prove the floor with the 3.9.6 interpreter |
| git | fixture repo, status capture | yes | 2.50.1 | none |
| bash | `selftest`, wrapper | yes | system 3.2.57 (the shim run reports it) and 5.3.9 on PATH | none |
| gitleaks | pre-commit hook | yes | 8.30.0 | none (hooks refuse without it) |
| Claude Code on PATH | real run | yes, but wrong build | symlink to 2.1.312 | explicit path to the retained 2.1.310 executable (also present: 2.1.307, 2.1.309, 2.1.311) |
| Harness config folder and login | real run | folder exists; last recorded probe `loggedIn=true` (2026-10-26) | n/a | one-time manual login (documented in README); not re-probed here because probing starts `claude` |
| Runs root | run roots | yes, exists, accepted by `runs_root()` (outside every home folder, no ancestor instruction files) | n/a | `PRECLEAR_RUNS_ROOT` |
| Spike spend ledger | not used for the row | `recorded spend: 0.26 USD over 10 call(s)`, 4.74 remaining | n/a | new matrix ledger |
| Disk | run roots and raw streams | 1.1 TiB free | n/a | none |

**Missing with no fallback:** none. **Missing with fallback:** the tested Claude Code build on PATH (use the explicit path). Baseline suite today: `tests/harness/selftest` ran 753 tests, OK (skipped=3), 97 seconds, "0 model calls; claude directories removed from PATH: 6", this session.

## Validation Architecture

(Included because the caller asked for it; `workflow.nyquist_validation` is `false` in the config.)

### Test framework

| Property | Value |
|----------|-------|
| Framework | `unittest`, standard library, Python 3.9 floor |
| Config file | none; discovery by `test_*.py` in `tests/harness/` |
| Quick run command | `python3 -B -m unittest discover -s tests/harness -p 'test_<file>.py'` (or `PC_SELFTEST_PATTERN='test_<file>.py' tests/harness/selftest`) |
| Full suite command | `tests/harness/selftest` (zero model calls; 753 tests today) |
| Floor proof | the same discovery under `/usr/bin/python3` (3.9.6) |

### Success criteria to zero-token proof

| SC | Behaviour | Test type | Command (new files are proposals) | Exists |
|----|-----------|-----------|-----------------------------------|--------|
| 1 | `--list` prints 3 layouts and 18 rows; unknown `--row` or `--layout` exits 2; `--dry-run` prints stages and sessions, exit 0, no process (tripwire log empty, `Popen` trap, no harness-home creation, ledger untouched) | CLI plus in-process | `python3 -B -m unittest discover -s tests/harness -p 'test_matrix_cli.py'` | Wave 0 |
| 1 | SKIP 10, FAIL 11, BLOCKED 12 and 13 through the real path with fake `claude` doubles and injected registry rows; SKIPPED folder named `SKIPPED-<row>` in a temp repo; BLOCKED message equals its README line | integration | `... -p 'test_matrix_preflight.py'` | Wave 0 |
| 2 | Full row 1 chain against a scripted fake `claude`: folder holds the expected file set, every provenance field non-empty, every file passed the gate, filed into a temp repo root by one exclusive `promote`; a second run to the same name is refused before any ledger line | integration | `... -p 'test_row1_run.py'` | Wave 0 |
| 2 | Cost accounting: committed S2a and S2b fixtures give stage costs 0.057689300000000006 and 0.002608; row total equals last totals | unit | `... -p 'test_spend.py'` | Wave 0 |
| 3 | Init assertions, each failing in its own variant (permission mode, model, skill missing, memory path, non-builtin plugin, user instruction outside config, no hook log); isolation mode `strict` recorded | unit | `... -p 'test_row1_assertions.py'` | Wave 0 (reuses `pc_spike.s1_evaluation` tests as models) |
| 3 | Write-boundary and git checks: clean seed gives zero counts; three seeded runs (outside file, outside `Write`, git commit) each report a non-zero count, exit non-zero, promote nothing | integration | `... -p 'test_checks.py'` | Wave 0 |
| 4 | Row README last line is `Reviewer verdict: PENDING`; checklist lines each name an existing staged file; harness-authored files contain none of the verdict words | unit | `... -p 'test_evidence.py'` | Wave 0 |
| 4 | WR-14: runner passes `deny_entries()`; promotion without them is detected | unit | `... -p 'test_evidence.py'` | Wave 0 |
| 5 | Comparer on synthetic trees and on the real committed row: tree digests identical before and after, digest function sensitive to content, name and empty-folder changes; runs on write-protected copies; write calls patched to raise; exit 0 when readable, 2 when not | unit | `... -p 'test_compare.py'` | Wave 0 |
| 5 | `SKILL.md` size at or under 12,000 bytes; frozen reference digest unchanged (exists) | unit | `... -p 'test_frozen_tree.py'` and existing `test_frozen_reference.py` | Wave 0 (size test) |
| 5 | `git diff --stat 0a97367e5c7b876163f68b1ac3f2c960ff5f70bc -- SKILL.md references tests/fixtures tests/evidence/publication-2026-10-20` is empty; `git diff --name-only 0a97367e5c7b876163f68b1ac3f2c960ff5f70bc` lists only `tests/harness/`, `tests/evidence/rerun-*`, `.planning/` | verification commands | run at the phase gate | n/a |
| all | README equals code (layout, exit table, flag table, switches, no `USD`, no absolute path) | existing | `... -p 'test_readme.py'` | exists |
| all | `test_allowlist.py` corpus counts still hold or are deliberately updated | existing | `... -p 'test_allowlist.py'` | exists, must be edited with the filing plan |

### What only the single paid run can prove

One row-1 run on the 2.1.310 executable, capped at 2.00 USD total, proves what no fake can: the real stream shape through the new renderers and the new usage extraction (including that `total_cost_usd` is cumulative on `--resume` for this build and model); that the resumed `status` call reports the s1 session bound to ledger B (the 2.1.310 spike did not observe it); that the real init manifest passes the assertions with the hook-log audit on this build; the model's behaviour with the stub's brand line, the per-verb allowlist and strict isolation (the real count of permission denials); that s2's final reply carries an extractable resume line and s3 stays read-only; the measured turns, tokens and cost per stage and per row; and that the real folder passes the gate and files. Everything else in the five success criteria is proven by the tests above before any token is spent.

### Sampling rate

- **Per task commit:** the touched test file (quick command).
- **Per wave merge:** `tests/harness/selftest` (about 97 seconds today, growing).
- **Phase gate:** selftest green; `--dry-run --row row1-wrong-binding` printed and read by bokiko; the git-diff and size checks above; only then the single paid run, then the comparer, then the SUMMARY with the measured figure.

### Wave 0 gaps

- [ ] `test_matrix_cli.py`, `test_matrix_preflight.py`, `test_row1_run.py`, `test_row1_assertions.py`, `test_checks.py`, `test_spend.py`, `test_evidence.py`, `test_compare.py`, `test_frozen_tree.py`
- [ ] A scripted multi-stage fake `claude` support module (extends the `FAKE_CLAUDE` pattern: stage detection from `--session-id` versus `--resume`, canned `tool_use` and `tool_result` events with timestamps and `tool_result_meta`, real wrapper calls, a checkpoint written under the fallback folder, cumulative cost on resume, optional seeded writes)
- [ ] Data files: s1 prompt, s2 prompt (byte copy), ledger A and B seeds, `CLAUDE.md` template, plan text
- [ ] README sections, layout lines and the BLOCKED-fix list, added by the plans that create each item

## Security Domain

`security_enforcement` is enabled (ASVS level 1).

### Applicable ASVS categories

| ASVS category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | no (the harness has no users); credential handling only | never read, copy or print a credential file; read the boolean `loggedIn` only (`pc_preflight`) |
| V3 Session management | no | session ids are test identifiers (`uuid4`), not secrets |
| V4 Access control | yes, containment | allowlist plus detection of out-of-root writes; exclusive creation; refuse destinations through symlinks or `..` (`pc_promote`) |
| V5 Input validation | yes | `--row` and `--layout` ids validated against the registry; strict stream parser; paths resolved with `realpath` and component-aware containment; `shell=False` everywhere |
| V6 Cryptography | yes, hashing only | `hashlib.sha256`; no custom crypto |
| V7 Error handling and logging | yes | counts and labels only; no value, path, host or deny entry in any message; fixed refusal texts |
| V8 Data protection | yes | sanitize then gate then promote; raw streams stay in the run root; harness config folder never snapshotted (`refuse_under`) |
| V12 Files and resources | yes | `O_EXCL`, `O_NOFOLLOW`, no deletion primitives outside test utilities, size limits in the gate |
| V14 Configuration | yes | harness-owned `CLAUDE_CONFIG_DIR`, scrubbed child environment, pinned flags, no `--dangerously-skip-permissions` |

### Known threat patterns for this stack

| Pattern | STRIDE | Standard mitigation |
|---------|--------|---------------------|
| Leaking the login, home path, host or temp path into committed evidence | Information disclosure | runtime-built sanitizer with the caller map, fail-closed gate, `deny_entries()` passed to `promote` (WR-14) |
| Model-directed write outside the fixture (bare `Write`/`Edit`, `python3 -c`) | Tampering | snapshot diff and trace scan reported as facts; run roots outside home folders; strict isolation |
| Path traversal or symlink swap in the evidence destination | Tampering | `promote` refuses dot-dot, symlinked parents and existing destinations; check before spend |
| Spend overrun or double spend (check-then-act, concurrent runs) | Denial of service (cost) | caps per stage, pessimistic launch lines, file-locked reservation, one attempt per stage, explicit budget flag |
| Untrusted bytes from a model-driven process parsed as trusted | Spoofing | strict parser; structured signals only; no reply-text decisions |
| Credential exposure through the config folder | Information disclosure | never opened by the harness; `tree_manifest` refuses it; promote refuses stages under it |
| Hook-log or stream tampering by the model | Repudiation | logger file written outside project roots (`raw/`), appended by the hook command not the model; a model `Write` into `raw/` would show in the trace scan as outside the approved model roots |

## Sources

### Primary (HIGH confidence: files opened this session)
- `.planning/phases/03-walking-skeleton-row-1/03-CONTEXT.md`, `03-DISCUSSION-LOG.md`; `.planning/REQUIREMENTS.md`, `STATE.md`, `ROADMAP.md` (Phase 3), `config.json`; `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`
- Phase 2: `02-CONTEXT.md`, `02-REVIEW.md` (WR-03, WR-05, WR-06, WR-08, WR-12, WR-14), `02-REVIEW-DISPOSITION.md`, `02-VERIFICATION.md` (next-phase readiness), `02-03-SUMMARY.md`
- `tests/harness/`: `pc_exitcodes.py`, `pc_flags.py`, `pc_preflight.py`, `pc_spike.py`, `pc_stream.py`, `pc_manifest.py`, `pc_measure.py`, `pc_runroot.py`, `pc_promote.py`, `pc_sanitize.py`, `pc_leakgate.py`, `pc_hooklog.py`, `pc_mine.py`, `pc_allowlist.py`, `pc_testutil.py`, `checkpoint-wrapper`, `checkpoint_stub.py`, `selftest`, `README.md`, `test_readme.py`, `test_imports.py`, `test_preflight.py`, `test_exitcode_agreement.py`, `test_allowlist.py`, `test_bash_shims.py`, `test_spike.py` (fake `claude` and dry-run tests), `data/spike-findings.md`, `data/s2-stream.jsonl`, `data/s2b-stream.jsonl`
- `tests/acceptance.md`; `tests/evidence/publication-2026-10-20/README.md` and every file of `row1-wrong-binding/`; `row8b-detached-head/` (s3 shape); `tests/evidence/bound-ledger-2026-10-19/README.md`; `tests/fixtures/bound-ledger/`
- `SKILL.md` (Step 5 resume line), `.claude/CLAUDE.md`, `.claude/settings.json`, `.gitleaks.toml`, `.githooks/README.md`
- Local gitignored scripts and raw streams under `runs/` (`pub-lib.sh`, `pub-row.sh`, `pub-env.sh`, `pub-plain.sh`, `pub-measure.py`, `pub-row1-wrong-binding/`), present only on this machine
- Commands run this session: `tests/harness/selftest` (753 tests OK), read-only `pc_spike.py spend` and `probes`, in-memory sanitizer and gate runs, directory listings of the installer's versions folder; the real `claude` was never started

### Secondary (MEDIUM)
- Claude Code behaviour statements taken from `.planning/research/STACK.md` (fetched from Anthropic documentation on 2026-10-21 per that file); no web search made here

### Tertiary (LOW)
- None used; everything unverified is in the Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, every module and function was read and its signature or quoted constant checked
- Architecture: MEDIUM, a recommended composition of verified parts; the module split is a proposal
- Pitfalls: HIGH for the repository-derived ones (C1 to C8 each reproduced from files or an in-memory run), MEDIUM for Bash-escape and limit-hit behaviour (A1, A8)
- Cost: MEDIUM for the data, LOW for the Sonnet projection (A5)

**Research date:** 2026-10-28
**Valid until:** the first of: the PATH or installer build changes the tested-version situation, `pc_flags.TESTED_VERSIONS` changes, or Phase 3 planning starts a week after this date (the Claude Code build moves several times a week)
