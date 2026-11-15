import unittest
from unittest.mock import patch

import scripts.atlas_mcp as mcp
import percival_memory


class McpTests(unittest.TestCase):
    def test_initialize_and_tool_listing(self):
        init = mcp.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init["result"]["serverInfo"]["name"], "percival-transit-atlas")
        listing = mcp.dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {tool["name"] for tool in listing["result"]["tools"]}
        self.assertIn("atlas_search_stops", names)
        self.assertIn("atlas_plan_trip", names)

    @patch.object(mcp, "_api", return_value=[{"id": "hartford:6", "name": "Hartford"}])
    def test_search_tool_maps_arguments(self, api):
        response = mcp.dispatch({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "atlas_search_stops", "arguments": {"query": "Hartford", "limit": 5}}})
        self.assertEqual(response["result"]["structuredContent"][0]["id"], "hartford:6")
        api.assert_called_once_with("/api/v1/stops", {"q": "Hartford", "feed": "", "limit": 5})

    @patch.object(mcp, "_api", return_value={"found": False})
    def test_plan_tool_maps_optional_network(self, api):
        mcp.call_tool("atlas_plan_trip", {"from_stop": "a", "to_stop": "b", "date": "2026-11-15", "time": 28800, "include_optional": True, "return_trip": True})
        params = api.call_args.args[1]
        self.assertEqual(params["include_optional"], "1")
        self.assertEqual(params["return"], "1")

    @patch.object(mcp, "_api", return_value={"routes": [{"id": "hartford:905", "short": "905", "feed": "hartford"}, {"id": "mbta:905", "short": "905", "feed": "mbta"}]})
    def test_route_search_uses_loaded_metadata(self, api):
        routes = mcp.call_tool("atlas_search_routes", {"query": "905", "feed": "hartford"})
        self.assertEqual([route["id"] for route in routes], ["hartford:905"])

    @patch.object(mcp, "_api", side_effect=[
        {"routes": [{"id": "cttransit:16545", "short": "905", "feed": "cttransit"}]},
        {"routes": [{"id": "cttransit:16545", "short": "905", "feed": "cttransit"}], "sources": [{"id": "cttransit", "status": "ok"}]},
    ])
    def test_route_report_returns_evidence_fields(self, api):
        report = mcp.call_tool("atlas_route_report", {"query": "905"})
        self.assertEqual(report["status"], "matched")
        self.assertEqual(report["sources"][0]["status"], "ok")
        self.assertIsNone(report["coverage"])

    @patch.object(mcp, "_api", return_value={"found": True, "return": {"found": True}, "latest_return": {"found": True}})
    def test_come_to_me_protects_return_and_is_draft_only(self, api):
        plan = mcp.call_tool("atlas_come_to_me", {"guest_from": "a", "host_stop": "b", "date": "2026-11-16", "depart_time": 28800, "return_deadline": 86399})
        self.assertEqual(plan["status"], "feasible")
        self.assertTrue(plan["draft_only"])
        self.assertEqual(api.call_args.args[1]["return"], "1")

    def test_notifications_do_not_emit_responses(self):
        self.assertIsNone(mcp.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    @patch.object(percival_memory, "get", return_value={"home_stop": "hartford:6"})
    def test_preferences_are_explicit_and_local(self, get_preferences):
        result = mcp.call_tool("percival_get_preferences", {})
        self.assertEqual(result["preferences"]["home_stop"], "hartford:6")
        self.assertFalse(result["inferred"])
        get_preferences.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
