"""test_variables.py — tests for all variable.* rules."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count, run

# ---------------------------------------------------------------------------
# Config: variables + file_prefix both enabled
# ---------------------------------------------------------------------------
FP = {"enabled": True, "severity": "error", "separator": "_",
      "case": "lower", "exempt_main": True, "exempt_patterns": []}

_VAR_BLOCK = {
    "enabled": True, "severity": "error",
    "case": "lower_snake", "min_length": 2, "max_length": 40,
    "allow_single_char_loop_vars": True, "allowed_abbreviations": [],
    "global":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": True,
                  "g_prefix": {"enabled": True, "severity": "warning", "prefix": "g_"}},
    "static":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": True,
                  "s_prefix": {"enabled": True, "severity": "warning", "prefix": "s_"}},
    "local":     {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": False},
    "parameter": {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False},
    "pointer_prefix": {"enabled": True, "severity": "warning", "prefix": "p_"},
    "pp_prefix":      {"enabled": True, "severity": "warning", "prefix": "pp_"},
    "bool_prefix":    {"enabled": True, "severity": "warning", "prefix": "b_"},
}

VARS_CFG   = cfg_only(file_prefix=FP, variables=_VAR_BLOCK)
VARS_NOFP  = cfg_only(variables={**_VAR_BLOCK,
                                  "global": {**_VAR_BLOCK["global"],
                                             "require_module_prefix": False,
                                             "g_prefix": {"enabled": False}},
                                  "static": {**_VAR_BLOCK["static"],
                                             "require_module_prefix": False,
                                             "s_prefix": {"enabled": False}}})
MOD = "testmod"


class TestGlobalVariables(unittest.TestCase):
    def test_correct_global_passes(self):
        src = f"uint32_t {MOD}_g_counter = 0U;\n"
        self.assertTrue(clean(src, VARS_CFG, filepath=f"{MOD}.c"))

    def test_wrong_module_prefix_fails(self):
        src = "uint32_t other_g_val = 0U;\n"
        self.assertTrue(has(src, VARS_CFG, "variable.global.prefix",
                            filepath=f"{MOD}.c"))

    def test_missing_g_prefix_fails(self):
        src = f"uint32_t {MOD}_counter = 0U;\n"
        self.assertTrue(has(src, VARS_CFG, "variable.global.g_prefix",
                            filepath=f"{MOD}.c"))

    def test_wrong_case_fails(self):
        src = f"uint32_t {MOD}_gCounter = 0U;\n"
        self.assertTrue(has(src, VARS_CFG, "variable.global.case",
                            filepath=f"{MOD}.c"))

    def test_extern_is_skipped(self):
        """extern declarations are references not definitions."""
        src = "extern uint32_t g_system_tick;\n"
        self.assertTrue(clean(src, VARS_CFG, filepath=f"{MOD}.c"))


class TestStaticVariables(unittest.TestCase):
    def test_correct_static_passes(self):
        src = f"static uint32_t {MOD}_s_count = 0U;\n"
        self.assertTrue(clean(src, VARS_CFG, filepath=f"{MOD}.c"))

    def test_wrong_module_prefix_fails(self):
        src = "static uint32_t other_s_count = 0U;\n"
        self.assertTrue(has(src, VARS_CFG, "variable.static.prefix",
                            filepath=f"{MOD}.c"))

    def test_missing_s_prefix_fails(self):
        src = f"static uint32_t {MOD}_count = 0U;\n"
        self.assertTrue(has(src, VARS_CFG, "variable.static.s_prefix",
                            filepath=f"{MOD}.c"))


class TestLocalVariables(unittest.TestCase):
    def test_lower_snake_passes(self):
        src = "void f(void){ uint32_t local_count = 0U; (void)local_count; }"
        self.assertTrue(clean(src, VARS_NOFP, filepath=f"{MOD}.c"))

    def test_camelCase_fails(self):
        src = "void f(void){ uint32_t localCount = 0U; (void)localCount; }"
        self.assertTrue(has(src, VARS_NOFP, "variable.local.case",
                            filepath=f"{MOD}.c"))

    def test_no_module_prefix_required(self):
        src = "void f(void){ uint32_t my_count = 0U; (void)my_count; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.local.prefix",
                             filepath=f"{MOD}.c"))

    def test_single_char_loop_var_allowed(self):
        # i is single char → allowed when allow_single_char_loop_vars is True
        src = "void f(void){ int i = 0; (void)i; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.local.case",
                             filepath=f"{MOD}.c"))


class TestParameterVariables(unittest.TestCase):
    """Parameter case is only caught via RE_VAR_DECL, which requires a
    statement boundary (;, {, \\n) before the type token.  Multiline
    parameter lists with each param on its own line satisfy this."""

    def test_multiline_param_lower_snake_passes(self):
        src = ("void f(\n"
               "    uint32_t p_len,\n"
               "    uint8_t  p_ch)\n"
               "{ (void)p_len; (void)p_ch; }\n")
        self.assertFalse(has(src, VARS_NOFP, "variable.parameter.case",
                             filepath=f"{MOD}.c"))

    def test_multiline_camelCase_param_fails(self):
        """pLen,pCh — only non-last params match RE_VAR_DECL (need comma after)."""
        src = ("void f(\n"
               "    uint32_t pLen,\n"
               "    uint8_t  pCh)\n"
               "{ (void)pLen; (void)pCh; }\n")
        self.assertTrue(has(src, VARS_NOFP, "variable.parameter.case",
                            filepath=f"{MOD}.c"))

    def test_multiline_params_not_classified_as_globals(self):
        """Multiline params at depth 0 must be recognised as parameters."""
        src = ("void f(\n"
               "    uint32_t p_len,\n"
               "    uint8_t  p_ch)\n"
               "{ (void)p_len; (void)p_ch; }\n")
        self.assertFalse(has(src, VARS_CFG, "variable.global.prefix",
                             filepath=f"{MOD}.c"))
        self.assertFalse(has(src, VARS_CFG, "variable.global.g_prefix",
                             filepath=f"{MOD}.c"))


class TestPointerPrefixes(unittest.TestCase):
    def test_single_pointer_correct_passes(self):
        src = "void f(uint8_t *p_buf){ (void)p_buf; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.pointer_prefix",
                             filepath=f"{MOD}.c"))

    def test_single_pointer_missing_p_fails(self):
        src = "void f(uint8_t *wrong_buf){ (void)wrong_buf; }"
        self.assertTrue(has(src, VARS_NOFP, "variable.pointer_prefix",
                            filepath=f"{MOD}.c"))

    def test_double_pointer_correct_passes(self):
        src = "void f(uint8_t **pp_tbl){ (void)pp_tbl; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.pp_prefix",
                             filepath=f"{MOD}.c"))

    def test_double_pointer_with_p_not_pp_fails(self):
        src = "void f(uint8_t **p_tbl){ (void)p_tbl; }"
        self.assertTrue(has(src, VARS_NOFP, "variable.pp_prefix",
                            filepath=f"{MOD}.c"))

    def test_double_pointer_does_not_trigger_single_pointer_rule(self):
        src = "void f(uint8_t **pp_tbl){ (void)pp_tbl; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.pointer_prefix",
                             filepath=f"{MOD}.c"))

    def test_non_pointer_not_flagged(self):
        src = "void f(void){ uint32_t count = 0U; (void)count; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.pointer_prefix",
                             filepath=f"{MOD}.c"))
        self.assertFalse(has(src, VARS_NOFP, "variable.pp_prefix",
                             filepath=f"{MOD}.c"))


class TestBoolPrefix(unittest.TestCase):
    def test_local_bool_with_b_prefix_passes(self):
        src = "void f(void){ bool b_done = false; (void)b_done; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.bool_prefix",
                             filepath=f"{MOD}.c"))

    def test_local_bool_missing_b_fails(self):
        src = "void f(void){ bool flag = false; (void)flag; }"
        self.assertTrue(has(src, VARS_NOFP, "variable.bool_prefix",
                            filepath=f"{MOD}.c"))

    def test_non_bool_uint32_not_flagged(self):
        src = "void f(void){ uint32_t count = 0U; (void)count; }"
        self.assertFalse(has(src, VARS_NOFP, "variable.bool_prefix",
                             filepath=f"{MOD}.c"))

    def test_bool_Bool_type_flagged(self):
        """_Bool type also triggers the rule."""
        src = "void f(void){ _Bool active = 0; (void)active; }"
        self.assertTrue(has(src, VARS_NOFP, "variable.bool_prefix",
                            filepath=f"{MOD}.c"))


class TestVariableMaxLength(unittest.TestCase):
    def test_at_limit_passes(self):
        name = "a" * 40
        src = f"void f(void){{ uint32_t {name} = 0U; (void){name}; }}"
        self.assertFalse(has(src, VARS_NOFP, "variable.max_length",
                             filepath=f"{MOD}.c"))

    def test_over_limit_fails(self):
        name = "a" * 41
        src = f"void f(void){{ uint32_t {name} = 0U; (void){name}; }}"
        self.assertTrue(has(src, VARS_NOFP, "variable.max_length",
                            filepath=f"{MOD}.c"))


class TestVariableMinLength(unittest.TestCase):
    """Barr-C 7.1.e: no variable name shorter than 3 characters."""

    _CFG = cfg_only(variables={
        "enabled": True, "severity": "warning",
        "case": "lower_snake", "min_length": 3, "max_length": 40,
        "allow_single_char_loop_vars": False, "allowed_abbreviations": [],
        "global":    {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False,
                      "g_prefix": {"enabled": False}},
        "static":    {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False,
                      "s_prefix": {"enabled": False}},
        "local":     {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False},
        "parameter": {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False},
        "pointer_prefix": {"enabled": False},
        "pp_prefix":  {"enabled": False},
        "bool_prefix":{"enabled": False},
    })

    def test_three_char_name_passes(self):
        src = "void f(void){ uint32_t abc = 0U; (void)abc; }"
        self.assertFalse(has(src, self._CFG, "variable.min_length",
                             filepath="mod.c"))

    def test_two_char_name_fails(self):
        src = "void f(void){ uint32_t ab = 0U; (void)ab; }"
        self.assertTrue(has(src, self._CFG, "variable.min_length",
                            filepath="mod.c"))

    def test_one_char_name_fails(self):
        """Single-char loop var flagged when allow_single_char_loop_vars is False."""
        src = "void f(void){ int i = 0; (void)i; }"
        self.assertTrue(has(src, self._CFG, "variable.min_length",
                            filepath="mod.c"))

    def test_allow_single_char_loop_var(self):
        """When allow_single_char_loop_vars is True, single-char names pass."""
        cfg = cfg_only(variables={**self._CFG["variables"],
                                   "allow_single_char_loop_vars": True})
        src = "void f(void){ int i = 0; (void)i; }"
        self.assertFalse(has(src, cfg, "variable.min_length", filepath="mod.c"))

    def test_message_mentions_barr_c(self):
        src = "void f(void){ uint32_t ab = 0U; (void)ab; }"
        viols = run(src, self._CFG, filepath="mod.c")
        ml = [v for v in viols if v.rule == "variable.min_length"]
        self.assertTrue(ml)
        self.assertIn("BARR-C", ml[0].message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
