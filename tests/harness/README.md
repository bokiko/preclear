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

## What it does not prove

- Nothing about how the skill behaves. The suite never starts a model.
- No verdicts. The harness prints facts, and a reviewer decides what they mean.
- Nothing about a real checkpoint helper. See The stub.

## Requirements

- Claude Code (needed for real runs; the self-test does not use it).
- git.
- Python 3.9 or newer, standard library only.
- bash for the two entry shims (`selftest` and `checkpoint-wrapper`).
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
- Only row 1 is implemented in this phase. The other rows and the three layouts are listed and
  refused with exit 2, and so is any id that is not an exact, whole match of a listed one (a
  prefix, another case, an empty value). The refusal text is fixed and never repeats the value.

## Replacement tokens

Evidence that becomes public is sanitized with these tokens, always lower case in angle brackets:
`<home>`, `<user>`, `<host>`, `<tmp>`, `<repo>` for the machine's own values; `<run>`, `<helper>` and
`<auto-memory-root>` for paths a caller maps; `<redacted>` for entries from a local deny file.

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
- `checkpoint_stub.py` - the single-file STUB-BACKED checkpoint helper
- `pc_allowlist.py` - bounded model of Bash permission-rule matching
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
- `pc_runroot.py` - exclusive run-root allocation and exclusive file creation
- `pc_sanitize.py` - runtime-built deny-list sanitizer
- `pc_seeds.py` - run-time assembly of leak-shaped test strings (test support)
- `pc_spike.py` - the spike driver: harness home, runs root, spend guard, S1 assertions, S2 probe
- `pc_hooklog.py` - the hook logger for the spikes
- `pc_stream.py` - strict stream-json parser and structured denial detection
- `pc_testutil.py` - fake and tripwire claude, shared-directory layout, minimal environments (test support)
- `replay-cases.json` - the mined helper calls the replay suite runs against the stub
- `test_allowlist.py` - tests for the allowlist model
- `test_bash_shims.py` - bash 3.2 lint of the shims and a run under the system bash
- `test_branch_table.py` - tests for the branch table
- `test_exitcode_agreement.py` - exit literals outside `pc_exitcodes.py` agree with its constants
- `test_flags.py` - tests for the pinned contract
- `test_frozen_reference.py` - the frozen reference is what the evidence ran on
- `test_imports.py` - standard library only, 3.9 syntax, no shadowing, naming rule
- `test_leakgate.py` - tests for the leak gate
- `test_manifest.py` - tests for the manifest writers
- `test_matrix_cli.py` - tests for the driver's list, selection and dry run
- `test_measure.py` - tests for the byte measurer
- `test_mine.py` - tests for the call-log miner
- `test_preflight.py` - tests for the exit-code table and the preflight
- `test_promote.py` - tests for promote
- `test_readme.py` - keeps this guide equal to the code
- `test_runroot.py` - tests for run roots
- `test_sanitize.py` - tests for the sanitizer
- `test_selftest_shim.py` - tests for the `selftest` shim with a tripwire claude
- `test_spike.py` - tests for the spike driver and hook logger
- `test_spike_fixture.py` - zero-token checks of the committed spike captures
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

## Limits

- The stub is not the real helper. Whatever is UNCONFIRMED in the branch table stays UNCONFIRMED
  until a real helper run shows it.
- Everything about `claude -p` depends on the Claude Code version. The exact-match version gate
  holds the set of versions the harness has actually run against; any other version is reported,
  not trusted.
- A green self-test says the harness machinery works. It says nothing about the skill.
- Later phases extend this guide with the run matrix, its order and its measured cost.
