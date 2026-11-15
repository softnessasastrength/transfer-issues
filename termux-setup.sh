#!/usr/bin/env bash
# One-command interactive setup. No silent package installation or data downloads.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo "Python missing. In Termux run: pkg install python git sqlite" >&2; exit 1; }
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: bash termux-setup.sh [--help|--list]"
  exit 0
fi
if [[ "${1:-}" == "--list" ]]; then
  exec python3 scripts/termux_tui.py --list
fi
exec python3 scripts/termux_tui.py
