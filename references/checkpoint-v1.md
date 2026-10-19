# Backend: checkpoint-v1

A ledger helper that keeps a hash-guarded checkpoint block inside a Markdown
continuity ledger. Each of six sections carries a hash; an update must present the
hash it read, so concurrent sessions cannot overwrite each other silently. On the
author's machine a hook blocks direct edits to the ledger; the helper is the only
write path.

Loaded only when a `Preclear configuration` block in state 2 names
`backend: checkpoint-v1`. Interface facts were verified against the helper build
of 2026-10-04 (`~/.claude/hooks/dist/checkpoint.mjs`). A different build may
differ; output that does not match the table is a failure, never a success.

## Preconditions for any mutation

All must hold, else the fallback policy in `references/configuration.md` applies:

1. The helper identifies the session from `CLAUDE_CODE_SESSION_ID` or `--session`.
   If neither is available there is no confirmed binding. Never guess an id.
2. `status` reports a binding (format below) whose ledger, symlinks resolved,
   equals the configured `ledger`.
3. The ledger's existing block names this project and the configured `task`.
4. The configured `task` is set. Preclear verifies task identity; configuration
   never causes a bind.

Preclear does not bind, create, or initialise ledgers. Those are setup actions the
user performs separately with the helper's `bind`, `create`, and `init` commands.

## Interface

`<executable>` is the configured absolute path. Paths and ids are passed quoted.
Section bodies and the serialized validation block go in an authorized
`backend-inputs/` subdirectory of `fallback_directory`, or of a separately
authorized scratch directory when `fallback_directory` is `none` (never create a
directory named `none`). They are retained checkpointing inputs, not canonical
state and not required resume reads; list them separately from working changes.

Exit codes: `0` ok, `1` internal error, `2` usage or validation (including no
checkpoint block), `3` conflict, `4` invalid checkpoint, `5` kill switch active,
`6` lock timeout.

| Operation | Command | Observed output |
| --- | --- | --- |
| Status | `status` | Unbound: one line `session <id8>: unbound`. Bound: line 1 `session <id8> → <ledger>`, optionally followed by ` (carried from <id8>, <verifier>)`; line 2 either `checkpoint updated <iso> by <id>` then `Next action: <text>`, or `checkpoint: NONE`. Take the ledger from line 1 between `→ ` and the optional ` (`. `checkpoint: NONE` fails precondition 3. |
| Read | `show [--ledger P] [--section S]` | Each section prints as `## <name>`, then `section-hash: <hash>`, then the body. One `--section` per call; a repeated flag is ignored. |
| Validate | `validate --from <file>` | Input must be a full serialized block (below). Same checks as `update`: all six sections present, no others, block ≤4,096 bytes, `Authorization boundaries` non-empty and ≤600 chars. |
| Update | `update --section S --expect-section <hash> --from <file>` | File holds one section body only. Exit 3: section changed since your read; message names a `.conflict-*` file. |
| Note | `note --from <file>` | Appends to ledger history outside the hashed block. |
| Lint | `lint` | Success prints `ledger lint OK`. It scans all registered ledgers; a warning counts only if it names the configured ledger. |
| Handoff | `handoff --from <file>` | Immutable snapshot tied to this session. Use on the Step 3 frozen-copy triggers. |

## Section assembly

The helper parses every `## ` line as a section, so the plain-file headings cannot
be nested inside it. Build **one complete final body per helper section**, using
short bold labels instead of headings. Strip any `section-hash:` lines copied from
`show`. Existing content that is still true stays; this is a merge, not a replace.

| Helper section | Final body contains |
| --- | --- |
| Goal & current state | Identity and state content |
| Authorization boundaries | Limits only, ≤600 chars, plus `Detail: <path#anchor>` |
| Blockers & open questions | Blockers and `UNCONFIRMED` items |
| Decisions (with reasons) | Existing decisions still relevant, then **Do not redo** entries |
| Evidence & key paths | **Resume reading** lines first, then Evidence and working changes |
| Next action | Next action |

Persist this rule in `Authorization boundaries` and as the first line of
`Evidence & key paths`, because the fresh session reads the ledger, not this file:

> Resume is read-only for continuity state: never bind. Update, note, or handoff
> only during an explicit `/preclear`; setup is a separate user action. Read the
> ledger file directly, or use `show --ledger <absolute-ledger-path>` without
> binding.

When the next action is a diff or answer in the reply only, also persist: "no
proposal files, section-input files, binding changes, or ledger writes." Do not
carry an earlier "edit files inside the project" scope into a chat-only resume
without marking it historical.

### Serialized block for `validate`

Write the six bodies into this exact shape, in this order, in a separate file
from the per-section `update` files. The `updated` and `by` values are
placeholders; the helper rewrites them on update.

```
<!-- CHECKPOINT:BEGIN updated: 1970-01-01T00:00:00Z by: preclear -->
## Goal & current state
<body>

## Decisions (with reasons)
<body>

## Blockers & open questions
<body>

## Authorization boundaries
<body>

## Evidence & key paths
<body>

## Next action
<body>
<!-- CHECKPOINT:END -->
```

The 4,096-byte limit applies to this rendered block including the markers and
headings, not to the six bodies alone.

## Flow

1. Check preconditions. 2. `show`; record every `section-hash`. 3. Assemble six
bodies; serialize; `validate`. 4. `update` each changed section with its hash,
one body file each. 5. Exit 3: read the conflict file, `show` again, merge by
hand, retry once with the new hash; a second conflict means `UNSTABLE` and the
fallback policy. 6. `lint` must print `ledger lint OK` or only warnings naming
other ledgers. 7. On a frozen trigger, `handoff`. 8. SKILL.md Step 4 still
applies in full.

## Failure handling

Missing or non-executable `executable` is a state 3 validation failure (see
configuration reference). Exit 1, 2, 4, 5, 6, a precondition failure, or output
not matching the table: stop backend operations, do not claim synchronization,
apply the fallback policy with "ledger not synchronized: <reason>". A validation
rejection (exit 2 or 4) may be repaired once if the message is understood;
otherwise fallback. Never edit the ledger directly, never initialise a missing
block, never change bindings.
