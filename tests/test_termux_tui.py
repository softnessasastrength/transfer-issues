"""Pure smoke tests for Termux TUI command registry and headless mode."""
import subprocess
import sys
import unittest
from pathlib import Path
from scripts.termux_tui import ACTIONS, safe_command, status_snapshot

ROOT = Path(__file__).resolve().parents[1]


class TermuxTuiTests(unittest.TestCase):
    def test_commands_are_fixed_and_safe(self):
        self.assertEqual(len(ACTIONS), 7)
        self.assertEqual(safe_command("serve"), ["bash", "termux-atlas.sh", "serve"])
        with self.assertRaises(ValueError):
            safe_command("rm -rf /")

    def test_status_without_database(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            rows = dict(status_snapshot(Path(root)))
            self.assertEqual(rows["GTFS database"], "NOT PREPARED")

    def test_headless_list(self):
        result = subprocess.run([sys.executable, "scripts/termux_tui.py", "--list"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("serve", result.stdout)

    def test_headless_network_action_blocked(self):
        result = subprocess.run([sys.executable, "scripts/termux_tui.py", "--run", "prepare"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("confirmation", result.stderr)


if __name__ == "__main__":
    unittest.main()
