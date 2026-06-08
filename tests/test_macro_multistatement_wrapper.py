"""test_macro_multistatement_wrapper.py — tests for macro.multistatement_wrapper (issue #222)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

MW_CFG = cfg_only(macros={
    "enabled": True, "severity": "warning", "case": "upper_snake",
    "trailing_semicolon": {"enabled": False},
    "multistatement_wrapper": {"enabled": True, "severity": "warning"},
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


class TestMacroMultistatementWrapper(unittest.TestCase):

    def test_single_statement_macro_passes(self):
        src = "#define INC(x)  ((x)++)\n"
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_single_statement_with_semicolon_passes(self):
        src = "#define LOG(x)  printf(\"%d\", (x));\n"
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_multi_stmt_without_wrapper_fails(self):
        src = "#define INIT(x) (x)->a = 0; (x)->b = 0;\n"
        self.assertTrue(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_multi_stmt_with_do_while_passes(self):
        src = "#define INIT(x) do { (x)->a = 0; (x)->b = 0; } while(0)\n"
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_multi_stmt_do_while_with_space_passes(self):
        src = "#define INIT(x) do { (x)->a = 0; (x)->b = 0; } while (0)\n"
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_multi_stmt_multiline_without_wrapper_fails(self):
        src = (
            "#define SETUP(p) \\\n"
            "    (p)->x = 0; \\\n"
            "    (p)->y = 0;\n"
        )
        self.assertTrue(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_multi_stmt_multiline_with_wrapper_passes(self):
        src = (
            "#define SETUP(p) \\\n"
            "    do { \\\n"
            "        (p)->x = 0; \\\n"
            "        (p)->y = 0; \\\n"
            "    } while(0)\n"
        )
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_object_like_macro_not_checked(self):
        # Object-like macros (no param list) should not be checked
        src = "#define VALS 1; 2;\n"
        self.assertFalse(has(src, MW_CFG, "macro.multistatement_wrapper"))

    def test_rule_disabled_passes(self):
        src = "#define INIT(x) (x)->a = 0; (x)->b = 0;\n"
        self.assertFalse(has(src, DISABLED_CFG, "macro.multistatement_wrapper"))
