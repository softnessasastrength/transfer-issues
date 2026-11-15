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


def status(provider: str = "mbta", route: str = "", stop: str = "", include_alerts: bool = True) -> dict:
    """Provider-neutral entry point used by the HTTP API and future adapters."""
    provider = (provider or "mbta").lower()
    if provider in {"mbta", "mbta_v3"}:
        return mbta(route, stop, include_alerts)
    return _unknown(provider, "No verified live provider is configured for this agency yet.")
