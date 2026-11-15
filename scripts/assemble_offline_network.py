"""Assemble explicitly selected, verified GTFS agency packs into one offline SQLite network.

No network access, no GPS, no implicit agency downloads. The original packs and
personal data are never modified. A failed build leaves the previous network intact.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

TABLES = ("stops", "routes", "trips", "times", "calendar", "exceptions", "shapes", "transfers")
PRIMARY = {"stops": ("id",), "routes": ("id",), "trips": ("id",),
           "times": ("trip", "seq"), "calendar": ("service",),
           "exceptions": ("service", "date"), "shapes": ("id", "seq"),
           "transfers": ("a", "b")}
AGENCIES = frozenset(("cttransit", "hartford", "pvta", "amtrak"))


class NetworkError(ValueError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def assemble(catalog, pack_dir, selected, output):
    """Build a new atomic network from approved agency packages only.

    Catalog is assumed locally trusted; this function verifies payload integrity
    against that catalog, not the catalog's signature or source authenticity.
    """
    chosen = sorted(set(selected))
    if not chosen or any(x not in AGENCIES for x in chosen):
        raise NetworkError("Choose one or more recognized agencies")
    packages = catalog.get("packages", {})
    inputs = []
    for agency in chosen:
        entry = packages.get(agency)
        if not entry or entry.get("agency") != agency or entry.get("kind") != "agency":
            raise NetworkError("Agency unavailable: " + agency)
        filename = entry.get("filename", "")
        if not filename or Path(filename).name != filename:
            raise NetworkError("Invalid package filename")
        source = Path(pack_dir) / filename
        if not source.is_file() or source.stat().st_size != entry.get("bytes"):
            raise NetworkError("Missing or incomplete pack: " + agency)
        if sha256(source) != entry.get("sha256"):
            raise NetworkError("Pack checksum mismatch: " + agency)
        inputs.append((agency, source, entry))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".unified-", suffix=".sqlite", dir=output.parent)
    os.close(fd)
    tmp = Path(name)
    tmp.unlink()
    try:
        with sqlite3.connect(tmp) as dst:
            # Use the existing source schema and indexes, without copying its data.
            with sqlite3.connect(f"file:{inputs[0][1]}?mode=ro", uri=True) as first:
                first.backup(dst)
            dst.execute("PRAGMA foreign_keys=OFF")
            for table in TABLES:
                dst.execute(f"DELETE FROM {table}")
            dst.execute("CREATE TABLE IF NOT EXISTS network_packs (agency TEXT PRIMARY KEY, sha256 TEXT NOT NULL, version TEXT NOT NULL)")
            dst.execute("DELETE FROM network_packs")
            for agency, source, entry in inputs:
                with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src:
                    src.row_factory = sqlite3.Row
                    if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise NetworkError("Invalid SQLite pack: " + agency)
                    routes = src.execute("SELECT COUNT(*) FROM routes WHERE feed=?", (agency,)).fetchone()[0]
                    if not routes:
                        raise NetworkError("No routes for selected agency: " + agency)
                    # Reject a package that includes unrelated agency routes/stops.
                    for table in ("routes", "stops"):
                        if src.execute(f"SELECT COUNT(*) FROM {table} WHERE feed != ? OR feed IS NULL", (agency,)).fetchone()[0]:
                            raise NetworkError("Unexpected agency data in " + agency)
                    for table in TABLES:
                        cols = [r[1] for r in src.execute(f"PRAGMA table_info({table})")]
                        dst_cols = [r[1] for r in dst.execute(f"PRAGMA table_info({table})")]
                        if cols != dst_cols:
                            raise NetworkError("Incompatible schema for " + table)
                        names = ",".join('"' + c.replace('"', '""') + '"' for c in cols)
                        placeholders = ",".join("?" for _ in cols)
                        seen = set()
                        index = [cols.index(c) for c in PRIMARY[table]]
                        for row in src.execute(f"SELECT {names} FROM {table}"):
                            key = tuple(row[i] for i in index)
                            if key in seen:
                                raise NetworkError("Duplicate key within " + agency + ": " + table)
                            seen.add(key)
                            # Existing shared IDs may occur in multiple agency packs.
                            existing = dst.execute(
                                f"SELECT {names} FROM {table} WHERE " +
                                " AND ".join('"' + col + '"=?' for col in PRIMARY[table]), key
                            ).fetchone()
                            if existing is not None:
                                if tuple(existing) != tuple(row):
                                    raise NetworkError("Conflicting shared ID in " + table)
                                continue
                            dst.execute(f"INSERT INTO {table} ({names}) VALUES ({placeholders})", tuple(row))
                dst.execute("INSERT INTO network_packs VALUES (?,?,?)",
                            (agency, entry["sha256"], str(entry.get("version", ""))))
            # Cross-table references must be coherent. No invented interagency links.
            checks = {
                "trip routes": "SELECT COUNT(*) FROM trips WHERE route NOT IN (SELECT id FROM routes)",
                "stop times": "SELECT COUNT(*) FROM times WHERE trip NOT IN (SELECT id FROM trips) OR stop NOT IN (SELECT id FROM stops)",
                "calendar": "SELECT COUNT(*) FROM trips WHERE service NOT IN (SELECT service FROM calendar UNION SELECT service FROM exceptions)",
                "transfers": "SELECT COUNT(*) FROM transfers WHERE a NOT IN (SELECT id FROM stops) OR b NOT IN (SELECT id FROM stops)",
            }
            for label, sql in checks.items():
                if dst.execute(sql).fetchone()[0]:
                    raise NetworkError("Broken references: " + label)
            dst.commit()
            if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise NetworkError("Unified database integrity check failed")
            counts = {t: dst.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
        # Atomic activation on same filesystem. Previous network survives failures.
        os.replace(tmp, output)
        return {"selected_agencies": chosen, "counts": counts, "bytes": output.stat().st_size,
                "sha256": sha256(output), "output": str(output),
                "limitations": ["No inferred cross-agency transfers", "No pedestrian graph",
                                "No native routing engine", "Scheduled service only"]}
    finally:
        tmp.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, default=Path("build/lan-packs/catalog.json"))
    p.add_argument("--pack-dir", type=Path, default=Path("build/lan-packs"))
    p.add_argument("--output", type=Path, default=Path("build/offline-network/atlas.sqlite"))
    p.add_argument("--agencies", nargs="+", required=True, choices=sorted(AGENCIES))
    a = p.parse_args()
    print(json.dumps(assemble(json.loads(a.catalog.read_text()), a.pack_dir, a.agencies, a.output), indent=2))


if __name__ == "__main__":
    main()
