"""Read-only integrity regression for local Atlas SQLite data and LAN pack exports.

Usage:
  python3 scripts/check_data_integrity.py --database data/atlas.sqlite
  python3 scripts/check_data_integrity.py --catalog build/lan-packs/catalog.json

This checks stored structure and references, not publisher authenticity, service
freshness, installed Android state, or offline map availability. No network I/O.
"""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


COLUMNS = {
    "stops": {"id", "feed"},
    "routes": {"id", "feed"},
    "trips": {"id", "route", "service"},
    "times": {"trip", "seq", "stop", "arr", "dep"},
    "calendar": {"service"},
    "exceptions": {"service"},
    "shapes": {"id"},
    "transfers": {"a", "b"},
}

# One row is sufficient to establish each regression. Keep diagnostics bounded
# even for a regional database with millions of stop times.
CHECKS = {
    "trip without route": "SELECT 1 FROM trips t WHERE NOT EXISTS (SELECT 1 FROM routes r WHERE r.id=t.route) LIMIT 1",
    "trip without service definition": "SELECT 1 FROM trips t WHERE NOT EXISTS (SELECT 1 FROM calendar c WHERE c.service=t.service) AND NOT EXISTS (SELECT 1 FROM exceptions e WHERE e.service=t.service) LIMIT 1",
    "trip without stop times": "SELECT 1 FROM trips t WHERE NOT EXISTS (SELECT 1 FROM times x WHERE x.trip=t.id) LIMIT 1",
    "stop time without trip": "SELECT 1 FROM times x WHERE NOT EXISTS (SELECT 1 FROM trips t WHERE t.id=x.trip) LIMIT 1",
    "stop time without stop": "SELECT 1 FROM times x WHERE NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=x.stop) LIMIT 1",
    "invalid stop time": "SELECT 1 FROM times WHERE typeof(seq)!='integer' OR seq<0 OR typeof(arr)!='integer' OR arr<0 OR typeof(dep)!='integer' OR dep<arr LIMIT 1",
    "transfer without stop": "SELECT 1 FROM transfers x WHERE NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=x.a) OR NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=x.b) LIMIT 1",
}


def check_database(path, expected_feed=None):
    """Return a bounded list of failures; never create or modify the database."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        return [f"database missing or symlink: {path}"]
    issues = []
    try:
        # as_uri escapes filenames containing ? or #. mode=ro cannot create DBs.
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            result = db.execute("PRAGMA quick_check(1)").fetchone()
            if result != ("ok",):
                return [f"SQLite quick_check failed: {result[0] if result else 'no result'}"]
            for table, required in COLUMNS.items():
                exists = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if not exists:
                    issues.append(f"missing table: {table}")
                    continue
                columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
                if not required <= columns:
                    issues.append(f"missing columns: {table} ({', '.join(sorted(required - columns))})")
            if issues:
                return issues
            for label, sql in CHECKS.items():
                if db.execute(sql).fetchone():
                    issues.append(label)
            if expected_feed is not None:
                for table in ("routes", "stops"):
                    if db.execute(f'SELECT 1 FROM "{table}" WHERE feed IS NULL OR feed!=? LIMIT 1',
                                  (expected_feed,)).fetchone():
                        issues.append(f"{table} outside declared feed: {expected_feed}")
    except sqlite3.Error as exc:
        issues.append(f"SQLite error: {exc}")
    return issues


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_catalog(path):
    """Verify an existing LAN export catalog and its declared agency payloads."""
    path = Path(path)
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"catalog unreadable: {exc}"]
    if not isinstance(catalog, dict) or catalog.get("format") != "transit-atlas-lan-v1" or not isinstance(catalog.get("packages"), dict):
        return ["invalid LAN catalog format"]
    issues = []
    for agency, entry in catalog["packages"].items():
        if not isinstance(agency, str) or not agency or not isinstance(entry, dict):
            issues.append("invalid catalog entry")
            continue
        filename = entry.get("filename")
        sha = entry.get("sha256")
        size = entry.get("bytes")
        version = entry.get("version")
        if (entry.get("id") != agency or entry.get("agency") != agency or
                entry.get("kind") != "agency" or not isinstance(filename, str) or
                filename in ("", ".", "..") or Path(filename).name != filename or
                "\\" in filename or not isinstance(sha, str) or len(sha) != 64 or
                any(c not in "0123456789abcdef" for c in sha) or
                not isinstance(version, str) or version != sha[:16] or
                type(size) is not int or size <= 0 or
                type(entry.get("route_count")) is not int or entry["route_count"] <= 0):
            issues.append(f"invalid metadata: {agency}")
            continue
        payload = path.parent / filename
        if payload.is_symlink() or not payload.is_file():
            issues.append(f"payload missing or symlink: {agency}")
            continue
        try:
            matches = payload.stat().st_size == size and _sha256(payload) == sha
        except OSError:
            matches = False
        if not matches:
            issues.append(f"payload size/hash mismatch: {agency}")
            continue
        issues.extend(f"{agency}: {issue}" for issue in check_database(payload, agency))
        # Count only after schema validation; do not query an invalid payload.
        if not any(issue.startswith(f"{agency}: ") for issue in issues):
            try:
                with closing(sqlite3.connect(payload.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                    db.execute("PRAGMA query_only=ON")
                    count = db.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
                if count != entry["route_count"]:
                    issues.append(f"route count mismatch: {agency}")
            except sqlite3.Error as exc:
                issues.append(f"{agency}: SQLite error: {exc}")
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--database", type=Path)
    group.add_argument("--catalog", type=Path)
    args = parser.parse_args(argv)
    issues = check_database(args.database) if args.database else check_catalog(args.catalog)
    for issue in issues:
        print("FAIL:", issue)
    if issues:
        return 1
    print("PASS: local structural integrity checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
