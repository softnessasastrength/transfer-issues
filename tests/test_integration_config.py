"""Integration guards for the PR #71 merge.

The two branches edited the feed registry from different directions:
config/feeds.json is the registry scripts/prepare_data.py seeds
data/sources.json from (special-casing one feed's optional flag), and
config/coverage.json holds per-feed import overrides keyed by feed id.
These tests assert the three stay mutually consistent. They read only
committed configuration — no live data, no network — and check shape
only; they are not evidence of live transit correctness.
"""
import ast
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class FeedConfigIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        cls.coverage = json.loads(
            (ROOT / 'config' / 'coverage.json').read_text())
        cls.by_id = {f['id']: f for f in cls.feeds}

    def test_feed_ids_unique_with_registry_fields(self):
        self.assertEqual(len(self.feeds), len(self.by_id))
        for feed in self.feeds:
            self.assertTrue(feed['url'].startswith(('http://', 'https://')))
            self.assertIn('official_page', feed)
            self.assertIn('status', feed)
            if 'optional' in feed:
                self.assertIsInstance(feed['optional'], bool)

    def test_seat_feed_registered_from_agency_source(self):
        # SEAT (Southeast Area Transit District) was added 2026-11-15 at
        # the owner's direction after the CT cities sweep found Norwich
        # and Groton with no stops in the data. The registry entry must
        # point at the archive the agency's own GTFS page publishes (the
        # Remix-hosted zip the FTA NTD weblink lists for SEAT), with the
        # agency page recorded as the official page — not a mirror.
        self.assertIn('seat', self.by_id)
        seat = self.by_id['seat']
        self.assertEqual(seat['url'],
                         'https://gtfs.remix.com/seat_preston_ct_us.zip')
        self.assertEqual(
            seat['official_page'],
            'https://www.southeastareatransitdistrict.com/gtfs-feed/')

    def test_coverage_overrides_reference_real_feeds(self):
        for feed_id in self.coverage['feeds']:
            self.assertIn(feed_id, self.by_id)
        self.assertIn('bounds', self.coverage['default'])

    def test_prepare_data_special_cased_feed_exists_and_is_explicit(self):
        # prepare_data.py updates one feed's url/official_page/optional
        # from config on re-seed; that feed must exist in feeds.json and
        # carry an explicit optional flag, or the update silently no-ops.
        tree = ast.parse(
            (ROOT / 'scripts' / 'prepare_data.py').read_text())
        special = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            left = node.left
            if (isinstance(left, ast.Subscript)
                    and isinstance(left.slice, ast.Constant)
                    and left.slice.value == 'id'
                    and node.comparators
                    and isinstance(node.comparators[0], ast.Constant)
                    and isinstance(node.comparators[0].value, str)):
                special.add(node.comparators[0].value)
        self.assertTrue(special, 'no special-cased feed found in prepare_data.py')
        for feed_id in special:
            self.assertIn(feed_id, self.by_id)
            self.assertIn('optional', self.by_id[feed_id])


if __name__ == '__main__':
    unittest.main()
