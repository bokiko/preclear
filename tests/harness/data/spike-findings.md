# Spike findings (plan 02-08)

These findings describe one Claude Code build only. Claude Code behaviour is version-dependent: the
captures below describe the recorded version, and the version gate refuses every other build until
spike S2 is rerun (HARN-04).

Claude Code version: 2.1.310
Model: claude-sonnet-5-5 (init.model of every capture; every call pins the full id, D-05). Phase 3 picks the matrix baseline model separately.
Date (UTC): 2026-10-26

## Spike S1: isolation

Isolation claim: strict. Each matrix run uses a harness-owned CLAUDE_CONFIG_DIR outside the repository and outside the user's own Claude config, plus --setting-sources project,local, so user-level instructions, memory and skills are absent from the run.

Isolation evidence: nine assertions, all passed on the S1 rerun (attempt 2 of 2). Asserted from the init event: permission-mode-default, model-pinned, skill-preclear-present, mcp-servers-empty, no-non-builtin-plugins, user-names-absent. Asserted from the InstructionsLoaded hook (the logger file was the only source, because the stream carried no hook events; the hook fired in print mode, so the audit was assertable and nothing was not assertable): no-user-instruction-outside-config, project-claude-md-loaded, project-local-inside-run-root. Two assertions were refined by bokiko on 2026-10-26 after attempt 1 (see "Attempt 1 and the decisions it led to"). No by-construction label is used anywhere.

Scratch login probe: the first zero-token auth-check on the freshly created harness-owned config directory ran on 2026-10-25T15:19:14Z and reported loggedIn false with exit 12 (BLOCKED), and that call created the directory (created true); the check sends no prompt, so its observed spend is 0.00 USD. The probe record is append-only under the harness home. After bokiko's one manual login the latest probe reported loggedIn true with exit 0 (created false). The login itself is therefore shown by those two records, not asserted.

### One-time login

A subscription user must run one manual login into the harness-owned config directory (D-03). The harness runs claude with its own config folder, and a scratch config folder loses the login, so the folder needs a login of its own. bokiko runs it in his own terminal with `CLAUDE_CONFIG_DIR=<harness home>/claude-config claude auth login`. The harness never reads, writes, copies or prints credential files; it reads one yes-or-no answer (loggedIn) from `claude auth status`. If the login is lost, the preflight reports BLOCKED (exit 12) with the same instruction and never falls back to the user's own config. Deleting the config directory does not delete the login: the credential sits in the macOS Keychain, keyed to that folder, and survives the delete, so the folder should not be deleted casually. Where the login credentials live on Linux (a file under the config directory instead of the Keychain) is documented but untested here.

### Assertion table (rerun, attempt 2)

| Assertion | How asserted | Result | Counts |
|---|---|---|---|
| permission-mode-default | init | pass | permissionMode is default |
| model-pinned | init | pass | init.model equals the pinned id |
| skill-preclear-present | init | pass | preclear is in init.skills (the project install) |
| mcp-servers-empty | init | pass | 0 MCP servers |
| no-non-builtin-plugins | init | pass | 3 plugins, all with source ending @builtin, 0 others |
| user-names-absent | init | pass | 193 user names listed locally (1 excluded: preclear), 0 leak hits, 2 binary-defined collision entries (1 distinct name) |
| no-user-instruction-outside-config | hook | pass | 0 User entries |
| project-claude-md-loaded | hook | pass | the fixture CLAUDE.md is the one Project entry |
| project-local-inside-run-root | hook | pass | 1 Project, 0 Local, 0 Managed, 0 unknown entries, all inside the run root |

Recorded without asserting: apiKeySource none; init.effort absent (the key is not in the init event of this build); 20 skills, 56 slash commands, 5 agents, 27 tools; memory_paths holds one auto-memory folder inside the run root; cwd is the project folder inside the run root. The frozen lists are in `s1-init-manifest.json`.

### Attempt 1 and the decisions it led to

Attempt 1 ran with the run root under the harness home, which sits inside the user's home folder. Three assertions failed and the driver stopped with exit 11 and wrote nothing:

1. project-local-inside-run-root failed, a real isolation leak. The hook logged 8 instruction entries, all typed Project: the fixture CLAUDE.md and 7 files from the user's own global Claude folder (its CLAUDE.md and 6 rule files). Claude Code walks up from the working directory and loads the .claude/CLAUDE.md and .claude/rules files of every ancestor folder as Project instructions, so a run root below a home folder loads that user's global rules even though CLAUDE_CONFIG_DIR and --setting-sources were set. This is the reason the runs root must not be under a home folder. Fix (bokiko, 2026-10-26): run roots live under a separate runs root outside every home folder, in the shared users folder by default, overridable with PRECLEAR_RUNS_ROOT. The config directory and the login stay in the harness home, so no new login was needed, and nothing in the user's own Claude folder was moved or deleted. The driver now refuses a runs root that is inside any local user's home folder, inside the repository or the user's Claude folder, or below an ancestor folder that holds an instruction file or folder (zero tokens, tested). The rerun loaded exactly one Project entry, inside the run root. Phase 3 and Phase 4 must place their run roots under the same kind of location; where exactly is an open item for those phases.
2. plugins-empty failed because init.plugins lists 3 plugins bundled with this build (cc-plugin-agents-md, cc-plugin-telemetry and cc-plugin-plugin-authoring, all with source ending @builtin). Refinement (bokiko, 2026-10-26): the assertion is now "no plugin whose source is not @builtin" (id no-non-builtin-plugins), and the built-in list is recorded in the baseline of the frozen S1 init manifest.
3. user-names-absent failed with 1 hit. Refinement (bokiko, 2026-10-26): a name that the Claude binary itself defines is a collision with a bundled skill or command, not a leak. The check excludes the name preclear (the user's own skill set has a skill of that name and the project install adds another, so it cannot signal contamination) and counts binary-defined collisions separately. This run had 1 distinct colliding name, which appears twice (once in skills and once in slash commands); the name is not printed. A name the binary does not define still fails the assertion. The init event lists 20 skills, not the 193 user names, so the user's skill set is not loaded.

### Corrections and confirmations made before the run (zero tokens)

- `--max-turns` is absent from `claude --help` on this build but is defined in the binary as a hidden option; the real run accepted it. `--include-hook-events`, `--strict-mcp-config` and `--effort` appear in `--help`.
- The InstructionsLoaded entry shape that `render_settings` emits (a nested hooks list with a command) and the hook payload (hook_event_name, file_path, memory_type of User, Project, Local or Managed, and load_reason) were confirmed against the installed binary's own schema and by the hook firing in print mode. The hooks documentation page was not fetched because the run is limited to the Claude Code calls themselves.
- The hook logger file was the only source of the instruction entries: with --include-hook-events accepted, the stream of this build still carried no hook event of any kind (it held init, assistant, rate-limit and result events only), so the audit source was the logger file and the stream was not a source.

### S1 spend

| Call | Attempt | Cap (USD) | Turns cap | Outcome | Actual cost (USD) |
|---|---|---|---|---|---|
| s1 | 1 | 0.50 | 3 | success, assertions failed | 0.0599855 |
| s1 | 2 | 0.50 | 3 | success, all assertions passed | 0.0264356 |

S1 spend: 0.09 USD

## Spike S2: stream shape and the policy probe

Both captures ran under the exact matrix flag set (no hook events), under the harness-owned config
directory, with the run roots in the runs root outside every home folder. Claude Code version: 2.1.310
in the init event of S1, S2a and S2b and in `claude --version` (the tested-version set holds exactly that
one build).

### Probe table (seven commands, expectations written before the run)

`<helper>` is the sanitized wrapper path and `<run>` the sanitized run root. The observed column is
derived from the two structured denial signals only; a reply that contains the word denied is never read.

| Probe | Command | Expected | Observed | tool_use id | is_error | permission_denied event | permission_denials entry |
|---|---|---|---|---|---|---|---|
| `wrapper-status` | `<helper> status` | allowed | allowed | toolu_01LqiJcfmQsu4cAApxSEExBC | false | false | false |
| `git-status` | `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` | allowed | allowed | toolu_01PceNNfxUWf4ntAbdsx5WK2 | false | false | false |
| `pwd` | `pwd -P` | allowed | allowed | toolu_01NLffYbDxGqRXPJ4RrkBYvG | false | false | false |
| `pwd-and-status` | `pwd -P && <helper> status` | allowed | allowed | toolu_01V5ETsbqSWveRGmTsxwdceb | false | false | false |
| `pwd-and-echo` | `pwd -P && echo done` | denied | allowed | toolu_01VNyqAf3cqDBVcCtEyQRrwg | false | false | false |
| `variable-expansion` | `wc -c "$PWD/CLAUDE.md"` | denied | allowed | toolu_012LuhSNvKv9GJfj6NXDnBx9 | false | false | false |
| `wrapper-bind` | `<helper> bind --ledger <run>/ckpt/ledgers/no-such-ledger.md --session aaaaaaaa-0000-4000-8000-000000000001` | denied | denied | toolu_018eWDxbioNagyWtW25pYwrx | true | true | true |

The denied wrapper bind is the live proof of STUB-06's first layer: the binary refused it, with the
permission_denied event and the result.permission_denials entry naming the same tool_use id, and the
tool result was an error. The two signals agreed on every row (one denied row, one id in both).

### Disagreements between the matcher model and the binary

Two probe rows were allowed by the binary although both the expectation written before the run and the
matcher model said denied. Neither is a heuristic refusal, and the model was left as it is: it is
deliberately conservative, and the labels flag both rows as outside the model.

- `pwd-and-echo`: expectation corrected to allowed. The binary allowed echo although no allow rule names it,
  because echo belongs to the binary's built-in read-only command set, which the model does not cover.
- `variable-expansion`: expectation corrected to allowed for this one form. The binary allowed a
  double-quoted $PWD in a wc call that the baseline rule for wc covers, while the model treats every
  expansion as a denial. The committed evidence of 2026-10-20 shows a braced variable and other
  plain variables refused, so only this form is known to be allowed.

No probe was refused by the binary where the model said allowed (no heuristic refusals), and the model
agrees with the binary on the other five rows. No placeholder for an opaque value was needed: the Python
gate and gitleaks found nothing in the sanitized fixtures.

### Stream facts (2.1.310)

- Event types seen in S2a: system init (1), assistant (10), user (7), system thinking_tokens (2),
  rate_limit_event (1), system permission_denied (1), result success (1). S2b: init, assistant,
  rate_limit_event and result. No hook events appear without --include-hook-events.
- `--verbose` is required with `--print` and stream-json: the verbose probe (no --verbose, one turn, the
  prompt x) was refused with exit code 1, nothing on stdout and the message "Error: When using --print,
  --output-format=stream-json requires --verbose" on stderr, before any model call. This confirms the
  pinned pair.
- Literal permissionMode in init: default. apiKeySource: none. memory_paths: one auto-memory folder inside
  the run root. effort: absent from the init event (the key is not present on this build, although
  --effort high was accepted). tools: 27 names (the list is in the init manifest).
- permission_denied system event fields: type, subtype, tool_name, tool_use_id, decision_reason_type
  (other), decision_reason and message (This command requires approval), uuid, session_id.
- result.permission_denials entry fields: tool_name, tool_use_id, tool_input (command and description).
- result fields include subtype, is_error, num_turns, terminal_reason (completed), stop_reason, session_id,
  total_cost_usd, usage, modelUsage, duration_ms and duration_api_ms. S2a took 8 turns. usage fields:
  input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens, output_tokens_details,
  server_tool_use, service_tier, cache_creation, inference_geo, iterations, speed, fallback_credit.

### Session-id handling

S2a init.session_id equals the requested id: yes
S2a result.session_id equals the requested id: yes
S2b init.session_id equals the requested id: yes
S2b result.session_id equals the requested id: yes

`--resume` with the S2a session id was honoured: the S2b init and result reported that same session in the
same run root, and the resumed turn read the earlier conversation from cache. In S2a the wrapper's status
output, run by the model's Bash tool, named the bound session by its leading characters, which are the
requested id's. The resumed turn itself carried no tool call by design (the prompt asks for one word), so
the resumed Bash tool reporting the same session through the wrapper's status was not observed.

### Flag confirmations and corrections

Rows now marked S1 (isolation capture): prompt on stdin, -p, --output-format, --setting-sources,
--settings, --permission-mode, --model, --max-turns, --max-budget-usd, --strict-mcp-config, --effort,
--include-hook-events, CLAUDE_CONFIG_DIR. Rows now marked S2: --verbose, --session-id, --resume,
--allowedTools, CKPT_HOME. No flag was rejected by the build, so none was removed. Rows left at research
were not exercised (the never-passed flags, DISABLE_AUTOUPDATER and CLAUDE_CODE_SUBPROCESS_ENV_SCRUB).
Corrections to row text: --max-turns is accepted although hidden from --help and its limit was not reached;
--effort is accepted but absent from init; --include-hook-events is accepted but surfaced no hook events.

### Spend

| Call | Attempt | Cap (USD) | Turns cap | Outcome | Cost (USD) |
|---|---|---|---|---|---|
| s1 | 1 | 0.50 | 3 | success, assertions failed | 0.0599855 |
| s1 | 2 | 0.50 | 3 | success, assertions passed | 0.0264356 |
| verbose | 1 | 0.05 | 1 | refused before any model call, no result event | 0.05 (counted at its cap) |
| s2a | 1 | 1.00 | 12 | success | 0.0576893 |
| s2b | 1 | 0.50 | 2 | success | 0.0602973 |

The exact sum is 0.2544077 USD with the verbose probe at its cap, because no result event reported a cost
for it; the driver shows ledger totals rounded up to cents.

Total spend: 0.26 USD

### Not asserted

- Refusals that are heuristics of the binary and not rules (none were observed in this probe).
- Where the login credentials live on Linux (a file under the config directory instead of the Keychain):
  documented, untested here.
- The indirect routes, which the live probe did not exercise: an env-prefixed wrapper bind is allowed by
  the baseline's env rule under the matcher model, was not probed live, and is refused by the wrapper
  with exit 71, as are python3 -c, awk and find launches of the driver verbs; the zero-token proof is in
  plan 02-04.
- The behaviour at --max-turns and --max-budget-usd limits, the effect of DISABLE_AUTOUPDATER and
  CLAUDE_CODE_SUBPROCESS_ENV_SCRUB, managed-policy instruction files (none were present: 0 Managed
  entries), and anything on another Claude Code build.
- Where Phase 3 and Phase 4 place their run roots is open: they must lie outside every home folder, as
  stated under Attempt 1 above, and the model for the matrix baseline is chosen in Phase 3 (D-05).
