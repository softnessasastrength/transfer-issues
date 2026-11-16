#!/usr/bin/env python3
"""Transit Atlas terminal UI — one panel for the local stack.

Two faces, one set of helpers:

* a full-screen curses interface (dashboard, departures board, trip
  planner, services, Percival chat launcher) when curses is available
  and both stdin/stdout are TTYs;
* the original plain-text menu otherwise (piped output, dumb
  terminals, Windows consoles without curses), so the tool never
  hard-fails.

Everything shown comes from the real local Atlas API
(http://127.0.0.1:8000) or the real data directory — no transit
service is fabricated here.

Warm-up rule (learned the hard way, 2026-11-15): server.py warms its
routing caches *before* it starts listening, so a freshly started
server can be alive as a process while the port still refuses
connections.  Nothing in this file talks to the API — chat,
departures, plans — until /api/v1/meta has actually answered.
"""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import urlopen

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = pathlib.Path(os.environ.get('ATLAS_DATA_DIR', ROOT / 'data'))
ATLAS_BASE = os.environ.get('ATLAS_URL', 'http://127.0.0.1:8000')
OLLAMA_BASE = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434')
META_URL = ATLAS_BASE + '/api/v1/meta'
SERVER_LOG = 'atlas-tui-server.log'
OLLAMA_LOG = 'atlas-tui-ollama.log'
# The server warms the full routing network before listening; on a
# full regional database that is measured in tens of seconds, and a
# cold first plan can take longer still.  Wait generously, report
# progress while waiting, and never pretend a dead server is up.
WARMUP_TIMEOUT = float(os.environ.get('ATLAS_TUI_WARMUP_TIMEOUT', '240'))

server = None
server_log = None
ollama = None
ollama_log = None


def model_name():
    return os.environ.get('OLLAMA_MODEL', 'qwen3:1.7b')


# ---------------------------------------------------------------------------
# Small pure helpers (unit-tested without curses or a network)
# ---------------------------------------------------------------------------

def fmt_clock(seconds):
    """Service-day seconds -> HH:MM (hours may exceed 23, GTFS-style)."""
    seconds = int(seconds)
    return f'{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}'


def fmt_duration(seconds):
    seconds = int(round(seconds))
    if seconds < 60:
        return f'{seconds} sec'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes} min'
    return f'{minutes // 60} h {minutes % 60:02d} min'


def fmt_bytes(count):
    if count is None:
        return 'absent'
    value = float(count)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if value < 1024 or unit == 'TB':
            return f'{value:.0f} {unit}' if unit == 'B' else f'{value:.1f} {unit}'
        value /= 1024


def parse_time_input(text):
    """'8:30' / '08:30' / '830' / '8' -> seconds since midnight, or None."""
    text = (text or '').strip()
    if not text:
        return None
    try:
        if ':' in text:
            hours, minutes = text.split(':', 1)
            hours, minutes = int(hours), int(minutes)
        elif text.isdigit() and len(text) > 2:
            hours, minutes = int(text[:-2]), int(text[-2:])
        else:
            hours, minutes = int(text), 0
    except ValueError:
        return None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 3600 + minutes * 60


def route_label(route_id):
    """'cttransit:16545' -> 'cttransit:16545' (ids are the honest label)."""
    return route_id or ''


def format_stop_label(stop):
    name = stop.get('name') or stop.get('id') or '(unnamed stop)'
    return f'{name}  [{stop.get("id", "")}]'


def format_departure_rows(departures, limit=None):
    """Departures API rows -> display lines, earliest first."""
    rows = sorted(departures, key=lambda d: d.get('departure', 0))
    lines = []
    for dep in rows:
        headsign = dep.get('headsign') or ''
        route = route_label(dep.get('route'))
        lines.append(f"{fmt_clock(dep.get('departure', 0))}  {route:<18} {headsign}".rstrip())
    if limit is not None:
        lines = lines[:limit]
    return lines


def format_plan_lines(result, names=None):
    """Plan API result -> readable itinerary lines.

    `names` maps stop ids to display names for the stops the caller
    already knows (origin/destination picks); other stops are shown
    by their id, which is honest rather than invented.
    """
    names = names or {}
    if not result.get('found'):
        return [result.get('message') or 'No itinerary found in the loaded feeds.']
    lines = []
    departure, arrival = result.get('departure'), result.get('arrival')
    if departure is not None and arrival is not None:
        lines.append(f'Depart {fmt_clock(departure)}  →  Arrive {fmt_clock(arrival)}'
                     f'   ({fmt_duration(arrival - departure)})')
    for leg in result.get('legs', []):
        start = names.get(leg.get('from_stop'), leg.get('from_stop', ''))
        end = names.get(leg.get('to_stop'), leg.get('to_stop', ''))
        when = f"{fmt_clock(leg.get('departure', 0))}–{fmt_clock(leg.get('arrival', 0))}"
        if leg.get('kind') == 'transit':
            headsign = leg.get('headsign') or ''
            lines.append(f'{when}  {route_label(leg.get("route"))}  {start} → {end}'
                         + (f'  (toward {headsign})' if headsign else ''))
        else:
            metres = leg.get('meters')
            walk = f'  ({int(metres)} m, estimated)' if metres is not None else '  (estimated)'
            lines.append(f'{when}  {leg.get("kind", "walk")}  {start} → {end}{walk}')
    fare = result.get('fare')
    fare_line = format_fare_line(fare)
    if fare_line:
        lines.append(fare_line)
    if result.get('status'):
        lines.append(result['status'])
    return lines


def format_fare_line(fare):
    """Best-effort one-line fare summary; None when nothing is known."""
    if not isinstance(fare, dict):
        return None
    for key in ('label', 'summary', 'display'):
        if fare.get(key):
            return f'Fare: {fare[key]}'
    total = fare.get('total')
    if isinstance(total, (int, float)):
        return f'Fare: ${total:.2f} (rough estimate)'
    return None


def feed_freshness(sources, today=None):
    """Summarise feed windows from /api/v1/meta sources.

    Returns dict(feeds, in_service, window_start, window_end) where the
    window is the widest span any feed covers and in_service counts the
    feeds whose [service_start, service_end] includes today — the same
    comparison database.coverage() makes.
    """
    today = today or datetime.date.today().strftime('%Y%m%d')
    starts = [s.get('service_start') for s in sources if s.get('service_start')]
    ends = [s.get('service_end') for s in sources if s.get('service_end')]
    in_service = sum(1 for s in sources
                     if (s.get('service_start') or '99999999') <= today <= (s.get('service_end') or '00000000'))
    return dict(feeds=len(sources), in_service=in_service,
                window_start=min(starts) if starts else None,
                window_end=max(ends) if ends else None)


def _pretty_day(yyyymmdd):
    if not yyyymmdd or len(yyyymmdd) != 8:
        return yyyymmdd or '?'
    return f'{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}'


def format_dashboard_lines(status):
    """Status dict -> dashboard lines (pure formatting)."""
    def mark(up):
        return 'up' if up else 'DOWN'
    lines = [
        f"Atlas API    {mark(status['atlas_up'])}   {ATLAS_BASE}",
        f"Ollama       {mark(status['ollama_up'])}   {OLLAMA_BASE}   model {status['model']}",
        f"Database     {status['db']}",
    ]
    fresh = status.get('freshness')
    if fresh:
        lines.append(f"Feeds        {fresh['feeds']} loaded, {fresh['in_service']} in service today")
        if fresh['window_start']:
            lines.append(f"Feed window  {_pretty_day(fresh['window_start'])} .. {_pretty_day(fresh['window_end'])}")
    elif status['atlas_up']:
        lines.append('Feeds        (meta response carried no source list)')
    else:
        lines.append('Feeds        unknown — Atlas API is down')
    lines.append(f'Data dir     {DATA}')
    return lines


class Menu:
    """A wrap-around selection list; pure logic, curses-free."""

    def __init__(self, items):
        self.items = list(items)
        self.index = 0

    @property
    def selected(self):
        return self.items[self.index] if self.items else None

    def move(self, delta):
        if self.items:
            self.index = (self.index + delta) % len(self.items)
        return self.selected

    def set(self, index):
        if self.items:
            self.index = max(0, min(index, len(self.items) - 1))
        return self.selected


def wait_for_api(opener, url=META_URL, timeout=WARMUP_TIMEOUT, interval=1.0,
                 progress=None, clock=time.monotonic, sleep=time.sleep):
    """Poll `url` until `opener(url)` succeeds or the deadline passes.

    The server warms caches before listening, so 'process started' is
    not 'API up'.  `progress(elapsed_seconds)` is called between polls
    when supplied.  Returns True/False — never raises for a refused
    connection.
    """
    deadline = clock() + timeout
    while True:
        try:
            opener(url)
            return True
        except Exception:
            pass
        remaining = deadline - clock()
        if remaining <= 0:
            return False
        if progress is not None:
            progress(timeout - remaining)
        sleep(min(interval, remaining))


# ---------------------------------------------------------------------------
# API access
# ---------------------------------------------------------------------------

class ApiError(Exception):
    """The Atlas API (or its absence) said something specific."""


def fetch_json(url, timeout=10):
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', 'replace')[:200] if exc.fp else ''
        raise ApiError(f'Atlas API returned HTTP {exc.code}: {detail or exc.reason}') from exc
    except URLError as exc:
        raise ApiError(f'Atlas API unreachable at {url} ({exc.reason})') from exc
    except json.JSONDecodeError as exc:
        raise ApiError(f'Atlas API returned non-JSON from {url}') from exc


def api_get(path, params=None, timeout=10):
    url = ATLAS_BASE + path
    if params:
        url += '?' + urlencode(params)
    return fetch_json(url, timeout=timeout)


def online(url, timeout=1):
    try:
        with urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


def collect_status():
    """Snapshot everything the dashboard shows, from real sources."""
    status = dict(atlas_up=False, ollama_up=online(OLLAMA_BASE + '/api/tags', timeout=1),
                  model=model_name(), freshness=None, db='absent')
    db_path = DATA / 'atlas.sqlite'
    if db_path.exists():
        status['db'] = f'{db_path}  ({fmt_bytes(db_path.stat().st_size)})'
    try:
        meta = fetch_json(META_URL, timeout=3)
        status['atlas_up'] = True
        if isinstance(meta, dict) and isinstance(meta.get('sources'), list):
            status['freshness'] = feed_freshness(meta['sources'])
    except ApiError:
        status['atlas_up'] = False
    return status


# ---------------------------------------------------------------------------
# Process management (shared by the plain menu and the curses UI)
# ---------------------------------------------------------------------------

def compact_status():
    atlas = '●' if online(META_URL) else '○'
    ollama_state = '●' if online(OLLAMA_BASE + '/api/tags') else '○'
    return f'Atlas {atlas}  Ollama {ollama_state}  Model {model_name()}'


def start_server_process(progress=None):
    """Start server.py if needed, then wait out the cache warm-up.

    Returns (ok, message).  ok=False means the API never answered —
    the message names the log to look at; no cause is invented.
    """
    global server, server_log
    if server and server.poll() is None:
        if online(META_URL):
            return True, 'Server is already running at ' + ATLAS_BASE
        ok = wait_for_api(lambda u: urlopen(u, timeout=2), progress=progress)
        return ok, ('Server finished warming up.' if ok else
                    f'Server process is running but the API did not answer within '
                    f'{int(WARMUP_TIMEOUT)}s. Log: {DATA / SERVER_LOG}')
    if online(META_URL):
        return True, 'Server is already running at ' + ATLAS_BASE
    DATA.mkdir(parents=True, exist_ok=True)
    server_log = open(DATA / SERVER_LOG, 'a', encoding='utf-8')
    server = subprocess.Popen([sys.executable, str(ROOT / 'server.py')], cwd=ROOT,
                              stdout=server_log, stderr=subprocess.STDOUT)
    ok = wait_for_api(lambda u: urlopen(u, timeout=2), progress=progress)
    if ok:
        return True, f'Server started at {ATLAS_BASE}'
    return False, (f'Server started but the API did not answer within {int(WARMUP_TIMEOUT)}s '
                   f'(it warms routing caches before listening). Log: {DATA / SERVER_LOG}')


def stop_server_process():
    global server, server_log
    if not server or server.poll() is not None:
        server = None
        return 'Server is not running (not started by this TUI).'
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
    if server_log:
        server_log.close()
        server_log = None
    server = None
    return 'Server stopped.'


def start_ollama_process():
    global ollama, ollama_log
    if ollama and ollama.poll() is None:
        return True, 'Ollama is already running.'
    if online(OLLAMA_BASE + '/api/tags'):
        return True, 'Ollama is already running outside the TUI.'
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        ollama_log = open(DATA / OLLAMA_LOG, 'a', encoding='utf-8')
        ollama = subprocess.Popen(['ollama', 'serve'], cwd=ROOT,
                                  stdout=ollama_log, stderr=subprocess.STDOUT)
        time.sleep(1)
        return True, f'Ollama started at {OLLAMA_BASE} (log: {DATA / OLLAMA_LOG})'
    except FileNotFoundError:
        return False, 'Ollama command not found. Install Ollama or start it outside the TUI.'


def stop_ollama_process():
    global ollama, ollama_log
    if not ollama or ollama.poll() is not None:
        ollama = None
        return 'TUI-started Ollama is not running.'
    ollama.terminate()
    try:
        ollama.wait(timeout=5)
    except subprocess.TimeoutExpired:
        ollama.kill()
        ollama.wait()
    if ollama_log:
        ollama_log.close()
        ollama_log = None
    ollama = None
    return 'Ollama stopped.'


def ensure_stack(progress=None):
    """Atlas API answering + Ollama up; the gate before chat/plans."""
    ok, message = start_server_process(progress=progress)
    if not ok:
        return False, message
    ollama_ok, ollama_message = start_ollama_process()
    if not ollama_ok:
        return False, ollama_message
    return True, 'Local stack ready.'


# ---------------------------------------------------------------------------
# Plain-text UI (fallback — the original menu, with the warm-up fix)
# ---------------------------------------------------------------------------

def clear_screen():
    if sys.stdin.isatty() and sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    input('\nPress Enter to return to the menu...')


def run(label, command):
    print(f'\n--- {label} ---')
    try:
        result = subprocess.run(command, cwd=ROOT, check=False)
        print(f'\n{label}: exit {result.returncode}')
    except KeyboardInterrupt:
        print('\nInterrupted.')
    pause()


def _plain_progress(elapsed):
    print(f'  …warming up ({int(elapsed)}s)', end='\r', flush=True)


def start_server(pause_after=True):
    ok, message = start_server_process(progress=_plain_progress)
    print(message)
    if pause_after:
        pause()
    return ok


def stop_server(pause_after=True):
    print(stop_server_process())
    if pause_after:
        pause()


def start_ollama(pause_after=True):
    ok, message = start_ollama_process()
    print(message)
    if pause_after:
        pause()
    return ok


def stop_ollama(pause_after=True):
    print(stop_ollama_process())
    if pause_after:
        pause()


def stack_status():
    print('\n--- Local AI stack ---')
    for label, url in [('Atlas API', META_URL), ('Ollama API', OLLAMA_BASE + '/api/tags')]:
        try:
            with urlopen(url, timeout=2) as response:
                print(f'{label:<12} online ({response.status})')
        except Exception as exc:
            print(f'{label:<12} offline ({exc.__class__.__name__})')
    try:
        result = subprocess.run(['ollama', 'list'], cwd=ROOT, check=False, text=True, capture_output=True)
        print('\nInstalled Ollama models:')
        print(result.stdout.strip() or '(none found)')
    except FileNotFoundError:
        print('Ollama CLI    not installed/on PATH')
    pause()


def chat_with_atlas():
    print(f'Launching Percival with {model_name()}. Type quit to return to the TUI.')
    run('Ollama MCP chat', [sys.executable, str(ROOT / 'scripts/ollama_mcp_chat.py'),
                            '--model', model_name()])


def android_environment():
    print('\n--- Android development environment ---')
    tools = [('Java', 'java'), ('Gradle', 'gradle'), ('ADB', 'adb'), ('SDK manager', 'sdkmanager')]
    for label, command in tools:
        found = shutil.which(command)
        print(f'{label:<14} {found or "missing"}')
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if sdk:
        sdk_path = pathlib.Path(sdk).expanduser()
        print(f'{"Android SDK":<14} {sdk_path} ({"present" if sdk_path.exists() else "missing directory"})')
    else:
        print('Android SDK    ANDROID_HOME/ANDROID_SDK_ROOT is not set')
    project = ROOT / 'android'
    print(f'{"Percival app":<14} {"present" if (project / "app").is_dir() else "missing"}')
    print('\nChromeOS setup path:')
    print('  1. Enable Linux development environment in ChromeOS Settings.')
    print('  2. Install Android Studio, or the Android command-line tools, on the Linux side.')
    print('  3. Install Java 17, SDK platform 35 and build-tools through SDK Manager.')
    print('  4. Set ANDROID_HOME to the SDK directory and add its platform-tools to PATH.')
    print('  5. Connect a device with USB debugging, or create an emulator in Android Studio.')
    print('\nNo package or system changes are made by this menu.')
    pause()


def android_build():
    print('\n--- Android debug build ---')
    gradle = shutil.which('gradle') or shutil.which('./gradlew')
    if not gradle:
        print('Gradle is not on PATH. Install Android Studio/Gradle, then retry.')
        pause()
        return
    try:
        result = subprocess.run([gradle, ':app:assembleDebug'], cwd=ROOT / 'android', check=False)
        print(f'Android debug build: exit {result.returncode}')
        if result.returncode == 0:
            print(f'APK: {ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"}')
    except KeyboardInterrupt:
        print('\nInterrupted.')
    pause()


def android_menu():
    while True:
        print('''\n--- Android development ---
[1] Check Android toolchain
[2] Build debug APK
[3] Print ChromeOS setup path
[b] Back''')
        choice = input('Android: ').strip().lower()
        if choice == '1':
            android_environment()
        elif choice == '2':
            android_build()
        elif choice == '3':
            android_environment()
        elif choice == 'b':
            return
        else:
            print('Choose a listed option.')


def start_stack():
    print('\nStarting Atlas and Ollama...')
    ok, message = ensure_stack(progress=_plain_progress)
    print(message)
    if ok:
        print('Use Chat to talk to Percival.')
    pause()


def advanced_menu():
    while True:
        print('''\n--- Advanced controls ---
[1] Start web app
[2] Stop web app
[3] Prepare core feeds
[4] Prepare core + optional MTA/LIRR
[5] External smoke test
[6] External smoke test + routing
[7] Run tests
[8] Feed status
[9] Local AI stack status
[10] Start Ollama
[11] Chat with Atlas via Ollama
[12] Stop TUI-started Ollama
[13] Android development
[b] Back''')
        choice = input('Advanced: ').strip().lower()
        if choice == '1':
            start_server()
        elif choice == '2':
            stop_server()
        elif choice == '3':
            run('Core feed preparation', [sys.executable, str(ROOT / 'scripts/prepare_data.py')])
        elif choice == '4':
            run('Core + optional MTA preparation', [sys.executable, str(ROOT / 'scripts/prepare_data.py'), '--include-optional'])
        elif choice == '5':
            run('External smoke test', [sys.executable, str(ROOT / 'scripts/external_smoke.py')])
        elif choice == '6':
            run('External smoke test with routing', [sys.executable, str(ROOT / 'scripts/external_smoke.py'), '--routing', '--date', os.environ.get('ATLAS_DATE', '2026-11-17')])
        elif choice == '7':
            run('Python tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        elif choice == '8':
            status()
        elif choice == '9':
            stack_status()
        elif choice == '10':
            start_ollama()
        elif choice == '11':
            ok, message = ensure_stack(progress=_plain_progress)
            print(message)
            if ok:
                chat_with_atlas()
            else:
                pause()
        elif choice == '12':
            stop_ollama()
        elif choice == '13':
            android_menu()
        elif choice == 'b':
            return
        else:
            print('Choose a listed option.')


def status():
    print('\n--- Feed status ---')
    path = DATA / 'sources.json'
    if not path.exists():
        print('No feed registry yet. Run a prepare action.')
        pause()
        return
    for source in json.loads(path.read_text()):
        mark = 'optional' if source.get('optional') else 'core'
        print(f"{source['id']:<14} {source.get('status', 'unknown'):<18} {mark:<8} "
              f"{source.get('service_start', '')}..{source.get('service_end', '')}")
    pause()


def plain_main():
    while True:
        clear_screen()
        print('╭──────────────────────────────────────────────╮')
        print('│ PERCIVAL · local transit companion            │')
        print('╰──────────────────────────────────────────────╯')
        print(compact_status())
        print('')
        print('  [s] Start stack     [c] Chat')
        print('  [r] Refresh status   [d] Android dev')
        print('  [a] Advanced')
        print('  [q] Quit')
        try:
            choice = input('\n  percival> ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'
        if choice in ('s', 'start', '1'):
            start_stack()
        elif choice in ('c', 'chat', '2'):
            ok, message = ensure_stack(progress=_plain_progress)
            print(message)
            if ok:
                chat_with_atlas()
        elif choice in ('r', 'refresh', '3'):
            print('\n' + compact_status())
            time.sleep(1)
        elif choice in ('d', 'android', '5'):
            android_menu()
        elif choice in ('a', 'advanced', '4'):
            advanced_menu()
        elif choice in ('q', 'quit', '0'):
            stop_server_process()
            stop_ollama_process()
            print('Goodbye.')
            return
        else:
            print('Unknown command. Press a, c, r, s or q.')


# ---------------------------------------------------------------------------
# Curses UI
# ---------------------------------------------------------------------------

def curses_available():
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    try:
        import curses  # noqa: F401
        return True
    except Exception:
        return False


class CursesTui:
    """Full-screen UI.  All data flows through the module helpers above."""

    HEADER_H = 3
    FOOTER_H = 2

    def __init__(self, stdscr):
        import curses
        self.curses = curses
        self.scr = stdscr
        self.message = ''
        self._init_colours()
        curses.curs_set(0)
        stdscr.keypad(True)

    # -- drawing primitives -------------------------------------------------

    def _init_colours(self):
        curses = self.curses
        self.colour = {}
        if not curses.has_colors():
            return
        curses.start_color()
        try:
            curses.use_default_colors()
            background = -1
        except Exception:
            background = curses.COLOR_BLACK
        curses.init_pair(1, curses.COLOR_GREEN, background)
        curses.init_pair(2, curses.COLOR_YELLOW, background)
        curses.init_pair(3, curses.COLOR_RED, background)
        curses.init_pair(4, curses.COLOR_CYAN, background)
        self.colour = {'ok': curses.color_pair(1), 'warn': curses.color_pair(2),
                       'bad': curses.color_pair(3), 'dim': curses.color_pair(4)}

    def _put(self, y, x, text, attr=0):
        height, width = self.scr.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        try:
            self.scr.addnstr(y, x, text, max(0, width - x - 1), attr)
        except Exception:
            pass

    def header(self, title):
        curses = self.curses
        status = collect_status_cached(self)
        atlas = ('● up' if status['atlas_up'] else '○ down')
        ollama = ('● up' if status['ollama_up'] else '○ down')
        self._put(0, 0, ' PERCIVAL · Transit Atlas', curses.A_BOLD)
        self._put(0, 34, f'Atlas {atlas}   Ollama {ollama}   Model {status["model"]}',
                  self.colour.get('ok' if status['atlas_up'] else 'bad', 0))
        self._put(1, 0, '─' * 200)
        self._put(2, 0, f' {title}', curses.A_BOLD | self.colour.get('dim', 0))

    def footer(self, hints):
        height, _ = self.scr.getmaxyx()
        if self.message:
            self._put(height - 2, 0, ' ' + self.message, self.colour.get('warn', 0))
        self._put(height - 1, 0, ' ' + hints, self.curses.A_DIM)

    def body_lines(self, lines, offset=0, selected=None):
        height, _ = self.scr.getmaxyx()
        top = self.HEADER_H + 1
        bottom = height - self.FOOTER_H
        for i, line in enumerate(lines[offset:offset + (bottom - top)]):
            y = top + i
            attr = self.curses.A_REVERSE if selected is not None and offset + i == selected else 0
            self._put(y, 1, line, attr)

    # -- input primitives ----------------------------------------------------

    def prompt_text(self, label, initial=''):
        """One-line text entry in the footer area; None on Esc."""
        curses = self.curses
        height, width = self.scr.getmaxyx()
        text = initial
        curses.curs_set(1)
        try:
            while True:
                self._put(height - 2, 0, ' ' * (width - 2))
                self._put(height - 2, 1, f'{label}: {text}')
                self.scr.move(height - 2, len(label) + 3 + len(text))
                self.scr.refresh()
                key = self.scr.getch()
                if key in (10, 13, curses.KEY_ENTER):
                    return text
                if key == 27:
                    return None
                if key in (curses.KEY_BACKSPACE, 127, 8):
                    text = text[:-1]
                elif 32 <= key < 127:
                    text += chr(key)
        finally:
            curses.curs_set(0)

    def pick_stop(self, title):
        """Search -> pick a stop.  Returns the stop dict or None."""
        while True:
            query = self.prompt_text('Search stops (name)')
            if query is None:
                return None
            if not query.strip():
                self.message = 'Type part of a stop name to search.'
                return None
            try:
                result = api_get('/api/v1/stops', {'q': query, 'limit': 100}, timeout=15)
            except ApiError as exc:
                self.message = str(exc)
                return None
            stops = result.get('stops', [])
            if not stops:
                self.message = f'No stops match "{query}" in the loaded feeds.'
                return None
            labels = [format_stop_label(s) for s in stops]
            if result.get('truncated'):
                labels.append(f'… {result["match_count"]} matches in total — refine the search to see more')
            index = self.list_screen(title, labels, '↑/↓ choose · Enter select · Esc back')
            if index is None or index >= len(stops):
                return None
            return stops[index]

    def list_screen(self, title, lines, hints, selected=0):
        """Scrollable list; returns the chosen index or None on Esc/q."""
        curses = self.curses
        menu = Menu(lines)
        menu.set(selected)
        offset = 0
        while True:
            self.scr.erase()
            self.header(title)
            height, _ = self.scr.getmaxyx()
            visible = max(1, height - self.HEADER_H - self.FOOTER_H - 1)
            if menu.index < offset:
                offset = menu.index
            if menu.index >= offset + visible:
                offset = menu.index - visible + 1
            self.body_lines(lines, offset=offset, selected=menu.index)
            self.footer(hints)
            self.scr.refresh()
            key = self.scr.getch()
            if key in (curses.KEY_UP, ord('k')):
                menu.move(-1)
            elif key in (curses.KEY_DOWN, ord('j')):
                menu.move(1)
            elif key in (10, 13, curses.KEY_ENTER):
                return menu.index
            elif key in (27, ord('q')):
                return None

    def text_screen(self, title, lines, hints='↑/↓ scroll · Esc/q back'):
        """Scrollable read-only text; returns when the user backs out."""
        curses = self.curses
        offset = 0
        while True:
            self.scr.erase()
            self.header(title)
            height, _ = self.scr.getmaxyx()
            visible = max(1, height - self.HEADER_H - self.FOOTER_H - 1)
            offset = max(0, min(offset, max(0, len(lines) - visible)))
            self.body_lines(lines, offset=offset)
            self.footer(hints)
            self.scr.refresh()
            key = self.scr.getch()
            if key in (curses.KEY_UP, ord('k')):
                offset -= 1
            elif key in (curses.KEY_DOWN, ord('j')):
                offset += 1
            elif key == curses.KEY_NPAGE:
                offset += visible
            elif key == curses.KEY_PPAGE:
                offset -= visible
            elif key in (27, ord('q'), 10, 13):
                return

    def notice(self, title, text):
        self.text_screen(title, [text], hints='Enter/Esc back')

    def working(self, text):
        self.scr.erase()
        self.header('Working')
        self._put(self.HEADER_H + 2, 1, text)
        self._put(self.HEADER_H + 3, 1, '(the first plan on a cold date can take a while — '
                                        'this is the planner working, not a hang)')
        self.footer('please wait…')
        self.scr.refresh()

    # -- screens ---------------------------------------------------------------

    def dashboard(self):
        curses = self.curses
        items = ['Departures board', 'Plan a trip', 'Services (start / stop / prepare / logs)',
                 'Chat with Percival', 'Quit']
        menu = Menu(items)
        while True:
            status = collect_status()
            self._status_cache = status
            self.scr.erase()
            self.header('Dashboard')
            lines = format_dashboard_lines(status)
            for i, line in enumerate(lines):
                attr = 0
                if line.startswith('Atlas API') and not status['atlas_up']:
                    attr = self.colour.get('bad', 0)
                if line.startswith('Ollama') and not status['ollama_up']:
                    attr = self.colour.get('warn', 0)
                self._put(self.HEADER_H + 1 + i, 1, line, attr)
            top = self.HEADER_H + 2 + len(lines)
            for i, item in enumerate(items):
                attr = curses.A_REVERSE if i == menu.index else 0
                self._put(top + i, 3, ('› ' if i == menu.index else '  ') + item, attr)
            self.footer('↑/↓ choose · Enter select · r refresh · q quit')
            self.scr.refresh()
            key = self.scr.getch()
            if key in (curses.KEY_UP, ord('k')):
                menu.move(-1)
            elif key in (curses.KEY_DOWN, ord('j')):
                menu.move(1)
            elif key == ord('r'):
                continue
            elif key in (10, 13, curses.KEY_ENTER):
                choice = menu.selected
                if choice == 'Quit':
                    return
                if choice == 'Departures board':
                    self.departures()
                elif choice == 'Plan a trip':
                    self.plan()
                elif choice.startswith('Services'):
                    self.services()
                elif choice == 'Chat with Percival':
                    self.chat()
            elif key in (ord('q'), 27):
                return

    def departures(self):
        stop = self.pick_stop('Departures — choose a stop')
        if stop is None:
            return
        self._departures_board(stop, datetime.date.today())

    def _departures_board(self, stop, day):
        curses = self.curses
        offset = 0
        while True:
            try:
                result = api_get('/api/v1/departures',
                                 {'stop': stop['id'], 'date': day.isoformat()}, timeout=30)
                rows = result.get('departures', [])
                error = None
            except ApiError as exc:
                rows, error = [], str(exc)
            lines = [f"{stop.get('name', stop['id'])}  [{stop['id']}] — {day.isoformat()}"]
            if error:
                lines.append(error)
            else:
                lines.append(f'{len(rows)} departures')
                lines += format_departure_rows(rows) or ['No departures on this date in the loaded feeds.']
            self.scr.erase()
            self.header('Departures')
            height, _ = self.scr.getmaxyx()
            visible = max(1, height - self.HEADER_H - self.FOOTER_H - 1)
            offset = max(0, min(offset, max(0, len(lines) - visible)))
            self.body_lines(lines, offset=offset)
            self.footer('↑/↓ scroll · n next day · p previous day · Esc/q back')
            self.scr.refresh()
            key = self.scr.getch()
            if key in (curses.KEY_UP, ord('k')):
                offset -= 1
            elif key in (curses.KEY_DOWN, ord('j')):
                offset += 1
            elif key == ord('n'):
                day += datetime.timedelta(days=1)
                offset = 0
            elif key == ord('p'):
                day -= datetime.timedelta(days=1)
                offset = 0
            elif key in (27, ord('q')):
                return

    def plan(self):
        origin = self.pick_stop('Plan — from which stop?')
        if origin is None:
            return
        destination = self.pick_stop('Plan — to which stop?')
        if destination is None:
            return
        now = datetime.datetime.now()
        default = f'{now.hour:02d}:{now.minute:02d}'
        while True:
            text = self.prompt_text('Depart at (HH:MM)', initial=default)
            if text is None:
                return
            seconds = parse_time_input(text)
            if seconds is not None:
                break
            self.message = f'"{text}" is not a time — use HH:MM, e.g. 08:30.'
            self.notice('Plan', self.message)
        day = datetime.date.today().isoformat()
        self.working(f'Planning {origin.get("name", origin["id"])} → '
                     f'{destination.get("name", destination["id"])} at {fmt_clock(seconds)}…')
        try:
            # Cold first plans on a new date can take minutes on the
            # full regional database; the timeout is generous on
            # purpose (slow is fine, wrong is not).
            result = api_get('/api/v1/plan',
                             {'from': origin['id'], 'to': destination['id'],
                              'date': day, 'time': seconds, 'kind': 'depart'},
                             timeout=600)
        except ApiError as exc:
            self.message = str(exc)
            self.notice('Plan', f'Planning failed: {exc}')
            return
        names = {origin['id']: origin.get('name', origin['id']),
                 destination['id']: destination.get('name', destination['id'])}
        lines = [f"{origin.get('name', origin['id'])} → {destination.get('name', destination['id'])}"
                 f' · {day} · depart {fmt_clock(seconds)}', '']
        lines += format_plan_lines(result, names)
        self.text_screen('Plan', lines)

    def services(self):
        items = ['Start Atlas server', 'Stop Atlas server', 'Start Ollama', 'Stop Ollama',
                 'Prepare data (core feeds)', 'Prepare data (core + optional MTA/LIRR)',
                 'View server log', 'Back']
        while True:
            index = self.list_screen('Services', items, '↑/↓ choose · Enter select · Esc back')
            if index is None:
                return
            choice = items[index]
            if choice == 'Back':
                return
            if choice == 'Start Atlas server':
                self._start_server_curses()
            elif choice == 'Stop Atlas server':
                self.message = stop_server_process()
            elif choice == 'Start Ollama':
                self.message = start_ollama_process()[1]
            elif choice == 'Stop Ollama':
                self.message = stop_ollama_process()
            elif choice == 'Prepare data (core feeds)':
                self._run_external('Prepare data (core feeds)',
                                   [sys.executable, str(ROOT / 'scripts/prepare_data.py')])
            elif choice == 'Prepare data (core + optional MTA/LIRR)':
                self._run_external('Prepare data (core + optional)',
                                   [sys.executable, str(ROOT / 'scripts/prepare_data.py'),
                                    '--include-optional'])
            elif choice == 'View server log':
                self._view_log()

    def _start_server_curses(self):
        curses = self.curses
        self.scr.erase()
        self.header('Services')
        self._put(self.HEADER_H + 2, 1, 'Starting the Atlas server…')
        self._put(self.HEADER_H + 3, 1, 'The server warms its routing caches before it '
                                        'starts listening — this wait is the fix for the')
        self._put(self.HEADER_H + 4, 1, '"Atlas API is unavailable" race. Nothing talks '
                                        'to the API until /api/v1/meta answers.')
        self.scr.refresh()

        def progress(elapsed):
            self._put(self.HEADER_H + 6, 1, f'  …warming up ({int(elapsed)}s)')
            self.scr.refresh()

        ok, message = start_server_process(progress=progress)
        self.message = message

    def _run_external(self, label, command):
        """Run a long foreground command with curses suspended."""
        curses = self.curses
        curses.endwin()
        print(f'--- {label} ---')
        try:
            result = subprocess.run(command, cwd=ROOT, check=False)
            print(f'\n{label}: exit {result.returncode}')
        except KeyboardInterrupt:
            print('\nInterrupted.')
        input('\nPress Enter to return to the TUI...')
        self.scr.clear()
        self.scr.refresh()

    def _view_log(self):
        path = DATA / SERVER_LOG
        if not path.exists():
            self.notice('Server log', f'No server log yet at {path} '
                                      '(the server has not been started by this TUI).')
            return
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        tail = lines[-200:]
        self.text_screen(f'Server log — last {len(tail)} lines of {path.name}', tail)

    def chat(self):
        curses = self.curses
        self.scr.erase()
        self.header('Percival chat')
        self._put(self.HEADER_H + 2, 1, 'Making sure the local stack is up before launching chat…')
        self.scr.refresh()

        def progress(elapsed):
            self._put(self.HEADER_H + 4, 1, f'  …Atlas warming up ({int(elapsed)}s)')
            self.scr.refresh()

        ok, message = ensure_stack(progress=progress)
        if not ok:
            self.message = message
            self.notice('Percival chat', message)
            return
        curses.endwin()
        print(f'Launching Percival with {model_name()}. Type quit to return to the TUI.')
        try:
            subprocess.run([sys.executable, str(ROOT / 'scripts/ollama_mcp_chat.py'),
                            '--model', model_name()], cwd=ROOT, check=False)
        except KeyboardInterrupt:
            print('\nInterrupted.')
        input('\nPress Enter to return to the TUI...')
        self.scr.clear()
        self.scr.refresh()


def collect_status_cached(tui):
    """Header status: reuse the dashboard's last snapshot when present."""
    status = getattr(tui, '_status_cache', None)
    if status is None:
        status = collect_status()
        tui._status_cache = status
    return status


def curses_main(stdscr):
    tui = CursesTui(stdscr)
    tui.dashboard()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def should_use_curses(argv):
    """Curses only when asked-for environment supports it."""
    if '--plain' in argv or '--advanced' in argv:
        return False
    if os.environ.get('ATLAS_TUI_PLAIN'):
        return False
    return curses_available()


def main():
    if '--advanced' in sys.argv:
        advanced_menu()
        return
    if should_use_curses(sys.argv):
        import curses
        try:
            curses.wrapper(curses_main)
        except Exception as exc:
            # A curses failure must never strand the user without a UI.
            print(f'Full-screen UI failed ({exc.__class__.__name__}: {exc}); '
                  'falling back to the plain menu.')
            plain_main()
        # Leaving the TUI stops only what this TUI started.
        stop_server_process()
        stop_ollama_process()
        return
    plain_main()


if __name__ == '__main__':
    main()
