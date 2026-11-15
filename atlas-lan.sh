#!/usr/bin/env bash
# Explicit opt-in LAN development launcher for Mac mini/Linux/Termux.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
HOST="${ATLAS_LAN_HOST:-0.0.0.0}"
PORT="${ATLAS_LAN_PORT:-8000}"
if [[ ! -f data/atlas.sqlite ]]; then
  echo "No GTFS database found. First run: bash atlas.sh (requires internet for initial import)." >&2
  exit 1
fi
echo "Building local agency packs from already-imported GTFS..."
python3 scripts/build_lan_packs.py --database data/atlas.sqlite --output build/lan-packs
echo "LAN server will listen on $HOST:$PORT."
echo "Use http://<YOUR-MAC-LAN-IP>:$PORT from Android on the same trusted Wi-Fi."
echo "Do not expose port $PORT to the internet; LAN server has no authentication."
exec python3 lan_server.py --host "$HOST" --port "$PORT"
