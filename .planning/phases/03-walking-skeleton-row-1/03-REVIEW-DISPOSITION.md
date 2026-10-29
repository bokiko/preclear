---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "`--refile` files a run that the live path refused"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "A write-capable Bash command aimed outside the run root is never a breach"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "The harness's `git status` runs a command the model can plant in `.git/config`"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Three model-writable places in the run root are invisible to the snapshot"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`status-begins-with-session` is wrong against the real tool output, and the fake hides it"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`file_row` does not insist on deny entries, so WR-14 is closed only by convention"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "Failures after the paid call carry no diagnosis, and a corrupted `.git` is not reported as a breach"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Two inputs fail open to \"no breach\""
  - id: WR-06
    severity: warning
    disposition: deferred
    title: "The user-names assertion is still vacuous, and the runner now depends on it"
  - id: IN-01
    severity: info
    disposition: fixed
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

Second state after gap-closure plans 03-07 and 03-08 (commits 2f9853c..679b758 and bc471b3..0375cdd, merged at 96226db and 8f23762). CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-05 and IN-01 are `fixed`: the harness now counts an executed write-capable Bash part aimed outside the approved roots as a breach, hardens every git call with `core.fsmonitor` and `core.untrackedCache` off and pins the project's git folder digest at setup, guards the run root's own record files, fails closed on the memory probe and the git state files, refuses to refile a run whose stage records are not clean, refuses to file without the deny entries (`promote` raises without an explicit opt-out), reads the helper's `session ` line within the first five lines of the status result, and writes `cumulative-consistent` lines to usage.txt. WR-04, WR-06 and IN-02 to IN-10 stay `deferred` to Phase 4 hardening. The filed baseline `tests/evidence/rerun-2026-10-29-claude-sonnet-5-5` is untouched and keeps `status-begins-with-session: no` under the earlier rule, which the harness README states. The second pass (03-REVIEW-2.md) found two residual blockers in those fixes: `--refile` still accepts a chain that stopped early (CR-01 of the second pass) and the write-escape rule is a closed program list that `env <program>` bypasses (CR-02 of the second pass), plus four warnings; they go to gap-closure plan 03-09 and are tracked in 03-REVIEW-2-DISPOSITION.md.

Of the 21 items deferred from Phase 2: WR-03 is closed; WR-05, WR-06, WR-12 and IN-01 are closed on the matrix path only (the spike driver is unchanged); WR-14 is now closed at the root (`promote` raises on missing deny entries); WR-09 (the vacuous user-names assertion, this pass's WR-06) stays open; WR-04, 07, 08, 10, 11, 13 and IN-02 to IN-06, IN-08 to IN-10 stay open, WR-10 mitigated.
