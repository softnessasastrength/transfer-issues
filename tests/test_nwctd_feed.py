"""NWCTD (Northwestern Connecticut Transit District) feed registration
and ingestion fixtures.

Synthetic data only; no live network and no real departures are
asserted. The fixture mirrors the published archive's distinctive
shapes:

- a small rural deviated-style district feed (Arcadis-published,
  hosted on S3): six routes -- 1 Winsted, 1B Winsted College Only,
  3 Torrington Main St-East Side, 5 Torrington Westside-Southend,
  SaturdayTorrington and Job Access -- across Torrington, Winsted
  and the Litchfield County area.
- four calendar.txt patterns: Weekdays (Mon-Fri) and Saturday span
  2026-07-28 to 2026-12-31, and two winter patterns (WD_Winter
  Mon-Fri, WND_Winter Sat) span 2026-08-27 to 2026-12-23 and
  carry the college route (1B) only. The
  window the importer records is the calendar span (2026-07-28 to
  2026-12-31); feed_info.txt declares an earlier start
  (2026-07-20) that no calendar pattern covers, so the declared
  edition overstates enumerated service by eight days at the
  front.
- no calendar_dates.txt at all: the edition publishes no holiday
  exceptions, so Thanksgiving (a Thursday) runs the ordinary
  weekday patterns exactly as published. The importer must not
  invent a holiday reduction the publisher did not declare.
- no pattern runs on Sunday at all: unlike NECTD's Weekender,
  this district publishes no Sunday service.
- every stop_times row is timed (the published archive times all
  770), so the build carries no untimed-row warning; but twelve
  of the archive's forty-eight published stops are referenced by
  no trip, and the importer prunes unreferenced stops -- the
  fixture carries one such stop to pin that behaviour.
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
        'agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone\n'
        '10131,Northwestern Connecticut Transit District,https://www.nwcttransit.com/about-localbusroute/,America/New_York,en,(860) 489-2535\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'Arcadis,https://www.arcadis.com/,en,20260720,20261231,nwctd_03082026\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        'John St,John St,41.802792,-73.124619\n'
        '5,Parkade,41.825352,-73.111242\n'
        '10,Wal-Mart,41.819088,-73.078445\n'
        '1,Koury Terrace,41.816371,-73.096249\n'
        "4,McGrane's,41.921900,-73.060452\n"
        # Published but referenced by no trip: the importer prunes it.
        '6,Stop and Shop,41.831235,-73.109837\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '3,10131,3,Torrington: Main St to East Side,3\n'
        '5,10131,5,Torrington: Westside to Southend,3\n'
        '1,10131,1,Winsted,3\n'
        '1B,10131,1B,Winsted College Only,3\n'
        'SaturdayTorrington,10131,Saturday,Torrington,3\n'
        'Job Access,10131,Job Access,Job Access,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id\n'
        '3,Weekdays,R3_WKD\n'
        '5,Weekdays,R5_WKD\n'
        '1,Weekdays,R1_WKD\n'
        'Job Access,Weekdays,RJA_WKD\n'
        '1B,WD_Winter,R1B_WIN\n'
        '1B,WND_Winter,R1B_SAT\n'
        'SaturdayTorrington,Saturday,RSAT\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint\n'
        # Route 3 out of John St in downtown Torrington, the
        # published archive's most-served stop.
        'R3_WKD,08:00:00,08:00:00,John St,1,1\n'
        'R3_WKD,08:12:00,08:12:00,5,2,0\n'
        'R5_WKD,08:05:00,08:05:00,John St,1,0\n'
        'R5_WKD,08:20:00,08:20:00,10,2,0\n'
        # Route 1 running north to Winsted.
        'R1_WKD,08:10:00,08:10:00,John St,1,0\n'
        "R1_WKD,08:55:00,08:55:00,4,2,0\n"
        # The winter-only college pattern.
        'R1B_WIN,09:00:00,09:00:00,John St,1,0\n'
        'R1B_WIN,09:08:00,09:08:00,1,2,0\n'
        # Job Access running into John St.
        'RJA_WKD,06:30:00,06:30:00,1,1,0\n'
        'RJA_WKD,06:38:00,06:38:00,John St,2,0\n'
        # The Saturday patterns: the base Saturday pattern, and
        # the winter Saturday pattern, which in the published
        # archive carries the college route only.
        'RSAT,10:00:00,10:00:00,John St,1,0\n'
        'RSAT,10:12:00,10:12:00,5,2,0\n'
        'R1B_SAT,11:00:00,11:00:00,John St,1,0\n'
        'R1B_SAT,11:08:00,11:08:00,1,2,0\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'Weekdays,1,1,1,1,1,0,0,20260728,20261231\n'
        'WD_Winter,1,1,1,1,1,0,0,20260827,20261223\n'
        'Saturday,0,0,0,0,0,1,0,20260728,20261231\n'
        'WND_Winter,0,0,0,0,0,1,0,20260827,20261223\n'
    ),
    # Deliberately no calendar_dates.txt: the published edition has
    # none -- no holiday exceptions are declared anywhere in it.
}


def fixture_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in FIXTURE_FILES.items():
            z.writestr(name, text)
    return buf.getvalue()


class NwctdRegistryTests(unittest.TestCase):
    def test_nwctd_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'nwctd']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The S3-hosted archive the FTA NTD GTFS weblinks dataset
        # lists for Northwestern Connecticut Transit District
        # (NTD 10131, FTA-validated 2026-01-14). Exactly one live
        # feed covers this service; neither the Mobility Database
        # nor Transitland carries a record for it.
        self.assertEqual(
            entry['url'],
            'https://hosted-gtfs-feeds.s3.amazonaws.com/NWCTD/gtfs.zip')
        self.assertIn('nwcttransit.com', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class NwctdBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'nwctd')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'nwctd.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='nwctd'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'nwctd:%'"
            ).fetchone()[0]
        # Five of the six published stops are referenced by a trip
        # and import; the unreferenced Stop and Shop stop is pruned.
        # All six published routes and all seven trips import.
        self.assertEqual(counts, {'stops': 5, 'routes': 6, 'trips': 7})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(len(source['agencies']), 1)
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'Northwestern Connecticut Transit District')
        # The recorded window is the calendar span: feed_info
        # declares a 2026-07-20 start, but no pattern covers the
        # eight days before 2026-07-28, so the importer records
        # the enumerated span.
        self.assertEqual(source['service_start'], '20260728')
        self.assertEqual(source['service_end'], '20261231')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 5, 'routes': 6, 'trips': 7})
        # All stop_times are timed: no untimed-row warning is recorded.
        self.assertNotIn('untimed_stop_times_skipped',
                         source['validation']['warnings'])
        self.assertEqual(source['validation']['errors'], {})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|nwctd:' in r[4] and 0 <= r[0] < 86400]

    def trips_on(self, day):
        return {r[4].rsplit('|nwctd:', 1)[1] for r in self.same_day(day)}

    def test_weekday_service_connects(self):
        # Tuesday 2026-11-17: the Weekdays and WD_Winter patterns
        # both run; route 3 connects out of John St, and route 1
        # reaches Winsted.
        on = self.same_day('2026-11-17')
        r3 = [r for r in on if r[4].endswith('|nwctd:R3_WKD')]
        self.assertEqual([(r[0], r[1]) for r in r3],
                         [(8 * 3600, 8 * 3600 + 720)])
        self.assertEqual(self.trips_on('2026-11-17'),
                         {'R3_WKD', 'R5_WKD', 'R1_WKD', 'RJA_WKD',
                          'R1B_WIN'})

    def test_thanksgiving_runs_the_ordinary_weekday_patterns(self):
        # Thursday 2026-11-26 is Thanksgiving. The edition publishes
        # no calendar_dates.txt at all, so no holiday reduction is
        # declared and the weekday patterns run exactly as published.
        self.assertEqual(self.trips_on('2026-11-26'),
                         {'R3_WKD', 'R5_WKD', 'R1_WKD', 'RJA_WKD',
                          'R1B_WIN'})

    def test_saturday_patterns_run_and_sunday_has_no_service(self):
        # Saturday 2026-11-21: the Saturday and WND_Winter patterns
        # run. Sunday 2026-11-22: no pattern runs at all -- this
        # district publishes no Sunday service.
        self.assertEqual(self.trips_on('2026-11-21'),
                         {'RSAT', 'R1B_SAT'})
        self.assertEqual(self.trips_on('2026-11-22'), set())


if __name__ == '__main__':
    unittest.main()
