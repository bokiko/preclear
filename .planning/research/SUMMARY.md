# Project Research Summary

**Project:** preclear (subsequent milestone: public release, then a reproducible acceptance harness with a test-only stub helper)
**Domain:** Public release of a Claude Code skill repository, plus a headless acceptance harness for a non-deterministic LLM skill
**Researched:** 2026-10-21
**Confidence:** MEDIUM-HIGH (HIGH on Claude Code flags and GitHub behaviour; MEDIUM on stub fidelity, isolation, and cost)

Detail files: `.planning/research/STACK.md`, `.planning/research/FEATURES.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`. Context: `.planning/PROJECT.md`.

## Executive Summary

The skill, three layouts and twelve publication rows are already accepted. This milestone is not about changing the skill. It is about (1) getting the repository public safely and (2) letting a stranger with only Claude Code, git and Python 3 rerun the whole matrix and compare the result row for row with the committed evidence. The comparable public harnesses (Superpowers shell tests, MLflow skill evals, record/replay tools) assert on model text or need heavy toolchains. Preclear's own history points to a different design: judge files, bytes, hashes and tool calls, never the model's claims. Defect D1 (the model's cap statements disagreed with the independent manifest in 5 of 12 runs) and the allowlist that never matched the skill's exact status command are the proof.

Recommended approach, on which all four files agree: drive plain `claude -p --output-format stream-json --verbose` with every behaviour flag pinned explicitly. Write the driver, stream parser, sanitizer, measurer, snapshotter and stub in Python 3.9 standard library only, with bash 3.2 kept to thin entry scripts. Do not use `--bare`, the Agent SDK, `--dangerously-skip-permissions`, jq, pytest or CI. Isolation is per run: an exclusively created run root, its own `CKPT_HOME`, a pinned `autoMemoryDirectory` via `--settings`, `--setting-sources project,local`, and an allowlist delivered on the command line (project `permissions.allow` is ignored in `-p` because the trust dialog never shows). The harness emits mechanical facts and `Reviewer verdict: PENDING`; it never prints "accepted". Only sanitized, leak-gated copies cross into `tests/evidence/`; originals stay in the gitignored run root, and byte measurement happens on originals first.

The main risks are irreversible ones. A history rewrite or an identity slip after the visibility flip cannot be cleanly retracted, and every commit already carries the same personal mailbox address in author and committer fields, which tree scans never see. "Publish first, harness after" means the harness's own mistakes land in public history, so the leak and identity gates must exist before the flip and stay on as hooks (there is no CI). The second cluster is validity: stub fidelity (the adapter and stub are written from the same document, so agreement alone proves nothing), silent allowlist mismatches, Claude Code default drift, and single-run verdicts on a stochastic agent. The mitigations are replay conformance against committed wrapper logs, structured denial parsing, a version gate, and a split between mechanical invariants (must hold every run) and behavioural content (judged).

## Key Findings

### Recommended Stack

Nothing to install beyond Claude Code itself (native binary, no Node). Python 3 ships with the macOS Command Line Tools that provide git and is present on mainstream Linux. Full flag contract and event shapes are in `.planning/research/STACK.md`.

**Core technologies:**
- Claude Code CLI `-p` (2.1.306 verified; evidence ran on 2.1.304; tested floor 2.1.302): the system under test, driven headless. Record version and `init.model` per run.
- Python 3.9 stdlib: driver, parser, sanitizer, leak gate, measurer, manifests (`os.walk` plus `os.fsencode` so newline filenames survive), stub. Replaces jq, `timeout`, `uuidgen`, `sha256sum`, `sed -i`.
- bash 3.2: entry scripts only, plus the shims where Architecture keeps them (see Open Disagreements).
- `unittest`: model-free self-tests (zero tokens).
- Pinned flags every run: `--output-format stream-json --verbose`, `--setting-sources project,local`, `--settings <per-run file>` (`autoMemoryDirectory`, absolute realpath), `--session-id <uuid>`, `--resume` for same-session follow-up only, `--permission-mode default` (assert `init.permissionMode`), `--allowedTools` literal list, full model id, `--max-turns`, `--max-budget-usd`, wall-clock watchdog (SIGINT first, then SIGTERM), `DISABLE_AUTOUPDATER=1`.
- Never: `--bare`, bypass or `auto` permission modes, `--include-partial-messages`, telemetry-disabling variables, any `rm -rf`.
- Stub: single-file Python executable under `tests/`, lowercase sha256 hex section hashes (64 chars, matching all committed evidence), session id from `--session` or `CLAUDE_CODE_SESSION_ID`, atomic writes via `os.replace`, `fcntl.flock` lock, UTF-8 stdout forced, exit codes 0 to 6, six-section / 4,096-byte / 600-char validation counted in UTF-8 bytes including markers. Built only from `references/checkpoint-v1.md` and committed evidence, never from the private helper's source.

### Expected Features

**Must have (table stakes, all P1 for this milestone):**
- One-command runner with `--list`, `--row`, `--layout`, `--all`, `--dry-run` (dry run prints session count, spends nothing)
- Preflight with distinct SKIP / FAIL / BLOCKED and exit codes (0 / 1 / 77); skipped never reads as passed
- Provenance record, exclusive run root, pinned committed per-row permission policy with a self-check that the allowlist matches the skill's exact commands
- Staged freezing of evidence, NUL-safe manifests, independent byte measurement on originals, write-boundary and git-read-only assertions, machine-readable per-row facts
- Executed-versus-attempted helper-call log, test-only stub with the fault branches rows 2, 3a, 3b, 4a, 4b need
- Model-free self-test suite (stub conformance, sanitizer, leak scan, collision refusal, NUL manifest, preflight paths, allowlist check)
- Sanitizer, leak scan, and a `promote` step that refuses to copy on scan failure
- Cost and runtime guardrails, run guide and result-reading guide
- Row 7 clean rerun and one full-matrix rerun from a clean clone, filed as a new dated evidence folder (the milestone's definition of done)

**Should have (P2, after the first promoted rerun):** per-row comparison against the committed baseline (contract derived from `measurements.md`, `wrapper-calls.log` and README tables, not a byte diff), extended trace assertions, reviewer-checklist emitter, resumable matrix, bring-your-own-helper mode.

**Defer (v2+):** repeat mode with per-row stability (but see the row 7 disagreement below), heuristic unsupported-claim flag (only if the row 7 defect recurs), token-free CI, second backend adapter.

**Anti-features, do not build:** live-matrix CI, committed raw stream-json, golden prose diffs, LLM-as-judge verdicts, an "ACCEPTED" printout, retry-until-green, automatic cleanup of run roots, parallel rows, any framework dependency, bundling the real helper, editing SKILL.md to satisfy a check (it sits at 11,994 of 12,000 bytes).

### Architecture Approach

One orchestrator drives a per-row pipeline with a hard private/public boundary. Rows are data files plus at most one hook function, so adding a row never touches the engine. Per row: allocate run root, materialize fixture (realpath everywhere; on macOS a logical temp path silently turns every backend row into "no block applies"), build policy and child environment, snapshot, then one `claude -p` process per stage (work with `--session-id`, `/preclear` with `--resume`, fresh resume in a new session, optional variants), snapshot after each stage, extract traces from stream-json, measure originals, run mechanical checks, stage text copies, sanitize, leak-gate (fail closed), and file with exclusive creation into `tests/evidence/<run-label>/<row>/`. Everything lives under `tests/harness/`; `SKILL.md`, `references/` and `tests/fixtures/` do not change. Full diagram, per-row file set and row-to-capability matrix are in `.planning/research/ARCHITECTURE.md`.

**Major components:**
1. Run-root allocator and materializer: exclusive `os.mkdir`, realpath, deterministic fixture git state, rendered configuration block
2. Policy builder: one pure function producing the allowlist, tool sets, settings file and the explicit child environment
3. Stub helper plus wrapper: `checkpoint-v1` implementation, and the executable named in the configuration block that logs every executed call
4. Stage runner and snapshotter: one process per stage, `os.walk`-based snapshots
5. Trace extractor, measurer, mechanical checks: parse tool_use / tool_result by id, `permission_denied` events and `result.permission_denials`; independent byte oracle; PASS / FAIL / UNCONFIRMED per check
6. Sanitizer, leak gate, evidence filer: rules built at run time from the live machine (raw, realpath, dash-slug and URL-encoded home forms, user, hostname, tmp roots), generic regexes only in the repo
7. Evidence comparer: read-only structural comparison with committed evidence

### Critical Pitfalls

Top five by consequence (all 20 plus minor ones are in `.planning/research/PITFALLS.md`):

1. **History rewrite and author identity handled as separate chores.** All 11 commits carry the same personal mailbox address; scans of the tree never see it; `.mailmap` does not change what GitHub shows. Decide the three open items together, classify what the ten home-path lines actually expose, do at most one `git filter-repo` pass on a fresh mirror with a bundle backup, update stale SHA citations in prose afterwards, and set the repo-local identity before any further commit. Do it while private.
2. **The real leak surface is evidence files, sanitizer gaps and everything added after the audit.** `!tests/evidence/**/*.log` tracks any new log automatically; token replacement misses new path shapes (symlink forms, dash-slug project directories, other OSes). Build the deny-list at run time, sanitize at write time after measuring originals, run gitleaks plus custom identifier rules over `--all` history on a fresh `--mirror` clone, and install pre-commit and pre-push hooks (test them with a seeded fake leak). There is no CI, so hooks are the only net.
3. **Allowlist patterns that silently do not match** (already happened: rows 10 and 11). Match is on whole command text; `:*` only at the end; a global option before the subcommand breaks it; compound commands need every part allowed; `$VAR` is denied. Derive an `expected-commands` table from committed traces, treat unexpected denials as row failures using structured events (never substring on the reply), and add an allowlist-versus-skill-commands self-check. Related: project `permissions.allow` is ignored under `-p`, so deliver the allowlist on the command line and treat a "has not been trusted" stderr line as a setup failure.
4. **Stub fidelity is circular.** Adapter and stub come from the same document, which omits hash scheme, conflict-file details, bind/create/init, lock and kill-switch behaviour. Replay every committed `wrapper-calls.log` argv sequence and decisive output against the stub in a scratch registry, keep an explicit branch table that the rerun must fully hit (including exits 2 and 4), brand the stub visibly (banner, digest, "stub-backed" labels). Do not edit `references/checkpoint-v1.md`: it changes the adapter digest and invalidates carried-forward rows.
5. **Stochastic agent judged by single runs and by its own claims.** Split assertions into mechanical invariants (every run, from files and logs) and behavioural content (judged). Never use the model's measurements. Instrumentation must not fire on Claude Code's own startup calls (row 11 first pass was lost this way): trigger on the n-th model-initiated call matching an exact argv, and correlate wrapper log lines with `tool_use` ids.

Also load-bearing: pass every Claude Code knob explicitly and gate on version (defaults changed in 2.1.302 and `--bare` is announced as the future `-p` default); no destructive code path and `set -e` fragility (row 3c died three times); "done" must be proven from a never-trusted fresh path with a minimal environment, no `runs/` folder and the private helper unreachable.

## Open Disagreements Between the Research Files

Recorded as positions and trade-offs. Items marked RULING are also in the next section.

**D-A. Where fault injection lives (conflict, logging).**
- STACK: inside the stub, via environment switches (`CKPT_STUB_LOG`, `CKPT_STUB_INJECT_CONFLICT=<n>`). One executable to allowlist and digest, no separate wrapper scripts. It flags MEDIUM and names a thin wrapper as the alternative for byte-parity with earlier artifacts.
- ARCHITECTURE: composed outside. The stub is faithful and has no test modes. A bash wrapper logs and, when armed, performs a real second-writer update through the stub so the caller gets a genuine exit 3 (count 2 gives conflict and then conflict again, UNSTABLE). Trade-off it accepts: more moving parts, in exchange for the conflict row proving the real hash guard and no stub that "lies on demand".
- FEATURES: keeps the logging wrapper but lists stub fault modes (conflict once or twice, deny, kill switch, lock timeout, invalid block) as a P1 differentiator; notes bring-your-own-helper cannot be combined with stub-internal faults.
- PITFALLS: leans to the existing wrapper path for conflict injection; built-in stub faults acceptable only for exits 5 and 6 and only if labelled.
- Synthesizer recommendation: three of four lean outside. Compose the conflict (exit 3) and call logging outside the stub through the wrapper, which also matches the committed evidence shape (`wrapper-calls.log`, `wrapper-injection.log`) and makes replay conformance straightforward. Allow stub-internal switches only for exits 5 and 6 (kill-switch marker file, bounded lock), clearly labelled, since no real row exercised them. Cost of this choice: two small bash shims stay in the tree and must pass shellcheck and work on bash 3.2.

**D-B. Python versus shell, and how much shell remains.**
- STACK: Python for everything including the stub; bash only as `exec python3` entry scripts. Argues bash 3.2/BSD userland is where byte-exact UTF-8 parsing, hashing and locking break first.
- ARCHITECTURE: Python for engine and stub, but the wrapper and git shim stay bash (they are the executables the model calls and the accepted evidence shows that shape).
- PITFALLS: Python or POSIX shell for the stub; stresses no Node.
- FEATURES: "bash plus Python 3 standard library".
- Synthesizer recommendation: Python for the stub and all logic (unanimous on no Node, no installs). Shims stay minimal bash only if D-A resolves outside the stub. If bokiko wants zero shell beyond entry scripts, the cost is moving injection into the stub (D-A, STACK position).

**D-C. Isolation of user-level instructions.**
- STACK: `--setting-sources project,local` is sufficient. Live probe on 2.1.306 showed user-level instructions absent from context and only built-in skills listed. `CLAUDE_CONFIG_DIR` empty is rejected as default because it may hide subscription credentials (unverified).
- ARCHITECTURE and PITFALLS: UNCONFIRMED. The accepted evidence contains a model command probing a user-level configuration path that appears nowhere in the skill or fixtures, hinting user-level instructions loaded. Proposes a strict mode (`CLAUDE_CONFIG_DIR` empty plus token auth) and a mandatory spike S1; until proven, record `isolation-mode.txt` as `default` and state the residual risk. PITFALLS adds an init-manifest assertion (skills, plugins, MCP servers, hook events) and notes `--restricted` and `--safe-mode` defeat the test.
- Synthesizer recommendation: treat it as unresolved, run the spike first, assert the `system/init` manifest in every run regardless. RULING needed (below) on which mode is the matrix's claimed baseline.

**D-D. How many runs per row.**
- FEATURES: one full-matrix rerun; repeat mode deferred (P3).
- PITFALLS: n of at least 3 on gating rows (row 7 and carried-forward rows 1, 2, 3c, 4b), mechanical invariants required in all n, failed attempts kept.
- ARCHITECTURE: one run per row, matrix idempotent restart.
- Synthesizer recommendation: pull a minimal repeat into scope for row 7 only (n = 3, invariants in 3 of 3), because it is the one correctness defect and a single clean run cannot show it is fixed. Keep the other rows at n = 1 for cost. Cost is unmeasured, so confirm after the walking skeleton reports usage.

**D-E. Allowlist shape and tool set.**
- STACK: literal absolute-path `--allowedTools`, `--permission-mode default`, no `--tools` pin; space-star prefix syntax.
- ARCHITECTURE: per-verb helper entries (never `wrapper:*`, because that would also allow `bind`, `init`, `create`), plus `--tools` and `--disallowedTools`, `--add-dir` for memory and ledger roots; notes the accepted evidence used the colon form and allowlisted Glob and Grep, so pinning `--tools` is a deliberate delta to document.
- Synthesizer recommendation: per-verb entries and a profile file (Architecture), syntax verified by the policy probe on the installed version (Stack/Pitfalls). Record every delta from the 2026-10-20 baseline in each README.

**D-F. Comparison timing.** FEATURES defers baseline comparison to P2 (contract built from two real data points); ARCHITECTURE builds a comparer into the walking skeleton and the final phase. Recommendation: a thin structural comparer at the walking skeleton for row 1 (proves the format lines up), the full per-row contract after the first complete rerun.

**D-G. Which verbs the driver may call on the stub.** ARCHITECTURE has the driver use stub setup verbs (`bind`, `init`, `create`) so one component owns state format; PITFALLS notes these are unspecified in the contract. Resolve by mining recorded logs and fixtures in the stub phase, and keep these verbs out of every model-facing allowlist.

## Implications for Roadmap

Seven phases. Order follows hard dependencies: the irreversible public step needs its gates first; the harness libraries need real stream data; the stub can be built in parallel with the model-free libraries; rows are added one capability at a time so failures are attributable.

### Phase 1: Publication gate
**Rationale:** Every later commit is public once the flip happens, and the identity, leak and history decisions are irreversible after it. Everything here can be done while the repo is still private and costs no tokens.
**Delivers:** Recorded decisions (history rewrite yes/no, public identity, row 7 disclosure) in `PROJECT.md` Key Decisions; at most one rewrite pass covering paths and author/committer fields on a fresh mirror with bundle backup; repo-local identity set, `user.useConfigOnly`, pre-push identity check; gitleaks plus custom identifier rules over `--all` history and tree on a `--mirror` clone; pre-commit and pre-push hooks proven by a seeded fake leak; live-repo inventory (refs, hooks, issues, deploy keys, Actions history); decision on whether `.planning/` stays tracked and removal of dangling pointers to private artifacts in new prose; a tag with per-row digest table; row 7 recorded as an open disclosed item. The visibility flip is a final manual step executed only on bokiko's explicit word in the conversation.
**Addresses:** Active requirement "repository is public".
**Avoids:** Pitfalls 1, 2, 3, 16, 17, 18, 20.
**Note:** the harness cannot be published before this phase, so the leak-scan configuration built here is reused as the harness's pre-commit gate.

### Phase 2: Prerequisite spikes and model-free foundation
**Rationale:** Two cheap spikes decide design (isolation mode, allowlist syntax and stream shape); the libraries behind them need no model and can be proven with zero tokens. Public commits from here on must pass the Phase 1 gates.
**Delivers:** Spike S1 (does `--setting-sources project,local` keep user-level instructions out; strict mode viability on macOS and Linux with subscription and API-key auth; does `--restricted` load project CLAUDE.md and skill). Spike S2 (capture one real stream-json stream as parser fixture and fake-claude input; policy probe proving the skill's exact commands match the allowlist; confirm `CLAUDE_CODE_SESSION_ID` reaches the helper and `--session-id` with pre-written binding works; confirm `preclear` appears in `init.skills`). Libraries: run-root allocator, sanitizer with runtime deny-list plus leak gate (also run as a regression over existing committed evidence), measurer, snapshotter, trace parser, expected-commands table extracted from committed traces, version gate. Python `unittest` selftest green with zero tokens; hostile-fixture manifest determinism test.
**Uses:** Python 3.9 stdlib, `os.mkdir`, `os.walk`, `hashlib`, `re`.
**Avoids:** Pitfalls 4, 6, 7, 9, 11, 12, 19.

### Phase 3: Stub helper and wrapper
**Rationale:** The backend rows (1, 2, 3a, 3b, 3c, 4a, 4b, bound-ledger) cannot run without it; it is independent of Phase 2's model-facing work and parallelizable. Fidelity is the risk, so ground truth comes from committed evidence.
**Delivers:** Mining of all committed `wrapper-calls.log` files and decisive outputs into an observable-contract note; the stub; wrapper (log, optional armed second-writer injector) per Disagreement D-A; a branch table; replay conformance suite; labelling (banner, digest, "stub-backed"); stub README stating coverage gaps (exits 5 and 6, `handoff` and `note` output unconfirmed against the real build, hash values never comparable across helpers). A scripted replay of row 2 shows exit 3 twice, then success after a manual merge.
**Avoids:** Pitfall 13, 10 (wrapper self-test: no trigger on a no-op session).

### Phase 4: Driver and walking skeleton (row 1)
**Rationale:** Row 1 touches every component except the injector and git shim, so one real end-to-end folder validates the engine before more rows are built.
**Delivers:** Driver proven first against a fake `claude`, then row 1 with the real binary: fixture, rendered config (physical paths), per-verb allowlist, `--session-id` pre-bound session, s1/s2/s3 stages, snapshots, measurement, sanitize, leak gate, exclusive filing, a first thin structural compare against `tests/evidence/publication-2026-10-20/row1-wrong-binding`. Reports measured usage and cost per category, which finally gives the README a real cost figure.
**Avoids:** Pitfalls 5, 14, 15 (partly), 22.

### Phase 5: Row waves A to D
**Rationale:** Each wave adds exactly one capability so failures are attributable; the expensive injector and git shim come last.
**Delivers:** Wave A config/allowlist variants (3a, 3b, 3c, 4a, 4b). Wave B memory and permission hooks (5a, 5b, 6, 7, plain-memory and hub-memory layouts; row 7 preflight proves `chmod` denial or the row is SKIPPED, never PASS). Wave C git states and stage hooks (8a, 8b, 8c, 9, 12). Wave D injector and git shim (2, bound-ledger conflict/unbound/tamper, 10, 11). Each row folder follows the committed file set plus `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt`, `harness-version.txt`.
**Avoids:** Pitfalls 4, 8, 10, 12.

### Phase 6: Row 7 fix check, full matrix from a clean clone, review, docs
**Rationale:** This is the milestone's definition of done and the only place the clean-environment claim is proven.
**Delivers:** Row 7 clean rerun (n = 3 per D-D) with a review table pairing each Do-not-redo entry with tool calls in that turn; the full matrix (three layouts plus twelve rows, 17 folders) from a never-used path, minimal environment, no `runs/` folder, private helper unreachable (wrapper logs prove every call hit the stub); per-row digest table; comparer output against committed evidence; Codex consultation in a visible Herdr tab before any acceptance claim; `tests/harness/README.md` (prerequisites, staged free-then-paid usage, cost, supported platforms, what a pass proves); CHANGELOG; `tests/acceptance.md` pointer. Second-OS run if available.
**Avoids:** Pitfalls 8, 12, 14, 15, 20.

### Phase 7 (optional, can fold into 6): Post-rerun P2 features
Baseline comparison contract, reviewer-checklist emitter, resumable matrix, bring-your-own-helper mode. Only after Phase 6 shows which are worth their cost.

### Phase Ordering Rationale

- Publication first is bokiko's decision (PROJECT.md) and is workable only because Phase 1 puts every irreversible gate ahead of any harness commit. Research (Pitfall 17) advises feature branches scanned before merge to `main`, and reviewing first harness evidence in the gitignored root before copying it into `tests/evidence/`.
- Spikes precede libraries because flag semantics are version-dependent, and an allowlist defect already cost a rerun once.
- Stub parallel to libraries because they share no code and both finish before the first model-driven row.
- The walking skeleton is row 1 because it exercises the most components with the fewest special hooks.
- No CI at any point; hooks and the model-free selftest are the substitute.

### Research Flags

Phases likely needing deeper research or hands-on verification during planning:
- **Phase 2:** spikes S1 and S2 are the research; flag semantics are version-dependent and some facts rest on one live probe (one model, one machine). `CLAUDE_CONFIG_DIR` behaviour with subscription login is unverified.
- **Phase 3:** needs targeted analysis of committed wrapper logs and traces before code (hash scheme as observed, `.conflict-*` content, bind/create/init, `handoff` and `note` outputs which no committed run exercised). Run `/gsd-plan-phase --research-phase 3`.
- **Phase 5 wave D (rows 10 and 11):** the NUL `-z` form has never executed headless because redirection needs approval; may be a skill-versus-policy finding. Row 11 needs the model-initiated-call trigger design.
- **Phase 5 row 7:** environment-sensitive (`chmod` ineffective as root or on permissive mounts).

Phases with standard patterns (skip research-phase):
- **Phase 1:** `git filter-repo`, gitleaks and GitHub visibility behaviour are documented; the only work is reading the ten affected lines and verifying current GitHub account toggles in the UI at the time.
- **Phase 4:** engine pattern fixed by Architecture; main unknown is cost, answered by measurement.
- **Phase 6:** execution and review, no new research.

## Questions That Need bokiko's Ruling

These change what the roadmap and requirements say. Recommendations are given, but each is bokiko's call.

1. **Row 10 NUL policy.** Either a documented, scoped exception lets row 10 permit the single output redirection so the NUL `-z` form runs (the harness then claims the exact-command test passes), or row 10 keeps the declared quoted-porcelain fallback and the comparison records that as the expected outcome. Recommendation: first try the dry-run denial capture to see what is actually needed; default to keeping the fallback as a disclosed exception unless the scoped permission is demonstrably narrow. This decides what the harness is allowed to claim for row 10.
2. **Model pin.** The evidence does not record which model produced it (UNCONFIRMED in STACK). Choose one full model id (not an alias) for the rerun and for the committed README, or accept that the rerun is a new baseline on whatever model is current and record it. Recommendation: pin one full id, record `init.model`, and label the run as a new baseline rather than a replication.
3. **Isolation mode.** Default (`--setting-sources project,local`, residual user-level risk disclosed) versus strict (`CLAUDE_CONFIG_DIR` empty plus token auth). Depends on spike S1. Recommendation: claim default mode only if S1 shows user-level instructions absent; otherwise make strict the documented baseline for API-key users and say plainly what subscription users get.
4. **One history rewrite or none.** Three items (home paths in d437af2, personal mailbox address in all 11 commits, row 7) feed one decision. Recommendation: read the ten lines first. If the exposed string is only the public handle, accept it and record why (GitHub Support will not purge non-sensitive data anyway). If bokiko wants the personal address out of metadata, do exactly one filter-repo pass that fixes paths and author and committer together, before the flip, from a mirror with a bundle backup. Never two passes, never after the flip.
5. **Secondary rulings that follow from the above:** public identity string (handle plus noreply address versus current); whether `.planning/` stays tracked in the public repo; row 7 repeat count (D-D); and the explicit go-word for the visibility change itself, which no automation may default.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official Claude Code docs fetched 2026-10-21 and cross-checked with live probes on 2.1.306. MEDIUM on stub design details tied to the private helper's unseen behaviour, and on one model/one machine for the probes. |
| Features | MEDIUM | Claude Code flags HIGH; what other skill repos ship is MEDIUM (few publish tests, several sources are summaries or blogs); cost per full matrix LOW-MEDIUM (no dollar figures in committed evidence). |
| Architecture | MEDIUM-HIGH | Component shapes, evidence formats and helper output strings derive from committed evidence (HIGH). Isolation of user-level instructions is UNCONFIRMED with a mandatory spike. Stream shapes MEDIUM until S2. |
| Pitfalls | HIGH for Claude Code permission/headless behaviour and GitHub rewrite/visibility behaviour; MEDIUM for flakiness practice (secondary sources) and stub-fidelity analysis (derived, not externally referenced). |

**Overall confidence:** MEDIUM-HIGH. The plan is well grounded; the weakest links are the stub's fidelity to a helper nobody outside can inspect, hermetic isolation, and cost.

### Gaps to Address

- **Isolation of user-level instructions:** STACK's live probe and ARCHITECTURE's evidence hint disagree. Resolve in spike S1 before any matrix claim.
- **Cost of one full matrix:** no figure exists. Roughly 40 to 70 `claude -p` processes estimated, unmeasured. Measure in the Phase 4 skeleton; record `total_cost_usd` and token categories per stage; put the measured figure in the README before telling strangers what to expect. Treat all as client-side estimates, not billing.
- **Flag set not run end to end:** FEATURES confirmed flags against docs only, STACK exercised a subset live. Verify every flag on the installed version in Phase 2.
- **`preclear` in `init.skills`:** unconfirmed until a run with the skill installed; make it a setup gate.
- **`memory_paths` in `system/init`:** appears in live output but not in official docs (MEDIUM); fall back to a trace-based check if it disappears.
- **Colon versus space-star allowlist syntax:** accepted evidence used the colon form, current docs use space-star. The policy probe decides; document the delta.
- **Glob and Grep availability:** accepted `tools.txt` lists them but current docs say they are off by default on macOS and Linux. Pinning `--tools` is a deliberate delta.
- **Real helper's `handoff` and `note` output, section-hash normalization, exits 5 and 6:** not in any committed run. Stub marks these UNCONFIRMED; state the coverage gap in the stub README.
- **Carry-forward rows (1, 2, 3c, 4b) on the pre-fix digest:** the full rerun closes this; until then the per-row digest table must not call them current.
- **SHA citations in prose** (`PROJECT.md`, changelog, evidence READMEs, `.planning/codebase/CONCERNS.md`) go stale after any rewrite; update in a follow-up commit, never edit evidence folders.
- **Commit attribution:** the project constraint says commits are authored solely by bokiko with no AI attribution lines. Any orchestrator or tooling that appends trailers, or commits under a different identity, conflicts with that constraint and with Pitfall 2. Resolve before the first commit of this milestone and check with `git log --format=%B`.
- **Second-OS validation:** no Linux run exists. Run the clean-clone acceptance on one if available; otherwise state macOS-only validation in the README. Windows is out of scope.
- **GitHub toggles:** "Block command line pushes that expose my email", secret scanning and push protection exist but their exact UI was not described in fetched docs; verify at the time.

## Sources

### Primary (HIGH confidence)
- Claude Code docs, fetched 2026-10-21: headless (`-p`, stream-json, `init`, `api_retry`, `permission_denials`, SIGINT versus SIGTERM, `--bare`), CLI reference (every flag in the contract table), permission modes (2.1.302 Manual default for `-p`), permissions (rule syntax, compound commands, wrappers, workspace trust), settings precedence, memory (`autoMemoryDirectory`), env vars (`CLAUDE_CODE_SESSION_ID`, `DISABLE_AUTOUPDATER`), setup (native installer, no Node)
- GitHub docs, fetched 2026-10-21: removing sensitive data (cached views, dangling commits, Support scope, filter-repo 2.47+), repository visibility side effects, commit email address behaviour
- Live probes on Claude Code 2.1.306 (stream-json shape, `memory_paths`, `--session-id` reuse error, `--resume` session id, `$VAR` and compound-command denials, `--verbose` requirement); local environment checks (bash 3.2.57, Python 3.9.6, no `timeout`)
- Repo primary sources: `tests/acceptance.md`, `references/checkpoint-v1.md`, `tests/evidence/publication-2026-10-20/` (READMEs, `tools.txt`, wrapper scripts and logs, traces, snapshots, measurements), `tests/evidence/bound-ledger-2026-10-19-rerun/conflict/`, `tests/fixtures/`, `.planning/PROJECT.md`, `.planning/codebase/`. The gitignored `runs/` folder and the real helper's source were deliberately not consulted.

### Secondary (MEDIUM confidence)
- Superpowers `tests/claude-code` runner and README; MLflow "Testing and Refining Claude Code Skills with MLflow"
- Agent-evaluation literature on pass@k versus pass^k (survey results, not Claude Code specific)

### Tertiary (LOW confidence, needs validation)
- Third-party descriptions of skill-creator evals; prompt-regression blog posts (promptfoo, CI for evals); record/replay package pages (cendor-cassette, coding-agent-vcr). Used for design ideas only.

---
*Research completed: 2026-10-21*
*Ready for roadmap: yes*
