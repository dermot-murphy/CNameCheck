"""test_include_guards.py — tests for include_guard.missing and
include_guard.format rules (headers only)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean

IG_CFG = cfg_only(
    include_guards={"enabled": True, "severity": "error",
                    "pattern": "{FILENAME_UPPER}_{EXT_UPPER}_",
                    "allow_pragma_once": True},
)

GOOD_GUARD = "#ifndef UART_H_\n#define UART_H_\n\n#endif\n"
BAD_CASE   = "#ifndef uart_h_\n#define uart_h_\n\n#endif\n"
BAD_NAME   = "#ifndef SOME_OTHER_GUARD\n#define SOME_OTHER_GUARD\n\n#endif\n"
PRAGMA     = "#pragma once\n"
NO_GUARD   = "void uart_Init(void);\n"

class TestIncludeGuardMissing(unittest.TestCase):
    def test_correct_guard_passes(self):
        self.assertFalse(has(GOOD_GUARD, IG_CFG, "include_guard.missing",
                             filepath="uart.h"))

    def test_missing_guard_fails(self):
        self.assertTrue(has(NO_GUARD, IG_CFG, "include_guard.missing",
                            filepath="uart.h"))

    def test_pragma_once_accepted(self):
        self.assertFalse(has(PRAGMA, IG_CFG, "include_guard.missing",
                             filepath="uart.h"))

    def test_c_file_not_checked(self):
        """Include guard check only applies to .h files."""
        self.assertFalse(has(NO_GUARD, IG_CFG, "include_guard.missing",
                             filepath="uart.c"))

class TestIncludeGuardFormat(unittest.TestCase):
    def test_correct_format_passes(self):
        self.assertFalse(has(GOOD_GUARD, IG_CFG, "include_guard.format",
                             filepath="uart.h"))

    def test_wrong_case_fails(self):
        self.assertTrue(has(BAD_CASE, IG_CFG, "include_guard.format",
                            filepath="uart.h"))

    def test_wrong_name_fails(self):
        self.assertTrue(has(BAD_NAME, IG_CFG, "include_guard.format",
                            filepath="uart.h"))

    def test_filename_drives_expected_pattern(self):
        """Expected pattern is derived from the actual filename."""
        guard = "#ifndef MY_MODULE_H_\n#define MY_MODULE_H_\n\n#endif\n"
        self.assertFalse(has(guard, IG_CFG, "include_guard.format",
                             filepath="my_module.h"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
