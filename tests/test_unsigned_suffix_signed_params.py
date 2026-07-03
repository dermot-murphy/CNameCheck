"""test_unsigned_suffix_signed_params.py — Tests for misc.unsigned_suffix
signed-parameter argument exemption (issue #340).

When an integer literal is passed as an argument to a function parameter
that is declared as a signed type (int8_t, int16_t, int, etc.), the
literal should NOT trigger the unsigned_suffix rule even without a 'U'
suffix — a signed parameter cannot receive an unsigned literal in any
meaningful way.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, run

RULE = "misc.unsigned_suffix"
US_CFG = cfg_only(misc={"unsigned_suffix": {"enabled": True, "severity": "info",
                                             "require_on_unsigned_constants": True}})


class TestSignedParamArgExempt(unittest.TestCase):
    """Literals at signed-parameter positions must NOT trigger unsigned_suffix."""

    def test_int8_param_literal_exempt(self):
        src = ("static void uart_SetBaud(int8_t scale) { (void)scale; }\n"
               "void f(void) { uart_SetBaud(80); }\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_int16_param_literal_exempt(self):
        src = ("static void uart_Init(int16_t val) { (void)val; }\n"
               "void f(void) { uart_Init(1000); }\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_int32_param_literal_exempt(self):
        src = ("static void uart_SetTimeout(int32_t ms) { (void)ms; }\n"
               "void f(void) { uart_SetTimeout(5000); }\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_plain_int_param_literal_exempt(self):
        src = ("static void uart_Write(int ch) { (void)ch; }\n"
               "void f(void) { uart_Write(65); }\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_second_param_signed_exempt(self):
        """Only the signed-parameter position should be exempt."""
        src = ("static void uart_SetPins(uint8_t pin, int8_t level)"
               "{ (void)pin; (void)level; }\n"
               "void f(void) { uart_SetPins(3U, 1); }\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_unsigned_param_literal_still_flagged(self):
        """A literal at an UNSIGNED-parameter position must still be flagged."""
        src = ("static void uart_SetPin(uint8_t pin) { (void)pin; }\n"
               "void f(void) { uart_SetPin(3); }\n")
        viols = [v for v in run(src, US_CFG) if v.rule == RULE]
        self.assertTrue(viols, "Expected unsigned_suffix violation for uint8_t param")

    def test_declaration_in_same_file(self):
        """Function declared (not defined) in the same file — exempts signed args."""
        src = ("void uart_SetGain(int8_t gain);\n"
               "void f(void) { uart_SetGain(42); }\n")
        self.assertFalse(has(src, US_CFG, RULE))


class TestSignedParamArgExemptMultiFile(unittest.TestCase):
    """Cross-file cases: if the declaration is NOT in the scanned file,
    the literal is NOT automatically exempt (user must use exempt_function_args)."""

    def test_unknown_function_literal_flagged(self):
        """A function with no local declaration: literal still flagged."""
        src = "void f(void) { unknown_fn(80); }\n"
        viols = [v for v in run(src, US_CFG) if v.rule == RULE]
        self.assertTrue(viols, "Expected unsigned_suffix violation for unknown function")

    def test_exempt_function_args_still_works(self):
        """The existing exempt_function_args config option still exempts all args."""
        cfg = cfg_only(misc={"unsigned_suffix": {
            "enabled": True, "severity": "info",
            "require_on_unsigned_constants": True,
            "exempt_function_args": ["api_vibration_set"],
        }})
        src = "void f(void) { api_vibration_set(80); }\n"
        self.assertFalse(has(src, cfg, RULE))


class TestSignedVarComparisonExempt(unittest.TestCase):
    """Issue #348: literals compared against signed local variables must not
    trigger misc.unsigned_suffix — adding U would change comparison semantics."""

    def test_less_than_signed_var_not_flagged(self):
        """if (1 < x) where x is int16_t — no violation."""
        src = ("void f(void) {\n"
               "    int16_t x;\n"
               "    if (1 < x) {}\n"
               "}\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_not_equal_signed_var_not_flagged(self):
        """if (x != 1) where x is int32_t — no violation on 1."""
        src = ("void f(void) {\n"
               "    int32_t count;\n"
               "    if (count != 1) {}\n"
               "}\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_greater_than_signed_var_not_flagged(self):
        """if (0 < count) where count is int8_t — no violation."""
        src = ("void f(void) {\n"
               "    int8_t delta;\n"
               "    if (0 < delta) {}\n"
               "}\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_geq_signed_var_not_flagged(self):
        """if (remaining >= 1) where remaining is int16_t — no violation."""
        src = ("void f(void) {\n"
               "    int16_t remaining;\n"
               "    if (remaining >= 1) {}\n"
               "}\n")
        self.assertFalse(has(src, US_CFG, RULE))

    def test_unsigned_var_comparison_still_flagged(self):
        """Comparison against UNSIGNED var — violation still raised."""
        src = ("void f(void) {\n"
               "    uint16_t u_val;\n"
               "    if (1 < u_val) {}\n"
               "}\n")
        viols = [v for v in run(src, US_CFG) if v.rule == RULE]
        self.assertTrue(viols, "Expected unsigned_suffix for comparison with uint16_t")

    def test_already_suffixed_no_violation(self):
        """1U < signed_var already has suffix — no violation regardless."""
        src = ("void f(void) {\n"
               "    int16_t x;\n"
               "    if (1U < x) {}\n"
               "}\n")
        self.assertFalse(has(src, US_CFG, RULE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
