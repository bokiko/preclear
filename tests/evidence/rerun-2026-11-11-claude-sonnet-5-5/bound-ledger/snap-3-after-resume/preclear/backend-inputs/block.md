<!-- CHECKPOINT:BEGIN updated: 1970-01-01T00:00:00Z by: preclear -->
## Goal & current state
widget-export in <run>/project (branch main, HEAD 1776be476c7f3e8dea3b7849b3b161e9b668bdd2).
Plan steps 1-2 done: widget_export.py (untracked, Python, pure funcs escape_field/widget_to_row/widgets_to_csv, columns id,name) writes CSV. Untested (tests not authorized).
PENDING FORMAT CHANGE: JSON is now the default export; CSV only on explicit request. Code is still CSV-only. Step 3 (empty-input test) not started; wait for the format decision.

## Decisions (with reasons)
2026-11-11 user correction, supersedes "CSV first, JSON deferred": JSON is the default export format; CSV only on explicit request. Why: downstream owner confirmed the consumer migrated to a JSON API in the week of 2026-10-12. Applies to future sessions.
Do not redo: CSV exporter is written (widget_export.py sha256 1661f3bc65a69c034c6fc5172570c9f89ab83b3995ed8c57286988968f9ef477); invalid if that file changes.

## Blockers & open questions
Pending: user review of the proposed JSON-default diff (not yet drafted). Plan file not yet updated for the format change (plan update pending).
UNCONFIRMED: the checkpoint helper prints a "STUB-BACKED test apparatus" banner, so its interface was not verified against the documented build.

## Authorization boundaries
Resume is read-only for continuity state: never bind. Update, note, or handoff only during an explicit `/preclear`; setup is a separate user action. Read the ledger file directly, or use `show --ledger <absolute-ledger-path>` without binding.
Next action is a diff in the reply only: no proposal files, section-input files, binding changes, or ledger writes. No tests, commits, pushes, or applying the diff until the user says so. Earlier "edit files inside project" scope is historical.
Detail: thoughts/plans/2026-10-15-widget-export.md

## Evidence & key paths
Resume is read-only for continuity state: never bind. Update, note, or handoff only during an explicit `/preclear`; setup is a separate user action. Read the ledger file directly, or use `show --ledger <absolute-ledger-path>` without binding.
Resume reading: verify branch main and HEAD 1776be476c7f3e8dea3b7849b3b161e9b668bdd2 in the project, then read widget_export.py (whole, 18 lines) and thoughts/plans/2026-10-15-widget-export.md.
Plan: thoughts/plans/2026-10-15-widget-export.md; steps 1-2 ticked 2026-11-11 (sha256 29145abeec4afe1019b8c5aabc29ba6d4d0f1c8220708f3d8c3c098085d4520c).
Working changes (non-preclear): untracked widget_export.py (sha256 1661f3bc65a69c034c6fc5172570c9f89ab83b3995ed8c57286988968f9ef477); unstaged plan edit; staged 0. .claude/ is user setup, ownership unknown. Preclear inputs: project/.preclear/backend-inputs/*.md.
Tests: none run (not authorized).

## Next action
In the project directory, draft in the reply only a proposed diff to widget_export.py making JSON the default export (CSV only on explicit request), keeping functions small and pure. Do not apply it. Done when the diff is shown for user review.
<!-- CHECKPOINT:END -->
