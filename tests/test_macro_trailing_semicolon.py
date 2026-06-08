"""test_macro_trailing_semicolon.py — tests for macro.trailing_semicolon rule (issue #223)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

TS_CFG = cfg_only(macros={
    "enabled": True, "severity": "warning", "case": "upper_snake",
    "trailing_semicolon": {"enabled": True, "severity": "warning"},
    "multistatement_wrapper": {"enabled": False},
    "function_like_suffix": {"enabled": False},
    "exempt_patterns": [],
})

DISABLED_CFG = cfg_only(macros={
    "enabled": True, "severity": "warning", "case": "upper_snake",
    "trailing_semicolon": {"enabled": False},
    "multistatement_wrapper": {"enabled": False},
    "function_like_suffix": {"enabled": False},
    "exempt_patterns": [],
})


class TestMacroTrailingSemicolon(unittest.TestCase):

    def test_clean_macro_no_semicolon_passes(self):
        src = "#define RESET_FLAG(x)  ((x) = 0)\n"
        self.assertFalse(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_trailing_semicolon_fails(self):
        src = "#define RESET_FLAG(x)  ((x) = 0);\n"
        self.assertTrue(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_object_like_macro_trailing_semicolon_fails(self):
        src = "#define MAX_SIZE  (100);\n"
        self.assertTrue(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_multiline_macro_trailing_semicolon_fails(self):
        src = "#define SET(a, b) \\\n    (a) = (b); \\\n    (void)(b);\n"
        self.assertTrue(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_multiline_macro_without_semicolon_passes(self):
        src = "#define SET(a, b) \\\n    (a) = (b)\n"
        self.assertFalse(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_semicolon_in_string_is_ignored(self):
        src = '#define ERR_MSG  "error;"\n'
        self.assertFalse(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_rule_disabled_passes(self):
        src = "#define RESET_FLAG(x)  ((x) = 0);\n"
        self.assertFalse(has(src, DISABLED_CFG, "macro.trailing_semicolon"))

    def test_include_guard_define_not_flagged(self):
        src = "#ifndef FOO_H_\n#define FOO_H_\n#endif\n"
        self.assertFalse(has(src, TS_CFG, "macro.trailing_semicolon"))

    def test_multiple_violations_counted(self):
        src = "#define A(x) (x);\n#define B(x) (x);\n"
        self.assertEqual(count(src, TS_CFG, "macro.trailing_semicolon"), 2)
