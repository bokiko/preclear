---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Sanitizer leaves the login name in place when a JSON escape precedes it, and the gate cannot catch it"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "Leak gate misses a home path that is followed by a JSON escape, a bracket or a quote-like delimiter"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Gate identifier rules can be evaded with non-ASCII neighbours or an upper-case host suffix"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "A git failure or a missing deny file silently drops the private deny list (fail-open), and the file parser mishandles BOM and padding"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Stub `update` accepts a body that holds the checkpoint end marker and corrupts the ledger for good"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "The stub deletes and overwrites files, outside the project's no-delete rule, and the static scan cannot see it"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "`run_s1` has no pre-paid existence check for its output, and the README's rerun advice conflicts with the lifetime caps"
  - id: WR-06
    severity: warning
    disposition: deferred
    title: "The spend guard is check-then-act; two concurrent paid calls can exceed the attempt limit and the 5.00 USD cap"
  - id: WR-07
    severity: warning
    disposition: deferred
    title: "`pc_spike.main` maps only `SpikeError`; the default runs root is macOS-specific and fails with a raw traceback elsewhere"
  - id: WR-08
    severity: warning
    disposition: deferred
    title: "`run_s2a` writes its two data files one after the other, so a late refusal leaves a half-written pair that blocks the retry"
  - id: WR-09
    severity: warning
    disposition: deferred
    title: "The user-names-absent assertion passes vacuously when the name list is empty"
  - id: WR-10
    severity: warning
    disposition: deferred
    title: "`pc_mine.parse_log` cannot read bash `%q` output for arguments with control characters"
  - id: WR-11
    severity: warning
    disposition: deferred
    title: "The manifest CLI never applies the credential-folder refusal that the module promises"
  - id: WR-12
    severity: warning
    disposition: deferred
    title: "`Sanitizer.from_machine` can now raise after the paid call, and `main` does not map `SanitizerError`"
  - id: WR-13
    severity: warning
    disposition: deferred
    title: "The gate matches the login as a case-insensitive substring, the sanitizer as a whole word, so residue is refused and some captures can never be written"
  - id: WR-14
    severity: warning
    disposition: deferred
    title: "The login reaches the gate only if the caller passes `sanitizer.deny_entries()`; `promote` and the gate CLI silently use the weaker default"
  - id: IN-07
    severity: info
    disposition: fixed
    title: "The leak-gate suite has no case for the delimiter and boundary gaps found above"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Spend and probe readers validate less than their writers"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "Wrapper injection numbering assumes the armed count starts at 2"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "Test hygiene: cleanup is inconsistent with the stated rule, and one assertion is timing-bound"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "`pc_stream check` does not print what its docstring promises"
  - id: IN-05
    severity: info
    disposition: deferred
    title: "`int()` over banner digits can raise on Python 3.11 and newer"
  - id: IN-06
    severity: info
    disposition: deferred
    title: "Config-folder containment in `promote` is case-sensitive on a case-insensitive filesystem"
  - id: IN-08
    severity: info
    disposition: deferred
    title: "A login that is a substring of a fixed token gets no gate entry"
  - id: IN-09
    severity: info
    disposition: deferred
    title: "`home-path-dash-slug` still needs a closing hyphen, and the folder-name length cap still hides long names"
  - id: IN-10
    severity: info
    disposition: deferred
    title: "The fixture-scan helper repeats 31 times per run and some calls assert nothing about the case under test"
---

# Phase 02 review disposition

Second pass after gap-closure plan 02-09. CR-01, CR-02, WR-01, WR-02 and IN-07 are `fixed` by 02-09 (commits 32057d0..b0805b8). Every other warning and info item is `deferred` to Phase 3 hardening by bokiko's workflow routing; WR-12 to WR-14 and IN-08 to IN-10 were raised by the second pass against the gap-closure diff and are deferred the same way. No critical finding is open.
