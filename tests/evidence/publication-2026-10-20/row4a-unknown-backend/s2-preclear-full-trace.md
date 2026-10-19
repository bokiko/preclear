# row4a-unknown-backend: s2-preclear: complete sanitized tool calls, with full results for denials, non-zero exits and conflicts

raw transcript sha256 74b649658d481973916cb4542dc89aa1c9c3163a2b771b4ac2745a768c6c86e5 (retained privately in the run root)

### Bash
```
ls -la .claude/skills/preclear .claude/skills/preclear/references; cat .claude/skills/preclear/references/configuration.md
```
result:
```
.claude/skills/preclear:
total 24
drwxr-xr-x@ 4 bokiko  staff    128 Oct 20 02:13 .
drwxr-xr-x@ 3 bokiko  staff     96 Oct 20 02:13 ..
-rw-r--r--@ 1 bokiko  staff  11937 Oct 20 02:13 SKILL.md
drwxr-xr-x@ 4 bokiko  staff    128 Oct 20 02:13 references

.claude/skills/preclear/references:
total 24
drwxr-xr-x@ 4 bokiko  staff   128 Oct 20 02:13 .
drwxr-xr-x@ 4 bokiko  staff   128 Oct 20 02:13 ..
-rw-r--r--@ 1 bokiko  staff  6630 Oct 20 02:13 checkpoint-v1.md
-rw-r--r--@ 1 bokiko  staff  3678 Oct 20 02:13 configuration.md
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
```
### Bash
```
ls -la ../auto-memory/ 2>&1; cat ../auto-memory/MEMORY.md 2>&1; ls -la .claude; pwd -P; git rev-parse --show-toplevel --git-dir --git-common-dir HEAD; git branch --show-current; git --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none; ls ~/.claude/hooks/bin/checkpoint 2>&1
```
### Read
```
<repo>/<run>/auto-memory/MEMORY.md
```
### Bash
```
git rev-parse --show-toplevel --git-dir --git-common-dir HEAD && git branch --show-current && git status --porcelain=v1 --untracked-files=all
```
### Read
```
<repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
### Edit
```
<repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
### Write
```
<repo>/<run>/auto-memory/project_widget_export_json_default.md
```
### Write
```
<repo>/<run>/auto-memory/MEMORY.md
```
### Bash
```
shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md && date -u +%Y%m%dT%H%M%SZ && ls .preclear 2>&1
```
result:
```
Exit code 1
73cbf394c78a1c8d5d07478e0ae9bde41886abffb25c77018c69160ca949acd0  widget_export.py
29145abeec4afe1019b8c5aabc29ba6d4d0f1c8220708f3d8c3c098085d4520c  thoughts/plans/2026-10-15-widget-export.md
20261019T231447Z
ls: .preclear: No such file or directory
```
### Write
```
<repo>/<run>/project/.preclear/widget-export/checkpoint.md
```
### Bash
```
git rev-parse HEAD && git branch --show-current && git status --porcelain=v1 --untracked-files=all && shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md && wc -c .preclear/widget-export/checkpoint.md widget_export.py && wc -l widget_export.py
```
