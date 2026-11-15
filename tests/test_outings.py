"""Deterministic Percival Outings fixtures; not evidence of real service."""
import unittest
from unittest.mock import patch

import outings
import routing
import server


class OutingFixture(unittest.TestCase):
    def setUp(self):
        ids = ['test:home', 'test:valid', 'test:noreturn', 'test:short',
               'test:walk', 'test:near', 'test:alternate', 'test:overnight',
               'test:isolated', 'missing:place']
        self.stops = {sid: dict(id=sid, name=sid.split(':')[1].title(),
                                lat=42., lon=-72., parent='') for sid in ids}
        self.conns = sorted([
            self.c(100, 200, 'test:home', 'test:valid', 'out-valid'),
            self.c(100, 200, 'test:home', 'test:noreturn', 'out-no-return'),
            self.c(100, 200, 'test:home', 'test:short', 'out-short'),
            self.c(100, 200, 'test:home', 'test:walk', 'out-walk'),
            # First chronological option is slower and misses the return after
            # the minimum stay; the later express arrives earlier and works.
            self.c(100, 580, 'test:home', 'test:alternate', 'slow'),
            self.c(300, 500, 'test:home', 'test:alternate', 'express'),
            self.c(400, 500, 'test:short', 'test:home', 'back-too-soon'),
            self.c(700, 900, 'test:walk', 'test:near', 'back-to-walk'),
            self.c(850, 950, 'test:alternate', 'test:home', 'back-alt'),
            self.c(1000, 1100, 'test:valid', 'test:home', 'back-valid'),
            self.c(86500, 87000, 'test:home', 'test:overnight', 'night-out'),
            self.c(88000, 89000, 'test:overnight', 'test:home', 'night-back'),
        ], key=lambda row: (row[0], row[9]))
        self.coverage = [
            dict(feed='test', status='imported', in_service_period=True,
                 start='20260101', end='20261231'),
            dict(feed='missing', status='not_downloaded',
                 in_service_period=False, start=None, end=None),
        ]
        self.complete_coverage = self.coverage[:1]
        walks = {
            'test:home': [('test:near', 200, 250)],
            'test:near': [('test:home', 200, 250)],
        }
        patches = [
            patch.object(routing, 'network', return_value=(self.stops, {}, {})),
            patch.object(routing, 'connections', return_value=self.conns),
            patch.object(routing, 'neighbors', side_effect=lambda sid, radius, mode: walks.get(sid, [])),
            patch.object(routing, 'coverage', return_value=self.coverage),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def c(dep, arr, a, b, trip):
        return (dep, arr, a, b, trip, 'test:route', 'Fixture', 0, 0, 0)

    def evaluate(self, destination, start=0, home_by=1200, stay=300,
                 budget=600):
        return outings.evaluate(
            '2026-11-14', 'test:home', destination, start, home_by,
            minimum_stay=stay, outbound_budget=budget, radius=0, buffer=0,
            coverage_rows=self.coverage if destination.startswith('missing:') else self.complete_coverage)

    def test_valid_trip_has_both_itineraries_and_meeting_window(self):
        result = self.evaluate('test:valid')
        self.assertEqual(result['status'], 'verified')
        self.assertTrue(result['outbound']['found'])
        self.assertTrue(result['return_trip']['found'])
        self.assertEqual(result['meeting_window'],
                         {'start': 200, 'end': 1000, 'seconds': 800})
        self.assertEqual(result['home_arrival'], 1100)

    def test_outbound_reachable_without_return_is_ruled_out(self):
        result = self.evaluate('test:noreturn')
        self.assertEqual(result['status'], 'ruled_out')
        self.assertEqual(result['reason']['code'], 'no_usable_return')

    def test_return_before_minimum_stay_is_not_feasible(self):
        result = self.evaluate('test:short')
        self.assertEqual(result['status'], 'ruled_out')
        self.assertEqual(result['reason']['code'], 'insufficient_time_together')

    def test_home_by_includes_final_walk(self):
        too_tight = self.evaluate('test:walk', home_by=1099)
        self.assertEqual(too_tight['status'], 'ruled_out')
        self.assertEqual(too_tight['reason']['code'], 'no_usable_return')
        exact = self.evaluate('test:walk', home_by=1100)
        self.assertEqual(exact['status'], 'verified')
        self.assertEqual(exact['home_arrival'], 1100)
        self.assertEqual(exact['return_trip']['legs'][-1]['kind'], 'walk')

    def test_overnight_service_day_seconds_are_preserved(self):
        result = self.evaluate('test:overnight', start=86000,
                               home_by=90000, stay=600, budget=2000)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['outbound']['arrival'], 87000)
        self.assertEqual(result['home_arrival'], 89000)

    def test_missing_data_is_unknown_but_known_failure_is_ruled_out(self):
        unknown = self.evaluate('missing:place')
        self.assertEqual(unknown['status'], 'unknown')
        self.assertEqual(unknown['reason']['code'], 'feed_unavailable')
        known = self.evaluate('test:isolated')
        self.assertEqual(known['status'], 'ruled_out')
        self.assertEqual(known['reason']['code'], 'no_outbound_within_budget')

    def test_missing_third_party_feed_makes_failed_search_unknown(self):
        result = outings.evaluate('2026-11-14', 'test:home', 'test:isolated',
                                  0, 1200, minimum_stay=300,
                                  outbound_budget=600, radius=0, buffer=0,
                                  coverage_rows=self.coverage)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason']['code'], 'incomplete_coverage')

    def test_later_faster_outbound_changes_the_result(self):
        result = self.evaluate('test:alternate')
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['outbound']['legs'][0]['trip'], 'express')
        self.assertEqual(result['outbound']['arrival'], 500)

    def test_minute_rounding_never_shortens_the_required_stay(self):
        self.conns.extend([
            self.c(201, 301, 'test:home', 'test:isolated', 'out-second'),
            self.c(500, 600, 'test:isolated', 'test:home', 'too-early'),
            self.c(550, 650, 'test:isolated', 'test:home', 'valid-second'),
        ])
        self.conns.sort(key=lambda row: (row[0], row[9]))
        result = self.evaluate('test:isolated', stay=200, budget=600)
        self.assertEqual(result['status'], 'verified')
        self.assertGreaterEqual(result['latest_verified_return_departure'], 501)
        self.assertEqual(result['latest_verified_return_departure'], 550)

    def test_browse_reports_bounded_search_without_false_classification(self):
        result = outings.browse(
            '2026-11-14', 'test:home', 0, 1200, minimum_stay=300,
            outbound_budget=600, radius=0, buffer=0,
            coverage_rows=self.coverage, limit=2)
        self.assertFalse(result['search']['complete'])
        self.assertEqual(result['search']['evaluated'], 2)
        self.assertGreater(result['search']['unevaluated_count'], 0)


class OutingHttpTests(unittest.TestCase):
    def test_selected_outing_endpoint_contract(self):
        fixture = OutingFixture('test_valid_trip_has_both_itineraries_and_meeting_window')
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        with patch.object(server.db, 'coverage', return_value=fixture.coverage), \
                patch.object(server.db, 'sources', return_value=[{'id': 'test'}]):
            result = server.handle('/api/v1/outings', {
                'from': ['test:home'], 'to': ['test:valid'],
                'date': ['2026-11-14'], 'time': ['0'], 'home_by': ['1200'],
                'stay': ['300'], 'outbound_budget': ['600'],
                'radius': ['0'], 'buffer': ['0'],
            })
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['reason']['code'], 'scheduled_round_trip')

    def test_outings_requires_walking_mode(self):
        with self.assertRaisesRegex(ValueError, 'requires walking'):
            server.handle('/api/v1/outings', {'mode': ['scooter']})


if __name__ == '__main__':
    unittest.main()
