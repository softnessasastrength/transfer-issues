"""Static tests for the Android integration CI contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidIntegrationContractTests(unittest.TestCase):
    def test_ci_validates_integration_pushes_and_prs(self):
        workflow = (ROOT / ".github/workflows/pr-ci.yml").read_text()
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("branches: [integration/android]", workflow)
        self.assertIn(":app:testDebugUnitTest", workflow)
        self.assertIn(":app:assembleDebug", workflow)

    def test_ci_has_no_automatic_merge_or_release(self):
        workflow = (ROOT / ".github/workflows/pr-ci.yml").read_text()
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("deploy:", workflow)
        self.assertNotIn("release:", workflow)

    def test_policy_preserves_manual_gates(self):
        policy = (ROOT / "docs/architecture/android-integration-policy.md").read_text()
        for phrase in ("integration/android", "Human reviewer", "physical Android",
                       "Do not merge on CI alone", "main"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, policy)


if __name__ == "__main__":
    unittest.main()
