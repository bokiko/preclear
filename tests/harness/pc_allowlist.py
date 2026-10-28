"""A bounded model of documented Bash permission-rule matching (HARN-06, STUB-06).

The model answers one question: would these allow rules let this Bash command run without
asking? It follows only what the Claude Code permission documentation states:

  * a compound command splits on &&, ||, ;, |, |&, & and newlines outside quotes, and every
    part must match some rule (a redirection such as 2>&1 or &> is not a separator);
  * a rule without a wildcard is exact; a trailing " *" or ":*" is a word-boundary prefix
    that also matches the bare command;
  * only timeout, time, nice, nohup, stdbuf, command, builtin and noglob are stripped before
    matching; env and path-qualified programs are not;
  * a part with a variable or command expansion outside single quotes is never allowed.

Everything else the binary decides (path scope, redirection approval, a cd combined with git,
brace-quote obfuscation, the built-in read-only command set) is not modelled. The model is a
regression guard against allowlist mistakes and is deliberately conservative; the binary is the
ground truth and plan 02-08 records a live capture to compare against.

Strings are compared exactly: no case folding, no Unicode normalisation, and only ASCII
whitespace is trimmed, so a non-breaking space or a differently normalised name never matches.

The loaders read committed evidence only and write nothing. The matcher functions take only a
command and a rule list; the text of an earlier refusal is used solely to label corpus entries.

Standard library only, Python 3.9 floor. Imported by the tests; no command-line entry point.
"""
from __future__ import annotations

import json
import os
import re
import shlex
from typing import Dict, Iterable, List, NamedTuple, Optional, Tuple

import pc_flags
import pc_mine

# The sanitised wrapper path the committed traces and tools.txt files carry.
WRAPPER_TOKEN = "<repo>/<run>/wrapper/checkpoint"

WRAPPER_VERBS: Tuple[str, ...] = pc_flags.MODEL_FACING_WRAPPER_VERBS
DRIVER_VERBS: Tuple[str, ...] = pc_flags.DRIVER_ONLY_VERBS

LABEL_REQUIRES_APPROVAL = "requires-approval"
LABEL_MULTIPLE_OPERATIONS = "multiple-operations"
LABEL_VARIABLE = "variable"

_LABEL_PREFIXES = (
    ("This command requires approval", LABEL_REQUIRES_APPROVAL),
    ("This Bash command contains multiple operations", LABEL_MULTIPLE_OPERATIONS),
    ("A variable in this command can't be checked", LABEL_VARIABLE),
)

GIT_STATUS_GLOBAL = "git --no-optional-locks status"
_EVIDENCE = ("tests", "evidence")
# The corpus is the committed publication evidence only. A new baseline is judged by its own run and a rerun folder
# next to it is never loaded here, so filing one cannot change the measured corpus counts (finding C5).
CORPUS_FOLDER = "publication-2026-10-20"
_REPLAY_CASES = ("tests", "harness", "replay-cases.json")

_ASCII_WS = " \t\r\n\f\v"
_WORD = re.compile(r"([^ \t\r\n\f\v]+)[ \t\r\n\f\v]*(.*)\Z", re.S)
_RULE = re.compile(r"\ABash\((.*)\)\Z", re.S)
_DURATION = re.compile(r"[0-9]+(\.[0-9]+)?[smhd]?\Z", re.A)
_INTEGER = re.compile(r"-?[0-9]+\Z", re.A)


class Decision(NamedTuple):
    """The answer of is_allowed: whether the command is allowed and a short reason."""

    allowed: bool
    reason: str


# ------------------------------------------------------------------- matching


def _separator_at(command: str, index: int) -> str:
    """The separator that starts at index outside quotes, or an empty string."""
    ch = command[index]
    pair = command[index:index + 2]
    if ch in "\n;":
        return ch
    if pair in ("&&", "||", "|&"):
        return pair
    if ch == "|":
        return ch
    if ch == "&":
        before = command[index - 1] if index > 0 else ""
        after = command[index + 1] if index + 1 < len(command) else ""
        if before in ("<", ">") or after == ">":
            return ""  # a redirection such as 2>&1, >&2 or &>file
        return ch
    return ""


def split_compound(command: str) -> List[str]:
    """Split a command into its parts on the documented separators, outside quotes."""
    parts: List[str] = []
    buf: List[str] = []
    quote = ""
    index = 0
    size = len(command)

    def flush() -> None:
        part = "".join(buf).strip(_ASCII_WS)
        del buf[:]
        if part:
            parts.append(part)

    while index < size:
        ch = command[index]
        if quote == "'":
            buf.append(ch)
            if ch == "'":
                quote = ""
            index += 1
            continue
        if quote == '"':
            buf.append(ch)
            if ch == "\\" and index + 1 < size:
                buf.append(command[index + 1])
                index += 2
                continue
            if ch == '"':
                quote = ""
            index += 1
            continue
        if ch == "\\" and index + 1 < size:
            buf.append(ch)
            buf.append(command[index + 1])
            index += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            index += 1
            continue
        separator = _separator_at(command, index)
        if separator:
            flush()
            index += len(separator)
            continue
        buf.append(ch)
        index += 1
    flush()
    return parts


def has_expansion(part: str) -> bool:
    """True when a dollar sign or a backtick appears outside single quotes and escapes."""
    quote = ""
    index = 0
    size = len(part)
    while index < size:
        ch = part[index]
        if quote == "'":
            if ch == "'":
                quote = ""
            index += 1
            continue
        if ch == "\\" and index + 1 < size:
            index += 2
            continue
        if quote == '"':
            if ch == '"':
                quote = ""
            elif ch in ("$", "`"):
                return True
            index += 1
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch in ("$", "`"):
            return True
        index += 1
    return False


def _next_word(text: str) -> Tuple[Optional[str], str]:
    match = _WORD.match(text)
    if match is None:
        return None, ""
    return match.group(1), match.group(2)


def _strip_one(text: str) -> Optional[str]:
    """The text after one leading wrapper, or None when no documented wrapper applies."""
    head, rest = _next_word(text)
    if head is None:
        return None
    if head in ("nohup", "command", "builtin", "noglob"):
        return rest
    if head == "time":
        word, after = _next_word(rest)
        return after if word == "-p" else rest
    if head == "nice":
        word, after = _next_word(rest)
        if word == "-n":
            number, tail = _next_word(after)
            return tail if number is not None and _INTEGER.match(number) else None
        if word is not None and _INTEGER.match(word) and word.startswith("-"):
            return after
        return rest
    if head == "timeout":
        remaining = rest
        while True:
            word, after = _next_word(remaining)
            if word is None:
                return None
            if word in ("-k", "-s", "--kill-after", "--signal"):
                _, after = _next_word(after)
                remaining = after
                continue
            if word.startswith("-"):
                remaining = after
                continue
            return after if _DURATION.match(word) else None
    if head == "stdbuf":
        remaining = rest
        consumed = False
        while True:
            word, after = _next_word(remaining)
            if word is None or not word.startswith("-"):
                break
            if word in ("-i", "-o", "-e"):
                _, after = _next_word(after)
            remaining = after
            consumed = True
        return remaining if consumed else None
    return None


def strip_wrappers(part: str) -> str:
    """Remove leading timeout, time, nice, nohup, stdbuf, command, builtin and noglob words."""
    current = part.strip(_ASCII_WS)
    while True:
        stripped = _strip_one(current)
        if stripped is None:
            return current
        current = stripped.strip(_ASCII_WS)


def rule_matches(rule: str, part: str) -> bool:
    """True when one Bash(...) rule matches one command part, exactly as documented."""
    match = _RULE.match(rule)
    if match is None:
        return False
    pattern = match.group(1)
    if pattern.endswith(":*") or pattern.endswith(" *"):
        prefix = pattern[:-2]
        if prefix == "":
            return False
        return part == prefix or part.startswith(prefix + " ")
    return part == pattern


def is_allowed(command: str, rules: Iterable[str]) -> Decision:
    """Allowed only when every part of the command matches some rule and has no expansion."""
    rule_list = tuple(rules)
    if not isinstance(command, str):
        return Decision(False, "command is not text")
    parts = split_compound(command)
    if not parts:
        return Decision(False, "empty command")
    if not rule_list:
        return Decision(False, "no rules")
    for part in parts:
        if has_expansion(part):
            return Decision(False, "variable in command")
        stripped = strip_wrappers(part)
        if not any(rule_matches(rule, stripped) for rule in rule_list):
            first, _ = _next_word(part)
            return Decision(False, "no rule matches: %s" % first)
    return Decision(True, "every part matches a rule")


# ------------------------------------------------------------ evidence loaders


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _split_rules(text: str) -> Tuple[str, ...]:
    """Split a tools.txt line on commas that sit outside parentheses."""
    rules: List[str] = []
    depth = 0
    buf: List[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            rules.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    rules.append("".join(buf).strip())
    return tuple(rule for rule in rules if rule)


def row_rules(folder: str) -> Optional[Tuple[str, ...]]:
    """The rules in a folder's tools.txt, in file order, or None when it has none."""
    path = os.path.join(folder, "tools.txt")
    if not os.path.isfile(path):
        return None
    return _split_rules(_read_text(path).strip())


def _label(first_line: str) -> Optional[str]:
    for prefix, label in _LABEL_PREFIXES:
        if first_line.startswith(prefix):
            return label
    return None


def load_trace_calls(repo_root: str, evidence_folder: str = CORPUS_FOLDER) -> List[Dict[str, object]]:
    """Every Bash call of every full trace under tests/evidence/<evidence_folder>, with its row's rules.

    The default folder is the committed publication evidence (CORPUS_FOLDER); a rerun baseline filed next to it is
    not part of the corpus. Traces sort by path bytes; a trace whose folder holds no tools.txt is skipped. Each
    record has folder, trace, number, command, refusal (the trace's own flag), first_line
    (the first line of the recorded reply), label (a rule-class label or None) and rules.
    """
    evidence = os.path.join(repo_root, *_EVIDENCE, evidence_folder)
    paths: List[str] = []
    for current, dirs, files in os.walk(evidence):
        dirs.sort(key=os.fsencode)
        for name in files:
            if name.endswith("full-trace.md"):
                paths.append(os.path.join(current, name))
    paths.sort(key=os.fsencode)
    records: List[Dict[str, object]] = []
    for path in paths:
        folder = os.path.dirname(path)
        rules = row_rules(folder)
        if rules is None:
            continue
        for call in pc_mine.parse_trace(_read_text(path)):
            first_line = str(call["result"]).split("\n", 1)[0]
            records.append(
                {
                    "folder": os.path.relpath(folder, repo_root).replace(os.sep, "/"),
                    "trace": os.path.relpath(path, repo_root).replace(os.sep, "/"),
                    "number": call["number"],
                    "command": call["command"],
                    "refusal": call["refusal"],
                    "first_line": first_line,
                    "label": _label(first_line),
                    "rules": rules,
                }
            )
    return records


def refusal_corpus(calls: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    """The calls refused for a rule reason, picked by the label on each record."""
    return [call for call in calls if call["label"] is not None]


def substitute_wrapper(text: str, wrapper_path: str) -> str:
    """Replace the sanitised wrapper token in text with a real absolute wrapper path."""
    return text.replace(WRAPPER_TOKEN, wrapper_path)


def _wrapper_commands_from_replay(repo_root: str) -> List[str]:
    data = json.loads(_read_text(os.path.join(repo_root, *_REPLAY_CASES)))
    commands = []
    for case in data["cases"]:
        for call in case["calls"]:
            words = [WRAPPER_TOKEN] + [shlex.quote(arg) for arg in call["argv"]]
            commands.append(" ".join(words))
    return commands


def canonical_commands(repo_root: str) -> List[str]:
    """The skill's exact single-part commands, taken from the committed traces and logs.

    From the traces: calls that were not refused and whose one part starts with the wrapper
    token, starts with the git status command carrying the global no-optional-locks option,
    or is pwd -P. From replay-cases.json: every wrapper argv, rendered with the wrapper token.
    The list is sorted and holds each command once.
    """
    found = set(_wrapper_commands_from_replay(repo_root))
    for call in load_trace_calls(repo_root):
        if call["refusal"] or call["label"] is not None:
            continue
        parts = split_compound(str(call["command"]))
        if len(parts) != 1 or has_expansion(parts[0]):
            continue
        part = parts[0]
        first, _ = _next_word(part)
        if (
            first == WRAPPER_TOKEN
            or part == GIT_STATUS_GLOBAL
            or part.startswith(GIT_STATUS_GLOBAL + " ")
            or part == "pwd -P"
        ):
            found.add(part)
    return sorted(found)


# ------------------------------------------------------ the indirect launch route

_LAUNCH_WORDS = ("env", "python3", "awk", "find")


def _launch_rules() -> Tuple[str, ...]:
    chosen = []
    for rule in pc_flags.BASELINE_ALLOWED_TOOLS:
        match = re.match(r"^Bash\(([^ :)]+)", rule)
        if match is not None and match.group(1) in _LAUNCH_WORDS:
            chosen.append(rule)
    return tuple(chosen)


INDIRECT_LAUNCH_NOTE = (
    "STUB-06 holds in two layers. Layer 1: no rule the harness builds names or prefix-matches "
    "wrapper bind, create or init, so the model-facing allowlist never reaches them directly. "
    "Layer 2: the committed baseline, kept verbatim so reruns stay comparable, holds rules that "
    "can start another program (env, python3 -c, awk, find); under the matcher an env-prefixed "
    "wrapper bind is allowed by the env rule, so the allowlist alone cannot close that route. "
    "The control is the wrapper itself: checkpoint-wrapper refuses bind, create and init with "
    "exit 71 whatever launched it, and the driver builds state through the stub directly."
)

# The baseline rules whose command word can start another program, read from the baseline at
# import time. They are the route INDIRECT_LAUNCH_NOTE records, not a list of rules to remove:
# narrowing the baseline would start a new baseline (a later phase's per-row decision).
INDIRECT_LAUNCH_RULES: Tuple[str, ...] = _launch_rules()
