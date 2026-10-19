## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261019T091321Z
project: <scratch>/project (git toplevel, not a linked worktree)
task: widget-export
objective: Add widget export per thoughts/plans/2026-10-15-widget-export.md; format decision changed to JSON-default on 2026-10-19.
result: Plan step 2 done (csv_exporter.py, untested, uncommitted). JSON-default diff drafted 2026-10-19, saved as sidecar proposed-json-default.diff, presented for review. Not applied; user has not yet approved.
branch: main
HEAD: 3d9865fbf0268f7ac276d6e580c8d1ffb9a0bac7
untracked-notice: sent

## Boundaries and blockers
- Do not run tests, stage, or commit.
- Do not apply the JSON diff to the tree until the user approves it.
- Do not start plan step 3 (empty-input test).
- Keep exporter functions small and pure (memory/feedback_small_pure_functions.md).
- UNCONFIRMED: plan step 1 is checked but no column list exists in the repo; COLUMNS (id, name, created_at) is an assumption.
- UNCONFIRMED: `git apply --check` of the sidecar diff not run (needed approval); hunk counts checked by hand only.
- Detail: memory/project_widget_export.md; thoughts/plans/2026-10-15-widget-export.md

## Next action
In the project directory, ask the user to approve, amend, or reject .preclear/widget-export/proposed-json-default.diff (JSON default via export(); CSV only with fmt="csv"; new json_exporter.py; __init__.py re-exports). Complete when the user answers. Do not apply, test, or commit before that.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
1. .preclear/widget-export/proposed-json-default.diff (whole file)
2. memory/project_widget_export.md (whole file)
3. widget_export/*.py only if amending the diff; plan file only if plan state is in question.
Then execute Next action within Boundaries; leave this checkpoint unchanged until the next `/preclear`.

## Evidence and working changes
Status at HEAD 3d9865f (2026-10-19T09:13Z): staged 0, unstaged 3, untracked 5, conflicted 0, changed submodules 0.
Unstaged (edited by preclear 2026-10-19, unchanged this session): memory/project_widget_export.md, memory/hub_projects.md, thoughts/plans/2026-10-15-widget-export.md.
Untracked, written by the 09:09 session, unchanged since:
- widget_export/csv_exporter.py sha256 b70138dd75181d6603de6ad549517682054f7e26c3965985f32a3b93f1c061da
- widget_export/__init__.py sha256 0ca2cdeb412dab3c551269263ef58cf48c92a9a6d5c897cd0fed5f6b6a334c68
Untracked, ownership unknown (pre-session): .claude/skills/preclear/{SKILL.md,references/checkpoint-v1.md,references/configuration.md}.
Preclear artifacts: .preclear/widget-export/checkpoint.md; .preclear/widget-export/proposed-json-default.diff sha256 8c13ed44f62b04be73c43bbb04fd91c11b675d4512d1096663a527e6c38a67f1 (base: the two digests above).
Verification: none run; user forbade tests. binding UNCONFIRMED.

## Do not redo
- Repo survey (2026-10-19, HEAD 3d9865f): no source, tests, package config, column list, or ledger before the first session. Evidence: `git ls-files`. Invalidated by a new commit.
- No `Preclear configuration` block in CLAUDE.md; no CLAUDE.local.md, AGENTS.md, rules, or .claude/settings*.json (rechecked 2026-10-19 09:13Z). Invalidated if CLAUDE.md or .claude/ changes.
- Memory layout: MEMORY.md lists hubs only; hub_*.md index topics; topic files carry frontmatter. Invalidated if memory/ changes.
- JSON diff drafted: see sidecar. Invalid if widget_export/ digests change.
