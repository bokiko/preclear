# Phase 4: Full Matrix, Row 7 and Review - Pattern Map

**Mapped:** 2026-11-01
**Files analyzed:** 27 (11 new, 16 modified)
**Analogs found:** 27 / 27 (all analogs are git-tracked files under `tests/harness/`)

Line numbers refer to the working tree at mapping time. Facts beyond the excerpts (per-row seeds, allowlist sizes, prompts) live in `04-RESEARCH.md`, section "The twelve rows and three layouts"; this file only says which code to copy.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/harness/pc_rows.py` (modify: registry, RowSpec gains seed, hooks, allowlist extras, expectations) | config/registry | transform | itself, `build_registry` (lines 135-160) | exact |
| `tests/harness/pc_row1.py` (modify: generalise stage engine) | service | request-response (process per stage) | itself, `run_row` / `run_stage` (lines 767-913, 1120-1184) | exact |
| `tests/harness/pc_rowseeds.py` (new: plain, git-shaped, helper-backed seeds) | service | file-I/O | `pc_row1.seed_row1` (lines 212-337) | role-match |
| `tests/harness/pc_checks.py` (modify: snapshot and stage tuples, git_state for no-.git) | utility | transform | itself, lines 55-58, 1811-1851, 2022-2030 | exact |
| `tests/harness/pc_evidence.py` (modify: per-row promote, top-level add-files, row-generic renderers) | service | file-I/O | itself, `file_row`, `file_skipped` (lines 1281-1322) | exact |
| `tests/harness/pc_matrix.py` (modify: `--all` loop, budget, `_usable_run_folder`) | controller | batch | itself (lines 559-585, 745-853) | exact |
| `tests/harness/pc_review.py` (new: checkpoint parser, Do-not-redo candidates, HARN-10 counts, id join) | utility | transform | `pc_checks.py` pure analyses plus `pc_stream.tool_calls` (lines 229-243) | role-match |
| `tests/harness/pc_baseline.py` (new: digest table, usage totals, review brief, comparer report) | service | batch / file-I/O | `pc_evidence.render_folder_readme` (line 909) and `pc_compare.report_lines` (line 542) | role-match |
| `tests/harness/pc_cleanclone.py` (new: bootstrap) | service | batch | `pc_spike.py` (runs-root and env handling) and `tests/harness/selftest` | partial |
| `tests/harness/git-wrapper` (new bash 3.2 wrapper, row 11) | middleware | event-driven | `tests/harness/checkpoint-wrapper` | exact |
| `tests/harness/data/*.md` (new plain-row and layout s1 prompts, plain plan) | config/data | file-I/O | `tests/harness/data/row1-s1-prompt.md`, `row1-plan.md` | exact |
| `tests/harness/pc_allowlist.py` (modify: per-row allowlist, open-world write rule kept) | utility | transform | itself, `row_rules` (line 315) | exact |
| `tests/harness/pc_flags.py` (modify: `_MAX_BUDGET`, `format_budget`, per-row tools) | utility | transform | itself (lines 113, 256-279) | exact |
| `tests/harness/pc_spend.py` (modify: campaign-scoped keys, retry authorisations) | service | CRUD (append-only ledger) | itself, `authorize_retry` (line 394), `ROW_CAP` (line 40) | exact |
| `tests/harness/pc_preflight.py` (modify: chmod probe precondition) | utility | request-response | itself, plus `pc_evidence.file_skipped` | role-match |
| `tests/harness/pc_compare.py` (modify: configurable reference, D-15) | utility | transform | itself (`main`, line 579) | exact |
| `tests/harness/pc_exitcodes.py` (no new family; chmod probe reuses `PREFLIGHT_SKIP` 10) | config | n/a | itself | exact |
| `tests/harness/README.md` (modify: RERUN-05, cost figure, new files) | docs | n/a | itself, checked by `test_readme.py` | exact |
| `tests/harness/test_row_generic.py` and one `test_<module>.py` per new module (new) | test | scripted-claude | `test_stages.py` with `pc_testutil.RowRig` | exact |
| `tests/harness/test_frozen_baseline.py` (new: new baseline frozen except one README line per row, D-14) | test | file-I/O | `tests/harness/test_frozen_tree.py` | exact |
| `tests/harness/test_matrix_cli.py` (modify: `--list` implemented flags, 21 lines) | test | request-response | itself (lines 117-142, 201-220) | exact |
| `tests/harness/test_bash_shims.py` (modify: `EXPECTED_SHIMS`, add `git-wrapper`) | test | n/a | itself (line 33) | exact |
| `tests/harness/test_readme.py` (modify: README may hold no cost figure, now required) | test | n/a | itself (lines 257-297) | exact |
| `tests/harness/test_allowlist.py` and `test_stages.py` (modify: size 40 assertion at `test_stages.py` argv test) | test | n/a | themselves | exact |
| `tests/acceptance.md`, `CHANGELOG.md` (pointer paragraphs only, D-17) | docs | n/a | existing sections in each | exact |
| `tests/evidence/rerun-<date>-<model>/` top-level `row7-review.md`, `codex-review.md`, review brief | evidence | file-I/O | `pc_evidence.render_folder_readme` plus `file_skipped` staging | role-match |

## Pattern Assignments

### `tests/harness/pc_rows.py` (registry, transform)

**Analog:** itself. New rows are more `RowSpec` entries in `build_registry` (lines 135-160), each with `implemented=True`, a stage tuple, a `"module:function"` runner and a `sources` tuple of `(repo-relative path, "file"|"dir")` pairs.

**Stage tuple pattern** (lines 117-122):
```python
_ROW1_STAGES: Tuple[StageSpec, ...] = (
    StageSpec("s1", WORK_TURN, "work", 15, Decimal("0.30"), 900, "new:A"),
    StageSpec("s2", PRECLEAR_TURN, "preclear", 60, Decimal("1.30"), 1800, "resume:A"),
    StageSpec("s3", FRESH_RESUME, "resume", 15, Decimal("0.40"), 900, "new:B"),
)
```
Row 12 adds an s4 with session `resume:B` (RESEARCH Pitfall 13: it resumes the s3 session, not s2's). Caps stay 0.30/1.30/0.40 (D-04).

**Registry branch to extend** (lines 143-160): replace the `if identifier == ROW1 ... else RowSpec(..., (), False, None, None, ())` with a lookup in a dict of specs; layouts (lines 137-138) get the same treatment. `precondition` is a zero-argument callable returning a reason or None. Row 7's precondition must stay write-free (return a reason only when `os.geteuid() == 0`), because `--dry-run` creates nothing.

**Ledger key** (lines 202-206): `stage_key` returns `row_id.split("-", 1)[0] + "-" + stage_name`; keep it, but add a campaign label parameter for reruns (RESEARCH summary item 3). `evidence_folder_name` (lines 209-224) also has no label parameter today.

### `tests/harness/pc_row1.py` (stage engine, request-response)

**Analog:** itself. The chain loop to generalise (lines 1156-1183) dispatches on `stage.kind` in `work`/`preclear`/`resume`. Keep the order of refusals before spend: destination exists (exit 17), run root, sanitizer (15), ledger read, seed, setup snapshot.

**Refusal-first opening** (lines 1129-1142) to keep verbatim for every row, with `ROW_ID` replaced by the entry's id:
```python
if os.path.lexists(ctx.destination):
    return pc_rows.RowOutcome(pc_exitcodes.PROMOTE_REFUSED, (MESSAGE_DESTINATION,))
run_name = "%s-%s" % (ROW_ID, _utc_now().strftime("%Y%m%dT%H%M%SZ"))
pc_spike.ensure_runs_root(ctx.runs_root)
run_root = pc_runroot.allocate_run_root(ctx.runs_root, run_name)
...
ctx = ctx._replace(run_root=run_root, sanitizer=sanitizer, deny_entries=deny_entries)
pc_spend.read_records(ctx.harness_home)
```
Multi-row filing means `destination` is the dated folder and the per-row target is `<dated>/<row>`; the existing-destination test moves to the row folder (RESEARCH item 2).

**Between-stage hooks and snapshots.** Row 7 needs a `chmod 555` step after s1 and snapshot `snap-1b-after-restriction`; row 12 needs `snap-2b-after-external-plan-edit` and an s4. Replace the fixed `SNAPSHOT_NAMES` dict (lines 76-80) with a per-row mapping from the spec.

**Breach and finish patterns to reuse unchanged** (`breach_outcome` lines 1060-1078, `finish` lines 1081-1117): counts only, exit 11 for isolation or git breach, then `pc_evidence.file_row`. The `len(results) == 2` branch printing `stage s3: not run (NO-RESUME-LINE)` is row-shape specific; row 7 prints no resume line by design, so its chain must build the s3 prompt from the printed checkpoint (D-05), not stop.

**Resume-line extraction** (lines 939-958, `extract_resume_line`): generic, reuse for every `preclear` stage. Row 7 needs a second extractor in `pc_review.py` for the printed checkpoint (fenced block parser; see RESEARCH "Fence scanner and Do-not-redo entries", lines 621-663).

---

### `tests/harness/pc_rowseeds.py` (new, file-I/O)

**Analog:** `pc_row1.seed_row1` (lines 212-337): bound-ledger fixture copy, config fill, two ledgers, stub `bind`, hook settings, `raw/run.json`. All seeds must create the same top-level names so `paths_for` (lines 340-372) stays generic, including an empty `ckpt/ledgers` (snapshot code calls `os.listdir`). Note `pc_seeds.py` holds only leak-shaped test strings and is exempt from the no-delete scan by name; do not add fixture materialisation there (RESEARCH structure note). Deletion primitives stay out of the new module (static scan in `test_runroot.py` lines 334-338).

**Run-root creation primitives to use:** `pc_runroot.exclusive_dir`, `pc_runroot.write_exclusive`, `allocate_run_root` (exclusive creation only).

---

### `tests/harness/pc_checks.py` (modify, transform)

**Analog:** itself. Lines 55-58 hold the tuples that filter silently:
```python
APPROVED_ROOTS = ("project", "ckpt", "auto-memory")
SNAPSHOT_ORDER = ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume")
STAGE_NAMES = ("s1", "s2", "s3")
```
Change them so an unknown snapshot or stage record is an error, not ignored (RESEARCH Pitfall 1), and add a test that row 7 and row 12 extra snapshots are read. `git_state` (lines 1811-1851) uses `gitdir_digest(project)` which needs a `.git` folder: rows 8a (none) and 9 (a file) need a branch. `_watched` (lines 2022-2030) names ledgers A and B; rows without ledgers report nothing to compare.

---

### `tests/harness/pc_evidence.py` (modify, file-I/O)

**Analog:** `file_skipped` (lines 1281-1322), the model for per-row promote into `<dated>/<row>` and for the SKIPPED label (D-08, HARN-02).

**Core pattern** (excerpt of lines 1303-1322): deny-entries check first, validate id, stage into a run-root folder, sanitize, then `pc_promote.promote(stage, target, ...)` and map the code:
```python
if deny_entries is None:
    return pc_rows.RowOutcome(pc_exitcodes.SCANNER_ERROR, (MESSAGE_NO_DENY_ENTRIES,))
if not pc_rows.is_valid_id(row_id):
    return pc_rows.RowOutcome(pc_exitcodes.PREFLIGHT_FAIL, (MESSAGE_SKIP_ROW,))
...
target = os.path.join(destination, SKIPPED_PREFIX + row_id)
result = pc_promote.promote(stage, target, repo_root, config_dir=config_dir, deny_entries=deny_entries)
if int(result.code) != pc_exitcodes.OK:
    return _outcome(result, target, 0)
return pc_rows.RowOutcome(
    pc_exitcodes.PREFLIGHT_SKIP,
    ("filed: %s/%s%s, 1 file(s); no session was run" % (os.path.basename(destination), SKIPPED_PREFIX, row_id),),
)
```
Row-1 specifics to parameterise (all use `pc_rows.ROW1`): `_SETUP_TEXT` (line 90), `render_row_readme` (877), `render_usage` (260), `render_mechanical_checks` (699), `render_folder_readme` (909), `collect_files` (1122), `harness_authored_names` (1102), `_chain_incomplete` (1059), `STAGE_LABELS`/`SNAPSHOT_OF` (49-53). Every row README must still end `Reviewer verdict: PENDING`. Add one "add files into an existing folder, exclusively, gate first" primitive for `row7-review.md`, the digest table, `codex-review.md` and the review brief. The `Reviewer verdict` replacement (D-14) is made by a person or on bokiko's word, not by harness code.

---

### `tests/harness/pc_matrix.py` (modify, batch)

**Analog:** itself. `--all` flow (lines 745-853): select implemented entries, gates for every chosen row, `_check_budget(args.budget, needed)`, one `RunContext`, loop returning at the first non-zero code. Changes needed:
- A SKIP or failed row must not end the whole matrix (D-02): record it and continue; the final exit code still must not read as pass (HARN-02).
- `_usable_run_folder` (lines 559-585) accepts only `record.get("row") == pc_rows.ROW1`; generalise for `--refile`.
- `_check_budget` and `pc_flags.format_budget` (`_MAX_BUDGET = Decimal("5.00")`, lines 113 and 256-279) cannot express 21 chains at 2.00; per-wave budgets with the typed go word (D-01) replace the matrix-wide rule.
- Order: layouts, then rows in acceptance order (D-12), which already matches `build_registry`.
- `list_lines` prints `-` for stages and `no` for unimplemented rows; a skipped or failed attempt needs a defined appearance (Claude's discretion).

---

### `tests/harness/git-wrapper` (new, event-driven, bash 3.2)

**Analog:** `tests/harness/checkpoint-wrapper`. Copy these structural elements:

**Header contract and configuration check** (lines 1-40):
```bash
W="$(cd "$(dirname "$0")" && pwd)"
PY=""
STUB=""
[ -f "$W/py" ] && PY=$(cat "$W/py")
...
if [ -z "${PY// /}" ] || [ -z "${STUB// /}" ]; then
  echo "checkpoint-wrapper: not configured" >&2
  exit 70
fi
real() { "$PY" -I -B "$STUB" "$@"; }
stamp() { date -u +%FT%TZ; }
```
**Logging every call, then an armed counter that gates injection** (lines 62-114): `printf ' %q' "$@" >> "$W/calls.log"`, `if [ -f "$W/armed" ] ...`, counter decrement, injection output sent to `injection.log`, never to the caller; final `real "$@"; rc=$?; printf '%s EXIT %s\n' ...; exit $rc`.

**Row 11 differences** (design in `04-RESEARCH.md` "Git wrapper core", lines 664-703): the injection fires only when the whole argv equals the stored `match-argv` (Claude Code's own git calls carry a `-c ...` preamble, so they never match), on the n-th match counted through a one-line O_APPEND `matches.log`, guarded by `mkdir fired.lock`. A no-op session leaves `matches.log`, `fired.lock` and `injection.log` absent. The wrapper must be transparent (Pitfall 14): same stdout, stderr and exit code as real git, injection after the real call as in the committed run. The wrapper does not know `tool_use` ids; they are joined later from the stream with `pc_stream.tool_calls` (lines 229-243) in `pc_review.join_ids`. Ledger of parallel git calls: Pitfall 8 (single-write log lines).

Add the new file to `EXPECTED_SHIMS` in `test_bash_shims.py` (line 33) and name it once in `README.md` (`test_readme.py` lines 266-297). Committed reference run for the injector: `tests/evidence/publication-2026-10-20/row11-concurrent-change-rerun/` (`git-calls.log`).

---

### `tests/harness/pc_review.py` (new, transform)

**Analog:** pure analyses already in `pc_checks.py` (`_tokens`, argv splitting via `pc_allowlist.split_compound`) and `pc_stream.tool_calls`. Pattern: functions take parsed events or text and return counts and candidate lists, never a verdict (EVID-05). Fixed-text output lines with ids and counts only, no paths. Row 7 Do-not-redo candidates (D-06): for each entry, list `tool_use` ids of the same `/preclear` turn whose input or output shares a file path or exact token; print `UNSUPPORTED` when none. Row 10 counts (HARN-10): executed `-z` redirects (expect 0), quoted form executed (expect at least 1), NUL bytes in the sidecar (expect 0). Sample code for these lives in `04-RESEARCH.md` (Code Examples, lines 621-704).

---

### `tests/harness/pc_baseline.py` (new, batch / file-I/O)

**Analog:** `pc_evidence.render_folder_readme` (line 909) for deterministic README-style text with fixed wording, and `pc_compare.report_lines` (line 542) for the comparer report. The digest table uses `pc_compare.tree_digest` (line 115). Costs come from per-row `usage.txt` (cumulative-consistent ledger lines; never recompute). Files are written through the new exclusive add-files primitive after the sanitizer and leak gate.

---

### `tests/harness/pc_cleanclone.py` (new bootstrap, batch)

**Analog:** partial. Reuse `pc_spike.ensure_runs_root` and the `selftest` bash shim style (bash 3.2, `env -i` allowlist). RESEARCH item 5 corrects D-09/D-10: `pc_spike.runs_root` refuses a runs root containing the repository, so the clone cannot sit under it; the config folder derives from `PRECLEAR_HARNESS_HOME` not `CLAUDE_CONFIG_DIR`; a throwaway `HOME` may hide the Keychain login (one zero-token probe by bokiko decides). Environment names (never values) are recorded; both helper-unreachable facts (before and after) are counts in the folder README. Minimal-env reference for tests: `pc_testutil.minimal_env` (line 141) and `RowRig.env` (lines 716-722).

---

### `tests/harness/pc_preflight.py` / `pc_rows` precondition (chmod probe, HARN-12)

**Analog:** design sketch in `04-RESEARCH.md` line 599 onward. Pattern: probe inside the run root at `raw/probe-chmod/` before `capture_guard`, `pc_runroot.exclusive_dir(probe, 0o700)`, `os.chmod(probe, 0o555)`, then `pc_runroot.write_exclusive`; only `PermissionError` with `errno.EACCES` counts as effective. Anything else files `SKIPPED-row7-all-destinations-denied` through `pc_evidence.file_skipped` and returns exit 10. No new exit code. Never use `os.remove`/`os.unlink` (static scan).

---

### `tests/harness/test_row_generic.py` and per-module tests (new, scripted-claude)

**Analog:** `tests/harness/test_stages.py` with `pc_testutil.RowRig` and the scripted fake claude (`make_scripted_claude`, `default_row1_stages`, `stages_with`, seed helpers at `pc_testutil.py` lines 449-660).

**Imports and lazy module access** (`test_stages.py` lines 1-50): modules imported inside small accessor functions so a missing module is one error per test, not a load failure:
```python
def row1():
    import pc_row1
    return pc_row1
```
**Run helper** (lines 60-80): `Run(stages=..., timeout_override=...)` builds `RowRig`, `ctx = rig.context()`, calls the runner, exposes `run_root`, `raw(name)`, `ledger()`.

**Assertions to copy** (lines 80-125): argv by index (`--session-id`, `--resume`, `--max-turns`, `--max-budget-usd`), ledger launch/settle pairs in order, snapshot folder names, output lines matched against a fixed regex with no base path or session id echoed. New rows replace the `len(...) == 40` allowlist assertion with a per-row size (RESEARCH Pitfall 9) and extend the line regex for new stage names. Every paid path is tested through the fake `claude`; the tripwire (`make_tripwire`, line 100) proves the self-test never starts a model.

---

### `tests/harness/test_frozen_baseline.py` (new, file-I/O)

**Analog:** `tests/harness/test_frozen_tree.py` (pinned constants at lines 37-42, `tree_digest` via `pc_compare` at lines 55-56): pinned sha256 per tree, failure messages name which tree differs but never a path. The new test pins the new baseline folder but must exclude exactly the one `Reviewer verdict:` line per row README (D-14); any other byte change fails. `PUBLICATION_TREE_SHA256` for the 2026-10-20 folder stays as is; after D-15 it is labelled superseded in the top-level evidence README, which is outside that tree.

---

### `tests/harness/test_matrix_cli.py`, `test_readme.py`, `test_bash_shims.py` (modify)

Change on purpose (RESEARCH Pitfall 9): `test_only_row_one_is_implemented_with_its_three_stages` (line 128) flips per row as rows land; `test_the_list_has_a_header_and_twenty_one_fixed_column_lines` (line 201) stays 21; `test_the_readme_gives_no_cost_figure_and_no_package_manager_command` (line 257) must allow the RERUN-05 cost figure; `EXPECTED_SHIMS` (line 33) gains `git-wrapper` (and the bootstrap if bash). Test count must not drop.

---

## Shared Patterns

### Exit codes and outcomes
**Source:** `tests/harness/pc_exitcodes.py` (lines 40-60) and `pc_rows.RowOutcome(code, lines)`.
**Apply to:** every new runner, probe, bootstrap and filing function. SKIP is 10 and never counts as OK; breach is 11; leak 14; scanner 15; collision 16; promote refused 17; budget 18; denial 19. A skipped row, a failed attempt and a retry attempt each keep their label and exit code (D-02, D-03). Messages are fixed text with ids and counts only, never a path or argument value. `test_exitcode_agreement.py` and the README table test enforce agreement.

### Exclusive creation, no deletion
**Source:** `pc_runroot.allocate_run_root`, `exclusive_dir`, `write_exclusive`; `pc_promote.promote` with `deny_entries`.
**Apply to:** all new files in run roots and evidence. Nothing renames, truncates or deletes; static scan in `test_runroot.py` lines 334-338 and `test_imports.py` lines 250-256 (only `pc_testutil.py` and `pc_seeds.py` are exempt).

### Sanitise, leak-gate, then exclusive write
**Source:** `pc_evidence.file_skipped` (lines 1303-1322), `pc_sanitize.Sanitizer.from_machine`, `caller_map` (`pc_row1.py` lines 969-992).
**Apply to:** `row7-review.md`, digest table, review brief, per-row READMEs, the SKIPPED label. Deny entries `None` is refused with 15 before anything is made.

### Spend ledger discipline
**Source:** `pc_spend.append_launch` (315), `settle` (356), `authorize_retry` (394), `row_total` (480); `ROW_CAP` = 2.00.
**Apply to:** every stage in every row. Reserve before the process, settle after; `total_cost_usd` on a resumed call is cumulative and the ledger records per-stage deltas. A retry is a new attempt folder (D-03) legalised through a campaign label or `authorize_retry`, never by editing the ledger (RESEARCH Pitfall 5).

### Zero-token test rig
**Source:** `pc_testutil.RowRig` (line 696), `make_scripted_claude` (413), `make_tripwire` (100).
**Apply to:** every new test of a paid path. Scratch folders are never deleted; no real home, host or login name in test text; leak-shaped strings only through `pc_seeds.py` functions.

### Frozen trees
**Source:** `test_frozen_tree.py`, `test_frozen_reference.py`.
**Apply to:** nothing in this phase edits `SKILL.md`, `references/`, `tests/fixtures/` or `tests/evidence/publication-2026-10-20/`; the only post-filing edit of the new baseline is the D-14 verdict line.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Review brief for Codex (D-16) | docs/evidence | file-I/O | No existing generated brief; use `render_folder_readme` style, content per D-16 |
| `row7-review.md` (D-07) | evidence | file-I/O | No multi-attempt review table exists; planner follows D-06/D-07 and RESEARCH "Row 7" section |
| Clean-clone bootstrap `env -i` runner | script | batch | Only the `selftest` shim style and `pc_spike` runs-root rules exist; design is in RESEARCH item 5 |

## Metadata

**Analog search scope:** `tests/harness/` (71 tracked files), `tests/evidence/publication-2026-10-20/` (references only).
**Files scanned:** about 20 read in part, plus RESEARCH and CONTEXT.
**Pattern extraction date:** 2026-11-01
**Tracked-source check:** `git ls-files --error-unmatch` passed for `pc_row1.py`, `checkpoint-wrapper`, `test_frozen_tree.py`, `pc_compare.py`; the other analogs are in the same tracked folder.

## PATTERN MAPPING COMPLETE
