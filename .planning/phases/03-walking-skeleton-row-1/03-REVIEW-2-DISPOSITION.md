---
phase: 03
review: 03-REVIEW-2.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "`--refile` files a run whose chain stopped early"
  - id: CR-02
    severity: critical
    disposition: open
    title: "The write-escape rule only sees programs on a fixed list, and `env` is allowed"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Labelled programs still miss two literal forms"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Read-only uses are counted as writes, so a clean run can still end in exit 11"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The git pin and the hardening do not cover a nested repository, and the pin is optional by absence"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The cumulative-consistent line is vacuous when the stream has no per-call cost block"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Formatting slip in `run_row`"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "An empty list of deny entries is accepted, and the guard test checks only a name"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "The git folder digest sees the built-in file system monitor's files"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "The hook log guard cannot see same-window changes, and the first stage has no baseline"
---

# Phase 03 second-pass review disposition

Second pass over the gap-closure diff of plans 03-07 and 03-08. Five of the eight first-pass fixes hold fully; three hold only for the shapes their tests cover. The two residual criticals (an interrupted chain can still be refiled; the write-escape rule is a closed program list that `env <program>`, `env -P`, `env -iS` and `find -exec sh -c` walk around) and the four warnings are `open` and go to gap-closure plan 03-09: chain completeness before staging, an open-world write rule with a short read-only list and a corpus test over every committed trace, a fail-closed git pin with a nested-repository refusal, and an `unknown` consistency value when the per-call cost block is absent. The four info items are `deferred` to Phase 4 hardening. The reviewer found no false positive on the 248 executed Bash commands across the committed traces or on the twelve real commands in the filed baseline.
