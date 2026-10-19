# Row 4b: two applicable blocks that disagree, one says `none` (1P)

Setup: `CLAUDE.md` block (task widget-export, fallback `.preclear`) and `CLAUDE.local.md` block (task
widget-export-v2, fallback `none`), both naming the same project (`fixture-CLAUDE.md`,
`fixture-CLAUDE.local.md`). Session bound.

Result: **PASS.** Zero helper calls. The model named both disagreements, resolved state 3, applied the
"any applicable block says none" rule: persistence BLOCKED, no checkpoint file, no resume line, no
escape to the generic Step 3 destinations, full checkpoint printed in the reply, remedy stated (make
the blocks agree or remove one). Plan step ticked and decision written to the fixture's memory root.

Codex verdict: **PASS.** Helper operations: attempted 0, executed 0. No checkpoint file and no resume
line; authorized plan and memory updates did occur. Ledger, registry and binding hashes unchanged.
