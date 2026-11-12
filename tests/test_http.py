"""HTTP contract smoke tests; do not require external feeds or browser binaries."""
import http.client
import json
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import server


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def get(self, path):
        c = http.client.HTTPConnection('127.0.0.1', self.http.server_port)
        c.request('GET', path)
        r = c.getresponse()
        result = r.status, dict(r.getheaders()), r.read()
        c.close()
        return result

    def test_page_and_controller_served(self):
        status, headers, body = self.get('/')
        self.assertEqual(status, 200)
        self.assertIn(b'src="app.js"', body)
        status, headers, body = self.get('/app.js')
        self.assertEqual(status, 200)
        self.assertIn(b'async function init()', body)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')

    def test_api_error_is_json(self):
        status, headers, body = self.get('/api/v1/coverage?date=invalid')
        self.assertEqual(status, 400)
        self.assertIn('error', json.loads(body))
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_metadata_contract(self):
        with patch.object(server.db, 'sources', return_value=[]), patch.object(server.db, 'query', return_value=[]):
            status, headers, body = self.get('/api/v1/meta')
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(data['api_version'], '1.0')
        self.assertTrue(data['cities'])
        self.assertEqual(data['routes'], [])
