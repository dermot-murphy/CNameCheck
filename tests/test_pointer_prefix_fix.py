"""test_pointer_prefix_fix.py — Tests for --fix mode on variable.pointer_prefix.

Covers:
  - _fix_pointer_prefix() renaming parameter in signature + body
  - _fix_pointer_prefix() renaming in doxygen @param comment
  - fix_pointer_prefix_in_header() renaming in .h file declarations
  - apply_fixes() handling list returns from fix functions
  - --fix CLI mode for variable.pointer_prefix
"""
import sys
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import cfg_only, run, apply_fixes  # noqa: E402

_HERE   = Path(__file__).resolve().parent
_SRC    = _HERE.parent / "src"
_CHECKER = str(_SRC / "cstylecheck.py")
_YAML   = str(_HERE / "rules.yml") if (_HERE / "rules.yml").exists() \
          else str(_SRC / "rules.yml")

# Import the fixer functions directly
sys.path.insert(0, str(_SRC))
from cstylecheck.fixer import (  # noqa: E402
    _fix_pointer_prefix, fix_pointer_prefix_in_header, get_fn_name_for_fix,
)

PTR_CFG = cfg_only(variables={
    "enabled": True, "severity": "error",
    "case": "lower_snake", "min_length": 2, "max_length": 40,
    "allow_single_char_loop_vars": True,
    "allowed_abbreviations": [],
    "global":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": True,
                  "g_prefix": {"enabled": False}},
    "static":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": True,
                  "s_prefix": {"enabled": False}},
    "local":     {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": False},
    "parameter": {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False},
    "pointer_prefix": {"enabled": True, "severity": "warning", "prefix": "p_"},
    "pp_prefix":  {"enabled": False},
    "bool_prefix": {"enabled": False},
})


def _cli_fix(*args, content=None, filename="test_module.c"):
    """Write *content* to a temp file, run CLI with --fix, return (rc, out, new_text)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / filename
        if content:
            p.write_text(content)
        cmd = [sys.executable, _CHECKER, "--config", _YAML, *args]
        if content:
            cmd.append(str(p))
        r = subprocess.run(cmd, capture_output=True, text=True)
        new_text = p.read_text() if content else None
    return r.returncode, r.stdout + r.stderr, new_text


class TestFixPointerPrefixUnit(unittest.TestCase):
    """Unit tests for _fix_pointer_prefix() directly."""

    def _get_ptr_violation(self, src, filepath="uart.c"):
        viols = run(src, PTR_CFG, filepath=filepath)
        return [v for v in viols if v.rule == "variable.pointer_prefix"]

    def test_renames_param_in_signature(self):
        src = "void uart_Init(uint8_t *buf) { (void)buf; }\n"
        viols = self._get_ptr_violation(src)
        self.assertTrue(viols, "Expected pointer_prefix violation")
        edit = _fix_pointer_prefix(src, viols[0])
        self.assertIsNotNone(edit)
        self.assertIsInstance(edit, list)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("*p_buf", fixed)
        self.assertNotIn("*buf)", fixed)

    def test_renames_param_in_body(self):
        src = ("void uart_Init(uint8_t *buf) {\n"
               "    buf[0] = 0U;\n"
               "    buf[1] = 1U;\n"
               "}\n")
        viols = self._get_ptr_violation(src)
        self.assertTrue(viols)
        fixed, count = apply_fixes(src, viols)
        self.assertIn("p_buf[0]", fixed)
        self.assertIn("p_buf[1]", fixed)
        self.assertNotIn(" buf[", fixed)

    def test_renames_param_in_doxygen(self):
        src = ("/**\n"
               " * @brief Init UART.\n"
               " * @param buf  The buffer to use.\n"
               " */\n"
               "void uart_Init(uint8_t *buf) { (void)buf; }\n")
        viols = self._get_ptr_violation(src)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("@param p_buf", fixed)
        self.assertNotIn("@param buf", fixed)

    def test_no_violation_no_change(self):
        src = "void uart_Init(uint8_t *p_buf) { (void)p_buf; }\n"
        viols = self._get_ptr_violation(src)
        self.assertEqual(viols, [], "Should have no pointer_prefix violation")

    def test_declaration_in_header_scope(self):
        """Violation in a declaration (ends with ;) — renames within signature."""
        src = "void uart_Init(uint8_t *buf);\n"
        viols = run(src, PTR_CFG, filepath="uart.h")
        ptr_viols = [v for v in viols if v.rule == "variable.pointer_prefix"]
        self.assertTrue(ptr_viols)
        edit = _fix_pointer_prefix(src, ptr_viols[0])
        self.assertIsNotNone(edit)
        fixed, _ = apply_fixes(src, ptr_viols)
        self.assertIn("p_buf", fixed)


class TestGetFnNameForFix(unittest.TestCase):
    def test_simple_function(self):
        src = "void uart_Init(uint8_t *buf) { (void)buf; }\n"
        viols = run(src, PTR_CFG)
        ptr_viols = [v for v in viols if v.rule == "variable.pointer_prefix"]
        self.assertTrue(ptr_viols)
        fn_name = get_fn_name_for_fix(src, ptr_viols[0])
        self.assertEqual(fn_name, "uart_Init")


class TestFixPointerPrefixInHeader(unittest.TestCase):
    def test_renames_in_declaration(self):
        h_src = "void uart_Init(uint8_t *buf);\n"
        result = fix_pointer_prefix_in_header(h_src, "uart_Init", "buf", "p_buf")
        self.assertIn("p_buf", result)
        self.assertNotIn("*buf)", result)

    def test_does_not_rename_in_other_functions(self):
        h_src = ("void uart_Init(uint8_t *buf);\n"
                 "void other_fn(uint8_t *buf);\n")
        result = fix_pointer_prefix_in_header(h_src, "uart_Init", "buf", "p_buf")
        self.assertIn("uart_Init(uint8_t *p_buf)", result)
        # other_fn's parameter should be unchanged
        self.assertIn("other_fn(uint8_t *buf)", result)

    def test_no_match_returns_unchanged(self):
        h_src = "void other_fn(uint8_t *p_buf);\n"
        result = fix_pointer_prefix_in_header(h_src, "uart_Init", "buf", "p_buf")
        self.assertEqual(result, h_src)


class TestApplyFixesHandlesList(unittest.TestCase):
    """apply_fixes() must handle fix functions that return a list of tuples."""

    def test_list_return_flattened(self):
        src = "void uart_Init(uint8_t *buf) { buf[0] = 0U; }\n"
        viols = run(src, PTR_CFG)
        ptr_viols = [v for v in viols if v.rule == "variable.pointer_prefix"]
        self.assertTrue(ptr_viols)
        fixed, count = apply_fixes(src, ptr_viols)
        # Both the signature and body occurrence should be renamed
        self.assertIn("p_buf", fixed)
        self.assertGreater(count, 0)


# Config where parameter prefix (p_) and pointer prefix (ptr_) differ so
# the order bug from issue #346 can be reproduced.
_PTR_TRP_CFG = cfg_only(variables={
    "enabled": True, "severity": "error",
    "case": "lower_snake", "min_length": 2, "max_length": 40,
    "allow_single_char_loop_vars": True,
    "allowed_abbreviations": [],
    "global":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": False,
                  "g_prefix": {"enabled": False}},
    "static":    {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": False,
                  "s_prefix": {"enabled": False}},
    "local":     {"severity": "error", "case": "lower_snake",
                  "require_module_prefix": False},
    "parameter": {"severity": "warning", "case": "lower_snake",
                  "require_module_prefix": False,
                  "p_prefix": {"enabled": True, "prefix": "p_",
                               "severity": "warning"}},
    "pointer_prefix": {"enabled": True, "severity": "warning", "prefix": "tr_"},
    "pp_prefix":  {"enabled": False},
    "bool_prefix": {"enabled": False},
})


class TestPtrPrefixOrderFix(unittest.TestCase):
    """Issue #346: --fix must produce pointer-prefix OUTERMOST (p_tr_buf not tr_p_buf)."""

    def _ptr_viols(self, src, cfg=None):
        return [v for v in run(src, cfg or _PTR_TRP_CFG)
                if v.rule == "variable.pointer_prefix"]

    def test_param_with_param_prefix_gets_correct_order(self):
        """p_buf already has param prefix; pointer prefix 'tr_' inserts after it."""
        src = "void uart_Init(uint8_t *p_buf) { (void)p_buf; }\n"
        viols = self._ptr_viols(src)
        self.assertTrue(viols, "Expected pointer_prefix violation")
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_tr_buf", fixed)
        self.assertNotIn("tr_p_buf", fixed)

    def test_bare_param_gets_pointer_prefix(self):
        """No prefix at all: pointer prefix prepended directly."""
        src = "void uart_Init(uint8_t *buf) { (void)buf; }\n"
        viols = self._ptr_viols(src, PTR_CFG)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_buf", fixed)

    def test_ptr_suffix_stripped_on_rename(self):
        """data_ptr → p_data (trailing _ptr stripped before prepending prefix)."""
        src = "void uart_Init(uint8_t *data_ptr) { (void)data_ptr; }\n"
        viols = self._ptr_viols(src, PTR_CFG)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_data", fixed)
        self.assertNotIn("p_data_ptr", fixed)

    def test_bare_ptr_renamed_to_data(self):
        """ptr alone → p_data (bare name replaced by conventional stem)."""
        src = "void uart_Init(uint8_t *ptr) { (void)ptr; }\n"
        viols = self._ptr_viols(src, PTR_CFG)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_data", fixed)
        self.assertNotIn("p_ptr", fixed)


class TestLocalVarPtrFix(unittest.TestCase):
    """Issue #347: --fix renames local pointer variables within their function body."""

    def _ptr_viols(self, src):
        return [v for v in run(src, PTR_CFG)
                if v.rule == "variable.pointer_prefix"]

    def test_renames_local_var_in_body(self):
        src = ("void uart_Process(void) {\n"
               "    uint8_t *buffer = get_buf();\n"
               "    buffer[0] = 0U;\n"
               "    send(buffer, 4U);\n"
               "}\n")
        viols = self._ptr_viols(src)
        self.assertTrue(viols, "Expected pointer_prefix violation for 'buffer'")
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_buffer", fixed)
        self.assertNotIn("*buffer ", fixed)
        self.assertIn("p_buffer[0]", fixed)

    def test_local_ptr_suffix_stripped(self):
        """data_ptr local variable → p_data after fix."""
        src = ("void f(void) {\n"
               "    uint8_t *data_ptr = get_buf();\n"
               "    data_ptr[0] = 0U;\n"
               "}\n")
        viols = self._ptr_viols(src)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_data", fixed)
        self.assertNotIn("data_ptr", fixed)

    def test_bare_ptr_local_renamed_to_data(self):
        """ptr local variable → p_data after fix."""
        src = ("void f(void) {\n"
               "    uint8_t *ptr = get_buf();\n"
               "    ptr[0] = 0U;\n"
               "}\n")
        viols = self._ptr_viols(src)
        self.assertTrue(viols)
        fixed, _ = apply_fixes(src, viols)
        self.assertIn("p_data", fixed)

    def test_global_var_not_renamed(self):
        """Global pointer variable must NOT be auto-fixed."""
        src = ("uint8_t *g_buffer;\n"
               "void f(void) { (void)g_buffer; }\n")
        viols = self._ptr_viols(src)
        if not viols:
            return  # no violation — nothing to fix
        fixed, count = apply_fixes(src, viols)
        # No fix should have been applied for the global
        self.assertEqual(fixed, src,
                         "Global pointer variable must not be renamed by --fix")

    def test_static_var_not_renamed(self):
        """Static file-scope pointer variable must NOT be auto-fixed."""
        src = ("static uint8_t *s_buffer;\n"
               "void f(void) { (void)s_buffer; }\n")
        viols = self._ptr_viols(src)
        if not viols:
            return
        fixed, count = apply_fixes(src, viols)
        self.assertEqual(fixed, src,
                         "Static file-scope pointer must not be renamed by --fix")

    def test_only_renames_within_function_scope(self):
        """Rename must not bleed into the next function."""
        src = ("void foo(void) {\n"
               "    uint8_t *buffer = get();\n"
               "    (void)buffer;\n"
               "}\n"
               "void bar(uint8_t *buffer) {\n"
               "    (void)buffer;\n"
               "}\n")
        # Only the local variable 'buffer' in foo should be renamed
        viols = self._ptr_viols(src)
        # bar's parameter should also have a violation; fix both separately
        fixed, _ = apply_fixes(src, viols)
        # After fix, p_buffer appears in foo
        self.assertIn("uint8_t *p_buffer = get()", fixed)
        # bar's parameter is also renamed (separate violation)
        self.assertIn("bar(uint8_t *p_buffer)", fixed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
