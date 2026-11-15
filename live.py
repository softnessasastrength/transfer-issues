"""Optional live-data overlays.

Live data is deliberately separate from ``routing.py``.  A provider outage,
stale prediction, or missing API key must never change scheduled feasibility.
The first provider is the official MBTA V3 JSON API.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MBTA_BASE = "https://api-v3.mbta.com"
CTTRANSIT_BASE = "https://cttprdtmgtfs.ctttrpcloud.com/TMGTFSRealTimeWebService"


def _route_filter(value: str) -> str:
    """Accept Atlas namespaced IDs (``mbta:Red``) or native MBTA IDs."""
    return value.split(":", 1)[1] if ":" in value else value


def _unknown(provider: str, reason: str, source_url: str | None = None) -> dict:
    return {
        "status": "unknown",
        "provider": provider,
        "source_url": source_url,
        "as_of": None,
        "predictions": [],
        "alerts": [],
        "limitations": [reason, "Live status is informational and does not alter scheduled routing."],
    }


def _fetch(path: str, params: dict[str, str], timeout: float = 8.0) -> tuple[dict, str]:
    query = urlencode(params)
    url = f"{MBTA_BASE}{path}?{query}" if query else f"{MBTA_BASE}{path}"
    headers = {"Accept": "application/vnd.api+json"}
    if os.environ.get("MBTA_API_KEY"):
        headers["x-api-key"] = os.environ["MBTA_API_KEY"]
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS provider
        return json.load(response), url


def _fetch_url(url: str, timeout: float = 8.0) -> dict:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS provider
        return json.load(response)


def _resource_rows(payload: dict) -> list[dict]:
    rows = []
    for item in payload.get("data", []):
        attrs = item.get("attributes") or {}
        rows.append({"id": item.get("id"), **attrs, "relationships": item.get("relationships") or {}})
    return rows


def mbta(route: str = "", stop: str = "", include_alerts: bool = True) -> dict:
    """Return normalized MBTA predictions and alerts, or an honest unknown.

    This function performs no routing and has no fallback to timetable data.
    """
    route_id = _route_filter(route.strip()) if route.strip() else ""
    stop_id = _route_filter(stop.strip()) if stop.strip() else ""
    params: dict[str, str] = {"page[limit]": "50", "sort": "departure_time"}
    if route_id:
        params["filter[route]"] = route_id
    if stop_id:
        params["filter[stop]"] = stop_id
    try:
        predictions, prediction_url = _fetch("/predictions", params)
        alerts_payload, alert_url = ({"data": []}, None)
        if include_alerts:
            alert_params = {"page[limit]": "50", "sort": "-severity"}
            if route_id:
                alert_params["filter[route]"] = route_id
            alerts_payload, alert_url = _fetch("/alerts", alert_params)
    except Exception as exc:  # Provider errors are data, not server failures.
        return _unknown("mbta_v3", f"MBTA live provider unavailable: {type(exc).__name__}")

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    return {
        "status": "live",
        "provider": "mbta_v3",
        "as_of": now,
        "source_url": prediction_url,
        "predictions": _resource_rows(predictions),
        "alerts": _resource_rows(alerts_payload),
        "limitations": [
            "Provider timestamps and coverage can be stale or incomplete.",
            "Live status is informational and does not alter scheduled routing.",
            "No guarantee of vehicle arrival, boarding, transfer, or seat availability.",
        ],
        "alert_source_url": alert_url,
    }


def _ct_entities(payload: dict) -> list[dict]:
    return payload.get("entity", []) if isinstance(payload, dict) else []


def cttransit(route: str = "", stop: str = "", include_alerts: bool = True) -> dict:
    """Read CTtransit's official JSON realtime feeds.

    CTtransit publishes JSON and GTFS-realtime feeds. The JSON adapter avoids a
    protobuf dependency while preserving the provider's trip/vehicle/alert
    separation. It is still informational and never participates in routing.
    """
    route_id = _route_filter(route.strip()) if route.strip() else ""
    stop_id = _route_filter(stop.strip()) if stop.strip() else ""
    urls = {
        "trips": f"{CTTRANSIT_BASE}/TripUpdate/TripUpdates.json",
        "vehicles": f"{CTTRANSIT_BASE}/Vehicle/VehiclePositions.json",
        "alerts": f"{CTTRANSIT_BASE}/Alert/Alerts.json",
    }
    try:
        trips = _fetch_url(urls["trips"])
        vehicles = _fetch_url(urls["vehicles"])
        alerts = _fetch_url(urls["alerts"]) if include_alerts else {"entity": [], "header": trips.get("header", {})}
    except Exception as exc:
        return _unknown("cttransit_json", f"CTtransit live provider unavailable: {type(exc).__name__}")

    predictions = []
    for entity in _ct_entities(trips):
        update = entity.get("trip_update") or {}
        trip = update.get("trip") or {}
        rid = str(trip.get("route_id") or "")
        if route_id and rid != route_id:
            continue
        for item in update.get("stop_time_update", [])[:5]:
            if stop_id and str(item.get("stop_id") or "") != stop_id:
                continue
            event = item.get("departure") or item.get("arrival") or {}
            predictions.append({
                "id": entity.get("id"), "route_id": rid, "trip_id": trip.get("trip_id"),
                "stop_id": item.get("stop_id"), "stop_sequence": item.get("stop_sequence"),
                "time": event.get("time"), "delay": event.get("delay", 0),
                "schedule_relationship": item.get("schedule_relationship"),
            })
    vehicle_rows = []
    for entity in _ct_entities(vehicles):
        vehicle = entity.get("vehicle") or {}
        trip = vehicle.get("trip") or {}
        rid = str(trip.get("route_id") or "")
        if route_id and rid != route_id:
            continue
        vehicle_rows.append({"id": entity.get("id"), "route_id": rid, "vehicle": vehicle.get("vehicle"), "position": vehicle.get("position"), "timestamp": vehicle.get("timestamp")})
    alert_rows = []
    for entity in _ct_entities(alerts):
        alert = entity.get("alert") or {}
        affected = alert.get("informed_entity") or []
        if route_id and affected and not any(str(x.get("route_id") or "") == route_id for x in affected):
            continue
        if stop_id and affected and not any(str(x.get("stop_id") or "") == stop_id for x in affected):
            continue
        alert_rows.append({"id": entity.get("id"), "header": alert.get("header_text"), "description": alert.get("description_text"), "informed_entity": affected})
    header = trips.get("header") or {}
    timestamp = header.get("timestamp")
    return {
        "status": "live", "provider": "cttransit_json", "as_of": _dt.datetime.fromtimestamp(timestamp, _dt.timezone.utc).isoformat() if timestamp else _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "source_url": urls["trips"], "predictions": predictions, "vehicles": vehicle_rows, "alerts": alert_rows,
        "limitations": ["CTtransit publishes provider data; this app does not guarantee freshness or arrival.", "Live status is informational and does not alter scheduled routing.", "No guarantee of vehicle arrival, boarding, transfer, accessibility, or seat availability."],
        "alert_source_url": urls["alerts"],
    }


def status(provider: str = "mbta", route: str = "", stop: str = "", include_alerts: bool = True) -> dict:
    """Provider-neutral entry point used by the HTTP API and future adapters."""
    provider = (provider or "mbta").lower()
    if provider in {"mbta", "mbta_v3"}:
        return mbta(route, stop, include_alerts)
    if provider in {"cttransit", "cttransit_json"}:
        return cttransit(route, stop, include_alerts)
    return _unknown(provider, "No verified live provider is configured for this agency yet.")
