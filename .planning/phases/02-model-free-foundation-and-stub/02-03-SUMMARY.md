---
phase: 02-model-free-foundation-and-stub
plan: 03
subsystem: testing
tags: [python-stdlib, unittest, run-root, manifest, sha256, byte-measurer, tdd]

requires:
  - phase: 01-publication-hardening
    provides: "hooks, gitleaks identifier rules and the frozen evidence shapes (sha.txt, measurements.md) this plan reproduces"
provides:
  - "pc_runroot: exclusive run-root allocator (exit 16 on collision), exclusive_dir, write_exclusive, copy_tree_exclusive"
  - "pc_manifest: byte-walk tree_manifest with refuse_under, escape_name, sha_txt_bytes, jsonl_bytes, write_snapshot, capture_git_status, GIT_ENV_OVERRIDES"
  - "pc_measure: heading-inclusive UTF-8 measurer printing actual/cap per section and total"
  - "A static AST scan (with its own positive and negative self-tests) proving no pc_ module deletes, renames, moves or overwrites"
affects: [02-05 sanitizer and leak gate, 02-07 exit-code agreement, 02-08 run-root materialiser, 03 matrix driver, 04 evidence comparison]

actuals:
  tokens: 21900
  tasks: 3
  commits: 6
plan_head_before: c3c615305b83d704d64fa3080c57046176405ce5
plan_head_after: a37a73c54cde82de13298c00bb5a0c594004a4da

tech-stack:
  added: []
  patterns:
    - "Creation only: os.mkdir without exist_ok and os.open with O_CREAT|O_EXCL|O_NOFOLLOW; collisions are errors, never reuse"
    - "Raw-byte walks (os.walk on bytes) sorted by relative path bytes; names carried as bytes and decoded only with surrogateescape"
    - "Facts-only reports: actual/cap with an over-by figure, exit 0 for any readable file"
    - "Static AST scan of every harness module for delete and overwrite constructs, with scanner self-tests so the scan cannot go silently blind"

key-files:
  created:
    - tests/harness/pc_runroot.py
    - tests/harness/pc_manifest.py
    - tests/harness/pc_measure.py
    - tests/harness/test_runroot.py
    - tests/harness/test_manifest.py
    - tests/harness/test_measure.py
  modified: []

key-decisions:
  - "A name with a trailing separator is refused as an invalid name (exit 2); the collision form is a parent given with a trailing separator or through a symlink (exit 16)"
  - "escape_name returns (text, escaped); non-UTF-8 name bytes are carried through with surrogateescape so sha.txt can hold the raw bytes"
  - "format_report(None, m) omits the heading line so its first line is the total line; the CLI passes the path as the label"
  - "copy_tree_exclusive validates the whole source before creating the destination, so a refusal leaves nothing behind"
  - "The no-delete scan treats a one-argument .replace(...) as Path.replace and a two-argument one as str.replace or bytes.replace"

patterns-established:
  - "Messages in tests carry labels only (assertTrue with a label), never a path value"
  - "Awkward names are built from code points and bytes at run time; test sources stay ASCII"
  - "Filesystem limits skip with a printed reason, at most one skip per limit, while an in-memory twin proves the logic"

requirements-completed: [HARN-03, HARN-08, EVID-01]

coverage:
  - id: D1
    description: "Run roots are allocated exclusively: existing directory, file, symlink (dangling too) and symlinked or trailing-separator parent are RunRootCollision; invalid names and a missing parent are refused before anything is created; the CLI exits 0, 16 or 2"
    requirement: HARN-03
    verification:
      - kind: unit
        ref: "tests/harness/test_runroot.py#AllocateRunRootTests, InvalidNameTests, ExclusiveHelperTests, CliTests"
        status: pass
      - kind: other
        ref: "tests/harness/pc_runroot.py first call exits 0, second call of the same name exits 16 (plan verify command)"
        status: pass
    human_judgment: false
  - id: D2
    description: "copy_tree_exclusive copies a tree exclusively, keeps the executable bit, and refuses an existing destination, a symlink or special file in the source and a symlinked source root"
    requirement: HARN-03
    verification:
      - kind: unit
        ref: "tests/harness/test_runroot.py#CopyTreeExclusiveTests"
        status: pass
    human_judgment: false
  - id: D3
    description: "A static AST scan of every pc_ module except the two test-support modules finds no delete, rename, move, overwrite or truncating-write construct, the exemption set is exactly {pc_testutil.py, pc_seeds.py}, and the scanner is itself proven to flag each forbidden construct"
    requirement: HARN-03
    verification:
      - kind: unit
        ref: "tests/harness/test_runroot.py#NoDeleteOrOverwriteScanTests, ModuleSurfaceTests"
        status: pass
    human_judgment: false
  - id: D4
    description: "Snapshots survive newline, carriage-return, backslash, CJK, emoji and right-to-left names: sha.txt keeps the committed shape with injective sha256sum-style escapes, manifest.jsonl round-trips every name including a lone surrogate, entries are sorted by raw bytes, an empty tree gives zero-byte files, a missing root raises"
    requirement: HARN-08
    verification:
      - kind: unit
        ref: "tests/harness/test_manifest.py#EscapeNameTests, TreeManifestTests, ShaTxtTests, JsonlTests, WriteSnapshotTests, OrderingAndDeterminismTests, LoneSurrogateTests, AdjacencyTests, EmptyAndZeroByteTests, OtherKindsTests, CliTests"
        status: pass
    human_judgment: false
  - id: D5
    description: "capture_git_status returns the raw NUL form and the plain text form from only no-optional-locks status, leaves the repository index bytes unchanged, and raises on a failing status; tree_manifest refuses a root at or under a refuse_under path (component-aware, symlink-aware)"
    requirement: HARN-08
    verification:
      - kind: unit
        ref: "tests/harness/test_manifest.py#GitStatusCaptureTests, RefuseUnderTests"
        status: pass
    human_judgment: false
  - id: D6
    description: "The measurer reports per-section and total UTF-8 bytes including headings as actual/cap, matches hand-computed ASCII, two-, three-, four-byte and CRLF fixtures, agrees with file size and wc -c, reads the file once, prints facts and never a verdict, and its constants equal SKILL.md's Schema table"
    requirement: EVID-01
    verification:
      - kind: unit
        ref: "tests/harness/test_measure.py#AsciiFixtureTests, MultibyteFixtureTests, CrlfFixtureTests, PreambleAndOtherTests, ReportTests, SchemaConstantsTests, StaticShapeTests"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-10-25
status: complete
---

# Phase 2 Plan 03: Run-root, manifest and measurer primitives Summary

**Exclusive run-root allocator (exit 16 on collision), newline- and non-Latin-safe byte-walk manifests with a lossless JSON-lines companion and read-only git status capture, and a heading-inclusive UTF-8 byte measurer printing actual/cap, all standard-library Python 3.9 with 108 passing tests and zero model calls.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-25T13:55:18Z
- **Completed:** 2026-10-25T14:07:00Z
- **Tasks:** 3
- **Files modified:** 6 (all new, under `tests/harness/`)

## Accomplishments

- `pc_runroot.py`: `allocate_run_root` validates the name and parent, then makes one `os.mkdir` call with no `exist_ok`; `write_exclusive` uses `O_CREAT|O_EXCL|O_NOFOLLOW`; `copy_tree_exclusive` validates a whole source tree before creating a new destination. The CLI exits 0 (prints the realpath), 16 on collision, 2 on a bad name, missing parent or bad usage.
- `pc_manifest.py`: in-process byte walk (never splits a name on a newline, no external listing command), sorted by raw path bytes; `sha.txt` keeps the committed shape and writes names needing escapes with a leading backslash and backslash escapes; `manifest.jsonl` round-trips every name, including a lone surrogate built in memory; `capture_git_status` returns the raw NUL form and the plain text form from `--no-optional-locks status` only; `tree_manifest` refuses a root at or under any `refuse_under` path.
- `pc_measure.py`: per-section and total UTF-8 bytes including headings as `actual/cap` (800, 600, 500, 600, 1000, 596 and 4096), preamble and other rows, an over-by figure instead of a verdict, one read of the original bytes per file, exit 0 for any readable file.
- A static AST scan keeps every `pc_` module free of delete, rename, move, copy-overwrite and truncating-write constructs. The scanner has its own tests for every forbidden construct and for the constructs the harness may use, so it cannot silently stop seeing violations.
- 108 tests pass under both the PATH Python (3.14) and the system Python 3.9.6, 3 skipped (one per filesystem limit, each with its reason printed).

## Task Commits

Each task followed RED, then GREEN. No REFACTOR commit was needed.

1. **Task 1 (tracer): exclusive allocator and snapshot manifest**
   - RED `1d90a71` (test): failing tests for the allocator and the manifest
   - GREEN `8ec7921` (feat): allocator, tree manifest, sha.txt and manifest.jsonl writers
2. **Task 2: heading-inclusive byte measurer**
   - RED `cfb81f8` (test): failing measurer tests with hand-computed fixtures
   - GREEN `efc4dc3` (feat): `pc_measure.py`
3. **Task 3: hardening**
   - RED `b03d807` (test): failing tests for tree copy, git status capture, refuse-under and the no-delete scan
   - GREEN `a37a73c` (feat): `copy_tree_exclusive`, `capture_git_status`, `refuse_under`

**Plan metadata:** the docs commit that adds this file follows the six commits above.

## Files Created/Modified

- `tests/harness/pc_runroot.py` - exclusive run-root allocation, exclusive file and tree creation, CLI with exit 16 on collision
- `tests/harness/pc_manifest.py` - byte-walk manifest, sha.txt and JSON-lines writers, read-only git status capture, refuse-under guard
- `tests/harness/pc_measure.py` - heading-inclusive byte measurer and CLI
- `tests/harness/test_runroot.py` - allocator, exclusive helpers, tree copy, CLI exit codes, static no-delete scan with self-tests
- `tests/harness/test_manifest.py` - names, ordering, determinism, adjacency, empty and zero-byte, git status in a temporary repository, refuse-under
- `tests/harness/test_measure.py` - hand-computed fixtures, report shape, SKILL.md schema comparison, static one-open check

## Decisions Made

- Trailing separator: see the interpretation noted under Deviations. A name with any separator, a trailing one included, is an invalid name (exit 2, nothing created). The collision form is a parent given with a trailing separator or reached through a symlink to an existing entry (exit 16).
- `escape_name` returns `(text, escaped)`. A name that is not valid UTF-8 is decoded with surrogateescape, so `sha_txt_bytes` can write the original raw bytes back and `jsonl_bytes` carries them through `os.fsdecode`.
- `format_report(None, measurement)` omits the heading line, so its first line is `total <N>/4096 bytes, sha256 <hex>`; the CLI passes the file path as the label, matching the committed `## <label>` shape.
- The new `.replace` rule in the scan: a call with fewer than two arguments is `Path.replace` and is flagged; two or more is `str`/`bytes` replace and is allowed. Plans 02-04 and later will need `str.replace` in the sanitiser.
- Stage folders and files are created owner-only (0o700 and 0o600); files copied by `copy_tree_exclusive` are 0o644 or 0o755 as the plan states, applied with `fchmod` so the umask cannot change them.
- `GIT_ENV_OVERRIDES` is exactly the four variables the plan names; `capture_git_status` also removes `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` from the copied environment and bounds each call with a timeout.

## TDD Gate Compliance

Plan frontmatter is `type: execute` with `tdd="true"` tasks, so each task ran RED then GREEN. Gate commits exist for every task (`test(02-03)` before `feat(02-03)` three times).

RED evidence was classified by `check tdd-red-evidence` (format: unittest) and returned `RED_EVIDENCE_OK` / `target_test_failed` five times:

| Task | Target test (failed on its planned assertion) | Semantic assessment |
|---|---|---|
| 1 | `test_runroot.CliTests.test_second_allocation_of_the_same_name_exits_16` | Skeleton CLI exited 0 on the second allocation; the planned assertion (exit 16) failed. 23 of 24 tests failed or errored, all on missing behaviour. |
| 1 | `test_manifest.ShaTxtTests.test_one_line_per_regular_file_and_no_name_is_split` | Skeleton returned zero bytes; one line per file expected. |
| 2 | `test_measure.ReportTests.test_a_file_of_4097_bytes_shows_over_by_1_and_still_exits_0` | Skeleton report was empty; `over by 1` expected. |
| 3 | `test_runroot.CopyTreeExclusiveTests.test_copies_a_tree_keeps_the_executable_bit_and_returns_the_file_count` | Skeleton returned `None`; 3 files copied expected. |
| 3 | `test_manifest.RefuseUnderTests.test_a_root_equal_to_a_listed_path_is_refused` | Skeleton ignored `refuse_under`; `ManifestError` expected. |

Notes on the RED steps:

- The RED commits include inert skeleton modules (right names and signatures, no behaviour), so the tests fail on assertions and not on an import error. Task 1 and Task 2 had three or fewer `ERROR` entries in total, all `TypeError`/`KeyError`/`FileNotFoundError` caused by the skeleton returning empty values; Task 3's RED run had zero errors.
- In Task 3 the static scan tests and the scanner self-tests passed at RED by construction: they guard code that already existed and the scanner lives in the test file. Only the new-behaviour tests were RED.
- RED evidence records were written under the gitignored `runs/` folder and are not committed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Inert skeleton modules in the RED commits**
- **Found during:** Task 1 (and repeated in Tasks 2 and 3)
- **Issue:** A test module that imports a module which does not exist fails at load time (`unittest.loader._FailedTest`), which the RED classifier rejects as `INVALID_RED`.
- **Fix:** Each RED commit also carries a skeleton of the module under test (names and signatures only, no behaviour), replaced by the real code in the GREEN commit. In Task 3 the skeleton added `refuse_under=()` to `tree_manifest` (ignored), `GIT_ENV_OVERRIDES = {}`, and stub `capture_git_status` and `copy_tree_exclusive`.
- **Files modified:** `tests/harness/pc_runroot.py`, `pc_manifest.py`, `pc_measure.py`
- **Verification:** `RED_EVIDENCE_OK` for all five targets above.
- **Committed in:** `1d90a71`, `cfb81f8`, `b03d807`

**2. [Rule 2 - Missing critical] Source files read without following a final symlink or blocking on a pipe**
- **Found during:** Task 3 (`copy_tree_exclusive`)
- **Issue:** The plan says to read each source file once; a plain `open` would follow a symlink swapped in after validation, or block on a pipe (threat T-02-14).
- **Fix:** `_read_regular` opens with `O_NOFOLLOW` and `O_NONBLOCK` and checks `fstat` for a regular file before reading.
- **Files modified:** `tests/harness/pc_runroot.py`
- **Verification:** `CopyTreeExclusiveTests` pass; the module-wide scan passes.
- **Committed in:** `a37a73c`

**3. [Rule 2 - Missing critical] Extra guards in the scan and in `refuse_under`**
- **Found during:** Task 3
- **Issue:** The plan's forbidden list did not name `os.truncate` or `os.ftruncate`, and an empty `refuse_under` entry would resolve to the current working folder and either refuse the wrong root or hide a bug.
- **Fix:** The scan also flags `os.truncate`/`os.ftruncate`; an empty `refuse_under` entry raises `ManifestError`.
- **Files modified:** `tests/harness/test_runroot.py`, `tests/harness/pc_manifest.py`
- **Verification:** scanner self-test and `test_an_empty_listed_path_is_refused...` pass.
- **Committed in:** `b03d807`, `a37a73c`

### Plan interpretations (no code deviation)

- **Trailing separator.** The plan says both that a name holding a path separator is refused before any directory is created, and that a name given with a trailing separator collides. These cannot both hold for one input. Implemented: a trailing separator on the name is an invalid name (`RunRootError`, exit 2); a trailing separator on the parent, or a symlinked parent, reaches the existing entry and raises `RunRootCollision` (exit 16). Both forms are tested. If the plan meant the first reading to win for names too, it is a one-line change in `_validate_name`.
- **Report first line.** The plan describes the report both as starting with a `## <label>` line and as having `total ...` as its first line. `format_report(label, m)` prints the heading when a label is given; the CLI always gives one (the file path).
- **Commit subject form.** The plan asks for one plain imperative sentence; the commits use `test(02-03): ...` / `feat(02-03): ...` followed by an imperative sentence, so the TDD gate commands that grep the commit scope also match. No trailer, no hook-skipping option.

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing critical) plus 3 interpretations
**Impact on plan:** All fixes serve the plan's own acceptance criteria and threat register (T-02-13, T-02-14, T-02-15). No scope creep.

## Issues Encountered

- This worktree's tool sandbox refused several compound shell commands that name git or loop over interpreters; they were split into plain commands. No effect on results.
- `gsd_run` is not a shell function in this runtime, so the RED classifier was run through the installed `gsd-tools.cjs` directly. The verdicts are the classifier's own output.
- Three filesystem-limit skips on this APFS volume, each with its reason printed: case-insensitive names, NFC versus NFD names, and non-UTF-8 file names (`EILSEQ`). The in-memory twin of each case runs and passes.

## Verification Results

- `python3 -I -B -m unittest discover -s tests/harness -t tests/harness -p 'test_*.py'`: Ran 108 tests, OK (skipped=3), under the PATH Python 3.14 and under the system Python 3.9.6.
- Run-root CLI: first allocation exits 0, second allocation of the same name exits 16.
- Measurer CLI prints a report for the committed `measurements.md` and for `SKILL.md` and exits 0 (those files are not checkpoints, so every heading shows as `(other)` with the six expected headings listed as missing, which is a fact and not a verdict).
- Frozen paths (`SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/`) show no difference from commit `56e155c`; `SKILL.md` is 11,994 bytes.
- No commit message in `git log --all` matches `.githooks/attribution.ere`.
- `gitleaks dir tests/harness --config .gitleaks.toml --no-banner --redact --exit-code 2 -l warn` exits 0 before each commit; the repository hooks also ran on every commit.
- Control experiment (not committed): with the tracked file made stat-dirty, a plain `git status` changes the temporary repository's index bytes and `capture_git_status` does not, so the index-digest test is sensitive.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. The inert skeletons exist only inside the RED commits and are replaced by the GREEN commits.

## Threat Flags

None. The only new process execution is `git --no-optional-locks status`, already covered by T-02-17.

## Next Phase Readiness

- Plans 02-05 (sanitiser, leak gate, promote), 02-07 (exit-code agreement) and 02-08 (run-root materialiser, snapshots) can import `allocate_run_root`, `exclusive_dir`, `write_exclusive`, `copy_tree_exclusive`, `tree_manifest`, `sha_txt_bytes`, `jsonl_bytes`, `write_snapshot`, `capture_git_status`, `measure_file` and `format_report` as documented above.
- `test_runroot` scans only the `pc_` modules present when it runs, so either completion order of plans 02-01 and 02-02 passes; once `pc_sanitize` and friends land they are scanned automatically, and they may use `str.replace` freely.
- Plan 02-07 compares the literal 16 in `pc_runroot.EXIT_COLLISION` with `pc_exitcodes` by running this CLI.
- Open for Phase 3: which of `sha.txt` and `manifest.jsonl` is promoted into evidence folders; the raw NUL form of git status must stay in the run root only.

## Self-Check: PASSED

- The six created files exist under `tests/harness/`.
- The six task commits (`1d90a71`, `8ec7921`, `cfb81f8`, `efc4dc3`, `b03d807`, `a37a73c`) are ancestors of HEAD.
- `requirements.mark-complete` marked HARN-03, HARN-08 and EVID-01 in REQUIREMENTS.md (no sibling plan declares them, so the shared-ID gate had nothing blocked).

---
*Phase: 02-model-free-foundation-and-stub*
*Completed: 2026-10-25*
