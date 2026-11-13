#!/usr/bin/env bash
# Explicit developer workflow for Debian-based ChromeOS Crostini.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
usage() {
  printf '%s\n' 'Usage: bash crostini-dev.sh [doctor|test|serve|packs|android-test|android-build|adb-devices]'
}
case "${1:-doctor}" in
  doctor)
    for cmd in python3 git java; do
      if command -v "$cmd" >/dev/null 2>&1; then printf 'OK: %s\n' "$cmd"; else printf 'MISSING: %s\n' "$cmd"; fi
    done
    python3 -c 'import sys,sqlite3,ssl; print("Python",sys.version.split()[0], "SQLite",sqlite3.sqlite_version); assert sys.version_info >= (3,11), "Python 3.11+ required"'
    if command -v gradle >/dev/null 2>&1; then gradle --version | head -n 8; else echo "Gradle not found. CI uses Gradle 8.9; do not rely on the Debian apt Gradle version."; fi
    if command -v adb >/dev/null 2>&1; then adb version | head -n 1; else echo "ADB not installed (optional)."; fi
    ;;
  test)
    python3 -m unittest discover -s tests -p 'test_*.py' -v
    ;;
  serve)
    [[ -s data/atlas.sqlite ]] || { echo "Run bash atlas.sh to prepare data before serving." >&2; exit 1; }
    echo "Loopback-only local backend on http://127.0.0.1:8000"
    exec python3 scripts/run_local.py
    ;;
  packs)
    [[ -s data/atlas.sqlite ]] || { echo "No data/atlas.sqlite; run bash atlas.sh first." >&2; exit 1; }
    python3 scripts/build_lan_packs.py --database data/atlas.sqlite --output build/lan-packs
    if [[ -f scripts/verify_lan_catalog.py ]]; then
      python3 scripts/verify_lan_catalog.py --packs build/lan-packs
    else
      echo "WARNING: Optional Stage 2 pack validator not installed. Exported packs are not independently verified." >&2
    fi
    ;;
  android-test|android-build)
    command -v gradle >/dev/null || { echo "Install compatible Gradle 8.9; CI can build APK if local SDK unavailable." >&2; exit 1; }
    [[ -n "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}" ]] || { echo "Set ANDROID_HOME to an installed SDK with Android 35 build tools." >&2; exit 1; }
    if [[ "$1" == android-test ]]; then task=:app:testDebugUnitTest; else task=:app:assembleDebug; fi
    (cd android && gradle --no-daemon "$task")
    ;;
  adb-devices)
    command -v adb >/dev/null || { echo "Install adb: sudo apt install adb" >&2; exit 1; }
    exec adb devices -l
    ;;
  help|-h|--help) usage ;;
  *) usage >&2; exit 2 ;;
esac
