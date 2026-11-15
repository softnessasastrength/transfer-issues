"""Read-only offline SQLite street shortest paths; conservative snap thresholds."""
import heapq
import math
from pathlib import Path
import sqlite3

from transfer_edges import meters


class NoStreetPath(ValueError):
    pass


class StreetGraph:
    def __init__(self, path):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as db:
            self.nodes = {row[0]: {"lat": row[1], "lon": row[2]}
                          for row in db.execute("SELECT id,lat,lon FROM nodes")}
            self.adj = {"walk": {}, "cycle": {}}
            for a, b, length, walk, cycle in db.execute(
                    "SELECT src,dst,meters,walk,cycle FROM edges"):
                for mode, allowed in (("walk", walk), ("cycle", cycle)):
                    if allowed:
                        self.adj[mode].setdefault(a, []).append((b, length))

    def snap(self, point, mode="walk", max_meters=100):
        if mode not in self.adj:
            raise ValueError("Unknown travel mode")
        eligible = set(self.adj[mode])
        eligible.update(b for links in self.adj[mode].values() for b, _ in links)
        closest = min(((meters(point, self.nodes[n]), n) for n in eligible),
                      default=(float("inf"), None))
        if closest[0] > max_meters:
            raise NoStreetPath("No accessible graph node within snap threshold")
        return closest

    def route(self, start, end, *, mode="walk", snap_meters=100):
        """Shortest permitted graph route with off-graph approach costs.

        Snap segments are estimates, not verified paths. A caller must not
        label the entire route as a verified accessible sidewalk.
        """
        if mode not in self.adj:
            raise ValueError("Unknown travel mode")
        a_dist, a = self.snap(start, mode, snap_meters)
        b_dist, b = self.snap(end, mode, snap_meters)
        best = {a: 0.0}
        previous = {}
        heap = [(0.0, a)]
        while heap:
            cost, node = heapq.heappop(heap)
            if cost > best.get(node, float("inf")):
                continue
            if node == b:
                break
            for dest, length in self.adj[mode].get(node, ()):
                candidate = cost + length
                if candidate < best.get(dest, float("inf")):
                    best[dest] = candidate
                    previous[dest] = node
                    heapq.heappush(heap, (candidate, dest))
        if b not in best:
            raise NoStreetPath("No permitted connected street path")
        path = [b]
        while path[-1] != a:
            path.append(previous[path[-1]])
        path.reverse()
        length = best[b] + a_dist + b_dist
        speed = 4.5 / 3.6 if mode == "walk" else 12 / 3.6
        return {"meters": math.ceil(length), "seconds": max(60, math.ceil(length / speed)),
                "nodes": path, "geometry": [[self.nodes[n]["lat"], self.nodes[n]["lon"]] for n in path],
                "snap_meters": [round(a_dist, 1), round(b_dist, 1)],
                "source": "osm_graph", "estimated": True,
                "limitations": "Snapping, legal access, barriers and crossing safety not verified"}
