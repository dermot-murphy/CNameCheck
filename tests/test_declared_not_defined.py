"""
tests/test_declared_not_defined.py
===================================
Tests for the misc.declared_not_defined cross-file rule (issue #114).

The rule detects C objects that are declared (via 'extern' or a forward
typedef) but for which no matching definition is found across all files
in a single checker invocation.

Key behaviours tested:
  - Disabled by default (opt-in)
  - Single-file run → no violations
  - extern function: satisfied vs unsatisfied
  - extern variable: satisfied vs unsatisfied
  - forward typedef struct/enum: satisfied vs unsatisfied
  - inline suppression comment
  - no false positive for static functions
  - custom severity
"""

import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import DeclaredNotDefinedChecker


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _cfg(enabled=True, severity="warning"):
    return {"misc": {"declared_not_defined": {"enabled": enabled,
                                               "severity": severity}}}


def _check(files, enabled=True, severity="warning"):
    """Ingest all (filepath, source) pairs and return violation list."""
    dndc = DeclaredNotDefinedChecker(_cfg(enabled=enabled, severity=severity))
    for fp, src in files:
        dndc.ingest(fp, src)
    return dndc.check()


def _rules(files, **kw):
    return [v.rule for v in _check(files, **kw)]


def _msgs(files, **kw):
    return [v.message for v in _check(files, **kw)]


# ---------------------------------------------------------------------------
# 1. Basic enable/disable and single-file guard
# ---------------------------------------------------------------------------

class TestDndBasic(unittest.TestCase):

    def test_disabled_no_violations(self):
        """Rule disabled → no violations even if declarations are unsatisfied."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        self.assertEqual(_check(files, enabled=False), [])

    def test_single_file_no_violations(self):
        """Single-file run → no violations (definition may be in unscanned TU)."""
        files = [("uart.h", "extern void UART_Init(void);\n")]
        self.assertEqual(_check(files), [])

    def test_two_files_triggers_check(self):
        """Two-file run with unsatisfied extern → one violation."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))


# ---------------------------------------------------------------------------
# 2. Extern function declarations
# ---------------------------------------------------------------------------

class TestDndExternFunction(unittest.TestCase):

    def test_extern_func_satisfied(self):
        """extern function declaration satisfied by definition → no violation."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "void UART_Init(void) { return; }\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_extern_func_unsatisfied(self):
        """extern function declaration with no definition → violation."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "void other_func(void) { return; }\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))

    def test_extern_func_message_contains_name(self):
        """Violation message names the undeclared symbol."""
        files = [
            ("uart.h", "extern int UART_ReadByte(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        msgs = _msgs(files)
        self.assertTrue(any("UART_ReadByte" in m for m in msgs))

    def test_extern_func_satisfied_in_third_file(self):
        """Definition in any scanned file satisfies the declaration."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("main.c", "int g_dummy = 0;\n"),
            ("uart.c", "void UART_Init(void) { return; }\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_non_extern_func_no_violation(self):
        """Bare prototype without 'extern' is not flagged by this rule."""
        files = [
            ("uart.h", "void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        # Bare prototype without extern → rule does not track it
        self.assertEqual(_check(files), [])

    def test_static_func_no_violation(self):
        """static function definition does not generate an extern declaration."""
        files = [
            ("uart.c", "static void helper(void) { return; }\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_each_name_reported_once(self):
        """Same declaration in two headers → violation reported only once."""
        files = [
            ("a.h", "extern void UART_Init(void);\n"),
            ("b.h", "extern void UART_Init(void);\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        count = sum(1 for r in _rules(files) if r == "misc.declared_not_defined")
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# 3. Extern variable declarations
# ---------------------------------------------------------------------------

class TestDndExternVariable(unittest.TestCase):

    def test_extern_var_satisfied(self):
        """extern variable satisfied by file-scope definition → no violation."""
        files = [
            ("uart.h", "extern int g_uart_baud_rate;\n"),
            ("uart.c", "int g_uart_baud_rate = 9600;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_extern_var_unsatisfied(self):
        """extern variable with no file-scope definition → violation."""
        files = [
            ("uart.h", "extern int g_uart_baud_rate;\n"),
            ("uart.c", "int g_other = 0;\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))

    def test_extern_const_var_satisfied(self):
        """extern const variable satisfied by const definition → no violation."""
        files = [
            ("config.h", "extern const int BAUD_RATE;\n"),
            ("config.c", "const int BAUD_RATE = 9600;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_extern_const_var_unsatisfied(self):
        """extern const variable with no definition → violation."""
        files = [
            ("config.h", "extern const int BAUD_RATE;\n"),
            ("config.c", "int g_dummy = 0;\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))

    def test_extern_var_message_contains_name(self):
        """Violation message names the undeclared variable."""
        files = [
            ("config.h", "extern int g_timeout;\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        msgs = _msgs(files)
        self.assertTrue(any("g_timeout" in m for m in msgs))


# ---------------------------------------------------------------------------
# 4. Forward typedef struct / enum
# ---------------------------------------------------------------------------

class TestDndForwardTypedef(unittest.TestCase):

    def test_fwd_struct_satisfied(self):
        """Forward typedef struct satisfied by full definition → no violation."""
        files = [
            ("uart.h", "typedef struct Uart Uart;\n"),
            ("uart.c", "typedef struct Uart { int baud; } Uart;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_fwd_struct_unsatisfied(self):
        """Forward typedef struct with no full definition → violation."""
        files = [
            ("uart.h", "typedef struct Uart Uart;\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))

    def test_fwd_struct_message_contains_name(self):
        """Violation message names the undeclared typedef."""
        files = [
            ("uart.h", "typedef struct UartConfig UartConfig;\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        msgs = _msgs(files)
        self.assertTrue(any("UartConfig" in m for m in msgs))

    def test_fwd_enum_satisfied(self):
        """Forward typedef enum satisfied by full definition → no violation."""
        files = [
            ("state.h", "typedef enum State State;\n"),
            ("state.c", "typedef enum State { IDLE, RUNNING } State;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_fwd_enum_unsatisfied(self):
        """Forward typedef enum with no full definition → violation."""
        files = [
            ("state.h", "typedef enum State State;\n"),
            ("state.c", "int g_dummy = 0;\n"),
        ]
        self.assertIn("misc.declared_not_defined", _rules(files))

    def test_full_struct_not_flagged_as_forward(self):
        """typedef struct with body is a definition, not a forward declaration."""
        files = [
            ("uart.h", "typedef struct Uart { int baud; } Uart;\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        self.assertEqual(_check(files), [])


# ---------------------------------------------------------------------------
# 5. Inline suppression
# ---------------------------------------------------------------------------

class TestDndSuppression(unittest.TestCase):

    def test_inline_suppression_extern_func(self):
        """Inline suppression comment silences the violation for that symbol."""
        files = [
            ("hal.h",
             "extern void HAL_Init(void);  "
             "/* cstylecheck: disable misc.declared_not_defined */\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_inline_suppression_extern_var(self):
        """Inline suppression on extern variable silences violation."""
        files = [
            ("hal.h",
             "extern int HAL_baudRate;  "
             "/* cstylecheck: disable misc.declared_not_defined */\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        self.assertEqual(_check(files), [])

    def test_suppression_only_affects_that_line(self):
        """Suppression on one declaration does not suppress another."""
        files = [
            ("hal.h",
             "extern void HAL_Init(void);  "
             "/* cstylecheck: disable misc.declared_not_defined */\n"
             "extern void HAL_Deinit(void);\n"),
            ("main.c", "int g_dummy = 0;\n"),
        ]
        rules = _rules(files)
        # HAL_Init suppressed, HAL_Deinit should be flagged
        self.assertIn("misc.declared_not_defined", rules)
        count = rules.count("misc.declared_not_defined")
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# 6. Severity
# ---------------------------------------------------------------------------

class TestDndSeverity(unittest.TestCase):

    def test_default_severity_warning(self):
        """Default severity is 'warning'."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        violations = _check(files)
        self.assertTrue(all(v.severity == "warning" for v in violations))

    def test_custom_severity_error(self):
        """severity: error is respected."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        violations = _check(files, severity="error")
        self.assertTrue(all(v.severity == "error" for v in violations))

    def test_violation_rule_id(self):
        """Violation carries the correct rule ID."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        violations = _check(files)
        self.assertTrue(all(v.rule == "misc.declared_not_defined"
                            for v in violations))


# ---------------------------------------------------------------------------
# 7. Location attributes
# ---------------------------------------------------------------------------

class TestDndLocation(unittest.TestCase):

    def test_violation_filepath_is_declaration_file(self):
        """Violation filepath points to the file containing the declaration."""
        files = [
            ("uart.h", "extern void UART_Init(void);\n"),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        violations = _check(files)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].filepath, "uart.h")

    def test_violation_line_number(self):
        """Violation line number points to the declaration line."""
        src = "/* header */\nextern void UART_Init(void);\n"
        files = [
            ("uart.h", src),
            ("uart.c", "int g_dummy = 0;\n"),
        ]
        violations = _check(files)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].line, 2)


if __name__ == "__main__":
    unittest.main()
