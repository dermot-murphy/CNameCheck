"""test_reserved_name.py — tests for the reserved_name rule.

No identifier may shadow a C/C++ keyword or C standard library name.
Project-specific banned names are added via --banned-names / extra_banned.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count, messages

RULE = "reserved_name"
RES_CFG  = cfg_only(reserved_names={"enabled": True, "severity": "error"})
RES_WARN = cfg_only(reserved_names={"enabled": True, "severity": "warning"})
RES_OFF  = cfg_only(reserved_names={"enabled": False})


class TestReservedStdlibVariables(unittest.TestCase):
    def test_strlen_flagged(self):
        self.assertTrue(has("void f(void){ int strlen = 0; (void)strlen; }", RES_CFG, RULE))

    def test_errno_flagged(self):
        self.assertTrue(has("void f(void){ int errno = 0; (void)errno; }", RES_CFG, RULE))

    def test_malloc_flagged(self):
        self.assertTrue(has("void f(void){ int malloc = 0; (void)malloc; }", RES_CFG, RULE))

    def test_printf_flagged(self):
        self.assertTrue(has("void f(void){ int printf = 0; (void)printf; }", RES_CFG, RULE))

    def test_assert_flagged(self):
        self.assertTrue(has("void f(void){ int assert = 0; (void)assert; }", RES_CFG, RULE))

    def test_signal_flagged(self):
        self.assertTrue(has("void f(void){ int signal = 0; (void)signal; }", RES_CFG, RULE))

    def test_time_flagged(self):
        self.assertTrue(has("void f(void){ int time = 0; (void)time; }", RES_CFG, RULE))

    def test_memset_global_flagged(self):
        self.assertTrue(has("static int memset = 0;\n", RES_CFG, RULE))


class TestReservedKeywordVariables(unittest.TestCase):
    def test_interrupt_flagged(self):
        self.assertTrue(has("void f(void){ int interrupt = 0; (void)interrupt; }", RES_CFG, RULE))

    def test_class_flagged(self):
        self.assertTrue(has("void f(void){ int class = 0; (void)class; }", RES_CFG, RULE))

    def test_true_flagged(self):
        self.assertTrue(has("void f(void){ int true = 1; (void)true; }", RES_CFG, RULE))

    def test_nullptr_flagged(self):
        self.assertTrue(has("void f(void){ int nullptr = 0; (void)nullptr; }", RES_CFG, RULE))


class TestReservedFunctions(unittest.TestCase):
    def test_function_named_strlen_flagged(self):
        self.assertTrue(has("int strlen(const char *s){ return 0; }", RES_CFG, RULE))

    def test_function_named_memcpy_flagged(self):
        self.assertTrue(has("void memcpy(void *d, const void *s, int n){}", RES_CFG, RULE))

    def test_function_named_printf_flagged(self):
        self.assertTrue(has("int printf(const char *fmt){ return 0; }", RES_CFG, RULE))


class TestReservedMacros(unittest.TestCase):
    def test_define_assert_flagged(self):
        self.assertTrue(has("#define assert(x) do_nothing(x)\n", RES_CFG, RULE))

    def test_define_null_not_flagged(self):
        """NULL itself is expected to be redefined by stddef.h — not banned."""
        viols = run("#define NULL ((void*)0)\n", RES_CFG)
        self.assertFalse(any(v.rule == RULE and "NULL" in v.message for v in viols))


class TestReservedNotFlagged(unittest.TestCase):
    def test_project_function_passes(self):
        self.assertFalse(has("void uart_BufferRead(void){}", RES_CFG, RULE))

    def test_project_variable_passes(self):
        self.assertFalse(has("void f(void){ int my_buffer_len = 0; (void)my_buffer_len; }",
                              RES_CFG, RULE))

    def test_project_macro_passes(self):
        self.assertFalse(has("#define UART_BUFFER_SIZE 256U\n", RES_CFG, RULE))

    def test_my_strlen_not_flagged(self):
        """'my_strlen' is not the same as 'strlen'."""
        self.assertFalse(has("void f(void){ int my_strlen = 0; (void)my_strlen; }",
                              RES_CFG, RULE))

    def test_strlen_prefix_not_flagged(self):
        self.assertFalse(has("int strlen_utf8(const char *s){ return 0; }", RES_CFG, RULE))

    def test_fast_memset_not_flagged(self):
        self.assertFalse(has("void fast_memset(void *d, int v, int n){}", RES_CFG, RULE))


class TestReservedExtraBanned(unittest.TestCase):
    def test_extra_banned_variable_flagged(self):
        src = "void f(void){ int legacy_init = 0; (void)legacy_init; }"
        extra = frozenset({"legacy_init"})
        self.assertTrue(has(src, RES_CFG, RULE, extra_banned=extra))

    def test_extra_banned_function_flagged(self):
        src = "void deprecated_alloc(void){}"
        extra = frozenset({"deprecated_alloc"})
        self.assertTrue(has(src, RES_CFG, RULE, extra_banned=extra))

    def test_extra_banned_not_present_passes(self):
        src = "void f(void){ int fine_name = 0; (void)fine_name; }"
        extra = frozenset({"other_name"})
        self.assertFalse(has(src, RES_CFG, RULE, extra_banned=extra))

    def test_stdlib_and_extra_banned_both_caught(self):
        src = ("void f(void){\n"
               "    int strlen  = 0;\n"
               "    int proj_bad = 0;\n"
               "    (void)strlen; (void)proj_bad;\n"
               "}")
        extra = frozenset({"proj_bad"})
        self.assertGreaterEqual(count(src, RES_CFG, RULE, extra_banned=extra), 2)


class TestReservedMessages(unittest.TestCase):
    def test_message_names_identifier(self):
        src = "void f(void){ int strlen = 0; (void)strlen; }"
        msgs = messages(src, RES_CFG)
        self.assertTrue(any("strlen" in m for m in msgs))

    def test_message_says_standard_library(self):
        src = "void f(void){ int malloc = 0; (void)malloc; }"
        msgs = messages(src, RES_CFG)
        self.assertTrue(any("standard library" in m for m in msgs))

    def test_message_says_keyword(self):
        src = "void f(void){ int interrupt = 0; (void)interrupt; }"
        msgs = messages(src, RES_CFG)
        self.assertTrue(any("keyword" in m for m in msgs))

    def test_message_says_project_banned(self):
        src = "void f(void){ int bad_name = 0; (void)bad_name; }"
        extra = frozenset({"bad_name"})
        msgs = messages(src, RES_CFG, extra_banned=extra)
        self.assertTrue(any("project-banned" in m for m in msgs))


class TestReservedSeverityAndControl(unittest.TestCase):
    def test_default_severity_error(self):
        src = "void f(void){ int strlen = 0; (void)strlen; }"
        viols = [v for v in run(src, RES_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_custom_severity_warning(self):
        src = "void f(void){ int strlen = 0; (void)strlen; }"
        viols = [v for v in run(src, RES_WARN) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_disabled_produces_no_violations(self):
        src = "void f(void){ int strlen = 0; int interrupt = 0; }"
        self.assertFalse(has(src, RES_OFF, RULE))

    def test_violation_on_correct_line(self):
        src = ("void f(void){\n"
               "    int good_name = 0; int strlen = 0;\n"
               "    (void)good_name; (void)strlen;\n"
               "}\n")
        viols = [v for v in run(src, RES_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].line, 2)


class TestReservedAllScopes(unittest.TestCase):
    def test_local_scope_flagged(self):
        self.assertTrue(has("void f(void){ int strlen = 0; (void)strlen; }", RES_CFG, RULE))

    def test_file_scope_flagged(self):
        self.assertTrue(has("static int malloc = 0;\n", RES_CFG, RULE))

    def test_function_definition_flagged(self):
        self.assertTrue(has("void free(void *p){ (void)p; }\n", RES_CFG, RULE))

    def test_macro_define_flagged(self):
        self.assertTrue(has("#define memcpy(d,s,n) platform_copy(d,s,n)\n", RES_CFG, RULE))

    def test_multiple_violations_all_reported(self):
        src = ("void f(void){\n"
               "    int strlen = 0;\n"
               "    int malloc = 0;\n"
               "    int printf = 0;\n"
               "    (void)strlen; (void)malloc; (void)printf;\n"
               "}")
        self.assertGreaterEqual(count(src, RES_CFG, RULE), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
