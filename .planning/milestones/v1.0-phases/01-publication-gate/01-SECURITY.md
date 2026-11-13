---
phase: "01"
slug: "publication-gate"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-12"
---
# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail. Written retroactively on 2026-11-12 by /gsd-secure-phase from the plans' threat models and the security auditor's verdict; the implementation was not changed.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| developer or agent shell to git client | commit identity, commit messages and tags are chosen by whoever runs git, including via environment overrides | see description |
| local clone to GitHub remote | only the pre-push hook sees what is about to leave the machine; hooks are opt-in per clone and skippable | see description |
| test script to real repository | the test script runs git operations and must never reach the real origin | see description |
| committed history to public readers | everything in the scanned range becomes world-readable at the flip | see description |
| scanner configuration to accepted findings | the accepted list decides what the gate lets through | see description |
| local machine facts to committed files | hostnames and a real name exist on the machine and must never be written into the repository | see description |
| local working copy to what GitHub holds | the working copy can differ from the remote; only a fresh mirror of the remote shows what would go public | see description |
| script to GitHub API | the tool must be read-only; a write call would change repository state without bokiko's word | see description |
| disclosure text to public readers | the README and CHANGELOG are the first things a stranger reads | see description |
| autonomous execution to GitHub | pushes and visibility changes are writes the project reserves to bokiko's explicit word | see description |
| scan time to flip time | the repository can change between the scan and the flip | see description |
| private to public | publication is the one-way door; everything in the scanned history becomes world-readable | see description |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 (01-01) | Spoofing | .githooks/checks/identity.sh (author, committer, tagger; GIT_AUTHOR and GIT_COMM | high | mitigate | pre-push compares both author and committer name-and-address plus the annotated-tag tagger to preclear.pinnedIdentity; cases identity-wrong-author-committer,... | closed |
| T-01-02 (01-01) | Information disclosure | repo-local git config with no identity (git derives an address from the machine  | high | mitigate | step 0 sets user.useConfigOnly true plus local user.name, user.email and preclear.pinnedIdentity before the first commit | closed |
| T-01-03 (01-01) | Repudiation | commit messages and public history (an agent-appended attribution trailer) | high | mitigate | .claude/settings.json attribution suppression, .claude/CLAUDE.md rule, commit-msg hook, pre-push attribution check; every committing task states no trailer a... | closed |
| T-01-04 (01-01) | Tampering | commit-time hook skip (git commit -n) | medium | mitigate | pre-push is the authoritative net (cases trailer-bypassed-prepush and leak-seed-prepush commit with the skip option and still get refused); GitHub push prote... | closed |
| T-01-05 (01-01) | Tampering | checks/leaks.sh when gitleaks is missing or crashes | high | mitigate | exit 1 when the scanner is absent; --exit-code 2 separates a finding (2) from a tool error (1) | closed |
| T-01-06 (01-01) | Information disclosure | scripts/test-hooks.sh fixtures (a fake key committed as a literal would be publi | high | mitigate | the seed is built from separate fragments at run time; --redact on every scan; no gitleaks report is committed | closed |
| T-01-07 (01-01) | Tampering | pre-push stdin parsing (ref and sha values used to build a range) | low | mitigate | every value quoted; the range is built only from a sha, fixed tokens and the remote name (ASVS V5) | closed |
| T-01-08 (01-01) | Elevation of privilege | test script pushing to the real origin | high | mitigate | origin URL asserted to start with the throwaway path before every push; case real-origin-refs-unchanged compares origin refs before and after | closed |
| T-01-26 (01-01) | Tampering | scripts/test-hooks.sh commit path (a hook-skipping or hook-less commit of the se | high | mitigate | every commit in the script goes through scratch_commit, whose first act is assert_scratch: the target's git rev-parse --show-toplevel must be non-empty, stri... | closed |
| T-01-SC (01-01, 01-02, 01-03, 01-04) | Tampering | package-manager installs | low | accept | this plan installs nothing; gitleaks, shellcheck, gh, git and python3 are already present and RESEARCH lists no npm, PyPI or crates package. Any added instal... | closed |
| T-01-09 (01-02) | Tampering | .gitleaksignore accepted list (a stale or padded list hides findings) | high | mitigate | generated from the strict run, never by hand; strict fingerprint set must equal the listed set exactly (15); only commit d437af2 and two home-path rules are ... | closed |
| T-01-10 (01-02) | Information disclosure | gitleaks reports and hook output (leaked values echoed) | high | mitigate | --redact on every run; JSON reports only in mktemp directories outside the repository; deny-list check prints counts and file names only | closed |
| T-01-11 (01-02) | Information disclosure | machine hostname or real name not matched by shape rules | medium | mitigate | denylist.sh builds entries at run time from the machine and from .git/info/preclear-deny.txt; entries are never committed or printed; verified by the denylis... | closed |
| T-01-12 (01-02) | Information disclosure | email-address rule allowlist scope | medium | mitigate | allowlist is path-scoped to .planning markdown AND the exact public address; a second allowlist covers reserved example domains only; cases identifiers-preco... | closed |
| T-01-13 (01-02) | Tampering | hooks are opt-in per clone and skippable | medium | mitigate | README states the limit plainly; pre-push is the authoritative net; the pre-flip gate (plan 01-03) asserts core.hooksPath; GitHub push protection covers secr... | closed |
| T-01-14 (01-02) | Denial of service | over-broad rules causing hook fatigue and bypass | low | mitigate | rules key on shapes with a name segment; false-positive guard case covers settings.local.json, npm specs, example addresses and bare-prefix prose | closed |
| T-01-15 (01-02) | Tampering | pre-commit with gitleaks absent (a missing scanner read as clean) | high | mitigate | pre-commit exits 1 when the scanner is missing; case fail-closed-no-scanner proves it | closed |
| T-01-16 (01-03) | Elevation of privilege | scripts/prepublish-check.sh performing a GitHub write (visibility, settings, pus | high | mitigate | read-only commands only; a whole-file grep gate for write verbs and flags must find nothing; rehearsal mode never records; the script has no flip logic | closed |
| T-01-17 (01-03) | Tampering | scanning the working copy instead of what the remote holds | high | mitigate | fresh --mirror clone of the remote; config and ignore file taken from the mirror's HEAD; default mode requires remote tip equal to local HEAD | closed |
| T-01-18 (01-03) | Information disclosure | script output or record echoing matched values or temporary paths | medium | mitigate | --redact, reports kept in mktemp directories outside the repository, counts and booleans only, no temp path in the record, record created exclusively | closed |
| T-01-19 (01-03) | Information disclosure | disclosure text introducing a home path, hostname, address or attribution | medium | mitigate | the pre-commit hook and a staged gitleaks run cover both files; the text names no address | closed |
| T-01-20 (01-03) | Repudiation | public docs overstating acceptance (carried-forward rows, shipped digest never r | medium | mitigate | the disclosure states only measured facts, each re-verified against the evidence tree; the historical evidence README is not edited; publication of the diges... | closed |
| T-01-21 (01-04) | Elevation of privilege | accidental visibility flip by an autopilot, a script or a subagent | critical | mitigate | the flip is in no auto action and no script; the steps are released only by the blocking-human decision checkpoint (task 3) and run only in the blocking-huma... | closed |
| T-01-22 (01-04) | Tampering | time of check to time of use between the scan and the flip | high | mitigate | the record names the scanned tip; the origin tip must equal it before the record commit; only the record path may differ afterwards; private state, probes an... | closed |
| T-01-23 (01-04) | Elevation of privilege | a push performed by an autonomous task | high | mitigate | the three pushes (task 1, the record push, the read-back push) are human-gated and run by the main conversation or bokiko; the script, task 2 and task 5 are ... | closed |
| T-01-24 (01-04) | Information disclosure | the window between the flip and the protections | high | mitigate | secret scanning and push protection are enabled in the same step sequence immediately after the flip; if either toggle fails the error is recorded verbatim, ... | closed |
| T-01-25 (01-04) | Tampering | a history rewrite or deletion offered as a fix for a gate finding | high | mitigate | prohibited by the 2026-10-21 decision; any FAIL or UNREVIEWED halts the plan and goes to bokiko; the executor never edits .gitleaksignore or evidence | closed |
| T-01-27 (01-04) | Repudiation | the post-flip state left unrecorded or unverifiable (no task after the go-word,  | high | mitigate | task 4 has the main conversation write the read-back into a fixed-layout committed record (01-POSTFLIP-READBACK.md) and commit it through the hooks; task 5 c... | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-SC (01-01, 01-02, 01-03, 01-04) | this plan installs nothing; gitleaks, shellcheck, gh, git and python3 are already present and RESEARCH lists no npm, PyPI or crates package. Any added install would need the audit table and a block... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-12 | 28 | 28 | 0 | gsd-security-auditor (sonnet) via /gsd-secure-phase, retroactive |

### Auditor evidence and observations

The auditor's full verdict is reproduced below (evidence pointers are file:line at the audited commit).

## SECURED

**Phase:** 01 - publication-gate
**Threats Closed:** 31/31 (27 mitigate verified in code, 4 accept rows closed by the accepted-risk entries below)
**Open at or above high (threats_open):** 0
**Open below high (non-blocking):** 0
**ASVS Level:** 1 | **block_on:** high
**Audited at:** HEAD 0c6cd7f (origin/main equals HEAD), 2026-11-12. Read-only audit; no repository file, config or ref was changed.

**threats_open:** 0

### How this was verified (evidence run by the auditor, not taken from documents)

- Read every implementation file named in the brief at HEAD. No drift between working tree and HEAD for `.githooks/`, `scripts/`, `.gitleaks.toml`, `.gitleaksignore`, `.claude/` (`git diff --stat HEAD` empty).
- `sh scripts/test-hooks.sh` with TMPDIR pointed at a scratchpad directory: exit 0, 29 PASS, 0 FAIL, 0 SKIP. The real repository's HEAD and full `for-each-ref` checksum were identical before and after.
- `sh scripts/prepublish-check.sh --rehearse --skip-inventory` (local source, no network): strict-equals-accepted PASS (exit 2, 15 fingerprints equal the list, all in d437af2), gate-clean PASS, tree-clean PASS, one-identity PASS, no-attribution-trailers PASS (0 matching lines), denylist-history PASS (host-name entries only). One FAIL: owner-clone-config (see Observation 1).
- Plan 01-03's write-verb gate (`grep -n -E 'repo edit|--method|[ ]-X[ =]|--field|--raw-field|--input|git push' scripts/prepublish-check.sh`) returns rc 1 (no match). Plan 01-01's static commit gate (awk over comment-stripped test-hooks.sh) returns rc 0 (seen=1, bad=0).
- `leaks.sh` run with PATH lacking gitleaks: prints "leak check FAILED: gitleaks not found", rc 1.
- Git lineage (read-only): scanned tip ab2e345 -> flip tip 9a794e7 differs by exactly one path (the pre-flip record); 9a794e7 -> 55835ad differs by exactly one path (the read-back); each is the sole child of the previous; all three are ancestors of HEAD; disclosure commit 4f9fd16 is an ancestor of the flip tip.
- All-ref history (382 commits): exactly 1 distinct author/committer identity and it equals the repo-local pin (values not printed); 0 lines matching attribution.ere; 0 tags; the full fake-key literal appears in no commit (`git log --all -S`, 0 hits); `d437af2` still present and an ancestor of HEAD (no rewrite).
- Not done on purpose: no network call (no `gh`, no `git ls-remote`, no push). The live PUBLIC / protections state was not re-queried; it rests on the committed read-back plus the 2026-10-24 live re-read recorded in 01-VERIFICATION.md and 01-04-SUMMARY.md.

### Threat Verification

| Threat ID | Category | Severity | Disposition | Status | Evidence |
|-----------|----------|----------|-------------|--------|----------|
| T-01-01 | Spoofing | high | mitigate | closed | `.githooks/checks/identity.sh:15-17` compares both `%an <%ae>` and `%cn <%ce>` of every commit in range to the pin; `:18-26` compares annotated-tag tagger; run from `.githooks/pre-push:30-40`. Cases identity-wrong-author-committer, identity-committer-only, identity-wrong-tagger (`scripts/test-hooks.sh:107,146,163`) PASS in my run; env-override variant included. |
| T-01-02 | Information disclosure | high | mitigate | closed | Repo-local config has `user.useConfigOnly=true`, `preclear.pinnedIdentity` set, local `user.name` and `user.email` set (presence checked, values not printed). All commits (382 on main; all refs checked) carry the single pinned identity (no hostname-derived address). Documented at `.githooks/README.md:22-32`. |
| T-01-03 | Repudiation | high | mitigate | closed | `.claude/settings.json` (attribution commit "" / pr "" / sessionUrl false), `.claude/CLAUDE.md:1`, `.githooks/commit-msg:9-18`, `.githooks/checks/identity.sh:28-35`, patterns `.githooks/attribution.ere:1-4`. Tests trailer-commit-msg and trailer-bypassed-prepush PASS. Effect confirmed: 0 attribution-pattern matches across all history. |
| T-01-04 | Tampering | medium | mitigate | closed | pre-push is the authoritative net: trailer-bypassed-prepush (`test-hooks.sh:202-212`, commit with the skip option at `:204`) and leak-seed-prepush (`:126-136`, skip at `:129`) both refused at push and PASS. Limit stated at `.githooks/README.md:73-81`; GitHub push protection enabled per `01-POSTFLIP-READBACK.md:6`. |
| T-01-05 | Tampering | high | mitigate | closed | `.githooks/checks/leaks.sh:7` exit 1 when scanner absent (reproduced, rc 1); `:10` `--exit-code 2`; `:11` any non-zero sets rc 1 (finding and tool error both refuse). Same in `.githooks/pre-commit:7,11-12`. Test gap only: no test case drives the leaks.sh no-scanner path (review IN-09); reproduced by hand instead. |
| T-01-06 | Information disclosure | high | mitigate | closed | Seed assembled from three fragments at run time (`scripts/test-hooks.sh:77-82`); full literal in no commit (`git log -S`, 0); `--redact` on all 5 gitleaks invocations (`pre-commit:11`, `leaks.sh:10`, `prepublish-check.sh:166,180,191`); no gitleaks report tracked; negative control asserts the seed is never printed (`test-hooks.sh:667,677`). |
| T-01-07 | Tampering | low | mitigate | closed | `.githooks/pre-push:15-24`: values read with `read -r`, written with `printf '%s%s%s\n'`, `"$remote_sha^{commit}"` quoted, range built only from the sha, `--not --remotes=` and the remote name; deletions skipped (`:17`). Residual: consumers expand `$rev` unquoted on purpose (`identity.sh:15,30`, `denylist.sh:162,166,170`) = open info finding IN-02; per the review it blocks a push and cannot bypass it, and the values come from git itself. See Observation 3. |
| T-01-08 | Elevation of privilege | high | mitigate | closed | `scripts/test-hooks.sh:65-74` push_in asserts scratch repo and that origin starts with the throwaway path before the only `git push` (`:73`, the sole push in the file); case real-origin-refs-unchanged (`:732-741`) PASS; real HEAD and all refs unchanged across my run. |
| T-01-26 | Tampering | high | mitigate | closed | `test-hooks.sh:40-46` scratch_ok (non-empty toplevel, strictly under physical TP, not the real toplevel), `:49-54` assert_scratch (prints FAIL, `kill -TERM "$$"`, then exit), `:56-63` scratch_commit calls assert_scratch first; the only two commit invocations (`:59,:61`) are inside it (static gate rc 0); tag/reset/rm steps are each preceded by assert_scratch (`:164,:76,:298`); `:732-741` proves the guard rejects the real repo (`:739`) and that real HEAD/refs are unchanged. Confirmed live. |
| T-01-SC (01-01) | Tampering | low | accept | closed | Accepted-risk AR-1 below. Verified: no dependency manifest or lock file changed in phase range 56e155c..55835ad. |
| T-01-09 | Tampering | high | mitigate | closed | `.gitleaksignore` holds 15 entries, all commit d437af2ef754..., rules home-path-unix (11) and home-path-dash-slug (4). `scripts/prepublish-check.sh:129-162` enforces set equality, count 15, commit prefix d437af2 and the two-rule set; rehearsal PASS in my run (strict exit 2, 15 equal, all in d437af2; gate exit 0). File edited once only (8938188, creation). No rewrite: d437af2 is an ancestor of HEAD. |
| T-01-10 | Information disclosure | high | mitigate | closed | `--redact` everywhere (see T-01-06); the only report file is `-r "$W/strict.json"` inside the `mktemp -d` dir (`prepublish-check.sh:63,166-167`); hooks write no report; `.githooks/checks/denylist.sh:80-97,135-139,154,175` print counts and file names only, with "(file name)" substituted when the path holds an entry; tests assert the entry is never printed (`test-hooks.sh:419,452,462,559`). |
| T-01-11 | Information disclosure | medium | mitigate | closed | `denylist.sh:40-74` builds entries at run time from `hostname`, `hostname -s`, `scutil` plus `.git/info/preclear-deny.txt` (inside .git, never committed); host names under 6 characters or generic are dropped; cases denylist-precommit, denylist-paths-and-messages, denylist-history-requires-local-list, denylist-awk-failure-fails, denylist-hostname-entries PASS. Real-name leg rests on an owner statement, see AR-3. |
| T-01-12 | Information disclosure | medium | mitigate | closed | `.gitleaks.toml:43-49` (condition AND, path `.planning/.+\.md`, exact `^bokiko@gmail\.com$`); `:51-58` reserved example domains, `users.noreply.github.com`, and two exact vendor role addresses only. Cases identifiers-precommit, named-vendor-address-refused, identifier-false-positive-guards (`test-hooks.sh:315,368,383`) PASS. |
| T-01-13 | Tampering | medium | mitigate | closed | Limits stated plainly at `.githooks/README.md:73-81`; pre-push is the push-time net and fails closed on a non-executable or absent check (`pre-push:27-40`, case prepush-nonexecutable-check-fail-closed PASS); `prepublish-check.sh:86-93` asserts hooksPath, useConfigOnly and the pin; push protection enabled (`01-POSTFLIP-READBACK.md:6`). See Observation 1 for the current hooksPath drift. |
| T-01-14 | Denial of service | low | mitigate | closed | Rules key on shapes with a name segment (`.gitleaks.toml:6-41`); false-positive guard case (`test-hooks.sh:383-402`: settings.local.json, npm spec, example and vendor role addresses, bare-prefix prose) PASS. |
| T-01-15 | Tampering | high | mitigate | closed | `.githooks/pre-commit:7` exits 1 when gitleaks is missing; case fail-closed-no-scanner (`test-hooks.sh:578-588`) PASS and actually ran (gitleaks is outside /usr/bin:/bin on this machine, so it was not skipped). |
| T-01-SC (01-02) | Tampering | low | accept | closed | Accepted-risk AR-1. Same verification. |
| T-01-16 | Elevation of privilege | high | mitigate | closed | Plan write-verb gate over `scripts/prepublish-check.sh` finds nothing (rc 1). Only GitHub calls: `gh repo view`, `gh api` with default GET and no -X/-f/-F/--input, `gh issue list`, `gh pr list`, `curl -s` GET, anonymous `git ls-remote` (`:281-340`). No `git push`. `--rehearse` refuses `--record` (`:42-45`). Repo-wide sweep for `gh repo edit`, `--visibility`, `change-visibility` finds nothing outside `.planning` prose. |
| T-01-17 | Tampering | high | mitigate | closed | `prepublish-check.sh:99-107` `git clone --mirror` of the source; `:125-127` config, ignore file and pattern file taken from the mirror's HEAD; `:113-119` default mode requires remote tip, local HEAD and mirror tip equal; scans run on the mirror and on a `git archive` extract of it (`:166,180,190`). |
| T-01-18 | Information disclosure | medium | mitigate | closed | `--redact`; scratch dir from `mktemp -d` (`:63`); detail strings are counts and booleans (compare.py output `:139-161`); record writer (`:352-370`) emits tip, scanner version, rows only; created exclusively via `set -C` (`:353`) and refused if it exists (`:50-53`). Both committed records contain no path, address, IP or host (grep none). |
| T-01-19 | Information disclosure | medium | mitigate | closed | README `## Known issues and limits` (`README.md:275-301`) and the CHANGELOG bullets name no address, home path, host or attribution; HEAD tree scanned with the identifier rules and no accepted list: tree-clean PASS (exit 0) in my run; pre-commit scans staged text. |
| T-01-20 | Repudiation | medium | mitigate | closed | Disclosure facts re-verified: digest 6d22a71e7f3c is the Rows 5-12 digest (`tests/evidence/publication-2026-10-20/README.md:55`); `SKILL.md` at disclosure commit 4f9fd16 hashes to 86e5b14e64b1 (sha256 prefix) as the README states; that evidence README was not edited in phase range (`git log` empty). Digest-gap bullet published as drafted after bokiko's checkpoint answer (`01-04-SUMMARY.md` Decisions Made). |
| T-01-SC (01-03) | Tampering | low | accept | closed | Accepted-risk AR-1. Same verification. |
| T-01-21 | Elevation of privilege | critical | mitigate | closed | No script, hook or auto action holds a flip command (tracked-file sweep for `gh repo edit`, `--visibility`, `accept-visibility-change-consequences`, write-method `gh api`: only `.planning` plan/research prose). `01-04-PLAN.md:10` `autonomous: false`; tasks 3 and 4 (`:162`, `:213`) and task 1 (`:107`) are `gate="blocking-human"` with no `auto_select`; go-word text and exclusive main-conversation actor at `:182-189`. Run record: `01-04-SUMMARY.md` (tasks run by the main conversation, no subagent ran a released step); stale auto-chain flag cleared before the scan (ab2e345); `.planning/config.json` now `auto_advance: false`, `_auto_chain_active: false`. Go-word provenance is a human fact (no script can show who typed it): confirmed by bokiko, `01-VERIFICATION.md` "Human item resolved". |
| T-01-22 | Tampering | high | mitigate | closed | Record names the scanned tip (`01-PREFLIP-INVENTORY.md:4`); `git diff --name-only ab2e345 9a794e7` lists exactly the record path, one commit, parent is ab2e345; plan steps 1-2 (`01-04-PLAN.md:183-184`) assert private state, probes and tip equality immediately before the flip; read-back's Flip tip equals `git rev-parse 9a794e7`. `prepublish-check.sh:50-53,353` never overwrites a record. |
| T-01-23 | Elevation of privilege | high | mitigate | closed | Script has no push (gate rc 1); pushes were run by the main conversation on bokiko's instruction (`01-04-SUMMARY.md` Task Commits and Deviations); hooks on, never skipped: all pushed history passes pre-push-equivalent checks today (rehearsal: 1 identity, 0 trailers, gate clean) and no tracked non-doc file recommends the skip option beyond the README Limits note. |
| T-01-24 | Information disclosure | high | mitigate | closed | Plan step order (`01-04-PLAN.md:185-188`): flip, then immediately `--enable-secret-scanning`, then `--enable-secret-scanning-push-protection`, failure path recorded verbatim with Result: FAIL and nothing pushed; `01-POSTFLIP-READBACK.md:5-6` shows both enabled; `01-04-SUMMARY.md` item g: both enabled on first attempt; local hooks remain on (`core.hooksPath` set). |
| T-01-25 | Tampering | high | mitigate | closed | Prohibition recorded at `.planning/PROJECT.md:78` (No history rewrite, 2026-10-21) and `01-04-PLAN.md` prohibitions; observed: no rewrite (d437af2 an ancestor of HEAD; phase commits linear ancestors; no rebase, forced-update or amend in the local reflog; `.gitleaksignore` touched only at creation; evidence tree untouched in phase range). |
| T-01-27 | Repudiation | high | mitigate | closed | `01-POSTFLIP-READBACK.md` is committed (55835ad, sole commit touching it) with exactly one each of Flip tip, Visibility: PUBLIC, Secret scanning: enabled, Push protection: enabled, Unauthenticated page status: 200, Result: PASS and no path or at-sign; flip tip = scanned tip + only the pre-flip record (verified by git); 55835ad is the direct child of 9a794e7 touching only the read-back path; origin/main equals HEAD. Task 5 live read-only re-read recorded as passed (`01-04-SUMMARY.md`, `01-VERIFICATION.md` truth 5). |
| T-01-SC (01-04) | Tampering | low | accept | closed | Accepted-risk AR-1. Same verification. |

### Trust boundaries confirmed (12/12 from the register)

1. Developer shell to git client (01-01): identity.sh reads the commit objects themselves, so GIT_AUTHOR_/GIT_COMMITTER_ overrides are caught; commit-msg and pre-push both enforce the shared attribution.ere.
2. Local clone to GitHub remote (01-01): pre-push fans every pushed range through leaks, identity and denylist checks and fails closed on a missing or non-executable check.
3. Test script to real repository (01-01): scratch guard, push guard, no commit outside scratch_commit; real HEAD and refs unchanged across a full run.
4. Committed history to public readers (01-02): mirror-based strict, gate and tree scans plus denylist-history all green before the flip and again at HEAD.
5. Scanner configuration to accepted findings (01-02): accepted list pinned to exactly 15 fingerprints in d437af2 and two rules, enforced by set equality, never hand-widened.
6. Local machine facts to committed files (01-02): deny entries built at run time, never committed or printed; both committed records are free of paths, hosts and addresses.
7. Local working copy to what GitHub holds (01-03): fresh `--mirror` clone, config from the mirror's HEAD, three-way tip equality in default mode.
8. Script to GitHub API (01-03): read-only gh and git commands only; write-verb gate empty; rehearsal cannot record.
9. Disclosure text to public readers (01-03): README and CHANGELOG contain only measured facts, no identifiers; tree scan clean.
10. Autonomous execution to GitHub (01-04): plan non-autonomous, blocking-human gates, no flip in any script, main-conversation-only actor.
11. Scan time to flip time (01-04): tip lineage proves only the record path changed between scan and flip.
12. Private to public (01-04): one-way step taken once, with disclosure first, protections right after, read-back committed and checked.

### Accepted-risk entries to persist (the orchestrator writes SECURITY.md)

| ID | Threat | Risk accepted | Basis | Owner | Date |
|----|--------|---------------|-------|-------|------|
| AR-1 | T-01-SC (all four plans) | Supply-chain install risk: accepted because phase 01 installs nothing. gitleaks, shellcheck, gh, git and python3 were already present; RESEARCH lists no npm, PyPI or crates package. Any future install needs the audit table and a blocking human checkpoint. | Verified: no dependency manifest or lock file changed in 56e155c..55835ad. | bokiko | 2026-10-22 plan decision |
| AR-2 | T-01-09 | Home-folder path lines (11 lines in 10 evidence files, 15 fingerprints) stay in immutable history at commit d437af2; they reveal only a folder name. | `.planning/PROJECT.md:78` "No history rewrite (2026-10-21)"; list equality enforced by prepublish-check.sh. | bokiko | 2026-10-21 |
| AR-3 | T-01-11 | The deny list never held the owner's real name: `.git/info/preclear-deny.txt` was absent at the flip and is absent now, so the name scan covered machine host names only (six or more characters, non-generic). bokiko confirmed there is no other name to scan for. Consequence: default-mode `prepublish-check.sh` fails its denylist step until entries exist; `--rehearse` runs on host names alone. | `01-04-SUMMARY.md` Decisions Made, item f (2026-10-24); `.githooks/README.md:58-71`. | bokiko | 2026-10-24 |
| AR-4 | T-01-04, T-01-13 | Hooks are opt-in per clone and skippable (`--no-verify`); identity and push-time attribution checks exist only in the pinned owner clone; server-side net after the flip is GitHub push protection (secrets only, not identity, paths or host names). | `.githooks/README.md:73-81`; `01-POSTFLIP-READBACK.md:6`. | bokiko | 2026-10-22 |
| AR-5 | T-01-19 (informational) | 154 session-id-shaped UUIDs in evidence files accepted as public without a decisions line. | `01-04-SUMMARY.md` Decisions Made (checkpoint item d). | bokiko | 2026-10-24 |

If the orchestrator does not persist AR-1 in SECURITY.md, the four T-01-SC rows revert to open, but at severity low they are below the block_on threshold and would not block.

### Unregistered Flags

None. `01-01-SUMMARY.md` and `01-02-SUMMARY.md` carry `## Threat Flags: None`; `01-03-SUMMARY.md` and `01-04-SUMMARY.md` carry no Threat Flags section at all (treated as none; the register's `summary_flags` is empty). No new attack surface found that lacks a register row. The nine open info review findings (IN-01..IN-09 in `01-REVIEW-DISPOSITION.md`) are recorded there, are not register rows, and none reopens a threat (cross-references in Observation 3).

### Observations (non-blocking, none changes the verdict)

1. **Owner-clone hooksPath drifted since phase verification.** `core.hooksPath` in this clone's `.git/config` (mtime 2026-11-03 09:23) is now the absolute path of this checkout's `.githooks`, not the literal `.githooks` that 01-VERIFICATION.md read on 2026-10-24. The hooks are still active (it resolves to the same directory, modes 100755, `useConfigOnly=true`, pin set). But `scripts/prepublish-check.sh:89` compares the string `.githooks`, so `--rehearse` currently exits FAIL on owner-clone-config alone; every other rehearsal check passes. This contradicts the brief's "`--rehearse` passes" and is why. It is local state drift, not a defect in the mitigation (the assertion fired exactly as designed). The owner can restore the relative value if a passing rehearsal is wanted. No threat row reopens: T-01-13's pre-flip assertion exists and works, and push-time hooks are enabled.
2. **Deny-list leg is host-name only (AR-3).** The deny-list file is absent by design here. The pre-flip record's denylist-history PASS (2026-10-22) was produced by the earlier script, before WR-03 (82af43d, 2026-10-24) made default mode refuse a run without loaded entries, so that PASS never proved owner entries were loaded; the owner's confirmation at the checkpoint is the compensating evidence.
3. **Open info review findings that touch register rows (all fail safe or are not triggered now).** IN-02 (unquoted `$rev` in consumers; blocked push, not a bypass) vs T-01-07. IN-03 (a pin starting with a dash would make `grep -v -x -F` error and pass; the current pin does not begin with a dash) vs T-01-01. IN-04 (annotated tag messages are never scanned for attribution; 0 tags exist) vs T-01-03. IN-06 (hooks read config from the working tree, scanner version not enforced at run time) vs T-01-05/T-01-09. IN-07 (the "anonymous" probe could use stored credentials; plan 01-04 reran it with git config and credential helper disabled, per its summary) vs T-01-22. IN-09 (no test drives the leaks.sh no-scanner path) vs T-01-05, reproduced by hand here.
4. **Bookkeeping.** `01-REVIEW-DISPOSITION.md` frontmatter says `open: 12`, but its table lists 9 open rows (IN-01..IN-09).
5. **Config.** `.planning/config.json` still has `mode: yolo` with `human_verify_mode: end-of-phase`; `auto_advance` and `_auto_chain_active` are false. T-01-21's one-way step is already taken, so this is moot for phase 01; later phases carry no visibility flip.
6. **Post-phase edits to gate files are covered.** `.gitleaks.toml` changed after the phase (62f0170, 2026-10-26, phase 2: home-path boundary, ASCII-only identifiers, case-insensitive host suffix). All mitigations above were verified against the current HEAD version, and strict-equals-accepted still yields exactly the 15 accepted fingerprints.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-12
