"""Guards for the Peter Pan doctrine-exception feed registration.

Peter Pan is the one feed in the registry that is NOT an official
publisher feed: the official Trillium GTFS has been stale since
2024-12-31 and the carrier publishes no timetable documents, so the
owner granted an explicit, named exception on 2026-11-15 to import the
Peter Pan rows of the third-party UTEL-UIUC Intercity Bus GTFS,
labelled unofficial/stale wherever provenance surfaces, until a
current official feed replaces it (see DECISIONS.md).

These tests read only committed configuration — no live data, no
network — and pin the labelling so the exception cannot silently
decay into an unlabelled unofficial source.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import import_gtfs  # noqa: E402


class PeterPanFeedRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        cls.matches = [f for f in feeds if f['id'] == 'peterpan']
        cls.coverage = json.loads(
            (ROOT / 'config' / 'coverage.json').read_text())

    def test_registered_once_from_the_ibg_compilation(self):
        self.assertEqual(len(self.matches), 1)
        feed = self.matches[0]
        self.assertIn('UTEL-UIUC/intercity-bus-gtfs', feed['url'])
        self.assertIn('Merged_GTFS_Feed.zip', feed['url'])

    def test_labelled_unofficial_with_provenance_and_sunset(self):
        feed = self.matches[0]
        self.assertEqual(feed.get('source_status'), 'unofficial')
        provenance = feed.get('provenance', '')
        self.assertIn('UNOFFICIAL', provenance)
        self.assertIn('UTEL-UIUC', provenance)
        # The exception is named and dated, not implied.
        self.assertIn('2026-11-15', provenance)
        # The staleness of the official feed is stated, with its date.
        self.assertIn('2024-12-31', provenance)
        # The sunset condition: the official feed replaces this source.
        self.assertIn('SUNSET', provenance)

    def test_coverage_policy_selects_only_peter_pan_agencies(self):
        policy = self.coverage['feeds']['peterpan']
        # IBG agency ids: 40 = Peter Pan Bus Lines, 71 = Peter Pan (BZ).
        self.assertEqual(policy['agency_ids'], ['40', '71'])
        self.assertEqual(policy['route_types'], [3])
        self.assertTrue(policy['description'].startswith('UNOFFICIAL'))

    def test_importer_selection_applies_the_policy(self):
        # A Peter Pan route from the compilation is selected...
        self.assertTrue(import_gtfs.route_is_selected(
            'peterpan', {'agency_id': '40', 'route_type': '3'}))
        self.assertTrue(import_gtfs.route_is_selected(
            'peterpan', {'agency_id': '71', 'route_type': '3'}))
        # ...and every other operator sharing the IBG archive is not.
        self.assertFalse(import_gtfs.route_is_selected(
            'peterpan', {'agency_id': '1', 'route_type': '3'}))
        self.assertFalse(import_gtfs.route_is_selected(
            'peterpan', {'agency_id': '40', 'route_type': '2'}))

    def test_exception_recorded_in_decisions(self):
        decisions = (ROOT / 'DECISIONS.md').read_text()
        self.assertIn('Peter Pan', decisions)
        self.assertIn('doctrine exception', decisions)
        self.assertIn('Approve the third-party exception', decisions)


if __name__ == '__main__':
    unittest.main()
