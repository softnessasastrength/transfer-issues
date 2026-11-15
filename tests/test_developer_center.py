"""Deterministic developer adapter tests; no SDK or device required."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from developer_center.adapters import run_action, snapshot


class DeveloperCenterTests(unittest.TestCase):
    def test_unknown_action_cannot_execute_shell_or_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output'
            with self.assertRaises(KeyError):
                run_action('test; touch unexpected', output=output)
            self.assertFalse(output.exists())

    def test_launch_failure_is_recorded_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch('developer_center.adapters.subprocess.Popen', side_effect=FileNotFoundError('bash')):
                result = run_action('test', output=output)
            self.assertEqual(result.exit_code, 127)
            record = json.loads(next(output.glob('*.json')).read_text())
            self.assertEqual(record['exit_code'], 127)
            self.assertIn('Launch failed', Path(record['log']).read_text())
            self.assertEqual(list(output.glob('*.tmp')), [])

    def test_artifact_hash_and_corrupt_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'android/app/build/outputs/apk/debug/app-debug.apk'
            apk.parent.mkdir(parents=True)
            apk.write_bytes(b'synthetic APK')
            output = root / 'history'
            output.mkdir()
            (output / 'broken.json').write_text('{')
            state = snapshot(root, output)
            self.assertEqual(state['artifacts'][0]['sha256'], hashlib.sha256(apk.read_bytes()).hexdigest())
            self.assertIn('error', state['history'][0])

    def test_nonzero_child_result_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('developer_center.adapters.git_value', return_value='fixture'), \
                 patch('developer_center.adapters.subprocess.Popen') as process:
                process.return_value.wait.return_value = 7
                result = run_action('android-build', output=Path(directory))
            self.assertEqual(result.exit_code, 7)
            self.assertEqual(process.call_args.args[0], ('bash', 'crostini-dev.sh', 'android-build'))

    def test_interruption_reaps_child_and_records_130(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('developer_center.adapters.git_value', return_value='fixture'), \
                 patch('developer_center.adapters.subprocess.Popen') as process:
                process.return_value.wait.side_effect = [KeyboardInterrupt, -2]
                result = run_action('test', output=Path(directory))
            self.assertEqual(result.exit_code, 130)
            self.assertEqual(process.return_value.wait.call_count, 2)
            self.assertEqual(Path(result.log).stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(next(Path(directory).glob('*.json')).read_text())['commit'], 'fixture')
