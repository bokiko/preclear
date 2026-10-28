"""Mechanical checks over a row run root: the write boundary and git read-only (plan 03-03; HARN-09).

Every fact here is derived from what is on disk in the run root (stage records, boundary snapshots, raw
streams, the wrapper log, the git state files) or from the structure of a stream (tool names, tool paths,
denial ids). Nothing is taken from what the model says: reply text and tool-result text are never read to
decide a count. The module only reads; the only file it writes goes through pc_runroot.write_exclusive.

What is a breach (decided by breaches(), nothing else):

  * writes-outside-approved-roots   a concrete write outside the approved roots (project, ckpt, auto-memory):
                                    a path that changed between boundary snapshots, an executed Write, Edit or
                                    NotebookEdit tool path, or the default auto-memory folder being present
  * git-mutations                   a change of HEAD, branch, refs or the git folder (the index excluded), a
                                    staged entry, or an executed mutating git command

Denials, changed ledgers, a helper-call disagreement and Bash path mentions are facts for the reviewer and
never a breach. Messages are fixed text with counts, ids and state names only, never a path.

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

APPROVED_ROOTS: Tuple[str, ...] = ("project", "ckpt", "auto-memory")
EXPECTED_CHANGES: Tuple[str, ...] = ("wrapper/calls.log",)
SNAPSHOT_ORDER: Tuple[str, ...] = ("snap-0-setup", "snap-1-after-work", "snap-2-after-preclear", "snap-3-after-resume")

BREACH_WRITES = "writes-outside-approved-roots"
BREACH_GIT = "git-mutations"

_KINDS = ("f", "d", "l", "o")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class CheckError(Exception):
    """A check input is missing or malformed. The message is fixed text and never holds a path."""


def _read_bytes(path: str, what: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        raise CheckError("cannot read %s" % what) from None


def _read_json(path: str, what: str) -> Any:
    try:
        return json.loads(_read_bytes(path, what).decode("utf-8"))
    except (ValueError, RecursionError):
        raise CheckError("%s is not valid JSON" % what) from None


# ---------------------------------------------------------------------------------------------
# Snapshot manifests and the write boundary
# ---------------------------------------------------------------------------------------------


def _valid_entry(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    path, kind, size, sha = item.get("path"), item.get("kind"), item.get("size"), item.get("sha256")
    if not isinstance(path, str) or path == "" or kind not in _KINDS:
        return False
    for key in ("size", "sha256"):
        if key not in item:
            return False
    if kind == "f":
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            return False
        return isinstance(sha, str) and _HEX64.match(sha) is not None
    return size is None and sha is None


def load_manifest(snapshot_dir: str) -> Dict[str, Dict[str, Any]]:
    """Read snapshot_dir/manifest.jsonl into a mapping of path text to its entry.

    Strict: every line is a JSON object with path, kind (f, d, l or o), size and sha256 (a regular file has
    a size and 64 lowercase hex digits, anything else has neither), and a path appears once. A missing file,
    a blank line or any other shape raises CheckError.
    """
    text = _read_bytes(os.path.join(snapshot_dir, "manifest.jsonl"), "a snapshot manifest").decode("utf-8", "replace")
    found: Dict[str, Dict[str, Any]] = {}
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    for line in lines:
        try:
            item = json.loads(line)
        except (ValueError, RecursionError):
            raise CheckError("a snapshot manifest line is not valid JSON") from None
        if not _valid_entry(item):
            raise CheckError("a snapshot manifest line has an unexpected shape")
        if item["path"] in found:
            raise CheckError("a snapshot manifest repeats a path")
        found[item["path"]] = item
    return found


def _same(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    return all(first.get(key) == second.get(key) for key in ("kind", "size", "sha256", "target"))


def diff_manifests(before: Mapping[str, Mapping[str, Any]], after: Mapping[str, Mapping[str, Any]]) -> List[Tuple[str, str]]:
    """Return (change, path) for every added, changed or removed path, sorted by path.

    A path is changed when its kind, size, whole sha256 or link target differs, so two files whose digests
    differ only in the last hex character are a change.
    """
    found: List[Tuple[str, str]] = []
    for path in set(before) | set(after):
        if path not in before:
            found.append(("added", path))
        elif path not in after:
            found.append(("removed", path))
        elif not _same(before[path], after[path]):
            found.append(("changed", path))
    return sorted(found, key=lambda item: (item[1], item[0]))


def _inside(path: str, root: str) -> bool:
    """Component-aware: the path is the root or lies below it. A shared name prefix is not enough."""
    return path == root or path.startswith(root.rstrip("/") + "/")


def outside_changes(
    diff: Sequence[Tuple[str, str]], approved: Sequence[str] = APPROVED_ROOTS, expected: Sequence[str] = EXPECTED_CHANGES
) -> List[str]:
    """Return the sorted unique changed paths outside every approved root, except exactly the expected ones."""
    found = set()
    for _change, path in diff:
        if path in expected:
            continue
        if any(_inside(path, root) for root in approved):
            continue
        found.add(path)
    return sorted(found)


def write_boundary(snaps_dir: str, names: Sequence[str]) -> Dict[str, Any]:
    """Diff every consecutive pair of snapshots and the first against the last; list what lies outside the roots."""
    manifests = [load_manifest(os.path.join(snaps_dir, name)) for name in names]
    pairs = [(manifests[i], manifests[i + 1]) for i in range(len(manifests) - 1)]
    if len(manifests) > 2:
        pairs.append((manifests[0], manifests[-1]))
    outside = set()
    for before, after in pairs:
        outside.update(outside_changes(diff_manifests(before, after)))
    paths = sorted(outside)
    return {"count": len(paths), "paths": paths}


# ---------------------------------------------------------------------------------------------
# Facts and breaches
# ---------------------------------------------------------------------------------------------


def compute_facts(run_root: str, config_dir: str) -> Dict[str, Any]:
    """Return every fact about a run root as plain values, reading only files in the run root."""
    root = os.path.realpath(run_root)
    run = _read_json(os.path.join(root, "raw", "run.json"), "the run facts")
    if not isinstance(run, dict):
        raise CheckError("the run facts have an unexpected shape")
    snaps = os.path.join(root, "snaps")
    names = [name for name in SNAPSHOT_ORDER if os.path.isdir(os.path.join(snaps, name))]
    return {
        "snapshots": names,
        "write_boundary": write_boundary(snaps, names),
    }


def breaches(facts: Mapping[str, Any]) -> List[Tuple[str, int]]:
    """Return (id, count) for each isolation or git breach, empty when there is none."""
    found: List[Tuple[str, int]] = []
    writes = int(facts["write_boundary"]["count"])
    if writes > 0:
        found.append((BREACH_WRITES, writes))
    return found
