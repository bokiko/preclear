# Measurements (UTF-8 bytes on ORIGINAL files, before sanitizing)

Skill under test sha256: 5c4315761540286e8ae3e94d053af4a375e7f8403fdb5270cf31805211a58e1d

## checkpoint
total 3150 bytes, sha256 91b91ac45905aa66418766112d5ef02376e41f0cd0cc163424cc13a36a265230
- Identity and state: 602
- Boundaries and blockers: 519
- Next action: 310
- Resume reading: 496
- Evidence and working changes: 816
- Do not redo: 407

## memory hashes (before work / after work / after /preclear)
### memory-before.sha
cc370df322e9c753b055142edcdbe94b867e244b4150e6d5617c3dffe812fae4  memory/MEMORY.md
a1d1dbc8544d046abded8d120e139040db59e664ec2d946719dd8262e8cf1f5b  memory/project_widget_export.md
### memory-after-work.sha
cc370df322e9c753b055142edcdbe94b867e244b4150e6d5617c3dffe812fae4  memory/MEMORY.md
a1d1dbc8544d046abded8d120e139040db59e664ec2d946719dd8262e8cf1f5b  memory/project_widget_export.md
### memory-after-preclear.sha
67d91a3545012d11ecbf19afd0c047c9f2a2179fdc1257b8c1cec42ae6540485  memory/MEMORY.md
b81c398c0283b946d61198d989f7b730397b07d7f50787b38232d345fd06c001  memory/project_widget_export.md

Work session changed no memory file (hashes identical before and after work). Both files changed only in the /preclear turn.

## resume line
255 bytes, 251 chars (over the 200-char target; exception reported)

## isolation audit
Claude Code created its per-project state folder for the fixture path (transcripts). Memory files found under it: 0. All model-directed memory writes went to <scratch>/project/memory.

## Exact artifact bytes (original files, added after Codex review)
- checkpoint.md: 3150
- memory/MEMORY.md: 137
- memory/project_widget_export.md: 561
- PLAN.md: 319
- exporter.py: 456
- resume line: 255

## Minimum resume package (what the fresh session must read before acting, per the checkpoint's Resume reading)
- checkpoint 3150 + resume line 255 + PLAN.md 319 + exporter.py 456 + memory/project_widget_export.md 561 = 4741 bytes, plus the freshness-check output (git identity, status, three digests; roughly 300 to 500 bytes). Under the 6,000-byte target.
