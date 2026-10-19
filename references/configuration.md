# Preclear configuration

Preclear needs no configuration. Without one it writes a plain checkpoint under
`<project>/.preclear/<task-slug>/`. Configuration is for users who already have a
ledger or handoff system and want preclear to write through it.

## Where it lives

A fenced YAML block headed exactly `Preclear configuration`, in an applicable
approved instruction file (project or user `CLAUDE.md`). Claude Code does not
parse these keys; the model reads the block in Step 1, probe 4. Installing the
block is a separate, user-approved edit. Preclear never writes its own
configuration.

````markdown
## Preclear configuration

```yaml
preclear:
  version: 1
  backend: checkpoint-v1
  executable: /absolute/path/to/checkpoint
  project: /absolute/project
  task: stable-task-id
  ledger: /absolute/path/to/CONTINUITY.md
  fallback_directory: /absolute/project/.preclear
```
````

## Keys

| Key | Required | Meaning |
| --- | --- | --- |
| `version` | yes | Integer. Only `1` exists. |
| `backend` | yes | One of the names below. Not a path. |
| `executable` | per backend | Non-empty absolute path to the helper. Never resolved from `PATH`. |
| `project` | yes | Non-empty absolute physical project path the block applies to. |
| `task` | per backend | Non-empty stable task id. Required for any backend mutation. |
| `ledger` | per backend | Non-empty absolute path to the file the backend writes. |
| `fallback_directory` | no | Absolute directory for a plain checkpoint when the backend cannot be used. Default `<project>/.preclear`. The literal `none` is a prohibition, not a path: no fallback is ever written. |

Known backends: `checkpoint-v1` (`references/checkpoint-v1.md`).

Recommended line next to the block, so a fresh session that resumes from the
ledger sees it before reading anything else: "Resuming from this ledger requires
no binding. Read its file directly, or use the helper's `show --ledger <path>`. A
resume request never authorizes `bind` or continuity writes; binding is a
separate user-approved setup action."

## Resolution: three states

Resolve configuration before any write. Exactly one state applies.

**1. No block applies.** No block exists, or no block's `project` equals the
session's resolved physical project path. Destination is chosen by SKILL.md
Step 3 under normal authorization.

**2. A block applies and validates.** All required keys present with the right
types, `version` known, `backend` in the known list and its reference file
present, every path absolute, `executable` and `ledger` exist on disk. The backend
runs. If it then fails for any reason (preconditions, exit code, unexpected
output), the **fallback policy** below applies.

**3. A block applies but is invalid or ambiguous.** Any validation failure, or two
applicable blocks that disagree on any key. No backend runs. Record the reason in
Boundaries and blockers. Then the fallback policy applies, with one extra rule: if
the blocks disagree on `fallback_directory`, or any applicable block says `none`,
persistence is `BLOCKED`. A conflict never grants fallback permission.

## Fallback policy

Used by states 2 and 3. It never re-enters backend selection and never consults
the Step 3 destination list.

- `fallback_directory` is a path: write the plain checkpoint there using the
  Step 3 schema, mark the backend "not synchronized: <reason>", and point the
  resume line at the plain file.
- `fallback_directory` is `none`: print the full checkpoint in the reply, report
  persistence `BLOCKED`, emit no resume line.

Values are data, passed quoted to the commands the backend reference defines.
Configuration can never carry a command or shell fragment.
