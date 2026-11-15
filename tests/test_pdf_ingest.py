import hashlib
import sqlite3
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import pdf_ingest
import server


class PdfIngestTests(unittest.TestCase):
    def setUp(self):
        self.pdf = b"fixture PDF bytes; the manifest is the reviewed transcription"
        self.path = Path(tempfile.mkstemp(suffix='.pdf')[1])
        self.path.write_bytes(self.pdf)
        self.manifest = {
            "document": {
                "document_id": "pvta-pdf-2026-11",
                "feed": "pvta-pdf",
                "source_url": "https://example.test/official-schedule.pdf",
                "pdf_sha256": hashlib.sha256(self.pdf).hexdigest(),
                "retrieved_at": "2026-11-15T12:00:00Z",
                "effective_start": "2026-11-02",
                "effective_end": "2026-12-19",
                "extraction_method": "ocr",
                "extractor": "OCR fixture review",
                "review_status": "reviewed",
                "reviewed_at": "2026-11-15T13:00:00Z",
                "reviewer": "fixture-reviewer",
            },
            "schedules": [{
                "schedule_id": "g1-north",
                "route": "G1",
                "direction": "Northbound",
                "service_days": "weekday",
                "confidence": "high",
                "source_page": 2,
                "stops": [
                    {"stop_id": "pvta:5101", "stop_name": "Union Station", "arrival": "08:00", "departure": "08:00"},
                    {"stop_id": "pvta:1495", "stop_name": "Court Square", "arrival": "08:12", "departure": "08:12"},
                ],
            }],
        }

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_reviewed_ocr_pdf_coexists_and_is_traceable(self):
        db = sqlite3.connect(':memory:')
        result = pdf_ingest.ingest(db, self.manifest, self.path, {'pvta:5101', 'pvta:1495'})
        document = db.execute('SELECT document_id, feed, pdf_sha256, extraction_method, review_status FROM pdf_documents').fetchone()
        schedule = db.execute('SELECT schedule_id, routing_eligible, source_page FROM pdf_schedules').fetchone()
        stop = db.execute('SELECT stop_name, arrival, departure FROM pdf_schedule_stops ORDER BY seq').fetchall()
        self.assertEqual(result['document']['pdf_sha256'], hashlib.sha256(self.pdf).hexdigest())
        self.assertEqual(document[0:2], ('pvta-pdf-2026-11', 'pvta-pdf'))
        self.assertEqual(document[2], hashlib.sha256(self.pdf).hexdigest())
        self.assertEqual(document[3:5], ('ocr', 'reviewed'))
        self.assertEqual(schedule, ('g1-north', 1, 2))
        self.assertEqual(stop, [('Union Station', 28800, 28800), ('Court Square', 29520, 29520)])

    def test_ambiguous_schedule_is_stored_but_not_routing_eligible(self):
        self.manifest['schedules'][0]['ambiguity'] = 'Footnote says weekday except school days'
        db = sqlite3.connect(':memory:')
        pdf_ingest.ingest(db, self.manifest, self.path, {'pvta:5101', 'pvta:1495'})
        self.assertEqual(db.execute('SELECT routing_eligible FROM pdf_schedules').fetchone()[0], 0)

    def test_hash_mismatch_and_bad_chronology_are_rejected(self):
        self.manifest['document']['pdf_sha256'] = '0' * 64
        with self.assertRaises(pdf_ingest.ManifestError):
            pdf_ingest.validate_manifest(self.manifest, self.pdf)
        self.manifest['document']['pdf_sha256'] = hashlib.sha256(self.pdf).hexdigest()
        self.manifest['schedules'][0]['stops'][1]['arrival'] = '07:59'
        with self.assertRaises(pdf_ingest.ManifestError):
            pdf_ingest.validate_manifest(self.manifest, self.pdf)

    def test_pending_and_unlinked_pdf_never_becomes_eligible(self):
        self.manifest['document']['review_status'] = 'pending'
        self.manifest['document'].pop('reviewed_at')
        self.manifest['document'].pop('reviewer')
        db = sqlite3.connect(':memory:')
        pdf_ingest.ingest(db, self.manifest, self.path)
        self.assertEqual(db.execute('SELECT routing_eligible FROM pdf_schedules').fetchone()[0], 0)

    def test_unlinked_reviewed_schedule_is_not_routable(self):
        self.manifest['document']['review_status'] = 'reviewed'
        for stop in self.manifest['schedules'][0]['stops']:
            stop.pop('stop_id')
        db = sqlite3.connect(':memory:')
        pdf_ingest.ingest(db, self.manifest, self.path)
        self.assertEqual(db.execute('SELECT routing_eligible FROM pdf_schedules').fetchone()[0], 0)

    def test_api_contract_exposes_pdf_registry(self):
        expected = {'documents': [], 'schedules': [], 'routing_note': 'kept separate'}
        with mock.patch.object(server.db, 'pdf_schedules', return_value=expected):
            self.assertEqual(server.handle('/api/v1/pdf-schedules', {}), expected)


if __name__ == '__main__':
    unittest.main()
