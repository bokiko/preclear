"""Exclusive run-root allocation (inert skeleton: behaviour arrives with the GREEN step)."""
from __future__ import annotations

import sys


class RunRootError(Exception):
    pass


class RunRootCollision(RunRootError):
    pass


def allocate_run_root(parent, name):
    return ""


def exclusive_dir(path, mode):
    return None


def write_exclusive(path, data, mode):
    return None


def main(argv):
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
