#!/bin/bash
# TEST APPARATUS ONLY. Logs every call and delegates unchanged to the stub, except that it
# refuses the three driver-only verbs bind, create and init (exit 71, nothing delegated). While
# the file `armed` beside this wrapper holds a positive count, each `update` call to the FIRST
# section the caller touched is preceded by a real update to that same section by a second bound
# session, so the stub itself returns a genuine exit 3 to the caller. Count 2 = conflict on the
# first attempt and again on the retry. Nothing about the caller's arguments, hashes, input
# files or output is altered; injection output goes to injection.log, never to the caller.
#
# Files beside this wrapper (W):
#   py                interpreter path (written by the run-root materialiser or a test)
#   stub              path of checkpoint_stub.py
#   calls.log         one `<UTC second> CALL <argv, printf %q>` and one `<UTC second> EXIT <n>` per call
#   injection.log     header, the writer's stub output and `writer2 update exit <n>` per injection
#   armed             remaining injections (positive integer)
#   target-section    the first section an armed update touched
#   writer2.session   session id of the second writer
# Exit codes: the stub's own (0 to 6, 64), 70 when py or stub is missing or empty, 71 when the
# verb is bind, create or init. bash 3.2 only.

W="$(cd "$(dirname "$0")" && pwd)"

PY=""
STUB=""
[ -f "$W/py" ] && PY=$(cat "$W/py")
[ -f "$W/stub" ] && STUB=$(cat "$W/stub")
if [ -z "${PY// /}" ] || [ -z "${STUB// /}" ]; then
  echo "checkpoint-wrapper: not configured" >&2
  exit 70
fi

real() {
  "$PY" -I -B "$STUB" "$@"
}

stamp() {
  date -u +%FT%TZ
}

# The verb is the first argument that is not a leading --session option; those are the only
# global options the stub's parser takes before the verb.
first_verb() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --session)
        shift
        [ "$#" -gt 0 ] && shift
        ;;
      --session=*)
        shift
        ;;
      *)
        printf '%s' "$1"
        return 0
        ;;
    esac
  done
  return 0
}

VERB=$(first_verb "$@")

printf '%s CALL' "$(stamp)" >> "$W/calls.log"
[ "$#" -gt 0 ] && printf ' %q' "$@" >> "$W/calls.log"
echo >> "$W/calls.log"

# Driver-only verbs: the driver builds state through the stub directly, never through this
# wrapper. Baseline allow rules (env, python3 -c, awk, find) could still launch the wrapper
# with one of these, so it refuses them whatever started it.
case "$VERB" in
  bind | create | init)
    echo "checkpoint-wrapper: driver-only verb, not available through the wrapper" >&2
    printf '%s EXIT 71\n' "$(stamp)" >> "$W/calls.log"
    exit 71
    ;;
esac

if [ -f "$W/armed" ] && [ "$VERB" = "update" ]; then
  n=$(cat "$W/armed")
  case "$n" in
    '' | *[!0-9]*) n=0 ;;
  esac
  sec=""
  prev=""
  for a in "$@"; do
    if [ "$prev" = "--section" ]; then
      sec="$a"
    fi
    case "$a" in
      --section=*) sec="${a#--section=}" ;;
    esac
    prev="$a"
  done
  if [ ! -f "$W/target-section" ]; then
    printf '%s' "$sec" > "$W/target-section"
  fi
  if [ "$n" -gt 0 ] && [ "$sec" = "$(cat "$W/target-section")" ]; then
    echo $((n - 1)) > "$W/armed"
    k=$((3 - n))
    SID2=$(cat "$W/writer2.session")
    {
      echo "=== $(stamp) injection $k to section [$sec] as writer2 $SID2"
      shown=$(real show --section "$sec" --session "$SID2")
      h=$(printf '%s\n' "$shown" | sed -n 's/^section-hash: //p')
      body=$(printf '%s\n' "$shown" | awk 'f{print} /^section-hash: /{f=1}')
      if [ "$k" = 1 ]; then
        fact="CI runner for this project was renamed to ci-02; nothing else changed."
      else
        fact="the staging database moved to db-stg-03; nothing else changed."
      fi
      printf '%s\n\n- Concurrent fact %s (second writer, 2026-10-20): %s\n' "$body" "$k" "$fact" > "$W/writer2-body-$k.md"
      real update --section "$sec" --expect-section "$h" --from "$W/writer2-body-$k.md" --session "$SID2"
      echo "writer2 update exit $?"
    } >> "$W/injection.log" 2>&1
  fi
fi

real "$@"
rc=$?
printf '%s EXIT %s\n' "$(stamp)" "$rc" >> "$W/calls.log"
exit $rc
