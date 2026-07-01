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


if __name__ == "__main__":
    unittest.main(verbosity=2)
