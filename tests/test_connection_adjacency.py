"""Synthetic GTFS adjacency fixtures; no claim about real-world service."""
import pathlib
import sqlite3
import tempfile
import unittest
import json
import zipfile
from contextlib import closing
from unittest.mock import patch

import database
import import_gtfs
import routing


class ConnectionAdjacencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        with closing(sqlite3.connect(root / 'atlas.sqlite')) as db, db:
            db.executescript('''
                CREATE TABLE calendar(service TEXT,start TEXT,end TEXT,days TEXT);
                CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
                CREATE TABLE trips(id TEXT,route TEXT,service TEXT,headsign TEXT);
                CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER,ordinal INTEGER);
                INSERT INTO calendar VALUES('fixture:weekday','20261101','20261201','1111111');
                INSERT INTO trips VALUES('fixture:t','fixture:r','fixture:weekday','Fixture');
            ''')
        self.patch = patch.object(database, 'DATA', root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        database.connections.cache_clear()
        self.addCleanup(database.connections.cache_clear)
        self.path = root / 'atlas.sqlite'

    def insert(self, rows):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO times VALUES(?,?,?,?,?,?,?,?)', rows)
        database.connections.cache_clear()

    def test_nonconsecutive_published_sequences_remain_connected(self):
        self.insert([
            ('fixture:t', 10, 'fixture:a', 100, 100, 0, 0, 0),
            ('fixture:t', 20, 'fixture:b', 200, 200, 0, 0, 1),
        ])
        rows = database.connections('2026-11-14')
        self.assertTrue(any(c[2:4] == ('fixture:a', 'fixture:b')
                            and c[0:2] == (100, 200) for c in rows))

    def test_old_database_fails_with_rebuild_instruction(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('ALTER TABLE times RENAME TO old_times')
            db.execute('CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER)')
        database.connections.cache_clear()
        with self.assertRaisesRegex(RuntimeError, 'rebuild from downloaded GTFS archives'):
            database.connections('2026-11-14')

    def test_clipped_middle_stop_never_creates_a_connection(self):
        # In the published trip, the successor of a (ordinal 0) is omitted
        # stop 20 (ordinal 1). Retained stop c (ordinal 2) is not adjacent.
        self.insert([
            ('fixture:t', 10, 'fixture:a', 100, 100, 0, 0, 0),
            ('fixture:t', 30, 'fixture:c', 300, 300, 0, 0, 2),
        ])
        self.assertFalse(any(c[2:4] == ('fixture:a', 'fixture:c')
                             for c in database.connections('2026-11-14')))

    def test_through_ride_uses_full_trip_ordinal(self):
        self.insert([
            ('fixture:t', 10, 'fixture:a', 100, 100, 0, 0, 0),
            ('fixture:t', 20, 'fixture:b', 200, 200, 0, 0, 1),
            ('fixture:t', 30, 'fixture:c', 300, 300, 0, 0, 2),
        ])
        stops = {sid: dict(id=sid, lat=42., lon=-72., parent='')
                 for sid in ('fixture:a', 'fixture:b', 'fixture:c')}
        with patch.object(routing, 'network', return_value=(stops, {}, {})), \
             patch.object(routing, 'connections', database.connections), \
             patch.object(routing, 'neighbors', return_value=[]), \
             patch.object(routing, 'coverage', return_value=[]):
            result = routing.plan('2026-11-14', 'fixture:a', 'fixture:c',
                                  0, 500, buffer=300)
        self.assertTrue(result['found'])
        self.assertEqual(len(result['legs']), 1)
        self.assertEqual(result['arrival'], 300)


class ImportAdjacencyTests(unittest.TestCase):
    def test_import_records_published_successors_across_sequence_gaps_and_clip(self):
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            (root / 'sources.json').write_text(json.dumps([{'id': 'fixture', 'url': 'https://example.invalid/fixture.zip'}]))
            files = {
                'agency.txt': 'agency_id,agency_name,agency_timezone\n1,Fixture,UTC\n',
                'stops.txt': 'stop_id,stop_name,stop_lat,stop_lon,parent_station\np,Parent,42,-72,\na,A,42,-72,p\nb,B,44,-72,\nc,C,42.2,-72,\n',
                'routes.txt': 'route_id,agency_id,route_type,route_short_name\nr,1,3,R\n',
                'trips.txt': 'trip_id,route_id,service_id\nt,r,weekday\n',
                'stop_times.txt': 'trip_id,arrival_time,departure_time,stop_id,stop_sequence\nt,08:00:00,08:00:00,a,10\nt,08:10:00,08:10:00,b,20\nt,08:20:00,08:20:00,c,30\n',
                'calendar.txt': 'service_id,start_date,end_date,monday,tuesday,wednesday,thursday,friday,saturday,sunday\nweekday,20261101,20261201,1,1,1,1,1,1,1\n',
                'transfers.txt': 'from_stop_id,to_stop_id,transfer_type,min_transfer_time\np,a,2,120\nb,c,2,120\n',
            }
            with zipfile.ZipFile(root / 'fixture.zip', 'w') as archive:
                for filename, body in files.items():
                    archive.writestr(filename, body)
            policy = {'default': {'bounds': [41, 45, -73, -71]}}
            with patch.object(import_gtfs, 'DATA', root), patch.object(import_gtfs, 'POLICY', policy):
                import_gtfs.build()
            with closing(sqlite3.connect(root / 'atlas.sqlite')) as db:
                rows = db.execute('SELECT seq,ordinal FROM times ORDER BY seq').fetchall()
                zones = db.execute('SELECT timezone FROM trips').fetchall()
            self.assertEqual(rows, [(10, 0), (20, 1), (30, 2)])
            self.assertEqual(zones, [('UTC',)])
            clipped = {'default': {'bounds': [41, 43, -73, -71]}}
            with patch.object(import_gtfs, 'DATA', root), patch.object(import_gtfs, 'POLICY', clipped):
                import_gtfs.build()
            with closing(sqlite3.connect(root / 'atlas.sqlite')) as db:
                rows = db.execute('SELECT seq,ordinal FROM times ORDER BY seq').fetchall()
                stops = {row[0] for row in db.execute('SELECT id FROM stops')}
                transfers = db.execute('SELECT a,b FROM transfers ORDER BY a').fetchall()
            self.assertEqual(rows, [(10, 0), (30, 2)])
            self.assertIn('fixture:p', stops)
            self.assertEqual(transfers, [('fixture:p', 'fixture:a')])
