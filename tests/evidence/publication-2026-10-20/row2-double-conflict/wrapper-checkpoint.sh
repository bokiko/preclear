#!/bin/bash
# TEST APPARATUS ONLY. Logs every call and delegates unchanged to the real helper. While `armed`
# holds a positive count, each `update` call to the FIRST section the caller touched is preceded
# by a real update to that same section by a second harness-bound fixture session, so the real
# helper returns a genuine exit 3 to the caller. Count 2 = conflict on the first attempt and again
# on the retry. Nothing about the caller's arguments, hashes or output is altered.
REAL=<helper>
W="$(cd "$(dirname "$0")" && pwd)"
printf '%s CALL' "$(date -u +%FT%TZ)" >> "$W/calls.log"; printf ' %q' "$@" >> "$W/calls.log"; echo >> "$W/calls.log"
if [ -f "$W/armed" ] && [ "$1" = "update" ]; then
  n=$(cat "$W/armed"); sec=""; prev=""
  for a in "$@"; do if [ "$prev" = "--section" ]; then sec="$a"; fi; prev="$a"; done
  if [ ! -f "$W/target-section" ]; then printf '%s' "$sec" > "$W/target-section"; fi
  if [ "$n" -gt 0 ] && [ "$sec" = "$(cat "$W/target-section")" ]; then
    echo $((n-1)) > "$W/armed"; k=$((3-n))
    SID2=$(cat "$W/writer2.session")
    {
      echo "=== $(date -u +%FT%TZ) injection $k to section [$sec] as writer2 $SID2"
      h=$("$REAL" show --section "$sec" --session "$SID2" | sed -n 's/^section-hash: //p')
      "$REAL" show --section "$sec" --session "$SID2" | awk 'f{print} /^section-hash: /{f=1}' > "$W/writer2-body-$k.md"
      printf '\n- Concurrent fact %s (second writer, 2026-10-20): %s\n' "$k" "$( [ $k = 1 ] && echo 'CI runner for this project was renamed to ci-02; nothing else changed.' || echo 'the staging database moved to db-stg-03; nothing else changed.')" >> "$W/writer2-body-$k.md"
      "$REAL" update --section "$sec" --expect-section "$h" --from "$W/writer2-body-$k.md" --session "$SID2"; echo "writer2 update exit $?"
    } >> "$W/injection.log" 2>&1
  fi
fi
"$REAL" "$@"; rc=$?
echo "$(date -u +%FT%TZ) EXIT $rc" >> "$W/calls.log"
exit $rc
