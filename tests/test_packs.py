"""Offline map packs: listing API + Range-capable serving.

PMTiles readers fetch byte ranges, which SimpleHTTPRequestHandler does not
support; these tests pin the minimal range implementation and the listing
contract against a synthetic pack file (no real tiles involved).
"""
import http.client
import json
import pathlib
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import server


class PackFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        data = pathlib.Path(self.tmp.name)
        packs = data / 'packs'
        packs.mkdir()
        self.body = bytes(range(256)) * 4  # 1024 deterministic bytes
        (packs / 'test-region.pmtiles').write_bytes(self.body)
        (packs / 'packs.json').write_text(json.dumps({'packs': {
            'test-region.pmtiles': {'name': 'Test Region', 'region': 'Nowhere',
                                    'source': '© OpenStreetMap contributors (ODbL)'}}}))
        self.patch = patch.object(server.db, 'DATA', data)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(lambda: (self.httpd.shutdown(), self.httpd.server_close()))

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        conn.request('GET', path, headers=headers or {})
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response, body


class PackListingTests(PackFixture):
    def test_listing_reports_manifest_and_size(self):
        result = server.handle('/api/v1/packs', {})
        self.assertEqual(result['count'], 1)
        row = result['packs'][0]
        self.assertEqual(row['name'], 'Test Region')
        self.assertEqual(row['size_bytes'], 1024)
        self.assertEqual(row['url'], '/packs/test-region.pmtiles')
        self.assertIn('OpenStreetMap', row['source'])


class PackServingTests(PackFixture):
    def test_full_file_200(self):
        response, body = self.get('/packs/test-region.pmtiles')
        self.assertEqual(response.status, 200)
        self.assertEqual(body, self.body)
        self.assertEqual(response.getheader('Accept-Ranges'), 'bytes')

    def test_range_206(self):
        response, body = self.get('/packs/test-region.pmtiles', {'Range': 'bytes=100-199'})
        self.assertEqual(response.status, 206)
        self.assertEqual(response.getheader('Content-Range'), 'bytes 100-199/1024')
        self.assertEqual(body, self.body[100:200])

    def test_open_ended_and_suffix_ranges(self):
        response, body = self.get('/packs/test-region.pmtiles', {'Range': 'bytes=1000-'})
        self.assertEqual(response.status, 206)
        self.assertEqual(body, self.body[1000:])
        response, body = self.get('/packs/test-region.pmtiles', {'Range': 'bytes=-24'})
        self.assertEqual(response.status, 206)
        self.assertEqual(body, self.body[-24:])

    def test_out_of_range_416(self):
        response, _ = self.get('/packs/test-region.pmtiles', {'Range': 'bytes=2000-3000'})
        self.assertEqual(response.status, 416)

    def test_missing_and_traversal_404(self):
        for path in ('/packs/nope.pmtiles', '/packs/sub/secret.pmtiles', '/packs/../atlas.sqlite'):
            response, _ = self.get(path)
            self.assertEqual(response.status, 404, path)


if __name__ == '__main__':
    unittest.main()
