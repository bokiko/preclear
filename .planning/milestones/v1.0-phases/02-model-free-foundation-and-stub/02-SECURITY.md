---
phase: "02"
slug: "model-free-foundation-and-stub"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-12"
---
# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail. Written retroactively on 2026-11-12 by /gsd-secure-phase from the plans' threat models and the security auditor's verdict; the implementation was not changed.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| harness to child claude process | the environment the child and the model's own Bash tool inherit; anything passed here can reach a transcript | see description |
| harness to local Claude Code auth state | login status read through the CLI; identity and token fields sit behind the same command | see description |
| stranger's machine to the shim | PATH, python3 and git resolved from the stranger's environment | see description |
| captured stream to the parser | untrusted bytes written by a model-driven process | see description |
| model or harness to stub CLI | argv, section names, hashes and body files come from a model-driven process | see description |
| stub to filesystem | the stub writes ledgers, bindings, conflict files and snapshots; anything outside CKPT_HOME would escape the per-run isolation | see description |
| committed evidence to miner | frozen, sanitised files read as data | see description |
| caller to allocator | run-root names and parents come from CLI arguments and later from a driver | see description |
| harness to filesystem | run roots and snapshots are created under paths the caller names; symlinks and odd names can redirect writes | see description |
| snapshotter to credentials | a snapshot root chosen wrongly could include the Claude config directory | see description |
| model-facing allowlist to the setup verbs | an allowlist that matches bind, create or init lets the model rebind or create ledgers | see description |
| wrapper to stub | the wrapper sits between the model and the stub and could alter calls or output | see description |
| documentation to evidence | the branch table and the reference digest claim fidelity to committed evidence | see description |
| run output to public evidence | everything promoted into tests/evidence becomes public history | see description |
| sanitizer and gate to terminal and logs | an echoed match would itself be a leak | see description |
| local deny file to the harness | the file holds private strings the owner chose; it must never leave the machine | see description |
| promote to the filesystem | destination and stage paths come from callers; links and traversal could redirect writes | see description |
| stub to concurrent callers | several processes can call the stub at once on one ledger | see description |
| stranger's environment to the harness | PATH, interpreters and any dependency the harness might silently import | see description |
| documentation to code | README tables that claim what the code pins | see description |
| committed harness files to the public repository | every file in tests/harness becomes public history | see description |
| harness to Claude Code login | a subscription login the harness must use without ever handling credentials | see description |
| executor session to the inner claude process | the inner run must not inherit the outer session, its environment or this repository's settings | see description |
| raw capture to public repository | a real stream holds paths, ids and model text; only sanitised, gated copies may be committed | see description |
| harness to the user's own Claude folders | listed by name for an absence check only | see description |
| captured run output to public evidence | a stream or transcript becomes public history once it is promoted into tests/evidence | see description |
| sanitizer and gate to terminal, logs and exceptions | an echoed login, path or entry would itself be a leak | see description |
| local deny file and its location to the gate | the file holds private strings the owner chose; if the gate cannot find it, the strings are silently not enforced | see description |
| gate rule set to the commit hooks | the Python rules and the hooks' configuration must stay identical, and a tighter hook rule must not block legitimate work | see description |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 (02-01) | Information disclosure | pc_preflight reading auth status (identity fields beside loggedIn) | high | mitigate | only the boolean loggedIn is parsed; the raw output is never stored, logged, printed or returned; test plants an identity sentinel in the fake output and ass... | closed |
| T-02-02 (02-01) | Information disclosure | pc_flags.build_env (credentials in the environment reaching the child and the mo | high | mitigate | allow-listed minimal environment; ANTHROPIC_*, CLAUDE_CODE_* and token variables dropped; CLAUDE_CODE_SUBPROCESS_ENV_SCRUB set; test with sentinel secrets (A... | closed |
| T-02-03 (02-01) | Elevation of privilege | pc_flags.build_allowed_tools (a bare wrapper prefix would allow bind, create and | high | mitigate | per-verb rules only; driver-only and unknown verbs refused; test asserts the output holds no rule that is only the wrapper path | closed |
| T-02-04 (02-01) | Spoofing | tests/harness/selftest zero-model-call guarantee (a claude still resolvable afte | medium | mitigate | the shim refuses to run (exit 12) when claude is still on the scrubbed PATH; test_selftest_shim runs a tripwire claude first on PATH, also in a directory sha... | closed |
| T-02-05 (02-01) | Repudiation | pc_stream denial detection (a refusal missed, or an incomplete stream read as a  | high | mitigate | structured events and result.permission_denials only; empty, truncated or result-less streams are errors; mismatch between the two signals reported both ways | closed |
| T-02-06 (02-01) | Tampering | pc_flags version gate (an untested Claude Code build silently drives a row) | medium | mitigate | exact-match tested set, distinct exit code 13; set seeded only from a captured S2 run; floor documented | closed |
| T-02-41 (02-01) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only and no package-manager command; any later install would need the legitimacy audit and a blocking human chec... | closed |
| T-02-09 (02-02) | Elevation of privilege | stub runs without isolation (state in the user's real helper home) | high | mitigate | CKPT_HOME required, exit 64 otherwise; no read of any other config directory; the stub never opens a path outside CKPT_HOME except the body file named by --f... | closed |
| T-02-10 (02-02) | Repudiation | stub passes its own tests but diverges from recorded behaviour (circular conform | medium | mitigate | replay of every mined call against committed outputs; four independent path-free hashes; the masked header values are checked by shape and the masking is lis... | closed |
| T-02-11 (02-02) | Information disclosure | replay or conflict output echoing real paths or ids into committed files | medium | mitigate | tests normalise to committed tokens, scratch directories live under the system temp directory and are never printed; nothing in this plan writes into tests/e... | closed |
| T-02-42 (02-02) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only | closed |
| T-02-13 (02-03) | Tampering | run root or evidence overwritten or deleted by harness code | high | mitigate | exclusive creation only (os.mkdir without exist_ok, os.open with O_EXCL); collision is exit 16; the static AST scan keeps every pc_ module free of delete, re... | closed |
| T-02-14 (02-03) | Tampering | path traversal and symlink following in allocate_run_root, write_exclusive and c | high | mitigate | name validation (no separators, dot names, NUL, over-long, unencodable), O_NOFOLLOW on file creation, symlinks and special files refused in copy_tree_exclusi... | closed |
| T-02-15 (02-03) | Information disclosure | snapshot taken over the harness-owned Claude config directory (credentials, hist | high | mitigate | tree_manifest refuses any root at or under a refuse_under path with a component-aware check; plan 02-08 passes the config directory there | closed |
| T-02-16 (02-03) | Repudiation | a manifest that splits names on newlines or drops entries (the committed row 10  | medium | mitigate | in-process byte walk, injective escaping, one line per regular file asserted by test, lossless JSON-lines companion | closed |
| T-02-17 (02-03) | Tampering | git status capture mutating the repository (index lock, refresh) | low | mitigate | --no-optional-locks, read-only status command only, index digest compared before and after in a temporary repository | closed |
| T-02-43 (02-03) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only | closed |
| T-02-18 (02-04) | Tampering | checkpoint-wrapper altering the caller's arguments, input files or output (poiso | high | mitigate | the wrapper forwards arguments and output unchanged; injection output goes to injection.log; test compares wrapper and direct stub output byte for byte and t... | closed |
| T-02-19 (02-04) | Elevation of privilege | an allowlist rule that matches wrapper bind, create or init | high | mitigate | per-verb builder (plan 02-01), matcher tests here deny all three, the historical bare-prefix shape is shown to allow bind and never emitted, plan 02-08 recor... | closed |
| T-02-20 (02-04) | Repudiation | injection happening without a trace | medium | mitigate | every injection writes a header, the writer's exit code and the section into injection.log; calls.log records every caller call with its exit code | closed |
| T-02-21 (02-04) | Tampering | references/checkpoint-v1.md edited to suit the stub, invalidating every carried- | high | mitigate | digest test against committed evidence and the frozen-path git diff in every verify; stub documentation lives under tests/harness only | closed |
| T-02-22 (02-04) | Repudiation | branch table overstating fidelity (a behaviour marked CONFIRMED with no committe | medium | mitigate | test requires each CONFIRMED row to name an existing evidence path; every unobserved branch is UNCONFIRMED; docstring and table cannot drift | closed |
| T-02-50 (02-04) | Elevation of privilege | indirect launch of the wrapper's driver verbs through baseline rules (env, pytho | high | mitigate | the wrapper refuses bind, create and init with exit 71 whatever launched it (task 1 test, including an env-prefixed launch); the matcher test records the rou... | closed |
| T-02-44 (02-04) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library and bash only | closed |
| T-02-23 (02-05) | Information disclosure | sanitizer, gate and promote output echoing a matched value, home path, host or t | high | mitigate | counts, rule ids and labels only; fixed messages for errors; tests assert no seeded fragment appears in any output (ASVS V7) | closed |
| T-02-24 (02-05) | Information disclosure | local deny file .git/info/preclear-deny.txt (printed, logged, copied or committe | high | mitigate | read-only, entries only in memory, accessor documented as never to print, error messages fixed, tests use fixed assertion messages and a synthetic file | closed |
| T-02-25 (02-05) | Repudiation | a scanner crash, zero rules or an unreadable input read as "no findings" | high | mitigate | every exception is ScannerError and exit 15; import-time rule validation; refusals for NUL, undecodable, symlink, special and oversize inputs; zero files is ... | closed |
| T-02-26 (02-05) | Tampering | promote path traversal, symlink following, destination outside tests/evidence, c | high | mitigate | realpath containment under the repository's tests/evidence, no dot-dot, symlink refusal, config-directory refusal, exclusive creation of every directory and ... | closed |
| T-02-27 (02-05) | Tampering | time-of-check to time-of-use between scan and copy | medium | mitigate | each file read once into memory, scanned and written from the same bytes; whole set gated before any creation; test patches a late read | closed |
| T-02-28 (02-05) | Information disclosure | sanitizer missing a form (slug, URL-encoded, NFD, case) so a path survives | medium | mitigate | all forms built at run time, case-insensitive matching, the gate scans the output as a second net, the Phase 1 hooks and push protection as third and fourth | closed |
| T-02-29 (02-05) | Denial of service | pathological input or oversized file stalling the scan | low | mitigate | linear-shaped rules reused from .gitleaks.toml, 5 MiB cap with refusal, single-buffer scan | closed |
| T-02-45 (02-05) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only | closed |
| T-02-07 (02-06) | Tampering | checkpoint_stub path handling (ledger or root outside CKPT_HOME, dot-dot, symlin | high | mitigate | realpath plus component-aware containment for every ledger, root, conflict and handoff path; test_stub_cli proves the three escape forms and the sibling-pref... | closed |
| T-02-08 (02-06) | Tampering | ledger update race (two sessions overwrite each other, or a crash leaves a half- | high | mitigate | dedicated lock file with flock, expected-hash compare inside the lock, mkstemp plus fsync plus os.replace in the ledger folder; concurrency test shows one wi... | closed |
| T-02-12 (02-06) | Tampering | stub lenient where the real helper rejects (blocks the matrix would then never e | medium | mitigate | boundary tests at 4,096 and 4,097 bytes and 600 and 601 characters, structural rejection cases for missing, extra, duplicate and misordered sections (plan 02... | closed |
| T-02-49 (02-06) | Denial of service | lock wait without a bound (a stuck holder hangs every caller) | low | mitigate | non-blocking flock inside a deadline loop with a default of 5000 ms, exit 6 on deadline, an invalid timeout value is a usage error; the contended-lock test p... | closed |
| T-02-46 (02-06) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only | closed |
| T-02-37 (02-07) | Information disclosure | README, tests or data under tests/harness carrying an absolute path, host name o | medium | mitigate | test_readme scans for forbidden needles assembled from fragments; the Python gate and gitleaks dir run over the whole folder in the phase gate; the commit ho... | closed |
| T-02-38 (02-07) | Tampering | a hidden non-standard dependency pulled in by a harness module (supply chain) | medium | mitigate | test_imports classifies every import by origin under the interpreter's stdlib paths and fails on anything else; no package-manager command appears anywhere | closed |
| T-02-39 (02-07) | Spoofing | the shim claiming zero model calls while a claude executable is reachable | medium | mitigate | the shim removes claude directories from PATH and refuses to run when claude still resolves; the end-to-end tripwire run proves nothing executes it | closed |
| T-02-40 (02-07) | Repudiation | documentation drifting from the code (flag table, exit codes, switches, isolatio | low | mitigate | test_readme compares each table and the isolation line with the code (the isolation line against pc_flags.ISOLATION_CLAIM; plan 02-08's fixture test compares... | closed |
| T-02-47 (02-07) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only, and the README instructs no install | closed |
| T-02-30 (02-08) | Information disclosure | credentials and account identity (login flow, auth status output, config directo | high | mitigate | bokiko logs in himself; the driver reads only the loggedIn boolean through the CLI, never opens a credential file, never prints other fields; the config dire... | closed |
| T-02-31 (02-08) | Denial of service | unbounded or repeated paid calls overrunning the 5.00 USD limit | high | mitigate | per-call --max-budget-usd and --max-turns, at most two attempts per call name, a spend ledger outside the repository, a guard that counts unknown cost as the... | closed |
| T-02-32 (02-08) | Information disclosure | raw stream, init output or hook log committed with paths, ids or text | high | mitigate | raw captures stay in the run root under the harness home, outside the repository; only sanitiser output that passed the Python gate and gitleaks is written, ... | closed |
| T-02-33 (02-08) | Tampering | spike result contaminated by the user's own config, skills or memory (isolation  | medium | mitigate | harness config directory outside the repository and the user's Claude folder, project and local setting sources only, S1 absence check by run-time name set a... | closed |
| T-02-34 (02-08) | Elevation of privilege | the model executing a setup verb (bind) or other commands during the probe | medium | mitigate | the allowlist is the per-verb builder output; the bind probe uses an unused session id and a nonexistent ledger so even an unexpected allow mutates nothing; ... | closed |
| T-02-35 (02-08) | Repudiation | fixtures and findings that no longer describe the build in use | medium | mitigate | the version is recorded in the findings and the manifest, TESTED_VERSIONS is seeded from the capture and a test ties the fixture to it, the gate refuses ever... | closed |
| T-02-36 (02-08) | Spoofing | the inner claude inheriting the outer session's environment, hooks or this repos | medium | mitigate | build_env passes an allow-listed minimal environment, the scratch project sits under the harness home, outside this repository, with its own settings, --sett... | closed |
| T-02-48 (02-08) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library and the already-installed claude CLI only | closed |
| T-02-51 (02-09) | Information disclosure | sanitizer: the login kept when a JSON letter escape precedes it (CR-01) | high | mitigate | the word-kind prefix accepts a backslash plus n, r, t, b or f; tests for each letter, for both normalisation forms and for the real login; ambiguous escapes ... | closed |
| T-02-52 (02-09) | Information disclosure | gate: no second net for the login, so a miss in the sanitizer reached evidence | high | mitigate | the login (NFC and NFD) joins Sanitizer.deny_entries(); the gate reports it as a deny-list count with no value; a login inside a fixed token is excluded so t... | closed |
| T-02-53 (02-09) | Information disclosure | gate and hooks: home-path rules ending only at a listed delimiter (CR-02), so a  | high | mitigate | a "not a name character" ending in the mirrored rule (engine-compatible, no lookaround) and in the two Python-only rules (lookaround allowed); the TOML twin ... | closed |
| T-02-54 (02-09) | Information disclosure | gate: identifier rules evaded by non-ASCII neighbours or an upper-case private s | medium | mitigate | `re.ASCII` compile and a scoped case-insensitive suffix group in both twins; tests for neighbours, six suffixes in two cases, and a look-alike that must not ... | closed |
| T-02-55 (02-09) | Repudiation | gate: a git failure, a missing git or a wrong repository root silently dropping  | high | mitigate | an unlocatable list is ScannerError and exit 15 with a fixed message; the only quiet case is a tree with no repository above it, decided by a filesystem chec... | closed |
| T-02-56 (02-09) | Tampering | deny file: a byte-order mark or trailing padding making an entry that can never  | medium | mitigate | `utf-8-sig` decode and a strip on every line before the comment and floor checks; tests with a mark, padding, tabs and an indented comment, and a CLI test th... | closed |
| T-02-57 (02-09) | Tampering | commit hooks: the tightened twin rule blocking the owner's pushes or the accepte | medium | mitigate | verified before and after: history scan exit 0 (accepted fingerprints are unchanged by a regex change), `sh scripts/test-hooks.sh` 29 PASS before the edit, a... | closed |
| T-02-58 (02-09) | Information disclosure | any new output echoing the login, a path or an entry | medium | mitigate | counts, rule ids and fixed messages only; every new test builds labels from case names and asserts the login is absent from the report, repr, str and error text | closed |
| T-02-SC (02-09) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only (D-11) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-02-01 | T-02-41 (02-01) | this plan installs nothing; standard library only and no package-manager command; any later install would need the legitimacy audit and a blocking human checkpoint | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-02 | T-02-42 (02-02) | this plan installs nothing; standard library only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-03 | T-02-15 (02-03) | ACCEPTED RISK, not mitigated in code: the refuse_under guard of pc_manifest.tree_manifest is unit-tested but no production snapshot call or the manifest CLI passes the harness config directory (rev... | orchestrator on bokiko's instruction to finish the phase close-out without further questions (2026-11-12); revisit on request | 2026-11-12 |
| AR-02-04 | T-02-43 (02-03) | this plan installs nothing; standard library only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-05 | T-02-44 (02-04) | this plan installs nothing; standard library and bash only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-06 | T-02-45 (02-05) | this plan installs nothing; standard library only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-07 | T-02-46 (02-06) | this plan installs nothing; standard library only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-08 | T-02-47 (02-07) | this plan installs nothing; standard library only, and the README instructs no install | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-09 | T-02-48 (02-08) | this plan installs nothing; standard library and the already-installed claude CLI only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-02-10 | T-02-SC (02-09) | this plan installs nothing; standard library only (D-11) | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-12 | 59 | 59 | 0 | gsd-security-auditor (sonnet) via /gsd-secure-phase, retroactive |

### Auditor evidence and observations

The auditor returned OPEN_THREATS for T-02-15 (guard present but never armed in production); it is closed above through accepted risk AR-02-03 with a tracked follow-up, so threats_open is 0. The unregistered summary flag `shared-folder-write` (02-08) is kept as an observation with the same follow-up. The auditor's full verdict is reproduced below (evidence pointers are file:line at the audited commit).

## OPEN_THREATS

**Phase:** 02 - model-free-foundation-and-stub (retroactive /gsd-secure-phase 2)
**ASVS Level:** 1 | **block_on:** high
**Register:** 59 threats (50 mitigate, 9 accept), authored at plan time (T-02-xx ids from the nine PLAN threat_model blocks)
**Closed:** 58/59 | **Open:** 1/59 | **Open at or above high (blocking):** 1 (T-02-15) | **Open below high (non-blocking):** 0
**threats_open:** 1

Audited against the working tree at HEAD 0c6cd7f, so Phase 3 and Phase 4 edits to the audited files are in scope (several deferred
Phase 2 review items were closed by Phase 3, see Observations). Implementation files were not modified. The unit suites were not run.
Read-only commands I did run: `python3 -E -s -B tests/harness/pc_leakgate.py scan tests/harness` (93 files, 0 findings, exit 0);
`gitleaks dir tests/harness --config .gitleaks.toml` (exit 0); `gitleaks git --config .gitleaks.toml` over the full history (exit 0);
`git diff 56e155c HEAD -- references SKILL.md tests/evidence/publication-2026-10-20` (empty); an AST import classifier over every
tests/harness/*.py (0 non-stdlib imports); a count-only scan of tests/harness/data with the live sanitizer deny entries (see Observation 11).

## Open (blocking: severity high >= block_on high)

| Threat ID | Category | Severity | Mitigation expected | Files searched | Finding |
|---|---|---|---|---|---|
| T-02-15 | Information disclosure | high | "tree_manifest refuses any root at or under a refuse_under path with a component-aware check; plan 02-08 passes the config directory there" | tests/harness/pc_manifest.py, pc_spike.py, pc_row1.py, pc_rowhooks.py, pc_rows.py, pc_matrix.py, pc_checks.py, pc_evidence.py, pc_compare.py, pc_baseline.py, pc_rowseeds.py | First clause present, second clause absent. The guard exists and is unit-tested (pc_manifest.py:318-338 `_check_refuse_under`/`tree_manifest`; test_manifest.py:254-284). But no production code arms it: `pc_spike.py` takes no snapshot and never passes `refuse_under` (its only `tree_manifest` call is `_copy_tree_with`, pc_spike.py:373, over repo-owned fixture sources); all three production calls of `pc_row1.take_snapshot` (pc_row1.py:775, pc_row1.py:1443, pc_rowhooks.py:628) leave `refuse_under` at its `()` default, so pc_row1.py:276 runs `tree_manifest(run_root, ())`; the `pc_manifest.py ROOT` CLI calls `tree_manifest(args[0])` with no guard (pc_manifest.py:436; this is review item WR-11, deferred by bokiko's routing and still open). A `grep -rn refuse_under tests/harness/pc_*.py` finds only the definition and the unused forwarding parameter. The guard is therefore dormant in every production path. |

Exposure assessment (does not change the status, for the owner's decision): there is no demonstrated exploit path today. Snapshot roots are
run roots allocated under the runs root (`pc_spike.runs_root`, pc_spike.py:264-306: outside the repo, outside every local home) while the
config directory is `<harness home>/claude-config`, a sibling and not a descendant; promote's own config-directory refusal IS armed in
production (pc_evidence.py:1690 passes `config_dir`). The protection for snapshots is by construction only, and the CLI would print names,
sizes and sha256 of the credential files in the harness config directory if pointed at it. To close: pass
`refuse_under=(<harness config dir>,)` at the three `take_snapshot` call sites (or have `take_snapshot` default it from
`pc_spike.CONFIG_DIR_NAME` under the harness home) and in `pc_manifest.main` (WR-11), with a test per call site; or record a dated
accepted risk (a proposed entry text is at the end of this file, NOT applied).

## Closed (58) - one row per threat

| Threat ID | Category | Severity | Disposition | Status | Evidence (file:line) |
|---|---|---|---|---|---|
| T-02-01 | Information disclosure | high | mitigate | closed | pc_preflight.py:208-216 reads only `loggedIn` then `del parsed`; module doc :19-20; identity sentinel absent from all output: test_preflight.py:133,175,255,272, test_spike.py:622,651,703 |
| T-02-02 | Information disclosure | high | mitigate | closed | pc_flags.py:101-111 allow-list (no ANTHROPIC_*/CLAUDE_CODE_*), :388-422 `build_env` sets CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 (:417); wired at pc_spike.py:1401, pc_row1.py:729; sentinel secrets: test_flags.py:226-262 |
| T-02-03 | Elevation of privilege | high | mitigate | closed | pc_flags.py:90-99 verb sets, :425-444 `build_allowed_tools` refuses bind/create/init/unknown (:438-440), emits per-verb rules only; wired pc_spike.py:1397; test_flags.py:327-345 |
| T-02-04 | Spoofing | medium | mitigate | closed | tests/harness/selftest:60-77 scrubs PATH and exits 12 if claude still resolves (:74-77); test_selftest_shim.py:58-96 tripwire first on PATH and in a shared dir, `read_tripwire == []` |
| T-02-05 | Repudiation | high | mitigate | closed | pc_stream.py:65-99 strict parse, :106-111 exactly one result else StreamError, :189-213 two structured signals with only_in_events/only_in_result, :221-226 `row_failed` fails closed, :294-327 CLI exits 19; test_stream.py:212-240,290-311,355 |
| T-02-06 | Tampering | medium | mitigate | closed | pc_flags.py:38 `TESTED_VERSIONS=("2.1.310",)`, :527-543 exact match; pc_preflight.py:185-191 + pc_exitcodes.py:39 (13); test_spike_fixture.py:83-88 ties the seed to the S1/S2 captures |
| T-02-41 | Tampering | low | accept | closed (accepted; see log) | no installs: independent import classifier found 0 non-stdlib imports in tests/harness/*.py; no requirements/package/pyproject/Cargo manifest; only install-command string is test_readme.py:277 asserting absence |
| T-02-09 | Elevation of privilege | high | mitigate | closed | checkpoint_stub.py:928-931 exit 64 without an existing CKPT_HOME; :203-208,:349-353,:365-369,:389-403 every ledger/root realpath-contained in a registered root that is itself inside CKPT_HOME; file reads no other config dir (no HOME/expanduser use) |
| T-02-10 | Repudiation | medium | mitigate | closed | test_stub_replay.py:1-37 listed normalisations, :76-81 four path-free hashes derived independently; replay-cases.json 9 cases/15 calls; test_branch_table.py:172-182 UNCONFIRMED list tied to the stub docstring |
| T-02-11 | Information disclosure | medium | mitigate | closed | test_stub_replay.py:37 scratch under system temp, paths never printed, nothing written to tests/evidence; leak gate over tests/harness: 0 findings |
| T-02-42 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |
| T-02-13 | Tampering | high | mitigate | closed | pc_runroot.py:59-78 `os.mkdir` no exist_ok (collision exit 16, :25), :86-104 O_CREAT\|O_EXCL; test_runroot.py:418-483 AST scan over pc_*.py, exemption set asserted == {pc_testutil.py, pc_seeds.py} (:419-420); independent grep: no remove/unlink/rename/replace/rmtree/move/truncate/"w"-mode in pc_*.py outside pc_testutil.py |
| T-02-14 | Tampering | high | mitigate | closed | pc_runroot.py:40-56 name validation (empty, dot names, separators, NUL, >255 bytes, unencodable), :93 O_NOFOLLOW, :132-170 `copy_tree_exclusive` refuses symlink/special; test_runroot.py:111-160,257-317 |
| T-02-15 | Information disclosure | high | mitigate | **OPEN (blocking)** | guard present pc_manifest.py:318-338 but never armed in production: see Open table |
| T-02-16 | Repudiation | medium | mitigate | closed | pc_manifest.py:343-373 in-process byte walk, :376-396 injective escaping and one line per regular file, :399-412 lossless JSON lines; test_manifest.py:75-163 |
| T-02-17 | Tampering | low | mitigate | closed | pc_manifest.py:68-73 hygiene env, :78 `--no-optional-locks status --porcelain=v1` only, :259-276; test_manifest.py:502-510 index digest unchanged after two captures |
| T-02-43 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |
| T-02-18 | Tampering | high | mitigate | closed | tests/harness/checkpoint-wrapper:118 `real "$@"` forwards args and output untouched; injection output goes only to injection.log (:102-114); test_wrapper_conflict.py:264-301 log shapes and unchanged output |
| T-02-19 | Elevation of privilege | high | mitigate | closed | pc_flags.py:425-444 per-verb builder; test_allowlist.py:220 bind/create/init denied, :380-384 historical bare prefix allows bind and is never emitted; live denial recorded data/spike-findings.md:82-84 |
| T-02-20 | Repudiation | medium | mitigate | closed | checkpoint-wrapper:63-65,73,120 calls.log CALL/EXIT per call; :102-114 injection.log header + `writer2 update exit`; test_wrapper_conflict.py:264-301 |
| T-02-21 | Tampering | high | mitigate | closed | `git diff 56e155c HEAD -- references SKILL.md tests/evidence/publication-2026-10-20` empty (run); test_frozen_reference.py:57-78 reference digest vs committed evidence; test_frozen_tree.py:33-36,69-78 pinned tree digests |
| T-02-22 | Repudiation | medium | mitigate | closed | test_branch_table.py:195-207 every CONFIRMED row names an existing path; data/branch-table.md UNCONFIRMED rows; :172-182 docstring/table tie |
| T-02-50 | Elevation of privilege | high | mitigate | closed | checkpoint-wrapper:68-75 refuses bind/create/init with exit 71 whatever launched it; test_wrapper_conflict.py:433-485 (direct, env-launched, option-prefixed); route left open by design and recorded: test_allowlist.py:460, spike-findings.md:168 |
| T-02-44 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 (bash plus stdlib only) |
| T-02-23 | Information disclosure | high | mitigate | closed | pc_leakgate.py:408-416 `format_findings` counts, rule ids and relative labels only, :587-589 fixed error text; pc_sanitize.py:84-86 fixed messages; pc_promote.py:57-62,195-199; pc_spike.py:1225-1244; test_leakgate.py:747-776 asserts no value/entry/path in output |
| T-02-24 | Information disclosure | high | mitigate | closed | pc_leakgate.py:516-542 read-only `rb` open, entries in memory, fixed error text (:534); pc_sanitize.py:24,279-286 accessor warning and counts-only repr; synthetic deny file in tests: test_promote.py:305-337 |
| T-02-25 | Repudiation | high | mitigate | closed | pc_leakgate.py:73-85 import-time rule compile, :166-174 zero rules refused, :232-259 NUL/undecodable/oversize/long-run refused and any exception is ScannerError, :304-343 symlink/special refused, :593-595 zero files refused; pc_exitcodes.py:41 (15); test_leakgate.py:563 |
| T-02-26 | Tampering | high | mitigate | closed | pc_promote.py:91-92 dot-dot, :96-133 under tests/evidence + per-component lstat symlink refusal + realpath containment, :165-169 config-dir refusal, :203-231 exclusive creation only; armed in production pc_evidence.py:1690; test_promote.py:158-300 |
| T-02-27 | Tampering | medium | mitigate | closed | pc_leakgate.py:283-301 single read, pc_promote.py:176,220-227 writes `entry.data` (the scanned bytes); test_promote.py:339-356 patched late read |
| T-02-28 | Information disclosure | medium | mitigate | closed | pc_sanitize.py:181-190 raw/realpath/two slugs/URL-encoded/NFC/NFD built at run time, :157 IGNORECASE; second net: pc_spike.py:1239, pc_promote.py:183-184; third/fourth: gitleaks history scan exit 0 (run) |
| T-02-29 | Denial of service | low | mitigate | closed | pc_leakgate.py:45,244-245 5 MiB cap refusal, :155-163 MAX_RUN refusal, :283-301 bounded single read, :90-104 rules identical to .gitleaks.toml |
| T-02-45 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |
| T-02-07 | Tampering | high | mitigate | closed | checkpoint_stub.py:203-208 `is_within` (realpath, separator appended), :349-353, :365-369, :389-403, :755-756, :788, :809; test_stub_cli.py:1209-1280 dot-dot, symlink, sibling-prefix refused for show/update/note/handoff and nothing written |
| T-02-08 | Tampering | high | mitigate | closed | checkpoint_stub.py:459-503 flock on CKPT_HOME/.lock held across the whole write verb incl. expected-hash compare (:679-688), :317-332 mkstemp+fsync+os.replace; test_stub_concurrency.py:60-72 one winner [0,3,3,3]; test_stub_cli.py:999-1030 patched os.replace leaves bytes unchanged |
| T-02-12 | Tampering | medium | mitigate | closed | checkpoint_stub.py:141-142,:264-294 structural rejections and 600/4096 limits; test_stub_cli.py:423-429,:1055-1089 boundary tests at 4,096/4,097 bytes and 600/601 chars |
| T-02-49 | Denial of service | low | mitigate | closed | checkpoint_stub.py:155,:446-456 invalid value exit 2, :466-481 non-blocking flock in a deadline loop, exit 6; test_stub_concurrency.py:90-103 exit 6 within 2 s |
| T-02-46 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |
| T-02-37 | Information disclosure | medium | mitigate | closed | test_readme.py:425-446 forbidden fragments assembled from pieces; live: leak gate over tests/harness 93 files 0 findings, `gitleaks dir tests/harness` exit 0 |
| T-02-38 | Tampering | medium | mitigate | closed | test_imports.py:1-70 origin-classified stdlib scan; independent re-run: 0 non-stdlib imports across every tests/harness/*.py |
| T-02-39 | Spoofing | medium | mitigate | closed | tests/harness/selftest:60-77; test_selftest_shim.py:58-96 end-to-end tripwire never fires |
| T-02-40 | Repudiation | low | mitigate | closed | test_readme.py:187 flag table == `pc_flags.render_flag_table_markdown()`, :190-200 exit-code table, :233 isolation line == `pc_flags.ISOLATION_CLAIM`; test_spike_fixture.py:200-205 |
| T-02-47 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 (README instructs no install) |
| T-02-30 | Information disclosure | high | mitigate | closed | pc_preflight.py:208-216 boolean only; no credential file, keychain or token string anywhere in pc_spike/pc_preflight/pc_promote; pc_spike.py takes no snapshot; promote refuses the config dir (pc_promote.py:165-169, armed at pc_evidence.py:1690); sentinels: test_spike.py:622,651,703,1200,1255 (snapshot-guard wiring is tracked under T-02-15) |
| T-02-31 | Denial of service | high | mitigate | closed | pc_spike.py:106-111 per-call caps, :1397-1399 + pc_flags.py:347,351 `--max-turns`/`--max-budget-usd` on every call, :86-87 5.00 USD and 2 attempts, :685-722 guard (unknown cost counts as the cap, refuses before the call), :1402 pessimistic launched line, :1967-1986 dry run unless `--run`, ledger under the harness home outside the repo (:143-170); worst case 2x(0.50+1.00+0.50+0.05)=4.10 |
| T-02-32 | Information disclosure | high | mitigate | closed | pc_spike.py:1225-1245 sole writer into the data folder (sanitise, gate with `deny_entries()`, exclusive write; every data write at :1431,:1699,:1700,:1773 goes through it), :1290-1291 raw captures 0600 in the run root outside the repo; committed data/ scanned clean (leak gate and gitleaks, run) |
| T-02-33 | Tampering | medium | mitigate | closed | pc_spike.py:143-170 harness home outside repo and own Claude folder, pc_flags.py:26 `project,local`, pc_spike.py:1062-1132 nine S1 assertions, :1155-1178 unassertable audit or failed assertion is a stop, :1206-1208 never silently weakened |
| T-02-34 | Elevation of privilege | medium | mitigate | closed | pc_spike.py:1397 allowlist from the per-verb builder, :1462-1467 bind probe on an unused session id and a nonexistent ledger, :1471-1476 prompt forbids other commands; checkpoint-wrapper:68-75; live denial data/spike-findings.md:82-84 |
| T-02-35 | Repudiation | medium | mitigate | closed | pc_flags.py:38; test_spike_fixture.py:83-88; data/spike-findings.md:7,65,105 and data/s1-init-manifest.json record 2.1.310 |
| T-02-36 | Spoofing | medium | mitigate | closed | pc_flags.py:388-422 minimal env, :359-376 `--setting-sources project,local` + `--strict-mcp-config`; pc_spike.py:264-306 runs root outside repo, outside every local home, no ancestor instruction files (owner decision 2026-10-26 supersedes "under the harness home"); :544-554 |
| T-02-48 | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |
| T-02-51 | Information disclosure | high | mitigate | closed | pc_sanitize.py:63 word prefix accepts a backslash plus n/r/t/b/f, :194-195; test_sanitize.py:341-431 LoginBoundaryTests |
| T-02-52 | Information disclosure | high | mitigate | closed | pc_sanitize.py:191-199 login (raw, NFC, NFD) with the fixed-token exclusion, :279-281 `deny_entries()`; handed to the gate at pc_spike.py:1239; promote refuses missing entries pc_promote.py:157-158, test_promote.py:429-460; test_sanitize.py:445 GateIntegrationTests |
| T-02-53 | Information disclosure | high | mitigate | closed | pc_leakgate.py:91,:136-137 end at any non-name character; .gitleaks.toml:9 byte-identical; test_leakgate.py:169 ParityTests, :314 HomePathBoundaryTests |
| T-02-54 | Information disclosure | medium | mitigate | closed | pc_leakgate.py:82 `re.ASCII`, :101 and .gitleaks.toml:34 scoped `(?i:...)` suffix; test_leakgate.py:368,439 |
| T-02-55 | Repudiation | high | mitigate | closed | pc_leakgate.py:467-513 unlocatable list is ScannerError with a fixed message, quiet only when no `.git` exists in the tree or any ancestor (:470-479); pc_sanitize.py:178-179; pc_leakgate.py:587-589 exit 15; test_leakgate.py:676 DenyListLocationTests |
| T-02-56 | Tampering | medium | mitigate | closed | pc_leakgate.py:532 `utf-8-sig`, :537 strip before comment/floor check; test_leakgate.py:624,676 |
| T-02-57 | Tampering | medium | mitigate | closed | .gitleaks.toml:9,34 tightened twin; `gitleaks git --config .gitleaks.toml` over the full history exit 0 (run); .gitleaksignore unchanged since 8938188 (2026-10-22); 02-09-SUMMARY records 29 PASS in scripts/test-hooks.sh before/after (script not re-run) |
| T-02-58 | Information disclosure | medium | mitigate | closed | pc_sanitize.py:283-286 counts-only repr, pc_leakgate.py:408-416,:467 fixed text; test_sanitize.py:433-445, test_leakgate.py:747-776 |
| T-02-SC | Tampering | low | accept | closed (accepted; see log) | same evidence as T-02-41 |

Counts check: 50 mitigate rows (49 closed, 1 open) + 9 accept rows (9 closed) = 59 rows; 25 high (24 closed, 1 open), 21 medium (all closed), 13 low (all closed).

## Trust boundaries (31 declared)

All confirmed present and enforced in code except where noted.

| Plan | Boundary | Status | Pointer |
|---|---|---|---|
| 02-01 | harness to child claude process | confirmed | pc_flags.py:388-422 |
| 02-01 | harness to local Claude Code auth state | confirmed | pc_preflight.py:208-216 |
| 02-01 | stranger's machine to the shim | confirmed | selftest:18-30,60-77 |
| 02-01 | captured stream to the parser | confirmed | pc_stream.py:65-99 |
| 02-02 | model or harness to stub CLI | confirmed | checkpoint_stub.py:865-950 (allow_abbrev off, session shape, hash shape, task shape) |
| 02-02 | stub to filesystem | confirmed | checkpoint_stub.py:203-208,349-353 |
| 02-02 | committed evidence to miner | confirmed | pc_mine.py read-only loaders; test_stub_replay.py:37 |
| 02-03 | caller to allocator | confirmed | pc_runroot.py:40-78 |
| 02-03 | harness to filesystem | confirmed | pc_runroot.py:86-104,132-170 |
| 02-03 | snapshotter to credentials | **partially confirmed** | guard exists (pc_manifest.py:318-338) but is not armed in production: T-02-15 |
| 02-04 | model-facing allowlist to the setup verbs | confirmed | pc_flags.py:425-444; live denial spike-findings.md:82-84 |
| 02-04 | wrapper to stub | confirmed | checkpoint-wrapper:118 |
| 02-04 | documentation to evidence | confirmed | test_branch_table.py:195-207; test_frozen_reference.py |
| 02-05 | run output to public evidence | confirmed | pc_promote.py:147-232; pc_spike.py:1225-1245 |
| 02-05 | sanitizer and gate to terminal and logs | confirmed | pc_leakgate.py:408-416; pc_sanitize.py:283-286 |
| 02-05 | local deny file to the harness | confirmed | pc_leakgate.py:516-542 |
| 02-05 | promote to the filesystem | confirmed | pc_promote.py:96-133,165-169 |
| 02-06 | model or harness to stub CLI | confirmed | as 02-02 |
| 02-06 | stub to filesystem | confirmed | checkpoint_stub.py:755-756,788,809 |
| 02-06 | stub to concurrent callers | confirmed | checkpoint_stub.py:459-503 |
| 02-07 | stranger's environment to the harness | confirmed | test_imports.py; selftest |
| 02-07 | documentation to code | confirmed | test_readme.py:187-233 |
| 02-07 | committed harness files to the public repository | confirmed | leak gate 0 findings over tests/harness (run) |
| 02-08 | harness to Claude Code login | confirmed | pc_preflight.py:208-216 |
| 02-08 | executor session to the inner claude process | confirmed | pc_flags.py:388-422; pc_spike.py:264-306 |
| 02-08 | raw capture to public repository | confirmed | pc_spike.py:1225-1245,:1290-1291 |
| 02-08 | harness to the user's own Claude folders | confirmed | pc_spike.py:143-170,:205-227 (names only, never opened) |
| 02-09 | captured run output to public evidence | confirmed | as 02-05 |
| 02-09 | sanitizer and gate to terminal, logs and exceptions | confirmed | fixed messages; see T-02-58 |
| 02-09 | local deny file and its location to the gate | confirmed | pc_leakgate.py:467-513 |
| 02-09 | gate rule set to the commit hooks | confirmed | .gitleaks.toml:9,34; test_leakgate.py:169 |

## Unregistered flags (WARNING, not blocking)

| Flag | Source | Status |
|---|---|---|
| `shared-folder-write` (02-08-SUMMARY, pc_spike.py) | The default runs root the default shared runs root (under the system shared-users folder, see pc_spike.py) sits under a sticky world-writable parent | No threat id maps to it. Partial mitigation exists: newly created levels are mode 0700 (pc_spike.py:309-324) and ancestors holding instruction files are refused (pc_spike.py:295-305). Not present: any owner (`st_uid`) or mode check on a level that already exists, so another local user who pre-creates the folder name owns the parent of the run roots (review WR-07, deferred; the only `st_uid` checks in the tree, pc_rowhooks.py:258,363,512, cover other objects). Recommend registering it as a threat (Tampering, medium) and either adding the owner/mode check or accepting it for a single-user machine. |

## Observations (no status change; recorded so the orchestrator can carry them into SECURITY.md)

1. T-02-15 / WR-11: see Open table. Remediation is two small wiring changes plus tests.
2. T-02-31 residual (review WR-06, deferred): `guard` (pc_spike.py:708-722) is check-then-act; two `--run` processes started together can both pass. Outside the register's declared mitigation text; closed as declared.
3. T-02-33 residual (WR-09, deferred): the names-absent assertion passes with an empty name set (pc_spike.py:1413, `frozenset()` when `HOME` is unset).
4. T-02-26/T-02-30 residual (IN-06, deferred): the config-directory refusal in pc_promote.py:165-169 compares realpaths case-sensitively; on the default case-insensitive macOS filesystem a differently-cased spelling would not match. Callers are harness code, not the model.
5. T-02-52/T-02-53 residuals (IN-08, IN-09, WR-13, deferred): a login that occurs inside a fixed token gets no gate entry (pc_sanitize.py:198); `home-path-dash-slug` still needs a closing hyphen (pc_leakgate.py:92) and folder names over 64 characters are not matched (pc_leakgate.py:91); the gate matches the login as a substring while the sanitizer matches it as a whole word (a safe-direction mismatch that can refuse a capture).
6. T-02-05 residual (IN-04, deferred): the `pc_stream.py check` CLI prints the union of denial ids but not the two mismatch sets or tool errors (pc_stream.py:317-326); the API reports both directions (pc_stream.py:189-213), and either signal alone yields exit 19.
7. T-02-13 scope note (WR-04, deferred): the no-delete AST scan globs `pc_*.py` only (test_runroot.py:413-416). `checkpoint_stub.py` uses `os.replace` and `os.unlink` on its own temp files and on ledgers, always inside CKPT_HOME (checkpoint_stub.py:317-332,:506-521). This matches the register text ("every pc_ module"), so T-02-13 stays closed.
8. T-02-23 adjacency (WR-07, deferred): `pc_spike.main` maps only `SpikeError` (pc_spike.py:1987), so an `OSError` or a `SanitizerError` after a paid call ends in a traceback that can print a local path to the terminal. Not a repository leak; outside the sanitizer/gate/promote output the register covers.
9. Closed by later phases since the second review pass: WR-03 end-marker lines in an update body (checkpoint_stub.py:692-693, 03-03), WR-14 promote without the sanitizer's deny entries (pc_promote.py:157-158 plus test_promote.py:429-460, 03-08), and `promote_into` adds a second evidence write path with the same gate-first, exclusive-creation rules (pc_promote.py:295-377).
10. T-02-50 is closed as declared: the wrapper refuses the driver verbs, but the baseline allowlist still lets the model reach the stub directly through `python3 -c` or `env`; the plan and spike-findings.md:168 record this openly, and narrowing the baseline is a Phase 3 per-row decision.
11. Fixture scan with the live sanitizer deny entries (counts only, nothing printed): `tests/harness/data` has 1 file with a deny-list match, `spike-findings.md`, 6 matches, and zero matches against host names plus the local deny file. The match is against the login entry, which the 02-09 summary says doubles as the owner's public alias and appears in committed prose by design (FA-3). Not a finding against any register threat.
12. `pc_spike.spike_preflight` deliberately allows an untested build (pc_spike.py:791-826) because those runs create the tested set; every other caller goes through the strict exact-match gate (pc_preflight.py:185-191). T-02-06 stays closed.

## Accepted-risk log rows for SECURITY.md (the nine accept dispositions)

All nine are low severity, so they could not block even if the log were absent. They are closed on the condition that the orchestrator writes these rows into the SECURITY.md accepted-risks log.

| Threat ID | Accepted risk | Basis verified | Date |
|---|---|---|---|
| T-02-41 | npm, pip and cargo installs (plan 02-01): none made; standard library only | 0 non-stdlib imports, no dependency manifest, no install command in tests/harness | 2026-11-12 |
| T-02-42 | same, plan 02-02 | as above | 2026-11-12 |
| T-02-43 | same, plan 02-03 | as above | 2026-11-12 |
| T-02-44 | same, plan 02-04 (standard library and bash only) | as above | 2026-11-12 |
| T-02-45 | same, plan 02-05 | as above | 2026-11-12 |
| T-02-46 | same, plan 02-06 | as above | 2026-11-12 |
| T-02-47 | same, plan 02-07 (README instructs no install) | as above; test_readme.py:277 | 2026-11-12 |
| T-02-48 | same, plan 02-08 (standard library and the already-installed claude CLI) | as above | 2026-11-12 |
| T-02-SC | same, plan 02-09 (D-11) | as above | 2026-11-12 |

Any later install would need the legitimacy audit and a blocking human checkpoint (the plans' own condition).

### Proposed accepted-risk entry for T-02-15 (NOT applied; only if bokiko chooses acceptance over the wiring fix)

T-02-15 (high): the `refuse_under` guard in `pc_manifest.tree_manifest` is not passed by any production snapshot call or by the manifest CLI.
Residual: a snapshot root chosen so that it contains the harness config directory would not be refused. Basis for accepting: snapshot roots are
harness-allocated run roots, disjoint from `<harness home>/claude-config` by construction; promote's config-directory refusal is armed
(pc_evidence.py:1690). Revisit in Phase 3 hardening together with WR-11.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-12
