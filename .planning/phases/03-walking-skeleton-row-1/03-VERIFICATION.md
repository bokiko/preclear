---
phase: 03-walking-skeleton-row-1
verified: 2026-10-29T21:45:00Z
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
  - "tests/harness/README.md"
  - "tests/harness/checkpoint_stub.py"
  - "tests/harness/pc_allowlist.py"
  - "tests/harness/pc_checks.py"
  - "tests/harness/pc_compare.py"
  - "tests/harness/pc_evidence.py"
  - "tests/harness/pc_manifest.py"
  - "tests/harness/pc_matrix.py"
  - "tests/harness/pc_preflight.py"
  - "tests/harness/pc_promote.py"
  - "tests/harness/pc_row1.py"
  - "tests/harness/pc_rows.py"
  - "tests/harness/pc_spend.py"
  - "tests/harness/pc_testutil.py"
  - "tests/harness/test_checks.py"
  - "tests/harness/test_evidence.py"
  - "tests/harness/test_row1_assertions.py"
  - "tests/harness/test_stages.py"
covered_digest: "v3:sha256:a8c538a6f9fb70761de6d91024a9b7d7c9a5d6d9830b766cbcd1437c2c15fb2b"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/6
  gaps_closed:
    - "Write-boundary and git-read-only checks are mechanical and sound (HARN-09)"
    - "A run the live path refused cannot be filed by the zero-token refile"
    - "Filed mechanical facts are accurate and complete enough to read without being misled (code closed; the frozen folder keeps its earlier answers)"
  gaps_remaining: []
  regressions: []
---

# Phase 3: Walking Skeleton (Row 1) Verification Report

**Phase Goal:** One row, row 1 (wrong binding), runs end to end through the real `claude -p` against the stub from a single command, is filed as sanitized evidence in a new dated folder with mechanical facts only, and lines up structurally with the committed row 1 evidence.
**Verified:** 2026-10-29T21:45:00Z
**Status:** passed
**Re-verification:** Yes, after gap closure (plans 03-07 to 03-12). Previous status gaps_found, 4/6.

## Verdict

The phase goal is achieved. All three earlier gaps are closed in the code, and I reproduced each fix myself instead of reading the summaries. Six of six truths verify.

**HARN-09 is now met.** The write-boundary check counts a write-capable Bash command that names a place outside the approved roots as a breach. The git state reads run with fsmonitor and the untracked cache forced off, and run no git command at all once the project's git folder differs from the setup pin. The real run is clean under the current rule. The seeded fixtures still end with exit 11. I recommend moving REQUIREMENTS.md from "In Progress (reopened)" to Complete.

The check is a conservative classifier over command text, not a sandbox. Its remaining limits are named in the harness README, and the pinned allowlist and the snapshot diff back it. The deferred review warnings are Phase 4 hardening and do not block this phase. They are listed under Warnings.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria. Truth 6 is derived from the goal. No plan truth reduced their scope.

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | `--list`, `--dry-run`, unknown ids and the three preflight codes behave as specified; a SKIPPED row files under a SKIPPED label (HARN-01, HARN-02) | VERIFIED | `--list` prints 3 layouts and the rows with one implemented. `--row nope`, `--layout nope`, `--row row3`, an upper-case id and a bare `--row` each exit 2. With the clock set to a free date the dry run prints 3 stages, 2 sessions, caps 0.30, 1.30 and 0.40, and exits 0 with no `claude` on PATH. The SKIPPED label tests pass in the suite. See the dry-run warning for today's date. |
| 2 | One real row 1 run is filed in a new dated folder under `tests/evidence/` with the committed file set plus the five new files, every provenance field non-empty, every file leak-gated (HARN-05, EVID-04) | VERIFIED | 65 files in `rerun-2026-10-29-claude-sonnet-5-5`, unchanged since commit 6637669. Claude Code 2.1.310, model claude-sonnet-5-5, strict isolation, digests, tools and usage with per-stage cost are all present. The leak gate scan ran over the folder: 65 files, 0 findings. A grep for home paths, the owner's email, private addresses and local hostnames found nothing. The only committed file absent is the auto-memory snapshot pair, which the model did not write in this run. |
| 3 | The init manifest is asserted, the isolation mode is recorded as spike S1 decided, and the write-boundary and git-read-only checks report zero on the real run and fail on a seeded out-of-root write (HARN-07, HARN-09) | VERIFIED | Twelve init assertions per stage are yes in the filed mechanical checks. `isolation-mode.txt` says strict. The filed facts show zero outside snapshot paths, zero Write-tool paths, zero git mutations over 4 states. I re-judged every Bash command in the three filed traces with today's rule: 0 write escapes, 0 git mutations. Seeded fixtures and run-level tests for a snapshot path, a Write-tool path, a Bash write, a planted fsmonitor command and a planted clean filter all pass in the suite. See the HARN-09 section. |
| 4 | The row README ends with `Reviewer verdict: PENDING` and a mechanical checklist, and no filed harness file carries an accepted, passed or failed verdict (EVID-05) | VERIFIED | The last line of the row README is `Reviewer verdict: PENDING`. A whole-word search of every harness-authored file for accepted, passed, failed, pass, fail and verdict matched only that line. The comparer output carries no verdict word either. |
| 5 | The read-only comparer prints per-row differences against the committed row 1 and leaves both trees byte-identical; the frozen trees are unchanged; `SKILL.md` is at most 12,000 bytes; all new code is under `tests/harness/` (EVID-06, HARN-13) | VERIFIED | The comparer exits 0 and prints tree digests before and after for both trees, `old unchanged: yes` and `new unchanged: yes`. A diff from the phase base (0a97367) to HEAD shows no change to `SKILL.md`, `references/` or `tests/fixtures/`, and no modified or deleted file under `tests/evidence/`; the only additions there are the 65 new files. Outside `.planning/` every changed path is under `tests/harness/`. `SKILL.md` is 11,994 bytes. |
| 6 | A run the live path refused cannot be filed as a baseline by `--refile` (derived: filed evidence is the record of a clean run) | VERIFIED | `_unfileable` in `tests/harness/pc_evidence.py` now refuses any stage record whose problem is not empty or whose evaluation is not the pass value, then requires the chain the registry defines. `file_row` also refuses a context without deny entries. The tests for a chain stopped at s2 by an error subtype, a failed isolation assertion and the controls that still refile pass in the suite. |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### HARN-09: is it met now

Yes. The three holes from the first report are closed, each reproduced against the current code.

- **Bash write outside the roots (was gap 1, CR-02).** `breaches()` now adds the write-escape count to the writes total. I fed 52 commands through the checker in two batches, with the roots set to a fake run root. Every write-capable form counted as an escape, and three git mutations counted under the git rule instead: mkdir, tee, cp, mv, dd, install, ln, rm, sed -i, curl -o, rsync, tar -C, unzip -d, a redirect, a tilde path, a home-variable path, a dot-dot path, `bash -c`, `sh -c`, `eval`, xargs, `find -fprint`, `exec 3>`, awk output, perl, node, sort -o, `cd /tmp; touch`, and a pipe into tee. Read-only forms (a listing, a read of a system file, a write inside the project) counted zero. One write form was not counted, `X=/tmp/elsewhere; touch $X/y`, which is the documented limit for expansions other than the home variable.
- **Planted git configuration (was gap 1, CR-03).** I planted a `core.fsmonitor` command in a throwaway repository. A plain `git status` created its marker, so the probe can see what it guards. `git_state` and `capture_git_status` never created it. With the setup pin, the harness started no git process at all and returned the fixed not-read state.
- **Refile of a refused run (was gap 2, CR-01).** Closed, see truth 6.

The filed baseline was produced by the earlier, weaker rule. Its facts still hold under the current rule, as the re-judge in truth 3 shows.

### Gap Closure Check

| Earlier gap | Status | Evidence |
| ----------- | ------ | -------- |
| 1. Bash write blind spot and fsmonitor route (BLOCKER) | CLOSED | Plans 03-07, 03-10, 03-11, 03-12. Reproduced as above. |
| 2. Refile files a refused run (BLOCKER) | CLOSED | Plans 03-08 and 03-09. Stage cleanliness and chain completeness are checked before filing. |
| 3. Misleading fact, cost flag, deny entries (WARNING) | CLOSED in code, one residue in the frozen folder | The session-line fact now scans the first five lines for a line starting with `session `. The usage rendering now writes a `cumulative-consistent` line per stage. `file_row` refuses a missing deny list. The 03-06 summary sentence now says the cumulative question was settled by the review. The frozen folder keeps the old answer, which the harness README states. |

All five review passes are closed on criticals: every critical in passes one to four is marked fixed with its proving commit, and the closing pass found none.

### Measured Cost

The row total in the filed usage file is 0.2723 USD. The sum of the three per-call costs (0.0487, 0.1584, 0.0652) matches it, and the s2 call cost equals the s2 cumulative total 0.2071 minus the s1 total. The cumulative reading rests on the first code review and the committed 2.1.310 fixtures, both with a passing named test. The filed `usage.txt` itself does not carry the consistency flag, because the folder was filed before the rendering fix and is frozen. I accept 0.2723 USD as the measured figure.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/harness/pc_matrix.py` | Driver: list, plan, run, refile, authorize-retry | VERIFIED | Ran list, dry run and the refusal ids. Wired to row, evidence, spend and preflight modules. |
| `tests/harness/pc_spend.py` | File-locked matrix ledger with delta cost | VERIFIED | Spend tests pass. |
| `tests/harness/pc_row1.py` | Seed, three-stage chain, init and instruction audit | VERIFIED | Produced the real run. |
| `tests/harness/pc_checks.py` | Mechanical facts and breaches | VERIFIED | Open-world write rule, wired into `breaches()`, git reads hardened. |
| `tests/harness/pc_manifest.py` | Hardened git status, pin guard | VERIFIED | Hardening tuple used by both capture paths; raises on a changed git folder before any process starts. |
| `tests/harness/pc_evidence.py` | Filing, SKIPPED, refile, checklist | VERIFIED | Clean-stage, chain and deny-entry refusals in place. |
| `tests/harness/pc_compare.py` | Read-only comparer with tree digests | VERIFIED | Ran it; digests identical before and after. |
| `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/` | New baseline folder | VERIFIED | See truth 2. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pc_matrix.py` real path | `pc_row1.run_row` then `pc_evidence.file_row` | run, checks, filing | WIRED | The real run produced the folder through this path. |
| `pc_row1.finish` | `pc_checks.breaches` | exit 11 on breach | WIRED | `breaches()` sums snapshot, trace, Bash escape and default-memory writes, git mutations and run-record changes. |
| `pc_checks.git_state`, `pc_manifest.capture_git_status` | git | `GIT_HARDENING` plus pin and nested-repository guard | WIRED | Marker file never created in my probe. |
| `pc_evidence.file_row` | sanitizer, leak gate, promote with deny entries | filing through the gate | WIRED | The API now refuses a missing deny list. |
| `pc_matrix --refile` | `pc_evidence.file_row` | same filing function | WIRED | Same refusals as the live path. |
| `pc_compare.py` | both evidence trees | read only | WIRED | Digests identical before and after. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
| -------- | ---- | ------ | --------- | ------ |
| `usage.txt` | per-stage cost and tokens | result events of the real streams | Yes | FLOWING |
| `mechanical-checks.md` | init manifest, counts, ids | real streams, snapshots, wrapper log | Yes | FLOWING |
| `digests.txt` | skill and adapter digests | files on disk at run time | Yes | FLOWING |

### Behavioral Spot-Checks

All run with no `claude` on PATH. A tripwire `claude` that logs any call was never invoked.

| Behavior | Command shape | Result | Status |
| -------- | ------------- | ------ | ------ |
| List | driver `--list` | exit 0, one implemented row | PASS |
| Unknown ids | `--row nope`, `--layout nope`, `--row row3`, upper-case id, bare `--row` | exit 2 each | PASS |
| Dry run on a free date | driver main with the clock set to 2031-01-02 | prints the plan, gate ok, exit 0 | PASS |
| Dry run today | `--dry-run --row row1-wrong-binding` and `--dry-run --all` | plan printed, then exit 17 because today's folder exists | PASS with warning |
| Comparer read-only | comparer over committed and rerun trees | exit 0, digests identical before and after | PASS |
| Leak gate | scan of the rerun folder | 65 files, 0 findings | PASS |
| Bash write rule | 52 hostile commands, then 11 real traced commands | every write form counted except one variable-expansion form (documented limit); 0 escapes and 0 git mutations on the real ones | PASS |
| Planted fsmonitor | throwaway repository with a planted command | control creates the marker; harness never does | PASS |
| Zero-token suite | `tests/harness/selftest` | 1305 tests, OK, 3 skipped, header says 0 model calls, 426 s | PASS |
| Plain discovery | `python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | 1305 tests, OK, 4 skipped, 484 s | PASS |

The skips are environmental: shellcheck absent, and filesystem behaviours this machine lacks. The working tree was unchanged after every check.

### Probe Execution

No probe scripts are declared by the plans. Step 7c: SKIPPED (none declared).

### Requirements Coverage

All nine phase IDs appear in plan frontmatter across plans 03-01 to 03-12. REQUIREMENTS.md maps exactly these nine to Phase 3, so none is orphaned.

| Requirement | Source plans | Description | Status | Evidence |
| ----------- | ------------ | ----------- | ------ | -------- |
| HARN-01 | 03-01 | One command with list, row, layout, all, dry-run | SATISFIED | Spot-checks. Dry run exits 17 today only because the dated folder exists. |
| HARN-02 | 03-01 | SKIP, FAIL and BLOCKED distinct, skipped never a pass | SATISFIED | Codes 10, 11, 12; SKIPPED label tests pass. |
| HARN-05 | 03-02, 03-04, 03-06, 03-08, 03-09 | Provenance recorded per run | SATISFIED | Truth 2. |
| HARN-07 | 03-02, 03-06 | Init manifest asserted every run, isolation mode recorded | SATISFIED | Twelve assertions per stage, strict recorded. |
| HARN-09 | 03-03, 03-06, 03-07, 03-08, 03-09, 03-10, 03-11, 03-12 | Mechanical write-boundary and git-read-only assertions | SATISFIED | See the HARN-09 section. Reopen status can be cleared. |
| HARN-13 | 03-05, 03-06 | New work under `tests/harness/`, skill frozen, size cap | SATISFIED | Truth 5. |
| EVID-04 | 03-04, 03-06, 03-08, 03-09 | Per-row file set written exclusively into a new dated folder | SATISFIED | Truth 2 and truth 6. |
| EVID-05 | 03-04, 03-06 | No verdict printed, PENDING plus checklist | SATISFIED | Truth 4. |
| EVID-06 | 03-05, 03-06 | Read-only structural comparer | SATISFIED | Truth 5. |

### Anti-Patterns Found

A search of `tests/harness` for TBD, FIXME and XXX matched only mktemp templates and a mktemp call in the selftest, none a debt marker. TODO, HACK and PLACEHOLDER matched one constant named for a ledger placeholder in the seed. No stub or empty implementation was found in the files I read, and the suite exercises the rest.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| none | - | - | - | No blocker found |

### Warnings

These do not change the status. None is mapped to a later roadmap phase, because Phase 4's roadmap section names no hardening work, so I did not move any of them into `deferred`.

- **Dry run exits 17 today.** On 2026-10-29 `--dry-run` for row 1 and for `--all` print the plan and then exit 17, because decision D-05 says a dated destination is never reused and today's folder exists. Roadmap criterion 1 says the dry run exits 0. That holds on any date without a folder, which the tests pin with a fixed clock and I confirmed with a clock set to 2031-01-02. A stranger who tries it today sees 17.
- **Deferred review warnings.** The closing review lists six: a literal `cd` joined by a semicolon, in a subshell or in a loop before a legitimate memory write ends the row with exit 11 (false positive); a `cd` to an expansion followed by a dot-dot write is no longer counted; an awk regular expression holding a semicolon or brace hides a redirect; five or more option letters before a slash value hide the value; a `cd` judged certain can still fail; a folder kept by a `cd` in one Bash call is not carried to the next. Earlier passes defer more warnings and info items. The three accepted residuals are a script file written earlier and run later, interpreter code that builds its path at run time, and leading assignment values. My own probe found the same limit for `X=/tmp/elsewhere; touch $X/y`, which the README states. These are Phase 4 items.
- **Frozen baseline keeps the earlier answers.** `status-begins-with-session` is no in the filed folder, and its `usage.txt` has no consistency line. The harness README states the first. Neither is a harness fault, and both would differ on a fresh run.

### Human Verification Required

None. Every item I checked is decidable from files and zero-token commands. The row's own Reviewer verdict stays PENDING by design and belongs to the later reviewer, not to this verification.

## Gaps Summary

No gaps. The earlier gaps are closed and HARN-09 is met. The phase is ready to close once REQUIREMENTS.md is updated and the Phase 4 hardening list is carried forward.

---

_Verified: 2026-10-29T21:45:00Z_
_Verifier: Claude (gsd-verifier)_
