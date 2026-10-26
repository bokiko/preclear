---
phase: 02-model-free-foundation-and-stub
verified: 2026-10-26T20:00:00Z
status: passed
score: 6/6 must-haves verified
covered_files:
  - ".gitleaks.toml"
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
  - ".planning/phases/02-model-free-foundation-and-stub/02-09-PLAN.md"
  - ".planning/phases/02-model-free-foundation-and-stub/02-09-SUMMARY.md"
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
  - "tests/harness/test_leakgate.py"
  - "tests/harness/test_sanitize.py"
covered_digest: "v3:sha256:29e6b91d2ef710a5a49e7bc2e593a6e92135359930844a030933f6a6320d3aa0"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "The runtime sanitizer and the leak gate stop the login name and home paths in the JSONL stream shape the harness files (CR-01, CR-02; EVID-02, EVID-03)"
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 2: Model-Free Foundation and Stub Verification Report

**Phase Goal:** A stranger with only Claude Code, git and Python 3 can run a zero-token self-test suite that proves the stub helper, run-root allocator, snapshotter, measurer, sanitizer, leak gate and allowlist check, and two spikes have decided the pinned flags and the isolation mode.
**Verified:** 2026-10-26
**Status:** passed
**Re-verification:** Yes, after gap-closure plan 02-09 (commits 32057d0 to b0805b8, merge f06616f)

## Verdict in one paragraph

The one blocker from the first report is closed. I reran the original failing inputs through the harness's own modules with a synthetic login (the real login was never printed or used as input to a printed line): the login after a JSON-escaped newline, tab or return is now replaced and the escape kept; a home path followed by a JSON escape, a bracket, a brace, a pipe, an equals sign, a tilde, an asterisk, a backslash, a quote, a slash, a dot, a space or end of text is now a gate finding for all four home shapes (macOS-style, Linux-style, superuser, Windows-style). The gate refuses the unsanitised text through the sanitizer's login entry and passes the sanitised text. I also reran the full suite myself: through the shim, exit 0 with "0 model calls" and 753 tests OK (3 skipped); directly under the system Python 3.9.6, 753 tests, OK, 3 skipped. The other five truths show no regression. Open warnings WR-03 to WR-14 and info items are real but none breaks the stated goal (a zero-token suite plus decided spikes); they are recorded below as next-phase readiness notes.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria (the contract). Truth 6 is derived from EVID-02, EVID-03 and the review.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Zero-token unittest suite exits 0 with claude absent from PATH; covers stub conformance, sanitizer, leak scan, collision refusal, manifest, preflight, allowlist, measurer; measurer reports per-section and total UTF-8 bytes actual/cap | VERIFIED (regression check) | `tests/harness/selftest`: exit 0, "0 model calls; claude directories removed from PATH: 6", "bash version used for the shim run: 3.2.57", Ran 753 tests, OK (skipped=3). Direct `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` on Python 3.9.6: Ran 753 tests, OK (skipped=3). The count rose from 724 to 753, matching the 29 tests plan 02-09 added; nothing was removed. |
| 2 | Replay of every mined argv sequence reproduces decisive outputs; stub refuses without CKPT_HOME and brands output; branch table lists exits and UNCONFIRMED rows; `references/checkpoint-v1.md` unchanged | VERIFIED (regression check) | `git diff --stat` from the 02-09 plan base to HEAD over everything outside `.planning` touches exactly five files (`.gitleaks.toml`, `pc_leakgate.py`, `pc_sanitize.py`, `test_leakgate.py`, `test_sanitize.py`). `SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/` have an empty diff. The replay, stub, branch-table and frozen-reference tests are inside the 753 that pass. |
| 3 | Conflict injection and call logging come from a wrapper outside the stub; double-conflict replay shows exit 3 twice then success; bind, create, init in no allowlist | VERIFIED (regression check) | `checkpoint-wrapper`, `checkpoint_stub.py` and `pc_allowlist.py` are untouched by 02-09; their tests (wrapper conflict, allowlist) pass in the full run. |
| 4 | Spike findings with real fixtures; one flag table; version gate exit 13; allowlist self-test from committed traces; structured denial signals only | VERIFIED (regression check) | Read-only `pc_spike.py spend`: remaining 4.74 USD, cap 5.00 USD, attempts s1 2 of 2, s2a 1 of 2, s2b 1 of 2, verbose 1 of 2. `probes` lists four probe records, all `loggedIn=true exit=0 created=false`; `auth-check` prints `loggedIn true`. Fixtures under `tests/harness/data/` scan clean (see truth 6). I did not run `claude` and did not run any spike with `--run`. |
| 5 | Run-root creation exclusive and never deleted; sanitizer builds its deny list at run time from the live machine; seeded leak makes gate and promote refuse; stdlib-only imports; bash 3.2 shims | VERIFIED (regression check) | `test_runroot`, `test_promote`, `test_imports` and the shim test pass in the full run; `from_machine` still builds from `machine_sources()` and the local deny file. 02-09 changed only the five files above, none of which adds a deletion or a non-stdlib import (test_imports passes over all modules). |
| 6 | The sanitizer and gate stop the login name and home paths in the JSONL stream shape the harness files | VERIFIED (gap closed) | See the reproduction table below. Code read: `pc_sanitize.py` `_PREFIX["word"] = (?:(?<!\w)|(?<=\\[nrtbf]))`; `Sanitizer.deny_entries()` returns hosts, local entries and login entries (raw, NFC, NFD; skipped when the login sits inside a fixed token or is under four characters). `pc_leakgate.py` `home-path-unix` ends in `(?:[^A-Za-z0-9._-]|$)`, `home-path-windows` the same negated class, `home-path-root` a lookahead; `make_rule` compiles with `re.ASCII`; the host suffix is `(?i:...)`; `.gitleaks.toml` carries byte-identical strings for the two mirrored rules (ParityTests pass). `_git_deny_path` fails closed with `ScannerError` (CLI exit 15); `local_file_entries` decodes `utf-8-sig` and strips padding. New tests: `LoginBoundaryTests`, `LocationFailClosedTests`, `GateIntegrationTests` in `test_sanitize.py`; `HomePathBoundaryTests`, `IdentifierBoundaryTests`, `AsciiAndCaseTests`, `DenyListLocationTests` in `test_leakgate.py`; 31 calls of `assert_fixtures_clean` tie each boundary table to the committed corpus (IN-07). |

**Score:** 6/6 truths verified (0 present but behavior-unverified).

Behavior-dependent truths (the double-conflict transition, exclusive create, the login boundary) each have a named passing test that exercises the transition or boundary, so none is PRESENT_BEHAVIOR_UNVERIFIED.

### Reproduction of the original failing inputs (synthetic login, harness modules)

Run with an injected `Sources` holding the synthetic login `zephyrine` (nine letters, not any real value), through `Sanitizer.from_machine(..., sources=...)`, `sanitize_bytes` and `scan_bytes`. "NAME" stands for the synthetic login in the table.

| Input shape | First report | Now |
|-------------|--------------|-----|
| `{"c":"line1\nNAME\nline3"}` (JSON escape before login) | login kept | replaced by `<user>`, escape kept |
| `{"c":"x\tNAME"}`, `{"c":"a\rNAME"}` | login kept | replaced |
| `{"c":"\\nNAME"}` (escaped backslash then n, ambiguous) | not tested | replaced (over-replacing is the stated safe direction) |
| `xNAMEy`, `wordnNAME` (inside a longer word, plain letter before) | kept | still kept (whole-word rule holds) |
| unsanitised JSON text vs the sanitizer's `deny_entries()` | no finding | one `deny-list` finding; the sanitised text gives none |
| home path then `\n`, `\t`, `\r`, `\"`, `\\` | no finding | one `home-path-unix` finding each |
| home path then `>`, `]`, `}`, `|`, `=`, `~`, `*`, `'`, space, `/`, `.`, end of text | no finding for most | one finding each |
| the Linux-style home folder of the synthetic login, superuser folder and Windows-style folder before `\n`, `>`, `}`, `|` | no finding | one finding each (`home-path-unix`, `home-path-root`, `home-path-windows`) |
| a path ending a JSON string, bare folder words with no name after them | n/a | bare words stay clean |
| a host in upper case or title case under a private suffix | evaded | one `internal-hostname` finding (WR-01) |
| wrong repository root for the deny list | silently dropped | `ScannerError`, fixed message, no path (WR-02) |

### Requirements Coverage

The union of the `requirements` field over the nine plans is exactly HARN-03, HARN-04, HARN-06, HARN-08, HARN-14, STUB-01 to STUB-07, EVID-01, EVID-02, EVID-03, EVID-07: 16 IDs. REQUIREMENTS.md maps exactly those 16 to Phase 2 and marks them Complete; EVID-04 to EVID-06 are Phase 3 and are not claimed. No orphans.

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| HARN-03 | 02-03 | SATISFIED | exclusive allocator, collision exit 16, no deletion primitive in `pc_*.py` |
| HARN-04 | 02-01, 02-08 | SATISFIED | flag table, builder, version gate exit 13, spike-pinned |
| HARN-06 | 02-01, 02-04, 02-08 | SATISFIED | structured denial detection, allowlist self-test on committed traces |
| HARN-08 | 02-03 | SATISFIED | NUL-safe manifest, newline and non-Latin names |
| HARN-14 | 02-07 | SATISFIED | stdlib-only import scan, bash 3.2 shims, Python 3.9.6 run proven |
| STUB-01 | 02-02, 02-06 | SATISFIED | all verbs, exits 0 to 6, lock, atomic write |
| STUB-02 | 02-02, 02-06 | SATISFIED | refuses without CKPT_HOME |
| STUB-03 | 02-02 | SATISFIED | 15 calls replayed against committed outputs |
| STUB-04 | 02-04, 02-06 | SATISFIED | wrapper injection outside the stub; two labelled switches |
| STUB-05 | 02-04 | SATISFIED | branch table with UNCONFIRMED rows; stub banner |
| STUB-06 | 02-04 | SATISFIED | wrapper refusal exit 71, allowlist denies bind, create, init |
| STUB-07 | 02-04 | SATISFIED | empty diff of `references/checkpoint-v1.md` and `SKILL.md` |
| EVID-01 | 02-03 | SATISFIED | measurer on original bytes, heading-inclusive |
| EVID-02 | 02-05, 02-09 | SATISFIED | runtime-built table from the live machine; login after a JSON escape replaced; login handed to the gate |
| EVID-03 | 02-05, 02-09 | SATISFIED | fail-closed gate, promote refusal exit 14; home-path, host and email boundaries closed; deny list location fails closed |
| EVID-07 | 02-01, 02-07 | SATISFIED | suite exits 0 with claude absent from PATH |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/harness/pc_sanitize.py` | runtime-built sanitizer with login boundary and gate entries | VERIFIED | 286 lines; `login_entries` wired into `deny_entries()` |
| `tests/harness/pc_leakgate.py` | fail-closed gate, tightened rules, fail-closed deny list location | VERIFIED | 601 lines; `utf-8-sig`, `_inside_a_repository`, `re.ASCII` present and exercised |
| `.gitleaks.toml` | twin of the two tightened rules | VERIFIED | byte-identical; `sh scripts/test-hooks.sh` prints 29 PASS, 0 FAIL (I ran it) |
| `tests/harness/test_sanitize.py`, `test_leakgate.py` | table-driven boundary tests | VERIFIED | classes listed under truth 6; all pass |
| all other Phase 2 artifacts | unchanged since the first report | VERIFIED | untouched by 02-09 (diff above) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| sanitizer | gate | `deny_entries()` carries the login | WIRED | unsanitised text gives a deny-list finding, sanitised gives none (reproduced) |
| `.gitleaks.toml` | gate rules | ParityTests byte compare | WIRED | passes, and the tightened strings run in the hooks (29 PASS) |
| gate | `from_machine` | `ScannerError` mapped to `SanitizerError` | WIRED | fixed message, no value |
| promote | gate | scan before copy | WIRED | exit 14 on seeded stage (tests) |

### Data-Flow Trace (Level 4)

The one chain that matters (live machine values to the table to replaced text, and the same values to the gate's entries) produced real data in the reproduction: the table replaced the synthetic login, home and escape-adjacent forms, and the gate saw the same values through `deny_entries()`.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Self-test via the shim | `tests/harness/selftest` | exit 0, 0 model calls, 753 OK (skipped=3) | PASS |
| Whole suite, system Python 3.9.6 | `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` | 753 tests OK, skipped=3 | PASS |
| Leak gate over the harness | `python3 tests/harness/pc_leakgate.py scan tests/harness` | 52 files scanned, 0 findings | PASS |
| Original CR-01 shapes | synthetic login through `sanitize_bytes` | replaced | PASS |
| Original CR-02 shapes | `scan_bytes` on home paths before escapes and delimiters | one finding each | PASS |
| Hook suite | `sh scripts/test-hooks.sh` | 29 PASS, 0 FAIL | PASS |
| Full-history secret scan | `gitleaks git . --config .gitleaks.toml --no-banner --redact --exit-code 2 -l warn` | exit 0 | PASS |
| Spend ledger, probes, auth check | `pc_spike.py spend`, `probes`, `auth-check` | 4.74 of 5.00 USD left; all probes loggedIn true; auth true | PASS |

### Probe Execution

No `probe-*.sh` files exist and no plan declares any. SKIPPED.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| the five files changed by 02-09 | n/a | TBD, FIXME, XXX markers | none found | clean |
| `tests/harness/pc_sanitize.py`, `pc_leakgate.py` | n/a | the two first-report blockers (CR-01, CR-02) | resolved | see truth 6 |

### Open review findings weighed against this phase's goal

The second-pass review (02-REVIEW.md) leaves 0 critical, 12 warning and 9 info items open, routed to Phase 3 hardening (02-REVIEW-DISPOSITION.md: 5 fixed, 21 deferred). I weighed each group against the goal of THIS phase (a zero-token suite plus decided spikes), not Phase 3's filing requirements.

| Group | Blocks this phase? | Reasoning |
|-------|--------------------|-----------|
| WR-13 (login matched as substring by the gate, whole word by the sanitizer) | No | The mismatch fails safe. I probed a login after `\u000a` and after a non-ASCII letter: the sanitizer keeps it, and the gate still refuses it when given `deny_entries()` (one `deny-list` finding). A refusal, never a leak. It is a usability and boundary-completeness issue (widen to `\uXXXX` and ANSI colour codes) for Phase 3 hardening. |
| WR-14 (callers must pass `sanitizer.deny_entries()` to promote) | No, readiness note | A Phase 3 runner contract, recorded below. The spike driver's own path already passes the entries. |
| WR-12 (`from_machine` can raise after the paid call; `main` does not map `SanitizerError`) | No | The spikes are finished and spend is 0.26 USD of 5.00 USD. It matters only if a spike is rerun. |
| WR-03 (stub `update` accepts a body holding the end marker) | No | Reachable only by a model quoting the marker; relevant when Phase 3 rows run for real. |
| WR-04 to WR-11, IN-01 to IN-06 | No | Spike-driver robustness, hygiene and reader strictness; no current damage to the suite or the decided spikes. |
| IN-08 (login inside a fixed token has no gate entry), IN-09 (dash-slug rule needs a closing hyphen; names over 64 characters), IN-10 (fixture scan repeated 31 times) | No | Narrow residue or test economy; the owner's own slug is covered by the sanitizer. |

Residual shapes I observed that are worth Phase 3 attention, none a goal blocker: the sanitizer keeps the login after a `\uXXXX` escape or next to a non-ASCII letter (the gate is the only net there, and only when it is handed the sanitizer's entries).

### Next-phase readiness notes

- **WR-14 runner contract (Phase 3):** after sanitising a run, the runner must pass `sanitizer.deny_entries()` to `pc_promote.promote`. `promote` with default entries and the gate CLI do not hold the login (by design, because the login is also the owner's public alias and appears in committed prose). A Phase 3 test should fail when a sanitised run is promoted without those entries.
- Build the sanitizer before any paid call and map `SanitizerError` in `pc_spike.main` (WR-12) before any spike is rerun on a new Claude Code build.
- Consider fixing WR-03 (stub end-marker corruption) before row runs, so a skill-looking failure cannot be a stub artifact.

### Deferred Items

Not applicable. The open warnings are routed by bokiko's workflow to Phase 3 hardening; none is a failed must-have of this phase, so none is listed as a gap or as a roadmap-matched deferral.

### Human Verification Required

None.

### Gaps Summary

No gaps. The first report's single gap (truth 6, EVID-02 and EVID-03 PARTIAL) is closed with code, tests and a rerun of the original failing inputs. Phase 2 delivers its goal: the zero-token suite runs and passes (753 tests on Python 3.9.6 and through the bash 3.2 shim), the stub, wrapper, run-root allocator, manifest, measurer, sanitizer, leak gate, promote and allowlist check are proven by it, and both spikes decided the pinned flags and the strict isolation mode within budget.

---

_Verified: 2026-10-26_
_Verifier: Claude (gsd-verifier)_
