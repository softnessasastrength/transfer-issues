#!/usr/bin/env bash
# Southern New England Transit Atlas: safe one-command launcher for macOS/Linux/Termux.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
MODE="${1:-start}"
case "$MODE" in start|--setup|--refresh|--update|--help) ;; *) echo "Usage: bash atlas.sh [start|--setup|--refresh|--update|--help]" >&2; exit 2;; esac
if [[ "$MODE" == "--help" ]]; then
  printf '%s\n' 'bash atlas.sh             Start existing atlas (first run imports feeds)' 'bash atlas.sh --setup     Install Python on Termux if needed, then start' 'bash atlas.sh --refresh   Back up data, download feeds, rebuild, then start' 'bash atlas.sh --update    Fast-forward current Git branch, then start'
  exit 0
fi
if ! command -v python3 >/dev/null 2>&1; then
  if [[ "$MODE" == "--setup" ]] && command -v pkg >/dev/null 2>&1; then
    pkg install -y python
  else
    echo "Python 3.11+ is required. On Termux: pkg install python; on macOS: install Python 3.11+." >&2
    exit 1
  fi
fi
python3 -c 'import sys,sqlite3,ssl,zipfile; assert sys.version_info >= (3,11), "Python 3.11+ required"' || exit 1
if [[ "$MODE" == "--update" ]]; then
  command -v git >/dev/null || { echo "Install git first." >&2; exit 1; }
  if [[ -n "$(git status --porcelain)" ]]; then echo "Uncommitted changes: refusing automatic update. Commit or stash first." >&2; exit 1; fi
  git fetch origin
  git pull --ff-only
fi
mkdir -p data
if [[ "$MODE" == "--refresh" ]]; then
  if [[ -e data/atlas.sqlite ]]; then
    BACKUP="data-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP"
    cp -p data/atlas.sqlite "$BACKUP/"
    [[ ! -f data/sources.json ]] || cp -p data/sources.json "$BACKUP/"
    [[ ! -f data/validation.json ]] || cp -p data/validation.json "$BACKUP/"
    echo "Database and metadata backed up to $BACKUP"
  fi
fi
if [[ ! -f data/atlas.sqlite || "$MODE" == "--refresh" ]]; then
  echo "Preparing transit feeds. This can take a while and requires internet access."
  python3 scripts/prepare_data.py
fi
[[ -s data/atlas.sqlite ]] || { echo "No usable database was created." >&2; exit 1; }
# Avoid confusing address-in-use errors with a working existing instance.
if python3 - <<'PY'
import urllib.request
try:
 with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/meta',timeout=2) as r:
  assert r.status==200
except Exception:
 raise SystemExit(1)
PY
then
  echo "Atlas is already running at http://127.0.0.1:8000"
  exit 0
fi
echo "Atlas ready: http://127.0.0.1:8000"
echo "Leave this terminal open. Press Ctrl+C to stop."
exec python3 scripts/run_local.py
