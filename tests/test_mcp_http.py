import http.client
import os
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch

import scripts.atlas_mcp_http as mcp_http


class McpHttpTests(unittest.TestCase):
    def test_initialize_and_tool_discovery_use_mcp_json_rpc(self):
        initialize = mcp_http.response_for({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(initialize["result"]["serverInfo"]["name"], "percival-transit-atlas")
        listing = mcp_http.response_for({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertIn("atlas_route_report", {tool["name"] for tool in listing["result"]["tools"]})
        self.assertIn("atlas_come_to_me", {tool["name"] for tool in listing["result"]["tools"]})

    def test_notifications_are_transport_no_content(self):
        self.assertIsNone(mcp_http.response_for({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    @patch.object(mcp_http.atlas_mcp, "dispatch", return_value={"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
    def test_forwards_json_rpc_to_canonical_server(self, dispatch):
        payload = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        self.assertEqual(mcp_http.response_for(payload)["result"], {"ok": True})
        dispatch.assert_called_once_with(payload)


class McpHttpTransportTests(unittest.TestCase):
    """RT-4 hardening: token auth, no wildcard CORS, Host check, body cap."""

    def setUp(self):
        self.env = patch.dict(os.environ, {"ATLAS_MCP_TOKEN": "test-token-123"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.server = mcp_http.make_server("127.0.0.1", 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close()))

    def request(self, method="POST", body=b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}',
                headers=None, host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        all_headers = {"Content-Type": "application/json"}
        if host is not None:
            all_headers["Host"] = host
        all_headers.update(headers or {})
        conn.request(method, "/mcp", body=body, headers=all_headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response, data

    def test_unauthenticated_post_is_401(self):
        response, _ = self.request()
        self.assertEqual(response.status, 401)
        self.assertEqual(response.getheader("WWW-Authenticate"), "Bearer")

    def test_wrong_token_is_401(self):
        response, _ = self.request(headers={"Authorization": "Bearer nope"})
        self.assertEqual(response.status, 401)

    def test_correct_token_is_accepted_without_wildcard_cors(self):
        response, data = self.request(headers={"Authorization": "Bearer test-token-123"})
        self.assertEqual(response.status, 200)
        self.assertIn(b'"tools"', data)
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_options_grants_no_cors(self):
        response, _ = self.request(method="OPTIONS", body=None)
        self.assertEqual(response.status, 204)
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_foreign_host_is_403_even_with_token(self):
        response, _ = self.request(headers={"Authorization": "Bearer test-token-123"},
                                   host="evil.example")
        self.assertEqual(response.status, 403)

    def test_oversized_body_is_413(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest("POST", "/mcp")
        conn.putheader("Authorization", "Bearer test-token-123")
        conn.putheader("Content-Length", str(mcp_http.MAX_BODY + 1))
        conn.endheaders()
        response = conn.getresponse()
        response.read()
        conn.close()
        self.assertEqual(response.status, 413)


class McpTokenFileTests(unittest.TestCase):
    def test_token_file_created_0600_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"ATLAS_DATA_DIR": tmp}):
                os.environ.pop("ATLAS_MCP_TOKEN", None)
                first = mcp_http.expected_token()
                second = mcp_http.expected_token()
                self.assertEqual(first, second)
                mode = stat.S_IMODE(os.stat(mcp_http.token_file()).st_mode)
                self.assertEqual(mode, 0o600)

    def test_env_override_wins_and_creates_no_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"ATLAS_DATA_DIR": tmp, "ATLAS_MCP_TOKEN": "from-env"}):
                self.assertEqual(mcp_http.expected_token(), "from-env")
                self.assertFalse(mcp_http.token_file().exists())


if __name__ == "__main__":
    unittest.main()
