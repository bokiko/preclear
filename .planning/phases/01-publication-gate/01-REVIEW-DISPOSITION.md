---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "commit-msg hook fails open when the pattern file is missing or empty"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "pre-push silently skips any check that is not executable or not present"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "home-folder path rule does not match a path with no trailing slash"
  - id: WR-01
    severity: warning
    disposition: open
    title: "relative `--source` and `--record` are resolved after the script changes directory"
  - id: WR-02
    severity: warning
    disposition: open
    title: "the attribution check passes when `git log` fails"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "the pre-flip deny-list scan can pass or skip without the owner's entries"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "deny-list check never looks at file paths or commit messages"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "deny-list scan treats an awk failure as \"no hits\""
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "host-name entries of short common words block unrelated commits"
  - id: WR-07
    severity: warning
    disposition: open
    title: "the whole `anthropic.com` domain is exempt from the email rule"
  - id: WR-08
    severity: warning
    disposition: fixed
    title: "the pre-flip negative control would pass for the wrong reason"
  - id: IN-01
    severity: info
    disposition: open
    title: "no option terminator before the user-supplied clone source"
  - id: IN-02
    severity: info
    disposition: open
    title: "unquoted range expansion mishandles remote names with spaces or glob characters"
  - id: IN-03
    severity: info
    disposition: open
    title: "deny entries are not trimmed, and a pinned name starting with a dash breaks grep"
  - id: IN-04
    severity: info
    disposition: open
    title: "attribution patterns are both broad and incomplete"
  - id: IN-05
    severity: info
    disposition: open
    title: "false positives and uncovered identifier forms in the gitleaks rules"
  - id: IN-06
    severity: info
    disposition: open
    title: "the hooks trust the working-tree config, and the scanner version is not enforced"
  - id: IN-07
    severity: info
    disposition: open
    title: "the \"anonymous\" probe can use the owner's credentials"
  - id: IN-08
    severity: info
    disposition: open
    title: "a pipe character in a detail string corrupts the record table"
  - id: IN-09
    severity: info
    disposition: open
    title: "coverage gaps and silent skips in the test script"
open: 12
total: 20
recorded: 2026-10-24T14:35:30.262Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 01-REVIEW-FIX.md |
| CR-02 | critical | fixed | 01-REVIEW-FIX.md |
| CR-03 | critical | fixed | 01-REVIEW-FIX.md |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | fixed | 01-REVIEW-FIX.md |
| WR-04 | warning | fixed | 01-REVIEW-FIX.md |
| WR-05 | warning | fixed | 01-REVIEW-FIX.md |
| WR-06 | warning | fixed | 01-REVIEW-FIX.md |
| WR-07 | warning | open | - |
| WR-08 | warning | fixed | 01-REVIEW-FIX.md |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
