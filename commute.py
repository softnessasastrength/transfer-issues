"""F-009 commute profiles: evaluate a saved commute against a real date.

A profile (stored by :mod:`percival_memory`) holds only the *shape* of a
commute: home and work as Atlas stop IDs, a preferred route chain per
direction (outbound and return are separate; asymmetry is the normal case),
and declared rideshare legs where transit ends before the endpoint.  This
module evaluates that shape with the Atlas planner -- it never reimplements
routing; every transit answer comes from ``/api/v1/plan``.

Rideshare legs are estimates only (F-004 doctrine): a distance-based drive
time range, labelled as an estimate -- never a price, never a booking, and
no rideshare API is called.
"""
import math


# --- Rideshare estimate method --------------------------------------------
# Straight-line (haversine) distance between the two stops, scaled by a road
# circuity factor of 1.3 (roads are not straight lines; 1.3 is the standard
# planning approximation for a suburban road network), then converted to a
# time range using average drive speeds of 35-60 km/h.  The factor and the
# speeds are stated in every estimate so the number can be argued with.
ROAD_CIRCUITY = 1.3
DRIVE_SPEED_KMH = (35.0, 60.0)
RIDESHARE_LABEL = "rideshare — estimated drive, not a quote, not booked"
RIDESHARE_METHOD = (
    "Haversine straight-line distance x %.1f road circuity; "
    "drive time at %.0f-%.0f km/h average" % (ROAD_CIRCUITY, DRIVE_SPEED_KMH[0], DRIVE_SPEED_KMH[1])
)

# The last viable return is bounded to the service day: in GTFS extended
# time a service day runs past midnight (trips up to about 28:00 belong to
# the day just ended), so the search deadline is 28:00 -- a later bound
# would surface the *next* evening's service and call it tonight's.
SERVICE_DAY_END = 28 * 3600

LIMITATIONS = [
    "Scheduled data only; not live arrivals or guaranteed connections",
    "Preferred chains are honoured only where the loaded feeds run them on the evaluated date",
    "Rideshare legs are estimated drives, not quotes, and nothing is booked",
]


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def estimate_rideshare(from_info, to_info, from_stop, to_stop, target):
    """Distance-based drive estimate between two stop records.

    Returns an explicit ``unknown`` (never an invented number) when either
    stop's coordinates are unavailable.
    """
    estimate = {
        "kind": "rideshare",
        "from_stop": from_stop,
        "to_stop": to_stop,
        "to": target,
        "label": RIDESHARE_LABEL,
        "booked": False,
    }
    if not from_info or not to_info or from_info.get("lat") is None or to_info.get("lat") is None:
        estimate["status"] = "unknown"
        estimate["limitations"] = ["Stop coordinates unavailable in the loaded data; drive time not estimated."]
        return estimate
    straight = haversine_km(from_info["lat"], from_info["lon"], to_info["lat"], to_info["lon"])
    road = straight * ROAD_CIRCUITY
    low = max(1, round(road / DRIVE_SPEED_KMH[1] * 60))
    high = max(low, round(road / DRIVE_SPEED_KMH[0] * 60))
    estimate.update({
        "status": "estimated",
        "straight_line_km": round(straight, 2),
        "estimated_road_km": round(road, 2),
        "drive_minutes": [low, high],
        "method": RIDESHARE_METHOD,
    })
    return estimate


def lookup_stop(api, stop_id, route_hints=(), date=None):
    """Resolve a stop ID to its loaded record (exact ID match only).

    The stops endpoint searches names, not IDs, so coordinates are resolved
    through the route endpoint: each hinted route's published stop list is
    checked for the exact ID.  A stop that no hinted route serves stays
    unresolved (``None``) rather than being approximated.
    """
    for route in route_hints:
        params = {"id": route}
        if date:
            params["date"] = date
        try:
            data = api("/api/v1/route", params)
        except Exception:
            continue
        for stop in data.get("stops", []) or []:
            if stop.get("id") == stop_id:
                return stop
    return None


def _plan(api, origin, destination, date, time, deadline, chain=(), kind="depart", mode="walk"):
    params = {
        "from": origin, "to": destination, "date": date, "time": time,
        "deadline": deadline, "kind": kind, "mode": mode, "radius": 500,
    }
    if chain:
        params["routes"] = ",".join(chain)
    return api("/api/v1/plan", params)


def evaluate_direction(api, profile, direction, date, time, deadline=86399):
    """Evaluate one direction of a profile at a departure time.

    The declared chain is planned first; where it cannot run, the planner's
    unpinned answer is shown instead and the preference note says so.  Where
    the chain does run, an unpinned plan is also computed so the preference's
    time cost (if any) is stated rather than hidden.
    """
    outbound = direction == "outbound"
    origin = profile["home_stop"] if outbound else profile["work_stop"]
    endpoint = profile["work_stop"] if outbound else profile["home_stop"]
    target = "work" if outbound else "home"
    prefs = profile.get(direction) or {}
    chain = list(prefs.get("routes") or [])
    mode = prefs.get("mode", "walk")
    leg = next((item for item in profile.get("rideshare_legs", []) if item["to"] == target), None)
    transit_dest = leg["from_stop"] if leg else endpoint

    notes = []
    applied = None
    plan = None
    if chain:
        chained = _plan(api, origin, transit_dest, date, time, deadline, chain, mode=mode)
        if chained.get("found"):
            plan = chained
            applied = bool(chained.get("route_chain_matched", True))
            if applied:
                notes.append("Preferred chain applied: " + " then ".join(chain) + ".")
            else:
                notes.append(
                    "Preferred chain partially honoured: the loaded feeds reach the destination "
                    "without riding every declared route in order (" + " then ".join(chain) + ")."
                )
            best = _plan(api, origin, transit_dest, date, time, deadline, (), mode=mode)
            if best.get("found") and best.get("arrival", 0) < chained.get("arrival", 0):
                notes.append(
                    "The planner's unpinned best arrives %d minutes earlier; the declared chain was kept."
                    % ((chained["arrival"] - best["arrival"]) // 60)
                )
        else:
            notes.append(
                "Preferred chain could not be honoured on this date and time ("
                + " then ".join(chain) + "); showing the planner's unpinned answer instead."
            )
            plan = _plan(api, origin, transit_dest, date, time, deadline, (), mode=mode)
    else:
        plan = _plan(api, origin, transit_dest, date, time, deadline, (), mode=mode)

    result = {
        "direction": direction,
        "from_stop": origin,
        "to_stop": endpoint,
        "transit_to_stop": transit_dest,
        "date": date,
        "depart_time": time,
        "preference": {"chain": chain, "applied": applied, "notes": notes},
        "plan": plan,
        "found": bool(plan and plan.get("found")),
    }
    if leg:
        # Coordinate hints: the rideshare origin is the alighting stop of the
        # plan's final transit leg and is served by this direction's chain;
        # the endpoint is an endpoint of both directions' chains.
        from_hints = []
        if plan and plan.get("found"):
            transit_routes = [item.get("route") for item in plan.get("legs", []) if item.get("kind") == "transit"]
            if transit_routes:
                from_hints.append(transit_routes[-1])
        from_hints += [route for route in reversed(chain) if route not in from_hints]
        other_chain = list((profile.get("return" if outbound else "outbound") or {}).get("routes") or [])
        endpoint_hints = other_chain + [route for route in chain if route not in other_chain]
        estimate = estimate_rideshare(
            lookup_stop(api, leg["from_stop"], from_hints, date),
            lookup_stop(api, endpoint, endpoint_hints, date),
            leg["from_stop"], endpoint, target,
        )
        result["rideshare"] = estimate
        if result["found"] and estimate.get("status") == "estimated":
            low, high = estimate["drive_minutes"]
            result["estimated_final_arrival"] = [plan["arrival"] + low * 60, plan["arrival"] + high * 60]
    return result


def evaluate(api, profile, date, depart_time, return_time, deadline=86399):
    """Evaluate both directions of a commute profile for one date.

    The return direction always carries ``last_viable_return``: the latest
    departure at or after the requested return time that still completes the
    return transit leg that day (the atlas_come_to_me return-protection
    instinct, applied to the principal's own commute).
    """
    outbound = evaluate_direction(api, profile, "outbound", date, depart_time, deadline)
    ret = evaluate_direction(api, profile, "return", date, return_time, deadline)
    prefs = profile.get("return") or {}
    chain = list(prefs.get("routes") or [])
    mode = prefs.get("mode", "walk")
    latest = _plan(api, ret["from_stop"], ret["transit_to_stop"], date, return_time, SERVICE_DAY_END, chain, kind="latest", mode=mode)
    if chain and not latest.get("found"):
        latest = _plan(api, ret["from_stop"], ret["transit_to_stop"], date, return_time, SERVICE_DAY_END, (), kind="latest", mode=mode)
    ret["last_viable_return"] = latest
    return {
        "profile": {"id": profile["id"], "name": profile["name"]},
        "date": date,
        "outbound": outbound,
        "return": ret,
        "limitations": list(LIMITATIONS),
    }
