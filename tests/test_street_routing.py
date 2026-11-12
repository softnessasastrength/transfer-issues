"""Synthetic OSM street routing tests. No network or real-user locations."""
import sqlite3
from pathlib import Path
import tempfile
import unittest
from scripts.build_street_graph import build
from street_routing import StreetGraph, NoStreetPath
from transfer_edges import edges

OSM = """<osm version="0.6">
<node id="1" lat="41.0" lon="-72.0"/>
<node id="2" lat="41.0" lon="-71.999"/>
<node id="3" lat="41.0" lon="-71.998"/>
<node id="4" lat="41.001" lon="-72.0"/>
<node id="5" lat="41.001" lon="-71.999"/>
<node id="6" lat="41.02" lon="-72.0"/>
<way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/>
<tag k="highway" v="residential"/></way>
<way id="11"><nd ref="1"/><nd ref="4"/>
<tag k="highway" v="footway"/></way>
<way id="12"><nd ref="4"/><nd ref="5"/>
<tag k="highway" v="residential"/><tag k="oneway" v="yes"/></way>
<way id="13"><nd ref="5"/><nd ref="2"/>
<tag k="highway" v="steps"/></way>
<way id="14"><nd ref="5"/><nd ref="6"/>
<tag k="highway" v="motorway"/></way>
</osm>"""


class StreetGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.osm = self.root / "fixture.osm"
        self.osm.write_text(OSM)
        self.path = self.root / "streets.sqlite"
        self.result = build(self.osm, self.path)
        self.graph = StreetGraph(self.path)

    def test_builder_creates_valid_sqlite(self):
        self.assertGreater(self.result["edges"], 0)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_walk_route_uses_connected_graph(self):
        a = {"lat": 41.0, "lon": -72.0}
        b = {"lat": 41.0, "lon": -71.998}
        result = self.graph.route(a, b)
        self.assertEqual(result["nodes"], [1, 2, 3])
        self.assertEqual(result["source"], "osm_graph")

    def test_footway_and_steps_not_cycleable(self):
        a = {"lat": 41.001, "lon": -72.0}
        b = {"lat": 41.0, "lon": -72.0}
        self.assertEqual(self.graph.route(a, b, mode="walk", snap_meters=5)["nodes"], [4, 1])
        self.assertNotIn(1, [dst for dst, _ in self.graph.adj["cycle"].get(4, [])])
        self.assertNotIn(2, [dst for dst, _ in self.graph.adj["cycle"].get(5, [])])

    def test_no_motorway_access_or_distant_snap(self):
        with self.assertRaises(NoStreetPath):
            self.graph.route({"lat": 41.02, "lon": -72.0},
                             {"lat": 41.0, "lon": -72.0}, snap_meters=50)

    def test_graph_transfer_does_not_use_geometric_fallback(self):
        stops = {"ct": {"lat": 41.0, "lon": -72.0},
                 "rail": {"lat": 41.0, "lon": -71.998},
                 "offgraph": {"lat": 41.0005, "lon": -71.9975}}
        result = edges(stops, [], radius=500, street_graph=self.graph)
        link = next(x for x in result["ct"] if x["to"] == "rail")
        self.assertEqual(link["source"], "osm_graph")
        self.assertTrue(link["estimated"])

    def test_failed_build_preserves_previous_graph(self):
        previous = self.path.read_bytes()
        self.osm.write_text("<osm><way>")
        with self.assertRaises(Exception):
            build(self.osm, self.path)
        self.assertEqual(self.path.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
