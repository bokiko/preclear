# preclear

## What This Is

preclear is a Claude Code skill that writes the minimum a fresh session needs to continue
after `/clear`: one checkpoint file per task, durable facts routed to whatever memory or plan
system the user already has, and one paste-ready resume line. It adapts to plain memory files,
hub-style memory indexes, plan files and an opt-in ledger helper, and it never installs, binds
or configures anything on its own. It is for anyone who uses Claude Code and loses tokens
re-deriving state after every clear.

## Core Value

A fresh session resumes from the checkpoint without guessing: every fact it reads was verified
when written, and anything unknown is marked `UNCONFIRMED` rather than invented.

## Current State

**Shipped:** v1.0 Public and Reproducible on 2026-11-13 (4 phases, 47 plans, 79 tasks). The
repository is public, the harness under `tests/harness/` runs 2,405 zero-token tests green, and
the matrix baseline `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5` (21 of 21 chains,
5.7467 USD) is filed and Codex-reviewed. Paid model spend for the milestone: 12.27 USD. The
planning archive is `.planning/milestones/` (v1.0 roadmap, requirements and phase folders).

## Next Milestone Goals

Not yet defined; `/gsd-new-milestone` starts the questioning. Candidates carried out of v1.0:

- Row 7: a clean rerun whose printed checkpoint carries no unsupported Do-not-redo entry
- Codex flags on the baseline: row 6 (plan edits succeeded despite mode 444) and row 10 (grouped sidecar, not verbatim porcelain)
- Security follow-up T-02-15: pass `refuse_under` at the three `take_snapshot` call sites and the manifest CLI, with tests
- Phase 4 review warnings WR-01 to WR-05, the harness README's "no network" opening line, an independent review of the 04-22 code
- CI: decide whether a live matrix on GitHub Actions is worth an API-key secret and per-run spend

## Requirements

### Validated

- ✓ `/preclear` discovers the user's memory, plan, ledger and configuration in a fixed probe order with a hard cap on speculative lookups — existing (SKILL.md Step 1; plain-memory, hub-memory, bound-ledger layouts accepted 2026-10-19)
- ✓ Plain checkpoint under `<project>/.preclear/<task-slug>/checkpoint.md` with six fixed headings, under 4,096 bytes, measured by command and printed as actual/cap — existing (publication rows 1–12, 2026-10-20)
- ✓ One resume line that authorizes only the checkpoint's next action; a fresh session resumes read-only with zero writes — existing (seven fresh-resume runs, zero Write/Edit calls)
- ✓ Durable facts go to their existing owners (memory, plan) in the owner's format; the checkpoint holds pointers, not parallel rationale — existing (adapter ownership rule after rows 1–4)
- ✓ Opt-in `checkpoint-v1` backend: hash-guarded section updates, one bounded conflict retry, stop after the first denied mutation, fallback checkpoint with "ledger not synchronized: <reason>" — existing (rows 1, 2, 3a, 3b, 3c, 4a, 4b)
- ✓ Configuration resolves to exactly one of three states; invalid or conflicting blocks never activate a backend; `fallback_directory: none` means BLOCKED, never a file — existing (rows 3c, 4a, 4b, 7)
- ✓ Correct identity in non-git, detached HEAD, unborn branch and linked-worktree projects; frozen handoff copies are never overwritten and detect external plan edits — existing (rows 8a–8c, 9, 12)
- ✓ Large or hostile `git status` captured to a sidecar with full escaping, quoted-porcelain fallback documented when NUL capture is refused; concurrent change during capture detected and marked — existing (rows 10, 11)
- ✓ Hard rules: git read-only, never delete, never run `/clear`, never bypass a hook or write a secret — existing (SKILL.md Hard rules, every row)
- ✓ Repository follows the owner's RepoFix standard: wave header and footer, badge rows, feature and tech tables, mermaid, structure tree, issue and PR templates — existing (commit a68da30)
- ✓ The repository is public on GitHub after the owner's three audit decisions and his explicit go-word, with identity, leak and attribution hooks, a full-history scan, a committed disclosure of row 7 and a recorded live inventory — Phase 1 (PUB-01 to PUB-07; flip 2026-10-24, secret scanning and push protection enabled)
- ✓ A test-only stub helper in `tests/harness/checkpoint_stub.py` implements the `checkpoint-v1` interface closely enough that all 15 committed calls replay with the recorded exit codes; `handoff`, `note`, exit 5 and exit 6 stay UNCONFIRMED in the branch table — Phase 2 (STUB-01 to STUB-07)
- ✓ The harness refuses to reuse a run root (exit 16), carries no deletion primitive outside its test utilities, sanitizes and leak-gates every capture before it lands under the repository, and the spikes decided the pinned flags (Claude Code 2.1.310, claude-sonnet-5-5) and the isolation mode with run roots outside every home folder — Phase 2 (HARN-03, HARN-04, HARN-06, HARN-08, HARN-14, EVID-01 to EVID-03, EVID-07; 753 zero-token tests; 0.26 USD of the 5 USD spike cap)
- ✓ Row 1 runs end to end through the real `claude -p` against the stub from one command on the pinned build and model, is filed as sanitized mechanical evidence with a reviewer checklist and no verdict in a new dated folder, compares read-only with the committed row, and the cost of one row is measured at 0.2723 USD; the runner passes the deny entries to `promote` and `promote` refuses without them; Bash writes outside the approved roots, planted git configuration and refiling an unclean or incomplete run are breaches or refusals — Phase 3 (HARN-01, 02, 05, 07, 09, 13, EVID-04 to 06; 1305 zero-token tests; 0.27 USD of the 2 USD row cap; five review passes)

- ✓ The full matrix (three layouts plus every publication row, 21 chains) runs from a clean clone of the public repository on the pinned build and model through one command, with the stub helper only; filed as the new dated baseline `tests/evidence/rerun-2026-11-11-claude-sonnet-5-5` (21/21 chains, every stage success, 5.7467 USD), leak-gated, compared row for row with the committed evidence, and reviewed by Codex in a visible Herdr tab with 21 per-row verdict lines recorded before any acceptance claim — Phase 4 (HARN-10 to HARN-12, RERUN-01 to RERUN-05; 2405 zero-token tests; Phase 4 paid total 11.74 USD)
- ✓ Row 7 was rerun three times in one folder and once more in the matrix; every Do-not-redo entry of every printed checkpoint, fenced or unfenced, is listed with its same-turn candidates in `row7-review.md` and `row7-review-part-2.md`, so the defect is visible in a review table rather than hidden — Phase 4 (RERUN-01; Codex row 7 verdict: safe denial response, evidence claim overstated)

### Active

- [ ] Row 7 has a clean rerun whose printed checkpoint carries no unsupported Do-not-redo entry — not yet achieved: the 2026-11-09 triple and the matrix run still show entries without a same-turn supporting call, and attempt 3 printed its checkpoint unfenced; the defect is now measured, not fixed

### Out of Scope

- Open-sourcing the real checkpoint helper — separate project with its own audit; the stub covers the tested interface
- Continuous integration on GitHub Actions — needs an API key as a repo secret and spends tokens per run; revisit after the harness is reproducible locally
- A second backend adapter — no second ledger system has a user yet; the adapter contract exists for when one does
- Enforcing the skill with hooks — preclear is a procedure the model follows, by design; enforcement is the user's hook layer
- Changing skill behaviour during this milestone — SKILL.md is accepted and at 11,994 of 12,000 bytes; harness work must not require skill edits except to fix a defect the rerun exposes

## Context

- The skill, three layouts and the twelve-row publication matrix are accepted after Codex review (consultations 8 and 9). Verdicts and disclosed exceptions are in `tests/evidence/publication-2026-10-20/README.md`.
- The harness that produced that evidence (`pub-lib.sh`, `pub-row.sh`, `pub-plain.sh`, `pub-env.sh`, `pub-file.py`, `pub-measure.py`) lives only in the gitignored `runs/` folder on the owner's machine. It drives headless Claude Code (`claude -p` with project and local setting sources, a pinned allowlist, stream-json output) and isolates the helper with `CKPT_HOME`, a logging wrapper and a counting conflict wrapper. Known harness limits: snapshot manifests split newline filenames before the `-print0` fix; the allowlist never matched the skill's exact status command until rows 10 and 11 were rerun.
- Known open defects from the matrix: row 7's printed checkpoint claims a workspace registry check no tool call supports (Codex: FAIL for evidence integrity on that row); the NUL `-z` status form has never executed under headless policy; rows 1, 2, 3c and 4b carry forward on the pre-fix skill digest.
- The 2026-11-11 clean-clone baseline and its Codex review (`codex-review.md`) are filed; Codex flagged row 6 (the 444 plan was still edited, so denial handling was not exercised), row 10 (grouped sidecar instead of verbatim porcelain) and row 7 (overstated evidence claim). Open review warnings WR-01 to WR-05 of 04-REVIEW.md, the README's "no network" opening line, and the unreviewed 04-22 code carry into the next milestone.
- A private audit record (2026-10-20) found no credentials, keys, IP addresses, hostnames or real name anywhere in history or the tree. One medium finding: ten evidence lines with home-folder paths in commit d437af2, sanitized in the next commit.
- `.planning/` is committed to this repo, so planning artifacts become public with it. v1.0 was archived on 2026-11-13: its roadmap, requirements and the four phase folders live under `.planning/milestones/`, and `REQUIREMENTS.md` is recreated by the next milestone.

## Constraints

- **Privacy**: the owner is referred to only as bokiko; no home paths, hostnames or credentials in any committed file — the repo is going public
- **Authorization**: history rewriting, deletion and visibility changes each require the owner's explicit word in the current conversation; GSD automation never defaults them
- **Evidence integrity**: historical evidence is preserved, never repaired; reruns supersede by adding new folders
- **Skill size**: SKILL.md stays at or under 12,000 bytes
- **Commits**: authored solely by bokiko, no AI attribution lines
- **Review**: Codex consultation in a visible Herdr tab before any acceptance claim, as for every earlier milestone
- **Harness safety**: no `rm -rf` on existing run roots; exclusive creation, fail on collision

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Publish first, harness after | Repo is audited and ready; harness work can land as public commits | Good — Phase 1 published 2026-10-24 |
| Ship a test-only stub helper for backend rows | Lets strangers run the full matrix without the private helper; real helper stays private | Done — Phase 2, 15 of 15 recorded calls replay |
| Done means a full matrix rerun from a clean clone | Committed scripts alone would not prove reproducibility | Done — Phase 4, 21/21 chains from a clean clone on 2026-11-11 |
| No CI this milestone | API-key secret and per-run token cost; local reproducibility first | Held — v1.0 shipped without CI; decide in the next milestone |
| No history rewrite (2026-10-21) | The d437af2 commit adds eleven home-folder path lines across ten files (measured 2026-10-21; earlier text said ten lines); they reveal only a folder name and SHA citations stay valid; the scan accepts exactly those 15 fingerprints through `.gitleaksignore`, and a new finding halts the phase and goes to bokiko | Decided 2026-10-21 |
| `bokiko <bokiko@gmail.com>` is the public identity (2026-10-21) | The address is already the public GitHub identity; all 14 pre-phase commits carry it as the only author and committer; each clone pins it with `user.useConfigOnly` and `preclear.pinnedIdentity` | Decided 2026-10-21 |
| Row 7 ships as a disclosed known issue, rerun three times in this milestone (2026-10-21) | A single clean run cannot show a stochastic defect is fixed | Decided 2026-10-21 |
| Row 10 keeps the quoted-porcelain fallback; no policy exception for the NUL form (2026-10-21) | The fallback is documented behaviour; widening headless policy for one row proves less than it costs | Kept — Codex 2026-11-11 flags the filed row 10 sidecar as grouped rather than verbatim; open item for the next milestone |
| Rerun pins one full model id and is labelled a new baseline (2026-10-21) | The 2026-10-20 evidence never recorded its model, so replication is impossible to claim | Done — `rerun-2026-11-11-claude-sonnet-5-5` on Claude Code 2.1.310 |
| Conflict injection and logging composed outside the stub (2026-10-21) | Three of four research files agree; the conflict row then proves the real hash guard | Done — Phase 2 wrapper, exit sequence 0,0,0,3,0,3,0,0 reproduced |
| Visibility flip on bokiko's own go-word (2026-10-24) | bokiko gave the exact go-word in his own message; the main conversation ran the flip, never a subagent; flip tip 9a794e7, read-back 55835ad, secret scanning and push protection enabled | Decided 2026-10-24 |
| gitleaks stays on 8.30.0 (2026-10-24) | The pre-flip scan and the hooks were proven on this version; no reason to move it at the checkpoint | Decided 2026-10-24 |
| The two Claude Code files are published (2026-10-24) | `.claude/settings.json` (attribution suppression) and `.claude/CLAUDE.md` (no-trailer rule) are accepted as public files | Decided 2026-10-24 |
| 154 session-id-shaped UUIDs in evidence are accepted (2026-10-24) | They are identifiers, not credentials; no decisions line was requested | Decided 2026-10-24 |
| The shipped-digest-gap README bullet is published as drafted (2026-10-24) | Facts were verified against SKILL.md and the evidence tree; the bullet discloses that the shipped skill digest was never run by a matrix row | Decided 2026-10-24 |
| Eleven critical and warning review findings fixed after the flip (2026-10-24) | Hooks now fail closed on missing pattern files, non-executable checks and failed git calls; 29 test cases pass | Done 2026-10-24 |
| Default mode of `scripts/prepublish-check.sh` requires local deny-list entries (2026-10-24) | An empty deny list no longer passes silently; `--rehearse` keeps the old behaviour for dry runs | Done 2026-10-24 |
| Spike run roots live outside every home folder (2026-10-26) | S1 attempt 1 showed Claude Code loading the user's own `~/.claude/CLAUDE.md` and rules as Project instructions through ancestor traversal; the driver now defaults to a shared folder and refuses a home folder, so the isolation claim holds with evidence | Decided 2026-10-26 |
| Two S1 assertions refined (2026-10-26) | Three plugins ship inside the binary with source `@builtin`, and one user skill name is also defined by the binary; `no-non-builtin-plugins` and a binary-defined name counted as a collision keep the claim honest without a by-construction label | Decided 2026-10-26 |
| `.gitleaks.toml` home-path and hostname rules tightened to match the Python gate (2026-10-26) | Review CR-02 and WR-01: a home path before a JSON escape or delimiter and an upper-case host suffix were missed; parity test keeps both strings byte-identical; hook suite still 29 of 29 | Done 2026-10-26 |
| Spike spend 0.26 USD of the 5 USD cap; 21 review warnings and info items deferred to Phase 3 hardening (2026-10-26) | Both critical findings were closed by gap plan 02-09; the rest do not touch the zero-token suite or the decided spikes | Decided 2026-10-26 |
| Phase 3 spends only on bokiko's own `go` (2026-10-29) | The executor refused a relayed go and a detached worktree; a fresh executor was dispatched with the word quoted; the run cost 0.2723 USD against a 2.00 cap | Decided 2026-10-29 |
| `total_cost_usd` on a resumed call is cumulative (2026-10-29) | The committed fixtures and the real s2 per-model token counts both show s1 plus s2; the harness subtracts the previous total and the row figure of 0.2723 USD stands | Decided 2026-10-29 |
| The Bash write-escape rule is open-world and conservative (2026-10-29) | Every executed part whose program is not on a short read-only list is write-capable; a corpus test replays all 348 committed Bash calls with zero escapes; a false positive costs a run, a false negative files bad evidence, so the rule errs to exit 11; residual shapes are Phase 4 items, the backstop is the snapshot and realpath boundary | Decided 2026-10-29 |
| The filed 2026-10-29 baseline is frozen as filed (2026-10-29) | Later rule changes (status line, consistency line) are not back-filled; a fresh run files the new answers; evidence is never repaired | Decided 2026-10-29 |
| Paid waves run only on bokiko's own go word, by the main conversation (2026-11-03 to 2026-11-11) | Executors refuse a relayed go; wave A 0.79, B 1.43, C 0.75, D 2.37, row 7 triple 0.65, clean-clone matrix 5.75 USD, Phase 4 total 11.74 USD | Done |
| The clean-clone run carries the real HOME and `USER` into the child (2026-11-11) | `claude auth status` reads the macOS Keychain and reports loggedIn only with both; the harness still reads only the boolean | Done — 0bacd2b |
| Codex review filed `file-only`; the default comparison reference is not swapped to the new baseline (2026-11-11) | Codex gave no acceptance; its 21 verdict lines are recorded in `codex-review.md` with the model read from the Herdr pane (GPT-6-Astra, Codex CLI 0.167.0) | Decided 2026-11-11 |
| The row 7 pairings of the triple are rejected; attempt 3's unfenced entries are read at lower confidence (2026-11-11) | Codex: the older table does not validate the run; gap plan 04-22 added unfenced reading and `row7-review-part-2.md` | Decided 2026-11-11 |
| Frozen evidence is never edited after filing; the only later additions are verdict lines and review parts (2026-11-11) | Evidence integrity; `test_frozen_baseline.py` pins both baselines by digest | Done |
| Phases 1 to 3 re-verified at milestone close instead of an override closeout (2026-11-13) | Later phases changed their covered files, so the earlier reports read stale; fresh verifiers passed 5/5, 6/6 and 6/6 on the current tree | Done — v1.0 closed as verified_closeout |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-13 after v1.0 milestone*
