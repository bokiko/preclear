# Phase 4: Full Matrix, Row 7 and Review - Context

**Gathered:** 2026-10-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Every remaining publication row (2 to 12) and the three layouts run through the Phase 3 harness
on the pinned model, each wave spending only on bokiko's word. Row 7 runs three times as
independent chains with a review table that pairs every Do-not-redo entry of each printed
checkpoint with the tool calls that support it. Row 10 keeps the quoted-porcelain fallback as
its expected outcome and row 11's injector fires on the n-th model-initiated call. Then a
bootstrap clones the public repository into a never-used path with a minimal environment and
runs `--all`, filed as a new dated baseline with a per-row digest table, cost per row and the
comparer's differences against `tests/evidence/publication-2026-10-20/`. Codex reviews that
folder in a visible Herdr tab, its verdicts are recorded per row, and `tests/harness/README.md`
becomes the entry point that `tests/acceptance.md` and `CHANGELOG.md` point to. Nothing in this
phase edits `SKILL.md`, `references/`, `tests/fixtures/` or any filed evidence folder except the
one verdict line named in D-14.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase contract
- `.planning/ROADMAP.md` §Phase 4 — goal, five success criteria, the three-plan outline, standing
  rules (budget word before multi-run spend, evidence never edited, verdicts only after Codex)
- `.planning/REQUIREMENTS.md` — HARN-10, HARN-11, HARN-12, RERUN-01 to RERUN-05; HARN-02 (a skip
  never reads as pass), EVID-05 (no verdict printed), EVID-06 (comparer)
- `.planning/PROJECT.md` — constraints and key decisions (row 7 disclosed and rerun three times,
  row 10 fallback, baseline labelling, cumulative cost, frozen 2026-10-29 baseline)
- `.planning/STATE.md` — Phase 3 blockers carried into Phase 4 (chmod denial, `-z` never executed
  headless, Bash rule residuals, dated-destination exit 17)

### What the rows and layouts are
- `tests/acceptance.md` §Common checks, §plain-memory, §hub-memory, §bound-ledger, §Publication
  matrix — the layout checklists (D-13 picks the core chain) and the twelve-row order
- `tests/evidence/publication-2026-10-20/README.md` — folder-level README shape and the
  carried-forward-row notes
- `tests/evidence/publication-2026-10-20/row7-all-destinations-denied/` — the committed row 7
  (s1, s2, `snap-1b-after-restriction/perms.txt`, the unsupported Do-not-redo entry in README)
- `tests/evidence/publication-2026-10-20/row10-large-status-rerun/` — the quoted-porcelain
  fallback and the exact status command the allowlist must match (HARN-10)
- `tests/evidence/publication-2026-10-20/row11-concurrent-change-rerun/` — `wrapper-git.sh` and
  `git-calls.log`: the injector that fires only on the model's own status call (HARN-11)
- `tests/evidence/publication-2026-10-20/row2-double-conflict/` and the other row folders — the
  per-row file sets and `tools.txt` allowlists the new row hooks reproduce
- `tests/evidence/plain-memory-2026-10-19/`, `hub-memory-2026-10-19-rerun/`,
  `bound-ledger-2026-10-19-rerun/` — the committed layout evidence the layout chains line up with

### What Phase 3 built
- `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` — the filed row 1 baseline (frozen): the
  per-row file set, `usage.txt`, `mechanical-checks.md`, folder README wording
- `tests/harness/README.md` — flag table, exit-code table, running one row, what a run files,
  comparing a rerun, platforms, limits; RERUN-05 extends it
- `.planning/phases/03-walking-skeleton-row-1/03-CONTEXT.md` — D-01 to D-14 and the carried rules
- `.planning/phases/03-walking-skeleton-row-1/03-06-SUMMARY.md` — the measured cost and how it
  was derived
- `.planning/phases/03-walking-skeleton-row-1/03-REVIEW-2-DISPOSITION.md` to
  `03-REVIEW-5-DISPOSITION.md` — deferred warnings and the three accepted Bash-rule residuals
- `.planning/phases/03-walking-skeleton-row-1/03-VERIFICATION.md` — the verified state of HARN-09
- `.planning/phases/02-model-free-foundation-and-stub/02-CONTEXT.md` — isolation and stub decisions
- `tests/harness/data/spike-findings.md` — stream facts on 2.1.310, session-id handling

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/harness/pc_matrix.py`: the driver (`--list`, `--row`, `--layout`, `--all`, `--dry-run`,
  `--claude`, `--budget`, `--refile`); today every entry except row 1 lists `implemented no`.
- `tests/harness/pc_rows.py`: `ROW_IDS`, `LAYOUT_IDS`, `StageSpec`, `RowSpec`, `RunContext`,
  `RowOutcome`, `build_registry`, `evidence_folder_name`; new rows register here with their caps.
- `tests/harness/pc_row1.py`: `seed_row1`, `take_snapshot`, `run_stage`, `run_row`,
  `extract_resume_line`, `breach_outcome`, `paths_for`, `finish`; the chain every new row reuses.
- `tests/harness/pc_seeds.py`: fixture materialisation (the only module beside `pc_testutil.py`
  allowed deletion primitives); row seeds for the restriction step, the hostile-name tree, the
  non-git and worktree cases go here.
- `tests/harness/checkpoint-wrapper`: the logging wrapper with the conflict injector
  (`injection.log`, `armed` counter) — the model for a git wrapper injector for row 11.
- `tests/harness/pc_preflight.py`, `pc_exitcodes.py`: SKIP, FAIL, BLOCKED and the exit-code
  agreement test; the chmod probe adds a SKIP reason, not a new code family.
- `tests/harness/pc_allowlist.py`: `row_rules(folder)` reads a committed row's `tools.txt`; the
  open-world write rule; the corpus test over all committed traces.
- `tests/harness/pc_checks.py`, `pc_manifest.py`, `pc_evidence.py`, `pc_promote.py`,
  `pc_compare.py`, `pc_spend.py`, `pc_stream.py`: breach checks, snapshots, filing, promotion,
  comparer, spend ledger (cumulative-consistent lines), stream parser with `tool_use` ids.
- `tests/harness/selftest` and `test_readme.py`: the zero-token gate and the README-equals-code
  tests every new flag, exit reason and file must extend.

### Established Patterns
- One go word per paid step, quoted verbatim in a fresh executor dispatch; a paused executor is
  never resumed (Phase 3 lesson).
- Append-only ledgers, counts only in printed text, raw captures only under the run root,
  sanitise then leak-gate then exclusive write.
- Every paid path is tested through a scripted fake `claude`; the self-test never starts a model.
- Filed folders are frozen; a test (`test_frozen_tree.py`, `test_frozen_reference.py`) diffs them
  against the commit that filed them.

### Integration Points
- New row hooks plug into `pc_rows.build_registry` and the stage runner of `pc_row1` (rename or
  generalise at the planner's discretion); `--list` flips `implemented` per row.
- The bootstrap script wraps `pc_matrix.py --all` with the `env -i` allowlist (D-10) and the
  helper-unreachable assertions (D-11); it lives under `tests/harness/` and is bash 3.2.
- The row 7 review table, the Codex review brief and `codex-review.md` are new top-level files in
  the evidence folder; `test_evidence.py` and the README file list grow with them.
- `pc_compare.py` gains a configurable reference target for D-15 after the verdicts.

</code_context>

<specifics>
## Specific Ideas

- The three row 7 attempts must be readable side by side: one review file, one section per
  attempt, failed attempts included.
- An `UNSUPPORTED` Do-not-redo entry is printed as such; the harness lists candidates and never
  decides.
- The clean-clone README states the environment variable names used and both helper-unreachable
  facts as counts.
- Every wave ends with its measured cost in the conversation before the next go word is asked.

</specifics>

<deferred>
## Deferred Ideas

- Full layout checklists as harness stages (identity collision, blocked instruction, freshness,
  tamper, repeat `/preclear`) — v2 (HARN-V2-03 territory).
- A tagged CHANGELOG release recording the skill digest per accepted baseline — after this phase.
- A second-OS (Linux) validation run and the Linux credential-file location — HARN-V2-05.
- A `SKILL.md` rule that Do-not-redo entries must cite a check made in the current session — only
  if the row 7 triple shows the defect recurs (HARN-V2-04); the skill is frozen in this phase.
- Resumable matrix that skips finished rows — HARN-V2-01.

</deferred>

---

*Phase: 04-full-matrix-row-7-and-review*
*Context gathered: 2026-10-31*
