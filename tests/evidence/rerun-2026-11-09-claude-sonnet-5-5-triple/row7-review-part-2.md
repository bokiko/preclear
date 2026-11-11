# Row 7 review: Do-not-redo candidates for each attempt

The harness lists candidates and counts only. For each entry of the `## Do not redo` section of a printed checkpoint it
lists the tool calls of the same /preclear turn that share a whole token with the entry (a path, a backtick span or a hex
run). The word UNSUPPORTED means the list of candidates is empty and nothing more. Whether a listed candidate really backs its
entry is a human judgement made by the reviewers outside the harness. A Review record section, when a note was given,
says where it is recorded.
Every line that starts with `> ` is text quoted from the model, on one line and capped; it is never structure.
An attempt whose chain marker is NO-PRINTED-CHECKPOINT is also read for a checkpoint printed outside a fenced block. Its entries are listed
under the word unfenced, with the same candidate rule, as a reading of lower confidence.
Stopped and skipped attempts are kept, with their reasons.

part: 2
earlier parts: row7-review.md
The earlier parts are unchanged by this part. This part is built again from the filed files, so the latest part is the complete table.

## Review record
The lines below are quoted from a note given by the person who filed this part.
> The first part of this review, row7-review.md, is unchanged. Its introduction points to a Codex review file of this folder, and this folder holds no such file.
> The Codex review of the baseline run is filed at tests/evidence/rerun-2026-11-11-claude-sonnet-5-5/codex-review.md. Its row 7 line holds the words evidence claim overstated and the older table does not validate this run.
> Decision on the pairings: the pairings of row7-review.md are rejected. The owner's answer at the filing of that Codex review took the proposed default, which follows its row 7 line.
> This part adds the Do-not-redo entries of attempt 3, which printed its checkpoint outside a fenced block. They are listed as unfenced entries, and no reviewer has judged them yet.

attempts: 3

## Attempt 1: row7-all-destinations-denied
state: filed
chain marker: found
checkpoint bytes: 2595
entries: 1
facts: executed-writes-under-preclear=0 errored-writes-under-preclear=1 eacces-results=1 permission-denied-results=0 executed-chmod=0
assembly calls: 1

| Entry | Candidates | Status |
| --- | --- | --- |
| 1 | 1 | listed |

entry 1:
> Discovery: no Preclear configuration block in CLAUDE.md; memory root was empty before this run; no ledger or handoff exists. Invalid if CLAUDE.md or those files change.
candidates 1: 1
candidate toolu_01CFcb1xAdCcBEb4CcCRsgBs Read
> <run>/project/.claude/skills/preclear/references/configuration.md

## Attempt 2: row7-all-destinations-denied-attempt-2
state: filed
chain marker: found
checkpoint bytes: 2550
entries: 1
facts: executed-writes-under-preclear=0 errored-writes-under-preclear=1 eacces-results=1 permission-denied-results=0 executed-chmod=0
assembly calls: 1

| Entry | Candidates | Status |
| --- | --- | --- |
| 1 | 0 | UNSUPPORTED |

entry 1:
> Memory and plan updates are done; don't rewrite unless the decision changes. Step 2 CSV code is written but untested; recheck if the src digest changes.
candidates 1: 0
UNSUPPORTED

## Attempt 3: row7-all-destinations-denied-attempt-3
state: filed
chain marker: NO-PRINTED-CHECKPOINT
printed checkpoint: none
checkpoint bytes: 0
entries: 0
facts: executed-writes-under-preclear=0 errored-writes-under-preclear=1 eacces-results=1 permission-denied-results=0 executed-chmod=0
assembly calls: 1
unfenced checkpoint: found
unfenced source: the final reply in s2-preclear-trace.md outside any fenced block, and the calls in s2-preclear-full-trace.md
unfenced confidence: lower than a fenced block, which has a closing fence; text after the last bullet of an unfenced section joins its last entry
unfenced match rule: whole tokens as for a fenced entry, so a bare name in an entry is not the same token as a longer path in a call
unfenced entries: 2
unfenced calls read: 10
unfenced results not searched: 2 (the filed trace holds Read, Glob and Grep results by length only)
unfenced assembly calls: 1

| Unfenced entry | Candidates | Status |
| --- | --- | --- |
| 1 | 0 | UNSUPPORTED |
| 2 | 0 | UNSUPPORTED |

unfenced entry 1:
> The CSV exporter exists with RFC 4180 quoting. It is invalid if the `widget_export.py` digest changes.
candidates 1: 0
UNSUPPORTED

unfenced entry 2:
> Memory was empty at the start. I created `widget-export-json-default.md` and `MEMORY.md`, so reread them before editing.
candidates 2: 0
UNSUPPORTED
