"""test_thread_safe_globals.py — regression tests for thread-safe keyword and
stdlib overrides (issue #79).

main() previously mutated C_KEYWORDS / C_STDLIB_NAMES / _BUILTIN_DICT as
module-level globals when CLI override flags were supplied.  Those sets are
now stored as instance variables on Checker so concurrent invocations do not
race on shared state.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
import cstylecheck
from harness import cfg_only, has, clean


_RESERVED_CFG = cfg_only(reserved_names={"enabled": True, "severity": "error"})


class TestThreadSafeKeywords(unittest.TestCase):
    """SWE4-TC-THREAD-001 to 004 — issue #79 regression suite."""

    # SWE4-TC-THREAD-001
    def test_custom_keywords_override_used_by_checker(self):
        """A Checker created with c_keywords override uses those words, not globals."""
        custom_kw = frozenset({"mykeyword"})
        from harness import run
        src = "void f(void){ uint32_t mykeyword = 0U; (void)mykeyword; }\n"
        viols = run(src, _RESERVED_CFG, filepath="mod.c",
                    c_keywords=custom_kw)
        rules = [v.rule for v in viols]
        self.assertIn("reserved_name", rules,
                      "Custom keyword 'mykeyword' should be flagged")

    # SWE4-TC-THREAD-002
    def test_module_global_c_keywords_unchanged_after_checker(self):
        """Creating a Checker with c_keywords override must not mutate C_KEYWORDS."""
        before = frozenset(cstylecheck.C_KEYWORDS)
        custom_kw = frozenset({"mykeyword"})
        from harness import run
        src = "void f(void){ uint32_t mykeyword = 0U; (void)mykeyword; }\n"
        run(src, _RESERVED_CFG, filepath="mod.c", c_keywords=custom_kw)
        self.assertEqual(cstylecheck.C_KEYWORDS, before,
                         "C_KEYWORDS global must not be mutated by Checker")

    # SWE4-TC-THREAD-003
    def test_custom_stdlib_override_used_by_checker(self):
        """A Checker created with c_stdlib_names override uses those words."""
        custom_stdlib = frozenset({"my_stdlib_fn"})
        from harness import run
        src = "void f(void){ uint32_t my_stdlib_fn = 0U; (void)my_stdlib_fn; }\n"
        viols = run(src, _RESERVED_CFG, filepath="mod.c",
                    c_stdlib_names=custom_stdlib)
        rules = [v.rule for v in viols]
        self.assertIn("reserved_name", rules,
                      "Custom stdlib name 'my_stdlib_fn' should be flagged")

    # SWE4-TC-THREAD-004
    def test_module_global_c_stdlib_names_unchanged_after_checker(self):
        """Creating a Checker with c_stdlib_names override must not mutate C_STDLIB_NAMES."""
        before = frozenset(cstylecheck.C_STDLIB_NAMES)
        custom_stdlib = frozenset({"my_stdlib_fn"})
        from harness import run
        src = "void f(void){ uint32_t my_stdlib_fn = 0U; (void)my_stdlib_fn; }\n"
        run(src, _RESERVED_CFG, filepath="mod.c", c_stdlib_names=custom_stdlib)
        self.assertEqual(cstylecheck.C_STDLIB_NAMES, before,
                         "C_STDLIB_NAMES global must not be mutated by Checker")


if __name__ == "__main__":
    unittest.main(verbosity=2)
