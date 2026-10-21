---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# Codebase Structure

**Analysis Date:** 2026-10-21

## Directory Layout

```
preclear/
├── SKILL.md              # The skill: frontmatter plus the five-step procedure
├── README.md             # User-facing overview
├── CHANGELOG.md          # Keep-a-Changelog, [Unreleased] section
├── LICENSE
├── references/           # Conditionally loaded detail
│   ├── configuration.md
│   ├── checkpoint-v1.md
│   └── status-sidecar.md
├── tests/
│   ├── acceptance.md     # Manual checklist, no runner
│   ├── fixtures/         # Copyable fake projects
│   │   ├── plain-memory/
│   │   ├── hub-memory/
│   │   └── bound-ledger/
│   └── evidence/         # Frozen sanitized run records, dated folders
├── .github/              # Issue templates, PR template
├── .planning/codebase/   # GSD codebase maps
├── runs/                 # Gitignored local harness; not shipped
├── .backups/             # Gitignored hook backups; not shipped
└── .claude/              # Gitignored local hook state (tsc-cache); not shipped
```

## Directory Purposes

**`references/`:**
- Purpose: detail the main procedure points to rather than inlining.
- Contains: Markdown only.
- Key files: `references/configuration.md` (YAML block contract, resolution states, fallback), `references/checkpoint-v1.md` (helper interface and section assembly), `references/status-sidecar.md` (porcelain sidecar formats).

**`tests/fixtures/`:**
- Purpose: starting states copied to a scratch folder outside the repo before a test.
- Contains: each fixture has `README.md` and a `project/` tree with `CLAUDE.md`; `plain-memory` and `hub-memory` add `memory/` (with `MEMORY.md`), a plan, and `runtime-settings.example.json`; `bound-ledger` adds `thoughts/ledgers/CONTINUITY_CLAUDE-widget-export.md`; `hub-memory` adds `thoughts/plans/2026-10-15-widget-export.md`.

**`tests/evidence/`:**
- Purpose: tracked, sanitized records of accepted runs.
- Layout: `<scenario>-<YYYY-MM-DD>[-rerun]/` (`plain-memory-2026-10-19`, `hub-memory-2026-10-19`, `hub-memory-2026-10-19-rerun`, `bound-ledger-2026-10-19`, `bound-ledger-2026-10-19-rerun`, `publication-2026-10-20`). Each has a `README.md`; stage subfolders hold `snap-N-<stage>/` (`ledger.md`, `sha.txt`, `status.txt`), `sN-*-trace.md`, `digests.txt`, `lint-*.txt`.
- `*.log` files here are tracked via a `.gitignore` exception.

## Key File Locations

**Entry Points:**
- `SKILL.md`: the only file Claude Code loads on `/preclear`.

**Configuration:**
- `references/configuration.md`: the `Preclear configuration` block spec (users place the block in their own `CLAUDE.md`; this repo ships none).
- `.gitignore`: excludes `runs/`, `.backups/`, `.claude/tsc-cache/`, `.claude/cache/`, `.env*`, `*.log` (except evidence).

**Core Logic:**
- `SKILL.md`: procedure and checkpoint schema.
- `references/checkpoint-v1.md`: backend adapter.

**Testing:**
- `tests/acceptance.md`: harness rules and checks.
- `tests/fixtures/*/README.md`: per-fixture instructions.

## Naming Conventions

**Files:**
- Top-level docs UPPERCASE: `SKILL.md`, `README.md`, `CHANGELOG.md`.
- References lowercase kebab-case; backend files named `<backend>-v<N>.md`: `references/checkpoint-v1.md`.
- Plans dated `YYYY-MM-DD-<slug>.md`: `tests/fixtures/hub-memory/project/thoughts/plans/2026-10-15-widget-export.md`.
- Memory topic files prefixed by kind (`project_`, `feedback_`, `hub_`) with `MEMORY.md` index.
- Runtime artifacts: `checkpoint.md`, `status.txt`; frozen `checkpoint-<UTC-timestamp>-<4-char-random>.md`.

**Directories:**
- Lowercase kebab-case; evidence folders `<scenario>-<date>[-rerun]`.

## Where to Add New Code

**Change the procedure:**
- Edit `SKILL.md` in place; keep the six checkpoint headings and the byte caps consistent with `tests/acceptance.md`; add an entry under `[Unreleased]` in `CHANGELOG.md`.

**New backend:**
- Add `references/<name>-v1.md` (preconditions, interface table with observed output, section assembly, exit codes), add the name to "Known backends" in `references/configuration.md`, and add a fixture plus acceptance case.

**New reference detail:**
- Put it in `references/` and link it from the exact `SKILL.md` step that needs it; keep `SKILL.md` self-sufficient for the default path.

**New test scenario:**
- Fixture: `tests/fixtures/<scenario>/` with `README.md` and `project/`. Evidence: `tests/evidence/<scenario>-<date>/` with a `README.md`, sanitized paths, per-stage snapshots. Extend `tests/acceptance.md`.

## Special Directories

**`runs/`:**
- Purpose: local harness scripts and raw transcripts.
- Generated: Yes. Committed: No (gitignored); not part of the shipped project.

**`.backups/`:**
- Purpose: timestamped hook copies of edited files.
- Generated: Yes. Committed: No.

**`.claude/`:**
- Purpose: local Claude Code hook cache.
- Generated: Yes. Committed: No.

**`tests/evidence/`:**
- Purpose: acceptance proof.
- Generated: copied from runs after sanitizing. Committed: Yes.

---

*Structure analysis: 2026-10-21*
