"""Vercel adapter tests; synthetic fixture SQLite only, not real service.

The adapter (api/index.py) must dispatch to server.handle unchanged:
same status mapping, same JSON, with the original /api/v1 path recovered
from the atlas_path parameter the vercel.json rewrite injects.
"""
import http.client
import importlib.util
import json
import pathlib
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import database

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    'atlas_vercel_adapter', ROOT / 'api' / 'index.py')
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)


class ResolveTests(unittest.TestCase):
    def test_atlas_path_injection(self):
        path, q = adapter.resolve(
            '/api/index.py', 'atlas_path=/api/v1/stops&q=Court&limit=5')
        self.assertEqual(path, '/api/v1/stops')
        self.assertEqual(q, {'q': ['Court'], 'limit': ['5']})

    def test_bare_function_url_is_meta(self):
        for bare in ('', '/', '/api', '/api/index.py'):
            path, q = adapter.resolve(bare, '')
            self.assertEqual(path, '/api/v1/meta')

    def test_direct_path_passes_through(self):
        path, q = adapter.resolve('/api/v1/coverage', 'date=2026-11-17')
        self.assertEqual(path, '/api/v1/coverage')
        self.assertEqual(q, {'date': ['2026-11-17']})


class DispatchTests(unittest.TestCase):
    def test_ok_passthrough(self):
        with patch.object(adapter.atlas_server, 'handle',
                          return_value={'ok': True}) as h:
            status, payload = adapter.dispatch(
                '/api/index.py', 'atlas_path=/api/v1/meta')
        self.assertEqual(status, 200)
        self.assertEqual(payload, {'ok': True})
        h.assert_called_once_with('/api/v1/meta', {})

    def test_value_error_is_400(self):
        with patch.object(adapter.atlas_server, 'handle',
                          side_effect=ValueError('bad date')):
            status, payload = adapter.dispatch('/api/v1/coverage', '')
        self.assertEqual(status, 400)
        self.assertEqual(payload, {'error': 'bad date'})

    def test_lookup_error_is_404(self):
        with patch.object(adapter.atlas_server, 'handle',
                          side_effect=LookupError('Unknown API endpoint')):
            status, payload = adapter.dispatch('/api/v1/nope', '')
        self.assertEqual(status, 404)
        self.assertIn('error', payload)

    def test_unexpected_error_is_500_without_leak(self):
        with patch.object(adapter.atlas_server, 'handle',
                          side_effect=RuntimeError('secret internals')), \
                patch('traceback.print_exc'):
            status, payload = adapter.dispatch('/api/v1/meta', '')
        self.assertEqual(status, 500)
        self.assertNotIn('secret', json.dumps(payload))


class HandlerFixture(unittest.TestCase):
    """End-to-end over HTTP against a two-stop fixture database."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        data = pathlib.Path(cls.tmp.name)
        d = sqlite3.connect(data / 'atlas.sqlite')
        d.execute('CREATE TABLE stops(id TEXT PRIMARY KEY,feed TEXT,'
                  'name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT)')
        d.executemany('INSERT INTO stops VALUES(?,?,?,?,?,?,?)', [
            ('test:1', 'test', 'Union Station', 42.108, -72.594, '', '0'),
            ('test:2', 'test', 'Court Square', 42.105, -72.594, '', '0'),
        ])
        d.execute('CREATE TABLE routes(id TEXT PRIMARY KEY,feed TEXT,'
                  'short TEXT,name TEXT,type TEXT,color TEXT,agency TEXT)')
        d.commit()
        d.close()
        (data / 'sources.json').write_text('[]')
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), adapter.handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever,
                                      daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def setUp(self):
        p = patch.object(database, 'DATA', pathlib.Path(self.tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def request(self, method, path):
        c = http.client.HTTPConnection('127.0.0.1', self.http.server_port)
        c.request(method, path)
        r = c.getresponse()
        result = r.status, dict(r.getheaders()), r.read()
        c.close()
        return result

    def test_stops_via_rewrite_param(self):
        status, headers, body = self.request(
            'GET', '/api/index.py?atlas_path=/api/v1/stops&q=Court')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data['match_count'], 1)
        self.assertEqual(data['stops'][0]['id'], 'test:2')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')

    def test_unknown_endpoint_is_404_json(self):
        status, headers, body = self.request(
            'GET', '/api/index.py?atlas_path=/api/v1/bogus')
        self.assertEqual(status, 404)
        self.assertIn('error', json.loads(body))

    def test_bare_url_serves_meta(self):
        status, headers, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data['api_version'], '1.0')
        self.assertEqual(len(data['stops']), 2)

    def test_post_is_405_json(self):
        status, headers, body = self.request(
            'POST', '/api/index.py?atlas_path=/api/v1/stops&q=Court')
        self.assertEqual(status, 405)
        self.assertIn('error', json.loads(body))


if __name__ == '__main__':
    unittest.main()
