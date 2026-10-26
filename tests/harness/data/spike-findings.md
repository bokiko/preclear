# Spike findings (plan 02-08)

These findings describe one Claude Code build only. Claude Code behaviour is version-dependent: the
captures below describe the recorded version, and the version gate refuses every other build until
spike S2 is rerun (HARN-04).

Claude Code version: 2.1.310
Model: claude-sonnet-5-5 (init.model of every capture; every call pins the full id, D-05). Phase 3 picks the matrix baseline model separately.
Date (UTC): 2026-10-26

## Spike S1: isolation

Isolation claim: strict. Each matrix run uses a harness-owned CLAUDE_CONFIG_DIR outside the repository and outside the user's own Claude config, plus --setting-sources project,local, so user-level instructions, memory and skills are absent from the run.

Isolation evidence: nine assertions, all passed on the S1 rerun (attempt 2 of 2). Asserted from the init event: permission-mode-default, model-pinned, skill-preclear-present, mcp-servers-empty, no-non-builtin-plugins, user-names-absent. Asserted from the InstructionsLoaded hook (the logger file was the source; the hook fired in print mode, so the audit was assertable and nothing was not assertable): no-user-instruction-outside-config, project-claude-md-loaded, project-local-inside-run-root. Two assertions were refined by bokiko on 2026-10-26 after attempt 1 (see "Attempt 1 and the decisions it led to"). No by-construction label is used anywhere.

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
- The hook logger file, not the stream, carried the instruction entries: with --include-hook-events the stream shows that the hook ran, and the logger records which files it loaded.

### S1 spend

| Call | Attempt | Cap (USD) | Turns cap | Outcome | Actual cost (USD) |
|---|---|---|---|---|---|
| s1 | 1 | 0.50 | 3 | success, assertions failed | 0.0599855 |
| s1 | 2 | 0.50 | 3 | success, all assertions passed | 0.0264356 |

S1 spend: 0.09 USD
