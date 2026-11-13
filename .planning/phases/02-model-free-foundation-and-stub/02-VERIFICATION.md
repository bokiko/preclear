---
phase: 02-model-free-foundation-and-stub
verified: 2026-11-13T09:00:00Z
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
  - "tests/harness/pc_exitcodes.py"
  - "tests/harness/pc_flags.py"
  - "tests/harness/pc_leakgate.py"
  - "tests/harness/pc_manifest.py"
  - "tests/harness/pc_measure.py"
  - "tests/harness/pc_preflight.py"
  - "tests/harness/pc_promote.py"
  - "tests/harness/pc_runroot.py"
  - "tests/harness/pc_sanitize.py"
  - "tests/harness/pc_spike.py"
  - "tests/harness/pc_stream.py"
  - "tests/harness/replay-cases.json"
  - "tests/harness/selftest"
  - "tests/harness/test_allowlist.py"
  - "tests/harness/test_bash_shims.py"
  - "tests/harness/test_leakgate.py"
  - "tests/harness/test_manifest.py"
  - "tests/harness/test_promote.py"
  - "tests/harness/test_sanitize.py"
  - "tests/harness/test_stub_cli.py"
covered_digest: "v3:sha256:23b31b96f798386c2a93526c6dd424c19e67775f09547a8b926a6fea489b82d3"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 6/6
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 2: Model-Free Foundation and Stub Verification Report

**Phase Goal:** A stranger with only Claude Code, git and Python 3 can run a zero-token self-test suite that proves the stub helper, run-root allocator, snapshotter, measurer, sanitizer, leak gate and allowlist check, and two spikes have decided the pinned flags and the isolation mode.
**Verified:** 2026-11-13
**Status:** passed
**Re-verification:** Yes. The report of 2026-10-26 went stale because Phases 3 and 4 changed covered files. This pass re-checks the goal on the current tree. It is read-only: I did not run the unittest suite or the self-test, and I started no model call.

## Verdict in one paragraph

The phase goal still holds. Between the last Phase 2 commit and HEAD, Phases 3 and 4 touched seven covered files. I read every hunk. Each one is additive, and none weakens a Phase 2 guarantee. The sanitizer, leak gate, run-root allocator, measurer, stream reader, spike driver, wrapper, self-test shim, replay cases, spike findings and the gitleaks config have an empty diff. The frozen skill, reference, fixture and publication evidence paths also have an empty diff. The leak gate scans the harness folder at 0 findings, and the spend ledger is unchanged at 0.26 USD of 5.00 USD. The suite itself was last run green by the orchestrator on 2026-11-12 (2405 tests OK, 3 skipped, 0 model calls); I did not rerun it, as instructed, and I checked the Phase 2 behaviours by reading code and by read-only one-liners instead.

## Goal Achievement

### Observable Truths

Truths 1 to 5 are the roadmap success criteria. Truth 6 was derived in the first verification from EVID-02, EVID-03 and the review.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Zero-token unittest suite exits 0 with `claude` absent from PATH; covers stub, sanitizer, leak scan, collision refusal, manifest, preflight, allowlist, measurer; measurer reports per-section and total UTF-8 bytes | VERIFIED | The self-test shim is byte-identical to the verified version: it drops every PATH entry holding `claude`, refuses to start if `claude` is still resolvable, and runs unittest discovery. All Phase 2 test modules are still present (measure, runroot, manifest, preflight, allowlist, sanitize, leakgate, stub replay and CLI, wrapper conflict, imports, shim). The orchestrator's last green run is 2405 tests OK, 3 skipped, 0 model calls (2026-11-12). Read-only check: the measurer returned 22 total bytes for a heading plus a multibyte line, which matches the hand count. |
| 2 | Replay of every mined argv sequence reproduces decisive outputs; stub refuses without CKPT_HOME and brands output; branch table lists exits and UNCONFIRMED rows; `references/checkpoint-v1.md` unchanged | VERIFIED | Run read-only: the stub with no CKPT_HOME prints the STUB-BACKED banner, says CKPT_HOME is not set, and exits 64. The replay cases file is unchanged. The one stub change since the last verification refuses an `update` body that holds a line equal to the end marker or a begin marker (exit 4, ledger untouched). It sits after the existing heading-line refusal and does not alter any replayed argv. The branch table gained exactly one row for it, marked STUB-ONLY, and its UNCONFIRMED rows for exit 5, exit 6 and the note and handoff verbs are intact. The diff of `SKILL.md`, `references/` and `tests/fixtures/` is empty. |
| 3 | Conflict injection and call logging come from a wrapper outside the stub; double-conflict replay shows exit 3 twice then success; bind, create, init in no allowlist | VERIFIED | `checkpoint-wrapper` is unchanged. `pc_allowlist.py` changes are additive: a splitter that also returns each part's separator (the old splitter is now defined from it, so there is still one splitter), and a corpus folder pin so a later rerun folder cannot change the measured corpus. The profile builder added to `pc_flags.py` builds the helper profile from the same model-facing verb tuple as before, and the plain and git profiles take no wrapper rule at all. No profile gains a rule for bind, create or init. |
| 4 | Spike findings with real fixtures; one flag table; version gate exit 13; allowlist self-test from committed traces; structured denial signals only | VERIFIED | Spike findings, spike driver, stream reader and the committed stream fixtures are unchanged. Read-only: the version check on an untested version returns UNTESTED, the exit constant is 13, and the flag table still renders (36 lines). The tested-version tuple is still the single pinned build. The spend command reports 0.26 USD over 10 calls, 4.74 USD remaining, attempts s1 2 of 2, s2a 1 of 2, s2b 1 of 2, verbose 1 of 2. `pc_flags.py` only gained a second budget ceiling (25.00 for a driver invocation) beside the unchanged 5.00 per-call ceiling, a row profile builder, and a memory switch on the settings builder. |
| 5 | Run-root creation exclusive and never deleted; sanitizer builds its deny list at run time from the live machine; seeded leak makes gate and promote refuse; stdlib-only imports; bash 3.2 shims | VERIFIED | Run-root: a second exclusive create of the same path raises an error (read-only check in a scratch folder). A grep of every `pc_*.py` and the stub for removal primitives finds only the stub's own temp-file cleanup and two test-helper operations in `pc_testutil.py`; the static scan in `test_runroot.py` that forbids them is still in place. Imports are stdlib or sibling modules (the import hygiene test is still present). The sanitizer and gate are unchanged. `pc_promote.py` is stricter than before: `promote` now raises unless the caller passes deny entries or opts in explicitly (review WR-03 follow-up), and the new `promote_into` adds files to an existing evidence folder only after every name and every byte has passed the gate, creating nothing on refusal. The command line path opts in explicitly and says why. The shim list in the shim test now includes the git wrapper, and `selftest` is unchanged and bash 3.2 only. |
| 6 | The sanitizer and gate stop the login name and home paths in the JSONL stream shape the harness files | VERIFIED | Both modules and the gitleaks config have an empty diff since the gap-closure plan. Read-only: the gate returns one `home-path-unix` finding for a home path followed by a space and for a home path followed by an escaped newline, and none for clean text. The leak gate over the harness folder scans 93 files with 0 findings. |

**Score:** 6/6 truths verified (0 present but behavior-unverified).

No truth rests on presence alone. The double-conflict, exclusive create and login-boundary behaviours each have a named test in the suite, and the single read-only behavioural checks above reproduce the gate and run-root outcomes directly.

### Changes since the last verification, hunk by hunk

| File | Change | Weakens Phase 2? |
|------|--------|------------------|
| `checkpoint_stub.py` | Refuses `update` bodies that hold a checkpoint marker line (WR-03) | No. Stricter, and the branch table records it as STUB-ONLY. |
| `data/branch-table.md` | One added row for that refusal | No. |
| `pc_allowlist.py` | Splitter returns separators; corpus pinned to the publication folder | No. The corpus pin keeps the Phase 2 counts stable as new evidence folders are filed. |
| `pc_flags.py` | Invocation budget ceiling, row profile builder, memory switch | No. The per-call 5.00 ceiling and the single-pin version gate are unchanged. |
| `pc_manifest.py` | Hardened git calls, setup pin, nested repository refusal, linked worktree and no-git states | No. The manifest format, NUL and non-Latin handling, and the `refuse_under` guard are unchanged. |
| `pc_promote.py` | Mandatory deny entries on `promote`; new `promote_into` | No. Stricter. |
| `tests/harness/README.md` | Large additions for Phase 3 and 4 sections | No. Documentation. |

### Requirements Coverage

The union of the `requirements` field over the nine plans is exactly the 16 IDs in the phase brief. REQUIREMENTS.md maps exactly those 16 to Phase 2 and marks each Complete. No ID is orphaned and none is missing from a plan.

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| HARN-03 | 02-03 | SATISFIED | Exclusive allocator; no deletion primitive in any harness module; the scan test is present. |
| HARN-04 | 02-01, 02-08 | SATISFIED | One flag table, builder, version gate exit 13, spike-pinned. |
| HARN-06 | 02-01, 02-04, 02-08 | SATISFIED | Structured denial detection and allowlist self-test on committed traces; corpus pinned. |
| HARN-08 | 02-03 | SATISFIED | NUL-safe manifest; a newline name and a non-Latin name both listed (read-only check). |
| HARN-14 | 02-07 | SATISFIED | Stdlib-only imports, bash 3.2 shims, Python 3.9 floor; the shim itself checks for Python 3.9 or newer. |
| STUB-01 | 02-02, 02-06 | SATISFIED | All verbs and exits; atomic write and lock unchanged. |
| STUB-02 | 02-02, 02-06 | SATISFIED | Refuses without CKPT_HOME, exit 64 (run read-only). |
| STUB-03 | 02-02 | SATISFIED | Replay cases unchanged; the stub change does not touch a replayed path. |
| STUB-04 | 02-04, 02-06 | SATISFIED | Injection lives in the unchanged wrapper outside the stub. |
| STUB-05 | 02-04 | SATISFIED | Branch table with UNCONFIRMED rows; stub banner printed. |
| STUB-06 | 02-04 | SATISFIED | No profile has a rule for bind, create or init. |
| STUB-07 | 02-04 | SATISFIED | Empty diff of `references/` and `SKILL.md`; stub documentation under `tests/` only. |
| EVID-01 | 02-03 | SATISFIED | Measurer on original bytes, heading-inclusive; unchanged. |
| EVID-02 | 02-05, 02-09 | SATISFIED | Sanitizer unchanged since gap closure; table built at run time. |
| EVID-03 | 02-05, 02-09 | SATISFIED | Gate unchanged and fails closed; promote refuses a leak and now also refuses a missing deny list. |
| EVID-07 | 02-01, 02-07 | SATISFIED | Self-test shim removes `claude` from PATH and reports 0 model calls (last full run 2026-11-12). |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| stub, wrapper, runroot, manifest, measure, sanitize, leakgate, allowlist, flags, promote, preflight, spike, stream modules | Phase 2 modules | VERIFIED | All present and substantive; the changes since the last report are listed above. |
| `tests/harness/selftest` | bash 3.2 zero-token entry shim | VERIFIED | Unchanged, wired to unittest discovery. |
| `tests/harness/data/spike-findings.md` and stream fixtures | decided spikes with real captures | VERIFIED | Unchanged. |
| `.gitleaks.toml` | twin of the leak gate rules | VERIFIED | Unchanged. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| sanitizer | gate | deny entries carry the login | WIRED | Both unchanged since the last verification. |
| promote | gate | scan before copy, for both `promote` and `promote_into` | WIRED | Both scan the whole stage first and create nothing on refusal. |
| wrapper | stub | argv passthrough with conflict injection outside the stub | WIRED | Wrapper unchanged. |
| selftest | unittest discovery | scrubbed PATH, `-I -B` | WIRED | Shim unchanged. |

### Data-Flow Trace (Level 4)

The one chain that matters is live machine values to the sanitizer table to replaced text, and the same values to the gate. Neither module changed, and the gate still reports real findings on real input in the read-only checks above (home path with a space and with an escape). Not otherwise applicable: the phase renders no dynamic UI data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Stub refuses without CKPT_HOME | the stub `status` with the variable unset | banner, error line, exit 64 | PASS |
| Version gate refuses an untested build | `check_version` on a fake newer build | status UNTESTED, exit constant 13 | PASS |
| Measurer counts UTF-8 bytes | `measure_bytes` on a heading plus multibyte text | 22 bytes, equal to the hand count | PASS |
| Manifest keeps odd names | `tree_manifest` on a scratch folder with a newline name and a non-Latin name | 2 entries | PASS |
| Run root is exclusive | second `exclusive_dir` on the same path | file-exists error | PASS |
| Gate refuses home paths | `scan_bytes` on a synthetic home path, and on one before an escaped newline | one `home-path-unix` finding each; clean text gives none | PASS |
| Leak gate over the harness | `pc_leakgate.py scan tests/harness` | 93 files scanned, 0 findings | PASS |
| Spend ledger | `pc_spike.py spend` | 0.26 USD of 5.00 USD, attempts as before | PASS |
| Full unittest suite and self-test | not run here, by instruction | last orchestrator run: 2405 OK, 3 skipped, 0 model calls | NOT RERUN |

### Probe Execution

No `probe-*.sh` files exist and no plan declares any. Skipped.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| the changed covered files and the README additions | n/a | TBD, FIXME, XXX markers | none found | clean |

### Known items weighed against the goal

| Item | Blocks this phase? | Reasoning |
|------|--------------------|-----------|
| T-02-15, accepted risk AR-02-03: the `refuse_under` guard in `pc_manifest.py` exists and is unit-tested, but no production `take_snapshot` call passes it | No | `tests/harness/pc_row1.py` threads the argument through with an empty default, and its callers still do not pass the config directory. The guard is part of the allocator and snapshotter tests; the phase goal asks that the snapshotter be proven by the suite, and it is. The risk is recorded in `02-SECURITY.md` (59 threats closed, 0 open) and a wiring follow-up is recorded in STATE.md. Not a new gap. |
| Open review warnings WR-04 to WR-14 and info items from the second-pass review | No | Weighed in the first report and unchanged in substance. WR-03 (stub end marker) is now fixed in the stub, and WR-14 (callers must pass the sanitizer's entries) is now enforced by `promote` raising when none are given. |
| Shared runs root with no owner or mode check on a pre-existing level | No | Recorded in STATE.md; an observation, not a failed must-have. |

### Human Verification Required

None.

### Gaps Summary

No gaps. Every Phase 2 guarantee still holds on the current tree, the Phase 3 and 4 changes to covered files are additive or stricter, and the frozen skill, reference, fixture and evidence paths are untouched. The one reservation is procedural: this pass read code and ran read-only one-liners, and relied on the orchestrator's record of the green suite on 2026-11-12 instead of rerunning it.

---

_Verified: 2026-11-13_
_Verifier: Claude (gsd-verifier)_
