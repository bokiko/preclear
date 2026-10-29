---
phase: 03-walking-skeleton-row-1
reviewed: 2026-10-29T18:30:00Z
depth: standard
pass: 4 (gap-closure diff 5ef92ed..HEAD, plan 03-11)
files_reviewed: 9
files_reviewed_list:
  - tests/harness/pc_checks.py
  - tests/harness/pc_manifest.py
  - tests/harness/pc_row1.py
  - tests/harness/pc_rows.py
  - tests/harness/pc_testutil.py
  - tests/harness/test_checks.py
  - tests/harness/test_evidence.py
  - tests/harness/test_row1_seed.py
  - tests/harness/README.md
findings:
  critical: 3
  warning: 2
  info: 2
  total: 7
status: issues_found
---

# Phase 3: Code Review Report, fourth pass

**Reviewed:** 2026-10-29T18:30:00Z
**Depth:** standard, limited to the diff since 5ef92ed (plan 03-11)
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Plan 03-11 closes most of what it set out to close. Five of the eight findings hold in full (WR-01, WR-02, WR-04, CR-02 and CR-04). CR-01 holds for every shape named, with one gap in how the working folder is tracked. CR-05 holds for the forms the third pass named and misses two nearby forms. CR-03 holds for the six forms named and then reopens through a new weakness in the way the awk reader blanks strings.

No source file was changed. All probes ran in scratch folders through `bash_mentions` and `git_mutations`, and each one was repeated against a copy of the tree at 5ef92ed to separate regressions from older behaviour. I also ran every command through the pinned allowlist model (`pc_flags.build_allowed_tools` and `pc_allowlist.is_allowed`) before calling it a bypass. Where a shell or tool effect mattered, I confirmed it with the real macOS tool. No real `claude` was started. The 289 tests of test_checks.py, test_evidence.py and test_row1_seed.py pass in about 284 seconds. The diff adds no deletion primitive outside pc_testutil.py (the one `os.rename` in test_checks.py is on a scratch repo), no home path, login or address, and touches no frozen path or filed folder. Nothing in the diff needs more than Python 3.9 stdlib.

### Verdict on the eight fixed findings

| Finding | Holds? | Proving test | What is left |
|---|---|---|---|
| CR-01 dot-dot to an approved root | Yes for the named shapes | `WriteEscapeDotDotTests` (inside, outside, expansion, link, start folder), `WriteEscapeCorpusTests.test_every_judged_or_not_run_memory_folder_command_of_the_traces_is_no_write_escape` | The working folder is modelled as if every `cd` runs in the main shell and succeeds (CR-02 below). Folders kept across Bash calls and `cd` to a substitution still read as escapes (WR-01). |
| CR-02 sed `w` operand | Yes | `SedScriptReaderTests` (all eight forms, data-only `w`, fallback). I also fuzzed several thousand generated scripts: every genuine `w` command was found, and the reader found nothing the old pattern found except text that is data. | Nothing. |
| CR-03 awk redirect after `;` or `}` | No | `AwkProgramReaderTests.test_each_redirect_after_a_semicolon_brace_or_newline_is_one_write_escape` passes for its six forms | CR-01 below reopens the closed `print >` and `system(` forms. |
| CR-04 git `-c` and kin | Yes | `GitCommandConfigTests` (four tests), `PinHeldInMemoryTests.test_every_command_running_git_configuration_ends_the_row_with_11_and_a_git_mutations_line`, the twelfth seeded case of `Harn09ReproofTests` | An attached `-ccore.x=y` is rejected by git itself ("unknown option"), so it is not a route. The environment-variable route (`GIT_CONFIG_COUNT`, `GIT_EXTERNAL_DIFF`) is the accepted leading-assignment residual and I do not count it. |
| CR-05 path attached to a short option | Partly | `WriteEscapeAttachedOptionTests` (twelve escaping and fourteen inside forms) | A cluster whose last letter takes the value, with a dot-dot value, and the `sort` gate (CR-03 below). |
| WR-01 nested walk case | Yes | `NestedRepositoryCaseTests` (four tests, including the end-to-end row with a renamed `.GIT`) | Nothing. |
| WR-02 pin in memory | Yes | `PinHeldInMemoryTests` (five tests), `test_a_rewritten_pin_file_ends_with_11_files_nothing_and_launches_no_second_stage` in test_evidence.py, the changed `Seeded.guard_setup` | Nothing. The digest is held in the run context, compared with the file before any snapshot folder or process exists, and `run_stage` is the only caller. |
| WR-04 harmless text | Yes | `ReadOnlyGateTextTests` (five tests) | Nothing for awk, sed and `[[ ]]`. The python regular-expression case stays documented. |

### Answers to the two probes

1. **False positives.** The 231 executed committed calls, the 13 `../auto-memory` commands and about 150 further shapes judge zero escapes: `../auto-memory` reads and writes from the project folder, `cd sub && ... ../x` inside one command, `cd .preclear/backend-inputs && { ... } > ../../note.md`, `LC_ALL=C awk`, `git --no-optional-locks status`, `$C` calls, quoted, unquoted and dash heredocs, `[[ ... && ... ]]`, `for` and `case` bodies, `sed w /dev/stdout`, `git log -c`. Nothing from the lists you named exits 11. Three other shapes do, and they are WR-01 and WR-02 (none appears in the corpus).
2. **Regressions.** All twelve second-pass forms, sed `w`, awk `system`, mktemp, `-f` scripts, `env -P` and `-iS`, `find -exec`, heredoc and backquote substitutions, reserved words and comments are still counted. A differential run of about 1,200 generated commands against the tree at 5ef92ed shows exactly two classes that were counted before and are not now: the awk string-blanking gap (CR-01) and the working-folder model (CR-02). Both are criticals below.

## Critical Issues

### CR-01: The awk string blanker reads a double quote inside a regular expression or comment as a string, so a following `print >` or `system(` is hidden

**File:** `tests/harness/pc_checks.py:817-837` (`_blank_strings`), used by `_awk_ok` at `tests/harness/pc_checks.py:883-890` and `_awk_redirects` at `tests/harness/pc_checks.py:877-881`
**Issue:** `_blank_strings` treats every double quote as the start of a string literal and does not know awk regular expressions or comments. A program such as `/"/ {print > o}` opens a "string" at the quote inside the regex and blanks everything up to the next quote, which hides the `print >` redirect and any `system(` call. The part then reads as read-only, so none of its words is judged. The old gate (`\bprintf?\b[^;}\n]*[>|]` and the bare word `system`) counted every one of these. All are accepted by the committed `Bash(awk:*)` rule, and each counts zero escapes now and one at 5ef92ed:

```
awk -v o=/tmp/x '/"/ {print > o}' f
awk -v o=/tmp/x '{gsub(/"/, ""); print $1 >> o}' f
awk -v c='touch /tmp/x' '/"/ {system(c)}' f
awk -v c='tee /tmp/x' '$0 ~ /"/ {print $1 | c}' f
awk -v o=/tmp/x '/a"b/ { print > o }' f
```

With the target as a literal in the program (`/"/ {print > "/tmp/x"}`), the literal-path scan lexes the same quotes wrongly and also finds nothing. The same hole opens with a comment that holds an odd quote. A regular expression with an unbalanced parenthesis inside the print statement (`print $1 ~ /\(/ > o`) also hides the redirect from the depth counter. Stripping a string makes the awk keywords harmless text, which is the purpose of WR-04, but the blanker must not turn the rest of the program into text.
**Fix:** Lex regular expressions and comments as well, and fail closed when the lexer is unsure.
```python
# in _blank_strings (or a new _awk_lex):
#  - a "/" starts a regex literal when the previous significant character is one of
#    ( , ~ ! { ; & | = < > + - * % ^ ? : or a newline or the start; blank its body up to the next unescaped "/"
#  - a "#" outside a string starts a comment to the end of the line; blank it
#  - if a quote is still open at the end of the program, return None
# in _awk_ok: when the lexer returns None, the part is not read-only.
```
Add the five forms above, a comment with an odd quote, and `awk '{gsub(/"/, ""); print $1}' f` (read-only, must stay zero) to `AwkProgramReaderTests`.

### CR-02: The working-folder model treats every `cd` as run by the main shell and as successful, so a `cd` in a pipeline, in the background, after `||`, or to a folder that does not exist lets a `..` write land outside the roots

**File:** `tests/harness/pc_checks.py:1455-1466` (`_judge`, the `cd` branch) and `tests/harness/pc_checks.py:1025-1043` (`_Tally.move`)
**Issue:** After a `cd` with a literal target inside a root, every later part of the command is resolved from the new folder. That holds only when the `cd` runs in the main shell and succeeds. The model of 5ef92ed counted every dot-dot as an escape, so these were all caught before plan 03-11 and are all missed now. Each command below is accepted by the committed `Bash(cd:*)` and `Bash(mkdir:*)` rules, each counts zero escapes, and I confirmed with bash that each one creates a folder in the run root, outside the three roots:

```
cd nosuch; mkdir ../x             # the cd fails, the shell stays in the project
cd nosuch || mkdir ../x
cd sub | cat; mkdir ../x          # a pipeline stage is a subshell
cd sub & mkdir ../x               # a background job is a subshell
```

The two with a missing folder are the likeliest in practice: a mistyped folder name followed by a write is a common slip. The parenthesised form `(cd sub); mkdir ../x` is also counted zero, but the pinned allowlist refuses a parenthesis, so it is only a rule-level gap. The folder is also resolved with `realpath` against the file system as it is after the run, so a folder the command deleted again, or never made, reads as an existing one.
**Fix:** Do not let a `cd` move the folder unless it is both certain to run in the main shell and certain to succeed. Track the working folder as a set of candidates and judge a dot-dot word against every candidate:
```python
# in _judge, cd branch: decide whether this cd certainly moved the main shell
certain = connector in (None, ";", "&&") and os.path.isdir(resolved_target)
tally.folders = {moved} if certain else tally.folders | {moved}
# a word with a dot-dot escapes when ANY folder in tally.folders resolves it outside the roots
```
`_prepass` and `split_compound` already see the separators, so the connector can be passed to `_read_unit`. At the least, mark the folder unknown (the current "unknown" state, where every dot-dot escapes) after a `cd` whose target does not exist, and after any `cd` that is joined to its neighbours by `|`, `&` or `||`. Add the four commands above to `WriteEscapeDotDotTests` as escapes.

### CR-03: Two forms of a short-option value are still unjudged: a cluster ending in the value letter with a dot-dot value, and the `sort` gate

**File:** `tests/harness/pc_checks.py:1443-1452` (`_attached_candidates`) with `tests/harness/pc_checks.py:275` (`_ATTACHED_CLUSTER`), and `tests/harness/pc_checks.py:893-896` (`_sort_ok`) with `tests/harness/pc_checks.py:771-773` (`_cluster_has`)
**Issue:** The fix for the third-pass CR-05 judges the text after the option letter, and the text from the first slash or tilde on after a cluster of one to four letters. Two cases slip through.

First, a value that starts with a dot is not found after a cluster. `-xC..` yields the candidate `C..`, which `realpath` reads as a folder named `C..` inside the project, so it resolves inside the roots. Both are accepted by `Bash(env:*)` and count zero. I confirmed that `tar -xC.. -f a.tar` extracts into the parent of the project and that `sort -ro../../x f` writes two folders up:

```
env tar -xC.. -f a.tar
env tar -xzC../.. -f a.tar
env cp -rt../.. f
env sort -ro../x f
```

Second, the `sort` gate never sees a cluster with an attached value. `_sort_ok` checks `startswith("-o")` and a cluster made only of letters, so `-ro/tmp/x` is neither, `sort` stays read-only, and none of its words is judged, whatever the path. (The single-letter `-o/tmp/x` is caught, which is what the new tests cover.)

```
env sort -ro/tmp/x f
env sort -ro~/x f
env sort -ro../x f
```

Both were also missed at 5ef92ed, so these are gaps in the fix and not regressions, but the finding they belong to was closed as "a path attached to a short option is never judged".
**Fix:** In `_attached_candidates`, offer every suffix of the letter cluster as a candidate, not only the one that starts with a slash or tilde:
```python
def _attached_candidates(word):
    if not word.startswith("-") or word.startswith("--") or len(word) <= 2:
        return []
    return [word[index:] for index in range(2, len(word))]
```
Each suffix is judged with the usual tests, so `C../..` is not enough but `../..` is found, and `o~/x` and `o/tmp/x` are found. Over-counting is the stated rule. In `_sort_ok`, return False for any word that starts with a single dash and holds an `o` before the first non-letter (`re.match(r"-[A-Za-z]*o", word)`). Add the seven forms above to `WriteEscapeAttachedOptionTests.ESCAPING`.

## Warnings

### WR-01: A folder kept across Bash calls, and a `cd` to a substitution, make a legitimate `../` write read as an escape and end the row with exit 11

**File:** `tests/harness/pc_checks.py:1016-1019` (`_Tally.begin`), `tests/harness/pc_checks.py:1025-1043` (`_Tally.move`)
**Issue:** Every command starts in the project, and a `cd` to a target with a non-literal segment leaves the folder unknown, which makes every later dot-dot an escape. Both are documented, but both give exit 11 after the money is spent for commands that are legitimate:

```
cd "$(git rev-parse --show-toplevel)" && printf hi > ../auto-memory/x
cd "$(pwd)" && printf hi > ../auto-memory/x
```

The committed traces show the model using `cd .preclear/backend-inputs && ...` (the row 2 and row 3b traces). The Bash tool keeps the folder between calls, so a following call such as `cat ../../widget_export.py > ../../note.md` works from `project/.preclear/backend-inputs`, lands inside the project, and is judged from the project and counted. None of the 231 committed calls follows a `cd` with such a use, so the corpus test cannot show it. The README names the cross-call case as a limit. It does not say that the limit fails in the false-positive direction.
**Fix:** Treat `$(pwd)` and `$(git rev-parse --show-toplevel)` as the current folder when the working folder is known. For the cross-call case, carry the last known literal folder over to the next call of the same stage, or document that the rule judges every call from the project and that a `cd` into a subfolder in one call makes a `../` in the next call an escape. Add the two commands above to the "must not escape" shapes.

### WR-02: Words that are data in a read-only command (`echo`, `printf`) are judged as paths when the command is redirected, so a note that mentions a path counts as an escape

**File:** `tests/harness/pc_checks.py:1493-1508` (`_judge`, the word loop)
**Issue:** A read-only program with an output redirect gets the label `redirect`, and the loop then judges every argument word as a possible write target, although the program only reads them. These common memory-note writes count one escape each, at 5ef92ed and now:

```
printf 'see /etc/hosts\n' > ../auto-memory/x.md
echo "path is /etc/hosts" > ../auto-memory/x
echo "wrote ~/notes" > ../auto-memory/x
printf '%s\n' "see /usr/bin/git for details" >> ../auto-memory/x.md
echo "use ../../other" > ../auto-memory/x
```

A quoted heredoc body is data and does not count, so the same note written with a heredoc passes. None of the 231 committed calls does this, and plan 03-11 did not change it, so this is not a regression. It is still a legitimate shape that ends the row with exit 11, and it is the commonest form of a note written from a one-line command.
**Fix:** When the program is read-only and the only write is a redirect, judge the redirect targets and skip the argument words (they are read or printed, never written). Keep judging every word for a program that is write-capable by itself. Add the five commands above to the "must not escape" table (IN-04 of the third pass asked for that table and it does not exist yet).

## Info

### IN-01: The new test-only rename operation is not confined to the test's own run root

**File:** `tests/harness/pc_testutil.py:195-196` (the comment), `tests/harness/pc_testutil.py:349-350` (`do_rename`)
**Issue:** The comment says the operation "may only aim at an entry of the test's own run root". The code calls `os.rename(subst(op["path"]), subst(op["to"]))` with no check. A rename onto an existing file replaces it, so this is a second unconfined removal-capable operation beside the deferred `do_remove` (third-pass IN-01). `test_checks.py` also calls `os.rename` directly in one test, on a scratch repository.
**Fix:** Resolve both paths and raise unless each is under the substituted run root, in `do_remove` and in `do_rename`.

### IN-02: A bare `git --exec-path` counts as a git mutation

**File:** `tests/harness/pc_checks.py:1783-1802` (`_git_globals`)
**Issue:** `--exec-path` without a value only prints the path and exits. The new rule counts every `--exec-path` before the verb as `config-command`, so `git --exec-path` ends the row with exit 11. A model that runs it is unlikely, and the rule is stated as "whatever the key and value", so this is a choice to confirm and not a defect.
**Fix:** Count the bare spelling only when a verb or another word follows it, or state in the README that the display form is counted too.

---

_Reviewed: 2026-10-29T18:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
