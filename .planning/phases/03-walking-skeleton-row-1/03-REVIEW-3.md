---
phase: 03-walking-skeleton-row-1
reviewed: 2026-10-29T14:55:00Z
depth: standard
pass: 3 (gap-closure diff e233020..HEAD)
files_reviewed: 12
files_reviewed_list:
  - tests/harness/pc_checks.py
  - tests/harness/pc_evidence.py
  - tests/harness/pc_manifest.py
  - tests/harness/pc_matrix.py
  - tests/harness/pc_row1.py
  - tests/harness/pc_spend.py
  - tests/harness/pc_testutil.py
  - tests/harness/test_checks.py
  - tests/harness/test_evidence.py
  - tests/harness/test_row1_seed.py
  - tests/harness/test_stages.py
  - tests/harness/README.md
findings:
  critical: 5
  warning: 4
  info: 4
  total: 13
status: issues_found
---

# Phase 3: Code Review Report, third pass

**Reviewed:** 2026-10-29T14:55:00Z
**Depth:** standard, limited to the diff since e233020 (plans 03-09 and 03-10)
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Plan 03-09 holds. The chain rule, the required pin and the unknown consistency value all work as described, and each has a test that fails without the fix. Plan 03-10 does not hold for command-line forms. The open-world rule closes every shape the second pass named, but it leaves five single-command routes that the committed allowlist permits and that file as clean, and it counts one legitimate class of writes as escapes.

No source file was changed. Every probe ran in scratch folders with a scripted event list, and no real `claude` was started. Python 3.9 syntax parses for all eleven changed code files. The diff adds no deletion primitive outside the test utilities, and no home path, login or address. The frozen paths and the filed rerun folder are untouched. The 58 tests of the new classes (chain, pin, nested repository, consistency, open-world, shell grammar, corpus, re-proof) pass in about two minutes. I did not run the whole suite.

Method for the bypass findings: each command was checked two ways. It was run through `pc_allowlist.is_allowed` with the current baseline rules from `pc_flags.build_allowed_tools`, and through `bash_mentions`. A finding is a critical only when the allowlist model accepts the command and the rule counts zero escapes. Where the effect is on the file system, I confirmed it with the real macOS tool in a scratch folder.

### Verdict on the six fixed findings

| Finding | Holds? | Proving test | What is left |
|---|---|---|---|
| CR-01 early chain is refused | Yes | `RefileChainTests` in test_evidence.py: s1 only, no s3, s3 with marker none, s2 missing, absent or foreign chain record, and `test_the_rule_itself_over_hand_built_runs`. The no-resume run still files through the live path in test_evidence.py around line 424 and in `test_the_controls_still_refile`. | Nothing. Probe 3 is answered below. |
| CR-02 write outside the roots | Partly | `WriteEscapeOpenWorldTests`, `OpenWorldRunTests`, the tenth case of `Harn09ReproofTests`. All twelve forms of the second pass are counted (checked by hand). | CR-02 to CR-05 below. |
| WR-01 literal forms | Partly | `sed w/tmp/x` (no space), `awk system(...)` and `-f` script files are counted. | The `w` operand is missed after `s` flags, after `!` and after a custom-delimiter address (CR-02 below). |
| WR-02 read-only uses | Mostly | `ShellGrammarTests` (quoted `>`, heredoc bodies, comments, reserved words) and `WriteEscapeCorpusTests`. | A dot-dot path to an approved root and some harmless script text still read as writes (CR-01, WR-04 below). |
| WR-03 pin and nested repository | Partly | `PinRequiredTests` (missing pin file is a CheckError, no process starts), `NestedRepositoryTests`, `Harn09ReproofTests` nested case. | Case-insensitive `.git` name (WR-01) and the pin read from a model-reachable file before the guard compares it (WR-02). |
| WR-04 unknown consistency | Yes | `ConsistencyUnknownTests` (`test_the_flag_gates_the_comparison`, `test_a_result_without_the_block_reads_unknown_for_that_stage_only`), the changed `CostTests` case, `UsageConsistencyTests`. | Nothing. |

### Answers to the six probes

1. **False positives.** The real traces and the known shapes pass: `../auto-memory` reads, `for`, `if`, `case` and `while` lines, comments, `LC_ALL=C awk`, `git --no-optional-locks status`, heredocs with quoted, unquoted and dash forms, `$C` calls, `env | grep`, and the helper by absolute path. Zero escapes on about 150 shapes. Writes that name an approved root through `..` do fail (CR-01).
2. **Bypasses within command-line forms.** Five remain (CR-02 to CR-05) plus run-time paths inside `python3 -c` (WR-03).
3. **Chain rule with no resume line.** Correct. The live path writes the chain record with the marker none, the stage records are s1 and s2, the expected list is the registry names without the last, and the run files. A refile of the same folder files too. A refile with s3 present and marker none is refused.
4. **Nested walk.** It does not follow links, fails closed on an unreadable folder, treats a link named `.git` as nested, and skips the top-level `.git` of any kind. It is case-sensitive, which fails on the default macOS file system (WR-01). It runs about four times per boundary (IN-02).
5. **Pin against the setup boundary.** The signature is right and no caller can omit it. A missing or malformed file after setup refuses before any process starts. The weakness is where the pin is read from (WR-02).
6. **Unknown consistency.** It reads unknown exactly when the result event has no non-empty per-call block, and also when the call's own cost could not be parsed, as before. A present block still gives yes or no.

## Critical Issues

### CR-01: A dot-dot path to an approved root counts as an escape, so legitimate writes end in exit 11

**File:** `tests/harness/pc_checks.py:410-429` (`_escapes`), used by `_judge` at `tests/harness/pc_checks.py:1103-1148`
**Issue:** `_escapes` treats every relative word with a dot-dot segment as an escape, and `_judge` applies it to every write-capable part. The run root holds `project`, `ckpt` and `auto-memory` side by side, and the model starts in `project`, so `../ckpt/...` and `../auto-memory/...` are inside the approved roots. The committed traces show the model naming the memory file as `../auto-memory/...` in nine commands across seven of them, and using `mkdir -p` and redirected writes with relative project paths in others. Each of these is allowed by the pinned allowlist model and counts at least one escape, so the row ends with exit 11 after the money is spent:

```
mkdir -p ../auto-memory
printf '%s\n' hi > ../auto-memory/note.md
echo hi >> ../auto-memory/log.md
cd ../auto-memory && mkdir -p sub
python3 -c "print(len(open('../auto-memory/x.md').read()))"
awk '/system/ {print}' ../auto-memory/MEMORY.md
awk '{printf "%s -> %d\n", $1, NR}' ../auto-memory/MEMORY.md
awk '{print ($1 > 3)}' ../auto-memory/MEMORY.md
```

The last three are reads. They count because the awk gate treats the words `system` and `close` in a regular expression, and any `>` or `|` after a print, as write-capable (WR-04). The dot-dot rule then turns the listing into an escape. The second pass had the same dot-dot rule; the open-world rule makes it reach many more commands.
**Fix:** Resolve a relative word against the project folder while the working folder is known, and test the result against the roots. `bash_mentions` already receives the roots, and the project is the first of them.
```python
def escapes(self, word):
    ...
# in _escapes, replace the final line
    if ".." in value.split("/"):
        resolved = os.path.normpath(os.path.join(project, value))
        return not any(_inside(resolved, root) for root in roots)
    return False
```
Keep the current behaviour after a `cd` or `env -C` whose target escaped (the working folder is then unknown). Add run-level tests for the shapes above and for `../wrapper/x` and `../raw/x` (still escapes).

### CR-02: The sed `w` operand is missed after `s` flags, after `!` and after a custom-delimiter address

**File:** `tests/harness/pc_checks.py:265` (`_SED_WRITE_OPERAND`), used by `_sed_ok` at line 599 and `_judge` at line 1139
**Issue:** The pattern `(?:^|[;{}/\s$0-9])[wW]\s*(\S+)` needs one of a few characters in front of the `w`. A `w` that follows a flag letter (`g`, `p`, `I`), a bang or a comma is not seen. The rule then calls the part read-only, because the only gate is that pattern. All of these are accepted by `Bash(sed -n:*)` and count zero escapes:

```
sed -n 's/a/b/gw /tmp/x' f
sed -n 's/a/b/pw /tmp/x' f
sed -n '1!w /tmp/x' f
sed -n '$!w /tmp/x' f
sed -n '/x/!w /tmp/x' f
sed -n '/x/Iw /tmp/x' f
sed -n '\,x,w /tmp/x' f
sed -n '/a/s//b/gw /tmp/x' f
```

I confirmed with the system sed that `s/a/b/gw FILE` and `1!w FILE` both create the file. `s/a/b/gw` is the common idiom. The GNU long form `--expression=w FILE` is missed for the same reason, but the macOS sed rejects it.
**Fix:** Do not anchor on the preceding character. Judge every `w` or `W` followed by optional spaces and a path-like token, and accept the over-count.
```python
_SED_WRITE_OPERAND = re.compile(r"[wW]\s*(\S+)")
```
Add the eight forms above to `ESCAPING` in `WriteEscapeTests`, and add `s/ w /x/p` to the harmless table only if the over-count is judged acceptable (it counts today).

### CR-03: The awk read-only gate stops at a semicolon or brace, so a write with one before the redirect passes as read-only

**File:** `tests/harness/pc_checks.py:268` (`_AWK_PRINT_REDIRECT`), used by `_awk_ok` at line 610
**Issue:** `\bprintf?\b[^;}\n]*[>|]` cannot cross a semicolon, a closing brace or a newline between `print` and the `>`. A string that holds one of them is enough. The part is then read-only, no word is judged, and the run files as clean:

```
awk 'BEGIN{print "a;b" > "/tmp/x"}'
awk '{print $1, "a;b" >> "/tmp/x"}' f
awk 'BEGIN{print "}" > "/tmp/x"}'
awk 'BEGIN{print 1,
 2 > "/tmp/x"}'
awk -v o=/tmp/x '{print "a;b" > o}' f
awk '{print "a;b" | "tee /tmp/x"}' f
```

I confirmed with the system awk that the first form writes the file. The inverse also holds: a `>` anywhere after a print makes the part write-capable (CR-01).
**Fix:** Do not try to parse the awk grammar. Treat any `>` or `|` that is outside a regular expression or string literal as a possible redirect, or simply treat any awk program that holds a `>`, `|` or `getline` token after stripping string literals as write-capable. The cheap fail-closed version:
```python
_AWK_REDIRECT = re.compile(r">|\|")   # applied to the program text with "..." literals blanked out
```
Add the six forms above to `ESCAPING`, and keep `{ if (length($0) > 80) print NR }` and `length>80` in the harmless table.

### CR-04: A git `-c` value that names a command is skipped, so `env git -c core.fsmonitor=... status` runs it unseen

**File:** `tests/harness/pc_checks.py:624-646` (`_git_ok`), `tests/harness/pc_checks.py:1384` (`_GIT_VALUE_OPTIONS`)
**Issue:** `_git_ok` steps over the value of `-c`, `--exec-path`, `--git-dir` and the others, then judges only the verb. `status`, `diff` and `log` are read verbs, so the part is read-only and none of its words is ever judged. The value of `-c` can be a command that git runs: `core.fsmonitor` on `status`, `diff.external` on `diff`. `Bash(env:*)` is on the committed allowlist, so `env git -c ...` is reachable. I ran both in a scratch repository, and both created their marker file. `git_mutations` counts zero for them (checked), so nothing else catches them.

```
env git -c core.fsmonitor='touch /tmp/x' status
env git -c diff.external='sh -c "touch /tmp/x"' diff
env git -c core.pager='touch /tmp/x' log
env git --exec-path=/tmp status
```

This is the harm of the first-pass CR-03 (a command named in git configuration runs) reached from the model's own call instead of the harness's.
**Fix:** The harness never needs `-c`, `--config-env` or `--exec-path` from the model. Make `_git_ok` return False when any of them appears before the verb, and make `_escapes` judge the value after the first equals sign for a word that is not a plain option (so `core.fsmonitor=/tmp/hook` counts):
```python
if word in ("-c", "--config-env", "--exec-path") or word.startswith(("--exec-path=", "--config-env=")):
    return False
```
Then give such a part the label `git-config` and count it as an escape outright, since no judgement of the value is reliable. Add the four forms above to `ESCAPING`.

### CR-05: A path attached to a short option is never judged

**File:** `tests/harness/pc_checks.py:417-421` (`_escapes`)
**Issue:** For any word that starts with a dash, `_escapes` returns False unless the word holds an equals sign. A path written directly after a short option letter (`-o/tmp/x`, `-C/tmp`) is therefore never judged. Through `env`, these are accepted and count zero:

```
env sort -o/tmp/x f
env tar -xf a.tar -C/tmp
env cc -o/tmp/x f.c
env git format-patch -o/tmp
env cp -t/tmp f
env install -t/tmp f
```

I confirmed with the system sort that `sort -o/path` writes the file. The second pass named `env sort -o OUT/x` as a closed form; only the spaced spelling is closed.
**Fix:** For a word of the form `-X<rest>` (one dash, one letter, more text), judge `<rest>` as well:
```python
if word.startswith("-") and not word.startswith("--") and len(word) > 2:
    candidates.append(word[2:])
```
Apply the same tests (tilde, `$HOME`, absolute outside the roots, dot-dot) to each candidate. Add the six forms to `ESCAPING`.

## Warnings

### WR-01: The nested repository walk is case-sensitive, and the default macOS file system is not

**File:** `tests/harness/pc_manifest.py:94-111` (`nested_git_present`)
**Issue:** The walk compares each name with the exact string `.git`. On a case-insensitive file system git opens `sub/.GIT` as the git folder of `sub`. I built a parent repository with a registered gitlink, renamed the nested folder to `.GIT`, and planted a clean filter in its config. `nested_git_present` returned False, and the harness's own status command (both hardening options, `--ignore-submodules=none`) ran the filter and created the marker. The top-level pin cannot see it. Reaching this needs several deliberate steps, and the git mutation rule still counts the `env git add` that registers the gitlink, so the run would not file as clean. The command has already run by then.
**Fix:** `if name.lower() == ".git" and not top`. Do the same for the top-level skip only if the top-level folder is looked up by exact name elsewhere (it is, so leave that one).

### WR-02: The pin is read from a file the model can reach, and it is read before the guard compares that file

**File:** `tests/harness/pc_checks.py:1337-1352` (`pinned_gitdir`), `tests/harness/pc_row1.py:422` and `tests/harness/pc_row1.py:833-834`
**Issue:** After a stage ends, `run_stage` calls `take_snapshot` and `capture_boundary_state`, which read the pin from `raw/setup.git.json`. The run record guard compares that file with its setup digest only later, in `breach_outcome` and in `compute_facts`. A model that rewrites the file (Write tool, or a Bash write that CR-02 to CR-05 miss) with the digest of a git folder it has changed gets its change accepted, and the harness's git call runs the planted command before the guard reports the rewrite. A removed file is now handled; a replaced file is not. The README states the pin as "taken at setup", which a reader will take as tamper-proof.
**Fix:** Keep the pin in memory. `run_row` has the state it just wrote at setup, so pass the digest to `take_snapshot` and `capture_boundary_state` instead of re-reading it. If the file must stay the source, compare its sha256 with the one in the setup guard first and raise `CheckError` on a mismatch.

### WR-03: Interpreter code that builds its path at run time is allowed by the allowlist and files as clean

**File:** `tests/harness/pc_checks.py:432-440` (`_path_like`), `tests/harness/pc_checks.py:1103-1148` (`_judge`), `tests/harness/README.md` (the "Known limits" paragraph)
**Issue:** `Bash(python3 -c:*)` is on the committed allowlist. The rule judges only literals that read as a path. These count zero escapes:

```
python3 -c "import os; os.chdir('/'); open('x','w').write('1')"
python3 -c "import os; os.chdir('..'); open('x','w').write('1')"
python3 -c "open('/'+'tmp/x','w')"   (a literal of one slash is not a path)
python3 -c "import tempfile; tempfile.NamedTemporaryFile(delete=False)"
python3 -c "import os; os.system('touch ' + chr(47) + 'tmp/x')"
python3 -c "exec(open('s.py').read())"
```

The README names "code that builds its path at run time" as a known limit, but the disposition lists only the script-file case as the accepted residual, and says the three findings are "closed for command-line forms". These are command-line forms. The relative-write-after-chdir case can also land inside the run root but outside the three roots, where the snapshot diff would catch it; a chdir to `/` or a temp file lands outside the run root, where nothing looks.
**Fix:** Either remove `python3 -c` from the row's allowlist, or fail closed: count any `python3 -c` text that holds a write-capable token (`open(` with a mode other than `r`, `chdir`, `system`, `popen`, `subprocess`, `shutil`, `tempfile`, `mkstemp`, `mktemp`, `os.symlink`, `exec`, `eval`, `__import__`, `pathlib` write calls) as an escape. Add the six forms as tests, and put the residual into the disposition if the owner accepts it.

### WR-04: Harmless text turns read-only commands into write-capable ones, and `[[ a && b ]]` is split into two parts

**File:** `tests/harness/pc_checks.py:267` (`_AWK_UNSAFE`), `tests/harness/pc_checks.py:268`, `tests/harness/pc_checks.py:265`, `tests/harness/pc_checks.py:1154` (`split_compound` use in `_read_unit`)
**Issue:** Four shapes that the README promises "stay mentions" become write-capable, and then count whenever one operand reads as an escape (CR-01 or an outside absolute path):
- an awk program that holds the word `system` or `close` inside a regular expression or string, or a `>` or `|` inside a string after a print (`print "a -> b"`);
- a sed script such as `s/ w /x/p`, which the `w` pattern reads as a write to `/x/p`;
- a python regular expression such as `r'/[a-z]+/'` (documented);
- `[[ -f ../auto-memory/x && -s ../auto-memory/x ]]`, which the part splitter cuts at the `&&` inside the brackets. The second half starts with `-s` and is judged as a program named `-s`.
**Fix:** Blank string and regular-expression literals before the awk keyword and redirect tests (this also helps CR-03). Treat a part that starts with `[[` as one part until the matching `]]`. With CR-01 fixed, the practical effect of the rest drops to the outside-absolute-path case.

## Info

### IN-01: The test-only remove operation is not confined to the test's own run root

**File:** `tests/harness/pc_testutil.py:344` (`do_remove`), `tests/harness/pc_testutil.py:194` (the comment)
**Issue:** The comment says the operation "may only aim at a file of the test's own run root". The code calls `os.remove(subst(op["path"]))` with no check, in a script that the tests run as a subprocess. Today the only callers are the two seed helpers, which use the `$RUN` token.
**Fix:** Resolve the path and refuse (raise) unless it is under the substituted run root.

### IN-02: The nested walk runs about four times per boundary

**File:** `tests/harness/pc_checks.py:1315` (`git_state`), `tests/harness/pc_manifest.py:159` (`capture_git_status`), `tests/harness/pc_row1.py:430` (`take_snapshot`), `tests/harness/pc_checks.py:1365` (`capture_boundary_state`)
**Issue:** The snapshot calls `capture_git_status` (one walk), then the state capture calls `git_state` (one walk) and, through it, `capture_git_status` again (a second). The cost scales with the size of the working tree, which the model can grow. Performance is outside the scope of this review, but the repeated walks also leave a small gap in time between the check and the git call.
**Fix:** Walk once per boundary and pass the result down, or cache it per boundary.

### IN-03: The chain rule assumes only the last registry stage is conditional

**File:** `tests/harness/pc_evidence.py:1076` (`_chain_incomplete`)
**Issue:** `expected = names if found else names[:-1]` is right for row 1 (s3 is the conditional stage and the last). It would be wrong silently for a row whose conditional stage is elsewhere. The registry entry carries the stage kinds.
**Fix:** Derive the optional stage from the spec (the `resume` kind) instead of slicing.

### IN-04: The corpus test cannot see the shapes that matter most

**File:** `tests/harness/test_checks.py:1786-1845` (`WriteEscapeCorpusTests`)
**Issue:** The corpus holds only the commands the model happened to run: no `python3`, no `sed` with a write, no relative write to an approved root, and `env` only as a pipe source. Zero escapes over it shows the rule is not noisy on those shapes, not that it is right on others. The committed traces also hold sanitised paths, and only `<repo>/<run>` and `<run>` are made concrete, so other placeholder paths are never judged as absolute.
**Fix:** Keep the corpus test and add a table of "must not escape" shapes (the first section of CR-01, the awk and sed read forms) beside the "must escape" table, so each side is pinned independently of what the model has done so far.

---

_Reviewed: 2026-10-29T14:55:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
