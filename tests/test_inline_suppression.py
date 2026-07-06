"""test_inline_suppression.py — Tests for inline suppression comments.

Covers parse_inline_suppressions() and end-to-end suppression via Checker.
"""
import sys
import os
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from harness import Checker, parse_inline_suppressions, cfg_only, run, has  # noqa: E402

_MN_CFG = cfg_only(misc={
    "magic_numbers": {"enabled": True, "severity": "warning",
                      "exempt_values": [0, 1]},
})


def _violations(source: str, cfg=None) -> list:
    """Return list of (line, rule) from checker."""
    c = Checker("test.c", source, cfg or _MN_CFG)
    return [(v.line, v.rule) for v in c.run_all().violations]


# ---------------------------------------------------------------------------
class TestParseInlineSuppressions(unittest.TestCase):

    def test_same_line_single_rule(self):
        src = 'int x = 1234;  // cstylecheck: disable=misc.magic_number\n'
        s = parse_inline_suppressions(src)
        self.assertIn(1, s)
        self.assertIn("misc.magic_number", s[1])

    def test_same_line_multiple_rules(self):
        src = 'int x;  // cstylecheck: disable=variables.case, misc.magic_number\n'
        s = parse_inline_suppressions(src)
        self.assertIn("variables.case", s[1])
        self.assertIn("misc.magic_number", s[1])

    def test_same_line_all_rules(self):
        src = 'int x;  // cstylecheck: disable\n'
        s = parse_inline_suppressions(src)
        self.assertIn("*", s[1])

    def test_disable_next_line_single_rule(self):
        src = '// cstylecheck: disable-next-line=misc.magic_number\nint x = 1234;\n'
        s = parse_inline_suppressions(src)
        self.assertNotIn(1, s)
        self.assertIn(2, s)
        self.assertIn("misc.magic_number", s[2])

    def test_disable_next_line_all_rules(self):
        src = '// cstylecheck: disable-next-line\nint x = 1234;\n'
        s = parse_inline_suppressions(src)
        self.assertIn("*", s[2])

    def test_block_disable_enable(self):
        src = textwrap.dedent("""\
            // cstylecheck: disable=variables.case
            int BadName = 1;
            int AnotherBad = 2;
            // cstylecheck: enable=variables.case
            int good_name = 3;
        """)
        s = parse_inline_suppressions(src)
        self.assertIn("variables.case", s.get(2, frozenset()))
        self.assertIn("variables.case", s.get(3, frozenset()))
        self.assertNotIn(4, s)
        self.assertNotIn(5, s)

    def test_block_disable_all_enable_all(self):
        src = textwrap.dedent("""\
            // cstylecheck: disable
            int BadName = 1;
            // cstylecheck: enable
            int good_name = 2;
        """)
        s = parse_inline_suppressions(src)
        self.assertIn("*", s.get(2, frozenset()))
        self.assertNotIn(4, s)

    def test_no_suppressions(self):
        src = 'int x = 1;\n'
        s = parse_inline_suppressions(src)
        self.assertEqual(s, {})

    def test_case_insensitive(self):
        src = 'int x;  // CStyleCheck: DISABLE=misc.magic_number\n'
        s = parse_inline_suppressions(src)
        self.assertIn("misc.magic_number", s.get(1, frozenset()))


# ---------------------------------------------------------------------------
class TestCheckerInlineSuppression(unittest.TestCase):

    def test_magic_number_suppressed_same_line(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                int uart_val = 42;  // cstylecheck: disable=misc.magic_number
                return uart_val;
            }
        """)
        violations = _violations(src)
        self.assertNotIn("misc.magic_number", [r for _, r in violations])

    def test_magic_number_not_suppressed_without_comment(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                int uart_val = 42;
                return uart_val;
            }
        """)
        violations = _violations(src)
        self.assertIn("misc.magic_number", [r for _, r in violations])

    def test_disable_next_line_suppresses_next_line_only(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                // cstylecheck: disable-next-line=misc.magic_number
                int uart_val = 42;
                int uart_val2 = 99;
                return uart_val;
            }
        """)
        violations = _violations(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(3, magic_by_line)
        self.assertIn(4, magic_by_line)

    def test_block_suppression(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                // cstylecheck: disable=misc.magic_number
                int uart_a = 42;
                int uart_b = 99;
                // cstylecheck: enable=misc.magic_number
                int uart_c = 77;
                return uart_a;
            }
        """)
        violations = _violations(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(3, magic_by_line)
        self.assertNotIn(4, magic_by_line)
        self.assertIn(6, magic_by_line)

    def test_disable_all_suppresses_all_rules(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                int uart_val = 42;  // cstylecheck: disable
                return uart_val;
            }
        """)
        violations = _violations(src)
        magic_violations = [r for _, r in violations if r == "misc.magic_number"]
        self.assertEqual(magic_violations, [])

    def test_explicit_empty_suppression_map_disables_auto_parse(self):
        src = 'int x;  // cstylecheck: disable=misc.magic_number\n'
        c = Checker("test.c", src, _MN_CFG, inline_suppressions={})
        self.assertEqual(c._inline_suppressions, {})


# ---------------------------------------------------------------------------
class TestBlockCommentSuppression(unittest.TestCase):
    """Issue #360: /* cstylecheck: disable=... */ block-comment syntax must
    be recognised in addition to // comments."""

    def test_block_comment_same_line_single_rule(self):
        src = 'int x = 1234;  /* cstylecheck: disable=misc.magic_number */\n'
        s = parse_inline_suppressions(src)
        self.assertIn("misc.magic_number", s.get(1, frozenset()))

    def test_block_comment_block_disable_enable(self):
        src = textwrap.dedent("""\
            /* cstylecheck: disable=misc.magic_number */
            int uart_a = 42;
            int uart_b = 99;
            /* cstylecheck: enable=misc.magic_number */
            int uart_c = 77;
        """)
        s = parse_inline_suppressions(src)
        self.assertIn("misc.magic_number", s.get(2, frozenset()))
        self.assertIn("misc.magic_number", s.get(3, frozenset()))
        self.assertNotIn(5, s)

    def test_block_comment_disable_multiple_rules(self):
        src = textwrap.dedent("""\
            /* cstylecheck: disable=misc.magic_number, variables.case */
            int BadName = 42;
            /* cstylecheck: enable=misc.magic_number, variables.case */
        """)
        s = parse_inline_suppressions(src)
        self.assertIn("misc.magic_number", s.get(2, frozenset()))
        self.assertIn("variables.case", s.get(2, frozenset()))

    def test_block_comment_suppress_end_to_end(self):
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                /* cstylecheck: disable=misc.magic_number */
                int uart_a = 42;
                int uart_b = 99;
                /* cstylecheck: enable=misc.magic_number */
                int uart_c = 77;
                return uart_a;
            }
        """)
        violations = _violations(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(3, magic_by_line)
        self.assertNotIn(4, magic_by_line)
        self.assertIn(6, magic_by_line)

    def test_slashslash_comment_still_works(self):
        """Existing // syntax must continue to work after adding /* support."""
        src = textwrap.dedent("""\
            uint8_t uart_Init(void) {
                // cstylecheck: disable=misc.magic_number
                int uart_a = 42;
                // cstylecheck: enable=misc.magic_number
                int uart_b = 77;
                return uart_a;
            }
        """)
        violations = _violations(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(3, magic_by_line)
        self.assertIn(5, magic_by_line)


# ---------------------------------------------------------------------------
_FP_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error"},
    functions={"enabled": True, "severity": "error"},
)


class TestFunctionPrefixBlockCommentSuppression(unittest.TestCase):
    """Inline suppression of function.prefix via /* */ block-comment syntax.

    RE_FUNCTION_DEF starts with (?:^|\\n) so m.start() used to point to the
    '\\n' ending the *previous* line, placing the violation one line before the
    function itself and outside the suppression block.  The fn_start correction
    in _check_functions() must ensure the violation lands on the function's own
    line so the suppression map can match it.
    """

    def _run(self, src: str) -> set:
        c = Checker("hal_ble.c", src, _FP_CFG)
        return {(v.line, v.rule) for v in c.run_all().violations}

    def test_function_prefix_fires_without_suppression(self):
        src = textwrap.dedent("""\
            void assert_nrf_callback(uint16_t line_num, const uint8_t* file_name)
            {
                (void)line_num; (void)file_name;
            }
        """)
        viols = self._run(src)
        self.assertTrue(any(r == "function.prefix" for _, r in viols))

    def test_function_prefix_suppressed_by_block_comment_disable(self):
        src = textwrap.dedent("""\
            /* cstylecheck: disable=function.prefix */
            void assert_nrf_callback(uint16_t line_num, const uint8_t* file_name)
            {
                (void)line_num; (void)file_name;
            }
            /* cstylecheck: enable=function.prefix */
        """)
        viols = self._run(src)
        self.assertFalse(any(r == "function.prefix" for _, r in viols),
                         f"Expected no function.prefix violation; got {viols}")

    def test_function_prefix_suppressed_by_slashslash_disable(self):
        src = textwrap.dedent("""\
            // cstylecheck: disable=function.prefix
            void assert_nrf_callback(uint16_t line_num, const uint8_t* file_name)
            {
                (void)line_num; (void)file_name;
            }
            // cstylecheck: enable=function.prefix
        """)
        viols = self._run(src)
        self.assertFalse(any(r == "function.prefix" for _, r in viols),
                         f"Expected no function.prefix violation; got {viols}")

    def test_function_after_enable_is_still_checked(self):
        src = textwrap.dedent("""\
            /* cstylecheck: disable=function.prefix */
            void assert_nrf_callback(uint16_t line_num, const uint8_t* file_name)
            {
                (void)line_num; (void)file_name;
            }
            /* cstylecheck: enable=function.prefix */
            void another_bad_name(void)
            {
            }
        """)
        viols = self._run(src)
        prefix_lines = {ln for ln, r in viols if r == "function.prefix"}
        self.assertNotIn(2, prefix_lines)
        self.assertIn(7, prefix_lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
