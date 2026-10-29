"""Tests for pc_allowlist: the bounded model of documented Bash permission-rule matching (HARN-06)
and the guarantee that the setup verbs bind, create and init are never model-facing (STUB-06).

The model is a regression guard against allowlist mistakes, never ground truth: the binary is
ground truth and plan 02-08 records a live capture. The corpus numbers below are measured
facts about frozen evidence under tests/evidence; if one changes, evidence was edited.

Wrapper commands use a synthetic absolute wrapper path under a scratch directory made at run
time; no real path, host or session id appears in this file.
"""
from __future__ import annotations

import inspect
import os
import re
import sys
import tempfile
import threading
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pc_allowlist as pa  # noqa: E402
import pc_flags  # noqa: E402

ROW2 = os.path.join(ROOT, "tests", "evidence", "publication-2026-10-20", "row2-double-conflict")
WRAPPER_FILE = os.path.join(HERE, "checkpoint-wrapper")


def synthetic_wrapper():
    folder = os.path.realpath(tempfile.mkdtemp(prefix="pc-allow-"))
    return os.path.join(folder, "wrapper", "checkpoint")


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


class SplitCompoundTests(unittest.TestCase):
    def test_splits_on_every_documented_separator(self):
        parts = pa.split_compound("a && b || c ; d | e |& f & g\nh")
        self.assertEqual(["a", "b", "c", "d", "e", "f", "g", "h"], parts)

    def test_keeps_separators_inside_single_and_double_quotes(self):
        for command in (
            "echo 'a && b | c ; d'",
            'echo "a || b & c"',
            "echo 'one\ntwo'",
            "printf 'café ; 中文 && x'",
            'echo "say \\" ; still quoted"',
            "echo a\\;b",
        ):
            self.assertEqual([command], pa.split_compound(command), command)

    def test_ignores_empty_parts_and_separator_only_input(self):
        self.assertEqual(["a", "b"], pa.split_compound("a ;; b"))
        self.assertEqual(["a"], pa.split_compound(" ; a ; "))
        self.assertEqual(["a", "b"], pa.split_compound("a &&  && b"))
        self.assertEqual([], pa.split_compound("&& ; | &"))
        self.assertEqual([], pa.split_compound(""))
        self.assertEqual([], pa.split_compound("  \t\n "))

    def test_redirections_that_carry_an_ampersand_are_not_separators(self):
        for command in ("ls 2>&1", "ls >&2", "ls &> out", "ls -la x 2>&1"):
            self.assertEqual([command], pa.split_compound(command), command)

    def test_a_fullwidth_semicolon_is_not_a_separator(self):
        self.assertEqual(["echo a；b"], pa.split_compound("echo a；b"))


class RuleMatchesTests(unittest.TestCase):
    def test_a_rule_without_a_wildcard_is_exact(self):
        self.assertTrue(pa.rule_matches("Bash(pwd)", "pwd"))
        self.assertFalse(pa.rule_matches("Bash(pwd)", "pwd -P"))
        self.assertFalse(pa.rule_matches("Bash(pwd)", "pwdx"))
        self.assertTrue(pa.rule_matches("Bash(pwd -P)", "pwd -P"))

    def test_trailing_wildcard_forms_are_word_boundary_prefixes_that_match_the_bare_command(self):
        for rule in ("Bash(ls:*)", "Bash(ls *)"):
            self.assertTrue(pa.rule_matches(rule, "ls"), rule)
            self.assertTrue(pa.rule_matches(rule, "ls -la /x"), rule)
            self.assertFalse(pa.rule_matches(rule, "lsof"), rule)
            self.assertFalse(pa.rule_matches(rule, "lsblk -f"), rule)
            self.assertFalse(pa.rule_matches(rule, "l"), rule)

    def test_a_multi_word_prefix_needs_the_whole_prefix(self):
        self.assertTrue(pa.rule_matches("Bash(git status:*)", "git status --short"))
        self.assertFalse(pa.rule_matches("Bash(git status:*)", "git --no-optional-locks status"))
        self.assertTrue(pa.rule_matches("Bash(sed -n:*)", "sed -n 1p x"))
        self.assertFalse(pa.rule_matches("Bash(sed -n:*)", "sed -i s/a/b/ x"))

    def test_only_bash_rules_apply(self):
        for rule in ("Read", "Write", "Edit", "Glob", "Grep", "Bash", "Bash(", ""):
            self.assertFalse(pa.rule_matches(rule, "ls"), rule)
        self.assertFalse(pa.rule_matches("Bash(:*)", "ls"))


class HasExpansionTests(unittest.TestCase):
    def test_variables_command_substitution_and_backticks_outside_single_quotes(self):
        for part in ("echo $HOME", "echo $(date)", "echo `date`", 'echo "$HOME"', "echo ${X}", 'echo "`date`"'):
            self.assertTrue(pa.has_expansion(part), part)

    def test_single_quotes_and_escapes_protect_the_characters(self):
        for part in ("echo '$HOME'", "echo '`date`'", "echo \\$HOME", "echo plain", "echo 'a $(b)' c"):
            self.assertFalse(pa.has_expansion(part), part)

    def test_a_compound_with_an_expansion_in_one_part_is_denied(self):
        rules = ("Bash(ls:*)", "Bash(echo:*)")
        decision = pa.is_allowed("ls && echo $HOME", rules)
        self.assertFalse(decision.allowed)
        self.assertEqual("variable in command", decision.reason)
        self.assertTrue(pa.is_allowed("ls && echo '$HOME'", rules).allowed)


class StripWrappersTests(unittest.TestCase):
    def test_documented_wrappers_are_removed_with_their_arguments(self):
        cases = {
            "timeout 30 ls -la": "ls -la",
            "timeout -k 5 30 ls": "ls",
            "time ls": "ls",
            "nice ls": "ls",
            "nice -n 5 ls": "ls",
            "nohup ls": "ls",
            "stdbuf -oL ls": "ls",
            "stdbuf -o L -e 0 ls x": "ls x",
            "command ls": "ls",
            "builtin cd x": "cd x",
            "noglob ls": "ls",
            "time nice -n 5 timeout 10 ls": "ls",
        }
        for command, expected in cases.items():
            self.assertEqual(expected, pa.strip_wrappers(command), command)

    def test_env_and_path_qualified_programs_are_left_alone(self):
        for command in ("env ls", "env A=b ls", "/usr/bin/time ls", "./timeout 5 ls", "/usr/bin/env ls"):
            self.assertEqual(command, pa.strip_wrappers(command), command)

    def test_a_timeout_without_a_duration_is_not_stripped(self):
        self.assertEqual("timeout ls", pa.strip_wrappers("timeout ls"))

    def test_is_allowed_matches_after_stripping(self):
        rules = ("Bash(ls:*)",)
        self.assertTrue(pa.is_allowed("timeout 5 ls -la", rules).allowed)
        self.assertTrue(pa.is_allowed("nohup nice ls", rules).allowed)
        self.assertFalse(pa.is_allowed("env ls", rules).allowed)
        self.assertFalse(pa.is_allowed("/usr/bin/ls", rules).allowed)
        self.assertFalse(pa.is_allowed("time", rules).allowed)


class EmptyAndEncodingTests(unittest.TestCase):
    RULES = ("Bash(git status:*)", "Bash(echo:*)", "Bash(printf café:*)")

    def test_empty_whitespace_and_separator_only_commands_are_never_allowed(self):
        for command in ("", "   ", "\t\n", "&& ;", "|", "\n\n"):
            decision = pa.is_allowed(command, self.RULES)
            self.assertFalse(decision.allowed, repr(command))
            self.assertEqual("empty command", decision.reason, repr(command))

    def test_an_empty_rule_list_allows_nothing(self):
        for rules in ((), []):
            decision = pa.is_allowed("ls", rules)
            self.assertFalse(decision.allowed)
            self.assertEqual("no rules", decision.reason)

    def test_a_non_breaking_space_does_not_match(self):
        self.assertFalse(pa.is_allowed("git status", self.RULES).allowed)
        self.assertFalse(pa.is_allowed("git status ", self.RULES).allowed)
        self.assertFalse(pa.is_allowed(" ", self.RULES).allowed)
        self.assertTrue(pa.is_allowed("git status", self.RULES).allowed)

    def test_a_differently_normalised_name_does_not_match(self):
        nfc = "printf café x"
        nfd = "printf café x"
        self.assertTrue(pa.is_allowed(nfc, self.RULES).allowed)
        self.assertFalse(pa.is_allowed(nfd, self.RULES).allowed)

    def test_quotes_protect_non_ascii_text_and_separators_inside_them(self):
        self.assertTrue(pa.is_allowed("echo 'a ; b && 中文'", self.RULES).allowed)
        self.assertTrue(pa.is_allowed("echo a；b", self.RULES).allowed)

    def test_the_reason_names_only_the_first_word_of_the_unmatched_part(self):
        decision = pa.is_allowed("echo ok && rm -rf some/secret-looking/path", self.RULES)
        self.assertFalse(decision.allowed)
        self.assertIn("rm", decision.reason)
        self.assertNotIn("secret-looking", decision.reason)


class CanonicalCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = synthetic_wrapper()
        cls.rules = pc_flags.build_allowed_tools(cls.wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        cls.commands = pa.canonical_commands(ROOT)

    def test_the_set_is_derived_from_the_committed_traces_and_logs(self):
        wrapper_commands = [c for c in self.commands if c.startswith(pa.WRAPPER_TOKEN)]
        git_commands = [c for c in self.commands if c.startswith("git --no-optional-locks status")]
        self.assertGreaterEqual(len(wrapper_commands), 6)
        self.assertGreaterEqual(len(git_commands), 1)
        self.assertEqual(sorted(set(self.commands)), self.commands, "sorted and distinct")
        for command in self.commands:
            self.assertEqual(1, len(pa.split_compound(command)), command)

    def test_every_canonical_command_is_allowed_for_the_synthetic_wrapper(self):
        for command in self.commands:
            real = pa.substitute_wrapper(command, self.wrapper)
            decision = pa.is_allowed(real, self.rules)
            self.assertTrue(decision.allowed, "%s: %s" % (decision.reason, command.split(" ")[0]))

    def test_every_replayed_verb_sequence_is_present_in_the_set(self):
        verbs = set(c.split(" ")[1] for c in self.commands if c.startswith(pa.WRAPPER_TOKEN + " "))
        for verb in ("status", "show", "validate", "update"):
            self.assertIn(verb, verbs)

    def test_wrapper_bind_create_and_init_are_denied(self):
        for verb in pc_flags.DRIVER_ONLY_VERBS:
            for tail in ("", " --ledger x", " --ledger x --project p"):
                decision = pa.is_allowed("%s %s%s" % (self.wrapper, verb, tail), self.rules)
                self.assertFalse(decision.allowed, verb)

    def test_a_compound_that_adds_an_unlisted_part_is_denied(self):
        for suffix in (" && rm -rf x", " ; curl x", " | tee out", " & sleep 1"):
            decision = pa.is_allowed("%s status%s" % (self.wrapper, suffix), self.rules)
            self.assertFalse(decision.allowed, suffix)
        self.assertTrue(pa.is_allowed("%s status && pwd -P" % self.wrapper, self.rules).allowed)

    def test_pwd_dash_p_is_allowed_exactly_and_nothing_longer_is(self):
        self.assertTrue(pa.is_allowed("pwd -P", self.rules).allowed)
        self.assertTrue(pa.is_allowed("pwd", self.rules).allowed)
        self.assertFalse(pa.is_allowed("pwd -L", self.rules).allowed)
        self.assertFalse(pa.is_allowed("pwd -P -L", self.rules).allowed)

    def test_with_only_a_plain_git_status_rule_the_global_option_form_is_not_matched(self):
        command = "git --no-optional-locks status --porcelain=v1"
        self.assertFalse(pa.is_allowed(command, ("Bash(git status:*)",)).allowed)
        self.assertTrue(pa.is_allowed(command, ("Bash(git --no-optional-locks status:*)",)).allowed)
        self.assertTrue(pa.is_allowed("git status --short", ("Bash(git status:*)",)).allowed)


class RefusalCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls = pa.load_trace_calls(ROOT)
        cls.corpus = pa.refusal_corpus(cls.calls)

    def test_the_corpus_has_the_measured_size(self):
        self.assertEqual(336, len(self.calls))
        self.assertEqual(32, len(set(c["trace"] for c in self.calls)))
        self.assertEqual(22, len(set(c["folder"] for c in self.calls)))
        for call in self.calls:
            self.assertTrue(call["rules"], "every trace is paired with its folder's tools.txt")

    def test_the_rule_class_refusals_split_47_34_and_6(self):
        counts = Counter(c["label"] for c in self.corpus)
        self.assertEqual(
            {pa.LABEL_REQUIRES_APPROVAL: 47, pa.LABEL_MULTIPLE_OPERATIONS: 34, pa.LABEL_VARIABLE: 6},
            dict(counts),
        )
        self.assertEqual(87, len(self.corpus))

    def test_no_rule_class_refusal_is_allowed_under_its_rows_rules(self):
        allowed = []
        for call in self.corpus:
            if pa.is_allowed(call["command"], call["rules"]).allowed:
                allowed.append("%s #%d" % (call["trace"], call["number"]))
        self.assertEqual([], allowed)

    def test_the_matcher_never_reads_result_text(self):
        for func in (pa.split_compound, pa.has_expansion, pa.strip_wrappers, pa.rule_matches, pa.is_allowed):
            source = inspect.getsource(func)
            for needle in ("requires approval", "multiple operations", "can't be checked", "result"):
                self.assertNotIn(needle, source, "%s mentions %r" % (func.__name__, needle))
        self.assertEqual(["command", "rules"], list(inspect.signature(pa.is_allowed).parameters))

    def test_the_loader_reads_evidence_only(self):
        before = sorted(os.listdir(os.path.join(ROOT, "tests", "evidence")))
        pa.load_trace_calls(ROOT)
        self.assertEqual(before, sorted(os.listdir(os.path.join(ROOT, "tests", "evidence"))))


class CorpusScopeTests(unittest.TestCase):
    """The corpus is the committed publication evidence only, so a rerun baseline never changes it (finding C5)."""

    PUBLICATION = "publication-2026-10-20"
    RERUN = "rerun-2026-10-29-model-x"

    @staticmethod
    def trace_text(command):
        return "### 1. Bash (toolu_0001)\n```\n%s\n```\nresult:\n```\nok\n```\n" % command

    def make_repo(self):
        repo = tempfile.mkdtemp(prefix="pc-scope-")
        for folder, command in ((self.PUBLICATION, "pwd -P"), (self.RERUN, "git --no-optional-locks status")):
            row = os.path.join(repo, "tests", "evidence", folder, "row-a")
            os.makedirs(row)
            with open(os.path.join(row, "tools.txt"), "w", encoding="utf-8") as handle:
                handle.write("Read,Bash(pwd -P)\n")
            with open(os.path.join(row, "s2-preclear-full-trace.md"), "w", encoding="utf-8") as handle:
                handle.write(self.trace_text(command))
        return repo

    def test_the_corpus_folder_is_the_publication_folder(self):
        self.assertEqual(pa.CORPUS_FOLDER, self.PUBLICATION)

    def test_a_rerun_folder_next_to_the_publication_folder_is_not_loaded(self):
        calls = pa.load_trace_calls(self.make_repo())
        self.assertEqual(1, len(calls), "only the publication call is loaded")
        self.assertEqual("pwd -P", calls[0]["command"])
        self.assertTrue(calls[0]["folder"].startswith("tests/evidence/" + self.PUBLICATION + "/"))

    def test_another_evidence_folder_name_reads_that_folder(self):
        calls = pa.load_trace_calls(self.make_repo(), evidence_folder=self.RERUN)
        self.assertEqual(1, len(calls))
        self.assertEqual("git --no-optional-locks status", calls[0]["command"])

    def test_a_missing_corpus_folder_gives_no_calls(self):
        repo = tempfile.mkdtemp(prefix="pc-scope-empty-")
        os.makedirs(os.path.join(repo, "tests", "evidence"))
        self.assertEqual([], pa.load_trace_calls(repo))

    def test_the_scoped_loader_equals_the_unscoped_walk_restricted_to_the_publication_folder(self):
        evidence = os.path.join(ROOT, "tests", "evidence")
        prefix = "tests/evidence/" + pa.CORPUS_FOLDER + "/"
        everything = []
        for current, dirs, files in os.walk(evidence):
            dirs.sort(key=os.fsencode)
            for name in files:
                if name.endswith("full-trace.md"):
                    everything.append(os.path.join(current, name))
        scoped = pa.load_trace_calls(ROOT)
        scoped_traces = sorted(set(call["trace"] for call in scoped))
        # The evidence tree also holds rerun folders (tests/evidence/rerun-*); the corpus is pinned to
        # the publication folder, so the unscoped walk is restricted to that prefix before comparing.
        walked = sorted(
            relative
            for relative in (os.path.relpath(path, ROOT).replace(os.sep, "/") for path in everything)
            if relative.startswith(prefix)
            and os.path.isfile(os.path.join(ROOT, os.path.dirname(relative), "tools.txt"))
        )
        self.assertEqual(walked, scoped_traces, "the scoped loader equals the walk restricted to the publication folder")
        self.assertLess(len(walked), len(everything), "the evidence tree holds traces outside the publication folder")
        self.assertTrue(all(trace.startswith(prefix) for trace in scoped_traces))

    def test_canonical_commands_are_unchanged_by_the_scope(self):
        scoped = pa.canonical_commands(ROOT)
        original = pa.load_trace_calls

        def unscoped(repo_root, evidence_folder=None):
            records = []
            base = os.path.join(repo_root, "tests", "evidence")
            for name in sorted(os.listdir(base), key=os.fsencode):
                if os.path.isdir(os.path.join(base, name)):
                    records.extend(original(repo_root, evidence_folder=name))
            return records

        pa.load_trace_calls = unscoped
        try:
            walked = pa.canonical_commands(ROOT)
        finally:
            pa.load_trace_calls = original
        self.assertEqual(walked, scoped, "the canonical command list is the same with or without the scope")
        self.assertTrue(scoped, "the list is not empty")


class HistoricalAllowlistTests(unittest.TestCase):
    def test_the_committed_row_2_bare_prefix_allows_wrapper_bind_and_the_builder_never_does(self):
        wrapper = synthetic_wrapper()
        committed = pa.row_rules(ROW2)
        bare = [r for r in committed if pa.WRAPPER_TOKEN in r]
        self.assertEqual(["Bash(%s:*)" % pa.WRAPPER_TOKEN], bare)
        rules = tuple(pa.substitute_wrapper(r, wrapper) for r in committed)
        for verb in pc_flags.DRIVER_ONLY_VERBS:
            command = "%s %s --ledger x" % (wrapper, verb)
            self.assertTrue(pa.is_allowed(command, rules).allowed, "historical shape, " + verb)
            built = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
            self.assertFalse(pa.is_allowed(command, built).allowed, "harness builder, " + verb)
        for rule in pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS):
            self.assertNotEqual("Bash(%s:*)" % wrapper, rule)


class IdempotencyAndConcurrencyTests(unittest.TestCase):
    def test_build_allowed_tools_is_idempotent_immutable_and_refuses_a_repeated_verb(self):
        wrapper = synthetic_wrapper()
        verbs = list(pc_flags.MODEL_FACING_WRAPPER_VERBS)
        first = pc_flags.build_allowed_tools(wrapper, verbs)
        second = pc_flags.build_allowed_tools(wrapper, verbs)
        self.assertEqual(first, second)
        self.assertIsInstance(first, tuple)
        self.assertIsNot(first, second)
        self.assertEqual(verbs, list(pc_flags.MODEL_FACING_WRAPPER_VERBS), "the input is not changed")
        with self.assertRaises(ValueError):
            pc_flags.build_allowed_tools(wrapper, ["status", "status"])
        with self.assertRaises(ValueError):
            pc_flags.build_allowed_tools(wrapper, ["status", "show", "status"])
        self.assertEqual(first, pc_flags.build_allowed_tools(wrapper, verbs), "a refusal changed nothing")

    def test_is_allowed_answers_identically_on_repeated_calls(self):
        rules = pc_flags.build_allowed_tools(synthetic_wrapper(), ["status"])
        for command in ("git status", "ls && pwd -P", "rm x", "env ls"):
            answers = set((d.allowed, d.reason) for d in (pa.is_allowed(command, rules) for _ in range(5)))
            self.assertEqual(1, len(answers), command)

    def test_several_threads_get_the_same_results(self):
        wrapper = synthetic_wrapper()
        commands = [
            "%s status" % wrapper,
            "%s bind --ledger x" % wrapper,
            "git --no-optional-locks status",
            "ls && echo $HOME",
            "timeout 5 wc -l x | head -n 1",
        ]
        results = []
        errors = []
        barrier = threading.Barrier(8)

        def work():
            try:
                barrier.wait()
                rules = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
                results.append((rules, [pa.is_allowed(c, rules) for c in commands]))
            except Exception as exc:  # pragma: no cover - reported through the assertion below
                errors.append(repr(exc))

        threads = [threading.Thread(target=work) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([], errors)
        self.assertEqual(8, len(results))
        self.assertEqual(1, len(set(repr(r) for r in results)))
        decisions = [d.allowed for d in results[0][1]]
        self.assertEqual([True, False, True, False, True], decisions)


class IndirectRouteTests(unittest.TestCase):
    """STUB-06 holds in two layers; this class records the second one openly."""

    def test_indirect_launch_rules_are_the_baseline_rules_that_can_start_another_program(self):
        words = set(re.match(r"^Bash\(([^ :)]+)", rule).group(1) for rule in pa.INDIRECT_LAUNCH_RULES)
        self.assertEqual({"env", "python3", "awk", "find"}, words)
        for rule in pa.INDIRECT_LAUNCH_RULES:
            self.assertIn(rule, pc_flags.BASELINE_ALLOWED_TOOLS)
        self.assertIsInstance(pa.INDIRECT_LAUNCH_RULES, tuple)

    def test_an_env_prefixed_wrapper_bind_is_allowed_by_the_env_rule_under_the_matcher(self):
        wrapper = synthetic_wrapper()
        rules = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        for verb in pc_flags.DRIVER_ONLY_VERBS:
            command = "env %s %s --ledger x" % (wrapper, verb)
            decision = pa.is_allowed(command, rules)
            self.assertTrue(decision.allowed, "the allowlist alone cannot close this route: " + verb)
            matching = [r for r in rules if pa.rule_matches(r, pa.strip_wrappers(command))]
            self.assertEqual(["Bash(env:*)"], matching)

    def test_the_per_verb_rules_the_builder_adds_match_none_of_the_driver_verbs(self):
        wrapper = synthetic_wrapper()
        rules = pc_flags.build_allowed_tools(wrapper, pc_flags.MODEL_FACING_WRAPPER_VERBS)
        added = rules[len(pc_flags.BASELINE_ALLOWED_TOOLS):]
        self.assertEqual(len(pc_flags.MODEL_FACING_WRAPPER_VERBS), len(added))
        for verb in pc_flags.DRIVER_ONLY_VERBS:
            for tail in ("", " --ledger x"):
                for rule in added:
                    self.assertFalse(pa.rule_matches(rule, "%s %s%s" % (wrapper, verb, tail)), (rule, verb))

    def test_the_wrapper_refusal_is_the_named_control_for_this_route(self):
        self.assertIn("exit 71", pa.INDIRECT_LAUNCH_NOTE)
        self.assertIn("checkpoint-wrapper", pa.INDIRECT_LAUNCH_NOTE)
        source = read_text(WRAPPER_FILE)
        self.assertIn("bind | create | init", source)
        self.assertIn("exit 71", source)


if __name__ == "__main__":
    unittest.main()
