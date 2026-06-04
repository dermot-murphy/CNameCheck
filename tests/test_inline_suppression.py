"""test_inline_suppression.py — Tests for inline suppression comments.

Covers parse_inline_suppressions() and end-to-end suppression behaviour via
the Checker class.
"""
import sys, tempfile, textwrap, unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC  = _HERE.parent / "src"
sys.path.insert(0, str(_SRC))

from cstylecheck.preprocessor import parse_inline_suppressions
from cstylecheck.checker import Checker

_YAML = _HERE / "rules.yml"
if not _YAML.exists():
    _YAML = _SRC / "rules.yml"

import yaml
with open(_YAML) as _f:
    _CFG = yaml.safe_load(_f)


def _check(source: str) -> list:
    """Run checker on source and return list of (line, rule) tuples."""
    c = Checker("test.c", source, _CFG)
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
        self.assertNotIn(1, s)   # directive line not suppressed
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
        self.assertNotIn(4, s)   # enable line itself not suppressed
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
            #include <stdint.h>
            uint8_t uart_Init(void) {
                uint8_t uart_val = 42;  // cstylecheck: disable=misc.magic_number
                return uart_val;
            }
        """)
        violations = _check(src)
        magic_violations = [r for _, r in violations if r == "misc.magic_number"]
        self.assertEqual(magic_violations, [])

    def test_magic_number_not_suppressed_without_comment(self):
        src = textwrap.dedent("""\
            #include <stdint.h>
            uint8_t uart_Init(void) {
                uint8_t uart_val = 42;
                return uart_val;
            }
        """)
        violations = _check(src)
        magic_violations = [r for _, r in violations if r == "misc.magic_number"]
        self.assertGreater(len(magic_violations), 0)

    def test_disable_next_line_suppresses_next_line_only(self):
        src = textwrap.dedent("""\
            #include <stdint.h>
            uint8_t uart_Init(void) {
                // cstylecheck: disable-next-line=misc.magic_number
                uint8_t uart_val = 42;
                uint8_t uart_val2 = 99;
                return uart_val;
            }
        """)
        violations = _check(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(4, magic_by_line)   # next line — suppressed
        self.assertIn(5, magic_by_line)      # line after — not suppressed

    def test_block_suppression(self):
        src = textwrap.dedent("""\
            #include <stdint.h>
            uint8_t uart_Init(void) {
                // cstylecheck: disable=misc.magic_number
                uint8_t uart_a = 42;
                uint8_t uart_b = 99;
                // cstylecheck: enable=misc.magic_number
                uint8_t uart_c = 77;
                return uart_a;
            }
        """)
        violations = _check(src)
        magic_by_line = {ln for ln, r in violations if r == "misc.magic_number"}
        self.assertNotIn(4, magic_by_line)
        self.assertNotIn(5, magic_by_line)
        self.assertIn(7, magic_by_line)

    def test_explicit_empty_suppression_map_disables_auto_parse(self):
        src = 'int x;  // cstylecheck: disable=misc.magic_number\n'
        c = Checker("test.c", src, _CFG, inline_suppressions={})
        # With empty map passed explicitly, auto-parse is skipped
        self.assertEqual(c._inline_suppressions, {})


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
