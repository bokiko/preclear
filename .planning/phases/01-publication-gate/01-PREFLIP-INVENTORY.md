# Pre-flip scan and live-repo inventory

Generated: 2026-10-22T13:46:13Z
Scanned tip: ab2e34509ed9a45af649127c8774fae9d988fa92
Gitleaks: 8.30.0
Result: PASS

| Check | Result | Detail |
|---|---|---|
| owner-clone-config | PASS | hooks path set, identity pin set |
| mirror-cloned | PASS | mirror of the source cloned |
| remote-tip-equals-head | PASS | remote main, local HEAD and mirror tip agree |
| strict-equals-accepted | PASS | strict exit 2; 15 fingerprints equal the accepted list; all in d437af2 |
| gate-clean | PASS | gate exit 0 |
| tree-clean | PASS | tree scan exit 0 |
| one-identity | PASS | 1 identity, equal to the pin |
| no-attribution-trailers | PASS | 0 matching lines |
| denylist-history | PASS | 0 added lines match |
| inventory | PASS | INVENTORY OK, 24 categories |

| Category | Expected | Observed |
|---|---|---|
| visibility | PRIVATE true | PRIVATE true |
| remote-refs | 2 refs, HEAD equals main | 2 refs, HEAD equals main |
| remote-tags | 0 | 0 |
| branches | 1 | 1 |
| tags | 0 | 0 |
| hooks | 0 | 0 |
| deploy-keys | 0 | 0 |
| issues | 0 | 0 |
| pull-requests | 0 | 0 |
| actions-runs | 0 | 0 |
| actions-workflows | 0 | 0 |
| actions-artifacts | 0 | 0 |
| actions-secrets | 0 | 0 |
| actions-variables | 0 | 0 |
| has-wiki | false | false |
| pages | HTTP 404 | HTTP 404 |
| releases | 0 | 0 |
| forks | 0 | 0 |
| collaborators | bokiko | bokiko |
| invitations | 0 | 0 |
| environments | 0 | 0 |
| deployments | 0 | 0 |
| activity-types | only branch_creation and push | only branch_creation and push |
| public-probe | 404, anonymous ls-remote refused | 404, anonymous ls-remote refused |
