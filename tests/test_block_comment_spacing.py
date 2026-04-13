"""test_block_comment_spacing.py — tests for misc.block_comment_spacing.

Checks the number of blank lines between the closing '*/' of a multi-line
block comment and the next non-blank line of code or text.

Rule defaults:
    min_blank_lines: 1   (at least 1 blank line after */)
    max_blank_lines: 2   (at most 2 blank lines after */)

Single-line block comments  /* like this */  are not checked.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count

RULE = "misc.block_comment_spacing"


def _cfg(enabled=True, mn=1, mx=2, sev="warning"):
    return cfg_only(misc={"block_comment_spacing": {
        "enabled": enabled,
        "severity": sev,
        "min_blank_lines": mn,
        "max_blank_lines": mx,
    }})


ON  = _cfg()          # enabled, defaults min=1 max=2
OFF = _cfg(enabled=False)


def _src(comment, after):
    """Build a source string: multi-line comment body + whitespace + next line."""
    return f"/*\n{comment}\n*/\n{after}"


# ===========================================================================
# Correct spacing — must NOT flag
# ===========================================================================

class TestBlockCommentSpacingPasses(unittest.TestCase):

    def test_one_blank_line_ok(self):
        src = "/*\n * Brief description.\n */\n\nvoid f(void){}"
        self.assertFalse(has(src, ON, RULE))

    def test_two_blank_lines_ok(self):
        src = "/*\n * Brief description.\n */\n\n\nvoid f(void){}"
        self.assertFalse(has(src, ON, RULE))

    def test_single_line_block_comment_not_checked(self):
        """/* single line */ is not a multi-line comment — never checked."""
        src = "/* single line comment */ void f(void){}"
        self.assertFalse(has(src, ON, RULE))

    def test_inline_single_line_not_checked(self):
        src = "int x = 0; /* inline comment */ int y = 0;"
        self.assertFalse(has(src, ON, RULE))

    def test_comment_at_end_of_file_not_flagged(self):
        """A block comment with nothing after it — no next line to check."""
        src = "/*\n * File trailer comment.\n */\n"
        self.assertFalse(has(src, ON, RULE))

    def test_disabled_zero_blanks_no_flag(self):
        src = "/*\n * Multi.\n */\nvoid f(void){}"
        self.assertFalse(has(src, OFF, RULE))

    def test_disabled_three_blanks_no_flag(self):
        src = "/*\n * Multi.\n */\n\n\n\nvoid f(void){}"
        self.assertFalse(has(src, OFF, RULE))

    def test_custom_min_zero_no_blanks_ok(self):
        """min_blank_lines=0 allows the code to follow immediately."""
        cfg = _cfg(mn=0, mx=2)
        src = "/*\n * Description.\n */\nvoid f(void){}"
        self.assertFalse(has(src, cfg, RULE))

    def test_custom_max_three_three_blanks_ok(self):
        cfg = _cfg(mn=1, mx=3)
        src = "/*\n * Description.\n */\n\n\n\nvoid f(void){}"
        self.assertFalse(has(src, cfg, RULE))

    def test_two_comments_both_correct(self):
        src = ("/*\n * First comment.\n */\n\nvoid f(void){}\n\n"
               "/*\n * Second comment.\n */\n\nvoid g(void){}")
        self.assertEqual(count(src, ON, RULE), 0)


# ===========================================================================
# Violations — below minimum
# ===========================================================================

class TestBlockCommentSpacingTooFew(unittest.TestCase):

    def test_zero_blank_lines_violates_min1(self):
        src = "/*\n * Description.\n */\nvoid f(void){}"
        self.assertTrue(has(src, ON, RULE))

    def test_zero_blank_lines_message_mentions_minimum(self):
        src = "/*\n * Description.\n */\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertIn("minimum", vs[0].message)

    def test_zero_blank_lines_message_mentions_count(self):
        src = "/*\n * Description.\n */\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertIn("0", vs[0].message)

    def test_custom_min_two_one_blank_violates(self):
        cfg = _cfg(mn=2, mx=4)
        src = "/*\n * Description.\n */\n\nvoid f(void){}"
        self.assertTrue(has(src, cfg, RULE))

    def test_two_comments_first_wrong(self):
        src = ("/*\n * First — no blank.\n */\nvoid f(void){}\n\n"
               "/*\n * Second — correct.\n */\n\nvoid g(void){}")
        self.assertEqual(count(src, ON, RULE), 1)

    def test_two_comments_both_wrong(self):
        src = ("/*\n * First — no blank.\n */\nvoid f(void){}\n\n"
               "/*\n * Second — no blank.\n */\nvoid g(void){}")
        self.assertEqual(count(src, ON, RULE), 2)


# ===========================================================================
# Violations — above maximum
# ===========================================================================

class TestBlockCommentSpacingTooMany(unittest.TestCase):

    def test_three_blank_lines_violates_max2(self):
        src = "/*\n * Description.\n */\n\n\n\nvoid f(void){}"
        self.assertTrue(has(src, ON, RULE))

    def test_three_blank_lines_message_mentions_maximum(self):
        src = "/*\n * Description.\n */\n\n\n\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertIn("maximum", vs[0].message)

    def test_three_blank_lines_message_mentions_count(self):
        src = "/*\n * Description.\n */\n\n\n\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertIn("3", vs[0].message)

    def test_custom_max_one_two_blanks_violates(self):
        cfg = _cfg(mn=1, mx=1)
        src = "/*\n * Description.\n */\n\n\nvoid f(void){}"
        self.assertTrue(has(src, cfg, RULE))

    def test_many_blank_lines_violates(self):
        src = "/*\n * Description.\n */\n\n\n\n\n\nvoid f(void){}"
        self.assertTrue(has(src, ON, RULE))


# ===========================================================================
# Line number and severity
# ===========================================================================

class TestBlockCommentSpacingSeverityAndMeta(unittest.TestCase):

    def test_default_severity_warning(self):
        src = "/*\n * Description.\n */\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].severity, "warning")

    def test_custom_severity_info(self):
        cfg = _cfg(sev="info")
        src = "/*\n * Description.\n */\nvoid f(void){}"
        vs = [v for v in run(src, cfg) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].severity, "info")

    def test_violation_line_number_is_comment_close_line(self):
        """Violation is reported on the line containing */."""
        src = "/*\n * Line 2.\n */\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        # The */ is on line 3
        self.assertEqual(vs[0].line, 3)

    def test_yaml_config_has_block_comment_spacing(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "naming_convention.yaml").read_text()
        )
        bcs = cfg["misc"].get("block_comment_spacing", {})
        self.assertIn("enabled",        bcs)
        self.assertIn("min_blank_lines", bcs)
        self.assertIn("max_blank_lines", bcs)

    def test_yaml_default_is_disabled(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "naming_convention.yaml").read_text()
        )
        self.assertFalse(cfg["misc"]["block_comment_spacing"]["enabled"])

    def test_yaml_default_min_is_1(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "naming_convention.yaml").read_text()
        )
        self.assertEqual(cfg["misc"]["block_comment_spacing"]["min_blank_lines"], 1)

    def test_yaml_default_max_is_2(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "naming_convention.yaml").read_text()
        )
        self.assertEqual(cfg["misc"]["block_comment_spacing"]["max_blank_lines"], 2)

    def test_rule_id_is_correct(self):
        src = "/*\n * Description.\n */\nvoid f(void){}"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].rule, "misc.block_comment_spacing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
