# Phase 3: Walking Skeleton (Row 1) - Pattern Map

**Mapped:** 2026-10-28
**Files analyzed:** 22 new or modified
**Analogs found:** 21 / 22 (one partial)

All analog paths are git-tracked files under `tests/harness/` (checked with `git ls-files`). Line numbers are for the files as of base commit `b27e8c5`. File names for the new modules follow the RESEARCH proposal and are at the planner's discretion. No `claude` process was started while mapping.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/harness/pc_matrix.py` (driver CLI: `--list/--row/--layout/--all/--dry-run/--claude`) | CLI / controller | request-response | `pc_spike.py` `main` + `_build_parser` + `describe_call` (1856-1994); `pc_preflight.py` `main` (189-215) | role-match |
| `tests/harness/pc_rows.py` (row and layout registry, stage caps) | config / model | transform | `pc_spike.py` `CallSpec`/`CALLS` (100-113) | exact |
| `tests/harness/pc_row1.py` (row 1 seed, stage chain) | service | batch + file-I/O | `pc_spike.py` `materialize` (464-583), `run_claude` (1260-1292), `run_s1` (1368-1438) | exact |
| `tests/harness/pc_spend.py` (matrix ledger, delta accounting, per-row cap) | service | file-I/O (append-only) | `pc_spike.py` `append_spend`/`_effective`/`_total_of`/`guard` (592-729) | exact |
| `tests/harness/pc_checks.py` (write boundary, git read-only, helper-call correlation) | utility | transform | `pc_manifest.py` (`tree_manifest`, `capture_git_status`), `pc_stream.py` (`tool_calls`, `denial_report`), `pc_mine.py` `parse_log` | role-match |
| `tests/harness/pc_evidence.py` (renderers, usage.txt, provenance, stage-sanitize-gate-promote) | service | file-I/O | `pc_spike.py` `sanitize_to_data` (1225-1250); `pc_promote.py` `promote` (140-223); `pc_measure.py` `format_report` | role-match |
| `tests/harness/pc_compare.py` (read-only comparer, tree digest) | utility / CLI | transform | `pc_mine.py` `mine_row`/`parse_trace`/`parse_log`; `pc_measure.py` `main`; `pc_manifest.py` `jsonl_bytes` | role-match |
| `tests/harness/pc_preflight.py` (MODIFY: explicit `--claude` path) | service | request-response | itself, `find_claude` + `run_preflight` (74-83, 106-179) | exact |
| `tests/harness/checkpoint_stub.py` (MODIFY: WR-03 end-marker fix) | service | CRUD | itself, `parse_block_lines`/`parse_ledger`/`append_history` (205-250, 515-540); `data/branch-table.md` | exact |
| `tests/harness/data/row1-s1-prompt.md`, `row1-s2-prompt.md` (byte copy), ledger seeds, CLAUDE.md template, plan text | config (data) | file-I/O | `data/s2-probe-labels.json`, committed `row1-wrong-binding/s2-preclear-prompt.md` | role-match |
| `tests/harness/test_matrix_cli.py` | test | request-response | `test_spike.py` `run_cli` (78-85), `DryRunTests` (448-543) | exact |
| `tests/harness/test_row1_seed.py` | test | file-I/O | `test_spike.py` `MaterializeTests` (237-352) | exact |
| `tests/harness/test_stages.py` (fake-claude paid-path rig) | test | batch | `test_spike.py` `FAKE_CLAUDE` + `PaidRig` (1023-1143), `PaidS1Tests` (1145+) | exact |
| `tests/harness/test_checks.py` (seeded write-boundary FAIL fixture) | test | transform | `test_spike.py` `FAKE_CLAUDE` canned `events` branch; `pc_testutil.git_env` | role-match |
| `tests/harness/test_spend.py` | test | file-I/O | `test_spike.py` `SpendGuardTests` (366-446) | exact |
| `tests/harness/test_evidence.py` (promote-without-deny-entries must fail) | test | file-I/O | `test_promote.py`, `test_spike.py` `SanitizeToDataTests` (946-994) | role-match |
| `tests/harness/test_compare.py` | test | transform | `test_mine.py`, `test_manifest.py` | role-match |
| `tests/harness/test_preflight.py` (MODIFY: `--claude` cases) | test | request-response | itself (exit-code class at 56-92) | exact |
| `tests/harness/test_stub_cli.py` + `data/branch-table.md` (WR-03 rows) | test / doc | CRUD | `test_stub_cli.py`, `test_branch_table.py` | exact |
| `tests/harness/README.md` + `tests/harness/test_readme.py` (MODIFY) | doc + test | transform | itself: Layout list (README line 228+), `PENDING_SPIKE_FILES`, exit-table and flag-table tests | exact |
| `tests/harness/test_allowlist.py` / `pc_allowlist.py` (MODIFY: scope `load_trace_calls`) | test | transform | itself (corpus test at 245-264, loader at 317) | exact |
| `SKILL.md` size cap test (new, 12,000 bytes) | test | transform | `test_frozen_reference.py` | role-match |

## Pattern Assignments

### Driver CLI `pc_matrix.py` (CLI, request-response)

**Analog:** `tests/harness/pc_spike.py` (`main`, `describe_call`, `_build_parser`) and `pc_preflight.py` `main`.

**Imports pattern** (`pc_spike.py` 14-37): `from __future__ import annotations`, stdlib first, then sibling modules only (`import pc_exitcodes`, `import pc_flags`, ...). `test_imports.py` enforces sibling-only imports, Python 3.9 grammar, `pc_` prefix, no stdlib-shadowing stem.

**CLI exit-mapping pattern** (`pc_preflight.py` 189-215):
```python
parser = argparse.ArgumentParser(prog="pc_preflight.py", add_help=True)
...
try:
    args = parser.parse_args(argv)
except SystemExit as exit_request:
    return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE
...
sys.stdout.write(result.line() + "\n")
return result.exit_code
```
Copy: `main(argv, env)` returns an int, never calls `sys.exit` inside; `if __name__ == "__main__": sys.exit(main())`. Run the CLI in tests as `python3 -E -s -B <script>` (`test_spike.py` 78-85). No new environment variable (README switch table is pinned to six names); use flags and injected callables.

**Exit-state mapping** (`pc_preflight.py` 61-71 and `pc_exitcodes.py` 49-60): SKIP 10, FAIL 11, BLOCKED 12, untested version 13 already exist. Add no constant (the "twelve named codes" test in `test_preflight.py` 56-92 stays green). `pc_spike.HomeRefused` carries exit 2; the driver must map "runs root under a home folder" to 12 itself (RESEARCH Pattern 4).

**Dry-run pattern** (`pc_spike.py` `describe_call` 1856-1897, `DryRunTests` 448-470): print the plan with role tokens (`_ROLE_CLAUDE`, `_ROLE_SETTINGS`, `_ROLE_WRAPPER`, `_ROLE_SESSION` at 1828-1831), start no process, write no ledger line. Dry-run test = tripwire `claude` first on PATH, then `assert code == 0 and pc_testutil.read_tripwire(bin_dir) == []`.

---

### Row registry `pc_rows.py` (config, transform)

**Analog:** `pc_spike.py` 100-113.
```python
class CallSpec(NamedTuple): ...
CALLS: Dict[str, CallSpec] = { ... }
```
Copy a NamedTuple stage spec (name, max_turns, cap USD as `Decimal`/string) with row 1 = s1 15 turns / 0.30, s2 60 / 1.30, s3 15 / 0.40 (D-14). Caps feed `pc_flags.build_argv(..., max_turns, max_budget_usd)` which validates `1 <= max_turns <= 100` and formats the budget via `format_budget`.

---

### Row 1 seed and stage chain `pc_row1.py` (service, batch + file-I/O)

**Analog:** `pc_spike.py` `materialize` (464-583). Write a sibling function; do not generalise `materialize` (12 tests pin it).

**Argument and containment checks** (471-492): canonical lowercase UUID check, `os.path.realpath` of repo and run root, refuse run root outside runs folder or inside the repo.

**Exclusive creation order to copy** (509-566):
```python
_copy_tree_with(source["fixture"], project, {"CLAUDE.md": fill})
_run_git(project, ["init", "-q"])
_run_git(project, ["symbolic-ref", "HEAD", "refs/heads/main"])
_run_git(project, ["add", "-A"])
_run_git(project, ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "Initial fixture commit"])
pc_runroot.exclusive_dir(skill_dir, 0o700)
pc_runroot.write_exclusive(os.path.join(skill_dir, "SKILL.md"), _read_bytes(source["skill"]), 0o644)
pc_runroot.write_exclusive(wrapper, _read_bytes(source["wrapper"]), 0o755)
pc_runroot.write_exclusive(os.path.join(wrapper_dir, "py"), interpreter.encode("utf-8"), 0o644)
pc_runroot.write_exclusive(os.path.join(wrapper_dir, "stub"), source["stub"].encode("utf-8"), 0o644)
```
Row 1 deltas (RESEARCH "Seeding row 1"): write ledger A and ledger B into `ckpt/ledgers/`, bind the session to B, skip the fixture's `thoughts/ledgers` (needs an exclusion parameter, `_copy_tree_with` at 367 has none), add the plan file, render `CLAUDE.md` from the committed row's `fixture-CLAUDE.md`, create an empty `wrapper/calls.log`, `audit_hook=True`.

**Driver-side state goes to the stub directly, never the wrapper** (539-556):
```python
stub_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "CKPT_HOME": ckpt}
done = subprocess.run(
    [interpreter, "-I", "-B", source["stub"], "bind", "--ledger", ledger, "--session", session_id],
    env=stub_env, cwd=project, stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=_STUB_TIMEOUT_SECONDS, shell=False)
if done.returncode != 0:
    raise SpikeError("the checkpoint stub refused the state setup")
```

**Paid-call launcher** (reuse `run_claude`, 1260-1292, do not copy):
```python
def run_claude(argv, env, cwd, prompt, timeout, raw_dir, stem) -> CallResult:
    done = subprocess.run(list(argv), env=dict(env), cwd=cwd, input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=False)
    ...
    pc_runroot.write_exclusive(os.path.join(raw_dir, stem + ".stdout"), result.stdout, 0o600)
```
Prompt on stdin, raw bytes kept exclusively under the run root. All three stages use the project folder as cwd (resume requires the same cwd).

**Argv for the three stages** (`pc_flags.py` 300-368, signature `build_argv(claude_path, session_id, settings_path, allowed_tools, max_turns, max_budget_usd, resume=False, include_hook_events=False, model=PINNED_MODEL)`):
```python
s1 = pc_flags.build_argv(claude, U1, settings, tools, 15, "0.30", include_hook_events=True)  # --session-id U1
s2 = pc_flags.build_argv(claude, U1, settings, tools, 60, "1.30", resume=True)               # --resume U1
s3 = pc_flags.build_argv(claude, U2, settings, tools, 15, "0.40")                            # new uuid4
```
Tools: `pc_flags.build_allowed_tools(str(paths["wrapper"]), pc_flags.MODEL_FACING_WRAPPER_VERBS)`; env: `pc_flags.build_env(base_env, cfg, str(paths["ckpt"]))`.

**Order of the paid path to copy** (`run_s1` 1368-1438): guard first (BudgetRefused propagates), strict preflight (nothing recorded when blocked), fresh run root, pessimistic ledger line, the call, reconciling ledger line, assertions, then sanitise and write. Use strict `pc_preflight.run_preflight`, not `spike_preflight` (which allows an untested build). Evaluate every pre-spend refusal (destination name free via `os.path.lexists`, sanitizer built, deny entries obtained, runs root accepted, budget flag present) before the first token (WR-05, WR-12, WR-14).

**Error handling** (1404-1414): non-success subtype, timeout or `events is None` returns `PREFLIGHT_FAIL` with a "one retry is allowed by the guard" style line; for Phase 3, a retry needs bokiko's explicit word, so the line must say no retry exists without the mechanical flag.

**Init and hook-log assertions to reuse:** `s1_evaluation`/`evaluate_s1`/`hit_candidates`/`binary_defines` (1062-1180), `pc_stream.init_manifest`. A memory-path assertion is missing (HARN-07) and must be added.

**Resume line extraction** (RESEARCH Code Examples): take the last fenced single line starting `Resume `; empty means record `NO-RESUME-LINE` and do not run s3. The s3 prompt is the line with no trailing newline.

---

### Spend ledger `pc_spend.py` (service, file-I/O append-only)

**Analog:** `pc_spike.py` 588-729.

**Append-only line writer** (592-602):
```python
def _append_json_line(path, record):
    line = (json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags, 0o600)
```

**Pessimistic ledger line** (`run_s1` 1393 and `_effective` 672-682): write `append_spend(home, "s1", attempt, None, "launched", version)` before launch; cost `None` counts as the stage cap; a later line for the same `(call, attempt)` supersedes it.
```python
latest[(record["call"], record["attempt"])] = record
...
total += CALLS[record["call"]].cap if cost is None else Decimal(cost)
```

**Guard** (708-726): refuse with `BudgetRefused` (exit 18) when the call name used its attempts or recorded spend plus this cap exceeds the cap. Matrix differences: one attempt per stage, row cap 2.00 USD, a human-typed retry flag appended by a separate zero-token subcommand, a file lock for races (WR-06), and **delta accounting** because `total_cost_usd` is cumulative across `--resume` (s2 delta = s2 total minus s1 total, or the sum of `model_usage_since_last_result[*].costUSD`; row total = s2 total + s3 total). Keep this ledger separate from `spike-spend.jsonl` and leave `pc_spike` untouched.

**Per-call cost helper** (RESEARCH Code Examples): sum `model_usage_since_last_result` `costUSD` as `Decimal`, else `total_cost_usd` for the first call of a session. `pc_stream._as_decimal` already yields `Decimal`.

---

### Mechanical checks `pc_checks.py` (utility, transform)

**Analogs:** `pc_manifest.py`, `pc_stream.py`, `pc_mine.py`.

**Snapshots** (`pc_manifest.py` 123-135, 182-218): `tree_manifest(root, refuse_under=(config,))` never follows symlinks and raises on walk errors; `sha_txt_bytes`, `jsonl_bytes`, `write_snapshot`. `tree_manifest` has no exclude parameter: filter the returned entries for `.git/`, `raw/`, `stage/`, `wrapper/py`, `wrapper/stub`.

**Git capture** (`pc_manifest.py` 94-105): `raw, text = capture_git_status(project_dir, git)`; raw NUL form stays in `raw/`, text form is the only evidence candidate (the leak gate refuses NUL bytes).

**Stream facts** (`pc_stream.py`):
```python
def tool_calls(events) -> List[Tuple[str, str, Dict]]   # (tool_use_id, name, input) in order
def denial_report(events) -> DenialReport               # event_ids, result_ids, union, only_in_events, only_in_result, tool_errors
def tool_results(events) -> Dict[str, Tuple[bool, str, int]]  # lengths only, never content
```
Denials are counted facts, not a FAIL (CONTEXT, "Claude's call"); FAIL is for a write-boundary or git breach or a broken harness. `pc_stream.unexpected_denials`/`row_failed` exist but invert that policy; do not use them as the row verdict.

**Wrapper log correlation** (`pc_mine.py` 49-83): `parse_log(text)` returns `[{"argv": [...], "exit": n}]` in line order, one CALL then one EXIT; raises `MineError` on malformed lines. Slice per stage by recording the `calls.log` line count at each snapshot (`calls.log` is cumulative). Split commands with `pc_allowlist.split_compound` (94). Report four counts: Bash calls naming the helper, executed (log CALL lines), denied, compound-command refusals.

---

### Evidence filer `pc_evidence.py` (service, file-I/O)

**Analogs:** `pc_spike.sanitize_to_data` (1225-1250), `pc_promote.promote` (140-223), `pc_measure.format_report` (84-101).

**Sanitize, gate, exclusive write** (1225-1250):
```python
if os.path.lexists(dest):
    raise FileExistsError("the data file already exists")
clean = sanitizer.sanitize_bytes(scrub_volatile(data))
findings = pc_leakgate.scan_bytes(os.path.basename(dest), clean, sanitizer.deny_entries())
if findings:
    raise LeakRefused("the leak gate found a leak after sanitising (%s); nothing was written" % shown)
pc_runroot.write_exclusive(dest, clean, 0o644)
```

**Filing call (WR-14, required):** stage the whole tree in `<run>/stage/`, then once:
```python
result = pc_promote.promote(stage, dest, repo_root, deny_entries=sanitizer.deny_entries())
# result.code: 0 promoted, 14 leak, 15 scanner error, 17 refused; never print deny_entries()
```
`promote` creates missing parents, refuses an existing destination (`"the destination already exists"`), and checks the gate before creating anything. This gives D-05's exclusive `tests/evidence/rerun-<date>-<model>/` creation.

**Caller map** (`pc_spike._caller_map` 1344-1350): extend the map with the runs root and its parent mapped to `<scratch>`, otherwise the gate's home-path rule flags the shared runs-root parent (finding C7):
```python
mapping = {str(paths["run_root"]): "<run>"}
mapping[str(paths["auto_memory"])] = "<auto-memory-root>"
# keep wrapper as <run>/wrapper/checkpoint for new traces (do not map to <helper>)
sanitizer = pc_sanitize.Sanitizer.from_machine(repo_root, caller_map)
```

**Byte measurement:** run `pc_measure.measure_file(path)` on the ORIGINAL checkpoint, then `pc_measure.format_report(label, m)` (output shape `total N/4096 bytes, sha256 H` and `- Section: N/cap`). Never measure sanitized copies.

**Trace shape:** renderers must match `pc_mine.parse_trace` (`_TRACE_HEAD`, `_TRACE_BODY`) so the comparer's reader keeps working. Harness-authored files use neutral vocabulary; `README.md` ends with `Reviewer verdict: PENDING` and the D-09 checklist, one source file named per line.

---

### Comparer `pc_compare.py` (utility, transform)

**Analog:** `pc_mine.py` (`parse_log`, `parse_trace`, `mine_row`) and `pc_measure.main` for the exit-code habit (2 for an unreadable input, 0 otherwise).

**Tree digest proof (EVID-06)** (RESEARCH Code Examples, from `pc_manifest.py` 123/194):
```python
import hashlib, pc_manifest
def tree_digest(root):
    return hashlib.sha256(pc_manifest.jsonl_bytes(pc_manifest.tree_manifest(root))).hexdigest()
```
Compute for both whole evidence trees before and after; print `unchanged: yes|no`. Open files read-only. Never print PASS or FAIL for a row (EVID-05); exit 0 whenever both trees were readable. Normalise `<repo>/<run>` and `<run>` before comparing trace-derived counts. Parse both measurement shapes (old `total N bytes (cap 4096)`, new `total N/4096 bytes`).

---

### `pc_preflight.py` MODIFY (`--claude <path>`)

**Analog:** itself, `find_claude` (74-83) and `run_preflight` (106-179).
```python
def find_claude(search_path, name="claude"):
    if search_path is None:
        return shutil.which(name)
    return shutil.which(name, path=os.pathsep.join(search_path))
```
Add an optional explicit `claude_path` parameter to `run_preflight` that bypasses `find_claude` (absolute path, must be an executable file) and still feeds `check_version` (exact match against `TESTED_VERSIONS`, 2.1.310). Do not widen `TESTED_VERSIONS`. The same path must reach `build_argv` and `binary_defines`. Add the `--claude` cases to `test_preflight.py` using `pc_testutil.make_fake_claude(directory, banner, logged_in)`.

---

### `checkpoint_stub.py` MODIFY (WR-03 end marker)

**Analog:** itself. The block parser closes on the first line equal to `END_LINE` (parse_ledger 242: `elif begin is not None and line == END_LINE`), and `append_history` searches `"\n" + END_LINE` (521). Body text quoting the marker corrupts the ledger. Fix per review WR-03: reject (usage error, `EXIT_USAGE`) any `update` body line equal to `END_LINE` (constant at 153) before the render at `render_block` (225-231). Pair the fix with a CLI test in `test_stub_cli.py` and a new row in `data/branch-table.md` (`test_branch_table.py` ties the table to the stub docstring; status column values `CONFIRMED`/`UNCONFIRMED`/`STUB-ONLY`, so mark it `STUB-ONLY`).

---

### Test scaffold for the paid path (fake `claude`)

**Analog:** `test_spike.py` `FAKE_CLAUDE` (1023-1076) and `PaidRig` (1078-1143). Copy into a shared test-support module (RESEARCH suggests one) rather than importing across test files if `test_imports.py` forbids it; check before doing so.

Key behaviours to reuse (1023-1076):
```python
args = sys.argv[1:]
cfg = json.load(open(os.path.join(here, "fake.json")))
if args == ["--version"]: print(cfg["banner"]); sys.exit(0)
if args == ["auth", "status", "--json"]: ...                       # boolean loggedIn only
prompt = sys.stdin.read()
record = {"args": args, "prompt": prompt, "cwd": os.getcwd(), "env": {...CLAUDE_CONFIG_DIR, CKPT_HOME, DISABLE_AUTOUPDATER}}
sid = args[args.index("--resume") + 1] if "--resume" in args else args[args.index("--session-id") + 1]
subs = {"$SID": sid, "$CWD": cwd, "$RUN": os.path.dirname(cwd), "$WRAPPER": ...}
if cfg.get("events"):                                              # canned stream path
    for event in cfg["events"]: ... print(line)
```
Extend with: a third stage, a `Write` `tool_use` plus a real out-of-root write (seed i, snapshot path; seed ii, trace path; seed iii, a commit in the project), cumulative `total_cost_usd` across `--resume` (use `tests/harness/data/s2-stream.jsonl` and `s2b-stream.jsonl` as the stream shape and cost fixtures), and an optional wrapper call so `calls.log` grows. Each seed must give a non-zero count, a non-zero driver exit, and nothing promoted.

`PaidRig` pattern: `self.bin` holds `claude` and `fake.json`; `self.repo = make_repo(self.base)`; `self.runs`, `self.data` temp folders; `cli_env(self.base, [self.bin], harness_home=..., extra={"HOME": ..., "PRECLEAR_RUNS_ROOT": self.runs})`; `calls()` reads `calls.log` back for argv assertions (check `--resume` vs `--session-id`, `--max-turns`, `--max-budget-usd` values per stage).

**Zero-token proof:** `pc_testutil.make_tripwire(bin_dir)` (any argv logged, exit 97) plus `read_tripwire`; add an in-process `subprocess` trap for the dry run.

**Spend tests:** copy the `SpendGuardTests` shape (366-446) against the new ledger.

---

### README and `test_readme.py` MODIFY

**Analog:** the files themselves.

- README Layout list (`## Layout`, line 228+): one line per file, `- \`name\` - description`; add every new module, test and `data/` file once. `test_every_file_in_the_folder_is_named_once_in_the_layout` (266) and `test_no_missing_file_is_named_except_the_pending_spike_files` (272) enforce both directions; `PENDING_SPIKE_FILES` (40-50) only matters for files not yet present, so new files should be committed in the same plan that lists them.
- Exit-code table: generated from `pc_exitcodes` via `render_exit_code_table()` (80-84); adding no constant avoids a table change. If a constant is added, update the README table, `test_preflight.py`'s expected dict and `test_exitcode_agreement.py` together.
- Flag table: must equal `pc_flags.render_flag_table_markdown()`; the new `--claude` and budget flags belong to the driver, so document them in a README driver section, not in the `pc_flags` table, unless `pc_flags` changes. No cost figure or package-manager command may appear in the README (`test_the_readme_gives_no_cost_figure_and_no_package_manager_command`, 257); keep the 2 USD figure out of it.
- Hygiene tests (300-322): no absolute path, home path, temp path, email, or this machine's host name in the README.
- Section order is pinned: Run this first, Environment knobs, The stub, Exit codes, Layout, Limits (293). Add the driver section inside that order.
- `data/` is the only subfolder (283); keep new data flat.

---

### `test_allowlist.py` / `pc_allowlist.py` MODIFY (finding C5)

`test_the_corpus_has_the_measured_size` (245-252) pins 336 calls, 32 traces, 22 folders; the refusal split test pins 47/34/6 and 87. `load_trace_calls(repo_root)` (pc_allowlist.py 317) walks all of `tests/evidence`. Scope it to `tests/evidence/publication-2026-10-20` (recommended) so filing the new folder leaves the numbers intact; otherwise update the numbers after reading the new corpus entries.

---

## Shared Patterns

### Exclusive creation, never delete
**Source:** `pc_runroot.py` 59-105 (`allocate_run_root`, `exclusive_dir`, `write_exclusive`).
**Apply to:** every file the driver writes under the run root and every evidence file.
```python
os.mkdir(path, 0o700)                      # FileExistsError -> RunRootCollision (exit 16)
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
```
No deletion primitives outside test utilities.

### Zero-claude-before-spend ordering
**Source:** `pc_spike.run_s1` 1368-1438.
**Apply to:** the driver's real-run path. Guard, strict preflight, run root, pessimistic ledger line, call, reconcile, assertions, sanitise, promote. Dry run and all tests never reach the call.

### Sanitise, gate, promote with deny entries
**Source:** `pc_spike.sanitize_to_data`, `pc_promote.promote`, `pc_sanitize.Sanitizer.from_machine`.
**Apply to:** all evidence output. Build the sanitizer once, before spend; pass `sanitizer.deny_entries()` to `promote`; add a test that fails when a sanitised run is promoted without them (WR-14). Messages carry counts and rule ids only, never values.

### Neutral vocabulary, counts not values
**Source:** `pc_leakgate.format_findings`, `pc_spike._infra_lines`.
**Apply to:** all printed text, harness-authored evidence files, and the comparer. No PASS or FAIL word per row; no model prose in checklists.

### Isolation and pinned argv
**Source:** `pc_flags.build_argv` / `build_env` / `build_allowed_tools` / `render_settings`, `pc_spike.ensure_config_dir`, `runs_root`.
**Apply to:** all three stages. Strict isolation, `--setting-sources project,local`, `--permission-mode default`, never `--dangerously-skip-permissions`, one full model id (`pc_flags.PINNED_MODEL`), runs root outside every home folder.

### Test conventions
**Source:** `test_spike.py` (`run_cli`, `scratch`, `cli_env`, `make_repo`), `pc_testutil.py` (`make_fake_claude`, `make_tripwire`, `minimal_env`, `git_env`).
**Apply to:** every new `test_*.py`. Standard library `unittest`, no network, no real `claude`, git env hygiene via `pc_testutil.git_env`, shim strips `claude` directories from PATH (`selftest`).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Read-only structural comparer between two evidence trees | utility | transform | No existing code diffs two trees; `pc_mine` reads one committed tree at a time, so only its parsers and `pc_manifest.jsonl_bytes` are reusable (partial match). |
| Trace and README renderers for the per-row file set | utility | transform | The committed traces were produced by gitignored shell scripts; only the reader `pc_mine.parse_trace` documents the shape. Write renderers to match it and test against the committed row 1 files. |

## Metadata

**Analog search scope:** `tests/harness/` (all 52 tracked files, 17 read in part), committed `tests/evidence/publication-2026-10-20/row1-wrong-binding` file list, `03-CONTEXT.md`, `03-RESEARCH.md`.
**Files scanned:** about 25 read or grepped.
**Pattern extraction date:** 2026-10-28
**Tracked-source gate:** all named analogs confirmed tracked; no gitignored mirror paths used. The gitignored `runs/` scripts cited in RESEARCH are deliberately not named as analogs.
