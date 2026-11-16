"""UConn / WRTD shared feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published archive's distinctive shapes:

- one shared Passio archive for two agencies: agency.txt carries a
  single record naming "University of Connecticut (UCONN / WRTD)" --
  UConn HuskyGO campus lines and WRTD's regional routes (671, 674,
  675/676, 991, 993) in a single feed, imported exactly once.
- a Passio export whose calendar.txt patterns span 2025-01-01 to
  2027-12-31 while feed_info.txt declares only the current rolling
  edition (2026-11-14 to 2026-12-15). The importer records the service
  window from the calendar data itself, so the recorded window is the
  wide one; the narrow declared edition is a republication commitment,
  not an importer clip.
- the academic calendar and a road-closure detour are expressed
  entirely as calendar_dates.txt removals (type 2): the regular
  weekday pattern is removed on a fall Tuesday while the detour
  pattern runs, and the detour pattern is removed on the December
  Tuesday when the regular pattern resumes.
- the 674 is a loop: one trip runs Willimantic -> Storrs ->
  Willimantic, visiting its origin stop twice.
- one published stop is referenced only by untimed stop_times rows,
  so it is not imported and no time is invented for it (the untimed
  rows are skipped and counted, never the trip).
- one service pattern has no active weekdays at all (the published
  archive's Red Line shape): its trips import as records but never
  produce a connection on any date.
"""
from contextlib import closing
import io
import json
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import database
import import_gtfs

ROOT = pathlib.Path(__file__).resolve().parents[1]

FIXTURE_FILES = {
    'agency.txt': (
        'agency_id,agency_name,agency_url,agency_timezone,agency_lang\n'
        '1541,University of Connecticut (UCONN / WRTD),https://transpo.uconn.edu/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'Passio Technologies,https://passiotech.com,en,20261114,20261215,20260917\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '9001,Storrs NZTC,41.8042,-72.2418\n'
        '9002,Willimantic Intermodal Center,41.7135,-72.2152\n'
        '9003,Norwich Transportation Center,41.5244,-72.0821\n'
        '9004,Roanoak Ave at Cameo Dr,41.7245,-72.2364\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '674,1541,674,Willimantic - Storrs,3\n'
        '991,1541,991,Willimantic - Norwich,3\n'
        'RED,1541,Red,Red Line,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '674,WKD,T_REG,Storrs NZTC,0\n'
        '674,DET,T_DET,Storrs NZTC,0\n'
        '674,WKD,T_LOOP,Willimantic Intermodal Center,0\n'
        '991,WKD,T_991,Norwich Transportation Center,0\n'
        'RED,NEVER,T_RED,Willimantic Intermodal Center,0\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint\n'
        'T_REG,08:00:00,08:00:00,9002,1,1\n'
        'T_REG,08:30:00,08:30:00,9001,2,1\n'
        'T_DET,08:05:00,08:05:00,9002,1,1\n'
        'T_DET,08:35:00,08:35:00,9001,2,1\n'
        # The 674 loop: out to Storrs and back in one trip. Stop 9004
        # is served only as an untimed intermediate on the return leg.
        'T_LOOP,09:00:00,09:00:00,9002,1,1\n'
        'T_LOOP,09:30:00,09:30:00,9001,2,1\n'
        'T_LOOP,,,9004,3,0\n'
        'T_LOOP,10:00:00,10:00:00,9002,4,1\n'
        'T_991,07:00:00,07:00:00,9002,1,1\n'
        'T_991,07:40:00,07:40:00,9003,2,1\n'
        'T_RED,12:00:00,12:00:00,9001,1,1\n'
        'T_RED,12:30:00,12:30:00,9002,2,1\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'WKD,1,1,1,1,1,0,0,20250101,20271231\n'
        'DET,1,1,1,1,1,0,0,20250101,20271231\n'
        'NEVER,0,0,0,0,0,0,0,20250101,20271231\n'
    ),
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        # Detour window: the regular pattern is removed, the detour runs.
        'WKD,20261117,2\n'
        # Switchover: the detour pattern is removed, the regular resumes.
        'DET,20261201,2\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class UconnRegistryTests(unittest.TestCase):
    def test_uconn_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'uconn']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The shared UConn/WRTD Passio archive -- the URL the FTA NTD
        # GTFS weblinks dataset lists for Windham Region Transit
        # District (NTD 10149) and Transitland's static_current for
        # f-university~of~connecticut. It is a different feed from
        # HART's own Passio archive (passio3.com/hart/...), and there
        # is no second, WRTD-only archive to import alongside it.
        self.assertEqual(
            entry['url'],
            'https://passio3.com/uconn/passioTransit/gtfs/google_transit.zip')
        self.assertIn('transpo.uconn.edu', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class UconnBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'uconn')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'uconn.zip').write_bytes(fixture_zip_bytes())
        for module in (import_gtfs, database):
            p = patch.object(module, 'DATA', self.data)
            p.start()
            self.addCleanup(p.stop)
        database.connections.cache_clear()
        self.addCleanup(database.connections.cache_clear)
        import io as _io, contextlib
        with contextlib.redirect_stdout(_io.StringIO()):
            import_gtfs.build()

    def test_import_counts_and_provenance(self):
        with closing(sqlite3.connect(self.data / 'atlas.sqlite')) as db:
            counts = {t: db.execute(
                f"SELECT COUNT(*) FROM {t} WHERE feed='uconn'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'uconn:%'"
            ).fetchone()[0]
        # Stop 9004 appears only as an untimed intermediate, so it is
        # not imported; every published trip imports, including the
        # never-active pattern's.
        self.assertEqual(counts, {'stops': 3, 'routes': 3, 'trips': 5})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        # One archive, one agency record, naming both agencies it
        # carries -- the shared feed is imported exactly once.
        self.assertEqual(len(source['agencies']), 1)
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'University of Connecticut (UCONN / WRTD)')
        # The recorded window comes from the calendar data, not from
        # feed_info's narrow rolling edition (20261114-20261215).
        self.assertEqual(source['service_start'], '20250101')
        self.assertEqual(source['service_end'], '20271231')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 3, 'trips': 5})
        self.assertEqual(source['validation']['warnings']
                         ['untimed_stop_times_skipped'], 1)
        self.assertEqual(source['validation']['errors'], {})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|uconn:' in r[4] and 0 <= r[0] < 86400]

    def test_detour_runs_while_regular_pattern_removed(self):
        # Tuesday 2026-11-17: the regular weekday pattern is removed
        # by exception, so only the detour trip connects; the loop and
        # the 991 ride the removed pattern and stay home, and the
        # never-active pattern's trip never connects on any date.
        on = self.same_day('2026-11-17')
        det = [r for r in on if r[4].endswith('|uconn:T_DET')]
        self.assertEqual([(r[0], r[1]) for r in det],
                         [(8 * 3600 + 300, 8 * 3600 + 2100)])
        for trip in ('T_REG', 'T_LOOP', 'T_991', 'T_RED'):
            self.assertEqual(
                [r for r in on if r[4].endswith(f'|uconn:{trip}')], [])

    def test_regular_pattern_resumes_and_loop_survives_untimed_stop(self):
        # Tuesday 2026-12-01: the detour pattern is removed, the
        # regular pattern runs again, and the loop trip connects
        # across its skipped untimed stop in both directions.
        on = self.same_day('2026-12-01')
        reg = [r for r in on if r[4].endswith('|uconn:T_REG')]
        self.assertEqual([(r[0], r[1]) for r in reg],
                         [(8 * 3600, 8 * 3600 + 1800)])
        self.assertEqual(
            [r for r in on if r[4].endswith('|uconn:T_DET')], [])
        loop = [r for r in on if r[4].endswith('|uconn:T_LOOP')]
        self.assertEqual([(r[0], r[1]) for r in loop],
                         [(9 * 3600, 9 * 3600 + 1800),
                          (9 * 3600 + 1800, 10 * 3600)])
        self.assertEqual(
            [r for r in on if r[4].endswith('|uconn:T_RED')], [])


if __name__ == '__main__':
    unittest.main()
