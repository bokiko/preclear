---
phase: 03-walking-skeleton-row-1
verified: 2026-10-29T09:20:00Z
status: gaps_found
score: 4/6 must-haves verified
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
  - "tests/harness/README.md"
  - "tests/harness/checkpoint_stub.py"
  - "tests/harness/pc_allowlist.py"
  - "tests/harness/pc_checks.py"
  - "tests/harness/pc_compare.py"
  - "tests/harness/pc_evidence.py"
  - "tests/harness/pc_manifest.py"
  - "tests/harness/pc_matrix.py"
  - "tests/harness/pc_preflight.py"
  - "tests/harness/pc_row1.py"
  - "tests/harness/pc_rows.py"
  - "tests/harness/pc_spend.py"
  - "tests/harness/test_checks.py"
  - "tests/harness/test_evidence.py"
covered_digest: "v3:sha256:789acdc78d6aa3510911ab24972e13af90c6274d451ef6cb7f013de3daa56cd6"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Write-boundary and git-read-only checks are mechanical and sound: a write outside the approved roots, by any tool the model can reach, ends the row with exit 11 (roadmap criterion 3, HARN-09)"
    status: failed
    reason: "Two holes reproduced by the code review (CR-02 and CR-03, both still open in the review disposition) and confirmed by me in the code, not re-run. A write-capable Bash command (mkdir, tee, cp, mv, touch, dd, install) aimed at a path outside the run root is only listed as a fact and never counted as a breach, and the snapshot cannot see outside the run root, so such a row files with exit 0. Separately, the harness runs git status inside the model's project after each stage without disabling core.fsmonitor, so a command the model planted in the project's .git/config executes as the harness user, before the breach check runs. The seeded fixtures required by the criterion pass (snapshot path, Write-tool path, commit), and the real run is clean, so the criterion's literal text holds; the mechanism behind HARN-09 does not."
    artifacts:
      - path: "tests/harness/pc_checks.py"
        issue: "bash_mentions() lists outside-path words and write programs but breaches() never reads them; words that are not absolute (tilde, dollar-HOME, dot-dot) are not even counted"
      - path: "tests/harness/test_checks.py"
        issue: "test_an_outside_path_mention_is_listed_and_the_run_still_returns_zero pins the current behaviour"
      - path: "tests/harness/pc_manifest.py"
        issue: "_run_git_status builds the command without -c core.fsmonitor=false; pc_checks._git_output has the same shape"
    missing:
      - "Count an executed write-capable program that names a path outside the approved roots, or a tilde, dollar or dot-dot expansion, as a write breach (exit 11); keep read-only mentions as facts"
      - "Pass -c core.fsmonitor=false (and the untracked-cache off setting) on every harness git call against a model-writable repository, with a test that plants a config command and asserts its marker is never created"
      - "Revisit the plan 03-03 decision that Bash mentions never decide a breach; it was implemented as planned and is the root of CR-02"
  - truth: "A run the live path refused cannot be filed as a baseline by the zero-token refile (derived from the phase goal: filed evidence is the record of a clean run)"
    status: failed
    reason: "Code review CR-01, still open. file_row only calls _unfileable, which checks that each stage has a prompt and a parseable stream. It never reads the stage record's problem or evaluation fields, so --refile of a run that ended on error_max_turns or a failed isolation assertion files a full folder and exits 0. I confirmed the cause in the code; I did not re-run the reviewer's reproduction."
    artifacts:
      - path: "tests/harness/pc_evidence.py"
        issue: "_unfileable (line 1017) never reads the stage evaluation or problem fields"
    missing:
      - "Refuse in file_row any run whose stage records are not clean, using the rule the live path uses, with a test that stops a chain at s2 and asserts --refile exits 11 and creates nothing"
  - truth: "Filed mechanical facts are accurate and complete enough for the reviewer to read without being misled (EVID-04, HARN-05)"
    status: partial
    reason: "Three review findings routed to gap closure. status-begins-with-session is no in the filed baseline because the real tool result starts with the stub's brand line, and the scripted claude hides this by returning stdout only (WR-02). usage.txt does not show the cumulative-consistency flag the harness computes, so the 0.2723 USD row cost rests on fixtures and the review rather than on the filed file (IN-01). file_row does not require deny entries, so the sanitizer deny-list contract is held by convention in every caller rather than by the API (WR-03)."
    artifacts:
      - path: "tests/harness/pc_checks.py"
        issue: "line 725: lstrip().startswith(\"session\") can never be yes on a real run"
      - path: "tests/harness/pc_evidence.py"
        issue: "usage rendering omits cumulative_consistent; file_row does not refuse deny_entries None"
    missing:
      - "Look for a line starting with session in the first few lines, and make the scripted claude return stdout then stderr as the real tool does"
      - "Write the cumulative-consistency flag to usage.txt and warn when it is no; make file_row refuse deny_entries None"
      - "Fix the leftover sentence in the 03-06 summary (unobserved question 2) that still calls the cumulative question unsettled"
---

# Phase 3: Walking Skeleton (Row 1) Verification Report

**Phase Goal:** One row, row 1 (wrong binding), runs end to end through the real `claude -p` against the stub from a single command, is filed as sanitized evidence in a new dated folder with mechanical facts only, and lines up structurally with the committed row 1 evidence.
**Verified:** 2026-10-29T09:20:00Z
**Status:** gaps_found
**Re-verification:** No, initial verification

## Verdict

The walking skeleton works and the evidence is real. One paid row 1 run on Claude Code 2.1.310 and claude-sonnet-5-5 was filed as a leak-gated folder, the comparer lines it up with the committed row without touching either tree, and the zero-token suite is green. Four of six truths verify.

The phase does not close yet. Three critical code review findings are open and I reproduced their cause in the code. Two of them (CR-02, CR-03) mean the HARN-09 write-boundary and git-read-only checks can report clean when they are not. The third (CR-01) lets the zero-token refile record a refused run as a baseline. All three are already routed to a gap-closure plan in the review disposition. The real run itself shows no breach, so the filed baseline's own facts are not in doubt.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria, which are the contract. Truth 6 is derived from the goal. The plan frontmatter truths were checked against these and none reduces their scope.

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | `--list`, `--dry-run`, unknown ids and the three preflight codes behave as specified; a SKIPPED row files under a SKIPPED label (HARN-01, HARN-02) | VERIFIED | See the spot-check table. Exit codes 10, 11 and 12 are named in `pc_exitcodes.py`. The SKIPPED label is exercised by `test_a_real_run_skip_files_a_label_folder_and_exits_10` and `test_a_precondition_with_a_reason_is_skip_10_and_printed_as_skipped`, both passing. |
| 2 | One real row 1 run is filed in a new dated folder under `tests/evidence/` with the committed file set plus the five new files, every provenance field non-empty, every file leak-gated (HARN-05, EVID-04) | VERIFIED | 65 files in the folder. Every committed file is present except the two `auto-memory` snapshot files, which the model did not write in this run; 28 files only in the rerun. Provenance files and `usage.txt` are non-empty. I ran the leak gate over the folder: 65 files, 0 findings. A grep of the folder for home paths, hostnames, private addresses and the owner's email found nothing. |
| 3 | The init manifest is asserted, the isolation mode is recorded as spike S1 decided, and the write-boundary and git-read-only checks report zero on the real run and fail on a seeded out-of-root write (HARN-07, HARN-09) | FAILED (partial) | Twelve init assertions per stage are `yes` for s1, s2 and s3. `isolation-mode.txt` says strict, matching the S1 finding. Zero writes outside the roots and zero git mutations are reported, and the seeded fixtures (snapshot path, Write-tool path, commit) end with exit 11. The failing part is soundness: the Bash route and the planted fsmonitor route are not covered. See gaps 1. |
| 4 | The row README ends with `Reviewer verdict: PENDING` and a mechanical checklist, and no filed harness file carries an accepted, passed or failed verdict (EVID-05) | VERIFIED | The last line of the row README is `Reviewer verdict: PENDING`. A whole-word search of the folder for accepted, passed, failed, pass and fail outside traces and snapshots found nothing; the only match for verdict is that line. |
| 5 | The read-only comparer prints per-row differences against the committed row 1 and leaves both trees byte-identical; the frozen trees are unchanged; `SKILL.md` is at most 12,000 bytes; all new code is under `tests/harness/` (EVID-06, HARN-13) | VERIFIED | I ran the comparer: exit 0, tree digests before and after identical for both trees, `old unchanged: yes`, `new unchanged: yes`. `git diff` from the phase base to HEAD shows no change to `SKILL.md`, `references/` or `tests/fixtures/`, and no modified or deleted file under `tests/evidence/`. `SKILL.md` is 11,994 bytes. Outside `.planning/` the only paths changed are under `tests/harness/` and the new evidence folder. |
| 6 | A run the live path refused cannot be filed as a baseline by `--refile` (derived: filed evidence is the record of a clean run) | FAILED | `_unfileable` in `tests/harness/pc_evidence.py` is unchanged and never reads the stage evaluation. See gap 2. |

**Score:** 4/6 truths verified (0 present, behavior-unverified)

### Decisions Honored

The context decisions that are observable in the filed run hold.

- **D-01 and D-02:** s1 and s2 share one session id and s3 is a new session. `session.id`, `session-resume.id` and `usage.txt` agree.
- **D-05 and D-06:** the folder is `rerun-2026-10-29-claude-sonnet-5-5` and its README labels the run a new baseline, not a replication.
- **D-08:** the comparer exited 0 and printed no verdict.
- **D-12 and D-13:** model claude-sonnet-5-5 in every stage, Claude Code 2.1.310 in every stage.
- **D-14:** the dry run prints caps of 0.30, 1.30 and 0.40 USD and 15, 60 and 15 turns.

### Measured Cost

The row total in `usage.txt` is 0.2723 USD. I recomputed it: s2 reported total 0.2071 plus s3 total 0.0652. The s2 call cost 0.1584 equals 0.2071 minus the s1 total 0.0487. The cumulative reading is supported by the committed 2.1.310 fixtures and the pinned test `test_the_delta_agrees_with_the_difference_of_the_two_cumulative_totals`, and by the review's finding that the per-call and per-model blocks of the real s2 result agree with it. The filed folder cannot show this by itself, which is the IN-01 part of gap 3. I accept 0.2723 USD as the measured figure.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/harness/pc_matrix.py` | Driver: list, plan, run, refile, authorize-retry | VERIFIED | Runs, exits as specified, wired to `pc_row1`, `pc_evidence`, `pc_spend`, `pc_preflight`. |
| `tests/harness/pc_spend.py` | File-locked matrix ledger with delta cost | VERIFIED | Thread race tests pass; the review confirms read, check and append under one lock. |
| `tests/harness/pc_row1.py` | Seed, three-stage chain, init and instruction audit | VERIFIED | Produced the real run. |
| `tests/harness/pc_checks.py` | Mechanical facts and breaches | PARTIAL | Substantive and wired, but the breach rule is unsound for Bash writes (gap 1). |
| `tests/harness/pc_evidence.py` | Filing, SKIPPED, refile, checklist | PARTIAL | Wired and used by the real run; refile accepts unclean runs (gap 2). |
| `tests/harness/pc_compare.py` | Read-only comparer with tree digests | VERIFIED | Ran it; digests unchanged. |
| `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` | New baseline folder | VERIFIED | See truth 2. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pc_matrix.py` real path | `pc_row1.run_row` then `pc_evidence.file_row` | run, checks, filing | WIRED | The real run produced the folder through this path. |
| `pc_row1.finish` | `pc_checks.breaches` | exit 11 on breach | WIRED, rule incomplete | Exit 11 is mapped; the rule does not cover Bash writes outside the run root. |
| `pc_evidence.file_row` | `pc_sanitize`, `pc_leakgate`, `pc_promote` with deny entries | filing through the gate | WIRED | Every caller passes the deny entries; the API does not insist (WR-03). |
| `pc_matrix --refile` | `pc_evidence.file_row` | same filing function | WIRED, guard missing | Gap 2. |
| `pc_compare.py` | both evidence trees | read only | WIRED | Tree digests identical before and after. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
| -------- | ---- | ------ | --------- | ------ |
| `usage.txt` | per-stage cost and tokens | result events of the real streams | Yes | FLOWING |
| `mechanical-checks.md` | init manifest, counts, ids | real streams, snapshots, wrapper log | Yes | FLOWING |
| `digests.txt` | skill and adapter digests | files on disk at run time | Yes, and the SKILL.md and references digests equal the digests of the repository files | FLOWING |

### Behavioral Spot-Checks

All run with a tripwire `claude` first on PATH. It was never invoked.

| Behavior | Command shape | Result | Status |
| -------- | ------------- | ------ | ------ |
| `--list` prints 3 layouts then 18 rows | driver `--list` | exit 0, one implemented row | PASS |
| Unknown or unimplemented ids | `--row row3`, `--row nope`, `--layout nope`, upper-case id, `--row row2-double-conflict`, bare `--row` | exit 2 each, fixed text, value never echoed | PASS |
| Dry run prints plan | `--dry-run --row row1-wrong-binding` | prints 3 stages, 2 sessions, caps, worst case 2.00, 40 allowlist rules; exits 17 today (see Warnings) | PASS with note |
| Comparer is read-only | comparer over committed and rerun trees | exit 0, digests identical before and after | PASS |
| Leak gate over the folder | `pc_leakgate.py scan` | 65 files, 0 findings | PASS |
| Zero-token suite | `tests/harness/selftest` | 1117 tests OK, 3 skipped, about 213 s | PASS |
| Plain discovery | `python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | 1117 tests OK, 4 skipped, about 249 s | PASS |

The skips are environmental: shellcheck absent, a case-insensitive and normalizing filesystem, and a filesystem that refuses non-UTF-8 names. The working tree was unchanged after every check.

### Probe Execution

No probe scripts are declared by the plans. Step 7c: SKIPPED (none declared).

### Requirements Coverage

All nine phase IDs appear in plan frontmatter, and REQUIREMENTS.md maps exactly these nine to Phase 3, so none is orphaned.

| Requirement | Source plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| HARN-01 | 03-01 | One command with list, row, layout, all, dry-run | SATISFIED | Spot-checks above. |
| HARN-02 | 03-01 | SKIP, FAIL and BLOCKED distinct, skipped never a pass | SATISFIED | Codes 10, 11, 12; SKIPPED label tests pass. |
| HARN-05 | 03-02, 03-04, 03-06 | Provenance recorded per run | SATISFIED | Truth 2. Cumulative flag not in the filed file (gap 3). |
| HARN-07 | 03-02, 03-06 | Init manifest asserted every run, isolation mode recorded | SATISFIED | Twelve assertions per stage, strict recorded. |
| HARN-09 | 03-03, 03-06 | Mechanical write-boundary and git-read-only assertions | BLOCKED | Gap 1. REQUIREMENTS.md marks it Complete; I recommend it be reopened until gap closure lands. |
| HARN-13 | 03-05, 03-06 | New work under `tests/harness/`, skill frozen, size cap | SATISFIED | Truth 5. |
| EVID-04 | 03-04, 03-06 | Per-row file set written exclusively into a new dated folder | SATISFIED | Truth 2. Refile hole (gap 2) and misleading status fact (gap 3) noted. |
| EVID-05 | 03-04, 03-06 | No verdict printed, PENDING plus checklist | SATISFIED | Truth 4. |
| EVID-06 | 03-05, 03-06 | Read-only structural comparer | SATISFIED | Truth 5. |

### Anti-Patterns Found

I did not re-run a stub scan over every harness file. The code review (28 files, standard depth) is the evidence for code quality, and I read the cited lines for the three critical findings. No debt marker check was run beyond that; none is cited by the review.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `tests/harness/pc_checks.py` | 283-311, 834-849 | Bash write mentions never feed `breaches()` | BLOCKER | CR-02, gap 1 |
| `tests/harness/pc_manifest.py` | 74-105 | git status without fsmonitor disabled | BLOCKER | CR-03, gap 1 |
| `tests/harness/pc_evidence.py` | 1017-1025 | `_unfileable` ignores stage evaluation | BLOCKER | CR-01, gap 2 |
| `tests/harness/pc_checks.py` | 725 | Check can never be yes on a real run | WARNING | WR-02, gap 3 |

### Review Findings Not Routed to Gap Closure

The disposition defers WR-01, WR-04, WR-05, WR-06 and IN-02 to IN-10 to Phase 4 hardening. Phase 4's roadmap section names no hardening work, so I did not move any of them into `deferred:`. They stay non-blocking warnings for this verdict. WR-01 (three run-root places invisible to the snapshot) and WR-05 (two inputs fail open to no breach) sit on the same boundary as CR-02, so bundling them into the gap-closure plan is cheap. That is bokiko's call.

### Warnings

- **Dry run exits 17 on the day the baseline was filed.** The dry run runs the claude-free gate, and the dated destination now exists, so `--dry-run --row row1-wrong-binding` prints the plan and then exits 17 on 2026-10-29. This follows decision D-05 (a destination is never reused) and clears on any other date. Criterion 1's exit 0 holds when the destination is free, which the tests cover.
- **Six permission denials in s2.** All six are Bash approval refusals of compound or variable-expansion forms, with the same shape as the committed baseline's seven. They are filed as facts with their ids and need no action from the harness.
- **Leftover sentence in the 03-06 summary.** Unobserved question 2 still says the cumulative question is not settled by the filed data, which contradicts the resolved paragraph above it (part of gap 3).

### Regression Check

| Earlier phase | Result |
| ------------- | ------ |
| Phase 1 (publication gate) | No change to any file outside `.planning/`, `tests/harness/` and the new evidence folder since the phase base, so the Phase 1 files are untouched. |
| Phase 2 (model-free foundation and stub) | The full suite, which includes all Phase 2 test modules (stub conformance, sanitizer, leak gate, run root, manifest, flags, stream, measure), passes with 1117 tests. Phase 3 edited the stub, the allowlist module, the branch table and the harness README, so the Phase 2 covered digest no longer matches. That is expected. |

### Human Verification Required

None. Every item I checked is decidable from files and zero-token commands.

## Gaps Summary

Three gaps, all already named by the code review and routed by its disposition to a gap-closure plan before the phase closes.

1. **Write boundary and git safety (BLOCKER, CR-02 and CR-03).** The HARN-09 checks have a Bash blind spot and a command-execution hole through `.git/config`. Plan 03-03 chose that Bash mentions never decide a breach, so this is a design gap that the executor implemented faithfully, not a deviation. Fix the rule and add the two tests named in the gap.
2. **Refile bypass (BLOCKER, CR-01).** One check in `file_row` closes it.
3. **Evidence accuracy (WARNING, WR-02, WR-03, IN-01).** A misleading fact in the baseline, a cost-consistency flag missing from the filed file, and a deny-entries contract held by convention.

Gap closure that changes the harness will change the code that produced the committed baseline. The folder was filed from head `baf8aa5` and the 03-06 commit changed no harness code, so the baseline remains a valid record of that run. Whether `status-begins-with-session: no` in it needs a note or a refile is a decision for bokiko.

---

_Verified: 2026-10-29T09:20:00Z_
_Verifier: Claude (gsd-verifier)_
