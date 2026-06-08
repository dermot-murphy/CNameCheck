"""test_identifier_length.py — tests for naming.identifier_length rule (issue #227)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

IL_CFG = cfg_only(**{
    "naming": {
        "identifier_length": {
            "enabled": True, "severity": "warning",
            "min_length": 3, "max_length": 10,
            "exempt_names": ["i", "j", "k"],
            "check_variables": True, "check_functions": True,
            "check_macros": True, "check_types": True,
        },
        "no_single_char_identifiers": {"enabled": False},
    }
})

IL_MIN_ONLY = cfg_only(**{
    "naming": {
        "identifier_length": {
            "enabled": True, "severity": "warning",
            "min_length": 3, "max_length": 0,
            "exempt_names": ["i"],
            "check_variables": True, "check_functions": False,
            "check_macros": False, "check_types": False,
        },
        "no_single_char_identifiers": {"enabled": False},
    }
})


class TestIdentifierLength(unittest.TestCase):

    def test_acceptable_variable_name_passes(self):
        src = "void foo(void) { int count = 0; (void)count; }\n"
        self.assertFalse(has(src, IL_CFG, "naming.identifier_length"))

    def test_short_variable_fails(self):
        # 'ab' has length 2 < min_length 3
        src = "void foo(void) { int ab = 0; (void)ab; }\n"
        self.assertTrue(has(src, IL_CFG, "naming.identifier_length"))

    def test_long_variable_fails(self):
        # 11 chars > max_length 10
        src = "void foo(void) { int long_var_xyz = 0; (void)long_var_xyz; }\n"
        self.assertTrue(has(src, IL_CFG, "naming.identifier_length"))

    def test_exempt_name_passes(self):
        src = "void foo(void) { int i = 0; (void)i; }\n"
        self.assertFalse(has(src, IL_CFG, "naming.identifier_length"))

    def test_c_keyword_not_flagged(self):
        # 'int' is a C keyword — should not be flagged
        src = "void foo(void) { int count = 0; (void)count; }\n"
        self.assertFalse(has(src, IL_CFG, "naming.identifier_length"))

    def test_min_only_no_max_check(self):
        # 'ab' (length 2) fails min but a long name is ok with max=0
        src = "void bar(void) { int long_name_here = 0; (void)long_name_here; }\n"
        self.assertFalse(has(src, IL_MIN_ONLY, "naming.identifier_length"))

    def test_short_macro_fails(self):
        src = "#define AB 1\n"
        self.assertTrue(has(src, IL_CFG, "naming.identifier_length"))

    def test_long_macro_fails(self):
        src = "#define VERY_LONG_MACRO_NAME 1\n"
        self.assertTrue(has(src, IL_CFG, "naming.identifier_length"))

    def test_acceptable_macro_passes(self):
        src = "#define BUF 1\n"
        self.assertFalse(has(src, IL_CFG, "naming.identifier_length"))

    def test_rule_disabled_passes(self):
        src = "void foo(void) { int ab = 0; (void)ab; }\n"
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "naming.identifier_length"))
