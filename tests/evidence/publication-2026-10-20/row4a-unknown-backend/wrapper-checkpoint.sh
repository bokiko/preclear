#!/bin/bash
# TEST APPARATUS ONLY. Logs every call (argv + exit code) to calls.log, delegates unchanged to the real helper.
REAL=<helper>
W="$(cd "$(dirname "$0")" && pwd)"
printf '%s CALL' "$(date -u +%FT%TZ)" >> "$W/calls.log"; printf ' %q' "$@" >> "$W/calls.log"; echo >> "$W/calls.log"
"$REAL" "$@"; rc=$?
echo "$(date -u +%FT%TZ) EXIT $rc" >> "$W/calls.log"
exit $rc
