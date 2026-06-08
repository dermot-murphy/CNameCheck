"""test_function_doc_header.py — tests for misc.function_doc_header rule (issue #224)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

FDH_CFG = cfg_only(misc={"function_doc_header": {
    "enabled": True, "severity": "warning",
    "require_brief": True, "require_param": True, "require_return": True,
    "style": "doxygen",
}})

FDH_BRIEF_ONLY = cfg_only(misc={"function_doc_header": {
    "enabled": True, "severity": "warning",
    "require_brief": True, "require_param": False, "require_return": False,
    "style": "doxygen",
}})

FDH_ANY = cfg_only(misc={"function_doc_header": {
    "enabled": True, "severity": "warning",
    "require_brief": False, "require_param": False, "require_return": False,
    "style": "any",
}})


class TestFunctionDocHeader(unittest.TestCase):

    def test_no_comment_fails(self):
        src = "void foo(void) {\n    int x = 0; (void)x;\n}\n"
        self.assertTrue(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_full_doxygen_header_passes(self):
        src = (
            "/**\n"
            " * @brief Does something.\n"
            " * @param count number of items\n"
            " * @return result code\n"
            " */\n"
            "int foo(int count) { return count; }\n"
        )
        self.assertFalse(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_missing_brief_fails(self):
        src = (
            "/**\n"
            " * @param count number of items\n"
            " * @return result code\n"
            " */\n"
            "int foo(int count) { return count; }\n"
        )
        self.assertTrue(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_missing_param_fails(self):
        src = (
            "/**\n"
            " * @brief Does something.\n"
            " * @return result code\n"
            " */\n"
            "int foo(int count) { return count; }\n"
        )
        self.assertTrue(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_void_function_no_return_required(self):
        src = (
            "/**\n"
            " * @brief Does something.\n"
            " */\n"
            "void foo(void) { int x = 0; (void)x; }\n"
        )
        self.assertFalse(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_non_void_missing_return_fails(self):
        src = (
            "/**\n"
            " * @brief Gets value.\n"
            " */\n"
            "int foo(void) { return 0; }\n"
        )
        self.assertTrue(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_brief_only_config_passes_without_param_return(self):
        src = (
            "/**\n"
            " * @brief Gets value.\n"
            " */\n"
            "int foo(int count) { return count; }\n"
        )
        self.assertFalse(has(src, FDH_BRIEF_ONLY, "misc.function_doc_header"))

    def test_any_style_accepts_plain_comment(self):
        src = (
            "/* Gets value. */\n"
            "int foo(void) { return 0; }\n"
        )
        self.assertFalse(has(src, FDH_ANY, "misc.function_doc_header"))

    def test_any_style_no_comment_fails(self):
        src = "int foo(void) { return 0; }\n"
        self.assertTrue(has(src, FDH_ANY, "misc.function_doc_header"))

    def test_backslash_brief_accepted(self):
        src = (
            "/**\n"
            " * \\brief Does something.\n"
            " * \\param count number\n"
            " * \\return result\n"
            " */\n"
            "int foo(int count) { return count; }\n"
        )
        self.assertFalse(has(src, FDH_CFG, "misc.function_doc_header"))

    def test_rule_disabled_passes(self):
        src = "int foo(void) { return 0; }\n"
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "misc.function_doc_header"))

    def test_static_function_checked(self):
        src = "static int foo(void) { return 0; }\n"
        self.assertTrue(has(src, FDH_CFG, "misc.function_doc_header"))
