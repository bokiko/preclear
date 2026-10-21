# Pitfalls Research

**Domain:** Taking a formerly private Claude Code skill repository public, and committing a reproducible headless test harness (with a stub helper) around a non-deterministic LLM agent
**Researched:** 2026-10-21
**Confidence:** HIGH for Claude Code headless/permission behaviour and GitHub visibility/history behaviour (official docs fetched 2026-10-21, Claude Code 2.1.30x era); MEDIUM for flakiness practice (secondary sources) and stub-fidelity analysis (derived from this repo's own contract and evidence, not an external reference)

Scope notes:

- Findings are tagged with the repository facts that make them real (checked read-only against tracked files and `git log`; the gitignored `runs/` folder was not read).
- This document is itself public once the repo flips. It therefore contains no home paths, hostnames, addresses or email, and refers to the owner only as bokiko.
- "Phase" names below are work-stream labels (Publication gate, Harness extraction, Stub helper, Matrix rerun, Visibility flip). The roadmapper maps them to numbers.

---

## Critical Pitfalls

### Pitfall 1: Rewriting history reflexively for a low-severity finding (or not rewriting when it matters), and doing it twice

**What goes wrong:**
Three audit items (home paths in d437af2, public author identity, the row 7 defect) get handled as separate chores. A history rewrite for the path lines, then a second one for the author email, changes every commit hash twice. Every SHA cited in prose (`PROJECT.md` cites d437af2; the changelog, evidence READMEs and `CONCERNS.md` cite commits) goes stale. Or the opposite: the paths are left because "it's only a path" without checking what the path actually contains.

**Why it happens:**
The audit labels the finding "medium" without stating what the exposed string reveals. A home-folder path whose user segment is the already-public handle reveals almost nothing; one containing a real name or an employer-specific folder reveals a lot. Rewriting is also a hard-rule action (needs bokiko's explicit word), so it gets deferred and then bundled badly.

**How to avoid:**
1. Read the ten affected lines first and classify the exposed string (public handle only, vs real name, vs private project names). Decide accept or rewrite on that evidence, and record the decision and reason in `PROJECT.md` Key Decisions.
2. Decide the three open items together, then do at most one rewrite pass covering both paths and author identity (`git filter-repo` with `--replace-text` and `--mailmap`/`--email-callback`; use a version that supports `--sensitive-data-removal` (2.47 or later), which GitHub's own guidance recommends).
3. Rewrite only on a fresh mirror clone, keep a `git bundle` of the pre-rewrite state outside the repo, run the full scan (Pitfall 3) against `--all` before pushing, and push once. After a push the rewrite is effectively irreversible.
4. Do it while the repo is still private. The old SHAs stay reachable on GitHub servers until garbage collection; GitHub Support removes cached views and dangling commits, but only for genuinely sensitive data ("GitHub Support won't remove non-sensitive data"). A path with only the handle will not qualify, so for that class the honest option is to accept it, not to rewrite and then ask Support.
5. After any rewrite, grep the docs for stale 7-40 hex strings and update the citations; evidence folders themselves are never edited (constraint: historical evidence is preserved), only the prose that points at commits, and that edit is itself a new commit.

**Warning signs:**
`git log --all --format='%h'` differs from SHAs in `CHANGELOG.md` / `PROJECT.md` / evidence READMEs; two separate "rewrite" tasks in the plan; a rewrite task with no stated exposure; a rewrite proposed after the visibility flip.

**Phase to address:** Publication gate (decision + single rewrite, before any visibility change).

---

### Pitfall 2: Author identity is in commit metadata, so tree scans never see it, and every new commit adds more

**What goes wrong:**
All 11 existing commits carry the same personal mailbox address as both author and committer, and the repo-local git config still uses it. A tree or content scan finds nothing (`git grep` for the address returns no files), so the audit says "clean". After the flip the address is permanently public via `git log`, and also harvestable from the GitHub API. Every commit made afterward (harness commits, GSD automation commits, evidence commits) repeats it, so a late fix needs another rewrite.

**Why it happens:**
Scanners such as gitleaks look for secrets in content, not for personal identifiers in metadata. `.mailmap` only changes how a local `git log`/`shortlog` displays names; it does not change stored commits or what GitHub shows. Enabling GitHub's "keep my email private" only affects web-based operations: local command-line commits use the local git config (GitHub docs, confirmed).

**How to avoid:**
1. bokiko decides the public identity explicitly (handle plus GitHub noreply address, or the current address knowingly). Record it.
2. Set it in the repo-local config before any further commit (`user.email` to the noreply form, optionally `user.useConfigOnly=true` so a missing config fails instead of falling back to a global address), and enable GitHub's "Block command line pushes that expose my email" account setting so a wrong identity is rejected at push time (setting exists; docs page fetched did not describe it, so verify in the account UI).
3. Include the identity change in the single rewrite pass from Pitfall 1 if the decision is to hide the old address; rewrite both author and committer fields.
4. Add a pre-push check: `git log origin/main..HEAD --format='%ae %ce'` must contain only the approved identity.
5. Remember tooling that commits for you (GSD workflows, hooks). The project constraint is "authored solely by bokiko, no AI attribution lines"; verify trailers with `git log --format=%B | grep -i -E 'co-authored|generated with'` before the flip and before every later push.

**Warning signs:**
`git log --all --format='%an|%ae|%cn|%ce' | sort -u` shows an address the owner has not approved; new commits after the decision still show it; a rewrite that fixed authors but not committers.

**Phase to address:** Publication gate (decide, set config, rewrite); re-checked by the pre-push gate in every later phase.

---

### Pitfall 3: The leak scan covers the tree and secrets, but the real leak surface is evidence files, sanitizer gaps, and everything added after the audit

**What goes wrong:**
The 2026-10-20 audit passed, and then new material arrives that was never scanned: harness scripts, fresh evidence, stub, and `.planning/` files. The `.gitignore` carve-out `!tests/evidence/**/*.log` means any new log under evidence is tracked automatically. Raw `.err`, `.out`, `session.id` and settings JSON already live in evidence folders. Committed evidence is post-processed with token replacement (`<run>`, `<home>`, `<repo>`), which is pattern-based and lossy.

**Why it happens:**
Sanitization by string replacement only covers path shapes seen so far. New leak shapes come from: another machine or OS (Linux home paths, Windows paths), symlink-resolved forms (macOS `/private/var/...` vs `/var/...`), the path-derived project slug Claude Code uses for its own storage (a home path with separators turned into dashes appears in transcript and memory directories and is not matched by a slash-based pattern), URL-encoded paths, `~`-relative forms, hostnames in stderr, session UUIDs, and the owner's tool paths. A one-time audit also does not protect later commits.

**How to avoid:**
1. Build the deny-list at runtime from the machine, not from memory: `$HOME` (raw, realpath, dash-slug form, URL-encoded), `$USER`, `hostname` (short and FQDN), git email, `$TMPDIR` realpath, `mktemp` root. The harness fails closed if any of them appears in a file about to be written under `tests/evidence/`.
2. Sanitize at write time inside the harness, after the independent byte measurement is taken on originals (the existing rule), and keep originals only in the gitignored run root.
3. Run gitleaks (already installed locally) with a custom rule file for the personal identifiers above, over the working tree and over `git log -p --all`. Make it a pre-commit and pre-push hook, because there is no CI (out of scope) to catch anything.
4. Scan a fresh `git clone --mirror` of the remote, not the working copy; the local clone can differ from what GitHub holds (extra refs, previously pushed branches).
5. Treat the repo-wide allow of `*.log` under evidence as a risk: keep it, but scan every new log before staging, or narrow it to named files.
6. Decide about session UUIDs in evidence (154 occurrences). They are not credentials, but they identify transcripts; accept explicitly or normalize them in new evidence.

**Warning signs:**
A stranger-contributed or second-machine run produces evidence containing a path shape the sanitizer does not tokenize; `git grep -c` for the home-slug form is non-zero; sanitized files differ by token style between old and new evidence.

**Phase to address:** Publication gate (scan the existing repo, install hooks); Harness extraction (runtime deny-list in the sanitizer); every later phase (hooks stay on).

---

### Pitfall 4: Allowlist patterns that silently do not match, so the model "works around" the denial and the row tests a different path

**What goes wrong:**
This already happened: `Bash(git status:*)` did not match `git --no-optional-locks status`, so the skill's exact status command was refused until rows 10 and 11 were rerun. Earlier accepted layouts used a declared fallback. The row passes, but it is not testing the command the skill prescribes.

**Why it happens (verified in the official permission docs):**
- A Bash rule matches the whole command text, with `*` as wildcard. `:*` is only recognised at the end of a pattern and is equivalent to a trailing ` *`; elsewhere the colon is literal.
- `git status *` matches commands that start with `git status`; a global option between `git` and the subcommand breaks the match.
- Compound commands are split on `&&`, `||`, `;`, `|`, `|&`, `&` and newlines, and every subcommand must match independently. The model's habit of chaining commands produces refusals ("contains multiple operations") that look like harness events but change the call sequence.
- Only a fixed list of wrappers (`timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob`) is stripped; `env`, `npx`, `sh -c` and path-qualified programs are not.
- Output redirection (`> file`) is checked against Edit rules and working directories separately, which is why the NUL `-z` sidecar form never executed headless.
- Patterns that constrain arguments are documented as fragile.

**How to avoid:**
1. Derive the allowlist from observed reality: extract every distinct Bash command string from the existing full traces and keep them as a committed `expected-commands` table (exact text, which row, allow or deny). Review the table against the skill text, not the other way round.
2. Make unexpected denial a first-class failure. Parse the `result` message's `permission_denials` list and `permission_denied` system events from `stream-json`. A row fails unless every denial is one the row is designed to produce (rows 3b, 7). Report refusal counts per row (already done manually).
3. Add a harness self-test per pattern: a tiny headless "run exactly this command" canary, or at minimum a golden test over saved `stream-json` excerpts. Run it whenever the Claude Code version or allowlist changes.
4. Note that read-only git forms are in Claude Code's built-in no-prompt set, so some patterns may be unnecessary and some denials may come from the exact flag form. Test each form on the pinned version instead of assuming.
5. Do not widen the allowlist to make a row go green without recording that the new baseline differs from the 2026-10-20 evidence.

**Warning signs:**
A row passes while its trace shows the model using a different command form than `SKILL.md` prescribes; refusal counts that are non-zero in rows not designed to deny; stderr containing permission warnings; a matrix that passes in a clean clone but with fewer tool calls than the committed evidence.

**Phase to address:** Harness extraction (expected-commands table, denial parser); Matrix rerun (verify on the pinned version).

---

### Pitfall 5: Project allow rules are ignored in headless mode, so a stranger's clone silently runs with no permissions

**What goes wrong:**
`permissions.allow` rules in a project's `.claude/settings.json` are applied only after the workspace trust dialog is accepted. `claude -p` never shows that dialog and does not count it as accepted, so those rules are not used; Claude Code prints a "this workspace has not been trusted" warning to stderr and carries on. If the committed harness (or a committed fixture settings file) relies on project-level allow rules, every stranger's run starts with Bash denied. The same run on the owner's machine works because trust was accepted earlier in an interactive session. Reverse risk: hooks, the `env` block and `.mcp.json` servers in the project run without any prompt in `-p`.

**Why it happens:**
The author's machine has accumulated trust state and local settings that a clean clone does not.

**How to avoid:**
1. Deliver the allowlist on the command line (`--allowedTools`) or with `--settings` (command-line tier, above file tiers), or via an untracked `.claude/settings.local.json` written by the harness into the throwaway fixture. Never rely on a committed `.claude/settings.json` for allow rules. Deny and ask rules are unaffected by trust.
2. Treat any stderr containing "has not been trusted" as a setup failure for the row, not a warning.
3. Do not place hooks or MCP config in fixtures unless the row is about them; headless runs execute them untrusted.
4. In the clean-clone acceptance run, use a fresh path that has never been trusted, on purpose.

**Warning signs:**
First tool call of the first row is denied; the stranger-run trace has zero successful Bash calls; stderr file non-empty with trust wording; row results differ between "my machine" and "fresh clone" with identical scripts.

**Phase to address:** Harness extraction (how the allowlist is delivered); Matrix rerun (clean-clone run catches it).

---

### Pitfall 6: Environment contamination makes the run depend on the person running it

**What goes wrong:**
`--setting-sources project,local` excludes user settings files but the run can still be influenced by: a personal `preclear` skill of the same name (shadowing, noted in the README), user-level memory/CLAUDE.md, user plugins and hooks, installed MCP servers, and user-level auto-memory (the harness pins `autoMemoryDirectory` per run for this reason). A stranger with a SessionStart hook or a different plugin set gets different behaviour; the owner's ledger-protecting hook layer is a particular risk because it blocks writes the stub-backed rows expect to succeed.

**Why it happens:**
No single flag gives "clean room while still testing the project skill":
- `--bare` skips CLAUDE.md, skills, hooks, plugins, MCP and auto-memory discovery and is documented as the recommended scripted mode (and "will become the default for `-p` in a future release"), but it also drops system reminders and the skill list and does not use subscription login (API key required). It changes the behaviour under test, and project skills are not discovered unless supplied through `--add-dir`.
- `--safe-mode` disables CLAUDE.md and skills too, which defeats a skill test.
- `--restricted` removes command-running tools, which defeats this matrix.

**How to avoid:**
1. Decide explicitly and write down which isolation level the matrix claims. Do not silently switch to `--bare` in a "cleanup" change; that creates a new baseline (new evidence folders).
2. Record the `system/init` event for every run (model, tools, MCP servers, plugins, loaded skills, plugin errors) and assert it against an expected manifest: only the fixture skill, no unexpected MCP servers, no hook events other than expected. `hook_started`/`hook_response` events for SessionStart are always emitted, so unexpected hooks are visible.
3. Confirm from the transcript which skill text loaded and compare its sha256 to `digests.txt` (the existing acceptance rule), failing the row on mismatch.
4. Probe whether pointing `CLAUDE_CONFIG_DIR` at an empty scratch directory is viable on both macOS and Linux with subscription and API-key auth before promising it (credential lookup may be keyed to the config directory; unverified). Until verified, document the contamination risk and rely on the init-manifest assertion.
5. Run the clean-clone acceptance with the owner's own helper unreachable (not on PATH, not at the configured path) and assert from `wrapper-calls.log` that every delegated call hit the stub.

**Warning signs:**
`system/init` lists skills, plugins or MCP servers not in the manifest; the loaded skill digest differs from `digests.txt`; the same fixture behaves differently on two accounts.

**Phase to address:** Harness extraction (init manifest assertion); Matrix rerun (clean environment run); research flag for the `CLAUDE_CONFIG_DIR` probe.

---

### Pitfall 7: Version and default drift in the Claude Code CLI

**What goes wrong:**
All evidence ran on one version (2.1.304). The CLI auto-updates and ships often. Defaults the harness may be relying on are documented as changing: from 2.1.302 a `-p` run with nothing setting a permission mode starts in Manual mode (earlier behaviour differed), `--bare` is planned to become the default for `-p`, `--permission-prompts` exists only from 2.1.259, `--forward-subagent-text` and several stream-json fields have minimum versions. A stranger on a newer or older version gets different tool policy, different loaded context, different refusal wording, or an unknown-option error before any model call.

**How to avoid:**
1. Pass every behaviour-relevant knob explicitly: `--permission-mode`, `--setting-sources`, `--model` (full model ID, not an alias, because aliases move), `--effort`, `--output-format stream-json --verbose`, and `--permission-prompts none` only if the baseline used it. Leave `--fallback-model` unset so a silent model swap cannot occur.
2. Record `claude --version` and the model reported in the result (`modelUsage`) in every run folder; abort with a clear message when the version is not in the tested list unless the user passes an explicit `--allow-version-drift`, in which case the evidence folder is labelled "drift run".
3. Keep a "tested versions" table in `tests/` and document pinning (`claude install <version>`; disabling the auto-updater via the supported setting or environment variable, which should be verified against current docs when written).
4. Preflight each flag the harness uses (`claude --help` is not exhaustive; test with a harmless call) and give a one-line actionable error.
5. Do not compare a drift run against old evidence row-for-row; compare invariants (Pitfall 8) and report version in the table.

**Warning signs:**
The first run after a CLI update changes refusal counts or tool-call counts; an "unknown option" error; stream-json fields the parser expects are absent; `permission_denied` events appear where none were seen before.

**Phase to address:** Harness extraction (explicit flags, version gate); Matrix rerun (record versions); ongoing maintenance note in the README.

---

### Pitfall 8: Judging a stochastic agent with single runs and with the model's own claims

**What goes wrong:**
A 12-row matrix with 1 run per row will occasionally fail or pass by chance, and "rerun until green" turns a flaky pass into acceptance evidence. The skill already shows this: the model's own cap statements disagreed with the independent manifest in 5 of 12 runs (D1), and row 7's claimed registry check had no supporting tool call. A single clean row 7 rerun does not show the defect is fixed.

**Why it happens:**
Model sampling is stochastic and multi-step workflows compound variance; environment state and timeouts add to it. Reliability literature separates "can succeed sometimes" (pass@k) from "succeeds every time" (pass^k); a gate built on average pass rate cannot tell those apart. (MEDIUM confidence: secondary sources.)

**How to avoid:**
1. Split every assertion into two classes in the acceptance doc:
   - Mechanical invariants (must hold on every run, checked from files and call logs, never from model text): zero writes on fresh resume, frozen handoff hash unchanged, helper call sequence and exit codes, no git mutation (tree hashes and `git status` before/after), no write outside the run root, stop after first denied helper mutation, byte caps from the independent manifest.
   - Behavioural content (judged, may vary): wording, ordering, which supported entries appear.
2. For gating rows (row 7 and the carried-forward rows 1, 2, 3c, 4b) run n of at least 3 and require the mechanical invariants in all n. Report the count (3 of 3), not just "passed". Keep failed attempts as evidence folders; never delete or overwrite them.
3. Replace "model said it measured" with the harness's own measurement; for Do-not-redo entries, emit a review table listing each entry next to the tool calls made in that turn so a reviewer (and later a script) can confirm each is supported.
4. Compare reruns to old evidence by invariants and table shape, not by text diff.
5. Pin model ID and effort level; sampling temperature is not exposed by the CLI, so variance cannot be removed, only measured.

**Warning signs:**
A verdict resting on one trace; a "fix" commit that coincides with one lucky rerun; assertions that grep the final reply for words; rows that pass only when the model volunteers a measurement.

**Phase to address:** Harness extraction (assertion classes); Matrix rerun (n of at least 3 on gating rows, row 7).

---

### Pitfall 9: Refusal and outcome detection by substring

**What goes wrong:**
Detecting a denial by searching the reply for "permission", "denied" or "not allowed" misses rewordings across versions and the model's own paraphrase, so a missed refusal reads as "no refusal happened". It can also false-positive on fixture content that contains those words.

**How to avoid:**
1. Use structured signals only: `permission_denied` system messages and the final `permission_denials` list in `stream-json`, tool_result error flags, process exit codes, and the helper's own logged exit codes.
2. Fail closed: if the stream does not parse, if no final `result` message exists, or if an unrecognised message shape appears, the row is an error, not a pass. Distinguish "model stopped" from "harness killed the run" (SIGTERM yields exit 143 and records no result for the in-progress turn; use SIGINT for a graceful stop).
3. Keep golden `stream-json` excerpts from the pinned version under `tests/` and unit-test the parser against them with zero model calls.
4. Keep a separate counter for tool-policy refusals of compound commands versus helper denials (the README already requires this).

**Warning signs:**
A row passes with an empty denial list in a case designed to deny; parser code with `grep -i` on the reply; different results after a CLI update with no skill change.

**Phase to address:** Harness extraction.

---

### Pitfall 10: Instrumentation that fires on Claude Code's own calls

**What goes wrong:**
Row 11's first pass was not exercised because the logging/trigger wrapper fired on Claude Code's own startup git call (the git status snapshot taken at session start), consuming the "concurrent change" trigger before the model acted. The same applies to the logging wrapper's counts and to any "n-th call" fault injection.

**How to avoid:**
1. Attribute every wrapped call to a model tool call: correlate wrapper log timestamps and argv with `tool_use` ids from the stream; classify unmatched calls as startup noise and report their count.
2. Fire triggers on the n-th model-initiated call matching an exact argv pattern, not on the first call of a program.
3. Write the wrapper's own self-test: start a session with a no-op prompt and assert the wrapper logged only startup calls and the trigger did not fire.
4. Do not disable the startup git snapshot (`includeGitInstructions`) just to quiet the wrapper; that changes the system prompt and therefore the behaviour being tested.

**Warning signs:**
A trigger that fires with zero model tool calls in the trace; wrapper log entries before the first assistant message; row 11 reports "not exercised".

**Phase to address:** Harness extraction.

---

### Pitfall 11: Destructive cleanup and fragile shell scaffolding in the harness itself

**What goes wrong:**
A `rm -rf` on a deterministic run root has already been hit. Related failures: `set -e` aborting on an expected non-zero exit (row 3c died three times this way: a skipped bind, a non-zero `status` for an unbound session, a missing bindings folder); unquoted variable expansion; a hostile-filename fixture (row 10) executed as shell by the harness.

**How to avoid:**
1. Exclusive creation only: `mkdir` (no `-p`) on a name containing a timestamp and random suffix, abort if it exists. No harness code path calls `rm -r`; cleanup is a printed instruction for bokiko, never an action (matches the project constraint).
2. Validate the run root before use: absolute, under a configured runs base, not `/`, not the home directory, not the repo root, contains no `.git`. Use `${VAR:?}` for required variables, `set -u`, and quote everything.
3. Capture expected non-zero exits explicitly (`cmd; rc=$?`) and record them as annotations kept separate from model output (existing rule), instead of globally relying on `set -e`.
4. Generate hostile fixtures (newline, quote, leading-dash, unicode, case-colliding names) at run time from Python, not shell; never commit them (some filesystems and Windows cannot check them out). Run shellcheck in the pre-commit hook.
5. Give every `claude -p` call a wall-clock timeout (macOS lacks `timeout` by default; `gtimeout` or a Python wrapper) because a headless run can wait on background work for up to 10 minutes by default.

**Warning signs:**
Any `rm` in a script; a run that "resumes" into an old root; drivers that exit mid-setup with no row output; hostile names appearing in a shell history.

**Phase to address:** Harness extraction.

---

### Pitfall 12: Snapshot manifests and portability assumptions (filenames, filesystems, tool flavours)

**What goes wrong:**
Manifests split filenames at newlines before the `-print0` fix; the same class of bug returns elsewhere. The harness was built on macOS: BSD `stat`/`sed -i`/`readlink`/`shasum` flags differ from GNU, bash 3.2 lacks `mapfile`, the default macOS filesystem is case-insensitive (a `Name` / `name` hostile pair collides) and may normalise unicode differently from Linux, `sort` order depends on locale, and tmp paths are symlinked (`/var` to `/private/var`). A Linux stranger gets different manifests; a hash mismatch looks like a skill defect.

**How to avoid:**
1. Write manifest, hashing, measurement and sanitizer logic in Python 3 standard library (the harness already has `pub-file.py` and `pub-measure.py`), NUL-delimited internally, byte-sorted, with `os.fsencode` for names; keep shell for orchestration only.
2. Add a model-free self-test that builds the hostile fixture, takes a manifest twice, and asserts determinism and round-trip of every name. This test costs zero tokens and should run before any paid row.
3. Resolve `realpath` for all roots before comparing or sanitizing.
4. Declare supported platforms (macOS, Linux; Windows only via WSL) in the harness README and fail early otherwise.
5. Run the clean-clone acceptance on a second OS if one is available; that is the cheapest portability test.

**Warning signs:**
Manifest counts that differ between two runs of the same fixture; files named with `\n` shown as two lines; BSD/GNU flag errors on a second machine.

**Phase to address:** Harness extraction (Python core, self-tests); Matrix rerun (second-OS run).

---

### Pitfall 13: Stub helper that is circular, incomplete, or too lenient, so backend rows stop testing the real branches

**What goes wrong:**
The adapter and the stub are written from the same document (`references/checkpoint-v1.md`), so agreement proves only self-consistency. The document is also an incomplete specification for a helper:

- It does not define how `section-hash` is computed, the `.conflict-*` file naming and content, the registry/bindings store the harness isolates with `CKPT_HOME`, `bind`/`create`/`init` (needed by harness setup though the skill never calls them), session-id resolution, `lint` scanning all registered ledgers, `handoff` immutability, or lock behaviour (exit 6) and the kill switch (exit 5).
- It states the interface was verified against one private build and that non-matching output "is a failure, never a success", so the stub must reproduce the exact formats (`session <id8> → <ledger>`, `checkpoint: NONE`, `ledger lint OK`, the `## <name>` plus `section-hash:` layout) byte for byte.
- A too-lenient stub accepts blocks the real helper rejects (exactly six sections and no others, rendered block at most 4,096 bytes including markers and headings, Authorization boundaries non-empty and at most 600 characters), so exits 2 and 4 are never exercised. A too-strict stub fails branches the real helper passes.
- The real setup has a hook that blocks direct ledger edits; the stub environment does not, so any row that relied on that hook for denial cannot be reproduced the same way.

**Why it happens:**
The stub is treated as a mock of an interface rather than as a reimplementation of behaviour, and nobody checks it against recorded real behaviour.

**How to avoid:**
1. Conformance by replay, with zero model tokens: parse every committed `wrapper-calls.log` (argv, exit code) and the traces' decisive helper outputs from existing evidence (rows 1, 2, 3b, 4b and the bound-ledger folders), replay the argv sequences against the stub in a scratch registry, and assert the same exit codes and output shapes. This is the only external ground truth available without publishing the private helper.
2. Write an explicit branch table (status bound/unbound/NONE; show; validate pass/exit 2/exit 4; update ok/exit 3; second conflict leading to UNSTABLE; denied write; lint ok/warning for other ledger; handoff) and assert the rerun matrix exercised each branch with the stub, using the wrapper logs. This is the acceptance criterion "exercise the same branches".
3. Implement conflict injection in a way that goes through the same wrapper path as before (the counting wrapper), or document and test the change. Fault injection built into the stub is fine for exits 5 and 6 only if labelled.
4. Name and brand it as a stub: a distinct executable name, a banner on `--version`, its sha256 in `digests.txt`, evidence folders labelled "stub-backed", and a README line that stub results are not real-helper results.
5. Build it from the public contract and the committed evidence, never from the private helper's source (the private project has its own audit; copying behaviour verbatim risks leaking it and contradicts the out-of-scope decision).
6. Use Python 3 standard library or POSIX shell only; a Node dependency that strangers lack breaks the "clone and run" promise.
7. Keep stub documentation under `tests/`. Editing `references/checkpoint-v1.md` (for example to remove the reference to the private build path or to mention the stub) changes the adapter digest, invalidates every carried-forward row, and counts as a skill change, which the milestone forbids unless a defect demands it. If wording in `references/` must change before publication, do it deliberately and rerun affected rows.

**Warning signs:**
The stub passes its own tests but fails replay of recorded logs; no backend row ever produces exit 2 or 4; `lint` always passes; the stub README says "implements checkpoint-v1" without a version or caveat; stub-backed and real-helper evidence are described as equivalent.

**Phase to address:** Stub helper (replay conformance, branch table); Matrix rerun (branch coverage report). Research flag: mining existing logs for the observable contract before writing the stub.

---

### Pitfall 14: Token cost surprises and unbounded runs for strangers

**What goes wrong:**
The matrix is about two dozen evidence folders, each with at least two model turns plus a fresh-session resume, each turn possibly dozens of tool calls. A newcomer runs "all rows" on a subscription (burning rate limits) or an API key (real money), a mis-set allowlist makes the model retry endlessly, or a hang waits on background work. There is no CI to cap this, and the milestone adds repetition (n of at least 3) on gating rows.

**How to avoid:**
1. Report cost before spending: take actual `total_cost_usd` and token-by-category figures from the existing evidence result lines, put a measured per-row and per-matrix estimate in the harness README, and print the worst-case from the caps at start. Both figures are client-side estimates, not billing.
2. Hard caps on every call: `--max-turns` and `--max-budget-usd` (spend can pass the cap, so leave headroom) and the per-turn wall-clock timeout.
3. Default to a no-model self-test and a single smoke row; require an explicit `--rows` list or `--all` plus a confirmation that prints the estimate. Never run the full matrix by default.
4. A `--dry-run` that does all setup, fixture generation, wrapper/stub wiring, manifests and sanitizer on a canned transcript, so most harness bugs surface at zero cost.
5. Use `--no-session-persistence` only for turns that are not resumed later; the matrix needs persisted sessions for turn 2 and resume checks.
6. Keep CI out of scope as decided; add a README note that wiring this into CI needs an API key secret and spends tokens per run.

**Warning signs:**
No cost figure anywhere in the harness output; the first stranger issue is "it used my whole quota"; runs longer than the timeout; retries visible in `api_retry` events.

**Phase to address:** Harness extraction (caps, dry run, cost printout); Matrix rerun (record actual spend per row).

---

### Pitfall 15: "Done" proven on the owner's machine instead of from a clean clone

**What goes wrong:**
The rerun passes because of leftovers: the gitignored `runs/` folder, trusted-workspace state, an existing helper on PATH, exported `CKPT_HOME`, a personal skill, cached auth for a specific config directory. The success criterion says "from a clean clone", but the clone happens next to all of it.

**How to avoid:**
1. Clone to a new path that has never been used with Claude Code (to hit Pitfall 5), with a minimal environment (`env -i` plus PATH, HOME, and only the variables the harness documents), no `runs/` folder, and the private helper made unreachable.
2. Assert in the output, not by eye: stub digest equals the helper digest in `digests.txt`; no call in any wrapper log targets a path outside the run root; the loaded skill digest equals the tracked file.
3. Repeat on a second machine or OS when possible.
4. Follow only the README's instructions, verbatim, copy-pasting; any step that needed unwritten knowledge becomes a README fix.

**Warning signs:**
The README says "see the other folder"; a step that works only after running another script manually; a pass that disappears when `runs/` is moved away.

**Phase to address:** Matrix rerun.

---

## Moderate Pitfalls

### Pitfall 16: Visibility flip side effects and incomplete pre-flip inventory

**What goes wrong:**
After the flip: Actions history and logs become visible, stars and watchers reset, private forks detach, push rulesets are disabled, and anyone can fork. Making the repo private again does not recall forks or clones (public forks stay public). Items forgotten: other refs on the remote (the local clone shows only `main`, but the remote may hold more), issues/PRs and their attachments, repository description, topics, wiki, releases, deploy keys, webhooks and secrets configured earlier.

**Prevention:**
Before the flip, produce a checklist from the live repo (`gh api` for refs, workflows and runs, issues, hooks, deploy keys; `git ls-remote`), clone `--mirror` and scan it (Pitfall 3), and add the missing community files (security policy, contribution note, issue templates already exist). Enable secret scanning and push protection right after (public repos get the Advanced Security features; confirm the actual toggles in the UI). The flip itself is a hard-rule action: a manual step in the plan, executed only on bokiko's explicit word in the current conversation, never inside an autonomous or auto-advance phase and never by a script default (`gh repo edit --visibility public` requires an acknowledgement flag; do not pass it on someone's behalf).

**Phase to address:** Visibility flip.

### Pitfall 17: "Publish first, harness after" makes every harness mistake public the moment it is pushed

**What goes wrong:**
With the order chosen in `PROJECT.md`, the Stub and Harness commits, first rerun evidence and any accidental path or identity leak land in public history immediately. The failures that already occurred in the harness (deletion, wrong allowlist) are now also visible in public commits; a leak there needs a rewrite of a public repo, which cannot be cleanly retracted (cloners keep copies).

**Prevention:**
Keep the order if bokiko wants it, but make the leak gates (Pitfall 3) and identity gate (Pitfall 2) mandatory for every push after the flip, work on feature branches reviewed by the scan before merging to `main`, and run first-time harness evidence output into the gitignored root and review it before copying anything into `tests/evidence/`. Put the known failing row (row 7) in the public README as an open disclosed item rather than hiding it.

**Phase to address:** Publication gate (policy), every later phase.

### Pitfall 18: `.planning/` and evidence READMEs go public with dangling or unverifiable references

**What goes wrong:**
`.planning/` is committed, so process notes become public: references to a private audit record (the evidence README says to see a private audit record before any visibility change, which a stranger cannot follow), to review-tool consultations and verdicts that cannot be independently checked, to the owner's private helper build and install location (`references/checkpoint-v1.md` names it), and GSD config. These are not secrets but they confuse readers and invite trust claims that cannot be verified.

**Prevention:**
Decide deliberately whether `.planning/` stays tracked (it is a policy choice, not an accident); rewrite or remove dangling pointers in new prose (never edit historical evidence; add an addendum or a new folder). Present verdicts as "recorded in the evidence README", not as authority. Leave `references/` as is unless a rerun follows (Pitfall 13, item 7).

**Phase to address:** Publication gate.

### Pitfall 19: Sanitized evidence is not byte-equal to harness output, so "compare row for row" is impossible by diff

**What goes wrong:**
Committed evidence contains tokens such as `<run>`, `<repo>/<run>`, `<home>`; new runs contain real paths until sanitized, plus session ids, timestamps and temp names. Comparing raw output to committed evidence always differs; comparing after sanitizing differs wherever the sanitizer version differs.

**Prevention:**
Version the sanitizer; sanitize new evidence with the same token vocabulary; compare invariants and table shapes (Pitfall 8); store the sanitizer version in each folder.

**Phase to address:** Harness extraction.

### Pitfall 20: Carry-forward rows hide staleness

**What goes wrong:**
Rows 1, 2, 3c and 4b are accepted on old skill and adapter digests; the earlier layouts used a plain-porcelain fallback and were not exact-command tests. Publishing makes "tested" claims visible to strangers. Any edit to `SKILL.md`, `references/` files, or fixtures after the rerun invalidates the claim.

**Prevention:**
Per-row evidence table with skill digest, adapter digest, Claude Code version and stub digest; refuse to mark a row "current" unless it ran on the digests in the tree at tag time; cut a tagged version at publication and record digests per version (changelog is all `[Unreleased]` today). Keep SKILL.md untouched (6 bytes of headroom under the 12,000 byte ceiling).

**Phase to address:** Matrix rerun; Publication gate (tag).

---

## Minor Pitfalls

### Pitfall 21: Missing or misleading repository metadata at flip time
License exists (MIT, handle as holder). Check that README install instructions (clone into the personal skills directory) do not suggest tests run against the personal copy; the personal copy shadows the project copy. Prevention: README states the `--setting-sources project,local` requirement for tests.

### Pitfall 22: Gitignore carve-outs that surprise
`*.log` is ignored but `tests/evidence/**/*.log` is tracked; `.claude/` and `.backups/` are untracked here. A harness that writes under `.claude/` in the repo (fixture skill copies) must not end up staged. Prevention: harness writes fixtures only under the run root, never in the repo tree; add a post-run `git status --porcelain` assertion for the repo itself.

### Pitfall 23: Model alias drift
Aliases such as `sonnet` change meaning over time. Prevention: full model ID in the command and in the evidence.

### Pitfall 24: Partial `--setting-sources` confusion
Omitting `user` also drops the user's permission rules and model setting; a stranger's auth may rely on user-level config. Prevention: preflight authentication (`claude auth status`) and print the auth method (`authMethod` field) in the run header.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy the old `pub-*.sh` scripts into the repo unchanged | Fast publication of the harness | Carries the known defects (macOS-only flags, `rm -rf`, substring detection, allowlist drift) into a public repo | Never; port with the fixes in Pitfalls 4, 9, 10, 11, 12 |
| Post-hoc sed sanitization of finished evidence | No harness change | New path shapes leak on other machines | Only for the one-time cleanup of existing evidence, with a verification scan |
| One run per row, accept on first green | Cheapest | Flaky acceptance, unprovable fixes | Non-gating rows only; never for row 7 and carried-forward rows |
| Stub that only echoes expected strings | Quick start | Backend rows stop exercising real branches | Never; replay conformance is the minimum |
| Editing `references/checkpoint-v1.md` for publication tidying | Removes private-build mention | Invalidates adapter digest and carried-forward rows | Only as a deliberate skill change followed by reruns |
| Relying on committed `.claude/settings.json` allow rules | Simple setup | Ignored untrusted in headless; silent failure for strangers | Never for allow rules |
| `--bare` to get a "clean" run | Removes contamination | Different behaviour than the evidence baseline; needs API key | Only as a new, labelled baseline |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `claude -p` permissions | Pattern with colon in the middle, global git option before the subcommand, relying on built-in read-only set | Exact command text derived from traces; verify denials from structured output |
| `stream-json` output | Parsing only the final text; ignoring `system/init` and `permission_denials` | Record init, check denials, require a final `result` message |
| Claude Code version | Assuming defaults are stable | Pass every knob; version gate; tested-versions table |
| Checkpoint helper (stub) | Treating the contract doc as the full spec | Replay recorded argv/exit codes; branch table |
| git | Capturing status with whitespace splitting; trusting the model's measurements | NUL or fully quoted porcelain parsing in Python; independent byte manifest |
| GitHub | Assuming a force-push removes old objects | Old SHAs persist until GC; Support only for sensitive data; rotate/accept for the rest |
| gitleaks | Scanning only HEAD or only content | Scan `--all` history with custom identifier rules and commit metadata checks |

## Performance (Cost) Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Running the whole matrix by default | Quota exhausted, surprise bill | Opt-in rows, printed estimate, caps | First contributor run |
| Repetition without budget (n of at least 3 on gating rows) | Cost multiplies | Limit repetition to gating rows; `--max-budget-usd` | The Matrix rerun phase |
| Background-wait hangs | Run stays open up to 10 minutes idle | Wall-clock timeout; SIGINT | Any row where the model starts a background task |
| Retry loops from denied tools | Long, expensive turns | `--max-turns`; consider `--permission-prompts none` (tells the model not to retry) only as a labelled baseline | Allowlist mismatches |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Running a stranger's allowlist with broad `Bash` | Fixture or hostile name drives command execution on the contributor's machine | Tight exact-command allowlist, run root confined, no `bypassPermissions`/`acceptEdits` unless a row requires it |
| Unquoted expansion of hostile filenames in harness shell | Injection on the host | Python generation and handling; shellcheck |
| Deny rules relied on as a boundary | Documented as bypassable by alternate invocation forms | Snapshot hashes and write-outside-root detection as the real control |
| Committing real transcripts | Paths, ids, account details | Write-time sanitizer plus runtime deny-list plus scan hooks |
| Pushing from a wrong git identity | Permanent personal email in public history | Local config, user.useConfigOnly, pre-push identity check, GitHub push block |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| README with a single "run the harness" command | Surprise cost, confusing failures | Staged: self-test (free), smoke row, one layout, full matrix |
| Failures reported as stack traces | Strangers abandon | One-line cause plus the fix (version, trust warning, missing stub) |
| Evidence folders without a summary table | Hard to see what was verified | Per-row table with digests, version, n, invariants |
| Silent partial runs | False confidence | Summary prints rows run, rows skipped, denials per row |

## "Looks Done But Isn't" Checklist

- [ ] **Audit accepted:** the three open items have recorded decisions and a recorded reason; the rewrite (if any) was a single pass; SHAs in prose updated.
- [ ] **Identity:** `git log --all --format='%an|%ae|%cn|%ce' | sort -u` shows only the approved identity; trailers checked.
- [ ] **Mirror scan:** gitleaks plus identifier rules clean on a fresh `--mirror` clone, history and tree.
- [ ] **Hooks installed:** pre-commit and pre-push scans active; they fail on a seeded fake leak (test the test).
- [ ] **Allowlist:** every command in the expected-commands table runs without an unexpected denial on the pinned version.
- [ ] **Trust:** no "has not been trusted" warning in any stderr of the clean-clone run.
- [ ] **Init manifest:** each run's `system/init` matches the expected skills, tools, MCP servers and plugin set.
- [ ] **Stub:** replay conformance passes against all recorded wrapper logs; branch table fully hit by the rerun.
- [ ] **Helper unreachable:** clean-clone run proves the private helper was never called.
- [ ] **Row 7:** n of at least 3, mechanical invariants hold in all, every Do-not-redo entry supported by a call in that turn.
- [ ] **Digests:** skill, adapter, stub, wrapper, Claude Code version and model ID recorded per row.
- [ ] **Cost:** measured per-row spend recorded; README states it; caps present.
- [ ] **No destructive code path:** `grep -n 'rm ' ` over harness scripts finds nothing; run root creation is exclusive.
- [ ] **Flip approval:** bokiko's explicit instruction is in the conversation record before the visibility change.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Leak found after flip (path, identity) | HIGH | Judge exposure; if sensitive: rotate, rewrite from a mirror, force-push, ask GitHub Support to purge cached views and dangling commits, notify known cloners; if not sensitive: accept and document |
| Wrong identity in new commits | LOW before push, HIGH after | Amend/rebase locally before push; after push treat as Pitfall 2 |
| Allowlist mismatch discovered after acceptance | MEDIUM | Fix table, rerun affected rows into new folders, mark old rows superseded (do not edit) |
| CLI drift breaks harness | MEDIUM | Pin version via install, record drift run as new evidence, update tested-versions table |
| Stub diverges from real behaviour | MEDIUM | Add the missing recorded call to replay tests, fix stub, rerun backend rows |
| Harness deleted or overwrote a run | HIGH (evidence loss) | Restore from backup/bundle; ensure exclusive creation; never repair history of evidence |
| Cost overrun | LOW to MEDIUM | Stop, review cap flags, restrict rows, document measured cost |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Rewrite decisions and SHA churn | Publication gate | One recorded decision; SHA citations resolve in `git cat-file -t` |
| 2 Author identity in metadata | Publication gate, then every push | Identity query clean; pre-push check fails on a wrong identity |
| 3 Leak surface and scan scope | Publication gate; Harness extraction | Mirror scan clean; seeded-leak test fails closed; runtime deny-list test |
| 4 Allowlist silent mismatch | Harness extraction; Matrix rerun | No unexpected `permission_denials`; expected-commands table matches traces |
| 5 Untrusted project allow rules | Harness extraction; Matrix rerun | Clean-path run with no trust warning |
| 6 Environment contamination | Harness extraction; Matrix rerun | Init manifest assertion; skill digest match; helper-unreachable proof |
| 7 CLI version/default drift | Harness extraction | Version gate test; explicit flags in `tools.txt`/run header |
| 8 Flakiness and self-reported claims | Harness extraction; Matrix rerun | Invariant/behaviour split in acceptance doc; n of at least 3 on gating rows |
| 9 Substring refusal detection | Harness extraction | Parser unit tests on golden stream-json excerpts |
| 10 Instrumentation on startup calls | Harness extraction | Wrapper self-test: no trigger on a no-op session |
| 11 Destructive / fragile shell | Harness extraction | No `rm` in scripts; exclusive creation test; shellcheck clean |
| 12 Manifest/portability | Harness extraction; Matrix rerun | Model-free hostile-fixture manifest self-test; second-OS run |
| 13 Stub fidelity | Stub helper; Matrix rerun | Replay conformance; branch coverage table |
| 14 Token cost | Harness extraction; Matrix rerun | Caps in every call; dry run costs zero; measured per-row spend published |
| 15 Not a true clean clone | Matrix rerun | Fresh path, minimal env, no `runs/`, helper unreachable |
| 16 Flip side effects | Visibility flip | Live-repo inventory, post-flip security toggles, explicit approval |
| 17 Harness mistakes become public | Publication gate (policy) | Branch-and-scan workflow; first evidence reviewed locally |
| 18 `.planning/` and dangling references | Publication gate | Reader-test of public docs; no pointers to private artifacts |
| 19 Non-comparable evidence | Harness extraction | Sanitizer version recorded; invariant-based comparison |
| 20 Stale carry-forward claims | Matrix rerun; Publication gate | Per-row digest table; tagged version |

## Research Flags for Phases

- **Stub helper:** needs targeted analysis of all committed wrapper logs and decisive helper outputs to extract the observable contract (section-hash scheme as seen, `.conflict-*` content, bind/create/init behaviour needed by setup) before writing code. MEDIUM-confidence area.
- **Harness extraction (isolation):** experiment whether a scratch `CLAUDE_CONFIG_DIR` (or `HOME` override) isolates user config while keeping auth working on both macOS and Linux; unverified.
- **Harness extraction (flags baseline):** inspect the committed `tools.txt`/`settings.json`/run headers to establish exactly which flags the 2026-10-20 evidence used; do not add `--permission-prompts none` or `--bare` without declaring a new baseline.
- **Publication gate:** standard patterns (filter-repo, gitleaks, GitHub docs); no extra research needed beyond reading the ten affected lines.
- **Visibility flip:** standard; verify current GitHub account and repo toggles in the UI at the time.

## Sources

- Claude Code documentation, permissions (rule syntax, compound commands, wrappers, bash rule limits, project allow rules and workspace trust, what runs before trust) - https://code.claude.com/docs/en/permissions - HIGH, fetched 2026-10-21
- Claude Code documentation, headless / programmatic use (`-p`, `--bare`, stream-json, `permission_denials`, `--permission-prompts`, background tasks at exit, SIGTERM exit 143, cost fields) - https://code.claude.com/docs/en/headless - HIGH, fetched 2026-10-21
- Claude Code CLI reference (`--setting-sources`, `--settings`, `--model`, `--fallback-model`, `--max-turns`, `--max-budget-usd`, `--no-session-persistence`, `--safe-mode`, `--restricted`, `--bare`) - https://code.claude.com/docs/en/cli-reference - HIGH, fetched 2026-10-21
- Claude Code settings and precedence (command-line tier above file tiers, local settings trust rules) - https://code.claude.com/docs/en/settings - HIGH, fetched 2026-10-21
- GitHub Docs, removing sensitive data from a repository (cached views, dangling commits, PR refs, forks, Support scope, filter-repo 2.47+) - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository - HIGH, fetched 2026-10-21
- GitHub Docs, setting repository visibility (Actions logs visible, forks, stars reset, rulesets disabled) - https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility - HIGH, fetched 2026-10-21
- GitHub Docs, setting your commit email address (local config governs command-line commits; old commits keep old address) - https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address - HIGH, fetched 2026-10-21
- Agent evaluation literature on pass@k versus pass^k and run-to-run variance (survey search results; not a Claude Code-specific source) - MEDIUM
- This repository, read-only: `PROJECT.md`, `CONCERNS.md`, the publication evidence README, `references/checkpoint-v1.md`, `tests/acceptance.md`, `.gitignore`, `git log` metadata and `git grep` counts (the gitignored `runs/` folder was not read) - HIGH for repo facts

---
*Pitfalls research for: public release of a Claude Code skill repository and a reproducible headless test harness with a stub helper*
*Researched: 2026-10-21*
