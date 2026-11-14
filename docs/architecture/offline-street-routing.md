# Step 3: OpenStreetMap + SQLite offline street graph

**Owner decision B.** Python prepares offline OSM graph packs on the Mac mini; Android will eventually read the same SQLite schema and run its own Kotlin pathfinder. This PR implements the Python proof of concept, not the Kotlin port.

## Build from a local OSM XML extract

```bash
python3 scripts/build_street_graph.py --osm /path/to/your-local-region.osm --output build/offline-network/streets.sqlite
ATLAS_STREET_GRAPH=build/offline-network/streets.sqlite bash atlas-lan.sh
python3 -m unittest tests.test_street_routing tests.test_interagency_transfers -v
```

The builder reads **local OSM XML**, not PBF. Obtain an appropriately licensed local extract separately; the tool does not fetch network data or silently install new agencies. Keep OSM source files and generated SQLite packs outside Git. OSM attribution and ODbL obligations must be reviewed before redistribution.

## Data model

`nodes(id,lat,lon)`, `edges(src,dst,meters,walk,cycle)`, `metadata(key,value)`. Directed edges support basic cycling one-way restrictions. Access tags and highway classifications exclude some prohibited paths. SQLite is atomically activated after integrity checking. The source SHA-256 is stored for provenance.

`street_routing.StreetGraph` performs nearest-node snapping (100 m maximum by default) and Dijkstra shortest paths for walk/cycle. It returns path node IDs, coordinates, estimated meters/time, snap distances, and explicit limitations. The Python transit planner loads this file **only** when `ATLAS_STREET_GRAPH` is configured. If graph routing is enabled and a stop-to-stop path cannot be found, no straight-line fallback is used. Without a configured graph, Step 2 geometric estimates remain in effect.

## Critical limitations

- Not yet a production OSM router: **no PBF import**, no full OSM relations, turn restrictions, gates/barriers, ferry access, complex conditional access, elevation/grade, scooter-specific legality, accessibility audits, or protected crossings.
- OSM snapping to the nearest node can be misleading near parallel streets, bridges and barriers; a returned route is **graph-derived but still estimated**, not guaranteed safe/legal/traversable.
- The builder holds all OSM nodes and eligible ways in memory, appropriate only for modest extracts. Larger regional datasets need a streaming/PBF importer, spatial index, and bounded-memory processing.
- The current Dijkstra implementation loads nodes/edges into RAM and is suitable for a proof of concept, not yet multi-state scale.
- No native Android Kotlin pathfinder or licensed offline basemap in this PR. The Mac mini LAN planner uses graph transfers; airplane-mode Android still needs the next implementation stage.
- Existing data packs are untouched; source file, map graph and user data are not committed. The script does not download anything.
- Six synthetic tests committed; not executed in this session. Real OSM extract, route validity, performance, macOS and Android device testing remain outstanding.

Next decision: whether to prioritize Kotlin offline route computation first or expand the OSM importer/graph completeness before the Android port.
