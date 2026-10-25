"""Skeleton for the fail-closed leak gate (EVID-03). Replaced by the implementation commit."""
from __future__ import annotations


class ScannerError(Exception):
    """The scanner itself failed; the result is a refusal, never a pass."""


def scan_tree(root, deny_entries):
    raise NotImplementedError


def scan_entries(entries, deny_entries):
    raise NotImplementedError


def collect_tree(root):
    raise NotImplementedError


def scan_bytes(label, data, deny_entries):
    raise NotImplementedError


def format_findings(report):
    raise NotImplementedError


def build_deny_entries(repo_root, hostnames, deny_file):
    raise NotImplementedError


def main(argv):
    raise NotImplementedError


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
