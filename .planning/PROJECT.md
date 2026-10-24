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

### Active

- [ ] A stranger with Claude Code can clone the repo and rerun the full acceptance matrix (three layouts plus twelve publication rows) from the committed harness, without the owner's private checkpoint helper
- [ ] A test-only stub helper in `tests/` implements the `checkpoint-v1` interface described in `references/checkpoint-v1.md` closely enough that the backend rows exercise the same branches they exercised against the real helper
- [ ] Row 7 has a clean rerun whose printed checkpoint carries no unsupported Do-not-redo entry
- [ ] A rerun produces evidence in the committed evidence format (sanitized traces, full traces, snapshots, measurements) so results can be compared row for row with the existing evidence
- [ ] The harness never deletes or overwrites an existing run root and never writes a home path, hostname or credential into committed evidence

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
- A private audit record (2026-10-20) found no credentials, keys, IP addresses, hostnames or real name anywhere in history or the tree. One medium finding: ten evidence lines with home-folder paths in commit d437af2, sanitized in the next commit.
- `.planning/` is committed to this repo, so planning artifacts become public with it.

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
| Ship a test-only stub helper for backend rows | Lets strangers run the full matrix without the private helper; real helper stays private | — Pending |
| Done means a full matrix rerun from a clean clone | Committed scripts alone would not prove reproducibility | — Pending |
| No CI this milestone | API-key secret and per-run token cost; local reproducibility first | — Pending |
| No history rewrite (2026-10-21) | The d437af2 commit adds eleven home-folder path lines across ten files (measured 2026-10-21; earlier text said ten lines); they reveal only a folder name and SHA citations stay valid; the scan accepts exactly those 15 fingerprints through `.gitleaksignore`, and a new finding halts the phase and goes to bokiko | Decided 2026-10-21 |
| `bokiko <bokiko@gmail.com>` is the public identity (2026-10-21) | The address is already the public GitHub identity; all 14 pre-phase commits carry it as the only author and committer; each clone pins it with `user.useConfigOnly` and `preclear.pinnedIdentity` | Decided 2026-10-21 |
| Row 7 ships as a disclosed known issue, rerun three times in this milestone (2026-10-21) | A single clean run cannot show a stochastic defect is fixed | Decided 2026-10-21 |
| Row 10 keeps the quoted-porcelain fallback; no policy exception for the NUL form (2026-10-21) | The fallback is documented behaviour; widening headless policy for one row proves less than it costs | — Pending |
| Rerun pins one full model id and is labelled a new baseline (2026-10-21) | The 2026-10-20 evidence never recorded its model, so replication is impossible to claim | — Pending |
| Conflict injection and logging composed outside the stub (2026-10-21) | Three of four research files agree; the conflict row then proves the real hash guard | — Pending |
| Visibility flip on bokiko's own go-word (2026-10-24) | bokiko gave the exact go-word in his own message; the main conversation ran the flip, never a subagent; flip tip 9a794e7, read-back 55835ad, secret scanning and push protection enabled | Decided 2026-10-24 |
| gitleaks stays on 8.30.0 (2026-10-24) | The pre-flip scan and the hooks were proven on this version; no reason to move it at the checkpoint | Decided 2026-10-24 |
| The two Claude Code files are published (2026-10-24) | `.claude/settings.json` (attribution suppression) and `.claude/CLAUDE.md` (no-trailer rule) are accepted as public files | Decided 2026-10-24 |
| 154 session-id-shaped UUIDs in evidence are accepted (2026-10-24) | They are identifiers, not credentials; no decisions line was requested | Decided 2026-10-24 |
| The shipped-digest-gap README bullet is published as drafted (2026-10-24) | Facts were verified against SKILL.md and the evidence tree; the bullet discloses that the shipped skill digest was never run by a matrix row | Decided 2026-10-24 |
| Eleven critical and warning review findings fixed after the flip (2026-10-24) | Hooks now fail closed on missing pattern files, non-executable checks and failed git calls; 29 test cases pass | Done 2026-10-24 |
| Default mode of `scripts/prepublish-check.sh` requires local deny-list entries (2026-10-24) | An empty deny list no longer passes silently; `--rehearse` keeps the old behaviour for dry runs | Done 2026-10-24 |

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
*Last updated: 2026-10-24 after Phase 1*
