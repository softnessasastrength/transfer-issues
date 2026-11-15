"""Crostini CLI safety and command-contract tests; no hardware required."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "crostini-dev.sh"


class CrostiniDevTests(unittest.TestCase):
    def test_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_help(self):
        result = subprocess.run(["bash", str(SCRIPT), "help"], cwd=ROOT,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        for command in ("doctor", "test", "serve", "packs", "android-build", "adb-devices"):
            self.assertIn(command, result.stdout)

    def test_unknown_command_fails(self):
        result = subprocess.run(["bash", str(SCRIPT), "unrecognized"], cwd=ROOT,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)

    def test_no_automatic_network_exposure_or_package_installation(self):
        source = SCRIPT.read_text()
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("sudo apt install", source.replace('echo "Install adb: sudo apt install adb"', ""))
        self.assertNotIn("adb pair ", source)
        self.assertNotIn("adb connect ", source)
        self.assertNotIn("git pull", source)


if __name__ == "__main__":
    unittest.main()
