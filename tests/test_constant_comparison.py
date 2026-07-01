"""test_constant_comparison.py — Tests for misc.constant_comparison rule.

Flags == and != where BOTH sides are compile-time constants (literals,
ALL_CAPS macros, true/false/NULL/nullptr).  This is almost certainly a
logic error because the result never changes at runtime.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count, messages

RULE = "misc.constant_comparison"
CC_CFG = cfg_only(misc={"constant_comparison": {"enabled": True,
                                                  "severity": "warning"}})
CC_OFF  = cfg_only(misc={"constant_comparison": {"enabled": False}})
CC_ERR  = cfg_only(misc={"constant_comparison": {"enabled": True,
                                                   "severity": "error"}})


class TestConstantComparisonViolations(unittest.TestCase):
    """Cases where both sides are constants — must be flagged."""

    def test_null_eq_null(self):
        self.assertTrue(has(
            "void f(void){ if (NULL == NULL) {} }", CC_CFG, RULE))

    def test_true_eq_false(self):
        self.assertTrue(has(
            "void f(void){ if (true == false) {} }", CC_CFG, RULE))

    def test_caps_eq_caps(self):
        self.assertTrue(has(
            "void f(void){ if (ERROR == SUCCESS) {} }", CC_CFG, RULE))

    def test_caps_neq_caps(self):
        self.assertTrue(has(
            "void f(void){ if (STATE_A != STATE_B) {} }", CC_CFG, RULE))

    def test_zero_eq_zero(self):
        self.assertTrue(has(
            "void f(void){ if (0 == 0) {} }", CC_CFG, RULE))

    def test_hex_eq_caps(self):
        self.assertTrue(has(
            "void f(void){ if (0xFF == MAX_BYTE) {} }", CC_CFG, RULE))

    def test_bool_keyword_eq_bool_keyword(self):
        self.assertTrue(has(
            "void f(void){ if (TRUE == FALSE) {} }", CC_CFG, RULE))

    def test_nullptr_eq_null(self):
        self.assertTrue(has(
            "void f(void){ if (nullptr == NULL) {} }", CC_CFG, RULE))


class TestConstantComparisonPasses(unittest.TestCase):
    """Cases with one or both sides variable — must NOT be flagged."""

    def test_var_eq_null_not_flagged(self):
        """Yoda-style (constant on left, variable on right) must not be flagged here."""
        self.assertFalse(has(
            "void f(void){ if (NULL == p_ptr) {} }", CC_CFG, RULE))

    def test_var_neq_null_not_flagged(self):
        self.assertFalse(has(
            "void f(void){ if (p_ptr != NULL) {} }", CC_CFG, RULE))

    def test_var_eq_var_not_flagged(self):
        self.assertFalse(has(
            "void f(void){ if (a == b) {} }", CC_CFG, RULE))

    def test_var_eq_caps_not_flagged(self):
        """Variable on left, ALL_CAPS constant on right — not constant_comparison."""
        self.assertFalse(has(
            "void f(void){ if (state == ERROR_CODE) {} }", CC_CFG, RULE))


class TestConstantComparisonExemptContexts(unittest.TestCase):
    """Contexts that should be exempt from this rule."""

    def test_define_rhs_exempt(self):
        self.assertFalse(has(
            "#define IS_BOTH(x) ((x) == NULL)\n", CC_CFG, RULE))

    def test_return_statement_exempt(self):
        self.assertFalse(has(
            "int f(void){ return (NULL == NULL); }", CC_CFG, RULE))


class TestConstantComparisonControl(unittest.TestCase):
    def test_disabled_produces_no_violations(self):
        self.assertFalse(has(
            "void f(void){ if (NULL == NULL) {} }", CC_OFF, RULE))

    def test_severity_warning_default(self):
        viols = [v for v in run(
            "void f(void){ if (NULL == NULL) {} }", CC_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_severity_error_override(self):
        viols = [v for v in run(
            "void f(void){ if (NULL == NULL) {} }", CC_ERR) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_message_contains_operator_and_operands(self):
        msgs = messages("void f(void){ if (NULL == NULL) {} }", CC_CFG)
        cc_msgs = [m for m in msgs if "NULL == NULL" in m or "==" in m]
        self.assertTrue(cc_msgs)

    def test_count_two_violations(self):
        src = ("void f(void){\n"
               "    if (NULL == NULL) {}\n"
               "    if (ERROR == SUCCESS) {}\n"
               "    if (a == b) {}\n"
               "}\n")
        self.assertEqual(count(src, CC_CFG, RULE), 2)


class TestConstantComparisonNotYoda(unittest.TestCase):
    """Verify constant_comparison and yoda_condition do not overlap."""

    def test_yoda_violation_not_flagged_by_cc(self):
        """variable == constant is a YODA violation, not a constant comparison."""
        self.assertFalse(has(
            "void f(void){ if (flag == NULL) {} }", CC_CFG, RULE))

    def test_correct_yoda_not_flagged_by_cc(self):
        """NULL == variable is correct YODA style; neither rule should fire."""
        self.assertFalse(has(
            "void f(void){ if (NULL == p_ptr) {} }", CC_CFG, RULE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
