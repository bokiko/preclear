# Stack Research

**Domain:** Reproducible headless acceptance harness for a Claude Code skill (preclear), plus a test-only stub of the `checkpoint-v1` ledger helper CLI
**Researched:** 2026-10-21
**Confidence:** HIGH on Claude Code flags and event shapes (official docs fetched and cross-checked against live probes on Claude Code 2.1.306); MEDIUM on stub design details that depend on the private helper's unseen behaviour

## Recommendation in one paragraph

Drive Claude Code with plain `claude -p --output-format stream-json --verbose`, pinned flags, and **no Agent SDK, no `--bare`, no test framework, no jq**. Write the harness driver, the stream parser, the sanitizer, the byte measurer and the stub helper all in **Python 3 standard library only, targeting Python 3.9** (the version macOS ships). Keep bash to a few thin entry scripts that run on bash 3.2. Nothing the harness needs is an install: Claude Code is a native binary (Node is not required), `git` is already a dependency of the fixtures, and Python 3 arrives with the same Xcode Command Line Tools that provide `git` on macOS and is present on mainstream Linux.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Claude Code CLI (`claude -p`) | 2.1.306 verified today; the existing evidence ran on 2.1.304. Record the version in every run and pin a tested floor of 2.1.302 | The system under test, driven headless | `-p` is the documented scripting surface ("Run Claude Code programmatically"). Everything the acceptance harness rules require (setting sources, per-run `autoMemoryDirectory`, session ids, resume, allowlist, usage by category) is a first-class flag or event field. 2.1.302 is the release where `-p` without a permission mode starts in Manual mode, so the floor keeps the allowlist semantics stable | HIGH |
| Python 3 (stdlib only) | Target 3.9 syntax. Verified: macOS 26.6 ships 3.9.6 via the Command Line Tools; Ubuntu 22.04 ships 3.10, Debian 12 ships 3.11 | Harness driver, stream-json parser, sanitizer, byte measurement, snapshot manifests, and the stub helper | Zero installs on both targets. Real JSON parsing (no jq dependency), real regex (sanitizing), real `hashlib`/`os`/`fcntl`/`subprocess`, byte-exact UTF-8 counting, a portable run-time watchdog (macOS has no `timeout` command; confirmed in a probe). The existing harness already uses Python for `pub-file.py` and `pub-measure.py`, so this removes a dependency rather than adding one | HIGH |
| bash | Target 3.2 (macOS `/bin/bash` is 3.2.57, verified) | Thin entry scripts only: environment pinning, then `exec python3 ...` | Matches the existing `pub-*.sh` entry style, but with no associative arrays, no `${var,,}`, no `mapfile`, no GNU-only flags. Lint with `shellcheck --shell=bash` if the author has it; it is a dev convenience, not a run requirement | HIGH |
| Python `unittest` | stdlib | Self-test of the stub and the sanitizer | pytest and bats-core are installs. `python3 -m unittest` needs nothing | HIGH |

### Headless invocation contract (verified flags)

All rows verified against the official CLI reference and headless pages on 2026-10-21, and the starred ones also exercised live on 2.1.306.

| Flag | Use in the harness | Verified behaviour |
|------|--------------------|--------------------|
| `-p` / `--print` | Every model turn | Non-interactive. Exit 0 on success, non-zero on failure. Failures inside a run (for example missing auth) are printed as the result on stdout, so judge success from the `result` event, not the exit code alone |
| `--output-format stream-json` * | Always, for trace evidence | Newline-delimited JSON events. **Requires `--verbose` together with `-p`**; without it the CLI exits 1 with "When using --print, --output-format=stream-json requires --verbose" (reproduced) |
| `--verbose` * | Always with stream-json | Required companion, see above |
| `--include-partial-messages` | **Do not use** | Adds token-delta noise; the sanitized traces want whole `assistant` and `user` messages |
| `--setting-sources project,local` * | Every run | Loads only project and local settings. Live probe: user-level instructions were not in the model's context and the init event's `skills` list contained only built-ins, so a personal `preclear` skill or user CLAUDE.md cannot shadow or leak into the test. This is the reproducibility lever, not `--bare` |
| `--settings <file>` * | Every run, one JSON file per run containing `{"autoMemoryDirectory": "<absolute fixture-local path>"}` | `autoMemoryDirectory` is accepted from any scope including `--settings`; the value must be an absolute path or start with `~/`. Live probe: `init.memory_paths.auto` echoed the configured directory, which gives the harness a **machine-checkable setup gate** (see Pitfalls on `realpath`) |
| `--session-id <uuid>` * | Every model turn that starts a conversation | Must be a valid UUID (non-UUID gives "Invalid session ID. Must be a valid UUID."). Reusing an existing id fails with "Session ID ... is already in use." (reproduced), which is the exclusive-creation behaviour the harness safety rule wants. Lets the harness pre-bind a known session id in the stub's registry before the model runs |
| `--resume <uuid>` * | Same-session follow-up turns (for example the `/preclear` turn after the work turn) | Reproduced: the resumed run reports the same `session_id`, and the Bash tool's `CLAUDE_CODE_SESSION_ID` equals it. A **fresh-resume row uses a new `--session-id`, not `--resume`**, because a fresh session is the thing under test |
| `--allowedTools "<rule>" ...` * | Pinned literal allowlist per row, written to `tools.txt` as today | Permission-rule syntax; `Bash(cmd *)` is prefix match and the space before `*` matters. **Commands containing `$VAR` expansions are denied even when a prefix rule matches** ("A variable in this command can't be checked before it runs"), and **compound commands (`;`, `&&`, pipes) need every part allowed** (reproduced: "contains multiple operations"). Rules must use literal absolute paths, and the allowlist must be tested against the skill's exact commands (this already bit rows 10 and 11) |
| `--permission-mode default` | Every run, pinned explicitly | Since 2.1.302 a `-p` run with no mode set starts in Manual; the docs say `-p` is the surface whose defaults are changing (bare mode "will become the default for `-p` in a future release"). Pin it and assert `init.permissionMode == "default"` so a future default change cannot silently alter behaviour. Calls needing approval are denied unless allowed. Manual and `default` are the same mode |
| `--max-turns N` | Safety cap per turn | Print-mode only; exits with an error at the limit. Treat a hit as a failed run, not a pass |
| `--max-budget-usd X` | Safety cap per turn | Print-mode only, client-side estimate, can be exceeded slightly. Leave headroom |
| `--model <full id>` | Pin | Aliases (`sonnet`, `opus`) move over time; pass the full model name and also record `init.model`. The model used by the existing evidence is not recorded in the files read for this research: UNCONFIRMED, decide in planning |
| `--no-session-persistence` | Setup probes only | Sessions are not saved and cannot be resumed. Never on rows that resume or re-read a session |
| `--bare` / `CLAUDE_CODE_SIMPLE=1` | **Do not use** | Skips CLAUDE.md discovery, auto memory, hooks and the skills list, and never reads OAuth or keychain credentials (needs `ANTHROPIC_API_KEY`). preclear's test needs the fixture's CLAUDE.md configuration block, auto memory, and the project skill, and a stranger may be on a subscription login |

### Stream events the harness must parse (verified live on 2.1.306)

| Event | Fields to extract | Use |
|-------|-------------------|-----|
| `system/init` | `session_id`, `claude_code_version`, `model`, `permissionMode`, `apiKeySource`, `cwd`, `memory_paths.auto`, `skills`, `plugins`, `tools`, `mcp_servers` | Setup gate and the "record version, setting sources, skill" harness rule. Fail setup if `memory_paths.auto` does not realpath-equal the fixture memory root, if `permissionMode` is not `default`, or if `preclear` is absent from `skills` (the last check is UNCONFIRMED until a run with the skill installed; verify in the first phase) |
| `assistant` (content blocks `tool_use`) | tool name, input | The list of **attempted** actions, keyed by `tool_use.id` |
| `user` (content blocks `tool_result`) | content, `is_error` | Results keyed by `tool_use_id`; the "full results for denials, non-zero exits and conflicts" evidence |
| `system/permission_denied` | `tool_name`, `tool_use_id`, `decision_reason_type`, `decision_reason` | "Report blocked attempts separately from successful filesystem changes" comes straight from this event |
| `system/api_retry` | `attempt`, `error_status`, `error` | Flag runs disturbed by API retries so they are not mistaken for skill behaviour |
| `result` | `subtype`, `is_error`, `terminal_reason`, `num_turns`, `result`, `session_id`, `permission_denials[]`, `total_cost_usd`, `usage` (`input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`), `modelUsage` | Verdict plumbing and the "token usage by category" report. `permission_denials` cross-checks the `permission_denied` events |

### Stub helper (`checkpoint-v1`, test-only)

| Decision | Choice | Why |
|----------|--------|-----|
| Language | **Python 3.9, stdlib only, one file**, `#!/usr/bin/env python3` | See the comparison below. Same runtime as the rest of the harness |
| Location and shape | Single executable file under `tests/` (for example `tests/harness/checkpoint-stub`), no package, no dependencies | The `Preclear configuration` block takes an absolute `executable`; one file is one path to allowlist and one digest to record in `digests.txt` |
| Hash | Lowercase sha256 hex, 64 characters, over the section body | Calibrated from the committed evidence: every `section-hash:` line in `tests/evidence/` is 64 hex characters. The real helper's normalization is not public and preclear treats the hash as opaque, so any stable function is faithful at the interface |
| Session identity | `--session` flag, else `CLAUDE_CODE_SESSION_ID`; short id is the first 8 characters | Official docs: Claude Code sets `CLAUDE_CODE_SESSION_ID` in Bash tool subprocesses and it matches the session's id (confirmed live). The stub therefore needs no wrapper to learn the id |
| State | Directory from `CKPT_HOME` holding a bindings registry and the list of registered ledgers; ledger is a Markdown file with the `<!-- CHECKPOINT:BEGIN ... -->` block from `references/checkpoint-v1.md` | Matches the isolation the existing harness used and lets each row own its registry |
| Exit codes | 0 ok, 1 internal, 2 usage or validation, 3 conflict, 4 invalid checkpoint, 5 kill switch, 6 lock timeout | As specified. `argparse` already exits 2 on usage errors. Kill switch is a marker file in `CKPT_HOME`; lock is `fcntl.flock` with a short timeout |
| Atomic writes | Write to a temp file in the same directory, then `os.replace` | Never leaves a half-written ledger even if the model's turn is killed |
| Conflict | On `update`, compare the presented `--expect-section` hash with the current hash; on mismatch write `conflict-<UTC timestamp with ms>Z-<8 hex>.md` and exit 3 naming it. File shape (title, `ledger:`, `your base hash`, `current hash`, `## Yours (not applied)`, `## Current (kept)`) follows the committed conflict evidence | Rows 2 and the conflict case need the same branch the real helper produced |
| Fault injection | Environment switches read by the stub itself: `CKPT_STUB_LOG=<file>` (append `CALL <argv>` and `EXIT <code>` lines in the same shape as the old `wrapper-calls.log`), and `CKPT_STUB_INJECT_CONFLICT=<n>` (a simulated concurrent writer changes the section before the first n updates compare, logging each injection) | Replaces the old separate logging wrapper and counting conflict wrapper with zero extra executables. Attempted-but-denied calls still appear only in the trace, as in the existing evidence, because a denied call never reaches the stub. MEDIUM: a thin wrapper is the alternative if planning prefers byte-for-byte parity with the earlier row artifacts |
| Output encoding | `sys.stdout.reconfigure(encoding="utf-8")` at startup | The status line contains the `→` arrow and ledger text is non-Latin in row 10; a C locale on a minimal Linux image would otherwise raise `UnicodeEncodeError` and exit 1 |
| Validation rules | Exactly the six section headings, no others, rendered block (markers and headings included) at most 4,096 bytes measured in UTF-8, `Authorization boundaries` non-empty and at most 600 characters | Copied from the interface table; the byte limit must count the markers, which a character count would get wrong |
| Contract test | `python3 -m unittest` file that replays the observed-output table in `references/checkpoint-v1.md` and the committed evidence samples (unbound line, bound two-line status, `checkpoint: NONE`, `ledger lint OK`, exit 3 with conflict file) | The stub's whole job is to match the documented interface; a test that parses the reference table keeps it from drifting |

### Supporting Libraries (all stdlib)

| Module | Purpose | When to Use |
|--------|---------|-------------|
| `json` | Parse stream-json, write `settings.json`, bindings registry | Always. Do not shell out to jq (not present on minimal Linux) |
| `subprocess` with `start_new_session` and `Popen.communicate(timeout=...)` | Run `claude -p` with a watchdog | Always. On timeout send **SIGINT first** (docs: ends the turn cleanly and records a result), then SIGTERM (exit 143, turn left unfinished) |
| `uuid` | `uuid.uuid4()` for `--session-id` | Always. `uuidgen` is not guaranteed on minimal Linux |
| `hashlib` | sha256 for section hashes, skill digest, `tree hashes` | Always. Avoids the `sha256sum` (Linux) versus `shasum -a 256` (macOS) split |
| `os.mkdir` (no `exist_ok`) | Exclusive creation of run roots | Always. Atomic, raises on collision, which implements "never delete or overwrite an existing run root" without any `rm` |
| `os.walk`, `os.fsencode` | Snapshot manifests | Always. Handles newline and non-UTF-8 filenames in-process, which is exactly what bit the `-print0` snapshot code |
| `re` | Sanitizing home paths, hostnames, run roots into the fixed tokens (`<run>`, `<helper>`, `<repo>`, `<home>`, `<auto-memory-root>`) | Always. Sanitize from a **replacement table built from the live environment** (real home, real run root, hostname) and then run a deny-scan over the output |
| `fcntl` | Ledger lock in the stub | Stub only (POSIX, fine for macOS and Linux; native Windows is out of scope) |
| `argparse` | Stub argument parsing | Stub only; usage errors already return exit 2 |
| `unittest` | Self-tests | Always |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `shellcheck` | Lint the thin bash entry scripts | Optional, author-side only; not required to run the matrix |
| `git` | Fixture creation (unborn, detached, linked worktree, hostile filenames) | Already required by the fixtures and by the skill's read-only git use. Set `GIT_CONFIG_GLOBAL=/dev/null`-style isolation only if a stranger's global config changes `git status` output; decide in planning |

## Installation

```bash
# Nothing to install beyond Claude Code itself.
# Claude Code (native installer, documented as the recommended route; no Node.js required)
curl -fsSL https://claude.ai/install.sh | bash
claude --version          # record in every run; tested: 2.1.304 (existing evidence), 2.1.306 (this research)

# Harness prerequisites already present on macOS 13+ and Ubuntu/Debian
git --version
python3 --version         # needs 3.9 or newer
```

Authentication is the stranger's own: a subscription login or `ANTHROPIC_API_KEY` both work for `claude -p` without `--bare` (when the key is set, `-p` always uses it).

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Plain `claude -p` + stdlib Python driver | Claude Agent SDK (`claude_agent_sdk` for Python, TypeScript package) | The SDK is a pip or npm install, which breaks "no installs", and it gives native message objects and tool-approval callbacks the harness does not need. Revisit only if the harness must make dynamic approval decisions mid-run |
| Python stub | Bash stub | Only if Python were unavailable. macOS ships bash 3.2 with BSD userland: no associative arrays, different `sed -i`, `stat`, `date`, `sha256sum`, and byte-exact UTF-8 section parsing, hashing and atomic locking in shell is where a "must match the real helper's branches" stub breaks first |
| Python stub | Node stub | Only if every user is already on Node. Claude Code's native installer does not need Node, and the docs state the installed binary does not invoke Node, so a Node stub would be a new prerequisite. Node 26 is on the author's machine but that is not the audience |
| stdlib `unittest` | pytest, bats-core | When contributors may install dev tools. Not for the "stranger clones and runs" path |
| Own sanitizer in Python | `sed` pipelines | `sed` cannot do multi-line replacement tables safely and differs between BSD and GNU. The medium audit finding (home paths in committed evidence) was a sanitizer failure, so the sanitizer deserves a real language plus a deny-scan |
| `--setting-sources project,local` | `CLAUDE_CONFIG_DIR` pointing at an empty directory | Use the config-dir route only for API-key users who want total isolation. On a subscription login it can hide the stored credentials; not verified here, so do not make it the default |
| Direct `--allowedTools` list, `--permission-mode default` | `--permission-mode dontAsk` | `dontAsk` is an explicit deny-all-unlisted mode and would also be deterministic, but it changes the pinned permission mode relative to all existing evidence. Keep `default` for row-for-row comparability |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `--bare` / `CLAUDE_CODE_SIMPLE=1` | Disables CLAUDE.md discovery, auto memory, skill listing and OAuth, i.e. most of what preclear's rows test | `--setting-sources project,local` plus a per-run `--settings` file |
| `--dangerously-skip-permissions` or `--permission-mode bypassPermissions` | Defeats the "fail on any unauthorized write or deletion attempt" rule; denials are evidence | Pinned `--allowedTools` and `--permission-mode default` |
| `--permission-mode auto` | A classifier decides, so the same row can differ between runs | Explicit allowlist |
| `--no-session-persistence` or `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` on real rows | Breaks `--resume` and removes the transcript used for the raw transcript digest | Default persistence; use the flag only for throwaway probes |
| `--include-partial-messages` | Token deltas flood the trace | Whole messages only |
| Commands with `$VAR` or compound operators in the model-facing allowlist path | Denied by the permission checker regardless of prefix rules | Literal absolute paths in the fixture configuration; let the stub read `CLAUDE_CODE_SESSION_ID` from its own environment |
| `jq`, `timeout`, `uuidgen`, `sha256sum`, `readlink -f`, `sed -i` in harness code | Present on this macOS but absent or different on minimal or other systems | The Python stdlib equivalents above |
| `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` as isolation | The docs say these also disable feature-flag fetching, which can change client behaviour relative to the existing evidence | Leave them unset; set only `DISABLE_AUTOUPDATER=1` so the CLI cannot change version mid-matrix, and record the version at start and end |
| `claude purge` or any `rm -rf` in the harness | Project rule: no deletion of existing run roots; deletion needs bokiko's explicit word | Exclusive creation with `os.mkdir`; leave cleanup to the owner |
| Reading or copying the real helper's source into the stub | The real helper stays private; the repo is going public | Implement from `references/checkpoint-v1.md` and the committed evidence only |

## Stack Patterns by Variant

**If the stranger uses a subscription login:**
- Run with the default credentials, no `--bare`, no `CLAUDE_CONFIG_DIR` override.
- Because `--bare` never reads OAuth, and the keychain entry for a different config directory is not verified to carry over.

**If the stranger uses `ANTHROPIC_API_KEY`:**
- Same invocation; the key is always used in `-p` when present. Report `init.apiKeySource` in the run header.
- Because cost and rate limits then differ from a subscription, and the evidence should say which one produced it.

**If a row must provoke a conflict, denial or collision:**
- Use a fixture copy and the stub's fault-injection switches, never a live session (existing acceptance rule).
- Because the injected branch is then deterministic and logged.

**If a row needs the NUL form of `git status -z`:**
- Make the allowlist rule match the exact command string the skill issues, and verify the match with a dry run that captures `permission_denied` events before spending a full row.
- Because the `-z` form has never executed under the headless policy and the earlier allowlist miss was found only after the fact.

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| Claude Code 2.1.302 or newer | `-p` starts in Manual mode when no mode is set | Pin `--permission-mode default` anyway |
| Claude Code 2.1.306 (tested today) | stream-json `system/init` with `memory_paths`, `permission_denied` events, `result.permission_denials` | These fields were read from live output; the official docs describe `permission_denied` and `permission_denials` explicitly, `memory_paths` only appears in live output (MEDIUM) |
| Claude Code 2.1.304 | Existing publication evidence | Runs on 2.1.306 should be recorded as a version delta, not mixed silently |
| `--permission-prompts none` | Needs 2.1.259 or later | Optional extra: not needed with `--permission-mode default` plus an allowlist |
| Python 3.9 (macOS CLT) | Ubuntu 22.04 (3.10), Debian 12 (3.11) | Avoid `match`, `X \| Y` annotations (use `from __future__ import annotations`), and `zoneinfo`-style newer modules |
| bash 3.2 (macOS) | bash 5 (Linux) | Entry scripts must work on both; use `[ ]`, indexed arrays only |
| Alpine Linux | Supported by Claude Code but ships neither bash nor python3 by default | Out of scope for "no installs"; document `apk add bash python3` if asked |

## Sources

- https://code.claude.com/docs/en/headless (fetched 2026-10-21): `-p` behaviour, exit codes, SIGINT versus SIGTERM, stream-json, `system/init`, `api_retry`, `--allowedTools`, `--bare` limits, `--resume`, `--session-id` context. HIGH
- https://code.claude.com/docs/en/cli-reference (fetched 2026-10-21): every flag row in the contract table, including `--setting-sources`, `--settings`, `--session-id`, `--max-turns`, `--max-budget-usd`, `--no-session-persistence`, `--permission-mode`. HIGH
- https://code.claude.com/docs/en/permission-modes (fetched, section "Tool calls denied in `claude -p`"): 2.1.302 default-to-Manual for `-p`. HIGH
- https://code.claude.com/docs/en/memory (fetched): `autoMemoryDirectory` accepted from user, project, local, policy or `--settings`; absolute path or `~/`. HIGH
- https://code.claude.com/docs/en/env-vars (fetched): `CLAUDE_CODE_SESSION_ID` is set in Bash tool subprocesses, `DISABLE_AUTOUPDATER`, `CLAUDE_CODE_SIMPLE`, telemetry variables and the feature-flag side effect. HIGH
- https://code.claude.com/docs/en/setup (fetched): native installer recommended, installed binary does not invoke Node, macOS 13+ and Ubuntu 20.04+ and Debian 10+ supported. HIGH
- Live probes on Claude Code 2.1.306 in a scratch directory (stream-json shape, `memory_paths`, `--session-id` reuse error, `--resume` session id, `$VAR` and compound-command denials, `--verbose` requirement, user-instruction isolation with `--setting-sources project,local`). HIGH for what was observed, one model and one machine
- Local environment checks: macOS `/bin/bash` 3.2.57, `python3` 3.9.6, no `timeout` command, `jq` present but not portable to minimal Linux. HIGH
- Committed evidence under `tests/evidence/` (section-hash length, conflict file shape, wrapper log shape, harness description in `publication-2026-10-20/README.md`). HIGH for the interface shape; the real helper's internals are not documented here
- Not consulted by design: the gitignored `runs/` folder and the real helper's source

---
*Stack research for: headless acceptance harness and stub helper for the preclear skill*
*Researched: 2026-10-21*
