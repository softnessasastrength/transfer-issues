# Native Android offline street routing (draft)

User selected **B** from the latest architectural choice: port the Step 3 SQLite walking/cycling graph to Kotlin and integrate it into offline transit transfers.

## Implemented

- `OfflineStreetGraph.kt`: read-only Android SQLite loader for `atlas-street-v1` (`nodes`, directed `edges`, `metadata`); validates SQLite integrity and graph schema marker; directed Dijkstra for walking and cycling, with bounded nearest-node snapping and estimated time/distance.
- `OfflineRouter.read(..., streetGraph)`: when a graph is supplied, uses graph-derived walking time for official and nearby transfers. **No geometric fallback** when the graph is present but disconnected. Published forbidden transfers still suppress paths.
- `OfflinePlannerActivity`: automatically looks for `files/offline/streets.sqlite`. With it, use graph-derived transfer estimates; without it, retain Step 4's clearly labeled proximity estimates.
- `OfflineStreetGraphTest.kt`: seven synthetic JUnit tests covering directed paths, cycle restrictions, disconnected routes, snap limits, same-node timing, invalid mode, and snap distance.

## Local test installation

1. Generate `streets.sqlite` on the Mac mini using `python3 scripts/build_street_graph.py --osm region.osm --output build/offline-network/streets.sqlite`.
2. Build and install the Android **debug** app; launch it once. Transfer via Android Studio's Device Explorer to app-private `files/offline/streets.sqlite`, or via ADB:

```bash
adb push build/offline-network/streets.sqlite /data/local/tmp/streets.sqlite
adb shell 'run-as org.southernnewengland.transitatlas sh -c "mkdir -p files/offline && cat /data/local/tmp/streets.sqlite > files/offline/streets.sqlite"'
adb shell rm /data/local/tmp/streets.sqlite
```

3. Install approved transit agency packs using the existing LAN download flow; turn off Wi-Fi, open **Plan journey offline (Kotlin)**, and plan between actual installed stop IDs.
4. Run `./gradlew testDebugUnitTest` from `android/` if a wrapper is available. Otherwise configure the project's compatible Gradle/JDK 17 in Android Studio.

## Outstanding work and caution

- **Not compiled or executed in this session.** No claim of passing Kotlin tests, a working Android APK, or real OSM/GTFS integration validation.
- OSM graph is an experimental XML-derived subset. Barriers, turn restrictions, pedestrian crossings, sidewalk continuity, wheelchair access, steep grades and scooter legality are **not** verified. A returned path is still an estimate, not a safe-route guarantee.
- The graph is loaded in memory; nearest-node snapping and many pairwise graph searches are slow at full regional scale. Before production: spatial indexing, bounded queries, precomputed stop connectors, performance benchmarking, and chunked regional packs.
- No in-app street graph download, signed catalog, atomic street-pack update, rollback, or offline street basemap yet. Transit pack selection remains unchanged; no implicit agency downloads.
- A manually installed graph is trusted only as a local test artifact. The loader checks SQLite integrity and format but not SHA-256 provenance or a signed manifest.
- Existing Mac mini Python street routing and the Step 4 Kotlin timetable planner remain intact.

Next choice: focus on reproducible build/correctness validation, in-app street-pack installation, or regional graph performance.
