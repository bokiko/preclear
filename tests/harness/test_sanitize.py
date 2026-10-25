"""Tests for pc_sanitize: the runtime-built deny-list sanitizer (EVID-02; D-15).

Injected sources use synthetic names assembled through pc_seeds. The one live test reads the
real machine but compares through boolean expressions with fixed assertion messages, so no
failure ever prints a home path, login name, host name, temp path or deny-file entry.
Scratch files come from tempfile.mkdtemp and are never deleted by the tests.
"""
from __future__ import annotations

import os
import pwd
import random
import re
import stat
import tempfile
import unicodedata
import unittest
import urllib.parse
from unittest import mock

import pc_leakgate  # noqa: E402  (the harness folder is on sys.path via discovery)
import pc_sanitize  # noqa: E402
import pc_seeds  # noqa: E402

TOKEN_RE = re.compile(r"<[a-z][a-z0-9-]*>")
SYNTHETIC_USER = "pcsynthuser"
ODD_HOME_NAME = "pc synth_u.x"  # a space, an underscore and a dot, so the forms differ from each other
PLANTED_ENTRY = "pcplantedentry"


def sources(homes=(), login="", hostnames=(), temp_dirs=(), repo_root=""):
    return pc_sanitize.Sources(list(homes), login, list(hostnames), list(temp_dirs), repo_root)


def build(src, extra_map=None, deny_file=None):
    repo = tempfile.mkdtemp(prefix="preclear-sn-")
    return pc_sanitize.Sanitizer.from_machine(repo, extra_map, deny_file, src)


def scratch_file(data):
    folder = tempfile.mkdtemp(prefix="preclear-sd-")
    path = os.path.join(folder, "deny.txt")
    with open(path, "xb") as handle:
        handle.write(data)
    return path


class HarnessTestCase(unittest.TestCase):
    def ok(self, condition, label):
        self.assertTrue(bool(condition), label)


class HomeFormTests(HarnessTestCase):
    def setUp(self):
        self.home = pc_seeds.home_path(ODD_HOME_NAME)
        self.san = build(sources(homes=[self.home]))

    def assert_replaced(self, form, suffix, label):
        out = self.san.sanitize_text("see " + form + suffix + " end")
        self.ok("<home>" in out, label + ": replaced by the home token")
        self.ok(form.lower() not in out.lower(), label + ": the form does not survive")
        self.ok(out.startswith("see ") and out.endswith(" end"), label + ": surrounding text is kept")

    def test_the_raw_form(self):
        self.assert_replaced(self.home, "/projects/a.txt", "raw")

    def test_the_slash_and_dot_dash_slug(self):
        slug = self.home.replace("/", "-").replace(".", "-")
        self.assert_replaced(slug, "-projects-x", "dash-slug one")

    def test_the_every_non_alphanumeric_dash_slug(self):
        slug = re.sub(r"[^A-Za-z0-9]", "-", self.home)
        self.assert_replaced(slug, "-projects-x", "dash-slug two")

    def test_the_url_encoded_forms_in_both_hex_cases(self):
        full = urllib.parse.quote(self.home, safe="")
        slashed = urllib.parse.quote(self.home, safe="/")
        self.assert_replaced(full, "%2Fprojects", "url full upper hex")
        self.assert_replaced(full.replace("%2F", "%2f").replace("%20", "%20"), "%2Fprojects", "url full lower hex")
        self.assert_replaced(slashed, "/projects", "url slashes kept")
        self.assert_replaced(slashed.upper(), "/projects", "url slashes kept, upper case")

    def test_matching_is_case_insensitive(self):
        self.assert_replaced(self.home.upper(), "/x", "upper case")
        self.assert_replaced(self.home.lower(), "/x", "lower case")

    def test_the_realpath_form_of_a_symlinked_home(self):
        base = tempfile.mkdtemp(prefix="preclear-sl-")
        target = os.path.join(base, "real-home")
        os.mkdir(target)
        link = os.path.join(base, "link-home")
        os.symlink(target, link)
        san = build(sources(homes=[link]))
        out = san.sanitize_text("a " + os.path.realpath(target) + "/f and " + link + "/g")
        self.ok(out == "a <home>/f and <home>/g", "both the link and its realpath become the home token")

    def test_a_longer_word_is_never_cut(self):
        longer = self.home + "extra"
        out = self.san.sanitize_text("x " + longer + "/y")
        self.ok("<home>" not in out, "a different, longer name is not treated as the home")

    def test_punctuation_after_the_path_still_matches(self):
        for tail in (".", ",", ")", ":", "'", '"', "\n", ""):
            out = self.san.sanitize_text("p=" + self.home + tail)
            self.ok(out == "p=<home>" + tail, "a trailing character does not block the match")


class NameFloorTests(HarnessTestCase):
    def test_a_three_character_login_is_not_replaced_a_four_character_one_is(self):
        short = build(sources(login="abc"))
        self.ok(short.sanitize_text("abc went home") == "abc went home", "three characters: untouched")
        four = build(sources(login="abcd"))
        self.ok(four.sanitize_text("abcd went home") == "<user> went home", "four characters: replaced")

    def test_the_login_matches_as_a_whole_word_only(self):
        san = build(sources(login="abcd"))
        self.ok(san.sanitize_text("abcdefg") == "abcdefg", "inside a longer word: untouched")
        self.ok(san.sanitize_text("xabcd") == "xabcd", "at the end of a longer word: untouched")
        self.ok(san.sanitize_text("ABCD, abcd.") == "<user>, <user>.", "case-insensitive at word edges")

    def test_hosts_follow_the_six_character_and_generic_floors(self):
        san = build(sources(hostnames=["short", "sixsix", "localhost", "workstation", "macbook-pro", "plainbox1"]))
        text = "short sixsix localhost workstation macbook-pro plainbox1"
        out = san.sanitize_text(text)
        self.ok(out == "short <host> localhost workstation macbook-pro <host>", "five characters and generic names stay")

    def test_a_non_ascii_login_is_replaced_in_nfc_and_nfd_form(self):
        name = "caf" + "é" + "xy"
        san = build(sources(login=unicodedata.normalize("NFC", name)))
        nfc = unicodedata.normalize("NFC", name)
        nfd = unicodedata.normalize("NFD", name)
        self.ok(nfc != nfd, "the synthetic name has distinct NFC and NFD forms")
        out = san.sanitize_text("a " + nfc + " b " + nfd + " c")
        self.ok(out == "a <user> b <user> c", "both normalisation forms are replaced")


class TempAndRepoTests(HarnessTestCase):
    def test_temp_roots_and_the_repository_root_get_their_tokens(self):
        tmp = pc_seeds.mac_temp_root() + "abcd1234/T"
        san = build(sources(temp_dirs=[tmp], repo_root="/work/pcrepo"))
        out = san.sanitize_text(tmp + "/f.txt and /work/pcrepo/tests/x")
        self.ok(out == "<tmp>/f.txt and <repo>/tests/x", "temp and repo tokens")

    def test_the_longest_match_wins_when_one_form_starts_with_another(self):
        home = pc_seeds.home_path(SYNTHETIC_USER)
        san = build(sources(homes=[home], temp_dirs=[home + "/tmpdir"]), extra_map=None)
        self.ok(san.sanitize_text(home + "/tmpdir/x") == "<tmp>/x", "the temp root inside the home becomes the temp token")
        self.ok(san.sanitize_text(home + "/other") == "<home>/other", "the shorter form still applies elsewhere")

    def test_a_run_root_inside_the_repository_root_wins(self):
        san = build(sources(repo_root="/work/pcrepo"), extra_map={"/work/pcrepo/run1": "<run>"})
        out = san.sanitize_text("/work/pcrepo/run1/ledger and /work/pcrepo/other")
        self.ok(out == "<run>/ledger and <repo>/other", "the caller-supplied mapping wins over the generic form")

    def test_an_unknown_caller_token_is_refused(self):
        with self.assertRaises(pc_sanitize.SanitizerError):
            build(sources(), extra_map={"/work/x": "<not-a-token>"})

    def test_the_helper_and_auto_memory_tokens_are_accepted(self):
        san = build(sources(), extra_map={"/work/h": "<helper>", "/work/m": "<auto-memory-root>"})
        self.ok(san.sanitize_text("/work/h/a /work/m/b") == "<helper>/a <auto-memory-root>/b", "caller tokens")


class AdjacencyTests(HarnessTestCase):
    def setUp(self):
        self.home = pc_seeds.home_path(SYNTHETIC_USER)
        self.src = sources(homes=[self.home], login=SYNTHETIC_USER, hostnames=["sixsix"], repo_root="/work/pcrepo")

    def test_sanitising_twice_equals_sanitising_once(self):
        san = build(self.src)
        text = "a %s/x b %s c sixsix d /work/pcrepo/e" % (self.home, SYNTHETIC_USER)
        once = san.sanitize_text(text)
        self.ok(san.sanitize_text(once) == once, "idempotent")
        self.ok(once != text, "something was replaced")

    def test_tokens_already_in_the_input_survive(self):
        san = build(sources(login="home"))
        text = "<home> <user> <host> <tmp> <repo> <run> <helper> <auto-memory-root> <scratch> <redacted>"
        self.ok(san.sanitize_text(text) == text, "every known token is preserved")

    def test_a_deny_entry_equal_to_a_word_inside_a_token_cannot_corrupt_it(self):
        path = scratch_file(b"redacted\nscratch\nhome\n")
        san = build(sources(), deny_file=path)
        out = san.sanitize_text("<redacted> redacted <scratch> scratch <home> home")
        self.ok(out == "<redacted> <redacted> <scratch> <redacted> <home> <redacted>", "tokens intact, bare words replaced")

    def test_numbered_run_and_helper_tokens_survive(self):
        san = build(sources(login="runb"))
        self.ok(san.sanitize_text("<run-b>/x <helper-dist>") == "<run-b>/x <helper-dist>", "evidence token variants")


class EmptyAndFailClosedTests(HarnessTestCase):
    def test_empty_and_whitespace_entries_are_ignored(self):
        san = build(sources(homes=["", "  "], login="", hostnames=["", "   "], temp_dirs=["", " "], repo_root=""))
        self.ok(san.sanitize_text("") == "", "empty text returns empty text")
        self.ok(san.sanitize_text("abc def / x") == "abc def / x", "no entry matches anything")

    def test_an_unset_home_falls_back_to_the_account_database(self):
        try:
            account_home = pwd.getpwuid(os.getuid()).pw_dir
        except KeyError:
            self.skipTest("no account database entry for this user")
        with mock.patch.dict(os.environ):
            os.environ.pop("HOME", None)
            found = pc_sanitize.machine_sources()
        self.ok(account_home in found.homes, "the account home is a source when HOME is unset")

    def test_an_absent_deny_file_counts_zero(self):
        folder = tempfile.mkdtemp(prefix="preclear-sd-")
        san = build(sources(), deny_file=os.path.join(folder, "missing.txt"))
        self.ok(san.deny_entry_count() == 0, "count is zero")
        self.ok(san.deny_entries() == [], "no entries")

    def test_a_present_deny_file_adds_entries_of_four_or_more_characters(self):
        data = ("# a comment\n\n   \nabc\nlongenough\r\n" + PLANTED_ENTRY + "\n").encode("utf-8")
        san = build(sources(), deny_file=scratch_file(data))
        self.ok(san.deny_entry_count() == 2, "two usable entries")
        out = san.sanitize_text("abc longenough and " + PLANTED_ENTRY.upper())
        self.ok(out == "abc <redacted> and <redacted>", "entries become the redacted token, case-insensitively")
        self.ok(san.counts().get("<redacted>") == 2, "counts are kept per token")

    def test_an_undecodable_deny_file_raises_without_echoing_an_entry(self):
        path = scratch_file(b"\xff\xfe\xfa" + PLANTED_ENTRY.encode("ascii") + b"\n")
        with self.assertRaises(pc_sanitize.SanitizerError) as caught:
            build(sources(), deny_file=path)
        self.ok(PLANTED_ENTRY not in str(caught.exception), "the message holds no entry")

    def test_an_unreadable_deny_file_raises_without_echoing_an_entry(self):
        path = scratch_file((PLANTED_ENTRY + "\n").encode("ascii"))
        os.chmod(path, 0)
        if os.access(path, os.R_OK):
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            self.skipTest("this account can read a mode 0 file (running as the superuser)")
        try:
            with self.assertRaises(pc_sanitize.SanitizerError) as caught:
                build(sources(), deny_file=path)
        finally:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        self.ok(PLANTED_ENTRY not in str(caught.exception), "the message holds no entry")

    def test_a_deny_file_that_is_a_directory_raises(self):
        folder = tempfile.mkdtemp(prefix="preclear-sd-")
        with self.assertRaises(pc_sanitize.SanitizerError):
            build(sources(), deny_file=folder)

    def test_undecodable_input_bytes_raise_without_echoing_them(self):
        san = build(sources())
        with self.assertRaises(pc_sanitize.SanitizerError) as caught:
            san.sanitize_bytes(b"ok \xff\xfe bytes")
        self.ok("xff" not in str(caught.exception).lower(), "the message holds no bytes")

    def test_sanitize_bytes_round_trips_valid_text(self):
        san = build(sources(login="abcd"))
        self.ok(san.sanitize_bytes(b"abcd \xc3\xa9\n") == "<user> é\n".encode("utf-8"), "bytes in, bytes out")


class OrderingTests(HarnessTestCase):
    def test_output_is_independent_of_source_and_map_order(self):
        base_home = pc_seeds.home_path(SYNTHETIC_USER)
        homes = [base_home, base_home + "/sub", pc_seeds.home_path_linux("other4")]
        hosts = ["hostone1", "hosttwo22", "hostthree"]
        temps = [pc_seeds.mac_temp_root() + "aa/T", "/scratch/pctmp"]
        extra = [("/work/pcrepo/r1", "<run>"), ("/work/pcrepo/h1", "<helper>"), ("/work/pcrepo/m1", "<auto-memory-root>")]
        text = " ".join(homes + hosts + temps + [path for path, _ in extra] + ["/work/pcrepo/z", SYNTHETIC_USER])
        outputs = set()
        for seed in range(8):
            rng = random.Random(seed)
            shuffled = [list(homes), list(hosts), list(temps), list(extra)]
            for group in shuffled:
                rng.shuffle(group)
            san = build(sources(shuffled[0], SYNTHETIC_USER, shuffled[1], shuffled[2], "/work/pcrepo"), extra_map=dict(shuffled[3]))
            outputs.add(san.sanitize_text(text).encode("utf-8"))
        self.ok(len(outputs) == 1, "shuffled inputs give byte-identical output")
        repeat = build(sources(homes, SYNTHETIC_USER, hosts, temps, "/work/pcrepo"), extra_map=dict(extra))
        self.ok(repeat.sanitize_text(text).encode("utf-8") in outputs, "a repeated run gives the same bytes")


class ObjectSurfaceTests(HarnessTestCase):
    def test_repr_and_str_show_counts_only(self):
        san = build(sources(homes=[pc_seeds.home_path(SYNTHETIC_USER)], login=SYNTHETIC_USER, hostnames=["sixsix"]))
        for text in (repr(san), str(san)):
            self.ok(SYNTHETIC_USER not in text and "sixsix" not in text and "Users" not in text, "no value in the text form")

    def test_the_token_set_is_the_documented_lower_case_set(self):
        expected = set(["<home>", "<user>", "<host>", "<tmp>", "<repo>", "<run>", "<helper>", "<auto-memory-root>", "<scratch>", "<redacted>"])
        self.ok(set(pc_sanitize.TOKENS) == expected, "token set")
        self.ok(all(token == token.lower() for token in pc_sanitize.TOKENS), "all lower case")


class LiveMachineTests(HarnessTestCase):
    def test_the_real_machine_forms_are_all_replaced(self):
        repo = tempfile.mkdtemp(prefix="preclear-sn-")
        san = pc_sanitize.Sanitizer.from_machine(repo)
        home = os.path.expanduser("~")
        if len(home) < 4:
            self.skipTest("the home path is too short to test")
        real = os.path.realpath(home)
        slug_one = home.replace("/", "-").replace(".", "-")
        slug_two = re.sub(r"[^A-Za-z0-9]", "-", home)
        quoted_full = urllib.parse.quote(home, safe="")
        quoted_slash = urllib.parse.quote(home, safe="/")
        forms_with_suffix = [
            (home, "/sub"),
            (real, "/sub"),
            (slug_one, "-sub"),
            (slug_two, "-sub"),
            (quoted_full, "%2Fsub"),
            (quoted_slash, "/sub"),
        ]
        forms = [form for form, _ in forms_with_suffix]
        login = pwd.getpwuid(os.getuid()).pw_name
        parts = []
        for form, suffix in forms_with_suffix:
            parts.append("p " + form + suffix + "/file.txt and " + form)
        if len(login) >= 4:
            parts.append("who " + login + " said")
        text = "\n".join(parts) + "\n"
        out = san.sanitize_text(text)
        stripped = TOKEN_RE.sub("", out).lower()
        for form in forms:
            self.ok(form.lower() not in stripped, "a real home form survived")
        if len(login) >= 4:
            self.ok(login.lower() not in stripped, "the real login survived")
        self.ok("<home>" in out, "the home token is present")


class GateIntegrationTests(HarnessTestCase):
    def test_sanitised_seeded_text_passes_the_gate_and_the_raw_text_does_not(self):
        home = pc_seeds.home_path(SYNTHETIC_USER)
        tmp = pc_seeds.mac_temp_root() + "abcd1234/T"
        host = "pcseedhost9"
        text = " ".join(["a", home + "/p", "b", pc_seeds.dash_slug(SYNTHETIC_USER) + "proj", "c", tmp + "/d", "x", host, "y"]) + "\n"
        san = build(sources(homes=[home], login=SYNTHETIC_USER, hostnames=[host], temp_dirs=[tmp]))
        deny = san.deny_entries()
        raw = pc_leakgate.scan_bytes("t.txt", text.encode("utf-8"), deny)
        self.ok(len(raw) > 0, "the unsanitised text is refused")
        clean = pc_leakgate.scan_bytes("t.txt", san.sanitize_text(text).encode("utf-8"), deny)
        self.ok(clean == [], "the sanitised text has zero findings")


if __name__ == "__main__":
    unittest.main()
