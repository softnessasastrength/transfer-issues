"""Static regression checks for the development CI workflow (no PyYAML dependency)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-ci.yml"


class CiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_jobs_and_artifact_present(self):
        for required in (
            "pull_request:", "workflow_dispatch:", "python-tests:",
            "android-debug:", ":app:testDebugUnitTest", ":app:assembleDebug",
            "actions/upload-artifact@v4", "android/app/build/outputs/apk/debug/*.apk",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.workflow)

    def test_no_release_or_write_permissions(self):
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)
        self.assertNotIn("push:", self.workflow)
        self.assertNotIn("release:", self.workflow)

    def test_android_project_exists_on_feature_base(self):
        self.assertTrue((ROOT / "android" / "app" / "build.gradle.kts").is_file())
        self.assertTrue((ROOT / "android" / "gradle" / "wrapper" / "gradle-wrapper.properties").is_file())


if __name__ == "__main__":
    unittest.main()
