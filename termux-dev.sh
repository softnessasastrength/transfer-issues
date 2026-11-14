#!/usr/bin/env bash
# Explicit local developer commands; no background services, uploads or automatic pairing.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
case "${1:-help}" in
  check)
    command -v python3 >/dev/null || { echo "Install Python: pkg install python" >&2; exit 1; }
    python3 -c 'import sys,sqlite3; assert sys.version_info >= (3,11)'
    command -v git >/dev/null || { echo "Install Git: pkg install git" >&2; exit 1; }
    git status --short
    echo "Termux development prerequisites available."
    ;;
  test)
    python3 -m unittest tests.test_termux_entrypoint tests.test_termux_pack_validation tests.test_lan_packs -v
    ;;
  adb-devices)
    command -v adb >/dev/null || { echo "Install Android platform tools in Termux first." >&2; exit 1; }
    adb devices -l
    ;;
  logcat)
    command -v adb >/dev/null || { echo "Install Android platform tools in Termux first." >&2; exit 1; }
    echo "Showing transient Android error logs. They may include sensitive data; review before sharing."
    echo "Press Ctrl+C to stop. Nothing is saved or uploaded by this script."
    exec adb logcat -v time '*:E'
    ;;
  help)
    echo "Usage: bash termux-dev.sh [check|test|adb-devices|logcat]"
    echo "ADB requires developer options, wireless debugging and manual pairing; never expose ADB to untrusted networks."
    ;;
  *) echo "Unknown command. Run bash termux-dev.sh help" >&2; exit 2;;
esac
