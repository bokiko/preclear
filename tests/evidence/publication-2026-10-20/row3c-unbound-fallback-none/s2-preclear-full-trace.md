# row3c-unbound-fallback-none: s2-preclear: complete sanitized tool calls, with full results for denials, non-zero exits and conflicts

raw transcript sha256 536bc8979ee2de07f1b9e4016d07dc588e1ae246d4fbe9ee6540ddd948c405fc (retained privately in the run root)

### Bash
```
ls -la .claude/skills/preclear .claude/skills/preclear/references && cat .claude/skills/preclear/references/configuration.md
```
result:
```
.claude/skills/preclear:
total 24
drwxr-xr-x@ 4 bokiko  staff    128 Oct 20 02:18 .
drwxr-xr-x@ 3 bokiko  staff     96 Oct 20 02:18 ..
-rw-r--r--@ 1 bokiko  staff  11937 Oct 20 02:18 SKILL.md
drwxr-xr-x@ 4 bokiko  staff    128 Oct 20 02:18 references

.claude/skills/preclear/references:
total 24
drwxr-xr-x@ 4 bokiko  staff   128 Oct 20 02:18 .
drwxr-xr-x@ 4 bokiko  staff   128 Oct 20 02:18 ..
-rw-r--r--@ 1 bokiko  staff  6630 Oct 20 02:18 checkpoint-v1.md
-rw-r--r--@ 1 bokiko  staff  3678 Oct 20 02:18 configuration.md
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
cat .claude/skills/preclear/references/checkpoint-v1.md; ls -la <repo>/<run>/wrapper/; pwd -P
```
### Read
```
<repo>/<run>/project/.claude/skills/preclear/references/checkpoint-v1.md
```
result:
```
1	# Backend: checkpoint-v1
2	
3	A ledger helper that keeps a hash-guarded checkpoint block inside a Markdown
4	continuity ledger. Each of six sections carries a hash; an update must present the
5	hash it read, so concurrent sessions cannot overwrite each other silently. On the
6	author's machine a hook blocks direct edits to the ledger; the helper is the only
7	write path.
8	
9	Loaded only when a `Preclear configuration` block in state 2 names
10	`backend: checkpoint-v1`. Interface facts were verified against the helper build
11	of 2026-10-04 (`~/.claude/hooks/dist/checkpoint.mjs`). A different build may
12	differ; output that does not match the table is a failure, never a success.
13	
14	## Preconditions for any mutation
15	
16	All must hold, else the fallback policy in `references/configuration.md` applies:
17	
18	1. The helper identifies the session from `CLAUDE_CODE_SESSION_ID` or `--session`.
19	   If neither is available there is no confirmed binding. Never guess an id.
20	2. `status` reports a binding (format below) whose ledger, symlinks resolved,
21	   equals the configured `ledger`.
22	3. The ledger's existing block names this project and the configured `task`.
23	4. The configured `task` is set. Preclear verifies task identity; configuration
24	   never causes a bind.
25	
26	Preclear does not bind, create, or initialise ledgers. Those are setup actions the
27	user performs separately with the helper's `bind`, `create`, and `init` commands.
28	
29	## Interface
30	
31	`<executable>` is the configured absolute path. Paths and ids are passed quoted.
32	Section bodies and the serialized validation block go in an authorized
33	`backend-inputs/` subdirectory of `fallback_directory`, or of a separately
34	authorized scratch directory when `fallback_directory` is `none` (never create a
35	directory named `none`). They are retained checkpointing inputs, not canonical
36	state and not required resume reads; list them separately from working changes.
37	
38	Exit codes: `0` ok, `1` internal error, `2` usage or validation (including no
39	checkpoint block), `3` conflict, `4` invalid checkpoint, `5` kill switch active,
40	`6` lock timeout.
41	
42	| Operation | Command | Observed output |
43	| --- | --- | --- |
44	| Status | `status` | Unbound: one line `session <id8>: unbound`. Bound: line 1 `session <id8> → <ledger>`, optionally followed by ` (carried from <id8>, <verifier>)`; line 2 either `checkpoint updated <iso> by <id>` then `Next action: <text>`, or `checkpoint: NONE`. Take the ledger from line 1 between `→ ` and the optional ` (`. `checkpoint: NONE` fails precondition 3. |
45	| Read | `show [--ledger P] [--section S]` | Each section prints as `## <name>`, then `section-hash: <hash>`, then the body. One `--section` per call; a repeated flag is ignored. |
46	| Validate | `validate --from <file>` | Input must be a full serialized block (below). Same checks as `update`: all six sections present, no others, block ≤4,096 bytes, `Authorization boundaries` non-empty and ≤600 chars. |
47	| Update | `update --section S --expect-section <hash> --from <file>` | File holds one section body only. Exit 3: section changed since your read; message names a `.conflict-*` file. |
48	| Note | `note --from <file>` | Appends to ledger history outside the hashed block. |
49	| Lint | `lint` | Success prints `ledger lint OK`. It scans all registered ledgers; a warning counts only if it names the configured ledger. |
50	| Handoff | `handoff --from <file>` | Immutable snapshot tied to this session. Use on the Step 3 frozen-copy triggers. |
51	
52	## Section assembly
53	
54	The helper parses every `## ` line as a section, so the plain-file headings cannot
55	be nested inside it. Build **one complete final body per helper section**, using
56	short bold labels instead of headings. Strip any `section-hash:` lines copied from
57	`show`. Existing content that is still true stays; this is a merge, not a replace.
58	
59	| Helper section | Final body contains |
60	| --- | --- |
61	| Goal & current state | Identity and state content |
62	| Authorization boundaries | Limits only, ≤600 chars, plus `Detail: <path#anchor>` |
63	| Blockers & open questions | Blockers and `UNCONFIRMED` items |
64	| Decisions (with reasons) | Existing decisions still relevant, then **Do not redo** entries |
65	| Evidence & key paths | **Resume reading** lines first, then Evidence and working changes |
66	| Next action | Next action |
67	
68	Persist this rule in `Authorization boundaries` and as the first line of
69	`Evidence & key paths`, because the fresh session reads the ledger, not this file:
70	
71	> Resume is read-only for continuity state: never bind. Update, note, or handoff
72	> only during an explicit `/preclear`; setup is a separate user action. Read the
73	> ledger file directly, or use `show --ledger <absolute-ledger-path>` without
74	> binding.
75	
76	When the next action is a diff or answer in the reply only, also persist: "no
77	proposal files, section-input files, binding changes, or ledger writes." Do not
78	carry an earlier "edit files inside the project" scope into a chat-only resume
79	without marking it historical.
80	
81	### Serialized block for `validate`
82	
83	Write the six bodies into this exact shape, in this order, in a separate file
84	from the per-section `update` files. The `updated` and `by` values are
85	placeholders; the helper rewrites them on update.
86	
87	```
88	<!-- CHECKPOINT:BEGIN updated: 1970-01-01T00:00:00Z by: preclear -->
89	## Goal & current state
90	<body>
91	
92	## Decisions (with reasons)
93	<body>
94	
95	## Blockers & open questions
96	<body>
97	
98	## Authorization boundaries
99	<body>
100	
101	## Evidence & key paths
102	<body>
103	
104	## Next action
105	<body>
106	<!-- CHECKPOINT:END -->
107	```
108	
109	The 4,096-byte limit applies to this rendered block including the markers and
110	headings, not to the six bodies alone.
111	
112	## Flow
113	
114	1. Check preconditions. 2. `show`; record every `section-hash`. 3. Assemble six
115	bodies; serialize; `validate`. 4. `update` each changed section with its hash,
116	one body file each. 5. Exit 3: read the conflict file, `show` again, merge by
117	hand, retry once with the new hash; a second conflict means `UNSTABLE` and the
118	fallback policy. 6. `lint` must print `ledger lint OK` or only warnings naming
119	other ledgers. 7. On a frozen trigger, `handoff`. 8. SKILL.md Step 4 still
120	applies in full.
121	
122	## Failure handling
123	
124	Missing or non-executable `executable` is a state 3 validation failure (see
125	configuration reference). Exit 1, 2, 4, 5, 6, a precondition failure, or output
126	not matching the table: stop backend operations, do not claim synchronization,
127	apply the fallback policy with "ledger not synchronized: <reason>". A validation
128	rejection (exit 2 or 4) may be repaired once if the message is understood;
129	otherwise fallback. Never edit the ledger directly, never initialise a missing
130	block, never change bindings.
131	
```
### Bash
```
test -x <repo>/<run>/wrapper/checkpoint && echo EXEC_OK; <repo>/<run>/wrapper/checkpoint status; echo "exit=$?"
```
result:
```
This Bash command contains multiple operations. The following part requires approval: echo "exit=$?"
```
### Bash
```
<repo>/<run>/wrapper/checkpoint status
```
### Bash
```
ls -la <repo>/<run>/auto-memory/
```
### Bash
```
git rev-parse --show-toplevel --git-dir --git-common-dir HEAD --abbrev-ref HEAD && git --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none && shasum -a 256 widget_export.py thoughts/plans/2026-10-15-widget-export.md
```
result:
```
This Bash command contains multiple operations. The following part requires approval: git --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none
```
### Glob
```
*
```
### Bash
```
git rev-parse --show-toplevel --git-dir --git-common-dir HEAD --abbrev-ref HEAD
```
### Bash
```
git -C <repo>/<run>/project --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none
```
result:
```
This command requires approval
```
### Bash
```
shasum -a 256 <repo>/<run>/project/widget_export.py <repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
### Bash
```
git status --porcelain=v1 --untracked-files=all
```
### Write
```
<repo>/<run>/auto-memory/widget-export-json-default.md
```
### Write
```
<repo>/<run>/auto-memory/MEMORY.md
```
### Edit
```
<repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
### Bash
```
git status --porcelain=v1 --untracked-files=all && git rev-parse HEAD --abbrev-ref HEAD
```
### Bash
```
shasum -a 256 <repo>/<run>/project/widget_export.py <repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
### Bash
```
wc -c <<'EOF'
## Identity and state
preclear-schema: 1
checkpoint-id: widget-export-20261020T000000Z
project: <repo>/<run>/project (main worktree)
task: widget-export
objective: export widgets (columns id, name)
result: plan step 2 done (CSV exporter in widget_export.py, untested). Format decision changed 2026-10-20: JSON is now the default, CSV only on explicit request (consumer moved to a JSON API in the week of 2026-10-12). JSON not implemented.
branch: main
HEAD: 745de255134bb00a89847414af7acf23dc1f56ba

## Boundaries and blockers
Scope: next action is a diff shown in the reply only. No file edits, proposal files, section-input files, binding changes or ledger writes. No tests, commits or pushes. Earlier "edit files inside project" scope is historical. Paths grant no permission; no deletion; no bypassing a denial.
Resume never binds. Read the ledger file directly or via `show --ledger`.
BLOCKED: ledger not synchronized (session unbound; fallback_directory none). Ledger still says CSV-first and "exporter not written": stale.
Detail: thoughts/plans/2026-10-15-widget-export.md

## Next action
In the project dir, draft a proposed unified diff that makes JSON the default export (e.g. a widgets_to_json and a format-select entry point that defaults to json, CSV still available on request) and show it in the reply for bokiko's review. Done when the diff has been shown, with nothing applied.

## Resume reading
cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting.
1. widget_export.py (all, 23 lines)
2. thoughts/plans/2026-10-15-widget-export.md (all)
3. Memory widget-export-json-default.md, only if this checkpoint is not in context
Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output, binding, or backend write without authorization.

## Evidence and working changes
Non-preclear: 0 staged, 1 unstaged (M thoughts/plans/2026-10-15-widget-export.md, step 2 ticked by preclear), 4 untracked (widget_export.py; .claude/skills/preclear/SKILL.md, references/checkpoint-v1.md, references/configuration.md: ownership unknown), 0 conflicted, 0 submodules.
Preclear artifacts: none in project; memory auto-memory/widget-export-json-default.md + MEMORY.md.
Digests (sha256): widget_export.py aaf296b9…0ef5a; plan 29145abe…4520c.
Verification: none run (tests not authorized).

## Do not redo
- Backend probe: `checkpoint status` printed "session e7ac129d: unbound". Invalidated if bokiko binds the session.
- CSV exporter written; keep it as the opt-in path. Invalidated if its digest changes.
EOF
```
### Bash
```
date -u +%Y%m%dT%H%M%SZ; wc -c <repo>/<run>/project/widget_export.py <repo>/<run>/project/thoughts/plans/2026-10-15-widget-export.md
```
