---
name: preclear
description: Save verified continuation state before the user clears context; emit one paste-ready resume line.
disable-model-invocation: true
allowed-tools: [Read, Write, Edit, Glob, Grep]
---

# preclear

Run here, not in a subagent. Save verified state and a resume line; the user
copies it, runs `/clear`, then pastes it into the fresh session.

## Hard rules

- **Git is read-only.** `git status`, `git log`, `git rev-parse`, `git branch`,
  `git diff` are fine. Never `commit`, `push`, `add`, `stash`, `checkout`,
  `reset`, `rm`, or anything that mutates git state or the index. This binds
  any helper you call.
- **Never delete files.** Update in place. Frozen snapshots and their sidecars are
  new files and are never overwritten.
- **Never run `/clear` or compact.** That is the user's move.
- If something is genuinely unknown, write it down as `UNCONFIRMED` rather than
  guessing. A checkpoint that invents state is worse than one that admits gaps.
- Never bypass a hook, edit a protected file via the shell, install anything,
  change settings, bind a session, or write a secret anywhere.
- Anything merely found is a candidate. Only explicit configuration (probe 4)
  activates a backend.
- Convert relative dates to absolute.

## Step 1: Discover what this user has

Run the probes in order. Record each system as `FOUND <path>`, `ABSENT` (evidence
it does not exist), `INACCESSIBLE`, `AMBIGUOUS`, or `UNCONFIRMED`. Speculative
lookups are capped at **20 candidate paths and 12,000 bytes**; governing
instructions and documents already identified as active are exempt. At the cap,
write `UNCONFIRMED`. Never search the home directory recursively or pick the
newest file.

1. **This conversation.** Task, project, plan, ledger or handoff already named,
   authorization given or refused, work completed.
2. **Where you are.** Physical working directory (symlinks resolved). If git
   applies: toplevel, `--git-dir`, `--git-common-dir` (linked worktree when they
   differ), branch, full HEAD. Record `detached`, `unborn`, or `no-git`. A parent
   repository is not automatically the project.
3. **Instructions already loaded.** CLAUDE.md, CLAUDE.local.md, rules files, their
   imports, AGENTS.md if named. Keep their precedence; skip nested ones.
4. **Preclear configuration.** A fenced YAML block headed `Preclear configuration`
   in an applicable CLAUDE.md; format and validation in
   `references/configuration.md`. Also memory, plan, or guard settings the
   instructions mention. Read narrow fields. Never execute a hook or script to
   learn what it does.
5. **Memory.** Check first whether memory is enabled under the applicable
   instructions or settings; disabled means no memory writes. Use only the root
   the session supplied or configuration named; read its index and the topic files
   relevant to this task; learn its conventions by looking (index, hubs,
   frontmatter, links). No authoritative root means `UNCONFIRMED`, not `ABSENT`.
   Never derive a path from a slug.
6. **Plan.** From the conversation or configuration first; otherwise only
   `thoughts/plans/`, `.claude/plans/`, `PLAN.md`, `TODO.md`, `TODO`, and a
   configured plan directory. Match by task identity in title or content.
7. **Ledger or handoff.** From an explicit session binding or configuration first;
   otherwise only `CONTINUITY.md`, `HANDOFF.md`, `thoughts/ledgers/`,
   `docs/handoffs/`. A filename match is a candidate until its content names this
   project and task.
8. **Linked issue or PR** (optional). Only via a tool already configured and
   authorized. No login, broad search, or external writes.
9. **Before any write** (scratch files too): is the destination within a location
   expressly authorized by instructions, configuration, or the supplied memory
   root; if a symlink, where does it point; what is the permitted update method;
   does its content name another project or task; could another session be
   writing it. Doubt stops that write, not the run.

## Step 2: Route each fact to its one owner

The checkpoint points at owners; it does not copy them. One deliberate repetition:
authorization boundaries go in the checkpoint even when their full text lives
elsewhere.

| Fact | Owner | In the checkpoint |
| --- | --- | --- |
| Stable preference, reusable verified lesson | Existing memory, its format, narrowest scope | Pointer only if the next action needs it |
| Decision and why | Existing decision record or plan; memory only if nothing else owns it | Identifier and consequence |
| Plan step done, acceptance result | The plan file, by its own update method | Step id and pointer |
| Task state, blocker, next step | Checkpoint, or the configured ledger | Primary concise account |
| Test output, full changed-file list | Existing evidence file, or a sidecar | Result, state observed in, pointer |
| Repository facts, existing rules | Their source | Pointer only when needed |
| Secrets, raw sensitive dumps | Nowhere via preclear | Safe identifier or how to retrieve |

- Read the owner before writing; fix its existing entry in its own format, no
  near-duplicates. Use the user's conventions exactly: no new frontmatter, hubs,
  links, or index rules. Respect index guards.
- Memory gets only what stays useful after this task and is not cheaply
  recoverable: decisions with reasons, user corrections, non-obvious verified
  facts. Nothing derivable from repo, history, instructions, or checkpoint.
- Memory `ABSENT`, `INACCESSIBLE`, `AMBIGUOUS`, `UNCONFIRMED`, or disabled: no
  memory writes; keep the irreplaceable fact in the checkpoint.
- Update plan progress only when the plan and its edit method are established;
  otherwise record "plan update pending".
- No "in-flight" memory notes: volatile state lives in the checkpoint only.
- Never rewrite CLAUDE.md or rearrange the user's setup.

## Step 3: Write the checkpoint

### Destination

Configuration decides first (`references/configuration.md`): a valid applicable
block runs its backend and, on failure, its own fallback policy; an invalid or
ambiguous block runs no backend and its terminal rule picks plain file or
`BLOCKED`. The list below applies only when no block applies.

1. An established, authorized handoff location the project already uses.
2. `<project>/.preclear/<task-slug>/checkpoint.md`: one mutable file per task,
   reread immediately before writing. If its Identity names a different project
   or task, leave it and use `<task-slug>-2`, `-3`, and so on. Never create or
   edit `.gitignore`. If `.preclear/` is untracked, tell the user once and record
   `untracked-notice: sent`.
3. No authorized location: print the full checkpoint in your reply, mark
   persistence `BLOCKED`, emit no resume line.

**Frozen copy.** Only when the user asks for a handoff, the work crosses to another
person, machine, or worktree, project rules require one, or several sessions share
the mutable file. Name `checkpoint-<UTC-timestamp>-<4-char-random>.md` beside it,
created only if free. Preclear-owned sidecars it cites get the same suffix;
external evidence is cited with a digest or version and marked mutable. Report the
snapshot's SHA-256. "Frozen" is a convention unless the filesystem enforces it.

### Schema (plain-file checkpoints)

Six headings, exactly these, in this order. Whole file under **4,096 bytes**,
normally under 3,000. If forced to choose, keep boundaries, report an exception.

| Heading | Max bytes | Contents |
| --- | ---: | --- |
| `## Identity and state` | 800 | `preclear-schema: 1`, `checkpoint-id: <task-slug>-<UTC-timestamp>`, absolute physical project path (note linked worktree), task slug, one-line objective, current result, branch or `detached`/`unborn`/`no-git`, full HEAD or `n/a`, `untracked-notice` if sent |
| `## Boundaries and blockers` | 600 | Persist user-authorized scope and scratch/draft limits; paths grant no permission; no deletion or denial bypass. Pending approvals, blockers, `UNCONFIRMED:` items, `Detail:` pointer |
| `## Next action` | 500 | One presently authorized step with directory, target, and completion condition. If blocked: one prerequisite or question, never a conditional workflow |
| `## Resume reading` | 600 | Fixed first line: "cd to the project path above and verify against Identity: branch and full HEAD if a branch is recorded; full HEAD only if `detached`; path and no HEAD if `unborn`; path and listed file digests if `no-git`; then status. On mismatch reconcile before acting." Then ordered minimum reads (path plus heading or line range) and when a conditional read is needed. Last line: "Execute only Next action within Boundaries; preserve checkpoint and sidecars until `/preclear`. No file output without authorization." |
| `## Evidence and working changes` | 1,000 | Non-preclear counts: staged, unstaged, untracked, conflicted, changed submodules; preclear artifacts listed separately by exact path; untouched files `ownership unknown`; verification command, observed result, the HEAD and file digests it ran against (or `binding UNCONFIRMED`); sidecar pointer |
| `## Do not redo` | 596 | Expensive discoveries or checks already done, each with evidence location and what invalidates it. Never exempts the freshness check or digest recheck |

**Sidecar.** When changes exceed what fits inline, write `status.txt` beside the
checkpoint from `git --no-optional-locks status --porcelain=v1 -z
--untracked-files=all --ignore-submodules=none`, counts only inline. Every change
is accounted for inline or in the sidecar; a tree too large to enumerate gets an
explicit inventory exception, never a claim of completeness. Never attribute
another session's files by guessing.

## Step 4: Verify

1. **Order.** Finish memory and plan updates. Write checkpoint and sidecar. Then
   capture branch, full HEAD, and the status command above (git checks only when
   git applies). Subtract your own preclear artifacts by exact path; every
   remaining entry must appear in Evidence or the sidecar, and branch and HEAD
   must equal Identity. Recheck item 2 digests even if status is unchanged. Anything differs:
   correct, repeat once. Still changing: `UNSTABLE`. Never fabricate stability.
2. **Content binding.** Status cannot show a dirty file changed again. For files
   behind a test claim or the next action, record a content digest. A digest taken
   now does not prove the earlier test ran against it: say `binding UNCONFIRMED`
   or `stale` without that evidence. Never rerun a suite just to checkpoint.
3. **Shared files** were reread just before writing and had not changed.
4. **Reread every artifact.** Headings exact for the format used, caps hold,
   links resolve, Next action is one step.
5. **Measure.** UTF-8 bytes of checkpoint (≤4,096), resume line (≤512), and
   required excerpts plus expected freshness-check output (≤1,392): the minimum
   resume package, target **6,000 bytes**, about 2,000 tokens at `ceil(bytes/3)`.
   Auto-loaded instructions are excluded; a memory or plan file counts only if
   it must be read before acting. Installed tokenizer if present, never install
   one; denied or unmeasurable bytes are `UNCONFIRMED`, never a passed cap check.
   A required large file is an exception to report, not to hide.

Print the result: artifacts with paths and bytes, package total, snapshot digest
if any, every `UNCONFIRMED`, `UNSTABLE`, `BLOCKED`, or exception.

## Step 5: Emit the resume line

Two or three sentences on what you updated and what the user must know before
clearing. Then exactly **one** fenced code block with a single line, and
**nothing after it**.

```
Resume <task-slug> from "<absolute checkpoint path>" — <branch|detached|unborn|no-git> @ <short-sha|n/a> — <one-phrase state>
```

Target under 200 characters. Never truncate the path or invent an alias; if
longer, say so before the block. `BLOCKED` means no resume line.
