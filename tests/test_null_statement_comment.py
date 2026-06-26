"""test_null_statement_comment.py — tests for misc.null_statement_comment (issue #228)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import time
import unittest
from harness import cfg_only, has, clean, count

NS_CFG = cfg_only(misc={"null_statement_comment": {
    "enabled": True, "severity": "warning",
}})


class TestNullStatementComment(unittest.TestCase):

    def test_while_null_same_line_fails(self):
        src = "void foo(void) { while (condition()); }\n"
        self.assertTrue(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_for_null_same_line_fails(self):
        src = "void foo(void) { for (;;); }\n"
        self.assertTrue(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_while_with_body_passes(self):
        src = "void foo(void) { while (condition()) { break; } }\n"
        self.assertFalse(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_standalone_semicolon_without_comment_fails(self):
        src = "void foo(void) {\n    while (condition())\n    ;\n}\n"
        self.assertTrue(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_standalone_semicolon_with_comment_passes(self):
        src = "void foo(void) {\n    while (condition())\n    ;   /* spin until ready */\n}\n"
        self.assertFalse(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_normal_statement_semicolon_not_flagged(self):
        src = "void foo(void) { int x = 0; (void)x; }\n"
        self.assertFalse(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_rule_disabled_passes(self):
        src = "void foo(void) { while (condition()); }\n"
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "misc.null_statement_comment"))

    def test_if_null_same_line_fails(self):
        src = "void foo(void) { if (condition()); }\n"
        self.assertTrue(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_multiple_violations(self):
        src = (
            "void foo(void) {\n"
            "    while (a());\n"
            "    for (;;);\n"
            "}\n"
        )
        self.assertEqual(count(src, NS_CFG, "misc.null_statement_comment"), 2)

    def test_do_while_terminator_not_flagged(self):
        # Bug #312: "} while (condition);" is the do-while loop terminator,
        # not a null statement — it must not produce a false positive.
        src = (
            "void foo(void) {\n"
            "    int val = 0;\n"
            "    do\n"
            "    {\n"
            "        some_function(&val);\n"
            "    } while (val < MAX_SIZE);\n"
            "}\n"
        )
        self.assertFalse(has(src, NS_CFG, "misc.null_statement_comment"))

    def test_no_catastrophic_backtracking_on_unclosed_condition(self):
        # Regression test: the inline-null regex used a nested-quantifier
        # alternation (?:[^()\n]*|\(...\))* which caused exponential
        # backtracking when a line opened "if (" / "while (" / "for (" with
        # a long run of plain characters and no matching ");" on that line.
        long_line = "if (" + "a" * 5000 + "\n"
        src = "void foo(void) {\n" + long_line + "}\n"
        start = time.time()
        has(src, NS_CFG, "misc.null_statement_comment")
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0,
                         f"null_statement_comment check took {elapsed:.2f}s; "
                         f"likely catastrophic regex backtracking")
