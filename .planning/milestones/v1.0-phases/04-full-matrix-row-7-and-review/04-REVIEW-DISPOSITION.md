---
phase: 04
review: 04-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "A model-issued `git -c ...` call is labelled as Claude Code's own internal call"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`unquote_printf_q` decodes escapes as code points, so non-ASCII arguments never match"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Row 8a states that no repository exists above the run root but nothing checks it"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The clean-clone stub-digest assertion passes silently when no digest line was checked"
  - id: WR-05
    severity: warning
    disposition: open
    title: "The default clean-clone source is an https clone, and the harness README still says it needs no network"
  - id: IN-01
    severity: info
    disposition: open
    title: "The copy-back runs before a contaminated run is refused"
  - id: IN-02
    severity: info
    disposition: open
    title: "The output scrubber masks paths only, not the login name used under `--real-home`"
  - id: IN-03
    severity: info
    disposition: open
    title: "Invisible U+2028 and U+2029 characters are written literally in a source string"
  - id: IN-04
    severity: info
    disposition: open
    title: "The correlated git-call file is harness-authored but not in the verdict-word scan set"
  - id: IN-05
    severity: info
    disposition: open
    title: "Wrapper logs are read through a silent 8 MiB cap"
  - id: IN-06
    severity: info
    disposition: open
    title: "Production modules call private functions of other modules"
  - id: IN-07
    severity: info
    disposition: open
    title: "The git wrapper runs the program named in a file that sits in a folder the model can write"
  - id: IN-08
    severity: info
    disposition: open
    title: "One meta-test asserts nothing about the code under test, and temporary-folder handling is inconsistent"
---

# Phase 04 review disposition

One row per finding of 04-REVIEW.md; every finding is `open` until a later fix or an accepted-residual note changes it. Phase 4 ships with 0 critical, 5 warning and 8 info findings; none is a blocker, and the harness suites (2364 tests) are green on the reviewed head.

| ID | Severity | Disposition | Source |
|---|---|---|---|
| WR-01 | warning | open | 04-REVIEW.md |
| WR-02 | warning | open | 04-REVIEW.md |
| WR-03 | warning | open | 04-REVIEW.md |
| WR-04 | warning | open | 04-REVIEW.md |
| WR-05 | warning | open | 04-REVIEW.md |
| IN-01 | info | open | 04-REVIEW.md |
| IN-02 | info | open | 04-REVIEW.md |
| IN-03 | info | open | 04-REVIEW.md |
| IN-04 | info | open | 04-REVIEW.md |
| IN-05 | info | open | 04-REVIEW.md |
| IN-06 | info | open | 04-REVIEW.md |
| IN-07 | info | open | 04-REVIEW.md |
| IN-08 | info | open | 04-REVIEW.md |
