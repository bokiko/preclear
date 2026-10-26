---
phase: 02-model-free-foundation-and-stub
verified: 2026-10-26T14:00:00Z
status: gaps_found
score: 5/6 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/ROADMAP.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-01-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-01-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-02-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-02-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-03-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-03-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-04-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-04-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-05-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-05-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-06-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-06-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-07-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-07-SUMMARY.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-08-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-08-SUMMARY.md"
  - "tests/harness/README.md"
  - "tests/harness/checkpoint-wrapper"
  - "tests/harness/checkpoint_stub.py"
  - "tests/harness/data/branch-table.md"
  - "tests/harness/data/spike-findings.md"
  - "tests/harness/pc_allowlist.py"
  - "tests/harness/pc_flags.py"
  - "tests/harness/pc_leakgate.py"
  - "tests/harness/pc_manifest.py"
  - "tests/harness/pc_measure.py"
  - "tests/harness/pc_promote.py"
  - "tests/harness/pc_runroot.py"
  - "tests/harness/pc_sanitize.py"
  - "tests/harness/pc_spike.py"
  - "tests/harness/pc_stream.py"
  - "tests/harness/replay-cases.json"
  - "tests/harness/selftest"
covered_digest: "v3:sha256:6901a049f15b68adc470ea1e41ce8bcf96b4cf3f20c4b23dbd058c63f9ed9320"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "The runtime sanitizer and the leak gate stop the identifiers EVID-02 and EVID-03 name (login name, home path) in the JSONL stream shape the harness exists to file, so a stranger's real run cannot reach tests/evidence/ with them still in place"
    status: failed
    reason: "Two reproduced evasions (review findings CR-01 and CR-02, both still open in the disposition file). The sanitizer keeps the login name when a JSON escape (a backslash plus n or t) directly precedes it, and the gate has no rule for the login, so nothing catches what is left. The gate's home-path rule does not fire when the path is followed by a JSON escape, a closing bracket or brace, a pipe, an equals sign, a tilde, an asterisk or a backslash. The same hole is mirrored in the commit-hook rule, so the Phase 1 net is open too. No test places an identifier next to such a boundary."
    artifacts:
      - path: "tests/harness/pc_sanitize.py"
        issue: "word-kind entries use a (?<!\\w) lookbehind, so a login after an escaped newline or tab is kept; Sanitizer.deny_entries() carries no login, so the gate cannot catch it"
      - path: "tests/harness/pc_leakgate.py"
        issue: "home-path-unix, home-path-dash-slug and the Python-only home rules list their closing delimiters instead of requiring 'not a name character', so a path before a JSON escape passes"
      - path: ".gitleaks.toml"
        issue: "parity copy of the same delimiter list (the parity test freezes the gap in both places)"
      - path: "tests/harness/test_leakgate.py"
        issue: "no boundary cases (finding IN-07)"
      - path: "tests/harness/test_sanitize.py"
        issue: "no case with the login after an escaped newline or tab"
    missing:
      - "Treat a JSON escape as a boundary in the sanitizer's word match, or make the login a substring entry, and add the login to the entries the gate refuses (CR-01 fix)"
      - "Replace the delimiter list in the gate's home-path rules and in .gitleaks.toml with a 'not followed by a name character' check (CR-02 fix), keeping the parity test green"
      - "Table-driven boundary tests (JSON escapes, brackets, non-ASCII neighbours, case) for the identifier rules and for the sanitizer's login handling (IN-07)"
      - "Strongly advised in the same closure, not required for this gap: WR-01 (ASCII flag and case-insensitive host suffix) and WR-02 (a git failure or a missing deny file silently drops the private deny list)"
human_verification: []
---

# Phase 2: Model-Free Foundation and Stub Verification Report

**Phase Goal:** A stranger with only Claude Code, git and Python 3 can run a zero-token self-test suite that proves the stub helper, run-root allocator, snapshotter, measurer, sanitizer, leak gate and allowlist check, and two spikes have decided the pinned flags and the isolation mode.
**Verified:** 2026-10-26
**Status:** gaps_found
**Re-verification:** No, initial verification

## Verdict in one paragraph

The phase is delivered and works. I ran the suite myself: through the bash entry shim it exits 0, and run directly under the system Python 3.9.6 it reports 724 tests, OK, 3 skipped (the three skips are filesystem-capability skips on macOS: case-insensitive names, NFC and NFD folding, non-UTF-8 names; each has an in-memory twin that runs). Every roadmap success criterion holds as written. One thing keeps the status from `passed`: the review's two critical findings are real, I reproduced both with the harness's own modules, and they sit in the privacy layer (EVID-02 and EVID-03) that Phase 3 relies on for "every filed file passed the leak gate". I judge them a small, well-specified fix that belongs before Phase 3 files real evidence, not a Phase 3 item that can wait, because no later phase's roadmap text covers them.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria (the contract). Truth 6 is derived from requirements EVID-02 and EVID-03 and from the review.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The unittest suite under tests/harness exits 0 with zero model calls while claude is absent from PATH; covers stub conformance, sanitizer, leak scan, collision refusal, newline and non-Latin manifest, preflight, allowlist, measurer; measurer reports per-section and total UTF-8 bytes as actual/cap and matches multibyte fixtures | VERIFIED | `tests/harness/selftest` exit 0 and printed "0 model calls; claude directories removed from PATH: 6" (claude is installed on this machine and the shim removed it). Direct `unittest discover`: 724 run, OK, 3 skipped. test_measure has 2-byte, 3-byte CJK, 4-byte emoji, CRLF, non-ASCII heading, 4096/4097 cap, and a test tying the cap constants to SKILL.md. test_manifest and test_selftest_shim exist and pass. |
| 2 | Replaying every argv sequence mined from the committed wrapper-calls.log files against the stub reproduces the decisive outputs; stub exits non-zero without CKPT_HOME and brands output; branch table lists exits 0 to 6 and marks handoff, note, exit 5, exit 6 UNCONFIRMED; references/checkpoint-v1.md unchanged, stub docs under tests/ only | VERIFIED | replay-cases.json inventory: 9 logs, 5 non-empty, 4 empty, 15 calls; I counted the committed logs and the per-case calls sum to 15 (1+6+4+3+1). I ran the stub with CKPT_HOME unset: exit 64 and a message. Every stub line starts with the STUB-BACKED banner and `--version` carries a stub banner. branch-table.md has rows for exits 1 to 6 and UNCONFIRMED rows for handoff, note, exit 5, exit 6. `git diff` of references/checkpoint-v1.md and SKILL.md across the phase's commits is empty, and test_frozen_reference.py passes. Stub documentation is in tests/harness/ only. |
| 3 | Conflict injection and call logging come from a wrapper outside the stub; a double-conflict replay of row 2 shows exit 3 twice then success after a manual merge; bind, create and init are in no model-facing allowlist | VERIFIED | test_wrapper_conflict asserts the exit sequence 0,0,0,3,0,3,0,0 plus lint OK, the hand-merged third update landing in the ledger, and that the stub names no log, no injection and at most the two labelled switch variables. The wrapper refuses driver verbs with exit 71 directly, through env and behind a leading session option. test_allowlist asserts bind, create and init are denied and that the builder never adds them. The live S2 probe also shows the real binary denying a wrapper bind (is_error true, permission_denied event and permission_denials entry with the same tool_use id). |
| 4 | Spike findings committed with a real stream-json fixture; one flag table pins every claude -p behaviour; version gate refuses an untested version with a distinct exit code; allowlist self-test matches the skill's exact commands from committed traces; a synthetic permission_denied event or permission_denials entry fails a row and the word "denied" in a reply does not | VERIFIED | tests/harness/data/spike-findings.md, s1-init-manifest.json, s2-stream.jsonl and s2b-stream.jsonl are committed. The fixtures are real captures: init event with version 2.1.310, model claude-sonnet-5-5, permissionMode default; S2a holds 10 assistant events, 7 user events, a permission_denied system event and a result. Flag table lives in pc_flags.py and is mirrored in the README (test_readme ties them). TESTED_VERSIONS is exactly the one recorded build; untested maps to exit 13 (test_untested_version_is_13, test_empty_tested_set_refuses_every_real_version). test_stream covers the structured denial signals, `test_the_words_denied_and_refused_are_never_a_signal`, and that no code searches text for denial words. test_allowlist derives its set from the committed traces. Spend: 0.26 USD of the 5.00 USD cap (I ran the read-only `spend` verb; 10 ledger lines, remaining 4.74 USD). |
| 5 | Run-root creation is exclusive and nothing deletes or overwrites a run root; sanitizer builds its deny-list at run time from the live machine; a seeded leak makes the gate and promote refuse to copy into tests/evidence/; harness imports are standard library only; bash entry shims run under bash 3.2 | VERIFIED | test_runroot: second allocation of the same name raises a collision (CLI exit 16), including symlink, dangling symlink and file-in-the-way cases. Static scan of pc_*.py finds no rmtree, os.remove or unlink. The only deletions anywhere are the stub's own `.ckpt-*` temporary-file cleanups inside CKPT_HOME (see WR-04 in warnings). Sanitizer sources come from `machine_sources()` (HOME, account home, login, hostnames, temp dirs) plus the local deny file. test_promote: a seeded stage is refused with exit 14 and nothing is created; a clean stage is copied byte for byte. test_imports scans every module for standard-library-only imports and for 3.10-only syntax. The shim test run printed "bash version used for the shim run: 3.2.57". |
| 6 | (Derived from EVID-02, EVID-03) The sanitizer and gate stop the login name and home paths in the JSONL stream shape the harness files | FAILED | CR-01 reproduced: with a synthetic login, `{"c":"line1\nNAME\nline3"}` and `{"c":"x\tNAME"}` pass through `sanitize_bytes` unchanged, while `owner NAME staff` becomes `owner <user> staff`. CR-02 reproduced: `scan_bytes` returns no finding for a home path followed by a JSON-escaped newline, a JSON-escaped quote or a `>`, and one finding for the same path followed by `/` or `.`. No test covers these boundaries. |

**Score:** 5/6 truths verified (0 present but behavior-unverified).

Behavior-dependent truths (the double-conflict state transition in truth 3, the exclusive create in truth 5) each have a named passing test that exercises the transition, so none is left PRESENT_BEHAVIOR_UNVERIFIED.

### Weighing the open critical findings

| Finding | Reproduced here | Blocks the phase goal? | Reasoning |
|---------|-----------------|------------------------|-----------|
| CR-01 sanitizer keeps login after a JSON escape | Yes | Yes, as a gap | The login is one of the identifiers EVID-02 lists, the harness files JSONL, and the gate has no login entry, so there is no second net. Impact on this machine is nil today because the login is the public alias, and the committed fixtures are clean, but a stranger's run is exactly the stated audience. |
| CR-02 gate home-path rule misses escape and bracket delimiters | Yes | Yes, as a gap | The gate is documented as the only defence for a home folder the sanitizer does not know. The sanitizer does handle the live machine's own home before the gate (I checked: a home followed by an escaped newline becomes `<home>` plus the escape), which narrows the exposure to foreign or unknown paths. Phase 3 success criterion 1 states "every filed file passed the leak gate", which leans on this rule, and Phase 3 does not list the fix anywhere, so it is not a deferred item. |

The fix is small and written out in the review. I recommend a short gap-closure plan (CR-01, CR-02, IN-07 boundary tests, ideally with WR-01 and WR-02) before Phase 3 starts. If bokiko prefers to take the risk and fold it into Phase 3 planning as an explicit first task, that is a defensible human call, and an `overrides:` entry would record it; I have not applied one.

### Deferred Items

None. No later phase in the roadmap names this work.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| tests/harness/selftest | bash 3.2 shim, claude-free PATH, tripwire safe | VERIFIED | ran it; exit 0; removes 6 claude directories and prints the count |
| tests/harness/checkpoint_stub.py | single-file checkpoint-v1 stub | VERIFIED | 968 lines, no sibling imports (test_imports), CKPT_HOME refusal exit 64, banner |
| tests/harness/checkpoint-wrapper | logging and conflict injection outside the stub; refuses bind, create, init | VERIFIED | exit 70 and 71 paths tested |
| tests/harness/pc_runroot.py | exclusive allocator | VERIFIED | collision exit 16 |
| tests/harness/pc_manifest.py | NUL-safe, newline and non-Latin names | VERIFIED with caveat | WR-11: the CLI never passes the credential-folder refusal (warning) |
| tests/harness/pc_measure.py | heading-inclusive bytes, actual/cap | VERIFIED | multibyte fixtures pass |
| tests/harness/pc_sanitize.py | runtime-built sanitizer, lower-case tokens | PARTIAL | works for the common case, fails CR-01 |
| tests/harness/pc_leakgate.py | fail-closed gate with gitleaks parity | PARTIAL | runs, 0 findings over tests/harness (52 files); fails CR-02 and WR-01, WR-02 |
| tests/harness/pc_promote.py | refuses on any finding or scanner error | VERIFIED | exit 14 and 17 paths tested |
| tests/harness/pc_allowlist.py | matcher and builder | VERIFIED | 3 binding rules, never adds bind, create, init |
| tests/harness/pc_flags.py, pc_preflight.py, pc_stream.py, pc_exitcodes.py | flag table, version gate, denial parser, distinct exit codes | VERIFIED | HARN-04 pinned set including DISABLE_AUTOUPDATER=1 in the built environment |
| tests/harness/pc_spike.py and data/ | spike driver, findings, fixtures | VERIFIED | findings, 2 fixtures, init manifest, probe labels committed |
| tests/harness/README.md, data/branch-table.md | stranger guide; branch table | VERIFIED | test_readme and test_branch_table tie them to the code |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| selftest shim | unittest discover over tests/harness | exec after PATH scrub | WIRED | ran |
| wrapper | stub | argv pass-through, injection files outside the stub | WIRED | wrapper and direct stub outputs identical once the scratch root is normalised (tested) |
| replay-cases.json | committed wrapper-calls.log files | pc_mine | WIRED | 15 calls |
| promote | leak gate | scan before copy, fail closed | WIRED | exit 14 on seeded stage |
| sanitizer | gate | deny_entries | PARTIAL | hosts and local file only; login absent (CR-01) |
| pc_spike | pc_stream, pc_flags, pc_hooklog | S1 assertions and S2 probe table | WIRED | real fixtures produced through it |
| leak gate rules | .gitleaks.toml | parity test | WIRED | parity holds, which also freezes the CR-02 gap |

### Data-Flow Trace (Level 4)

Not applicable in the UI sense. The one data chain that matters, captured stream to sanitized fixture to committed file, produced real data: the committed streams carry real events, and the lower-case placeholder tokens appear in the fixtures; the live login, hostname and home path do not (counted by fixed-string search, 0 files for hostname and home, and the only login hits are the public alias in prose).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Self-test via the shim | `tests/harness/selftest` | exit 0, 0 model calls | PASS |
| Whole suite, system Python 3.9.6 | `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | 724 tests, OK, skipped=3 (run twice) | PASS |
| Stub refuses without CKPT_HOME | `checkpoint_stub.py status` with the variable unset | exit 64 | PASS |
| Python leak gate over the harness | `pc_leakgate.py scan tests/harness` | 52 files, 0 findings | PASS |
| Gate boundary | `scan_bytes` with a home path before a JSON escape | no finding | FAIL (CR-02) |
| Sanitizer boundary | `sanitize_bytes` with the login after an escaped newline | unchanged | FAIL (CR-01) |
| Spend ledger | `pc_spike.py spend` | 0.26 USD of 5.00 USD, remaining 4.74 | PASS |
| Login probe record | `pc_spike.py probes`, `auth-check` | first probe loggedIn false exit 12, later probes loggedIn true; auth-check true | PASS |
| Phase 1 regression | `bash scripts/test-hooks.sh` | all PASS, including real-origin-refs-unchanged | PASS |

I did not run `claude` and did not run any spike with `--run`.

### Probe Execution

No `probe-*.sh` files exist and the plans declare none. SKIPPED.

### Requirements Coverage

All 16 Phase 2 IDs appear in a plan's `requirements` field (union of the eight plans), and REQUIREMENTS.md maps exactly 16 IDs to Phase 2. No orphans.

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| HARN-03 | 02-03 | SATISFIED | exclusive allocator, no deletion primitive in pc_*.py; stub temp-file cleanup is inside CKPT_HOME only |
| HARN-04 | 02-01, 02-08 | SATISFIED | flag table, builder, env scrub, version gate exit 13, flags marked by spike |
| HARN-06 | 02-01, 02-04, 02-08 | SATISFIED | structured denial detection, allowlist self-test on committed traces |
| HARN-08 | 02-03 | SATISFIED | NUL-safe manifest with newline and non-Latin names |
| HARN-14 | 02-07 | SATISFIED | import scan, bash 3.2 shims, Python 3.9 floor proven by running on 3.9.6 |
| STUB-01 | 02-02, 02-06 | SATISFIED | all verbs, exits 0 to 6, lock and atomic write (WR-03 is a robustness warning) |
| STUB-02 | 02-02, 02-06 | SATISFIED | exit 64 without CKPT_HOME, containment tests |
| STUB-03 | 02-02 | SATISFIED | 15 calls replayed against committed outputs |
| STUB-04 | 02-04, 02-06 | SATISFIED | wrapper injection; only the two labelled CKPT_STUB_ switches |
| STUB-05 | 02-04 | SATISFIED | branch table, banner |
| STUB-06 | 02-04 | SATISFIED | refusal exit 71 plus matcher plus one live denial in the real binary |
| STUB-07 | 02-04 | SATISFIED | frozen reference digest test; no diff |
| EVID-01 | 02-03 | SATISFIED | measurer on original bytes |
| EVID-02 | 02-05 | PARTIAL | live-machine deny list is built at run time as required; the login handling fails CR-01 on JSON streams |
| EVID-03 | 02-05 | PARTIAL | fail-closed promote works on the covered cases; the gate misses CR-02 shapes |
| EVID-07 | 02-01, 02-07 | SATISFIED | suite exits 0 with claude absent from PATH |

### Context decisions D-01 to D-16

D-01, D-02, D-03 honoured: strict isolation chosen, one manual login into a harness-owned config dir, the harness only reads a yes-or-no from `auth status`. Spike S1 originally failed three assertions on attempt 1; bokiko's dated 2026-10-26 decision moved run roots outside every home folder (a real isolation finding: ancestor instruction files load as Project instructions) and refined two assertions (built-in plugins, binary-defined name collisions). The rerun passed nine of nine and no by-construction label is used. D-04 honoured (0.26 USD of 5.00 USD, at most two attempts per call). D-05 honoured (full model id pinned; recorded `init.model`). D-06 to D-09 reflected in the branch table, `CKPT_STUB_` switches and banner. D-10 to D-13 honoured (shim, Python 3.9 floor, flat directory, zero-model suite). D-14 to D-16: Python gate with parity test, lower-case tokens, fail-closed promote that prints counts only. The gaps above are about the strength of D-14 and D-15, not their presence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| tests/harness (all files) | n/a | TBD, FIXME, XXX markers | none found | clean |
| tests/harness/pc_sanitize.py | 60 | word lookbehind treats a JSON escape letter as a word character | Blocker (CR-01) | login survives |
| tests/harness/pc_leakgate.py | 84, 85, 129, 130 | closing-delimiter list instead of negative lookahead | Blocker (CR-02) | path before an escape passes |

### Warnings (open review findings, not blocking this phase)

I did not reproduce each of these; I read the cited code for WR-04 and confirmed the two deletions are the stub's own `.ckpt-*` temporary-file cleanups. The rest are taken from the review.

- WR-01 (non-ASCII neighbours and upper-case host suffix evade the gate) and WR-02 (a git failure or a missing deny file silently drops the private deny list, so the gate fails open): both belong in the same closure as CR-01 and CR-02.
- WR-03: stub `update` accepts a body holding the checkpoint end marker and corrupts its own ledger permanently. Only reachable by a model quoting the marker; fix before Phase 3 rows run for real, since a skill-looking failure could be a stub artifact.
- WR-04: `checkpoint_stub.py` is outside the no-delete static scan, which globs only `pc_*.py`. Hygiene, no run root is touched.
- WR-05 to WR-09: spike driver robustness (no pre-paid output check in `run_s1`, check-then-act spend guard, macOS-only default runs root with a raw traceback elsewhere, half-written S2a pair, vacuous user-names assertion when the name list is empty). The spikes are finished; these matter only if a spike is rerun on a new Claude Code build, and the README's rerun advice currently conflicts with the lifetime caps (WR-05).
- WR-10 (`pc_mine` cannot read bash `$'...'` quoting), WR-11 (manifest CLI never applies the credential-folder refusal), IN-01 to IN-07: no current damage; IN-07 is part of the gap closure.

### Human Verification Required

None. The remaining decision (close CR-01 and CR-02 now, or accept them into Phase 3) is a scheduling choice for bokiko, recorded in the gaps and in the weighing table above.

### Gaps Summary

One gap, one root concern: the privacy layer's identifier matching is anchored on character lists and word characters that do not understand JSON escapes. Everything else in the phase goal is delivered and independently re-run: the zero-token suite, the stub and its replay, the wrapper, the run-root allocator, the manifest, the measurer, the allowlist check, the flag table and version gate, and both spikes with real captured fixtures within budget. The closure plan is small: change two regexes (the gate and its gitleaks twin), change one lookbehind and one deny-entry list, and add boundary tests.

---

_Verified: 2026-10-26_
_Verifier: Claude (gsd-verifier)_
