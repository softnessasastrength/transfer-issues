"""Deterministic tests of offline multi-agency SQLite assembly. No internet."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.assemble_offline_network import assemble, NetworkError

SCHEMA = """
CREATE TABLE stops(id TEXT,feed TEXT,name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT);
CREATE TABLE routes(id TEXT,feed TEXT,short TEXT,name TEXT,type TEXT,color TEXT,agency TEXT);
CREATE TABLE trips(id TEXT,route TEXT,service TEXT,headsign TEXT,direction TEXT,shape TEXT);
CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER);
CREATE TABLE calendar(service TEXT,start TEXT,end TEXT,days TEXT);
CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
CREATE TABLE shapes(id TEXT,seq INTEGER,lat REAL,lon REAL);
CREATE TABLE transfers(a TEXT,b TEXT,type INTEGER,seconds INTEGER);
"""


class UnifiedNetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = {"packages": {}}
        self.add("cttransit")
        self.add("hartford")

    def add(self, agency, conflict=False):
        path = self.root / (agency + ".sqlite")
        with sqlite3.connect(path) as db:
            db.executescript(SCHEMA)
            db.execute("INSERT INTO stops VALUES (?,?,?,?,?,?,?)",
                       (agency + ":s", agency, "Stop", 41.7, -72.6, None, None))
            db.execute("INSERT INTO routes VALUES (?,?,?,?,?,?,?)",
                       (agency + ":r", agency, "1", "Route", "3", None, None))
            db.execute("INSERT INTO trips VALUES (?,?,?,?,?,?)",
                       (agency + ":t", agency + ":r", agency + ":svc", "Test", None, agency + ":shape"))
            db.execute("INSERT INTO times VALUES (?,?,?,?,?,?,?)",
                       (agency + ":t", 1, agency + ":s", 3600, 3600, 0, 0))
            db.execute("INSERT INTO calendar VALUES (?,?,?,?)",
                       (agency + ":svc", "20260101", "20261231", "1111111"))
            db.execute("INSERT INTO shapes VALUES (?,?,?,?)",
                       (agency + ":shape", 1, 41.7, -72.6))
            db.commit()
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        self.catalog["packages"][agency] = {
            "agency": agency, "kind": "agency", "filename": path.name,
            "bytes": path.stat().st_size, "sha256": digest, "version": "test"
        }

    def run_merge(self, chosen=("cttransit", "hartford")):
        return assemble(self.catalog, self.root, chosen, self.root / "unified.sqlite")

    def test_combines_both_agencies(self):
        result = self.run_merge()
        self.assertEqual(result["counts"]["routes"], 2)
        self.assertEqual(result["counts"]["times"], 2)
        with sqlite3.connect(self.root / "unified.sqlite") as db:
            self.assertEqual({r[0] for r in db.execute("SELECT agency FROM network_packs")},
                             {"cttransit", "hartford"})

    def test_only_selected_agency(self):
        result = self.run_merge(("cttransit",))
        self.assertEqual(result["counts"]["routes"], 1)

    def test_missing_agency_refused(self):
        with self.assertRaises(NetworkError):
            self.run_merge(("pvta",))

    def test_bad_checksum_preserves_previous(self):
        self.run_merge(("cttransit",))
        previous = (self.root / "unified.sqlite").read_bytes()
        with (self.root / "hartford.sqlite").open("ab") as f:
            f.write(b"tampered")
        with self.assertRaises(NetworkError):
            self.run_merge()
        self.assertEqual((self.root / "unified.sqlite").read_bytes(), previous)

    def test_cross_agency_stop_time_remains_linked(self):
        self.run_merge()
        with sqlite3.connect(self.root / "unified.sqlite") as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM times t JOIN stops s ON t.stop=s.id").fetchone()[0], 2)

    def test_no_invented_interagency_transfers(self):
        self.run_merge()
        with sqlite3.connect(self.root / "unified.sqlite") as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM transfers").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
