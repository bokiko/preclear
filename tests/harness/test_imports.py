"""Hygiene tests for the harness folder itself (HARN-14; D-11, D-12).

The harness must need nothing beyond Claude Code, git and Python 3. These tests scan every
Python file under tests/harness, tests included, and check four things:

  * every import is the standard library (classified by where the module lives under the
    running interpreter, not by a name list), a sibling harness module, or a built-in;
  * nothing needs Python 3.10 or later that a parse can see (feature version 3.9, no tomllib,
    no stdlib_module_names, no zip with strict, no parenthesized multi-item with);
  * no harness module stem equals a standard-library module name, because the folder is first
    on sys.path during discovery and a same-named file would shadow the real module;
  * the naming rule: library modules start with pc_, tests with test_, and checkpoint_stub is
    the one exception and a single file that imports no sibling.

Parsing with feature version 3.9 is a partial guard only: it still accepts some newer
constructs. The real proof of the 3.9 floor is running the whole suite under a 3.9 interpreter.
Failure messages name a file by its name inside the folder and a module by its name, never a
path.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import sys
import sysconfig
import tempfile
import unittest
from typing import Dict, List, Optional, Set

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))

# Spelled in pieces so that a plain-text search for these names does not hit this file.
FORBIDDEN_MODULE = "tom" + "llib"
FORBIDDEN_ATTRIBUTE = "stdlib_" + "module_names"
UNSUPPORTED_ZIP_KEYWORD = "str" + "ict"

NAMING_EXCEPTION = "checkpoint_stub"
TEST_SUPPORT_STEMS = ("pc_testutil", "pc_seeds")


def python_files(folder: str) -> List[str]:
    """Return every .py file under folder as a path relative to it, sorted, caches excluded."""
    found: List[str] = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(name for name in dirnames if name != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".py"):
                found.append(os.path.relpath(os.path.join(dirpath, name), folder))
    return sorted(found)


def harness_stems(folder: str) -> Set[str]:
    """Return the stems of the Python modules that sit directly in folder."""
    return {name[:-3] for name in os.listdir(folder) if name.endswith(".py")}


_STDLIB_ROOTS: Optional[Set[str]] = None


def _stdlib_roots() -> Set[str]:
    global _STDLIB_ROOTS
    if _STDLIB_ROOTS is None:
        paths = sysconfig.get_paths()
        _STDLIB_ROOTS = {os.path.realpath(paths[key]) for key in ("stdlib", "platstdlib")}
    return _STDLIB_ROOTS


def is_stdlib(top: str) -> bool:
    """Classify a top-level module name by origin (3.9-safe, no stdlib name list)."""
    if top in sys.builtin_module_names:
        return True
    try:
        spec = importlib.util.find_spec(top)
    except (ImportError, ValueError, AttributeError):
        return False
    if spec is None:
        return False
    if spec.origin in ("built-in", "frozen"):
        return True
    if spec.origin and spec.origin != "namespace":
        location = spec.origin
    elif spec.submodule_search_locations:
        location = list(spec.submodule_search_locations)[0]
    else:
        return False
    real = os.path.realpath(location)
    if "site-packages" in real or "dist-packages" in real:
        return False
    return any(real == root or real.startswith(root + os.sep) for root in _stdlib_roots())


def stdlib_names() -> Set[str]:
    """Return standard-library module names read from the interpreter's own directories."""
    names: Set[str] = set(sys.builtin_module_names)
    paths = sysconfig.get_paths()
    folders = {paths["stdlib"], paths["platstdlib"]}
    for folder in list(folders):
        folders.add(os.path.join(folder, "lib-dynload"))
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for entry in os.listdir(folder):
            if entry in ("site-packages", "dist-packages", "__pycache__"):
                continue
            full = os.path.join(folder, entry)
            if os.path.isdir(full):
                names.add(entry)
            elif entry.endswith(".py"):
                names.add(entry[:-3])
            elif entry.endswith((".so", ".pyd", ".dylib")):
                names.add(entry.split(".")[0])
    return names


def imported_top_levels(tree: ast.AST) -> Dict[str, int]:
    """Return {top-level module name: first line} for every absolute import in the tree."""
    found: Dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.setdefault(alias.name.split(".")[0], node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.setdefault(node.module.split(".")[0], node.lineno)
    return found


def scan_source(source: str, name: str, local_stems: Set[str]) -> List[str]:
    """Return one message per problem in source; name is the file's name inside the folder."""
    try:
        tree = ast.parse(source, filename=name, feature_version=(3, 9))
    except SyntaxError as error:
        return ["%s: does not parse as Python 3.9 (%s)" % (name, error.msg)]
    problems: List[str] = []
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            problems.append("%s line %d: relative import" % (name, node.lineno))
        if isinstance(node, ast.Attribute) and node.attr == FORBIDDEN_ATTRIBUTE:
            problems.append("%s line %d: reads %s (3.10 or later)" % (name, node.lineno, FORBIDDEN_ATTRIBUTE))
        if isinstance(node, ast.Name) and node.id == FORBIDDEN_ATTRIBUTE:
            problems.append("%s line %d: names %s (3.10 or later)" % (name, node.lineno, FORBIDDEN_ATTRIBUTE))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "zip"
            and any(keyword.arg == UNSUPPORTED_ZIP_KEYWORD for keyword in node.keywords)
        ):
            problems.append("%s line %d: zip with a %s keyword (3.10 or later)" % (name, node.lineno, UNSUPPORTED_ZIP_KEYWORD))
        if isinstance(node, ast.With) and len(node.items) > 1 and 0 < node.lineno <= len(lines):
            after_keyword = lines[node.lineno - 1][node.col_offset + len("with"):].lstrip()
            if after_keyword.startswith("("):
                problems.append("%s line %d: parenthesized multi-item with (3.10 or later)" % (name, node.lineno))
    for top, line in sorted(imported_top_levels(tree).items(), key=lambda item: item[1]):
        if top == FORBIDDEN_MODULE:
            problems.append("%s line %d: imports %s (3.11 or later)" % (name, line, top))
        elif top in local_stems and not is_stdlib(top):
            continue
        elif not is_stdlib(top):
            problems.append("%s line %d: imports %s, which is not standard library or a sibling module" % (name, line, top))
    return problems


def scan_folder(folder: str) -> List[str]:
    local = harness_stems(folder)
    problems: List[str] = []
    for relative in python_files(folder):
        with open(os.path.join(folder, relative), "r", encoding="utf-8") as handle:
            source = handle.read()
        problems.extend(scan_source(source, relative, local))
    return problems


class ClassifierTests(unittest.TestCase):
    def test_standard_library_names_are_classified_as_standard(self) -> None:
        for name in ("json", "fcntl", "unittest", "os", "sys", "ast"):
            self.assertTrue(is_stdlib(name), "%s should be standard library" % name)

    def test_a_made_up_name_is_not_standard(self) -> None:
        self.assertFalse(is_stdlib("pc_no_such_module_for_this_test"))

    def test_the_removed_toml_reader_is_never_accepted_by_the_scan(self) -> None:
        problems = scan_source("import %s\n" % FORBIDDEN_MODULE, "synthetic.py", set())
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(FORBIDDEN_MODULE, problems[0])


class SyntheticScanTests(unittest.TestCase):
    def test_a_non_standard_import_fails_the_folder_scan(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "pc_ok.py"), "w", encoding="utf-8") as handle:
                handle.write("import json\n")
            with open(os.path.join(folder, "pc_bad.py"), "w", encoding="utf-8") as handle:
                handle.write("import pc_made_up_third_party_name\n")
            problems = scan_folder(folder)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("pc_bad.py", problems[0])
        self.assertIn("pc_made_up_third_party_name", problems[0])
        self.assertNotIn(os.sep + "pc_bad.py", problems[0])

    def test_a_sibling_module_import_is_accepted(self) -> None:
        self.assertEqual(scan_source("import pc_flags\nfrom pc_flags import X\n", "t.py", {"pc_flags"}), [])

    def test_a_relative_import_fails(self) -> None:
        problems = scan_source("from . import pc_flags\n", "t.py", {"pc_flags"})
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("relative", problems[0])

    def test_the_stdlib_names_attribute_fails(self) -> None:
        problems = scan_source("import sys\nx = sys.%s\n" % FORBIDDEN_ATTRIBUTE, "t.py", set())
        self.assertEqual(len(problems), 1, problems)

    def test_zip_with_the_new_keyword_fails(self) -> None:
        problems = scan_source("x = list(zip([1], [2], %s=True))\n" % UNSUPPORTED_ZIP_KEYWORD, "t.py", set())
        self.assertEqual(len(problems), 1, problems)

    def test_a_match_statement_does_not_parse_at_feature_version_3_9(self) -> None:
        source = "match 1:\n    case 1:\n        pass\n"
        problems = scan_source(source, "t.py", set())
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("3.9", problems[0])

    def test_a_parenthesized_multi_item_with_fails(self) -> None:
        source = "with (open('a') as a, open('b') as b):\n    pass\n"
        problems = scan_source(source, "t.py", set())
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("parenthesized", problems[0])

    def test_an_ordinary_multi_item_with_is_accepted(self) -> None:
        source = "with open('a') as a, open('b') as b:\n    pass\n"
        self.assertEqual(scan_source(source, "t.py", set()), [])


class HarnessFolderTests(unittest.TestCase):
    def test_the_folder_holds_python_files(self) -> None:
        self.assertGreaterEqual(len(python_files(HARNESS_DIR)), 10)

    def test_every_python_file_imports_only_standard_library_or_siblings_and_needs_no_3_10(self) -> None:
        problems = scan_folder(HARNESS_DIR)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_the_stub_is_one_file_that_imports_no_sibling(self) -> None:
        with open(os.path.join(HARNESS_DIR, NAMING_EXCEPTION + ".py"), "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), feature_version=(3, 9))
        siblings = harness_stems(HARNESS_DIR) - {NAMING_EXCEPTION}
        tops = set(imported_top_levels(tree))
        self.assertEqual(sorted(tops & siblings), [], "the stub imports a sibling module")
        self.assertEqual(sorted(name for name in tops if name.startswith("pc_")), [], "the stub imports a pc_ module")

    def test_naming_rule_library_modules_start_with_pc_and_tests_with_test(self) -> None:
        wrong = []
        for stem in sorted(harness_stems(HARNESS_DIR)):
            if stem == NAMING_EXCEPTION or stem.startswith("pc_") or stem.startswith("test_"):
                continue
            wrong.append(stem)
        self.assertEqual(wrong, [], "modules that break the naming rule: %s" % ", ".join(wrong))

    def test_the_two_test_support_modules_keep_their_names(self) -> None:
        for stem in TEST_SUPPORT_STEMS:
            self.assertTrue(os.path.isfile(os.path.join(HARNESS_DIR, stem + ".py")), "%s.py is missing" % stem)

    def test_no_module_stem_shadows_a_standard_library_module(self) -> None:
        names = stdlib_names()
        for expected in ("json", "os", "types", "queue", "select", "platform", "code", "trace"):
            self.assertIn(expected, names, "the standard-library name list looks incomplete")
        shadowing = sorted(stem for stem in harness_stems(HARNESS_DIR) if stem in names)
        self.assertEqual(shadowing, [], "module stems that shadow the standard library: %s" % ", ".join(shadowing))


if __name__ == "__main__":
    unittest.main()
