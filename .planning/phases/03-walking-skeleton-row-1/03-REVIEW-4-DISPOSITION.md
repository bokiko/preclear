---
phase: 03
review: 03-REVIEW-4.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "The awk string blanker reads a double quote inside a regular expression or comment as a string, so a following `print >` or `system(` is hidden"
  - id: CR-02
    severity: critical
    disposition: open
    title: "The working-folder model treats every `cd` as run by the main shell and as successful, so a `cd` in a pipeline, in the background, after `||`, or to a folder that does not exist lets a `..` write land outside the roots"
  - id: CR-03
    severity: critical
    disposition: open
    title: "Two forms of a short-option value are still unjudged: a cluster ending in the value letter with a dot-dot value, and the `sort` gate"
  - id: WR-01
    severity: warning
    disposition: open
    title: "A folder kept across Bash calls, and a `cd` to a substitution, make a legitimate `../` write read as an escape and end the row with exit 11"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "Words that are data in a read-only command (`echo`, `printf`) are judged as paths when the command is redirected, so a note that mentions a path counts as an escape"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "The new test-only rename operation is not confined to the test's own run root"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "A bare `git --exec-path` counts as a git mutation"
---

# Phase 03 fourth-pass review disposition

Fourth pass over the diff of gap-closure plan 03-11. Five of the eight third-pass fixes hold in full; the dot-dot resolution and the attached-option fix hold for the named shapes only, and the awk redirect fix is reopened by a string-blanking defect. CR-01 and CR-02 are regressions against 5ef92ed and CR-03 is a gap in the attached-option fix; with WR-01 (a `cd` to a substitution, which the skill may legitimately do, must not turn a `../auto-memory` write into exit 11) they are `open` and go to the closing gap plan 03-12, which makes the rule strictly more conservative: the awk gate judges the raw program text as well as the blanked text; only a `cd` to a literal target inside the roots joined by `&&` moves the working folder, and every other `cd` form leaves it unknown; every candidate after each option letter is judged as well as the from-the-slash candidate; and a `cd` to a substitution leaves the folder unknown without setting the escape flag, so a later `../auto-memory` write resolves against the project folder as before. WR-02 (data words in a redirected `echo`/`printf`), IN-01 and IN-02 are `deferred` to Phase 4 hardening. The closing pass after 03-12 counts only a regression against 5ef92ed or a false positive on the committed corpus as critical; further new bypass shapes are recorded as warnings for Phase 4, because a shell-command classifier cannot be closed by enumeration and the backstop remains the snapshot diff and the realpath boundary.
