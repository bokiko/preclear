# Publication matrix, 2026-10-20

Twelve ordered cases Codex specified after the three layouts were accepted. Each row runs on an
isolated fixture copy under the repo's gitignored `runs/` folder: own `CKPT_HOME` (helper
registry and bindings), own ledger and handoff roots, auto-memory pinned with `--settings`
`autoMemoryDirectory` to `<run>/auto-memory`, `--setting-sources project,local`, the skill
copied into the fixture's `.claude/skills/preclear/`. The configured helper executable is a logging
wrapper (`wrapper-checkpoint.sh` in each row) that records every executed helper call with argv and
exit code and delegates unchanged to the real helper. Each row: one work turn (plan step 2, CSV
exporter) in a new session, then `/preclear` with the JSON-default correction (`s2-preclear-prompt.md`)
in the same session. Claude Code 2.1.304.

Per row: `fixture-CLAUDE.md` (configuration), `tools.txt` (allowed tools), `digests.txt` (skill,
adapter, helper, wrapper), `s2-preclear-trace.md` (short trace and raw final reply),
`s2-preclear-full-trace.md` (complete sanitized commands, full results for denials, non-zero exits and
conflicts, raw transcript digest), `wrapper-calls.log` (executed helper calls), `snap-*/` (ledger
copies, tree hashes, git status, bindings, `.preclear`, memory per stage), `measurements.md`
(independent heading-inclusive UTF-8 byte counts on the original files, ledger and memory
inventory). Attempted-but-denied helper calls appear only in the traces, never in `wrapper-calls.log`. Permission
refusals of compound shell commands ("contains multiple operations") are harness tool-policy events,
not helper denials; the model then ran the parts separately. They are counted in each full trace.

Sanitized tokens: `<run>` the run root, `<helper>` the helper path, `<auto-memory-root>`,
`<repo>`, `<home>`.

## Rows 1–4 (first pass, skill sha256 bbda28403d95…, adapter 272838d4722d…)

| Row | Case | Codex verdict |
| --- | --- | --- |
| 1 | wrong active binding | PASS for binding isolation and fallback |
| 2 | second conflict before retry | PASS |
| 3a | missing executable | PASS backend selection; FAIL cap verification and disclosure |
| 3b | denied helper write | FAIL stop-on-denial; preservation and fallback PASS; false cap claim |
| 3c | unbound, `fallback_directory: none`, correct identity | PASS |
| 4a | unknown backend, relative executable | PASS invalid-config isolation; FAIL cap disclosure |
| 4b | two applicable blocks disagree, one says `none` | PASS |

Overall verdict on the first pass: **FIX FIRST**. Three changes followed (see the changelog): SKILL.md
Step 4 now requires per-section byte measurement by command with actual/cap printed; the adapter stops
all helper mutations after the first denial; the adapter states that backend failure changes
persistence, not ownership. Rows 3a and 3b were rerun on the new digests (`row3a-*-rerun`,
`row3b-*-rerun`); rows 1, 2, 3c and 4b carry forward on the old digests because no edit changed the
behaviour they test. Rows 5–12 run on the new digests.

Harness notes: the driver for row 3c died twice during setup (a `set -e` exit on a skipped bind, a
non-zero `status` exit for an unbound session, a missing bindings folder); each time the root was
discarded and a fresh root run to completion. No model turn was affected. After the first pass the
harness was changed to refuse an existing run root and to retain complete sanitized commands and
decisive results.

Recurring defect D1 across all evidence so far: the model's own cap statements disagreed with the
independent manifest in 5 of 12 checkpoint-producing runs (character counts, heading lines skipped,
or no per-section measurement). Historical artifacts are kept as produced.

## Rows 5–12 (new digests: skill 6d22a71e7f3c…, adapter eca134a3defc…)

Codex verdict on this group: FIX FIRST on evidence reporting, functional coverage complete; the corrections it required are applied in the READMEs and traces (full per-call results keyed by tool-use id, refusal counts recomputed, manifest limits stated, package totals marked as estimates where freshness output was unmeasured).

| Row | Case | Result (Codex verdict in each README) |
| --- | --- | --- |
| 5a | no memory system | PASS: no memory writes, no invented hierarchy, correction kept in the plan |
| 5b | memory explicitly disabled | PASS: no memory writes, plan carries the correction |
| 6 | read-only plan | PASS: plan untouched, pending update recorded |
| 7 | all destinations denied | PASS for destination handling; FAIL for evidence integrity (unsupported Do-not-redo entry) |
| 8a | non-git (inside an unrelated parent repo) | PASS + resume: `no-git @ n/a` |
| 8b | detached HEAD | PASS + resume |
| 8c | unborn branch | PASS + resume |
| 9 | linked worktree | PASS + resume: main checkout untouched |
| 10 | large status, hostile names | first pass: prescribed command refused by the harness; rerun PASS with format and measurement exceptions (NUL form never executed) |
| 11 | concurrent change during capture | first pass not exercised (wrapper fired on Claude Code's own git call); rerun PASS |
| 12 | frozen handoff, external edit, resume, refresh | PASS: frozen copy hash identical through four stages |

Section caps: every checkpoint produced in rows 5–12 and in the 3a/3b reruns measured within cap except
one overrun event in row 12, reproduced in its two identical initial artifacts (Resume reading 712/600)
and disclosed; the refreshed mutable checkpoint is within every cap. No false section-cap claim after the
Step 4 change (14 artifacts). This says nothing about complete resume packages: several rows disclose
required reads above the 1,392-byte allocation and unmeasured freshness output, and package totals in
replies are estimates unless a row README says otherwise.

Harness defects found during this group, both fixed for later runs: the allowlist never matched the
skill's exact status command until the row 10/11 reruns (earlier runs, including the three accepted
layouts, used a declared plain-porcelain fallback; Codex: those acceptances stand for the behaviour
actually demonstrated and are not exact-command tests); snapshot manifests split newline-containing
paths. The `-z` NUL sidecar form has not executed under this headless tool policy, because output
redirection needs approval.

Public-content and history audit: see `../../..`'s private audit record before any visibility change.

