---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "`--refile` files a run that the live path refused"
  - id: CR-02
    severity: critical
    disposition: open
    title: "A write-capable Bash command aimed outside the run root is never a breach"
  - id: CR-03
    severity: critical
    disposition: open
    title: "The harness's `git status` runs a command the model can plant in `.git/config`"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Three model-writable places in the run root are invisible to the snapshot"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`status-begins-with-session` is wrong against the real tool output, and the fake hides it"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`file_row` does not insist on deny entries, so WR-14 is closed only by convention"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "Failures after the paid call carry no diagnosis, and a corrupted `.git` is not reported as a breach"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Two inputs fail open to \"no breach\""
  - id: WR-06
    severity: warning
    disposition: deferred
    title: "The user-names assertion is still vacuous, and the runner now depends on it"
  - id: IN-01
    severity: info
    disposition: open
    title: "The 03-06 open question is answered by existing data; close it and surface the check"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "A torn final ledger line bricks the ledger, and the lock has no timeout"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`--budget` is checked but never enforced, and the row cap is defined twice"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "The comparer can still raise on huge digit strings (IN-05 recurs)"
  - id: IN-05
    severity: info
    disposition: deferred
    title: "The git hygiene environment is written twice, and a private name is imported"
  - id: IN-06
    severity: info
    disposition: deferred
    title: "Two definitions of a wrapper call line"
  - id: IN-07
    severity: info
    disposition: deferred
    title: "`--all` cannot run a second row into one dated folder"
  - id: IN-08
    severity: info
    disposition: deferred
    title: "A timeout kills only the direct child"
  - id: IN-09
    severity: info
    disposition: deferred
    title: "The default-memory probe rests on an unverified folder name"
  - id: IN-10
    severity: info
    disposition: deferred
    title: "A few read-only git forms count as mutations"
---

# Phase 03 review disposition

First pass after wave 6 (the paid row 1 run). The three critical findings (CR-01 refile bypass, CR-02 Bash writes outside the run root never counted as a breach, CR-03 a `core.fsmonitor` command planted in the project's `.git/config` runs under the harness) are `open` and go to a gap-closure plan before the phase closes, together with WR-01 and WR-05 (the same write boundary as CR-02; bundled on the verifier's note), WR-02 (the status check can never be yes on a real run), WR-03 (the deny-entries contract is enforced only by convention) and IN-01 (the cost question). Every other warning and info item is `deferred` to Phase 4 hardening. The reviewer settled the 03-06 open question: `total_cost_usd` on a resumed call is cumulative, so the harness row total of 0.2723 USD is correct and Phase 4 may project from it. The 03-06 summary records that resolution.

Of the 21 items deferred from Phase 2: WR-03 is closed; WR-05, WR-06, WR-12 and IN-01 are closed on the matrix path only (the spike driver is unchanged); WR-14 is closed in every caller but not at the root (this pass's WR-03); WR-09 is open and now load-bearing (this pass's WR-06); WR-04, 07, 08, 10, 11, 13 and IN-02 to IN-06, IN-08 to IN-10 stay open, WR-10 mitigated.
