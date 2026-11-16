"""River Valley Transit feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published RVT archive's distinctive shape: the
merged agency's Trillium archive splits weekday service across several
calendar.txt patterns (a full Mon-Fri pattern plus day-specific ones,
including a Thursday-only pattern), calendar_dates.txt carries no
exception rows at all -- so Thanksgiving runs the ordinary Thursday
service, with no holiday swap -- and feed_info declares a narrower
window (2026-11-13 to 2027-11-04) than the calendar patterns span
(2026-11-03 to 2027-11-30). The archive also publishes stops no trip
references and a seasonal route (the Clinton Trolley) with no trips in
this edition; the import must carry neither.
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
        '4964,River Valley Transit,https://estuarytransit.org/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Trillium Solutions, Inc.,http://www.trilliumtransit.com,en,20261113,20271104\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '9001,Downtown Terminal,41.5613,-72.6491\n'
        '9002,Wesleyan University,41.5525,-72.6565\n'
        '9003,Old Saybrook Train Station,41.3000,-72.3770\n'
        '9004,Unreferenced Point,41.4000,-72.5000\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '19480,4964,581,Saybrook Road,3\n'
        '16490,4964,,Clinton Trolley,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,trip_headsign,direction_id\n'
        '19480,WEEKDAY,T1,Old Saybrook,0\n'
        '19480,THU,T2,Downtown Terminal,1\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'T1,08:00:00,08:00:00,9001,1\n'
        'T1,08:10:00,08:10:00,9002,2\n'
        'T1,08:40:00,08:40:00,9003,3\n'
        'T2,09:00:00,09:00:00,9003,1\n'
        'T2,09:30:00,09:30:00,9002,2\n'
        'T2,09:40:00,09:40:00,9001,3\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'WEEKDAY,1,1,1,1,1,0,0,20261103,20271130\n'
        'THU,0,0,0,1,0,0,0,20261103,20271130\n'
    ),
    # The published archive's calendar_dates.txt has a header and no
    # rows: no holiday exceptions are published in this edition.
    'calendar_dates.txt': (
        'date,service_id,holiday_name,exception_type\n'
    ),
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class RiverValleyRegistryTests(unittest.TestCase):
    def test_rivervalley_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'rivervalley']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The archive the merged agency's GTFS vendor (Trillium)
        # publishes under the feed's own registered id -- the URL the
        # Mobility Database registers for this service (mdb-551) and
        # Transitland's static_current for the Estuary Transit
        # District feed. A second Trillium URL (rivervalley-ct-us)
        # serves byte-identical content and is deliberately not
        # configured: one feed only, never both.
        self.assertEqual(
            entry['url'],
            'https://data.trilliumtransit.com/gtfs/ninetown-connecticut-us/ninetown-connecticut-us.zip')
        self.assertIn('estuarytransit.org', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class RiverValleyBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'rivervalley')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'rivervalley.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='rivervalley'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'rivervalley:%'"
            ).fetchone()[0]
        # Stop 9004 is referenced by no trip and is pruned; the
        # Clinton Trolley route publishes no trips and is not carried.
        self.assertEqual(counts, {'stops': 3, 'routes': 1, 'trips': 2})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        # The recorded window is the calendar span, which is wider
        # than feed_info's declared 20261113-20271104 edition window.
        self.assertEqual(source['service_start'], '20261103')
        self.assertEqual(source['service_end'], '20271130')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 3, 'routes': 1, 'trips': 2})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|rivervalley:' in r[4] and 0 <= r[0] < 86400]

    def test_weekday_service_on_a_tuesday(self):
        on = [r for r in self.same_day('2026-11-17')
              if r[4].endswith('|rivervalley:T1')]
        self.assertEqual([(r[0], r[1]) for r in on],
                         [(8 * 3600, 8 * 3600 + 600),
                          (8 * 3600 + 600, 8 * 3600 + 2400)])
        # The Thursday-only pattern does not run on a Tuesday.
        thu = [r for r in self.same_day('2026-11-17')
               if r[4].endswith('|rivervalley:T2')]
        self.assertEqual(thu, [])

    def test_thursday_only_pattern_runs_on_thursday(self):
        thu = [r for r in self.same_day('2026-11-19')
               if r[4].endswith('|rivervalley:T2')]
        self.assertEqual([(r[0], r[1]) for r in thu],
                         [(9 * 3600, 9 * 3600 + 1800),
                          (9 * 3600 + 1800, 9 * 3600 + 2400)])

    def test_no_holiday_exception_on_thanksgiving(self):
        # Thanksgiving 2026-11-26 is a Thursday. Unlike GBT/Norwalk,
        # this edition publishes no exception rows, so the ordinary
        # Thursday service -- both patterns -- runs unchanged.
        day = self.same_day('2026-11-26')
        self.assertTrue(any(r[4].endswith('|rivervalley:T1') for r in day))
        self.assertTrue(any(r[4].endswith('|rivervalley:T2') for r in day))


if __name__ == '__main__':
    unittest.main()
