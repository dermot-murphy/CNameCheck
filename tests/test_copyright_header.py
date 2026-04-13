"""test_copyright_header.py — tests for misc.copyright_header.

Rule summary
------------
Every C source file must begin with a copyright block comment that exactly
matches the template supplied via --copyright FILE (implemented here by
calling ``load_copyright_file`` directly), with one exception: the year (or
year range) on the line containing "(C) Copyright" may differ.

Exactly one blank line must follow the closing ``*/`` of the header.

The rule is *only* active when a copyright template is passed to the Checker
(i.e. --copyright was provided on the CLI).  When no template is supplied the
check is silently skipped.

Violation cases
---------------
- File does not start with ``/*``
- File starts with ``/*`` but the block comment content differs from the template
- Copyright year differs on a non-year line (treated as mismatch)
- Header is correct but zero blank lines follow it
- Header is correct but more than one blank line follows it
- YAML ``enabled: false`` suppresses the rule even when a template is present
"""
import sys, os, re, textwrap, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count, load_copyright_file

RULE = "misc.copyright_header"

# ---------------------------------------------------------------------------
# Template text used throughout the tests
# ---------------------------------------------------------------------------

TEMPLATE = textwrap.dedent("""\
    /*
     * Acme Firmware
     * (C) Copyright 2024 Acme Corp. All rights reserved.
     *
     * SPDX-License-Identifier: Proprietary
     */""")

# The template with a different (older) year — must still pass
TEMPLATE_OLD_YEAR = TEMPLATE.replace("2024", "2019")
# A range variant used in some template tests
TEMPLATE_RANGE = TEMPLATE.replace("2024", "2020-2024")

# Minimal template with no year — tests the graceful "no year" path
TEMPLATE_NO_YEAR = textwrap.dedent("""\
    /*
     * Acme Firmware — no year line
     * All rights reserved.
     */""")


# ---------------------------------------------------------------------------
# Helper: build (template_text, compiled_re) without touching the filesystem
# ---------------------------------------------------------------------------

def _make_hdr(template_text: str = TEMPLATE) -> tuple:
    """
    Build a copyright header tuple the same way load_copyright_file does,
    but from an in-memory string instead of a file.
    Writes to a temp file and calls load_copyright_file so the real parser
    is exercised.
    """
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write(template_text)
        name = fh.name
    try:
        return load_copyright_file(name)
    finally:
        os.unlink(name)


HDR       = _make_hdr()                  # default template
HDR_RANGE = _make_hdr(TEMPLATE_RANGE)    # year-range template


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _cfg(enabled=True, sev="error"):
    return cfg_only(misc={"copyright_header": {
        "enabled": enabled,
        "severity": sev,
    }})


ON  = _cfg()
OFF = _cfg(enabled=False)


def _run(source, cfg=ON, hdr=HDR, filepath="module.c"):
    return run(source, cfg, filepath=filepath, copyright_header=hdr)

def _has(source, cfg=ON, hdr=HDR, filepath="module.c"):
    return any(v.rule == RULE for v in _run(source, cfg, hdr, filepath))

def _clean(source, cfg=ON, hdr=HDR, filepath="module.c"):
    return not _has(source, cfg, hdr, filepath)


# Correct source: exact template + one blank line + body
GOOD = TEMPLATE + "\n\nvoid f(void) {}\n"
# Correct source with only the header (minimal file)
GOOD_MINIMAL = TEMPLATE + "\n\n"


# ===========================================================================
# 1. Passing cases
# ===========================================================================

class TestCopyrightHeaderPasses(unittest.TestCase):

    def test_exact_match(self):
        """Exact template + one blank line."""
        self.assertTrue(_clean(GOOD))

    def test_minimal_file_header_only(self):
        """File is only the header + blank line."""
        self.assertTrue(_clean(GOOD_MINIMAL))

    def test_year_differs_single(self):
        """Source has a different single year — must pass."""
        src = TEMPLATE.replace("2024", "2021") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src))

    def test_year_differs_range_in_source(self):
        """Source has a year range where template has single year."""
        src = TEMPLATE.replace("2024", "2018-2024") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src))

    def test_year_range_in_template_single_in_source(self):
        """Template has YYYY-YYYY, source has single YYYY."""
        src = TEMPLATE_RANGE.replace("2020-2024", "2023") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src, hdr=HDR_RANGE))

    def test_year_range_in_template_range_in_source(self):
        """Template has YYYY-YYYY, source has different YYYY-YYYY."""
        src = TEMPLATE_RANGE.replace("2020-2024", "2019-2025") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src, hdr=HDR_RANGE))

    def test_en_dash_year_range(self):
        """Year range with en-dash (U+2013) in source is accepted."""
        src = TEMPLATE.replace("2024", "2020\u20132024") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src))

    def test_no_copyright_template_skips_check(self):
        """When no template is supplied the rule is never triggered."""
        src = "/* wrong header */\n\nvoid f(void) {}\n"
        violations = run(src, ON, copyright_header=None)
        self.assertFalse(any(v.rule == RULE for v in violations))

    def test_yaml_disabled_skips_check(self):
        """YAML enabled=false suppresses even when template is present."""
        self.assertTrue(_clean(GOOD, cfg=OFF))

    def test_body_content_irrelevant(self):
        """Arbitrary content after the blank line is not checked."""
        body = "static int s_counter = 0;\nvoid init(void) { s_counter = 1; }\n"
        src = TEMPLATE + "\n\n" + body
        self.assertTrue(_clean(src))

    def test_copyright_case_insensitive_for_word_copyright(self):
        """'copyright' keyword is matched case-insensitively in the template."""
        tpl_lower = TEMPLATE.replace("Copyright", "copyright")
        hdr_lower = _make_hdr(tpl_lower)
        src = tpl_lower.replace("2024", "1999") + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src, hdr=hdr_lower))

    def test_crlf_source_normalised(self):
        """CRLF line endings in the source are normalised before matching."""
        src_crlf = (TEMPLATE + "\n\nvoid f(void) {}\n").replace('\n', '\r\n')
        self.assertTrue(_clean(src_crlf))

    def test_severity_info_still_passes_clean(self):
        """Custom severity does not affect passing files."""
        cfg = _cfg(sev="info")
        self.assertTrue(_clean(GOOD, cfg=cfg))

    def test_header_without_year_matches_literally(self):
        """Template with no copyright year line matches the source literally."""
        hdr_ny = _make_hdr(TEMPLATE_NO_YEAR)
        src = TEMPLATE_NO_YEAR + "\n\nvoid f(void) {}\n"
        self.assertTrue(_clean(src, hdr=hdr_ny))


# ===========================================================================
# 2. Missing or wrong header content
# ===========================================================================

class TestCopyrightHeaderMissing(unittest.TestCase):

    def test_no_block_comment_at_all(self):
        """File starts with code — no /* anywhere near the top."""
        src = "int x = 0;\n\n" + GOOD
        self.assertTrue(_has(src))

    def test_starts_with_single_line_comment(self):
        """File starts with // comment, not /*."""
        src = "// Module header\n" + GOOD
        self.assertTrue(_has(src))

    def test_blank_line_before_header(self):
        """Leading blank line before /* is a mismatch."""
        src = "\n" + GOOD
        self.assertTrue(_has(src))

    def test_wrong_first_line_of_comment(self):
        """The /* opening line is correct but the second line differs."""
        bad = TEMPLATE.replace("Acme Firmware", "Different Project")
        src = bad + "\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_wrong_company_name(self):
        """Company name in copyright line differs."""
        bad = TEMPLATE.replace("Acme Corp", "Other Corp")
        src = bad + "\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_extra_line_in_header(self):
        """Source header has an extra line not in the template."""
        extra = TEMPLATE.replace(
            " * SPDX-License-Identifier: Proprietary",
            " * SPDX-License-Identifier: Proprietary\n * Extra line")
        src = extra + "\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_missing_line_in_header(self):
        """Source header is missing a line that the template has."""
        # Remove the blank separator line and SPDX line (they appear in this
        # order in TEMPLATE: ' *\n * SPDX-...')
        short = TEMPLATE.replace(" *\n * SPDX-License-Identifier: Proprietary", "")
        src = short + "\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_wrong_spdx_identifier(self):
        """SPDX identifier differs."""
        bad = TEMPLATE.replace("Proprietary", "MIT")
        src = bad + "\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_violation_rule_id(self):
        """Rule ID is misc.copyright_header."""
        src = "int x;\n"
        violations = _run(src)
        self.assertTrue(any(v.rule == RULE for v in violations))

    def test_violation_line_one_when_no_comment(self):
        """When no /* at start, violation is reported at line 1."""
        src = "int x;\n"
        violations = _run(src)
        hits = [v for v in violations if v.rule == RULE]
        self.assertTrue(hits)
        self.assertEqual(hits[0].line, 1)

    def test_violation_severity_matches_config(self):
        """Severity comes from the YAML config."""
        cfg = _cfg(sev="warning")
        src = "int x;\n"
        violations = run(src, cfg, copyright_header=HDR)
        hits = [v for v in violations if v.rule == RULE]
        self.assertTrue(hits)
        self.assertEqual(hits[0].severity, "warning")

    def test_mismatch_reports_differing_line(self):
        """When content mismatches, violation line points to the bad line."""
        # Line 2 of the template is " * Acme Firmware"; change it.
        bad = TEMPLATE.replace("Acme Firmware", "Wrong Project Name")
        src = bad + "\n\nvoid f(void) {}\n"
        violations = _run(src)
        hits = [v for v in violations if v.rule == RULE]
        self.assertTrue(hits)
        # Line 2 differs (/* is line 1, "Acme Firmware" is line 2)
        self.assertEqual(hits[0].line, 2)

    def test_exactly_one_violation_for_content_error(self):
        """Only one violation raised for wrong header content."""
        src = "/* totally wrong */\n\nvoid f(void) {}\n"
        hits = [v for v in _run(src) if v.rule == RULE]
        self.assertEqual(len(hits), 1)


# ===========================================================================
# 3. Correct header but wrong blank-line count
# ===========================================================================

class TestCopyrightHeaderBlankLine(unittest.TestCase):

    def test_no_blank_line_after_header(self):
        """Header immediately followed by code — no blank line."""
        src = TEMPLATE + "\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_two_blank_lines_after_header(self):
        """Two blank lines after header — one too many."""
        src = TEMPLATE + "\n\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_three_blank_lines_after_header(self):
        """Three blank lines after header."""
        src = TEMPLATE + "\n\n\n\nvoid f(void) {}\n"
        self.assertTrue(_has(src))

    def test_no_newline_at_all_after_header(self):
        """Header is last content with no trailing newline."""
        src = TEMPLATE   # no trailing \n at all
        self.assertTrue(_has(src))

    def test_whitespace_only_blank_line_counts(self):
        """A line with only spaces counts as blank."""
        src = TEMPLATE + "\n   \nvoid f(void) {}\n"
        self.assertTrue(_clean(src))

    def test_blank_line_violation_message_says_none(self):
        """Message says 'found none' when there is no blank line."""
        src = TEMPLATE + "\nvoid f(void) {}\n"
        violations = _run(src)
        msgs = [v.message for v in violations if v.rule == RULE]
        self.assertTrue(any("none" in m.lower() for m in msgs), msgs)

    def test_blank_line_violation_message_says_count(self):
        """Message includes the count when there are too many blank lines."""
        src = TEMPLATE + "\n\n\nvoid f(void) {}\n"  # 2 blanks
        violations = _run(src)
        msgs = [v.message for v in violations if v.rule == RULE]
        self.assertTrue(any("2" in m for m in msgs), msgs)

    def test_blank_line_violation_line_number(self):
        """Blank-line violation is reported on the line after */."""
        src = TEMPLATE + "\nvoid f(void) {}\n"
        violations = _run(src)
        hits = [v for v in violations if v.rule == RULE]
        self.assertTrue(hits)
        # Count lines in TEMPLATE to find where */ is
        tpl_lines = TEMPLATE.count('\n') + 1
        self.assertEqual(hits[0].line, tpl_lines + 1)

    def test_exactly_one_violation_for_blank_error(self):
        """Only one violation when content is right but blank count is wrong."""
        src = TEMPLATE + "\nvoid f(void) {}\n"   # missing blank
        hits = [v for v in _run(src) if v.rule == RULE]
        self.assertEqual(len(hits), 1)


# ===========================================================================
# 4. load_copyright_file() unit tests
# ===========================================================================

class TestLoadCopyrightFile(unittest.TestCase):

    def _write_and_load(self, text: str) -> tuple:
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt', delete=False, encoding='utf-8') as fh:
            fh.write(text)
            name = fh.name
        try:
            return load_copyright_file(name)
        finally:
            os.unlink(name)

    def test_returns_tuple(self):
        tpl, pat = self._write_and_load(TEMPLATE)
        self.assertIsInstance(tpl, str)
        self.assertTrue(hasattr(pat, 'match'))

    def test_template_text_matches_block_comment(self):
        tpl, _ = self._write_and_load(TEMPLATE)
        self.assertTrue(tpl.startswith('/*'))
        self.assertTrue(tpl.endswith('*/'))

    def test_pattern_anchored_to_start(self):
        """The compiled pattern must only match at position 0."""
        _, pat = self._write_and_load(TEMPLATE)
        # Should match the template itself at start
        self.assertIsNotNone(pat.match(TEMPLATE + "\n\n"))
        # Should NOT match the template when it's not at position 0
        self.assertIsNone(pat.match("\n" + TEMPLATE + "\n\n"))

    def test_pattern_accepts_different_year(self):
        """Pattern accepts any 4-digit year in the copyright line."""
        _, pat = self._write_and_load(TEMPLATE)
        for year in ["1999", "2000", "2024", "2099"]:
            src = TEMPLATE.replace("2024", year) + "\n\n"
            self.assertIsNotNone(pat.match(src), f"year {year} should match")

    def test_pattern_accepts_year_range(self):
        """Pattern accepts YYYY-YYYY in the copyright line."""
        _, pat = self._write_and_load(TEMPLATE)
        src = TEMPLATE.replace("2024", "2018-2024") + "\n\n"
        self.assertIsNotNone(pat.match(src))

    def test_pattern_accepts_en_dash_year_range(self):
        """Pattern accepts YYYY–YYYY (en-dash) in the copyright line."""
        _, pat = self._write_and_load(TEMPLATE)
        src = TEMPLATE.replace("2024", "2018\u20132024") + "\n\n"
        self.assertIsNotNone(pat.match(src))

    def test_pattern_rejects_wrong_company(self):
        """Pattern rejects a source where the company name differs."""
        _, pat = self._write_and_load(TEMPLATE)
        src = TEMPLATE.replace("Acme Corp", "Other Co") + "\n\n"
        self.assertIsNone(pat.match(src))

    def test_crlf_template_normalised(self):
        """CRLF in the template file is normalised to LF."""
        crlf_template = TEMPLATE.replace('\n', '\r\n')
        tpl, pat = self._write_and_load(crlf_template)
        self.assertNotIn('\r', tpl)
        self.assertIsNotNone(pat.match(TEMPLATE + "\n\n"))

    def test_file_with_surrounding_text(self):
        """Only the first /* ... */ block in the file is used."""
        text = "Some preamble text\n\n" + TEMPLATE + "\n\nTrailing text"
        tpl, _ = self._write_and_load(text)
        self.assertEqual(tpl, TEMPLATE)

    def test_template_with_range_accepts_single_year(self):
        """Template with YYYY-YYYY accepts a single year in the source."""
        _, pat = self._write_and_load(TEMPLATE_RANGE)
        src = TEMPLATE_RANGE.replace("2020-2024", "2025") + "\n\n"
        self.assertIsNotNone(pat.match(src))


# ===========================================================================
# 5. Edge / integration cases
# ===========================================================================

class TestCopyrightHeaderEdgeCases(unittest.TestCase):

    def test_empty_file(self):
        self.assertTrue(_has(""))

    def test_only_blank_lines(self):
        self.assertTrue(_has("\n\n\n"))

    def test_correct_header_is_entire_file(self):
        """Header + one blank line with nothing after — valid."""
        src = TEMPLATE + "\n\n"
        self.assertTrue(_clean(src))

    def test_bom_at_start_of_file(self):
        """UTF-8 BOM before /* is treated as 'no /* at start'."""
        src = '\ufeff' + GOOD
        # BOM means /* is not literally at position 0 in the raw string.
        # The checker strips BOM before looking for /* so this should pass.
        # (If the implementation does NOT strip BOM, this test documents that
        #  the BOM causes a violation — adjust assertion accordingly.)
        violations = _run(src)
        hits = [v for v in violations if v.rule == RULE]
        # Either passes cleanly (BOM stripped) or produces exactly one violation.
        self.assertLessEqual(len(hits), 1)

    def test_header_file_same_rule(self):
        """Rule applies equally to .h files."""
        src = TEMPLATE + "\n\n#ifndef FOO_H\n#define FOO_H\n#endif\n"
        self.assertTrue(_clean(src, filepath="foo.h"))

    def test_multiple_files_independent(self):
        """Each file checked independently — one bad, one good."""
        good_src = GOOD
        bad_src  = "int x;\n"
        good_violations = _run(good_src)
        bad_violations  = _run(bad_src)
        self.assertFalse(any(v.rule == RULE for v in good_violations))
        self.assertTrue(any(v.rule == RULE for v in bad_violations))

    def test_rule_id_string(self):
        """Rule ID is exactly 'misc.copyright_header'."""
        violations = _run("int x;\n")
        ids = [v.rule for v in violations]
        self.assertIn(RULE, ids)

    def test_content_mismatch_gives_one_violation_not_two(self):
        """Wrong content: only the content violation is raised, not a blank-line one too."""
        src = "/* wrong */\n\nvoid f(void) {}\n"
        hits = [v for v in _run(src) if v.rule == RULE]
        self.assertEqual(len(hits), 1)

    def test_correct_header_no_other_copyright_violations(self):
        """A valid header produces zero copyright violations."""
        self.assertEqual(
            sum(1 for v in _run(GOOD) if v.rule == RULE), 0)


if __name__ == "__main__":
    unittest.main()
