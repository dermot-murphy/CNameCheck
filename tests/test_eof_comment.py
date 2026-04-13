"""test_eof_comment.py — tests for misc.eof_comment.

Rule summary
------------
The last non-blank line of every C source file must equal the configured
template string, with ``{filename}`` substituted by the file's base name
(case controlled by ``filename_case``).  Exactly one blank line must follow
the EOF comment as the very last line of the file.

Default template : ``/* EOF: {filename} */``
Default case     : lower

Violation cases
---------------
- Last non-blank line does not match the expected string
- No blank line follows the EOF comment
- More than one blank line follows the EOF comment
- Line after EOF comment is non-blank
- File is empty / entirely blank
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has, clean, count

RULE = "misc.eof_comment"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _cfg(enabled=True, template="/* EOF: {filename} */",
         filename_case="lower", sev="warning"):
    return cfg_only(misc={"eof_comment": {
        "enabled":       enabled,
        "severity":      sev,
        "template":      template,
        "filename_case": filename_case,
    }})


ON  = _cfg()                # enabled, all defaults
OFF = _cfg(enabled=False)   # disabled


# Helpers that wire in a fixed filename so tests are self-contained.
FILE_C = "module.c"
FILE_H = "module.h"

EXPECTED_C = "/* EOF: module.c */"
EXPECTED_H = "/* EOF: module.h */"


def _run(source, cfg=ON, filepath=FILE_C):
    return run(source, cfg, filepath=filepath)

def _has(source, cfg=ON, filepath=FILE_C):
    return has(source, cfg, RULE, filepath=filepath)

def _clean(source, cfg=ON, filepath=FILE_C):
    return not _has(source, cfg, filepath)


# ---------------------------------------------------------------------------
# 1. Passing cases — must NOT flag
# ---------------------------------------------------------------------------

class TestEofCommentPasses(unittest.TestCase):

    def test_correct_structure(self):
        """Exact EOF comment followed by one blank line."""
        src = f"int x = 0;\n{EXPECTED_C}\n\n"
        self.assertTrue(_clean(src))

    def test_correct_header_file(self):
        """EOF comment adapted to .h extension."""
        src = f"#ifndef FOO_H\n#endif\n{EXPECTED_H}\n\n"
        self.assertTrue(_clean(src, filepath=FILE_H))

    def test_rule_disabled(self):
        """When disabled, any file tail is accepted."""
        src = "int x = 0;\n/* wrong */\n"
        self.assertTrue(_clean(src, cfg=OFF))

    def test_content_before_eof_comment_ignored(self):
        """Content before the EOF comment is not examined."""
        body = "void f(void) { }\n" * 10
        src = f"{body}{EXPECTED_C}\n\n"
        self.assertTrue(_clean(src))

    def test_whitespace_only_trailing_blank(self):
        """A trailing blank line containing only spaces counts as blank."""
        src = f"int x;\n{EXPECTED_C}\n   \n"
        self.assertTrue(_clean(src))

    def test_upper_case_filename(self):
        """filename_case=upper transforms basename to uppercase."""
        cfg = _cfg(filename_case="upper")
        expected = "/* EOF: MODULE.C */"
        src = f"int x;\n{expected}\n\n"
        self.assertTrue(_clean(src, cfg=cfg))

    def test_preserve_case_filename(self):
        """filename_case=preserve keeps the filename as-is."""
        cfg = _cfg(filename_case="preserve")
        # filepath has mixed case
        src = f"int x;\n/* EOF: MyModule.c */\n\n"
        self.assertTrue(_clean(src, cfg=cfg, filepath="MyModule.c"))

    def test_custom_template(self):
        """User-configured template is respected."""
        cfg = _cfg(template="// end of {filename}")
        src = f"int x;\n// end of module.c\n\n"
        self.assertTrue(_clean(src, cfg=cfg))

    def test_template_without_placeholder(self):
        """Template with no {filename} is a literal match."""
        cfg = _cfg(template="/* END OF FILE */")
        src = "int x;\n/* END OF FILE */\n\n"
        self.assertTrue(_clean(src, cfg=cfg))


# ---------------------------------------------------------------------------
# 2. Wrong last non-blank line — must flag
# ---------------------------------------------------------------------------

class TestEofCommentWrongContent(unittest.TestCase):

    def test_wrong_comment_text(self):
        """EOF comment with wrong text."""
        src = f"int x;\n/* EOF: wrong.c */\n\n"
        self.assertTrue(_has(src))

    def test_wrong_comment_no_colon(self):
        """Malformed comment misses the colon."""
        src = f"int x;\n/* EOF {FILE_C} */\n\n"
        self.assertTrue(_has(src))

    def test_wrong_comment_wrong_case(self):
        """filename in comment is uppercase but filename_case is lower."""
        src = f"int x;\n/* EOF: MODULE.C */\n\n"
        self.assertTrue(_has(src))

    def test_no_eof_comment_at_all(self):
        """File ends without any EOF comment."""
        src = "int x = 0;\n\n"
        self.assertTrue(_has(src))

    def test_eof_comment_is_code_line(self):
        """Last non-blank line is a code line, not the EOF comment."""
        src = f"int x = 0;\nreturn 0;\n\n"
        self.assertTrue(_has(src))

    def test_violation_message_content(self):
        """Violation message includes both expected and actual strings."""
        src = "int x;\n/* wrong */\n\n"
        violations = _run(src)
        msgs = [v.message for v in violations if v.rule == RULE]
        self.assertTrue(any(EXPECTED_C in m for m in msgs),
                        f"Expected '{EXPECTED_C}' in message, got: {msgs}")
        self.assertTrue(any("/* wrong */" in m for m in msgs),
                        f"Expected found text in message, got: {msgs}")

    def test_violation_line_number_points_to_last_nonblank(self):
        """Violation line number is the actual last non-blank line."""
        src = "int x;\nint y;\n/* wrong */\n\n"
        violations = _run(src)
        hits = [v for v in violations if v.rule == RULE
                and "Last non-blank" in v.message]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].line, 3)   # "/* wrong */" is on line 3

    def test_upper_case_mismatch(self):
        """Lower-case comment rejected when filename_case=upper."""
        cfg = _cfg(filename_case="upper")
        src = f"int x;\n{EXPECTED_C}\n\n"   # lower-case — wrong for upper cfg
        self.assertTrue(_has(src, cfg=cfg))

    def test_exactly_one_violation_for_content_error(self):
        """Only one violation raised for wrong content (trailing blank OK)."""
        src = "int x;\n/* wrong */\n\n"
        hits = [v for v in _run(src) if v.rule == RULE]
        self.assertEqual(len(hits), 1)


# ---------------------------------------------------------------------------
# 3. Wrong trailing blank line — must flag
# ---------------------------------------------------------------------------

class TestEofCommentTrailingBlank(unittest.TestCase):

    def test_no_trailing_blank_line(self):
        """EOF comment is the very last byte — no trailing newline."""
        src = f"int x;\n{EXPECTED_C}"
        self.assertTrue(_has(src))

    def test_no_trailing_blank_line_has_newline(self):
        """EOF comment ends with exactly one \\n (no blank line)."""
        src = f"int x;\n{EXPECTED_C}\n"
        self.assertTrue(_has(src))

    def test_two_trailing_blank_lines(self):
        """Two blank lines after EOF comment — one too many."""
        src = f"int x;\n{EXPECTED_C}\n\n\n"
        self.assertTrue(_has(src))

    def test_three_trailing_blank_lines(self):
        """Three blank lines after EOF comment."""
        src = f"int x;\n{EXPECTED_C}\n\n\n\n"
        self.assertTrue(_has(src))

    def test_non_blank_line_after_eof_comment(self):
        """A non-blank line after EOF comment means it is not the last non-blank line."""
        # In this case last_nb points to the actual last non-blank line
        # which is not the EOF comment, so we get a content mismatch.
        src = f"int x;\n{EXPECTED_C}\nsome_code();\n\n"
        self.assertTrue(_has(src))

    def test_violation_message_for_missing_blank(self):
        """Violation message mentions 'blank line'."""
        src = f"int x;\n{EXPECTED_C}\n"
        violations = _run(src)
        msgs = [v.message for v in violations if v.rule == RULE]
        self.assertTrue(any("blank" in m.lower() for m in msgs),
                        f"Expected blank-line mention, got: {msgs}")

    def test_violation_message_for_extra_blanks(self):
        """Violation message mentions count of trailing blank lines."""
        src = f"int x;\n{EXPECTED_C}\n\n\n"
        violations = _run(src)
        msgs = [v.message for v in violations if v.rule == RULE]
        self.assertTrue(any("2" in m for m in msgs),
                        f"Expected count '2' in message, got: {msgs}")

    def test_correct_content_wrong_trailing_exactly_one_violation(self):
        """When comment is right but trailing blank is wrong, exactly one violation."""
        src = f"int x;\n{EXPECTED_C}\n"    # missing blank
        hits = [v for v in _run(src) if v.rule == RULE]
        self.assertEqual(len(hits), 1)


# ---------------------------------------------------------------------------
# 4. Empty / degenerate files — must flag
# ---------------------------------------------------------------------------

class TestEofCommentEdgeCases(unittest.TestCase):

    def test_empty_file(self):
        """Entirely empty file raises violation."""
        self.assertTrue(_has(""))

    def test_blank_lines_only(self):
        """File with only blank lines raises violation."""
        self.assertTrue(_has("\n\n\n"))

    def test_single_line_no_newline(self):
        """Single non-blank line with no newline — content wrong, no blank."""
        src = "int x;"
        hits = [v for v in _run(src) if v.rule == RULE]
        # At minimum one violation (content mismatch)
        self.assertGreater(len(hits), 0)

    def test_eof_comment_is_only_content(self):
        """File contains only the EOF comment line — missing trailing blank."""
        src = f"{EXPECTED_C}\n"
        # Comment is correct but no blank line follows
        self.assertTrue(_has(src))

    def test_eof_comment_with_correct_trailing_is_only_content(self):
        """File is just the EOF comment + one blank line — valid."""
        src = f"{EXPECTED_C}\n\n"
        self.assertTrue(_clean(src))

    def test_filepath_with_directory(self):
        """Only the basename is substituted — directory components ignored."""
        src = f"int x;\n/* EOF: module.c */\n\n"
        # filepath contains directory prefix
        self.assertTrue(_clean(src, filepath="src/drivers/module.c"))

    def test_severity_propagated(self):
        """Configured severity appears on the violation."""
        cfg = _cfg(sev="error")
        src = "int x;\n/* wrong */\n\n"
        violations = _run(src, cfg=cfg)
        hits = [v for v in violations if v.rule == RULE]
        self.assertTrue(all(v.severity == "error" for v in hits))


if __name__ == "__main__":
    unittest.main()
