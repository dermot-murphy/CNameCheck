"""test_print_summary.py
=======================
Tests for the per-file breakdown section added to print_summary() (issue #278).

ASPICE traceability
-------------------
  SWE1 requirement: SWE1-078 (per-file summary breakdown in output)
  SWE4 test IDs:    SWE4-TC-278-*
"""

import io
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))

# Import directly from the output module
_SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, _SRC_DIR)

import cstylecheck as _mod

Violation = _mod.Violation


def _make_tee():
    """Return a Tee that captures output to a StringIO buffer."""
    from cstylecheck.output import Tee
    buf = io.StringIO()
    tee = Tee(log_fh=buf)
    return tee, buf


def _capture(violations, files_checked):
    """Run print_summary and return the captured output string."""
    from cstylecheck.output import print_summary
    import io
    from unittest.mock import patch

    buf = io.StringIO()
    with patch("builtins.print", side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
        tee, _ = _make_tee()
        print_summary(violations, files_checked, tee)
    # Reopen and read through the log
    tee2, buf2 = _make_tee()
    from cstylecheck.output import print_summary as ps2
    with patch("builtins.print", side_effect=lambda *a, **kw: buf2.write(" ".join(str(x) for x in a) + "\n")):
        ps2(violations, files_checked, tee2)
    return buf2.getvalue()


def _v(filepath, severity):
    return Violation(filepath=filepath, line=1, col=1, severity=severity,
                     rule="test.rule", message="test message")


class TestPrintSummaryPerFileBreakdown(unittest.TestCase):
    """Issue #278: print_summary must show a per-file breakdown section."""

    def _run(self, violations, files_checked):
        return _capture(violations, files_checked)

    def test_per_file_section_present(self):
        """Output must contain a 'Per-file breakdown' header."""
        out = self._run([_v("a.c", "error")], 1)
        self.assertIn("Per-file breakdown", out)

    def test_files_with_errors_count(self):
        """Files with errors must be counted correctly."""
        viols = [_v("a.c", "error"), _v("a.c", "error"), _v("b.c", "error")]
        out = self._run(viols, 3)
        self.assertIn("Files with errors", out)
        # 2 unique files with errors
        lines = [l for l in out.splitlines() if "Files with errors" in l]
        self.assertTrue(any("2" in l for l in lines))

    def test_files_with_warnings_count(self):
        """Files with warnings (no errors) counted in their own bucket."""
        viols = [_v("a.c", "warning"), _v("b.c", "error")]
        out = self._run(viols, 3)
        lines = [l for l in out.splitlines() if "Files with warnings" in l]
        self.assertTrue(any("1" in l for l in lines))

    def test_files_clean_count(self):
        """Clean files (no violations) are counted."""
        viols = [_v("a.c", "error")]
        out = self._run(viols, 3)
        lines = [l for l in out.splitlines() if "Files clean" in l]
        self.assertTrue(any("2" in l for l in lines))

    def test_all_clean(self):
        """Zero violations: all files shown as clean."""
        out = self._run([], 5)
        self.assertIn("Per-file breakdown", out)
        lines = [l for l in out.splitlines() if "Files clean" in l]
        self.assertTrue(any("5" in l for l in lines))

    def test_file_counted_once_highest_severity(self):
        """A file with both errors and warnings is counted only under errors."""
        viols = [_v("a.c", "error"), _v("a.c", "warning")]
        out = self._run(viols, 2)
        err_lines = [l for l in out.splitlines() if "Files with errors" in l]
        warn_lines = [l for l in out.splitlines() if "Files with warnings" in l]
        # 1 file with errors
        self.assertTrue(any("1" in l for l in err_lines))
        # 0 files counted in warnings bucket (already in errors)
        self.assertTrue(any("0" in l for l in warn_lines))

    def test_no_files_checked_no_breakdown(self):
        """With 0 files checked, no breakdown section is emitted."""
        out = self._run([], 0)
        self.assertNotIn("Per-file breakdown", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
