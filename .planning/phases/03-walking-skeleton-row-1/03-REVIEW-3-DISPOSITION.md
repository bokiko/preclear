---
phase: 03
review: 03-REVIEW-3.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "A dot-dot path to an approved root counts as an escape, so legitimate writes end in exit 11"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "The sed `w` operand is missed after `s` flags, after `!` and after a custom-delimiter address"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "The awk read-only gate stops at a semicolon or brace, so a write with one before the redirect passes as read-only"
  - id: CR-04
    severity: critical
    disposition: fixed
    title: "A git `-c` value that names a command is skipped, so `env git -c core.fsmonitor=... status` runs it unseen"
  - id: CR-05
    severity: critical
    disposition: fixed
    title: "A path attached to a short option is never judged"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "The nested repository walk is case-sensitive, and the default macOS file system is not"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The pin is read from a file the model can reach, and it is read before the guard compares that file"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Interpreter code that builds its path at run time is allowed by the allowlist and files as clean"
  - id: WR-04
    severity: warning
    disposition: fixed
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

Third pass over the diff of gap-closure plans 03-09 and 03-10. Plan 03-09 held in full. The five criticals and three of the warnings against the open-world write rule and the pin were `open` and are now `fixed` by gap-closure plan 03-11 (commits 178cc0b..df28c24, merged at 98693c5): a dot-dot word is resolved with realpath against the tracked working folder over literal segments only, so the skill's `../auto-memory` writes are inside the roots while any expansion before a dot-dot stays an escape; text attached to a short option is judged; the awk and sed readers find a print redirect at parenthesis depth zero and the `w` operand after `s` flags, `!` and a custom delimiter; every git `-c`, `--exec-path` and `--config-env` before the verb is a git mutation of the fixed form `config-command`; the nested-repository walk compares names without case; the setup pin is held in memory in the run context and a rewritten, removed or malformed pin file is refused before any process. HARN-09 is re-proved through the driver with the clean control and twelve seeded failures, and the corpus test reports zero write escapes and zero git mutations over the 231 executed committed Bash calls, with the 13 `../auto-memory` commands covered. WR-03 (interpreter code building its path at run time) and the four info items are `deferred` to Phase 4 hardening, with the executor's proposal to judge the values of leading `NAME=value` assignments recorded for bokiko's decision alongside the script-file residual.
