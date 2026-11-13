---
phase: 01-publication-gate
fixed_at: 2026-10-24T14:34:46Z
review_path: .planning/phases/01-publication-gate/01-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-10-24T14:34:46Z
**Source review:** .planning/phases/01-publication-gate/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 11 (CR-01..CR-03, WR-01..WR-08)
- Fixed: 11
- Skipped: 0

**Verification:** each fix ran `sh scripts/test-hooks.sh` in an isolated worktree (the tests use temporary clones). The new test case for each finding was also run against the pre-fix code and failed there. After the fast-forward and worktree removal the full suite was run again in the main checkout: 29 cases, 29 PASS, 0 FAIL (the baseline was 18). The pre-flip tool in `--rehearse` mode also passed on the real history (15 accepted fingerprints unchanged).

## Fixed Issues

### CR-01: commit-msg hook fails open when the pattern file is missing or empty

**Files modified:** `.githooks/commit-msg`, `.githooks/checks/identity.sh`, `scripts/test-hooks.sh`
**Commit:** 6235b16
**Applied fix:** commit-msg refuses when the pattern file is missing or empty or the message file is unreadable, and treats a grep status above 1 as failure. identity.sh uses a non-empty test and refuses on a grep error. New case: attribution-pattern-fail-closed (missing and empty, commit-msg and pre-push).

### CR-02: pre-push silently skips any check that is not executable or not present

**Files modified:** `.githooks/pre-push`, `scripts/test-hooks.sh`
**Commit:** faa0c50
**Applied fix:** a non-executable check, or no check at all, now prints a message and refuses the push. New case: prepush-nonexecutable-check-fail-closed.

### CR-03: home-folder path rule does not match a path with no trailing slash

**Files modified:** `.gitleaks.toml`, `scripts/test-hooks.sh`
**Commit:** 42543cc
**Applied fix:** the user-name segment now ends at a boundary (slash, whitespace, quote, punctuation, or end of input). The strict mirror scan was repeated: the 15 accepted fingerprints are unchanged, no new finding, tree scan clean. New case: bare-homedir-precommit (end of line, before a space, before a quote, end of file). The Windows path form and `/root/` named in the issue text are not covered, because the review's fix text only changes the boundary. This is a decision left open (see below). Marked: fixed, requires human verification (regex logic).

### WR-01: relative --source and --record are resolved after the script changes directory

**Files modified:** `scripts/prepublish-check.sh`, `scripts/test-hooks.sh`
**Commit:** 1b24082
**Applied fix:** both are made absolute right after argument parsing. A `--source` that names no local path (URL or host:path) is left as given. New case: prepublish-relative-source, run from a subdirectory.

### WR-02: the attribution check passes when git log fails

**Files modified:** `scripts/prepublish-check.sh`, `scripts/test-hooks.sh`
**Commit:** a816ed6
**Applied fix:** the git log status and the grep status are checked; a failure prints FAIL. Standard error stays hidden so no path is printed. New case: prepublish-log-failure-fails (a git shim fails only the message listing).

### WR-03: the pre-flip deny-list scan can pass or skip without the owner's entries

**Files modified:** `.githooks/checks/denylist.sh`, `scripts/prepublish-check.sh`, `.githooks/README.md`, `scripts/test-hooks.sh`
**Commit:** 82af43d
**Applied fix:** `denylist.sh --history` exits 3 without scanning when the local deny list is missing or has no usable entry (it counts entries, never reads them out). `--allow-no-local` is for rehearsal only. The pre-flip tool passes it only with `--rehearse`, and in default mode a SKIP or missing list is a FAIL. New case: denylist-history-requires-local-list. Marked: fixed, requires human verification (gate logic).

### WR-04: deny-list check never looks at file paths or commit messages

**Files modified:** `.githooks/checks/denylist.sh`, `scripts/test-hooks.sh`
**Commit:** 5ff3422
**Applied fix:** added and modified file names (including empty files) are matched in staged, push and history modes. Commit messages are matched in push and history modes. A name that holds an entry is shown as "(file name)" so the entry is never printed. A staged commit message cannot be seen at pre-commit time, so staged mode covers names only. New case: denylist-paths-and-messages.

### WR-05: deny-list scan treats an awk failure as "no hits"

**Files modified:** `.githooks/checks/denylist.sh`, `scripts/test-hooks.sh`
**Commit:** e00fcec
**Applied fix:** scan output goes to a temporary file with the status checked, the totals step is checked, and the entry-list build (awk and sort) is checked, so a failure refuses instead of reading as an empty list. New case: denylist-awk-failure-fails (awk shim, both failure points).

### WR-06: host-name entries of short common words block unrelated commits

**Files modified:** `.githooks/checks/denylist.sh`, `.githooks/README.md`, `scripts/test-hooks.sh`
**Commit:** a041187
**Applied fix:** host names need six or more characters and must not be on a short generic list. Local-file entries keep the four-character floor. New case: denylist-hostname-entries (generic names allowed, a distinctive name refused, a four-character local entry refused). Marked: fixed, requires human verification (the stop list is a judgment call).

### WR-07: the whole anthropic.com domain is exempt from the email rule

**Files modified:** `.gitleaks.toml`, `scripts/test-hooks.sh`
**Commit:** 2011b61
**Applied fix:** the history author list holds only the owner's address, and the repository contains only two addresses at that domain (the no-reply and the support role address). The allowlist now names exactly those two. Reserved example domains and the GitHub no-reply form are unchanged. New case: named-vendor-address-refused, plus a no-reply line in the false-positive guard.

### WR-08: the pre-flip negative control would pass for the wrong reason

**Files modified:** `scripts/test-hooks.sh`
**Commit:** b4ae0bd
**Applied fix:** the control now asserts gate-clean and tree-clean fail with exit 2, strict-equals-accepted names a finding outside the accepted commit, and one-identity names the second identity. A scanner that crashes (exit 1) no longer satisfies it (verified with a stub scanner). New positive control: prepublish-passes-clean-source.

## Skipped Issues

None.

## Left open

- The real clone's local deny list is empty or missing, so the pre-flip rehearsal now reports host-name entries only. The default-mode final gate will FAIL until the owner adds entries to the local deny list. This is the intended effect of WR-03.
- CR-03: Windows-style home paths and `/root/` are still not covered (new rules would need their own accepted-list review).

---

_Fixed: 2026-10-24T14:34:46Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
