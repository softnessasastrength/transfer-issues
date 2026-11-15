"""Stop lookup endpoint tests; synthetic fixture SQLite only, not real service."""
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import database
import server

FIXTURE_STOPS = [
    ('test:1', 'test', 'Union Station', 42.108, -72.594, '', '0'),
    ('test:2', 'test', 'Union Station Bay 2', 42.108, -72.594, '', '0'),
    ('test:3', 'test', 'Court Square', 42.105, -72.594, '', '0'),
    ('test:4', 'test', '100% Transfer Point', 42.0, -72.0, '', '0'),
    ('other:1', 'other', 'Union Station', 41.0, -71.0, '', '0'),
    ('other:2', 'other', 'Uniondale Plaza', 41.1, -71.1, '', '0'),
]


class StopSearchFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db_path = pathlib.Path(cls.tmp.name) / 'atlas.sqlite'
        d = sqlite3.connect(db_path)
        d.execute('CREATE TABLE stops(id TEXT PRIMARY KEY,feed TEXT,'
                  'name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT)')
        d.executemany('INSERT INTO stops VALUES(?,?,?,?,?,?,?)',
                      FIXTURE_STOPS)
        d.commit()
        d.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        p = patch.object(database, 'DATA', pathlib.Path(self.tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def search(self, *a, **kw):
        return database.search_stops(*a, **kw)

    def test_substring_match(self):
        r = self.search('Court')
        self.assertEqual(r['match_count'], 1)
        self.assertEqual(r['stops'][0]['id'], 'test:3')
        self.assertEqual(r['stops'][0]['name'], 'Court Square')

    def test_case_insensitive(self):
        r = self.search('UNION STATION')
        self.assertEqual(r['match_count'], 3)
        self.assertEqual({s['id'] for s in r['stops']},
                         {'test:1', 'test:2', 'other:1'})

    def test_result_fields(self):
        r = self.search('Court Square')
        s = r['stops'][0]
        self.assertEqual(s['feed'], 'test')
        self.assertEqual(s['lat'], 42.105)
        self.assertEqual(s['lon'], -72.594)

    def test_feed_filter(self):
        r = self.search('union', feed='test')
        self.assertEqual({s['id'] for s in r['stops']}, {'test:1', 'test:2'})
        self.assertTrue(all(s['feed'] == 'test' for s in r['stops']))
        self.assertEqual(r['feed'], 'test')
        r = self.search('union', feed='other')
        self.assertEqual({s['id'] for s in r['stops']},
                         {'other:1', 'other:2'})

    def test_no_match_is_honest_empty(self):
        r = self.search('zzzqqq nowhere')
        self.assertEqual(r['stops'], [])
        self.assertEqual(r['match_count'], 0)
        self.assertFalse(r['truncated'])

    def test_empty_query_is_honest_empty(self):
        for q in ['', '   ']:
            r = self.search(q)
            self.assertEqual(r['stops'], [])
            self.assertEqual(r['match_count'], 0)

    def test_limit_and_total_count(self):
        r = self.search('union', limit=2)
        self.assertEqual(len(r['stops']), 2)
        self.assertEqual(r['match_count'], 4)
        self.assertTrue(r['truncated'])
        r = self.search('union')
        self.assertEqual(len(r['stops']), 4)
        self.assertFalse(r['truncated'])

    def test_like_wildcards_match_literally(self):
        r = self.search('%')
        self.assertEqual(r['match_count'], 1)
        self.assertEqual(r['stops'][0]['id'], 'test:4')
        r = self.search('100%')
        self.assertEqual(r['match_count'], 1)
        self.assertEqual(r['stops'][0]['id'], 'test:4')

    def test_endpoint_contract(self):
        r = server.handle('/api/v1/stops',
                          {'q': ['union'], 'feed': ['test']})
        self.assertEqual(r['query'], 'union')
        self.assertEqual(r['match_count'], 2)
        self.assertEqual({s['id'] for s in r['stops']}, {'test:1', 'test:2'})

    def test_endpoint_limit_validated(self):
        with self.assertRaises(ValueError):
            server.handle('/api/v1/stops',
                          {'q': ['union'], 'limit': ['9999']})
        with self.assertRaises(ValueError):
            server.handle('/api/v1/stops',
                          {'q': ['union'], 'limit': ['0']})


if __name__ == '__main__':
    unittest.main()
