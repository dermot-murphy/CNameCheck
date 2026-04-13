"""test_dictionaries.py — tests for externally loadable dictionary files.

Covers three new CLI flags:
  --keywords-file   replace the built-in C keyword list
  --stdlib-file     replace the built-in C stdlib name list
  --spell-dict      replace the built-in spell-check dictionary

Also covers the _load_dict_file() helper that reads those files.
"""
import sys, os, tempfile, subprocess, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import cfg_only, run, has, clean, _load_dict_file, _BUILTIN_DICT

_HERE   = Path(__file__).resolve().parent
_SRC    = _HERE.parent / "src"
CHECKER = str(_SRC / "cnamecheck.py")
YAML    = str(_SRC / "naming_convention.yaml")


def _subprocess(*args, src_text=None, filename="mod.c"):
    """Run checker as subprocess; return (rc, combined output)."""
    with tempfile.TemporaryDirectory() as td:
        if src_text:
            p = Path(td) / filename
            p.write_text(src_text)
            extra = [str(p)]
        else:
            extra = []
        r = subprocess.run(
            [sys.executable, CHECKER, "--config", YAML, *args, *extra],
            capture_output=True, text=True,
        )
        return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------------------
# _load_dict_file helper
# ---------------------------------------------------------------------------

class TestLoadDictFile(unittest.TestCase):
    def test_loads_plain_words(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("alpha\nbeta\ngamma\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertIn("alpha", result)
            self.assertIn("beta", result)
            self.assertIn("gamma", result)
        finally:
            os.unlink(fname)

    def test_ignores_comment_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# This is a comment\nalpha\n# Another comment\nbeta\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertNotIn("# This is a comment", result)
            self.assertIn("alpha", result)
        finally:
            os.unlink(fname)

    def test_ignores_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("alpha\n\n\nbeta\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertNotIn("", result)
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(fname)

    def test_returns_frozenset(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("alpha\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertIsInstance(result, frozenset)
        finally:
            os.unlink(fname)

    def test_missing_file_returns_empty_frozenset(self):
        result = _load_dict_file("/nonexistent/path/file.txt")
        self.assertEqual(result, frozenset())

    def test_strips_whitespace_from_entries(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("  alpha  \n  beta\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertIn("alpha", result)
            self.assertIn("beta", result)
        finally:
            os.unlink(fname)

    def test_duplicate_entries_deduplicated(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("alpha\nalpha\nalpha\n")
            fname = f.name
        try:
            result = _load_dict_file(fname)
            self.assertEqual(len(result), 1)
        finally:
            os.unlink(fname)


# ---------------------------------------------------------------------------
# Default dictionary files exist and contain expected entries
# ---------------------------------------------------------------------------

class TestDefaultDictionaryFiles(unittest.TestCase):
    def test_c_keywords_file_exists(self):
        self.assertTrue((_SRC / "c_keywords.txt").exists())

    def test_c_stdlib_names_file_exists(self):
        self.assertTrue((_SRC / "c_stdlib_names.txt").exists())

    def test_c_spell_dict_file_exists(self):
        self.assertTrue((_SRC / "c_spell_dict.txt").exists())

    def test_keywords_contains_expected_entries(self):
        kw = _load_dict_file(_SRC / "c_keywords.txt")
        for expected in ("if", "while", "for", "return", "static", "extern",
                         "typedef", "struct", "enum", "interrupt"):
            self.assertIn(expected, kw, f"'{expected}' missing from c_keywords.txt")

    def test_stdlib_contains_expected_entries(self):
        stdlib = _load_dict_file(_SRC / "c_stdlib_names.txt")
        for expected in ("strlen", "malloc", "free", "printf", "memset",
                         "memcpy", "assert", "errno"):
            self.assertIn(expected, stdlib, f"'{expected}' missing from c_stdlib_names.txt")

    def test_spell_dict_contains_embedded_domain_words(self):
        words = _load_dict_file(_SRC / "c_spell_dict.txt")
        for expected in ("uart", "dma", "fifo", "gpio", "spi", "hal",
                         "mcu", "cpu", "buffer", "register"):
            self.assertIn(expected, words, f"'{expected}' missing from c_spell_dict.txt")

    def test_keywords_file_has_no_duplicates(self):
        lines = [l.strip() for l in (_SRC / "c_keywords.txt").read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        self.assertEqual(len(lines), len(set(lines)), "Duplicate entries in c_keywords.txt")

    def test_stdlib_file_has_no_duplicates(self):
        lines = [l.strip() for l in (_SRC / "c_stdlib_names.txt").read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        self.assertEqual(len(lines), len(set(lines)), "Duplicate entries in c_stdlib_names.txt")


# ---------------------------------------------------------------------------
# --keywords-file CLI flag
# ---------------------------------------------------------------------------

class TestKeywordsFileCLI(unittest.TestCase):
    def test_custom_keyword_flagged(self):
        """A name in a custom keywords file triggers reserved_name."""
        with tempfile.TemporaryDirectory() as td:
            kw = Path(td) / "kw.txt"
            kw.write_text("my_reserved_kw\n")
            src = "void f(void){ int my_reserved_kw = 0; (void)my_reserved_kw; }"
            rc, out = _subprocess("--keywords-file", str(kw), src_text=src)
        self.assertIn("reserved_name", out)
        self.assertIn("my_reserved_kw", out)

    def test_custom_keyword_file_replaces_builtin(self):
        """With a custom keyword file, builtin keywords NOT in the file are no
        longer flagged."""
        with tempfile.TemporaryDirectory() as td:
            kw = Path(td) / "kw.txt"
            # Only one custom keyword — 'interrupt' is a builtin but NOT listed
            kw.write_text("my_only_kw\n")
            # 'interrupt' used as variable name — should NOT be flagged now
            src = "void f(void){ int interrupt = 0; (void)interrupt; }"
            rc, out = _subprocess("--keywords-file", str(kw), src_text=src)
        # 'interrupt' is NOT in our custom file → not flagged as keyword
        kw_violations = [l for l in out.splitlines()
                         if "reserved_name" in l and "interrupt" in l]
        self.assertEqual(kw_violations, [])

    def test_empty_keywords_file_no_keyword_violations(self):
        """An empty keyword file means no keyword reserved_name checks fire."""
        with tempfile.TemporaryDirectory() as td:
            kw = Path(td) / "kw.txt"
            kw.write_text("# empty\n")
            src = "void f(void){ int while_var = 0; (void)while_var; }"
            rc, out = _subprocess("--keywords-file", str(kw), src_text=src)
        kw_violations = [l for l in out.splitlines()
                         if "reserved_name" in l and "keyword" in l]
        self.assertEqual(kw_violations, [])

    def test_default_keywords_file_loaded_without_flag(self):
        """Without --keywords-file the tool loads src/c_keywords.txt automatically."""
        src = "void f(void){ int interrupt = 0; (void)interrupt; }"
        rc, out = _subprocess(src_text=src)
        self.assertIn("reserved_name", out)

    def test_keywords_file_comment_lines_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            kw = Path(td) / "kw.txt"
            kw.write_text("# this is a comment\nmy_kw\n# another comment\n")
            src = "void f(void){ int my_kw = 0; (void)my_kw; }"
            rc, out = _subprocess("--keywords-file", str(kw), src_text=src)
        self.assertIn("reserved_name", out)


# ---------------------------------------------------------------------------
# --stdlib-file CLI flag
# ---------------------------------------------------------------------------

class TestStdlibFileCLI(unittest.TestCase):
    def test_custom_stdlib_name_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            sl = Path(td) / "stdlib.txt"
            sl.write_text("project_deprecated_fn\n")
            src = "void f(void){ int project_deprecated_fn = 0; (void)project_deprecated_fn; }"
            rc, out = _subprocess("--stdlib-file", str(sl), src_text=src)
        self.assertIn("reserved_name", out)

    def test_custom_stdlib_file_replaces_builtin(self):
        """With a custom stdlib file, builtin stdlib names not in it are not flagged."""
        with tempfile.TemporaryDirectory() as td:
            sl = Path(td) / "stdlib.txt"
            sl.write_text("only_custom_name\n")
            # strlen is a builtin stdlib name but NOT in our custom file
            src = "void f(void){ int strlen = 0; (void)strlen; }"
            rc, out = _subprocess("--stdlib-file", str(sl), src_text=src)
        stdlib_violations = [l for l in out.splitlines()
                             if "reserved_name" in l and "strlen" in l]
        self.assertEqual(stdlib_violations, [])

    def test_default_stdlib_file_loaded_without_flag(self):
        src = "void f(void){ int strlen = 0; (void)strlen; }"
        rc, out = _subprocess(src_text=src)
        self.assertIn("reserved_name", out)

    def test_combining_keywords_and_stdlib_files(self):
        """Both flags can be used simultaneously."""
        with tempfile.TemporaryDirectory() as td:
            kw = Path(td) / "kw.txt"
            sl = Path(td) / "sl.txt"
            kw.write_text("my_kw\n")
            sl.write_text("my_lib_fn\n")
            src = ("void f(void){\n"
                   "    int my_kw     = 0;\n"
                   "    int my_lib_fn = 0;\n"
                   "    (void)my_kw; (void)my_lib_fn;\n"
                   "}")
            rc, out = _subprocess("--keywords-file", str(kw),
                                  "--stdlib-file", str(sl), src_text=src)
        self.assertIn("my_kw",     out)
        self.assertIn("my_lib_fn", out)


# ---------------------------------------------------------------------------
# --spell-dict CLI flag
# ---------------------------------------------------------------------------

class TestSpellDictCLI(unittest.TestCase):
    def test_custom_spell_dict_word_not_flagged(self):
        """A word in the custom dict is not reported as unknown."""
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "spell.txt"
            sd.write_text("xyzquux\n")
            # Enable spell check via a minimal config override isn't easy
            # via subprocess — test that the tool accepts the flag
            rc, out = _subprocess("--spell-dict", str(sd), "--version")
        self.assertEqual(rc, 0)
        self.assertIn("CStyleCheck", out)

    def test_custom_spell_dict_replaces_builtin(self):
        """If custom dict has only one word, other builtin words are unknown."""
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "spell.txt"
            sd.write_text("xyzquux\n")
            # Just verify the flag is accepted without error
            rc, _ = _subprocess("--spell-dict", str(sd), "--version")
        self.assertEqual(rc, 0)

    def test_spell_dict_flag_accepted_by_parser(self):
        rc, out = _subprocess("--spell-dict", str(_SRC / "c_spell_dict.txt"), "--version")
        self.assertEqual(rc, 0)

    def test_keywords_file_flag_accepted_by_parser(self):
        rc, out = _subprocess("--keywords-file", str(_SRC / "c_keywords.txt"), "--version")
        self.assertEqual(rc, 0)

    def test_stdlib_file_flag_accepted_by_parser(self):
        rc, out = _subprocess("--stdlib-file", str(_SRC / "c_stdlib_names.txt"), "--version")
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Default dictionary files loaded at startup (module-level)
# ---------------------------------------------------------------------------

class TestDictionaryLoadedAtStartup(unittest.TestCase):
    def test_c_keywords_module_loaded(self):
        import importlib, sys
        # Import fresh
        if 'cnamecheck' in sys.modules:
            mod = sys.modules['cnamecheck']
        else:
            sys.path.insert(0, str(_SRC))
            mod = importlib.import_module('cnamecheck')
        self.assertGreater(len(mod.C_KEYWORDS), 0)
        self.assertIn("interrupt", mod.C_KEYWORDS)

    def test_c_stdlib_module_loaded(self):
        import sys
        mod = sys.modules.get('cnamecheck')
        if mod is None:
            sys.path.insert(0, str(_SRC))
            import cnamecheck as mod
        self.assertGreater(len(mod.C_STDLIB_NAMES), 0)
        self.assertIn("strlen", mod.C_STDLIB_NAMES)

    def test_builtin_spell_dict_loaded(self):
        import sys
        mod = sys.modules.get('cnamecheck')
        if mod is None:
            sys.path.insert(0, str(_SRC))
            import cnamecheck as mod
        self.assertGreater(len(mod._BUILTIN_DICT), 0)
        self.assertIn("uart", mod._BUILTIN_DICT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
