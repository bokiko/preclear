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
            "awk '{print > \"out.txt\"}' f",
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
            "rm x",
            "ls && mkdir e",
        )
        self.assertEqual(
            found["write_programs"],
            {"python3-c": 1, "awk": 1, "sed-write": 1, "find-output": 1, "git-diff-output": 1, "mkdir": 2, "tee": 1,
             "cp": 1, "mv": 1, "dd": 1, "touch": 1, "install": 1, "rm": 1},
            "each program is counted by name",
        )

    def test_read_only_forms_of_those_programs_are_not_listed(self) -> None:
        found = self.mentions(
            "sed -n '1,3p' f", "find . -name x", "git diff", "git log", "ls -la", "grep -r x .", "diff a b",
            "awk '{print $1}' f",
        )
        self.assertEqual(found["write_programs"], {}, "nothing write-capable")

    def test_an_interpreter_is_never_provably_read_only_and_is_listed(self) -> None:
        found = self.mentions("python3 script.py", "rm x")
        self.assertEqual(found["write_programs"], {"python3": 1, "rm": 1}, "listed under the program name")

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
            with self.assertRaises(c.CheckError, msg="any other error is a failure to read"):
                c.memory_probe(self.config, self.project)

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


class StatusFactTests(unittest.TestCase):
    """WR-02: the status question is about the helper's session line, which follows the brand line."""

    def answer(self, text):
        c = checks()
        found = c.session_facts({"s1": stream([])}, {"s1": "sid"}, text)
        return found["status_begins_with_session"]

    def test_the_helper_session_line_among_the_first_five_lines_is_yes(self) -> None:
        brand = "a brand line"
        cases = {
            "brand then session": brand + "\nsession abc\nledger x\n",
            "session alone": "session abc\nledger x\n",
            "session as the fifth line": "one\ntwo\nthree\nfour\nsession abc\nsix\n",
        }
        for label, text in sorted(cases.items()):
            self.assertEqual(self.answer(text), "yes", label)

    def test_anything_else_is_no(self) -> None:
        cases = {
            "session as the sixth line": "one\ntwo\nthree\nfour\nfive\nsession abc\n",
            "the word sessions": "sessions abc\nledger x\n",
            "a capital S": "Session abc\nledger x\n",
            "only indented session text": "brand\n  session abc\n",
            "the word with no space after it": "brand\nsession\n",
            "empty": "",
        }
        for label, text in sorted(cases.items()):
            self.assertEqual(self.answer(text), "no", label)

    def test_the_other_two_questions_and_the_unconfirmed_case_are_unchanged(self) -> None:
        c = checks()
        found = c.session_facts({"s1": stream([])}, {"s1": "abcdefgh-1234"}, "brand\nsession abcdefgh\nledger B\n")
        self.assertEqual(found["status_holds_s1_prefix"], "yes")
        self.assertEqual(found["status_names_ledger_b"], "no")
        missing = c.session_facts({"s1": stream([])}, {"s1": "sid"}, None)
        for key in ("status_begins_with_session", "status_holds_s1_prefix", "status_names_ledger_b"):
            self.assertEqual(missing[key], "UNCONFIRMED", key)

    def test_the_scripted_status_result_starts_with_the_stub_brand_line_and_the_default_run_is_yes(self) -> None:
        import checkpoint_stub

        run = Run(pc_testutil.default_row1_stages())
        wrapper = os.path.join(run.run_root, "wrapper", "checkpoint")
        text = checks().first_status_text(events_of(run, "s2"), wrapper)
        self.assertIsNotNone(text, "s2 made an executed status call")
        lines = text.splitlines()
        self.assertEqual(lines[0], checkpoint_stub.BRAND, "the brand line comes first, as on the real tool result")
        self.assertTrue(lines[1].startswith("session "), "the session line is the second line")
        self.assertEqual(run.facts()["session"]["status_begins_with_session"], "yes")


FACT_NAMES = [
    "bash_mentions", "denials", "git", "guard", "helper_calls", "ledgers", "memory_probe", "session", "snapshots",
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
            checks().capture_boundary_state(paths, "s1", shutil.which("git"), stored_pin(run.run_root))

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
        self.assertIsNone(c.pinned_gitdir(raw, True, None), "at setup the pin does not exist yet")
        with self.assertRaises(c.CheckError, msg="after setup a missing file is refused, not unpinned"):
            c.pinned_gitdir(raw, False, digest("2"))
        state = {"head": "h", "branch": "b", "refs_digest": digest("1"), "gitdir_digest": digest("2"), "staged": 0}
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        self.assertEqual(c.pinned_gitdir(raw, False, digest("2")), digest("2"), "the stored digest")
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            handle.write("not json")
        with self.assertRaises(c.CheckError, msg="a malformed file is refused"):
            c.pinned_gitdir(raw, False, digest("2"))

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
        pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=stored_pin(run.run_root))
        with open(os.path.join(run.run_root, "snaps", "snap-9-extra", "status.txt"), "rb") as handle:
            text = handle.read()
        self.assertNotIn(pc_row1.STATUS_NOT_RUN.encode("utf-8"), text, "real status output, not the fixed line")


def bare_paths():
    """A seeded run root with no snapshot and no state file yet, and its paths."""
    import uuid

    rig = pc_testutil.RowRig()
    ctx = rig.context()
    run_root = rig.new_run_root(ctx, "row1-bare-case")
    paths = pc_row1.seed_row1(
        rig.repo, run_root, str(uuid.uuid4()), ctx.harness_home, ctx.runs_root, ctx.evidence_date, ctx.model
    )
    return rig, paths


def move_pin_aside(run_root: str) -> None:
    raw = os.path.join(run_root, "raw")
    os.rename(os.path.join(raw, "setup.git.json"), os.path.join(raw, "setup.git.json.moved"))


class PinRequiredTests(unittest.TestCase):
    """WR-03 of the second pass, moved to the in-memory contract of WR-02: the pin is required after setup."""

    def test_the_boundary_and_the_value_are_required_arguments(self) -> None:
        c = checks()
        raw = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-")), "raw")
        os.makedirs(raw)
        self.assertIsNone(c.pinned_gitdir(raw, True, None), "setup, no file")
        state = {"head": "h", "branch": "b", "refs_digest": digest("1"), "gitdir_digest": digest("2"), "staged": 0}
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        self.assertIsNone(c.pinned_gitdir(raw, True, None), "setup, with a file: the pin is not used at setup")
        self.assertEqual(c.pinned_gitdir(raw, False, digest("2")), digest("2"), "after setup the stored digest")
        with self.assertRaises(TypeError, msg="no caller can reach the unpinned path by omission"):
            c.pinned_gitdir(raw)
        with self.assertRaises(TypeError, msg="the value is required too"):
            c.pinned_gitdir(raw, False)

    def test_a_missing_pin_file_with_a_good_value_refuses_and_starts_no_process(self) -> None:
        c = checks()
        run = Run(pc_testutil.default_row1_stages())
        pin = stored_pin(run.run_root)
        move_pin_aside(run.run_root)
        paths = pc_row1.paths_for(run.run_root)
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(c.CheckError, msg="a snapshot after setup needs the file"):
                pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=pin)
            with self.assertRaises(c.CheckError, msg="a boundary state after setup needs the file"):
                c.capture_boundary_state(paths, "s9", real_git(), pin)
        self.assertFalse(os.path.exists(os.path.join(run.run_root, "snaps", "snap-9-extra")), "no partial snapshot")

    def test_the_setup_boundary_still_works_on_a_bare_run_root(self) -> None:
        c = checks()
        rig, paths = bare_paths()
        pc_row1.take_snapshot(paths, pc_row1.SNAPSHOT_SETUP, real_git(), setup=True)
        pin = c.capture_boundary_state(paths, c.SETUP_STATE, real_git(), None)
        state = read_json(os.path.join(paths["raw"], "setup.git.json"))
        self.assertEqual(sorted(state), GIT_KEYS, "the setup state was written")
        pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=pin)
        self.assertTrue(os.path.isdir(os.path.join(paths["snaps"], "snap-9-extra")), "a pinned snapshot runs")

    def test_a_pinned_snapshot_without_the_keyword_is_not_a_setup_snapshot(self) -> None:
        rig, paths = bare_paths()
        with self.assertRaises(checks().CheckError, msg="the keyword defaults to false and the pin to none"):
            pc_row1.take_snapshot(paths, pc_row1.SNAPSHOT_SETUP, real_git())

    def test_the_end_to_end_row_with_the_pin_removed_ends_with_a_check_error(self) -> None:
        stages = pc_testutil.seed_pin_removed(pc_testutil.default_row1_stages(), 0)
        with self.assertRaises(checks().CheckError):
            Run(stages)

    def test_the_end_to_end_row_with_the_pin_rewritten_ends_with_a_check_error(self) -> None:
        stages = pc_testutil.seed_pin_rewritten(pc_testutil.default_row1_stages(), 0)
        with self.assertRaises(checks().CheckError):
            Run(stages)


def make_nested_plant(marker: str, committed: bool = True) -> str:
    """A repository holding a nested repository with a clean filter planted in its own configuration.

    The tracked file of the nested repository is staged first (and committed, so that the gitlink in the
    project's index names a real commit), then the filter command, an attributes file and a new modification
    time are planted. The top-level git folder is not changed by any of it.
    """
    repo = make_repo()
    nested = os.path.join(repo, "sub")
    git_in(repo, "init", "-q", nested)
    with open(os.path.join(nested, "tracked.txt"), "w", encoding="utf-8") as handle:
        handle.write("one\n")
    git_in(nested, "add", "tracked.txt")
    if committed:
        git_in(nested, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first")
        object_name = git_in(nested, "rev-parse", "HEAD").strip()
    else:
        object_name = "1" * 40
    git_in(repo, "update-index", "--add", "--cacheinfo", "160000,%s,sub" % object_name)
    git_in(nested, "config", "filter.planted.clean", "touch %s #" % marker)
    with open(os.path.join(nested, ".gitattributes"), "w", encoding="utf-8") as handle:
        handle.write("* filter=planted\n")
    os.utime(os.path.join(nested, "tracked.txt"), None)
    return repo


def harness_shaped_status(repo: str) -> None:
    """The control: the harness's own status command, run without the walk that refuses a nested repository."""
    import subprocess

    m = manifest()
    command = [real_git(), "-C", repo] + m._GIT_STATUS_BEFORE_Z + m._GIT_STATUS_AFTER_Z
    subprocess.run(command, env=m._git_environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, check=True)


class NestedRepositoryTests(unittest.TestCase):
    """WR-03 of the second pass: the harness runs no git command in a project that holds a nested repository."""

    def plain_project(self) -> str:
        return os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-nested-")), "project")

    def test_the_walk_refuses_an_entry_named_git_below_the_top_level_only(self) -> None:
        present = manifest().nested_git_present
        self.assertFalse(present(make_repo()), "a repository whose only .git is the top-level one")
        linked = self.plain_project()
        os.makedirs(linked)
        with open(os.path.join(linked, ".git"), "w", encoding="utf-8") as handle:
            handle.write("gitdir: elsewhere\n")
        self.assertFalse(present(linked), "a top-level .git file (a linked worktree layout)")
        linked_dir = self.plain_project()
        os.makedirs(linked_dir)
        os.symlink(make_repo(), os.path.join(linked_dir, ".git"))
        self.assertFalse(present(linked_dir), "a top-level .git link")
        nested = make_repo()
        git_in(nested, "init", "-q", os.path.join(nested, "sub"))
        self.assertTrue(present(nested), "a nested repository in a subfolder")
        as_file = make_repo()
        os.makedirs(os.path.join(as_file, "sub"))
        with open(os.path.join(as_file, "sub", ".git"), "w", encoding="utf-8") as handle:
            handle.write("gitdir: elsewhere\n")
        self.assertTrue(present(as_file), "a .git file in a subfolder")
        as_link = make_repo()
        os.makedirs(os.path.join(as_link, "sub"))
        os.symlink(make_repo(), os.path.join(as_link, "sub", ".git"))
        self.assertTrue(present(as_link), "a link named .git")
        deep = make_repo()
        os.makedirs(os.path.join(deep, "a", "b", "c"))
        git_in(deep, "init", "-q", os.path.join(deep, "a", "b", "c", "d"))
        self.assertTrue(present(deep), "three folders deep")

    def test_the_walk_fails_closed_and_follows_no_links(self) -> None:
        present = manifest().nested_git_present
        unreadable = make_repo()
        hidden = os.path.join(unreadable, "locked")
        os.makedirs(hidden)
        os.chmod(hidden, 0)
        try:
            if os.access(hidden, os.R_OK):
                self.skipTest("this user can read a folder with no permissions")
            self.assertTrue(present(unreadable), "a folder that cannot be read counts as a nested repository")
        finally:
            os.chmod(hidden, 0o700)
        outside = make_repo()
        outside_project = self.plain_project()
        os.makedirs(outside_project)
        os.symlink(os.path.dirname(outside), os.path.join(outside_project, "elsewhere"))
        self.assertFalse(present(outside_project), "a link to a folder that holds a repository is not followed")

    def test_a_planted_nested_clean_filter_runs_on_a_plain_status_and_never_under_the_harness(self) -> None:
        markers = [os.path.join(marker_folder(), "marker") for _ in range(3)]
        control, guarded, stated = [make_nested_plant(marker) for marker in markers]
        harness_shaped_status(control)
        self.assertTrue(os.path.exists(markers[0]), "the control proves the nested plant runs on the harness's status")
        pin = manifest().gitdir_digest(guarded)
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(manifest().NestedRepository, msg="the capture refuses before a process starts"):
                manifest().capture_git_status(guarded, real_git(), pin)
            with self.assertRaises(manifest().GitDirChanged, msg="it is a git folder refusal"):
                manifest().capture_git_status(guarded, real_git())
            state = checks().git_state(stated, real_git(), manifest().gitdir_digest(stated))
        self.assertFalse(os.path.exists(markers[1]), "capture_git_status never ran the filter")
        self.assertFalse(os.path.exists(markers[2]), "git_state never ran the filter")
        self.assertEqual(sorted(state), GIT_KEYS, "the same five keys")
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], checks().GIT_NOT_READ, key + " is the not-read text")
        self.assertEqual(state["gitdir_digest"], manifest().gitdir_digest(stated), "the current digest is reported")
        self.assertTrue(issubclass(manifest().NestedRepository, manifest().GitDirChanged), "a GitDirChanged")

    def test_the_pin_alone_cannot_see_the_nested_plant(self) -> None:
        repo = make_repo()
        before = manifest().gitdir_digest(repo)
        marker = os.path.join(marker_folder(), "marker")
        nested = os.path.join(repo, "sub")
        git_in(repo, "init", "-q", nested)
        with open(os.path.join(nested, "tracked.txt"), "w", encoding="utf-8") as handle:
            handle.write("one\n")
        git_in(nested, "add", "tracked.txt")
        git_in(repo, "update-index", "--add", "--cacheinfo", "160000,%s,sub" % ("1" * 40))
        git_in(nested, "config", "filter.planted.clean", "touch %s #" % marker)
        self.assertEqual(manifest().gitdir_digest(repo), before, "the top-level digest is the same after the plant")

    def test_a_nested_repository_at_setup_is_a_broken_fixture(self) -> None:
        c = checks()
        rig, paths = bare_paths()
        git_in(paths["project"], "init", "-q", os.path.join(paths["project"], "inner"))
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(c.CheckError, msg="a nested repository at setup is refused"):
                c.capture_boundary_state(paths, c.SETUP_STATE, real_git(), None)

    def test_the_snapshot_notes_the_nested_repository_with_a_fixed_line(self) -> None:
        rig, paths = bare_paths()
        pc_row1.take_snapshot(paths, pc_row1.SNAPSHOT_SETUP, real_git(), setup=True)
        c = checks()
        pin = c.capture_boundary_state(paths, c.SETUP_STATE, real_git(), None)
        git_in(paths["project"], "init", "-q", os.path.join(paths["project"], "inner"))
        with unittest.mock.patch("subprocess.run", forbid_processes):
            pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=pin)
        with open(os.path.join(paths["snaps"], "snap-9-extra", "status.txt"), "r", encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), pc_row1.STATUS_NOT_RUN_NESTED, "the fixed nested not-run line")
        self.assertNotEqual(pc_row1.STATUS_NOT_RUN_NESTED, pc_row1.STATUS_NOT_RUN, "a line of its own")
        self.assertNotIn("inner", pc_row1.STATUS_NOT_RUN_NESTED, "no name of the nested folder in the line")

    def test_the_end_to_end_row_ends_with_11_and_the_filter_never_runs(self) -> None:
        stages = pc_testutil.seed_nested_repo_plant(pc_testutil.default_row1_stages(), 0)
        run = Run(stages)
        marker = os.path.join(run.rig.outside, "planted-nested")
        self.assertFalse(os.path.exists(marker), "the planted command never ran")
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: git mutations: [1-9][0-9]*", "fixed text with the count")
        self.assertNotIn(run.rig.base, text, "no path in the text")
        state = read_json(os.path.join(run.run_root, "raw", "s1.git.json"))
        for key in ("head", "branch", "refs_digest"):
            self.assertEqual(state[key], checks().GIT_NOT_READ, key + " is the not-read text")
        snap = os.path.join(run.run_root, "snaps", SNAP_ONE)
        with open(os.path.join(snap, "status.txt"), "r", encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), pc_row1.STATUS_NOT_RUN_NESTED, "the fixed nested not-run line")
        self.assertEqual(len(run.rig.calls()), 1, "the second stage was never launched")


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


class WriteEscapeTests(unittest.TestCase):
    """The write-escape rule of bash_mentions (CR-02, D-03). OUT and PRJ stand for real folders of the test."""

    ESCAPING = [
        ("mkdir OUT/x", "mkdir"),
        ("mkdir -p OUT/x/y", "mkdir"),
        ("touch ~/x", "touch"),
        ("mkdir $HOME/x", "mkdir"),
        ("mkdir ${HOME}/x", "mkdir"),
        ("cp a ../b", "cp"),
        ("mv a ../../b", "mv"),
        ("cp -t OUT a", "cp"),
        ("tee OUT/f", "tee"),
        ("dd if=a of=OUT/f", "dd"),
        ("install -D a OUT/f", "install"),
        ("find . -fprint OUT/f", "find-output"),
        ("find . -exec cp {} OUT/ \\;", "find-output"),
        ("git diff --output=OUT/f", "git-diff-output"),
        ("python3 -c \"open('OUT/f','w').write('x')\"", "python3-c"),
        ("awk 'BEGIN{print \"x\" > \"OUT/f\"}'", "awk"),
        ("sed -n 'w OUT/f' g", "sed-write"),
        ("sed -i s/a/b/ OUT/f", "sed-write"),
        ("cat a > OUT/f", "redirect"),
        ("printf x >> ~/f", "redirect"),
        ("cd OUT && mkdir x", "mkdir"),
        ("cd && touch x", "touch"),
        ("cd .. && touch x", "touch"),
        ("env FOO=1 mkdir OUT/x", "mkdir"),
        ("LC_ALL=C mkdir OUT/x", "mkdir"),
        ("LC_ALL=C env FOO=1 mkdir OUT/x", "mkdir"),
        ("FOO=1 BAR=2 touch ~/x", "touch"),
        ("env -C OUT mkdir x", "mkdir"),
        ("awk -v f=OUT/x 'BEGIN{print 1 > f}'", "awk"),
        ("timeout 5 mkdir OUT/x", "mkdir"),
        ("ls && mkdir OUT/x", "mkdir"),
    ]
    HARMLESS = [
        "ls", "cat a", "head f", "wc -l f", "shasum f", "git status", "pwd", "date", "find . -name x",
        "sed -n '1,3p' f", "sed -n '/^## /p' f", "awk '{print $1}' f", "python3 -c 'print(1)'",
        "ls OUT", "cat OUT/f", "ls ~", "ls ..", "cd OUT", "cd OUT && ls",
        "mkdir -p PRJ/sub", "cp PRJ/a PRJ/b", "touch t", "tee PRJ/f", "mkdir CKPT/d", "install a MEM/f",
        "sed -i s/a/b/ PRJ/f", "git diff --output=out.txt", "python3 -c \"open('PRJ/f').read()\"",
        "find . -exec grep -l x {} \\;", "env -C PRJ mkdir sub", "LC_ALL=C awk '{print}' f",
        "cat a > PRJ/f", "cat a > /dev/null", "ls 2>&1", "ls >&2", "ls &>/dev/null",
    ]

    def setUp(self) -> None:
        self.run, self.project, self.ckpt, self.memory, self.outside = real_dirs()
        self.approved = [self.project, self.ckpt, self.memory]

    def found(self, command, denied=()):
        text = (command.replace("OUT", self.outside).replace("PRJ", self.project)
                .replace("CKPT", self.ckpt).replace("MEM", self.memory))
        return checks().bash_mentions(stream([bash(text)], denied), self.approved)["write_escapes"]

    def test_every_escaping_shape_is_one_write_escape_with_its_program_label(self) -> None:
        for number, (command, label) in enumerate(self.ESCAPING):
            self.assertEqual(self.found(command), {"count": 1, "programs": {label: 1}}, "escaping case %d" % number)

    def test_every_harmless_shape_is_no_write_escape(self) -> None:
        for number, command in enumerate(self.HARMLESS):
            self.assertEqual(self.found(command), {"count": 0, "programs": {}}, "harmless case %d" % number)

    def test_the_read_only_outside_mentions_are_still_counted_as_mentions(self) -> None:
        found = checks().bash_mentions(stream([bash("ls " + self.outside), bash("cat " + self.outside + "/f")]), self.approved)
        self.assertEqual(found["outside_path_tokens"], 2, "listed as before")
        self.assertEqual(found["write_escapes"]["count"], 0, "and no write escape")

    def test_an_awk_regex_pattern_is_not_a_path(self) -> None:
        self.assertEqual(self.found("awk '/x/{print}' f")["count"], 0, "a pattern")
        self.assertEqual(self.found("awk '/^## /{print}' f")["count"], 0, "a pattern with a heading")

    def test_an_awk_slash_literal_is_not_a_path(self) -> None:
        self.assertEqual(self.found("awk '{print $1 \"/\" $2}' f")["count"], 0, "a bare slash literal")

    def test_an_awk_field_separator_is_not_a_path(self) -> None:
        self.assertEqual(self.found("awk -F '/' '{print $1}' f")["count"], 0, "the separator after -F")

    def test_a_python_split_separator_is_not_a_path(self) -> None:
        self.assertEqual(self.found("python3 -c \"print('a/b'.split('/'))\"")["count"], 0, "a split separator")
        self.assertEqual(self.found("python3 -c \"print('a/b')\"")["count"], 0, "a relative literal")

    def test_a_path_literal_inside_a_script_still_counts(self) -> None:
        self.assertEqual(self.found("python3 -c \"open('OUT/f').read()\"")["count"], 1, "an open of an outside literal")
        self.assertEqual(self.found("awk '{print > \"OUT/g\"}'")["count"], 1, "a print redirected to an outside literal")
        self.assertEqual(self.found("python3 -c \"open('../up/f')\"")["count"], 1, "a dot-dot literal")

    def test_a_leading_assignment_does_not_hide_the_program(self) -> None:
        self.assertEqual(self.found("LC_ALL=C mkdir OUT/x"), {"count": 1, "programs": {"mkdir": 1}})
        self.assertEqual(self.found("LC_ALL=C awk '{print}' f")["count"], 0, "and the same prefix on a harmless use")

    def test_a_denied_command_is_not_counted_and_an_unparsed_part_decides_nothing(self) -> None:
        self.assertEqual(self.found("mkdir OUT/x", denied=["t0"])["count"], 0, "a denied call never ran")
        found = checks().bash_mentions(stream([bash("echo 'unbalanced")]), self.approved)
        self.assertEqual(found["unparsed_parts"], 1, "counted as unparsed")
        self.assertEqual(found["write_escapes"]["count"], 0, "and decides nothing")

    def test_tokens_skips_leading_assignments_and_the_env_prefix(self) -> None:
        c = checks()
        self.assertEqual(c._tokens("LC_ALL=C awk '{print}'")[0], "awk")
        self.assertEqual(c._tokens("FOO=1 BAR=2 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env FOO=1 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("FOO=1 env BAR=2 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env -u NAME -C dir mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("FOO=1 BAR=2"), [], "only assignments: no words")
        self.assertEqual(c._tokens("dd of=x"), ["dd", "of=x"], "an equals sign after the program is kept")

    def test_the_other_callers_of_tokens_see_through_the_prefixes(self) -> None:
        c = checks()
        self.assertEqual(c.git_mutations([], ["LC_ALL=C git commit -m x"])["executed"], 1, "a mutating form")
        found = checks().helper_calls(stream([bash("FOO=1 /zz/wrapper/checkpoint status")]), "/zz/wrapper/checkpoint", "")
        self.assertEqual(found["attempted"], 1, "an attempted helper call")

    def test_breaches_adds_the_write_escapes_to_the_single_writes_count(self) -> None:
        c = checks()

        def facts(escapes):
            return {"write_boundary": {"count": 1}, "trace_writes": {"count": 1}, "memory_probe": "present",
                    "git": {"mutations": {"total": 0}}, "guard": {"count": 0, "kinds": {}},
                    "bash_mentions": {"write_escapes": {"count": escapes, "programs": {}}}}

        self.assertEqual(c.breaches(facts(2)), [("writes-outside-approved-roots", 5)], "one id, all four sources")
        self.assertEqual(c.breaches(facts(0)), [("writes-outside-approved-roots", 3)], "none added for zero")

    def test_compute_facts_folds_the_write_escapes_of_every_stage(self) -> None:
        run = Run(pc_testutil.default_row1_stages())

        def mentions(count, programs):
            return {"commands": 1, "outside_path_tokens": 0, "unparsed_parts": 0, "write_programs": {},
                    "write_escapes": {"count": count, "programs": programs}}

        replies = [mentions(1, {"mkdir": 1}), mentions(2, {"mkdir": 1, "touch": 1}), mentions(0, {})]
        with unittest.mock.patch("pc_checks.bash_mentions", side_effect=replies):
            folded = run.facts()["bash_mentions"]["write_escapes"]
        self.assertEqual(folded, {"count": 3, "programs": {"mkdir": 2, "touch": 1}}, "summed over the three stages")
        self.assertEqual(run.facts()["bash_mentions"]["write_escapes"], {"count": 0, "programs": {}}, "clean run")


class WriteEscapeRunTests(unittest.TestCase):
    def check_breach(self, run) -> None:
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        text = "\n".join(run.outcome.lines)
        self.assertIn("isolation or git breach: writes outside approved roots: 1", text, "fixed text with the count")
        self.assertNotIn(run.rig.base, text, "no path in the text")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s2.stdout")), "the raw bytes stay")
        for name in (SNAP_SETUP, SNAP_ONE, SNAP_TWO):
            self.assertTrue(os.path.isdir(os.path.join(run.run_root, "snaps", name)), "snapshot kept: " + name)
        self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")
        self.assertFalse(os.path.exists(os.path.join(raw, "s3.stdout")), "no third stage output")

    def test_an_executed_mkdir_outside_with_a_really_written_file_ends_the_row_with_11(self) -> None:
        run = Run(pc_testutil.seed_bash_outside_write(pc_testutil.default_row1_stages()))
        self.check_breach(run)
        self.assertTrue(os.path.isfile(os.path.join(run.rig.outside, "made", "escaped.txt")), "the snapshot is blind to it")
        self.assertEqual(run.facts()["write_boundary"]["count"], 0, "no snapshot path")
        self.assertEqual(run.facts()["bash_mentions"]["write_escapes"], {"count": 1, "programs": {"mkdir": 1}})

    def test_each_expansion_form_alone_ends_the_row_with_11(self) -> None:
        for command in ("mkdir ~/x", "mkdir $HOME/x", "touch ../x", "cd .. && touch x"):
            run = Run(pc_testutil.seed_bash_outside_write(pc_testutil.default_row1_stages(), 1, command, False))
            self.check_breach(run)

    def test_a_read_only_outside_mention_and_a_write_inside_the_project_still_return_zero(self) -> None:
        mention = Run(pc_testutil.seed_outside_mention(pc_testutil.default_row1_stages(), 1))
        self.assertEqual(mention.outcome.code, 0, "\n".join(mention.outcome.lines))
        inside = Run(pc_testutil.seed_bash_outside_write(pc_testutil.default_row1_stages(), 1, "mkdir -p sub", False))
        self.assertEqual(inside.outcome.code, 0, "\n".join(inside.outcome.lines))


class OpenWorldBase(unittest.TestCase):
    """Shared set-up of the open-world write-rule tests. OUT and PRJ stand for real folders of the test."""

    def setUp(self) -> None:
        self.run, self.project, self.ckpt, self.memory, self.outside = real_dirs()
        self.approved = [self.project, self.ckpt, self.memory]
        self.wrapper = os.path.join(self.run, "wrapper", "checkpoint")

    def text(self, command):
        return (command.replace("OUT", self.outside).replace("PRJ", self.project)
                .replace("CKPT", self.ckpt).replace("MEM", self.memory).replace("WRAPPER", self.wrapper))

    def mentions(self, command):
        return checks().bash_mentions(stream([bash(self.text(command))]), self.approved, [self.wrapper])

    def found(self, command):
        return self.mentions(command)["write_escapes"]

    def check_table(self, table, what):
        for number, (command, label) in enumerate(table):
            self.assertEqual(self.found(command), {"count": 1, "programs": {label: 1}}, "%s case %d" % (what, number))


class WriteEscapeOpenWorldTests(OpenWorldBase):
    """The open-world write rule (CR-02, WR-01, D-03): every part not provably read-only is write-capable."""

    REVIEW_FORMS = [
        ("env sh -c 'touch OUT/x'", "sh"),
        ("env bash -c 'echo hi > OUT/x'", "bash"),
        ("env rm OUT/x", "rm"),
        ("env ln -s a OUT/x", "ln"),
        ("env tar -xf a.tar -C OUT", "tar"),
        ("env curl -o OUT/x https://example.invalid/", "curl"),
        ("env sort -o OUT/x f", "sort"),
        ("env xargs touch OUT/x", "xargs"),
        ("env python3 -Bc \"open('OUT/x','w').write('x')\"", "python3"),
        ("env -P PRJ mkdir OUT/x", "unparsed"),
        ("env -iS 'touch OUT/x'", "unparsed"),
        ("find . -exec sh -c 'echo hi > OUT/x' \\;", "find-output"),
    ]
    EXTRA_FORMS = [
        ("sed -n 'wOUT/x' f", "sed-write"),
        ("sed -n '1,3wOUT/x' f", "sed-write"),
        ("sed -n '/re/wOUT/x' f", "sed-write"),
        ("awk 'BEGIN{system(\"touch OUT/x\")}'", "awk"),
        ("python3 -c \"import os; os.system('touch OUT/x')\"", "python3-c"),
        ("sh -c 'touch OUT/x'", "sh"),
        ("env -a name mkdir OUT/x", "unparsed"),
        ("echo hi | tee OUT/x", "tee"),
        ("eval 'touch OUT/x'", "eval"),
        ("cd OUT && rm x", "rm"),
        ("env -S 'touch OUT/x'", "touch"),
        ("ln -s a OUT/x", "ln"),
        ("printf x | sort -o OUT/x", "sort"),
        ("find OUT -delete", "find-output"),
        ("find . -exec rm OUT/x {} +", "find-output"),
        ("awk '{print > \"OUT/f\"}'", "awk"),
        ("awk '{print | \"tee OUT/f\"}'", "awk"),
    ]
    MKTEMP_ESCAPING = [
        "mktemp", "mktemp -d", "mktemp -t name", "mktemp -p OUT", "mktemp OUT/tmp.XXXXXX", "mktemp --tmpdir=OUT",
        "mktemp -t -p PRJ",
    ]
    MKTEMP_INSIDE = ["mktemp -p PRJ", "mktemp PRJ/tmp.XXXXXX", "mktemp --tmpdir=PRJ", "mktemp tmp.XXXXXX"]
    SCRIPT_FILES = [
        "awk -f prog.awk f", "gawk --file prog.awk f", "awk -i inplace '{print}' f", "awk --include x '{print}' f",
        "awk -l x '{print}' f", "awk --load x '{print}' f", "sed -n -f s.sed f", "sed --file=s.sed f",
    ]
    READ_ONLY = [
        "awk '{print}' OUT/hosts",
        "awk '{print}' ../x",
        "awk '/^## /{if(h)print n, h; h=$0; n=0} {n+=length($0)+1; if(length($0)>m)m=length($0)} END{print n, h}' OUT/f",
        "cat OUT/hosts",
        "find OUT -name x -exec ls {} \\;",
        "find OUT -name x -exec grep -l y {} +",
        "grep -r x OUT",
        "sort OUT/f",
        "diff OUT/a OUT/b",
        "test -e OUT/f",
        "git -C OUT status",
        "git --no-optional-locks status --porcelain",
        "ls ~",
        "shasum -a 256 ../x",
        "sed -n '/w/p' f",
        "sed -n 's/x/w/p' f",
        "sed -n '/^wait/p' f",
        "WRAPPER status",
        "WRAPPER update --from OUT/f",
    ]
    INSIDE = [
        ("rm PRJ/x", "rm"),
        ("env rm PRJ/x", "rm"),
        ("env sh -c 'touch PRJ/x'", "sh"),
        ("ln -s a PRJ/b", "ln"),
        ("python3 script.py", "python3"),
        ("sh -c 'touch x'", "sh"),
        ("tar -xf a.tar -C PRJ/sub", "tar"),
        ("env -C PRJ rm x", "rm"),
        ("sed -n 'w out.txt' f", "sed-write"),
        ("awk '{print > \"PRJ/f\"}'", "awk"),
    ]

    def test_the_twelve_forms_of_the_review_are_each_one_write_escape_with_their_label(self) -> None:
        self.check_table(self.REVIEW_FORMS, "review form")

    def test_the_sed_awk_python_and_other_open_world_forms_are_each_one_write_escape(self) -> None:
        self.check_table(self.EXTRA_FORMS, "extra form")

    def test_mktemp_is_an_escape_unless_it_names_a_destination_inside_the_roots(self) -> None:
        for number, command in enumerate(self.MKTEMP_ESCAPING):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"mktemp": 1}}, "escaping mktemp %d" % number)
        for number, command in enumerate(self.MKTEMP_INSIDE):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "inside mktemp %d" % number)
            self.assertEqual(found["write_programs"], {"mktemp": 1}, "inside mktemp %d is listed" % number)

    def test_a_script_program_file_option_is_an_unparsed_escape_whatever_the_words(self) -> None:
        for number, command in enumerate(self.SCRIPT_FILES):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"unparsed": 1}}, "script file %d" % number)

    def test_read_only_uses_are_mentions_and_decide_nothing(self) -> None:
        for number, command in enumerate(self.READ_ONLY):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "read-only case %d" % number)
            self.assertEqual(found["write_programs"], {}, "read-only case %d is not listed" % number)

    def test_the_absolute_outside_words_of_read_only_uses_are_still_listed(self) -> None:
        self.assertEqual(self.mentions("awk '{print}' OUT/hosts")["outside_path_tokens"], 1, "awk over an outside file")
        self.assertEqual(self.mentions("cat OUT/hosts")["outside_path_tokens"], 1, "cat of an outside file")

    def test_write_capable_parts_inside_the_roots_are_listed_and_not_counted(self) -> None:
        for number, (command, label) in enumerate(self.INSIDE):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "inside case %d" % number)
            self.assertEqual(found["write_programs"], {label: 1}, "inside case %d is listed under its label" % number)

    def test_an_interpreter_that_only_reads_an_outside_path_is_counted_though_it_only_reads(self) -> None:
        self.assertEqual(
            self.found("python3 -c \"print(open('OUT/hosts').read())\""), {"count": 1, "programs": {"python3-c": 1}},
            "a read through an interpreter cannot be shown read-only",
        )
        self.assertEqual(
            self.found("python3 -c \"import re; print(re.findall(r'/[a-z]+/', 'x'))\""),
            {"count": 1, "programs": {"python3-c": 1}}, "a regular expression that reads as an absolute path is counted",
        )

    def test_an_unknown_env_option_fails_closed_and_the_known_prefixes_are_still_read(self) -> None:
        c = checks()
        for command in ("env -P x mkdir y", "env -a x mkdir y", "env -iS 'touch x'"):
            self.assertIsNone(c._tokens(command), "unparsed: " + command)
        self.assertEqual(c._tokens("env -i FOO=1 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env -0 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env -u A -C d mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env --chdir=d mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env --unset=A mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("env -- mkdir x"), ["mkdir", "x"])
        self.assertEqual(c._tokens("FOO=1 env BAR=2 mkdir x"), ["mkdir", "x"])
        self.assertEqual(c.git_mutations([], ["env -i LC_ALL=C git commit -m x"])["executed"], 1, "git still sees through env")

    def test_an_unparsed_part_without_an_escaping_word_decides_nothing_and_is_counted(self) -> None:
        found = self.mentions("env -P x mkdir y")
        self.assertEqual(found["unparsed_parts"], 1, "counted as unparsed")
        self.assertEqual(found["write_escapes"]["count"], 0, "and no escaping word")

    def test_labels_are_short_plain_words_and_the_listing_agrees_with_the_count(self) -> None:
        odd = self.mentions("./we$ird x")
        self.assertEqual(odd["write_programs"], {"other": 1}, "a basename that is not a plain word is other")
        long_name = self.mentions("a" * 40 + " x")
        self.assertEqual(long_name["write_programs"], {"other": 1}, "a long basename is other")
        inside = self.mentions("rm PRJ/x && rm OUT/x")
        self.assertEqual(inside["write_programs"], {"rm": 2}, "both write-capable parts are listed")
        self.assertEqual(inside["write_escapes"], {"count": 1, "programs": {"rm": 1}}, "only the escaping one is counted")
        for label in list(inside["write_programs"]) + list(odd["write_programs"]):
            self.assertNotIn("/", label, "no slash in a label")
            self.assertNotIn(" ", label, "no space in a label")

    def test_no_label_or_fact_holds_a_folder_of_the_rig(self) -> None:
        found = checks().bash_mentions(stream([bash(self.text("env sh -c 'touch OUT/x'"))]), self.approved)
        self.assertNotIn(self.outside, json.dumps(found), "no path in the facts")


class CheckMixin(object):
    """Table helpers shared by the Task 1 classes of plan 03-11."""

    def check_zero_table(self, table, what):
        for number, command in enumerate(table):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "%s zero case %d: %s" % (what, number, command))


class WriteEscapeDotDotTests(CheckMixin, OpenWorldBase):
    """A dot-dot path is resolved against the folder the command works in (CR-01, D-03)."""

    def setUp(self) -> None:
        super().setUp()
        os.makedirs(os.path.join(self.project, "sub"))

    INSIDE = [
        "mkdir -p ../auto-memory", "mkdir ../ckpt/sub", "printf '%s\\n' hi > ../auto-memory/note.md",
        "echo hi >> ../auto-memory/log.md", "cp a ../auto-memory/b", "mktemp -p ../auto-memory",
        "cd ../auto-memory && mkdir -p sub", "cd ../auto-memory && printf x > n.md",
        "cd ../auto-memory && mkdir ../ckpt/x", "cd sub && mkdir ../x", "mkdir sub/../other",
        "env -C ../auto-memory mkdir ../ckpt/y", "python3 -c \"open('../auto-memory/x.md').read()\"",
        "sed -n 'w ../ckpt/out.txt' f", "find ../auto-memory -name x -exec rm {} \\;",
        "awk '/system/ {print}' ../auto-memory/notes.md",
        "awk '{printf \"%s -> %d\\n\", $1, NR}' ../auto-memory/notes.md",
        "awk '{print ($1 > 3)}' ../auto-memory/notes.md",
    ]
    OUTSIDE = [
        ("mkdir -p ../../outside", "mkdir"), ("printf x > ../wrapper/x", "redirect"),
        ("printf x > ../raw/x", "redirect"), ("mkdir ..", "mkdir"), ("touch ../ckpt/../x", "touch"),
        ("cd sub && mkdir ../../x", "mkdir"), ("cd ../auto-memory && mkdir ../../x", "mkdir"),
        ("cd ../auto-memory/.. && touch x", "touch"), ("env -C ../auto-memory mkdir ../../x", "mkdir"),
        ("cd OUT && mkdir ../auto-memory", "mkdir"), ("cd && mkdir ../auto-memory", "mkdir"),
        ("python3 -c \"open('../../x','w').write('x')\"", "python3-c"),
        ("mkdir \"$PWD/../x\"", "mkdir"), ("mkdir $(pwd)/../x", "mkdir"), ("mkdir */../x", "mkdir"),
        ("mkdir ?/../x", "mkdir"), ("mkdir [a]/../x", "mkdir"), ("mkdir {a,b}/../x", "mkdir"),
        ("mkdir `pwd`/../x", "mkdir"), ("mkdir $d/../x", "mkdir"), ("mkdir ${d}/../x", "mkdir"),
        ("mkdir ../auto-memory/$d/../../x", "mkdir"), ("mkdir PRJ/$d/../x", "mkdir"),
        ("python3 -c \"open('$PWD/../x','w').write('x')\"", "python3-c"),
    ]
    UNKNOWN_FOLDER = [
        "cd $d && mkdir ../x", "cd \"$PWD\" && mkdir ../x", "cd $(pwd) && mkdir ../x", "cd sub* && mkdir ../x",
        "cd ../auto-memory/$d && mkdir ../../x", "env -C $d mkdir ../x",
    ]

    def test_a_dot_dot_path_that_resolves_inside_the_roots_is_not_an_escape(self) -> None:
        self.check_zero_table(self.INSIDE, "inside")

    def test_the_inside_dot_dot_writes_are_still_listed_under_their_labels(self) -> None:
        listed = self.mentions("mkdir -p ../auto-memory")["write_programs"]
        self.assertEqual(listed, {"mkdir": 1}, "the write-capable part is listed")
        self.assertEqual(self.mentions("printf x > ../auto-memory/n.md")["write_programs"], {"redirect": 1})
        self.assertEqual(self.mentions("sed -n 'w ../ckpt/out.txt' f")["write_programs"], {"sed-write": 1})
        self.assertEqual(self.mentions("python3 -c \"open('../auto-memory/x.md')\"")["write_programs"], {"python3-c": 1})

    def test_a_dot_dot_path_that_resolves_outside_or_follows_an_expansion_is_one_escape(self) -> None:
        self.check_table(self.OUTSIDE, "outside")

    def test_a_cd_or_env_directory_with_an_expansion_leaves_the_folder_unknown(self) -> None:
        for number, command in enumerate(self.UNKNOWN_FOLDER):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"mkdir": 1}}, "unknown folder %d" % number)
        self.check_zero_table(["cd $d && mkdir x", "cd $d && ls ../x", "cd sub && mkdir ../x"], "unknown folder, plain")

    def test_the_resolution_follows_a_link_and_does_not_cut_the_text(self) -> None:
        os.symlink(self.outside, os.path.join(self.project, "link"))
        self.assertEqual(self.found("mkdir link/../x"), {"count": 1, "programs": {"mkdir": 1}}, "through the link")
        self.assertEqual(self.found("mkdir sub/../x"), {"count": 0, "programs": {}}, "a plain folder name")

    def test_the_first_approved_root_is_the_start_folder(self) -> None:
        events = stream([bash("mkdir ../auto-memory"), bash("mkdir x")])
        ordered = checks().bash_mentions(events, [self.project, self.ckpt, self.memory])
        self.assertEqual(ordered["write_escapes"]["count"], 0, "project first: the memory folder is inside")
        empty = checks().bash_mentions(stream([bash("mkdir ../auto-memory")]), [])
        self.assertEqual(empty["write_escapes"]["count"], 1, "no start folder: a dot-dot word escapes")
        plain = checks().bash_mentions(stream([bash("mkdir x")]), [])
        self.assertEqual(plain["write_escapes"]["count"], 0, "and a plain word does not")


class WriteEscapeAttachedOptionTests(CheckMixin, OpenWorldBase):
    """A path attached to a short option is judged like any word (CR-05, D-03)."""

    ESCAPING = [
        ("env sort -oOUT/x f", "sort"), ("env tar -xf a.tar -COUT", "tar"), ("env tar -xvCOUT f", "tar"),
        ("env tar -czfOUT/a.tgz d", "tar"), ("env cc -oOUT/x f.c", "cc"), ("env git format-patch -oOUT", "git"),
        ("env cp -tOUT f", "cp"), ("env install -tOUT f", "install"), ("sort --output=OUT/x f", "sort"),
        ("env sort -o~/x f", "sort"), ("env cp -t$HOME f", "cp"), ("env cc -Isrc/x f.c", "cc"),
    ]
    INSIDE = [
        "env sort -o PRJ/x f", "env cp -tPRJ f", "env tar -xf a.tar -CPRJ/sub", "env tar -xvCPRJ/sub f",
        "env cc -oout f.c", "env tar -xzf a.tgz", "env mkdir -pv sub", "env cp -a src dst",
        "env git format-patch -o../ckpt", "env cc -o../ckpt/out f.c", "env cc -Iinclude/x -o out f.c",
        "env sort -n5 f", "grep -e OUT/hosts f", "ls -I OUT",
    ]

    def test_each_attached_option_form_is_one_escape_under_its_label(self) -> None:
        self.check_table(self.ESCAPING, "attached option")

    def test_relative_attached_values_and_read_only_parts_are_zero(self) -> None:
        self.check_zero_table(self.INSIDE, "attached option inside")

    def test_a_write_capable_part_with_an_attached_value_is_listed(self) -> None:
        self.assertEqual(self.mentions("env cc -oout f.c")["write_programs"], {"cc": 1})


class ReadOnlyGateTextTests(CheckMixin, OpenWorldBase):
    """Harmless script text and a test group are not writes (WR-04)."""

    HARMLESS_AWK = [
        "awk '/system/ {print}' OUT/hosts", "awk '/close/ {print}' OUT/hosts", "awk '{print \"system\"}' OUT/hosts",
        "awk '{print \"system(x)\"}' OUT/hosts", "awk '/getline/' OUT/hosts",
        "awk '{ while ((getline line < \"OUT/g\") > 0) print line }' f",
    ]
    CALLS = [
        "awk 'BEGIN{system(\"touch OUT/x\")}'", "awk 'BEGIN{system (\"touch OUT/x\")}'",
        "awk 'BEGIN{close(\"OUT/x\")}'", "awk 'BEGIN{\"touch OUT/x\" | getline}'",
    ]

    def test_awk_words_in_a_regular_expression_or_a_string_are_a_mention(self) -> None:
        for number, command in enumerate(self.HARMLESS_AWK):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "harmless awk %d" % number)
            self.assertEqual(found["write_programs"], {}, "harmless awk %d is not listed" % number)

    def test_awk_calls_are_still_write_escapes(self) -> None:
        for number, command in enumerate(self.CALLS):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"awk": 1}}, "awk call %d" % number)

    def test_a_double_bracket_test_is_one_part(self) -> None:
        found = self.mentions("[[ -f ../auto-memory/x && -s ../auto-memory/x ]] && echo ok")
        self.assertEqual(found["write_escapes"]["count"], 0)
        self.assertEqual(found["write_programs"], {}, "no part starts with -s")
        found = self.mentions("[[ -f OUT/x && -s OUT/x ]] && echo ok")
        self.assertEqual(found["write_escapes"]["count"], 0)
        self.assertEqual(found["outside_path_tokens"], 2)
        self.check_zero_table([
            "[[ ( -f a || -f b ) && -s c ]]", "if [[ -f a || -f b ]]; then wc -c a; fi",
            "[[ a =~ ^[[:alpha:]]+$ && -f b ]] && echo ok",
        ], "test group")

    def test_a_command_after_the_closing_brackets_is_still_a_part(self) -> None:
        self.check_table([
            ("[[ -f a ]] && rm OUT/x", "rm"), ("if [[ -f a || -f b ]]; then rm OUT/x; fi", "rm"),
            ("echo [[ && rm OUT/x", "rm"),
        ], "after the group")

    def test_an_unterminated_group_is_unparsed(self) -> None:
        found = self.mentions("[[ -f a && rm OUT/x")
        self.assertEqual(found["write_escapes"], {"count": 1, "programs": {"unparsed": 1}})
        self.assertEqual(found["unparsed_parts"], 1)


class SedScriptReaderTests(CheckMixin, OpenWorldBase):
    """The sed w operand is found by a reader of the script, not by an anchored pattern (CR-02, WR-04)."""

    ESCAPING = [
        ("sed -n 's/a/b/gw OUT/x' f", "sed-write"), ("sed -n 's/a/b/pw OUT/x' f", "sed-write"),
        ("sed -n '1!w OUT/x' f", "sed-write"), ("sed -n '1!wOUT/x' f", "sed-write"),
        ("sed -n '$!w OUT/x' f", "sed-write"), ("sed -n '/x/!w OUT/x' f", "sed-write"),
        ("sed -n '/x/Iw OUT/x' f", "sed-write"), ("sed -n '\\,x,w OUT/x' f", "sed-write"),
        ("sed -n '/a/s//b/gw OUT/x' f", "sed-write"), ("sed -n --expression='w OUT/x' f", "sed-write"),
        ("sed -n -e p -e 'w OUT/x' f", "sed-write"), ("sed -n '2,4w OUT/x' f", "sed-write"),
        ("sed -n '2~3w OUT/x' f", "sed-write"), ("sed -n '/a/,/b/w OUT/x' f", "sed-write"),
        ("sed -n 'y/a/b/;w OUT/x' f", "sed-write"), ("sed -n 's/a/b/;w OUT/x' f", "sed-write"),
        ("sed -n 'wOUT/x' f", "sed-write"), ("sed -n '1,3wOUT/x' f", "sed-write"),
        ("sed -n '/re/wOUT/x' f", "sed-write"), ("sed -n 'k;w OUT/x' f", "sed-write"),
        ("sed -n '1,+2w OUT/x' f", "sed-write"), ("sed -n '{w OUT/x\n}' f", "sed-write"),
    ]
    READ_ONLY = [
        "sed -n 's/ w /x/p' OUT/f", "sed -n 's/x/w/p' OUT/f", "sed -n '/w/p' OUT/f", "sed -n '/^wait/p' OUT/f",
        "sed -n '/a w b/p' OUT/f", "sed -n 'y/w/x/;p' OUT/f", "sed -n 's/a/b/g;p' OUT/f", "sed -n '1,3p' OUT/f",
        "sed -n '$p' OUT/f", "sed -n '/x/!p' OUT/f", "sed -n 's/\\//w/gp' OUT/f", "sed -n 's/a/ w \\/x\\/y/p' OUT/f",
    ]

    def test_each_form_of_the_review_and_the_range_step_and_y_forms_is_one_write_escape(self) -> None:
        self.check_table(self.ESCAPING, "sed write")

    def test_a_w_inside_a_pattern_a_replacement_or_a_y_part_is_data_and_read_only(self) -> None:
        for number, command in enumerate(self.READ_ONLY):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "read-only sed %d" % number)
            self.assertEqual(found["write_programs"], {}, "read-only sed %d is not listed" % number)

    def test_an_operand_inside_the_roots_is_listed_and_not_counted(self) -> None:
        for command in ("sed -n 'w out.txt' f", "sed -n 'w ../ckpt/out.txt' f", "sed -n 's/a/b/gw out.txt' f"):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, command)
            self.assertEqual(found["write_programs"], {"sed-write": 1}, command)

    def test_the_older_sed_cases_still_hold(self) -> None:
        self.assertEqual(self.found("sed -n '/w/p' f"), {"count": 0, "programs": {}})
        self.assertEqual(self.found("sed -n 's/x/w/p' f"), {"count": 0, "programs": {}})


class AwkProgramReaderTests(CheckMixin, OpenWorldBase):
    """The awk redirect test reads the program as awk does (CR-03, WR-04)."""

    ESCAPING = [
        ("awk 'BEGIN{print \"a;b\" > \"OUT/x\"}'", "awk"), ("awk '{print $1, \"a;b\" >> \"OUT/x\"}' f", "awk"),
        ("awk 'BEGIN{print \"}\" > \"OUT/x\"}'", "awk"), ("awk 'BEGIN{print 1,\n 2 > \"OUT/x\"}'", "awk"),
        ("awk -v o=OUT/x '{print \"a;b\" > o}' f", "awk"), ("awk '{print \"a;b\" | \"tee OUT/x\"}' f", "awk"),
        ("awk 'BEGIN{printf(\"%s\\n\", \"a;b\") > \"OUT/x\"}'", "awk"),
        ("awk '{print \"a\" > \"OUT/x\"; print \"b;\"}' f", "awk"), ("awk 'BEGIN{\"touch OUT/x\" | getline}'", "awk"),
        ("awk 'BEGIN{print \"x\" |& \"tee OUT/x\"}'", "awk"), ("awk 'BEGIN{print \"x\" > \"OUT/f\"}'", "awk"),
        ("awk '{print | \"tee OUT/f\"}'", "awk"),
    ]
    READ_ONLY = [
        "awk '{ if (length($0) > 80) print NR }' OUT/f", "awk 'length>80' OUT/f", "awk '{print ($1 > 3)}' OUT/f",
        "awk '{print $1, ($2 >= 3), ($3 || $4)}' OUT/f", "awk '{printf \"%s -> %d\\n\", $1, NR}' OUT/f",
        "awk '{print \"a -> b\"}' OUT/f", "awk '{print \"a;b\"}' OUT/f", "awk '/system/ {print}' OUT/f",
        "awk -F '>' '{print $1}' OUT/f", "awk -v t=\">\" '{print $1 t $2}' OUT/f",
        "awk '{ while ((getline line < \"OUT/g\") > 0) print line }' f",
        "awk '/^## /{if(h)print n, h; h=$0; n=0} {n+=length($0)+1; if(length($0)>m)m=length($0)} END{print n, h}' OUT/f",
    ]

    def test_each_redirect_after_a_semicolon_brace_or_newline_is_one_write_escape(self) -> None:
        self.check_table(self.ESCAPING, "awk redirect")

    def test_comparisons_strings_and_conditions_are_read_only_and_not_listed(self) -> None:
        for number, command in enumerate(self.READ_ONLY):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "read-only awk %d" % number)
            self.assertEqual(found["write_programs"], {}, "read-only awk %d is not listed" % number)

    def test_a_redirect_to_a_variable_is_listed_as_write_capable_inside_the_roots(self) -> None:
        found = self.mentions("awk -v o=out.txt '{print \"a;b\" > o}' f")
        self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}})
        self.assertEqual(found["write_programs"], {"awk": 1})


class AwkRawProgramTests(CheckMixin, OpenWorldBase):
    """A double quote inside an awk regular expression or comment cannot hide a statement (fourth pass CR-01, D-03)."""

    ESCAPING = [
        "awk -v o=OUT/x '/\"/ {print > o}' f",
        "awk -v o=OUT/x '{gsub(/\"/, \"\"); print $1 >> o}' f",
        "awk -v c='touch OUT/x' '/\"/ {system(c)}' f",
        "awk -v c='tee OUT/x' '$0 ~ /\"/ {print $1 | c}' f",
        "awk -v o=OUT/x '/a\"b/ { print > o }' f",
        "awk '/\"/ {print > \"OUT/x\"}' f",
        "awk '/\"/ {system(\"touch OUT/x\")}' f",
        "awk '/\"/ {close(\"OUT/x\")}' f",
        "awk -v o=OUT/x '/\"/ { print \"b\" > o } /\"/' f",
        "awk -v o=OUT/x '# \"word\n{print > o}' f",
        "awk -v o=OUT/x '{print $1 ~ /\\(/ > o}' f",
    ]
    OVER_COUNT = "awk '/x/ {print \"a -> b\"}' OUT/f"
    HARMLESS = [
        "awk '{gsub(/\"/, \"\"); print $1}' OUT/f", "awk '{print \"a -> b\"}' OUT/f",
        "awk '{print \"system(x)\"}' OUT/hosts", "awk '{printf \"%s -> %d\\n\", $1, NR}' OUT/f",
        "awk '/system/ {print}' OUT/hosts", "awk '{print ($1 > 3)}' OUT/f",
        "awk '{ if (length($0) > 80) print NR }' OUT/f",
    ]

    def test_each_quote_hidden_statement_is_one_escape_under_awk(self) -> None:
        for number, command in enumerate(self.ESCAPING):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"awk": 1}}, "raw awk case %d" % number)

    def test_each_quote_hidden_statement_is_listed_under_awk(self) -> None:
        for number, command in enumerate(self.ESCAPING):
            self.assertEqual(self.mentions(command)["write_programs"], {"awk": 1}, "raw awk listed %d" % number)

    def test_the_named_over_count_is_one_escape_under_awk(self) -> None:
        self.assertEqual(self.found(self.OVER_COUNT), {"count": 1, "programs": {"awk": 1}}, "pattern then a string")

    def test_the_harmless_string_forms_stay_read_only_and_unlisted(self) -> None:
        self.check_zero_table(self.HARMLESS, "raw awk harmless")
        for number, command in enumerate(self.HARMLESS):
            self.assertEqual(self.mentions(command)["write_programs"], {}, "harmless awk not listed %d" % number)


class WorkingFolderCertaintyTests(CheckMixin, OpenWorldBase):
    """The working folder moves only on a cd that is certain to run in the main shell and to succeed (CR-02, WR-01)."""

    STRICT = [
        "cd nosuch; mkdir ../x", "cd nosuch || mkdir ../x", "cd sub | cat; mkdir ../x", "cd sub & mkdir ../x",
        "cd sub; mkdir ../x", "cd sub\nmkdir ../x", "cd PRJ/sub; mkdir ../x", "cd nosuch && mkdir ../auto-memory/x",
        "true || cd sub && mkdir ../x", "echo hi | cd sub && mkdir ../x", "cd sub && true & mkdir ../x",
        "(cd sub && true); mkdir ../x", "(cd sub); mkdir ../x", "if true; then cd sub && true; fi; mkdir ../y",
        "for d in a; do cd sub && true; done; mkdir ../y", "{ cd sub && true; }; mkdir ../y",
        "x=$(cd sub; mkdir ../y)", "env -C nosuch mkdir ../x",
    ]
    STILL_ONE = [
        "echo $(cd sub && true); mkdir ../x", "cd sub && mkdir ../../x", "cd sub && cd .. && mkdir ../x",
    ]
    CERTAIN = [
        "cd sub && mkdir ../x", "cd PRJ/sub && mkdir ../x", "cd ../auto-memory && mkdir -p sub",
        "mkdir y && cd sub && mkdir ../z; true; cd .. && cd sub && mkdir ../x", "true & cd sub && mkdir ../x",
        "cd sub && cd .. && mkdir ../auto-memory/x", "cd sub && mkdir ../x || true",
        "cd sub && ls | wc -l && mkdir ../x", "x=$(cd sub && mkdir ../y)", "env -C sub mkdir ../x",
        "cd sub && mkdir ../x\nmkdir ../y",
    ]
    LOOSE_ZERO = [
        "cd \"$(git rev-parse --show-toplevel)\" && printf hi > ../auto-memory/x",
        "cd \"$(pwd)\" && printf hi > ../auto-memory/x", "cd $d && mkdir ../auto-memory/x", "cd $d; mkdir ../ckpt/y",
        "cd \"$PWD\" && cp a ../auto-memory/b",
    ]
    LOOSE_ONE = [
        "cd $d && mkdir ../x", "cd \"$(pwd)\" && mkdir ../x", "cd $d && cd ../auto-memory && mkdir ../x",
        "cd $d && mkdir ../../auto-memory/x",
    ]

    def setUp(self) -> None:
        super().setUp()
        os.makedirs(os.path.join(self.project, "sub"))

    def test_every_cd_that_is_not_certain_leaves_a_later_dot_dot_word_an_escape(self) -> None:
        for number, command in enumerate(self.STRICT):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"mkdir": 1}}, "strict %d: %s" % (number, command))

    def test_the_forms_that_were_already_one_escape_stay_one(self) -> None:
        for number, command in enumerate(self.STILL_ONE):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"mkdir": 1}}, "still one %d: %s" % (number, command))

    def test_a_certain_cd_to_an_existing_folder_moves_the_folder(self) -> None:
        self.check_zero_table(self.CERTAIN, "certain cd")

    def test_a_cd_to_an_expansion_resolves_a_dot_dot_word_against_the_project(self) -> None:
        self.check_zero_table(self.LOOSE_ZERO, "loose folder")
        for number, command in enumerate(self.LOOSE_ONE):
            self.assertEqual(self.found(command), {"count": 1, "programs": {"mkdir": 1}}, "loose one %d: %s" % (number, command))

    def test_the_two_unknown_states_in_one_place(self) -> None:
        self.assertEqual(self.found("cd $d && mkdir ../auto-memory/x")["count"], 0, "loose: resolved from the project")
        self.assertEqual(self.found("cd nosuch && mkdir ../auto-memory/x")["count"], 1, "strict: every dot-dot escapes")

    def test_the_folder_is_never_carried_from_one_bash_call_to_the_next(self) -> None:
        both = stream([bash(self.text("cd sub")), bash(self.text("mkdir ../x"))])
        found = checks().bash_mentions(both, self.approved, [self.wrapper])
        self.assertEqual(found["write_escapes"], {"count": 1, "programs": {"mkdir": 1}}, "the second call starts in the project")
        quiet = stream([bash(self.text("cd sub && true")), bash(self.text("mkdir ../auto-memory/x"))])
        found = checks().bash_mentions(quiet, self.approved, [self.wrapper])
        self.assertEqual(found["write_escapes"]["count"], 0, "and from the project it is inside")

    def test_the_connected_splitter_pairs_each_part_with_the_separator_after_it(self) -> None:
        import pc_allowlist

        self.assertEqual(pc_allowlist.split_compound_connected("cd sub && mkdir ../x"),
                         [("cd sub", "&&"), ("mkdir ../x", "")], "two parts")
        self.assertEqual(pc_allowlist.split_compound_connected("a; b | c & d || e\nf"),
                         [("a", ";"), ("b", "|"), ("c", "&"), ("d", "||"), ("e", "\n"), ("f", "")], "every separator")
        self.assertEqual(pc_allowlist.split_compound_connected("echo 'a;b' && \"x|y\""),
                         [("echo 'a;b'", "&&"), ("\"x|y\"", "")], "a separator in quotes stays in its part")
        self.assertEqual(pc_allowlist.split_compound_connected(""), [], "empty text")
        tables = (self.STRICT + self.STILL_ONE + self.CERTAIN + self.LOOSE_ZERO + self.LOOSE_ONE + AwkRawProgramTests.ESCAPING
                  + AwkRawProgramTests.HARMLESS)
        for command in tables:
            text = self.text(command)
            self.assertEqual(pc_allowlist.split_compound(text),
                             [part for part, _sep in pc_allowlist.split_compound_connected(text)], "one splitter: " + command)


class AttachedClusterValueTests(CheckMixin, OpenWorldBase):
    """The text after each option letter of a cluster is judged, and so is a sort cluster holding o (CR-03, D-03)."""

    TILDE = "~" + "/neutral"
    ESCAPING = [
        ("tar -xC.. -f a.tar", "tar"), ("tar -xzC../.. -f a.tar", "tar"), ("tar -xzvfC.. a.tar", "tar"),
        ("cp -rt../.. f", "cp"), ("sort -ro../x f", "sort"), ("sort -roOUT/x f", "sort"),
    ]
    ZERO = [
        "env cc -o../ckpt/out f.c", "env cc -Iinclude/x -o out f.c", "env sort -n5 f", "sort -rn OUT/f",
        "sort -t, -k2,2 OUT/f", "sort -u OUT/f", "sort --reverse OUT/f", "env tar -xzf a.tgz", "env cp -tPRJ f",
    ]

    def test_a_value_after_the_value_letter_of_a_cluster_is_one_escape_under_its_label(self) -> None:
        self.check_table(self.ESCAPING, "cluster value")
        self.check_table([("env " + command, label) for command, label in self.ESCAPING], "cluster value, env")

    def test_a_tilde_value_after_a_sort_cluster_is_one_escape(self) -> None:
        self.check_table([("sort -ro" + self.TILDE + " f", "sort"), ("env sort -ro" + self.TILDE + " f", "sort")], "tilde")

    def test_relative_values_and_read_only_sort_forms_are_zero(self) -> None:
        self.check_zero_table(self.ZERO, "cluster zero")

    def test_the_sort_cluster_holding_o_is_listed_and_the_read_only_forms_are_not(self) -> None:
        self.assertEqual(self.mentions("sort -roOUT/x f")["write_programs"], {"sort": 1}, "listed under sort")
        for command in ("sort -rn OUT/f", "sort -t, -k2,2 OUT/f", "sort -u OUT/f", "sort --reverse OUT/f"):
            self.assertEqual(self.mentions(command)["write_programs"], {}, "not listed: " + command)


class GitCommandConfigTests(CheckMixin, OpenWorldBase):
    """Git configuration that runs a command is a mutation whatever the key (CR-04, D-03)."""

    MUTATING = [
        "env git -c core.fsmonitor='touch x' status", "git -c core.fsmonitor=false status",
        "git -c color.ui=always status", "git -c core.x=y status", "git -c core.pager status",
        "git -c include.path=PRJ/cfg status", "git -c include.path=PRJ/cfg log", "git -c alias.x='!touch x' x",
        "git -c diff.external='sh -c \"touch x\"' diff", "git -c core.hooksPath=h status",
        "git -c filter.f.clean=x status", "git -C OUT -c core.fsmonitor=x status",
        "git --no-optional-locks -c color.ui=always status", "git -c color.ui=always -c core.pager=x log",
        "git -c", "git --exec-path=OUT status", "git --exec-path status", "git --config-env=core.fsmonitor=V status",
        "git --config-env core.fsmonitor=V status",
    ]
    READING = ["git status", "git -C dir status", "git --no-optional-locks status", "git log -c", "git show -c HEAD",
               "git diff -c"]

    def test_every_dash_c_before_the_verb_and_the_exec_path_and_config_env_options_are_a_mutation(self) -> None:
        for number, command in enumerate(self.MUTATING):
            found = checks().git_mutations([], [self.text(command)])
            self.assertEqual(found["executed"], 1, "mutating case %d: %s" % (number, command))
            self.assertEqual(found["forms"], ["config-command"], "mutating case %d: %s" % (number, command))
            self.assertEqual(found["total"], 1, "mutating case %d" % number)
            self.assertEqual(self.mentions(command)["unparsed_parts"], 0, "mutating case %d is not unparsed" % number)

    def test_a_dash_c_after_the_verb_and_the_plain_forms_count_nothing_and_stay_read_only(self) -> None:
        for number, command in enumerate(self.READING):
            self.assertEqual(checks().git_mutations([], [self.text(command)])["executed"], 0, "reading case %d" % number)
            found = self.mentions(command)
            self.assertEqual(found["write_programs"], {}, "reading case %d is read-only" % number)
            self.assertEqual(found["unparsed_parts"], 0, "reading case %d is not unparsed" % number)

    def test_the_read_only_gate_refuses_a_command_running_configuration(self) -> None:
        for command in ("git -c color.ui=always status", "git --exec-path=PRJ/h status", "git --config-env=a=B log"):
            self.assertEqual(self.mentions(command)["write_programs"], {"git": 1}, command)

    def test_an_outside_directory_beside_a_dash_c_is_a_mutation_and_one_write_escape(self) -> None:
        self.assertEqual(self.found("git -C OUT status"), {"count": 0, "programs": {}}, "a plain read stays a mention")
        self.assertEqual(self.found("git -C OUT -c core.x=y status"), {"count": 1, "programs": {"git": 1}})
        self.assertEqual(checks().git_mutations([], [self.text("git -C OUT -c core.x=y status")])["executed"], 1)


class NestedRepositoryCaseTests(unittest.TestCase):
    """WR-01: the nested walk compares names below the top level without regard to case."""

    TRUE_NAMES = (".GIT", ".Git", ".gIT")
    FALSE_NAMES = (".gitignore", ".github", ".gitattributes", ".gitmodules", "git", ".git-old")

    def project(self) -> str:
        return os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-nested-")), "project")

    def case_sensitive(self) -> bool:
        probe = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-case-")), "Probe")
        os.makedirs(probe)
        return not os.path.exists(probe.lower())

    def test_a_name_that_differs_only_in_case_is_a_nested_repository_and_a_lookalike_is_not(self) -> None:
        present = manifest().nested_git_present
        for name in self.TRUE_NAMES:
            for kind in ("folder", "file", "link"):
                project = self.project()
                folder = os.path.join(project, "sub")
                os.makedirs(folder)
                entry = os.path.join(folder, name)
                if kind == "folder":
                    os.makedirs(entry)
                elif kind == "file":
                    with open(entry, "w", encoding="utf-8") as handle:
                        handle.write("gitdir: elsewhere\n")
                else:
                    os.symlink(self.project(), entry)
                self.assertTrue(present(project), "%s as a %s" % (name, kind))
        for name in self.FALSE_NAMES:
            project = self.project()
            os.makedirs(os.path.join(project, "sub", name))
            self.assertFalse(present(project), "lookalike " + name)

    def test_the_top_level_entry_is_still_skipped_by_its_exact_name(self) -> None:
        present = manifest().nested_git_present
        for kind in ("folder", "file", "link"):
            project = self.project()
            os.makedirs(project)
            entry = os.path.join(project, ".git")
            if kind == "folder":
                os.makedirs(entry)
            elif kind == "file":
                with open(entry, "w", encoding="utf-8") as handle:
                    handle.write("gitdir: elsewhere\n")
            else:
                os.symlink(self.project(), entry)
            self.assertFalse(present(project), "top-level .git as a " + kind)

    def test_a_nested_repository_with_a_renamed_git_folder_never_runs_its_filter(self) -> None:
        if self.case_sensitive():
            self.skipTest("the scratch file system is case-sensitive")
        markers = [os.path.join(marker_folder(), "marker") for _ in range(3)]
        control, guarded, stated = [make_nested_plant(marker) for marker in markers]
        for repo in (control, guarded, stated):
            os.rename(os.path.join(repo, "sub", ".git"), os.path.join(repo, "sub", ".GIT"))
        harness_shaped_status(control)
        self.assertTrue(os.path.exists(markers[0]), "the control proves the plant runs through a renamed git folder")
        pin = manifest().gitdir_digest(guarded)
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(manifest().NestedRepository, msg="the capture refuses before a process starts"):
                manifest().capture_git_status(guarded, real_git(), pin)
            state = checks().git_state(stated, real_git(), manifest().gitdir_digest(stated))
        self.assertFalse(os.path.exists(markers[1]), "capture_git_status never ran the filter")
        self.assertFalse(os.path.exists(markers[2]), "git_state never ran the filter")
        self.assertEqual(state["head"], checks().GIT_NOT_READ, "the not-read text")

    def test_the_end_to_end_row_with_a_renamed_nested_git_folder_ends_with_11(self) -> None:
        if self.case_sensitive():
            self.skipTest("the scratch file system is case-sensitive")
        run = Run(pc_testutil.seed_nested_repo_plant(pc_testutil.default_row1_stages(), 0, ".GIT"))
        self.assertFalse(os.path.exists(os.path.join(run.rig.outside, "planted-nested")), "the planted command never ran")
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        self.assertNotIn(run.rig.base, "\n".join(run.outcome.lines), "no path in the text")
        self.assertEqual(len(run.rig.calls()), 1, "the second stage was never launched")


def stored_pin(run_root: str) -> str:
    """The setup digest a run stored, read the way the harness no longer does."""
    return read_json(os.path.join(run_root, "raw", "setup.git.json"))["gitdir_digest"]


def write_pin_file(raw: str, value) -> None:
    state = {"head": "h", "branch": "b", "refs_digest": digest("1"), "gitdir_digest": value, "staged": 0}
    with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
        json.dump(state, handle)


class PinHeldInMemoryTests(unittest.TestCase):
    """WR-02: the setup digest is held in memory and compared with the pin file before any git call."""

    def raw_folder(self) -> str:
        raw = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-")), "raw")
        os.makedirs(raw)
        return raw

    def test_pinned_gitdir_compares_the_file_with_the_value_held_in_memory(self) -> None:
        c = checks()
        raw = self.raw_folder()
        self.assertIsNone(c.pinned_gitdir(raw, True, None), "setup: no pin yet")
        self.assertIsNone(c.pinned_gitdir(raw, True, digest("2")), "setup: whatever is passed")
        with self.assertRaises(c.CheckError, msg="a missing file"):
            c.pinned_gitdir(raw, False, digest("2"))
        write_pin_file(raw, digest("2"))
        self.assertEqual(c.pinned_gitdir(raw, False, digest("2")), digest("2"), "the matching file")
        for bad in (None, "", "xyz", 5, digest("2")[:-1], digest("2").upper() + "0"):
            with self.assertRaises(c.CheckError, msg="a missing or malformed in-memory value: %r" % (bad,)):
                c.pinned_gitdir(raw, False, bad)
        with self.assertRaises(c.CheckError, msg="a file whose digest differs from the value held"):
            c.pinned_gitdir(raw, False, digest("3"))
        with open(os.path.join(raw, "setup.git.json"), "w", encoding="utf-8") as handle:
            handle.write("not json")
        with self.assertRaises(c.CheckError, msg="a malformed file"):
            c.pinned_gitdir(raw, False, digest("2"))

    def test_capture_boundary_state_returns_the_setup_digest_and_needs_the_pin_after_setup(self) -> None:
        c = checks()
        rig, paths = bare_paths()
        pc_row1.take_snapshot(paths, pc_row1.SNAPSHOT_SETUP, real_git(), setup=True)
        pin = c.capture_boundary_state(paths, c.SETUP_STATE, real_git(), None)
        self.assertEqual(pin, read_json(os.path.join(paths["raw"], "setup.git.json"))["gitdir_digest"], "the digest it wrote")
        with self.assertRaises(TypeError, msg="the pin is a required argument"):
            c.capture_boundary_state(paths, "s9", real_git())
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(c.CheckError, msg="a missing value after setup"):
                c.capture_boundary_state(paths, "s9", real_git(), None)
        c.capture_boundary_state(paths, "s9", real_git(), pin)
        self.assertTrue(os.path.isfile(os.path.join(paths["raw"], "s9.git.json")), "the pinned capture runs")

    def test_a_snapshot_with_a_file_that_differs_from_the_pin_is_refused_before_anything_starts(self) -> None:
        c = checks()
        run = Run(pc_testutil.default_row1_stages())
        paths = pc_row1.paths_for(run.run_root)
        pin = stored_pin(run.run_root)
        write_pin_file(paths["raw"], digest("9"))
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(c.CheckError, msg="the snapshot refuses"):
                pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=pin)
            with self.assertRaises(c.CheckError, msg="the boundary state refuses"):
                c.capture_boundary_state(paths, "s9", real_git(), pin)
        self.assertFalse(os.path.exists(os.path.join(run.run_root, "snaps", "snap-9-extra")), "no snapshot folder")
        self.assertFalse(os.path.exists(os.path.join(paths["raw"], "s9.git.json")), "no state file")

    def test_a_pin_file_rewritten_to_a_planted_state_is_refused_and_the_filter_never_runs(self) -> None:
        c = checks()
        run = Run(pc_testutil.default_row1_stages())
        paths = pc_row1.paths_for(run.run_root)
        pin = stored_pin(run.run_root)
        markers = [os.path.join(marker_folder(), "marker") for _ in range(2)]
        project = str(paths["project"])
        plant_filter(project, markers[0])
        os.utime(os.path.join(project, "CLAUDE.md"), None)
        planted = manifest().gitdir_digest(project)
        self.assertNotEqual(planted, pin, "the plant changed the git folder")
        write_pin_file(paths["raw"], planted)
        with unittest.mock.patch("subprocess.run", forbid_processes):
            with self.assertRaises(c.CheckError, msg="the snapshot refuses a rewritten file"):
                pc_row1.take_snapshot(paths, "snap-9-extra", real_git(), pin=pin)
            with self.assertRaises(c.CheckError, msg="the boundary state refuses it"):
                c.capture_boundary_state(paths, "s9", real_git(), pin)
        self.assertFalse(os.path.exists(markers[0]), "the planted filter never ran")
        control = make_repo()
        plant_filter(control, markers[1])
        os.utime(os.path.join(control, "a.txt"), None)
        manifest().capture_git_status(control, real_git(), manifest().gitdir_digest(control))
        self.assertTrue(os.path.exists(markers[1]), "the control: a file trusted with the planted digest runs it")

    def test_run_row_keeps_the_setup_digest_in_the_run_context(self) -> None:
        import pc_rows

        self.assertIn("setup_pin", pc_rows.RunContext._fields, "the context holds the pin")
        self.assertIsNone(pc_rows.RunContext._field_defaults.get("setup_pin", "missing"), "defaulted to None")


class OpenWorldRunTests(unittest.TestCase):
    """The open-world write rule at run level: each escaping form ends run_row with 11 and nothing filed."""

    ESCAPING = [
        "env sh -c 'touch OUT/x'", "env bash -c 'echo hi > OUT/x'", "env rm OUT/x", "env ln -s a OUT/x",
        "env tar -xf a.tar -C OUT", "env curl -o OUT/x https://example.invalid/", "env sort -o OUT/x f",
        "env xargs touch OUT/x", "env python3 -Bc \"open('OUT/x','w').write('x')\"", "env -P . mkdir OUT/x",
        "env -iS 'touch OUT/x'", "find . -exec sh -c 'echo hi > OUT/x' \\;",
        "sed -n 'wOUT/x' f", "sed -n '1,3wOUT/x' f", "sed -n '/re/wOUT/x' f", "awk 'BEGIN{system(\"touch OUT/x\")}'",
        "python3 -c \"import os; os.system('touch OUT/x')\"", "sh -c 'touch OUT/x'", "env -a name mkdir OUT/x",
        "mktemp -d", "awk -f prog.awk f", "sed -n -f s.sed f",
        "cat <<EOF\n$(touch OUT/x)\nEOF", "ls $(touch OUT/x)", "echo `rm OUT/x`", "cat <(touch OUT/x)",
        "if [ -e a ]; then rm OUT/x; fi",
        "env sort -oOUT/x f", "env tar -xf a.tar -COUT", "mkdir -p ../../outside", "printf x > ../raw/x",
        "cd sub && mkdir ../../x", "mkdir \"$PWD/../x\"", "mkdir $(pwd)/../x", "mkdir */../x", "cd $d && mkdir ../x",
        "sed -n 's/a/b/gw OUT/x' f", "sed -n '1!w OUT/x' f", "sed -n '/a/s//b/gw OUT/x' f",
        "awk 'BEGIN{print \"a;b\" > \"OUT/x\"}'", "awk 'BEGIN{print \"}\" > \"OUT/x\"}'",
        "awk 'BEGIN{print 1,\n 2 > \"OUT/x\"}'", "awk '{print \"a;b\" | \"tee OUT/x\"}' f",
        "env tar -xC.. -f a.tar", "env sort -ro../x f", "env sort -roOUT/x f", "cd nosuch; mkdir ../x",
        "cd sub | cat; mkdir ../x", "(cd sub && true); mkdir ../x", "awk -v o=OUT/x '/\"/ {print > o}' f",
        "awk '/\"/ {print > \"OUT/x\"}' f", "awk -v c='touch OUT/x' '/\"/ {system(c)}' f",
        "awk -v o=OUT/x '{print $1 ~ /\\(/ > o}' f",
    ]
    GIT_CONFIG = [
        "env git -c core.fsmonitor='touch x' status", "git -c include.path=$PROJECT/cfg status",
        "git -c color.ui=always status", "git --exec-path=helpers status",
    ]
    HARMLESS = ["awk '{print}' OUT/hosts", "cat OUT/hosts", "find OUT -name x -exec ls {} \\;", "sed -n '/w/p' f",
                "env sh -c 'touch x'", "mktemp -p .", "cat > f <<'EOF'\nmkdir OUT/x\nEOF", "cat '>' OUT/hosts",
                "ls\n# rm OUT/x", "if [ -e a ]; then wc -c a; fi",
                "mkdir -p ../auto-memory", "printf x > ../auto-memory/n.md", "cd ../auto-memory && mkdir -p sub",
                "[[ -f ../auto-memory/x && -s ../auto-memory/x ]] && echo ok", "awk '/system/ {print}' OUT/hosts",
                "sed -n 's/ w /x/p' OUT/f", "awk '{print \"a -> b\"}' OUT/f", "awk '{print ($1 > 3)}' OUT/f",
                "git log -c", "cd \"$(git rev-parse --show-toplevel)\" && printf hi > ../auto-memory/n.md",
                "awk '{gsub(/\"/, \"\"); print $1}' OUT/hosts", "sort -rn OUT/hosts", "env sort -n5 f"]

    def check_breach(self, run) -> None:
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        text = "\n".join(run.outcome.lines)
        self.assertIn("isolation or git breach: writes outside approved roots: 1", text, "fixed text with the count")
        self.assertNotIn(run.rig.base, text, "no path in the text")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s2.stdout")), "the raw bytes stay")
        for name in (SNAP_SETUP, SNAP_ONE, SNAP_TWO):
            self.assertTrue(os.path.isdir(os.path.join(run.run_root, "snaps", name)), "snapshot kept: " + name)
        self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")
        self.assertFalse(os.path.exists(os.path.join(raw, "s3.stdout")), "no third stage output")

    def run_of(self, command):
        return Run(pc_testutil.seed_bash_outside_write(
            pc_testutil.default_row1_stages(), 1, command.replace("OUT", "$OUTSIDE"), False))

    def test_every_escaping_form_ends_the_row_with_11_and_files_nothing(self) -> None:
        for command in self.ESCAPING:
            self.check_breach(self.run_of(command))

    def test_every_command_running_git_configuration_ends_the_row_with_11_and_a_git_mutations_line(self) -> None:
        for command in self.GIT_CONFIG:
            run = self.run_of(command)
            self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, command + ": " + "\n".join(run.outcome.lines))
            text = "\n".join(run.outcome.lines)
            self.assertRegex(text, r"isolation or git breach: git mutations: [1-9][0-9]*", "fixed text with the count")
            self.assertNotIn("writes outside approved roots", text, "no write line for " + command)
            self.assertNotIn(run.rig.base, text, "no path in the text")
            self.assertEqual(len(run.rig.calls()), 2, "no later stage was launched")
            self.assertFalse(os.path.exists(os.path.join(run.run_root, "raw", "s3.stdout")), "no third stage output")

    def test_the_harmless_forms_return_zero(self) -> None:
        for command in self.HARMLESS:
            run = self.run_of(command)
            self.assertEqual(run.outcome.code, 0, command + ": " + "\n".join(run.outcome.lines))


def lines(*items):
    """A multi-line command built with explicit newlines."""
    return "\n".join(items)


class ShellGrammarTests(OpenWorldBase):
    """Shell grammar read as the shell reads it (WR-02): quotes, heredocs, substitutions, comments, reserved words."""

    def check_zero(self, table, what):
        for number, command in enumerate(table):
            found = self.mentions(command)
            self.assertEqual(found["write_escapes"], {"count": 0, "programs": {}}, "%s zero case %d" % (what, number))

    def test_a_quoted_greater_than_is_a_word_and_an_unquoted_redirection_is_read_in_every_form(self) -> None:
        self.check_zero([
            "cat '>' OUT/hosts", "printf '%s\\n' '>' OUT/hosts", "awk -F '>' '{print $1}' OUT/hosts",
            "cat a > PRJ/f", "ls 2>&1", "ls >&2", "cat a > /dev/null", "cat a 2> /dev/null",
        ], "redirection")
        self.check_table([
            ("cat a > OUT/f", "redirect"), ("cat a >OUT/f", "redirect"), ("cat a 2>OUT/f", "redirect"),
            ("cat a >> OUT/f", "redirect"), ("cat a &> OUT/f", "redirect"), ("cat a >| OUT/f", "redirect"),
            ("cat a 2> OUT/f", "redirect"), ("cat a >>OUT/f", "redirect"),
        ], "redirection")

    def test_a_quoted_greater_than_makes_no_listed_redirect(self) -> None:
        found = self.mentions("cat '>' OUT/hosts")
        self.assertEqual(found["write_programs"], {}, "a read-only cat with a word that is only a greater-than sign")

    def test_the_body_of_a_quoted_delimiter_heredoc_is_data(self) -> None:
        self.check_zero([
            lines("cat > PRJ/f <<'EOF'", "mkdir OUT/x", "EOF"),
            lines("cat > PRJ/f <<\"EOF\"", "mkdir OUT/x", "EOF"),
            lines("cat > PRJ/f <<\\EOF", "mkdir OUT/x", "EOF"),
            lines("cat <<'EOF'", "$(rm OUT/x)", "EOF"),
            lines("cat <<'EOF'", "`rm OUT/x`", "EOF"),
        ], "quoted heredoc")

    def test_the_body_of_an_unquoted_delimiter_heredoc_is_scanned_for_substitutions(self) -> None:
        self.check_zero([
            lines("cat <<EOF", "mkdir OUT/x", "EOF"),
            lines("cat <<-EOF", "\tmkdir OUT/x", "\tEOF"),
            lines("cat <<A <<B", "mkdir OUT/x", "A", "rm OUT/y", "B"),
            lines("cat <<EOF", "price is \\$(rm OUT/x)", "EOF"),
        ], "unquoted heredoc with plain text")
        self.check_table([
            (lines("cat <<EOF", "$(rm OUT/x)", "EOF"), "rm"),
            (lines("cat <<EOF", "`rm OUT/x`", "EOF"), "rm"),
            (lines("cat <<-EOF", "\t$(touch OUT/x)", "\tEOF"), "touch"),
            (lines("cat <<A <<B", "plain", "A", "$(rm OUT/y)", "B"), "rm"),
        ], "unquoted heredoc with a substitution")

    def test_the_lines_after_the_closing_delimiter_are_judged(self) -> None:
        self.check_table([
            (lines("cat <<'EOF'", "body", "EOF", "rm OUT/x"), "rm"),
            (lines("cat > PRJ/f <<'EOF'", "mkdir OUT/x", "EOF", "touch OUT/y"), "touch"),
        ], "after the delimiter")

    def test_an_unterminated_heredoc_makes_the_command_unparsed(self) -> None:
        found = self.mentions(lines("cat <<EOF", "mkdir PRJ/x"))
        self.assertEqual(found["unparsed_parts"], 1, "counted as unparsed")
        self.assertEqual(found["write_escapes"]["count"], 0, "no escaping word")
        self.assertEqual(self.found(lines("cat <<EOF", "rm OUT/x")), {"count": 1, "programs": {"unparsed": 1}})

    def test_a_substitution_is_a_command_of_its_own(self) -> None:
        self.check_table([
            ("ls $(touch OUT/x)", "touch"),
            ("echo `rm OUT/x`", "rm"),
            ("cat <(touch OUT/x)", "touch"),
            ("echo \"$(touch OUT/x)\"", "touch"),
            ("echo $(echo $(rm OUT/x))", "rm"),
            ("d=$(mktemp -d)", "mktemp"),
        ], "substitution")
        self.check_zero([
            "ls $(ls OUT)", "echo \"$(ls OUT)\"", "echo '$(touch OUT/x)'",
        ], "substitution")

    def test_an_unbalanced_or_too_deep_substitution_makes_the_command_unparsed(self) -> None:
        self.assertEqual(self.found("echo $(rm OUT/x"), {"count": 1, "programs": {"unparsed": 1}}, "unbalanced and holding OUT")
        self.assertEqual(self.mentions("echo $(ls")["unparsed_parts"], 1, "unbalanced")
        deep = "echo " + "$(echo " * 6 + "x" + ")" * 6
        self.assertEqual(self.mentions(deep)["unparsed_parts"], 1, "nested over four levels")
        shallow = "echo " + "$(echo " * 3 + "x" + ")" * 3
        self.assertEqual(self.mentions(shallow)["unparsed_parts"], 0, "nested to a depth the rule reads")

    def test_a_comment_is_dropped_and_never_opens_a_quote(self) -> None:
        tilde = "~" + "/neutral-name"
        self.check_zero([
            lines("ls", "# it's " + tilde + " here", "wc -c f"),
            "# rm OUT/x",
            "ls # rm OUT/x",
            lines("ls", "# an apostrophe: don't", "wc -c f"),
        ], "comment")
        self.check_table([
            (lines("# a note", "rm OUT/x"), "rm"),
            (lines("ls # it's", "rm OUT/x"), "rm"),
            ("mkdir x#y OUT/z", "mkdir"),
            ("mkdir $# OUT/z", "mkdir"),
            ("mkdir \"x # y\" OUT/z", "mkdir"),
        ], "comment")

    def test_reserved_words_are_transparent_and_loop_headers_are_data(self) -> None:
        self.check_zero([
            "if [ -e ../auto-memory/x ]; then wc -c ../auto-memory/x; fi",
            "for f in OUT/a OUT/b; do ls $f; done",
            "while read l; do echo $l; done",
            "if ! test -e OUT/x; then echo no; fi",
            "[[ -e OUT/x ]] && echo yes",
            "{ ls; wc -c f; }",
            "case $x in a) ls;; esac",
        ], "reserved word")
        self.check_table([
            ("if [ -e a ]; then rm OUT/x; fi", "rm"),
            ("for f in a b; do touch OUT/x; done", "touch"),
            ("while true; do mkdir OUT/x; done", "mkdir"),
            ("case $x in a) rm OUT/x;; esac", "rm"),
            ("if [ -e a ]; then ls; else rm OUT/x; fi", "rm"),
        ], "reserved word")

    def test_the_old_redirection_reader_is_gone(self) -> None:
        self.assertFalse(hasattr(checks(), "_redirections"), "redirections are read from the raw text")


REFUSAL_PREFIXES = (
    "A variable", "A command used as a file", "A pipeline in this command", "Contains brace with quote character",
    "This command requires approval", "This Bash command contains multiple operations",
)
CONTROL_TRACE = os.path.join("publication-2026-10-20", "row10-large-status-first-pass", "s3-resume-full-trace.md")
CONTROL_CALL = 5
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tests", "evidence")


class WriteEscapeCorpusTests(OpenWorldBase):
    """The rule replayed over every committed full trace: zero write escapes among the commands that ran (WR-02)."""

    def trace_files(self):
        found = []
        for folder, _names, files in os.walk(EVIDENCE_DIR):
            found.extend(os.path.join(folder, name) for name in files if name.endswith("full-trace.md"))
        return sorted(found)

    def concrete(self, command: str) -> str:
        killswitch = "~" + "/killswitch-neutral"
        return (command.replace("<repo>/<run>", self.run).replace("<run>", self.run)
                .replace("<helper-killswitch>", killswitch))

    def judged(self, command: str):
        return checks().bash_mentions(stream([bash(self.concrete(command))]), self.approved, [self.wrapper])["write_escapes"]

    def walk(self):
        """Yield (trace name, call, kind) for every Bash call; kind is flagged, not-run or judged."""
        import pc_mine

        for path in self.trace_files():
            with open(path, "r", encoding="utf-8", newline="") as handle:
                calls = pc_mine.parse_trace(handle.read())
            name = os.path.relpath(path, EVIDENCE_DIR).replace(os.sep, "/")
            for call in calls:
                if call["refusal"]:
                    yield name, call, "flagged"
                elif call["result"].startswith(REFUSAL_PREFIXES):
                    yield name, call, "not-run"
                else:
                    yield name, call, "judged"

    def test_no_command_that_ran_in_a_committed_trace_is_a_write_escape(self) -> None:
        parsed = judged = 0
        first = None
        for name, call, kind in self.walk():
            parsed += 1
            if kind != "judged":
                continue
            judged += 1
            if first is None and self.judged(call["command"])["count"] != 0:
                first = "%s call %d" % (name, call["number"])
        self.assertGreaterEqual(len(self.trace_files()), 35, "full traces found")
        self.assertGreaterEqual(parsed, 348, "Bash calls parsed")
        self.assertGreaterEqual(judged, 231, "Bash calls judged")
        self.assertIsNone(first, "a command that ran is judged a write escape: %s" % first)

    def test_no_command_that_ran_in_a_committed_trace_is_a_git_mutation(self) -> None:
        commands = [call["command"] for _name, call, kind in self.walk() if kind == "judged"]
        self.assertGreaterEqual(len(commands), 231, "Bash calls judged")
        found = checks().git_mutations([], [self.concrete(command) for command in commands])
        self.assertEqual(found["executed"], 0, "an executed command is a git mutation, config-command included")
        self.assertEqual(found["forms"], [], "no form")

    def test_every_judged_or_not_run_memory_folder_command_of_the_traces_is_no_write_escape(self) -> None:
        found = 0
        failing = []
        for name, call, kind in self.walk():
            if kind == "flagged" or "../auto-memory" not in call["command"]:
                continue
            found += 1
            if self.judged(call["command"])["count"] != 0:
                failing.append("%s call %d" % (name, call["number"]))
        self.assertGreaterEqual(found, 9, "the memory-folder commands are found by text")
        self.assertEqual(failing, [], "a memory-folder command is judged a write escape")

    def test_the_refused_temporary_folder_write_is_not_judged_and_is_an_escape_when_handed_to_the_rule(self) -> None:
        control = [call for name, call, kind in self.walk()
                   if name == CONTROL_TRACE.replace(os.sep, "/") and call["number"] == CONTROL_CALL]
        self.assertEqual(len(control), 1, "the control call is in the corpus")
        kinds = [kind for name, call, kind in self.walk()
                 if name == CONTROL_TRACE.replace(os.sep, "/") and call["number"] == CONTROL_CALL]
        self.assertEqual(kinds, ["not-run"], "the walker skips it: the binary refused it, so it never ran")
        whole = self.judged(control[0]["command"])
        self.assertGreaterEqual(whole["programs"].get("mktemp", 0), 1, "the temporary folder made by a substitution")
        self.assertGreaterEqual(whole["programs"].get("rm", 0), 1, "the removal after the change to the root")
        self.assertEqual(self.judged("d=$(mktemp -d)")["programs"], {"mktemp": 1}, "the mktemp rule alone")
        self.assertEqual(self.judged("cd / && rm -r \"$d\"")["programs"], {"rm": 1}, "the rm after the cd alone")


class FailOpenInputTests(unittest.TestCase):
    def test_memory_probe_reads_absent_for_a_missing_path_and_for_a_parent_that_is_a_file(self) -> None:
        c = checks()
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-"))
        config = os.path.join(base, "config-folder")
        os.makedirs(config)
        project = os.path.join(base, "run", "project")
        os.makedirs(project)
        self.assertEqual(c.memory_probe(config, project), "absent", "a missing path")
        with open(os.path.join(config, "projects"), "w", encoding="utf-8") as handle:
            handle.write("a plain file where a folder should be")
        self.assertEqual(c.memory_probe(config, project), "absent", "a parent that is a plain file")
        os.makedirs(os.path.join(base, "other-config", "projects"))
        other = os.path.join(base, "other-config")
        os.makedirs(c.default_memory_path(other, project))
        self.assertEqual(c.memory_probe(other, project), "present", "a folder")

    def test_an_lstat_error_other_than_missing_is_a_check_error_with_no_path(self) -> None:
        c = checks()
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-"))
        with unittest.mock.patch("pc_checks.os.lstat", side_effect=PermissionError("planted")):
            with self.assertRaises(c.CheckError) as caught:
                c.memory_probe(os.path.join(base, "config-folder"), os.path.join(base, "project"))
        self.assertNotIn(base, str(caught.exception), "no path in the message")

    def test_a_run_whose_probe_raises_is_the_unreadable_line_with_11_and_files_nothing(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        real = os.lstat

        def fussy(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith(run.ctx.config_dir):
                raise PermissionError("planted")
            return real(path, *args, **kwargs)

        with unittest.mock.patch("os.lstat", fussy):
            outcome = pc_row1.breach_outcome(run.ctx, pc_row1.paths_for(run.run_root))
        self.assertEqual(outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "exit 11")
        self.assertEqual(tuple(outcome.lines), (pc_row1.MESSAGE_CHECKS_UNREADABLE,), "the fixed unreadable line")

    def test_a_missing_git_state_file_is_a_check_error_for_setup_and_for_a_recorded_stage(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        raw = os.path.join(run.run_root, "raw")
        for name in ("s2", "setup"):
            path = os.path.join(raw, name + ".git.json")
            os.rename(path, path + ".aside")
            try:
                with self.assertRaises(checks().CheckError, msg="missing state file of " + name):
                    run.facts()
            finally:
                os.rename(path + ".aside", path)
        self.assertEqual(sorted(run.facts()["stages"]), ["s1", "s2", "s3"], "the clean run still computes")


def make_guard(raw=None, snaps=None, size=0, sha=None, prefix="n/a") -> dict:
    return {"raw": dict(raw or {}), "snaps": dict(snaps or {}),
            "hooklog": {"size": size, "sha256": sha if sha is not None else digest("9"), "prefix_intact": prefix}}


class RunRecordGuardTests(unittest.TestCase):
    PREVIOUS_RAW = {"run.json": digest("1"), "s1.stdout": digest("2"), "s1.git.json": digest("3"), "setup.guard.json": digest("4")}
    PREVIOUS_SNAPS = {"snap-0-setup": digest("5"), "snap-1-after-work": digest("6")}

    def previous(self) -> dict:
        return make_guard(self.PREVIOUS_RAW, self.PREVIOUS_SNAPS, 100, digest("7"), "yes")

    def current(self, extra_raw=(), extra_snaps=(), prefix="yes", drop_raw=(), drop_snaps=(), change_raw=(), change_snaps=()):
        raw = dict(self.PREVIOUS_RAW)
        for name in extra_raw:
            raw[name] = digest("8")
        for name in drop_raw:
            raw.pop(name)
        for name in change_raw:
            raw[name] = digest("0")
        snaps = dict(self.PREVIOUS_SNAPS)
        for name in extra_snaps:
            snaps[name] = digest("8")
        for name in drop_snaps:
            snaps.pop(name)
        for name in change_snaps:
            snaps[name] = digest("0")
        return make_guard(raw, snaps, 250, digest("a"), prefix)

    S2_WINDOW = ("s1.record.json", "s1.guard.json", "s2.prompt", "s2.stdout", "s2.stderr", "s2.git.json")

    def test_what_the_harness_writes_in_a_window_and_a_grown_hook_log_are_no_violation(self) -> None:
        c = checks()
        grown = self.current(extra_raw=self.S2_WINDOW, extra_snaps=["snap-2-after-preclear"])
        self.assertEqual(c.guard_violations(self.previous(), grown, "s2"), [], "the s1 to s2 window")
        raw = dict(grown["raw"])
        snaps = dict(grown["snaps"])
        for name in ("s2.record.json", "s2.guard.json", "chain.json", "s3.prompt", "s3.stdout", "s3.stderr", "s3.git.json"):
            raw[name] = digest("8")
        snaps["snap-3-after-resume"] = digest("8")
        later = make_guard(raw, snaps, 300, digest("b"), "yes")
        self.assertEqual(c.guard_violations(grown, later, "s3"), [], "the s2 to s3 window adds chain.json")
        self.assertEqual(c.guard_violations(grown, make_guard(dict(raw, **{"s1.stdout": digest("0")}), snaps, 300,
                                                              digest("b"), "yes"), "s3"),
                         ["raw-entry-changed"], "an earlier stream that changed")

    def test_each_kind_of_change_is_one_violation_of_its_name(self) -> None:
        c = checks()
        previous = self.previous()
        cases = [
            (self.current(change_raw=["run.json"]), "raw-entry-changed"),
            (self.current(drop_raw=["run.json"]), "raw-entry-changed"),
            (self.current(extra_raw=["extra.txt"]), "raw-entry-unexpected"),
            (self.current(extra_raw=["s3.stdout"]), "raw-entry-unexpected"),
            (self.current(change_snaps=["snap-1-after-work"]), "snapshot-changed"),
            (self.current(drop_snaps=["snap-0-setup"]), "snapshot-changed"),
            (self.current(extra_snaps=["snap-9-extra"]), "snapshot-unexpected"),
            (self.current(prefix="no"), "hooklog-rewritten"),
        ]
        for number, (current, kind) in enumerate(cases):
            self.assertEqual(c.guard_violations(previous, current, "s2"), [kind], "violation case %d" % number)

    def test_the_names_are_the_documented_ones(self) -> None:
        c = checks()
        self.assertEqual(tuple(c.GUARD_ORDER), ("setup", "s1", "s2", "s3"), "the boundary order")
        self.assertEqual(c.BREACH_RECORD, "run-record-changes", "the breach id")

    def layout(self):
        base = os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-"))
        raw, snaps = os.path.join(base, "raw"), os.path.join(base, "snaps")
        os.makedirs(raw)
        os.makedirs(os.path.join(snaps, "snap-0-setup"))
        with open(os.path.join(raw, "run.json"), "w", encoding="utf-8") as handle:
            handle.write("{}\n")
        os.makedirs(os.path.join(raw, "sub"))
        with open(os.path.join(raw, "hooklog.jsonl"), "w", encoding="utf-8") as handle:
            handle.write("first line\n")
        with open(os.path.join(snaps, "snap-0-setup", "manifest.jsonl"), "w", encoding="utf-8") as handle:
            handle.write("")
        return {"raw": raw, "snaps": snaps}

    def test_capture_guard_lists_every_raw_file_but_the_hook_log_every_snapshot_tree_and_the_hook_log_state(self) -> None:
        import hashlib

        c = checks()
        paths = self.layout()
        c.capture_guard(paths, "setup")
        guard = read_json(os.path.join(paths["raw"], "setup.guard.json"))
        self.assertEqual(sorted(guard), ["hooklog", "raw", "snaps"], "the three parts")
        self.assertEqual(guard["raw"], {"run.json": hashlib.sha256(b"{}\n").hexdigest(), "sub": "dir"}, "raw without the log")
        expected = hashlib.sha256(manifest().jsonl_bytes(manifest().tree_manifest(os.path.join(paths["snaps"], "snap-0-setup")))).hexdigest()
        self.assertEqual(guard["snaps"], {"snap-0-setup": expected}, "the tree digest of the snapshot")
        self.assertEqual(guard["hooklog"], {"size": 11, "sha256": hashlib.sha256(b"first line\n").hexdigest(),
                                            "prefix_intact": "n/a"})
        with self.assertRaises(FileExistsError, msg="a second guard of the same name is refused"):
            c.capture_guard(paths, "setup")

    def test_a_boundary_after_setup_needs_the_previous_guard(self) -> None:
        paths = self.layout()
        with self.assertRaises(checks().CheckError):
            checks().capture_guard(paths, "s1")

    def test_the_prefix_flag_follows_the_hook_log_between_boundaries(self) -> None:
        c = checks()
        paths = self.layout()
        log = os.path.join(paths["raw"], "hooklog.jsonl")
        c.capture_guard(paths, "setup")
        with open(log, "a", encoding="utf-8") as handle:
            handle.write("second line\n")
        os.makedirs(os.path.join(paths["snaps"], "snap-1-after-work"))
        c.capture_guard(paths, "s1")
        self.assertEqual(read_json(os.path.join(paths["raw"], "s1.guard.json"))["hooklog"]["prefix_intact"], "yes", "grown")
        os.rename(log, log + ".aside")
        with open(log, "w", encoding="utf-8") as handle:
            handle.write("another long first line\nand more\n")
        c.capture_guard(paths, "s2")
        self.assertEqual(read_json(os.path.join(paths["raw"], "s2.guard.json"))["hooklog"]["prefix_intact"], "no", "rewritten")

    def test_a_shorter_or_missing_hook_log_is_not_intact(self) -> None:
        c = checks()
        for replacement in (None, "x\n"):
            paths = self.layout()
            log = os.path.join(paths["raw"], "hooklog.jsonl")
            c.capture_guard(paths, "setup")
            os.rename(log, log + ".aside")
            if replacement is not None:
                with open(log, "w", encoding="utf-8") as handle:
                    handle.write(replacement)
            c.capture_guard(paths, "s1")
            self.assertEqual(read_json(os.path.join(paths["raw"], "s1.guard.json"))["hooklog"]["prefix_intact"], "no")

    def test_load_guard_is_strict(self) -> None:
        c = checks()
        raw = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="pc-checks-")), "raw")
        os.makedirs(raw)
        good = make_guard({"a": digest("1"), "d": "dir"}, {"snap-0-setup": digest("2")}, 3, digest("3"), "n/a")
        bad = [
            "not json",
            [1],
            dict(good, extra=1),
            dict((k, v) for k, v in good.items() if k != "snaps"),
            dict(good, raw={"a": "ABC"}),
            dict(good, raw={"a": digest("1").upper()}),
            dict(good, snaps={"s": 5}),
            dict(good, hooklog=dict(good["hooklog"], size=True)),
            dict(good, hooklog=dict(good["hooklog"], size=-1)),
            dict(good, hooklog=dict(good["hooklog"], sha256="abc")),
            dict(good, hooklog=dict(good["hooklog"], prefix_intact="maybe")),
            dict(good, hooklog={"size": 1}),
        ]
        with open(os.path.join(raw, "setup.guard.json"), "w", encoding="utf-8") as handle:
            json.dump(good, handle)
        self.assertEqual(c.load_guard(raw, "setup"), good, "a good guard is read")
        for number, value in enumerate(bad):
            with open(os.path.join(raw, "s1.guard.json"), "w", encoding="utf-8") as handle:
                if isinstance(value, str):
                    handle.write(value)
                else:
                    json.dump(value, handle)
            with self.assertRaises(c.CheckError, msg="bad guard case %d" % number):
                c.load_guard(raw, "s1")
        with self.assertRaises(c.CheckError, msg="a missing guard file"):
            c.load_guard(raw, "s3")


class RunRecordRunTests(unittest.TestCase):
    def test_a_clean_run_has_four_guard_files_and_a_guard_fact_of_zero(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        self.assertEqual(run.outcome.code, 0, "\n".join(run.outcome.lines))
        for name in ("setup", "s1", "s2", "s3"):
            self.assertTrue(os.path.isfile(os.path.join(run.run_root, "raw", name + ".guard.json")), "guard of " + name)
        facts = run.facts()
        self.assertEqual(facts["guard"], {"count": 0, "kinds": {}}, "the hook's own appends are no violation")
        self.assertGreater(read_json(os.path.join(run.run_root, "raw", "s3.guard.json"))["hooklog"]["size"], 0, "the log grew")

    def test_breaches_adds_the_record_changes_when_the_count_is_above_zero(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        facts = run.facts()
        self.assertEqual(checks().breaches(facts), [], "none for a clean run")
        facts = dict(facts, guard={"count": 3, "kinds": {"raw-entry-changed": 3}})
        self.assertEqual(checks().breaches(facts), [("run-record-changes", 3)], "the id and the count")

    def check_tamper(self, kind: str) -> None:
        run = Run(pc_testutil.seed_run_record_tamper(pc_testutil.default_row1_stages(), kind))
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, kind + ": " + "\n".join(run.outcome.lines))
        text = "\n".join(run.outcome.lines)
        self.assertRegex(text, r"isolation or git breach: changes to the run's own record files: [1-9][0-9]*", kind)
        self.assertNotIn(run.rig.base, text, kind + ": no path in the text")
        raw = os.path.join(run.run_root, "raw")
        self.assertTrue(os.path.isfile(os.path.join(raw, "s2.stdout")), kind + ": the raw bytes stay")
        self.assertFalse(os.path.exists(os.path.join(raw, "s3.stdout")), kind + ": no third stage")
        self.assertEqual(len(run.rig.calls()), 2, kind + ": no later stage was launched")
        self.assertFalse(os.path.lexists(run.ctx.destination), kind + ": nothing was filed")

    def test_a_rewritten_hook_log_ends_the_row_with_11(self) -> None:
        self.check_tamper("hooklog")

    def test_a_replaced_stage_record_ends_the_row_with_11(self) -> None:
        self.check_tamper("record")

    def test_an_extra_raw_file_ends_the_row_with_11(self) -> None:
        self.check_tamper("extra")

    def test_an_emptied_snapshot_manifest_ends_the_row_with_11(self) -> None:
        self.check_tamper("snapshot")

    def test_the_seed_refuses_an_unknown_kind(self) -> None:
        with self.assertRaises(ValueError):
            pc_testutil.seed_run_record_tamper(pc_testutil.default_row1_stages(), "other")

    def test_a_model_made_stage_prefixed_folder_is_listed_as_a_write_outside_the_roots(self) -> None:
        stages = with_extra_ops(pc_testutil.default_row1_stages(), 1, [
            {"op": "write", "path": "$RUN/stage-9/x.txt", "text": "a model-made folder\n"}])
        run = Run(stages)
        self.assertEqual(run.outcome.code, pc_exitcodes.PREFLIGHT_FAIL, "\n".join(run.outcome.lines))
        facts = run.facts()
        self.assertIn("stage-9/x.txt", facts["write_boundary"]["paths"], "the file is listed")
        self.assertGreaterEqual(facts["write_boundary"]["count"], 1, "and counted")

    def test_a_missing_guard_file_is_a_check_error(self) -> None:
        run = Run(pc_testutil.default_row1_stages())
        path = os.path.join(run.run_root, "raw", "s2.guard.json")
        os.rename(path, path + ".aside")
        try:
            with self.assertRaises(checks().CheckError):
                run.facts()
        finally:
            os.rename(path + ".aside", path)
        self.assertEqual(run.facts()["guard"]["count"], 0, "back in place, the run reads clean")


if __name__ == "__main__":
    unittest.main()
