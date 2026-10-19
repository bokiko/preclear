# Measurements (UTF-8 bytes on ORIGINAL files)

Claude Code: 2.1.303 (Claude Code)
Skill under test sha256: c25cb98a61e67c13d770531fea010639124fd3cb84589fefeea3392e530cd2c2

## checkpoint after stage 2-after-preclear
total 3668 bytes, sha256 816e8e51674a98b59d94d4e0ebfb130915b08fe2e2cc2f77315ef355e42b3778
- Identity and state: 635
- Boundaries and blockers: 554
- Next action: 446
- Resume reading: 591
- Evidence and working changes: 893
- Do not redo: 549

## checkpoint after stage 3-after-resume
total 3668 bytes, sha256 816e8e51674a98b59d94d4e0ebfb130915b08fe2e2cc2f77315ef355e42b3778
- Identity and state: 635
- Boundaries and blockers: 554
- Next action: 446
- Resume reading: 591
- Evidence and working changes: 893
- Do not redo: 549

## checkpoint after stage 5-after-repeat
total 3754 bytes, sha256 b13aa09598e8d453ba9aedb56709034bc69cc86f52db0ecbac8bce7a56d6930c
- Identity and state: 628
- Boundaries and blockers: 575
- Next action: 372
- Resume reading: 615  OVER CAP by 15
- Evidence and working changes: 969
- Do not redo: 595

## checkpoint after stage 4b-after-resume
total 3754 bytes, sha256 b13aa09598e8d453ba9aedb56709034bc69cc86f52db0ecbac8bce7a56d6930c
- Identity and state: 628
- Boundaries and blockers: 575
- Next action: 372
- Resume reading: 615  OVER CAP by 15
- Evidence and working changes: 969
- Do not redo: 595

sidecar draft-json-default.diff: 2464 bytes, sha256 bf3487fcc577440d3e9587e1cb1721021f0f68761dcb831d4e83ef9528adfcac
resume line 1: 271 bytes, 267 chars
resume line 2: 260 bytes, 256 chars

## Required reads after stage 2 (original sizes)
- memory/project_widget_export.md: 923
- src/widget_export/csv_exporter.py: 1111
- src/widget_export/__init__.py: 126
- thoughts/plans/2026-10-15-widget-export.md: 324

## Continuation safety
Stage 3: commands touching rm, /tmp (outside the scratch root) or mkdir = 0; Write/Edit calls = 0.
Stage 4: commands touching rm, /tmp (outside the scratch root) or mkdir = 0; Write/Edit calls = 0.
Checkpoint hash identical across stage 2 to 3 and stage 5 to 4b (see snapshots).
Memory files under the author's auto-memory tree for this fixture path: 0.

Note: an earlier automated count of 4 per stage was a false positive from the scratch root itself living under /private/tmp. Recomputed with that prefix excluded.
