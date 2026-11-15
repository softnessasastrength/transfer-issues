#!/usr/bin/env python3
"""Run a no-dependency smoke test from an ordinary terminal.

Usage:
  python3 scripts/external_smoke.py
  python3 scripts/external_smoke.py --routing --date 2026-11-17
  python3 scripts/external_smoke.py --outings --date 2026-11-14
  python3 scripts/external_smoke.py --regional --date 2026-11-16

This starts the same loopback server a user launches with run_local.py,
checks the page and read-only API, then shuts it down. It needs no Codex,
Node, Playwright, browser driver, or third-party Python package.
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]


def request(base, path):
    with urllib.request.urlopen(base + path, timeout=15) as response:
        body = response.read()
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} for {path}")
        return body


def json_request(base, path):
    return json.loads(request(base, path))


def check(label, condition, detail=""):
    if not condition:
        raise RuntimeError(f"FAIL: {label}" + (f" ({detail})" if detail else ""))
    print(f"PASS: {label}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--date", default=os.environ.get("ATLAS_DATE", datetime.date.today().isoformat()))
    parser.add_argument("--routing", action="store_true", help="also exercise a scheduled Hartford rail query")
    parser.add_argument("--outings", action="store_true", help="exercise the real-data Saturday outing workflow")
    parser.add_argument("--regional", action="store_true", help="exercise imported MNR, LIRR and Greyhound schedules; choose a covered date")
    args = parser.parse_args()
    data_dir = pathlib.Path(os.environ.get("ATLAS_DATA_DIR", ROOT / "data"))
    if not (data_dir / "atlas.sqlite").exists():
        print("No imported database found. Run: python3 scripts/prepare_data.py", file=sys.stderr)
        return 2
    base = f"http://127.0.0.1:{args.port}"
    env = os.environ.copy()
    env["ATLAS_DATE"] = args.date
    env["PORT"] = str(args.port)
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "server.py"), "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read().strip()
                raise RuntimeError(f"server exited with code {process.returncode}: {output}")
            try:
                request(base, "/")
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.25)
        else:
            raise RuntimeError("server did not become ready within 90 seconds")

        page = request(base, "/").decode("utf-8")
        check("homepage loads", '<script type="module" src="app.js">' in page)
        app = request(base, "/app.js").decode("utf-8")
        check("controller loads", "async function init()" in app)
        check("Outings UI loads", 'id="outingPlanner"' in page and "async function browseOutings()" in app)
        meta = json_request(base, "/api/v1/meta")
        check("metadata endpoint responds", meta.get("api_version") == "1.0")
        coverage = json_request(base, "/api/v1/coverage?date=" + urllib.parse.quote(args.date))
        check("coverage endpoint responds", isinstance(coverage, list))
        stops = json_request(base, "/api/v1/stops?q=Union%20Station")
        check("stop lookup responds", "stops" in stops and "match_count" in stops)
        pdfs = json_request(base, "/api/v1/pdf-schedules")
        check("PDF registry endpoint responds", "documents" in pdfs and "schedules" in pdfs)
        if args.regional:
            imported = {s['id'] for s in meta['sources'] if s.get('status') == 'imported'}
            check("regional feeds imported", {'mnr', 'lirr', 'greyhound'} <= imported)
            check("Connecticut city shortcuts exposed", {'Hartford', 'New Haven', 'Stamford', 'Bridgeport'} <= set(meta.get('ct_cities', [])))
            def stop_id(feed, name, latitude=None):
                matches = [s['id'] for s in meta['stops'] if s['feed'] == feed and s['name'] == name
                           and (latitude is None or abs(s['lat'] - latitude) < 0.1)]
                check(f"{feed} stop published: {name}", len(matches) == 1)
                return matches[0]
            query = urllib.parse.urlencode({
                "from": stop_id('mnr', 'New Haven'), "to": stop_id('lirr', 'Jamaica'), "date": args.date,
                "time": 28800, "home_by": 79200, "stay": 7200,
                "outbound_budget": 14400, "radius": 500, "buffer": 300,
            })
            outing = json_request(base, "/api/v1/outings?" + query)
            check("MNR to LIRR scheduled round trip", outing.get("status") == "verified", str(outing.get("reason")))
            query = urllib.parse.urlencode({
                "from": stop_id('greyhound', 'Hartford (Union Station)', 41.77),
                "to": stop_id('greyhound', 'Springfield Union Station', 42.11),
                "date": args.date, "time": 0, "deadline": 86400,
                "feeds": "greyhound",
            })
            trip = json_request(base, "/api/v1/plan?" + query)
            check("Greyhound UTC timetable routes", trip.get("found"), str(trip.get("message")))
        if args.routing:
            query = urllib.parse.urlencode({"from": "hartford:6", "to": "hartford:9", "date": args.date, "time": 28800, "radius": 0})
            plan = json_request(base, "/api/v1/plan?" + query)
            check("routing endpoint responds", "found" in plan, str(plan))
        if args.outings:
            query = urllib.parse.urlencode({
                "from": "hartford:6", "to": "hartford:5", "date": args.date,
                "time": 28800, "home_by": 79200, "stay": 7200,
                "outbound_budget": 3600, "radius": 500, "buffer": 300,
            })
            outing = json_request(base, "/api/v1/outings?" + query)
            check("Saturday outing is verified", outing.get("status") == "verified", str(outing.get("reason")))
            check("outing has exact outbound and return", outing.get("outbound", {}).get("found") and outing.get("return_trip", {}).get("found"))
            check("outing reaches home by deadline", outing.get("home_arrival", 10**9) <= 79200)
        print("External smoke test passed.")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"External smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
