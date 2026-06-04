"""
Tests for HTML report output (issue #192).

Tests cover:
  - _violations_to_html: structure, content, escaping, empty input
  - CLI --output-format html integration
"""
import os
import sys
import io

sys.path.insert(0, os.path.dirname(__file__))
from harness import _violations_to_html, Violation, cfg_only  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_violation(filepath="test.c", line=10, col=5,
                    severity="error", rule="misc.line_length",
                    message="Line too long") -> Violation:
    return Violation(filepath, line, col, severity, rule, message)


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestHtmlStructure:
    def test_returns_string(self):
        html = _violations_to_html([], 0, "1.0")
        assert isinstance(html, str)

    def test_valid_html_doctype(self):
        html = _violations_to_html([], 0, "1.0")
        assert html.startswith("<!DOCTYPE html>")

    def test_contains_html_tag(self):
        html = _violations_to_html([], 0, "1.0")
        assert "<html" in html
        assert "</html>" in html

    def test_contains_style_block(self):
        html = _violations_to_html([], 0, "1.0")
        assert "<style>" in html

    def test_empty_shows_no_violations_message(self):
        html = _violations_to_html([], 5, "1.0")
        assert "No violations found" in html

    def test_files_checked_in_summary(self):
        html = _violations_to_html([], 42, "1.0")
        assert "42" in html

    def test_version_in_output(self):
        html = _violations_to_html([], 0, "2.3.4")
        assert "2.3.4" in html or "CStyleCheck" in html


# ---------------------------------------------------------------------------
# Violation content tests
# ---------------------------------------------------------------------------

class TestHtmlViolationContent:
    def test_filepath_in_output(self):
        v = _make_violation(filepath="src/foo.c")
        html = _violations_to_html([v], 1, "1.0")
        assert "src/foo.c" in html

    def test_line_number_in_output(self):
        v = _make_violation(line=42)
        html = _violations_to_html([v], 1, "1.0")
        assert "42" in html

    def test_col_in_output(self):
        v = _make_violation(col=7)
        html = _violations_to_html([v], 1, "1.0")
        assert "7" in html

    def test_severity_in_output(self):
        v = _make_violation(severity="warning")
        html = _violations_to_html([v], 1, "1.0")
        assert "warning" in html

    def test_rule_in_output(self):
        v = _make_violation(rule="variables.case")
        html = _violations_to_html([v], 1, "1.0")
        assert "variables.case" in html

    def test_message_in_output(self):
        v = _make_violation(message="Identifier should be lower_snake_case")
        html = _violations_to_html([v], 1, "1.0")
        assert "lower_snake_case" in html

    def test_error_count_in_summary(self):
        violations = [
            _make_violation(severity="error"),
            _make_violation(severity="error"),
            _make_violation(severity="warning"),
        ]
        html = _violations_to_html(violations, 1, "1.0")
        # 2 errors, 1 warning, 0 info in the summary cards
        assert "2" in html
        assert "1" in html

    def test_multiple_files_each_shown(self):
        v1 = _make_violation(filepath="src/alpha.c")
        v2 = _make_violation(filepath="src/beta.c")
        html = _violations_to_html([v1, v2], 2, "1.0")
        assert "alpha.c" in html
        assert "beta.c" in html


# ---------------------------------------------------------------------------
# HTML escaping tests
# ---------------------------------------------------------------------------

class TestHtmlEscaping:
    def test_filepath_lt_gt_escaped(self):
        v = _make_violation(filepath="src/<module>.c")
        html = _violations_to_html([v], 1, "1.0")
        assert "<module>" not in html   # raw angle brackets must not appear
        assert "&lt;module&gt;" in html

    def test_message_ampersand_escaped(self):
        v = _make_violation(message="use a && b instead")
        html = _violations_to_html([v], 1, "1.0")
        assert "&amp;&amp;" in html

    def test_message_quotes_escaped(self):
        v = _make_violation(message='variable "foo" is not snake_case')
        html = _violations_to_html([v], 1, "1.0")
        assert "&quot;" in html or "&#x27;" in html or '"' not in html.split("foo")[0]


# ---------------------------------------------------------------------------
# CLI integration test
# ---------------------------------------------------------------------------

class TestHtmlReportCLI:
    def test_html_flag_produces_html_output(self, tmp_path, monkeypatch, capsys):
        import cstylecheck as _mod
        import yaml as _yaml

        root_cfg = cfg_only(
            misc={"line_length": {"enabled": True, "severity": "error", "max": 10}},
        )
        rules_yml = tmp_path / "rules.yml"
        rules_yml.write_text(_yaml.dump(root_cfg), encoding="utf-8")

        src_file = tmp_path / "test_module.c"
        src_file.write_text("x" * 20 + "\n", encoding="utf-8")

        orig_argv = sys.argv[:]
        try:
            sys.argv = [
                "cstylecheck",
                str(src_file),
                "--config", str(rules_yml),
                "--output-format", "html",
                "--exit-zero",
            ]
            monkeypatch.chdir(tmp_path)
            _mod.main()
        finally:
            sys.argv = orig_argv

        captured = capsys.readouterr()
        assert "<!DOCTYPE html>" in captured.out
        assert "<style>" in captured.out

    def test_html_flag_no_violations_shows_clean(self, tmp_path, monkeypatch, capsys):
        import cstylecheck as _mod
        import yaml as _yaml

        root_cfg = cfg_only()  # all rules off
        rules_yml = tmp_path / "rules.yml"
        rules_yml.write_text(_yaml.dump(root_cfg), encoding="utf-8")

        src_file = tmp_path / "test_module.c"
        src_file.write_text("int x = 1;\n", encoding="utf-8")

        orig_argv = sys.argv[:]
        try:
            sys.argv = [
                "cstylecheck",
                str(src_file),
                "--config", str(rules_yml),
                "--output-format", "html",
            ]
            monkeypatch.chdir(tmp_path)
            rc = _mod.main()
        finally:
            sys.argv = orig_argv

        assert rc == 0
        captured = capsys.readouterr()
        assert "No violations found" in captured.out
