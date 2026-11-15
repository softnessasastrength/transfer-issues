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


if __name__ == "__main__":
    unittest.main()
