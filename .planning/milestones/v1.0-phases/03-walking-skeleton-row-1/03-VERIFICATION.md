---
phase: 03-walking-skeleton-row-1
verified: 2026-11-13T12:22:37Z
status: passed
score: 6/6 must-haves verified
covered_files:
  - ".planning/phases/03-walking-skeleton-row-1/03-01-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-01-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-02-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-02-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-03-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-03-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-04-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-04-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-05-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-05-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-06-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-06-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-07-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-07-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-08-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-08-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-09-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-09-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-10-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-10-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-11-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-11-SUMMARY.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-12-PLAN.md"
  - ".planning/phases/03-walking-skeleton-row-1/03-12-SUMMARY.md"
  - "SKILL.md"
  - "references/checkpoint-v1.md"
  - "references/configuration.md"
  - "references/status-sidecar.md"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/README.md"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/README.md"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/digests.txt"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/isolation-mode.txt"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/mechanical-checks.md"
  - "tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/row1-wrong-binding/usage.txt"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/row1-wrong-binding/README.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/row1-wrong-binding/mechanical-checks.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/row1-wrong-binding/usage.txt"
  - "tests/harness/README.md"
  - "tests/harness/checkpoint_stub.py"
  - "tests/harness/pc_allowlist.py"
  - "tests/harness/pc_checks.py"
  - "tests/harness/pc_compare.py"
  - "tests/harness/pc_evidence.py"
  - "tests/harness/pc_exitcodes.py"
  - "tests/harness/pc_leakgate.py"
  - "tests/harness/pc_manifest.py"
  - "tests/harness/pc_matrix.py"
  - "tests/harness/pc_preflight.py"
  - "tests/harness/pc_promote.py"
  - "tests/harness/pc_row1.py"
  - "tests/harness/pc_rows.py"
  - "tests/harness/pc_spend.py"
  - "tests/harness/pc_stream.py"
  - "tests/harness/pc_testutil.py"
  - "tests/harness/test_checks.py"
  - "tests/harness/test_evidence.py"
  - "tests/harness/test_row1_assertions.py"
  - "tests/harness/test_stages.py"
covered_digest: "v3:sha256:f52ba527893f4114787ca01f87d5192efe3b5abe8f85f4b740ea5d8a664bbb26"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 6/6
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 3: Walking Skeleton (Row 1) Verification Report

**Phase Goal:** One row, row 1 (wrong binding), runs end to end through the real `claude -p` against the stub from a single command, is filed as sanitized evidence in a new dated folder with mechanical facts only, and lines up structurally with the committed row 1 evidence.
**Verified:** 2026-11-13T12:22:37Z
**Status:** passed
**Re-verification:** Yes, at milestone close. The earlier report passed 6/6 on 2026-10-29 and went stale because Phase 4 changed thirteen covered harness files.

## Verdict

The phase goal still holds on the current tree. I re-read the code and re-ran the zero-token checks instead of trusting the earlier report or the summaries. Six of six truths verify and no gap was found.

Phase 4 grew the harness a great deal, but it did not weaken any Phase 3 behavior. The row 1 write-escape rule, the hardened git reads, the refile refusal and the verdict line are all still in force and still behave as the earlier report described.

I did not run the unit test suite, the selftest or any `claude` command, as instructed. The 2405 passing tests (3 skipped) on 2026-11-12 come from the orchestrator and are not independently confirmed here.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria. Truth 6 is derived from the goal and carried from the earlier report.

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | `--list`, `--dry-run`, unknown ids and the three preflight codes behave as specified; a SKIPPED row files under a SKIPPED label (HARN-01, HARN-02) | VERIFIED | With no `claude` on PATH, `--list` exits 0 and prints 3 layouts and 18 rows, all implemented. `--row nope`, `--layout nope`, `--row row3`, an upper-case id and a bare `--row` each exit 2. `--dry-run --row row1-wrong-binding` prints 3 stages, 2 sessions, caps 0.30, 1.30 and 0.40, worst case 2.00 USD, and exits 0. `--dry-run --all` exits 0. The exit code module names 10 skip, 11 fail and 12 blocked. A SKIPPED label writer exists and ends on the verdict line. |
| 2 | One real row 1 run is filed in a new dated folder under `tests/evidence/` with the committed file set plus the five new files, every provenance field non-empty, every file leak-gated (HARN-05, EVID-04) | VERIFIED | The folder `rerun-2026-10-29-claude-sonnet-5-5` holds 65 files and has not changed since its filing commit. The row folder carries the five new files, all non-empty: Claude Code 2.1.310, model claude-sonnet-5-5, strict isolation, digests, tools and per-stage usage with cost. The leak gate scan of the folder reports 65 files, 0 findings. |
| 3 | The init manifest is asserted, the isolation mode is recorded as spike S1 decided, and the write-boundary and git-read-only checks report zero on the real run and fail on a seeded out-of-root write (HARN-07, HARN-09) | VERIFIED | The filed mechanical checks show ten init assertions per stage, all yes. The isolation file says strict. They show zero snapshot paths outside the roots, zero Write-tool paths, zero Bash outside paths, an absent default memory folder and zero git mutations. I seeded 17 hostile Bash commands against the current checker with fake roots. Every one counted as exactly one write escape. Six harmless forms counted zero. `breaches()` turned one escape into a write breach. See the HARN-09 section. |
| 4 | The row README ends with `Reviewer verdict: PENDING` and a mechanical checklist, and no harness-authored file carries an accepted, passed or failed verdict (EVID-05) | VERIFIED | The last line of the filed row README is the pending line. The harness still writes that exact line in the filing code. A whole-word search of the folder for verdict words matched that line and model-authored text only (checkpoint prose and trace content). The comparer output carries no verdict word. |
| 5 | The read-only comparer prints per-row differences against the committed row 1 and leaves both trees byte-identical; the frozen trees are unchanged; `SKILL.md` is at most 12,000 bytes; all new code is under `tests/harness/` (EVID-06, HARN-13) | VERIFIED | The comparer exits 0 against both the 2026-10-29 folder and the 2026-11-11 baseline. In both runs the tree digests before and after are identical for both sides, and the report says old unchanged yes and new unchanged yes. A diff from the phase base shows no change to `SKILL.md`, `references/`, `tests/fixtures/` or the committed publication folder, and no modified or deleted file under `tests/evidence/`. `SKILL.md` is 11,994 bytes. See the warning on two documentation files. |
| 6 | A run the live path refused cannot be filed as a baseline by `--refile` (derived: filed evidence is the record of a clean run) | VERIFIED | `_unfileable` in `tests/harness/pc_evidence.py` refuses any stage record whose problem is not empty or whose evaluation is not the pass value, then requires the chain the registry defines for the row. This is still in place after the Phase 4 rewrite of that module. |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### HARN-09 on the current tree

HARN-09 is met. I reproduced the three mechanisms the earlier report relied on.

- **Bash write outside the roots.** `breaches()` adds the Bash write-escape count to the writes total. The seeded probe covered mkdir, tee, cp, a redirect, sed -i, curl -o, rm, a tilde path, a dot-dot path, `bash -c`, a `cd` then touch, a pipe into tee, mv, dd, ln, rsync and tar -C. None was missed.
- **Planted git configuration.** I planted a `core.fsmonitor` command in a throwaway repository. A plain `git status` created its marker, so the probe can see what it guards. `git_state` and `capture_git_status` with the setup pin did not create it. After the git folder changed, `git_state` returned the not-read state and started no process.
- **Run-level evidence.** The Phase 4 baseline row 1 run, produced under the current rule, shows `bash-write-escapes: 0`, zero mutations and zero outside paths.

The check is a conservative classifier over command text, not a sandbox. Its documented limits are carried over from the earlier report and the harness README and are not new.

### Measured Cost

The row total in the filed usage file is 0.2723 USD and the three per-call costs sum to it. The Phase 4 clean-clone baseline ran row 1 again through the generalized engine at 0.2682 USD. That run's usage file carries the cumulative-consistent flag for s2 and s3, which closes the residue the earlier report left in the frozen folder.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/harness/pc_matrix.py` | Driver: list, plan, run, refile, authorize-retry | VERIFIED | Ran list, dry run and the refusal ids. |
| `tests/harness/pc_exitcodes.py` | Distinct codes for skip, fail and blocked | VERIFIED | Codes 10, 11 and 12, all other codes distinct. |
| `tests/harness/pc_spend.py` | File-locked matrix ledger | VERIFIED | Unchanged since the earlier verification. |
| `tests/harness/pc_row1.py` | Seed, three-stage chain, init and instruction audit | VERIFIED | Produced the 2026-10-29 run and still drives the 2026-11-11 row 1 run. |
| `tests/harness/pc_checks.py` | Mechanical facts and breaches | VERIFIED | Open-world write rule wired into `breaches()`; git reads hardened. |
| `tests/harness/pc_manifest.py` | Hardened git status, pin guard | VERIFIED | Hardening tuple used by both capture paths; refuses before any process when the git folder differs from the pin. |
| `tests/harness/pc_evidence.py` | Filing, SKIPPED, refile, checklist | VERIFIED | Clean-stage and chain refusals present; verdict line written. |
| `tests/harness/pc_compare.py` | Read-only comparer with tree digests | VERIFIED | Ran it twice; digests identical before and after. |
| `tests/harness/pc_leakgate.py` | Fail-closed leak gate | VERIFIED | Scanned both row 1 folders, 0 findings. |
| `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` | New baseline folder | VERIFIED | See truth 2. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pc_matrix.py` real path | `pc_row1` then `pc_evidence.file_row` | run, checks, filing | WIRED | Produced the real folder and the later baseline row. |
| `pc_row1.finish` | `pc_checks.breaches` | exit 11 on breach | WIRED | `breaches()` sums snapshot, trace, Bash escape and default-memory writes, git mutations and run-record changes. |
| `pc_checks.git_state`, `pc_manifest.capture_git_status` | git | hardening flags plus pin and nested-repository guard | WIRED | Probe marker never created. |
| `pc_evidence.file_row` | sanitizer, leak gate, promote | filing through the gate | WIRED | Folder scans clean. |
| `pc_matrix --refile` | `pc_evidence.file_row` | same filing function | WIRED | Same refusals as the live path. |
| `pc_compare.py` | both evidence trees | read only | WIRED | Digests identical before and after. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `usage.txt` | per-stage cost and tokens | result events of the real streams | Yes | FLOWING |
| `mechanical-checks.md` | init manifest, counts, ids | real streams, snapshots, wrapper log | Yes | FLOWING |
| `digests.txt` | skill and adapter digests | files on disk at run time | Yes | FLOWING |

### Behavioral Spot-Checks

All ran read-only with no `claude` on PATH. The working tree showed no change from them.

| Behavior | Command shape | Result | Status |
| -------- | ------------- | ------ | ------ |
| List | driver `--list` | exit 0, 3 layouts and 18 rows | PASS |
| Unknown ids | `--row nope`, `--layout nope`, `--row row3`, upper-case id, bare `--row` | exit 2 each | PASS |
| Dry run | `--dry-run` for row 1 and for `--all` | plan printed, gate ok, exit 0 | PASS |
| Comparer read-only | comparer against the 2026-10-29 and 2026-11-11 trees | exit 0, digests identical before and after | PASS |
| Leak gate | scan of both row 1 folders | 65 and 64 files, 0 findings | PASS |
| Bash write rule | 17 hostile and 6 harmless seeded commands | 0 missed, 0 false positives | PASS |
| Planted fsmonitor | throwaway repository | control creates the marker; harness never does | PASS |

The unit suite was not run by this verifier.

### Probe Execution

No probe scripts are declared by the plans. Step 7c: SKIPPED (none declared).

### Requirements Coverage

All nine phase IDs appear in plan frontmatter across plans 03-01 to 03-12. REQUIREMENTS.md maps exactly these nine to Phase 3 and marks each Complete, so none is orphaned.

| Requirement | Source plans | Description | Status | Evidence |
| ----------- | ------------ | ----------- | ------ | -------- |
| HARN-01 | 03-01 | One command with list, row, layout, all, dry-run | SATISFIED | Spot-checks. |
| HARN-02 | 03-01 | SKIP, FAIL and BLOCKED distinct, skipped never a pass | SATISFIED | Codes 10, 11, 12; SKIPPED writer. |
| HARN-05 | 03-02, 03-04, 03-06, 03-08, 03-09 | Provenance recorded per run | SATISFIED | Truth 2. |
| HARN-07 | 03-02, 03-06 | Init manifest asserted every run, isolation mode recorded | SATISFIED | Truth 3. |
| HARN-09 | 03-03, 03-06, 03-07, 03-08, 03-09, 03-10, 03-11, 03-12 | Mechanical write-boundary and git-read-only assertions | SATISFIED | HARN-09 section. |
| HARN-13 | 03-05, 03-06 | New work under `tests/harness/`, skill frozen, size cap | SATISFIED | Truth 5, with the documentation warning below. |
| EVID-04 | 03-04, 03-06, 03-08, 03-09 | Per-row file set written exclusively into a new dated folder | SATISFIED | Truth 2 and truth 6. |
| EVID-05 | 03-04, 03-06 | No verdict printed, PENDING plus checklist | SATISFIED | Truth 4. |
| EVID-06 | 03-05, 03-06 | Read-only structural comparer | SATISFIED | Truth 5. |

### Anti-Patterns Found

I did not repeat the full debt-marker sweep. The earlier sweep found only mktemp templates and one ledger placeholder constant. Phase 4 added files, and the flagged Phase 3 modules showed no stub or empty implementation in the code I read.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| none | - | - | - | No blocker found |

### Warnings

None of these changes the status.

- **Two documentation files changed outside `tests/harness/`.** Phase 4 added eight lines to the changelog and to the acceptance checklist, both pointing at the harness. HARN-13 says new work lives under `tests/harness/`. These are documentation additions made by Phase 4's documentation plan, and the files the requirement freezes are untouched.
- **The Phase 4 baseline row README does not end in the pending line.** Phase 4 designed a one-line reviewer edit taken from the Codex review. The harness still writes the pending line, and the frozen Phase 3 folder keeps it. This is a reviewer edit, not a harness-printed verdict.
- **Known non-blocking items.** The unbounded integer parse in the comparer, the project and local setting-sources observation and the tar probe are recorded in the state file and the security report. None breaks the phase goal. The security report shows 87 of 88 threats closed.
- **Deferred review warnings and write-rule limits.** The earlier report lists them and they are unchanged. They remain hardening items, not gaps.
- **A modified second-phase report is in the working tree.** `.planning/phases/02-model-free-foundation-and-stub/02-VERIFICATION.md` showed as modified during my run. I did not touch it.

### Human Verification Required

None. Every item I checked is decidable from files and zero-token commands. The row's reviewer verdict stays pending by design.

## Gaps Summary

No gaps. The phase goal is achieved on the current tree and the fingerprint below replaces the stale one.

---

_Verified: 2026-11-13T12:22:37Z_
_Verifier: Claude (gsd-verifier)_
