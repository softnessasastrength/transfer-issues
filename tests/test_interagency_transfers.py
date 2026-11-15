"""Synthetic cross-agency transfer and journey tests. No live feeds."""
import unittest
from unittest.mock import patch
from transfer_edges import edges
import routing


def stop(id, feed, lat, lon, parent=None):
    return {"id": id, "feed": feed, "lat": lat, "lon": lon, "parent": parent}


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.stops = {
            "ct:a": stop("ct:a", "cttransit", 41.760, -72.680),
            "rail:b": stop("rail:b", "hartford", 41.7603, -72.680),
            "amtrak:c": stop("amtrak:c", "amtrak", 41.7606, -72.680),
            "far:d": stop("far:d", "pvta", 42.0, -72.680),
        }

    def test_cross_agency_proximity_is_estimated(self):
        e = edges(self.stops, [], radius=150)
        link = next(x for x in e["ct:a"] if x["to"] == "rail:b")
        self.assertEqual(link["source"], "proximity")
        self.assertTrue(link["estimated"])
        self.assertGreaterEqual(link["seconds"], 60)
        self.assertNotIn("far:d", [x["to"] for x in e["ct:a"]])

    def test_forbidden_overrides_proximity(self):
        e = edges(self.stops, [{"a": "ct:a", "b": "rail:b", "type": 3, "seconds": 0}], radius=150)
        self.assertNotIn("rail:b", [x["to"] for x in e["ct:a"]])
        self.assertIn("ct:a", [x["to"] for x in e["rail:b"]])  # directed rule

    def test_official_minimum_transfer_time(self):
        e = edges(self.stops, [{"a": "ct:a", "b": "rail:b", "type": 2, "seconds": 420}], radius=150)
        link = next(x for x in e["ct:a"] if x["to"] == "rail:b")
        self.assertEqual(link["source"], "official")
        self.assertGreaterEqual(link["seconds"], 420)

    def test_parent_station_rule_expands(self):
        s = dict(self.stops)
        s["station"] = stop("station", "hartford", 41.760, -72.680)
        s["rail:b"]["parent"] = "station"
        e = edges(s, [{"a": "ct:a", "b": "station", "type": 3, "seconds": 0}], radius=150)
        self.assertNotIn("rail:b", [x["to"] for x in e["ct:a"]])

    def test_radius_zero_disables_estimated_proximity(self):
        e = edges(self.stops, [], radius=0)
        self.assertFalse(e["ct:a"])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            edges(self.stops, [], mode="teleport")

    def test_scan_walk_then_board_with_buffer(self):
        # Buffer doctrine (DECISIONS.md, 2026-11-15): the transfer buffer
        # never applies to first-mile walking — a local CT stop walks to
        # the Hartford Line station and boards there ready at its walk
        # arrival, however large the buffer. The buffer applies in full
        # at a genuine transfer: after alighting, the next boarding waits
        # arrival + buffer.
        stops = dict(self.stops)
        stops["beyond:e"] = stop("beyond:e", "pvta", 42.5, -72.680)
        connections = [(600, 900, "rail:b", "far:d", "service|rail:trip",
                        "hartford:r", "Outbound", 0, 0, 1),
                       (960, 1200, "far:d", "beyond:e", "service|rail:trip2",
                        "hartford:r", "Outbound", 0, 0, 1)]
        def fake_query(sql):
            if "FROM stops" in sql:
                return list(stops.values())
            if "FROM transfers" in sql:
                return []
            raise AssertionError(sql)
        routing.network.cache_clear()
        routing.transfer_graph.cache_clear()
        routing.neighbors.cache_clear()
        with patch.object(routing, "query", side_effect=fake_query), \
             patch.object(routing, "connections", return_value=connections):
            # First-mile half: even an excessive buffer cannot block the
            # boarding after the walk from the origin.
            arrivals, paths = routing.scan("2026-11-12", "ct:a", 0, 1200, radius=150, buffer=700)
            self.assertEqual(arrivals["far:d"], 900)
            self.assertEqual(paths["far:d"][-1]["kind"], "transit")
            self.assertEqual(paths["rail:b"][0]["transfer_source"], "proximity")
            # Transfer half: alighting at far:d at 900, the onward trip
            # departs 960. A 180 s buffer makes ready 1080 — too late.
            arrivals, _ = routing.scan("2026-11-12", "ct:a", 0, 1200, radius=150, buffer=180)
            self.assertEqual(arrivals["far:d"], 900)
            self.assertNotIn("beyond:e", arrivals)
            # A 30 s buffer makes ready 930 — the transfer succeeds.
            arrivals, paths = routing.scan("2026-11-12", "ct:a", 0, 1200, radius=150, buffer=30)
            self.assertEqual(arrivals["beyond:e"], 1200)
            self.assertEqual(paths["beyond:e"][-1]["kind"], "transit")
        routing.network.cache_clear()
        routing.transfer_graph.cache_clear()
        routing.neighbors.cache_clear()


if __name__ == "__main__":
    unittest.main()
