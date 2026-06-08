"""test_function_length.py — tests for misc.function_length rule (issue #221)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

# max_lines=7: a function body with 5 code lines + { + } = 7 lines total
FL_CFG = cfg_only(misc={"function_length": {
    "enabled": True, "severity": "warning", "max_lines": 7, "count_comments": True,
}})
FL_CFG_NOCOMMENT = cfg_only(misc={"function_length": {
    "enabled": True, "severity": "warning", "max_lines": 5, "count_comments": False,
}})
FL_CFG_60 = cfg_only(misc={"function_length": {
    "enabled": True, "severity": "warning", "max_lines": 60, "count_comments": True,
}})


def _make_fn(body_lines):
    """Build a C function with the given number of body lines.
    Total body (from { to }) is body_lines + 2 (for the braces).
    """
    body = "\n".join(f"    int var_{i} = {i}; (void)var_{i};" for i in range(body_lines))
    return f"void foo(void) {{\n{body}\n}}\n"


class TestFunctionLength(unittest.TestCase):

    def test_short_function_passes(self):
        src = "void foo(void) {\n    int x = 1; (void)x;\n}\n"
        self.assertFalse(has(src, FL_CFG, "misc.function_length"))

    def test_exactly_at_limit_passes(self):
        # 5 code lines + { + } = 7 lines total ≤ max_lines 7 → pass
        src = _make_fn(5)
        self.assertFalse(has(src, FL_CFG, "misc.function_length"))

    def test_one_over_limit_fails(self):
        # 6 code lines + { + } = 8 lines > max_lines 7 → fail
        src = _make_fn(6)
        self.assertTrue(has(src, FL_CFG, "misc.function_length"))

    def test_well_over_limit_fails(self):
        src = _make_fn(20)
        self.assertTrue(has(src, FL_CFG, "misc.function_length"))

    def test_violation_on_function_name_line(self):
        src = _make_fn(10)
        violations = [v for v in __import__('harness').run(src, FL_CFG)
                      if v.rule == "misc.function_length"]
        self.assertTrue(violations)

    def test_multiple_functions_each_checked(self):
        src = _make_fn(10) + _make_fn(10)
        self.assertEqual(count(src, FL_CFG, "misc.function_length"), 2)

    def test_second_function_clean_not_flagged(self):
        long_fn = _make_fn(10)
        short_fn = "void bar(void) { int x = 0; (void)x; }\n"
        src = long_fn + short_fn
        self.assertEqual(count(src, FL_CFG, "misc.function_length"), 1)

    def test_count_comments_false_excludes_blank_comment_lines(self):
        # Body: 3 code lines + 4 blank/comment lines; max_lines=5 (no-comment mode)
        src = (
            "void foo(void) {\n"
            "    int x = 0;\n"
            "    /* a comment */\n"
            "\n"
            "    /* another */\n"
            "    int y = 1; (void)x; (void)y;\n"
            "    int z = 2; (void)z;\n"
            "}\n"
        )
        self.assertFalse(has(src, FL_CFG_NOCOMMENT, "misc.function_length"))

    def test_rule_disabled_by_default_in_all_off(self):
        src = _make_fn(200)
        cfg = cfg_only()  # all rules off
        self.assertFalse(has(src, cfg, "misc.function_length"))

    def test_default_max_60(self):
        src = _make_fn(61)
        self.assertTrue(has(src, FL_CFG_60, "misc.function_length"))

    def test_nested_braces_not_counted_twice(self):
        # Function with an inner if{} block.  Use max_lines=3 so the 7-line
        # function is flagged exactly once — inner {} must not trigger a second match.
        small_cfg = cfg_only(misc={"function_length": {
            "enabled": True, "severity": "warning", "max_lines": 3, "count_comments": True,
        }})
        src = (
            "void foo(void) {\n"
            "    int x = 1;\n"
            "    if (x) {\n"
            "        int y = 2; (void)y;\n"
            "    }\n"
            "    (void)x;\n"
            "}\n"
        )
        self.assertEqual(count(src, small_cfg, "misc.function_length"), 1)
