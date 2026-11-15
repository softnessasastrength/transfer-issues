#!/usr/bin/env python3
"""Run Percival's Atlas and MCP HTTP services together.

Loopback is the safe default. Pass --lan only when a phone or another trusted
device on the same private network needs to connect.
"""
import argparse
import pathlib
import signal
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Run Percival locally or on a trusted LAN")
    parser.add_argument("--lan", action="store_true", help="Bind Atlas and MCP HTTP to 0.0.0.0; keep this network private")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mcp-port", type=int, default=8765)
    args = parser.parse_args()
    host = "0.0.0.0" if args.lan else "127.0.0.1"
    if args.lan:
        print("WARNING: LAN mode exposes scheduled data and MCP tools to devices that can reach this host.")
        print("Use only on a trusted private network; no authentication is configured.")
    processes = [
        subprocess.Popen([sys.executable, str(ROOT / "server.py"), "--host", host, "--port", str(args.port)], cwd=ROOT),
        subprocess.Popen([sys.executable, str(ROOT / "scripts" / "atlas_mcp_http.py"), "--host", host, "--port", str(args.mcp_port)], cwd=ROOT),
    ]
    print("Percival Atlas: http://%s:%s" % (host, args.port), flush=True)
    print("Percival MCP:  http://%s:%s/mcp" % (host, args.mcp_port), flush=True)
    print("Press Control-C to stop both services.", flush=True)
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()
