"""Zero-token tests for the mechanical checks (plan 03-03; HARN-09, D-03, D-09).

No test starts a real claude: the only claude executed is the scripted fake written by pc_testutil. Every
folder comes from tempfile or RowRig and is never deleted. pc_checks is imported inside each test, so a
missing module is one error per test and not one load failure of the file. Assertion labels are fixed text.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
import unittest.mock

import pc_exitcodes
import pc_row1
import pc_testutil

SNAP_SETUP = "snap-0-setup"
SNAP_ONE = "snap-1-after-work"
SNAP_TWO = "snap-2-after-preclear"
SNAP_THREE = "snap-3-after-resume"


def checks():
    import pc_checks

    return pc_checks


def digest(last: str = "0") -> str:
    return "a" * 63 + last


def file_entry(path: str, sha: str = None, size: int = 3) -> dict:
    return {"path": path, "kind": "f", "size": size, "sha256": sha if sha is not None else digest(), "target": None}


def dir_entry(path: str) -> dict:
    return {"path": path, "kind": "d", "size": None, "sha256": None, "target": None}


def write_manifest(folder: str, entries) -> str:
    """Create folder and a manifest.jsonl in it from entry mappings; return folder."""
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "manifest.jsonl"), "w", encoding="utf-8") as handle:
        for item in entries:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    return folder


def mapping(entries) -> dict:
    return dict((item["path"], item) for item in entries)


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class Run(object):
    """A rig, a context and the outcome of one run_row call."""

    def __init__(self, stages=None, **config) -> None:
        self.rig = pc_testutil.RowRig(stages=stages, **config)
        self.ctx = self.rig.context()
        self.outcome = pc_row1.run_row(self.ctx)

    @property
    def run_root(self) -> str:
        names = os.listdir(self.ctx.runs_root)
        assert len(names) == 1, names
        return os.path.join(self.ctx.runs_root, names[0])

    def facts(self):
        return checks().compute_facts(self.run_root, self.ctx.config_dir)


class BoundaryTests(unittest.TestCase):
    def test_load_manifest_reads_a_snapshot_and_refuses_a_missing_or_malformed_file(self) -> None:
        c = checks()
        base = tempfile.mkdtemp(prefix="pc-checks-")
        good = write_manifest(os.path.join(base, "good"), [dir_entry("project"), file_entry("project/a", digest("7"))])
        loaded = c.load_manifest(good)
        self.assertEqual(sorted(loaded), ["project", "project/a"], "both paths are loaded")
        self.assertEqual(loaded["project/a"]["kind"], "f", "the kind is kept")
        self.assertEqual(loaded["project/a"]["size"], 3, "the size is kept")
        self.assertEqual(loaded["project/a"]["sha256"], digest("7"), "the whole digest is kept")
        self.assertEqual(loaded["project"]["kind"], "d", "a directory entry is kept")
        with self.assertRaises(c.CheckError, msg="a missing snapshot folder is refused"):
            c.load_manifest(os.path.join(base, "no-such-folder"))
        bad_lines = [
            "not json at all",
            "[1, 2]",
            json.dumps({"path": "x", "kind": "f", "size": 1}),
            json.dumps({"path": "x", "kind": "f", "size": 1, "sha256": "abc"}),
            json.dumps({"path": "x", "kind": "f", "size": 1, "sha256": "A" * 64}),
            json.dumps({"path": "x", "kind": "q", "size": None, "sha256": None}),
            json.dumps({"path": 7, "kind": "d", "size": None, "sha256": None}),
        ]
        for number, line in enumerate(bad_lines):
            folder = os.path.join(base, "bad%d" % number)
            os.makedirs(folder)
            with open(os.path.join(folder, "manifest.jsonl"), "w", encoding="utf-8") as handle:
                handle.write(line + "\n")
            with self.assertRaises(c.CheckError, msg="a malformed line is refused (case %d)" % number):
                c.load_manifest(folder)
        twice = os.path.join(base, "twice")
        write_manifest(twice, [dir_entry("project"), dir_entry("project")])
        with self.assertRaises(c.CheckError, msg="a repeated path is refused"):
            c.load_manifest(twice)

    def test_diff_lists_added_changed_and_removed_paths(self) -> None:
        c = checks()
        before = mapping([file_entry("a"), file_entry("b"), file_entry("c"), dir_entry("d")])
        after = mapping([file_entry("a"), file_entry("b", digest("1")), file_entry("e"), dir_entry("d")])
        found = c.diff_manifests(before, after)
        self.assertEqual(sorted(found), [("added", "e"), ("changed", "b"), ("removed", "c")], "one entry per change")

    def test_a_digest_that_differs_only_in_the_last_character_is_a_change(self) -> None:
        c = checks()
        before = mapping([file_entry("x", digest("0"))])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("1"))])), [("changed", "x")])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("0"))])), [], "same digest, no change")

    def test_a_change_of_kind_or_size_is_a_change(self) -> None:
        c = checks()
        before = mapping([file_entry("x", digest("0"), 3)])
        self.assertEqual(c.diff_manifests(before, mapping([file_entry("x", digest("0"), 4)])), [("changed", "x")])
        self.assertEqual(c.diff_manifests(before, mapping([dir_entry("x")])), [("changed", "x")])

    def test_the_approved_roots_and_the_expected_change_are_the_documented_ones(self) -> None:
        c = checks()
        self.assertEqual(tuple(c.APPROVED_ROOTS), ("project", "ckpt", "auto-memory"))
        self.assertEqual(tuple(c.EXPECTED_CHANGES), ("wrapper/calls.log",))

    def test_the_root_match_is_component_aware(self) -> None:
        c = checks()
        inside = ["project/x", "ckpt/ledgers/x", "auto-memory/y", "project", "ckpt", "auto-memory"]
        outside = [
            "project-other/x",
            "project.bak",
            "ckpt2/x",
            "auto-memory-old/x",
            "wrapper/py",
            "wrapper/stub",
            "settings.json",
            "newtop/file",
            "newtop",
        ]
        for path in inside:
            found = c.outside_changes([("added", path)], c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
            self.assertEqual(found, [], "inside the approved roots: %s" % path)
        for path in outside:
            found = c.outside_changes([("added", path)], c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
            self.assertEqual(found, [path], "outside the approved roots: %s" % path)

    def test_a_changed_call_log_is_expected_and_a_removed_outside_file_is_listed(self) -> None:
        c = checks()
        diff = [("changed", "wrapper/calls.log"), ("removed", "stray.txt"), ("changed", "wrapper/checkpoint")]
        found = c.outside_changes(diff, c.APPROVED_ROOTS, c.EXPECTED_CHANGES)
        self.assertEqual(found, ["stray.txt", "wrapper/checkpoint"], "the log is excluded and nothing else is")
        self.assertEqual(c.outside_changes([("removed", "wrapper/calls.log.bak")], c.APPROVED_ROOTS, c.EXPECTED_CHANGES),
                         ["wrapper/calls.log.bak"], "only the exact expected path is excluded")

    def test_write_boundary_diffs_consecutive_pairs_and_first_against_last_and_counts_a_path_once(self) -> None:
        c = checks()
        base = tempfile.mkdtemp(prefix="pc-checks-")
        common = [dir_entry("project"), file_entry("project/a"), file_entry("wrapper/calls.log", digest("0"))]
        write_manifest(os.path.join(base, SNAP_SETUP), common)
        write_manifest(os.path.join(base, SNAP_ONE), common + [file_entry("stray.txt")])
        write_manifest(os.path.join(base, SNAP_TWO), common + [file_entry("stray.txt", digest("9")), file_entry("project/b")])
        found = c.write_boundary(base, [SNAP_SETUP, SNAP_ONE, SNAP_TWO])
        self.assertEqual(found["paths"], ["stray.txt"], "the same path in three pairs is listed once")
        self.assertEqual(found["count"], 1, "and counted once")
        quiet = c.write_boundary(base, [SNAP_SETUP])
        self.assertEqual(quiet["count"], 0, "one snapshot has nothing to compare")
        changed_log = os.path.join(base, "log")
        os.makedirs(changed_log)
        write_manifest(os.path.join(changed_log, SNAP_SETUP), common)
        write_manifest(os.path.join(changed_log, SNAP_ONE),
                       [dir_entry("project"), file_entry("project/a"), file_entry("wrapper/calls.log", digest("5"))])
        self.assertEqual(c.write_boundary(changed_log, [SNAP_SETUP, SNAP_ONE])["count"], 0, "the call log may change")


class TracerTests(unittest.TestCase):
    def test_a_clean_default_run_reports_zero_and_returns_zero(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertEqual(facts["write_boundary"]["count"], 0, "no write outside the approved roots")
        self.assertEqual(checks().breaches(facts), [], "no breach")

    def test_a_seeded_write_outside_the_roots_is_reported_and_ends_the_row_with_11(self) -> None:
        stages = pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1)
        run = Run(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertGreaterEqual(facts["write_boundary"]["count"], 1, "the write is counted")
        self.assertIn("outside.txt", facts["write_boundary"]["paths"], "the path is run-root relative text")
        ids = [name for name, _count in checks().breaches(facts)]
        self.assertIn("writes-outside-approved-roots", ids, "the breach is named")
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: writes outside approved roots: [1-9][0-9]*", "count in text")
        self.assertNotIn("outside.txt", text, "no path in the text")
        self.assertNotIn(run.rig.base, text, "no folder in the text")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s2.stdout")), "the raw bytes stay")
        for name in (SNAP_SETUP, SNAP_ONE, SNAP_TWO):
            self.assertTrue(os.path.isdir(os.path.join(run.run_root, "snaps", name)), "snapshot kept: " + name)
        self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")
        self.assertFalse(os.path.exists(os.path.join(raw, "s3.stdout")), "no third stage output")

    def test_the_facts_are_computed_from_files_alone_and_repeat(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        first = run.facts()
        second = run.facts()
        self.assertEqual(first, second, "the same call gives equal facts")
        self.assertEqual(json.loads(json.dumps(first)), first, "the facts are plain values")


def stream(calls, denied=()):
    """Build a stream by hand: calls is a list of (name, input) and denied lists tool_use ids (t0, t1, ...)."""
    events = [{"type": "system", "subtype": "init", "session_id": "sid"}]
    for number, (name, tool_input) in enumerate(calls):
        events.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t%d" % number, "name": name, "input": tool_input}]}})
    events.append({"type": "result", "subtype": "success", "is_error": False, "session_id": "sid",
                   "permission_denials": [{"tool_use_id": item} for item in denied]})
    return events


def bash(command: str):
    return ("Bash", {"command": command})


def events_of(run: Run, stage: str):
    import pc_stream

    with open(os.path.join(run.run_root, "raw", stage + ".stdout"), "rb") as handle:
        return pc_stream.parse_stream(handle.read())


def real_dirs(prefix: str = "pc-checks-"):
    """Return (run root, project, ckpt, auto-memory, outside) as real folders in a fresh scratch folder."""
    base = os.path.realpath(tempfile.mkdtemp(prefix=prefix))
    run = os.path.join(base, "run")
    folders = [os.path.join(run, name) for name in ("project", "ckpt", "auto-memory")] + [os.path.join(base, "outside")]
    for folder in folders:
        os.makedirs(folder)
    return [run] + folders


class TraceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run, self.project, self.ckpt, self.memory, self.outside = real_dirs()
        self.approved = [self.project, self.ckpt, self.memory]

    def paths(self, calls, denied=()):
        return checks().trace_write_paths(stream(calls, denied), self.project, self.approved)

    def test_write_edit_and_notebook_paths_outside_the_roots_are_listed_as_run_relative_or_a_fixed_token(self) -> None:
        found = self.paths([
            ("Write", {"file_path": os.path.join(self.run, "stray.txt")}),
            ("Edit", {"file_path": "../other.txt"}),
            ("NotebookEdit", {"notebook_path": os.path.join(self.outside, "n.ipynb")}),
            ("Write", {"file_path": os.path.join(self.run, "project-other", "x")}),
        ])
        self.assertEqual(found, ["other.txt", "outside-run-root", "project-other/x", "stray.txt"], "outside paths")

    def test_a_symlink_and_a_dot_dot_path_are_resolved_before_the_test(self) -> None:
        os.symlink(self.outside, os.path.join(self.project, "link"))
        found = self.paths([
            ("Write", {"file_path": os.path.join(self.project, "link", "f.txt")}),
            ("Write", {"file_path": os.path.join(self.project, "sub", "..", "..", "up.txt")}),
        ])
        self.assertEqual(found, ["outside-run-root", "up.txt"], "the link target and the dot-dot path are outside")

    def test_paths_inside_the_roots_are_not_listed(self) -> None:
        found = self.paths([
            ("Write", {"file_path": os.path.join(self.memory, "m.md")}),
            ("Write", {"file_path": os.path.join(self.project, ".preclear", "x", "checkpoint.md")}),
            ("Edit", {"file_path": os.path.join(self.ckpt, "ledgers", "l.md")}),
            ("Write", {"file_path": "relative/inside.txt"}),
            ("Read", {"file_path": os.path.join(self.outside, "read-only.txt")}),
            ("Bash", {"command": "touch " + os.path.join(self.outside, "b.txt")}),
        ])
        self.assertEqual(found, [], "nothing outside, and Read and Bash are not write tools here")

    def test_a_denied_call_is_not_listed_and_an_executed_one_is(self) -> None:
        calls = [("Write", {"file_path": os.path.join(self.run, "denied.txt")}),
                 ("Write", {"file_path": os.path.join(self.run, "done.txt")})]
        self.assertEqual(self.paths(calls, denied=["t0"]), ["done.txt"], "only the executed call counts")
        self.assertEqual(self.paths(calls, denied=["t0", "t1"]), [], "both denied")

    def test_an_odd_path_value_is_skipped_and_never_fails(self) -> None:
        self.assertEqual(self.paths([("Write", {"file_path": 7}), ("Write", {}), ("Write", {"file_path": ""})]), [])

    def test_the_seeded_trace_write_is_found_by_the_scan_and_not_by_the_snapshot(self) -> None:
        run = Run(pc_testutil.seed_trace_write(pc_testutil.default_row1_stages(), 1))
        facts = run.facts()
        self.assertEqual(facts["write_boundary"]["count"], 0, "the snapshot diff is blind to it")
        self.assertEqual(facts["trace_writes"]["count"], 1, "the trace scan sees it")
        self.assertEqual(facts["trace_writes"]["paths"], ["outside-run-root"], "as a fixed token")
        self.assertTrue(os.path.isfile(os.path.join(run.rig.outside, "traced.txt")), "it was really written")


class MentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run, self.project, self.ckpt, self.memory, self.outside = real_dirs()
        self.approved = [self.project, self.ckpt, self.memory]

    def mentions(self, *commands, denied=()):
        return checks().bash_mentions(stream([bash(c) for c in commands], denied), self.approved)

    def test_an_absolute_path_outside_the_roots_is_counted_and_never_printed(self) -> None:
        found = self.mentions("ls " + self.outside, "cat " + os.path.join(self.project, "a"), "ls .")
        self.assertEqual(found["outside_path_tokens"], 1, "one outside path")
        self.assertEqual(found["commands"], 3, "three executed commands")
        self.assertNotIn(self.outside, json.dumps(found), "no path in the facts")

    def test_write_capable_programs_are_listed_by_name_with_counts(self) -> None:
        found = self.mentions(
            "python3 -c 'print(1)'",
            "awk '{print}' f",
            "sed -n 'w out.txt' f",
            "find . -fprint out.txt",
            "git diff --output=f",
            "mkdir -p d",
            "tee x",
            "cp a b",
            "mv a b",
            "dd if=a of=b",
            "touch t",
            "install a b",
            "ls && mkdir e",
        )
        self.assertEqual(
            found["write_programs"],
            {"python3-c": 1, "awk": 1, "sed-write": 1, "find-output": 1, "git-diff-output": 1, "mkdir": 2, "tee": 1,
             "cp": 1, "mv": 1, "dd": 1, "touch": 1, "install": 1},
            "each program is counted by name",
        )

    def test_read_only_forms_of_those_programs_are_not_listed(self) -> None:
        found = self.mentions("sed -n '1,3p' f", "find . -name x", "python3 script.py", "git diff", "git log", "ls -la")
        self.assertEqual(found["write_programs"], {}, "nothing write-capable")

    def test_a_denied_call_is_not_listed_and_an_unparseable_part_is_counted(self) -> None:
        found = self.mentions("mkdir denied", "echo 'unbalanced", denied=["t0"])
        self.assertEqual(found["write_programs"], {}, "the denied mkdir is not listed")
        self.assertEqual(found["unparsed_parts"], 1, "the unbalanced quote is counted, not guessed")
        self.assertEqual(found["commands"], 1, "one executed command")

    def test_a_read_only_command_naming_an_outside_path_is_no_breach(self) -> None:
        run = Run(pc_testutil.seed_outside_mention(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertGreaterEqual(facts["bash_mentions"]["outside_path_tokens"], 1, "the mention is listed")
        self.assertEqual(checks().breaches(facts), [], "and is no breach")


class MemoryProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-"))
        self.config = os.path.join(base, "config-folder")
        os.makedirs(self.config)
        self.project = os.path.join(base, "run", "project")
        os.makedirs(self.project)

    def test_the_default_path_is_the_slug_of_the_project_under_the_projects_folder(self) -> None:
        c = checks()
        path = c.default_memory_path(self.config, self.project)
        slug = "".join(ch if ch.isascii() and ch.isalnum() else "-" for ch in os.path.realpath(self.project))
        self.assertEqual(path, os.path.join(self.config, "projects", slug, "memory"))

    def test_absent_present_and_unknown(self) -> None:
        c = checks()
        self.assertEqual(c.memory_probe(self.config, self.project), "absent", "nothing there")
        os.makedirs(c.default_memory_path(self.config, self.project))
        self.assertEqual(c.memory_probe(self.config, self.project), "present", "the folder is there")
        with unittest.mock.patch("pc_checks.os.lstat", side_effect=PermissionError("planted")):
            self.assertEqual(c.memory_probe(self.config, self.project), "unknown", "any other error is unknown")

    def test_one_lstat_and_the_config_folder_is_never_opened_listed_or_walked(self) -> None:
        import builtins

        c = checks()
        os.makedirs(c.default_memory_path(self.config, self.project))
        sentinel = os.path.join(self.config, "projects", "sentinel-name-5d1c")
        with open(sentinel, "w", encoding="utf-8") as handle:
            handle.write("planted")
        real = {"open": builtins.open, "listdir": os.listdir, "scandir": os.scandir, "walk": os.walk,
                "lstat": os.lstat}
        under = lambda value: isinstance(value, (str, bytes, os.PathLike)) and os.fsdecode(value).startswith(self.config)
        counted = []

        def guard(name):
            def inner(target=".", *args, **kwargs):
                if under(target):
                    raise AssertionError("the config folder was touched by " + name)
                return real[name](target, *args, **kwargs)
            return inner

        def counting_lstat(target, *args, **kwargs):
            if under(target):
                counted.append(os.fsdecode(target))
            return real["lstat"](target, *args, **kwargs)

        with unittest.mock.patch("builtins.open", guard("open")), \
                unittest.mock.patch("os.listdir", guard("listdir")), \
                unittest.mock.patch("os.scandir", guard("scandir")), \
                unittest.mock.patch("os.walk", guard("walk")), \
                unittest.mock.patch("os.lstat", counting_lstat):
            state = c.memory_probe(self.config, self.project)
        self.assertEqual(state, "present", "the function still returns")
        self.assertEqual(len(counted), 1, "exactly one lstat on a path under the config folder")
        self.assertNotIn("sentinel-name-5d1c", json.dumps(state), "the planted name never appears")

    def test_a_present_default_folder_counts_as_one_write_outside_the_roots(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        c = checks()
        folder = c.default_memory_path(run.ctx.config_dir, os.path.join(run.run_root, "project"))
        self.assertEqual(run.facts()["memory_probe"], "absent", "a clean run leaves it absent")
        os.makedirs(folder)
        facts = run.facts()
        self.assertEqual(facts["memory_probe"], "present", "the folder is seen")
        self.assertEqual(c.breaches(facts), [("writes-outside-approved-roots", 1)], "one write outside")
        self.assertNotIn(folder, json.dumps(facts), "no path in the facts")


def git_in(repo: str, *args: str) -> str:
    import subprocess

    env = pc_testutil.git_env({"PATH": os.environ.get("PATH", "/usr/bin:/bin")})
    done = subprocess.run(["git", "-C", repo] + list(args), env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return done.stdout.decode("utf-8", "replace")


def make_repo() -> str:
    repo = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-")), "project")
    os.makedirs(repo)
    git_in(repo, "init", "-q")
    git_in(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    with open(os.path.join(repo, "a.txt"), "w", encoding="utf-8") as handle:
        handle.write("one\n")
    git_in(repo, "add", "-A")
    git_in(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first")
    return repo


GIT_KEYS = ["branch", "gitdir_digest", "head", "refs_digest", "staged"]


class GitTests(unittest.TestCase):
    def state(self, repo: str):
        import shutil

        return checks().git_state(repo, shutil.which("git"))

    def test_the_state_has_head_branch_refs_gitdir_and_staged(self) -> None:
        repo = make_repo()
        state = self.state(repo)
        self.assertEqual(sorted(state), GIT_KEYS, "the documented keys")
        self.assertEqual(state["branch"], "refs/heads/main", "the branch")
        self.assertRegex(state["head"], r"^[0-9a-f]{40,64}$", "the head")
        self.assertEqual(state["staged"], 0, "nothing staged")
        self.assertEqual(self.state(repo), state, "reading twice gives the same state")

    def test_a_plain_git_status_changes_nothing(self) -> None:
        repo = make_repo()
        with open(os.path.join(repo, "a.txt"), "w", encoding="utf-8") as handle:
            handle.write("one\n")
        before = self.state(repo)
        git_in(repo, "status")
        git_in(repo, "status", "--porcelain")
        self.assertEqual(self.state(repo), before, "an index refresh is not a mutation")

    def test_a_commit_a_branch_a_staged_file_and_a_tag_each_change_the_state(self) -> None:
        repo = make_repo()
        base = self.state(repo)
        git_in(repo, "branch", "other")
        branched = self.state(repo)
        self.assertNotEqual(branched["refs_digest"], base["refs_digest"], "a new branch changes the refs")
        self.assertNotEqual(branched["gitdir_digest"], base["gitdir_digest"], "and the git folder")
        git_in(repo, "tag", "v1")
        tagged = self.state(repo)
        self.assertNotEqual(tagged["refs_digest"], branched["refs_digest"], "a tag changes the refs")
        with open(os.path.join(repo, "b.txt"), "w", encoding="utf-8") as handle:
            handle.write("two\n")
        git_in(repo, "add", "b.txt")
        staged = self.state(repo)
        self.assertEqual(staged["staged"], 1, "one staged entry")
        git_in(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "second")
        committed = self.state(repo)
        self.assertNotEqual(committed["head"], staged["head"], "a commit moves the head")
        self.assertEqual(committed["staged"], 0, "and empties the stage")

    def test_state_changes_staged_entries_and_executed_forms_are_counted(self) -> None:
        c = checks()
        base = {"head": "h1", "branch": "refs/heads/main", "refs_digest": "r1", "gitdir_digest": "g1", "staged": 0}
        moved = dict(base, head="h2", refs_digest="r2", gitdir_digest="g2")
        quiet = c.git_mutations([base, dict(base), dict(base)], [])
        self.assertEqual(quiet["total"], 0, "identical states and no calls")
        changed = c.git_mutations([base, moved], [])
        self.assertEqual(changed["state_changes"], 3, "three fields changed")
        self.assertEqual(changed["total"], 3, "and they are the total")
        staged = c.git_mutations([base, dict(base, staged=2)], [])
        self.assertEqual(staged["staged"], 2, "staged entries are counted")
        self.assertEqual(staged["total"], 2, "and counted in the total")
        both = c.git_mutations([base, dict(base, staged=1)], ["git add f"])
        self.assertEqual((both["staged"], both["executed"], both["total"]), (1, 1, 2), "each part is counted")

    def test_mutating_forms_are_counted_and_read_only_forms_are_not(self) -> None:
        c = checks()
        mutating = [
            "git add -A", "git commit -m x", "git rm f", "git mv a b", "git reset --hard", "git checkout main",
            "git switch x", "git restore f", "git stash", "git merge x", "git rebase x", "git cherry-pick x",
            "git revert x", "git clean -fd", "git tag v1", "git push", "git pull", "git fetch", "git config a b",
            "git init", "git gc", "git apply p", "git update-index --refresh", "git branch name",
            "git branch -d name", "git branch -D name", "git branch -m a b", "git branch -c a b",
            "git symbolic-ref HEAD refs/heads/x", "git worktree add p", "git worktree remove p",
            "git diff --output=f", "git -C dir commit -m x", "git -c a=b add f", "timeout 5 git commit -m x",
            "env GIT_DIR=x git add f", "ls && git commit -m x",
        ]
        read_only = [
            "git status", "git log --oneline", "git diff", "git show HEAD", "git rev-parse HEAD", "git ls-files",
            "git branch", "git branch --list", "git branch -a", "git branch --show-current", "git branch -v",
            "git symbolic-ref HEAD", "git symbolic-ref -q HEAD", "git worktree list", "git --no-optional-locks status",
            "git -C dir status", "ls -la", "echo git commit",
        ]
        for command in mutating:
            self.assertEqual(c.git_mutations([], [command])["executed"], 1, "counted: " + command)
        for command in read_only:
            self.assertEqual(c.git_mutations([], [command])["executed"], 0, "not counted: " + command)

    def test_a_denied_mutating_call_is_not_counted(self) -> None:
        c = checks()
        events = stream([bash("git add -A"), bash("git status")], denied=["t0"])
        commands = c.executed_bash_commands(events)
        self.assertEqual(commands, ["git status"], "the denied call is not executed")
        self.assertEqual(c.git_mutations([], commands)["total"], 0, "nothing counted")


class SeededBreachTests(unittest.TestCase):
    def breach_ids(self, run):
        return [name for name, _count in checks().breaches(run.facts())]

    def test_a_clean_run_reports_zero_for_every_count_and_returns_zero(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertEqual(facts["write_boundary"]["count"], 0, "snapshot path")
        self.assertEqual(facts["trace_writes"]["count"], 0, "trace path")
        self.assertEqual(facts["memory_probe"], "absent", "memory probe")
        self.assertEqual(facts["bash_mentions"]["outside_path_tokens"], 0, "the helper path is not a mention")
        self.assertEqual(facts["git"]["mutations"]["total"], 0, "git path")
        self.assertEqual(checks().breaches(facts), [], "no breach")

    def test_a_file_written_outside_the_roots_during_s2_is_a_breach(self) -> None:
        run = Run(pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertGreaterEqual(run.facts()["write_boundary"]["count"], 1, "snapshot path")
        self.assertIn("writes-outside-approved-roots", self.breach_ids(run), "named")

    def test_a_write_tool_call_outside_the_roots_is_a_breach_the_snapshot_cannot_see(self) -> None:
        run = Run(pc_testutil.seed_trace_write(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertEqual(run.facts()["write_boundary"]["count"], 0, "invisible to the snapshot")
        self.assertGreaterEqual(run.facts()["trace_writes"]["count"], 1, "trace path")
        self.assertIn("writes-outside-approved-roots", self.breach_ids(run), "named")
        self.assertIn("writes outside approved roots: 1", "\n".join(run.outcome.lines), "fixed text with the count")

    def test_a_commit_in_the_project_is_a_breach(self) -> None:
        run = Run(pc_testutil.seed_git_commit(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertGreaterEqual(run.facts()["git"]["mutations"]["state_changes"], 1, "git path")
        self.assertIn("git-mutations", self.breach_ids(run), "named")
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: git mutations: [1-9][0-9]*", "fixed text with the count")
        self.assertNotIn(run.rig.base, text, "no path")
        self.assertTrue(os.path.isfile(os.path.join(run.run_root, "raw", "s2.stdout")), "the raw bytes stay")
        self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")

    def test_an_executed_git_branch_is_a_breach(self) -> None:
        run = Run(pc_testutil.seed_git_branch(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        mutations = run.facts()["git"]["mutations"]
        self.assertGreaterEqual(mutations["executed"], 1, "the executed form is counted")
        self.assertGreaterEqual(mutations["state_changes"], 1, "and the state change")

    def test_a_denied_git_add_is_no_breach(self) -> None:
        run = Run(pc_testutil.seed_denied_git_add(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertEqual(facts["git"]["mutations"]["total"], 0, "nothing counted")
        self.assertEqual(len(facts["denials"]["s2"]), 2, "the denial is a fact: the bind and the add")

    def test_an_outside_path_mention_is_listed_and_the_run_still_returns_zero(self) -> None:
        run = Run(pc_testutil.seed_outside_mention(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        self.assertEqual(run.facts()["write_boundary"]["count"], 0, "no write")


def with_extra_ops(stages, index, ops):
    return pc_testutil.stages_with(stages, index, ops=list(stages[index]["ops"]) + list(ops))


LEDGER_A = "CONTINUITY_CLAUDE-widget-export.md"
WRAPPER_STATUS = {"op": "tool", "name": "Bash", "input": {"command": "$WRAPPER status"}, "run": "wrapper",
                  "args": ["status"]}


class LedgerFactTests(unittest.TestCase):
    def test_an_untouched_run_reports_every_watched_file_unchanged(self) -> None:
        facts = Run(pc_testutil.default_row1_stages()).facts()["ledgers"]
        self.assertEqual(sorted(facts["names"]), ["binding", "checkpoint-log", "ledger-a", "ledger-b", "ledger-roots"])
        self.assertEqual(set(facts["names"].values()), {"unchanged"}, "all unchanged")
        self.assertIs(facts["unchanged"], True, "and so overall")

    def test_a_changed_ledger_is_a_finding_for_the_reviewer_and_no_breach(self) -> None:
        stages = with_extra_ops(pc_testutil.default_row1_stages(), 1, [
            {"op": "write", "path": "$RUN/ckpt/ledgers/" + LEDGER_A, "text": "changed by the model\n"}])
        run = Run(stages)
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertEqual(facts["ledgers"]["names"]["ledger-a"], "changed", "reported")
        self.assertEqual(facts["ledgers"]["names"]["ledger-b"], "unchanged", "the other one is not")
        self.assertIs(facts["ledgers"]["unchanged"], False, "overall flag")
        self.assertEqual(checks().breaches(facts), [], "no breach")

    def test_ledger_digests_reports_absent_files_by_side(self) -> None:
        base = tempfile.mkdtemp(prefix="pc-checks-")
        both = [file_entry("ckpt/ledger-roots.json", digest("1"))]
        write_manifest(os.path.join(base, "first"), both)
        write_manifest(os.path.join(base, "last"), [])
        found = checks().ledger_digests(os.path.join(base, "first"), os.path.join(base, "last"))
        self.assertEqual(found["names"]["ledger-roots"], "absent-after", "removed")
        write_manifest(os.path.join(base, "again"), both)
        found = checks().ledger_digests(os.path.join(base, "last"), os.path.join(base, "again"))
        self.assertEqual(found["names"]["ledger-roots"], "absent-before", "added")
        self.assertEqual(found["names"]["ledger-a"], "absent-both", "never there")


class HelperCallTests(unittest.TestCase):
    WRAPPER = "/zz/wrapper/checkpoint"

    def calls(self, commands, log, denied=()):
        return checks().helper_calls(stream([bash(c) for c in commands], denied), self.WRAPPER, log)

    def test_the_default_s2_gives_two_attempted_one_executed_one_denied_and_agreement(self) -> None:
        facts = Run(pc_testutil.default_row1_stages()).facts()["helper_calls"]
        self.assertEqual(facts["s2"], {"attempted": 2, "executed": 1, "denied": 1, "compound_refusals": 0,
                                       "correlated": "yes"})
        self.assertEqual(facts["s1"]["attempted"], 0, "s1 made no helper call")
        self.assertEqual(facts["s3"]["executed"], 0, "s3 made no helper call")

    def test_a_denied_compound_command_naming_the_helper_is_a_refusal_and_not_a_denial(self) -> None:
        found = self.calls([self.WRAPPER + " status && ls"], "", denied=["t0"])
        self.assertEqual(found, {"attempted": 1, "executed": 0, "denied": 0, "compound_refusals": 1,
                                 "correlated": "yes"})

    def test_an_executed_call_with_no_log_line_is_correlated_no_and_never_a_breach(self) -> None:
        found = self.calls([self.WRAPPER + " status"], "")
        self.assertEqual(found["correlated"], "no")
        self.assertEqual(found["executed"], 0, "the log decides how many executed")

    def test_a_matching_log_line_is_correlated_yes_and_quoting_is_compared_as_arguments(self) -> None:
        log = "2026-10-28T21:49:02Z CALL status --session abc\n2026-10-28T21:49:02Z EXIT 0\n"
        found = self.calls([self.WRAPPER + " status --session 'abc'"], log)
        self.assertEqual((found["executed"], found["correlated"]), (1, "yes"))

    def test_a_malformed_log_line_is_unconfirmed(self) -> None:
        found = self.calls([self.WRAPPER + " status"], "this is not a log line\n")
        self.assertEqual(found["correlated"], "UNCONFIRMED")

    def test_a_command_that_does_not_split_is_unconfirmed(self) -> None:
        found = self.calls([self.WRAPPER + " status 'unbalanced"], "")
        self.assertEqual(found["correlated"], "UNCONFIRMED")

    def test_slices_follow_the_stage_records_so_an_s1_call_is_never_counted_for_s2(self) -> None:
        stages = with_extra_ops(pc_testutil.default_row1_stages(), 0, [WRAPPER_STATUS])
        facts = Run(stages).facts()["helper_calls"]
        self.assertEqual((facts["s1"]["attempted"], facts["s1"]["executed"]), (1, 1), "s1 has its own call")
        self.assertEqual((facts["s2"]["attempted"], facts["s2"]["executed"]), (2, 1), "s2 keeps its own")
        self.assertEqual(facts["s1"]["correlated"], "yes")
        self.assertEqual(facts["s2"]["correlated"], "yes")


class SessionFactTests(unittest.TestCase):
    def test_the_default_run_reports_the_session_agreement_and_the_status_facts(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        session = checks().compute_facts(run.run_root, run.ctx.config_dir)["session"]
        for stage in ("s1", "s2", "s3"):
            self.assertIs(session["stages"][stage]["init_session_as_requested"], True, stage + " init")
            self.assertIs(session["stages"][stage]["result_session_as_requested"], True, stage + " result")
        self.assertEqual(session["status_begins_with_session"], "yes")
        self.assertEqual(session["status_holds_s1_prefix"], "yes")
        self.assertEqual(session["status_names_ledger_b"], "yes")
        self.assertEqual(len(session["stages"]["s2"]["denial_ids"]), 1, "the denied bind")
        self.assertEqual(session["stages"]["s1"]["denial_ids"], [], "none in s1")

    def test_without_a_status_call_in_s2_the_status_facts_are_unconfirmed(self) -> None:
        stages = pc_testutil.default_row1_stages()
        stages = pc_testutil.stages_with(stages, 1, ops=[op for op in stages[1]["ops"] if op.get("run") != "wrapper"])
        session = Run(stages).facts()["session"]
        for key in ("status_begins_with_session", "status_holds_s1_prefix", "status_names_ledger_b"):
            self.assertEqual(session[key], "UNCONFIRMED", key)

    def test_a_session_id_that_differs_is_reported_false(self) -> None:
        c = checks()
        events = stream([])
        found = c.session_facts({"s1": events}, {"s1": "other-id"}, None)
        self.assertIs(found["stages"]["s1"]["init_session_as_requested"], False)
        self.assertIs(found["stages"]["s1"]["result_session_as_requested"], False)

    def test_reply_text_claiming_no_writes_changes_no_count(self) -> None:
        plain = Run(pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1))
        stages = pc_testutil.seed_outside_write(pc_testutil.default_row1_stages(), 1)
        stages[1]["result"] = dict(stages[1]["result"], text="no writes outside the approved roots were made")
        claimed = Run(stages)
        self.assertEqual(plain.facts()["write_boundary"], claimed.facts()["write_boundary"], "the same count")
        self.assertEqual(claimed.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "still a breach")


FACT_NAMES = [
    "bash_mentions", "denials", "git", "helper_calls", "ledgers", "memory_probe", "session", "snapshots",
    "stages", "streams", "trace_writes", "write_boundary",
]


class RefileFactsTests(unittest.TestCase):
    def test_compute_facts_returns_the_documented_names_as_plain_values(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        facts = run.facts()
        self.assertEqual(sorted(facts), FACT_NAMES, "the fact names")
        self.assertEqual(json.loads(json.dumps(facts)), facts, "plain values only")
        self.assertEqual(facts["stages"], ["s1", "s2", "s3"])
        self.assertEqual(facts["streams"], {"s1": "ok", "s2": "ok", "s3": "ok"})
        self.assertEqual(facts["snapshots"], [SNAP_SETUP, SNAP_ONE, SNAP_TWO, SNAP_THREE])

    def test_the_git_state_files_exist_after_a_run_and_are_exclusive(self) -> None:
        import shutil

        run = Run(pc_testutil.default_row1_stages())
        raw = os.path.join(run.run_root, "raw")
        for name in ("setup", "s1", "s2", "s3"):
            state = read_json(os.path.join(raw, name + ".git.json"))
            self.assertEqual(sorted(state), GIT_KEYS, "state file " + name)
        paths = {"project": os.path.join(run.run_root, "project"), "raw": raw}
        with self.assertRaises(FileExistsError):
            checks().capture_boundary_state(paths, "s1", shutil.which("git"))

    def test_the_facts_follow_a_second_look_after_the_run_ended(self) -> None:
        run = Run(pc_testutil.seed_git_commit(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(run.facts(), run.facts(), "a second look gives equal facts")
        self.assertGreaterEqual(run.facts()["git"]["mutations"]["total"], 1, "the breach is still there")

    def test_the_snapshot_order_agrees_with_the_row_runner(self) -> None:
        self.assertEqual(
            list(checks().SNAPSHOT_ORDER), [pc_row1.SNAPSHOT_SETUP] + [pc_row1.SNAPSHOT_NAMES[k] for k in ("s1", "s2", "s3")]
        )


def manifest():
    import pc_manifest

    return pc_manifest


def real_git() -> str:
    import shutil

    return shutil.which("git", path=os.pathsep.join(pc_testutil.SYSTEM_DIRS))


class Recorder(object):
    """Stands in for subprocess.run: records each command and returns a successful empty result."""

    def __init__(self) -> None:
        self.commands = []

    def __call__(self, command, *args, **kwargs):
        import types

        self.commands.append(list(command))
        return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")


def forbid_processes(*_args, **_kwargs):
    raise AssertionError("a process was started")


def marker_folder() -> str:
    return os.path.realpath(tempfile.mkdtemp(prefix="pc-marker-"))


def plant_fsmonitor(repo: str, marker: str) -> None:
    git_in(repo, "config", "core.fsmonitor", "touch %s #" % marker)


def plant_filter(repo: str, marker: str) -> None:
    git_in(repo, "config", "filter.planted.clean", "touch %s #" % marker)
    with open(os.path.join(repo, ".gitattributes"), "w", encoding="utf-8") as handle:
        handle.write("* filter=planted\n")


def plain_status(repo: str) -> None:
    """The control: a plain git status under the harness git environment, with no hardening option."""
    import subprocess

    subprocess.run([real_git(), "-C", repo, "status"], env=manifest()._git_environment(), stdin=subprocess.DEVNULL,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


HARDENING = ["-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false"]


class GitHardeningTests(unittest.TestCase):
    def test_every_git_call_against_the_project_carries_both_options_before_the_subcommand(self) -> None:
        recorder = Recorder()
        repo = make_repo()
        with unittest.mock.patch("subprocess.run", recorder):
            manifest().capture_git_status(repo, "git")
            checks().git_state(repo, "git")
        self.assertEqual(manifest().GIT_HARDENING, tuple(HARDENING), "the shared options")
        self.assertEqual(len(recorder.commands), 7, "two direct status captures, then three reads and two more captures")
        for command in recorder.commands:
            self.assertEqual(command[1:3], ["-C", repo], "the project is named first")
            self.assertEqual(command[3:7], HARDENING, "both options come right after the project")
            if "status" in command:
                self.assertLess(command.index("--no-optional-locks"), command.index("status"), "lock option first")
        self.assertEqual(sum(1 for command in recorder.commands if "status" in command), 4, "with and without -z, twice")
        for verb in ("rev-parse", "symbolic-ref", "for-each-ref"):
            self.assertEqual(sum(1 for command in recorder.commands if verb in command), 1, "one read: " + verb)

    def test_a_planted_fsmonitor_command_runs_only_for_a_plain_status(self) -> None:
        control, status_repo, state_repo = make_repo(), make_repo(), make_repo()
        markers = [os.path.join(marker_folder(), "marker") for _ in range(3)]
        for repo, marker in zip((control, status_repo, state_repo), markers):
            plant_fsmonitor(repo, marker)
        plain_status(control)
        self.assertTrue(os.path.exists(markers[0]), "the control proves the plant works on this git")
        manifest().capture_git_status(status_repo, real_git())
        self.assertFalse(os.path.exists(markers[1]), "capture_git_status never ran the command")
        checks().git_state(state_repo, real_git())
        self.assertFalse(os.path.exists(markers[2]), "git_state never ran the command")

    def test_the_digest_function_agrees_with_the_state_and_the_pin_stops_the_status(self) -> None:
        repo = make_repo()
        pin = manifest().gitdir_digest(repo)
        self.assertEqual(pin, checks().git_state(repo, real_git())["gitdir_digest"], "one digest, two callers")
        raw, text = manifest().capture_git_status(repo, real_git(), pin)
        self.assertEqual((raw, text), (b"", b""), "a clean repository with the matching pin runs")
        with open(os.path.join(repo, ".git", "config"), "a", encoding="utf-8") as handle:
            handle.write("[alias]\n\tx = status\n")
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(manifest().GitDirChanged, msg="a changed git folder stops the capture"):
                manifest().capture_git_status(repo, real_git(), pin)
        self.assertTrue(issubclass(manifest().GitDirChanged, manifest().ManifestError), "a manifest refusal")

    def test_a_change_confined_to_the_index_does_not_trip_the_pin(self) -> None:
        repo = make_repo()
        pin = manifest().gitdir_digest(repo)
        os.utime(os.path.join(repo, "a.txt"), (1, 1))
        git_in(repo, "update-index", "--refresh")
        with open(os.path.join(repo, ".git", "index.lock"), "wb") as handle:
            handle.write(b"")
        self.assertEqual(manifest().gitdir_digest(repo), pin, "index and index.lock are left out")
        manifest().capture_git_status(repo, real_git(), pin)

    def test_git_state_starts_no_git_command_once_the_folder_differs_from_the_pin(self) -> None:
        repo = make_repo()
        pin = manifest().gitdir_digest(repo)
        normal = checks().git_state(repo, real_git(), pin)
        self.assertEqual(normal["gitdir_digest"], pin, "the matching pin reads normally")
        self.assertRegex(normal["head"], r"^[0-9a-f]{40,64}$", "a real head")
        with open(os.path.join(repo, ".git", "config"), "a", encoding="utf-8") as handle:
            handle.write("[alias]\n\tx = status\n")
        with unittest.mock.patch("subprocess.run", forbid_processes):
            state = checks().git_state(repo, real_git(), pin)
        self.assertEqual(sorted(state), GIT_KEYS, "the same five keys")
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], checks().GIT_NOT_READ, key + " is the fixed text")
        self.assertEqual(checks().GIT_NOT_READ, "not-read", "the documented text")
        self.assertEqual(state["staged"], 0, "nothing staged is claimed")
        self.assertEqual(state["gitdir_digest"], manifest().gitdir_digest(repo), "the current digest is reported")
        self.assertNotEqual(state["gitdir_digest"], pin, "and it differs from the pin")

    def test_pinned_gitdir_reads_the_setup_state_file(self) -> None:
        c = checks()
        raw = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-")), "raw")
        os.makedirs(raw)
        self.assertIsNone(c.pinned_gitdir(raw), "no setup state file, no pin")
        state = {"head": "h", "branch": "b", "refs_digest": digest("1"), "gitdir_digest": digest("2"), "staged": 0}
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        self.assertEqual(c.pinned_gitdir(raw), digest("2"), "the stored digest")
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            handle.write("not json")
        with self.assertRaises(c.CheckError, msg="a malformed file is refused"):
            c.pinned_gitdir(raw)

    def test_a_planted_clean_filter_driver_never_runs_once_the_pin_is_taken(self) -> None:
        control, guarded = make_repo(), make_repo()
        markers = [os.path.join(marker_folder(), "marker") for _ in range(2)]
        pin = manifest().gitdir_digest(guarded)
        for repo, marker in zip((control, guarded), markers):
            plant_filter(repo, marker)
            os.utime(os.path.join(repo, "a.txt"), None)
        plain_status(control)
        self.assertTrue(os.path.exists(markers[0]), "the control proves the filter plant works on this git")
        self.assertNotEqual(manifest().gitdir_digest(guarded), pin, "the plant changed the git folder")
        with self.assertRaises(manifest().GitDirChanged, msg="the pinned capture refuses"):
            manifest().capture_git_status(guarded, real_git(), pin)
        self.assertFalse(os.path.exists(markers[1]), "the driver never ran")

    def test_a_pinned_snapshot_of_an_untouched_repository_runs_normally(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        paths = pc_row1.paths_for(run.run_root)
        pc_row1.take_snapshot(paths, "snap-9-extra", real_git())
        with open(os.path.join(run.run_root, "snaps", "snap-9-extra", "status.txt"), "rb") as handle:
            text = handle.read()
        self.assertNotIn(pc_row1.STATUS_NOT_RUN.encode("utf-8"), text, "real status output, not the fixed line")


class PlantedConfigTracerTests(unittest.TestCase):
    def check_plant(self, kind: str) -> None:
        stages = pc_testutil.seed_git_config_plant(pc_testutil.default_row1_stages(), 0, kind)
        run = Run(stages)
        marker = os.path.join(run.rig.outside, "planted-" + kind)
        self.assertFalse(os.path.exists(marker), "the planted command never ran")
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: git mutations: [1-9][0-9]*", "fixed text with the count")
        self.assertNotIn(run.rig.base, text, "no path in the text")
        raw = os.path.join(run.run_root, "raw")
        for name in ("s1.record.json", "s1.git.json", "s1.stdout"):
            self.assertTrue(os.path.isfile(os.path.join(raw, name)), "kept: " + name)
        snap = os.path.join(run.run_root, "snaps", SNAP_ONE)
        self.assertTrue(os.path.isdir(snap), "the snapshot is kept")
        with open(os.path.join(snap, "status.txt"), "r", encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), pc_row1.STATUS_NOT_RUN, "the fixed not-run line")
        self.assertEqual(len(run.rig.calls()), 1, "the second stage was never launched")

    def test_a_planted_fsmonitor_command_never_runs_and_the_row_ends_with_11(self) -> None:
        self.check_plant("fsmonitor")

    def test_a_planted_clean_filter_never_runs_and_the_row_ends_with_11(self) -> None:
        self.check_plant("filter")

    def test_the_clean_run_keeps_real_status_text_and_the_state_keys(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        for name in (SNAP_SETUP, SNAP_ONE, SNAP_TWO, SNAP_THREE):
            with open(os.path.join(run.run_root, "snaps", name, "status.txt"), "r", encoding="utf-8") as handle:
                self.assertNotEqual(handle.read().strip(), pc_row1.STATUS_NOT_RUN, "real status in " + name)
        for name in ("setup", "s1", "s2", "s3"):
            state = read_json(os.path.join(run.run_root, "raw", name + ".git.json"))
            self.assertEqual(sorted(state), GIT_KEYS, "state file " + name)

    def test_the_seed_refuses_an_unknown_kind(self) -> None:
        with self.assertRaises(ValueError):
            pc_testutil.seed_git_config_plant(pc_testutil.default_row1_stages(), 0, "other")


if __name__ == "__main__":
    unittest.main()
