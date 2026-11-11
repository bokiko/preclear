# Mechanical checks for row12-frozen-handoff

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
s4 model: claude-sonnet-5-5
s4 claude-code-version: 2.1.310
s4 permission-mode: default
s4 tool-count: 26
s4 tools: Task, Bash, CronCreate, CronDelete, CronList, DesignSync, Edit, EnterWorktree, ExitWorktree, Glob, Grep, ListAgents, Monitor, NotebookEdit, PushNotification, Read, RemoteTrigger, ReportFindings, ScheduleWakeup, SendMessage, Skill, TaskStop, ToolSearch, WebSearch, Workflow, Write
s4 mcp-server-count: 0
s4 skills: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring
s4 plugins: cc-plugin-agents-md, cc-plugin-telemetry, cc-plugin-plugin-authoring
s4 agents: claude, Explore, general-purpose, Plan, statusline-setup, web-fetch
s4 slash-commands: preclear, deep-research, design, design-sync, dataviz, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, doctor, loop, schedule, claude-api, workflow-authoring, run, run-skill-generator, plugin-authoring, advisor, agents, auto-mode-setup, autocompact, clear, color, compact, config, output-style, context, effort, fast, focus, heapdump, init, mcp, import, model, __remote-workflow, workflow-launch-exec, reload-plugins, reload-skills, rename, ultrareview, security-review, usage-credits, extra-usage, usage, insights, recap, skill-doctor, goal, design-consent, design-revoke, list-agents, team-onboarding
s4 api-key-source: none

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
s4 audit-source: logger
s4 instruction-entries: user=0 project=2 local=0 managed=0 unknown=0
s4 isolation-assertions-all-hold: yes

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
s4 permission-mode-default: yes (init)
s4 model-pinned: yes (init)
s4 skill-preclear-present: yes (init)
s4 mcp-servers-empty: yes (init)
s4 no-non-builtin-plugins: yes (init)
s4 user-names-absent: yes (init)
s4 no-user-instruction-outside-config: yes (hook)
s4 project-claude-md-loaded: yes (hook)
s4 project-local-inside-run-root: yes (hook)
s4 memory-path-as-set: yes (init)
s4 cwd-is-project: yes (init)
s4 session-id-as-requested: yes (init)

## Write boundary
snapshot-paths-outside-approved-roots: 0
snapshot-paths: none
write-tool-paths-outside-approved-roots: 0
write-tool-paths: none
bash-commands-seen: 15
bash-outside-path-tokens: 3
bash-unparsed-parts: 0
bash-write-programs: sha256sum=1
bash-write-escapes: 0
run-record-changes: 0
default-memory-folder: absent
memory-setting: pinned
auto-memory-files: 2
project-memory-paths: 0
default-memory-root: absent

## Git
states: 6
state setup: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
state s1: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
state s2: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
state s2-append-plan-note: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
state s3: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
state s4: head 2e44702137af1166e157bc1162076b95c188d11d, branch refs/heads/main, staged 0
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
s4 attempted: 0
s4 executed: 0
s4 denied: 0
s4 compound-refusals: 0
s4 correlated: yes

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
s4 init-session-as-requested: yes
s4 result-session-as-requested: yes
status-begins-with-session: UNCONFIRMED
status-holds-s1-prefix: UNCONFIRMED
status-names-ledger-b: UNCONFIRMED
session-ids: s1 36ffc8c3-bb43-4a3f-87ca-00de30e41ca9, s2 36ffc8c3-bb43-4a3f-87ca-00de30e41ca9, s3 fcd43228-5751-47dd-b25a-d3d479ce37ef, s4 fcd43228-5751-47dd-b25a-d3d479ce37ef
s3-session-differs-from-s1: yes

## Denials
s1 denial-ids: 0
s2 denial-ids: 5 (toolu_015ms5H8mxV6Bn5k9RbKjiFy, toolu_017rz9qLWehRv6owoNA85tZ3, toolu_01LihcvCK1yoUj73uQzgsfMN, toolu_01VyLtDwUWv3vqLya2qBf9EF, toolu_01WzDotWT8sCa6qPvRkvVtsi)
s3 denial-ids: 0
s4 denial-ids: 3 (toolu_01959D8dAV77r3ohpziMUXXN, toolu_01UzroimjWF4g4k3YNgn4Lcz, toolu_01VVkuenrGgjPLbnrnmA4Rn1)

## Checkpoint bytes
checkpoint-total-bytes: 3239
checkpoint-file-cap: 4096
checkpoint-over-cap-by: 0
section Identity and state: 625/800
section Boundaries and blockers: 552/600
section Next action: 366/500
section Resume reading: 527/600
section Evidence and working changes: 881/1000
section Do not redo: 288/596

## Frozen copy
snap-2-after-preclear: checkpoint widget-export/checkpoint.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-2-after-preclear: frozen-copies 1
snap-2-after-preclear: frozen-copy widget-export/checkpoint-20261111T070840Z-k7q3.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-2b-after-external-plan-edit: checkpoint widget-export/checkpoint.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-2b-after-external-plan-edit: frozen-copies 1
snap-2b-after-external-plan-edit: frozen-copy widget-export/checkpoint-20261111T070840Z-k7q3.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-3-after-resume: checkpoint widget-export/checkpoint.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-3-after-resume: frozen-copies 1
snap-3-after-resume: frozen-copy widget-export/checkpoint-20261111T070840Z-k7q3.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
snap-4-after-refresh: checkpoint widget-export/checkpoint.md sha256 0969ac53bae2a265f2386f99bf33cd7f30f17c4a99f4c1b186ba20faa455dbf4
snap-4-after-refresh: frozen-copies 1
snap-4-after-refresh: frozen-copy widget-export/checkpoint-20261111T070840Z-k7q3.md sha256 beb313a9eabf756ddb5a2a8c8dbf82cfdb655017e1d52192a0156810cf5c0ef3
frozen-copy-names-in-any-snapshot: 1
frozen-copy widget-export/checkpoint-20261111T070840Z-k7q3.md: held-in-snapshots 4 of 4, digest-same-in-every-snapshot-that-holds-it yes
