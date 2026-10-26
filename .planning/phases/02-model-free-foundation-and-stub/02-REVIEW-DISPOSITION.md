---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Sanitizer leaves the login name in place when a JSON escape precedes it, and the gate cannot catch it"
  - id: CR-02
    severity: critical
    disposition: open
    title: "Leak gate misses a home path that is followed by a JSON escape, a bracket or a quote-like delimiter"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Gate identifier rules can be evaded with non-ASCII neighbours or an upper-case host suffix"
  - id: WR-02
    severity: warning
    disposition: open
    title: "A git failure or a missing deny file silently drops the private deny list (fail-open), and the file parser mishandles BOM and padding"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Stub `update` accepts a body that holds the checkpoint end marker and corrupts the ledger for good"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The stub deletes and overwrites files, outside the project's no-delete rule, and the static scan cannot see it"
  - id: WR-05
    severity: warning
    disposition: open
    title: "`run_s1` has no pre-paid existence check for its output, and the README's rerun advice conflicts with the lifetime caps"
  - id: WR-06
    severity: warning
    disposition: open
    title: "The spend guard is check-then-act; two concurrent paid calls can exceed the attempt limit and the 5.00 USD cap"
  - id: WR-07
    severity: warning
    disposition: open
    title: "`pc_spike.main` maps only `SpikeError`; the default runs root is macOS-specific and fails with a raw traceback elsewhere"
  - id: WR-08
    severity: warning
    disposition: open
    title: "`run_s2a` writes its two data files one after the other, so a late refusal leaves a half-written pair that blocks the retry"
  - id: WR-09
    severity: warning
    disposition: open
    title: "The user-names-absent assertion passes vacuously when the name list is empty"
  - id: WR-10
    severity: warning
    disposition: open
    title: "`pc_mine.parse_log` cannot read bash `%q` output for arguments with control characters"
  - id: WR-11
    severity: warning
    disposition: open
    title: "The manifest CLI never applies the credential-folder refusal that the module promises"
  - id: IN-01
    severity: info
    disposition: open
    title: "Spend and probe readers validate less than their writers"
  - id: IN-02
    severity: info
    disposition: open
    title: "Wrapper injection numbering assumes the armed count starts at 2"
  - id: IN-03
    severity: info
    disposition: open
    title: "Test hygiene: cleanup is inconsistent with the stated rule, and one assertion is timing-bound"
  - id: IN-04
    severity: info
    disposition: open
    title: "`pc_stream check` does not print what its docstring promises"
  - id: IN-05
    severity: info
    disposition: open
    title: "`int()` over banner digits can raise on Python 3.11 and newer"
  - id: IN-06
    severity: info
    disposition: open
    title: "Config-folder containment in `promote` is case-sensitive on a case-insensitive filesystem"
  - id: IN-07
    severity: info
    disposition: open
    title: "The leak-gate suite has no case for the delimiter and boundary gaps found above"
---

# Phase 02 review disposition

Recorded by execute-phase after the code review returned. Every finding starts as `open`; `/gsd-code-review 02 --fix` or a manual triage updates the rows.
