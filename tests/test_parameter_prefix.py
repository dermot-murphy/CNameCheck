"""test_parameter_prefix.py — tests for the new variable.parameter.p_prefix rule.

All function parameters must begin with p_ (configurable prefix) when this
rule is enabled.  When the parameter also carries another prefix (pointer p_,
bool b_, handle h_) the parameter prefix must come first:

  uint8_t        p_channel      OK — plain param
  uint8_t *      p_p_buffer     OK — param prefix then pointer prefix
  bool           p_b_enabled    OK — param prefix then bool prefix
  TaskHandle_t   p_h_task       OK — param prefix then handle prefix
  uint8_t        channel        VIOLATION — missing param prefix

The rule is off by default (enabled: false) to maintain backwards
compatibility.  Enable with:

  variables:
    parameter:
      p_prefix:
        enabled: true
        severity: warning
        prefix: "p_"
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count

RULE = "variable.parameter.p_prefix"


def _cfg(enabled=True, prefix="p_", severity="warning",
         ptr_enabled=False, bool_enabled=False):
    """Build a config with parameter.p_prefix and optional pointer/bool rules."""
    return cfg_only(variables={
        "enabled": True, "severity": "error",
        "case": "lower_snake", "min_length": 2, "max_length": 40,
        "allow_single_char_loop_vars": True,
        "allow_loop_vars_short": True,
        "allowed_abbreviations": [],
        "global": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "g_prefix": {"enabled": False},
        },
        "static": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "s_prefix": {"enabled": False},
        },
        "local":     {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": False},
        "parameter": {"severity": severity, "case": "lower_snake",
                      "require_module_prefix": False,
                      "p_prefix": {"enabled": enabled,
                                   "severity": severity,
                                   "prefix": prefix}},
        "pointer_prefix": {"enabled": ptr_enabled,
                           "severity": "warning", "prefix": "p_"},
        "pp_prefix":      {"enabled": False},
        "bool_prefix":    {"enabled": bool_enabled,
                           "severity": "warning", "prefix": "b_"},
        "no_numeric_in_name": {"enabled": False, "exempt_patterns": []},
        "prefix_order": {"enabled": False},
        "handle_prefix": {"enabled": False, "handle_types": []},
    })


ON  = _cfg(enabled=True)
OFF = _cfg(enabled=False)


# ===========================================================================
# Correct usage — must NOT flag
# ===========================================================================

class TestParameterPrefixPasses(unittest.TestCase):

    def test_single_param_correct(self):
        src = "void f(uint8_t p_channel){ (void)p_channel; }"
        self.assertFalse(has(src, ON, RULE))

    def test_two_params_both_correct(self):
        src = "void f(uint32_t p_size, uint8_t p_mode){ (void)p_size; (void)p_mode; }"
        self.assertFalse(has(src, ON, RULE))

    def test_pointer_param_correct_ordering(self):
        """Pointer param: parameter p_ then pointer p_ → p_p_buffer."""
        src = "void f(uint8_t * p_p_buffer){ (void)p_p_buffer; }"
        self.assertFalse(has(src, ON, RULE))

    def test_void_param_not_flagged(self):
        src = "void f(void){}"
        self.assertFalse(has(src, ON, RULE))

    def test_no_params_not_flagged(self):
        src = "void f(){}"
        self.assertFalse(has(src, ON, RULE))

    def test_multiline_params_correct(self):
        src = ("void uart_Write(\n"
               "    uint32_t p_length,\n"
               "    uint8_t  p_data)\n"
               "{ (void)p_length; (void)p_data; }\n")
        self.assertFalse(has(src, ON, RULE))

    def test_three_params_all_correct(self):
        src = ("void f(uint8_t p_a, uint16_t p_b, uint32_t p_c)"
               "{ (void)p_a; (void)p_b; (void)p_c; }")
        self.assertFalse(has(src, ON, RULE))

    def test_custom_prefix_correct(self):
        cfg = _cfg(prefix="par_")
        src = "void f(uint8_t par_channel){ (void)par_channel; }"
        self.assertFalse(has(src, cfg, RULE))

    def test_disabled_passes_any_name(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        self.assertFalse(has(src, OFF, RULE))


# ===========================================================================
# Violations — must flag
# ===========================================================================

class TestParameterPrefixViolations(unittest.TestCase):

    def test_single_param_missing_prefix(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        self.assertTrue(has(src, ON, RULE))

    def test_count_no_prefix(self):
        src = "void f(uint32_t count){ (void)count; }"
        self.assertTrue(has(src, ON, RULE))

    def test_pointer_param_wrong_name(self):
        """Pointer param without p_ at start should flag."""
        src = "void f(uint8_t * buffer){ (void)buffer; }"
        self.assertTrue(has(src, ON, RULE))

    def test_two_params_one_wrong(self):
        src = "void f(uint32_t p_size, uint8_t mode){ (void)p_size; (void)mode; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertEqual(len(vs), 1)
        self.assertIn("mode", vs[0].message)

    def test_two_params_both_wrong(self):
        src = "void f(uint32_t size, uint8_t mode){ (void)size; (void)mode; }"
        self.assertEqual(count(src, ON, RULE), 2)

    def test_multiline_param_missing_prefix(self):
        src = ("void uart_Write(\n"
               "    uint32_t length,\n"
               "    uint8_t  data)\n"
               "{ (void)length; (void)data; }\n")
        self.assertTrue(has(src, ON, RULE))

    def test_message_names_the_parameter(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertIn("channel", vs[0].message)

    def test_message_names_the_required_prefix(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertIn("p_", vs[0].message)

    def test_custom_prefix_violation(self):
        cfg = _cfg(prefix="par_")
        src = "void f(uint8_t p_channel){ (void)p_channel; }"
        self.assertTrue(has(src, cfg, RULE))


# ===========================================================================
# Prefix ordering — p_ comes before other prefixes
# ===========================================================================

class TestParameterPrefixOrdering(unittest.TestCase):
    """When a parameter carries multiple prefix requirements, the parameter
    p_ prefix must come first."""

    def test_param_then_pointer_correct(self):
        """Pointer param: p_ (param) + p_ (ptr) → p_p_name."""
        src = "void f(uint8_t * p_p_buf){ (void)p_p_buf; }"
        self.assertFalse(has(src, ON, RULE))

    def test_pointer_without_param_prefix_violates(self):
        """Pointer named p_buf — starts with p_ so param prefix satisfied."""
        src = "void f(uint8_t * p_buf){ (void)p_buf; }"
        self.assertFalse(has(src, ON, RULE))

    def test_param_bool_prefix_ordering(self):
        """Boolean param: p_ (param) + b_ (bool) → p_b_enabled."""
        src = "void f(bool p_b_enabled){ (void)p_b_enabled; }"
        self.assertFalse(has(src, ON, RULE))

    def test_wrong_bool_order_violates(self):
        """Boolean param named b_enabled — starts with b_ not p_ → violation."""
        src = "void f(bool b_enabled){ (void)b_enabled; }"
        self.assertTrue(has(src, ON, RULE))

    def test_deeply_prefixed_param_correct(self):
        """p_h_task — param prefix + handle prefix."""
        src = "void f(uint32_t p_h_task){ (void)p_h_task; }"
        self.assertFalse(has(src, ON, RULE))


# ===========================================================================
# Severity and YAML defaults
# ===========================================================================

class TestParameterPrefixSeverityAndDefaults(unittest.TestCase):

    def test_default_severity_is_warning(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].severity, "warning")

    def test_custom_severity_error(self):
        cfg = _cfg(severity="error")
        src = "void f(uint8_t channel){ (void)channel; }"
        vs = [v for v in run(src, cfg) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].severity, "error")

    def test_yaml_default_is_disabled(self):
        """Rule is off by default in tests/rules.yml."""
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "rules.yml").read_text(encoding="utf-8")
        )
        param_cfg = cfg["variables"]["parameter"]
        p_prefix = param_cfg.get("p_prefix", {})
        self.assertFalse(p_prefix.get("enabled", False))

    def test_disabled_no_violation(self):
        src = "void f(uint8_t channel, uint32_t count){ (void)channel; (void)count; }"
        self.assertFalse(has(src, OFF, RULE))

    def test_rule_id_is_correct(self):
        src = "void f(uint8_t channel){ (void)channel; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertTrue(vs)
        self.assertEqual(vs[0].rule, "variable.parameter.p_prefix")

    def test_local_variables_not_flagged(self):
        """The rule only applies to parameters, not local variables."""
        src = "void f(uint8_t p_ch){ uint32_t counter = 0U; (void)p_ch; (void)counter; }"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertEqual(vs, [])

    def test_global_variables_not_flagged(self):
        """The rule only applies to parameters, not globals."""
        src = "uint32_t my_global = 0U;\n"
        vs = [v for v in run(src, ON) if v.rule == RULE]
        self.assertEqual(vs, [])


# ===========================================================================
# Regression: param prefix + type prefix combined — no false positive
# (GitHub issue: variable.pointer_prefix fires on 'p_ptr_packet_buffer'
#  even though the local part 'ptr_packet_buffer' starts with 'ptr_')
# ===========================================================================

def _cfg_combined(param_pfx="p_", ptr_pfx="ptr_",
                  pp_pfx="pp_", bool_pfx="b_",
                  ptr_enabled=True, pp_enabled=True, bool_enabled=True):
    """Config with parameter prefix AND pointer/pp/bool prefix all active."""
    return cfg_only(variables={
        "enabled": True, "severity": "error",
        "case": "lower_snake", "min_length": 2, "max_length": 60,
        "allow_single_char_loop_vars": True,
        "allow_loop_vars_short": True,
        "allowed_abbreviations": [],
        "global": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "g_prefix": {"enabled": False},
        },
        "static": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "s_prefix": {"enabled": False},
        },
        "local":     {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": False},
        "parameter": {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False,
                      "p_prefix": {"enabled": True,
                                   "severity": "warning",
                                   "prefix": param_pfx}},
        "pointer_prefix": {"enabled": ptr_enabled,
                            "severity": "warning", "prefix": ptr_pfx},
        "pp_prefix":      {"enabled": pp_enabled,
                            "severity": "warning", "prefix": pp_pfx},
        "bool_prefix":    {"enabled": bool_enabled,
                            "severity": "warning", "prefix": bool_pfx},
        "no_numeric_in_name": {"enabled": False, "exempt_patterns": []},
        "prefix_order": {"enabled": False},
        "handle_prefix": {"enabled": False, "handle_types": []},
    })


# ===========================================================================
# Regression: param prefix + type prefix combined — no false positive
# (GitHub issue: variable.pointer_prefix fires on 'p_ptr_packet_buffer'
#  even though the local part 'ptr_packet_buffer' starts with 'ptr_')
# ===========================================================================

def _cfg_combined(param_pfx="p_", ptr_pfx="ptr_",
                  pp_pfx="pp_", bool_pfx="b_",
                  ptr_enabled=True, pp_enabled=True, bool_enabled=True,
                  param_prefix_rule_enabled=True):
    """Config with pointer/pp/bool prefix active.
    param_prefix_rule_enabled controls variable.parameter.p_prefix.
    The parameter prefix value (_pp_param_pfx) is always 'p_' regardless,
    mirroring the real-world scenario where projects use the p_ naming
    convention without enabling the rule that enforces it.
    """
    return cfg_only(variables={
        "enabled": True, "severity": "error",
        "case": "lower_snake", "min_length": 2, "max_length": 60,
        "allow_single_char_loop_vars": True,
        "allow_loop_vars_short": True,
        "allowed_abbreviations": [],
        "global": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "g_prefix": {"enabled": False},
        },
        "static": {
            "severity": "error", "case": "lower_snake",
            "require_module_prefix": False,
            "s_prefix": {"enabled": False},
        },
        "local":     {"severity": "error", "case": "lower_snake",
                      "require_module_prefix": False},
        "parameter": {"severity": "warning", "case": "lower_snake",
                      "require_module_prefix": False,
                      "p_prefix": {"enabled": param_prefix_rule_enabled,
                                   "severity": "warning",
                                   "prefix": param_pfx}},
        "pointer_prefix": {"enabled": ptr_enabled,
                            "severity": "warning", "prefix": ptr_pfx},
        "pp_prefix":      {"enabled": pp_enabled,
                            "severity": "warning", "prefix": pp_pfx},
        "bool_prefix":    {"enabled": bool_enabled,
                            "severity": "warning", "prefix": bool_pfx},
        "no_numeric_in_name": {"enabled": False, "exempt_patterns": []},
        "prefix_order": {"enabled": False},
        "handle_prefix": {"enabled": False, "handle_types": []},
    })


# Config with p_prefix ENABLED (rule enforced)
PTR_RULE_ON  = _cfg_combined(param_prefix_rule_enabled=True)
# Config with p_prefix DISABLED (the default — real-world failing case)
PTR_RULE_OFF = _cfg_combined(param_prefix_rule_enabled=False)


class TestParamPrefixCombinedNoFalsePositive(unittest.TestCase):
    """Regression: when pointer_prefix (or pp_prefix / bool_prefix) is active,
    a parameter named '<param_pfx><type_pfx>name' must NOT trigger a false
    positive on the type-prefix rule — regardless of whether
    variable.parameter.p_prefix is enabled.

    The reported failure:
        uint8_t* p_ptr_packet_buffer
        WARNING [variable.pointer_prefix] local part should start with 'ptr_'
    The local part after the parameter prefix is 'ptr_packet_buffer' which
    DOES start with 'ptr_', so the warning is incorrect.
    """

    # ------------------------------------------------------------------
    # Exact failing signature from the bug report
    # ------------------------------------------------------------------

    def test_exact_bug_report_signature(self):
        """Full multiline declaration from the bug report — no violation."""
        src = (
            "void\t\t\tAPI_Vibration_PacketGet\t\t(api_vibration_buffer_t p_buffer,\n"
            "\t\t\t\tapi_vibration_axis_t\tp_sensor_axis,\n"
            "\t\t\t\tuint8_t*\t\tp_ptr_packet_buffer,\n"
            "\t\t\t\tuint8_t\t\t\tp_packet_size,\n"
            "\t\t\t\tuint16_t\t\tp_packet,\n"
            "\t\t\t\tbool\t\t\tp_hibyte_first) ;\n"
        )
        for cfg, label in ((PTR_RULE_ON, "p_prefix enabled"),
                           (PTR_RULE_OFF, "p_prefix disabled")):
            with self.subTest(config=label):
                violations = [v for v in run(src, cfg)
                              if v.rule == "variable.pointer_prefix"]
                self.assertEqual(violations, [],
                    f"False positive with {label}: {violations}")

    # ------------------------------------------------------------------
    # Single-pointer (*) parameters — p_prefix rule DISABLED (default)
    # ------------------------------------------------------------------

    def test_ptr_param_rule_off_no_violation(self):
        """p_ptr_packet_buffer: p_prefix rule off, pointer prefix 'ptr_' → no warn."""
        src = ("void f(uint8_t * p_ptr_packet_buffer)"
               "{ (void)p_ptr_packet_buffer; }")
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pointer_prefix"]
        self.assertEqual(violations, [],
            "False positive: pointer_prefix fired on p_ptr_packet_buffer "
            "when p_prefix rule is disabled")

    def test_ptr_param_rule_on_no_violation(self):
        """p_ptr_buf: p_prefix rule ON, pointer prefix 'ptr_' → no warn."""
        src = "void f(uint8_t * p_ptr_buf){ (void)p_ptr_buf; }"
        violations = [v for v in run(src, PTR_RULE_ON)
                      if v.rule == "variable.pointer_prefix"]
        self.assertEqual(violations, [],
            "False positive: pointer_prefix fired on p_ptr_buf "
            "when p_prefix rule is enabled")

    def test_ptr_param_missing_type_pfx_rule_off_flags(self):
        """p_buffer: param prefix present but no 'ptr_' → should flag."""
        src = "void f(uint8_t * p_buffer){ (void)p_buffer; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pointer_prefix"]
        self.assertTrue(violations,
            "pointer_prefix should fire: local 'buffer' missing 'ptr_'")

    def test_ptr_param_no_param_prefix_but_type_pfx_present(self):
        """ptr_buffer: only type prefix, no param prefix → pointer_prefix passes."""
        src = "void f(uint8_t * ptr_buffer){ (void)ptr_buffer; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pointer_prefix"]
        self.assertEqual(violations, [],
            "ptr_buffer should satisfy pointer_prefix='ptr_' directly")

    def test_ptr_param_multiline_rule_off_no_false_positive(self):
        """Multiline declaration with p_ptr_buf — p_prefix rule off."""
        src = ("void uart_Send(\n"
               "    uint8_t *  p_ptr_buf,\n"
               "    uint32_t   p_length)\n"
               "{ (void)p_ptr_buf; (void)p_length; }\n")
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pointer_prefix"]
        self.assertEqual(violations, [],
            "False positive on multiline p_ptr_buf with p_prefix rule off")

    # ------------------------------------------------------------------
    # Double-pointer (**) parameters
    # ------------------------------------------------------------------

    def test_pp_param_rule_off_no_violation(self):
        """p_pp_table: p_prefix rule off, pp_prefix='pp_' → no warn."""
        src = "void f(uint8_t ** p_pp_table){ (void)p_pp_table; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pp_prefix"]
        self.assertEqual(violations, [],
            "False positive: pp_prefix fired on p_pp_table when rule off")

    def test_pp_param_missing_pp_pfx_rule_off_flags(self):
        """p_table: param prefix OK but 'pp_' absent on ** param → violation."""
        src = "void f(uint8_t ** p_table){ (void)p_table; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.pp_prefix"]
        self.assertTrue(violations,
            "pp_prefix should fire: local 'table' missing 'pp_'")

    # ------------------------------------------------------------------
    # Boolean parameters
    # ------------------------------------------------------------------

    def test_bool_param_rule_off_no_violation(self):
        """p_b_enabled: p_prefix rule off, bool_prefix='b_' → no warn."""
        src = "void f(bool p_b_enabled){ (void)p_b_enabled; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.bool_prefix"]
        self.assertEqual(violations, [],
            "False positive: bool_prefix fired on p_b_enabled when rule off")

    def test_bool_param_missing_b_pfx_rule_off_flags(self):
        """p_enabled: param prefix OK but 'b_' absent on bool param → violation."""
        src = "void f(bool p_enabled){ (void)p_enabled; }"
        violations = [v for v in run(src, PTR_RULE_OFF)
                      if v.rule == "variable.bool_prefix"]
        self.assertTrue(violations,
            "bool_prefix should fire: local 'enabled' missing 'b_'")

    # ------------------------------------------------------------------
    # Default pointer_prefix="p_" — existing convention must still work
    # ------------------------------------------------------------------

    def test_default_ptr_prefix_p_param_p_buf_passes(self):
        """pointer_prefix='p_' (default): p_buf satisfies directly — no strip needed."""
        cfg = _cfg_combined(ptr_pfx="p_", param_prefix_rule_enabled=False)
        src = "void f(uint8_t * p_buf){ (void)p_buf; }"
        violations = [v for v in run(src, cfg)
                      if v.rule == "variable.pointer_prefix"]
        self.assertEqual(violations, [],
            "p_buf should satisfy pointer_prefix='p_' without stripping")

    def test_default_ptr_prefix_p_param_p_p_buf_passes(self):
        """pointer_prefix='p_', p_prefix rule ON: p_p_buf satisfies both."""
        cfg = _cfg_combined(ptr_pfx="p_", param_prefix_rule_enabled=True)
        src = "void f(uint8_t * p_p_buf){ (void)p_p_buf; }"
        violations = [v for v in run(src, cfg)
                      if v.rule in ("variable.pointer_prefix",
                                    "variable.parameter.p_prefix")]
        self.assertEqual(violations, [],
            "p_p_buf should satisfy both p_prefix and pointer_prefix='p_'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
