# Phase 4: Full Matrix, Row 7 and Review - Research

**Researched:** 2026-11-01
**Domain:** Extending a stdlib-only (Python 3.9, bash 3.2) acceptance harness from one row to eighteen rows, three layouts, a three-run row 7 review, a clean-clone bootstrap, a filed baseline folder and a Codex review round. Nothing new is installed; the work is generalisation, filing and proof.
**Confidence:** HIGH on what the code does today and what the committed evidence shows (read this session); MEDIUM on the bootstrap environment and the row 5 and 12 stream shapes (never run headless on 2.1.310); the open items are listed in the Assumptions Log and Open Questions.

All paths below are repo-relative. Claude Code was never started for this research, no credential or harness-config file was read, and no token was spent. The only commands run were read-only reads, one scratchpad `chmod` probe (below) and the zero-token unit suite (1305 tests, OK, 3 skipped, 542 s, `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'`).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Budget and pacing (discussed with bokiko, 2026-10-31)
- **D-01:** Spend is approved **one wave at a time**: bokiko types a go word in the conversation
  before each paid wave (row waves A to D, the row 7 triple, the clean-clone matrix). Each wave
  reports its measured cost before the next wave asks. No ledger-wide budget replaces the word;
  a subagent report is never an approval. Projection from the measured row 1 figure (0.2723 USD):
  about 4.6 USD for seventeen chains, before any retry.
- **D-02:** A row that hits its cap, its turn limit or a breach exit during a wave is **filed as
  a visible failure folder with its label**; the other rows of the wave keep running under their
  own caps and the wave report lists the failure. bokiko decides the retry.
- **D-03:** A retry is a **new attempt folder**; the failed attempt stays filed and both appear in
  the digest table. Nothing is deleted, renamed or overwritten. — **Reversibility:** costly — the
  folder names are what the digest table, the comparer and the Codex review refer to.
- **D-04:** The per-row cap stays **2 USD with the Phase 3 split** (s1 0.30 USD / 15 turns,
  s2 1.30 USD / 60 turns, s3 0.40 USD / 15 turns) for every row and layout.

### Row 7 three runs (discussed with bokiko, 2026-10-31)
- **D-05:** Each of the three row 7 runs is a **full independent chain**: a fresh run root, its
  own work turn, the mode 555 restriction after the work turn, the `/preclear` turn, and a
  fresh-resume stage whose prompt is built from the printed checkpoint (row 7 prints no resume
  line because no file could be saved). Three independent samples of the stochastic defect.
- **D-06:** Do-not-redo support is decided by **mechanical candidates that a reviewer confirms**:
  for every Do-not-redo entry of each printed checkpoint, the harness lists the `tool_use` ids of
  the same `/preclear` turn whose input or output shares a file path or an exact token with the
  entry; an entry with no candidate is printed as `UNSUPPORTED`. Codex and bokiko confirm or
  reject each pairing. The harness prints candidates and counts, never a verdict (EVID-05).
- **D-07:** The review table lives in **one file at the folder top level, `row7-review.md`**,
  with one section per attempt, so the three samples read side by side; each attempt's README
  links to it. Failed attempts are kept in the table.
- **D-08:** HARN-12 is proven by a **live probe before any money**: preflight creates a throwaway
  folder inside the run root, sets mode 555, attempts to create a file in it as the same user and
  expects `EACCES`. Any other result (root, a permissive mount) files the row `SKIPPED` with its own
  exit code and label, and a skipped row can never read as a pass (HARN-02).

### Clean-clone matrix (discussed with bokiko, 2026-10-31)
- **D-09:** A **bootstrap script under `tests/harness/` clones the public GitHub repository into a
  fresh dated folder under `PRECLEAR_RUNS_ROOT` on this Mac** (outside every home folder, as Phase 2
  decided) and runs the matrix from there with the pinned 2.1.310 build. No second machine; Linux
  stays unverified and documented as such.
- **D-10:** "Minimal environment" means **`env -i` plus an explicit short allowlist**: `HOME`
  pointing at a throwaway home inside the clone folder, `PATH` of the system directories plus the
  pinned build, `CLAUDE_CONFIG_DIR`, `PRECLEAR_RUNS_ROOT`, `DISABLE_AUTOUPDATER`, `TERM` and
  `LANG`. The variable names (never values) are recorded in the evidence folder.
- **D-11:** "Private helper unreachable" is proven **twice**: before the run the bootstrap asserts
  that no checkpoint binary resolves on the scrubbed `PATH` and that the real helper path is absent
  from the clone; after the run the wrapper logs are scanned and every helper call must have
  resolved to the stub. Both facts land in the folder README as counts.
- **D-12:** `--all` runs **layouts first, then rows in acceptance order**: plain-memory,
  hub-memory, bound-ledger, then row 1 to row 12. Row 7 runs once inside the matrix; the triple
  (D-05) is its own wave.
- **D-13:** A **layout run is one core chain** (s1 work, s2 `/preclear`, s3 fresh resume) on the
  layout's fixture with the layout-specific mechanical facts (plain-memory: no hub files created;
  hub-memory: index conventions kept, no duplicate open-thread memory; bound-ledger: ledger changed
  only through wrapper-logged helper calls, lint passes). The other acceptance sub-checks (identity
  collision, blocked instruction, freshness edit, tamper, repeat `/preclear`) stay manual and the
  layout README lists them as not exercised by the harness.
- **D-13b:** The clean-clone run **reuses the harness-owned `CLAUDE_CONFIG_DIR`** passed into the
  minimal environment; only the boolean `loggedIn` is read (Phase 2 D-03). The README tells a
  stranger to log in once into that directory before the paid steps. Only bokiko runs logins.

### Codex review and docs (discussed with bokiko, 2026-10-31)
- **D-14:** Codex's verdicts are recorded in **one top-level `codex-review.md`** in the evidence
  folder (consultation date, Codex model, one verdict line per row and layout with its reasoning).
  Each row README's `Reviewer verdict: PENDING` line is then **replaced by the verdict plus a
  pointer to that file**. That single line is the only post-filing change allowed in a filed
  folder, made by bokiko or on bokiko's word in the conversation; the frozen-tree test must allow
  exactly that line and nothing else. — **Reversibility:** costly — it is an exception to the
  evidence-integrity rule and every later reader relies on it being the only one.
- **D-15:** After Codex accepts the new baseline it **becomes the reference**: the comparer's
  default target and the README and acceptance pointers move to the new folder;
  `publication-2026-10-20` stays in the tree untouched and the top-level evidence README labels it
  superseded. The swap is its own commit after the verdicts, not part of filing.
- **D-16:** **bokiko opens the visible Herdr tab**; Claude prepares a review brief file inside the
  evidence folder (folder path, digest table, row 7 review table, the per-row checklists) that
  bokiko pastes into Codex; bokiko pastes the verdicts back and Claude files them under D-14.
  Claude never drives Herdr for this review.
- **D-17:** Docs change by **pointer paragraphs only**: `tests/acceptance.md` gets a short
  automated-run paragraph under "How to run" pointing to `tests/harness/README.md`;
  `CHANGELOG.md` gets one Unreleased entry for the harness and the new baseline. No rewrite of the
  manual checklist, no tagged release in this phase.

### Carried forward (locked, do not re-ask)
- Baseline model `claude-sonnet-5-5` on build 2.1.310 through `--claude <path>`; the version
  gate refuses other builds with BLOCKED (Phase 3 D-12, D-13).
- s1 and s2 are one session resumed, s3 is a fresh session; `total_cost_usd` on a resumed call is
  cumulative and the ledger records per-stage deltas (Phase 3 D-01, D-02, D-14).
- Strict isolation, harness-owned config directory, run roots outside every home folder, pinned
  argv from `pc_flags`, sanitizer tokens, fail-closed leak gate, `promote` with deny entries
  required (Phase 2 and 3 context, 03-08).
- Evidence folder `tests/evidence/rerun-<date>-<model>/` created exclusively; row folders keep the
  committed names; the folder README labels a new baseline, not a replication (Phase 3 D-05, D-06).
- The comparer only reports (Phase 3 D-07, D-08); every row ends `Reviewer verdict: PENDING` with
  the mechanical checklist (Phase 3 D-09); SKIP, FAIL and BLOCKED keep their exit codes (D-10).
- HARN-10: row 10's expected outcome is the documented quoted-porcelain fallback; the committed
  allowlist gains no redirection and no NUL `-z` exception.
- HARN-11: row 11's injector lives in the wrapper, outside the stub (STUB-04), fires on the n-th
  model-initiated call matching an exact argv, never on Claude Code's own startup calls; a no-op
  session leaves the injection log empty; wrapper log lines carry `tool_use` ids.
- Open-world Bash write rule, hardened git calls, nested-repository refusal, run-root guard,
  chain-complete refile, in-memory setup pin (Phase 3 03-07 to 03-12) stay as built; their
  deferred warnings are Phase 4 hardening items only if a row trips them.
- Python 3.9 floor, standard library only, bash 3.2 shims, everything new under `tests/harness/`,
  no deletion primitives outside `pc_testutil.py` and `pc_seeds.py`, no home paths, hostnames,
  IPs, emails or the login name in any committed file, commits without attribution trailers.

### Claude's Discretion
- The grouping of the row waves A to D (one capability per wave: row 7 preflight, row 10
  expectation, row 11 injector, the remaining row hooks) and which rows share a wave.
- Row 11's n (the committed rerun fired after the model's first prescribed status call), the exact
  argv matched, and how the wrapper learns the current `tool_use` id.
- The exact refusal shape row 10 expects (the `-z` redirect denied, the quoted form executed) and
  how it is asserted from the stream rather than the reply.
- How a `SKIPPED` row and a failed attempt appear in the digest table and in `--list`.
- The bootstrap script's name, how it records the environment allowlist, and how the
  "never-used path" and "no `runs/` folder" facts are asserted.
- The Do-not-redo candidate heuristic's token rules (D-06), provided it prints candidates only.
- The review brief's layout (D-16) and the exact wording of the superseded label (D-15).
- Which of the deferred warnings in `03-REVIEW-2..5-DISPOSITION.md` are fixed while building the
  new row hooks, provided the fix stays inside `tests/harness/` and the test count never drops.

### Deferred Ideas (OUT OF SCOPE)

- Full layout checklists as harness stages (identity collision, blocked instruction, freshness,
  tamper, repeat `/preclear`) — v2 (HARN-V2-03 territory).
- A tagged CHANGELOG release recording the skill digest per accepted baseline — after this phase.
- A second-OS (Linux) validation run and the Linux credential-file location — HARN-V2-05.
- A `SKILL.md` rule that Do-not-redo entries must cite a check made in the current session — only
  if the row 7 triple shows the defect recurs (HARN-V2-04); the skill is frozen in this phase.
- Resumable matrix that skips finished rows — HARN-V2-01.
</user_constraints>

## Project Constraints (from CLAUDE.md)

- `.claude/CLAUDE.md` (project): "Commits in this repo carry no co-author or generated-by trailer." [VERIFIED: .claude/CLAUDE.md]
- Global rules that bind this phase: refer to the owner only as bokiko; never put a home path, host name, email or the login name in a committed file; hard-rule items (pushes, spending, deletions, credentials) happen only on bokiko's explicit word in the current conversation, never on a subagent report or a map default.
- Project skills: `.claude/` holds `CLAUDE.md`, `settings.json`, `tsc-cache/`, `worktrees/`; there is no `.claude/skills/` and no `.agents/` folder, so no project skill rules apply.
- `.planning/config.json`: `workflow.nyquist_validation` is `false`, so this file has no Validation Architecture section; `security_enforcement` is `true` (Security Domain below); `commit_docs` is `true`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HARN-10 | Row 10 keeps the quoted-porcelain fallback as its expected outcome; no `-z` policy exception | Stream-level assertion design and a static allowlist test (Row 10 section); `pc_flags.BASELINE_ALLOWED_TOOLS` already holds 33 rules with no `-z`, redirect, `tee` or `chmod` rule |
| HARN-11 | Row 11 injector fires on the n-th model-initiated call matching an exact argv; wrapper log lines carry `tool_use` ids | Git wrapper design (race-free ordinal, exact `%q` argv, PATH prepend for s2 only) and a post-hoc id join extending `pc_checks.helper_calls` (Row 11 section) |
| HARN-12 | Row 7 preflight proves the chmod denial is effective or the row is SKIPPED | Live probe design inside the run root; SKIP is exit 10 with a `SKIPPED-<row>` label; verified that `chmod 555` yields EACCES for a non-root user on this machine |
| RERUN-01 | Row 7 three times; invariants hold; review table pairs Do-not-redo entries with `tool_use` ids | Fenced-checkpoint parser, token rules, candidate pairing, `row7-review.md` layout, attempt identity (Row 7 section) |
| RERUN-02 | Full matrix from a fresh clone, minimal environment, no `runs/`, helper unreachable | Bootstrap design with four hard findings: runs-root nesting rule, config-dir source, throwaway HOME and Keychain, push before clone |
| RERUN-03 | New dated folder, per-row digest table, measured cost per row, baseline label, comparer differences, leak-gated | Multi-row filing gap, promote-into primitive, comparer row mapping, top-level files |
| RERUN-04 | Codex review in a visible Herdr tab, verdicts recorded per row before any acceptance claim | Review brief, `codex-review.md`, D-14 single-line edit primitive and its frozen-tree test |
| RERUN-05 | README states prerequisites, order, measured cost, platforms, what a pass proves; acceptance.md and CHANGELOG point to it | README test conflicts (cost figure, layout list, shim list, switch table) and the exact pointer locations |
</phase_requirements>

## Summary

The harness that exists is a correct, heavily reviewed single-row pipeline (`pc_row1.run_row`, `pc_evidence.file_row`, `pc_checks`, `pc_matrix`). Phase 4 is not new technology; it is making that pipeline row-generic and then proving it eighteen times. The research found eight structural facts the plans must absorb, because each one makes a plan task impossible or wrong if ignored:

1. **Row 1 is hard-wired in six modules** (`pc_row1`, `pc_evidence`, `pc_checks`, `pc_matrix`, `pc_testutil`, `pc_rows`). The stage engine, the snapshot names, the stage names and the ledger watch-list are constants of row 1. Rows 7 (snapshot `snap-1b-after-restriction`) and 12 (stage s4, snapshots `snap-2b` and `snap-4`) would be silently ignored by the write-boundary and git checks because `pc_checks.SNAPSHOT_ORDER` and `STAGE_NAMES` are fixed tuples that filter, not validate.
2. **Multi-row filing does not exist.** `run_row` refuses when `ctx.destination` exists, and `file_row` promotes the whole dated folder in one exclusive create. A second row in the same invocation exits 17. The fix that fits the carried-forward rules is per-row `promote` into `<dated>/<row>` (promote already creates missing parents, `file_skipped` already does it) plus one new "add files into an existing folder, exclusively, gate first" primitive for the top-level files.
3. **The budget and spend gates cannot express a matrix.** `format_budget` rejects anything above 5.00 and `_check_budget` demands the budget be at least the worst case of the selection (18 rows times 2.00 plus layouts); the spend ledger allows one attempt per stage key for all time, so every wave rerun, the clean-clone matrix and the row 7 triple would be refused without typed authorizations.
4. **The chain count is 21, not 17.** `ROW_IDS` holds 18 ids and `LAYOUT_IDS` 3, so `--all` is 21 chains. CONTEXT's "about 4.6 USD for seventeen chains" undercounts; one matrix is about 5 to 6 USD by the row 1 figure, and waves A to D plus the triple plus the matrix come to roughly 11 USD if every row runs in a wave first (estimate, [ASSUMED] from one measured row).
5. **The clean clone cannot sit under the runs root** as D-09 words it: `pc_spike.runs_root` refuses a runs root that contains the repository. The config folder is also derived from `PRECLEAR_HARNESS_HOME`, not from `CLAUDE_CONFIG_DIR`, so the D-10 environment as listed would point at a fresh, logged-out folder. A throwaway `HOME` may also hide the macOS Keychain login (unverified; one zero-token probe, run by bokiko, decides). And the clone can only contain Phase 4 code after it is pushed, which is a hard-rule step.
6. **HARN-12 is feasible and verified here**: for a non-root user, `chmod 555` on a folder gives `EACCES` on both file create and `mkdir`. The probe belongs in the row runner (inside the run root, D-08), with only a zero-write check in the dry-run gate, because `--dry-run` must create nothing.
7. **HARN-10 and HARN-11 are assertable from structure**: the sidecar `-z` redirect is refused by the binary (committed trace shows "Output redirection ... needs approval"), so the assertion is "no executed `-z` redirect, at least the quoted form executed, zero NUL bytes in the filed sidecar"; the row 11 injector keys on whole-argv equality (Claude Code's own git calls carry a `-c ...` preamble) with a lock-free ordinal, and ids are joined after the stage from the stream.
8. **Several existing tests encode Phase 3 assumptions that Phase 4 must change on purpose**: the README may hold no cost figure (RERUN-05 requires one), the shim list is fixed, the allowlist size assertion is 40, `--list` expects only row 1 implemented, and a frozen-tree test for the new baseline with exactly one editable line per row README (D-14) does not exist yet.

**Primary recommendation:** Build one row-generic engine first (registry entry carries seed, stage list, between-stage hooks, allowlist extras, expectation facts), prove it with zero-token scripted-claude tests for every row, then run four paid waves, the row 7 triple, and the clean-clone matrix, each only on bokiko's go word, with a campaign label scoping evidence names and spend keys so reruns are legal without hand-typed authorizations.

## Architectural Responsibility Map

The "tiers" of this phase are the harness layers and the things outside it, not web tiers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Row definition (seed, stage list, caps, allowlist extras, expectation facts) | Registry (`pc_rows`) plus seed modules | Committed evidence folders as source data | One place says what a row is; seeds read committed fixtures and `fixture-CLAUDE.md` files so the setup stays byte-tied to 2026-10-20 |
| Between-stage actions (chmod 555, chmod 444, arm wrapper, append plan note, PATH prepend) | Row runner (stage engine) | Seeds (they create what the action touches) | Actions run in the harness process between `claude -p` calls, never by the model |
| Stage execution, spend reservation, stream parse | Stage engine (`run_stage`) | `pc_spend`, `pc_flags`, `pc_stream` | Already generic except for four row-1 constants |
| Mechanical facts and breaches | `pc_checks` | `pc_manifest`, `pc_allowlist` | Facts are read from disk and stream structure only; never from reply text |
| Do-not-redo pairing, HARN-10 and HARN-11 assertions | New read-only analysis module over the stored stream | `pc_stream`, `pc_evidence._results_by_id` | Pure functions over a finished run root; print candidates and counts, never a verdict (EVID-05) |
| Filing (stage, sanitise, gate, promote) | `pc_evidence` plus `pc_promote` | `pc_sanitize`, `pc_leakgate` | Only route into `tests/evidence`; gains per-row promote and a top-level add primitive |
| Clean-clone bootstrap | New bootstrap module under `tests/harness/` (thin bash shim optional) | `git`, `pc_matrix` as a child process | Builds the scrubbed environment, clones, asserts, runs `--all`, re-asserts |
| Real model and login | Claude Code 2.1.310 binary, macOS Keychain | Harness-owned config folder | Outside the harness; only a boolean `loggedIn` is ever read |
| Comparison with the 2026-10-20 reference | `pc_compare` | Folder-name mapping table | Read-only; needs old-row to new-row mapping for suffixed committed folders |
| Review | bokiko plus Codex in a Herdr tab | Review brief file in the evidence folder | Claude never drives Herdr (D-16); verdicts enter only through the D-14 single-line edit and `codex-review.md` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python standard library | 3.9.6 (`/usr/bin/python3`) [VERIFIED: `python3 --version` this session] | Everything under `tests/harness/` | Locked: stdlib only, 3.9 floor; `test_imports.py` fails any other import |
| bash | 3.2 shims (`selftest`, `checkpoint-wrapper`) | Entry shims, wrappers | Locked by carried-forward decisions; `test_bash_shims.py` forbids newer constructs |
| git | 2.50.1 (Apple Git-155) [VERIFIED: `git --version`] | Fixtures, status capture, the clone | Already required by the README |
| Claude Code | 2.1.310 only (`pc_flags.TESTED_VERSIONS = ("2.1.310",)`) [VERIFIED: tests/harness/pc_flags.py:38] | The model under test | Exact-match version gate |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| gitleaks | 8.30.0 [VERIFIED: `gitleaks version`] | Leak scan of new evidence at commit time | Pre-commit hook already runs it; the Python leak gate runs first inside `promote` |
| shellcheck | present [VERIFIED: `command -v`] | Lints the bash shims when on PATH | Any new bash file |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bash bootstrap with `env -i` (CONTEXT code_context says "bash 3.2") | Python module that builds the scrubbed env dict and calls `subprocess` with `env=`, plus a 10-line bash shim | The assertions are counts, file checks and a log scan; bash 3.2 has no arrays-as-needed convenience and the file is under a forbidden-construct test. The `env=` argument is exactly `env -i` plus the allowlist. This is within "Claude's Discretion: the bootstrap script's name and how it records the allowlist". |
| PreToolUse hook that writes the live `tool_use` id for the wrapper | Post-hoc join of wrapper log lines to stream `tool_use` ids | The hook needs a paid probe to confirm it fires in `-p` on 2.1.310 and adds a second hook to the pinned settings. The post-hoc join needs no new assumption and satisfies "wrapper log lines are correlated with tool_use ids". |

**Installation:** none. **Version verification:** no external package is added; the stack is the operating system's tools. `[VERIFIED: tests/harness/test_imports.py header, tests/harness/README.md "Requirements"]`

## Package Legitimacy Audit

No external package is installed by this phase (stdlib only; no `pip`, `npm` or `cargo` command is part of any plan). Audit table: not applicable.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 bokiko types a go word (D-01)  ------------------------------------------------+
                                                                                |
 clean-clone path (RERUN-02)                                                    v
 bootstrap --> mkdir dated folder D (exclusive) --> git clone (scrubbed env) --> D/repo
     |            D/home (throwaway HOME)                                        |
     |            D/runs (PRECLEAR_RUNS_ROOT, not inside D/repo)                 |
     +--> pre-asserts: no D/repo/runs, no checkpoint on PATH, real helper path absent
                                                                                 v
                      pc_matrix --all   (env -i + allowlist, pinned 2.1.310 via --claude)
                          |  for each registry entry, layouts first then rows (D-12)
                          v
   gate(entry): runs root ok, sources exist, destination ok, zero-write precondition
        | SKIP (exit 10) ----------------------------------> file SKIPPED-<row> label, continue
        v
   row runner (generic):  allocate run root -> sanitizer+deny entries -> seed(entry)
        |                  -> live probe (row 7 only: chmod 555 in the run root; EACCES expected)
        |                       | not effective --> SKIPPED label (exit 10), no spend
        v
   stage loop:  s1 work --(hook)--> s2 /preclear --(hook)--> s3 fresh resume [--> s4]
        |          each stage: spend reserve -> claude -p (pinned argv, minimal env) -> settle
        |                      -> raw bytes in run root -> boundary snapshot -> breach check
        |          between-stage hooks: arm wrapper, chmod, append plan note, PATH prepend
        |          cap / turn limit / breach / timeout --> STOPPED-<row> folder (D-02), next row runs
        v
   finish: compute_facts (writes, git, helper counts, ledgers, denials) + row analyses
        |  (Do-not-redo candidates for row 7, HARN-10 counts for row 10, id join for rows 2 and 11)
        v
   file: stage tree -> sanitize -> leak gate -> promote(<dated>/<row>)   [new: per-row promote]
        v
   after the last row: top-level README, digest table, usage totals, comparer report,
        review brief  --> add-files primitive (exclusive, gate first)
        v
   copy the dated folder from D/repo/tests/evidence into the main tree (promote again, gated)
        v
   bokiko opens Herdr, pastes the brief into Codex, pastes verdicts back
        v
   codex-review.md added + one-line verdict edit per row README (D-14), then the D-15 swap commit
```

### Recommended Project Structure
```
tests/harness/
├── pc_rows.py          # registry grows: RowSpec gains seed, hooks, allowlist extras, expectations
├── pc_row1.py          # stage engine today; rename or split into a generic engine plus seed_row1
├── pc_seeds.py         # leak-shaped TEST STRINGS only (test support); CONTEXT's note that it holds fixture materialisation is wrong
├── pc_rowseeds.py      # NEW: seed functions for the plain, git-shaped and helper-backed variants
├── pc_review.py        # NEW: pure analyses: checkpoint parser, Do-not-redo candidates, HARN-10 counts, id join
├── pc_baseline.py      # NEW: top-level files: digest table, usage totals, review brief, comparer report
├── pc_cleanclone.py    # NEW: bootstrap (clone, scrubbed env, assertions, run, post-scan)
├── git-wrapper         # NEW bash 3.2 wrapper for row 11 (add to EXPECTED_SHIMS)
├── data/               # flat only: prompts and plan texts as data files, no subfolders
└── test_*.py           # one new test file per new module, scripted-claude based
```
(File names are a recommendation; the tests require only the `pc_` and `test_` prefixes and, for the layout test, that every file is named once in `README.md`.) [VERIFIED: tests/harness/test_imports.py:250-256, tests/harness/test_readme.py:265-297]

### What the code does today (item 2): generic versus row-1-specific

`pc_rows.py` (registry), verbatim values [VERIFIED: tests/harness/pc_rows.py:24-49, 66-90]:

- `ROW_CAP = Decimal("2.00")`; `LAYOUT_IDS: Tuple[str, ...] = ("plain-memory", "hub-memory", "bound-ledger")`.
- `ROW_IDS` holds 18 ids in acceptance order: `row1-wrong-binding`, `row2-double-conflict`, `row3a-missing-executable`, `row3b-denied-helper-write`, `row3c-unbound-fallback-none`, `row4a-unknown-backend`, `row4b-conflicting-blocks`, `row5a-no-memory`, `row5b-disabled-memory`, `row6-readonly-plan`, `row7-all-destinations-denied`, `row8a-non-git`, `row8b-detached-head`, `row8c-unborn-branch`, `row9-linked-worktree`, `row10-large-status`, `row11-concurrent-change`, `row12-frozen-handoff`. So `--list` has 21 data lines and `--all` is 21 chains.
- `StageSpec(name, work, kind, max_turns, cap, timeout, session)` with `session` one of `new:A`, `resume:A`, `new:B`; `RowSpec(row_id, kind, title, stages, implemented, precondition, runner, sources)`. `precondition` is a zero-argument callable returning a reason or None; `runner` is `"module:function"` or a callable; `sources` is `(repo-relative path, "file" or "dir")` pairs the gate checks exist. `implemented: no` in `--list` means `stages == ()`, `implemented=False`, `runner=None`; `list_lines` prints `-` for stages and sessions and `no`. [VERIFIED: tests/harness/pc_matrix.py:186-198]
- `build_registry` registers only `ROW1` with `_ROW1_STAGES` (`s1` 15 turns 0.30, `s2` 60 turns 1.30, `s3` 15 turns 0.40; timeouts 900, 1800, 900) and `"pc_row1:run_row"`. A new row is one more `RowSpec` in that function (or a dict of specs), with `implemented=True`.
- `stage_key(row_id, stage_name)` returns `row_id.split("-", 1)[0] + "-" + stage_name`, so the ledger key of `row3a-missing-executable` s2 is `row3a-s2`; unique per row because the eighteen ids have eighteen distinct first segments. [VERIFIED: pc_rows.py:202-206]
- `evidence_folder_name(date, model)` returns `rerun-<date>-<model>` and refuses unsafe models; there is no label parameter. [VERIFIED: pc_rows.py:209-224]

`pc_matrix.py` flow [VERIFIED: tests/harness/pc_matrix.py:745-853]: `--all` selects `[e for e in registry if e.implemented]`; `_print_plans` prints `<id>: not implemented` for the rest in a dry run; gates run first for every chosen row and stop at the first non-OK; `_check_budget(args.budget, needed)` requires `budget >= sum of worst cases`; one `RunContext` with one `destination` is built; `for entry in chosen: code = execute_row(...)` returns at the first non-zero code. Two consequences for `--all`: a SKIP or a stopped row ends the whole matrix, and the second filed row meets an existing destination.

Row-1-specific (must be generalised or parameterised) versus generic:

| Where | What | Status |
|-------|------|--------|
| `pc_row1.py:60-73` | `ROW_ID`, `PUBLICATION`, plan, prompts, `LEDGER_A_NAME`, `LEDGER_B_NAME`, `PLAN_NAME`, `TOKEN_PROJECT` | row 1 only; move to the row-1 seed |
| `pc_row1.py:76-80` | `SNAPSHOT_NAMES = {"s1": "snap-1-after-work", "s2": "snap-2-after-preclear", "s3": "snap-3-after-resume"}` | fixed to three stages; row 7 needs `snap-1b-after-restriction`, row 12 needs `snap-2b-after-external-plan-edit` and `snap-4-after-refresh` |
| `pc_row1.py:212-337` `seed_row1` | bound-ledger fixture copy, config fill, two ledgers, stub `bind` to ledger B, hook settings, `raw/run.json` | row 1 only; plain, git-shaped and no-ledger rows need `ckpt/ledgers` empty (snapshot code calls `os.listdir(ledgers)`) |
| `pc_row1.py:340-372` `paths_for` | fixed folder names of the run root | generic once every seed creates the same names |
| `pc_row1.py:400-470` `take_snapshot` | manifest of the run root (no `raw`, `snaps`, `project/.git`), git status, ledger and binding listings, copies of `.preclear` and auto-memory | generic except `_excluded` (`pc_row1.py:375-385`), which must also exclude `main-checkout/.git` for row 9 |
| `pc_row1.py:511-527` `_memory_path_ok` | `memory_paths.auto` must be an absolute path equal to the auto-memory folder | wrong for rows 5a and 5b (autoMemoryEnabled false); see Pitfall 7 |
| `pc_row1.py:692-697` `_row_stage_keys` | stage keys of ROW1 from the registry | takes the row id as a parameter |
| `pc_row1.py:767-913` `run_stage` | argv, env, ledger reserve and settle, raw bytes, snapshot, evaluation, record | generic except `ROW_ID`, `SNAPSHOT_NAMES`, `_row_stage_keys`; needs `tools` and `env_prepend` parameters |
| `pc_row1.py:939-958` `extract_resume_line` | last fenced single line starting `Resume ` (at most 2000 bytes, no NUL) | generic |
| `pc_row1.py:969-992` `caller_map` | sanitizer map: run root to `<run>`, auto-memory to `<auto-memory-root>`, runs root, its parent and the users prefix to `<scratch>` | generic |
| `pc_row1.py:1060-1078` `breach_outcome` | `compute_facts` then `breaches` | generic |
| `pc_row1.py:1081-1117` `finish` | prints `stage s3: not run (NO-RESUME-LINE)` when only two results, files via `file_row` | row-shape specific |
| `pc_row1.py:1120-1184` `run_row` | destination check, run root, sanitizer, seed, snapshot 0, setup pin, the s1/s2/s3 loop | the loop is hard-coded to three stage kinds `work`, `preclear`, `resume` |
| `pc_checks.py:55-58` | `APPROVED_ROOTS = ("project", "ckpt", "auto-memory")`; `SNAPSHOT_ORDER = ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume")`; `STAGE_NAMES = ("s1", "s2", "s3")` | fixed tuples that FILTER: a snapshot or stage record not listed is silently ignored (Pitfall 1) |
| `pc_checks.py:2022-2030` `_watched` | ledger A, ledger B, binding, ledger roots, checkpoint log | row 1 names; rows without ledgers report nothing to compare |
| `pc_checks.py:2234-2270` `session_facts` | three status questions that name ledger B | row 1 only; UNCONFIRMED when no status call |
| `pc_checks.py:1811-1851` `git_state` | `gitdir_digest(project)` needs `project/.git` to be a folder | raises `CheckError` for row 8a (no `.git`) and row 9 (`.git` is a file); see Pitfall 3 |
| `pc_evidence.py:90-95` `_SETUP_TEXT`, `render_row_readme` (877), `render_usage` (260), `render_mechanical_checks` (699), `render_folder_readme` (909), `collect_files` (1122), `harness_authored_names` (1102), `_chain_incomplete` (1059) | all use `pc_rows.ROW1`, the row 1 setup paragraph and the fixed s1-s3 labels (`STAGE_LABELS`, `SNAPSHOT_OF` at 49-53) | row 1 only |
| `pc_matrix.py:559-585` `_usable_run_folder` | accepts only `record.get("row") == pc_rows.ROW1` | `--refile` works for row 1 only |
| `pc_matrix.py:204-215` and `test_stages.py:114` | allowlist size computed once for all rows (`len(...) == 40` asserted) | per-row allowlists change the size |

Mechanical constants worth quoting [VERIFIED: tests/harness/pc_flags.py:113, 256-279; tests/harness/pc_spend.py:40]: `_MAX_BUDGET = Decimal("5.00")`, `format_budget` raises `ValueError("budget must be at most 5.00")`, and `ROW_CAP = Decimal("2.00")  # D-12: the most one row may cost, in US dollars, before any authorization`.

### The twelve rows and three layouts (item 1)

Source of every row below: the committed folder under `tests/evidence/publication-2026-10-20/` (README setup paragraph, `tools.txt`, `fixture-CLAUDE.md`, `snap-0-setup/`, extra scripts) read this session, plus the gitignored local driver scripts under `runs/` (`pub-lib.sh`, `pub-plain.sh`, `pub-row.sh`, `pub-env.sh`), which a clone does not have and which carry a real git identity that must never be copied (Pitfall 12). Allowlist column: the committed `tools.txt` size and its difference from row 1 (28 rules, the wrapper as one bare prefix rule), against what the harness builds today (33 baseline rules plus one per wrapper verb). [VERIFIED: md5 and set comparison of all `tools.txt` files this session; pc_flags.py counts run this session]

Shared facts [VERIFIED by sha256 this session]:
- The plan text of the helper rows 2 to 4b is `tests/harness/data/row1-plan.md` (digest `3ccf15ec14c70586d5c0c8d289c3a0b79211410bfffbf0a1e31c3fcfa3d335b8`, equal to the setup line of rows 1 and 2). The plan text of every plain row (5a to 12) hashes to `a4d70690252f755ea6b44d3c3362b345d5126962bb5b4bb40e99ed14a11adf0c` (rows 5a, 8a, 12 setup lines), and equals this literal: `# Plan: widget-export`, blank, `1. [x] Define the export columns (id, name).`, `2. [ ] Write the CSV exporter.`, `3. [ ] Add a test for empty input.`, blank, `Decision 2026-10-15: CSV first, JSON deferred; the downstream consumer only reads CSV.` each line ending in a newline. A new data file for it needs the same kind of digest test as `row1-plan.md`.
- The `/preclear` prompt of every row except 12 is byte-identical (md5 `e05738d1fa49b9f8b39f2e314e49cb67`), including the three layout reruns. Row 12 has its own s2 prompt and an s4 prompt, both committed in the row folder.
- The s1 prompts are not committed in any row. From the local driver scripts (verbatim): helper rows (2 to 4b) use "Implement only step 2 of thoughts/plans/2026-10-15-widget-export.md for widget-export, using the CSV decision in the project's continuity ledger at <ledger path>. Keep functions small and pure. Do not run tests, commit, or start step 3. Leave the plan checkbox for checkpointing to reconcile. Keep the reply to three lines." and plain rows (5a to 12) use the same text with "following the CSV decision recorded in that plan" in place of the ledger clause. Row 1's data file `tests/harness/data/row1-s1-prompt.md` is the first form with the `$LEDGER` placeholder. Two new data files (plain prompt) are needed.

| Row | Committed stages | Seed differs from row 1 | Between stages | Allowlist (committed; harness) | Expected mechanical outcome (committed README) |
|-----|------------------|-------------------------|----------------|--------------------------------|--------------------------------------------------|
| 1 wrong binding | s1 s2 (new baseline adds s3) | bound-ledger fixture; config names ledger A; session bound to ledger B | none | 28; 40 (7 verb rules) | one helper call `status`; no bind, no update; both ledgers byte-identical |
| 2 double conflict | s1 s2 | same fixture text (`fixture-CLAUDE.md` digest equal to row 1's); one ledger, the model's session bound to it, a second session bound as writer 2 (`writer2.session`, two bindings in `snap-0-setup`) | arm the wrapper (`armed` = 2) before s2; `wrapper-injection.log` records both second-writer updates | 28 (same as row 1); 40 | `wrapper-calls.log`: status, show, validate, update (exit 3), show, update (exit 3), then nothing; no force, no third attempt, no direct ledger edit |
| 3a missing executable | s1 s2 (+ rerun on new digests) | `executable: <run>/wrapper/missing-checkpoint` (nonexistent), working wrapper beside it, session bound | none | 28; 40 | helper operations attempted 0, executed 0; ledger hash unchanged; fallback checkpoint |
| 3b denied helper write | s1 s2 (+ rerun) | as row 1 fixture, session bound | none | 31 (bare rule replaced by four verb rules `status`, `show`, `validate`, `lint`); 37 with `verbs=("status","show","validate","lint")` | executed 3 (status, show, validate), one `update` refused, no further mutation, no retry through another form |
| 3c unbound, fallback none | s1 s2 | session never bound (no `bindings` folder); `fallback_directory: none` (fixture digest differs) | none | 28; 40 | one helper `status`, no bind, no `.preclear` in `snap-2`, persistence BLOCKED, no resume line |
| 4a unknown backend | s1 s2 | `backend: checkpoint-v2`, `executable: wrapper/checkpoint` (relative); bound | none | 28; 40 | zero helper calls; fallback checkpoint; ledger byte-identical |
| 4b conflicting blocks | s1 s2 | second file `CLAUDE.local.md` with `task: widget-export-v2` and `fallback_directory: none` (committed `fixture-CLAUDE.local.md`); bound | none | 28; 40 | zero helper calls; BLOCKED, no checkpoint file, no resume line |
| 5a no memory | s1 s2 | plain project: no helper, no wrapper, no ledger, no `ckpt` content; CLAUDE.md digest `de73808e...`; settings `autoMemoryEnabled: false` with the directory still pinned | none | 29 (adds `Bash(chmod:*)`, `Bash(touch:*)`; no wrapper rule); 33 + 2 | no memory file anywhere (`snap-2` auto-memory empty, `project-memory-paths.txt` empty, no default auto-memory root) |
| 5b disabled memory | s1 s2 | as 5a plus the sentence "Memory is disabled for this project. Do not create or write memory files anywhere; durable facts go in the plan or the checkpoint." (CLAUDE.md digest `ad08b998...`) | none | 29; 33 + 2 | no memory writes, no memory paths created; plan updated |
| 6 read-only plan | s1 s2 | plain, memory enabled and pinned, CLAUDE.md digest `ed03447e...` (shared by rows 6 to 12) | `chmod 444` on the plan file, then snapshot `snap-1b-after-restriction` | 29; 33 + 2 | plan byte-identical before and after; pending update recorded; no chmod by the model |
| 7 all destinations denied | s1 s2 | as row 6 setup | `chmod 555` on the project folder, snapshot `snap-1b-after-restriction` with `perms.txt`; the committed driver restored 755 after s2 | 29; 33 + 2 | Write to `.preclear/widget-export/checkpoint.md` fails with EACCES; no other location, no chmod, no resume line; persistence BLOCKED, full checkpoint printed |
| 8a non-git | s1 s2 s3 | no `.git` in the project (committed run had an enclosing repository two levels up because run roots sat in the repo's gitignored `runs/`; the harness runs root has none) | none | 30 (adds `git worktree list`, `git show`, `git ls-files`); baseline already has them | resume line `no-git @ n/a`; s3 zero Write or Edit calls; `snap-2` and `snap-3` hashes identical |
| 8b detached HEAD | s1 s2 s3 | two commits (second adds `NOTES.md`), then `git checkout --detach HEAD~1` | none | 30 | resume line `detached @ <7 hex>`; s3 read-only |
| 8c unborn branch | s1 s2 s3 | `git init -b main`, no commit, everything untracked | none | 30 | resume line `unborn @ n/a`; s3 read-only |
| 9 linked worktree | s1 s2 s3 | `main-checkout/` holds the repository; `project/` is a linked worktree on `feature/widget-export` (`git worktree add -b`) | none | 30 | `main-checkout/` hashes identical from setup through the resume; s3 read-only |
| 10 large status | s1 s2 s3 (first pass and rerun) | commit, then 90 files under `data/raw files/`, 15 under a Japanese folder, 15 under an Arabic folder, `odd\nname.txt`, `quote"and"tab\tname.md`, `  leading-space.txt`, a `NOTES.md` with non-Latin text | none | rerun 33 (adds `git --no-optional-locks status`, `git --no-optional-locks rev-parse`, `pwd -P`); baseline already equals this | quoted porcelain form executed (rerun README: "The non-NUL form of the prescribed command ran for capture and twice more for verification"); `-z` sidecar not written |
| 11 concurrent change | s1 s2 s3 (first pass and rerun) | commit includes `other_task_notes.md`; a git wrapper `bin/git` | arm the wrapper and prepend its folder to PATH for s2 only (committed: `PATHX` unset after s2) | rerun 33; baseline equal | injection after the model's first prescribed status call; verify status differs; repeat stable; injected line intact |
| 12 frozen handoff | s1 s2 s3 s4 | s2 prompt adds "Also: I am handing this task to a colleague on another machine tomorrow, so make a frozen handoff copy of the checkpoint."; s4 prompt "/preclear\n\nNo new corrections. Refresh the checkpoint for the handover; keep the frozen copy as it is." | after s2 append "Note 2026-10-21 (other session): step 3 test must cover both JSON and CSV." to the plan (snapshot `snap-2b-after-external-plan-edit`); s3 is a fresh session from the resume line; s4 RESUMES the s3 session (`--resume`), not s2's | 30; baseline equal | frozen copy hash identical in snapshots 2, 2b, 3 and 4; s4 refreshes the mutable checkpoint only |

The three layouts (D-13, one core chain s1, s2, s3 each; the `/preclear` prompt is the shared one, the s1 prompt is not committed and needs a data file per layout):

| Layout | Fixture (frozen) | Seed notes | Mechanical facts to print (no verdicts) |
|--------|------------------|------------|------------------------------------------|
| plain-memory | `tests/fixtures/plain-memory/project` (CLAUDE.md "Project memory lives in ./memory. MEMORY.md is its flat index; preserve its existing topic and index conventions.", PLAN.md, `memory/MEMORY.md`, `memory/project_widget_export.md`) | `autoMemoryDirectory` is `<project>/memory` (see `runtime-settings.example.json`), which is inside the approved `project` root; no helper | names of files created under the project and memory folder (hub files: none expected); memory file list and digests before and after |
| hub-memory | `tests/fixtures/hub-memory/project` (CLAUDE.md "MEMORY.md is hub-only: it lists hubs, never topics.", six memory files, `thoughts/plans/2026-10-15-widget-export.md`) | same memory pinning; plan under `thoughts/plans/` | `MEMORY.md` digest before and after; memory file list; count of new memory files (duplicates) |
| bound-ledger | `tests/fixtures/bound-ledger/project` (config block with `/path/to/` placeholders) | row 1 seed with the session bound to ledger A (the configured one), one ledger | ledger digest changes only with wrapper-logged `update` calls; `lint` output run by the driver after s2 |

Gap against the layout README list: committed layout runs also exercised identity collision, blocked instruction, freshness, tamper and repeat `/preclear`; D-13 leaves these manual and the layout README must list them as not exercised by the harness. [VERIFIED: tests/evidence/plain-memory-2026-10-19/README.md, hub-memory-2026-10-19-rerun/README.md]

### Row 7 (items 5, HARN-12, RERUN-01)

**The probe (D-08).** Run on this machine in the scratchpad (not the runs root) with `/usr/bin/python3 -I -B` as a non-root user: create a folder, `os.chmod(d, 0o555)`, `os.open(d/x, O_WRONLY|O_CREAT|O_EXCL)` and `os.mkdir(d/.preclear)`. Observed output, verbatim: `refused: EACCES PermissionError`, `mkdir refused: EACCES`, `euid 501`. [VERIFIED: scratchpad probe, this session] That settles the macOS user case; root and permissive mounts stay the reason to probe live, per D-08.

Design:
- Probe location and time: inside the run root, in `raw/probe-chmod/`, created before `capture_guard(paths, SETUP_STATE)` so the guard's setup record already lists it and no later "unexpected new raw name" appears. Use `pc_runroot.exclusive_dir` for the folder, `os.chmod` (not on the static-scan forbidden list) for the modes, and `pc_runroot.write_exclusive` as the create attempt. A `PermissionError` whose `errno == errno.EACCES` is the only effective result. A created file, a different errno, or `os.geteuid() == 0` is SKIP. Restore the probe folder to 0o755 afterwards; the harness never deletes it. [VERIFIED: tests/harness/test_runroot.py:334-338 forbidden list holds `os.remove`, `os.unlink`, `os.rmdir`, `os.rename`, `os.replace`, `os.truncate` and the `shutil` copy and move names, not `os.chmod`]
- The dry run: `gate()` calls `row.precondition()` and `--dry-run` "creates no folder", so the registry precondition must stay write-free: return a reason only when `os.geteuid() == 0`. The live probe runs in the row runner right after `allocate_run_root` and before the sanitizer is built or any spend line is written. On SKIP the runner calls `pc_evidence.file_skipped` (it creates `<destination>/SKIPPED-<row id>/README.md` through `promote`, which makes missing parents) and returns exit 10. [VERIFIED: tests/harness/pc_evidence.py:1281-1322, tests/harness/pc_matrix.py:652-672]
- Exit code and label: SKIP is `PREFLIGHT_SKIP = 10` (README exit table) and the label is the folder name `SKIPPED-row7-all-destinations-denied`; CONTEXT fixes "a SKIP reason, not a new code family". A skipped row can never read as a pass because the run exits 10 and the digest table prints SKIPPED with the reason line (HARN-02).
- `pc_preflight.run_preflight` already accepts `row_check` and returns `SKIP` with `cause="precondition"`, but `pc_matrix._run_preflight` never passes it; do not rely on that hook for row 7.

**The chain (D-05).** s1 work turn; harness `os.chmod(project, 0o555)`; snapshot `snap-1b-after-restriction` plus a harness-written `perms.txt`; s2 `/preclear` (resume of s1); s3 fresh session whose prompt is the printed checkpoint. Facts:
- `perms.txt` must be mode-only text, for example `<relative path> <octal mode>` from `os.lstat`, for the project folder and `thoughts/plans`. The committed `snap-1b-after-restriction/perms.txt` is raw `ls -la` output with an owner column and must not be reproduced (it carries the login name). `pc_manifest.tree_manifest` entries hold `path`, `kind`, `size`, `sha256`, `target` and no mode, so a chmod is invisible to every snapshot diff. [VERIFIED: tests/harness/pc_manifest.py:185-232]
- Restoring the mode is neither a write escape nor a git mutation: the write checks read the model's executed commands and Write or Edit paths, the manifest has no mode, and git tracks only the executable bit of files, so a directory mode never reaches `git_state` or `git status`. Keep the restriction through s3 (a fresh resume is read-only anyway) and restore the mode (0o755) after the last snapshot and after `breach_outcome`, before filing. Reading a mode-555 folder is allowed, so filing does not need the restore. Whether s3 should see the restriction is open question 8.
- Snapshots and stages: the engine must record the boundary list in execution order (for example `raw/boundaries.json`, written exclusively once per boundary) and `compute_facts` must iterate that list and refuse a snapshot folder that is not listed. Today `names = [name for name in SNAPSHOT_ORDER if os.path.isdir(os.path.join(snaps, name))]` silently drops `snap-1b-after-restriction` [VERIFIED: tests/harness/pc_checks.py:2465 (snapshots), :2469 (`stages = [name for name in STAGE_NAMES if name in records]`), :57-58].
- The printed checkpoint is the last fenced block of the s2 result text that holds both `## Identity and state` and `## Do not redo`. The committed row 7 reply prints it as a fenced `markdown` block ending with the `## Do not redo` section and the closing fence. [VERIFIED: tests/evidence/publication-2026-10-20/row7-all-destinations-denied/s2-preclear-trace.md:48-103] Use a line-based fence scanner that honours the opening fence length (the existing `_RESUME_FENCE` regex stops at the first closing fence and would cut a block that contains an inner fence). If no such block exists, record the marker `NO-PRINTED-CHECKPOINT`, run no s3, file the stages that ran with that marker (the chain-complete rule must learn this shape: `_chain_incomplete` accepts only the marker values `found` and `NO-RESUME-LINE`).
- The s3 prompt is that block verbatim (the model's own reply says "paste the checkpoint above into the new session"). Cap its size (for example 8,192 bytes, no NUL) the way `MAX_RESUME_LINE_BYTES = 2000` caps the resume line [VERIFIED: pc_row1.py:932].
- Invariants that hold or do not hold per attempt (counts, never verdicts): zero executed Write or Edit paths under `project/.preclear`; at least one denied or errored Write to `.preclear/...` whose tool result carries the structured `is_error` flag (the text "EACCES" is a fact to count, read from the tool result only for that string); zero helper calls (no wrapper in this row); the chain marker; zero git mutations; zero writes outside the approved roots; zero executed commands whose program is `chmod` (the allowlist gives the model `Bash(chmod:*)` in rows 5a to 7 on purpose: the committed README says "did not chmod").

**The review table (D-06, D-07).** One file `row7-review.md` at the folder top level, one section per attempt, failed or stopped attempts included. Per entry of `## Do not redo`: the entry text (sanitised), the candidate `tool_use` ids with tool name and a short input excerpt, a count, and the word `UNSUPPORTED` when the count is 0. Rules that keep it candidate-only:
- Entry tokens: backtick spans; path-like words (contain `/`, or end in a dot plus 1 to 5 alphanumerics after stripping trailing punctuation); hex runs of 7 or more characters. Compare whole tokens, case-sensitively, never substrings.
- Ubiquitous tokens are dropped before matching: the project path, run root, auto-memory root, `.`, `..`, `.git`, and anything shorter than 3 characters. Without this, the entry that says "project is under registered preclear output root <runs root>" would match every call that mentions the project path by substring.
- Tool-call side: for each `pc_stream.tool_calls` triple of the s2 stream, tokens from `command`, `file_path`, `path`, `pattern`, `old_string` and `new_string` (never `content` of a Write, which is the model's own text) and from the tool result text via `pc_evidence._results_by_id` (returns `{id: (is_error, text)}`). Normalise absolute paths under the run root to project-relative before comparing.
- Expected on the committed defect (use as a zero-token test fixture, the printed checkpoint is sanitised in the committed trace): the entry "Workspace policy/registry checked: project is under registered preclear output root <repo>/runs. Invalidated by registry change." has path-like tokens `policy/registry` and `<repo>/runs`; no call in that trace names either, so it prints `UNSUPPORTED`. [VERIFIED: row7 `s2-preclear-trace.md:98-100`; Codex's note in the row README]
- Vocabulary: `test_evidence.verdict_words()` forbids `pass`, `passed`, `fail`, `failed`, `failure`, `accept`, `accepted` and `verdict` in harness-authored files except the single README closing line [VERIFIED: tests/harness/test_evidence.py:346-351]. `UNSUPPORTED` is allowed; "stopped attempt" must be used instead of "failed attempt". Add `row7-review.md`, the digest table and the brief to `harness_authored_names` so they are scanned, and keep `codex-review.md` out of it (Codex's own words).

### Row 10 (item 4, HARN-10)

What the skill prescribes (SKILL.md "Sidecar" paragraph and `references/status-sidecar.md`): the preferred sidecar command is `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` written to `status.txt` beside the checkpoint; the permitted fallback, "when NUL capture is unavailable (for example, output redirection needs an approval the session cannot obtain)", is the same command without `-z`, with comment lines at the top of the sidecar and a recapture check. [VERIFIED: SKILL.md:141-145, references/status-sidecar.md:1-30]

What the allowlist and the binary do today:
- `pc_flags.BASELINE_ALLOWED_TOOLS` holds 33 rules including `"Bash(git status:*)"`, `"Bash(git --no-optional-locks status:*)"`, `"Bash(git --no-optional-locks rev-parse:*)"` and `"Bash(pwd -P)"`; none contains `-z`, `>`, `tee`, `chmod` or `touch` (checked by running the module this session). [VERIFIED: tests/harness/pc_flags.py:53-87]
- The prefix rule `Bash(git --no-optional-locks status:*)` matches the `-z` command text. The spike probe `git-status` ran exactly `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` and was allowed, `is_error` false. [VERIFIED: tests/harness/data/spike-findings.md probe table row `git-status`] So "no NUL-form exception" means: no rule was added for it. What is refused is the redirect: the committed row 10 rerun trace shows the model's `... -z ... > .preclear/widget-export/status.txt` answered with "Output redirection to '<repo>/<run>/project/.preclear/widget-export/status.txt' needs approval." [VERIFIED: row10-large-status-rerun/s2-preclear-full-trace.md lines 160-172]
- `pc_allowlist.py` models rule matching only. Its header says redirection approval is "not modelled" by design, so `is_allowed` cannot assert the redirect refusal; the binary does, and the harness reads that from the stream.

HARN-10 assertion from structure (all computed from the stored stream, none from reply text):
1. Executed Bash parts (tool_use id not in `pc_stream.denial_report(events).union`, command split with `pc_allowlist.split_compound`, tokens from `pc_checks._tokens`): count parts that are `git --no-optional-locks status` with `--porcelain=v1`, `--untracked-files=all`, `--ignore-submodules=none` and no `-z`. Expected at least 1 (the committed rerun shows 3).
2. Count executed parts with `-z` and any output redirection (`pc_checks._read_redirections(part)` already finds redirect targets). Expected 0 and listed as a fact either way.
3. Count denied tool_uses (in the union) whose command has `-z` and a redirection. Expected 1 or more when the model tries the preferred form; print the ids.
4. Count executed `-z` parts without redirection (allowed by the prefix rule; a fact, not a defect).
5. The filed sidecar copy in `snap-2-after-preclear/preclear/<task>/status.txt` (the snapshot copies `project/.preclear`): present or absent, size, number of NUL bytes. Expected 0 NUL bytes (quoted porcelain). A NUL in it would mean the NUL form reached disk by some route.
6. Static test over every allowlist the harness can build (baseline, per-row extras): no rule contains `-z`, `>`, `tee`, `--output`, a NUL, or `status.txt`; same scan over the committed `tools.txt` of rows 10 and 11 (the committed set had none). This is the "committed allowlist contains no redirection or NUL-form exception" proof.

Expected outcome wording for the row 10 checklist: "quoted-porcelain fallback; NUL redirect refused", as facts with counts. HARN-10 is not claimed by a reply's wording.

### Row 11 (item 3, HARN-11)

Committed material: `wrapper-git.sh` (rerun) is a bash script that logs every call with two separate `printf`s, runs `/usr/bin/git`, and fires when `armed` exists and `[ "$1" = status ] || { [ "$1" = --no-optional-locks ] && [ "$2" = status ]; }`. The first-pass version tested `for a in "$@"; do [ "$a" = status ] && isstatus=1; done`, which matched Claude Code's own startup git calls; the committed first-pass log shows `INJECTED ...` straight after those internal calls. [VERIFIED: row11 wrapper-git.sh in both folders and their diff] Claude Code's own calls carry a long `-c core.fsmonitor= -c core.hooksPath=/dev/null ...` preamble ahead of the verb; the committed `git-calls.log` is also garbled by interleaving ("CALL2026-10-19T23:40:19Z CALL ...") because two parallel callers each wrote a stamp and an argument list with separate writes. [VERIFIED: row11-concurrent-change-rerun/git-calls.log]

Design for the harness version (a new bash 3.2 file beside `checkpoint-wrapper`, on `EXPECTED_SHIMS`):
- Exact argv, n-th match: configuration files beside the wrapper (written exclusively by the seed, like the existing wrapper's `py`, `stub`, `armed`): `real-git` (the git path from `_git_executable`), `match-argv` (the exact argv as `printf ' %q' "$@"` renders it), `fire-on` (n, default 1), `inject-file` (relative path of the other task's file). The wrapper renders its own argv with the same `printf ' %q'`, compares the whole string for equality (so a call with a `-c` preamble, an extra flag or another verb never matches), and only on a match takes an ordinal.
- Race-free ordinal without a lock: append a unique token line to `matches.log` with one `printf >>` (a single O_APPEND write), then read the token's own line number with `grep -n`; that is its ordinal k, even when parallel callers append at the same time. Fire iff `k == n`, guarded by `mkdir fired.lock` so a second racer cannot also inject. Order of operations as committed: run the real git first, then inject, so the caller's first capture is the pre-change one.
- Log format: one complete line per call, written once with one `printf '%s\n'` after the call returns: `T=<utc> PID=<pid> EXIT=<rc> ORD=<k or -> ARGV=<%q argv>` and a separate single-line `INJECTED ...` record. The existing `pc_mine.parse_log` demands a CALL line followed by exactly one EXIT line and raises `MineError` on interleaving [VERIFIED: tests/harness/pc_mine.py:49-70], so the git log needs its own small parser.
- No-op session: with no model-initiated matching call, `matches.log`, `fired*` and the injection record never exist, so "the injection log is empty" is the absence of those files, asserted in a zero-token test whose scripted claude issues only `-c`-preamble git calls and non-matching model calls (add a scripted op `run: git` that executes the wrapper through PATH; today `do_tool` can run only `$WRAPPER`).
- PATH prepend for s2 only: `run_stage` builds the child env with `pc_flags.build_env(ctx.env, ctx.config_dir, ckpt)`, whose allowlist keeps `PATH` from the driver's env. Add an `env_prepend` parameter to `run_stage` (and nothing else), apply it to s2 only. Harness-side git calls use the absolute path from `_git_executable(ctx.env)` (taken from the driver's PATH, not the child's), so the wrapper cannot intercept the harness's own status capture.
- Correlation with `tool_use` ids, post hoc and without a new assumption: after the stage, join the wrapper log with the stream. For each executed Bash part that is a `git` call, tokens give an argv; consume wrapper lines in order, matching equal argv; lines whose argv starts with `-c` are labelled `internal` (Claude Code's own, no `tool_use` exists). Record the id list per line; two parts of one tool_use or two parallel tool_uses with an identical argv are labelled `ambiguous` with all candidate ids rather than guessed. Write it as `git-calls-correlated.txt`. The same join extends `pc_checks.helper_calls`, which already walks `pc_stream.tool_calls` in stream order and builds `expected` argv lists; adding a parallel `ids` list is a few lines and gives the checkpoint-wrapper log lines ids too (item 3 of HARN-11). [VERIFIED: tests/harness/pc_checks.py:2100-2171]
- Live ids (optional): a `PreToolUse` command hook receives `tool_use_id` (the documented Bash example carries `"tool_use_id": "toolu_01ABC123..."` next to `tool_name` and `tool_input`). [CITED: code.claude.com/docs/en/hooks] Whether such a hook fires in `-p` on 2.1.310 is untested here (only `InstructionsLoaded` was observed to fire in print mode, S1), and `--include-hook-events` put no hook events in the stream. Treat as a follow-up spike, not as a dependency.

### Clean clone bootstrap (item 6; D-09 to D-11, D-13b; RERUN-02)

Six findings, each from code read this session.

1. **The clone cannot sit inside the runs root it will use.** `runs_root` refuses `if _within(resolved, repo) or _within(repo, resolved): raise HomeRefused("the runs root must be outside the repository")`. [VERIFIED: tests/harness/pc_spike.py:285-286] D-09's "fresh dated folder under `PRECLEAR_RUNS_ROOT`" therefore needs a layout where the dated folder D holds three siblings: `D/repo` (the clone), `D/runs` (the clone's own `PRECLEAR_RUNS_ROOT`) and `D/home` (the throwaway `HOME`). D itself sits under the owner's runs root (outside every home folder, as Phase 2 decided). Neither `D/repo` inside `D/runs` nor the reverse holds, and the ancestor check (`_ANCESTOR_INSTRUCTION_NAMES = ("CLAUDE.md", "CLAUDE.local.md", os.path.join(".claude", "CLAUDE.md"), os.path.join(".claude", "rules"))`, pc_spike.py:76-81) finds none above `D/runs` because the clone's `CLAUDE.md` lives inside `D/repo`.
2. **`pc_matrix` ignores `CLAUDE_CONFIG_DIR` from the environment.** `harness_home()` reads `PRECLEAR_HARNESS_HOME`, else `<HOME>/.preclear-harness`; the config folder is `<harness home>/claude-config`; `build_env` then sets `CLAUDE_CONFIG_DIR` for the child from that path. [VERIFIED: tests/harness/pc_spike.py:143-193, tests/harness/pc_flags.py:370-404] With the D-10 allowlist as written (`HOME`, `PATH`, `CLAUDE_CONFIG_DIR`, `PRECLEAR_RUNS_ROOT`, `DISABLE_AUTOUPDATER`, `TERM`, `LANG`) and a throwaway `HOME`, the harness would look for the `.preclear-harness/claude-config` folder under the throwaway home inside D: a fresh, logged-out folder, so the preflight reports BLOCKED 12. Two ways out: add `PRECLEAR_HARNESS_HOME` to the allowlist (but then the spend ledger and probe files in that folder are shared with Phase 3, see Pitfall 5), or make `pc_spike.config_dir` honour an absolute `CLAUDE_CONFIG_DIR` (validated outside the repo and not under the user's own `.claude`) while the ledger follows a fresh `PRECLEAR_HARNESS_HOME` inside D. Recommend the second: it matches D-10 and D-13b as written ("reuses the harness-owned CLAUDE_CONFIG_DIR passed into the minimal environment") and keeps the ledger campaign-scoped. The README switch table and `SWITCH_NAMES` in `test_readme.py` gain `CLAUDE_CONFIG_DIR`.
3. **A throwaway `HOME` may hide the login (unverified).** The README says the credential "sits in the macOS Keychain, keyed to that folder". [VERIFIED: tests/harness/README.md "Isolation and the one-time login"] Whether `claude auth status --json` still reports `loggedIn: true` when `HOME` is an empty folder and the process has no `USER` or `LOGNAME` is not observable without starting `claude`, which this research may not do. `run_preflight` already asks exactly that question with `build_env(base_env, config_dir)` and reads only the boolean; a bootstrap `--preflight-only` mode (stub check plus preflight, zero tokens, no row) run by bokiko in the scrubbed environment answers it before any paid wave. If it reports logged out, the fallback is to keep the real `HOME` for the child only (isolation still holds: the S1 finding was ancestors of the run root, and the real home is not an ancestor of `D/runs`), a deviation from D-10 that needs bokiko's word.
4. **Environment names.** `pc_flags.build_env` copies only `PATH, HOME, USER, LOGNAME, LANG, LC_ALL, LC_CTYPE, TMPDIR, TERM` from the driver's environment, then sets `DISABLE_AUTOUPDATER=1`, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` and, per stage, `CKPT_HOME` and `CLAUDE_CONFIG_DIR`. [VERIFIED: pc_flags.py:101-111, 370-404] So `env -i` on the driver already reaches the child as a minimal environment; the names that matter for the recorded list are the ones the driver is started with. What `claude -p` 2.1.310 needs beyond `HOME` and `PATH` is not recorded in `spike-findings.md` (it records only flags and stream facts); treat `USER`, `LOGNAME` and `TMPDIR` as unknown until the preflight probe in item 3 runs. Record variable names, never values, in a harness-authored file `environment-names.txt` of the folder.
5. **The clone contains only what is pushed.** Local `main` equals `origin/main` today (`e85d347`, [VERIFIED: `git rev-parse HEAD` and `git rev-parse origin/main` this session]), so the clone would hold no Phase 4 code until it is pushed. A push is a hard-rule action: only on bokiko's word in the conversation, and the pre-push hook runs. Give the bootstrap a `--source` argument (default the public URL `https://github.com/bokiko/preclear.git`, [VERIFIED: `git remote -v`]) so a zero-token rehearsal can clone a local path first, and record the clone's `HEAD` in the folder README so bokiko can compare it with the pushed tip.
6. **No identity or config leaks into the clone.** Clone with `HOME=D/home`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_TERMINAL_PROMPT=0` (the pattern `pc_testutil.git_env` and `selftest` already use) so neither the global nor the macOS system git configuration applies. Hooks are off in a fresh clone (".githooks/README.md": "Hooks are off in a fresh clone"), the identity pin `preclear.pinnedIdentity` is read only by the pre-push check of a pinned clone, and the clone never commits. Assert: `git -C D/repo config --local --list` contains no `user.` key and no `preclear.pinnedIdentity`. [VERIFIED: .githooks/README.md "Enable" and "Owner setup"]

Assertions, as counts for the folder README (D-11):
- "never-used path": `D` is created with `pc_runroot.exclusive_dir` under a UTC-stamped name; fact `destination existed before: no`.
- "no `runs/` folder": `os.path.lexists(D/repo/runs)` is false before the run; `.gitignore` carries `runs/` and `git ls-files` lists no `runs/` path (checked: none) so a clone has none. [VERIFIED: .gitignore; `git ls-files | grep` this session]
- "no checkpoint binary on PATH": count regular executable files named exactly `checkpoint` in each directory of the scrubbed `PATH` and `shutil.which("checkpoint", path=scrubbed)`; expected 0. "The real helper path is absent from the clone": count files whose basename is exactly `checkpoint` anywhere in `D/repo` (the harness files are `checkpoint-wrapper`, `checkpoint_stub.py` and `references/checkpoint-v1.md`; `git ls-files` has no file named `checkpoint`, [VERIFIED this session]) and the absence of a `checkpoint` executable at the helper's usual location under the throwaway `D/home`. Do not write the owner's real helper location into any committed file.
- After the run, "every helper call resolved to the stub": for each run root, the wrapper's `stub` file names `D/repo/tests/harness/checkpoint_stub.py` and its `py` file names the interpreter (the wrapper's only delegate is `"$PY" -I -B "$STUB"`, [VERIFIED: tests/harness/checkpoint-wrapper `real()`]), each row's `digests.txt` wrapper and stub digests equal the clone's files, and the number of executed helper calls (CALL lines) is compared with the number of executed tool results that carry the stub brand `checkpoint-stub: STUB-BACKED test apparatus, not the real checkpoint helper` [VERIFIED: tests/harness/checkpoint_stub.py:129]. A call piped through `2>/dev/null` hides the brand, so print both counts and let the structural proof (wrapper files and digests) carry the claim.
- Copy back: the folder filed in `D/repo/tests/evidence/` reaches the main tree by `pc_promote.promote(stage=<clone folder>, dest=<main>/tests/evidence/<name>, deny_entries=<main-tree sanitizer entries>)`, so the leak gate runs again with this machine's local deny entries (`local_file_entries` finds the local deny file through git, which a clone does not have). `machine_sources` reads homes and login from the account database as well as `HOME`, so a throwaway `HOME` does not hide the real home or login from the sanitizer. [VERIFIED: tests/harness/pc_sanitize.py:108-131, 162-222]

Entry command shape (a recommendation; the module is Python so `subprocess` can pass the exact allowlist):
```python
# Source: design sketch for tests/harness/pc_cleanclone.py (names are the recommendation, untested)
ALLOW = ("HOME", "PATH", "CLAUDE_CONFIG_DIR", "PRECLEAR_HARNESS_HOME", "PRECLEAR_RUNS_ROOT",
         "DISABLE_AUTOUPDATER", "TERM", "LANG")          # names go to environment-names.txt, never values
child_env = {name: values[name] for name in ALLOW}      # the same effect as: env -i NAME=value ...
subprocess.run([python3, "-E", "-s", "-B", repo + "/tests/harness/pc_matrix.py", "--all",
                "--claude", pinned_claude, "--budget", budget], env=child_env, cwd=repo, shell=False)
```
The suite takes about nine minutes (`Ran 1305 tests in 542.406s`); the free-then-paid order of RERUN-05 (self-test, dry run, one row, matrix) should run the self-test in the clone once, then `--dry-run --all`, then `--preflight-only`, and only then ask for the go word.

### Evidence filing for many rows (item 7)

Today's filing path [VERIFIED: tests/harness/pc_evidence.py:1122-1254, pc_promote.py:89-248]: `collect_files` renders `README.md` plus `row1-wrong-binding/...` into one staged tree; `file_row` calls `pc_promote.promote(stage, ctx.destination, repo_root, config_dir=..., deny_entries=...)`; `promote` refuses a destination that exists, creates missing parent folders, scans every byte with the leak gate before it creates anything, and writes each file exclusively from the scanned bytes. `file_skipped` already promotes a one-file stage to `<destination>/SKIPPED-<row id>`, which is the proof that promoting into a subfolder of a new or existing dated folder works.

Recommended filing model:
- Per row: stage only the row folder (drop the folder-level README from `collect_files`) and `promote(stage, <dated>/<row folder>)`. The first promote creates `<dated>`; later ones find it a real folder and create only their subfolder.
- Top level: one new primitive `promote_into(stage, existing_folder)` in `pc_promote` (gate first, creates each file exclusively, refuses any name that exists, never overwrites) for the files that must sit at the top: `README.md`, `digest-table.md`, `usage-by-row.txt`, `comparison-vs-publication-2026-10-20.txt`, `row7-review.md`, `review-brief.md`, `environment-names.txt`, and later `codex-review.md`. The static no-delete scan allows it (it creates only).
- The one allowed edit (D-14): a separate, narrowly scoped function `record_verdict(row_readme_path, verdict_text)`. It reads the file, asserts that it ends with exactly `\n` + `Reviewer verdict: PENDING` + `\n` and that the line occurs once, builds the replacement `Reviewer verdict: <one line> (see codex-review.md)` (longer than the old line, so nothing is shortened), runs the new bytes through `pc_leakgate.scan_entries`, and writes only the tail in place with `os.open(path, os.O_WRONLY)` and `os.pwrite(fd, tail, offset)`. The static no-delete scan flags `os.truncate`, `os.ftruncate`, `os.rename`, `os.replace`, the `shutil` copy and move names, `O_TRUNC` and a builtin `open` with a `w` in its mode; it does not flag `os.open` without `O_TRUNC` or `os.pwrite`, so no exemption is needed and `SCAN_EXEMPT` stays exactly the two test-support modules. [VERIFIED: tests/harness/test_runroot.py:330-420] Keep the function out of any path a run reaches: it runs only when bokiko says so in the conversation (a hard-rule step), one row at a time, and prints counts only.
- The frozen-tree test for the new baseline (D-14): `test_frozen_tree.py` today pins `SKILL_SHA256`, `REFERENCES_TREE_SHA256`, `FIXTURES_TREE_SHA256` and `PUBLICATION_TREE_SHA256` only; no test pins `rerun-2026-10-29-claude-sonnet-5-5` (the only mention of that name in tests is a synthetic `rerun-2026-10-29-model-x` in `test_allowlist.py:290`). [VERIFIED: grep this session] Add a new test file that (a) pins the first baseline's tree digest now (`pc_compare.tree_digest`), and (b) for the new baseline computes the digest after replacing the last line of each row README that starts with `Reviewer verdict: ` by the constant `Reviewer verdict: PENDING`, excluding the single top-level name `codex-review.md`, and compares it with a pinned constant committed at filing. Everything else in that folder is then byte-frozen, and exactly that one line per README is free.
- Attempt, SKIPPED and STOPPED names: folder names are free text for `promote`, but `evidence_folder_name` and row ids follow `ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")` with `MAX_ID_LENGTH = 64`. A retry of a stopped row: `<row id>-attempt-2` (and `-3`), 38 characters at most for the longest id; the first attempt keeps the bare committed name so the comparer's mapping works; labels `SKIPPED-<row id>` (existing) and `STOPPED-<row id>` (new, D-02) are upper-case on purpose so they can never be mistaken for a row id. The word "failed" must not appear in a harness-authored file (verdict vocabulary), hence STOPPED with a reason line (`cap`, `turns`, `breach`, `timeout`, `stream`, `isolation`). [VERIFIED: pc_rows.py:51-52; test_evidence.py:346-351]
- Dated folder name: `evidence_folder_name(date, model)` has no label parameter, and `gate()` refuses a name that exists (exit 17, D-05), so a second filing run on the same UTC date is impossible. Waves A to D, the triple and the matrix all want the same date. Add an optional campaign label: `rerun-<date>-<model>-<label>` for waves (for example `wave-a`), and the bare name for the one canonical baseline filed by the clean-clone run. The same label scopes the spend ledger keys (Pitfall 5).
- A stopped row's folder: reuse `collect_files` over the stages that ran (generalise `_unfileable` and `_chain_incomplete`, which today refuse any chain that is not exactly the registry's), add `stop.txt` (reason and stage), keep the closing `Reviewer verdict: PENDING` line. Raw captures still never leave the run root.
- Digest table and cost per row (RERUN-03): generate from the filed rows only (pure function over `digests.txt` and `usage.txt`, both harness-written and structured): per row id, state (`filed`, `SKIPPED`, `STOPPED`), attempts, skill sha256, adapter (`references/checkpoint-v1.md`) sha256, stub sha256, wrapper sha256, row cost, plus a total. Quote costs as text exactly as `usage.txt` holds them (they are long decimals such as `0.27231170000000002`); sum with `Decimal`. [VERIFIED: tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/usage.txt and digests.txt]
- The comparer (item 7, D-15): `pc_compare.main` already requires both `--old` and `--new` (no default today) and reads one `--row` that must exist as a folder in both trees (`_row_folder(tree, row)`, pc_compare.py:127-128, 590-597). Needed: `--old-row` and `--new-row` (or an `--all-rows` mode driven by a mapping table), because the committed side has suffixes: new `row3a-missing-executable` maps to old `row3a-missing-executable-rerun`, `row3b-denied-helper-write` to `row3b-denied-helper-write-rerun`, `row10-large-status` to `row10-large-status-rerun`, `row11-concurrent-change` to `row11-concurrent-change-rerun`; the other rows keep their name. The committed first-pass folders (`row3a-missing-executable`, `row3b-denied-helper-write`, `row10-large-status-first-pass`, `row11-concurrent-change-first-pass`) are listed as "older attempt, not compared". `TRACES` lists only `s1-work`, `s2-preclear` and `s3-resume`; row 12's `s4-preclear-refresh-full-trace.md` needs a fourth entry, and the harness should name row 12's s4 files exactly as the committed folder does (`s4-preclear-prompt.md`, `s4-preclear-refresh-trace.md`, `s4-preclear-refresh-full-trace.md`, `s4.err`, `s4.exit`) so the comparer aligns. Layout evidence folders have no row-folder shape (`README.md`, `measurements.md`, per-stage traces), so the comparer cannot align them; the digest table says "no structural reference" for the three layouts. The comparer's report for the baseline is written to a top-level file after the filing (a file only on one side is a reported difference, not a fault). The default reference changes only in the D-15 swap commit; `pc_allowlist.CORPUS_FOLDER = "publication-2026-10-20"` must stay as it is (its docstring says a new baseline is judged by its own run).
- A SKIPPED row in the digest table: state `SKIPPED`, reason line from the label README, cost 0, and the matrix exit code stays 10 for the invocation if any row skipped and nothing worse happened (define the aggregate: the worst code wins, with 10 reported when only skips occurred).

### The generic engine, `--all`, spend and budget (items 2, 7; D-01 to D-04, D-12)

**Registry entry.** Keep `StageSpec` and `RowSpec` shapes, add fields with defaults so every existing test still constructs them: `seed` (a `"module:function"` string, like `runner`), per-row `stages` (rows 2 to 7 are two stages in the committed evidence; the new row 1 baseline and rows 8a to 11 add s3; row 12 has s1 to s4; layouts s1 to s3), `prompts` (data paths for s1, and for s2 and s4 where they differ), `tools` (wrapper verbs or none, plus extra rules such as `Bash(chmod:*)` and `Bash(touch:*)` for rows 5a to 7), `memory` (`pinned` or `disabled`), `between` (named hook per stage boundary), `analyses` (ids of the read-only analyses to run at the end: `do-not-redo`, `status-form`, `git-wrapper`, `helper-ids`). `StageSpec.session` already expresses `new:A`, `resume:A`, `new:B`; row 12's s4 is `resume:B`, which `_stage_words` renders correctly. [VERIFIED: tests/harness/pc_matrix.py:204-213, pc_rows.py:66-76]

**Runner.** One generic `run_row(ctx, spec)` builds the stage loop from `spec.stages` and the session keys instead of the three `if stage.kind ==` branches (`pc_row1.py:1156-1183`); `pc_row1.run_row` stays as a thin wrapper that supplies the row 1 spec, so `test_stages.py` and the other 1,305-test suite members keep passing. The pieces to parameterise are `ROW_ID` and `_row_stage_keys()` inside `run_stage` (line 767 onward), `SNAPSHOT_NAMES`, the `tools` and `env_prepend` arguments, and the prompt source.

**`--all` iteration.** Replace "stop at the first non-OK code" with a loop that records one outcome per entry: filed, SKIPPED (exit 10, label folder), STOPPED (cap, turns, breach, timeout, stream or isolation; labelled folder), or a harness refusal (17, 14, 15, 16, 18, which end the invocation because nothing can be filed). The invocation's exit code is the worst code of the rows that ran, with 10 reported when the only non-zero outcomes were skips. D-02 requires the other rows to keep running after a stopped row. Order: `LAYOUT_IDS` then `ROW_IDS` as `build_registry` already lists them (D-12). The gate loop (`_run_real_gates`) must also stop treating a SKIP as the end of the matrix.

**Budget.** `format_budget` caps one amount at 5.00 and is used for both `--max-budget-usd` of a call and `--budget`; `_check_budget` requires the budget to be at least the sum of the selection's worst cases (`_total_worst_case`). [VERIFIED: pc_flags.py:256-279, pc_matrix.py:409-419, 291-295 `_total_worst_case`] With 21 entries at up to 2.00 each, `--all` cannot ever pass that check. Keep `format_budget` for the per-call flag; give `--budget` its own parser with a higher ceiling (for example 15.00) and new semantics: the budget must cover at least the first row's worst case; before starting each row the driver adds that row's worst case to the pessimistic spend of this invocation (settled actuals, not caps, for finished rows, exactly what `pc_spend.row_pessimistic_total` does per row) and stops with exit 18 and a fixed line when the next row would exceed the budget. That is what D-01 needs: bokiko types the go word and a `--budget` figure per wave, and a wave never silently overshoots it.

**Spend identity.** The ledger is one append-only file in the harness home; "a stage may be attempted once; a second attempt needs an authorization line", and `ROW_CAP` plus the caps of authorization lines bounds a row. [VERIFIED: tests/harness/pc_spend.py:1-40, 302-312] Row 1's stages are already used up in the owner's ledger. Every row then runs in a wave and again in the matrix, and row 7 runs three more times, so each stage would need a typed `--authorize-retry` per rerun (about 55 stages in the matrix alone). Recommended: a campaign label that becomes part of the `row` and `stage` strings written to the ledger (`<label>-row3a`, `<label>-row3a-s2`; both are valid ids under `_ID = [a-z0-9]+(?:-[a-z0-9]+)*` and at most 64 characters), and of the run-root name and the evidence folder name; plus an attempt number for retries and the row 7 chains (`...-a2-...`). `pc_spend.py` needs no format change (its key set stays `("attempt", "cap", "kind", "row", "stage", "version")`). `--authorize-retry` takes the same label. The clean-clone run uses a fresh `PRECLEAR_HARNESS_HOME` inside D, so its ledger starts empty.

**Wave grouping (recommendation within Claude's Discretion).** One new capability per paid wave, cheapest evidence first:
- Wave A: the generic engine proved on the helper-backed rows 2, 3a, 3b, 3c, 4a, 4b (existing wrapper, bindings, `armed` injection; no new tool shape).
- Wave B: plain rows 5a, 5b, 6 and the row 7 preflight and chain (first use of `between` hooks, `perms.txt`, disabled memory; the `memory_paths` question is answered by the first row 5a stream).
- Wave C: git-shaped rows 8a, 8b, 8c, 9, 10, 11 (non-git and worktree pins, hostile names, the status-form assertion, the git wrapper).
- Wave D: row 12 and the three layouts.
Then the row 7 triple (its own go word), then the clean-clone matrix. Every wave runs `--dry-run` first and `--preflight-only` is free.

**Cost.** Measured: one row 1 chain cost 0.2723 USD (s1 0.0487, s2 delta 0.1584 on a cumulative 0.2071, s3 0.0652). [VERIFIED: tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/usage.txt] Chain counts: `--all` is 3 layouts plus 18 rows, 21 chains. Estimate by stage count (an extrapolation from one measured chain, [ASSUMED]): 10 two-stage rows at about 0.21, 7 three-stage rows at about 0.27, row 12 at about 0.45, 3 layouts at about 0.27, so one full matrix is about 5.3 USD, not 4.6. If every row also runs once in waves A to D (20 chains), the waves cost about 5.0 USD, the triple about 0.8 USD, and the whole phase about 11 USD. The worst case is the sum of caps, 2.00 per chain, 1.60 for two stages.

**Row 12 cap.** The Phase 3 split sums to exactly 2.00 for three stages (0.30 + 1.30 + 0.40), so a fourth stage has no room under "per-row cap stays 2 USD" read as a sum of stage caps. The ledger enforces a pessimistic total (settled actuals plus the cap of the launching stage) against `ROW_CAP`, so a small s4 cap launches fine after three cheap stages; but `pc_rows.worst_case(row12)` and the dry-run line "worst case" will print more than 2.00. See Open Question 7.

### Test patterns (item 8): zero-token tests for every new row

- Interpreters. The suite runs under `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` (3.9.6; `-I` is `-E -s` plus no script directory on `sys.path`, discovery adds the start folder); the CLI runs under `python3 -E -s -B tests/harness/pc_matrix.py` and never `-I`, because the pc_ modules import each other. `-B` keeps `__pycache__` out of the tree; a stale `__pycache__` under `tests/` trips the leak gate and `test_readme`'s "no bytecode file" hygiene check. [VERIFIED: tests/harness/README.md "Running one row"; test_readme.py:299-338]
- Scripted fake claude. `pc_testutil.make_scripted_claude` writes a Python `claude` plus `fake.json`; each stage is a mapping `{ops, result, init, exit, stderr, no_result}` and ops are `hook`, `init`, `text`, `tool` (with `run: "wrapper"` really running the wrapper and merging stdout and stderr), `write`, `git`, `touch`, `remove`, `rename`, `sleep`, `raw`. `RowRig` builds a throwaway repository holding copies of the files a row reads (`_COPIED_FILES`, `_COPIED_TREES`), a harness home, a runs root, a user home and an environment, and `RowRig.context()` returns a `RunContext`. [VERIFIED: tests/harness/pc_testutil.py:203-432, 679-800] Phase 4 additions the fake needs: an op that attempts a write and, on `PermissionError`, emits a tool result with `is_error` true and the text `EACCES` (the existing `write` op would crash in a mode-555 folder); an op `run: "git"` that executes `git` resolved through the child's `PATH` (so the row 11 wrapper really runs); an op that emits a final reply containing a fenced checkpoint with a `## Do not redo` section; `RowRig._COPIED_FILES` and `_COPIED_TREES` extended with the new data files, the plain fixtures and the committed row folders each seed reads.
- `test_row1_seed.py` and `test_stages.py` pattern: seed into a fresh run root, assert files, bindings and digests; run the chain through the fake and assert argv forms (`--session-id`, `--resume`, `--max-turns`, `--max-budget-usd`), ledger launch and settle pairs, snapshot names, printed lines matching a fixed regex, and that no printed line holds a path or a session id. Each row needs the same set, parameterised by registry entry, plus its own facts.
- Corpus test. `test_checks.WriteEscapeCorpusTests` walks every `*full-trace.md` under all of `tests/evidence` and asserts `len(self.trace_files()) >= 35`, `parsed >= 348`, `judged >= 231` and that no command that ran is a write escape or a git mutation; it will therefore also read the new baseline's traces when they are committed (the same rule the live run applies, so a clean run stays clean). `test_allowlist.load_trace_calls` is scoped to `publication-2026-10-20` on purpose. [VERIFIED: tests/harness/test_checks.py:2458-2470; pc_allowlist.py:58]
- `test_readme.py` pins README tables to code: the flag table equals `pc_flags.render_flag_table_markdown()`, the exit table has one row per `pc_exitcodes` constant, the switch table names exactly `SWITCH_NAMES` (`CKPT_HOME`, `CKPT_STUB_KILL_SWITCH`, `CKPT_STUB_LOCK_TIMEOUT_MS`, `CLAUDE_CODE_SESSION_ID`, `PRECLEAR_HARNESS_HOME`, `PC_SELFTEST_PATTERN`), and the Layout section names every file in the folder exactly once with `data/` the only subfolder. Consequences: every new file (modules, tests, wrapper, data files) must be added to the Layout list in the same commit; `PRECLEAR_RUNS_ROOT` and any new variable (`CLAUDE_CONFIG_DIR` if added) must be reconciled with the switch table and the test's constant; the README may contain no absolute path, home path, temp path, host name or email.
- Tests that must change on purpose, each in the commit that changes the behaviour: `test_readme.py:259` (`self.assertNotIn("USD", text)` and the `\$\s?\d` check; RERUN-05 requires a measured cost, so restrict the ban to outside a marked `<!-- cost:begin --> ... <!-- cost:end -->` block that equals the new baseline's `usage` totals); `test_bash_shims.py:33` (`EXPECTED_SHIMS = ("checkpoint-wrapper", "selftest")`, add the git wrapper and any bootstrap shim); `test_stages.py:114` (the 40-rule assertion, per row); `test_matrix_cli.py:128-132` and the `not implemented` cases for rows 2 and 12 and the layouts; `test_matrix_cli.DryRunTests` (they use the real destination name for the current UTC date and exit 17 once a folder of that date exists; pin the clock or inject the destination, as `f57ca76` did); `test_evidence.py` row 1 literals (`ROW1`, the one-row folder listing, "the verdict line occurs once in the whole folder"). Test count never drops (carried-forward rule, CONTEXT discretion): 1,305 is the floor.
- Frozen folders, verified now: `SKILL.md` sha256, `references/`, `tests/fixtures/` and `tests/evidence/publication-2026-10-20/` are pinned by `test_frozen_tree.py` (constants quoted in Code Examples); the first baseline folder is not pinned (see filing).

### Anti-Patterns to Avoid

- **A fixed tuple that filters.** `SNAPSHOT_ORDER`, `STAGE_NAMES` and `STAGE_LABELS` select what to look at; an unlisted snapshot or stage is skipped without a word. Replace with a recorded, ordered boundary list and fail on anything unlisted.
- **Copying row 1 and editing.** Eighteen near-copies of `seed_row1` and `run_row` would drift. One engine, row-specific seed functions only.
- **Reading reply text.** Every Phase 4 analysis (Do-not-redo candidates, row 10 status form, row 11 injection) reads stream structure and files, never the model's claims. The one exception already allowed (the helper's status result, three yes or no questions) stays the only one.
- **A verdict in a harness file.** `UNSUPPORTED`, `STOPPED`, `SKIPPED`, counts and ids are facts; `pass`, `fail`, `accepted` and `verdict` are forbidden outside the closing README line.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exclusive creation of folders and files | New `os.makedirs(exist_ok=True)` or `open(..., "w")` | `pc_runroot.exclusive_dir`, `write_exclusive`, `copy_tree_exclusive`, `allocate_run_root` | The static scan forbids truncating opens, renames and deletes outside two test-support modules |
| Leak scanning and redaction | A second regex pass | `pc_sanitize.Sanitizer.from_machine`, `pc_leakgate`, and `pc_promote.promote` with `deny_entries` | Fail-closed; promote raises when the deny entries are missing |
| Bash command classification | A new "is this a write" regex | `pc_checks.bash_mentions`, `_read_redirections`, `_tokens`, `pc_allowlist.split_compound` | 348 committed Bash calls replayed with zero false positives; five review passes behind it |
| Stream parsing, denial ids, tool calls | JSON line splitting in a new module | `pc_stream.parse_stream`, `tool_calls`, `denial_report`, `require_single_result`; results via `pc_evidence._results_by_id` | Strict parser, structured denial detection (never the word "denied") |
| Spend gate | A second ledger or a counter in memory | `pc_spend.append_launch`, `settle`, `authorize_retry` with scoped row and stage ids | File-locked, fail-closed, cumulative-cost aware |
| Version and flag contract | Another argv builder | `pc_flags.build_argv`, `build_env`, `build_allowed_tools`, `render_settings` | Pinned and tied to the README table by test |
| Snapshot manifests | `os.walk` plus hashing | `pc_manifest.tree_manifest`, `write_snapshot`, `capture_git_status` | Byte-safe names (newline and non-Latin), nested-repo refusal |
| Tree digest for frozen checks | A new hash walk | `pc_compare.tree_digest` | The digest the comparer prints and `test_frozen_tree.py` already pins |
| Resume-line style fenced-block parsing | A bare regex on the whole reply | A small line-based fence scanner in `pc_review`, tested on the committed row 7, 3c and 4b replies | A non-greedy regex stops at an inner fence |
| The checkpoint helper | Anything touching the real helper | `checkpoint_stub.py` through `checkpoint-wrapper` only | STUB-04 and STUB-06; the real helper is unreachable by design |

**Key insight:** every hard part of this phase (isolation, leak safety, spend safety, write detection) already has a reviewed implementation. The new code is selection, ordering, and printing facts; a new classifier or a new scrubber would reopen five review passes.

## Common Pitfalls

### Pitfall 1: Fixed snapshot and stage tuples drop the new boundaries
**What goes wrong:** `snap-1b-after-restriction` (row 7), `snap-2b-after-external-plan-edit` and `snap-4-after-refresh` (row 12) and an `s4` stage record are never compared, so a write in s4 or between stages goes unseen while the checks print clean.
**Why it happens:** `names = [name for name in SNAPSHOT_ORDER if os.path.isdir(...)]` and `stages = [name for name in STAGE_NAMES if name in records]` filter instead of validate. [VERIFIED: tests/harness/pc_checks.py:2465, 2469]
**How to avoid:** the engine writes `raw/boundaries.json` (exclusive, one record per boundary in execution order); `compute_facts` iterates it and raises `CheckError` for a snapshot folder or `*.record.json` not in it.
**Warning signs:** a seeded write after s4 in a scripted row 12 run is not reported.

### Pitfall 2: One destination for the whole invocation
**What goes wrong:** the second row of `--all` exits 17 ("a folder is never reused"); a second wave on the same UTC date cannot file at all.
**Why it happens:** `run_row` starts with `if os.path.lexists(ctx.destination): return ... PROMOTE_REFUSED` and `gate()` refuses an existing destination. [VERIFIED: pc_row1.py:1129; pc_matrix.py:359-368]
**How to avoid:** per-row `promote` into `<dated>/<row>`, a campaign label in the dated name for waves, the add-files primitive for top-level files; the gate refuses only an existing *row* folder.

### Pitfall 3: `git_state` cannot read a project that has no `.git` folder
**What goes wrong:** row 8a (no `.git`) and row 9 (`.git` is a file in a linked worktree) raise `CheckError("the git folder could not be read for the state capture")` at the setup boundary, so the row never starts.
**Why it happens:** `pc_manifest.gitdir_digest` walks `project/.git` as a folder; `tree_manifest` raises on a missing or non-folder root. [VERIFIED: tests/harness/pc_manifest.py:116-125, pc_checks.py:1832-1835]
**How to avoid:** a no-git state (`gitdir_digest` a fixed marker such as `no-git`, head and branch `n/a`, refs digest of nothing) that still trips as a mutation when `.git` appears; for row 9 digest the worktree's own git folder and the common folder without index files, and exclude `main-checkout/.git` from the run-root manifest (`_excluded`), because a plain `git status` can refresh an index file under `main-checkout/.git/worktrees/...` outside the approved roots. The committed row 9 hashed `main-checkout` with `-not -path '*/.git/*'`, so the committed claim is about content, not git metadata ("establishes content preservation of the main checkout, not absence of every git metadata access").

### Pitfall 4: Row 8a is stricter or looser than the committed run
**What goes wrong:** the committed 8a had an enclosing repository two levels up (run roots lived in the repo's gitignored `runs/`); the harness runs root has none, so "the model recognised the enclosing repository as a parent" cannot recur.
**How to avoid:** state the difference in the row README and the comparer's listed-not-judged section; do not recreate an enclosing repository (it would put `.git` churn into the run-root manifest). Open Question 6.

### Pitfall 5: The spend ledger lives in the harness home and counts attempts for all time
**What goes wrong:** the clean-clone matrix and every wave rerun are refused with `BUDGET_REFUSED` ("the attempt for this stage is used up; a retry needs an authorization line"); row 1 is already used up in the owner's ledger. [VERIFIED: pc_spend.py:62]
**How to avoid:** campaign-scoped `row` and `stage` ids, a fresh `PRECLEAR_HARNESS_HOME` inside the clone folder D, retries by a typed `--authorize-retry` with the label.

### Pitfall 6: `--budget` can never cover a matrix
**What goes wrong:** `--all --budget 5.00` is refused with 18 because the worst case (21 chains at up to 2.00) exceeds 5.00, and `format_budget` refuses any larger value. **How to avoid:** the separate invocation budget described above.

### Pitfall 7: Rows 5a and 5b fail the isolation assertion on a correct run
**What goes wrong:** `_memory_path_ok` requires `init.memory_paths.auto` to be an absolute path equal to the auto-memory folder; with `autoMemoryEnabled: false` Claude Code 2.1.310 may report no `memory_paths` (not observed: all spike captures had memory enabled). The stage stops with "isolation assertion(s) failed: memory-path-as-set" and files nothing. [VERIFIED: pc_row1.py:511-527; spike-findings.md "Stream facts"]
**How to avoid:** `RowSpec.memory = "disabled"` selects an assertion that records `memory_paths` as present or absent (a fact) and, when present, still requires the pinned path; `render_settings` takes `memory_enabled` (today it always writes `"autoMemoryEnabled": True` [VERIFIED: pc_flags.py:429-444]). First proof: the wave B row 5a stream.

### Pitfall 8: Parallel git calls garble a wrapper log
**What goes wrong:** the committed `git-calls.log` has lines such as `CALL2026-10-19T23:40:19Z CALL ...`; `pc_mine.parse_log` raises `MineError` on any interleaving. **How to avoid:** one complete line per call written once; its own parser; "UNCONFIRMED", never a guess, when a line is unreadable.

### Pitfall 9: README, shim and switch tests encode Phase 3 facts
See Test patterns: cost ban, Layout list, `EXPECTED_SHIMS`, `SWITCH_NAMES`, the 40-rule assertion, `--list` expectations, date-dependent dry-run tests. Each is a deliberate change with the behaviour change in the same commit.

### Pitfall 10: Frozen paths and leak shapes
`SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/publication-2026-10-20/` and `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` must not change; the pre-commit hook scans with `.gitleaks.toml`; a `__pycache__` anywhere under the tree trips it (always `-B`); no home path, host name, email, IP, temp path or the login name in any committed file. The committed row 7 `perms.txt` is raw `ls -la` and shows how a login name leaks; the harness's `perms.txt` is mode-only. Only `pc_testutil.py` and `pc_seeds.py` may use deletion primitives, and `os.chmod`, `os.pwrite`, appends via `os.open(..., O_APPEND)` are not on the forbidden list.

### Pitfall 11: Dry-run exit 17 and date-dependent tests
`--dry-run --row row1-wrong-binding` exits 17 whenever `tests/evidence/rerun-<UTC date>-claude-sonnet-5-5` exists; on 2026-10-29 it did. With campaign labels this holds per label. Tests that call the dry run with the real clock must pin the date.

### Pitfall 12: The local driver scripts under `runs/` are a source of facts, not of code
They are gitignored (a clone has none), they hold a real git identity and absolute home paths, and they call the real helper. Port the facts (seeds, prompts, orderings) into data files and seed functions that use the harness identity (`pc_spike._git_env` uses `Harness Spike` and an example.com address) and the stub.

### Pitfall 13: Row 12's s4 resumes s3's session
The committed s4 ran `--resume "$SID3"` (the fresh session), not s2's session. A generic "resume the first session" rule would be wrong. `StageSpec.session = "resume:B"`; `session_count` stays 2. The row 12 chain also has two `/preclear` turns and an external plan edit in between (snapshot `snap-2b`), so `_chain_incomplete` and the filed file names (`s4-*`) need a per-row stage list.

### Pitfall 14: Row 11's wrapper must be transparent
It sits in front of Claude Code's own git calls during s2. It must pass stdin, stdout, stderr and the exit code through unchanged, log only to its own files, and never fail the call because logging failed (the committed wrapper logs first, so a read-only log folder would break git for the model).

### Pitfall 15: Clean clone
Runs-root nesting, config-dir source, Keychain with a throwaway `HOME`, and push-before-clone (Clean clone bootstrap items 1, 2, 3, 5). Each is a plan task or a checkpoint; none can be left to the executor to discover.

## Code Examples

All Python sketches are 3.9-valid, stdlib only, and use the real helper names read this session. They are design sketches, not tested code.

### Frozen constants a new test must leave alone
```python
# Source: tests/harness/test_frozen_tree.py:36-39 (verbatim)
SKILL_SHA256 = "86e5b14e64b17397e3876768de398f15ddb40d6e31a3e605227dafed984c5a06"
REFERENCES_TREE_SHA256 = "0c2e133dedc56cf451206df72ab3cd894b7563bd0a51cfb9e1247cfd8b58fe25"
FIXTURES_TREE_SHA256 = "7f8ecc9bfe4d0e3fd7fee870c6f0f5b7d4dab8900a67389865ed30c58556a668"
PUBLICATION_TREE_SHA256 = "268818206a76c809ce832ba245e5bda648b7f48a46a56c6d9da8b08ef2aea117"
```
The `SKILL.md` size cap is 12,000 bytes (`SKILL_MAX_BYTES = 12000`); `SKILL.md` was 11,994 bytes at the Phase 3 close. [VERIFIED: test_frozen_tree.py:34-35; 03-06-SUMMARY.md]

### Row 7 live probe (HARN-12)
```python
# Source: design sketch; helpers are pc_runroot.exclusive_dir / write_exclusive (tests/harness/pc_runroot.py:81-100)
import errno, os
import pc_runroot

def chmod_denial_effective(raw_dir):
    """Return None when mode 555 denies a create, else the SKIP reason (no path in the text)."""
    if os.geteuid() == 0:
        return "the account is root, so mode 555 does not deny a create"
    probe = os.path.join(raw_dir, "probe-chmod")
    pc_runroot.exclusive_dir(probe, 0o700)
    os.chmod(probe, 0o555)
    try:
        pc_runroot.write_exclusive(os.path.join(probe, "x"), b"", 0o600)
    except PermissionError as problem:
        os.chmod(probe, 0o755)
        return None if problem.errno == errno.EACCES else "the create was refused with another error"
    os.chmod(probe, 0o755)
    return "a file was created inside a mode 555 folder"
```

### Fence scanner and Do-not-redo entries
```python
# Source: design sketch; the committed reply shape is row7 s2-preclear-trace.md:48-103
import re
_OPEN = re.compile(r"^(`{3,})[A-Za-z0-9_-]*\s*$")

def fenced_blocks(text):
    blocks, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        m = _OPEN.match(lines[i])
        if m:
            fence, body = m.group(1), []
            i += 1
            while i < len(lines) and not (lines[i].startswith(fence) and set(lines[i].strip()) == {"`"}):
                body.append(lines[i]); i += 1
            blocks.append("\n".join(body))
        i += 1
    return blocks

def printed_checkpoint(reply):
    found = [b for b in fenced_blocks(reply) if "## Identity and state" in b and "## Do not redo" in b]
    return found[-1] if found else None

def do_not_redo_entries(block):
    section, on = [], False
    for line in block.split("\n"):
        if line.startswith("## "):
            on = line.strip() == "## Do not redo"
            continue
        if on:
            section.append(line)
    entries = []
    for line in section:
        if line.startswith(("- ", "* ")):
            entries.append(line[2:].strip())
        elif entries and line.startswith((" ", "\t")) and line.strip():
            entries[-1] += " " + line.strip()
    if not entries:                      # row 4b prints plain lines, not bullets
        entries = [line.strip() for line in section if line.strip()]
    return entries
```
Run on the committed printed replies this session: row 7 gives 2 bulleted entries (the first is the unsupported "Workspace policy/registry checked: ..." entry), row 3c gives 2 bulleted entries, row 4b finds the block and its two entries are plain unbulleted lines (the committed trace lines 78-79), so a bullet-only parser would report zero entries for row 4b. [VERIFIED: sketch run against `row7-all-destinations-denied`, `row3c-unbound-fallback-none` and `row4b-conflicting-blocks` `s2-preclear-trace.md`]

### Git wrapper core (row 11; bash 3.2)
```bash
# Source: design sketch derived from the committed wrapper-git.sh and tests/harness/checkpoint-wrapper
W="$(cd "$(dirname "$0")" && pwd)"
REAL=$(cat "$W/real-git")
shown=$(printf ' %q' "$@")
"$REAL" "$@"; rc=$?
ord="-"
if [ -f "$W/match-argv" ] && [ "$shown" = "$(cat "$W/match-argv")" ]; then
  tok="$$.$RANDOM.$(date +%s)"
  printf '%s\n' "$tok" >> "$W/matches.log"          # one O_APPEND write
  ord=$(grep -n -F -x "$tok" "$W/matches.log" | head -1 | cut -d: -f1)
  if [ "$ord" = "$(cat "$W/fire-on")" ] && mkdir "$W/fired.lock" 2>/dev/null; then
    printf '\n- injected by the harness\n' >> "$W/../project/$(cat "$W/inject-file")"
    printf '%s\n' "INJECTED ORD=$ord" >> "$W/injection.log"
  fi
fi
printf '%s\n' "T=$(date -u +%FT%TZ) PID=$$ EXIT=$rc ORD=$ord ARGV=$shown" >> "$W/git-calls.log"
exit $rc
```
Notes: the matching argv is stored as the same `printf ' %q'` rendering; the injection runs after the real git, as committed; `fired.lock` and `matches.log` are absent in a no-op session; the log line is written once.

### Joining wrapper lines to `tool_use` ids (HARN-11)
```python
# Source: design sketch over pc_stream.tool_calls (tests/harness/pc_stream.py:229-243) and pc_checks._tokens
def join_ids(events, logged_argv_lines, is_git_part):
    """Return [(argv, [tool_use ids] or ["internal"] or ["ambiguous", ...])] aligned with the log."""
    expected = []                                    # (tool_use_id, argv) in stream order, executed calls only
    union = pc_stream.denial_report(events).union
    for tool_id, name, tool_input in pc_stream.tool_calls(events):
        command = tool_input.get("command")
        if name != "Bash" or not isinstance(command, str) or tool_id in union:
            continue
        for part in pc_allowlist.split_compound(command):
            words = pc_checks._tokens(part)
            if words and is_git_part(words):
                expected.append((tool_id, words[1:]))
    # consume expected in order, matching equal argv; a line whose argv starts with -c is Claude Code's own
```

### Status-form counts (HARN-10)
Executed parts are those whose `tool_use` id is not in `pc_stream.denial_report(events).union`; a part is the quoted form when its tokens, after `git`, are `--no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none` with no `-z`; a part is the sidecar NUL form when it holds `-z` and `pc_checks._read_redirections(part)` finds a redirect. Print the four counts and the denied ids; compare nothing to a reply.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Driver scripts under gitignored `runs/` with a real helper and a real git identity | Stdlib harness under `tests/harness/` with a stub helper and a harness identity | Phase 2 and 3 (2026-10-26 to 2026-10-29) | Seeds must be ported from facts, not copied |
| Rows run by hand against Claude Code 2.1.304, model not recorded | `claude-sonnet-5-5` on 2.1.310 through `--claude`, exact-match version gate | 2026-10-28 (D-12, D-13) | The new baseline is "a new baseline, not a replication" |
| First-pass row 11 injector matched any `status` argument | Whole-argv match plus ordinal | this phase | Fires only on the model's own call |
| `-z` sidecar expected in row 10 | Quoted-porcelain fallback is the expected outcome | 2026-10-20 (committed rerun), HARN-10 | No policy exception; the redirect refusal is the evidence |

**Deprecated/outdated:** the Phase 3 README sentence "Only row 1 is implemented in this phase" and the "README gives no cost figure" rule; `ROW_CAP`-as-sum reading for a four-stage row.

## Assumptions Log

> Claims tagged `[ASSUMED]` in this research. The planner and discuss-phase should confirm the ones with real risk before they become locked decisions.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `claude auth status` may report logged out when `HOME` is an empty throwaway folder and `USER`, `LOGNAME`, `TMPDIR` are absent (Keychain lookup behaviour unobserved) | Clean clone bootstrap items 3 and 4 | The first paid matrix wave stops at BLOCKED 12; a deviation from D-10 (real `HOME` for the child) would need bokiko's word |
| A2 | A `PreToolUse` command hook would fire in `-p` mode on 2.1.310 and carry `tool_use_id` (documented input; only `InstructionsLoaded` was observed headless) | Row 11 | None for the recommended post-hoc join; a live-id design built on it would fail |
| A3 | With `autoMemoryEnabled: false`, the init event may omit `memory_paths` | Pitfall 7, rows 5a and 5b | The isolation assertion `memory-path-as-set` stops a correct row 5 run unless made conditional |
| A4 | Per-chain costs by stage count (about 0.21, 0.27, 0.45) and the totals (about 5.3 per matrix, about 11 for the phase) extrapolate from the one measured chain | Spend and budget | Real rows (10, 11, 12, the helper rows) may cost more; bokiko's per-wave word covers this |
| A5 | Claude Code's own git calls always start with `-c` options (read from a garbled committed log); the exact-argv injector does not depend on it, only the `internal` label does | Row 11 | A few log lines mislabelled `ambiguous` instead of `internal` |
| A6 | `claude -p` 2.1.310 runs normally in a project folder with mode 555 (the committed row 7 ran on 2.1.304) | Row 7 | Row 7 stops early for a reason unrelated to the skill; visible as a STOPPED folder |
| A7 | The runs-root volume behaves like the scratchpad volume for `chmod 555` | Row 7 | None: the live probe in the run root decides at run time |
| A8 | The committed stage shapes (rows 2 to 7 without s3, rows 8a to 11 with s3, row 12 with s4) are the shapes to reproduce | Row table, Open Question 9 | Structural comparer differences larger than necessary, or missed read-only resume coverage |
| A9 | A row 12 s4 cap of about 0.60 USD and 20 turns is enough | Row 12 cap | A stopped row 12 on the cap; retried as a new attempt per D-03 |
| A10 | Claude Code accepts `--settings` with `autoMemoryEnabled: false` and the pinned directory (as the committed rows 5a and 5b settings did on 2.1.304) | Rows 5a and 5b | Row 5 stops at the first stage |

## Open Questions (RESOLVED)

Disposition of every question (planning revision, 2026-11-01): each is RESOLVED by a decision that a plan carries. Questions 1, 2 and 3 are resolved as a procedure whose answer only the real build or bokiko can give, so each also names the checkpoint where it is answered (DEFERRED to checkpoint). Question 12 is resolved by not building the item.

1. **Does the login survive a throwaway `HOME`?**
   - What we know: `run_preflight` asks `claude auth status --json` through `build_env`; the credential is in the Keychain keyed to the config folder; this research may not start `claude`.
   - What's unclear: whether an empty `HOME` and missing `USER` hide it (A1).
   - Recommendation: add `--preflight-only` to the bootstrap and have bokiko run it once before the clean-clone wave; if logged out, ask bokiko whether the child may keep the real `HOME`.
   - Resolution: RESOLVED as a procedure, DEFERRED to checkpoint in plan 04-20 for the answer itself. Plan 04-19 builds the free `--preflight-only` mode and the explicit `--real-home` flag (a recorded deviation that needs bokiko's word) and carries the owner's logged-in config folder through `PRECLEAR_HARNESS_HOME` (04-19 FA-1); plan 04-20 Task 1 runs the probe on the real build under the scrubbed environment before anything is asked, and Task 2 offers `go-real-home` or `stop` if it reports logged out. Whether the login survives is a fact only that run can show.
2. **Push timing for the clone.**
   - What we know: the clone holds only pushed commits; `main` equals `origin/main` at `e85d347`; a push is a hard-rule step.
   - What's unclear: when bokiko wants to push the Phase 4 code.
   - Recommendation: plan a checkpoint task "push, then record the pushed tip" before the clean-clone wave, and a local-path `--source` rehearsal (zero tokens) before it.
   - Resolution: RESOLVED as a procedure, DEFERRED to checkpoint in plan 04-20 for his timing. Plan 04-19 FA-3 puts the push in plan 04-20; plan 04-20 Task 1 counts the unpushed commits read only and rehearses the clone from a local path with `--source` at zero tokens, Task 2 asks him for the push timing (push now or not yet), and Task 3 pushes only after his go word, with the hooks running and no skip.
3. **Does the matrix's row 7 count as attempt 1 of three?**
   - What we know: D-12 says row 7 runs once in the matrix and the triple is its own wave; ROADMAP says "runs three times".
   - What's unclear: four chains or three (0.27 USD apart).
   - Recommendation: four chains (matrix once, triple three times), the review table covering the three triple attempts and listing the matrix run as a fourth section; ask bokiko only if cost matters. Triple folders are filed as `row7-all-destinations-denied-attempt-1..3` into the canonical dated folder after copy-back.
   - Resolution: RESOLVED with the recommended default fixed, DEFERRED to checkpoint in plan 04-17 for his decision. Plan 04-06 FA-1 records four chains (the triple, then the matrix's own run listed separately); plan 04-17 Task 2 asks him the counting question with that default, and plan 04-20 Task 2 item 5 restates his answer.
4. **Are the wave runs filed?**
   - What we know: D-02 files stopped rows visibly; a dated name can be used once (D-05).
   - What's unclear: whether waves A to D produce committed evidence.
   - Recommendation: file each wave under a labelled folder (`rerun-<date>-<model>-wave-a` ...), commit only on bokiko's word, and make the clean-clone folder the one canonical baseline.
   - Resolution: RESOLVED in plans 04-08, 04-11, 04-14, 04-16 and 04-17. Each paid wave files into its own labelled dated folder (`rerun-<date>-claude-sonnet-5-5-wave-a` to `-wave-d`, and `-triple` for the row 7 triple) as an attribution run, committed locally by the wave's task after his go word; the clean-clone folder of plan 04-20 is the one canonical baseline.
5. **The `--budget` ceiling and meaning.** Recommendation: a new `--budget` parser (ceiling for example 15.00, at least one row's worst case, stop before the row that would exceed it). The amounts per wave are bokiko's.
   - Resolution: RESOLVED in plan 04-02 Task 3: `--budget` is a per-invocation budget with a 25.00 ceiling, at least the largest single worst case of the selected rows, and a stop before the row that would pass it (exit 18). The amount for each wave is bokiko's at that wave's checkpoint; plan 04-20 recommends it from the measured costs of the earlier waves with headroom.
6. **Row 8a enclosing repository.** Recommendation: none (a true non-git tree), and say so in the README and the comparer's listed section; the committed run was stricter in one way (enclosing repo) and the harness is stricter in another (no repo anywhere).
   - Resolution: RESOLVED in plan 04-09: row 8a is a true non-git tree with no enclosing repository, its `setup_text` says so and the comparer lists the difference without judging it.
7. **Row 12 cap versus the 2 USD row cap.** Recommendation: read the cap as the ledger's pessimistic limit (as built), s4 cap about 0.60 USD and 20 turns, and accept that the printed worst case of row 12 exceeds 2.00.
   - Resolution: RESOLVED in plans 04-01 (FA-6) and 04-13 (Task 2): s4 has a 0.60 USD cap and 20 turns, the row stays under 2.00 by the spend ledger's own rule, and `worst_case` reports 2.00.
8. **Row 7 s3 with the restriction kept or lifted?** Recommendation: keep mode 555 through s3 and restore it after the last snapshot; the resumed session is read-only anyway and the setup then stays identical across stages.
   - Resolution: RESOLVED in plan 04-06: mode 555 is kept through s3 and the finalizer restores 755 after the last snapshot and the breach check, on every exit path of the row.
9. **Stage shapes for rows 2 to 7.** Recommendation: the committed shapes (two stages) so the comparer lines up; rows 8a to 11 and the layouts with s3; row 12 with s4. A row whose s2 prints a resume line but has no s3 is a documented difference, not a gap.
   - Resolution: RESOLVED in plan 04-01 (FA-5): two stages for rows 2 to 6, three for row 7 (D-05, plan 04-06), rows 8a to 11 and the three layouts, and four for row 12 (plan 04-13).
10. **Layout s1 prompts.** The committed layout runs did not store them. Recommendation: one data file per layout in the style of the row prompts ("Implement only step 2 of <plan> ... Do not run tests, commit, or start step 3 ... Keep the reply to three lines"), written once, pinned by digest.
   - Resolution: RESOLVED in plan 04-15 (Task 3 and FA-1): one data file `data/layout-s1-prompts.md` holds the plain-memory and hub-memory prompts under two headings, written once from the committed layout outputs and pinned by digest in a test; bound-ledger reuses the row 1 prompt.
11. **When and how the D-14 edit runs.** Recommendation: `record_verdict` runs one row at a time on bokiko's word after `codex-review.md` is filed; the new frozen-baseline test computes its digest with the verdict lines normalised.
   - Resolution: RESOLVED in plans 04-18 (Task 3) and 04-21 (Task 3): `record_verdict` edits one row README at a time, only on bokiko's word after `codex-review.md` is filed, and `frozen_digest` normalises exactly that line and leaves `codex-review.md` out.
12. **Live `tool_use` ids from a hook.** Recommendation: not now (A2); if bokiko wants it, a single paid probe of about 0.05 USD in a later phase.
   - Resolution: RESOLVED by not building it. Plans 04-10 and 04-12 join wrapper log lines to `tool_use` ids after the stage (04-12 FA-3), so nothing in Phase 4 depends on a live id from a hook; the single paid probe is DEFERRED to a later phase, only if bokiko asks, and appears in no plan.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 (system) | Harness, suite, bootstrap | yes | 3.9.6 (`/usr/bin/python3`) | none needed |
| bash (system, `/bin/bash`) | shims | yes | 3.2.57 (the `selftest` run printed it); the bash first on `PATH` is 5.3.9, which proves syntax only | none needed |
| git | fixtures, status capture, clone | yes | 2.50.1 (Apple Git-155) | none |
| gitleaks | pre-commit leak scan | yes | 8.30.0 (the version the rules were tested on) | the Python leak gate runs first in `promote` |
| shellcheck | lint of new bash files | yes | present | the lint test states a skip |
| gh | read-only repo checks, not required | yes | 2.83.2 | none needed |
| codex CLI | Codex review (bokiko's tab) | yes | 0.166.0 | bokiko pastes into Codex another way |
| Herdr | visible review tab (bokiko opens it) | yes | present | none; Claude never drives it (D-16) |
| claude on `PATH` | not used by the harness (`--claude` names the 2.1.310 build) | yes, version not probed here (probing runs claude) | the `PATH` build was 2.1.312 at Phase 3 and is refused by the version gate | `--claude <absolute path of the 2.1.310 build>`; its location was found by listing in Phase 3 and is not recorded in any file |
| Login state of the harness config folder | every paid wave | not probed (needs claude) | unknown | bokiko's one-time `claude auth login` with the config folder variable; the bootstrap preflight reports it for free |
| Network to the public repository | clean clone | not probed | unknown | clone a local path for the rehearsal |
| Non-root account | row 7 chmod denial | yes | uid is not 0 (`euid=501`) | row 7 files SKIPPED if the live probe fails |
| Runs root | all rows | yes | exists under the shared folder outside every home; the harness folder is mode `drwx------` | `PRECLEAR_RUNS_ROOT` |

**Missing dependencies with no fallback:** none known. **Unknown until bokiko runs a free check:** login under the scrubbed environment (A1).

## Security Domain

`security_enforcement` is on (`.planning/config.json`, level 1, block on high).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (harness never authenticates; only the boolean `loggedIn` is read) | the harness never reads, writes, copies or prints credentials |
| V3 Session Management | no | none implemented |
| V4 Access Control | yes (what the model may touch) | pinned allowlist, per-verb helper rules, strict isolation, realpath boundary on Write and Edit, snapshot diff |
| V5 Input Validation | yes | exact whole-id matching of `--row`, `--layout`, labels and attempt numbers (`ID_PATTERN`, `MAX_ID_LENGTH`); whole-token matching in the Do-not-redo candidates; NUL and size bounds on the resume line and the printed checkpoint |
| V6 Cryptography | no | only `hashlib` digests |
| V7 Error handling and logging | yes | fixed-text messages, counts and ids only, never a path, host name or login |
| V8 Data protection | yes | sanitizer built from the live machine, fail-closed leak gate, `promote` with deny entries, gitleaks at commit |
| V12 Files and resources | yes | exclusive creation, symlink and dot-dot refusal in `promote`, run-root guard, no deletion outside two test-support modules |
| V14 Configuration | yes | pinned flag table equal to the README, environment scrub, exact-match version gate |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Model writes outside the project (Bash redirect, interpreter, git) | Tampering | Open-world Bash rule, Write and Edit realpath scan, manifest diff of the run root; a breach is a STOPPED folder, nothing raw is filed |
| Model or hook rewrites the run's own record | Tampering | Guard files at every boundary (`BREACH_RECORD`) |
| Home path, login name, host name or credential in evidence | Information disclosure | Sanitizer, leak gate inside `promote`, gitleaks at commit; mode-only `perms.txt`; the review brief and `codex-review.md` are inside the folder and so are gated too; the brief goes to an external service, so it is gated before it leaves |
| Clone supplies code that runs on the owner's machine | Spoofing, Tampering | Public repository of the owner only, `HEAD` recorded and compared with the pushed tip, no hooks in the clone, `GIT_CONFIG_NOSYSTEM` and a null global config for the clone |
| Environment carries tokens into the model's Bash | Information disclosure | `env -i` plus allowlist for the driver, `build_env` allowlist for the child, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` |
| Planted git config makes the harness run a command | Elevation | `core.fsmonitor=false` hardening, the setup gitdir pin held in memory, nested-repository refusal, `config-command` counted as a mutation |
| Silent overspend | Denial of service (cost) | Reserve-before-launch ledger, per-stage caps, per-invocation budget stop, go word per wave; a subagent report is never an approval |
| The one in-place edit (D-14) used to alter evidence | Tampering | Dedicated function that edits only the last line of a row README, leak-gates the new bytes, runs on bokiko's word; the frozen-baseline test normalises exactly that line and nothing else |
| A model-written fake `## Do not redo` entry or tool result steering the review table | Tampering | The table lists candidates and counts only; Codex and bokiko confirm; no automatic verdict (EVID-05) |

## Sources

### Primary (HIGH confidence)
- Repository files read this session: `.planning/phases/04-full-matrix-row-7-and-review/04-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` (Phase 4), `.planning/phases/03-walking-skeleton-row-1/03-CONTEXT.md`, `03-06-SUMMARY.md`, `03-REVIEW-2..5-DISPOSITION.md`, `tests/harness/README.md`, `tests/acceptance.md`, `tests/harness/data/spike-findings.md`, `SKILL.md` (Step 3, Step 4), `references/status-sidecar.md`, `CHANGELOG.md`, `.githooks/README.md`, `.gitignore`.
- Harness code read: `pc_rows.py`, `pc_matrix.py`, `pc_row1.py`, `pc_evidence.py`, `pc_checks.py` (structure, `git_state`, `helper_calls`, `compute_facts`, `breaches`), `pc_promote.py`, `pc_compare.py`, `pc_flags.py`, `pc_spend.py`, `pc_spike.py` (`harness_home`, `runs_root`, `run_claude`, `s1_evaluation`, `_fill_configuration`), `pc_preflight.py`, `pc_exitcodes.py`, `pc_stream.py`, `pc_hooklog.py`, `pc_manifest.py`, `pc_mine.py`, `pc_sanitize.py`, `pc_allowlist.py`, `pc_seeds.py`, `pc_testutil.py`, `checkpoint-wrapper`, `selftest`, and the tests `test_frozen_tree.py`, `test_frozen_reference.py`, `test_readme.py`, `test_bash_shims.py`, `test_runroot.py` (static scan), `test_stages.py`, `test_checks.py` (corpus), `test_allowlist.py`, `test_evidence.py` (vocabulary), `test_matrix_cli.py`.
- Committed evidence read: every row folder of `tests/evidence/publication-2026-10-20/` (README setup paragraphs, `tools.txt` for all, `fixture-CLAUDE.md` digests, `snap-0-setup` listings, row 2 injection log, row 7 trace and `perms.txt`, row 10 and 11 rerun traces and `wrapper-git.sh`, row 12 prompts), the three layout evidence folders' READMEs, and the filed baseline `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` (README, `usage.txt`, `digests.txt`).
- Gitignored local driver scripts `runs/pub-lib.sh`, `pub-plain.sh`, `pub-row.sh`, `pub-env.sh` (facts only; not copied).
- Observations made by running read-only commands or scratch probes this session: the chmod 555 probe, the fence scanner against committed traces, `python3 -I -B -m unittest discover` (1305 tests OK), tool versions.

### Secondary (MEDIUM confidence)
- [CITED: https://code.claude.com/docs/en/hooks] PreToolUse input fields including `tool_use_id`; the page excerpt read did not state print-mode behaviour for every event (first 100,000 of 284,258 characters read).

### Tertiary (LOW confidence)
- None used for a recommendation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, no new dependency; everything is read from the repository and the environment.
- Architecture: HIGH for what exists and where it is row-1-specific (read in full); MEDIUM for the recommended designs (untested sketches, one verified probe, one verified parser run on committed fixtures).
- Pitfalls: HIGH for the code-derived ones (1, 2, 3, 5, 6, 9 to 13); MEDIUM for 7 and 15 (depend on unobserved Claude Code 2.1.310 behaviour, A1 and A3).
- Costs: LOW to MEDIUM (one measured chain, extrapolated).

**Research date:** 2026-11-01
**Valid until:** 2026-12-01, or until `tests/harness/` changes shape (the line references above are to HEAD `e85d347`); re-read `pc_rows.py` and `pc_matrix.py` first if either has moved.
