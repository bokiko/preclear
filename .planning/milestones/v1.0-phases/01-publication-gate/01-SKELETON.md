# Walking Skeleton - preclear Phase 1 (Publication Gate)

**Phase:** 1
**Generated:** 2026-10-21

## Capability Proven End-to-End

> One committed hook set, enabled with one command, that in a throwaway clone with a local
> bare remote accepts a clean push under the pinned identity, refuses a push carrying one
> seeded fake leak, and refuses a push under a wrong identity, with neither refused commit
> ever present on the remote.

This is the "thinnest end-to-end slice" of the template mapped to this project. preclear is a
Markdown skill plus shell test apparatus, not an application: there is no routing, database,
UI or hosted deployment, so the template's stack checklist is adapted below instead of
fabricated. The slice is task 1 of plan 01-01 (`type="tracer"`); every later task in the phase
expands that proven slice (more rules, more cases, the pre-flip scan, the human-gated flip)
without changing the decisions in the next table.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Product type | Markdown skill plus shell test apparatus; this phase adds repo hygiene only | The skill is frozen (SKILL.md at 11,994 of 12,000 bytes); nothing in this phase may edit `SKILL.md`, `references/`, `tests/fixtures/` or `tests/evidence/` |
| Hook mechanism | Committed `.githooks/` enabled per clone by `git config core.hooksPath .githooks`; POSIX `sh` only | Zero install, versioned with the repo, runs under the macOS `/bin/sh` (bash 3.2). The pre-commit framework and lefthook were rejected: each adds an install a stranger does not need |
| Scanner | gitleaks 8.30.x (tested on 8.30.0) driven by one committed `.gitleaks.toml` (default ruleset plus six identifier rules and two allowlists) and a committed `.gitleaksignore` of 15 immutable fingerprints | Already installed; custom rules key on shapes with a user-name segment so prose that merely names a prefix does not match; fingerprints are used only for immutable history, config allowlists for living files |
| Pre-push structure | `.githooks/pre-push` parses git's stdin once into a ranges file and fans out to `.githooks/checks/*.sh` (`leaks.sh`, `identity.sh`, `denylist.sh`) | One parsed copy of the pushed ranges; each check is owned by one plan so no two plans edit one file in the same wave |
| Exit-code contract | gitleaks run with `--exit-code 2`; exit 2 means a finding, exit 1 means a tool error; a missing scanner exits 1 (fail closed) | A crash is never read as clean, and tests can tell the two apart |
| Identity | Owner mode: repo-local `user.useConfigOnly true`, `user.name`, `user.email` and `preclear.pinnedIdentity`; strangers' clones are unpinned and the identity check skips with a visible message while the leak check stays on | `.git/config` is never cloned, so strangers are not forced into the owner's identity |
| AI attribution | One pattern file `.githooks/attribution.ere` read by `commit-msg` and by the pre-push identity check; source suppression in `.claude/settings.json` plus a one-line `.claude/CLAUDE.md` rule | Suppress at the source, refuse at commit, verify at push (PUB-04, project constraint) |
| Test layout | `scripts/test-hooks.sh` builds a throwaway clone and a local bare remote, builds fake secrets from runtime fragments, prints one `PASS <name>` or `FAIL <name>: <reason>` line per check; `scripts/prepublish-check.sh` is the read-only mirror scan and live-repo inventory | A literal fake key committed anywhere would itself be blocked and would sit in public history |
| Visibility flip | Human-gated. The flip is in no task action and no script. The last task of the last plan is a `blocking-human` go or no-go checkpoint; only the main conversation runs the flip, only after bokiko's own message says so | Hard rule (PUB-07): never inside an autonomous execution, a script or a subagent |
| Directory layout | `.githooks/`, `.githooks/checks/`, `scripts/`, `.gitleaks.toml`, `.gitleaksignore`, `.claude/settings.json`, `.claude/CLAUDE.md` at the repo root; the pre-flip record under `.planning/phases/01-publication-gate/` | Nothing under `tests/harness/` (that directory belongs to Phases 2 to 4) |

## Stack Touched in Phase 1 (adapted from the template)

- [x] Scaffold - `.githooks/`, `.gitleaks.toml`, `scripts/`; lint is `shellcheck -s sh`; the test runner is `sh scripts/test-hooks.sh`
- [ ] Routing - not applicable: no routes exist in a Markdown skill
- [ ] Database - not applicable: no data store. The closest analogue is `.gitleaksignore`, a committed fingerprint list that is read, never written, by the hooks
- [ ] UI - not applicable: the only interface is hook output on stderr and the `PASS`/`FAIL` lines
- [x] Deployment analogue - the documented local full-stack run: `git config core.hooksPath .githooks`, then `sh scripts/test-hooks.sh`, then (pre-flip only) `sh scripts/prepublish-check.sh`

## Out of Scope (Deferred to Later Slices)

- Continuous integration on GitHub Actions (needs an API-key secret; revisit after the harness is reproducible)
- The pre-commit framework, lefthook, any second scanner
- Any history rewrite or author-identity change (owner decision 2026-10-21; a new scan finding halts the phase and goes to bokiko)
- The test harness, the stub helper and every rerun (Phases 2 to 4); nothing is created under `tests/harness/`
- A policy exception for the NUL `-z` status form (Phase 4 keeps the quoted-porcelain fallback as row 10's expected outcome)
- Open-sourcing the real checkpoint helper

## Artifacts This Phase Produces

| Artifact | Kind | Plan |
|---|---|---|
| `.githooks/pre-push` | hook (mode 100755) | 01-01 |
| `.githooks/checks/leaks.sh` | check script (100755) | 01-01 |
| `.githooks/checks/identity.sh` | check script (100755) | 01-01, extended in 01-01 |
| `.githooks/attribution.ere` | pattern file (100644) | 01-01 |
| `.githooks/commit-msg` | hook (100755) | 01-01 |
| `.gitleaks.toml` | scan config | 01-01 (default ruleset), 01-02 (full rules) |
| `.gitleaksignore` | 15 accepted fingerprints | 01-02 |
| `.githooks/pre-commit` | hook (100755) | 01-02 |
| `.githooks/checks/denylist.sh` | check script (100755) | 01-02, history mode in 01-03 |
| `.githooks/README.md` | doc: one-command enable, owner pin, caveats | 01-02 |
| `scripts/test-hooks.sh` | throwaway-clone test suite | 01-01, extended in 01-02 and 01-03 |
| `scripts/prepublish-check.sh` | read-only mirror scan, inventory, record writer | 01-03 |
| `.claude/settings.json` | Claude Code attribution suppression | 01-01 |
| `.claude/CLAUDE.md` | one-line no-trailer rule | 01-01 |
| `README.md` section `## Known issues and limits` | disclosure | 01-03 |
| `CHANGELOG.md` entry and corrected publication sentence | disclosure | 01-03 |
| `.planning/PROJECT.md` Key Decisions rows (history, identity, row 7) | owner decisions | 01-01 |
| `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md` | generated pre-flip record | 01-04 |
| Repo-local git config keys `core.hooksPath`, `user.useConfigOnly`, `user.name`, `user.email`, `preclear.pinnedIdentity` | `.git/config` (not tracked) | 01-01 |
| Documented command `git config core.hooksPath .githooks` | enable command | 01-02 |
| Documented commands `sh scripts/test-hooks.sh`, `sh scripts/prepublish-check.sh` | test and pre-flip commands | 01-01, 01-03 |

## Subsequent Slice Plan

Each later phase adds one slice on top of this skeleton without altering its decisions. From
the first commit of Phase 2 on, every commit is public history and must pass these hooks.

- Phase 2: model-free foundation and stub helper (spikes, stub, sanitizer, leak gate, zero-token self-tests)
- Phase 3: walking skeleton for the harness (row 1 end to end through the real `claude -p`)
- Phase 4: full matrix, row 7 three times, Codex review, harness README
