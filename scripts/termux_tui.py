#!/usr/bin/env python3
"""Transit Atlas Termux Command Center: dependency-free, opt-in terminal UI."""
import argparse
import curses
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = [
    ("System diagnostics", "doctor", ["bash", "termux-dev.sh", "check"], False),
    ("Import GTFS feeds (internet)", "prepare", ["bash", "termux-atlas.sh", "prepare"], True),
    ("Start loopback pack server", "serve", ["bash", "termux-atlas.sh", "serve"], True),
    ("Check localhost catalog", "check", ["bash", "termux-atlas.sh", "check"], False),
    ("Run Python regression tests", "test", ["bash", "termux-dev.sh", "test"], False),
    ("List wireless ADB devices", "adb", ["bash", "termux-dev.sh", "adb-devices"], False),
    ("Stream Android error logs", "logcat", ["bash", "termux-dev.sh", "logcat"], True),
]
ACTION_BY_KEY = {item[1]: item for item in ACTIONS}


def status_snapshot(root=ROOT):
    db = root / "data" / "atlas.sqlite"
    catalog = root / "build" / "lan-packs" / "catalog.json"
    return [
        ("GTFS database", f"{db.stat().st_size / 1048576:.1f} MiB" if db.is_file() else "NOT PREPARED"),
        ("Offline catalog", "READY" if catalog.is_file() else "NOT BUILT"),
        ("Python", shutil.which("python3") or "MISSING"),
        ("ADB", "AVAILABLE" if shutil.which("adb") else "OPTIONAL / MISSING"),
        ("Server", "127.0.0.1:8000 (manual start)"),
    ]


def safe_command(key):
    if key not in ACTION_BY_KEY:
        raise ValueError("Unknown command")
    return ACTION_BY_KEY[key][2]


def clipped(text, width):
    return text[:max(0, width - 1)]


def draw(stdscr, selected, lines, running=False):
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    if height < 19 or width < 54:
        stdscr.addstr(0, 0, clipped("Resize terminal to at least 54 x 19; Q quits.", width))
        stdscr.refresh()
        return
    def put(y, x, msg, attr=0):
        if 0 <= y < height and 0 <= x < width:
            try:
                stdscr.addnstr(y, x, msg, width - x - 1, attr)
            except curses.error:
                pass
    accent = curses.color_pair(1) | curses.A_BOLD
    put(0, 1, "╔" + "═" * (width - 4) + "╗", accent)
    put(1, 1, "║  TRANSIT ATLAS  //  TERMUX COMMAND CENTER", accent)
    put(2, 1, "╚" + "═" * (width - 4) + "╝", accent)
    put(3, 2, "LOCAL-FIRST  •  NO CLOUD  •  NO AUTOMATIC IMPORTS")
    put(5, 2, "SYSTEM TELEMETRY", accent)
    for i, (label, value) in enumerate(status_snapshot()):
        put(6 + i, 3, f"{label:<19} {clipped(value, width - 26)}")
    put(12, 2, "OPERATIONS", accent)
    for i, (label, key, _, dangerous) in enumerate(ACTIONS):
        prefix = "▶" if i == selected else " "
        attr = curses.A_REVERSE | curses.A_BOLD if i == selected else 0
        put(13 + i, 3, f"{prefix} {i + 1}. {label}" + ("  [CONFIRM]" if dangerous else ""), attr)
    log_top = 21
    if height > log_top + 3:
        put(log_top, 2, "LIVE OUTPUT / SESSION LOG", accent)
        for j, line in enumerate(lines[-(height - log_top - 4):]):
            put(log_top + 1 + j, 3, clipped(line.rstrip(), width - 5))
    put(height - 2, 2, "↑↓ select   ENTER run   R refresh   Q quit   Ctrl+C stop command")
    if running:
        put(height - 3, 2, "RUNNING: Ctrl+C stops the current process", accent)
    stdscr.refresh()


def execute(stdscr, command, lines):
    # All commands are hardcoded; never interpolate user input into a shell.
    lines.append(f"[{datetime.now():%H:%M:%S}] $ {' '.join(command)}")
    draw(stdscr, 0, lines, running=True)
    try:
        with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, bufsize=1,
                              start_new_session=True) as process:
            for line in process.stdout:
                lines.append(line.rstrip())
                if len(lines) > 400:
                    del lines[:-400]
                draw(stdscr, 0, lines, running=True)
            code = process.wait()
            lines.append(f"Process finished: exit {code}")
    except KeyboardInterrupt:
        lines.append("Interrupted by user. Stop any child process if still running.")
    except OSError as exc:
        lines.append(f"Launch failed: {exc}")


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
    selected = 0
    lines = ["No operations started. Select a command; destructive/network actions require confirmation."]
    while True:
        draw(stdscr, selected, lines)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break
        if key in (curses.KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(ACTIONS)
        elif key in (curses.KEY_UP, ord("k")):
            selected = (selected - 1) % len(ACTIONS)
        elif key in (10, 13, curses.KEY_ENTER):
            label, action, command, confirm = ACTIONS[selected]
            if confirm:
                lines.append(f"Confirm {label}: press Y to run, any other key cancels.")
                draw(stdscr, selected, lines)
                if stdscr.getch() not in (ord("y"), ord("Y")):
                    lines.append("Cancelled.")
                    continue
            if action in ("serve", "logcat"):
                curses.def_prog_mode()
                curses.endwin()
                print(f"\nStarting {label}. Ctrl+C to stop and return to the menu.\n")
                try:
                    subprocess.run(command, cwd=ROOT, check=False)
                except KeyboardInterrupt:
                    pass
                finally:
                    curses.reset_prog_mode()
                    stdscr.refresh()
                lines.append(f"{label} stopped.")
            else:
                execute(stdscr, command, lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Show operations without launching TUI")
    parser.add_argument("--run", choices=sorted(ACTION_BY_KEY), help="Run one known operation without TUI")
    args = parser.parse_args()
    if args.list:
        for label, key, _, _ in ACTIONS:
            print(f"{key:<9} {label}")
    elif args.run:
        if args.run in ("prepare", "serve", "logcat"):
            parser.error("Network/long-running operations require interactive TUI confirmation")
        sys.exit(subprocess.call(safe_command(args.run), cwd=ROOT))
    elif not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("Interactive terminal required; use --list or --run for headless checks")
    else:
        curses.wrapper(main)
