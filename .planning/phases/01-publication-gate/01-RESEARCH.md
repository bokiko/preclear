# Phase 1: Publication Gate - Research

**Researched:** 2026-10-21
**Domain:** Pre-publication leak and identity gates for a git repository (gitleaks, git hooks, GitHub visibility via `gh`)
**Confidence:** HIGH (every behaviour below was run against this repo and its real `--mirror` clone this session; GitHub-side enabling of repo-level push protection on a free account is the one MEDIUM item, see A2)

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for this phase (no `/gsd-discuss-phase` was run). The binding inputs are the roadmap, requirements and `PROJECT.md`. Treat them as locked.

### Locked Decisions (copied from PROJECT.md Key Decisions, REQUIREMENTS.md Out of Scope, ROADMAP.md hard-rule gate)
- No history rewrite; `bokiko` with the address recorded in `PROJECT.md` stays the public identity (2026-10-21). A new scan finding halts the phase and goes to bokiko; a rewrite is never a fallback the executor may choose.
- Row 7 ships as a disclosed known issue (rerun three times later, in Phase 4).
- The visibility flip (PUB-07), any history rewrite and any deletion run only on bokiko's explicit word in the conversation. Never inside an autonomous execution, a script, or a subagent. Plan 01-03 ends at a go or no-go checkpoint and stops there.
- Commits are authored solely by bokiko with no AI attribution trailers. No CI this milestone; hooks are the only net.
- `SKILL.md`, `references/`, `tests/fixtures/` are frozen; `SKILL.md` stays at or under 12,000 bytes (currently 11,994).
- Privacy: planning artifacts use repo-relative paths and refer to the owner only as bokiko (`.planning/` becomes public).
- Mode `mvp`: plan the phase as vertical slices (three plans in ROADMAP: 01-01, 01-02, 01-03).

### Claude's Discretion
- Hook mechanism, scan-rule design, file layout, check scripts, disclosure wording, inventory format.

### Deferred Ideas (OUT OF SCOPE)
- Live-matrix CI on GitHub Actions; open-sourcing the real checkpoint helper; any harness, stub or rerun work (Phases 2 to 4); history rewrite; a policy exception for the NUL `-z` form.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-01 | Owner decisions recorded in `PROJECT.md` Key Decisions | Current table state and the three gaps (no row 7 date, two decisions share one row, "Pending" outcomes) in "PROJECT.md edit targets" |
| PUB-02 | gitleaks plus custom rules over full history and tree of a fresh `--mirror` clone; only the two accepted findings | Verified config, true counts (19 matches, 15 fingerprints, 11 lines in 10 files), mirror-scan recipe, interpretation of "author email" |
| PUB-03 | Pre-commit and pre-push hooks run the same scan; proven by a seeded fake leak; committed config | `.githooks/` design, tested scripts, one-command enable, throwaway-clone test recipe |
| PUB-04 | Repo-local identity pinned with `user.useConfigOnly`; pre-push refuses other identities and AI trailers | `useConfigOnly` semantics (tested), pre-push stdin protocol, identity and trailer checks (tested), `commit-msg` and Claude Code `attribution` settings |
| PUB-05 | Live-repo inventory recorded immediately before the flip | Read-only `gh`/`git ls-remote` command list with the values observed today |
| PUB-06 | Row 7, carried-forward rows, NUL `-z` form disclosed before the flip | Exact facts to quote, plus one new finding (shipped SKILL.md digest was never run) and disclosure shape |
| PUB-07 | Flip only on explicit word; secret scanning and push protection enabled right after | `gh repo edit` flags (verified from installed help), REST shape, read-back, unauthenticated probes, checkpoint rules |
</phase_requirements>

## Summary

Everything this phase needs is local and cheap: gitleaks 8.30.0 is already installed, `gh` is authenticated as the repo admin, and the repo is private right now. The scan, the hooks and the mirror check were prototyped end to end against a real `git clone --mirror` of `bokiko/preclear` and a throwaway clone with a local bare remote. A seeded fake secret, a wrong author and committer, a wrong tagger and a `Co-Authored-By` trailer were each refused with a non-zero exit, and none reached the remote. All prototype files live in the research scratchpad only; nothing in the repo or on GitHub was changed.

The history is cleaner than the roadmap's wording implies, and the exact allowlist is small and immutable. Default gitleaks rules find nothing across 14 commits. The custom rules find exactly one accepted cluster: **eleven added lines in ten evidence files of commit d437af2** (the roadmap says "ten lines"; it is ten files), which gitleaks reports as 19 matches and **15 unique fingerprints** (11 home-path, 4 Claude Code dash-slug). The author email is not a gitleaks finding at all (gitleaks never reads commit metadata); it appears in two planning-doc lines and in the author and committer fields of all 14 commits, so it needs a config allowlist for the two document lines plus a separate metadata check. The two worries recorded in STATE.md resolve cleanly: rules that key on a home path *with a user-name segment* do not match the prose in `ARCHITECTURE.md` and `PITFALLS.md` (zero tree hits), so no rewording is needed.

One new fact the planner must surface to bokiko: the **shipped `SKILL.md` was never run in any matrix row**. Rows 5 to 12 and the 3a/3b reruns recorded skill digest `6d22a71e7f3c`; commit 188930b (the same commit that filed rows 5 to 12) edited `SKILL.md` and added `references/status-sidecar.md`, so the shipped digest is `86e5b14e64b1`. This belongs in the PUB-06 disclosure.

**Primary recommendation:** Use a committed `.githooks/` directory enabled by `git config core.hooksPath .githooks`; one committed `.gitleaks.toml` (default rules plus six identifier rules and two allowlists) and a 15-line `.gitleaksignore`; modular pre-push checks (`checks/identity.sh`, `checks/leaks.sh`) fed from one parsed copy of stdin; run gitleaks with `--exit-code 2` so a leak is distinguishable from a tool error; and make the flip a `checkpoint` that only the main conversation executes after bokiko's go-word.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Block secrets and identifiers on new content | Local git client (pre-commit hook) | Local git client (pre-push hook) | Server cannot see identifiers; no CI exists. Both hooks call the same config. |
| Refuse wrong identity and AI trailers | Local git client (pre-push, commit-msg) | Claude Code project settings (`attribution`) | Identity lives in commit metadata, invisible to content scanners. Suppress at the source, verify at push. |
| Pin the owner identity | Local repo config (`.git/config`) | Committed `.githooks/README.md` documents the 3 commands | `.git/config` is never cloned, so strangers are not forced into the owner's identity. |
| Whole-history assurance | Fresh `--mirror` clone of the remote scanned from outside the working copy | Committed `.gitleaks.toml` + `.gitleaksignore` | The local clone can differ from what GitHub holds. |
| Live-repo state (refs, hooks, keys, runs) | GitHub REST API via `gh` (read-only) | `git ls-remote` | Only GitHub knows hooks, keys, Actions history, pages. |
| Visibility change | Main conversation, human-gated | `gh repo edit` (single command) | Hard rule: never a script, subagent or autonomous task. |
| Post-flip secret protection | GitHub (secret scanning, push protection) | Local hooks stay on | Server-side net for secrets only; it cannot check identity or trailers. |
| Disclosure of known defects | Committed docs (README, CHANGELOG) | Evidence READMEs stay untouched | Historical evidence is never edited. |

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| gitleaks | 8.30.0 installed; 8.30.1 latest, published 2026-03-21 [VERIFIED: `gh api repos/gitleaks/gitleaks/releases/latest`, `gitleaks version`] | Secret and custom-regex scan of history (`git`), tree (`dir`), staged diff (`git --staged`) | Already installed (`/opt/homebrew/bin/gitleaks`), MIT, official `gitleaks/gitleaks` repo, supports custom rules, allowlists and fingerprints. Pin "8.30.x"; all behaviour below was observed on 8.30.0. |
| git hooks via `core.hooksPath` | git 2.50.1 [VERIFIED: `git --version`] | Committed hooks, one-command enable | Zero install, POSIX sh, works with the GSD commit tool, which runs hooks unless a caller passes `--no-verify` (opt-in only) [VERIFIED: read `bin/lib/commands.cjs` lines 2418-2419 in the GSD install]. |
| gh | 2.83.2, authenticated as bokiko, token has `repo` scope, repo `viewerPermission` ADMIN [VERIFIED: `gh auth status`, `gh repo view`] | Inventory, visibility flip, security toggles | Only supported CLI for these REST calls. |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| shellcheck | 0.11.0 installed [VERIFIED: `shellcheck --version`] | Lint the hook scripts | Run `shellcheck -s sh` in the verify step. Expect only the two intentional findings (SC2034 unused `remote_ref`, SC2086 deliberate word splitting of `$rev`); annotate them with `# shellcheck disable=`. |
| python3 `-I` | 3.14.7 [VERIFIED] | Parse gitleaks JSON reports for count and set-equality checks | Standard library only (matches HARN-14 spirit). |
| curl | system | Unauthenticated public/private probe | Before and after the flip. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `.githooks/` + `core.hooksPath` | `pre-commit` framework (latest tag v4.7.0 [VERIFIED: gh api]; not installed [VERIFIED: `command -v`]) | Needs Python install plus network fetch of hook repos; its installer is documented to conflict with a set `core.hooksPath` [ASSUMED, A1]. Rejected: adds an install a stranger does not need. |
| `.githooks/` + `core.hooksPath` | lefthook (latest tag v2.2.2 [VERIFIED: gh api]; not installed [VERIFIED: `command -v`]) | Go binary plus YAML; second dependency beside gitleaks. Rejected for the same reason. |
| `gitleaks git --staged` | `gitleaks git --pre-commit` | `--pre-commit` scans `git diff`; `--staged` scans exactly what will be committed. Use `--staged`. |
| `.gitleaksignore` for the d437af2 cluster | `--baseline-path` JSON | Baseline stores full report entries and is brittle; the plain fingerprint list is auditable line by line. |

**Installation (nothing new to install):**
```bash
command -v gitleaks gh git shellcheck   # all present; gitleaks 8.30.0
# optional upgrade, owner's call: brew upgrade gitleaks   (8.30.1)
```

**Version verification:** `gitleaks version` returned `8.30.0`; the GitHub latest-release API returned `v8.30.1` published 2026-03-21 [VERIFIED].

## Package Legitimacy Audit

No npm, PyPI or crates packages are installed in this phase, so the `package-legitimacy` seam (npm/pypi/crates only) does not apply. The one external tool was assessed by hand.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| gitleaks | Homebrew formula / GitHub releases | created 2018-01-27, not archived, MIT, ~30k stars [VERIFIED: `gh api repos/gitleaks/gitleaks`] | n/a (binary) | github.com/gitleaks/gitleaks | OK (manual) | Approved; already installed locally |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
pre-commit and lefthook were considered and not recommended, so they are not installed.

## Architecture Patterns

### System Architecture Diagram

```
 developer / GSD executor
        |  git commit
        v
 [pre-commit]  gitleaks git --staged --config .gitleaks.toml --exit-code 2
        |            fail -> commit refused (nothing written to history)
        v
 [commit-msg]  grep -E -f .githooks/attribution.ere <msg file>
        |            match -> commit refused
        v
   local commit  ------------------------------------------.
        |  git push                                         | (git commit --no-verify skips both:
        v                                                   |  pre-push is the authoritative net)
 [pre-push]  reads stdin "<lref> <lsha> <rref> <rsha>" per ref
        |     builds one range per ref (rsha..lsha, or lsha --not --remotes=<remote>)
        |     writes ranges to a temp file, runs every .githooks/checks/*.sh with it
        |-->  checks/leaks.sh     gitleaks git . --log-opts="<range>"  (exit 2 on finding)
        |-->  checks/identity.sh  %an/%ae/%cn/%ce == preclear.pinnedIdentity (owner mode)
        |                         tagger == pinned for annotated tags
        |                         git log %B | grep -E -f attribution.ere  -> none
        v
   any non-zero -> push refused, nothing reaches the remote
        |
        v  (private remote, until the go-word)
 PRE-FLIP GATE (01-03, read-only, same session as the flip)
   git clone --mirror <remote> ---> gitleaks strict run (ignore file OFF) == accepted list exactly
                                \-> gitleaks gate run  (ignore file ON)  == exit 0
                                \-> unique author/committer identities   == exactly 1
                                \-> trailer grep over all refs           == none
   gh api / git ls-remote inventory ---> record (refs, hooks, keys, runs, pages ...)
        |
        v
 CHECKPOINT: present evidence, STOP, wait for bokiko's go-word in the conversation
        |  go-word
        v
 main conversation only:  gh repo edit --visibility public --accept-visibility-change-consequences
        |-> enable secret scanning -> enable push protection -> read back -> unauthenticated probe
```

### Recommended Project Structure
```
.gitleaks.toml            # committed scan config (default rules + identifier rules + 2 allowlists)
.gitleaksignore           # 15 immutable fingerprints for d437af2, header comment explains why
.githooks/
├── README.md             # one-command enable; owner setup (3 commands); how to test; bypass caveat
├── attribution.ere       # one source of truth for forbidden trailer/attribution patterns
├── pre-commit            # gitleaks --staged
├── commit-msg            # refuse attribution at commit time
├── pre-push              # parse stdin once, run checks/*.sh
└── checks/
    ├── leaks.sh          # owned by plan 01-02
    └── identity.sh       # owned by plan 01-01
scripts/
├── test-hooks.sh         # seeded-leak, wrong-identity, trailer tests in a throwaway clone (no origin)
└── prepublish-check.sh   # read-only: mirror scan + metadata + trailers + inventory (plan 01-03)
.claude/settings.json     # attribution suppressed for Claude Code in this repo (see Pitfall 1)
```
The split into `checks/*.sh` lets plan 01-01 ship the pre-push scaffold and `identity.sh`, and plan 01-02 add `leaks.sh` and `pre-commit`, without editing the same file. Run the plans sequentially (waves 1, 2, 3); 01-02 depends on the scaffold from 01-01.

### Pattern 1: Scan config (tested)
**What:** Extend the default ruleset, add six identifier rules keyed on *shapes with a name segment* so prose that merely names a prefix does not match, and scope two allowlists.
**When to use:** the single committed `.gitleaks.toml`; hooks pass it explicitly with `--config`.
```toml
# Source: gitleaks README config reference (docs fetched 2026-10-21) + behaviour verified on gitleaks 8.30.0
title = "preclear public-release scan"

[extend]
useDefault = true

[[rules]]
id = "home-path-unix"
description = "Home-folder path with a user name segment (macOS or Linux)"
regex = '''/(?:Users|home)/[A-Za-z0-9._-]{1,64}/'''
tags = ["identifier", "path"]

[[rules]]
id = "home-path-dash-slug"
description = "Claude Code dash-slug of a home-folder path"
regex = '''-(?:Users|home)-[A-Za-z0-9._]{1,64}-'''
tags = ["identifier", "path"]

[[rules]]
id = "mac-temp-root"
description = "macOS per-user temp root"
regex = '''/(?:private/)?var/folders/[A-Za-z0-9_]{2}/'''
tags = ["identifier", "path"]

[[rules]]
id = "private-ipv4"
description = "RFC1918 or CGNAT (Tailscale) IPv4 address"
regex = '''(?:^|[^0-9.])((?:10\.[0-9]{1,3}|192\.168|172\.(?:1[6-9]|2[0-9]|3[01])|100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7]))\.[0-9]{1,3}\.[0-9]{1,3})(?:[^0-9]|$)'''
secretGroup = 1
tags = ["identifier", "network"]

[[rules]]
id = "internal-hostname"
description = "Hostname under a private or mDNS suffix"
regex = '''\b[A-Za-z0-9][A-Za-z0-9-]*\.(?:local|lan|home\.arpa|internal|localdomain|ts\.net)(?:[^A-Za-z0-9._-]|$)'''
tags = ["identifier", "host"]

[[rules]]
id = "email-address"
description = "Any email address; the public identity is allowlisted below"
regex = '''[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b'''
tags = ["identifier", "email"]

[[allowlists]]
description = "The public identity address may appear in planning documents"
condition = "AND"
targetRules = ["email-address"]
paths = ['''^\.planning/.+\.md$''']
regexes = ['''^<public-email-escaped>$''']      # exact public address, dots escaped; take it from PROJECT.md
regexTarget = "match"

[[allowlists]]
description = "Reserved or role-account domains are not personal identifiers"
targetRules = ["email-address"]
regexes = ['''@(?:(?:[A-Za-z0-9-]+\.)*example\.(?:com|org|net|test)|users\.noreply\.github\.com|anthropic\.com)$''']
regexTarget = "match"
```
Notes proven during testing: Go RE2 has no lookahead, so the `.local` rule uses a trailing character class (`settings.local.json` correctly does not match; a plain `\.local\b` produced 53 false hits in history). The email regex requires an alphabetic TLD, otherwise npm specs such as `name@0.2.25` in `FEATURES.md` match. The config file itself does not trip its own rules (committing it under the hooks succeeded).

### Pattern 2: Pre-push reads stdin once, fans out to checks (tested)
```sh
#!/bin/sh
# .githooks/pre-push   args: $1 remote name, $2 remote url; stdin: "<local ref> <local sha> <remote ref> <remote sha>"
here=$(cd "$(dirname "$0")" && pwd)
cd "$(git rev-parse --show-toplevel)" || exit 1
remote=$1
tab=$(printf '\t')
ranges=$(mktemp "${TMPDIR:-/tmp}/preclear-ranges.XXXXXX") || exit 1
trap 'rm -f "$ranges"' EXIT
while read -r local_ref local_sha remote_ref remote_sha; do   # shellcheck disable=SC2034
  case $local_sha in *[!0]*) ;; *) continue ;; esac            # deletion: nothing to check
  rev="$local_sha --not --remotes=$remote"                     # new ref: everything not already on this remote
  case $remote_sha in
    *[!0]*) git cat-file -e "$remote_sha^{commit}" 2>/dev/null && rev="$remote_sha..$local_sha" ;;
  esac
  printf '%s%s%s\n' "$local_ref" "$tab" "$rev" >> "$ranges"
done
[ -s "$ranges" ] || exit 0
rc=0
for check in "$here"/checks/*.sh; do
  [ -x "$check" ] || continue
  "$check" "$ranges" || rc=1
done
exit $rc
```
`checks/leaks.sh` (add `-v` so a refusal shows the rule and file; `--redact` keeps the value out of the log):
```sh
#!/bin/sh
ranges=$1
command -v gitleaks >/dev/null 2>&1 || { echo "leak check FAILED: gitleaks not found (brew install gitleaks)" >&2; exit 1; }
tab=$(printf '\t'); rc=0
while IFS=$tab read -r ref rev; do
  gitleaks git . --config .gitleaks.toml --no-banner --redact -v --exit-code 2 --log-opts="$rev" -l warn \
    || { echo "leak check FAILED for $ref" >&2; rc=1; }
done < "$ranges"
exit $rc
```
`checks/identity.sh` (owner mode; skips with a visible message when the pin is unset so strangers' pushes still work; the leak check still runs for them):
```sh
#!/bin/sh
ranges=$1
pinned=$(git config --local --get preclear.pinnedIdentity 2>/dev/null)
if [ -z "$pinned" ]; then echo "identity check skipped: preclear.pinnedIdentity is not set in this clone" >&2; exit 0; fi
tab=$(printf '\t'); rc=0
while IFS=$tab read -r ref rev; do
  bad=$(git log --format='%an <%ae>%n%cn <%ce>' $rev | sort -u | grep -v -x -F "$pinned")     # shellcheck disable=SC2086
  case $ref in refs/tags/*)
    t=$(git for-each-ref --format='%(taggername) %(taggeremail)' "$ref")
    [ -z "$t" ] || [ "$t" = "$pinned" ] || bad="$bad
$t" ;;
  esac
  [ -z "$bad" ] || { echo "identity check FAILED for $ref (pinned identity differs):" >&2; echo "$bad" >&2; rc=1; }
  attr=$(git log --format='%H %s%n%B' $rev | grep -i -E -f "$(dirname "$0")/../attribution.ere")   # shellcheck disable=SC2086
  [ -z "$attr" ] || { echo "attribution check FAILED for $ref:" >&2; echo "$attr" >&2; rc=1; }
done < "$ranges"
exit $rc
```
`.githooks/attribution.ere` (anchored on trailer keys; a bare word match on "claude" would false-positive on real history, e.g. a commit body that says "Claude Code's own git"):
```
^(co-authored-by|assisted-by|generated-by)[[:space:]]*:
^(signed-off-by|reviewed-by)[[:space:]]*:.*(claude|anthropic|openai|codex|copilot|gemini)
generated with .*(claude|codex|copilot|gemini)
noreply@anthropic\.com
```
`pre-commit`: `exec gitleaks git --staged --config .gitleaks.toml --no-banner --redact -v --exit-code 2 -l warn` after a `command -v gitleaks` guard that exits 1 (fail closed). `commit-msg`: `grep -i -E -f "$here/attribution.ere" "$1"` match means `exit 1`.

Enable (the one documented command a fresh clone runs): `git config core.hooksPath .githooks`. Confirm the file modes are committed as 100755 (`git ls-files -s .githooks`).

### Pattern 3: Throwaway-clone hook test (tested)
Never touch the real remote. Create `T=$(mktemp -d)`; `git init --bare "$T/remote.git"`; `git clone <repo> "$T/work"`; point `origin` at the bare path; copy the hooks and config in (or commit them in the clone); set `core.hooksPath`, the local identity and `preclear.pinnedIdentity`. Build the fake secret **at runtime from fragments** (a literal fake key committed in the test script would itself be blocked and would sit in public history). Cases and the exit codes observed:

| Case | Setup | Observed |
|------|-------|----------|
| Seeded secret blocked at pre-commit | `printf 'k = %s\n' "AKIA$(printf 'QYLPMN5HHHFPZAM7')"`, `git add`, `git commit` | commit exit 1, rule `aws-access-token`, no commit created |
| Seeded identifiers blocked at pre-commit | home-path-with-name, private IPv4, mDNS-suffix host, non-allowlisted email in one file | 4 findings, exit 1 |
| Pre-commit bypassed, pre-push blocks | `git commit --no-verify`, then `git push origin HEAD:refs/heads/t` | push exit 1; `git cat-file -e <seed-sha>` on the bare remote fails (seed absent) |
| Wrong author and committer | `GIT_AUTHOR_EMAIL=... GIT_COMMITTER_EMAIL=...` at commit | push exit 1 |
| Committer-only mismatch | `GIT_COMMITTER_EMAIL=` on `--amend` | push exit 1 (author-only checks would miss this) |
| Wrong tagger on annotated tag | `GIT_COMMITTER_*` on `git tag -a` | push exit 1 |
| AI trailer, commit-msg | `git commit -m s -m "Co-Authored-By: ..."` | commit exit 1 |
| AI trailer, commit-msg bypassed | `--no-verify`, then push | push exit 1 |
| Clean push | no findings | exit 0, ref updated |
| Unpinned clone | `preclear.pinnedIdentity` unset | identity check skipped with message, leak check still active, push exit 0 |

### Anti-Patterns to Avoid
- **Bare-prefix rules** (`/Users/`, `/home/`): they hit the prose in `ARCHITECTURE.md:65` and `PITFALLS.md` (1 line with both prefixes, plus 2 `/private/var` mentions) and force rewording or more allowlist entries. Key on prefix plus a name segment instead.
- **Fingerprints for ongoing content** (the email lines): a fingerprint embeds the commit hash, which does not exist yet at pre-commit time, and any edit to a flagged line creates a new finding. Use config allowlists for living files, `.gitleaksignore` only for immutable history.
- **`--redact=0` or committing a gitleaks JSON report**: reports carry `Match`, `Secret` and the commit message. Always `--redact`, and keep reports outside the repo (the `Fingerprint` field is the only thing worth committing).
- **Treating exit 1 as "leak"**: gitleaks returns 1 for leaks and for errors (a bad config path also exits 1; an unknown flag exits 126) [VERIFIED: observed]. Pass `--exit-code 2` so tests can tell them apart.
- **`git push --no-verify` / `git commit --no-verify` in any plan task**: bypasses the only net.
- **Putting the flip in a task `<action>`** or any script that an executor may run.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secret detection | regex list of key formats | gitleaks default ruleset (`useDefault = true`) | Maintained rule corpus; it found zero secrets in all 14 commits |
| History walk | loop over `git show` | `gitleaks git --log-opts="--all"` on a mirror | Handles every ref and diff; `--staged` for the commit path |
| Pushed-range detection | custom ref bookkeeping | pre-push stdin protocol (`rsha..lsha`, else `lsha --not --remotes=<name>`) | Exactly what git sends; handles new branches and deletions |
| Trailer parsing | custom message parser | anchored `grep -E -f attribution.ere` over `git log --format=%B`; `git interpret-trailers --parse` only if needed | Generic "any `key: value`" parsing false-positives on prose lines such as `defect: ...` that exist in real history |
| Hook distribution | install script that copies into `.git/hooks` | `core.hooksPath` | One config line, hooks stay versioned |
| Server-side secret net | hook-only trust | GitHub push protection after the flip | Catches pushes that skip local hooks (secrets only) |

**Key insight:** every control here is either configuration of an existing tool or a few lines of POSIX sh around `git log`. The only place real judgement is needed is what counts as an "accepted finding", and that is a documented owner decision, not code.

## Common Pitfalls

### Pitfall 1: Claude Code appends an AI trailer by default
**What goes wrong:** Claude Code's default commit attribution is `Co-Authored-By: <model name> <noreply@anthropic.com>` [CITED: code.claude.com/docs/en/settings-reference#attribution-commit]. This very research run was handed an instruction to add such a trailer to commits. Any executor or orchestrator that follows it puts an AI trailer into public history, contradicting the project constraint and PUB-04.
**Why it happens:** attribution is a per-user default, and the project has no `CLAUDE.md` and no project settings (verified: `ls .claude` shows only `tsc-cache`).
**How to avoid:** (a) commit `.claude/settings.json` with `{"attribution": {"commit": "", "pr": "", "sessionUrl": false}}`, the form that older versions also accept; the single-value `"attribution": false` needs Claude Code 2.1.281 or later (installed: 2.1.306) [CITED: same page]; (b) add a one-line rule to a committed `CLAUDE.md` or `.claude/CLAUDE.md` (the GSD config already points at `./.claude/CLAUDE.md`): "Commits in this repo carry no co-author or generated-by trailer"; Claude Code tells the model that CLAUDE.md attribution rules take precedence over its default lines [CITED: same page]; (c) every plan task that commits states "no trailer"; (d) `commit-msg` and pre-push enforce it.
**Warning signs:** `git log --format=%B | grep -i -E -f .githooks/attribution.ere` returns anything; a hook refusal citing `noreply@anthropic.com`.

### Pitfall 2: Without `useConfigOnly`, git invents an identity from the hostname
**What goes wrong:** in a repo with no identity in any config file, a commit succeeded with an address of the form `<login>@<hostname>.localdomain` [VERIFIED: ran with `GIT_CONFIG_GLOBAL=/dev/null` in a scratch repo]. That would publish the machine hostname in author and committer fields.
**How to avoid:** `git config --local user.useConfigOnly true` plus local `user.name` and `user.email`. With `useConfigOnly` and no identity anywhere the commit exits 128 ("Author identity unknown") [VERIFIED]. It does not stop `GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL` environment overrides, which beat config [VERIFIED]; that is why the pre-push identity check exists.
**Caveat:** the machine's global config also defines an identity, so `useConfigOnly` alone is satisfied by the global value; the local `user.name`/`user.email` pin is what makes the pin real.

### Pitfall 3: "Author email" is not a gitleaks finding
**What goes wrong:** the roadmap says the scan "exits with exactly the two accepted findings (ten home-path lines in d437af2, the author email)". gitleaks reads diffs, not commit metadata, so the author address never appears as a finding. What exists is (i) two content lines in `PROJECT.md:75` and `REQUIREMENTS.md:15`, both added in 0de513f, and (ii) author and committer fields on all 14 commits (one identity, verified).
**How to avoid:** define the acceptance mechanically as three checks, not one: strict gitleaks run (ignore file off) equals the 15-fingerprint list exactly; gate run (ignore file on) exits 0; `git log --all --format='%an <%ae>%n%cn <%ce>' | sort -u` yields exactly one line, the public identity. Tell the planner to restate PUB-02/SC2 in these terms (see Open Question 1).

### Pitfall 4: The fingerprint list can silently go stale
**What goes wrong:** with the ignore file active, a fingerprint that no longer matches anything is harmless, and a missing one fails loudly, but a stale list hides the real size of the accepted set.
**How to avoid:** the strict run's fingerprint set must equal the non-comment lines of `.gitleaksignore` exactly (set equality in the check script). Two matches on one line with the same rule share a fingerprint, so 19 matches collapse to 15 lines.

### Pitfall 5: Scanning the wrong thing, or at the wrong time
**What goes wrong:** scanning the working copy misses refs GitHub holds; scanning before the last push misses the newest commits; the record commit created after the scan is itself unscanned.
**How to avoid:** scan a fresh `git clone --mirror` of the remote, take the config and ignore file *from the mirror's HEAD* (`git show HEAD:.gitleaks.toml`) so the committed config is what is proven, and scan only after every phase commit is pushed to the private remote. The inventory record is committed last; assert `git diff --name-only <scanned-tip> HEAD` lists only that record file, which the hooks already scanned.

### Pitfall 6: Hooks are opt-in per clone
**What goes wrong:** `core.hooksPath` is local config; a fresh clone has no hooks until enabled, and `--no-verify` skips them anywhere.
**How to avoid:** `.githooks/README.md` states the one command. The pre-flip gate asserts `git config --get core.hooksPath` equals `.githooks` and `preclear.pinnedIdentity` is set in the owner's clone. State the limit plainly in the README: hooks are a safety net, not enforcement; after the flip GitHub push protection is the server-side net for secrets only.

### Pitfall 7: Planning docs are public, and the new ones can leak too
**What goes wrong:** `.planning/phases/01-publication-gate/*` (this file, plans, summaries) are committed. A literal home path, hostname, private IP or real name in them is a new finding. The test script's own fake values must be built at runtime.
**How to avoid:** run `gitleaks dir` over each new planning file before committing (the pre-commit hook does this once installed). Describe path shapes in words ("the macOS home prefix plus the user folder") rather than spelling an example with a real name.

### Pitfall 8: Flip step executed by an autopilot
**What goes wrong:** `gsd` config here is `mode: yolo`, `workflow.auto_advance: false`, `human_verify_mode: "end-of-phase"` [VERIFIED: read `.planning/config.json`]. How the executor treats a `checkpoint:human-verify` under yolo or end-of-phase deferral was not verified [ASSUMED, A7]. A deferred or auto-approved checkpoint must never carry the flip.
**How to avoid:** plan 01-03 is `autonomous: false`; the flip is not in any `<action>`. The executor's last task is a `checkpoint:decision` (or `human-action`) that prints the evidence and asks for the go-word in plain text; the flip command lives only in the checkpoint's "on approval" note for the main conversation to run itself. The go-word must come from bokiko's own message in the current conversation, not from any agent message.

## Code Examples

### Mirror scan, strict and gate (tested; exit codes observed)
```bash
# Source: verified on gitleaks 8.30.0 against a real mirror of bokiko/preclear (14 commits)
W=$(mktemp -d)                                   # new directory, never reused or deleted
git clone --mirror https://github.com/bokiko/preclear.git "$W/preclear.git"
mkdir "$W/empty" "$W/accepted"
git -C "$W/preclear.git" show HEAD:.gitleaks.toml    > "$W/gitleaks.toml"
git -C "$W/preclear.git" show HEAD:.gitleaksignore   > "$W/accepted/.gitleaksignore"

# strict: accepted list OFF  -> expect exit 2, 19 matches, 15 unique fingerprints, all commit d437af2
gitleaks git "$W/preclear.git" -c "$W/gitleaks.toml" -i "$W/empty" --no-banner --redact \
  --exit-code 2 --log-opts="--all" -f json -r "$W/strict.json" -l error; echo "strict exit=$?"

# gate: accepted list ON     -> expect exit 0, "no leaks found"
gitleaks git "$W/preclear.git" -c "$W/gitleaks.toml" -i "$W/accepted" --no-banner \
  --exit-code 2 --log-opts="--all" -l info; echo "gate exit=$?"

# metadata: exactly one identity, equal to the pinned one
git -C "$W/preclear.git" log --all --format='%an <%ae>%n%cn <%ce>' | sort -u

# set equality between actual strict findings and the committed accepted list
python3 -I - "$W/strict.json" "$W/accepted/.gitleaksignore" <<'PY'
import json, sys
found = {x["Fingerprint"] for x in json.load(open(sys.argv[1]))}
listed = {l.strip() for l in open(sys.argv[2]) if l.strip() and not l.startswith("#")}
print("found", len(found), "listed", len(listed), "equal", found == listed)
sys.exit(0 if found == listed else 1)
PY
```
Observed: strict exit 2 with 19 matches, 13 `home-path-unix` plus 6 `home-path-dash-slug`, 15 unique fingerprints; gate exit 0 ("14 commits scanned", "no leaks found"); `.gitleaksignore` accepts a `#` comment header and either a directory or a file path for `-i`.

### Generating `.gitleaksignore` from the strict report
```bash
python3 -I - "$W/strict.json" > .gitleaksignore <<'PY'
import json, sys
print("# Accepted historical findings (owner decision 2026-10-21, see .planning/PROJECT.md Key Decisions).")
print("# Home-folder path lines in commit d437af2 (11 lines in 10 evidence files), immutable history.")
for fp in sorted({x["Fingerprint"] for x in json.load(open(sys.argv[1])) if x["RuleID"] in ("home-path-unix", "home-path-dash-slug")}):
    print(fp)
PY
```
Fingerprint format in git mode is `<commit>:<file>:<rule-id>:<line>` [CITED: gitleaks README]; staged mode prints `<file>:<rule-id>:<line>` [VERIFIED: observed].

### Read-only live-repo inventory (values observed 2026-10-21; this is the expected baseline)
```bash
R=bokiko/preclear
git ls-remote origin                                   # HEAD and refs/heads/main only, both = local tip
git ls-remote --tags origin                            # empty
gh repo view $R --json visibility,isPrivate --jq '.visibility+" "+(.isPrivate|tostring)'   # PRIVATE true
gh api repos/$R/branches --jq 'length'                 # 1
gh api repos/$R/tags --jq 'length'                     # 0
gh api repos/$R/hooks --jq 'length'                    # 0
gh api repos/$R/keys --jq 'length'                     # 0  (deploy keys)
gh issue list -R $R --state all --json number --jq 'length'   # 0
gh pr list    -R $R --state all --json number --jq 'length'   # 0
gh api repos/$R/actions/runs      --jq '.total_count'  # 0
gh api repos/$R/actions/workflows --jq '.total_count'  # 0
gh api repos/$R/actions/artifacts --jq '.total_count'  # 0
gh api repos/$R/actions/secrets   --jq '.total_count'  # 0
gh api repos/$R/actions/variables --jq '.total_count'  # 0
gh api repos/$R --jq '.has_wiki'                       # false
gh api repos/$R/pages                                  # HTTP 404 Not Found (no Pages site); non-zero exit
gh api repos/$R/releases --jq 'length'                 # 0
gh api repos/$R/forks --jq 'length'                    # 0
gh api repos/$R/collaborators --jq '[.[].login]'       # ["bokiko"]
gh api repos/$R/invitations --jq 'length'              # 0
gh api repos/$R/environments --jq '.total_count'       # 0
gh api repos/$R/deployments --jq 'length'              # 0
gh api repos/$R/activity --paginate --jq '.[].activity_type' | sort | uniq -c   # branch_creation 1, push 8: no force_push, no branch_deletion
```
Also observed and worth recording: Dependabot alerts, code scanning and secret scanning are all disabled; `security_and_analysis` is `null` while the repo is private on this plan; rulesets return HTTP 403 "Upgrade to GitHub Pro or make this repository public"; community profile health 57 (code of conduct, contributing, issue and PR templates, license, readme present). Description is set; topics empty; 10 labels; Projects enabled, Discussions off.

### Visibility flip and protections (human-gated; not executed in research)
```bash
# Pre-conditions asserted immediately before, in the same session:
gh repo view bokiko/preclear --json visibility --jq .visibility                  # PRIVATE
curl -s -o /dev/null -w '%{http_code}\n' https://github.com/bokiko/preclear      # 404  (observed today)
GIT_TERMINAL_PROMPT=0 git -c credential.helper= ls-remote https://github.com/bokiko/preclear.git   # fatal, exit 128 (observed today)

# ONLY after bokiko's go-word, run in the main conversation:
gh repo edit bokiko/preclear --visibility public --accept-visibility-change-consequences

# Immediately after, sequential (gh states secret scanning must be enabled first):
gh repo edit bokiko/preclear --enable-secret-scanning
gh repo edit bokiko/preclear --enable-secret-scanning-push-protection
# equivalent REST shape: PATCH /repos/bokiko/preclear with
#   {"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}

# Read back:
gh repo view bokiko/preclear --json visibility --jq .visibility                  # PUBLIC
gh api repos/bokiko/preclear --jq '.security_and_analysis | [.secret_scanning.status, .secret_scanning_push_protection.status]'   # ["enabled","enabled"]
curl -s -o /dev/null -w '%{http_code}\n' https://github.com/bokiko/preclear      # 200
```
Flag names confirmed from the installed `gh repo edit --help` (2.83.2): `--visibility string` (`public`, `private`, `internal`), `--accept-visibility-change-consequences` (required whenever `--visibility` is used), `--enable-secret-scanning`, `--enable-secret-scanning-push-protection` ("Secret scanning must be enabled first"). The documented `security_and_analysis` PATCH keys include `secret_scanning` and `secret_scanning_push_protection`, each with a `status` of enabled or disabled, and require repository admin permission [CITED: docs.github.com/en/rest/repos/repos#update-a-repository]. Secret scanning alerts for users "can be enabled on any free public repository that you own" [CITED: docs.github.com enabling-secret-scanning-for-your-repository]; repository-level push protection is "disabled by default, and can be enabled by a repository administrator" [CITED: docs.github.com about-push-protection]. Whether both toggles succeed on this free account is the one thing not testable while the repo is private (A2); if the second call fails, record the error verbatim and stop for bokiko.

## PROJECT.md edit targets (PUB-01)

Current Key Decisions rows [VERIFIED: read `.planning/PROJECT.md` lines 67-79]:
- Row at line 75, verbatim start: "No history rewrite; ... stays the public identity (2026-10-21)". It combines two decisions in one row and its Outcome is "Pending".
- Row at line 76: "Row 7 ships as a disclosed known issue, rerun three times in this milestone". **It carries no date**, while ROADMAP SC1 requires all three decisions "with dates".

Recommendation: split line 75 into two rows (history, identity), keep row 7 as the third, and set each Outcome to a decided state with its date. The only dated source for row 7 is that PUB-01 itself was written 2026-10-21, so the date should be confirmed by bokiko before it is written (A3). Mechanical check: three rows, each containing `2026-10-21` and none ending in `Pending`.

Factual corrections to fold in while editing (all verified today): the history has **14 commits** (PITFALLS says 11); the d437af2 cluster is **eleven lines in ten files**, not "ten lines" (PROJECT.md, REQUIREMENTS PUB-02 and ROADMAP SC2 all say ten). 020778b, the sanitizing commit, shows "10 files changed, 11 insertions(+), 11 deletions(-)".

## True hit counts (the allowlist size the planner needs)

All counts from this session's `git grep`, `git log -p` and gitleaks runs over the 14 commits (tip 56e155c).

| Question | Result |
|----------|--------|
| Current tree, home path with a user-name segment | 0 lines |
| Current tree, bare `/Users/` or `/home/` | 1 line (`ARCHITECTURE.md:65`, prose naming both prefixes) |
| Current tree, `/private/var` | 2 lines (`PITFALLS.md:67`, `PITFALLS.md:258`, prose) |
| Current tree, dash-slug form | 0 |
| History, added lines with `/Users/` | 12 (11 in d437af2, 1 in cd8af5c = the `ARCHITECTURE.md:65` prose) |
| History, added lines with `/home/` | 1 (cd8af5c, same prose line) |
| History, added lines with the dash-slug | 4, all in d437af2 |
| d437af2 distinct added lines with a home path or slug | **11 lines in 10 files** |
| gitleaks matches in d437af2 (my rules) | 19 matches = 13 `home-path-unix` + 6 `home-path-dash-slug` |
| gitleaks unique fingerprints (the `.gitleaksignore` size) | **15** (11 unix + 4 slug) |
| Private IPv4 or any dotted quad, tree or history | 0 |
| Hostnames: `hostname`, `hostname -s`, both `scutil` names, tree and history | 0 (checked by count only) |
| Default gitleaks rules over all history | 0 findings |
| Email in tree | 2 lines (`PROJECT.md:75`, `REQUIREMENTS.md:15`), both added in 0de513f |
| Distinct author and committer identities across all refs | 1 (author equals committer on all 14 commits) |
| Commit messages: anchored trailer grep (co-authored, signed-off, assisted, generated-by, reviewed-by) | 0 hits; a loose word grep for "claude" hits 2 real commit bodies, which is why the pattern file is anchored |
| Tracked files | 1,294 (1,246 under `tests/evidence`); no `.env`, key, db or credential-named files |
| Session-id-shaped UUIDs in the tree | 154 (not credentials; see Open Question 5) |
| `LICENSE` copyright holder | `bokiko` |

`id -F` on this Mac returns a 6-character string equal to the handle, so the real name cannot be derived at run time; an optional local-only deny list (below) is the way to cover it.

### Optional local deny list (not committed)
A hook step can build entries at run time from `hostname`, `hostname -s`, `scutil --get LocalHostName` and `ComputerName`, plus lines in `.git/info/preclear-deny.txt` (inside `.git`, so never committed; bokiko can put the real name there). Tested: `git diff --cached -U0 | grep '^+' | grep -v '^+++' | grep -i -c -F -f <list>` returns the count for staged content, and `git log -p -U0 --format= <range>` for pushed ranges. Print counts and file names only, never the matched value. This covers the privacy rule for the real name and machine names without committing them. It is an addition beyond PUB-02 and can be one small `checks/denylist.sh`.

## Disclosure content (PUB-06)

Where it lives now: `README.md` has "Tests" (line ~268) and a Roadmap checklist whose open items are "Clean rerun of publication row 7 (unsupported Do-not-redo entry)" and "Public release". `CHANGELOG.md` `[Unreleased]` already carries one sentence on row 7 and says "The repository stays private until the public-content and history audit is accepted and publication is explicitly approved", which becomes false at the flip and must be updated. The evidence README (`tests/evidence/publication-2026-10-20/README.md`) stays untouched.

Facts to quote [VERIFIED: read the evidence READMEs and row digests this session]:
- **Row 7 (all destinations denied):** PASS for destination handling; FAIL for evidence integrity (Codex). The printed checkpoint's "Do not redo" section claims a "Workspace policy/registry checked" fact that no tool call in that turn supports. Preserved as produced. A clean content pass needs a fresh targeted checkpoint turn, not yet run. Planned: three reruns (Phase 4).
- **Carried-forward rows 1, 2, 3c, 4b:** first-pass rows ran on skill digest `bbda28403d95` and adapter `272838d4722d`; after the three changes (Step 4 per-section measurement, stop after the first denied helper write, "persistence not ownership") they carried forward unchanged because no edit changed the behaviour they test (evidence README lines 38 to 43). They have not been rerun on the later digests.
- **NUL `-z` form never executed:** the sidecar form with `-z` has not run under the headless tool policy (output redirection needs approval). Rows 10 and 11 passed through the documented quoted-porcelain fallback (`references/status-sidecar.md`). The allowlist did not match the skill's exact status command until the row 10 and 11 reruns, so earlier runs, including the three accepted layouts, used a declared plain-porcelain fallback and are not exact-command tests.
- **New, not in any current document: the shipped `SKILL.md` digest was never run.** Rows 5 to 12 and the 3a/3b reruns recorded skill `6d22a71e7f3c` and adapter `eca134a3defc`. Current `SKILL.md` is `86e5b14e64b1` (11,994 bytes); the adapter `eca134a3defc` still matches. Commit 188930b (rows 5 to 12) changed `SKILL.md` by 14 lines (Do-not-redo wording, a status-sidecar pointer) and added `references/status-sidecar.md`. The Phase 4 rerun is therefore the first run of the shipped text and is a new baseline. bokiko should see this before the disclosure is written.
- Smaller items already in the evidence README worth one line: defect D1 (the model's cap statements disagreed with the independent manifest in 5 of 12 checkpoint-producing runs) and the disclosed row 12 overrun (Resume reading 712 of 600 bytes).
- The evidence README ends with "see ... private audit record before any visibility change". A reader cannot follow it. Do not edit the historical file; say in the new disclosure that the audit record is not part of the repository and that the reproducible scan is `.gitleaks.toml` plus the mirror-scan script.

Minimal shape (README "Known issues" section above "Roadmap", plus a CHANGELOG entry):
```markdown
## Known issues and limits

- **Row 7 (all destinations denied):** destination handling passed; evidence integrity failed. The printed checkpoint
  lists a "workspace policy/registry checked" entry that no tool call in that turn supports. Kept as produced.
  A rerun (three runs) is planned; the Roadmap item stays open.
- **Rows 1, 2, 3c, 4b carry forward** from the first pass (skill `bbda28403d95`, adapter `272838d4722d`); not rerun
  on later digests.
- **Shipped skill digest not run:** matrix rows ran on skill `6d22a71e7f3c`; the shipped `SKILL.md` is `86e5b14e64b1`
  (wording edits after the rows). A full rerun on the shipped text is planned and will be filed as a new baseline.
- **NUL `-z` status form never executed** under the headless tool policy; rows 10 and 11 exercised the documented
  quoted-porcelain fallback. Earlier acceptances are not exact-command tests.
- Details: `tests/evidence/publication-2026-10-20/README.md`. Reviewer verdicts there came from a private review
  and are recorded, not independently reproducible yet.
```
Keep it free of home paths, hostnames, the address and any AI attribution. Commit and push it (private) before the flip; the ancestor check `git merge-base --is-ancestor <disclosure-sha> <tip-at-flip>` proves "before".

## Runtime State Inventory

Not a rename, refactor or migration phase. Omitted.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `includeCoAuthoredBy` setting | `attribution` object with `commit`, `pr`, `sessionUrl` | deprecated since Claude Code v2.0.62; `attribution: false` form from v2.1.281 [CITED: settings reference] | Use the empty-string form for compatibility |
| `gitleaks detect` / `gitleaks protect` | `gitleaks git`, `gitleaks dir`, `gitleaks stdin` | v8.19+ era; installed 8.30.0 exposes only `dir`, `git`, `stdin` [VERIFIED: `gitleaks --help`] | Old subcommand names in blog posts will not work |
| `.gitleaks.toml` allowlist as a single `[allowlist]` | `[[allowlists]]` with `condition`, `targetRules`, `regexTarget` [CITED: gitleaks README] | recent 8.x | Use the plural table array |
| Secret scanning only for private repos with Advanced Security | Secret Protection naming; free for user-owned public repos [CITED: GitHub docs] | 2025 | Toggles available right after the flip |

**Deprecated/outdated:** pre-commit framework `repos:` hook for gitleaks is valid but unnecessary here; `git filter-repo` guidance in the project research is moot because the rewrite decision is "no".

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `pre-commit` framework's installer refuses or conflicts when `core.hooksPath` is set | Standard Stack, Alternatives | Low; it is already rejected on other grounds |
| A2 | Both `--enable-secret-scanning` and `--enable-secret-scanning-push-protection` succeed on a free-account public repo owned by a user | Visibility flip | Medium; if either errors, record verbatim and stop for bokiko (the flip would already be done, so the post-flip window has no protection beyond local hooks; do not push during that window) |
| A3 | The row 7 decision dates to 2026-10-21 | PROJECT.md edit targets | Low; wrong date in a decisions table. Ask bokiko to confirm before writing it |
| A4 | The owner's real name is absent from the repo | True hit counts | Medium; cannot be checked without the string. The 2026-10-20 private audit says none. Mitigate with the optional local deny list, filled by bokiko |
| A5 | `gh repo edit --enable-secret-scanning*` issues the same PATCH as the documented REST body | Visibility flip | Low; the REST form is the fallback |
| A6 | GitHub account setting "Block command line pushes that expose my email" state is unknown | Pitfall 2 | Low; all 14 commits with the current identity already pushed successfully, so it is not blocking this identity |
| A7 | How GSD treats `checkpoint:human-verify` under `mode: yolo` and `human_verify_mode: end-of-phase` | Pitfall 8 | High if wrong, which is why the flip is kept out of every task action and gated by an explicit go-word instead |
| A8 | Owner-mode identity pin (opt-in via local config) is preferred over enforcing the owner's identity on every contributor's clone | Architecture Pattern 2 | Low; if bokiko wants unconditional enforcement, hard-code the identity from a committed file and add that path to the email allowlist |
| A9 | Secret scanning status may take a moment to read back as `enabled` right after the PATCH | Visibility flip | Low; re-read once before reporting failure |

## Open Questions (RESOLVED)

Each item below is disposed in the phase plans. Where the answer belongs to bokiko, the disposition is the pointer to the plan 01-04 go or no-go checkpoint item (Task 3, items a to g) that asks him; nothing here is decided on his behalf, and every pointer names the plan task that carries it.

1. **Restate PUB-02 / SC2 in verifiable terms** (RESOLVED)
   - What we know: the cluster is 11 lines in 10 files, 19 matches, 15 fingerprints; the "author email" is metadata plus two allowlisted doc lines, not a gitleaks finding.
   - What's unclear: whether bokiko wants the docs corrected from "ten lines" to "eleven lines in ten files".
   - Recommendation: correct the counts in `PROJECT.md` during 01-01 and define PUB-02 as the three checks in Pitfall 3.
   - Disposition (RESOLVED): flagged assumptions FA-1 and FA-2 in `01-01-PLAN.md`. `REQUIREMENTS.md` and `ROADMAP.md` wording is left unedited; the measured counts go into the "No history rewrite" row (`01-01-PLAN.md` Task 3) and the acceptance criteria of `01-02-PLAN.md` Task 1. PUB-02 is proven as strict-equals-accepted, gate-clean, tree-clean and one-identity in `01-02-PLAN.md` Task 1 and `01-03-PLAN.md` Task 1.
2. **Shipped skill digest not run in any row** (see Disclosure content) (RESOLVED)
   - Recommendation: include it in the disclosure and tell bokiko before the disclosure commit; it does not block the flip but changes what "accepted" means publicly.
   - Disposition (RESOLVED): drafted as the README bullet "Shipped skill digest not run:" in `01-03-PLAN.md` Task 2 (FA-4b, claims re-verified by its verify). Whether it is published as drafted, edited or dropped is bokiko's call at `01-04-PLAN.md` Task 3, item a.
3. **Evidence README points to a private audit record.** (RESOLVED)
   - Recommendation: leave the file, add one clarifying sentence in the new disclosure. Evidence integrity forbids editing it.
   - Disposition (RESOLVED): the "Details:" line of the new README section in `01-03-PLAN.md` Task 2 states that the audit record is not part of the repository; the historical evidence file is not edited (prohibition and T-01-20 in `01-03-PLAN.md`).
4. **Where the pre-flip record is committed.** (RESOLVED)
   - Recommendation: `.planning/phases/01-publication-gate/01-PREFLIP-INVENTORY.md`, generated by `scripts/prepublish-check.sh`, committed and pushed last; the script records the scanned tip SHA and a fresh run of the read-only commands.
   - Disposition (RESOLVED): `01-04-PLAN.md` Task 2 writes that path with `scripts/prepublish-check.sh` in record mode (numbered name if the file exists) and commits only that file; it is pushed under the go-word in Task 4 (Task 3 on-approval step 2). The post-flip read-back is a second record, `01-POSTFLIP-READBACK.md`, written in Task 4 and verified in Task 5.
5. **154 session-id-shaped UUIDs in evidence.** They identify transcripts, not credentials. Recommendation: accept explicitly in the decisions table (one line) rather than normalizing historical evidence. (RESOLVED)
   - Disposition (RESOLVED): not decided in the plans. `01-01-PLAN.md` Task 3 deliberately adds no row; bokiko decides at `01-04-PLAN.md` Task 3, item d. A "yes" is an edit, so it is answered with "changes:" and followed by a regenerated record, never with the go-word alone.
6. **Attribution suppression files.** Committing `.claude/settings.json` and a one-line `CLAUDE.md` rule changes the public file set slightly. Recommendation: do it; it is the documented source-level fix. Ask bokiko only if he objects to either file being public. (RESOLVED)
   - Disposition (RESOLVED): both files are created in `01-01-PLAN.md` Task 3; bokiko's acceptance of them becoming public is asked explicitly at `01-04-PLAN.md` Task 3, item c, before any flip.
7. **Does bokiko want gitleaks upgraded to 8.30.1?** Behaviour here was verified on 8.30.0; a bump needs the same strict/gate re-run. Recommendation: leave at 8.30.0 for this phase and write "8.30.x tested on 8.30.0" in the hooks README. (RESOLVED)
   - Disposition (RESOLVED): `01-02-PLAN.md` Task 1 requires 8.30.x and Task 3 writes "8.30.0" as the tested version into `.githooks/README.md`; whether to stay on 8.30.0 is bokiko's call at `01-04-PLAN.md` Task 3, item e.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| gitleaks | PUB-02, PUB-03 | yes | 8.30.0 (8.30.1 exists) | none needed; hooks fail closed if absent |
| git | all | yes | 2.50.1 | none |
| gh | PUB-05, PUB-07 | yes, authenticated as bokiko, ADMIN on the repo | 2.83.2 | none |
| python3 | check scripts | yes | 3.14.7 | none |
| shellcheck | lint of hooks | yes | 0.11.0 | skip lint |
| curl | public/private probe | yes | system | `gh api` |
| pre-commit framework | not used | no | n/a | n/a |
| lefthook | not used | no | n/a | n/a |
| Network to github.com | mirror clone, inventory | yes (clone and API calls succeeded) | n/a | none |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none required.
Shell notes: `/bin/sh` is bash 3.2.57 on macOS 26.6.2; the hook scripts use only POSIX constructs and passed shellcheck apart from the two intentional warnings. The `gh` token also carries `delete_repo` and `workflow` scopes: no plan task may use them.

## Validation Architecture

(`workflow.nyquist_validation` is `false` in `.planning/config.json`; this section is included because the caller asked for it.)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | POSIX sh scripts plus `python3 -I` for JSON set checks; no test runner to install |
| Config file | none; checks live in `scripts/test-hooks.sh` (throwaway clone) and `scripts/prepublish-check.sh` (read-only mirror and inventory) |
| Quick run command | `sh scripts/test-hooks.sh` |
| Full suite command | `sh scripts/test-hooks.sh && sh scripts/prepublish-check.sh` |

Each script prints one `PASS <name>` / `FAIL <name>: <reason>` line per check and exits non-zero on any FAIL. Neither script may call `git push` against `origin`, `gh repo edit`, or any write API.

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | Failure signal |
|--------|----------|-----------|-------------------|----------------|
| PUB-01 | Three dated, decided rows in Key Decisions (history, identity, row 7) | static | `grep -c -E '^\| .*(history rewrite\|public identity\|Row 7).*2026-10-21' .planning/PROJECT.md` prints 3 (adjust the three alternatives to the final row titles), and the same three rows contain no `Pending` (`grep -c Pending` over just those rows prints 0) | count not 3, or any Pending |
| PUB-04 | Identity pinned locally | config | `git config --local --get user.useConfigOnly` prints `true`; `git config --local --get user.name` prints `bokiko`; `git config --local --get preclear.pinnedIdentity` equals the public identity; `git config --get core.hooksPath` prints `.githooks` | any empty or different value |
| PUB-04 | Wrong identity refused | integration (throwaway clone) | `scripts/test-hooks.sh` case "wrong identity": push exits non-zero and stderr contains `identity check FAILED` | exit 0, or message missing |
| PUB-04 | AI trailer refused | integration | cases "trailer at commit-msg" (commit exit 1, stderr `commit-msg FAILED`) and "trailer, bypassed" (push exit non-zero, stderr `attribution check FAILED`) | exit 0 |
| PUB-04 | Repo history carries no trailer or foreign identity | static | `git log --all --format=%B \| grep -i -E -f .githooks/attribution.ere` exits 1 (no match); `git log --all --format='%an <%ae>%n%cn <%ce>' \| sort -u \| wc -l` prints 1 | match found, or count not 1 |
| PUB-02 | Strict scan equals the accepted list | integration (fresh mirror) | mirror recipe: strict run exits 2; python check prints `equal True`, `found 15 listed 15`, and every finding's commit starts with `d437af2` | exit not 2, sets differ, any other commit or rule |
| PUB-02 | Gate scan clean | integration | gate run exits 0 and prints `no leaks found` | exit 2 (finding) or 1 (tool error, distinct) |
| PUB-02 | Tree scan | integration | `git clone <mirror> t; gitleaks dir t -c cfg -i empty --exit-code 2` exits 0 | any finding |
| PUB-02 | Config and accepted list committed | static | `git ls-files --error-unmatch .gitleaks.toml .gitleaksignore .githooks/pre-commit .githooks/pre-push` exits 0 | pathspec error |
| PUB-03 | Seeded secret blocked at commit | integration | case "seed pre-commit": `git commit` exits non-zero, stderr contains `aws-access-token`, `git rev-list --count HEAD` unchanged | commit succeeded |
| PUB-03 | Seeded secret blocked at push | integration | case "seed pre-push": push exits non-zero, `git -C remote.git cat-file -e <seed-sha>` exits non-zero | seed present on remote |
| PUB-03 | Seed never in real history | static | after tests, `gitleaks git . -c .gitleaks.toml --exit-code 2 --log-opts=--all` exits 0 on the real repo, and `git log --all -S"AKIA" --oneline` prints nothing | any output |
| PUB-03 | One-command enable works in a fresh clone | integration | `git clone <pushed repo> c && cd c && git config core.hooksPath .githooks`, then a seeded commit is refused | commit allowed |
| PUB-03 | Hook modes and lint | static | `git ls-files -s .githooks` shows `100755` for executables; `shellcheck -s sh .githooks/pre-push .githooks/pre-commit .githooks/commit-msg .githooks/checks/*.sh` reports only SC2034/SC2086 unless annotated | other findings |
| PUB-06 | Disclosure present and committed before flip | static | `grep -c -i -E 'row 7' README.md` at least 1; `grep -c -E 'rows? 1, 2, 3c' README.md CHANGELOG.md` at least 1; `grep -c -i 'NUL' README.md CHANGELOG.md` at least 1; `git merge-base --is-ancestor <disclosure-sha> HEAD` exits 0 | any zero count |
| PUB-06 | Disclosure leaks nothing | static | `gitleaks dir README.md CHANGELOG.md -c .gitleaks.toml --exit-code 2` exits 0 | finding |
| PUB-05 | Inventory matches the reviewed baseline | integration (read-only) | `scripts/prepublish-check.sh` prints `INVENTORY OK` and each category line equals the baseline in "Code Examples"; any deviation prints `UNREVIEWED: <category>` and exits 1 | `UNREVIEWED` |
| PUB-05 | Scanned tip is the pushed tip | integration | `git ls-remote origin refs/heads/main` equals `git rev-parse HEAD`; mirror tip equals both | mismatch |
| PUB-07 | Still private before the go-word | integration | `gh repo view bokiko/preclear --json visibility --jq .visibility` prints `PRIVATE`; `curl -s -o /dev/null -w '%{http_code}' https://github.com/bokiko/preclear` prints `404` | `PUBLIC` or 200 |
| PUB-07 | Public after the go-word | integration | `gh repo view ... --jq .visibility` prints `PUBLIC`; curl prints `200` | otherwise |
| PUB-07 | Protections on | integration | `gh api repos/bokiko/preclear --jq '.security_and_analysis.secret_scanning.status,.security_and_analysis.secret_scanning_push_protection.status'` prints `enabled` twice | `disabled`, `null` or HTTP error |

Manual-only checks (justified): bokiko's go-word (cannot be automated by design); confirmation of the row 7 decision date; reading the disclosure text.

### Sampling Rate
- **Per task commit:** `sh scripts/test-hooks.sh` (a few seconds) plus the hooks themselves running on the commit.
- **Per wave merge:** add the mirror-scan recipe against the private remote after pushing.
- **Phase gate:** full suite green and a fresh inventory taken in the same session as the go-word, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `scripts/test-hooks.sh` (throwaway clone, bare local remote, runtime-built seeds) covers PUB-03, PUB-04
- [ ] `scripts/prepublish-check.sh` (mirror, set equality, identity, trailers, inventory) covers PUB-02, PUB-05
- No framework install needed; gitleaks, gh, git, python3, shellcheck are present.

## Security Domain

`security_enforcement` is enabled in `.planning/config.json` (ASVS level 1, block on high).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (no app auth) | `gh` keyring credential only; no token ever written to a file or argv |
| V3 Session Management | no | n/a |
| V4 Access Control | yes | Visibility flip and any rewrite restricted to bokiko's explicit word; hooks cannot be the only gate |
| V5 Input Validation | yes | Hook scripts quote ref and sha values from stdin; `$rev` is built only from a sha, fixed tokens and the remote name |
| V6 Cryptography | no | none used |
| V7 Error Handling and Logging | yes | `--redact` on every gitleaks call; print counts and file names, never matched values; no reports committed |
| V10 Malicious Code / supply chain | yes | One pinned, already-installed scanner; no new packages; no `curl \| sh` |
| V14 Configuration | yes | Config and hooks committed; `core.hooksPath` documented; fail closed when gitleaks is missing |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `--no-verify` skips local hooks | Tampering / Repudiation | pre-push authoritative net, pre-flip mirror scan from outside the working copy, post-flip push protection for secrets |
| Wrong identity via `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env | Spoofing | pre-push checks all four fields plus tagger; `useConfigOnly` for the no-config case |
| Hostname-derived address when no identity configured | Information disclosure | `user.useConfigOnly true` plus local pin (tested) |
| Report files or logs echo the leaked value | Information disclosure | `--redact`; reports outside the repo; never `--redact=0` in committed paths |
| Scanner missing or crashing is read as clean | Tampering | hooks `exit 1` when gitleaks is absent; `--exit-code 2` separates findings (2) from errors (1, 126) |
| Time-of-check to time-of-use between scan and flip | Tampering | record scanned tip SHA; require remote tip equals it at the go-word; only the record file may differ |
| Accidental visibility change by an executor | Elevation of privilege | flip only in the checkpoint, never in an `<action>`, script or subagent; the consequence flag is never passed on someone's behalf |
| AI attribution trailer slips into public history | Repudiation / policy | source suppression (`attribution` empty), CLAUDE.md rule, commit-msg, pre-push |
| Test fixtures committed as real secrets | Information disclosure | build fake values at runtime from fragments; never store the literal |

## Sources

### Primary (HIGH confidence)
- Local runs this session on gitleaks 8.30.0, git 2.50.1, gh 2.83.2: mirror clone of `bokiko/preclear`, scratch clones with bare remotes, `gitleaks git/dir` with `--log-opts`, `-i`, `-c`, `--staged`, `--redact`, `--exit-code`; `git config` semantics; hook behaviours.
- `gh api` read-only calls on `bokiko/preclear` (repo, branches, tags, hooks, keys, issues, PRs, Actions, pages, releases, forks, collaborators, activity, community profile), `gh repo edit --help` (2.83.2).
- Repo files read: `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json`, `tests/evidence/publication-2026-10-20/README.md` and row 7 README, `README.md`, `CHANGELOG.md`, `references/status-sidecar.md`, `.gitignore`.
- GSD install: `bin/lib/commands.cjs` commit path (hooks run unless `--no-verify` is passed).

### Secondary (MEDIUM confidence)
- gitleaks README (raw.githubusercontent.com/gitleaks/gitleaks/master/README.md): subcommands, `--log-opts`, exit codes, config tables, `.gitleaksignore` git-mode fingerprint, baseline.
- code.claude.com/docs/en/settings-reference (`attribution`, `attribution.commit`, `includeCoAuthoredBy`).
- docs.github.com REST "Update a repository" (`security_and_analysis`, admin permission); "Enabling secret scanning for your repository"; "About push protection".

### Tertiary (LOW confidence)
- A web search for push protection on free public repos returned only Enterprise Server pages; it confirmed nothing new, hence A2.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - tools present and exercised.
- Architecture: HIGH - hooks and mirror recipe tested end to end in throwaway clones.
- Pitfalls: HIGH - each reproduced or read from the repo, except A2, A7.
- GitHub post-flip toggles on a free account: MEDIUM - documented, not testable while private.

**Research date:** 2026-10-21
**Valid until:** 2026-11-20 (gitleaks and `gh` flags are stable; recheck GitHub secret-protection wording and the Claude Code `attribution` page if the phase slips)
