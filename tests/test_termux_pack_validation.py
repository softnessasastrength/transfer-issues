"""Synthetic phone pack verification tests, no live feeds or downloads."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from scripts.verify_lan_catalog import verify


class PackValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root / "cttransit-synthetic.sqlite"
        with sqlite3.connect(self.pack) as db:
            db.execute("CREATE TABLE routes (feed TEXT)")
            db.execute("INSERT INTO routes VALUES ('cttransit')")
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
        with sqlite3.connect(self.pack) as db:
            db.execute("INSERT INTO routes VALUES ('amtrak')")
        entry = self.catalog["packages"]["cttransit"]
        entry["bytes"] = self.pack.stat().st_size
        entry["sha256"] = hashlib.sha256(self.pack.read_bytes()).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "Agency route coverage mismatch"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
