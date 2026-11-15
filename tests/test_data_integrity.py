"""Synthetic, local regressions for the read-only data integrity command."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.check_data_integrity import check_catalog, check_database, main


SCHEMA = """
CREATE TABLE stops(id TEXT PRIMARY KEY, feed TEXT);
CREATE TABLE routes(id TEXT PRIMARY KEY, feed TEXT);
CREATE TABLE trips(id TEXT PRIMARY KEY, route TEXT, service TEXT);
CREATE TABLE times(trip TEXT, seq INTEGER, stop TEXT, arr INTEGER, dep INTEGER);
CREATE TABLE calendar(service TEXT PRIMARY KEY);
CREATE TABLE exceptions(service TEXT, date TEXT);
CREATE TABLE shapes(id TEXT);
CREATE TABLE transfers(a TEXT, b TEXT);
INSERT INTO stops VALUES ('a:s1', 'a'), ('a:s2', 'a');
INSERT INTO routes VALUES ('a:r1', 'a');
INSERT INTO trips VALUES ('a:t1', 'a:r1', 'a:weekday');
INSERT INTO times VALUES ('a:t1', 1, 'a:s1', 100, 100),
                         ('a:t1', 2, 'a:s2', 200, 200);
INSERT INTO calendar VALUES ('a:weekday');
"""


class DataIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "agency?#.sqlite"
        with contextlib.closing(sqlite3.connect(self.db)) as conn, conn:
            conn.executescript(SCHEMA)

    def test_valid_database_and_special_path_are_read_only(self):
        before = self.db.read_bytes()
        self.assertEqual([], check_database(self.db, "a"))
        self.assertEqual(before, self.db.read_bytes())
        self.assertFalse((self.root / "agency?#.sqlite-wal").exists())

    def test_missing_file_does_not_create_database(self):
        missing = self.root / "missing.sqlite"
        self.assertTrue(check_database(missing))
        self.assertFalse(missing.exists())

    def test_missing_schema_and_broken_references(self):
        with contextlib.closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("DROP TABLE shapes")
        self.assertIn("missing table: shapes", check_database(self.db))
        with contextlib.closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("CREATE TABLE shapes(id TEXT)")
            conn.execute("UPDATE trips SET route='absent'")
            conn.execute("UPDATE times SET stop='absent' WHERE seq=2")
            conn.execute("INSERT INTO transfers VALUES ('a:s1', 'absent')")
        issues = check_database(self.db)
        self.assertIn("trip without route", issues)
        self.assertIn("stop time without stop", issues)
        self.assertIn("transfer without stop", issues)

    def test_invalid_times_and_foreign_feed(self):
        with contextlib.closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("UPDATE times SET dep=50 WHERE seq=1")
            conn.execute("UPDATE routes SET feed='other'")
        issues = check_database(self.db, "a")
        self.assertIn("invalid stop time", issues)
        self.assertIn("routes outside declared feed: a", issues)

    def catalog(self):
        payload = self.root / "a.sqlite"
        payload.write_bytes(self.db.read_bytes())
        sha = hashlib.sha256(payload.read_bytes()).hexdigest()
        catalog = {"format": "transit-atlas-lan-v1", "packages": {
            "a": {"id": "a", "agency": "a", "kind": "agency",
                  "filename": payload.name, "sha256": sha, "version": sha[:16],
                  "bytes": payload.stat().st_size, "route_count": 1}}}
        path = self.root / "catalog.json"
        path.write_text(json.dumps(catalog))
        return path, catalog, payload

    def test_catalog_valid_and_cli(self):
        path, _, _ = self.catalog()
        self.assertEqual([], check_catalog(path))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, main(["--catalog", str(path)]))
        self.assertIn("PASS", output.getvalue())

    def test_catalog_detects_tamper_version_and_route_count(self):
        path, catalog, payload = self.catalog()
        payload.write_bytes(payload.read_bytes() + b"tamper")
        self.assertIn("payload size/hash mismatch: a", check_catalog(path))
        payload.write_bytes(self.db.read_bytes())
        catalog["packages"]["a"]["version"] = "wrong"
        path.write_text(json.dumps(catalog))
        self.assertIn("invalid metadata: a", check_catalog(path))
        catalog["packages"]["a"]["version"] = catalog["packages"]["a"]["sha256"][:16]
        catalog["packages"]["a"]["route_count"] = 2
        path.write_text(json.dumps(catalog))
        self.assertIn("route count mismatch: a", check_catalog(path))

    def test_catalog_rejects_path_escape_and_reports_cli_failure(self):
        path, catalog, _ = self.catalog()
        catalog["packages"]["a"]["filename"] = "../outside.sqlite"
        path.write_text(json.dumps(catalog))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(1, main(["--catalog", str(path)]))
        self.assertIn("invalid metadata: a", output.getvalue())


if __name__ == "__main__":
    unittest.main()
