"""Milford Transit District feed registration and ingestion fixtures.

Synthetic data only; no live network and no real departures are asserted.
The fixture mirrors the published archive's distinctive shapes:

- a small deviated-style district feed (Arcadis-published, hosted on
  S3): three routes, a handful of stops, and every trip a loop out of
  Milford Center -- each loop starts at MILFORD-CENTER and ends at
  its southbound twin MILFORD-CENTER-S.
- two calendar.txt patterns only -- WEEKDAY (Mon-Fri) and SATURDAY --
  both spanning 2025-12-31 to 2026-12-31, exactly the window
  feed_info.txt declares. Unlike the Passio and Trillium editions,
  the declared edition and the calendar span agree, and the importer
  records that same window.
- no calendar_dates.txt at all: the edition publishes no holiday
  exceptions, so Thanksgiving (a Thursday) runs the ordinary WEEKDAY
  pattern exactly as published. The importer must not invent a
  holiday reduction the publisher did not declare.
- Route 2 publishes WEEKDAY trips only: on Saturday it stays home
  while Routes 3 and 4 run. There is no Sunday service at all.
- every stop_times row is timed (the published archive times all
  525), so the build carries no untimed-row warning and every
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
        '10107,Milford Transit District,https://www.milfordtransit.com/,America/New_York,en\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\n'
        'Arcadis,https://www.arcadis.com/,en,20251231,20261231\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        'CTR,MILFORD-CENTER,41.2223,-73.0572\n'
        'CTRS,MILFORD-CENTER-S,41.2210,-73.0587\n'
        'MALL,CT-POST-MALL,41.2366,-73.0389\n'
        'POINT,MILFORD-POINT,41.1804,-73.0965\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        '2,10107,2,Route 2,3\n'
        '3,10107,3,Route 3,3\n'
        '4,10107,4,Route 4,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id\n'
        '3,WEEKDAY,R3_WKD\n'
        '3,SATURDAY,R3_SAT\n'
        '2,WEEKDAY,R2_WKD\n'
        '4,WEEKDAY,R4_WKD\n'
        '4,SATURDAY,R4_SAT\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint\n'
        # The Route 3 loop: out of Milford Center and back to its
        # southbound twin, the shape every published trip takes.
        'R3_WKD,08:00:00,08:00:00,CTR,1,1\n'
        'R3_WKD,08:10:00,08:10:00,MALL,2,1\n'
        'R3_WKD,08:25:00,08:25:00,POINT,3,1\n'
        'R3_WKD,08:40:00,08:40:00,CTRS,4,1\n'
        'R3_SAT,09:00:00,09:00:00,CTR,1,1\n'
        'R3_SAT,09:10:00,09:10:00,MALL,2,1\n'
        'R3_SAT,09:25:00,09:25:00,POINT,3,1\n'
        'R3_SAT,09:40:00,09:40:00,CTRS,4,1\n'
        # Route 2 is weekday-only in the published archive.
        'R2_WKD,08:05:00,08:05:00,CTR,1,1\n'
        'R2_WKD,08:15:00,08:15:00,MALL,2,1\n'
        'R4_WKD,08:20:00,08:20:00,CTR,1,1\n'
        'R4_WKD,08:35:00,08:35:00,POINT,2,1\n'
        'R4_SAT,09:20:00,09:20:00,CTR,1,1\n'
        'R4_SAT,09:35:00,09:35:00,POINT,2,1\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'WEEKDAY,1,1,1,1,1,0,0,20251231,20261231\n'
        'SATURDAY,0,0,0,0,0,1,0,20251231,20261231\n'
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


class MilfordRegistryTests(unittest.TestCase):
    def test_milford_registered_once_with_official_source(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        matches = [f for f in feeds if f['id'] == 'milford']
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        # The S3-hosted archive the FTA NTD GTFS weblinks dataset
        # lists for Milford Transit District (NTD 10107, FTA-validated
        # 2026-02-17), the direct-download URL of the Mobility
        # Database's official record ntd-10107, and Transitland's
        # static_current for f-milford~transit~district. Exactly one
        # live feed covers this service; the Mobility Database's own
        # "latest" URL is its NTD mirror of this same archive, not a
        # second producer feed.
        self.assertEqual(
            entry['url'],
            'https://hosted-gtfs-feeds.s3.amazonaws.com/Milford/gtfs.zip')
        self.assertIn('milfordtransit.com', entry['official_page'])
        # Official current feed: no unofficial labelling.
        self.assertNotIn('source_status', entry)


class MilfordBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == 'milford')
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / 'milford.zip').write_bytes(fixture_zip_bytes())
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
                f"SELECT COUNT(*) FROM {t} WHERE feed='milford'").fetchone()[0]
                for t in ('stops', 'routes')}
            # trips carries no feed column; its ids are feed-prefixed.
            counts['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE 'milford:%'"
            ).fetchone()[0]
        # Every published stop is referenced and timed, so all four
        # import; all five published trips import.
        self.assertEqual(counts, {'stops': 4, 'routes': 3, 'trips': 5})
        source = json.loads((self.data / 'sources.json').read_text())[0]
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(len(source['agencies']), 1)
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'Milford Transit District')
        # The recorded window comes from the calendar span, which for
        # this edition is exactly feed_info's declared window.
        self.assertEqual(source['service_start'], '20251231')
        self.assertEqual(source['service_end'], '20261231')
        self.assertEqual(source['validation']['counts'],
                         {'stops': 4, 'routes': 3, 'trips': 5})
        # All stop_times are timed: no untimed-row warning is recorded.
        self.assertNotIn('untimed_stop_times_skipped',
                         source['validation']['warnings'])
        self.assertEqual(source['validation']['errors'], {})

    def same_day(self, day):
        # database.connections() spans the previous, current and next
        # service days by design (overnight handling); restrict to the
        # day itself for calendar-shape assertions.
        return [r for r in database.connections(day)
                if '|milford:' in r[4] and 0 <= r[0] < 86400]

    def trips_on(self, day):
        return {r[4].rsplit('|milford:', 1)[1] for r in self.same_day(day)}

    def test_weekday_loop_connects(self):
        # Tuesday 2026-11-17: the Route 3 loop runs out of Milford
        # Center and back to its southbound twin.
        on = self.same_day('2026-11-17')
        loop = [r for r in on if r[4].endswith('|milford:R3_WKD')]
        self.assertEqual([(r[0], r[1]) for r in loop],
                         [(8 * 3600, 8 * 3600 + 600),
                          (8 * 3600 + 600, 8 * 3600 + 1500),
                          (8 * 3600 + 1500, 8 * 3600 + 2400)])
        self.assertEqual(self.trips_on('2026-11-17'),
                         {'R3_WKD', 'R2_WKD', 'R4_WKD'})

    def test_thanksgiving_runs_the_ordinary_weekday_pattern(self):
        # Thursday 2026-11-26 is Thanksgiving. The edition publishes
        # no calendar_dates.txt at all, so no holiday reduction is
        # declared and the WEEKDAY pattern runs exactly as published.
        self.assertEqual(self.trips_on('2026-11-26'),
                         {'R3_WKD', 'R2_WKD', 'R4_WKD'})

    def test_saturday_shape_and_no_sunday_service(self):
        # Saturday 2026-11-21: the SATURDAY trips run; weekday-only
        # Route 2 stays home. Sunday 2026-11-22: nothing runs.
        self.assertEqual(self.trips_on('2026-11-21'),
                         {'R3_SAT', 'R4_SAT'})
        self.assertEqual(self.trips_on('2026-11-22'), set())


if __name__ == '__main__':
    unittest.main()
