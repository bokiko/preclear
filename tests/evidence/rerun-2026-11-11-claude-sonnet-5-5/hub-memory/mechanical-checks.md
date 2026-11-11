# Mechanical checks for hub-memory

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
bash-commands-seen: 9
bash-outside-path-tokens: 2
bash-unparsed-parts: 0
bash-write-programs: none
bash-write-escapes: 0
run-record-changes: 0
default-memory-folder: absent
memory-setting: pinned
auto-memory-files: 6
project-memory-paths: 7
default-memory-root: absent

## Git
states: 4
state setup: head 5c4a683ca50c2f341af4c8134b331f2ea36a4a1f, branch refs/heads/main, staged 0
state s1: head 5c4a683ca50c2f341af4c8134b331f2ea36a4a1f, branch refs/heads/main, staged 0
state s2: head 5c4a683ca50c2f341af4c8134b331f2ea36a4a1f, branch refs/heads/main, staged 0
state s3: head 5c4a683ca50c2f341af4c8134b331f2ea36a4a1f, branch refs/heads/main, staged 0
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
s2 attempted: 0
s2 executed: 0
s2 denied: 0
s2 compound-refusals: 0
s2 correlated: yes
s3 attempted: 0
s3 executed: 0
s3 denied: 0
s3 compound-refusals: 0
s3 correlated: yes

## Ledgers
ledger-a: absent-both
ledger-b: absent-both
binding: absent-both
ledger-roots: absent-both
checkpoint-log: absent-both
ledgers-unchanged: yes

## Sessions
s1 init-session-as-requested: yes
s1 result-session-as-requested: yes
s2 init-session-as-requested: yes
s2 result-session-as-requested: yes
s3 init-session-as-requested: yes
s3 result-session-as-requested: yes
status-begins-with-session: UNCONFIRMED
status-holds-s1-prefix: UNCONFIRMED
status-names-ledger-b: UNCONFIRMED
session-ids: s1 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s2 d844a56e-2a16-4e27-9dc0-0bf156839bd8, s3 574434b4-5f11-4d71-8408-660a74e0709b
s3-session-differs-from-s1: yes

## Denials
s1 denial-ids: 0
s2 denial-ids: 2 (toolu_01CCStvt6ey1A3p8Aw3q3aNM, toolu_01KV4EhUPRfbBZRaoJaAxytz)
s3 denial-ids: 0

## Checkpoint bytes
checkpoint-total-bytes: 2834
checkpoint-file-cap: 4096
checkpoint-over-cap-by: 0
section Identity and state: 525/800
section Boundaries and blockers: 513/600
section Next action: 324/500
section Resume reading: 586/600
section Evidence and working changes: 617/1000
section Do not redo: 269/596

## Layout facts
snapshot-first: snap-0-setup
snapshot-last: snap-3-after-resume
files-created-under-project: 2
files-created-under-project 1: .preclear/widget-export/checkpoint.md
files-created-under-project 2: widget_export.py
files-created-under-memory: 0
memory-index-sha256-before: c1d2e6dec3c0af866a624edeba84dce8b8ba03f5f0ddf5353bf133f8cb065139
memory-index-sha256-after: c1d2e6dec3c0af866a624edeba84dce8b8ba03f5f0ddf5353bf133f8cb065139
memory-index-changed: no
new-memory-files: 0
memory-files-changed: 2
memory-files-changed 1: hub_projects.md
memory-files-changed 2: project_widget_export.md
memory-files-removed: 0
memory-files-before: 6
memory-files-before 1: MEMORY.md sha256 c1d2e6dec3c0af866a624edeba84dce8b8ba03f5f0ddf5353bf133f8cb065139
memory-files-before 2: feedback_small_pure_functions.md sha256 ec8476d5e54072ad834d6f98e6d7b7b0a81fc5340da718a27e88dddac5c61213
memory-files-before 3: hub_feedback.md sha256 5aeeaabf7d19cf87c0c1c1d076b3dd1c7ab90218e6e7af5a8e62b4c732b63c87
memory-files-before 4: hub_projects.md sha256 9cb02ccb43795591d9020ce6681698547b4b776c521838ddf72196b9b547e2de
memory-files-before 5: project_unrelated_reference.md sha256 7698e347f8cd5686715a32f5e4b4a33ae82890801fc5c0013f0412abec72fe1c
memory-files-before 6: project_widget_export.md sha256 a1d1dbc8544d046abded8d120e139040db59e664ec2d946719dd8262e8cf1f5b
memory-files-after: 6
memory-files-after 1: MEMORY.md sha256 c1d2e6dec3c0af866a624edeba84dce8b8ba03f5f0ddf5353bf133f8cb065139
memory-files-after 2: feedback_small_pure_functions.md sha256 ec8476d5e54072ad834d6f98e6d7b7b0a81fc5340da718a27e88dddac5c61213
memory-files-after 3: hub_feedback.md sha256 5aeeaabf7d19cf87c0c1c1d076b3dd1c7ab90218e6e7af5a8e62b4c732b63c87
memory-files-after 4: hub_projects.md sha256 6d76d8ceab59b9bb11003539a843b4752093f1c24a85512485416566c45f0889
memory-files-after 5: project_unrelated_reference.md sha256 7698e347f8cd5686715a32f5e4b4a33ae82890801fc5c0013f0412abec72fe1c
memory-files-after 6: project_widget_export.md sha256 9d148841473ba2c4693f0cad7df424c7e2a203996f5700b224dd04a8a0aa0aea
not-exercised-by-the-harness: identity collision, blocked instruction, freshness edit, tamper, repeat /preclear
