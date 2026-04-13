"""test_misc.py — tests for misc.line_length, misc.indentation,
misc.magic_number, misc.unsigned_suffix rules."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

LL_CFG = cfg_only(misc={"line_length": {"enabled": True, "severity": "warning", "max": 80}})
IND_CFG = cfg_only(misc={"indentation": {"enabled": True, "severity": "info", "style": "spaces"}})
TAB_CFG = cfg_only(misc={"indentation": {"enabled": True, "severity": "info", "style": "tabs"}})
MN_CFG  = cfg_only(misc={"magic_numbers": {"enabled": True, "severity": "warning",
                                             "exempt_values": [0, 1]}})
US_CFG  = cfg_only(misc={"unsigned_suffix": {"enabled": True, "severity": "info",
                                               "require_on_unsigned_constants": True}})

class TestLineLength(unittest.TestCase):
    def test_short_line_passes(self):
        self.assertTrue(clean("void f(void){}\n", LL_CFG))

    def test_exactly_at_limit_passes(self):
        line = "x" * 80
        self.assertFalse(has(line + "\n", LL_CFG, "misc.line_length"))

    def test_over_limit_fails(self):
        line = "x" * 81
        self.assertTrue(has(line + "\n", LL_CFG, "misc.line_length"))

    def test_comment_line_not_flagged(self):
        line = "/* " + "x" * 100 + " */"
        self.assertFalse(has(line + "\n", LL_CFG, "misc.line_length"))

class TestIndentation(unittest.TestCase):
    def test_spaces_pass_when_spaces_required(self):
        self.assertTrue(clean("    int x = 0;\n", IND_CFG))

    def test_tab_fails_when_spaces_required(self):
        self.assertTrue(has("\tint x = 0;\n", IND_CFG, "misc.indentation"))

    def test_tab_passes_when_tabs_required(self):
        self.assertTrue(clean("\tint x = 0;\n", TAB_CFG))

    def test_spaces_fail_when_tabs_required(self):
        self.assertTrue(has("    int x = 0;\n", TAB_CFG, "misc.indentation"))

    def test_comment_line_not_checked(self):
        self.assertFalse(has("\t/* comment */\n", IND_CFG, "misc.indentation"))

class TestMagicNumbers(unittest.TestCase):
    def test_named_constant_passes(self):
        self.assertTrue(clean("void f(void){ uint32_t x = MAX_SIZE; (void)x; }\n",
                               MN_CFG))

    def test_bare_literal_fails(self):
        self.assertTrue(has("void f(void){ uint32_t x = 42; (void)x; }\n",
                            MN_CFG, "misc.magic_number"))

    def test_exempt_zero_passes(self):
        self.assertFalse(has("void f(void){ uint32_t x = 0; (void)x; }\n",
                              MN_CFG, "misc.magic_number"))

    def test_exempt_one_passes(self):
        self.assertFalse(has("void f(void){ uint32_t x = 1; (void)x; }\n",
                              MN_CFG, "misc.magic_number"))

    def test_define_rhs_exempt(self):
        self.assertFalse(has("#define BUF_SIZE 256\n", MN_CFG, "misc.magic_number"))

    def test_array_index_exempt(self):
        self.assertFalse(has("void f(void){ buf[42] = 0; }\n",
                              MN_CFG, "misc.magic_number"))

    def test_return_value_exempt(self):
        self.assertFalse(has("int f(void){ return 99; }\n",
                              MN_CFG, "misc.magic_number"))

class TestUnsignedSuffix(unittest.TestCase):
    def test_u_suffix_passes(self):
        self.assertTrue(clean("void f(void){ uint32_t x = 42U; (void)x; }\n",
                               US_CFG))

    def test_lowercase_u_passes(self):
        self.assertFalse(has("void f(void){ uint32_t x = 42u; (void)x; }\n",
                              US_CFG, "misc.unsigned_suffix"))

    def test_missing_suffix_fails(self):
        self.assertTrue(has("void f(void){ uint32_t x = 42; (void)x; }\n",
                            US_CFG, "misc.unsigned_suffix"))

    def test_negative_literal_exempt(self):
        """Negative literals don't need U suffix."""
        self.assertFalse(has("void f(void){ int x = -1; (void)x; }\n",
                              US_CFG, "misc.unsigned_suffix"))

    def test_return_zero_exempt(self):
        self.assertFalse(has("int f(void){ return 0; }\n",
                              US_CFG, "misc.unsigned_suffix"))

    def test_define_rhs_exempt(self):
        self.assertFalse(has("#define MAX 100\n", US_CFG, "misc.unsigned_suffix"))

    def test_array_subscript_exempt(self):
        self.assertFalse(has("void f(void){ buf[2] = 0U; }\n",
                              US_CFG, "misc.unsigned_suffix"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
