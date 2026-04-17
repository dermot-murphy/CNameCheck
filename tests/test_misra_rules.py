"""test_misra_rules.py
=====================
Unit tests for the three MISRA C:2012/2023 checks added by NR-001/002/003:

  NR-001  misc.lowercase_l_suffix  — MISRA C Rule 7.3 (Required)
  NR-002  misc.octal_constant      — MISRA C Rule 7.1 (Required)
  NR-003  misc.trigraph            — MISRA C Rule 4.2 (Advisory/Required)

Each class documents the rule it covers, lists positive (should flag) and
negative (should not flag) cases, and verifies the violation message text.
Line/column positions are verified for representative cases.

ASPICE traceability
-------------------
  SWE1 requirements: SWE1-MISRA-001 (Rule 7.3), SWE1-MISRA-002 (Rule 7.1),
                     SWE1-MISRA-003 (Rule 4.2)
  SWE4 test IDs:     SWE4-TC-7.3-*, SWE4-TC-7.1-*, SWE4-TC-4.2-*
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from harness import cfg_only, run, has, clean, count

# ---------------------------------------------------------------------------
# Shared config builders
# ---------------------------------------------------------------------------

def _ll_cfg(enabled=True, severity="error"):
    """Config with only misc.lowercase_l_suffix enabled."""
    return cfg_only(misc={"lowercase_l_suffix": {
        "enabled": enabled,
        "severity": severity,
    }})


def _oc_cfg(enabled=True, severity="error"):
    """Config with only misc.octal_constant enabled."""
    return cfg_only(misc={"octal_constant": {
        "enabled": enabled,
        "severity": severity,
    }})


def _tg_cfg(enabled=True, severity="error"):
    """Config with only misc.trigraph enabled."""
    return cfg_only(misc={"trigraph": {
        "enabled": enabled,
        "severity": severity,
    }})


RULE_LL = "misc.lowercase_l_suffix"
RULE_OC = "misc.octal_constant"
RULE_TG = "misc.trigraph"


# ===========================================================================
# NR-001 — MISRA C Rule 7.3: lowercase 'l' suffix
# SWE4-TC-7.3-*
# ===========================================================================

class TestLowercaseLSuffix(unittest.TestCase):
    """MISRA C:2012/2023 Rule 7.3 — integer literal suffixes must be uppercase.

    The lowercase letter 'l' is visually identical to '1' in many fonts.
    """

    # -----------------------------------------------------------------------
    # SWE4-TC-7.3-001 to 7.3-006: positive tests (should flag)
    # -----------------------------------------------------------------------

    def test_plain_lowercase_l_flagged(self):
        """SWE4-TC-7.3-001: bare '1l' must be flagged."""
        src = "void f(void){ int x = 1l; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    def test_ul_suffix_lowercase_l_flagged(self):
        """SWE4-TC-7.3-002: '1ul' must be flagged (lowercase l in compound suffix)."""
        src = "void f(void){ unsigned long x = 1ul; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    def test_lu_suffix_flagged(self):
        """SWE4-TC-7.3-003: '1lu' must be flagged (l before u)."""
        src = "void f(void){ unsigned long x = 1lu; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    def test_hex_lowercase_l_flagged(self):
        """SWE4-TC-7.3-004: hex literal '0xFFl' must be flagged."""
        src = "void f(void){ long x = 0xFFl; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    def test_large_decimal_lowercase_l_flagged(self):
        """SWE4-TC-7.3-005: '100000l' must be flagged."""
        src = "void f(void){ long x = 100000l; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    def test_ll_suffix_lowercase_flagged(self):
        """SWE4-TC-7.3-006: '1ll' (long long, all lowercase) must be flagged."""
        src = "void f(void){ long long x = 1ll; (void)x; }\n"
        self.assertTrue(has(src, _ll_cfg(), RULE_LL))

    # -----------------------------------------------------------------------
    # SWE4-TC-7.3-007 to 7.3-013: negative tests (should NOT flag)
    # -----------------------------------------------------------------------

    def test_uppercase_L_not_flagged(self):
        """SWE4-TC-7.3-007: '1L' is valid (uppercase L)."""
        src = "void f(void){ long x = 1L; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_uppercase_UL_not_flagged(self):
        """SWE4-TC-7.3-008: '1UL' is valid."""
        src = "void f(void){ unsigned long x = 1UL; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_uppercase_LL_not_flagged(self):
        """SWE4-TC-7.3-009: '1LL' is valid (long long)."""
        src = "void f(void){ long long x = 1LL; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_u_suffix_only_not_flagged(self):
        """SWE4-TC-7.3-010: '1U' has no l/L suffix — not flagged."""
        src = "void f(void){ unsigned x = 1U; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_no_suffix_not_flagged(self):
        """SWE4-TC-7.3-011: plain '42' with no suffix is not flagged."""
        src = "void f(void){ int x = 42; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_hex_uppercase_L_not_flagged(self):
        """SWE4-TC-7.3-012: '0xFFL' is valid."""
        src = "void f(void){ long x = 0xFFL; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(), RULE_LL))

    def test_rule_disabled_not_flagged(self):
        """SWE4-TC-7.3-013: rule disabled in config suppresses violation."""
        src = "void f(void){ int x = 1l; (void)x; }\n"
        self.assertFalse(has(src, _ll_cfg(enabled=False), RULE_LL))

    # -----------------------------------------------------------------------
    # SWE4-TC-7.3-014: violation message content
    # -----------------------------------------------------------------------

    def test_violation_message_mentions_misra_rule(self):
        """SWE4-TC-7.3-014: message must reference MISRA C Rule 7.3."""
        src = "void f(void){ int x = 1l; (void)x; }\n"
        viols = [v for v in run(src, _ll_cfg()) if v.rule == RULE_LL]
        self.assertTrue(viols, "Expected at least one violation")
        self.assertIn("7.3", viols[0].message)
        self.assertIn("uppercase", viols[0].message.lower())

    # -----------------------------------------------------------------------
    # SWE4-TC-7.3-015: severity configurable
    # -----------------------------------------------------------------------

    def test_severity_is_configurable(self):
        """SWE4-TC-7.3-015: severity follows YAML configuration."""
        src = "void f(void){ int x = 1l; (void)x; }\n"
        viols = [v for v in run(src, _ll_cfg(severity="warning")) if v.rule == RULE_LL]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")


# ===========================================================================
# NR-002 — MISRA C Rule 7.1: octal constants forbidden
# SWE4-TC-7.1-*
# ===========================================================================

class TestOctalConstants(unittest.TestCase):
    """MISRA C:2012/2023 Rule 7.1 — octal integer constants shall not be used.

    An integer literal with a leading zero followed by octal digits (0–7) is
    an octal constant and is easy to confuse with a decimal literal.
    """

    # -----------------------------------------------------------------------
    # SWE4-TC-7.1-001 to 7.1-006: positive tests (should flag)
    # -----------------------------------------------------------------------

    def test_octal_010_flagged(self):
        """SWE4-TC-7.1-001: '010' (= decimal 8) must be flagged."""
        src = "void f(void){ int x = 010; (void)x; }\n"
        self.assertTrue(has(src, _oc_cfg(), RULE_OC))

    def test_octal_07_flagged(self):
        """SWE4-TC-7.1-002: '07' must be flagged."""
        src = "void f(void){ int x = 07; (void)x; }\n"
        self.assertTrue(has(src, _oc_cfg(), RULE_OC))

    def test_octal_0777_flagged(self):
        """SWE4-TC-7.1-003: '0777' (unix-style permission literal) must be flagged."""
        src = "void f(void){ int mode = 0777; (void)mode; }\n"
        self.assertTrue(has(src, _oc_cfg(), RULE_OC))

    def test_octal_with_u_suffix_flagged(self):
        """SWE4-TC-7.1-004: '07U' (octal with suffix) must be flagged."""
        src = "void f(void){ unsigned x = 07U; (void)x; }\n"
        self.assertTrue(has(src, _oc_cfg(), RULE_OC))

    def test_octal_leading_zeros_in_array_init_flagged(self):
        """SWE4-TC-7.1-005: octal in array initialiser must be flagged."""
        src = "int arr[] = {01, 02, 03};\n"
        self.assertGreaterEqual(count(src, _oc_cfg(), RULE_OC), 1)

    def test_octal_0_followed_by_octal_digit_in_macro_rhs(self):
        """SWE4-TC-7.1-006: octal in #define RHS is still an octal constant."""
        src = "#define MY_PERM 0755\nvoid f(void){}\n"
        # Even in a #define this is a valid octal constant violation
        self.assertTrue(has(src, _oc_cfg(), RULE_OC))

    # -----------------------------------------------------------------------
    # SWE4-TC-7.1-007 to 7.1-013: negative tests (should NOT flag)
    # -----------------------------------------------------------------------

    def test_zero_alone_not_flagged(self):
        """SWE4-TC-7.1-007: bare '0' is zero, not an octal constant."""
        src = "void f(void){ int x = 0; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_zero_with_u_suffix_not_flagged(self):
        """SWE4-TC-7.1-008: '0U' is zero — not octal."""
        src = "void f(void){ unsigned x = 0U; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_hex_literal_not_flagged(self):
        """SWE4-TC-7.1-009: '0x08' is hex, not octal."""
        src = "void f(void){ int x = 0x08; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_hex_0xFF_not_flagged(self):
        """SWE4-TC-7.1-010: '0xFF' must not be flagged."""
        src = "void f(void){ int x = 0xFF; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_float_0_point_5_not_flagged(self):
        """SWE4-TC-7.1-011: '0.5' is a float literal, not octal."""
        src = "void f(void){ float x = 0.5f; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_decimal_10_not_flagged(self):
        """SWE4-TC-7.1-012: decimal '10' with no leading zero is not octal."""
        src = "void f(void){ int x = 10; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(), RULE_OC))

    def test_rule_disabled_not_flagged(self):
        """SWE4-TC-7.1-013: rule disabled in config suppresses violation."""
        src = "void f(void){ int x = 010; (void)x; }\n"
        self.assertFalse(has(src, _oc_cfg(enabled=False), RULE_OC))

    # -----------------------------------------------------------------------
    # SWE4-TC-7.1-014: violation message content
    # -----------------------------------------------------------------------

    def test_violation_message_mentions_misra_rule(self):
        """SWE4-TC-7.1-014: message must reference MISRA C Rule 7.1."""
        src = "void f(void){ int x = 010; (void)x; }\n"
        viols = [v for v in run(src, _oc_cfg()) if v.rule == RULE_OC]
        self.assertTrue(viols, "Expected at least one violation")
        self.assertIn("7.1", viols[0].message)

    def test_violation_includes_octal_value(self):
        """SWE4-TC-7.1-015: message must include the offending literal."""
        src = "void f(void){ int x = 0777; (void)x; }\n"
        viols = [v for v in run(src, _oc_cfg()) if v.rule == RULE_OC]
        self.assertTrue(viols)
        self.assertIn("0777", viols[0].message)

    # -----------------------------------------------------------------------
    # SWE4-TC-7.1-016: severity configurable
    # -----------------------------------------------------------------------

    def test_severity_is_configurable(self):
        """SWE4-TC-7.1-016: severity follows YAML configuration."""
        src = "void f(void){ int x = 010; (void)x; }\n"
        viols = [v for v in run(src, _oc_cfg(severity="warning")) if v.rule == RULE_OC]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")


# ===========================================================================
# NR-003 — MISRA C Rule 4.2: trigraphs forbidden
# SWE4-TC-4.2-*
# ===========================================================================

class TestTrigraphs(unittest.TestCase):
    """MISRA C:2012 Rule 4.2 (Advisory) / MISRA C:2023 Rule 4.2 (Required).

    Trigraphs are ??X sequences that the preprocessor silently replaces.
    They must not appear anywhere in a C source file.
    """

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-001 to 4.2-009: one test per trigraph character
    # -----------------------------------------------------------------------

    def test_trigraph_hash_flagged(self):
        """SWE4-TC-4.2-001: '??=' (→ #) must be flagged."""
        src = "/* ??= comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_open_bracket_flagged(self):
        """SWE4-TC-4.2-002: '??(' (→ [) must be flagged."""
        src = "/* ??( comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_close_bracket_flagged(self):
        """SWE4-TC-4.2-003: '??)' (→ ]) must be flagged."""
        src = "/* ??) comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_backslash_flagged(self):
        """SWE4-TC-4.2-004: '??/' (→ \\) must be flagged."""
        src = "/* ??/ comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_caret_flagged(self):
        """SWE4-TC-4.2-005: \"??'\" (→ ^) must be flagged."""
        src = "/* ??' comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_open_brace_flagged(self):
        """SWE4-TC-4.2-006: '??<' (→ {) must be flagged."""
        src = "/* ??< comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_close_brace_flagged(self):
        """SWE4-TC-4.2-007: '??>' (→ }) must be flagged."""
        src = "/* ??> comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_pipe_flagged(self):
        """SWE4-TC-4.2-008: '??!' (→ |) must be flagged."""
        src = "/* ??! comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    def test_trigraph_tilde_flagged(self):
        """SWE4-TC-4.2-009: '??-' (→ ~) must be flagged."""
        src = "/* ??- comment */\nvoid f(void){}\n"
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-010: trigraph in code (not just comments)
    # -----------------------------------------------------------------------

    def test_trigraph_in_code_flagged(self):
        """SWE4-TC-4.2-010: trigraph in code (not just comments) is flagged."""
        # '??(' would be preprocessed to '[' — tool must flag it regardless
        src = 'char s??( = {0};\n'
        self.assertTrue(has(src, _tg_cfg(), RULE_TG))

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-011 to 4.2-013: negative tests
    # -----------------------------------------------------------------------

    def test_double_question_mark_not_trigraph(self):
        """SWE4-TC-4.2-011: '??' alone (not followed by a trigraph char) is OK."""
        src = "/* What?? No trigraph here. */\nvoid f(void){}\n"
        self.assertFalse(has(src, _tg_cfg(), RULE_TG))

    def test_single_question_mark_not_flagged(self):
        """SWE4-TC-4.2-012: single '?' in a ternary expression is OK."""
        src = "void f(int x){ int y = x ? 1 : 0; (void)y; }\n"
        self.assertFalse(has(src, _tg_cfg(), RULE_TG))

    def test_rule_disabled_not_flagged(self):
        """SWE4-TC-4.2-013: rule disabled in config suppresses violation."""
        src = "/* ??= */\nvoid f(void){}\n"
        self.assertFalse(has(src, _tg_cfg(enabled=False), RULE_TG))

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-014: violation message content
    # -----------------------------------------------------------------------

    def test_violation_message_mentions_misra_rule(self):
        """SWE4-TC-4.2-014: message must reference MISRA C Rule 4.2."""
        src = "/* ??= */\nvoid f(void){}\n"
        viols = [v for v in run(src, _tg_cfg()) if v.rule == RULE_TG]
        self.assertTrue(viols, "Expected at least one violation")
        self.assertIn("4.2", viols[0].message)

    def test_violation_includes_trigraph_sequence(self):
        """SWE4-TC-4.2-015: message must include the offending trigraph."""
        src = "/* ??= */\nvoid f(void){}\n"
        viols = [v for v in run(src, _tg_cfg()) if v.rule == RULE_TG]
        self.assertTrue(viols)
        self.assertIn("??=", viols[0].message)

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-016: line number accuracy
    # -----------------------------------------------------------------------

    def test_line_number_is_accurate(self):
        """SWE4-TC-4.2-016: violation line number must match actual location."""
        src = "/* clean line */\n/* ??= here */\nvoid f(void){}\n"
        viols = [v for v in run(src, _tg_cfg()) if v.rule == RULE_TG]
        self.assertTrue(viols)
        self.assertEqual(viols[0].line, 2)

    # -----------------------------------------------------------------------
    # SWE4-TC-4.2-017: severity configurable
    # -----------------------------------------------------------------------

    def test_severity_is_configurable(self):
        """SWE4-TC-4.2-017: severity follows YAML configuration."""
        src = "/* ??= */\nvoid f(void){}\n"
        viols = [v for v in run(src, _tg_cfg(severity="warning")) if v.rule == RULE_TG]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")


# ===========================================================================
# BUG-004 regression — Yoda condition message for negative-literal RHS
# ===========================================================================

class TestYodaNegativeLiteralMessage(unittest.TestCase):
    """Regression tests for BUG-004: Yoda violation message was showing
    the digit token without the leading '-' sign.

    e.g.  if (x == -1)  was producing  "write '1 == x'"
          instead of the correct        "write '-1 == x'"
    """

    def _yoda_cfg(self):
        return cfg_only(misc={"yoda_conditions": {
            "enabled": True,
            "severity": "warning",
        }})

    def test_negative_literal_message_includes_minus(self):
        """BUG-004: message for 'x == -1' must say '-1 == x', not '1 == x'."""
        src = "void f(int x){ if (x == -1) {} }\n"
        viols = [v for v in run(src, self._yoda_cfg())
                 if v.rule == "misc.yoda_condition"]
        self.assertTrue(viols, "Expected a Yoda violation")
        self.assertIn("-1", viols[0].message,
                      f"Message should include '-1': {viols[0].message}")
        # The message must NOT suggest the wrong correction
        self.assertNotIn("write '1 ==", viols[0].message,
                         f"Message incorrectly omits minus: {viols[0].message}")

    def test_negative_literal_detection_fires(self):
        """BUG-004: 'x == -1' must be detected as a Yoda violation."""
        src = "void f(int x){ if (x == -1) {} }\n"
        self.assertTrue(has(src, self._yoda_cfg(), "misc.yoda_condition"))

    def test_positive_literal_message_unchanged(self):
        """BUG-004: positive literal message is unaffected by the fix."""
        src = "void f(int x){ if (x == 42) {} }\n"
        viols = [v for v in run(src, self._yoda_cfg())
                 if v.rule == "misc.yoda_condition"]
        self.assertTrue(viols)
        self.assertIn("42", viols[0].message)

    def test_null_comparison_message_unchanged(self):
        """BUG-004: NULL comparison message is unaffected."""
        src = "void f(void *p){ if (p == NULL) {} }\n"
        viols = [v for v in run(src, self._yoda_cfg())
                 if v.rule == "misc.yoda_condition"]
        self.assertTrue(viols)
        self.assertIn("NULL", viols[0].message)


if __name__ == "__main__":
    unittest.main()
