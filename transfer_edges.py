"""Offline, direction-aware transfer edges. Geometric paths are estimates, never verified sidewalks."""
import math
from collections import defaultdict

WALK_MPS = 4.5 / 3.6
CYCLE_MPS = 12 / 3.6
DETOUR = 1.3


def meters(a, b):
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dy = lat2 - lat1
    dx = math.radians(b["lon"] - a["lon"])
    h = math.sin(dy / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dx / 2) ** 2
    return 12742000 * math.asin(min(1, math.sqrt(h)))


def transfer_rules(stops, transfers):
    """Expand parent-station rules to child platforms; explicit rules win."""
    children = defaultdict(list)
    for sid, stop in stops.items():
        if stop.get("parent"):
            children[stop["parent"]].append(sid)
    rules = {}
    for rule in transfers:
        aa = [rule["a"]] + children[rule["a"]]
        bb = [rule["b"]] + children[rule["b"]]
        for a in aa:
            for b in bb:
                if a in stops and b in stops:
                    rules[a, b] = (int(rule["type"]), int(rule.get("seconds") or 0))
    return rules


def edges(stops, transfers, *, radius=500, mode="walk"):
    """Return directed adjacency with explicit rules and estimated nearby paths.

    GTFS type 3 forbids a transfer, including when within geographic radius.
    Type 2 enforces a minimum transfer time. Type 1/0 are explicitly published
    connections; still apply conservative walking time for distinct locations.
    No cross-agency edge is synthesized outside the requested radius.
    """
    if not 0 <= radius <= 5000:
        raise ValueError("Transfer radius must be between 0 and 5000 meters")
    if mode not in ("walk", "cycle"):
        raise ValueError("Unsupported transfer mode")
    speed = WALK_MPS if mode == "walk" else CYCLE_MPS
    rules = transfer_rules(stops, transfers)
    grid = defaultdict(list)
    for sid, stop in stops.items():
        if stop.get("lat") is None or stop.get("lon") is None:
            continue
        grid[math.floor(stop["lat"] * 100), math.floor(stop["lon"] * 100)].append(sid)
    output = {}
    # 0.01 degree grid: conservative latitude search; longitude cells
    # expanded for the regional latitude, including eastern/western edges.
    for sid, source in stops.items():
        if source.get("lat") is None or source.get("lon") is None:
            output[sid] = []
            continue
        lat, lon = source["lat"], source["lon"]
        lat_cells = math.ceil(radius / 110000 * 100) + 1
        lon_cells = math.ceil(radius / max(1, 111000 * math.cos(math.radians(lat))) * 100) + 1
        y, x = math.floor(lat * 100), math.floor(lon * 100)
        candidates = set()
        for yy in range(y - lat_cells, y + lat_cells + 1):
            for xx in range(x - lon_cells, x + lon_cells + 1):
                candidates.update(grid.get((yy, xx), ()))
        # Explicit published transfers may exceed the default proximity radius.
        candidates.update(b for a, b in rules if a == sid)
        found = []
        for dest in sorted(candidates):
            if dest == sid:
                continue
            rule = rules.get((sid, dest))
            if rule and rule[0] == 3:
                continue
            d = meters(source, stops[dest])
            if d > radius and rule is None:
                continue
            if rule is None and radius == 0:
                continue
            # For explicit long-distance transfers, straight-line timing is
            # still an estimate; no claim of a traversable pedestrian path.
            length = math.ceil(d * DETOUR)
            seconds = max(60, math.ceil(length / speed))
            if rule and rule[0] == 2:
                seconds = max(seconds, rule[1])
            found.append({"to": dest, "seconds": seconds, "meters": length,
                          "estimated": True, "source": "official" if rule else "proximity",
                          "minimum_transfer_seconds": rule[1] if rule and rule[0] == 2 else 0})
        output[sid] = found
    return output
