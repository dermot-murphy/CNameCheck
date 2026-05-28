"""test_whitespace_ratio.py — tests for misc.whitespace_ratio rule (issue #143).

The rule measures the ratio of blank lines to code lines in the file body.

Counting rules:
  - Blank lines (empty / whitespace-only) in the code body → numerator.
  - Non-blank, non-comment lines (code, preprocessor) → denominator.
  - Comment-only lines (// and /* … */) are excluded from both counts.
  - The file header (all leading comment/blank lines before the first code line)
    is excluded — copyright notices must not artificially inflate the ratio.
  - A code line with a trailing // comment is still a code line (denominator).
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, run

RULE = "misc.whitespace_ratio"


def _cfg(enabled=True, warning_threshold=0.10, error_threshold=0.01,
         min_lines=5, severity="warning"):
    return cfg_only(misc={
        "whitespace_ratio": {
            "enabled": enabled,
            "severity": severity,
            "warning_threshold": warning_threshold,
            "error_threshold": error_threshold,
            "min_lines": min_lines,
        }
    })


CFG = _cfg()   # default: warning>=0.10, error>=0.01, min_lines=5


def _code(n, start=0):
    """Return n code lines (simple function calls)."""
    return "".join(f"func_{i}();\n" for i in range(start, start + n))


def _blank(n):
    """Return n blank lines."""
    return "\n" * n


def _comment(n, start=0):
    """Return n comment-only lines."""
    return "".join(f"// note {i}\n" for i in range(start, start + n))


# ---------------------------------------------------------------------------
# Basic pass / fail
# ---------------------------------------------------------------------------

class TestWhitespaceRatioBasic(unittest.TestCase):

    def test_disabled_produces_no_violation(self):
        # Even with zero blank lines, disabled rule must not fire.
        src = _code(10)
        self.assertFalse(has(src, _cfg(enabled=False), RULE))

    def test_zero_blank_lines_raises_violation(self):
        # 0 blank / 10 code = 0.00 < 0.01 (error threshold)
        src = _code(10)
        self.assertTrue(has(src, CFG, RULE))

    def test_sufficient_blank_lines_passes(self):
        # 1 blank / 10 code = 0.10 == warn_thr → not below → no violation
        src = _code(1) + _blank(1) + _code(9, start=1)
        self.assertFalse(has(src, CFG, RULE))

    def test_exactly_at_warning_threshold_passes(self):
        # 1 blank / 10 code = 0.10 (exactly at threshold — not below)
        src = _code(1) + _blank(1) + _code(9, start=1)
        self.assertFalse(has(src, CFG, RULE))

    def test_one_below_warning_threshold_fails(self):
        # 1 blank / 20 code = 0.05 < 0.10 but >= 0.01 → warning
        src = _code(1) + _blank(1) + _code(19, start=1)
        self.assertTrue(has(src, CFG, RULE))

    def test_single_violation_emitted_per_file(self):
        # Only one violation per file regardless of how far below threshold
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertEqual(len(viols), 1)


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class TestWhitespaceRatioSeverity(unittest.TestCase):

    def test_below_error_threshold_emits_error(self):
        # 0 blank / 10 code = 0.00 < 0.01 (error threshold)
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_between_thresholds_emits_configured_severity(self):
        # 1 blank / 20 code = 0.05 — between 0.01 (error) and 0.10 (warning)
        src = _code(1) + _blank(1) + _code(19, start=1)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_custom_severity_used_between_thresholds(self):
        # When between error and warning thresholds, the configured severity is used
        src = _code(1) + _blank(1) + _code(19, start=1)
        cfg = _cfg(severity="info")
        viols = [v for v in run(src, cfg) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "info")

    def test_exactly_at_error_threshold_is_warning_not_error(self):
        # ratio == err_thr is NOT below error threshold → warning, not error
        # 1 blank / 100 code = 0.01 == err_thr
        src = _code(1) + _blank(1) + _code(99, start=1)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")


# ---------------------------------------------------------------------------
# min_lines guard
# ---------------------------------------------------------------------------

class TestWhitespaceRatioMinLines(unittest.TestCase):

    def test_fewer_than_min_lines_skipped(self):
        # 4 code lines < min_lines=5 → file skipped, no violation
        src = _code(4)
        self.assertFalse(has(src, CFG, RULE))

    def test_exactly_min_lines_is_checked(self):
        # 5 code lines == min_lines=5 → file checked → violation (0 blanks)
        src = _code(5)
        self.assertTrue(has(src, CFG, RULE))

    def test_custom_min_lines(self):
        # With min_lines=3, a 3-line file is checked
        src = _code(3)
        cfg = _cfg(min_lines=3)
        self.assertTrue(has(src, cfg, RULE))

    def test_comments_do_not_contribute_to_min_lines(self):
        # 4 code lines + 10 comment lines → code_lines=4 < min_lines=5 → skipped
        src = _comment(10) + _code(4)
        self.assertFalse(has(src, CFG, RULE))


# ---------------------------------------------------------------------------
# File header exclusion
# ---------------------------------------------------------------------------

class TestWhitespaceRatioHeaderExclusion(unittest.TestCase):

    def test_blank_lines_in_block_header_not_counted(self):
        # Blank lines inside the copyright block must NOT inflate the numerator.
        # Header: /* Copyright ... */ with internal blank lines
        header = "/*\n\n * Copyright 2026 ACME Corp.\n\n */\n"
        body = _code(10)   # 0 blank lines in body
        src = header + body
        # Header excluded → blank=0, code=10 → violation
        self.assertTrue(has(src, CFG, RULE))

    def test_blank_lines_between_header_comments_not_counted(self):
        # Blank lines between // header comments are also in the header region
        header = "// File: foo.c\n\n// Author: ACME\n"
        body = _code(10)
        src = header + body
        # Header excluded → blank=0, code=10 → violation
        self.assertTrue(has(src, CFG, RULE))

    def test_blank_lines_in_body_counted_after_header(self):
        header = "/* Copyright 2026 ACME. All rights reserved. */\n"
        body   = _code(1) + _blank(1) + _code(9, start=1)   # 1 blank / 10 code
        src    = header + body
        # Header excluded; body has 1/10 = 0.10 == warn_thr → no violation
        self.assertFalse(has(src, CFG, RULE))


# ---------------------------------------------------------------------------
# Comment line exclusion
# ---------------------------------------------------------------------------

class TestWhitespaceRatioCommentExclusion(unittest.TestCase):

    def test_line_comments_excluded_from_denominator(self):
        # 5 code + 10 comment-only = denominator is 5 only, not 15
        # ratio = 0/5 = 0.00 < 0.01 → error
        src = _code(5) + _comment(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_block_comments_excluded_from_denominator(self):
        # A block comment does not count toward code lines
        block = "/*\n * This is a block comment.\n */\n"
        src   = _code(5) + block * 5   # 5 code + 5 block comments (15 lines)
        # denominator = 5 code, numerator = 0 blank → ratio=0.00 → error
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_code_line_with_trailing_comment_counts_as_code(self):
        # "func(); // reason" is a CODE line, not blank and not a comment line
        src = "func_0(); // why we call this\n" + _code(9, start=1)
        # code_lines=10, blank_lines=0 → ratio=0.00 → error
        self.assertTrue(has(src, CFG, RULE))

    def test_mixed_blanks_and_comments_ratio_correct(self):
        # 10 code, 2 blank, 5 comments → ratio = 2/10 = 0.20 >= 0.10 → clean
        src = _code(5) + _blank(1) + _comment(5) + _blank(1) + _code(5, start=5)
        self.assertFalse(has(src, CFG, RULE))


# ---------------------------------------------------------------------------
# Violation message content
# ---------------------------------------------------------------------------

class TestWhitespaceRatioMessage(unittest.TestCase):

    def test_message_contains_ratio_and_counts(self):
        src = _code(10)   # 0 blank / 10 code
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        msg = viols[0].message
        self.assertIn("0.00", msg)
        self.assertIn("0 blank", msg)
        self.assertIn("10 code", msg)

    def test_message_mentions_threshold(self):
        # 1 blank / 20 code = 0.05 — between thresholds → warning threshold in msg
        src = _code(1) + _blank(1) + _code(19, start=1)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertIn("0.1", viols[0].message)   # warning threshold

    def test_message_says_error_threshold_when_below_error(self):
        src = _code(10)   # 0/10 → below error threshold
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertIn("error", viols[0].message)

    def test_violation_reported_at_line_1(self):
        src = _code(10)
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].line, 1)

    def test_singular_blank_line_grammar(self):
        # "1 blank line" not "1 blank lines"
        src = _code(1) + _blank(1) + _code(19, start=1)   # 1 blank / 20 code
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertIn("1 blank line", viols[0].message)
        self.assertNotIn("1 blank lines", viols[0].message)

    def test_plural_blank_lines_grammar(self):
        # "2 blank lines" not "2 blank line"
        src = _code(1) + _blank(2) + _code(39, start=1)   # 2 blank / 40 code = 0.05
        viols = [v for v in run(src, CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertIn("2 blank lines", viols[0].message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
