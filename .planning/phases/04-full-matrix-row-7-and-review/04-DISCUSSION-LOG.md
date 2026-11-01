# Phase 4: Full Matrix, Row 7 and Review - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-31
**Phase:** 04-full-matrix-row-7-and-review
**Areas discussed:** Budget and pacing, Row 7 three runs, Clean-clone matrix, Codex review and docs

---

## Budget and pacing

| Option | Description | Selected |
|--------|-------------|----------|
| One word per wave | A go before each paid wave; each wave reports its cost before the next asks | ✓ |
| One budget word for the phase | One total cap enforced by the ledger; waves run back to back | |
| One word for dev waves, one for the matrix | Two go words: waves A to D plus row 7 triple, then the clean-clone matrix | |

**User's choice:** One word per wave

| Option | Description | Selected |
|--------|-------------|----------|
| Finish the wave, label the row | Failed row filed as a visible failure folder; other rows continue; bokiko decides the retry | ✓ |
| Stop at the first failure | Driver exits at the first failed row | |
| Stop only on a breach, label on cap or turns | Exit 11 halts; cap or turn limit continues | |

**User's choice:** Finish the wave, label the row

| Option | Description | Selected |
|--------|-------------|----------|
| New attempt folder, failed one kept | Retry is attempt 2 in its own folder; both in the digest table | ✓ |
| Retry replaces the failed row | Only the retry is filed | |

**User's choice:** New attempt folder, failed one kept

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 2 USD and the split | s1 0.30/15, s2 1.30/60, s3 0.40/15 on every row | ✓ |
| Lower to 1 USD per row | Tighter cap; risk of stalling on a heavy row | |
| Claude decides per row | Planner sets a cap per row from the committed trace length, never above 2 USD | |

**User's choice:** Keep 2 USD and the split

---

## Row 7 three runs

| Option | Description | Selected |
|--------|-------------|----------|
| Three full independent chains | Fresh run root, own work turn, restriction, /preclear, fresh resume from the printed checkpoint | ✓ |
| One work turn, three /preclear turns | One s1, three s2 sessions resumed from it | |
| Three chains without s3 | Match the committed row exactly | |

**User's choice:** Three full independent chains

| Option | Description | Selected |
|--------|-------------|----------|
| Mechanical candidates, reviewer confirms | Harness lists same-turn tool_use ids sharing a path or token; none means UNSUPPORTED; reviewer confirms | ✓ |
| Reviewer fills the table by hand | Harness prints entries and all tool_use ids; a human pairs them | |
| Fully mechanical verdict | Harness decides supported or not (conflicts with EVID-05) | |

**User's choice:** Mechanical candidates, reviewer confirms

| Option | Description | Selected |
|--------|-------------|----------|
| One review file across all three runs | row7-review.md at the folder top level, one section per attempt | ✓ |
| Inside each attempt's README | Each run folder carries its own table | |

**User's choice:** One review file across all three runs

| Option | Description | Selected |
|--------|-------------|----------|
| Live probe in the run root | Throwaway folder, mode 555, create attempt, expect EACCES; otherwise SKIPPED | ✓ |
| Check uid and mount flags only | Infers rather than proves | |

**User's choice:** Live probe in the run root

---

## Clean-clone matrix

| Option | Description | Selected |
|--------|-------------|----------|
| New folder under the shared runs root, this Mac | Bootstrap clones the public repository into a dated folder under PRECLEAR_RUNS_ROOT | ✓ |
| Another machine | Second Mac or Linux box; widens the phase | |
| You pick the path by hand | bokiko creates the folder and runs the bootstrap | |

**User's choice:** New folder under the shared runs root, this Mac

| Option | Description | Selected |
|--------|-------------|----------|
| env -i with an explicit short allowlist | HOME (throwaway), PATH, CLAUDE_CONFIG_DIR, PRECLEAR_RUNS_ROOT, DISABLE_AUTOUPDATER, TERM, LANG; names recorded | ✓ |
| Your normal shell environment | No scrubbing | |
| Claude decides the list | Planner picks the minimal set | |

**User's choice:** env -i with an explicit short allowlist

| Option | Description | Selected |
|--------|-------------|----------|
| PATH has no helper plus wrapper log scan | Before: no checkpoint binary on PATH, helper path absent; after: every call resolved to the stub | ✓ |
| Wrapper log scan only | Only the after-run scan | |

**User's choice:** PATH has no helper plus wrapper log scan

| Option | Description | Selected |
|--------|-------------|----------|
| Layouts first, then rows in acceptance order | plain-memory, hub-memory, bound-ledger, row 1 to 12 | ✓ |
| Rows first, layouts last | | |

**User's choice:** Layouts first, then rows in acceptance order

| Option | Description | Selected |
|--------|-------------|----------|
| One core chain per layout | s1, s2, s3 with layout-specific mechanical facts; other sub-checks stay manual and are listed as not exercised | ✓ |
| Full checklist per layout | Every sub-check as a harness stage | |
| Claude decides which sub-cases | Planner picks the mechanically checkable ones | |

**User's choice:** One core chain per layout

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse the harness-owned config dir | Existing CLAUDE_CONFIG_DIR passed into the minimal environment; only loggedIn read | ✓ |
| Fresh config dir, you log in once | New config dir inside the clone; BLOCKED until login | |

**User's choice:** Reuse the harness-owned config dir

---

## Codex review and docs

| Option | Description | Selected |
|--------|-------------|----------|
| One verdicts file plus README lines | codex-review.md at top level; each row's PENDING line replaced by the verdict plus a pointer, on bokiko's word | ✓ |
| Verdicts only in the top-level file | Row READMEs keep PENDING | |
| Verdict edits in each row README only | No separate file | |

**User's choice:** One verdicts file plus README lines

| Option | Description | Selected |
|--------|-------------|----------|
| New baseline becomes the reference, old folder kept | Comparer target and pointers move; publication-2026-10-20 labelled superseded | ✓ |
| Both stay references | Comparer takes both targets | |
| Decide after seeing the verdicts | Pointer question left open | |

**User's choice:** New baseline becomes the reference, old folder kept

| Option | Description | Selected |
|--------|-------------|----------|
| You open the tab, Claude prepares the brief | Brief file in the evidence folder; bokiko pastes it into Codex and the verdicts back | ✓ |
| Claude drives Herdr | Claude opens the tab via the herdr skill | |

**User's choice:** You open the tab, Claude prepares the brief

| Option | Description | Selected |
|--------|-------------|----------|
| Pointer paragraphs only | Short automated-run paragraph in acceptance.md; one Unreleased CHANGELOG entry | ✓ |
| Rewrite acceptance.md around the harness | Manual procedure becomes an appendix | |
| Also cut a tagged release in CHANGELOG | Pointer paragraphs plus a versioned release | |

**User's choice:** Pointer paragraphs only

---

## Claude's Discretion

- Row wave A to D grouping; row 11's n and argv; row 10's asserted refusal shape; how SKIPPED
  rows and failed attempts appear in the digest table; the bootstrap script's name and assertions;
  the Do-not-redo candidate heuristic's token rules; the review brief layout; which deferred
  Phase 3 warnings are fixed alongside the new row hooks.

## Deferred Ideas

- Full layout checklists as harness stages; a tagged CHANGELOG release; a Linux validation run;
  a SKILL.md rule on Do-not-redo citations if the defect recurs; a resumable matrix.
