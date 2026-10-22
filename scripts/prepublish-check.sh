#!/bin/sh
# Pre-flip check for the publication gate.
#
# READ-ONLY. It clones a mirror of the source into a new temporary directory, scans that
# mirror, and reads repository facts from the hosting service. It changes nothing on the
# remote and has no switch that does. Output is PASS / FAIL / SKIP lines, counts and
# booleans: a matched value, a temporary path, a home path or a host name is never printed.
# The reports and the mirror stay under the temporary directory and are never deleted.
#
# Usage: sh scripts/prepublish-check.sh [--rehearse] [--source SRC] [--skip-inventory] [--record FILE]
#   default     the source is the origin URL; the remote tip must equal local HEAD; --record
#               may write a record file (created exclusively, never overwritten).
#   --rehearse  the source is --source (a path or URL; default: this repository) and the
#               tip check is skipped; --record is refused, so a rehearsal leaves no record.
#   --skip-inventory   leave out the live-repository inventory (needs no network for gh).
# Exit status: 0 when every check passed, 1 when any FAIL line was printed, 2 on bad usage.

usage() {
  echo "usage: sh scripts/prepublish-check.sh [--rehearse] [--source SRC] [--skip-inventory] [--record FILE]" >&2
  exit 2
}

REHEARSE=0
SKIP_INV=0
RECORD=
SOURCE=
while [ $# -gt 0 ]; do
  case $1 in
    --rehearse) REHEARSE=1 ;;
    --skip-inventory) SKIP_INV=1 ;;
    --record) [ $# -ge 2 ] || usage; RECORD=$2; shift ;;
    --source) [ $# -ge 2 ] || usage; SOURCE=$2; shift ;;
    *) usage ;;
  esac
  shift
done
if [ "$REHEARSE" -eq 1 ] && [ -n "$RECORD" ]; then
  echo "rehearsal never writes a record" >&2
  exit 2
fi
if [ "$REHEARSE" -eq 0 ] && [ -n "$SOURCE" ]; then
  echo "--source is only for --rehearse; the default source is the origin URL" >&2
  exit 2
fi
if [ -n "$RECORD" ] && [ -e "$RECORD" ]; then
  echo "record file already exists; this script never overwrites" >&2
  exit 2
fi

TOP=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "not inside a git repository" >&2; exit 2; }
cd "$TOP" || exit 2
GIT_TERMINAL_PROMPT=0
GH_PROMPT_DISABLED=1
GH_NO_UPDATE_NOTIFIER=1
NO_COLOR=1
export GIT_TERMINAL_PROMPT GH_PROMPT_DISABLED GH_NO_UPDATE_NOTIFIER NO_COLOR

W=$(mktemp -d "${TMPDIR:-/tmp}/preclear-prepublish.XXXXXX") || { echo "no temporary directory" >&2; exit 2; }
: > "$W/rows"
: > "$W/inv"
FAILS=0
note() { printf '%s|%s|%s\n' "$1" "$2" "$3" >> "$W/rows"; }
pass() { if [ -n "$2" ]; then echo "PASS $1 ($2)"; else echo "PASS $1"; fi; note "$1" PASS "$2"; }
skip() { echo "SKIP $1 ($2)"; note "$1" SKIP "$2"; }
fail() { echo "FAIL $1: $2"; FAILS=$((FAILS + 1)); note "$1" FAIL "$2"; }

finish() {
  if [ "$FAILS" -gt 0 ]; then echo "RESULT FAIL ($FAILS check(s) failed)"; exit 1; fi
  echo "RESULT PASS"
  exit 0
}

for tool in git gitleaks python3; do
  command -v "$tool" >/dev/null 2>&1 || { fail tools "$tool not found"; finish; }
done
if [ "$SKIP_INV" -eq 0 ]; then
  command -v gh >/dev/null 2>&1 || { fail tools "gh not found"; finish; }
fi

# ---- owner-clone-config: the owner's clone enforces the hooks and the identity pin ----
hooks_path=$(git config --get core.hooksPath)
use_config_only=$(git config --get user.useConfigOnly)
pin=$(git config --local --get preclear.pinnedIdentity)
if [ "$hooks_path" = .githooks ] && [ "$use_config_only" = true ] && [ -n "$pin" ]; then
  pass owner-clone-config "hooks path set, identity pin set"
else
  fail owner-clone-config "need core.hooksPath=.githooks, user.useConfigOnly=true and preclear.pinnedIdentity set in this clone"
fi

# ---- mirror-cloned: scan what the source holds, not the working copy ----
origin_url=$(git remote get-url origin 2>/dev/null)
if [ "$REHEARSE" -eq 1 ]; then src=${SOURCE:-$TOP}; else src=$origin_url; fi
if [ -z "$src" ]; then fail mirror-cloned "no source: origin is not configured"; finish; fi
M="$W/mirror.git"
if git clone -q --mirror "$src" "$M" >/dev/null 2>&1; then
  tip=$(git -C "$M" rev-parse HEAD)
  pass mirror-cloned "mirror of the source cloned"
  echo "INFO mirror-tip $tip"
else
  fail mirror-cloned "git clone --mirror of the source failed"
  finish
fi

# ---- remote-tip-equals-head: default mode only ----
if [ "$REHEARSE" -eq 1 ]; then
  skip remote-tip-equals-head rehearsal
else
  remote_tip=$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)
  local_head=$(git rev-parse HEAD)
  if [ -n "$remote_tip" ] && [ "$remote_tip" = "$local_head" ] && [ "$remote_tip" = "$tip" ]; then
    pass remote-tip-equals-head "remote main, local HEAD and mirror tip agree"
  else
    fail remote-tip-equals-head "remote main, local HEAD and mirror tip are not the same commit"
  fi
fi

# The committed configuration is what is proven: copy it out of the mirror's HEAD.
mkdir "$W/empty" "$W/accepted" "$W/tree"
CFG_OK=1
git -C "$M" show HEAD:.gitleaks.toml > "$W/gitleaks.toml" 2>/dev/null || CFG_OK=0
git -C "$M" show HEAD:.gitleaksignore > "$W/accepted/.gitleaksignore" 2>/dev/null || CFG_OK=0
git -C "$M" show HEAD:.githooks/attribution.ere > "$W/attribution.ere" 2>/dev/null || CFG_OK=0

cat > "$W/compare.py" <<'PY_EOF'
import json
import sys

report, listed_path, rc = sys.argv[1], sys.argv[2], int(sys.argv[3])
allowed_rules = {"home-path-unix", "home-path-dash-slug"}
try:
    with open(report) as fh:
        data = json.load(fh)
except Exception:
    print("the strict report is missing or unreadable")
    sys.exit(1)
found = {x["Fingerprint"] for x in data}
with open(listed_path) as fh:
    listed = {ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")}
problems = []
if rc != 2:
    problems.append("strict exit %d, expected 2" % rc)
if found != listed:
    problems.append("fingerprint sets differ (found %d, listed %d, only found %d, only listed %d)"
                    % (len(found), len(listed), len(found - listed), len(listed - found)))
if len(found) != 15:
    problems.append("%d fingerprints, expected 15" % len(found))
outside = sum(1 for x in data if not x["Commit"].startswith("d437af2"))
if outside:
    problems.append("%d finding(s) outside commit d437af2" % outside)
other = sum(1 for x in data if x["RuleID"] not in allowed_rules)
if other:
    problems.append("%d finding(s) under a rule other than the two home-path rules" % other)
if problems:
    print("; ".join(problems))
    sys.exit(1)
print("strict exit 2; 15 fingerprints equal the accepted list; all in d437af2")
PY_EOF

# ---- strict-equals-accepted: with the accepted list OFF, the findings are exactly the list ----
if [ "$CFG_OK" -eq 1 ]; then
  gitleaks git "$M" -c "$W/gitleaks.toml" -i "$W/empty" --no-banner --redact --exit-code 2 \
    --log-opts="--all" -f json -r "$W/strict.json" -l error >/dev/null 2>&1
  strict_rc=$?
  if detail=$(python3 -I "$W/compare.py" "$W/strict.json" "$W/accepted/.gitleaksignore" "$strict_rc"); then
    pass strict-equals-accepted "$detail"
  else
    fail strict-equals-accepted "$detail"
  fi
else
  fail strict-equals-accepted "configuration files are missing from the mirror HEAD"
fi

# ---- gate-clean: with the accepted list ON, nothing is left ----
if [ "$CFG_OK" -eq 1 ]; then
  gitleaks git "$M" -c "$W/gitleaks.toml" -i "$W/accepted" --no-banner --redact --exit-code 2 \
    --log-opts="--all" -l error >/dev/null 2>&1
  gate_rc=$?
  if [ "$gate_rc" -eq 0 ]; then pass gate-clean "gate exit 0"
  else fail gate-clean "gate exit $gate_rc, expected 0"; fi
else
  fail gate-clean "configuration files are missing from the mirror HEAD"
fi

# ---- tree-clean: the committed tree itself needs no accepted list ----
if [ "$CFG_OK" -eq 1 ] && git -C "$M" archive HEAD | tar -x -C "$W/tree"; then
  gitleaks dir "$W/tree" -c "$W/gitleaks.toml" -i "$W/empty" --no-banner --redact --exit-code 2 -l error >/dev/null 2>&1
  tree_rc=$?
  if [ "$tree_rc" -eq 0 ]; then pass tree-clean "tree scan exit 0"
  else fail tree-clean "tree scan exit $tree_rc, expected 0"; fi
else
  fail tree-clean "could not extract the mirror HEAD tree"
fi

# ---- one-identity: every author, committer and tagger is the pinned identity ----
{
  git -C "$M" log --all --format='%an <%ae>%n%cn <%ce>'
  git -C "$M" for-each-ref --format='%(taggername) %(taggeremail)' refs/tags | grep -v '^[[:space:]]*$'
} 2>/dev/null | sort -u > "$W/ids"
id_count=$(wc -l < "$W/ids" | tr -d ' ')
if [ -z "$pin" ]; then
  fail one-identity "no preclear.pinnedIdentity to compare with"
elif [ "$id_count" -ne 1 ]; then
  fail one-identity "$id_count distinct identities in the history, expected 1"
elif [ "$(cat "$W/ids")" != "$pin" ]; then
  fail one-identity "the one identity in the history differs from the pin"
else
  pass one-identity "1 identity, equal to the pin"
fi

# ---- no-attribution-trailers: no commit message matches the attribution patterns ----
if [ -s "$W/attribution.ere" ]; then
  git -C "$M" log --all --format=%B > "$W/messages" 2>/dev/null
  trailer_hits=$(grep -i -E -c -f "$W/attribution.ere" "$W/messages")
  if [ "$trailer_hits" -eq 0 ]; then pass no-attribution-trailers "0 matching lines"
  else fail no-attribution-trailers "$trailer_hits matching line(s) in commit messages"; fi
else
  fail no-attribution-trailers "attribution patterns are missing from the mirror HEAD"
fi

# ---- denylist-history: no added line in any ref matches a local deny-list entry ----
dl_out=$(sh "$TOP/.githooks/checks/denylist.sh" --history "$M" 2>&1)
dl_rc=$?
if [ "$dl_rc" -ne 0 ]; then
  fail denylist-history "$dl_out"
elif printf '%s\n' "$dl_out" | grep -q 'skipped: no entries'; then
  skip denylist-history "no entries"
else
  pass denylist-history "0 added lines match"
fi

# ---- inventory: the live repository against the reviewed baseline ----
INV_BAD=0
INV_COUNT=0
# inv CATEGORY EXPECTED OBSERVED: one comparison; a difference is unreviewed state.
inv() {
  INV_COUNT=$((INV_COUNT + 1))
  printf '%s|%s|%s\n' "$1" "$2" "$3" >> "$W/inv"
  [ "$2" = "$3" ] && return 0
  echo "FAIL inv-$1: observed '$3', expected '$2'"
  echo "UNREVIEWED: $1"
  FAILS=$((FAILS + 1))
  INV_BAD=1
}
# ghv CMD...: print the command's output, or the word error when it fails.
ghv() {
  ghv_out=$("$@" 2>/dev/null) || { printf 'error'; return 0; }
  printf '%s' "$ghv_out"
}

if [ "$SKIP_INV" -eq 1 ]; then
  skip inventory "skipped by request"
else
  slug=$(printf '%s' "$origin_url" | sed -E 's#^.*github\.com[:/]##; s#\.git$##; s#/$##')
  case $slug in
    */*) ;;
    *) slug= ;;
  esac
  if [ -z "$slug" ] || printf '%s' "$slug" | grep -q -E '[^A-Za-z0-9._/-]'; then
    fail inventory "cannot derive the repository name from the origin URL"
  else
    owner=${slug%%/*}
    inv visibility "PRIVATE true" "$(ghv gh repo view "$slug" --json visibility,isPrivate --jq '.visibility+" "+(.isPrivate|tostring)')"

    refs=$(git ls-remote origin 2>/dev/null)
    ref_count=$(printf '%s\n' "$refs" | grep -c .)
    head_sha=$(printf '%s\n' "$refs" | awk '$2 == "HEAD" { print $1 }')
    main_sha=$(printf '%s\n' "$refs" | awk '$2 == "refs/heads/main" { print $1 }')
    if [ "$ref_count" -eq 2 ] && [ -n "$head_sha" ] && [ "$head_sha" = "$main_sha" ]; then refs_obs="2 refs, HEAD equals main"
    else refs_obs="$ref_count refs, HEAD and main not the only equal pair"; fi
    inv remote-refs "2 refs, HEAD equals main" "$refs_obs"
    inv remote-tags 0 "$(git ls-remote --tags origin 2>/dev/null | grep -c .)"

    inv branches 1 "$(ghv gh api "repos/$slug/branches" --jq length)"
    inv tags 0 "$(ghv gh api "repos/$slug/tags" --jq length)"
    inv hooks 0 "$(ghv gh api "repos/$slug/hooks" --jq length)"
    inv deploy-keys 0 "$(ghv gh api "repos/$slug/keys" --jq length)"
    inv issues 0 "$(ghv gh issue list -R "$slug" --state all --json number --jq length)"
    inv pull-requests 0 "$(ghv gh pr list -R "$slug" --state all --json number --jq length)"
    inv actions-runs 0 "$(ghv gh api "repos/$slug/actions/runs" --jq .total_count)"
    inv actions-workflows 0 "$(ghv gh api "repos/$slug/actions/workflows" --jq .total_count)"
    inv actions-artifacts 0 "$(ghv gh api "repos/$slug/actions/artifacts" --jq .total_count)"
    inv actions-secrets 0 "$(ghv gh api "repos/$slug/actions/secrets" --jq .total_count)"
    inv actions-variables 0 "$(ghv gh api "repos/$slug/actions/variables" --jq .total_count)"
    inv has-wiki false "$(ghv gh api "repos/$slug" --jq .has_wiki)"

    pages_out=$(gh api "repos/$slug/pages" 2>&1)
    pages_rc=$?
    if [ "$pages_rc" -ne 0 ] && printf '%s' "$pages_out" | grep -q '404'; then pages_obs="HTTP 404"
    elif [ "$pages_rc" -eq 0 ]; then pages_obs="a Pages site exists"
    else pages_obs=error; fi
    inv pages "HTTP 404" "$pages_obs"

    inv releases 0 "$(ghv gh api "repos/$slug/releases" --jq length)"
    inv forks 0 "$(ghv gh api "repos/$slug/forks" --jq length)"
    inv collaborators "$owner" "$(ghv gh api "repos/$slug/collaborators" --jq '[.[].login]|join(",")')"
    inv invitations 0 "$(ghv gh api "repos/$slug/invitations" --jq length)"
    inv environments 0 "$(ghv gh api "repos/$slug/environments" --jq .total_count)"
    inv deployments 0 "$(ghv gh api "repos/$slug/deployments" --jq length)"

    # The activity feed's push count rises with every push, so the set of event types is
    # compared, not a count: only branch_creation and push are reviewed.
    if types=$(gh api "repos/$slug/activity" --paginate --jq '.[].activity_type' 2>/dev/null); then
      type_obs=$(printf '%s\n' "$types" | sort -u | grep -v '^$' | tr '\n' ',' | sed 's/,$//')
      bad_types=$(printf '%s\n' "$types" | sort -u | grep -v -x -e branch_creation -e push -e '')
      if [ -z "$bad_types" ]; then type_obs="only branch_creation and push"; fi
    else
      type_obs=error
    fi
    inv activity-types "only branch_creation and push" "$type_obs"

    # Anonymous probes: a private repository is invisible to a caller with no credentials.
    http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://github.com/$slug" 2>/dev/null)
    if GIT_TERMINAL_PROMPT=0 git -c credential.helper= ls-remote "https://github.com/$slug.git" >/dev/null 2>&1
    then anon_obs="anonymous ls-remote succeeds"; else anon_obs="anonymous ls-remote refused"; fi
    inv public-probe "404, anonymous ls-remote refused" "$http_code, $anon_obs"

    sa_obs=$(ghv gh api "repos/$slug" --jq '.security_and_analysis')
    echo "INFO security_and_analysis ${sa_obs:-null}"
    echo "INFO topics $(ghv gh api "repos/$slug" --jq '.topics|length')"
    echo "INFO labels $(ghv gh api "repos/$slug/labels" --jq length)"
    echo "INFO community-health $(ghv gh api "repos/$slug/community/profile" --jq .health_percentage)"

    if [ "$INV_BAD" -eq 0 ]; then
      echo "INVENTORY OK"
      note inventory PASS "INVENTORY OK, $INV_COUNT categories"
    else
      note inventory FAIL "unreviewed state in the live repository"
    fi
  fi
fi

# ---- record: default mode only, only after a clean run; created exclusively ----
write_record() {
  ( set -C; : > "$RECORD" ) 2>/dev/null || { fail record "cannot create the record file (it exists or is not writable)"; return 1; }
  {
    echo "# Pre-flip scan and live-repo inventory"
    echo
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Scanned tip: $tip"
    echo "Gitleaks: $(gitleaks version)"
    echo "Result: PASS"
    echo
    echo "| Check | Result | Detail |"
    echo "|---|---|---|"
    awk -F'|' '{ printf "| %s | %s | %s |\n", $1, $2, $3 }' "$W/rows"
    echo
    echo "| Category | Expected | Observed |"
    echo "|---|---|---|"
    if [ "$SKIP_INV" -eq 1 ]; then echo "| (all) | skipped | skipped |"
    else awk -F'|' '{ printf "| %s | %s | %s |\n", $1, $2, $3 }' "$W/inv"; fi
  } >> "$RECORD"
}

if [ -n "$RECORD" ]; then
  if [ "$FAILS" -eq 0 ]; then
    if write_record; then echo "RECORD written"; fi
  else
    echo "no record written: a check failed"
  fi
fi

finish
