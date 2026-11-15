"""GBT feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published GBT archive's distinctive shape: base
service lives in calendar.txt (year-round weekday / Saturday / Sunday
service ids) and calendar_dates.txt carries only holiday exceptions --
Thanksgiving 2026-11-26 swaps weekday service for Sunday service. The
import must honour both layers.
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
        '668,Greater Bridgeport Transit,http://www.gogbt.com/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Trillium Solutions, Inc.,http://www.trilliumtransit.com,en,20260923,20261227\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '9001,Bridgeport Transportation Center,41.1812,-73.1873\n'
        '9002,Main St at North Ave,41.1900,-73.2100\n'
        '9003,Trumbull Mall,41.2430,-73.2200\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '6246,668,1,Route 1,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '6246,WEEKDAY,T1,Trumbull Mall,0\n'
        '6246,WEEKDAY,T2,Bridgeport Transportation Center,1\n'
        '6246,SUNDAY,T3,Trumbull Mall,0\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'T1,08:00:00,08:00:00,9001,1\n'
        'T1,08:10:00,08:10:00,9002,2\n'
        'T1,08:25:00,08:25:00,9003,3\n'
        'T2,17:00:00,17:00:00,9003,1\n'
        'T2,17:15:00,17:15:00,9002,2\n'
        'T2,17:25:00,17:25:00,9001,3\n'
        'T3,09:00:00,09:00:00,9001,1\n'
        'T3,09:10:00,09:10:00,9002,2\n'
        'T3,09:25:00,09:25:00,9003,3\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'WEEKDAY,1,1,1,1,1,0,0,20260923,20261227\n'
        'SUNDAY,0,0,0,0,0,0,1,20260923,20261227\n'
    ),
    # Thanksgiving: weekday service removed, Sunday service added --
    # the same swap the published archive carries for 2026-11-26.
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        'WEEKDAY,20261126,2\n'
        'SUNDAY,20261126,1\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class GbtRegistryTests(unittest.TestCase):
    def test_gbt_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'gbt']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The archive GBT's GTFS vendor (Trillium) publishes, registered
        # in the Mobility Database as mdb-530; the agency's own page is
        # its "For Transit Geeks" GTFS page.
        self.assertEqual(
            entry['url'],
            'https://data.trilliumtransit.com/gtfs/gbt-ct-us/gbt-ct-us.zip')
        self.assertIn('gogbt.com', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class GbtBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'gbt')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'gbt.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='gbt'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'gbt:%'"
            ).fetchone()[0]
        self.assertEqual(counts, {'stops': 3, 'routes': 1, 'trips': 3})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(source['service_start'], '20260923')
        self.assertEqual(source['service_end'], '20261227')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 1, 'trips': 3})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|gbt:' in r[4] and 0 <= r[0] < 86400]

    def test_weekday_service_on_a_tuesday(self):
        on = [r for r in self.same_day('2026-11-17')
              if r[4].endswith('|gbt:T1')]
        self.assertEqual([(r[0], r[1]) for r in on],
                         [(8 * 3600, 8 * 3600 + 600),
                          (8 * 3600 + 600, 8 * 3600 + 1500)])

    def test_sunday_service_only_on_sunday(self):
        sun = self.same_day('2026-11-22')
        self.assertTrue(sun)
        self.assertTrue(all(r[4].endswith('|gbt:T3') for r in sun))

    def test_holiday_exception_swaps_the_service(self):
        # Thanksgiving 2026-11-26 is a Thursday: the exception removes
        # WEEKDAY and adds SUNDAY, so T3 runs and T1 does not.
        thu = self.same_day('2026-11-26')
        self.assertTrue(thu)
        self.assertTrue(all(r[4].endswith('|gbt:T3') for r in thu))


if __name__ == '__main__':
    unittest.main()
