# Requirements: preclear

**Defined:** 2026-10-21
**Core Value:** A fresh session resumes from the checkpoint without guessing: every fact it reads was verified when written, and anything unknown is marked `UNCONFIRMED` rather than invented.

This milestone does not change the skill. It makes the repository public and the acceptance
matrix reproducible by a stranger with Claude Code, git and Python 3.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Publication

- [x] **PUB-01**: Owner decisions are recorded in `PROJECT.md` Key Decisions: no history rewrite, `bokiko <bokiko@gmail.com>` is the public identity, row 7 ships as a disclosed known issue
- [x] **PUB-02**: A secret and identifier scan (gitleaks plus custom rules for home paths, hostnames, private IPs) over the full history and tree of a fresh `--mirror` clone reports zero findings beyond the two accepted ones (ten home-path lines in d437af2, author email)
- [x] **PUB-03**: Pre-commit and pre-push hooks run the same scan on new content and are proven by a seeded fake leak that they block; the hook configuration is committed so a clone can enable it
- [x] **PUB-04**: The repo-local git identity is pinned to the public identity with `user.useConfigOnly`, and a pre-push check refuses commits under any other identity or carrying AI attribution trailers
- [x] **PUB-05**: A live-repo inventory (refs, tags, hooks, issues, PRs, deploy keys, Actions history, wiki, pages) is recorded immediately before the flip and shows nothing unreviewed
- [x] **PUB-06**: Row 7's known defect, the carried-forward rows (1, 2, 3c, 4b on the pre-fix digest) and the unexercised NUL `-z` form are disclosed in README or CHANGELOG before the flip
- [x] **PUB-07**: `gh repo edit --visibility public` runs only after bokiko's explicit go-word in the conversation, never inside an autonomous phase or a script; secret scanning and push protection are enabled right after

### Harness

- [x] **HARN-01**: A stranger runs one command under `tests/harness/` with `--list`, `--row <id>`, `--layout <name>`, `--all` and `--dry-run`; dry run prints the session count and spends no tokens
- [x] **HARN-02**: Preflight distinguishes SKIP, FAIL and BLOCKED with distinct exit codes, and a skipped row can never be read as a pass
- [x] **HARN-03**: Every run root is created exclusively and never overwritten or deleted by the harness; a collision is an error
- [x] **HARN-04**: Every `claude -p` invocation pins its behaviour explicitly (`--output-format stream-json --verbose`, `--setting-sources project,local`, `--settings` with an absolute realpath `autoMemoryDirectory`, `--session-id`, `--permission-mode default`, `--allowedTools` as a literal list, one full model id, `--max-turns`, `--max-budget-usd`, `DISABLE_AUTOUPDATER=1`) and a version gate refuses an untested Claude Code version
- [ ] **HARN-05**: Each run records provenance: Claude Code version, `init.model`, skill and adapter digests, harness version, isolation mode, tool set, allowlist, and per-stage usage and `total_cost_usd`
- [x] **HARN-06**: The allowlist is checked against the skill's exact commands by a self-test, and any unexpected `permission_denied` event or `result.permission_denials` entry fails the row; refusals are never detected by substring on the reply
- [ ] **HARN-07**: The `system/init` manifest (skills, permission mode, memory paths) is asserted every run, and the isolation mode in force (default or strict) is recorded per row after spike S1 decides which the matrix claims
- [x] **HARN-08**: Snapshots and manifests are filename-safe (newline and non-Latin names survive) and are taken before and after every stage
- [ ] **HARN-09**: Write-boundary and git-read-only assertions are mechanical: zero writes outside approved roots, no git mutation, derived from snapshots and traces rather than the model's claims
- [ ] **HARN-10**: Row 10 keeps the documented quoted-porcelain fallback as its expected outcome; no policy exception is added for the NUL `-z` form
- [ ] **HARN-11**: Row 11's injector triggers on the n-th model-initiated call matching an exact argv, never on Claude Code's own startup calls, and wrapper log lines are correlated with `tool_use` ids
- [ ] **HARN-12**: Row 7's preflight proves the `chmod` denial is effective or marks the row SKIPPED
- [ ] **HARN-13**: Everything new lives under `tests/harness/`; `SKILL.md`, `references/` and `tests/fixtures/` are unchanged unless a rerun exposes a defect, and `SKILL.md` stays at or under 12,000 bytes
- [x] **HARN-14**: The harness needs no install beyond Claude Code, git and Python 3 (standard library only); shell is limited to bash 3.2-compatible entry shims and the model-facing wrapper

### Stub helper

- [x] **STUB-01**: A single-file Python stub under `tests/harness/` implements the `checkpoint-v1` interface in `references/checkpoint-v1.md`: `status`, `show`, `validate`, `update`, `note`, `lint`, `handoff`, exit codes 0 to 6, 64-char lowercase sha256 section hashes, six-section and byte-cap validation, atomic writes and a lock
- [x] **STUB-02**: The stub refuses to run without `CKPT_HOME` and keeps all state under it, so every run is isolated
- [x] **STUB-03**: The observable contract is mined from every committed `wrapper-calls.log` and decisive output in `tests/evidence/`, and a replay conformance suite reruns those argv sequences against the stub with zero model tokens
- [x] **STUB-04**: Conflict injection and call logging are composed outside the stub by a wrapper, so the conflict row proves the real hash guard; stub-internal switches exist only for exits 5 and 6 and are labelled
- [x] **STUB-05**: A branch table lists every exit code and status shape the rows need and marks `handoff`, `note`, exit 5 and exit 6 as UNCONFIRMED against the real build; the stub brands its output as stub-backed
- [x] **STUB-06**: `bind`, `create` and `init` are never in any model-facing allowlist; only the driver may call them
- [x] **STUB-07**: `references/checkpoint-v1.md` is not edited for the stub; stub documentation lives under `tests/`

### Evidence

- [x] **EVID-01**: Byte measurement runs on original files before any sanitizing, per section heading-inclusive, against the same caps as the committed evidence
- [x] **EVID-02**: A sanitizer builds its deny-list at run time from the live machine (raw, realpath, dash-slug and URL-encoded home forms, user, hostname, temp roots) and sanitizes at write time
- [x] **EVID-03**: A fail-closed leak gate scans every file before it is filed; a `promote` step refuses to copy anything into `tests/evidence/` on a scan failure
- [ ] **EVID-04**: Filed rows follow the committed per-row file set (README, tools, digests, short and full traces, snapshots, measurements) plus `mechanical-checks.md`, `usage.txt`, `model-id.txt`, `isolation-mode.txt`, `harness-version.txt`, and are written with exclusive creation into a new dated folder
- [ ] **EVID-05**: The harness never prints a verdict; each row ends with `Reviewer verdict: PENDING` and a reviewer checklist of mechanical facts
- [ ] **EVID-06**: A read-only structural comparer reports per-row differences between a rerun and `tests/evidence/publication-2026-10-20/` without editing either
- [x] **EVID-07**: A model-free `unittest` self-test suite (stub conformance, sanitizer, leak scan, collision refusal, NUL manifest, preflight paths, allowlist check, measurer) passes with zero tokens and is the first thing a stranger runs

### Rerun

- [ ] **RERUN-01**: Row 7 reruns three times on the pinned model; mechanical invariants hold in all three and a review table pairs every Do-not-redo entry with the tool calls that support it
- [ ] **RERUN-02**: The full matrix (three layouts plus twelve rows) runs from a fresh clone in a never-trusted path with a minimal environment, no `runs/` folder and the private helper unreachable; wrapper logs prove every helper call hit the stub
- [ ] **RERUN-03**: The rerun is filed as a new dated evidence folder with a per-row digest table, measured cost per row, and is labelled a new baseline on the pinned model
- [ ] **RERUN-04**: Codex reviews the rerun in a visible Herdr tab before any acceptance claim; its verdicts are recorded per row
- [ ] **RERUN-05**: `tests/harness/README.md` states prerequisites, the free-then-paid order (self-test, dry run, one row, matrix), measured cost, supported platforms and what a pass proves; `tests/acceptance.md` and CHANGELOG point to it

## v2 Requirements

Deferred to a later milestone. Tracked but not in the current roadmap.

### Harness

- **HARN-V2-01**: Resumable matrix that continues a stopped run without redoing finished rows
- **HARN-V2-02**: Bring-your-own-helper mode that runs backend rows against a real helper
- **HARN-V2-03**: Repeat mode with per-row stability reporting for rows other than row 7
- **HARN-V2-04**: Heuristic flag for unsupported claims in printed checkpoints, only if the row 7 defect recurs
- **HARN-V2-05**: Second-OS (Linux) validation run

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Live-matrix CI on GitHub Actions | Needs an API key as a repo secret and spends tokens per run |
| Committing raw stream-json transcripts | The source of the d437af2 home-path finding; sanitized copies only |
| LLM-as-judge or an automatic "ACCEPTED" verdict | Verdicts stay with a reviewer; the harness reports facts |
| Retry-until-green or parallel rows | Hides flakiness and makes failures unattributable |
| Open-sourcing the real checkpoint helper | Separate project and audit; the stub covers the tested interface |
| History rewrite or author-identity change | Owner decision 2026-10-21: paths reveal only a folder name, gmail is the public identity |
| Scoped policy exception for row 10's NUL form | Owner decision 2026-10-21: the fallback is the expected outcome |
| Editing `SKILL.md` or `references/` to satisfy a harness check | Changes digests and invalidates carried-forward evidence |
| Second backend adapter | No second ledger system has a user |
| `--bare`, `--restricted`, `--safe-mode`, bypass permission modes, the Agent SDK | Each changes or disables what is under test, or adds an install |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PUB-01 | Phase 1 | Complete |
| PUB-02 | Phase 1 | Complete |
| PUB-03 | Phase 1 | Complete |
| PUB-04 | Phase 1 | Complete |
| PUB-05 | Phase 1 | Complete |
| PUB-06 | Phase 1 | Complete |
| PUB-07 | Phase 1 | Complete |
| HARN-01 | Phase 3 | Complete |
| HARN-02 | Phase 3 | Complete |
| HARN-03 | Phase 2 | Complete |
| HARN-04 | Phase 2 | Complete |
| HARN-05 | Phase 3 | Pending |
| HARN-06 | Phase 2 | Complete |
| HARN-07 | Phase 3 | Pending |
| HARN-08 | Phase 2 | Complete |
| HARN-09 | Phase 3 | Pending |
| HARN-10 | Phase 4 | Pending |
| HARN-11 | Phase 4 | Pending |
| HARN-12 | Phase 4 | Pending |
| HARN-13 | Phase 3 | Pending |
| HARN-14 | Phase 2 | Complete |
| STUB-01 | Phase 2 | Complete |
| STUB-02 | Phase 2 | Complete |
| STUB-03 | Phase 2 | Complete |
| STUB-04 | Phase 2 | Complete |
| STUB-05 | Phase 2 | Complete |
| STUB-06 | Phase 2 | Complete |
| STUB-07 | Phase 2 | Complete |
| EVID-01 | Phase 2 | Complete |
| EVID-02 | Phase 2 | Complete |
| EVID-03 | Phase 2 | Complete |
| EVID-04 | Phase 3 | Pending |
| EVID-05 | Phase 3 | Pending |
| EVID-06 | Phase 3 | Pending |
| EVID-07 | Phase 2 | Complete |
| RERUN-01 | Phase 4 | Pending |
| RERUN-02 | Phase 4 | Pending |
| RERUN-03 | Phase 4 | Pending |
| RERUN-04 | Phase 4 | Pending |
| RERUN-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0
- Phase 1: 7, Phase 2: 16, Phase 3: 9, Phase 4: 8

---
*Requirements defined: 2026-10-21*
*Last updated: 2026-10-21 after roadmap creation*
