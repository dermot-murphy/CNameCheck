"""test_misc_improvements.py — tests for four enhancements to CStyleCheck:

  1. misc.unsigned_suffix: zero_is_neutral option — literal 0 exempt from U suffix
  2. misc.unsigned_suffix: signed-variable context — literals assigned to signed-typed
     variables do not need a U suffix
  3. variables.allow_loop_vars_short — short loop-counter variables (<=3 chars,
     appearing in a for-loop initialiser) are exempt from variable.min_length
  4. variables.no_numeric_in_name: unit-suffix exempt patterns — names like
     timer_24hour, delay_100ms, freq_48mhz are not flagged
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count

# ---------------------------------------------------------------------------
# Shared config builders
# ---------------------------------------------------------------------------

def _us_cfg(zero_is_neutral=True, enabled=True):
    """unsigned_suffix-only config."""
    return cfg_only(misc={"unsigned_suffix": {
        "enabled": enabled,
        "severity": "info",
        "require_on_unsigned_constants": True,
        "zero_is_neutral": zero_is_neutral,
    }})


def _var_cfg(min_length=3, allow_loop=False, no_numeric=False,
             exempt_patterns=None):
    """variables-only config with configurable options."""
    return cfg_only(variables={
        "enabled": True, "severity": "warning",
        "case": "lower_snake", "min_length": min_length, "max_length": 40,
        "allow_single_char_loop_vars": False,
        "allow_loop_vars_short": allow_loop,
        "allowed_abbreviations": [],
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
        "pp_prefix":      {"enabled": False},
        "bool_prefix":    {"enabled": False},
        "no_numeric_in_name": {
            "enabled": no_numeric,
            "severity": "warning",
            "exempt_patterns": exempt_patterns or [],
        },
    })


RULE_US  = "misc.unsigned_suffix"
RULE_ML  = "variable.min_length"
RULE_NUM = "variable.no_numeric_in_name"

# Unit-suffix exempt pattern matching timer_24hour, delay_100ms etc.
_UNIT_PATTERNS = [
    r".*_[0-9]+(hour|hours|min|sec|ms|us|ns|hz|khz|mhz|bit|bits|byte|bytes|baud|rpm|deg)$",
]


# ===========================================================================
# Fix 1 — zero_is_neutral
# ===========================================================================

class TestZeroIsNeutral(unittest.TestCase):
    """literal 0 may be used with unsigned types without a U suffix when
    zero_is_neutral is True (default), because 0 is bitwise identical
    for signed and unsigned types."""

    def test_zero_not_flagged_when_neutral_enabled(self):
        src = "void f(void){ uint32_t x = 0; (void)x; }"
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=True), RULE_US))

    def test_zero_flagged_when_neutral_disabled(self):
        src = "void f(void){ uint32_t x = 0; (void)x; }"
        self.assertTrue(has(src, _us_cfg(zero_is_neutral=False), RULE_US))

    def test_nonzero_always_flagged_regardless_of_neutral(self):
        src = "void f(void){ uint32_t x = 42; (void)x; }"
        self.assertTrue(has(src, _us_cfg(zero_is_neutral=True),  RULE_US))
        self.assertTrue(has(src, _us_cfg(zero_is_neutral=False), RULE_US))

    def test_zero_with_u_suffix_passes_always(self):
        src = "void f(void){ uint32_t x = 0U; (void)x; }"
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=False), RULE_US))

    def test_zero_in_array_subscript_always_exempt(self):
        src = "void f(void){ uint32_t x = buf[0]; (void)x; }"
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=False), RULE_US))

    def test_zero_in_return_always_exempt(self):
        src = "int f(void){ return 0; }"
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=False), RULE_US))

    def test_zero_is_neutral_default_is_true(self):
        """Default config should treat 0 as neutral (no flag)."""
        src = "void f(void){ uint32_t x = 0; (void)x; }"
        cfg = cfg_only(misc={"unsigned_suffix": {
            "enabled": True, "severity": "info",
            "require_on_unsigned_constants": True,
            # zero_is_neutral intentionally omitted — should default to True
        }})
        self.assertFalse(has(src, cfg, RULE_US))

    def test_multiple_zeros_all_exempt_when_neutral(self):
        src = ("void f(void){\n"
               "    uint32_t x = 0;\n"
               "    uint8_t  y = 0;\n"
               "    (void)x; (void)y;\n"
               "}")
        self.assertEqual(count(src, _us_cfg(zero_is_neutral=True), RULE_US), 0)

    def test_memset_zero_no_warning_reported_case(self):
        """Regression test for the exact pattern reported as a false positive:
          (void) memset (&app_test_data, 0, sizeof (app_test_data))
        The literal 0 is the 'int c' parameter of memset — it must NOT
        raise misc.unsigned_suffix under any unsigned_suffix configuration.
        This is guaranteed by exempt_function_args (which covers memset by
        default) independently of the zero_is_neutral setting.
        """
        src = (
            "void app_Init(void){\n"
            "    (void) memset (&app_test_data, 0, sizeof (app_test_data));\n"
            "}\n"
        )
        # Must pass with zero_is_neutral=True (default)
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=True),  RULE_US),
                         "memset 0 must not flag with zero_is_neutral=True")
        # Must also pass with zero_is_neutral=False — exempt_function_args covers it
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=False), RULE_US),
                         "memset 0 must not flag with zero_is_neutral=False")


# ===========================================================================
# Fix 2 — signed-variable context (no U suffix required)
# ===========================================================================

class TestSignedVariableContext(unittest.TestCase):
    """Integer literals assigned to signed-type variables do not need U suffix."""

    def test_int_rhs_not_flagged(self):
        src = "void f(void){ int counter = 100; (void)counter; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_uint_rhs_flagged(self):
        src = "void f(void){ uint32_t val = 100; (void)val; }"
        self.assertTrue(has(src, _us_cfg(), RULE_US))

    def test_uint_with_u_suffix_passes(self):
        src = "void f(void){ uint32_t val = 100U; (void)val; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_int8_t_rhs_not_flagged(self):
        src = "void f(void){ int8_t temp = 25; (void)temp; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_int32_t_rhs_not_flagged(self):
        src = "void f(void){ int32_t ticks = 1000; (void)ticks; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_signed_compound_assign_not_flagged(self):
        src = "void f(void){ int counter = 0; counter += 5; (void)counter; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_multiple_signed_vars_none_flagged(self):
        src = ("void f(void){\n"
               "    int   a = 10;\n"
               "    short b = 20;\n"
               "    long  c = 30;\n"
               "    (void)a; (void)b; (void)c;\n"
               "}")
        self.assertEqual(count(src, _us_cfg(), RULE_US), 0)

    def test_mixed_signed_unsigned_only_unsigned_flagged(self):
        src = ("void f(void){\n"
               "    int      a = 10;\n"
               "    uint32_t b = 20;\n"
               "    (void)a; (void)b;\n"
               "}")
        viols = [v for v in run(src, _us_cfg()) if v.rule == RULE_US]
        self.assertEqual(len(viols), 1)
        self.assertIn("20", viols[0].message)

    def test_negative_literal_always_exempt(self):
        src = "void f(void){ int x = -1; (void)x; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_char_type_rhs_not_flagged(self):
        src = "void f(void){ char ch = 65; (void)ch; }"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_define_rhs_always_exempt(self):
        src = "#define MAX_RETRIES 5\n"
        self.assertFalse(has(src, _us_cfg(), RULE_US))

    def test_unsigned_suffix_disabled_no_violations(self):
        src = "void f(void){ uint32_t x = 100; (void)x; }"
        self.assertFalse(has(src, _us_cfg(enabled=False), RULE_US))


# ===========================================================================
# Fix 3 — allow_loop_vars_short
# ===========================================================================

class TestAllowLoopVarsShort(unittest.TestCase):
    """Short variable names (<=3 chars) in for-loop initialisers are exempt
    from variable.min_length when allow_loop_vars_short is enabled."""

    # Pre-declared and used as loop counter
    def test_single_char_loop_var_exempt_when_enabled(self):
        src = "void f(void){ int i = 0; for(i=0;i<10;i++){} (void)i; }"
        self.assertFalse(has(src, _var_cfg(allow_loop=True), RULE_ML))

    def test_single_char_loop_var_flagged_when_disabled(self):
        src = "void f(void){ int i = 0; for(i=0;i<10;i++){} (void)i; }"
        self.assertTrue(has(src, _var_cfg(allow_loop=False), RULE_ML))

    def test_two_char_loop_var_exempt_when_enabled(self):
        src = "void f(void){ int ix = 0; for(ix=0;ix<10;ix++){} (void)ix; }"
        self.assertFalse(has(src, _var_cfg(allow_loop=True), RULE_ML))

    def test_two_char_loop_var_flagged_when_disabled(self):
        src = "void f(void){ int ix = 0; for(ix=0;ix<10;ix++){} (void)ix; }"
        self.assertTrue(has(src, _var_cfg(allow_loop=False), RULE_ML))

    def test_short_var_not_in_loop_still_flagged(self):
        """A short variable that is NOT used in a for-loop is still flagged."""
        src = "void f(void){ int ii = 0; (void)ii; }"
        self.assertTrue(has(src, _var_cfg(allow_loop=True), RULE_ML))

    def test_three_char_loop_var_exempt(self):
        src = "void f(void){ int idx = 0; for(idx=0;idx<10;idx++){} (void)idx; }"
        self.assertFalse(has(src, _var_cfg(allow_loop=True), RULE_ML))

    def test_normal_length_var_never_flagged_for_min_length(self):
        """Variables meeting min_length are never flagged regardless of allow_loop."""
        src = "void f(void){ int counter = 0; (void)counter; }"
        self.assertFalse(has(src, _var_cfg(allow_loop=False), RULE_ML))

    def test_loop_var_typed_with_type_qualifier_detected(self):
        src = "void f(void){ int j = 0; for(int j=0;j<5;j++){} (void)j; }"
        self.assertFalse(has(src, _var_cfg(allow_loop=True), RULE_ML))

    def test_allow_loop_vars_short_default_is_false(self):
        """Test suite YAML (tests/cstylecheck_rules.yaml) has allow_loop_vars_short
        disabled so tests behave predictably regardless of project config."""
        import yaml, pathlib
        # Read from tests/ — the stable test config, not the project src/ YAML
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "cstylecheck_rules.yaml")
            .read_text()
        )
        self.assertFalse(cfg["variables"].get("allow_loop_vars_short", False))


# ===========================================================================
# Fix 4 — no_numeric_in_name unit-suffix exempt patterns
# ===========================================================================

class TestUnitSuffixExemptPatterns(unittest.TestCase):
    """Names with embedded numbers that represent a unit qualifier after an
    underscore (e.g. timer_24hour, delay_100ms) should be exempt when the
    appropriate regex is in exempt_patterns."""

    def _run(self, name, enabled=True):
        src = f"void f(void){{ uint32_t {name} = 0U; (void){name}; }}"
        return has(src, _var_cfg(no_numeric=enabled,
                                  exempt_patterns=_UNIT_PATTERNS), RULE_NUM)

    # --- Names that SHOULD be exempt with unit patterns ---
    def test_timer_24hour_exempt(self):
        self.assertFalse(self._run("timer_24hour"))

    def test_delay_100ms_exempt(self):
        self.assertFalse(self._run("delay_100ms"))

    def test_freq_48mhz_exempt(self):
        self.assertFalse(self._run("freq_48mhz"))

    def test_buf_16bit_exempt(self):
        self.assertFalse(self._run("buf_16bit"))

    def test_timeout_500us_exempt(self):
        self.assertFalse(self._run("timeout_500us"))

    def test_period_60sec_exempt(self):
        self.assertFalse(self._run("period_60sec"))

    def test_rate_9600baud_exempt(self):
        self.assertFalse(self._run("rate_9600baud"))

    def test_angle_90deg_exempt(self):
        self.assertFalse(self._run("angle_90deg"))

    # --- Names that SHOULD still be flagged ---
    def test_buffer32_flagged(self):
        """buffer32 has no unit qualifier — still flagged."""
        self.assertTrue(self._run("buffer32"))

    def test_array8_flagged(self):
        self.assertTrue(self._run("array8"))

    def test_gpio3_flagged(self):
        """gpio3 doesn't end with a unit word — flagged."""
        self.assertTrue(self._run("gpio3"))

    def test_data2_flagged(self):
        self.assertTrue(self._run("data2"))

    # --- Disabled rule produces no violations ---
    def test_disabled_timer_24hour_passes(self):
        self.assertFalse(self._run("timer_24hour", enabled=False))

    # --- Built-in heuristic: digit immediately followed by a letter is treated
    # as a unit qualifier (e.g. 24h in timer_24hour, 100m in delay_100ms).
    # This means timer_24hour is NOT flagged even without any YAML exempt_patterns
    # because the checker detects the "24h" pattern inline.
    def test_timer_24hour_not_flagged_due_to_builtin_heuristic(self):
        """timer_24hour contains '24h' — digit+letter = unit qualifier; not flagged."""
        src = "void f(void){ uint32_t timer_24hour = 0U; (void)timer_24hour; }"
        cfg_no_pattern = _var_cfg(no_numeric=True, exempt_patterns=[])
        self.assertFalse(has(src, cfg_no_pattern, RULE_NUM))

    # --- A name with trailing digits only (no letter after) IS flagged ---
    def test_buffer32_flagged_trailing_digits(self):
        """buffer32 ends with '32' — no letter follows — flagged."""
        src = "void f(void){ uint32_t buffer32 = 0U; (void)buffer32; }"
        self.assertTrue(has(src, _var_cfg(no_numeric=True, exempt_patterns=[]), RULE_NUM))

    # --- Default YAML exempt_patterns include unit suffixes ---
    def test_yaml_contains_unit_patterns(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "cstylecheck_rules.yaml")
            .read_text()
        )
        patterns = cfg["variables"]["no_numeric_in_name"]["exempt_patterns"]
        # At least one pattern should match timer_24hour
        import re
        exempt = any(re.match(p, "timer_24hour") for p in patterns)
        self.assertTrue(exempt, f"no pattern in YAML matches 'timer_24hour': {patterns}")


# ===========================================================================
# Combined interaction tests
# ===========================================================================

class TestCombinedImprovements(unittest.TestCase):
    """Verify the four improvements work correctly together."""

    def test_clean_embedded_code_no_false_positives(self):
        """Typical embedded C code should produce zero violations."""
        src = ("void uart_Init(void)\n"
               "{\n"
               "    int32_t  ret_val    = -1;\n"
               "    uint32_t timeout    = 1000U;\n"
               "    uint32_t baud_rate  = 0U;\n"
               "    int      err_code   = 0;\n"
               "    uint8_t  idx        = 0U;\n"
               "    (void)ret_val; (void)timeout; (void)baud_rate;\n"
               "    (void)err_code; (void)idx;\n"
               "}\n")
        cfg = cfg_only(misc={"unsigned_suffix": {
            "enabled": True, "severity": "info",
            "require_on_unsigned_constants": True,
            "zero_is_neutral": True,
        }})
        viols = [v for v in run(src, cfg) if v.rule == RULE_US]
        self.assertEqual(viols, [],
                         f"False positives: {[v.message for v in viols]}")

    def test_loop_counter_and_unsigned_together(self):
        """Loop counter 'i' exempt from min_length; literals still checked."""
        src = ("void f(void){\n"
               "    int i = 0;\n"
               "    for(i = 0; i < 10; i++){}\n"
               "    uint32_t buf_size = 256U;\n"
               "    (void)i; (void)buf_size;\n"
               "}")
        ml_viols = [v for v in run(src, _var_cfg(allow_loop=True)) if v.rule == RULE_ML]
        self.assertEqual(ml_viols, [])

    def test_signed_zero_assigned_no_violation(self):
        """int x = 0 must not trigger unsigned_suffix."""
        src = "void f(void){ int x = 0; (void)x; }"
        self.assertFalse(has(src, _us_cfg(zero_is_neutral=True), RULE_US))


if __name__ == "__main__":
    unittest.main(verbosity=2)

# ===========================================================================
# Fix 5 — exempt_function_args (no header scanning required)
# ===========================================================================

class TestExemptFunctionArgs(unittest.TestCase):
    """Integer literals inside calls to known signed-parameter functions are
    exempt from misc.unsigned_suffix regardless of zero_is_neutral setting.
    The function list is configurable in cstylecheck_rules.yaml and requires
    no header file scanning."""

    def _us(self, zero_neutral=False, exempt_fns=None):
        cfg = {
            "enabled": True, "severity": "info",
            "require_on_unsigned_constants": True,
            "zero_is_neutral": zero_neutral,
        }
        if exempt_fns is not None:
            cfg["exempt_function_args"] = exempt_fns
        return cfg_only(misc={"unsigned_suffix": cfg})

    # --- Default exempt functions ---
    def test_memset_zero_exempt(self):
        src = "void f(void){ (void)memset(&buf, 0, sizeof(buf)); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_memset_with_spaces_exempt(self):
        """Matches even with spaces between name and paren."""
        src = "void f(void){ (void) memset (&app_test_data, 0, sizeof (app_test_data)); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_memset_fill_byte_exempt(self):
        """0xFF fill byte in memset is also exempt (signed int c parameter)."""
        src = "void f(void){ (void)memset(&buf, 0xFF, sizeof(buf)); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_memchr_zero_exempt(self):
        src = "void f(void){ (void)memchr(ptr, 0, len); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_printf_integer_arg_exempt(self):
        src = 'void f(void){ printf("%d", 42); }'
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_snprintf_integer_arg_exempt(self):
        src = 'void f(void){ char buf[32]; snprintf(buf, 32, "%d", 10); }'
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_fputc_char_value_exempt(self):
        src = "void f(void){ (void)fputc(10, stdout); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    def test_putchar_char_value_exempt(self):
        src = "void f(void){ (void)putchar(65); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    # --- Nested parens handled (sizeof inside memset) ---
    def test_sizeof_nested_in_memset_not_confused(self):
        """sizeof() inside the memset call does not break the span detection."""
        src = "void f(void){ (void)memset(&data, 0, sizeof(data)); }"
        self.assertFalse(has(src, self._us(), RULE_US))

    # --- Non-exempt function still flags ---
    def test_non_exempt_function_still_flags(self):
        src = "void f(void){ custom_write(100); }"
        self.assertTrue(has(src, self._us(), RULE_US))

    def test_uint_direct_assignment_still_flags(self):
        src = "void f(void){ uint32_t x = 100; (void)x; }"
        self.assertTrue(has(src, self._us(), RULE_US))

    # --- Custom function list ---
    def test_custom_function_exempt_when_listed(self):
        src = "void f(void){ my_rtos_delay(100); }"
        self.assertFalse(has(src, self._us(exempt_fns=["my_rtos_delay"]), RULE_US))

    def test_custom_function_not_exempt_without_listing(self):
        src = "void f(void){ my_rtos_delay(100); }"
        # Default list doesn't include my_rtos_delay → flagged
        self.assertTrue(has(src, self._us(), RULE_US))

    def test_empty_list_disables_all_function_exemptions(self):
        """Setting exempt_function_args: [] disables exemption for all functions
        including builtins like memset."""
        src = "void f(void){ (void)memset(&buf, 0, sizeof(buf)); }"
        self.assertTrue(has(src, self._us(exempt_fns=[]), RULE_US))

    # --- Exempt functions independent of zero_is_neutral ---
    def test_memset_exempt_even_when_zero_is_neutral_false(self):
        """Function-arg exemption works independently of zero_is_neutral."""
        src = "void f(void){ (void)memset(&buf, 0, sizeof(buf)); }"
        self.assertFalse(has(src, self._us(zero_neutral=False), RULE_US))

    def test_memset_exempt_with_nonzero_fill_regardless_of_zero_neutral(self):
        src = "void f(void){ (void)memset(&buf, 255, sizeof(buf)); }"
        self.assertFalse(has(src, self._us(zero_neutral=False), RULE_US))

    # --- YAML default list documented ---
    def test_yaml_has_exempt_function_args(self):
        import yaml, pathlib
        cfg = yaml.safe_load(
            (pathlib.Path(__file__).parent / "cstylecheck_rules.yaml")
            .read_text()
        )
        fns = cfg["misc"]["unsigned_suffix"].get("exempt_function_args", [])
        self.assertIn("memset",   fns)
        self.assertIn("printf",   fns)
        self.assertIn("snprintf", fns)
        self.assertIn("memchr",   fns)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ===========================================================================
# Fix: preprocessor conditionals exempt from misc.unsigned_suffix
# ===========================================================================

class TestPreprocessorExempt(unittest.TestCase):
    """Integer constants inside #if / #elif / #ifdef / #ifndef preprocessor
    directives must not raise misc.unsigned_suffix — the C preprocessor
    treats integer tokens as signed by default."""

    _US = cfg_only(misc={"unsigned_suffix": {
        "enabled": True, "severity": "info",
        "require_on_unsigned_constants": True,
        "zero_is_neutral": False,  # strict mode
    }})

    def _vs(self, src):
        return [v for v in run(src, self._US) if v.rule == RULE_US]

    def test_if_numeric_not_flagged(self):
        self.assertEqual(self._vs("#if (HAL_SPI_DEBUG_LEVEL >= 3)\n"), [])

    def test_if_equality_not_flagged(self):
        self.assertEqual(self._vs("#if (VERSION == 2)\n"), [])

    def test_elif_not_flagged(self):
        self.assertEqual(self._vs("#elif (BUILD_TYPE == 1)\n"), [])

    def test_ifdef_not_flagged(self):
        self.assertEqual(self._vs("#ifdef DEBUG\n"), [])

    def test_ifndef_not_flagged(self):
        self.assertEqual(self._vs("#ifndef NDEBUG\n"), [])

    def test_define_still_exempt(self):
        self.assertEqual(self._vs("#define BUF_SIZE 256\n"), [])

    def test_real_code_still_flagged(self):
        src = "void f(void){ uint32_t x = 256; (void)x; }"
        self.assertNotEqual(self._vs(src), [])

    def test_multiline_with_if_and_code(self):
        """Only the code line should flag, not the #if line."""
        src = "#if (LEVEL >= 3)\nuint32_t x = 42;\n#endif\n"
        vs = self._vs(src)
        # The standalone declaration line should flag; the #if line should not
        flagged_values = [v.message for v in vs]
        self.assertTrue(any("42" in m for m in flagged_values))
        self.assertFalse(any("3" in m for m in flagged_values))


# ===========================================================================
# Fix: summary Total line
# ===========================================================================

class TestSummaryTotal(unittest.TestCase):
    """The summary table must include a Total line summing errors+warnings+info."""

    def _summary_output(self, src_text, filename="mod.c"):
        import subprocess, sys, tempfile
        from pathlib import Path as P
        _HERE = P(__file__).parent
        CHECKER = str(_HERE.parent / "src" / "cstylecheck.py")
        YAML    = str(_HERE / "cstylecheck_rules.yaml")
        with tempfile.TemporaryDirectory() as td:
            f = P(td) / filename
            f.write_text(src_text)
            r = subprocess.run(
                [sys.executable, CHECKER, "--config", YAML, "--summary", str(f)],
                capture_output=True, text=True,
            )
            return r.stdout + r.stderr

    def test_total_line_present(self):
        out = self._summary_output("void mod_DoWork(void){}\n")
        self.assertIn("Total", out)

    def test_total_zero_when_clean(self):
        out = self._summary_output("int main(void){ return 0; }\n", "main.c")
        import re
        m = re.search(r"Total\s+:\s+(\d+)", out)
        self.assertIsNotNone(m, "Total line not found")
        self.assertEqual(int(m.group(1)), 0)

    def test_total_matches_sum(self):
        out = self._summary_output("int main(void){ return 0; }\n", "main.c")
        import re
        errors   = int((re.search(r"Errors\s+:\s+(\d+)", out)   or re.search(r"0","0")).group(1) if re.search(r"Errors\s+:\s+(\d+)", out)   else 0)
        warnings = int((re.search(r"Warnings\s+:\s+(\d+)", out) or re.search(r"0","0")).group(1) if re.search(r"Warnings\s+:\s+(\d+)", out) else 0)
        infos    = int((re.search(r"Info\s+:\s+(\d+)", out)      or re.search(r"0","0")).group(1) if re.search(r"Info\s+:\s+(\d+)", out)      else 0)
        total    = int((re.search(r"Total\s+:\s+(\d+)", out)     or re.search(r"0","0")).group(1) if re.search(r"Total\s+:\s+(\d+)", out)     else -1)
        self.assertEqual(total, errors + warnings + infos)


if __name__ == "__main__":
    unittest.main(verbosity=2)
