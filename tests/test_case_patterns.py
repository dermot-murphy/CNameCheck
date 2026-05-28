"""test_case_patterns.py — regression tests for _CASE_PATTERNS (issue #74).

lower and upper styles must not accept underscores; lower_snake / upper_snake
must continue to accept them.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from cstylecheck import matches_case


class TestCasePatterns(unittest.TestCase):
    """SWE4-TC-CASE-STYLE-001 to 006 — issue #74 regression suite."""

    # SWE4-TC-CASE-STYLE-001
    def test_lower_rejects_underscore(self):
        """'lower' must not accept names with underscores."""
        self.assertFalse(matches_case("bad_name", "lower"))

    # SWE4-TC-CASE-STYLE-002
    def test_lower_accepts_alphanumeric(self):
        """'lower' must accept names with only lowercase letters and digits."""
        self.assertTrue(matches_case("goodname1", "lower"))

    # SWE4-TC-CASE-STYLE-003
    def test_upper_rejects_underscore(self):
        """'upper' must not accept names with underscores."""
        self.assertFalse(matches_case("BAD_NAME", "upper"))

    # SWE4-TC-CASE-STYLE-004
    def test_upper_accepts_alphanumeric(self):
        """'upper' must accept names with only uppercase letters and digits."""
        self.assertTrue(matches_case("GOODNAME1", "upper"))

    # SWE4-TC-CASE-STYLE-005
    def test_lower_snake_still_accepts_underscore(self):
        """'lower_snake' must still accept names with underscores."""
        self.assertTrue(matches_case("good_name", "lower_snake"))

    # SWE4-TC-CASE-STYLE-006
    def test_upper_snake_still_accepts_underscore(self):
        """'upper_snake' must still accept names with underscores."""
        self.assertTrue(matches_case("GOOD_NAME", "upper_snake"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
