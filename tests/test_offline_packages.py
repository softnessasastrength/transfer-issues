"""Synthetic, network-free offline pack manager tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from offline_packages import OfflinePackManager, PackError, resolve


def entry(key, payload, kind="agency", agency=None, dependencies=None):
    return {"id": key, "kind": kind, "agency": agency,
            "version": "1", "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "dependencies": dependencies or []}


class OfflinePackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = {"map": b"offline-map", "ct": b"ct-gtfs",
                     "rail": b"rail-gtfs", "pvta": b"pvta-gtfs",
                     "amtrak": b"amtrak-gtfs"}
        self.catalog = {"packages": {
            "map": entry("map", self.data["map"], "shared"),
            "ct": entry("ct", self.data["ct"], agency="cttransit", dependencies=["map"]),
            "rail": entry("rail", self.data["rail"], agency="hartford", dependencies=["map"]),
            "pvta": entry("pvta", self.data["pvta"], agency="pvta", dependencies=["map"]),
            "amtrak": entry("amtrak", self.data["amtrak"], agency="amtrak", dependencies=["map"])}}
        self.payloads = {}
        for key, data in self.data.items():
            path = self.root / (key + ".bin")
            path.write_bytes(data)
            self.payloads[key] = path
        self.manager = OfflinePackManager(self.root / "store")

    def test_shared_dependency_once(self):
        p = resolve(self.catalog, ["cttransit", "hartford"])
        self.assertEqual(p["packages"].count("map"), 1)
        self.assertEqual(p["total_bytes"], sum(len(self.data[k]) for k in ("map", "ct", "rail")))

    def test_requires_approval_and_no_implicit_install(self):
        with self.assertRaises(PackError):
            self.manager.install(self.catalog, ["cttransit"], self.payloads)
        self.assertEqual(self.manager.state()["installed"], {})

    def test_install_selected_and_verify_offline(self):
        s = self.manager.install(self.catalog, ["cttransit", "hartford"], self.payloads, approved=True)
        self.assertEqual(set(s["installed"]), {"ct", "rail", "map"})
        self.assertTrue(all(self.manager.verify_installed().values()))
        self.assertEqual(s["update_policy"], "auto")

    def test_missing_pvta_never_claimed_installed(self):
        c = {"packages": {k: v for k, v in self.catalog["packages"].items() if k != "pvta"}}
        self.assertEqual(resolve(c, ["pvta"])["missing_agencies"], ["pvta"])
        with self.assertRaises(PackError):
            self.manager.install(c, ["pvta"], self.payloads, approved=True)

    def test_bad_checksum_preserves_state(self):
        self.manager.install(self.catalog, ["cttransit"], self.payloads, approved=True)
        before = self.manager.state()
        self.payloads["rail"].write_bytes(b"corrupt!!")
        with self.assertRaises(PackError):
            self.manager.install(self.catalog, ["cttransit", "hartford"], self.payloads, approved=True)
        self.assertEqual(self.manager.state(), before)

    def test_unselected_agency_dependency_rejected(self):
        self.catalog["packages"]["ct"]["dependencies"] = ["rail"]
        with self.assertRaises(PackError):
            resolve(self.catalog, ["cttransit"])

    def test_cycle_rejected(self):
        self.catalog["packages"]["map"]["dependencies"] = ["ct"]
        with self.assertRaises(PackError):
            resolve(self.catalog, ["cttransit"])

    def test_update_only_existing_selected_and_no_new_dependency(self):
        self.manager.install(self.catalog, ["cttransit"], self.payloads, approved=True)
        self.assertFalse(self.manager.check_update(self.catalog, "rail"))
        newer = {"packages": {k: dict(v) for k, v in self.catalog["packages"].items()}}
        newer["packages"]["ct"]["sha256"] = "a" * 64
        self.assertTrue(self.manager.check_update(newer, "ct"))
        newer["packages"]["ct"]["dependencies"] = ["map", "new-graph"]
        self.assertFalse(self.manager.check_update(newer, "ct"))

    def test_no_selection_no_payload(self):
        s = self.manager.install(self.catalog, [], {}, approved=True)
        self.assertEqual(s["installed"], {})


if __name__ == "__main__":
    unittest.main()
