"""Norwalk Transit District feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published Norwalk archive's distinctive shape:
calendar.txt carries a single all-week base service id that no trip
uses, and every trip's service (weekday / Saturday / Sunday-and-holiday)
is enumerated date-by-date in calendar_dates.txt as type-1 additions --
weekdays through 2026-12-31, with Thanksgiving 2026-11-26 running the
Sunday/holiday service instead of the weekday one. feed_info.txt still
declares the window out to 2027-05-31 (its last rows are 2027 holiday
dates), so the import must honour the enumerated dates, not the
declared end.
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
        '10057,Norwalk Transit District,http://www.norwalktransit.com/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Norwalk Transit District,http://www.norwalktransit.com/,en,20261019,20270531\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '9001,Burnell Blvd Hub,41.1183,-73.4150\n'
        '9002,SoNo Station,41.0959,-73.4224\n'
        '9003,Norwalk Community College,41.1019,-73.4525\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '1,10057,1,Route 1: NCC - East Norwalk Station,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '1,26,T1,Norwalk Community College,0\n'
        '1,7,T2,Norwalk Community College,0\n'
        '1,8,T3,Norwalk Community College,0\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'T1,08:00:00,08:00:00,9001,1\n'
        'T1,08:10:00,08:10:00,9002,2\n'
        'T1,08:25:00,08:25:00,9003,3\n'
        'T2,09:00:00,09:00:00,9001,1\n'
        'T2,09:10:00,09:10:00,9002,2\n'
        'T2,09:25:00,09:25:00,9003,3\n'
        'T3,10:00:00,10:00:00,9001,1\n'
        'T3,10:10:00,10:10:00,9002,2\n'
        'T3,10:25:00,10:25:00,9003,3\n'
    ),
    # The published archive's calendar.txt base service is used by no
    # trip; all trip service is enumerated in calendar_dates.txt.
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        '1,1,1,1,1,1,1,1,20261019,20270531\n'
    ),
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        '26,20261116,1\n'
        '26,20261117,1\n'
        '26,20261118,1\n'
        '7,20261121,1\n'
        '8,20261122,1\n'
        '8,20261126,1\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class NorwalkRegistryTests(unittest.TestCase):
    def test_norwalk_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'norwalk']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The archive the agency hosts on its own InfoPoint portal --
        # the URL the FTA NTD GTFS weblinks dataset lists for Norwalk
        # Transit District (NTD 10057) and the direct-download URL the
        # Mobility Database carries for this service (mdb-2242).
        self.assertEqual(
            entry['url'],
            'https://mystop.norwalktransit.com/InfoPoint/gtfs-zip.ashx')
        self.assertIn('norwalktransit.com', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class NorwalkBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'norwalk')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'norwalk.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='norwalk'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'norwalk:%'"
            ).fetchone()[0]
        self.assertEqual(counts, {'stops': 3, 'routes': 1, 'trips': 3})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(source['service_start'], '20261019')
        self.assertEqual(source['service_end'], '20270531')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 1, 'trips': 3})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|norwalk:' in r[4] and 0 <= r[0] < 86400]

    def test_weekday_service_on_an_enumerated_tuesday(self):
        on = [r for r in self.same_day('2026-11-17')
              if r[4].endswith('|norwalk:T1')]
        self.assertEqual([(r[0], r[1]) for r in on],
                         [(8 * 3600, 8 * 3600 + 600),
                          (8 * 3600 + 600, 8 * 3600 + 1500)])

    def test_saturday_service_only_on_saturday(self):
        sat = self.same_day('2026-11-21')
        self.assertTrue(sat)
        self.assertTrue(all(r[4].endswith('|norwalk:T2') for r in sat))

    def test_holiday_date_runs_the_sunday_service(self):
        # Thanksgiving 2026-11-26 is a Thursday: the archive enumerates
        # it under the Sunday/holiday service (8), not the weekday
        # service (26), so T3 runs and T1 does not.
        thu = self.same_day('2026-11-26')
        self.assertTrue(thu)
        self.assertTrue(all(r[4].endswith('|norwalk:T3') for r in thu))

    def test_weekday_service_stops_after_the_enumerated_dates(self):
        # feed_info declares the window to 2027-05-31, but weekday
        # dates are enumerated only through 2026-12-31: a Tuesday in
        # January 2027 has no Norwalk service at all.
        self.assertEqual(self.same_day('2027-01-05'), [])


if __name__ == '__main__':
    unittest.main()
