---
phase: 03
review: 03-REVIEW-3.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "A dot-dot path to an approved root counts as an escape, so legitimate writes end in exit 11"
  - id: CR-02
    severity: critical
    disposition: open
    title: "The sed `w` operand is missed after `s` flags, after `!` and after a custom-delimiter address"
  - id: CR-03
    severity: critical
    disposition: open
    title: "The awk read-only gate stops at a semicolon or brace, so a write with one before the redirect passes as read-only"
  - id: CR-04
    severity: critical
    disposition: open
    title: "A git `-c` value that names a command is skipped, so `env git -c core.fsmonitor=... status` runs it unseen"
  - id: CR-05
    severity: critical
    disposition: open
    title: "A path attached to a short option is never judged"
  - id: WR-01
    severity: warning
    disposition: open
    title: "The nested repository walk is case-sensitive, and the default macOS file system is not"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The pin is read from a file the model can reach, and it is read before the guard compares that file"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Interpreter code that builds its path at run time is allowed by the allowlist and files as clean"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Harmless text turns read-only commands into write-capable ones, and `[[ a && b ]]` is split into two parts"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "The test-only remove operation is not confined to the test's own run root"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "The nested walk runs about four times per boundary"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "The chain rule assumes only the last registry stage is conditional"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "The corpus test cannot see the shapes that matter most"
---

# Phase 03 third-pass review disposition

Third pass over the diff of gap-closure plans 03-09 and 03-10. Plan 03-09 holds in full (chain rule, required pin, nested-repository refusal, unknown consistency). The open-world write rule of 03-10 counts all twelve second-pass forms and passes about 150 legitimate shapes, but leaves one false positive (a dot-dot path that resolves inside an approved root, which the skill uses for `../auto-memory`) and four command-line bypasses (the sed `w` operand after `s` flags, an awk write after a semicolon or brace, a command planted through a git `-c` value, and a path attached to a short option). Those five criticals, with WR-01 (case-insensitive `.git` match), WR-02 (the pin held in memory from setup instead of re-read from a model-reachable file) and WR-04 (a tighter read-only gate and `[[ ]]` kept whole), are `open` and go to gap-closure plan 03-11. WR-03 (interpreter code building its path at run time) is `deferred`: it is the run-time-path residual already accepted alongside the script-file residual, for bokiko's Phase 4 decision. The four info items are `deferred` to Phase 4 hardening.
