---
phase: 04-full-matrix-row-7-and-review
reviewed: 2026-11-11T16:04:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - CHANGELOG.md
  - tests/acceptance.md
  - tests/harness/README.md
  - tests/harness/data/layout-s1-prompts.md
  - tests/harness/git-wrapper
  - tests/harness/pc_baseline.py
  - tests/harness/pc_checks.py
  - tests/harness/pc_cleanclone.py
  - tests/harness/pc_compare.py
  - tests/harness/pc_evidence.py
  - tests/harness/pc_flags.py
  - tests/harness/pc_manifest.py
  - tests/harness/pc_matrix.py
  - tests/harness/pc_review.py
  - tests/harness/pc_row1.py
  - tests/harness/pc_rowhooks.py
  - tests/harness/pc_rows.py
  - tests/harness/pc_rowseeds.py
  - tests/harness/pc_testutil.py
  - tests/harness/test_allowlist.py
  - tests/harness/test_baseline.py
  - tests/harness/test_bash_shims.py
  - tests/harness/test_boundaries.py
  - tests/harness/test_cleanclone.py
  - tests/harness/test_compare.py
  - tests/harness/test_driver_matrix.py
  - tests/harness/test_frozen_baseline.py
  - tests/harness/test_git_wrapper.py
  - tests/harness/test_manifest.py
  - tests/harness/test_matrix_cli.py
  - tests/harness/test_readme.py
  - tests/harness/test_review.py
  - tests/harness/test_row12.py
  - tests/harness/test_row_generic.py
  - tests/harness/test_rows_git.py
  - tests/harness/test_rows_helper.py
  - tests/harness/test_rows_plain.py
findings:
  critical: 0
  warning: 5
  info: 8
  total: 13
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-11-11T16:04:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Scope was the files Phase 4 changed since base commit 994267a. The production modules and the shell wrapper were read in full or by their complete diff. The large test files were scanned for reliability patterns and for the project constraints, not read line by line. No test suite, claude binary, matrix run or clean-clone run was started. The git wrapper was exercised once by hand in a scratch folder with a stub run root to confirm its logging, ordinal and exit code.

Checked against the stated constraints:

- **Python 3.9 floor and stdlib only:** every scoped Python file parses with feature version 3.9, and a search for 3.10+ APIs found none.
- **bash 3.2:** the git wrapper uses nothing newer and behaved correctly under the system bash 3.2.57.
- **Deletion primitives:** none in the production modules other than the two allowed ones. The test files use temporary folders that are never removed, with one exception noted in IN-08.
- **Home path, host name, email, login name:** none found in the harness sources, the scoped docs, or the new baseline folder under tests/evidence. The child environment in the clean-clone bootstrap carries the login name only as a value that is never printed or filed.
- **No verdict from the harness:** the new analyses print counts, ids and yes/no equality only.
- **No network:** one conflict, WR-05.

There are no blockers. The five warnings are places where the harness can report a wrong or weaker fact than it appears to, so a reviewer reading the filed evidence could be misled.

## Warnings

### WR-01: A model-issued `git -c ...` call is labelled as Claude Code's own internal call

**File:** `tests/harness/pc_review.py:1096`
**Issue:** `join_ids` labels every logged git call whose first argument is `-c` as `internal` before it looks for a matching executed part of the stream. The wrapper log cannot tell Claude Code's own calls from the model's calls, so a model call such as `git -c color.ui=never status` is filed as "internal: no tool_use exists for it" although the stream holds exactly that tool_use. `test_a_dash_c_call_is_internal_even_when_a_part_has_the_same_argv` in `tests/harness/test_review.py:1111` pins this behaviour, so the defect is encoded as intended. The README states the rule as fact ("a call that starts with `-c` is Claude Code's own"). For row 11 this matters because the row exists to show which git calls the model made.
**Fix:** Try the match first and fall back to `internal` only when no executed part has the same arguments.
```python
else:
    matches = [tool_id for tool_id, argv in parts if argv == call.argv]
    unique = tuple(dict.fromkeys(matches))
    if not matches:
        label = LABEL_INTERNAL if call.argv[:1] == ("-c",) else LABEL_UNMATCHED
        joined.append(JoinedCall(call, label, ()))
    elif len(matches) == 1:
        joined.append(JoinedCall(call, LABEL_ID, unique))
    else:
        joined.append(JoinedCall(call, LABEL_AMBIGUOUS, unique))
```
Update the test and the README sentence to match.

### WR-02: `unquote_printf_q` decodes escapes as code points, so non-ASCII arguments never match

**File:** `tests/harness/pc_review.py:970-985` (`_ansi_c`) and `:1039-1045`
**Issue:** Under a C locale, bash 3.2 prints a non-ASCII argument through `%q` as `$'caf\303\251'`. This was checked on the system bash. `_ansi_c` turns each octal or hex escape into one character with `chr(...)`, which yields the two characters U+00C3 U+00A9 instead of the single character U+00E9. The tool_use argument from the stream holds U+00E9, so the call is reported as `unmatched` even though it ran. Row 10's hostile file names make non-ASCII git arguments plausible, and the wrapper sits first on the search path for any row that names it. The failure is silent: the line is counted as readable.
**Fix:** Collect escapes as bytes and decode the finished word as UTF-8, falling back to the `None` (UNCONFIRMED) result when the bytes are not valid UTF-8.
```python
# in _ansi_c: append bytes for \xHH and \NNN, characters (encoded) for everything else,
# then at the closing quote: return b"".join(out).decode("utf-8"), index + 1  (UnicodeDecodeError -> None)
```

### WR-03: Row 8a states that no repository exists above the run root but nothing checks it

**File:** `tests/harness/pc_rowseeds.py:1190` (`seed_row8a`), `tests/harness/pc_rows.py:370-377`, `tests/harness/README.md:387`
**Issue:** The row's setup text, copied into the row README, says "the run root lies under no repository either". The seed only creates a project with no `.git` entry. The runs root comes from `PRECLEAR_RUNS_ROOT`, and `pc_spike.runs_root` refuses ancestors that hold instruction files but never looks for an ancestor `.git`. If the runs root is set under any repository, the model's `git status` finds that repository, the row no longer tests the no-git case, and the filed README still asserts otherwise. The git state captured by the harness (`n/a`) would also disagree with what the model saw.
**Fix:** In `seed_row8a`, walk the ancestors of the project folder and raise `pc_spike.SpikeError` with a fixed message when any of them holds a `.git` entry. Do this before the first spend.

### WR-04: The clean-clone stub-digest assertion passes silently when no digest line was checked

**File:** `tests/harness/pc_cleanclone.py:529-541`, `:607-621`, `:633-635`
**Issue:** `_small_text` returns `None` for any file over 4096 bytes, and the digest loop `continue`s on `None`. A row folder whose `digests.txt` is larger than the cap, missing, or lacking the stub line contributes nothing to `digests_checked` or `digest_mismatches`. `post_refused` looks only at mismatches, so a run with zero digests checked and a stub that differs from the clone's passes the post-assertion. The README states that "each filed row's stub digest must equal the clone stub's digest". Today the files are about 700 bytes, so the filed baseline is not affected, but the guard fails open as soon as the file grows.
**Fix:** Treat an unreadable or oversized `digests.txt` of a row with a wrapper as a mismatch, and refuse when `stub_roots > 0` and `digests_checked == 0`.
```python
def post_refused(post: Post) -> bool:
    return (post.helper_calls_other > 0 or post.other_roots > 0 or post.digest_mismatches > 0
            or (post.stub_roots > 0 and post.digests_checked == 0))
```

### WR-05: The default clean-clone source is an https clone, and the harness README still says it needs no network

**File:** `tests/harness/pc_cleanclone.py:900-908` (default source), `:332` (clone), `tests/harness/README.md:5`
**Issue:** The project constraint for this phase is "no network". With no `--source`, `pc_cleanclone.py` reads the origin address of the main tree and runs `git clone` against it. The classifier accepts any `https://` address, so the default path is a network fetch. The harness README opening still reads "Everything here runs without a model, without a network and without spending a token", which Phase 4 made untrue for the paid rows and for this bootstrap. A reader relying on that sentence would run the bootstrap believing it is offline.
**Fix:** Either require an explicit `--source` and accept only a local folder unless a flag such as `--allow-network` is given, or record the clone as the one sanctioned network step in the constraint list. In both cases correct the README sentence to name the paid rows and the clone as the exceptions.

## Info

### IN-01: The copy-back runs before a contaminated run is refused

**File:** `tests/harness/pc_cleanclone.py:1034-1041`
**Issue:** When a helper call reached something other than the clone's stub, the folder is still finalized and copied into the main tree's evidence folder, and only then does the bootstrap exit 11. The README documents this ("ends the run with exit 11 after the copy-back"), and the clone facts record the count, so it is a deliberate trade-off against stranding measured rows. The risk is that a folder known to be contaminated sits in the working tree next to clean ones with nothing in its name saying so.
**Fix:** Optional. Copy back under a distinct, labelled name when `post_refused(post)` is true.

### IN-02: The output scrubber masks paths only, not the login name used under `--real-home`

**File:** `tests/harness/pc_cleanclone.py:164-180`, `:257-259`
**Issue:** `Scrubber` replaces known paths and home-shaped paths. With `--real-home` the child receives the account name as `USER`, and any child line that prints the bare name, such as an authentication message, passes through unchanged. The clone's own scripts are built not to print it, so this is a hardening gap and not a known leak.
**Fix:** When `real_home` is set, add the `USER` value as a scrub pair with a fixed token, skipping values shorter than three characters.

### IN-03: Invisible U+2028 and U+2029 characters are written literally in a source string

**File:** `tests/harness/pc_baseline.py:1274`
**Issue:** The control-character check in `record_verdict` contains literal U+2028 and U+2029 characters inside the string `"  \x85"`. Python accepts them, but an editor or a copy-paste can mangle or drop them, and a reader cannot see what is rejected.
**Fix:** Write them as escapes: `character in "  \x85"`.

### IN-04: The correlated git-call file is harness-authored but not in the verdict-word scan set

**File:** `tests/harness/pc_evidence.py:1326-1343`
**Issue:** `git-calls-correlated.txt` is written by the harness in its own words but is not listed in `_AUTHORED_ROW_FILES`, so `check-words` never scans it. Its content is fixed text plus ids restricted by `_safe`, so no vocabulary can reach it today. A later edit to the renderer would not be covered.
**Fix:** Add the file name to `_AUTHORED_ROW_FILES`.

### IN-05: Wrapper logs are read through a silent 8 MiB cap

**File:** `tests/harness/pc_review.py:1195-1203`
**Issue:** `_read_capped` returns the first 8 MiB of a log without saying it truncated. Calls after the cap are missing from the counts, and the cut line is counted UNCONFIRMED, so the output looks complete.
**Fix:** Read one byte more than the cap and, when it is present, add a counted line such as `log-truncated: yes`.

### IN-06: Production modules call private functions of other modules

**File:** `tests/harness/pc_review.py:763-768` (calls `pc_checks._read_redirections` and `_tokens`), `tests/harness/pc_cleanclone.py:131` (the probe calls `pc_matrix._run_preflight`)
**Issue:** Renaming or changing the signature of those underscore functions breaks the callers without any signal in the defining module. The clean-clone probe fails only after the clone has been made.
**Fix:** Expose public names in `pc_checks` and `pc_matrix` and call those.

### IN-07: The git wrapper runs the program named in a file that sits in a folder the model can write

**File:** `tests/harness/git-wrapper:24-33`, `tests/harness/pc_review.py:1159-1192`
**Issue:** The wrapper executes whatever path `real-git` holds and runs inside `ckpt`, an approved write root. The digest record detects a change after the fact and the filed section reports it, but nothing stops the changed file from running during the session. The profile for row 11 limits what the model can run, so this is hardening and not an exploitable path under the current allowlist.
**Fix:** Optional. Have the wrapper compare the file's digest with a value baked in at install time, or resolve the real git at install time into the wrapper itself.

### IN-08: One meta-test asserts nothing about the code under test, and temporary-folder handling is inconsistent

**File:** `tests/harness/test_readme.py:324-330`, `tests/harness/test_bash_shims.py:141,203`
**Issue:** `test_a_changed_digit_in_the_block_would_fail_the_check` builds an altered string and asserts that `str.replace` changed it. It cannot fail for any change to the harness. Separately, every other test file uses `tempfile.mkdtemp` and leaves the folders behind, as the new test docstrings state, while `test_bash_shims.py` uses `TemporaryDirectory`, which deletes on exit.
**Fix:** Either drive the real block check with the altered text or remove the test. Pick one temporary-folder policy for the harness tests.

---

_Reviewed: 2026-11-11T16:04:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
