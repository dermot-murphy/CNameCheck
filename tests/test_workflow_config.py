"""test_workflow_config.py — structural tests for CI workflow configuration.

These tests verify critical workflow properties that cannot be exercised by
running the checker itself.  They guard against accidental removal of safety
or correctness settings during future YAML edits.
"""
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
