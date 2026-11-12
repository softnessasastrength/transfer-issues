"""Golden cases shared verbatim with android JVM tests; no GTFS download or SQLite."""
import pathlib
import unittest
from unittest.mock import patch

import routing

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "routing_golden.psv"


def cases():
    for line in FIXTURES.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("|")
            assert len(fields) == 10, line
            yield fields


class GoldenParityPythonTests(unittest.TestCase):
    def test_shared_golden_cases(self):
        for name, origin, destination, start, deadline, buffer, raw_links, raw_transfers, expected, modes in cases():
            with self.subTest(name=name):
                stops = {sid: {"id": sid, "lat": 41.0, "lon": -72.0, "parent": ""} for sid in "abc"}
                connections = []
                if raw_links != "-":
                    for raw in raw_links.split(";"):
                        a, b, dep, arr, trip, route, seq, pu, do = raw.split(",")
                        connections.append((int(dep), int(arr), a, b, trip, route, "Synthetic",
                                            int(pu), int(do), int(seq)))
                connections.sort(key=lambda x: x[0])
                adjacency = {sid: [] for sid in stops}
                if raw_transfers != "-":
                    for raw in raw_transfers.split(";"):
                        a, b, seconds = raw.split(",")
                        adjacency[a].append({"to": b, "seconds": int(seconds), "meters": int(seconds),
                                             "source": "synthetic", "estimated": True})
                with patch.object(routing, "network", return_value=(stops, None, {})), \
                     patch.object(routing, "transfer_graph", return_value=adjacency), \
                     patch.object(routing, "connections", return_value=connections), \
                     patch.object(routing, "coverage", return_value=[]):
                    result = routing.plan("2026-11-12", origin, destination, int(start),
                                          int(deadline), buffer=int(buffer))
                self.assertEqual(None if not result["found"] else result["arrival"],
                                 None if expected == "NONE" else int(expected))
                if expected != "NONE":
                    actual_modes = ["walk" if leg["kind"] == "walk" else leg["route"]
                                    for leg in result["legs"]]
                    self.assertEqual(actual_modes, [] if modes == "-" else modes.split(","))


if __name__ == "__main__":
    unittest.main()
