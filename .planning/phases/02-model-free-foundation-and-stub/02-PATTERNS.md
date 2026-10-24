# Phase 2: Model-Free Foundation and Stub - Pattern Map

**Mapped:** 2026-10-25
**Files analyzed:** 27 new files (no existing file is modified; `SKILL.md`, `references/`, `tests/fixtures/`, `tests/evidence/` stay frozen)
**Analogs found:** 27 / 27 role or data-flow matches. No file has an exact same-language analog, because the repository holds no Python yet. Every analog below is tracked source (verified with `git ls-files`). All paths are repo-relative.

## Ground rules that apply to every file

- **Python conventions are set here.** Python 3.9 floor, standard library only, flat directory, `pc_` module prefix, `unittest` (CONTEXT D-11, D-12). Nothing in the repo shows Python style, so the shell gates supply behaviour (fail closed, counts only, scratch guard) and the evidence supplies data shapes.
- **Seeds are assembled at run time.** Any test that needs a leak-shaped string builds it from fragments, exactly like `write_seed` in `scripts/test-hooks.sh` (lines 75-79). Never commit a literal home path, private address, internal host suffix, personal email or credential-shaped string in source or prose.
- **Replay data must not end in `.log`.** The root ignore file drops `*.log` outside `tests/evidence/`, so mined replay data uses `.json`.

## File Classification

| New file | Role | Data flow | Closest analog | Match quality |
|----------|------|-----------|----------------|---------------|
| `tests/harness/selftest` | shim (bash 3.2) | request-response | `.githooks/pre-push` (header, `here=`, fail-closed loop) | role-match |
| `tests/harness/pc_exitcodes.py` | utility (constants) | transform | `scripts/prepublish-check.sh` (usage block, exit 0/1/2 contract) | partial |
| `tests/harness/pc_runroot.py` | utility | file-I/O (exclusive create) | `scripts/prepublish-check.sh` (`--record` created exclusively, never overwritten) | role-match |
| `tests/harness/pc_manifest.py` | service | file-I/O, batch | `tests/evidence/*/snap-*/sha.txt` (output shape) plus `.githooks/checks/denylist.sh` (never split names on newlines in awk) | data-match |
| `tests/harness/pc_measure.py` | utility | transform | `tests/evidence/hub-memory-2026-10-19/measurements.md` (output shape) | data-match |
| `tests/harness/pc_sanitize.py` | service | transform | `.githooks/checks/denylist.sh` lines 33-74 (runtime deny-list, length floors) | exact (logic) |
| `tests/harness/pc_leakgate.py` | service | batch, request-response | `.githooks/checks/denylist.sh` lines 80-126 and `.gitleaks.toml` | exact (logic) |
| `tests/harness/pc_promote.py` | service | file-I/O | `scripts/test-hooks.sh` scratch guard (lines 41-72) plus `.githooks/pre-push` fail-closed loop | role-match |
| `tests/harness/pc_flags.py` | config | transform | none in repo; table content from `02-RESEARCH.md` flag table | no analog |
| `tests/harness/pc_allowlist.py` | utility | transform | none in repo; corpus is `tools.txt` per evidence row | no analog |
| `tests/harness/pc_stream.py` | utility | streaming (parse) | none in repo; shapes in `.planning/research/STACK.md` | no analog |
| `tests/harness/pc_mine.py` | utility | batch (log parse) | `tests/evidence/publication-2026-10-20/row2-double-conflict/wrapper-calls.log` (input format) | data-match |
| `tests/harness/checkpoint_stub.py` | service | CRUD (files under `CKPT_HOME`) | `references/checkpoint-v1.md` (contract), committed `show`, `status`, conflict outputs | contract-match |
| `tests/harness/checkpoint-wrapper` | middleware (bash 3.2) | request-response | `tests/evidence/publication-2026-10-20/row2-double-conflict/wrapper-checkpoint.sh` | exact |
| `tests/harness/replay-cases.json` | data | batch | `wrapper-calls.log` files (mined) | data-match |
| `tests/harness/data/*` (stream fixture, branch table, flag prose) | data | n/a | `tests/evidence/publication-2026-10-20/README.md` (verdict and sequence tables) | role-match |
| `tests/harness/README.md` | docs | n/a | `.githooks/README.md` | role-match |
| `tests/harness/.gitignore` | config | n/a | root ignore file (no entry for bytecode today) | partial |
| `tests/harness/test_selftest_shim.py`, `test_bash_shims.py`, `test_imports.py` | test | request-response | `scripts/test-hooks.sh` (PASS/FAIL per case, scratch dir, no leakage of global config) | role-match |
| `tests/harness/test_runroot.py`, `test_manifest.py`, `test_measure.py` | test | file-I/O | `scripts/test-hooks.sh` case functions | role-match |
| `tests/harness/test_sanitize.py`, `test_leakgate.py`, `test_promote.py` | test | batch | `scripts/test-hooks.sh` `case_*` leak cases (seed from fragments) | exact (approach) |
| `tests/harness/test_stub_cli.py`, `test_stub_replay.py`, `test_mine.py`, `test_wrapper_conflict.py`, `test_branch_table.py`, `test_frozen_reference.py` | test | request-response | `scripts/test-hooks.sh` plus committed evidence as oracle | role-match |
| `tests/harness/test_flags.py`, `test_version_gate.py`, `test_allowlist.py`, `test_stream.py`, `test_preflight.py` | test | transform | none in repo | no analog |
| spike findings and real stream fixture (paid, outside the suite) | docs and data | request-response | `tests/evidence/publication-2026-10-20/README.md` and its per-row `s2-preclear-full-trace.md` | role-match |

## Pattern Assignments

### `tests/harness/pc_leakgate.py` and `tests/harness/pc_sanitize.py` (service, batch/transform)

**Analog:** `.githooks/checks/denylist.sh`

**Build the entry list at run time, check every step, drop short entries** (lines 40-73). Port as: gather names (hostname, short hostname, `scutil` names), read the local deny file if present, treat any read error as a refusal, apply length floors, sort unique.
```sh
{
  hostname
  hostname -s
  scutil --get LocalHostName
  scutil --get ComputerName
} >> "$raw" 2>/dev/null
extra=$(git rev-parse --git-path info/preclear-deny.txt 2>/dev/null)
if [ -n "$extra" ] && [ -r "$extra" ]; then
  grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$extra" >> "$extraraw"
  # grep status 1 only means "no entry lines"; above 1 is a read error and must not pass.
  [ $? -le 1 ] || { echo "denylist check FAILED: could not read the local deny list" >&2; exit 1; }
fi
```
Floors to mirror: host names need at least 6 characters and must not be in the generic list (line 67); local-file entries need at least 4 (line 71). Matching is case-insensitive fixed-string.

**Counts only, never the value; file name shown as a label when the name itself matches** (lines 80-97, label function lines 83-87):
```sh
function lab(p,   e, lp) {
  lp = tolower(p)
  for (e in entries) if (index(lp, e) > 0) return "(file name)"
  return p
}
```
Python equivalent: `label_for(path)` returns `"(file name)"` when the path matches any entry, otherwise the path; output is `label<TAB>count` only.

**Scanner failure is a refusal** (lines 111-126). Every scan helper checks its own status:
```sh
scan_diff() {
  count_hits < "$diffout" > "$hitsout" || { echo "denylist check FAILED: scan error" >&2; exit 1; }
}
sum_hits() {
  n=$(awk -F"$tab" '{ s += $2 } END { print s + 0 }' "$hitsout") \
    || { echo "denylist check FAILED: scan error" >&2; exit 1; }
  case $n in ''|*[!0-9]*) echo "denylist check FAILED: scan error" >&2; exit 1 ;; esac
}
```
Python equivalent: wrap the whole scan in one `try/except Exception` that returns a refusal code, validate counts are integers, and never let an empty result stand for "clean" when the scanner raised.

**Output message shape** (lines 137, 154): `denylist check FAILED: <file> (<n> match(es) against ...)`. Reuse the wording style `leak gate FAILED: <label> (<n> match(es))`. No matched text.

**Rule parity source:** `.gitleaks.toml`. Rule ids to mirror one for one: `home-path-unix` (line 7), `home-path-dash-slug` (13), `mac-temp-root` (19), `private-ipv4` (25, `secretGroup = 1`), `internal-hostname` (32), `email-address` (38), plus two allowlists (lines 43-58): the planning-docs path condition with the public identity, and the reserved-domain and two role-address allowlist. Parity test reads each `id =` and `regex = '''...'''` line with a small line reader (no `tomllib`) and asserts the Python pattern strings are byte-identical. Do not paste the regexes into this document or into test source as literals that could themselves match; read them from the TOML file at test time.

**Seed pattern for tests** (`scripts/test-hooks.sh` lines 75-79): assemble the seed from three fragments inside a function that writes it to a scratch file. Apply the same idea to a home path (`"/" + "Users" + "/" + name`), a private address (join octets) and an email (join local part, `@`, domain).

---

### `tests/harness/pc_promote.py` (service, file-I/O)

**Analog:** `scripts/test-hooks.sh` scratch guard, `.githooks/pre-push`

**Prove the target before acting; refuse otherwise** (`scripts/test-hooks.sh` lines 41-55):
```sh
scratch_ok() {
  scratch_top=$(git -C "$1" rev-parse --show-toplevel 2>/dev/null) || return 1
  [ -n "$scratch_top" ] || return 1
  case $scratch_top in "$TP"/*) ;; *) return 1 ;; esac
  [ "$scratch_top" != "$REPO_TOP" ] || return 1
  return 0
}
```
Python equivalent for `promote`: resolve with `os.path.realpath`, require the destination to be strictly under the repo's `tests/evidence/`, refuse any realpath under the Claude config directory, refuse symlinks (`os.lstat`), absolute names and `..` segments, then create every directory with `os.mkdir` and every file with `O_CREAT|O_EXCL`.

**Fail closed when a required check is missing or not runnable** (`.githooks/pre-push` lines 28-41):
```sh
found=0
for check in "$here"/checks/*.sh; do
  [ -e "$check" ] || continue
  found=1
  if [ ! -x "$check" ]; then
    echo "pre-push FAILED: $check is not executable" >&2
    rc=1
    continue
  fi
  "$check" "$ranges" || rc=1
done
[ "$found" -eq 1 ] || { echo "pre-push FAILED: no checks found under $here/checks" >&2; rc=1; }
```
Apply: `promote` runs gate first, copy second; zero rules loaded counts as a refusal, not a pass.

**Second net:** `.githooks/pre-commit` (lines 7-14) runs gitleaks and `checks/denylist.sh --staged` on every commit, so a promoted file still faces them. `promote` does not replace them.

---

### `tests/harness/pc_runroot.py` (utility, file-I/O)

**Analog:** `scripts/prepublish-check.sh`

**Exclusive creation, no overwrite, bad usage gets its own code** (lines 1-8, 47-56): header states "created exclusively, never overwritten", usage exits 2, a pre-existing target is refused before any work. Also resolves caller-relative paths up front (lines 44-46) before changing directory; copy that: resolve the run-root parent once with `os.path.realpath` and pass absolute paths everywhere.
```sh
if [ -n "$RECORD" ] && [ -e "$RECORD" ]; then
```
Python: `os.mkdir(path)` with no `exist_ok`, let `FileExistsError` surface as the refusal. Throwaway directories are never deleted (`scripts/test-hooks.sh` header line 8: "The throwaway directory is never deleted."). A static test scans harness modules for delete and overwrite calls (HARN-03).

---

### `tests/harness/pc_exitcodes.py`, `pc_flags.py` (version gate)

**Analog:** `scripts/prepublish-check.sh` exit contract (header lines 13-14: "0 when every check passed, 1 when any FAIL line was printed, 2 on bad usage") and `scripts/test-hooks.sh` PASS/FAIL line format (lines 35-36).
```sh
pass() { echo "PASS $1"; }
fail() { echo "FAIL $1: $2"; FAILS=$((FAILS + 1)); }
```
Use distinct codes for SKIP, FAIL, BLOCKED, untested version and stub refusal (64, from research). Keep them in `pc_exitcodes.py` so tests assert them by name. Flag table content has no repo analog: copy from `02-RESEARCH.md` "Flag table the plans should commit". A test asserts the README table equals `pc_flags.py` output.

---

### `tests/harness/checkpoint-wrapper` (middleware, bash 3.2, request-response)

**Analog:** `tests/evidence/publication-2026-10-20/row2-double-conflict/wrapper-checkpoint.sh` (tracked). Copy the shape; two changes are mandatory. First, `REAL=<helper>` becomes the absolute interpreter plus stub invocation (`"$PY" -I -B "$STUB" "$@"`). Second, the wrapper reads its paths from the run root, not from `dirname "$0"` assumptions beyond its own directory.

**Header and log line** (lines 1-8):
```bash
#!/bin/bash
# TEST APPARATUS ONLY. Logs every call and delegates unchanged to the real helper. ...
W="$(cd "$(dirname "$0")" && pwd)"
printf '%s CALL' "$(date -u +%FT%TZ)" >> "$W/calls.log"; printf ' %q' "$@" >> "$W/calls.log"; echo >> "$W/calls.log"
```
The `%q` quoting is what `shlex.split` undoes in the miner. Keep `CALL`/`EXIT` and the UTC second timestamp exactly.

**Armed injection to the first touched section** (lines 9-26): `armed` file holds a count, `target-section` remembers the first `--section` seen, a second bound session (`writer2.session`) does a real `show` then a real `update` with the section hash it just read, so the stub returns a genuine exit 3. Count 2 gives conflict on attempt one and attempt two, then success. Injection output goes to `injection.log`, never to the caller.

**Delegate unchanged and log exit** (lines 27-29):
```bash
"$REAL" "$@"; rc=$?
echo "$(date -u +%FT%TZ) EXIT $rc" >> "$W/calls.log"
exit $rc
```
Bash 3.2 notes: the file already avoids associative arrays and `mapfile`. Keep that, and run the bash 3.2 lint in `test_bash_shims.py`. The stub must contain no injection and no logging (STUB-04); a test greps the stub for both.

**Log format to produce and parse** (`row2-double-conflict/wrapper-calls.log`):
```
<UTC second> CALL update --section Goal\ \&\ current\ state --expect-section <64 hex> --from <relative file>
<UTC second> EXIT 3
```

---

### `tests/harness/checkpoint_stub.py` (service, CRUD under `CKPT_HOME`)

**Analog:** no code analog. The contract is `references/checkpoint-v1.md` (frozen, STUB-07) and committed outputs. The branch table in `data/` marks each row CONFIRMED or UNCONFIRMED as listed in `02-RESEARCH.md`.

**Output shapes to reproduce byte for byte** (all from committed evidence):

`status`, bound (`tests/evidence/publication-2026-10-20/row1-wrong-binding/status-before.txt`):
```
session eace4601 → <repo>/<run>/ledgers/CONTINUITY_CLAUDE-other-task.md
checkpoint updated 2026-10-19T23:06:03.260Z by eace4601
Next action: Rename settings_loader.py to config_loader.py.
```
`status`, unbound: `session <id8>: unbound`, exit 0 (row 3c `status-before.txt`).

`show`: header lines `ledger:`, `file-fingerprint:` (whole-file SHA-256), `checkpoint-updated: <iso-ms>Z by <id8>`, blank line, then per section `## <name>`, `section-hash: <hash>`, body, blank line. Sample in `row2-double-conflict/s2-preclear-full-trace.md`.

Section hash: `hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()`, no heading, no `section-hash:` line (research, verified on eight hashes). Replay asserts four path-free hashes exactly, and for path-bearing sections only `hash == sha256(displayed body)`.

`update` ok: `updated "<section>" in <ledger path>`. `update` conflict: exit 3, message `checkpoint: conflict: "<section>" changed since your read. Nothing written. Details: <ledger>.conflict-<date>T<hh>-<mm>-<ss>.<ms>Z-<id8>.md`, conflict file body as described in research (`# Conflict on section`, `ledger:`, `your base hash:`, `current hash:`, `## Yours (not applied)`, `## Current (kept)`). `lint` ok: `ledger lint OK` (unchanged). `validate` ok: `valid checkpoint: <N> bytes, Authorization <M> chars`, matched by pattern, not by value.

**Branding (D-09 as refined):** one stub-marker line on stderr per call, a banner on `--version`, nothing added to stdout. The replay normalizer strips the stderr line.

**Mechanics from research** (no repo analog, techniques verified on 3.9.6): refuse without `CKPT_HOME` (exit 64), state under `bindings/`, `ledger-roots.json` and a dedicated lock file, atomic write via `tempfile.mkstemp(dir=...)` then `os.fsync` then `os.replace`, lock via `fcntl.flock(LOCK_EX|LOCK_NB)` with a deadline loop on the lock file (never the ledger), exit 5 via `CKPT_STUB_KILL_SWITCH`, exit 6 via `CKPT_STUB_LOCK_TIMEOUT_MS`. Set stdout to UTF-8 at startup because `status` prints the arrow.

**Ledger file and binding formats** (`row2-double-conflict/snap-0-setup/` copies; binding keys `session_id`, `project`, `workstream`, `ledger`, `created`, `retired`, `predecessor`): `# CONTINUITY` line, block between `<!-- CHECKPOINT:BEGIN updated: <iso-ms>Z by: <id8> -->` and `<!-- CHECKPOINT:END -->`, then `## History`. File name `CONTINUITY_CLAUDE-<task>.md`.

---

### `tests/harness/pc_mine.py` and `replay-cases.json` (utility, batch)

**Analog (input):** `tests/evidence/publication-2026-10-20/row*/wrapper-calls.log`. Nine row folders hold such a file; five are non-empty (15 calls), four are empty and must be mined as "zero calls" cases (rows 3a, its rerun, 4a, 4b). The bound-ledger folders hold none, despite CONTEXT naming them.

Parse (from research, verified on all 15 calls):
```python
m = re.match(r"^(\S+) (CALL|EXIT) ?(.*)$", line)
argv = shlex.split(m.group(3)) if m.group(2) == "CALL" else None
```
Decisive outputs for each case live beside the log, for example `row1-wrong-binding/status-before.txt` and `row2-double-conflict/s2-preclear-full-trace.md`. `test_mine.py` regenerates `replay-cases.json` and compares it to the committed copy so the miner cannot drift.

---

### `tests/harness/pc_manifest.py` (service, file-I/O)

**Analog (output shape):** `tests/evidence/publication-2026-10-20/row2-double-conflict/snap-0-setup/sha.txt`. Lines are `<64 hex>`, two spaces, relative path, sorted by path bytes:
```
4f94eefee16d51c2cc909a518ed972ebe4d1b0c59cb7dafd677c661ca76fe53b  ledgers/CONTINUITY_CLAUDE-widget-export.md
```
Keep the folder names `snap-0-setup`, `snap-1-after-work`, `snap-2-after-preclear` and files `sha.txt`, `status.txt`, `ledger.md` unchanged so Phase 3 evidence compares row for row (CONTEXT, Established Patterns). New in this module: walk with `os.walk(os.fsencode(root))`, sort raw bytes, escape newline, carriage return and backslash in the text form, and emit a lossless JSON-lines companion with `json.dumps(os.fsdecode(name), ensure_ascii=True)`. Status capture: `git --no-optional-locks status --porcelain=v1 -z --untracked-files=all` from the harness, raw NUL form kept, `status.txt` derived from the non-`-z` form. Formats follow `references/status-sidecar.md`.

---

### `tests/harness/pc_measure.py` (utility, transform)

**Analog (output shape):** `tests/evidence/hub-memory-2026-10-19/measurements.md`:
```
## checkpoint after stage 2-after-preclear
total 3603 bytes, sha256 0aabedfe...
- Identity and state: 692
- Boundaries and blockers: 529
```
EVID-01 asks for actual/cap, so print `692/800` style while keeping the same section order and names. Caps and names come from `SKILL.md` lines 134-139 (800, 600, 500, 600, 1000, 596; file cap 4096). Read bytes, split with `re.split(rb"(?m)^(?=## )", data)`, count `len()` per piece including the heading. Tests use synthetic fixtures with hand-computed sizes (ASCII, 2-byte, 3-byte, 4-byte, CRLF); the committed evidence is sanitized and cannot serve as an oracle.

---

### `tests/harness/selftest` (shim, bash 3.2)

**Analog:** `.githooks/pre-push` (lines 1-12) for header comment, own-directory resolution and fail-closed exit style; `scripts/test-hooks.sh` lines 1-16 for environment hygiene.
```sh
here=$(cd "$(dirname "$0")" && pwd)
cd "$(git rev-parse --show-toplevel)" || exit 1
```
and
```sh
GIT_CONFIG_GLOBAL=/dev/null
GIT_CONFIG_NOSYSTEM=1
GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM GIT_TERMINAL_PROMPT
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
```
Use the same git-environment hygiene so a stranger's global git config cannot change a result. The shim then drops PATH entries that hold an executable `claude`, and ends with `exec "$py" -I -B -m unittest discover -s "$here" -t "$here"` (research, verified under bash 3.2.57). Use `#!/bin/sh`-compatible syntax where possible, as the hooks do.

---

### Test modules (`tests/harness/test_*.py`)

**Analog:** `scripts/test-hooks.sh`. Carry over these ideas rather than code:
- One function per case, each ending in a single named PASS or FAIL with a reason (lines 35-36, 103, 120). Use `unittest` test method names that match the case names.
- Isolated scratch location, never the real repo, and nothing deleted afterwards (lines 22-33, 41-55). Use `tempfile.mkdtemp` per test class and assert resolved paths stay inside it.
- Never touch the real remote or real state: the script records ref digests at start (lines 22-23) and compares at the end. Mirror this for the stub: snapshot the parent of `CKPT_HOME` before and after and assert nothing else changed.
- Seeds from fragments (lines 75-79).
- Tripwire pattern for zero model calls: place a fake `claude` first on PATH that writes a marker file, run the suite in a subprocess with a minimal PATH, assert exit 0 and no marker (`test_selftest_shim.py`).

---

### `tests/harness/README.md` (docs)

**Analog:** `.githooks/README.md` for structure (what it is, how to enable, what each check does). Required content from CONTEXT: first command is `tests/harness/selftest`; the `CKPT_STUB_` switches by name; the one-time manual login into the harness-owned config directory (D-03) in plain words; the flag table; the note that deleting the config directory leaves the keychain entry. Verdict and sequence table style comes from `tests/evidence/publication-2026-10-20/README.md`.

---

### `tests/harness/test_frozen_reference.py` (test)

STUB-07 check: SHA-256 of `references/checkpoint-v1.md` equals the adapter digest recorded in `digests.txt` of the committed row 5 to 12 evidence folders under `tests/evidence/publication-2026-10-20/` (digest begins `eca134a3defc`). Read the expected value from the evidence file at test time. Never edit the reference.

## Shared Patterns

### Fail closed, counts only
**Source:** `.githooks/checks/denylist.sh` (lines 49-50, 111-126, 135-139), `.githooks/pre-commit` line 9 and `.githooks/checks/leaks.sh` line 7.
**Apply to:** `pc_leakgate.py`, `pc_sanitize.py`, `pc_promote.py`, `pc_flags.py` (preflight), every CLI entry point.
A missing scanner, unreadable deny file, zero loaded rules or any exception is a refusal with its own non-zero code. Output holds counts and labels only, never a matched value, home path, host name or temp path.
```sh
command -v gitleaks >/dev/null 2>&1 || { echo "pre-commit FAILED: gitleaks not found (install it, then retry)" >&2; exit 1; }
```

### Distinct codes for "finding" versus "tool error"
**Source:** `.githooks/pre-commit` lines 10-12 (`--exit-code 2` keeps a finding apart from a tool error) and `denylist.sh` exit 3 for "owner's entries were not loaded".
**Apply to:** the preflight (SKIP, FAIL, BLOCKED), the version gate and the stub refusal (64). Document each in `pc_exitcodes.py` and the branch table.

### Run-time assembly of anything leak-shaped
**Source:** `scripts/test-hooks.sh` lines 75-79.
**Apply to:** every test and fixture that needs a seeded home path, address, email, host name or key shape.
```sh
write_seed() {
  seed_a=AK; seed_b=IA; seed_c=<fragment>
  printf 'aws_key = %s%s%s\n' "$seed_a" "$seed_b" "$seed_c" > "$1"
}
```

### Placeholder tokens
**Source:** committed evidence, for example `<repo>/<run>/ledgers/...` in `row1-wrong-binding/status-before.txt`.
**Apply to:** `pc_sanitize.py`. CONTEXT D-15 locks lower-case `<home>`, `<user>`, `<host>`, `<tmp>`, `<repo>`, matching the evidence byte for byte. Research still lists upper-case tokens; CONTEXT was refined after research, so use lower-case. The evidence also uses `<run>`, `<helper>` and `<auto-memory-root>`; keep those in the replacement set so sanitized output matches committed files.

### Evidence layout
**Source:** `tests/evidence/publication-2026-10-20/row2-double-conflict/` (folder names, `snap-N-*`, `sha.txt`, `wrapper-calls.log`, `wrapper-checkpoint.sh`, `tools.txt`, `digests.txt`, `measurements.md`, `session.id`).
**Apply to:** snapshotter and `promote` output names.

### Fixture materialization
**Source:** `tests/fixtures/hub-memory/README.md` ("Harness setup" paragraph) and `tests/fixtures/*/runtime-settings.example.json`, which holds a single `autoMemoryDirectory` key with an absolute-path placeholder.
**Apply to:** run-root materializer and settings builder. Copy a fixture folder into the run root, render `runtime-settings.example.json` with the absolute realpath of the copy's `project/memory`, launch with `--settings <that file>` and `--setting-sources project,local`. `tests/fixtures/bound-ledger/` has no settings example (it uses the helper state instead). Fixtures are read-only inputs here.

## No Analog Found

Planner should use `02-RESEARCH.md` for these.

| File | Role | Data flow | Reason |
|------|------|-----------|--------|
| `tests/harness/pc_flags.py` | config | transform | No Python or flag table exists; use the research flag table and minimum-version list. |
| `tests/harness/pc_allowlist.py` | utility | transform | No matcher exists; use the research "Bash rule semantics" and the per-row `tools.txt` corpus. |
| `tests/harness/pc_stream.py` | utility | streaming | No stream-json parser exists; shapes from research and `.planning/research/STACK.md`, ground truth from the paid S2 capture. Union the three denial signals; never inspect reply text. |
| `tests/harness/test_flags.py`, `test_version_gate.py`, `test_allowlist.py`, `test_stream.py`, `test_preflight.py` | test | transform | No Python tests exist; follow the `unittest` conventions above and the research validation map. |
| Spike S1 and S2 scripts and findings | docs and data | request-response | The only paid work; no precedent for a live driver in tracked source. Evidence layout and the verdict-table style of `tests/evidence/publication-2026-10-20/README.md` are the nearest format. |

## Metadata

**Analog search scope:** `.githooks/`, `scripts/`, `.gitleaks.toml`, `references/`, `tests/fixtures/`, `tests/evidence/` (publication folder, bound-ledger folders, hub-memory measurements).
**Files read:** `.githooks/checks/denylist.sh`, `.githooks/checks/leaks.sh`, `.githooks/pre-commit`, `.githooks/pre-push`, `.gitleaks.toml`, `scripts/test-hooks.sh` (lines 1-100 and a grep of the rest), `scripts/prepublish-check.sh` (lines 1-50), the row 2 wrapper and log, one `sha.txt`, one `measurements.md`, one status file, fixture README and settings example, `02-CONTEXT.md`, `02-RESEARCH.md`.
**Tracked-source check:** all named analog paths appear in `git ls-files` output.
**Pattern extraction date:** 2026-10-25
