"""RIPTA feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published RIPTA archive's distinctive shape: it
ships no calendar.txt, so every operating date is enumerated as a
type-1 row in calendar_dates.txt. The import must honour exactly those
dates -- service on a listed date, none on an unlisted one.
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
        'RIPTA,Rhode Island Public Transit Authority,http://www.ripta.com/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Rhode Island Public Transit Authority,http://www.ripta.com/,en,20261101,20270115\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '16400,Kennedy Plaza (Stop B),41.8241,-71.4131\n'
        '57505,Providence Station,41.8294,-71.4131\n'
        '1380,Newport Transit Center (Stop A),41.4901,-71.3130\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '64,RIPTA,64,Providence - Newport,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '64,WKD,T1,Newport,0\n'
        '64,WKD,T2,Kennedy Plaza,1\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'T1,08:00:00,08:00:00,16400,1\n'
        'T1,08:05:00,08:05:00,57505,2\n'
        'T1,08:50:00,08:50:00,1380,3\n'
        'T2,17:00:00,17:00:00,1380,1\n'
        'T2,17:45:00,17:45:00,57505,2\n'
        'T2,17:50:00,17:50:00,16400,3\n'
    ),
    # No calendar.txt on purpose: RIPTA publishes service this way.
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        'WKD,20261117,1\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class RiptaRegistryTests(unittest.TestCase):
    def test_ripta_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'ripta']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        self.assertTrue(entry['url'].startswith('https://ripta.com/'))
        self.assertIn('ripta.com', entry['official_page'])


class RiptaBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'ripta')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'ripta.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='ripta'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'ripta:%'"
            ).fetchone()[0]
        self.assertEqual(counts, {'stops': 3, 'routes': 1, 'trips': 2})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        # With no calendar.txt, the service window comes from the
        # enumerated exception dates alone.
        self.assertEqual(source['service_start'], '20261117')
        self.assertEqual(source['service_end'], '20261117')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 1, 'trips': 2})

    def test_service_only_on_enumerated_dates(self):
        on = [r for r in database.connections('2026-11-17')
              if r[4].endswith('|ripta:T1')]
        # Connections are per-segment: Kennedy Plaza -> Providence
        # Station -> Newport, exactly the published stop times.
        self.assertEqual([(r[0], r[1]) for r in on],
                         [(8 * 3600, 8 * 3600 + 300),
                          (8 * 3600 + 300, 8 * 3600 + 3000)])
        off = [r for r in database.connections('2026-11-18')
               if '|ripta:' in r[4]]
        self.assertEqual(off, [])


if __name__ == '__main__':
    unittest.main()
