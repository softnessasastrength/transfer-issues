"""MTA (New York) feed registrations and ingestion fixtures.

Synthetic data only; no live network and no real departures are
asserted. The fixtures mirror the published archives' distinctive
shapes, verified first-hand against the 2026-11-16 downloads:

- All seven archives are published from the MTA developer
  resources page (https://www.mta.info/developers) on the
  rrgtfsfeeds.s3.amazonaws.com host: the regular subway GTFS, the
  five NYCT bus borough files, and the MTA Bus Company file. The
  supplemented subway GTFS is deliberately NOT registered: it is
  an hourly-refreshed seven-day service-change overlay, while the
  Atlas registers the stable quarterly/annual editions.
- The subway archive's agency is "MTA NYCT" and it carries the
  Staten Island Railway inside the same feed as route SI
  (route_short_name SIR, route_type 2) alongside the subway
  routes (route_type 1) -- there is no separate SIR static feed
  on the developer page, and none is registered.
- Subway stops come as parent stations with N/S platform
  children (parent_station), and the archive publishes
  stop-to-stop transfers (including timed self-transfers at a
  station). Service is three calendar patterns (Weekday /
  Saturday / Sunday, 2026-11-01 to 2027-05-15) plus a small set
  of calendar_dates exceptions.
- Every bus borough archive's routes.txt is the shared
  system-wide master (307 routes across all boroughs in the
  2026-10-09 edition), but trips.txt is borough-scoped: the
  importer must carry only the routes that actually run trips
  in that file, never the whole master list.
- The MTA Bus Company archive's agency is distinct: agency_id
  MTABC, "MTA Bus Company".
- None of the seven archives publishes fare_attributes.txt or
  fare_rules.txt: the MTA publishes no GTFS fares, and the Atlas
  fare layer (fares.py) is hand-maintained per supported feed.
  No MTA fare is asserted anywhere in these tests.
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

EXPECTED_URLS = {
    'mta_subway': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip',
    'mta_bronx': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_bx.zip',
    'mta_brooklyn': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_b.zip',
    'mta_manhattan': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_m.zip',
    'mta_queens': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_q.zip',
    'mta_staten_island': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_si.zip',
    'mta_busco': 'https://rrgtfsfeeds.s3.amazonaws.com/gtfs_busco.zip',
}

SUBWAY_FILES = {
    'agency.txt': (
        'agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone\n'
        'MTA NYCT,MTA New York City Transit,http://www.mta.info,America/New_York,en,718-330-1234\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'MTA New York City Transit,https://www.mta.info/,EN,20261101,20270515,20261028-fall-2026-pick-with-long-term-supplements\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station\n'
        'A01,Alpha Station,40.7500,-73.9900,1,\n'
        'A01N,Alpha Station,40.7500,-73.9900,,A01\n'
        'A01S,Alpha Station,40.7500,-73.9900,,A01\n'
        'A02,Beta Station,40.7600,-73.9800,1,\n'
        'A02N,Beta Station,40.7600,-73.9800,,A02\n'
        'SIR1,Gamma Station,40.6400,-74.0800,1,\n'
        'SIR1S,Gamma Station,40.6400,-74.0800,,SIR1\n'
        'SIR2,Delta Station,40.6300,-74.0900,1,\n'
        'SIR2S,Delta Station,40.6300,-74.0900,,SIR2\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        'A,MTA NYCT,A,Eighth Avenue Express,1\n'
        'SI,MTA NYCT,SIR,Staten Island Railway,2\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id,direction_id\n'
        'A,Weekday,A_WKD_N,0\n'
        'SI,Weekday,SIR_WKD,0\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'A_WKD_N,08:00:00,08:00:00,A01N,1\n'
        'A_WKD_N,08:05:00,08:05:00,A02N,2\n'
        'SIR_WKD,08:10:00,08:10:00,SIR1S,1\n'
        'SIR_WKD,08:20:00,08:20:00,SIR2S,2\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'Weekday,1,1,1,1,1,0,0,20261101,20270515\n'
        'Saturday,0,0,0,0,0,1,0,20261101,20270515\n'
        'Sunday,0,0,0,0,0,0,1,20261101,20270515\n'
    ),
    'calendar_dates.txt': (
        'service_id,date,exception_type\n'
        # Christmas Day 2026 (a Friday): the Weekday pattern is
        # removed, as the published edition's exceptions do.
        'Weekday,20261225,2\n'
    ),
    'transfers.txt': (
        'from_stop_id,to_stop_id,transfer_type,min_transfer_time\n'
        'A01,A01,2,180\n'
    ),
}

BROOKLYN_FILES = {
    'agency.txt': (
        'agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone\n'
        'MTA NYCT,MTA New York City Transit,http://www.mta.info,America/New_York,en,718-330-1234\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'MTA New York City Transit,https://www.mta.info/,en,20261012,20270102,20261009\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '300001,FLATBUSH AV/EASTERN PKWY,40.6700,-73.9600\n'
        '300002,FLATBUSH AV/ATLANTIC AV,40.6850,-73.9750\n'
    ),
    # The published routes.txt is the shared system-wide master:
    # it lists Queens and Manhattan routes that run no trips in
    # this file. Only B1 runs here.
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        'B1,MTA NYCT,B1,,3\n'
        'Q1,MTA NYCT,Q1,,3\n'
        'M1,MTA NYCT,M1,,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id\n'
        'B1,Weekday,B1_WKD\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'B1_WKD,09:00:00,09:00:00,300001,1\n'
        'B1_WKD,09:07:00,09:07:00,300002,2\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'Weekday,1,1,1,1,1,0,0,20261008,20270102\n'
    ),
}

BUSCO_FILES = {
    'agency.txt': (
        'agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone\n'
        'MTABC,MTA Bus Company,http://www.mta.info,America/New_York,en,718-330-1234\n'
    ),
    'feed_info.txt': (
        'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n'
        'MTA Bus Company,https://www.mta.info/,en,20261012,20270102,20261009\n'
    ),
    'stops.txt': (
        'stop_id,stop_name,stop_lat,stop_lon\n'
        '700001,MAIN ST/ROOSEVELT AV,40.7600,-73.8300\n'
        '700002,MAIN ST/NORTHERN BLVD,40.7650,-73.8250\n'
    ),
    'routes.txt': (
        'route_id,agency_id,route_short_name,route_long_name,route_type\n'
        'Q25,MTABC,Q25,,3\n'
    ),
    'trips.txt': (
        'route_id,service_id,trip_id\n'
        'Q25,Weekday,Q25_WKD\n'
    ),
    'stop_times.txt': (
        'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
        'Q25_WKD,10:00:00,10:00:00,700001,1\n'
        'Q25_WKD,10:06:00,10:06:00,700002,2\n'
    ),
    'calendar.txt': (
        'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n'
        'Weekday,1,1,1,1,1,0,0,20261009,20270102\n'
    ),
}


def zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


class MtaRegistryTests(unittest.TestCase):
    def test_all_seven_feeds_registered_once_with_official_sources(self):
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        for feed_id, url in EXPECTED_URLS.items():
            matches = [f for f in feeds if f['id'] == feed_id]
            self.assertEqual(len(matches), 1, feed_id)
            entry = matches[0]
            self.assertEqual(entry['url'], url, feed_id)
            # The MTA developer resources page is the listing that
            # publishes every one of these archives.
            self.assertEqual(entry['official_page'],
                             'https://www.mta.info/developers')
            # Official current feeds: no unofficial labelling.
            self.assertNotIn('source_status', entry)

    def test_each_feed_has_a_whole_network_coverage_policy(self):
        # New York City lies outside the default New England clip;
        # each MTA archive is a compact single-city network, so --
        # like Amtrak and Metro-North -- it is imported whole.
        coverage = json.loads((ROOT / 'config' / 'coverage.json').read_text())
        for feed_id in EXPECTED_URLS:
            policy = coverage['feeds'].get(feed_id, {})
            self.assertTrue(policy.get('whole_network'), feed_id)
            self.assertIn('description', policy)


class MtaBuildFixture(unittest.TestCase):
    feed_id = None
    files = None

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = pathlib.Path(self.tmp.name)
        feeds = json.loads((ROOT / 'config' / 'feeds.json').read_text())
        entry = next(f for f in feeds if f['id'] == self.feed_id)
        (self.data / 'sources.json').write_text(json.dumps([entry]))
        (self.data / (self.feed_id + '.zip')).write_bytes(zip_bytes(self.files))
        for module in (import_gtfs, database):
            p = patch.object(module, 'DATA', self.data)
            p.start()
            self.addCleanup(p.stop)
        database.connections.cache_clear()
        self.addCleanup(database.connections.cache_clear)
        with io.StringIO() as sink, patch('sys.stdout', sink):
            import_gtfs.build()

    def counts(self):
        with closing(sqlite3.connect(self.data / 'atlas.sqlite')) as db:
            result = {t: db.execute(
                f"SELECT COUNT(*) FROM {t} WHERE feed=?",
                (self.feed_id,)).fetchone()[0]
                for t in ('stops', 'routes')}
            result['trips'] = db.execute(
                "SELECT COUNT(*) FROM trips WHERE id LIKE ?",
                (self.feed_id + ':%',)).fetchone()[0]
        return result

    def source(self):
        return json.loads((self.data / 'sources.json').read_text())[0]

    def trips_on(self, day):
        rows = [r for r in database.connections(day)
                if ('|' + self.feed_id + ':') in r[4] and 0 <= r[0] < 86400]
        return {r[4].rsplit('|' + self.feed_id + ':', 1)[1] for r in rows}


class MtaSubwayBuildTests(MtaBuildFixture):
    feed_id = 'mta_subway'
    files = SUBWAY_FILES

    def test_rebuild_with_missing_archive_clears_imported_coverage(self):
        self.assertEqual(self.source()['status'], 'imported')
        self.assertGreater(self.counts()['trips'], 0)
        (self.data / (self.feed_id + '.zip')).unlink()

        with io.StringIO() as sink, patch('sys.stdout', sink):
            import_gtfs.build()

        self.assertEqual(self.counts(), {'stops': 0, 'routes': 0, 'trips': 0})
        source = self.source()
        self.assertEqual(source['status'], 'not_downloaded')
        for field in ('service_start', 'service_end', 'scope', 'agencies',
                      'feed_info', 'sha256'):
            self.assertNotIn(field, source)


    def test_import_counts_provenance_and_sir(self):
        # Four platform stops are referenced by trips and their
        # four parent stations are retained as parents; the
        # unreferenced A01S platform is pruned (8 of 9 published
        # stops). Both routes import -- including SI, the Staten
        # Island Railway the subway archive carries (route_type 2).
        self.assertEqual(self.counts(), {'stops': 8, 'routes': 2, 'trips': 2})
        source = self.source()
        self.assertEqual(source['status'], 'imported')
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'MTA New York City Transit')
        self.assertEqual(source['service_start'], '20261101')
        self.assertEqual(source['service_end'], '20270515')
        self.assertEqual(source['validation']['errors'], {})
        with closing(sqlite3.connect(self.data / 'atlas.sqlite')) as db:
            sir = db.execute(
                "SELECT type FROM routes WHERE id='mta_subway:SI'").fetchone()
        self.assertEqual(sir[0], '2')

    def test_weekday_service_and_christmas_exception(self):
        # Tuesday 2026-11-17: the Weekday pattern runs both the
        # subway trip and the SIR trip.
        self.assertEqual(self.trips_on('2026-11-17'),
                         {'A_WKD_N', 'SIR_WKD'})
        # Friday 2026-12-25: the published exception removes the
        # Weekday pattern; nothing is invented in its place.
        self.assertEqual(self.trips_on('2026-12-25'), set())


class MtaBrooklynBuildTests(MtaBuildFixture):
    feed_id = 'mta_brooklyn'
    files = BROOKLYN_FILES

    def test_shared_master_routes_without_trips_are_not_carried(self):
        # routes.txt lists B1, Q1 and M1; only B1 runs trips in
        # this archive, so only B1 imports.
        self.assertEqual(self.counts(), {'stops': 2, 'routes': 1, 'trips': 1})
        source = self.source()
        self.assertEqual(source['validation']['counts'],
                         {'stops': 2, 'routes': 1, 'trips': 1})
        self.assertEqual(source['service_start'], '20261008')
        self.assertEqual(source['service_end'], '20270102')

    def test_weekday_connection(self):
        self.assertEqual(self.trips_on('2026-11-17'), {'B1_WKD'})


class MtaBuscoBuildTests(MtaBuildFixture):
    feed_id = 'mta_busco'
    files = BUSCO_FILES

    def test_bus_company_agency_is_distinct(self):
        self.assertEqual(self.counts(), {'stops': 2, 'routes': 1, 'trips': 1})
        source = self.source()
        self.assertEqual(len(source['agencies']), 1)
        self.assertEqual(source['agencies'][0]['agency_id'], 'MTABC')
        self.assertEqual(source['agencies'][0]['agency_name'],
                         'MTA Bus Company')


if __name__ == '__main__':
    unittest.main()
