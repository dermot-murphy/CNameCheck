"""test_typedefs.py — tests for typedef.case and typedef.suffix rules.

RE_TYPEDEF_SIMPLE matches single-token typedefs: typedef <one_token> ALIAS;
Multi-token types (typedef unsigned int X) are not captured by this regex
and are therefore not checked — by design.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean

TD_CFG = cfg_only(
    typedefs={"enabled": True, "severity": "warning",
              "case": "upper_snake",
              "suffix": {"enabled": True, "suffix": "_T"}},
)

class TestTypedefCase(unittest.TestCase):
    def test_upper_snake_with_suffix_passes(self):
        self.assertTrue(clean("typedef uint32_t UART_STATUS_T;\n", TD_CFG))

    def test_lower_snake_fails(self):
        """Single-token alias that is lower_snake triggers typedef.case."""
        self.assertTrue(has("typedef uint32_t uart_status_T;\n", TD_CFG,
                            "typedef.case"))

    def test_mixed_case_fails(self):
        self.assertTrue(has("typedef uint32_t UartStatus_T;\n", TD_CFG,
                            "typedef.case"))

    def test_struct_typedef_checked(self):
        """Struct-based typedef alias is also checked."""
        self.assertTrue(has("typedef struct uart_s uart_cfg_T;\n", TD_CFG,
                            "typedef.case"))

class TestTypedefSuffix(unittest.TestCase):
    def test_correct_suffix_passes(self):
        self.assertFalse(has("typedef uint32_t UART_STATUS_T;\n", TD_CFG,
                              "typedef.suffix"))

    def test_missing_suffix_fails(self):
        self.assertTrue(has("typedef uint32_t UART_STATUS;\n", TD_CFG,
                            "typedef.suffix"))

    def test_wrong_suffix_fails(self):
        self.assertTrue(has("typedef uint32_t UART_STATUS_t;\n", TD_CFG,
                            "typedef.suffix"))

class TestTypedefDisabled(unittest.TestCase):
    def test_disabled_produces_no_violations(self):
        cfg = cfg_only(typedefs={"enabled": False})
        self.assertTrue(clean("typedef uint32_t bad_name;\n", cfg))

if __name__ == "__main__":
    unittest.main(verbosity=2)
