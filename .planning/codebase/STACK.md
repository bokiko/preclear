---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# Technology Stack

**Analysis Date:** 2026-10-21

## Languages

**Primary:**
- Markdown - the whole product. Skill instructions in `SKILL.md`, backend adapters in `references/*.md`, docs in `README.md` and `CHANGELOG.md`.

**Secondary:**
- YAML - the `Preclear configuration` fenced block users put in their `CLAUDE.md` (schema in `references/configuration.md`). Issue templates in `.github/ISSUE_TEMPLATE/`.
- JSON - example runtime settings in `tests/fixtures/hub-memory/runtime-settings.example.json` and `tests/fixtures/plain-memory/runtime-settings.example.json`.
- Shell/git commands - issued by the model at run time (read-only git, see below). No shell scripts ship in the repo.

## Runtime

**Environment:**
- Claude Code with skills enabled. `SKILL.md` frontmatter: `name: preclear`, `disable-model-invocation: true` (invoked only by typing `/preclear`), `allowed-tools: [Read, Write, Edit, Glob, Grep]`.
- The model interprets the Markdown at run time; there is no compiled or interpreted code, no server, no process.
- `git` on `PATH` is optional and used read-only (`status`, `log`, `rev-parse`, `branch`, `diff`).

**Package Manager:**
- None. No `package.json`, lockfile, or dependency manifest.
- Install is `git clone` into `~/.claude/skills/preclear` or `<repo>/.claude/skills/preclear` (see `README.md`).

## Frameworks

**Core:**
- Claude Code skill format (`SKILL.md` + `references/`) - the only framework.

**Testing:**
- None automated. `tests/acceptance.md` is a manual checklist ("There is no test runner"). Fixtures in `tests/fixtures/{plain-memory,hub-memory,bound-ledger}/`; reviewed transcripts in `tests/evidence/`.

**Build/Dev:**
- None. No build step, linter, formatter, or CI workflow (`.github/` holds only `pull_request_template.md` and issue templates).

## Key Dependencies

**Critical:**
- Claude Code skill loader - reads `SKILL.md` frontmatter and body.
- Optional `checkpoint-v1` ledger helper (external executable, user-supplied; contract in `references/checkpoint-v1.md`, verified against a 2026-10-04 build). Opt-in only through configuration.

**Infrastructure:**
- Not applicable.

## Configuration

**Environment:**
- No env files required. `.gitignore` excludes `.env`, `.env.*`.
- Optional user config: fenced YAML `Preclear configuration` block in project or user `CLAUDE.md`; keys `version`, `backend`, `executable`, `project`, `task`, `ledger`, `fallback_directory`. Claude Code does not parse it; the model reads it in SKILL.md Step 1 probe 4.
- Backend helper reads `CLAUDE_CODE_SESSION_ID` (or `--session`) to identify the session.

**Build:**
- None. Size budgets are enforced by the skill itself: checkpoint under 4,096 bytes, resume package under about 6,000 bytes.

## Platform Requirements

**Development:**
- Any editor; Claude Code to run the manual acceptance tests in `tests/acceptance.md`.

**Production:**
- A Claude Code installation; distributed via the GitHub repository (`bokiko/preclear`, license in `LICENSE`).

---

*Stack analysis: 2026-10-21*
