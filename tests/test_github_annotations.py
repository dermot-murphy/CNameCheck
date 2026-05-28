"""test_github_annotations.py — regression tests for github_annotation() title
categories (issue #77).

Every rule category must produce the correct annotation title rather than the
previously hardcoded "NamingConvention" label.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import Violation


class TestGitHubAnnotationTitles(unittest.TestCase):
    """SWE4-TC-ANNOT-001 to 008 — issue #77 regression suite."""

    def _annotation_for(self, rule: str) -> str:
        return Violation("source.c", 10, 4, "error", rule, "message").github_annotation()

    # SWE4-TC-ANNOT-001
    def test_naming_variable_rule_uses_naming_convention_title(self):
        """variable.* rules must produce NamingConvention title."""
        self.assertIn("title=NamingConvention[variable.global.prefix]::",
                      self._annotation_for("variable.global.prefix"))

    # SWE4-TC-ANNOT-002
    def test_naming_function_rule_uses_naming_convention_title(self):
        """function.* rules must produce NamingConvention title."""
        self.assertIn("title=NamingConvention[function.prefix]::",
                      self._annotation_for("function.prefix"))

    # SWE4-TC-ANNOT-003
    def test_misra_trigraph_uses_misra_title(self):
        """misc.trigraph must produce MISRA title."""
        self.assertIn("title=MISRA[misc.trigraph]::",
                      self._annotation_for("misc.trigraph"))

    # SWE4-TC-ANNOT-004
    def test_misra_octal_uses_misra_title(self):
        """misc.octal_constant must produce MISRA title."""
        self.assertIn("title=MISRA[misc.octal_constant]::",
                      self._annotation_for("misc.octal_constant"))

    # SWE4-TC-ANNOT-005
    def test_misra_lowercase_l_uses_misra_title(self):
        """misc.lowercase_l_suffix must produce MISRA title."""
        self.assertIn("title=MISRA[misc.lowercase_l_suffix]::",
                      self._annotation_for("misc.lowercase_l_suffix"))

    # SWE4-TC-ANNOT-006
    def test_sign_compatibility_uses_signcompat_title(self):
        """sign_compatibility must produce SignCompat title."""
        self.assertIn("title=SignCompat[sign_compatibility]::",
                      self._annotation_for("sign_compatibility"))

    # SWE4-TC-ANNOT-007
    def test_spell_check_uses_spellcheck_title(self):
        """spell_check must produce SpellCheck title."""
        self.assertIn("title=SpellCheck[spell_check]::",
                      self._annotation_for("spell_check"))

    # SWE4-TC-ANNOT-008
    def test_other_misc_rule_uses_misc_title(self):
        """Non-MISRA misc.* rules must produce Misc title."""
        self.assertIn("title=Misc[misc.line_length]::",
                      self._annotation_for("misc.line_length"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
