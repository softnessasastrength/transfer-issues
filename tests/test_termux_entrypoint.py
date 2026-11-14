"""Static safety and CLI contract tests for phone-local Termux entrypoint."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "termux-atlas.sh"


class TermuxEntrypointTests(unittest.TestCase):
    def test_bash_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_unknown_command_fails_without_import_or_server(self):
        result = subprocess.run(["bash", str(SCRIPT), "not-a-command"], cwd=ROOT,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_loopback_only_and_no_implicit_downloads(self):
        source = SCRIPT.read_text()
        self.assertIn('HOST="127.0.0.1"', source)
        self.assertIn('case "${1:-serve}"', source)
        self.assertIn("prepare)", source)
        self.assertIn("serve)", source)
        self.assertIn("--host \"$HOST\"", source)
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("curl ", source)


if __name__ == "__main__":
    unittest.main()
