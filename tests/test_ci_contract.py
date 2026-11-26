"""Guard CI coverage and failure visibility for the portable developer workflows."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/routing-verification.yml'


class CiContractTests(unittest.TestCase):
    def test_verification_runs_for_all_prs_and_merge_groups(self):
        source = WORKFLOW.read_text()
        triggers = source.split('on:\n', 1)[1].split('\n\n', 1)[0]
        self.assertRegex(triggers, r'(?m)^  pull_request:$')
        self.assertRegex(triggers, r'(?m)^  merge_group:\n    types: \[checks_requested\]$')
        self.assertRegex(triggers, r'(?m)^  push:\n    branches: \[main\]$')
        self.assertNotRegex(triggers, r'(?m)^\s+paths(?:-ignore)?:')

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
