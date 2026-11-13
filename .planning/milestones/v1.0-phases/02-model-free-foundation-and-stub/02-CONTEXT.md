# Phase 2: Model-Free Foundation and Stub - Context

**Gathered:** 2026-10-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the parts of the acceptance harness that need no model, plus the two spikes
that pin how the model will be driven later. Concretely: the exclusive run-root allocator, the
NUL-safe snapshotter and manifests, the byte measurer, the runtime-built sanitizer, the
fail-closed leak gate with `promote`, the single-file `checkpoint-v1` stub under
`tests/harness/` with its logging and conflict wrapper and branch table, a replay conformance
suite mined from the committed `wrapper-calls.log` files, the allowlist self-test, the flag
table and version gate, and a `unittest` suite a stranger runs first with zero tokens. The two
spikes (S1 isolation, S2 stream shape and policy probe) are the only token-spending work in
the phase and end in committed findings plus one real stream-json fixture.

Not in this phase: driving any matrix row (Phase 3), the row 7 rerun and row 11 injector
(Phase 4), any edit to `SKILL.md` or `references/` (project constraint), CI, a second backend.

</domain>

<decisions>
## Implementation Decisions

### Spike run policy (discussed with bokiko)
- **D-01:** The machine that runs S1 and S2 is logged in by **subscription** (claude.ai login),
  not an API key. S1 must therefore probe whether a scratch `CLAUDE_CONFIG_DIR` keeps the
  subscription credentials before strict isolation is promised.
- **D-02:** The matrix claims **strict isolation**: a harness-owned `CLAUDE_CONFIG_DIR` outside
  the repo and outside the user's home config, plus `--setting-sources project,local`.
  User-level instructions, memory and skills must be provably absent (the `init` event's
  skill and instruction lists are the assertion). — **Reversibility:** costly — the isolation
  level is part of the baseline every Phase 3 and Phase 4 evidence folder is labelled with;
  changing it later means a new baseline and new evidence folders.
- **D-03:** If S1 shows a scratch `CLAUDE_CONFIG_DIR` loses the login, the fallback is **one
  manual login into the harness-owned config dir** (bokiko runs `claude login` once with
  `CLAUDE_CONFIG_DIR` pointed at a persistent directory outside the repo). The step is
  documented for strangers in the run guide. The harness never falls back silently to
  standard isolation, and never writes, copies or reads credential files itself.
- **D-04:** Token budget for both spikes together is **at most 5 USD**, enforced per call with
  `--max-budget-usd` and a small `--max-turns`. S1 and S2 each get one retry inside that cap.
  The spike findings record the measured spend.
- **D-05:** The spikes pin **`claude-sonnet-5-5`** as the full model id. The stream-json shape
  does not depend on the model, so the S2 fixture is representative. Phase 3 picks the matrix
  baseline model separately; the spike findings note that dependency and record `init.model`.

### Stub gaps (Claude's call, confirmed by bokiko as "you decide")
- **D-06:** Where `references/checkpoint-v1.md` and the committed logs are silent, the stub
  takes the most literal reading of the document, and the branch table marks the behaviour
  **UNCONFIRMED** against the real build. Behaviours that no committed run exercised
  (`handoff`, `note`, exit 5, exit 6) are implemented as the document describes and listed as
  UNCONFIRMED, as STUB-05 requires.
- **D-07:** Section hashes are 64-character lowercase SHA-256 hex over the section body bytes
  as the committed `sha.txt` snapshots show; if the exact input bytes cannot be derived from
  the committed snapshots, the replay suite proves whichever reading reproduces them and the
  branch table records the derivation.
- **D-08:** Exits 5 and 6 get **labelled stub-internal switches** (environment variables with a
  `CKPT_STUB_` prefix, named in `tests/harness/README.md`), the only stub-internal test modes
  STUB-04 allows. Conflict injection (exit 3) and call logging live in the wrapper outside the
  stub, never inside it (roadmap decision, STUB-04).
- **D-09:** The stub refuses to run without `CKPT_HOME` (distinct non-zero exit), keeps all state
  under it, writes atomically via `os.replace`, holds an `fcntl.flock` lock, and brands itself
  as stub-backed without changing the stdout contract the adapter parses: one stub-marker line on
  stderr per call (stripped by the replay suite) plus a stub banner in `--version` output. stdout
  stays byte-identical to the committed decisive outputs (STUB-02, STUB-05). *(Refined after
  research: branding every stdout line would break the adapter's parse of `status` and `lint`.)*

### Self-test UX (Claude's call)
- **D-10:** One bash 3.2 entry shim `tests/harness/selftest` that `exec`s
  `python3 -m unittest discover` over `tests/harness/`; the shim is the first thing the README
  tells a stranger to run. Plain `python3 -m unittest discover -s tests/harness` works too.
- **D-11:** **Python floor is 3.9**, standard library only (HARN-14). No `tomllib`, so the
  harness never parses TOML; the leak-gate rules live in Python (see D-14).
- **D-12:** `tests/harness/` is a flat directory of modules plus `test_*.py` files, no package
  install step, no `setup.py`, no `pyproject.toml`.
- **D-13:** The self-test suite exits 0 with zero model calls while `claude` is absent from
  `PATH`; each test that would touch the model is a preflight-path test that asserts the
  distinct SKIP / FAIL / BLOCKED exit codes instead (EVID-07, success criterion 1).

### Sanitizer and leak gate (Claude's call)
- **D-14:** The leak gate is a Python stdlib regex scanner with its own rule list in
  `tests/harness/`. It is independent of gitleaks at run time, and one self-test cross-checks
  that every identifier rule in `.gitleaks.toml` (home paths, hostnames, private IPs, emails,
  session ids where applicable) has a counterpart in the Python list, so the two cannot drift
  silently.
- **D-15:** Replacement tokens are lower-case angle-bracket placeholders: `<home>`, `<user>`,
  `<host>`, `<tmp>`, `<repo>`, exactly the form the committed sanitized evidence already uses
  (research confirmed the evidence is lower-case; the tokens must match it byte for byte). The deny-list is
  built at run time from the live machine (raw, realpath, dash-slug and URL-encoded home forms,
  user, hostname, temp roots) and, when present, from the local file
  `.git/info/preclear-deny.txt`, whose contents are never printed or committed (EVID-02).
- **D-16:** `promote` refuses to copy anything into `tests/evidence/` on any scan failure or
  scanner error (fail closed), prints counts only, never matched values (EVID-03).

### Claude's Discretion
- Internal module boundaries inside `tests/harness/`, test naming, fixture file layout for the
  replay suite, and the exact exit codes for the version gate and the stub's missing-`CKPT_HOME`
  refusal (distinct from 0 to 6 and documented in the branch table).
- The order of the two spikes and whether S2 captures its fixture in the same call as the
  policy probe, within D-04's budget.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Interface the stub implements
- `references/checkpoint-v1.md` — the `checkpoint-v1` helper interface: commands, exit codes
  0 to 6, section hashes, six-section and byte-cap validation. Frozen: never edited for the stub
  (STUB-07).
- `references/configuration.md` — the configuration block and three resolution states the
  fixtures render.
- `references/status-sidecar.md` — NUL and quoted-porcelain sidecar formats the snapshotter
  must preserve.

### Observable contract the replay suite mines
- `tests/evidence/bound-ledger-2026-10-19/wrapper-calls.log`,
  `tests/evidence/bound-ledger-2026-10-19-rerun/wrapper-calls.log` and every
  `tests/evidence/publication-2026-10-20/row*/wrapper-calls.log` — executed helper argv
  sequences and decisive outputs (STUB-03).
- `tests/evidence/*/snap-*/sha.txt` and `measurements.md` — hash shapes and byte caps the stub
  and measurer must reproduce.
- `tests/acceptance.md` — the manual procedure and per-row criteria the harness mechanizes.

### Harness contract and research
- `.planning/REQUIREMENTS.md` — HARN-03, HARN-04, HARN-06, HARN-08, HARN-14, STUB-01 to
  STUB-07, EVID-01, EVID-02, EVID-03, EVID-07 (the 16 Phase 2 requirements).
- `.planning/research/STACK.md` — pinned `claude -p` flag contract and stream-json event shapes.
- `.planning/research/PITFALLS.md` §4, §5, §6, §7, §9, §12, §13 — allowlist matching, headless
  permission tiers, isolation, version drift, substring refusal detection, manifest
  portability, stub circularity.
- `.planning/research/ARCHITECTURE.md` — component split and the private/public boundary.
- `.planning/codebase/TESTING.md` and `.planning/codebase/CONVENTIONS.md` — evidence folder
  layout and file naming the snapshotter and `promote` must follow.

### Phase 1 gates every commit must pass
- `.githooks/README.md`, `.gitleaks.toml`, `scripts/test-hooks.sh` — the leak, identity and
  attribution hooks; the Python leak gate mirrors the identifier rules (D-14).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/prepublish-check.sh` and `.githooks/checks/denylist.sh`: shell precedents for a
  fail-closed gate that prints counts only; the Python leak gate follows the same output rule.
- `.gitleaks.toml` identifier rules: the authoritative list the Python rules must mirror (D-14).
- `tests/fixtures/*/`: the three fixtures the run-root materializer copies; each has a
  `runtime-settings.example.json` the settings builder renders with an absolute realpath.
- `tests/evidence/publication-2026-10-20/README.md`: verdict and sequence tables whose shape the
  branch table and the replay suite reuse.

### Established Patterns
- Markdown-only repository today: there is no Python yet, so `tests/harness/` sets the Python
  conventions (3.9, stdlib, flat modules, `unittest`).
- Evidence naming: `s1` to `s5` stages, `snap-N-*` folders, `wrapper-calls.log`; the snapshotter
  and `promote` must emit these names unchanged so Phase 3 evidence compares row for row.
- Hooks run on every commit: anything the harness writes under the repo must pass the leak
  gate before `git add`, and `tests/evidence/**/*.log` is tracked by a gitignore exception.

### Integration Points
- The wrapper executable named in the fixtures' configuration block is what the model calls;
  the stub sits behind it. The allowlist self-test reads the skill's exact commands from the
  committed traces, never from `SKILL.md` prose.
- Phase 3 consumes the flag table, the version gate, the policy builder and the `promote`
  step unchanged; Phase 4 adds the row 11 injector on top of the wrapper.

</code_context>

<specifics>
## Specific Ideas

- bokiko wants the stranger experience to be one command first: clone, run `tests/harness/selftest`,
  see 0 tokens spent and a green suite before anything touches the model.
- The spike findings must say in plain words which isolation level the matrix claims and
  what a subscription user has to do once (D-03), so a stranger is never surprised by a login
  prompt mid-run.

</specifics>

<deferred>
## Deferred Ideas

- Windows-style and `/root/` home-path coverage in the gitleaks home-path rule (Phase 1 review
  CR-03 leftover) — fold into the Python rule list in this phase only if cheap; the gitleaks
  rule itself is a Phase 4 hygiene item.
- A matrix-wide `--dry-run` cost estimate (counts sessions, spends nothing) — belongs to the
  Phase 3 runner.
- Per-row structural comparison against committed evidence — Phase 4 (research P2).

</deferred>

---

*Phase: 02-model-free-foundation-and-stub*
*Context gathered: 2026-10-24*
