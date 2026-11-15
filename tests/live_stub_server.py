#!/usr/bin/env python3
"""Fixture-backed live-data stub for browser verification of the live overlay.

TEST TOOLING ONLY — never imported by the shipped app. It monkeypatches
live.py's two fetch seams with deterministic fixture payloads and serves the
real Atlas server, so browser passes can verify fresh / stale / unavailable
live behaviour without depending on the real internet (tests/AGENTS.md).

Mode is read from the file named by LIVE_STUB_MODE_FILE (default
/tmp/live_stub_mode) on every request: "fresh", "stale", or "down".
Run: ATLAS_DATA_DIR=<data dir> python3 tests/live_stub_server.py [port]
"""
import os
import sys
import time
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import live  # noqa: E402

MODE_FILE = os.environ.get("LIVE_STUB_MODE_FILE", "/tmp/live_stub_mode")


def _mode() -> str:
    try:
        return open(MODE_FILE).read().strip() or "fresh"
    except OSError:
        return "fresh"


def _ct_payload(kind: str, mode: str) -> dict:
    now = int(time.time())
    ts = now if mode == "fresh" else now - 25 * 60
    if kind == "trips":
        return {"header": {"timestamp": ts}, "entity": [
            {"id": "t1", "trip_update": {"trip": {"route_id": "905", "trip_id": "stub1"},
             "stop_time_update": [{"stop_id": "HFD", "departure": {"time": now + 12 * 60, "delay": 0}}]}}]}
    if kind == "vehicles":
        return {"header": {"timestamp": ts}, "entity": [
            {"id": "cv1", "vehicle": {"trip": {"route_id": "905"}, "vehicle": {"id": "CT-101"},
             "position": {"latitude": 41.767, "longitude": -72.674, "bearing": 90}, "timestamp": ts}},
            {"id": "cv2", "vehicle": {"trip": {"route_id": "47"}, "vehicle": {"id": "CT-102"},
             "position": {"latitude": 41.762, "longitude": -72.681, "bearing": 180}, "timestamp": ts}},
            {"id": "cv3", "vehicle": {"trip": {"route_id": "905"}, "vehicle": {"id": "CT-103"},
             "position": {"latitude": 41.772, "longitude": -72.665, "bearing": 45}, "timestamp": ts}},
        ]}
    return {"entity": []}


def _mbta_payload(path: str, mode: str) -> dict:
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    ts = now if mode == "fresh" else now - _dt.timedelta(minutes=25)
    iso = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    if path == "/predictions":
        dep = (now + _dt.timedelta(minutes=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"data": [{"id": "p1", "attributes": {"departure_time": dep, "status": "On time"},
                          "relationships": {"route": {"data": {"id": "Red"}}}}]}
    if path == "/vehicles":
        return {"data": [
            {"id": "mv1", "attributes": {"label": "1709", "latitude": 42.365, "longitude": -71.062,
             "bearing": 10, "current_status": "IN_TRANSIT_TO", "updated_at": iso},
             "relationships": {"route": {"data": {"id": "Red"}}, "stop": {"data": {"id": "place-pktrm"}}}},
            {"id": "mv2", "attributes": {"label": "1711", "latitude": 42.352, "longitude": -71.055,
             "bearing": 200, "current_status": "STOPPED_AT", "updated_at": iso},
             "relationships": {"route": {"data": {"id": "Red"}}, "stop": {"data": {"id": "place-sstat"}}}},
        ]}
    return {"data": []}


def _stub_fetch(path, params, timeout=8.0):
    mode = _mode()
    if mode == "down":
        raise TimeoutError("stub: provider down")
    return _mbta_payload(path, mode), f"https://stub.invalid{path}"


def _stub_fetch_url(url, timeout=8.0):
    mode = _mode()
    if mode == "down":
        raise TimeoutError("stub: provider down")
    if "TripUpdate" in url:
        return _ct_payload("trips", mode)
    if "Vehicle" in url:
        return _ct_payload("vehicles", mode)
    return _ct_payload("alerts", mode)


live._fetch = _stub_fetch
live._fetch_url = _stub_fetch_url

import server  # noqa: E402


if __name__ == "__main__":
    import datetime
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8003
    day = os.environ.get("ATLAS_DATE", datetime.date.today().isoformat())
    print(f"Live stub server: warming caches for {day}...", flush=True)
    server.warm_caches(day)
    print(f"Live stub server: http://127.0.0.1:{port} (mode file {MODE_FILE})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), server.Handler).serve_forever()
