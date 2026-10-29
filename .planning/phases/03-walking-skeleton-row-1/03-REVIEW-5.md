---
phase: 03-walking-skeleton-row-1
reviewed: 2026-10-29T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - tests/harness/pc_allowlist.py
  - tests/harness/pc_checks.py
  - tests/harness/test_checks.py
  - tests/harness/test_evidence.py
  - tests/harness/README.md
findings:
  critical: 0
  warning: 6
  info: 0
  total: 6
status: issues_found
---

# Phase 3: Code Review Report (fifth pass, closing)

**Reviewed:** 2026-10-29
**Depth:** standard (diff 6d3fe56..HEAD, with an old-versus-new differential run)
**Files Reviewed:** 5
**Status:** issues_found (no critical)

## Summary

Closing pass on gap plan 03-12 (commits 7856600 and 7652b40). All four fixed findings hold. No finding meets the critical bar set for this pass. Six warnings are recorded for Phase 4.

How the critical bar was checked, by running the old tree (6d3fe56) and the new tree (HEAD) side by side on the same inputs:

| Check | Result |
|---|---|
| All 348 committed Bash calls (231 judged, 13 `../auto-memory` commands included), write escapes, write-capable listing and git mutations, old versus new | 0 differences; 0 escapes over the 231 judged; 0 over the memory-folder commands |
| `split_compound` old versus new, over every corpus command, every string in `tests/harness/data` and `replay-cases.json`, and 60,000 random quote, separator and paren strings | 0 differences (61,527 inputs); the connected splitter's parts equal `split_compound` on all of them |
| `cd "$(git rev-parse --show-toplevel)" && printf hi > ../auto-memory/x`, and the `$(pwd)` and newline variants | 0 escapes at HEAD (1 at 6d3fe56); run-level row passes |
| 2,231 generated cd, separator, writer, awk, sort and option-cluster commands, old versus new | 98 forms counted at 6d3fe56 are no longer counted, all of them a cd to an expansion (WR-02 below); every other change is a new count |
| Test run, `python3 -B -m unittest test_checks test_evidence test_allowlist` | 340 tests, OK |
| `ast.parse` with feature_version 3.9, system Python 3.9.6 | all four .py files parse; imports are stdlib only |
| Deletion primitives (`shutil`, `os.remove`, `unlink`, `rmtree`, `rmdir`, `rename`) in added lines | none |
| Paths, logins, hosts, keys in added lines | none |
| Frozen paths and filed evidence (`SKILL.md`, `references`, `tests/fixtures`, `tests/evidence`, `runs`, `scripts`) since 6d3fe56 | no diff; the five harness files are the only source files changed |

## Verdict on the four fixed findings

| Finding | Holds | Proving test | What I ran |
|---|---|---|---|
| CR-01 awk quote hides a statement | Yes | `AwkRawProgramTests.test_each_quote_hidden_statement_is_one_escape_under_awk` (11 forms), `..._is_listed_under_awk`, `test_the_harmless_string_forms_stay_read_only_and_unlisted`; run level: four forms in `OpenWorldRunTests` exit 11 | The five forms, the comment form, the literal-target form and `print $1 ~ /\(/ > o` from REVIEW-4: 0 at 6d3fe56, 1 at HEAD. `awk '{gsub(/"/, ""); print $1}' f` stays 0. The fix only adds views, so it cannot uncount an old form. |
| CR-02 every cd treated as certain | Yes | `WorkingFolderCertaintyTests.test_every_cd_that_is_not_certain_leaves_a_later_dot_dot_word_an_escape` (18 forms), `test_a_certain_cd_to_an_existing_folder_moves_the_folder` (11 forms), `test_the_folder_is_never_carried_from_one_bash_call_to_the_next`; run level: three rows | The four REVIEW-4 forms (`cd nosuch; mkdir ../x`, `|| `, `| cat;`, `&`) and `(cd sub); mkdir ../x`: 0 at 6d3fe56, 1 at HEAD. The set of cds that move the folder is a subset of the old set, so nothing is uncounted by this part. |
| CR-03 cluster values and the sort gate | Yes | `AttachedClusterValueTests.test_a_value_after_the_value_letter_of_a_cluster_is_one_escape_under_its_label`, `test_a_tilde_value_after_a_sort_cluster_is_one_escape`, `test_relative_values_and_read_only_sort_forms_are_zero`, `test_the_sort_cluster_holding_o_is_listed_and_the_read_only_forms_are_not` | `env tar -xC..`, `-xzC../..`, `cp -rt../..`, `sort -ro../x`, `sort -ro/tmp/x`, `sort -ro~/x`: 0 at 6d3fe56, 1 at HEAD. New sort pattern is a superset of the old cluster test; the new candidate list contains every old candidate. |
| WR-01 cd to a substitution, folder across calls | Yes for the substitution half; the cross-call half is documented only (see WR-06) | `WorkingFolderCertaintyTests.test_a_cd_to_an_expansion_resolves_a_dot_dot_word_against_the_project`, `test_the_two_unknown_states_in_one_place`; run level: the `git rev-parse --show-toplevel` row in `OpenWorldRunTests` | Both REVIEW-4 commands now count 0; `cd $d && mkdir ../x` still counts 1. The cross-call limit is pinned by `test_the_folder_is_never_carried_from_one_bash_call_to_the_next` and named in the README. |

## Warnings

### WR-01: A literal cd that is not joined by a double ampersand, or sits in a group, if or loop, now ends a legitimate `../auto-memory` write with exit 11

**File:** `tests/harness/pc_checks.py:1660-1663` (the `certain` test), `tests/harness/pc_checks.py:1631-1640` (the compound flag)
**Issue:** The rule is strictly more conservative by design (03-REVIEW-4-DISPOSITION.md), but the false-positive direction is wider than the plan's corpus shows. These commands write inside the memory folder in a real shell, counted 0 at 6d3fe56 and count 1 at HEAD, so each would end a row with exit 11:

```
cd /abs/project; printf hi > ../auto-memory/x
cd /abs/project
printf hi > ../auto-memory/x
(cd /abs/project && printf hi > ../auto-memory/x)
if cd /abs/project; then printf hi > ../auto-memory/x; fi
for f in a; do cd /abs/project && printf hi > ../auto-memory/$f; done
```

None is among the 231 judged commands, the 13 memory-folder commands or the named skill shapes, so this is not critical under this pass's rule. The `&&` form `cd /abs/project && printf ... ../auto-memory/x` and the substitution form are fine. The subshell case is worst: the cd and the write are in the same subshell, so the working folder is certain, but the compound flag is set by the opening parenthesis before the cd is read.
**Fix:** Track the compound flag per nesting level. A cd inside a group is certain for the rest of that group when it is `&&`-joined and its group is not backgrounded; reset the folder when the group closes. For `;` and newline, treat the cd as certain when the target exists and the part is not in a pipeline or background list, since a `;` cd that succeeds moves the main shell. The failure case (`cd nosuch; mkdir ../x`) is already covered by the existence test. Add the five forms above to `WorkingFolderCertaintyTests.CERTAIN`.

### WR-02: A cd to an expansion no longer counts a `../` write that lands outside the roots (a form counted at 6d3fe56)

**File:** `tests/harness/pc_checks.py:1117` (`move`, the `_LOOSE` return), `tests/harness/pc_checks.py:1096-1098` (`folder`), `tests/harness/pc_checks.py:1587` (the `mktemp` call)
**Issue:** By the letter of the pass rule (b) this is a regression: 98 of the 2,231 battery forms counted at 6d3fe56 and count 0 now, every one a cd or `env -C` to an expansion followed by a write through a dot-dot path that resolves inside the roots from the project, for example `cd $d && mkdir ../auto-memory/x` and `env -C $d mkdir ../auto-memory/x`. If the variable holds a folder outside the project, the write lands outside. I rate it a warning and not critical because 03-REVIEW-4-DISPOSITION.md chose this trade for WR-01 and the README names it as the residual. Flagged so the lead can overrule the rating.
**Fix:** None needed for this phase. For Phase 4, resolve `$(git rev-parse --show-toplevel)`, `$(pwd)` and `$PWD` to the known folder, and keep every other expansion strict. That keeps the two legitimate shapes at 0 and returns every other expansion to counting.

### WR-03: An awk regular expression that holds a semicolon or a closing brace hides a following redirect (not counted at 6d3fe56 either)

**File:** `tests/harness/pc_checks.py:908-944` (`_awk_statement_redirects`)
**Issue:** The statement reader ends a statement at the first semicolon or closing brace at depth zero in the blanked text. A regular expression that holds one of them ends the statement early, so the redirect after it is not seen. There is no double quote, so the raw view is not triggered. Both count 0 at 6d3fe56 and at HEAD:

```
awk -v o=OUT/x '{print $1 ~ /;/ > o}' f
awk -v o=OUT/x '{print $1 ~ /}/ > o}' f
```

Not a regression and not a corpus form, so a warning for Phase 4.
**Fix:** Blank regex literals (a slash that follows `~`, `(`, `,`, `!`, `{`, `;`, `&`, `|` or a line start, to the next unescaped slash) in the text the statement reader sees, and fail closed to the raw view when a slash is present in a print statement.

### WR-04: A short-option cluster of five or more letters before a slash value hides the value

**File:** `tests/harness/pc_checks.py:1529-1546` (`_attached_candidates`)
**Issue:** The four-letter rule keeps `-Iinclude/x` relative but drops any slash or tilde value after five or more option letters. `tar -xzvpC/etc -f a.tar` extracts into `/etc`, counts 0 at 6d3fe56 and at HEAD. The same value after four letters (`tar -xzvC/etc`) counts 1. The dot-dot form `tar -xzvpC.. -f a.tar` now counts 1.
**Fix:** Offer the slash and tilde candidates for any run length, and over-count `-Iinclude/x` (the README already names the ambiguity), or keep the rule and add the five-letter form to the README's named limits.

### WR-05: A cd judged certain can still fail or not run, so a later `../` write after `||` or a bad cd is judged from the wrong folder

**File:** `tests/harness/pc_checks.py:1104-1134` (`move`, the existence test), `tests/harness/pc_checks.py:1660-1662`
**Issue:** The existence test reads the folder when the command is judged, and the certain test looks only at the next and previous separator. Both count 0 at 6d3fe56 and at HEAD:

```
cd sub && mkdir ../x || mkdir ../y     # if the cd fails, ../y is written from the project
cd sub extra && mkdir ../x             # cd with two operands fails in bash; only the first operand is read
```

The README names the `||` form for the cd's own list; the two-operand form and the existence timing (a folder made later, or removed, between the run and the judging) are not named.
**Fix:** Treat a cd as uncertain when any `||` follows it in the same and-or list, and when it has more than one operand. Name the existence timing in the README next to the cross-call limit.

### WR-06: A folder kept by a cd in one Bash call makes a legitimate `../` write in the next call read as an escape (carried from the fourth pass, fixed by documentation only)

**File:** `tests/harness/pc_checks.py:1091-1094` (`begin`), `tests/harness/README.md` (the "every Bash call is judged from the project folder" sentence)
**Issue:** The committed row 2 and row 3b traces use `cd .preclear/backend-inputs && ...`. The Bash tool keeps that folder for the next call, so a later call such as `cat ../../widget_export.py > ../../note.md` writes inside the project, but each call is judged from the project and `../../note.md` counts 1. No committed call has this follow-up, so the corpus cannot show it. The behaviour is unchanged by plan 03-12 and the README now says the error can go either way, which is what the fourth pass offered as the alternative fix.
**Fix:** Carry the last literal folder of the previous call of the same stage into the next call as the start folder, judged at the same existence test, so the false-positive direction closes while the false-negative direction stays as documented. Until then, keep the README sentence.

---

_Reviewed: 2026-10-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
