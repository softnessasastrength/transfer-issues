import json
import unittest
from unittest.mock import patch

import live


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def __iter__(self): return iter(())
    def read(self): return json.dumps(self.payload).encode()


class LiveTests(unittest.TestCase):
    def test_unknown_provider_is_explicit_and_does_not_fallback(self):
        result = live.status("cttransit")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["predictions"], [])
        self.assertIn("No verified live provider", result["limitations"][0])

    @patch("live.urlopen")
    def test_mbta_normalizes_predictions_and_alerts(self, urlopen):
        urlopen.side_effect = [
            Response({"data": [{"id": "p1", "attributes": {"status": "", "departure_time": "2026-11-15T12:00:00Z"}}]}),
            Response({"data": [{"id": "a1", "attributes": {"severity": 7, "header": "Delay"}}]}),
        ]
        result = live.mbta("mbta:Red", "place-pktrm")
        self.assertEqual(result["status"], "live")
        self.assertEqual(result["predictions"][0]["id"], "p1")
        self.assertEqual(result["alerts"][0]["severity"], 7)
        first_request = urlopen.call_args_list[0].args[0]
        self.assertIn("filter%5Broute%5D=Red", first_request.full_url)
        self.assertIn("filter%5Bstop%5D=place-pktrm", first_request.full_url)

    @patch("live.urlopen", side_effect=TimeoutError())
    def test_provider_failure_is_unknown_not_http_failure(self, _urlopen):
        result = live.mbta()
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["provider"], "mbta_v3")


if __name__ == "__main__":
    unittest.main()
