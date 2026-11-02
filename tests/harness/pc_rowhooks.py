"""Between-stage hooks and their finalizers (plan 04-05; RERUN-02; D-04, D-08).

A row may restrict part of its project between two stages, so that the next stage meets a read-only plan file. The
restriction is done by the harness itself, in the harness process, never by the model and never through an allowlist;
the model's own chmod and touch are counted afterwards (pc_checks.program_counts) and are never prevented or hidden.

What is here:

  * HOOKS             hook id to the function that applies it (restrict-plan-444 sets mode 444 on the plan file)
  * HOOK_SNAPSHOTS    hook id to the extra snapshot the engine takes right after the hook (snap-1b-after-restriction)
  * FINALIZER_OF      hook id to the finalizer id that undoes it; FINALIZERS maps that id to the function
                      (restore-plan-644 sets the plan file back to mode 644)
  * TARGETS           hook id to the table of things it may touch: (path relative to the project, "file" or "dir")
  * plan_boundaries   the boundaries a spec will take, in execution order, as (boundary name, snapshot name) pairs;
                      the engine records them in raw/boundaries.json at setup
  * run_after_stage   after a stage: apply the hooks the spec names for it, then take the hook's snapshot, write
                      perms.txt into it, capture the git state and the guard under the hook boundary name
  * run_finalizers    undo every restriction that was applied, with the same checks as the hook
  * write_perms       perms.txt: one `<path relative to the project> <octal mode>` line per target, sorted, from the
                      file's own status and never from an ls listing, so no owner, group, date, size or login name
                      can reach a filed file (T-04-21)
  * HookRun           what the engine keeps of one run: which hooks were applied and which were restored

Safety (T-04-19). Before it touches anything a hook or finalizer checks the target against its own table: the project
folder is a real folder directly inside the run root, no part of the path below it is a symbolic link, the last part is
opened without following a link and is a regular file (or the folder the table names) owned by the same user with one
name only, and its real path lies inside the project folder. A target that fails any check is a HookRefused with fixed
text and nothing is changed; the engine ends the row as a stop with reason breach (exit 11). The mode is set on the
opened descriptor, so a link planted between the check and the change cannot redirect it. Nothing here deletes,
renames, moves or truncates anything; perms.txt and the boundary list are created exclusively.

Standard library only, Python 3.9 floor.
"""
from __future__ import annotations

import os
import stat
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pc_checks
import pc_rows
import pc_rowseeds
import pc_runroot

KIND_FILE = "file"
KIND_DIR = "dir"

HOOK_RESTRICT_PLAN = "restrict-plan-444"
FINALIZER_RESTORE_PLAN = "restore-plan-644"

MODE_RESTRICTED = 0o444
MODE_RESTORED = 0o644

PLAN_RELATIVE = "thoughts/plans/" + pc_rowseeds.PLAN_NAME
PERMS_NAME = "perms.txt"

MESSAGE_REFUSED = "the hook target is not a plain file inside the project; nothing was changed"
MESSAGE_CHMOD = "the hook could not set the mode of its target; nothing more was changed"
MESSAGE_UNKNOWN = "the row names a hook that is not known"

# The table of what each hook may touch: path relative to the project, and whether it is a regular file or a folder.
TARGETS: Dict[str, Tuple[Tuple[str, str], ...]] = {
    HOOK_RESTRICT_PLAN: ((PLAN_RELATIVE, KIND_FILE),),
}
# The extra snapshot each hook makes the engine take (its name sorts between the stage's snapshot and the next one's).
HOOK_SNAPSHOTS: Dict[str, str] = {HOOK_RESTRICT_PLAN: "snap-1b-after-restriction"}
# The finalizer that undoes each hook.
FINALIZER_OF: Dict[str, str] = {HOOK_RESTRICT_PLAN: FINALIZER_RESTORE_PLAN}


class HookRefused(Exception):
    """A hook or finalizer refused its target. The message is fixed text and never holds a path."""


class HookRun(object):
    """What the engine keeps of one run: the hook ids applied so far and the finalizers already run."""

    def __init__(self) -> None:
        self.applied: List[str] = []
        self.restored: List[str] = []

    def pending(self) -> List[str]:
        """The hooks applied and not yet restored, in the order they were applied."""
        return [hook for hook in self.applied if hook not in self.restored]


def boundary_name(stage_name: str, hook_id: str) -> str:
    """The boundary name of a hook: the stage it follows and the hook id (s1-restrict-plan-444)."""
    return "%s-%s" % (stage_name, hook_id)


def known_hook(hook_id: Any) -> bool:
    return isinstance(hook_id, str) and hook_id in HOOKS and hook_id in HOOK_SNAPSHOTS and hook_id in TARGETS


def hooks_of(spec: pc_rows.RowSpec, stage_name: Optional[str] = None) -> List[str]:
    """The hook ids a spec names, in order, for one stage when stage_name is given; an unknown id is a ValueError."""
    found: List[str] = []
    for pair in spec.hooks:
        stage, hook = pair
        if not known_hook(hook):
            raise ValueError(MESSAGE_UNKNOWN)
        if stage_name is None or stage == stage_name:
            found.append(hook)
    return found


def plan_boundaries(spec: pc_rows.RowSpec) -> List[Tuple[str, str]]:
    """The boundaries a spec will take, in execution order, as (boundary name, snapshot name) pairs.

    setup first, then each stage (its name and its snapshot name), each followed by the boundaries of the hooks the
    spec names for that stage. A row that stops early simply has a prefix of this list on disk.
    """
    planned: List[Tuple[str, str]] = [pc_checks.LEGACY_BOUNDARIES[0]]
    stage_names = [stage.name for stage in spec.stages]
    for stage_name, hook in spec.hooks:
        if stage_name not in stage_names:
            raise ValueError(MESSAGE_UNKNOWN)
        if not known_hook(hook):
            raise ValueError(MESSAGE_UNKNOWN)
    for stage in spec.stages:
        planned.append((stage.name, "snap-%s-after-%s" % (stage.name[1:], stage.kind)))
        for hook in hooks_of(spec, stage.name):
            planned.append((boundary_name(stage.name, hook), HOOK_SNAPSHOTS[hook]))
    return planned


def write_boundary_list(paths: Mapping[str, Optional[str]], spec: pc_rows.RowSpec) -> None:
    """Create raw/boundaries.json exclusively with the boundaries the spec will take (the engine calls this at setup)."""
    pc_checks.write_boundaries(str(paths["raw"]), plan_boundaries(spec))


# ---------------------------------------------------------------------------------------------
# The checked target
# ---------------------------------------------------------------------------------------------


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _table_entry(relative: str, kind: str) -> List[str]:
    parts = relative.split("/")
    if kind not in (KIND_FILE, KIND_DIR) or not parts or any(part in ("", ".", "..") for part in parts):
        raise HookRefused(MESSAGE_REFUSED)
    return parts


def _open_target(paths: Mapping[str, Optional[str]], relative: str, kind: str) -> int:
    """Check one table entry and return a descriptor opened on it without following a link; the caller closes it.

    The checks, in order: the project is a real folder directly inside the real run root; every part of the path
    below the project is a real folder (a link anywhere in the path is a refusal); the last part opens without
    following a link and is a regular file (KIND_FILE) or a folder (KIND_DIR) of the running user with one name only
    (a second name for the same file would let a mode change reach a file elsewhere); and the real path of what was
    opened lies inside the real project folder. Anything else is HookRefused and nothing was changed.
    """
    parts = _table_entry(relative, kind)
    run_root = os.path.realpath(str(paths["run_root"]))
    project = os.path.join(run_root, "project")
    try:
        project_status = os.lstat(project)
    except OSError:
        raise HookRefused(MESSAGE_REFUSED) from None
    if not stat.S_ISDIR(project_status.st_mode) or os.path.realpath(project) != project:
        raise HookRefused(MESSAGE_REFUSED)
    current = project
    for part in parts[:-1]:
        current = os.path.join(current, part)
        try:
            status = os.lstat(current)
        except OSError:
            raise HookRefused(MESSAGE_REFUSED) from None
        if not stat.S_ISDIR(status.st_mode):
            raise HookRefused(MESSAGE_REFUSED)
    full = os.path.join(current, parts[-1])
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    if kind == KIND_DIR:
        flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(full, flags)
    except OSError:
        raise HookRefused(MESSAGE_REFUSED) from None
    try:
        status = os.fstat(descriptor)
        right_kind = stat.S_ISREG(status.st_mode) if kind == KIND_FILE else stat.S_ISDIR(status.st_mode)
        if not right_kind or status.st_uid != os.getuid():
            raise HookRefused(MESSAGE_REFUSED)
        if kind == KIND_FILE and status.st_nlink != 1:
            raise HookRefused(MESSAGE_REFUSED)
        if not _inside(os.path.realpath(full), project):
            raise HookRefused(MESSAGE_REFUSED)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _set_modes(paths: Mapping[str, Optional[str]], hook_id: str, mode: int) -> None:
    """Check every target of the hook before the first change, then set the mode on each opened descriptor."""
    if hook_id not in TARGETS:
        raise HookRefused(MESSAGE_UNKNOWN)
    opened: List[int] = []
    try:
        for relative, kind in TARGETS[hook_id]:
            opened.append(_open_target(paths, relative, kind))
        for descriptor in opened:
            try:
                os.fchmod(descriptor, mode)
            except OSError:
                raise HookRefused(MESSAGE_CHMOD) from None
    finally:
        for descriptor in opened:
            os.close(descriptor)


def restrict_plan_444(ctx: Any, paths: Mapping[str, Optional[str]], spec: Any) -> None:
    """Set mode 444 on the plan file (and nothing else) after its checks."""
    _set_modes(paths, HOOK_RESTRICT_PLAN, MODE_RESTRICTED)


def restore_plan_644(ctx: Any, paths: Mapping[str, Optional[str]], spec: Any) -> None:
    """Set the plan file back to mode 644 with the same checks as the restriction."""
    _set_modes(paths, HOOK_RESTRICT_PLAN, MODE_RESTORED)


HOOKS: Dict[str, Any] = {HOOK_RESTRICT_PLAN: restrict_plan_444}
FINALIZERS: Dict[str, Any] = {FINALIZER_RESTORE_PLAN: restore_plan_644}


# ---------------------------------------------------------------------------------------------
# perms.txt
# ---------------------------------------------------------------------------------------------


def perms_text(paths: Mapping[str, Optional[str]], targets: Sequence[Tuple[str, str]]) -> bytes:
    """The perms.txt bytes for a target table: sorted `<path relative to the project> <octal mode>` lines.

    The mode is read from the opened target's own status, after the target passed the same checks as a hook (a target
    that fails them is HookRefused). Only the permission bits are written, as at least three octal digits; there is no
    owner, group, date or size column and no login name.
    """
    lines: List[str] = []
    for relative, kind in sorted(targets):
        descriptor = _open_target(paths, relative, kind)
        try:
            mode = stat.S_IMODE(os.fstat(descriptor).st_mode)
        finally:
            os.close(descriptor)
        lines.append("%s %03o" % (relative, mode))
    return "".join(line + "\n" for line in lines).encode("utf-8")


def write_perms(paths: Mapping[str, Optional[str]], targets: Sequence[Tuple[str, str]], snapshot: str) -> None:
    """Create perms.txt exclusively inside the snapshot folder of the given name (see perms_text)."""
    if snapshot not in HOOK_SNAPSHOTS.values():
        raise HookRefused(MESSAGE_UNKNOWN)
    data = perms_text(paths, targets)
    pc_runroot.write_exclusive(os.path.join(str(paths["snaps"]), snapshot, PERMS_NAME), data, 0o600)


# ---------------------------------------------------------------------------------------------
# The engine's calls
# ---------------------------------------------------------------------------------------------


def run_after_stage(
    ctx: Any,
    paths: Mapping[str, Optional[str]],
    spec: pc_rows.RowSpec,
    stage_name: str,
    run: Optional[HookRun] = None,
) -> List[str]:
    """Apply the hooks the spec names for a stage and take their boundaries; return the snapshot names created.

    The engine calls this after the stage's own snapshot, boundary state and guard have been written and its checks
    have passed. For each hook: the hook function runs first (HookRefused ends the row), then the extra snapshot is
    taken through pc_row1.take_snapshot with the held setup pin, perms.txt is written into it from the target table,
    the git state is captured under the hook boundary name and the guard last, so the next stage is compared with this
    boundary. The hook is recorded in run before it runs, so a hook that fails half way is still restored.
    """
    import pc_row1  # imported late: pc_row1 imports this module

    created: List[str] = []
    for hook in hooks_of(spec, stage_name):
        if run is not None:
            run.applied.append(hook)
        HOOKS[hook](ctx, paths, spec)
        snapshot = HOOK_SNAPSHOTS[hook]
        vcs = pc_row1._git_executable(ctx.env)
        pc_row1.take_snapshot(paths, snapshot, vcs, pin=ctx.setup_pin)
        write_perms(paths, TARGETS[hook], snapshot)
        name = boundary_name(stage_name, hook)
        pc_checks.capture_boundary_state(paths, name, vcs, ctx.setup_pin)
        pc_checks.capture_guard(paths, name)
        created.append(snapshot)
    return created


def run_finalizers(
    ctx: Any,
    paths: Mapping[str, Optional[str]],
    spec: pc_rows.RowSpec,
    run: Optional[HookRun] = None,
) -> List[str]:
    """Run the finalizer of every hook that was applied (every hook the spec names when run is None); return their ids.

    Idempotent: a finalizer that already ran for this run is not run again. A refusal is HookRefused after the
    remaining finalizers have been tried, so one refused target does not leave another restriction in place.
    """
    if run is None:
        hooks = hooks_of(spec)
    else:
        hooks = run.pending()
    done: List[str] = []
    refused = False
    for hook in hooks:
        finalizer = FINALIZER_OF.get(hook)
        if finalizer is None or finalizer not in FINALIZERS:
            refused = True
            continue
        try:
            FINALIZERS[finalizer](ctx, paths, spec)
        except HookRefused:
            refused = True
            if run is not None:
                run.restored.append(hook)
            continue
        if run is not None:
            run.restored.append(hook)
        done.append(finalizer)
    if refused:
        raise HookRefused(MESSAGE_REFUSED)
    return done
