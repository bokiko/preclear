"""Heading-inclusive UTF-8 byte measurer for plain-file checkpoints (EVID-01).

Reads ORIGINAL files as bytes (no newline translation, so CRLF counts as two bytes) and
reports per-section and total sizes as actual/cap. It reports facts and never a verdict:
an over-cap row shows its actual/cap pair with an over-by figure, and the exit status is
0 for any readable file. It never writes, and it measures originals only, never
sanitised copies.

The section names and caps are the plain-file checkpoint schema of SKILL.md, copied as
constants; test_measure reads the Schema table from SKILL.md and compares.

A section runs from a line that starts with "## " to the byte before the next such line,
heading line included and nothing stripped. Text before the first heading is the
(preamble) row; a heading outside SECTIONS is an (other) row with no cap; duplicate
headings are separate rows. A "## " line inside a fenced code block also starts a new
piece, because the split is by lines only.

CLI: python3 -E -s -B pc_measure.py FILE...
  prints one report per readable file; exits 0, or 2 for no arguments or an unreadable file.
"""
from __future__ import annotations

import hashlib
import re
import sys

SECTIONS = (
    ("Identity and state", 800),
    ("Boundaries and blockers", 600),
    ("Next action", 500),
    ("Resume reading", 600),
    ("Evidence and working changes", 1000),
    ("Do not redo", 596),
)
FILE_CAP = 4096

PREAMBLE = "(preamble)"
OTHER = "(other)"

_CAPS = dict(SECTIONS)
_SPLIT = re.compile(rb"(?m)^(?=## )")


def measure_bytes(data):
    """Measure DATA. Returns a dict: total, sha256, rows [(name, size, cap or None)], missing."""
    rows = []
    for piece in _SPLIT.split(data):
        if piece == b"":
            continue
        if piece.startswith(b"## "):
            first_line = piece.split(b"\n", 1)[0]
            name = first_line[3:].rstrip(b"\r").decode("utf-8", "replace")
            if name in _CAPS:
                rows.append((name, len(piece), _CAPS[name]))
            else:
                rows.append((OTHER, len(piece), None))
        else:
            rows.append((PREAMBLE, len(piece), None))
    seen = set(name for name, _size, _cap in rows)
    missing = [name for name, _cap in SECTIONS if name not in seen]
    return {
        "total": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": rows,
        "missing": missing,
    }


def measure_file(path):
    """Read PATH once into memory and measure that one buffer.

    Per-section sizes therefore always sum to the reported total, even if the file
    changes while this call runs.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    return measure_bytes(data)


def _over(actual, cap):
    return " over by %d" % (actual - cap) if actual > cap else ""


def format_report(label, measurement):
    """Return the report text. A label of None or "" omits the heading line."""
    lines = []
    if label:
        lines.append("## %s" % label)
    total = measurement["total"]
    lines.append(
        "total %d/%d bytes, sha256 %s%s"
        % (total, FILE_CAP, measurement["sha256"], _over(total, FILE_CAP))
    )
    for name, size, cap in measurement["rows"]:
        if cap is None:
            lines.append("- %s: %d" % (name, size))
        else:
            lines.append("- %s: %d/%d%s" % (name, size, cap, _over(size, cap)))
    if measurement["missing"]:
        lines.append("missing: %s" % ", ".join(measurement["missing"]))
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) == 0:
        print("usage: pc_measure.py FILE...", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="surrogateescape")
    status = 0
    for path in argv:
        try:
            measurement = measure_file(path)
        except OSError:
            print("cannot read a file named on the command line", file=sys.stderr)
            status = 2
            continue
        print(format_report(path, measurement), end="")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
