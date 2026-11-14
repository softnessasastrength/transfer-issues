"""Read-only inspection guards against filesystem escape and terminal controls."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from developer_center.inspection import environment, git_inspection, log_preview, logs


class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_log_traversal_rejected(self):
        for name in ('../secret.log', '/tmp/secret.log', 'data.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                log_preview(self.root, name)

    def test_symlinks_and_special_files_are_not_read(self):
        (self.root / 'source').write_text('private')
        (self.root / 'linked.log').symlink_to(self.root / 'source')
        os.mkfifo(self.root / 'pipe.log')
        self.assertEqual(logs(self.root), [])
        for name in ('linked.log', 'pipe.log'):
            self.assertEqual(log_preview(self.root, name)['status'], 'unavailable')

    def test_tail_is_bounded_and_controls_are_inert(self):
        path = self.root / 'large.log'
        path.write_bytes(b'x' * 70000 + b'\n\x1b[31mERROR\x1b[0m\x00\n')
        original = path.read_bytes()
        preview = log_preview(self.root, path.name)
        self.assertTrue(preview['truncated'])
        self.assertLessEqual(len(preview['text']), 65536)
        self.assertNotIn('\x1b', preview['text'])
        self.assertNotIn('\x00', preview['text'])
        self.assertIn('ERROR', preview['text'])
        self.assertEqual(path.read_bytes(), original)

    def test_listing_is_newest_first_and_missing_log_is_visible(self):
        for name, timestamp in [('old.log', 10), ('new.log', 20)]:
            path = self.root / name
            path.write_text(name)
            os.utime(path, (timestamp, timestamp))
        self.assertEqual([r['name'] for r in logs(self.root)], ['new.log', 'old.log'])
        self.assertEqual(log_preview(self.root, 'missing.log')['status'], 'unavailable')

    def test_environment_distinguishes_configured_from_present(self):
        with patch.dict(os.environ, {'ANDROID_HOME': str(self.root), 'ANDROID_SDK_ROOT': ''}):
            result = environment(self.root)
            self.assertTrue(result['sdk_environment_configured'])
            self.assertFalse(result['android_35_platform_present'])
            platform = self.root / 'platforms/android-35/android.jar'
            platform.parent.mkdir(parents=True)
            platform.touch()
            self.assertTrue(environment(self.root)['android_35_platform_present'])

    def test_git_inspection_never_fetches_or_mutates(self):
        with patch('developer_center.inspection.git_value', return_value='fixture') as git:
            result = git_inspection(self.root)
        self.assertEqual(result['branch'], 'fixture')
        self.assertTrue(all(call.args[1] in ('branch', 'rev-parse', 'status', 'log') for call in git.call_args_list))
