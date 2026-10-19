#!/bin/bash
# TEST APPARATUS ONLY. Delegates every call to the real helper unchanged. While the
# "armed" flag exists, the first `update` call first lets a second, harness-bound
# fixture session perform a real update to the same section, so the real helper
# returns a genuine exit 3 to the caller. Nothing about the caller's arguments,
# hashes or output is altered.
REAL=<helper>
W="$(cd "$(dirname "$0")" && pwd)"
LOG="$W/injection.log"
if [ -f "$W/armed" ] && [ "$1" = "update" ]; then
  sec=""; prev=""
  for a in "$@"; do if [ "$prev" = "--section" ]; then sec="$a"; fi; prev="$a"; done
  SID2=$(cat "$W/writer2.session")
  mv "$W/armed" "$W/fired"
  {
    echo "=== $(date -u +%FT%TZ) injecting concurrent update to section [$sec] as writer2 $SID2"
    h=$("$REAL" show --section "$sec" --session "$SID2" | sed -n 's/^section-hash: //p')
    "$REAL" show --section "$sec" --session "$SID2" | awk 'f{print} /^section-hash: /{f=1}' > "$W/writer2-body.md"
    printf '\n- Concurrent fact (second writer, 2026-10-19): CI runner for this project was renamed to ci-02; nothing else changed.\n' >> "$W/writer2-body.md"
    "$REAL" update --section "$sec" --expect-section "$h" --from "$W/writer2-body.md" --session "$SID2"; echo "writer2 update exit $?"
  } >> "$LOG" 2>&1
fi
exec "$REAL" "$@"
