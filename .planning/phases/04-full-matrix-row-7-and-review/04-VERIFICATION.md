---
phase: 04-full-matrix-row-7-and-review
verified: 2026-11-11T16:14:55Z
status: gaps_found
score: 3/5 must-haves verified
covered_files:
  - ".planning/phases/04-full-matrix-row-7-and-review/04-01-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-01-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-02-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-02-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-03-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-03-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-04-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-04-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-05-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-05-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-06-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-06-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-07-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-07-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-08-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-08-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-09-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-09-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-10-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-10-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-11-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-11-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-12-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-12-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-13-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-13-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-14-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-14-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-15-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-15-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-16-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-16-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-17-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-17-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-18-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-18-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-19-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-19-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-20-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-20-SUMMARY.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-21-PLAN.md"
  - ".planning/phases/04-full-matrix-row-7-and-review/04-21-SUMMARY.md"
  - "CHANGELOG.md"
  - "tests/acceptance.md"
  - "tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/README.md"
  - "tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/README.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/digest-table.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/environment-names.txt"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/review-brief.md"
  - "tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/usage-by-row.txt"
  - "tests/harness/README.md"
  - "tests/harness/git-wrapper"
  - "tests/harness/pc_baseline.py"
  - "tests/harness/pc_cleanclone.py"
  - "tests/harness/pc_review.py"
  - "tests/harness/pc_rowhooks.py"
  - "tests/harness/pc_rows.py"
  - "tests/harness/pc_rowseeds.py"
  - "tests/harness/test_frozen_baseline.py"
covered_digest: "v3:sha256:33a8e89d742caf4baf074174608885d562e7b5c01dd74dbd59832355c0f92f45"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Row 7 reruns three times and a review table pairs every Do-not-redo entry of each printed checkpoint with the tool_use ids that support it, entries with no supporting call listed as such (SC1, RERUN-01)"
    status: partial
    reason: "Attempt 3 of the triple printed a full checkpoint as plain markdown (no fenced block) with a Do not redo section of two bullets. The harness takes only a fenced block, so row7-review.md records 'printed checkpoint: none', 'entries: 0' and the attempt has no third stage. Two Do-not-redo entries of a printed checkpoint are therefore in no review table. The note that Codex should decide whether they count (04-17-SUMMARY, notes for plan 04-21) was not carried into the review brief and the Codex answer does not mention it."
    artifacts:
      - path: "tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-review.md"
        issue: "Attempt 3 section lists 0 entries although s2-preclear-trace.md of that attempt holds a ## Do not redo section with two bullets; its closing line also names a Codex review file of the triple that does not exist"
      - path: "tests/evidence/rerun-2026-11-09-claude-sonnet-5-5-triple/row7-all-destinations-denied-attempt-3/s2-preclear-trace.md"
        issue: "Holds the unlisted entries: the CSV exporter exists with RFC 4180 quoting; memory was empty at the start and two memory files were created"
    missing:
      - "A review-table part (the row7-review command writes row7-review-part-N.md and never edits the earlier file) that lists attempt 3's two unfenced Do-not-redo entries with their candidates or UNSUPPORTED, or an accepted override stating that only fenced prints count"
      - "A recorded decision on the D-06 reviewer confirmation of the pairings, or a correction of the closing sentence of row7-review.md that points at a Codex review file of the triple"
human_verification:
  - test: "Confirm the Codex review of the baseline was run in a visible Herdr tab (SC4, D-16)"
    expected: "bokiko states that the pasted answer came from Codex running in a Herdr tab he opened. The filed codex-review.md records only that the answer was pasted into the conversation, shows a terminal footer, and says the Codex model was not stated."
    why_human: "Nothing in the repository records where Codex ran. Only bokiko can attest to the tab."
  - test: "Decide the row 7 attempt 3 question (see gaps) and the D-06 pairing confirmation"
    expected: "bokiko either asks for a review-table part that lists attempt 3's two entries, or accepts the fenced-only definition as an override."
    why_human: "Whether an unfenced printed checkpoint counts as a printed checkpoint is a judgement about the contract, and the evidence folder is frozen."
---

# Phase 4: Full Matrix, Row 7 and Review Verification Report

**Phase Goal:** A stranger clones the public repository, runs the free self-test, and then the full matrix (three layouts plus every publication row) on a pinned model. The result is filed as a new dated baseline that Codex has reviewed, and row 7 has been rerun three times with its defect visible in a review table, not hidden.
**Verified:** 2026-11-11T16:14:55Z
**Status:** gaps_found
**Re-verification:** No, initial verification

Repository state checked: HEAD c05c9cc equals origin/main, working tree clean apart from two untracked planning files. The repository is PUBLIC per `gh repo view`. The commits after the orchestrator's a8b7f83 gate add review and security documents only.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Row 7 preflight proves the chmod denial or files SKIPPED; row 7 runs three times; invariants hold in all three; review table pairs every Do-not-redo entry of each printed checkpoint; failed attempts kept (HARN-12, RERUN-01) | FAILED (partial, BLOCKER) | Probe, SKIPPED path, three runs and invariants verified. Attempt 3's two Do-not-redo entries are missing from the table (see Gaps). |
| 2 | Row 10 expects the quoted-porcelain fallback with no redirection or NUL exception in the allowlist; row 11 injector fires on the n-th model-initiated exact-argv call, never on startup calls, empty log for a no-op session, wrapper lines correlated with tool_use ids (HARN-10, HARN-11) | VERIFIED (warning on correlation) | See below. |
| 3 | From a fresh clone in a never-used path, minimal environment, no runs folder, private helper unreachable, --all produces one folder per --list entry, every helper call resolved to the stub (RERUN-02) | VERIFIED (recorded deviation) | 21 of 21 folders, 24 of 24 helper calls to the stub. Real home folder used on bokiko's word. |
| 4 | New dated folder with digest table, cost per row, new-baseline label, comparer differences against the publication folder, leak-gated, Codex per-row verdicts recorded from a visible Herdr tab before any acceptance claim (RERUN-03, RERUN-04) | UNCERTAIN (WARNING, human decision) | Everything checkable is verified. The Herdr tab cannot be confirmed from the repository. |
| 5 | tests/harness/README.md states prerequisites, free-then-paid order, measured cost, platforms, what a pass proves; acceptance.md and CHANGELOG point to it (RERUN-05) | VERIFIED (warning: stale opening line) | See below. |

**Score:** 3/5 truths verified. Behavior-unverified truths: 0.

### Truth 1 detail

Verified parts:
- **HARN-12 probe.** `chmod_denial_probe` in `tests/harness/pc_rowhooks.py` makes a throwaway folder in the raw run folder, sets mode 555, attempts one exclusive create and accepts only EACCES. Root, a created file and any other error each return a fixed reason. A reason files the row SKIPPED with exit 10 before any spend. `test_row7.py` ran alone: 98 tests OK, including the root, permissive-mount, other-error and SKIPPED-never-reads-as-success cases.
- **Three runs.** `rerun-2026-11-09-claude-sonnet-5-5-triple` holds three filed attempts (exit 0 each, 0.2295, 0.2445 and 0.1736 USD). The 555 restriction snapshot is present in each. Each s2 shows one Write to the preclear folder that failed with EACCES, executed chmod 0, writes outside approved roots 0, Bash write escapes 0, git mutations 0, ledgers unchanged, isolation assertions holding.
- **Defect visible.** Attempt 2's only entry is listed UNSUPPORTED with 0 candidates. Attempt 1's entry lists one candidate, a Read of the skill's own configuration reference, which a reviewer must still judge. The matrix chain's two entries are also UNSUPPORTED in its candidates file.
- **Failed attempts kept.** Attempt 3 is filed with its reason.

Failed part, observed directly: attempt 3's `s2-preclear-trace.md` ends with a printed checkpoint whose `## Do not redo` section holds two bullets. `row7-review.md` says "printed checkpoint: none", "entries: 0" for that attempt, and no third stage ran. The harness documents that only a fenced block counts (`tests/harness/README.md` line 381), and the executor of plan 04-17 disclosed this and asked the Codex round to decide whether the bullets count. Plan 04-21 did not carry the question into the review brief, the Codex answer does not address it, and the plan 04-21 summary says the row 7 pairings were not decided. The closing paragraph of `row7-review.md` also tells readers that Codex and the owner confirm each pairing "in the Codex review file of the triple", and no such file exists. Net effect: of the three row 7 samples, one entry set is hidden from the table, which is the thing the phase goal says must not happen, and only two of three samples ran a fresh-resume stage.

**This may look intentional.** The fenced-only rule is documented. To accept it instead of closing the gap, bokiko can add to this file's frontmatter:

```yaml
overrides:
  - must_have: "review table pairs every Do-not-redo entry of each printed checkpoint"
    reason: "A printed checkpoint means a fenced block; attempt 3 printed none and is filed with NO-PRINTED-CHECKPOINT"
    accepted_by: "bokiko"
    accepted_at: "<ISO timestamp>"
```

### Truth 2 detail

- **HARN-10.** The baseline row 10 allowlist is the 33-rule file with no redirection, tee, sidecar or NUL rule (tools.txt holds only the two status prefix rules). `test_rows_git.py` pins this, including a corpus test over every buildable allowlist. The filed row 10 shows the quoted-porcelain form executed twice and the NUL form with a redirect denied once (`mechanical-checks.md`, Row 10 status form). The sidecar file holds 0 NUL bytes.
- **HARN-11.** `tests/harness/git-wrapper` compares the whole argument list to exact lines, counts a match under a lock, injects only when the ordinal equals the fire-on number, and exits with the real git's code. Claude Code's own calls start with `-c`, never equal a listed line, and show ORD=- in the filed log. Filed row 11: `injection.log` holds `INJECTED ORD=1` and the first prescribed status call carries ORD=1. `test_git_wrapper.py` ran alone: 52 tests OK, including the no-op session test (absent injection log, notes file untouched), the concurrent-racer test and the committed-internal-calls-never-match test.
- **Correlation, warning.** `git-calls-correlated.txt` joins 18 logged calls: 9 internal, 2 matched to one tool_use id, 7 ambiguous with several candidate ids, including all three prescribed status calls. This is the designed behaviour of the join (plan 04-10) and was disclosed in plans 04-12 and 04-14. Only the ordinal tells the three status calls apart. Review finding WR-01 (a model-issued `git -c` call is labelled internal) and WR-02 (non-ASCII arguments reported unmatched) are open and weaken the join further for rows with hostile names.

### Truth 3 detail

- **Folder shape.** 21 outcome folders equal 3 layouts plus the 18 numbered rows of `ROW_IDS`. README reports 21 filed, 0 STOPPED, 0 SKIPPED, Run state complete.
- **Clone facts.** Clone head 0bacd2b equals the pushed tip. Source: the public address. Pre-run counts: 0 runs paths, 0 checkpoint binaries on the child's search path, 0 helper files in the clone.
- **Helper calls, re-counted by this verifier.** The eight `wrapper-calls.log` files hold 24 CALL lines (11, 7, 2, 3, 1 over five folders with calls). Every wrapper delegates to `checkpoint_stub.py`. The stub sha256 in the eight wrapper rows equals the committed stub (`96791fa6...`). Filed skill digest equals `shasum -a 256 SKILL.md` (`86e5b14e...`).
- **Environment.** `environment-names.txt` lists 8 names. Every stage of every row reports isolation assertions holding and user-level instruction entries 0.
- **Recorded deviation from D-10.** The login did not survive the throwaway home, so the child ran with the real HOME plus USER. bokiko said "1.yes 2.yes ... 3.yes" at the checkpoint (plan 04-20 deviations 2 to 4), the README names the home kind as real, and `--real-home` is an explicit flag that prints a warning. The default path of the bootstrap still uses the throwaway home. Consequence worth knowing: under the real home the private helper exists on disk, so "unreachable" for this run rests on the scrubbed search path, the clone check and the zero non-stub calls, not on absence from the file system. WR-04 (the digest check can pass with zero digests checked) is open; the filed baseline is not affected because all eight wrapper rows hold a matching stub digest line.

### Truth 4 detail

Verified:
- **Files.** `digest-table.md` (21 rows with skill, adapter, stub, wrapper digests and cost), `usage-by-row.txt` (per-stage costs, total 5.7467 USD, 0 UNCONFIRMED), `README.md` (labels the run a new baseline on claude-sonnet-5-5, Claude Code 2.1.310, not a replication), `comparison-vs-publication-2026-10-20.txt` (18 rows compared, differences listed and not judged), `review-brief.md`, `environment-names.txt`.
- **Leak gate.** Run by this verifier: baseline folder 1203 files, 0 findings; triple folder 172 files, 0 findings. gitleaks: no leaks in either. `check-words`: 0 hits in 487 and 84 files. No home path, host or private address found by grep.
- **Codex verdicts.** `codex-review.md` holds 21 verdict lines. All 21 row READMEs end with the matching verdict plus "(see codex-review.md)", none is PENDING. The recomputed frozen digest equals the pinned `1e4f68bb...`; `test_frozen_baseline.py` 30 OK, `test_frozen_reference.py` 5 OK, `test_frozen_tree.py` 9 OK.
- **No acceptance claim.** CHANGELOG, README and the harness text state no acceptance of the new baseline, and the reference was not swapped (bokiko's word was file-only, and Codex's lines are mixed). D-15 therefore remains open by design.
- **Frozen paths.** `git diff 994267a HEAD` over SKILL.md, references, tests/fixtures, the publication folder, the first baseline and the five older layout folders is empty. SKILL.md is 11994 bytes. All 70 commits since the base are authored by bokiko, 0 carry an attribution trailer.

Not verifiable here: that the review ran in a visible Herdr tab, and which Codex model answered (the file says "not stated"). The review took about one minute for 21 rows.

Observation for acceptance, not a gap: the filed Codex lines are not uniformly favourable. Row 6 "denial handling cannot be judged" (the plan file was mode 444 yet both edits succeeded), row 7 "evidence claim overstated", and row 10 "sidecar format failed". The harness makes no verdict, which is what the contract asks for.

### Truth 5 detail

`tests/harness/README.md` section "Reproducing the matrix" lists prerequisites (build 2.1.310, git, Python 3.9 stdlib, own login, network for the clone), the order self-test, dry run, one paid row, bootstrap probe then paid matrix, the measured cost block tied to the two evidence files by a test, platforms (macOS verified, Linux not) and both "what a green run proves" and "does not prove" paragraphs. `test_readme.py` ran alone: 41 OK. `tests/acceptance.md` points to the README (lines 17 to 18) and CHANGELOG Unreleased carries an entry that names it. Warning (review finding WR-05): line 5 of the README still says everything runs without a network, which the clone step contradicts a few hundred lines later.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/harness/pc_rowhooks.py` | restrict-555 hook, chmod probe | VERIFIED | Exists, wired through the row registry, 98 row 7 tests pass |
| `tests/harness/git-wrapper` | row 11 injector | VERIFIED | Exercised by 52 tests and by filed row 11 evidence |
| `tests/harness/pc_review.py` | Do-not-redo candidates, git-call join | VERIFIED with limits | Fenced-only checkpoint detection; ambiguity in the join |
| `tests/harness/pc_baseline.py` | close, finalize, file-review, record-verdict, frozen digest | VERIFIED | Digest recomputed and equal to the pin |
| `tests/harness/pc_cleanclone.py` | clean-clone bootstrap | VERIFIED | Produced the filed baseline; default path uses a throwaway home |
| `tests/evidence/rerun-2026-11-09-...-triple/` | three row 7 attempts, row7-review.md | PARTIAL | Attempt 3 entries absent from the table |
| `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/` | baseline with 21 outcome folders | VERIFIED | Six top-level files plus codex-review.md |
| `tests/harness/README.md` | stranger entry point | VERIFIED | Stale opening sentence |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| row registry | row 7 probe | `PROBES` in pc_rowhooks | WIRED | Probe runs before the first snapshot |
| git wrapper | row 11 seed | `install_git_wrapper`, `MATCH_ARGV_LINES`, `FIRE_ON` | WIRED | Filed row 11 carries wrapper-git.sh, git-calls.log, injection.log |
| baseline README | verdict lines | `record-verdict` | WIRED | 21 of 21 |
| README cost block | filed evidence | cost:begin and cost:end markers and a test | WIRED | Figures equal the digest table total |
| acceptance.md, CHANGELOG | harness README | pointer text | WIRED | Present |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| digest-table.md, usage-by-row.txt | costs, digests | filed per-row usage.txt and digests.txt | Yes | FLOWING |
| README cost block | measured cost | the two evidence files, read by test | Yes | FLOWING |
| review-brief.md | row facts | filed row folders | Yes | FLOWING |

### Behavioral Spot-Checks

Run as single test files, with claude removed from PATH and temporary output in the scratch folder. No model, no matrix and no clean-clone run was started.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Row 7 probe, SKIPPED path, restriction | unittest test_row7 | 98 OK | PASS |
| Injector, no-op session, startup calls | unittest test_git_wrapper | 52 OK | PASS |
| Allowlist model | unittest test_allowlist | 48 OK | PASS |
| Frozen baseline digest and pins | unittest test_frozen_baseline | 30 OK | PASS |
| Frozen reference and tree | unittest test_frozen_reference, test_frozen_tree | 5 and 9 OK | PASS |
| README equals code | unittest test_readme | 41 OK | PASS |
| Leak gate over both new folders | pc_leakgate.py scan | 0 findings | PASS |
| gitleaks over both new folders | gitleaks detect --no-git | no leaks | PASS |
| Verdict vocabulary | pc_baseline.py check-words | 0 hits | PASS |

The orchestrator's gate (not re-run here, as instructed) reported the full suite and selftest at 2364 tests OK and hooks 29 pass, 0 fail.

### Probe Execution

Step 7c: SKIPPED. No probe-*.sh files are declared by this phase's plans.

### Requirements Coverage

All eight IDs appear in plan frontmatter. REQUIREMENTS.md still shows each as unchecked and Pending in the traceability table, which the orchestrator owns. No orphaned IDs.

| Requirement | Source plans | Status | Evidence |
|-------------|--------------|--------|----------|
| HARN-10 | 04-10, 04-11 | SATISFIED | Row 10 allowlist and filed fallback outcome, tests pin both |
| HARN-11 | 04-10, 04-12, 04-14 | SATISFIED (warning) | Injector verified; correlation is candidate lists, 7 of 18 ambiguous |
| HARN-12 | 04-06, 04-08, 04-17 | SATISFIED | Live probe with SKIPPED exit 10, filed rows ran after it held |
| RERUN-01 | 04-06, 04-07, 04-17 | PARTIAL | Attempt 3 entries absent from the table |
| RERUN-02 | 04-01 to 04-05, 04-08 to 04-16, 04-19, 04-20 | SATISFIED | 21 of 21 from a clean clone; real home deviation recorded |
| RERUN-03 | 04-01 to 04-03, 04-18, 04-20 | SATISFIED | Folder, digest table, usage, label, comparison present |
| RERUN-04 | 04-18, 04-21 | SATISFIED, provenance unconfirmed | 21 verdict lines filed; Herdr tab needs bokiko's confirmation |
| RERUN-05 | 04-21 | SATISFIED | README, acceptance.md, CHANGELOG |

### Decisions D-01 to D-17

| Decision | Honored | Note |
|----------|---------|------|
| D-01 to D-04 (go word per wave, failure folders, new attempt folders, 2 USD cap) | Yes | Paid commands ran on bokiko's word; no retry authorization used; no row run twice in the matrix |
| D-05 (three independent full chains) | Partly | Attempt 3 ended after s2 because no fenced checkpoint was printed |
| D-06 (candidates, reviewer confirms) | Partly | Candidates printed; no reviewer confirmation of pairings filed |
| D-07 (one row7-review.md, one section per attempt) | Yes | |
| D-08 (live probe before money) | Yes | |
| D-09 to D-13b (clean-clone mechanics) | Yes, with D-10 deviation | Real home and USER, approved by bokiko |
| D-14 (codex-review.md, one verdict line per row) | Yes | Model line reads "not stated" |
| D-15 (swap after acceptance) | Not triggered | No acceptance; word was file-only |
| D-16 (bokiko opens the tab) | Unconfirmed | See human verification |
| D-17 (pointer paragraphs only) | Yes | |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| tests/harness (all non-allowed modules) | deletion, rename, truncate primitives | none found | Constraint held |
| tests/evidence new folders | home path, host, address, verdict vocabulary | none found | Constraint held |
| harness modules, README, acceptance.md, CHANGELOG | debt markers (TBD, FIXME, XXX) | none found by grep | No debt-marker blocker |
| 04-REVIEW.md | 5 warnings and 8 info findings, all open, 0 critical | Warning | WR-01, WR-02 and WR-04 touch the proofs this phase relies on; WR-05 is the stale README line. None changes a filed result. |

### Warnings (non-blocking)

1. Row 7 review table closing sentence refers to a Codex review file of the triple that does not exist.
2. Real home folder for the clean-clone run (recorded deviation); "helper unreachable" rests on search path and call counts.
3. Git-call correlation is mostly candidate lists, not single ids.
4. README line 5 still says no network.
5. Codex model not stated; review duration about one minute.
6. REQUIREMENTS.md traceability rows still Pending (orchestrator-owned).

### Human Verification Required

1. **Herdr tab provenance.** Test: bokiko confirms the Codex answer filed in codex-review.md came from Codex in a Herdr tab he opened. Expected: a yes, or a note to add to the folder's review record. Why human: not recorded anywhere in the repository.
2. **Row 7 attempt 3.** Test: bokiko decides between a review-table part that lists the two unfenced entries and an override that only fenced prints count. Expected: one of the two. Why human: it is a contract interpretation and the evidence folder is frozen.

### Gaps Summary

One blocker. The row 7 review table omits the Do-not-redo entries that attempt 3 of the triple printed without a fenced block, so the defect the phase promises to show is partly hidden in one of three samples, and the third sample has no fresh-resume stage. The data to close it exists in the committed trace of that attempt. A new part file from the existing `row7-review` command, or an explicit override, closes it without spending any money. Everything else in the goal is achieved: the clean-clone matrix is filed as a leak-gated new baseline with 21 Codex verdict lines and no acceptance claim, the README is a working entry point, and the HARN-10 to HARN-12 machinery is in place and tested.

---

_Verified: 
_Verifier: Claude (gsd-verifier)_
