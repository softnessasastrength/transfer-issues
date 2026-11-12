# Android Studio starter: offline CT + PVTA Transit Atlas

This is a **native Android proof-of-concept shell** using Kotlin and Android's built-in SQLite APIs. It opens offline, detects a local database, and lists up to 100 routes from it. It does **not** yet offer an offline map, trip routing, or GPS.

## Open in Android Studio

1. Install Android Studio with Android SDK 35 and JDK 17.
2. Clone the repo and check out `feature/android-offline-shell`.
3. Open the **android/** directory as a project, let Gradle sync, then Run on an emulator or your phone.
4. Android Studio can generate the missing Gradle wrapper for this source skeleton, or use your locally installed Gradle 8.9 to generate it. No wrapper binary is committed.

## Build and install a test data pack

From repo root, first prepare valid transit feeds and import them into `data/atlas.sqlite`. Then:

```bash
python3 scripts/build_offline_poc.py --allow-partial --output build/offline-ct-pvta-partial
adb shell run-as org.southernnewengland.transitatlas mkdir -p files/offline
adb push build/offline-ct-pvta-partial/atlas.sqlite /data/local/tmp/atlas.sqlite
adb shell 'run-as org.southernnewengland.transitatlas sh -c "cat /data/local/tmp/atlas.sqlite > files/offline/atlas.sqlite"'
adb shell rm /data/local/tmp/atlas.sqlite
```

Run the app once before using `run-as` so its private app directory exists. `run-as` works for the debug build. The command assumes a USB-connected device with adb debugging enabled. This is **development-only** and does not constitute a production data-pack installer.

Turn on airplane mode and relaunch the app: it should still list locally stored routes. This is the first acceptance check, **not** proof of offline journey planning.

## Planned offline features

- Shared CT/PVTA SQLite packs and manifest checksum verification
- Offline schedule browser, calendar/exception logic, and native trip routing
- Licensed offline vector map packs and local street/path routing
- Native foreground GPS, with optional background service only after explicit permission and purpose
- Exploration mode: show all routes by color, route discovery, stops near me, and random destinations
- Optional online-only overlays for live vehicle positions and alerts, clearly labeled
- Safe updates with expiry warnings and rollback; never silently replace user notes

No API keys, credentials, databases, GTFS ZIPs or generated build outputs should be committed. Android's background APIs remain permission- and battery-policy-limited.

## Experimental Mac mini LAN client (new)

See `docs/architecture/lan-android-poc.md`. Build the debug Android variant, run `bash atlas-lan.sh` on the Mac mini, enter its private LAN URL, select agencies and explicitly confirm package downloads. The app can use the existing server planner over Wi-Fi and display a rough native offline GTFS shape/stop map after downloading. It is not a full offline route planner or street map; no device compilation was verified.

## Native Kotlin offline journey planner (Step 4 draft)

See `docs/architecture/android-native-offline-routing.md`. The main screen now opens a native offline journey planner that reads previously installed GTFS agency SQLite files without a Mac mini or network connection. Enter GTFS stop IDs, date and HH:MM. This is a scheduled journey POC with estimated walking transfers; it does not yet consume the OSM street graph. Seven synthetic Kotlin JUnit tests are committed but not executed. Compile and run `testDebugUnitTest` before claiming device readiness.

## Native offline street routing (draft)

See `docs/architecture/android-native-street-routing.md`. Build `streets.sqlite` on the Mac mini and manually copy it into the Android app-private `files/offline/` folder for debug testing. The native planner then uses graph-derived walking transfer times. This is not an in-app street pack installer or a verified safe pedestrian route. Seven Kotlin synthetic tests committed, not executed.

## Step 6 visual journey planner (draft)

The native offline planner now supports stop-name/ID search, map-tap origin/destination selection and readable itinerary legs. It draws geographic stop points without internet; no offline street basemap yet. See `docs/architecture/android-visual-journey-planner.md`. Nine synthetic Kotlin tests committed, not executed.
