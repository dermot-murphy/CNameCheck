"""Tests for GitHub Actions annotation formatting."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from harness import Violation  # noqa: E402


class TestGitHubAnnotationTitles(unittest.TestCase):
    def _annotation_for(self, rule):
        return Violation(
            "source.c", 10, 4, "error", rule, "message"
        ).github_annotation()

    def test_naming_rule_uses_naming_convention_title(self):
        self.assertIn("title=NamingConvention[variable.prefix]::",
                      self._annotation_for("variable.prefix"))

    def test_misra_rule_uses_misra_title(self):
        self.assertIn("title=MISRA[misc.trigraph]::",
                      self._annotation_for("misc.trigraph"))

    def test_sign_compatibility_rule_uses_signcompat_title(self):
        self.assertIn("title=SignCompat[sign_compatibility]::",
                      self._annotation_for("sign_compatibility"))

    def test_spell_check_rule_uses_spellcheck_title(self):
        self.assertIn("title=SpellCheck[spell_check]::",
                      self._annotation_for("spell_check"))

    def test_other_misc_rule_uses_misc_title(self):
        self.assertIn("title=Misc[misc.line_length]::",
                      self._annotation_for("misc.line_length"))


if __name__ == "__main__":
    unittest.main()
