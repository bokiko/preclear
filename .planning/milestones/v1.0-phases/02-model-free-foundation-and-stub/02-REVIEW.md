---
phase: 02-model-free-foundation-and-stub
reviewed: 2026-10-26T18:00:00Z
depth: standard
files_reviewed: 53
files_reviewed_list:
  - tests/harness/README.md
  - tests/harness/.gitignore
  - tests/harness/checkpoint_stub.py
  - tests/harness/pc_allowlist.py
  - tests/harness/pc_exitcodes.py
  - tests/harness/pc_flags.py
  - tests/harness/pc_hooklog.py
  - tests/harness/pc_leakgate.py
  - tests/harness/pc_manifest.py
  - tests/harness/pc_measure.py
  - tests/harness/pc_mine.py
  - tests/harness/pc_preflight.py
  - tests/harness/pc_promote.py
  - tests/harness/pc_runroot.py
  - tests/harness/pc_sanitize.py
  - tests/harness/pc_seeds.py
  - tests/harness/pc_spike.py
  - tests/harness/pc_stream.py
  - tests/harness/pc_testutil.py
  - tests/harness/replay-cases.json
  - tests/harness/data/branch-table.md
  - tests/harness/data/spike-findings.md
  - tests/harness/data/s1-init-manifest.json
  - tests/harness/data/s2-probe-labels.json
  - tests/harness/data/s2-stream.jsonl
  - tests/harness/data/s2b-stream.jsonl
  - tests/harness/test_allowlist.py
  - tests/harness/test_bash_shims.py
  - tests/harness/test_branch_table.py
  - tests/harness/test_exitcode_agreement.py
  - tests/harness/test_flags.py
  - tests/harness/test_frozen_reference.py
  - tests/harness/test_imports.py
  - tests/harness/test_leakgate.py
  - tests/harness/test_manifest.py
  - tests/harness/test_measure.py
  - tests/harness/test_mine.py
  - tests/harness/test_preflight.py
  - tests/harness/test_promote.py
  - tests/harness/test_readme.py
  - tests/harness/test_runroot.py
  - tests/harness/test_sanitize.py
  - tests/harness/test_selftest_shim.py
  - tests/harness/test_spike.py
  - tests/harness/test_spike_fixture.py
  - tests/harness/test_stream.py
  - tests/harness/test_stub_cli.py
  - tests/harness/test_stub_concurrency.py
  - tests/harness/test_stub_replay.py
  - tests/harness/test_wrapper_conflict.py
  - tests/harness/selftest
  - tests/harness/checkpoint-wrapper
findings:
  critical: 0
  warning: 12
  info: 9
  total: 21
status: issues_found
---

# Phase 2: Code Review Report (second pass, after gap-closure plan 02-09)

**Reviewed:** 2026-10-26
**Depth:** standard
**Files Reviewed:** 53 (full phase scope kept for downstream consumers; this pass re-read the five files changed since the first pass, `git diff e1b6374..HEAD`: `tests/harness/pc_sanitize.py`, `tests/harness/pc_leakgate.py`, `.gitleaks.toml`, `tests/harness/test_sanitize.py`, `tests/harness/test_leakgate.py`; the other 48 are unchanged)
**Status:** issues_found

The frontmatter counts are the findings still open after this pass: 0 critical, 12 warning (9 carried, 3 new), 9 info (6 carried, 3 new). Five first-pass findings are closed (CR-01, CR-02, WR-01, WR-02, IN-07) and are kept below with their resolution line.

## Summary

Plan 02-09 closes both critical findings. I checked each claim against the code, the new tests and the machine: the full harness suite passes (753 tests, 3 skipped) through `tests/harness/selftest` and through `/usr/bin/python3 -I -B -m unittest discover -s tests/harness -p 'test_*.py'` on Python 3.9.6, and `scripts/test-hooks.sh` still passes with the tightened `.gitleaks.toml` rules. No source file was modified and no model was called.

The diff is careful (the mirrored rules stay byte-identical to `.gitleaks.toml`, the lookbehind and lookahead forms are kept out of the mirrored rules, the failure messages carry no value). The gap-closure still leaves three issues of its own, all in the seam between the sanitizer and the gate: the login is matched as a whole word by the sanitizer but as a case-insensitive substring by the gate (WR-13), the new fail-closed location error can surface after money is spent as a raw traceback (WR-12), and the gate gets the login only when a caller remembers to pass `sanitizer.deny_entries()` (WR-14). None is a leak path; each fails closed or is a wiring gap, which is why none is rated critical. The nine carried warnings are untouched by this diff and stay deferred to Phase 3 hardening.

## Critical Issues

None open. CR-01 and CR-02 are resolved (below).

### Resolved critical findings (carried forward)
### CR-01: Sanitizer leaves the login name in place when a JSON escape precedes it, and the gate cannot catch it

**File:** `tests/harness/pc_sanitize.py:60` (word prefix `(?<!\w)`), `tests/harness/pc_sanitize.py:188-190` (login entries), `tests/harness/pc_leakgate.py:270-272` (gate deny entries hold only hosts and the local file)
**Issue:** The login name is matched as a whole word with the lookbehind `(?<!\w)`. The sanitizer runs on the raw bytes of JSON streams (`sanitize_bytes`, used by `pc_spike.sanitize_to_data`), where a line break is the two characters backslash and `n`. A login directly after `\n` or `\t` is therefore preceded by the word character `n` or `t`, the lookbehind fails and the name is kept.
Reproduced with an injected source (login `alicex`):
- `{"c":"line1\nalicex\nline3"}` is returned unchanged (the `\n` there is the JSON escape).
- `{"c":"x\talicex"}` is returned unchanged.
- `{"c":"owner alicex staff"}` becomes `owner <user> staff` as intended.

The gate is the documented second net, but `Sanitizer.deny_entries()` and `pc_leakgate.build_deny_entries()` carry only host names and the optional local deny file. The login name is in neither, so the gate passes the file. Any multi-line tool output (a process list, `who`, a listing where the name starts a line) in a captured stream can put the account name into committed evidence.
**Fix:**
```python
# pc_sanitize.py: treat a JSON escape as a boundary, not as word characters
_PREFIX = {"path": "", "slug": "", "word": r"(?<![A-Za-z0-9_])(?<!\\[ntrbf])", "substring": ""}
# or, simpler and safer: make the login a "substring" kind at LOGIN_FLOOR >= 4 (like host names)
# and add the login to the entries returned by deny_entries() so the gate refuses what is left:
def deny_entries(self):
    return sorted(set(self._hosts) | set(self._local) | set(self._logins))
```
Add a test with the login after `\n`, `\t` and `\"` in `test_sanitize.py`.

**Resolution:** Resolved by 02-09. Verified in code and tests. `_PREFIX["word"]` in `tests/harness/pc_sanitize.py:63` now accepts a JSON letter escape (backslash plus n, r, t, b or f) as the boundary, and `Sanitizer.deny_entries()` (`pc_sanitize.py:279-281`) returns the login in raw, NFC and NFD form, so the gate refuses what the sanitizer leaves. Re-run with an injected login: the login after `\n` is now `<user>`, and the gate holds it. `LoginBoundaryTests` covers all five escapes, upper case, NFC/NFD, the quote and doubled-backslash cases, the whole-word negatives, and the gate refusing the unsanitised text and passing the sanitised text. Two limits remain, both tracked as new findings: the boundary covers only the five letter escapes (a `\uXXXX` escape or an ANSI colour code before the login is still left by the sanitizer, and is then caught only as a gate refusal, WR-13), and the gate only gets the login when a caller passes `sanitizer.deny_entries()` (WR-14).

### CR-02: Leak gate misses a home path that is followed by a JSON escape, a bracket or a quote-like delimiter

**File:** `tests/harness/pc_leakgate.py:84` (`home-path-unix`), `:85` (`home-path-dash-slug`), `:129-130` (Python-only home rules); parity copy in `.gitleaks.toml`
**Issue:** The rule needs the folder name to be followed by one of `/ whitespace " ' backtick : ; , ) ]` or end of text. The backslash is not in that set, so the first character of a JSON escape (`\n`, `\t`, `\"`) ends no match. Reproduced with a synthetic user name from `pc_seeds.home_path`:

| Text after the home path | Gate result |
|---|---|
| JSON-escaped newline (backslash, n) | no finding |
| JSON-escaped quote (backslash, quote) | no finding |
| `>`  `}`  `|`  `=`  `*`  `~`  a backslash | no finding |
| `.` (end of sentence) | finding |

The streams that `promote` and `sanitize_to_data` are meant to protect are JSONL, where a path ending a string value is routinely followed by `\n` or `\"`. For a home folder the sanitizer does not know (another user, another machine, a path a tool printed), the gate is the only defence, and it returns exit 0. The same hole exists in the commit-hook rule it mirrors, so the second net is open too.
**Fix:** Invert the rule: after the name, require "not a name character" instead of listing delimiters, in both the gate and `.gitleaks.toml` (the parity test keeps them identical):
```python
make_rule("home-path-unix", r'''/(?:Users|home)/[A-Za-z0-9._-]{1,64}(?![A-Za-z0-9._-])''')
make_rule("home-path-root", r'''(?<![A-Za-z0-9._-])/root(?![A-Za-z0-9._-])''')
make_rule("home-path-windows", r'''(?i)\b[a-z]:\\users\\[a-z0-9._-]{1,64}(?![a-z0-9._-])''')
```
Accept the extra hits (a CI runner's home folder, for example) or allowlist them explicitly. Add JSON-escape cases to `test_leakgate.py`.

**Resolution:** Resolved by 02-09 for `home-path-unix`, `home-path-root` and `home-path-windows`, which were the cases reproduced in the table. `home-path-unix` now ends at any non-name character or end of text (`pc_leakgate.py:74`, `.gitleaks.toml:9`, byte-identical, parity test green), and the two Python-only rules were rewritten the same way. `HomePathBoundaryTests` runs every row of the table (JSON newline, tab, return and quote escapes, doubled and single backslash, `>`, `}`, `|`, `=`, `*`, `~`, sentence dot) over four folder shapes, plus the old delimiters, bare `Users`/`home` words and the superuser negatives. I also re-ran `scripts/test-hooks.sh`: all PASS lines, no FAIL, so the `.gitleaks.toml` edit did not break the commit hooks. Only partly covered: `home-path-dash-slug` (named in the original File line, `pc_leakgate.py:92`) is unchanged and still needs a closing hyphen, so a slug at the end of a value or before a JSON escape is not found (IN-09, deliberate per the summary's FA-6).

## Warnings

### Resolved warnings (carried forward)

### WR-01: Gate identifier rules can be evaded with non-ASCII neighbours or an upper-case host suffix

**File:** `tests/harness/pc_leakgate.py:94` (`internal-hostname`), `:96` (`email-address`)
**Issue:** Both rules rely on `\b` and character classes compiled as Python `str` patterns, so `\b` is Unicode-aware, unlike the linear ASCII engine the docstring says the original rules use. A value directly followed or preceded by a non-ASCII letter is not matched (an address ending in an accented letter after the top-level domain, a host name preceded by one). The host rule is also case-sensitive, so a name ending in an upper-case private suffix is not matched, although DNS names are case-insensitive. Both reproduced: no finding for either form.
**Fix:** Compile these patterns with `re.ASCII`, and make the suffix alternation case-insensitive (`(?i:local|lan|home\.arpa|internal|localdomain|ts\.net)`). Mirror the change in `.gitleaks.toml` so the parity test stays green.

**Resolution:** Resolved by 02-09. `make_rule` compiles every pattern with `re.ASCII` (`pc_leakgate.py:82`), and the private host suffix is `(?i:...)` in both the Python rule and `.gitleaks.toml:34`. `AsciiAndCaseTests` checks e-mail and host next to a non-ASCII letter, every suffix in lower, upper and title case, the suffix look-alikes that must stay clean, and that a reserved example domain stays allowed next to a non-ASCII letter. The two forms that gave no finding in the first pass are now covered by explicit one-finding assertions.

### WR-02: A git failure or a missing deny file silently drops the private deny list (fail-open), and the file parser mishandles BOM and padding

**File:** `tests/harness/pc_leakgate.py:460-481` (`_git_deny_path`), `:493-509` (`local_file_entries`)
**Issue:** The module promises that every scanner failure fails closed. `_git_deny_path` returns `None` on a missing git, a timeout, a non-zero exit or a wrong `--repo-root`; `local_file_entries` then returns `[]` and the scan can exit 0 without the local deny entries. A typo in `--repo-root` is enough to turn the private deny list off. Separately, a UTF-8 byte-order mark stays attached to the first line (so that entry never matches), and entries are not stripped, so a trailing space (common editor artifact) makes an entry that can never match a word followed by a newline.
**Fix:** Distinguish "no deny file" (clean) from "could not look" (ScannerError). Decode with `utf-8-sig`, and `line.strip()` before the floor check:
```python
text = raw.decode("utf-8-sig")
...
entry = line.strip()
if len(entry) >= LOCAL_FLOOR and not entry.startswith("#"):
    entries.add(entry)
```
When `git rev-parse` fails but `repo_root` is a directory, raise `ScannerError("could not locate the local deny list")`.

**Resolution:** Resolved by 02-09. `_git_deny_path` (`pc_leakgate.py:482-514`) now raises the fixed `ScannerError` for a root that is not a folder, git missing or timing out, a failing git while a `.git` entry exists in the tree or any ancestor, and an empty answer; the only quiet case is a tree with no repository at all. `local_file_entries` decodes with `utf-8-sig` and strips each line before the floor check, so a byte-order mark and padding no longer switch an entry off. `DenyListLocationTests` covers each branch, the fixed message with no path, the CLI exit 15 for a wrong `--repo-root`, and a BOM first entry taking effect through the CLI. Side effect of the fix: `Sanitizer.from_machine` can now raise after a paid call, see WR-12. Minor residue: a double BOM keeps the second U+FEFF on the first entry, which is not worth a finding.

### Open warnings carried forward

### WR-03: Stub `update` accepts a body that holds the checkpoint end marker and corrupts the ledger for good

**File:** `tests/harness/checkpoint_stub.py:683-690` (`verb_update`), `:705-706` (`verb_note`), `:242-243` (`parse_ledger`)
**Issue:** `update` rejects body lines that start with `## ` but not a line equal to `<!-- CHECKPOINT:END -->` (or a begin marker). `parse_ledger` stops at the first end marker, so the written block parses with its later sections cut off. Reproduced against the stub in a scratch home: after one `update` whose body held that line, `lint` reported `missing section`, `show` printed a truncated block, and the next `update` exited 4 permanently. A model-driven row can do this by accident (a body that quotes the marker), producing a ledger state that no real helper behaviour is known to share, and a confusing result that looks like a skill failure.
**Fix:** In `verb_update` (and for note bodies placed in the block region) reject any line equal to `END_LINE` or matching `BEGIN_RE`/`BEGIN_LINE_RE` with exit 4:
```python
if any(line == END_LINE or BEGIN_LINE_RE.match(line) for line in new_body.split("\n")):
    raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: body contains a checkpoint marker line")
```
Add a CLI test and an UNCONFIRMED row to `branch-table.md`.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-04: The stub deletes and overwrites files, outside the project's no-delete rule, and the static scan cannot see it

**File:** `tests/harness/checkpoint_stub.py:320` (`os.replace`), `:323` and `:513` (`os.unlink`), `:510` (`os.link`); `tests/harness/test_runroot.py:413-416` (`harness_modules()` lists only `pc_*.py`)
**Issue:** Project rule: no deletion primitives outside `pc_testutil.py` and `pc_seeds.py`. The stub calls `os.unlink` twice and overwrites with `os.replace`. The module docstring admits it ("the only deletion anywhere in it") but the rule has no exemption for it, and the scan that enforces the rule only globs `pc_*.py`, so `checkpoint_stub.py` (the one file that mutates ledgers) is never checked. Note also that neither exempt module actually deletes anything, so the exemption set is wider than any code needs.
**Fix:** Either (a) add `checkpoint_stub.py` to the scan with an explicit, asserted exemption limited to the two temporary-file cleanups and the atomic replace, documented in the project rules, or (b) drop the unlink: leave `.ckpt-*` temporaries (name them so `lint` ignores them) and create new ledger files through `os.link` or exclusive create only. Extend `harness_modules()` to cover every `.py` file that is not a test.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-05: `run_s1` has no pre-paid existence check for its output, and the README's rerun advice conflicts with the lifetime caps

**File:** `tests/harness/pc_spike.py:1384-1431` (`run_s1`) against `:1638` (`run_s2a`, `_precheck_free`); `:718-719` (`guard`); `tests/harness/README.md:210-212`
**Issue:** `run_s2a` and `run_s2b` check that their output files are free before spending. `run_s1` does not: the manifest `tests/harness/data/s1-init-manifest.json` is already committed, so `s1 --run` spends up to 0.50 USD and then `sanitize_to_data` raises `FileExistsError`, which `main` does not catch (traceback after the money is gone). Separately, the README tells a reader to rerun a spike on a new Claude Code build, but the spend ledger is append-only with a lifetime limit of two attempts per call name and 5.00 USD in total, and the output files must not exist. After the recorded attempts, a rerun is impossible without editing or deleting files the harness forbids itself to delete, so the documented path cannot be followed.
**Fix:** Call `_precheck_free([manifest_path])` at the top of `run_s1` before the guard, and map `FileExistsError` to a `SpikeError` in `main`. Either make the ledger and output names carry the tested version (for example `spike-spend-2.1.310.jsonl`, `s1-init-manifest-2.1.310.json`) so a new build starts clean, or rewrite the README paragraph to say a rerun needs a new harness home and new output names.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-06: The spend guard is check-then-act; two concurrent paid calls can exceed the attempt limit and the 5.00 USD cap

**File:** `tests/harness/pc_spike.py:708-722` (`guard`), `:1402`, `:1654`, `:1759`, `:1805` (the pessimistic `launched` line is appended later)
**Issue:** `guard` reads the ledger and returns an attempt number; the reserving line is written only after the zero-token preflight (up to two 20 second timeouts), the git setup and the run-root build. Two `pc_spike.py ... --run` processes started together both pass the guard against the same ledger state. The ledger is the only budget enforcement (D-04).
**Fix:** Reserve inside `guard` under an exclusive `fcntl.flock` on a lock file beside the ledger: take the lock, read, check, append the `launched` line, release, and return the attempt. Have the later code skip the duplicate append.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-07: `pc_spike.main` maps only `SpikeError`; the default runs root is macOS-specific and fails with a raw traceback elsewhere

**File:** `tests/harness/pc_spike.py:75` (`DEFAULT_RUNS_ROOT`), `:309-324` (`ensure_runs_root`), `:1987-1990` (`except SpikeError`)
**Issue:** The default runs root is the shared users folder of macOS, built from pieces. On Linux (or for a second macOS account, since the first creator makes the harness folder mode 0700) the `os.mkdir` raises `PermissionError` or `FileNotFoundError`, which is not a `SpikeError`, so the CLI prints a traceback. The module header promises "Messages never carry a home path"; a traceback prints the source path and the exception's own path. Any `ValueError`, `FileExistsError` or `RunRootCollision` from `new_run_root`/`materialize` behaves the same. The README states Linux is "written for but unverified", but nothing steers a Linux user to `PRECLEAR_RUNS_ROOT`. Existing folders in a world-writable shared location are also tolerated without an owner or mode check (`ensure_runs_root`).
**Fix:** Catch `OSError`, `ValueError` and `pc_runroot.RunRootError` in `main`, print a fixed one-line message and return the matching exit code. On a non-macOS platform, make `runs_root()` refuse the default with a message that names `PRECLEAR_RUNS_ROOT`. In `ensure_runs_root`, verify `st_uid == os.getuid()` and no group/other write bit for each tolerated existing level.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-08: `run_s2a` writes its two data files one after the other, so a late refusal leaves a half-written pair that blocks the retry

**File:** `tests/harness/pc_spike.py:1699-1700`, `:1638`
**Issue:** The stream fixture is written first, then the labels file is sanitised, gate-scanned and written. If the second step raises `LeakRefused` or `FileExistsError`, the fixture is already on disk, and every later `s2a --run` stops at `_precheck_free` with the "file already exists" error, after the run's cost is recorded. Recovering needs a deletion the project forbids.
**Fix:** Sanitise and gate-scan both payloads in memory first, then write the two files; only the writes remain after the last refusal point. Apply the same pattern anywhere two outputs are produced from one paid call.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-09: The user-names-absent assertion passes vacuously when the name list is empty

**File:** `tests/harness/pc_spike.py:1413` (`names = local_user_names(home_dir) if home_dir else frozenset()`), `:1083`, `:1954`
**Issue:** When `HOME` is unset or empty, `main` passes `home_dir=None`, `names` is empty, `hits` is 0 and the assertion reports pass. The printed line says "0 listed", but the assertion result and the frozen manifest record a pass, which weakens the isolation evidence. The same happens on a machine whose own skill folders are absent.
**Fix:** Treat an empty effective name set as "not assertable" (`HOW_NONE`, failure with a stated reason), the way the instruction audit is handled when no entry was seen.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-10: `pc_mine.parse_log` cannot read bash `%q` output for arguments with control characters

**File:** `tests/harness/pc_mine.py:58`, `:69`
**Issue:** The wrapper logs argv with `printf ' %q'`. Newer bash writes an argument holding a newline or control byte in the ANSI-C form `$'a\nb'`. `shlex.split` does not know that form: it returned `$a\nb` (backslash and `n` literal) in a direct check. A logged call with such an argument would be mined with a wrong argv and replayed wrongly, silently. `text.splitlines()` also splits on U+2028, U+0085 and the other Unicode separators, which can cut one logged line in two. No committed log holds a `$'` today, so there is no current damage.
**Fix:** Parse the log by splitting only on `\n`, and decode `$'...'` words before `shlex`, or make the wrapper log with a format that `shlex` reads exactly (for example JSON-encode each argument). Add a test with a newline argument.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### WR-11: The manifest CLI never applies the credential-folder refusal that the module promises

**File:** `tests/harness/pc_manifest.py:231` (`tree_manifest(args[0])`), `:123-133`
**Issue:** `tree_manifest(root, refuse_under=())` refuses a root at or under any listed path, and the docstring says the harness-owned Claude config folder "must never be snapshotted". The CLI entry point calls it with the empty default, so `pc_manifest.py <config folder>` prints names, sizes and sha256 values of the credential files.
**Fix:** In `main`, pass `refuse_under=(pc_promote.default_config_dir(),)` (or compute it from `PRECLEAR_HARNESS_HOME` the same way), and add a CLI test for the refusal.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff; re-checked that none of the five changed files changes its behaviour.

### Open warnings added by the gap-closure diff

### WR-12: `Sanitizer.from_machine` can now raise after the paid call, and `main` does not map `SanitizerError`

**File:** `tests/harness/pc_spike.py:1429`, `:1686`, `:1772`, `:1808` (the four constructions), `:1987` (`except SpikeError` only); `tests/harness/pc_sanitize.py:178-179`
**Issue:** The WR-02 fix turns "git cannot be run, timed out, or fails inside a repository" into an error, and `from_machine` converts it to `SanitizerError("the local deny list could not be read or located")`. Every `from_machine` call in `pc_spike.py` happens after `run_claude` has returned (the spend is already recorded), and `SanitizerError` is not a `SpikeError`, so `main` does not catch it. Before 02-09 the same git failure was silent; now a transient git problem (a timeout, an ownership refusal on the repository, git off the path) ends in a traceback after up to 0.50 USD per call, with no data file written and a retry attempt burned. `sanitize_to_data` only wraps `sanitize_bytes`, not the construction.
**Fix:** Build the sanitizer before anything is spent (before `guard` and before `append_spend`), in each of the four runners, so the location failure is a zero-token refusal. Also catch `pc_sanitize.SanitizerError` in `main` and map it to a `SpikeError`-style exit 15 with the fixed message. Add a test that patches `pc_leakgate.subprocess.run` to fail and asserts no spend line is written.
**Resolution:** Open (new in 02-09).

### WR-13: The gate matches the login as a case-insensitive substring, the sanitizer as a whole word, so residue is refused and some captures can never be written

**File:** `tests/harness/pc_sanitize.py:63` (word prefix), `:196-199` (gate entry); `tests/harness/pc_leakgate.py:194-205` (`_deny_regex`)
**Issue:** The new gate entry is the bare login, matched anywhere. The sanitizer still replaces it only at a whole-word boundary (plus the five letter escapes). Probed with an injected login `alice` (zero tokens): `{"c":"malice and alice"}` becomes `{"c":"malice and <user>"}` and the gate then reports one `deny-list` finding; the same for `latest` with a login `work` embedded in a longer word, for `\u001b[0malice` (an ANSI colour code before the name) and for `\u000aalice` (a unicode newline escape). `sanitize_to_data` then raises `LeakRefused` and nothing is written, and there is no way to proceed (no override, and the sanitizer will not rewrite the text). This is the safe direction (no leak), but it makes the evidence capture a lottery for any owner whose login is a common word or substring, and it hides the real residual: the two escape forms above are genuine boundary cases the sanitizer should have replaced, which only the gate stops.
**Fix:** Make both sides agree. Either (a) widen the sanitizer boundary to every JSON escape (`\\u[0-9a-fA-F]{4}`, and a terminal colour sequence ending in `m`) and give the gate entry the same word-bounded pattern instead of a bare substring (a separate "word" entry kind in `_deny_regex`), or (b) for logins of at least six characters treat the login as a substring kind in the sanitizer like host names, and keep the gate as it is. Add a test for the longer-word case and for `\u001b[0m` before the login.
**Resolution:** Open (new in 02-09).

### WR-14: The login reaches the gate only if the caller passes `sanitizer.deny_entries()`; `promote` and the gate CLI silently use the weaker default

**File:** `tests/harness/pc_promote.py:171` (`deny_entries if deny_entries is not None else pc_leakgate.build_deny_entries(...)`), `tests/harness/pc_leakgate.py:578` (CLI `build_deny_entries(repo_root, None, deny_file)`); the contract itself is recorded only in `.planning/phases/02-model-free-foundation-and-stub/02-09-SUMMARY.md` (key-decisions)
**Issue:** The login joined the gate through `Sanitizer.deny_entries()` on purpose (the login is also the owner's public alias and appears in committed prose, so the default entry builder must not carry it). The consequence is that the second net for CR-01 exists only on the `sanitize_to_data` path. `pc_promote.promote` (default `deny_entries=None`) and `pc_leakgate.py scan` both run without the login, with nothing in their docstrings or in the README saying so. The first Phase 3 caller that forgets the argument gets a green gate and no login check, which is exactly the first-pass CR-01 failure mode. The docstring of `promote` says only that entries are "built at run time".
**Fix:** State the requirement in the `promote` docstring and the README privacy section, and add a test that fails when a run is promoted after sanitising without passing the sanitizer's entries (or make `promote` take a required `sanitizer`/entries argument for runs that were sanitised, with an explicit `None` meaning "unsanitised input"). Phase 3 should wire this when the runner lands.
**Resolution:** Open (new in 02-09).

## Info

### Resolved info (carried forward)

### IN-07: The leak-gate suite has no case for the delimiter and boundary gaps found above

**File:** `tests/harness/test_leakgate.py`, `tests/harness/test_sanitize.py`
**Issue:** No test places a home path, e-mail address or host name next to a JSON escape, a bracket, a non-ASCII letter or an upper-case suffix, and none puts the login after `\n`. The committed corpus passes the gate, but only because the sanitizer got the machine's own values; the parity test with `.gitleaks.toml` also freezes the gaps in both places.
**Fix:** Add table-driven boundary cases (delimiter set, Unicode neighbours, case) for each of the six identifier rules and for the sanitizer's login handling; run them against the fixed patterns from CR-01 to CR-02 and WR-01.

**Resolution:** Resolved by 02-09. `LoginBoundaryTests`, `LocationFailClosedTests` (`tests/harness/test_sanitize.py`) and `HomePathBoundaryTests`, `IdentifierBoundaryTests`, `AsciiAndCaseTests`, `DenyListLocationTests` (`tests/harness/test_leakgate.py`) add table-driven boundary cases for delimiters, JSON escapes, Unicode neighbours, case and the login. Selftest: 753 tests OK, 3 skipped (run with the real harness runner and with `/usr/bin/python3 -I -B -m unittest discover`, Python 3.9.6, both green). The NEW_BOUNDARIES rows are exactly the first-pass reproduced misses, so they would fail against the pre-diff rule strings (read from the diff, not re-run against the old code). See IN-10 for a quality note on the repeated fixture-scan helper.

### Open info carried forward

### IN-01: Spend and probe readers validate less than their writers

**File:** `tests/harness/pc_spike.py:656-668` (`read_spend`), `:1935-1939` (`_cmd_probes`), `:1921` (`_cmd_spend`)
**Issue:** `append_spend` refuses a negative cost and a non-positive attempt, but `read_spend` accepts both (and booleans as attempts), so a hand-edited line can lower the recorded total. `_cmd_probes` raises `KeyError` or `TypeError` on a probe line with an unexpected `loggedIn` or `exit` value. `_cmd_spend` prints "over N call(s)" where N counts ledger lines, which is about twice the call count because each paid call writes two lines.
**Fix:** Validate `attempt >= 1` and `cost >= 0` on read, validate probe field types, and print the number of effective (call, attempt) keys.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### IN-02: Wrapper injection numbering assumes the armed count starts at 2

**File:** `tests/harness/checkpoint-wrapper:88` (`k=$((3 - n))`)
**Issue:** With `armed` set to 1, the single injection is labelled injection 2 and carries the second fact. With a count above 2, `k` is zero or negative and picks the second fact text. The header comment documents only count 2.
**Fix:** Keep a counter file, or compute `k` from a recorded total, and reject `armed` values other than 1 or 2 with exit 70.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### IN-03: Test hygiene: cleanup is inconsistent with the stated rule, and one assertion is timing-bound

**File:** `tests/harness/test_selftest_shim.py:76`, `tests/harness/test_bash_shims.py`, `tests/harness/test_exitcode_agreement.py`, `tests/harness/test_flags.py`, `tests/harness/test_preflight.py` (use `tempfile.TemporaryDirectory`, which deletes); `tests/harness/test_stub_concurrency.py:96` (`assertLess(elapsed, 2.0)`)
**Issue:** Most test modules state that scratch folders are created with `mkdtemp` and never deleted (the project rule); these five modules use `TemporaryDirectory`, which removes the tree, and the scan that enforces the rule covers only `pc_*.py`. Every run also leaves new `preclear-selftest.*` and `pc-home-*` folders in the temp area. The lock-timeout test asserts a two second wall-clock ceiling around a subprocess start and may flake on a loaded machine.
**Fix:** Pick one policy and enforce it for `test_*.py` as well; widen the elapsed bound (for example 10 seconds, while still asserting exit 6 and an unchanged ledger).

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### IN-04: `pc_stream check` does not print what its docstring promises

**File:** `tests/harness/pc_stream.py:306-327` against `:1-13`
**Issue:** The module says the two denial signals are cross-checked with a mismatch "reported in both directions" and that tool results flagged as errors are listed for diagnostics. `_check_command` prints only the union of ids and never `only_in_events`, `only_in_result` or `tool_errors`; a result with `is_error` true or an error subtype also exits 0.
**Fix:** Print the three counts and the result `is_error` flag, and decide (and document) whether a mismatch or an error result should change the exit code.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### IN-05: `int()` over banner digits can raise on Python 3.11 and newer

**File:** `tests/harness/pc_flags.py:475`, `tests/harness/pc_spike.py:818`
**Issue:** `parse_banner` accepts `[0-9]+` of any length. Python 3.11+ refuses to convert more than 4300 digits and raises `ValueError`, which neither caller catches, while 3.9 accepts it. Only a malicious or broken `claude` triggers it, but the preflight is the first code to run on its output.
**Fix:** Bound the groups in the banner pattern (`[0-9]{1,6}`).

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### IN-06: Config-folder containment in `promote` is case-sensitive on a case-insensitive filesystem

**File:** `tests/harness/pc_promote.py:154-157`
**Issue:** `os.path.realpath` does not normalise letter case on the default macOS filesystem, so a stage or destination spelled with different case under the harness config folder is not seen as "under" it. The folder holds credentials.
**Fix:** Compare with `os.path.normcase` plus a `samefile` check on the nearest existing ancestor.

**Resolution:** Open (deferred to Phase 3 hardening). Not touched by the 02-09 diff.

### Open info added by the gap-closure diff

### IN-08: A login that is a substring of a fixed token gets no gate entry

**File:** `tests/harness/pc_sanitize.py:196-199`
**Issue:** The FA-4 guard skips the gate entry when `login.lower()` occurs inside any fixed token (`<user>`, `<home>`, `<host>`, `<repo>`, `<run>`, `<helper>`, `<scratch>`, `<redacted>`, `<tmp>`, `<auto-memory-root>`). A login such as `user`, `home`, `host`, `repo` or `root` (a container account, say) therefore has no second net at all, and only the sanitizer's whole-word and letter-escape rule protects it. The test only asserts the entry is absent, not that anything else covers the gap. Numbered token variants the sanitizer also emits (`<run-1>` and the like) are not part of the check.
**Fix:** Keep the gate entry but allow the gate to ignore the fixed tokens (strip `TOKENS` and their numbered forms from the text before the login entry is matched), instead of dropping the entry. Document the limitation until then.
**Resolution:** Open (new in 02-09).

### IN-09: `home-path-dash-slug` still needs a closing hyphen, and the folder-name length cap still hides long names

**File:** `tests/harness/pc_leakgate.py:92` (`-(?:Users|home)-[A-Za-z0-9._]{1,64}-`), `:74` (`{1,64}`); `.gitleaks.toml:15`
**Issue:** The slug rule was left unchanged on purpose (FA-6). Probed: `-Users-name"` and `-Users-name\n` (the slug of the home folder itself, as the name of a project folder, at the end of a JSON string) give no finding. The same hole, in the dash-slug form, that CR-02 closed for the slash form; the sanitizer covers only the owner's own slug. Separately, a folder name longer than 64 characters is not matched by any home-path rule (the class is capped and the next character must be a non-name character), so an unusual 65-plus character folder name passes. Both are narrow.
**Fix:** End the slug rule with `(?:-|[^A-Za-z0-9._]|$)` in both files (parity test keeps them equal) after checking `scripts/test-hooks.sh`, and drop the upper bound or refuse long runs (`MAX_RUN` already exists).
**Resolution:** Open (new in 02-09, residue of CR-02).

### IN-10: The fixture-scan helper repeats 31 times per run and some calls assert nothing about the case under test

**File:** `tests/harness/test_leakgate.py:69` (22 calls), `tests/harness/test_sanitize.py:58` (9 calls)
**Issue:** `assert_fixtures_clean` is appended to nearly every new test. It scans the same unchanged committed data folder each time, so it proves the same thing 31 times (`test_leakgate` now takes about 3.3 s). It does not exercise the case the test is about, and several calls pass an empty deny list (for example the real-login test), so they do not prove the login is absent from the fixtures. The IN-07 intent (a corpus-level regression guard) is better served by one dedicated test that scans the data folder with the full entry set.
**Fix:** Replace the repeated calls with a single `FixturesCleanTests` case using `Sanitizer.from_machine(...).deny_entries()`; keep the per-case tests focused on their own inputs.
**Resolution:** Open (new in 02-09).

---

_Reviewed: 2026-10-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
