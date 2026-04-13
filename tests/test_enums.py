"""test_enums.py — tests for enum.type_case, enum.type_suffix,
enum.member_case, enum.member_prefix rules.

Note: RE_ENUM_MEMBER requires a comma, = or } after the member name.
Use two or more members (with commas) so the non-last member is captured.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean

ENUM_CFG = cfg_only(
    enums={"enabled": True, "severity": "error",
           "type_case": "lower_snake",
           "type_suffix": {"enabled": True, "suffix": "_t"},
           "member_case": "upper_snake",
           "member_prefix_from_type": {"enabled": True, "severity": "warning"}},
)

class TestEnumTypeCase(unittest.TestCase):
    def test_lower_snake_type_passes(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } uart_state_t;\n"
        self.assertFalse(has(src, ENUM_CFG, "enum.type_case"))

    def test_upper_snake_type_fails(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } UART_STATE_T;\n"
        self.assertTrue(has(src, ENUM_CFG, "enum.type_case"))

    def test_camel_type_fails(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } UartState_t;\n"
        self.assertTrue(has(src, ENUM_CFG, "enum.type_case"))

class TestEnumTypeSuffix(unittest.TestCase):
    def test_correct_suffix_passes(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } uart_state_t;\n"
        self.assertFalse(has(src, ENUM_CFG, "enum.type_suffix"))

    def test_missing_suffix_fails(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } uart_state;\n"
        self.assertTrue(has(src, ENUM_CFG, "enum.type_suffix"))

class TestEnumMemberCase(unittest.TestCase):
    def test_upper_snake_members_pass(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } uart_state_t;\n"
        self.assertFalse(has(src, ENUM_CFG, "enum.member_case"))

    def test_lower_snake_member_fails(self):
        src = "typedef enum { uart_state_idle, uart_state_busy } uart_state_t;\n"
        self.assertTrue(has(src, ENUM_CFG, "enum.member_case"))

class TestEnumMemberPrefix(unittest.TestCase):
    def test_correct_prefix_passes(self):
        src = "typedef enum { UART_STATE_IDLE, UART_STATE_BUSY } uart_state_t;\n"
        self.assertFalse(has(src, ENUM_CFG, "enum.member_prefix"))

    def test_wrong_prefix_fails(self):
        """Members that don't start with the derived prefix are flagged."""
        src = "typedef enum { STATE_IDLE, STATE_BUSY } uart_state_t;\n"
        self.assertTrue(has(src, ENUM_CFG, "enum.member_prefix"))

    def test_prefix_derived_from_type_name(self):
        """Different type name → different required prefix."""
        src = "typedef enum { MOTOR_CTRL_STOP, MOTOR_CTRL_RUN } motor_ctrl_t;\n"
        self.assertFalse(has(src, ENUM_CFG, "enum.member_prefix"))

class TestEnumDisabled(unittest.TestCase):
    def test_disabled_produces_no_violations(self):
        cfg = cfg_only(enums={"enabled": False})
        src = "typedef enum { bad, WRONG } BadType;\n"
        self.assertTrue(clean(src, cfg))

if __name__ == "__main__":
    unittest.main(verbosity=2)
