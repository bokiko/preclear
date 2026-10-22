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
W2="$TP/work2"
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
# Push guard (T-01-08): the pushing repository's origin must sit inside the throwaway directory.
push_in() {
  push_dir=$1; shift
  assert_scratch "$push_dir"
  origin_url=$(git -C "$push_dir" remote get-url origin 2>/dev/null)
  case $origin_url in
    "$TP"/*) ;;
    *) echo "FAIL push-guard: origin is not inside the throwaway directory" >&2; kill -TERM "$$"; exit 1 ;;
  esac
  git -C "$push_dir" push "$@"
}
absent_on_remote() { ! git -C "$R" cat-file -e "${1}^{commit}" 2>/dev/null; }
back_one() { assert_scratch "$1"; git -C "$1" reset -q --hard HEAD~1; }
# The seed is assembled at run time from three fragments; no source line holds the whole key.
write_seed() {
  seed_a=AK; seed_b=IA; seed_c=QYLPMN5HHHFPZAM7
  printf 'aws_key = %s%s%s\n' "$seed_a" "$seed_b" "$seed_c" > "$1"
}

# ---- setup: bare remote, work repo pinned to a fake owner identity, hooks copied in ----
git init -q --bare -b main "$R" || exit 1
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
  out=$(push_in "$W" origin main 2>&1); rc=$?
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
  out=$(push_in "$W" origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'identity check FAILED' && absent_on_remote "$bad_sha"
  then pass identity-wrong-author-committer
  else fail identity-wrong-author-committer "exit $rc, expected a refusal naming the identity check with the commit absent"; printf '%s\n' "$out" | tail -n 6
  fi
  back_one "$W"
}

SEED_SHA=
case_leak_seed_prepush() {
  write_seed "$W/seed.txt"
  git -C "$W" add seed.txt
  scratch_commit "$W" "Add a seed file" skip
  SEED_SHA=$(git -C "$W" rev-parse HEAD)
  out=$(push_in "$W" origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'aws-access-token' && printf '%s\n' "$out" | grep -q 'leak check FAILED'
  then pass leak-seed-prepush
  else fail leak-seed-prepush "exit $rc, expected a refusal naming rule aws-access-token"; printf '%s\n' "$out" | tail -n 6
  fi
}

case_leak_seed_absent_on_remote() {
  if [ -n "$SEED_SHA" ] && absent_on_remote "$SEED_SHA"; then pass leak-seed-absent-on-remote
  else fail leak-seed-absent-on-remote "the seed commit '$SEED_SHA' is on the throwaway remote or was never made"
  fi
  back_one "$W"
}

# ---- attribution and identity cases ----
case_identity_committer_only() {
  printf 'committer only\n' > "$W/committer-only.txt"
  git -C "$W" add committer-only.txt
  (
    GIT_COMMITTER_NAME=Intruder; GIT_COMMITTER_EMAIL=intruder@example.org
    export GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
    scratch_commit "$W" "Add a file with a foreign committer"
  )
  bad_sha=$(git -C "$W" rev-parse HEAD)
  out=$(push_in "$W" origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'identity check FAILED' && absent_on_remote "$bad_sha"
  then pass identity-committer-only
  else fail identity-committer-only "exit $rc, expected a refusal naming the identity check with the commit absent"; printf '%s\n' "$out" | tail -n 6
  fi
  back_one "$W"
}

case_identity_wrong_tagger() {
  assert_scratch "$W"
  (
    GIT_COMMITTER_NAME=Intruder; GIT_COMMITTER_EMAIL=intruder@example.org
    export GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
    git -C "$W" tag -a tag-foreign -m "Tag under a foreign identity"
  )
  git -C "$W" tag -a tag-owner -m "Tag under the pinned identity"
  git -C "$W" tag tag-light
  out_bad=$(push_in "$W" origin refs/tags/tag-foreign 2>&1); rc_bad=$?
  out_owner=$(push_in "$W" origin refs/tags/tag-owner 2>&1); rc_owner=$?
  out_light=$(push_in "$W" origin refs/tags/tag-light 2>&1); rc_light=$?
  why=
  if [ "$rc_bad" -eq 0 ] || ! printf '%s\n' "$out_bad" | grep -q 'identity check FAILED'; then why="$why foreign tagger not refused (exit $rc_bad);"; fi
  if [ "$rc_owner" -ne 0 ]; then why="$why annotated tag under the pin refused (exit $rc_owner);"; fi
  if [ "$rc_light" -ne 0 ]; then why="$why lightweight tag refused (exit $rc_light);"; fi
  if [ -z "$why" ]; then pass identity-wrong-tagger
  else fail identity-wrong-tagger "$why"; printf '%s\n%s\n%s\n' "$out_bad" "$out_owner" "$out_light" | tail -n 12
  fi
}

# The trailer key is built at run time so this file never holds a complete trailer line.
TRAILER_KEY=Co-Authored
TRAILER_KEY="${TRAILER_KEY}-By"
trailer_message() { printf 'Add a note under test\n\n%s: A Helper <helper@example.org>\n' "$TRAILER_KEY"; }

case_trailer_commit_msg() {
  printf 'note\n' > "$W/note.txt"
  git -C "$W" add note.txt
  before=$(git -C "$W" rev-list --count HEAD)
  msg=$(trailer_message)
  out=$(scratch_commit "$W" "$msg" 2>&1); rc=$?
  after=$(git -C "$W" rev-list --count HEAD)
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'commit-msg FAILED' && [ "$before" = "$after" ]
  then pass trailer-commit-msg
  else fail trailer-commit-msg "exit $rc, history count $before -> $after, expected a refusal naming commit-msg"; printf '%s\n' "$out" | tail -n 6
  fi
}

case_trailer_bypassed_prepush() {
  msg=$(trailer_message)
  scratch_commit "$W" "$msg" skip
  bad_sha=$(git -C "$W" rev-parse HEAD)
  out=$(push_in "$W" origin main 2>&1); rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'attribution check FAILED' && absent_on_remote "$bad_sha"
  then pass trailer-bypassed-prepush
  else fail trailer-bypassed-prepush "exit $rc, expected a refusal naming the attribution check with the commit absent"; printf '%s\n' "$out" | tail -n 6
  fi
  back_one "$W"
}

case_unpinned_skips_identity() {
  git clone -q "$R" "$W2" || { fail unpinned-skips-identity "clone of the throwaway remote failed"; return; }
  git -C "$W2" config user.name Intruder
  git -C "$W2" config user.email intruder@example.org
  git -C "$W2" config core.hooksPath .githooks
  printf 'unpinned\n' > "$W2/unpinned.txt"
  git -C "$W2" add unpinned.txt
  scratch_commit "$W2" "Add a file from an unpinned clone"
  out_ok=$(push_in "$W2" origin HEAD:refs/heads/unpinned 2>&1); rc_ok=$?
  write_seed "$W2/seed.txt"
  git -C "$W2" add seed.txt
  scratch_commit "$W2" "Add a seed file from an unpinned clone" skip
  out_leak=$(push_in "$W2" origin HEAD:refs/heads/unpinned 2>&1); rc_leak=$?
  why=
  if [ "$rc_ok" -ne 0 ]; then why="$why unpinned push refused (exit $rc_ok);"; fi
  if ! printf '%s\n' "$out_ok" | grep -q 'identity check skipped'; then why="$why no visible skip message;"; fi
  if [ "$rc_leak" -eq 0 ] || ! printf '%s\n' "$out_leak" | grep -q 'leak check FAILED'; then why="$why leak check not enforced (exit $rc_leak);"; fi
  if [ -z "$why" ]; then pass unpinned-skips-identity
  else fail unpinned-skips-identity "$why"; printf '%s\n%s\n' "$out_ok" "$out_leak" | tail -n 10
  fi
}

# ---- pre-commit cases ----
# Every flagged value below is assembled at run time from separate words, so no line of this
# file holds a complete home path, address, host name or deny-list token.
# reset_w SHA: return the work repository to SHA after a case (scratch guard first).
# reset_in DIR SHA: the same for any scratch repository; reset_w is the work-repository form.
reset_in() { assert_scratch "$1"; git -C "$1" reset -q --hard "$2"; }
reset_w() { reset_in "$W" "$1"; }

case_leak_seed_precommit() {
  head_before=$(git -C "$W" rev-parse HEAD)
  count_before=$(git -C "$W" rev-list --count HEAD)
  write_seed "$W/seed-precommit.txt"
  git -C "$W" add seed-precommit.txt
  out=$(scratch_commit "$W" "Add a seed file" 2>&1); rc=$?
  count_after=$(git -C "$W" rev-list --count HEAD)
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'aws-access-token' && [ "$count_before" = "$count_after" ]
  then pass leak-seed-precommit
  else fail leak-seed-precommit "exit $rc, history count $count_before -> $count_after, expected a refusal naming rule aws-access-token"; printf '%s\n' "$out" | tail -n 6
  fi
  reset_w "$head_before"; rm -f "$W/seed-precommit.txt"
}

case_identifiers_precommit() {
  head_before=$(git -C "$W" rev-parse HEAD)
  count_before=$(git -C "$W" rev-list --count HEAD)
  id_a=Users; id_b=devname; id_c=project
  {
    printf 'path=/%s/%s/%s/notes\n' "$id_a" "$id_b" "$id_c"
    printf 'addr=%s.%s.%s.%s\n' 192 168 1 20
    printf 'host=%s.%s\n' testbox local
    printf 'mail=%s@%s\n' person mail.org
  } > "$W/identifiers.txt"
  git -C "$W" add identifiers.txt
  out=$(scratch_commit "$W" "Add a file of identifiers" 2>&1); rc=$?
  count_after=$(git -C "$W" rev-list --count HEAD)
  why=
  [ "$rc" -ne 0 ] || why="$why commit succeeded;"
  [ "$count_before" = "$count_after" ] || why="$why history count $count_before -> $count_after;"
  for rule in home-path-unix private-ipv4 internal-hostname email-address; do
    printf '%s\n' "$out" | grep -q "$rule" || why="$why rule $rule not named;"
  done
  if [ -z "$why" ]; then pass identifiers-precommit
  else fail identifiers-precommit "$why"; printf '%s\n' "$out" | tail -n 8
  fi
  reset_w "$head_before"; rm -f "$W/identifiers.txt"
}

case_identifier_false_positive_guards() {
  head_before=$(git -C "$W" rev-parse HEAD)
  count_before=$(git -C "$W" rev-list --count HEAD)
  {
    printf 'contact: someone@example.com\n'
    printf 'contact: support@anthropic.com\n'
    printf 'settings file: settings.local.json\n'
    printf 'dependency: some-package@0.2.25\n'
    printf 'prose: macOS keeps homes under /Users/ and Linux under /home/ in general.\n'
  } > "$W/benign.txt"
  git -C "$W" add benign.txt
  out=$(scratch_commit "$W" "Add a file of benign look-alikes" 2>&1); rc=$?
  count_after=$(git -C "$W" rev-list --count HEAD)
  if [ "$rc" -eq 0 ] && [ "$count_after" -eq $((count_before + 1)) ]
  then pass identifier-false-positive-guards
  else fail identifier-false-positive-guards "exit $rc, history count $count_before -> $count_after, expected the commit to succeed"; printf '%s\n' "$out" | tail -n 8
  fi
  reset_w "$head_before"; rm -f "$W/benign.txt"
}

case_denylist_precommit() {
  head_before=$(git -C "$W" rev-parse HEAD)
  count_before=$(git -C "$W" rev-list --count HEAD)
  deny_a=gnarly; deny_b=Wombat42
  deny_token="${deny_a}${deny_b}"
  deny_file="$W/.git/info/preclear-deny.txt"
  printf '# local deny list for this throwaway clone\n%s\n' "$deny_token" > "$deny_file"
  printf 'note about %s here\n' "$deny_token" > "$W/deny-hit.txt"
  git -C "$W" add deny-hit.txt
  out=$(scratch_commit "$W" "Add a file with a deny-list entry" 2>&1); rc=$?
  count_after=$(git -C "$W" rev-list --count HEAD)
  why=
  [ "$rc" -ne 0 ] || why="$why commit succeeded;"
  [ "$count_before" = "$count_after" ] || why="$why history count $count_before -> $count_after;"
  printf '%s\n' "$out" | grep -q 'denylist check FAILED' || why="$why no denylist refusal message;"
  if printf '%s\n' "$out" | grep -q -i -F "$deny_token"; then why="$why the output printed the entry;"; fi
  if [ -z "$why" ]; then pass denylist-precommit
  else fail denylist-precommit "$why"; printf '%s\n' "$out" | tail -n 8
  fi
  : > "$deny_file"
  reset_w "$head_before"; rm -f "$W/deny-hit.txt"
}

case_fail_closed_no_scanner() {
  if env PATH=/usr/bin:/bin sh -c 'command -v gitleaks' >/dev/null 2>&1; then
    echo "SKIP fail-closed-no-scanner: gitleaks is on the system directories"
    return
  fi
  out=$(cd "$W" && env PATH=/usr/bin:/bin sh .githooks/pre-commit 2>&1); rc=$?
  if [ "$rc" -eq 1 ] && printf '%s\n' "$out" | grep -q 'gitleaks not found'
  then pass fail-closed-no-scanner
  else fail fail-closed-no-scanner "exit $rc, expected exit 1 saying gitleaks was not found"; printf '%s\n' "$out" | tail -n 4
  fi
}

# ---- fresh-clone cases ----
# A local-path clone of the real repository (no network). Its origin is removed at once, so
# nothing in this clone can ever be pushed anywhere. Both seeded commits go through
# scratch_commit without its skip mode: the first shows that hooks really are off in a fresh
# clone, the second that the one documented command turns them on. The guard asserts the
# clone's toplevel is under the throwaway directory and is not the real repository.
W3="$TP/fresh"
FRESH_OK=
fresh_clone() {
  [ -n "$FRESH_OK" ] && return 0
  git clone -q "$REPO" "$W3" 2>/dev/null || return 1
  git -C "$W3" remote remove origin
  git -C "$W3" config user.name "Fresh Cloner"
  git -C "$W3" config user.email fresh-cloner@example.com
  scratch_ok "$W3" || return 1
  FRESH_OK=yes
}

case_fresh_clone_hooks_off_by_default() {
  if ! fresh_clone; then fail fresh-clone-hooks-off-by-default "the local clone of the repository failed"; return; fi
  assert_scratch "$W3"
  hp=$(git -C "$W3" config --get core.hooksPath)
  head_before=$(git -C "$W3" rev-parse HEAD)
  count_before=$(git -C "$W3" rev-list --count HEAD)
  write_seed "$W3/seed-fresh.txt"
  git -C "$W3" add seed-fresh.txt
  out=$(scratch_commit "$W3" "Add a seed file" 2>&1); rc=$?
  count_after=$(git -C "$W3" rev-list --count HEAD)
  why=
  [ -z "$hp" ] || why="$why core.hooksPath is already set;"
  [ "$rc" -eq 0 ] || why="$why the seeded commit was refused (exit $rc);"
  [ "$count_after" -eq $((count_before + 1)) ] || why="$why history count $count_before -> $count_after;"
  if [ -z "$why" ]; then pass fresh-clone-hooks-off-by-default
  else fail fresh-clone-hooks-off-by-default "$why"; printf '%s\n' "$out" | tail -n 6
  fi
  reset_in "$W3" "$head_before"; rm -f "$W3/seed-fresh.txt"
}

case_fresh_clone_enable_blocks_seed() {
  if ! fresh_clone; then fail fresh-clone-enable-blocks-seed "the local clone of the repository failed"; return; fi
  assert_scratch "$W3"
  git -C "$W3" config core.hooksPath .githooks
  head_before=$(git -C "$W3" rev-parse HEAD)
  count_before=$(git -C "$W3" rev-list --count HEAD)
  write_seed "$W3/seed-fresh.txt"
  git -C "$W3" add seed-fresh.txt
  out=$(scratch_commit "$W3" "Add a seed file" 2>&1); rc=$?
  count_after=$(git -C "$W3" rev-list --count HEAD)
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q 'aws-access-token' && [ "$count_before" = "$count_after" ]
  then pass fresh-clone-enable-blocks-seed
  else fail fresh-clone-enable-blocks-seed "exit $rc, history count $count_before -> $count_after, expected a refusal naming rule aws-access-token"; printf '%s\n' "$out" | tail -n 6
  fi
  reset_in "$W3" "$head_before"; rm -f "$W3/seed-fresh.txt"
}

# ---- pre-flip tool negative control ----
# The tool must be able to FAIL. A local-path clone of the real repository (origin removed at
# once) gets one commit under a foreign identity that holds the run-time-built seed. The tool
# runs from the real repository with that clone as its source and must refuse on the three
# checks named below. The commit goes through scratch_commit without its skip mode, after the
# guard asserted the clone's toplevel is under the throwaway directory (T-01-26). The seed is
# never printed, and the case checks that the tool did not print it either.
W4="$TP/prepublish"
case_prepublish_detects_seed_and_foreign_identity() {
  if ! git clone -q "$REPO" "$W4" 2>/dev/null; then
    fail prepublish-detects-seed-and-foreign-identity "the local clone of the repository failed"; return
  fi
  git -C "$W4" remote remove origin
  assert_scratch "$W4"
  write_seed "$W4/seed-prepublish.txt"
  git -C "$W4" add seed-prepublish.txt
  (
    GIT_AUTHOR_NAME=Intruder; GIT_AUTHOR_EMAIL=intruder@example.org
    GIT_COMMITTER_NAME=Intruder; GIT_COMMITTER_EMAIL=intruder@example.org
    export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
    scratch_commit "$W4" "Add a seed file under a foreign identity"
  )
  seed_value=$(sed 's/^aws_key = //' "$W4/seed-prepublish.txt")
  out=$(cd "$REPO" && sh scripts/prepublish-check.sh --rehearse --skip-inventory --source "$W4" 2>&1); rc=$?
  why=
  [ "$rc" -ne 0 ] || why="$why the tool exited 0;"
  for chk in gate-clean strict-equals-accepted one-identity; do
    printf '%s\n' "$out" | grep -q "^FAIL $chk" || why="$why no FAIL line for $chk;"
  done
  if printf '%s\n' "$out" | grep -q -F "$seed_value"; then why="$why the tool printed the seed;"; fi
  if [ -z "$why" ]; then pass prepublish-detects-seed-and-foreign-identity
  else fail prepublish-detects-seed-and-foreign-identity "$why"; printf '%s\n' "$out" | tail -n 10
  fi
}

# Last case: nothing in the real repository moved, and the guard is not vacuous.
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

case_clean_push
case_identity_wrong_author_committer
case_leak_seed_prepush
case_leak_seed_absent_on_remote
case_identity_committer_only
case_identity_wrong_tagger
case_trailer_commit_msg
case_trailer_bypassed_prepush
case_unpinned_skips_identity
case_leak_seed_precommit
case_identifiers_precommit
case_identifier_false_positive_guards
case_denylist_precommit
case_fail_closed_no_scanner
case_fresh_clone_hooks_off_by_default
case_fresh_clone_enable_blocks_seed
case_prepublish_detects_seed_and_foreign_identity
case_real_origin_refs_unchanged

echo "throwaway directory (kept): $T"
[ "$FAILS" -eq 0 ]
