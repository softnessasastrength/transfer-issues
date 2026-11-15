#!/usr/bin/env python3
"""Run a no-dependency smoke test from an ordinary terminal.

Usage:
  python3 scripts/external_smoke.py
  python3 scripts/external_smoke.py --routing --date 2026-11-17

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
        meta = json_request(base, "/api/v1/meta")
        check("metadata endpoint responds", meta.get("api_version") == "1.0")
        coverage = json_request(base, "/api/v1/coverage?date=" + urllib.parse.quote(args.date))
        check("coverage endpoint responds", isinstance(coverage, list))
        stops = json_request(base, "/api/v1/stops?q=Union%20Station")
        check("stop lookup responds", "stops" in stops and "match_count" in stops)
        pdfs = json_request(base, "/api/v1/pdf-schedules")
        check("PDF registry endpoint responds", "documents" in pdfs and "schedules" in pdfs)
        if args.routing:
            query = urllib.parse.urlencode({"from": "hartford:6", "to": "hartford:9", "date": args.date, "time": 28800, "radius": 0})
            plan = json_request(base, "/api/v1/plan?" + query)
            check("routing endpoint responds", "found" in plan, str(plan))
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
