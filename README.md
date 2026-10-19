# preclear

When you run `/clear` in Claude Code, the conversation is gone. The next session
then spends tokens working out what you were doing, what was decided, and what
comes next. `preclear` is a skill that writes the minimum a fresh session needs to
continue, puts each fact in the one place that owns it, and prints one
paste-ready line that points at the result.

Author: bokiko.

## Install

Copy or symlink this folder to one of:

- `~/.claude/skills/preclear` (personal, all projects)
- `<repo>/.claude/skills/preclear` (one project)

The skill is invoked only by typing `/preclear`. It never fires on its own,
because `SKILL.md` sets `disable-model-invocation: true`.

**Existing installation:** a personal skill named `preclear` takes precedence
over a project installation of the same name. Before testing or migrating, check
which `SKILL.md` will load. Move an old installation outside every skill
directory before replacing it; renaming its folder alone can leave a conflicting
frontmatter name. Start a fresh session after changing the installation. Never
delete or overwrite an existing installation automatically.

## Usage

In this order:

1. Run `/preclear`.
2. Copy the line it prints.
3. Run `/clear` yourself.
4. Paste the line into the new session.

preclear never runs `/clear` for you.

After resuming, do the authorized next action and update the normal plan as
needed. Leave the saved checkpoint unchanged; run `/preclear` again when you want
a fresh verified checkpoint. A checkpoint records its capture time and goes stale
as work proceeds.

A resume line authorizes only the checkpoint's next action. Respect its allowed
paths and scratch or file-output limits; never delete files or bypass a denied
operation. Preserve existing checkpoint sidecars as well as the checkpoint. Create
another task artifact only when its output is authorized.

## What it writes

By default, one checkpoint file per task:

```
<project>/.preclear/<task-slug>/checkpoint.md
```

Optional files next to it:

- `checkpoint-<UTC-timestamp>-<4-char-random>.md`, a frozen copy. Written only
  for a handoff, a move to another person, machine or worktree, a project rule,
  or shared sessions. Never overwritten, nor are the sidecars it cites.
- `status.txt`, a sidecar with the full `git status` when it is long.

Other facts go to their existing owners (your memory files, your plan file) in
their own format, only when they are durable and not recoverable elsewhere.

preclear never edits `.gitignore`. If `.preclear/` is untracked it tells you once.
You decide whether to track it.

## Budgets

- Checkpoint: under 4,096 bytes, six fixed headings.
- Resume package (checkpoint, resume line, required excerpts): under about
  6,000 bytes, roughly 2,000 tokens estimated as `ceil(bytes / 3)`.

preclear prints the measured bytes. The token figure is an estimate, not a
tokenizer count. Byte measurement may be unavailable under your tool
permissions; unchecked sizes are reported as `UNCONFIRMED`, and an estimate never
certifies a cap.

## Configuration

None is needed. If you already keep a ledger or handoff system and want preclear
to write through it, see `references/configuration.md`. Backends are opt-in only.
Finding a helper or a ledger on disk never activates one.

## Safety

Hard rules, as stated in `SKILL.md`:

- **Git is read-only.** `git status`, `git log`, `git rev-parse`, `git branch`,
  `git diff` are fine. Never `commit`, `push`, `add`, `stash`, `checkout`,
  `reset`, `rm`, or anything that mutates git state or the index. This also
  binds any helper you call.
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

## Limitations

- It is a procedure the model follows, not a hook. Nothing enforces it.
- It cannot control what the next session does with the checkpoint.
- Token numbers are estimates.
- It does not install, bind, or configure anything for you.

## Tests

See `tests/acceptance.md`. Fixtures are in `tests/fixtures/`.

## License

MIT. See `LICENSE`.
