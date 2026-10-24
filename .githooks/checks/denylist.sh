#!/bin/sh
# Deny-list check: refuse added lines, file names and (push and history modes) commit messages
# that contain a local deny-list entry. Entries are
# built at run time from this machine's host names plus the non-comment lines of
# .git/info/preclear-deny.txt (inside .git, so never committed; the owner may put a real
# name there). Host names shorter than six characters, and generic host names such as
# localhost or a bare distribution name, are dropped: a short common word would block
# ordinary text and push people towards --no-verify. Local-file entries keep a four-character
# floor. Output is counts and file names only: an entry or a matched line is never printed,
# and a file name that itself holds an entry is shown as "(file name)".
# Usage: denylist.sh --staged         check the staged diff (pre-commit)
#        denylist.sh RANGES_FILE      check each "ref<TAB>range" line (pre-push fan-out)
#        denylist.sh --history GITDIR check every added line, file name and message in all refs
#                                     of GITDIR (pre-flip scan;
#                                     the entries still come from the repository you run it in)
mode=$1
histdir=
if [ "$mode" = --history ]; then
  if [ -n "$2" ] && [ -d "$2" ]; then histdir=$(cd "$2" && pwd -P); fi
  [ -n "$histdir" ] || { echo "denylist check FAILED (history): git directory not readable" >&2; exit 1; }
fi
cd "$(git rev-parse --show-toplevel)" || exit 1
raw=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
extraraw=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
list=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
diffout=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
hitsout=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
cand=$(mktemp "${TMPDIR:-/tmp}/preclear-deny.XXXXXX") || exit 1
trap 'rm -f "$raw" "$extraraw" "$list" "$diffout" "$hitsout" "$cand"' EXIT
{
  hostname
  hostname -s
  scutil --get LocalHostName
  scutil --get ComputerName
} >> "$raw" 2>/dev/null
extra=$(git rev-parse --git-path info/preclear-deny.txt 2>/dev/null)
if [ -n "$extra" ] && [ -r "$extra" ]; then
  grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$extra" >> "$extraraw"
  # grep status 1 only means "no entry lines"; above 1 is a read error and must not pass.
  [ $? -le 1 ] || { echo "denylist check FAILED: could not read the local deny list" >&2; exit 1; }
fi
# Every step that builds the list is checked: a failed awk or sort would leave an empty list
# and the "no entries" skip below would then approve everything.
# Host names: at least six characters and not a generic name. Local-file entries: at least four.
awk 'BEGIN {
       n = split("localhost localdomain ubuntu debian fedora centos alpine docker container runner builder server laptop desktop machine default workstation macbook macbook-pro macbook-air mac-mini mac-studio mac-pro", g, " ")
       for (i = 1; i <= n; i++) generic[g[i]] = 1
     }
     { sub(/\r$/, ""); if (length($0) >= 6 && !(tolower($0) in generic)) print }' "$raw" > "$cand" \
  && awk '{ sub(/\r$/, ""); if (length($0) >= 4) print }' "$extraraw" >> "$cand" \
  && sort -u "$cand" > "$list" \
  || { echo "denylist check FAILED: could not build the entry list" >&2; exit 1; }
if [ ! -s "$list" ]; then echo "denylist check skipped: no entries" >&2; exit 0; fi

# count_hits: read a unified diff on stdin, print "<file><TAB><n>" for every file with n
# added lines that contain an entry (case-insensitive, fixed string). Hunk bodies are told
# apart from file headers by the diff --git line and the first hunk marker. A path that holds
# an entry is printed as "(file name)" so the entry itself never reaches the output.
count_hits() {
  awk -v listfile="$list" '
    BEGIN { while ((getline e < listfile) > 0) entries[tolower(e)] = 1 }
    function lab(p,   e, lp) {
      lp = tolower(p)
      for (e in entries) if (index(lp, e) > 0) return "(file name)"
      return p
    }
    /^diff --git / { inhdr = 1; next }
    /^@@/ { inhdr = 0; next }
    inhdr && /^\+\+\+ / { f = substr($0, 5); sub(/^b\//, "", f); next }
    !inhdr && /^\+/ {
      line = tolower(substr($0, 2))
      for (e in entries) if (index(line, e) > 0) { hits[f]++; break }
    }
    END { for (k in hits) { l = lab(k); agg[l] += hits[k] } for (l in agg) printf "%s\t%d\n", l, agg[l] }
  '
}

# count_plain LABEL: read lines on stdin (file names or message text), print "<LABEL><TAB><n>"
# when n lines contain an entry. Same matching as count_hits.
count_plain() {
  awk -v listfile="$list" -v label="$1" '
    BEGIN { while ((getline e < listfile) > 0) entries[tolower(e)] = 1 }
    { line = tolower($0); for (e in entries) if (index(line, e) > 0) { n++; break } }
    END { if (n > 0) printf "%s\t%d\n", label, n }
  '
}

rc=0
tab=$(printf '\t')
# scan_diff: scan $diffout into $hitsout. A scanner that dies (out of memory, a locale error)
# leaves no output, which must not read as "no hits": the status is checked and a failure
# stops the check with a refusal.
scan_diff() {
  count_hits < "$diffout" > "$hitsout" || { echo "denylist check FAILED: scan error" >&2; exit 1; }
}
# scan_plain LABEL: scan the lines in $cand and append any hit to $hitsout (status checked).
scan_plain() {
  count_plain "$1" < "$cand" >> "$hitsout" || { echo "denylist check FAILED: scan error" >&2; exit 1; }
}
# sum_hits: total the counts in $hitsout into n, again refusing on a tool error.
sum_hits() {
  n=$(awk -F"$tab" '{ s += $2 } END { print s + 0 }' "$hitsout") \
    || { echo "denylist check FAILED: scan error" >&2; exit 1; }
  case $n in ''|*[!0-9]*) echo "denylist check FAILED: scan error" >&2; exit 1 ;; esac
}
case $mode in
  --staged)
    git diff --cached -U0 --no-color --no-ext-diff --no-textconv > "$diffout" \
      || { echo "denylist check FAILED: could not read the staged diff" >&2; exit 1; }
    scan_diff
    git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR --no-renames --no-ext-diff > "$cand" \
      || { echo "denylist check FAILED: could not read the staged file names" >&2; exit 1; }
    scan_plain "(file name)"
    if [ -s "$hitsout" ]; then
      while IFS=$tab read -r file n; do
        echo "denylist check FAILED: $file ($n match(es) against a local deny-list entry)" >&2
      done < "$hitsout"
      rc=1
    fi
    ;;
  --history)
    git --git-dir="$histdir" log -p -U0 --format= --all --no-color --no-ext-diff --no-textconv > "$diffout" \
      || { echo "denylist check FAILED (history): could not read the history" >&2; exit 1; }
    scan_diff
    git --git-dir="$histdir" -c core.quotePath=false log --all --name-only --format= --diff-filter=ACMR --no-renames --no-ext-diff > "$cand" \
      || { echo "denylist check FAILED (history): could not read the file names" >&2; exit 1; }
    scan_plain "(file name)"
    git --git-dir="$histdir" log --all --format=%B > "$cand" \
      || { echo "denylist check FAILED (history): could not read the messages" >&2; exit 1; }
    scan_plain "(commit message)"
    sum_hits
    if [ "$n" -gt 0 ]; then
      echo "denylist check FAILED (history): $n added line(s), file name(s) or message line(s) match a local deny-list entry" >&2
      rc=1
    fi
    ;;
  *)
    [ -r "$mode" ] || { echo "denylist check FAILED: ranges file not readable" >&2; exit 1; }
    while IFS=$tab read -r ref rev; do
      # shellcheck disable=SC2086
      git log -p -U0 --format= --no-color --no-ext-diff --no-textconv $rev > "$diffout" \
        || { echo "denylist check FAILED for $ref: could not read the range" >&2; rc=1; continue; }
      scan_diff
      # shellcheck disable=SC2086
      git -c core.quotePath=false log --name-only --format= --diff-filter=ACMR --no-renames --no-ext-diff $rev > "$cand" \
        || { echo "denylist check FAILED for $ref: could not read the file names" >&2; rc=1; continue; }
      scan_plain "(file name)"
      # shellcheck disable=SC2086
      git log --format=%B $rev > "$cand" \
        || { echo "denylist check FAILED for $ref: could not read the messages" >&2; rc=1; continue; }
      scan_plain "(commit message)"
      sum_hits
      if [ "$n" -gt 0 ]; then
        echo "denylist check FAILED for $ref: $n added line(s), file name(s) or message line(s) match a local deny-list entry" >&2
        rc=1
      fi
    done < "$mode"
    ;;
esac
exit $rc
