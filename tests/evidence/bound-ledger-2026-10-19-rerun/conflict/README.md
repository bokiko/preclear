# Conflict recovery case (bound-ledger), 2026-10-19

Codex's design: the fixture's configured `executable` is a test-only wrapper
(`wrapper-checkpoint.sh`) that delegates every call unchanged to the real helper. While an
`armed` flag exists, the wrapper intercepts the model's first `update`, lets a second
harness-bound fixture session perform a real `update` to the same section (adding one benign
fact: "CI runner renamed to ci-02"), disarms itself, then passes the model's original command
through untouched. The real helper therefore returns a genuine exit 3 with its real conflict
file. `injection.log` records the second writer's update. Isolation: same `CKPT_HOME` as the
other bound-ledger runs, two fixture sessions bound by the harness.

## Result: PASS

- The model's first `update` on "Goal & current state" returned exit 3 (trace shows the
  result text and the conflict file path).
- It read the conflict file, ran `show` again, merged its content with the second writer's
  fact (the final ledger contains the ci-02 line), and retried once with the new hash.
- No force, no direct ledger edit, bounded retry, `lint OK`, conflict file left in place and
  reported to the user.
- Backend inputs went to `.preclear/backend-inputs/` per the patched adapter.
- Honest exceptions in the reply: package about 6,375 bytes; Evidence body 1,096 bytes over
  the plain-file guideline while the helper's 4,096-byte block cap governs.

Not covered here: the second variant where another edit lands before the retry, which should
end in UNSTABLE and fallback after one bounded retry.
