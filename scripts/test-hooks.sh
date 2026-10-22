#!/bin/sh
# Throwaway-clone tests for the pre-push gate. Run: sh scripts/test-hooks.sh
# Throwaway clones only: this script never pushes to the real origin, and it stores no fake
# secret as a literal (the seed is assembled from fragments at run time). It prints one
# "PASS <name>" or "FAIL <name>: <reason>" line per check and exits 1 when any FAIL was printed.
# Every history-changing step in a scratch repository goes through the scratch guard below
# (scratch_ok, assert_scratch, scratch_commit), which proves the target is an isolated
# throwaway repository before it acts (T-01-26). The throwaway directory is never deleted.

# The machine's global identity and hook settings must not influence any result.
GIT_CONFIG_GLOBAL=/dev/null
GIT_CONFIG_NOSYSTEM=1
GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM GIT_TERMINAL_PROMPT
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
unset GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL

SELF_DIR=$(cd "$(dirname "$0")" && pwd) || exit 1
REPO=$(cd "$SELF_DIR/.." && pwd) || exit 1
REPO_TOP=$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_TOP" ]; then echo "FAIL setup: cannot resolve the repository toplevel" >&2; exit 1; fi
ORIGIN_DIGEST_START=$(git -C "$REPO" for-each-ref refs/remotes/origin | cksum)
ALLREFS_DIGEST_START=$({ git -C "$REPO" rev-parse HEAD; git -C "$REPO" for-each-ref; } | cksum)

T=$(mktemp -d "${TMPDIR:-/tmp}/preclear-hooktest.XXXXXX")
if [ -z "$T" ] || [ ! -d "$T" ]; then echo "FAIL setup: no throwaway directory" >&2; exit 1; fi
# mktemp may return a path through a symlink; git reports the physical path (FA-7).
TP=$(cd "$T" && pwd -P)
if [ -z "$TP" ] || [ ! -d "$TP" ]; then echo "FAIL setup: cannot resolve the throwaway directory" >&2; exit 1; fi
W="$TP/work"
R="$TP/remote.git"

FAILS=0
pass() { echo "PASS $1"; }
fail() { echo "FAIL $1: $2"; FAILS=$((FAILS + 1)); }

# Scratch guard (T-01-26). scratch_ok DIR: silent, returns 0 only when DIR's repository
# toplevel is non-empty, strictly under TP, and not the real repository's toplevel.
scratch_ok() {
  scratch_top=$(git -C "$1" rev-parse --show-toplevel 2>/dev/null) || return 1
  [ -n "$scratch_top" ] || return 1
  case $scratch_top in "$TP"/*) ;; *) return 1 ;; esac
  [ "$scratch_top" != "$REPO_TOP" ] || return 1
  return 0
}
# A plain exit would end only a command-substitution subshell, so the guard signals the
# script's own process id (it stays the script's id inside subshells).
assert_scratch() {
  if scratch_ok "$1"; then return 0; fi
  echo "FAIL scratch-guard: $1 is not an isolated throwaway repository" >&2
  kill -TERM "$$"
  exit 1
}
# scratch_commit DIR MESSAGE [skip]: the only place this script records history.
scratch_commit() {
  assert_scratch "$1"
  if [ "${3:-}" = skip ]; then
    git -C "$1" commit -q -n -m "$2"
  else
    git -C "$1" commit -q -m "$2"
  fi
}
# Push guard (T-01-08): the work repository's origin must sit inside the throwaway directory.
push_work() {
  origin_url=$(git -C "$W" remote get-url origin 2>/dev/null)
  case $origin_url in
    "$TP"/*) ;;
    *) echo "FAIL push-guard: origin is not inside the throwaway directory" >&2; kill -TERM "$$"; exit 1 ;;
  esac
  git -C "$W" push "$@"
}
absent_on_remote() { ! git -C "$R" cat-file -e "${1}^{commit}" 2>/dev/null; }
back_one() { assert_scratch "$W"; git -C "$W" reset -q --hard HEAD~1; }

# ---- setup: bare remote, work repo pinned to a fake owner identity, hooks copied in ----
git init -q --bare "$R" || exit 1
git init -q -b main "$W" || exit 1
git -C "$W" config user.name "Hook Owner"
git -C "$W" config user.email hook-owner@example.com
git -C "$W" config user.useConfigOnly true
git -C "$W" config preclear.pinnedIdentity "Hook Owner <hook-owner@example.com>"
cp -Rp "$REPO/.githooks" "$W/.githooks" || exit 1
cp -p "$REPO/.gitleaks.toml" "$W/.gitleaks.toml" || exit 1
git -C "$W" add -A
scratch_commit "$W" "Add the hook set under test"
git -C "$W" config core.hooksPath .githooks
git -C "$W" remote add origin "$R"

# ---- tracer cases ----
case_clean_push() {
  out=$(push_work origin main 2>&1); rc=$?
  want=$(git -C "$W" rev-parse HEAD)
  got=$(git -C "$R" rev-parse refs/heads/main 2>/dev/null)
  if [ "$rc" -eq 0 ] && [ "$got" = "$want" ]; then pass clean-push
  else fail clean-push "exit $rc, remote main '$got' differs from work '$want'"; printf '%s\n' "$out" | tail -n 6
  fi
}

case_identity_wrong_author_committer() {
  printf 'foreign\n' > "$W/foreign.txt"
  git -C "$W" add foreign.txt
  (
    GIT_AUTHOR_NAME=Intruder; GIT_AUTHOR_EMAIL=intruder@example.org
    GIT_COMMITTER_NAME=Intruder; GIT_COMMITTER_EMAIL=intruder@example.org
    export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
    scratch_commit "$W" "Add a file under a foreign identity"
  )
  bad_sha=$(git -C "$W" rev-parse HEAD)
  out=$(push_work origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'identity check FAILED' && absent_on_remote "$bad_sha"
  then pass identity-wrong-author-committer
  else fail identity-wrong-author-committer "exit $rc, expected a refusal naming the identity check with the commit absent"; printf '%s\n' "$out" | tail -n 6
  fi
  back_one
}

# The seed is assembled at run time from three fragments; no source line holds the whole key.
SEED_SHA=
case_leak_seed_prepush() {
  seed_a=AK; seed_b=IA; seed_c=QYLPMN5HHHFPZAM7
  printf 'aws_key = %s%s%s\n' "$seed_a" "$seed_b" "$seed_c" > "$W/seed.txt"
  git -C "$W" add seed.txt
  scratch_commit "$W" "Add a seed file" skip
  SEED_SHA=$(git -C "$W" rev-parse HEAD)
  out=$(push_work origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'aws-access-token' && printf '%s\n' "$out" | grep -q 'leak check FAILED'
  then pass leak-seed-prepush
  else fail leak-seed-prepush "exit $rc, expected a refusal naming rule aws-access-token"; printf '%s\n' "$out" | tail -n 6
  fi
}

case_leak_seed_absent_on_remote() {
  if [ -n "$SEED_SHA" ] && absent_on_remote "$SEED_SHA"; then pass leak-seed-absent-on-remote
  else fail leak-seed-absent-on-remote "the seed commit '$SEED_SHA' is on the throwaway remote or was never made"
  fi
  back_one
}

case_clean_push
case_identity_wrong_author_committer
case_leak_seed_prepush
case_leak_seed_absent_on_remote

# Last tracer case: nothing in the real repository moved, and the guard is not vacuous.
case_real_origin_refs_unchanged() {
  origin_end=$(git -C "$REPO" for-each-ref refs/remotes/origin | cksum)
  allrefs_end=$({ git -C "$REPO" rev-parse HEAD; git -C "$REPO" for-each-ref; } | cksum)
  why=
  [ "$origin_end" = "$ORIGIN_DIGEST_START" ] || why="$why origin refs changed;"
  [ "$allrefs_end" = "$ALLREFS_DIGEST_START" ] || why="$why real HEAD or refs changed;"
  scratch_ok "$W" || why="$why guard rejected the throwaway repository;"
  if scratch_ok "$REPO"; then why="$why guard accepted the real repository;"; fi
  if [ -z "$why" ]; then pass real-origin-refs-unchanged; else fail real-origin-refs-unchanged "$why"; fi
}
case_real_origin_refs_unchanged

echo "throwaway directory (kept): $T"
[ "$FAILS" -eq 0 ]
