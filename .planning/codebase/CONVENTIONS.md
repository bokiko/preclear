---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# Coding Conventions

**Analysis Date:** 2026-10-21

The project is a Claude Code skill written in Markdown. There is no compiled or interpreted source, so "code style" means how skill instructions, reference docs, fixtures and evidence are written. No formatter, linter or build step exists (no `package.json`, no lint config).

## Naming Patterns

**Files:**
- Skill entry point is `SKILL.md` (upper case, repo root). Frontmatter keys: `name`, `description`, `disable-model-invocation: true`, `allowed-tools: [Read, Write, Edit, Glob, Grep]`.
- Reference docs are lowercase kebab-case under `references/`: `references/checkpoint-v1.md`, `references/configuration.md`, `references/status-sidecar.md`. Backend docs carry the backend id and version (`checkpoint-v1`).
- Evidence folders: `tests/evidence/<layout>-<YYYY-MM-DD>[-rerun]/` (e.g. `tests/evidence/hub-memory-2026-10-19-rerun/`); publication rows: `tests/evidence/publication-2026-10-20/row<N><letter>-<case>[-first-pass|-rerun]/`.
- Stage-named evidence files: `s1-work.out`, `s2-preclear-trace.md`, `s2-preclear-prompt.md`, `s3-fresh-resume-trace.md`, `s5-repeat-preclear-trace.md`, `snap-<n>-<stage>/`, `measurements.md`, `digests.txt`, `lint-after-s<n>.txt`.
- Fixtures: `tests/fixtures/<layout>/` with a `README.md`, a `project/` tree, and `runtime-settings.example.json` where memory is pinned.

**Task and checkpoint identifiers:**
- Task slugs are lowercase kebab-case (`widget-export`); collisions append `-2`, `-3`.
- Frozen copies: `checkpoint-<UTC-timestamp>-<4-char-random>.md`.
- Checkpoint id: `<task-slug>-<UTC-timestamp>`.

**Status words (fixed vocabulary, upper case, in backticks):** `FOUND <path>`, `ABSENT`, `INACCESSIBLE`, `AMBIGUOUS`, `UNCONFIRMED`, `UNSTABLE`, `BLOCKED`. Use exactly these; never invent synonyms.

## Code Style

**Formatting:**
- Plain Markdown, hard-wrapped near 80-85 columns in `SKILL.md` and `references/*.md`.
- Bullets use `-`. Numbered lists for ordered probes/steps. Tables for routing and schemas (`SKILL.md` Step 2 and the Step 3 schema table).
- Bold lead-ins for rule names (`**Git is read-only.**`, `**Frozen copy.**`, `**Sidecar.**`).
- Headings: `## Hard rules`, `## Step N: <title>`; sub-steps `###`. Keep the six checkpoint headings verbatim: `## Identity and state`, `## Boundaries and blockers`, `## Next action`, `## Resume reading`, `## Evidence and working changes`, `## Do not redo`.
- Command and path literals in backticks; example config in fenced blocks (use four-backtick fences when nesting a triple-backtick block, see `references/configuration.md`).
- Byte arithmetic uses thousands separators in prose tables (`4,096`), plain digits in evidence files.

**Linting / size gates:**
- `SKILL.md` has a 12,000-byte ceiling (currently 11,994 bytes; essentially no headroom). Check with `wc -c SKILL.md` before committing; the PR template at `.github/pull_request_template.md` enforces it.
- No absolute home paths or private hostnames in tracked files (PR template checklist). Evidence uses sanitized tokens: `<run>`, `<helper>`, `<repo>`, `<home>`, `<scratch>`, `<auto-memory-root>`.
- `.gitignore` excludes `runs/` (local harness), `*.log` except `tests/evidence/**/*.log`, `.env*`, `.claude/cache/`, `.backups/`.

## Import Organization

Not applicable. Cross-file references are by repo-relative path in backticks (`references/configuration.md`), and `SKILL.md` loads a reference only when a condition holds (e.g. `references/checkpoint-v1.md` only when the configuration names `backend: checkpoint-v1`).

## Error Handling

Instruction-level patterns the skill prescribes (follow them when editing):
- Unknown means write `UNCONFIRMED`; never guess or invent state.
- Doubt stops that write, not the whole run.
- Doubt about a destination falls through to the next authorized one; no authorized location yields `BLOCKED` and no resume line.
- Verification mismatch: correct and repeat once; still changing is `UNSTABLE`. Never fabricate stability.
- After a denied write, use an already-authorized alternative; never alter syntax to bypass a restriction.
- Backend failure follows the `fallback_directory` policy in `references/configuration.md`; output that does not match the documented table is a failure.
- Helper exit codes are documented in `references/checkpoint-v1.md` (0 ok, 1 internal, 2 usage/validation, 3 conflict, 4 invalid, 5 kill switch, 6 lock timeout).

## Logging

Not applicable at runtime. Evidence logs (wrapper call logs, `injection.log`) live in `tests/evidence/**` and are the only tracked `.log` files.

## Comments

- Documents state current behavior only; history belongs in `CHANGELOG.md` (Keep a Changelog format, single `[Unreleased]` section).
- Say why a limit exists (e.g. caps are a proxy for the 2,000-token target; "Frozen is a convention unless the filesystem enforces it").
- Convert relative dates to absolute in everything written (a skill rule and an evidence convention).

## Function Design

Not applicable. The analogue is skill step design: numbered steps with a single owner per fact (routing table in `SKILL.md` Step 2), one presently authorized next action, one fenced single-line resume block as the final output.

## Module Design

- `SKILL.md` is the only always-loaded file; keep it generic (no author-specific paths or tooling). Author-specific or optional behavior goes in `references/` and is loaded conditionally.
- Hard limits: checkpoint <=4,096 bytes, resume line <=512 bytes (target <200 chars), package <=6,000 bytes. Per-section caps are in the Step 3 table of `SKILL.md`; edits to one cap must keep the sum consistent with the total.
- Git is read-only, nothing is deleted, no secrets written. These rules are binding on any helper and must remain in `SKILL.md` "Hard rules".
- Changelog entries go under `### Added` in `CHANGELOG.md`; commit messages are plain imperative sentences (e.g. "Run publication rows 5-12; document the quoted-porcelain sidecar fallback").

---

*Convention analysis: 2026-10-21*
