"""
tests/test_config_loading.py
============================
Tests for config.py loading behaviour — focusing on edge cases that are not
covered by the main test suite (encoding errors, missing files, bad YAML).

Issue #167: UnicodeDecodeError when rules.yml contains non-ASCII bytes such as
the Windows-1252 ellipsis (0x85) or a Latin-1 em-dash (0x96).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure src/ is on the path (mirrors harness.py convention).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, os.path.dirname(__file__))

# We test load_config by importing it directly.  sys.exit() is patched so
# the tests can capture the error message without actually exiting.
from unittest.mock import patch

from cstylecheck.config import load_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Exit(Exception):
    """Raised instead of sys.exit() so tests can capture the message."""
    pass


def _exit_raise(msg=""):
    raise _Exit(str(msg))


def _make_exit():
    """Return a fresh side_effect function for patching sys.exit."""
    return _exit_raise


# ---------------------------------------------------------------------------
# 1. Happy-path UTF-8 loading
# ---------------------------------------------------------------------------

class TestLoadConfigUTF8(unittest.TestCase):

    def _write(self, content: bytes) -> str:
        fh = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        fh.write(content)
        fh.close()
        return fh.name

    def tearDown(self):
        # Temp files are cleaned up individually in each test.
        pass

    def test_valid_utf8_yaml(self):
        """Well-formed UTF-8 YAML returns a dict."""
        path = self._write(b"spell_check:\n  enabled: false\n")
        try:
            cfg = load_config(path)
            self.assertIsInstance(cfg, dict)
            self.assertIn("spell_check", cfg)
        finally:
            os.unlink(path)

    def test_valid_utf8_with_unicode_comment(self):
        """UTF-8 file containing multi-byte characters (e.g. em-dash U+2014)."""
        content = "# config — version 1\nspell_check:\n  enabled: false\n"
        path = self._write(content.encode("utf-8"))
        try:
            cfg = load_config(path)
            self.assertIsInstance(cfg, dict)
        finally:
            os.unlink(path)

    def test_empty_yaml_returns_none_not_dict(self):
        """Empty YAML file is valid — yaml.safe_load returns None for empty input."""
        path = self._write(b"")
        try:
            # load_config returns whatever yaml.safe_load returns (None for empty).
            result = load_config(path)
            self.assertIsNone(result)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# 2. Missing file
# ---------------------------------------------------------------------------

class TestLoadConfigMissingFile(unittest.TestCase):

    def test_missing_file_exits(self):
        """Non-existent path → sys.exit with 'not found' message."""
        with patch("sys.exit", side_effect=_exit_raise):
            with self.assertRaises(_Exit) as ctx:
                load_config("/nonexistent/path/rules.yml")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_missing_file_message_contains_path(self):
        """Error message contains the offending path."""
        bad_path = "/no/such/rules.yml"
        with patch("sys.exit", side_effect=_exit_raise):
            with self.assertRaises(_Exit) as ctx:
                load_config(bad_path)
        self.assertIn(bad_path, str(ctx.exception))


# ---------------------------------------------------------------------------
# 3. Non-UTF-8 bytes (issue #167)
# ---------------------------------------------------------------------------

class TestLoadConfigNonUTF8(unittest.TestCase):

    def _write(self, content: bytes) -> str:
        fh = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        fh.write(content)
        fh.close()
        return fh.name

    def _assert_non_utf8_exit(self, raw: bytes):
        """Helper: write raw bytes, call load_config, expect sys.exit with clear msg."""
        path = self._write(raw)
        try:
            with patch("sys.exit", side_effect=_exit_raise):
                with self.assertRaises(_Exit) as ctx:
                    load_config(path)
            msg = str(ctx.exception)
            return msg
        finally:
            os.unlink(path)

    def test_windows1252_ellipsis_0x85(self):
        """Windows-1252 ellipsis byte 0x85 triggers clear error, not raw traceback."""
        # Valid YAML prefix + a Windows-1252 ellipsis where a comment might be
        raw = b"spell_check:\n  enabled: false  # options\x85\n"
        msg = self._assert_non_utf8_exit(raw)
        self.assertIn("non-UTF-8", msg)
        # byte value may be formatted as 0x85 or 0X85 (implementation choice)
        self.assertIn("85", msg.lower())

    def test_latin1_em_dash_0x96(self):
        """Latin-1 em-dash byte 0x96 triggers clear error."""
        raw = b"# config\x96note\nspell_check:\n  enabled: false\n"
        msg = self._assert_non_utf8_exit(raw)
        self.assertIn("non-UTF-8", msg)
        self.assertIn("96", msg.lower())

    def test_error_message_contains_filename(self):
        """Error message names the offending file."""
        raw = b"key: value\x85\n"
        path = self._write(raw)
        try:
            with patch("sys.exit", side_effect=_exit_raise):
                with self.assertRaises(_Exit) as ctx:
                    load_config(path)
            self.assertIn(path, str(ctx.exception))
        finally:
            os.unlink(path)

    def test_error_message_contains_byte_offset(self):
        """Error message includes the byte offset of the bad byte."""
        prefix = b"spell_check:\n  enabled: false\n"
        raw = prefix + b"\x85\n"
        expected_offset = len(prefix)
        path = self._write(raw)
        try:
            with patch("sys.exit", side_effect=_exit_raise):
                with self.assertRaises(_Exit) as ctx:
                    load_config(path)
            msg = str(ctx.exception)
            self.assertIn(str(expected_offset), msg)
        finally:
            os.unlink(path)

    def test_error_message_contains_save_as_utf8_hint(self):
        """Error message tells the user to save as UTF-8."""
        raw = b"key: value\x96\n"
        msg = self._assert_non_utf8_exit(raw)
        self.assertIn("UTF-8", msg)

    def test_pure_binary_file(self):
        """Completely binary file triggers clear non-UTF-8 error."""
        raw = bytes(range(128, 200))
        msg = self._assert_non_utf8_exit(raw)
        self.assertIn("non-UTF-8", msg)


# ---------------------------------------------------------------------------
# 4. Bad YAML (valid UTF-8 but malformed syntax)
# ---------------------------------------------------------------------------

class TestLoadConfigBadYAML(unittest.TestCase):

    def _write(self, content: bytes) -> str:
        fh = tempfile.NamedTemporaryFile(suffix=".yml", delete=False)
        fh.write(content)
        fh.close()
        return fh.name

    def test_bad_yaml_exits(self):
        """Malformed YAML → sys.exit with 'parse' or 'Cannot parse' message."""
        raw = b"key: [unclosed\n"
        path = self._write(raw)
        try:
            with patch("sys.exit", side_effect=_exit_raise):
                with self.assertRaises(_Exit) as ctx:
                    load_config(path)
            msg = str(ctx.exception).lower()
            self.assertTrue("parse" in msg or "cannot" in msg)
        finally:
            os.unlink(path)

    def test_bad_yaml_message_contains_filename(self):
        """YAML parse error message names the offending file."""
        raw = b"bad: [yaml\n"
        path = self._write(raw)
        try:
            with patch("sys.exit", side_effect=_exit_raise):
                with self.assertRaises(_Exit) as ctx:
                    load_config(path)
            self.assertIn(path, str(ctx.exception))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
