---
phase: 03
review: 03-REVIEW-2.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "`--refile` files a run whose chain stopped early"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "The write-escape rule only sees programs on a fixed list, and `env` is allowed"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Labelled programs still miss two literal forms"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Read-only uses are counted as writes, so a clean run can still end in exit 11"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "The git pin and the hardening do not cover a nested repository, and the pin is optional by absence"
  - id: WR-04
    severity: warning
    disposition: fixed
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

Second pass over the gap-closure diff of plans 03-07 and 03-08. Five of the eight first-pass fixes held fully; three held only for the shapes their tests covered. The two residual criticals and the four warnings were `open` and are now `fixed` by gap-closure plans 03-09 (commits bc17be6..2959732, merged at e064d2c) and 03-10 (commits deb99cb..941fe90, merged at 2208843): filing and refiling require the chain the registry defines (s1, s2, and s3 exactly when the resume marker was found); the git pin is required after setup and a nested repository below the project is refused before any harness git call; the consistency value reads `unknown` when the per-call cost block is absent; and the write-escape rule is open-world (every executed part whose program is not on a short read-only list is write-capable, with fail-closed `env` prefixes, judged script and command-string literals, `mktemp` and `-f` script files, shell reserved words, comments, heredocs and substitutions read as the shell does). A corpus test replays all 348 committed Bash calls (231 executed) with zero escapes, with the refused row10 `mktemp` call as the positive control. CR-02, WR-01 and WR-02 are closed for command-line forms with one residual limit accepted: a script or program file written earlier and run later by `sh file`, `python3 file` or an `env` form is judged by its command line only; scanning executed Write and Edit inputs when a later part names the file is proposed as a Phase 4 follow-up for bokiko's decision. The four info items are `deferred` to Phase 4 hardening.
