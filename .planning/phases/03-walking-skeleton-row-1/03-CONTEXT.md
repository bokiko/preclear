# Phase 3: Walking Skeleton (Row 1) - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning

<domain>
## Phase Boundary

One command under `tests/harness/` runs row 1 (wrong active binding) end to end through the real
`claude -p` against the stub helper, files the run as sanitized evidence in a new dated folder that
holds mechanical facts only, and a read-only comparer lines that folder up structurally with the
committed `tests/evidence/publication-2026-10-20/row1-wrong-binding`. The driver also lists every
layout and row, dry-runs the whole matrix with zero tokens, and reports SKIP, FAIL and BLOCKED with
distinct exit codes. This phase measures the cost of one real row; Phase 4 spends only after bokiko
has seen that figure. Other rows, the row 7 reruns, the injector and the Codex review are Phase 4.

</domain>

<decisions>
## Implementation Decisions

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

### Decisions after research (bokiko, 2026-10-28)
- **D-13:** Row 1 runs on the **exact build the spikes tested, 2.1.310**, selected through a new
  `--claude <path>` driver option (the build on `PATH` is 2.1.312 and the version gate refuses it).
  No spike rerun. A stranger with another build hits the BLOCKED exit and the README tells them how
  to seed a tested version.
- **D-14:** The 2 USD row cap splits as **s1 0.30 USD / 15 turns, s2 1.30 USD / 60 turns,
  s3 0.40 USD / 15 turns**, because the committed `/preclear` turn took 49 turns. One attempt per
  stage; a retry needs bokiko's explicit word. `total_cost_usd` is cumulative across `--resume`, so
  the ledger records per-stage deltas and the row total is s2's cumulative total plus s3's total.
- **Claude's call, recorded here so nobody re-asks:** permission denials in the stream are
  **counted mechanical facts**, not a FAIL; FAIL is reserved for an isolation or git breach or a
  broken harness. The retry gate is a mechanical flag bokiko types (name at the planner's
  discretion). The committed row 1 has no s3 and no committed s1 prompt, so the s1 prompt is
  committed as a data file under `tests/harness/data/` and the comparer reports the s3 files as
  present on the rerun side only. The runs root and its parent map to a `<scratch>` token in the
  sanitizer so the gate does not read the shared folder as a home. The stub's `update` end-marker
  bug (review WR-03) is fixed inside `tests/harness/` as part of this phase.

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` §Phase 3 — goal, five success criteria, three-plan outline, exit output
- `.planning/REQUIREMENTS.md` — HARN-01, HARN-02, HARN-05, HARN-07, HARN-09, HARN-13, EVID-04,
  EVID-05, EVID-06
- `.planning/PROJECT.md` — validated behaviours row 1 must reproduce (fallback checkpoint, read-only
  fresh resume), constraints, key decisions

### What row 1 is and what it produced
- `tests/acceptance.md` §How to run, §Harness rules, §bound-ledger, §Evidence to record,
  §Publication matrix — the row definitions and the manual procedure the harness automates
- `tests/evidence/publication-2026-10-20/row1-wrong-binding/` — the committed per-row file set
  (README.md, tools.txt, digests.txt, s1/s2 traces and prompts, snap-0/1/2, measurements,
  wrapper-calls.log, wrapper-checkpoint.sh, session.id, claude-version.txt); the structural target
  of the comparer
- `tests/evidence/publication-2026-10-20/README.md` — the folder-level README shape

### Phase 2 outputs the runner builds on
- `tests/harness/data/spike-findings.md` — isolation claim and evidence, stream facts on 2.1.310,
  session-id handling, flag confirmations, the probe table, and the open items for Phase 3
- `tests/harness/README.md` — flag table, exit-code table, spike spend section, stranger run guide
- `.planning/phases/02-model-free-foundation-and-stub/02-CONTEXT.md` — D-01 to D-16 (isolation,
  stub switches, self-test UX, sanitizer and gate)
- `.planning/phases/02-model-free-foundation-and-stub/02-REVIEW-DISPOSITION.md` — the 21 deferred
  findings; WR-12, WR-14 and WR-03 touch the runner directly
- `.planning/phases/02-model-free-foundation-and-stub/02-VERIFICATION.md` §Next-phase readiness

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/harness/pc_spike.py`: `materialize()` builds a scratch project with the wrapper, stub
  `CKPT_HOME`, ledger, auto-memory dir and settings; `run_claude()` runs the pinned argv and captures
  stdout, stderr and the hook log; `build_manifest()` and `s1_assertions()` assert the `init` event;
  `sanitize_to_data()` sanitises, scrubs volatile fields and leak-gates before any write under the
  repository; `guard()`, `append_spend()`, `read_spend()` keep the append-only spend ledger with a
  pessimistic launch line; `runs_root()` refuses home folders.
- `tests/harness/pc_flags.py`: `build_argv`, `build_env`, `render_settings`, `build_allowed_tools`,
  `TESTED_VERSIONS`, `ISOLATION_CLAIM`, the flag table.
- `tests/harness/pc_preflight.py` and `pc_exitcodes.py`: SKIP, FAIL and BLOCKED exit codes already
  reserved for the version gate and login probe; extend, do not re-invent.
- `tests/harness/pc_stream.py`: strict stream-json parser with structured denial detection
  (`permission_denied` events and `result.permission_denials`), `result` usage and cost fields.
- `tests/harness/pc_runroot.py`, `pc_manifest.py`, `pc_measure.py`: exclusive run roots (exit 16),
  snapshot manifests with sha256sum escapes, git status capture, byte measurer (actual/cap).
- `tests/harness/pc_sanitize.py`, `pc_leakgate.py`, `pc_promote.py`: runtime-built sanitizer with
  `deny_entries()`, fail-closed gate, `promote(stage, dest, repo_root, deny_entries=...)`.
- `tests/harness/checkpoint-wrapper` and `checkpoint_stub.py`: logging wrapper (exit 71 for bind,
  create, init), the stub with `CKPT_STUB_KILL_SWITCH` and `CKPT_STUB_LOCK_TIMEOUT_MS`.
- `tests/harness/pc_allowlist.py`: matcher model, `canonical_commands()`, `row_rules(folder)` reads
  a committed row's `tools.txt`.

### Established Patterns
- Append-only ledgers (spend, probes) with a later line superseding an earlier one; counts only,
  never values, in any printed or committed text.
- Every paid path is tested through a scripted fake `claude`; the self-test suite never starts a
  real model; the shim strips `claude` directories from `PATH`.
- Captures stay raw only under the run root; sanitise, scrub, leak-gate, then exclusive write.
- README tables are asserted equal to the code by `test_readme.py`; a new exit code or flag goes
  into the table and the test together.

### Integration Points
- The driver CLI is a new `tests/harness/` module (name at Claude's discretion) that composes
  `materialize`, `run_claude`, the snapshot and measurement modules, the sanitizer and `promote`.
- Row fixtures come from `tests/fixtures/` copies (read-only source) materialised into the run
  root; the committed row 1 `wrapper-checkpoint.sh` and `tools.txt` define the wrapper path form
  and the tool set.
- `test_readme.py`'s pending-file list and the README tables must be extended for the new files.

</code_context>

<specifics>
## Specific Ideas

- The evidence folder name carries both the date and the model so two baselines never collide and
  the comparer can name both sides in its output.
- The checklist lines name their source file so a reviewer can verify each fact without the
  harness's help.
- A SKIPPED row must be visibly a skip in the folder listing, not a quiet absence.

</specifics>

<deferred>
## Deferred Ideas

- Whether the rerun folder replaces `publication-2026-10-20` as the reference — Phase 4, after the
  Codex review (RERUN-04).
- Fixing the remaining Phase 2 review warnings that do not touch the runner (WR-04 to WR-11,
  WR-13, the Info items) — Phase 4 hygiene, or a dedicated hardening pass.
- Per-row extra allowlist rules beyond the committed `tools.txt` — only if a later row needs them
  (Phase 4 rows 10 and 11).
- Linux location of the login credentials (file under the config dir instead of the Keychain) is
  documented, untested — Phase 4 stranger-clone criterion (RERUN-02).

</deferred>

---

*Phase: 03-walking-skeleton-row-1*
*Context gathered: 2026-10-28*
