# Step 6: Native Android visual offline journey planner (draft)

User selected **D: map-based journey planning**. The new `OfflinePlannerActivity` uses only installed SQLite GTFS data and optional local `streets.sqlite`. No network calls, remote map tiles, GPS permissions or cloud dependencies.

## Implemented

- Search stops by name or GTFS ID with case-insensitive filtering, deterministic sorting, and exact-name prioritization.
- Select origin and destination from search results or by tapping a stop marker on a custom geographic canvas.
- Show selected origin/destination distinctly, with a toggle for which endpoint to choose.
- Calculate native Kotlin scheduled journeys using the existing offline routing engine and optional OSM street graph.
- Display named stop-to-stop itinerary legs, departure/arrival times, estimated walking labels, and an honest no-result message.
- Search/selection/time formatting tests in `JourneyUiModelTest.kt` (nine synthetic JUnit cases).

## Testing

Run `./gradlew testDebugUnitTest` in `android/` with a compatible Android SDK/JDK 17 and build environment. Install agency packs using the existing LAN flow, then disable Wi-Fi and test stop search, map selection, and itinerary planning. **No Gradle compile, test execution, emulator run, or device validation occurred in this session.**

## Limits

- This is a geographic stop scatter plot, **not** an offline street basemap. It does not draw roads, transit lines, transfer geometries or map tiles. A future offline vector map is required.
- Canvas is not yet pannable/zoomable and the full regional extent may make densely clustered stops hard to tap; search is the alternative.
- Stop data is loaded in memory. Regional-scale performance and accessibility (screen reader semantics, keyboard navigation, contrast, touch target sizes) need verification.
- Transit results depend on the Step 4 Kotlin routing engine, which still needs timetable correctness, Gradle compilation and real-feed testing. No assertion that the app is production-ready.
- A street graph must still be manually installed for graph-derived walking transfer estimates. Geometric estimates remain when absent.
- No current-location tracking or automatic network downloads were added.

Next decision: validate/harden the Android build, add an offline vector basemap, or improve stop/map interaction and accessibility.
