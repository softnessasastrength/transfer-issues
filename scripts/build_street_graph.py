"""Small, offline OSM XML -> SQLite pedestrian/cycling graph builder.

This deliberately accepts local .osm XML extracts, not PBF. No network requests.
Not a substitute for a complete OSM access/turn-restriction routing engine.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

WALK_BLOCK = {"motorway", "motorway_link", "trunk", "trunk_link"}
CYCLE_BLOCK = WALK_BLOCK | {"steps", "footway", "pedestrian"}
WALK_ALLOWED = {"footway", "path", "pedestrian", "steps", "living_street", "residential",
                "service", "tertiary", "secondary", "primary", "track", "cycleway",
                "unclassified", "road", "bridleway"}
CYCLE_ALLOWED = WALK_ALLOWED - {"steps"}
SCHEMA = """
CREATE TABLE nodes(id INTEGER PRIMARY KEY, lat REAL NOT NULL, lon REAL NOT NULL);
CREATE TABLE edges(src INTEGER NOT NULL, dst INTEGER NOT NULL, meters REAL NOT NULL,
 walk INTEGER NOT NULL, cycle INTEGER NOT NULL,
 PRIMARY KEY(src,dst), FOREIGN KEY(src) REFERENCES nodes(id), FOREIGN KEY(dst) REFERENCES nodes(id));
CREATE INDEX edge_dst ON edges(dst);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
"""


def haversine(a, b):
    lat1, lat2 = map(math.radians, (a[0], b[0]))
    dlat = lat2 - lat1
    dlon = math.radians(b[1] - a[1])
    x = math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2
    return 12742000 * math.asin(min(1, math.sqrt(x)))


def modes(tags):
    highway = tags.get("highway")
    if not highway or tags.get("access") in {"no", "private"}:
        return False, False
    walk = highway in WALK_ALLOWED and highway not in WALK_BLOCK
    cycle = highway in CYCLE_ALLOWED and highway not in CYCLE_BLOCK
    if highway == "cycleway":
        walk = tags.get("foot") in {"yes", "designated", "permissive"}
    if highway == "footway":
        cycle = tags.get("bicycle") in {"yes", "designated", "permissive"}
    if highway == "bridleway":
        cycle = tags.get("bicycle") in {"yes", "designated", "permissive"}
    if tags.get("foot") in {"no", "private"}:
        walk = False
    if tags.get("bicycle") in {"no", "private"}:
        cycle = False
    if tags.get("foot") in {"yes", "designated", "permissive"}:
        walk = True
    if tags.get("bicycle") in {"yes", "designated", "permissive"}:
        cycle = True
    return walk, cycle


def build(source, output):
    """Parse an OSM XML extract, write a verified graph, atomically activate."""
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise FileNotFoundError(source)
    coords = {}
    ways = []
    # For a bounded regional extract. Large extracts need streaming/OSM PBF tooling.
    for _, element in ET.iterparse(source, events=("end",)):
        if element.tag == "node":
            if "lat" in element.attrib and "lon" in element.attrib:
                coords[int(element.attrib["id"])] = (float(element.attrib["lat"]), float(element.attrib["lon"]))
            element.clear()
        elif element.tag == "way":
            tags = {tag.attrib["k"]: tag.attrib["v"] for tag in element.findall("tag")}
            walk, cycle = modes(tags)
            if walk or cycle:
                ids = [int(nd.attrib["ref"]) for nd in element.findall("nd")]
                ways.append((ids, walk, cycle, tags.get("oneway"), tags.get("oneway:bicycle")))
            element.clear()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix=".streets-", suffix=".sqlite", dir=output.parent)
    os.close(fd)
    temp = Path(filename)
    try:
        with sqlite3.connect(temp) as db:
            db.executescript(SCHEMA)
            used = set()
            edge_map = {}
            for ids, walk, cycle, oneway, bike_oneway in ways:
                for a, b in zip(ids, ids[1:]):
                    if a not in coords or b not in coords or a == b:
                        continue
                    length = haversine(coords[a], coords[b])
                    if length <= 0:
                        continue
                    used.update((a, b))
                    # Pedestrian travel is normally bidirectional; signed foot
                    # restrictions and barriers are NOT modeled in this POC.
                    directions = [(a, b, walk, cycle)]
                    if oneway not in {"yes", "1", "true"}:
                        directions.append((b, a, walk, cycle))
                    elif walk:
                        directions.append((b, a, True, False))
                    if bike_oneway == "no" and cycle:
                        directions.append((b, a, False, True))
                    for src, dst, foot, bike in directions:
                        old = edge_map.get((src, dst))
                        if old:
                            edge_map[src, dst] = (min(length, old[0]), int(foot or old[1]), int(bike or old[2]))
                        else:
                            edge_map[src, dst] = (length, int(foot), int(bike))
            db.executemany("INSERT INTO nodes VALUES (?,?,?)",
                           ((i, *coords[i]) for i in sorted(used)))
            db.executemany("INSERT INTO edges VALUES (?,?,?,?,?)",
                           ((a, b, *edge_map[a, b]) for a, b in sorted(edge_map)))
            with source.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            db.executemany("INSERT INTO metadata VALUES (?,?)",
                           [("format", "atlas-street-v1"), ("osm_sha256", digest),
                            ("limitations", "OSM XML POC: no turn restrictions, barriers, grade or access validation")])
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Graph integrity failure")
            counts = {"nodes": len(used), "edges": len(edge_map)}
        os.replace(temp, output)
        return {**counts, "source_sha256": digest, "output": str(output)}
    finally:
        temp.unlink(missing_ok=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--osm", type=Path, required=True, help="Existing local OSM XML extract")
    p.add_argument("--output", type=Path, default=Path("build/offline-network/streets.sqlite"))
    a = p.parse_args()
    print(json.dumps(build(a.osm, a.output), indent=2))
