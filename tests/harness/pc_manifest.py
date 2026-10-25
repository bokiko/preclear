"""Tree manifests (inert skeleton: behaviour arrives with the GREEN step)."""
from __future__ import annotations

import sys


class ManifestError(Exception):
    pass


def tree_manifest(root):
    return []


def escape_name(name_bytes):
    return ("", False)


def sha_txt_bytes(entries):
    return b""


def jsonl_bytes(entries):
    return b""


def write_snapshot(dest_dir, entries):
    return None


def main(argv):
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
