# Mechanical checks for bound-ledger

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
s3 model: claude-sonnet-5-5
s3 claude-code-version: 2.1.310
s3 permission-mode: default
s3 tool-count: 26
s3 tools: Task, Bash, CronCreate, CronDelete, CronList, DesignSync, Edit, EnterWorktree, ExitWorktree, Glob, Grep, ListAgents, Monitor, NotebookEdit, PushNotification, Read, RemoteTrigger, ReportFindings, ScheduleWakeup, SendMessage, Skill, TaskStop, ToolSearch, WebSearch, Workflow, Write
s3 mcp-server-count: 0
s3 skills: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring
s3 plugins: cc-plugin-agents-md, cc-plugin-telemetry, cc-plugin-plugin-authoring
s3 agents: claude, Explore, general-purpose, Plan, statusline-setup, web-fetch
s3 slash-commands: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring, advisor, agents, auto-mode-setup, autocompact, clear, color, compact, config, output-style, context, effort, fast, focus, heapdump, init, mcp, import, model, __remote-workflow, workflow-launch-exec, reload-plugins, reload-skills, rename, ultrareview, security-review, usage-credits, extra-usage, usage, insights, recap, skill-doctor, goal, design-consent, design-revoke, list-agents, team-onboarding
s3 api-key-source: none

## Instruction audit
s1 audit-source: logger
s1 instruction-entries: user=0 project=1 local=0 managed=0 unknown=0
s1 isolation-assertions-all-hold: yes
s2 audit-source: logger
s2 instruction-entries: user=0 project=2 local=0 managed=0 unknown=0
s2 isolation-assertions-all-hold: yes
s3 audit-source: logger
s3 instruction-entries: user=0 project=1 local=0 managed=0 unknown=0
s3 isolation-assertions-all-hold: yes

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
s3 permission-mode-default: yes (init)
s3 model-pinned: yes (init)
s3 skill-preclear-present: yes (init)
s3 mcp-servers-empty: yes (init)
s3 no-non-builtin-plugins: yes (init)
s3 user-names-absent: yes (init)
s3 no-user-instruction-outside-config: yes (hook)
s3 project-claude-md-loaded: yes (hook)
s3 project-local-inside-run-root: yes (hook)
s3 memory-path-as-set: yes (init)
s3 cwd-is-project: yes (init)
s3 session-id-as-requested: yes (init)

## Write boundary
snapshot-paths-outside-approved-roots: 0
snapshot-paths: none
write-tool-paths-outside-approved-roots: 0
write-tool-paths: none
bash-commands-seen: 22
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
state setup: head 822561dd5e7f05b13a09123ef4cb03e36856c2d1, branch refs/heads/main, staged 0
state s1: head 822561dd5e7f05b13a09123ef4cb03e36856c2d1, branch refs/heads/main, staged 0
state s2: head 822561dd5e7f05b13a09123ef4cb03e36856c2d1, branch refs/heads/main, staged 0
state s3: head 822561dd5e7f05b13a09123ef4cb03e36856c2d1, branch refs/heads/main, staged 0
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
s2 attempted: 15
s2 executed: 14
s2 denied: 0
s2 compound-refusals: 1
s2 correlated: yes
s3 attempted: 0
s3 executed: 0
s3 denied: 0
s3 compound-refusals: 0
s3 correlated: yes

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
s3 init-session-as-requested: yes
s3 result-session-as-requested: yes
status-begins-with-session: yes
status-holds-s1-prefix: yes
status-names-ledger-a: yes
session-ids: s1 896198d6-f642-49bc-953b-64608d694c26, s2 896198d6-f642-49bc-953b-64608d694c26, s3 b9f578e0-6e3c-430b-84cd-239453036040
s3-session-differs-from-s1: yes

## Denials
s1 denial-ids: 0
s2 denial-ids: 6 (toolu_012Ex39Hu8Yq5gU6rr2UeBj3, toolu_01C8yYmBm4HQ8raJksvdTwd6, toolu_01KEERk9Kz9zUatzGv5thr6X, toolu_01V2ECxQZ3xwHrkDM6x6kcrv, toolu_01VbtUUxTutGVgQgPyxqEKqM, toolu_01YA76uPHxKFF1soMjTEKBeK)
s3 denial-ids: 0

## Checkpoint bytes
checkpoint-total-bytes: UNCONFIRMED

## Layout facts
snapshot-first: snap-0-setup
snapshot-last: snap-3-after-resume
ledger-a-sha256-before: 4477e63e71e132ae105bf12046a901a1adadc3bf308377c3896419a3891c5dd5
ledger-a-sha256-after: 15bb02c6dcf75275a94b1cdca24dacb190bd86a02708c2811e279b82c5efeb32
ledger-a-changed: yes
update-calls-in-wrapper-log: 7
update-calls-with-exit 0: 7
lint-after-s2: present
lint-after-s2-lines: 1
lint-after-s2-sha256: 0b38d77b86cd618b31d6110dc02a3a3de8fa73b8de72b5e504ed0a6ef7cba1f3
lint-after-s2 line 1: ledger lint OK
not-exercised-by-the-harness: identity collision, blocked instruction, freshness edit, tamper, repeat /preclear
