"""NECTD (Northeastern Connecticut Transit District) feed registration
and ingestion fixtures.

Synthetic data only; no live network and no real departures are
asserted. The fixture mirrors the published archive's distinctive
shapes:

- a small rural deviated-style district feed (Arcadis-published,
  hosted on S3): five colour-named routes (Blue, Green, Orange,
  Weekender, Red-Purple Shuttle) and fifty stops across the Quiet
  Corner -- Danielson/Killingly, Putnam, Plainfield and Thompson.
- two calendar.txt patterns only -- Weekdays (Mon-Fri) and Weekender
  (Sat-Sun) -- both spanning 2025-12-31 to 2026-12-31, exactly the
  window feed_info.txt declares. The declared edition and the
  calendar span agree, and the importer records that same window.
- no calendar_dates.txt at all: the edition publishes no holiday
  exceptions, so Thanksgiving (a Thursday) runs the ordinary
  Weekdays pattern exactly as published. The importer must not
  invent a holiday reduction the publisher did not declare.
- the Weekender pattern runs on Saturday AND Sunday (one route,
  five trips in the published archive): unlike Milford, this
  district does publish Sunday service, on the Weekender pattern
  only.
- every stop_times row is timed (the published archive times all
  704), so the build carries no untimed-row warning and every
  published stop is referenced and imported.
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
        '10156,Northeastern Connecticut Transit District,https://www.nectd.org/index.php,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Arcadis,https://www.arcadis.com/,en,20251231,20261231\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        'GREEN-1,Commerce Ave Commuter Lot,41.805124,-71.884405\n'
        'GREEN-3,Big Y Danielson,41.793076,-71.883841\n'
        'ORANGE-2,Central Village (Route 12/14),41.723905,-71.907492\n'
        'ORANGE-13,Lisbon Landing/SEAT Connection,41.585396,-71.989809\n'
        'REDPURPLE-4,Day Kimball Hospital,41.907074,-71.914143\n'
        'BLUE-14,Downtown Putnam,41.915340,-71.910163\n'
        'WEEKENDER-9,Putnam Farmers Market,41.906327,-71.905353\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        'BLUE,10156,Blue,,3\n'
        'GREEN,10156,Green,,3\n'
        'ORANGE,10156,Orange,,3\n'
        'WEEKENDER,10156,Weekender,,3\n'
        'PURPLE-RED,10156,Red-Purple Shuttle,,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id\n'
        'GREEN,Weekdays,GREEN_WKD\n'
        'ORANGE,Weekdays,ORANGE_WKD\n'
        'PURPLE-RED,Weekdays,REDPURPLE_WKD\n'
        'BLUE,Weekdays,BLUE_WKD\n'
        'WEEKENDER,Weekender,WKND\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint\n'
        # The Green route out of the Commerce Ave Commuter Lot in
        # Danielson, the published archive's most-served stop.
        'GREEN_WKD,08:00:00,08:00:00,GREEN-1,1,1\n'
        'GREEN_WKD,08:12:00,08:12:00,GREEN-3,2,1\n'
        # The Orange route running south to the Lisbon Landing /
        # SEAT Connection stop.
        'ORANGE_WKD,08:00:00,08:00:00,ORANGE-2,1,1\n'
        'ORANGE_WKD,08:30:00,08:30:00,ORANGE-13,2,1\n'
        'REDPURPLE_WKD,08:05:00,08:05:00,REDPURPLE-4,1,1\n'
        'REDPURPLE_WKD,08:20:00,08:20:00,GREEN-1,2,1\n'
        'BLUE_WKD,08:10:00,08:10:00,BLUE-14,1,1\n'
        'BLUE_WKD,08:18:00,08:18:00,REDPURPLE-4,2,1\n'
        # The Weekender trip: the only service on Saturday/Sunday.
        'WKND,10:00:00,10:00:00,WEEKENDER-9,1,1\n'
        'WKND,10:10:00,10:10:00,REDPURPLE-4,2,1\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'Weekdays,1,1,1,1,1,0,0,20251231,20261231\n'
        'Weekender,0,0,0,0,0,1,1,20251231,20261231\n'
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


class NectdRegistryTests(unittest.TestCase):
    def test_nectd_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'nectd']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The S3-hosted archive the FTA NTD GTFS weblinks dataset
        # lists for Northeastern Connecticut Transit District
        # (NTD 10156, FTA-validated 2026-01-14) and Transitland's
        # static_current for
        # f-northeastern~connecticut~transit~district. Exactly one
        # live feed covers this service.
        self.assertEqual(
            entry['url'],
            'https://hosted-gtfs-feeds.s3.amazonaws.com/NECTD/gtfs.zip')
        self.assertIn('nectd.org', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class NectdBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'nectd')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'nectd.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='nectd'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'nectd:%'"
            ).fetchone()[0]
        # Every published stop is referenced and timed, so all seven
        # import; all five published trips import.
        self.assertEqual(counts, {'stops': 7, 'routes': 5, 'trips': 5})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(len(source['agencies']), 1)
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'Northeastern Connecticut Transit District')
        # The recorded window comes from the calendar span, which for
        # this edition is exactly feed_info's declared window.
        self.assertEqual(source['service_start'], '20251231')
        self.assertEqual(source['service_end'], '20261231')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 7, 'routes': 5, 'trips': 5})
        # All stop_times are timed: no untimed-row warning is recorded.
        self.assertNotIn('untimed_stop_times_skipped',
                         source['validation']['warnings'])
        self.assertEqual(source['validation']['errors'], {})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|nectd:' in r[4] and 0 <= r[0] < 86400]

    def trips_on(self, day):
        return {r[4].rsplit('|nectd:', 1)[1] for r in self.same_day(day)}

    def test_weekday_service_connects(self):
        # Tuesday 2026-11-17: the four weekday colour routes run;
        # the Green route connects out of the Commerce Ave Commuter
        # Lot, and the Orange route reaches the Lisbon Landing /
        # SEAT Connection stop.
        on = self.same_day('2026-11-17')
        green = [r for r in on if r[4].endswith('|nectd:GREEN_WKD')]
        self.assertEqual([(r[0], r[1]) for r in green],
                         [(8 * 3600, 8 * 3600 + 720)])
        orange = [r for r in on if r[4].endswith('|nectd:ORANGE_WKD')]
        self.assertEqual([(r[0], r[1]) for r in orange],
                         [(8 * 3600, 8 * 3600 + 1800)])
        self.assertEqual(self.trips_on('2026-11-17'),
                         {'GREEN_WKD', 'ORANGE_WKD', 'REDPURPLE_WKD',
                          'BLUE_WKD'})

    def test_thanksgiving_runs_the_ordinary_weekday_pattern(self):
        # Thursday 2026-11-26 is Thanksgiving. The edition publishes
        # no calendar_dates.txt at all, so no holiday reduction is
        # declared and the Weekdays pattern runs exactly as published.
        self.assertEqual(self.trips_on('2026-11-26'),
                         {'GREEN_WKD', 'ORANGE_WKD', 'REDPURPLE_WKD',
                          'BLUE_WKD'})

    def test_weekender_runs_saturday_and_sunday(self):
        # Saturday 2026-11-21 and Sunday 2026-11-22: only the
        # Weekender pattern runs -- this district does publish
        # Sunday service, on that pattern alone.
        self.assertEqual(self.trips_on('2026-11-21'), {'WKND'})
        self.assertEqual(self.trips_on('2026-11-22'), {'WKND'})


if __name__ == '__main__':
    unittest.main()
