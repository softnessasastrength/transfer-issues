"""Synthetic Mobility Bubble tests; fixture data only, not real service."""
import unittest
from unittest.mock import patch
import bubble, routing, server


class BubbleFixture(unittest.TestCase):
    """Network: home -a- b by rail with a return; c outbound-only; d isolated;
    w walk-only; pvta:z belongs to a feed that is not loaded."""

    def setUp(self):
        self.stops = {k: dict(id=k, name=k, lat=42., lon=-72., parent='')
                      for k in ['test:home', 'test:a', 'test:b', 'test:c',
                                'test:d', 'test:w', 'pvta:z']}
        self.conns = [
            (600, 900, 'test:home', 'test:a', 't1', 'test:rail', 'Out', 0, 0, 0),
            (900, 1200, 'test:a', 'test:b', 't1', 'test:rail', 'Out', 0, 0, 1),
            (1500, 1800, 'test:b', 'test:a', 't2', 'test:rail', 'Back', 0, 0, 0),
            (1800, 2100, 'test:a', 'test:home', 't2', 'test:rail', 'Back', 0, 0, 1),
            (3000, 3300, 'test:home', 'test:c', 't3', 'test:rail', 'Out', 0, 0, 0),
        ]
        walks = {'test:home': [('test:w', 600, 700)],
                 'test:w': [('test:home', 600, 700)]}
        patches = [
            patch.object(routing, 'network',
                         return_value=(self.stops, {}, {})),
            patch.object(routing, 'connections', return_value=self.conns),
            patch.object(routing, 'neighbors',
                         side_effect=lambda s, r, m: walks.get(s, [])),
            patch.object(routing, 'transfer_graph',
                         return_value={s: [dict(to=t, seconds=sec, meters=m,
                                                 source='synthetic')
                                            for t, sec, m in edges]
                                       for s, edges in walks.items()}),
            patch.object(routing, 'coverage', return_value=[]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.coverage = [dict(feed='test', status='imported',
                              in_service_period=True, start='20260101',
                              end='20261231'),
                         dict(feed='pvta', status='not_downloaded',
                              in_service_period=False, start=None, end=None)]
        self.sources = [dict(id='test', status='imported',
                             retrieved_at='2026-11-14T00:00:00+00:00',
                             service_start='20260101', service_end='20261231',
                             sha256='fixture'),
                        dict(id='pvta', status='not_downloaded',
                             refresh_error='HTTP Error 403: Forbidden')]

    def classify(self, **kw):
        kw.setdefault('coverage_rows', self.coverage)
        kw.setdefault('source_rows', self.sources)
        kw.setdefault('buffer', 60)
        return bubble.classify('2026-11-17', 'test:home', 0, budget=3600, **kw)

    def test_round_trip_stops_reachable(self):
        r = self.classify()
        ids = {s['id'] for s in r['reachable']}
        self.assertIn('test:a', ids)
        self.assertIn('test:b', ids)
        b = next(s for s in r['reachable'] if s['id'] == 'test:b')
        self.assertEqual(b['arrival'], 1200)
        self.assertEqual(b['latest_return_departure'], 1500)
        self.assertTrue(b['legs'])

    def test_origin_itself_reachable(self):
        r = self.classify()
        self.assertIn('test:home', {s['id'] for s in r['reachable']})

    def test_outbound_only_is_unreachable_with_reason(self):
        r = self.classify()
        self.assertNotIn('test:c', {s['id'] for s in r['reachable']})
        self.assertEqual(r['unreachable_reasons']['no_feasible_return'], 1)

    def test_no_outbound_is_unreachable_with_reason(self):
        r = self.classify()
        self.assertNotIn('test:d', {s['id'] for s in r['reachable']})
        self.assertEqual(
            r['unreachable_reasons']['no_outbound_within_budget'], 1)

    def test_missing_feed_is_unknown_never_unreachable(self):
        r = self.classify()
        self.assertEqual(r['unknown']['stop_count'], 1)
        self.assertEqual([f['feed'] for f in r['unknown']['feeds']], ['pvta'])
        self.assertIn('403', r['unknown']['feeds'][0]['reason'])
        self.assertEqual(r['unreachable_count'], 2)  # only c and d

    def test_walk_out_and_back_reachable(self):
        r = self.classify()
        w = next(s for s in r['reachable'] if s['id'] == 'test:w')
        self.assertEqual(w['arrival'], 600)
        self.assertEqual(w['latest_return_departure'], 3000)

    def test_visit_consumes_budget(self):
        r = self.classify(visit=400)
        ids = {s['id'] for s in r['reachable']}
        self.assertIn('test:a', ids)       # ready 1300 <= last return 1800
        self.assertNotIn('test:b', ids)    # ready 1600 > last return 1500

    def test_evidence_and_freshness_exposed(self):
        r = self.classify()
        src = {s['feed']: s for s in r['sources']}
        self.assertEqual(src['test']['sha256'], 'fixture')
        self.assertEqual(src['test']['service_end'], '20261231')
        self.assertIn('Not live service', r['status'])

    def test_reverse_scan_matches_brute_force_plan(self):
        best = bubble.latest_return_departures('2026-11-17', 'test:home',
                                               3600, buffer=60)
        for sid, latest in [('test:a', 1800), ('test:b', 1500)]:
            self.assertEqual(best[sid], latest)
            plan = routing.plan('2026-11-17', sid, 'test:home', latest, 3600,
                                buffer=60)
            self.assertTrue(plan['found'], sid)
        self.assertNotIn('test:c', best)

    def test_unknown_origin_rejected(self):
        with self.assertRaises(ValueError):
            bubble.classify('2026-11-17', 'test:nope', 0,
                            coverage_rows=[], source_rows=[])


class BubbleHttpTests(unittest.TestCase):
    def test_bubble_endpoint_contract(self):
        fx = BubbleFixture('test_round_trip_stops_reachable')
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        with patch.object(server.db, 'coverage', return_value=fx.coverage), \
                patch.object(server.db, 'sources', return_value=fx.sources):
            r = server.handle('/api/v1/bubble',
                              {'from': ['test:home'], 'date': ['2026-11-17'],
                               'time': ['0'], 'budget': ['3600'],
                               'buffer': ['1']})
        self.assertEqual(r['budget'], 3600)
        self.assertIn('test:b', {s['id'] for s in r['reachable']})
        self.assertEqual(r['unknown']['stop_count'], 1)

    def test_bubble_budget_validation(self):
        with self.assertRaises(ValueError):
            server.handle('/api/v1/bubble',
                          {'from': ['test:home'], 'budget': ['30']})


class FirstMileReturnShapeFixture(unittest.TestCase):
    """RT-3 regression: walk -> transit -> walk -> transit outbound where
    the first boarding is only catchable because first-mile walking from
    the origin carries no transfer buffer (ready == arrival at the
    walk-reached stop). With the buffer wrongly applied there, the scan
    boards a later first trip, reaches the destination after its last
    feasible return has left, and the bubble reports no_feasible_return
    for a stop that does have a way back."""

    def setUp(self):
        self.stops = {k: dict(id=k, name=k, lat=42., lon=-72., parent='')
                      for k in ['test:home', 'test:p', 'test:q', 'test:r',
                                'test:dest']}
        self.conns = [
            # First trip is catchable only with ready == arrival at p
            # (walk 120s, departure 150s, buffer 60s).
            (150, 450, 'test:p', 'test:q', 't1a', 'test:bus', 'Out', 0, 0, 0),
            (1200, 1500, 'test:p', 'test:q', 't1b', 'test:bus', 'Out', 0, 0, 0),
            (700, 1000, 'test:r', 'test:dest', 't2a', 'test:bus', 'Out', 0, 0, 0),
            (1800, 2100, 'test:r', 'test:dest', 't2b', 'test:bus', 'Out', 0, 0, 0),
            (1500, 1800, 'test:dest', 'test:r', 't3', 'test:bus', 'Back', 0, 0, 0),
            (2000, 2300, 'test:q', 'test:p', 't4', 'test:bus', 'Back', 0, 0, 0),
        ]
        walks = {'test:home': [('test:p', 120, 130)],
                 'test:p': [('test:home', 120, 130)],
                 'test:q': [('test:r', 120, 130)],
                 'test:r': [('test:q', 120, 130)]}
        patches = [
            patch.object(routing, 'network',
                         return_value=(self.stops, {}, {})),
            patch.object(routing, 'connections', return_value=self.conns),
            patch.object(routing, 'neighbors',
                         side_effect=lambda s, r, m: walks.get(s, [])),
            patch.object(routing, 'transfer_graph',
                         return_value={s: [dict(to=t, seconds=sec, meters=m,
                                                 source='synthetic')
                                            for t, sec, m in edges]
                                       for s, edges in walks.items()}),
            patch.object(routing, 'coverage', return_value=[]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.coverage = [dict(feed='test', status='imported',
                              in_service_period=True, start='20260101',
                              end='20261231')]
        self.sources = [dict(id='test', status='imported',
                             retrieved_at='2026-11-15T00:00:00+00:00',
                             service_start='20260101', service_end='20261231',
                             sha256='fixture')]

    def test_first_mile_walk_ready_without_buffer(self):
        arrivals, paths = routing.scan('2026-11-17', 'test:home', 0, 3600,
                                       buffer=60)
        self.assertEqual(arrivals['test:dest'], 1000)
        self.assertEqual([leg['kind'] for leg in paths['test:dest']],
                         ['walk', 'transit', 'walk', 'transit'])

    def test_destination_reachable_with_return(self):
        r = bubble.classify('2026-11-17', 'test:home', 0, budget=3600,
                            buffer=60, coverage_rows=self.coverage,
                            source_rows=self.sources)
        dest = next((s for s in r['reachable'] if s['id'] == 'test:dest'),
                    None)
        self.assertIsNotNone(dest)
        self.assertEqual(dest['arrival'], 1000)
        self.assertEqual(dest['latest_return_departure'], 1500)
        self.assertEqual(r['unreachable_reasons']['no_feasible_return'], 0)


if __name__ == '__main__':
    unittest.main()
