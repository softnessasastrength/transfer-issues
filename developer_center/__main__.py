"""Transit Atlas Developer Command Center (curses or headless JSON)."""
from __future__ import annotations

import argparse
import curses
import json
import os
from pathlib import Path
import sys

from .adapters import COMMANDS, ROOT, run_action, snapshot


def menu(screen, output: Path) -> None:
    selected = 0
    message = "No operation started. R refreshes; Q quits."
    actions = list(COMMANDS)
    while True:
        state = snapshot(output=output)
        screen.erase()
        height, width = screen.getmaxyx()
        lines = ["TRANSIT ATLAS DEVELOPER COMMAND CENTER",
                 f"Branch: {state['branch']}  Commit: {state['commit']}",
                 f"Free storage: {state['disk_free_bytes'] / 2**30:.1f} GiB",
                 "Tools: " + ", ".join(f"{k}={'OK' if v else 'missing'}" for k, v in state['tools'].items()),
                 f"APKs discovered: {len(state['artifacts'])}",
                 "Changes: " + (state['changes'].replace('\n', ' | ') or "clean"), ""]
        lines += [("> " if i == selected else "  ") + action for i, action in enumerate(actions)]
        lines += ["", message, "Enter run | arrows select | R refresh | Q quit",
                  "Logs/history: " + str(output),
                  "Recent recorded runs (not a current-tree certification):"]
        for record in state['history'][:3]:
            if not isinstance(record, dict) or 'exit_code' not in record:
                lines.append("Unreadable or incomplete history record; inspect --status")
            else:
                lines.append(f"{record.get('action', '?')}: exit {record['exit_code']} "
                             f"in {record.get('seconds', '?')}s "
                             f"at {record.get('started_utc', '?')}")
        for row, line in enumerate(lines[:max(0, height - 1)]):
            try:
                screen.addnstr(row, 0, line, max(0, width - 1))
            except curses.error:
                pass
        screen.refresh()
        key = screen.getch()
        if key in (ord('q'), ord('Q')):
            return
        if key == curses.KEY_DOWN:
            selected = (selected + 1) % len(actions)
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(actions)
        elif key in (10, 13, curses.KEY_ENTER):
            curses.def_prog_mode()
            curses.endwin()
            try:
                print(f"Running {actions[selected]}; output is saved in {output}. Ctrl+C interrupts.", flush=True)
                result = run_action(actions[selected], output=output)
                message = f"{result.action}: exit {result.exit_code}, {result.seconds}s; {result.log}"
            finally:
                curses.reset_prog_mode()
                screen.refresh()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', action='store_true', help='Print dashboard JSON without running builds')
    parser.add_argument('--run', choices=COMMANDS, help='Run one fixed operation and save its result')
    parser.add_argument('--output', type=Path, default=Path(os.environ.get(
        'ATLAS_DEV_OUTPUT', str(ROOT / 'build/developer-center'))), help='Local log/history directory')
    args = parser.parse_args()
    if args.status and args.run:
        parser.error('--status and --run are mutually exclusive')
    if args.status:
        print(json.dumps(snapshot(output=args.output), indent=2))
        return 0
    if args.run:
        result = run_action(args.run, output=args.output)
        print(json.dumps(result.__dict__, indent=2))
        return result.exit_code if result.exit_code >= 0 else 128 - result.exit_code
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error('Interactive terminal required; use --status or --run')
    curses.wrapper(menu, args.output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
