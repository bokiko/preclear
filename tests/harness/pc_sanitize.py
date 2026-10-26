"""Runtime-built deny-list sanitizer with lower-case angle-bracket tokens (EVID-02; D-15).

The sanitizer builds its replacement table when it is constructed, from the live machine (home
folder in every form, login name, host names, temp roots, repository root) and, when it exists,
the local file .git/info/preclear-deny.txt. It applies the table in one left-to-right pass, so
replaced text is never rescanned and a second pass changes nothing. It never prints a value:
counts, token names and fixed error messages are the only text it produces about its table.

Tokens: <home> <user> <host> <tmp> <repo> are emitted for the machine's own values; <run>,
<helper> and <auto-memory-root> come from a caller-supplied mapping of absolute paths (the
committed evidence uses them); <redacted> replaces local deny-file entries; <scratch> is
accepted from callers but never emitted by default. Tokens already in the input survive.

Forms per home path: the raw form, its realpath, the two dash-slugs (slash and dot to hyphen,
and every non-alphanumeric to hyphen) and the URL-encoded forms with and without safe slashes,
each also in NFC and NFD, all matched case-insensitively. Path-like forms never cut a longer
word. The login name matches as a whole word at four or more characters; a JSON letter escape (a
backslash plus n, r, t, b or f) directly before it counts as the word boundary, and an ambiguous
escape is replaced rather than kept. The login is also one of the gate's entries (unless it occurs
inside a fixed token). Host names and deny-file entries are replaced wherever they occur, exactly
as the leak gate looks for them (one source of floors and one fail-closed file reader live in
pc_leakgate).

Do not print the result of Sanitizer.deny_entries(): it is the only accessor of private values.
"""
from __future__ import annotations

import collections
import os
import re
import tempfile
import unicodedata
import urllib.parse

try:
    import pwd
except ImportError:  # pragma: no cover - not a POSIX platform
    pwd = None

import pc_leakgate

TOKENS = (
    "<home>",
    "<user>",
    "<host>",
    "<tmp>",
    "<repo>",
    "<run>",
    "<helper>",
    "<auto-memory-root>",
    "<scratch>",
    "<redacted>",
)

# Tokens a caller may attach to its own absolute paths.
CALLER_TOKENS = frozenset(["<run>", "<helper>", "<auto-memory-root>", "<scratch>"])

LOGIN_FLOOR = 4

# Kind priority on equal text: caller map, repository root, home forms, temp, host, user, deny entries.
_PRIO_CALLER, _PRIO_REPO, _PRIO_HOME, _PRIO_TEMP, _PRIO_HOST, _PRIO_USER, _PRIO_DENY = range(7)

_PREFIX = {"path": "", "slug": "", "word": r"(?:(?<!\w)|(?<=\\[nrtbf]))", "substring": ""}
_SUFFIX = {
    "path": r"(?![A-Za-z0-9_\-]|\.[A-Za-z0-9])",
    "slug": r"(?![A-Za-z0-9])",
    "word": r"(?!\w)",
    "substring": "",
}

# Tokens already present in the input: the fixed set plus the numbered run and helper variants
# the committed evidence uses. Only the text between them is sanitised.
_TOKEN_RE = re.compile(
    "|".join(
        [re.escape(token) for token in sorted(TOKENS, key=lambda item: (-len(item), item))]
        + [r"<(?:run|helper)-[a-z0-9]+(?:-[a-z0-9]+)*>"]
    )
)

_USER_TEMP_PARENT_RE = re.compile(r"^(?:/private)?/var/folders/[^/]+/[^/]+/[^/]+$")

Sources = collections.namedtuple("Sources", "homes login hostnames temp_dirs repo_root")


class SanitizerError(Exception):
    """The sanitizer refused or failed; messages are fixed text and never hold a value."""


def _variants(text):
    return set([text, unicodedata.normalize("NFC", text), unicodedata.normalize("NFD", text)])


def _real(path):
    try:
        return os.path.realpath(path)
    except (OSError, ValueError):
        return path


def _clean_path(path):
    """Return PATH without trailing slashes, or None when nothing usable is left."""
    if not isinstance(path, str) or path.strip() == "":
        return None
    trimmed = path.rstrip("/")
    return trimmed if trimmed != "" else None


def machine_sources(repo_root=""):
    """Gather the live machine's values: HOME and the account home, login, hosts, temp dirs."""
    homes = []
    login = ""
    env_home = os.environ.get("HOME")
    if env_home:
        homes.append(env_home)
    if pwd is not None:
        try:
            entry = pwd.getpwuid(os.getuid())
            homes.append(entry.pw_dir)
            login = entry.pw_name
        except (KeyError, OSError):
            pass
    if not login:
        login = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    temp_dirs = []
    try:
        temp_dirs.append(tempfile.gettempdir())
    except OSError:
        pass
    if os.environ.get("TMPDIR"):
        temp_dirs.append(os.environ["TMPDIR"])
    return Sources(homes, login, pc_leakgate.machine_hostnames(), temp_dirs, repo_root or "")


class Sanitizer(object):
    """Applies a replacement table built at construction time. Build it with from_machine."""

    def __init__(self, entries, local_entries, host_list, login_entries=()):
        # entries: (text, token, priority, kind). local_entries, host_list and login_entries feed the gate.
        self._local = list(local_entries)
        self._hosts = list(host_list)
        self._logins = list(login_entries)
        best = {}
        for text, token, priority, kind in entries:
            if text == "" or text.strip() == "" or len(text) < 2:
                continue
            key = text.lower()
            if key not in best or priority < best[key][2]:
                best[key] = (text, token, priority, kind)
        ordered = sorted(best.values(), key=lambda item: (-len(item[0]), item[0].lower(), item[2]))
        self._table = dict((item[0].lower(), item[1]) for item in ordered)
        self._fallback = ordered
        self._counts = {}
        if ordered:
            alternation = "|".join(
                "(?:%s%s%s)" % (_PREFIX[kind], re.escape(text), _SUFFIX[kind]) for text, _token, _prio, kind in ordered
            )
            self._regex = re.compile(alternation, re.IGNORECASE)
        else:
            self._regex = None

    @classmethod
    def from_machine(cls, repo_root, extra_map=None, deny_file=None, sources=None):
        """Build a sanitizer.

        With SOURCES None the real machine is read, and the local deny file is looked up through
        git (or DENY_FILE when given). With injected SOURCES the local file is read only when
        DENY_FILE is given, so tests never depend on the real machine. A deny file that exists but
        cannot be read or decoded raises SanitizerError.
        """
        try:
            if sources is None:
                sources = machine_sources(repo_root)
                local = pc_leakgate.local_file_entries(repo_root, deny_file)
            elif deny_file is not None:
                local = pc_leakgate.local_file_entries(repo_root, deny_file)
            else:
                local = []
        except pc_leakgate.ScannerError:
            raise SanitizerError("the local deny file could not be read") from None
        entries = []
        for home in sources.homes:
            cleaned = _clean_path(home)
            if cleaned is None:
                continue
            for base in _variants(cleaned) | _variants(_real(cleaned)):
                entries.append((base, "<home>", _PRIO_HOME, "path"))
                entries.append((base.replace("/", "-").replace(".", "-"), "<home>", _PRIO_HOME, "slug"))
                entries.append((re.sub(r"[^A-Za-z0-9]", "-", base), "<home>", _PRIO_HOME, "slug"))
                entries.append((urllib.parse.quote(base, safe=""), "<home>", _PRIO_HOME, "path"))
                entries.append((urllib.parse.quote(base, safe="/"), "<home>", _PRIO_HOME, "path"))
        login = sources.login
        login_entries = []
        if isinstance(login, str) and len(login.strip()) >= LOGIN_FLOOR:
            for form in _variants(login):
                entries.append((form, "<user>", _PRIO_USER, "word"))
            stripped = login.strip()
            # FA-4: a login that occurs inside a fixed token would make the gate refuse its own tokens.
            if not any(stripped.lower() in token for token in TOKENS):
                login_entries = sorted(_variants(stripped))
        for temp in sources.temp_dirs:
            cleaned = _clean_path(temp)
            if cleaned is None:
                continue
            for form in set([cleaned, _real(cleaned)]):
                entries.append((form, "<tmp>", _PRIO_TEMP, "path"))
                if _USER_TEMP_PARENT_RE.match(form):
                    entries.append((os.path.dirname(form), "<tmp>", _PRIO_TEMP, "path"))
        repo = _clean_path(sources.repo_root)
        if repo is not None:
            for form in set([repo, _real(repo)]):
                entries.append((form, "<repo>", _PRIO_REPO, "path"))
        for path, token in dict(extra_map or {}).items():
            if token not in CALLER_TOKENS:
                raise SanitizerError("a caller token is not one of the allowed tokens")
            cleaned = _clean_path(path)
            if cleaned is None:
                continue
            for form in set([cleaned, _real(cleaned)]):
                entries.append((form, token, _PRIO_CALLER, "path"))
        hosts = pc_leakgate.host_entries(list(sources.hostnames))
        for host in hosts:
            entries.append((host, "<host>", _PRIO_HOST, "substring"))
        for entry in local:
            if entry.strip() != "":
                entries.append((entry, "<redacted>", _PRIO_DENY, "substring"))
        return cls(entries, local, hosts, login_entries)

    def _token_for(self, text):
        token = self._table.get(text.lower())
        if token is None:
            for entry_text, entry_token, _prio, _kind in self._fallback:
                if re.fullmatch(re.escape(entry_text), text, re.IGNORECASE):
                    token = entry_token
                    break
        if token is None:
            token = "<redacted>"
        self._counts[token] = self._counts.get(token, 0) + 1
        return token

    def _apply(self, piece):
        if self._regex is None or piece == "":
            return piece
        return self._regex.sub(lambda match: self._token_for(match.group(0)), piece)

    def sanitize_text(self, text):
        """Return TEXT with every table entry replaced by its token; tokens already present survive."""
        if not isinstance(text, str):
            raise SanitizerError("text is required")
        if text == "":
            return ""
        out = []
        last = 0
        for match in _TOKEN_RE.finditer(text):
            out.append(self._apply(text[last:match.start()]))
            out.append(match.group(0))
            last = match.end()
        out.append(self._apply(text[last:]))
        return "".join(out)

    def sanitize_bytes(self, data):
        """Decode DATA as strict UTF-8, sanitise it and return UTF-8 bytes."""
        decoded = None
        try:
            decoded = bytes(data).decode("utf-8")
        except (UnicodeDecodeError, TypeError, ValueError):
            decoded = None
        if decoded is None:
            raise SanitizerError("input is not valid UTF-8")
        return self.sanitize_text(decoded).encode("utf-8")

    def counts(self):
        """Replacement counts per token (a copy)."""
        return dict(self._counts)

    def deny_entry_count(self):
        """The number of usable entries read from the local deny file."""
        return len(self._local)

    def deny_entries(self):
        """Host-name, local-file and login entries for the leak gate. Private: never print the result."""
        return sorted(set(self._hosts) | set(self._local) | set(self._logins))

    def __repr__(self):
        return "Sanitizer(%d pattern(s), %d deny entr(ies))" % (len(self._fallback), len(self._local))

    __str__ = __repr__
