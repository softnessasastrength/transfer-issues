"""Historical evidence must not silently become a current-tree success claim."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from developer_center.adapters import snapshot
from developer_center.reports import apk_metadata, junit_results, python_result


class DeveloperReportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def log(self, text):
        path = self.root / 'run.log'
        path.write_text(text)
        return path

    def test_nonzero_exit_overrides_passing_text(self):
        result = python_result(self.log('Ran 3 tests in 0.1s\nOK\n'), {'exit_code': 1})
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['current_tree_verified'])

    def test_latest_summary_overrides_earlier_success(self):
        result = python_result(self.log('Ran 3 tests in 0.1s\nOK\nRan 4 tests in 0.2s\nFAILED (errors=1)\n'), {'exit_code': 0})
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['tests'], 4)

    def test_incomplete_or_empty_run_is_not_passed(self):
        for text in ('Ran 0 tests in 0.1s\nOK\n', 'Ran 3 tests in 0.1s\n'):
            with self.subTest(text=text):
                self.assertEqual(python_result(self.log(text), {'exit_code': 0})['status'], 'unknown')

    def test_passed_log_retains_provenance_and_age(self):
        path = self.log('Ran 12 tests in 0.1s\nOK (skipped=1)\n')
        os.utime(path, (100, 100))
        result = python_result(path, {'exit_code': 0, 'commit': 'abc', 'changes': 'dirty'})
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['commit'], 'abc')
        self.assertEqual(result['changes'], 'dirty')
        self.assertGreater(result['age_seconds'], 0)
        self.assertFalse(result['current_tree_verified'])

    def suite(self, name, tests=3, failures=0, errors=0, skipped=0):
        path = self.root / f'TEST-{name}.xml'
        path.write_text(f'<testsuite tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}"/>')
        return path

    def test_junit_aggregates_and_discloses_failure(self):
        self.suite('one', tests=4, failures=1)
        self.suite('two', tests=2, skipped=1)
        result = junit_results(self.root)
        self.assertEqual((result['tests'], result['failures'], result['skipped']), (6, 1, 1))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(result['reports']), 2)
        self.assertFalse(result['current_tree_verified'])

    def test_corruption_and_invalid_counts_prevent_green_aggregate(self):
        self.suite('valid')
        self.suite('negative', tests=-1)
        self.suite('inconsistent', tests=1, failures=2)
        (self.root / 'TEST-malformed.xml').write_text('<testsuite')
        result = junit_results(self.root)
        self.assertEqual(result['status'], 'invalid')
        self.assertEqual(len(result['issues']), 3)
        self.assertEqual(result['tests'], 3)

    def test_no_junit_reports_or_all_skipped_is_not_passed(self):
        self.assertEqual(junit_results(self.root)['status'], 'unavailable')
        self.suite('skipped', tests=3, skipped=3)
        self.assertEqual(junit_results(self.root)['status'], 'no-tests')

    def test_newest_missing_python_log_does_not_fall_back_to_old_success(self):
        output = self.root / 'history'
        output.mkdir()
        for name, timestamp in [('older', 100), ('newer', 200)]:
            record = output / f'{name}.json'
            record.write_text(json.dumps({'action': 'test', 'exit_code': 0}))
            os.utime(record, (timestamp, timestamp))
        (output / 'older.log').write_text('Ran 3 tests in 0.1s\nOK\n')
        result = snapshot(self.root, output)['test_results']['python']
        self.assertEqual(result['status'], 'unavailable')
        self.assertTrue(result['record_source'].endswith('newer.json'))

    def test_apk_metadata_requires_unique_matching_filename(self):
        apk = self.root / 'app.apk'
        metadata = self.root / 'output-metadata.json'
        self.assertEqual(apk_metadata(apk)['status'], 'unavailable')
        data = {'applicationId': 'example.test', 'variantName': 'debug',
                'elements': [{'outputFile': 'other.apk', 'versionCode': 1, 'versionName': '0.1'}]}
        metadata.write_text(json.dumps(data))
        self.assertEqual(apk_metadata(apk)['status'], 'invalid')
        data['elements'][0]['outputFile'] = apk.name
        metadata.write_text(json.dumps(data))
        result = apk_metadata(apk)
        self.assertEqual(result['application_id'], 'example.test')
        self.assertFalse(result['current_tree_verified'])
        data['elements'] *= 2
        metadata.write_text(json.dumps(data))
        self.assertEqual(apk_metadata(apk)['status'], 'invalid')
