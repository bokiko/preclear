---
phase: "04"
slug: "full-matrix-row-7-and-review"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-11"
---
# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| model ↔ run root | the real model (claude-sonnet-5-5 on Claude Code 2.1.310) works only inside a scratch run root; every write outside it ends the row with exit 11 and a STOPPED folder | fixture files, traces, the printed checkpoint |
| run root ↔ filed evidence | the harness copies a run into `tests/evidence` only through `pc_promote` behind the leak gate, gitleaks and check-words; filed text never carries a home path, host, address, email, login or build path | traces, digests, usage figures, READMEs |
| harness ↔ owner | spending, pushing, the real home and the reference swap happen only on bokiko's own typed word at a blocking-human checkpoint; an agent message is never his word | budget amounts, go words, verdict lines pasted from Codex |
| clone ↔ main tree | the clean-clone bootstrap runs from a never-used folder with a fixed child environment (seven names, eight under `--real-home`) and copies back through the same gate | the baseline folder, clone facts (names and counts only) |
| model ↔ private helper | the private `checkpoint` helper is never reachable: a stub on a scrubbed PATH, wrapper rules by verb, post-assertions over every helper call | helper calls (all 24 of the baseline reached the clone stub) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-01 (04-01) | Tampering | row id reaching a path, ledger key or promote destination | high | mitigate | run_registered_row resolves the RowSpec by exact registry match before any path is built; the row folder name is derived from the entry, never from caller text; | closed |
| T-04-02 (04-01) | Information disclosure | setup_text, README and filed names carrying a home path or the login | high | mitigate | the sanitizer, leak gate and promote with deny entries run on every staged file as before; a test scans every registry setup_text for path-shaped strings; the R | closed |
| T-04-03 (04-01) | Tampering | a deletion, rename or truncation primitive in the new module pc_rowseeds.py | high | mitigate | pc_rowseeds.py is not exempt from the static scan in test_runroot.py; it creates only through pc_runroot; the scan and test_imports.py run in this plan's gate ( | closed |
| T-04-04 (04-01) | Tampering | the model writing outside the run root during a registry-driven row | high | mitigate | snapshot, trace and git-state checks are unchanged and run for every registry row; a scripted out-of-root write ends the row with exit 11 and nothing filed | closed |
| T-04-05 (04-01) | Repudiation | the spec refactor silently changing row 1's filed shape | medium | mitigate | Row1ParityTests compares the filed names with the committed Phase 3 baseline, read only; the three Phase 3 test modules named in Task 2 run unchanged in this pl | closed |
| T-04-06 (04-02) | Denial of service (cost) | the loop spending past the stated budget, or a retry started without an earlier  | high | mitigate | stop-before-row rule over settled spend plus the next worst case; the minimum-budget rule; attempt N needs a ledger launch line for attempt N-1; every stage sti | closed |
| T-04-07 (04-02) | Tampering | a label, attempt or date text reaching a path, a ledger id or a promote destinat | high | mitigate | exact patterns, length caps and the reserved a1 to a9 words; refusal text never echoes the value; ids are built only from validated parts and checked against th | closed |
| T-04-08 (04-02) | Tampering | a label such as a2 colliding with attempt scoping to obtain an extra attempt | medium | mitigate | labels a1 to a9 are reserved and refused; a test builds scoped ids for every label and attempt pair and asserts no two selections give the same id | closed |
| T-04-09 (04-02) | Information disclosure | summary and per-row lines carrying a path, a session id or a command line value | medium | mitigate | fixed-text lines with registry ids, counts and amounts only; a test scans all printed output of every case for path-shaped text and the raw label (ASVS V7) | closed |
| T-04-10 (04-02) | Repudiation | a skipped or stopped row read as success | high | mitigate | exit 10 for skip-only, 11 or 19 for stops, never 0; the summary counts skipped and stopped; the word pass is absent from driver output (HARN-02) | closed |
| T-04-11 (04-03) | Information disclosure | a STOPPED folder carrying a home path, the login or a credential-shaped string f | high | mitigate | the same sanitizer, leak gate and promote with deny entries as a complete row; raw captures, settings and session ids are never staged; a refusal is exit 14 and | closed |
| T-04-12 (04-03) | Tampering | promote_into overwriting a file or writing outside the folder through a name, a  | high | mitigate | every name is checked (no slash, dot-dot, leading dot, existing) before the first create; the folder must be a real folder whose realpath is inside tests/eviden | closed |
| T-04-13 (04-03) | Repudiation | a stopped or skipped row hidden from the reviewer or counted as success | high | mitigate | the STOPPED and SKIPPED labels, the digest table state column, exit codes 11, 19 and 10 that never read as success, and the part files that list every row prese | closed |
| T-04-14 (04-03) | Tampering | model-written text steering the digest table through a crafted trace or README l | medium | mitigate | the tables read only harness-written files (digests.txt, usage.txt, stop.txt, the SKIPPED reason line) with strict patterns; anything else prints UNCONFIRMED; m | closed |
| T-04-15 (04-04) | Elevation of privilege | a plain row inheriting a wrapper rule or a bare executable prefix | high | mitigate | build_row_tools returns no wrapper rule for the plain profile; a test asserts the list equals the baseline plus the two extras and contains no entry naming a wr | closed |
| T-04-16 (04-04) | Tampering | the model writing a memory file outside the run root when memory is disabled | high | mitigate | the memory directory stays pinned inside the run root, the default memory root is probed absent at every snapshot, and the write-boundary check is unchanged; a  | closed |
| T-04-17 (04-04) | Information disclosure | the new data files or setup text carrying a path or the login | medium | mitigate | the data files are literal committed text; a test scans the data files and every registry setup_text for path-shaped strings; the README hygiene test runs in th | closed |
| T-04-18 (04-04) | Tampering | a seed that silently differs from the committed row, weakening the comparison | medium | mitigate | byte-tie tests against the committed digests and the derived-prompt test; the 5a and 5b seeds are compared with each other | closed |
| T-04-19 (04-05) | Tampering | the hook or finalizer changing the mode of a file outside the run root through a | high | mitigate | lstat must show a regular file or the named folder, no symlink, realpath inside the project folder; a refusal is HookRefused, exit 11 with a STOPPED folder; tes | closed |
| T-04-20 (04-05) | Tampering | the boundary list or its absence hiding a comparison, or the model rewriting the | high | mitigate | raw/boundaries.json is created before the setup guard so the guard's raw listing records it; compute_facts refuses any unlisted snapshot, record or guard; only  | closed |
| T-04-21 (04-05) | Information disclosure | perms.txt carrying the owner, group or login | high | mitigate | the file is written by the harness as mode-only lines from lstat, never from ls output; a test asserts there are no extra columns; the sanitizer, leak gate and  | closed |
| T-04-22 (04-05) | Denial of service | a harness fault leaving the plan file read-only | low | accept | the finalizer runs on every exit path of the row; only a killed process can leave one scratch file at mode 444 inside the run root, which the owner can change a | closed (accepted risk) |
| T-04-23 (04-06) | Tampering | the chmod probe or its restore touching the wrong folder | high | mitigate | the probe folder is created exclusively inside this run root's raw folder and is the only object the probe changes; no path comes from the model, the environmen | closed |
| T-04-24 (04-06) | Tampering | the 555 hook or finalizer following a planted symlink or swapped parent to a fol | high | mitigate | the plan 04-05 checks apply to the project folder: not a symlink, a real folder, realpath equal to the run root's project folder; a refusal is exit 11 with a ST | closed |
| T-04-25 (04-06) | Denial of service (cost) | spending on a machine where the denial does not work, or after a SKIP | high | mitigate | the probe runs after the seed and before the first ledger line; a SKIP exits 10 with no ledger line and no process; a test asserts an empty ledger after every S | closed |
| T-04-26 (04-06) | Tampering | a fabricated checkpoint block steering s3 | medium | mitigate | the block comes only from the final result text of s2, at most 8192 bytes, no NUL; it is stored raw and passed as a prompt, never executed or followed by the ha | closed |
| T-04-27 (04-06) | Information disclosure | the printed checkpoint's real paths reaching tests/evidence through the s3 promp | high | mitigate | the prompt is stored in raw only; the filed copy passes the sanitizer, the leak gate and promote with the deny entries; the committed perms.txt shape (raw ls ou | closed |
| T-04-28 (04-06) | Repudiation | a skipped row read as success | high | mitigate | exit 10, the SKIPPED label folder, no ledger line and the digest table state (plan 04-03); the word pass never appears (HARN-02) | closed |
| T-04-29 (04-07) | Tampering | model-authored entry or excerpt text adding structure (a heading, a record, a ma | high | mitigate | every piece of model text is one line, capped, sanitised and prefixed with `> `; the parser reads only structured lines; HostileTextTests feed headings, fake ca | closed |
| T-04-30 (04-07) | Information disclosure | entry text or excerpts carrying a real path or the login into tests/evidence | high | mitigate | the sanitizer runs before staging, then the leak gate and promote with the deny entries; a scripted entry carrying a path-shaped string must be redacted or refu | closed |
| T-04-31 (04-07) | Repudiation | the harness deciding or implying that an entry is supported | high | mitigate | only candidates, counts and the word UNSUPPORTED are printed; no word for a supported entry exists in the module; the vocabulary scan skips only quoted lines (E | closed |
| T-04-32 (04-07) | Denial of service | a huge checkpoint or entry list inflating the files | low | mitigate | caps of 8192 bytes for the checkpoint (plan 04-06), 64 entries, 400 and 160 characters and 20 candidates with a count of the rest; tests build over-cap input | closed |
| T-04-33 (04-08) | Denial of service (cost) | spending without confirmation, over the stated budget, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage in the ledger and no authorizat | closed |
| T-04-34 (04-08) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-35 (04-08) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; the autoupdater is disabled for the child; a mismatch with the tested set stops the wave  | closed |
| T-04-36 (04-08) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | the sanitizer is built before spend; whole-folder leak gate, promote with the deny entries, an extra gate scan and a gitleaks scan before the commit; the build  | closed |
| T-04-37 (04-08) | Tampering | the model writing outside the scratch project or mutating git during the wave | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; run roots outside every home folder; snapshot, trace and git-state checks; a | closed |
| T-04-38 (04-08) | Repudiation | the evidence read as accepted, or a stopped or skipped row hidden | medium | mitigate | the folder README labels an attribution run, not the baseline; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes ne | closed |
| T-04-39 (04-09) | Tampering | the model writing into main-checkout, or planting a .git in a no-git project | high | mitigate | the manifest keeps every main-checkout entry except its git metadata, so a write is a write outside the approved roots and ends the row with 11; a planted .git  | closed |
| T-04-40 (04-09) | Elevation of privilege | the harness starting git in a project whose pointer, configuration or reference  | high | mitigate | the setup pin covers the no-git marker, the folder shape and the worktree shape (pointer, worktree folder, common folder, index entries aside); any difference s | closed |
| T-04-41 (04-09) | Information disclosure | git identity, paths or the login in filed git facts or seeds | medium | mitigate | the seeds use the pc_spike spike identity; the filed Git facts are heads, branches and digests; the sanitizer, leak gate and promote with the deny entries cover | closed |
| T-04-42 (04-09) | Repudiation | row 8a's difference from the committed run, or row 9's limited claim, hidden | medium | mitigate | the setup texts and the README paragraph state both; the comparer lists differences without judging them | closed |
| T-04-43 (04-10) | Elevation of privilege | an allowlist rule for the NUL -z form, a redirection or the sidecar file being a | high | mitigate | the row uses the baseline alone; the static test scans every buildable rule list and the committed tools files and fails on any such rule; a test proves the sca | closed |
| T-04-44 (04-10) | Tampering | hostile names breaking a line-oriented harness file or hiding a changed file | medium | mitigate | the manifest already lists names in an escaped, one-line form and a lossless ASCII JSON companion; the row 10 chain is filed through the real filing path in a t | closed |
| T-04-45 (04-10) | Information disclosure | a hostile name or the non-Latin text carrying a path or the login into tests/evi | medium | mitigate | names come from a fixed table; the sanitizer, leak gate and promote with the deny entries run on every filed file; the committed rows already file the same name | closed |
| T-04-46 (04-10) | Repudiation | the status form read from the reply, or a verdict implied about the fallback | medium | mitigate | the counts come from tool_use events, the structured denial union and the filed sidecar copy; the section holds counts and ids only and no verdict word; the Cod | closed |
| T-04-47 (04-11) | Denial of service (cost) | spending without confirmation, over the stated budget, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage in the ledger and no authorizat | closed |
| T-04-48 (04-11) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-49 (04-11) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; the autoupdater is disabled for the child; a mismatch with the tested set stops the wave  | closed |
| T-04-50 (04-11) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | the sanitizer is built before spend; whole-folder leak gate, promote with the deny entries, an extra gate scan and a gitleaks scan before the commit; the build  | closed |
| T-04-51 (04-11) | Tampering | the model writing outside the scratch project or mutating git during the wave | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; run roots outside every home folder; snapshot, trace and git-state checks; a | closed |
| T-04-52 (04-11) | Repudiation | the evidence read as accepted, or a stopped or skipped row hidden | medium | mitigate | the folder README labels an attribution run, not the baseline; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes ne | closed |
| T-04-53 (04-12) | Tampering | the injector firing on Claude Code's own startup calls or on a harness call, put | high | mitigate | whole-argv equality with a listed argv; the committed internal calls (every `-c`-prefixed line of the committed git-calls.log) are replayed against the matcher  | closed |
| T-04-54 (04-12) | Tampering | the injection writing outside the project through the inject-file value | high | mitigate | the value must be a relative name without a dot-dot that resolves to a regular file inside the project, else nothing is injected; tests plant absolute, dot-dot  | closed |
| T-04-55 (04-12) | Elevation of privilege | the wrapper changing what the model's git does or widening the allowlist | high | mitigate | it delegates unchanged to the fixed real git with every stream and the exit code intact, runs the real call first, and no allowlist rule is added; transparency  | closed |
| T-04-56 (04-12) | Denial of service | a logging, lock or injection failure breaking the model's git | medium | mitigate | every auxiliary step is best-effort and the exit code is always the real git's; a read-only wrapper folder test proves it | closed |
| T-04-57 (04-12) | Information disclosure | paths in the filed wrapper log or shim | medium | mitigate | the filed log passes the sanitizer, the leak gate and promote with the deny entries; the shim holds no path and the real git path lives only in a config file in | closed |
| T-04-58 (04-13) | Tampering | the plan-note hook writing through a symlink or outside the project, or truncati | high | mitigate | lstat must show a regular file, no symlink, realpath inside the project; the open is append-only with no create and no truncate; a test plants a symlink to an o | closed |
| T-04-59 (04-13) | Denial of service (cost) | the fourth stage taking row 12 past 2.00 | high | mitigate | the ledger refuses a launch whose settled spend plus the cap passes the row limit; worst_case reports the ledger's bound; a test settles the first three stages  | closed |
| T-04-60 (04-13) | Tampering | s4 resuming s2's session or counting its cost against the wrong chain | medium | mitigate | the stage's session key resume:B selects s3's session id; the previous total is tracked per session key; tests assert the argv and the delta | closed |
| T-04-61 (04-13) | Information disclosure | the frozen-copy section or the checkpoint copies carrying run paths | medium | mitigate | the section prints digests and counts only; the snapshot copies pass the sanitizer, the leak gate and promote with the deny entries (ASVS V8) | closed |
| T-04-62 (04-14) | Denial of service (cost) | spending without confirmation, over the stated budget, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage in the ledger and no authorizat | closed |
| T-04-63 (04-14) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-64 (04-14) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; the autoupdater is disabled for the child; a mismatch with the tested set stops the wave  | closed |
| T-04-65 (04-14) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | the sanitizer is built before spend; whole-folder leak gate, promote with the deny entries, an extra gate scan and a gitleaks scan before the commit; the build  | closed |
| T-04-66 (04-14) | Tampering | the model writing outside the scratch project or mutating git during the wave | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; run roots outside every home folder; snapshot, trace and git-state checks; a | closed |
| T-04-67 (04-14) | Repudiation | the evidence read as accepted, or a stopped or skipped row hidden | medium | mitigate | the folder README labels an attribution run, not the baseline; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes ne | closed |
| T-04-68 (04-15) | Tampering | the expected-change allowance hiding a model write under the wrapper folder | high | mitigate | exact file names from the guarded run record, no folder or pattern allowance; a scripted model write to another name under wrapper/ ends the row with 11; the fi | closed |
| T-04-69 (04-15) | Elevation of privilege | a row gaining an update, note or handoff rule (3b), a bare wrapper prefix or a d | high | mitigate | profile verbs through the one builder; the wrapper refuses bind, create and init with exit 71; seeds bind through the stub directly; tests count rules per row a | closed |
| T-04-70 (04-15) | Information disclosure | layout memory files, the local instruction file or the layout facts carrying a p | medium | mitigate | the sanitizer, leak gate and promote with the deny entries cover every filed file; the facts are counts, names and digests (ASVS V8) | closed |
| T-04-71 (04-15) | Tampering | memory pinned inside the project letting a stray memory write go unseen | medium | mitigate | the default memory root is still probed absent at every snapshot, the project is an approved root so memory writes appear in the manifest diff, and the memory a | closed |
| T-04-72 (04-15) | Repudiation | a layout run read as the full layout acceptance | medium | mitigate | each layout README lists the five checks the harness does not exercise (D-13); the comparer lists, never judges | closed |
| T-04-73 (04-16) | Denial of service (cost) | spending without confirmation, over the stated budget, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage in the ledger and no authorizat | closed |
| T-04-74 (04-16) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-75 (04-16) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; the autoupdater is disabled for the child; a mismatch with the tested set stops the wave  | closed |
| T-04-76 (04-16) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | the sanitizer is built before spend; whole-folder leak gate, promote with the deny entries, an extra gate scan and a gitleaks scan before the commit; the build  | closed |
| T-04-77 (04-16) | Tampering | the model writing outside the scratch project or mutating git during the wave | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; run roots outside every home folder; snapshot, trace and git-state checks; a | closed |
| T-04-78 (04-16) | Repudiation | the evidence read as accepted, or a stopped or skipped row hidden | medium | mitigate | the folder README labels an attribution run, not the baseline; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes ne | closed |
| T-04-79 (04-17) | Denial of service (cost) | spending without confirmation, over the stated budget, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage in the ledger and no authorizat | closed |
| T-04-80 (04-17) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-81 (04-17) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; the autoupdater is disabled for the child; a mismatch with the tested set stops the wave  | closed |
| T-04-82 (04-17) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | the sanitizer is built before spend; whole-folder leak gate, promote with the deny entries, an extra gate scan and a gitleaks scan before the commit; the build  | closed |
| T-04-83 (04-17) | Tampering | the model writing outside the scratch project or mutating git during the wave | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; run roots outside every home folder; snapshot, trace and git-state checks; a | closed |
| T-04-84 (04-17) | Repudiation | the evidence read as accepted, or a stopped or skipped row hidden | medium | mitigate | the folder README labels an attribution run, not the baseline; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes ne | closed |
| T-04-85 (04-18) | Tampering | record_verdict editing more than the one line, the wrong file or a frozen folder | high | mitigate | strict preconditions (the pending line once at the end, a row README of a non-frozen baseline, one line of text), a positional write that only grows the file, a | closed |
| T-04-86 (04-18) | Information disclosure | the review brief or the baseline README carrying a path, the login or an environ | high | mitigate | the brief and README are built from filed files and the strict clone-facts schema (names and counts only), then filed through promote_into with the leak gate, s | closed |
| T-04-87 (04-18) | Repudiation | a harness file implying or stating a verdict | high | mitigate | the brief asks for a conclusion without verdict words; the comparison quotes committed text only on marked lines; check-words covers every harness-authored file | closed |
| T-04-88 (04-18) | Tampering | the frozen digest normalisation hiding a second change in a README or another fi | high | mitigate | exactly one line per row README and the single name codex-review.md are normalised or left out; mutation tests change a trace byte, a second README line and an  | closed |
| T-04-89 (04-18) | Elevation of privilege | evidence-readme writing more than its one file into the evidence root | medium | mitigate | the evidence-root allowance of promote_into accepts one flat name only and refuses an existing file; tests try a second name and a subfolder | closed |
| T-04-90 (04-19) | Information disclosure | the child inheriting the caller's environment (a cloud key, a token, a git ident | high | mitigate | the child environment is built from an empty dict with exactly seven names; a test starts a child with a noisy caller environment and asserts it sees none of it | closed |
| T-04-91 (04-19) | Spoofing | the private helper being reachable, so a call that the baseline calls a stub cal | high | mitigate | pre-assertions count checkpoint executables on the scrubbed PATH, files named checkpoint in the clone and under the throwaway HOME (all 0); post-assertions read | closed |
| T-04-92 (04-19) | Tampering | the clone carrying code that runs on the owner's machine, or hooks or an identit | high | mitigate | the clone is of the owner's own repository only; NOSYSTEM, the null global configuration and no terminal prompt apply; hooks are off in a fresh clone; the clone | closed |
| T-04-93 (04-19) | Information disclosure | a path, the origin address or the login reaching a printed line, the clone-facts | high | mitigate | the origin address is read at run time and never stored; clone-facts values are names, counts and a head only; the finalized folder goes through the sanitizer a | closed |
| T-04-94 (04-19) | Elevation of privilege | the real home being handed to the child by default, or a login being run | medium | mitigate | the real home needs the explicit --real-home flag, is printed and recorded as home_kind real, and is never used by a task of any plan without bokiko's word; the | closed |
| T-04-95 (04-19) | Denial of service (cost) | the matrix running over budget or twice | high | mitigate | the matrix is the clone's own pc_matrix.py with the --budget the caller gave and the ledger scope matrix (plan 04-02); the paid step is only in plan 04-20 behin | closed |
| T-04-96 (04-19) | Tampering | the copy-back overwriting or mixing evidence in the main tree | medium | mitigate | promote refuses an existing destination (17) and creates exclusively; a leak refuses before any write; the bootstrap never deletes the clone folder or reuses a  | closed |
| T-04-97 (04-20) | Denial of service (cost) | spending without confirmation, over the stated budget, twice, or more than 21 ch | high | mitigate | a blocking-human checkpoint before any push or spend; the `--budget` amount he named with the stop-before-row rule; one launch per stage under the matrix scope  | closed |
| T-04-98 (04-20) | Spoofing | an agent message or summary treated as bokiko's consent to spend or push | high | mitigate | gate type blocking-human, which no mode auto-approves; resolved only by his own message quoted in a fresh dispatch; an executor that cannot see his words refuse | closed |
| T-04-99 (04-20) | Information disclosure | the push or the baseline carrying a path, the login, a host name, a credential o | high | mitigate | every commit that reaches the push passed the Phase 1 hooks and the leak gate and gitleaks at its own plan; the baseline passed the sanitizer, the leak gate and | closed |
| T-04-100 (04-20) | Tampering | the clone containing different code from the owner's, so the run proves somethin | high | mitigate | the clone is of the owner's own origin after his push; the clone head and the pushed tip are recorded and compared in the summary; the bootstrap never commits o | closed |
| T-04-101 (04-20) | Tampering | a model writing outside its scratch project or mutating git during any of 21 cha | high | mitigate | `--permission-mode default` with the pinned allowlists and no skip-permissions flag; run roots outside every home folder in the clone's runs folder; snapshot, t | closed |
| T-04-102 (04-20) | Elevation of privilege | the real home being given to the child, or a build other than 2.1.310 running | medium | mitigate | `--real-home` only for the explicit `go-real-home` answer and recorded as home kind real; `--claude` names the exact build and the preflight must print OK for i | closed |
| T-04-103 (04-20) | Repudiation | the baseline read as accepted, or stopped, skipped or other-helper calls hidden | high | mitigate | the README labels a new baseline and not a replication; every row README ends with the pending verdict line; STOPPED and SKIPPED labels and exit codes never rea | closed |
| T-04-104 (04-21) | Spoofing | an agent writing or inventing verdict text, or treating its own message as bokik | high | mitigate | the filed lines come only from his pasted message, one row at a time, after a blocking-human checkpoint no mode auto-approves; the executor adds only the consul | closed |
| T-04-105 (04-21) | Tampering | the verdict edit touching more than one line, the wrong file or a frozen folder | high | mitigate | record_verdict's strict preconditions and positional in-place write (plan 04-18), one folder per call; after the edits the frozen digest must equal the digest r | closed |
| T-04-106 (04-21) | Information disclosure | Codex's pasted text or a verdict line carrying a path, the login or a credential | high | mitigate | file-review and record-verdict gate every byte with the leak scanner before any write and refuse with the leak code; the gate, gitleaks and the pre-commit hooks | closed |
| T-04-107 (04-21) | Tampering | markup or instructions inside the pasted review altering the evidence structure  | medium | mitigate | the review is stored verbatim as data in one file whose name is fixed, never parsed or executed; a verdict line is one line of at most 400 characters inside a f | closed |
| T-04-108 (04-21) | Repudiation | a rejection or a reservation by Codex hidden by filing only agreeable lines | high | mitigate | the whole pasted answer is filed in codex-review.md; each row line is his own choice of line, and a row he leaves out stays pending and is named in the summary; | closed |
| T-04-109 (04-21) | Elevation of privilege | the swap made without his word or as part of filing | high | mitigate | the swap is its own commit after the verdicts and only for the word `file-and-swap`; `file-only` makes no commit 3; the publication folder is never edited and i | closed |
| T-04-110 (04-21) | Tampering | the README cost block drifting from the evidence, or a currency figure appearing | medium | mitigate | one marked block whose figures are read by a test from the filed digest table and the first baseline's usage file; the currency ban holds outside it | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Verification evidence (gsd-security-auditor, 2026-11-11)

| Threat IDs | Status | Evidence |
|---|---|---|
| T-04-01 | CLOSED | `pc_row1._entry_of` uses an exact `pc_rows.find_runnable` match. `test_row_generic` test_an_unknown_or_odd_id_raises_before_anything_is_created. |
| T-04-02, T-04-17 | CLOSED | `test_row_generic` test_every_setup_text_is_free_of_path_shaped_strings and `test_rows_plain` test_the_data_files_and_every_setup_text_hold_no_path_shaped_string. Filing runs `pc_evidence.file_row`, then `stage_tree` with the sanitizer, then `pc_promote.promote` with deny entries. |
| T-04-03 | CLOSED | `test_runroot.SCAN_EXEMPT` is only `pc_testutil` and `pc_seeds`. My own scan of the other 26 modules found no delete, rename or truncate construct. |
| T-04-04 | CLOSED | `test_row_generic` test_a_scripted_write_outside_the_run_root_ends_with_11_and_files_nothing. |
| T-04-05 | CLOSED | `test_row_generic.Row1ParityTests` test_the_filed_names_equal_the_committed_baseline_names_none_added_none_missing. |
| T-04-06 | CLOSED | `pc_matrix._run_rows` stop-before-row, `_check_earlier_attempt`, and `pc_spend.append_launch` before `pc_row1.run_stage` starts a process. `test_driver_matrix` budget-stop tests. |
| T-04-07, T-04-08 | CLOSED | `pc_rows.is_valid_campaign`, `_scoped`, `parse_evidence_date`, `pc_matrix._parse_attempt`. `test_driver_matrix` test_a_bad_label_is_refused_with_exit_2_and_the_value_is_never_echoed and test_no_two_selections_give_the_same_ledger_id. |
| T-04-09 | CLOSED | `pc_matrix.summary_lines` prints fixed text. `test_driver_matrix.assert_clean` runs on every case. |
| T-04-10, T-04-13, T-04-28 | CLOSED | `pc_matrix._aggregate_code` never returns 0 for a skip or stop. SKIPPED and STOPPED label folders in `pc_evidence`. State column in `pc_baseline.read_items`. `test_driver_matrix` test_a_skip_only_run_exits_10_and_never_0 and the `test_row7` skip tests. |
| T-04-11 | CLOSED | `pc_evidence.file_stopped` sanitizes, then promotes with deny entries. `test_baseline` test_a_leak_shaped_string_in_a_stopped_stage_is_refused_with_14_and_nothing_is_filed. |
| T-04-12 | CLOSED | `pc_promote._check_folder`, `_flat_names`, `promote_into`, `pc_runroot.write_exclusive`. `test_promote.PromoteIntoTests`, including folder-unchanged assertions. |
| T-04-14 | CLOSED | `pc_baseline._digest_values` and the strict readers. `test_baseline` test_model_written_text_cannot_steer_the_table. |
| T-04-15, T-04-69 | CLOSED | `pc_flags.build_row_tools` gives no wrapper rule to plain and git profiles. `checkpoint-wrapper` exits 71 for bind, create and init. `test_rows_plain` test_the_plain_allowlist_is_the_baseline_plus_the_two_extras_and_no_wrapper_rule, `test_rows_helper` test_every_helper_profile_row_lists_wrapper_rules_by_verb_and_never_a_bare_prefix_or_a_driver_verb. |
| T-04-16, T-04-71 | CLOSED | `pc_flags.render_settings` pins the memory directory. `test_rows_plain` test_5a_and_5b_a_scripted_write_to_the_default_memory_root_ends_the_row_with_11_and_files_a_label. |
| T-04-18 | CLOSED | `test_rows_plain` byte-tie tests for the seeded files, the plan digest and the 5a against 5b comparison. |
| T-04-19, T-04-24, T-04-58 | CLOSED | `pc_rowhooks._open_target`, `_set_modes` with `os.fchmod` on an opened descriptor, and `append_plan_note` with append-only open and an inode check. `test_boundaries` symlink and swapped-parent tests, `test_row7` hook tests, `test_row12` symlink tests. |
| T-04-20 | CLOSED | `pc_checks.read_boundaries`, `present_boundaries`, `write_boundaries`, called before the setup guard in `pc_row1._run_registered_row`. `test_boundaries`. |
| T-04-21, T-04-27 | CLOSED | `pc_rowhooks.perms_text` writes mode-only lines from fstat. Mode-only shape confirmed in all 7 filed perms.txt files. `test_row7` test_row7_perms_text_holds_no_owner_group_date_size_or_login_name. |
| T-04-22 | CLOSED as accepted | `pc_row1.restore_hooks` runs on every exit path. The orchestrator must record the accepted-risk entry in SECURITY.md. It is low severity, so it never counts toward threats_open. |
| T-04-23 | CLOSED | `pc_rowhooks._probe_chmod` and `chmod_denial_probe`. `test_row7` test_probe_a_planted_link_in_place_of_the_folder_is_refused_and_nothing_outside_is_changed. |
| T-04-25 | CLOSED | The probe runs before any ledger line in `pc_row1._run_registered_row`. `test_row7` test_skip_no_session_ran_and_the_ledger_holds_no_line_and_no_stage_record_exists. |
| T-04-26, T-04-32 | CLOSED | `pc_row1.printed_checkpoint` with the 8192-byte and NUL rules. `pc_review` MAX_ENTRIES, MAX_ENTRY_CHARS, MAX_EXCERPT_CHARS, MAX_CANDIDATES. `test_row7` extract tests and `test_review` test_over_cap_input_gives_bounded_files. |
| T-04-29 | CLOSED | `pc_review.quote_line` and `one_line`. `test_review.HostileTextTests`. |
| T-04-30 | CLOSED | Sanitizer inside `quote_line`, then the gate. `test_review` test_a_path_shaped_string_in_a_filed_entry_is_refused_with_14_and_nothing_is_written. |
| T-04-31, T-04-87 | CLOSED | `pc_evidence.verdict_pattern` and the `check-words` command. `test_baseline.CheckWordsTests`. My own `check-words` run found 0 hits across all six folders. |
| T-04-39, T-04-40, T-04-41, T-04-42 | CLOSED | `pc_checks.capture_boundary_state` and `pinned_gitdir` start no git on a changed pin. `test_rows_git` tripwire tests for planted `.git`, config and pointer, the spike-identity tests, and the setup-text test. |
| T-04-43 | CLOSED | `test_rows_git` test_no_rule_of_any_buildable_allowlist_holds_a_nul_form_a_redirection_tee_output_or_the_sidecar and test_the_scan_can_fail_on_a_hand_built_list_with_a_redirection_or_a_nul_rule. |
| T-04-44, T-04-45 | CLOSED | `pc_manifest.escape_name` and `jsonl_bytes` with `ensure_ascii`. `test_manifest` escape tests and the row 10 filing tests. |
| T-04-46 | CLOSED | `pc_review` status-form counts from tool_use events. `test_review.StatusFormTests` test_the_section_holds_counts_ids_and_present_or_absent_and_no_verdict_word. |
| T-04-53 to T-04-57 | CLOSED | `git-wrapper` uses whole-argv equality, a plain-relative inject-file check, the real git exit code, best-effort auxiliary steps, and a shim with no path. `test_git_wrapper` near-miss, inject-file, read-only-folder and shim-text tests. |
| T-04-59, T-04-60, T-04-61 | CLOSED | `pc_spend.append_launch` row-limit refusal. Per-key totals in `pc_row1._walk_stages`. `test_row12` test_the_s4_launch_is_refused_with_18_before_any_process_when_the_first_three_settled_past_the_bound, the s4 delta tests, and the frozen-copy section test. |
| T-04-68, T-04-70, T-04-72 | CLOSED | `pc_checks.validated_expected_changes` accepts exactly five names. `test_rows_helper` test_exactly_the_five_wrapper_names_are_accepted_in_any_order_and_subset. `pc_rows.py` setup text lists the five unexercised checks, confirmed in the filed layout READMEs. |
| T-04-85, T-04-88, T-04-89 | CLOSED | `pc_baseline.record_verdict`, `frozen_digest` and `evidence_readme`. `test_frozen_baseline.VerdictLineTests` and `FrozenDigestTests`, and `test_baseline.EvidenceReadmeTests`. |
| T-04-86 | CLOSED | `pc_baseline.read_clone_facts` strict schema. `test_baseline.CloneFactsTests`, including test_the_schema_holds_no_key_that_could_carry_a_path_or_a_login. |
| T-04-90 | CLOSED | `pc_cleanclone.build_child_env` starts from an empty dict. `test_cleanclone` test_nothing_of_a_noisy_caller_environment_reaches_the_builder_result. USER is the one added name under the real-home flag, tested separately. |
| T-04-91 | CLOSED | `pc_cleanclone.pre_assertions`, `post_assertions` and `post_refused`, ending in exit 11. Baseline README records 24 helper calls, 24 to the stub, 0 to anything else. |
| T-04-92, T-04-100 | CLOSED | `clone_repository` with `git_env` and `--no-hardlinks`. Identity and hook-key counts must be 0. Clone head 0bacd2b is an ancestor of `origin/main` and equals the pushed tip. |
| T-04-93 | CLOSED | `pc_cleanclone.Scrubber`, clone-facts schema, and `copy_back` with the main tree's deny entries. `test_cleanclone` path-free and origin-never-written tests. |
| T-04-94 | CLOSED | `--real-home` is an explicit flag and is recorded as home kind real. `test_cleanclone` test_the_real_home_is_given_only_with_the_explicit_flag. |
| T-04-95, T-04-96 | CLOSED | The clone runs its own `pc_matrix.py --all` with `--budget`. `pc_promote.promote` refuses an existing destination. `test_cleanclone` test_an_existing_destination_is_refused_with_17_and_left_unchanged. |
| T-04-104, T-04-108 | CLOSED | All 21 closing lines in the baseline equal the text in `codex-review.md`. The reservations on rows 6, 7 and 10 are present in both places. No invented model or date. |
| T-04-105 | CLOSED | I recomputed the baseline frozen digest, 1e4f68bb, and the publication tree digest, 26881820. Both equal the pins in `test_frozen_baseline` and `test_frozen_tree`. |
| T-04-106, T-04-107 | CLOSED | `pc_baseline.file_review` goes through `promote_into` with the gate. The first filing was refused with exit 14, as designed. `MAX_VERDICT_TEXT` is 400. The review is stored as data and the vocabulary scan skips it. |
| T-04-109 | CLOSED | bokiko's word resolved to file-only. No swap commit exists. `pc_compare.DEFAULT_REFERENCE` is still the publication folder. |
| T-04-110 | CLOSED | `test_readme` test_there_is_exactly_one_cost_block, test_the_block_holds_no_other_decimal_figure, and the currency-ban test. |

**Recurring paid-wave threats** cover plans 04-08, 04-11, 04-14, 04-16, 04-17 and 04-20.

| Threat IDs | Status | Evidence |
|---|---|---|
| Spend: T-04-33, 47, 62, 73, 79, 97 | CLOSED | Stop-before-row in `pc_matrix._run_rows`. Stop on any other code. Per-stage caps in `pc_flags.build_argv`. Launch reserved before the process in `pc_row1.run_stage`. The ledger holds 118 launch lines, 118 settle lines and 118 distinct stages. No stage launched twice and 0 authorization lines. |
| Spoofing: T-04-34, 48, 63, 74, 80, 98 | CLOSED | Blocking-human gates. Executors refused a quoted go in waves C, D, the triple and the matrix. The orchestrator ran those commands on bokiko's own typed word, as 04-14, 04-16, 04-17 and 04-20 SUMMARY record. No agent-originated consent found. |
| Build: T-04-35, 49, 64, 75, 81, 102 | CLOSED | `pc_flags.TESTED_VERSIONS` is exactly 2.1.310, and `pc_preflight` returns UNTESTED with exit 13 otherwise. `DISABLE_AUTOUPDATER=1` is set. Real home needed bokiko's "3.yes", recorded in 04-20 SUMMARY deviation 2. |
| Disclosure: T-04-36, 50, 65, 76, 82, 99 | CLOSED | Sanitizer, `promote` with deny entries, and fail-closed hooks. `.githooks` and `.gitleaks.toml` are unchanged since the phase base. |
| Tamper: T-04-37, 51, 66, 77, 83, 101 | CLOSED | `--permission-mode default` with no skip flag, checked in `test_flags` and `test_stages`. `pc_spike.runs_root` refuses roots under any home. Breach ends in a STOPPED folder with exit 11. No STOPPED or SKIPPED folder exists in any Phase 4 evidence folder. |
| Repudiation: T-04-38, 52, 67, 78, 84, 103 | CLOSED | Wave READMEs say attribution run, not baseline. Every wave row README ends with the pending line. The baseline README says new baseline, Run state complete. Its 21 closing lines come from the filed review. |

### Auditor observations outside the register (advisory, no new threat opened)

None of these change a verdict or threats_open.

- **Local deny file absent.** `.git/info/preclear-deny.txt` does not exist in this checkout. The history deny-list check exits 3 for that reason. The gate still enforced host names and, through the sanitizer, the login. If bokiko expects a real-name entry to be enforced, it is not. The 04-21 SUMMARY says his name was on the local list, which this does not match.
- **No Threat Flags section in 04-11 SUMMARY.** That plan was a paid wave with no new code, so no mapping is lost.
- **Real-home matrix run.** The child ran with the real home and USER under `--real-home`. Containment there is detective only, through snapshots and the write-boundary checks. The run filed 21 of 21 with 0 breaches.
- **Possible false alarm.** A read hook flagged invisible unicode in `pc_baseline.py`. It is two literal line-separator characters inside a text-validation set in `record_verdict`. It is not an injection.

**Accepted rows for SECURITY.md.** T-04-22 is accepted because the finalizer runs on every exit path, and a killed process can leave one scratch file at mode 444 inside the run root. The 21 T-04-SC rows are accepted because Phase 4 installs nothing. I confirmed no dependency manifest changed since the phase base, and `test_imports` enforces standard-library imports.

**My read-only checks:**
- gitleaks found 0 findings over `tests/evidence`, `tests/harness` and the 104 commits since 613054d.
- The harness leak gate found 0 findings over all six Phase 4 evidence folders: 194, 286, 144, 523, 172 and 1203 files.
- `check-words` found 0 hits over the same six folders.
- Greps for home paths, private addresses and the login found 0 hits in Phase 4 evidence.
- The static no-delete scan from `test_runroot` found 0 findings over 26 modules.
- The spend ledger holds 118 launch and 118 settle lines, 118 distinct stages, at most one launch per stage and 0 authorization lines.
- Frozen digests recomputed and equal to the pins: baseline 1e4f68bb, publication tree 26881820, first baseline f186124f.
- The 21 closing lines in the baseline equal the entries in `codex-review.md`.
- `origin/main` equals HEAD a8b7f83, and the working tree shows only the two untracked planning files.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-22 (04-05) | the finalizer runs on every exit path of the row; only a killed process can leave one scratch file at mode 444 inside the run root, which the owner can change a | bokiko (plan 04-05 approved at planning) | 2026-11-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-11 | 110 | 110 | 0 | gsd-security-auditor (sonnet), verify-mitigations mode, register authored at plan time |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-11
