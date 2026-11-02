"""Zero-token tests for the Do-not-redo review (plan 04-07; RERUN-01; D-06, D-07).

A row 7 /preclear reply prints its checkpoint, and the checkpoint ends with a `## Do not redo` section. The review code
parses those entries, lists for each entry the tool calls of the same turn that share a whole token with it, marks an
entry with no candidate UNSUPPORTED, files the candidates and the row 7 facts with each completed chain, and builds the
side-by-side table of the attempts. It never decides anything. These tests prove the entry parser, the token rules, the
candidate rule, the facts, the fixed candidate file, the table and the hostile-text and cap behaviour, against built
streams, scripted row 7 chains and the committed replies (read in place and never copied). No test starts a real
claude: the only claude executed is the scripted fake written by pc_testutil. Folders come from RowRig and are never
deleted. Modules are imported inside small accessors so a missing module is one error per test, not one load failure of
the file. Leak-shaped strings are never typed in this file; hostile-text tests use plain marker words.
"""
from __future__ import annotations

import os
import re
import unittest

from test_row7 import (
    ROW7,
    SECTIONS,
    Row7Run,
    reply_with,
    row7_stages,
)
from test_row_generic import Registered
from test_rows_plain import committed, read_text, spec_of

CANDIDATES = "do-not-redo-candidates.md"
ASSEMBLY_LINE = "## Do not redo"
RUN_ROOT = "/scratch/run-aaaa"
PATHS = {"run_root": RUN_ROOT, "project": RUN_ROOT + "/project", "auto_memory": RUN_ROOT + "/auto-memory"}


def review():
    import pc_review

    return pc_review


def row1():
    import pc_row1

    return pc_row1


def committed_final_reply(row_id: str) -> str:
    text = read_text(committed(row_id, "s2-preclear-trace.md"))
    head = "\n## Final reply\n"
    assert head in text, row_id
    return text.split(head, 1)[1]


def block_with(entries) -> str:
    """A printed checkpoint whose last section holds the given lines."""
    parts = ["## %s\nA short body for this section.\n" % name for name in SECTIONS[:-1]]
    parts.append("## Do not redo\n" + "\n".join(entries))
    return "\n".join(parts)


def stream(calls, denied=()) -> list:
    """Events of one stream: calls is a list of (id, name, input, result text, error flag)."""
    events = [{"type": "system", "subtype": "init", "session_id": "s"}]
    for tool_id, name, tool_input, result, flagged in calls:
        events.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]}})
        events.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_id, "content": result, "is_error": flagged}]}})
    for tool_id in denied:
        events.append({"type": "system", "subtype": "permission_denied", "tool_use_id": tool_id})
    events.append({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "result": "x",
                   "session_id": "s", "permission_denials": [{"tool_use_id": tool_id} for tool_id in denied]})
    return events


def call(tool_id, name, tool_input, result="", flagged=False):
    return (tool_id, name, tool_input, result, flagged)


class EntryParserTests(unittest.TestCase):
    def entries(self, lines):
        return review().do_not_redo_entries(block_with(lines))

    def test_two_bullets_one_wrapped_over_two_lines_give_two_entries(self) -> None:
        found = self.entries(["- first entry that is long", "  and wraps here", "- second entry"])
        self.assertEqual(found, ["first entry that is long and wraps here", "second entry"])

    def test_star_bullets_count_and_a_blank_line_between_bullets_is_ignored(self) -> None:
        self.assertEqual(self.entries(["* one", "", "* two"]), ["one", "two"])

    def test_a_section_with_no_bullet_gives_its_plain_non_empty_lines(self) -> None:
        self.assertEqual(self.entries(["plain one", "", "plain two"]), ["plain one", "plain two"])

    def test_a_block_with_no_section_gives_none(self) -> None:
        self.assertEqual(review().do_not_redo_entries("## Identity and state\nx\n"), [])
        self.assertEqual(review().do_not_redo_entries(""), [])
        self.assertEqual(review().do_not_redo_entries(None), [])

    def test_a_heading_like_text_inside_an_entry_does_not_end_the_section(self) -> None:
        found = self.entries(["- one mentions ## Next action in passing", "   ## indented text", "- two"])
        self.assertEqual(len(found), 2)
        self.assertIn("## Next action", found[0])
        self.assertIn("## indented text", found[0])

    def test_the_next_heading_ends_the_section_and_a_later_heading_line_is_not_read(self) -> None:
        block = block_with(["- one"]) + "\n## Later section\n- not an entry\n"
        self.assertEqual(review().do_not_redo_entries(block), ["one"])

    def test_empty_bullets_are_not_entries(self) -> None:
        self.assertEqual(self.entries(["- ", "- real"]), ["real"])

    def test_an_unindented_line_after_a_bullet_joins_it_so_no_text_is_hidden(self) -> None:
        self.assertEqual(self.entries(["- one", "continues unindented", "- two"]), ["one continues unindented", "two"])

    def test_the_committed_replies_give_two_entries_each_and_row_4b_has_plain_lines(self) -> None:
        counts = {}
        for row_id in ("row7-all-destinations-denied", "row3c-unbound-fallback-none", "row4b-conflicting-blocks"):
            block = row1().extract_printed_checkpoint(committed_final_reply(row_id))
            self.assertTrue(block, row_id)
            counts[row_id] = review().do_not_redo_entries(block)
        self.assertEqual([len(counts[key]) for key in sorted(counts)], [2, 2, 2])
        first = counts["row7-all-destinations-denied"][0]
        self.assertTrue(first.startswith("Workspace policy/registry checked"), first)
        for line in counts["row4b-conflicting-blocks"]:
            self.assertFalse(line.startswith(("-", "*")), "row 4b prints plain lines, not bullets")


class TokenRuleTests(unittest.TestCase):
    def tokens(self, entry, ubiquitous=(), run_root=""):
        return review().entry_tokens(entry, ubiquitous, run_root)

    def test_backtick_spans_path_like_words_and_long_hex_runs_are_tokens(self) -> None:
        found = self.tokens("Read `checkpoint status` and src/app.py then notes.txt, digest df71fd0 and abc123 short.")
        self.assertIn("checkpoint status", found)
        self.assertIn("src/app.py", found)
        self.assertIn("notes.txt", found)
        self.assertIn("df71fd0", found)
        self.assertNotIn("abc123", found, "six hex characters are not a hex run")
        self.assertNotIn("Read", found)

    def test_a_trailing_punctuation_mark_is_stripped_before_the_dot_rule(self) -> None:
        found = self.tokens("see src/app.py. Also (notes.md); and done.")
        self.assertIn("src/app.py", found)
        self.assertIn("notes.md", found)
        self.assertNotIn("done", found)

    def test_the_dot_rule_takes_one_to_five_letters_or_digits_only(self) -> None:
        found = self.tokens("a.b1234 c.abcdef file.py")
        self.assertIn("a.b1234", found)
        self.assertNotIn("c.abcdef", found)
        self.assertIn("file.py", found)

    def test_ubiquitous_tokens_dot_names_and_short_tokens_are_dropped(self) -> None:
        paths = review().ubiquitous_tokens(PATHS)
        found = self.tokens(
            "root %s project %s memory %s . .. .git ./ x/ .c and ok/" % (PATHS["run_root"], PATHS["project"], PATHS["auto_memory"]),
            paths, RUN_ROOT,
        )
        self.assertEqual(found, [], found)

    def test_absolute_paths_under_the_run_root_become_relative(self) -> None:
        paths = review().ubiquitous_tokens(PATHS)
        found = self.tokens("wrote %s/project/src/app.py and %s/auto-memory/note.md" % (RUN_ROOT, RUN_ROOT), paths, RUN_ROOT)
        self.assertEqual(found, ["auto-memory/note.md", "src/app.py"])

    def test_a_leading_dot_slash_is_removed_on_both_sides(self) -> None:
        r = review()
        self.assertEqual(r.entry_tokens("see ./src/app.py", (), RUN_ROOT), ["src/app.py"])
        self.assertIn("src/app.py", r.call_tokens({"command": "cat ./src/app.py"}, "", RUN_ROOT))

    def test_tokens_are_whole_and_case_sensitive_never_substrings(self) -> None:
        r = review()
        wanted = set(r.entry_tokens("uses foo.py and Docs/Readme.md"))
        self.assertFalse(wanted & r.call_tokens({"command": "cat barfoo.py foo.pyc"}, "", RUN_ROOT), "no substring match")
        self.assertFalse(wanted & r.call_tokens({"command": "cat docs/readme.md"}, "", RUN_ROOT), "case matters")
        self.assertTrue(wanted & r.call_tokens({"command": "cat foo.py"}, "", RUN_ROOT))

    def test_call_tokens_read_the_six_input_keys_and_the_result_but_never_a_write_content(self) -> None:
        r = review()
        tool_input = {
            "command": "run cmd/one", "file_path": "dir/file.txt", "path": "dir/path.txt", "pattern": "pat/tern",
            "old_string": "old/value", "new_string": "new/value", "content": "secret/content.txt",
        }
        found = r.call_tokens(tool_input, "result/holds.txt df71fd0", RUN_ROOT)
        for expected in ("cmd/one", "dir/file.txt", "dir/path.txt", "pat/tern", "old/value", "new/value", "result/holds.txt", "df71fd0"):
            self.assertIn(expected, found)
        self.assertNotIn("secret/content.txt", found, "the content of a Write is the model's own text")

    def test_a_backtick_span_equal_to_a_whole_command_or_line_matches_as_a_whole(self) -> None:
        r = review()
        wanted = set(r.entry_tokens("ran `git status --porcelain` there"))
        self.assertTrue(wanted & r.call_tokens({"command": "git status --porcelain"}, "", RUN_ROOT))
        self.assertFalse(wanted & r.call_tokens({"command": "git status --porcelain --ignored"}, "", RUN_ROOT))

    def test_the_committed_first_entry_has_the_policy_registry_token_and_a_runs_root_token(self) -> None:
        block = row1().extract_printed_checkpoint(committed_final_reply("row7-all-destinations-denied"))
        first = review().do_not_redo_entries(block)[0]
        found = review().entry_tokens(first)
        self.assertIn("policy/registry", found)
        self.assertTrue(any(token.endswith("/runs") for token in found), found)


class CandidateTests(unittest.TestCase):
    def pair(self, entries, calls, denied=()):
        return review().candidates(entries, stream(calls, denied), PATHS)

    def test_a_bash_command_that_names_a_shared_path_is_a_candidate(self) -> None:
        found = self.pair(["checked `docs/alpha.md` already"], [call("t1", "Bash", {"command": "cat docs/alpha.md"}, "text")])
        self.assertEqual([item.tool_id for item in found[0]], ["t1"])
        self.assertEqual(found[0][0].tool, "Bash")
        self.assertEqual(found[0][0].excerpt, "cat docs/alpha.md")

    def test_a_read_whose_result_names_a_shared_hex_run_is_a_candidate(self) -> None:
        found = self.pair(
            ["head df71fd0db1bef3 matched"],
            [call("t1", "Read", {"file_path": "%s/project/other.txt" % RUN_ROOT}, "head df71fd0db1bef3 here")],
        )
        self.assertEqual([item.tool_id for item in found[0]], ["t1"])

    def test_no_shared_token_gives_an_empty_list(self) -> None:
        found = self.pair(["checked docs/alpha.md"], [call("t1", "Bash", {"command": "ls"}, "beta.txt")])
        self.assertEqual(found, [[]])

    def test_a_write_content_never_matches_but_its_path_does(self) -> None:
        entries = ["see docs/alpha.md"]
        found = self.pair(entries, [call("t1", "Write", {"file_path": "x/y.md", "content": "docs/alpha.md"}, "ok")])
        self.assertEqual(found, [[]])
        found = self.pair(entries, [call("t1", "Write", {"file_path": "docs/alpha.md", "content": "text"}, "ok")])
        self.assertEqual([item.tool_id for item in found[0]], ["t1"])

    def test_a_call_that_reproduces_the_checkpoint_is_not_a_candidate_whichever_heading_it_holds(self) -> None:
        for heading in ("## Do not redo", "## Identity and state"):
            body = "cat <<'EOF'\n%s\nline policy/registry\nEOF" % heading
            found = self.pair(["root policy/registry checked"], [call("t1", "Bash", {"command": body}, "ok")])
            self.assertEqual(found, [[]], heading)
        write = {"file_path": "p/q.md", "content": "## Identity and state\npolicy/registry\n"}
        self.assertEqual(self.pair(["policy/registry"], [call("t1", "Write", write, "ok")]), [[]])

    def test_a_heading_inside_a_longer_line_does_not_make_an_assembly_call(self) -> None:
        r = review()
        self.assertFalse(r.is_assembly_call({"command": "echo '## Do not redo'"}))
        self.assertFalse(r.is_assembly_call({"command": "grep -c '## Identity and state' f.md"}))
        self.assertTrue(r.is_assembly_call({"command": "x\n## Do not redo   \ny"}))
        self.assertTrue(r.is_assembly_call({"edits": [{"new_string": "## Identity and state"}]}))

    def test_a_call_is_listed_once_per_entry_in_call_order_and_an_entry_can_share_a_call(self) -> None:
        calls = [
            call("t1", "Bash", {"command": "cat a/one.md b/two.md"}, ""),
            call("t2", "Bash", {"command": "cat b/two.md"}, ""),
        ]
        found = self.pair(["a/one.md", "b/two.md", "c/none.md"], calls)
        self.assertEqual([[item.tool_id for item in entry] for entry in found], [["t1"], ["t1", "t2"], []])

    def test_a_result_that_holds_the_run_root_path_is_normalised_before_comparing(self) -> None:
        found = self.pair(
            ["updated `src/app.py`"],
            [call("t1", "Bash", {"command": "ls"}, "%s/project/src/app.py" % RUN_ROOT)],
        )
        self.assertEqual([item.tool_id for item in found[0]], ["t1"])

    def test_the_candidate_file_prints_unsupported_for_no_candidate_and_ids_for_the_rest(self) -> None:
        r = review()
        entries = ["alpha docs/alpha.md", "nothing to find zz/zz.md"]
        found = self.pair(entries, [call("t1", "Bash", {"command": "cat docs/alpha.md"}, "")])
        facts = r.row7_facts(stream([]), PATHS)
        text = r.render_candidates(ROW7, "found", 120, entries, found, facts)
        lines = text.splitlines()
        self.assertEqual(lines[0], "# Do-not-redo candidates for " + ROW7)
        self.assertIn("chain marker: found", lines)
        self.assertIn("checkpoint bytes: 120", lines)
        self.assertIn("entries: 2", lines)
        self.assertIn("candidates 1: 1", lines)
        self.assertIn("candidate t1 Bash", lines)
        self.assertIn("candidates 2: 0", lines)
        self.assertEqual(lines.count("UNSUPPORTED"), 1)
        self.assertIn("> cat docs/alpha.md", lines)
        for line in lines:
            if not line.startswith("> "):
                self.assertNotRegex(line, r"(?i)\b(?:supported|pa" + "ss|fa" + "il|ver" + "dict|acc" + "ept)", line)

    def test_the_candidate_file_round_trips_through_the_parser(self) -> None:
        r = review()
        entries = ["alpha docs/alpha.md", "nothing zz/zz.md", "both docs/alpha.md beta/b.txt"]
        calls = [call("t1", "Bash", {"command": "cat docs/alpha.md"}, ""), call("t2", "Read", {"file_path": "beta/b.txt"}, "")]
        found = self.pair(entries, calls)
        text = r.render_candidates(ROW7, "found", 77, entries, found, r.row7_facts(stream(calls), PATHS))
        parsed = r.parse_candidates(text)
        self.assertEqual((parsed["row"], parsed["marker"], parsed["bytes"], parsed["entries"]), (ROW7, "found", 77, 3))
        self.assertEqual([record["text"] for record in parsed["records"]], entries)
        self.assertEqual([record["count"] for record in parsed["records"]], [1, 0, 2])
        self.assertEqual([record["unsupported"] for record in parsed["records"]], [False, True, False])
        self.assertEqual([item["id"] for item in parsed["records"][2]["candidates"]], ["t1", "t2"])
        self.assertEqual(parsed["records"][0]["candidates"][0]["excerpt"], "cat docs/alpha.md")
        self.assertEqual(parsed["facts"]["errored_writes"], 0)

    def test_the_cap_of_twenty_candidates_states_the_rest(self) -> None:
        r = review()
        calls = [call("t%02d" % number, "Bash", {"command": "cat docs/alpha.md"}, "") for number in range(25)]
        found = self.pair(["docs/alpha.md"], calls)
        self.assertEqual(len(found[0]), 25)
        text = r.render_candidates(ROW7, "found", 1, ["docs/alpha.md"], found, r.row7_facts(stream([]), PATHS))
        self.assertEqual(len([line for line in text.splitlines() if line.startswith("candidate t")]), r.MAX_CANDIDATES)
        self.assertIn("candidates 1: 25", text.splitlines())
        self.assertIn("more candidates: 5", text.splitlines())
        record = r.parse_candidates(text)["records"][0]
        self.assertEqual((record["count"], len(record["candidates"]), record["more"]), (25, 20, 5))

    def test_the_caps_of_entries_entry_length_and_excerpt_length(self) -> None:
        r = review()
        entries = ["entry %d docs/n%d.md %s" % (number, number, "w" * 600) for number in range(70)]
        calls = [call("t1", "Bash", {"command": "cat docs/n0.md " + "z" * 500}, "")]
        found = r.candidates(entries[:64], stream(calls), PATHS)
        text = r.render_candidates(ROW7, "found", 1, entries, found, r.row7_facts(stream([]), PATHS))
        parsed = r.parse_candidates(text)
        self.assertEqual((parsed["entries"], parsed["more_entries"]), (64, 6))
        for record in parsed["records"]:
            self.assertLessEqual(len(record["text"]), r.MAX_ENTRY_CHARS)
        excerpt = parsed["records"][0]["candidates"][0]["excerpt"]
        self.assertLessEqual(len(excerpt), r.MAX_EXCERPT_CHARS)
        self.assertTrue(excerpt.startswith("cat docs/n0.md"))

    def test_the_committed_row_7_full_trace_keeps_the_first_entry_unsupported(self) -> None:
        """Every call of the committed trace that holds a token of the first entry also holds the heading line."""
        r = review()
        block = row1().extract_printed_checkpoint(committed_final_reply(ROW7))
        first = r.do_not_redo_entries(block)[0]
        tokens = r.entry_tokens(first)
        self.assertTrue(tokens, "the entry has tokens")
        text = read_text(committed(ROW7, "s2-preclear-full-trace.md"))
        calls = re.split(r"(?m)^(?=### [0-9]+\. )", text)[1:]
        self.assertEqual(len(calls), 16, "the trace lists sixteen calls")
        holders = []
        for number, part in enumerate(calls, 1):
            if any(token in part for token in tokens):
                holders.append(number)
                heading_lines = [line.rstrip() for line in part.splitlines()]
                self.assertIn(ASSEMBLY_LINE, heading_lines, "call %d holds a token and must reproduce the checkpoint" % number)
        self.assertEqual(holders, [14, 16], "the refused Write of the checkpoint and the byte-measuring heredoc")
        for number in holders:
            body = calls[number - 1]
            self.assertTrue(r.is_assembly_call({"content": body}), "the exclusion rule explains call %d" % number)


class Row7FactsTests(unittest.TestCase):
    def facts(self, calls, denied=()):
        return review().row7_facts(stream(calls, denied), PATHS)

    def test_an_errored_write_under_preclear_is_counted_with_its_id_and_an_executed_one_is_not_an_error(self) -> None:
        target = RUN_ROOT + "/project/.preclear/widget/checkpoint.md"
        found = self.facts([
            call("t1", "Write", {"file_path": target}, "EACCES: permission denied, mkdir", True),
            call("t2", "Write", {"file_path": RUN_ROOT + "/project/.preclear/other.md"}, "created", False),
            call("t3", "Edit", {"file_path": ".preclear/rel.md"}, "edited", False),
            call("t4", "Write", {"file_path": RUN_ROOT + "/project/elsewhere.md"}, "created", False),
            call("t5", "Write", {"file_path": RUN_ROOT + "/auto-memory/note.md"}, "created", False),
        ])
        self.assertEqual(found["errored_write_ids"], ["t1"])
        self.assertEqual(found["executed_writes"], 2)

    def test_a_denied_write_under_preclear_counts_as_errored_not_executed(self) -> None:
        found = self.facts([call("t1", "Write", {"file_path": ".preclear/a.md"}, "no", True)], denied=["t1"])
        self.assertEqual((found["executed_writes"], found["errored_write_ids"]), (0, ["t1"]))

    def test_results_holding_eacces_or_permission_denied_are_counted_by_result_not_by_call(self) -> None:
        found = self.facts([
            call("t1", "Write", {"file_path": ".preclear/a.md"}, "EACCES: permission denied, mkdir", True),
            call("t2", "Bash", {"command": "mkdir x"}, "mkdir: x: Permission denied", True),
            call("t3", "Bash", {"command": "echo EACCES"}, "ok", False),
            call("t4", "Bash", {"command": "ls"}, "fine", False),
        ])
        self.assertEqual((found["eacces_results"], found["permission_denied_results"]), (1, 1))

    def test_executed_chmod_commands_count_and_a_denied_one_does_not(self) -> None:
        found = self.facts(
            [
                call("t1", "Bash", {"command": "chmod 755 project"}, "", False),
                call("t2", "Bash", {"command": "ls; chmod u+w x"}, "", False),
                call("t3", "Bash", {"command": "chmod 777 y"}, "no", True),
                call("t4", "Bash", {"command": "echo chmod"}, "chmod", False),
            ],
            denied=["t3"],
        )
        self.assertEqual(found["executed_chmod"], 2)

    def test_assembly_calls_are_counted(self) -> None:
        found = self.facts([
            call("t1", "Write", {"file_path": "p.md", "content": "## Do not redo\n- x"}, "ok"),
            call("t2", "Bash", {"command": "cat <<'EOF'\n## Identity and state\nEOF"}, "ok"),
            call("t3", "Bash", {"command": "ls"}, "ok"),
        ])
        self.assertEqual(found["assembly_calls"], 2)

    def test_a_stream_with_no_calls_gives_zero_counts(self) -> None:
        found = self.facts([])
        self.assertEqual(
            (found["executed_writes"], found["errored_write_ids"], found["eacces_results"], found["permission_denied_results"],
             found["executed_chmod"], found["assembly_calls"]),
            (0, [], 0, 0, 0, 0),
        )

    def test_the_facts_section_lines_are_name_value_lines_with_ids(self) -> None:
        found = self.facts([call("t1", "Write", {"file_path": ".preclear/a.md"}, "EACCES: x", True)])
        lines = review().facts_lines(found)
        self.assertEqual(len(lines), 6)
        for line in lines:
            self.assertRegex(line, r"^[a-z-]+: .+$")
        self.assertIn("errored-writes-under-preclear: 1 (t1)", lines)
        self.assertIn("tool-results-holding-eacces: 1", lines)


def scripted_chain(entries, extra_ops, reply_before="The checkpoint could not be saved.\n\n"):
    """A scripted row 7 run whose s2 reply prints a checkpoint holding the given Do-not-redo lines."""
    reply = reply_with(block_with(entries), before=reply_before)
    return Row7Run(stages=row7_stages(reply=reply, extra_s2_ops=extra_ops))


READ_PLAN = {"op": "tool", "name": "Read", "input": {"file_path": "$PROJECT/thoughts/plans/2026-10-15-widget-export.md"},
             "content": "plan text"}
ASSEMBLE_WRITE = {"op": "tool", "name": "Write",
                  "input": {"file_path": "$PROJECT/policy/registry", "content": "## Identity and state\nx\n## Do not redo\n- y\n"},
                  "content": "ok"}
ASSEMBLE_BASH = {"op": "tool", "name": "Bash",
                 "input": {"command": "cat <<'EOF' | wc -c\n## Do not redo\n- root policy/registry checked\nEOF"},
                 "content": "42"}
ENTRIES = [
    "- Registry check: root `policy/registry` was verified.",
    "- Plan `thoughts/plans/2026-10-15-widget-export.md` was read in full.",
]


class ScriptedChainTests(unittest.TestCase):
    def test_a_scripted_row_7_chain_files_the_candidates_unsupported_one_candidate_and_the_facts(self) -> None:
        run = scripted_chain(ENTRIES, [READ_PLAN, ASSEMBLE_WRITE, ASSEMBLE_BASH])
        self.assertEqual(run.run.outcome.code, 0, run.lines())
        text = run.read(CANDIDATES)
        parsed = review().parse_candidates(text)
        self.assertEqual(parsed["row"], ROW7)
        self.assertEqual(parsed["marker"], "found")
        self.assertEqual(parsed["entries"], 2)
        first, second = parsed["records"]
        self.assertTrue(first["unsupported"], "its tokens occur only in the calls that reproduce the checkpoint")
        self.assertEqual(first["count"], 0)
        self.assertEqual(second["count"], 1)
        self.assertEqual([(item["id"], item["tool"]) for item in second["candidates"]], [("toolu_0003", "Read")])
        self.assertEqual(text.count("UNSUPPORTED"), 1)
        self.assertEqual(parsed["assembly"], 2)
        self.assertEqual(parsed["facts"]["executed_writes"], 0)
        self.assertEqual(parsed["facts"]["eacces_results"], 1)
        self.assertGreater(parsed["bytes"], 0)

    def test_the_facts_section_is_added_to_mechanical_checks_after_the_ten_sections(self) -> None:
        run = scripted_chain(ENTRIES, [READ_PLAN, ASSEMBLE_WRITE, ASSEMBLE_BASH])
        text = run.read("mechanical-checks.md")
        headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings[-1], "Row 7 facts")
        self.assertEqual(len(headings), 11)
        section = text.split("## Row 7 facts\n", 1)[1].splitlines()
        section = [line for line in section if line]
        self.assertIn("executed-writes-under-preclear: 0", section)
        self.assertIn("errored-writes-under-preclear: 1 (toolu_0002)", section)
        self.assertIn("tool-results-holding-eacces: 1", section)
        self.assertIn("tool-results-holding-permission-denied: 0", section)
        self.assertIn("executed-chmod-commands: 0", section)
        self.assertIn("checkpoint-assembly-calls: 2", section)

    def test_the_row_readme_points_to_the_review_table_in_fixed_words(self) -> None:
        run = scripted_chain(ENTRIES, [READ_PLAN])
        readme = run.read("README.md")
        self.assertIn("row7-review.md at the top of the dated folder", readme)
        self.assertTrue(readme.endswith("Reviewer verdict: PENDING\n"))

    def test_a_chain_with_no_printed_checkpoint_files_a_candidate_file_with_no_entries(self) -> None:
        stages = row7_stages(reply="No block here at all.\n")
        run = Row7Run(stages=stages)
        self.assertEqual(run.run.outcome.code, 0, run.lines())
        parsed = review().parse_candidates(run.read(CANDIDATES))
        self.assertEqual((parsed["marker"], parsed["entries"], parsed["bytes"], parsed["records"]),
                         ("NO-PRINTED-CHECKPOINT", 0, 0, []))
        self.assertIn("## Row 7 facts", run.read("mechanical-checks.md"))

    def test_a_row_with_no_analysis_files_neither_the_file_nor_the_section(self) -> None:
        ran = Registered("row6-readonly-plan")
        self.assertNotIn(CANDIDATES, os.listdir(ran.row_dir))
        self.assertNotIn("## Row 7 facts", read_text(os.path.join(ran.row_dir, "mechanical-checks.md")))

    def test_the_registry_names_the_two_analyses_for_row_7_only_and_pc_review_has_both(self) -> None:
        import pc_rows

        r = review()
        self.assertEqual(spec_of(ROW7).analyses, ("row7-facts", "do-not-redo"))
        self.assertEqual(sorted(r.ANALYSES), ["do-not-redo", "row7-facts"])
        for entry in pc_rows.build_registry():
            if entry.row_id != ROW7:
                self.assertEqual(entry.analyses, (), entry.row_id)
        built = pc_rows.RowSpec("row0-x", "row", "x", (), False, None, None, ())
        self.assertEqual(built.analyses, ())

    def test_an_unknown_analysis_id_is_refused_and_files_nothing(self) -> None:
        import pc_evidence

        run = scripted_chain(ENTRIES, [READ_PLAN])
        data = pc_evidence.load_stage_data(run.run_root)
        spec = spec_of(ROW7)._replace(analyses=("no-such-analysis",))
        with self.assertRaises(pc_evidence.EvidenceError):
            pc_evidence._run_analyses(spec, data, {}, lambda text: text, b"# x\n")


if __name__ == "__main__":
    unittest.main()
