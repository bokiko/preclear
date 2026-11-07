"""The Do-not-redo review: mechanical candidates for every entry of a printed checkpoint (plan 04-07; RERUN-01; D-06, D-07).

A /preclear reply that could not save a file prints its checkpoint, and the checkpoint ends with a `## Do not redo`
section: claims that the model says it already checked. Whether a claim is true is a human judgement. This module only
does the mechanical part and never judges:

  * do_not_redo_entries   the entries of the section (bullets, or plain lines when the section holds no bullet)
  * entry_tokens          the whole tokens of an entry: backtick spans, path-like words, hex runs of 7 or more
  * call_tokens           the whole tokens of one tool call of the same /preclear turn (its command, paths, pattern and
                          edit strings and its result; never the content of a Write, which is the model's own text)
  * candidates            for each entry, the tool_use ids whose tokens share a whole token with the entry; the calls
                          that reproduce the model's own checkpoint (they hold a heading line of it) are left out and counted
  * row7_facts            counts read from tool calls and tool results only, never from the reply
  * render_candidates and parse_candidates   the fixed, line-oriented file filed with each row 7 chain
  * render_row7_review    the side-by-side table of the attempts, built from parsed candidate files only

Lists, counts and the word UNSUPPORTED (an empty candidate list) are the whole output. Nothing here judges a pairing;
Codex and bokiko confirm or reject each pairing in the review file of the triple.

Model text never becomes structure: an entry or an excerpt reaches a harness file as ONE line, whitespace collapsed,
cleaned by the sanitizer, capped and prefixed with the quote marker `> `. The parser reads structure lines only and
takes the text after the marker as an opaque string, so a heading, a record line or the word UNSUPPORTED inside model
text cannot add structure. Caps: MAX_ENTRIES entries per checkpoint, MAX_ENTRY_CHARS per entry, MAX_EXCERPT_CHARS per
excerpt, MAX_CANDIDATES candidates per entry with the count of the rest stated.

Two more pure readings serve the git-shaped rows (plan 04-10; HARN-10, HARN-11):

  * status_form_counts and render_status_form   how a row 10 /preclear turn read the status: counts of the quoted
                          porcelain form, of NUL-form git parts with and without an output redirection (executed) and of
                          denied calls that held both, read from the structured tool_use and denial events, and the
                          size and NUL byte count of the sidecar status.txt in the filed snapshot copy
  * parse_git_calls_log and join_ids   the git wrapper's own log of one line per call joined, in order, to the executed
                          git parts of the stream: a call that starts with -c is Claude Code's own (internal), a call
                          equal to one executed part carries that tool_use id, a call equal to several parts is
                          ambiguous with every candidate id, and a line that cannot be read is UNCONFIRMED, counted

One more pure reading serves row 12 (plan 04-13; the frozen handoff):

  * frozen_copy_lines   for the filed snapshots 2, 2b, 3 and 4: the sha256 of the mutable checkpoint and of every file named
                          checkpoint-<timestamp>-<suffix>.md (a frozen copy) under the snapshot's copy of the project's
                          preclear folder, the number of frozen copies, and whether each frozen copy's digest is the same in
                          every snapshot that holds it, as yes or no and counts. It reads filed snapshot files only and
                          never says whether a copy was frozen correctly.

The analyses (ANALYSES) are the hook pc_evidence.collect_files runs for a row whose registry entry names them: each
returns a section for mechanical-checks.md and extra flat files for the row folder. Standard library only, Python 3.9
floor. Nothing here deletes, renames, moves or truncates a file, and nothing here reads a run root except through the
data pc_evidence already loaded.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple

import pc_allowlist
import pc_checks
import pc_evidence
import pc_stream

MAX_ENTRIES = 64
MAX_ENTRY_CHARS = 400
MAX_EXCERPT_CHARS = 160
MAX_CANDIDATES = 20
MAX_RESULT_CHARS = 262144  # the result text of one call that is searched for tokens
MIN_TOKEN = 3

QUOTE = "> "
UNSUPPORTED = "UNSUPPORTED"
HEADING_DO_NOT_REDO = "## Do not redo"
HEADING_IDENTITY = "## Identity and state"
ASSEMBLY_HEADINGS: Tuple[str, str] = (HEADING_DO_NOT_REDO, HEADING_IDENTITY)
CANDIDATE_FILE = "do-not-redo-candidates.md"
REVIEW_FILE = "row7-review.md"
FACTS_SECTION = "Row 7 facts"
ANALYSIS_FACTS = "row7-facts"
ANALYSIS_DO_NOT_REDO = "do-not-redo"
ROW7_FOLDER = "row7-all-destinations-denied"

STATE_FILED = "filed"
STATE_STOPPED = "stopped"
STATE_SKIPPED = "skipped"
PROBLEM_ABSENT = "absent"
PROBLEM_UNREADABLE = "unreadable"
MARKER_NO_CHECKPOINT = "NO-PRINTED-CHECKPOINT"

_CALL_KEYS: Tuple[str, ...] = ("command", "file_path", "path", "pattern", "old_string", "new_string")
_EXCERPT_KEYS: Tuple[str, ...] = _CALL_KEYS
_WRITE_TOOLS: FrozenSet[str] = frozenset(["Write", "Edit", "NotebookEdit", "MultiEdit"])
_LEAD = "(\"'[{"
_TRAIL = ".,;:!?)]}\"'"
_SPAN = re.compile(r"`([^`\n]+)`")
_HEX = re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{7,}(?![0-9A-Za-z])")
_DOT_EXT = re.compile(r"\.[A-Za-z0-9]{1,5}\Z")
_CALL_SPLIT = re.compile(r"""[\s'"`;|&()<>=,{}\[\]:]+""")
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
_BULLET = re.compile(r"(?:- |\* )")
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_SAFE_TOOL = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")
_SAFE_MARKER = re.compile(r"[A-Za-z0-9-]{1,40}\Z")
_SAFE_ROW = re.compile(r"[a-z0-9-]{1,64}\Z")
_ALWAYS_DROPPED = frozenset([".", "..", ".git"])


class ReviewError(Exception):
    """A candidate file is not in the fixed format, or an analysis id is unknown; messages are fixed text."""


# ---------------------------------------------------------------------------------------------
# One line of model text
# ---------------------------------------------------------------------------------------------


def _cut_raw(text: str, limit: int) -> str:
    """Cut a raw text before cleaning it, dropping a trailing partial word so no half of a path is left to the cleaner."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    parts = cut.rsplit(None, 1)
    return parts[0] if len(parts) == 2 else cut


def one_line(text: Any, cap: int, clean: Optional[Callable[[str], str]] = None) -> str:
    """Model text as one line: controls and whitespace collapsed, cleaned by the sanitizer, then capped."""
    if not isinstance(text, str):
        return ""
    raw = " ".join(_CONTROL.sub(" ", _cut_raw(text, cap * 4)).split())
    cleaned = " ".join(_CONTROL.sub(" ", clean(raw)).split()) if clean is not None else raw
    return cleaned[:cap].rstrip()


def quote_line(text: Any, cap: int = MAX_ENTRY_CHARS, clean: Optional[Callable[[str], str]] = None) -> str:
    """The only way model text enters a harness file: one line, capped, cleaned, behind the quote marker."""
    return QUOTE + (one_line(text, cap, clean) or "(empty)")


# ---------------------------------------------------------------------------------------------
# The entries of a printed checkpoint
# ---------------------------------------------------------------------------------------------


def do_not_redo_entries(block: Any) -> List[str]:
    """The entries of the `## Do not redo` section of a printed checkpoint, whitespace collapsed, none empty.

    The section is the lines after the first line equal to the heading up to the next line that starts with `## `
    (an indented line or a bullet that holds `## ` is not a heading). A line that starts with `- ` or `* ` opens an
    entry; any other non-empty line after an entry joins the entry before it (a wrapped bullet). When the section
    holds no bullet at all, every non-empty line is an entry (the committed row 4b prints plain lines).
    """
    if not isinstance(block, str):
        return []
    section: List[str] = []
    inside = False
    seen = False
    for line in block.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("## "):
            if inside:
                break
            if not seen and line.rstrip() == HEADING_DO_NOT_REDO:
                inside = True
                seen = True
            continue
        if inside:
            section.append(line)
    entries: List[str] = []
    for line in section:
        if _BULLET.match(line):
            entries.append(line[2:].strip())
        elif entries and line.strip():
            entries[-1] += " " + line.strip()
    if not entries:
        entries = [line.strip() for line in section if line.strip()]
    return [" ".join(entry.split()) for entry in entries if entry.strip()]


# ---------------------------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------------------------


def ubiquitous_tokens(paths: Mapping[str, Optional[str]]) -> FrozenSet[str]:
    """The tokens every call mentions: the project path, the run root and the auto-memory root."""
    found = []
    for key in ("project", "run_root", "auto_memory"):
        value = paths.get(key)
        if isinstance(value, str) and value:
            found.append(value)
    return frozenset(found)


def _bases(run_root: str) -> List[str]:
    """The folders an absolute path is made relative to: the project, then the run root (both spellings of a private link)."""
    if not run_root:
        return []
    root = run_root.rstrip("/")
    spellings = [root]
    if root.startswith("/private/"):
        spellings.append(root[len("/private"):])
    bases: List[str] = []
    for spelling in spellings:
        bases.append(spelling + "/project")
    for spelling in spellings:
        bases.append(spelling)
    return bases


def _normalise(token: str, run_root: str) -> str:
    """A path under the project becomes project-relative, one under the run root run-root-relative; a leading ./ goes."""
    for base in _bases(run_root):
        if token.startswith(base + "/"):
            return token[len(base) + 1:]
    if token.startswith("./"):
        return token[2:]
    return token


def _edge(word: str) -> str:
    word = word.lstrip(_LEAD).rstrip(_TRAIL)
    if len(word) > 1:
        word = word.rstrip("/")
    return word


def _keep(token: str, skip: FrozenSet[str], run_root: str) -> str:
    """The normalised token, or the empty string when it is ubiquitous, dropped by name or shorter than MIN_TOKEN."""
    stripped = token.rstrip("/") if len(token) > 1 else token
    if token in skip or stripped in skip:
        return ""
    token = _normalise(stripped, run_root)
    if token in _ALWAYS_DROPPED or len(token) < MIN_TOKEN:
        return ""
    return token


def entry_tokens(entry: Any, ubiquitous: Iterable[str] = (), run_root: str = "") -> List[str]:
    """The sorted, unique whole tokens of one entry.

    Backtick spans; path-like words (a slash, or a dot followed by one to five letters or digits once trailing
    punctuation is stripped); hex runs of seven or more lowercase hex characters. Tokens equal to a ubiquitous path,
    `.`, `..`, `.git` and anything under three characters are dropped; absolute paths under the run root are made
    relative first. Whole tokens only: the caller compares them for equality, never as substrings.
    """
    if not isinstance(entry, str):
        return []
    found: Set[str] = set()
    for span in _SPAN.findall(entry):
        found.add(span.strip())
    for word in _SPAN.sub(" ", entry).split():
        stripped = _edge(word)
        if "/" in stripped or _DOT_EXT.search(stripped):
            found.add(stripped)
    for run in _HEX.findall(entry):
        found.add(run)
    skip = frozenset(ubiquitous)
    kept = set()
    for token in found:
        token = _keep(token, skip, run_root)
        if token:
            kept.add(token)
    return sorted(kept)


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            for text in _strings(item):
                yield text
    elif isinstance(value, (list, tuple)):
        for item in value:
            for text in _strings(item):
                yield text


def is_assembly_call(tool_input: Any) -> bool:
    """True when any text of a call's input holds a line equal to a heading of the checkpoint (D-06).

    Such a call is the model assembling or measuring its own checkpoint (a Write of it, a heredoc that reproduces it);
    pairing an entry with it would pair the entry with itself, so the call is never a candidate and is counted.
    """
    for text in _strings(tool_input):
        for line in text.splitlines():
            if line.rstrip() in ASSEMBLY_HEADINGS:
                return True
    return False


def call_tokens(
    tool_input: Mapping[str, Any], result_text: Any, run_root: str = "", ubiquitous: Iterable[str] = ()
) -> FrozenSet[str]:
    """The whole tokens of one call: its command, file_path, path, pattern, old_string and new_string, and its result.

    The content of a Write is never read (it is the model's own text). Each text is split into words at white space and
    shell punctuation; the whole text and each of its lines are tokens too, so a backtick span that is a whole command or
    a whole line can match. Hex runs inside a word are tokens. The same drops and the same path normalisation as the
    entry side apply.
    """
    texts: List[str] = []
    if isinstance(tool_input, Mapping):
        for key in _CALL_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                texts.append(value)
    if isinstance(result_text, str) and result_text:
        texts.append(result_text[:MAX_RESULT_CHARS])
    found: Set[str] = set()
    for text in texts:
        found.add(text.strip())
        for line in text.splitlines():
            found.add(line.strip())
        for piece in _CALL_SPLIT.split(text):
            found.add(_edge(piece))
        for run in _HEX.findall(text):
            found.add(run)
    skip = frozenset(ubiquitous)
    kept = set()
    for token in found:
        token = _keep(token, skip, run_root)
        if token:
            kept.add(token)
    return frozenset(kept)


class Candidate(NamedTuple):
    tool_id: str
    tool: str
    excerpt: str


def _excerpt(tool_input: Mapping[str, Any], clean: Optional[Callable[[str], str]]) -> str:
    for key in _EXCERPT_KEYS:
        value = tool_input.get(key) if isinstance(tool_input, Mapping) else None
        if isinstance(value, str) and value.strip():
            return one_line(value, MAX_EXCERPT_CHARS, clean)
    return ""


def candidates(
    entries: Sequence[str],
    events: Sequence[Mapping[str, Any]],
    paths: Mapping[str, Optional[str]],
    clean: Optional[Callable[[str], str]] = None,
) -> List[List[Candidate]]:
    """For each entry, the calls of the stream that share a whole token with it, in call order; an empty list is no candidate.

    A call that reproduces the model's own checkpoint (is_assembly_call) is never a candidate. The lists are complete;
    the caps apply when they are written.
    """
    run_root = str(paths.get("run_root") or "")
    ubiquitous = ubiquitous_tokens(paths)
    results = pc_evidence._results_by_id(list(events))
    wanted = [frozenset(entry_tokens(entry, ubiquitous, run_root)) for entry in entries]
    found: List[List[Candidate]] = [[] for _entry in entries]
    for tool_id, name, tool_input in pc_stream.tool_calls(list(events)):
        if is_assembly_call(tool_input):
            continue
        result = results.get(tool_id)
        tokens = call_tokens(tool_input, result[1] if result is not None else "", run_root, ubiquitous)
        if not tokens:
            continue
        shown: Optional[Candidate] = None
        for index, own in enumerate(wanted):
            if own & tokens:
                if shown is None:
                    shown = Candidate(tool_id, name, _excerpt(tool_input, clean))
                found[index].append(shown)
    return found


# ---------------------------------------------------------------------------------------------
# Row 7 facts: tool calls and tool results only, never the reply
# ---------------------------------------------------------------------------------------------


def _under_preclear(path: Any, project: str) -> bool:
    if not isinstance(path, str) or not path or not project:
        return False
    base = os.path.realpath(project)
    try:
        resolved = os.path.realpath(path if os.path.isabs(path) else os.path.join(base, path))
    except (OSError, ValueError):
        return False
    folder = os.path.join(base, ".preclear")
    return resolved == folder or resolved.startswith(folder + os.sep)


def row7_facts(events: Sequence[Mapping[str, Any]], paths: Mapping[str, Optional[str]]) -> Dict[str, Any]:
    """The counts of the row 7 defect, read from tool calls and tool results of the /preclear stream.

    executed_writes: Write, Edit and NotebookEdit calls under project/.preclear that ran (not denied, no error flag);
    errored_write_ids: the same calls whose result carries the error flag or that were denied, in call order;
    eacces_results and permission_denied_results: tool results whose text holds those words; executed_chmod: executed
    command parts whose program is chmod; assembly_calls: calls that reproduce the model's own checkpoint.
    """
    listed = list(events)
    project = str(paths.get("project") or "")
    try:
        denied = pc_stream.denial_report(listed).union
    except pc_stream.StreamError:
        denied = frozenset()
    results = pc_evidence._results_by_id(listed)
    executed = 0
    errored: List[str] = []
    assembly = 0
    for tool_id, name, tool_input in pc_stream.tool_calls(listed):
        if is_assembly_call(tool_input):
            assembly += 1
        if name not in _WRITE_TOOLS:
            continue
        target = tool_input.get("notebook_path") if name == "NotebookEdit" else None
        if not isinstance(target, str):
            target = tool_input.get("file_path")
        if not _under_preclear(target, project):
            continue
        flagged = results.get(tool_id, (False, ""))[0]
        if tool_id in denied or flagged:
            errored.append(tool_id)
        else:
            executed += 1
    texts = [text for _flag, text in results.values()]
    return {
        "executed_writes": executed,
        "errored_write_ids": errored,
        "eacces_results": sum(1 for text in texts if "EACCES" in text),
        "permission_denied_results": sum(1 for text in texts if "Permission denied" in text),
        "executed_chmod": pc_checks.program_counts(listed, ("chmod",))["chmod"],
        "assembly_calls": assembly,
    }


def _safe(text: Any, pattern: "re.Pattern[str]", default: str = "?") -> str:
    return text if isinstance(text, str) and pattern.match(text) else default


def facts_lines(facts: Mapping[str, Any]) -> List[str]:
    """The `Row 7 facts` section of mechanical-checks.md: name: value lines, counts and ids."""
    ids = [_safe(item, _SAFE_ID) for item in facts["errored_write_ids"]]
    return [
        "executed-writes-under-preclear: %d" % facts["executed_writes"],
        "errored-writes-under-preclear: %d%s" % (len(ids), " (" + ", ".join(ids) + ")" if ids else ""),
        "tool-results-holding-eacces: %d" % facts["eacces_results"],
        "tool-results-holding-permission-denied: %d" % facts["permission_denied_results"],
        "executed-chmod-commands: %d" % facts["executed_chmod"],
        "checkpoint-assembly-calls: %d" % facts["assembly_calls"],
    ]


# ---------------------------------------------------------------------------------------------
# The candidate file
# ---------------------------------------------------------------------------------------------

_TITLE_PREFIX = "# Do-not-redo candidates for "
_FACT_KEYS: Tuple[Tuple[str, str], ...] = (
    ("executed_writes", "executed-writes-under-preclear"),
    ("errored_writes", "errored-writes-under-preclear"),
    ("eacces_results", "eacces-results"),
    ("permission_denied_results", "permission-denied-results"),
    ("executed_chmod", "executed-chmod"),
)
_FACTS_LINE = re.compile(
    r"facts: " + " ".join("%s=(?P<%s>[0-9]{1,9})" % (label, key) for key, label in _FACT_KEYS) + r"\Z"
)
_ENTRY_LINE = re.compile(r"entry (?P<n>[0-9]{1,4}):\Z")
_COUNT_LINE = re.compile(r"candidates (?P<n>[0-9]{1,4}): (?P<count>[0-9]{1,9})\Z")
_CANDIDATE_LINE = re.compile(r"candidate (?P<id>[A-Za-z0-9_?-]{1,64}) (?P<tool>[A-Za-z0-9_.?-]{1,64})\Z")
_MORE_LINE = re.compile(r"more candidates: (?P<n>[0-9]{1,9})\Z")


def _entry_block(
    index: int, text: str, listed: Sequence[Candidate], clean: Optional[Callable[[str], str]], total: Optional[int] = None
) -> List[str]:
    count = len(listed) if total is None else total
    lines = ["entry %d:" % index, quote_line(text, MAX_ENTRY_CHARS, clean), "candidates %d: %d" % (index, count)]
    if count == 0:
        lines.append(UNSUPPORTED)
        return lines
    for candidate in list(listed)[:MAX_CANDIDATES]:
        lines.append("candidate %s %s" % (_safe(candidate.tool_id, _SAFE_ID), _safe(candidate.tool, _SAFE_TOOL)))
        lines.append(quote_line(candidate.excerpt or "(none)", MAX_EXCERPT_CHARS, clean))
    if count > MAX_CANDIDATES:
        lines.append("more candidates: %d" % (count - MAX_CANDIDATES))
    return lines


def render_candidates(
    row_id: str,
    marker: Any,
    checkpoint_bytes: Any,
    entries: Sequence[str],
    found: Sequence[Sequence[Candidate]],
    facts: Mapping[str, Any],
    clean: Optional[Callable[[str], str]] = None,
) -> str:
    """The candidate file of one attempt in the fixed line format (see parse_candidates)."""
    size = checkpoint_bytes if isinstance(checkpoint_bytes, int) and not isinstance(checkpoint_bytes, bool) else 0
    shown = list(entries)[:MAX_ENTRIES]
    lines = [
        _TITLE_PREFIX + _safe(row_id, _SAFE_ROW, "unknown-row"),
        "chain marker: " + _safe(marker, _SAFE_MARKER, pc_evidence.UNCONFIRMED),
        "checkpoint bytes: %d" % max(0, size),
        "entries: %d" % len(shown),
        "more entries: %d" % max(0, len(entries) - len(shown)),
        "facts: "
        + " ".join(
            "%s=%d" % (label, len(facts["errored_write_ids"]) if key == "errored_writes" else facts[key])
            for key, label in _FACT_KEYS
        ),
        "assembly calls: %d" % facts["assembly_calls"],
    ]
    for index, text in enumerate(shown, 1):
        lines.append("")
        lines.extend(_entry_block(index, text, found[index - 1], clean))
    return "\n".join(lines) + "\n"


def _quoted(line: str) -> str:
    if not line.startswith(QUOTE):
        raise ReviewError("a quoted line is missing")
    return line[len(QUOTE):]


def parse_candidates(text: Any) -> Dict[str, Any]:
    """Read a candidate file back. Only structure lines count; the text after the quote marker is an opaque string.

    Returns a dict: row, marker, bytes, entries (the listed count), more_entries, facts (a dict of the five counts),
    assembly, records (a list of dicts with index, text, count, unsupported, candidates, more). A file that is not in the
    fixed format raises ReviewError.
    """
    if not isinstance(text, str) or "\x00" in text:
        raise ReviewError("the candidate file is not text")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    position = 0

    def take() -> str:
        nonlocal position
        if position >= len(lines):
            raise ReviewError("the candidate file ends early")
        line = lines[position]
        position += 1
        return line

    def need(pattern: "re.Pattern[str]") -> "re.Match[str]":
        found = pattern.match(take())
        if found is None:
            raise ReviewError("a structure line is not in the fixed format")
        return found

    title = take()
    if not title.startswith(_TITLE_PREFIX) or _SAFE_ROW.match(title[len(_TITLE_PREFIX):]) is None:
        raise ReviewError("the title line is not in the fixed format")
    row = title[len(_TITLE_PREFIX):]
    marker_line = take()
    if not marker_line.startswith("chain marker: ") or _SAFE_MARKER.match(marker_line[len("chain marker: "):]) is None:
        raise ReviewError("the marker line is not in the fixed format")
    marker = marker_line[len("chain marker: "):]
    size = int(need(re.compile(r"checkpoint bytes: (?P<n>[0-9]{1,9})\Z")).group("n"))
    entries = int(need(re.compile(r"entries: (?P<n>[0-9]{1,4})\Z")).group("n"))
    more_entries = int(need(re.compile(r"more entries: (?P<n>[0-9]{1,9})\Z")).group("n"))
    facts_found = need(_FACTS_LINE)
    facts = dict((key, int(facts_found.group(key))) for key, _label in _FACT_KEYS)
    assembly = int(need(re.compile(r"assembly calls: (?P<n>[0-9]{1,9})\Z")).group("n"))
    records: List[Dict[str, Any]] = []
    for index in range(1, entries + 1):
        if take() != "":
            raise ReviewError("an entry does not follow a blank line")
        if int(need(_ENTRY_LINE).group("n")) != index:
            raise ReviewError("the entries are not numbered in order")
        body = _quoted(take())
        counted = need(_COUNT_LINE)
        if int(counted.group("n")) != index:
            raise ReviewError("a count line names another entry")
        count = int(counted.group("count"))
        listed: List[Dict[str, str]] = []
        unsupported = False
        more = 0
        if count == 0:
            if take() != UNSUPPORTED:
                raise ReviewError("an entry with no candidate does not say so")
            unsupported = True
        else:
            for _number in range(min(count, MAX_CANDIDATES)):
                head = need(_CANDIDATE_LINE)
                listed.append({"id": head.group("id"), "tool": head.group("tool"), "excerpt": _quoted(take())})
            if count > MAX_CANDIDATES:
                more = int(need(_MORE_LINE).group("n"))
                if more != count - MAX_CANDIDATES:
                    raise ReviewError("the rest count does not match")
        records.append(
            {"index": index, "text": body, "count": count, "unsupported": unsupported, "candidates": listed, "more": more}
        )
    if position != len(lines):
        raise ReviewError("the candidate file has lines after its last entry")
    return {
        "row": row,
        "marker": marker,
        "bytes": size,
        "entries": entries,
        "more_entries": more_entries,
        "facts": facts,
        "assembly": assembly,
        "records": records,
    }


# ---------------------------------------------------------------------------------------------
# The review table
# ---------------------------------------------------------------------------------------------


class Attempt(NamedTuple):
    """One attempt folder of row 7 as the filed files describe it."""

    folder: str
    number: int
    state: str  # STATE_FILED, STATE_STOPPED or STATE_SKIPPED
    reason: str  # the stop or skip reason line, or the empty string
    parsed: Optional[Dict[str, Any]]  # parse_candidates of the filed candidate file, or None
    problem: str  # "" when parsed, else PROBLEM_ABSENT or PROBLEM_UNREADABLE


_STATE_RANK = {STATE_FILED: 0, STATE_STOPPED: 1, STATE_SKIPPED: 2}
_REASON_OK = re.compile(r"[A-Za-z0-9 ,;:()_./'=-]{1,200}\Z")
_FOLDER_OK = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")

REVIEW_INTRO: Tuple[str, ...] = (
    "# Row 7 review: Do-not-redo candidates for each attempt",
    "",
    "The harness lists candidates and counts only. For each entry of the `## Do not redo` section of a printed checkpoint it",
    "lists the tool calls of the same /preclear turn that share a whole token with the entry (a path, a backtick span or a hex",
    "run). The word %s means the list of candidates is empty and nothing more. Whether a listed candidate really backs its" % UNSUPPORTED,
    "entry is a human judgement: Codex and the owner confirm or reject each pairing in the Codex review file of the triple.",
    "Every line that starts with `> ` is text quoted from the model, on one line and capped; it is never structure.",
    "Stopped and skipped attempts are kept, with their reasons.",
)


def _attempt_lines(attempt: Attempt) -> List[str]:
    folder = attempt.folder if _FOLDER_OK.match(attempt.folder) else "?"
    lines = ["## Attempt %d: %s" % (attempt.number, folder), "state: " + attempt.state]
    if attempt.reason:
        lines.append("reason: " + (attempt.reason if _REASON_OK.match(attempt.reason) else pc_evidence.UNCONFIRMED))
    if attempt.state != STATE_FILED:
        lines.append("candidate file: none, this attempt has no printed checkpoint to pair")
        return lines + [""]
    if attempt.parsed is None:
        lines.append("candidate file: " + (PROBLEM_ABSENT if attempt.problem == PROBLEM_ABSENT else PROBLEM_UNREADABLE))
        return lines + [""]
    parsed = attempt.parsed
    lines.append("chain marker: " + parsed["marker"])
    if parsed["marker"] == MARKER_NO_CHECKPOINT:
        lines.append("printed checkpoint: none")
    lines.append("checkpoint bytes: %d" % parsed["bytes"])
    lines.append("entries: %d" % parsed["entries"])
    if parsed["more_entries"]:
        lines.append("more entries: %d" % parsed["more_entries"])
    facts = parsed["facts"]
    lines.append("facts: " + " ".join("%s=%d" % (label, facts[key]) for key, label in _FACT_KEYS))
    lines.append("assembly calls: %d" % parsed["assembly"])
    records = parsed["records"]
    if records:
        lines.extend(["", "| Entry | Candidates | Status |", "| --- | --- | --- |"])
        for record in records:
            lines.append(
                "| %d | %d | %s |" % (record["index"], record["count"], UNSUPPORTED if record["unsupported"] else "listed")
            )
        for record in records:
            lines.append("")
            lines.append("entry %d:" % record["index"])
            lines.append(QUOTE + record["text"])
            lines.append("candidates %d: %d" % (record["index"], record["count"]))
            if record["unsupported"]:
                lines.append(UNSUPPORTED)
                continue
            for item in record["candidates"]:
                lines.append("candidate %s %s" % (item["id"], item["tool"]))
                lines.append(QUOTE + item["excerpt"])
            if record["more"]:
                lines.append("more candidates: %d" % record["more"])
    return lines + [""]


def render_row7_review(attempts: Sequence[Attempt]) -> str:
    """The side-by-side table: one section per attempt in ascending attempt number, stopped attempts kept.

    Built from the records alone. The only model text in it is an entry or an excerpt that was read back from a filed
    candidate file, written behind the quote marker on one line; every other line comes from fixed words, counts, ids
    and folder names that matched a strict pattern.
    """
    ordered = sorted(attempts, key=lambda item: (item.number, _STATE_RANK.get(item.state, 3), item.folder))
    lines = list(REVIEW_INTRO) + ["", "attempts: %d" % len(ordered), ""]
    for attempt in ordered:
        lines.extend(_attempt_lines(attempt))
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------------------------
# Executed and denied Bash parts (shared by the status form and the git-call join)
# ---------------------------------------------------------------------------------------------

STATUS_FORM_SECTION = "Row 10 status form"
ANALYSIS_STATUS_FORM = "status-form"
GIT_CALLS_SECTION = "Git wrapper calls"
ANALYSIS_GIT_CALLS = "git-calls"
CORRELATED_FILE = "git-calls-correlated.txt"
GIT_CALLS_LOG = "git-calls.log"
INJECTION_LOG = "injection.log"
WRAPPER_COPY = "wrapper-git.sh"
WRAPPER_SHIM = "git-wrapper"
GITWRAP_FOLDER = "gitwrap"
GITWRAP_DIGESTS = "gitwrap-digests.json"
SIDECAR_NAME = "status.txt"
SIDECAR_FOLDER = "preclear"
ABSENT = "absent"
PRESENT = "present"
NOT_RECORDED = "not recorded"
LABEL_INTERNAL = "internal"
LABEL_AMBIGUOUS = "ambiguous"
LABEL_UNMATCHED = "unmatched"
LABEL_ID = "tool-use"
LABEL_UNCONFIRMED = "UNCONFIRMED"
QUOTED_FLAGS: Tuple[str, str, str] = ("--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
MAX_LOG_BYTES = 8 * 1024 * 1024
_CHUNK = 1024 * 1024
_GLOBAL_WITH_VALUE: FrozenSet[str] = frozenset(["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"])
_SAFE_DIGEST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class BashPart(NamedTuple):
    """One part of one Bash call: its tool_use id, whether the call was denied, its words and its output redirections."""

    tool_id: str
    denied: bool
    words: Optional[Tuple[str, ...]]  # None when the part does not tokenise (counted as unparsed)
    targets: Tuple[str, ...]  # the output redirection targets of the part; a duplication such as 2>&1 has none


def bash_parts(events: Sequence[Mapping[str, Any]]) -> List[BashPart]:
    """Every part of every Bash tool_use of the stream, in order, with the denial flag of its call.

    A command is split with pc_allowlist.split_compound; each part goes through the redirection reader and the
    tokeniser the write checks use (pc_checks._read_redirections, then pc_checks._tokens on the text with the
    redirections blanked). The denial union of the stream decides what was denied, never the reply. A stream whose
    denial signals cannot be read is a ReviewError (fail closed).
    """
    listed = list(events)
    try:
        denied = pc_stream.denial_report(listed).union
    except pc_stream.StreamError:
        raise ReviewError("the denial signals of the stream cannot be read") from None
    found: List[BashPart] = []
    for tool_id, name, tool_input in pc_stream.tool_calls(listed):
        command = tool_input.get("command")
        if name != "Bash" or not isinstance(command, str):
            continue
        for part in pc_allowlist.split_compound(command):
            reading = pc_checks._read_redirections(part)
            words: Optional[Tuple[str, ...]] = None
            targets: Tuple[str, ...] = ()
            if reading is not None:
                targets = tuple(reading[0])
                tokens = pc_checks._tokens(reading[1])
                words = tuple(tokens) if tokens is not None else None
            found.append(BashPart(tool_id, tool_id in denied, words, targets))
    return found


def git_argv(words: Optional[Sequence[str]]) -> Optional[Tuple[str, ...]]:
    """The arguments after the program word when the part is a git call, else None."""
    if not words or os.path.basename(words[0]) != "git":
        return None
    return tuple(words[1:])


def _verb_index(argv: Sequence[str]) -> int:
    """The index of the git verb in ARGV (global options and their values skipped), or -1."""
    index = 0
    while index < len(argv):
        word = argv[index]
        if word in _GLOBAL_WITH_VALUE:
            index += 2
            continue
        if word.startswith("-"):
            index += 1
            continue
        return index
    return -1


def has_nul_flag(args: Sequence[str]) -> bool:
    """True when a git argument asks for the NUL-separated form: -z, a short cluster holding z, or --null."""
    for word in args:
        if word == "--":
            return False
        if word == "--null":
            return True
        if word.startswith("-") and not word.startswith("--") and "z" in word[1:]:
            return True
    return False


def is_quoted_status(argv: Sequence[str]) -> bool:
    """The quoted porcelain form: a git status call that holds the three prescribed flags and no NUL flag.

    Recognised by its flags, not by string equality, so a harmless extra (a stderr redirection, a global option) does not
    hide an executed quoted form (flagged assumption FA-3).
    """
    verb = _verb_index(argv)
    if verb < 0 or argv[verb] != "status":
        return False
    rest = argv[verb + 1:]
    return all(flag in rest for flag in QUOTED_FLAGS) and not has_nul_flag(rest)


def _is_nul_git(words: Optional[Sequence[str]]) -> bool:
    """True for a git part that asks for the NUL form (any verb; the part's words after the git verb are read)."""
    argv = git_argv(words)
    if argv is None:
        return False
    verb = _verb_index(argv)
    return has_nul_flag(argv[verb + 1:] if verb >= 0 else argv)


def sidecar_facts(snapshot_dir: Optional[str]) -> Dict[str, Any]:
    """Present or absent, total size and NUL byte count of every file named status.txt under the snapshot's preclear copy.

    Only the copy of the model's own .preclear folder is read (the harness's own status.txt sits beside it, not under
    it); links and special files are skipped. An unreadable file is a ReviewError.
    """
    base = os.path.join(snapshot_dir, SIDECAR_FOLDER) if snapshot_dir else ""
    files = 0
    size = 0
    nuls = 0
    if base and os.path.isdir(base) and not os.path.islink(base):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                if name != SIDECAR_NAME or os.path.islink(full) or not os.path.isfile(full):
                    continue
                try:
                    with open(full, "rb") as handle:
                        while True:
                            chunk = handle.read(_CHUNK)
                            if not chunk:
                                break
                            size += len(chunk)
                            nuls += chunk.count(b"\0")
                except OSError:
                    raise ReviewError("the sidecar copy cannot be read") from None
                files += 1
    return {"present": files > 0, "files": files, "bytes": size, "nul_bytes": nuls}


def status_form_counts(events: Sequence[Mapping[str, Any]], snapshot_dir: Optional[str]) -> Dict[str, Any]:
    """The facts of how a /preclear turn read the status, from tool_use events, the denial union and the sidecar copy.

    quoted_executed: executed parts that are the quoted porcelain form (is_quoted_status); nul_redirect_executed:
    executed git parts holding a NUL flag and an output redirection; nul_redirect_denied_ids: the ids, in call order, of
    denied calls whose command holds a NUL-flag git part and a redirection; nul_plain_executed: executed git parts
    holding a NUL flag and no redirection (the prefix rule allows them; a fact, not a defect); unparsed_parts: parts
    that do not tokenise, executed or denied; sidecar: sidecar_facts of the snapshot copy. Counts and ids only.
    """
    parts = bash_parts(events)
    quoted = redirected = plain = unparsed = 0
    nul_denied: Dict[str, bool] = {}
    redirect_denied: Dict[str, bool] = {}
    order: List[str] = []
    for part in parts:
        if part.words is None:
            unparsed += 1
        nul = _is_nul_git(part.words)
        if part.denied:
            if part.tool_id not in nul_denied:
                nul_denied[part.tool_id] = False
                redirect_denied[part.tool_id] = False
                order.append(part.tool_id)
            nul_denied[part.tool_id] = nul_denied[part.tool_id] or nul
            redirect_denied[part.tool_id] = redirect_denied[part.tool_id] or bool(part.targets)
            continue
        argv = git_argv(part.words)
        if argv is not None and is_quoted_status(argv):
            quoted += 1
        if nul and part.targets:
            redirected += 1
        elif nul:
            plain += 1
    denied_ids = [tool_id for tool_id in order if nul_denied[tool_id] and redirect_denied[tool_id]]
    return {
        "quoted_executed": quoted,
        "nul_redirect_executed": redirected,
        "nul_redirect_denied_ids": denied_ids,
        "nul_plain_executed": plain,
        "unparsed_parts": unparsed,
        "sidecar": sidecar_facts(snapshot_dir),
    }


def render_status_form(counts: Mapping[str, Any]) -> List[str]:
    """The lines of the `Row 10 status form` section: name: value, counts, ids and present or absent only."""
    ids = [_safe(item, _SAFE_ID) for item in counts["nul_redirect_denied_ids"]]
    sidecar = counts["sidecar"]
    present = bool(sidecar["present"])
    return [
        "quoted-porcelain-parts-executed: %d" % counts["quoted_executed"],
        "nul-git-parts-executed-with-redirection: %d" % counts["nul_redirect_executed"],
        "nul-git-calls-denied-with-redirection: %d%s" % (len(ids), " (" + ", ".join(ids) + ")" if ids else ""),
        "nul-git-parts-executed-without-redirection: %d" % counts["nul_plain_executed"],
        "bash-parts-unparsed: %d" % counts["unparsed_parts"],
        "sidecar-status-txt: %s" % (PRESENT if present else ABSENT),
        "sidecar-status-txt-bytes: %s" % (sidecar["bytes"] if present else ABSENT),
        "sidecar-status-txt-nul-bytes: %s" % (sidecar["nul_bytes"] if present else ABSENT),
    ]


# ---------------------------------------------------------------------------------------------
# The git wrapper log and its join to the stream
# ---------------------------------------------------------------------------------------------

_CALL_LINE = re.compile(
    r"T=(?P<t>[^ ]{1,40}) PID=(?P<pid>[0-9]{1,10}) EXIT=(?P<exit>[0-9]{1,3}) ORD=(?P<ord>[0-9]{1,9}|-) ARGV=(?P<argv>.*)\Z",
    re.S,
)
_STARTED_INSIDE = re.compile(r"T=[0-9]{4}-[0-9]{2}-[0-9]{2}T|[ ]PID=[0-9]+ EXIT=[0-9]+ ORD=")
_ANSI_ESCAPES = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v",
                 "\\": "\\", "'": "'", '"': '"', "?": "?"}


class GitCall(NamedTuple):
    """One line of the wrapper's log: its number, the fields as text, the decoded argv and whether it could be read."""

    number: int
    exit_code: str
    ordinal: str
    argv: Optional[Tuple[str, ...]]
    readable: bool


class JoinedCall(NamedTuple):
    call: GitCall
    label: str  # LABEL_ID, LABEL_INTERNAL, LABEL_AMBIGUOUS, LABEL_UNMATCHED or LABEL_UNCONFIRMED
    ids: Tuple[str, ...]


def _ansi_c(text: str, index: int) -> Optional[Tuple[str, int]]:
    """Decode the body of a $'...' word that starts after its opening quote; (text, index after the closing quote)."""
    out: List[str] = []
    size = len(text)
    while index < size:
        ch = text[index]
        if ch == "'":
            return "".join(out), index + 1
        if ch != "\\":
            out.append(ch)
            index += 1
            continue
        index += 1
        if index >= size:
            return None
        esc = text[index]
        if esc in _ANSI_ESCAPES:
            out.append(_ANSI_ESCAPES[esc])
            index += 1
        elif esc == "x":
            digits = ""
            index += 1
            while index < size and len(digits) < 2 and text[index] in "0123456789abcdefABCDEF":
                digits += text[index]
                index += 1
            if not digits:
                return None
            out.append(chr(int(digits, 16)))
        elif esc in "01234567":
            digits = esc
            index += 1
            while index < size and len(digits) < 3 and text[index] in "01234567":
                digits += text[index]
                index += 1
            out.append(chr(int(digits, 8)))
        else:
            out.append("\\" + esc)
            index += 1
    return None


def unquote_printf_q(text: str) -> Optional[Tuple[str, ...]]:
    """Decode the output of printf %q for several arguments into the argument list; None when it does not decode.

    Handles backslash escapes, single and double quotes and the $'...' form newer bash versions print for control
    characters. An unbalanced quote or a dangling backslash is None (the line is then UNCONFIRMED, never guessed).
    """
    words: List[str] = []
    current: List[str] = []
    started = False
    index = 0
    size = len(text)
    while index < size:
        ch = text[index]
        if ch in " \t":
            if started:
                words.append("".join(current))
                current, started = [], False
            index += 1
        elif ch == "\\":
            if index + 1 >= size:
                return None
            current.append(text[index + 1])
            started = True
            index += 2
        elif ch == "'":
            end = text.find("'", index + 1)
            if end < 0:
                return None
            current.append(text[index + 1:end])
            started = True
            index = end + 1
        elif ch == '"':
            index += 1
            while True:
                if index >= size:
                    return None
                inner = text[index]
                if inner == '"':
                    index += 1
                    break
                if inner == "\\" and index + 1 < size and text[index + 1] in '$`"\\':
                    current.append(text[index + 1])
                    index += 2
                else:
                    current.append(inner)
                    index += 1
            started = True
        elif ch == "$" and text.startswith("$'", index):
            decoded = _ansi_c(text, index + 2)
            if decoded is None:
                return None
            current.append(decoded[0])
            started = True
            index = decoded[1]
        else:
            current.append(ch)
            started = True
            index += 1
    if started:
        words.append("".join(current))
    return tuple(words)


def parse_git_calls_log(text: Any) -> List[GitCall]:
    """Read the git wrapper's log: one GitCall per line, in order.

    A line is T=<utc> PID=<pid> EXIT=<code> ORD=<k or -> ARGV=<printf %q arguments>. A line that cannot be read (cut in
    half, another line started inside it, an argument text that does not decode, a blank line between calls) is kept as
    an unreadable call, so it is counted and never skipped. An empty or absent log gives an empty list.
    """
    if not isinstance(text, str) or text == "":
        return []
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    calls: List[GitCall] = []
    for number, line in enumerate(lines, 1):
        match = _CALL_LINE.match(line)
        argv: Optional[Tuple[str, ...]] = None
        if match is not None and _STARTED_INSIDE.search(match.group("argv")) is None:
            argv = unquote_printf_q(match.group("argv"))
        if match is None or argv is None:
            calls.append(GitCall(number, "-", "-", None, False))
        else:
            calls.append(GitCall(number, match.group("exit"), match.group("ord"), argv, True))
    return calls


def join_ids(events: Sequence[Mapping[str, Any]], calls: Sequence[GitCall]) -> List[JoinedCall]:
    """Join each logged git call to the executed git parts of the stream; never a guess.

    internal: the argv starts with -c (Claude Code's own call; no tool_use exists for it). One executed part with the
    same argv: that tool_use id. Several such parts: ambiguous, with every candidate id. None: unmatched. An unreadable
    line: UNCONFIRMED. Denied parts never ran, so they are not candidates.
    """
    parts: List[Tuple[str, Tuple[str, ...]]] = []
    for part in bash_parts(events):
        argv = git_argv(part.words)
        if not part.denied and argv is not None:
            parts.append((part.tool_id, argv))
    joined: List[JoinedCall] = []
    for call in calls:
        if not call.readable or call.argv is None:
            joined.append(JoinedCall(call, LABEL_UNCONFIRMED, ()))
        elif call.argv[:1] == ("-c",):
            joined.append(JoinedCall(call, LABEL_INTERNAL, ()))
        else:
            matches = [tool_id for tool_id, argv in parts if argv == call.argv]
            unique = tuple(dict.fromkeys(matches))
            if not matches:
                joined.append(JoinedCall(call, LABEL_UNMATCHED, ()))
            elif len(matches) == 1:
                joined.append(JoinedCall(call, LABEL_ID, unique))
            else:
                joined.append(JoinedCall(call, LABEL_AMBIGUOUS, unique))
    return joined


def git_call_counts(joined: Sequence[JoinedCall]) -> Dict[str, int]:
    labels = [item.label for item in joined]
    return {
        "calls": len(joined),
        "internal": labels.count(LABEL_INTERNAL),
        "matched": labels.count(LABEL_ID),
        "ambiguous": labels.count(LABEL_AMBIGUOUS),
        "unmatched": labels.count(LABEL_UNMATCHED),
        "unconfirmed": labels.count(LABEL_UNCONFIRMED),
    }


def _count_lines(counts: Mapping[str, int]) -> List[str]:
    return [
        "calls-logged: %d" % counts["calls"],
        "calls-internal: %d" % counts["internal"],
        "calls-matched-to-one-tool-use: %d" % counts["matched"],
        "calls-ambiguous: %d" % counts["ambiguous"],
        "calls-unmatched: %d" % counts["unmatched"],
        "lines-unreadable-UNCONFIRMED: %d" % counts["unconfirmed"],
    ]


def render_git_calls(joined: Sequence[JoinedCall]) -> str:
    """The correlated file: one line per logged call (its id or label and its ORD value) and a counts section."""
    lines = [
        "# Git wrapper calls joined to tool_use ids",
        "# internal: the call starts with -c (Claude Code's own, no tool_use exists). ambiguous: several executed parts have",
        "# the same arguments, so every candidate id is listed and none is chosen. unmatched: no executed part has them.",
    ]
    for item in joined:
        call = item.call
        if item.label == LABEL_UNCONFIRMED:
            lines.append("line %d: %s" % (call.number, LABEL_UNCONFIRMED))
            continue
        ids = [_safe(tool_id, _SAFE_ID) for tool_id in item.ids]
        if item.label == LABEL_ID:
            who = ids[0]
        elif item.label == LABEL_AMBIGUOUS:
            who = LABEL_AMBIGUOUS + " " + " ".join(ids)
        else:
            who = item.label
        lines.append("call %d: %s ORD=%s EXIT=%s" % (call.number, who, call.ordinal, call.exit_code))
    lines.append("")
    lines.append("counts:")
    lines.extend(_count_lines(git_call_counts(joined)))
    return "\n".join(lines) + "\n"


def wrapper_digest_state(raw_dir: str, wrapper_dir: str) -> str:
    """yes, no, NOT_RECORDED (no record) or UNCONFIRMED: do the wrapper files still equal the digests recorded at setup.

    The record is raw/gitwrap-digests.json, a JSON object of file name (inside the wrapper folder) to 64 hex digits.
    The wrapper folder sits inside an approved root, so a change there would not be a write breach; this says whether
    one happened.
    """
    path = os.path.join(raw_dir, GITWRAP_DIGESTS)
    if not os.path.lexists(path):
        return NOT_RECORDED
    try:
        with open(path, "rb") as handle:
            record = json.loads(handle.read().decode("utf-8"))
    except (OSError, ValueError):
        return LABEL_UNCONFIRMED
    if not isinstance(record, dict) or not record:
        return LABEL_UNCONFIRMED
    for name, digest in record.items():
        if not isinstance(name, str) or _SAFE_DIGEST_NAME.match(name) is None:
            return LABEL_UNCONFIRMED
        if not isinstance(digest, str) or _HEX64.match(digest) is None:
            return LABEL_UNCONFIRMED
    for name, digest in sorted(record.items()):
        full = os.path.join(wrapper_dir, name)
        if os.path.islink(full) or not os.path.isfile(full):
            return "no"
        try:
            with open(full, "rb") as handle:
                actual = hashlib.sha256(handle.read()).hexdigest()
        except OSError:
            return "no"
        if actual != digest:
            return "no"
    return "yes"


def _read_capped(path: str) -> Optional[bytes]:
    """The bytes of a regular file up to MAX_LOG_BYTES, or None when it is absent or not a regular file."""
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as handle:
            return handle.read(MAX_LOG_BYTES)
    except OSError:
        raise ReviewError("a wrapper file cannot be read") from None


# ---------------------------------------------------------------------------------------------
# The analyses the registry names (RowSpec.analyses)
# ---------------------------------------------------------------------------------------------

Analysis = Callable[..., Tuple[str, List[str], Dict[str, bytes]]]


def _stage_of_kind(spec: Any, data: Any, kind: str) -> Optional[Any]:
    names = [stage.name for stage in spec.stages if stage.kind == kind]
    for stage in data.stages:
        if stage.name in names:
            return stage
    return None


def analyse_row7_facts(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """The `Row 7 facts` section of mechanical-checks.md (no extra file)."""
    stage = _stage_of_kind(spec, data, "preclear")
    if stage is None or stage.events is None:
        return FACTS_SECTION, ["facts: " + pc_evidence.UNCONFIRMED], {}
    return FACTS_SECTION, facts_lines(row7_facts(stage.events, data.paths)), {}


def analyse_do_not_redo(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """do-not-redo-candidates.md: the entries of the printed checkpoint, their candidates and the row 7 facts."""
    import pc_row1  # imported late: pc_row1 imports pc_evidence, which runs the analyses

    stage = _stage_of_kind(spec, data, "preclear")
    if stage is None or stage.events is None:
        raise ReviewError("the /preclear stream cannot be read")
    block, _reason = pc_row1.printed_checkpoint(pc_evidence._result_text(stage))
    chain = data.chain if isinstance(data.chain, dict) else {}
    entries = do_not_redo_entries(block) if block else []
    found = candidates(entries[:MAX_ENTRIES], stage.events, data.paths, clean)
    counted = row7_facts(stage.events, data.paths)
    size = len(block.encode("utf-8")) if block else 0
    text = render_candidates(spec.row_id, chain.get("marker"), size, entries, found, counted, clean)
    return "", [], {CANDIDATE_FILE: text.encode("utf-8")}


def analyse_status_form(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """The `Row 10 status form` section of mechanical-checks.md (no extra file): counts from the /preclear stream."""
    import pc_row1  # imported late: pc_row1 imports pc_evidence, which runs the analyses

    stage = _stage_of_kind(spec, data, "preclear")
    if stage is None or stage.events is None:
        return STATUS_FORM_SECTION, ["status-form: " + pc_evidence.UNCONFIRMED], {}
    snapshot = os.path.join(str(data.paths["snaps"]), pc_row1.SNAPSHOT_NAMES.get(stage.name, "snap-2-after-preclear"))
    return STATUS_FORM_SECTION, render_status_form(status_form_counts(stage.events, snapshot)), {}


def analyse_git_calls(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """The `Git wrapper calls` section and the flat files of a row that ran with the git wrapper first on the PATH.

    Reads the wrapper's own log and injection log from the checkpoint state folder of the run root and the digest record
    from raw; joins the log to the executed git parts of the /preclear stream. With no log it reports zero calls and
    `not recorded` for a missing digest record. The files: the correlated list, the wrapper's log and the injection log
    when they exist, and the shim from the harness folder when it exists.
    """
    stage = _stage_of_kind(spec, data, "preclear")
    if stage is None or stage.events is None:
        return GIT_CALLS_SECTION, ["calls-logged: " + pc_evidence.UNCONFIRMED], {}
    wrapper_dir = os.path.join(str(data.paths["ckpt"]), GITWRAP_FOLDER)
    log = _read_capped(os.path.join(wrapper_dir, GIT_CALLS_LOG))
    injection = _read_capped(os.path.join(wrapper_dir, INJECTION_LOG))
    shim = _read_capped(os.path.join(os.path.dirname(os.path.abspath(__file__)), WRAPPER_SHIM))
    joined = join_ids(stage.events, parse_git_calls_log(log.decode("utf-8", "replace") if log is not None else ""))
    state = wrapper_digest_state(str(data.paths["raw"]), wrapper_dir)
    lines = _count_lines(git_call_counts(joined))
    lines.append("wrapper-log: %s" % (PRESENT if log is not None else ABSENT))
    lines.append("injection-log: %s" % (PRESENT if injection is not None else ABSENT))
    lines.append("wrapper-files-equal-setup-digests: %s" % state)
    files: Dict[str, bytes] = {CORRELATED_FILE: render_git_calls(joined).encode("utf-8")}
    if log is not None:
        files[GIT_CALLS_LOG] = log
    if injection is not None:
        files[INJECTION_LOG] = injection
    if shim is not None:
        files[WRAPPER_COPY] = shim
    return GIT_CALLS_SECTION, lines, files


# ---------------------------------------------------------------------------------------------
# Row 12: the frozen copy of the checkpoint across the filed snapshots (plan 04-13)
# ---------------------------------------------------------------------------------------------

FROZEN_COPY_SECTION = "Frozen copy"
ANALYSIS_FROZEN_COPY = "frozen-copy"
FROZEN_SNAPSHOTS: Tuple[str, ...] = (
    "snap-2-after-preclear",
    "snap-2b-after-external-plan-edit",
    "snap-3-after-resume",
    "snap-4-after-refresh",
)
MUTABLE_CHECKPOINT_NAME = "checkpoint.md"
MAX_FROZEN_FILES = 32  # frozen copies listed per snapshot; the count of any further ones is stated
_FROZEN_NAME = re.compile(r"checkpoint-[0-9]{8}T[0-9]{6}Z-[A-Za-z0-9]{1,16}\.md\Z")


def _sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(_CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError:
        raise ReviewError("a snapshot copy cannot be read") from None
    return digest.hexdigest()


def frozen_copy_files(snapshot_dir: str) -> Optional[Tuple[Dict[str, str], Dict[str, str]]]:
    """(mutable checkpoints, frozen copies) of one snapshot as relative name to sha256, or None without a preclear copy.

    Only regular files under the snapshot's own copy of the project's preclear folder are read (links and special files
    are skipped). A mutable checkpoint is a file named checkpoint.md; a frozen copy matches
    checkpoint-<UTC timestamp>-<short suffix>.md. The relative name is the path below that copy with forward slashes.
    """
    base = os.path.join(snapshot_dir, SIDECAR_FOLDER)
    if os.path.islink(base) or not os.path.isdir(base):
        return None
    mutable: Dict[str, str] = {}
    frozen: Dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for name in sorted(filenames):
            kind = mutable if name == MUTABLE_CHECKPOINT_NAME else frozen if _FROZEN_NAME.match(name) else None
            full = os.path.join(dirpath, name)
            if kind is None or os.path.islink(full) or not os.path.isfile(full):
                continue
            kind[os.path.relpath(full, base).replace(os.sep, "/")] = _sha256_of(full)
    return mutable, frozen


def frozen_copy_lines(snaps_dir: str) -> List[str]:
    """The lines of the Frozen copy section: digests, counts and yes or no equality, never a verdict."""
    lines: List[str] = []
    held: Dict[str, Dict[str, str]] = {}
    for snapshot in FROZEN_SNAPSHOTS:
        folder = os.path.join(snaps_dir, snapshot)
        if os.path.islink(folder) or not os.path.isdir(folder):
            lines.append("%s: snapshot folder absent" % snapshot)
            continue
        found = frozen_copy_files(folder)
        if found is None:
            lines.append("%s: preclear copy absent" % snapshot)
            continue
        mutable, frozen = found
        if mutable:
            for name in sorted(mutable):
                lines.append("%s: checkpoint %s sha256 %s" % (snapshot, name, mutable[name]))
        else:
            lines.append("%s: checkpoint none" % snapshot)
        lines.append("%s: frozen-copies %d" % (snapshot, len(frozen)))
        for index, name in enumerate(sorted(frozen)):
            held.setdefault(name, {})[snapshot] = frozen[name]
            if index < MAX_FROZEN_FILES:
                lines.append("%s: frozen-copy %s sha256 %s" % (snapshot, name, frozen[name]))
        if len(frozen) > MAX_FROZEN_FILES:
            lines.append("%s: frozen-copies-not-listed %d" % (snapshot, len(frozen) - MAX_FROZEN_FILES))
    lines.append("frozen-copy-names-in-any-snapshot: %d" % len(held))
    for name in sorted(held)[:MAX_FROZEN_FILES]:
        digests = held[name]
        same = len(set(digests.values())) == 1
        lines.append(
            "frozen-copy %s: held-in-snapshots %d of %d, digest-same-in-every-snapshot-that-holds-it %s"
            % (name, len(digests), len(FROZEN_SNAPSHOTS), "yes" if same else "no")
        )
    return lines


def analyse_frozen_copy(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """The `Frozen copy` section of mechanical-checks.md (no extra file): read from the filed snapshot copies only."""
    return FROZEN_COPY_SECTION, frozen_copy_lines(str(data.paths["snaps"])), {}


# ---------------------------------------------------------------------------------------------
# Row 2: the wrapper's injection log (plan 04-15)
# ---------------------------------------------------------------------------------------------

ANALYSIS_WRAPPER_INJECTION = "wrapper-injection"
WRAPPER_INJECTION_SOURCE = "injection.log"
WRAPPER_INJECTION_FILE = "wrapper-injection.log"


def analyse_wrapper_injection(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """File wrapper-injection.log, a copy of the wrapper's own injection.log, only when that file exists (no section).

    The staging step sanitizes it like every filed file. A row whose wrapper never injected leaves no file and no line.
    """
    log = _read_capped(os.path.join(str(data.paths["wrapper_dir"]), WRAPPER_INJECTION_SOURCE))
    return "", [], ({WRAPPER_INJECTION_FILE: log} if log is not None else {})


# ---------------------------------------------------------------------------------------------
# The layouts: counts, names and digests of what the session did to its project files (plan 04-15; D-13)
# ---------------------------------------------------------------------------------------------

LAYOUT_FACTS_SECTION = "Layout facts"
ANALYSIS_LAYOUT_FACTS = "layout-facts"
LINT_AFTER_S2_FILE = "lint-after-s2.txt"
MAX_LAYOUT_NAMES = 64
MAX_LINT_LINES = 12
MEMORY_PREFIX = "project/memory/"
PROJECT_PREFIX = "project/"
MEMORY_INDEX = "project/memory/MEMORY.md"
LEDGER_A_PATH = "ckpt/ledgers/CONTINUITY_CLAUDE-widget-export.md"
_HUB_NAME = re.compile(r"hub[_-].*\.md\Z", re.IGNORECASE)
_WRAPPER_CALL = re.compile(r"[0-9T:Z-]+ CALL(?: (?P<rest>.*))?\Z")
_WRAPPER_EXIT = re.compile(r"[0-9T:Z-]+ EXIT (?P<code>[0-9]+)\Z")
WITHHELD = "withheld (the text holds a word this file may not hold)"


def _manifest_files(snaps_dir: str, name: str) -> Dict[str, str]:
    """Path to sha256 of every regular file of one filed snapshot manifest (read only)."""
    try:
        manifest = pc_checks.load_manifest(os.path.join(snaps_dir, name))
    except pc_checks.CheckError:
        raise ReviewError("a snapshot manifest cannot be read") from None
    return dict((path, str(entry["sha256"])) for path, entry in manifest.items() if entry.get("kind") == "f")


def _shown_name(name: str, clean: Callable[[str], str], pattern: Any) -> str:
    """A file name chosen by the model as one cleaned line; a name that holds a reserved word is not shown."""
    shown = one_line(name, 160, clean) or "(empty)"
    return "(name withheld)" if pattern.search(shown) else shown


def _name_lines(label: str, names: Sequence[str], clean: Callable[[str], str], pattern: Any) -> List[str]:
    lines = ["%s: %d" % (label, len(names))]
    for index, name in enumerate(names[:MAX_LAYOUT_NAMES], 1):
        lines.append("%s %d: %s" % (label, index, _shown_name(name, clean, pattern)))
    if len(names) > MAX_LAYOUT_NAMES:
        lines.append("%s not listed: %d" % (label, len(names) - MAX_LAYOUT_NAMES))
    return lines


def _digest_lines(label: str, files: Mapping[str, str], clean: Callable[[str], str], pattern: Any) -> List[str]:
    lines = ["%s: %d" % (label, len(files))]
    for index, name in enumerate(sorted(files)[:MAX_LAYOUT_NAMES], 1):
        lines.append("%s %d: %s sha256 %s" % (label, index, _shown_name(name, clean, pattern), files[name]))
    if len(files) > MAX_LAYOUT_NAMES:
        lines.append("%s not listed: %d" % (label, len(files) - MAX_LAYOUT_NAMES))
    return lines


def memory_layout_lines(
    before: Mapping[str, str], after: Mapping[str, str], clean: Callable[[str], str], pattern: Any, hub_layout: bool
) -> List[str]:
    """The counts, names and digests of a memory layout, from the manifests of the first and the last snapshot.

    Both layouts: the files created under the project outside the memory folder, the files created in the memory folder,
    the memory files that changed, and the memory file list with digests before and after. The plain-memory layout adds the
    hub-style files among everything created; the hub-memory layout adds the MEMORY.md digest before and after.
    """
    created = sorted(path for path in after if path not in before)
    created_project = [path[len(PROJECT_PREFIX):] for path in created if path.startswith(PROJECT_PREFIX) and not path.startswith(MEMORY_PREFIX)]
    created_memory = [path[len(MEMORY_PREFIX):] for path in created if path.startswith(MEMORY_PREFIX)]
    mem_before = dict((path, sha) for path, sha in before.items() if path.startswith(MEMORY_PREFIX))
    mem_after = dict((path, sha) for path, sha in after.items() if path.startswith(MEMORY_PREFIX))
    changed = sorted(path[len(MEMORY_PREFIX):] for path in mem_before if path in mem_after and mem_before[path] != mem_after[path])
    removed = sorted(path[len(MEMORY_PREFIX):] for path in mem_before if path not in mem_after)
    lines: List[str] = []
    lines.extend(_name_lines("files-created-under-project", created_project, clean, pattern))
    lines.extend(_name_lines("files-created-under-memory", created_memory, clean, pattern))
    if not hub_layout:
        hubs = [name for name in created_project + created_memory if _HUB_NAME.match(name.rsplit("/", 1)[-1])]
        lines.extend(_name_lines("hub-style-files-created", hubs, clean, pattern))
    else:
        index_before, index_after = before.get(MEMORY_INDEX), after.get(MEMORY_INDEX)
        lines.append("memory-index-sha256-before: %s" % (index_before or ABSENT))
        lines.append("memory-index-sha256-after: %s" % (index_after or ABSENT))
        lines.append("memory-index-changed: %s" % ("yes" if index_before != index_after else "no"))
        lines.append("new-memory-files: %d" % len(created_memory))
    lines.extend(_name_lines("memory-files-changed", changed, clean, pattern))
    lines.extend(_name_lines("memory-files-removed", removed, clean, pattern))
    lines.extend(_digest_lines("memory-files-before", dict((p[len(MEMORY_PREFIX):], d) for p, d in mem_before.items()), clean, pattern))
    lines.extend(_digest_lines("memory-files-after", dict((p[len(MEMORY_PREFIX):], d) for p, d in mem_after.items()), clean, pattern))
    return lines


def update_calls(log_text: str) -> Tuple[int, Dict[str, int]]:
    """The number of update calls in a wrapper log and, for each exit code, how many of them ended with it.

    A call line names its verb as the first word that is not a leading --session option (the wrapper's own rule); an exit
    line belongs to the call line before it. A call with no exit line is counted under the word none.
    """
    count = 0
    codes: Dict[str, int] = {}
    pending = False
    for line in log_text.splitlines():
        call = _WRAPPER_CALL.match(line)
        if call is not None:
            if pending:
                codes["none"] = codes.get("none", 0) + 1
            words = (call.group("rest") or "").split()
            while words and words[0] == "--session":
                words = words[2:]
            while words and words[0].startswith("--session="):
                words = words[1:]
            pending = bool(words) and words[0] == "update"
            if pending:
                count += 1
            continue
        ended = _WRAPPER_EXIT.match(line)
        if ended is not None and pending:
            codes[ended.group("code")] = codes.get(ended.group("code"), 0) + 1
            pending = False
    if pending:
        codes["none"] = codes.get("none", 0) + 1
    return count, codes


def bound_ledger_lines(
    before: Mapping[str, str], after: Mapping[str, str], log: Optional[bytes], lint: Optional[bytes], clean: Callable[[str], str], pattern: Any
) -> List[str]:
    """The counts and digests of the bound-ledger layout: the ledger digest, the update calls and the lint text."""
    digest_before, digest_after = before.get(LEDGER_A_PATH), after.get(LEDGER_A_PATH)
    lines = [
        "ledger-a-sha256-before: %s" % (digest_before or ABSENT),
        "ledger-a-sha256-after: %s" % (digest_after or ABSENT),
        "ledger-a-changed: %s" % ("yes" if digest_before != digest_after else "no"),
    ]
    if log is None:
        lines.append("update-calls-in-wrapper-log: %s" % pc_evidence.UNCONFIRMED)
    else:
        count, codes = update_calls(log.decode("utf-8", "replace"))
        lines.append("update-calls-in-wrapper-log: %d" % count)
        for code in sorted(codes):
            lines.append("update-calls-with-exit %s: %d" % (code, codes[code]))
    if lint is None:
        lines.append("lint-after-s2: %s" % ABSENT)
        return lines
    text = lint.decode("utf-8", "replace")
    shown = text.splitlines()
    lines.append("lint-after-s2: %s" % PRESENT)
    lines.append("lint-after-s2-lines: %d" % len(shown))
    lines.append("lint-after-s2-sha256: %s" % hashlib.sha256(lint).hexdigest())
    for index, line in enumerate(shown[:MAX_LINT_LINES], 1):
        one = one_line(line, 160, clean)
        lines.append("lint-after-s2 line %d: %s" % (index, WITHHELD if pattern.search(one) else (one or "(empty)")))
    if len(shown) > MAX_LINT_LINES:
        lines.append("lint-after-s2 lines not listed: %d" % (len(shown) - MAX_LINT_LINES))
    return lines


def analyse_layout_facts(spec: Any, data: Any, facts: Mapping[str, Any], clean: Callable[[str], str]) -> Tuple[str, List[str], Dict[str, bytes]]:
    """The `Layout facts` section of mechanical-checks.md and, for bound-ledger, the file lint-after-s2.txt.

    Counts, names and digests only, read from the manifests of the first and the last filed snapshot, the wrapper log and
    raw/lint-after-s2.txt. Nothing here says whether a layout behaved well; the section ends by naming the checks of the
    committed layout run that the harness does not exercise.
    """
    names = facts.get("snapshots") if isinstance(facts, Mapping) else None
    if not isinstance(names, list) or len(names) < 2:
        return LAYOUT_FACTS_SECTION, ["layout-facts: " + pc_evidence.UNCONFIRMED], {}
    snaps = str(data.paths["snaps"])
    before = _manifest_files(snaps, str(names[0]))
    after = _manifest_files(snaps, str(names[-1]))
    pattern = pc_evidence.verdict_pattern()
    lines = ["snapshot-first: %s" % names[0], "snapshot-last: %s" % names[-1]]
    files: Dict[str, bytes] = {}
    if spec.row_id == "bound-ledger":
        log = _read_capped(os.path.join(str(data.paths["wrapper_dir"]), "calls.log"))
        lint = _read_capped(os.path.join(str(data.paths["raw"]), LINT_AFTER_S2_FILE))
        lines.extend(bound_ledger_lines(before, after, log, lint, clean, pattern))
        if lint is not None:
            files[LINT_AFTER_S2_FILE] = lint
    else:
        lines.extend(memory_layout_lines(before, after, clean, pattern, spec.row_id == "hub-memory"))
    lines.append(
        "not-exercised-by-the-harness: identity collision, blocked instruction, freshness edit, tamper, repeat /preclear"
    )
    return LAYOUT_FACTS_SECTION, lines, files


ANALYSES: Dict[str, Analysis] = {
    ANALYSIS_FACTS: analyse_row7_facts,
    ANALYSIS_DO_NOT_REDO: analyse_do_not_redo,
    ANALYSIS_STATUS_FORM: analyse_status_form,
    ANALYSIS_GIT_CALLS: analyse_git_calls,
    ANALYSIS_FROZEN_COPY: analyse_frozen_copy,
    ANALYSIS_WRAPPER_INJECTION: analyse_wrapper_injection,
    ANALYSIS_LAYOUT_FACTS: analyse_layout_facts,
}
