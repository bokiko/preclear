---
phase: 03
review: 03-REVIEW-5.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "A literal cd that is not joined by a double ampersand, or sits in a group, if or loop, now ends a legitimate `../auto-memory` write with exit 11"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "A cd to an expansion no longer counts a `../` write that lands outside the roots (a form counted at 6d3fe56)"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "An awk regular expression that holds a semicolon or a closing brace hides a following redirect (not counted at 6d3fe56 either)"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "A short-option cluster of five or more letters before a slash value hides the value"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "A cd judged certain can still fail or not run, so a later `../` write after `||` or a bad cd is judged from the wrong folder"
  - id: WR-06
    severity: warning
    disposition: deferred
    title: "A folder kept by a cd in one Bash call makes a legitimate `../` write in the next call read as an escape (carried from the fourth pass, fixed by documentation only)"
---

# Phase 03 closing review disposition

Closing pass over the diff of gap-closure plan 03-12, run with the old tree at 6d3fe56 and the new tree side by side. No critical finding: all 348 committed Bash calls give identical results on both trees (zero escapes, zero git mutations), the known `cd "$(git rev-parse --show-toplevel)"` memory write now counts zero, and the `split_compound` delegation matches the old output on 61,527 inputs. All four fourth-pass fixes hold with their proving tests. The six warnings (literal `cd` joined by `;`, a newline, a subshell, `if` or a loop before a memory write; 98 battery forms of a `cd` to an expansion followed by a `../` write no longer counted, the trade the fourth-pass disposition chose; an awk regex holding `;` or `}`; clusters of five or more option letters; a certain `cd` that still fails; a folder kept across Bash calls) are `deferred` to Phase 4 hardening together with the earlier deferred items and the three accepted residuals (a script file written earlier and run later; interpreter code building its path at run time; values of leading `NAME=value` assignments). The backstop for every residual stays the snapshot diff inside the run root and the realpath boundary on the Write and Edit traces. The Bash write-escape rule is a conservative classifier over command text, not a sandbox, and the harness README says so.
