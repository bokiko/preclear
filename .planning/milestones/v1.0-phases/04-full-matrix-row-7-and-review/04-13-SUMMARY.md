---
phase: 04-full-matrix-row-7-and-review
plan: 13
subsystem: testing
tags: [harness, row12, frozen-handoff, plan-note-hook, four-stage-chain, ledger-bound, frozen-copy, zero-token]

requires:
  - phase: 04-full-matrix-row-7-and-review
    provides: plan 04-12 path_prepend, extra_files seeds and the 12-row --all total; plan 04-05 hook registry and its lstat and containment checks; plan 04-06 chain-complete rule; plan 04-07 and 04-10 analysis signature (spec, data, facts, clean)
provides:
  - row 12 (row12-frozen-handoff) registered as implemented, four stages (15/0.30, 60/1.30, 15/0.40, 20/0.60), two sessions, PROFILE_GIT (33 rules), memory pinned, resume-line chain, hook (s2, append-plan-note), analyses ("frozen-copy",)
  - pc_rowhooks hook append-plan-note (snapshot snap-2b-after-external-plan-edit; NO_FINALIZER and NO_PERMS tables) and PLAN_NOTE_LINE
  - pc_rowseeds.seed_row12 and ROW12_FOLDER; pc_rows.ROW12, ANALYSIS_FROZEN_COPY and snapshot_name (one rule for snapshot names, fourth stage gives snap-4-after-refresh)
  - pc_evidence.STAGE_ORDER s1..s4, is_refresh_stage, prompt_label, exit_label, and the none-marker chain rule that drops every stage from the first resume stage on
  - pc_review.frozen_copy_lines, analyse_frozen_copy and the Frozen copy section
  - tests/harness/test_row12.py (55 tests)
affects: [04-14, 04-18, 04-19, 04-21]

actuals:
  tokens: 24000
  tasks: 3
  commits: 3

commits: 3
plan_head_before: c4f07b8521da5ee28eb5ce9ae028779d7a5e1869
plan_head_after: 14730b1cd62163f555c9039d202251abd8c3a8c0

key-files:
  created:
    - tests/harness/test_row12.py
  modified:
    - tests/harness/pc_rows.py
    - tests/harness/pc_rowseeds.py
    - tests/harness/pc_rowhooks.py
    - tests/harness/pc_row1.py
    - tests/harness/pc_evidence.py
    - tests/harness/pc_review.py
    - tests/harness/test_rows_plain.py
    - tests/harness/test_boundaries.py
    - tests/harness/test_review.py
    - tests/harness/README.md

key-decisions:
  - "The plan-note hook checks the plan with the same _open_target as every hook, then opens it a second time with O_WRONLY, O_APPEND and O_NOFOLLOW (never O_CREAT or O_TRUNC) and requires the same device and inode as the checked descriptor; the newline and the note line go out in one write"
  - "A hook that appends content has no finalizer and no perms.txt (NO_FINALIZER, NO_PERMS), matching the committed snap-2b folder, which holds no perms.txt"
  - "Snapshot names have one rule, pc_rows.snapshot_name; the only exception is the fourth /preclear stage, which takes snap-4-after-refresh"
  - "Only the first /preclear stage feeds the chain; a later /preclear stage neither reads a resume line nor rewrites chain.json"
  - "The previous cumulative total was already tracked per session key (totals[key]); s4 therefore takes its delta against s3's chain total, and a test pins it"
  - "The s4 file labels follow the committed folder: traces s4-preclear-refresh-*, prompt s4-preclear-prompt.md, s4.err and s4.exit with no label"
  - "The none marker ends the chain before the first resume-kind stage and drops every stage after it, so --refile accepts exactly found with s1 to s4 and none with s1 and s2"
  - "The frozen-copy section prints sha256 digests, counts and yes or no only; matching is by name pattern checkpoint-<UTC timestamp>-<short suffix>.md under each snapshot's preclear copy"

patterns-established:
  - "a between-stage hook may change content and not a mode: it names itself in NO_FINALIZER and NO_PERMS and the engine skips restore and perms for it"
  - "a registry entry may name stages beyond s3; every per-stage name (snapshot, trace, prompt, exit file) comes from one function"

requirements-completed: [RERUN-02]

duration: about 2 hours wall time including three suite passes
completed: 2026-11-06
status: complete
---

# Phase 4 Plan 13: Row 12 frozen handoff Summary

**Row 12 now runs four stages in two sessions on the scripted claude: a work turn, a /preclear turn that also asks for a frozen copy, a harness-made append of one fixed note line to the plan (with its own snapshot and guard), a fresh session from the printed resume line, and a /preclear refresh that resumes that fresh session. The fourth stage is bounded by the spend ledger, its files carry the committed names, and a Frozen copy section prints digests and yes or no equality across the snapshots.**

## Accomplishments

- `append-plan-note` hook: after s2 the harness appends `Note 2026-10-21 (other session): step 3 test must cover both JSON and CSV.` to the plan only. Checks: regular file of the running user, one name, no link in the path, real path inside the project, then an append-only open that must be the same file as the checked descriptor; a newline is added first only when the file is non-empty and does not end in one. Nothing is truncated, created, renamed or deleted. Snapshot `snap-2b-after-external-plan-edit` with its git state and guard (boundary `s2-append-plan-note`); the plan's sha256 differs between snap-2 and snap-2b by exactly that line (test computes both digests).
- Row 12 registered: `--list` shows 4 stages and 2 sessions; the dry run prints `4 stages, 2 sessions`, the s4 line `/preclear turn, resumes the s3 session, 20 turns, cap 0.60`, `worst case 2.00 USD` (the ledger's bound; the four caps sum to 2.60) and `allowlist 33 rules`, and starts no process.
- `seed_row12`: `project/CLAUDE.md` equals the committed fixture byte for byte (sha256 prefix ed03447e9df43888), the plan equals `data/plain-plan.md`; the s2 and s4 prompts are the committed `s2-preclear-prompt.md` and `s4-preclear-prompt.md` read in place (the s2 prompt differs from every other row's, md5 da2d9df3).
- Stage walk: s4 carries `--resume` with s3's session id (not s1's), session count stays 2, and its delta (0.06) is taken against the s3 chain total (0.04, cumulative 0.10). The chain is fed by the first /preclear stage only.
- Filing: the s4 files are `s4-preclear-prompt.md`, `s4-preclear-refresh-trace.md`, `s4-preclear-refresh-full-trace.md`, `s4.err`, `s4.exit`; snapshot folders `snap-2b-after-external-plan-edit` and `snap-4-after-refresh`; every name exists in the committed row 12 folder (test reads it in place). Rows with one /preclear stage keep their labels.
- Chain shapes: found with s1 to s4, and none with s1 and s2 only (no s3, no s4, the hook still ran). `--refile` accepts exactly those two and refuses a found marker with three stages, a none marker with four, and odd marker words.
- Ledger bound: with the first three stages settled at 1.41 the s4 launch is refused with exit 18 (`pc_matrix.execute_row`) before any process, three calls only, no s4 launch line and no authorization line; at exactly 1.40 s4 launches (1.40 plus 0.60 is exactly 2.00).
- `Frozen copy` analysis (`frozen-copy`): for snapshots 2, 2b, 3 and 4 the sha256 of the mutable checkpoint and of every `checkpoint-<timestamp>-<suffix>.md` under the snapshot's preclear copy, the copy count, and per frozen copy `held-in-snapshots N of 4` and `digest-same-in-every-snapshot-that-holds-it yes|no`. Absent snapshot folders and absent preclear copies print `absent`; no file is added; no verdict word (a test scans for the verdict vocabulary and for a list of judging words). Read over the committed row 12 snapshots in place it reports one frozen copy equal in all four.
- Suite: 1999 -> 2054 tests (3 skipped as before), green through `tests/harness/selftest` (banner `0 model calls`) and through `/usr/bin/python3 -I -B -m unittest discover` (Python 3.9).

Suite count: 2054

## Task Commits

1. **Task 1 (tracer): row 12 runs four stages** - `eca9601` (feat)
2. **Task 2: s4 names, chain shapes, ledger bound** - `c471884` (feat)
3. **Task 3: frozen-copy analysis, README, gates** - `14730b1` (feat)

_Tracer gate: the tracer `<verify>` (Task 1 tests, the tripwire dry run, the stage-loop guard modules) ran and passed before the Task 1 commit; no `blocking-human` gate was set. The SUMMARY commit that follows is the fourth commit of the range; `commits:` above is measured before it._

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tests outside `files_modified` encoded old meanings and were moved, none deleted**
- `test_rows_plain.py`: the registry hook-list test now expects rows 6, 7 and 12 (method renamed `..._only_rows_6_7_and_12_name_a_hook`) and the finalizer check allows a hook listed in `NO_FINALIZER`. Commit eca9601.
- `test_boundaries.py`: the hook-table test now expects `append-plan-note` in `HOOKS`. Commit eca9601.
- `test_review.py`: two registry tests listing which rows name an analysis now include row 12 and the `frozen-copy` id. Commit 14730b1.

**2. [Rule 3 - Blocking] README Layout line came with Task 1**
- `test_readme` requires every new file in the Layout list in the commit that adds it; the row 12 paragraph and the module descriptions are in the Task 3 commit.

**3. [Plan sequencing] ROW12 named no analysis until Task 3, and `STAGE_ORDER` was widened in Task 1**
- Filing refuses an unknown analysis id, so the entry carried `analyses=()` until the analysis existed; the tracer needed a fourth stage record to file, so `STAGE_ORDER` moved to s1..s4 in Task 1 and the names and chain rule followed in Task 2.

**4. [Plan wording] 1.40 settled does not refuse s4**
- The plan says three stages settled at 1.40 USD have the s4 launch refused. By the ledger's own rule (pessimistic total plus cap above the row limit) 1.40 plus 0.60 equals 2.00 and launches. The tests refuse at 1.41 and prove the exact boundary at 1.40.

**5. [Plan wording] `pc_row1.py` needed no Task 2 change**
- The s4 launch already goes through `pc_spend.append_launch`; exit 18 comes from the driver's exception table. Task 1 changed `pc_row1.py` (first-/preclear chain feed, comments on the per-session total).

**6. [Rule 3 - Blocking] RED commits not made (tdd="true")**
- A failing test commit would break the green-suite rule; tests were written with the code and run before each commit.

**7. [Process] The commit guard refused `main`**
- `git.branching_strategy: none`, so the Step 0 guard refused every commit; the orchestrator made the task commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed.

**Total deviations:** 7, none changing the behaviour of any earlier row.

## Known Stubs

None.

## Threat Flags

None. The new surface (the harness appending one fixed line to one file of the project between two stages) is the plan's threat model, T-04-58 to T-04-61: symlink, parent-folder swap, second name, read-only plan, directory in place of the file and missing plan are refused with fixed text and the outside file unchanged (tests); a symlink planted by the scripted s2 stops the row with exit 11 and a STOPPED folder; the ledger refuses an over-limit s4; s4's session key selects s3's id and the delta is per session; the frozen-copy section prints digests and counts only and holds no path.

## Notes for plan 04-14 (paid wave C: rows 11 and 12 on the real build)

- **Row ids:** `--row row11-concurrent-change` and `--row row12-frozen-handoff`.
- **Row 11:** three stages 15/0.30 (s1 work), 60/1.30 (s2 /preclear, the git wrapper first on PATH), 15/0.40 (s3 fresh resume); 2 sessions; worst case 2.00.
- **Row 12:** four stages 15/0.30 (s1 work, new session A), 60/1.30 (s2 /preclear with the frozen-copy ask, resumes A), 15/0.40 (s3 fresh resume from the printed line, new session B), 20/0.60 (s4 /preclear refresh, resumes B); caps sum to 2.60, so the worst case is 2.00 (the ledger limit; a fourth launch past it is refused with exit 18); 2 sessions; 33 rules; memory pinned.
- **Wave C worst case:** 2.00 + 2.00 = 4.00. `--dry-run --all` now prints 13 rows, 36 stages, 22 sessions, worst case 24.40 USD (12 earlier rows at 22.40 plus 2.00), under the 25.00 ceiling.
- **First-time observations in row 12:** (a) whether 0.60 and 20 turns are enough for the real s4 refresh (research assumption A9); (b) what the real model does with the s2 prompt's frozen-copy ask (committed run: the mutable checkpoint and `checkpoint-<timestamp>-<suffix>.md` written, one `cp -n` refused by policy and the copy made with Write) and whether it keeps the frozen copy untouched in s4; (c) what the real model does when the plan changed under it (the note is dated 2026-10-21, later than the run, kept as committed; the committed run flagged the future date); (d) the first real run of a second resumed session (s4 resumes s3's session). A stopped row 12 is filed as a visible STOPPED folder; the retry is bokiko's decision.
- **What to read after the row 12 run:** the `Frozen copy` section of `mechanical-checks.md` (per snapshot digest of the mutable checkpoint and of every frozen copy, `held-in-snapshots`, `digest-same-in-every-snapshot-that-holds-it`), the row folder's s4 files, `snap-2b-after-external-plan-edit` and `usage.txt` (s4's cost is taken against the s3 chain). The filed copies are sanitized, so their digests are not the ones measured on the original files.
- **For plan 04-18:** `pc_compare.TRACES` still lists only s1 to s3; the committed and filed s4 trace is `s4-preclear-refresh-full-trace.md`. `pc_evidence.measure_checkpoint` and the row 10 checklist read the first /preclear stage's snapshot (snap-2-after-preclear); the final checkpoint of row 12 is in snap-4-after-refresh.

## Self-Check: PASSED

- Created files exist: `tests/harness/test_row12.py`, this summary.
- Task commits `eca9601`, `c471884`, `14730b1` are ancestors of HEAD (`git rev-list --count c4f07b8..HEAD` was 3 before this summary).
- `commits: 3` measured from the persisted ledger (base c4f07b8).
- Final gates (on the tree of 14730b1): `tests/harness/selftest` 2054 tests OK (3 skipped) with the `0 model calls` banner (floor 1999); the system-interpreter (3.9) unit suite 2054 tests OK; `scripts/test-hooks.sh` 29 PASS, 0 FAIL; leak gate over `tests/harness` 88 files, 0 findings; gitleaks clean; frozen paths against 56e155c unchanged and SKILL.md 11994 bytes; no attribution trailer in the range; nothing under `tests/evidence` changed in `c4f07b8..HEAD`.
