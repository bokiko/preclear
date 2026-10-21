---
last_mapped_commit: a68da30760d453667f526919b2c09fe86c32940c
last_mapped_at: 2026-10-21
---
# Codebase Concerns

**Analysis Date:** 2026-10-21

Scope note: preclear is a Markdown-only Claude Code skill (`SKILL.md`, `references/`, `tests/`). There is no executable code, so concerns are about instruction correctness, evidence integrity, and test coverage. The gitignored `runs/` folder is not part of the project and is not covered.

## Tech Debt

**Unsupported Do-not-redo entry in the row 7 checkpoint (open content defect):**
- Issue: the printed checkpoint claims "Workspace policy/registry checked", but no tool call in that turn reads a registry. The fact appears carried over from the work turn's context.
- Files: `tests/evidence/publication-2026-10-20/row7-all-destinations-denied/README.md`, `CHANGELOG.md` (Status entry), `README.md` (Roadmap item "Clean rerun of publication row 7")
- Impact: the row passes for destination handling but fails evidence integrity. It blocks the "public release" roadmap item.
- Fix approach: run a fresh targeted checkpoint turn for row 7, confirm every Do-not-redo entry is backed by a call in that turn, and update the README verdict. Consider a `SKILL.md` rule that Do-not-redo entries must cite a check made in the current session.

**Recurring cap-reporting defect (D1):**
- Issue: the model's own section-cap statements disagreed with the independent byte manifest in 5 of 12 checkpoint-producing runs (character counts, heading lines skipped, or no per-section measurement).
- Files: `SKILL.md` (Step 4, around line 166), `tests/evidence/publication-2026-10-20/README.md`
- Impact: the skill depends on the model's self-measurement. The Step 4 change (measure by command, print actual/cap) held in 14 artifacts, but a model that cannot run the measurement command can only report "Size not measured" (seen in row 7).
- Fix approach: keep the independent manifest check in the acceptance harness for every new digest.

**Skill size ceiling is a hard constraint:**
- Issue: `SKILL.md` is about 12 KB. The `CHANGELOG.md` entry for Step 4 says the installed-tokenizer preference was dropped "to stay within the size ceiling". Any new rule must displace existing text.
- Files: `SKILL.md`, `CHANGELOG.md`
- Impact: fixes for the issues here compete for the same space. The ceiling is 12,000 bytes; it is stated only in `.github/pull_request_template.md`, not in `SKILL.md` or `tests/acceptance.md`.
- Fix approach: state the ceiling number in `tests/acceptance.md`. Move detail into `references/` where possible.

**Changelog is all `[Unreleased]`:**
- Issue: `CHANGELOG.md` has no versioned release, and the Added and Changed sections mix evidence runs with skill changes.
- Files: `CHANGELOG.md`
- Impact: it is hard to tell which skill digest each accepted result applies to.
- Fix approach: cut a tagged version at publication and record the digest per version.

## Known Bugs

**Row 5a-12 evidence relies on a declared fallback for earlier runs:**
- Symptoms: the harness allowlist never matched the skill's exact status command until the row 10 and 11 reruns, so earlier runs (including the three accepted layouts) used a plain-porcelain fallback.
- Files: `tests/evidence/publication-2026-10-20/README.md`, `references/status-sidecar.md`
- Trigger: any run before the row 10/11 reruns.
- Workaround: the acceptances stand for the behaviour demonstrated but are not exact-command tests.

**Row 12 section overrun:**
- Symptoms: Resume reading measured 712 bytes against a 600 cap in two identical initial artifacts. It was disclosed, and the refreshed checkpoint is within every cap.
- Files: `tests/evidence/publication-2026-10-20/row12-frozen-handoff/`
- Workaround: the overrun is recorded as a measured exception.

## Security Considerations

**Public-content and history audit not yet accepted:**
- Risk: evidence files carry sanitized tokens (`<run>`, `<home>`, `<repo>`). A private audit record exists (2026-10-20) and found no secrets, but its acceptance and the visibility change are owner decisions not yet taken; nothing in the repo records acceptance.
- Files: `tests/evidence/` (all subfolders), `CHANGELOG.md`, `README.md`
- Current mitigation: the repo is private. `.gitignore` excludes `.env*`, `*.log` (except under `tests/evidence/`), and `runs/`.
- Recommendations: finish the audit and re-scan `tests/evidence/**` for home paths, hostnames and identifiers before any visibility change. The `.gitignore` exception `!tests/evidence/**/*.log` means raw logs there are tracked, so it is the main leak surface.

**Resume and backend boundaries rely on prompt compliance:**
- Risk: "no file output, binding, or backend write without authorization" and "read-only resume" are instructions, not enforced controls. Compliance is shown only by the evidence runs.
- Files: `SKILL.md`, `references/checkpoint-v1.md`
- Current mitigation: acceptance rows verify zero writes on fresh resume and stop-on-first-denied-helper-write.
- Recommendations: rerun the matrix after any `SKILL.md` or adapter change, since rows 1, 2, 3c and 4b only carry forward on old digests.

## Performance Bottlenecks

**Context cost of the resume package:**
- Problem: several rows disclose required reads above the 1,392-byte allocation, and freshness output is unmeasured.
- Files: `SKILL.md`, `tests/evidence/publication-2026-10-20/README.md`
- Cause: the package totals in replies are estimates unless a row README says otherwise.
- Improvement path: measure freshness output in the harness and report package totals as measured values.

## Fragile Areas

**Quoted-porcelain status fallback:**
- Files: `references/status-sidecar.md`
- Why fragile: the preferred `-z` NUL form has never executed under the headless tool policy, because output redirection needs approval. The fallback depends on never re-splitting quoted names on whitespace.
- Safe modification: keep `--untracked-files=all` and `--ignore-submodules=none`. Test with hostile filenames (row 10).
- Test coverage: the NUL form is untested.

**Cross-file digests and rules:**
- Files: `SKILL.md`, `references/checkpoint-v1.md`, `references/configuration.md`
- Why fragile: acceptance results are tied to a skill sha256 and adapter sha256 (for example `6d22a71e7f3c…` and `eca134a3defc…`). Any edit invalidates carried-forward rows.
- Safe modification: re-run affected rows and record new digests.

**Skill name shadowing:**
- Files: `README.md` (install note)
- Why fragile: a personal skill of the same name shadows a project one, so a user can run a different copy than the tested one. Digest checks in the skill are the only guard.

## Scaling Limits

**Discovery lookup cap:**
- Current capacity: governing-instruction lookups are capped at 20 candidate paths and 12,000 bytes (`SKILL.md`, line 34).
- Limit: larger instruction sets may be partly missed. Documents already identified as active are exempt.
- Scaling path: not defined.

## Dependencies at Risk

**Claude Code behaviour:**
- Risk: all evidence ran on one Claude Code version (2.1.304) with specific permission and tool-policy behaviour (for example refusals of compound shell commands). Other versions or policies are unverified.
- Files: `tests/evidence/publication-2026-10-20/README.md`, `tests/acceptance.md`

**External `checkpoint` helper:**
- Risk: the bound-ledger backend depends on a helper outside this repo. Its contract is described only in `references/checkpoint-v1.md`.
- Impact: helper changes can break the adapter silently. A test-only wrapper was needed for the conflict case.

## Missing Critical Features

**Public release:**
- Problem: the roadmap item is open. It needs the row 7 rerun and the audit.
- Files: `README.md` (Roadmap), `CHANGELOG.md`

**Automated acceptance run:**
- Problem: acceptance is a manual, Codex-reviewed procedure in `tests/acceptance.md`. The harness scripts are local (gitignored `runs/`), so a contributor cannot reproduce the runs from the repository alone.
- Blocks: independent verification of the claims in `tests/evidence/`.

## Test Coverage Gaps

**NUL-separated sidecar:**
- What's not tested: the preferred `-z` status form.
- Files: `references/status-sidecar.md`, `SKILL.md` Step 3
- Priority: Medium

**Row 7 clean content pass:**
- What's not tested: a checkpoint with only supported Do-not-redo entries under all-destinations-denied.
- Files: `tests/evidence/publication-2026-10-20/row7-all-destinations-denied/`
- Priority: High

**Carried-forward rows on old digests:**
- What's not tested: rows 1, 2, 3c and 4b on the current skill digest.
- Files: `tests/evidence/publication-2026-10-20/row1-wrong-binding/`, `row2-double-conflict/`, `row3c-unbound-fallback-none/`, `row4b-conflicting-blocks/`
- Priority: Medium

**Complete resume packages:**
- What's not tested: measured package totals including freshness output.
- Files: `tests/evidence/publication-2026-10-20/README.md`
- Priority: Low

---

*Concerns audit: 2026-10-21*
