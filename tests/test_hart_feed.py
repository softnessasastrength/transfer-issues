"""HART / HARTransit feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published HART archive's distinctive shapes:

- a Passio export whose calendar.txt patterns span 2025-01-01 to
  2027-12-31 while feed_info.txt declares only the current rolling
  edition (2026-11-14 to 2026-12-15). The importer records the service
  window from the calendar data itself, so the recorded window is the
  wide one; the narrow declared edition is a republication commitment,
  not an importer clip.
- stop_times that time only the timepoints: intermediate stops carry
  empty arrival/departure times (timepoint 0), which GTFS permits.
  The importer must skip those rows -- never drop the trip over them,
  and never invent a time for the stop -- while still rejecting a
  trip whose published time is malformed.
- split base services: the weekday pattern carries most routes, a
  second weekday pattern carries the LOOP routes, and the Sunday
  pattern is added on individual holidays by calendar_dates.txt
  (type 1) while the weekday pattern is removed on others (type 2).
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
        '2250,HARTransit,http://www.hartransit.com,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'Passio Technologies,https://passiotech.com,en,20261114,20261215,20260917\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '9001,Pulse Point,41.3965,-73.4560\n'
        '9002,Danbury Fair Mall,41.3810,-73.4815\n'
        '9003,Norwalk WHEELS Hub,41.1189,-73.4142\n'
        '9004,Branchville,41.2629,-73.4382\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '3261,2250,15,Danbury-Ridgefield-Norwalk 7 Link,3\n'
        '6312,2250,8,LOOP: Danbury Mall - Mill Plain,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '3261,WKD,T1,Norwalk WHEELS Hub,0\n'
        '6312,SUN,T2,Danbury Fair Mall,0\n'
        '3261,WKD,T3,Norwalk WHEELS Hub,0\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint\n'
        'T1,08:00:00,08:00:00,9001,1,1\n'
        # The published archive leaves non-timepoint stops untimed.
        'T1,,,9004,2,0\n'
        'T1,08:20:00,08:20:00,9002,3,1\n'
        'T1,09:10:00,09:10:00,9003,4,1\n'
        'T2,10:00:00,10:00:00,9001,1,1\n'
        'T2,10:15:00,10:15:00,9002,2,1\n'
        # A malformed published time is not an untimed stop: the trip
        # carrying it must still be rejected.
        'T3,11:00:00,11:00:00,9001,1,1\n'
        'T3,11:70:00,11:70:00,9002,2,1\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'WKD,1,1,1,1,1,0,0,20250101,20271231\n'
        'SUN,0,0,0,0,0,0,1,20250101,20271231\n'
    ),
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        'WKD,20261126,2\n'
        'SUN,20261127,1\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class HartRegistryTests(unittest.TestCase):
    def test_hart_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'hart']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # HARTransit's own Passio-hosted archive -- the URL the FTA
        # NTD GTFS weblinks dataset lists for Housatonic Area Regional
        # Transit (NTD 10051) and Transitland's static_current for
        # f-hartransit~ct~us. It is a different feed from the shared
        # UConn/WRTD Passio archive (passio3.com/uconn/...).
        self.assertEqual(
            entry['url'],
            'https://passio3.com/hart/passioTransit/gtfs/google_transit.zip')
        self.assertIn('hartransit.com', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class HartBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'hart')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'hart.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='hart'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'hart:%'"
            ).fetchone()[0]
        # Stop 9004 appears only as an untimed intermediate, so it is
        # not imported; T3 is excluded over its malformed time.
        self.assertEqual(counts, {'stops': 3, 'routes': 2, 'trips': 2})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        # The recorded window comes from the calendar data, not from
        # feed_info's narrow rolling edition (20261114-20261215).
        self.assertEqual(source['service_start'], '20250101')
        self.assertEqual(source['service_end'], '20271231')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 2, 'trips': 2})
        self.assertEqual(source['validation']['warnings']
                         ['untimed_stop_times_skipped'], 1)
        self.assertEqual(source['validation']['errors'],
                         {'invalid_or_missing_time': 1})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|hart:' in r[4] and 0 <= r[0] < 86400]

    def test_untimed_intermediate_does_not_break_the_trip(self):
        # On Tuesday 2026-11-17 the 7 Link trip runs across its skipped
        # untimed stop: the timed stops become adjacent connections.
        on = [r for r in self.same_day('2026-11-17')
              if r[4].endswith('|hart:T1')]
        self.assertEqual([(r[0], r[1]) for r in on],
                         [(8 * 3600, 8 * 3600 + 1200),
                          (8 * 3600 + 1200, 9 * 3600 + 600)])

    def test_weekday_service_removed_on_thanksgiving(self):
        thu = self.same_day('2026-11-26')
        self.assertEqual(
            [r for r in thu if r[4].endswith('|hart:T1')], [])

    def test_sunday_service_only_on_sunday_and_added_holiday(self):
        sun = self.same_day('2026-11-22')
        self.assertTrue(sun)
        self.assertTrue(all(r[4].endswith('|hart:T2') for r in sun))
        # The day after Thanksgiving is a Friday: the weekday trip
        # runs, and the Sunday pattern is added by exception, so the
        # LOOP trip runs too.
        fri = self.same_day('2026-11-27')
        self.assertTrue(any(r[4].endswith('|hart:T1') for r in fri))
        self.assertTrue(any(r[4].endswith('|hart:T2') for r in fri))


if __name__ == '__main__':
    unittest.main()
