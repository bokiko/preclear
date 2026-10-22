# Git hooks

Local checks that stop a leak or a wrong identity before it leaves this machine. They
are a safety net, not enforcement. See Limits.

## Enable

Hooks are off in a fresh clone. Turn them on once per clone:

```sh
git config core.hooksPath .githooks
```

Install `gitleaks` first (`brew install gitleaks` on macOS). Without it the hooks
refuse to run, on purpose.

## Owner setup

The push-time identity and attribution checks run only in a clone that sets the pin.
Skip this section unless you are the owner. Replace each slot with your own value:

```sh
git config user.useConfigOnly true
git config user.name "<name>"
git config user.email "<address>"
git config preclear.pinnedIdentity "<name> <<address>>"
```

`user.useConfigOnly` stops git from inventing an identity from the machine name. The
pin value is the name, one space, then the address in literal angle brackets, the same
text git prints for `%an <%ae>`. The leak check and the deny-list check run in every
clone, pinned or not.

## What runs

- `pre-commit`: `gitleaks` over the staged diff with `.gitleaks.toml`, then the
  deny-list check.
- `commit-msg`: refuses a message that carries an AI attribution trailer. The patterns
  live in `attribution.ere`.
- `pre-push`: over each pushed range, the leak check, the deny-list check and, in a
  pinned clone, the identity and attribution checks.

## Test

```sh
sh scripts/test-hooks.sh
```

The script works in throwaway clones under the temp directory. It never pushes to the
real remote and never stores a fake secret as a literal. It prints one `PASS` or `FAIL`
line per case and exits 1 on any `FAIL`.

## Scanner

`gitleaks` 8.30.x. The rules and the accepted-findings list were tested on 8.30.0. A
different minor release needs the strict and gate scans repeated before you trust it.

## Local deny list

The deny-list check builds its entries when it runs, from this machine's host names. To
add more, such as a real name, put one entry per line in `.git/info/preclear-deny.txt`.
Lines that start with `#` and entries shorter than four characters are ignored. The
file sits inside `.git`, so it is never committed. The check prints counts and file
names only, never an entry and never a matched line.

## Limits

- The hooks are a safety net, not enforcement. `git commit --no-verify` and
  `git push --no-verify` skip them, and a clone that never ran the enable command has
  none.
- The identity and push-time attribution checks exist only in the owner's pinned clone.
  Nothing on the server repeats them.
- Once the repository is public, GitHub push protection is the server-side net. It
  covers secrets only, not identity, paths or host names.
