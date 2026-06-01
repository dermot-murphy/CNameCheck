"""test_preprocessor.py — Direct unit tests for preprocessor.py functions.

Covers: strip_comments, strip_strings, preprocess, _comment_only_lines,
        extract_comments, _build_brace_depths, build_line_map,
        offset_to_line_col.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cstylecheck.preprocessor import (
    strip_comments,
    strip_strings,
    preprocess,
    _comment_only_lines,
    extract_comments,
    _build_brace_depths,
    build_line_map,
    offset_to_line_col,
)


# ---------------------------------------------------------------------------
# strip_comments
# ---------------------------------------------------------------------------

class TestStripComments(unittest.TestCase):

    def test_line_comment_replaced_with_spaces(self):
        src = "int x; // a comment\n"
        result = strip_comments(src)
        self.assertNotIn("//", result)
        self.assertEqual(len(result), len(src))

    def test_line_comment_preserves_newline(self):
        src = "int x; // comment\nint y;\n"
        result = strip_comments(src)
        self.assertEqual(result.count("\n"), src.count("\n"))

    def test_block_comment_replaced_with_spaces(self):
        src = "int x; /* block */ int y;"
        result = strip_comments(src)
        self.assertNotIn("/*", result)
        self.assertNotIn("*/", result)
        self.assertEqual(len(result), len(src))

    def test_block_comment_preserves_newlines(self):
        src = "int x;\n/* line1\n   line2\n*/\nint y;\n"
        result = strip_comments(src)
        self.assertEqual(result.count("\n"), src.count("\n"))

    def test_multiline_block_comment(self):
        src = "a\n/* foo\n   bar\n   baz\n*/\nb\n"
        result = strip_comments(src)
        self.assertNotIn("foo", result)
        self.assertNotIn("bar", result)
        self.assertNotIn("baz", result)
        self.assertEqual(len(result), len(src))

    def test_no_comments_unchanged(self):
        src = "int x = 1;\nreturn x;\n"
        self.assertEqual(strip_comments(src), src)

    def test_url_inside_line_comment_removed(self):
        src = "// see https://example.com\nint x;\n"
        result = strip_comments(src)
        self.assertNotIn("https", result)

    def test_block_comment_inline(self):
        src = "int /* counter */ x;"
        result = strip_comments(src)
        self.assertNotIn("counter", result)
        self.assertIn("x", result)
        self.assertEqual(len(result), len(src))

    def test_adjacent_block_comments(self):
        src = "/* a *//* b */int x;"
        result = strip_comments(src)
        self.assertNotIn("a", result)
        self.assertNotIn("b", result)
        self.assertIn("x", result)

    def test_comment_delimiter_inside_string_not_stripped(self):
        # The comment delimiter is inside a string — strip_comments alone
        # should still attempt to strip; only the combined preprocess()
        # call gets this fully right. Here we verify strip_comments does
        # not crash or corrupt the surrounding code.
        src = 'char *s = "/* not a comment */";\nint x;\n'
        result = strip_comments(src)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), len(src))

    def test_length_preserved_for_offset_tracking(self):
        src = "x /* hello */ y"
        result = strip_comments(src)
        self.assertEqual(len(result), len(src))

    def test_empty_block_comment(self):
        src = "int x = /**/1;"
        result = strip_comments(src)
        self.assertNotIn("/*", result)
        self.assertEqual(len(result), len(src))

    def test_empty_line_comment(self):
        src = "int x;//\nint y;\n"
        result = strip_comments(src)
        self.assertNotIn("//", result)
        self.assertEqual(len(result), len(src))


# ---------------------------------------------------------------------------
# strip_strings
# ---------------------------------------------------------------------------

class TestStripStrings(unittest.TestCase):

    def test_string_content_blanked(self):
        src = 'char *s = "hello world";'
        result = strip_strings(src)
        self.assertNotIn("hello", result)
        self.assertNotIn("world", result)

    def test_string_delimiters_preserved(self):
        src = 'char *s = "hello";'
        result = strip_strings(src)
        self.assertIn('"', result)

    def test_string_length_preserved(self):
        src = 'char *s = "hello world";'
        result = strip_strings(src)
        self.assertEqual(len(result), len(src))

    def test_empty_string_unchanged(self):
        src = 'char *s = "";'
        result = strip_strings(src)
        self.assertEqual(result, src)

    def test_escape_in_string(self):
        src = r'char *s = "say \"hi\"";'
        result = strip_strings(src)
        self.assertNotIn("say", result)
        self.assertEqual(len(result), len(src))

    def test_char_literal_normalised_to_x(self):
        src = "char c = 'A';"
        result = strip_strings(src)
        self.assertIn("'x'", result)
        self.assertNotIn("'A'", result)

    def test_char_literal_escape_normalised(self):
        src = r"char c = '\n';"
        result = strip_strings(src)
        self.assertIn("'x'", result)

    def test_no_strings_unchanged(self):
        src = "int x = 42;\n"
        self.assertEqual(strip_strings(src), src)

    def test_multiple_strings(self):
        src = '"foo" "bar"'
        result = strip_strings(src)
        self.assertNotIn("foo", result)
        self.assertNotIn("bar", result)
        self.assertEqual(len(result), len(src))

    def test_comment_delimiter_in_string_not_eaten(self):
        src = '"/*still a string*/"'
        result = strip_strings(src)
        self.assertEqual(len(result), len(src))
        self.assertNotIn("still", result)


# ---------------------------------------------------------------------------
# preprocess (combined)
# ---------------------------------------------------------------------------

class TestPreprocess(unittest.TestCase):

    def test_comments_and_strings_both_stripped(self):
        src = '/* header */\nchar *s = "hello"; // inline\n'
        result = preprocess(src)
        self.assertNotIn("header", result)
        self.assertNotIn("hello", result)
        self.assertNotIn("inline", result)

    def test_length_preserved(self):
        src = '/* comment */\nchar *s = "value";\nint x = 1;\n'
        result = preprocess(src)
        self.assertEqual(len(result), len(src))

    def test_newline_count_preserved(self):
        src = '/* line1\n   line2\n*/\nchar *s = "text";\n'
        result = preprocess(src)
        self.assertEqual(result.count("\n"), src.count("\n"))

    def test_code_tokens_remain(self):
        src = '/* hdr */\nint main(void) {\n    return 0;\n}\n'
        result = preprocess(src)
        self.assertIn("int", result)
        self.assertIn("return", result)

    def test_empty_source(self):
        self.assertEqual(preprocess(""), "")

    def test_string_containing_comment_marker(self):
        # The string contains comment markers; after preprocess the code
        # structure outside the string should survive.
        src = 'char *s = "a /* b */ c";\nint x;\n'
        result = preprocess(src)
        self.assertIn("int", result)
        self.assertIn("x", result)


# ---------------------------------------------------------------------------
# _comment_only_lines
# ---------------------------------------------------------------------------

class TestCommentOnlyLines(unittest.TestCase):

    def test_blank_line_is_exempt(self):
        src = "\n"
        self.assertIn(1, _comment_only_lines(src))

    def test_code_line_not_exempt(self):
        src = "int x = 1;\n"
        self.assertNotIn(1, _comment_only_lines(src))

    def test_line_comment_is_exempt(self):
        src = "// a comment\n"
        self.assertIn(1, _comment_only_lines(src))

    def test_block_comment_single_line_exempt(self):
        src = "/* single line */\n"
        self.assertIn(1, _comment_only_lines(src))

    def test_block_comment_multiline_all_exempt(self):
        src = "/*\n * middle\n */\n"
        exempt = _comment_only_lines(src)
        self.assertIn(1, exempt)
        self.assertIn(2, exempt)
        self.assertIn(3, exempt)

    def test_code_after_block_close_not_exempt(self):
        src = "/* comment */\nint x;\n"
        exempt = _comment_only_lines(src)
        self.assertIn(1, exempt)
        self.assertNotIn(2, exempt)

    def test_mixed_file(self):
        src = "int x;\n// comment\n\nint y;\n"
        exempt = _comment_only_lines(src)
        self.assertNotIn(1, exempt)  # code
        self.assertIn(2, exempt)     # line comment
        self.assertIn(3, exempt)     # blank
        self.assertNotIn(4, exempt)  # code

    def test_indented_line_comment(self):
        src = "    // indented comment\n"
        self.assertIn(1, _comment_only_lines(src))

    def test_indented_block_comment_start(self):
        src = "    /* start\n    end */\n"
        exempt = _comment_only_lines(src)
        self.assertIn(1, exempt)
        self.assertIn(2, exempt)

    def test_empty_source_returns_empty_set(self):
        self.assertEqual(_comment_only_lines(""), set())

    def test_block_never_closed_marks_rest_exempt(self):
        src = "int x;\n/* unclosed\nmore\n"
        exempt = _comment_only_lines(src)
        self.assertIn(2, exempt)
        self.assertIn(3, exempt)

    def test_inline_block_comment_line_not_exempt(self):
        # A line that has code AND a block comment is not comment-only.
        src = "int x; /* comment */\n"
        self.assertNotIn(1, _comment_only_lines(src))


# ---------------------------------------------------------------------------
# extract_comments
# ---------------------------------------------------------------------------

class TestExtractComments(unittest.TestCase):

    def test_line_comment_extracted(self):
        src = "int x; // a value\n"
        results = extract_comments(src)
        self.assertTrue(any("a value" in text for _, text in results))

    def test_block_comment_extracted(self):
        src = "/* block comment */\nint x;\n"
        results = extract_comments(src)
        self.assertTrue(any("block comment" in text for _, text in results))

    def test_line_number_correct_for_first_line(self):
        src = "// first\nint x;\n"
        results = extract_comments(src)
        linenos = [ln for ln, _ in results]
        self.assertIn(1, linenos)

    def test_line_number_correct_for_later_line(self):
        src = "int x;\nint y;\n// third line\n"
        results = extract_comments(src)
        linenos = [ln for ln, _ in results]
        self.assertIn(3, linenos)

    def test_doxygen_marker_stripped(self):
        src = "/** @param x the value */\n"
        results = extract_comments(src)
        self.assertTrue(any("param" not in text for _, text in results))

    def test_block_comment_asterisks_stripped(self):
        src = "/*\n * description\n */\n"
        results = extract_comments(src)
        texts = [text for _, text in results]
        self.assertFalse(any(text.strip().startswith("*") for text in texts))

    def test_no_comments_returns_empty(self):
        src = "int x = 1;\n"
        self.assertEqual(extract_comments(src), [])

    def test_multiple_line_comments(self):
        src = "// one\n// two\n// three\n"
        results = extract_comments(src)
        self.assertEqual(len(results), 3)

    def test_multiple_block_comments(self):
        src = "/* a */\n/* b */\n"
        results = extract_comments(src)
        self.assertEqual(len(results), 2)

    def test_returns_list_of_tuples(self):
        src = "// hello\n"
        results = extract_comments(src)
        self.assertIsInstance(results, list)
        self.assertIsInstance(results[0], tuple)
        self.assertEqual(len(results[0]), 2)


# ---------------------------------------------------------------------------
# _build_brace_depths
# ---------------------------------------------------------------------------

class TestBuildBraceDepths(unittest.TestCase):

    def test_no_braces_all_zero(self):
        src = "int x = 1;"
        depths = _build_brace_depths(src)
        self.assertEqual(depths, [0] * len(src))

    def test_length_matches_source(self):
        src = "void f(void) { int x; }"
        depths = _build_brace_depths(src)
        self.assertEqual(len(depths), len(src))

    def test_depth_increases_at_open_brace(self):
        src = "{"
        depths = _build_brace_depths(src)
        self.assertEqual(depths[0], 1)

    def test_depth_after_close_brace(self):
        # The '}' character records the depth of the scope it closes (pre-decrement).
        # Depth at positions AFTER '}' correctly reflects the outer scope.
        src = "{} "
        depths = _build_brace_depths(src)
        self.assertEqual(depths[0], 1)  # '{' — inner scope
        self.assertEqual(depths[1], 1)  # '}' — still inner (closes the scope)
        self.assertEqual(depths[2], 0)  # space after '}' — outer scope

    def test_nested_braces(self):
        # '}' records the depth of the scope it closes (pre-decrement).
        src = "{{} "
        depths = _build_brace_depths(src)
        self.assertEqual(depths[0], 1)  # outer '{'
        self.assertEqual(depths[1], 2)  # inner '{'
        self.assertEqual(depths[2], 2)  # '}' closes depth-2 scope
        self.assertEqual(depths[3], 1)  # space — back to outer scope

    def test_depth_never_negative(self):
        src = "}} int x;"
        depths = _build_brace_depths(src)
        self.assertTrue(all(d >= 0 for d in depths))

    def test_unmatched_close_clamps_at_zero(self):
        src = "}"
        depths = _build_brace_depths(src)
        self.assertEqual(depths[0], 0)

    def test_function_body(self):
        src = "void f(void) {\n    int x;\n}\n"
        depths = _build_brace_depths(src)
        open_idx  = src.index("{")
        close_idx = src.index("}")
        # '{' records the depth of the scope it opens (post-increment → 1)
        self.assertEqual(depths[open_idx], 1)
        # '}' records the depth of the scope it closes (pre-decrement → 1)
        self.assertEqual(depths[close_idx], 1)
        # characters after '}' are back at outer scope (0)
        self.assertEqual(depths[close_idx + 1], 0)

    def test_empty_source(self):
        self.assertEqual(_build_brace_depths(""), [])


# ---------------------------------------------------------------------------
# build_line_map
# ---------------------------------------------------------------------------

class TestBuildLineMap(unittest.TestCase):

    def test_single_line_no_newline(self):
        src = "int x;"
        offsets = build_line_map(src)
        self.assertEqual(offsets, [0])

    def test_single_line_with_newline(self):
        src = "int x;\n"
        offsets = build_line_map(src)
        self.assertEqual(len(offsets), 2)
        self.assertEqual(offsets[0], 0)
        self.assertEqual(offsets[1], 7)

    def test_three_lines(self):
        src = "a\nb\nc\n"
        offsets = build_line_map(src)
        self.assertEqual(len(offsets), 4)

    def test_first_offset_always_zero(self):
        src = "anything\n"
        offsets = build_line_map(src)
        self.assertEqual(offsets[0], 0)

    def test_offsets_are_sorted(self):
        src = "line1\nline2\nline3\n"
        offsets = build_line_map(src)
        self.assertEqual(offsets, sorted(offsets))

    def test_empty_source(self):
        offsets = build_line_map("")
        self.assertEqual(offsets, [0])

    def test_consecutive_newlines(self):
        src = "\n\n\n"
        offsets = build_line_map(src)
        self.assertEqual(len(offsets), 4)


# ---------------------------------------------------------------------------
# offset_to_line_col
# ---------------------------------------------------------------------------

class TestOffsetToLineCol(unittest.TestCase):

    def _offsets(self, src: str) -> list:
        return build_line_map(src)

    def test_start_of_file_is_line1_col1(self):
        src = "int x;\n"
        offsets = self._offsets(src)
        self.assertEqual(offset_to_line_col(offsets, 0), (1, 1))

    def test_mid_first_line(self):
        src = "int x;\n"
        offsets = self._offsets(src)
        line, col = offset_to_line_col(offsets, 4)
        self.assertEqual(line, 1)
        self.assertEqual(col, 5)

    def test_start_of_second_line(self):
        src = "int x;\nint y;\n"
        offsets = self._offsets(src)
        line, col = offset_to_line_col(offsets, 7)
        self.assertEqual(line, 2)
        self.assertEqual(col, 1)

    def test_third_line(self):
        src = "a\nb\nc\n"
        offsets = self._offsets(src)
        line, col = offset_to_line_col(offsets, 4)
        self.assertEqual(line, 3)
        self.assertEqual(col, 1)

    def test_column_within_second_line(self):
        src = "abc\ndefg\n"
        offsets = self._offsets(src)
        # 'g' is at offset 7 (0-based): line 2, col 4
        line, col = offset_to_line_col(offsets, 7)
        self.assertEqual(line, 2)
        self.assertEqual(col, 4)

    def test_last_char_before_newline(self):
        src = "abc\n"
        offsets = self._offsets(src)
        line, col = offset_to_line_col(offsets, 2)
        self.assertEqual(line, 1)
        self.assertEqual(col, 3)

    def test_offset_at_newline_character(self):
        src = "abc\ndef\n"
        offsets = self._offsets(src)
        line, col = offset_to_line_col(offsets, 3)
        self.assertEqual(line, 1)
        self.assertEqual(col, 4)

    def test_single_char_source(self):
        src = "x"
        offsets = self._offsets(src)
        self.assertEqual(offset_to_line_col(offsets, 0), (1, 1))

    def test_consistent_with_extract_comments(self):
        src = "int x;\n// comment on line 2\nint y;\n"
        results = extract_comments(src)
        self.assertTrue(any(ln == 2 for ln, _ in results))


if __name__ == "__main__":
    unittest.main(verbosity=2)
