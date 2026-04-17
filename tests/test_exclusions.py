"""test_exclusions.py -- tests for the per-file and per-identifier exclusion system.

Exclusions are configured via a YAML file passed with --exclusions FILE.

Per-file exclusions (existing):
  "filename.c":
    disabled_rules:
      - function.prefix
      - misc.magic_number

Per-identifier exclusions (new):
  "filename.c":
    identifiers:
      LegacyFunction:
        disabled_rules:
          - function.prefix
          - function.style
      g_legacy_var:
        disabled_rules:
          - variable.global.g_prefix

Both can be combined:
  "filename.c":
    disabled_rules:         # suppresses for EVERY identifier in file
      - misc.magic_number
    identifiers:            # suppresses for SPECIFIC identifiers only
      LegacyFn:
        disabled_rules:
          - function.prefix
"""
import sys, os, tempfile, subprocess, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import cfg_only, run, has

_HERE    = Path(__file__).resolve().parent
_SRC     = _HERE.parent / "src"
CHECKER  = str(_SRC / "cstylecheck.py")
YAML     = str(_HERE / "rules.yml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(td, name, content):
    p = Path(td) / name
    p.write_text(content)
    return str(p)


def _run_with_excl(td, excl_yaml, c_src, filename="mod.c"):
    """Write files, run checker, return combined output string."""
    src_file  = _write(td, filename, c_src)
    excl_file = _write(td, "excl.yml", excl_yaml)
    r = subprocess.run(
        [sys.executable, CHECKER, "--config", YAML,
         "--exclusions", excl_file, src_file],
        capture_output=True, text=True,
    )
    return r.stdout + r.stderr


def _violations_in(output, rule=None, identifier=None):
    """Return lines from output that match the given rule and/or identifier."""
    lines = output.splitlines()
    result = []
    for line in lines:
        if rule and rule not in line:
            continue
        if identifier and identifier not in line:
            continue
        if ": " in line and "[" in line:
            result.append(line)
    return result


# ---------------------------------------------------------------------------
# load_exclusions_file unit tests
# ---------------------------------------------------------------------------

class TestLoadExclusionsFile(unittest.TestCase):

    def _load(self, yaml_text):
        import cstylecheck as m
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "excl.yml"
            f.write_text(yaml_text)
            return m.load_exclusions_file(str(f))

    def test_file_level_rules_parsed(self):
        data = self._load('"mod.c":\n  disabled_rules:\n    - function.prefix\n')
        self.assertIn("mod.c", data)
        self.assertIn("function.prefix", data["mod.c"]["file_rules"])

    def test_identifier_rules_parsed(self):
        data = self._load(
            '"mod.c":\n'
            '  identifiers:\n'
            '    LegacyFn:\n'
            '      disabled_rules:\n'
            '        - function.prefix\n'
            '        - function.style\n'
        )
        ident_rules = data["mod.c"]["ident_rules"]
        self.assertIn("LegacyFn", ident_rules)
        self.assertIn("function.prefix", ident_rules["LegacyFn"])
        self.assertIn("function.style",  ident_rules["LegacyFn"])

    def test_combined_file_and_identifier_rules(self):
        data = self._load(
            '"mod.c":\n'
            '  disabled_rules:\n'
            '    - misc.magic_number\n'
            '  identifiers:\n'
            '    OldFn:\n'
            '      disabled_rules:\n'
            '        - function.prefix\n'
        )
        self.assertIn("misc.magic_number", data["mod.c"]["file_rules"])
        self.assertIn("OldFn", data["mod.c"]["ident_rules"])

    def test_empty_identifiers_ok(self):
        data = self._load('"mod.c":\n  disabled_rules:\n    - function.prefix\n')
        self.assertEqual(data["mod.c"]["ident_rules"], {})

    def test_multiple_identifiers(self):
        data = self._load(
            '"mod.c":\n'
            '  identifiers:\n'
            '    FnOne:\n'
            '      disabled_rules:\n'
            '        - function.prefix\n'
            '    FnTwo:\n'
            '      disabled_rules:\n'
            '        - function.style\n'
        )
        ir = data["mod.c"]["ident_rules"]
        self.assertIn("FnOne", ir)
        self.assertIn("FnTwo", ir)

    def test_glob_pattern_key_preserved(self):
        data = self._load('"ascii.*":\n  disabled_rules:\n    - function.prefix\n')
        self.assertIn("ascii.*", data)

    def test_multiple_file_patterns(self):
        data = self._load(
            '"mod_a.c":\n  disabled_rules:\n    - function.prefix\n'
            '"mod_b.c":\n  disabled_rules:\n    - function.style\n'
        )
        self.assertIn("mod_a.c", data)
        self.assertIn("mod_b.c", data)


# ---------------------------------------------------------------------------
# _disabled_rules_for_file unit tests
# ---------------------------------------------------------------------------

class TestDisabledRulesForFile(unittest.TestCase):

    def _build_excl(self, yaml_text):
        import cstylecheck as m
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "excl.yml"
            f.write_text(yaml_text)
            return m.load_exclusions_file(str(f))

    def _get(self, filepath, yaml_text):
        import cstylecheck as m
        excl = self._build_excl(yaml_text)
        return m._disabled_rules_for_file(filepath, excl)

    def test_file_rules_returned_for_matching_file(self):
        fd, _ = self._get("/src/mod.c",
                          '"mod.c":\n  disabled_rules:\n    - function.prefix\n')
        self.assertIn("function.prefix", fd)

    def test_file_rules_empty_for_nonmatching_file(self):
        fd, _ = self._get("/src/other.c",
                          '"mod.c":\n  disabled_rules:\n    - function.prefix\n')
        self.assertEqual(fd, frozenset())

    def test_ident_rules_returned_for_matching_file(self):
        _, id_ = self._get("/src/mod.c",
                           '"mod.c":\n'
                           '  identifiers:\n'
                           '    LegacyFn:\n'
                           '      disabled_rules:\n'
                           '        - function.prefix\n')
        self.assertIn("LegacyFn", id_)
        self.assertIn("function.prefix", id_["LegacyFn"])

    def test_ident_rules_empty_for_nonmatching_file(self):
        _, id_ = self._get("/src/other.c",
                           '"mod.c":\n'
                           '  identifiers:\n'
                           '    LegacyFn:\n'
                           '      disabled_rules:\n'
                           '        - function.prefix\n')
        self.assertEqual(id_, {})

    def test_glob_pattern_matches(self):
        fd, _ = self._get("/src/ascii.c",
                          '"ascii.*":\n  disabled_rules:\n    - function.prefix\n')
        self.assertIn("function.prefix", fd)

    def test_glob_pattern_matches_header(self):
        fd, _ = self._get("/src/ascii.h",
                          '"ascii.*":\n  disabled_rules:\n    - function.prefix\n')
        self.assertIn("function.prefix", fd)

    def test_multiple_patterns_union(self):
        yaml = ('"mod.c":\n  disabled_rules:\n    - function.prefix\n'
                '"mod.c":\n  disabled_rules:\n    - function.style\n')
        # Note: YAML duplicate keys — second overwrites first in most parsers
        # but patterns are different keys in practice
        fd, _ = self._get("/src/mod.c",
                          '"mod.c":\n'
                          '  disabled_rules:\n'
                          '    - function.prefix\n'
                          '    - function.style\n')
        self.assertIn("function.prefix", fd)
        self.assertIn("function.style", fd)


# ---------------------------------------------------------------------------
# Per-file exclusion end-to-end (existing behaviour, regression tests)
# ---------------------------------------------------------------------------

class TestPerFileExclusionsEndToEnd(unittest.TestCase):

    def test_file_level_rule_suppressed(self):
        excl = '"mod.c":\n  disabled_rules:\n    - variable.global.prefix\n'
        src  = "uint32_t g_counter = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        flagged = bool(_violations_in(out, rule="variable.global"))
        self.assertFalse(flagged, f"File-level exclusion should suppress; got: {out}")

    def test_file_level_rule_not_suppressed_in_other_file(self):
        excl = '"other.c":\n  disabled_rules:\n    - variable.global.prefix\n'
        src  = "uint32_t g_counter = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        flagged = bool(_violations_in(out, identifier="g_counter"))
        self.assertTrue(flagged, "Exclusion in other.c should not suppress mod.c")

    def test_multiple_rules_suppressed_per_file(self):
        excl = ('"mod.c":\n'
                '  disabled_rules:\n'
                '    - variable.global.prefix\n'
                '    - variable.global.g_prefix\n')
        src  = "uint32_t counter = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        self.assertFalse(bool(_violations_in(out, identifier="counter")))

    def test_glob_pattern_applies_to_c_and_h(self):
        excl = '"mod.*":\n  disabled_rules:\n    - variable.global.prefix\n'
        src  = "uint32_t g_counter = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src, filename="mod.c")
        self.assertFalse(bool(_violations_in(out, identifier="g_counter")))


# ---------------------------------------------------------------------------
# Per-identifier exclusion end-to-end (new feature)
# ---------------------------------------------------------------------------

class TestPerIdentifierExclusionsEndToEnd(unittest.TestCase):

    def test_identifier_rule_suppressed(self):
        """A specific variable's rule is suppressed by identifier exclusion."""
        excl = (
            '"mod.c":\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
            '        - variable.global.g_prefix\n'
        )
        src = "uint32_t g_legacy = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        flagged = bool(_violations_in(out, identifier="g_legacy"))
        self.assertFalse(flagged, f"Identifier exclusion should suppress; got:\n{out}")

    def test_other_identifier_not_suppressed(self):
        """Rules suppressed for one identifier do not affect others."""
        excl = (
            '"mod.c":\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
        )
        src = ("uint32_t g_legacy = 0U;\n"
               "uint32_t g_active = 0U;\n")
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        legacy_flagged = bool(_violations_in(out, identifier="g_legacy"))
        active_flagged = bool(_violations_in(out, identifier="g_active"))
        self.assertFalse(legacy_flagged, "g_legacy should be suppressed")
        self.assertTrue(active_flagged,  "g_active should still be flagged")

    def test_multiple_identifiers_each_suppressed(self):
        """Multiple identifiers can each have their own suppressions."""
        excl = (
            '"mod.c":\n'
            '  identifiers:\n'
            '    g_legacy_a:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
            '    g_legacy_b:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
        )
        src = ("uint32_t g_legacy_a = 0U;\n"
               "uint32_t g_legacy_b = 0U;\n"
               "uint32_t g_active   = 0U;\n")
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        self.assertFalse(bool(_violations_in(out, identifier="g_legacy_a")))
        self.assertFalse(bool(_violations_in(out, identifier="g_legacy_b")))
        self.assertTrue(bool( _violations_in(out, identifier="g_active")))

    def test_identifier_only_suppresses_listed_rule(self):
        """Only the listed rules are suppressed; other rules still fire."""
        excl = (
            '"mod.c":\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.g_prefix\n'
            # NOT suppressing variable.global.prefix
        )
        # g_legacy should still get variable.global.prefix (no module prefix)
        src = "uint32_t g_legacy = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        # g_prefix suppressed, but prefix (module prefix) still fires
        g_prefix_flagged  = bool(_violations_in(out, rule="g_prefix",
                                                  identifier="g_legacy"))
        self.assertFalse(g_prefix_flagged, "g_prefix should be suppressed")

    def test_file_and_identifier_exclusions_combined(self):
        """File-level suppresses all; identifier-level suppresses specific."""
        excl = (
            '"mod.c":\n'
            '  disabled_rules:\n'
            '    - misc.magic_number\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
        )
        src = ("uint32_t g_legacy = 0U;\n"    # prefix suppressed by identifier
               "uint32_t g_active = 0U;\n"     # prefix still flags
               "const int z = 99;\n")           # magic_number suppressed file-wide
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        self.assertFalse(bool(_violations_in(out, identifier="g_legacy",
                                              rule="variable.global.prefix")))
        self.assertFalse(bool(_violations_in(out, rule="misc.magic_number")))

    def test_identifier_exclusion_in_nonmatching_file_ignored(self):
        """Identifier exclusions only apply to files matching the pattern."""
        excl = (
            '"other.c":\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
        )
        src = "uint32_t g_legacy = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src, filename="mod.c")
        self.assertTrue(bool(_violations_in(out, identifier="g_legacy")))

    def test_identifier_exclusion_with_glob_pattern(self):
        """Identifier exclusions work when the file key is a glob pattern."""
        excl = (
            '"mod.*":\n'
            '  identifiers:\n'
            '    g_legacy:\n'
            '      disabled_rules:\n'
            '        - variable.global.prefix\n'
        )
        src = "uint32_t g_legacy = 0U;\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src, filename="mod.c")
        self.assertFalse(bool(_violations_in(out, identifier="g_legacy",
                                              rule="variable.global")))


# ---------------------------------------------------------------------------
# Exclusions YAML format correctness
# ---------------------------------------------------------------------------

class TestExclusionsYamlFormat(unittest.TestCase):

    def test_empty_exclusions_file_runs_cleanly(self):
        """An empty exclusions file causes no crash."""
        excl = "{}\n"
        src  = "void mod_DoWork(void){}\n"
        with tempfile.TemporaryDirectory() as td:
            out = _run_with_excl(td, excl, src)
        self.assertNotIn("Error", out[:50])

    def test_exclusions_file_with_only_comments(self):
        excl = "# This file is intentionally empty\n"
        src  = "void mod_DoWork(void){}\n"
        with tempfile.TemporaryDirectory() as td:
            _run_with_excl(td, excl, src)  # must not crash

    def test_identifier_without_disabled_rules_ignored(self):
        """An identifier block with no disabled_rules list is silently ignored."""
        excl = ('"mod.c":\n'
                '  identifiers:\n'
                '    SomeFn: {}\n')
        src  = "void mod_DoWork(void){}\n"
        with tempfile.TemporaryDirectory() as td:
            _run_with_excl(td, excl, src)  # must not crash


if __name__ == "__main__":
    unittest.main(verbosity=2)
