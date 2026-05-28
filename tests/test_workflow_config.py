"""test_workflow_config.py — structural tests for CI workflow configuration.

These tests verify critical workflow properties that cannot be exercised by
running the checker itself.  They guard against accidental removal of safety
or correctness settings during future YAML edits.
"""
import unittest
from pathlib import Path

_REPO_ROOT        = Path(__file__).resolve().parent.parent
_WORKFLOWS_DIR    = _REPO_ROOT / ".github" / "workflows"
_WORKFLOW_RULES   = _WORKFLOWS_DIR / "cstylecheck_rules.yml"
_WORKFLOW_TESTS   = _WORKFLOWS_DIR / "cstylecheck_tests.yml"
_WORKFLOW_DOCKER  = _WORKFLOWS_DIR / "docker_publish.yml"
_WORKFLOW_WIKI    = _WORKFLOWS_DIR / "wiki_publish.yml"

# Back-compat alias used by existing TestConcurrencyControl
_WORKFLOW = _WORKFLOW_RULES


def _load_yaml(path=None):
    try:
        import yaml
    except ImportError:
        return None
    return yaml.safe_load((path or _WORKFLOW_RULES).read_text(encoding="utf-8"))


def _checkout_steps(wf_dict):
    """Return all checkout step dicts found anywhere in a parsed workflow."""
    import re
    steps = []
    for job in (wf_dict or {}).get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "") or ""
            if re.match(r"actions/checkout@", uses):
                steps.append(step)
    return steps


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


class TestCheckoutToken(unittest.TestCase):
    """SUP9-TC-CHKOUT-001 to 008 — issue #55 regression suite.

    Verifies that every actions/checkout step in all three affected workflows
    carries an explicit token so checkout@v6 credential changes cannot cause
    silent authentication failures.
    """

    def _assert_all_have_token(self, path):
        wf = _load_yaml(path)
        if wf is None:
            self.skipTest("PyYAML not available")
        steps = _checkout_steps(wf)
        self.assertTrue(steps, f"No checkout steps found in {path.name}")
        for step in steps:
            token = (step.get("with") or {}).get("token", "")
            self.assertTrue(
                token,
                f"Checkout step in {path.name} is missing explicit token: {step}",
            )

    # SUP9-TC-CHKOUT-001
    def test_rules_workflow_all_checkouts_have_token(self):
        """Every checkout in cstylecheck_rules.yml must have an explicit token."""
        self._assert_all_have_token(_WORKFLOW_RULES)

    # SUP9-TC-CHKOUT-002
    def test_tests_workflow_all_checkouts_have_token(self):
        """Every checkout in cstylecheck_tests.yml must have an explicit token."""
        self._assert_all_have_token(_WORKFLOW_TESTS)

    # SUP9-TC-CHKOUT-003
    def test_docker_workflow_all_checkouts_have_token(self):
        """Every checkout in docker_publish.yml must have an explicit token."""
        self._assert_all_have_token(_WORKFLOW_DOCKER)

    # SUP9-TC-CHKOUT-004
    def test_wiki_workflow_all_checkouts_have_token(self):
        """Every checkout in wiki_publish.yml must have an explicit token."""
        self._assert_all_have_token(_WORKFLOW_WIKI)

    # SUP9-TC-CHKOUT-005 — spot-check token value format
    def test_token_references_github_token_secret(self):
        """Token value must reference secrets.GITHUB_TOKEN (not a hardcoded value)."""
        for path in (_WORKFLOW_RULES, _WORKFLOW_TESTS, _WORKFLOW_DOCKER, _WORKFLOW_WIKI):
            wf = _load_yaml(path)
            if wf is None:
                self.skipTest("PyYAML not available")
            for step in _checkout_steps(wf):
                token = (step.get("with") or {}).get("token", "")
                self.assertIn(
                    "secrets.GITHUB_TOKEN", token,
                    f"Token in {path.name} does not reference secrets.GITHUB_TOKEN: {token!r}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
