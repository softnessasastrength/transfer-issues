"""Synthetic agency pack build tests; no live feeds or network access."""
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.build_lan_packs import build


class LanPackTests(unittest.TestCase):
    def test_selective_build_and_missing_feed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source.sqlite"
            with sqlite3.connect(source) as db:
                db.executescript("""
                    CREATE TABLE stops(id TEXT,feed TEXT,name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT);
                    CREATE TABLE routes(id TEXT,feed TEXT,short TEXT,name TEXT,type TEXT,color TEXT,agency TEXT);
                    CREATE TABLE trips(id TEXT,route TEXT,service TEXT,headsign TEXT,direction TEXT,shape TEXT);
                    CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER);
                    CREATE TABLE calendar(service TEXT,start TEXT,end TEXT,days TEXT);
                    CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
                    CREATE TABLE shapes(id TEXT,seq INTEGER,lat REAL,lon REAL);
                    CREATE TABLE transfers(a TEXT,b TEXT,type INTEGER,seconds INTEGER);
                    INSERT INTO stops VALUES ('ct:s','cttransit','Stop',41.7,-72.6,NULL,NULL);
                    INSERT INTO routes VALUES ('ct:r','cttransit','1','Route',3,NULL,NULL);
                    INSERT INTO trips VALUES ('ct:t','ct:r','ct:svc','Test',NULL,'ct:shape');
                    INSERT INTO times VALUES ('ct:t',1,'ct:s',3600,3600,0,0);
                    INSERT INTO calendar VALUES ('ct:svc','20260101','20261231','1111111');
                    INSERT INTO shapes VALUES ('ct:shape',1,41.7,-72.6);
                """)
            catalog = build(source, root / "packs")
            self.assertEqual(set(catalog["packages"]), {"cttransit"})
            self.assertIn("pvta", catalog["missing_agencies"])
            p = catalog["packages"]["cttransit"]
            file = root / "packs" / p["filename"]
            with file.open("rb") as f:
                self.assertEqual(hashlib.file_digest(f, "sha256").hexdigest(), p["sha256"])
            with sqlite3.connect(file) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM routes").fetchone()[0], 1)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")


if __name__ == "__main__":
    unittest.main()
