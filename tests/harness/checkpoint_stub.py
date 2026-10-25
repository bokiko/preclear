#!/usr/bin/env python3
"""STUB-BACKED test apparatus: a single-file stand-in for the checkpoint-v1 helper.

This is not the real checkpoint helper. It is built only from
references/checkpoint-v1.md and the committed evidence under
tests/evidence/publication-2026-10-20, so the acceptance harness can drive the
skill with zero model tokens and no private tooling. Anything it prints or does
is a stub result, never a real-helper result.

Run as ``<python> -I -B checkpoint_stub.py <verb> [options]``. Every invocation
prints exactly one stub-marker line on standard error and nothing of the brand on
standard output (the ``--version`` banner is the one exception). Standard output
is byte-identical to the committed decisive outputs.

State lives under CKPT_HOME, which must name an existing directory (exit 64
otherwise; only --version and --help work without it):

    bindings/<session-uuid>.json   keys session_id, project, workstream, ledger,
                                   created, retired, predecessor
    ledger-roots.json              {"roots": [sorted absolute folders]}
    ledgers/                       the usual ledger root (any folder under
                                   CKPT_HOME that bind registers also works)
    <ledger folder>/.checkpoint-log.jsonl   one JSON object per mutating call

Containment is path-component aware: realpath on both sides, compared with the
separator appended. Bind refuses a ledger outside CKPT_HOME; show and update
refuse a ledger outside a registered root.

Session identity: --session (before or after the verb), else the
CLAUDE_CODE_SESSION_ID variable, else exit 2. The short id is the first eight
characters.

Verbs implemented here: status, show, validate, update, lint (model-facing) and
bind (driver only, needed to build state). note, handoff, create and init exit 1
("not implemented in this build step"); the stub completion in a later plan fills
them, the two labelled exit 5 and 6 switches and the lock with them.

Exit codes: 0 ok, 1 internal error, 2 usage or validation (including no
checkpoint block), 3 conflict, 4 invalid checkpoint, 5 kill switch (later plan),
6 lock timeout (later plan), 64 CKPT_HOME missing or not a directory.

UNCONFIRMED behaviours. Where references/checkpoint-v1.md and the committed
evidence are silent the stub takes the most literal reading and marks it here so
the branch table can mirror this list. None of these was observed against the
real helper:

  * note: stdout and exit code (the stub prints one line and exits 0; appends
    under the History heading a ``### <iso-ms>Z (<id8>)`` heading and the body,
    which is the one committed effect). Later plan.
  * handoff: the snapshot file name and stdout (the stub writes one immutable
    snapshot beside the ledger and prints its path). Later plan.
  * kill switch scope: write verbs only (update, note, handoff, bind, create,
    init); reads and validate are unaffected. Later plan.
  * status with no checkpoint block prints ``checkpoint: NONE`` as line 2.
  * status carried-from suffix: `` (carried from <id8>, unverified)`` when the
    binding names a predecessor.
  * lint warnings: one ``warning: <ledger path>: <reason>`` line per problem,
    exit 0.
  * validate rejection codes: exit 4 and ``checkpoint: invalid checkpoint:
    <reason>`` for block content (missing, extra, duplicate or misordered
    sections, empty or over-long Authorization boundaries, block over 4,096
    bytes, undecodable bytes); exit 2 for usage, a missing or unreadable file,
    and a ledger with no block.
  * validate byte count: the length of the re-rendered block (begin marker with a
    millisecond time and the caller id8, six sections separated by one blank
    line, end marker, no trailing newline).
  * bind, create and init argument shapes: bind takes --session, --ledger,
    --project, --workstream and --predecessor; create and init take --ledger,
    --project, --workstream and --task.
  * ledger-roots.json and .checkpoint-log.jsonl content (the shapes above).
  * a repeated --section flag: the first value wins.
  * a non-Authorization section with an empty body is allowed (its hash is the
    digest of the empty string).
  * update with the current hash and an unchanged body succeeds; the same
    stale-hash update repeated conflicts again.
  * the conflict message goes to standard error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time

BRAND = "checkpoint-stub: STUB-BACKED test apparatus, not the real checkpoint helper"
BANNER = "checkpoint-stub 1 (stub-backed checkpoint-v1; test apparatus, not the real helper)"

SECTIONS = (
    "Goal & current state",
    "Decisions (with reasons)",
    "Blockers & open questions",
    "Authorization boundaries",
    "Evidence & key paths",
    "Next action",
)
AUTH = "Authorization boundaries"
AUTH_LIMIT = 600
BLOCK_LIMIT = 4096

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_CONFLICT = 3
EXIT_INVALID = 4
EXIT_NO_HOME = 64

BEGIN_RE = re.compile(r"^<!-- CHECKPOINT:BEGIN updated: (\S+) by: (\S+) -->$")
END_LINE = "<!-- CHECKPOINT:END -->"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{7,63}$")
LEDGER_GLOB_RE = re.compile(r"^CONTINUITY_CLAUDE-[^/]+\.md$")
ARROW = "→"

NOT_IMPLEMENTED = ("note", "handoff", "create", "init")


class Exit(Exception):
    """Control flow: leave with a code and an optional stderr message."""

    def __init__(self, code: int, message: str = "") -> None:
        Exception.__init__(self, message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------- pure helpers


def utc_iso_ms(ns: int) -> str:
    """UTC time as YYYY-MM-DDTHH:MM:SS.mmmZ; truncates, never rounds."""
    seconds = ns // 1000000000
    millis = (ns % 1000000000) // 1000000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds)) + ".%03dZ" % millis


def conflict_stamp(ns: int) -> str:
    """The time part of a conflict file name: colons become hyphens."""
    stamp = utc_iso_ms(ns)
    return stamp[:13] + "-" + stamp[14:16] + "-" + stamp[17:]


def section_hash(body: str) -> str:
    """SHA-256 hex of the body as UTF-8 with trailing newlines stripped."""
    return hashlib.sha256(body.rstrip("\n").encode("utf-8")).hexdigest()


def is_within(path: str, base: str) -> bool:
    """True when path lies strictly inside base (realpath both, separator appended)."""
    real_path = os.path.realpath(path)
    real_base = os.path.realpath(base)
    prefix = real_base.rstrip(os.sep) + os.sep
    return real_path.startswith(prefix) and real_path != real_base


def parse_block_lines(lines: list):
    """Split the lines between the markers into [(name, body)]; None if text precedes a heading."""
    sections = []
    current = None
    for line in lines:
        if line.startswith("## "):
            current = [line[3:], []]
            sections.append(current)
        elif current is None:
            if line.strip():
                return None
        else:
            current[1].append(line)
    return [(name, "\n".join(body).rstrip("\n")) for name, body in sections]


def render_block(updated: str, by: str, sections: list) -> str:
    """The serialized block: begin marker, sections separated by one blank line, end marker."""
    parts = []
    for name, body in sections:
        parts.append("## " + name + ("\n" + body if body else ""))
    return (
        "<!-- CHECKPOINT:BEGIN updated: %s by: %s -->\n" % (updated, by)
        + "\n\n".join(parts)
        + "\n"
        + END_LINE
    )


def parse_ledger(text: str):
    """Return (pre, updated, by, sections, post) or None when there is no block."""
    lines = text.split("\n")
    begin = None
    end = None
    for index, line in enumerate(lines):
        if begin is None and BEGIN_RE.match(line):
            begin = index
        elif begin is not None and line == END_LINE:
            end = index
            break
    if begin is None or end is None:
        return None
    sections = parse_block_lines(lines[begin + 1:end])
    if sections is None:
        return None
    match = BEGIN_RE.match(lines[begin])
    pre = "".join(line + "\n" for line in lines[:begin])
    post = "\n".join(lines[end + 1:])
    if len(lines) > end + 1:
        post = "\n" + post
    return pre, match.group(1), match.group(2), sections, post


def check_sections(sections: list) -> str:
    """Return a rejection reason, or an empty string when the six sections are valid."""
    names = [name for name, _ in sections]
    for name in SECTIONS:
        if names.count(name) > 1:
            return "duplicate section: " + name
    for name in names:
        if name not in SECTIONS:
            return "extra section: " + name
    for name in SECTIONS:
        if name not in names:
            return "missing section: " + name
    if tuple(names) != SECTIONS:
        return "sections are out of order"
    return ""


def check_block(updated: str, by: str, sections: list) -> str:
    """Full checkpoint validation; returns a reason or an empty string."""
    reason = check_sections(sections)
    if reason:
        return reason
    auth = dict(sections)[AUTH]
    if not auth.strip():
        return AUTH + " is empty"
    if len(auth) > AUTH_LIMIT:
        return "%s is %d chars (limit %d)" % (AUTH, len(auth), AUTH_LIMIT)
    size = len(render_block(updated, by, sections).encode("utf-8"))
    if size > BLOCK_LIMIT:
        return "block is %d bytes (limit %d)" % (size, BLOCK_LIMIT)
    return ""


# -------------------------------------------------------------- state and files


class Context(object):
    def __init__(self, home: str, session: str, verb: str) -> None:
        self.home = home
        self.session = session
        self.id8 = session[:8] if session else ""
        self.verb = verb

    def path(self, *parts: str) -> str:
        return os.path.join(self.home, *parts)


def read_text_strict(path: str) -> str:
    with open(path, "rb") as handle:
        data = handle.read()
    return data.decode("utf-8")


def atomic_write(path: str, data: bytes, mode: int = 0o644) -> None:
    folder = os.path.dirname(path)
    fd, temp = tempfile.mkstemp(dir=folder, prefix=".ckpt-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def load_roots(ctx: Context) -> list:
    path = ctx.path("ledger-roots.json")
    if not os.path.exists(path):
        return []
    try:
        data = json.loads(read_text_strict(path))
        roots = data["roots"]
        if not isinstance(roots, list) or not all(isinstance(r, str) for r in roots):
            raise ValueError("roots")
    except (OSError, ValueError, KeyError, TypeError):
        raise Exit(EXIT_INTERNAL, "checkpoint: ledger-roots.json is unreadable")
    return roots


def register_root(ctx: Context, folder: str) -> None:
    roots = load_roots(ctx)
    real = os.path.realpath(folder)
    if real not in roots:
        roots.append(real)
    data = json.dumps({"roots": sorted(roots)}, indent=2) + "\n"
    atomic_write(ctx.path("ledger-roots.json"), data.encode("utf-8"))


def in_registered_root(ctx: Context, ledger: str) -> bool:
    for root in load_roots(ctx):
        if is_within(root, ctx.home) and is_within(ledger, root):
            return True
    return False


def binding_path(ctx: Context) -> str:
    return ctx.path("bindings", ctx.session + ".json")


def load_binding(ctx: Context):
    path = binding_path(ctx)
    if not os.path.exists(path):
        return None
    try:
        data = json.loads(read_text_strict(path))
    except (OSError, ValueError):
        raise Exit(EXIT_INTERNAL, "checkpoint: binding file is unreadable")
    if not isinstance(data, dict) or not isinstance(data.get("ledger"), str):
        raise Exit(EXIT_INTERNAL, "checkpoint: binding file has no ledger")
    return data


def resolve_ledger(ctx: Context, explicit):
    """Ledger path from --ledger or the session binding, checked against the roots."""
    binding = None
    if explicit:
        ledger = os.path.realpath(explicit)
    else:
        binding = load_binding(ctx)
        if binding is None or binding.get("retired"):
            raise Exit(EXIT_USAGE, "checkpoint: session %s is unbound; pass --ledger" % ctx.id8)
        ledger = os.path.realpath(binding["ledger"])
    if not in_registered_root(ctx, ledger):
        raise Exit(EXIT_USAGE, "checkpoint: ledger is outside the registered roots")
    if not os.path.isfile(ledger):
        raise Exit(EXIT_USAGE, "checkpoint: ledger not found")
    return ledger, binding


def load_ledger(ledger: str):
    try:
        text = read_text_strict(ledger)
    except UnicodeDecodeError:
        raise Exit(EXIT_USAGE, "checkpoint: ledger is not valid UTF-8: " + ledger)
    except OSError:
        raise Exit(EXIT_USAGE, "checkpoint: ledger is unreadable: " + ledger)
    return text, parse_ledger(text)


def audit(ledger: str, ctx: Context, verb: str, section=None) -> None:
    record = {
        "by": ctx.id8,
        "ledger": os.path.basename(ledger),
        "ts": utc_iso_ms(time.time_ns()),
        "verb": verb,
    }
    if section is not None:
        record["section"] = section
    line = json.dumps(record, sort_keys=True) + "\n"
    path = os.path.join(os.path.dirname(ledger), ".checkpoint-log.jsonl")
    with open(path, "ab") as handle:
        handle.write(line.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


def guard_write(ctx: Context) -> None:
    """Every write verb calls this first. Plain pass-through until the stub completion."""
    return None


# ------------------------------------------------------------------------ verbs


def out(text: str) -> None:
    sys.stdout.write(text)


def verb_status(ctx: Context, args) -> int:
    binding = load_binding(ctx)
    if binding is None or binding.get("retired"):
        out("session %s: unbound\n" % ctx.id8)
        return EXIT_OK
    ledger, _ = resolve_ledger(ctx, None)
    _, parsed = load_ledger(ledger)
    line1 = "session %s %s %s" % (ctx.id8, ARROW, ledger)
    if binding.get("predecessor"):
        line1 += " (carried from %s, unverified)" % str(binding["predecessor"])[:8]
    out(line1 + "\n")
    if parsed is None:
        out("checkpoint: NONE\n")
        return EXIT_OK
    _, updated, by, sections, _ = parsed
    out("checkpoint updated %s by %s\n" % (updated, by))
    nxt = dict(sections).get("Next action", "")
    out("Next action: %s\n" % nxt.split("\n", 1)[0])
    return EXIT_OK


def verb_show(ctx: Context, args) -> int:
    wanted = None
    if args.section:
        wanted = args.section[0]
        if wanted not in SECTIONS:
            raise Exit(EXIT_USAGE, 'checkpoint: unknown section "%s"' % wanted)
    ledger, _ = resolve_ledger(ctx, args.ledger)
    text, parsed = load_ledger(ledger)
    if parsed is None:
        raise Exit(EXIT_USAGE, "checkpoint: no checkpoint block in " + ledger)
    _, updated, by, sections, _ = parsed
    fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out("ledger: %s\n" % ledger)
    out("file-fingerprint: %s\n" % fingerprint)
    out("checkpoint-updated: %s by %s\n" % (updated, by))
    out("\n")
    for name, body in sections:
        if wanted is not None and name != wanted:
            continue
        out("## %s\n" % name)
        out("section-hash: %s\n" % section_hash(body))
        if body:
            out(body + "\n")
        out("\n")
    return EXIT_OK


def read_input_file(path: str) -> str:
    try:
        return read_text_strict(path)
    except UnicodeDecodeError:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: input is not valid UTF-8")
    except OSError:
        raise Exit(EXIT_USAGE, "checkpoint: cannot read " + path)


def verb_validate(ctx: Context, args) -> int:
    text = read_input_file(args.source)
    lines = text.rstrip("\n").split("\n")
    if not BEGIN_RE.match(lines[0]):
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: missing begin marker")
    if lines[-1] != END_LINE or len(lines) < 2:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: missing end marker")
    sections = parse_block_lines(lines[1:-1])
    if sections is None:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: text before the first section")
    updated = utc_iso_ms(time.time_ns())
    reason = check_block(updated, ctx.id8, sections)
    if reason:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: " + reason)
    size = len(render_block(updated, ctx.id8, sections).encode("utf-8"))
    out("valid checkpoint: %d bytes, Authorization %d chars\n" % (size, len(dict(sections)[AUTH])))
    return EXIT_OK


def write_conflict(ledger: str, ctx: Context, name: str, base_hash: str, current: str, yours: str, kept: str) -> str:
    content = (
        '# Conflict on section "%s"\n' % name
        + "ledger: %s\n" % ledger
        + "your base hash: %s\n" % base_hash
        + "current hash: %s\n" % current
        + "\n## Yours (not applied)\n%s\n" % yours
        + "\n## Current (kept)\n%s\n" % kept
    )
    ns = time.time_ns()
    while True:
        target = "%s.conflict-%s-%s.md" % (ledger, conflict_stamp(ns), ctx.id8)
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            ns += 1000000
            continue
        with os.fdopen(fd, "wb") as handle:
            handle.write(content.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        return target


def verb_update(ctx: Context, args) -> int:
    guard_write(ctx)
    name = args.section
    if name not in SECTIONS:
        raise Exit(EXIT_USAGE, 'checkpoint: unknown section "%s"' % name)
    if not HASH_RE.match(args.expect_section):
        raise Exit(EXIT_USAGE, "checkpoint: --expect-section must be 64 lowercase hex characters")
    ledger, _ = resolve_ledger(ctx, args.ledger)
    _, parsed = load_ledger(ledger)
    if parsed is None:
        raise Exit(EXIT_USAGE, "checkpoint: no checkpoint block in " + ledger)
    pre, _, _, sections, post = parsed
    new_body_raw = read_input_file(args.source)
    reason = check_sections(sections)
    if reason:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: ledger block: " + reason)
    current_body = dict(sections)[name]
    current_hash = section_hash(current_body)
    if current_hash != args.expect_section:
        target = write_conflict(
            ledger, ctx, name, args.expect_section, current_hash, new_body_raw.rstrip("\n"), current_body
        )
        raise Exit(
            EXIT_CONFLICT,
            'checkpoint: conflict: "%s" changed since your read. Nothing written. Details: %s' % (name, target),
        )
    new_body = new_body_raw.rstrip("\n")
    if any(line.startswith("## ") for line in new_body.split("\n")):
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: body contains a section heading line")
    updated_sections = [(n, new_body if n == name else b) for n, b in sections]
    updated = utc_iso_ms(time.time_ns())
    reason = check_block(updated, ctx.id8, updated_sections)
    if reason:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: " + reason)
    block = render_block(updated, ctx.id8, updated_sections)
    mode = os.stat(ledger).st_mode & 0o777
    atomic_write(ledger, (pre + block + post).encode("utf-8"), mode)
    audit(ledger, ctx, "update", name)
    out('updated "%s" in %s\n' % (name, ledger))
    return EXIT_OK


def verb_lint(ctx: Context, args) -> int:
    warnings = []
    for root in sorted(load_roots(ctx), key=os.fsencode):
        if not is_within(root, ctx.home) or not os.path.isdir(root):
            continue
        for fname in sorted(os.listdir(root), key=os.fsencode):
            path = os.path.join(root, fname)
            if not LEDGER_GLOB_RE.match(fname) or ".conflict-" in fname or not os.path.isfile(path):
                continue
            try:
                text = read_text_strict(path)
            except (OSError, UnicodeDecodeError):
                warnings.append("warning: %s: ledger is unreadable or not UTF-8" % path)
                continue
            parsed = parse_ledger(text)
            if parsed is None:
                warnings.append("warning: %s: no checkpoint block" % path)
                continue
            _, updated, by, sections, _ = parsed
            reason = check_block(updated, by, sections)
            if reason:
                warnings.append("warning: %s: %s" % (path, reason))
            elif not text.startswith("# CONTINUITY"):
                warnings.append("warning: %s: first line is not a CONTINUITY title" % path)
    if not warnings:
        out("ledger lint OK\n")
    else:
        out("\n".join(warnings) + "\n")
    return EXIT_OK


def verb_bind(ctx: Context, args) -> int:
    guard_write(ctx)
    ledger = os.path.realpath(args.ledger)
    folder = os.path.dirname(ledger)
    if not is_within(ledger, ctx.home) or not is_within(folder, ctx.home):
        raise Exit(EXIT_USAGE, "checkpoint: ledger is outside CKPT_HOME")
    os.makedirs(ctx.path("bindings"), exist_ok=True)
    record = {
        "session_id": ctx.session,
        "project": args.project,
        "workstream": args.workstream,
        "ledger": ledger,
        "created": utc_iso_ms(time.time_ns()),
        "retired": None,
        "predecessor": args.predecessor,
    }
    atomic_write(binding_path(ctx), (json.dumps(record, indent=2) + "\n").encode("utf-8"), 0o644)
    register_root(ctx, folder)
    audit(ledger, ctx, "bind")
    out("bound %s %s %s\n" % (ctx.id8, ARROW, ledger))
    return EXIT_OK


VERBS = {
    "status": verb_status,
    "show": verb_show,
    "validate": verb_validate,
    "update": verb_update,
    "lint": verb_lint,
    "bind": verb_bind,
}


# ------------------------------------------------------------------------- CLI


class StubParser(argparse.ArgumentParser):
    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        sys.stderr.write("checkpoint: usage error: %s\n" % message)
        raise Exit(EXIT_USAGE)


def _session_option(parser: argparse.ArgumentParser, suppress: bool) -> None:
    kwargs = {"default": argparse.SUPPRESS} if suppress else {"default": None}
    parser.add_argument("--session", help="session id (else CLAUDE_CODE_SESSION_ID)", **kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = StubParser(
        prog="checkpoint",
        description="checkpoint-v1 interface for the acceptance harness",
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=BANNER)
    _session_option(parser, False)
    sub = parser.add_subparsers(dest="verb", metavar="verb", parser_class=StubParser)
    sub.required = True

    def verb(name: str, help_text: str):
        p = sub.add_parser(name, help=help_text, allow_abbrev=False)
        _session_option(p, True)
        return p

    verb("status", "show the session binding and the checkpoint summary")
    p = verb("show", "print the sections with their hashes")
    p.add_argument("--ledger")
    p.add_argument("--section", action="append")
    p = verb("validate", "validate a full serialized block")
    p.add_argument("--from", dest="source", required=True)
    p = verb("update", "replace one section body, guarded by its hash")
    p.add_argument("--section", required=True)
    p.add_argument("--expect-section", required=True)
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--ledger")
    p = verb("note", "append to the ledger history (later plan)")
    p.add_argument("--from", dest="source")
    verb("lint", "scan the registered ledgers")
    p = verb("handoff", "write an immutable snapshot (later plan)")
    p.add_argument("--from", dest="source")
    p = verb("bind", "bind a session to a ledger (driver only)")
    p.add_argument("--ledger", required=True)
    p.add_argument("--project")
    p.add_argument("--workstream")
    p.add_argument("--predecessor")
    for name in ("create", "init"):
        p = verb(name, name + " a ledger (driver only, later plan)")
        p.add_argument("--ledger")
        p.add_argument("--project")
        p.add_argument("--workstream")
        p.add_argument("--task")
    return parser


def check_home() -> str:
    home = os.environ.get("CKPT_HOME", "")
    if not home or not os.path.isdir(home):
        raise Exit(EXIT_NO_HOME, "checkpoint: CKPT_HOME is not set to an existing directory")
    return os.path.realpath(home)


def run(argv: list) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # --help and --version leave through argparse
        return exc.code if isinstance(exc.code, int) else EXIT_OK
    home = check_home()
    verb = args.verb
    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if verb != "lint":
        if not session:
            raise Exit(EXIT_USAGE, "checkpoint: no session id; use --session or CLAUDE_CODE_SESSION_ID")
        if not SESSION_RE.match(session):
            raise Exit(EXIT_USAGE, "checkpoint: session id has an unexpected shape")
    ctx = Context(home, session, verb)
    if verb in NOT_IMPLEMENTED:
        raise Exit(EXIT_INTERNAL, "checkpoint: %s is not implemented in this build step" % verb)
    return VERBS[verb](ctx, args)


def main(argv: list) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.write(BRAND + "\n")
    try:
        return run(argv)
    except Exit as exc:
        if exc.message:
            sys.stderr.write(exc.message + "\n")
        return exc.code
    except Exception as exc:  # exit 1: internal error, one line, no traceback
        sys.stderr.write("checkpoint: internal error: %s\n" % type(exc).__name__)
        return EXIT_INTERNAL
    finally:
        try:
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
