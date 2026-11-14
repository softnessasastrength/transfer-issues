#!/usr/bin/env bash
# Phone-local, explicitly invoked Transit Atlas GTFS pack server.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
HOST="127.0.0.1"
PORT="${ATLAS_TERMUX_PORT:-8000}"
case "$PORT" in ''|*[!0-9]*) echo "ATLAS_TERMUX_PORT must be numeric" >&2; exit 2;; esac
if (( PORT < 1024 || PORT > 65535 )); then echo "Use an unprivileged TCP port" >&2; exit 2; fi
command -v python3 >/dev/null || { echo "Install Termux Python: pkg install python" >&2; exit 1; }
python3 -c 'import sys,sqlite3; assert sys.version_info >= (3,11), "Python 3.11+ required"'
case "${1:-serve}" in
  serve)
    [[ -s data/atlas.sqlite ]] || { echo "Missing data/atlas.sqlite. Run bash atlas.sh once while online to import official feeds." >&2; exit 1; }
    python3 scripts/build_lan_packs.py --database data/atlas.sqlite --output build/lan-packs
    python3 scripts/verify_lan_catalog.py --packs build/lan-packs
    echo "Phone-only loopback server: http://127.0.0.1:$PORT"
    echo "In Transit Atlas debug APK, enter that URL and explicitly approve selected network downloads."
    echo "Keep Termux open until installation completes. Ctrl+C stops the server."
    exec python3 lan_server.py --host "$HOST" --port "$PORT"
    ;;
  prepare)
    echo "Importing official-first available feeds; internet required. Missing feeds remain missing."
    python3 scripts/prepare_data.py
    ;;
  check)
    python3 - "$PORT" <<'PY'
import json, sys, urllib.request
url = "http://127.0.0.1:" + sys.argv[1] + "/api/v1/packs/catalog"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        catalog = json.load(response)
    assert catalog["format"] == "transit-atlas-lan-v1"
    print("Available:", ", ".join(sorted(catalog["packages"])) or "none")
    print("Missing:", ", ".join(sorted(catalog["missing_agencies"])) or "none")
except Exception as exc:
    print("Loopback catalog unavailable:", exc, file=sys.stderr)
    sys.exit(1)
PY
    ;;
  *) echo "Usage: bash termux-atlas.sh [prepare|serve|check]" >&2; exit 2;;
esac
