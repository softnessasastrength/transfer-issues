#!/usr/bin/env python3
"""Small dependency-free MCP server for the local Transit Atlas API.

The process speaks newline-delimited JSON-RPC on stdin/stdout.  It does not
start the Atlas HTTP server; run ``python3 scripts/run_local.py`` separately
and point ATLAS_URL at it when using a different port.
"""
import json
import os
import pathlib
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
try:
    from .. import percival_memory
except ImportError:  # direct execution as scripts/atlas_mcp.py
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import percival_memory


ATLAS_URL = os.environ.get("ATLAS_URL", "http://127.0.0.1:8000").rstrip("/")
PROTOCOL_VERSION = "2024-11-05"


TOOLS = [
    {
        "name": "atlas_meta",
        "description": "Inspect loaded Transit Atlas feeds, routes, stops, limitations, and station-code metadata.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "atlas_search_stops",
        "description": "Search loaded transit stops by name or ID, optionally restricted to a feed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Stop name, station code, or feed-qualified ID."},
                "feed": {"type": "string", "description": "Optional feed ID such as cttransit, mbta, pvta, or amtrak."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_coverage",
        "description": "Show service coverage and source status for a specific service date.",
        "inputSchema": {
            "type": "object",
            "properties": {"date": {"type": "string", "description": "YYYY-MM-DD; defaults to the server date."}},
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_search_routes",
        "description": "Search loaded transit routes by short name, route ID, long name, or agency. Use this before answering questions about a route number.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Route number, name, or ID such as 905 or hartford:905."},
                "feed": {"type": "string", "description": "Optional feed ID."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_route_report",
        "description": "Produce an evidence-first report for a route: loaded identity, operator/feed, source status, service coverage and limitations. Use this for questions like 'tell me about route 905'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Route number, name, or ID."},
                "date": {"type": "string", "description": "Optional YYYY-MM-DD service date."},
                "feed": {"type": "string", "description": "Optional feed ID to disambiguate duplicate route numbers."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_departures",
        "description": "List scheduled departures from a loaded stop on a service date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stop": {"type": "string", "description": "Feed-qualified stop ID."},
                "date": {"type": "string", "description": "YYYY-MM-DD."},
                "route": {"type": "string", "description": "Optional feed-qualified route ID."},
            },
            "required": ["stop", "date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_live_status",
        "description": "Query an opt-in live provider overlay. Live status is separate from scheduled routing and may be unknown or stale.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "default": "mbta", "description": "Verified provider, currently mbta."},
                "route": {"type": "string", "description": "Optional feed-qualified route ID such as mbta:Red."},
                "stop": {"type": "string", "description": "Optional feed-qualified stop ID such as mbta:place-pktrm."},
                "include_alerts": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_fare",
        "description": "Calculate a supported scheduled fare, currently CTrail Hartford Line direct fares and CTtransit regular local fares.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_stop": {"type": "string", "description": "Origin stop ID."},
                "to_stop": {"type": "string", "description": "Destination stop ID."},
                "route": {"type": "string", "description": "Optional route ID, for example hartford:HART."},
            },
            "required": ["from_stop", "to_stop"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_plan_trip",
        "description": "Plan a scheduled trip between loaded stops. Results are timetable feasibility, not live arrivals or guaranteed connections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_stop": {"type": "string"},
                "to_stop": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD."},
                "time": {"type": "integer", "minimum": 0, "maximum": 86399, "description": "Departure time as seconds after midnight."},
                "deadline": {"type": "integer", "minimum": 0, "maximum": 172799},
                "kind": {"type": "string", "enum": ["depart", "latest"], "default": "depart"},
                "return_trip": {"type": "boolean", "default": False},
                "visit_seconds": {"type": "integer", "minimum": 0, "maximum": 86400, "default": 3600},
                "include_optional": {"type": "boolean", "default": False},
                "mode": {"type": "string", "enum": ["walk", "scooter"], "default": "walk"},
                "radius": {"type": "integer", "minimum": 0, "maximum": 3000, "default": 500},
                "route_chain": {"type": "array", "items": {"type": "string"}, "description": "Optional ordered feed-qualified route IDs to explore."},
            },
            "required": ["from_stop", "to_stop", "date", "time"],
            "additionalProperties": False,
        },
    },
    {
        "name": "atlas_come_to_me",
        "description": "Build a protected visit plan: guest origin to host stop, time to stay, return journey and latest safe return. This never sends an invitation or books anything.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "guest_from": {"type": "string", "description": "Guest origin stop ID."},
                "host_stop": {"type": "string", "description": "Host/destination stop ID."},
                "date": {"type": "string", "description": "YYYY-MM-DD."},
                "depart_time": {"type": "integer", "minimum": 0, "maximum": 86399},
                "return_deadline": {"type": "integer", "minimum": 0, "maximum": 172799},
                "visit_seconds": {"type": "integer", "minimum": 0, "maximum": 86400, "default": 3600},
                "include_optional": {"type": "boolean", "default": False},
                "mode": {"type": "string", "enum": ["walk", "scooter"], "default": "walk"},
                "radius": {"type": "integer", "minimum": 0, "maximum": 3000, "default": 500},
            },
            "required": ["guest_from", "host_stop", "date", "depart_time", "return_deadline"],
            "additionalProperties": False,
        },
    },
    {
        "name": "percival_get_preferences",
        "description": "Read Percival's explicitly saved local trip preferences. These are device-local and never inferred from conversation.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "percival_set_preferences",
        "description": "Save explicit local trip preferences such as home stop, default origin/host, departure window, return deadline, mode and walking radius.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "home_stop": {"type": "string"}, "default_origin": {"type": "string"}, "default_host": {"type": "string"},
                "default_depart_time": {"type": "integer", "minimum": 0, "maximum": 172799},
                "default_return_deadline": {"type": "integer", "minimum": 0, "maximum": 172799},
                "mode": {"type": "string", "enum": ["walk", "scooter"]}, "radius": {"type": "integer", "minimum": 0, "maximum": 3000},
            },
            "minProperties": 1, "additionalProperties": False,
        },
    },
    {
        "name": "percival_clear_preferences",
        "description": "Clear all explicitly saved local Percival trip preferences after the user asks to forget them.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _api(path, params=None):
    url = ATLAS_URL + path
    if params:
        url += "?" + urlencode(params)
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=30) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            return data
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            detail = {"error": str(exc)}
        raise RuntimeError("Atlas API %s: %s" % (exc.code, detail.get("error", detail)))
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Atlas API is unavailable at %s: %s" % (ATLAS_URL, exc))


def call_tool(name, args):
    args = args or {}
    if name == "atlas_meta":
        return _api("/api/v1/meta")
    if name == "atlas_search_stops":
        return _api("/api/v1/stops", {"q": args["query"], "feed": args.get("feed", ""), "limit": args.get("limit", 20)})
    if name == "atlas_coverage":
        return _api("/api/v1/coverage", {"date": args["date"]} if args.get("date") else None)
    if name == "atlas_search_routes":
        query = str(args["query"]).casefold()
        feed = str(args.get("feed", "")).casefold()
        limit = int(args.get("limit", 20))
        routes = _api("/api/v1/meta").get("routes", [])
        matches = []
        for route in routes:
            haystack = " ".join(str(route.get(key, "")) for key in ("id", "short", "long", "agency", "feed")).casefold()
            if query in haystack and (not feed or str(route.get("feed", "")).casefold() == feed):
                matches.append(route)
        return matches[:max(1, min(limit, 100))]
    if name == "atlas_route_report":
        query = str(args["query"])
        matches = call_tool("atlas_search_routes", {"query": query, "feed": args.get("feed", ""), "limit": 100})
        meta = _api("/api/v1/meta")
        source_by_id = {source.get("id"): source for source in meta.get("sources", [])}
        return {
            "status": "matched" if matches else "unknown",
            "query": query,
            "matched_routes": matches,
            "sources": [source_by_id.get(route.get("feed"), {"id": route.get("feed"), "status": "unknown"}) for route in matches],
            "coverage": _api("/api/v1/coverage", {"date": args["date"]}) if args.get("date") else None,
            "limitations": ["Loaded scheduled data only; not live arrivals", "A route match does not prove service on every date", "Route numbers may be duplicated across feeds"],
        }
    if name == "atlas_departures":
        params = {"stop": args["stop"], "date": args["date"]}
        if args.get("route"):
            params["route"] = args["route"]
        return _api("/api/v1/departures", params)
    if name == "atlas_live_status":
        return _api("/api/v1/live", {
            "provider": args.get("provider", "mbta"),
            "route": args.get("route", ""),
            "stop": args.get("stop", ""),
            "alerts": "1" if args.get("include_alerts", True) else "0",
        })
    if name == "atlas_fare":
        params = {"from": args["from_stop"], "to": args["to_stop"]}
        if args.get("route"):
            params["route"] = args["route"]
        return _api("/api/v1/fares", params)
    if name == "atlas_plan_trip":
        params = {
            "from": args["from_stop"], "to": args["to_stop"], "date": args["date"],
            "time": args["time"], "deadline": args.get("deadline", 86399),
            "kind": args.get("kind", "depart"), "mode": args.get("mode", "walk"),
            "radius": args.get("radius", 500), "return": "1" if args.get("return_trip", False) else "0",
            "visit": args.get("visit_seconds", 3600),
            "routes": ",".join(args.get("route_chain", [])),
        }
        if args.get("include_optional", False):
            params["include_optional"] = "1"
        return _api("/api/v1/plan", params)
    if name == "atlas_come_to_me":
        params = {
            "from": args["guest_from"], "to": args["host_stop"], "date": args["date"],
            "time": args["depart_time"], "deadline": args["return_deadline"],
            "return": "1", "visit": args.get("visit_seconds", 3600),
            "mode": args.get("mode", "walk"), "radius": args.get("radius", 500),
        }
        if args.get("include_optional", False):params["include_optional"]="1"
        result = _api("/api/v1/plan", params)
        return {
            "status": "feasible" if result.get("found") and result.get("return", {}).get("found") else ("outbound_only" if result.get("found") else "unknown"),
            "outbound": result,
            "return_trip": result.get("return"),
            "latest_safe_return": result.get("latest_return"),
            "draft_only": True,
            "limitations": ["Scheduled data only; not live arrivals or guaranteed connections", "Walking and scooter links are geographic estimates", "This prepares a plan but does not message, book or spend"],
        }
    if name == "percival_get_preferences":
        return {"preferences": percival_memory.get(), "storage": "device-local", "inferred": False}
    if name == "percival_set_preferences":
        return {"preferences": percival_memory.set_values(args), "storage": "device-local", "inferred": False}
    if name == "percival_clear_preferences":
        return {"preferences": percival_memory.clear(), "storage": "device-local", "inferred": False}
    raise ValueError("Unknown MCP tool: " + name)


def result_for(value):
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}], "structuredContent": value}


def dispatch(message):
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "percival-transit-atlas", "version": "0.1.0"}}}
    if method == "notifications/initialized" or method == "notifications/cancelled":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            return {"jsonrpc": "2.0", "id": request_id, "result": result_for(call_tool(params["name"], params.get("arguments")))}
        except (KeyError, ValueError, RuntimeError) as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": {"isError": True, "content": [{"type": "text", "text": str(exc)}]}}
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found: " + str(method)}}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = dispatch(message)
        except (ValueError, TypeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Invalid JSON-RPC request: " + str(exc)}}
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
