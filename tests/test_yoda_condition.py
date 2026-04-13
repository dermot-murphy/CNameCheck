"""test_yoda_condition.py — tests for the misc.yoda_condition rule.

Yoda style: constant on the LEFT of == and !=.
  Correct:    if (NULL == p_buf)
  Violation:  if (p_buf == NULL)
Only == and != are checked; directional operators < > <= >= are excluded.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count, messages

RULE = "misc.yoda_condition"
YODA_CFG = cfg_only(misc={"yoda_conditions": {"enabled": True, "severity": "warning"}})
YODA_OFF  = cfg_only(misc={"yoda_conditions": {"enabled": False}})
YODA_ERR  = cfg_only(misc={"yoda_conditions": {"enabled": True, "severity": "error"}})


class TestYodaViolations(unittest.TestCase):
    """Cases where a constant is on the RHS — must be flagged."""

    def test_var_eq_null(self):
        self.assertTrue(has("void f(void){ if (p_buf == NULL) {} }", YODA_CFG, RULE))

    def test_var_neq_null(self):
        self.assertTrue(has("void f(void){ if (p_ptr != NULL) {} }", YODA_CFG, RULE))

    def test_var_eq_true(self):
        self.assertTrue(has("void f(void){ if (flag == true) {} }", YODA_CFG, RULE))

    def test_var_eq_false(self):
        self.assertTrue(has("void f(void){ if (done == false) {} }", YODA_CFG, RULE))

    def test_var_eq_TRUE(self):
        self.assertTrue(has("void f(void){ if (flag == TRUE) {} }", YODA_CFG, RULE))

    def test_var_eq_FALSE(self):
        self.assertTrue(has("void f(void){ if (done == FALSE) {} }", YODA_CFG, RULE))

    def test_var_eq_nullptr(self):
        self.assertTrue(has("void f(void){ if (p_obj == nullptr) {} }", YODA_CFG, RULE))

    def test_var_eq_decimal_literal(self):
        self.assertTrue(has("void f(void){ if (count == 0U) {} }", YODA_CFG, RULE))

    def test_var_eq_hex_literal(self):
        self.assertTrue(has("void f(void){ if (status == 0xFF) {} }", YODA_CFG, RULE))

    def test_var_eq_char_literal(self):
        self.assertTrue(has("void f(void){ if (ch == 'A') {} }", YODA_CFG, RULE))

    def test_var_eq_all_caps_macro(self):
        self.assertTrue(has("void f(void){ if (state == ERROR_CODE) {} }", YODA_CFG, RULE))

    def test_var_neq_false(self):
        self.assertTrue(has("void f(void){ if (b_running != false) {} }", YODA_CFG, RULE))

    def test_while_var_eq_const(self):
        self.assertTrue(has("void f(void){ while (done == false) {} }", YODA_CFG, RULE))


class TestYodaPasses(unittest.TestCase):
    """Cases with correct Yoda style — must NOT be flagged."""

    def test_null_eq_var(self):
        self.assertFalse(has("void f(void){ if (NULL == p_buf) {} }", YODA_CFG, RULE))

    def test_zero_eq_var(self):
        self.assertFalse(has("void f(void){ if (0U == count) {} }", YODA_CFG, RULE))

    def test_true_eq_var(self):
        self.assertFalse(has("void f(void){ if (true == flag) {} }", YODA_CFG, RULE))

    def test_macro_eq_var(self):
        self.assertFalse(has("void f(void){ if (ERROR_CODE == state) {} }", YODA_CFG, RULE))

    def test_hex_neq_var(self):
        self.assertFalse(has("void f(void){ if (0xFF != status) {} }", YODA_CFG, RULE))

    def test_while_const_eq_var(self):
        self.assertFalse(has("void f(void){ while (false == done) {} }", YODA_CFG, RULE))


class TestYodaNotChecked(unittest.TestCase):
    """Cases the rule intentionally ignores."""

    def test_var_eq_var_not_flagged(self):
        self.assertFalse(has("void f(void){ if (a == b) {} }", YODA_CFG, RULE))

    def test_const_eq_const_not_flagged(self):
        self.assertFalse(has("void f(void){ if (NULL == NULL) {} }", YODA_CFG, RULE))

    def test_macro_neq_macro_not_flagged(self):
        self.assertFalse(has("void f(void){ if (STATE_A != STATE_B) {} }", YODA_CFG, RULE))

    def test_lt_not_checked(self):
        self.assertFalse(has("void f(void){ if (count < MAX) {} }", YODA_CFG, RULE))

    def test_gt_not_checked(self):
        self.assertFalse(has("void f(void){ if (level > THRESHOLD) {} }", YODA_CFG, RULE))

    def test_le_not_checked(self):
        self.assertFalse(has("void f(void){ if (count <= MAX_SIZE) {} }", YODA_CFG, RULE))

    def test_ge_not_checked(self):
        self.assertFalse(has("void f(void){ if (val >= MIN_VAL) {} }", YODA_CFG, RULE))

    def test_single_uppercase_not_a_macro(self):
        """A single uppercase letter is not treated as an ALL_CAPS constant."""
        self.assertFalse(has("void f(void){ if (x == A) {} }", YODA_CFG, RULE))


class TestYodaExemptContexts(unittest.TestCase):
    def test_define_rhs_exempt(self):
        self.assertFalse(has("#define IS_READY(x) ((x) == READY_FLAG)\n",
                              YODA_CFG, RULE))

    def test_return_statement_exempt(self):
        self.assertFalse(has("int f(void){ return (result == 0U); }", YODA_CFG, RULE))


class TestYodaCounting(unittest.TestCase):
    def test_two_violations_counted(self):
        src = ("void f(void){\n"
               "    if (a == NULL) {}\n"
               "    if (NULL == b) {}\n"
               "    if (c == true) {}\n"
               "    if (false == d) {}\n"
               "}")
        self.assertEqual(count(src, YODA_CFG, RULE), 2)


class TestYodaMessage(unittest.TestCase):
    def test_message_shows_corrected_form(self):
        src = "void f(void){ if (flag == NULL) {} }"
        msgs = messages(src, YODA_CFG)
        yoda = [m for m in msgs if "NULL" in m]
        self.assertTrue(yoda)
        self.assertIn("NULL == flag", yoda[0])

    def test_message_includes_operator(self):
        src = "void f(void){ if (x != FALSE) {} }"
        msgs = messages(src, YODA_CFG)
        self.assertTrue(any("!=" in m for m in msgs))


class TestYodaSeverityAndControl(unittest.TestCase):
    def test_default_severity_warning(self):
        src = "void f(void){ if (x == NULL) {} }"
        viols = [v for v in run(src, YODA_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "warning")

    def test_custom_severity_error(self):
        src = "void f(void){ if (x == NULL) {} }"
        viols = [v for v in run(src, YODA_ERR) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_disabled_produces_no_violations(self):
        src = "void f(void){ if (x == NULL) {} }"
        self.assertFalse(has(src, YODA_OFF, RULE))

    def test_violation_on_correct_line(self):
        src = ("void f(void){\n"
               "    int x = 0;\n"
               "    if (x == NULL) {}\n"
               "}\n")
        viols = [v for v in run(src, YODA_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertEqual(viols[0].line, 3)

    def test_column_is_positive(self):
        src = "void f(void){ if (flag == true) {} }"
        viols = [v for v in run(src, YODA_CFG) if v.rule == RULE]
        self.assertTrue(viols)
        self.assertGreater(viols[0].col, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
