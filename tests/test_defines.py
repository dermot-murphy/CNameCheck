"""test_defines.py — tests for constant.* and macro.* rules."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count, run

# ---------------------------------------------------------------------------
# Configs
# ---------------------------------------------------------------------------
CONST_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error", "separator": "_",
                 "case": "lower", "exempt_main": True, "exempt_patterns": []},
    constants={"enabled": True, "severity": "error", "case": "upper_snake",
               "max_length": 30, "min_length": 2, "exempt_patterns": []},
    macros={"enabled": False},
)

MACRO_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error", "separator": "_",
                 "case": "lower", "exempt_main": True, "exempt_patterns": []},
    constants={"enabled": False},
    macros={"enabled": True, "severity": "error", "case": "upper_snake",
            "max_length": 30, "exempt_patterns": []},
)

EXEMPT_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error", "separator": "_",
                 "case": "lower", "exempt_main": True, "exempt_patterns": []},
    constants={"enabled": True, "severity": "error", "case": "upper_snake",
               "max_length": 60, "min_length": 2,
               "exempt_patterns": [r"^STACK_SIZE$", r"^__", r"^NULL$"]},
    macros={"enabled": False},
)


# ---------------------------------------------------------------------------
class TestConstantCase(unittest.TestCase):
    def test_upper_snake_passes(self):
        self.assertTrue(clean("#define MODULE_BUFFER_SIZE 64U\n", CONST_CFG,
                               filepath="module.c"))

    def test_lower_snake_fails(self):
        self.assertTrue(has("#define module_bad_name 1U\n", CONST_CFG,
                            "constant.case", filepath="module.c"))

    def test_mixed_case_fails(self):
        self.assertTrue(has("#define Module_Name 1U\n", CONST_CFG,
                            "constant.case", filepath="module.c"))

    def test_single_word_upper_passes(self):
        self.assertTrue(clean("#define MODULE_X 1U\n", CONST_CFG,
                               filepath="module.c"))


class TestConstantPrefix(unittest.TestCase):
    def test_with_module_prefix_passes(self):
        self.assertFalse(has("#define MODULE_MAX_SIZE 64U\n", CONST_CFG,
                              "constant.prefix", filepath="module.c"))

    def test_without_module_prefix_fails(self):
        self.assertTrue(has("#define OTHER_MAX_SIZE 64U\n", CONST_CFG,
                             "constant.prefix", filepath="module.c"))

    def test_include_guard_define_not_checked(self):
        """Bare #define NAME with nothing after it is a guard — not checked."""
        self.assertTrue(clean("#define MODULE_H_\n", CONST_CFG,
                               filepath="module.c"))


class TestConstantMaxLength(unittest.TestCase):
    def test_within_limit_passes(self):
        name = "MODULE_" + "X" * 23   # 30 chars
        self.assertFalse(has(f"#define {name} 1U\n", CONST_CFG,
                              "constant.max_length", filepath="module.c"))

    def test_exceeds_limit_fails(self):
        name = "MODULE_" + "X" * 24   # 31 chars > max 30
        self.assertTrue(has(f"#define {name} 1U\n", CONST_CFG,
                             "constant.max_length", filepath="module.c"))


class TestConstantExemptPatterns(unittest.TestCase):
    def test_stack_size_exempt(self):
        self.assertFalse(has("#define STACK_SIZE 512U\n", EXEMPT_CFG,
                              "constant.case", filepath="mod.c"))

    def test_double_underscore_exempt(self):
        self.assertFalse(has("#define __GUARD_H 1\n", EXEMPT_CFG,
                              "constant.case", filepath="mod.c"))

    def test_non_exempt_still_flagged(self):
        self.assertTrue(has("#define bad_lower 1U\n", EXEMPT_CFG,
                             "constant.case", filepath="mod.c"))


class TestMacroCase(unittest.TestCase):
    def test_function_like_upper_passes(self):
        self.assertFalse(has("#define MODULE_SWAP(a, b) do {} while(0)\n",
                              MACRO_CFG, "macro.case", filepath="module.c"))

    def test_function_like_lower_fails(self):
        self.assertTrue(has("#define module_swap(a, b) do {} while(0)\n",
                             MACRO_CFG, "macro.case", filepath="module.c"))


class TestMacroPrefix(unittest.TestCase):
    def test_function_like_with_prefix_passes(self):
        self.assertFalse(has("#define MODULE_MIN(a, b) ((a)<(b)?(a):(b))\n",
                              MACRO_CFG, "macro.prefix", filepath="module.c"))

    def test_function_like_without_prefix_fails(self):
        self.assertTrue(has("#define OTHER_MIN(a, b) ((a)<(b)?(a):(b))\n",
                             MACRO_CFG, "macro.prefix", filepath="module.c"))


TYPEDEF_CONST_CFG = cfg_only(
    file_prefix={"enabled": True, "severity": "error", "separator": "_",
                 "case": "lower", "exempt_main": True, "exempt_patterns": []},
    constants={"enabled": True, "severity": "error", "case": "upper_snake",
               "max_length": 60, "min_length": 2, "exempt_patterns": []},
    macros={"enabled": True, "severity": "error", "case": "upper_snake",
            "max_length": 60, "exempt_patterns": []},
    typedefs={"enabled": True, "severity": "error", "case": "lower_snake",
              "suffix": {"enabled": True, "suffix": "_t"}},
)

TYPEDEF_CONST_CFG_DISABLED_SUFFIX = cfg_only(
    file_prefix={"enabled": True, "severity": "error", "separator": "_",
                 "case": "lower", "exempt_main": True, "exempt_patterns": []},
    constants={"enabled": True, "severity": "error", "case": "upper_snake",
               "max_length": 60, "min_length": 2, "exempt_patterns": []},
    macros={"enabled": False},
    typedefs={"enabled": True, "severity": "error", "case": "lower_snake",
              "suffix": {"enabled": False, "suffix": "_t"}},
)


class TestTypedefSuffixExemption(unittest.TestCase):
    """Issue #272/#244: #define type aliases ending with _t must not trigger
    constant.case even though they are object-like #defines."""

    def test_typedef_alias_lower_snake_no_constant_case(self):
        """#define api_nvm_error_t uint8_t should NOT trigger constant.case."""
        self.assertFalse(has(
            "#define module_my_type_t uint8_t\n",
            TYPEDEF_CONST_CFG,
            "constant.case",
            filepath="module.c",
        ))

    def test_typedef_alias_mixed_case_no_constant_case(self):
        """Mixed-case typedef alias must NOT trigger constant.case."""
        self.assertFalse(has(
            "#define module_MyType_t uint16_t\n",
            TYPEDEF_CONST_CFG,
            "constant.case",
            filepath="module.c",
        ))

    def test_regular_constant_still_flagged(self):
        """Non-_t constant with wrong case must still be flagged."""
        self.assertTrue(has(
            "#define module_bad_name 1U\n",
            TYPEDEF_CONST_CFG,
            "constant.case",
            filepath="module.c",
        ))

    def test_function_like_macro_still_flagged(self):
        """Function-like macro with wrong case is still flagged even when suffix matches."""
        self.assertTrue(has(
            "#define module_swap_t(a,b) ((a)+(b))\n",
            TYPEDEF_CONST_CFG,
            "macro.case",
            filepath="module.c",
        ))

    def test_typedef_suffix_disabled_alias_flagged(self):
        """When suffix check is disabled, _t-suffixed name IS flagged as constant.case."""
        self.assertTrue(has(
            "#define module_my_type_t uint8_t\n",
            TYPEDEF_CONST_CFG_DISABLED_SUFFIX,
            "constant.case",
            filepath="module.c",
        ))

    def test_typedef_alias_uppercase_t_suffix(self):
        """Suffix matching is case-insensitive: _T suffix also exempted."""
        cfg_upper = cfg_only(
            file_prefix={"enabled": True, "severity": "error", "separator": "_",
                         "case": "lower", "exempt_main": True, "exempt_patterns": []},
            constants={"enabled": True, "severity": "error", "case": "upper_snake",
                       "max_length": 60, "min_length": 2, "exempt_patterns": []},
            macros={"enabled": False},
            typedefs={"enabled": True, "severity": "error", "case": "lower_snake",
                      "suffix": {"enabled": True, "suffix": "_T"}},
        )
        self.assertFalse(has(
            "#define module_my_type_T uint8_t\n",
            cfg_upper,
            "constant.case",
            filepath="module.c",
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
