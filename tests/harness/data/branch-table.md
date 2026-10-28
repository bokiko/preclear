# Checkpoint stub branch table

The checkpoint helper used by the acceptance harness is a stub: `tests/harness/checkpoint_stub.py`.
It is STUB-BACKED test apparatus, built only from `references/checkpoint-v1.md` and the committed
evidence, and what it prints is never a real-helper result. This table says, branch by branch,
what the stub does and how much of that the committed evidence actually shows.

Status values:

- CONFIRMED: the committed evidence shows this behaviour; the Evidence cell names the files.
- UNCONFIRMED: the reference and the evidence are silent or partial; the stub takes the most
  literal reading. A branch with no committed evidence says so ("document only" or "none").
- STUB-ONLY: behaviour that exists only in the stub or the wrapper (no real-helper counterpart).

Rows are in ascending exit-code order, then in the verb order of the interface table (status,
show, validate, update, note, lint, handoff, the driver verbs, anything else). The stub's own
docstring lists its UNCONFIRMED behaviours and `tests/harness/test_branch_table.py` requires each
to appear here, so the two cannot drift.

| Branch | Command | Exit | Evidence | Status |
|--------|---------|------|----------|--------|
| status, bound session | status | 0 | `tests/evidence/publication-2026-10-20/row1-wrong-binding/status-before.txt`; `tests/evidence/publication-2026-10-20/row3b-denied-helper-write-rerun/status-before.txt` | CONFIRMED |
| status, unbound session | status | 0 | `tests/evidence/publication-2026-10-20/row3c-unbound-fallback-none/status-before.txt` | CONFIRMED |
| status with no checkpoint block prints checkpoint: NONE | status | 0 | document only | UNCONFIRMED |
| status carried-from suffix | status | 0 | document only | UNCONFIRMED |
| show, whole ledger | show | 0 | `tests/evidence/publication-2026-10-20/row2-double-conflict/s2-preclear-full-trace.md`; `tests/evidence/publication-2026-10-20/row3b-denied-helper-write/s2-preclear-full-trace.md` | CONFIRMED |
| show, one section | show | 0 | `tests/evidence/publication-2026-10-20/row3b-denied-helper-write/s2-preclear-full-trace.md` | CONFIRMED |
| a repeated --section flag: the first value wins | show | 0 | document only | UNCONFIRMED |
| section hash derivation (D-07) | show | 0 | `tests/evidence/publication-2026-10-20/row2-double-conflict/s2-preclear-full-trace.md`; `tests/evidence/bound-ledger-2026-10-19/main/show-after-s2.txt`; `tests/harness/test_stub_replay.py`; the committed sha.txt snapshots list files and not section hashes, so the rule (SHA-256 of the body, trailing newlines stripped) was derived from the committed show output; four path-free hashes reproduce exactly; the two path-bearing hashes cannot be recovered because the committed copy holds sanitised path tokens; the trimming of surrounding whitespace is unobservable | UNCONFIRMED |
| validate, accepted block | validate | 0 | `tests/evidence/publication-2026-10-20/row2-double-conflict/s2-preclear-full-trace.md`; `tests/evidence/publication-2026-10-20/row3b-denied-helper-write/s2-preclear-full-trace.md` | CONFIRMED |
| validate byte count | validate | 0 | document only; three committed samples only, matched by pattern in the replay | UNCONFIRMED |
| update, ok | update | 0 | `tests/evidence/publication-2026-10-20/row2-double-conflict/wrapper-injection.log` | CONFIRMED |
| update with the current hash and an unchanged body succeeds | update | 0 | document only | UNCONFIRMED |
| a non-Authorization section with an empty body is allowed | update | 0 | document only | UNCONFIRMED |
| note: stdout and exit code | note | 0 | document only for stdout and exit code; the ledger effect is in `tests/evidence/bound-ledger-2026-10-19-rerun/conflict/snap-2-after-preclear/ledger.md` | UNCONFIRMED |
| lint, ok | lint | 0 | `tests/evidence/publication-2026-10-20/row2-double-conflict/lint-after-s2.txt` | CONFIRMED |
| lint warnings: one warning line per problem | lint | 0 | document only | UNCONFIRMED |
| handoff: the snapshot file name and stdout | handoff | 0 | none | UNCONFIRMED |
| bind, create and init argument shapes (driver only, never model-facing; the wrapper refuses them with exit 71) | bind, create, init | 0 | document only; the prior driver script shape only | UNCONFIRMED |
| ledger-roots.json and .checkpoint-log.jsonl content | bind, update | 0 | document only; the file names appear only in committed sha.txt lists such as `tests/evidence/publication-2026-10-20/row2-double-conflict/snap-0-setup/sha.txt` | UNCONFIRMED |
| stderr brand line and the --version banner | any | 0 | `tests/harness/test_stub_cli.py` | STUB-ONLY |
| exit 1 internal error | any | 1 | none | UNCONFIRMED |
| exit 2 usage error or a ledger with no checkpoint block | any | 2 | document only | UNCONFIRMED |
| update conflict, first and second attempt | update | 3 | `tests/evidence/publication-2026-10-20/row2-double-conflict/s2-preclear-full-trace.md`; `tests/evidence/publication-2026-10-20/row2-double-conflict/snap-2-after-preclear` | CONFIRMED |
| the conflict message goes to standard error | update | 3 | document only; the committed trace merges the two streams | UNCONFIRMED |
| validate rejection codes (exit 4 and the invalid checkpoint message) | validate, update | 4 | document only | UNCONFIRMED |
| update: a body line equal to the checkpoint end marker or matching a begin marker is refused, so a model-written body cannot corrupt the block | update | 4 | `tests/harness/test_stub_cli.py` | STUB-ONLY |
| exit 5 kill switch (kill switch scope: write verbs only) | any write verb | 5 | none | UNCONFIRMED |
| exit 6 lock timeout | any write verb | 6 | none | UNCONFIRMED |
| exit 64 CKPT_HOME missing or not a directory | any | 64 | `tests/harness/test_stub_cli.py` | STUB-ONLY |
| exit 70 wrapper not configured (py or stub file missing or empty) | any | 70 | `tests/harness/test_wrapper_conflict.py` | STUB-ONLY |
| exit 71 driver-only verb refused by the wrapper | bind, create, init | 71 | `tests/harness/test_wrapper_conflict.py` | STUB-ONLY |

## Wrapper (outside the stub)

`tests/harness/checkpoint-wrapper` (bash 3.2) sits between the caller and the stub. It adds call
logging and conflict injection so the stub itself carries neither. Files beside the wrapper:

- `calls.log`: one `<UTC second> CALL <argv>` line (argv quoted with printf %q) and one
  `<UTC second> EXIT <n>` line per call, the same shape as the committed `wrapper-calls.log`.
- `injection.log`: written only while armed; a header line, the second writer's stub output
  and `writer2 update exit <n>` per injection. Nothing in it ever reaches the caller.
- `armed`: the remaining number of injections. With count 2 the first update to the first
  touched section conflicts (exit 3), the retry conflicts again, the third update succeeds.
- `target-section`: the first section an armed update touched; only that section is injected.
- `writer2.session`: the session id of the second bound writer.
- `py` and `stub`: the interpreter path and the stub path; a missing or empty file is exit 70.

The wrapper never changes the caller's arguments, input files or output. Its one exception is the
driver-only verbs: when the verb is bind, create or init it logs the call, prints a refusal on
standard error and exits 71 without delegating, however it was launched.

## Not modelled

The model of the allowlist (`tests/harness/pc_allowlist.py`) covers rule matching only. These
are decided by the real binary and are not modelled here; the live capture in plan 02-08 records
the cases it meets:

- a cd combined with git, output redirection approval, path scope outside the working
  directories, and brace-quote obfuscation;
- the built-in read-only command set, which runs without a rule;
- the indirect launch routes through the baseline's env, python3 -c, awk and find rules: they can
  start another program, so the allowlist alone cannot stop an env-prefixed wrapper bind. They are
  not rule-matchable and are stopped by the wrapper's exit 71, not by the allowlist.
