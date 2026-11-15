"""Synthetic agency-timezone fixtures; no real departures are asserted."""
from contextlib import closing
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import database
import import_gtfs


class AgencyTimezoneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        with closing(sqlite3.connect(root / 'atlas.sqlite')) as db, db:
            db.executescript('''
                CREATE TABLE calendar(service TEXT,start TEXT,end TEXT,days TEXT);
                CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
                CREATE TABLE trips(id TEXT,route TEXT,service TEXT,headsign TEXT,timezone TEXT);
                CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER,ordinal INTEGER);
                INSERT INTO calendar VALUES('utc:all','20261101','20270331','1111111');
                INSERT INTO trips VALUES('utc:t','utc:r','utc:all','Fixture','UTC');
            ''')
        p = patch.object(database, 'DATA', root)
        p.start()
        self.addCleanup(p.stop)
        database.connections.cache_clear()
        self.addCleanup(database.connections.cache_clear)
        self.path = root / 'atlas.sqlite'

    def trip(self, departure, arrival):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO times VALUES(?,?,?,?,?,?,?,?)', [
                ('utc:t', 10, 'fixture:a', departure, departure, 0, 0, 0),
                ('utc:t', 20, 'fixture:b', arrival, arrival, 0, 0, 1),
            ])
        database.connections.cache_clear()

    def test_utc_feed_normalizes_to_new_york_service_clock(self):
        self.trip(14 * 3600, 15 * 3600)
        rows = [r for r in database.connections('2026-11-15')
                if r[4] == '2026-11-15|utc:t']
        self.assertEqual([(r[0], r[1]) for r in rows], [(9 * 3600, 10 * 3600)])

    def test_next_utc_service_day_can_depart_on_previous_local_evening(self):
        self.trip(2 * 3600, 3 * 3600)
        rows = [r for r in database.connections('2026-11-15')
                if r[4] == '2026-11-16|utc:t']
        self.assertEqual([(r[0], r[1]) for r in rows], [(21 * 3600, 22 * 3600)])

    def test_dst_fall_back_preserves_elapsed_order(self):
        self.trip(5 * 3600 + 30 * 60, 6 * 3600 + 30 * 60)
        rows = [r for r in database.connections('2026-11-01')
                if r[4] == '2026-11-01|utc:t']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1] - rows[0][0], 3600)


class RegionalFeedPolicyTests(unittest.TestCase):
    def test_greyhound_excludes_flixbus_agency(self):
        self.assertTrue(import_gtfs.route_is_selected('greyhound',
                        {'agency_id': 'GREYHOUND-us', 'route_type': '3'}))
        self.assertFalse(import_gtfs.route_is_selected('greyhound',
                         {'agency_id': 'FLIXBUS-us', 'route_type': '3'}))

    def test_metro_north_uses_full_published_trip(self):
        self.assertTrue(import_gtfs.in_scope('mnr', 40.75, -73.98))
