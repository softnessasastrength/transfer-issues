"""Offline integrity and coverage verification for exported Termux agency packs."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

ALLOWED = {"cttransit", "hartford", "pvta", "amtrak"}


def verify(directory: Path) -> dict:
    catalog = json.loads((directory / "catalog.json").read_text())
    if catalog.get("format") != "transit-atlas-lan-v1":
        raise ValueError("Unexpected catalog format")
    packages = catalog.get("packages")
    missing = catalog.get("missing_agencies")
    if not isinstance(packages, dict) or not isinstance(missing, list):
        raise ValueError("Invalid catalog structure")
    if set(packages) - ALLOWED or set(missing) - ALLOWED or set(packages).intersection(missing):
        raise ValueError("Unexpected or contradictory agency coverage")
    verified = {}
    for agency, entry in packages.items():
        filename = entry["filename"]
        if Path(filename).name != filename or not filename.endswith(".sqlite"):
            raise ValueError("Unsafe package filename")
        path = directory / filename
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"Missing or wrong-size pack: {agency}")
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {agency}")
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError(f"SQLite integrity failure: {agency}")
            routes = db.execute("SELECT COUNT(*) FROM routes WHERE feed=?", (agency,)).fetchone()[0]
            other = db.execute("SELECT COUNT(*) FROM routes WHERE feed!=?", (agency,)).fetchone()[0]
            if not routes or other or routes != entry["route_count"]:
                raise ValueError(f"Agency route coverage mismatch: {agency}")
        verified[agency] = {"routes": routes, "bytes": path.stat().st_size}
    return {"verified": verified, "missing": sorted(missing)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--packs", type=Path, default=Path("build/lan-packs"))
    args = parser.parse_args()
    print(json.dumps(verify(args.packs), indent=2))
