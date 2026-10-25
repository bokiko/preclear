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
separator appended. Bind, create and init refuse a ledger or root outside
CKPT_HOME; show, update, note, handoff and init refuse a ledger outside a
registered root; handoff refuses a handoffs folder that resolves outside CKPT_HOME.

Session identity: --session (before or after the verb), else the
CLAUDE_CODE_SESSION_ID variable, else exit 2. The short id is the first eight
characters.

Verbs. Model-facing: status, show, validate, update, note, handoff and lint. The
driver-only verbs exist so a test driver can build state and never appear in a
model-facing allowlist:

    bind    driver only: bind a session to a ledger under CKPT_HOME
    create  driver only: make CONTINUITY_CLAUDE-<task>.md under a registered root
    init    driver only: write a validated serialized block into a ledger without one

Every write verb (update, note, handoff, bind, create, init) runs the write guard
first, then holds one dedicated lock file, CKPT_HOME/.lock, across read, compare and
atomic replace. The ledger itself is never locked, because os.replace swaps its
inode. Read verbs (status, show, validate, lint), --version and --help take no lock
and write nothing.

Labelled stub-internal switches. These two are the only test modes inside the stub,
and nothing else in it reads a CKPT_STUB_ variable:

    CKPT_STUB_KILL_SWITCH      1 makes every write verb exit 5 before the lock is
                               taken and before any file is touched; any other
                               value, including empty and 0, leaves it off
    CKPT_STUB_LOCK_TIMEOUT_MS  non-negative integer milliseconds the lock wait may
                               last (default 5000); any other value, including
                               empty, is a usage error (exit 2); a lock that another
                               process really holds past the deadline gives exit 6

Exit codes: 0 ok, 1 internal error, 2 usage or validation (including no
checkpoint block), 3 conflict, 4 invalid checkpoint, 5 kill switch, 6 lock
timeout, 64 CKPT_HOME missing or not a directory.

Failure handling: every mutation writes a temporary file in the target folder,
fsyncs it and swaps it in with os.replace; if that fails the stub removes its own
temporary file (the only deletion anywhere in it), leaves the target as it was and
exits 1 with ``checkpoint: internal error: <exception class name>`` and nothing
else. Any unexpected exception maps to the same exit 1 line.

UNCONFIRMED behaviours. Where references/checkpoint-v1.md and the committed
evidence are silent the stub takes the most literal reading and marks it here so
the branch table can mirror this list. None of these was observed against the
real helper:

  * note: stdout and exit code (the stub prints ``noted in <ledger>`` and exits
    0; appends under the History heading a ``### <iso-ms>Z (<id8>)`` heading and
    the body, which is the one committed effect; a ledger with no History heading
    gets one appended; a ledger with no checkpoint block exits 2).
  * handoff: the snapshot file name and stdout (the stub resolves the session
    ledger like note does, writes the file body unchanged as
    CKPT_HOME/handoffs/handoff-<YYYYMMDDTHHMMSSmmmZ>-<id8>.md by exclusive
    creation, never overwriting, and prints ``handoff written: <path>``).
  * kill switch scope: write verbs only (update, note, handoff, bind, create,
    init); reads and validate are unaffected.
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
    --project, --workstream and --predecessor; create takes --task (required),
    --root, --project and --workstream (the last two go to the audit line only);
    init takes --ledger and --from. Their one-line outputs are ``bound ...``,
    ``created <path>`` and ``initialised <path>``.
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
import errno
import fcntl
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
EXIT_KILL = 5
EXIT_LOCK = 6
EXIT_NO_HOME = 64

KILL_SWITCH_VAR = "CKPT_STUB_KILL_SWITCH"
LOCK_TIMEOUT_VAR = "CKPT_STUB_LOCK_TIMEOUT_MS"
DEFAULT_LOCK_TIMEOUT_MS = 5000
LOCK_POLL_SECONDS = 0.02

BEGIN_RE = re.compile(r"^<!-- CHECKPOINT:BEGIN updated: (\S+) by: (\S+) -->$")
END_LINE = "<!-- CHECKPOINT:END -->"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{7,63}$")
LEDGER_GLOB_RE = re.compile(r"^CONTINUITY_CLAUDE-[^/]+\.md$")
ARROW = "→"

HISTORY_RE = re.compile(r"(?m)^## History[ \t]*$")
NEXT_HEADING_RE = re.compile(r"(?m)^## ")
BEGIN_LINE_RE = re.compile(r"(?m)^<!-- CHECKPOINT:BEGIN [^\n]*$")

TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
TIMEOUT_RE = re.compile(r"[0-9]+")


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


def require_within(path: str, base: str, message: str) -> str:
    """The one containment gate for write paths: the realpath of path, or exit 2 with message."""
    if not is_within(path, base):
        raise Exit(EXIT_USAGE, message)
    return os.path.realpath(path)


def register_root(ctx: Context, folder: str) -> None:
    roots = load_roots(ctx)
    real = require_within(folder, ctx.home, "checkpoint: ledger root is outside CKPT_HOME")
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


def audit(ledger: str, ctx: Context, verb: str, section=None, **extra) -> None:
    record = {
        "by": ctx.id8,
        "ledger": os.path.basename(ledger),
        "ts": utc_iso_ms(time.time_ns()),
        "verb": verb,
    }
    if section is not None:
        record["section"] = section
    for key, value in extra.items():
        if value is not None:
            record[key] = value
    line = json.dumps(record, sort_keys=True) + "\n"
    path = os.path.join(os.path.dirname(ledger), ".checkpoint-log.jsonl")
    with open(path, "ab") as handle:
        handle.write(line.encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


def guard_write(ctx: Context) -> None:
    """Every write verb calls this first, before any lock or file access.

    The labelled kill switch: CKPT_STUB_KILL_SWITCH equal to 1 refuses the write
    with exit 5. Any other value, including empty and 0, leaves it off.
    """
    if os.environ.get(KILL_SWITCH_VAR) == "1":
        raise Exit(EXIT_KILL, "checkpoint: kill switch active")


def lock_timeout_ms() -> int:
    """The lock wait bound from CKPT_STUB_LOCK_TIMEOUT_MS; anything but digits is exit 2."""
    raw = os.environ.get(LOCK_TIMEOUT_VAR)
    if raw is None:
        return DEFAULT_LOCK_TIMEOUT_MS
    if not TIMEOUT_RE.fullmatch(raw):
        raise Exit(
            EXIT_USAGE,
            "checkpoint: usage error: %s must be a non-negative integer (milliseconds)" % LOCK_TIMEOUT_VAR,
        )
    return int(raw)


class WriteLock(object):
    """Exclusive flock on CKPT_HOME/.lock, retried every 20 ms until the deadline (exit 6)."""

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.fd = -1

    def __enter__(self) -> "WriteLock":
        timeout = lock_timeout_ms()
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        self.fd = os.open(self.ctx.path(".lock"), flags, 0o644)
        deadline = time.monotonic() + timeout / 1000.0
        try:
            while True:
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self
                except OSError as exc:
                    if exc.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                        raise
                if time.monotonic() >= deadline:
                    raise Exit(EXIT_LOCK, "checkpoint: lock timeout")
                time.sleep(LOCK_POLL_SECONDS)
        except BaseException:
            os.close(self.fd)
            self.fd = -1
            raise

    def __exit__(self, *exc_info) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


def write_verb(func):
    """Wrap a write verb: the guard first (kill switch), then the lock held for the whole verb."""

    def wrapper(ctx: Context, args) -> int:
        guard_write(ctx)
        with WriteLock(ctx):
            return func(ctx, args)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def create_exclusive(path: str, data: bytes, mode: int = 0o644) -> None:
    """Create path with data only if it does not exist (FileExistsError otherwise); never overwrites."""
    folder = os.path.dirname(path)
    fd, temp = tempfile.mkstemp(dir=folder, prefix=".ckpt-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, mode)
        os.link(temp, path)
    finally:
        try:
            os.unlink(temp)
        except OSError:
            pass


def append_history(text: str, entry: str) -> str:
    """Append entry under ## History; every byte up to and including the end marker is kept."""
    begin = BEGIN_LINE_RE.search(text)
    end = text.find("\n" + END_LINE, begin.end()) if begin else -1
    if end < 0:
        raise Exit(EXIT_USAGE, "checkpoint: no checkpoint block")
    cut = end + 1 + len(END_LINE)
    head, tail = text[:cut], text[cut:]
    found = HISTORY_RE.search(tail)
    if found is None:
        before, after = tail, ""
        if not before.endswith("\n"):
            before += "\n"
        if not before.endswith("\n\n"):
            before += "\n"
        before += "## History\n"
    else:
        following = NEXT_HEADING_RE.search(tail, found.end())
        split = following.start() if following else len(tail)
        before, after = tail[:split], tail[split:]
    if not before.endswith("\n"):
        before += "\n"
    if not before.endswith("\n\n"):
        before += "\n"
    return head + before + entry + after


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


def parse_serialized(text: str) -> list:
    """Sections of a full serialized block (the validate and init input), or exit 4."""
    lines = text.rstrip("\n").split("\n")
    if not BEGIN_RE.match(lines[0]):
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: missing begin marker")
    if lines[-1] != END_LINE or len(lines) < 2:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: missing end marker")
    sections = parse_block_lines(lines[1:-1])
    if sections is None:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: text before the first section")
    return sections


def verb_validate(ctx: Context, args) -> int:
    sections = parse_serialized(read_input_file(args.source))
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


@write_verb
def verb_update(ctx: Context, args) -> int:
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


@write_verb
def verb_note(ctx: Context, args) -> int:
    ledger, _ = resolve_ledger(ctx, args.ledger)
    text, parsed = load_ledger(ledger)
    if parsed is None:
        raise Exit(EXIT_USAGE, "checkpoint: no checkpoint block in " + ledger)
    body = read_input_file(args.source).rstrip("\n")
    entry = "### %s (%s)\n%s\n\n" % (utc_iso_ms(time.time_ns()), ctx.id8, body)
    mode = os.stat(ledger).st_mode & 0o777
    atomic_write(ledger, append_history(text, entry).encode("utf-8"), mode)
    audit(ledger, ctx, "note")
    out("noted in %s\n" % ledger)
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


@write_verb
def verb_bind(ctx: Context, args) -> int:
    ledger = require_within(args.ledger, ctx.home, "checkpoint: ledger is outside CKPT_HOME")
    folder = require_within(os.path.dirname(ledger), ctx.home, "checkpoint: ledger is outside CKPT_HOME")
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


def compact_stamp(ns: int) -> str:
    """The time part of a handoff file name: YYYYMMDDTHHMMSSmmmZ."""
    return utc_iso_ms(ns).replace("-", "").replace(":", "").replace(".", "")


@write_verb
def verb_handoff(ctx: Context, args) -> int:
    ledger, _ = resolve_ledger(ctx, args.ledger)
    body = read_input_file(args.source)
    folder = ctx.path("handoffs")
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    require_within(folder, ctx.home, "checkpoint: handoffs folder resolves outside CKPT_HOME")
    ns = time.time_ns()
    while True:
        target = os.path.join(folder, "handoff-%s-%s.md" % (compact_stamp(ns), ctx.id8))
        try:
            create_exclusive(target, body.encode("utf-8"))
        except FileExistsError:
            ns += 1000000
            continue
        break
    audit(ledger, ctx, "handoff")
    out("handoff written: %s\n" % target)
    return EXIT_OK


@write_verb
def verb_create(ctx: Context, args) -> int:
    task = args.task
    if not TASK_RE.match(task):
        raise Exit(EXIT_USAGE, "checkpoint: --task must be a plain name (letters, digits, dot, dash, underscore)")
    requested = args.root if args.root else ctx.path("ledgers")
    root = require_within(requested, ctx.home, "checkpoint: ledger root is outside CKPT_HOME")
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "CONTINUITY_CLAUDE-%s.md" % task)
    content = "# CONTINUITY %s %s\n\n## History\n" % ("—", task)
    try:
        create_exclusive(path, content.encode("utf-8"))
    except FileExistsError:
        raise Exit(EXIT_USAGE, "checkpoint: ledger already exists")
    register_root(ctx, root)
    audit(path, ctx, "create", project=args.project, workstream=args.workstream)
    out("created %s\n" % path)
    return EXIT_OK


@write_verb
def verb_init(ctx: Context, args) -> int:
    ledger, _ = resolve_ledger(ctx, args.ledger)
    text, parsed = load_ledger(ledger)
    if parsed is not None or BEGIN_LINE_RE.search(text):
        raise Exit(EXIT_USAGE, "checkpoint: ledger already has a checkpoint block")
    sections = parse_serialized(read_input_file(args.source))
    updated = utc_iso_ms(time.time_ns())
    reason = check_block(updated, ctx.id8, sections)
    if reason:
        raise Exit(EXIT_INVALID, "checkpoint: invalid checkpoint: " + reason)
    block = render_block(updated, ctx.id8, sections)
    found = HISTORY_RE.search(text)
    if found:
        head = text[:found.start()].rstrip("\n")
        new_text = (head + "\n\n" if head else "") + block + "\n\n" + text[found.start():]
    else:
        new_text = text.rstrip("\n") + "\n\n" + block + "\n\n## History\n"
    mode = os.stat(ledger).st_mode & 0o777
    atomic_write(ledger, new_text.encode("utf-8"), mode)
    audit(ledger, ctx, "init")
    out("initialised %s\n" % ledger)
    return EXIT_OK


VERBS = {
    "status": verb_status,
    "show": verb_show,
    "validate": verb_validate,
    "update": verb_update,
    "note": verb_note,
    "handoff": verb_handoff,
    "lint": verb_lint,
    "bind": verb_bind,
    "create": verb_create,
    "init": verb_init,
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
    p = verb("note", "append to the ledger history")
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--ledger")
    verb("lint", "scan the registered ledgers")
    p = verb("handoff", "write an immutable snapshot of the file body")
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--ledger")
    p = verb("bind", "bind a session to a ledger (driver only)")
    p.add_argument("--ledger", required=True)
    p.add_argument("--project")
    p.add_argument("--workstream")
    p.add_argument("--predecessor")
    p = verb("create", "create a ledger under a registered root (driver only)")
    p.add_argument("--task", required=True)
    p.add_argument("--root")
    p.add_argument("--project")
    p.add_argument("--workstream")
    p = verb("init", "write a serialized block into a ledger that has none (driver only)")
    p.add_argument("--ledger", required=True)
    p.add_argument("--from", dest="source", required=True)
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
