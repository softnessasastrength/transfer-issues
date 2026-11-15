#!/usr/bin/env python3
"""SPIKE (testing only): decode MTA GTFS-Realtime protobuf feeds end-to-end.

Doctrine exception scope: granted by the owner 2026-11-15 for TESTING /
EVALUATION of protobuf GTFS-RT feeds only. This is NOT a production
adoption and NOT a standing doctrine change. Nothing in this directory is
imported by the shipped app.

Fetches the MTA Metro-North and LIRR combined GTFS-RT feeds (public, no key)
with the gtfs-realtime-bindings protobuf binding and prints a JSON analysis:
entity counts, field coverage, sample IDs, fetch/parse latency.

Usage: decode_mta.py [mnr|lirr|both]   (default both)
Requires: pip install gtfs-realtime-bindings protobuf requests (venv).
"""
import json
import sys
import time

import requests
from google.transit import gtfs_realtime_pb2

FEEDS = {
    "mnr": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr",
    "lirr": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/lirr%2Fgtfs-lirr",
}


def analyze(name: str, url: str) -> dict:
    t0 = time.time()
    resp = requests.get(url, timeout=30, headers={"User-Agent": "TransitAtlas-Spike/0.1 (testing only)"})
    fetch_s = time.time() - t0
    resp.raise_for_status()
    t1 = time.time()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    parse_s = time.time() - t1

    out = {
        "feed": name,
        "url": url,
        "bytes": len(resp.content),
        "fetch_seconds": round(fetch_s, 3),
        "parse_seconds": round(parse_s, 4),
        "header": {
            "gtfs_realtime_version": feed.header.gtfs_realtime_version,
            "incrementality": feed.header.incrementality,
            "timestamp": feed.header.timestamp,
        },
        "entities": {"trip_update": 0, "vehicle": 0, "alert": 0},
        "trip_update_fields": {"trip_id": 0, "route_id": 0, "start_date": 0,
                               "with_stop_time_updates": 0, "with_delay": 0, "with_event_times": 0},
        "vehicle_fields": {"trip_id": 0, "route_id": 0, "position": 0, "timestamp": 0,
                           "stop_id": 0, "current_status": 0, "occupancy": 0},
        "alert_fields": {"header_text": 0, "informed_route": 0, "active_period": 0},
        "sample_route_ids": [],
        "sample_trip_ids": [],
        "sample_vehicle_trip_ids": [],
    }
    routes, trips, vtrip = set(), set(), set()
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            out["entities"]["trip_update"] += 1
            f = out["trip_update_fields"]
            if tu.trip.trip_id:
                f["trip_id"] += 1
                trips.add(tu.trip.trip_id)
            if tu.trip.route_id:
                f["route_id"] += 1
                routes.add(tu.trip.route_id)
            if tu.trip.start_date:
                f["start_date"] += 1
            if tu.stop_time_update:
                f["with_stop_time_updates"] += 1
            for stu in tu.stop_time_update:
                if stu.HasField("arrival") or stu.HasField("departure"):
                    f["with_event_times"] += 1
                    ev = stu.departure if stu.HasField("departure") else stu.arrival
                    if ev.HasField("delay"):
                        f["with_delay"] += 1
                    break
        elif entity.HasField("vehicle"):
            v = entity.vehicle
            out["entities"]["vehicle"] += 1
            f = out["vehicle_fields"]
            if v.trip.trip_id:
                f["trip_id"] += 1
                vtrip.add(v.trip.trip_id)
            if v.trip.route_id:
                f["route_id"] += 1
                routes.add(v.trip.route_id)
            if v.HasField("position"):
                f["position"] += 1
            if v.timestamp:
                f["timestamp"] += 1
            if v.stop_id:
                f["stop_id"] += 1
            if v.HasField("current_status"):
                f["current_status"] += 1
            if v.HasField("occupancy_status"):
                f["occupancy"] += 1
        elif entity.HasField("alert"):
            a = entity.alert
            out["entities"]["alert"] += 1
            f = out["alert_fields"]
            if a.HasField("header_text"):
                f["header_text"] += 1
            if any(e.route_id for e in a.informed_entity):
                f["informed_route"] += 1
            if a.active_period:
                f["active_period"] += 1
    out["sample_route_ids"] = sorted(routes)[:12]
    out["sample_trip_ids"] = sorted(trips)[:12]
    out["sample_vehicle_trip_ids"] = sorted(vtrip)[:12]
    out["all_route_ids"] = sorted(routes)
    out["all_trip_ids"] = sorted(trips)
    out["all_vehicle_trip_ids"] = sorted(vtrip)
    out["distinct_route_ids"] = len(routes)
    out["distinct_trip_update_trip_ids"] = len(trips)
    out["distinct_vehicle_trip_ids"] = len(vtrip)
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    names = list(FEEDS) if which == "both" else [which]
    print(json.dumps([analyze(n, FEEDS[n]) for n in names], indent=1))
