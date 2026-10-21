---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
<!-- refreshed: 2026-10-21 -->

# Architecture

**Analysis Date:** 2026-10-21

## System Overview

preclear is a Claude Code skill written entirely in Markdown. There is no compiled code and no test runner. The model reads `SKILL.md` and executes it as a procedure. Reference files are loaded only when a branch of the procedure needs them.

```text
┌─────────────────────────────────────────────────────────────┐
│  Entry: user types /preclear  (disable-model-invocation)     │
│  `SKILL.md`  (frontmatter + 5 steps + hard rules)            │
└────────┬───────────────────┬───────────────────┬────────────┘
         │ Step 1 probe 4     │ Step 3 destination │ Step 3 sidecar
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ configuration    │ │ checkpoint-v1    │ │ status-sidecar   │
│ `references/     │ │ `references/     │ │ `references/     │
│ configuration.md`│ │ checkpoint-v1.md`│ │ status-sidecar.md`│
└────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
         ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Outputs (in the user's project, never in this repo):         │
│ `<project>/.preclear/<task-slug>/checkpoint.md` + status.txt │
│ or a configured ledger written through a helper executable   │
│ then ONE resume line printed in the reply                    │
└─────────────────────────────────────────────────────────────┘
Verification: `tests/acceptance.md` + `tests/fixtures/` + `tests/evidence/`
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Procedure | Hard rules, five steps (discover, route, write, verify, emit) | `SKILL.md` |
| Configuration contract | `Preclear configuration` YAML block, three resolution states, fallback policy | `references/configuration.md` |
| Backend adapter | How to write a hash-guarded ledger through the `checkpoint` helper; preconditions, interface table, section assembly | `references/checkpoint-v1.md` |
| Sidecar formats | NUL-separated and quoted-porcelain `status.txt` rules | `references/status-sidecar.md` |
| Acceptance checklist | Manual harness rules and pass criteria | `tests/acceptance.md` |
| Fixtures | Copyable fake projects (plain, hub memory, bound ledger) | `tests/fixtures/` |
| Evidence | Frozen, sanitized transcripts and snapshots of accepted runs | `tests/evidence/` |
| Release notes | Keep-a-Changelog history | `CHANGELOG.md` |

## Pattern Overview

**Overall:** Prompt-as-program skill with progressive disclosure: one main procedure plus on-demand reference files.

**Key Characteristics:**
- Read-mostly: git is read-only, nothing is deleted, no `/clear` or compact, no binding, no installs (`SKILL.md` Hard rules).
- Pointer-not-copy: each fact has one owner; the checkpoint points at owners (`SKILL.md` Step 2 routing table).
- Honest gaps: unknowns are written as `UNCONFIRMED`; unverifiable stability is `UNSTABLE`; no authorized location is `BLOCKED`.
- Configuration activates backends; anything merely found is only a candidate (`SKILL.md` probe 4).
- Measure by command: byte caps are counted, not claimed (`SKILL.md` Step 4 item 5).
- Tool allowlist in frontmatter: `Read, Write, Edit, Glob, Grep` (Bash use is governed by the user's session permissions).

## Layers

**Procedure layer:**
- Purpose: the ordered steps the model follows.
- Location: `SKILL.md`
- Depends on: reference layer (loaded conditionally).
- Used by: the `/preclear` invocation.

**Reference layer:**
- Purpose: detail that applies only to some runs.
- Location: `references/`
- Contains: configuration schema, backend interface, sidecar formats.
- Used by: `SKILL.md` (Step 1 probe 4, Step 3 Destination and Sidecar).

**Verification layer:**
- Purpose: manual acceptance of behavior.
- Location: `tests/`
- Depends on: an installed skill and a Claude Code session.

## Data Flow

### Primary Request Path

1. User runs `/preclear` in the working session (`SKILL.md` frontmatter and intro).
2. Step 1 runs nine probes in order (conversation, location and git, instructions, configuration, memory, plan, ledger or handoff, issue or PR, pre-write check) with a cap of 20 candidate paths and 12,000 bytes for speculative lookups.
3. Step 2 routes each fact to its single owner (memory, plan, ledger, evidence file, sidecar).
4. Step 3 resolves destination: configuration first (`references/configuration.md`), then an established handoff location, then `<project>/.preclear/<task-slug>/checkpoint.md`, else print and mark `BLOCKED`.
5. The checkpoint is written with six fixed headings under 4,096 bytes; a `status.txt` sidecar is added when changes do not fit inline.
6. Step 4 re-captures branch, HEAD and porcelain status, subtracts preclear's own artifacts, rechecks digests, measures bytes.
7. Step 5 prints 2-3 sentences and exactly one fenced resume line; nothing after it.

### Backend path (checkpoint-v1)

1. Configuration state 2 (valid block) selects `backend: checkpoint-v1`.
2. Preconditions (session id, existing binding equals configured ledger, block names project and task) are checked via the helper's `status` (`references/checkpoint-v1.md`).
3. One body per helper section is assembled, validated with `validate --from`, then applied with `update --section --expect-section <hash>`; exit 3 means conflict.
4. Any failure falls to the fallback policy in `references/configuration.md`.

### Fresh-session resume

The pasted line points at the checkpoint. Its fixed `Resume reading` first and last lines carry verification and limits, so a session that never loads the skill still inherits them.

**State Management:**
- Mutable per-task file `checkpoint.md` (reread immediately before writing); optional frozen copy `checkpoint-<UTC>-<rand>.md` with same-suffix sidecars; no in-memory state.

## Key Abstractions

**Checkpoint (schema 1):**
- Purpose: bounded continuation record (six sections, 4,096 bytes).
- Examples: `SKILL.md` Step 3 Schema; fixture `tests/fixtures/bound-ledger/project/thoughts/ledgers/CONTINUITY_CLAUDE-widget-export.md`.
- Pattern: fixed headings with per-section byte caps.

**System status vocabulary:**
- `FOUND <path>`, `ABSENT`, `INACCESSIBLE`, `AMBIGUOUS`, `UNCONFIRMED`; outcome flags `UNSTABLE`, `BLOCKED`.

**Backend:**
- Purpose: named adapter that writes through an existing ledger system.
- Examples: `references/checkpoint-v1.md`.
- Pattern: config names backend, reference file defines commands and output table.

## Entry Points

**`/preclear`:**
- Location: `SKILL.md`
- Triggers: user only (`disable-model-invocation: true`).
- Responsibilities: runs in the main session, never a subagent.

## Architectural Constraints

- **Threading:** Not applicable; a single sequential model run.
- **Global state:** None in this repo. Concurrent sessions may share a checkpoint; the guard is reread-before-write and the helper's section hashes.
- **Circular imports:** Not applicable. References are one-directional from `SKILL.md`; `references/configuration.md` and `references/checkpoint-v1.md` cross-link each other.
- **Size limits:** checkpoint 4,096 bytes; resume line under 200 characters (hard 512); package 6,000 bytes.
- **Configuration is data only:** it can never carry a command or shell fragment (`references/configuration.md`).

## Anti-Patterns

### Copying owned facts into the checkpoint

**What happens:** Decisions, test output or memory text duplicated into the checkpoint.
**Why it's wrong:** Creates near-duplicates and breaches the byte caps.
**Do this instead:** Point at the owner using the `SKILL.md` Step 2 table.

### Guessing locations or bindings

**What happens:** Picking the newest ledger, deriving memory paths from a slug, guessing a session id.
**Why it's wrong:** Writes to another task's state.
**Do this instead:** Use explicit configuration or session binding; otherwise record `UNCONFIRMED`.

### Mutating state during resume

**What happens:** A resumed session binds or writes the ledger.
**Why it's wrong:** Resume is read-only for continuity state.
**Do this instead:** Follow the persisted rule in `references/checkpoint-v1.md` (Section assembly).

## Error Handling

**Strategy:** Degrade, never fabricate.

**Patterns:**
- Doubt stops that write, not the run (`SKILL.md` probe 9).
- Backend failure goes to the fallback policy; `fallback_directory: none` means `BLOCKED` and no resume line.
- Verification mismatch: correct and repeat once, then `UNSTABLE`.

## Cross-Cutting Concerns

**Logging:** Final printed report of artifacts, bytes, digests and every flagged item (`SKILL.md` Step 4).
**Validation:** Byte counts by command; schema reread; content digests for claimed tests.
**Authentication:** None; secrets are never written (`SKILL.md` Hard rules).

---

*Architecture analysis: 2026-10-21*
