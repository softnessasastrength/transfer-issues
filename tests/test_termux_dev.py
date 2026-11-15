"""Synthetic safety contract tests for optional Termux developer tooling."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "termux-dev.sh"


class TermuxDevTests(unittest.TestCase):
    def test_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_help_has_no_side_effects(self):
        result = subprocess.run(["bash", str(SCRIPT), "help"], capture_output=True,
                                text=True, cwd=ROOT, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("adb-devices", result.stdout)

    def test_unknown_command_fails(self):
        result = subprocess.run(["bash", str(SCRIPT), "oops"], capture_output=True,
                                text=True, cwd=ROOT, timeout=10)
        self.assertEqual(result.returncode, 2)

    def test_no_implicit_pairing_or_log_persistence(self):
        content = SCRIPT.read_text()
        self.assertNotIn("adb pair ", content)
        self.assertNotIn("adb connect ", content)
        self.assertNotIn("logcat -d", content)
        self.assertNotIn(" > ", content)


if __name__ == "__main__":
    unittest.main()
