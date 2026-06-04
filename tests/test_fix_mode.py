"""test_fix_mode.py — Tests for --fix mode (issue #189).

Covers apply_fixes(), unified_diff(), and end-to-end CLI --fix / --dry-run.
"""
import sys
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import apply_fixes, unified_diff, cfg_only, run  # noqa: E402

_HERE   = Path(__file__).resolve().parent
_SRC    = _HERE.parent / "src"
_CHECKER = str(_SRC / "cstylecheck.py")
_YAML   = str(_HERE / "rules.yml") if (_HERE / "rules.yml").exists() \
          else str(_SRC / "rules.yml")


def _cli(*args, content=None, filename="test.c"):
    """Write *content* to a temp file, run the CLI, return (rc, output)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / filename
        if content:
            p.write_text(content)
        cmd = [sys.executable, _CHECKER, "--config", _YAML, *args]
        if content:
            cmd.append(str(p))
        r = subprocess.run(cmd, capture_output=True, text=True)
        fixed_text = p.read_text() if content else None
    return r.returncode, r.stdout + r.stderr, fixed_text


_US_CFG = cfg_only(misc={
    "unsigned_suffix": {
        "enabled": True, "severity": "info",
        "require_on_unsigned_constants": True,
    },
})

_LL_CFG = cfg_only(misc={
    "lowercase_l_suffix": {"enabled": True, "severity": "error"},
})


# ---------------------------------------------------------------------------
class TestApplyFixes(unittest.TestCase):

    def test_unsigned_suffix_appends_U(self):
        src = "uint8_t uart_Init(void) { uint8_t uart_x = 42; return uart_x; }\n"
        violations = run(src, _US_CFG, filepath="uart.c")
        us_violations = [v for v in violations if v.rule == "misc.unsigned_suffix"]
        self.assertGreater(len(us_violations), 0)
        fixed, count = apply_fixes(src, us_violations)
        self.assertIn("42U", fixed)
        self.assertNotIn(" 42;", fixed)
        self.assertEqual(count, len(us_violations))

    def test_lowercase_l_suffix_uppercased(self):
        src = "long uart_Init(void) { long uart_x = 100l; return uart_x; }\n"
        violations = run(src, _LL_CFG, filepath="uart.c")
        ll_violations = [v for v in violations if v.rule == "misc.lowercase_l_suffix"]
        self.assertGreater(len(ll_violations), 0)
        fixed, count = apply_fixes(src, ll_violations)
        self.assertIn("100L", fixed)
        self.assertNotIn("100l", fixed)
        self.assertEqual(count, len(ll_violations))

    def test_no_fixable_violations_returns_unchanged(self):
        src = "uint8_t uart_Init(void) { return 0U; }\n"
        fixed, count = apply_fixes(src, [])
        self.assertEqual(fixed, src)
        self.assertEqual(count, 0)

    def test_safe_only_applies_only_safe_fixes(self):
        src = "uint8_t uart_Init(void) { uint8_t uart_x = 42; return uart_x; }\n"
        violations = run(src, _US_CFG, filepath="uart.c")
        fixed, count = apply_fixes(src, violations, safe_only=True)
        # unsigned_suffix is a safe fix — should still be applied
        self.assertIn("42U", fixed)

    def test_multiple_literals_all_fixed(self):
        src = "uint8_t uart_Init(void) { uint8_t uart_x = 10; uint8_t uart_y = 20; return uart_x; }\n"
        violations = run(src, _US_CFG, filepath="uart.c")
        us_violations = [v for v in violations if v.rule == "misc.unsigned_suffix"]
        fixed, count = apply_fixes(src, us_violations)
        self.assertIn("10U", fixed)
        self.assertIn("20U", fixed)


# ---------------------------------------------------------------------------
class TestUnifiedDiff(unittest.TestCase):

    def test_diff_shows_change(self):
        original = "int x = 42;\n"
        fixed    = "int x = 42U;\n"
        diff = unified_diff(original, fixed, "test.c")
        self.assertIn("-int x = 42;", diff)
        self.assertIn("+int x = 42U;", diff)

    def test_no_change_produces_empty_diff(self):
        src = "int x = 42U;\n"
        diff = unified_diff(src, src, "test.c")
        self.assertEqual(diff, "")


# ---------------------------------------------------------------------------
class TestCLIFixMode(unittest.TestCase):

    def test_fix_rewrites_file(self):
        src = "long uart_Init(void) { long uart_x = 100l; return uart_x; }\n"
        rc, out, fixed_text = _cli("--fix", content=src)
        self.assertIn("100L", fixed_text)
        self.assertNotIn("100l", fixed_text)

    def test_dry_run_does_not_rewrite(self):
        src = "long uart_Init(void) { long uart_x = 100l; return uart_x; }\n"
        rc, out, fixed_text = _cli("--fix", "--dry-run", content=src)
        # File should be UNCHANGED
        self.assertIn("100l", fixed_text)
        # But the diff should be in output
        self.assertIn("-", out)

    def test_dry_run_shows_diff(self):
        src = "long uart_Init(void) { long uart_x = 100l; return uart_x; }\n"
        rc, out, _ = _cli("--fix", "--dry-run", content=src)
        self.assertIn("100L", out)

    def test_fix_no_violations_reports_none(self):
        src = "long uart_Init(void) { long uart_x = 100L; return uart_x; }\n"
        rc, out, fixed_text = _cli("--fix", "--dry-run", content=src)
        # lowercase_l is fine here; nothing to fix
        self.assertNotIn("---", out)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
