#!/bin/sh
# Leak check: run gitleaks over each pushed range listed in the file named by $1
# (one "ref<TAB>range" line per ref). Fails closed: a missing scanner is an error, and
# --exit-code 2 keeps a finding (2) apart from a tool error (1). Findings are always
# redacted; never pass a value that turns redaction off.
ranges=$1
command -v gitleaks >/dev/null 2>&1 || { echo "leak check FAILED: gitleaks not found (brew install gitleaks)" >&2; exit 1; }
tab=$(printf '\t'); rc=0
while IFS=$tab read -r ref rev; do
  gitleaks git . --config .gitleaks.toml --no-banner --redact -v --exit-code 2 --log-opts="$rev" -l warn \
    || { echo "leak check FAILED for $ref" >&2; rc=1; }
done < "$ranges"
exit $rc
