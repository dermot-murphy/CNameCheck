"""test_print_summary.py
=======================
Tests for the per-file breakdown section added to print_summary() (issue #278).

ASPICE traceability
-------------------
  SWE1 requirement: SWE1-089 (per-file summary breakdown in output)
  SWE4 test IDs:    UV-SUM-001 to UV-SUM-007
"""

import io
import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
from harness import Violation  # noqa: E402

# harness already added src/ to sys.path, so cstylecheck is importable
from cstylecheck.output import Tee, print_summary  # noqa: E402


def _v(filepath, severity):
    return Violation(filepath=filepath, line=1, col=1, severity=severity,
                     rule="test.rule", message="test message")


def _capture(violations, files_checked):
    """Run print_summary and return captured output string."""
    buf = io.StringIO()
    with patch("builtins.print",
               side_effect=lambda *a, **kw: buf.write(" ".join(str(x) for x in a) + "\n")):
        tee = Tee()
        print_summary(violations, files_checked, tee)
    return buf.getvalue()


class TestPrintSummaryPerFileBreakdown(unittest.TestCase):
    """Issue #278: print_summary must show a per-file breakdown section."""

    def test_per_file_section_present(self):
        """Output must contain a 'Files:' header."""
        out = _capture([_v("a.c", "error")], 1)
        self.assertIn("Files:", out)

    def test_files_with_errors_count(self):
        """Files with errors must be counted correctly."""
        viols = [_v("a.c", "error"), _v("a.c", "error"), _v("b.c", "error")]
        out = _capture(viols, 3)
        lines = [l for l in out.splitlines() if "Files with errors" in l]
        self.assertTrue(any("2" in l for l in lines))

    def test_files_with_warnings_count(self):
        """Files with warnings (no errors) counted in their own bucket."""
        viols = [_v("a.c", "warning"), _v("b.c", "error")]
        out = _capture(viols, 3)
        lines = [l for l in out.splitlines() if "Files with warnings" in l]
        self.assertTrue(any("1" in l for l in lines))

    def test_files_clean_count(self):
        """Clean files (no violations) are counted."""
        viols = [_v("a.c", "error")]
        out = _capture(viols, 3)
        lines = [l for l in out.splitlines() if "Files clean" in l]
        self.assertTrue(any("2" in l for l in lines))

    def test_all_clean(self):
        """Zero violations: all files shown as clean."""
        out = _capture([], 5)
        self.assertIn("Files:", out)
        lines = [l for l in out.splitlines() if "Files clean" in l]
        self.assertTrue(any("5" in l for l in lines))

    def test_file_counted_once_highest_severity(self):
        """A file with both errors and warnings is counted only under errors."""
        viols = [_v("a.c", "error"), _v("a.c", "warning")]
        out = _capture(viols, 2)
        err_lines = [l for l in out.splitlines() if "Files with errors" in l]
        warn_lines = [l for l in out.splitlines() if "Files with warnings" in l]
        self.assertTrue(any("1" in l for l in err_lines))
        self.assertTrue(any("0" in l for l in warn_lines))

    def test_no_files_checked_no_breakdown(self):
        """With 0 files checked, no breakdown section is emitted."""
        out = _capture([], 0)
        self.assertNotIn("Files:", out)


class TestPrintSummaryLabels(unittest.TestCase):
    """Issue #352: section labels and Files checked placement."""

    def test_errors_and_warnings_label_present(self):
        """Top section must be labelled 'Errors & Warnings:'."""
        out = _capture([_v("a.c", "error")], 1)
        self.assertIn("Errors & Warnings:", out)

    def test_files_checked_in_files_section(self):
        """'Files checked' must appear in the Files: section, not above it."""
        out = _capture([_v("a.c", "error")], 3)
        lines = out.splitlines()
        files_label_idx   = next(i for i, l in enumerate(lines) if "Files:" in l)
        files_checked_idx = next(i for i, l in enumerate(lines) if "Files checked" in l)
        self.assertGreater(files_checked_idx, files_label_idx)

    def test_files_checked_not_in_errors_section(self):
        """'Files checked' must NOT appear before the Errors & Warnings label."""
        out = _capture([_v("a.c", "warning")], 2)
        lines = out.splitlines()
        ew_idx = next(i for i, l in enumerate(lines) if "Errors & Warnings:" in l)
        fc_idx = next(i for i, l in enumerate(lines) if "Files checked" in l)
        self.assertGreater(fc_idx, ew_idx)

    def test_files_checked_count_correct(self):
        """Files checked count in the Files: section matches argument."""
        out = _capture([], 7)
        lines = [l for l in out.splitlines() if "Files checked" in l]
        self.assertTrue(any("7" in l for l in lines))


if __name__ == "__main__":
    unittest.main(verbosity=2)
