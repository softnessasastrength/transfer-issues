"""F-009 commute profiles: storage round-trip, asymmetric evaluation,
rideshare estimate labelling, and return protection.

All fixtures are synthetic stop/route IDs and canned planner responses; no
test touches the network or a real Atlas database (tests/AGENTS.md).
"""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import commute
import percival_memory
import scripts.atlas_mcp as mcp


PROFILE = {
    "id": "work-commute",
    "name": "Work commute",
    "home_stop": "test:home",
    "work_stop": "test:work",
    "outbound": {"routes": ["test:905", "test:82"]},
    "return": {"routes": ["test:82", "test:HART"]},
    "rideshare_legs": [{"from_stop": "test:station", "to": "home"}],
}

STOPS = {
    "test:home": {"id": "test:home", "name": "Home Corner", "lat": 42.0, "lon": -72.60},
    "test:work": {"id": "test:work", "name": "Work", "lat": 41.80, "lon": -72.55},
    "test:station": {"id": "test:station", "name": "Rail Station", "lat": 41.99, "lon": -72.62},
}

ROUTE_STOPS = {
    "test:905": [STOPS["test:home"]],
    "test:82": [STOPS["test:work"], STOPS["test:station"]],
    "test:HART": [STOPS["test:station"]],
}

NOT_FOUND = {"found": False, "message": "No itinerary found in the loaded feeds and selected time window."}


def plan(departure, arrival, matched=True):
    return {
        "found": True, "departure": departure, "arrival": arrival,
        "legs": [], "route_chain_matched": matched,
    }


def make_api(plans):
    calls = []

    def api(path, params=None):
        params = params or {}
        calls.append((path, dict(params)))
        if path == "/api/v1/route":
            return {"stops": list(ROUTE_STOPS.get(params["id"], []))}
        if path == "/api/v1/plan":
            key = (params["from"], params["to"], params.get("kind", "depart"), params.get("routes"))
            if key in plans:
                return dict(plans[key])
            return dict(NOT_FOUND)
        raise AssertionError("unexpected API path: " + path)

    api.calls = calls
    return api


def standard_plans():
    return {
        ("test:home", "test:work", "depart", "test:905,test:82"): plan(25200, 29700),
        ("test:home", "test:work", "depart", None): plan(25200, 29100),
        ("test:work", "test:station", "depart", "test:82,test:HART"): plan(61200, 64800),
        ("test:work", "test:station", "depart", None): plan(61200, 64800),
        ("test:work", "test:station", "latest", "test:82,test:HART"): plan(70200, 73800),
    }


class PrefsPatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.object(percival_memory, "PATH", pathlib.Path(self.tmp.name) / "prefs.json")
        patcher.start()
        self.addCleanup(patcher.stop)


class CommuteStorageTests(PrefsPatch):
    def test_profile_round_trip(self):
        stored = percival_memory.set_commute(PROFILE)
        self.assertEqual(stored["outbound"]["routes"], ["test:905", "test:82"])
        self.assertEqual(stored["return"]["routes"], ["test:82", "test:HART"])
        self.assertEqual([p["id"] for p in percival_memory.get_commutes()], ["work-commute"])
        self.assertEqual(percival_memory.get_commute("work-commute")["work_stop"], "test:work")
        self.assertEqual(percival_memory.get_commute("work commute")["id"], "work-commute")
        self.assertIsNone(percival_memory.get_commute("nope"))
        # The profile survives a full preferences validation pass.
        self.assertEqual(percival_memory.get()["commutes"][0]["id"], "work-commute")

    def test_upsert_replaces_and_clear_forgets(self):
        percival_memory.set_commute(PROFILE)
        changed = dict(PROFILE, name="Renamed commute")
        percival_memory.set_commute(changed)
        self.assertEqual(len(percival_memory.get_commutes()), 1)
        self.assertEqual(percival_memory.get_commute("work-commute")["name"], "Renamed commute")
        self.assertEqual(percival_memory.clear_commute("work-commute"), [])
        self.assertEqual(percival_memory.get_commutes(), [])

    def test_validation_rejects_bad_profiles(self):
        with self.assertRaises(ValueError):
            percival_memory.set_commute(dict(PROFILE, rideshare_legs=[{"from_stop": "test:station", "to": "moon"}]))
        with self.assertRaises(ValueError):
            percival_memory.set_commute(dict(PROFILE, outbound={"routes": ["905"]}))
        with self.assertRaises(ValueError):
            percival_memory.set_commute(dict(PROFILE, name=""))
        with self.assertRaises(ValueError):
            percival_memory.set_commute(dict(PROFILE, teleport=True))
        self.assertEqual(percival_memory.get_commutes(), [])


class CommuteEvaluationTests(unittest.TestCase):
    def test_asymmetric_evaluation_shape(self):
        api = make_api(standard_plans())
        result = commute.evaluate(api, PROFILE, "2026-11-17", 25200, 61200)
        outbound, ret = result["outbound"], result["return"]
        self.assertTrue(outbound["found"])
        self.assertEqual((outbound["from_stop"], outbound["to_stop"]), ("test:home", "test:work"))
        self.assertNotIn("rideshare", outbound)
        self.assertTrue(ret["found"])
        self.assertEqual(ret["transit_to_stop"], "test:station")
        plan_calls = [params for path, params in api.calls if path == "/api/v1/plan"]
        outbound_call = next(p for p in plan_calls if p["from"] == "test:home")
        return_call = next(p for p in plan_calls if p["from"] == "test:work" and p.get("kind", "depart") == "depart")
        self.assertEqual(outbound_call["routes"], "test:905,test:82")
        self.assertEqual(return_call["routes"], "test:82,test:HART")
        self.assertNotEqual(outbound_call["routes"], return_call["routes"])

    def test_rideshare_estimate_is_labelled_and_priceless(self):
        api = make_api(standard_plans())
        result = commute.evaluate(api, PROFILE, "2026-11-17", 25200, 61200)
        estimate = result["return"]["rideshare"]
        self.assertEqual(estimate["status"], "estimated")
        self.assertIn("not a quote", estimate["label"])
        self.assertIn("not booked", estimate["label"])
        self.assertFalse(estimate["booked"])
        for key in estimate:
            self.assertNotIn("price", key)
            self.assertNotIn("cost", key)
            self.assertNotIn("fare", key)
        low, high = estimate["drive_minutes"]
        self.assertGreaterEqual(low, 1)
        self.assertLessEqual(low, high)
        self.assertIn("circuity", estimate["method"])
        arrival = result["return"]["plan"]["arrival"]
        self.assertEqual(
            result["return"]["estimated_final_arrival"],
            [arrival + low * 60, arrival + high * 60],
        )

    def test_preference_applied_and_time_cost_noted(self):
        api = make_api(standard_plans())
        result = commute.evaluate(api, PROFILE, "2026-11-17", 25200, 61200)
        preference = result["outbound"]["preference"]
        self.assertTrue(preference["applied"])
        notes = " ".join(preference["notes"])
        self.assertIn("applied", notes)
        self.assertIn("10 minutes earlier", notes)

    def test_preference_fallback_when_chain_cannot_run(self):
        plans = standard_plans()
        del plans[("test:home", "test:work", "depart", "test:905,test:82")]
        api = make_api(plans)
        result = commute.evaluate(api, PROFILE, "2026-11-17", 25200, 61200)
        outbound = result["outbound"]
        self.assertTrue(outbound["found"])
        self.assertFalse(outbound["preference"]["applied"])
        self.assertIn("could not be honoured", " ".join(outbound["preference"]["notes"]))
        self.assertEqual(outbound["plan"]["arrival"], 29100)

    def test_return_protection_includes_last_viable_return(self):
        api = make_api(standard_plans())
        result = commute.evaluate(api, PROFILE, "2026-11-17", 25200, 61200)
        latest = result["return"]["last_viable_return"]
        self.assertTrue(latest["found"])
        self.assertEqual(latest["departure"], 70200)
        latest_calls = [
            params for path, params in api.calls
            if path == "/api/v1/plan" and params.get("kind") == "latest"
        ]
        self.assertEqual(len(latest_calls), 1)
        self.assertEqual(latest_calls[0]["from"], "test:work")
        self.assertEqual(latest_calls[0]["to"], "test:station")
        # Bounded to the service day (28:00 GTFS extended time): a wider
        # window would surface tomorrow evening's service as tonight's.
        self.assertEqual(latest_calls[0]["deadline"], commute.SERVICE_DAY_END)

    def test_rideshare_unknown_without_coordinates(self):
        estimate = commute.estimate_rideshare(None, STOPS["test:home"], "test:station", "test:home", "home")
        self.assertEqual(estimate["status"], "unknown")
        self.assertNotIn("drive_minutes", estimate)
        self.assertIn("not a quote", estimate["label"])


class CommuteToolTests(PrefsPatch):
    def test_tools_are_listed(self):
        listing = mcp.dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in listing["result"]["tools"]}
        self.assertTrue({
            "percival_get_commute", "percival_set_commute",
            "percival_clear_commute", "atlas_commute_evaluate",
        } <= names)

    def test_set_and_get_commute_via_tools(self):
        saved = mcp.call_tool("percival_set_commute", PROFILE)
        self.assertEqual(saved["commute"]["id"], "work-commute")
        self.assertFalse(saved["inferred"])
        listed = mcp.call_tool("percival_get_commute", {})
        self.assertEqual([p["id"] for p in listed["commutes"]], ["work-commute"])
        fetched = mcp.call_tool("percival_get_commute", {"id": "Work commute"})
        self.assertEqual(fetched["commute"]["home_stop"], "test:home")
        with self.assertRaises(ValueError):
            mcp.call_tool("percival_get_commute", {"id": "missing"})

    def test_evaluate_commute_via_tool(self):
        percival_memory.set_commute(PROFILE)
        api = make_api(standard_plans())
        with patch.object(mcp, "_api", api):
            result = mcp.call_tool("atlas_commute_evaluate", {
                "profile": "work-commute", "date": "2026-11-17",
                "depart_time": 25200, "return_time": 61200,
            })
        self.assertTrue(result["outbound"]["found"])
        self.assertTrue(result["return"]["last_viable_return"]["found"])
        self.assertEqual(result["profile"]["name"], "Work commute")
        with self.assertRaises(ValueError):
            mcp.call_tool("atlas_commute_evaluate", {
                "profile": "missing", "date": "2026-11-17",
                "depart_time": 25200, "return_time": 61200,
            })


if __name__ == "__main__":
    unittest.main()
