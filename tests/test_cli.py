"""test_cli.py — end-to-end CLI tests using subprocess.

Covers: --version, --help, --warnings-as-errors, --options-file, --defines,
--banned-names, --exclusions, --summary, --log.
"""
import sys, os, subprocess, tempfile, textwrap, unittest
from pathlib import Path

_HERE    = Path(__file__).resolve().parent
_SRC     = _HERE.parent / "src"
CHECKER  = str(_SRC / "cnamecheck.py")
# Use the tests/ copy of naming_convention.yaml so src/ config
# can be changed independently without breaking the test suite.
_TESTS_YAML = _HERE / "naming_convention.yaml"
YAML = str(_TESTS_YAML if _TESTS_YAML.exists() else _SRC / "naming_convention.yaml")


def _run(*args, files=None):
    """Run checker; return (returncode, combined stdout+stderr)."""
    cmd = [sys.executable, CHECKER, "--config", YAML, *args]
    if files:
        cmd += [str(f) for f in files]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _write(td, name, content):
    p = Path(td) / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
class TestVersionAndHelp(unittest.TestCase):
    def test_version_exits_zero(self):
        rc, _ = _run("--version")
        self.assertEqual(rc, 0)

    def test_version_prints_tool_name(self):
        _, out = _run("--version")
        self.assertIn("CNameCheck", out)

    def test_help_exits_zero(self):
        rc, _ = _run("--help")
        self.assertEqual(rc, 0)

    def test_help_short_flag_exits_zero(self):
        rc, _ = _run("-h")
        self.assertEqual(rc, 0)

    def test_help_documents_key_flags(self):
        _, out = _run("--help")
        for flag in ("--config", "--defines", "--options-file",
                     "--warnings-as-errors", "--summary"):
            self.assertIn(flag, out)


# ---------------------------------------------------------------------------
class TestWarningsAsErrors(unittest.TestCase):
    """Use main.c (exempt from prefix rules). A tab → misc.indentation INFO."""

    _SRC = "\tvoid f(void){}\n"

    def test_info_alone_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", self._SRC)
            rc, _ = _run(files=[src])
        self.assertEqual(rc, 0)

    def test_warnings_as_errors_makes_exit_one(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", self._SRC)
            rc, _ = _run("--warnings-as-errors", files=[src])
        self.assertEqual(rc, 1)

    def test_exit_zero_overrides_warnings_as_errors(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", self._SRC)
            rc, _ = _run("--warnings-as-errors", "--exit-zero", files=[src])
        self.assertEqual(rc, 0)

    def test_summary_reflects_promoted_counts(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", self._SRC)
            _, out = _run("--warnings-as-errors", "--summary", files=[src])
        # After promotion the summary Errors line should be > 0
        import re
        m = re.search(r"Errors\s+:\s+(\d+)", out)
        self.assertIsNotNone(m)
        self.assertGreater(int(m.group(1)), 0)


# ---------------------------------------------------------------------------
class TestOptionsFile(unittest.TestCase):
    def test_summary_in_options_file_appears_in_output(self):
        with tempfile.TemporaryDirectory() as td:
            opts = _write(td, "cnamecheck.options", "--summary\n")
            src  = _write(td, "main.c", "int main(void){ return 0; }\n")
            _, out = _run("--options-file", str(opts), files=[src])
        self.assertIn("Files checked", out)

    def test_comment_lines_in_options_file_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            opts = _write(td, "cnamecheck.options", "# comment\n--summary\n")
            src  = _write(td, "main.c", "int main(void){ return 0; }\n")
            rc, out = _run("--options-file", str(opts), files=[src])
        self.assertEqual(rc, 0)
        self.assertIn("Files checked", out)

    def test_log_file_created(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "out.log"
            src = _write(td, "main.c", "int main(void){ return 0; }\n")
            _run("--log", str(log), files=[src])
            self.assertTrue(log.exists())

    def test_log_file_contains_output(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "out.log"
            src = _write(td, "main.c", "\tvoid f(void){}\n")
            _run("--log", str(log), files=[src])
            content = log.read_text()
        self.assertIn("misc.indentation", content)


# ---------------------------------------------------------------------------
class TestDefinesFile(unittest.TestCase):
    def test_custom_keyword_mapped_to_static(self):
        """NONSTANDARD_STATIC → static via --defines; function found correctly."""
        with tempfile.TemporaryDirectory() as td:
            defs = _write(td, "project.defines", "NONSTANDARD_STATIC static\n")
            src  = _write(td, "uart.c",
                          "NONSTANDARD_STATIC void uart_BufferRead(void){}\n")
            _, out = _run("--defines", str(defs), files=[src])
        self.assertNotIn("function.prefix", out)

    def test_type_alias_substituted(self):
        """MYBYTE → unsigned char via --defines; variable type recognised."""
        with tempfile.TemporaryDirectory() as td:
            defs = _write(td, "project.defines", "MYBYTE unsigned char\n")
            src  = _write(td, "uart.c",
                          "void uart_DoWork(void){\n"
                          "    MYBYTE *p_buf = 0U;\n"
                          "    (void)p_buf;\n"
                          "}\n")
            _, out = _run("--defines", str(defs), files=[src])
        # After substitution MYBYTE → unsigned char; pointer check works normally
        self.assertNotIn("ERROR [variable", out)


# ---------------------------------------------------------------------------
class TestBannedNamesFile(unittest.TestCase):
    def test_project_banned_name_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            banned = _write(td, "banned.txt", "legacy_init\n")
            src    = _write(td, "mod.c",
                            "void mod_DoWork(void){\n"
                            "    int legacy_init = 0;\n"
                            "    (void)legacy_init;\n"
                            "}\n")
            _, out = _run("--banned-names", str(banned), files=[src])
        self.assertIn("reserved_name", out)
        self.assertIn("legacy_init", out)

    def test_name_not_in_banned_file_not_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            banned = _write(td, "banned.txt", "some_other_name\n")
            src    = _write(td, "mod.c",
                            "void mod_DoWork(void){\n"
                            "    int fine_name = 0;\n"
                            "    (void)fine_name;\n"
                            "}\n")
            _, out = _run("--banned-names", str(banned), files=[src])
        # fine_name not in stdlib, not a keyword, not in banned list
        self.assertNotIn("fine_name", out)

    def test_stdlib_name_always_flagged_without_file(self):
        """stdlib names are caught without any --banned-names file."""
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int strlen = 0; (void)strlen;\n"
                         "}\n")
            _, out = _run(files=[src])
        self.assertIn("reserved_name", out)


# ---------------------------------------------------------------------------
class TestExclusions(unittest.TestCase):
    def test_disabled_rule_suppressed_for_matching_file(self):
        with tempfile.TemporaryDirectory() as td:
            excl = _write(td, "exclusions.yml", textwrap.dedent("""\
                "legacy_mod.*":
                  disabled_rules:
                    - reserved_name
            """))
            src = _write(td, "legacy_mod.c",
                         "void legacy_mod_DoWork(void){\n"
                         "    int strlen = 0; (void)strlen;\n"
                         "}\n")
            _, out = _run("--exclusions", str(excl), files=[src])
        self.assertNotIn("reserved_name", out)

    def test_non_matching_file_still_receives_violations(self):
        with tempfile.TemporaryDirectory() as td:
            excl = _write(td, "exclusions.yml", textwrap.dedent("""\
                "legacy_mod.*":
                  disabled_rules:
                    - reserved_name
            """))
            src = _write(td, "other_mod.c",
                         "void other_mod_DoWork(void){\n"
                         "    int strlen = 0; (void)strlen;\n"
                         "}\n")
            _, out = _run("--exclusions", str(excl), files=[src])
        self.assertIn("reserved_name", out)

    def test_multiple_rules_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            excl = _write(td, "exclusions.yml", textwrap.dedent("""\
                "legacy_mod.*":
                  disabled_rules:
                    - reserved_name
                    - misc.indentation
            """))
            src = _write(td, "legacy_mod.c",
                         "void legacy_mod_DoWork(void){\n"
                         "\tint strlen = 0; (void)strlen;\n"
                         "}\n")
            _, out = _run("--exclusions", str(excl), files=[src])
        self.assertNotIn("reserved_name", out)
        self.assertNotIn("misc.indentation", out)


class TestDictionaryCLI(unittest.TestCase):
    """End-to-end tests for --keywords-file, --stdlib-file, --spell-dict flags."""

    def test_keywords_file_custom_word_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            kw  = _write(td, "kw.txt",  "proj_reserved\n")
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int proj_reserved = 0;\n"
                         "    (void)proj_reserved;\n"
                         "}\n")
            _, out = _run("--keywords-file", str(kw), files=[src])
        self.assertIn("reserved_name", out)
        self.assertIn("proj_reserved", out)

    def test_stdlib_file_custom_word_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            sl  = _write(td, "stdlib.txt", "legacy_alloc\n")
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int legacy_alloc = 0;\n"
                         "    (void)legacy_alloc;\n"
                         "}\n")
            _, out = _run("--stdlib-file", str(sl), files=[src])
        self.assertIn("reserved_name", out)
        self.assertIn("legacy_alloc", out)

    def test_keywords_file_replaces_builtin(self):
        """Custom keyword file replaces builtin — builtin-only words no longer flagged."""
        with tempfile.TemporaryDirectory() as td:
            kw  = _write(td, "kw.txt",  "only_custom_kw\n")
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int interrupt = 0;\n"
                         "    (void)interrupt;\n"
                         "}\n")
            _, out = _run("--keywords-file", str(kw), files=[src])
        hits = [l for l in out.splitlines()
                if "reserved_name" in l and "interrupt" in l]
        self.assertEqual(hits, [], "interrupt should not be flagged with custom keyword file")

    def test_stdlib_file_replaces_builtin(self):
        """Custom stdlib file replaces builtin — strlen no longer reserved."""
        with tempfile.TemporaryDirectory() as td:
            sl  = _write(td, "stdlib.txt", "only_custom_name\n")
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int strlen = 0;\n"
                         "    (void)strlen;\n"
                         "}\n")
            _, out = _run("--stdlib-file", str(sl), files=[src])
        hits = [l for l in out.splitlines()
                if "reserved_name" in l and "strlen" in l]
        self.assertEqual(hits, [], "strlen should not be flagged with custom stdlib file")

    def test_spell_dict_flag_accepted(self):
        from pathlib import Path
        spell_dict = str(Path(__file__).parent.parent / "src" / "c_spell_dict.txt")
        rc, _ = _run("--spell-dict", spell_dict, "--version")
        self.assertEqual(rc, 0)

    def test_all_three_dict_flags_together(self):
        with tempfile.TemporaryDirectory() as td:
            kw = _write(td, "kw.txt", "my_kw\n")
            sl = _write(td, "sl.txt", "my_lib\n")
            sd = _write(td, "sd.txt", "embeddedword\n")
            rc, _ = _run("--keywords-file", str(kw),
                         "--stdlib-file",   str(sl),
                         "--spell-dict",    str(sd),
                         "--version")
        self.assertEqual(rc, 0)

    def test_default_keyword_file_loaded_automatically(self):
        """Without --keywords-file the default c_keywords.txt is used."""
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int interrupt = 0;\n"
                         "    (void)interrupt;\n"
                         "}\n")
            _, out = _run(files=[src])
        self.assertIn("reserved_name", out)

    def test_default_stdlib_file_loaded_automatically(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c",
                         "void mod_DoWork(void){\n"
                         "    int strlen = 0;\n"
                         "    (void)strlen;\n"
                         "}\n")
            _, out = _run(files=[src])
        self.assertIn("reserved_name", out)

class TestVerboseFlag(unittest.TestCase):
    """--verbose prints the current directory to stderr as each new directory
    is entered. The progress line is cleared after all files are processed."""

    def test_verbose_exits_zero_on_clean_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", "int main(void){ return 0; }\n")
            rc, _ = _run("--verbose", "--exit-zero", files=[src])
        self.assertEqual(rc, 0)

    def test_verbose_shows_directory_on_stderr(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", "int main(void){ return 0; }\n")
            cmd = [sys.executable, CHECKER, "--config", YAML,
                   "--verbose", "--exit-zero", str(src)]
            r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertIn("Scanning", r.stderr)

    def test_verbose_output_goes_to_stderr_not_stdout(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", "int main(void){ return 0; }\n")
            cmd = [sys.executable, CHECKER, "--config", YAML,
                   "--verbose", "--exit-zero", str(src)]
            r = subprocess.run(cmd, capture_output=True, text=True)
        # Violations go to stdout; progress goes to stderr
        self.assertNotIn("Scanning", r.stdout)
        self.assertIn("Scanning", r.stderr)

    def test_without_verbose_no_progress_on_stderr(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "main.c", "int main(void){ return 0; }\n")
            cmd = [sys.executable, CHECKER, "--config", YAML,
                   "--exit-zero", str(src)]
            r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotIn("Scanning", r.stderr)

    def test_verbose_flag_in_help(self):
        _, out = _run("--help")
        self.assertIn("--verbose", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
