"""test_file_length.py — tests for misc.file_length rule (issue #232)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

FL_CFG = cfg_only(misc={"file_length": {
    "enabled": True, "severity": "warning",
    "max_lines": 5, "count_blank_lines": True, "count_comment_lines": True,
}})

FL_NO_BLANK = cfg_only(misc={"file_length": {
    "enabled": True, "severity": "warning",
    "max_lines": 3, "count_blank_lines": False, "count_comment_lines": True,
}})

FL_NO_COMMENT = cfg_only(misc={"file_length": {
    "enabled": True, "severity": "warning",
    "max_lines": 3, "count_blank_lines": True, "count_comment_lines": False,
}})


class TestFileLength(unittest.TestCase):

    def test_short_file_passes(self):
        src = "void foo(void) {}\n"
        self.assertFalse(has(src, FL_CFG, "misc.file_length"))

    def test_exactly_at_limit_passes(self):
        src = "line1\nline2\nline3\nline4\nline5\n"
        self.assertFalse(has(src, FL_CFG, "misc.file_length"))

    def test_one_over_limit_fails(self):
        src = "line1\nline2\nline3\nline4\nline5\nline6\n"
        self.assertTrue(has(src, FL_CFG, "misc.file_length"))

    def test_violation_on_line_1(self):
        src = "\n".join(f"line {i}" for i in range(10)) + "\n"
        violations = [v for v in __import__('harness').run(src, FL_CFG)
                      if v.rule == "misc.file_length"]
        self.assertTrue(violations)
        self.assertEqual(violations[0].line, 1)

    def test_exclude_blank_lines(self):
        # 3 code lines + 4 blank lines = 7 total, but only 3 non-blank
        src = "line1\n\nline2\n\nline3\n\n\n"
        self.assertFalse(has(src, FL_NO_BLANK, "misc.file_length"))

    def test_include_blank_lines(self):
        # Same 7 lines but counting blanks: 7 > max 5
        src = "line1\n\nline2\n\nline3\n\n\n"
        self.assertTrue(has(src, FL_CFG, "misc.file_length"))

    def test_exclude_comment_lines(self):
        # 2 code lines + 3 comment lines; excluding comments = 2 ≤ 3 max
        src = "/* c1 */\n/* c2 */\n/* c3 */\ncode1\ncode2\n"
        self.assertFalse(has(src, FL_NO_COMMENT, "misc.file_length"))

    def test_rule_disabled_passes(self):
        src = "\n".join(f"line {i}" for i in range(1000)) + "\n"
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "misc.file_length"))
