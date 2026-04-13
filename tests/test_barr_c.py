"""test_barr_c.py — tests for new Barr-C rules added in this release.

Covers four rules from the Embedded C Coding Standard that were not
previously implemented:

  7.1.e  variable.min_length       — no name shorter than 3 chars (configurable)
  7.1.g  variable.no_numeric_in_name — no embedded digit sequences
  7.1.n  variable.handle_prefix     — handle-typed variables must start with h_
  7.1.o  variable.prefix_order      — prefix chain [g_][p_|pp_][b_|h_] ordering
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count

# ---------------------------------------------------------------------------
# Shared config builder: only variables enabled, with the rules under test
# ---------------------------------------------------------------------------

_BASE_VARS = {
    "enabled": True, "severity": "warning",
    "case": "lower_snake", "min_length": 3, "max_length": 40,
    "allow_single_char_loop_vars": False, "allowed_abbreviations": [],
    "global":    {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False,
                  "g_prefix": {"enabled": True, "severity": "warning",
                               "prefix": "g_"}},
    "static":    {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False,
                  "s_prefix": {"enabled": False}},
    "local":     {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False},
    "parameter": {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False},
    "pointer_prefix": {"enabled": True,  "severity": "warning", "prefix": "p_"},
    "pp_prefix":      {"enabled": True,  "severity": "warning", "prefix": "pp_"},
    "bool_prefix":    {"enabled": True,  "severity": "warning", "prefix": "b_"},
    "handle_prefix":  {"enabled": True,  "severity": "warning", "prefix": "h_",
                       "handle_types": ["TaskHandle_t", "QueueHandle_t",
                                        "SemaphoreHandle_t", "FILE",
                                        "osThreadId_t", "osMutexId_t"]},
    "no_numeric_in_name": {"enabled": True, "severity": "warning",
                            "exempt_patterns": [r"^uart[0-9]$",
                                                r"^spi[0-9]$",
                                                r"^i2c[0-9]$"]},
    "prefix_order": {"enabled": True, "severity": "warning"},
}


def _cfg(**overrides):
    import copy
    v = copy.deepcopy(_BASE_VARS)
    v.update(overrides)
    return cfg_only(variables=v)


FULL_CFG = _cfg()   # all four new rules active


# ===========================================================================
# Rule 7.1.e  variable.min_length
# ===========================================================================

class TestMinLength(unittest.TestCase):
    """No variable name may be shorter than the configured minimum (3)."""

    CFG = _cfg()

    def test_three_chars_passes(self):
        self.assertTrue(clean("void f(void){ uint32_t abc = 0U; (void)abc; }",
                               self.CFG))

    def test_two_chars_fails(self):
        self.assertTrue(has("void f(void){ uint32_t ab = 0U; (void)ab; }",
                            self.CFG, "variable.min_length"))

    def test_one_char_fails(self):
        self.assertTrue(has("void f(void){ int i = 0; (void)i; }",
                            self.CFG, "variable.min_length"))

    def test_single_char_exemption_when_configured(self):
        cfg = _cfg(allow_single_char_loop_vars=True)
        self.assertFalse(has("void f(void){ int i = 0; (void)i; }",
                              cfg, "variable.min_length"))

    def test_exactly_three_is_boundary(self):
        """Length == min_length must pass (boundary condition)."""
        self.assertFalse(has("void f(void){ uint32_t buf = 0U; (void)buf; }",
                              self.CFG, "variable.min_length"))

    def test_global_two_chars_fails(self):
        self.assertTrue(has("uint32_t ab = 0U;\n",
                            self.CFG, "variable.min_length"))

    def test_parameter_two_chars_caught_via_re_var_decl(self):
        """Params with a comma after them are caught by RE_VAR_DECL."""
        src = ("void f(\n"
               "    uint32_t ab,\n"
               "    uint32_t cd)\n"
               "{ (void)ab; (void)cd; }\n")
        self.assertTrue(has(src, self.CFG, "variable.min_length"))

    def test_severity_respected(self):
        cfg = _cfg()
        cfg["variables"]["severity"] = "error"
        viols = [v for v in run("void f(void){ uint32_t ab=0U;(void)ab;}",
                                 cfg)
                 if v.rule == "variable.min_length"]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")

    def test_message_cites_barr_c(self):
        viols = [v for v in run("void f(void){ uint32_t ab=0U;(void)ab;}",
                                 self.CFG)
                 if v.rule == "variable.min_length"]
        self.assertTrue(viols)
        self.assertIn("BARR-C", viols[0].message)

    def test_disabled_produces_no_violations(self):
        cfg = _cfg(min_length=1)
        self.assertFalse(has("void f(void){ int i=0; (void)i; }",
                              cfg, "variable.min_length"))


# ===========================================================================
# Rule 7.1.g  variable.no_numeric_in_name
# ===========================================================================

class TestNoNumericInName(unittest.TestCase):
    """Variable names must not contain embedded digit sequences."""

    CFG = _cfg()

    def test_no_digit_passes(self):
        self.assertFalse(has("void f(void){ uint32_t my_buf=0U;(void)my_buf;}",
                              self.CFG, "variable.no_numeric_in_name"))

    def test_trailing_digit_fails(self):
        self.assertTrue(has("void f(void){ uint32_t buffer32=0U;(void)buffer32;}",
                            self.CFG, "variable.no_numeric_in_name"))

    def test_leading_digit_in_segment_fails(self):
        self.assertTrue(has("void f(void){ uint32_t array8=0U;(void)array8;}",
                            self.CFG, "variable.no_numeric_in_name"))

    def test_embedded_digit_fails(self):
        self.assertTrue(has("void f(void){ uint32_t gpio3_val=0U;(void)gpio3_val;}",
                            self.CFG, "variable.no_numeric_in_name"))

    def test_exempt_pattern_passes(self):
        """uart2 matches the exemption pattern ^uart[0-9]$ — not flagged."""
        self.assertFalse(has("void f(void){ uint32_t uart2=0U;(void)uart2;}",
                              self.CFG, "variable.no_numeric_in_name"))

    def test_spi1_exempt(self):
        self.assertFalse(has("void f(void){ uint32_t spi1=0U;(void)spi1;}",
                              self.CFG, "variable.no_numeric_in_name"))

    def test_non_exempt_hardware_fails(self):
        """tim3 is not in the exempt list — flagged."""
        self.assertTrue(has("void f(void){ uint32_t tim3=0U;(void)tim3;}",
                            self.CFG, "variable.no_numeric_in_name"))

    def test_global_with_digit_fails(self):
        self.assertTrue(has("uint32_t buf32 = 0U;\n",
                            self.CFG, "variable.no_numeric_in_name"))

    def test_disabled_passes_any_name(self):
        cfg = _cfg(no_numeric_in_name={"enabled": False})
        self.assertFalse(has("void f(void){ uint32_t buffer32=0U;(void)buffer32;}",
                              cfg, "variable.no_numeric_in_name"))

    def test_message_cites_barr_c(self):
        viols = [v for v in run("void f(void){ uint32_t buf32=0U;(void)buf32;}",
                                 self.CFG)
                 if v.rule == "variable.no_numeric_in_name"]
        self.assertTrue(viols)
        self.assertIn("BARR-C", viols[0].message)


# ===========================================================================
# Rule 7.1.n  variable.handle_prefix
# ===========================================================================

class TestHandlePrefix(unittest.TestCase):
    """Handle-typed variables must begin with h_."""

    CFG = _cfg()

    # ── Single-parameter signatures ─────────────────────────────────────────
    # Note: RE_VAR_DECL requires a comma or brace after the name.
    # Single last-param without comma is caught via _RE_PARAM_TYPED in sigs.
    def test_file_handle_correct(self):
        src = "void f(FILE *h_log){ (void)h_log; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_task_handle_missing_h_prefix_fails(self):
        src = "void f(TaskHandle_t task){ (void)task; }"
        self.assertTrue(has(src, self.CFG, "variable.handle_prefix"))

    def test_task_handle_correct_h_prefix_passes(self):
        src = "void f(TaskHandle_t h_task){ (void)h_task; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_queue_handle_missing_prefix_fails(self):
        src = "void f(QueueHandle_t queue){ (void)queue; }"
        self.assertTrue(has(src, self.CFG, "variable.handle_prefix"))

    def test_queue_handle_correct_prefix_passes(self):
        src = "void f(QueueHandle_t h_queue){ (void)h_queue; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_non_handle_type_not_flagged(self):
        src = "void f(uint32_t count){ (void)count; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_local_handle_var_via_re_var_decl(self):
        """Local handle variable caught via RE_VAR_DECL (has ; after it)."""
        src = "void f(void){ TaskHandle_t task = 0; (void)task; }"
        self.assertTrue(has(src, self.CFG, "variable.handle_prefix"))

    def test_local_handle_var_correct(self):
        src = "void f(void){ TaskHandle_t h_task = 0; (void)h_task; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_os_mutex_handle_flagged(self):
        src = "void f(osMutexId_t mtx){ (void)mtx; }"
        self.assertTrue(has(src, self.CFG, "variable.handle_prefix"))

    def test_os_mutex_handle_correct(self):
        src = "void f(osMutexId_t h_mtx){ (void)h_mtx; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_type_not_in_handle_types_not_flagged(self):
        """A type not listed in handle_types must not trigger the rule."""
        src = "void f(MY_CUSTOM_T val){ (void)val; }"
        self.assertFalse(has(src, self.CFG, "variable.handle_prefix"))

    def test_disabled_no_violations(self):
        cfg = _cfg(handle_prefix={"enabled": False, "handle_types": []})
        src = "void f(TaskHandle_t task){ (void)task; }"
        self.assertFalse(has(src, cfg, "variable.handle_prefix"))

    def test_message_cites_barr_c(self):
        viols = [v for v in run("void f(TaskHandle_t task){ (void)task; }",
                                 self.CFG)
                 if v.rule == "variable.handle_prefix"]
        self.assertTrue(viols)
        self.assertIn("BARR-C", viols[0].message)
        self.assertIn("TaskHandle_t", viols[0].message)


# ===========================================================================
# Rule 7.1.o  variable.prefix_order
# ===========================================================================

class TestPrefixOrder(unittest.TestCase):
    """Prefix chain must follow [g_][p_|pp_][b_|h_] ordering."""

    CFG = _cfg()

    def test_global_bool_correct_order(self):
        """Global bool: g_b_ ordering."""
        src = "bool g_b_done = 0;\n"
        # bool_prefix will fire because RE_VAR_DECL captures it as global
        # and g_b_done strips to 'g_b_done'. The bool_prefix checks local
        # which is 'g_b_done' after stripping — no module prefix to strip.
        # prefix_order checks scope=global, is_bool → expected g_b_
        self.assertFalse(has(src, self.CFG, "variable.prefix_order"))

    def test_global_bool_wrong_order_fails(self):
        """b_g_done: bool prefix before scope prefix is wrong."""
        src = "bool b_g_done = 0;\n"
        self.assertTrue(has(src, self.CFG, "variable.prefix_order"))

    def test_global_pointer_correct(self):
        """Global pointer: g_p_ ordering."""
        src = "uint32_t *g_p_buf = 0;\n"
        self.assertFalse(has(src, self.CFG, "variable.prefix_order"))

    def test_global_pointer_wrong_order_fails(self):
        """p_g_buf: pointer before scope prefix is wrong."""
        src = "uint32_t *p_g_buf = 0;\n"
        self.assertTrue(has(src, self.CFG, "variable.prefix_order"))

    def test_non_global_pointer_no_order_check(self):
        """Local pointer only needs p_ — no g_ expected."""
        src = "void f(void){ uint32_t *p_buf = 0; (void)p_buf; }"
        self.assertFalse(has(src, self.CFG, "variable.prefix_order"))

    def test_disabled_no_violations(self):
        cfg = _cfg(prefix_order={"enabled": False})
        src = "bool b_g_done = 0;\n"
        self.assertFalse(has(src, cfg, "variable.prefix_order"))

    def test_message_cites_barr_c(self):
        viols = [v for v in run("bool b_g_done = 0;\n", self.CFG)
                 if v.rule == "variable.prefix_order"]
        self.assertTrue(viols)
        self.assertIn("BARR-C", viols[0].message)


# ===========================================================================
# Combined interaction tests
# ===========================================================================

class TestBarrCInteractions(unittest.TestCase):
    """Multiple Barr-C rules in one file — each fires independently."""

    def test_clean_file_no_violations(self):
        src = ("void f(\n"
               "    TaskHandle_t h_task,\n"
               "    uint32_t     p_len,\n"
               "    bool         b_done)\n"
               "{\n"
               "    uint32_t my_count = 0U;\n"
               "    (void)h_task; (void)p_len;\n"
               "    (void)b_done; (void)my_count;\n"
               "}\n")
        viols = [v for v in run(src, FULL_CFG)
                 if v.rule in ("variable.min_length",
                               "variable.no_numeric_in_name",
                               "variable.handle_prefix",
                               "variable.prefix_order")]
        self.assertEqual(viols, [], f"Unexpected: {[(v.rule,v.message[:40]) for v in viols]}")

    def test_multiple_barr_c_violations_all_reported(self):
        """Short name AND numeric name in same function — both caught."""
        src = ("void f(void){\n"
               "    uint32_t ab     = 0U;\n"   # too short
               "    uint32_t buf32  = 0U;\n"   # has digit
               "    (void)ab; (void)buf32;\n"
               "}\n")
        r = [v.rule for v in run(src, FULL_CFG)]
        self.assertIn("variable.min_length",       r)
        self.assertIn("variable.no_numeric_in_name", r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
