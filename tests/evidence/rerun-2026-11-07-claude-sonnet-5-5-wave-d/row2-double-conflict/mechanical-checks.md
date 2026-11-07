# Mechanical checks for row2-double-conflict

## Init manifest
s1 model: claude-sonnet-5-5
s1 claude-code-version: 2.1.310
s1 permission-mode: default
s1 tool-count: 26
s1 tools: Task, Bash, CronCreate, CronDelete, CronList, DesignSync, Edit, EnterWorktree, ExitWorktree, Glob, Grep, ListAgents, Monitor, NotebookEdit, PushNotification, Read, RemoteTrigger, ReportFindings, ScheduleWakeup, SendMessage, Skill, TaskStop, ToolSearch, WebSearch, Workflow, Write
s1 mcp-server-count: 0
s1 skills: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring
s1 plugins: cc-plugin-agents-md, cc-plugin-telemetry, cc-plugin-plugin-authoring
s1 agents: claude, Explore, general-purpose, Plan, statusline-setup, web-fetch
s1 slash-commands: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring, advisor, agents, auto-mode-setup, autocompact, clear, color, compact, config, output-style, context, effort, fast, focus, heapdump, init, mcp, import, model, __remote-workflow, workflow-launch-exec, reload-plugins, reload-skills, rename, ultrareview, security-review, usage-credits, extra-usage, usage, insights, recap, skill-doctor, goal, design-consent, design-revoke, list-agents, team-onboarding
s1 api-key-source: none
s2 model: claude-sonnet-5-5
s2 claude-code-version: 2.1.310
s2 permission-mode: default
s2 tool-count: 26
s2 tools: Task, Bash, CronCreate, CronDelete, CronList, DesignSync, Edit, EnterWorktree, ExitWorktree, Glob, Grep, ListAgents, Monitor, NotebookEdit, PushNotification, Read, RemoteTrigger, ReportFindings, ScheduleWakeup, SendMessage, Skill, TaskStop, ToolSearch, WebSearch, Workflow, Write
s2 mcp-server-count: 0
s2 skills: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring
s2 plugins: cc-plugin-agents-md, cc-plugin-telemetry, cc-plugin-plugin-authoring
s2 agents: claude, Explore, general-purpose, Plan, statusline-setup, web-fetch
s2 slash-commands: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring, advisor, agents, auto-mode-setup, autocompact, clear, color, compact, config, output-style, context, effort, fast, focus, heapdump, init, mcp, import, model, __remote-workflow, workflow-launch-exec, reload-plugins, reload-skills, rename, ultrareview, security-review, usage-credits, extra-usage, usage, insights, recap, skill-doctor, goal, design-consent, design-revoke, list-agents, team-onboarding
s2 api-key-source: none

## Instruction audit
s1 audit-source: logger
s1 instruction-entries: user=0 project=1 local=0 managed=0 unknown=0
s1 isolation-assertions-all-hold: yes
s2 audit-source: logger
s2 instruction-entries: user=0 project=2 local=0 managed=0 unknown=0
s2 isolation-assertions-all-hold: yes

## Assertions
s1 permission-mode-default: yes (init)
s1 model-pinned: yes (init)
s1 skill-preclear-present: yes (init)
s1 mcp-servers-empty: yes (init)
s1 no-non-builtin-plugins: yes (init)
s1 user-names-absent: yes (init)
s1 no-user-instruction-outside-config: yes (hook)
s1 project-claude-md-loaded: yes (hook)
s1 project-local-inside-run-root: yes (hook)
s1 memory-path-as-set: yes (init)
s1 cwd-is-project: yes (init)
s1 session-id-as-requested: yes (init)
s2 permission-mode-default: yes (init)
s2 model-pinned: yes (init)
s2 skill-preclear-present: yes (init)
s2 mcp-servers-empty: yes (init)
s2 no-non-builtin-plugins: yes (init)
s2 user-names-absent: yes (init)
s2 no-user-instruction-outside-config: yes (hook)
s2 project-claude-md-loaded: yes (hook)
s2 project-local-inside-run-root: yes (hook)
s2 memory-path-as-set: yes (init)
s2 cwd-is-project: yes (init)
s2 session-id-as-requested: yes (init)

## Write boundary
snapshot-paths-outside-approved-roots: 0
snapshot-paths: none
write-tool-paths-outside-approved-roots: 0
write-tool-paths: none
bash-commands-seen: 17
bash-outside-path-tokens: 0
bash-unparsed-parts: 0
bash-write-programs: none
bash-write-escapes: 0
run-record-changes: 0
default-memory-folder: absent
memory-setting: pinned
auto-memory-files: 0
project-memory-paths: 0
default-memory-root: absent

## Git
states: 4
state setup: head 80cdf0fa5f80dbdf79d04c9e7839a02d10b28905, branch refs/heads/main, staged 0
state s1: head 80cdf0fa5f80dbdf79d04c9e7839a02d10b28905, branch refs/heads/main, staged 0
state s1-arm-wrapper-conflict: head 80cdf0fa5f80dbdf79d04c9e7839a02d10b28905, branch refs/heads/main, staged 0
state s2: head 80cdf0fa5f80dbdf79d04c9e7839a02d10b28905, branch refs/heads/main, staged 0
mutations-total: 0
mutation-state-changes: 0
mutation-changed-fields: none
mutation-staged-entries: 0
mutation-executed-forms: 0

## Helper calls
s1 attempted: 0
s1 executed: 0
s1 denied: 0
s1 compound-refusals: 0
s1 correlated: yes
s2 attempted: 7
s2 executed: 7
s2 denied: 0
s2 compound-refusals: 0
s2 correlated: yes

## Ledgers
ledger-a: changed
ledger-b: absent-both
binding: unchanged
ledger-roots: unchanged
checkpoint-log: changed
ledgers-unchanged: no

## Sessions
s1 init-session-as-requested: yes
s1 result-session-as-requested: yes
s2 init-session-as-requested: yes
s2 result-session-as-requested: yes
status-begins-with-session: yes
status-holds-s1-prefix: yes
status-names-ledger-a: yes
session-ids: s1 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4, s2 128ae7fc-ba4b-47a0-aaee-55a0ca4f9ba4

## Denials
s1 denial-ids: 0
s2 denial-ids: 5 (toolu_01AarzBrTZKnGMSb3k4y74St, toolu_01CJKVeKQAb9VT3rcZTHtejB, toolu_01Eng3U75kEYtgN4tEeb8SE6, toolu_01KaS3xWtBDZBH66hZ1gMEvV, toolu_01T6fjQW9KniQzdTg2xk4pPm)

## Checkpoint bytes
checkpoint-total-bytes: 3002
checkpoint-file-cap: 4096
checkpoint-over-cap-by: 0
section Identity and state: 757/800
section Boundaries and blockers: 536/600
section Next action: 273/500
section Resume reading: 577/600
section Evidence and working changes: 595/1000
section Do not redo: 264/596
