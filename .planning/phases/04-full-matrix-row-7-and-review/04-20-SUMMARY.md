---
phase: 04-full-matrix-row-7-and-review
plan: 20
subsystem: testing
tags: [harness, matrix, clean-clone, paid-run, baseline, real-home, do-not-redo]
requires:
  - phase: 04-19
    provides: the clean-clone bootstrap (pc_cleanclone.py), its stub and its zero-token gates
  - phase: 04-17
    provides: the row 7 triple, the cost reference for the matrix's own row 7 chain
provides:
  - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5, the baseline: 21 filed entries, six top-level files, 1202 files, Run state complete
  - measured cost of the full 21-chain matrix on claude-sonnet-5-5 and Claude Code 2.1.310 from a clean clone
  - the helper-unreachable counts of the clean-clone run (24 helper calls, all to the clone stub)
  - the USER fix for the real-home child environment (commit 0bacd2b)
affects: [04-21]
key-files:
  created:
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/README.md
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/digest-table.md
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/usage-by-row.txt
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/comparison-vs-publication-2026-10-20.txt
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/review-brief.md
    - tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/environment-names.txt
  modified:
    - tests/harness/pc_cleanclone.py
    - tests/harness/test_cleanclone.py
    - tests/harness/README.md
key-decisions:
  - "bokiko allowed the real home folder for the child (a recorded deviation from D-10): the login did not survive the throwaway home"
  - "USER is carried into the real-home child environment as an eighth name, because the macOS Keychain login needs both HOME and USER"
  - "The paid command ran once on bokiko's own go with budget 10.50 USD, started by the orchestrator, not by an executor; the executors started no claude process"
  - "The baseline is unreviewed: every row README ends with the reviewer line PENDING; the review is plan 04-21"
metrics:
  duration: filing and verification after the paid run, about 15 minutes
  completed: 2026-11-11
status: complete
requirements-completed: [RERUN-02, RERUN-03]
actuals:
  tokens: 451000
  tasks: 3
  commits: 2
commits: 2
plan_head_before: 6cd60f068a664cdfea43a6f5702afff4ba9a19ba
plan_head_after: 8d7d00d6a853931a7361f4f8f5e04d5c66e958a7
---

# Phase 4 Plan 20: Clean-Clone Matrix Baseline Summary

**The full matrix ran once from a clean clone on bokiko's word (`go`, budget 10.50 USD, real home allowed): 21 of 21 entries filed, 0 stopped, 0 skipped, 0 refused, every stage `success`, 5.7467 USD in all against a projection of about 5.3. The login did not survive the throwaway home, so the child ran under the real home folder. Nothing is reviewed.**

The folder `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5` is the new baseline. Every row README ends with the reviewer line `PENDING`. The review is plan 04-21.

## The run

- Rehearsal (zero tokens): the free probe under the throwaway home printed BLOCKED, exit 12 (the login is hidden). The matrix dry run printed 21 chains with a worst case of 38.40 USD (the plan text says 42.00). The unit suite ran 2347 tests, OK.
- Push 1: origin 994267a to 6cd60f0, 54 commits, the hooks ran.
- Attempt 1 of the paid command: exit 2 (usage), nothing spent. Build 2.1.310 had been pruned from the machine by the Claude Code auto-updater. bokiko said go to reinstalling it; the orchestrator reinstalled 2.1.310 and restored the default `claude` to its newer build.
- Attempt 2 (`--budget 10.50 --selftest --real-home`): the clone self-test printed 2347 OK, the dry run was OK, the preflight printed BLOCKED, exit 12, nothing spent. Measured cause: `claude auth status` reports a logged-in account only when the real HOME and the variable USER are both present. LOGNAME alone, or USER with a throwaway home, do not work (the macOS Keychain). Fix commit `0bacd2b` (`pc_cleanclone.py`, `test_cleanclone.py` with 103 tests, README). Quick gates on it: hooks 29 ok and 0 not ok, leak gate 0 findings, gitleaks 0.
- Push 2: 6cd60f0 to 0bacd2b.
- Attempt 3: exit 0. Run state complete. No `--authorize-retry`, no `--refile`, no row run twice.
- Copy-back promoted 1202 files into the baseline folder, which this plan's evidence commit `8d7d00d` (`test(04-20): file the clean-clone baseline evidence`) files. The commit carries no trailer and no hook was skipped.

## Facts the plan's output demands

| Fact | Value |
|---|---|
| Login survived the throwaway home | No (BLOCKED, exit 12, twice: once in the rehearsal, once in attempt 2 before the USER fix) |
| Home kind of the child | real (named in the README as "the real home folder") |
| Entries filed / STOPPED / SKIPPED / refused / not started | 21 / 0 / 0 / 0 / 0 |
| Stage outcome | every stage that ran ended with result subtype `success` |
| Stages that ran | 55 (21 s1, 21 s2, 12 s3, 1 s4); rows 2, 3a, 3b, 3c, 4a, 4b, 5a, 5b and 6 have s1 and s2 only |
| Exit code | 0 |
| Clone head vs pushed tip | clone head 0bacd2b1e8223b442bbfdea45f585668eb15c942, pushed tip 0bacd2b: equal |
| Clone self-test | 2347 tests, OK, 4 skipped |
| Environment names (8) | DISABLE_AUTOUPDATER, HOME, LANG, PATH, PRECLEAR_HARNESS_HOME, PRECLEAR_RUNS_ROOT, TERM, USER (the seven of the plan plus USER) |
| Helper files in the clone before the run | 0 |
| Checkpoint binaries on the child's search path before the run | 0 |
| Helper calls after the run | 24, of which 24 to the clone stub and 0 to anything else |
| Wrapper run roots | 8, all naming the clone stub, none elsewhere |
| Run state | complete, 21 of 21 entries with an outcome folder |

## Measured cost (from `usage-by-row.txt`; USD, rounded to four places from the text the file holds)

| Entry | s1 | s2 | s3 | s4 | Row total |
|---|---|---|---|---|---|
| plain-memory | 0.0527 | 0.1207 | 0.0465 | - | 0.2200 |
| hub-memory | 0.0571 | 0.1534 | 0.0487 | - | 0.2591 |
| bound-ledger | 0.0537 | 0.3159 | 0.0548 | - | 0.4244 |
| row1-wrong-binding | 0.0557 | 0.1550 | 0.0575 | - | 0.2682 |
| row2-double-conflict | 0.0563 | 0.3711 | - | - | 0.4274 |
| row3a-missing-executable | 0.0533 | 0.1729 | - | - | 0.2262 |
| row3b-denied-helper-write | 0.0533 | 0.2615 | - | - | 0.3148 |
| row3c-unbound-fallback-none | 0.0536 | 0.1344 | - | - | 0.1880 |
| row4a-unknown-backend | 0.0555 | 0.1726 | - | - | 0.2281 |
| row4b-conflicting-blocks | 0.0575 | 0.1714 | - | - | 0.2289 |
| row5a-no-memory | 0.0447 | 0.1206 | - | - | 0.1653 |
| row5b-disabled-memory | 0.0416 | 0.1538 | - | - | 0.1955 |
| row6-readonly-plan | 0.0472 | 0.1511 | - | - | 0.1983 |
| row7-all-destinations-denied | 0.0478 | 0.1199 | 0.0547 | - | 0.2224 |
| row8a-non-git | 0.0439 | 0.1656 | 0.0551 | - | 0.2646 |
| row8b-detached-head | 0.0476 | 0.1427 | 0.0821 | - | 0.2724 |
| row8c-unborn-branch | 0.0467 | 0.1534 | 0.0559 | - | 0.2561 |
| row9-linked-worktree | 0.0465 | 0.1588 | 0.0556 | - | 0.2609 |
| row10-large-status | 0.0490 | 0.2482 | 0.0697 | - | 0.3669 |
| row11-concurrent-change | 0.0515 | 0.1765 | 0.0559 | - | 0.2839 |
| row12-frozen-handoff | 0.0481 | 0.2167 | 0.0673 | 0.1435 | 0.4755 |

The cheapest entry is row5a at 0.1653; the dearest is row12 at 0.4755, then row2 at 0.4274 and bound-ledger at 0.4244. The usage file counts 21 cost values and 0 UNCONFIRMED.

| Measure | USD |
|---|---|
| Matrix total (`usage-by-row.txt`) | 5.7467 |
| Budget bokiko named | 10.50 |
| Projection from one measured chain (an extrapolation, FA-8) | about 5.3 |
| M, the measured sample of the whole matrix before this run (row 1 of Phase 3 plus waves A to D plus the triple) | 6.26 |
| Phase 3 row 1 chain | 0.2723 |
| Wave A (04-08) | 0.79 |
| Wave B (04-11) | 1.43 |
| Wave C (04-14) | 0.75 |
| Wave D (04-16) | 2.37 |
| Row 7 triple (04-17; three attempts 0.2295, 0.2445, 0.1736) | 0.6476 |
| Phase 4 paid total before this plan | 5.99 |
| Phase 4 paid total after this plan | 11.74 |

The matrix cost about 1.08 of the projection and about 0.92 of M, and used about 0.55 of the budget. The cost was reported to bokiko by the orchestrator before the review is asked.

## Ledger

The spend ledger holds, under the scope `matrix`, 55 launch lines and 55 settle lines: one launch line per stage that ran, 55 distinct stage keys over 21 rows, no stage launched twice and no authorization line.

## Row 7 of the matrix, beside the triple

The matrix's own row 7 chain is a fourth row 7 chain, listed separately from the three triple attempts (bokiko's answer recorded in 04-17).

| Chain | s1 | s2 | s3 | Total | Checkpoint | Do-not-redo entries |
|---|---|---|---|---|---|---|
| Matrix row 7 | 0.0478 (4 turns) | 0.1199 (11 turns) | 0.0547 (4 turns) | 0.2224 | printed, 2506 bytes, s3 ran | 2, each with 0 candidates, both UNSUPPORTED |
| Triple attempt 1 | 0.0465 | 0.1274 | 0.0556 | 0.2295 | 2595 bytes | 1, 1 candidate |
| Triple attempt 2 | 0.0455 | 0.1445 | 0.0545 | 0.2445 | 2550 bytes | 1, 0 candidates, UNSUPPORTED |
| Triple attempt 3 | 0.0457 | 0.1278 | not run | 0.1736 | NO-PRINTED-CHECKPOINT, reason none | 0 |

Facts of the matrix chain, from `row7-all-destinations-denied/do-not-redo-candidates.md` and `mechanical-checks.md`:

- **Candidate list.** The chain marker is found and the list holds 2 entries. Entry 1 reads that plan, memory and git state were read on the run date. Entry 2 reads that the memory root had no index and that one index and one note were created. Each entry has 0 candidates and is marked UNSUPPORTED, so the harness found no call of the /preclear turn that shares a whole token with either entry.
- **s3 outcome.** The /preclear reply printed a checkpoint in a fenced block, a fresh session was started from it, and s3 ended `success` after 4 turns.
- **Write denial.** One Write to the preclear folder errored with `EACCES: permission denied, mkdir '<run>/project/.preclear'`. Executed writes under the preclear folder 0, errored writes 1, tool results holding EACCES 1, tool results holding the words permission denied 0, checkpoint assembly calls 1. The denial recurs in all four row 7 chains. The reply states that persistence is blocked and that no other path was tried.
- **chmod.** Executed chmod commands 0. The harness applied the mode 555 restriction between s1 and s2 (the `snap-1b-after-restriction` snapshot), as in the triple.
- **Other counts.** Writes outside the approved roots 0, Bash write escapes 0, git mutations 0, helper calls 0, ledger digests unchanged from setup to the last snapshot.
- **Readability.** The row has its README, `do-not-redo-candidates.md` and the row 7 section of `review-brief.md`. The brief says that no row 7 review table is filed in this folder and points to the triple's `row7-review.md`. A table for the matrix chain does not exist yet; building or reading it from `do-not-redo-candidates.md` is a task of the 04-21 round.

## Verification results

| Check | Result |
|---|---|
| Folder shape | 21 outcome folders (one per `--list` entry), the six top-level files, `Run state: complete`, 27 entries at the top level |
| README clone head and environment names | clone head equals the pushed tip 0bacd2b; 8 names listed, also in `environment-names.txt` |
| Row READMEs | 21 of 21 end with the exact reviewer line, which reads PENDING |
| `pc_baseline.py check-words` | 487 files scanned, 0 hits |
| Leak gate over the folder | 1202 files scanned, 0 findings |
| gitleaks over the folder | exit 0 |
| Ledger | scope `matrix`, 55 launch lines, 55 distinct stages, 0 authorization lines |
| Write-escape corpus (`test_checks.py -k WriteEscapeCorpus`) | 4 tests, OK, with the folder present |
| `test_frozen_baseline.py` | 30 tests, OK, with the folder present (no pinned list needed the new folder) |
| `test_evidence.py` | 91 tests, OK, with the folder present |
| Diffs of frozen paths: `SKILL.md`, `references`, `tests/fixtures`, publication-2026-10-20 against 56e155c; rerun-2026-10-29 against e85d347; wave-a f30bee2; wave-b 11e0317; wave-c af6da17; wave-d bbbbadf; triple 45d444d | all empty |
| `SKILL.md` size | 11994 bytes |
| Comparison report against the publication folder | 3666 lines, 18 rows compared, differences listed and not judged; the new side's tree digest it prints (2aecd7f5...) was taken while the report was written and is not the frozen digest below |
| `git status --porcelain -- tests/harness` | empty |

Deletions in the evidence commit: 0.

The orchestrator's gate runs the full unit suite and the selftest; this executor did not run them. Suite count: 2347 (the figure printed by the rehearsal suite and by the clone's own self-test on head 0bacd2b; the orchestrator's final gate re-measures it and its printed figure overrides this line if it differs).

## Frozen digest of the baseline (for plan 04-21)

`pc_baseline.frozen_digest` over `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5` (reads only; reviewer line and `codex-review.md` excluded):

```
1e4f68bbf7f87c8b57df31414e80d6f2bccc2bee3a336769a71f1efa993dc805
```

The publication folder's frozen digest by the same function, for comparison: 268818206a76c809ce832ba245e5bda648b7f48a46a56c6d9da8b08ef2aea117.

## Deviations from Plan

**1. [Process] Build 2.1.310 pruned and reinstalled**
- The Claude Code auto-updater had removed 2.1.310 from the machine (its versions folder held only newer builds), so attempt 1 exited 2 with nothing spent. bokiko said go to reinstalling the build; the orchestrator did it and restored the default `claude` to the newer build. The run used the 2.1.310 build, which the README and every row record.

**2. [D-10] Real home folder allowed by bokiko**
- The free probe printed BLOCKED (login hidden under the throwaway home). bokiko answered the checkpoint in his own words: "1.yes 2.yes and push it as much commits as you can i wanna my activity to be high 3.yes", which the orchestrator took as go, budget 10.50, push now and real home allowed. The README names the home kind as real.

**3. [Rule 1 - Bug] USER added to the real-home child environment (an eighth name)**
- **Found during:** attempt 2 (preflight BLOCKED, exit 12, nothing spent).
- **Issue:** under `--real-home` the child had HOME but no USER, and the Keychain login needs both. A D-10 deviation, shown to bokiko through the run's README.
- **Fix:** carry USER into the child environment for the real-home case only (commit `0bacd2b`, with 70 new test lines in `test_cleanclone.py`).
- **Files modified:** `tests/harness/pc_cleanclone.py`, `tests/harness/test_cleanclone.py`, `tests/harness/README.md`.

**4. [D-10 wording] Item 8 shown at the checkpoint**
- The checkpoint showed bokiko the wording difference that the harness config folder variable carries the harness home slot (`PRECLEAR_HARNESS_HOME`) instead of the config folder variable named in D-10. His answer to the checkpoint is the quoted message in deviation 2.

**5. [Process] Two pushes instead of the plan's one**
- The second push carried the USER fix. bokiko's message asked for the pushes to go out ("push it as much commits as you can").

**6. [Process] Paid commands run by the orchestrator, not by an executor**
- As in 04-14, 04-16 and 04-17, the executor pattern refuses a go that is only quoted to it. The orchestrator ran the paid command on bokiko's own word. The executors of this plan started no claude process and spent nothing.

**7. [Process] The commit guard refuses `main`**
- The orchestrator made the commits from COMMIT REQUESTED blocks. No config was changed and no hook was bypassed. STATE.md, ROADMAP.md and REQUIREMENTS.md are left to the orchestrator.

**8. [Estimate] The plan's worst case printed differently**
- The dry run printed a worst case of 38.40 USD, the plan text says 42.00 (21 chains at 2.00). Not a fault: the plan's text is the upper ceiling and the dry run is the harness's own sum.

The dry-run folder date did not drift this time: the rehearsal and the run both fell on 2026-11-11.

**Total deviations:** 8, one of which (3) changed code.

## Known Stubs
None.

## Threat Flags
None. The USER fix adds one environment name to the child under an option bokiko already allowed; it adds no endpoint, no file path and no secret value. The leak gate and gitleaks scanned the baseline folder with 0 findings.

## Notes for plan 04-21

- **The folder to review:** `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5`; the paste text for the reviewer is its `review-brief.md`. Every row README ends with the reviewer line PENDING; a verdict is written there only after the Codex round.
- **The digest to record:** `1e4f68bbf7f87c8b57df31414e80d6f2bccc2bee3a336769a71f1efa993dc805` (frozen digest above, commit `8d7d00d`). Any later change to the folder other than a verdict line or `codex-review.md` changes it.
- **Row 7:** four chains to pair: wave A's single chain, the three triple attempts and the matrix chain. The matrix chain's two entries have no candidates, so both are UNSUPPORTED in the harness list; the pairing decision is the Codex round's. The brief names no row 7 table for this folder, so the round needs one built for the matrix chain.
- **The swap:** after acceptance, the one-value swap is `DEFAULT_REFERENCE` in `tests/harness/pc_compare.py` (now `tests/evidence/publication-2026-10-20`) to this folder, with the frozen-baseline pins and the comparer text that name the publication folder moved in the same commit.
- **Comparison:** the report against the publication folder compares the 18 numbered rows. The three memory entries (plain-memory, hub-memory, bound-ledger) are not in it; the publication folder has no such entries, and the older dated memory folders sit beside it, not inside it. Differences are listed, not judged.
- **Cost facts to carry:** matrix 5.7467 USD, Phase 4 paid total 11.74 USD.
- Every harness-authored string must stay free of the forbidden vocabulary; `check-words` over this folder exited 0.

## Self-Check: PASSED
- The baseline folder exists with 21 outcome folders and its six top-level files; this summary exists.
- Commits `0bacd2b` and `8d7d00d` are ancestors of HEAD; `git rev-list --count 6cd60f0..HEAD` was 2 before this summary.
- `commits: 2` is measured from the base 6cd60f068a664cdfea43a6f5702afff4ba9a19ba (the head before the fix commit; no ledger file for 04-20 existed, so the base is the head the orchestrator's tracking commit left); the summary commit that follows is the third commit of the range.
