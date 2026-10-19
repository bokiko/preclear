# sample-project

Task plan is in thoughts/plans/. The continuity ledger for this project is managed by the checkpoint helper named below.

Resuming from this ledger requires no binding. Read its file directly, or use the helper's `show --ledger <path>`. A resume request never authorizes `bind` or continuity writes; binding is a separate user-approved setup action.

## Preclear configuration

```yaml
preclear:
  version: 1
  backend: checkpoint-v1
  executable: <repo>/<run>/wrapper/missing-checkpoint
  project: <repo>/<run>/project
  task: widget-export
  ledger: <repo>/<run>/ledgers/CONTINUITY_CLAUDE-widget-export.md
  fallback_directory: <repo>/<run>/project/.preclear
```
