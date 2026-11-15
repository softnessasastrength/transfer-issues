# Step 7: Routing verification and repair (draft)

Owner chose A: verify and harden existing Android and Python routing. Preserve all previous features, leave all PRs draft and unmerged.

## Concrete fixes committed

1. `scripts/build_lan_packs.py` contained a literal backslash-n escape after a Python `with` statement. Replaced it with an actual newline so the file parses.
2. Android debug manifest previously specified `usesCleartextTraffic=true` while main manifest specified `false`. Added an explicit `tools:replace` override in the **debug** manifest only. Release remains cleartext-disabled.
3. Native Kotlin timetable connections now carry GTFS pickup and dropoff flags from SQLite, block new boarding where pickup is prohibited, and block alighting where dropoff is prohibited. Through passengers may continue on the same trip without reboarding.
4. Added six synthetic Kotlin regression cases for these conditions, deadline rejection and zero-leg same-stop routes.

## Reproducible verification

New `.github/workflows/routing-verification.yml` runs on pull requests touching routing files and on manual dispatch:
- Python 3.12 `py_compile` of the street/transfer/planner modules and OSM graph builder.
- Python `unittest discover` for all `tests/test_*.py` synthetic fixtures.
- JDK 17, Android SDK 35, Gradle 8.9, `:app:assembleDebug`, `:app:testDebugUnitTest`.
- Debug APK uploaded as a short-lived CI artifact only on success.

The repo does **not** currently contain an `android/gradlew` wrapper. CI therefore provisions a pinned Gradle 8.9 executable. This does not claim the Gradle dependency graph or Android plugin version is validated until CI runs.

## Not yet verified

- **No CI result, Gradle compile, Kotlin JUnit execution, Android emulator/device test or real-feed comparison was observed in this session.** CI configuration is not evidence of passing checks.
- Routing semantics remain incomplete: parent-station transfer expansion, GTFS transfer type 1 semantics, scoped transfer restrictions, calendar edge cases, frequency-based services, DST, late departures, and end-to-end parity with Python need additional work.
- A regional-scale performance test and actual airplane-mode Android run are still required.
- No PR merged, no release published, no new feed downloaded.

## Follow-up architecture choice

A: test with actual licensed regional GTFS/OSM datasets and compare Kotlin/Python itineraries.
B: add cross-language golden fixtures and CI parity checks first.
C: add Android emulator instrumentation tests for offline installation and airplane mode.
D: harden package distribution and rollback before wider testing.
