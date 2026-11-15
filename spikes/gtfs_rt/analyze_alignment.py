#!/usr/bin/env python3
"""SPIKE (testing only): do GTFS-RT IDs join to the Atlas's static GTFS?

Doctrine exception scope: testing/evaluation only, granted 2026-11-15.
Not a production adoption; nothing here is imported by the shipped app.

Compares the route/trip IDs decoded from the live MTA feeds (decode_mta.py
output on stdin, or --fetch to decode fresh) against the imported static
feeds in the Atlas SQLite database: routes/trips whose namespaced Atlas IDs
carry the mnr:/lirr: prefixes. Reports raw match rates both ways.

Usage: analyze_alignment.py --db /path/to/atlas.sqlite [--fetch]
"""
import json
import sqlite3
import subprocess
import sys


def suffix(namespaced: str) -> str:
    return namespaced.split(":", 1)[1] if ":" in namespaced else namespaced


def main() -> None:
    args = sys.argv[1:]
    db_path = args[args.index("--db") + 1] if "--db" in args else "atlas.sqlite"
    if "--fetch" in args:
        raw = subprocess.run([sys.executable, "decode_mta.py", "both"],
                             capture_output=True, text=True, check=True,
                             cwd=sys.path[0] or ".").stdout
        decoded = json.loads(raw)
    else:
        decoded = json.load(sys.stdin)

    db = sqlite3.connect(db_path)
    report = {}
    for item in decoded:
        feed = item["feed"]
        static_routes = {suffix(r[0]) for r in db.execute(
            "SELECT id FROM routes WHERE feed=?", (feed,))}
        static_trips = {suffix(t[0]) for t in db.execute(
            "SELECT t.id FROM trips t JOIN routes r ON t.route = r.id WHERE r.feed=?", (feed,))}
        rt_routes = set(item["sample_route_ids"])  # full set re-derived below if present
        rt_routes = set(item.get("all_route_ids") or item["sample_route_ids"])
        rt_trips = set(item.get("all_trip_ids") or item["sample_trip_ids"])
        def rate(rt: set, static: set) -> dict:
            if not rt:
                return {"rt_ids": 0, "matched": 0, "match_rate": None}
            matched = len(rt & static)
            return {"rt_ids": len(rt), "matched": matched,
                    "match_rate": round(matched / len(rt), 4),
                    "unmatched_samples": sorted(rt - static)[:8]}
        report[feed] = {
            "static_routes": len(static_routes),
            "static_trips": len(static_trips),
            "routes": rate(rt_routes, static_routes),
            "trip_update_trip_ids": rate(rt_trips, static_trips),
        }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
