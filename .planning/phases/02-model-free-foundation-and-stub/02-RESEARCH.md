# Phase 2: Model-Free Foundation and Stub - Research

**Researched:** 2026-10-25
**Domain:** Zero-token Python 3.9 test harness primitives, a test-only stub of the `checkpoint-v1` helper, and two paid spikes that pin the `claude -p` contract
**Confidence:** MEDIUM-HIGH. HIGH for the Claude Code flag contract, the stub contract mined from committed evidence, and the Python techniques (all run this session on Python 3.9.6). MEDIUM for the spike predictions (isolation, instruction audit, stream shape), which the spikes themselves must confirm.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Spike run policy (discussed with bokiko)
- **D-01:** The machine that runs S1 and S2 is logged in by **subscription** (claude.ai login),
  not an API key. S1 must therefore probe whether a scratch `CLAUDE_CONFIG_DIR` keeps the
  subscription credentials before strict isolation is promised.
- **D-02:** The matrix claims **strict isolation**: a harness-owned `CLAUDE_CONFIG_DIR` outside
  the repo and outside the user's home config, plus `--setting-sources project,local`.
  User-level instructions, memory and skills must be provably absent (the `init` event's
  skill and instruction lists are the assertion). — **Reversibility:** costly — the isolation
  level is part of the baseline every Phase 3 and Phase 4 evidence folder is labelled with;
  changing it later means a new baseline and new evidence folders.
- **D-03:** If S1 shows a scratch `CLAUDE_CONFIG_DIR` loses the login, the fallback is **one
  manual login into the harness-owned config dir** (bokiko runs `claude login` once with
  `CLAUDE_CONFIG_DIR` pointed at a persistent directory outside the repo). The step is
  documented for strangers in the run guide. The harness never falls back silently to
  standard isolation, and never writes, copies or reads credential files itself.
- **D-04:** Token budget for both spikes together is **at most 5 USD**, enforced per call with
  `--max-budget-usd` and a small `--max-turns`. S1 and S2 each get one retry inside that cap.
  The spike findings record the measured spend.
- **D-05:** The spikes pin **`claude-sonnet-5-5`** as the full model id. The stream-json shape
  does not depend on the model, so the S2 fixture is representative. Phase 3 picks the matrix
  baseline model separately; the spike findings note that dependency and record `init.model`.

### Stub gaps (Claude's call, confirmed by bokiko as "you decide")
- **D-06:** Where `references/checkpoint-v1.md` and the committed logs are silent, the stub
  takes the most literal reading of the document, and the branch table marks the behaviour
  **UNCONFIRMED** against the real build. Behaviours that no committed run exercised
  (`handoff`, `note`, exit 5, exit 6) are implemented as the document describes and listed
  as UNCONFIRMED, as STUB-05 requires.
- **D-07:** Section hashes are 64-character lowercase SHA-256 hex over the section body bytes
  as the committed `sha.txt` snapshots show; if the exact input bytes cannot be derived from
  the committed snapshots, the replay suite proves whichever reading reproduces them and the
  branch table records the derivation.
- **D-08:** Exits 5 and 6 get **labelled stub-internal switches** (environment variables with a
  `CKPT_STUB_` prefix, named in `tests/harness/README.md`), the only stub-internal test modes
  STUB-04 allows. Conflict injection (exit 3) and call logging live in the wrapper outside the
  stub, never inside it (roadmap decision, STUB-04).
- **D-09:** The stub refuses to run without `CKPT_HOME` (distinct non-zero exit), keeps all state
  under it, writes atomically via `os.replace`, holds an `fcntl.flock` lock, and brands every
  output line that a model could read with a stub marker (STUB-02, STUB-05).

### Self-test UX (Claude's call)
- **D-10:** One bash 3.2 entry shim `tests/harness/selftest` that `exec`s
  `python3 -m unittest discover` over `tests/harness/`; the shim is the first thing the README
  tells a stranger to run. Plain `python3 -m unittest discover -s tests/harness` works too.
- **D-11:** **Python floor is 3.9**, standard library only (HARN-14). No `tomllib`, so the
  harness never parses TOML; the leak-gate rules live in Python (see D-14).
- **D-12:** `tests/harness/` is a flat directory of modules plus `test_*.py` files, no package
  install step, no `setup.py`, no `pyproject.toml`.
- **D-13:** The self-test suite exits 0 with zero model calls while `claude` is absent from
  `PATH`; each test that would touch the model is a preflight-path test that asserts the
  distinct SKIP / FAIL / BLOCKED exit codes instead (EVID-07, success criterion 1).

### Sanitizer and leak gate (Claude's call)
- **D-14:** The leak gate is a Python stdlib regex scanner with its own rule list in
  `tests/harness/`. It is independent of gitleaks at run time, and one self-test cross-checks
  that every identifier rule in `.gitleaks.toml` (home paths, hostnames, private IPs, emails,
  session ids where applicable) has a counterpart in the Python list, so the two cannot drift
  silently.
- **D-15:** Replacement tokens are angle-bracket placeholders: `<HOME>`, `<USER>`, `<HOST>`,
  `<TMP>`, `<REPO>`, matching the shape of the committed sanitized evidence. The deny-list is
  built at run time from the live machine (raw, realpath, dash-slug and URL-encoded home forms,
  user, hostname, temp roots) and, when present, from the local file
  `.git/info/preclear-deny.txt`, whose contents are never printed or committed (EVID-02).
- **D-16:** `promote` refuses to copy anything into `tests/evidence/` on any scan failure or
  scanner error (fail closed), prints counts only, never matched values (EVID-03).

### Claude's Discretion
- Internal module boundaries inside `tests/harness/`, test naming, fixture file layout for the
  replay suite, and the exact exit codes for the version gate and the stub's missing-`CKPT_HOME`
  refusal (distinct from 0 to 6 and documented in the branch table).
- The order of the two spikes and whether S2 captures its fixture in the same call as the
  policy probe, within D-04's budget.

### Deferred Ideas (OUT OF SCOPE)
- Windows-style and `/root/` home-path coverage in the gitleaks home-path rule (Phase 1 review
  CR-03 leftover) — fold into the Python rule list in this phase only if cheap; the gitleaks
  rule itself is a Phase 4 hygiene item.
- A matrix-wide `--dry-run` cost estimate (counts sessions, spends nothing) — belongs to the
  Phase 3 runner.
- Per-row structural comparison against committed evidence — Phase 4 (research P2).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HARN-03 | Run roots created exclusively, never overwritten or deleted | `os.mkdir` without `exist_ok` raises on collision, also over a dangling symlink (verified, Code Examples 1). Static scan forbids delete calls in harness modules. |
| HARN-04 | Every `claude -p` call pins its behaviour; version gate refuses untested versions | Flag table with source and minimum version per flag (Claude Code Headless Contract). Gate is an exact-match set of tested versions plus a distinct exit code. |
| HARN-06 | Allowlist self-test; any unexpected `permission_denied` or `permission_denials` fails a row; no substring detection | Documented Bash rule semantics, a labelled corpus of 336 real commands, and the finding that `permission_denials` is authoritative while the event is best-effort. |
| HARN-08 | Filename-safe snapshots and manifests | In-process `os.walk` on bytes, byte-sorted, escaped text form plus lossless JSON-lines form. APFS rejects non-UTF-8 names (verified), so that case needs a skip or a synthetic unit test. |
| HARN-14 | No install beyond Claude Code, git, Python 3; bash 3.2 shims | stdlib-only import classifier that works on 3.9 (verified), forbidden-bash-feature list, shim prototype run under bash 3.2.57. |
| STUB-01 | Single-file stub implements `checkpoint-v1` | Mined contract: argv shapes, output shapes, hash derivation, ledger and binding file formats. |
| STUB-02 | Refuses to run without `CKPT_HOME`, all state under it | Recommended state layout and exit code 64. |
| STUB-03 | Replay conformance from committed logs | Exact inventory: 5 non-empty logs, 15 calls, 4 empty logs, and which outputs are reproducible byte for byte. |
| STUB-04 | Conflict injection and logging outside the stub | Wrapper design taken from the committed `wrapper-checkpoint.sh`. |
| STUB-05 | Branch table, UNCONFIRMED marks, stub branding | Draft branch table with evidence status per row. The UNCONFIRMED list is longer than the four items in the requirement. |
| STUB-06 | `bind`, `create`, `init` never model-facing | Per-verb allow rules only, never a bare wrapper rule; the allowlist matcher model asserts it. |
| STUB-07 | `references/checkpoint-v1.md` unchanged | Current file digest equals the adapter digest in the committed row 5 to 12 evidence. |
| EVID-01 | Measurer: bytes on originals, heading-inclusive, actual/cap | Caps and splitting rule verified in SKILL.md and the prior measurer. Binary read avoids newline translation. |
| EVID-02 | Runtime-built deny-list sanitizer | Home, slug, URL-encoded, temp and host forms, with ordering and length-floor rules. |
| EVID-03 | Fail-closed leak gate and `promote` | Six gitleaks rules compile in Python 3.9 `re`; parity test design; counts-only output precedent. |
| EVID-07 | Zero-token self-test suite is the first thing a stranger runs | Shim prototype with PATH scrubbing and a tripwire `claude`; discovery works on a flat directory. |
</phase_requirements>

## Summary

Phase 2 is mostly deterministic Python plumbing, and the evidence needed to build it is already committed. The one piece with real unknowns is the pair of paid spikes. Research resolved most of what they were meant to learn, so the plans can treat S1 and S2 as confirmation runs with pre-written assertions instead of open exploration.

Five findings change the plan. First, the committed section hashes can be derived: a section hash is the SHA-256 of the section body as UTF-8 text with trailing newlines removed, no heading, no `section-hash:` line. This reproduced eight section hashes from two evidence folders. The `sha.txt` snapshot files are a different thing (a whole-file digest list) and cannot serve as the derivation source. Second, a scratch `CLAUDE_CONFIG_DIR` loses the subscription login on macOS. The official docs say the Keychain entry is keyed to the directory, and a zero-token probe on this machine (Claude Code 2.1.310) reported `loggedIn: false` for a fresh directory. So the D-03 one-time login fallback will be needed, and S1 only has to confirm that the login persists and the isolation assertions hold. Third, the `system/init` event has no list of loaded instruction files, so D-02's parenthetical assumption is wrong. The documented `InstructionsLoaded` hook reports each instruction file with a `memory_type` of User, Project, Local or Managed, and can be turned into a machine-checkable audit. Fourth, only the `publication-2026-10-20` folder holds `wrapper-calls.log` files. The bound-ledger paths named in CONTEXT have none. Fifth, `permission_denied` events are documented as best-effort, so `result.permission_denials` is the authoritative denial record and the parser must use both.

Two locked decisions collide with fidelity and need a recorded resolution. D-09 says to brand every output line a model could read, but `references/checkpoint-v1.md` tells the adapter to parse line 1 of `status` and the exact string `ledger lint OK`. D-15 names uppercase tokens such as `<HOME>`, while the committed evidence uses lowercase `<home>`. Both are in Open Questions with a recommended reading that honours the lock as far as possible.

**Primary recommendation:** Build everything as flat, `pc_`-prefixed, stdlib-only Python 3.9 modules behind one bash 3.2 shim. Derive the stub's section hash, status, show, validate, update and conflict formats from the mined evidence below, and mark everything else UNCONFIRMED. Treat S1 and S2 as one or two cheap capture runs (a few cents each at published Sonnet 5.5 prices) whose assertions are written first.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run-root allocation, snapshots, measurer, sanitizer, leak gate, promote | Harness library (Python, host) | none | Pure functions over files; no model involvement. Must run with `claude` absent. |
| Conflict injection and call logging | Model-facing wrapper (bash) | Stub (never) | STUB-04: the wrapper is the executable named in the fixture configuration; the stub carries no injection or logging. |
| `checkpoint-v1` behaviour (hashes, ledger, bindings, exit codes) | Stub helper (Python, single file) | none | One file means one path to allowlist and one digest to record. |
| Bash permission rule semantics | Claude Code process (ground truth) | Harness matcher model (regression guard) | The real policy lives in the binary. The Python model only guards against allowlist regressions between spikes. |
| Denial detection | Harness stream parser | none | Structured events and the result record only; never reply text. |
| Isolation (config dir, setting sources, MCP, instruction audit) | Claude Code process flags and env | Harness init-manifest assertions | The harness sets flags; the binary enforces; the stream proves. |
| Credentials | Claude Code and the OS keychain | none | The harness never reads, copies or writes them (D-03). |
| Evidence staging and promotion | Harness library | Phase 1 git hooks (second net) | Gate first, copy second, hooks last. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3 standard library | 3.9 floor; macOS Command Line Tools ships 3.9.6 [VERIFIED: `python3 --version` on the system interpreter this session] | Every harness module and the stub | HARN-14 and D-11. The PATH interpreter on the author's machine is 3.14.7, so green there does not prove the 3.9 floor. |
| `unittest` | stdlib | Self-test suite | Zero installs; `discover` works on a flat directory (verified). |
| bash 3.2 | macOS `/bin/bash` 3.2.57 [VERIFIED: `bash --version`] | Entry shims and the model-facing wrapper only | Matches the committed wrapper style. |
| Claude Code CLI | 2.1.310 installed here [VERIFIED: `claude --version`]; evidence ran on 2.1.304 [VERIFIED: `claude-version.txt` reads `2.1.304 (Claude Code)`] | System under test | See flag table. |
| git | 2.50.1 here [VERIFIED: `git --version`] | Fixture creation, read-only `status` in snapshots | Already a project dependency. |

### Supporting (all stdlib modules the plans will use)
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `os`, `os.path` | `mkdir`, `open` with `O_CREAT|O_EXCL`, `replace`, `walk` on bytes, `fsencode` | Run roots, snapshots, atomic ledger writes |
| `fcntl` | `flock` | Stub lock on a dedicated lock file |
| `hashlib` | SHA-256 | Section hashes, file fingerprints, `sha.txt` |
| `tempfile` | `mkstemp` in the target directory | Atomic writes |
| `json` | Stream parsing, JSON-lines manifests, binding files | Everywhere; no jq |
| `re` | Leak rules, section splitting | Measurer, sanitizer, gate |
| `shlex` | Parse `%q`-quoted argv in `wrapper-calls.log` | Replay miner (verified on all 15 calls) |
| `urllib.parse` | URL-encoded home forms | Sanitizer deny-list |
| `subprocess` | Run stub, wrapper, `git`, `claude --version`, `claude auth status` | Argv lists only, never `shell=True` |
| `importlib.util`, `sysconfig`, `sys` | Stdlib import classifier | HARN-14 scan |
| `ast` | Parse harness sources for imports and delete calls | Static scans |
| `uuid` | `uuid4()` session ids | Spike and wrapper setup |
| `argparse` | Stub CLI | Exit 2 on usage already matches the contract |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `unittest` | pytest, bats-core | Installs; breaks the stranger path. |
| Hand-written minimal reader for `.gitleaks.toml` ids and regexes | `tomllib` | 3.11+ only; D-11 forbids it. A 15-line reader was tested against the live file this session. |
| Stdlib import classifier by `find_spec` origin | `sys.stdlib_module_names` | The latter is 3.10+ only (absent on 3.9.6, verified). |

**Installation:** none. `python3 --version` must report 3.9 or newer.

**Version verification:** no external packages are recommended. Python 3.9.6, bash 3.2.57, git 2.50.1 and Claude Code 2.1.310 were read from the machine this session.

## Package Legitimacy Audit

No external packages are installed in this phase (standard library only). Nothing to check with the legitimacy seam.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| none | none | none | none | none | none | Not applicable |

**Packages removed due to SLOP verdict:** none
**Packages flagged SUS:** none

## Claude Code Headless Contract

Sources are the official pages fetched this session (listed under Sources). Minimum versions are from those pages. The local build is 2.1.310.

### Flag table the plans should commit (recommended pins)

| Flag or env | Pinned value | Status | Why and source |
|-------------|--------------|--------|----------------|
| prompt | stdin (`input=` in `subprocess.run`) | Pin | Prior harness piped the prompt. `--allowedTools` is variadic in `claude --help` (`<tools...>`), so a positional prompt after it may be consumed as a tool name [ASSUMED: commander.js variadic semantics]. The docs example puts the prompt first. |
| `-p` | always | Pin | `claude -p` exits 0 on success; in-run failures such as missing auth print as the result on stdout [CITED: code.claude.com/docs/en/headless]. Judge success from the `result` event. |
| `--output-format stream-json --verbose` | both | Pin | The headless page's streaming example pairs them. That `--verbose` is mandatory with `-p` stream-json comes from the prior live probe [CITED: .planning/research/STACK.md]; S2 re-confirms. |
| `--setting-sources project,local` | exact | Pin | Accepts `user`, `project`, `local` [CITED: cli-reference]. Leaving out `user` also stops claude.ai skill sync [CITED: code.claude.com/docs/en/skills]. |
| `--settings <abs file>` | regular file, at most 2 MiB | Pin | Overrides same keys in settings files for the session [CITED: cli-reference]. |
| `--session-id <uuid4>` and `--resume <uuid>` | per stage | Pin | Must be a valid UUID [CITED: cli-reference]. `CLAUDE_CODE_SESSION_ID` is set in Bash tool subprocesses [CITED: code.claude.com/docs/en/env-vars]. |
| `--permission-mode default` | exact | Pin, assert `init.permissionMode == "default"` | `claude --help` lists `manual` in its place and both work [CITED: cli-reference, v2.1.200+]. The SDK type has `default`, not `manual` [CITED: agent-sdk/typescript]. S2 records the literal init string. |
| `--allowedTools "<one comma-joined string>"` | one argument | Pin | Trailing ` *` and `:*` are equivalent prefix wildcards [CITED: code.claude.com/docs/en/permissions]. Naming `Glob` or `Grep` restores both tools, which are absent by default on macOS [CITED: tools-reference]. |
| `--model claude-sonnet-5-5` | exact | Pin (D-05) | API ID confirmed [CITED: platform.claude.com models overview]. Needs Claude Code 2.1.284 or newer [CITED: model-config]. Aliases move. |
| `--max-turns N` | small, per call | Pin | Print mode only; exits with an error at the limit [CITED: cli-reference]. Result subtype `error_max_turns` [CITED: agent-sdk/typescript]. |
| `--max-budget-usd X` | per call | Pin | Client-side estimate; spend can pass the cap; cap enforcement needs 2.1.217 or newer [CITED: cli-reference]. |
| `--strict-mcp-config` with no `--mcp-config` | add | Recommended addition | Only servers from `--mcp-config` are used [CITED: cli-reference]. That this yields zero servers when none are passed is [ASSUMED]; S2 asserts `init.mcp_servers == []`. |
| `--effort high` | add | Recommended addition, discretion | Sonnet 5.5 default effort is `high` [CITED: models overview], so pinning changes nothing today and blocks drift. Record `init.effort` (optional field). Prior evidence did not record effort. |
| `DISABLE_AUTOUPDATER=1` | env | Pin | [CITED: env-vars]. `claude update` still works manually. |
| `CLAUDE_CONFIG_DIR=<harness-owned dir>` | env | Pin for strict isolation (D-02) | Credentials, settings, history and plugins all live under it [CITED: env-vars, authentication]. |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` | env | Recommended addition | Strips credential-shaped variables from Bash tool subprocesses, and removes `CLAUDE_CONFIG_DIR` there [CITED: env-vars]. Protects the trace if an allowlist permits `env`. |
| `CKPT_HOME=<run-owned dir>` | env | Pin | Prior harness exported it and the model's Bash inherited it [VERIFIED: the local prior driver script exports it before `claude -p`]. |

### Considered and not pinned
`--bare`, `--safe-mode`, `--restricted`, `--dangerously-skip-permissions`, `--permission-mode auto|dontAsk|acceptEdits`, `--include-partial-messages`, `--no-session-persistence` on real rows, `--fallback-model`, `--tools`, `--add-dir`, `--system-prompt*`, `--exclude-dynamic-system-prompt-sections`, `--input-format`. `--permission-prompts none` stays off: in a `-p` run with no host, prompts are denied either way and the flag only adds a "do not retry" message to the model [CITED: headless], which would change behaviour against the 2.1.304 evidence. Record `init.tools` instead of passing `--tools`.

### Minimum versions that bound the version gate floor
| Capability | Minimum | Source |
|------------|---------|--------|
| `manual` alias for `default` | 2.1.200 | cli-reference |
| `--max-budget-usd` cap behaviours | 2.1.217 | cli-reference |
| `permission_denied` event in a `-p` run without a callback | 2.1.223 | agent-sdk/typescript |
| `--permission-prompts` | 2.1.259 | headless |
| Sonnet 5.5 | 2.1.284 | model-config |
| `-p` starts in Manual when nothing sets a mode | 2.1.302 | headless, permission-modes |

A floor of 2.1.302 satisfies all of these. The gate should be an exact-match set of versions the new harness has actually run S2 against, because HARN-04 says "untested". Seed it with the S2 version (2.1.310 today). List 2.1.304 as the committed-evidence baseline, not as harness-tested.

### Stream shape (documented fields)
- `system/init`: `session_id`, `claude_code_version`, `cwd`, `tools`, `mcp_servers[{name,status,source?}]`, `model`, `permissionMode`, `slash_commands`, `skills`, `plugins[{name,path}]`, `plugin_errors?`, `output_style`, `apiKeySource`, `agents?`, `effort?`, `capabilities?` [CITED: agent-sdk/typescript, `SDKSystemMessage`]. `memory_paths` is not in the documented type; it appeared only in live output earlier [CITED: STACK.md], so S2 must capture it.
- `apiKeySource` for a subscription login is `"none"`: the reported values are `ANTHROPIC_API_KEY`, `apiKeyHelper`, `/login managed key`, `none`, and `none` covers claude.ai login, bearer token and cloud provider [CITED: agent-sdk/typescript]. Subscription cannot be told from other non-key auth by this field alone.
- `system/permission_denied`: `tool_name`, `tool_use_id`, `decision_reason_type?`, `decision_reason?`, `message`. It skips denials decided on the PreToolUse hook path and is "best-effort", so the docs call `result.permission_denials` "the authoritative record" [CITED: agent-sdk/typescript].
- `result`: `subtype` (`success`, `error_max_turns`, `error_during_execution`, `error_max_budget_usd`, `error_max_structured_output_retries`), `is_error`, `num_turns`, `total_cost_usd`, `usage`, `modelUsage`, `permission_denials[{tool_name,tool_use_id,tool_input}]`, `terminal_reason?` [CITED: agent-sdk/typescript].
- A SIGTERM'd run exits 143 and records no result for the unfinished turn; SIGINT ends the turn cleanly [CITED: headless].

### Bash rule semantics (priority 2 answer)
- `Bash(ls *)` and `Bash(ls:*)` are equivalent; the space before a trailing `*` is part of the rule; a trailing ` *` also matches the bare command. The `:*` form is recognised only at the end of a pattern [CITED: permissions, Wildcard patterns].
- A rule without a wildcard is exact, so `Bash(pwd)` does not match `pwd -P` [CITED: permissions table row `Bash(npm run build)` does not match `npm run build --watch`].
- Compound commands split on `&&`, `||`, `;`, `|`, `|&`, `&` and newlines, and every part must match [CITED: permissions, Compound commands]. Only `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob` are stripped; `env` and path-qualified programs are not [CITED: permissions, Wrappers].
- A built-in read-only command set runs without a rule, but path scope still applies. The committed traces show `ls` and `wc` blocked outside the working directory even with `Bash(ls:*)` allowed [VERIFIED: full traces, messages such as "was blocked. For security, Claude Code may only list files in the allowed working directories"]. Allow rules do not widen file scope.
- The 2026-10-20 evidence used the `:*` form throughout (for example the row 10 rerun allowlist lists `Bash(git --no-optional-locks status:*)` and `Bash(pwd -P)`) [VERIFIED: `tests/evidence/publication-2026-10-20/row10-large-status-rerun/tools.txt`]. Every rule in it is still valid under the current docs. The earlier miss was structural: `Bash(git status:*)` cannot match `git --no-optional-locks status ...` because a global option sits between `git` and the subcommand.

## Spike Designs

### S1: isolation
Decided by research, to be confirmed:
1. **Zero tokens, already observed.** With `CLAUDE_CONFIG_DIR` pointing at a fresh directory and API-key variables unset, `claude auth status --json` on 2.1.310 printed `"loggedIn": false`, `"authMethod": "none"` and exited 1. The docs explain why: the credentials file or Keychain entry is keyed to the config directory [CITED: code.claude.com/docs/en/authentication, Credential management]. The command also showed `.claude.json` is created inside the config directory, and that transcripts live under `<config>/projects`.
2. **One-time login (D-03).** bokiko runs `CLAUDE_CONFIG_DIR=<persistent dir> claude auth login` (subcommand verified in `claude auth login --help`). The login stays in a Keychain entry keyed to that directory. Deleting the directory later leaves the entry, so the run guide must say so.
3. **Zero-token preflight.** `claude auth status --json` under the harness-owned directory gives a boolean before any spend. Read only `loggedIn`. A logged-in response probably carries identity fields, which must never be printed, logged or committed. Not-logged-in maps to BLOCKED with the one-time login instruction.
4. **One cheap model call** under the full pinned flag set with a trivial prompt, to assert the isolation manifest (below). Expected cost is cents.

**Instruction audit (fix for the D-02 premise).** `init` has `skills` and `slash_commands` but no instruction-file list. Use the documented `InstructionsLoaded` hook: it fires for every CLAUDE.md or rules file with `file_path` and `memory_type` of `User`, `Project`, `Local` or `Managed` [CITED: code.claude.com/docs/en/hooks]. Deliver a logger hook through `--settings` (command-line tier), and add `--include-hook-events` so `hook_response` events (fields `stdout`, `output`, `exit_code`) land in the stream [CITED: agent-sdk/typescript; flag present in local `claude --help`]. Whether an async `InstructionsLoaded` hook fires in a `-p` run and appears in the stream is [ASSUMED]; the logger can also append to a harness-owned file as a fallback. Assertions: no `User` entry outside the harness config directory, exactly the expected `Project` entries, and any `Managed` entry reported rather than hidden (admin policy still applies under strict isolation [CITED: cli-reference `--safe-mode` text]).

**Manifest assertions from `init`** (all recorded from the real capture, then frozen): `skills` equals the built-ins plus `preclear`, `plugins == []`, `mcp_servers == []`, `agents` equals the built-in baseline, `slash_commands` equals the baseline, `tools` includes `Glob` and `Grep` only because the allowlist names them, `permissionMode == "default"`, `model == "claude-sonnet-5-5"`, `apiKeySource` recorded.

### S2: stream shape and policy probe
Capture one real stream-json run and the policy probe in the same call (within the CONTEXT discretion). Prompt the model to run a numbered list of exact Bash commands one at a time without changing them:
- the wrapper `status` (expect allowed);
- the skill's status command `git --no-optional-locks status --porcelain=v1 --untracked-files=all --ignore-submodules=none` (allowed);
- `pwd -P` (allowed);
- a compound of two allowed commands (allowed);
- a compound with a part that has no rule, for example a trailing `echo "exit=$?"` (expect denial with the "contains multiple operations" message);
- the wrapper with the verb `bind` (expect denial, the live proof for STUB-06);
- a command containing a variable expansion (expect denial).

Record, for each: `tool_use`, `tool_result.is_error`, the matching `permission_denied` event if any, and the entry in `result.permission_denials`. This labelled capture becomes the ground truth the Python matcher model is tested against, and the committed parser fixture. Also capture `init.memory_paths`, the literal `permissionMode`, `apiKeySource`, and the hook events from S1's audit if combined.

**Budget.** D-04 allows 5 USD total with one retry each. Sonnet 5.5 is priced at 2 USD per million input tokens and 10 USD per million output tokens [CITED: platform.claude.com models overview]. A prior full `/preclear` row recorded 45 turns with 42,407 cache-creation, 1,126,739 cache-read and 21,787 output tokens [VERIFIED: `bound-ledger-2026-10-19-rerun/conflict/s2-preclear-conflict-trace.md`, line "Turns 45. Usage: input 546, cache creation 42407, cache read 1126739, output 21787."]. Priced at Sonnet 5.5 rates (cache reads at 5 percent of input per the overview; cache writes at 1.25 times input [ASSUMED]) that is roughly 0.4 to 0.5 USD for a whole row on a different model, so a spike call should land well under 1 USD. Suggested caps: `--max-budget-usd 1.00` and `--max-turns 12` per call, which keeps two spikes with two attempts each at or under 4 USD.

**Sanitizing the fixture.** Capture raw into a private staging directory, then commit only the sanitized copy. Run the Phase 1 scan on it before commit. If a default gitleaks rule fires on an opaque value such as a thinking `signature`, replace only that value with a same-length placeholder and say so in the findings.

## Stub Contract Mined From Committed Evidence

### Corrections to CONTEXT
- `wrapper-calls.log` exists only under `tests/evidence/publication-2026-10-20/`. `bound-ledger-2026-10-19/` and its rerun hold no such file; those runs called the real helper directly and their short traces list calls without output [VERIFIED: directory listings and `find` this session].
- Five logs are non-empty (15 calls in total); four are empty (rows 3a, its rerun, 4a, 4b): those four prove zero helper calls [VERIFIED: parsed this session].

### Replay inventory (argv shapes and decisive outputs)

| Case | Calls (argv verbs) | Exits | Decisive outputs live in |
|------|--------------------|-------|--------------------------|
| row1 | `status` | 0 | `row1-wrong-binding/status-before.txt` (bound to another task's ledger, three lines) |
| row2 | `status`, `show`, `validate --from F`, `update --section "Goal & current state" --expect-section H0 --from G`, `show`, `update ... --expect-section H1 ...` | 0, 0, 0, 3, 0, 3 | `row2-double-conflict/s2-preclear-full-trace.md`, both `.conflict-*` files, `wrapper-injection.log`, `snap-0-setup` ledger |
| row3b | `status`, `show`, `validate`, `show --section "Next action"` | 0, 0, 0, 0 | `row3b-denied-helper-write/` trace and `status-before.txt` |
| row3b rerun | `status`, `show`, `validate` | 0, 0, 0 | rerun trace |
| row3c | `status` (unbound) | 0 | `status-before.txt`: `session e7ac129d: unbound` |
| rows 3a, 3a rerun, 4a, 4b | none | n/a | assert zero calls |

Log lines are `<UTC second> CALL <argv>` and `<UTC second> EXIT <n>`, with the argv written by bash `printf %q`. `shlex.split` recovers it exactly [VERIFIED: parsed all 15 calls]. Exit codes seen in any helper call across all evidence are 0 and 3 only [VERIFIED: grep of every "Exit code" line; the other non-zero exits in traces are `git`].

### Section hash (D-07 answered)
The hash is SHA-256 of the section body as UTF-8 text, with trailing newlines removed, excluding the `## ` heading and the `section-hash:` line. Eight section hashes across two evidence folders were reproduced exactly, including multi-line bodies with non-ASCII characters:
- `903ea500e7ccf842c1312b6c2f964e3e98ff146456cecec717e9a0e122bf735f` is the hash of the body `None.`
- `ce26d74e1d4ccc3ec8ba4add6a30df523b974bf263b5d32b353d115e7744529e` is the hash of `Write the CSV exporter (plan step 2).`
- `2b0f84aac189b468066ae72aae01359d73b6c64b25e2de7f39406441014ce366` is the hash of `CSV first, JSON deferred: the downstream consumer only reads CSV.`
- `2caab006bb9d0bba2c4f412d9522c4181baf140aadef7e5a186025be7f06fb01` is the hash of `Plan: thoughts/plans/2026-10-15-widget-export.md. Branch main.`
- Four more matched in `bound-ledger-2026-10-19/main/show-after-s2.txt` (Decisions, Blockers, Evidence, Next action), including bodies of three to four lines.

[VERIFIED: computed with Python this session against the committed `show` output in `row2-double-conflict/s2-preclear-full-trace.md` and `bound-ledger-2026-10-19/main/show-after-s2.txt`.] Not provable from committed text: the Goal and Authorization sections, because their original bodies held a real run path that the sanitizer replaced with a token, so their recorded hashes cannot be recomputed. Whether leading or inner trailing whitespace is trimmed is also unobservable. The replay should assert the four path-free hashes exactly and, for path-bearing sections, only that the displayed hash equals `sha256(displayed body)`. Conflict files must carry the same hashes `show` displayed before and after.

`sha.txt` snapshot files are `<sha256>␣␣<relative path>` lines sorted by path bytes, hashing whole files; they are unrelated to section hashes. Example: `show`'s `file-fingerprint:` equals the ledger file's whole-file digest in the matching snapshot (`4f94eefee16d51c2cc909a518ed972ebe4d1b0c59cb7dafd677c661ca76fe53b`, present both in `snap-0-setup/sha.txt` and in the first `show` of the row 2 trace) [VERIFIED: both files read].

### Output and file formats seen
- `status` bound: three lines, `session <id8> → <ledger>`, `checkpoint updated <iso-ms>Z by <id8>`, `Next action: <text>`. Unbound: `session <id8>: unbound`, exit 0. [VERIFIED: status files in rows 1, 3b, 3c.]
- `show`: header lines `ledger: <path>`, `file-fingerprint: <sha256 of file>`, `checkpoint-updated: <iso-ms>Z by <id8>`, a blank line, then per section `## <name>`, `section-hash: <hash>`, body, blank line. `show --section S` prints the same header and one section. [VERIFIED: row 2 and row 3b full traces.]
- `validate` success: `valid checkpoint: <N> bytes, Authorization <M> chars` (three samples: 3449/452, 3987/529, 3456/485). The model's file measured 3446 bytes and the committed `auth.md` measures 453 characters including its trailing newline, so `M` excludes the trailing newline. `N` was 3 larger than the file. One hypothesis fits exactly: re-rendering the begin marker with a millisecond timestamp (+4) and no newline after the end marker (-1) [ASSUMED, arithmetic only]. Match `N` by pattern in the replay, not by value.
- `update` success stdout: `updated "<section>" in <ledger path>` [VERIFIED: `wrapper-injection.log`].
- `update` exit 3, message: `checkpoint: conflict: "Goal & current state" changed since your read. Nothing written. Details: <ledger>.conflict-2026-10-19T23-12-21.789Z-b9edab22.md` [VERIFIED: row 2 trace]. The conflict file name is `<ledger filename>.conflict-<date>T<hh>-<mm>-<ss>.<ms>Z-<caller id8>.md`, written beside the ledger. Content: `# Conflict on section "<name>"`, `ledger:`, `your base hash:`, `current hash:`, a blank line, `## Yours (not applied)`, body, `## Current (kept)`, body. One older conflict file also carries a `section-hash:` line under `Current (kept)`; the later ones do not [VERIFIED: both files read]. Which stream carries the message is unobservable (the trace merges them) [ASSUMED: stderr].
- `lint` success: `ledger lint OK` [VERIFIED: `lint-*` files].
- Ledger file: first line `# CONTINUITY` followed by an em dash and the task, then the block between `<!-- CHECKPOINT:BEGIN updated: <iso-ms>Z by: <id8> -->` and `<!-- CHECKPOINT:END -->` with six sections separated by one blank line, then a blank line and `## History`. File name `CONTINUITY_CLAUDE-<task>.md` [VERIFIED: row 2 ledger copies].
- `note` effect: appends under `## History` a heading `### <iso-ms>Z (<id8>)` and the note body [VERIFIED: `bound-ledger-2026-10-19-rerun/conflict/snap-2-after-preclear/ledger.md`]. Stdout and exit code of `note` are not in any committed output.
- Binding file `bindings/<session-uuid>.json` has keys `session_id`, `project`, `workstream`, `ledger`, `created`, `retired`, `predecessor` [VERIFIED: `bound-ledger-2026-10-19/main/snap-2-after-preclear/binding-b5f263b4.json`]. A `ledger-roots.json` registry exists beside the bindings [VERIFIED: names in `sha.txt`]; its content is not committed.
- The six section names, in order: `Goal & current state`, `Decisions (with reasons)`, `Blockers & open questions`, `Authorization boundaries`, `Evidence & key paths`, `Next action` [VERIFIED: `references/checkpoint-v1.md`, serialized block].

### Draft branch table (UNCONFIRMED marks beyond STUB-05's four)
| Branch | Exit | Evidence | Status |
|--------|------|----------|--------|
| `status` bound, unbound | 0 | rows 1, 3b, 3c | CONFIRMED |
| `status` `checkpoint: NONE`, `(carried from ...)` suffix | 0 | document only | UNCONFIRMED |
| `show`, `show --section` | 0 | rows 2, 3b | CONFIRMED |
| `validate` ok | 0 | three samples | CONFIRMED shape, byte count UNCONFIRMED |
| `validate` reject: six sections, 4,096 byte, 600 char limits | 2 or 4 | document only | UNCONFIRMED (code and text) |
| `update` ok | 0 | writer2 stdout | CONFIRMED |
| `update` conflict | 3 | row 2 | CONFIRMED |
| `lint` ok | 0 | lint files | CONFIRMED |
| `lint` warning naming another ledger | 0 or other | document only | UNCONFIRMED |
| `note` | unknown | ledger effect only | UNCONFIRMED (stdout, exit) |
| `handoff` | unknown | none | UNCONFIRMED |
| exit 1 (internal), 5 (kill switch), 6 (lock timeout) | 1, 5, 6 | none | UNCONFIRMED |
| `bind`, `create`, `init` (driver only) | n/a | prior driver script shape only | UNCONFIRMED |

### Stub design recommendations
- **Exit codes outside 0 to 6:** 64 when `CKPT_HOME` is unset or not an existing directory. Reserve 126, 127 and 128+n for the shell and signals (143 is the documented SIGTERM exit [CITED: headless]).
- **Switches (D-08):** `CKPT_STUB_KILL_SWITCH=1` forces exit 5. `CKPT_STUB_LOCK_TIMEOUT_MS` (default a few seconds) bounds lock waiting and exit 6; a test holds the lock in-process on a second descriptor to cause a genuine timeout (verified: a second `flock` on the same file from another descriptor blocks).
- **State:** under `CKPT_HOME`: `bindings/<uuid>.json`, `ledger-roots.json`, a dedicated lock file, and ledgers under a root registered beneath `CKPT_HOME`. Recommend refusing any ledger outside registered roots and registering roots only beneath `CKPT_HOME`, so a test can prove nothing is written elsewhere. Lock a dedicated file, never the ledger: `os.replace` swaps the inode and would orphan a lock held on the old file.
- **Invocation:** the wrapper runs `"$PY" -I -B "$STUB" "$@"` with an absolute interpreter recorded at setup, so a minimal PATH cannot change the interpreter and no bytecode lands in the repo.
- **No clock override.** D-08 allows only the exit 5 and 6 switches, so the replay normalizes timestamps, session ids and ledger paths by regex instead.
- **Branding (see Open Questions):** recommended reading is one extra stderr line per invocation, stripped by the replay normalizer, plus a banner on `--version` and the stub digest in `digests.txt`.
- **Session identity:** `--session` flag, else `CLAUDE_CODE_SESSION_ID`; short id is the first 8 characters [CITED: checkpoint-v1.md precondition 1 and the evidence ids].
- **Output encoding:** set UTF-8 on stdout at startup; `status` prints the arrow character.

### Wrapper design (STUB-04)
Copy the committed shape: log each call, then delegate unchanged. Armed injection: before delegating an `update` to the first section the caller touches, perform a real `update` to that section as a second bound session, so the stub returns a genuine exit 3. Arm count 2 gives a conflict on the first attempt and again on the retry; the third `update` then succeeds [VERIFIED: `row2-double-conflict/wrapper-checkpoint.sh` and its log]. The wrapper stays bash 3.2. The scripted replay for success criterion 3 plays the model: `show`, `update` (exit 3), `show`, `update` (exit 3), `show`, merge by hand, `update` (exit 0).

## Allowlist Matcher Model and Denial Detection

- **Corpus.** The 32 committed full traces hold 336 Bash calls, 94 of them flagged as refusals, each with the allowlist of its row in `tools.txt` [VERIFIED: parsed this session]. Refusal messages seen: "This command requires approval", "This Bash command contains multiple operations. The following part requires approval: ...", "... was blocked. For security, ...", "Output redirection to '...' needs approval", "Contains brace with quote character (expansion obfuscation)", and a `cp` flag refusal. Several refusals come from heuristics beyond rule matching (path scope, redirection, obfuscation checks). A faithful Python model of all of that is not possible; scope the model to rule matching only.
- **Model to implement:** split on the documented separators, require every part to match some allow rule (exact when no wildcard, prefix when trailing ` *` or `:*`), reject any part with a variable expansion, strip only the documented wrappers.
- **Tests it must pass:** the skill's canonical commands from committed traces match the pinned allowlist; the known-bad compounds do not; no rule shape such as a bare wrapper prefix matches `<wrapper> bind`, `<wrapper> create` or `<wrapper> init` (STUB-06). Per-verb rules (`status`, `show`, `validate`, `update`, `lint`, `note`, `handoff`) are how the committed row 3b rerun allowed the wrapper.
- **Ground truth** for the model is the S2 labelled capture; re-run S2 whenever the version or allowlist changes.
- **Denial detection (HARN-06).** Union of three structured signals: `system/permission_denied` events, `result.permission_denials`, and `tool_result` blocks with `is_error`. Cross-check the first two. Treat a stream with no `result` event, an unparseable line, or an unknown shape as an error, never a pass. A reply that contains the word "denied" is not a signal.

## Harness Primitives (verified techniques)

All run on `/usr/bin/python3` 3.9.6 on this APFS volume this session.

- **Exclusive creation:** `os.mkdir` and `os.open(..., O_CREAT|O_EXCL)` both raise `FileExistsError` on a second creation, including over a dangling symlink.
- **Atomic write:** `tempfile.mkstemp(dir=<target dir>)`, write, `flush`, `fsync`, `os.replace`.
- **Lock:** `fcntl.flock(fd, LOCK_EX|LOCK_NB)` in a deadline loop; a second descriptor on the same file conflicts inside one process, so lock contention is testable without a subprocess.
- **Measurer:** read bytes (never text mode: universal newlines would change CRLF counts), split with `re.split(rb'(?m)^(?=## )', data)`, count `len()` of each piece including the heading line. The first piece is empty when the file starts with a heading, so section sizes sum to the total. Caps: 800, 600, 500, 600, 1,000, 596 for the six plain sections and 4,096 for the file, in the order `Identity and state`, `Boundaries and blockers`, `Next action`, `Resume reading`, `Evidence and working changes`, `Do not redo` [VERIFIED: `SKILL.md` lines 134 to 139 and the Step 4 limits]. The prior one-off measurer used the same split but read in text mode. No committed original digest matches any committed file, since all evidence is sanitized, so test fixtures must be synthetic with hand-computed sizes: ASCII, a 2-byte letter, a 3-byte CJK character, a 4-byte emoji, CRLF, with `wc -c` as an independent oracle where available.
- **Manifest (HARN-08):** walk bytes paths with `os.walk(os.fsencode(root))`, sort by raw bytes, hash file bytes. Emit `sha.txt` in the committed shape (`<hex>`, two spaces, path) for ordinary names, with backslash escaping for newline, carriage return and backslash in names (the same convention `sha256sum` uses), and a lossless companion in JSON lines using `os.fsdecode` plus `json.dumps(ensure_ascii=True)`; lone surrogates round-trip back to the original bytes (verified). The committed row 10 evidence omitted a newline-named file because an earlier pipeline split on newlines; this design cannot.
- **Filesystem limits:** APFS refused a non-UTF-8 filename with `EILSEQ` (errno 92, verified), and it preserved an NFC name as written. So the non-UTF-8 case needs a skip with a stated reason plus a synthetic in-memory unit test, and the non-Latin fixtures should avoid characters with distinct NFC and NFD forms.
- **Git status capture:** run `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all` from the harness (it is not under the model's tool policy), keep the raw NUL form, and derive `status.txt` from the non-`-z` form to match the committed shape.
- **Sanitizer deny-list (EVID-02):** build at run time from `HOME` and the account database home, their `realpath`, the dash-slug (verified rule: both `/` and `.` become `-`, so a hidden folder gives a double dash; other characters [ASSUMED]), `urllib.parse.quote` forms with `safe=''` and `safe='/'` (match percent codes case-insensitively), the login name, `socket.gethostname()` plus `scutil` names on macOS, `tempfile.gettempdir()`, its `realpath` and `TMPDIR`. Apply longest-first. Mirror the Phase 1 floors: host names under six characters or on the generic list are dropped, local-file entries under four characters are dropped. Replace a login name only as a whole word and only when four or more characters; shorter names are already covered inside path forms. The optional local deny file is read, never printed, and a read error fails closed.
- **Leak gate (EVID-03):** scan file names and contents; refuse NUL bytes, undecodable bytes and symlinks; output is a count per file label, with `(file name)` as the label when the name itself matches (the precedent in `.githooks/checks/denylist.sh`). Any exception inside the scanner is a refusal.
- **gitleaks parity (D-14):** the six identifier rules are `home-path-unix`, `home-path-dash-slug`, `mac-temp-root`, `private-ipv4`, `internal-hostname`, `email-address`, plus two allowlists for the email rule [VERIFIED: `.gitleaks.toml` lines 7, 13, 19, 25, 32, 38, 43, 51]. All six regexes compile in Python 3.9 `re` and behaved as intended on positive and negative samples (including the scoped `(?i:...)` group in the allowlist). Strongest drift guard: read each `id` and `regex` out of the TOML with a small line reader and assert the Python strings are byte-identical; mirror the allowlist regexes too, including the path condition that allows the public address only in planning documents. The default gitleaks secret rules cannot be mirrored; add a small credential-shape list in Python and document the limit. `/root/` and drive-letter home paths are cheap additions (deferred idea).
- **`promote`:** gate first, then copy using exclusive creation for every directory and file, refusing existing targets, symlinks, traversal in names and any path whose realpath is under the Claude config directory.

## Self-Test Suite Wiring

- **Shim** (tested under bash 3.2.57): resolve its own directory, find `python3`, drop every PATH entry that holds an executable named `claude`, then `exec "$py" -I -B -m unittest discover -s "$here" -t "$here"`. With a tripwire `claude` first on PATH the suite passed and the tripwire never fired. Use `-B`: `-I` ignores `PYTHONDONTWRITEBYTECODE`, so that variable did not stop `__pycache__` and the flag does.
- **Discovery:** a flat directory with `test_*.py` and sibling modules works with `-s` and `-t` set to the same directory, even under `-I`.
- **Zero model calls:** run the suite with the shim and also a meta-test that runs it in a subprocess with a minimal PATH and a tripwire `claude`, asserting exit 0 and an empty tripwire log. Run the final verification with the system 3.9 interpreter explicitly.
- **Module names:** library modules share a `pc_` prefix. The start directory is put first on `sys.path`, so a module named `trace`, `types`, `select`, `platform`, `queue` or `code` would shadow the standard library. Add a test comparing every harness module stem with the standard-library module names.
- **Stdlib import scan (3.9-safe):** classify each imported top-level name by `find_spec` origin under the `stdlib` or `platstdlib` paths from `sysconfig`, excluding `site-packages` and `dist-packages`; built-ins count; sibling `pc_` modules count as local. Verified on 3.9.6: `json`, `fcntl`, `unittest` classify as stdlib; `pip`, `setuptools`, `yaml`, `tomllib` do not. `ast.parse(..., feature_version=(3, 9))` rejects `match`, `except*` and `type` statements but accepts parenthesized `with` and newer f-string nesting, so it is a partial guard only; the real proof is running on 3.9.
- **Bash 3.2 lint:** forbid `declare -A`, `mapfile`, `readarray`, case-conversion expansions (comma and caret forms), `[[ -v`, `&>>`, `|&`, `coproc`, `wait -n`, `local -n`, `declare -g`; avoid empty-array expansion under `set -u`. Run `bash -n` and, when `/bin/bash` is 3.2, run the shim. `shellcheck` is optional.
- **Repo hygiene:** add `tests/harness/.gitignore` for `__pycache__/` and `*.pyc` (the root `.gitignore` has no entry). The root `.gitignore` excludes `*.log` except under `tests/evidence/`, so any replay data file in `tests/harness/` must not end in `.log`.

## Architecture Patterns

### System Architecture Diagram

```
 committed evidence                                   stranger runs: tests/harness/selftest
 (logs, traces, snapshots)                                         |
        |                                                          v
        v                                         bash 3.2 shim: scrub PATH, python3 -I -B -m unittest
  miner (rerunnable) --> replay cases (json)                       |
                               |                                   v
                               v                          test_*.py (zero model calls)
   +----------------- replay suite ------------------+     |   |   |   |    |    |
   |  scratch CKPT_HOME                              |     v   v   v   v    v    v
   |   wrapper (bash: log + armed injection)         |   runroot manifest measure sanitize leakgate/promote
   |      |                                          |   stream-parser  allowlist-model  flags+version gate
   |      v                                          |
   |   stub (python: status show validate update     |   paid, one-off, outside the suite:
   |         note lint handoff; driver: bind create) |   S1 isolation  --> findings + init manifest
   +-------------------------------------------------+   S2 stream/policy --> findings + real fixture
                                                              |
                                              auth status (zero tokens) -> BLOCKED or proceed
                                              claude -p (pinned flags, stdin prompt, scrubbed env)
```

### Recommended Project Structure (flat, D-12)
```
tests/harness/
├── selftest                  # bash 3.2 shim
├── README.md                 # stranger guide, switches, first-login step
├── .gitignore                # __pycache__/ and *.pyc
├── checkpoint_stub.py        # single-file stub (importable and executable)
├── checkpoint-wrapper        # bash: logging and armed injection
├── pc_exitcodes.py           # preflight and gate codes (discretion)
├── pc_runroot.py  pc_manifest.py  pc_measure.py
├── pc_sanitize.py  pc_leakgate.py  pc_promote.py
├── pc_flags.py               # flag table, version gate, policy builder (source of truth)
├── pc_allowlist.py           # rule matcher model
├── pc_stream.py              # stream-json parser, denial detection
├── pc_mine.py                # miner for replay cases
├── replay-cases.json         # mined, committed, regenerated by a test
├── data/                     # spike fixture, flag-table prose, branch table prose
└── test_*.py
```

The README table of flags should be asserted against `pc_flags.py` by a test so prose and code cannot drift. Stub documentation (branch table, switches) stays under `tests/`; `references/checkpoint-v1.md` is untouched. Its current digest begins `eca134a3defc`, equal to the adapter digest in the committed row 5 to 12 evidence [VERIFIED: `shasum` and `digests.txt`], so an optional test can tie "unchanged" to the evidence.

### Anti-Patterns to Avoid
- **Locking the ledger itself** while replacing it (orphans the lock).
- **Branding by prefixing every line** (breaks the adapter's line-1 and `ledger lint OK` parsing).
- **Detecting denial from reply text.**
- **Trusting only `permission_denied` events** (documented best-effort).
- **Text-mode reads for byte counts** and **shell pipelines for names** (newline bugs).
- **Committing seeded leaks as literals** (see Pitfalls).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing `%q`-quoted argv from logs | A custom unescaper | `shlex.split` | Verified on all 15 recorded calls |
| Atomic writes | Write-then-rename by hand | `tempfile.mkstemp` + `os.replace` | Same-directory temp, fsync, no partial file |
| Locking | Polling for a marker file | `fcntl.flock` on a dedicated file | Released on process death |
| UUIDs, hashes, JSON, URL encoding | Custom code | `uuid`, `hashlib`, `json`, `urllib.parse` | Standard |
| TOML | A parser | A two-field line reader for `id` and `regex` only | D-11 forbids `tomllib`; the harness never needs more |
| Leak rules | A fresh rule set | The six `.gitleaks.toml` regexes, byte-identical | Parity test makes drift visible |
| Bash rule matching | Nothing exists to import | A bounded model validated against S2 | The only hand-rolled piece; keep it to rule matching |

**Key insight:** every fragile area here (byte counts, filenames, hashes, redaction) already failed once in the manual harness. The fixes are structural (bytes in, bytes out, no shell splitting), not clever.

## Common Pitfalls

### Pitfall 1: Green on the wrong Python
**What goes wrong:** The PATH interpreter is 3.14.7 here; the floor is 3.9.
**How to avoid:** Run the final suite with the system interpreter. Keep the AST feature check as a partial guard only.
**Warning signs:** `tomllib` or `match` imports pass locally.

### Pitfall 2: `-I` silently drops environment settings
**What goes wrong:** `PYTHONDONTWRITEBYTECODE` had no effect under `-I`; `__pycache__` appeared.
**How to avoid:** Pass `-B` explicitly; ignore bytecode in `tests/harness/.gitignore`.

### Pitfall 3: Seeded leaks and test strings trip the Phase 1 hooks
**What goes wrong:** Any literal home path with a user segment, private address, internal hostname suffix, or non-allowlisted email in committed test source fails gitleaks on commit. The same applies to this phase's own fixtures and prose.
**How to avoid:** Assemble seeds at run time from fragments, as `scripts/test-hooks.sh` does (its seed is "assembled at run time from three fragments") [VERIFIED: `scripts/test-hooks.sh` line 77]. Run the repo scan on every new file before staging.

### Pitfall 4: Sanitized evidence is not byte-equal to originals
**What goes wrong:** No committed file matches any recorded original digest, and path-bearing section hashes cannot be recomputed.
**How to avoid:** Synthetic measurer fixtures; replay asserts only path-free hashes exactly.

### Pitfall 5: Branding versus the adapter's parse
**What goes wrong:** `references/checkpoint-v1.md` says "Take the ledger from line 1 between `→ ` and the optional ` (`" and that non-matching output "is a failure, never a success". A prefix or plain suffix on line 1 breaks the binding precondition; a changed `ledger lint OK` breaks the lint check.
**How to avoid:** Keep every table-shaped stdout line byte-identical; put the brand where parsers do not look. Confirm in Phase 3's first real row that the extra line does not change model behaviour.

### Pitfall 6: Allow rules do not widen file scope
**What goes wrong:** The wrapper directory sits outside the project; `ls` and `wc` there were blocked even with allow rules.
**How to avoid:** Expect these denials in the corpus; decide per row whether `--add-dir` is part of the baseline, and record it in the flag table if so.

### Pitfall 7: Variadic `--allowedTools`
**What goes wrong:** A positional prompt after the flag may be read as another tool name.
**How to avoid:** One comma-joined argument, prompt on stdin.

### Pitfall 8: Identity fields in auth output
**What goes wrong:** `auth status --json` for a logged-in config probably carries account fields.
**How to avoid:** Parse only `loggedIn`; discard the rest; never write the raw output to evidence. Never include the config directory in snapshot roots or in `promote`.

### Pitfall 9: Tokens through the model's environment
**What goes wrong:** The earlier allowlists permit `Bash(env:*)`, so a credential in the environment could reach a trace.
**How to avoid:** Set the subprocess scrub variable, never export credentials, and let the sanitizer's key-shape list catch strays.

### Pitfall 10: Keychain entry outlives the directory
**What goes wrong:** Deleting the harness config directory leaves a Keychain entry; a recreated directory with the same path may or may not reuse it.
**How to avoid:** Say so in the run guide; the harness never deletes the directory.

### Pitfall 11: Opaque values in the committed stream fixture
**What goes wrong:** Thinking signatures and ids can resemble secrets to default gitleaks rules.
**How to avoid:** Run the scan before staging; placeholder only the offending value, same length, documented.

### Pitfall 12: Platform filename behaviour
**What goes wrong:** Non-UTF-8 names cannot be created on APFS; names differing only by case collide.
**How to avoid:** Skip with a stated reason and cover the byte logic synthetically.

### Pitfall 13: Module shadowing
**What goes wrong:** A harness module named like a standard-library module hides it for the whole suite.
**How to avoid:** The `pc_` prefix and the stem-comparison test.

### Pitfall 14: Bash 3.2 traps
**What goes wrong:** Empty-array expansion under `set -u`, and any bash 4 feature, fail on macOS.
**How to avoid:** The forbidden-feature list and an actual run under `/bin/bash`.

## Code Examples

All verified on Python 3.9.6 this session unless stated.

### Exclusive run root and exclusive file
```python
import os
os.mkdir(path)                       # no exist_ok; FileExistsError on collision or dangling symlink
fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
```

### Section hash and measurer
```python
import hashlib, re
def section_hash(body: str) -> str:
    return hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()

def measure(path):
    data = open(path, "rb").read()                      # bytes, no newline translation
    pieces = re.split(rb"(?m)^(?=## )", data)           # first piece empty when file starts with a heading
    return len(data), [(p.split(b"\n", 1)[0][3:].decode(), len(p)) for p in pieces if p.startswith(b"## ")]
```

### Lock with deadline (works across descriptors in one process)
```python
import fcntl, errno, time
def lock(fd, timeout):
    end = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); return True
        except OSError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN): raise
            if time.monotonic() >= end: return False    # caller exits 6
            time.sleep(0.02)
```

### Lossless name round trip
```python
import os, json
line = json.dumps(os.fsdecode(name_bytes), ensure_ascii=True)
assert os.fsencode(json.loads(line)) == name_bytes
```

### Stdlib classifier (3.9-safe)
```python
import sys, sysconfig, importlib.util, os
def is_stdlib(top):
    if top in sys.builtin_module_names: return True
    spec = importlib.util.find_spec(top)
    if spec is None: return False
    if spec.origin in ("built-in", "frozen"): return True
    o = os.path.realpath(spec.origin or list(spec.submodule_search_locations)[0])
    if "site-packages" in o or "dist-packages" in o: return False
    std = {os.path.realpath(sysconfig.get_paths()[k]) for k in ("stdlib", "platstdlib")}
    return any(o == s or o.startswith(s + os.sep) for s in std)
```

### Wrapper log parse
```python
import shlex, re
m = re.match(r"^(\S+) (CALL|EXIT) ?(.*)$", line)
argv = shlex.split(m.group(3)) if m.group(2) == "CALL" else None
```

### Denial detection skeleton (HARN-06)
```python
def denials(events):
    seen = {e["tool_use_id"] for e in events
            if e.get("type") == "system" and e.get("subtype") == "permission_denied"}
    for e in events:
        if e.get("type") == "result":
            seen |= {d["tool_use_id"] for d in e.get("permission_denials", [])}
    return seen          # never inspect reply text
```

### Zero-token auth preflight (command shape)
```bash
CLAUDE_CONFIG_DIR="$harness_cfg" claude auth status --json   # exit 1 and loggedIn false when not logged in
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `-p` default depended on settings | `-p` starts in Manual mode when nothing sets a mode | 2.1.302 | Pin the mode anyway |
| Glob and Grep always in the tool set | Absent by default on macOS and Linux; naming them in `--allowedTools` restores both | current docs | Record `init.tools`; the old allowlists name them |
| `default` shown in `--help` | `--help` shows `manual`; both work | 2.1.200 | Pin `default`, assert the init string |
| `--bare` optional | Documented as the future default for `-p` | announced | Never rely on defaults; pass every flag |
| Model alias `sonnet` | Resolves to Sonnet 5.5 on the Anthropic API | current | Use the full id |

**Deprecated or outdated:** nothing in the pinned set is deprecated. `:*` is documented as equivalent to a trailing ` *`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `--allowedTools` variadic parsing can swallow a positional prompt | Flag table | Low; stdin avoids it either way |
| A2 | `--strict-mcp-config` with no `--mcp-config` gives zero MCP servers, including account connectors | Flag table, S2 | Extra tools in `init`; S2 asserts and the flag table adapts |
| A3 | An async `InstructionsLoaded` hook fires in `-p` and reaches the stream with `--include-hook-events` | S1 | Fall back to a file-writing hook; if neither works, the instruction audit needs a canary approach |
| A4 | Under a scratch config directory the real user-level CLAUDE.md is not read | S1 | Isolation claim fails; S1 must show it via the audit |
| A5 | `validate` byte count equals re-rendered block (+4 timestamp, -1 trailing newline) | Stub contract | Stub's `N` differs; harmless if replay matches by pattern |
| A6 | Conflict message goes to stderr | Stub contract | Merged in tool results, so low |
| A7 | Cache writes cost 1.25 times input | S2 budget | Cost estimate only |
| A8 | Dash-slug maps every non-alphanumeric to `-` (only `/` and `.` verified) | Sanitizer | Slug form of an unusual path escapes redaction; the generic home-path forms still catch most |
| A9 | Extra stderr brand line does not alter model behaviour | Stub design | Phase 3 row 1 shows divergence; fall back to banner-only branding |
| A10 | `show` and `update` trim only trailing newlines from bodies | Stub contract | Whitespace edge cases differ from the real build; listed UNCONFIRMED |
| A11 | Keychain entry for a recreated config path may persist or be reused | S1 guide | Run guide wording only |

## Open Questions

1. **How to satisfy D-09 (brand every model-readable output line) without breaking the adapter's parse of `status` line 1 and `ledger lint OK`?**
   - What we know: the reference parses line 1 between `→ ` and an optional ` (`, and treats any non-matching output as failure.
   - What's unclear: whether bokiko meant a literal per-line marker.
   - Recommendation: one stderr line per call, stripped in replay, plus banner and digest. Ask bokiko to confirm during planning. If a literal per-line brand is wanted, the adapter would have to change, which STUB-07 forbids.
2. **Token case: D-15 names `<HOME>`, `<REPO>`; the committed evidence and `CONVENTIONS.md` use `<home>`, `<repo>`, `<run>`, `<helper>`, `<auto-memory-root>`.**
   - Recommendation: emit the D-15 set verbatim, accept lowercase tokens as safe in the leak gate, and have the Phase 4 comparer normalize case. Confirm with bokiko.
3. **D-02 says the init event lists instructions. It does not.**
   - Recommendation: the hook-based audit above; record the correction in the S1 findings.
4. **Should the policy builder add `--add-dir` for the wrapper directory?**
   - What we know: out-of-project reads of the wrapper directory were blocked in the evidence.
   - Recommendation: do not add by default, since it changes the baseline; decide per row in Phase 3.
5. **`CLAUDE_CODE_OAUTH_TOKEN` via `claude setup-token` is a documented alternative to a Keychain login** [CITED: authentication]. D-03 locks the manual login, so this is only an option the run guide could mention if bokiko wants it; it moves a secret into the environment.
6. **Linux behaviour of the config-directory login** (file under the directory instead of the Keychain) is documented but untested here.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9 or newer | all harness code | yes | system 3.9.6, PATH 3.14.7 | none; floor is 3.9 |
| bash 3.2 | shims, wrapper | yes | 3.2.57 at `/bin/bash` | none needed |
| git | status capture, fixtures | yes | 2.50.1 | none |
| Claude Code CLI | spikes only | yes | 2.1.310 | self-test needs none |
| gitleaks | Phase 1 hooks, optional pre-scan | yes | 8.30.0 | Python gate is independent |
| shellcheck | optional lint | yes | present | skip |
| Subscription login inside the harness config directory | S1, S2 | no, one-time step | n/a | BLOCKED with login instruction (D-03) |

**Missing dependencies with no fallback:** none for the zero-token suite.
**Missing with fallback:** the harness-owned login, handled by D-03.

## Validation Architecture

Nyquist validation is disabled in `.planning/config.json`; this section maps each success criterion to concrete tests the planner can lift.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `unittest` (stdlib), run under Python 3.9.6 |
| Config file | none (flat directory discovery) |
| Quick run command | `python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p "test_<area>*.py"` |
| Full suite command | `tests/harness/selftest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVID-07, SC1 | Suite exits 0 with `claude` absent and a tripwire never fires | meta | `test_selftest_shim.py` | Wave 0 |
| EVID-01, SC1 | Per-section and total UTF-8 bytes as actual/cap; multibyte, CRLF, oracle `wc -c` | unit | `test_measure.py` | Wave 0 |
| HARN-08, SC1 | Newline and non-Latin names round trip; byte-sorted; determinism across two runs | unit | `test_manifest.py` | Wave 0 |
| SC1 | Preflight paths: claude absent, not logged in, untested version map to distinct codes | unit | `test_preflight.py` | Wave 0 |
| STUB-01/03, SC2 | Replay of all 15 mined calls reproduces normalized outputs; four empty logs mean zero calls; four path-free hashes exact | integration | `test_stub_replay.py`, `test_mine.py` | Wave 0 |
| STUB-02/05, SC2 | Unset `CKPT_HOME` gives exit 64; output branded; branch table lists 0 to 6 and the UNCONFIRMED rows | unit | `test_stub_cli.py`, `test_branch_table.py` | Wave 0 |
| STUB-07, SC2 | `references/checkpoint-v1.md` digest equals the committed adapter digest | unit | `test_frozen_reference.py` | Wave 0 |
| STUB-04, SC3 | Armed wrapper gives exit 3 twice, then success after a manual merge; stub contains no injection or logging | integration | `test_wrapper_conflict.py` | Wave 0 |
| STUB-06, SC3 | No allow rule matches `bind`, `create`, `init` | unit | `test_allowlist.py` | Wave 0 |
| HARN-04, SC4 | Flag table equals policy builder output; simulated untested version gives its own exit code; README table matches code | unit | `test_flags.py`, `test_version_gate.py` | Wave 0 |
| HARN-06, SC4 | Skill's exact commands match; synthetic denial event or `permission_denials` entry fails; the word "denied" in a reply does not; real fixture parses | unit | `test_stream.py`, `test_allowlist.py` | Wave 0 (fixture from S2) |
| HARN-03, SC5 | Second creation errors; static scan finds no delete or overwrite of run roots | unit | `test_runroot.py` | Wave 0 |
| EVID-02, SC5 | Deny-list built from live machine; ordering; length floors | unit | `test_sanitize.py` | Wave 0 |
| EVID-03, SC5 | Seeded leak (assembled at run time) makes gate and `promote` refuse; scanner error refuses; counts only; gitleaks parity | unit | `test_leakgate.py`, `test_promote.py` | Wave 0 |
| HARN-14, SC5 | Only stdlib imports; no module shadowing; bash 3.2 shims lint and run | unit | `test_imports.py`, `test_bash_shims.py` | Wave 0 |

### Sampling Rate
- **Per task commit:** the quick command for the touched area.
- **Per wave merge:** `tests/harness/selftest`.
- **Phase gate:** full suite green on the system 3.9 interpreter, plus a clean Phase 1 scan of every new file, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] All test files above, none exist
- [ ] `pc_` modules, stub, wrapper, shim, `.gitignore`
- [ ] Spike findings and the real stream fixture (paid, outside the suite)

## Security Domain

`security_enforcement` is on (ASVS level 1).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (consumes it, never handles it) | Never read, copy or write credentials (D-03); read only the `loggedIn` boolean |
| V5 Input Validation | yes | Strict decoding, NUL and symlink refusal, traversal checks on names and labels, argv lists with no shell |
| V6 Cryptography | no hand-rolled crypto | `hashlib` SHA-256 for integrity only |
| V7 Error Handling and Logging | yes | Counts-only output; scanner errors fail closed; matched values never printed |
| V8 Data Protection | yes | Environment scrub, config directory excluded from snapshots and promote, local deny file never printed |
| V12 Files and Resources | yes | Exclusive creation, no delete or overwrite of run roots, same-directory atomic writes, 0600 temp files |
| V14 Configuration | yes | Pinned flags, `DISABLE_AUTOUPDATER`, explicit isolation |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal or symlink following in `promote` and run-root creation | Tampering | `lstat`, refuse symlinks, reject `..` and absolute names, exclusive create |
| Secret or identity echoed into evidence | Information disclosure | Runtime deny-list, key-shape rules, env scrub, gate before copy, hooks as second net |
| Scanner crash read as "no findings" | Repudiation | Any exception is a refusal; check every subprocess status |
| Regex catastrophic backtracking on large files | Denial of service | Reuse the linear-shaped gitleaks patterns; cap file size and refuse above it |
| Subprocess injection | Tampering | `subprocess.run([...])` with argv lists; no `shell=True` |
| Stub writing outside its state | Tampering | Registered roots beneath `CKPT_HOME` only; a test snapshots the parent before and after |
| Allowlist wider than intended | Elevation of privilege | Per-verb rules; matcher model test; S2 live proof |

## Sources

### Primary (HIGH confidence)
- https://code.claude.com/docs/en/cli-reference : flag rows, permission-mode alias, minimum versions
- https://code.claude.com/docs/en/headless : `-p` behaviour, stream-json, denials, signals
- https://code.claude.com/docs/en/permissions : Bash rule syntax, compound commands, wrappers, read-only set
- https://code.claude.com/docs/en/permission-modes : starting mode in `-p`
- https://code.claude.com/docs/en/authentication : credential storage keyed to `CLAUDE_CONFIG_DIR`, precedence, `setup-token`
- https://code.claude.com/docs/en/env-vars : config dir, session id, scrub, auto-updater
- https://code.claude.com/docs/en/agent-sdk/typescript : init, result, denial, hook message types
- https://code.claude.com/docs/en/hooks : `InstructionsLoaded`
- https://code.claude.com/docs/en/tools-reference : Glob and Grep availability
- https://code.claude.com/docs/en/model-config and https://platform.claude.com/docs/en/about-claude/models/overview : model id, pricing, effort, minimum versions
- Local, zero-token probes this session: `claude --version`, `claude --help`, `claude auth status --json` under a scratch config directory
- Committed repo files read this session: `references/checkpoint-v1.md`, `SKILL.md`, `.gitleaks.toml`, `scripts/test-hooks.sh`, `.githooks/checks/denylist.sh`, and the evidence listed in the stub section

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` and `PITFALLS.md` (live probes on 2.1.306, one machine)

### Tertiary (LOW confidence)
- None used as authority; all items from this tier are in the Assumptions Log.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, stdlib only and every technique run on 3.9.6
- Architecture: HIGH for the harness and stub split, MEDIUM for branding and spike outcomes
- Pitfalls: HIGH, most reproduced or taken from committed evidence

**Research date:** 2026-10-25
**Valid until:** 2026-11-08, because the Claude Code CLI ships often; re-check the flag table and `claude --help` if the installed version changes before the spikes run
