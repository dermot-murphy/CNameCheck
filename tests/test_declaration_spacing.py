"""test_declaration_spacing.py — tests for misc.declaration_spacing rule (issue #229)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

DS_CFG = cfg_only(misc={"declaration_spacing": {
    "enabled": True, "severity": "info",
}})


class TestDeclarationSpacing(unittest.TestCase):

    def test_blank_line_present_passes(self):
        src = (
            "void foo(void) {\n"
            "    int x;\n"
            "    int y;\n"
            "\n"
            "    x = 1; (void)x;\n"
            "    y = 2; (void)y;\n"
            "}\n"
        )
        self.assertFalse(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_no_blank_line_fails(self):
        src = (
            "void foo(void) {\n"
            "    int x;\n"
            "    int y;\n"
            "    x = 1; (void)x;\n"
            "    y = 2; (void)y;\n"
            "}\n"
        )
        self.assertTrue(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_no_declarations_no_violation(self):
        src = (
            "void foo(void) {\n"
            "    int x = 0; (void)x;\n"
            "    int y = 1; (void)y;\n"
            "}\n"
        )
        # Lines end with '=' so they're declarations with initialisers
        # But there's no separate 'executable' after them — no violation
        self.assertFalse(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_function_with_only_decl_no_exec_passes(self):
        src = "void foo(void) {\n    int x;\n}\n"
        self.assertFalse(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_empty_function_passes(self):
        src = "void foo(void) {}\n"
        self.assertFalse(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_rule_disabled_passes(self):
        src = (
            "void foo(void) {\n"
            "    int x;\n"
            "    x = 1; (void)x;\n"
            "}\n"
        )
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "misc.declaration_spacing"))

    def test_static_declaration_detected(self):
        src = (
            "void foo(void) {\n"
            "    static int count;\n"
            "    count++;\n"
            "}\n"
        )
        self.assertTrue(has(src, DS_CFG, "misc.declaration_spacing"))

    def test_multiple_functions_each_checked(self):
        bad_fn = (
            "void foo(void) {\n"
            "    int x;\n"
            "    x = 1; (void)x;\n"
            "}\n"
        )
        src = bad_fn + bad_fn
        self.assertEqual(count(src, DS_CFG, "misc.declaration_spacing"), 2)
