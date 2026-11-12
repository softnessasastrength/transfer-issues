"""Local-network development server for Android and browser clients.

Explicit LAN binding; no public hosting, accounts, GPS logging or auto downloads.
"""
import argparse
import hashlib
import json
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server
from scripts.build_lan_packs import build

ROOT = Path(__file__).resolve().parent
PACKS = ROOT / "build/lan-packs"
NAMES = {"cttransit", "hartford", "pvta", "amtrak"}


class Handler(server.Handler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/v1/packs/catalog":
            file = PACKS / "catalog.json"
            if not file.is_file():
                return self.reply(503, {"error": "Build local packs first"})
            return self.reply(200, json.loads(file.read_text()))
        if path.startswith("/api/v1/packs/download/"):
            name = path.removeprefix("/api/v1/packs/download/")
            if name not in NAMES:
                return self.reply(404, {"error": "Unknown agency"})
            catalog = json.loads((PACKS / "catalog.json").read_text())
            entry = catalog["packages"].get(name)
            if not entry:
                return self.reply(404, {"error": "Agency feed unavailable"})
            file = PACKS / entry["filename"]
            if not file.is_file() or file.stat().st_size != entry["bytes"]:
                return self.reply(503, {"error": "Package missing or changed"})
            # Stream only files enumerated in the generated catalog.
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(file.stat().st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with file.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    self.wfile.write(chunk)
            return
        return super().do_GET()

    def reply(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Avoid printing request paths/queries that might include personal locations.
        print("LAN request status:", args[1] if len(args) > 1 else "unknown")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--build-packs", action="store_true")
    args = parser.parse_args()
    if args.build_packs:
        result = build(ROOT / "data/atlas.sqlite", PACKS)
        print("Pack coverage:", sorted(result["packages"]), "missing:", result["missing_agencies"])
    print(f"Transit Atlas LAN dev: http://{args.host}:{args.port} (Ctrl+C to stop)", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
