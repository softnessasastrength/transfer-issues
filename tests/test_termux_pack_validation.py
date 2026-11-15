"""Synthetic phone pack verification tests, no live feeds or downloads."""
import hashlib
import json
from pathlib import Path
import sqlite3
from contextlib import closing
import tempfile
import unittest
import subprocess
import sys
from scripts.verify_lan_catalog import verify
from pack_fixtures import agency_database
from developer_center.inspection import pack_inspection


class PackValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root / "cttransit-synthetic.sqlite"
        agency_database(self.pack)
        digest = hashlib.sha256(self.pack.read_bytes()).hexdigest()
        self.catalog = {"format": "transit-atlas-lan-v1", "missing_agencies": ["pvta"],
                        "packages": {"cttransit": {"filename": self.pack.name,
                        "bytes": self.pack.stat().st_size, "sha256": digest, "route_count": 1}}}
        self.save()

    def save(self):
        (self.root / "catalog.json").write_text(json.dumps(self.catalog))

    def test_valid_pack(self):
        result = verify(self.root)
        self.assertEqual(result["verified"]["cttransit"]["routes"], 1)
        self.assertEqual(result["missing"], ["pvta"])

    def test_tampered_checksum(self):
        self.catalog["packages"]["cttransit"]["sha256"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            verify(self.root)

    def test_reject_path_traversal(self):
        self.catalog["packages"]["cttransit"]["filename"] = "../secret.sqlite"
        self.save()
        with self.assertRaisesRegex(ValueError, "Unsafe package filename"):
            verify(self.root)

    def test_reject_mixed_agency(self):
        with closing(sqlite3.connect(self.pack)) as db, db:
            db.execute("INSERT INTO routes (id,feed) VALUES ('amtrak:r','amtrak')")
        entry = self.catalog["packages"]["cttransit"]
        entry["bytes"] = self.pack.stat().st_size
        entry["sha256"] = hashlib.sha256(self.pack.read_bytes()).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "Agency route coverage mismatch"):
            verify(self.root)

    def mutate(self, sql):
        with closing(sqlite3.connect(self.pack)) as db, db:
            db.executescript(sql)
        entry = self.catalog['packages']['cttransit']
        entry['bytes'] = self.pack.stat().st_size
        entry['sha256'] = hashlib.sha256(self.pack.read_bytes()).hexdigest()
        self.save()

    def test_missing_tables_and_columns_rejected(self):
        original = self.pack.read_bytes()
        for sql, message in [
            ('DROP TABLE stops', 'Missing required table: stops'),
            ('ALTER TABLE times DROP COLUMN stop', 'Missing required columns: times'),
            ('DROP TABLE shapes; CREATE VIEW shapes AS SELECT 1 AS id', 'Missing required table: shapes'),
        ]:
            with self.subTest(sql=sql):
                self.pack.write_bytes(original)
                self.mutate(sql)
                with self.assertRaisesRegex(ValueError, message):
                    verify(self.root)

    def test_null_and_dangling_references_rejected(self):
        original = self.pack.read_bytes()
        cases = [
            ("UPDATE trips SET route='missing'", 'trip routes'),
            ("UPDATE trips SET route=NULL", 'trip routes'),
            ("UPDATE times SET trip='missing'", 'stop-time trips'),
            ("UPDATE times SET stop='missing'", 'stop-time stops'),
            ("UPDATE times SET stop=NULL", 'stop-time stops'),
            ("UPDATE trips SET service='missing'", 'trip service'),
            ("UPDATE trips SET service=NULL", 'trip service'),
            ("DELETE FROM times", 'trip stop times'),
            ("INSERT INTO transfers VALUES ('ct:a','missing',0,0)", 'transfer stops'),
        ]
        for sql, message in cases:
            with self.subTest(sql=sql):
                self.pack.write_bytes(original)
                self.mutate(sql)
                with self.assertRaisesRegex(ValueError, message):
                    verify(self.root)

    def test_duplicate_and_empty_keys_rejected(self):
        original = self.pack.read_bytes()
        for sql in ("INSERT INTO times SELECT * FROM times", "UPDATE routes SET id=NULL",
                    "INSERT INTO calendar SELECT * FROM calendar", "UPDATE stops SET id=''"):
            with self.subTest(sql=sql):
                self.pack.write_bytes(original)
                self.mutate(sql)
                with self.assertRaisesRegex(ValueError, 'Duplicate key|Empty key'):
                    verify(self.root)

    def test_timing_and_calendar_errors_rejected(self):
        original = self.pack.read_bytes()
        cases = [
            ("UPDATE times SET dep=arr-1", 'Invalid stop times'),
            ("UPDATE times SET arr=-1", 'Invalid stop times'),
            ("UPDATE times SET pickup=4", 'Invalid stop times'),
            ("UPDATE times SET arr=100,dep=100 WHERE seq=2", 'Non-monotonic'),
            ("UPDATE calendar SET start='20260230'", 'Invalid service date'),
            ("UPDATE calendar SET end='20250101'", 'Invalid service calendar'),
            ("UPDATE calendar SET days='111'", 'Invalid service calendar'),
            ("INSERT INTO exceptions VALUES ('ct:svc','20260101',3)", 'Invalid calendar exception'),
            ("INSERT INTO transfers VALUES ('ct:a','ct:b',0,-1)", 'Invalid transfers'),
        ]
        for sql, message in cases:
            with self.subTest(sql=sql):
                self.pack.write_bytes(original)
                self.mutate(sql)
                with self.assertRaisesRegex(ValueError, message):
                    verify(self.root)

    def test_exception_only_overnight_gapped_trip_is_preserved(self):
        self.mutate("DELETE FROM calendar; INSERT INTO exceptions VALUES ('ct:svc','20260101',1)")
        before = self.pack.read_bytes()
        result = verify(self.root)
        self.assertEqual(result['verified']['cttransit']['counts']['times'], 2)
        self.assertEqual(self.pack.read_bytes(), before)
        with closing(sqlite3.connect(self.pack)) as db, db:
            self.assertEqual(db.execute('SELECT seq,arr FROM times ORDER BY seq').fetchall(), [(0,85800),(2,87000)])

    def test_symlink_pack_rejected(self):
        link = self.root / 'linked.sqlite'
        link.symlink_to(self.pack)
        self.catalog['packages']['cttransit']['filename'] = link.name
        self.save()
        with self.assertRaisesRegex(ValueError, 'Symlink package'):
            verify(self.root)

    def test_invalid_catalog_types_and_identity_rejected(self):
        original = json.dumps(self.catalog)
        for field, value in [('bytes', True), ('route_count', -1), ('sha256', 'invalid'),
                             ('agency', 'pvta'), ('filename', None)]:
            with self.subTest(field=field):
                self.catalog = json.loads(original)
                self.catalog['packages']['cttransit'][field] = value
                self.save()
                with self.assertRaises(ValueError):
                    verify(self.root)
        for catalog in ([], {'format': 'transit-atlas-lan-v1', 'packages': {}, 'missing_agencies': [[]]}):
            self.catalog = catalog
            self.save()
            with self.assertRaises(ValueError):
                verify(self.root)

    def test_sqlite_uri_special_characters(self):
        special = self.root / 'folder?#'
        special.mkdir()
        target = special / self.pack.name
        target.write_bytes(self.pack.read_bytes())
        (special / 'catalog.json').write_text(json.dumps(self.catalog))
        self.assertIn('cttransit', verify(special)['verified'])

    def test_command_center_distinguishes_missing_invalid_and_validated(self):
        self.assertEqual(pack_inspection(self.root / 'absent')['status'], 'unavailable')
        result = pack_inspection(self.root)
        self.assertEqual(result['status'], 'validated')
        self.assertEqual(result['unreported'], ['amtrak', 'hartford'])
        self.assertIn('not Android-installed', result['scope'])
        self.mutate("UPDATE times SET stop='missing'")
        self.assertEqual(pack_inspection(self.root)['status'], 'invalid')

    def test_bad_sqlite_and_cli_failure_are_actionable(self):
        self.pack.write_bytes(b'not a database')
        entry = self.catalog['packages']['cttransit']
        entry['bytes'] = self.pack.stat().st_size
        entry['sha256'] = hashlib.sha256(self.pack.read_bytes()).hexdigest()
        self.save()
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts/verify_lan_catalog.py'),
                                 '--packs', str(self.root)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Invalid SQLite pack', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == "__main__":
    unittest.main()
