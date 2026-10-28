"""The matrix driver: the one command that lists, plans and (later) runs acceptance rows (HARN-01).

Run it as python3 -E -s -B pc_matrix.py, never with -I, because the pc_ modules import each other.

    --list                  every layout and row, layouts first, then rows in acceptance order,
                            one fixed-column line each: kind, id, stages, sessions, implemented
    --row ID                one row, by its exact id
    --layout NAME           one layout, by its exact name
    --all                   every implemented row, in registry order
    --dry-run               print the plan (stages, sessions, turns, caps, worst case, allowlist
                            size, model, destination) and start nothing: no process, no file

Exactly one of --list, --row, --layout and --all is given. An id is matched whole and exactly
against the registry before it is used for anything; an unknown or unimplemented id exits 2 with
fixed text that never repeats the value.

A dry run starts no process of any kind, creates no folder and writes no ledger line; it needs no
claude. Messages are fixed text: counts, row ids and stage ids only, never an argument, a path,
a host name or the login.
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from decimal import ROUND_UP, Decimal
from typing import Any, Callable, List, Mapping, Optional, Sequence, TextIO, Tuple

import pc_exitcodes
import pc_flags
import pc_rows

PROG = "pc_matrix.py"
USAGE_LINE = "usage: pc_matrix.py (--list | --row ID | --layout NAME | --all) [--dry-run]"
ALLOWLIST_ROLE_WRAPPER = "/role/wrapper/checkpoint"

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

MESSAGE_USAGE = "invalid command line"
MESSAGE_UNKNOWN_ROW = "unknown row id"
MESSAGE_UNKNOWN_LAYOUT = "unknown layout name"
MESSAGE_NOT_IMPLEMENTED = "that entry is not implemented in this phase"
MESSAGE_NEEDS_BUDGET = "a real run needs --budget at least the worst case printed above"


class _Parser(argparse.ArgumentParser):
    """An argument parser whose errors print one fixed line and exit 2, never echoing a value."""

    def __init__(self, out: TextIO, err: TextIO) -> None:
        super().__init__(prog=PROG, add_help=True, allow_abbrev=False)
        self._out = out
        self._err = err

    def error(self, message: str) -> Any:  # type: ignore[override]
        _write(self._err, USAGE_LINE + "\n")
        _write(self._err, "%s: error: %s\n" % (PROG, MESSAGE_USAGE))
        raise SystemExit(pc_exitcodes.USAGE)

    def print_help(self, file: Optional[TextIO] = None) -> None:
        _write(self._out, USAGE_LINE + "\n")

    def print_usage(self, file: Optional[TextIO] = None) -> None:
        _write(self._err, USAGE_LINE + "\n")


def _write(stream: TextIO, text: str) -> None:
    stream.write(text)
    stream.flush()


def build_parser(out: TextIO, err: TextIO) -> argparse.ArgumentParser:
    parser = _Parser(out, err)
    parser.add_argument("--list", action="store_true", dest="list_all")
    parser.add_argument("--row", default=None)
    parser.add_argument("--layout", default=None)
    parser.add_argument("--all", action="store_true", dest="all_rows")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    return parser


def _money_up(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_UP), "f")


def list_lines(registry: Sequence[pc_rows.RowSpec]) -> List[str]:
    """Return the header and one fixed-column line per entry, layouts first (registry order)."""
    template = "%-6s %-28s %6s %8s %s"
    lines = [template % ("kind", "id", "stages", "sessions", "implemented")]
    for entry in registry:
        if entry.implemented:
            stages = str(len(entry.stages))
            sessions = str(pc_rows.session_count(entry))
        else:
            stages = "-"
            sessions = "-"
        lines.append(template % (entry.kind, entry.row_id, stages, sessions, "yes" if entry.implemented else "no"))
    return lines


def _allowlist_size() -> int:
    tools = pc_flags.build_allowed_tools(ALLOWLIST_ROLE_WRAPPER, pc_flags.MODEL_FACING_WRAPPER_VERBS)
    return len(tools)


def _stage_words(row: pc_rows.RowSpec, stage: pc_rows.StageSpec) -> str:
    if stage.session.startswith("resume:"):
        key = "new:" + stage.session.split(":", 1)[1]
        origin = [other.name for other in row.stages if other.session == key]
        session = "resumes the %s session" % origin[0] if origin else "resumes an earlier session"
    else:
        session = "new session"
    return "%s, %s, %d turns, cap %s" % (stage.work, session, stage.max_turns, format(stage.cap, "f"))


def plan_lines(row: pc_rows.RowSpec, evidence_date: str, model: str = pc_flags.PINNED_MODEL) -> List[str]:
    """Return the dry-run text for one implemented row. It reads nothing and starts nothing."""
    lines = ["%s: %d stages, %d sessions" % (row.row_id, len(row.stages), pc_rows.session_count(row))]
    for stage in row.stages:
        lines.append("  %s: %s" % (stage.name, _stage_words(row, stage)))
    lines.append("worst case %s USD" % _money_up(pc_rows.worst_case(row)))
    lines.append("allowlist %d rules" % _allowlist_size())
    lines.append("model %s" % model)
    lines.append("destination tests/evidence/%s" % pc_rows.evidence_folder_name(evidence_date, model))
    return lines


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _usage(parser_err: TextIO) -> int:
    _write(parser_err, USAGE_LINE + "\n")
    _write(parser_err, "%s: error: %s\n" % (PROG, MESSAGE_USAGE))
    return pc_exitcodes.USAGE


def _refuse(err: TextIO, message: str) -> int:
    _write(err, "%s: %s\n" % (PROG, message))
    return pc_exitcodes.USAGE


def _select_entries(
    args: argparse.Namespace, registry: Sequence[pc_rows.RowSpec], err: TextIO
) -> Tuple[Optional[List[pc_rows.RowSpec]], int]:
    """Resolve the selection to registry entries; the second item is an exit code when it is refused."""
    if args.all_rows:
        return [entry for entry in registry if entry.implemented], pc_exitcodes.OK
    if args.row is not None:
        kind, unknown = pc_rows.KIND_ROW, MESSAGE_UNKNOWN_ROW
        text = args.row
    else:
        kind, unknown = pc_rows.KIND_LAYOUT, MESSAGE_UNKNOWN_LAYOUT
        text = args.layout
    entry = pc_rows.find_entry(registry, kind, text) if pc_rows.is_valid_id(text) else None
    if entry is None:
        return None, _refuse(err, unknown)
    if not entry.implemented:
        return None, _refuse(err, MESSAGE_NOT_IMPLEMENTED)
    return [entry], pc_exitcodes.OK


def _print_plans(
    args: argparse.Namespace,
    registry: Sequence[pc_rows.RowSpec],
    chosen: Sequence[pc_rows.RowSpec],
    evidence_date: str,
    out: TextIO,
) -> None:
    if args.all_rows:
        for entry in registry:
            if entry.implemented:
                for line in plan_lines(entry, evidence_date):
                    _write(out, line + "\n")
            else:
                _write(out, "%s: not implemented\n" % entry.row_id)
    else:
        for entry in chosen:
            for line in plan_lines(entry, evidence_date):
                _write(out, line + "\n")
    stages = sum(len(entry.stages) for entry in chosen)
    sessions = sum(pc_rows.session_count(entry) for entry in chosen)
    total = Decimal("0")
    for entry in chosen:
        total += pc_rows.worst_case(entry)
    if args.all_rows:
        _write(
            out,
            "total: %d row(s), %d stage(s), %d session(s), worst case %s USD\n"
            % (len(chosen), stages, sessions, _money_up(total)),
        )


def main(
    argv: Optional[Sequence[str]] = None,
    env: Optional[Mapping[str, str]] = None,
    repo_root: Optional[str] = None,
    registry: Optional[Sequence[pc_rows.RowSpec]] = None,
    clock: Optional[Callable[[], datetime.datetime]] = None,
    out: Optional[TextIO] = None,
    err: Optional[TextIO] = None,
) -> int:
    """Run the driver and return the exit code; this function never calls sys.exit."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = build_parser(out, err)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return pc_exitcodes.OK if exit_request.code in (0, None) else pc_exitcodes.USAGE

    selections = [
        args.list_all,
        args.row is not None,
        args.layout is not None,
        args.all_rows,
    ]
    if sum(1 for chosen in selections if chosen) != 1:
        return _usage(err)
    if args.dry_run and args.list_all:
        return _usage(err)

    entries = pc_rows.build_registry() if registry is None else tuple(registry)
    if args.list_all:
        for line in list_lines(entries):
            _write(out, line + "\n")
        return pc_exitcodes.OK

    chosen, refused = _select_entries(args, entries, err)
    if chosen is None:
        return refused
    now = (clock or _utc_now)()
    evidence_date = now.strftime("%Y-%m-%d")
    _print_plans(args, entries, chosen, evidence_date, out)
    if args.dry_run:
        return pc_exitcodes.OK
    _write(err, "%s: %s\n" % (PROG, MESSAGE_NEEDS_BUDGET))
    return pc_exitcodes.BUDGET_REFUSED


if __name__ == "__main__":
    sys.exit(main())
