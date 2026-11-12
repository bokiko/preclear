---
phase: "03"
slug: "walking-skeleton-row-1"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-12"
---
# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail. Written retroactively on 2026-11-12 by /gsd-secure-phase from the plans' threat models and the security auditor's verdict; the implementation was not changed.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| argv and environment to the driver | untrusted ids, paths and amounts decide what runs, where it is written and how much may be spent | see description |
| the driver to the `claude` executable | `--claude` names a program that the harness will execute with the harness environment | see description |
| the driver to the harness home | the spend ledger and the login live there; the repository must never hold either | see description |
| printed text to the terminal and later files | an echoed argument, path, host or login would itself be a leak | see description |
| the real `claude -p` process and the model's tool calls versus the scratch project | bare Write and Edit rules let a model write anywhere; the run root and the later checks are the only containment evidence | see description |
| the harness-owned config folder and the login | the credential lives there; the harness passes the folder by environment only | see description |
| the spend ledger and the 2 USD row cap | a stage that starts twice or ignores a cap spends real money | see description |
| captured stream bytes to parsed facts | the stream is written by a model-driven process | see description |
| the model's tool calls versus the scratch project | bare Write and Edit rules and a handful of write-capable programs can reach any path the account can write | see description |
| the harness config folder and the login | the credential lives there; a check must not read it | see description |
| stream, log and snapshot bytes to facts | all of them are produced by a model-driven process or by files it can touch | see description |
| the stub ledger and a model-written body | a body holding a marker line corrupts the block and looks like a skill failure | see description |
| the run root to `tests/evidence/` | the one route from raw model-driven bytes to public history; the sanitizer, the leak gate and promote guard it | see description |
| the sanitizer to the gate | the login joins the gate only through the sanitizer's deny entries (WR-14) | see description |
| the destination folder name | a taken name must be refused, never reused | see description |
| harness-authored text to the reviewer | a verdict word in the harness's own text would be an acceptance claim without a review | see description |
| the comparer to the two evidence trees | the comparer reads trees that must stay byte-identical; a write there would corrupt the reference | see description |
| report text to the reviewer | a verdict word in the comparer's output would be an acceptance claim without a review | see description |
| the frozen trees to the suite | a silent change to the skill, fixtures or committed evidence would invalidate carried-forward evidence | see description |
| the spend ledger and the 2.00 row cap | the single place real money is spent | see description |
| the leak gate between the run root and tests/evidence | the one route from raw model output to public history | see description |
| the committed reference folder | must stay byte-identical | see description |
| model to the project repository's own git folder | the model can write .git/config, attribute files and other git state inside its working project; the harness then runs git there as the harness user | see description |
| model to the Bash tool | the allowlist permits programs that can write anywhere the harness user can (mkdir, python3 -c, awk, sed, find, env, cd) | see description |
| model to the run root's own record | raw/, snaps/ and the hook log sit beside the project and are read back by the checks and by the filing | see description |
| harness checks to a paid run | a false breach discards a paid row and a retry needs bokiko's explicit word | see description |
| run root on disk to public evidence | a finished or half-finished run root can be filed into tests/evidence by the live path or by --refile; filed evidence is the record of a clean run | see description |
| sanitizer and deny entries to promote | the login and the local deny list are checked by the gate only when the caller hands the entries over | see description |
| the stub's output through the Bash tool to a filed fact | the first line of a real status result is the helper's brand line | see description |
| harness-written files to the reviewer | the filed facts, the usage lines and the checklist are what a reviewer reads without the harness's help | see description |
| model to the project's own git folder and any repository inside the project | the model can write .git/config and attribute files of the project and of a nested repository it creates; the harness then runs git there as the harness user | see description |
| harness-written facts to the reviewer | the filed facts and cost-consistency lines are what a reviewer reads without the harness's help | see description |
| model to the run root's own files | a script or program file the model writes inside the project can be run later by a program the allowlist reaches through env | see description |
| model to the project's git folder and nested folders | a command named in configuration or in a nested repository's own folder runs under the harness's git calls | see description |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-01 (03-01) | Tampering | `--row`, `--layout` and `--authorize-retry` values reaching a folder name or pat | medium | mitigate | the id pattern and an exact whole-id registry match run before any use; only registry ids reach a path or a file name; every refusal is fixed text with no ec... | closed |
| T-03-02 (03-01) | Denial of service (cost) | a real run started by accident, by a typo or by `--all` | high | mitigate | a real run needs `--budget` at least the printed worst case or exits 18 before any process; the dry run is free and prints the worst case first; the per-row ... | closed |
| T-03-03 (03-01) | Elevation of privilege | `--claude PATH` executes an arbitrary file with the harness environment | medium | mitigate | the path must be absolute, existing and an executable regular file; it is run as an argument list with no shell and the `build_env` scrub; the exact-match ve... | closed |
| T-03-04 (03-01) | Tampering | double spend through a race or a lost update of the ledger | high | mitigate | one file lock around read, check and append; append-only O_APPEND lines with mode 0600; fail closed on any malformed line; one attempt per stage (review WR-0... | closed |
| T-03-05 (03-01) | Elevation of privilege | an agent types `--authorize-retry` instead of bokiko | medium | mitigate | no task of this phase runs the flag; a launch without the line is refused; the paid-run plan stops and asks bokiko before any retry; the residual (a line pro... | closed |
| T-03-06 (03-01) | Information disclosure | messages echoing an untrusted value, a path, a host name or the login | medium | mitigate | fixed texts, ids and counts only; tests assert a distinctive probe never appears in stdout or stderr (ASVS V7) | closed |
| T-03-07 (03-01) | Denial of service | `--dry-run` starting a process or writing a file | medium | mitigate | an in-process subprocess trap, a tripwire claude first on PATH and a missing-harness-home assertion all stay silent in tests | closed |
| T-03-08 (03-01) | Information disclosure | the BLOCKED login instruction printing the config folder | low | accept | it is printed only to the caller's own terminal and the README holds the token form, never the real path | closed |
| T-03-SC (03-01, 03-02, 03-03, 03-04, 03-05, 03-06, 03-07, 03-08, 03-09, 03-10, 03-11, 03-12) | Tampering | npm, pip and cargo installs | low | accept | this plan installs nothing; standard library only | closed |
| T-03-09 (03-02) | Tampering | model tool calls reaching outside the scratch project through bare Write and Edi | high | mitigate | `--permission-mode default` with the pinned literal allowlist, never a skip-permissions flag (a test asserts the argv), run roots outside every home folder (... | closed |
| T-03-10 (03-02) | Information disclosure | the login and credential files in the harness config folder | high | mitigate | the folder is reached only through CLAUDE_CONFIG_DIR from build_env; tree_manifest is never pointed at it and snapshots walk the run root only; preflight rea... | closed |
| T-03-11 (03-02) | Denial of service (cost) | a stage that ignores its cap or starts twice | high | mitigate | the cap is an argv value and a ledger reservation made before the process; one attempt per stage; the chain stops at the first stage that is not a clean succ... | closed |
| T-03-12 (03-02) | Spoofing | untrusted stream bytes and a model-written resume line | medium | mitigate | the strict pc_stream parser and structured signals only; the resume line is the last fenced single line starting `Resume `, at most 2000 bytes with no NUL; s... | closed |
| T-03-13 (03-02) | Tampering | reuse or overwrite of a run root, snapshot or record | medium | mitigate | every file and folder is created with O_EXCL or mkdir; a taken name is exit 16 or FileExistsError; nothing is replaced | closed |
| T-03-14 (03-02) | Repudiation | the model writing into raw/ to alter the hook log or stream | medium | mitigate | the raw folder is outside the approved roots, the logger is appended by the hook command, raw is excluded from snapshots by design and the trace scan of plan... | closed |
| T-03-15 (03-02) | Information disclosure | the sanitizer or the deny entries built after the paid call (review WR-12) | high | mitigate | run_row builds both before the first ledger line; SanitizerError and ScannerError are exit 15 with no spend; a test patches the git call to fail and asserts ... | closed |
| T-03-16 (03-02) | Denial of service | a stage that hangs | medium | mitigate | per-stage timeouts, a settle without delta that keeps the cap, chain stop, raw bytes kept | closed |
| T-03-17 (03-02) | Information disclosure | the shared runs-root parent read by the gate as a home folder | medium | mitigate | the caller map sends the runs root, its parent and a two-component users or home prefix to the scratch token, longest match first; a test shows the parent su... | closed |
| T-03-18 (03-03) | Tampering | an undetected write outside the approved roots, the headline risk of the phase | high | mitigate | three nets: the snapshot diff by full digest with a component-aware root test, the executed Write and Edit path scan with realpath, and the single lstat of t... | closed |
| T-03-19 (03-03) | Tampering | an undetected git mutation | high | mitigate | state compared at setup and after every stage (HEAD, branch, refs digest, git folder digest without the index), staged entries counted, executed mutating for... | closed |
| T-03-20 (03-03) | Spoofing | a check that believes the model's own claims | medium | mitigate | facts come from snapshots, structured stream fields and the wrapper log only; a test shows reply text claiming no writes changes no count (ASVS V5) | closed |
| T-03-21 (03-03) | Information disclosure | the memory probe or any check reading the config folder | medium | mitigate | one lstat on a constructed path; tests patch open, listdir, scandir and walk to raise under the config folder; snapshots walk the run root only | closed |
| T-03-22 (03-03) | Tampering | the stub's end-marker bug producing a ledger state no real helper shares (review | medium | mitigate | update refuses a marker-bearing body with exit 4 before any write; CLI tests prove the bytes stay unchanged and the next update works; a branch-table row rec... | closed |
| T-03-23 (03-03) | Denial of service | a false breach after the money is spent (a heuristic read as a violation) | medium | mitigate | only concrete writes and git state or executed mutating calls decide exit 11; Bash path mentions, changed ledgers and helper-call mismatches are facts; raw b... | closed |
| T-03-24 (03-04) | Information disclosure | a leak (login, home path, host, temp path, scratch folder, credential shape) rea | high | mitigate | every staged file is sanitized with the sanitizer built before spend, the whole stage is gated and promoted once with `deny_entries()` and the config folder ... | closed |
| T-03-25 (03-04) | Tampering | overwrite or reuse of an evidence folder, a stage folder or a snapshot | high | mitigate | the destination is checked before spend and promote refuses an existing one (17); stage folders, staged files and the destination are exclusive; two writers ... | closed |
| T-03-26 (03-04) | Repudiation | a verdict word in a harness-authored file making an acceptance claim without a r | medium | mitigate | neutral `name: value` text, yes and no for booleans; a vocabulary test over the harness-authored set with the one allowed line; the row README ends with `Rev... | closed |
| T-03-27 (03-04) | Information disclosure | raw streams, the NUL status capture, the hook log, stage records or git state fi | medium | mitigate | an explicit staging list renders only named files; a test walks the promoted folder for forbidden names and suffixes and for NUL bytes; the gate refuses NUL | closed |
| T-03-28 (03-04) | Denial of service | a refusal after the paid stages wasting the run | medium | mitigate | every pre-spend refusal comes first; filing reads the run root only, so `--refile` repeats the checks and the filing for zero tokens; stage folders are numbe... | closed |
| T-03-29 (03-04) | Spoofing | a SKIPPED row read as a pass or a result | medium | mitigate | a folder named SKIPPED- plus the row id, a README that says no session was run, no usage and no snapshots in it, exit 10 and never 0 | closed |
| T-03-30 (03-04) | Information disclosure | the owner's login or the real config folder path in harness text | medium | mitigate | the text says the reviewer; run-root-relative tokens; the sanitizer and the gate cover anything that slips through; a test asserts the synthetic login never ... | closed |
| T-03-31 (03-04) | Tampering | a prompt or data file changing between the run and a refile | low | mitigate | each stage prompt is stored verbatim under raw at run time and a refile reads that copy; a missing copy is exit 11 | closed |
| T-03-32 (03-05) | Tampering | the comparer editing either evidence tree (EVID-06) | high | mitigate | read-mode opens only, no write primitive in the module (the static scan covers it); tests on write-protected copies and with every write primitive patched to... | closed |
| T-03-33 (03-05) | Repudiation | a verdict word in the comparer's own output | medium | mitigate | neutral section headings and `name: value` lines; a vocabulary test over the comparer's words for the committed row against a fake new side; quoted heading t... | closed |
| T-03-34 (03-05) | Tampering | a silent change to SKILL.md, references, tests/fixtures or the committed evidenc | medium | mitigate | pinned sha256 values and a size cap in a permanent test, computed only from the tree that the base-commit diff shows unchanged and never edited to fit a change | closed |
| T-03-35 (03-05) | Denial of service | an odd tree (a symlink, an oversized or unreadable file) making the comparer loo | low | mitigate | tree_manifest never follows symlinks and raises on walk errors, mapped to exit 2; parsers tolerate missing and malformed files and report them; the run never... | open |
| T-03-36 (03-05) | Information disclosure | the report or an error naming an absolute path, a host or the login | low | mitigate | output names the row id, folder base names, relative file names, counts and digests only; usage and read errors are fixed text; a test asserts no path appear... | closed |
| T-03-37 (03-06) | Denial of service (cost) | spending without confirmation, over the cap, or repeating a stage | high | mitigate | a blocking-human checkpoint before any spend; `--budget 2.00` equals the printed worst case; one launch per stage in the ledger and no authorization line; a ... | closed |
| T-03-38 (03-06) | Spoofing | an agent message or summary treated as bokiko's consent | high | mitigate | gate type blocking-human, which no mode auto-approves; the checkpoint is resolved only by bokiko's own message in the conversation; the executor returns to t... | closed |
| T-03-39 (03-06) | Elevation of privilege | running a different or auto-updated build | medium | mitigate | `--claude` names the exact build; preflight must print OK for 2.1.310; DISABLE_AUTOUPDATER is set for the child; the banner and each stage's recorded version... | closed |
| T-03-40 (03-06) | Information disclosure | the login, a home path, a host name or the build path reaching tests/evidence or | high | mitigate | sanitizer built before spend, whole-stage gate, promote with the deny entries; an extra Python gate scan and a gitleaks scan of the folder before the commit;... | closed |
| T-03-41 (03-06) | Tampering | the model writing outside the scratch project or mutating git during the real ru | high | mitigate | `--permission-mode default` with the pinned allowlist and no skip-permissions flag; the run root outside every home folder; snapshot, trace and git-state che... | closed |
| T-03-42 (03-06) | Repudiation | the evidence read as a replication or as an accepted result | medium | mitigate | the folder README labels it a new baseline and not a replication; the row README ends with `Reviewer verdict: PENDING`; acceptance is claimed only after the ... | closed |
| T-03-43 (03-06) | Tampering | a hook bypass or a pushed, unreviewed evidence folder | medium | mitigate | the commit runs the Phase 1 hooks and never `--no-verify`; nothing is pushed; the folder is committed locally only | closed |
| T-03-44 (03-06) | Information disclosure | the summary or a message quoting a path | medium | mitigate | the summary quotes counts, ids and repo-relative names only and is scanned with the Python gate before it is committed | closed |
| T-03-45 (03-07) | Elevation of privilege | the harness's git status and state reads in the model-writable project (a core.f | high | mitigate | both options set to false on every harness git call (pc_manifest.GIT_HARDENING shared with pc_checks); a planting test with a control that proves the plant r... | closed |
| T-03-46 (03-07) | Elevation of privilege | a clean-filter driver defined in .git/config and selected by an attributes file, | high | mitigate | the gitdir digest recorded at setup pins every later git call: once the folder differs, no git process is started, take_snapshot writes the fixed not-run tex... | closed |
| T-03-47 (03-07) | Tampering | a write-capable Bash program writing outside the approved roots, invisible to th | high | mitigate | the write-escape rule counts an executed write-capable part that names an outside place into the writes-outside-approved-roots breach and ends the row with 1... | closed |
| T-03-48 (03-07) | Tampering | the same write reached by a tilde, $HOME, a dot-dot segment, a cd that moved the | high | mitigate | each shape is a row of the escaping table (FA-3, FA-4); realpath comparison for absolute words; the part-by-part cd flag | closed |
| T-03-49 (03-07) | Tampering | code that computes its target at run time, other variable expansions, a working  | medium | accept | not decidable from the command text; the pinned allowlist and the binary's own permission layer are the first net (six expansion refusals in the baseline), t... | closed |
| T-03-50 (03-07) | Tampering | the model rewriting the hook log, a raw stream or record, a snapshot manifest, o | high | mitigate | the per-boundary guard (digest of every raw file, tree digest of every snapshot, hook-log prefix check, name judging) and the stage-prefixed folder no longer... | closed |
| T-03-51 (03-07) | Repudiation | an unreadable default-memory reading or a missing git state file silently removi | medium | mitigate | memory_probe raises CheckError and compute_facts raises on a missing state file or guard; both end the row with the unreadable-run-root line and exit 11 | closed |
| T-03-52 (03-07) | Denial of service | a false breach discarding a paid row (the cost is spent and a retry needs bokiko | medium | mitigate | the escape rule is tabled both ways (FA-5): harmless read-only, inside-the-roots, /dev/null and descriptor shapes are zero; the known conservative cases are ... | closed |
| T-03-53 (03-07) | Information disclosure | new fixed lines, facts or test labels echoing a path, a command, a marker name o | medium | mitigate | counts, ids and kind names only; tests assert that the printed lines hold no path and no folder of the rig; planted markers live in temporary folders | closed |
| T-03-54 (03-08) | Tampering | --refile (and any other caller of file_row) filing a run the live path refused a | high | mitigate | _unfileable reads each stage record's problem and evaluation by the live path's rule and fails closed on a missing key; refile tests for every unclean shape ... | closed |
| T-03-55 (03-08) | Information disclosure | filing or promoting without the sanitizer's deny entries, so the login is not ch | high | mitigate | file_row and file_skipped return exit 15 on None before doing anything; promote raises unless a caller opts out and only its command line does; a source test... | closed |
| T-03-56 (03-08) | Repudiation | a filed fact that reads no for a reason that is not a defect of the skill, read  | medium | mitigate | the question looks at the first five lines for the helper's session line; the fake now returns the brand line first so the test can see the defect; the READM... | closed |
| T-03-57 (03-08) | Repudiation | a row cost that cannot be checked from the filed file (IN-01, D-14) | medium | mitigate | usage.txt carries the cumulative-consistent flag per stage and a warning line for a no; the figure is still quoted from the same file | closed |
| T-03-58 (03-08) | Repudiation | the guide, the checklist or the filed counters disagreeing with the exit rule af | medium | mitigate | the checklist's writes number is the sum breaches() uses and a test compares them; the mechanical file lists the two new counters; README phrases are pinned ... | closed |
| T-03-59 (03-08) | Information disclosure | the new usage, mechanical and refusal lines carrying a path, a command, the logi | medium | mitigate | counts, ids, yes and no and fixed text only; the existing vocabulary test is applied to the new lines; the leak gate and gitleaks run over the sources | closed |
| T-03-60 (03-09) | Tampering | --refile and the live filing accepting a run whose chain stopped early (a clean  | high | mitigate | _unfileable requires the chain the registry defines after the per-stage rule; refile tests for the stopped shapes assert exit 11, no folder, no stage folder,... | closed |
| T-03-64 (03-09) | Elevation of privilege | a command planted in the configuration of a nested repository, registered as a g | high | mitigate | nested_git_present is checked before any harness git call; capture_git_status raises before a process starts; git_state reads nothing and the not-read state ... | closed |
| T-03-65 (03-09) | Tampering | removing or replacing raw/setup.git.json (reachable by any write route) so the p | high | mitigate | pinned_gitdir takes the boundary as a required argument and raises CheckError for a missing or malformed pin after setup; no git process is started; the end-... | closed |
| T-03-66 (03-09) | Repudiation | a cumulative-consistent yes that compared a number with itself because the strea | medium | mitigate | has_call_block gates the comparison; the value is unknown when the call's cost came from the totals; a test on a result without the block asserts unknown in ... | closed |
| T-03-67 (03-09) | Information disclosure | the new fixed lines and facts of this plan (the stage-missing line, the nested n | medium | mitigate | fixed text, counts and state names only; tests assert that no printed line holds a folder of the rig; the vocabulary test covers the harness-authored files; ... | closed |
| T-03-61 (03-10) | Tampering | a write outside the approved roots by a program no closed list names (rm, ln, ta | high | mitigate | the open-world rule (read-only list and gates, everything else write-capable and judged by plain word, token, literal, redirection target and directory chang... | closed |
| T-03-62 (03-10) | Denial of service | a false breach after the paid call: a read-only use (awk or cat over an outside  | medium | mitigate | the read-only list with per-program gates; mentions decide nothing; the shell grammar is read as the shell reads it (comments, reserved words, heredocs, subs... | closed |
| T-03-63 (03-10) | Tampering | writes the rule cannot decide: a script or program file the model wrote earlier  | medium | accept | not decidable from the command text. The pinned allowlist and the binary's permission layer are the first net (the traces show refusals of expansion forms an... | closed |
| T-03-68 (03-10) | Denial of service | the corpus test failing when a later baseline folder is filed with traces | low | accept | the counts are floors and the expected number of escapes is zero; a later folder whose commands ran under the rule cannot contain an escape, and one that doe... | closed |
| T-03-69 (03-10) | Information disclosure | new labels echoing a path, a command text, a login or a verdict word (EVID-05):  | medium | mitigate | a label that is not a short plain word is written as other; counts, ids and fixed text only; tests assert that no printed line holds a folder of the rig; the... | closed |
| T-03-70 (03-11) | Denial of service | a false breach after the paid call: a legitimate write to the memory or checkpoi | high | mitigate | a relative word with a dot-dot segment is resolved with realpath against the tracked working folder and judged against the roots; tests table the inside and ... | closed |
| T-03-71 (03-11) | Tampering | the new dot-dot resolution accepting a path that leaves the roots: a wrong start | high | mitigate | each command starts in the first approved root; realpath resolves through links; a dot-dot is resolved only over literal segments, so a word with an expansio... | closed |
| T-03-72 (03-11) | Tampering | a path attached to a short option (-oOUT/x, -COUT, -tOUT, a cluster ending in th | high | mitigate | the text after the option letter and, for a cluster of one to four letters, the text from the first slash or tilde on are judged like any word; the run-level... | closed |
| T-03-73 (03-11) | Tampering | a sed w command after s flags, a bang or a custom-delimiter address, and the exp | high | mitigate | a script reader finds the operand wherever the w command can stand, with an over-counting fallback for anything it cannot read; eight review forms plus range... | closed |
| T-03-74 (03-11) | Tampering | an awk write whose string holds a semicolon, brace or newline before the redirec | high | mitigate | strings are blanked, each print statement is scanned to its end at depth zero, a redirect or pipe at depth zero is a write, and system, close and a piped get... | closed |
| T-03-75 (03-11) | Elevation of privilege | git -c with any key, --exec-path or --config-env run through env or directly: gi | high | mitigate | every -c before the verb, --exec-path and --config-env in any spelling are a git mutation of the fixed form whatever the key, value and verb, so the row ends... | closed |
| T-03-76 (03-11) | Elevation of privilege | a nested repository whose git folder is named .GIT or .Git: on a case-insensitiv | medium | mitigate | the names below the top level are compared without regard to case; a table of true and false names; an end-to-end plant with a control that proves the filter... | closed |
| T-03-77 (03-11) | Tampering | the pin read from raw/setup.git.json, a file the model can reach, before the gua | high | mitigate | the digest is held in memory from the setup write, the file is compared with it before any git call, and a mismatch, a missing or malformed file or a missing... | closed |
| T-03-78 (03-11) | Denial of service | a false breach from harmless script text or a two-file test group: awk with syst | medium | mitigate | the awk keyword test and the print statement reader work on blanked text and on calls; the sed reader treats patterns and replacements as data; the test grou... | closed |
| T-03-79 (03-11) | Information disclosure | the new fixed form and counts echoing a path, a command text or a login: the git | medium | mitigate | fixed words, counts and ids only; tests assert that no printed line holds a folder of the rig; the vocabulary test covers the harness-authored files; the lea... | closed |
| T-03-80 (03-11) | Tampering | writes the rule still cannot decide: the working folder kept between separate Ba | medium | accept | not decidable from the command text. The pinned allowlist and the binary's permission layer are the first net, the snapshot diff and the Write and Edit trace... | closed |
| T-03-81 (03-12) | Tampering | an awk program whose double quote sits inside a regular expression or a comment: | high | mitigate | the keyword and redirect tests also read the raw program text whenever a double quote stands after a still-visible slash or hash; a statement with parenthese... | closed |
| T-03-82 (03-12) | Tampering | the working folder moved by a cd that did not certainly run in the main shell or | high | mitigate | the folder moves only when the cd is joined to the next part by a double ampersand, is not after a double bar or a pipe, is not in a background list, is not ... | closed |
| T-03-83 (03-12) | Tampering | a dot-dot or absolute value after the value letter of a short-option cluster, an | high | mitigate | the text after each option letter of the leading run is judged, with the four-letter rule for a slash or tilde start so relative values stay inside; the sort... | closed |
| T-03-84 (03-12) | Denial of service | a false breach after the paid call: a cd to the output of git rev-parse --show-t | medium | mitigate | a cd to an expansion leaves the folder loose and a dot-dot word is then resolved against the project, as at the start of the command; tests table the zero an... | closed |
| T-03-85 (03-12) | Denial of service | false breaches from the new conservatism: the over-count of the raw awk view (a  | medium | accept | named in the guide and the truths; the corpus (231 judged commands) gives zero; the narrowing of the raw view to suspect programs keeps the 03-11 harmless fo... | closed |
| T-03-86 (03-12) | Tampering | a cd to a variable or substitution that stands for a folder outside the project, | medium | accept | not decidable from the command text; the pinned allowlist and the binary's permission layer are the first net, the snapshot diff and the realpath boundary th... | closed |
| T-03-87 (03-12) | Tampering | the allowlist model changed by the splitter refactor: a different part list woul | high | mitigate | split_compound becomes the parts of the new function and returns the same output for every input; test_allowlist.py and the whole suite run unchanged; a test... | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-08 (03-01) | it is printed only to the caller's own terminal and the README holds the token form, never the real path | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-02 | T-03-SC (03-01, 03-02, 03-03, 03-04, 03-05, 03-06, 03-07, 03-08, 03-09, 03-10, 03-11, 03-12) | this plan installs nothing; standard library only | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-03 | T-03-49 (03-07) | not decidable from the command text; the pinned allowlist and the binary's own permission layer are the first net (six expansion refusals in the baseline), the snapshot diff and the Write and Edit ... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-04 | T-03-63 (03-10) | not decidable from the command text. The pinned allowlist and the binary's permission layer are the first net (the traces show refusals of expansion forms and of output redirections to project file... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-05 | T-03-68 (03-10) | the counts are floors and the expected number of escapes is zero; a later folder whose commands ran under the rule cannot contain an escape, and one that does should fail the test and be reviewed | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-06 | T-03-80 (03-11) | not decidable from the command text. The pinned allowlist and the binary's permission layer are the first net, the snapshot diff and the Write and Edit trace the second. Each limit is named in the ... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-07 | T-03-85 (03-12) | named in the guide and the truths; the corpus (231 judged commands) gives zero; the narrowing of the raw view to suspect programs keeps the 03-11 harmless forms read-only; if the corpus catches a h... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |
| AR-03-08 | T-03-86 (03-12) | not decidable from the command text; the pinned allowlist and the binary's permission layer are the first net, the snapshot diff and the realpath boundary the second; named in the guide, the truths... | bokiko, at plan approval (disposition accept in the PLAN threat model) | 2026-11-12 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-12 | 88 | 87 | 1 | gsd-security-auditor (sonnet) via /gsd-secure-phase, retroactive |

### Auditor evidence and observations

T-03-35 (low) stays open below the blocking threshold: `pc_compare.py` converts an unbounded digit run with `int()` and `main` does not catch ValueError (review IN-05, deferred). The auditor also noted one unregistered, unverified surface: the harness passes `--setting-sources project,local` while the allowlist carries bare Write and Edit, so a model-written project settings file could be loaded by a later stage; no exploitability claim was made and no threat row is added here. The auditor's full verdict is reproduced below (evidence pointers are file:line at the audited commit).

## OPEN_THREATS (non-blocking only): no blocking threat is open, threats_open: 0

**Phase:** 3, walking skeleton (row 1). **ASVS level:** 1. **block_on:** high.
**Register:** 99 rows, 88 distinct ids (T-03-SC repeats once per plan, 12 times, one id). 80 mitigate, 8 accept ids.
**Closed:** 87 of 88 (80 mitigate ids: 79 closed, 1 open; 8 accept ids: 8 closed as accepted). **Open at or above high:** 0. **Open below high (non-blocking):** 1 (T-03-35, low).
**threats_open:** 0

Verdict logic: the gate field counts only open threats at severity high or above. All 37 high threats and all 45 medium threats are closed; the one open row is low and does not block. The structured status is OPEN_THREATS only because T-03-35 is open and below the threshold; if the orchestrator prefers a binary gate, this is SECURED with one tracked non-blocking item.

Paths are under `tests/harness` unless stated. No implementation file was touched, no SECURITY.md was written, and I ran no suite, selftest, matrix or claude binary. `git status` is unchanged (only `.planning/state.json` untracked, as at the start).

### Threat verification (one row per distinct id)

| Threat ID | Plan | Category | Severity | Disposition | Status | Evidence |
|---|---|---|---|---|---|---|
| T-03-01 | 03-01 | Tampering | medium | mitigate | closed | pc_rows.py:122,961-976 (ID_PATTERN ends `\Z`; find_entry exact match, never a prefix); pc_matrix.py:287-313,1121-1131 (unknown/unimplemented/repeated id, bad campaign, bad attempt refused with fixed text); test_matrix_cli.py:275-279 |
| T-03-02 | 03-01 | Denial of service (cost) | high | mitigate | closed | pc_matrix.py:1188-1192 (real run without --budget is exit 18 before any process), 500-512 (budget must cover worst case), 1165-1171 (dry run is free); pc_spend.py:40,302-307,339-340 (2.00 plus authorizations); pc_rows.py:987-996 |
| T-03-03 | 03-01 | Elevation of privilege | medium | mitigate | closed | pc_preflight.py:123-131 (absolute, isfile, X_OK), 102-114 (argument list, shell=False), 163,180-191 (build_env, exact-match version gate); pc_flags.py:38,527-543. Note: with no --claude the preflight searches PATH (README.md:235-238), still behind the exact-match gate |
| T-03-04 | 03-01 | Tampering | high | mitigate | closed | pc_spend.py:233-246 (flock around read, check, append), 213-229 (O_APPEND, 0600, fsync), 180-210 and 129-177 (strict read, any malformed line refused), 337-340 (one attempt per stage). Observed: matrix-spend.jsonl mode 0600, 236 lines, no stage launched twice |
| T-03-05 | 03-01 | Elevation of privilege | medium | mitigate | closed | pc_spend.py:337-338 (launch without an authorization line refused); observed ledger: 0 authorize lines in 236; the 'a line proves the flag ran, not who typed it' truth is recorded at 03-01-PLAN.md:38 and 03-01-SUMMARY.md:149 |
| T-03-06 | 03-01 | Information disclosure | medium | mitigate | closed | pc_matrix.py:88-109,173-176,515-556 (fixed texts, exception message never printed); test_matrix_cli.py:275-279 (probe value never in stderr) |
| T-03-07 | 03-01 | Denial of service | medium | mitigate | closed | pc_matrix.py:1165-1171 (dry run returns after claude-free gates; no stub check, preflight or ledger); pc_rowhooks.py:495-501 (write-free precondition); test_matrix_cli.py:354,363 (tripwire claude stays silent) |
| T-03-08 | 03-01 | Information disclosure | low | accept | closed (accepted) | accepted: login line prints the real config folder on the caller's terminal only; README.md:315,320-321 holds the `<config>` token form; pc_matrix.py:84,365-373, pc_preflight.py:96-100 |
| T-03-SC | all 12 plans | Tampering | low | accept | closed (accepted) | accepted: nothing installed. AST scan of every tests/harness/*.py finds no import outside the standard library or the harness itself; no package manifest among tracked files; no install command in any pc_*.py |
| T-03-09 | 03-02 | Tampering | high | mitigate | closed | pc_flags.py:25,365-366 (`--permission-mode default`; no skip-permissions flag is built anywhere in pc_*.py, only mentioned in docs); pc_spike.py:264-306 (runs root outside every home); pc_row1.py:773-776,833 (snapshot, git state and guard at every boundary); README.md:510-511 (containment detected, not enforced) |
| T-03-10 | 03-02 | Information disclosure | high | mitigate | closed | pc_flags.py:388-422 (config only via CLAUDE_CONFIG_DIR, refuses repo or user config); pc_preflight.py:208-216 (boolean loggedIn only); pc_row1.py:276 and pc_manifest.py:328-338 (snapshots walk the run root only); no pc_ module opens, lists or walks the config folder (grep); test_checks.py:396-421 |
| T-03-11 | 03-02 | Denial of service (cost) | high | mitigate | closed | pc_row1.py:725-735 (cap and turns on argv, ledger reservation before the process), 1529-1538 (chain stops at first non-clean stage); pc_rows.py:230-234 (turns 15/60/15, caps 0.30/1.30/0.40); pc_spend.py:281-294 (timeout/no cost keeps the cap). Observed: 118 launches, none repeated |
| T-03-12 | 03-02 | Spoofing | medium | mitigate | closed | pc_stream.py:65-99,106-111 (strict parse, exactly one result); pc_row1.py:879-898 (last fenced single `Resume ` line, 2000 bytes, no NUL), 725-729 (s3 built by the same allowlist, mode and caps as every stage) |
| T-03-13 | 03-02 | Tampering | medium | mitigate | closed | pc_runroot.py:59-78 (mkdir, no exist_ok), 86-100 (O_EXCL\|O_NOFOLLOW); pc_row1.py:1423; AST scan finds no delete, rename or truncate call in production modules (test_runroot.py:331-338 pins it) |
| T-03-14 | 03-02 | Repudiation | medium | mitigate | closed | pc_checks.py:2749 (raw is not an approved root), 276-311 (a Write/Edit path under raw/ is listed), 2583-2714 (guard over every raw file, hook-log prefix); pc_hooklog.py:46 (O_APPEND) |
| T-03-15 | 03-02 | Information disclosure | high | mitigate | closed | pc_row1.py:1426-1431 (sanitizer and deny entries built; SanitizerError/ScannerError returns exit 15) before the first launch line at 733; test_stages.py:391 (PreSpendTests) |
| T-03-16 | 03-02 | Denial of service | medium | mitigate | closed | pc_spike.py:1282 (timeout), 1286-1291 (raw bytes kept); pc_row1.py:764-771 (timeout settles with no delta), 1529-1538 (chain stop); pc_spend.py:288-293 (cap stays counted) |
| T-03-17 | 03-02 | Information disclosure | medium | mitigate | closed | pc_row1.py:1007-1026 (caller_map: runs root, its parent and the two-component users prefix to the scratch token); pc_matrix.py:633-637; test_stages.py:451 |
| T-03-18 | 03-03 | Tampering | high | mitigate | closed | pc_checks.py:122-124,210-237 (full-digest diff, component-aware), 276-311 (realpath Write/Edit scan), 1847-1859 (single lstat), 2846-2866; test_checks.py:555 (seeded fixtures plus clean control) |
| T-03-19 | 03-03 | Tampering | high | mitigate | closed | pc_checks.py:1894-1942 (HEAD, branch, refs, git folder digest minus index, staged), 2038-2099 (executed mutating forms); test_checks.py:465 |
| T-03-20 | 03-03 | Spoofing | medium | mitigate | closed | pc_checks.py:2735-2843 (facts only from snapshots, stream structure, wrapper log, state files); README.md:515-517 |
| T-03-21 | 03-03 | Information disclosure | medium | mitigate | closed | pc_checks.py:1847-1859 (one lstat); pc_row1.py:276; test_checks.py:396-421 (open, listdir, scandir, walk patched to raise under the config folder) |
| T-03-22 | 03-03 | Tampering | medium | mitigate | closed | checkpoint_stub.py:693 (marker-bearing body refused with exit 4) before the write at 701; data/branch-table.md:47 (STUB-ONLY row) |
| T-03-23 | 03-03 | Denial of service | medium | mitigate | closed | pc_checks.py:2846-2866 (breaches(): concrete writes, git mutations, record changes only); pc_row1.py:1177-1195; raw and snapshots are never deleted |
| T-03-24 | 03-04 | Information disclosure | high | mitigate | closed | pc_row1.py:1426-1431; pc_evidence.py:1236-1255 (every file sanitized, then staged), 1613-1619 (promote with deny entries and config folder); pc_sanitize.py:197-199,279-281 (login reaches the gate); test_evidence.py:274-316 (Wr14Tests with control). My scan of the Phase 3 baseline folder rerun-2026-10-29-claude-sonnet-5-5: 0 login, host, home-path, secret-shape, NUL or raw-capture-name hits; login, host and home-path greps over all 7 rerun-* folders also 0 |
| T-03-25 | 03-04 | Tampering | high | mitigate | closed | pc_promote.py:96-144 (existing destination refused, exit 17), pc_runroot.py:81-100 (exclusive); pc_matrix.py:400-469 (gate refuses taken row/STOPPED/SKIPPED names before spend); pc_evidence.py:1223-1233 |
| T-03-26 | 03-04 | Repudiation | medium | mitigate | closed | pc_evidence.py:51,1633-1645 (neutral text, one verdict line), 1729-1739 (vocabulary pattern); test_evidence.py:902-922; filed row README ends `Reviewer verdict: PENDING` |
| T-03-27 | 03-04 | Information disclosure | medium | mitigate | closed | pc_evidence.py:1473-1542 (explicit staging list, no raw capture), pc_leakgate.py:246 (NUL refused); test_evidence.py:200,263 |
| T-03-28 | 03-04 | Denial of service | medium | mitigate | closed | pc_matrix.py:400-469,1177-1180 (pre-spend refusals first), 761-832 (--refile repeats checks and filing, no claude, no ledger line); pc_evidence.py:1223-1233 (numbered stage folders) |
| T-03-29 | 03-04 | Spoofing | medium | mitigate | closed | pc_evidence.py:1633-1696 (SKIPPED- label, README says no session was run), pc_matrix.py:920-928 (a skip never aggregates to 0) |
| T-03-30 | 03-04 | Information disclosure | medium | mitigate | closed | pc_evidence.py:1236-1255 plus pc_row1.py:1007-1026 (tokens); my grep of the baseline folder and the six later rerun-* folders: 0 login hits |
| T-03-31 | 03-04 | Tampering | low | mitigate | closed | pc_row1.py:738 (prompt stored verbatim in raw before the process); pc_evidence.py:1268-1269 (missing copy refuses filing, exit 11) |
| T-03-32 | 03-05 | Tampering | high | mitigate | closed | pc_compare.py:168 (the only open is mode rb; no write primitive in the module), 128-130, 774-804 (digests before and after); test_compare.py:618-632 |
| T-03-33 | 03-05 | Repudiation | medium | mitigate | closed | pc_compare.py:70-72 (neutral headers, CONTENT_MARK); test_compare.py:799-811,969 |
| T-03-34 | 03-05 | Tampering | medium | mitigate | closed | test_frozen_tree.py:36-39 pins; I recomputed SKILL.md and the three tree digests and all four equal the pins; `git diff --name-only 56e155c` over the frozen paths is empty; SKILL.md is 11994 bytes (cap 12000) |
| T-03-35 | 03-05 | Denial of service | low | mitigate | OPEN (non-blocking) | PARTIAL. Present: tree_manifest never follows links and raises on walk errors (pc_manifest.py:328-373), main maps OSError/ManifestError/CompareError to exit 2 (pc_compare.py:760,795), tolerant parsers (pc_compare.py:158-172). Gap: pc_compare.py:236-237,288,294,621 call int() on an unbounded `\d+` group and main does not catch ValueError, so a >4300-digit run in a filed trace or measurements file raises past main (I confirmed int('9'*5000) raises ValueError on this Python 3.14.7). Same as review-1 IN-05, deferred. Input is the harness's own filed evidence; low severity |
| T-03-36 | 03-05 | Information disclosure | low | mitigate | closed | pc_compare.py:686-700,774-804 (base names and counts only, fixed MESSAGE_UNREADABLE); test_compare.py asserts no path in either stream |
| T-03-37 | 03-06 | Denial of service (cost) | high | mitigate | closed | 03-06-PLAN.md:176 (blocking-human checkpoint before spend); pc_spend.py:337-340; pc_rows.py:987-996 (worst case 2.00 = --budget 2.00). Observed ledger: row1 s1/s2/s3 launched once each, no authorize line, row total 0.2723 |
| T-03-38 | 03-06 | Spoofing | high | mitigate | closed | 03-06-PLAN.md:176 (`checkpoint:decision` gate=blocking-human), 03-06-SUMMARY.md:48 (paid command ran once 'after bokiko's own go'); observed ledger: 0 authorize lines. Procedural: the consent text itself cannot be re-verified from the repository |
| T-03-39 | 03-06 | Elevation of privilege | medium | mitigate | closed | pc_flags.py:416,527-543 (DISABLE_AUTOUPDATER, exact-match gate); pc_preflight.py:180-191; pc_matrix.py:1198-1200 (untested build stops before spend); pc_row1.py:805 (version in each stage record); row folder claude-version.txt |
| T-03-40 | 03-06 | Information disclosure | high | mitigate | closed | same chain as T-03-24; 03-06-SUMMARY.md:85 (gate 0 findings, gitleaks clean); my scan of the baseline folder rerun-2026-10-29-claude-sonnet-5-5: 0 login, host, home-path, secret-shape, NUL or forbidden-name hits (login, host and home-path also 0 in the six later rerun-* folders) |
| T-03-41 | 03-06 | Tampering | high | mitigate | closed | T-03-09 argv plus pc_row1.py:1177-1195,1518-1528 (breach is exit 11, label filed, raw stays); 03-06-SUMMARY.md:67-68 (0 outside writes, 0 git mutations) |
| T-03-42 | 03-06 | Repudiation | medium | mitigate | closed | tests/evidence/rerun-2026-10-29-claude-sonnet-5-5/README.md:3 ('a new baseline ... not a replication'); row README last line `Reviewer verdict: PENDING` |
| T-03-43 | 03-06 | Tampering | medium | mitigate | closed | .githooks/commit-msg, pre-commit, pre-push exist and core.hooksPath is .githooks; commit 6637669 message has no trailer. Scoped to plan 03-06: the folder has since reached origin/main under Phase 4's own authority |
| T-03-44 | 03-06 | Information disclosure | medium | mitigate | closed | no home-path, temp-path or config-folder string in any 03-*-SUMMARY.md, and no home or temp path in any 03-*-PLAN.md (grep) |
| T-03-45 | 03-07 | Elevation of privilege | high | mitigate | closed | pc_manifest.py:77-78,260 (core.fsmonitor and core.untrackedCache forced false on status), pc_checks.py:1870 (same on every state call); test_checks.py:884 (GitHardeningTests) |
| T-03-46 | 03-07 | Elevation of privilege | high | mitigate | closed | pc_checks.py:1894-1925 (changed git folder digest: no git process, not-read state counts as a mutation), pc_manifest.py:295-305, pc_row1.py:274-286; test_checks.py:1012 |
| T-03-47 | 03-07 | Tampering | high | mitigate | closed | pc_checks.py:1597-1656,1740-1828 (open-world write-escape rule counted into BREACH_WRITES at 2855); my probes: rm, tee, curl, cp, tar, sh -c, python3 -c, env -S/-i all counted; test_checks.py:1414,2223 |
| T-03-48 | 03-07 | Tampering | high | mitigate | closed | pc_checks.py:483-516 (tilde, $HOME, dot-dot, realpath), 1597-1656; my probes: `> ~/x`, `> $HOME/x`, `> ../../outside`, cd moves, python3 -c / awk / sed quoted paths all counted |
| T-03-49 | 03-07 | Tampering | medium | accept | closed (accepted) | accepted: run-time targets, other expansions, folder kept across Bash calls; first net is the allowlist and the binary's permission layer, then snapshot diff and Write/Edit realpath trace; named at README.md:646-657 |
| T-03-50 | 03-07 | Tampering | high | mitigate | closed | pc_checks.py:2475-2528 (boundary list strict), 2583-2630 (digest of every raw file, snapshot tree digests, hook-log prefix), 2679-2714; pc_row1.py:219-231 (only raw, snaps and .git left out of the snapshot); test_checks.py:2566,2726 |
| T-03-51 | 03-07 | Repudiation | medium | mitigate | closed | pc_checks.py:1847-1859 (memory_probe raises), 2800-2804 (missing state file or guard raises), pc_row1.py:1186-1189 (unreadable run root is exit 11) |
| T-03-52 | 03-07 | Denial of service | medium | mitigate | closed | pc_row1.py:1193-1194 (counts printed); my probes: cat/ls/grep over outside files, quoted heredoc body, find -delete inside the roots, sed w inside a pattern all 0; corpus test_checks.py:2460-2472 |
| T-03-53 | 03-07 | Information disclosure | medium | mitigate | closed | pc_checks.py:339,1066-1078 (label is a plain word or `other`); fixed count lines at pc_row1.py:1170-1195 |
| T-03-54 | 03-08 | Tampering | high | mitigate | closed | pc_evidence.py:1258-1277 (missing key is not clean, fail closed), 1591-1595; pc_matrix.py:825-829 |
| T-03-55 | 03-08 | Information disclosure | high | mitigate | closed | pc_evidence.py:1581-1582,1670-1671 (None deny entries is exit 15); pc_promote.py:157-158,309-310; every production promote call passes deny_entries (pc_evidence.py:1613,1690; pc_cleanclone.py:718; pc_baseline.py:620) |
| T-03-56 | 03-08 | Repudiation | medium | mitigate | closed | pc_checks.py:2313-2319,2376 (first five lines); pc_testutil.py:359 (fake returns the brand line first); README.md:695-701 (earlier baseline value explained) |
| T-03-57 | 03-08 | Repudiation | medium | mitigate | closed | pc_evidence.py:314-362 (flag per stage, warning line for a no) |
| T-03-58 | 03-08 | Repudiation | medium | mitigate | closed | pc_evidence.py:986-1000 uses the same sum as pc_checks.py:2854-2857; test_evidence.py:802 |
| T-03-59 | 03-08 | Information disclosure | medium | mitigate | closed | pc_evidence.py:314-362,986-1036 (counts, ids, yes/no only); vocabulary tests test_evidence.py:902-922 |
| T-03-60 | 03-09 | Tampering | high | mitigate | closed | pc_evidence.py:1280-1316 (_chain_incomplete: stage records must equal the registry chain); used by file_row at 1593 for the live path and refile |
| T-03-64 | 03-09 | Elevation of privilege | high | mitigate | closed | pc_manifest.py:112-131,295-296 (nested repo: no git started), pc_checks.py:1919-1921,1983-1984 (setup refuses a nested repo); test_checks.py:1111 |
| T-03-65 | 03-09 | Tampering | high | mitigate | closed | pc_checks.py:1945-1966 (pin required after setup; missing or malformed file is CheckError before any git process); test_checks.py:1012 |
| T-03-66 | 03-09 | Repudiation | medium | mitigate | closed | pc_spend.py:443-452 (has_call_block), pc_row1.py:627-639,814-816 (unknown without the block) |
| T-03-67 | 03-09 | Information disclosure | medium | mitigate | closed | fixed lines only: pc_row1.py:242-243,1035-1049,1167-1175; no path in printed lines (tests assert) |
| T-03-61 | 03-10 | Tampering | high | mitigate | closed | pc_checks.py:344-347,1045-1063 (read-only list with gates, everything else write-capable), 1081-1109 (mktemp), 802 (awk/sed program-file options); 12 probes of unlisted writers counted |
| T-03-62 | 03-10 | Denial of service | medium | mitigate | closed | pc_checks.py:1045-1063,1360-1467 (grammar pre-pass), 2460-2472 test floors; my probes: read-only uses stay 0 |
| T-03-63 | 03-10 | Tampering | medium | accept | closed (accepted) | accepted: script file written earlier and run later, path built at run time, variable expansion, stdin operand, sed e; named at README.md:646-657; Phase 4 follow-up for bokiko recorded in the 03-10-PLAN threat row |
| T-03-68 | 03-10 | Denial of service | low | accept | closed (accepted) | accepted: test_checks.py:2470-2472 holds floors (>=35 traces, >=348 parsed, >=231 judged) and expects zero escapes; a later folder that breaks it fails the test |
| T-03-69 | 03-10 | Information disclosure | medium | mitigate | closed | pc_checks.py:339,1066-1078 (_PLAIN_LABEL else `other`) |
| T-03-70 | 03-11 | Denial of service | high | mitigate | closed | pc_checks.py:483-516,1153-1177; my probes: `mkdir -p ../auto-memory`, `> ../auto-memory/n.md`, `mkdir ../ckpt/ledgers` = 0; corpus test_checks.py:2482-2493 |
| T-03-71 | 03-11 | Tampering | high | mitigate | closed | pc_checks.py:498-516 (realpath, literal segments only), 1153-1177 (cd rules); my probes: ../wrapper, ../raw, ../../outside, $PWD/.., $(pwd)/.., glob, brace, variable all counted |
| T-03-72 | 03-11 | Tampering | high | mitigate | closed | pc_checks.py:1578-1594,1650-1654; my probes: -o../../x, -t../../x, -C ../../x, git format-patch -o../../x, cc -o../../x counted |
| T-03-73 | 03-11 | Tampering | high | mitigate | closed | pc_checks.py:643-743 (script reader with over-counting fallback); my probes: s///w, !w, 1,3w, y;w, -e forms counted; `s/w/x/p` and `/w /p` stay 0 |
| T-03-74 | 03-11 | Tampering | high | mitigate | closed | pc_checks.py:877-1011 (blanked strings, depth-zero print redirect, system/close/piped getline); my probes: print "a;b" > f, pipe to tee, printf "a}b" > f counted; `$1 > 3` stays 0 |
| T-03-75 | 03-11 | Elevation of privilege | high | mitigate | closed | pc_checks.py:2003-2069 (any -c, --exec-path, --config-env before the verb is `config-command`); my probes: git -c, env git -c, --exec-path=, --config-env= all returned config-command |
| T-03-76 | 03-11 | Elevation of privilege | medium | mitigate | closed | pc_manifest.py:125 (`name.lower() == ".git"` below the top level); test_checks.py:2048 |
| T-03-77 | 03-11 | Tampering | high | mitigate | closed | pc_row1.py:776,1444 (pin held in memory from setup), pc_checks.py:1945-1966 (file compared with it before any git call); test_checks.py:2137 |
| T-03-78 | 03-11 | Denial of service | medium | mitigate | closed | pc_checks.py:900-1003 (keyword and print reader on blanked text), 1409-1428 (double-bracket test is one part, in the pre-pass); my probes: `[[ a && b ]]` and comparisons = 0 |
| T-03-79 | 03-11 | Information disclosure | medium | mitigate | closed | pc_checks.py:2003,1066-1078 (fixed form word, label `other`) |
| T-03-80 | 03-11 | Tampering | medium | accept | closed (accepted) | accepted: leading NAME=value, awk ENVIRON, redirect target in a variable, expansion after last dot-dot, earlier script files, run-time paths, folder kept across calls; named at README.md:646-657 |
| T-03-81 | 03-12 | Tampering | high | mitigate | closed | pc_checks.py:900-930 (_awk_suspect, _quote_pairs), 1645-1646; my probes: `/"/ {print > "/tmp/x"}` and a `# "` comment before a redirect counted |
| T-03-82 | 03-12 | Tampering | high | mitigate | closed | pc_checks.py:1667-1712 (certain cd only), 1659-1664, 1153-1177; my probes: 10 strict forms (;, \|\|, pipe, &, newline, subshell, if body, missing folder, ..) counted, certain `cd sub && > ../../auto-memory/n` = 0 |
| T-03-83 | 03-12 | Tampering | high | mitigate | closed | pc_checks.py:1578-1594 (text after each letter of the run, four-letter rule), 1014-1019 (sort gate); my probes: sort -uo../../x, tar -cvzpf../../x.tar counted. Known limit (REVIEW-5 WR-04, deferred): `tar -cvzpf/tmp/x.tar a` (five letters, then a slash) is not counted |
| T-03-84 | 03-12 | Denial of service | medium | mitigate | closed | pc_checks.py:1165-1166 (non-literal cd target leaves the folder loose); my probe: `cd $(git rev-parse --show-toplevel) && > ../auto-memory/n` = 0 |
| T-03-85 | 03-12 | Denial of service | medium | accept | closed (accepted) | accepted: false breaches from conservatism; named at README.md:583-596,618-622; corpus of 231 judged commands gives zero (test_checks.py:2472) |
| T-03-86 | 03-12 | Tampering | medium | accept | closed (accepted) | accepted: cd to a variable or substitution standing for an outside folder, then a dot-dot write resolving inside the roots; named at README.md:590-595 |
| T-03-87 | 03-12 | Tampering | high | mitigate | closed | pc_allowlist.py:97-157 (split_compound is the parts of split_compound_connected, one splitter); test_checks.py:1974-1975, test_allowlist.py:44-73 |

### Open (blocking, severity at or above high)

None.

### Open (non-blocking, below high)

| Threat ID | Severity | Mitigation expected | Files searched |
|---|---|---|---|
| T-03-35 | low | the comparer never raises past main on an odd tree; parsers tolerate malformed files | pc_compare.py:158-172,225-301,616-625,760,795; pc_manifest.py:328-373 |

Suggested fix (for a later phase, not a gate): bound the digit groups (for example `\d{1,12}`) or catch ValueError next to the OSError/ManifestError/CompareError catch in `pc_compare.main` and `_main_all_rows`, and map it to the same exit 2 line.

### Accepted risks log (for the orchestrator to record in SECURITY.md)

| # | Threat ID | Severity | Accepted residual | Compensating net and where it is stated |
|---|---|---|---|---|
| AR-1 | T-03-08 | low | The BLOCKED login instruction prints the real harness config folder path | printed only on the caller's own terminal; README.md:315,320-321 holds the `<config>` token form, never a path |
| AR-2 | T-03-SC (plans 03-01 to 03-12) | low | No supply-chain control beyond installing nothing | standard library only; verified by AST scan and absence of package manifests; test_imports.py enforces it |
| AR-3 | T-03-49 | medium | The Bash write-escape rule cannot decide run-time computed targets, other variable expansions, or a folder kept between Bash calls | pinned allowlist and the binary's permission layer first, snapshot diff inside the run root and the realpath boundary on Write/Edit traces second; README.md:646-657 |
| AR-4 | T-03-63 | medium | A script or program file written earlier and run later (sh, interpreter, env); interpreter code that builds its path at run time; a file operand read from stdin; sed `e` | same nets; each limit named in README.md:646-657; scanning Write/Edit inputs and heredoc bodies is a proposed Phase 4 follow-up for bokiko's decision |
| AR-5 | T-03-68 | low | The corpus test counts are floors | test_checks.py:2470-2472 expects zero escapes, so a later folder that breaks the rule fails the test and is reviewed |
| AR-6 | T-03-80 | medium | Leading NAME=value values, awk ENVIRON lookups, a redirect target held in a variable, an expansion after the last dot-dot segment | same nets; named at README.md:646-657 |
| AR-7 | T-03-85 | medium | False breaches from the conservative reading (raw awk view, a cd after a semicolon, in a background list or in a compound body read as unknown) | named at README.md:583-596,618-622; corpus of 231 judged commands gives zero false breaches |
| AR-8 | T-03-86 | medium | A cd to a variable or substitution that stands for an outside folder, followed by a dot-dot write that resolves inside the roots from the project | same nets; named at README.md:590-595; price of T-03-84 |

### Trust boundaries confirmed (48 declared; each maps to a verified mitigation above)

- argv and environment to the driver: T-03-01, T-03-02, T-03-06, T-03-07 (pc_rows.py ID_PATTERN and exact match, pc_matrix.py budget and dry-run paths).
- driver to the claude executable: T-03-03, T-03-39 (absolute executable file, no shell, scrubbed env, exact-match version gate, autoupdater off).
- driver to the harness home (ledger and login): T-03-04, T-03-05, T-03-10, T-03-11. The ledger and its lock are mode 0600 inside a 0700 home outside the repository (pc_spike.py:166-169 refuses a home inside the repository). No credential-like name is tracked.
- printed text to terminal and files: T-03-06, T-03-30, T-03-36, T-03-44, T-03-53, T-03-59, T-03-67, T-03-69, T-03-79 (fixed text, counts, ids).
- real claude -p and model tool calls versus the scratch project: T-03-09, T-03-18, T-03-19, T-03-41, T-03-45 to T-03-48, T-03-61, T-03-70 to T-03-75, T-03-81 to T-03-84. Containment is detected after the fact, not enforced; the README says so (README.md:510-511).
- spend ledger and the 2 USD row cap: T-03-02, T-03-04, T-03-05, T-03-11, T-03-37, T-03-38. Observed ledger: 118 launch and 118 settle lines, no stage launched twice, zero authorize lines, row 1 total 0.2723 USD.
- captured stream bytes to parsed facts: T-03-12, T-03-20 (strict parser, facts never read from reply text).
- model to the run root's own record and the git pin: T-03-14, T-03-50, T-03-51, T-03-64, T-03-65, T-03-76, T-03-77.
- stub ledger and model-written body: T-03-22.
- run root to tests/evidence: T-03-24, T-03-25, T-03-27, T-03-28, T-03-31, T-03-54, T-03-55, T-03-60 (sanitize, gate with the login deny entries, exclusive promote). Independent scan: the Phase 3 baseline folder holds no login, host, home path, secret shape, NUL byte or raw-capture file name; the six later rerun-* folders hold no login, host or home path.
- sanitizer to the gate: T-03-15, T-03-17, T-03-24, T-03-55.
- destination folder name: T-03-25, T-03-13. Harness-authored text to the reviewer: T-03-26, T-03-29, T-03-33, T-03-42, T-03-56, T-03-57, T-03-58, T-03-66.
- comparer to the two evidence trees and the frozen trees: T-03-32, T-03-34, T-03-35. Frozen digests recomputed and equal to the pins; the base-commit diff over the frozen paths is empty.
- harness checks to a paid run (false breach): T-03-23, T-03-52, T-03-62, T-03-70, T-03-78, T-03-84, T-03-85.

### Unregistered flags (SUMMARY.md Threat Flags)

All twelve summaries state none (03-01, 03-04 and 03-05 have no Threat Flags section). No unregistered_flag from the summaries. One observation of mine, outside the register, listed below as a warning and not counted.

### Observations (none changes the counts)

1. WARNING, outside the register, unverified. The harness passes `--setting-sources project,local` (pc_flags.py:26,360) and the baseline allowlist carries bare Write and Edit (pc_flags.py:53-55). A file the model writes under the project's own `.claude/` during one stage is inside an approved root, so it is not a breach, and a later stage loads project-level settings. I did not verify what Claude Code does with such a file, so I make no claim of exploitability. It is a decision for bokiko whether to add a threat row and a check (for example a snapshot fact listing any `project/.claude/settings*` file).
2. Known deferred limit confirmed by probe: REVIEW-5 WR-04. `tar -cvzpf/tmp/x.tar a` (a five-letter cluster with an attached slash value) is not counted as a write escape; the four-letter rule is the declared T-03-83 mitigation and README.md:598-603 states it. The allowlist reaches such a program only through `Bash(env:*)`. Deferred to Phase 4 hardening with WR-01 to WR-06 of the closing review; the same probes showed the other forms counted.
3. Known over-count confirmed: `echo 'note about /etc' > notes.txt` counts as an escape (REVIEW-4 deferred warning on echo/printf data words). It errs toward a false breach, never a missed write.
4. T-03-38 is procedural. The repository shows the blocking-human gate in the plan, the summary's statement that the paid run followed bokiko's own go, and a ledger with one launch per stage and no authorization line. The consent message itself is not in the repository.
5. T-03-43 says nothing was pushed. That was true of plan 03-06's execution. Commit 6637669 (the baseline folder) is now contained in origin/main (pushed after plan 03-06; I did not trace under which decision); the pre-push hook and its checks (leaks.sh, identity.sh, denylist.sh) exist.
6. The pre-existing committed `tests/evidence/publication-2026-10-20` folder (frozen, digest-pinned, produced before the harness existed) holds the owner's login handle in `ls -l` style output in some traces. It is not a Phase 3 product and the pin blocks editing it; the harness-produced rerun-* folders are clean.
7. Gate-adjacent items I did not treat as register gaps: timeout kills only the direct child (review-1 deferred info), a torn final ledger line makes the ledger refuse every launch (fails closed by design), and `tests/harness/mechanical-checks.md` does not exist (the mechanical-checks text is generated into each filed row folder).
8. Read-only checks I ran myself: AST scan of imports and of delete/rename/truncate calls; grep of the filed folders and phase documents for login, host, home-path and secret shapes; recomputation of the four frozen digests; `git diff --name-only 56e155c` over the frozen paths (with --no-optional-locks); a read of `the harness home spend ledger (matrix-spend.jsonl)` (not the config folder); and about 100 probes of the pure functions `pc_checks.bash_mentions` and `pc_checks._mutating_git_verb` from the scratchpad with `python3 -B -I`, which touch no repository file and start no claude. The probe scripts are in the scratchpad folder as p03_probe*.py.

**threats_open:** 0

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-12
