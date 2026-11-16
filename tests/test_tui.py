"""Terminal UI (scripts/atlas_tui.py): pure formatting/selection logic,
the server warm-up wait, and the non-TTY fallback decision.

No test here touches curses, a real server, or a real database: the
warm-up wait is exercised against a fake opener and a fake clock, and
the fallback decision against patched environment checks.
"""
import unittest
from unittest.mock import patch

import scripts.atlas_tui as tui


class FormattingTests(unittest.TestCase):
    def test_fmt_clock(self):
        self.assertEqual(tui.fmt_clock(0), '00:00')
        self.assertEqual(tui.fmt_clock(30900), '08:35')
        self.assertEqual(tui.fmt_clock(33428), '09:17')
        # GTFS-style overflow past midnight stays readable.
        self.assertEqual(tui.fmt_clock(90000), '25:00')

    def test_fmt_duration(self):
        self.assertEqual(tui.fmt_duration(45), '45 sec')
        self.assertEqual(tui.fmt_duration(2520), '42 min')
        self.assertEqual(tui.fmt_duration(4620), '1 h 17 min')

    def test_fmt_bytes(self):
        self.assertEqual(tui.fmt_bytes(None), 'absent')
        self.assertEqual(tui.fmt_bytes(512), '512 B')
        self.assertEqual(tui.fmt_bytes(856_506_368), '816.8 MB')

    def test_parse_time_input(self):
        self.assertEqual(tui.parse_time_input('8:30'), 30600)
        self.assertEqual(tui.parse_time_input('08:30'), 30600)
        self.assertEqual(tui.parse_time_input('830'), 30600)
        self.assertEqual(tui.parse_time_input('8'), 28800)
        self.assertIsNone(tui.parse_time_input('25:00'))
        self.assertIsNone(tui.parse_time_input('8:75'))
        self.assertIsNone(tui.parse_time_input('morning'))
        self.assertIsNone(tui.parse_time_input(''))

    def test_format_departure_rows_sorted(self):
        rows = [
            dict(departure=34200, route='cttransit:16508', headsign='Buckland Hills'),
            dict(departure=30900, route='cttransit:16545', headsign='Hartford'),
        ]
        lines = tui.format_departure_rows(rows)
        self.assertTrue(lines[0].startswith('08:35'))
        self.assertIn('cttransit:16545', lines[0])
        self.assertIn('Hartford', lines[0])
        self.assertTrue(lines[1].startswith('09:30'))

    def test_format_plan_lines_transit_and_walk(self):
        result = dict(
            found=True, departure=30900, arrival=33428,
            legs=[
                dict(kind='transit', route='cttransit:16545', headsign='Hartford',
                     from_stop='a:1', to_stop='b:2', departure=30900, arrival=32400),
                dict(kind='walk', from_stop='b:2', to_stop='c:3',
                     departure=32400, arrival=33428, meters=640, estimated=True),
            ],
            status='Scheduled feasibility only; transfers are estimates, not guarantees.')
        names = {'a:1': 'Bright Meadow Blvd', 'c:3': 'Court Square'}
        lines = tui.format_plan_lines(result, names)
        self.assertIn('Depart 08:35', lines[0])
        self.assertIn('Arrive 09:17', lines[0])
        self.assertIn('Bright Meadow Blvd', lines[1])
        # Unknown intermediate stop falls back to its id, never an invented name.
        self.assertIn('b:2', lines[1])
        self.assertIn('640 m, estimated', lines[2])
        self.assertIn('Court Square', lines[2])

    def test_format_plan_lines_not_found(self):
        lines = tui.format_plan_lines(dict(found=False, message='No itinerary found in the loaded feeds.'))
        self.assertEqual(lines, ['No itinerary found in the loaded feeds.'])

    def test_feed_freshness(self):
        sources = [
            dict(id='a', service_start='20260101', service_end='20261231'),
            dict(id='b', service_start='20250101', service_end='20250630'),
        ]
        fresh = tui.feed_freshness(sources, today='20261115')
        self.assertEqual(fresh['feeds'], 2)
        self.assertEqual(fresh['in_service'], 1)
        self.assertEqual(fresh['window_start'], '20250101')
        self.assertEqual(fresh['window_end'], '20261231')

    def test_dashboard_lines_when_down(self):
        status = dict(atlas_up=False, ollama_up=False, model='qwen3:1.7b',
                      freshness=None, db='absent')
        lines = tui.format_dashboard_lines(status)
        self.assertIn('DOWN', lines[0])
        self.assertIn('unknown — Atlas API is down', lines[-2])


class MenuTests(unittest.TestCase):
    def test_wrap_around(self):
        menu = tui.Menu(['a', 'b', 'c'])
        self.assertEqual(menu.selected, 'a')
        menu.move(-1)
        self.assertEqual(menu.selected, 'c')
        menu.move(1)
        self.assertEqual(menu.selected, 'a')
        menu.move(2)
        self.assertEqual(menu.selected, 'c')

    def test_empty_menu_is_safe(self):
        menu = tui.Menu([])
        self.assertIsNone(menu.selected)
        self.assertIsNone(menu.move(1))


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class WarmUpWaitTests(unittest.TestCase):
    def test_succeeds_after_refusals(self):
        # The diagnosed race: the port refuses while caches warm, then answers.
        clock = FakeClock()
        attempts = []

        def opener(url):
            attempts.append(clock.now)
            if len(attempts) < 4:
                raise ConnectionRefusedError('warm-up in progress')

        progress = []
        ok = tui.wait_for_api(opener, timeout=30, interval=2.0,
                              progress=progress.append, clock=clock, sleep=clock.sleep)
        self.assertTrue(ok)
        self.assertEqual(len(attempts), 4)
        self.assertEqual(len(progress), 3)

    def test_times_out_and_reports_false(self):
        clock = FakeClock()

        def opener(url):
            raise ConnectionRefusedError('never answers')

        ok = tui.wait_for_api(opener, timeout=10, interval=3.0,
                              clock=clock, sleep=clock.sleep)
        self.assertFalse(ok)
        self.assertGreaterEqual(clock.now, 10)

    def test_immediate_success(self):
        clock = FakeClock()
        ok = tui.wait_for_api(lambda url: object(), timeout=10,
                              clock=clock, sleep=clock.sleep)
        self.assertTrue(ok)
        self.assertEqual(clock.now, 0.0)


class FallbackDecisionTests(unittest.TestCase):
    def test_non_tty_never_uses_curses(self):
        with patch.object(tui, 'curses_available', return_value=False):
            self.assertFalse(tui.should_use_curses([]))

    def test_plain_flag_forces_fallback(self):
        with patch.object(tui, 'curses_available', return_value=True):
            self.assertFalse(tui.should_use_curses(['--plain']))
            self.assertFalse(tui.should_use_curses(['--advanced']))

    def test_env_var_forces_fallback(self):
        with patch.object(tui, 'curses_available', return_value=True), \
                patch.dict('os.environ', {'ATLAS_TUI_PLAIN': '1'}):
            self.assertFalse(tui.should_use_curses([]))

    def test_tty_with_curses_uses_curses(self):
        with patch.object(tui, 'curses_available', return_value=True), \
                patch.dict('os.environ', {}, clear=True):
            self.assertTrue(tui.should_use_curses([]))


if __name__ == '__main__':
    unittest.main()
