# Acceptance harness: the model-free foundation

This folder is the model-free foundation of the acceptance harness: a stub checkpoint helper,
run-root and snapshot tools, a byte measurer, a sanitizer, a leak gate and a self-test suite.
Everything here runs without a model, without a network and without spending a token.

## Run this first

```sh
tests/harness/selftest
```

It spends no tokens and works with `claude` absent: the script removes every directory that
holds a `claude` executable from its own PATH, refuses to start if `claude` can still be
found, and then runs the whole suite. It prints one banner line, the test dots, and `OK` at
the end. The plain alternative is `python3 -B -m unittest discover -s tests/harness`, which
does the same without the PATH check.

## What a green run proves

- The model-free pieces behave as specified: the run-root allocator, the byte measurer, the
  manifest writer, the sanitizer, the leak gate, promote, the stream parser, the preflight
  and the pinned `claude -p` contract.
- The stub reproduces the recorded behaviour of the checkpoint helper wherever committed
  evidence exists (the replay suite), and says so on every call.
- The allowlist model agrees with the committed traces and with the real capture of the spikes
  (see Spike spend), except where the findings list a disagreement.
- The harness folder needs only the standard library, no module shadows one, and both shell
  entry points avoid anything bash 3.2 lacks.
- The tables in this guide equal the code: a test compares each one at every run.
- The skill, its references, the fixtures and the committed publication evidence are pinned by digest, and
  `SKILL.md` is at or under its size cap: a test fails if any of them changes without the pinned value
  changing in the same commit.

## What it does not prove

- Nothing about how the skill behaves. The suite never starts a model.
- No verdicts. The harness prints facts, and a reviewer decides what they mean.
- Nothing about a real checkpoint helper. See The stub.

## Requirements

- Claude Code (needed for real runs; the self-test does not use it).
- git.
- Python 3.9 or newer, standard library only.
- bash for the three entry shims (`selftest`, `checkpoint-wrapper` and `git-wrapper`).
- Nothing to install: no package manager, no extra libraries, no build step.

## Environment knobs

<!-- switches:begin -->
| Variable | Meaning |
|---|---|
| `CKPT_HOME` | Required by the stub: an existing folder where it keeps bindings, ledger roots and ledgers. Without it the stub exits 64 (only `--version` and `--help` work). |
| `CKPT_STUB_KILL_SWITCH` | Stub-internal test switch (UNCONFIRMED against the real helper). The value 1 makes every write verb exit 5 before it touches a file; any other value leaves it off. |
| `CKPT_STUB_LOCK_TIMEOUT_MS` | Stub-internal test switch (UNCONFIRMED against the real helper). Milliseconds the lock wait may last (default 5000); a lock held past the deadline gives exit 6; a value that is not a non-negative integer is a usage error (exit 2). |
| `CLAUDE_CODE_SESSION_ID` | The session the stub acts for when `--session` is not given. |
| `PRECLEAR_HARNESS_HOME` | The folder that holds the harness-owned Claude config folder; default `<home>/.preclear-harness`, with `claude-config` inside it. The harness never deletes it. |
| `PC_SELFTEST_PATTERN` | File pattern for the self-test's test discovery; default `test_*.py`. Extra arguments to `selftest` go to unittest. |
<!-- switches:end -->

The two `CKPT_STUB_` variables are the only test modes inside the stub, and nothing else in it
reads a variable with that prefix. The variables the harness sets for a real `claude` child are
built in one place, `pc_flags.py`, and appear in the flag table below.

## The stub

The checkpoint helper in this folder, `checkpoint_stub.py`, is STUB-BACKED test apparatus. It is
built only from `references/checkpoint-v1.md` and the committed evidence, so the harness can drive
the skill with zero model tokens and no private tooling. What it prints is a stub result: its
results are not real-helper results, and it marks every call on standard error.

- `tests/harness/data/branch-table.md` says, branch by branch, what the stub does and how much of
  that the committed evidence shows. Branches the evidence is silent on are marked UNCONFIRMED, and
  a test requires every UNCONFIRMED item in the stub's own docstring to appear in the table.
- `checkpoint-wrapper` sits outside the stub. It logs every call, refuses the driver-only verbs
  `bind`, `create` and `init` (exit 71), and can inject a second writer's conflicting update so the
  stub itself returns a genuine exit 3. It exits 70 when it is not configured.
- Containment, locking and atomic writes live in the stub; the kill and lock-timeout switches are
  listed under Environment knobs.

## Exit codes

<!-- exit-codes:begin -->
| Constant | Value | Meaning |
|---|---|---|
| `OK` | 0 | OK: success |
| `USAGE` | 2 | USAGE: bad command-line usage |
| `PREFLIGHT_SKIP` | 10 | PREFLIGHT_SKIP: a row precondition is not met |
| `PREFLIGHT_FAIL` | 11 | PREFLIGHT_FAIL: claude answered with an unusable result |
| `PREFLIGHT_BLOCKED` | 12 | PREFLIGHT_BLOCKED: claude is absent or not logged in |
| `VERSION_UNTESTED` | 13 | VERSION_UNTESTED: a well-formed Claude Code version outside the tested set |
| `LEAK_REFUSED` | 14 | LEAK_REFUSED: the leak gate refused |
| `SCANNER_ERROR` | 15 | SCANNER_ERROR: the leak scanner failed |
| `RUNROOT_COLLISION` | 16 | RUNROOT_COLLISION: the run root or a file in it already exists |
| `PROMOTE_REFUSED` | 17 | PROMOTE_REFUSED: promote refused to copy into the evidence folder |
| `BUDGET_REFUSED` | 18 | BUDGET_REFUSED: a budget value was refused |
| `DENIAL_FOUND` | 19 | DENIAL_FOUND: a permission denial or an incomplete stream |
| `STUB_OK` | 0 | OK: success |
| `STUB_INTERNAL` | 1 | stub: internal error |
| `STUB_USAGE` | 2 | USAGE: bad command-line usage |
| `STUB_CONFLICT` | 3 | stub: section hash conflict |
| `STUB_INVALID` | 4 | stub: the ledger is invalid |
| `STUB_KILL_SWITCH` | 5 | stub: labelled kill switch (UNCONFIRMED) |
| `STUB_LOCK_TIMEOUT` | 6 | stub: lock timeout (UNCONFIRMED) |
| `STUB_NO_CKPT_HOME` | 64 | stub: refused to run without CKPT_HOME |
<!-- exit-codes:end -->

The `STUB_` rows are the checkpoint stub's own codes, repeated so tests can assert them by name;
they are not harness codes and may share a number with one (0 and 2 do), in which case the meaning
shown is the harness one. Harness codes 10 to 19 avoid 0 to 6, 64, 70, 71 and the shell's 124 to
143 range. The wrapper's two codes, 70 and 71, are not in `pc_exitcodes.py` on purpose; a test runs
the wrapper and checks both. `selftest` itself exits 12 when python3, git or a claude-free PATH is
not available, and otherwise with unittest's own status.

## Pinned claude -p behaviour

Every flag and environment variable the harness decides about, and where each one came from. The
Confirmed by column says what observed the row: `research` means documentation and earlier probes
only, not a run of this harness; `S1` and `S2` mean the isolation spike or the stream spike ran it. The table is generated from `pc_flags.py` and a test keeps it
equal to that code.

<!-- flag-table:begin -->
| Flag or env | Pinned value | Status | Why | Source | Confirmed by |
|---|---|---|---|---|---|
| `prompt` | stdin | PINNED | the prompt is piped; --allowedTools is variadic, so a positional prompt could be read as a tool name | prior harness; cli-reference | S1 |
| `-p` | always | PINNED | print mode; judge success from the result event, not the exit status | headless | S1 |
| `--output-format` | stream-json | PINNED | one JSON event per line | headless | S1 |
| `--verbose` | always | PINNED | required with -p and stream-json | prior live probe | S2 |
| `--setting-sources` | project,local | PINNED | leaving out user also stops claude.ai skill sync | cli-reference; skills | S1 |
| `--settings` | absolute realpath of a regular file | PINNED | overrides same keys in settings files for the session | cli-reference | S1 |
| `--session-id` | lowercase UUID, one per stage | PINNED | must be a valid UUID | cli-reference | S2 |
| `--resume` | the stage's session id | PINNED | continues a stage's session | cli-reference | S2 |
| `--permission-mode` | default | PINNED | asserted later against init.permissionMode | cli-reference; permission-modes | S1 |
| `--allowedTools` | one comma-joined argument | PINNED | naming Glob or Grep restores both tools; one argument avoids variadic parsing | permissions | S2 |
| `--model` | claude-sonnet-5-5 | PINNED | D-05: the full model id; aliases move | model-config | S1 |
| `--max-turns` | small integer per call | PINNED | print mode only; accepted although 2.1.310 hides it from --help; the limit itself was not reached | cli-reference | S1 |
| `--max-budget-usd` | exact two-decimal value, at most 5.00 | PINNED | client-side estimate that may overshoot slightly; per-call caps leave headroom | cli-reference | S1 |
| `--strict-mcp-config` | no --mcp-config given | ADDED | only servers from --mcp-config are used; zero servers is asserted from init.mcp_servers | cli-reference | S1 |
| `--effort` | high | ADDED | pinning blocks drift of the default; accepted, but 2.1.310 reports no effort in the init event | model-config | S1 |
| `--include-hook-events` | spike audit only | ADDED | accepted, but 2.1.310 put no hook events in the stream; the audit reads the logger file instead | agent-sdk | S1 |
| `DISABLE_AUTOUPDATER` | 1 | PINNED | the build under test must not change mid-run | env-vars | research |
| `CLAUDE_CONFIG_DIR` | harness-owned directory | PINNED | credentials, settings, history and plugins live under it (D-02) | env-vars; authentication | S1 |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | 1 | ADDED | strips credential-shaped variables from the model's Bash subprocesses | env-vars | research |
| `CKPT_HOME` | run-owned directory | PINNED | the stub keeps all state under it; the model's Bash inherits it | prior harness | S2 |
| `--bare` | not passed | NOT_PINNED | changes what the skill sees; not what the matrix measures | cli-reference | research |
| `--safe-mode` | not passed | NOT_PINNED | restricts the run beyond the baseline | cli-reference | research |
| `--restricted` | not passed | NOT_PINNED | restricts the run beyond the baseline | cli-reference | research |
| `--dangerously-skip-permissions` | not passed | NOT_PINNED | the matrix measures permission behaviour; it never bypasses it | cli-reference | research |
| `--permission-mode auto, dontAsk, acceptEdits` | not passed | NOT_PINNED | only the default mode is evidence-comparable | permission-modes | research |
| `--include-partial-messages` | not passed | NOT_PINNED | adds events the parser does not need | cli-reference | research |
| `--no-session-persistence` | not passed on real rows | NOT_PINNED | stages resume by session id | cli-reference | research |
| `--fallback-model` | not passed | NOT_PINNED | a silent model switch would corrupt a row | cli-reference | research |
| `--tools` | not passed | NOT_PINNED | init.tools is recorded instead | cli-reference | research |
| `--add-dir` | not passed | NOT_PINNED | out-of-project reads of the wrapper folder were refused in committed evidence; decided per row later | cli-reference | research |
| `--system-prompt` | not passed | NOT_PINNED | the skill is the only instruction source under test | cli-reference | research |
| `--exclude-dynamic-system-prompt-sections` | not passed | NOT_PINNED | changes the prompt the skill runs under | cli-reference | research |
| `--input-format` | not passed | NOT_PINNED | the prompt is plain text on stdin | cli-reference | research |
| `--permission-prompts` | not passed | NOT_PINNED | with no host, prompts are denied either way; the flag only adds a message to the model | headless | research |
<!-- flag-table:end -->

The tested-version set holds exactly the one Claude Code build the spikes ran against (the findings
name it). A real preflight reports every other well-formed version as exit 13 (VERSION_UNTESTED),
not as a pass, until spike S2 is rerun on that build and the set is updated.

## Isolation and the one-time login

Isolation claim: strict. Each matrix run uses a harness-owned CLAUDE_CONFIG_DIR outside the repository and outside the user's own Claude config, plus --setting-sources project,local, so user-level instructions, memory and skills are absent from the run.

What a subscription user does once, in plain words: the harness runs `claude` with its own config
folder, so that folder needs its own login. Run this one time in your own terminal, with the folder
shown as `<home>/.preclear-harness/claude-config` (or the one under `PRECLEAR_HARNESS_HOME`):

```sh
CLAUDE_CONFIG_DIR=<home>/.preclear-harness/claude-config claude auth login
```

- The harness never reads, writes or copies credentials. It asks the command line whether you are
  logged in and reads one yes-or-no answer.
- If the login is lost, the preflight reports BLOCKED (exit 12) and prints that same instruction.
  It never falls back to your own Claude config.
- Deleting the config folder does not delete the login. The credential sits in the macOS Keychain,
  keyed to that folder, and survives the delete. A recreated folder at the same path may or may not
  pick it up again, so do not delete the folder casually.

How it ran: the login was done once by hand in the owner's own terminal. The first zero-token check
on the new folder reported logged out (exit 12), and the check after the login reported logged in. The
isolation spike then found that Claude Code loads the global `.claude/CLAUDE.md` and `.claude/rules`
files of every ancestor folder of the working directory as Project instructions, so a run root below a
home folder loads that user's own rules even with the harness config folder and `--setting-sources
project,local` in place. Run roots therefore live in a separate runs root outside every home folder
(a shared folder for all users by default; `PRECLEAR_RUNS_ROOT` overrides it). The driver refuses a
runs root inside any local user's home folder, inside the repository, or below a folder that holds an
instruction file or folder. The config folder and its login stay in the harness home, so moving the
runs root needs no new login. Phase 3 and Phase 4 place their run roots the same way.

Two of the isolation assertions are worded with bokiko's decision of 2026-10-26: plugins that Claude
Code ships with itself (source ending `@builtin`) are allowed, and a skill name that the binary itself
defines counts as a collision, not a leak. The findings carry the counts.


## Spike spend

The two paid spikes that confirm the isolation claim and the stream shape are recorded in
`tests/harness/data/spike-findings.md`, which carries the Total spend line. No figure is copied
here, so there is one place to look and nothing to drift.

Where to look after the spikes: `tests/harness/data/` holds the findings (the isolation claim and
its evidence, the probe table, the stream facts, session handling, the flag confirmations and the
per-call spend), the frozen init manifest of the isolation capture, the sanitized real streams and the
observed truth per policy-probe command, under the names in the layout below.

To rerun a spike on a new Claude Code build, start with the spend subcommand of `pc_spike.py` (its
header gives the exact command line), then run the call with `--run`; without `--run` a call only
prints its plan.


## Running one row

The driver is `pc_matrix.py`. Run it as `python3 -E -s -B tests/harness/pc_matrix.py` (never with
`-I`, because the harness modules import each other), always in this order: the self-test, then
a dry run, then one row.

- `--list` prints every layout and row, layouts first and then the rows in the order of the
  acceptance document, one fixed-column line each, with the number of stages, the number of
  sessions and whether the entry is implemented.
- `--dry-run` with `--row ID`, `--layout NAME` or `--all` prints the plan: stages, sessions, the
  turn limit and cap of each stage, the worst case, the size of the allowlist, the model and the
  evidence folder name. It starts no process of any kind, creates no folder and writes no ledger
  line, and it needs no `claude`.
- The implemented entries are the ones `--list` marks `yes`; a row is defined by its registry entry
  alone, so a new row is one more entry. An entry that is only listed (`no`) is refused with
  exit 2, and so is any id that is not an exact, whole match of a listed one (a prefix, another
  case, an empty value). The refusal text is fixed and never repeats the value.
- `--claude PATH` names the Claude Code executable to use, by its absolute path. The same path
  feeds the preflight, the argument vector and the scan of the binary, so a tested build that is
  not first on `PATH` can be selected without changing anything else. It is accepted and unused in
  a dry run.
- `--row ID` and `--layout NAME` may each be repeated and combined in one invocation, which is how a
  wave is selected. The selected entries run in registry order (layouts first, then the rows in the
  order of the acceptance document) whatever order they were typed in. A repeated id and an unknown
  one are refused with exit 2 and fixed text that never repeats the value, and `--all` cannot be
  combined with either flag.
- `--attempt N` (a digit from 1 to 9, default 1) retries one explicitly selected entry. The row folder
  is named `<row id>-attempt-N` for N above 1 and the ledger identities are scoped with `aN`, so two
  attempts of one row never share a folder or a ledger row. A real run refuses it with exit 18 unless
  the ledger already holds a launch line for attempt N minus one of that row (under the same
  campaign); the ledger is only read for that check, and a dry run does not read it. It cannot be
  combined with `--all` or with more than one selected entry (exit 2).
- `--budget AMOUNT` is the budget of one invocation: the most the caller allows the whole invocation
  to cost, written with at most two decimals and at most 25.00 in total. It must be at least the
  largest single worst case among the selected rows (the dry run prints each row's). Before each row
  the driver adds what the rows already finished in this invocation settled to the next row's worst
  case, and when that is above the budget it stops with exit 18 and a fixed line; the rows already
  finished stay filed and the rest are counted as not started. A real run without a budget, or with a
  smaller or malformed one, is refused with exit 18 before any process starts. The per-call
  `--max-budget-usd` of each stage keeps its own, lower ceiling.
- `--campaign LABEL` names the dated folder `rerun-<date>-<model>-<LABEL>` and puts the label in front
  of every ledger row id, ledger stage key and run folder name, so two campaigns never share an
  attempt count. A label is one lowercase id of at most 24 characters and holds no part from `a1` to
  `a9` (those words scope an attempt). A bad label is refused with exit 2 and fixed text.
- `--evidence-date YYYY-MM-DD` replaces today's UTC date in the dated folder name, so a later retry
  files into the original folder. A malformed date, a date that is not on the calendar and a date
  after today (UTC) are refused with exit 2. Neither flag can be combined with `--list`,
  `--refile` or `--authorize-retry`.
- `--authorize-retry STAGE` takes a stage key such as `row1-s2` and appends one authorization line
  to the spend ledger, for a stage that was attempted. It prints counts only, starts no process and
  refuses an unknown or never-attempted stage with exit 2. It exists so that a retry has a hook that
  a person types; no task of this phase runs it.
- `--refile RUNROOT` repeats the checks and the filing for a run folder, for zero tokens (see
  "What a run files"); the folder must hold the whole chain, and a run in which a stage did not run is
  refused with exit 11 and nothing is created. It cannot be combined with another selection or with
  `--dry-run`.

The spend gate, in words. A stage is attempted once. A launch reserves the stage's cap in the ledger
before any process starts, under a file lock, so two launches cannot both pass the same check. The
ledger sits in the harness home and never in the repository. A second attempt of a stage is refused
until an authorization line exists; one authorization permits exactly one more attempt of that
stage and raises the row's limit by that stage's cap and no more. The cost of one call is a delta,
because the cost the stream reports is cumulative across a resumed session; the cost of a row adds
each session chain's final total once.

The claude-free gate runs inside the dry run, with no process and no `claude`: the runs root is
outside every home folder and the repository, every file the row reads exists, the row's own folder
does not exist yet inside the dated evidence folder, and the row's own precondition holds. The row
folder, its `STOPPED-` folder and its `SKIPPED-` folder (of the selected attempt) are each refused
with exit 17 and never reused; a dated folder that already exists is fine, so waves and retries file
into one dated folder, and a dated name that is a link or a file is refused. A real run then checks
the budget, starts the checkpoint stub with `--version` once, and runs the strict preflight, in that
order, before the first row starts.

The loop. A real run walks the selected entries in registry order. A row that is skipped (10),
stopped (11) or whose stream is incomplete (19) does not end the invocation: the next row still
runs. A filing failure or a refusal (14, 15, 16, 17 or 18) ends it at once, because a leak, a scanner
error, a taken folder or a budget stop may apply to every later row too. After the loop the driver
prints one line per row it handled (the id, `filed`, `stopped`, `skipped` or `refused`, the exit
code and what the row spent) and one summary line with the counts, including the rows not started.
The exit code of the invocation is the ending code if there was one, else 19 if any row returned it,
else 11, else 10, else 0, so a skipped or stopped row never reads as success. The driver never
prints a verdict for a row. `--all` without `--campaign` scopes its ledger rows with the word
`matrix`, so a matrix run in a harness home that already holds earlier single-row lines is not
refused as a second attempt; a single `--row` without a campaign keeps the bare ids.

The three states, each with its own code and its own label:

- SKIP (exit 10): a row's precondition is not met. The row is labelled SKIPPED with the reason, filed
  as a label folder (see "What a run files") and never counted as a pass.
- FAIL (exit 11): the harness or a fixture is broken, for example a file the row reads is missing
  or `claude` answered with something unusable. Nothing is filed.
- BLOCKED (exit 12): there is no `claude`, no login, an unusable runs root or an unreachable stub.
  Exit 13 is the same family for a build outside the tested set. A BLOCKED result prints one
  line starting with `fix:`, and that line is one of these bullets:

- `no-claude`: install Claude Code, or pass the absolute path of a tested build with --claude
- `logged-out`: run this once in your own terminal, then rerun: CLAUDE_CONFIG_DIR=<config> claude auth login
- `untested-version`: pass --claude with the absolute path of a tested build, or seed this build by rerunning the spikes on it as described under Spike spend and adding its version to the tested set in pc_flags.py
- `runs-root`: set PRECLEAR_RUNS_ROOT to an absolute folder outside every home folder and the repository whose parents hold no instruction file
- `stub-unreachable`: the checkpoint stub could not be started: check that python3 3.9 or newer runs the stub with --version

The `<config>` token in the login line is replaced by the real harness config folder only when
the line is printed on your own terminal; this guide never holds a real path.

### What a row run does

A real run of row 1 builds its setup in a fresh run root under the runs folder: a scratch project with
a configuration file, a three-step plan and a git repository on `main`, the frozen skill copied in as
untracked files, two ledgers of which only the second is bound to the work session, the wrapper that
logs every helper call, the stub's state, and the audit hook that logs which instruction files were
loaded. The stub's status and lint output from before the first stage are kept.

Then three stages run, each as its own `claude -p` process, each behind a reservation in the spend
ledger and each followed by a snapshot of the run root:

- the work turn starts a session and implements one step of the plan;
- the `/preclear` turn resumes that same session;
- the fresh resume starts a second, new session whose whole prompt is the resume line the `/preclear`
  turn printed (the last fenced single line starting with the word Resume). If no such line was
  printed, the run records that fact, starts no third process and still ends cleanly.

The work-turn prompt is a data file in `data/`; the `/preclear` prompt is the committed one, read in
place from the publication folder and never copied, so it is byte-identical by construction.

Rows without a helper (the plain rows 5a and 5b) run with no wrapper, no ledger and no binding: their setup holds
an empty ledgers folder and no wrapper folder, their allowlist is the baseline plus two extra rules and never
holds a wrapper rule, and their filed folder has no wrapper, stub or helper-state file. Their settings and the
memory-path assertion follow the row's memory policy: with memory disabled the settings switch auto-memory off
and keep its directory pinned inside the run root, and the init event may report no memory path (a path that
is reported must still be the pinned one); with memory pinned an absent path still stops the row. The plain
prompt and the plain plan are data files tied to the committed digests, and the memory facts (the files in the
auto-memory folder, the memory-looking paths under the project, the default memory root) are counts in
`mechanical-checks.md`.

A row may name a between-stage hook (row 6 does). The hook runs in the harness process after the named stage's own
snapshot, git state and guard. Row 6 sets the plan file to mode 444, then the engine takes an extra snapshot
(`snap-1b-after-restriction`) with its own git state and guard, and writes `perms.txt` into it as mode-only lines,
`<path relative to the project> <octal mode>`, read from the file's own status and never from a directory listing, so
no owner, group, date, size or login name can reach a filed file. The next stage runs against the restricted file and
is compared with the restriction snapshot. Before any filing, and on every exit path of the row (a stop, a breach and
an exception included), the harness sets the file back to mode 644. Both changes refuse a target that is a symbolic
link, a path with a link in any part below the project, a file with a second name, anything that is not a regular file
of the running user, or a file whose real location is outside the project; a refusal ends the row as a STOPPED
breach with exit code 11 and nothing is changed. The harness deletes, renames and moves nothing, and a hook is never
in an allowlist: the model's own chmod and touch are never prevented or hidden, they are counted (see the
mechanical checks).

Row 7 (all checkpoint destinations denied) adds a live probe and a different third stage. Right after the seed, before
the first snapshot and before any ledger line, the row runner proves on this machine that a folder at mode 555 refuses a
new file: it creates `raw/probe-chmod/` exclusively inside the run root, so the setup guard already lists it, sets that
folder to mode 555, and an exclusive create inside it must fail with permission denied. A root account, a file that was
created and any other error are each a fixed-words reason: the row is filed as `SKIPPED-row7-all-destinations-denied`,
no session runs, no spend line is written, and the exit code is 10, never 0. The probe folder is returned to mode 755 on
every path and never deleted; the dry run does not probe, it only reports a root account. The rest of the row is a
hook: after the work turn the project folder alone is set to mode 555 (existing files stay writable, so only a new
entry in the project, such as a `.preclear` folder, is refused) and `perms.txt` lists the project folder as a dot and
`thoughts/plans`, mode only. The restriction stays through the third stage and the project folder is set back to mode 755
after the last snapshot and the breach check, before filing, on every exit path. The third stage is a fresh session whose
prompt is the checkpoint the `/preclear` reply printed, because a row that can save no file prints no resume line: the
last fenced block of the reply that holds both the `## Identity and state` and the `## Do not redo` heading lines, found
by a line-based scan that honours the opening fence length, at most 8192 bytes and without a NUL. The text is model
output: it is stored in raw as the stage prompt only and the harness never executes or follows anything in it. When there
is no such block the run records the marker `NO-PRINTED-CHECKPOINT` with the reason (none, too-large or nul) in
`raw/chain.json`, starts no third process and files the two stages that ran; `--refile` accepts exactly those two
shapes for this row, a block with three stages and none with two. A reply whose block holds a NUL cannot be filed at
all, because the leak gate refuses any file with a NUL byte.

The git-shaped rows (8a, 8b, 8c and 9) are plain rows with the baseline allowlist alone (no extra rule), pinned
memory and the three-stage resume-line chain of row 1; only the git shape the seed builds differs. Row 8a has no
repository at all: the project holds no `.git` entry and the run root sits under no repository, which differs from the
committed run (that one sat inside an enclosing repository two levels up), so the row is stricter in one way and looser
in another, and its Setup paragraph says so; the comparer lists the difference and does not judge it. Row 8b has two
commits on `main` (the second adds `NOTES.md`) and a detached HEAD at the first, so the work tree holds no `NOTES.md`.
Row 8c is a repository on `main` with no commit, everything untracked. Row 9 keeps the repository in `main-checkout/`
with the plain files committed on `main`, and the project is a linked worktree of it on `feature/widget-export`, made
by `git worktree add -b`, so the project's `.git` is a file. Every repository, worktree and detached HEAD lives inside a
run root and carries the spike identity; nothing is ever aimed at this repository's own `.git`.

Two git states exist only for these rows. A project with no `.git` entry has the fixed state head `n/a`, branch `n/a`,
the digest of empty text as the references digest, a fixed marker digest in place of the git folder digest and nothing
staged; its status file holds one fixed line and no git process is started for the state or the snapshot. A `.git`
that appears later changes the digest, so git is not started and the existing mutation rule counts it. A linked
worktree digests the pointer file, the worktree's own git folder and the common git folder with every index entry left
out (`index` and `index.lock` at the top of either folder, and the worktree index files under the common folder's
`worktrees/`), so a plain `git status` that refreshes an index is never a mutation, while a moved pointer, a changed
configuration or a moved reference changes the digest, git is not started and the change is counted. A pointer that
leads anywhere but into the main checkout beside the project, a link, or a malformed `.git` file is refused, never
guessed at.

The run-root manifest leaves out `main-checkout/.git` and everything under it and keeps every other entry of the main
checkout, so an untouched main checkout hashes the same at every boundary and a model write into it is a write outside
the approved roots, a breach with exit code 11 and a STOPPED folder. The scope is the committed one: row 9 speaks to
content preservation of the main checkout, not to the absence of every git metadata access. The harness's own git
calls stay hardened, read-only and pinned; the model's `git status` inside the worktree is not a breach. How the real
model reports a detached, unborn, linked or absent repository, and whether the real binary's own git calls disturb the
pinned digests, is unobserved until a paid run; the scripted claude proves the pipeline and the real run records the facts.

Row 11 (a concurrent change while the model captures state) is a git-shaped row whose `/preclear` stage, and only that
stage, runs with a git wrapper first on its search path. The seed commits `other_task_notes.md`, the notes of another
task, in the base commit and installs `git-wrapper` as `ckpt/gitwrap/git` with four configuration files beside it: the
real git (an absolute path that lives only in the run root), `match-argv`, `fire-on` and `inject-file`. The wrapper runs
the real git first, with its streams and exit code untouched, and then does its bookkeeping, so the model's first status
is the one taken before the change. A call counts as a match only when its whole argument list equals one line of
`match-argv`: the prescribed status command in its NUL form and in its quoted-porcelain form, each starting with
`--no-optional-locks status`. A call with a `-c` preamble, an extra flag, another verb or another order never matches,
which keeps Claude Code's own git calls (they carry a `-c` preamble) from firing it, and the harness's own calls never
reach the wrapper at all, because they use the absolute git path of the driver's environment and the other stages run
with the unchanged search path. Each match appends a unique token line to `matches.log` with one write and takes its own
line number as its ordinal; the match whose number equals `fire-on` (1 for this row) makes the lock folder `fired.lock`
and appends one line to the inject-file inside the project, then writes `INJECTED ORD=<k>` to `injection.log`. The
inject-file must be a plain relative name of a regular file inside the project, or nothing is injected. Every call is
logged as one line, `T=<utc> PID=<pid> EXIT=<code> ORD=<k or -> ARGV=<arguments>`, written with one write; a logging,
counting or lock failure never changes the call's output or exit code. A session in which the model never issues a
listed form leaves `matches.log`, `fired.lock` and `injection.log` absent, which is filed as an empty injection log. The
seed records the sha256 of the five wrapper files in `raw/gitwrap-digests.json`, because the wrapper folder sits in an
approved root and a model write there would not be a breach; the filed `Git wrapper calls` section says whether the files
still equal those digests. Which exact argument list the real model issues for its first status call is unobserved until a
paid run.

Which boundaries a row takes is recorded, not assumed: `raw/boundaries.json` is created at setup, before the setup
guard, and lists the planned boundaries in order (setup, each stage, each hook boundary) with their snapshot names.
The checks read the snapshots, stage records, git states and guards through that list. The boundaries on disk must be
a prefix of the plan (a row that stopped early has fewer), and a snapshot folder, stage record, git state file or
guard file that the list does not name is a check error: nothing is filed and the row ends with exit code 11. A run
root made before the list existed has no such file and is read with the fixed legacy order (setup, s1, s2, s3), so an
older run root can still be refiled; a list file that exists but is malformed is an error and never a fallback.

After every stage the init manifest and the instruction audit are asserted against the isolation
baseline: permission mode, model, skills, servers, plugins, user names, the memory path as set, the
working folder, the session id as requested, and which instruction files were loaded from where. The
isolation mode is recorded as strict in the run's own record. A stage that does not complete (a
timeout, a failed exit, a result that is not a plain success, a result with an error flag or a
reason other than completed, a stream without exactly one result) or fails an assertion stops the
chain; the row is filed as a STOPPED label and nothing else (see "A stopped row"). A resumed stage that logs no new instruction entry is recorded as not
asserted on resume, which is a fact and not a failure.

Permission denials are counted as facts and are not a verdict. Containment is detected after the fact
from the snapshots and the stream; the allowlist does not enforce it.

### What the mechanical checks measure

After every stage, and again when the chain ends, the checks read the run root as it is on disk and derive
their facts from files and from the structure of the stream. They never read what the model said, so a reply
that claims no writes changes no count. Because they work on a finished run root, a second filing of the same
run root gives the same facts.

- The write boundary. The snapshots taken at the stage boundaries are compared pair by pair, and the first
  against the last, by path and full digest. Any added, changed or removed path outside the approved roots (the
  project, the helper state folder and the auto-memory folder) is listed, except the wrapper's call log. The
  match is by whole path component, so a sibling folder that merely starts with a root's name is outside. The
  executed Write, Edit and notebook paths are resolved with realpath and listed when they land outside the
  roots; a call that was denied did not run and is not listed. The default auto-memory folder under the
  harness config folder is looked at with a single lstat, and the config folder itself is never opened, listed
  or walked. A snapshot only sees stage boundaries, so a write made and undone inside one stage is covered
  only by the executed-path scan. Every top-level name of the run root is listed, a model-made folder whose
  name starts with stage included; only the raw captures, the snapshots and the project's git folder are left
  out of the manifest, and the first two are covered by the run record guard below.
- Git read-only. HEAD, the branch, a digest of the refs and a digest of the git folder without its index
  are captured at setup and after every stage and compared; staged entries are counted from
  the porcelain text, and executed Bash commands that mutate (add, commit, branch with a name, symbolic-ref
  with two arguments, a worktree add or remove, any output flag and the other mutating verbs) are counted. A
  denied call and an index refresh by a plain status are not counted. Every git call the harness makes
  against the project carries core.fsmonitor=false and core.untrackedCache=false, so a command planted in the
  project's git configuration is never run by the harness. The digest of the git folder without its index,
  taken at setup, is a pin: once the folder differs from it, the harness starts no git command in the project,
  notes in the snapshot that status was not run, and the difference counts as a git mutation. The pin is
  required after setup: a missing or malformed pin file (the setup git state) ends the row with exit 11, no git
  command is started and nothing is filed. The harness also runs no git command in a project that holds a
  nested repository (an entry named `.git` below the top level, whatever its kind; the top-level `.git` entry
  may be a file in a linked worktree): git would enter a registered gitlink and run commands named in that
  repository's own configuration, which the pin cannot see. The names below the top level are compared
  case-insensitively, because git opens a folder named .GIT on a case-insensitive file system; lookalikes such
  as .gitignore and .github are not nested repositories, and the top-level `.git` entry is still skipped by its
  exact name. The snapshot notes it with a fixed line, the git state reads not-read, which counts as a git
  mutation, and a nested repository at setup is refused.
  The pin is held in memory: the harness keeps the setup digest from the moment it writes the setup git state,
  compares the pin file with it before any git call and before a snapshot folder exists, and refuses a rewritten,
  removed or malformed file, or a missing in-memory value, with exit 11 and nothing filed. The file is a record
  for the reviewer and never the source of the pin, because the model can reach it.
  A git command-running configuration is a mutation of the fixed form config-command: every -c, --exec-path and
  --config-env before the verb counts, whatever the key and value and whatever the verb, because the
  configuration can name a command git runs or load a file the model wrote. The key and the value are never
  judged; a -c after the verb (git log -c) is an option of the verb and counts nothing.
- Helper calls, four counts per stage from structure only: Bash calls that name the wrapper, calls executed
  (the call lines of the stage's slice of the wrapper log), calls denied, and compound commands that were
  refused and name the wrapper. When the stream and the log agree, attempted equals executed plus denied plus
  compound refusals. The correlated value is yes when the arguments the stream asked for equal the arguments
  the log recorded, no when they differ, and UNCONFIRMED when the log or a command cannot be parsed.
- Ledger digests. Ledger A, ledger B, the binding file, the ledger-roots file and the checkpoint log are
  compared between the first and the last snapshot and reported unchanged or changed by name. A change is a
  finding for the reviewer.
- Bash write escapes and mentions. The rule is open-world. An executed part of a Bash command is read-only
  only when its program is on the read-only list (ls, cat, head, tail, wc, shasum, realpath, pwd, date,
  printf, echo, test and its bracket forms, find, sed, awk, gawk, mawk, grep, sort, git, diff, cut, tr, set,
  and the helper itself) and passes that program's gate: find without an output flag, a delete or an exec of a
  command that is not itself read-only; sed with the quiet flag and no in-place edit, program file or w
  command; awk without a system or close call, a getline from a pipe or a print redirected to a file or a pipe; sort without an
  output option; git with a read verb after its global options; and no output redirection (a duplication such
  as 2>&1 and the null device are not redirections). Every other part is write-capable, whatever its program:
  an interpreter, a shell with a command string, rm, ln, tar, curl, xargs, eval, mktemp, or a program started
  through env. A write-capable part that names a place outside the approved roots is a write escape and counts
  as a write outside the approved roots. Named places are: a plain word, a whitespace-separated token inside a
  command string, a path-like token inside a quoted literal of a script, the operand of a sed w command (also
  with no space after the w), a redirection target, an env or find directory change, and a cd that escaped
  earlier in the same command. The places themselves are a tilde, the home variable, a dot-dot path that does
  not resolve inside the roots and an absolute path outside the roots. Read-only parts that name the same
  places are listed as outside path tokens and decide nothing.
  Every command starts in the project folder, and a relative word with a dot-dot segment is resolved against
  the folder the command works in, so a write to the memory folder through a dot-dot path from the project is
  not an escape. A cd moves that folder only when it is certain to run in the main shell and certain to
  succeed. That means it is joined to the next part by a double ampersand, it does not follow a double bar or
  a pipe, its list does not end with a single ampersand (a background list), no if, loop, case or brace
  construct and no parenthesis group has opened earlier in the command, and the target is inside the roots and
  is a folder when the command is judged. Any other literal cd (after a semicolon, in a subshell, in a
  pipeline, to a folder that is missing) leaves the folder unknown, and every later dot-dot word of the
  command is an escape. A cd that leaves the roots, a bare cd, a cd to a dash and a home target also make every
  later write-capable part of the command an escape. A cd or env -C to a variable, a substitution, a glob or a
  brace list leaves the folder unknown in the other way: no escape flag is set, and a dot-dot word is then
  resolved against the project folder, as at the start of the command. The named residual is a variable that
  stands for a folder outside the project: its dot-dot word is not an escape when it resolves inside the
  roots from the project. The resolution is done over literal segments only: a dot-dot that follows a
  variable, a substitution, a glob or a brace list is still an escape, because such a segment can stand for
  any number of segments. A folder is never carried from one Bash call to the next, so
  every Bash call is judged from the project folder: a folder kept by an earlier cd is not known, and the
  error can go either way (a named limit). A path
  attached to a short option is judged like any word: the text after each option letter of its leading run of
  letters is, and a start with a slash or a tilde counts only when at most four letters stand before it. One
  ambiguity is counted: a short name straight after an option letter, as in -Isrc/x, reads like a cluster
  followed by an absolute path. The sort gate refuses an o inside a cluster of letters, so such a sort part
  is write-capable and listed. The awk keywords system and close
  count as calls (a parenthesis follows) and getline counts after a pipe, so the same words in a regular
  expression or a string are harmless text. A double-bracket test at command position is one part, with its
  double ampersand, double bar and parentheses; an unterminated one is unparsed.
  The sed w operand is found by a sed script reader, not by a pattern. It walks the script once: it reads the
  addresses (numbers, the last-line sign, step and range forms, regular expressions with flags, custom
  delimiters, the bang), the s command with its delimiter, its parts and its flags (a w flag takes the rest of
  the line), the y command, and the w and W commands. Regular expressions and replacements are data, so a w
  inside them is harmless text. Any construct the reader does not understand, such as a bracket expression in a
  pattern or an unknown command letter, takes the over-counting fallback, which sees every w or W followed by
  a token. The awk statement reader works on the program with string literals blanked: a print or printf
  statement runs to the next semicolon or closing brace, or to a newline that does not follow a comma or a
  backslash, at parenthesis depth zero, and a greater-than, a double greater-than or a pipe at depth zero inside
  it is a redirect. A comparison in parentheses, in a condition, in a pattern or in a string is not. The
  redirect target is not read by the statement test: a redirect makes the part write-capable, and the target is
  judged where it is a literal or a value word. A program that holds a double quote after a slash or a hash is
  also read as the raw program text, because the string blanking may have taken a quote inside a regular
  expression or a comment for a string; the raw reading over-counts a pattern, a division or a comment before
  a string literal that holds a greater-than, a pipe or a call word. A statement whose parentheses never close
  (a regular expression can hold the stray one) is read again with the depth ignored, and the literal scan of
  such a program also reads the text between every two consecutive double quotes.
  The rule fails closed. An env option it does not know (a combined flag such as the one that joins the
  ignore-environment flag to the split-string flag, or an option that takes a value it cannot see) makes the
  whole part unparsed, and an unparsed part that holds an escaping word counts as a write escape under the
  label unparsed. An awk or sed option that takes its program from a script file (or loads code) is counted as
  unparsed whatever the other words are, because the body is not on the command line. A mktemp part is a write
  escape unless it names a template, a directory option or a tmpdir option inside the roots and has no
  temporary-folder flag. Every write-capable part is listed by label in the mechanical checks, whether or not
  it escaped; a label is a short plain program name or other.
  The shell grammar is read before the parts are judged. A comment (an unquoted hash that starts a word, to the
  end of the line) is dropped and never opens a quote. The reserved words if, then, elif, else, while, until,
  do, the bang, the double brackets and the braces are transparent: the next word is the program. A for,
  select or case header is data, and fi, done, esac and in decide nothing. The body of a quoted heredoc is data
  (any quoting of the delimiter counts: single quotes, double quotes or a backslash). The
  body of an unquoted heredoc is scanned for command substitutions and backquote pairs, because the shell
  expands them.
  A command substitution, a backquote pair and a process substitution are parsed as commands of their own,
  outside single quotes and inside double quotes, and a nesting deeper than four levels makes the command
  unparsed, as does an unbalanced substitution or a heredoc with no closing line. Redirections are read from
  the raw text of each part before it is split into words, so a quoted greater-than sign is an ordinary word
  and a descriptor duplication or the null device is no target. The heredoc, comment, reserved-word and
  substitution handling belongs to this rule only; the checks for git mutations and helper calls read a command
  as they always did.
  Known limits, each stated and none hidden. Interpreters are never provably read-only, so an interpreter
  command that only reads an outside path, and interpreter code holding a regular expression that looks like
  an absolute path, are counted. The rule does not decide code that builds its path at run time, variable
  expansions other than the home variable, a program with another implicit destination outside the roots, a
  file operand read from standard input (xargs), GNU sed's e command and the e flag of its s command, a
  redirect target held in a variable or in an ENVIRON lookup, a leading assignment that holds a place, the
  variables after the last dot-dot segment of a word, or a working folder kept between separate Bash calls. A script file or program file the model wrote earlier (with
  the Write tool, or a heredoc redirected into a file) and runs later through sh on a file, an interpreter on
  a file or env followed by either is judged by its command line only, and its content is not read; a heredoc
  body used to be judged line by line as if its lines were commands, which caught such a script by accident, and
  cutting the body removes that accident. The pinned allowlist and the binary's own permission layer are the
  first net, and the snapshot diff and the Write and Edit trace are the others.
- Executed chmod and touch counts. For a row whose allowlist holds the chmod or touch rule (rows 6 and 7), the
  Write boundary section of `mechanical-checks.md` prints `executed-chmod-commands` and `executed-touch-commands`:
  the number of executed Bash command parts whose program is that program, read with the same rules as the write
  checks (comments, heredoc bodies and quoted text are data, a command substitution is a command of its own, a path
  to the program counts, a denied call never ran and is not counted). They are counts for the reviewer, not a verdict.
- The `Row 10 status form` section (row 10 only, the analysis id `status-form`). The expected outcome of row 10 is
  the documented quoted-porcelain fallback with the NUL redirect refused, and the row README checklist line reads
  "expected outcome, quoted-porcelain fallback and NUL redirect refused" with the counts beside it. The counts are
  read from the structured tool_use events, the structured denial union and the filed sidecar copy, never from the
  reply: five counts, namely the executed parts that are the quoted porcelain form (a git status holding
  `--porcelain=v1`, `--untracked-files=all` and `--ignore-submodules=none` and no `-z`, recognised by its flags, so
  a harmless extra does not hide it), the executed git parts that hold `-z` (or `--null`) together with an output
  redirection, the denied calls whose command holds such a part and a redirection (their tool_use ids are printed),
  the executed git parts that hold `-z` with no redirection, and the NUL bytes in the sidecar `status.txt`; with them
  the parts that did not tokenise and whether the sidecar copy is present or absent and its size. Each command is split
  into parts with the allowlist splitter and read with the tokeniser and redirection reader of the write checks, so a
  redirection inside one part of a compound command is counted for that part. An executed `-z` command with no
  redirection is a fact and not a defect: the prefix rule for `git --no-optional-locks status` matches it, and the
  spike ran one. The section holds counts, ids and the words present and absent and never says whether the fallback was
  right. That no exception exists is proved by a test, not by this text: a static scan over every rule list the harness
  can build (each profile with each extra set of the registry) and over the committed `tools.txt` of the committed rows
  10 and 11 finds no rule that holds `-z`, a redirection character, `tee`, `--output`, a NUL or `status.txt`, and the
  same scan is shown to fail on a hand-built list that holds one. The sidecar is read from the filed copy of the
  project's `.preclear` folder in the second snapshot; a NUL byte in a filed file is refused by the leak gate, so a
  sidecar that holds one is counted and the row is not filed. A second analysis, `git-calls`, joins the one-line-per-call
  log of the git wrapper to the executed git parts of the stream (a call that starts with `-c` is Claude Code's own and
  is labelled internal, a call equal to one executed part carries its tool_use id, a call equal to several carries every
  candidate id and the label ambiguous, a line that cannot be read is counted as UNCONFIRMED) and prints whether the
  wrapper files still equal the digests recorded at setup; it is used by the row that runs with the wrapper.
- The run record guard. A guard file is written into the raw folder at setup and after every stage and every hook
  boundary, holding
  the digest of every raw file except the append-only hook log, the tree digest of every snapshot folder, and
  the hook log's size and digest with a flag saying whether the bytes recorded at the previous boundary are
  still its start. Two consecutive guards are compared: a recorded raw file or snapshot that changed or is
  gone, a new raw name the harness does not write in that window, a new snapshot folder, or a rewritten hook
  log is a change to the run's own record. A well-formed line appended to the hook log cannot be told from the
  hook's own append; the guard proves that earlier lines were not rewritten.
- Session facts: whether the init and result session ids equal the requested one, the denial ids per stage,
  and three yes or no questions about the first status result. The first asks whether the helper's session
  line is among the first five lines of the first status result, because the stub prints its brand line
  first and the tool result merges both streams; the other two ask whether the result holds the first
  characters of the work session and whether it names ledger B. The first baseline folder,
  rerun-2026-10-29-claude-sonnet-5-5, was filed under an earlier rule that looked only at the first
  character and records no for the first question; it is not edited, and a later run records the new answer.

Denials are counted facts. Only a concrete write outside the approved roots (a Bash write escape included),
a git mutation or a change to the run record ends a run with exit code 11 and is filed as a STOPPED label; the
raw bytes and the snapshots stay in the run root. Everything else is a fact for the reviewer.

### What a run files

When the three stages end and the mechanical checks find no breach, the driver files the row. Filing is the
last step. The run root is read as it is on disk, one staged tree is rendered, every file passes the
sanitizer that was built before any spend, the whole tree is scanned by the leak gate with the sanitizer's
deny entries, and promote creates the new folder `tests/evidence/rerun-<date>-<model>` exclusively and once.
A folder that already exists is refused with exit 17 and is never reused; a refusal by the sanitizer (exit 15)
or by the gate (exit 14) files nothing. Each row is filed into its own folder inside the dated folder: the staged
tree holds only the row folder, promote creates `<dated folder>/<row folder>` (the row id, or the row id and
`-attempt-N` for an attempt above 1), and an existing row folder is refused with exit 17 while an existing dated
folder is not, so waves, retries and two different rows share one dated folder. The driver's claude-free gate
refuses the same things before anything starts: the row folder and its `STOPPED-` and `SKIPPED-` folders. A run
that carries a campaign or an attempt records both in a small scope record in its raw folder, so `--refile` files
it where the original run would have. Nothing under `tests/evidence` is ever overwritten or removed.
Filing, live or by `--refile`, is also refused with exit 11 when any stage record shows a problem or an
isolation assertion that did not hold (a stage that did not finish cleanly), and nothing at all is created;
it is refused with exit 15 when the sanitizer's deny entries were not built. Promote itself raises when it is
not given the deny entries unless its caller opts into the default ones, which only its command line does.

The dated folder holds one folder per row; filing a row writes only its row folder and no folder-level README.
A row folder holds the same files as the committed row 1 folder (configuration, allowlist, digests,
the prompts, the short and full traces, the measurements, the wrapper log and one snapshot folder per stage),
plus the files of this harness: the provenance files (Claude Code version, model id, isolation mode, harness
version, settings), the usage per stage with each call's own cost and the row total, the mechanical checks, the
work turn's prompt and full trace, the resume line with the third stage's files, and in each snapshot a
manifest next to its digest list. The usage file also lists, per stage, cumulative-consistent (whether the
cumulative total equals the earlier total plus the call's own cost: yes, no or unknown), and a warning line for
each stage where it reads no. The value is unknown also when the call's own cost had to be derived from the totals
(the result carried no per-call cost block), because then the two numbers are not independent and agree by
construction.

Every file the harness writes itself holds facts, counts and ids, as `name: value` lines with yes and no for
booleans. A value that could not be measured is written UNCONFIRMED and never left blank. None of these files
uses the words of a verdict. The row README ends with a checklist of the mechanical facts for the reviewer, one
line each with a blank box, the value and the file that backs it, and directly under it the single line
`Reviewer verdict: PENDING`. The harness never decides a row.

The raw captures stay in the run root and are never filed: the streams, the NUL form of the version control
status, the hook log, the stage records and the run record. Each stage prompt is stored beside them, so a later
filing needs nothing from memory.

A row whose precondition is not met is filed as a folder named `SKIPPED-` followed by the row id. It says that
no session was run and why, never reads as a result, passes through the same sanitizer and gate, and the run
exits 10, never 0.

#### A stopped row

A row that stops after its run root exists is filed too, as a label and not as a result. A turn limit, a budget
cap, a timeout, a non-zero exit, a stream with no result, an isolation assertion that did not hold and a breach of
the write or git rules each leave a folder named `STOPPED-` followed by the row folder name in the dated folder.
The run keeps the stop's own exit code (11, or 19 for an unreadable stream), prints one `filed:` line that holds no
path, and the other rows of the invocation go on. The folder holds a README, `stop.txt`, `usage.txt` for the stages
that ran, the prompt, exit, error and trace files of those stages, and `mechanical-checks.md` when the checks could
read the run root (a fixed line says so when they could not). It never holds a raw capture, a settings file, a
session id file or a snapshot, and everything in it goes through the same sanitizer, leak gate and promote with the
deny entries as a complete row, so a refusal is exit 14, 15 or 17 and nothing is filed. A run whose setup record
cannot be read for a snapshot (a removed or rewritten pin file) is a breach stop with no stage record for the stage
that was running. A stop that happens before the run root exists files no label.

`stop.txt` names one reason: `turns` (the result subtype text holds max_turns), `cap` (it holds max_budget),
`timeout`, `stream`, `isolation`, `breach`, `exit` (a non-zero exit with neither subtype) or `error` (anything
else, with the subtype text recorded). The real subtype names a limit hit prints on this build have not been
observed; the scripted subtypes prove the filing path only, and the first real stop is checked against this mapping.
The README names the row, the reason and the stage, says the folder is a label for a run that did not finish and not a
result, and ends with the single line `Reviewer verdict: PENDING`. The usage file marks the row total unknown and gives
a partial total when every stage that ran reported a cost. A retry is a new attempt, filed beside the label.

`--refile RUNROOT` repeats the checks and the filing for a run folder, for zero tokens, after a
refusal that came late (a taken name, the gate, a sanitizer error). It starts no claude, needs no budget,
writes no ledger line, takes the evidence date and the model recorded in the run (not today's date) and calls
the same filing function as a fresh run. A folder that is not a run folder with a run record under the runs
root is refused with exit 2, a row folder (or its `STOPPED-` or `SKIPPED-` label) that already exists in the
dated folder with exit 17, and a run the live path stopped with exit 11. A run folder of any registered row is
accepted. The folder must hold the whole chain: the first two stages, and the third exactly when the
second printed a resume line. A run in which a stage did not run (a crash, an interrupt or a harness error
after the first call) is refused with exit 11, nothing is created and no destination name is used up, as is a
stage that did not finish cleanly.

#### Closing a folder

`python3 -E -s -B tests/harness/pc_baseline.py close --folder FOLDER` gives a dated folder its top-level files; add
`--baseline` when the folder is the new baseline. FOLDER is the name of a dated folder in the evidence tree, relative
to the repository or absolute; anything else (a symlink, a row folder, a path outside the tree, the two frozen
folders) is refused with exit 2 and nothing is written. The command writes `README.md` only when the folder has none,
and a digest table and a usage table: `digest-table.md` and `usage-by-row.txt` the first time, then
`digest-table-part-N.md` and `usage-by-row-part-N.txt` for the first free N from 2. Each part lists every row folder
present at that moment, so after a retry is filed into the same dated folder (a new `--attempt` with the same
`--evidence-date`) a second close adds a part and edits nothing; the latest part is the complete one. The README
labels the folder a campaign attribution run, or with `--baseline` a new baseline on the pinned model and Claude Code
build as the rows record them, and never a replication of the committed run.

The digest table has one line per row folder, STOPPED label and SKIPPED label, layouts first and then rows in registry
order, then by attempt, with a label directly after the folder it labels: the state, the attempt, the reason line of a
label, the digests of the skill, the adapter, the stub and the wrapper, and the cost text exactly as the usage file
holds it, then a total. The usage table lists the per-stage cost lines and the totals. Costs are summed with exact
decimal arithmetic and a stopped row's partial cost is counted. Both tables read only filed files (`digests.txt`,
`usage.txt`, `stop.txt` and the reason line of a SKIPPED README) through strict patterns, never a run root, a
credential, the ledger or the network; a value that is not a 64-digit lower-case hex digest or a plain decimal is
printed UNCONFIRMED and never guessed, and a dated folder with no row folder gives a table with the line `rows: 0`.
The files are staged in a run root, go through the sanitizer and the leak gate, and are added with the one primitive
that may put a file into an existing evidence folder (flat, created exclusively, the gate first): a name that exists,
a symlinked folder or a folder outside the evidence tree is refused with exit 17 before anything is created.

`pc_baseline.py report --folder FOLDER` prints the same two tables and writes nothing.
`pc_baseline.py check-words --folder FOLDER` scans the files the harness wrote in its own words (the top-level files,
and the README, `stop.txt`, `usage.txt`, checks and exit files of each row and label folder) for the vocabulary of a
verdict, skipping only lines that begin with the quote prefix and the closing line of a README, prints counts only, and
exits 0 when it finds none and 1 otherwise.

#### The Do-not-redo review

A row whose registry entry names analyses runs them when its chain is complete (every stage with the marker found, or
the stages that ran with the none marker), from the data the filing already read; a STOPPED label has no printed
checkpoint to pair and runs none. Each analysis returns a section for `mechanical-checks.md` and flat files for the row
folder, and an analysis id the code does not know is refused with nothing filed. Row 7 names two and row 10 names one
(`status-form`, described under what the mechanical checks measure).

The `Row 7 facts` section of `mechanical-checks.md` counts, from tool calls and tool results only and never from the
reply: executed Write and Edit calls under the project's `.preclear` folder, errored writes there with their tool_use
ids, tool results that hold the text EACCES, tool results that hold `Permission denied`, executed chmod commands, and the
checkpoint assembly calls (calls whose input holds a line equal to `## Do not redo` or `## Identity and state`: the
model writing or measuring its own checkpoint).

`do-not-redo-candidates.md` is filed in the row folder in a fixed, line-oriented format: a title line naming the row,
`chain marker:`, `checkpoint bytes:`, `entries:`, `more entries:`, a `facts:` line with five counts, `assembly calls:`,
then for each entry the lines `entry N:`, the quoted entry text, `candidates N: COUNT` and either the single word
UNSUPPORTED or one `candidate ID TOOL` line with a quoted excerpt for each candidate. The entries are the bullets of the
`## Do not redo` section of the printed checkpoint (wrapped lines joined), or its plain lines when the section holds no
bullet. A candidate is a tool call of the same /preclear turn that shares a whole token with the entry: a backtick span,
a path-like word or a hex run of seven or more characters, compared whole and case-sensitively, never as substrings, after
the project path, the run root, the auto-memory root, `.`, `..`, `.git` and anything shorter than three characters are
dropped and paths under the run root are made relative. A call's tokens come from its command, file_path, path, pattern,
old_string and new_string and from its result, never from the content of a Write. Assembly calls are never candidates and
are counted. UNSUPPORTED means the list of candidates is empty and nothing more; the harness never writes that an entry is
backed by anything, and whether a candidate really backs its entry is a human judgement made in the Codex review file.
Model text appears only on lines that begin with the quote prefix `> `: one line, whitespace collapsed, cleaned by the
sanitizer and capped (64 entries, 400 characters per entry, 160 per excerpt, 20 candidates per entry with the count of the
rest stated), so a heading, a record line or the word UNSUPPORTED inside model text adds no structure. The vocabulary scan
skips exactly those quoted lines in this file and in the review files and scans every other line.

`python3 -E -s -B tests/harness/pc_baseline.py row7-review --folder FOLDER` builds the side-by-side table of the row 7
attempts of a dated folder from the filed candidate files and stop files only, never a run root. It has one section per
attempt in attempt order (the bare folder is attempt 1); a stopped or skipped attempt is kept with its reason, an attempt
with no printed checkpoint says so, and an attempt with zero entries has a section and no table body. A candidate file
that is absent or damaged is listed as such. The table is staged, sanitized, gated and added exactly like the files of
`close`, as `row7-review.md` or the first free `row7-review-part-N.md`, so an earlier file is never touched. A folder with
no row 7 attempt, and the two frozen folders, are refused with exit 2. Each row 7 README points to `row7-review.md` at
the top of the dated folder.

### Comparing a rerun with the committed row

`python3 -E -s -B tests/harness/pc_compare.py --old tests/evidence/publication-2026-10-20 --new tests/evidence/<the new folder>`
lines the new row 1 folder up against the committed one. `--row ID` names another row folder; the default is row 1.
Both values name a folder that holds the row folder, and neither may be a symlink.

It prints facts under neutral headings and decides nothing. For the one row folder in each tree it lists: the
files and folders present on one side only, in both directions; the row README headings that differ; the helper
calls (the total, the count per verb and the exit codes) from the wrapper log; the tool calls per tool name from
the full traces, with the header count and the two flag counts, a trace that exists on one side only being
reported on that side; and the byte measurements, read from the old and the new shape of the measurement file,
with every total or section above its cap named (a size equal to the cap is within it, one byte more is above).
Under the heading `listed, not judged` it lists the snapshot digests that differ and the paths on one side
only (a leading helper-state or ledgers folder is read as `ckpt`), the allowlist rule difference with both
counts, the digest lines, the Claude Code version and the usage file. Content digests that differ are expected
and are only listed. The committed token `<repo>/<run>` and the newer token `<run>` are read as equal before any
count that depends on text. A file that is missing or cannot be parsed is reported as such for that side and the
run goes on.

It opens everything for reading only and writes nothing but its report. To show that, it prints a digest of each
whole tree before the comparison and again after it, and says for each side whether the two are equal. The digest
covers names, bytes, empty folders and symlink targets; file modes and timestamps are not part of it. It exits 0
whenever both trees were readable, whatever they differ in, and 2 when a folder is missing, is a file or a
symlink, lacks the row folder, or the command line is wrong; its error text is fixed and never repeats a path. It
never says that a row is accepted or rejected: that is the reviewer's decision.

## Replacement tokens

Evidence that becomes public is sanitized with these tokens, always lower case in angle brackets:
`<home>`, `<user>`, `<host>`, `<tmp>`, `<repo>` for the machine's own values; `<run>`, `<helper>`,
`<auto-memory-root>` and `<scratch>` for paths a caller maps (`<scratch>` is the runs folder and the folders
above it); `<redacted>` for entries from a local deny file.

## Platforms

Only macOS is verified, with the system Python 3.9 interpreter and the bash 3.2 that ships as the
system bash. Linux and other bash versions are written for but unverified: the forbidden-construct
scan applies everywhere, and the self-test records the bash version it ran under, but a different
bash proves the syntax travels, not the 3.2 floor. Windows is not covered.

## Layout

Every file in this folder, once. `data/` is the only subfolder and holds non-code data.

- `.gitignore` - keeps bytecode and `__pycache__` out of history
- `README.md` - this guide
- `selftest` - the one command to run first; bash 3.2 shim that scrubs claude from PATH and runs the suite
- `checkpoint-wrapper` - logs every stub call, refuses driver-only verbs, injects conflicts
- `git-wrapper` - the row 11 git wrapper: delegates every call to the real git, logs one line per call, injects one concurrent change on the n-th exact status call
- `checkpoint_stub.py` - the single-file STUB-BACKED checkpoint helper
- `pc_allowlist.py` - bounded model of Bash permission-rule matching
- `pc_baseline.py` - closing a dated folder: README, digest table and usage table as part files; report, check-words and the row 7 review table
- `pc_checks.py` - the mechanical checks: write boundary, git read-only, helper-call counts, ledger digests, session facts
- `pc_compare.py` - the read-only comparer: file sets, headings, call counts, bytes against the cap, tree digests before and after
- `pc_evidence.py` - filing a finished run: staging, provenance and usage files, traces, the reviewer checklist, SKIPPED and STOPPED labels
- `pc_exitcodes.py` - the named exit codes
- `pc_flags.py` - the pinned `claude -p` contract: flag table, argv builder, environment scrub, version gate
- `pc_leakgate.py` - fail-closed leak gate for evidence about to become public
- `pc_manifest.py` - byte-walk tree manifests and JSON-lines writers
- `pc_matrix.py` - the matrix driver: list, plan and run rows; dry run starts nothing
- `pc_measure.py` - heading-inclusive UTF-8 byte measurer
- `pc_mine.py` - miner for the committed wrapper call logs
- `pc_preflight.py` - zero-token check that claude is present, in the tested set and logged in
- `pc_promote.py` - gate-first, exclusive-creation copy of a stage into the evidence folder
- `pc_rows.py` - the row and layout registry: ids in acceptance order, stages, caps, records
- `pc_row1.py` - row 1 and the engine every row runs through: the seed, the snapshots, the stage chain (resume line or printed checkpoint), the probe call and the init and instruction-audit assertions
- `pc_rowhooks.py` - the between-stage hooks and their finalizers, the live chmod probe, the boundary plan of a row and the mode-only `perms.txt`
- `pc_rowseeds.py` - the seeds of registered rows: the parameterised helper-backed seed, the row 1 and row 4a setups, the plain-row seed and the row 5a to 7 setups, the git shapes and the row 8a to 10 setups
- `pc_review.py` - the Do-not-redo review: the entries of a printed checkpoint, the mechanical candidates for each, the row 7 facts, the candidate file and the side-by-side review table; the row 10 status-form counts and the join of git wrapper log lines to tool_use ids
- `pc_runroot.py` - exclusive run-root allocation and exclusive file creation
- `pc_spend.py` - the matrix spend ledger: file-locked reservation, retry authorization, per-call delta cost
- `pc_sanitize.py` - runtime-built deny-list sanitizer
- `pc_seeds.py` - run-time assembly of leak-shaped test strings (test support)
- `pc_spike.py` - the spike driver: harness home, runs root, spend guard, S1 assertions, S2 probe
- `pc_hooklog.py` - the hook logger for the spikes
- `pc_stream.py` - strict stream-json parser and structured denial detection
- `pc_testutil.py` - fake and tripwire claude, shared-directory layout, minimal environments (test support)
- `replay-cases.json` - the mined helper calls the replay suite runs against the stub
- `test_allowlist.py` - tests for the allowlist model
- `test_baseline.py` - tests for stopped rows, promote_into and the top-level files of a dated folder
- `test_bash_shims.py` - bash 3.2 lint of the shims and a run under the system bash
- `test_boundaries.py` - tests for the recorded boundary list, its legacy fallback, the guard chain and the hook safety checks
- `test_branch_table.py` - tests for the branch table
- `test_checks.py` - tests for the mechanical checks, with seeded failing runs and a clean control
- `test_compare.py` - tests for the comparer: the tracer against the committed row, the read-only proofs, digests, exits and vocabulary
- `test_driver_matrix.py` - tests for the campaign driver: labels, attempts, the date override, the multi-row loop, the exit code and the invocation budget
- `test_evidence.py` - tests for filing: the deny entries, the file set, provenance, usage, vocabulary, the checklist, SKIPPED, refile and a race
- `test_exitcode_agreement.py` - exit literals outside `pc_exitcodes.py` agree with its constants
- `test_flags.py` - tests for the pinned contract
- `test_frozen_reference.py` - the frozen reference is what the evidence ran on
- `test_frozen_tree.py` - SKILL.md size cap and pinned digests of the skill, references, fixtures and committed evidence
- `test_imports.py` - standard library only, 3.9 syntax, no shadowing, naming rule
- `test_leakgate.py` - tests for the leak gate
- `test_manifest.py` - tests for the manifest writers
- `test_matrix_cli.py` - tests for the driver's list, selection and dry run
- `test_matrix_preflight.py` - tests for the driver's gate, the three states, --claude and the budget
- `test_measure.py` - tests for the byte measurer
- `test_mine.py` - tests for the call-log miner
- `test_preflight.py` - tests for the exit-code table and the preflight
- `test_promote.py` - tests for promote
- `test_readme.py` - keeps this guide equal to the code
- `test_row1_assertions.py` - tests for the init manifest and instruction-audit assertions of a row run
- `test_row1_seed.py` - tests for the row 1 seed, the snapshots and the first stage
- `test_row_generic.py` - tests for a row run from its registry entry: row 4a, the seed byte-tie, per-row filing and the row 1 parity
- `test_rows_plain.py` - tests for the plain rows 5a and 5b: the seed byte-tie, the 35-rule allowlist, the memory settings and assertion and a scripted chain of each
- `test_row7.py` - tests for row 7: the live chmod probe and the SKIPPED label, the 555 restriction and its restore, the printed-checkpoint chain and its fence scanner, including the committed replies
- `test_rows_git.py` - tests for the git-shaped rows 8a, 8b, 8c, 9 and 10: the git shape seeds and their byte-tie, the no-git and worktree git states, the main-checkout exclusion, the row 10 hostile tree and status form, the static allowlist scan and a scripted chain of each
- `test_git_wrapper.py` - tests for the row 11 git wrapper (transparency, exact argument lists, ordinal and race, no-op session, safety) and for row 11 on the scripted claude
- `test_review.py` - tests for the Do-not-redo review: the entry parser, the token and candidate rules, the row 7 facts, the candidate file, the review table, hostile text and the caps
- `test_runroot.py` - tests for run roots
- `test_sanitize.py` - tests for the sanitizer
- `test_selftest_shim.py` - tests for the `selftest` shim with a tripwire claude
- `test_spend.py` - tests for the spend ledger, the retry authorization and the delta cost
- `test_spike.py` - tests for the spike driver and hook logger
- `test_spike_fixture.py` - zero-token checks of the committed spike captures
- `test_stages.py` - tests for the three-stage chain, the resume line, cost, stop rules and the pre-spend order
- `test_stream.py` - tests for the stream parser
- `test_stub_cli.py` - command-line tests for the stub
- `test_stub_concurrency.py` - races, a contended lock and the timeout switch
- `test_stub_replay.py` - zero-token replay of every mined helper call
- `test_wrapper_conflict.py` - tests for the wrapper and its conflict injection
- `data/branch-table.md` - the stub's branch table
- `data/spike-findings.md` - the spike findings, with the Total spend line
- `data/s1-init-manifest.json` - the init facts frozen from spike S1
- `data/s2-stream.jsonl` - the sanitized real stream from spike S2
- `data/s2b-stream.jsonl` - the sanitized resume stream from spike S2
- `data/s2-probe-labels.json` - the policy-probe labels for spike S2
- `data/row1-s1-prompt.md` - the row 1 work-turn prompt, with a ledger placeholder
- `data/row1-plan.md` - the row 1 plan text, whose digest equals the committed setup digest
- `data/plain-plan.md` - the plan text of every plain row, whose digest equals the committed setup digest of rows 5a and 5b
- `data/plain-s1-prompt.md` - the plain work-turn prompt: the row 1 prompt with the ledger clause replaced

## Limits

- The stub is not the real helper. Whatever is UNCONFIRMED in the branch table stays UNCONFIRMED
  until a real helper run shows it.
- Everything about `claude -p` depends on the Claude Code version. The exact-match version gate
  holds the set of versions the harness has actually run against; any other version is reported,
  not trusted.
- A green self-test says the harness machinery works. It says nothing about the skill.
- Rerunning the spikes on a new Claude Code build needs fresh output names and a fresh harness home,
  because the committed outputs and the lifetime attempt limits of the spike ledger stay in the way.
- Later phases extend this guide with the run matrix, its order and its measured cost.
