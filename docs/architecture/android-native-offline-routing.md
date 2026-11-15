# Step 4: Native Android offline timetable routing (draft)

Owner selected **A: native Kotlin offline routing**. This PR implements a Kotlin timetable journey engine and a basic Android screen. It does not merge or replace any Python or LAN code.

## What's implemented

- `OfflineRouter.kt`: reads only explicitly installed agency SQLite packs from Android app-private storage, validates SQLite integrity, combines stops, GTFS calendar/exception-based service days (previous/current/next), connection times, explicit directed transfer rules and estimated nearby walking transfers.
- Kotlin connection-scan and walking closure, including a configurable 180-second default transfer buffer. The app does **not** call the Mac mini or internet to calculate.
- `OfflinePlannerActivity.kt`: simple native UI with origin/destination stop IDs, service date and departure HH:MM; returns a scheduled itinerary or an honest no-result state.
- Main screen button opens the planner; manifest registers the non-exported activity.
- `OfflineRouterTest.kt`: seven synthetic JUnit tests for walk-to-board, buffer rejection, missed connection, no invented route, same-stop route, invalid stop and chained walking.
- Existing LAN WebView, package download UI, route-shape preview, Python server and street graph preserved.

## How to try it

Build the **debug** Android project in Android Studio with JDK 17 and SDK 35. Use the existing LAN onboarding to explicitly download agency packs. Tap **Plan journey offline (Kotlin)**, enter exact GTFS stop IDs and a service date/time, and calculate. Repeat in airplane mode. The Mac mini can be powered off for this specific calculation after packs have been installed.

Run JVM tests from `android/` with `./gradlew testDebugUnitTest` if a Gradle wrapper is available, or use your locally installed compatible Gradle. **No Gradle build, unit tests or physical device tests were executed in this session.**

## Limitations and known gaps

- The Kotlin planner uses individual installed agency databases. It does not yet install/consume the Step 1 unified network file or the Step 3 SQLite pedestrian street graph. Walking connections are geometric estimates, not verified sidewalks.
- This is a **basic earliest-arrival timetable prototype**, not production-correct multi-criteria routing. It needs tests for service calendars/exception dates, 24+ hour times, pickup/dropoff restrictions, GTFS transfer type semantics, same-trip continuity, stop-parent rules, service frequency trips, accessibility, cross-midnight travel, and comparison with Python results.
- It currently reads all selected stop and timetable records into memory and uses a spatial bucket index for proximity. Regional scale and performance must be benchmarked on actual Android hardware.
- Source GTFS pack integrity is checked as SQLite but the app's existing installer performs manifest SHA-256 verification. Catalog authenticity and production signatures remain unresolved.
- No actual street basemap, offline turn-by-turn walking instructions, geocoding, stop search/autocomplete or full UX polish. Stop IDs must be entered manually.
- No cloud routing is required; downloaded schedules may become stale. Real-time delays are not available offline.

## Next decision

Prioritize correctness and integration: **A** validate/test Kotlin against Python and real feeds; **B** connect Step 3 street graph to Kotlin; **C** build a unified SQLite package installer for Android; **D** add searchable stop picker and map-based journey UI.
