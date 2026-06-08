"""test_no_single_char_identifiers.py — tests for naming.no_single_char_identifiers (issue #231)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

NI_CFG = cfg_only(**{
    "naming": {
        "no_single_char_identifiers": {
            "enabled": True, "severity": "warning",
            "exempt": ["i", "j", "k", "n", "x", "y", "z"],
        },
        "identifier_length": {"enabled": False},
    }
})

NI_STRICT = cfg_only(**{
    "naming": {
        "no_single_char_identifiers": {
            "enabled": True, "severity": "warning",
            "exempt": [],
        },
        "identifier_length": {"enabled": False},
    }
})


class TestNoSingleCharIdentifiers(unittest.TestCase):

    def test_normal_name_passes(self):
        src = "void foo(void) { int count = 0; (void)count; }\n"
        self.assertFalse(has(src, NI_CFG, "naming.no_single_char_identifiers"))

    def test_exempt_loop_var_passes(self):
        src = "void foo(void) { int i = 0; (void)i; }\n"
        self.assertFalse(has(src, NI_CFG, "naming.no_single_char_identifiers"))

    def test_non_exempt_single_char_fails(self):
        src = "void foo(void) { int a = 0; (void)a; }\n"
        self.assertTrue(has(src, NI_CFG, "naming.no_single_char_identifiers"))

    def test_strict_mode_flags_i(self):
        src = "void foo(void) { int i = 0; (void)i; }\n"
        self.assertTrue(has(src, NI_STRICT, "naming.no_single_char_identifiers"))

    def test_two_char_name_not_flagged(self):
        src = "void foo(void) { int ix = 0; (void)ix; }\n"
        self.assertFalse(has(src, NI_CFG, "naming.no_single_char_identifiers"))

    def test_rule_disabled_passes(self):
        src = "void foo(void) { int a = 0; (void)a; }\n"
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "naming.no_single_char_identifiers"))

    def test_multiple_violations_counted(self):
        src = "void foo(void) { int a = 0; int b = 0; (void)a; (void)b; }\n"
        self.assertEqual(count(src, NI_CFG, "naming.no_single_char_identifiers"), 2)

    def test_exempt_xyz_passes(self):
        src = "void foo(void) { int x = 0; int y = 0; int z = 0; (void)x; (void)y; (void)z; }\n"
        self.assertFalse(has(src, NI_CFG, "naming.no_single_char_identifiers"))
