"""Build independently installable agency SQLite packs from imported GTFS.

Does not download feeds or claim missing coverage. All outputs are staged in build/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import os

ROOT = Path(__file__).resolve().parents[1]
AGENCIES = {"cttransit": "cttransit", "hartford": "hartford", "pvta": "pvta", "amtrak": "amtrak"}
TABLES = ("stops", "routes", "trips", "times", "calendar", "exceptions", "shapes", "transfers")


def build(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {"format": "transit-atlas-lan-v1", "packages": {}, "missing_agencies": []}
    if not source.is_file():
        raise FileNotFoundError(source)
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as original:
        for agency, feed in AGENCIES.items():
            count = original.execute("SELECT COUNT(*) FROM routes WHERE feed=?", (feed,)).fetchone()[0]
            if not count:
                manifest["missing_agencies"].append(agency)
                continue
            fd, name = tempfile.mkstemp(prefix=".build-", suffix=".sqlite", dir=destination)
            os.close(fd)
            tmp = Path(name)
            try:
                with sqlite3.connect(tmp) as target:
                    original.backup(target)
                    target.execute("DELETE FROM routes WHERE feed != ?", (feed,))
                    target.execute("DELETE FROM stops WHERE feed != ?", (feed,))
                    target.execute("DELETE FROM trips WHERE route NOT IN (SELECT id FROM routes)")
                    target.execute("DELETE FROM times WHERE trip NOT IN (SELECT id FROM trips)")
                    target.execute("DELETE FROM calendar WHERE service NOT IN (SELECT service FROM trips)")
                    target.execute("DELETE FROM exceptions WHERE service NOT IN (SELECT service FROM trips)")
                    target.execute("DELETE FROM shapes WHERE id NOT IN (SELECT shape FROM trips)")
                    target.execute("DELETE FROM transfers WHERE a NOT IN (SELECT id FROM stops) OR b NOT IN (SELECT id FROM stops)")
                    target.commit()
                    if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ValueError("SQLite integrity failure")
                    target.execute("VACUUM")
                sha = hashlib.file_digest(tmp.open("rb"), "sha256").hexdigest()
                filename = agency + "-" + sha[:16] + ".sqlite"
                os.replace(tmp, destination / filename)
                manifest["packages"][agency] = {"id": agency, "kind": "agency", "agency": agency,
                    "version": sha[:16], "bytes": (destination / filename).stat().st_size,
                    "sha256": sha, "dependencies": [], "filename": filename, "route_count": count,
                    "media_type": "application/vnd.sqlite3", "scope": "GTFS timetable and shapes only; no offline street map or walking graph"}
            finally:
                tmp.unlink(missing_ok=True)
    tmpmanifest = destination / ".catalog.tmp"
    tmpmanifest.write_text(json.dumps(manifest, indent=2))
    os.replace(tmpmanifest, destination / "catalog.json")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=ROOT / "data/atlas.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / "build/lan-packs")
    args = parser.parse_args()
    print(json.dumps(build(args.database.resolve(), args.output.resolve()), indent=2))
