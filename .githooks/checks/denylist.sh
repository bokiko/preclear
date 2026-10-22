#!/bin/sh
# Deny-list check: refuse added lines that contain a local deny-list entry. Entries are
# built at run time from this machine's host names plus the non-comment lines of
# .git/info/preclear-deny.txt (inside .git, so never committed; the owner may put a real
# name there). Entries shorter than four characters are dropped. Output is counts and
# file names only: an entry or a matched line is never printed.
# Usage: denylist.sh --staged         check the staged diff (pre-commit)
#        denylist.sh RANGES_FILE      check each "ref<TAB>range" line (pre-push fan-out)
mode=$1
cd "$(git rev-parse --show-toplevel)" || exit 1
raw=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
list=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
diffout=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
trap 'rm -f "$raw" "$list" "$diffout"' EXIT
{
  hostname
  hostname -s
  scutil --get LocalHostName
  scutil --get ComputerName
} >> "$raw" 2>/dev/null
extra=$(git rev-parse --git-path info/preclear-deny.txt 2>/dev/null)
if [ -n "$extra" ] && [ -r "$extra" ]; then
  grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$extra" >> "$raw"
fi
awk '{ sub(/\r$/, ""); if (length($0) >= 4) print }' "$raw" | sort -u > "$list"
if [ ! -s "$list" ]; then echo "denylist check skipped: no entries" >&2; exit 0; fi

# count_hits: read a unified diff on stdin, print "<file><TAB><n>" for every file with n
# added lines that contain an entry (case-insensitive, fixed string). Hunk bodies are told
# apart from file headers by the diff --git line and the first hunk marker.
count_hits() {
  awk -v listfile="$list" '
    BEGIN { while ((getline e < listfile) > 0) entries[tolower(e)] = 1 }
    /^diff --git / { inhdr = 1; next }
    /^@@/ { inhdr = 0; next }
    inhdr && /^\+\+\+ / { f = substr($0, 5); sub(/^b\//, "", f); next }
    !inhdr && /^\+/ {
      line = tolower(substr($0, 2))
      for (e in entries) if (index(line, e) > 0) { hits[f]++; break }
    }
    END { for (k in hits) printf "%s\t%d\n", k, hits[k] }
  '
}

rc=0
tab=$(printf '\t')
case $mode in
  --staged)
    git diff --cached -U0 --no-color --no-ext-diff --no-textconv > "$diffout" \
      || { echo "denylist check FAILED: could not read the staged diff" >&2; exit 1; }
    hits=$(count_hits < "$diffout")
    if [ -n "$hits" ]; then
      printf '%s\n' "$hits" | while IFS=$tab read -r file n; do
        echo "denylist check FAILED: $file ($n added line(s) match a local deny-list entry)" >&2
      done
      rc=1
    fi
    ;;
  *)
    [ -r "$mode" ] || { echo "denylist check FAILED: ranges file not readable" >&2; exit 1; }
    while IFS=$tab read -r ref rev; do
      # shellcheck disable=SC2086
      git log -p -U0 --format= --no-color --no-ext-diff --no-textconv $rev > "$diffout" \
        || { echo "denylist check FAILED for $ref: could not read the range" >&2; rc=1; continue; }
      n=$(count_hits < "$diffout" | awk -F"$tab" '{ s += $2 } END { print s + 0 }')
      if [ "$n" -gt 0 ]; then
        echo "denylist check FAILED for $ref: $n added line(s) match a local deny-list entry" >&2
        rc=1
      fi
    done < "$mode"
    ;;
esac
exit $rc
