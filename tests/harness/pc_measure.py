"""Heading-inclusive byte measurer (inert skeleton: behaviour arrives with the GREEN step)."""
from __future__ import annotations

import sys

SECTIONS = ()
FILE_CAP = 0


def measure_bytes(data):
    return {"total": 0, "sha256": "", "rows": [], "missing": []}


def measure_file(path):
    with open(path, "rb") as handle:
        handle.read()
    return measure_bytes(b"")


def format_report(label, measurement):
    return ""


def main(argv):
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
