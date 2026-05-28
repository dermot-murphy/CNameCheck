"""test_workflow_config.py — structural tests for CI workflow configuration.

These tests verify critical workflow properties that cannot be exercised by
running the checker itself.  They guard against accidental removal of safety
or correctness settings during future YAML edits.
"""
import re
import unittest
from pathlib import Path

_REPO_ROOT   = Path(__file__).resolve().parent.parent
_WORKFLOW    = _REPO_ROOT / ".github" / "workflows" / "cstylecheck_rules.yml"


def _load_yaml():
    try:
        import yaml
    except ImportError:
        return None
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))


class TestConcurrencyControl(unittest.TestCase):
    """SUP9-TC-CONC-001 to 004 — issue #51 regression suite.

    Verifies that the workflow has a concurrency group so parallel pushes
    cannot race to corrupt trend.jsonl or cause a non-fast-forward gh-pages
    push failure.
    """

    def setUp(self):
        self._wf = _load_yaml()
        if self._wf is None:
            self.skipTest("PyYAML not available")

    # SUP9-TC-CONC-001
    def test_workflow_file_exists(self):
        """Workflow file must exist at the expected path."""
        self.assertTrue(_WORKFLOW.exists(), f"Missing: {_WORKFLOW}")

    # SUP9-TC-CONC-002
    def test_concurrency_key_present(self):
        """Top-level 'concurrency' key must be present."""
        self.assertIn("concurrency", self._wf,
                      "concurrency block missing from cstylecheck_rules.yml")

    # SUP9-TC-CONC-003
    def test_concurrency_group_set(self):
        """concurrency.group must be a non-empty string."""
        group = self._wf.get("concurrency", {}).get("group", "")
        self.assertTrue(group, "concurrency.group is empty or missing")
        self.assertIn("github.workflow", group)
        self.assertIn("github.ref", group)

    # SUP9-TC-CONC-004
    def test_cancel_in_progress_enabled(self):
        """cancel-in-progress must be True so the latest push wins."""
        conc = self._wf.get("concurrency", {})
        self.assertTrue(
            conc.get("cancel-in-progress", False),
            "cancel-in-progress is not True in concurrency block",
        )


class TestBadgePath(unittest.TestCase):
    """SUP9-TC-BADGE-001 to 005 — issue #42 regression suite.

    The original bug: the trend job wrote files to 'stylecheck/' while the
    README badge URL pointed to 'cstylecheck/'.  These tests pin the correct
    directory name throughout the workflow and README so the mismatch cannot
    silently recur.
    """

    def setUp(self):
        try:
            import yaml as _yaml
            self._yaml = _yaml
        except ImportError:
            self.skipTest("PyYAML not available")
        self._wf_text  = _WORKFLOW.read_text(encoding="utf-8")
        self._wf       = self._yaml.safe_load(self._wf_text)
        self._readme   = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")

    # SUP9-TC-BADGE-001
    def test_trend_directory_is_cstylecheck(self):
        """Workflow must use 'cstylecheck/' for trend data — not 'stylecheck/'."""
        self.assertIn("cstylecheck/trend.jsonl", self._wf_text,
                      "trend.jsonl path is not under cstylecheck/")
        # Use negative-lookbehind so we only match bare 'stylecheck/' and not
        # the correct 'cstylecheck/' (which contains 'stylecheck' as a suffix).
        self.assertIsNone(
            re.search(r"(?<!c)stylecheck/trend\.jsonl", self._wf_text),
            "Old 'stylecheck/' path still present in workflow",
        )

    # SUP9-TC-BADGE-002
    def test_badge_json_path_is_cstylecheck(self):
        """badge.json must be written to cstylecheck/ — not stylecheck/."""
        self.assertIn("cstylecheck/badge.json", self._wf_text,
                      "badge.json path is not under cstylecheck/")
        self.assertIsNone(
            re.search(r"(?<!c)stylecheck/badge\.json", self._wf_text),
            "Old 'stylecheck/' path still present in workflow",
        )

    # SUP9-TC-BADGE-003
    def test_index_html_path_is_cstylecheck(self):
        """index.html must be written to cstylecheck/ — not stylecheck/."""
        self.assertIn("cstylecheck/index.html", self._wf_text,
                      "index.html path is not under cstylecheck/")
        self.assertIsNone(
            re.search(r"(?<!c)stylecheck/index\.html", self._wf_text),
            "Old 'stylecheck/' path still present in workflow",
        )

    # SUP9-TC-BADGE-004
    def test_git_add_targets_cstylecheck(self):
        """'git add' in the trend commit step must target cstylecheck/."""
        self.assertIn("git add cstylecheck/", self._wf_text,
                      "'git add cstylecheck/' not found in workflow")
        self.assertNotIn("git add stylecheck/", self._wf_text,
                         "'git add stylecheck/' (wrong path) still present")

    # SUP9-TC-BADGE-005
    def test_readme_badge_url_points_to_cstylecheck(self):
        """README Naming Convention badge URL must reference cstylecheck/badge.json."""
        self.assertIn("cstylecheck/badge.json", self._readme,
                      "README badge URL does not reference cstylecheck/badge.json")
        self.assertIsNone(
            re.search(r"(?<!c)stylecheck/badge\.json", self._readme),
            "README badge URL references old stylecheck/ path",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
