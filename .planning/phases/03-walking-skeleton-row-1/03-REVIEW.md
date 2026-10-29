---
phase: 03-walking-skeleton-row-1
reviewed: 2026-10-29T09:08:44Z
depth: standard
files_reviewed: 28
files_reviewed_list:
  - tests/harness/checkpoint_stub.py
  - tests/harness/pc_allowlist.py
  - tests/harness/pc_checks.py
  - tests/harness/pc_compare.py
  - tests/harness/pc_evidence.py
  - tests/harness/pc_matrix.py
  - tests/harness/pc_preflight.py
  - tests/harness/pc_row1.py
  - tests/harness/pc_rows.py
  - tests/harness/pc_spend.py
  - tests/harness/pc_testutil.py
  - tests/harness/test_allowlist.py
  - tests/harness/test_checks.py
  - tests/harness/test_compare.py
  - tests/harness/test_evidence.py
  - tests/harness/test_frozen_tree.py
  - tests/harness/test_matrix_cli.py
  - tests/harness/test_matrix_preflight.py
  - tests/harness/test_preflight.py
  - tests/harness/test_row1_assertions.py
  - tests/harness/test_row1_seed.py
  - tests/harness/test_spend.py
  - tests/harness/test_stages.py
  - tests/harness/test_stub_cli.py
  - tests/harness/data/branch-table.md
  - tests/harness/data/row1-plan.md
  - tests/harness/data/row1-s1-prompt.md
  - tests/harness/README.md
findings:
  critical: 3
  warning: 6
  info: 10
  total: 19
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-29T09:08:44Z
**Depth:** standard (diff against db05d74, plus cross-file tracing of the call chains the lead named)
**Files Reviewed:** 28
**Status:** issues_found

## Summary

The row 1 pipeline is carefully built. The spend ledger is correct and race-safe, the destination gate runs before any money is spent, the sanitizer and deny entries are built before the first paid call, and the comparer is read-only. The project constraints hold. Python 3.9 syntax parses cleanly, imports are standard library only, no deletion primitive appears outside the test utilities, and no home path, host, IP or email is committed in the reviewed files or in the filed rerun folder.

Three defects are serious enough to fix before Phase 4 spends against this code. All three were reproduced with the scripted fake claude (zero tokens, no real `claude` started):

1. `--refile` files a run that the live path had just refused (CR-01).
2. A write-capable Bash command aimed at a path outside the run root is listed but never counted as a breach, so the run files with exit 0 (CR-02).
3. The harness's own `git status` executes a repo-local `core.fsmonitor` command that the model can plant, and it does so before the breach check can see the planted file (CR-03).

**The cumulative-cost question from the 03-06 summary is settled by data already on disk.** `total_cost_usd` on a resumed call is cumulative. The committed first-call and resumed-call fixtures show 0.0577 plus the resumed call's own 0.0026 equals the resumed total 0.0603 exactly. The real s2 result agrees. Its per-model cumulative block holds 28 input and 6486 output tokens, which are s1 plus s2 (6+22 and 854+5632). Its per-call block holds only s2's own 22 and 5632, and the per-call cost 0.15843 is what the harness subtracted. The harness row total of 0.2723 USD is therefore correct, and the alternative 0.3210 is refuted. The token-ratio inference in the summary fails because the result's `usage` field is per call, not cumulative. See IN-01.

The test suite passes for the modules I ran (spend 36, checks 57, compare 54). The working tree is unchanged by this review.

## Phase 2 deferred items (21): what Phase 3 did

| ID | Status | Evidence |
|---|---|---|
| WR-03 stub end marker | **Fixed** | `checkpoint_stub.py:692` refuses a body line equal to the end marker or matching a begin marker, after the stale-hash check and before any write. Split and parse both use `split("\n")`, so the check and the parser agree. Branch table row added. |
| WR-12 sanitizer after the paid call | **Fixed for the matrix path** | `pc_row1.py:1095-1099` builds the sanitizer and deny entries before the ledger launch and maps both error types to exit 15. `pc_spike.main` is unchanged, so the spike driver is still open. |
| WR-14 deny entries to promote | **Fixed in every caller, root cause open** | `pc_evidence.py:1192`, `pc_matrix.py:549` and `pc_matrix.py:620` pass `deny_entries`. `promote` still falls back to the weaker default when given None (`pc_promote.py:171`). See WR-03 below. |
| WR-05 existence check before paid output | **Fixed for the matrix path** | `pc_row1.py:1089` and `pc_matrix.py:363` check the destination before any spend. `pc_spike.run_s1` is unchanged. |
| WR-06 check-then-act spend guard | **Fixed for the matrix ledger** | `pc_spend.py` reads, checks and appends under one `flock`. Thread race tests pass. The spike ledger in `pc_spike.py` is unchanged and still open. |
| WR-09 vacuous user-names assertion | **Open, now load-bearing** | See WR-06 below. |
| WR-10 `%q` log parsing | **Open, mitigated** | `pc_checks.helper_calls` catches `MineError` and records UNCONFIRMED. |
| WR-04 stub deletes and overwrites | Open | `checkpoint_stub.py` still calls `os.unlink` and `os.replace`. |
| WR-07 `pc_spike.main` error mapping | Open | `pc_spike.py` unchanged. |
| WR-08 `run_s2a` half-written pair | Open | `pc_spike.py` unchanged. |
| WR-11 manifest CLI credential refusal | Open | `pc_manifest.py` unchanged. `take_snapshot` takes a `refuse_under` argument but no caller passes one. Not reachable today because a run root is always a new folder under the runs root. |
| WR-13 gate substring vs sanitizer whole word | Open | `pc_leakgate.py` and `pc_sanitize.py` unchanged. |
| IN-01 reader validates less than writer | Fixed for the new ledger only | The new ledger is strict. The spike ledger is unchanged. |
| IN-02, IN-03, IN-04, IN-05, IN-06, IN-08, IN-09, IN-10 | Open | The files that hold them are unchanged. IN-05 recurs in a new place, see IN-04 below. |

Of the 21, one is closed outright, four are closed for the matrix path only, and sixteen remain open. That matches the Phase 3 context, which deferred all but WR-03, WR-12 and WR-14.

## Critical Issues

### CR-01: `--refile` files a run that the live path refused

**File:** `tests/harness/pc_evidence.py:1017-1025`, `tests/harness/pc_matrix.py:559-644`
**Issue:** The live chain stops at the first stage that did not finish cleanly or whose isolation assertions failed, and prints "nothing was filed". `--refile` skips that decision. `_usable_run_folder` accepts any folder with a `run.json` for row 1, and `file_row` only calls `_unfileable`, which checks that each stage has a prompt and a parseable stream. It never reads the stage record's `problem` or `evaluation` fields.

Reproduced with the scripted claude. When s2 ended with `error_max_turns`, the live run exited 11 and filed nothing. A `--refile` of that run root then exited 0 and filed 53 files into a new `rerun-...` folder, with `usage.txt` listing the failed subtype. The destination name is then consumed for good (no deletion primitive exists), and the folder reads as a baseline. The README describes `--refile` as being "for a finished run folder, after a refusal that came late", but nothing marks a folder as finished. A person whose retry is blocked by the one-attempt ledger will reach for `--refile`.
**Fix:** Make `file_row` refuse a run whose stage records are not clean, using the same rule the live path uses.
```python
def _unfileable(data: RunData) -> Optional[str]:
    if not data.stages:
        return MESSAGE_UNREADABLE
    for stage in data.stages:
        if stage.prompt is None:
            return MESSAGE_NO_PROMPT
        if stage.events is None:
            return MESSAGE_NO_STREAM
        if stage.record.get("problem") != "" or stage.record.get("evaluation") != "pass":
            return MESSAGE_STAGE_NOT_CLEAN   # fixed text: "FAIL: a stage did not finish cleanly; nothing is filed"
    return None
```
Add a test that stops a chain at s2 (non-success subtype, then a failed isolation assertion) and asserts `--refile` exits 11 with nothing created.

### CR-02: A write-capable Bash command aimed outside the run root is never a breach

**File:** `tests/harness/pc_checks.py:283-311`, `tests/harness/pc_checks.py:834-849`, `tests/harness/test_checks.py:600-606`
**Issue:** The write boundary has two nets. The snapshot diff only sees the run root (and CR-02 is about what it cannot see). The Write and Edit trace only sees those two tools. A Bash command is only listed by `bash_mentions` and, by design, never feeds `breaches()`. The comment at `pc_checks.py:291` says "a real write by any program still shows in the snapshot diff", which is false for any path outside the run root.

The committed allowlist (`tools.txt`) allows `mkdir`, `python3 -c`, `awk`, `sed -n`, `find`, `env` and `cd`, so an executed `mkdir <outside path>` is reachable. Reproduced: a scripted s2 that executed `mkdir` on an outside folder and really wrote a file there finished with exit 0 and filed 67 files. The only trace is two lines in `mechanical-checks.md`: `bash-outside-path-tokens: 1` and `bash-write-programs: mkdir=1`. That contradicts D-03 ("nothing can leave the scratch project") and the HARN-09 contract that a write outside the approved roots is exit 11.

The listing is also weaker than it looks. `bash_mentions` counts only words that start with `/`, so `~/x`, `$HOME/x` and `../../x` are not counted at all.
**Fix:** Treat the conjunction as a breach: an executed part that `_write_program` labels and that names a path outside the approved roots, a `~` or `$` expansion, or a `..` segment. Keep read-only mentions as facts.
```python
# in bash_mentions, per part:
label = _write_program(words)
escaping = any(_escapes(word, roots) for word in words[1:])   # "/" outside roots, "~", "$HOME", "..", etc.
if label is not None and escaping:
    escapes += 1
# return it as "write_escapes", and in breaches():
writes += int(facts["bash_mentions"]["write_escapes"])
```
Update the `MentionTests` case at `test_checks.py:600` so a read-only `ls` stays a mention and a `mkdir` of the same path is exit 11.

### CR-03: The harness's `git status` runs a command the model can plant in `.git/config`

**File:** `tests/harness/pc_manifest.py:74-105` (called from `tests/harness/pc_checks.py:378` and `tests/harness/pc_row1.py:409`)
**Issue:** After every stage the harness runs `git status` inside the model's project. The git environment overrides remove the user and system config but not the repository's own `.git/config`. `Write` and `Edit` are in the allowlist and the project is an approved root, so the model can write `.git/config`. A `core.fsmonitor` value is then executed as a shell command by the harness, as the harness user, outside the model's permission layer.

Reproduced: a repo whose config carried a `core.fsmonitor` command created a marker file when `pc_manifest.capture_git_status` ran on it. The ordering makes it worse. `take_snapshot` and `capture_boundary_state` run in `run_stage` (lines 803-804) before `breach_outcome`, so the planted file executes before the changed `gitdir_digest` could be reported. Phase 3 adds more call sites for the same function, so this is in scope even though the helper began in Phase 2.
**Fix:** Force the setting off on every harness git call against a model-writable repository.
```python
_GIT_STATUS_BEFORE_Z = ["-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
                        "--no-optional-locks", "status", "--porcelain=v1"]
```
Apply the same `-c core.fsmonitor=false` in `pc_checks._git_output`. Add a test that plants a config with a command and asserts the marker is never created.

## Warnings

### WR-01: Three model-writable places in the run root are invisible to the snapshot

**File:** `tests/harness/pc_row1.py:375-380`
**Issue:** `_excluded` drops `raw/`, `snaps/` and any top-level folder starting with `stage` from the boundary manifest. `raw/` holds the audit hook log and the streams the assertions are computed from. A Bash write there (`python3 -c`, `awk`, `env`) is not seen by the snapshot, and the Write and Edit trace only covers those two tools. A forged `raw/hooklog.jsonl` would feed the instruction audit.
**Fix:** Hash `raw/hooklog.jsonl` and the list of names in `raw/` and `snaps/` before each stage and recheck after, treating an unexpected change as a breach. Stop excluding `stage*` before filing, or list its names too.

### WR-02: `status-begins-with-session` is wrong against the real tool output, and the fake hides it

**File:** `tests/harness/pc_checks.py:725`, `tests/harness/pc_testutil.py:315`, `tests/harness/test_checks.py:698`
**Issue:** The stub prints a branding line on standard error before `session ...`. Claude Code's Bash tool result merges both streams, so the first line of the real result is the brand. The check uses `lstrip().startswith("session")` and therefore can never be yes on a real run. The filed baseline says `status-begins-with-session: no` (mechanical-checks.md line 142), which a reviewer will read as a defect in the skill. The scripted claude captures only stdout, so the test passes and masks it.
**Fix:** Test for a line that starts with `session ` anywhere in the first few lines. Make the scripted claude return stdout then stderr, as the real tool does, and keep the brand line in the fake's output.

### WR-03: `file_row` does not insist on deny entries, so WR-14 is closed only by convention

**File:** `tests/harness/pc_evidence.py:1192`, `tests/harness/pc_promote.py:171`
**Issue:** The runner always passes `ctx.deny_entries`, and a test covers it. But `file_row` never checks that the value is set, and `promote` quietly builds the weaker list without the login when given None. A future caller that builds a context without the entries files a run whose login is not checked by the gate. The Phase 3 context says a test must fail when a sanitised run is promoted without the entries; that proves the current callers, not the API.
**Fix:** Return an error from `file_row` when `ctx.deny_entries is None`. Consider making `promote` raise on None unless the caller passes an explicit opt-out.

### WR-04: Failures after the paid call carry no diagnosis, and a corrupted `.git` is not reported as a breach

**File:** `tests/harness/pc_matrix.py:454-461`, `tests/harness/pc_row1.py:803-804`
**Issue:** Every unexpected exception becomes one fixed line, "the row runner stopped unexpectedly", exit 11, with no exception class. If the model damages `.git`, `capture_boundary_state` raises `CheckError` from inside `run_stage`, after the cost was settled and before the stage record is written. The operator sees the generic line, the ledger refuses a rerun, and `--refile` has no record to read. That is a git breach that is not reported as one.
**Fix:** Print the exception class name (no path or message). Catch `CheckError` around the snapshot and boundary capture in `run_stage`, write the stage record first, and return the breach outcome.

### WR-05: Two inputs fail open to "no breach"

**File:** `tests/harness/pc_checks.py:330-338`, `tests/harness/pc_checks.py:797-800`, `tests/harness/pc_checks.py:842`
**Issue:** `memory_probe` returns `unknown` on any lstat error other than not-found, and `breaches()` only acts on `present`. `compute_facts` includes only the git state files that exist, so a missing state file for a stage silently removes that comparison.
**Fix:** Treat `unknown` as a failure to read (`CheckError`), and require a git state file for every stage that has a record.

### WR-06: The user-names assertion is still vacuous, and the runner now depends on it

**File:** `tests/harness/pc_row1.py:809-810`, `tests/harness/test_row1_assertions.py:239-283`
**Issue:** This is Phase 2 WR-09. `names` is empty when `HOME` is missing from the environment or the listing finds nothing, and `user-names-absent` then passes with zero hits. `evaluate_stage` does not stop on an empty list, and the tests use an empty set as the happy path. The real run printed a count, but nothing fails when the count is zero.
**Fix:** Make `evaluate_stage` stop with a fixed reason when the list is empty, or record the assertion as not assertable the way the hook assertions are.

## Info

### IN-01: The 03-06 open question is answered by existing data; close it and surface the check

**File:** `.planning/phases/03-walking-skeleton-row-1/03-06-SUMMARY.md:62`, `tests/harness/pc_row1.py:841`
**Issue:** See the summary above. The fixture test `test_the_delta_agrees_with_the_difference_of_the_two_cumulative_totals` already pins this for 2.1.310. The harness also computes `cumulative_consistent` for each stage (yes for s1, s2 and s3 in the real run's raw records) but writes it only to the raw record, so the filed evidence cannot show it.
**Fix:** Replace the open question in the summary with the finding (row cost 0.2723 USD is correct, Phase 4 may project from it). Add the consistency flag to `usage.txt`, and print a warning line when it is `no`.

### IN-02: A torn final ledger line bricks the ledger, and the lock has no timeout

**File:** `tests/harness/pc_spend.py:206-207`, `tests/harness/pc_spend.py:243`
**Issue:** A crash mid-append leaves a line without a newline, and every later read raises `SpendError`. That is correct fail-closed behaviour, but nothing documents the recovery, and the harness may not truncate. `flock` blocks forever if another process holds it.
**Fix:** Document the manual recovery in the README. Use `LOCK_NB` in a short retry loop with a deadline.

### IN-03: `--budget` is checked but never enforced, and the row cap is defined twice

**File:** `tests/harness/pc_matrix.py:836`, `tests/harness/pc_rows.py:24`
**Issue:** `ctx.budget` is set and never read. The ledger limit decides spend. `pc_rows.ROW_CAP` is unused and duplicates `pc_spend.ROW_CAP`.
**Fix:** Either cap the ledger limit at the budget or document the flag as a gate only. Delete the unused constant.

### IN-04: The comparer can still raise on huge digit strings (IN-05 recurs)

**File:** `tests/harness/pc_compare.py:223-224`, `tests/harness/pc_compare.py:275`, `tests/harness/pc_compare.py:603`
**Issue:** `int()` over `\d+` text raises `ValueError` past 4300 digits on Python 3.11 and newer, and `\d` also matches non-ASCII digits. `main` catches only `OSError`, `ManifestError` and `CompareError`, so a crafted file gives a traceback.
**Fix:** Use `[0-9]{1,12}` in the patterns and add `ValueError` to the caught set.

### IN-05: The git hygiene environment is written twice, and a private name is imported

**File:** `tests/harness/pc_evidence.py:324-329`, `tests/harness/pc_checks.py:350`
**Issue:** `_hygiene_environment` copies `pc_manifest._git_environment`, and `pc_checks` calls the private original.
**Fix:** Make one public function in `pc_manifest` and use it in both places.

### IN-06: Two definitions of a wrapper call line

**File:** `tests/harness/pc_row1.py:833`, `tests/harness/pc_checks.py:60`
**Issue:** The stage record counts lines containing `" CALL"`, while `slice_log` matches `^\S+ CALL(?: |$)`. They agree on current logs but can drift.
**Fix:** Use one shared regex.

### IN-07: `--all` cannot run a second row into one dated folder

**File:** `tests/harness/pc_row1.py:1089`, `tests/harness/pc_promote.py:106-109`
**Issue:** Every row shares `ctx.destination`. After the first row is filed, `run_row` and `promote` both refuse an existing folder with exit 17. Only row 1 exists today, so this is latent, but `--all` is advertised.
**Fix:** Decide for Phase 4 whether a row files into a per-row subfolder of a folder created once, and change the gate and `promote` together.

### IN-08: A timeout kills only the direct child

**File:** `tests/harness/pc_spike.py:1275-1286` (used at `tests/harness/pc_row1.py:769`)
**Issue:** `subprocess.run` kills `claude` but not its Bash children, which can keep writing while the harness snapshots.
**Fix:** Start the child in its own session and kill the process group on timeout.

### IN-09: The default-memory probe rests on an unverified folder name

**File:** `tests/harness/pc_checks.py:319-327`
**Issue:** Assumption A3 is flagged in the code. If the real folder name differs, `default-memory-folder: absent` in the evidence is vacuous.
**Fix:** Confirm the name once on 2.1.310 by a stat of the expected path after a run that is known to write memory, and record the result.

### IN-10: A few read-only git forms count as mutations

**File:** `tests/harness/pc_checks.py:410-413`, `tests/harness/pc_checks.py:438`
**Issue:** `config`, `tag` and `stash` are mutating for every form, so `env git config --get x` or `env git tag` (reachable through the `env` rule) would make a clean run exit 11 after the money is spent.
**Fix:** Apply the read-only exceptions already used for `branch` (list and get forms).

---

_Reviewed: 2026-10-29T09:08:44Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
