---
name: widget-export-no-tests-no-commit
description: Standing rule for the widget-export task — do not run tests and do not commit until the user says so
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1ba7eef4-5a70-4b18-b19d-91343722a179
  modified: 2026-10-19T08:45:00.675Z
---

For the whole widget-export task, do not run tests and do not commit until the user explicitly says so.

**Why:** User instruction given 2026-10-19; they want to control when verification and commits happen.

**How to apply:** Write code and update PLAN.md, but stop short of `pytest`/`python -m` test runs and `git commit`. Wait for an explicit go-ahead. Related: [[widget-export-json-default]].
