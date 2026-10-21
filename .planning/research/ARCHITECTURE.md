# Architecture Research

**Domain:** Reproducible headless acceptance harness for a Claude Code skill (preclear), with a test-only stub ledger helper
**Researched:** 2026-10-21
**Confidence:** MEDIUM-HIGH. Component shapes, evidence formats and helper output strings are HIGH (derived from the committed evidence and the adapter spec). Claude Code flag behavior is MEDIUM (official docs plus `claude --help` on 2.1.306; the accepted evidence ran on 2.1.304). Hermetic isolation of user-level instructions is UNCONFIRMED and has a mandatory spike (see Open Questions).

Scope note: the gitignored `runs/` folder was not read. Everything about the previous harness below comes from the committed evidence (`tests/evidence/publication-2026-10-20/`, the layout rerun folders), `tests/acceptance.md`, and the planning documents.

Paths in this document are repo-relative or tokens (`<repo>`, `<run>`, `<helper>`), the same tokens the sanitized evidence uses.

## Standard Architecture

### System Overview

One orchestrator drives a pipeline per row. The only things that cross the private-to-public boundary are sanitized copies produced by one component.

```
 PRIVATE SIDE (run root, outside the repo, raw, contains real paths)         PUBLIC SIDE (repo)
┌──────────────────────────────────────────────────────────────────┐        ┌────────────────────────┐
│ Row spec (declarative) ─► Orchestrator (run-row / run-matrix)    │        │ tests/fixtures/  (RO)  │
│                              │                                   │ copy   │ SKILL.md, references/  │
│  1 Run-root allocator        │  (exclusive mkdir, realpath)      │◄───────│  (RO inputs)           │
│  2 Materializer              │  fixture copy, git init, skill    │        └────────────────────────┘
│                              │  install, config variant,         │
│                              │  settings, memory root, ledgers   │
│  3 Policy builder            │  allowlist, --tools, env, PATH    │
│  4 Helper stack  (per run)   │  claude ─► wrapper ─► stub        │
│        wrapper: log + inject │        CKPT_HOME=<run>/helper-state
│        git shim: concurrent change                               │
│  5 Stage runner              │  claude -p x N stages             │
│        s1 work ► s2 /preclear ► s3 fresh resume ► s4/s5 variants │
│  6 Snapshotter               │  snap-N-* after every stage       │
│  7 Stage hooks               │  chmod, external edit, worktree...│
│  8 Trace extractor           │  stream-json ─► short + full trace│
│  9 Measurer (originals)      │  UTF-8 bytes, per section         │
│ 10 Mechanical checks         │  objective PASS/FAIL/UNCONFIRMED  │
│        │                                                         │
│        ▼  staging/ (text only, original names)                   │
│ 11 Sanitizer ─► 12 Leak gate (fail closed) ─► 13 Evidence filer ─┼───────►┌────────────────────────┐
└──────────────────────────────────────────────────────────────────┘ O_EXCL │ tests/evidence/<run>/  │
                                                                            │   <row>/ …             │
        14 Evidence comparer (reads old + new evidence, read-only) ◄────────┤ (sanitized, committed) │
                                                                            └────────────────────────┘
```

Reading the picture: left to right is data flow. Nothing flows from public back into a run except the read-only inputs (fixtures, skill files). The comparer only reads.

### Component Responsibilities

| # | Component | Owns | Does not do | Typical implementation |
|---|-----------|------|-------------|------------------------|
| 1 | Run-root allocator | Exclusive creation of a fresh run root; `realpath` of every path later written into config; a collision is a hard error | Never reuses, empties or removes a root. A failed setup root is marked `ABANDONED` and left on disk | Python `os.mkdir` (no `exist_ok`), `os.path.realpath` |
| 2 | Materializer | Turns fixture plus row spec into a runnable project: copies fixture, replaces the fixture's placeholder project path, deterministic `git init` and commit, installs `SKILL.md` and `references/` under the project's `.claude/skills/preclear/`, renders the configuration block from a variant template, writes `settings.json` (memory pin), creates ledgers and memory roots | Never edits `tests/fixtures/` or the skill. Never decides allowlist or env | Python, template files under `tests/harness/config/` |
| 3 | Policy builder | One place that produces the allowlist string (`tools.txt`), the `--tools` set, the `--disallowedTools` set, `--add-dir` set, `--settings` path and the exact child environment | Does not run anything | Pure function of the row spec plus run root; unit-testable |
| 4a | Stub helper | The `checkpoint-v1` interface from `references/checkpoint-v1.md`: `status show validate update note lint handoff`, plus setup verbs `bind init create` for the driver only. State only under `CKPT_HOME` | No fault injection, no test modes, no logging policy. Refuses to run without `CKPT_HOME` (never defaults to a user-level directory) | Single-file Python 3 stdlib executable |
| 4b | Helper wrapper | The executable named in the configuration block. Logs every executed call (argv, exit code, UTC time) and delegates unchanged. Optional armed behavior: before delegating an `update`, perform a real update as a second bound session so the stub returns a genuine exit 3 (count 2 = conflict on the first attempt and again on the retry) | Never alters the caller's arguments, hashes or output | Bash, about 30 lines, same behavior as the accepted wrapper; recorded by digest |
| 4c | Git shim | A `git` earlier on `PATH` that appends one line to a named plain file on the model's own `status` call and ignores Claude Code's internal calls (those begin with `-c`) | Does not change git output | Bash |
| 5 | Stage runner | One `claude -p` process per stage with `--output-format stream-json --verbose`, `--session-id` for s1, `--resume <id>` for s2, a new id for fresh sessions; captures stdout, stderr, exit code, wall time, usage; enforces a timeout and `--max-turns` and `--max-budget-usd` | Does not interpret results | Python `subprocess` with timeout (macOS has no `timeout` binary) |
| 6 | Snapshotter | After setup and after every stage: copies ledgers and the `.preclear` tree, memory, writes `sha.txt` (sha256 of every file under the allowed roots), `status.txt` (git porcelain, escaped), `bindings-ls.txt`, `ledgers-ls.txt` | Not a git operation on the project beyond read-only status | Python `os.walk`, so filenames with newlines or non-Latin text are handled structurally (the earlier newline bug cannot recur) |
| 7 | Stage hooks | Row-specific state mutation between stages: `chmod` the project (row 7) or plan (row 6), append an external plan note (row 12), create a linked worktree (row 9), arm the injector, create hostile filenames (row 10), copy-and-retarget a checkpoint for the identity-collision case | Do not run the model | Python functions registered by row id |
| 8 | Trace extractor | Parses stream-json into `sN-preclear-trace.md` (short plus final reply) and `sN-preclear-full-trace.md` (every Bash, Write and Edit call with full result keyed by `tool_use` id; Read, Glob, Grep summarized by length). Counts calls, refusals (use the stream's `permission_denied` events and the result message's denial list, with the old text patterns as a cross-check), errors. Records the raw-transcript sha256 and size | Does not judge the model | Python; pairs `tool_use` blocks in assistant messages with `tool_result` blocks in user messages |
| 9 | Measurer | Independent oracle for sizes: total and per-section UTF-8 bytes on the ORIGINAL files, heading-inclusive, in the existing `measurements.txt` and `measurements.md` shapes; sha256 of each measured file | Never reads sanitized text. Never trusts the model's cap claims (defect D1: the model's own cap statements disagreed with the manifest in 5 of 12 runs) | Python; caps from `tests/harness/config/caps.json` |
| 10 | Mechanical checks | Objective, scripted verdicts per row: helper calls attempted vs executed, mutation attempts, ledger fingerprints unchanged or changed as expected, frozen copy hashes stable, no write outside approved roots, no git mutation, repo under test unchanged, checkpoint byte-identical after fresh resume, caps within limit, final reply ends in exactly one fenced single line, exit codes. Output `mechanical-checks.md` with PASS / FAIL / UNCONFIRMED per check | Does not assign the row verdict. Model-behavior judgments (routing quality, claim integrity such as row 7) stay with the reviewer | Python |
| 11 | Sanitizer | Pure function over text artifacts: ordered rewrite table to the existing tokens `<run>`, `<repo>`, `<helper>`, `<auto-memory-root>`, `<home>`; handles both the logical and physical (`realpath`) forms of each path | Never touches measured originals. Refuses binary or unknown file types rather than guessing | Python, rules built at run time from the actual run values (no literal user data in the repo) |
| 12 | Leak gate | Independent second pass on the sanitized staging tree. Fails closed if it finds the real home path, login name, hostname, `/Users/` or `/home/` prefixes, IPv4 or IPv6 addresses, email addresses, key-shaped strings, the owner's real name, or a path under the user-level Claude configuration directory | Does not repair. A failing file stays in staging; nothing is filed | Python; rules are values discovered at run time plus generic regexes |
| 13 | Evidence filer | Copies staged files into `tests/evidence/<run-label>/<row>/` using exclusive creation; writes `README.md` skeleton with mechanical results and `Reviewer verdict: PENDING`; writes `harness-version.txt` (commit of the harness), `claude-version.txt`, `model-id.txt`, `digests.txt` | Never overwrites, never deletes, never edits historical folders | Python |
| 14 | Evidence comparer | Row-for-row structural comparison of a new evidence folder with the old one (same row folder names): file-set diff, normalized helper-call sequence, exit codes, per-section byte table, refusal counts, stable hashes | Does not compare model prose or hash values (the stub defines its own hash function, so hash strings differ by design) | Python, read-only |

### Recommended Project Structure

Everything new lives under `tests/harness/`. Nothing in `SKILL.md`, `references/`, or `tests/fixtures/` changes.

```
tests/
├── acceptance.md                  # existing rules; later gains a "Run it with the harness" pointer
├── fixtures/                      # existing, read-only to the harness
├── evidence/
│   ├── publication-2026-10-20/    # existing, never touched
│   └── <rerun-label>/             # new: same row folder names as the old matrix
│       └── row1-wrong-binding/ …  # per-row file set (list below)
└── harness/
    ├── README.md                  # prerequisites, one-row quick start, isolation modes
    ├── bin/
    │   └── preclear-accept        # entry: check-setup | run-row <id> | run-matrix | compare <old> <new> | selftest
    ├── lib/                       # Python modules: runroot, materialize, policy, stages, snapshot,
    │                              #   trace, measure, checks, sanitize, leakgate, evidence, compare
    ├── rows/                      # one small file per row: fixture, config variant, memory mode,
    │                              #   helper mode, allowlist profile, prompts, stage hooks, expected helper-call shape
    ├── config/
    │   ├── caps.json              # section caps (guard test compares them with SKILL.md)
    │   ├── allowlists.json        # profiles: plain, helper-full, helper-readonly, git-exact
    │   ├── config-variants/       # CLAUDE.md configuration blocks (valid, unknown backend, relative path, conflicting, none)
    │   └── prompts/               # s1-work, s2-<variant>, s3-resume, s4/s5 variants
    ├── shims/
    │   ├── helper-wrapper.sh      # log + armed second-writer injector
    │   └── git-shim.sh
    ├── stub/
    │   ├── checkpoint             # the stub helper
    │   └── conformance/           # golden call/response scripts used by `selftest`
    └── selftest/                  # model-free tests: sanitizer, leak gate, measurer, stub, trace parser,
                                   #   policy builder, run-root collision, driver against a fake claude
```

Rationale: a row file is data plus at most one hook function, so adding a row never touches the engine. `selftest/` costs no tokens and runs before any model call. Python 3 standard library only (no packages to install; macOS and Linux). The two shims stay Bash because they are the configured executables the model calls and the accepted evidence shows that exact shape.

### Per-row evidence file set (committed, sanitized)

Matches the accepted rows so the comparer can diff by name. New files are marked.

```
README.md                     mechanical results, sequence, reviewer verdict (PENDING until Codex review)
claude-version.txt            e.g. "2.1.30x (Claude Code)"
model-id.txt                  (new) model id reported in the stream init event
isolation-mode.txt            (new) default | strict, plus the setting sources used
harness-version.txt           (new) harness commit, stub digest, wrapper digest
digests.txt                   skill, references, stub, wrapper, harness
fixture-CLAUDE.md             the rendered configuration block
tools.txt                     the exact allowlist string; (new) tools-set.txt for --tools and --disallowedTools
settings.json                 sanitized --settings content
s1-work.out s1.err s1.exit    work stage
s2-preclear-prompt.md         exact prompt including the correction
s2-preclear-trace.md          short trace and raw final reply
s2-preclear-full-trace.md     complete sanitized calls, results keyed by tool_use id
s2-preclear.err s2-preclear.exit session.id
s3-resume-trace.md s3-resume-full-trace.md resume-line.txt     (rows with a fresh resume)
snap-0-setup/ snap-1-after-work/ snap-2-after-preclear/ …      ledgers, sha.txt, status.txt, bindings-ls.txt
measurements.txt measurements.md                                originals, before sanitizing
wrapper-calls.log wrapper-checkpoint.sh wrapper-injection.log   helper rows
mechanical-checks.md          (new) objective checks with PASS/FAIL/UNCONFIRMED
usage.txt                     (new) tokens by category per stage, from the result event
```

Raw stream-json is not filed. It stays in the run root; the trace records its sha256 and size, as the accepted traces do.

## Isolation Boundaries

This section is the core design constraint. Each boundary has one owner, one place it is set, and one place it is verified.

| Boundary | Mechanism | Set by | Verified by |
|----------|-----------|--------|-------------|
| Run root | Fresh directory per row, exclusive creation, physical path | Allocator | A second allocation of the same name must fail (selftest) |
| Project path identity | The configuration block's `project` must equal the session's physical project path. On macOS a temp directory sits behind a symlink, so a logical path silently yields "no block applies" (state 1) and the backend row would test nothing | Materializer writes only `realpath` values | Mechanical check: rendered `project:` equals `pwd -P` captured in setup |
| Settings | `--setting-sources project,local` so user-level settings and hooks do not load; `--settings <run>/settings.json` pins `autoMemoryDirectory` and `autoMemoryEnabled`. Do NOT use `--bare`: it skips CLAUDE.md, skills and auto-memory, which are the things under test | Policy builder | `system/init` event recorded: tool list, loaded skills; zero hook events; Read of the project-installed `SKILL.md` and its digest appear in the trace |
| User-level instructions (UNCONFIRMED) | A stranger's own user-level `CLAUDE.md` and rules could change model behavior. The accepted evidence contains a model command that probes a path under the user-level configuration directory which appears nowhere in the skill or fixtures, a hint that user-level instructions may have loaded despite `--setting-sources project,local`. This must be tested, not assumed | Strict mode: `CLAUDE_CONFIG_DIR=<run>/claude-config` (empty) with token auth (`ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN`). Transcripts and auto-memory then also land inside the run root | Spike S1 (build order). Until it passes, `isolation-mode.txt` says `default` and the README states the residual risk |
| Memory root | Fixture-local directory pinned by `autoMemoryDirectory`; the fixture's `CLAUDE.md` is rendered from the same variable, so the instruction-named root and effective root cannot diverge | Materializer | `acceptance.md` rule: both resolve to the same directory, else setup fails before any model call |
| Helper state | `CKPT_HOME=<run>/helper-state`, set in the child environment and in the wrapper. The stub exits 2 if it is unset, so it can never touch a real state directory. Ledgers live in `<run>/ledgers/` | Policy builder (env), stub (refusal) | Snapshot hashes of helper-state and ledgers; wrapper log shows only verbs the profile allows |
| Child environment | Built explicitly: `PATH` (shim directory first for row 11 only), `CKPT_HOME`, locale `C.UTF-8` or `en_US.UTF-8` (non-Latin names), `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` pointed at an empty file, fixed `GIT_AUTHOR_*` and `GIT_COMMITTER_*` including dates (deterministic HEAD), pass-through of `HOME` and the auth variable only. An inherited `CKPT_HOME` or other `CLAUDE_*` variable is dropped | Policy builder | `harness.json` records the variable names (not values) passed |
| Allowlist | `--allowedTools` generated from a profile; per-verb helper entries (`status`, `show`, `validate`, `lint` for read-only rows; add `update`, `note`, `handoff` for mutation rows). Never `wrapper:*`, because that would allow `bind`, `init`, `create`, which the skill must never run. Pair with `--tools "Read,Write,Edit,Glob,Grep,Bash"` (Glob and Grep are off by default on macOS and Linux per current docs) and `--disallowedTools` for network and subagent tools | Policy builder | `tools.txt`; a policy probe (below) proves the skill's exact commands match |
| Permission mode | Pin explicitly (`--permission-mode default`, the alias of Manual). From 2.1.302 `-p` starts in Manual when nothing is set; pinning protects against default drift. Unlisted approval-needing calls are denied in Manual, which is what rows 3b and 7 rely on | Policy builder | Result event's denial list |
| Filesystem writes | Approved roots only: project, memory root, ledger root, evidence staging. Claude Code confines file tools to working directories; the harness adds `--add-dir` only for memory and ledger roots, recorded in `tools-set.txt` | Policy builder | Mechanical check: Write/Edit paths from the trace plus before/after `sha.txt` of every approved root plus `git status` of the repository under test (must be unchanged) |
| Git | Read-only for the model; the repository under test is never a run's project. Materializer builds its own repositories with fixed identity and dates | Materializer | `git status --porcelain` before and after at snapshot points |
| Privacy valve | Raw artifacts are private. Only text that passed sanitizer and leak gate can be filed | Evidence filer | Leak gate exit status gates filing; it also runs over the existing committed `tests/evidence/` tree as a regression check |

## Architectural Patterns

### Pattern 1: Faults are composed outside the stub, never built into it

**What:** The stub is a faithful interface implementation with no test modes. Faults come from layers around it: allowlist profile (denied write), wrapper (genuine conflict via a second bound session), configuration variant (missing executable, unknown backend), file permissions (read-only plan, unwritable project), unbound session (no binding file).
**When:** Always. It is what makes "the backend rows exercise the same branches" a claim about the skill, not about a mock.
**Trade-offs:** More moving parts than a `--fail-next` flag, but the conflict row then proves the hash guard really returns exit 3, and the stub's conformance suite is the only place the stub's own behavior is tested.

```bash
# helper-wrapper.sh essentials (shape of the accepted wrapper)
W="$(cd "$(dirname "$0")" && pwd)"
printf '%s CALL' "$(date -u +%FT%TZ)" >> "$W/calls.log"; printf ' %q' "$@" >> "$W/calls.log"; echo >> "$W/calls.log"
# armed injector: if "$1" = update and $W/armed > 0, run a real stub update as writer2, decrement armed
"$STUB" "$@"; rc=$?
echo "$(date -u +%FT%TZ) EXIT $rc" >> "$W/calls.log"; exit $rc
```

### Pattern 2: Golden-output stub derived from committed evidence

**What:** Stub output strings are copied from what the real helper printed in committed traces, not from memory. Verified strings in the evidence: `session <id8> → <ledger>` and `session <id8>: unbound`; `checkpoint updated <iso> by <id8>`; `show` header lines `ledger:`, `file-fingerprint:`, `checkpoint-updated: <iso> by <id8>` followed by `## <section>` and `section-hash: <hash>`; `valid checkpoint: <N> bytes, Authorization <M> chars`; `updated "<section>" in <ledger>`; conflict on stderr with exit 3 `checkpoint: conflict: "<section>" changed since your read. Nothing written. Details: <ledger>.conflict-<UTC>-<id8>.md`; `ledger lint OK`. The conflict file layout (`# Conflict on section`, `ledger:`, `your base hash:`, `current hash:`, `## Yours (not applied)`, `## Current (kept)`) is in the rerun conflict evidence.
**When:** Building the stub and its conformance suite.
**Trade-offs:** `handoff` and `note` outputs appear in no committed run; the stub implements them from the spec and the conformance suite marks them UNCONFIRMED against the real build. Exit codes 5 (kill switch) and 6 (lock timeout) are specified but never exercised by any row; implement 5 cheaply (a `disabled` marker under `CKPT_HOME`), skip 6 or implement with a bounded lock wait, and state the coverage gap in the stub README. The section-hash algorithm is the stub's own, so hash values never compare across helpers.

### Pattern 3: Setup through the helper's own setup verbs

**What:** The driver creates state by calling the stub's `bind`, `init`, `create` rather than writing its JSON files, so one component owns the state format. The committed bound-ledger fixture has no checkpoint block markers and no hash lines ("the hash lines are added by the helper"), so the stub's `init` wraps the fixture's six `## ` sections in `<!-- CHECKPOINT:BEGIN … -->` / `<!-- CHECKPOINT:END -->`. The six fixture headings already equal the six helper sections.
**When:** Materializing any helper row; `--session-id` lets the driver know the session UUID before launch, so the binding is written before the model runs (row 1 binds a different ledger; row 3c binds nothing; row 2 binds a second writer session).
**Trade-offs:** The model must never reach these verbs: allowlist per verb, and a mechanical check that the wrapper log contains none of them.

### Pattern 4: Measure originals, file sanitized copies

**What:** The measurer reads files from the run root before any rewriting; the sanitizer only ever produces copies in `staging/`. Evidence integrity needs two independent byte oracles, so the leak gate also recounts nothing: it only blocks.
**When:** Every checkpoint-producing run.
**Trade-offs:** Sanitizing changes byte counts (path tokens differ in length), so evidence files are not byte-comparable to originals; `measurements.*` is the canonical size record and says so.

### Pattern 5: One process per stage, session continuity by id

**What:** `claude -p` is one turn per process. s1 starts with `--session-id <uuid>`, s2 continues it with `--resume <uuid>` and a prompt that starts with `/preclear` (user-invoked skills expand in `-p`), s3 starts a new session whose prompt is the resume line extracted from s2's final fenced block. Snapshot between every process.
**When:** All rows. `--no-session-persistence` is usable only for fresh sessions that will never be resumed (s3, s4).
**Trade-offs:** s1 and s2 sessions persist transcripts in Claude Code's own storage, a side effect performed by Claude Code, not by the model; strict mode relocates it into the run root.

### Pattern 6: Mechanical verdict versus reviewer verdict

**What:** The harness produces facts and objective checks. The README is generated with `Reviewer verdict: PENDING`. Codex review (the project's acceptance rule) fills verdicts. The harness never writes PASS for a row.
**When:** Always, which also keeps the project rule "no acceptance claim without Codex consultation" intact.
**Trade-offs:** A human step remains, but it now starts from a complete fact table instead of raw transcripts.

## Data Flow

### Per-row flow

```
row spec ─► allocate <run> ─► materialize ─► policy build ─► preflight asserts ─► snap-0-setup
                                                                      │
                          ┌───────────────────────────────────────────┘
                          ▼
   s1 work  (claude -p --session-id U1)           ─► s1.stream.jsonl ─► snap-1-after-work
        │  stage hook (chmod / arm injector / external edit / worktree)
        ▼
   s2 /preclear + correction (claude -p --resume U1) ─► s2.stream.jsonl ─► snap-2-after-preclear
        │  extract resume line (last fenced single line of final reply)
        ▼
   s3 fresh resume (claude -p, new session U2)    ─► s3.stream.jsonl ─► snap-3-after-resume
        │  s4 / s5 variants where the row defines them (unbound repeat, refresh, collision)
        ▼
   post: trace extract ─► measure originals ─► mechanical checks ─► staging/ (text copies)
                                                       ─► sanitize ─► leak gate ─► file (O_EXCL) ─► tests/evidence/<run>/<row>/
```

### Matrix flow

`run-matrix` is a loop over row specs in the order fixed by `tests/acceptance.md` (three layouts, then twelve publication rows). Each row is independent: own root, own `CKPT_HOME`, own session ids. Default sequential. A matrix invocation skips rows that already have filed evidence under the target label (idempotent restart) and never overwrites. Per-stage `--max-turns` and `--max-budget-usd` bound cost; usage per stage is recorded from the result event, by category (input, cache creation, cache read, output) as the acceptance rules require.

### Helper call path (what the model sees)

```
model Bash tool ─► <run>/wrapper/checkpoint (configured executable; per-verb allowlist)
                      │ log argv + exit  ──► <run>/wrapper/calls.log
                      │ (armed) real update as writer2 ─► stub ─► ledger changes ─► exit 3 for the caller
                      ▼
                 <run>/helper/checkpoint (stub copy, digest recorded)
                      │ CKPT_HOME=<run>/helper-state
                      ▼
        bindings/<session>.json, ledger-roots.json, <ledger> (+ .conflict-* files, .checkpoint-log.jsonl)
```

State file names mirror the accepted snapshots (`helper-state/bindings/<session>.json`, `helper-state/ledger-roots.json`, `ledgers/.checkpoint-log.jsonl`, `<ledger>.conflict-<UTC>-<id8>.md`) so snapshot folders diff cleanly.

### Attempted versus executed (a first-class distinction)

Wrapper log = executed helper calls. Denied calls never reach the wrapper and exist only in the trace. The mechanical checks report both numbers per row ("attempted 1, executed 1, denied 0") exactly as the accepted READMEs do. Compound-shell refusals are counted as harness policy events, not helper denials.

## Row-to-Capability Matrix

What each row needs from the harness. This decides build order.

| Row | Needs |
|-----|-------|
| Layout plain-memory, hub-memory | materializer, memory pin, s1..s3, identity-collision copy hook, freshness-change hook, "blocked" prompt variant |
| Layout bound-ledger | stub, wrapper log, `init`/`bind`, conflict variant (injector), unbound variant (s4), tamper hook |
| 1 wrong binding | stub `status`, second ledger bound to the session, per-verb allowlist, fallback dir |
| 2 double conflict | injector armed=2, writer2 session bound to the same ledger, genuine exit 3 twice, conflict files, `lint` |
| 3a missing executable | config variant pointing at a nonexistent path, no wrapper |
| 3b denied helper write | read-only helper allowlist profile, bound session |
| 3c unbound, `fallback_directory: none` | no binding file, `none` variant, correct identity |
| 4a unknown backend, relative executable; 4b conflicting blocks | config variants only (two applicable blocks, one with `none`) |
| 5a no memory; 5b memory disabled | memory modes (absent root; `autoMemoryEnabled: false`) |
| 6 read-only plan | permission hook on the plan file |
| 7 all destinations denied | `chmod` hook on the project after s1; preflight proving the filesystem honors it (not running as root, not a permissive mount); otherwise the row is SKIPPED with a reason, never PASS |
| 8a non-git inside an unrelated parent repo; 8b detached HEAD; 8c unborn branch | git-state variants in the materializer, each with s3 fresh resume |
| 9 linked worktree | worktree hook, main checkout snapshot unchanged |
| 10 hostile filenames | file generator (newlines, quotes, non-Latin, thousands of entries), exact-command allowlist profile including the NUL status form, NUL-safe snapshots |
| 11 concurrent change during capture | git shim firing only on the model's own `status` call |
| 12 frozen handoff | external-edit hook between s2 and s3, s4 refresh, frozen-copy hash stable across snapshots (mechanical) |

## Build Order and Dependencies

Dependency graph:

```
S1 isolation spike ──────────────────────────────┐
S2 stream-json + policy probe (one cheap turn) ──┤
                                                 ▼
P1 pure libs: runroot, sanitizer+leak gate, measurer, snapshotter, trace parser ─┐
P2 stub + conformance + wrapper (log, injector)  (no model)  ────────────────────┤
                                                                                 ▼
P3a driver + materializer + policy builder, proven against a FAKE claude (replay of recorded stream-json)
P3b WALKING SKELETON: row 1 end to end with the real claude  ──► file one real evidence folder, run comparer vs old row 1
                                                                                 ▼
P4 row waves (each wave adds one capability, then runs its rows)
   A config/allowlist variants:        3a 3b 3c 4a 4b
   B memory and permission hooks:      5a 5b 6 7, plain-memory and hub-memory layouts (s1..s5 hooks)
   C git states and stage hooks:       8a 8b 8c 9 12
   D injector and git shim:            2, bound-ledger conflict/unbound/tamper, 10, 11
                                                                                 ▼
P5 comparer + full matrix from a clean clone ─► Codex review ─► docs (acceptance.md pointer, CHANGELOG)
```

Phase proposals for the roadmap:

1. **Prerequisite spikes (small, cheap, decide design).**
   - S1: does `--setting-sources project,local` keep user-level instructions out? Method: a throwaway project and a model-free signal is not possible, so use one headless turn that asks the model to list the instruction sources it loaded and whether it knows of any user-level rule; repeat in strict mode (`CLAUDE_CONFIG_DIR` empty plus token auth). Record which mode is hermetic. Also check whether `--restricted` (documented for evaluation harnesses, v2.1.248+) can load a project `CLAUDE.md` and a project skill; it removes command-running tools unless named in `--tools`, so adopt it only if both load.
   - S2: capture one real stream-json stream (all message types, `permission_denied`, result usage, `system/init` fields) to use as the trace-parser and fake-claude fixture; run a policy probe that proves every command the skill prescribes (exact git status forms, `wc`, `shasum`, helper verbs) matches the allowlist syntax on the installed Claude Code version (the colon form `Bash(x:*)` in accepted evidence versus the space-star form in current docs; the earlier harness shipped an allowlist that never matched the skill's exact status command). Confirm `CLAUDE_CODE_SESSION_ID` reaches the helper and that `--session-id` plus pre-written binding works.
2. **Model-free foundation (P1 and P2, parallelizable).** Sanitizer with leak gate (also run over the existing committed evidence as a regression check), measurer, snapshotter, run-root allocator, trace parser, stub, wrapper, conformance and collision selftests. Exit criterion: `preclear-accept selftest` green with zero tokens spent, including a scripted replay of row 2 against stub plus injector showing exit 3 twice, then success after a manual merge.
3. **Driver and walking skeleton.** Driver against a fake `claude` (environment variable overrides the binary), then row 1 with the real binary. Row 1 is the right first row because it touches every component except the injector and git shim: fixture copy, configuration rendering, `CKPT_HOME`, `bind` for two ledgers, wrapper log, per-verb allowlist, s1/s2, snapshots, measurement, sanitize, file, compare. Exit criterion: one evidence folder filed, comparer output reviewed against `publication-2026-10-20/row1-wrong-binding`.
4. **Row waves A to D** as in the graph. Each wave starts by adding exactly one capability, runs its rows, and files them. Rationale: failures are then attributable to one new capability, and the expensive injector and shim work is deferred until the cheaper rows prove the engine.
5. **Full matrix from a clean clone, comparison and review.** Run the three layouts and twelve rows from a fresh clone on a machine that has Claude Code and no private helper (the project's done-criterion). Include the clean row 7 rerun here (its defect is a content defect, not a harness defect). Then Codex review in a visible Herdr tab, CHANGELOG, `acceptance.md` pointer.

Research flags for phases:
- Phase 1 spikes: needs hands-on verification (flag semantics are version-dependent; docs say `--bare` will become the `-p` default in a future release, so pin and assert at run start rather than trusting defaults).
- Phase 2: standard patterns; the only risk is stub fidelity, handled by golden evidence strings.
- Phase 4 wave D (rows 10 and 11): likely needs row-specific investigation. The NUL `-z` status form has never executed under the headless policy because output redirection needs approval; this may be a skill-versus-policy finding, not a harness bug, and the harness must report it rather than hide it.
- Row 7: environment-sensitive (`chmod` ineffective for root or unusual mounts).

## Anti-Patterns

### Anti-Pattern 1: Fault flags inside the stub
**What people do:** Add `STUB_FAIL_UPDATE=1`, `STUB_CONFLICT=2` and similar.
**Why it's wrong:** The skill then runs against a script that lies on demand; the conflict row proves nothing about the hash guard, and the stub drifts from the interface it claims to implement.
**Do this instead:** Compose faults outside (Pattern 1).

### Anti-Pattern 2: Whole-wrapper allowlist entry
**What people do:** Allow `Bash(<wrapper>:*)`, as the accepted row 1 allowlist did.
**Why it's wrong:** It also allows `bind`, `init`, `create`, which the skill must never run, and it makes "the model attempted a forbidden verb" undetectable by refusal.
**Do this instead:** Per-verb entries from a named profile.

### Anti-Pattern 3: Sanitizing before measuring, or measuring the sanitized text
**What people do:** Rewrite paths in place and count bytes afterwards.
**Why it's wrong:** Token lengths differ from real path lengths, so caps appear to pass or fail wrongly.
**Do this instead:** Measure originals in the run root, file copies only.

### Anti-Pattern 4: Reusing or clearing a run root
**What people do:** Rerun into the same directory after a failed setup, or `rm -rf` the previous root.
**Why it's wrong:** Violates the project rule (never delete or overwrite an existing run root) and mixes stale state with new evidence.
**Do this instead:** Exclusive creation; mark failed roots `ABANDONED`; new root per attempt. Failed first passes are kept beside the rerun with a `-first-pass` suffix and never relabelled.

### Anti-Pattern 5: Letting the harness declare PASS
**What people do:** Print a green summary and file it.
**Why it's wrong:** Model-behavior claims (routing, claim integrity) need review; an automated PASS invites exactly the evidence-integrity failures row 7 recorded.
**Do this instead:** Mechanical checks plus `Reviewer verdict: PENDING`.

### Anti-Pattern 6: Trusting the model's own measurements or the allowlist's intent
**What people do:** Accept "3,494 of 4,096 bytes" from the reply, or assume the allowlist matches the prescribed command.
**Why it's wrong:** Defect D1 (5 of 12 runs) and the allowlist defect both happened.
**Do this instead:** Independent measurer; policy probe before the matrix; record refusals per row.

### Anti-Pattern 7: Regexing sanitization rules from literals in the repo
**What people do:** Commit a rules file containing the real home path, login name or hostname.
**Why it's wrong:** The rules file itself becomes the leak, in a repo that is going public.
**Do this instead:** Build rules at run time from `$HOME`, the login name, the host name and the run values; commit only generic patterns and token names.

## Integration Points

### External services

| Service | Integration pattern | Notes |
|---------|---------------------|-------|
| Claude Code CLI (2.1.304 in accepted evidence; 2.1.306 installed now) | `claude -p`, `--output-format stream-json --verbose`, `--setting-sources`, `--settings`, `--session-id`, `--resume`, `--allowedTools`, `--tools`, `--disallowedTools`, `--permission-mode`, `--add-dir`, `--max-turns`, `--max-budget-usd` | Record `--version` and the model id per run. Replace the binary through one environment variable for the fake-claude tests. Stream shape: `system/init` first, assistant `tool_use` blocks and user `tool_result` blocks paired by id, `permission_denied` system messages, final `result` with usage and a denial list (MEDIUM: from docs, confirm in S2) |
| Authentication | Existing login for default mode; token or API key for strict mode | `ANTHROPIC_API_KEY` always wins in `-p` when present, so strict mode must set exactly one method deliberately and record which (not the value) |
| git | Read-only for the model; harness-side `git init`, `worktree add`, `checkout --detach` with fixed identity and dates | Deterministic HEAD makes snapshots comparable run to run |

### Internal boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Orchestrator ↔ row spec | Data file plus optional hook function | Rows never import engine internals other than a small hook API |
| Orchestrator ↔ stub | Subprocess, setup verbs only | The model never reaches setup verbs |
| Wrapper ↔ stub | `exec`-style delegation | Wrapper holds the only copy of fault state (`armed`, `target-section`, `writer2.session`) |
| Extractor / measurer / checks ↔ files | Read run-root files; write staging | One-way; no component edits a prior stage's output |
| Sanitizer → leak gate → filer | Staging directory | Filer accepts only files that carry the gate's pass marker |
| Comparer ↔ evidence | Read-only on both folders | Structural comparison only |

## Cost and Scale

| Concern | One row | Full matrix (3 layouts + 12 rows, 17 folders counting a/b/c variants) |
|---------|---------|-----------------------------------------------------------------------|
| Model turns | 2 to 5 `claude -p` processes (s1, s2, optional s3..s5) | Roughly 40 to 70 processes; exact token cost is UNCONFIRMED until the skeleton reports usage by category |
| Wall time | Minutes | Sequential by default; rows are independent (own root, `CKPT_HOME`, session ids), so a `--jobs` option is possible later, limited by API rate limits, not by isolation |
| Disk | Tens of megabytes of raw stream plus snapshots in the private run root | Evidence in the repo stays small because raw streams are not filed |
| Nondeterminism | A rerun reproduces the evidence format and the objective facts, not the model's prose | Compare shapes (call sequence, exit codes, byte tables, hashes of unchanged files), never text |

First bottleneck: token cost per row, controlled by `--max-turns`, `--max-budget-usd` and running one row at a time while building. Second: reviewer time, reduced by the generated fact table.

## Pitfalls Specific to the Architecture

1. **Physical versus logical project path** (macOS temp symlink) turns every backend row into a silent no-op. Mitigation in Isolation Boundaries.
2. **Default flips in Claude Code** (`--bare` default for `-p` announced; `-p` permission default changed in 2.1.302). Mitigation: pass every behavior flag explicitly and assert `system/init` contents at the start of each stage.
3. **User-level instruction leakage** (UNCONFIRMED). Mitigation: spike S1, strict mode, `isolation-mode.txt` in every row.
4. **Compound shell commands** are refused by the headless policy ("contains multiple operations", brace and quote obfuscation rules). These are harness policy events the model works around; count them per row, do not tune the allowlist to hide them silently, and keep the earlier practice of reporting them.
5. **Root or permissive filesystems** make `chmod` rows pass vacuously; preflight must prove denial before the model runs.
6. **Windows** is out of scope for this milestone (Bash shims, `chmod`, `realpath`); state it in the harness README.
7. **Stub fidelity drift**: the only defense is the conformance suite built from evidence strings, plus an optional mode where bokiko can point `PRECLEAR_HELPER` at the real helper on a machine that has it, run the same suite, and compare shapes (not hashes). That keeps the real helper private and still gives the stub an independent check.

## Open Questions

- Is user-level instruction loading really excluded by `--setting-sources project,local`? (S1.) The strict-mode design is ready if not.
- Does `--restricted` load project `CLAUDE.md` and project skills? If yes it may replace several allowlist and add-dir mechanisms; if no, ignore it.
- Are Glob and Grep present in the old runs' tool set? Accepted `tools.txt` lists them in `--allowedTools`, but current docs say they are not in the default `--tools` set on macOS and Linux. Pinning `--tools` is a deliberate delta from the accepted harness and must be written in each README.
- Exact `handoff` and `note` output of the real helper (no committed run exercised them).
- Whether the `-z` NUL status form can ever run under the headless policy (redirection needs approval); this decides whether row 10 can pass the exact-command test or stays a disclosed exception.
- Total token cost of one full matrix.

## Sources

- `tests/acceptance.md` (harness rules, layouts, matrix order) - HIGH
- `references/checkpoint-v1.md` (interface table, exit codes, flow, failure handling) - HIGH
- `tests/evidence/publication-2026-10-20/` READMEs, `tools.txt`, wrapper scripts, `wrapper-calls.log`, `fixture-CLAUDE.md`, `snap-*/sha.txt`, `measurements.txt`, `s2-preclear-full-trace.md` (previous harness behavior, helper output strings, state file names) - HIGH
- `tests/evidence/bound-ledger-2026-10-19-rerun/conflict/` (conflict file format, injector behavior) - HIGH
- `tests/fixtures/` (bound-ledger ledger without block markers; placeholder project path in `CLAUDE.md`; `runtime-settings.example.json`) - HIGH
- `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/TESTING.md` - HIGH
- Claude Code documentation, "Run Claude Code programmatically" (headless): permission behavior in `-p`, `--permission-prompts none`, `permission_denied` stream events, stream-json message shapes, `--bare` semantics and planned default - MEDIUM (official docs, fetched 2026-10-21)
- Claude Code documentation, CLI reference: `--setting-sources`, `--settings`, `--session-id`, `--no-session-persistence`, `--tools` default set, `--restricted`, `--safe-mode`, `--max-budget-usd`, `--max-turns` - MEDIUM (official docs, fetched 2026-10-21)
- Claude Code documentation, environment variables: `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY` precedence in `-p`, `CLAUDE_CODE_DISABLE_CLAUDE_MDS` - MEDIUM (page truncated; `CLAUDE_CODE_SESSION_ID` row not seen, so its behavior rests on the accepted evidence where the helper identified bound sessions)
- `claude --help` and `claude --version` on the local machine (2.1.306) - HIGH for flag existence

---
*Architecture research for: headless acceptance harness for the preclear skill*
*Researched: 2026-10-21*
