"""
tests/test_update_config.py
============================
Tests for the --update-config flag and the supporting functions
_deep_merge, _collect_paths, update_config (issue #166).

Behaviour under test:
  - _deep_merge: shallow keys, nested dicts, user-wins, default-fills-gaps
  - _collect_paths: flat dict, nested dict
  - update_config: adds new keys, preserves user values, warns on unknowns,
                   handles missing file, handles non-mapping YAML, writes back
  - CLI --update-config flag integration
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure src/ is on the path (mirrors harness.py convention).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, os.path.dirname(__file__))

from cstylecheck.config import _deep_merge, _collect_paths, update_config

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _tmpyml(content: str) -> str:
    """Write *content* to a temp .yml file and return the path."""
    fh = tempfile.NamedTemporaryFile(suffix=".yml", delete=False,
                                     mode="w", encoding="utf-8")
    fh.write(content)
    fh.close()
    return fh.name


class _Exit(Exception):
    pass


def _exit_raise(msg=""):
    raise _Exit(str(msg))


# ---------------------------------------------------------------------------
# 1. _deep_merge
# ---------------------------------------------------------------------------

class TestDeepMerge(unittest.TestCase):

    def test_base_key_added_when_missing_in_override(self):
        """Keys only in base (defaults) are added to the result."""
        base     = {"a": 1, "b": 2}
        override = {"a": 99}
        result   = _deep_merge(base, override)
        self.assertEqual(result["a"], 99)   # override wins
        self.assertEqual(result["b"], 2)    # base filled in

    def test_override_key_wins(self):
        """Override value takes priority over base value."""
        base     = {"x": "default"}
        override = {"x": "custom"}
        self.assertEqual(_deep_merge(base, override)["x"], "custom")

    def test_new_key_in_override_added(self):
        """Keys only in override appear in the result."""
        base     = {"a": 1}
        override = {"b": 2}
        result   = _deep_merge(base, override)
        self.assertIn("a", result)
        self.assertIn("b", result)

    def test_nested_dict_merged_recursively(self):
        """Nested dicts are merged recursively, not replaced wholesale."""
        base     = {"rules": {"severity": "error", "enabled": True}}
        override = {"rules": {"enabled": False}}
        result   = _deep_merge(base, override)
        # 'severity' from base should be retained
        self.assertEqual(result["rules"]["severity"], "error")
        # 'enabled' from override should win
        self.assertFalse(result["rules"]["enabled"])

    def test_nested_non_dict_override_replaces(self):
        """When override value is not a dict, it replaces the base value."""
        base     = {"key": {"nested": True}}
        override = {"key": "flat_value"}
        result   = _deep_merge(base, override)
        self.assertEqual(result["key"], "flat_value")

    def test_empty_base(self):
        """Empty base returns a copy of override."""
        override = {"x": 1, "y": {"z": 2}}
        result   = _deep_merge({}, override)
        self.assertEqual(result, override)

    def test_empty_override(self):
        """Empty override returns a copy of base."""
        base   = {"x": 1}
        result = _deep_merge(base, {})
        self.assertEqual(result, base)

    def test_inputs_not_mutated(self):
        """_deep_merge is a pure function — inputs are not modified."""
        base     = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        _deep_merge(base, override)
        self.assertNotIn("c", base["a"])   # base not mutated
        self.assertNotIn("b", override["a"])  # override not mutated

    def test_list_values_use_override(self):
        """List values are not merged — override list replaces base list."""
        base     = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result   = _deep_merge(base, override)
        self.assertEqual(result["items"], [4, 5])


# ---------------------------------------------------------------------------
# 2. _collect_paths
# ---------------------------------------------------------------------------

class TestCollectPaths(unittest.TestCase):

    def test_flat_dict(self):
        d = {"a": 1, "b": 2}
        paths = _collect_paths(d)
        self.assertIn("a", paths)
        self.assertIn("b", paths)

    def test_nested_dict(self):
        d = {"outer": {"inner": 1}}
        paths = _collect_paths(d)
        self.assertIn("outer", paths)
        self.assertIn("outer.inner", paths)

    def test_deeply_nested(self):
        d = {"a": {"b": {"c": 1}}}
        paths = _collect_paths(d)
        self.assertIn("a.b.c", paths)

    def test_empty_dict(self):
        self.assertEqual(_collect_paths({}), [])


# ---------------------------------------------------------------------------
# 3. update_config — core behaviour
# ---------------------------------------------------------------------------

@unittest.skipIf(yaml is None, "PyYAML not installed")
class TestUpdateConfig(unittest.TestCase):

    def setUp(self):
        self._files: list = []

    def tearDown(self):
        for f in self._files:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _write(self, content: str) -> str:
        p = _tmpyml(content)
        self._files.append(p)
        return p

    def _read(self, path: str) -> dict:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    # --- Happy path: missing file ---

    def test_missing_file_returns_2(self):
        """Non-existent config path → return code 2."""
        rc = update_config("/no/such/rules.yml")
        self.assertEqual(rc, 2)

    # --- Happy path: keys are added ---

    def test_new_default_key_added(self):
        """A key present in defaults but absent from user config is added."""
        # Write a minimal user config that is missing 'spell_check'
        user_path = self._write("file_prefix:\n  enabled: true\n")
        # We need the bundled default to exist; mock _find_default_rules
        default_path = self._write(
            "file_prefix:\n  enabled: false\nspell_check:\n  enabled: false\n"
        )
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            rc = update_config(user_path)
        self.assertEqual(rc, 0)
        result = self._read(user_path)
        # spell_check should now be in the file (from default)
        self.assertIn("spell_check", result)

    def test_user_value_preserved(self):
        """Existing user values are NOT overwritten by defaults."""
        user_path = self._write("file_prefix:\n  enabled: true\n")
        default_path = self._write("file_prefix:\n  enabled: false\n")
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            update_config(user_path)
        result = self._read(user_path)
        # User had enabled: true — must survive the merge
        self.assertTrue(result["file_prefix"]["enabled"])

    def test_nested_default_key_added(self):
        """A nested key present in defaults but absent from user config is added."""
        user_path = self._write(
            "misc:\n  line_length:\n    enabled: true\n"
        )
        default_path = self._write(
            "misc:\n  line_length:\n    enabled: false\n  eof_comment:\n    enabled: true\n"
        )
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            update_config(user_path)
        result = self._read(user_path)
        self.assertIn("eof_comment", result["misc"])

    def test_returns_0_on_success(self):
        """Successful update returns 0."""
        user_path = self._write("file_prefix:\n  enabled: true\n")
        default_path = self._write("file_prefix:\n  enabled: true\n")
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            rc = update_config(user_path)
        self.assertEqual(rc, 0)

    def test_no_change_when_already_up_to_date(self):
        """Config that matches defaults exactly is written back unchanged."""
        content = "file_prefix:\n  enabled: true\nspell_check:\n  enabled: false\n"
        user_path    = self._write(content)
        default_path = self._write(content)
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            rc = update_config(user_path)
        self.assertEqual(rc, 0)
        result = self._read(user_path)
        self.assertTrue(result["file_prefix"]["enabled"])

    def test_unknown_key_preserved_in_output(self):
        """Keys in user config not in defaults are preserved in the merged output."""
        user_path = self._write(
            "file_prefix:\n  enabled: true\ncustom_setting: hello\n"
        )
        default_path = self._write("file_prefix:\n  enabled: false\n")
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            update_config(user_path)
        result = self._read(user_path)
        self.assertIn("custom_setting", result)

    def test_missing_default_file_returns_2(self):
        """If bundled default rules.yml cannot be found, return 2."""
        user_path = self._write("file_prefix:\n  enabled: true\n")
        non_existent = Path("/no/such/rules.yml")
        with patch("cstylecheck.config._find_default_rules",
                   return_value=non_existent):
            rc = update_config(user_path)
        self.assertEqual(rc, 2)

    def test_non_mapping_yaml_returns_2(self):
        """Config file that is a list, not a mapping, → return 2."""
        user_path = self._write("- item1\n- item2\n")
        default_path = self._write("file_prefix:\n  enabled: true\n")
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            rc = update_config(user_path)
        self.assertEqual(rc, 2)

    def test_output_prints_added_keys(self, capsys=None):
        """Print message lists new keys that were added."""
        user_path = self._write("file_prefix:\n  enabled: true\n")
        default_path = self._write(
            "file_prefix:\n  enabled: false\nspell_check:\n  enabled: false\n"
        )
        import io
        captured = io.StringIO()
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            with patch("sys.stdout", captured):
                update_config(user_path)
        output = captured.getvalue()
        self.assertIn("spell_check", output)

    def test_output_warns_unknown_keys(self):
        """Print WARNING for keys in user config not found in defaults."""
        user_path = self._write(
            "file_prefix:\n  enabled: true\nmy_custom_block:\n  x: 1\n"
        )
        default_path = self._write("file_prefix:\n  enabled: false\n")
        import io
        captured = io.StringIO()
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            with patch("sys.stdout", captured):
                update_config(user_path)
        self.assertIn("WARNING", captured.getvalue())
        self.assertIn("my_custom_block", captured.getvalue())


# ---------------------------------------------------------------------------
# 4. CLI integration — --update-config flag
# ---------------------------------------------------------------------------

@unittest.skipIf(yaml is None, "PyYAML not installed")
class TestUpdateConfigCLI(unittest.TestCase):
    """Test that --update-config is correctly wired up in the CLI."""

    def setUp(self):
        self._files: list = []
        self._orig_argv = sys.argv[:]

    def tearDown(self):
        sys.argv[:] = self._orig_argv
        for f in self._files:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _write(self, content: str) -> str:
        p = _tmpyml(content)
        self._files.append(p)
        return p

    def test_update_config_flag_exits_0(self):
        """--update-config returns exit code 0 when config exists."""
        from cstylecheck.cli import main
        user_path    = self._write("file_prefix:\n  enabled: true\n")
        default_path = self._write("file_prefix:\n  enabled: false\n")
        sys.argv = ["cstylecheck", "--config", user_path, "--update-config"]
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            rc = main()
        self.assertEqual(rc, 0)

    def test_update_config_modifies_file(self):
        """--update-config writes merged content back to --config file."""
        from cstylecheck.cli import main
        user_path    = self._write("file_prefix:\n  enabled: true\n")
        default_path = self._write(
            "file_prefix:\n  enabled: false\nspell_check:\n  enabled: false\n"
        )
        sys.argv = ["cstylecheck", "--config", user_path, "--update-config"]
        with patch("cstylecheck.config._find_default_rules",
                   return_value=Path(default_path)):
            main()
        result = yaml.safe_load(Path(user_path).read_text(encoding="utf-8"))
        self.assertIn("spell_check", result)

    def test_update_config_missing_file_exits_2(self):
        """--update-config with non-existent --config exits 2."""
        from cstylecheck.cli import main
        sys.argv = ["cstylecheck", "--config", "/no/such/rules.yml",
                    "--update-config"]
        rc = main()
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
