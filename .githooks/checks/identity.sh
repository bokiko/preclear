#!/bin/sh
# Identity check: every commit in each pushed range must carry the pinned identity as both
# author and committer, and an annotated tag must carry it as tagger. The pin is the
# repo-local git config key preclear.pinnedIdentity ("name <address>"). When the key is
# unset (a stranger's clone) the check skips with a visible message; the leak check still runs.
# The same pass refuses any commit message matching ../attribution.ere (AI attribution trailers).
ranges=$1
pinned=$(git config --local --get preclear.pinnedIdentity 2>/dev/null)
if [ -z "$pinned" ]; then echo "identity check skipped: preclear.pinnedIdentity is not set in this clone" >&2; exit 0; fi
pattern_file="$(dirname "$0")/../attribution.ere"
[ -r "$pattern_file" ] || { echo "attribution check FAILED: pattern file $pattern_file is missing or unreadable" >&2; exit 1; }
tab=$(printf '\t'); rc=0
while IFS=$tab read -r ref rev; do
  # shellcheck disable=SC2086
  ids=$(git log --format='%an <%ae>%n%cn <%ce>' $rev) \
    || { echo "identity check FAILED for $ref (git log failed for range)" >&2; rc=1; continue; }
  bad=$(printf '%s\n' "$ids" | sort -u | grep -v -x -F "$pinned")
  case $ref in refs/tags/*)
    # A lightweight tag has no tagger; only compare when a tagger name exists.
    tname=$(git for-each-ref --format='%(taggername)' "$ref")
    if [ -n "$tname" ]; then
      t="$tname $(git for-each-ref --format='%(taggeremail)' "$ref")"
      [ "$t" = "$pinned" ] || bad="$bad
$t"
    fi ;;
  esac
  [ -z "$bad" ] || { echo "identity check FAILED for $ref (pinned identity differs):" >&2; echo "$bad" >&2; rc=1; }
  # Attribution: no commit message in the range may match a forbidden trailer pattern (PUB-04).
  # shellcheck disable=SC2086
  msgs=$(git log --format='%H %s%n%B' $rev) \
    || { echo "attribution check FAILED for $ref (git log failed for range)" >&2; rc=1; continue; }
  attr=$(printf '%s\n' "$msgs" | grep -i -E -f "$pattern_file")
  [ -z "$attr" ] || { echo "attribution check FAILED for $ref:" >&2; echo "$attr" >&2; rc=1; }
done < "$ranges"
exit $rc
