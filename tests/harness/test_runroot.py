"""Tests for pc_runroot: exclusive run-root allocation and exclusive creation helpers.

Scratch directories come from tempfile.mkdtemp under the system temp directory. The
tests never delete them and never print their paths (failure messages carry labels
only). Names that cannot be typed safely are built from code points at run time.
"""
from __future__ import annotations

import ast
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
RUNROOT_CLI = os.path.join(HARNESS_DIR, "pc_runroot.py")

import pc_runroot  # noqa: E402  (the harness folder is on sys.path via discovery)


def run_cli(*args):
    """Run the allocator CLI the way a stranger would: python3 -E -s -B script args."""
    return subprocess.run(
        [sys.executable, "-E", "-s", "-B", RUNROOT_CLI] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class HarnessTestCase(unittest.TestCase):
    """Shared helpers. Messages never include a path value."""

    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)

    @classmethod
    def fresh_parent(cls):
        # Never deleted, never printed (HARN-03: the harness removes nothing).
        return tempfile.mkdtemp(prefix="preclear-rr-")


class AllocateRunRootTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_first_allocation_creates_a_private_directory_and_returns_its_realpath(self):
        created = pc_runroot.allocate_run_root(self.parent, "run-first")
        expected = os.path.realpath(os.path.join(self.parent, "run-first"))
        self.ok(created == expected, "returned path is the realpath of the new directory")
        self.ok(os.path.isdir(created), "the run root exists as a directory")
        mode = stat.S_IMODE(os.stat(created).st_mode)
        self.ok(mode == 0o700, "the run root is owner-only (0o700)")

    def test_second_allocation_of_same_name_raises_collision(self):
        pc_runroot.allocate_run_root(self.parent, "run-twice")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "run-twice")

    def test_collision_is_a_run_root_error(self):
        self.ok(issubclass(pc_runroot.RunRootCollision, pc_runroot.RunRootError), "collision subclasses RunRootError")

    def test_existing_regular_file_is_a_collision_and_is_left_alone(self):
        path = os.path.join(self.parent, "taken-by-file")
        with open(path, "xb") as handle:
            handle.write(b"keep me")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "taken-by-file")
        with open(path, "rb") as handle:
            self.ok(handle.read() == b"keep me", "the existing file is untouched")

    def test_symlink_to_existing_directory_is_a_collision(self):
        target = os.path.join(self.parent, "link-target-dir")
        os.mkdir(target)
        os.symlink(target, os.path.join(self.parent, "link-to-dir"))
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "link-to-dir")

    def test_dangling_symlink_is_a_collision(self):
        os.symlink("no-such-target-anywhere", os.path.join(self.parent, "dangling"))
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent, "dangling")
        self.ok(os.path.islink(os.path.join(self.parent, "dangling")), "the dangling link is untouched")

    def test_parent_with_trailing_separator_reaches_the_same_entry(self):
        pc_runroot.allocate_run_root(self.parent, "run-trailing")
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(self.parent + os.sep, "run-trailing")

    def test_symlinked_parent_resolves_to_the_existing_entry(self):
        real_parent = self.fresh_parent()
        pc_runroot.allocate_run_root(real_parent, "run-via-link")
        link_parent = os.path.join(self.parent, "parent-link")
        os.symlink(real_parent, link_parent)
        with self.assertRaises(pc_runroot.RunRootCollision):
            pc_runroot.allocate_run_root(link_parent, "run-via-link")

    def test_sibling_that_only_shares_a_name_prefix_is_allowed(self):
        pc_runroot.allocate_run_root(self.parent, "run-prefix")
        sibling = pc_runroot.allocate_run_root(self.parent, "run-prefix-2")
        shorter = pc_runroot.allocate_run_root(self.parent, "run-pre")
        self.ok(os.path.isdir(sibling) and os.path.isdir(shorter), "prefix siblings are created")

    def test_name_of_exactly_255_bytes_is_accepted(self):
        created = pc_runroot.allocate_run_root(self.parent, "n" * 255)
        self.ok(os.path.isdir(created), "a 255-byte name is a valid run root name")


class InvalidNameTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def assert_refused_before_creation(self, name, label):
        before = sorted(os.listdir(self.parent))
        with self.assertRaises(pc_runroot.RunRootError) as caught:
            pc_runroot.allocate_run_root(self.parent, name)
        self.ok(
            not isinstance(caught.exception, pc_runroot.RunRootCollision),
            label + ": refused as an invalid name, not as a collision",
        )
        self.ok(sorted(os.listdir(self.parent)) == before, label + ": nothing was created")

    def test_empty_name(self):
        self.assert_refused_before_creation("", "empty")

    def test_dot_and_dot_dot(self):
        self.assert_refused_before_creation(".", "dot")
        self.assert_refused_before_creation("..", "dot-dot")

    def test_names_holding_a_separator(self):
        self.assert_refused_before_creation("a" + os.sep + "b", "inner separator")
        self.assert_refused_before_creation("a" + os.sep, "trailing separator")
        self.assert_refused_before_creation(os.sep + "a", "leading separator")

    def test_name_holding_a_nul(self):
        self.assert_refused_before_creation("a" + chr(0) + "b", "NUL")

    def test_name_over_255_utf8_bytes(self):
        self.assert_refused_before_creation("n" * 256, "256 ASCII bytes")
        # 128 two-byte letters are 128 characters but 256 bytes.
        self.assert_refused_before_creation(chr(0xE9) * 128, "256 bytes in 128 characters")

    def test_name_that_cannot_be_encoded_as_utf8(self):
        self.assert_refused_before_creation("bad" + chr(0xDCFF), "lone surrogate")

    def test_missing_parent(self):
        missing = os.path.join(self.parent, "no-such-parent")
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.allocate_run_root(missing, "run-x")
        self.ok(not os.path.exists(missing), "the missing parent was not created")

    def test_parent_that_is_a_file(self):
        path = os.path.join(self.parent, "parent-is-a-file")
        with open(path, "xb"):
            pass
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.allocate_run_root(path, "run-x")


class ExclusiveHelperTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_exclusive_dir_creates_with_the_given_mode_and_refuses_a_second_call(self):
        path = os.path.join(self.parent, "dir-a")
        self.ok(pc_runroot.exclusive_dir(path, 0o700) is None, "exclusive_dir returns None")
        self.ok(os.path.isdir(path), "the directory exists")
        self.ok(stat.S_IMODE(os.stat(path).st_mode) == 0o700, "mode applied")
        with self.assertRaises(FileExistsError):
            pc_runroot.exclusive_dir(path, 0o700)

    def test_write_exclusive_writes_all_bytes_and_refuses_an_existing_file(self):
        path = os.path.join(self.parent, "file-a")
        payload = bytes(range(256)) * 300
        pc_runroot.write_exclusive(path, payload, 0o600)
        with open(path, "rb") as handle:
            self.ok(handle.read() == payload, "every byte was written")
        self.ok(stat.S_IMODE(os.stat(path).st_mode) == 0o600, "mode applied")
        with self.assertRaises(FileExistsError):
            pc_runroot.write_exclusive(path, b"other", 0o600)
        with open(path, "rb") as handle:
            self.ok(handle.read() == payload, "the existing file was not overwritten")

    def test_write_exclusive_refuses_a_dangling_symlink_and_does_not_follow_it(self):
        link = os.path.join(self.parent, "file-link")
        victim = os.path.join(self.parent, "file-link-victim")
        os.symlink(victim, link)
        with self.assertRaises(FileExistsError):
            pc_runroot.write_exclusive(link, b"data", 0o600)
        self.ok(not os.path.exists(victim), "the link target was not created through the link")


class CliTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_first_allocation_prints_the_path_and_exits_0(self):
        result = run_cli(self.parent, "cli-run-a")
        self.ok(result.returncode == 0, "first allocation exits 0")
        printed = result.stdout.decode("utf-8").strip()
        self.ok(printed == os.path.realpath(os.path.join(self.parent, "cli-run-a")), "stdout is the created realpath")
        self.ok(os.path.isdir(printed), "the printed directory exists")

    def test_second_allocation_of_the_same_name_exits_16(self):
        first = run_cli(self.parent, "cli-run-b")
        self.ok(first.returncode == 0, "first allocation exits 0")
        second = run_cli(self.parent, "cli-run-b")
        self.ok(second.returncode == 16, "collision exits 16")
        self.ok(b"run root collision" in second.stderr, "stderr names the collision")
        self.ok(second.stdout == b"", "nothing is printed to stdout on a collision")

    def test_invalid_name_and_missing_parent_and_bad_usage_exit_2(self):
        before = sorted(os.listdir(self.parent))
        self.ok(run_cli(self.parent, "..").returncode == 2, "dot-dot exits 2")
        self.ok(run_cli(self.parent, "a" + os.sep + "b").returncode == 2, "separator exits 2")
        self.ok(run_cli(self.parent, "a" + os.sep).returncode == 2, "trailing separator exits 2")
        self.ok(run_cli(os.path.join(self.parent, "nope"), "x").returncode == 2, "missing parent exits 2")
        self.ok(run_cli().returncode == 2, "no arguments exits 2")
        self.ok(run_cli(self.parent).returncode == 2, "one argument exits 2")
        self.ok(sorted(os.listdir(self.parent)) == before, "no run root was created by a refusal")


def make_source_tree():
    """A small tree: nested folders, an executable file, a plain file, a CJK-named file."""
    src = tempfile.mkdtemp(prefix="preclear-src-")
    os.mkdir(os.path.join(src, "nested"))
    os.mkdir(os.path.join(src, "nested", "deeper"))
    os.mkdir(os.path.join(src, "empty-dir"))
    with open(os.path.join(src, "plain.txt"), "xb") as handle:
        handle.write(b"plain\n")
    with open(os.path.join(src, "nested", "run.sh"), "xb") as handle:
        handle.write(b"#!/bin/sh\nexit 0\n")
    os.chmod(os.path.join(src, "nested", "run.sh"), 0o755)
    with open(os.path.join(src, "nested", "deeper", chr(0x6587) + chr(0x4EF6) + ".txt"), "xb") as handle:
        handle.write(b"cjk name\n")
    return src


def tree_listing(root):
    """Sorted (relative path, kind, bytes-or-None) triples for comparing two trees."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames:
            out.append((os.path.relpath(os.path.join(dirpath, name), root), "d", None))
        for name in filenames:
            full = os.path.join(dirpath, name)
            with open(full, "rb") as handle:
                out.append((os.path.relpath(full, root), "f", handle.read()))
    return sorted(out)


class CopyTreeExclusiveTests(HarnessTestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = cls.fresh_parent()

    def test_copies_a_tree_keeps_the_executable_bit_and_returns_the_file_count(self):
        src = make_source_tree()
        dst = os.path.join(self.parent, "copy-ok")
        count = pc_runroot.copy_tree_exclusive(src, dst)
        self.ok(count == 3, "three files were copied")
        self.ok(tree_listing(dst) == tree_listing(src), "the copy has the same folders, files and bytes")
        run_mode = stat.S_IMODE(os.stat(os.path.join(dst, "nested", "run.sh")).st_mode)
        plain_mode = stat.S_IMODE(os.stat(os.path.join(dst, "plain.txt")).st_mode)
        self.ok(run_mode == 0o755, "an executable source file stays executable (0o755)")
        self.ok(plain_mode == 0o644, "a plain source file is 0o644")
        self.ok(os.path.isdir(os.path.join(dst, "empty-dir")), "an empty folder is copied")

    def test_an_existing_destination_is_refused_and_left_alone(self):
        src = make_source_tree()
        dst = os.path.join(self.parent, "copy-exists")
        os.mkdir(dst)
        with open(os.path.join(dst, "keep.txt"), "xb") as handle:
            handle.write(b"keep")
        with self.assertRaises(FileExistsError):
            pc_runroot.copy_tree_exclusive(src, dst)
        self.ok(os.listdir(dst) == ["keep.txt"], "the existing destination holds only what it held")

    def test_a_destination_that_is_a_dangling_symlink_is_refused(self):
        src = make_source_tree()
        dst = os.path.join(self.parent, "copy-dangling")
        os.symlink("no-such-target-anywhere", dst)
        with self.assertRaises(FileExistsError):
            pc_runroot.copy_tree_exclusive(src, dst)

    def test_a_symlink_inside_the_source_is_refused_before_anything_is_created(self):
        src = make_source_tree()
        os.symlink("plain.txt", os.path.join(src, "link-inside"))
        dst = os.path.join(self.parent, "copy-symlink")
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.copy_tree_exclusive(src, dst)
        self.ok(not os.path.lexists(dst), "no destination was created")

    def test_a_special_file_inside_the_source_is_refused(self):
        src = make_source_tree()
        os.mkfifo(os.path.join(src, "pipe-inside"))
        dst = os.path.join(self.parent, "copy-fifo")
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.copy_tree_exclusive(src, dst)
        self.ok(not os.path.lexists(dst), "no destination was created")

    def test_a_symlinked_source_root_or_a_missing_source_is_refused(self):
        src = make_source_tree()
        link = os.path.join(self.parent, "src-link")
        os.symlink(src, link)
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.copy_tree_exclusive(link, os.path.join(self.parent, "copy-from-link"))
        with self.assertRaises(pc_runroot.RunRootError):
            pc_runroot.copy_tree_exclusive(os.path.join(self.parent, "no-such-src"), os.path.join(self.parent, "copy-x"))
        self.ok(not os.path.lexists(os.path.join(self.parent, "copy-from-link")), "nothing created for a symlinked source")

    def test_an_empty_source_copies_zero_files(self):
        src = tempfile.mkdtemp(prefix="preclear-src-")
        dst = os.path.join(self.parent, "copy-empty")
        self.ok(pc_runroot.copy_tree_exclusive(src, dst) == 0, "zero files copied")
        self.ok(os.path.isdir(dst) and os.listdir(dst) == [], "an empty destination folder exists")


# ---------------------------------------------------------------------------
# HARN-03: static scan. No harness module deletes, renames, moves or overwrites.
# ---------------------------------------------------------------------------

# The two test-support modules may do what the scan forbids (they build and tear down
# test scenarios); every other pc_ module is scanned. The set is asserted exactly below so
# it cannot grow silently.
SCAN_EXEMPT = frozenset(["pc_testutil.py", "pc_seeds.py"])

FORBIDDEN_DOTTED = frozenset([
    "os.remove", "os.unlink", "os.rmdir", "os.removedirs", "os.rename", "os.renames", "os.replace",
    "os.truncate", "os.ftruncate",
    "shutil.rmtree", "shutil.move", "shutil.copy", "shutil.copy2", "shutil.copyfile", "shutil.copytree",
])
FORBIDDEN_METHODS = frozenset(["unlink", "rmdir", "rename", "write_text", "write_bytes"])
FORBIDDEN_FROM_IMPORTS = {
    "os": frozenset(name.split(".")[1] for name in FORBIDDEN_DOTTED if name.startswith("os.")),
    "shutil": frozenset(name.split(".")[1] for name in FORBIDDEN_DOTTED if name.startswith("shutil.")),
}


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def scan_source(source):
    """Return a list of labels, one per forbidden construct found in SOURCE (Python text)."""
    tree = ast.parse(source)
    aliases = {}
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_FROM_IMPORTS:
            for item in node.names:
                if item.name in FORBIDDEN_FROM_IMPORTS[node.module]:
                    findings.append("imports %s.%s" % (node.module, item.name))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "O_TRUNC":
            findings.append("mentions O_TRUNC")
        if isinstance(node, ast.Attribute) and node.attr == "O_TRUNC":
            findings.append("mentions O_TRUNC")
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        dotted = _dotted(func)
        if dotted is not None:
            head, _, rest = dotted.partition(".")
            resolved = aliases.get(head, head) + ("." + rest if rest else "")
        else:
            resolved = None
        if resolved in FORBIDDEN_DOTTED:
            findings.append("calls %s" % resolved)
        elif isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_METHODS:
            findings.append("calls .%s" % func.attr)
        elif isinstance(func, ast.Attribute) and func.attr == "replace" and len(node.args) + len(node.keywords) < 2:
            # str.replace and bytes.replace take two arguments; a one-argument replace is Path.replace.
            findings.append("calls one-argument .replace")
        # Builtin or io open with a truncating write mode.
        is_open = (isinstance(func, ast.Name) and func.id == "open") or resolved in ("io.open", "codecs.open", "os.fdopen")
        is_path_open = isinstance(func, ast.Attribute) and func.attr == "open" and resolved not in ("io.open", "codecs.open")
        if is_open or is_path_open:
            mode_node = None
            index = 0 if is_path_open else 1
            if len(node.args) > index:
                mode_node = node.args[index]
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode_node = keyword.value
            mode = _const_str(mode_node) if mode_node is not None else None
            if mode is not None and "w" in mode:
                findings.append("opens a file in a truncating write mode")
    return findings


def harness_modules():
    names = sorted(n for n in os.listdir(HARNESS_DIR) if n.startswith("pc_") and n.endswith(".py"))
    return [n for n in names if n not in SCAN_EXEMPT]


class NoDeleteOrOverwriteScanTests(HarnessTestCase):
    def test_the_exemption_set_is_exactly_the_two_test_support_modules(self):
        self.ok(SCAN_EXEMPT == frozenset(["pc_testutil.py", "pc_seeds.py"]), "exemption set is exactly pc_testutil.py and pc_seeds.py")

    def test_the_scan_covers_the_modules_of_this_plan(self):
        modules = harness_modules()
        for needed in ("pc_runroot.py", "pc_manifest.py", "pc_measure.py"):
            self.ok(needed in modules, needed + " is scanned")

    def test_no_scanned_module_holds_a_delete_rename_move_or_overwrite_construct(self):
        for name in harness_modules():
            with open(os.path.join(HARNESS_DIR, name), "rb") as handle:
                findings = scan_source(handle.read())
            self.ok(findings == [], "%s: %s" % (name, "; ".join(sorted(set(findings)))))

    def test_the_scanner_flags_every_forbidden_construct(self):
        cases = {
            "import os\nos.remove(p)\n": "calls os.remove",
            "import os\nos.unlink(p)\n": "calls os.unlink",
            "import os\nos.rmdir(p)\n": "calls os.rmdir",
            "import os\nos.removedirs(p)\n": "calls os.removedirs",
            "import os\nos.rename(a, b)\n": "calls os.rename",
            "import os\nos.renames(a, b)\n": "calls os.renames",
            "import os\nos.replace(a, b)\n": "calls os.replace",
            "import shutil\nshutil.rmtree(p)\n": "calls shutil.rmtree",
            "import shutil\nshutil.move(a, b)\n": "calls shutil.move",
            "import shutil\nshutil.copy(a, b)\n": "calls shutil.copy",
            "import shutil\nshutil.copy2(a, b)\n": "calls shutil.copy2",
            "import shutil\nshutil.copyfile(a, b)\n": "calls shutil.copyfile",
            "import shutil\nshutil.copytree(a, b)\n": "calls shutil.copytree",
            "import os as o\no.remove(p)\n": "calls os.remove",
            "import shutil as sh\nsh.rmtree(p)\n": "calls shutil.rmtree",
            "from os import remove\nremove(p)\n": "imports os.remove",
            "from shutil import rmtree\nrmtree(p)\n": "imports shutil.rmtree",
            "from pathlib import Path\nPath(p).unlink()\n": "calls .unlink",
            "from pathlib import Path\nPath(p).rmdir()\n": "calls .rmdir",
            "from pathlib import Path\nPath(p).rename(q)\n": "calls .rename",
            "from pathlib import Path\nPath(p).replace(q)\n": "calls one-argument .replace",
            "from pathlib import Path\nPath(p).write_text('x')\n": "calls .write_text",
            "from pathlib import Path\nPath(p).write_bytes(b'x')\n": "calls .write_bytes",
            "open(p, 'w')\n": "opens a file in a truncating write mode",
            "open(p, 'wb')\n": "opens a file in a truncating write mode",
            "open(p, mode='w+')\n": "opens a file in a truncating write mode",
            "from pathlib import Path\nPath(p).open('w')\n": "opens a file in a truncating write mode",
            "import os\nos.open(p, os.O_WRONLY | os.O_TRUNC)\n": "mentions O_TRUNC",
            "from os import O_TRUNC\nx = O_TRUNC\n": "mentions O_TRUNC",
            "import os\nos.truncate(p, 0)\n": "calls os.truncate",
        }
        for source, label in cases.items():
            self.ok(label in scan_source(source), "scanner flags: " + label)

    def test_the_scanner_passes_constructs_the_harness_is_allowed_to_use(self):
        allowed = (
            "import os\nos.mkdir(p, 0o700)\n",
            "import os\nfd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)\n",
            "open(p, 'rb')\n",
            "open(p, 'xb')\n",
            "open(p)\n",
            "x = text.replace('a', 'b')\n",
            "x = data.replace(b'a', b'b')\n",
            "import os\nos.path.join(a, b)\n",
            "import os\nos.fsync(fd)\n",
        )
        for source in allowed:
            self.ok(scan_source(source) == [], "scanner accepts: " + source.splitlines()[-1])


class ModuleSurfaceTests(HarnessTestCase):
    def test_pc_runroot_defines_only_creation_helpers(self):
        with open(os.path.join(HARNESS_DIR, "pc_runroot.py"), "rb") as handle:
            tree = ast.parse(handle.read())
        public = set(
            node.name for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        )
        allowed = set(["allocate_run_root", "exclusive_dir", "write_exclusive", "copy_tree_exclusive", "main"])
        self.ok(public == allowed, "public functions are exactly the creation helpers and main")


if __name__ == "__main__":
    unittest.main()
