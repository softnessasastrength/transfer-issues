"""Offline integrity and coverage verification for exported Termux agency packs."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import re

if __package__:
    from .pack_validation import validate_database
else:
    from pack_validation import validate_database

ALLOWED = {"cttransit", "hartford", "pvta", "amtrak"}


def verify(directory: Path) -> dict:
    catalog = json.loads((directory / "catalog.json").read_text())
    if not isinstance(catalog, dict) or catalog.get("format") != "transit-atlas-lan-v1":
        raise ValueError("Unexpected catalog format")
    packages = catalog.get("packages")
    missing = catalog.get("missing_agencies")
    if not isinstance(packages, dict) or not isinstance(missing, list):
        raise ValueError("Invalid catalog structure")
    if any(not isinstance(key, str) for key in missing) or len(missing) != len(set(missing)):
        raise ValueError("Invalid missing-agency list")
    if set(packages) - ALLOWED or set(missing) - ALLOWED or set(packages).intersection(missing):
        raise ValueError("Unexpected or contradictory agency coverage")
    verified = {}
    for agency, entry in packages.items():
        if not isinstance(entry, dict):
            raise ValueError("Invalid package entry: " + agency)
        filename = entry.get("filename")
        if not isinstance(filename, str):
            raise ValueError("Unsafe package filename")
        if (type(entry.get("bytes")) is not int or entry["bytes"] <= 0 or
                type(entry.get("route_count")) is not int or entry["route_count"] <= 0 or
                not isinstance(entry.get("sha256"), str) or
                not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise ValueError("Invalid package size, checksum or route count: " + agency)
        for field, expected in (("agency", agency), ("id", agency), ("kind", "agency")):
            if field in entry and entry[field] != expected:
                raise ValueError("Package identity mismatch: " + agency)
        if Path(filename).name != filename or not filename.endswith(".sqlite"):
            raise ValueError("Unsafe package filename")
        path = directory / filename
        if path.is_symlink():
            raise ValueError("Symlink package refused: " + agency)
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"Missing or wrong-size pack: {agency}")
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {agency}")
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                db.execute("PRAGMA query_only=ON")
                db.execute("PRAGMA trusted_schema=OFF")
                if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError(f"SQLite integrity failure: {agency}")
                counts = validate_database(db, agency)
                routes = counts['routes']
                if not routes or routes != entry["route_count"]:
                    raise ValueError(f"Agency route coverage mismatch: {agency}")
        except sqlite3.Error as exc:
            raise ValueError(f"Invalid SQLite pack: {agency}: {exc}") from exc
        verified[agency] = {"routes": routes, "bytes": path.stat().st_size, "counts": counts}
    return {"verified": verified, "missing": sorted(missing),
            "unreported": sorted(ALLOWED - set(packages) - set(missing))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--packs", type=Path, default=Path("build/lan-packs"))
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.packs), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Pack verification failed: {exc}\n")
