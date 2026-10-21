---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# External Integrations

**Analysis Date:** 2026-10-21

## APIs & External Services

**Network services:**
- None. The skill makes no HTTP calls and holds no API keys.

**Optional tooling (only if already configured and authorized, SKILL.md Step 1 probe 8):**
- Linked issue or PR lookup via an existing tool. No login, broad search, or external writes.

**Local helper backend:**
- `checkpoint-v1` ledger helper - hash-guarded checkpoint block inside a Markdown continuity ledger.
  - Contract: `references/checkpoint-v1.md` (commands `status`, `show`, `validate`, `update`, `note`, `lint`, `handoff`; exit codes 0-6)
  - Activated only by a valid `Preclear configuration` block with `backend: checkpoint-v1` (`references/configuration.md`)
  - Auth/identity: session id from `CLAUDE_CODE_SESSION_ID` or `--session`; binding is a user-performed setup action, never done by preclear

**Git (local, read-only):**
- `git status/log/rev-parse/branch/diff`; sidecar capture via `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` (fallback format in `references/status-sidecar.md`). Mutating git commands are forbidden by SKILL.md hard rules.

## Data Storage

**Databases:**
- None.

**File Storage:**
- Local filesystem only. Default output `<project>/.preclear/<task-slug>/checkpoint.md`, optional `status.txt` sidecar and frozen `checkpoint-<UTC-timestamp>-<4-char-random>.md` copies. Reads (never invents) user memory roots, plans, and ledgers/handoffs the session or configuration names.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. Authorization comes from the user's instructions, configuration, and Claude Code permission prompts. A resume line authorizes only the checkpoint's next action.

## Monitoring & Observability

**Error Tracking:**
- None.

**Logs:**
- Sanitized helper and git call logs kept as `.log` evidence under `tests/evidence/` (the `.gitignore` exception `!tests/evidence/**/*.log`).

## CI/CD & Deployment

**Hosting:**
- GitHub repository `bokiko/preclear` (remote `origin`). README banner image is fetched from `capsule-render.vercel.app` (docs only, not runtime).

**CI Pipeline:**
- None. Manual acceptance testing per `tests/acceptance.md`.

## Environment Configuration

**Required env vars:**
- None for the default plain-file mode. `CLAUDE_CODE_SESSION_ID` only for the `checkpoint-v1` backend.

**Secrets location:**
- Not applicable. The skill must never write secrets anywhere (SKILL.md hard rules).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-10-21*
