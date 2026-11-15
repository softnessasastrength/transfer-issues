"""Synthetic adversarial routing cases; no claim about published service."""
import unittest
from unittest.mock import patch

import routing


class RouteChainTests(unittest.TestCase):
    def setUp(self):
        stops = {sid: dict(id=sid, lat=42.0, lon=-72.0, parent='')
                 for sid in ('a', 'b', 'c')}
        for name, value in (('network', (stops, {}, {})),
                            ('neighbors', []),
                            ('coverage', [])):
            mocked = patch.object(routing, name, return_value=value)
            mocked.start()
            self.addCleanup(mocked.stop)

    @staticmethod
    def connection(dep, arr, a, b, trip, route):
        return (dep, arr, a, b, trip, route, 'Fixture', 0, 0, 0)

    def test_partial_chain_is_not_a_found_plan_or_reachable_stop(self):
        chain = ('test:A', 'test:B')
        rows = [self.connection(100, 200, 'a', 'c', 'partial', 'test:A')]
        with patch.object(routing, 'connections', return_value=rows):
            self.assertFalse(routing.plan('2026-11-17', 'a', 'c', 0, 500,
                                          route_chain=chain)['found'])
            arrivals, _ = routing.scan('2026-11-17', 'a', 0, 500,
                                       route_chain=chain)
        self.assertNotIn('c', arrivals)

    def test_later_complete_chain_survives_earlier_partial_arrival(self):
        chain = ('test:A', 'test:B')
        rows = [
            self.connection(100, 150, 'a', 'b', 'first', 'test:A'),
            self.connection(100, 200, 'a', 'c', 'partial', 'test:A'),
            self.connection(300, 400, 'b', 'c', 'second', 'test:B'),
        ]
        with patch.object(routing, 'connections', return_value=rows):
            plan = routing.plan('2026-11-17', 'a', 'c', 0, 500,
                                buffer=0, route_chain=chain)
        self.assertTrue(plan['found'])
        self.assertEqual(plan['arrival'], 400)
        self.assertEqual([leg['route'] for leg in plan['legs']], list(chain))


if __name__ == '__main__':
    unittest.main()
