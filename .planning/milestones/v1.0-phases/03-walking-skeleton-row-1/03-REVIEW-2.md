---
phase: 03-walking-skeleton-row-1
reviewed: 2026-10-29T12:30:00Z
depth: standard
pass: 2 (gap-closure diff 48e1cd2..HEAD)
files_reviewed: 11
files_reviewed_list:
  - tests/harness/pc_checks.py
  - tests/harness/pc_evidence.py
  - tests/harness/pc_manifest.py
  - tests/harness/pc_promote.py
  - tests/harness/pc_row1.py
  - tests/harness/pc_testutil.py
  - tests/harness/test_checks.py
  - tests/harness/test_evidence.py
  - tests/harness/test_promote.py
  - tests/harness/test_row1_seed.py
  - tests/harness/README.md
findings:
  critical: 2
  warning: 4
  info: 4
  total: 10
status: issues_found
---

# Phase 3: Code Review Report, second pass

**Reviewed:** 2026-10-29T12:30:00Z
**Depth:** standard, limited to the gap-closure diff (`git diff 48e1cd2 HEAD`)
**Files Reviewed:** 11
**Status:** issues_found

## Summary

The zero-token suite passes (1190 tests, 3 skipped). Python 3.9 syntax parses for every changed source file, no deletion primitive was added outside the test utilities (the tests use `os.rename` and restore the name), and the diff holds no home path, host, login or address. The frozen paths and the filed rerun folder are untouched. No source file was changed by this review. All probes ran against temporary folders and scripted data.

Five of the eight "fixed" findings hold in the form the first pass described. Three hold only for the exact shapes the new tests cover:

- **CR-01** holds for a stage that ended badly, but `--refile` still files a run that stopped early (new CR-01 below).
- **CR-02** holds for the listed write programs and for redirections, but the label list is open-ended and `env` is allowed (new CR-02 and WR-01 below).
- **CR-03** holds for a command planted in the project's own git configuration, but a nested repository still runs one (new WR-03 below).

The write-escape rule produced no false positive on the twelve Bash commands of the filed baseline (three trace files, including the six the permission layer denied) and none on any of the 248 executed Bash commands in all committed full traces. Two heredoc commands in those traces give one unparsed part each, which is not an escape. The risk of a false exit 11 is real but latent (WR-02).

### Verdict on the eight fixed findings

| First-pass ID | Holds? | Proof in the suite | What is left |
|---|---|---|---|
| CR-01 refile of a refused run | Partly | `RefileCleanRunTests` in test_evidence.py: error subtype, max turns, error flag, terminal reason, process exit, failed isolation assertion, missing keys, stop value. A clean run and a run with no s3 still refile. | An interrupted chain is filed with exit 0 (CR-01 below). |
| CR-02 Bash write outside the roots | Partly | `WriteEscapeTests`, `WriteEscapeRunTests` in test_checks.py; `Harn09ReproofTests` cases "bash write outside, really written" and "bash expansion-form write" | Unlabeled programs, command-string literals, `sed w<path>` (CR-02, WR-01 below). |
| CR-03 planted git configuration | Partly | `GitHardeningTests`, `PlantedConfigTracerTests`; `Harn09ReproofTests` cases "planted fsmonitor command" and "planted clean filter" (marker never created) | Nested repository, pin file removal (WR-03 below). |
| WR-01 invisible run-root places | Yes, for rewrites | `RunRecordGuardTests`, `RunRecordRunTests`; "rewritten hook log" case | An append to the hook log stays invisible, as the README says (IN-04). |
| WR-02 status question | Yes | `StatusFactTests`; the scripted claude now merges the two streams (`stderr=subprocess.STDOUT` in `pc_testutil.py`). The real baseline result has the brand line first and `session e125001c ...` second, so the new rule gives yes on the real shape. | None. |
| WR-03 deny entries | Yes | `DenyEntriesRequiredTests`, `DenyEntriesContractTests`. Every production call of `promote` passes `deny_entries`: `file_row` and `file_skipped` refuse None with exit 15 before anything is read, and the command line opts out explicitly. | An empty list is still accepted (IN-02). |
| WR-05 fail-open inputs | Yes | `FailOpenInputTests`: an unreadable memory path and a missing git state file now raise a read error that ends in exit 11. | A run root made before this change has no guard files and cannot be refiled (expected). |
| IN-01 cumulative check in usage.txt | Yes, with a caveat | `UsageConsistencyTests`. The lines and the one warning per stage render as described. | The yes is vacuous when the stream lacks the per-call cost block (WR-04). |

### Answers to the seven probes

1. **Write-escape rule.** False positives on the real traces: none. Bypasses that the rule closes: leading assignments, `env -C`, `env --chdir`, `env -S`, quoted and attached `>` targets, `2>&1` and `/dev/null` (not escapes), `sed 's/a/b/w /x'`, `cd` then write, subshell and brace groups, tilde, `$HOME`, dot-dot. Bypasses that remain are in CR-02 and WR-01. False positives that remain are in WR-02.
2. **Gitdir pin on legitimate state.** It does not fire. Over thirty files with fresh mtimes, a plain `git status`, `diff`, `log`, `show`, `ls-files`, `branch`, `worktree list`, `rev-parse` and `symbolic-ref` left the digest unchanged, because the digest has no timestamps and leaves out `index` and `index.lock`. The one exception is a user whose own git configuration turns on the built-in file system monitor (IN-03).
3. **Run-root guard on the harness's own writes.** It does not fire. The driver path with three stages passes, and I traced each window: the prompt, stdout, stderr, git state and record of the stage, the previous guard, and the chain record in the s3 window are all allowed. A record written before the guard is part of what the next boundary compares.
4. **`_unfileable`.** It refuses every non-clean record shape I tried, but not an incomplete chain (CR-01).
5. **`promote` and None.** It raises a `ValueError` naming the keyword. `file_row` and `file_skipped` both guard None before calling it, so no production caller reaches the raise.
6. **Status scan and merged-stream fake.** Correct. Boundary tests cover the fifth line (yes), the sixth line (no), an indented line (no) and the bare word (no).
7. **usage.txt lines.** Format and warning are right. The yes can be vacuous (WR-04).

## Critical Issues

### CR-01: `--refile` files a run whose chain stopped early

**File:** `tests/harness/pc_evidence.py:1035-1047`, `tests/harness/pc_matrix.py:559-580`
**Issue:** `_unfileable` loops over the stage records that exist and requires each to be clean. It never asks whether the chain is complete. `_usable_run_folder` treats any folder with a run record as "a finished row 1 run folder", and that record is written at setup. A run that was interrupted after a clean s1 (a crash, a power cut, an interrupt, a harness error after the paid call) has one clean stage record and passes both checks.

Reproduced with the scripted claude. I built a normal run, then removed everything the second and third stages wrote:

| Run root content | `--refile` result |
|---|---|
| Only s1 (clean) | exit 0, 39 files filed, usage.txt shows one stage and a row total of the first call only |
| s1 and s2, chain record says a resume line was found, s3 missing | exit 0, 53 files filed |

The live path files only after s2 has run, and runs s3 whenever s2 printed a resume line. So this is the first-pass CR-01 again: `--refile` files something the live path would not. The one-attempt ledger blocks a rerun after an interrupted run, which makes `--refile` the natural next step. Filing is not undoable (the destination name is consumed and no deletion primitive exists), and the folder reads as a baseline. The README says a refile is refused "if the folder is not a finished run folder", which is not true here.
**Fix:** Require the chain the registry defines before anything is staged.
```python
def _unfileable(data: RunData) -> Optional[str]:
    if not data.stages:
        return MESSAGE_UNREADABLE
    names = [stage.name for stage in data.stages]
    expected = ["s1", "s2"]
    if data.chain is None or names[:2] != expected:
        return MESSAGE_STAGE_NOT_CLEAN          # chain incomplete
    wants_s3 = data.chain.get("marker") == _row1().MARKER_FOUND
    if names != expected + (["s3"] if wants_s3 else []):
        return MESSAGE_STAGE_NOT_CLEAN
    ...existing per-stage checks...
```
Give the incomplete case its own fixed text if wanted ("a stage did not run"). Add tests for: s1 only, s1 and s2 with a found marker but no s3, s3 present with marker none, and s2 missing.

### CR-02: The write-escape rule only sees programs on a fixed list, and `env` is allowed

**File:** `tests/harness/pc_checks.py:354-381` (`_write_program`), `tests/harness/pc_checks.py:590-596` (`if label is None and not redirects: continue`)
**Issue:** An executed part counts as a write escape only when `_write_program` labels it or it carries a redirection. The committed allowlist contains `Bash(env:*)`, and the pinned allowlist model (`pc_allowlist.is_allowed`) accepts `env` followed by any program. So any program that is not on the label list can be run through `env`, names an outside path as a plain word, and is never counted. I ran each of these against the committed `tools.txt` rules. Every one is allowed, and every one gives zero escapes:

```
env sh -c 'touch /tmp/x'
env bash -c 'echo hi > /tmp/x'
env rm /tmp/x
env ln -s /etc /tmp/x
env tar -xf a.tar -C /tmp
env curl -o /tmp/x http://h
env sort -o /tmp/x f
env xargs touch /tmp/x
env python3 -Bc "open('/tmp/x','w')"
env -P /usr/bin mkdir /tmp/x
env -iS 'touch /tmp/x'
find . -exec sh -c 'echo hi > /tmp/x' \;
```

`env -P` and `env -a` take an argument that the option parser does not know, so the argument is read as the program and the real program is hidden. `-iS` is a combined flag the parser misses. The `bash_mentions` docstring and the README name the "pinned allowlist" as the first net, but that net has this hole by construction. The effect is the first-pass CR-02: a write outside the approved roots files with exit 0 and `bash-write-escapes: 0` in the evidence, which then reads as proof of isolation.
**Fix:** Stop relying on a closed list of write programs. Either of these closes it:
- Treat every executed part whose program is not on a short read-only list (`ls`, `cat`, `head`, `wc`, `shasum`, `realpath`, `pwd`, `date`, `printf` without a redirect, `find` without an output or exec flag, `sed -n` without a write, the git read verbs, the helper) as write-capable, and apply `_escapes` to its words.
- Or remove `env` from the model-facing allowlist, or allow only `env` with the exact options the skill needs.

Also make `_strip_prefix` fail closed: an `env` option it does not recognise should make the whole part count as unparsed, and unparsed parts that contain an escaping word should count as an escape. Add run-level tests for `env sh -c`, `env rm`, `env -P`, `env -iS` and `find -exec sh -c`.

## Warnings

### WR-01: Labelled programs still miss two literal forms

**File:** `tests/harness/pc_checks.py:264` (`_SED_WRITE_OPERAND`), `tests/harness/pc_checks.py:490-507` (`_script_literals`), `tests/harness/pc_checks.py:411-419` (`_path_like`)
**Issue:** Inside programs the rule does label, these writes to a plain outside path give zero escapes and are all allowed by the committed rules:
- `sed -n 'w/tmp/x' f` writes the file on the macOS sed (I confirmed it creates the file). The operand pattern requires whitespace after `w`.
- `awk 'BEGIN{system("touch /tmp/x")}'` and `python3 -c "import os; os.system('touch /tmp/x')"`. A string literal with whitespace is never judged as a path, so a command string with a literal outside path passes.
- `sed -n -f script f`, where the script file was written earlier with the Write tool, is not read at all. (GNU sed also takes `--expression=`; the macOS sed rejects it.)
**Fix:** Accept zero whitespace after `w` (`[wW]\s*(\S+)`). Judge each whitespace-separated token inside a script string literal with `_escapes`, not only literals that are themselves a bare path. Count `-f` and `-e` scripts for `sed` and `awk` with an unreadable body as unparsed, and fail closed on them.

### WR-02: Read-only uses are counted as writes, so a clean run can still end in exit 11

**File:** `tests/harness/pc_checks.py:354-381`, `tests/harness/pc_checks.py:510-544` (`_redirections`), `tests/harness/pc_checks.py:547-600` (`bash_mentions`)
**Issue:** The README promises that read-only commands "stay mentions and decide nothing". Four shapes break that. I reproduced each against the committed rules:
- `awk` and `python3 -c` are labelled write-capable for every use. `awk '{print}' /etc/hosts`, `awk '{print}' ../x`, `python3 -c "print(open('/etc/hosts').read())"` and a script with `re.findall(r'/[a-z]+/', 'x')` each count one escape.
- A quoted `>` word becomes a redirection after `shlex` removes the quotes. `awk -F '>' '{print $1}' /etc/hosts`, `cat '>' /etc/hosts` and `printf '%s\n' '>' /etc/hosts` each count one escape.
- `find /usr -name x -exec ls {} \;` is labelled `find-output`, so the read-only listing counts.
- Heredoc bodies are split on newlines and each line is judged as its own command. `cat > f <<'EOF'` with the body line `mkdir /tmp/x` counts one escape although nothing runs it. The model writes checkpoint text through heredocs in the committed traces (the row 3c and row 7 commands), so every line of a checkpoint body is judged as a command.

None of these shapes appears in the 248 committed executed commands, so the next real run is probably safe. When one does appear, the run ends in exit 11 after the money is spent, and the destination name is not consumed, but the ledger blocks a rerun.
**Fix:** Keep the quote information: judge redirections on the raw part text before `shlex`, not on unquoted words. Cut a heredoc body out of the command before it is split (everything after the line that starts `<<DELIM` up to the closing delimiter). For `awk` and `python3 -c`, count an escape only for a redirection or a write call in the script, not for a read operand. Ignore `-exec` of a command that is not itself write-labelled.

### WR-03: The git pin and the hardening do not cover a nested repository, and the pin is optional by absence

**File:** `tests/harness/pc_manifest.py:71` (`--ignore-submodules=none`), `tests/harness/pc_manifest.py:118-135`, `tests/harness/pc_checks.py:714-722` (`pinned_gitdir`), `tests/harness/pc_checks.py:675-712` (`git_state`)
**Issue:** The pin compares only the top-level `.git` folder without its index. The harness's status call uses `--ignore-submodules=none`, so git enters any gitlink in the index and reads that nested repository's own configuration. The index is left out of the digest, so registering a gitlink (`git update-index --add --cacheinfo 160000,<sha>,sub`) changes nothing the pin sees. I reproduced this against the real functions: a nested repo with a `filter.clean` command in its config, a `.gitattributes` selecting it and a touched file. The top-level digest was unchanged, `capture_git_status` ran with the pin and the hardening, and the planted command created its marker file. The first-pass CR-03 was exactly that the harness runs a command the model plants. A `core.fsmonitor` value in the nested config is stopped, because the command line setting is inherited by the child git.

The route needs several steps, and under the committed allowlist only `env git ...` or hand-written files reach it, so I rate it a warning. Separately, `pinned_gitdir` returns None when `raw/setup.git.json` does not exist, and every caller then runs git unpinned. A missing pin file should refuse, not unpin. The file is in the part of the run root that the model can reach through any write route in CR-02.
**Fix:** Before any harness git call, walk the project once and refuse (as the pin does) when any entry named `.git` exists below the top level. Or replace `--ignore-submodules=none` with `--ignore-submodules=all` for the harness's own calls and keep the old form only if SKILL.md needs it for parity. Make `pinned_gitdir` raise a read error for every boundary after setup when the file is missing, and take the setup boundary as an explicit argument.

### WR-04: The cumulative-consistent line is vacuous when the stream has no per-call cost block

**File:** `tests/harness/pc_row1.py:723-728` (`_consistent`), `tests/harness/pc_spend.py:443-466` (`call_cost`)
**Issue:** `call_cost` takes the call's own cost from `model_usage_since_last_result`. When that block is missing it falls back to the total minus the previous total. `_consistent` then checks that previous plus delta equals the total, which is true by construction, so the line prints `yes` without comparing two independent numbers. IN-01 asked for this check so that a reviewer could see the cumulative claim hold. A tool version that drops the block would print `yes` for every stage.
**Fix:** Have `call_cost` return where the delta came from, or have `_consistent` receive that flag, and record `unknown` when the delta was derived from the totals. Add a test with a result that lacks the block and assert `unknown`.

## Info

### IN-01: Formatting slip in `run_row`

**File:** `tests/harness/pc_row1.py:1131`
**Issue:** `entry =pc_rows.find_entry(...)` has no space after the equals sign. It was introduced by the gap-closure commit.
**Fix:** `entry = pc_rows.find_entry(...)`.

### IN-02: An empty list of deny entries is accepted, and the guard test checks only a name

**File:** `tests/harness/pc_evidence.py:1191`, `tests/harness/pc_promote.py:150`, `tests/harness/test_promote.py:429-449`
**Issue:** Both guards test `is None`. `file_row(ctx._replace(deny_entries=[]))` and `promote(..., deny_entries=[])` run the gate with no entries, so the login is again not checked. The new test says an explicit empty list is accepted. The AST test only checks that a keyword called `deny_entries` is present, so `deny_entries=None` in a production call would pass it.
**Fix:** Refuse an empty list in `file_row` and `file_skipped` (the sanitizer never returns one). In the AST test, reject a literal `None` or `[]` value.

### IN-03: The git folder digest sees the built-in file system monitor's files

**File:** `tests/harness/pc_manifest.py:83-96` (`gitdir_digest`)
**Issue:** I ran `git -c core.fsmonitor=true status` in a scratch repo. The digest changed because the daemon adds `fsmonitor--daemon`, its socket and a cookie folder inside `.git`. The model's own git calls use the operator's global git configuration, so a user who has that setting turns every run into a "git mutation", and now also stops the harness's git calls. The digest rule is older than this diff, but the pin gives it a second effect. The global configuration on this machine does not set it.
**Fix:** Leave `fsmonitor--daemon*` out of the digest, or give the model's process `GIT_CONFIG_GLOBAL` pointing at the null device in `build_env`. Either needs a decision from the owner of the isolation contract.

### IN-04: The hook log guard cannot see same-window changes, and the first stage has no baseline

**File:** `tests/harness/pc_checks.py:1112-1128` (`_hooklog_state`), `tests/harness/pc_checks.py:1180-1196` (`_window_names`)
**Issue:** The README admits that an appended well-formed line looks like the hook's own append. The consequence is wider than the README says. At the first stage the recorded size is 0, so a full replacement of the log also counts as growth. A file created in a window (the stage's own prompt, and the chain record in the s3 window) is compared with nothing until the next guard, and there is no guard after the last stage for files created after it. The write routes into these files are the trace (Write and Edit tools, which count) and CR-02 (Bash, which does not), so this is only as strong as the Bash rule.
**Fix:** Document the first-stage case in the README. Consider having the hook write a running hash chain (each line carries the hash of the previous line) so a replacement or a forged line breaks verification.

---

_Reviewed: 2026-10-29T12:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
