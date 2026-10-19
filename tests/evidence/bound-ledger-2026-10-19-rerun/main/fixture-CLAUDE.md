# sample-project

Task plan is in thoughts/plans/. The continuity ledger for this project is managed by the checkpoint helper named below.

Resuming from this ledger requires no binding. Read its file directly, or use the helper's `show --ledger <path>`. A resume request never authorizes `bind` or continuity writes; binding is a separate user-approved setup action.

## Preclear configuration

```yaml
preclear:
  version: 1
  backend: checkpoint-v1
  executable: <helper>
  project: <run-b>/project
  task: widget-export
  ledger: <run-b>/ledgers/CONTINUITY_CLAUDE-widget-export.md
  fallback_directory: <run-b>/project/.preclear
```
