"""test_comment_ratio.py — tests for misc.comment_ratio rule (issue #68).

The rule measures the ratio of explanatory comment lines to code lines.

Exclusion rules:
  - Blank lines are excluded from both counts.
  - File header (all leading comment/blank lines before the first code line)
    is excluded — copyright notices must not artificially inflate the ratio.
  - Doxygen blocks (/** … */) are excluded — they are documentation, not
    explanatory inline comments.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, run

RULE = "misc.comment_ratio"


def _cfg(enabled=True, warning_threshold=0.15, error_threshold=0.05,
         min_code_lines=5, severity="warning"):
    return cfg_only(misc={
        "comment_ratio": {
            "enabled": enabled,
            "severity": severity,
            "warning_threshold": warning_threshold,
            "error_threshold": error_threshold,
            "min_code_lines": min_code_lines,
        }
    })


CFG = _cfg()   # default config: warning>=0.15, error>=0.05, min_code=5


def _code(n, start=0):
    """Return n code lines (simple function calls)."""
    return "".join(f"func_{i}();\n" for i in range(start, start + n))


def _comment(n, start=0):
    """Return n inline // comment lines."""
    return "".join(f"// explanation {i}\n" for i in range(start, start + n))


def _mixed(code_n, comment_n):
    """One code line first (ends header), then comment lines, then more code."""
    return _code(1) + _comment(comment_n) + _code(code_n - 1, start=1)


# ---------------------------------------------------------------------------
# Basic pass/fail
# ---------------------------------------------------------------------------

class TestCommentRatioBasic(unittest.TestCase):

    def test_disabled_produces_no_violation(self):
        src = _code(10)
        self.assertFalse(has(src, _cfg(enabled=False), RULE))

    def test_zero_comments_raises_violation(self):
        # 0 comment / 10 code = 0.00 < 0.15
        src = _code(10)
        self.assertTrue(has(src, CFG, RULE))

    def test_sufficient_comments_passes(self):
        # 2 comment / 10 code = 0.20 >= 0.15
        src = _mixed(10, 2)
        self.assertFalse(has(src, CFG, RULE))

    def test_exactly_at_warning_threshold_passes(self):
        # 15 comment / 100 code = 0.15 (exactly at threshold — not below)
        src = _mixed(100, 15)
        self.assertFalse(has(src, CFG, RULE))

    def test_one_below_warning_threshold_fails(self):
        # 14 comment / 100 code = 0.14 < 0.15
        src = _mixed(100, 14)
        self.assertTrue(has(src, CFG, RULE))

    def test_single_violation_emitted(self):
        # Only one violation per file regardless of how far below threshold
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertEqual(len(viols), 1)


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class TestCommentRatioSeverity(unittest.TestCase):

    def test_below_error_threshold_emits_error(self):
        # 0 comment / 10 code = 0.00 < 0.05 (error threshold)
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_between_thresholds_emits_configured_severity(self):
        # 1 comment / 10 code = 0.10 — between 0.05 (error) and 0.15 (warning)
        src = _mixed(10, 1)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_custom_severity_used(self):
        src = _mixed(10, 1)   # between thresholds → uses severity setting
        cfg = _cfg(severity="info")
        viols = [v for v in run(src, cfg) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "info")


# ---------------------------------------------------------------------------
# min_code_lines guard
# ---------------------------------------------------------------------------

class TestCommentRatioMinCodeLines(unittest.TestCase):

    def test_fewer_than_min_code_lines_skipped(self):
        # 0 comment / 4 code = 0.00 but min_code_lines=5 → no violation
        src = _code(4)
        self.assertFalse(has(src, CFG, RULE))

    def test_exactly_min_code_lines_is_checked(self):
        # 0 comment / 5 code = 0.00 < 0.15 → violation
        src = _code(5)
        self.assertTrue(has(src, CFG, RULE))

    def test_custom_min_code_lines(self):
        src = _code(3)
        cfg = _cfg(min_code_lines=3)
        self.assertTrue(has(src, cfg, RULE))   # exactly 3 code lines — checked


# ---------------------------------------------------------------------------
# File header exclusion
# ---------------------------------------------------------------------------

class TestCommentRatioHeaderExclusion(unittest.TestCase):

    def test_block_header_not_counted_as_comments(self):
        # A large copyright block should NOT make the body look well-commented.
        big_header = "/*\n" + " * copyright line\n" * 50 + " */\n"
        body = _code(10)   # 0 inline comments
        src = big_header + body
        # Header excluded → 0 comment / 10 code → violation
        self.assertTrue(has(src, CFG, RULE))

    def test_inline_comments_in_body_counted_after_header(self):
        header = "/* Copyright 2026 ACME. All rights reserved. */\n"
        body   = _mixed(10, 2)   # 2 inline comments in body
        src    = header + body
        # Header excluded; body has 2/10 = 0.20 >= 0.15 → no violation
        self.assertFalse(has(src, CFG, RULE))

    def test_line_comment_header_not_counted(self):
        # // comments at the top (before first code line) are also header
        line_header = "// File: uart_driver.c\n// Author: ACME\n"
        body = _code(10)
        src  = line_header + body
        # Header excluded → 0 / 10 → violation
        self.assertTrue(has(src, CFG, RULE))


# ---------------------------------------------------------------------------
# Doxygen exclusion
# ---------------------------------------------------------------------------

class TestCommentRatioDoxygenExclusion(unittest.TestCase):

    def test_doxygen_block_not_counted_as_comment(self):
        # Functions with Doxygen headers but no inline comments
        dox = "/**\n * @brief Do something.\n * @param x Value.\n * @return none.\n */\n"
        code = "void mod_DoSomething(int x) {\n    x = x + 1U;\n}\n"
        # 5 doxygen-only functions: 0 regular comments / 10 code lines → violation
        src = (dox + code) * 5
        self.assertTrue(has(src, CFG, RULE))

    def test_doxygen_single_line_not_counted(self):
        # One-liner Doxygen: /** @brief foo */
        src = "/** @brief one-liner */\n" + _code(10)
        self.assertTrue(has(src, CFG, RULE))

    def test_doxygen_then_regular_comment_counted(self):
        # Doxygen opener followed by a regular // comment on the next function
        dox  = "/**\n * @brief Init.\n */\n"
        code = _code(1)
        cmt  = "// important safety note\n"
        # 1 dox block (excluded) + 1 code + 1 comment + 9 more code = 1/10
        src  = dox + code + cmt + _code(9, start=1)
        # 1 comment / 10 code = 0.10 — between error and warning thresholds
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")


# ---------------------------------------------------------------------------
# Block comment counting
# ---------------------------------------------------------------------------

class TestCommentRatioBlockComments(unittest.TestCase):

    def test_multiline_block_comment_each_line_counted(self):
        # A 3-line regular block comment: /*, middle, */
        block = "/*\n * This is why.\n */\n"
        src   = _code(1) + block + _code(9, start=1)
        # 3 block comment lines / 10 code = 0.30 >= 0.15 → no violation
        self.assertFalse(has(src, CFG, RULE))

    def test_single_line_block_comment_counted(self):
        src = _code(1) + "/* inline note */\n" + _code(9, start=1)
        # 1 comment / 10 code = 0.10 — between thresholds
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_code_line_with_trailing_comment_counts_as_code(self):
        # "func(); // trailing comment" is a CODE line, not a comment line
        src = "func_0(); // why we call this\n" + _code(9, start=1)
        # 0 pure comment lines / 10 code → violation (trailing comment = code)
        self.assertTrue(has(src, CFG, RULE))


# ---------------------------------------------------------------------------
# Violation message content
# ---------------------------------------------------------------------------

class TestCommentRatioMessage(unittest.TestCase):

    def test_message_contains_ratio_and_counts(self):
        src = _code(10)   # 0 comments / 10 code
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        msg = viols[0].message
        self.assertIn("0.00", msg)
        self.assertIn("0 comment", msg)
        self.assertIn("10 code", msg)

    def test_message_mentions_threshold(self):
        src = _mixed(10, 1)   # 1/10 = 0.10 — between thresholds
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertIn("0.15", viols[0].message)   # warning threshold

    def test_violation_reported_at_line_1(self):
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].line, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
