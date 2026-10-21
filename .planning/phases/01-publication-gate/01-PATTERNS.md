# Phase 1: Publication Gate - Pattern Map

**Mapped:** 2026-10-21
**Files analyzed:** 19 new or modified
**Analogs found:** 8 repo analogs for 19 files; the remaining files copy the tested excerpts in `01-RESEARCH.md` (the repo has no hooks, no config tooling, no top-level scripts)

All analog paths below were confirmed git-tracked with `git ls-files`. `.claude/` holds only untracked `tsc-cache`, so there is no mirror-path risk. Paths are repo-relative. The owner is bokiko only.

The repo is a Markdown skill with no source code. The only shell in it is test apparatus under `tests/evidence/`. The hook and check scripts are therefore new in kind, and `01-RESEARCH.md` Patterns 1 to 3 (tested on gitleaks 8.30.0) are the primary source for them. Repo analogs supply style: header comments, wrapper idiom, log lines, doc voice and conventions.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.gitleaks.toml` | config | transform (regex scan rules) | none in repo; RESEARCH Pattern 1 | no analog |
| `.gitleaksignore` | config | batch (15 immutable fingerprints) | none in repo; RESEARCH "Generating .gitleaksignore" | no analog |
| `.githooks/pre-commit` | hook | request-response (staged diff to exit code) | RESEARCH Pattern 2 text; style from `tests/evidence/publication-2026-10-20/row11-concurrent-change-rerun/wrapper-git.sh` | partial |
| `.githooks/commit-msg` | hook | request-response | same | partial |
| `.githooks/pre-push` | hook | event-driven (stdin ref protocol, fan-out) | RESEARCH Pattern 2 | no repo analog |
| `.githooks/checks/leaks.sh` | utility | batch | RESEARCH Pattern 2 | no repo analog |
| `.githooks/checks/identity.sh` | utility | batch | RESEARCH Pattern 2 | no repo analog |
| `.githooks/checks/denylist.sh` (optional) | utility | batch | RESEARCH "Optional local deny list" | no repo analog |
| `.githooks/attribution.ere` | config | transform | RESEARCH Pattern 2 | no repo analog |
| `.githooks/README.md` | doc | n/a | `README.md` (Safety/Tests sections) and `tests/acceptance.md` | role-match |
| `scripts/test-hooks.sh` | test | file-I/O (throwaway clone, PASS/FAIL lines) | RESEARCH Pattern 3 table; wrapper idiom from `wrapper-checkpoint.sh` | partial |
| `scripts/prepublish-check.sh` | utility | batch (read-only mirror scan and inventory) | RESEARCH "Code Examples" mirror scan and inventory | no repo analog |
| `.claude/settings.json` | config | n/a | `tests/evidence/publication-2026-10-20/row10-large-status-rerun/settings.json` (JSON shape only) | partial |
| `CLAUDE.md` or `.claude/CLAUDE.md` | config (instructions) | n/a | `tests/fixtures/plain-memory/project/CLAUDE.md` | role-match |
| `README.md` (Known issues section, Roadmap) | doc | n/a | `README.md` lines 268-285 | exact (self) |
| `CHANGELOG.md` (`[Unreleased]` entry, fix the "stays private" sentence) | doc | n/a | `CHANGELOG.md` lines 6-30 | exact (self) |
| `.planning/PROJECT.md` Key Decisions rows | doc | CRUD (table rows) | `.planning/PROJECT.md` Key Decisions table, lines ~67-79 | exact (self) |
| `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md` | doc | batch (generated record) | `tests/evidence/bound-ledger-2026-10-19/main/digests.txt` and evidence READMEs | role-match |
| `.github/pull_request_template.md` (optional touch) | doc | n/a | itself | exact |

## Pattern Assignments

### `.gitleaks.toml`, `.gitleaksignore`, `.githooks/pre-push`, `checks/leaks.sh`, `checks/identity.sh`, `attribution.ere`, `pre-commit`, `commit-msg` (no repo analog)

**Source:** `01-RESEARCH.md` lines 172-302 (Pattern 1 config, Pattern 2 scripts). They were tested end to end. Copy them as written, with three adjustments:
- In the `email-address` allowlist, replace `<public-email-escaped>` with the address from `.planning/PROJECT.md` (Key Decisions identity row, line ~75), dots escaped. Never spell the address in a plan or summary.
- Keep the `# shellcheck disable=SC2034` and `SC2086` annotations; run `shellcheck -s sh`.
- Run gitleaks with `--exit-code 2` (1 means tool error), `--redact`, and a `command -v gitleaks` guard that exits 1 (fail closed).

Commit modes as 100755 (`git ls-files -s .githooks`). Enable with `git config core.hooksPath .githooks`. Pin the identity in the owner clone with `git config --local user.useConfigOnly true`, local `user.name`, `user.email`, and `preclear.pinnedIdentity`.

**Repo style to match in these scripts** (from `row11-concurrent-change-rerun/wrapper-git.sh` lines 1-5): a shebang, then a one-comment header stating purpose and scope, then `W="$(cd "$(dirname "$0")" && pwd)"` for self-location:
```bash
#!/bin/bash
# TEST APPARATUS ONLY. Passes every call to the real git unchanged. ...
REAL=/usr/bin/git
W="$(cd "$(dirname "$0")" && pwd)"
```
Hooks use `#!/bin/sh` and POSIX only, because RESEARCH tested them under macOS `/bin/sh` (bash 3.2). The existing evidence wrappers use `#!/bin/bash`; do not copy that for hooks.

### `scripts/test-hooks.sh` (test, file-I/O)

**Analog:** RESEARCH Pattern 3 table (lines 304-318) defines the 10 cases and expected exit codes. Output contract from RESEARCH Validation Architecture: one `PASS <name>` or `FAIL <name>: <reason>` line per check, non-zero exit on any FAIL.

**Wrapper and logging idiom** (`tests/evidence/publication-2026-10-20/row3a-missing-executable/wrapper-checkpoint.sh` lines 1-7):
```bash
printf '%s CALL' "$(date -u +%FT%TZ)" >> "$W/calls.log"; printf ' %q' "$@" >> "$W/calls.log"; echo >> "$W/calls.log"
"$REAL" "$@"; rc=$?
echo "$(date -u +%FT%TZ) EXIT $rc" >> "$W/calls.log"
exit $rc
```
Use UTC `date -u +%FT%TZ` stamps and capture `rc` the same way.

Rules for this file (RESEARCH Pitfall 7 and Pattern 3):
- Throwaway clone: `T=$(mktemp -d)`, a bare remote inside `$T`, `origin` pointed at the bare path. Never `git push` to the real `origin`.
- Build fake secrets, home paths, IPs, hostnames and emails at runtime from fragments (for example the `AKIA` plus fragment form). A literal in the script would be blocked and would reach public history.
- No `rm -rf` on existing paths. The project rule is no `rm -rf` on existing run roots and exclusive creation (see PROJECT.md Constraints, "Harness safety"). Use a new `mktemp -d` and leave it.
- Never pass `--no-verify` to a push to `origin`. The `--no-verify` commits inside the throwaway clone are the intended bypass tests only.

### `scripts/prepublish-check.sh` (utility, batch, read-only)

**Source:** RESEARCH "Mirror scan, strict and gate" (lines 380-409) and "Read-only live-repo inventory" (lines 423-450). Copy the strict run (ignore dir empty), the gate run (ignore file on), the one-identity check, and the `python3 -I` set-equality check (found fingerprints must equal the non-comment `.gitleaksignore` lines, 15). Also copy the `gh api` and `git ls-remote` inventory list with its expected baseline values.

Constraints: no `gh repo edit`, no write API, no push. It records the scanned tip SHA. Config and ignore file come from `git show HEAD:...` of the mirror. Print counts and file names only, never matched values (`--redact`, reports kept outside the repo). Same PASS/FAIL line contract.

### `.claude/settings.json` (config)

**Analog (JSON shape only):** `tests/evidence/publication-2026-10-20/row10-large-status-rerun/settings.json`: a flat, two-space-indented JSON object with no comments. Write the content from RESEARCH Pitfall 1:
```json
{"attribution": {"commit": "", "pr": "", "sessionUrl": false}}
```
Pretty-print it to match. Note that `.gitignore` ignores only `.claude/tsc-cache/` and `.claude/cache/`, so `.claude/settings.json` is trackable without a `.gitignore` change. Do not use `"attribution": false`, which needs Claude Code 2.1.281 or later.

### `CLAUDE.md` or `.claude/CLAUDE.md` (instruction file)

**Analog:** `tests/fixtures/plain-memory/project/CLAUDE.md` is a one-line, plain-prose instruction file with no frontmatter: "Project memory lives in ./memory. MEMORY.md is its flat index; ..." Follow that voice: one sentence, imperative, for example "Commits in this repo carry no co-author or generated-by trailer." `.planning/config.json` has `claude_md_path: "./.claude/CLAUDE.md"`, so place it there unless bokiko prefers the repo root (RESEARCH Open Question 6). It must not contain a home path, hostname or the address.

### `README.md` Known issues section and Roadmap (doc)

**Analog:** `README.md` itself. Insert `## Known issues and limits` above `## Roadmap` (line 275). Match the existing Roadmap list syntax (lines 277-282):
```markdown
- [x] Twelve-row publication matrix run and reviewed (2026-10-20)
- [ ] Clean rerun of publication row 7 (unsupported Do-not-redo entry)
- [ ] Public release
```
Keep the open row 7 item open, and leave "Public release" unchecked until the flip happens on bokiko's word. Body text is the "Minimal shape" block in RESEARCH lines 528-543: bold lead-in per item, `-` bullets, backticked literals, hard-wrapped near 85 columns, absolute dates only. Do not edit anything under `tests/evidence/`.

### `CHANGELOG.md` (doc)

**Analog:** `CHANGELOG.md` `[Unreleased]` / `### Added` (lines 6-30). Add bullets under the existing `### Added`, in the existing style: plain bullets, continuation lines indented two spaces, dates in parentheses, repo-relative paths in backticks. No new section, because the convention is a single `[Unreleased]` section (`.planning/codebase/CONVENTIONS.md`, Comments).

**Must fix:** the existing sentence at lines 27-28 says "The repository stays private until the public-content and history audit is accepted and publication is explicitly approved". RESEARCH flags it as becoming false at the flip. Update it in the disclosure commit and push it before the flip. Check with `git merge-base --is-ancestor <disclosure-sha> <tip-at-flip>`.

### `.planning/PROJECT.md` Key Decisions rows (PUB-01)

**Analog:** the same table, lines ~67-79. Row format:
```markdown
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| No history rewrite; `bokiko <...>` stays the public identity (2026-10-21) | The ten d437af2 lines reveal only a folder name; ... | — Pending |
| Row 7 ships as a disclosed known issue, rerun three times in this milestone | A single clean run cannot show a stochastic defect is fixed | — Pending |
```
Actions per RESEARCH "PROJECT.md edit targets":
- Split the combined history and identity row into two rows.
- Give row 7 a date, after bokiko confirms 2026-10-21 (A3).
- Replace `— Pending` with a decided outcome on those three rows.
- Fix counts: 14 commits, and "eleven lines in ten files". Mechanical check: three rows, each containing `2026-10-21`, none ending in `Pending`.
- Optionally add one line accepting the 154 session-id UUIDs (Open Question 5).

Neighbouring rows already use `(2026-10-21)` placed in the Decision cell; copy that placement. Leave the other `— Pending` rows alone.

### `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md` (generated record)

**Analog:** `tests/evidence/bound-ledger-2026-10-19/main/digests.txt` (sha256 followed by two spaces and a label) and the evidence READMEs. The record states the scanned tip SHA, the expected-versus-observed value of each inventory command, and the exit codes of the strict and gate runs. Generated by `scripts/prepublish-check.sh`, committed and pushed last. Assert `git diff --name-only <scanned-tip> HEAD` lists only this file. Repo-relative paths only, with no home path or hostname.

### `.githooks/README.md` (doc)

**Analog:** the `README.md` Safety and Tests sections (voice: short, imperative, backticked commands) and the "How to run" numbered list in `tests/acceptance.md`. Content (RESEARCH Pitfalls 2 and 6, Open Question 7):
- The one enable command.
- The 3 owner pin commands.
- How to run `sh scripts/test-hooks.sh`.
- "8.30.x tested on 8.30.0".
- Hooks are a safety net, not enforcement. `--no-verify` skips them, and GitHub push protection covers secrets only after the flip.

## Shared Patterns

### No identifiers in tracked text
**Source:** `.github/pull_request_template.md` ("No absolute home paths or private hostnames in new files") and `.planning/codebase/CONVENTIONS.md` (sanitized tokens `<run>`, `<helper>`, `<repo>`, `<home>`, `<scratch>`).
**Apply to:** every new file, including plans, summaries and `.planning/phases/01-publication-gate/*`. Describe path shapes in words. Run `gitleaks dir` on each new planning file before committing (RESEARCH Pitfall 7).

### Commit authorship and message style
**Source:** `.planning/codebase/CONVENTIONS.md` ("commit messages are plain imperative sentences", for example "Run publication rows 5-12; document the quoted-porcelain sidecar fallback") and PROJECT.md Constraints ("authored solely by bokiko, no AI attribution lines").
**Apply to:** every commit made by an executor of any plan.
**Conflict to surface:** this session's harness reminder asks for a `Co-Authored-By` trailer on commits. That contradicts the locked constraint and PUB-04. The planner must put "no trailer" in every commit task. The pre-push check and `attribution.ere` will refuse it. Commits are made without `--no-verify`.

### Frozen files and size gate
**Source:** `.planning/codebase/CONVENTIONS.md`. `SKILL.md`, `references/` and `tests/fixtures/` are frozen. `SKILL.md` stays at or under 12,000 bytes (`wc -c SKILL.md` gives 11,994). Historical evidence under `tests/evidence/` is never edited.
**Apply to:** all plans. Add a verify step that `git diff --name-only` touches none of these paths.

### Human gate for destructive and visibility actions
**Source:** PROJECT.md Constraints (Authorization) and RESEARCH Pitfall 8.
**Apply to:** plan 01-03. `gh repo edit --visibility public ...`, any history rewrite and any deletion are never in a task `<action>` or script. The plan ends at a checkpoint that prints evidence and waits for bokiko's go-word in his own message. The flip commands appear only in the checkpoint's "on approval" note, for the main conversation to run. `.planning/config.json` has `mode: yolo` and `human_verify_mode: end-of-phase`, so make 01-03 `autonomous: false`.

### Fail closed and distinguish findings from errors
**Source:** RESEARCH Anti-Patterns and Security Domain.
**Apply to:** all hook and check scripts. Missing gitleaks means exit 1. A finding means exit 2 via `--exit-code 2`. Use `--redact` everywhere. Never commit a gitleaks JSON report.

### PASS/FAIL line output
**Source:** RESEARCH Validation Architecture.
**Apply to:** `scripts/test-hooks.sh` and `scripts/prepublish-check.sh`. Quick run is `sh scripts/test-hooks.sh`. Full run is both scripts.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.gitleaks.toml`, `.gitleaksignore` | config | transform | no scanner config exists; use RESEARCH Pattern 1 |
| `.githooks/*` (pre-commit, commit-msg, pre-push, checks, attribution.ere) | hook/utility | event-driven | no hooks exist in the repo (`core.hooksPath` unset); use RESEARCH Pattern 2 |
| `scripts/` directory | utility/test | batch | no tracked top-level scripts; the only `.sh` files are evidence wrappers, which serve as style hints only |
| `scripts/prepublish-check.sh` | utility | batch | use RESEARCH mirror scan and inventory code |

## Plan-split notes (from RESEARCH)

- 01-01 owns `.githooks/pre-push`, `checks/identity.sh`, `attribution.ere`, `commit-msg`, `.claude/settings.json`, the `CLAUDE.md` line, the identity pin docs and the PROJECT.md rows (PUB-01, PUB-04).
- 01-02 owns `.gitleaks.toml`, `.gitleaksignore`, `pre-commit`, `checks/leaks.sh`, `scripts/test-hooks.sh` and the optional `checks/denylist.sh` (PUB-02, PUB-03). It depends on the 01-01 scaffold. Run the plans sequentially.
- 01-03 owns `scripts/prepublish-check.sh`, the disclosure edits to `README.md` and `CHANGELOG.md`, the inventory record, and the final checkpoint (PUB-05, PUB-06, PUB-07).
- `.githooks/README.md` is best written in 01-02, once the tests exist.

## Metadata

**Analog search scope:** whole tracked tree (`git ls-files`, about 1,294 files, of which 1,246 are under `tests/evidence`), `.github/`, `.claude/`, `.planning/codebase/CONVENTIONS.md`, `README.md`, `CHANGELOG.md`, `.gitignore`, `.planning/config.json`.
**Files scanned:** about 12 read in full or in part; the rest enumerated by `git ls-files`.
**Pattern extraction date:** 2026-10-21
