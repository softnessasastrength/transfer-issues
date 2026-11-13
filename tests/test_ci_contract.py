"""Guard CI coverage and failure visibility for the portable developer workflows."""
import fnmatch
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/routing-verification.yml'


class CiContractTests(unittest.TestCase):
    def test_python_and_shell_changes_select_verification(self):
        source = WORKFLOW.read_text()
        path_block = source.split('    paths:\n', 1)[1].split('  workflow_dispatch:', 1)[0]
        patterns = re.findall(r"^      - '([^']+)'$", path_block, re.MULTILINE)
        for path in ('developer_center/reports.py', 'crostini-dev.sh', 'termux-atlas.sh',
                     'scripts/verify_lan_catalog.py', 'import_gtfs.py',
                     'offline_packages.py', 'tests/test_developer_reports.py',
                     'android/app/src/main/AndroidManifest.xml'):
            with self.subTest(path=path):
                self.assertTrue(any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns))

    def test_captured_test_failure_is_not_hidden_by_tee(self):
        source = WORKFLOW.read_text()
        test_step = source.split('      - name: Run synthetic regression tests\n', 1)[1].split('      - name:', 1)[0]
        self.assertIn('shell: bash', test_step)
        self.assertIn('set -o pipefail', test_step)
        self.assertIn('| tee build/ci/python-tests.log', test_step)
        self.assertNotIn('continue-on-error', source)
        self.assertNotIn('|| true', test_step)

    def test_failure_reports_retained_without_release_or_write_permission(self):
        source = WORKFLOW.read_text()
        for step in ('Upload Python test output', 'Upload Android JVM test results'):
            block = source.split(f'      - name: {step}\n', 1)[1].split('      - name:', 1)[0]
            self.assertIn('if: always()', block)
            self.assertIn('actions/upload-artifact@', block)
        self.assertIn('contents: read', source)
        self.assertNotIn('contents: write', source)
        self.assertNotIn('pull_request_target:', source)
        self.assertNotIn('gh release', source)
