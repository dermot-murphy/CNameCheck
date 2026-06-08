"""test_assert_density.py — tests for misc.assert_density rule (issue #225)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, count

AD_CFG = cfg_only(misc={"assert_density": {
    "enabled": True, "severity": "info",
    "min_asserts": 1, "min_function_lines": 5, "exempt_functions": [],
}})

AD_CFG_2 = cfg_only(misc={"assert_density": {
    "enabled": True, "severity": "info",
    "min_asserts": 2, "min_function_lines": 5, "exempt_functions": [],
}})

AD_EXEMPT = cfg_only(misc={"assert_density": {
    "enabled": True, "severity": "info",
    "min_asserts": 1, "min_function_lines": 5,
    "exempt_functions": ["foo", "ISR_.*"],
}})


def _make_fn_with_asserts(n_asserts, n_lines=10):
    body = "\n".join(f"    int var_{i} = {i}; (void)var_{i};" for i in range(n_lines))
    asserts = "\n".join(f"    assert(var_{i} >= 0);" for i in range(n_asserts))
    return f"void foo(void) {{\n{body}\n{asserts}\n}}\n"


class TestAssertDensity(unittest.TestCase):

    def test_function_with_assert_passes(self):
        src = _make_fn_with_asserts(1)
        self.assertFalse(has(src, AD_CFG, "misc.assert_density"))

    def test_function_without_assert_fails(self):
        src = _make_fn_with_asserts(0)
        self.assertTrue(has(src, AD_CFG, "misc.assert_density"))

    def test_two_asserts_required_one_fails(self):
        src = _make_fn_with_asserts(1)
        self.assertTrue(has(src, AD_CFG_2, "misc.assert_density"))

    def test_two_asserts_required_two_passes(self):
        src = _make_fn_with_asserts(2)
        self.assertFalse(has(src, AD_CFG_2, "misc.assert_density"))

    def test_short_function_exempt(self):
        # Function body has only 2 body lines < min_function_lines (5) — not flagged
        src = "void foo(void) { int x = 0; (void)x; }\n"
        self.assertFalse(has(src, AD_CFG, "misc.assert_density"))

    def test_exempt_function_name_passes(self):
        src = _make_fn_with_asserts(0)
        self.assertFalse(has(src, AD_EXEMPT, "misc.assert_density"))

    def test_rule_disabled_passes(self):
        src = _make_fn_with_asserts(0)
        cfg = cfg_only()
        self.assertFalse(has(src, cfg, "misc.assert_density"))

    def test_multiple_functions_each_checked(self):
        src = _make_fn_with_asserts(0) + _make_fn_with_asserts(0)
        self.assertEqual(count(src, AD_CFG, "misc.assert_density"), 2)
