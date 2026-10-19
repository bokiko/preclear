# Status sidecar formats

Preferred: the NUL-separated form named in SKILL.md Step 3, written beside the
checkpoint as `status.txt`:

```
git --no-optional-locks status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none
```

Permitted fallback when NUL capture is unavailable (for example, output
redirection needs an approval the session cannot obtain): the same command
without `-z`, which prints git's quoted porcelain v1 format. Rules for the
fallback:

- Keep git's escaping exactly as printed; never re-split a line on whitespace.
  Quoted names, rename records (`R  old -> new`) and submodule entries are
  copied verbatim.
- Keep full coverage: `--untracked-files=all` and `--ignore-submodules=none`
  stay in the command.
- Start the sidecar with comment lines naming the exact command, the capture
  time, HEAD, the reason the NUL form was not used, and the preclear artifacts
  excluded from the counts.
- Verify the sidecar against a recapture before finishing Step 4; a difference
  is handled like any other verify mismatch.
- Record the format as an exception in Evidence and in the reply. A sidecar
  written in either format never replaces the inline counts.

Both formats are documented in git's `git status` reference. Whether an
approval prompt appears once or repeatedly depends on the user's permission
configuration; never assume it has been granted.
