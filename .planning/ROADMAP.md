# Roadmap: preclear

## Overview

The skill, its three layouts and the twelve-row publication matrix are already accepted, and this
roadmap does not change the skill. It does two things. First it takes the repository public,
safely: owner decisions recorded, identity and leak gates live as hooks, the full history scanned,
and the visibility flip made only on bokiko's explicit word. Then it makes the acceptance matrix
reproducible by a stranger who has only Claude Code, git and Python 3: a model-free foundation and
a test-only stub helper first, one row proven end to end through the real `claude -p` as a walking
skeleton, then the full matrix run from a clean clone, filed as a new dated baseline and reviewed by
Codex. Every success criterion below can be checked from files, logs and exit codes. None depends on
what the model says about itself.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Publication Gate** - Decisions recorded, identity and leak gates live, history scanned, repository public on bokiko's word (completed 2026-10-24)
- [x] **Phase 2: Model-Free Foundation and Stub** - Spikes decided, test-only stub helper, sanitizer, leak gate and a zero-token self-test suite (completed 2026-10-26)
- [ ] **Phase 3: Walking Skeleton (Row 1)** - One row run end to end from one command, filed as sanitized evidence, compared with the committed row
- [ ] **Phase 4: Full Matrix, Row 7 and Review** - Row waves, row 7 three times, the full matrix from a clean clone as a new baseline, Codex review, docs

## Phase Details

### Phase 1: Publication Gate

**Goal:** The repository is public on GitHub with nothing unreviewed in its history, tree or live settings, and the visibility changes only after bokiko says so in the conversation.
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, PUB-06, PUB-07
**Success Criteria** (what must be TRUE):
  1. `PROJECT.md` Key Decisions records the three owner decisions with dates (no history rewrite, the public identity, row 7 as a disclosed known issue), and the repo-local git configuration shows `user.useConfigOnly` true with the public identity pinned. A test push under a different identity, and a test commit carrying an AI attribution trailer, are each refused by the pre-push check with a non-zero exit. (PUB-01, PUB-04)
  2. A secret and identifier scan (gitleaks plus the custom rules for home paths, hostnames and private IPs) over a fresh `--mirror` clone covering the full history and tree exits with exactly the two accepted findings (ten home-path lines in d437af2, the author email) and zero others. The scan configuration and the accepted-finding list are committed. (PUB-02)
  3. A seeded fake leak is blocked by the pre-commit hook and by the pre-push hook, the seeded commit never reaches history, and the hook configuration is committed so a fresh clone can enable it with one documented command. (PUB-03)
  4. The README or CHANGELOG discloses row 7's known defect, the carried-forward rows (1, 2, 3c, 4b on the pre-fix digest) and the never-executed NUL `-z` form, and this disclosure is committed before the flip. A recorded live-repo inventory (refs, tags, hooks, issues, PRs, deploy keys, Actions history, wiki, pages) taken in the same session as the flip shows nothing unreviewed. (PUB-05, PUB-06)
  5. After bokiko's explicit go-word, `gh repo view` reports the repository as public, and secret scanning and push protection are reported enabled right after. Before that word the repository is still private. (PUB-07)

**Plans:** 4/4 plans complete

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Tracer: pre-push hook set that refuses one seeded leak and one wrong-identity push in a throwaway clone; attribution-trailer gate; pin repo-local identity and `user.useConfigOnly`; record the three owner decisions in `PROJECT.md` (PUB-01, PUB-03, PUB-04)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Full scan rules and 15-fingerprint accepted-finding list; pre-commit hook and local deny-list check; hooks README and fresh-clone one-command enable (PUB-02, PUB-03)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03-PLAN.md — Read-only pre-flip tool (fresh `--mirror` scan, identity and trailer checks, live-repo inventory); row 7, carry-forward, shipped-digest and NUL `-z` disclosures (PUB-02, PUB-05, PUB-06)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 01-04-PLAN.md — Human-gated push, recorded pre-flip scan and inventory, go or no-go checkpoint; visibility flip and protections run only on bokiko's explicit word, then the read-back is recorded in a committed file and checked (PUB-02, PUB-05, PUB-07)

**Hard-rule gate:** The visibility flip (PUB-07) and any history rewrite happen only on bokiko's explicit word in the conversation. They never run inside an autonomous execution, a script, or a subagent. Plan 01-04 stops at a go or no-go checkpoint first; only after that word does the main conversation (never a subagent) run the flip, and it then records the read-back in a committed file that a read-only task checks. The recorded decision is no rewrite, so a new finding in the scan halts the phase and goes to bokiko. A rewrite is not a fallback the executor may choose.

### Phase 2: Model-Free Foundation and Stub

**Goal:** A stranger with only Claude Code, git and Python 3 can run a zero-token self-test suite that proves the stub helper, run-root allocator, snapshotter, measurer, sanitizer, leak gate and allowlist check, and two spikes have decided the pinned flags and the isolation mode.
**Mode:** mvp
**Depends on:** Phase 1 (every commit from here on is public history and must pass the Phase 1 gates)
**Requirements:** HARN-03, HARN-04, HARN-06, HARN-08, HARN-14, STUB-01, STUB-02, STUB-03, STUB-04, STUB-05, STUB-06, STUB-07, EVID-01, EVID-02, EVID-03, EVID-07
**Success Criteria** (what must be TRUE):
  1. The `unittest` self-test suite under `tests/harness/` exits 0 with zero model calls while `claude` is absent from `PATH`. It covers stub conformance, sanitizer, leak scan, collision refusal, a newline-and-non-Latin filename manifest, preflight paths, the allowlist check and the byte measurer. The measurer reports per-section and total UTF-8 bytes including headings, as actual/cap, and matches known-size fixtures that include multibyte text. (EVID-07, EVID-01, HARN-08)
  2. Replaying every argv sequence mined from the committed `wrapper-calls.log` files against the stub, in a scratch `CKPT_HOME`, reproduces the recorded decisive outputs, with zero tokens. The stub exits non-zero when `CKPT_HOME` is unset, brands its output as stub-backed, and the branch table lists exit codes 0 to 6 and marks `handoff`, `note`, exit 5 and exit 6 as UNCONFIRMED. `git diff` shows `references/checkpoint-v1.md` unchanged and stub documentation under `tests/` only. (STUB-01, STUB-02, STUB-03, STUB-05, STUB-07)
  3. Conflict injection and call logging come from a wrapper outside the stub. A scripted double-conflict replay of row 2 shows exit 3 twice and then success after a manual merge, and `bind`, `create` and `init` appear in no model-facing allowlist (checked by the allowlist self-test). (STUB-04, STUB-06)
  4. The spike findings (isolation mode, flag semantics, `init` manifest, session-id handling) are committed with a real captured stream-json fixture. One committed flag table pins every `claude -p` behaviour. The version gate refuses a simulated untested version with a distinct exit code. The allowlist self-test matches the skill's exact commands taken from committed traces. A synthetic `permission_denied` event or `permission_denials` entry fails a row, and a reply that merely contains the word "denied" does not. (HARN-04, HARN-06)
  5. Run-root creation is exclusive: a second creation of the same path is an error, and nothing in the harness deletes or overwrites a run root. The sanitizer builds its deny-list at run time from the live machine, and a seeded leak makes both the leak gate and `promote` refuse to copy into `tests/evidence/`. A scan of the harness imports finds only the standard library, and the bash entry shims run under bash 3.2. (HARN-03, HARN-14, EVID-02, EVID-03)

**Plans:** 9/9 plans complete

Plans:
**Wave 1**
- [x] 02-01-PLAN.md — Tracer: the `tests/harness/selftest` shim runs green with `claude` absent, also when `claude` shares a directory with python3 and git, and preflight has distinct exit codes; flag table, call builder, environment scrub, allowlist builder, exact-match version gate and the isolation sentence; strict stream parser with structured denial detection (HARN-04, HARN-06, EVID-07)
- [x] 02-02-PLAN.md — Tracer: mine the committed wrapper logs and replay `status` against the stub; single-file `checkpoint-v1` stub core (status, show, validate, update with the conflict path, lint, bind), exits 0, 2, 3, 4 and 64; replay of all 15 recorded calls (STUB-01, STUB-02, STUB-03)
- [x] 02-03-PLAN.md — Tracer: exclusive run-root allocator and newline-safe snapshot manifest; heading-inclusive byte measurer (actual/cap); tree copy, read-only git status capture, no-delete static scan (HARN-03, HARN-08, EVID-01)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-04-PLAN.md — Tracer: row 2 double-conflict replay through the logging and conflict wrapper outside the stub, which also refuses bind, create and init with exit 71; allowlist matcher model tested on committed traces (bind, create, init never model-facing, the env-prefixed route recorded); branch table with UNCONFIRMED marks and the hash-derivation row; frozen-reference digest check (STUB-04, STUB-05, STUB-06, STUB-07, HARN-06)
- [x] 02-05-PLAN.md — Tracer: seeded leak refused by the gate and by `promote`; runtime-built sanitizer with lower-case tokens; fail-closed leak gate with gitleaks parity; hardened `promote` (EVID-02, EVID-03)
- [x] 02-06-PLAN.md — Tracer: stub write guard, exit 5 kill switch and `note`; lock with the exit 6 timeout switch, atomic-write failure handling, `handoff`, `create`, `init`; boundary, encoding, precision, concurrency, read-only, ordering and containment proofs, and the two-switch inventory (STUB-01, STUB-02, STUB-04)

**Wave 3** *(blocked on Wave 2 completion; needs no login and spends nothing)*
- [x] 02-07-PLAN.md — Tracer: the real shim runs every module's tests under bash 3.2 with a tripwire `claude`, alone and sharing a directory with python3 and git; standard-library, shadowing, bash and exit-code agreement tests; stranger README with tables tied to the code; the model-free phase gate (HARN-14, EVID-07)

**Wave 4** *(blocked on Wave 3 completion; autonomous: false)*
- [x] 02-08-PLAN.md — Spikes S1 and S2: driver and zero-token dry run with a login-probe record, one-time manual login by bokiko (blocking), measured isolation capture that stops and asks bokiko if the instruction audit cannot be asserted, real stream fixture, seven-command policy probe, resume turn, tested-version seed, committed findings, README flag-table regeneration and gate rerun; total spend at most 5 USD (HARN-04, HARN-06)

**Wave 5** *(gap closure after verification; blocked on Wave 4 completion)*
- [x] 02-09-PLAN.md — Gap closure: sanitizer login boundary after JSON escapes and login deny entry (CR-01), leak-gate home-path, ASCII identifier and case-insensitive host rules with the `.gitleaks.toml` twin (CR-02, WR-01), fail-closed deny-list lookup with BOM-tolerant reader (WR-02), boundary tests over the committed fixtures (IN-07) (EVID-02, EVID-03)

*Plan count note: the earlier three-plan outline (02-01 spikes and flag table, 02-02 stub, 02-03 foundation and wiring) could not fit the 50 percent context target, the 3-task limit and the checkpoint-isolation rule, so each outline plan was split by concern. A plan check then reshaped the seven-plan split: the stub's completion became its own plan (02-06) to keep 02-02 inside the context budget, and the README and model-free gate (02-07) now come before the login-gated spikes (02-08), so finishing the model-free work never waits on bokiko's login. No requirement or decision moved.*

### Phase 3: Walking Skeleton (Row 1)

**Goal:** One row, row 1 (wrong binding), runs end to end through the real `claude -p` against the stub from a single command, is filed as sanitized evidence in a new dated folder with mechanical facts only, and lines up structurally with the committed row 1 evidence.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** HARN-01, HARN-02, HARN-05, HARN-07, HARN-09, HARN-13, EVID-04, EVID-05, EVID-06
**Success Criteria** (what must be TRUE):
  1. Under `tests/harness/`, `--list` prints every layout and row, `--dry-run` prints the session count and exits 0 with no `claude` process started and no usage recorded, and an unknown `--row` or `--layout` exits non-zero. Preflight reports SKIP, FAIL and BLOCKED with three distinct exit codes, and a SKIPPED row is filed under a SKIPPED label, never PASS. (HARN-01, HARN-02)
  2. One real row-1 run files a new dated folder, created exclusively under `tests/evidence/`, holding the committed per-row file set plus `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt` and `harness-version.txt`. Provenance (Claude Code version, `init.model`, skill and adapter digests, harness version, isolation mode, tool set, allowlist, per-stage usage and `total_cost_usd`) is non-empty in every field, and every filed file passed the leak gate. (HARN-05, EVID-04)
  3. The `system/init` manifest is asserted on the run (the `preclear` skill is listed, the permission mode is as pinned, the memory paths are as set) and the isolation mode is recorded as decided by spike S1. The write-boundary and git-read-only checks are derived from snapshots and traces: they report zero writes outside approved roots and zero git mutations on the real run, and they FAIL on a fixture run seeded with an out-of-root write. (HARN-07, HARN-09)
  4. The row README ends with `Reviewer verdict: PENDING` and a checklist of mechanical facts, and no filed file from the harness contains an accepted, passed or failed verdict. (EVID-05)
  5. The read-only comparer prints per-row differences between the rerun and `tests/evidence/publication-2026-10-20/row1-wrong-binding`, and tree digests of both evidence trees are identical before and after it runs. `git diff` shows `SKILL.md`, `references/` and `tests/fixtures/` unchanged, `SKILL.md` is at or under 12,000 bytes, and all new code sits under `tests/harness/`. (EVID-06, HARN-13)

**Plans:** 6/6 plans executed

Plans:
**Wave 1**
- [x] 03-01-PLAN.md — Tracer: `--list` and `--dry-run` print the registry and the session count with no process; the claude-free gate, SKIP, FAIL and BLOCKED codes, `--claude`, the budget gate and README fix lines; the file-locked matrix spend ledger with delta cost and the retry authorization flag (HARN-01, HARN-02)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — Tracer: seed the row 1 run root and run s1 through a scripted claude; the three-stage chain (s2 resumed, s3 from the resume line) with delta cost, stop rules and the pre-spend order; the init manifest and instruction audit asserted after every stage, isolation mode recorded (HARN-05, HARN-07)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03-PLAN.md — Tracer: write boundary from snapshots with seeded failing fixtures and exit 11; trace paths, git state, memory probe, ledger digests, helper-call counts; the stub end-marker fix (review WR-03) (HARN-09)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 03-04-PLAN.md — Tracer: file a finished run through the sanitizer, the leak gate and promote with the deny entries (WR-14); the full per-row file set with provenance, usage, mechanical checks and the reviewer checklist ending in `Reviewer verdict: PENDING`; SKIPPED filing and the zero-token `--refile` (HARN-05, EVID-04, EVID-05)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 03-05-PLAN.md — Tracer: the read-only comparer with tree digests before and after; structural comparison, measurement shapes and read-only proofs; pinned frozen trees, the SKILL.md size cap, the allowlist corpus scope and the zero-token phase gate (EVID-06, HARN-13)

**Wave 6** *(blocked on Wave 5 completion; autonomous: false)*
- [x] 03-06-PLAN.md — Tracer: zero-token rehearsal against the real 2.1.310 build; blocking-human checkpoint for the build, the cap and the green gate; the one paid row 1 run, filed, compared and costed (HARN-05, HARN-07, HARN-09, EVID-04, EVID-05, EVID-06, HARN-13)

*Plan count note: the earlier three-plan outline (03-01 driver, 03-02 row 1 with the real binary, 03-03 filing and comparer) could not fit the 50 percent context target, the 3-task limit and the rule that a human-gated paid run never shares a plan with implementation, so each outline plan was split by concern: the driver and spend ledger, the row seed and stage chain, the mechanical checks, the evidence filing, the comparer and frozen guards, and the single paid run. The README is one file that every plan extends, so the plans run in serial waves. No requirement or decision moved.*

**Exit output:** This phase reports the measured cost of one row, which gives the first real cost figure. Phase 4's spend is confirmed from that figure.

### Phase 4: Full Matrix, Row 7 and Review

**Goal:** A stranger clones the public repository, runs the free self-test, and then the full matrix (three layouts plus every publication row) on a pinned model. The result is filed as a new dated baseline that Codex has reviewed, and row 7 has been rerun three times with its defect visible in a review table, not hidden.
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** HARN-10, HARN-11, HARN-12, RERUN-01, RERUN-02, RERUN-03, RERUN-04, RERUN-05
**Success Criteria** (what must be TRUE):
  1. Row 7's preflight proves the `chmod` denial is effective, or the row is marked SKIPPED with its own exit code and label. Row 7 then runs three times on the pinned model. The mechanical invariants hold in all three, and a review table pairs every Do-not-redo entry of each printed checkpoint with the `tool_use` ids that support it. Entries with no supporting call are listed as such. Failed attempts are kept. (HARN-12, RERUN-01)
  2. Row 10's expected outcome is the documented quoted-porcelain fallback, and the committed allowlist contains no redirection or NUL-form exception. Row 11's injector fires on the n-th model-initiated call that matches an exact argv. A no-op session leaves the injection log empty, and wrapper log lines are correlated with `tool_use` ids. (HARN-10, HARN-11)
  3. From a fresh clone in a never-used path, with a minimal environment, no `runs/` folder and the private helper unreachable, `--all` produces one folder per entry in `--list`. The wrapper logs show every helper call resolved to the stub, and none to the private helper. (RERUN-02)
  4. A new dated evidence folder holds a per-row digest table, the measured cost per row and a label that the run is a new baseline on the pinned model. It also holds the comparer's per-row differences against `tests/evidence/publication-2026-10-20/`, and every file passed the leak gate. Codex's per-row verdicts, from a review in a visible Herdr tab, are recorded in it before any acceptance claim is made. (RERUN-03, RERUN-04)
  5. `tests/harness/README.md` states the prerequisites, the free-then-paid order (self-test, dry run, one row, matrix), the measured cost, the supported platforms and what a pass proves. `tests/acceptance.md` and `CHANGELOG.md` both point to it. (RERUN-05)

**Plans:** 3 plans

Plans:
- [ ] 04-01: Row waves A to D, one capability per wave: row 7 preflight, row 10 fallback expectation, row 11 model-initiated-call injector, then the remaining row hooks; each wave run once and attributed before the next (HARN-10, HARN-11, HARN-12)
- [ ] 04-02: Row 7 three-run check with the Do-not-redo review table (RERUN-01); starts only after bokiko has confirmed the budget from the Phase 3 cost figure
- [ ] 04-03: Clean-clone full-matrix baseline, per-row digest table and cost, comparer output, Codex review in a visible Herdr tab, harness README, CHANGELOG and acceptance pointers (RERUN-02, RERUN-03, RERUN-04, RERUN-05)

## Standing Rules For Every Phase

- **Hard-rule actions need bokiko's word in the conversation:** the visibility flip, any history rewrite, any deletion. No autonomous run, script or subagent performs them or defaults them. Phase 4 also stops for a budget confirmation before multi-run spend.
- **Evidence integrity:** historical folders under `tests/evidence/` are never edited. A rerun adds a new dated folder. Measurement happens on original files before sanitizing, and only leak-gated copies are filed.
- **The skill is frozen:** `SKILL.md`, `references/` and `tests/fixtures/` change only to fix a defect a rerun exposes, and `SKILL.md` stays at or under 12,000 bytes.
- **Commits:** authored solely by bokiko with no AI attribution trailers. From Phase 1 on, every commit passes the scan hooks.
- **Verdicts:** the harness prints facts. Acceptance is claimed only after Codex review in a visible Herdr tab.
- **Privacy:** this file and every planning artifact use repo-relative paths and refer to the owner only as bokiko, because `.planning/` becomes public with the repository.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Publication Gate | 4/4 | Complete    | 2026-10-24 |
| 2. Model-Free Foundation and Stub | 9/9 | Complete    | 2026-10-26 |
| 3. Walking Skeleton (Row 1) | 6/6 | In Progress | - |
| 4. Full Matrix, Row 7 and Review | 0/3 | Not started | - |
