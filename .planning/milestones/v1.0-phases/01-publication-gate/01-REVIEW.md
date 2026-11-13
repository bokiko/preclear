---
phase: 01-publication-gate
reviewed: 2026-10-24T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - .githooks/pre-commit
  - .githooks/commit-msg
  - .githooks/pre-push
  - .githooks/checks/leaks.sh
  - .githooks/checks/identity.sh
  - .githooks/checks/denylist.sh
  - .githooks/attribution.ere
  - .githooks/README.md
  - .gitleaks.toml
  - .gitleaksignore
  - scripts/prepublish-check.sh
  - scripts/test-hooks.sh
  - .claude/settings.json
  - .claude/CLAUDE.md
findings:
  critical: 3
  warning: 8
  info: 9
  total: 20
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-24
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the POSIX sh hooks, the three check scripts, the gitleaks config, the accepted-findings list, the pre-flip script and the throwaway-clone test script. No structural (fallow) findings were supplied. The hook set is carefully built and mostly fails closed. Three paths do not. The commit-msg hook allows every message when its pattern file is missing or empty. The pre-push hook silently skips any check that is not executable. The home-folder path rule misses a bare home path with no trailing slash.

Verified by experiment against gitleaks 8.30.0 and a copy of the commit-msg hook (no repository file was modified, the deny-list file was not read, and the test suite was not run because it reads the deny list indirectly):

- With the pattern file missing or empty, the commit-msg hook exits 0 on a message that carries a co-author trailer.
- A skipped non-executable check prints nothing and does not change the exit status.
- With the repository gitleaks config, a bare home path (at end of line, before a space, before a quote) produced no finding. A four-part dotted version string (four numbers in the private 10-dot range separated by dots) and an SSH clone address (the git user, an at-sign, the GitHub host) did.

`.claude/settings.json` was checked against the installed Claude Code binary: `attribution` with `commit`, `pr` and `sessionUrl` is a recognised form, so no finding. `.claude/CLAUDE.md` and `.gitleaksignore` (15 fingerprints, 11 lines, 10 files, matching the comment and the count of 15 hard-coded in the pre-flip script) are consistent. The ignore list is an owner decision and is not reviewed on its merits.

## Critical Issues

### CR-01: commit-msg hook fails open when the pattern file is missing or empty

**File:** `.githooks/commit-msg:7`
**Issue:** The test is `if grep -v '^#' "$1" | grep -q -i -E -f "$here/attribution.ere"`. When `attribution.ere` is missing or unreadable, `grep` exits 2, the `if` treats any non-zero status as "no match", and the hook exits 0. An empty pattern file matches nothing, so the result is the same. Reproduced: both cases accept a message with a co-author trailer and only the missing-file case prints a `grep` error. This contradicts the stated fail-closed design. `identity.sh:11` checks readability but not emptiness, and `prepublish-check.sh:211` checks non-empty, so the three consumers of the one file disagree. The pre-push attribution check is the only backstop, and it runs only in a pinned clone.
**Fix:**
```sh
pat="$here/attribution.ere"
[ -s "$pat" ] || { echo "commit-msg FAILED: pattern file $pat is missing or empty" >&2; exit 1; }
grep -v '^#' "$1" | grep -q -i -E -f "$pat"
case $? in
  0) echo "commit-msg FAILED: attribution trailer found in the commit message" >&2; exit 1 ;;
  1) exit 0 ;;
  *) echo "commit-msg FAILED: pattern check errored" >&2; exit 1 ;;
esac
```
Use `[ -s ]` in `identity.sh` as well, and treat a grep status above 1 as failure there.

### CR-02: pre-push silently skips any check that is not executable or not present

**File:** `.githooks/pre-push:27-30`
**Issue:** `[ -x "$check" ] || continue` drops a check with no message. If the executable bit is lost (a zip download, a copy without mode preservation, a checkout with `core.fileMode=false`), the leak, identity and deny-list checks all vanish and the hook exits 0 with `rc=0`. If the glob matches nothing, the literal pattern fails `-x` and the same happens. The README tells strangers to enable these hooks, so this is a realistic way to end up with a gate that approves everything. `pre-commit` handles the same condition correctly: a non-executable `denylist.sh` gives exit 126 and the commit stops.
**Fix:**
```sh
found=0
for check in "$here"/checks/*.sh; do
  [ -e "$check" ] || continue
  found=1
  if [ ! -x "$check" ]; then
    echo "pre-push FAILED: $check is not executable" >&2; rc=1; continue
  fi
  "$check" "$ranges" || rc=1
done
[ "$found" -eq 1 ] || { echo "pre-push FAILED: no checks found" >&2; rc=1; }
exit $rc
```
Alternatively invoke each check as `sh "$check"` so the mode bit does not matter.

### CR-03: home-folder path rule does not match a path with no trailing slash

**File:** `.gitleaks.toml:9`
**Issue:** The regex `/(?:Users|home)/[A-Za-z0-9._-]{1,64}/` requires a slash after the user name. A bare home directory is the commonest way a user name leaks and none of these matched in testing: `HOME=/Users/<name>`, `cd /Users/<name> && ls`, and `cd "/Users/<name>"`. A Windows path (`C:\Users\<name>\...`) and `/root/...` are also not covered. This rule is the main reason for the identifier scan, so a miss here defeats the stated goal of the gate.
**Fix:** End the user-name segment with a boundary instead of a slash:
```toml
regex = '''/(?:Users|home)/[A-Za-z0-9._-]{1,64}(?:[/\s"'`:;,)\]]|$)'''
```
Then re-run the strict scan: the `.gitleaksignore` fingerprints and the fixed count of 15 in `prepublish-check.sh` may change. Add a test case for the bare form. The prose guard in `scripts/test-hooks.sh` (`/Users/` and `/home/` followed by a space) must still pass, which the segment requirement ensures.

## Warnings

### WR-01: relative `--source` and `--record` are resolved after the script changes directory

**File:** `scripts/prepublish-check.sh:45`, `:51`, `:92`
**Issue:** The script runs `cd "$TOP"` at line 51. The existing-record check at line 45 runs before that, in the caller's directory. The record write and the `--source` clone happen after it, relative to the repository top. A relative `--record out.md` is tested in one place and created in another, which can drop an untracked file into the repository. A relative `--source ../other` is resolved against the repository top and can clone a different directory from the one the caller meant.
**Fix:** Make both absolute before the `cd`:
```sh
case $RECORD in ''|/*) ;; *) RECORD=$(pwd)/$RECORD ;; esac
case $SOURCE in ''|/*|*://*|*:*) ;; *) SOURCE=$(pwd)/$SOURCE ;; esac
```
Do this right after argument parsing, then keep the existing-file test.

### WR-02: the attribution check passes when `git log` fails

**File:** `scripts/prepublish-check.sh:212-215`
**Issue:** `git -C "$M" log --all --format=%B > "$W/messages" 2>/dev/null` ignores its exit status and hides its errors. A failure leaves an empty file, `grep -c` prints 0, and the check reports PASS. Other checks in this script fail closed on tool errors, so this one is the odd one out.
**Fix:**
```sh
if git -C "$M" log --all --format=%B > "$W/messages"; then
  trailer_hits=$(grep -i -E -c -f "$W/attribution.ere" "$W/messages")
  ...
else
  fail no-attribution-trailers "could not read the commit messages"
fi
```

### WR-03: the pre-flip deny-list scan can pass or skip without the owner's entries

**File:** `scripts/prepublish-check.sh:221-229`, `.githooks/checks/denylist.sh:33`
**Issue:** The list is built from host names plus an optional local file. If that file is absent or empty in the clone running the check, the scan still reports `PASS denylist-history (0 added lines match)` whenever a host name supplies one entry. If nothing supplies an entry it prints SKIP, and `finish` still reports `RESULT PASS`. The final gate therefore cannot tell "no hits" from "the owner's real entries were never loaded". That is the exact condition the pre-publication gate exists to rule out.
**Fix:** Make the pre-flip run require the local file to exist and hold at least one entry (a status check, not a read of its content), and treat a SKIP in this check as a FAIL in default mode. For example, have `denylist.sh --history` exit non-zero with a distinct message when the extra file is missing or yields no entry, and let `prepublish-check.sh` fail on it unless `--rehearse` is set.

### WR-04: deny-list check never looks at file paths or commit messages

**File:** `.githooks/checks/denylist.sh:43-47`
**Issue:** `count_hits` tests only added content lines. The `+++ b/<path>` header is captured for reporting and then skipped, so an added or renamed file whose name contains an entry passes. Commit subjects and bodies are not examined either (the identity check scans messages for trailers only). A real name or host name in a path or message is as much a leak as one in content.
**Fix:** Also test the captured path in the header branch, and add a message pass such as `git log --format=%B $rev` through the same entry list for the push and history modes. Report counts only, as now.

### WR-05: deny-list scan treats an awk failure as "no hits"

**File:** `.githooks/checks/denylist.sh:58`, `:69`, `:81`
**Issue:** `hits=$(count_hits < "$diffout")` and the two `n=$(count_hits ... | awk ...)` forms take the status of the last command only. If the first `awk` dies (out of memory on a huge diff, a locale error), its output is empty and the check reports zero hits and passes. This is a fail-open on a tool error in a gate that otherwise checks every `git` status.
**Fix:** Write the awk output to a file and test its status:
```sh
count_hits < "$diffout" > "$hitsout" || { echo "denylist check FAILED: scan error" >&2; exit 1; }
```
Keep `$hitsout` under the same `trap` as the other temporary files.

### WR-06: host-name entries of short common words block unrelated commits

**File:** `.githooks/checks/denylist.sh:22-32`
**Issue:** Every output of `hostname`, `hostname -s` and the two `scutil` names of four or more characters is added and matched as a case-insensitive substring. A machine called `host`, `home`, `work`, `main`, `test`, `node` or `localhost` (common in containers and CI) makes any added line that contains that word fail the commit and the push. A stranger who enables the hooks in such an environment cannot commit normal text and will likely reach for `--no-verify`, which switches off the leak gate too.
**Fix:** Raise the host-name minimum (for example 6) or add a short stop list of generic names, and keep the four-character floor only for entries from the local file.

### WR-07: the whole `anthropic.com` domain is exempt from the email rule

**File:** `.gitleaks.toml:54`
**Issue:** The allowlist is described as "Reserved or role-account domains", but `anthropic.com` is neither, and the pattern exempts every local part. A named person's work address at that domain passes both the staged and the push scan. The test only needs a role address (`support@`), and `attribution.ere` only needs `noreply@`.
**Fix:** Allow the specific role local parts instead, for example `(?:noreply|support)@anthropic\.com`, and keep the reserved `example.*` domains and the GitHub no-reply form as they are.

### WR-08: the pre-flip negative control would pass for the wrong reason

**File:** `scripts/test-hooks.sh:419-421`
**Issue:** The case only checks that a `FAIL gate-clean`, `FAIL strict-equals-accepted` and `FAIL one-identity` line exists. In `prepublish-check.sh` the gate check fails for any non-zero scanner status, so a broken config or a scanner crash (exit 1) satisfies the test exactly as a real detection (exit 2) does. The strict check also fails for an unrelated reason because the count of 15 will not match. The control therefore does not prove the seed was detected. There is no positive control for the tool either.
**Fix:** Assert the specific text: `grep -q '^FAIL gate-clean: gate exit 2'`, and for the strict check require the `outside commit` or `fingerprint sets differ` detail. Add a positive case, if feasible, in which a clean scratch repository with a matching accepted list passes the history checks.

## Info

### IN-01: no option terminator before the user-supplied clone source

**File:** `scripts/prepublish-check.sh:95`
**Issue:** `git clone -q --mirror "$src" "$M"` takes `--source` from the command line or the origin URL from config. A value that starts with `-` is read as an option (for example `--upload-pack=...`). The input comes from the owner, so the risk is low.
**Fix:** `git clone -q --mirror -- "$src" "$M"`.

### IN-02: unquoted range expansion mishandles remote names with spaces or glob characters

**File:** `.githooks/pre-push:19`, consumers in `checks/identity.sh:15`, `checks/denylist.sh:79`
**Issue:** The range is stored as one string and expanded unquoted on purpose. When pushing to a URL or path (the hook receives it as `$1`) that contains a space, the `--remotes=` argument is split and `git log` fails on a bad revision. The result is a blocked push, not a bypass, but a glob character in the URL can also expand against files in the repository root.
**Fix:** Store the revision arguments separately (one per line) and read them into positional parameters, or skip the `--remotes` exclusion when `$remote` is not a plain remote name.

### IN-03: deny entries are not trimmed, and a pinned name starting with a dash breaks grep

**File:** `.githooks/checks/denylist.sh:32`, `.githooks/checks/identity.sh:17`
**Issue:** An entry with trailing spaces (a common editor artefact) is kept verbatim and then never matches. In `identity.sh`, `grep -v -x -F "$pinned"` would read a pinned value that begins with `-` as an option, error out, and leave `bad` empty, which passes.
**Fix:** Trim in the awk step (`gsub(/^[ \t]+|[ \t]+$/, "")`) and use `grep -v -x -F -e "$pinned"`.

### IN-04: attribution patterns are both broad and incomplete

**File:** `.githooks/attribution.ere:2-3`
**Issue:** The third pattern is unanchored, so ordinary prose such as a commit that discusses the pattern ("generated with Gemini-style output") is refused, which confirmed in testing. Gaps: `Co-developed-by:` and `Made with <tool>` are not matched, the signed-off and reviewed-by lines list only five tool names, and annotated tag messages are never scanned by any check.
**Fix:** Anchor the third pattern to a line start or to the common `Generated with [` form, add `co-developed-by` to the first pattern, and scan `%(contents)` of pushed annotated tags in `identity.sh`.

### IN-05: false positives and uncovered identifier forms in the gitleaks rules

**File:** `.gitleaks.toml:27`, `:34`, `:40`
**Issue:** Confirmed false positives: a four-part dotted version string whose first number is 10 (private-ipv4) and an SSH clone address of the form git, at-sign, GitHub host, colon, path (email-address). Not detected in testing: IPv6 unique-local and link-local addresses, MAC addresses, `169.254.x.x`, and a `.local` host name followed by a full stop.
**Fix:** Add the SSH clone address form (git user, at-sign, GitHub host) to the second allowlist, decide which of the missed forms matter for this repository, and add rules or test cases for them.

### IN-06: the hooks trust the working-tree config, and the scanner version is not enforced

**File:** `.githooks/checks/leaks.sh:10`, `.githooks/pre-commit:11`, `.githooks/README.md:55`
**Issue:** Both hooks read `.gitleaks.toml` and `.gitleaksignore` from the working tree, so an uncommitted edit changes what the gate accepts. The pre-flip script correctly takes them from the mirror HEAD. The README says only 8.30.x was tested but nothing checks the version at run time; the record only prints it.
**Fix:** Optionally warn when either file differs from HEAD, and compare `gitleaks version` against the tested minor release in the pre-flip script.

### IN-07: the "anonymous" probe can use the owner's credentials

**File:** `scripts/prepublish-check.sh:313`
**Issue:** `-c credential.helper=` does not undo a global `url.<base>.insteadOf` rewrite from https to SSH. With such a rewrite the "anonymous" `ls-remote` authenticates with the owner's key and succeeds on a private repository, so the probe reports a false failure.
**Fix:** Run the probe with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1`, as `test-hooks.sh` already does for its own runs.

### IN-08: a pipe character in a detail string corrupts the record table

**File:** `scripts/prepublish-check.sh:62`, `:345`, `:350`
**Issue:** Rows are stored as `a|b|c` and printed with `awk -F'|'`. A detail that contains `|` is cut off at the third field and the table loses content.
**Fix:** Use a character that cannot occur (a tab or `\037`) as the delimiter.

### IN-09: coverage gaps and silent skips in the test script

**File:** `scripts/test-hooks.sh:326-336`, `:453`
**Issue:** The no-scanner case exercises only `pre-commit`. The same fail-closed path in `leaks.sh` is untested, and nothing tests a non-executable check (see CR-02) or an empty or missing pattern file (see CR-01). The case is skipped, not failed, when `gitleaks` is in the system directories, and the run still exits 0. The throwaway directories hold the run-time seed file and are never removed.
**Fix:** Add cases for the three untested conditions, run the no-scanner case with a sanitised `PATH` that provably lacks the scanner, and count a skipped case in the final summary line.

---

_Reviewed: 2026-10-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
