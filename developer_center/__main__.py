"""Transit Atlas Developer Command Center (curses or headless JSON)."""
from __future__ import annotations

import argparse
import curses
import json
import os
from pathlib import Path
import sys

from .adapters import COMMANDS, ROOT, run_action, snapshot
from .inspection import HELP, environment, git_inspection, log_preview, logs, pack_inspection


def menu(screen, output: Path, packs: Path) -> None:
    report_offset = 0
    page = "dashboard"
    log_index = 0
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
                  "D dashboard | T reports | G git | E env | L logs | P packs | H help",
                  "Logs/history: " + str(output),
                  "Recent recorded runs (not a current-tree certification):"]
        for record in state['history'][:3]:
            if not isinstance(record, dict) or 'exit_code' not in record:
                lines.append("Unreadable or incomplete history record; inspect --status")
            else:
                lines.append(f"{record.get('action', '?')}: exit {record['exit_code']} "
                             f"in {record.get('seconds', '?')}s "
                             f"at {record.get('started_utc', '?')}")
        if page == "reports":
            python = state['test_results']['python']
            android = state['test_results']['android']
            lines = ["LOCAL TEST AND APK EVIDENCE (historical; tree not verified)",
                     "D dashboard | arrows scroll | R refresh | Q quit", "",
                     f"Python: {python['status']} | {python.get('tests', '?')} tests",
                     f"Started: {python.get('started_utc', '?')}",
                     f"Commit: {python.get('commit') or 'unknown'}",
                     f"Working tree at start: {python.get('changes', 'unknown')!r}",
                     f"Log age: {python.get('age_seconds', '?')}s",
                     "", f"Android XML: {android['status']} | {android['tests']} tests",
                     f"Failures {android['failures']} | errors {android['errors']} | skipped {android['skipped']}",
                     android['provenance']]
            lines += [f"{Path(r['source']).name}: {r['tests']} tests, age {r['age_seconds']}s"
                      for r in android['reports']]
            lines += [f"Invalid: {r['source']} {r['detail']}" for r in android['issues']]
            for artifact in state['artifacts']:
                metadata = artifact['metadata']
                lines += ["", artifact['path'],
                          f"Metadata: {metadata['status']} | {metadata.get('application_id', '?')}",
                          f"Version: {metadata.get('version_name', '?')} ({metadata.get('version_code', '?')})",
                          "Adjacent metadata; not verified against APK bytes"]
        if page in ('git', 'environment', 'help', 'packs'):
            data = {'git': git_inspection, 'environment': environment,
                    'packs': lambda: pack_inspection(packs), 'help': lambda: HELP}[page]()
            lines = [f"{page.upper()} (read-only) | D dashboard | H help | Q quit", ""]
            for label, value in data.items():
                lines.append(label + ':')
                if isinstance(value, dict):
                    lines.extend(json.dumps(value, indent=2).splitlines())
                else:
                    lines.extend(str(value).splitlines() or ['(none)'])
                lines.append('')
        elif page == 'logs':
            available = logs(output)
            log_index = min(log_index, max(0, len(available) - 1))
            lines = ["LOG PREVIEW | left/right selects | arrows scroll | D dashboard | Q quit"]
            if available:
                preview = log_preview(output, available[log_index]['name'])
                lines += [f"Log {log_index + 1}/{len(available)}: {preview['name']}",
                          f"{preview['status']} | tail limited to 64 KiB | no files deleted", '']
                lines += preview.get('detail', preview['text']).splitlines()
            else:
                lines += ['No saved regular .log files. Run an operation from the dashboard.']
        if page != "dashboard":
            report_offset = min(report_offset, max(0, len(lines) - max(1, height - 1)))
        visible = lines[report_offset:] if page != "dashboard" else lines
        for row, line in enumerate(visible[:max(0, height - 1)]):
            try:
                screen.addnstr(row, 0, line, max(0, width - 1))
            except curses.error:
                pass
        screen.refresh()
        key = screen.getch()
        if key in (ord('q'), ord('Q')):
            return
        navigation = {'d': 'dashboard', 't': 'reports', 'g': 'git',
                      'e': 'environment', 'l': 'logs', 'p': 'packs', 'h': 'help', '?': 'help'}
        letter = chr(key).lower() if 0 <= key <= 255 else ''
        if letter in navigation:
            page = navigation[letter]
            report_offset = 0
        elif page != 'dashboard':
            if key == curses.KEY_DOWN:
                report_offset += 1
            elif key == curses.KEY_UP:
                report_offset = max(0, report_offset - 1)
            elif page == 'logs' and key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                log_index = max(0, log_index + (1 if key == curses.KEY_RIGHT else -1))
                report_offset = 0
            continue
        elif key == curses.KEY_DOWN:
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
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--status', action='store_true', help='Print dashboard JSON without running builds')
    modes.add_argument('--run', choices=COMMANDS, help='Run one fixed operation and save its result')
    modes.add_argument('--inspect', choices=('git', 'environment', 'logs', 'packs', 'help'), help='Read-only inspection JSON')
    modes.add_argument('--log', help='Preview one saved .log filename as safe JSON')
    parser.add_argument('--output', type=Path, default=Path(os.environ.get(
        'ATLAS_DEV_OUTPUT', str(ROOT / 'build/developer-center'))), help='Local log/history directory')
    parser.add_argument('--packs', type=Path, default=ROOT / 'build/lan-packs',
                        help='Existing local catalogue directory to validate (no downloads)')
    args = parser.parse_args()
    if args.inspect:
        data = {'git': git_inspection, 'environment': environment,
                'logs': lambda: logs(args.output), 'packs': lambda: pack_inspection(args.packs),
                'help': lambda: HELP}[args.inspect]()
        print(json.dumps(data, indent=2))
        return (0 if data['status'] == 'validated' else 1) if args.inspect == 'packs' else 0
    if args.log:
        try:
            result = log_preview(args.output, args.log)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'available' else 1
    if args.status:
        print(json.dumps(snapshot(output=args.output), indent=2))
        return 0
    if args.run:
        result = run_action(args.run, output=args.output)
        print(json.dumps(result.__dict__, indent=2))
        return result.exit_code if result.exit_code >= 0 else 128 - result.exit_code
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error('Interactive terminal required; use --status or --run')
    curses.wrapper(menu, args.output, args.packs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
