# Phase 3: Walking Skeleton (Row 1) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-28
**Phase:** 03-walking-skeleton-row-1
**Areas discussed:** Row 1 session shape, Evidence folder and comparison, Reviewer checklist and preflight

Area not selected by bokiko: "Baseline model and row budget" — folded into the last area as one
question, because spend is bokiko's hard rule and cannot default.

---

## Row 1 session shape

| Option | Description | Selected |
|--------|-------------|----------|
| One session, resumed | s1 with a pinned --session-id, s2 with --resume, as S2b proved | ✓ |
| Two fresh sessions | New session per stage; /preclear sees only the files | |
| You decide | Claude matches the committed traces | |

**User's choice:** One session, resumed

| Option | Description | Selected |
|--------|-------------|----------|
| Committed prompts, byte for byte | Reuse s1 and s2 prompts unchanged | |
| Committed prompts with a pinned preamble | Add a fixed containment line | |
| You decide | Reuse; add a preamble only if the dry run shows the allowlist cannot contain the work turn | ✓ |

**User's choice:** You decide

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include it | Row 1 files s1, s2 and the read-only fresh-resume s3 | ✓ |
| No, s1 and s2 only | Smallest first paid row; s3 joins in Phase 4 | |
| You decide | Include if the committed folder holds a third-stage trace | |

**User's choice:** Yes, include it

| Option | Description | Selected |
|--------|-------------|----------|
| Pinned allowlist, no approvals | Committed tools.txt, permission mode default, denials reported | ✓ |
| Pinned allowlist plus a per-row extra list | Row fixtures may add Bash rules | |
| You decide | Start from tools.txt, add only rules the traces show used | |

**User's choice:** Pinned allowlist, no approvals

---

## Evidence folder and comparison

| Option | Description | Selected |
|--------|-------------|----------|
| rerun-<date>-<model> | Date and model in the path; row folders keep committed names | ✓ |
| publication-<date> | Mirrors the committed name; model only in model-id.txt | |
| You decide | Any scheme that refuses an existing name | |

**User's choice:** rerun-<date>-<model>

| Option | Description | Selected |
|--------|-------------|----------|
| New baseline, not a replication | States model, build and cost; committed folder stays the reference | ✓ |
| Candidate replacement | Calls the folder a replacement candidate pending the Phase 4 review | |
| You decide | Label as new baseline, note replacement for Phase 4 | |

**User's choice:** New baseline, not a replication

| Option | Description | Selected |
|--------|-------------|----------|
| File set, headings, counts | Missing files, differing headings, call counts, bytes outside cap; digests listed | ✓ |
| File set only | Missing or extra files per row | |
| You decide | Whatever compares mechanically without reading prose | |

**User's choice:** File set, headings, counts

| Option | Description | Selected |
|--------|-------------|----------|
| Nobody, it only reports | Exit 0 when both trees readable; never PASS or FAIL | ✓ |
| Exit non-zero on any difference | Script-friendly gate, but reads as a verdict | |

**User's choice:** Nobody, it only reports

---

## Reviewer checklist and preflight

| Option | Description | Selected |
|--------|-------------|----------|
| Mechanical facts with their sources | One fact per line naming its source file; blank reviewer boxes | ✓ |
| Facts plus the model's own claims | Each fact beside the model's claim | |
| You decide | Facts, plus claims only where the committed README contrasted them | |

**User's choice:** Mechanical facts with their sources

| Option | Description | Selected |
|--------|-------------|----------|
| Three states, three exit codes, SKIPPED filed | SKIP filed with reason; FAIL and BLOCKED file nothing; dry run covers all three | ✓ |
| Two states: run or refuse | One refusal exit | |
| You decide | Reuse the reserved pc_exitcodes family | |

**User's choice:** Three states, three exit codes, SKIPPED filed

| Option | Description | Selected |
|--------|-------------|----------|
| usage.txt per row plus a folder total | Per-stage tokens, turns, total_cost_usd; README repeats totals | ✓ |
| Folder-level total only | One usage line in the top README | |
| You decide | Per-stage usage wherever the committed format has room | |

**User's choice:** usage.txt per row plus a folder total

| Option | Description | Selected |
|--------|-------------|----------|
| claude-sonnet-5-5, 2 USD per row | Same model the spikes pinned; one attempt without bokiko's word | ✓ |
| claude-sonnet-5-5, 5 USD per row | More headroom, same model | |
| A different model id | Typed under Other | |

**User's choice:** claude-sonnet-5-5, 2 USD per row

---

## Claude's Discretion

- Prompt reuse versus a pinned preamble, decided by the dry run.
- Driver CLI surface details, exact exit code values, max-turns per stage under the row cap.
- Fixture seeding of the stub home and ledgers, wrapper-log to tool_use correlation, staging layout.

## Deferred Ideas

- Replacement of the committed reference folder — Phase 4 after the Codex review.
- Remaining Phase 2 review warnings not touching the runner — Phase 4 hygiene.
- Per-row extra allowlist rules — only if Phase 4 rows need them.
- Linux credential location for the stranger clone — Phase 4.
